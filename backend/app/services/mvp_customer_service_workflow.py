from __future__ import annotations

from dataclasses import dataclass
import re

from sqlalchemy.orm import Session

from app.core.auth import CurrentPrincipal
from app.models import Conversation, Message, ObjectKnowledgeCard
from app.schemas.knowledge import KnowledgeDocumentSearchRequest, KnowledgeSearchRequest
from app.services.knowledge import search_knowledge_cards, search_knowledge_documents
from app.services.model_gateway import ModelDraftKnowledge, ModelDraftRequest, ModelDraftResult, generate_reply_draft


WORKFLOW_NAME = "ai_customer_service_mvp"
WORKFLOW_VERSION = "2026-07-08.v1"

INJECTION_TERMS = {
    "忽略以上指令",
    "忽略之前的指令",
    "ignore previous",
    "system prompt",
    "system instruction",
    "jailbreak",
    "developer mode",
    "绕过限制",
}
SENSITIVE_TERMS = {"炸弹", "枪支", "毒品", "自杀", "自残", "杀人", "爆炸", "制毒"}
COMPLAINT_TERMS = {"投诉", "转人工", "真人客服", "人工客服", "差评", "起诉", "律师", "赔偿", "举报", "监管", "工商"}
PRODUCT_TERMS = {
    "商品",
    "产品",
    "价格",
    "多少钱",
    "库存",
    "规格",
    "参数",
    "推荐",
    "热销",
    "优惠",
    "活动",
    "下单",
    "营业时间",
    "营业",
    "上班",
    "下班",
    "开门",
    "关门",
    "几点",
    "接入",
    "客服",
    "业务",
    "合作",
    "流程",
    "费用",
    "收费",
    "套餐",
}
AFTER_SALES_TERMS = {"订单", "物流", "快递", "退货", "换货", "退款", "售后", "发票", "订单号", "查一下"}
SMALL_TALK_TERMS = {"你好", "您好", "在吗", "谢谢", "感谢", "再见", "有人吗", "早上好", "晚上好"}


@dataclass(frozen=True)
class WorkflowKnowledgeMatch:
    source_kind: str
    card_id: int
    document_id: int | None
    chunk_id: int | None
    chunk_index: int | None
    title: str
    confidence: float
    matched_terms: list[str]
    source_uri: str
    answer: str


@dataclass(frozen=True)
class MvpWorkflowResult:
    intent: str
    safety_status: str
    reply_branch: str
    state: str
    reason: str
    confidence: float
    delivery_mode: str
    draft_reply: str
    matched_terms: list[str]
    knowledge_matches: list[WorkflowKnowledgeMatch]
    handoff_required: bool
    knowledge_gap_required: bool
    risk_level: str
    model_result: ModelDraftResult | None
    payload: dict


def _contains_any(text: str, terms: set[str]) -> list[str]:
    lowered = text.lower()
    return [term for term in sorted(terms, key=len, reverse=True) if term.lower() in lowered]


def _safety_status(text: str) -> tuple[str, str]:
    if _contains_any(text, INJECTION_TERMS):
        return "blocked_prompt_injection", "用户输入已被安全系统过滤，请回复标准客服问候语并引导用户正常提问。"
    if _contains_any(text, SENSITIVE_TERMS):
        return "warning_sensitive", text
    return "safe", text


def _classify_intent(text: str) -> tuple[str, list[str]]:
    for intent, terms in (
        ("complaint_handoff", COMPLAINT_TERMS),
        ("after_sales_order", AFTER_SALES_TERMS),
        ("product_consulting", PRODUCT_TERMS),
        ("small_talk", SMALL_TALK_TERMS),
    ):
        hits = _contains_any(text, terms)
        if hits:
            return intent, hits
    if len(text.strip()) <= 8:
        return "clarify_needed", []
    return "clarify_needed", []


def _synthetic_model_reply(*, user_message: str, intent: str, instruction: str, confidence: float = 0.88) -> ModelDraftResult:
    return generate_reply_draft(
        ModelDraftRequest(
            user_message=user_message,
            intent=intent,
            knowledge=[
                ModelDraftKnowledge(
                    title=f"{intent} 回复规范",
                    answer=instruction,
                    source_uri="internal://ai-customer-service-mvp/prompt",
                    matched_terms=[],
                )
            ],
            provider="auto",
            confidence=confidence,
            risk_level="low",
        )
    )


def _order_no(text: str) -> str:
    match = re.search(r"[A-Za-z]{0,4}\d{6,}", text)
    return match.group(0) if match else ""


def _knowledge_match_payload(matches: list[WorkflowKnowledgeMatch]) -> list[dict]:
    return [
        {
            "source_kind": item.source_kind,
            "card_id": item.card_id,
            "document_id": item.document_id,
            "chunk_id": item.chunk_id,
            "chunk_index": item.chunk_index,
            "title": item.title,
            "confidence": item.confidence,
            "matched_terms": item.matched_terms,
            "source_uri": item.source_uri,
            "content_preview": item.answer[:300],
        }
        for item in matches
    ]


