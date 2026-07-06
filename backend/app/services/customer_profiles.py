import json
from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.audit import add_audit_event
from app.core.auth import CurrentPrincipal
from app.models import Channel, Contact, Conversation, ConversationEvent, Message, SalesLead, SupportTicket, User
from app.models.foundation import utc_now
from app.schemas.customer_profiles import (
    ContactConversationSummary,
    ContactProfileDetail,
    ContactProfileList,
    ContactProfileRead,
    ContactTicketSummary,
    SalesLeadCreate,
    SalesLeadList,
    SalesLeadRead,
    SalesLeadUpdate,
)

CONTACT_PROFILE_ACCESS_ROLES = {"owner", "admin", "agent"}
CONTACT_PROFILE_MANAGER_ROLES = {"owner", "admin"}
OPEN_CONVERSATION_STATUSES = {"bot", "handoff", "open", "pending", "waiting_human", "follow_up"}
OPEN_TICKET_STATUSES = {"open", "in_progress", "pending_customer"}
ACTIVE_LEAD_STAGES = {"new", "contacted", "proposal"}
LEAD_STAGES = {"new", "contacted", "proposal", "won", "invalid", "lost"}
LEAD_INTENT_LEVELS = {"cold", "warm", "hot"}
INTENT_ORDER = {"cold": 1, "warm": 2, "hot": 3}


def _is_manager(principal: CurrentPrincipal) -> bool:
    return bool(CONTACT_PROFILE_MANAGER_ROLES.intersection(principal.roles))


def _require_access(principal: CurrentPrincipal) -> None:
    if not CONTACT_PROFILE_ACCESS_ROLES.intersection(principal.roles):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="insufficient role")


def _require_same_tenant(tenant_id: int, principal: CurrentPrincipal) -> None:
    if tenant_id != principal.tenant.id:
        raise HTTPException(status_code=404, detail="tenant not found")


def _validate_user(db: Session, user_id: int, tenant_id: int) -> None:
    user = db.get(User, user_id)
    if user is None or user.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="user not found")


def _mask_phone(value: str) -> str:
    text = value.strip()
    if not text:
        return ""
    if len(text) <= 7:
        return f"{text[:2]}****{text[-1:]}"
    return f"{text[:3]}****{text[-4:]}"


def _mask_wechat(value: str) -> str:
    text = value.strip()
    if not text:
        return ""
    if len(text) <= 6:
        return f"{text[:2]}****{text[-1:]}"
    return f"{text[:4]}****{text[-4:]}"


def _visible_phone(contact: Contact, principal: CurrentPrincipal) -> str:
    return contact.phone if _is_manager(principal) else _mask_phone(contact.phone)


def _visible_wechat(contact: Contact, principal: CurrentPrincipal) -> str:
    return contact.wechat if _is_manager(principal) else _mask_wechat(contact.wechat)


def _last_message(db: Session, conversation_id: int) -> Message | None:
    return db.scalar(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.desc(), Message.id.desc())
        .limit(1)
    )


def _preview(message: Message | None) -> str:
    if message is None:
        return ""
    return message.content.strip().replace("\n", " ")[:140]


def _count(db: Session, query) -> int:
    return int(db.scalar(query) or 0)


def _highest_intent(db: Session, tenant_id: int, contact_id: int) -> str:
    levels = list(
        db.scalars(
            select(SalesLead.intent_level).where(
                SalesLead.tenant_id == tenant_id,
                SalesLead.contact_id == contact_id,
            )
        ).all()
    )
    if not levels:
        return "none"
    return max(levels, key=lambda value: INTENT_ORDER.get(value, 0))


def _latest_conversation(db: Session, tenant_id: int, contact_id: int) -> Conversation | None:
    return db.scalar(
        select(Conversation)
        .where(Conversation.tenant_id == tenant_id, Conversation.contact_id == contact_id)
        .order_by(Conversation.last_message_at.desc(), Conversation.id.desc())
        .limit(1)
    )


