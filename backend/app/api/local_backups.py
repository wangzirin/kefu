from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.tenants import require_tenant
from app.core.auth import CurrentPrincipal
from app.core.rbac import require_permission
from app.db.session import get_db
from app.schemas.local_backups import (
    LocalBackupCreate,
    LocalPostgresBackupManifestRegister,
    LocalPostgresFormalRestoreExecutionDryRunRegister,
    LocalPostgresFormalRestorePreflightRegister,
    LocalPostgresFormalRestoreRunbookRegister,
    LocalPostgresRestoreRehearsalPlanCreate,
    LocalPostgresTempRestoreManifestRegister,
    LocalBackupRead,
    LocalBackupRestoreDryRunCreate,
    LocalBackupRestoreDryRunRead,
    LocalBackupVerifyCreate,
)
from app.services.local_backups import (
    LocalBackupNotFound,
    LocalBackupUnsupported,
    create_local_database_restore_dry_run,
    create_local_database_backup,
    create_postgres_restore_rehearsal_plan,
    list_local_database_backups,
    register_postgres_formal_restore_execution_dry_run_manifest,
    register_postgres_formal_restore_preflight_approval,
    register_postgres_formal_restore_runbook,
    register_postgres_backup_dry_run_manifest,
    register_postgres_temp_restore_rehearsal_manifest,
    verify_local_database_backup,
)

router = APIRouter(prefix="/api", tags=["local-backups"])

UPDATES_MANAGE_PERMISSION = "updates.manage"


def _require_same_tenant(tenant_id: int, principal: CurrentPrincipal) -> None:
    if principal.tenant.id != tenant_id:
        raise HTTPException(status_code=404, detail="tenant not found")


@router.post(
    "/tenants/{tenant_id}/local-backups",
    response_model=LocalBackupRead,
    status_code=status.HTTP_201_CREATED,
)
def create_local_backup(
    tenant_id: int,
    payload: LocalBackupCreate,
    principal: CurrentPrincipal = Depends(require_permission(UPDATES_MANAGE_PERMISSION)),
    db: Session = Depends(get_db),
) -> dict:
    tenant = require_tenant(db, tenant_id)
    _require_same_tenant(tenant_id, principal)
    try:
        return create_local_database_backup(
            db,
            tenant=tenant,
            actor_id=principal.user.id,
            reason=payload.reason,
        )
    except LocalBackupUnsupported as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/tenants/{tenant_id}/local-backups", response_model=list[LocalBackupRead])
def list_local_backups(
    tenant_id: int,
    principal: CurrentPrincipal = Depends(require_permission(UPDATES_MANAGE_PERMISSION)),
    db: Session = Depends(get_db),
) -> list[dict]:
    tenant = require_tenant(db, tenant_id)
    _require_same_tenant(tenant_id, principal)
    return list_local_database_backups(db, tenant=tenant)


