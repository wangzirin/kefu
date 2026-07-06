#!/usr/bin/env python3
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]


REQUIRED_TEXT = {
    "backend/app/models/foundation.py": [
        "class OutboxDeliveryJob",
        "outbox_delivery_jobs",
        "external_write_requested",
        "external_write_permitted",
        "dead_letter_reason",
    ],
    "backend/app/migrations/versions/0008_outbox_delivery_jobs.py": [
        "outbox_delivery_jobs",
        "uq_outbox_delivery_jobs_tenant_id_idempotency_key",
        "ix_outbox_delivery_jobs_tenant_status_next_run",
    ],
    "backend/app/core/config.py": [
        "outbox_external_write_enabled",
        "OUTBOX_EXTERNAL_WRITE_ENABLED",
    ],
    ".env.example": [
        "OUTBOX_EXTERNAL_WRITE_ENABLED=false",
    ],
    "backend/app/services/outbox_delivery_queue.py": [
        "run_outbox_delivery_queue",
        "create_outbox_delivery_job",
        "external_write_kill_switch",
        "channel_not_active",
        "DEAD_LETTER",
        "attach_delivery_normalization_and_review",
    ],
    "backend/app/api/outbox.py": [
        "/outbox-drafts/{draft_id}/delivery-jobs",
        "/tenants/{tenant_id}/outbox-delivery-jobs",
        "/tenants/{tenant_id}/outbox-delivery-queue-runs",
    ],
    "backend/app/schemas/outbox.py": [
        "OutboxDeliveryJobRead",
        "OutboxDeliveryQueueRunRead",
        "kill_switch",
        "dead_lettered",
    ],
    "backend/tests/test_outbox_delivery_queue_api.py": [
        "test_delivery_queue_creates_single_job_and_repeated_runs_do_not_duplicate_attempts",
        "test_delivery_queue_kill_switch_blocks_external_write_requested_job_and_creates_review",
        "test_delivery_queue_rate_limit_leaves_due_job_unprocessed_without_attempt",
        "test_delivery_queue_retries_then_dead_letters_channel_failure",
    ],
    "frontend/src/api/client.ts": [
        "OutboxDeliveryJob",
        "OutboxDeliveryQueueRun",
        "createOutboxDeliveryJob",
        "runOutboxDeliveryQueue",
    ],
    "frontend/src/App.tsx": [
        "DeliveryQueueState",
        "handleCreateDeliveryJob",
        "handleRunDeliveryQueue",
        "运行发送队列",
        "加入发送队列",
    ],
}


def fail(message: str) -> None:
    print(f"FAIL stage2 outbox delivery queue: {message}")
    sys.exit(1)


def main() -> None:
    for path, fragments in REQUIRED_TEXT.items():
        full_path = ROOT / path
        if not full_path.exists():
            fail(f"missing file: {path}")
        content = full_path.read_text(encoding="utf-8")
        missing = [fragment for fragment in fragments if fragment not in content]
        if missing:
            fail(f"missing fragment in {path}: {', '.join(missing)}")
    print("PASS stage2 outbox delivery queue")


if __name__ == "__main__":
    main()
