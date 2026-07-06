from __future__ import annotations

from dataclasses import dataclass
import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.core.config import Settings, get_settings


MODEL_GATEWAY_VERSION = "model_gateway_v1"
DETERMINISTIC_PROVIDER = "deterministic"
DETERMINISTIC_MODEL = "deterministic-local-draft-v1"
OPENAI_COMPATIBLE_PROVIDERS = {"bailian", "deepseek"}
SIMPLE_INTENTS = {"greeting", "small_talk", "navigation", "business_hours", "simple_faq"}
SIMPLE_TERMS = {"你好", "您好", "在吗", "有人吗", "谢谢", "感谢", "早上好", "晚上好"}
HIGH_RISK_TERMS = {
    "起诉",
    "律师",
    "赔偿",
    "投诉",
    "监管",
    "违法",
    "合同",
    "发票纠纷",
    "退款纠纷",
    "承诺",
}
COMPLEX_TERMS = {
    "综合",
    "多个政策",
    "多份文档",
    "技术接入",
    "接口",
    "集成",
    "方案",
    "报价",
    "合同",
}


@dataclass(frozen=True)
class ModelDraftKnowledge:
    title: str
    answer: str
    source_uri: str
    matched_terms: list[str]


@dataclass(frozen=True)
class ModelDraftRequest:
    user_message: str
    intent: str
    knowledge: list[ModelDraftKnowledge]
    provider: str = DETERMINISTIC_PROVIDER
    model: str = ""
    temperature: float = 0.2
    confidence: float = 1.0
    risk_level: str = "low"


@dataclass(frozen=True)
class ModelRouteDecision:
    provider: str
    model: str
    route_name: str
    complexity: str
    target_model_tier: str
    fallback_chain: list[str]
    human_review_required: bool
    reasons: list[str]


@dataclass(frozen=True)
class ModelDraftResult:
    provider: str
    model: str
    status: str
    draft_text: str
    prompt_summary: str
    prompt_chars: int
    completion_chars: int
    total_chars: int
    error_message: str = ""
    route_name: str = "explicit_provider"
    complexity: str = "standard"
    target_model_tier: str = "standard"
    fallback_chain: list[str] | None = None
    human_review_required: bool = False
    route_reasons: list[str] | None = None
    estimated_cost: float = 0.0
    cost_currency: str = "CNY"
    pricing_source: str = ""
    pricing_version: str = ""
    budget_status: str = "not_evaluated"
    budget_reason: str = ""
    budget_action: str = ""
    budget_policy_snapshot: dict | None = None


def _prompt_summary(intent: str, knowledge_count: int) -> str:
    return f"intent={intent}, knowledge_matches={knowledge_count}"


def _contains_any(value: str, terms: set[str]) -> bool:
    return any(term in value for term in terms)


def _complexity_for_request(
    *,
    user_message: str,
    intent: str,
    risk_level: str,
    confidence: float,
) -> tuple[str, list[str]]:
    text = f"{intent} {user_message}".lower()
    reasons: list[str] = []
    if risk_level in {"high", "critical"} or _contains_any(text, HIGH_RISK_TERMS):
        reasons.append(f"risk_level={risk_level}")
        return "high_risk", reasons
    if risk_level == "medium":
        reasons.append("risk_level=medium")
        return "complex", reasons
    if confidence < 0.75:
        reasons.append(f"low_confidence={confidence:.2f}")
        return "complex", reasons
    if _contains_any(text, COMPLEX_TERMS) or "complex" in intent or "dispute" in intent:
        reasons.append("complex_intent_or_terms")
        return "complex", reasons
    if intent in SIMPLE_INTENTS or _contains_any(text, SIMPLE_TERMS):
        reasons.append("simple_intent_or_short_message")
        return "simple", reasons
    reasons.append("standard_customer_question")
    return "standard", reasons


def _tier_for_complexity(complexity: str) -> str:
    if complexity == "simple":
        return "fast"
    if complexity in {"complex", "high_risk"}:
        return "premium"
    return "standard"


def _bailian_model_for_tier(settings: Settings, tier: str) -> str:
    if tier == "fast":
        return settings.bailian_fast_model
    if tier == "premium":
        return settings.bailian_premium_model
    return settings.bailian_standard_model


def _fallback_chain(settings: Settings, tier: str) -> list[str]:
    return [
        f"bailian:{_bailian_model_for_tier(settings, tier)}",
        f"deepseek:{settings.deepseek_fallback_model or settings.deepseek_model}",
        f"{DETERMINISTIC_PROVIDER}:{DETERMINISTIC_MODEL}",
    ]


def _explicit_provider_model(provider: str, requested_model: str, settings: Settings) -> str:
    if requested_model:
        return requested_model
    if provider == DETERMINISTIC_PROVIDER:
        return DETERMINISTIC_MODEL
    if provider == "bailian":
        return settings.bailian_model
    if provider == "deepseek":
        return settings.deepseek_model
    return requested_model


