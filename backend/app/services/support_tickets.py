import json
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.audit import add_audit_event
from app.core.auth import CurrentPrincipal
from app.models import Channel, Contact, Conversation, ConversationEvent, SupportTicket, Team, User
from app.models.foundation import utc_now
from app.schemas.support_tickets import SupportTicketCreate, SupportTicketList, SupportTicketRead, SupportTicketUpdate

SUPPORT_TICKET_ACCESS_ROLES = {"owner", "admin", "agent"}
SUPPORT_TICKET_MANAGER_ROLES = {"owner", "admin"}
SUPPORT_TICKET_STATUSES = {"open", "in_progress", "pending_customer", "resolved", "closed", "canceled"}
SUPPORT_TICKET_PRIORITIES = {"low", "normal", "high", "urgent"}
AGENT_ALLOWED_STATUSES = {"open", "in_progress", "pending_customer", "resolved"}
COMPLETED_STATUSES = {"resolved", "closed", "canceled"}
DEFAULT_SLA_MINUTES_BY_PRIORITY = {
    "urgent": 30,
    "high": 60,
    "normal": 240,
    "low": 1440,
}
SLA_WARNING_WINDOW_MINUTES = 15


def _is_manager(principal: CurrentPrincipal) -> bool:
    return bool(SUPPORT_TICKET_MANAGER_ROLES.intersection(principal.roles))


def _require_access(principal: CurrentPrincipal) -> None:
    if not SUPPORT_TICKET_ACCESS_ROLES.intersection(principal.roles):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="insufficient role")


def _require_same_tenant(tenant_id: int, principal: CurrentPrincipal) -> None:
    if tenant_id != principal.tenant.id:
        raise HTTPException(status_code=404, detail="tenant not found")


def _as_aware(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def _validate_user(db: Session, user_id: int, tenant_id: int) -> None:
    user = db.get(User, user_id)
    if user is None or user.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="user not found")


def _validate_team(db: Session, team_id: int, tenant_id: int) -> None:
    team = db.get(Team, team_id)
    if team is None or team.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="team not found")


def _sanitize_priority(priority: str | None, fallback: str = "normal") -> str:
    value = (priority or fallback or "normal").strip().lower()
    return value if value in SUPPORT_TICKET_PRIORITIES else "normal"


def _default_sla_minutes(priority: str) -> int:
    return DEFAULT_SLA_MINUTES_BY_PRIORITY.get(priority, DEFAULT_SLA_MINUTES_BY_PRIORITY["normal"])


def _sla_target_minutes(priority: str, explicit_value: int | None) -> int:
    if explicit_value is None:
        return _default_sla_minutes(priority)
    return min(10080, max(5, explicit_value))


def _compute_sla_due_at(created_at: datetime, target_minutes: int) -> datetime:
    return created_at + timedelta(minutes=target_minutes)


def _compute_sla_status(ticket: SupportTicket, now: datetime) -> str:
    if ticket.status in COMPLETED_STATUSES:
        return "completed"
    if ticket.status == "pending_customer":
        return "paused"
    due_at = _as_aware(ticket.sla_due_at)
    if due_at is None:
        return "ok"
    if now >= due_at:
        return "breached"
    if now + timedelta(minutes=SLA_WARNING_WINDOW_MINUTES) >= due_at:
        return "warning"
    return "ok"


def _ticket_state(ticket: SupportTicket) -> dict[str, object]:
    return {
        "status": ticket.status,
        "priority": ticket.priority,
        "assigned_user_id": ticket.assigned_user_id,
        "assigned_team_id": ticket.assigned_team_id,
        "sla_target_minutes": ticket.sla_target_minutes,
        "sla_due_at": ticket.sla_due_at.isoformat() if ticket.sla_due_at else None,
        "sla_status": ticket.sla_status,
        "resolved_by_id": ticket.resolved_by_id,
        "resolved_at": ticket.resolved_at.isoformat() if ticket.resolved_at else None,
    }


def _event_payload(
    ticket: SupportTicket,
    action: str,
    changed: dict | None = None,
    previous_state: dict | None = None,
) -> str:
    return json.dumps(
        {
            "action": action,
            "support_ticket_id": ticket.id,
            "previous_state": previous_state,
            "next_state": _ticket_state(ticket),
            "changed": changed or {},
        },
        ensure_ascii=False,
    )


