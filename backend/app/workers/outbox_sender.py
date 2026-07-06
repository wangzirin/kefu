from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.audit import add_audit_event
from app.core.auth import CurrentPrincipal
from app.core.config import get_settings
from app.models import Channel, OutboxDraft, OutboxSendAttempt, WorkflowRun
from app.models.foundation import utc_now
from app.schemas.outbox import OutboxWorkerRunCreate, OutboxWorkerRunRead


READY_TO_SEND = "ready_to_send"
NOT_SENT = "not_sent"
DRY_RUN = "dry_run"
DRY_RUN_WORKER = "dry_run_worker"
SUCCEEDED = "succeeded"
FAILED = "failed"


def _attempt_count(db: Session, draft_id: int) -> int:
    return db.scalar(select(func.count(OutboxSendAttempt.id)).where(OutboxSendAttempt.outbox_draft_id == draft_id)) or 0


def _has_worker_success(db: Session, draft_id: int) -> bool:
    existing = db.scalar(
        select(OutboxSendAttempt.id).where(
            OutboxSendAttempt.outbox_draft_id == draft_id,
            OutboxSendAttempt.provider == DRY_RUN_WORKER,
            OutboxSendAttempt.status == SUCCEEDED,
        )
    )
    return existing is not None


def _next_attempt_number(db: Session, draft_id: int) -> int:
    current = db.scalar(
        select(func.max(OutboxSendAttempt.attempt_number)).where(OutboxSendAttempt.outbox_draft_id == draft_id)
    )
    return (current or 0) + 1


def _update_workflow_worker_state(db: Session, *, draft: OutboxDraft, attempt: OutboxSendAttempt) -> None:
    if draft.source_workflow_run_id is None:
        return
    run = db.get(WorkflowRun, draft.source_workflow_run_id)
    if run is None:
        return
    run.state_payload = {
        **(run.state_payload or {}),
        "outbox_worker": {
            "mode": DRY_RUN_WORKER,
            "outbox_draft_id": draft.id,
            "attempt_id": attempt.id,
            "attempt_number": attempt.attempt_number,
            "status": attempt.status,
            "delivery_status": attempt.delivery_status,
            "external_write": False,
            "receipt_status": "not_available",
            "retry_next_action": attempt.response_payload.get("retry_placeholder", {}).get("next_action", ""),
            "finished_at": attempt.finished_at.isoformat() if attempt.finished_at else "",
        },
        "outbox_send_attempt": {
            "id": attempt.id,
            "outbox_draft_id": attempt.outbox_draft_id,
            "attempt_number": attempt.attempt_number,
            "delivery_mode": attempt.delivery_mode,
            "provider": attempt.provider,
            "status": attempt.status,
            "delivery_status": attempt.delivery_status,
            "external_write": False,
            "finished_at": attempt.finished_at.isoformat() if attempt.finished_at else "",
        },
    }


