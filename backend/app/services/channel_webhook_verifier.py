from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import hmac
import json
from typing import Any

from app.models import ChannelConnector
from app.services.channel_secret_store import resolve_webhook_secret_material
from app.services.channel_provider_registry import normalize_provider


MAX_WEBHOOK_TIMESTAMP_SKEW_SECONDS = 300


@dataclass(frozen=True)
class WebhookVerificationResult:
    status: str
    signature_validated: bool
    next_action: str
    method: str
    detail: str = ""


def _sha1_sorted_signature(parts: list[str]) -> str:
    return hashlib.sha1("".join(sorted(parts)).encode("utf-8")).hexdigest()


def _constant_time_equal(left: str, right: str) -> bool:
    return hmac.compare_digest(str(left).strip().lower(), str(right).strip().lower())


def _missing_required_query(query_params: dict[str, str], required_keys: tuple[str, ...]) -> str:
    missing = [key for key in required_keys if not query_params.get(key)]
    return ",".join(missing)


def _timestamp_status(timestamp: str) -> tuple[bool, str]:
    try:
        timestamp_int = int(timestamp)
    except (TypeError, ValueError):
        return False, "timestamp_invalid"
    now = int(datetime.now(timezone.utc).timestamp())
    if abs(now - timestamp_int) > MAX_WEBHOOK_TIMESTAMP_SKEW_SECONDS:
        return False, "timestamp_expired"
    return True, ""


def _extract_encrypt(raw_payload: dict[str, Any]) -> str:
    for key in ("Encrypt", "encrypt", "msg_encrypt"):
        value = raw_payload.get(key)
        if value:
            return str(value)
    return ""


