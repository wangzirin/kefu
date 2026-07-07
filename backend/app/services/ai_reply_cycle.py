import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.audit import add_audit_event
from app.core.config import get_settings
from app.models import Channel, Conversation, ConversationEvent, KnowledgeGapItem, Message, ModelCallRecord, ReplyDecision
from app.models.foundation import utc_now
from app.schemas.reply_decisions import ReplyDecisionCreate
from app.services.model_budget import estimate_route_cost
from app.services.model_gateway import ModelDraftKnowledge, ModelDraftRequest, generate_reply_draft, select_model_route
from app.services.reply_decisions import _decide
from app.services.reply_provenance import build_reply_provenance_id, create_reply_decision_citation_snapshot


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


def process_inbound_message_for_ai(db: Session, *, message_id: int, actor_id: int | None = None) -> dict:
    message = db.get(Message, message_id)
    if message is None or message.direction != "inbound":
        return {"status": "skipped", "reason": "message_not_found_or_not_inbound"}
    conversation = db.get(Conversation, message.conversation_id)
    if conversation is None:
        return {"status": "skipped", "reason": "conversation_not_found"}
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

    payload = ReplyDecisionCreate(
        external_write_allowed=channel.type == "website",
        force_draft_only=channel.type != "website",
        idempotency_key=idempotency_key,
    )
    candidate = _decide(db, conversation, message, payload)
    settings = get_settings()
    model_configured = bool(settings.bailian_api_key)
    if candidate.state == "auto_reply_ready" and channel.type == "website" and not model_configured:
        candidate = candidate.__class__(
            state="manual_gate_required",
            reason="model_service_not_configured",
            confidence=candidate.confidence,
            delivery_mode="human_review",
            draft_reply=candidate.draft_reply,
            matched_terms=candidate.matched_terms,
            business_object=candidate.business_object,
            card=candidate.card,
            payload={**candidate.payload, "decision_note": "AI 服务未配置，已转人工。"},
        )

    provenance_id = build_reply_provenance_id(
        tenant_id=conversation.tenant_id,
        message_id=message.id,
        idempotency_key=idempotency_key,
    )
    record = ReplyDecision(
        tenant_id=conversation.tenant_id,
        conversation_id=conversation.id,
        message_id=message.id,
        channel_id=conversation.channel_id,
        business_object_id=candidate.business_object.id if candidate.business_object else None,
        object_knowledge_card_id=candidate.card.id if candidate.card else None,
        workflow_run_id=None,
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
                "model_call_recorded": False,
                "external_write_allowed": channel.type == "website" and candidate.state == "auto_reply_ready",
            },
        },
        external_write_allowed=channel.type == "website" and candidate.state == "auto_reply_ready",
        idempotency_key=idempotency_key,
        created_by_id=actor_id,
        created_at=utc_now(),
    )
    db.add(record)
    db.flush()
    create_reply_decision_citation_snapshot(db, decision=record, card=candidate.card)

    outbound_message_id = None
    model_status = "not_called"
    if record.state == "auto_reply_ready" and channel.type == "website" and candidate.card is not None:
        draft = generate_reply_draft(
            ModelDraftRequest(
                user_message=message.content,
                intent="simple_faq",
                knowledge=[
                    ModelDraftKnowledge(
                        title=candidate.business_object.title if candidate.business_object else "已发布资料",
                        answer=candidate.card.answer,
                        source_uri=candidate.card.source,
                        matched_terms=record.matched_terms,
                    )
                ],
                provider="auto",
                confidence=record.confidence,
                risk_level="low",
            )
        )
        model_status = draft.status
        route = select_model_route(
            user_message=message.content,
            intent="simple_faq",
            risk_level="low",
            confidence=record.confidence,
            knowledge_count=1,
            requested_provider="auto",
            requested_model="",
            settings=settings,
        )
        estimate = estimate_route_cost(route, input_units=draft.prompt_chars, output_units=draft.completion_chars, settings=settings)
        db.add(
            ModelCallRecord(
                tenant_id=conversation.tenant_id,
                channel_id=conversation.channel_id,
                conversation_id=conversation.id,
                message_id=message.id,
                reply_decision_id=record.id,
                provenance_id=provenance_id,
                request_id=f"reply-decision-{record.id}",
                idempotency_key=f"model_call:{record.id}:v1",
                provider=draft.provider,
                model=draft.model,
                route_name=draft.route_name,
                target_model_tier=draft.target_model_tier,
                complexity=draft.complexity,
                status=draft.status,
                error_code=draft.error_message[:120],
                input_units=draft.prompt_chars,
                output_units=draft.completion_chars,
                total_units=draft.total_chars,
                unit_type="estimated_chars_or_tokens",
                estimated_cost=estimate.estimated_cost,
                currency=estimate.currency,
                pricing_source=estimate.pricing_source,
                pricing_version=estimate.pricing_version,
                raw_text_logged=False,
                metadata_payload={"secret_included": False, "prompt_summary": draft.prompt_summary},
                created_at=utc_now(),
            )
        )
        if draft.status == "succeeded" and draft.draft_text.strip():
            outbound = Message(
                conversation_id=conversation.id,
                direction="outbound",
                sender_type="ai",
                content=draft.draft_text.strip(),
                external_message_id=f"website-ai-{conversation.id}-{message.id}-{record.id}",
                created_at=utc_now(),
            )
            db.add(outbound)
            db.flush()
            outbound_message_id = outbound.id
            conversation.status = "bot"
            conversation.last_message_at = outbound.created_at
        else:
            record.state = "manual_gate_required"
            record.reason = "model_service_failed"
            record.delivery_mode = "human_review"
            conversation.status = "waiting_human"
            _create_gap_for_decision(db, record, message)
    else:
        conversation.status = "waiting_human" if record.state != "auto_reply_ready" else conversation.status
        if record.state in {"manual_gate_required", "knowledge_gap", "blocked_by_policy"}:
            _create_gap_for_decision(db, record, message)

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
        "conversation_status": conversation.status,
    }
