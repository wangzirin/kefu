from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.tenants import require_tenant
from app.core.auth import CurrentPrincipal
from app.core.rbac import require_permission
from app.db.session import get_db
from app.schemas.diagnostics import (
    DiagnosticBundleRead,
    DiagnosticIntakeCreate,
    DiagnosticIntakeDownloadRead,
    DiagnosticIntakeListRead,
    DiagnosticIntakeRecordRead,
    DiagnosticIntakeStatusUpdate,
    DiagnosticRemediationRequestCreate,
    DiagnosticRemediationRequestDownloadRead,
    DiagnosticRemediationRequestListRead,
    DiagnosticRemediationRequestRead,
    DiagnosticRemediationRequestStatusUpdate,
    DiagnosticRemediationUpdatePlanCreate,
    DiagnosticUploadPackageCreate,
    DiagnosticUploadPackageRead,
    LocalMaintenanceReadinessRead,
)
from app.services.diagnostics import (
    build_diagnostic_bundle,
    build_diagnostic_upload_package,
    create_diagnostic_intake_record,
    create_diagnostic_remediation_request,
    create_diagnostic_remediation_update_plan,
    download_diagnostic_remediation_request,
    download_diagnostic_intake_record,
    list_diagnostic_intake_records,
    list_diagnostic_remediation_requests,
    update_diagnostic_remediation_request_status,
    update_diagnostic_intake_record_status,
)
from app.services.local_maintenance import build_local_maintenance_readiness

router = APIRouter(prefix="/api", tags=["diagnostics"])

OPS_METRICS_READ_PERMISSION = "ops.metrics.read"
UPDATES_MANAGE_PERMISSION = "updates.manage"


def _require_same_tenant(tenant_id: int, principal: CurrentPrincipal) -> None:
    if principal.tenant.id != tenant_id:
        raise HTTPException(status_code=404, detail="tenant not found")


@router.get("/tenants/{tenant_id}/diagnostic-bundle", response_model=DiagnosticBundleRead)
def get_diagnostic_bundle(
    tenant_id: int,
    principal: CurrentPrincipal = Depends(require_permission(OPS_METRICS_READ_PERMISSION)),
    db: Session = Depends(get_db),
) -> dict:
    tenant = require_tenant(db, tenant_id)
    _require_same_tenant(tenant_id, principal)
    return build_diagnostic_bundle(db, tenant=tenant, generated_by_user_id=principal.user.id)


@router.post("/tenants/{tenant_id}/diagnostic-upload-package", response_model=DiagnosticUploadPackageRead)
def create_diagnostic_upload_package(
    tenant_id: int,
    payload: DiagnosticUploadPackageCreate,
    principal: CurrentPrincipal = Depends(require_permission(OPS_METRICS_READ_PERMISSION)),
    db: Session = Depends(get_db),
) -> dict:
    tenant = require_tenant(db, tenant_id)
    _require_same_tenant(tenant_id, principal)
    package = build_diagnostic_upload_package(
        db,
        tenant=tenant,
        generated_by_user_id=principal.user.id,
        authorization_note=payload.authorization_note,
        contact_name=payload.contact_name,
        support_ticket=payload.support_ticket,
    )
    db.commit()
    return package


@router.post("/tenants/{tenant_id}/diagnostic-intake-records", response_model=DiagnosticIntakeRecordRead)
def create_diagnostic_intake(
    tenant_id: int,
    payload: DiagnosticIntakeCreate,
    principal: CurrentPrincipal = Depends(require_permission(OPS_METRICS_READ_PERMISSION)),
    db: Session = Depends(get_db),
) -> dict:
    tenant = require_tenant(db, tenant_id)
    _require_same_tenant(tenant_id, principal)
    record = create_diagnostic_intake_record(
        db,
        tenant=tenant,
        upload_package=payload.upload_package,
        received_by_user_id=principal.user.id,
        source_channel=payload.source_channel,
        processing_note=payload.processing_note,
    )
    db.commit()
    return record


@router.get("/tenants/{tenant_id}/diagnostic-intake-records", response_model=DiagnosticIntakeListRead)
def list_diagnostic_intakes(
    tenant_id: int,
    principal: CurrentPrincipal = Depends(require_permission(OPS_METRICS_READ_PERMISSION)),
    db: Session = Depends(get_db),
) -> dict:
    require_tenant(db, tenant_id)
    _require_same_tenant(tenant_id, principal)
    return list_diagnostic_intake_records(db, tenant_id=tenant_id)


@router.patch("/tenants/{tenant_id}/diagnostic-intake-records/{record_id}", response_model=DiagnosticIntakeRecordRead)
def update_diagnostic_intake(
    tenant_id: int,
    record_id: int,
    payload: DiagnosticIntakeStatusUpdate,
    principal: CurrentPrincipal = Depends(require_permission(UPDATES_MANAGE_PERMISSION)),
    db: Session = Depends(get_db),
) -> dict:
    require_tenant(db, tenant_id)
    _require_same_tenant(tenant_id, principal)
    try:
        record = update_diagnostic_intake_record_status(
            db,
            tenant_id=tenant_id,
            record_id=record_id,
            status=payload.status,
            processing_note=payload.processing_note,
            handled_by_user_id=principal.user.id,
        )
    except LookupError:
        raise HTTPException(status_code=404, detail="diagnostic intake record not found") from None
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    db.commit()
    return record


