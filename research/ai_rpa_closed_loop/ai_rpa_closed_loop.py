from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Iterable, Literal


ActionKind = Literal[
    "observe_message",
    "fill_reply_box",
    "mark_needs_human",
    "record_knowledge_gap",
    "capture_evidence",
]


@dataclass(frozen=True)
class ChannelMessage:
    message_id: str
    channel: str
    customer_name: str
    text: str
    received_at: str
    attachments: list[str] = field(default_factory=list)
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class KnowledgeCard:
    card_id: str
    title: str
    keywords: list[str]
    answer: str
    source: str
    risk_tags: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class KnowledgeHit:
    card_id: str
    title: str
    score: float
    answer: str
    source: str
    risk_tags: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class DraftReply:
    text: str
    route: str
    confidence: float
    citations: list[str]
    missing_knowledge: bool = False


@dataclass(frozen=True)
class GuardrailDecision:
    status: Literal["draft_only", "needs_human", "blocked"]
    reasons: list[str]
    allow_auto_send: bool


@dataclass(frozen=True)
class ReplyStrategyDecision:
    intent: str
    answer_mode: Literal[
        "knowledge_draft_with_citation",
        "human_handoff_draft",
        "knowledge_gap_handoff",
    ]
    delivery_mode: Literal["fill_draft_only", "human_takeover", "record_gap"]
    customer_visible_policy: str
    next_best_action: str
    quality_signals: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class RpaAction:
    kind: ActionKind
    target: str
    payload: dict[str, object]
    external_write: bool = False


@dataclass(frozen=True)
class ClosedLoopResult:
    message: ChannelMessage
    hits: list[KnowledgeHit]
    draft: DraftReply
    guardrail: GuardrailDecision
    reply_strategy: ReplyStrategyDecision
    actions: list[RpaAction]
    audit: dict[str, object]


class ResearchKnowledgeBase:
    def __init__(self, cards: Iterable[KnowledgeCard]) -> None:
        self._cards = list(cards)

    def search(self, text: str, limit: int = 3) -> list[KnowledgeHit]:
        normalized = text.lower()
        hits: list[KnowledgeHit] = []
        for card in self._cards:
            matched = [kw for kw in card.keywords if kw.lower() in normalized]
            if not matched:
                continue
            score = min(1.0, 0.35 + 0.2 * len(matched))
            hits.append(
                KnowledgeHit(
                    card_id=card.card_id,
                    title=card.title,
                    score=round(score, 2),
                    answer=card.answer,
                    source=card.source,
                    risk_tags=list(card.risk_tags),
                )
            )
        hits.sort(key=lambda hit: hit.score, reverse=True)
        return hits[:limit]


class DeterministicDraftGenerator:
    def draft(self, message: ChannelMessage, hits: list[KnowledgeHit]) -> DraftReply:
        if not hits:
            return DraftReply(
                text=(
                    "您好，这个问题我需要进一步核对资料后再回复。"
                    "我已经为您记录并转给人工客服确认。"
                ),
                route="knowledge_gap",
                confidence=0.32,
                citations=[],
                missing_knowledge=True,
            )

        top = hits[0]
        confidence = min(0.92, top.score + 0.12)
        text = f"您好，关于{top.title}：{top.answer}"
        return DraftReply(
            text=text,
            route="knowledge_first_draft",
            confidence=round(confidence, 2),
            citations=[top.source],
            missing_knowledge=False,
        )


class ResearchGuardrail:
    def __init__(self, low_confidence_threshold: float = 0.68) -> None:
        self.low_confidence_threshold = low_confidence_threshold
        self.risk_terms = [
            "投诉",
            "差评",
            "赔偿",
            "起诉",
            "监管",
            "假货",
            "退款纠纷",
            "平台介入",
            "工商",
            "律师",
            "法院",
            "人身",
        ]

    def evaluate(
        self, message: ChannelMessage, draft: DraftReply, hits: list[KnowledgeHit]
    ) -> GuardrailDecision:
        reasons: list[str] = []
        text = message.text
        if draft.confidence < self.low_confidence_threshold:
            reasons.append("low_confidence")
        if draft.missing_knowledge:
            reasons.append("missing_knowledge")
        if any(term in text for term in self.risk_terms):
            reasons.append("risk_term")
        if any("human_required" in hit.risk_tags for hit in hits):
            reasons.append("knowledge_card_requires_human")

        if reasons:
            return GuardrailDecision(
                status="needs_human",
                reasons=reasons,
                allow_auto_send=False,
            )

        return GuardrailDecision(status="draft_only", reasons=[], allow_auto_send=False)


