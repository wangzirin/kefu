from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.auth import CurrentPrincipal
from app.core.rbac import require_permission
from app.db.session import get_db
from app.schemas.reply_decisions import ReplyDecisionCreate, ReplyDecisionList, ReplyDecisionRead
from app.services.reply_decisions import create_reply_decision_for_message, list_reply_decisions

router = APIRouter(prefix="/api", tags=["reply-decisions"])

CONVERSATION_READ_PERMISSION = "conversation.read"
CONVERSATION_MANAGE_PERMISSION = "conversation.manage"


@router.post(
    "/messages/{message_id}/reply-decisions",
    response_model=ReplyDecisionRead,
    status_code=status.HTTP_201_CREATED,
)
def create_message_reply_decision(
    message_id: int,
    payload: ReplyDecisionCreate,
    principal: CurrentPrincipal = Depends(require_permission(CONVERSATION_MANAGE_PERMISSION)),
    db: Session = Depends(get_db),
) -> ReplyDecisionRead:
    return create_reply_decision_for_message(db, message_id, payload, principal)


@router.get("/tenants/{tenant_id}/reply-decisions", response_model=ReplyDecisionList)
def list_tenant_reply_decisions(
    tenant_id: int,
    state_filter: str | None = Query(
        default=None,
        alias="state",
        pattern="^(auto_reply_ready|manual_gate_required|knowledge_gap|blocked_by_policy|draft_only)$",
    ),
    conversation_id: int | None = Query(default=None, ge=1),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    principal: CurrentPrincipal = Depends(require_permission(CONVERSATION_READ_PERMISSION)),
    db: Session = Depends(get_db),
) -> ReplyDecisionList:
    return list_reply_decisions(
        db,
        tenant_id,
        state_filter=state_filter,
        conversation_id=conversation_id,
        page=page,
        page_size=page_size,
        principal=principal,
    )
