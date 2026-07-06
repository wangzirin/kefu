#!/usr/bin/env python3
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]


REQUIRED_PATHS = [
    "backend/app/api/outbox.py",
    "backend/app/schemas/outbox.py",
    "backend/app/services/outbox.py",
    "backend/app/migrations/versions/0004_outbox_drafts.py",
    "backend/tests/test_outbox_api.py",
]

REQUIRED_TEXT = {
    "backend/app/main.py": [
        "app.include_router(outbox.router)",
    ],
    "backend/app/models/foundation.py": [
        "class OutboxDraft",
        "__tablename__ = \"outbox_drafts\"",
        "source_review_task_id",
        "delivery_status",
    ],
    "backend/app/models/__init__.py": [
        "OutboxDraft",
    ],
    "backend/app/api/outbox.py": [
        "/human-review-tasks/{task_id}/outbox-drafts",
        "/tenants/{tenant_id}/outbox-drafts",
        "/outbox-drafts/{draft_id}/confirmation",
        "/outbox-drafts/{draft_id}/cancellation",
        "require_current_principal",
    ],
    "backend/app/services/outbox.py": [
        "create_outbox_draft_from_review_task",
        "confirm_outbox_draft",
        "cancel_outbox_draft",
        "pending_confirmation",
        "ready_to_send",
        "not_sent",
        "outbox_draft.created",
        "outbox_draft.ready_to_send",
    ],
    "backend/app/schemas/outbox.py": [
        "class OutboxDraftRead",
        "class OutboxDraftCreateFromReview",
        "class OutboxDraftConfirm",
        "class OutboxDraftCancel",
    ],
    "backend/app/migrations/versions/0004_outbox_drafts.py": [
        "outbox_drafts",
        'down_revision = "0003_knowledge_cards"',
        "ix_outbox_drafts_tenant_status",
    ],
    "backend/tests/test_outbox_api.py": [
        "test_approved_review_can_create_and_confirm_outbox_draft_without_sending",
        "test_outbox_draft_can_be_canceled_before_confirmation",
        "test_outbox_draft_requires_approved_human_review",
        "delivery_status",
        "not_sent",
    ],
}


def fail(message: str) -> None:
    print(f"FAIL stage2 outbox: {message}")
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

    print("PASS stage2 outbox")


if __name__ == "__main__":
    main()
