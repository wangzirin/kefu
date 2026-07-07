from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.tenants import require_tenant
from app.core.auth import CurrentPrincipal
from app.core.rbac import require_permission
from app.db.session import get_db
from app.models import Channel, Contact, Conversation, ConversationEvent, Message
from app.models.foundation import utc_now
from app.schemas.conversation_inbox import (
    AgentReplyCreate,
    ConversationAssignmentUpdate,
    ConversationInboxList,
    ConversationWorkflowAction,
)
from app.schemas.foundation import (
    ConversationCreate,
    ConversationDetail,
    ConversationRead,
    MessageCreate,
    MessageRead,
)
from app.services.conversation_inbox import (
    apply_conversation_workflow_action,
    create_agent_reply,
    list_conversation_inbox,
    update_conversation_assignment,
)
from app.services.ai_reply_cycle import process_inbound_message_for_ai

router = APIRouter(prefix="/api", tags=["conversations"])

CONVERSATION_READ_PERMISSION = "conversation.read"
CONVERSATION_MANAGE_PERMISSION = "conversation.manage"


def _require_tenant_owned(db: Session, model: type, item_id: int, tenant_id: int):
    item = db.get(model, item_id)
    if item is None or item.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail=f"{model.__name__.lower()} not found")
    return item


def _require_principal_tenant(tenant_id: int, principal: CurrentPrincipal) -> None:
    if tenant_id != principal.tenant.id:
        raise HTTPException(status_code=404, detail="tenant not found")


@router.post(
    "/tenants/{tenant_id}/conversations",
    response_model=ConversationRead,
    status_code=status.HTTP_201_CREATED,
)
def create_conversation(
    tenant_id: int,
    payload: ConversationCreate,
    principal: CurrentPrincipal = Depends(require_permission(CONVERSATION_MANAGE_PERMISSION)),
    db: Session = Depends(get_db),
) -> Conversation:
    require_tenant(db, tenant_id)
    _require_principal_tenant(tenant_id, principal)
    _require_tenant_owned(db, Channel, payload.channel_id, tenant_id)
    _require_tenant_owned(db, Contact, payload.contact_id, tenant_id)
    conversation = Conversation(tenant_id=tenant_id, **payload.model_dump())
    db.add(conversation)
    db.flush()
    db.add(
        ConversationEvent(
            conversation_id=conversation.id,
            event_type="conversation.created",
            payload="{}",
        )
    )
    db.commit()
    db.refresh(conversation)
    return conversation


@router.get("/tenants/{tenant_id}/conversations", response_model=list[ConversationRead])
def list_conversations(
    tenant_id: int,
    status_filter: str | None = Query(default=None, alias="status"),
    channel_id: int | None = None,
    principal: CurrentPrincipal = Depends(require_permission(CONVERSATION_READ_PERMISSION)),
    db: Session = Depends(get_db),
) -> list[Conversation]:
    require_tenant(db, tenant_id)
    _require_principal_tenant(tenant_id, principal)
    query = select(Conversation).where(Conversation.tenant_id == tenant_id)
    if status_filter:
        query = query.where(Conversation.status == status_filter)
    if channel_id:
        query = query.where(Conversation.channel_id == channel_id)
    query = query.order_by(Conversation.last_message_at.desc(), Conversation.id.desc())
    return list(db.scalars(query).all())