@router.post(
    "/tenants/{tenant_id}/local-backups/postgres-dry-run-manifests",
    response_model=LocalBackupRead,
    status_code=status.HTTP_201_CREATED,
)
def register_postgres_backup_manifest(
    tenant_id: int,
    payload: LocalPostgresBackupManifestRegister,
    principal: CurrentPrincipal = Depends(require_permission(UPDATES_MANAGE_PERMISSION)),
    db: Session = Depends(get_db),
) -> dict:
    tenant = require_tenant(db, tenant_id)
    _require_same_tenant(tenant_id, principal)
    try:
        return register_postgres_backup_dry_run_manifest(
            db,
            tenant=tenant,
            actor_id=principal.user.id,
            manifest_payload=payload.manifest_payload,
            reason=payload.reason,
        )
    except LocalBackupUnsupported as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post(
    "/tenants/{tenant_id}/local-backups/postgres-temp-restore-manifests",
    response_model=LocalBackupRead,
    status_code=status.HTTP_201_CREATED,
)
def register_postgres_temp_restore_manifest(
    tenant_id: int,
    payload: LocalPostgresTempRestoreManifestRegister,
    principal: CurrentPrincipal = Depends(require_permission(UPDATES_MANAGE_PERMISSION)),
    db: Session = Depends(get_db),
) -> dict:
    tenant = require_tenant(db, tenant_id)
    _require_same_tenant(tenant_id, principal)
    try:
        return register_postgres_temp_restore_rehearsal_manifest(
            db,
            tenant=tenant,
            actor_id=principal.user.id,
            backup_record_id=payload.backup_record_id,
            manifest_payload=payload.manifest_payload,
            reason=payload.reason,
        )
    except LocalBackupNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except LocalBackupUnsupported as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post(
    "/tenants/{tenant_id}/local-backups/postgres-formal-restore-preflight",
    response_model=LocalBackupRead,
    status_code=status.HTTP_201_CREATED,
)
def register_postgres_formal_restore_preflight(
    tenant_id: int,
    payload: LocalPostgresFormalRestorePreflightRegister,
    principal: CurrentPrincipal = Depends(require_permission(UPDATES_MANAGE_PERMISSION)),
    db: Session = Depends(get_db),
) -> dict:
    tenant = require_tenant(db, tenant_id)
    _require_same_tenant(tenant_id, principal)
    try:
        return register_postgres_formal_restore_preflight_approval(
            db,
            tenant=tenant,
            actor_id=principal.user.id,
            backup_record_id=payload.backup_record_id,
            confirmation_payload=payload.confirmation_payload,
            reason=payload.reason,
        )
    except LocalBackupNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except LocalBackupUnsupported as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post(
    "/tenants/{tenant_id}/local-backups/postgres-formal-restore-execution-dry-run",
    response_model=LocalBackupRead,
    status_code=status.HTTP_201_CREATED,
)
def register_postgres_formal_restore_execution_dry_run(
    tenant_id: int,
    payload: LocalPostgresFormalRestoreExecutionDryRunRegister,
    principal: CurrentPrincipal = Depends(require_permission(UPDATES_MANAGE_PERMISSION)),
    db: Session = Depends(get_db),
) -> dict:
    tenant = require_tenant(db, tenant_id)
    _require_same_tenant(tenant_id, principal)
    try:
        return register_postgres_formal_restore_execution_dry_run_manifest(
            db,
            tenant=tenant,
            actor_id=principal.user.id,
            backup_record_id=payload.backup_record_id,
            manifest_payload=payload.manifest_payload,
            reason=payload.reason,
        )
    except LocalBackupNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except LocalBackupUnsupported as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post(
    "/tenants/{tenant_id}/local-backups/postgres-formal-restore-runbook",
    response_model=LocalBackupRead,
    status_code=status.HTTP_201_CREATED,
)
def register_postgres_formal_restore_runbook_api(
    tenant_id: int,
    payload: LocalPostgresFormalRestoreRunbookRegister,
    principal: CurrentPrincipal = Depends(require_permission(UPDATES_MANAGE_PERMISSION)),
    db: Session = Depends(get_db),
) -> dict:
    tenant = require_tenant(db, tenant_id)
    _require_same_tenant(tenant_id, principal)
    try:
        return register_postgres_formal_restore_runbook(
            db,
            tenant=tenant,
            actor_id=principal.user.id,
            backup_record_id=payload.backup_record_id,
            runbook_payload=payload.runbook_payload,
            reason=payload.reason,
        )
    except LocalBackupNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except LocalBackupUnsupported as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/local-backups/{local_backup_id}/verify", response_model=LocalBackupRead)
def verify_local_backup(
    local_backup_id: int,
    payload: LocalBackupVerifyCreate,
    principal: CurrentPrincipal = Depends(require_permission(UPDATES_MANAGE_PERMISSION)),
    db: Session = Depends(get_db),
) -> dict:
    try:
        return verify_local_database_backup(
            db,
            backup_record_id=local_backup_id,
            tenant=principal.tenant,
            actor_id=principal.user.id,
            reason=payload.reason,
        )
    except LocalBackupNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/local-backups/{local_backup_id}/restore-dry-run", response_model=LocalBackupRestoreDryRunRead)
def create_local_backup_restore_dry_run(
    local_backup_id: int,
    payload: LocalBackupRestoreDryRunCreate,
    principal: CurrentPrincipal = Depends(require_permission(UPDATES_MANAGE_PERMISSION)),
    db: Session = Depends(get_db),
) -> dict:
    try:
        return create_local_database_restore_dry_run(
            db,
            backup_record_id=local_backup_id,
            tenant=principal.tenant,
            actor_id=principal.user.id,
            reason=payload.reason,
        )
    except LocalBackupNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except LocalBackupUnsupported as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post(
    "/local-backups/{local_backup_id}/postgres-restore-rehearsal-plan",
    response_model=LocalBackupRead,
)
def create_postgres_local_backup_restore_rehearsal_plan(
    local_backup_id: int,
    payload: LocalPostgresRestoreRehearsalPlanCreate,
    principal: CurrentPrincipal = Depends(require_permission(UPDATES_MANAGE_PERMISSION)),
    db: Session = Depends(get_db),
) -> dict:
    try:
        return create_postgres_restore_rehearsal_plan(
            db,
            backup_record_id=local_backup_id,
            tenant=principal.tenant,
            actor_id=principal.user.id,
            reason=payload.reason,
        )
    except LocalBackupNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except LocalBackupUnsupported as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
