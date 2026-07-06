from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import and_, or_, select, update
from sqlalchemy.orm import Session

from app.core.audit import add_audit_event
from app.core.auth import CurrentPrincipal
from app.models import (
    Conversation,
    ConversationEvent,
    Message,
    ReplyDecision,
    TrustedInboundMessageJob,
    TrustedInboundWorkerRunRecord,
    WorkflowRun,
    utc_now,
)
from app.schemas.inbound_worker import (
    TrustedInboundWorkerItemRead,
    TrustedInboundWorkerRunCreate,
    TrustedInboundWorkerRunRead,
)
from app.schemas.reply_decisions import ReplyDecisionCreate
from app.schemas.workflows import HumanReviewTaskCreate, WorkflowCheckpointCreate, WorkflowRunCreate
from app.services.knowledge import create_knowledge_gap_from_reply_decision
from app.services.reply_decisions import create_reply_decision_for_message
from app.services.workflows import add_checkpoint, complete_workflow_run, create_human_review_task, create_workflow_run


WORKER_MODE = "trusted_inbound_orchestrator"
TRUSTED_INBOUND_EVENT_TYPE = "message.inbound.trusted_webhook"
JOB_QUEUED = "queued"
JOB_LOCKED = "locked"
JOB_SUCCEEDED = "succeeded"
JOB_FAILED = "failed"


def _payload_from_event(event: ConversationEvent) -> dict[str, Any]:
    try:
        value = json.loads(event.payload or "{}")
    except json.JSONDecodeError:
        return {}
    return value if isinstance(value, dict) else {}


def _workflow_idempotency_key(message_id: int) -> str:
    return f"trusted_inbound_message:{message_id}:reply_orchestration"


def _reply_decision_idempotency_key(message_id: int) -> str:
    return f"trusted_inbound_message:{message_id}:reply_decision:v1"


