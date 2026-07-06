from __future__ import annotations

from pathlib import Path
import sys


RESEARCH_DIR = (
    Path(__file__).resolve().parents[2] / "research" / "ai_rpa_closed_loop"
)
sys.path.insert(0, str(RESEARCH_DIR))

from ai_rpa_closed_loop import build_default_engine, load_messages


def test_ai_rpa_research_loop_never_performs_external_write() -> None:
    engine = build_default_engine()
    messages = load_messages(RESEARCH_DIR / "sample_inbound_messages.json")

    results = [engine.handle(message) for message in messages]

    assert results
    assert len(results) >= 12
    assert all(not action.external_write for result in results for action in result.actions)
    assert all(not result.audit["external_write_performed"] for result in results)
    assert all(not result.audit["private_protocol_used"] for result in results)
    assert all(not result.audit["cookie_or_token_reuse_used"] for result in results)
    assert all(not result.audit["auto_send_enabled"] for result in results)


def test_ai_rpa_research_loop_routes_risky_refund_to_human() -> None:
    engine = build_default_engine()
    messages = load_messages(RESEARCH_DIR / "sample_inbound_messages.json")
    risky = next(message for message in messages if message.message_id == "demo-002")

    result = engine.handle(risky)

    assert result.guardrail.status == "needs_human"
    assert "risk_term" in result.guardrail.reasons
    assert any(action.kind == "mark_needs_human" for action in result.actions)
    assert not any(
        action.kind == "fill_reply_box" and not action.payload["requires_human_click_send"]
        for action in result.actions
    )
    assert result.reply_strategy.delivery_mode == "human_takeover"
    assert result.reply_strategy.next_best_action == "collect_evidence_and_handoff"


def test_ai_rpa_research_loop_records_gap_when_knowledge_missing() -> None:
    engine = build_default_engine()
    messages = load_messages(RESEARCH_DIR / "sample_inbound_messages.json")
    missing = next(message for message in messages if message.message_id == "demo-004")

    result = engine.handle(missing)

    assert result.draft.missing_knowledge is True
    assert result.guardrail.status == "needs_human"
    assert any(action.kind == "record_knowledge_gap" for action in result.actions)
    assert result.reply_strategy.delivery_mode == "record_gap"


def test_ai_rpa_research_loop_uses_strategy_for_standard_questions() -> None:
    engine = build_default_engine()
    messages = load_messages(RESEARCH_DIR / "sample_inbound_messages.json")
    shipping = next(message for message in messages if message.message_id == "demo-001")

    result = engine.handle(shipping)

    assert result.reply_strategy.intent == "shipping_status_or_policy"
    assert result.reply_strategy.answer_mode == "knowledge_draft_with_citation"
    assert result.reply_strategy.delivery_mode == "fill_draft_only"
    assert result.reply_strategy.next_best_action == "operator_review_and_send"
    assert any(action.kind == "fill_reply_box" for action in result.actions)
    assert result.audit["reply_delivery_mode"] == "fill_draft_only"


def test_ai_rpa_research_loop_routes_price_negotiation_to_human() -> None:
    engine = build_default_engine()
    messages = load_messages(RESEARCH_DIR / "sample_inbound_messages.json")
    price = next(message for message in messages if message.message_id == "demo-006")

    result = engine.handle(price)

    assert result.reply_strategy.intent == "policy_or_risk_review"
    assert result.reply_strategy.delivery_mode == "human_takeover"
    assert "knowledge_card_requires_human" in result.guardrail.reasons
    assert not any(action.kind == "fill_reply_box" for action in result.actions)
