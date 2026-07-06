from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.tenants import require_tenant
from app.core.auth import CurrentPrincipal, require_current_principal
from app.db.session import get_db
from app.schemas.worker_heartbeats import WorkerHeartbeatRead
from app.services.worker_heartbeats import list_worker_heartbeats

router = APIRouter(prefix="/api", tags=["worker-heartbeats"])


def _require_same_tenant(tenant_id: int, principal: CurrentPrincipal) -> None:
    if principal.tenant.id != tenant_id:
        raise HTTPException(status_code=404, detail="tenant not found")


@router.get(
    "/tenants/{tenant_id}/worker-heartbeats",
    response_model=list[WorkerHeartbeatRead],
)
def list_tenant_worker_heartbeats(
    tenant_id: int,
    stale_after_seconds: int = Query(default=120, ge=1, le=3600),
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    principal: CurrentPrincipal = Depends(require_current_principal),
    db: Session = Depends(get_db),
) -> list[WorkerHeartbeatRead]:
    require_tenant(db, tenant_id)
    _require_same_tenant(tenant_id, principal)
    return list_worker_heartbeats(
        db,
        tenant_id=tenant_id,
        stale_after_seconds=stale_after_seconds,
        limit=limit,
        offset=offset,
    )
