from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def require_contains(path: str, snippets: list[str]) -> None:
    text = (ROOT / path).read_text()
    missing = [snippet for snippet in snippets if snippet not in text]
    if missing:
        raise SystemExit(f"{path} missing: {', '.join(missing)}")


def main() -> None:
    require_contains(
        "backend/app/workers/outbox_sender.py",
        [
            "run_outbox_worker_dry_run",
            "DRY_RUN_WORKER",
            "receipt_placeholder",
            "retry_placeholder",
            "rate_limited_draft_ids",
            "external_write",
        ],
    )
    require_contains(
        "backend/app/api/outbox.py",
        [
            "/tenants/{tenant_id}/outbox-worker-runs",
            "OutboxWorkerRunCreate",
            "OutboxWorkerRunRead",
            "run_outbox_worker_dry_run",
        ],
    )
    require_contains(
        "backend/app/schemas/outbox.py",
        [
            "OutboxWorkerRunCreate",
            "OutboxWorkerRunRead",
            "rate_limited_draft_ids",
            "attempts: list[OutboxSendAttemptRead]",
        ],
    )
    require_contains(
        "backend/app/core/config.py",
        [
            "outbox_worker_batch_size",
            "outbox_worker_rate_limit_per_minute",
            "outbox_worker_max_attempts",
        ],
    )
    require_contains(
        ".env.example",
        [
            "OUTBOX_WORKER_BATCH_SIZE",
            "OUTBOX_WORKER_RATE_LIMIT_PER_MINUTE",
            "OUTBOX_WORKER_MAX_ATTEMPTS",
        ],
    )
    require_contains(
        "backend/tests/test_outbox_api.py",
        [
            "test_outbox_worker_dry_run_processes_ready_draft_with_receipt_and_rate_limit_metadata",
            "test_outbox_worker_records_failed_attempt_and_retry_placeholder_for_inactive_channel",
            "test_outbox_worker_rate_limit_records_unprocessed_ready_drafts_without_attempts",
        ],
    )
    require_contains(
        "frontend/src/api/client.ts",
        [
            "OutboxWorkerRun",
            "runOutboxWorker",
            "/outbox-worker-runs",
        ],
    )
    require_contains(
        "frontend/src/App.tsx",
        [
            "handleRunWorker",
            "运行发送检查",
            "最近发送检查",
            "外部写入：否",
        ],
    )
    print("PASS stage2 outbox worker")


if __name__ == "__main__":
    main()
