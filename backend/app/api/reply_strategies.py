from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.auth import CurrentPrincipal
from app.core.rbac import require_permission
from app.db.session import get_db
from app.schemas.reply_strategies import TenantReplyStrategyRead, TenantReplyStrategyUpdate
from app.services.reply_strategies import get_tenant_reply_strategy, update_tenant_reply_strategy

router = APIRouter(prefix="/api", tags=["reply-strategies"])

KNOWLEDGE_READ_PERMISSION = "knowledge.read"
KNOWLEDGE_MANAGE_PERMISSION = "knowledge.manage"


@router.get("/tenants/{tenant_id}/reply-strategy", response_model=TenantReplyStrategyRead)
def read_tenant_reply_strategy(
    tenant_id: int,
    principal: CurrentPrincipal = Depends(require_permission(KNOWLEDGE_READ_PERMISSION)),
    db: Session = Depends(get_db),
) -> TenantReplyStrategyRead:
    return get_tenant_reply_strategy(db, tenant_id, principal)


@router.patch("/tenants/{tenant_id}/reply-strategy", response_model=TenantReplyStrategyRead)
def patch_tenant_reply_strategy(
    tenant_id: int,
    payload: TenantReplyStrategyUpdate,
    principal: CurrentPrincipal = Depends(require_permission(KNOWLEDGE_MANAGE_PERMISSION)),
    db: Session = Depends(get_db),
) -> TenantReplyStrategyRead:
    return update_tenant_reply_strategy(db, tenant_id, payload, principal)