def _as_aware(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def _existing_workflow_run(db: Session, *, tenant_id: int, message_id: int, idempotency_key: str) -> WorkflowRun | None:
    return db.scalar(
        select(WorkflowRun)
        .where(
            WorkflowRun.tenant_id == tenant_id,
            WorkflowRun.trigger_message_id == message_id,
            WorkflowRun.idempotency_key == idempotency_key,
        )
        .order_by(WorkflowRun.id.asc())
    )


def _candidate_messages(db: Session, *, tenant_id: int, batch_size: int) -> list[Message]:
    events = list(
        db.scalars(
            select(ConversationEvent)
            .join(Conversation, Conversation.id == ConversationEvent.conversation_id)
            .where(
                Conversation.tenant_id == tenant_id,
                ConversationEvent.event_type == TRUSTED_INBOUND_EVENT_TYPE,
            )
            .order_by(ConversationEvent.id.asc())
            .limit(batch_size)
        ).all()
    )
    messages: list[Message] = []
    seen_message_ids: set[int] = set()
    for event in events:
        payload = _payload_from_event(event)
        message_id = int(payload.get("trusted_message_id") or 0)
        if message_id <= 0 or message_id in seen_message_ids:
            continue
        message = db.get(Message, message_id)
        if message is None or message.conversation_id != event.conversation_id or message.direction != "inbound":
            continue
        conversation = db.get(Conversation, message.conversation_id)
        if conversation is None or conversation.tenant_id != tenant_id:
            continue
        messages.append(message)
        seen_message_ids.add(message.id)
    return messages


def _create_run_record(
    db: Session,
    *,
    tenant_id: int,
    payload: TrustedInboundWorkerRunCreate,
    principal: CurrentPrincipal,
) -> TrustedInboundWorkerRunRecord:
    record = TrustedInboundWorkerRunRecord(
        tenant_id=tenant_id,
        worker_id=payload.worker_id,
        mode=WORKER_MODE,
        status="running",
        batch_size=payload.batch_size,
        rate_limit_per_minute=payload.rate_limit_per_minute,
        lease_seconds=payload.lease_seconds,
        external_write=False,
        request_payload={
            "batch_size": payload.batch_size,
            "rate_limit_per_minute": payload.rate_limit_per_minute,
            "mode": payload.mode,
            "risk_level": payload.risk_level,
            "intent": payload.intent,
            "knowledge_top_k": payload.knowledge_top_k,
            "model_provider": payload.model_provider,
            "external_write": False,
        },
        created_by_id=principal.user.id,
        started_at=utc_now(),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def _finish_run_record(
    db: Session,
    *,
    run_record_id: int,
    summary: TrustedInboundWorkerRunRead,
) -> None:
    record = db.get(TrustedInboundWorkerRunRecord, run_record_id)
    if record is None:
        return
    record.status = "failed" if summary.failed and not summary.succeeded else "completed"
    record.scanned = summary.scanned
    record.processed = summary.processed
    record.succeeded = summary.succeeded
    record.failed = summary.failed
    record.skipped = summary.skipped
    record.rate_limited = summary.rate_limited
    record.external_write = summary.external_write
    record.result_payload = {
        "lease": summary.lease,
        "skipped_message_ids": summary.skipped_message_ids,
        "rate_limited_message_ids": summary.rate_limited_message_ids,
        "items": [item.model_dump(mode="json") for item in summary.items],
    }
    record.finished_at = utc_now()
    db.commit()


def _ensure_message_job(
    db: Session,
    *,
    tenant_id: int,
    message: Message,
    idempotency_key: str,
) -> TrustedInboundMessageJob:
    job = db.scalar(
        select(TrustedInboundMessageJob).where(
            TrustedInboundMessageJob.tenant_id == tenant_id,
            TrustedInboundMessageJob.message_id == message.id,
        )
    )
    if job is not None:
        return job
    job = TrustedInboundMessageJob(
        tenant_id=tenant_id,
        conversation_id=message.conversation_id,
        message_id=message.id,
        idempotency_key=idempotency_key,
        status=JOB_QUEUED,
        created_at=utc_now(),
        updated_at=utc_now(),
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def _claimable_message_job_filter(*, tenant_id: int, lease_cutoff: datetime):
    return and_(
        TrustedInboundMessageJob.tenant_id == tenant_id,
        or_(
            TrustedInboundMessageJob.status.in_([JOB_QUEUED, JOB_FAILED]),
            and_(
                TrustedInboundMessageJob.status == JOB_LOCKED,
                or_(
                    TrustedInboundMessageJob.locked_at.is_(None),
                    TrustedInboundMessageJob.locked_at <= lease_cutoff,
                ),
            ),
        ),
    )


def _claim_message_job(
    db: Session,
    *,
    tenant_id: int,
    job: TrustedInboundMessageJob,
    worker_id: str,
    run_record_id: int,
    now: datetime,
    lease_cutoff: datetime,
) -> tuple[TrustedInboundMessageJob | None, str]:
    if job.status == JOB_SUCCEEDED:
        return None, "already_succeeded"
    locked_at = _as_aware(job.locked_at)
    if job.status == JOB_LOCKED and locked_at is not None and locked_at > lease_cutoff:
        return None, "fresh_locked"
    claim_kind = "claimed"
    if job.status == JOB_LOCKED:
        claim_kind = "stale_reclaimed"
    elif job.status == JOB_FAILED:
        claim_kind = "failed_replayed"
    result = db.execute(
        update(TrustedInboundMessageJob)
        .where(
            TrustedInboundMessageJob.id == job.id,
            _claimable_message_job_filter(tenant_id=tenant_id, lease_cutoff=lease_cutoff),
        )
        .values(
            status=JOB_LOCKED,
            locked_by=worker_id,
            locked_at=now,
            attempts_count=TrustedInboundMessageJob.attempts_count + 1,
            last_run_record_id=run_record_id,
            last_error="",
            updated_at=now,
            completed_at=None,
        )
        .execution_options(synchronize_session=False)
    )
    if result.rowcount != 1:
        db.rollback()
        return None, "claim_lost"
    db.commit()
    claimed = db.get(TrustedInboundMessageJob, job.id)
    return claimed, claim_kind


def _mark_job_succeeded(
    db: Session,
    *,
    job_id: int,
    workflow_run_id: int,
    human_review_task_id: int | None,
) -> None:
    job = db.get(TrustedInboundMessageJob, job_id)
    if job is None:
        return
    now = utc_now()
    job.status = JOB_SUCCEEDED
    job.workflow_run_id = workflow_run_id
    job.human_review_task_id = human_review_task_id
    job.last_error = ""
    job.updated_at = now
    job.completed_at = now
    db.commit()


def _mark_job_failed(
    db: Session,
    *,
    job_id: int,
    error_message: str,
) -> None:
    job = db.get(TrustedInboundMessageJob, job_id)
    if job is None:
        return
    now = utc_now()
    job.status = JOB_FAILED
    job.last_error = error_message[:1000]
    job.updated_at = now
    job.completed_at = None


def _mark_success_state(
    db: Session,
    *,
    workflow_run_id: int,
    message: Message,
    principal: CurrentPrincipal,
) -> WorkflowRun:
    run = db.get(WorkflowRun, workflow_run_id)
    if run is None:
        raise RuntimeError("workflow run disappeared after orchestration")
    run.state_payload = {
        **(run.state_payload or {}),
        "trusted_inbound_worker": {
            "worker": WORKER_MODE,
            "message_id": message.id,
            "conversation_id": message.conversation_id,
            "external_write": False,
            "next_action": "human_review_or_outbox_after_operator_decision",
        },
    }
    add_audit_event(
        db,
        tenant_id=principal.tenant.id,
        actor_id=principal.user.id,
        action="trusted_inbound_worker.orchestrated",
        resource_type="workflow_run",
        resource_id=str(run.id),
        payload={
            "message_id": message.id,
            "conversation_id": message.conversation_id,
            "idempotency_key": run.idempotency_key,
            "external_write": False,
        },
    )
    db.commit()
    db.refresh(run)
    return run


def _decision_state_payload(decision: ReplyDecision, *, next_action: str, knowledge_gap_id: int | None = None) -> dict:
    knowledge_matches = []
    if decision.object_knowledge_card_id:
        knowledge_matches.append(
            {
                "source_kind": "object_knowledge_card",
                "business_object_id": decision.business_object_id,
                "object_knowledge_card_id": decision.object_knowledge_card_id,
                "score": decision.confidence,
                "matched_terms": decision.matched_terms,
            }
        )
    return {
        "source": "trusted_inbound_worker",
        "message_id": decision.message_id,
        "conversation_id": decision.conversation_id,
        "intent": "customer_reply",
        "reply_decision_id": decision.id,
        "reply_decision": {
            "state": decision.state,
            "reason": decision.reason,
            "confidence": decision.confidence,
            "delivery_mode": decision.delivery_mode,
            "business_object_id": decision.business_object_id,
            "object_knowledge_card_id": decision.object_knowledge_card_id,
            "matched_terms": decision.matched_terms,
            "external_write_allowed": decision.external_write_allowed,
        },
        "retrieved_knowledge_count": 1 if decision.object_knowledge_card_id else 0,
        "confidence": decision.confidence,
        "risk_level": "high" if decision.state == "blocked_by_policy" else "medium",
        "draft_reply": decision.draft_reply,
        "draft_source": "object_knowledge_card" if decision.object_knowledge_card_id else "reply_decision",
        "retrieval_mode": "business_object_state_machine",
        "retrieval_engine": "object_knowledge_card_v1",
        "knowledge_matches": knowledge_matches,
        "model_call": None,
        "auto_reply_threshold": 0.72,
        "knowledge_gap_id": knowledge_gap_id,
        "trusted_inbound_worker": {
            "worker": WORKER_MODE,
            "message_id": decision.message_id,
            "conversation_id": decision.conversation_id,
            "external_write": False,
            "next_action": next_action,
        },
        "outbox_pre_gate": {
            "eligible": decision.state == "auto_reply_ready",
            "external_write_allowed": decision.external_write_allowed,
            "external_write": False,
            "reason": "external_write_closed" if decision.state == "auto_reply_ready" else decision.reason,
        },
    }


def _create_decision_workflow(
    db: Session,
    *,
    message: Message,
    decision: ReplyDecision,
    idempotency_key: str,
    principal: CurrentPrincipal,
) -> WorkflowRun:
    run = create_workflow_run(
        db,
        message.conversation_id,
        WorkflowRunCreate(
            trigger_message_id=message.id,
            workflow_type="customer_reply_decision",
            current_step="reply_decision",
            idempotency_key=idempotency_key,
            state_payload=_decision_state_payload(decision, next_action="evaluate_reply_decision"),
        ),
        principal,
    )
    decision.workflow_run_id = run.id
    db.commit()
    db.refresh(decision)
    return run


def _complete_decision_workflow(
    db: Session,
    *,
    run: WorkflowRun,
    decision: ReplyDecision,
    principal: CurrentPrincipal,
    step_name: str,
    status_text: str,
    next_action: str,
    knowledge_gap_id: int | None = None,
) -> WorkflowRun:
    state_payload = _decision_state_payload(decision, next_action=next_action, knowledge_gap_id=knowledge_gap_id)
    add_checkpoint(
        db,
        run.id,
        WorkflowCheckpointCreate(
            step_name=step_name,
            status=status_text,
            state_payload=state_payload,
            input_summary=f"reply_decision={decision.state}, reason={decision.reason}",
            output_summary=next_action,
        ),
        principal,
    )
    if status_text == "waiting_human":
        db.refresh(run)
        return run
    return complete_workflow_run(
        db,
        run.id,
        current_step=step_name,
        state_payload=state_payload,
        principal=principal,
    )


def _run_reply_decision_branch(
    db: Session,
    *,
    message: Message,
    workflow_idempotency_key: str,
    principal: CurrentPrincipal,
) -> tuple[WorkflowRun, int | None, ReplyDecision, int | None, str, str, str]:
    decision = create_reply_decision_for_message(
        db,
        message.id,
        ReplyDecisionCreate(
            idempotency_key=_reply_decision_idempotency_key(message.id),
            external_write_allowed=False,
            force_draft_only=True,
        ),
        principal,
    )
    run = _create_decision_workflow(
        db,
        message=message,
        decision=decision,
        idempotency_key=workflow_idempotency_key,
        principal=principal,
    )
    if decision.state == "manual_gate_required":
        run = _complete_decision_workflow(
            db,
            run=run,
            decision=decision,
            principal=principal,
            step_name="manual_gate",
            status_text="waiting_human",
            next_action="await_human_review",
        )
        task = create_human_review_task(
            db,
            run.id,
            HumanReviewTaskCreate(
                reason=decision.reason,
                risk_level="high" if decision.reason == "manual_review_terms" else "medium",
                draft_reply=decision.draft_reply,
            ),
            principal,
        )
        return run, task.id, decision, None, "manual_gate_required", decision.reason, "await_human_review"
    if decision.state == "knowledge_gap":
        gap, _created = create_knowledge_gap_from_reply_decision(
            db,
            decision=decision,
            message=message,
            principal=principal,
        )
        run = _complete_decision_workflow(
            db,
            run=run,
            decision=decision,
            principal=principal,
            step_name="knowledge_gap_sync",
            status_text="completed",
            next_action="knowledge_gap_created",
            knowledge_gap_id=gap.id,
        )
        return run, None, decision, gap.id, "knowledge_gap", decision.reason, "review_knowledge_gap"
    if decision.state == "auto_reply_ready":
        run = _complete_decision_workflow(
            db,
            run=run,
            decision=decision,
            principal=principal,
            step_name="outbox_pre_gate",
            status_text="completed",
            next_action="outbox_pre_gate_external_write_closed",
        )
        return run, None, decision, None, "auto_reply_ready", decision.reason, "await_outbox_pre_gate"

    run = _complete_decision_workflow(
        db,
        run=run,
        decision=decision,
        principal=principal,
        step_name="policy_gate",
        status_text="completed",
        next_action="blocked_by_policy_review",
    )
    return run, None, decision, None, decision.state, decision.reason, "blocked_by_policy_review"


def _mark_failure(
    db: Session,
    *,
    tenant_id: int,
    message: Message,
    principal: CurrentPrincipal,
    idempotency_key: str,
    error_message: str,
) -> None:
    add_audit_event(
        db,
        tenant_id=tenant_id,
        actor_id=principal.user.id,
        action="trusted_inbound_worker.failed",
        resource_type="message",
        resource_id=str(message.id),
        payload={
            "message_id": message.id,
            "conversation_id": message.conversation_id,
            "idempotency_key": idempotency_key,
            "error_message": error_message[:1000],
            "next_action": "review_failed_trusted_inbound_worker_item",
            "external_write": False,
        },
    )
    db.commit()


def run_trusted_inbound_worker(
    db: Session,
    *,
    tenant_id: int,
    payload: TrustedInboundWorkerRunCreate,
    principal: CurrentPrincipal,
) -> TrustedInboundWorkerRunRead:
    run_record = _create_run_record(db, tenant_id=tenant_id, payload=payload, principal=principal)
    now = utc_now()
    lease_cutoff = now - timedelta(seconds=payload.lease_seconds)
    raw_candidates = _candidate_messages(db, tenant_id=tenant_id, batch_size=payload.batch_size)
    skipped_message_ids: list[int] = []
    candidates: list[tuple[Message, TrustedInboundMessageJob]] = []
    lease_stats = {
        "worker_id": payload.worker_id,
        "lease_seconds": payload.lease_seconds,
        "stale_lock_cutoff": lease_cutoff.isoformat(),
        "atomic_claim": True,
        "claimed": 0,
        "fresh_locked_skipped": 0,
        "stale_locked_reclaimed": 0,
        "failed_replayed": 0,
        "already_succeeded_skipped": 0,
        "claim_lost_skipped": 0,
    }
    for message in raw_candidates:
        idempotency_key = _workflow_idempotency_key(message.id)
        job = _ensure_message_job(db, tenant_id=tenant_id, message=message, idempotency_key=idempotency_key)
        existing_run = _existing_workflow_run(
            db,
            tenant_id=tenant_id,
            message_id=message.id,
            idempotency_key=idempotency_key,
        )
        if existing_run is not None:
            if job.status != JOB_SUCCEEDED:
                job.status = JOB_SUCCEEDED
                job.workflow_run_id = existing_run.id
                job.updated_at = utc_now()
                db.commit()
            skipped_message_ids.append(message.id)
            continue
        locked_at = _as_aware(job.locked_at)
        if job.status == JOB_LOCKED and locked_at is not None and locked_at > lease_cutoff:
            skipped_message_ids.append(message.id)
            lease_stats["fresh_locked_skipped"] += 1
            continue
        if job.status == JOB_SUCCEEDED:
            skipped_message_ids.append(message.id)
            lease_stats["already_succeeded_skipped"] += 1
            continue
        candidates.append((message, job))

    capacity = max(min(payload.batch_size, payload.rate_limit_per_minute), 0)
    to_process = candidates[:capacity]
    rate_limited_messages = candidates[capacity:]
    items: list[TrustedInboundWorkerItemRead] = []

    for message, job in to_process:
        idempotency_key = _workflow_idempotency_key(message.id)
        claimed_job, claim_status = _claim_message_job(
            db,
            tenant_id=tenant_id,
            job=job,
            worker_id=payload.worker_id,
            run_record_id=run_record.id,
            now=now,
            lease_cutoff=lease_cutoff,
        )
        if claimed_job is None:
            skipped_message_ids.append(message.id)
            if claim_status == "fresh_locked":
                lease_stats["fresh_locked_skipped"] += 1
            elif claim_status == "already_succeeded":
                lease_stats["already_succeeded_skipped"] += 1
            else:
                lease_stats["claim_lost_skipped"] += 1
            continue
        job = claimed_job
        lease_stats["claimed"] += 1
        if claim_status == "stale_reclaimed":
            lease_stats["stale_locked_reclaimed"] += 1
        elif claim_status == "failed_replayed":
            lease_stats["failed_replayed"] += 1
        try:
            run, human_review_task_id, decision, knowledge_gap_id, decision_text, reason, next_action = (
                _run_reply_decision_branch(
                    db,
                    message=message,
                    workflow_idempotency_key=idempotency_key,
                    principal=principal,
                )
            )
            run = _mark_success_state(db, workflow_run_id=run.id, message=message, principal=principal)
            _mark_job_succeeded(
                db,
                job_id=job.id,
                workflow_run_id=run.id,
                human_review_task_id=human_review_task_id,
            )
            items.append(
                TrustedInboundWorkerItemRead(
                    message_id=message.id,
                    conversation_id=message.conversation_id,
                    job_id=job.id,
                    reply_decision_id=decision.id,
                    knowledge_gap_id=knowledge_gap_id,
                    status="succeeded",
                    idempotency_key=idempotency_key,
                    workflow_run_id=run.id,
                    human_review_task_id=human_review_task_id,
                    decision=decision_text,
                    reason=reason,
                    next_action=next_action,
                )
            )
        except Exception as exc:  # pragma: no cover - exercised by failure tests when provider behavior expands
            db.rollback()
            error_message = str(exc)
            _mark_job_failed(db, job_id=job.id, error_message=error_message)
            _mark_failure(
                db,
                tenant_id=tenant_id,
                message=message,
                principal=principal,
                idempotency_key=idempotency_key,
                error_message=error_message,
            )
            items.append(
                TrustedInboundWorkerItemRead(
                    message_id=message.id,
                    conversation_id=message.conversation_id,
                    job_id=job.id,
                    status="failed",
                    idempotency_key=idempotency_key,
                    error_message=error_message,
                    next_action="review_failed_trusted_inbound_worker_item",
                )
            )

    succeeded = sum(1 for item in items if item.status == "succeeded")
    failed = sum(1 for item in items if item.status == "failed")
    summary = TrustedInboundWorkerRunRead(
        run_record_id=run_record.id,
        tenant_id=tenant_id,
        worker_id=payload.worker_id,
        mode=WORKER_MODE,
        scanned=len(raw_candidates),
        processed=len(items),
        succeeded=succeeded,
        failed=failed,
        skipped=len(skipped_message_ids),
        rate_limited=len(rate_limited_messages),
        skipped_message_ids=skipped_message_ids,
        rate_limited_message_ids=[message.id for message, _job in rate_limited_messages],
        external_write=False,
        rate_limit={
            "per_minute": payload.rate_limit_per_minute,
            "batch_size": payload.batch_size,
        },
        lease=lease_stats,
        items=items,
    )
    _finish_run_record(db, run_record_id=run_record.id, summary=summary)
    return summary
