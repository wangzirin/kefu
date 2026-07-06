from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Any

from app.services.channel_provider_registry import normalize_provider


@dataclass(frozen=True)
class WebhookSecretMaterial:
    provider: str
    credential_ref: str
    token: str = ""
    encoding_aes_key: str = ""
    webhook_signing_secret: str = ""
    receiver_id: str = ""
    source: str = "fixture"


@dataclass(frozen=True)
class WebhookSecretResolution:
    status: str
    material: WebhookSecretMaterial | None = None
    detail: str = ""


# P2-13 uses deterministic development fixtures to prove the trust boundary.
# Real customer tokens, EncodingAESKey values, app secrets, and signing secrets
# must come from a secret store or KMS in a later stage.
_WEBHOOK_SECRET_FIXTURES: dict[str, WebhookSecretMaterial] = {
    "p2_13_wecom_fixture": WebhookSecretMaterial(
        provider="wecom",
        credential_ref="p2_13_wecom_fixture",
        token="p2_13_wecom_token",
        encoding_aes_key="p2_13_wecom_encoding_aes_key_fixture_only",
    ),
    "p2_13_wechat_fixture": WebhookSecretMaterial(
        provider="wechat_official_account",
        credential_ref="p2_13_wechat_fixture",
        token="p2_13_wechat_token",
        encoding_aes_key="p2_13_wechat_encoding_aes_key_fixture_only",
    ),
    "p2_13_website_fixture": WebhookSecretMaterial(
        provider="website",
        credential_ref="p2_13_website_fixture",
        webhook_signing_secret="p2_13_website_signing_secret",
    ),
}


def _credential_ref_from_public_config(public_config: dict[str, Any] | None) -> str:
    if not public_config:
        return ""
    value = public_config.get("credential_ref", "")
    return str(value).strip()


def _env_first(*keys: str) -> str:
    for key in keys:
        value = os.getenv(key, "").strip()
        if value:
            return value
    return ""


def _resolve_env_secret_material(*, provider: str, credential_ref: str) -> WebhookSecretResolution:
    prefix = credential_ref.removeprefix("env:").strip().upper()
    if not prefix:
        return WebhookSecretResolution(
            status="reference_unresolved",
            detail="env credential_ref must include an environment variable prefix",
        )

    normalized_provider = normalize_provider(provider)
    receiver_id = _env_first(f"{prefix}_RECEIVER_ID", f"{prefix}_CORP_ID", f"{prefix}_APP_ID")
    if normalize_provider(provider) == "wecom":
        receiver_id = receiver_id or _env_first("WECOM_CORP_ID")
    material = WebhookSecretMaterial(
        provider=normalized_provider,
        credential_ref=credential_ref,
        token=_env_first(f"{prefix}_TOKEN", f"{prefix}_CALLBACK_TOKEN", f"{prefix}_WEBHOOK_TOKEN"),
        encoding_aes_key=_env_first(
            f"{prefix}_ENCODING_AES_KEY",
            f"{prefix}_ENCODINGAESKEY",
            f"{prefix}_AES_KEY",
        ),
        webhook_signing_secret=_env_first(f"{prefix}_WEBHOOK_SIGNING_SECRET", f"{prefix}_SIGNING_SECRET"),
        receiver_id=receiver_id,
        source="env",
    )
    missing_fields: list[str] = []
    if normalized_provider in {"wecom", "wechat_official_account"}:
        if not material.token:
            missing_fields.append(f"{prefix}_TOKEN")
        if not material.encoding_aes_key:
            missing_fields.append(f"{prefix}_ENCODING_AES_KEY")
    elif normalized_provider == "website" and not material.webhook_signing_secret:
        missing_fields.append(f"{prefix}_WEBHOOK_SIGNING_SECRET")
    else:
        return WebhookSecretResolution(
            status="provider_mismatch",
            detail="env credential_ref is not supported for this provider",
        )
    if missing_fields:
        return WebhookSecretResolution(
            status="env_missing_fields",
            detail="missing environment variables: " + ",".join(missing_fields),
        )
    return WebhookSecretResolution(status="env_configured", material=material)


def resolve_webhook_secret_material(
    *,
    provider: str,
    public_config: dict[str, Any] | None,
) -> WebhookSecretResolution:
    credential_ref = _credential_ref_from_public_config(public_config)
    if not credential_ref:
        return WebhookSecretResolution(
            status="not_configured",
            detail="connector public_config does not contain credential_ref",
        )
    if credential_ref.startswith("env:"):
        return _resolve_env_secret_material(provider=provider, credential_ref=credential_ref)
    material = _WEBHOOK_SECRET_FIXTURES.get(credential_ref)
    if material is None:
        return WebhookSecretResolution(
            status="reference_unresolved",
            detail="credential_ref is not resolvable by the current secret store boundary",
        )
    if normalize_provider(material.provider) != normalize_provider(provider):
        return WebhookSecretResolution(
            status="provider_mismatch",
            detail="credential_ref exists but belongs to another provider",
        )
    return WebhookSecretResolution(status="fixture_configured", material=material)


def connector_secret_status(*, provider: str, public_config: dict[str, Any] | None) -> str:
    return resolve_webhook_secret_material(provider=provider, public_config=public_config).status