@router.get("/tenants/{tenant_id}/conversation-inbox", response_model=ConversationInboxList)
def list_tenant_conversation_inbox(
    tenant_id: int,
    status_filter: str | None = Query(default="all", alias="status", max_length=32),
    channel_id: int | None = None,
    priority: str | None = Query(default="all", max_length=32),
    assigned: str = Query(default="all", pattern="^(all|mine|assigned|unassigned)$"),
    sla: str = Query(default="all", pattern="^(all|idle|ok|warning|breached)$"),
    query_text: str = Query(default="", alias="query", max_length=200),
    sort: str = Query(default="last_message_desc", pattern="^(last_message_desc|waiting_desc|priority_desc)$"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    principal: CurrentPrincipal = Depends(require_permission(CONVERSATION_READ_PERMISSION)),
    db: Session = Depends(get_db),
) -> ConversationInboxList:
    require_tenant(db, tenant_id)
    return list_conversation_inbox(
        db,
        tenant_id,
        status_filter=status_filter,
        channel_id=channel_id,
        priority=priority,
        assigned=assigned,
        sla=sla,
        query_text=query_text,
        sort=sort,
        page=page,
        page_size=page_size,
        principal=principal,
    )


@router.get("/conversations/{conversation_id}", response_model=ConversationDetail)
def get_conversation(
    conversation_id: int,
    principal: CurrentPrincipal = Depends(require_permission(CONVERSATION_READ_PERMISSION)),
    db: Session = Depends(get_db),
) -> Conversation:
    query = (
        select(Conversation)
        .options(selectinload(Conversation.messages))
        .where(Conversation.id == conversation_id)
    )
    conversation = db.scalar(query)
    if conversation is None or conversation.tenant_id != principal.tenant.id:
        raise HTTPException(status_code=404, detail="conversation not found")
    return conversation


@router.patch("/conversations/{conversation_id}/assignment", response_model=ConversationRead)
def patch_conversation_assignment(
    conversation_id: int,
    payload: ConversationAssignmentUpdate,
    principal: CurrentPrincipal = Depends(require_permission(CONVERSATION_MANAGE_PERMISSION)),
    db: Session = Depends(get_db),
) -> Conversation:
    return update_conversation_assignment(db, conversation_id, payload, principal)


@router.post("/conversations/{conversation_id}/workflow-actions", response_model=ConversationRead)
def post_conversation_workflow_action(
    conversation_id: int,
    payload: ConversationWorkflowAction,
    principal: CurrentPrincipal = Depends(require_permission(CONVERSATION_MANAGE_PERMISSION)),
    db: Session = Depends(get_db),
) -> Conversation:
    return apply_conversation_workflow_action(db, conversation_id, payload, principal)


@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=MessageRead,
    status_code=status.HTTP_201_CREATED,
)
def create_message(
    conversation_id: int,
    payload: MessageCreate,
    principal: CurrentPrincipal = Depends(require_permission(CONVERSATION_MANAGE_PERMISSION)),
    db: Session = Depends(get_db),
) -> Message:
    conversation = db.get(Conversation, conversation_id)
    if conversation is None or conversation.tenant_id != principal.tenant.id:
        raise HTTPException(status_code=404, detail="conversation not found")
    created_at = utc_now()
    message = Message(
        conversation_id=conversation_id,
        created_at=created_at,
        **payload.model_dump(),
    )
    conversation.last_message_at = message.created_at
    db.add(message)
    db.add(
        ConversationEvent(
            conversation_id=conversation_id,
            event_type=f"message.{payload.direction}",
            payload="{}",
        )
    )
    db.commit()
    db.refresh(message)
    return message


@router.post(
    "/conversations/{conversation_id}/inbound-message-cycle",
    status_code=status.HTTP_201_CREATED,
)
def create_conversation_inbound_message_cycle(
    conversation_id: int,
    payload: MessageCreate,
    principal: CurrentPrincipal = Depends(require_permission(CONVERSATION_MANAGE_PERMISSION)),
    db: Session = Depends(get_db),
) -> dict:
    if payload.direction != "inbound":
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="direction must be inbound")
    message = create_message(conversation_id, payload, principal, db)
    result = process_inbound_message_for_ai(db, message_id=message.id, actor_id=principal.user.id)
    return {"message": MessageRead.model_validate(message, from_attributes=True), "ai_cycle": result}


@router.post(
    "/conversations/{conversation_id}/agent-replies",
    response_model=MessageRead,
    status_code=status.HTTP_201_CREATED,
)
def create_conversation_agent_reply(
    conversation_id: int,
    payload: AgentReplyCreate,
    principal: CurrentPrincipal = Depends(require_permission(CONVERSATION_MANAGE_PERMISSION)),
    db: Session = Depends(get_db),
) -> Message:
    return create_agent_reply(db, conversation_id, payload, principal)
