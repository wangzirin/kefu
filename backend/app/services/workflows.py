from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.audit import add_audit_event
from app.core.auth import CurrentPrincipal
from app.models import (
    Conversation,
    HumanReviewTask,
    Message,
    WorkflowCheckpoint,
    WorkflowRun,
    WorkflowStepAttempt,
)
from app.models.foundation import utc_now
from app.schemas.workflows import (
    HumanReviewTaskCreate,
    HumanReviewConversationRead,
    HumanReviewEvidenceRead,
    HumanReviewInboxItemRead,
    HumanReviewMessageRead,
    HumanReviewTaskResolve,
    HumanReviewWorkflowRead,
    WorkflowCheckpointCreate,
    WorkflowRunCreate,
    WorkflowStepAttemptCreate,
)


def require_conversation_for_principal(
    db: Session,
    conversation_id: int,
    principal: CurrentPrincipal,
) -> Conversation:
    conversation = db.get(Conversation, conversation_id)
    if conversation is None or conversation.tenant_id != principal.tenant.id:
        raise HTTPException(status_code=404, detail="conversation not found")
    return conversation


def require_workflow_run_for_principal(
    db: Session,
    workflow_run_id: int,
    principal: CurrentPrincipal,
) -> WorkflowRun:
    run = db.get(WorkflowRun, workflow_run_id)
    if run is None or run.tenant_id != principal.tenant.id:
        raise HTTPException(status_code=404, detail="workflow run not found")
    return run


def require_review_task_for_principal(
    db: Session,
    task_id: int,
    principal: CurrentPrincipal,
) -> HumanReviewTask:
    task = db.get(HumanReviewTask, task_id)
    if task is None or task.tenant_id != principal.tenant.id:
        raise HTTPException(status_code=404, detail="human review task not found")
    return task


def create_workflow_run(
    db: Session,
    conversation_id: int,
    payload: WorkflowRunCreate,
    principal: CurrentPrincipal,
) -> WorkflowRun:
    conversation = require_conversation_for_principal(db, conversation_id, principal)
    if payload.trigger_message_id is not None:
        message = db.get(Message, payload.trigger_message_id)
        if message is None or message.conversation_id != conversation.id:
            raise HTTPException(status_code=404, detail="trigger message not found")
    now = utc_now()
    run = WorkflowRun(
        tenant_id=conversation.tenant_id,
        conversation_id=conversation.id,
        trigger_message_id=payload.trigger_message_id,
        workflow_type=payload.workflow_type,
        status="running",
        current_step=payload.current_step,
        idempotency_key=payload.idempotency_key,
        state_payload=payload.state_payload,
        created_at=now,
        updated_at=now,
    )
    db.add(run)
    db.flush()
    add_audit_event(
        db,
        tenant_id=conversation.tenant_id,
        actor_id=principal.user.id,
        action="workflow_run.created",
        resource_type="workflow_run",
        resource_id=str(run.id),
        payload={
            "conversation_id": conversation.id,
            "trigger_message_id": payload.trigger_message_id,
            "workflow_type": payload.workflow_type,
        },
    )
    db.commit()
    db.refresh(run)
    return run


def add_step_attempt(
    db: Session,
    workflow_run_id: int,
    payload: WorkflowStepAttemptCreate,
    principal: CurrentPrincipal,
) -> WorkflowStepAttempt:
    run = require_workflow_run_for_principal(db, workflow_run_id, principal)
    attempt_number = payload.attempt_number
    if attempt_number is None:
        max_attempt = db.scalar(
            select(func.max(WorkflowStepAttempt.attempt_number)).where(
                WorkflowStepAttempt.workflow_run_id == run.id,
                WorkflowStepAttempt.step_name == payload.step_name,
            )
        )
        attempt_number = int(max_attempt or 0) + 1
    now = utc_now()
    attempt = WorkflowStepAttempt(
        workflow_run_id=run.id,
        step_name=payload.step_name,
        attempt_number=attempt_number,
        status=payload.status,
        input_summary=payload.input_summary,
        output_summary=payload.output_summary,
        error_message=payload.error_message,
        started_at=now,
        finished_at=now if payload.status in {"succeeded", "failed"} else None,
    )
    run.current_step = payload.step_name
    run.updated_at = now
    db.add(attempt)
    db.commit()
    db.refresh(attempt)
    return attempt


def add_checkpoint(
    db: Session,
    workflow_run_id: int,
    payload: WorkflowCheckpointCreate,
    principal: CurrentPrincipal,
) -> WorkflowCheckpoint:
    run = require_workflow_run_for_principal(db, workflow_run_id, principal)
    now = utc_now()
    checkpoint = WorkflowCheckpoint(
        workflow_run_id=run.id,
        step_name=payload.step_name,
        status=payload.status,
        state_payload=payload.state_payload,
        input_summary=payload.input_summary,
        output_summary=payload.output_summary,
        error_message=payload.error_message,
        created_at=now,
    )
    run.current_step = payload.step_name
    run.status = payload.status
    run.state_payload = payload.state_payload
    run.updated_at = now
    if payload.status in {"completed", "failed", "canceled"}:
        run.completed_at = now
    db.add(checkpoint)
    db.commit()
    db.refresh(checkpoint)
    return checkpoint


def complete_workflow_run(
    db: Session,
    workflow_run_id: int,
    *,
    current_step: str,
    state_payload: dict,
    principal: CurrentPrincipal,
) -> WorkflowRun:
    run = require_workflow_run_for_principal(db, workflow_run_id, principal)
    now = utc_now()
    run.status = "completed"
    run.current_step = current_step
    run.state_payload = state_payload
    run.updated_at = now
    run.completed_at = now
    add_audit_event(
        db,
        tenant_id=run.tenant_id,
        actor_id=principal.user.id,
        action="workflow_run.completed",
        resource_type="workflow_run",
        resource_id=str(run.id),
        payload={"conversation_id": run.conversation_id, "current_step": current_step},
    )
    db.commit()
    db.refresh(run)
    return run


