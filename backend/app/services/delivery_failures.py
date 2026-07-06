from dataclasses import dataclass

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.audit import add_audit_event
from app.core.auth import CurrentPrincipal
from app.models import ChannelDeliveryReceipt, DeliveryFailureReview, OutboxSendAttempt
from app.models.foundation import utc_now
from app.schemas.delivery_failures import DeliveryFailureReviewUpdate


SUCCESS_STATUSES = {
    "delivered",
    "delivery_success",
    "send_success",
    "sent",
    "success",
    "ok",
    "read",
}
INBOUND_NON_FAILURE_STATUSES = {
    "received",
    "webhook_received",
    "message_received",
    "accepted",
}
FAILED_STATUSES = {
    "failed",
    "send_failed",
    "delivery_failed",
    "rejected",
    "undeliverable",
}
RATE_LIMIT_CODES = {"45009", "rate_limited", "too_many_requests", "system_busy", "throttled"}
AUTH_FAILURE_CODES = {"40014", "42001", "invalid_access_token", "access_token_expired", "unauthorized"}
PERMISSION_CODES = {
    "48002",
    "permission_denied",
    "scope_missing",
    "not_authorized",
    "external_write_kill_switch",
    "connector_external_write_disabled",
    "external_sender_not_implemented",
}
RECIPIENT_UNREACHABLE_CODES = {"43004", "customer_not_found", "user_not_found", "not_followed", "recipient_unreachable"}
CONTENT_REJECTED_CODES = {"87014", "content_violation", "sensitive_word", "message_rejected", "spam_risk"}


@dataclass(frozen=True)
class DeliveryNormalization:
    provider_status: str
    provider_error_code: str
    normalized_status: str
    severity: str
    retryable: bool
    needs_review: bool
    review_reason: str
    next_action: str


def _as_string(value) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _unwrap_payload(raw_payload: dict) -> dict:
    if isinstance(raw_payload.get("payload"), dict):
        return raw_payload["payload"]
    return raw_payload


def _first_value(raw_payload: dict, keys: tuple[str, ...]) -> str:
    for key in keys:
        value = raw_payload.get(key)
        if value not in (None, ""):
            return _as_string(value)
    nested_error = raw_payload.get("error")
    if isinstance(nested_error, dict):
        for key in keys:
            value = nested_error.get(key)
            if value not in (None, ""):
                return _as_string(value)
    return ""


def _normalize_status_text(value: str) -> str:
    return value.strip().lower().replace(" ", "_").replace("-", "_")


def normalize_delivery_status(*, provider: str, delivery_status: str, raw_payload: dict) -> DeliveryNormalization:
    payload = _unwrap_payload(raw_payload or {})
    provider_status = _normalize_status_text(
        delivery_status
        or _first_value(payload, ("Status", "status", "delivery_status", "event_status", "DeliveryStatus"))
        or "unknown"
    )
    provider_error_code = _normalize_status_text(
        _first_value(payload, ("errcode", "ErrCode", "error_code", "errorCode", "code", "Code"))
    )
    _ = provider

    if provider_error_code in RATE_LIMIT_CODES or provider_status in RATE_LIMIT_CODES:
        return DeliveryNormalization(
            provider_status=provider_status,
            provider_error_code=provider_error_code,
            normalized_status="rate_limited",
            severity="warning",
            retryable=True,
            needs_review=True,
            review_reason="provider_rate_limited",
            next_action="retry_later",
        )
    if provider_error_code in AUTH_FAILURE_CODES or provider_status in AUTH_FAILURE_CODES:
        return DeliveryNormalization(
            provider_status=provider_status,
            provider_error_code=provider_error_code,
            normalized_status="auth_failed",
            severity="critical",
            retryable=False,
            needs_review=True,
            review_reason="provider_auth_failed",
            next_action="refresh_authorization_or_reconfigure_secret",
        )
    if provider_error_code in PERMISSION_CODES or provider_status in PERMISSION_CODES:
        return DeliveryNormalization(
            provider_status=provider_status,
            provider_error_code=provider_error_code,
            normalized_status="permission_denied",
            severity="critical",
            retryable=False,
            needs_review=True,
            review_reason="provider_permission_denied",
            next_action="check_provider_scope_or_service_market_permission",
        )
    if provider_error_code in RECIPIENT_UNREACHABLE_CODES or provider_status in RECIPIENT_UNREACHABLE_CODES:
        return DeliveryNormalization(
            provider_status=provider_status,
            provider_error_code=provider_error_code,
            normalized_status="recipient_unreachable",
            severity="warning",
            retryable=False,
            needs_review=True,
            review_reason="recipient_unreachable",
            next_action="manual_contact_check",
        )
    if provider_error_code in CONTENT_REJECTED_CODES or provider_status in CONTENT_REJECTED_CODES:
        return DeliveryNormalization(
            provider_status=provider_status,
            provider_error_code=provider_error_code,
            normalized_status="content_rejected",
            severity="warning",
            retryable=False,
            needs_review=True,
            review_reason="provider_content_rejected",
            next_action="manual_rewrite",
        )
    if provider_status in SUCCESS_STATUSES and provider_error_code in {"", "0", "ok"}:
        return DeliveryNormalization(
            provider_status=provider_status,
            provider_error_code=provider_error_code,
            normalized_status="delivered" if provider_status != "read" else "read",
            severity="info",
            retryable=False,
            needs_review=False,
            review_reason="none",
            next_action="none",
        )
    if provider_status in INBOUND_NON_FAILURE_STATUSES and provider_error_code in {"", "0", "ok"}:
        return DeliveryNormalization(
            provider_status=provider_status,
            provider_error_code=provider_error_code,
            normalized_status="received",
            severity="info",
            retryable=False,
            needs_review=False,
            review_reason="none",
            next_action="none",
        )
    if provider_status in FAILED_STATUSES:
        return DeliveryNormalization(
            provider_status=provider_status,
            provider_error_code=provider_error_code,
            normalized_status="failed",
            severity="warning",
            retryable=True,
            needs_review=True,
            review_reason="provider_failed_without_known_code",
            next_action="manual_review_before_retry",
        )
    return DeliveryNormalization(
        provider_status=provider_status,
        provider_error_code=provider_error_code,
        normalized_status="unknown_provider_status",
        severity="warning",
        retryable=False,
        needs_review=True,
        review_reason="unknown_provider_status",
        next_action="manual_review_provider_status",
    )