def select_model_route(
    *,
    user_message: str,
    intent: str,
    risk_level: str,
    confidence: float,
    knowledge_count: int,
    requested_provider: str,
    requested_model: str,
    settings: Settings | None = None,
) -> ModelRouteDecision:
    settings = settings or get_settings()
    complexity, reasons = _complexity_for_request(
        user_message=user_message,
        intent=intent,
        risk_level=risk_level,
        confidence=confidence,
    )
    human_review_required = (
        knowledge_count == 0
        or confidence < 0.75
        or risk_level in {"medium", "high", "critical"}
        or complexity == "high_risk"
    )
    tier = _tier_for_complexity(complexity)
    if requested_provider != "auto":
        provider = requested_provider
        model = _explicit_provider_model(provider, requested_model, settings)
        return ModelRouteDecision(
            provider=provider,
            model=model,
            route_name="explicit_provider",
            complexity=complexity,
            target_model_tier=tier if provider != DETERMINISTIC_PROVIDER else "standard",
            fallback_chain=_fallback_chain(settings, tier),
            human_review_required=human_review_required,
            reasons=reasons + [f"explicit_provider={provider}"],
        )

    if settings.bailian_api_key:
        model = requested_model or _bailian_model_for_tier(settings, tier)
        route_name = {
            "fast": "simple_fast",
            "standard": "standard_support",
            "premium": "premium_guarded" if human_review_required else "complex_premium",
        }[tier]
        return ModelRouteDecision(
            provider="bailian",
            model=model,
            route_name=route_name,
            complexity=complexity,
            target_model_tier=tier,
            fallback_chain=_fallback_chain(settings, tier),
            human_review_required=human_review_required,
            reasons=reasons + ["primary_provider=bailian"],
        )

    if settings.deepseek_api_key:
        model = requested_model or settings.deepseek_fallback_model or settings.deepseek_model
        return ModelRouteDecision(
            provider="deepseek",
            model=model,
            route_name="deepseek_cost_fallback",
            complexity=complexity,
            target_model_tier=tier,
            fallback_chain=_fallback_chain(settings, tier),
            human_review_required=human_review_required,
            reasons=reasons + ["primary_provider_missing=bailian", "fallback_provider=deepseek"],
        )

    return ModelRouteDecision(
        provider=DETERMINISTIC_PROVIDER,
        model=DETERMINISTIC_MODEL,
        route_name="deterministic_safe_fallback",
        complexity=complexity,
        target_model_tier=tier,
        fallback_chain=_fallback_chain(settings, tier),
        human_review_required=human_review_required,
        reasons=reasons + ["no_external_model_key_configured"],
    )


def _build_prompt(request: ModelDraftRequest) -> tuple[str, str]:
    knowledge_lines = []
    for index, item in enumerate(request.knowledge, start=1):
        matched = "、".join(item.matched_terms[:8])
        source = f"，来源：{item.source_uri}" if item.source_uri else ""
        knowledge_lines.append(
            f"{index}. {item.title}{source}\n"
            f"   命中词：{matched or '无'}\n"
            f"   标准答案：{item.answer}"
        )
    system_prompt = (
        "你是企业客服助手。只能依据已审核知识回答；不要编造政策、价格、承诺或渠道信息。"
        "如果知识不足，输出需要人工确认的谨慎回复。语气要自然、简洁、可直接给客户。"
    )
    user_prompt = (
        f"客户问题：{request.user_message}\n"
        f"意图：{request.intent}\n"
        "已审核知识：\n"
        + "\n".join(knowledge_lines)
        + "\n请生成一条客服回复草稿。"
    )
    return system_prompt, user_prompt


def _route_kwargs(route: ModelRouteDecision) -> dict:
    return {
        "route_name": route.route_name,
        "complexity": route.complexity,
        "target_model_tier": route.target_model_tier,
        "fallback_chain": route.fallback_chain,
        "human_review_required": route.human_review_required,
        "route_reasons": route.reasons,
    }


def _deterministic_draft(request: ModelDraftRequest, route: ModelRouteDecision) -> ModelDraftResult:
    prompt_summary = _prompt_summary(request.intent, len(request.knowledge))
    system_prompt, user_prompt = _build_prompt(request)
    if not request.knowledge:
        draft = "暂时没有找到可引用的知识，请人工确认后回复。"
    else:
        top_answer = request.knowledge[0].answer
        draft = f"根据已审核知识，{top_answer}\n\n针对您的问题，我们建议先按以上规则核对订单和商品状态。"
    return ModelDraftResult(
        provider=DETERMINISTIC_PROVIDER,
        model=DETERMINISTIC_MODEL,
        status="succeeded",
        draft_text=draft,
        prompt_summary=prompt_summary,
        prompt_chars=len(system_prompt) + len(user_prompt),
        completion_chars=len(draft),
        total_chars=len(system_prompt) + len(user_prompt) + len(draft),
        **_route_kwargs(route),
    )


def _provider_credentials(provider: str, settings: Settings) -> tuple[str, str, str]:
    if provider == "bailian":
        return settings.bailian_api_base, settings.bailian_api_key, settings.bailian_model
    if provider == "deepseek":
        return settings.deepseek_api_base, settings.deepseek_api_key, settings.deepseek_model
    raise ValueError(f"unsupported provider: {provider}")