def _ticket_read(db: Session, ticket: SupportTicket, now: datetime | None = None) -> SupportTicketRead:
    channel = db.get(Channel, ticket.channel_id)
    contact = db.get(Contact, ticket.contact_id)
    effective_now = now or utc_now()
    sla_status = _compute_sla_status(ticket, effective_now)
    return SupportTicketRead(
        id=ticket.id,
        tenant_id=ticket.tenant_id,
        conversation_id=ticket.conversation_id,
        channel_id=ticket.channel_id,
        channel_name=channel.name if channel else "",
        channel_type=channel.type if channel else "",
        contact_id=ticket.contact_id,
        contact_display_name=contact.display_name if contact else "",
        subject=ticket.subject,
        description=ticket.description,
        status=ticket.status,
        priority=ticket.priority,
        source_type=ticket.source_type,
        source_ref=ticket.source_ref,
        assigned_user_id=ticket.assigned_user_id,
        assigned_team_id=ticket.assigned_team_id,
        sla_target_minutes=ticket.sla_target_minutes,
        sla_due_at=ticket.sla_due_at,
        sla_status=sla_status,
        resolution_note=ticket.resolution_note,
        created_by_id=ticket.created_by_id,
        updated_by_id=ticket.updated_by_id,
        resolved_by_id=ticket.resolved_by_id,
        created_at=ticket.created_at,
        updated_at=ticket.updated_at,
        resolved_at=ticket.resolved_at,
    )


def _get_ticket_or_404(db: Session, ticket_id: int, principal: CurrentPrincipal) -> SupportTicket:
    ticket = db.get(SupportTicket, ticket_id)
    if ticket is None or ticket.tenant_id != principal.tenant.id:
        raise HTTPException(status_code=404, detail="support ticket not found")
    return ticket


def _require_agent_can_update(ticket: SupportTicket, payload: SupportTicketUpdate, principal: CurrentPrincipal) -> None:
    if _is_manager(principal):
        return
    if ticket.assigned_user_id not in {None, principal.user.id}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="ticket assigned to another user")
    if "assigned_user_id" in payload.model_fields_set and payload.assigned_user_id not in {None, principal.user.id}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="agent can only claim own ticket")
    if "assigned_team_id" in payload.model_fields_set:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="agent cannot assign teams")
    if payload.status and payload.status not in AGENT_ALLOWED_STATUSES:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="agent cannot set this ticket status")


def _assign_on_create(
    db: Session,
    tenant_id: int,
    payload: SupportTicketCreate,
    principal: CurrentPrincipal,
) -> tuple[int | None, int | None]:
    assigned_user_id = payload.assigned_user_id
    assigned_team_id = payload.assigned_team_id
    if _is_manager(principal):
        if assigned_user_id is not None:
            _validate_user(db, assigned_user_id, tenant_id)
        if assigned_team_id is not None:
            _validate_team(db, assigned_team_id, tenant_id)
        return assigned_user_id, assigned_team_id
    if assigned_team_id is not None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="agent cannot assign teams")
    if assigned_user_id is not None and assigned_user_id != principal.user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="agent can only claim own ticket")
    return principal.user.id, None


