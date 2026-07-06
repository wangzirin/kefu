from datetime import timedelta

from fastapi import HTTPException, status
from sqlalchemy import and_, func, or_, select, update
from sqlalchemy.orm import Session

from app.core.audit import add_audit_event
from app.core.auth import CurrentPrincipal
from app.core.config import get_settings
from app.models import (
    Channel,
    ChannelConnector,
    ChannelDeliveryReceipt,
    OutboxDeliveryJob,
    OutboxDraft,
    OutboxSendAttempt,
)
from app.models.foundation import utc_now
from app.schemas.outbox import (
    OutboxDeliveryJobCreate,
    OutboxDeliveryQueueRunCreate,
    OutboxDeliveryQueueRunRead,
)
from app.services.delivery_failures import attach_delivery_normalization_and_review


READY_TO_SEND = "ready_to_send"
DELIVERY_QUEUE = "delivery_queue"
DELIVERY_QUEUE_WORKER = "delivery_queue_skeleton"
NOT_SENT = "not_sent"
QUEUED = "queued"
LOCKED = "locked"
SUCCEEDED = "succeeded"
FAILED = "failed"
BLOCKED = "blocked"
RETRY_SCHEDULED = "retry_scheduled"
DEAD_LETTER = "dead_letter"


def _next_attempt_number(db: Session, draft_id: int) -> int:
    current = db.scalar(
        select(func.max(OutboxSendAttempt.attempt_number)).where(OutboxSendAttempt.outbox_draft_id == draft_id)
    )
    return (current or 0) + 1


def _get_ready_connector(db: Session, *, tenant_id: int, channel_id: int) -> ChannelConnector | None:
    return db.scalar(
        select(ChannelConnector).where(
            ChannelConnector.tenant_id == tenant_id,
            ChannelConnector.channel_id == channel_id,
            ChannelConnector.status == "ready",
        )
    )


def create_outbox_delivery_job(
    db: Session,
    draft_id: int,
    payload: OutboxDeliveryJobCreate,
    principal: CurrentPrincipal,
) -> OutboxDeliveryJob:
    draft = db.get(OutboxDraft, draft_id)
    if draft is None or draft.tenant_id != principal.tenant.id:
        raise HTTPException(status_code=404, detail="outbox draft not found")
    if draft.status != READY_TO_SEND:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="outbox draft must be ready to send")
    connector = _get_ready_connector(db, tenant_id=draft.tenant_id, channel_id=draft.channel_id)
    if connector is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="channel connector must be configured")

    idempotency_key = payload.idempotency_key or f"outbox_delivery_job:{draft.id}:{connector.id}"
    duplicate = db.scalar(
        select(OutboxDeliveryJob).where(
            OutboxDeliveryJob.tenant_id == draft.tenant_id,
            OutboxDeliveryJob.idempotency_key == idempotency_key,
        )
    )
    if duplicate is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="delivery job already exists")

    settings = get_settings()
    now = utc_now()
    job = OutboxDeliveryJob(
        tenant_id=draft.tenant_id,
        outbox_draft_id=draft.id,
        channel_id=draft.channel_id,
        connector_id=connector.id,
        status=QUEUED,
        priority=payload.priority,
        attempts_count=0,
        max_attempts=payload.max_attempts or settings.outbox_worker_max_attempts,
        locked_by="",
        locked_at=None,
        next_run_at=now,
        idempotency_key=idempotency_key,
        external_write_requested=payload.external_write_requested,
        external_write_permitted=False,
        last_attempt_id=None,
        last_error="",
        dead_letter_reason="",
        created_by_id=principal.user.id,
        created_at=now,
        updated_at=now,
        completed_at=None,
    )
    db.add(job)
    db.flush()
    add_audit_event(
        db,
        tenant_id=job.tenant_id,
        actor_id=principal.user.id,
        action="outbox_delivery_job.created",
        resource_type="outbox_delivery_job",
        resource_id=str(job.id),
        payload={
            "outbox_draft_id": job.outbox_draft_id,
            "channel_id": job.channel_id,
            "connector_id": job.connector_id,
            "external_write_requested": job.external_write_requested,
            "external_write_permitted": False,
        },
    )
    db.commit()
    db.refresh(job)
    return job


