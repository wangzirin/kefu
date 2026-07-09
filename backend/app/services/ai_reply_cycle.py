import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.audit import add_audit_event
from app.core.auth import CurrentPrincipal
from app.core.config import get_settings
from app.models import (
    Channel,
    ChannelConnector,
    Conversation,
    ConversationEvent,
    KnowledgeGapItem,
    Message,
    ModelCallRecord,
    OutboxDeliveryJob,
    OutboxDraft,
    ReplyDecision,
    Role,
    Tenant,
    User,
    UserRole,
    WorkflowRun,
)
from app.models.foundation import utc_now
from app.schemas.outbox import OutboxDeliveryQueueRunCreate
from app.services.model_budget import estimate_route_cost
from app.services.model_gateway import ModelDraftKnowledge, ModelDraftRequest, generate_reply_draft, select_model_route
from app.services.reply_provenance import build_reply_provenance_id, create_reply_decision_citation_snapshot
from app.services.mvp_customer_service_workflow import run_mvp_customer_service_workflow
from app.services.outbox_delivery_queue import run_outbox_delivery_queue

HUMAN_CONTROLLED_STATUSES = {"queued_for_me", "assigned_to_me", "handoff", "follow_up", "waiting_customer"}


def _create_gap_for_decision(db: Session, decision: ReplyDecision, message: Message) -> None:
    source_ref = f"reply_decision:{decision.id}"
    existing = db.scalar(
        select(KnowledgeGapItem).where(
            KnowledgeGapItem.tenant_id == decision.tenant_id,
            KnowledgeGapItem.source_type == "reply_decision",
            KnowledgeGapItem.source_ref == source_ref,
        )
    )
    if existing is not None:
        return
    db.add(
        KnowledgeGapItem(
            tenant_id=decision.tenant_id,
            status="open",
            severity="high" if decision.state == "blocked_by_policy" else "medium",
            source_type="reply_decision",
            source_ref=source_ref,
            source_title="AI 未能自动回复",
            source_excerpt=message.content[:500],
            question_excerpt=message.content[:1000],
            gap_type=decision.reason or decision.state,
            expected_terms=decision.matched_terms,
            evidence_payload={
                "reply_decision_id": decision.id,
                "conversation_id": decision.conversation_id,
                "state": decision.state,
                "confidence": decision.confidence,
            },
            created_at=utc_now(),
            updated_at=utc_now(),
        )
    )


def _principal_for_cycle(db: Session, *, tenant_id: int, actor_id: int | None) -> CurrentPrincipal | None:
    user = db.get(User, actor_id) if actor_id else None
    if user is None:
        user = db.scalar(select(User).where(User.tenant_id == tenant_id, User.status == "active").order_by(User.id.asc()))
    tenant = db.get(Tenant, tenant_id)
    if user is None or tenant is None:
        return None
    roles = list(
        db.scalars(
            select(Role.code)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(UserRole.user_id == user.id)
            .order_by(Role.code.asc())
        ).all()
    )
    return CurrentPrincipal(user=user, tenant=tenant, roles=roles)


def _ready_connector(db: Session, *, tenant_id: int, channel_id: int) -> ChannelConnector | None:
    return db.scalar(
        select(ChannelConnector).where(
            ChannelConnector.tenant_id == tenant_id,
            ChannelConnector.channel_id == channel_id,
            ChannelConnector.status.in_(["ready", "active"]),
        )
    )


def _create_ready_outbox_draft(
    db: Session,
    *,
    conversation: Conversation,
    message: Message,
    reply_text: str,
    actor_id: int | None,
) -> OutboxDraft:
    now = utc_now()
    draft = db.scalar(
        select(OutboxDraft).where(
            OutboxDraft.tenant_id == conversation.tenant_id,
            OutboxDraft.idempotency_key == f"message:{message.id}:mvp_auto_reply_draft:v1",
        )
    )
    if draft is not None:
        return draft
    draft = OutboxDraft(
        tenant_id=conversation.tenant_id,
        conversation_id=conversation.id,
        channel_id=conversation.channel_id,
        contact_id=conversation.contact_id,
        source_review_task_id=None,
        source_workflow_run_id=None,
        source_message_id=message.id,
        status="ready_to_send",
        delivery_status="not_sent",
        reply_text=reply_text,
        idempotency_key=f"message:{message.id}:mvp_auto_reply_draft:v1",
        confirmation_note="AI MVP workflow auto-approved low-risk draft.",
        created_by_id=actor_id,
        confirmed_by_id=actor_id,
        created_at=now,
        updated_at=now,
        confirmed_at=now,
    )
    db.add(draft)
    db.flush()
    return draft


