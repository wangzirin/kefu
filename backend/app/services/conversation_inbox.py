import json
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.auth import CurrentPrincipal
from app.models import (
    Channel,
    Contact,
    Conversation,
    ConversationEvent,
    DeliveryFailureReview,
    HumanReviewTask,
    Message,
    OutboxDraft,
    Team,
    User,
)
from app.models.foundation import utc_now
from app.schemas.conversation_inbox import (
    AgentReplyCreate,
    ConversationAssignmentUpdate,
    ConversationInboxItemRead,
    ConversationInboxList,
    ConversationWorkflowAction,
)

SLA_WARNING_MINUTES = 30
SLA_BREACH_MINUTES = 60
OPEN_CONVERSATION_STATUSES = {
    "bot",
    "bot_visiting",
    "handoff",
    "queued_for_me",
    "assigned_to_me",
    "open",
    "pending",
    "waiting_human",
    "follow_up",
}
PENDING_OUTBOX_STATUSES = {"pending_confirmation", "ready_to_send"}
CUSTOMER_CLOSE_NOTICE = "客服已关闭对话，本次咨询已结束。"
CUSTOMER_TRANSFER_NOTICE = "正在为您转接其他客服，请稍候。"
PRIORITY_ORDER = {
    "critical": 5,
    "urgent": 4,
    "high": 3,
    "medium": 2,
    "normal": 1,
    "low": 0,
}
HANDOFF_REASON_LABELS = {
    "complaint": "投诉",
    "abnormal_emotion": "情绪异常",
    "sensitive_content": "敏感内容",
    "prompt_injection": "Prompt 注入",
    "no_knowledge_hit": "无知识命中",
    "low_confidence": "低置信",
    "model_failure": "模型失败",
    "external_send_failure": "外发失败",
    "customer_requested_human": "客户要求人工",
}


def _require_same_tenant(tenant_id: int, principal: CurrentPrincipal) -> None:
    if tenant_id != principal.tenant.id:
        raise HTTPException(status_code=404, detail="tenant not found")


