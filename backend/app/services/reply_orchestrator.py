from dataclasses import dataclass, replace

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.auth import CurrentPrincipal
from app.models import Conversation, Message, WorkflowRun
from app.schemas.knowledge import KnowledgeDocumentSearchRequest, KnowledgeSearchRequest
from app.schemas.reply_orchestrator import (
    ReplyKnowledgeMatchRead,
    ReplyModelCallRead,
    ReplyOrchestrationCreate,
    ReplyOrchestrationRead,
)
from app.schemas.workflows import (
    HumanReviewTaskCreate,
    WorkflowCheckpointCreate,
    WorkflowRunCreate,
    WorkflowStepAttemptCreate,
)
from app.services.knowledge import search_knowledge_cards, search_knowledge_documents
from app.services.model_gateway import (
    DETERMINISTIC_MODEL,
    DETERMINISTIC_PROVIDER,
    ModelDraftKnowledge,
    ModelDraftRequest,
    ModelDraftResult,
    generate_reply_draft,
    select_model_route,
)
from app.services.model_budget import evaluate_budget, estimate_route_cost
from app.services.reply_provenance import (
    build_reply_provenance_id,
    create_model_call_record_from_result,
    create_reply_match_citation_snapshots,
)
from app.services.workflows import (
    add_checkpoint,
    add_step_attempt,
    complete_workflow_run,
    create_human_review_task,
    create_workflow_run,
)


AUTO_REPLY_CONFIDENCE_THRESHOLD = 0.75
REVIEW_RISK_LEVELS = {"medium", "high", "critical"}


@dataclass(frozen=True)
class ResolvedReplyPlan:
    intent: str
    retrieved_knowledge_count: int
    draft_reply: str
    confidence: float
    risk_level: str
    draft_source: str
    retrieval_mode: str
    retrieval_engine: str
    knowledge_matches: list[ReplyKnowledgeMatchRead]
    model_call: ReplyModelCallRead | None = None
    model_result: ModelDraftResult | None = None


def require_inbound_message_for_principal(
    db: Session,
    message_id: int,
    principal: CurrentPrincipal,
) -> tuple[Message, Conversation]:
    query = select(Message).options(joinedload(Message.conversation)).where(Message.id == message_id)
    message = db.scalar(query)
    if message is None or message.conversation.tenant_id != principal.tenant.id:
        raise HTTPException(status_code=404, detail="message not found")
    if message.direction != "inbound":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="only inbound messages can start reply orchestration",
        )
    return message, message.conversation


def _review_reason(plan: ResolvedReplyPlan) -> str | None:
    if plan.retrieved_knowledge_count == 0:
        return "no_knowledge_hit"
    if plan.model_call is not None and plan.model_call.status in {"budget_blocked", "degraded"}:
        return "model_budget_limited"
    if plan.model_call is not None and plan.model_call.status != "succeeded":
        return "model_unavailable"
    if plan.confidence < AUTO_REPLY_CONFIDENCE_THRESHOLD:
        return "low_confidence"
    if plan.risk_level in REVIEW_RISK_LEVELS:
        return f"risk_level_{plan.risk_level}"
    return None


def _state_payload(plan: ResolvedReplyPlan, decision: str, reason: str, provenance_id: str) -> dict:
    return {
        "provenance_id": provenance_id,
        "decision": decision,
        "reason": reason,
        "intent": plan.intent,
        "retrieved_knowledge_count": plan.retrieved_knowledge_count,
        "confidence": plan.confidence,
        "risk_level": plan.risk_level,
        "draft_reply": plan.draft_reply,
        "draft_source": plan.draft_source,
        "retrieval_mode": plan.retrieval_mode,
        "retrieval_engine": plan.retrieval_engine,
        "knowledge_matches": [match.model_dump() for match in plan.knowledge_matches],
        "model_call": plan.model_call.model_dump() if plan.model_call else None,
        "auto_reply_threshold": AUTO_REPLY_CONFIDENCE_THRESHOLD,
    }


def _reply_confidence_from_knowledge_match(match_confidence: float, matched_terms: list[str]) -> float:
    term_bonus = min(len(matched_terms), 5) * 0.04
    return round(min(0.95, max(match_confidence, 0.70 + term_bonus)), 4)


def _resolve_manual_plan(payload: ReplyOrchestrationCreate) -> ResolvedReplyPlan:
    return ResolvedReplyPlan(
        intent=payload.intent or "general_inquiry",
        retrieved_knowledge_count=int(payload.retrieved_knowledge_count or 0),
        draft_reply=payload.draft_reply or "",
        confidence=float(payload.confidence or 0),
        risk_level=payload.risk_level,
        draft_source="manual",
        retrieval_mode="manual",
        retrieval_engine="manual",
        knowledge_matches=[],
    )


