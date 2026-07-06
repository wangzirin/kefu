import re
from dataclasses import dataclass

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.core.audit import add_audit_event
from app.core.auth import CurrentPrincipal
from app.models import (
    BusinessObject,
    BusinessObjectAlias,
    Channel,
    ChannelConnector,
    Conversation,
    Message,
    ObjectKnowledgeCard,
    ReplyDecision,
)
from app.models.foundation import utc_now
from app.schemas.reply_decisions import ReplyDecisionCreate, ReplyDecisionList, ReplyDecisionRead
from app.services.reply_provenance import (
    build_reply_provenance_id,
    create_reply_decision_citation_snapshot,
)
from app.services.reply_strategy_config import resolve_effective_reply_strategy


TOKEN_RE = re.compile(r"[a-z0-9]+|[\u4e00-\u9fff]+")
BLOCKED_POLICY_TERMS = {
    "私下转账",
    "线下付款",
    "绕过平台",
    "刷单",
    "虚假交易",
    "保证收益",
    "百分百保证",
    "100%保证",
}
MANUAL_REVIEW_TERMS = {
    "投诉",
    "起诉",
    "律师",
    "赔偿",
    "举报",
    "监管",
    "工商",
    "差评",
    "封号",
    "违约",
    "法务",
}


@dataclass(frozen=True)
class MatchResult:
    score: float
    matched_terms: list[str]
    exact_hits: list[str]


@dataclass(frozen=True)
class CandidateDecision:
    state: str
    reason: str
    confidence: float
    delivery_mode: str
    draft_reply: str
    matched_terms: list[str]
    business_object: BusinessObject | None
    card: ObjectKnowledgeCard | None
    payload: dict


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", "", value.strip().lower())


def _tokenize(text: str) -> list[str]:
    tokens: list[str] = []
    for segment in TOKEN_RE.findall(text.lower()):
        if segment.isascii():
            tokens.append(segment)
            continue
        tokens.append(segment)
        if len(segment) <= 1:
            continue
        tokens.extend(segment[index : index + 2] for index in range(len(segment) - 1))
        if len(segment) >= 3:
            tokens.extend(segment[index : index + 3] for index in range(len(segment) - 2))
    return tokens


def _clean_terms(values: list[str], *, limit: int = 12) -> list[str]:
    cleaned: list[str] = []
    seen: set[str] = set()
    for value in values:
        item = value.strip()
        if not item or item in seen:
            continue
        cleaned.append(item)
        seen.add(item)
        if len(cleaned) >= limit:
            break
    return cleaned


def _keyword_hits(normalized_query: str, terms: set[str]) -> list[str]:
    return _clean_terms([term for term in terms if term and _normalize_text(term) in normalized_query])


def _weighted_match(query: str, weighted_chunks: list[tuple[str, float]]) -> MatchResult:
    normalized_query = _normalize_text(query)
    query_terms = set(_tokenize(query))
    score = 0.0
    matched_terms: list[str] = []
    exact_hits: list[str] = []
    for text, weight in weighted_chunks:
        clean_text = text.strip()
        if not clean_text:
            continue
        normalized_text = _normalize_text(clean_text)
        if normalized_text and normalized_text in normalized_query:
            exact_hits.append(clean_text)
            score += min(0.35, weight * 0.7)
        field_terms = set(_tokenize(clean_text))
        if not field_terms:
            continue
        overlaps = sorted(query_terms.intersection(field_terms), key=lambda value: (-len(value), value))
        matched_terms.extend(overlaps[:8])
        denominator = max(1, min(len(field_terms), max(len(query_terms), 1)))
        score += min(1.0, len(overlaps) / denominator) * weight
    score = round(min(0.98, score), 4)
    return MatchResult(score=score, matched_terms=_clean_terms(matched_terms), exact_hits=_clean_terms(exact_hits))


def _message_for_principal(db: Session, message_id: int, principal: CurrentPrincipal) -> tuple[Message, Conversation]:
    message = db.scalar(
        select(Message)
        .options(joinedload(Message.conversation))
        .where(Message.id == message_id)
    )
    if message is None or message.conversation.tenant_id != principal.tenant.id:
        raise HTTPException(status_code=404, detail="message not found")
    if message.direction != "inbound":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="only inbound messages can be evaluated for reply decisions",
        )
    return message, message.conversation