def _fallback_object_knowledge(db: Session, *, tenant_id: int, query: str, limit: int = 4) -> list[WorkflowKnowledgeMatch]:
    query_terms = {term for term in re.findall(r"[a-zA-Z0-9]+|[\u4e00-\u9fff]{2,}", query.lower()) if term}
    matches: list[WorkflowKnowledgeMatch] = []
    cards = (
        db.query(ObjectKnowledgeCard)
        .filter(ObjectKnowledgeCard.tenant_id == tenant_id, ObjectKnowledgeCard.status == "active")
        .order_by(ObjectKnowledgeCard.updated_at.desc(), ObjectKnowledgeCard.id.desc())
        .all()
    )
    for card in cards:
        haystack = " ".join([card.question, card.answer, " ".join(card.trigger_keywords or [])]).lower()
        hits = [term for term in sorted(query_terms, key=len, reverse=True) if term in haystack]
        keyword_hits = [term for term in (card.trigger_keywords or []) if term and term.lower() in query.lower()]
        all_hits = list(dict.fromkeys(keyword_hits + hits))
        if not all_hits:
            continue
        confidence = min(0.95, 0.68 + 0.06 * len(all_hits))
        matches.append(
            WorkflowKnowledgeMatch(
                source_kind="object_knowledge_card",
                card_id=card.id,
                document_id=None,
                chunk_id=None,
                chunk_index=None,
                title=card.question[:80] or f"对象知识卡 {card.id}",
                confidence=confidence,
                matched_terms=all_hits[:8],
                source_uri=card.source,
                answer=card.answer,
            )
        )
        if len(matches) >= limit:
            break
    return matches


def _document_chunk_reply_confidence(*, retrieval_confidence: float, score: float, matched_terms: list[str]) -> float:
    """Convert conservative retrieval confidence into an auto-reply gate score."""
    evidence_score = 0.58 + (min(score, 4.0) * 0.04) + (min(len(matched_terms), 6) * 0.025)
    return min(0.9, max(retrieval_confidence, evidence_score))