class ReplyStrategyPlanner:
    def plan(
        self,
        message: ChannelMessage,
        draft: DraftReply,
        guardrail: GuardrailDecision,
        hits: list[KnowledgeHit],
    ) -> ReplyStrategyDecision:
        text = message.text
        quality_signals: list[str] = []
        if hits:
            quality_signals.append("has_knowledge_citation")
            quality_signals.append(f"top_score={hits[0].score:.2f}")
        else:
            quality_signals.append("no_knowledge_hit")
        if message.attachments:
            quality_signals.append("has_attachment")
        if guardrail.reasons:
            quality_signals.extend(f"guardrail:{reason}" for reason in guardrail.reasons)

        if draft.missing_knowledge:
            return ReplyStrategyDecision(
                intent="knowledge_gap_or_uncovered_question",
                answer_mode="knowledge_gap_handoff",
                delivery_mode="record_gap",
                customer_visible_policy=(
                    "不编造答案；先承认需要核对，再记录知识缺口并交给人工确认。"
                ),
                next_best_action="record_knowledge_gap_and_handoff",
                quality_signals=quality_signals,
            )

        if guardrail.status == "needs_human":
            if any(term in text for term in ["退款", "投诉", "平台介入", "质量问题"]):
                intent = "after_sales_risk"
                next_best_action = "collect_evidence_and_handoff"
            else:
                intent = "policy_or_risk_review"
                next_best_action = "handoff_with_draft_and_context"
            return ReplyStrategyDecision(
                intent=intent,
                answer_mode="human_handoff_draft",
                delivery_mode="human_takeover",
                customer_visible_policy=(
                    "可生成安抚和资料收集草稿，但不自动发送，由人工确认责任和口径。"
                ),
                next_best_action=next_best_action,
                quality_signals=quality_signals,
            )

        intent = "standard_service_question"
        if hits:
            card_id = hits[0].card_id
            if "shipping" in card_id:
                intent = "shipping_status_or_policy"
            elif "invoice" in card_id:
                intent = "invoice_request"
            elif "warranty" in card_id:
                intent = "warranty_or_aftercare"
            elif "price" in card_id:
                intent = "price_or_promotion"

        return ReplyStrategyDecision(
            intent=intent,
            answer_mode="knowledge_draft_with_citation",
            delivery_mode="fill_draft_only",
            customer_visible_policy=(
                "只依据命中的知识卡生成草稿并填入回复框；正式发送仍由人工点击。"
            ),
            next_best_action="operator_review_and_send",
            quality_signals=quality_signals,
        )


class DryRunRpaAdapter:
    def plan_actions(
        self,
        message: ChannelMessage,
        draft: DraftReply,
        guardrail: GuardrailDecision,
        reply_strategy: ReplyStrategyDecision,
    ) -> list[RpaAction]:
        actions = [
            RpaAction(
                kind="observe_message",
                target=f"{message.channel}:{message.message_id}",
                payload={
                    "customer": message.customer_name,
                    "intent": reply_strategy.intent,
                },
                external_write=False,
            ),
            RpaAction(
                kind="capture_evidence",
                target=f"{message.channel}:{message.message_id}",
                payload={
                    "evidence_type": "message_snapshot",
                    "strategy": reply_strategy.delivery_mode,
                },
                external_write=False,
            ),
        ]

        if draft.missing_knowledge:
            actions.append(
                RpaAction(
                    kind="record_knowledge_gap",
                    target=f"{message.channel}:{message.message_id}",
                    payload={
                        "question": message.text[:80],
                        "next_best_action": reply_strategy.next_best_action,
                    },
                    external_write=False,
                )
            )

        if guardrail.status == "needs_human":
            actions.append(
                RpaAction(
                    kind="mark_needs_human",
                    target=f"{message.channel}:{message.message_id}",
                    payload={
                        "reasons": guardrail.reasons,
                        "draft": draft.text,
                        "next_best_action": reply_strategy.next_best_action,
                    },
                    external_write=False,
                )
            )
            return actions

        actions.append(
            RpaAction(
                kind="fill_reply_box",
                target=f"{message.channel}:{message.message_id}",
                payload={
                    "draft": draft.text,
                    "requires_human_click_send": True,
                    "strategy": reply_strategy.delivery_mode,
                    "citations": draft.citations,
                },
                external_write=False,
            )
        )
        return actions