def _resolve_provider(provider: str, settings: Settings) -> str:
    if provider != "auto":
        return provider
    if settings.bailian_api_key:
        return "bailian"
    if settings.deepseek_api_key:
        return "deepseek"
    return DETERMINISTIC_PROVIDER


def _openai_compatible_draft(
    request: ModelDraftRequest,
    settings: Settings,
    route: ModelRouteDecision,
) -> ModelDraftResult:
    provider = request.provider
    base_url, api_key, default_model = _provider_credentials(provider, settings)
    model = request.model or default_model
    prompt_summary = _prompt_summary(request.intent, len(request.knowledge))
    system_prompt, user_prompt = _build_prompt(request)
    if not api_key:
        return ModelDraftResult(
            provider=provider,
            model=model,
            status="unavailable",
            draft_text="模型服务暂不可用，请人工根据已命中知识确认后回复。",
            prompt_summary=prompt_summary,
            prompt_chars=len(system_prompt) + len(user_prompt),
            completion_chars=0,
            total_chars=len(system_prompt) + len(user_prompt),
            error_message=f"{provider} API key is not configured",
            **_route_kwargs(route),
        )

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": request.temperature,
    }
    endpoint = base_url.rstrip("/") + "/chat/completions"
    http_request = Request(
        endpoint,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urlopen(http_request, timeout=settings.model_http_timeout_seconds) as response:
            raw_body = response.read().decode("utf-8")
        data = json.loads(raw_body)
        choices = data.get("choices")
        if not isinstance(choices, list) or not choices:
            raise ValueError("missing choices in model response")
        message = choices[0].get("message")
        if not isinstance(message, dict) or not isinstance(message.get("content"), str):
            raise ValueError("missing message content in model response")
        draft = message["content"].strip()
        usage = data.get("usage") if isinstance(data.get("usage"), dict) else {}
        prompt_tokens = int(usage.get("prompt_tokens") or 0)
        completion_tokens = int(usage.get("completion_tokens") or 0)
        total_tokens = int(usage.get("total_tokens") or (prompt_tokens + completion_tokens))
        return ModelDraftResult(
            provider=provider,
            model=model,
            status="succeeded",
            draft_text=draft,
            prompt_summary=prompt_summary,
            prompt_chars=prompt_tokens,
            completion_chars=completion_tokens or len(draft),
            total_chars=total_tokens or prompt_tokens + completion_tokens,
            **_route_kwargs(route),
        )
    except HTTPError as exc:
        return _model_failure_result(request, model, prompt_summary, system_prompt, user_prompt, f"HTTP {exc.code}", route)
    except (URLError, TimeoutError, ValueError, json.JSONDecodeError) as exc:
        return _model_failure_result(request, model, prompt_summary, system_prompt, user_prompt, str(exc), route)


def _model_failure_result(
    request: ModelDraftRequest,
    model: str,
    prompt_summary: str,
    system_prompt: str,
    user_prompt: str,
    error_message: str,
    route: ModelRouteDecision,
) -> ModelDraftResult:
    return ModelDraftResult(
        provider=request.provider,
        model=model,
        status="failed",
        draft_text="模型服务调用失败，请人工根据已命中知识确认后回复。",
        prompt_summary=prompt_summary,
        prompt_chars=len(system_prompt) + len(user_prompt),
        completion_chars=0,
        total_chars=len(system_prompt) + len(user_prompt),
        error_message=error_message[:500],
        **_route_kwargs(route),
    )


def generate_reply_draft(request: ModelDraftRequest, settings: Settings | None = None) -> ModelDraftResult:
    settings = settings or get_settings()
    route = select_model_route(
        user_message=request.user_message,
        intent=request.intent,
        risk_level=request.risk_level,
        confidence=request.confidence,
        knowledge_count=len(request.knowledge),
        requested_provider=request.provider,
        requested_model=request.model,
        settings=settings,
    )
    provider = route.provider
    resolved_request = ModelDraftRequest(
        user_message=request.user_message,
        intent=request.intent,
        knowledge=request.knowledge,
        provider=provider,
        model=route.model,
        temperature=request.temperature,
        confidence=request.confidence,
        risk_level=request.risk_level,
    )
    if provider == DETERMINISTIC_PROVIDER:
        return _deterministic_draft(resolved_request, route)
    if provider in OPENAI_COMPATIBLE_PROVIDERS:
        return _openai_compatible_draft(resolved_request, settings, route)
    return ModelDraftResult(
        provider=provider,
        model=route.model,
        status="unavailable",
        draft_text="模型服务暂不可用，请人工根据已命中知识确认后回复。",
        prompt_summary=_prompt_summary(request.intent, len(request.knowledge)),
        prompt_chars=0,
        completion_chars=0,
        total_chars=0,
        error_message=f"unsupported model provider: {provider}",
        **_route_kwargs(route),
    )