def attach_delivery_normalization_and_review(
    db: Session,
    *,
    receipt: ChannelDeliveryReceipt,
    actor_id: int | None,
) -> DeliveryFailureReview | None:
    normalization = normalize_delivery_status(
        provider=receipt.provider,
        delivery_status=receipt.delivery_status,
        raw_payload=receipt.raw_payload,
    )
    receipt.provider_status = normalization.provider_status
    receipt.provider_error_code = normalization.provider_error_code
    receipt.normalized_status = normalization.normalized_status
    receipt.retryable = normalization.retryable
    receipt.needs_review = normalization.needs_review
    receipt.next_action = normalization.next_action

    if not normalization.needs_review:
        return None
    existing = db.scalar(
        select(DeliveryFailureReview).where(DeliveryFailureReview.receipt_id == receipt.id)
    )
    if existing is not None:
        return existing
    attempt = db.get(OutboxSendAttempt, receipt.matched_attempt_id) if receipt.matched_attempt_id else None
    now = utc_now()
    review = DeliveryFailureReview(
        tenant_id=receipt.tenant_id,
        channel_id=receipt.channel_id,
        connector_id=receipt.connector_id,
        receipt_id=receipt.id,
        matched_attempt_id=receipt.matched_attempt_id,
        outbox_draft_id=attempt.outbox_draft_id if attempt else None,
        provider=receipt.provider,
        external_message_id=receipt.external_message_id,
        provider_status=normalization.provider_status,
        provider_error_code=normalization.provider_error_code,
        normalized_status=normalization.normalized_status,
        severity=normalization.severity,
        retryable=normalization.retryable,
        review_reason=normalization.review_reason,
        next_action=normalization.next_action,
        status="open",
        created_at=now,
        updated_at=now,
    )
    db.add(review)
    db.flush()
    add_audit_event(
        db,
        tenant_id=review.tenant_id,
        actor_id=actor_id,
        action="delivery_failure_review.created",
        resource_type="delivery_failure_review",
        resource_id=str(review.id),
        payload={
            "receipt_id": receipt.id,
            "matched_attempt_id": receipt.matched_attempt_id,
            "outbox_draft_id": review.outbox_draft_id,
            "provider": review.provider,
            "normalized_status": review.normalized_status,
            "review_reason": review.review_reason,
            "retryable": review.retryable,
            "next_action": review.next_action,
        },
    )
    return review


def list_delivery_failure_reviews(
    db: Session,
    *,
    tenant_id: int,
    status_filter: str | None,
    principal: CurrentPrincipal,
) -> list[DeliveryFailureReview]:
    if tenant_id != principal.tenant.id:
        raise HTTPException(status_code=404, detail="tenant not found")
    query = select(DeliveryFailureReview).where(DeliveryFailureReview.tenant_id == tenant_id)
    if status_filter:
        query = query.where(DeliveryFailureReview.status == status_filter)
    query = query.order_by(DeliveryFailureReview.created_at.desc(), DeliveryFailureReview.id.desc())
    return list(db.scalars(query).all())


def update_delivery_failure_review(
    db: Session,
    *,
    review_id: int,
    payload: DeliveryFailureReviewUpdate,
    principal: CurrentPrincipal,
) -> DeliveryFailureReview:
    review = db.get(DeliveryFailureReview, review_id)
    if review is None or review.tenant_id != principal.tenant.id:
        raise HTTPException(status_code=404, detail="delivery failure review not found")
    now = utc_now()
    review.status = payload.status
    review.resolution_note = payload.resolution_note
    review.updated_at = now
    if payload.status in {"resolved", "ignored"}:
        review.resolved_by_id = principal.user.id
        review.resolved_at = now
    else:
        review.resolved_by_id = None
        review.resolved_at = None
    add_audit_event(
        db,
        tenant_id=review.tenant_id,
        actor_id=principal.user.id,
        action=f"delivery_failure_review.{payload.status}",
        resource_type="delivery_failure_review",
        resource_id=str(review.id),
        payload={
            "receipt_id": review.receipt_id,
            "provider": review.provider,
            "normalized_status": review.normalized_status,
            "resolution_note": payload.resolution_note,
        },
    )
    db.commit()
    db.refresh(review)
    return review