def _object_aliases(db: Session, business_object_id: int, channel_type: str) -> list[str]:
    aliases = db.scalars(
        select(BusinessObjectAlias)
        .where(BusinessObjectAlias.business_object_id == business_object_id)
        .order_by(BusinessObjectAlias.id.asc())
    ).all()
    return [
        alias.alias
        for alias in aliases
        if alias.channel_scope in {"all", channel_type, ""}
    ]


def _best_business_object(
    db: Session,
    tenant_id: int,
    channel_type: str,
    message_text: str,
) -> tuple[BusinessObject | None, MatchResult]:
    candidates = db.scalars(
        select(BusinessObject)
        .where(BusinessObject.tenant_id == tenant_id, BusinessObject.status == "active")
        .order_by(BusinessObject.type.asc(), BusinessObject.title.asc(), BusinessObject.id.asc())
    ).all()
    best_object: BusinessObject | None = None
    best_match = MatchResult(score=0.0, matched_terms=[], exact_hits=[])
    for item in candidates:
        aliases = _object_aliases(db, item.id, channel_type)
        match = _weighted_match(
            message_text,
            [(item.title, 0.34), (item.external_id, 0.08), (item.summary, 0.12)]
            + [(alias, 0.5) for alias in aliases],
        )
        if match.score > best_match.score:
            best_object = item
            best_match = match
    if best_match.score < 0.22:
        return None, best_match
    return best_object, best_match


def _best_object_card(
    db: Session,
    business_object: BusinessObject,
    message_text: str,
) -> tuple[ObjectKnowledgeCard | None, MatchResult]:
    cards = db.scalars(
        select(ObjectKnowledgeCard)
        .where(
            ObjectKnowledgeCard.business_object_id == business_object.id,
            ObjectKnowledgeCard.status == "active",
        )
        .order_by(ObjectKnowledgeCard.updated_at.desc(), ObjectKnowledgeCard.id.desc())
    ).all()
    best_card: ObjectKnowledgeCard | None = None
    best_match = MatchResult(score=0.0, matched_terms=[], exact_hits=[])
    for card in cards:
        match = _weighted_match(
            message_text,
            [(keyword, 0.42) for keyword in card.trigger_keywords]
            + [(card.question, 0.42), (card.answer, 0.08), (card.source, 0.04)],
        )
        if match.score > best_match.score:
            best_card = card
            best_match = match
    return best_card, best_match


def _channel_external_write_enabled(db: Session, tenant_id: int, channel_id: int) -> bool:
    connector = db.scalar(
        select(ChannelConnector)
        .where(ChannelConnector.tenant_id == tenant_id, ChannelConnector.channel_id == channel_id)
        .order_by(ChannelConnector.id.desc())
        .limit(1)
    )
    return bool(connector and connector.status == "active" and connector.external_write_enabled)