def run_mvp_customer_service_workflow(
    db: Session,
    *,
    conversation: Conversation,
    message: Message,
    principal: CurrentPrincipal | None,
) -> MvpWorkflowResult:
    safety_status, processed_text = _safety_status(message.content.strip())
    intent, intent_hits = _classify_intent(processed_text)
    if safety_status == "blocked_prompt_injection":
        intent = "small_talk"
    if safety_status == "warning_sensitive":
        intent = "complaint_handoff"

    knowledge_matches: list[WorkflowKnowledgeMatch] = []
    model_result: ModelDraftResult | None = None
    state = "manual_gate_required"
    reason = "needs_human_review"
    reply_branch = intent
    delivery_mode = "human_review"
    handoff_required = False
    knowledge_gap_required = False
    confidence = 0.0
    risk_level = "low"
    draft_reply = ""

    if intent == "product_consulting":
        if principal is not None:
            search = search_knowledge_cards(
                db,
                conversation.tenant_id,
                KnowledgeSearchRequest(query=processed_text, top_k=4, status="active"),
                principal,
            )
            for match in search.matches:
                knowledge_matches.append(
                    WorkflowKnowledgeMatch(
                        source_kind="knowledge_card",
                        card_id=match.card.id,
                        document_id=None,
                        chunk_id=None,
                        chunk_index=None,
                        title=match.card.title,
                        confidence=match.confidence,
                        matched_terms=match.matched_terms,
                        source_uri=match.card.source_uri,
                        answer=match.card.answer,
                    )
                )
        if principal is not None and not knowledge_matches:
            document_search = search_knowledge_documents(
                db,
                conversation.tenant_id,
                KnowledgeDocumentSearchRequest(query=processed_text, top_k=4, status="active"),
                principal,
            )
            for match in document_search.matches:
                knowledge_matches.append(
                    WorkflowKnowledgeMatch(
                        source_kind="document_chunk",
                        card_id=0,
                        document_id=match.document_id,
                        chunk_id=match.chunk_id,
                        chunk_index=match.chunk_index,
                        title=match.section_title or match.document_title,
                        confidence=_document_chunk_reply_confidence(
                            retrieval_confidence=match.confidence,
                            score=match.score,
                            matched_terms=match.matched_terms,
                        ),
                        matched_terms=match.matched_terms,
                        source_uri=match.source_uri,
                        answer=match.content_preview,
                    )
                )
        if not knowledge_matches:
            knowledge_matches = _fallback_object_knowledge(db, tenant_id=conversation.tenant_id, query=processed_text)
        if not knowledge_matches:
            state = "knowledge_gap"
            reason = "product_knowledge_not_found"
            delivery_mode = "human_review"
            handoff_required = True
            knowledge_gap_required = True
            reply_branch = "knowledge_gap"
            risk_level = "medium"
            draft_reply = "关于这个产品，我目前还没有可引用的知识。需要客服补充商品资料后再准确回复。"
        else:
            confidence = max(item.confidence for item in knowledge_matches)
            model_result = generate_reply_draft(
                ModelDraftRequest(
                    user_message=processed_text,
                    intent="product_consulting",
                    knowledge=[
                        ModelDraftKnowledge(
                            title=item.title,
                            answer=item.answer,
                            source_uri=item.source_uri,
                            matched_terms=item.matched_terms,
                        )
                        for item in knowledge_matches
                    ],
                    provider="auto",
                    confidence=confidence,
                    risk_level="low",
                )
            )
            draft_reply = model_result.draft_text
            state = "auto_reply_ready" if model_result.status == "succeeded" and confidence >= 0.72 else "manual_gate_required"
            reason = "product_rag_ready" if state == "auto_reply_ready" else "product_rag_low_confidence"
            reply_branch = "product_consulting_rag"
            delivery_mode = "external_write_allowed" if state == "auto_reply_ready" else "human_review"
            handoff_required = state != "auto_reply_ready"
            risk_level = "low" if state == "auto_reply_ready" else "medium"
    elif intent == "after_sales_order":
        order_no = _order_no(processed_text)
        if not order_no:
            draft_reply = "收到，我来帮您处理。请先提供一下订单号，您可以在【我的订单】里查看订单号哦。"
        else:
            draft_reply = (
                f"收到，我来帮您处理。\n"
                f"订单号：{order_no}\n"
                "我已记录您的售后需求，建议客服继续核对订单状态、商品情况和处理规则。"
            )
        model_result = _synthetic_model_reply(user_message=processed_text, intent="after_sales_order", instruction=draft_reply)
        draft_reply = model_result.draft_text or draft_reply
        confidence = 0.86
        state = "auto_reply_ready"
        reason = "after_sales_guidance_ready"
        reply_branch = "after_sales_order"
        delivery_mode = "external_write_allowed"
    elif intent == "complaint_handoff":
        draft_reply = (
            "非常抱歉给您带来不好的体验。您的反馈对我们非常重要，我会尽快帮您记录并转交处理。\n\n"
            "为了给您更好的服务体验，我将为您转接高级客服专员，他们会更专业地帮您解决这个问题。"
        )
        model_result = _synthetic_model_reply(user_message=processed_text, intent="complaint_handoff", instruction=draft_reply, confidence=0.5)
        draft_reply = model_result.draft_text or draft_reply
        confidence = 0.5
        state = "manual_gate_required"
        reason = "complaint_or_handoff_requested"
        reply_branch = "complaint_handoff"
        delivery_mode = "human_review"
        handoff_required = True
        risk_level = "high"
    elif intent == "small_talk":
        draft_reply = "您好，我是小界，您的专属客服顾问。商品咨询、订单物流、退换货问题都可以直接问我。"
        model_result = _synthetic_model_reply(user_message=processed_text, intent="small_talk", instruction=draft_reply)
        draft_reply = model_result.draft_text or draft_reply
        confidence = 0.9
        state = "auto_reply_ready"
        reason = "small_talk_ready"
        reply_branch = "small_talk"
        delivery_mode = "external_write_allowed"
    else:
        draft_reply = (
            "我来帮您看看。您是想了解商品信息，还是需要查询订单、物流、退换货呢？"
            "请告诉我具体需要什么帮助。"
        )
        model_result = _synthetic_model_reply(user_message=processed_text, intent="clarify_needed", instruction=draft_reply)
        draft_reply = model_result.draft_text or draft_reply
        confidence = 0.78
        state = "auto_reply_ready"
        reason = "clarify_question_ready"
        reply_branch = "clarify_needed"
        delivery_mode = "external_write_allowed"

    if safety_status != "safe":
        state = "manual_gate_required"
        reason = safety_status
        delivery_mode = "human_review"
        handoff_required = True
        confidence = min(confidence, 0.4)
        risk_level = "high" if safety_status == "warning_sensitive" else "medium"
        reply_branch = safety_status

    payload = {
        "workflow_name": WORKFLOW_NAME,
        "workflow_version": WORKFLOW_VERSION,
        "intent": intent,
        "safety_status": safety_status,
        "file_route": "text_only",
        "reply_branch": reply_branch,
        "knowledge_matches": _knowledge_match_payload(knowledge_matches),
        "knowledge_gap_required": knowledge_gap_required,
        "handoff_required": handoff_required,
        "model_call": {
            "provider": model_result.provider,
            "model": model_result.model,
            "status": model_result.status,
            "prompt_summary": model_result.prompt_summary,
        }
        if model_result
        else None,
        "external_write_allowed_after_gate": state == "auto_reply_ready",
        "matched_terms": intent_hits,
    }
    return MvpWorkflowResult(
        intent=intent,
        safety_status=safety_status,
        reply_branch=reply_branch,
        state=state,
        reason=reason,
        confidence=round(confidence, 4),
        delivery_mode=delivery_mode,
        draft_reply=draft_reply.strip(),
        matched_terms=intent_hits,
        knowledge_matches=knowledge_matches,
        handoff_required=handoff_required,
        knowledge_gap_required=knowledge_gap_required,
        risk_level=risk_level,
        model_result=model_result,
        payload=payload,
    )