class ResearchClosedLoopEngine:
    def __init__(
        self,
        knowledge_base: ResearchKnowledgeBase,
        draft_generator: DeterministicDraftGenerator,
        guardrail: ResearchGuardrail,
        reply_strategy_planner: ReplyStrategyPlanner,
        rpa_adapter: DryRunRpaAdapter,
    ) -> None:
        self.knowledge_base = knowledge_base
        self.draft_generator = draft_generator
        self.guardrail = guardrail
        self.reply_strategy_planner = reply_strategy_planner
        self.rpa_adapter = rpa_adapter

    def handle(self, message: ChannelMessage) -> ClosedLoopResult:
        hits = self.knowledge_base.search(message.text)
        draft = self.draft_generator.draft(message, hits)
        decision = self.guardrail.evaluate(message, draft, hits)
        reply_strategy = self.reply_strategy_planner.plan(
            message=message,
            draft=draft,
            guardrail=decision,
            hits=hits,
        )
        actions = self.rpa_adapter.plan_actions(
            message=message,
            draft=draft,
            guardrail=decision,
            reply_strategy=reply_strategy,
        )
        audit = {
            "evaluated_at": datetime.now(timezone.utc).isoformat(),
            "mode": "research_dry_run",
            "external_write_performed": any(action.external_write for action in actions),
            "private_protocol_used": False,
            "cookie_or_token_reuse_used": False,
            "auto_send_enabled": False,
            "reply_delivery_mode": reply_strategy.delivery_mode,
            "reply_next_best_action": reply_strategy.next_best_action,
        }
        return ClosedLoopResult(
            message,
            hits,
            draft,
            decision,
            reply_strategy,
            actions,
            audit,
        )


def default_cards() -> list[KnowledgeCard]:
    return [
        KnowledgeCard(
            card_id="shipping_policy",
            title="发货时效",
            keywords=["发货", "多久", "什么时候发", "物流"],
            answer="常规现货订单会在付款后48小时内发出，节假日或预售商品以页面说明为准。",
            source="demo:shipping_policy_v1",
        ),
        KnowledgeCard(
            card_id="refund_policy",
            title="退款售后",
            keywords=["退款", "退货", "售后", "质量问题"],
            answer="如商品未使用且不影响二次销售，可按平台规则申请退换；质量问题请先提供照片或视频。",
            source="demo:refund_policy_v1",
            risk_tags=["human_required"],
        ),
        KnowledgeCard(
            card_id="invoice_policy",
            title="开票信息",
            keywords=["发票", "开票", "抬头", "税号"],
            answer="支持电子发票。请提供发票抬头、税号和接收邮箱，财务会在核对后处理。",
            source="demo:invoice_policy_v1",
        ),
        KnowledgeCard(
            card_id="warranty_policy",
            title="质保说明",
            keywords=["保修", "质保", "售后多久", "坏了怎么办"],
            answer="常规商品按页面和订单约定提供售后保障；具体质保范围以商品说明和平台规则为准。",
            source="demo:warranty_policy_v1",
        ),
        KnowledgeCard(
            card_id="price_policy",
            title="价格优惠",
            keywords=["优惠", "便宜", "最低价", "活动价"],
            answer="可先告知当前页面展示价格和活动信息；涉及额外优惠、最低价承诺或大额订单需人工确认。",
            source="demo:price_policy_v1",
            risk_tags=["human_required"],
        ),
    ]


def load_messages(path: Path) -> list[ChannelMessage]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return [ChannelMessage(**item) for item in data["messages"]]


def result_to_dict(result: ClosedLoopResult) -> dict[str, object]:
    return asdict(result)


def build_default_engine() -> ResearchClosedLoopEngine:
    return ResearchClosedLoopEngine(
        knowledge_base=ResearchKnowledgeBase(default_cards()),
        draft_generator=DeterministicDraftGenerator(),
        guardrail=ResearchGuardrail(),
        reply_strategy_planner=ReplyStrategyPlanner(),
        rpa_adapter=DryRunRpaAdapter(),
    )