def _canonical_json(raw_payload: dict[str, Any]) -> str:
    return json.dumps(raw_payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _valid_result(method: str) -> WebhookVerificationResult:
    return WebhookVerificationResult(
        status="signature_validated",
        signature_validated=True,
        next_action="build_trusted_inbound_message_pipeline_before_creating_messages",
        method=method,
    )


def _invalid_result(status: str, *, method: str, detail: str, next_action: str) -> WebhookVerificationResult:
    return WebhookVerificationResult(
        status=status,
        signature_validated=False,
        next_action=next_action,
        method=method,
        detail=detail,
    )


def _verify_wecom(
    *,
    token: str,
    raw_payload: dict[str, Any],
    query_params: dict[str, str],
) -> WebhookVerificationResult:
    method = "wecom_sha1_token_timestamp_nonce_encrypt"
    missing = _missing_required_query(query_params, ("msg_signature", "timestamp", "nonce"))
    if missing:
        return _invalid_result(
            "required_query_missing",
            method=method,
            detail=f"missing query keys: {missing}",
            next_action="provide_required_official_webhook_query_keys",
        )
    timestamp_ok, timestamp_error = _timestamp_status(query_params["timestamp"])
    if not timestamp_ok:
        return _invalid_result(
            timestamp_error,
            method=method,
            detail="timestamp is missing, invalid, or outside the replay protection window",
            next_action="reject_replayed_or_stale_webhook_before_trusting_message",
        )
    encrypt = _extract_encrypt(raw_payload)
    if not encrypt:
        return _invalid_result(
            "encrypted_payload_missing",
            method=method,
            detail="wecom webhook fixture requires Encrypt payload before trust",
            next_action="provide_encrypted_payload_before_trusting_webhook",
        )
    expected = _sha1_sorted_signature([token, query_params["timestamp"], query_params["nonce"], encrypt])
    if _constant_time_equal(expected, query_params["msg_signature"]):
        return _valid_result(method)
    return _invalid_result(
        "signature_invalid",
        method=method,
        detail="msg_signature does not match server-side SHA1 calculation",
        next_action="inspect_official_webhook_signature_or_secret_ref",
    )


def _verify_wechat_official_account(
    *,
    token: str,
    raw_payload: dict[str, Any],
    query_params: dict[str, str],
) -> WebhookVerificationResult:
    encrypt = _extract_encrypt(raw_payload)
    if encrypt or query_params.get("msg_signature"):
        method = "wechat_sha1_token_timestamp_nonce_encrypt"
        missing = _missing_required_query(query_params, ("msg_signature", "timestamp", "nonce"))
        signature_key = "msg_signature"
        signature_parts = [token, query_params.get("timestamp", ""), query_params.get("nonce", ""), encrypt]
        if not encrypt:
            return _invalid_result(
                "encrypted_payload_missing",
                method=method,
                detail="wechat encrypted mode requires Encrypt payload before trust",
                next_action="provide_encrypted_payload_before_trusting_webhook",
            )
    else:
        method = "wechat_sha1_token_timestamp_nonce"
        missing = _missing_required_query(query_params, ("signature", "timestamp", "nonce"))
        signature_key = "signature"
        signature_parts = [token, query_params.get("timestamp", ""), query_params.get("nonce", "")]
    if missing:
        return _invalid_result(
            "required_query_missing",
            method=method,
            detail=f"missing query keys: {missing}",
            next_action="provide_required_official_webhook_query_keys",
        )
    timestamp_ok, timestamp_error = _timestamp_status(query_params["timestamp"])
    if not timestamp_ok:
        return _invalid_result(
            timestamp_error,
            method=method,
            detail="timestamp is missing, invalid, or outside the replay protection window",
            next_action="reject_replayed_or_stale_webhook_before_trusting_message",
        )
    expected = _sha1_sorted_signature(signature_parts)
    if _constant_time_equal(expected, query_params[signature_key]):
        return _valid_result(method)
    return _invalid_result(
        "signature_invalid",
        method=method,
        detail=f"{signature_key} does not match server-side SHA1 calculation",
        next_action="inspect_official_webhook_signature_or_secret_ref",
    )


def _verify_website(
    *,
    signing_secret: str,
    raw_payload: dict[str, Any],
    query_params: dict[str, str],
) -> WebhookVerificationResult:
    method = "website_hmac_sha256_timestamp_nonce_payload"
    missing = _missing_required_query(query_params, ("signature", "timestamp", "nonce"))
    if missing:
        return _invalid_result(
            "required_query_missing",
            method=method,
            detail=f"missing query keys: {missing}",
            next_action="provide_required_official_webhook_query_keys",
        )
    timestamp_ok, timestamp_error = _timestamp_status(query_params["timestamp"])
    if not timestamp_ok:
        return _invalid_result(
            timestamp_error,
            method=method,
            detail="timestamp is missing, invalid, or outside the replay protection window",
            next_action="reject_replayed_or_stale_webhook_before_trusting_message",
        )
    signing_base = f"{query_params['timestamp']}\n{query_params['nonce']}\n{_canonical_json(raw_payload)}"
    expected = hmac.new(
        signing_secret.encode("utf-8"),
        signing_base.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    if _constant_time_equal(expected, query_params["signature"]):
        return _valid_result(method)
    return _invalid_result(
        "signature_invalid",
        method=method,
        detail="signature does not match server-side HMAC calculation",
        next_action="inspect_official_webhook_signature_or_secret_ref",
    )


def verify_channel_webhook_request(
    *,
    connector: ChannelConnector,
    raw_payload: dict[str, Any],
    query_params: dict[str, str],
) -> WebhookVerificationResult:
    secret_resolution = resolve_webhook_secret_material(
        provider=connector.provider,
        public_config=connector.public_config,
    )
    if secret_resolution.material is None:
        if secret_resolution.status == "not_configured":
            return _invalid_result(
                "secret_not_configured",
                method="secret_store_boundary",
                detail=secret_resolution.detail,
                next_action="configure_secret_store_before_trusting_webhook",
            )
        return _invalid_result(
            f"secret_{secret_resolution.status}",
            method="secret_store_boundary",
            detail=secret_resolution.detail,
            next_action="inspect_official_webhook_signature_or_secret_ref",
        )
    provider = normalize_provider(connector.provider)
    if provider == "wecom":
        return _verify_wecom(
            token=secret_resolution.material.token,
            raw_payload=raw_payload,
            query_params=query_params,
        )
    if provider == "wechat_official_account":
        return _verify_wechat_official_account(
            token=secret_resolution.material.token,
            raw_payload=raw_payload,
            query_params=query_params,
        )
    if provider == "website":
        return _verify_website(
            signing_secret=secret_resolution.material.webhook_signing_secret,
            raw_payload=raw_payload,
            query_params=query_params,
        )
    return _invalid_result(
        "verification_not_implemented",
        method="provider_dispatch",
        detail=f"provider verifier is not implemented: {connector.provider}",
        next_action="implement_provider_signature_verifier_before_trusting_webhook",
    )
