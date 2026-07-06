from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.models import ModelCallRecord
from app.services.model_gateway import DETERMINISTIC_PROVIDER, ModelRouteDecision


@dataclass(frozen=True)
class ModelCostEstimate:
    provider: str
    model: str
    route_name: str
    target_model_tier: str
    complexity: str
    input_units: int
    output_units: int
    total_units: int
    unit_type: str
    estimated_cost: float
    currency: str
    pricing_source: str
    pricing_version: str


@dataclass(frozen=True)
class ModelBudgetDecision:
    allowed: bool
    status: str
    reason: str
    action: str
    spent_today: float
    spent_month: float
    estimate: ModelCostEstimate
    policy_snapshot: dict


def _start_of_day_utc() -> datetime:
    now = datetime.now(timezone.utc)
    return now.replace(hour=0, minute=0, second=0, microsecond=0)


def _start_of_month_utc() -> datetime:
    now = datetime.now(timezone.utc)
    return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def _spent_since(db: Session, tenant_id: int, start_at: datetime) -> float:
    value = db.scalar(
        select(func.coalesce(func.sum(ModelCallRecord.estimated_cost), 0.0)).where(
            ModelCallRecord.tenant_id == tenant_id,
            ModelCallRecord.created_at >= start_at,
        )
    )
    return float(value or 0.0)


def _unit_price_per_1k(route: ModelRouteDecision, settings: Settings) -> float:
    if route.provider == DETERMINISTIC_PROVIDER:
        return settings.model_price_deterministic_per_1k_units
    if route.provider == "deepseek":
        return settings.model_price_deepseek_per_1k_units
    if route.provider == "bailian":
        if route.target_model_tier == "fast":
            return settings.model_price_bailian_fast_per_1k_units
        if route.target_model_tier == "premium":
            return settings.model_price_bailian_premium_per_1k_units
        return settings.model_price_bailian_standard_per_1k_units
    return 0.0


def estimate_route_cost(
    route: ModelRouteDecision,
    *,
    input_units: int,
    output_units: int,
    settings: Settings | None = None,
) -> ModelCostEstimate:
    settings = settings or get_settings()
    total_units = max(0, input_units) + max(0, output_units)
    price_per_1k = _unit_price_per_1k(route, settings)
    estimated_cost = round((total_units / 1000.0) * price_per_1k, 6)
    pricing_source = settings.model_budget_pricing_source
    pricing_version = settings.model_budget_price_table_version
    if route.provider == DETERMINISTIC_PROVIDER:
        pricing_source = "deterministic_no_external_cost"
        pricing_version = "local-deterministic"
    return ModelCostEstimate(
        provider=route.provider,
        model=route.model,
        route_name=route.route_name,
        target_model_tier=route.target_model_tier,
        complexity=route.complexity,
        input_units=max(0, input_units),
        output_units=max(0, output_units),
        total_units=total_units,
        unit_type="estimated_chars_or_tokens",
        estimated_cost=estimated_cost,
        currency=settings.model_budget_cost_currency,
        pricing_source=pricing_source,
        pricing_version=pricing_version,
    )


def _policy_snapshot(settings: Settings, estimate: ModelCostEstimate, spent_today: float, spent_month: float) -> dict:
    return {
        "enabled": settings.model_budget_guard_enabled,
        "currency": settings.model_budget_cost_currency,
        "daily_limit": settings.model_budget_daily_limit_cny,
        "monthly_limit": settings.model_budget_monthly_limit_cny,
        "single_call_limit": settings.model_budget_single_call_limit_cny,
        "spent_today_before_call": round(spent_today, 6),
        "spent_month_before_call": round(spent_month, 6),
        "estimated_call_cost": estimate.estimated_cost,
        "pricing_source": estimate.pricing_source,
        "pricing_version": estimate.pricing_version,
        "price_estimate_not_provider_bill": True,
    }


def evaluate_budget(
    db: Session,
    *,
    tenant_id: int,
    estimate: ModelCostEstimate,
    settings: Settings | None = None,
) -> ModelBudgetDecision:
    settings = settings or get_settings()
    spent_today = _spent_since(db, tenant_id, _start_of_day_utc())
    spent_month = _spent_since(db, tenant_id, _start_of_month_utc())
    snapshot = _policy_snapshot(settings, estimate, spent_today, spent_month)
    if not settings.model_budget_guard_enabled:
        return ModelBudgetDecision(
            allowed=True,
            status="allowed",
            reason="budget_guard_disabled",
            action="allow",
            spent_today=spent_today,
            spent_month=spent_month,
            estimate=estimate,
            policy_snapshot=snapshot,
        )
    if settings.model_budget_single_call_limit_cny > 0 and estimate.estimated_cost > settings.model_budget_single_call_limit_cny:
        return ModelBudgetDecision(
            allowed=False,
            status="blocked",
            reason="single_call_budget_exceeded",
            action="budget_blocked",
            spent_today=spent_today,
            spent_month=spent_month,
            estimate=estimate,
            policy_snapshot=snapshot,
        )
    if settings.model_budget_daily_limit_cny > 0 and spent_today + estimate.estimated_cost > settings.model_budget_daily_limit_cny:
        return ModelBudgetDecision(
            allowed=False,
            status="blocked",
            reason="daily_budget_exceeded",
            action="budget_blocked",
            spent_today=spent_today,
            spent_month=spent_month,
            estimate=estimate,
            policy_snapshot=snapshot,
        )
    if settings.model_budget_monthly_limit_cny > 0 and spent_month + estimate.estimated_cost > settings.model_budget_monthly_limit_cny:
        return ModelBudgetDecision(
            allowed=False,
            status="blocked",
            reason="monthly_budget_exceeded",
            action="budget_blocked",
            spent_today=spent_today,
            spent_month=spent_month,
            estimate=estimate,
            policy_snapshot=snapshot,
        )
    return ModelBudgetDecision(
        allowed=True,
        status="allowed",
        reason="within_budget",
        action="allow",
        spent_today=spent_today,
        spent_month=spent_month,
        estimate=estimate,
        policy_snapshot=snapshot,
    )
