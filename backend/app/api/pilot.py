from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.auth import CurrentPrincipal
from app.core.rbac import require_permission
from app.db.session import get_db
from app.schemas.pilot import (
    CustomerMaterialHandoffBundleRead,
    CustomerMaterialBatchListRead,
    CustomerMaterialPrecheckCreate,
    CustomerMaterialPrecheckRead,
    CustomerMaterialTemplatePackageRead,
    KnowledgeConfirmationImportCreate,
    KnowledgeConfirmationImportRead,
    PilotReadinessRead,
    SafeTestConversationRead,
)
from app.services.pilot import (
    build_pilot_readiness,
    create_safe_test_conversation,
    get_customer_material_handoff_bundle,
    get_customer_material_template_package,
    import_knowledge_confirmation_csv,
    list_customer_material_batches,
    precheck_customer_materials,
)


router = APIRouter(prefix="/api", tags=["pilot"])


@router.get("/tenants/{tenant_id}/pilot-readiness", response_model=PilotReadinessRead)
def get_pilot_readiness(
    tenant_id: int,
    principal: CurrentPrincipal = Depends(require_permission("ops.metrics.read")),
    db: Session = Depends(get_db),
) -> PilotReadinessRead:
    return build_pilot_readiness(db, tenant_id=tenant_id, principal=principal)


@router.post(
    "/tenants/{tenant_id}/knowledge-confirmations/imports",
    response_model=KnowledgeConfirmationImportRead,
)
def import_knowledge_confirmation(
    tenant_id: int,
    payload: KnowledgeConfirmationImportCreate,
    principal: CurrentPrincipal = Depends(require_permission("knowledge.manage")),
    db: Session = Depends(get_db),
) -> KnowledgeConfirmationImportRead:
    return import_knowledge_confirmation_csv(db, tenant_id=tenant_id, payload=payload, principal=principal)


@router.post(
    "/tenants/{tenant_id}/customer-materials/precheck",
    response_model=CustomerMaterialPrecheckRead,
)
def precheck_customer_material_package(
    tenant_id: int,
    payload: CustomerMaterialPrecheckCreate,
    principal: CurrentPrincipal = Depends(require_permission("knowledge.manage")),
    db: Session = Depends(get_db),
) -> CustomerMaterialPrecheckRead:
    return precheck_customer_materials(db, tenant_id=tenant_id, payload=payload, principal=principal)


@router.get(
    "/tenants/{tenant_id}/customer-materials/batches",
    response_model=CustomerMaterialBatchListRead,
)
def list_customer_material_batch_records(
    tenant_id: int,
    principal: CurrentPrincipal = Depends(require_permission("knowledge.manage")),
    db: Session = Depends(get_db),
) -> CustomerMaterialBatchListRead:
    return list_customer_material_batches(db, tenant_id=tenant_id, principal=principal)


@router.post(
    "/tenants/{tenant_id}/pilot-safe-test-conversation",
    response_model=SafeTestConversationRead,
)
def create_pilot_safe_test_conversation(
    tenant_id: int,
    principal: CurrentPrincipal = Depends(require_permission("conversation.manage")),
    db: Session = Depends(get_db),
) -> SafeTestConversationRead:
    return create_safe_test_conversation(db, tenant_id=tenant_id, principal=principal)


@router.get(
    "/tenants/{tenant_id}/customer-materials/template-package",
    response_model=CustomerMaterialTemplatePackageRead,
)
def get_customer_material_template_package_endpoint(
    tenant_id: int,
    principal: CurrentPrincipal = Depends(require_permission("knowledge.manage")),
    db: Session = Depends(get_db),
) -> CustomerMaterialTemplatePackageRead:
    return get_customer_material_template_package(db, tenant_id=tenant_id, principal=principal)


@router.get(
    "/tenants/{tenant_id}/customer-materials/handoff-bundle",
    response_model=CustomerMaterialHandoffBundleRead,
)
def get_customer_material_handoff_bundle_endpoint(
    tenant_id: int,
    principal: CurrentPrincipal = Depends(require_permission("knowledge.manage")),
    db: Session = Depends(get_db),
) -> CustomerMaterialHandoffBundleRead:
    return get_customer_material_handoff_bundle(db, tenant_id=tenant_id, principal=principal)
