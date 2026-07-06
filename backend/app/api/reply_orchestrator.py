from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.auth import CurrentPrincipal
from app.core.rbac import require_permission
from app.db.session import get_db
from app.schemas.reply_orchestrator import ReplyOrchestrationCreate, ReplyOrchestrationRead
from app.services.reply_orchestrator import orchestrate_reply_for_message

router = APIRouter(prefix="/api", tags=["reply-orchestrator"])

CONVERSATION_MANAGE_PERMISSION = "conversation.manage"


@router.post(
    "/messages/{message_id}/reply-orchestrations",
    response_model=ReplyOrchestrationRead,
    status_code=status.HTTP_201_CREATED,
)
def create_reply_orchestration(
    message_id: int,
    payload: ReplyOrchestrationCreate,
    principal: CurrentPrincipal = Depends(require_permission(CONVERSATION_MANAGE_PERMISSION)),
    db: Session = Depends(get_db),
) -> ReplyOrchestrationRead:
    return orchestrate_reply_for_message(db, message_id, payload, principal)