def list_outbox_delivery_jobs(
    db: Session,
    *,
    tenant_id: int,
    status_filter: str | None,
    principal: CurrentPrincipal,
) -> list[OutboxDeliveryJob]:
    if tenant_id != principal.tenant.id:
        raise HTTPException(status_code=404, detail="tenant not found")
    query = select(OutboxDeliveryJob).where(OutboxDeliveryJob.tenant_id == tenant_id)
    if status_filter:
        query = query.where(OutboxDeliveryJob.status == status_filter)
    query = query.order_by(OutboxDeliveryJob.created_at.desc(), OutboxDeliveryJob.id.desc())
    return list(db.scalars(query).all())


def _create_delivery_attempt(
    db: Session,
    *,
    job: OutboxDeliveryJob,
    draft: OutboxDraft,
    channel: Channel,
    connector: ChannelConnector,
    principal: CurrentPrincipal,
    worker_id: str,
    blocked_reason: str,
    result_status: str,
    max_attempts: int,
) -> OutboxSendAttempt:
    now = utc_now()
    attempt_number = _next_attempt_number(db, draft.id)
    request_payload = {
        "external_write": False,
        "external_write_requested": job.external_write_requested,
        "external_write_permitted": job.external_write_permitted,
        "queue_job_id": job.id,
        "worker_id": worker_id,
        "channel": {
            "id": channel.id,
            "type": channel.type,
            "status": channel.status,
        },
        "connector": {
            "id": connector.id,
            "provider": connector.provider,
            "mode": connector.mode,
            "external_write_enabled": connector.external_write_enabled,
        },
        "payload_preview": {
            "conversation_id": draft.conversation_id,
            "contact_id": draft.contact_id,
            "text": draft.reply_text,
        },
    }
    response_payload = {
        "external_write": False,
        "external_write_requested": job.external_write_requested,
        "external_write_permitted": job.external_write_permitted,
        "queue_job_id": job.id,
        "worker_id": worker_id,
        "result": result_status,
        "blocked_reason": blocked_reason,
        "retry": {
            "attempt_number": attempt_number,
            "attempts_used_after_this_run": job.attempts_count + 1,
            "max_attempts": max_attempts,
        },
        "message": "delivery queue skeleton recorded; no external provider was called",
    }
    attempt = OutboxSendAttempt(
        tenant_id=job.tenant_id,
        outbox_draft_id=draft.id,
        conversation_id=draft.conversation_id,
        channel_id=draft.channel_id,
        contact_id=draft.contact_id,
        attempt_number=attempt_number,
        delivery_mode=DELIVERY_QUEUE,
        provider=connector.provider,
        status=result_status,
        delivery_status=NOT_SENT,
        idempotency_key=f"delivery_queue:{job.id}:attempt:{attempt_number}",
        external_message_id="",
        request_payload=request_payload,
        response_payload=response_payload,
        error_message=blocked_reason,
        operator_note="delivery queue skeleton; no external provider was called",
        created_by_id=principal.user.id,
        started_at=now,
        finished_at=now,
        sent_at=None,
    )
    db.add(attempt)
    db.flush()
    return attempt


def _record_synthetic_failure_review(
    db: Session,
    *,
    job: OutboxDeliveryJob,
    attempt: OutboxSendAttempt,
    connector: ChannelConnector,
    delivery_status: str,
    error_code: str,
    actor_id: int | None,
) -> None:
    receipt = ChannelDeliveryReceipt(
        tenant_id=job.tenant_id,
        channel_id=job.channel_id,
        connector_id=job.connector_id,
        matched_attempt_id=attempt.id,
        provider=connector.provider,
        external_message_id=f"delivery-job:{job.id}",
        delivery_status=delivery_status,
        provider_event_id=f"delivery-job:{job.id}:{attempt.id}:{error_code}",
        verification_status="internal_queue_synthetic",
        signature_validated=True,
        raw_payload={
            "Status": delivery_status,
            "error_code": error_code,
            "delivery_job_id": job.id,
            "attempt_id": attempt.id,
            "source": "outbox_delivery_queue",
        },
        received_at=utc_now(),
    )
    db.add(receipt)
    db.flush()
    attach_delivery_normalization_and_review(db, receipt=receipt, actor_id=actor_id)