def _decide(
    db: Session,
    conversation: Conversation,
    message: Message,
    payload: ReplyDecisionCreate,
) -> CandidateDecision:
    text = message.content.strip()
    normalized_text = _normalize_text(text)
    strategy = resolve_effective_reply_strategy(
        db,
        tenant_id=conversation.tenant_id,
        default_blocked_terms=BLOCKED_POLICY_TERMS,
        default_manual_terms=MANUAL_REVIEW_TERMS,
    )
    blocked_terms = _keyword_hits(normalized_text, strategy.blocked_policy_terms)
    manual_terms = _keyword_hits(normalized_text, strategy.manual_review_terms)
    auto_reply_threshold = strategy.auto_reply_threshold if strategy.auto_reply_threshold is not None else payload.auto_reply_threshold
    manual_review_threshold = (
        strategy.manual_review_threshold
        if strategy.manual_review_threshold is not None
        else payload.manual_review_threshold
    )
    force_draft_only = payload.force_draft_only or strategy.force_draft_only
    channel = db.get(Channel, conversation.channel_id)
    channel_type = channel.type if channel else ""
    business_object, object_match = _best_business_object(db, conversation.tenant_id, channel_type, text)

    base_payload = {
        "message_preview": text[:400],
        "object_match_score": object_match.score,
        "object_matched_terms": object_match.matched_terms,
        "object_exact_hits": object_match.exact_hits,
        "blocked_terms": blocked_terms,
        "manual_review_terms": manual_terms,
        "thresholds": {
            "auto_reply": auto_reply_threshold,
            "manual_review": manual_review_threshold,
        },
        "strategy": {
            "strategy_id": strategy.strategy_id,
            "strategy_version": strategy.strategy_version,
            "force_draft_only": strategy.force_draft_only,
            "model_routing": strategy.model_routing,
        },
        "external_write_requested": payload.external_write_allowed,
        "force_draft_only": force_draft_only,
    }

    if blocked_terms:
        return CandidateDecision(
            state="blocked_by_policy",
            reason="blocked_policy_terms",
            confidence=0.0,
            delivery_mode="blocked",
            draft_reply="",
            matched_terms=blocked_terms,
            business_object=business_object,
            card=None,
            payload={**base_payload, "decision_note": "命中禁止外发或平台风险词，不能自动回复。"},
        )

    if business_object is None:
        return CandidateDecision(
            state="knowledge_gap",
            reason="no_business_object_match",
            confidence=object_match.score,
            delivery_mode="human_review",
            draft_reply="",
            matched_terms=object_match.matched_terms,
            business_object=None,
            card=None,
            payload={**base_payload, "decision_note": "未命中业务对象，需要补对象或人工确认。"},
        )

    card, card_match = _best_object_card(db, business_object, text)
    confidence = round(min(0.98, max(object_match.score * 0.35 + card_match.score * 0.65, card_match.score)), 4)
    matched_terms = _clean_terms(object_match.exact_hits + card_match.exact_hits + card_match.matched_terms + object_match.matched_terms)
    decision_payload = {
        **base_payload,
        "business_object": {
            "id": business_object.id,
            "type": business_object.type,
            "title": business_object.title,
        },
        "card_match_score": card_match.score,
        "card_matched_terms": card_match.matched_terms,
        "card_exact_hits": card_match.exact_hits,
    }

    if card is None or card_match.score < manual_review_threshold:
        return CandidateDecision(
            state="knowledge_gap",
            reason="object_matched_no_confident_card",
            confidence=confidence,
            delivery_mode="human_review",
            draft_reply="",
            matched_terms=matched_terms,
            business_object=business_object,
            card=card,
            payload={**decision_payload, "decision_note": "命中业务对象但没有可信对象问答卡。"},
        )

    if manual_terms:
        return CandidateDecision(
            state="manual_gate_required",
            reason="manual_review_terms",
            confidence=confidence,
            delivery_mode="human_review",
            draft_reply=card.answer,
            matched_terms=_clean_terms(manual_terms + matched_terms),
            business_object=business_object,
            card=card,
            payload={**decision_payload, "decision_note": "命中投诉、法务或赔付等人工门禁词。"},
        )

    if confidence < auto_reply_threshold:
        return CandidateDecision(
            state="manual_gate_required",
            reason="low_confidence_object_card",
            confidence=confidence,
            delivery_mode="human_review",
            draft_reply=card.answer,
            matched_terms=matched_terms,
            business_object=business_object,
            card=card,
            payload={**decision_payload, "decision_note": "对象问答卡命中不足以自动回复。"},
        )

    external_write_enabled = _channel_external_write_enabled(db, conversation.tenant_id, conversation.channel_id)
    external_write_allowed = payload.external_write_allowed and external_write_enabled and not force_draft_only
    return CandidateDecision(
        state="auto_reply_ready",
        reason="object_card_high_confidence",
        confidence=confidence,
        delivery_mode="external_write_allowed" if external_write_allowed else "draft_only",
        draft_reply=card.answer,
        matched_terms=matched_terms,
        business_object=business_object,
        card=card,
        payload={
            **decision_payload,
            "external_write_enabled_by_channel": external_write_enabled,
            "external_write_allowed_after_gate": external_write_allowed,
            "decision_note": "命中高置信对象问答卡；当前切片只记录可回复状态，不执行真实发送。",
        },
    )


