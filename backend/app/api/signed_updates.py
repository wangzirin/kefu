from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.tenants import require_tenant
from app.core.auth import CurrentPrincipal
from app.core.rbac import require_permission
from app.db.session import get_db
from app.schemas.signed_updates import (
    SignedUpdateApplyCreate,
    SignedUpdatePreflightCreate,
    SignedUpdatePreflightRead,
    SignedUpdateProgramDryRunCreate,
    SignedUpdateRollbackCreate,
    SignedUpdateStageCreate,
    SignedUpdateStagedPackageRead,
)
from app.services.signed_updates import (
    SignedUpdatePackageConflict,
    SignedUpdatePackageNotFound,
    SignedUpdatePreflightRejected,
    apply_staged_signed_update_package,
    create_program_update_dry_run,
    list_staged_update_packages,
    preflight_signed_update_package,
    rollback_applied_signed_update_package,
    stage_signed_update_package,
)

router = APIRouter(prefix="/api", tags=["signed-updates"])

UPDATES_MANAGE_PERMISSION = "updates.manage"


def _require_same_tenant(tenant_id: int, principal: CurrentPrincipal) -> None:
    if principal.tenant.id != tenant_id:
        raise HTTPException(status_code=404, detail="tenant not found")


@router.post(
    "/tenants/{tenant_id}/signed-update-package/preflights",
    response_model=SignedUpdatePreflightRead,
)
def create_signed_update_package_preflight(
    tenant_id: int,
    payload: SignedUpdatePreflightCreate,
    principal: CurrentPrincipal = Depends(require_permission(UPDATES_MANAGE_PERMISSION)),
    db: Session = Depends(get_db),
) -> dict:
    tenant = require_tenant(db, tenant_id)
    _require_same_tenant(tenant_id, principal)
    return preflight_signed_update_package(db, tenant=tenant, package=payload.package)


@router.post(
    "/tenants/{tenant_id}/signed-update-package/staged",
    response_model=SignedUpdateStagedPackageRead,
    status_code=status.HTTP_201_CREATED,
)
def stage_signed_update_package_for_tenant(
    tenant_id: int,
    payload: SignedUpdateStageCreate,
    principal: CurrentPrincipal = Depends(require_permission(UPDATES_MANAGE_PERMISSION)),
    db: Session = Depends(get_db),
) -> dict:
    tenant = require_tenant(db, tenant_id)
    _require_same_tenant(tenant_id, principal)
    try:
        return stage_signed_update_package(db, tenant=tenant, package=payload.package, actor_id=principal.user.id)
    except SignedUpdatePreflightRejected as exc:
        raise HTTPException(status_code=400, detail=exc.preflight_result) from exc
    except SignedUpdatePackageConflict as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get(
    "/tenants/{tenant_id}/signed-update-package/staged",
    response_model=list[SignedUpdateStagedPackageRead],
)
def list_staged_signed_update_packages(
    tenant_id: int,
    principal: CurrentPrincipal = Depends(require_permission(UPDATES_MANAGE_PERMISSION)),
    db: Session = Depends(get_db),
) -> list[dict]:
    tenant = require_tenant(db, tenant_id)
    _require_same_tenant(tenant_id, principal)
    return list_staged_update_packages(db, tenant=tenant)


@router.post(
    "/signed-update-packages/{signed_update_package_id}/apply",
    response_model=SignedUpdateStagedPackageRead,
)
def apply_signed_update_package(
    signed_update_package_id: int,
    payload: SignedUpdateApplyCreate,
    principal: CurrentPrincipal = Depends(require_permission(UPDATES_MANAGE_PERMISSION)),
    db: Session = Depends(get_db),
) -> dict:
    try:
        return apply_staged_signed_update_package(
            db,
            signed_update_package_id=signed_update_package_id,
            principal=principal,
            reason=payload.reason,
        )
    except SignedUpdatePackageNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except SignedUpdatePackageConflict as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post(
    "/signed-update-packages/{signed_update_package_id}/rollback",
    response_model=SignedUpdateStagedPackageRead,
)
def rollback_signed_update_package(
    signed_update_package_id: int,
    payload: SignedUpdateRollbackCreate,
    principal: CurrentPrincipal = Depends(require_permission(UPDATES_MANAGE_PERMISSION)),
    db: Session = Depends(get_db),
) -> dict:
    try:
        return rollback_applied_signed_update_package(
            db,
            signed_update_package_id=signed_update_package_id,
            principal=principal,
            reason=payload.reason,
        )
    except SignedUpdatePackageNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except SignedUpdatePackageConflict as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post(
    "/signed-update-packages/{signed_update_package_id}/program-dry-run",
    response_model=SignedUpdateStagedPackageRead,
)
def create_signed_update_program_dry_run(
    signed_update_package_id: int,
    payload: SignedUpdateProgramDryRunCreate,
    principal: CurrentPrincipal = Depends(require_permission(UPDATES_MANAGE_PERMISSION)),
    db: Session = Depends(get_db),
) -> dict:
    try:
        return create_program_update_dry_run(
            db,
            signed_update_package_id=signed_update_package_id,
            principal=principal,
            reason=payload.reason,
        )
    except SignedUpdatePackageNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except SignedUpdatePackageConflict as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
