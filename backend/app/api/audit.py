from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.auth import CurrentPrincipal
from app.core.rbac import require_permission
from app.db.session import get_db
from app.models import AuditEvent
from app.schemas.foundation import AuditEventRead

router = APIRouter(prefix="/api", tags=["audit"])


@router.get("/tenants/{tenant_id}/audit-events", response_model=list[AuditEventRead])
def list_audit_events(
    tenant_id: int,
    limit: int = Query(default=50, ge=1, le=100),
    principal: CurrentPrincipal = Depends(require_permission("audit.events.read")),
    db: Session = Depends(get_db),
) -> list[AuditEvent]:
    if principal.tenant.id != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="cannot read audit events across tenants",
        )
    query = (
        select(AuditEvent)
        .where(AuditEvent.tenant_id == tenant_id)
        .order_by(AuditEvent.id.desc())
        .limit(limit)
    )
    return list(db.scalars(query).all())