def _to_reply_knowledge_match(match) -> ReplyKnowledgeMatchRead:
    return ReplyKnowledgeMatchRead(
        source_kind="knowledge_card",
        card_id=match.card.id,
        title=match.card.title,
        score=match.score,
        confidence=match.confidence,
        matched_terms=match.matched_terms,
        source_type=match.card.source_type,
        source_uri=match.card.source_uri,
        content_preview=match.card.answer[:600],
        citation={
            "card_id": match.card.id,
            "title": match.card.title,
            "source_uri": match.card.source_uri,
        },
    )


def _to_reply_document_match(match) -> ReplyKnowledgeMatchRead:
    return ReplyKnowledgeMatchRead(
        source_kind="document_chunk",
        card_id=None,
        document_id=match.document_id,
        chunk_id=match.chunk_id,
        chunk_index=match.chunk_index,
        title=match.document_title,
        score=match.score,
        confidence=match.confidence,
        matched_terms=match.matched_terms,
        source_type=match.source_type,
        source_uri=match.source_uri,
        content_preview=match.content_preview,
        citation=match.citation,
    )


def _to_model_knowledge(match) -> ModelDraftKnowledge:
    return ModelDraftKnowledge(
        title=match.card.title,
        answer=match.card.answer,
        source_uri=match.card.source_uri,
        matched_terms=match.matched_terms,
    )


def _to_reply_model_call(result: ModelDraftResult) -> ReplyModelCallRead:
    return ReplyModelCallRead(
        provider=result.provider,
        model=result.model,
        status=result.status,
        prompt_summary=result.prompt_summary,
        prompt_chars=result.prompt_chars,
        completion_chars=result.completion_chars,
        total_chars=result.total_chars,
        error_message=result.error_message,
        route_name=result.route_name,
        complexity=result.complexity,
        target_model_tier=result.target_model_tier,
        fallback_chain=result.fallback_chain or [],
        human_review_required=result.human_review_required,
        route_reasons=result.route_reasons or [],
        estimated_cost=result.estimated_cost,
        cost_currency=result.cost_currency,
        pricing_source=result.pricing_source,
        pricing_version=result.pricing_version,
        budget_status=result.budget_status,
        budget_reason=result.budget_reason,
        budget_action=result.budget_action,
    )


def _estimated_model_input_units(message: Message, matches) -> int:
    knowledge_units = 0
    for match in matches:
        knowledge_units += len(match.card.title) + len(match.card.answer) + len(" ".join(match.matched_terms))
    # Includes the fixed system instructions and the short structured prompt envelope.
    return len(message.content) + knowledge_units + 600


def _with_budget_metadata(
    result: ModelDraftResult,
    *,
    budget_decision,
    status: str | None = None,
    draft_text: str | None = None,
    error_message: str | None = None,
    route_reasons: list[str] | None = None,
    budget_action: str | None = None,
) -> ModelDraftResult:
    estimate = budget_decision.estimate
    return replace(
        result,
        status=status or result.status,
        draft_text=draft_text if draft_text is not None else result.draft_text,
        error_message=error_message if error_message is not None else result.error_message,
        route_reasons=route_reasons if route_reasons is not None else result.route_reasons,
        estimated_cost=estimate.estimated_cost,
        cost_currency=estimate.currency,
        pricing_source=estimate.pricing_source,
        pricing_version=estimate.pricing_version,
        budget_status=budget_decision.status,
        budget_reason=budget_decision.reason,
        budget_action=budget_action or budget_decision.action,
        budget_policy_snapshot=budget_decision.policy_snapshot,
    )


def _run_knowledge_search(
    db: Session,
    conversation: Conversation,
    message: Message,
    payload: ReplyOrchestrationCreate,
    principal: CurrentPrincipal,
) -> tuple[str, object, list[ReplyKnowledgeMatchRead]]:
    query = payload.knowledge_query or message.content
    search_result = search_knowledge_cards(
        db,
        conversation.tenant_id,
        KnowledgeSearchRequest(query=query, top_k=payload.knowledge_top_k, status="active"),
        principal,
    )
    matches = [_to_reply_knowledge_match(match) for match in search_result.matches]
    return query, search_result, matches