def _finalize_job_after_attempt(
    db: Session,
    *,
    job: OutboxDeliveryJob,
    attempt: OutboxSendAttempt,
    connector: ChannelConnector,
    result_status: str,
    blocked_reason: str,
    max_attempts: int,
    principal: CurrentPrincipal,
) -> None:
    now = utc_now()
    job.attempts_count += 1
    job.last_attempt_id = attempt.id
    job.last_error = blocked_reason
    job.locked_by = ""
    job.locked_at = None
    job.updated_at = now

    if result_status == SUCCEEDED:
        job.status = SUCCEEDED
        job.dead_letter_reason = ""
        job.completed_at = now
    elif result_status == BLOCKED:
        job.status = BLOCKED
        job.dead_letter_reason = blocked_reason
        job.completed_at = now
        _record_synthetic_failure_review(
            db,
            job=job,
            attempt=attempt,
            connector=connector,
            delivery_status="permission_denied",
            error_code=blocked_reason,
            actor_id=principal.user.id,
        )
    elif job.attempts_count >= max_attempts:
        job.status = DEAD_LETTER
        job.dead_letter_reason = blocked_reason
        job.completed_at = now
        _record_synthetic_failure_review(
            db,
            job=job,
            attempt=attempt,
            connector=connector,
            delivery_status=FAILED,
            error_code=blocked_reason,
            actor_id=principal.user.id,
        )
    else:
        job.status = RETRY_SCHEDULED
        job.dead_letter_reason = ""
        job.next_run_at = now
        job.completed_at = None

    add_audit_event(
        db,
        tenant_id=job.tenant_id,
        actor_id=principal.user.id,
        action=f"outbox_delivery_queue.{job.status}",
        resource_type="outbox_delivery_job",
        resource_id=str(job.id),
        payload={
            "outbox_draft_id": job.outbox_draft_id,
            "attempt_id": attempt.id,
            "attempts_count": job.attempts_count,
            "max_attempts": max_attempts,
            "external_write": False,
            "external_write_requested": job.external_write_requested,
            "external_write_permitted": job.external_write_permitted,
            "blocked_reason": blocked_reason,
        },
    )


def _claimable_job_filter(*, tenant_id: int, now, lease_cutoff):
    return and_(
        OutboxDeliveryJob.tenant_id == tenant_id,
        or_(
            and_(
                OutboxDeliveryJob.status.in_([QUEUED, RETRY_SCHEDULED]),
                OutboxDeliveryJob.next_run_at <= now,
            ),
            and_(
                OutboxDeliveryJob.status == LOCKED,
                or_(OutboxDeliveryJob.locked_at.is_(None), OutboxDeliveryJob.locked_at <= lease_cutoff),
            ),
        ),
    )


def _claim_delivery_job(
    db: Session,
    *,
    tenant_id: int,
    job_id: int,
    worker_id: str,
    now,
    lease_cutoff,
) -> OutboxDeliveryJob | None:
    result = db.execute(
        update(OutboxDeliveryJob)
        .where(
            OutboxDeliveryJob.id == job_id,
            _claimable_job_filter(tenant_id=tenant_id, now=now, lease_cutoff=lease_cutoff),
        )
        .values(status=LOCKED, locked_by=worker_id, locked_at=now, updated_at=now)
        .execution_options(synchronize_session=False)
    )
    if result.rowcount != 1:
        return None
    db.flush()
    return db.get(OutboxDeliveryJob, job_id)


def _process_delivery_job(
    db: Session,
    *,
    job: OutboxDeliveryJob,
    payload: OutboxDeliveryQueueRunCreate,
    principal: CurrentPrincipal,
) -> tuple[OutboxDeliveryJob, OutboxSendAttempt]:
    settings = get_settings()
    max_attempts = payload.max_attempts or job.max_attempts or settings.outbox_worker_max_attempts
    job.max_attempts = max_attempts
    db.flush()

    draft = db.get(OutboxDraft, job.outbox_draft_id)
    channel = db.get(Channel, job.channel_id)
    connector = db.get(ChannelConnector, job.connector_id) if job.connector_id else None
    if draft is None or channel is None or connector is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="delivery job has broken references")

    global_external_write_enabled = settings.outbox_external_write_enabled
    connector_external_write_enabled = connector.external_write_enabled
    job.external_write_permitted = (
        job.external_write_requested and global_external_write_enabled and connector_external_write_enabled
    )

    result_status = SUCCEEDED
    blocked_reason = ""
    if job.external_write_requested and not global_external_write_enabled:
        result_status = BLOCKED
        blocked_reason = "external_write_kill_switch"
    elif job.external_write_requested and not connector_external_write_enabled:
        result_status = BLOCKED
        blocked_reason = "connector_external_write_disabled"
    elif channel.status != "active":
        result_status = FAILED
        blocked_reason = "channel_not_active"
    elif job.external_write_requested:
        result_status = BLOCKED
        blocked_reason = "external_sender_not_implemented"

    attempt = _create_delivery_attempt(
        db,
        job=job,
        draft=draft,
        channel=channel,
        connector=connector,
        principal=principal,
        worker_id=payload.worker_id,
        blocked_reason=blocked_reason,
        result_status=result_status,
        max_attempts=max_attempts,
    )
    _finalize_job_after_attempt(
        db,
        job=job,
        attempt=attempt,
        connector=connector,
        result_status=result_status,
        blocked_reason=blocked_reason,
        max_attempts=max_attempts,
        principal=principal,
    )
    return job, attempt