def _create_delivery_job(
    db: Session,
    *,
    draft: OutboxDraft,
    connector: ChannelConnector,
    actor_id: int | None,
) -> OutboxDeliveryJob:
    job = db.scalar(
        select(OutboxDeliveryJob).where(
            OutboxDeliveryJob.tenant_id == draft.tenant_id,
            OutboxDeliveryJob.idempotency_key == f"outbox_delivery_job:auto_reply:{draft.id}:{connector.id}",
        )
    )
    if job is not None:
        return job
    settings = get_settings()
    now = utc_now()
    job = OutboxDeliveryJob(
        tenant_id=draft.tenant_id,
        outbox_draft_id=draft.id,
        channel_id=draft.channel_id,
        connector_id=connector.id,
        status="queued",
        priority=10,
        attempts_count=0,
        max_attempts=settings.outbox_worker_max_attempts,
        locked_by="",
        locked_at=None,
        next_run_at=now,
        idempotency_key=f"outbox_delivery_job:auto_reply:{draft.id}:{connector.id}",
        external_write_requested=True,
        external_write_permitted=False,
        created_by_id=actor_id,
        created_at=now,
        updated_at=now,
    )
    db.add(job)
    db.flush()
    return job


def process_inbound_message_for_ai(db: Session, *, message_id: int, actor_id: int | None = None) -> dict:
    message = db.get(Message, message_id)
    if message is None or message.direction != "inbound":
        return {"status": "skipped", "reason": "message_not_found_or_not_inbound"}
    conversation = db.get(Conversation, message.conversation_id)
    if conversation is None:
        return {"status": "skipped", "reason": "conversation_not_found"}
    if conversation.status in HUMAN_CONTROLLED_STATUSES:
        db.add(
            ConversationEvent(
                conversation_id=conversation.id,
                event_type="ai_reply_cycle.skipped_human_controlled",
                actor_id=actor_id,
                payload=json.dumps(
                    {
                        "message_id": message.id,
                        "conversation_status": conversation.status,
                        "assigned_user_id": conversation.assigned_user_id,
                        "reason": "conversation_claimed_by_agent",
                        "secret_included": False,
                    },
                    ensure_ascii=False,
                ),
            )
        )
        db.flush()
        return {
            "status": "skipped",
            "reason": "conversation_claimed_by_agent",
            "conversation_status": conversation.status,
            "assigned_user_id": conversation.assigned_user_id,
        }
    channel = db.get(Channel, conversation.channel_id)
    if channel is None:
        return {"status": "skipped", "reason": "channel_not_found"}
    idempotency_key = f"message:{message.id}:reply_decision:auto_cycle:v1"
    existing = db.scalar(
        select(ReplyDecision).where(
            ReplyDecision.tenant_id == conversation.tenant_id,
            ReplyDecision.idempotency_key == idempotency_key,
        )
    )
    if existing is not None:
        return {"status": "already_processed", "reply_decision_id": existing.id}

    principal = _principal_for_cycle(db, tenant_id=conversation.tenant_id, actor_id=actor_id)
    handoff_user_id = actor_id or (principal.user.id if principal is not None else None)
    candidate = run_mvp_customer_service_workflow(db, conversation=conversation, message=message, principal=principal)

    provenance_id = build_reply_provenance_id(
        tenant_id=conversation.tenant_id,
        message_id=message.id,
        idempotency_key=idempotency_key,
    )
    workflow_run = WorkflowRun(
        tenant_id=conversation.tenant_id,
        conversation_id=conversation.id,
        trigger_message_id=message.id,
        workflow_type="customer_reply_mvp",
        status="completed" if candidate.state == "auto_reply_ready" else "waiting_human",
        current_step=candidate.reply_branch,
        idempotency_key=f"message:{message.id}:mvp_customer_service_workflow:v1",
        state_payload={**candidate.payload, "provenance_id": provenance_id},
        created_at=utc_now(),
        updated_at=utc_now(),
        completed_at=utc_now() if candidate.state == "auto_reply_ready" else None,
    )
    db.add(workflow_run)
    db.flush()
    record = ReplyDecision(
        tenant_id=conversation.tenant_id,
        conversation_id=conversation.id,
        message_id=message.id,
        channel_id=conversation.channel_id,
        business_object_id=None,
        object_knowledge_card_id=None,
        workflow_run_id=workflow_run.id,
        provenance_id=provenance_id,
        state=candidate.state,
        reason=candidate.reason,
        confidence=candidate.confidence,
        delivery_mode=candidate.delivery_mode,
        draft_reply=candidate.draft_reply,
        matched_terms=candidate.matched_terms,
        decision_payload={
            **candidate.payload,
            "provenance": {
                "provenance_id": provenance_id,
                "tenant_id": conversation.tenant_id,
                "conversation_id": conversation.id,
                "message_id": message.id,
                "channel_id": conversation.channel_id,
                "workflow_run_id": workflow_run.id,
                "model_call_recorded": False,
                "external_write_allowed": candidate.state == "auto_reply_ready",
            },
        },
        external_write_allowed=candidate.state == "auto_reply_ready",
        idempotency_key=idempotency_key,
        created_by_id=actor_id,
        created_at=utc_now(),
    )
    db.add(record)
    db.flush()
    create_reply_decision_citation_snapshot(db, decision=record, card=None)

    outbound_message_id = None
    model_status = candidate.model_result.status if candidate.model_result else "not_called"
    outbox_draft_id = None
    delivery_job_id = None
    delivery_status = "not_requested"
    if candidate.model_result is not None:
        route = select_model_route(
            user_message=message.content,
            intent=candidate.intent,
            risk_level=candidate.risk_level,
            confidence=candidate.confidence,
            knowledge_count=max(1, len(candidate.knowledge_matches)),
            requested_provider=candidate.model_result.provider,
            requested_model=candidate.model_result.model,
            settings=get_settings(),
        )
        estimate = estimate_route_cost(
            route,
            input_units=candidate.model_result.prompt_chars,
            output_units=candidate.model_result.completion_chars,
            settings=get_settings(),
        )
        db.add(
            ModelCallRecord(
                tenant_id=conversation.tenant_id,
                channel_id=conversation.channel_id,
                conversation_id=conversation.id,
                message_id=message.id,
                reply_decision_id=record.id,
                workflow_run_id=workflow_run.id,
                provenance_id=provenance_id,
                request_id=f"reply-decision-{record.id}",
                idempotency_key=f"model_call:{record.id}:v1",
                provider=candidate.model_result.provider,
                model=candidate.model_result.model,
                route_name=candidate.model_result.route_name,
                target_model_tier=candidate.model_result.target_model_tier,
                complexity=candidate.model_result.complexity,
                status=candidate.model_result.status,
                error_code=candidate.model_result.error_message[:120],
                input_units=candidate.model_result.prompt_chars,
                output_units=candidate.model_result.completion_chars,
                total_units=candidate.model_result.total_chars,
                unit_type="estimated_units",
                estimated_cost=estimate.estimated_cost,
                currency=estimate.currency,
                pricing_source=estimate.pricing_source,
                pricing_version=estimate.pricing_version,
                raw_text_logged=False,
                metadata_payload={"secret_included": False, "prompt_summary": candidate.model_result.prompt_summary},
                created_at=utc_now(),
            )
        )
    if record.state == "auto_reply_ready" and record.draft_reply.strip():
        draft = _create_ready_outbox_draft(
            db,
            conversation=conversation,
            message=message,
            reply_text=record.draft_reply,
            actor_id=actor_id,
        )
        outbox_draft_id = draft.id
        connector = _ready_connector(db, tenant_id=conversation.tenant_id, channel_id=conversation.channel_id)
        if connector is not None:
            job = _create_delivery_job(db, draft=draft, connector=connector, actor_id=actor_id)
            delivery_job_id = job.id
            if principal is not None:
                db.commit()
                run_summary = run_outbox_delivery_queue(
                    db,
                    tenant_id=conversation.tenant_id,
                    payload=OutboxDeliveryQueueRunCreate(batch_size=1, rate_limit_per_minute=1, worker_id="ai-cycle-inline-sender"),
                    principal=principal,
                )
                delivery_status = "sent" if run_summary.succeeded else "blocked_or_failed"
                if run_summary.attempts and run_summary.attempts[0].status == "succeeded":
                    outbound_message_id = None
                    conversation = db.get(Conversation, conversation.id)
                    if conversation is not None:
                        conversation.status = "bot_visiting"
                else:
                    record.state = "manual_gate_required"
                    record.reason = "external_delivery_failed"
                    record.delivery_mode = "human_review"
                    conversation.status = "queued_for_me"
                    conversation.assigned_user_id = conversation.assigned_user_id or handoff_user_id
            else:
                conversation.status = "queued_for_me"
                conversation.assigned_user_id = conversation.assigned_user_id or handoff_user_id
        else:
            if channel.type in {"website", "web"}:
                now = utc_now()
                outbound = Message(
                    conversation_id=conversation.id,
                    direction="outbound",
                    sender_type="ai",
                    content=record.draft_reply.strip(),
                    external_message_id=f"website-ai-{conversation.id}-{message.id}-{record.id}",
                    created_at=now,
                )
                db.add(outbound)
                db.flush()
                outbound_message_id = outbound.id
                draft.delivery_status = "sent"
                draft.sent_at = now
                draft.updated_at = now
                conversation.status = "bot_visiting"
                conversation.last_message_at = now
                delivery_status = "website_local_sent"
            else:
                record.delivery_mode = "draft_only"
                record.external_write_allowed = False
                conversation.status = "queued_for_me"
                conversation.assigned_user_id = conversation.assigned_user_id or handoff_user_id
                delivery_status = "connector_missing"
    else:
        conversation.status = "queued_for_me"
        conversation.assigned_user_id = conversation.assigned_user_id or handoff_user_id
        if record.state in {"manual_gate_required", "knowledge_gap", "blocked_by_policy"}:
            _create_gap_for_decision(db, record, message)
    if record.state == "auto_reply_ready" and delivery_status == "sent":
        conversation.status = "bot_visiting"
    elif record.state != "auto_reply_ready":
        conversation.status = "queued_for_me"
        conversation.assigned_user_id = conversation.assigned_user_id or handoff_user_id
    record.decision_payload = {
        **record.decision_payload,
        "outbox_draft_id": outbox_draft_id,
        "delivery_job_id": delivery_job_id,
        "delivery_status": delivery_status,
    }

    db.add(
        ConversationEvent(
            conversation_id=conversation.id,
            event_type="ai_reply_cycle.processed",
            actor_id=actor_id,
            payload=json.dumps({
                "reply_decision_id": record.id,
                "state": record.state,
                "reason": record.reason,
                "model_status": model_status,
                "outbound_message_id": outbound_message_id,
                "outbox_draft_id": outbox_draft_id,
                "delivery_job_id": delivery_job_id,
                "delivery_status": delivery_status,
                "secret_included": False,
            }, ensure_ascii=False),
        )
    )
    add_audit_event(
        db,
        tenant_id=conversation.tenant_id,
        actor_id=actor_id,
        action="ai_reply_cycle.processed",
        resource_type="reply_decision",
        resource_id=str(record.id),
        payload={
            "conversation_id": conversation.id,
            "message_id": message.id,
            "state": record.state,
            "reason": record.reason,
            "outbound_message_id": outbound_message_id,
            "outbox_draft_id": outbox_draft_id,
            "delivery_job_id": delivery_job_id,
            "delivery_status": delivery_status,
            "secret_included": False,
        },
    )
    db.commit()
    return {
        "status": "processed",
        "reply_decision_id": record.id,
        "state": record.state,
        "reason": record.reason,
        "outbound_message_id": outbound_message_id,
        "outbox_draft_id": outbox_draft_id,
        "delivery_job_id": delivery_job_id,
        "delivery_status": delivery_status,
        "conversation_status": conversation.status,
    }
