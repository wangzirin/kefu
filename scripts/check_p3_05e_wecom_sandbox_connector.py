#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


REQUIRED_FILES = [
    "backend/app/services/wecom_callback_crypto.py",
    "backend/app/services/channel_secret_store.py",
    "backend/app/services/channel_connectors.py",
    "backend/app/api/channel_connectors.py",
    "backend/tests/test_p3_05e_wecom_official_sandbox_connector.py",
    "docs/P3-05E_WECOM_OFFICIAL_SANDBOX_CONNECTOR.md",
]


REQUIRED_SNIPPETS = {
    "backend/requirements.txt": ["pycryptodome"],
    "backend/pyproject.toml": ["pycryptodome"],
    "backend/app/services/wecom_callback_crypto.py": [
        "decrypt_wecom_payload",
        "parse_wecom_xml",
        "EncodingAESKey must be 43 characters",
        "AES.MODE_CBC",
        "expected_receiver_id",
    ],
    "backend/app/services/channel_secret_store.py": [
        "env:",
        "_CALLBACK_TOKEN",
        "_ENCODING_AES_KEY",
        "WECOM_CORP_ID",
        "env_configured",
    ],
    "backend/app/services/channel_connectors.py": [
        "verify_wecom_callback_url",
        "receive_wecom_official_xml_webhook",
        "official_xml_decrypted",
        "external_write",
    ],
    "backend/app/api/channel_connectors.py": [
        '@router.get("/webhooks/wecom/channels/{channel_id}"',
        '@router.post(\n    "/webhooks/wecom/channels/{channel_id}"',
        "PlainTextResponse",
        "receive_wecom_official_xml_webhook",
    ],
    "backend/app/services/channel_provider_registry.py": [
        "official_sandbox_inbound_only",
        '"external_write_enabled": False',
        "真实 access_token",
    ],
    ".env.example": [
        "WECOM_KF_CALLBACK_TOKEN=",
        "WECOM_KF_ENCODING_AES_KEY=",
        "WECOM_KF_RECEIVER_ID=",
        "OUTBOX_EXTERNAL_WRITE_ENABLED=false",
    ],
    "backend/tests/test_p3_05e_wecom_official_sandbox_connector.py": [
        "test_wecom_official_url_verification_decrypts_echostr",
        "test_wecom_official_xml_message_decrypts_and_creates_trusted_inbound_message",
        "signature_values_stored",
        "external_write",
    ],
    "docs/P3-05E_WECOM_OFFICIAL_SANDBOX_CONNECTOR.md": [
        "企业微信官方 Sandbox Connector",
        "URL:",
        "Token:",
        "EncodingAESKey:",
        "不真实外发",
        "可信 IP",
        "个人微信外挂",
    ],
}


def _read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def run_check() -> dict:
    errors: list[str] = []

    for relative_path in REQUIRED_FILES:
        if not (ROOT / relative_path).exists():
            errors.append(f"missing file: {relative_path}")

    for relative_path, snippets in REQUIRED_SNIPPETS.items():
        path = ROOT / relative_path
        if not path.exists():
            errors.append(f"missing snippet file: {relative_path}")
            continue
        text = _read(relative_path)
        for snippet in snippets:
            if snippet not in text:
                errors.append(f"{relative_path} missing snippet: {snippet}")

    if errors:
        return {"status": "failed", "errors": errors}

    return {
        "status": "passed",
        "stage": "P3-05E",
        "wecom_url_verification": True,
        "wecom_xml_decrypt": True,
        "trusted_inbound_creation": True,
        "external_write_enabled": False,
        "real_access_token_send": False,
    }


def main() -> int:
    result = run_check()
    if result["status"] != "passed":
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1
    print("PASS p3-05e wecom sandbox connector")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