def _as_aware(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def _count_scalar(db: Session, query) -> int:
    return int(db.scalar(query) or 0)


def _add_customer_visible_system_message(
    db: Session,
    conversation: Conversation,
    *,
    content: str,
    external_message_id: str,
    created_at: datetime,
) -> Message:
    conversation.last_message_at = created_at
    message = Message(
        conversation_id=conversation.id,
        direction="outbound",
        sender_type="system",
        content=content,
        external_message_id=external_message_id,
        created_at=created_at,
    )
    db.add(message)
    db.flush()
    return message


def _last_message(db: Session, conversation_id: int, direction: str | None = None) -> Message | None:
    query = select(Message).where(Message.conversation_id == conversation_id)
    if direction:
        query = query.where(Message.direction == direction)
    query = query.order_by(Message.created_at.desc(), Message.id.desc()).limit(1)
    return db.scalar(query)


def _waiting_minutes(
    *,
    now: datetime,
    conversation: Conversation,
    last_inbound: Message | None,
    last_outbound: Message | None,
) -> int:
    if conversation.status not in OPEN_CONVERSATION_STATUSES or last_inbound is None:
        return 0
    inbound_at = _as_aware(last_inbound.created_at)
    outbound_at = _as_aware(last_outbound.created_at) if last_outbound else None
    if inbound_at is None or (outbound_at is not None and outbound_at >= inbound_at):
        return 0
    return max(0, int((now - inbound_at).total_seconds() // 60))


def _sla_status(waiting_minutes: int) -> str:
    if waiting_minutes >= SLA_BREACH_MINUTES:
        return "breached"
    if waiting_minutes >= SLA_WARNING_MINUTES:
        return "warning"
    if waiting_minutes > 0:
        return "ok"
    return "idle"


def _next_action(
    *,
    human_review_open_count: int,
    outbox_pending_count: int,
    delivery_failure_open_count: int,
    last_message_direction: str | None,
) -> str:
    if delivery_failure_open_count > 0:
        return "处理发送失败"
    if human_review_open_count > 0:
        return "审核 AI 草稿"
    if outbox_pending_count > 0:
        return "确认待发送草稿"
    if last_message_direction == "inbound":
        return "接待客户或触发 AI 回复"
    return "继续观察"


def _latest_open_human_review_task(db: Session, conversation: Conversation) -> HumanReviewTask | None:
    return db.scalar(
        select(HumanReviewTask)
        .where(
            HumanReviewTask.tenant_id == conversation.tenant_id,
            HumanReviewTask.conversation_id == conversation.id,
            HumanReviewTask.status == "open",
        )
        .order_by(HumanReviewTask.created_at.desc(), HumanReviewTask.id.desc())
        .limit(1)
    )


def _build_inbox_item(db: Session, conversation: Conversation, now: datetime) -> ConversationInboxItemRead:
    channel = db.get(Channel, conversation.channel_id)
    contact = db.get(Contact, conversation.contact_id)
    last_any = _last_message(db, conversation.id)
    last_inbound = _last_message(db, conversation.id, "inbound")
    last_outbound = _last_message(db, conversation.id, "outbound")
    waiting = _waiting_minutes(
        now=now,
        conversation=conversation,
        last_inbound=last_inbound,
        last_outbound=last_outbound,
    )
    sla_status = _sla_status(waiting)
    last_inbound_at = _as_aware(last_inbound.created_at) if last_inbound else None
    sla_due_at = last_inbound_at + timedelta(minutes=SLA_WARNING_MINUTES) if last_inbound_at and waiting > 0 else None
    human_review_open_count = _count_scalar(
        db,
        select(func.count(HumanReviewTask.id)).where(
            HumanReviewTask.tenant_id == conversation.tenant_id,
            HumanReviewTask.conversation_id == conversation.id,
            HumanReviewTask.status == "open",
        ),
    )
    latest_human_review_task = _latest_open_human_review_task(db, conversation)
    outbox_pending_count = _count_scalar(
        db,
        select(func.count(OutboxDraft.id)).where(
            OutboxDraft.tenant_id == conversation.tenant_id,
            OutboxDraft.conversation_id == conversation.id,
            OutboxDraft.status.in_(PENDING_OUTBOX_STATUSES),
        ),
    )
    delivery_failure_open_count = _count_scalar(
        db,
        select(func.count(DeliveryFailureReview.id))
        .join(OutboxDraft, DeliveryFailureReview.outbox_draft_id == OutboxDraft.id)
        .where(
            DeliveryFailureReview.tenant_id == conversation.tenant_id,
            DeliveryFailureReview.status == "open",
            OutboxDraft.conversation_id == conversation.id,
        ),
    )
    last_preview = ""
    if last_any is not None:
        last_preview = last_any.content.strip().replace("\n", " ")[:140]
    return ConversationInboxItemRead(
        id=conversation.id,
        tenant_id=conversation.tenant_id,
        channel_id=conversation.channel_id,
        channel_type=channel.type if channel else "",
        channel_name=channel.name if channel else "",
        contact_id=conversation.contact_id,
        contact_display_name=contact.display_name if contact else "",
        assigned_user_id=conversation.assigned_user_id,
        assigned_team_id=conversation.assigned_team_id,
        status=conversation.status,
        priority=conversation.priority,
        subject=conversation.subject,
        last_message_at=conversation.last_message_at,
        created_at=conversation.created_at,
        last_message_preview=last_preview,
        last_message_direction=last_any.direction if last_any else None,
        last_customer_message_at=last_inbound.created_at if last_inbound else None,
        waiting_minutes=waiting,
        sla_status=sla_status,
        sla_due_at=sla_due_at,
        human_review_open_count=human_review_open_count,
        latest_handoff_reason=latest_human_review_task.reason if latest_human_review_task else "",
        latest_handoff_reason_label=(
            HANDOFF_REASON_LABELS.get(latest_human_review_task.reason, latest_human_review_task.reason)
            if latest_human_review_task
            else ""
        ),
        latest_human_review_task_id=latest_human_review_task.id if latest_human_review_task else None,
        outbox_pending_count=outbox_pending_count,
        delivery_failure_open_count=delivery_failure_open_count,
        next_action=_next_action(
            human_review_open_count=human_review_open_count,
            outbox_pending_count=outbox_pending_count,
            delivery_failure_open_count=delivery_failure_open_count,
            last_message_direction=last_any.direction if last_any else None,
        ),
    )


def _priority_rank(value: str) -> int:
    return PRIORITY_ORDER.get(value, 0)


def _validate_user(db: Session, user_id: int, tenant_id: int) -> None:
    user = db.get(User, user_id)
    if user is None or user.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="user not found")


def _validate_team(db: Session, team_id: int, tenant_id: int) -> None:
    team = db.get(Team, team_id)
    if team is None or team.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="team not found")


def _conversation_state(conversation: Conversation) -> dict[str, int | str | None]:
    return {
        "assigned_user_id": conversation.assigned_user_id,
        "assigned_team_id": conversation.assigned_team_id,
        "status": conversation.status,
        "priority": conversation.priority,
    }


def list_conversation_inbox(
    db: Session,
    tenant_id: int,
    *,
    status_filter: str | None,
    channel_id: int | None,
    priority: str | None,
    assigned: str,
    sla: str,
    query_text: str,
    sort: str,
    page: int,
    page_size: int,
    principal: CurrentPrincipal,
) -> ConversationInboxList:
    _require_same_tenant(tenant_id, principal)
    query = (
        select(Conversation)
        .join(Contact, Conversation.contact_id == Contact.id)
        .where(Conversation.tenant_id == tenant_id)
    )
    if status_filter and status_filter != "all":
        query = query.where(Conversation.status == status_filter)
    if channel_id:
        query = query.where(Conversation.channel_id == channel_id)
    if priority and priority != "all":
        query = query.where(Conversation.priority == priority)
    if assigned == "mine":
        query = query.where(Conversation.assigned_user_id == principal.user.id)
    elif assigned == "unassigned":
        query = query.where(Conversation.assigned_user_id.is_(None))
    elif assigned == "assigned":
        query = query.where(Conversation.assigned_user_id.is_not(None))
    search_text = query_text.strip()
    if search_text:
        like_text = f"%{search_text}%"
        message_exists = (
            select(Message.id)
            .where(
                Message.conversation_id == Conversation.id,
                Message.content.ilike(like_text),
            )
            .exists()
        )
        query = query.where(
            or_(
                Conversation.subject.ilike(like_text),
                Conversation.priority.ilike(like_text),
                Conversation.status.ilike(like_text),
                Contact.display_name.ilike(like_text),
                message_exists,
            )
        )

    conversations = list(db.scalars(query).all())
    now = utc_now()
    items = [_build_inbox_item(db, conversation, now) for conversation in conversations]
    if sla != "all":
        items = [item for item in items if item.sla_status == sla]

    floor = datetime.min.replace(tzinfo=timezone.utc)
    if sort == "waiting_desc":
        items.sort(
            key=lambda item: (item.waiting_minutes, _as_aware(item.last_message_at) or floor, item.id),
            reverse=True,
        )
    elif sort == "priority_desc":
        items.sort(
            key=lambda item: (_priority_rank(item.priority), _as_aware(item.last_message_at) or floor, item.id),
            reverse=True,
        )
    else:
        items.sort(key=lambda item: (_as_aware(item.last_message_at) or floor, item.id), reverse=True)

    total = len(items)
    start = (page - 1) * page_size
    return ConversationInboxList(
        items=items[start : start + page_size],
        page=page,
        page_size=page_size,
        total=total,
    )


def update_conversation_assignment(
    db: Session,
    conversation_id: int,
    payload: ConversationAssignmentUpdate,
    principal: CurrentPrincipal,
) -> Conversation:
    conversation = db.get(Conversation, conversation_id)
    if conversation is None or conversation.tenant_id != principal.tenant.id:
        raise HTTPException(status_code=404, detail="conversation not found")
    if "assigned_user_id" in payload.model_fields_set and payload.assigned_user_id is not None:
        _validate_user(db, payload.assigned_user_id, principal.tenant.id)
    if "assigned_team_id" in payload.model_fields_set and payload.assigned_team_id is not None:
        _validate_team(db, payload.assigned_team_id, principal.tenant.id)

    if "assigned_user_id" in payload.model_fields_set:
        conversation.assigned_user_id = payload.assigned_user_id
    if "assigned_team_id" in payload.model_fields_set:
        conversation.assigned_team_id = payload.assigned_team_id
    if payload.status:
        conversation.status = payload.status
    db.add(
        ConversationEvent(
            conversation_id=conversation.id,
            event_type="conversation.assignment_updated",
            actor_id=principal.user.id,
            payload=payload.model_dump_json(exclude_unset=True),
        )
    )
    db.commit()
    db.refresh(conversation)
    return conversation


def apply_conversation_workflow_action(
    db: Session,
    conversation_id: int,
    payload: ConversationWorkflowAction,
    principal: CurrentPrincipal,
) -> Conversation:
    conversation = db.get(Conversation, conversation_id)
    if conversation is None or conversation.tenant_id != principal.tenant.id:
        raise HTTPException(status_code=404, detail="conversation not found")

    previous_state = _conversation_state(conversation)
    note = payload.note.strip()
    if payload.target_user_id is not None:
        _validate_user(db, payload.target_user_id, principal.tenant.id)
    if payload.target_team_id is not None:
        _validate_team(db, payload.target_team_id, principal.tenant.id)

    if payload.action == "claim":
        if conversation.assigned_user_id not in {None, principal.user.id}:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="conversation already assigned",
            )
        conversation.assigned_user_id = principal.user.id
        conversation.status = "assigned_to_me"
    elif payload.action == "release":
        conversation.assigned_user_id = None
        conversation.assigned_team_id = None
        conversation.status = "queued_for_me"
    elif payload.action == "transfer":
        if payload.target_user_id is None and payload.target_team_id is None:
            raise HTTPException(
                status_code=422,
                detail="target_user_id or target_team_id required",
            )
        now = utc_now()
        conversation.assigned_user_id = payload.target_user_id
        conversation.assigned_team_id = payload.target_team_id
        conversation.status = "queued_for_me"
        _add_customer_visible_system_message(
            db,
            conversation,
            content=CUSTOMER_TRANSFER_NOTICE,
            external_message_id=f"local-transfer-{conversation.id}-{int(now.timestamp())}",
            created_at=now,
        )
    elif payload.action == "close":
        now = utc_now()
        conversation.status = "closed"
        _add_customer_visible_system_message(
            db,
            conversation,
            content=CUSTOMER_CLOSE_NOTICE,
            external_message_id=f"local-close-{conversation.id}-{int(now.timestamp())}",
            created_at=now,
        )
    elif payload.action == "resolve":
        conversation.status = "resolved"
    elif payload.action == "follow_up":
        conversation.assigned_user_id = conversation.assigned_user_id or principal.user.id
        conversation.status = "follow_up"
    elif payload.action == "wait_customer":
        conversation.assigned_user_id = conversation.assigned_user_id or principal.user.id
        conversation.status = "waiting_customer"
    elif payload.action == "reopen":
        conversation.assigned_user_id = conversation.assigned_user_id or principal.user.id
        conversation.status = "assigned_to_me"
    elif payload.action == "note":
        if not note:
            raise HTTPException(
                status_code=422,
                detail="note required",
            )

    event_payload = payload.model_dump()
    event_payload.update(
        {
            "note": note,
            "previous_state": previous_state,
            "next_state": _conversation_state(conversation),
        }
    )
    db.add(
        ConversationEvent(
            conversation_id=conversation.id,
            event_type=f"conversation.workflow.{payload.action}",
            actor_id=principal.user.id,
            payload=json.dumps(event_payload, ensure_ascii=False),
        )
    )
    db.commit()
    db.refresh(conversation)
    return conversation