def _next_action(
    *,
    open_ticket_count: int,
    active_lead_count: int,
    open_conversation_count: int,
    highest_intent_level: str,
) -> str:
    if open_ticket_count > 0:
        return "处理未完成工单"
    if highest_intent_level == "hot" and active_lead_count > 0:
        return "优先销售跟进"
    if active_lead_count > 0:
        return "推进线索跟进"
    if open_conversation_count > 0:
        return "继续会话接待"
    return "保持观察"


def _contact_profile_read(db: Session, contact: Contact, principal: CurrentPrincipal) -> ContactProfileRead:
    latest_conversation = _latest_conversation(db, contact.tenant_id, contact.id)
    latest_channel = db.get(Channel, latest_conversation.channel_id) if latest_conversation else None
    last_message = _last_message(db, latest_conversation.id) if latest_conversation else None
    conversation_count = _count(
        db,
        select(func.count(Conversation.id)).where(
            Conversation.tenant_id == contact.tenant_id,
            Conversation.contact_id == contact.id,
        ),
    )
    open_conversation_count = _count(
        db,
        select(func.count(Conversation.id)).where(
            Conversation.tenant_id == contact.tenant_id,
            Conversation.contact_id == contact.id,
            Conversation.status.in_(OPEN_CONVERSATION_STATUSES),
        ),
    )
    support_ticket_count = _count(
        db,
        select(func.count(SupportTicket.id)).where(
            SupportTicket.tenant_id == contact.tenant_id,
            SupportTicket.contact_id == contact.id,
        ),
    )
    open_support_ticket_count = _count(
        db,
        select(func.count(SupportTicket.id)).where(
            SupportTicket.tenant_id == contact.tenant_id,
            SupportTicket.contact_id == contact.id,
            SupportTicket.status.in_(OPEN_TICKET_STATUSES),
        ),
    )
    lead_count = _count(
        db,
        select(func.count(SalesLead.id)).where(
            SalesLead.tenant_id == contact.tenant_id,
            SalesLead.contact_id == contact.id,
        ),
    )
    active_lead_count = _count(
        db,
        select(func.count(SalesLead.id)).where(
            SalesLead.tenant_id == contact.tenant_id,
            SalesLead.contact_id == contact.id,
            SalesLead.stage.in_(ACTIVE_LEAD_STAGES),
        ),
    )
    highest_intent_level = _highest_intent(db, contact.tenant_id, contact.id)
    return ContactProfileRead(
        id=contact.id,
        tenant_id=contact.tenant_id,
        display_name=contact.display_name,
        phone=_visible_phone(contact, principal),
        wechat=_visible_wechat(contact, principal),
        created_at=contact.created_at,
        conversation_count=conversation_count,
        open_conversation_count=open_conversation_count,
        support_ticket_count=support_ticket_count,
        open_support_ticket_count=open_support_ticket_count,
        lead_count=lead_count,
        active_lead_count=active_lead_count,
        highest_intent_level=highest_intent_level,
        latest_channel_id=latest_channel.id if latest_channel else None,
        latest_channel_name=latest_channel.name if latest_channel else "",
        latest_channel_type=latest_channel.type if latest_channel else "",
        last_message_at=latest_conversation.last_message_at if latest_conversation else None,
        last_message_preview=_preview(last_message),
        next_action=_next_action(
            open_ticket_count=open_support_ticket_count,
            active_lead_count=active_lead_count,
            open_conversation_count=open_conversation_count,
            highest_intent_level=highest_intent_level,
        ),
    )


