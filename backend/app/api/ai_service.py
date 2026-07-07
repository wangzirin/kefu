from fastapi import APIRouter, Depends

from app.core.auth import CurrentPrincipal
from app.core.rbac import require_permission
from app.schemas.ai_service import AiServiceStatusRead
from app.services.ai_service import get_ai_service_status

router = APIRouter(prefix="/api", tags=["ai-service"])


@router.get("/tenants/{tenant_id}/ai-service-status", response_model=AiServiceStatusRead)
def get_tenant_ai_service_status(
    tenant_id: int,
    principal: CurrentPrincipal = Depends(require_permission("conversation.read")),
) -> AiServiceStatusRead:
    return get_ai_service_status(tenant_id, principal)

