import json
from typing import Any

from sqlalchemy.orm import Session

from app.models import AuditEvent


def add_audit_event(
    db: Session,
    *,
    tenant_id: int,
    action: str,
    resource_type: str,
    actor_id: int | None = None,
    resource_id: str = "",
    payload: dict[str, Any] | None = None,
) -> AuditEvent:
    event = AuditEvent(
        tenant_id=tenant_id,
        actor_id=actor_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        payload=json.dumps(payload or {}, ensure_ascii=False),
    )
    db.add(event)
    return event
