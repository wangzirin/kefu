from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import WorkerHeartbeat, utc_now
from app.schemas.worker_heartbeats import WorkerHeartbeatRead


def _as_aware(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def compute_worker_health_status(
    heartbeat: WorkerHeartbeat,
    *,
    stale_after_seconds: int,
    now: datetime | None = None,
) -> str:
    if heartbeat.status == "failed":
        return "failed"
    current = _as_aware(now or utc_now())
    last_heartbeat = _as_aware(heartbeat.last_heartbeat_at)
    if last_heartbeat is None:
        return "stale"
    if current - last_heartbeat > timedelta(seconds=stale_after_seconds):
        return "stale"
    return "healthy"


def worker_heartbeat_to_read(
    heartbeat: WorkerHeartbeat,
    *,
    stale_after_seconds: int,
    now: datetime | None = None,
) -> WorkerHeartbeatRead:
    return WorkerHeartbeatRead(
        id=heartbeat.id,
        tenant_id=heartbeat.tenant_id,
        worker_type=heartbeat.worker_type,
        worker_id=heartbeat.worker_id,
        status=heartbeat.status,
        health_status=compute_worker_health_status(
            heartbeat,
            stale_after_seconds=stale_after_seconds,
            now=now,
        ),
        last_heartbeat_at=heartbeat.last_heartbeat_at,
        last_run_record_id=heartbeat.last_run_record_id,
        last_run_mode=heartbeat.last_run_mode,
        last_error=heartbeat.last_error,
        loops_completed=heartbeat.loops_completed,
        metadata_payload=heartbeat.metadata_payload or {},
        created_at=heartbeat.created_at,
        updated_at=heartbeat.updated_at,
    )


def upsert_worker_heartbeat(
    db: Session,
    *,
    tenant_id: int,
    worker_type: str,
    worker_id: str,
    status: str,
    last_run_record_id: int | None = None,
    last_run_mode: str = "",
    last_error: str = "",
    metadata_payload: dict | None = None,
    increment_loops: bool = False,
) -> WorkerHeartbeat:
    now = utc_now()
    heartbeat = db.scalar(
        select(WorkerHeartbeat).where(
            WorkerHeartbeat.tenant_id == tenant_id,
            WorkerHeartbeat.worker_type == worker_type,
            WorkerHeartbeat.worker_id == worker_id,
        )
    )
    if heartbeat is None:
        heartbeat = WorkerHeartbeat(
            tenant_id=tenant_id,
            worker_type=worker_type,
            worker_id=worker_id,
            created_at=now,
        )
        db.add(heartbeat)
    heartbeat.status = status
    heartbeat.last_heartbeat_at = now
    if last_run_record_id is not None:
        heartbeat.last_run_record_id = last_run_record_id
    if last_run_mode:
        heartbeat.last_run_mode = last_run_mode
    heartbeat.last_error = last_error
    if metadata_payload is not None:
        heartbeat.metadata_payload = metadata_payload
    if increment_loops:
        heartbeat.loops_completed = (heartbeat.loops_completed or 0) + 1
    heartbeat.updated_at = now
    db.commit()
    db.refresh(heartbeat)
    return heartbeat


def list_worker_heartbeats(
    db: Session,
    *,
    tenant_id: int,
    stale_after_seconds: int,
    limit: int = 100,
    offset: int = 0,
) -> list[WorkerHeartbeatRead]:
    rows = list(
        db.scalars(
            select(WorkerHeartbeat)
            .where(WorkerHeartbeat.tenant_id == tenant_id)
            .order_by(WorkerHeartbeat.worker_type.asc(), WorkerHeartbeat.worker_id.asc())
            .offset(offset)
            .limit(limit)
        ).all()
    )
    now = utc_now()
    return [
        worker_heartbeat_to_read(heartbeat, stale_after_seconds=stale_after_seconds, now=now)
        for heartbeat in rows
    ]