def _create_worker_attempt(
    db: Session,
    *,
    draft: OutboxDraft,
    channel: Channel,
    principal: CurrentPrincipal,
    max_attempts: int,
    rate_limit_per_minute: int,
    batch_size: int,
) -> OutboxSendAttempt:
    attempt_number = _next_attempt_number(db, draft.id)
    now = utc_now()
    channel_active = channel.status == "active"
    status = SUCCEEDED if channel_active else FAILED
    error_message = "" if channel_active else "channel is not active"
    attempts_remaining = max(max_attempts - attempt_number, 0)
    retry_next_action = "none" if status == SUCCEEDED else ("retry_later" if attempts_remaining > 0 else "manual_review")
    request_payload = {
        "dry_run": True,
        "worker": DRY_RUN_WORKER,
        "external_write": False,
        "channel_id": draft.channel_id,
        "channel_type": channel.type,
        "channel_status": channel.status,
        "conversation_id": draft.conversation_id,
        "contact_id": draft.contact_id,
        "reply_text": draft.reply_text,
        "rate_limit": {
            "per_minute": rate_limit_per_minute,
            "batch_size": batch_size,
        },
    }
    response_payload = {
        "dry_run": True,
        "worker": DRY_RUN_WORKER,
        "external_write": False,
        "would_send": channel_active,
        "provider": DRY_RUN_WORKER,
        "result": status,
        "receipt_placeholder": {
            "status": "not_available",
            "external_message_id": "",
            "message": "no official channel provider was called",
        },
        "retry_placeholder": {
            "next_action": retry_next_action,
            "max_attempts": max_attempts,
            "attempts_used": attempt_number,
            "attempts_remaining": attempts_remaining,
        },
    }
    attempt = OutboxSendAttempt(
        tenant_id=draft.tenant_id,
        outbox_draft_id=draft.id,
        conversation_id=draft.conversation_id,
        channel_id=draft.channel_id,
        contact_id=draft.contact_id,
        attempt_number=attempt_number,
        delivery_mode=DRY_RUN,
        provider=DRY_RUN_WORKER,
        status=status,
        delivery_status=NOT_SENT,
        idempotency_key=f"outbox_worker:{draft.id}:attempt:{attempt_number}",
        external_message_id="",
        request_payload=request_payload,
        response_payload=response_payload,
        error_message=error_message,
        operator_note="worker dry-run; no external provider was called",
        created_by_id=principal.user.id,
        started_at=now,
        finished_at=now,
        sent_at=None,
    )
    db.add(attempt)
    db.flush()
    draft.updated_at = now
    _update_workflow_worker_state(db, draft=draft, attempt=attempt)
    add_audit_event(
        db,
        tenant_id=attempt.tenant_id,
        actor_id=principal.user.id,
        action=f"outbox_worker.dry_run_{status}",
        resource_type="outbox_send_attempt",
        resource_id=str(attempt.id),
        payload={
            "outbox_draft_id": attempt.outbox_draft_id,
            "conversation_id": attempt.conversation_id,
            "status": attempt.status,
            "delivery_status": attempt.delivery_status,
            "external_write": False,
            "retry_next_action": retry_next_action,
            "receipt_status": "not_available",
        },
    )
    return attempt


def run_outbox_worker_dry_run(
    db: Session,
    *,
    tenant_id: int,
    payload: OutboxWorkerRunCreate,
    principal: CurrentPrincipal,
) -> OutboxWorkerRunRead:
    settings = get_settings()
    batch_size = payload.batch_size or settings.outbox_worker_batch_size
    rate_limit_per_minute = (
        settings.outbox_worker_rate_limit_per_minute
        if payload.rate_limit_per_minute is None
        else payload.rate_limit_per_minute
    )
    max_attempts = payload.max_attempts or settings.outbox_worker_max_attempts
    raw_candidates = list(
        db.scalars(
            select(OutboxDraft)
            .where(OutboxDraft.tenant_id == tenant_id, OutboxDraft.status == READY_TO_SEND)
            .order_by(OutboxDraft.confirmed_at.asc(), OutboxDraft.id.asc())
            .limit(batch_size)
        ).all()
    )

    candidates: list[OutboxDraft] = []
    skipped_draft_ids: list[int] = []
    for draft in raw_candidates:
        if _has_worker_success(db, draft.id) or _attempt_count(db, draft.id) >= max_attempts:
            skipped_draft_ids.append(draft.id)
            continue
        candidates.append(draft)

    capacity = max(min(batch_size, rate_limit_per_minute), 0)
    to_process = candidates[:capacity]
    rate_limited_draft_ids = [draft.id for draft in candidates[capacity:]]
    attempts: list[OutboxSendAttempt] = []
    for draft in to_process:
        channel = db.get(Channel, draft.channel_id)
        if channel is None or channel.tenant_id != draft.tenant_id:
            continue
        attempts.append(
            _create_worker_attempt(
                db,
                draft=draft,
                channel=channel,
                principal=principal,
                max_attempts=max_attempts,
                rate_limit_per_minute=rate_limit_per_minute,
                batch_size=batch_size,
            )
        )

    db.commit()
    for attempt in attempts:
        db.refresh(attempt)

    succeeded = sum(1 for attempt in attempts if attempt.status == SUCCEEDED)
    failed = sum(1 for attempt in attempts if attempt.status == FAILED)
    return OutboxWorkerRunRead(
        tenant_id=tenant_id,
        mode=DRY_RUN_WORKER,
        scanned=len(candidates),
        processed=len(attempts),
        succeeded=succeeded,
        failed=failed,
        rate_limited=len(rate_limited_draft_ids),
        rate_limited_draft_ids=rate_limited_draft_ids,
        skipped_draft_ids=skipped_draft_ids,
        external_write=False,
        rate_limit={
            "per_minute": rate_limit_per_minute,
            "batch_size": batch_size,
            "max_attempts": max_attempts,
        },
        attempts=attempts,
    )