def list_contact_profiles(
    db: Session,
    tenant_id: int,
    *,
    query_text: str,
    page: int,
    page_size: int,
    principal: CurrentPrincipal,
) -> ContactProfileList:
    _require_access(principal)
    _require_same_tenant(tenant_id, principal)
    query = select(Contact).where(Contact.tenant_id == tenant_id)
    search_text = query_text.strip()
    if search_text:
        like_text = f"%{search_text}%"
        message_exists = (
            select(Message.id)
            .join(Conversation, Message.conversation_id == Conversation.id)
            .where(
                Conversation.contact_id == Contact.id,
                Message.content.ilike(like_text),
            )
            .exists()
        )
        query = query.where(
            or_(
                Contact.display_name.ilike(like_text),
                Contact.phone.ilike(like_text),
                Contact.wechat.ilike(like_text),
                message_exists,
            )
        )
    total = _count(db, select(func.count()).select_from(query.order_by(None).subquery()))
    contacts = list(
        db.scalars(
            query.order_by(Contact.created_at.desc(), Contact.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()
    )
    return ContactProfileList(
        items=[_contact_profile_read(db, contact, principal) for contact in contacts],
        page=page,
        page_size=page_size,
        total=total,
    )


def get_contact_profile(
    db: Session,
    contact_id: int,
    principal: CurrentPrincipal,
) -> ContactProfileDetail:
    _require_access(principal)
    contact = db.get(Contact, contact_id)
    if contact is None or contact.tenant_id != principal.tenant.id:
        raise HTTPException(status_code=404, detail="contact not found")
    base = _contact_profile_read(db, contact, principal)
    conversations = list(
        db.scalars(
            select(Conversation)
            .where(Conversation.tenant_id == contact.tenant_id, Conversation.contact_id == contact.id)
            .order_by(Conversation.last_message_at.desc(), Conversation.id.desc())
            .limit(5)
        ).all()
    )
    recent_conversations: list[ContactConversationSummary] = []
    for conversation in conversations:
        channel = db.get(Channel, conversation.channel_id)
        recent_conversations.append(
            ContactConversationSummary(
                id=conversation.id,
                channel_id=conversation.channel_id,
                channel_name=channel.name if channel else "",
                channel_type=channel.type if channel else "",
                status=conversation.status,
                priority=conversation.priority,
                subject=conversation.subject,
                last_message_at=conversation.last_message_at,
                last_message_preview=_preview(_last_message(db, conversation.id)),
            )
        )
    open_leads = [
        _lead_read(db, lead)
        for lead in db.scalars(
            select(SalesLead)
            .where(
                SalesLead.tenant_id == contact.tenant_id,
                SalesLead.contact_id == contact.id,
                SalesLead.stage.in_(ACTIVE_LEAD_STAGES),
            )
            .order_by(SalesLead.updated_at.desc(), SalesLead.id.desc())
            .limit(5)
        ).all()
    ]
    open_tickets = []
    tickets = list(
        db.scalars(
            select(SupportTicket)
            .where(
                SupportTicket.tenant_id == contact.tenant_id,
                SupportTicket.contact_id == contact.id,
                SupportTicket.status.in_(OPEN_TICKET_STATUSES),
            )
            .order_by(SupportTicket.updated_at.desc(), SupportTicket.id.desc())
            .limit(5)
        ).all()
    )
    for ticket in tickets:
        open_tickets.append(
            ContactTicketSummary(
                id=ticket.id,
                subject=ticket.subject,
                status=ticket.status,
                priority=ticket.priority,
                sla_status=ticket.sla_status,
                updated_at=ticket.updated_at,
            )
        )
    return ContactProfileDetail(
        **base.model_dump(),
        recent_conversations=recent_conversations,
        open_leads=open_leads,
        open_tickets=open_tickets,
    )


def _lead_state(lead: SalesLead) -> dict[str, object]:
    return {
        "stage": lead.stage,
        "intent_level": lead.intent_level,
        "owner_user_id": lead.owner_user_id,
        "next_follow_up_at": lead.next_follow_up_at.isoformat() if lead.next_follow_up_at else None,
        "closed_at": lead.closed_at.isoformat() if lead.closed_at else None,
    }


def _lead_read(db: Session, lead: SalesLead) -> SalesLeadRead:
    contact = db.get(Contact, lead.contact_id)
    channel = db.get(Channel, lead.channel_id)
    latest_message = _last_message(db, lead.conversation_id) if lead.conversation_id else None
    return SalesLeadRead(
        id=lead.id,
        tenant_id=lead.tenant_id,
        contact_id=lead.contact_id,
        contact_display_name=contact.display_name if contact else "",
        channel_id=lead.channel_id,
        channel_name=channel.name if channel else "",
        channel_type=channel.type if channel else "",
        conversation_id=lead.conversation_id,
        title=lead.title,
        summary=lead.summary,
        stage=lead.stage,
        intent_level=lead.intent_level,
        expected_budget=lead.expected_budget,
        next_step=lead.next_step,
        owner_user_id=lead.owner_user_id,
        source_type=lead.source_type,
        source_ref=lead.source_ref,
        latest_message_preview=_preview(latest_message),
        next_follow_up_at=lead.next_follow_up_at,
        closed_at=lead.closed_at,
        created_by_id=lead.created_by_id,
        updated_by_id=lead.updated_by_id,
        created_at=lead.created_at,
        updated_at=lead.updated_at,
    )


def _sanitize_stage(value: str | None, fallback: str = "new") -> str:
    candidate = (value or fallback or "new").strip().lower()
    return candidate if candidate in LEAD_STAGES else "new"


def _sanitize_intent(value: str | None, fallback: str = "warm") -> str:
    candidate = (value or fallback or "warm").strip().lower()
    return candidate if candidate in LEAD_INTENT_LEVELS else "warm"


def create_lead_from_conversation(
    db: Session,
    conversation_id: int,
    payload: SalesLeadCreate,
    principal: CurrentPrincipal,
) -> tuple[SalesLeadRead, bool]:
    _require_access(principal)
    conversation = db.get(Conversation, conversation_id)
    if conversation is None or conversation.tenant_id != principal.tenant.id:
        raise HTTPException(status_code=404, detail="conversation not found")
    if payload.owner_user_id is not None:
        if _is_manager(principal):
            _validate_user(db, payload.owner_user_id, conversation.tenant_id)
        elif payload.owner_user_id != principal.user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="agent can only own lead")
    source_ref = f"conversation:{conversation.id}"
    existing = db.scalar(
        select(SalesLead).where(
            SalesLead.tenant_id == conversation.tenant_id,
            SalesLead.source_type == "conversation",
            SalesLead.source_ref == source_ref,
        )
    )
    if existing is not None:
        return _lead_read(db, existing), False
    now = utc_now()
    owner_user_id = payload.owner_user_id
    if owner_user_id is None and not _is_manager(principal):
        owner_user_id = principal.user.id
    stage = _sanitize_stage(payload.stage)
    lead = SalesLead(
        tenant_id=conversation.tenant_id,
        contact_id=conversation.contact_id,
        channel_id=conversation.channel_id,
        conversation_id=conversation.id,
        title=payload.title.strip() or conversation.subject.strip() or f"会话 #{conversation.id} 线索",
        summary=payload.summary.strip() or "由客户会话生成的销售线索，需确认需求、预算和下一步跟进。",
        stage=stage,
        intent_level=_sanitize_intent(payload.intent_level),
        expected_budget=payload.expected_budget.strip(),
        next_step=payload.next_step.strip(),
        owner_user_id=owner_user_id,
        source_type="conversation",
        source_ref=source_ref,
        created_by_id=principal.user.id,
        updated_by_id=principal.user.id,
        next_follow_up_at=payload.next_follow_up_at,
        closed_at=now if stage in {"won", "invalid", "lost"} else None,
        created_at=now,
        updated_at=now,
    )
    db.add(lead)
    db.flush()
    db.add(
        ConversationEvent(
            conversation_id=conversation.id,
            event_type="sales_lead.created",
            actor_id=principal.user.id,
            payload=json.dumps(
                {"sales_lead_id": lead.id, "stage": lead.stage, "intent_level": lead.intent_level},
                ensure_ascii=False,
            ),
        )
    )
    add_audit_event(
        db,
        tenant_id=lead.tenant_id,
        action="sales_lead.created",
        resource_type="sales_lead",
        resource_id=str(lead.id),
        actor_id=principal.user.id,
        payload={
            "conversation_id": lead.conversation_id,
            "contact_id": lead.contact_id,
            "next_state": _lead_state(lead),
        },
    )
    db.commit()
    db.refresh(lead)
    return _lead_read(db, lead), True


def list_sales_leads(
    db: Session,
    tenant_id: int,
    *,
    stage: str,
    intent: str,
    owner: str,
    query_text: str,
    page: int,
    page_size: int,
    principal: CurrentPrincipal,
) -> SalesLeadList:
    _require_access(principal)
    _require_same_tenant(tenant_id, principal)
    query = (
        select(SalesLead)
        .join(Contact, SalesLead.contact_id == Contact.id)
        .where(SalesLead.tenant_id == tenant_id)
    )
    if stage and stage != "all":
        query = query.where(SalesLead.stage == stage)
    if intent and intent != "all":
        query = query.where(SalesLead.intent_level == intent)
    if owner == "mine":
        query = query.where(SalesLead.owner_user_id == principal.user.id)
    elif owner == "unassigned":
        query = query.where(SalesLead.owner_user_id.is_(None))
    elif owner == "assigned":
        query = query.where(SalesLead.owner_user_id.is_not(None))
    search_text = query_text.strip()
    if search_text:
        like_text = f"%{search_text}%"
        query = query.where(
            or_(
                SalesLead.title.ilike(like_text),
                SalesLead.summary.ilike(like_text),
                SalesLead.expected_budget.ilike(like_text),
                Contact.display_name.ilike(like_text),
            )
        )
    total = _count(db, select(func.count()).select_from(query.order_by(None).subquery()))
    leads = list(
        db.scalars(
            query.order_by(SalesLead.updated_at.desc(), SalesLead.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()
    )
    return SalesLeadList(items=[_lead_read(db, lead) for lead in leads], page=page, page_size=page_size, total=total)


def update_sales_lead(
    db: Session,
    lead_id: int,
    payload: SalesLeadUpdate,
    principal: CurrentPrincipal,
) -> SalesLeadRead:
    _require_access(principal)
    lead = db.get(SalesLead, lead_id)
    if lead is None or lead.tenant_id != principal.tenant.id:
        raise HTTPException(status_code=404, detail="lead not found")
    if not _is_manager(principal) and lead.owner_user_id not in {None, principal.user.id}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="lead assigned to another user")
    if "owner_user_id" in payload.model_fields_set and payload.owner_user_id is not None:
        if _is_manager(principal):
            _validate_user(db, payload.owner_user_id, lead.tenant_id)
        elif payload.owner_user_id != principal.user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="agent can only own lead")

    previous_state = _lead_state(lead)
    changed: dict[str, object] = {}
    if payload.title is not None:
        lead.title = payload.title.strip()
        changed["title"] = True
    if payload.summary is not None:
        lead.summary = payload.summary.strip()
        changed["summary"] = True
    if payload.stage is not None:
        lead.stage = _sanitize_stage(payload.stage, lead.stage)
        changed["stage"] = lead.stage
    if payload.intent_level is not None:
        lead.intent_level = _sanitize_intent(payload.intent_level, lead.intent_level)
        changed["intent_level"] = lead.intent_level
    if payload.expected_budget is not None:
        lead.expected_budget = payload.expected_budget.strip()
        changed["expected_budget"] = lead.expected_budget
    if payload.next_step is not None:
        lead.next_step = payload.next_step.strip()
        changed["next_step"] = True
    if "owner_user_id" in payload.model_fields_set:
        lead.owner_user_id = payload.owner_user_id
        changed["owner_user_id"] = payload.owner_user_id
    if "next_follow_up_at" in payload.model_fields_set:
        lead.next_follow_up_at = payload.next_follow_up_at
        changed["next_follow_up_at"] = lead.next_follow_up_at.isoformat() if lead.next_follow_up_at else None
    if lead.stage in {"won", "invalid", "lost"} and lead.closed_at is None:
        lead.closed_at = utc_now()
        changed["closed_at"] = lead.closed_at.isoformat()
    elif lead.stage in ACTIVE_LEAD_STAGES:
        lead.closed_at = None
    lead.updated_by_id = principal.user.id
    lead.updated_at = utc_now()
    add_audit_event(
        db,
        tenant_id=lead.tenant_id,
        action="sales_lead.updated",
        resource_type="sales_lead",
        resource_id=str(lead.id),
        actor_id=principal.user.id,
        payload={
            "previous_state": previous_state,
            "next_state": _lead_state(lead),
            "changed": changed,
        },
    )
    db.commit()
    db.refresh(lead)
    return _lead_read(db, lead)