def create_support_ticket_from_conversation(
    db: Session,
    conversation_id: int,
    payload: SupportTicketCreate,
    principal: CurrentPrincipal,
) -> tuple[SupportTicketRead, bool]:
    _require_access(principal)
    conversation = db.get(Conversation, conversation_id)
    if conversation is None or conversation.tenant_id != principal.tenant.id:
        raise HTTPException(status_code=404, detail="conversation not found")

    source_ref = f"conversation:{conversation.id}"
    existing = db.scalar(
        select(SupportTicket).where(
            SupportTicket.tenant_id == conversation.tenant_id,
            SupportTicket.source_type == "conversation",
            SupportTicket.source_ref == source_ref,
        )
    )
    if existing is not None:
        return _ticket_read(db, existing), False

    priority = _sanitize_priority(payload.priority, conversation.priority)
    assigned_user_id, assigned_team_id = _assign_on_create(db, conversation.tenant_id, payload, principal)
    now = utc_now()
    sla_target_minutes = _sla_target_minutes(priority, payload.sla_target_minutes)
    subject = payload.subject.strip() or conversation.subject.strip() or f"会话 #{conversation.id}"
    description = payload.description.strip()
    if not description:
        description = "由会话生成的客服工单，需坐席确认处理结果。"
    ticket = SupportTicket(
        tenant_id=conversation.tenant_id,
        conversation_id=conversation.id,
        channel_id=conversation.channel_id,
        contact_id=conversation.contact_id,
        subject=subject,
        description=description,
        status="open",
        priority=priority,
        source_type="conversation",
        source_ref=source_ref,
        assigned_user_id=assigned_user_id,
        assigned_team_id=assigned_team_id,
        sla_target_minutes=sla_target_minutes,
        sla_due_at=_compute_sla_due_at(now, sla_target_minutes),
        sla_status="ok",
        created_by_id=principal.user.id,
        updated_by_id=principal.user.id,
        created_at=now,
        updated_at=now,
    )
    db.add(ticket)
    db.flush()
    db.add(
        ConversationEvent(
            conversation_id=conversation.id,
            event_type="support_ticket.created",
            actor_id=principal.user.id,
            payload=_event_payload(ticket, "created", previous_state=None),
        )
    )
    add_audit_event(
        db,
        tenant_id=ticket.tenant_id,
        action="support_ticket.created",
        resource_type="support_ticket",
        resource_id=str(ticket.id),
        actor_id=principal.user.id,
        payload={
            "conversation_id": ticket.conversation_id,
            "previous_state": None,
            "next_state": _ticket_state(ticket),
            "priority": ticket.priority,
            "sla_target_minutes": ticket.sla_target_minutes,
            "sla_due_at": ticket.sla_due_at.isoformat() if ticket.sla_due_at else None,
        },
    )
    db.commit()
    db.refresh(ticket)
    return _ticket_read(db, ticket), True


def list_support_tickets(
    db: Session,
    tenant_id: int,
    *,
    status_filter: str | None,
    priority: str | None,
    assigned: str,
    sla: str,
    query_text: str,
    page: int,
    page_size: int,
    principal: CurrentPrincipal,
) -> SupportTicketList:
    _require_access(principal)
    _require_same_tenant(tenant_id, principal)
    query = select(SupportTicket).where(SupportTicket.tenant_id == tenant_id)
    if status_filter and status_filter != "all":
        query = query.where(SupportTicket.status == status_filter)
    if priority and priority != "all":
        query = query.where(SupportTicket.priority == priority)
    if assigned == "mine":
        query = query.where(SupportTicket.assigned_user_id == principal.user.id)
    elif assigned == "unassigned":
        query = query.where(SupportTicket.assigned_user_id.is_(None))
    elif assigned == "assigned":
        query = query.where(SupportTicket.assigned_user_id.is_not(None))

    search_text = query_text.strip()
    if search_text:
        like_text = f"%{search_text}%"
        query = query.where(
            or_(
                SupportTicket.subject.ilike(like_text),
                SupportTicket.description.ilike(like_text),
                SupportTicket.source_ref.ilike(like_text),
            )
        )

    now = utc_now()
    if sla == "completed":
        query = query.where(SupportTicket.status.in_(COMPLETED_STATUSES))
    elif sla == "paused":
        query = query.where(SupportTicket.status == "pending_customer")
    elif sla == "breached":
        query = query.where(
            SupportTicket.status.not_in(COMPLETED_STATUSES | {"pending_customer"}),
            SupportTicket.sla_due_at.is_not(None),
            SupportTicket.sla_due_at <= now,
        )
    elif sla == "warning":
        query = query.where(
            SupportTicket.status.not_in(COMPLETED_STATUSES | {"pending_customer"}),
            SupportTicket.sla_due_at.is_not(None),
            SupportTicket.sla_due_at > now,
            SupportTicket.sla_due_at <= now + timedelta(minutes=SLA_WARNING_WINDOW_MINUTES),
        )
    elif sla == "ok":
        query = query.where(
            SupportTicket.status.not_in(COMPLETED_STATUSES | {"pending_customer"}),
            or_(
                SupportTicket.sla_due_at.is_(None),
                SupportTicket.sla_due_at > now + timedelta(minutes=SLA_WARNING_WINDOW_MINUTES),
            ),
        )

    total = int(db.scalar(select(func.count()).select_from(query.order_by(None).subquery())) or 0)
    start = (page - 1) * page_size
    tickets = list(
        db.scalars(
            query.order_by(SupportTicket.updated_at.desc(), SupportTicket.id.desc()).offset(start).limit(page_size)
        ).all()
    )
    items = [_ticket_read(db, ticket, now) for ticket in tickets]
    return SupportTicketList(items=items, page=page, page_size=page_size, total=total)


