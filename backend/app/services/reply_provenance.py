from __future__ import annotations

from hashlib import sha256
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    ModelCallRecord,
    ObjectKnowledgeCard,
    ReplyCitationSnapshot,
    ReplyDecision,
)
from app.models.foundation import utc_now


def stable_text_hash(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def build_reply_provenance_id(*, tenant_id: int, message_id: int, idempotency_key: str) -> str:
    seed = f"tenant:{tenant_id}|message:{message_id}|key:{idempotency_key}"
    digest = sha256(seed.encode("utf-8")).hexdigest()[:16]
    return f"rp_t{tenant_id}_m{message_id}_{digest}"


def create_reply_decision_citation_snapshot(
    db: Session,
    *,
    decision: ReplyDecision,
    card: ObjectKnowledgeCard | None,
) -> ReplyCitationSnapshot:
    if card is None:
        snapshot = ReplyCitationSnapshot(
            tenant_id=decision.tenant_id,
            provenance_id=decision.provenance_id,
            reply_decision_id=decision.id,
            workflow_run_id=decision.workflow_run_id,
            source_kind="no_citation",
            score=decision.confidence,
            no_citation_reason=f"{decision.state}:{decision.reason}",
            citation_payload={
                "state": decision.state,
                "reason": decision.reason,
                "reply_decision_id": decision.id,
                "message_id": decision.message_id,
            },
            created_at=utc_now(),
        )
        db.add(snapshot)
        return snapshot

    snapshot = ReplyCitationSnapshot(
        tenant_id=decision.tenant_id,
        provenance_id=decision.provenance_id,
        reply_decision_id=decision.id,
        workflow_run_id=decision.workflow_run_id,
        source_kind="object_knowledge_card",
        object_knowledge_card_id=card.id,
        source_version=f"v{card.version}",
        content_hash=stable_text_hash(card.answer),
        source_uri=card.source or f"object_knowledge_card:{card.id}",
        score=decision.confidence,
        citation_payload={
            "business_object_id": card.business_object_id,
            "object_knowledge_card_id": card.id,
            "question_hash": stable_text_hash(card.question),
            "answer_hash": stable_text_hash(card.answer),
            "source": card.source,
            "version": card.version,
            "matched_terms": decision.matched_terms[:12],
        },
        created_at=utc_now(),
    )
    db.add(snapshot)
    return snapshot


def create_reply_match_citation_snapshots(
    db: Session,
    *,
    tenant_id: int,
    provenance_id: str,
    workflow_run_id: int,
    matches: list[Any],
    no_citation_reason: str = "",
) -> list[ReplyCitationSnapshot]:
    snapshots: list[ReplyCitationSnapshot] = []
    if not matches:
        snapshot = ReplyCitationSnapshot(
            tenant_id=tenant_id,
            provenance_id=provenance_id,
            workflow_run_id=workflow_run_id,
            source_kind="no_citation",
            no_citation_reason=no_citation_reason or "no_knowledge_match",
            citation_payload={"workflow_run_id": workflow_run_id},
            created_at=utc_now(),
        )
        db.add(snapshot)
        return [snapshot]

    for match in matches:
        payload = match.model_dump() if hasattr(match, "model_dump") else dict(match)
        content_preview = str(payload.get("content_preview") or "")
        citation = payload.get("citation") if isinstance(payload.get("citation"), dict) else {}
        source_kind = str(payload.get("source_kind") or "")
        snapshot = ReplyCitationSnapshot(
            tenant_id=tenant_id,
            provenance_id=provenance_id,
            workflow_run_id=workflow_run_id,
            source_kind=source_kind or "knowledge_match",
            knowledge_card_id=payload.get("card_id"),
            document_id=payload.get("document_id"),
            document_chunk_id=payload.get("chunk_id"),
            chunk_index=payload.get("chunk_index"),
            source_version=str(citation.get("version") or citation.get("source_version") or ""),
            content_hash=stable_text_hash(content_preview) if content_preview else "",
            source_uri=str(payload.get("source_uri") or citation.get("source_uri") or ""),
            score=float(payload.get("confidence") or payload.get("score") or 0),
            citation_payload={
                "title_hash": stable_text_hash(str(payload.get("title") or "")),
                "source_type": payload.get("source_type"),
                "matched_terms": list(payload.get("matched_terms") or [])[:12],
                "citation": citation,
            },
            created_at=utc_now(),
        )
        db.add(snapshot)
        snapshots.append(snapshot)
    return snapshots


def create_model_call_record_from_result(
    db: Session,
    *,
    tenant_id: int,
    channel_id: int | None,
    conversation_id: int | None,
    message_id: int | None,
    workflow_run_id: int | None,
    reply_decision_id: int | None = None,
    provenance_id: str,
    idempotency_key: str,
    result: Any,
    budget_policy_snapshot: dict | None = None,
    degrade_action: str = "",
) -> ModelCallRecord:
    existing = db.scalar(
        select(ModelCallRecord).where(
            ModelCallRecord.tenant_id == tenant_id,
            ModelCallRecord.idempotency_key == idempotency_key,
        )
    )
    if existing is not None:
        return existing

    provider = str(getattr(result, "provider", ""))
    result_budget_snapshot = getattr(result, "budget_policy_snapshot", None)
    merged_budget_snapshot = {
        **(budget_policy_snapshot or {}),
        **(result_budget_snapshot if isinstance(result_budget_snapshot, dict) else {}),
    }
    pricing_source = str(getattr(result, "pricing_source", "") or "")
    if not pricing_source:
        pricing_source = "deterministic_no_external_cost" if provider == "deterministic" else "provider_usage_recorded_without_price_table"
    status = str(getattr(result, "status", ""))
    fallback_chain = list(getattr(result, "fallback_chain", None) or [])
    route_reasons = list(getattr(result, "route_reasons", None) or [])
    record = ModelCallRecord(
        tenant_id=tenant_id,
        channel_id=channel_id,
        conversation_id=conversation_id,
        message_id=message_id,
        workflow_run_id=workflow_run_id,
        reply_decision_id=reply_decision_id,
        provenance_id=provenance_id,
        idempotency_key=idempotency_key,
        provider=provider,
        model=str(getattr(result, "model", "")),
        route_name=str(getattr(result, "route_name", "")),
        target_model_tier=str(getattr(result, "target_model_tier", "")),
        complexity=str(getattr(result, "complexity", "")),
        status=status,
        error_code=status if status != "succeeded" else "",
        input_units=int(getattr(result, "prompt_chars", 0) or 0),
        output_units=int(getattr(result, "completion_chars", 0) or 0),
        total_units=int(getattr(result, "total_chars", 0) or 0),
        unit_type="tokens_or_chars",
        estimated_cost=float(getattr(result, "estimated_cost", 0.0) or 0.0),
        currency=str(getattr(result, "cost_currency", "") or "CNY"),
        pricing_source=pricing_source,
        pricing_version=str(getattr(result, "pricing_version", "") or "h2w7b_operator_config"),
        budget_policy_snapshot=merged_budget_snapshot,
        degrade_action=degrade_action or str(getattr(result, "budget_action", "") or ""),
        raw_text_logged=False,
        metadata_payload={
            "prompt_summary": str(getattr(result, "prompt_summary", "")),
            "fallback_chain": fallback_chain,
            "human_review_required": bool(getattr(result, "human_review_required", False)),
            "route_reasons": route_reasons,
            "budget_status": str(getattr(result, "budget_status", "") or ""),
            "budget_reason": str(getattr(result, "budget_reason", "") or ""),
            "error_present": bool(getattr(result, "error_message", "")),
        },
        created_at=utc_now(),
    )
    db.add(record)
    return record
