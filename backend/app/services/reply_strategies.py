from __future__ import annotations

from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.audit import add_audit_event
from app.core.auth import CurrentPrincipal
from app.models import TenantReplyStrategy
from app.models.foundation import utc_now
from app.schemas.reply_strategies import TenantReplyStrategyRead, TenantReplyStrategyUpdate


DEFAULT_STRATEGY_ID = "customer-local-reply-policy"
DEFAULT_STRATEGY_VERSION = "local"


def _require_same_tenant(tenant_id: int, principal: CurrentPrincipal) -> None:
    if principal.tenant.id != tenant_id:
        raise HTTPException(status_code=404, detail="tenant not found")


def _clean_terms(values: list[str]) -> list[str]:
    cleaned: list[str] = []
    seen: set[str] = set()
    for value in values:
        term = str(value).strip()
        if not term or term in seen:
            continue
        cleaned.append(term)
        seen.add(term)
    return cleaned


def _read_payload(strategy: TenantReplyStrategy | None) -> dict:
    if strategy is None or not isinstance(strategy.strategy_payload, dict):
        return {}
    return dict(strategy.strategy_payload)


def _to_read_model(tenant_id: int, strategy: TenantReplyStrategy | None) -> TenantReplyStrategyRead:
    payload = _read_payload(strategy)
    reply_policy = payload.get("reply_policy") if isinstance(payload.get("reply_policy"), dict) else {}
    model_routing = payload.get("model_routing") if isinstance(payload.get("model_routing"), dict) else {}
    return TenantReplyStrategyRead(
        tenant_id=tenant_id,
        strategy_id=str(payload.get("strategy_id") or (strategy.strategy_id if strategy else "")),
        strategy_version=str(payload.get("strategy_version") or (strategy.strategy_version if strategy else "")),
        status=str(strategy.status if strategy else "inactive"),
        reply_policy={
            "auto_reply_threshold": reply_policy.get("auto_reply_threshold"),
            "manual_review_threshold": reply_policy.get("manual_review_threshold"),
            "blocked_policy_terms": _clean_terms(reply_policy.get("blocked_policy_terms") or []),
            "manual_review_terms": _clean_terms(reply_policy.get("manual_review_terms") or []),
            "force_draft_only": bool(reply_policy.get("force_draft_only") is True),
        },
        model_routing=dict(model_routing),
        updated_by_id=strategy.updated_by_id if strategy else None,
        updated_at=strategy.updated_at if strategy else None,
        created_at=strategy.created_at if strategy else None,
        source="tenant_reply_strategies" if strategy else "default_empty_policy",
        external_write_performed=False,
        model_call_performed=False,
    )


def get_tenant_reply_strategy(
    db: Session,
    tenant_id: int,
    principal: CurrentPrincipal,
) -> TenantReplyStrategyRead:
    _require_same_tenant(tenant_id, principal)
    strategy = db.query(TenantReplyStrategy).filter(TenantReplyStrategy.tenant_id == tenant_id).one_or_none()
    return _to_read_model(tenant_id, strategy)


def update_tenant_reply_strategy(
    db: Session,
    tenant_id: int,
    payload: TenantReplyStrategyUpdate,
    principal: CurrentPrincipal,
) -> TenantReplyStrategyRead:
    _require_same_tenant(tenant_id, principal)
    now = utc_now()
    strategy = db.query(TenantReplyStrategy).filter(TenantReplyStrategy.tenant_id == tenant_id).one_or_none()
    previous_payload = _read_payload(strategy)
    if strategy is None:
        strategy = TenantReplyStrategy(tenant_id=tenant_id, created_at=now)
        db.add(strategy)

    previous_reply_policy = (
        previous_payload.get("reply_policy") if isinstance(previous_payload.get("reply_policy"), dict) else {}
    )
    model_routing = previous_payload.get("model_routing") if isinstance(previous_payload.get("model_routing"), dict) else {}
    reply_policy = {
        "auto_reply_threshold": payload.auto_reply_threshold
        if payload.auto_reply_threshold is not None
        else previous_reply_policy.get("auto_reply_threshold"),
        "manual_review_threshold": payload.manual_review_threshold
        if payload.manual_review_threshold is not None
        else previous_reply_policy.get("manual_review_threshold"),
        "blocked_policy_terms": _clean_terms(payload.blocked_policy_terms),
        "manual_review_terms": _clean_terms(payload.manual_review_terms),
        "force_draft_only": payload.force_draft_only,
    }
    version = datetime.strftime(now, "%Y%m%d%H%M%S")
    strategy_payload = {
        "schema_version": "wanfa.customer_reply_strategy.v1",
        "strategy_id": previous_payload.get("strategy_id") or DEFAULT_STRATEGY_ID,
        "strategy_version": version,
        "reply_policy": reply_policy,
        "model_routing": model_routing,
        "updated_from": "customer_knowledge_center",
    }

    strategy.strategy_id = str(strategy_payload["strategy_id"])
    strategy.strategy_version = version
    strategy.status = "active"
    strategy.previous_strategy_payload = previous_payload
    strategy.strategy_payload = strategy_payload
    strategy.updated_by_id = principal.user.id
    strategy.updated_at = now
    add_audit_event(
        db,
        tenant_id=tenant_id,
        actor_id=principal.user.id,
        action="tenant_reply_strategy.updated_from_knowledge_center",
        resource_type="tenant_reply_strategy",
        resource_id=str(strategy.id or ""),
        payload={
            "blocked_policy_terms_count": len(reply_policy["blocked_policy_terms"]),
            "manual_review_terms_count": len(reply_policy["manual_review_terms"]),
            "external_write_performed": False,
            "model_call_performed": False,
        },
    )
    db.commit()
    db.refresh(strategy)
    return _to_read_model(tenant_id, strategy)