def _resolve_knowledge_search_plan(
    db: Session,
    conversation: Conversation,
    message: Message,
    payload: ReplyOrchestrationCreate,
    principal: CurrentPrincipal,
) -> ResolvedReplyPlan:
    _, search_result, matches = _run_knowledge_search(db, conversation, message, payload, principal)
    if not search_result.matches:
        return ResolvedReplyPlan(
            intent=payload.intent or "general_inquiry",
            retrieved_knowledge_count=0,
            draft_reply="暂时没有找到可引用的知识，请人工确认后回复。",
            confidence=0.0,
            risk_level=payload.risk_level,
            draft_source="no_knowledge",
            retrieval_mode="knowledge_search",
            retrieval_engine=search_result.retrieval_mode,
            knowledge_matches=[],
        )

    top_match = search_result.matches[0]
    return ResolvedReplyPlan(
        intent=payload.intent or "general_inquiry",
        retrieved_knowledge_count=len(search_result.matches),
        draft_reply=top_match.card.answer,
        confidence=_reply_confidence_from_knowledge_match(top_match.confidence, top_match.matched_terms),
        risk_level=payload.risk_level,
        draft_source="knowledge_card",
        retrieval_mode="knowledge_search",
        retrieval_engine=search_result.retrieval_mode,
        knowledge_matches=matches,
    )


def _resolve_document_rag_plan(
    db: Session,
    conversation: Conversation,
    message: Message,
    payload: ReplyOrchestrationCreate,
    principal: CurrentPrincipal,
) -> ResolvedReplyPlan:
    query = payload.knowledge_query or message.content
    search_result = search_knowledge_documents(
        db,
        conversation.tenant_id,
        KnowledgeDocumentSearchRequest(query=query, top_k=payload.knowledge_top_k, status="active"),
        principal,
    )
    matches = [_to_reply_document_match(match) for match in search_result.matches]
    if not search_result.matches:
        return ResolvedReplyPlan(
            intent=payload.intent or "general_inquiry",
            retrieved_knowledge_count=0,
            draft_reply="暂时没有找到可引用的文档片段，请人工确认后回复。",
            confidence=0.0,
            risk_level=payload.risk_level,
            draft_source="no_document_chunk",
            retrieval_mode="document_rag",
            retrieval_engine=search_result.retrieval_mode,
            knowledge_matches=[],
        )

    top_match = search_result.matches[0]
    return ResolvedReplyPlan(
        intent=payload.intent or "general_inquiry",
        retrieved_knowledge_count=len(search_result.matches),
        draft_reply=f"根据《{top_match.document_title}》：{top_match.content_preview}",
        confidence=_reply_confidence_from_knowledge_match(top_match.confidence, top_match.matched_terms),
        risk_level=payload.risk_level,
        draft_source="document_chunk",
        retrieval_mode="document_rag",
        retrieval_engine=search_result.retrieval_mode,
        knowledge_matches=matches,
    )


