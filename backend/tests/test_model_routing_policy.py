from app.core.config import get_settings
from app.services.model_gateway import select_model_route


def test_auto_route_selects_fast_bailian_model_for_simple_low_risk(monkeypatch) -> None:
    monkeypatch.setenv("BAILIAN_API_KEY", "test-bailian-key")
    monkeypatch.setenv("BAILIAN_FAST_MODEL", "qwen3.6-flash")

    route = select_model_route(
        user_message="你好，在吗？",
        intent="greeting",
        risk_level="low",
        confidence=0.92,
        knowledge_count=1,
        requested_provider="auto",
        requested_model="",
        settings=get_settings(),
    )

    assert route.provider == "bailian"
    assert route.model == "qwen3.6-flash"
    assert route.route_name == "simple_fast"
    assert route.complexity == "simple"
    assert route.human_review_required is False
    assert "bailian:qwen3.6-flash" in route.fallback_chain


def test_auto_route_selects_standard_bailian_model_for_normal_customer_question(monkeypatch) -> None:
    monkeypatch.setenv("BAILIAN_API_KEY", "test-bailian-key")
    monkeypatch.setenv("BAILIAN_STANDARD_MODEL", "qwen3.7-plus")

    route = select_model_route(
        user_message="客户问超过七天是否还能退货，需要怎么回复？",
        intent="after_sales_policy",
        risk_level="low",
        confidence=0.86,
        knowledge_count=2,
        requested_provider="auto",
        requested_model="",
        settings=get_settings(),
    )

    assert route.provider == "bailian"
    assert route.model == "qwen3.7-plus"
    assert route.route_name == "standard_support"
    assert route.complexity == "standard"
    assert route.human_review_required is False


def test_auto_route_selects_premium_guarded_model_for_high_risk_or_complex_question(monkeypatch) -> None:
    monkeypatch.setenv("BAILIAN_API_KEY", "test-bailian-key")
    monkeypatch.setenv("BAILIAN_PREMIUM_MODEL", "qwen3.7-max")

    route = select_model_route(
        user_message="客户投诉说要起诉并要求我们承诺赔偿，应该怎么处理？",
        intent="complaint_legal_refund_dispute",
        risk_level="high",
        confidence=0.81,
        knowledge_count=3,
        requested_provider="auto",
        requested_model="",
        settings=get_settings(),
    )

    assert route.provider == "bailian"
    assert route.model == "qwen3.7-max"
    assert route.route_name == "premium_guarded"
    assert route.complexity == "high_risk"
    assert route.human_review_required is True
    assert any("risk_level=high" in reason for reason in route.reasons)


def test_auto_route_falls_back_to_deterministic_without_external_keys(monkeypatch) -> None:
    monkeypatch.delenv("BAILIAN_API_KEY", raising=False)
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)

    route = select_model_route(
        user_message="这个问题需要综合多个政策判断。",
        intent="complex_policy_question",
        risk_level="medium",
        confidence=0.72,
        knowledge_count=2,
        requested_provider="auto",
        requested_model="",
        settings=get_settings(),
    )

    assert route.provider == "deterministic"
    assert route.model == "deterministic-local-draft-v1"
    assert route.route_name == "deterministic_safe_fallback"
    assert route.human_review_required is True
    assert "no_external_model_key_configured" in route.reasons