def run_outbox_delivery_queue(
    db: Session,
    *,
    tenant_id: int,
    payload: OutboxDeliveryQueueRunCreate,
    principal: CurrentPrincipal,
) -> OutboxDeliveryQueueRunRead:
    if tenant_id != principal.tenant.id:
        raise HTTPException(status_code=404, detail="tenant not found")
    settings = get_settings()
    batch_size = payload.batch_size or settings.outbox_worker_batch_size
    rate_limit_per_minute = (
        settings.outbox_worker_rate_limit_per_minute
        if payload.rate_limit_per_minute is None
        else payload.rate_limit_per_minute
    )
    now = utc_now()
    lease_cutoff = now - timedelta(seconds=payload.lease_seconds)
    candidates = list(
        db.scalars(
            select(OutboxDeliveryJob)
            .where(_claimable_job_filter(tenant_id=tenant_id, now=now, lease_cutoff=lease_cutoff))
            .order_by(OutboxDeliveryJob.priority.asc(), OutboxDeliveryJob.next_run_at.asc(), OutboxDeliveryJob.id.asc())
            .limit(batch_size)
        ).all()
    )
    active_locked_jobs = list(
        db.scalars(
            select(OutboxDeliveryJob)
            .where(
                OutboxDeliveryJob.tenant_id == tenant_id,
                OutboxDeliveryJob.status == LOCKED,
                OutboxDeliveryJob.locked_at.is_not(None),
                OutboxDeliveryJob.locked_at > lease_cutoff,
            )
            .order_by(OutboxDeliveryJob.locked_at.asc(), OutboxDeliveryJob.id.asc())
            .limit(batch_size)
        ).all()
    )
    capacity = max(min(batch_size, rate_limit_per_minute), 0)
    to_process = candidates[:capacity]
    rate_limited_jobs = candidates[capacity:]
    skipped_job_ids = [job.id for job in active_locked_jobs]
    processed_jobs: list[OutboxDeliveryJob] = []
    attempts: list[OutboxSendAttempt] = []
    for job in to_process:
        claimed_job = _claim_delivery_job(
            db,
            tenant_id=tenant_id,
            job_id=job.id,
            worker_id=payload.worker_id,
            now=now,
            lease_cutoff=lease_cutoff,
        )
        if claimed_job is None:
            skipped_job_ids.append(job.id)
            continue
        processed_job, attempt = _process_delivery_job(db, job=claimed_job, payload=payload, principal=principal)
        processed_jobs.append(processed_job)
        attempts.append(attempt)

    db.commit()
    for job in processed_jobs:
        db.refresh(job)
    for attempt in attempts:
        db.refresh(attempt)

    succeeded = sum(1 for job in processed_jobs if job.status == SUCCEEDED)
    blocked = sum(1 for job in processed_jobs if job.status == BLOCKED)
    retry_scheduled = sum(1 for job in processed_jobs if job.status == RETRY_SCHEDULED)
    dead_lettered = sum(1 for job in processed_jobs if job.status == DEAD_LETTER)
    failed = retry_scheduled + dead_lettered
    return OutboxDeliveryQueueRunRead(
        tenant_id=tenant_id,
        mode=DELIVERY_QUEUE_WORKER,
        scanned=len(candidates) + len(active_locked_jobs),
        processed=len(processed_jobs),
        succeeded=succeeded,
        failed=failed,
        blocked=blocked,
        retry_scheduled=retry_scheduled,
        dead_lettered=dead_lettered,
        rate_limited=len(rate_limited_jobs),
        rate_limited_job_ids=[job.id for job in rate_limited_jobs],
        skipped_job_ids=skipped_job_ids,
        external_write=False,
        kill_switch={
            "global_external_write_enabled": settings.outbox_external_write_enabled,
            "external_write_default": False,
            "real_sender_available": False,
            "lease": {
                "worker_id": payload.worker_id,
                "lease_seconds": payload.lease_seconds,
                "stale_lock_cutoff": lease_cutoff.isoformat(),
                "active_locked_skipped": len(active_locked_jobs),
                "atomic_claim": True,
            },
        },
        attempts=attempts,
        jobs=processed_jobs,
    )