def create_agent_reply(
    db: Session,
    conversation_id: int,
    payload: AgentReplyCreate,
    principal: CurrentPrincipal,
) -> Message:
    conversation = db.get(Conversation, conversation_id)
    if conversation is None or conversation.tenant_id != principal.tenant.id:
        raise HTTPException(status_code=404, detail="conversation not found")
    if conversation.status == "resolved" and not payload.close_conversation:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="conversation already resolved")
    if conversation.status == "closed":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="conversation already closed")
    if conversation.assigned_user_id not in {None, principal.user.id}:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="conversation assigned to another agent")
    if conversation.status == "queued_for_me":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="claim conversation before replying")
    if conversation.status not in {"assigned_to_me", "handoff", "follow_up", "waiting_customer"}:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="conversation is not claimed by agent")
    now = utc_now()
    if conversation.assigned_user_id is None:
        conversation.assigned_user_id = principal.user.id
    conversation.status = "assigned_to_me"
    message = Message(
        conversation_id=conversation.id,
        direction="outbound",
        sender_type="agent",
        content=payload.content.strip(),
        external_message_id=payload.idempotency_key.strip() or f"agent-reply-{conversation.id}-{int(now.timestamp() * 1000)}",
        created_at=now,
    )
    conversation.last_message_at = now
    db.add(message)
    db.flush()
    close_message_id = None
    if payload.close_conversation:
        conversation.status = "closed"
        close_message = _add_customer_visible_system_message(
            db,
            conversation,
            content=CUSTOMER_CLOSE_NOTICE,
            external_message_id=f"local-close-{conversation.id}-{int(now.timestamp())}",
            created_at=now,
        )
        close_message_id = close_message.id
    db.add(
        ConversationEvent(
            conversation_id=conversation.id,
            event_type="message.agent_reply",
            actor_id=principal.user.id,
            payload=json.dumps(
                {
                    "message_id": message.id,
                    "close_message_id": close_message_id,
                    "close_conversation": payload.close_conversation,
                    "external_write": True,
                },
                ensure_ascii=False,
            ),
        )
    )
    db.commit()
    db.refresh(message)
    return message
