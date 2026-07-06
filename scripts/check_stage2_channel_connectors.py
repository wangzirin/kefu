#!/usr/bin/env python3
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]


REQUIRED_PATHS = [
    "backend/app/api/channel_connectors.py",
    "backend/app/schemas/channel_connectors.py",
    "backend/app/services/channel_connectors.py",
    "backend/app/migrations/versions/0006_channel_connectors.py",
    "backend/tests/test_channel_connectors_api.py",
]

REQUIRED_TEXT = {
    "backend/app/models/foundation.py": [
        "class ChannelConnector",
        "__tablename__ = \"channel_connectors\"",
        "external_write_enabled",
        "class ChannelDeliveryReceipt",
        "__tablename__ = \"channel_delivery_receipts\"",
        "verification_status",
    ],
    "backend/app/api/channel_connectors.py": [
        "/channels/{channel_id}/connector-config",
        "/outbox-drafts/{draft_id}/connector-send-plans",
        "/channels/{channel_id}/delivery-receipts",
    ],
    "backend/app/services/channel_connectors.py": [
        "external_delivery_disabled",
        "official_api_enabled",
        "not_verified_placeholder",
        "channel_connector.configured",
        "channel_connector.send_plan_created",
        "channel_delivery_receipt.placeholder_recorded",
    ],
    "backend/app/migrations/versions/0006_channel_connectors.py": [
        'down_revision = "0005_outbox_send_attempts"',
        "channel_connectors",
        "channel_delivery_receipts",
    ],
    "backend/tests/test_channel_connectors_api.py": [
        "test_channel_connector_config_and_noop_send_plan_never_external_writes",
        "test_connector_send_plan_requires_configured_connector",
        "test_channel_delivery_receipt_placeholder_records_unmatched_event_without_claiming_verification",
        "test_channel_connector_config_is_tenant_isolated",
    ],
}


def fail(message: str) -> None:
    print(f"FAIL stage2 channel connectors: {message}")
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

    print("PASS stage2 channel connectors")


if __name__ == "__main__":
    main()