@router.get(
    "/tenants/{tenant_id}/diagnostic-intake-records/{record_id}/download",
    response_model=DiagnosticIntakeDownloadRead,
)
def download_diagnostic_intake(
    tenant_id: int,
    record_id: int,
    principal: CurrentPrincipal = Depends(require_permission(OPS_METRICS_READ_PERMISSION)),
    db: Session = Depends(get_db),
) -> dict:
    require_tenant(db, tenant_id)
    _require_same_tenant(tenant_id, principal)
    try:
        return download_diagnostic_intake_record(db, tenant_id=tenant_id, record_id=record_id)
    except LookupError:
        raise HTTPException(status_code=404, detail="diagnostic intake record not found") from None


@router.post(
    "/tenants/{tenant_id}/diagnostic-intake-records/{record_id}/remediation-requests",
    response_model=DiagnosticRemediationRequestRead,
)
def create_diagnostic_remediation(
    tenant_id: int,
    record_id: int,
    payload: DiagnosticRemediationRequestCreate,
    principal: CurrentPrincipal = Depends(require_permission(UPDATES_MANAGE_PERMISSION)),
    db: Session = Depends(get_db),
) -> dict:
    require_tenant(db, tenant_id)
    _require_same_tenant(tenant_id, principal)
    try:
        request = create_diagnostic_remediation_request(
            db,
            tenant_id=tenant_id,
            intake_record_id=record_id,
            created_by_user_id=principal.user.id,
            request_type=payload.request_type,
            title=payload.title,
            summary=payload.summary,
            priority=payload.priority,
        )
    except LookupError:
        raise HTTPException(status_code=404, detail="diagnostic intake record not found") from None
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    db.commit()
    return request


@router.get(
    "/tenants/{tenant_id}/diagnostic-remediation-requests",
    response_model=DiagnosticRemediationRequestListRead,
)
def list_diagnostic_remediations(
    tenant_id: int,
    principal: CurrentPrincipal = Depends(require_permission(OPS_METRICS_READ_PERMISSION)),
    db: Session = Depends(get_db),
) -> dict:
    require_tenant(db, tenant_id)
    _require_same_tenant(tenant_id, principal)
    return list_diagnostic_remediation_requests(db, tenant_id=tenant_id)


@router.patch(
    "/tenants/{tenant_id}/diagnostic-remediation-requests/{request_id}",
    response_model=DiagnosticRemediationRequestRead,
)
def update_diagnostic_remediation(
    tenant_id: int,
    request_id: int,
    payload: DiagnosticRemediationRequestStatusUpdate,
    principal: CurrentPrincipal = Depends(require_permission(UPDATES_MANAGE_PERMISSION)),
    db: Session = Depends(get_db),
) -> dict:
    require_tenant(db, tenant_id)
    _require_same_tenant(tenant_id, principal)
    try:
        request = update_diagnostic_remediation_request_status(
            db,
            tenant_id=tenant_id,
            request_id=request_id,
            status=payload.status,
            summary=payload.summary,
            updated_by_user_id=principal.user.id,
        )
    except LookupError:
        raise HTTPException(status_code=404, detail="diagnostic remediation request not found") from None
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    db.commit()
    return request


@router.post(
    "/tenants/{tenant_id}/diagnostic-remediation-requests/{request_id}/signed-update-plan",
    response_model=DiagnosticRemediationRequestRead,
)
def create_diagnostic_remediation_signed_update_plan(
    tenant_id: int,
    request_id: int,
    payload: DiagnosticRemediationUpdatePlanCreate,
    principal: CurrentPrincipal = Depends(require_permission(UPDATES_MANAGE_PERMISSION)),
    db: Session = Depends(get_db),
) -> dict:
    require_tenant(db, tenant_id)
    _require_same_tenant(tenant_id, principal)
    try:
        request = create_diagnostic_remediation_update_plan(
            db,
            tenant_id=tenant_id,
            request_id=request_id,
            signed_update_package_id=payload.signed_update_package_id,
            updated_by_user_id=principal.user.id,
            operator_note=payload.operator_note,
        )
    except LookupError:
        raise HTTPException(
            status_code=404,
            detail="diagnostic remediation request or signed update package not found",
        ) from None
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    db.commit()
    return request


@router.get(
    "/tenants/{tenant_id}/diagnostic-remediation-requests/{request_id}/download",
    response_model=DiagnosticRemediationRequestDownloadRead,
)
def download_diagnostic_remediation(
    tenant_id: int,
    request_id: int,
    principal: CurrentPrincipal = Depends(require_permission(UPDATES_MANAGE_PERMISSION)),
    db: Session = Depends(get_db),
) -> dict:
    require_tenant(db, tenant_id)
    _require_same_tenant(tenant_id, principal)
    try:
        return download_diagnostic_remediation_request(db, tenant_id=tenant_id, request_id=request_id)
    except LookupError:
        raise HTTPException(status_code=404, detail="diagnostic remediation request not found") from None


@router.get(
    "/tenants/{tenant_id}/local-maintenance/readiness",
    response_model=LocalMaintenanceReadinessRead,
)
def get_local_maintenance_readiness(
    tenant_id: int,
    principal: CurrentPrincipal = Depends(require_permission(UPDATES_MANAGE_PERMISSION)),
    db: Session = Depends(get_db),
) -> dict:
    tenant = require_tenant(db, tenant_id)
    _require_same_tenant(tenant_id, principal)
    return build_local_maintenance_readiness(db, tenant=tenant)
