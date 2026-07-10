from __future__ import annotations

from dataclasses import dataclass
import base64
import hashlib
import json
import os
from pathlib import Path
from typing import Any

from app.services.channel_provider_registry import normalize_provider


@dataclass(frozen=True)
class WebhookSecretMaterial:
    provider: str
    credential_ref: str
    token: str = ""
    encoding_aes_key: str = ""
    app_secret: str = ""
    open_kfid: str = ""
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


def _secret_store_path() -> Path:
    return Path(__file__).resolve().parents[2] / "data" / "local_channel_secrets.json"


def _local_secret_key() -> bytes:
    seed = os.getenv("STANDARD_OPS_LOCAL_SECRET_KEY", "") or os.getenv("ADMIN_BOOTSTRAP_PASSWORD", "") or "wanfa-standard-ops-local-secret"
    return hashlib.sha256(seed.encode("utf-8")).digest()


def _xor_bytes(data: bytes, key: bytes) -> bytes:
    return bytes(byte ^ key[index % len(key)] for index, byte in enumerate(data))


def _encrypt_secret(value: str) -> str:
    raw = value.encode("utf-8")
    return base64.urlsafe_b64encode(_xor_bytes(raw, _local_secret_key())).decode("ascii")


def _decrypt_secret(value: str) -> str:
    raw = base64.urlsafe_b64decode(value.encode("ascii"))
    return _xor_bytes(raw, _local_secret_key()).decode("utf-8")


def _read_local_secret_store() -> dict[str, Any]:
    path = _secret_store_path()
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _write_local_secret_store(payload: dict[str, Any]) -> None:
    path = _secret_store_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def save_local_connector_secrets(*, credential_ref: str, secrets: dict[str, str]) -> dict[str, str]:
    store = _read_local_secret_store()
    clean = {key: value for key, value in secrets.items() if str(value).strip()}
    store[credential_ref] = {key: _encrypt_secret(str(value).strip()) for key, value in clean.items()}
    _write_local_secret_store(store)
    return {key: "configured" for key in clean}


def clear_local_connector_secrets(*, credential_ref: str) -> None:
    store = _read_local_secret_store()
    if credential_ref in store:
        del store[credential_ref]
        _write_local_secret_store(store)


def resolve_local_connector_secret_value(*, credential_ref: str, secret_key: str) -> str:
    encrypted = _read_local_secret_store().get(credential_ref)
    if not isinstance(encrypted, dict):
        return ""
    value = encrypted.get(secret_key)
    if not isinstance(value, str) or not value:
        return ""
    try:
        return _decrypt_secret(value)
    except Exception:
        return ""


def _resolve_local_secret_material(
    *,
    provider: str,
    credential_ref: str,
    public_config: dict[str, Any] | None = None,
) -> WebhookSecretResolution:
    encrypted = _read_local_secret_store().get(credential_ref)
    if not isinstance(encrypted, dict):
        return WebhookSecretResolution(status="reference_unresolved", detail="local credential_ref is missing")
    try:
        secrets = {key: _decrypt_secret(str(value)) for key, value in encrypted.items()}
    except Exception:
        return WebhookSecretResolution(status="invalid", detail="local credential_ref cannot be decrypted")
    normalized_provider = normalize_provider(provider)
    material = WebhookSecretMaterial(
        provider=normalized_provider,
        credential_ref=credential_ref,
        token=secrets.get("token", "") or secrets.get("callback_token", ""),
        encoding_aes_key=secrets.get("encoding_aes_key", "") or secrets.get("encodingAESKey", ""),
        app_secret=secrets.get("app_secret", "") or secrets.get("secret", ""),
        open_kfid=secrets.get("open_kfid", "") or secrets.get("kf_id", ""),
        webhook_signing_secret=secrets.get("webhook_signing_secret", "") or secrets.get("signing_secret", ""),
        receiver_id=(
            secrets.get("receiver_id", "")
            or secrets.get("corp_id", "")
            or secrets.get("app_id", "")
            or str((public_config or {}).get("corp_id") or "").strip()
            or str((public_config or {}).get("receiver_id") or "").strip()
        ),
        source="local_encrypted",
    )
    missing_fields: list[str] = []
    if normalized_provider in {"wecom", "wechat_official_account", "wechat_kf", "wechat_miniapp"}:
        if not material.token:
            missing_fields.append("token")
        if normalized_provider != "wechat_miniapp" and not material.encoding_aes_key:
            missing_fields.append("encoding_aes_key")
        if normalized_provider == "wechat_kf":
            if not material.receiver_id:
                missing_fields.append("corp_id")
    elif normalized_provider == "website" and not material.webhook_signing_secret:
        missing_fields.append("webhook_signing_secret")
    if missing_fields:
        return WebhookSecretResolution(status="local_missing_fields", material=material, detail="missing fields: " + ",".join(missing_fields))
    return WebhookSecretResolution(status="local_configured", material=material)


def _resolve_env_secret_material(*, provider: str, credential_ref: str) -> WebhookSecretResolution:
    prefix = credential_ref.removeprefix("env:").strip().upper()
    if not prefix:
        return WebhookSecretResolution(
            status="reference_unresolved",
            detail="env credential_ref must include an environment variable prefix",
        )

    normalized_provider = normalize_provider(provider)
    receiver_id = _env_first(f"{prefix}_RECEIVER_ID", f"{prefix}_CORP_ID", f"{prefix}_APP_ID")
    if normalize_provider(provider) in {"wecom", "wechat_kf"}:
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
        app_secret=_env_first(f"{prefix}_APP_SECRET", f"{prefix}_SECRET", f"{prefix}_CORP_SECRET"),
        open_kfid=_env_first(f"{prefix}_OPEN_KFID", f"{prefix}_KF_ID"),
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
    elif normalized_provider == "wechat_kf":
        if not material.token:
            missing_fields.append(f"{prefix}_TOKEN")
        if not material.encoding_aes_key:
            missing_fields.append(f"{prefix}_ENCODING_AES_KEY")
        if not material.receiver_id:
            missing_fields.append(f"{prefix}_CORP_ID")
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
    if credential_ref.startswith("local:"):
        return _resolve_local_secret_material(provider=provider, credential_ref=credential_ref, public_config=public_config)
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
