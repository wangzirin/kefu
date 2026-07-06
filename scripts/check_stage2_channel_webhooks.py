#!/usr/bin/env python3
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]


REQUIRED_PATHS = [
    "backend/app/services/channel_provider_registry.py",
    "backend/app/api/channel_connectors.py",
    "backend/app/schemas/channel_connectors.py",
    "backend/app/services/channel_connectors.py",
    "backend/app/services/channel_secret_store.py",
    "backend/app/services/channel_webhook_verifier.py",
    "backend/app/services/trusted_inbound_messages.py",
    "backend/tests/test_channel_webhooks_api.py",
]

REQUIRED_TEXT = {
    "backend/app/services/channel_provider_registry.py": [
        "ChannelProviderContract",
        "wecom_token_aeskey",
        "wechat_token",
        "website_hmac_sha256",
        "skeleton_only",
        "external_write_enabled",
    ],
    "backend/app/api/channel_connectors.py": [
        "/channel-providers",
        "/webhooks/{provider}/channels/{channel_id}",
        "receive_official_channel_webhook",
    ],
    "backend/app/schemas/channel_connectors.py": [
        "class ChannelProviderRead",
        "class ChannelWebhookEventCreate",
        "class ChannelWebhookEventRead",
    ],
    "backend/app/services/channel_connectors.py": [
        "list_channel_provider_registry",
        "receive_channel_webhook_event",
        "verify_channel_webhook_request",
        "create_trusted_inbound_message_if_ready",
        "channel_webhook.placeholder_received",
        "signature_values_stored",
        "trusted_message_creation",
    ],
    "backend/app/services/channel_secret_store.py": [
        "WebhookSecretMaterial",
        "p2_13_wecom_fixture",
        "p2_13_wechat_fixture",
        "p2_13_website_fixture",
        "fixture_configured",
    ],
    "backend/app/services/channel_webhook_verifier.py": [
        "wecom_sha1_token_timestamp_nonce_encrypt",
        "wechat_sha1_token_timestamp_nonce",
        "website_hmac_sha256_timestamp_nonce_payload",
        "MAX_WEBHOOK_TIMESTAMP_SKEW_SECONDS",
        "secret_not_configured",
    ],
    "backend/app/services/trusted_inbound_messages.py": [
        "build_webhook_idempotency_key",
        "trusted_inbound_message_created",
        "duplicate_ignored",
        "message.inbound.trusted_webhook",
        "queue_trusted_inbound_message_for_reply_orchestration",
    ],
    "backend/tests/test_channel_webhooks_api.py": [
        "test_channel_provider_registry_exposes_official_skeleton_contracts",
        "test_official_webhook_intake_records_untrusted_receipt_without_bearer_token",
        "test_wecom_fixture_signature_validates_without_storing_signature_value",
        "test_verified_wecom_message_webhook_creates_trusted_inbound_message",
        "test_verified_wecom_message_webhook_replay_does_not_duplicate_message",
        "test_wecom_fixture_rejects_invalid_signature_as_untrusted",
        "test_invalid_signature_does_not_create_trusted_inbound_message",
        "test_wechat_official_account_plain_fixture_signature_validates",
        "test_website_fixture_hmac_signature_validates",
        "test_webhook_intake_rejects_unknown_or_mismatched_provider",
        "test_placeholder_receipt_cannot_self_claim_signature_validation",
    ],
}


def fail(message: str) -> None:
    print(f"FAIL stage2 channel webhooks: {message}")
    sys.exit(1)


def main() -> None:
    missing = [path for path in REQUIRED_PATHS if not (ROOT / path).exists()]
    if missing:
        fail("missing files: " + ", ".join(missing))

    for path, fragments in REQUIRED_TEXT.items():
        content = (ROOT / path).read_text(encoding="utf-8")
        for fragment in fragments:
            if fragment not in content:
                fail(f"missing fragment in {path}: {fragment}")

    print("PASS stage2 channel webhooks")


if __name__ == "__main__":
    main()
