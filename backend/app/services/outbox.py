from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.audit import add_audit_event
from app.core.auth import CurrentPrincipal
from app.models import Channel, Conversation, HumanReviewTask, OutboxDraft, OutboxSendAttempt, WorkflowRun
from app.models.foundation import utc_now
from app.schemas.outbox import (
    OutboxDraftCancel,
    OutboxDraftConfirm,
    OutboxDraftCreateFromReview,
    OutboxSendAttemptCreate,
)


PENDING_CONFIRMATION = "pending_confirmation"
READY_TO_SEND = "ready_to_send"
CANCELED = "canceled"
NOT_SENT = "not_sent"
DRY_RUN = "dry_run"
SUCCEEDED = "succeeded"


def require_outbox_draft_for_principal(
    db: Session,
    draft_id: int,
    principal: CurrentPrincipal,
) -> OutboxDraft:
    draft = db.get(OutboxDraft, draft_id)
    if draft is None or draft.tenant_id != principal.tenant.id:
        raise HTTPException(status_code=404, detail="outbox draft not found")
    return draft


def _require_review_task_for_outbox(
    db: Session,
    task_id: int,
    principal: CurrentPrincipal,
) -> HumanReviewTask:
    task = db.get(HumanReviewTask, task_id)
    if task is None or task.tenant_id != principal.tenant.id:
        raise HTTPException(status_code=404, detail="human review task not found")
    return task


def _update_workflow_outbox_state(
    db: Session,
    *,
    workflow_run_id: int | None,
    draft: OutboxDraft,
) -> None:
    if workflow_run_id is None:
        return
    run = db.get(WorkflowRun, workflow_run_id)
    if run is None:
        return
    run.state_payload = {
        **(run.state_payload or {}),
        "outbox_draft": {
            "id": draft.id,
            "status": draft.status,
            "delivery_status": draft.delivery_status,
            "updated_at": draft.updated_at.isoformat() if draft.updated_at else "",
        },
    }


def _update_workflow_send_attempt_state(
    db: Session,
    *,
    workflow_run_id: int | None,
    attempt: OutboxSendAttempt,
) -> None:
    if workflow_run_id is None:
        return
    run = db.get(WorkflowRun, workflow_run_id)
    if run is None:
        return
    run.state_payload = {
        **(run.state_payload or {}),
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


def create_outbox_draft_from_review_task(
    db: Session,
    task_id: int,
    payload: OutboxDraftCreateFromReview,
    principal: CurrentPrincipal,
) -> OutboxDraft:
    task = _require_review_task_for_outbox(db, task_id, principal)
    if task.status != "approved":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="human review task must be approved before creating an outbox draft",
        )
    reply_text = task.final_reply.strip()
    if not reply_text:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="approved human review task has no final reply",
        )
    idempotency_key = payload.idempotency_key or f"human_review_task:{task.id}:final_reply"
    duplicate = db.scalar(
        select(OutboxDraft).where(
            OutboxDraft.tenant_id == task.tenant_id,
            OutboxDraft.idempotency_key == idempotency_key,
        )
    )
    if duplicate is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="outbox draft already exists for this idempotency key",
        )
    conversation = db.get(Conversation, task.conversation_id)
    if conversation is None or conversation.tenant_id != task.tenant_id:
        raise HTTPException(status_code=404, detail="conversation not found")

    now = utc_now()
    draft = OutboxDraft(
        tenant_id=task.tenant_id,
        conversation_id=task.conversation_id,
        channel_id=conversation.channel_id,
        contact_id=conversation.contact_id,
        source_review_task_id=task.id,
        source_workflow_run_id=task.workflow_run_id,
        source_message_id=task.message_id,
        status=PENDING_CONFIRMATION,
        delivery_status=NOT_SENT,
        reply_text=reply_text,
        idempotency_key=idempotency_key,
        created_by_id=principal.user.id,
        created_at=now,
        updated_at=now,
    )
    db.add(draft)
    db.flush()
    _update_workflow_outbox_state(db, workflow_run_id=task.workflow_run_id, draft=draft)
    add_audit_event(
        db,
        tenant_id=draft.tenant_id,
        actor_id=principal.user.id,
        action="outbox_draft.created",
        resource_type="outbox_draft",
        resource_id=str(draft.id),
        payload={
            "conversation_id": draft.conversation_id,
            "source_review_task_id": draft.source_review_task_id,
            "source_workflow_run_id": draft.source_workflow_run_id,
        },
    )
    db.commit()
    db.refresh(draft)
    return draft


