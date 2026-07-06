from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.tenants import require_tenant
from app.core.auth import CurrentPrincipal
from app.core.rbac import require_permission
from app.db.session import get_db
from app.models import TrustedInboundWorkerRunRecord
from app.schemas.inbound_worker import (
    TrustedInboundWorkerLoopRunCreate,
    TrustedInboundWorkerLoopRunRead,
    TrustedInboundWorkerRunCreate,
    TrustedInboundWorkerRunRead,
    TrustedInboundWorkerRunRecordRead,
)
from app.workers.trusted_inbound_loop import run_trusted_inbound_worker_loop
from app.workers.trusted_inbound_orchestrator import run_trusted_inbound_worker

router = APIRouter(prefix="/api", tags=["trusted-inbound-worker"])

CHANNEL_READ_PERMISSION = "channel.read"
CHANNEL_MANAGE_PERMISSION = "channel.manage"


def _require_same_tenant(tenant_id: int, principal: CurrentPrincipal) -> None:
    if principal.tenant.id != tenant_id:
        raise HTTPException(status_code=404, detail="tenant not found")


@router.post(
    "/tenants/{tenant_id}/trusted-inbound-worker-runs",
    response_model=TrustedInboundWorkerRunRead,
    status_code=status.HTTP_201_CREATED,
)
def create_trusted_inbound_worker_run(
    tenant_id: int,
    payload: TrustedInboundWorkerRunCreate,
    principal: CurrentPrincipal = Depends(require_permission(CHANNEL_MANAGE_PERMISSION)),
    db: Session = Depends(get_db),
) -> TrustedInboundWorkerRunRead:
    require_tenant(db, tenant_id)
    _require_same_tenant(tenant_id, principal)
    return run_trusted_inbound_worker(db, tenant_id=tenant_id, payload=payload, principal=principal)


@router.post(
    "/tenants/{tenant_id}/trusted-inbound-worker-loop-runs",
    response_model=TrustedInboundWorkerLoopRunRead,
    status_code=status.HTTP_201_CREATED,
)
def create_trusted_inbound_worker_loop_run(
    tenant_id: int,
    payload: TrustedInboundWorkerLoopRunCreate,
    principal: CurrentPrincipal = Depends(require_permission(CHANNEL_MANAGE_PERMISSION)),
    db: Session = Depends(get_db),
) -> TrustedInboundWorkerLoopRunRead:
    require_tenant(db, tenant_id)
    _require_same_tenant(tenant_id, principal)
    return run_trusted_inbound_worker_loop(db, tenant_id=tenant_id, payload=payload, principal=principal)


@router.get(
    "/tenants/{tenant_id}/trusted-inbound-worker-runs",
    response_model=list[TrustedInboundWorkerRunRecordRead],
)
def list_trusted_inbound_worker_runs(
    tenant_id: int,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    principal: CurrentPrincipal = Depends(require_permission(CHANNEL_READ_PERMISSION)),
    db: Session = Depends(get_db),
) -> list[TrustedInboundWorkerRunRecord]:
    require_tenant(db, tenant_id)
    _require_same_tenant(tenant_id, principal)
    return list(
        db.scalars(
            select(TrustedInboundWorkerRunRecord)
            .where(TrustedInboundWorkerRunRecord.tenant_id == tenant_id)
            .order_by(TrustedInboundWorkerRunRecord.started_at.desc(), TrustedInboundWorkerRunRecord.id.desc())
            .offset(offset)
            .limit(limit)
        ).all()
    )