def update_support_ticket(
    db: Session,
    ticket_id: int,
    payload: SupportTicketUpdate,
    principal: CurrentPrincipal,
) -> SupportTicketRead:
    _require_access(principal)
    ticket = _get_ticket_or_404(db, ticket_id, principal)
    _require_agent_can_update(ticket, payload, principal)
    previous_state = _ticket_state(ticket)
    changed: dict[str, object] = {}

    if "assigned_user_id" in payload.model_fields_set and payload.assigned_user_id is not None:
        _validate_user(db, payload.assigned_user_id, ticket.tenant_id)
    if "assigned_team_id" in payload.model_fields_set and payload.assigned_team_id is not None:
        _validate_team(db, payload.assigned_team_id, ticket.tenant_id)

    if payload.subject is not None:
        ticket.subject = payload.subject.strip()
        changed["subject"] = True
    if payload.description is not None:
        ticket.description = payload.description.strip()
        changed["description"] = True
    if payload.priority is not None:
        ticket.priority = _sanitize_priority(payload.priority, ticket.priority)
        changed["priority"] = ticket.priority
    if "assigned_user_id" in payload.model_fields_set:
        ticket.assigned_user_id = payload.assigned_user_id
        changed["assigned_user_id"] = payload.assigned_user_id
    if "assigned_team_id" in payload.model_fields_set:
        ticket.assigned_team_id = payload.assigned_team_id
        changed["assigned_team_id"] = payload.assigned_team_id
    if not _is_manager(principal) and ticket.assigned_user_id is None:
        ticket.assigned_user_id = principal.user.id
        changed["assigned_user_id"] = principal.user.id
    if payload.sla_target_minutes is not None:
        ticket.sla_target_minutes = _sla_target_minutes(ticket.priority, payload.sla_target_minutes)
        ticket.sla_due_at = _compute_sla_due_at(_as_aware(ticket.created_at) or utc_now(), ticket.sla_target_minutes)
        changed["sla_target_minutes"] = ticket.sla_target_minutes
    if payload.resolution_note is not None:
        ticket.resolution_note = payload.resolution_note.strip()
        changed["resolution_note_set"] = bool(ticket.resolution_note)
    if payload.status is not None:
        if payload.status not in SUPPORT_TICKET_STATUSES:
            raise HTTPException(status_code=422, detail="invalid ticket status")
        if ticket.status in COMPLETED_STATUSES and payload.status not in COMPLETED_STATUSES:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="ticket reopen action required",
            )
        ticket.status = payload.status
        changed["status"] = ticket.status
        if payload.status in COMPLETED_STATUSES:
            ticket.resolved_at = utc_now()
            ticket.resolved_by_id = principal.user.id
        else:
            ticket.resolved_at = None
            ticket.resolved_by_id = None

    ticket.updated_by_id = principal.user.id
    ticket.updated_at = utc_now()
    ticket.sla_status = _compute_sla_status(ticket, ticket.updated_at)

    db.add(
        ConversationEvent(
            conversation_id=ticket.conversation_id,
            event_type="support_ticket.updated",
            actor_id=principal.user.id,
            payload=_event_payload(ticket, "updated", changed, previous_state),
        )
    )
    add_audit_event(
        db,
        tenant_id=ticket.tenant_id,
        action="support_ticket.updated",
        resource_type="support_ticket",
        resource_id=str(ticket.id),
        actor_id=principal.user.id,
        payload={
            "previous_state": previous_state,
            "next_state": _ticket_state(ticket),
            "changed": changed,
        },
    )
    db.commit()
    db.refresh(ticket)
    return _ticket_read(db, ticket)