def create_outbox_send_attempt(
    db: Session,
    draft_id: int,
    payload: OutboxSendAttemptCreate,
    principal: CurrentPrincipal,
) -> OutboxSendAttempt:
    draft = require_outbox_draft_for_principal(db, draft_id, principal)
    if draft.status != READY_TO_SEND:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="only ready-to-send outbox drafts can create send attempts",
        )
    if payload.delivery_mode != DRY_RUN:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="only dry-run send attempts are supported before a real channel sender exists",
        )
    idempotency_key = payload.idempotency_key or f"outbox_draft:{draft.id}:dry_run"
    duplicate = db.scalar(
        select(OutboxSendAttempt).where(
            OutboxSendAttempt.tenant_id == draft.tenant_id,
            OutboxSendAttempt.idempotency_key == idempotency_key,
        )
    )
    if duplicate is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="outbox send attempt already exists for this idempotency key",
        )
    channel = db.get(Channel, draft.channel_id)
    if channel is None or channel.tenant_id != draft.tenant_id:
        raise HTTPException(status_code=404, detail="channel not found")

    current_attempt = db.scalar(
        select(func.max(OutboxSendAttempt.attempt_number)).where(OutboxSendAttempt.outbox_draft_id == draft.id)
    )
    attempt_number = (current_attempt or 0) + 1
    now = utc_now()
    request_payload = {
        "dry_run": True,
        "external_write": False,
        "channel_id": draft.channel_id,
        "channel_type": channel.type,
        "conversation_id": draft.conversation_id,
        "contact_id": draft.contact_id,
        "reply_text": draft.reply_text,
    }
    response_payload = {
        "dry_run": True,
        "external_write": False,
        "would_send": True,
        "provider": DRY_RUN,
        "message": "dry run recorded; no external provider was called",
    }
    attempt = OutboxSendAttempt(
        tenant_id=draft.tenant_id,
        outbox_draft_id=draft.id,
        conversation_id=draft.conversation_id,
        channel_id=draft.channel_id,
        contact_id=draft.contact_id,
        attempt_number=attempt_number,
        delivery_mode=DRY_RUN,
        provider=DRY_RUN,
        status=SUCCEEDED,
        delivery_status=NOT_SENT,
        idempotency_key=idempotency_key,
        external_message_id="",
        request_payload=request_payload,
        response_payload=response_payload,
        error_message="",
        operator_note=payload.operator_note,
        created_by_id=principal.user.id,
        started_at=now,
        finished_at=now,
        sent_at=None,
    )
    db.add(attempt)
    db.flush()
    draft.updated_at = now
    _update_workflow_send_attempt_state(db, workflow_run_id=draft.source_workflow_run_id, attempt=attempt)
    add_audit_event(
        db,
        tenant_id=attempt.tenant_id,
        actor_id=principal.user.id,
        action="outbox_send_attempt.dry_run_succeeded",
        resource_type="outbox_send_attempt",
        resource_id=str(attempt.id),
        payload={
            "outbox_draft_id": attempt.outbox_draft_id,
            "conversation_id": attempt.conversation_id,
            "delivery_status": attempt.delivery_status,
            "external_write": False,
        },
    )
    db.commit()
    db.refresh(attempt)
    return attempt


def list_outbox_send_attempts(
    db: Session,
    draft_id: int,
    principal: CurrentPrincipal,
) -> list[OutboxSendAttempt]:
    draft = require_outbox_draft_for_principal(db, draft_id, principal)
    query = (
        select(OutboxSendAttempt)
        .where(
            OutboxSendAttempt.tenant_id == principal.tenant.id,
            OutboxSendAttempt.outbox_draft_id == draft.id,
        )
        .order_by(OutboxSendAttempt.attempt_number.asc(), OutboxSendAttempt.id.asc())
    )
    return list(db.scalars(query).all())


def list_outbox_drafts(
    db: Session,
    tenant_id: int,
    *,
    status_filter: str | None,
    principal: CurrentPrincipal,
) -> list[OutboxDraft]:
    if tenant_id != principal.tenant.id:
        raise HTTPException(status_code=404, detail="tenant not found")
    query = select(OutboxDraft).where(OutboxDraft.tenant_id == tenant_id)
    if status_filter:
        query = query.where(OutboxDraft.status == status_filter)
    query = query.order_by(OutboxDraft.created_at.desc(), OutboxDraft.id.desc())
    return list(db.scalars(query).all())


def confirm_outbox_draft(
    db: Session,
    draft_id: int,
    payload: OutboxDraftConfirm,
    principal: CurrentPrincipal,
) -> OutboxDraft:
    draft = require_outbox_draft_for_principal(db, draft_id, principal)
    if draft.status != PENDING_CONFIRMATION:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="only pending outbox drafts can be confirmed",
        )
    now = utc_now()
    draft.status = READY_TO_SEND
    draft.delivery_status = NOT_SENT
    draft.confirmation_note = payload.confirmation_note
    draft.confirmed_by_id = principal.user.id
    draft.confirmed_at = now
    draft.updated_at = now
    _update_workflow_outbox_state(db, workflow_run_id=draft.source_workflow_run_id, draft=draft)
    add_audit_event(
        db,
        tenant_id=draft.tenant_id,
        actor_id=principal.user.id,
        action="outbox_draft.ready_to_send",
        resource_type="outbox_draft",
        resource_id=str(draft.id),
        payload={"conversation_id": draft.conversation_id, "delivery_status": draft.delivery_status},
    )
    db.commit()
    db.refresh(draft)
    return draft


def cancel_outbox_draft(
    db: Session,
    draft_id: int,
    payload: OutboxDraftCancel,
    principal: CurrentPrincipal,
) -> OutboxDraft:
    draft = require_outbox_draft_for_principal(db, draft_id, principal)
    if draft.status != PENDING_CONFIRMATION:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="only pending outbox drafts can be canceled",
        )
    now = utc_now()
    draft.status = CANCELED
    draft.cancellation_reason = payload.cancellation_reason
    draft.canceled_by_id = principal.user.id
    draft.canceled_at = now
    draft.updated_at = now
    _update_workflow_outbox_state(db, workflow_run_id=draft.source_workflow_run_id, draft=draft)
    add_audit_event(
        db,
        tenant_id=draft.tenant_id,
        actor_id=principal.user.id,
        action="outbox_draft.canceled",
        resource_type="outbox_draft",
        resource_id=str(draft.id),
        payload={"conversation_id": draft.conversation_id, "reason": payload.cancellation_reason},
    )
    db.commit()
    db.refresh(draft)
    return draft
