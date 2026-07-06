#!/usr/bin/env python3
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]


REQUIRED_PATHS = [
    "backend/app/api/outbox.py",
    "backend/app/schemas/outbox.py",
    "backend/app/services/outbox.py",
    "backend/app/migrations/versions/0005_outbox_send_attempts.py",
    "backend/tests/test_outbox_api.py",
]

REQUIRED_TEXT = {
    "backend/app/models/foundation.py": [
        "class OutboxSendAttempt",
        "__tablename__ = \"outbox_send_attempts\"",
        "attempt_number",
        "delivery_mode",
        "request_payload",
        "response_payload",
    ],
    "backend/app/models/__init__.py": [
        "OutboxSendAttempt",
    ],
    "backend/app/api/outbox.py": [
        "/outbox-drafts/{draft_id}/send-attempts",
        "OutboxSendAttemptCreate",
        "OutboxSendAttemptRead",
    ],
    "backend/app/services/outbox.py": [
        "create_outbox_send_attempt",
        "list_outbox_send_attempts",
        "only ready-to-send outbox drafts",
        "dry_run",
        "external_write",
        "outbox_send_attempt.dry_run_succeeded",
    ],
    "backend/app/schemas/outbox.py": [
        "class OutboxSendAttemptCreate",
        "class OutboxSendAttemptRead",
        "request_payload",
        "response_payload",
    ],
    "backend/app/migrations/versions/0005_outbox_send_attempts.py": [
        "outbox_send_attempts",
        'down_revision = "0004_outbox_drafts"',
        "ix_outbox_send_attempts_tenant_status",
    ],
    "backend/tests/test_outbox_api.py": [
        "test_ready_outbox_draft_can_create_dry_run_send_attempt_without_external_delivery",
        "test_outbox_send_attempt_requires_ready_to_send_draft",
        "delivery_status",
        "not_sent",
        "external_write",
    ],
}


def fail(message: str) -> None:
    print(f"FAIL stage2 send attempts: {message}")
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

    print("PASS stage2 send attempts")


if __name__ == "__main__":
    main()