def _resolve_model_assisted_plan(
    db: Session,
    conversation: Conversation,
    message: Message,
    payload: ReplyOrchestrationCreate,
    principal: CurrentPrincipal,
) -> ResolvedReplyPlan:
    _, search_result, matches = _run_knowledge_search(db, conversation, message, payload, principal)
    if not search_result.matches:
        return ResolvedReplyPlan(
            intent=payload.intent or "general_inquiry",
            retrieved_knowledge_count=0,
            draft_reply="暂时没有找到可引用的知识，请人工确认后回复。",
            confidence=0.0,
            risk_level=payload.risk_level,
            draft_source="no_knowledge",
            retrieval_mode="knowledge_search",
            retrieval_engine=search_result.retrieval_mode,
            knowledge_matches=[],
            model_call=None,
        )

    top_match = search_result.matches[0]
    routed_confidence = _reply_confidence_from_knowledge_match(top_match.confidence, top_match.matched_terms)
    model_request = ModelDraftRequest(
        user_message=message.content,
        intent=payload.intent or "general_inquiry",
        knowledge=[_to_model_knowledge(match) for match in search_result.matches],
        provider=payload.model_provider,
        model=payload.model_name,
        temperature=payload.model_temperature,
        confidence=routed_confidence,
        risk_level=payload.risk_level,
    )
    planned_route = select_model_route(
        user_message=model_request.user_message,
        intent=model_request.intent,
        risk_level=model_request.risk_level,
        confidence=model_request.confidence,
        knowledge_count=len(model_request.knowledge),
        requested_provider=model_request.provider,
        requested_model=model_request.model,
    )
    estimated_input_units = _estimated_model_input_units(message, search_result.matches)
    planned_estimate = estimate_route_cost(planned_route, input_units=estimated_input_units, output_units=700)
    budget_decision = evaluate_budget(db, tenant_id=conversation.tenant_id, estimate=planned_estimate)
    if not budget_decision.allowed and payload.model_provider == "auto" and planned_route.provider != DETERMINISTIC_PROVIDER:
        deterministic_result = generate_reply_draft(
            replace(model_request, provider=DETERMINISTIC_PROVIDER, model=DETERMINISTIC_MODEL)
        )
        model_result = _with_budget_metadata(
            deterministic_result,
            budget_decision=budget_decision,
            status="degraded",
            error_message=f"model budget limited: {budget_decision.reason}",
            route_reasons=(deterministic_result.route_reasons or [])
            + [
                f"budget_limited_original_provider={planned_route.provider}",
                f"budget_limited_original_model={planned_route.model}",
                f"budget_reason={budget_decision.reason}",
            ],
            budget_action="budget_degraded_to_deterministic",
        )
        model_result = replace(
            model_result,
            estimated_cost=0.0,
            pricing_source="deterministic_no_external_cost",
            pricing_version="local-deterministic",
        )
    elif not budget_decision.allowed:
        model_result = ModelDraftResult(
            provider=planned_route.provider,
            model=planned_route.model,
            status="budget_blocked",
            draft_text="当前模型预算不足，请人工根据已命中知识确认后回复。",
            prompt_summary=f"intent={model_request.intent}, knowledge_matches={len(model_request.knowledge)}",
            prompt_chars=planned_estimate.input_units,
            completion_chars=0,
            total_chars=planned_estimate.total_units,
            error_message=f"model budget limited: {budget_decision.reason}",
            route_name=planned_route.route_name,
            complexity=planned_route.complexity,
            target_model_tier=planned_route.target_model_tier,
            fallback_chain=planned_route.fallback_chain,
            human_review_required=True,
            route_reasons=planned_route.reasons + [f"budget_reason={budget_decision.reason}"],
            estimated_cost=0.0,
            cost_currency=planned_estimate.currency,
            pricing_source="budget_block_no_external_cost",
            pricing_version=planned_estimate.pricing_version,
            budget_status=budget_decision.status,
            budget_reason=budget_decision.reason,
            budget_action="budget_blocked",
            budget_policy_snapshot=budget_decision.policy_snapshot,
        )
    else:
        model_result = _with_budget_metadata(
            generate_reply_draft(model_request),
            budget_decision=budget_decision,
            budget_action="allow",
        )
    model_call = _to_reply_model_call(model_result)
    return ResolvedReplyPlan(
        intent=payload.intent or "general_inquiry",
        retrieved_knowledge_count=len(search_result.matches),
        draft_reply=model_result.draft_text,
        confidence=(
            _reply_confidence_from_knowledge_match(top_match.confidence, top_match.matched_terms)
            if model_result.status == "succeeded"
            else 0.0
        ),
        risk_level=payload.risk_level,
        draft_source=(
            "model_gateway"
            if model_result.status == "succeeded"
            else "model_budget_limited"
            if model_result.status in {"budget_blocked", "degraded"}
            else "model_gateway_unavailable"
        ),
        retrieval_mode="knowledge_search",
        retrieval_engine=search_result.retrieval_mode,
        knowledge_matches=matches,
        model_call=model_call,
        model_result=model_result,
    )


def _record_step_attempts(
    db: Session,
    run: WorkflowRun,
    plan: ResolvedReplyPlan,
    principal: CurrentPrincipal,
) -> None:
    add_step_attempt(
        db,
        run.id,
        WorkflowStepAttemptCreate(
            step_name="classify_intent",
            status="succeeded",
            input_summary="入站消息意图分类",
            output_summary=f"intent={plan.intent}",
        ),
        principal,
    )
    add_step_attempt(
        db,
        run.id,
        WorkflowStepAttemptCreate(
            step_name="retrieve_knowledge",
            status="succeeded",
            input_summary=f"intent={plan.intent}, retrieval_mode={plan.retrieval_mode}",
            output_summary=(
                f"{plan.retrieval_mode}/{plan.retrieval_engine} 命中 "
                f"{plan.retrieved_knowledge_count} 条候选知识"
            ),
        ),
        principal,
    )
    add_step_attempt(
        db,
        run.id,
        WorkflowStepAttemptCreate(
            step_name="draft_reply",
            status="succeeded",
            input_summary=(
                f"model_gateway/{plan.model_call.provider}, model={plan.model_call.model}, "
                f"status={plan.model_call.status}"
                if plan.model_call
                else f"基于知识候选生成回复草稿，draft_source={plan.draft_source}"
            ),
            output_summary=plan.draft_reply[:400],
        ),
        principal,
    )
    add_step_attempt(
        db,
        run.id,
        WorkflowStepAttemptCreate(
            step_name="risk_check",
            status="succeeded",
            input_summary=f"confidence={plan.confidence}, risk_level={plan.risk_level}",
            output_summary="进入人工复核判断" if _review_reason(plan) else "允许自动完成",
        ),
        principal,
    )


