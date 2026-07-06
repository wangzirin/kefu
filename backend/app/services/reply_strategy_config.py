from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from sqlalchemy.orm import Session

from app.models import TenantReplyStrategy


@dataclass(frozen=True)
class EffectiveReplyStrategy:
    strategy_id: str
    strategy_version: str
    auto_reply_threshold: float | None
    manual_review_threshold: float | None
    blocked_policy_terms: set[str]
    manual_review_terms: set[str]
    force_draft_only: bool
    model_routing: dict


def get_active_reply_strategy(db: Session, tenant_id: int) -> TenantReplyStrategy | None:
    strategy = (
        db.query(TenantReplyStrategy)
        .filter(TenantReplyStrategy.tenant_id == tenant_id, TenantReplyStrategy.status == "active")
        .one_or_none()
    )
    return strategy


def resolve_effective_reply_strategy(
    db: Session,
    *,
    tenant_id: int,
    default_blocked_terms: Iterable[str],
    default_manual_terms: Iterable[str],
) -> EffectiveReplyStrategy:
    strategy = get_active_reply_strategy(db, tenant_id)
    payload = strategy.strategy_payload if strategy is not None and isinstance(strategy.strategy_payload, dict) else {}
    reply_policy = payload.get("reply_policy") if isinstance(payload.get("reply_policy"), dict) else {}
    model_routing = payload.get("model_routing") if isinstance(payload.get("model_routing"), dict) else {}
    return EffectiveReplyStrategy(
        strategy_id=str(payload.get("strategy_id") or (strategy.strategy_id if strategy else "")),
        strategy_version=str(payload.get("strategy_version") or (strategy.strategy_version if strategy else "")),
        auto_reply_threshold=_optional_float(reply_policy.get("auto_reply_threshold")),
        manual_review_threshold=_optional_float(reply_policy.get("manual_review_threshold")),
        blocked_policy_terms=set(default_blocked_terms).union(_clean_terms(reply_policy.get("blocked_policy_terms"))),
        manual_review_terms=set(default_manual_terms).union(_clean_terms(reply_policy.get("manual_review_terms"))),
        force_draft_only=bool(reply_policy.get("force_draft_only") is True),
        model_routing=dict(model_routing),
    )


def _clean_terms(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    cleaned: list[str] = []
    seen: set[str] = set()
    for item in value:
        term = str(item).strip()
        if not term or term in seen:
            continue
        cleaned.append(term)
        seen.add(term)
    return cleaned


def _optional_float(value: object) -> float | None:
    if value is None:
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    if parsed < 0 or parsed > 1:
        return None
    return parsed
