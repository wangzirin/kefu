from fastapi import APIRouter, Depends

from app.core.auth import CurrentPrincipal
from app.core.rbac import require_permission
from app.schemas.ai_service import (
    AiServiceStatusRead,
    ModelServiceConfigRead,
    ModelServiceConfigUpdate,
    ModelServiceProbeRead,
)
from app.services.ai_service import (
    clear_model_service_config,
    get_ai_service_status,
    get_model_service_config,
    probe_model_service,
    update_model_service_config,
)

router = APIRouter(prefix="/api", tags=["ai-service"])


@router.get("/tenants/{tenant_id}/ai-service-status", response_model=AiServiceStatusRead)
def get_tenant_ai_service_status(
    tenant_id: int,
    principal: CurrentPrincipal = Depends(require_permission("conversation.read")),
) -> AiServiceStatusRead:
    return get_ai_service_status(tenant_id, principal)


@router.get("/tenants/{tenant_id}/model-service", response_model=ModelServiceConfigRead)
def get_tenant_model_service_config(
    tenant_id: int,
    principal: CurrentPrincipal = Depends(require_permission("knowledge.read")),
) -> ModelServiceConfigRead:
    return get_model_service_config(tenant_id, principal)


@router.put("/tenants/{tenant_id}/model-service", response_model=ModelServiceConfigRead)
def update_tenant_model_service_config(
    tenant_id: int,
    payload: ModelServiceConfigUpdate,
    principal: CurrentPrincipal = Depends(require_permission("knowledge.manage")),
) -> ModelServiceConfigRead:
    return update_model_service_config(tenant_id, payload, principal)


@router.delete("/tenants/{tenant_id}/model-service", response_model=ModelServiceConfigRead)
def clear_tenant_model_service_config(
    tenant_id: int,
    principal: CurrentPrincipal = Depends(require_permission("knowledge.manage")),
) -> ModelServiceConfigRead:
    return clear_model_service_config(tenant_id, principal)


@router.post("/tenants/{tenant_id}/model-service/probe", response_model=ModelServiceProbeRead)
def probe_tenant_model_service(
    tenant_id: int,
    principal: CurrentPrincipal = Depends(require_permission("knowledge.manage")),
) -> ModelServiceProbeRead:
    return probe_model_service(tenant_id, principal)