def orchestrate_reply_for_message(
    db: Session,
    message_id: int,
    payload: ReplyOrchestrationCreate,
    principal: CurrentPrincipal,
) -> ReplyOrchestrationRead:
    message, conversation = require_inbound_message_for_principal(db, message_id, principal)
    provenance_key = payload.idempotency_key or f"message:{message.id}:reply_orchestration:{payload.mode}:v1"
    provenance_id = build_reply_provenance_id(
        tenant_id=conversation.tenant_id,
        message_id=message.id,
        idempotency_key=provenance_key,
    )
    if payload.mode == "model_assisted":
        plan = _resolve_model_assisted_plan(db, conversation, message, payload, principal)
    elif payload.mode == "document_rag":
        plan = _resolve_document_rag_plan(db, conversation, message, payload, principal)
    elif payload.mode == "knowledge_search":
        plan = _resolve_knowledge_search_plan(db, conversation, message, payload, principal)
    else:
        plan = _resolve_manual_plan(payload)
    run = create_workflow_run(
        db,
        conversation.id,
        WorkflowRunCreate(
            trigger_message_id=message.id,
            workflow_type="customer_reply",
            current_step="classify_intent",
            idempotency_key=payload.idempotency_key,
            state_payload={
                "source": "inbound_message",
                "message_id": message.id,
                "provenance_id": provenance_id,
                "message_preview": message.content[:400],
                "orchestration_mode": payload.mode,
            },
        ),
        principal,
    )
    if plan.model_result is not None:
        create_model_call_record_from_result(
            db,
            tenant_id=conversation.tenant_id,
            channel_id=conversation.channel_id,
            conversation_id=conversation.id,
            message_id=message.id,
            workflow_run_id=run.id,
            provenance_id=provenance_id,
            idempotency_key=f"{provenance_id}:workflow:{run.id}:model_call:v1",
            result=plan.model_result,
            budget_policy_snapshot={
                "phase": "h2w7b_model_cost_budget_gate",
                "external_write_allowed": False,
                "budget_gate_enforced": True,
            },
            degrade_action="",
        )
    create_reply_match_citation_snapshots(
        db,
        tenant_id=conversation.tenant_id,
        provenance_id=provenance_id,
        workflow_run_id=run.id,
        matches=plan.knowledge_matches,
        no_citation_reason=_review_reason(plan) or "",
    )
    _record_step_attempts(db, run, plan, principal)

    reason = _review_reason(plan)
    if reason is not None:
        decision = "human_review"
        state_payload = _state_payload(plan, decision, reason, provenance_id)
        add_checkpoint(
            db,
            run.id,
            WorkflowCheckpointCreate(
                step_name="risk_check",
                status="waiting_human",
                state_payload=state_payload,
                input_summary="回复草稿未达到自动发送条件",
                output_summary=f"进入人工复核：{reason}",
            ),
            principal,
        )
        review_task = create_human_review_task(
            db,
            run.id,
            HumanReviewTaskCreate(
                reason=reason,
                risk_level=plan.risk_level,
                draft_reply=plan.draft_reply,
            ),
            principal,
        )
        db.refresh(run)
        return ReplyOrchestrationRead(
            decision=decision,
            reason=reason,
            workflow_run=run,
            human_review_task=review_task,
            draft_reply=plan.draft_reply,
            knowledge_matches=plan.knowledge_matches,
            model_call=plan.model_call,
        )

    decision = "completed"
    reason = "high_confidence_low_risk"
    state_payload = _state_payload(plan, decision, reason, provenance_id)
    add_checkpoint(
        db,
        run.id,
        WorkflowCheckpointCreate(
            step_name="risk_check",
            status="completed",
            state_payload=state_payload,
            input_summary="回复草稿达到自动完成条件",
            output_summary="记录为可自动回复草稿",
        ),
        principal,
    )
    run = complete_workflow_run(
        db,
        run.id,
        current_step="record_result",
        state_payload=state_payload,
        principal=principal,
    )
    return ReplyOrchestrationRead(
        decision=decision,
        reason=reason,
        workflow_run=run,
        human_review_task=None,
        draft_reply=plan.draft_reply,
        knowledge_matches=plan.knowledge_matches,
        model_call=plan.model_call,
    )