def create_reply_decision_for_message(
    db: Session,
    message_id: int,
    payload: ReplyDecisionCreate,
    principal: CurrentPrincipal,
) -> ReplyDecision:
    message, conversation = _message_for_principal(db, message_id, principal)
    idempotency_key = payload.idempotency_key.strip() or f"message:{message.id}:reply_decision:v1"
    existing = db.scalar(
        select(ReplyDecision).where(
            ReplyDecision.tenant_id == conversation.tenant_id,
            ReplyDecision.idempotency_key == idempotency_key,
        )
    )
    if existing is not None:
        if existing.message_id != message.id:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="idempotency key already used")
        return existing

    provenance_id = build_reply_provenance_id(
        tenant_id=conversation.tenant_id,
        message_id=message.id,
        idempotency_key=idempotency_key,
    )
    decision = _decide(db, conversation, message, payload)
    external_write_allowed = (
        decision.state == "auto_reply_ready"
        and decision.delivery_mode == "external_write_allowed"
        and bool(decision.payload.get("external_write_allowed_after_gate"))
    )
    now = utc_now()
    decision_payload = {
        **decision.payload,
        "provenance": {
            "provenance_id": provenance_id,
            "tenant_id": conversation.tenant_id,
            "conversation_id": conversation.id,
            "message_id": message.id,
            "channel_id": conversation.channel_id,
            "model_call_recorded": False,
            "citation_snapshot_expected": True,
            "external_write_allowed": external_write_allowed,
        },
    }
    record = ReplyDecision(
        tenant_id=conversation.tenant_id,
        conversation_id=conversation.id,
        message_id=message.id,
        channel_id=conversation.channel_id,
        business_object_id=decision.business_object.id if decision.business_object else None,
        object_knowledge_card_id=decision.card.id if decision.card else None,
        workflow_run_id=None,
        provenance_id=provenance_id,
        state=decision.state,
        reason=decision.reason,
        confidence=decision.confidence,
        delivery_mode=decision.delivery_mode,
        draft_reply=decision.draft_reply,
        matched_terms=decision.matched_terms,
        decision_payload=decision_payload,
        external_write_allowed=external_write_allowed,
        idempotency_key=idempotency_key,
        created_by_id=principal.user.id,
        created_at=now,
    )
    db.add(record)
    db.flush()
    record.decision_payload = {
        **record.decision_payload,
        "provenance": {
            **record.decision_payload.get("provenance", {}),
            "reply_decision_id": record.id,
        },
    }
    create_reply_decision_citation_snapshot(db, decision=record, card=decision.card)
    add_audit_event(
        db,
        tenant_id=conversation.tenant_id,
        actor_id=principal.user.id,
        action="reply_decision.created",
        resource_type="reply_decision",
        resource_id=str(record.id),
        payload={
            "message_id": message.id,
            "conversation_id": conversation.id,
            "state": record.state,
            "reason": record.reason,
            "confidence": record.confidence,
            "delivery_mode": record.delivery_mode,
            "business_object_id": record.business_object_id,
            "object_knowledge_card_id": record.object_knowledge_card_id,
            "external_write_allowed": record.external_write_allowed,
            "provenance_id": record.provenance_id,
        },
    )
    db.commit()
    db.refresh(record)
    return record


def list_reply_decisions(
    db: Session,
    tenant_id: int,
    *,
    state_filter: str | None,
    conversation_id: int | None,
    page: int,
    page_size: int,
    principal: CurrentPrincipal,
) -> ReplyDecisionList:
    if principal.tenant.id != tenant_id:
        raise HTTPException(status_code=404, detail="tenant not found")
    query = select(ReplyDecision).where(ReplyDecision.tenant_id == tenant_id)
    count_query = select(func.count(ReplyDecision.id)).where(ReplyDecision.tenant_id == tenant_id)
    if state_filter:
        query = query.where(ReplyDecision.state == state_filter)
        count_query = count_query.where(ReplyDecision.state == state_filter)
    if conversation_id is not None:
        query = query.where(ReplyDecision.conversation_id == conversation_id)
        count_query = count_query.where(ReplyDecision.conversation_id == conversation_id)
    query = query.order_by(ReplyDecision.created_at.desc(), ReplyDecision.id.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    return ReplyDecisionList(
        items=[
            ReplyDecisionRead.model_validate(item, from_attributes=True)
            for item in db.scalars(query).all()
        ],
        page=page,
        page_size=page_size,
        total=int(db.scalar(count_query) or 0),
    )