def create_human_review_task(
    db: Session,
    workflow_run_id: int,
    payload: HumanReviewTaskCreate,
    principal: CurrentPrincipal,
) -> HumanReviewTask:
    run = require_workflow_run_for_principal(db, workflow_run_id, principal)
    now = utc_now()
    task = HumanReviewTask(
        tenant_id=run.tenant_id,
        workflow_run_id=run.id,
        conversation_id=run.conversation_id,
        message_id=run.trigger_message_id,
        status="open",
        reason=payload.reason,
        risk_level=payload.risk_level,
        draft_reply=payload.draft_reply,
        assigned_user_id=payload.assigned_user_id,
        created_at=now,
    )
    run.status = "waiting_human"
    run.current_step = "human_review"
    run.updated_at = now
    db.add(task)
    add_audit_event(
        db,
        tenant_id=run.tenant_id,
        actor_id=principal.user.id,
        action="human_review.created",
        resource_type="human_review_task",
        payload={"workflow_run_id": run.id, "reason": payload.reason, "risk_level": payload.risk_level},
    )
    db.commit()
    db.refresh(task)
    return task


def _human_review_evidence_from_state(state_payload: dict | None) -> HumanReviewEvidenceRead:
    state = state_payload or {}
    return HumanReviewEvidenceRead(
        intent=str(state.get("intent") or ""),
        retrieved_knowledge_count=int(state.get("retrieved_knowledge_count") or 0),
        confidence=state.get("confidence"),
        risk_level=str(state.get("risk_level") or ""),
        draft_source=str(state.get("draft_source") or ""),
        retrieval_mode=str(state.get("retrieval_mode") or ""),
        retrieval_engine=str(state.get("retrieval_engine") or ""),
        knowledge_matches=list(state.get("knowledge_matches") or []),
        model_call=state.get("model_call") if isinstance(state.get("model_call"), dict) else None,
        auto_reply_threshold=state.get("auto_reply_threshold"),
    )


def list_human_review_inbox(
    db: Session,
    tenant_id: int,
    *,
    status_filter: str | None,
    principal: CurrentPrincipal,
) -> list[HumanReviewInboxItemRead]:
    if tenant_id != principal.tenant.id:
        raise HTTPException(status_code=404, detail="tenant not found")
    query = select(HumanReviewTask).where(HumanReviewTask.tenant_id == tenant_id)
    if status_filter:
        query = query.where(HumanReviewTask.status == status_filter)
    query = query.order_by(HumanReviewTask.created_at.desc(), HumanReviewTask.id.desc())
    tasks = list(db.scalars(query).all())

    items: list[HumanReviewInboxItemRead] = []
    for task in tasks:
        run = db.get(WorkflowRun, task.workflow_run_id)
        conversation = db.get(Conversation, task.conversation_id)
        message = db.get(Message, task.message_id) if task.message_id else None
        if run is None or conversation is None:
            continue
        items.append(
            HumanReviewInboxItemRead(
                id=task.id,
                tenant_id=task.tenant_id,
                workflow_run_id=task.workflow_run_id,
                conversation_id=task.conversation_id,
                message_id=task.message_id,
                status=task.status,
                reason=task.reason,
                risk_level=task.risk_level,
                draft_reply=task.draft_reply,
                final_reply=task.final_reply,
                assigned_user_id=task.assigned_user_id,
                reviewer_id=task.reviewer_id,
                resolution_note=task.resolution_note,
                created_at=task.created_at,
                resolved_at=task.resolved_at,
                conversation=HumanReviewConversationRead.model_validate(conversation),
                trigger_message=HumanReviewMessageRead.model_validate(message) if message else None,
                workflow=HumanReviewWorkflowRead.model_validate(run),
                evidence=_human_review_evidence_from_state(run.state_payload),
            )
        )
    return items


def resolve_human_review_task(
    db: Session,
    task_id: int,
    payload: HumanReviewTaskResolve,
    principal: CurrentPrincipal,
) -> HumanReviewTask:
    task = require_review_task_for_principal(db, task_id, principal)
    if task.status != "open":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="human review task already resolved",
        )
    run = require_workflow_run_for_principal(db, task.workflow_run_id, principal)
    now = utc_now()
    final_reply = payload.final_reply.strip()
    if payload.decision == "approved" and not final_reply:
        final_reply = task.draft_reply
    task.status = payload.decision
    task.final_reply = final_reply
    task.resolution_note = payload.resolution_note
    task.reviewer_id = principal.user.id
    task.resolved_at = now
    run.status = "completed"
    run.current_step = "record_result"
    run.state_payload = {
        **(run.state_payload or {}),
        "human_review": {
            "task_id": task.id,
            "decision": payload.decision,
            "reviewer_id": principal.user.id,
            "final_reply": final_reply,
            "resolution_note": payload.resolution_note,
            "resolved_at": now.isoformat(),
        },
    }
    run.updated_at = now
    run.completed_at = now
    add_audit_event(
        db,
        tenant_id=task.tenant_id,
        actor_id=principal.user.id,
        action=f"human_review.{payload.decision}",
        resource_type="human_review_task",
        resource_id=str(task.id),
        payload={"workflow_run_id": run.id, "conversation_id": task.conversation_id},
    )
    db.commit()
    db.refresh(task)
    return task
