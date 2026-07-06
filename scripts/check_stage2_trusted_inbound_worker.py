#!/usr/bin/env python3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def require_contains(path: str, snippets: list[str]) -> None:
    text = (ROOT / path).read_text(encoding="utf-8")
    missing = [snippet for snippet in snippets if snippet not in text]
    if missing:
        raise SystemExit(f"{path} missing: {', '.join(missing)}")


def main() -> None:
    require_contains(
        "backend/app/workers/trusted_inbound_orchestrator.py",
        [
            "run_trusted_inbound_worker",
            "TRUSTED_INBOUND_EVENT_TYPE",
            "trusted_inbound_message:{message_id}:reply_orchestration",
            "orchestrate_reply_for_message",
            "trusted_inbound_worker.orchestrated",
            "trusted_inbound_worker.failed",
            "external_write",
        ],
    )
    require_contains(
        "backend/app/api/inbound_worker.py",
        [
            "/tenants/{tenant_id}/trusted-inbound-worker-runs",
            "TrustedInboundWorkerRunCreate",
            "TrustedInboundWorkerRunRead",
            "run_trusted_inbound_worker",
            "require_current_principal",
        ],
    )
    require_contains(
        "backend/app/schemas/inbound_worker.py",
        [
            "TrustedInboundWorkerRunCreate",
            "TrustedInboundWorkerItemRead",
            "TrustedInboundWorkerRunRead",
            "rate_limited_message_ids",
            "external_write",
        ],
    )
    require_contains(
        "backend/app/main.py",
        [
            "inbound_worker",
            "app.include_router(inbound_worker.router)",
        ],
    )
    require_contains(
        "backend/tests/test_trusted_inbound_worker_api.py",
        [
            "test_trusted_inbound_worker_orchestrates_verified_message_into_human_review_inbox",
            "test_trusted_inbound_worker_respects_rate_limit_without_creating_workflow",
            "test_trusted_inbound_worker_ignores_untrusted_webhook_receipts",
            "trusted-inbound-worker-runs",
            "human-review-inbox",
        ],
    )
    require_contains(
        "frontend/src/api/client.ts",
        [
            "TrustedInboundWorkerRun",
            "runTrustedInboundWorker",
            "/trusted-inbound-worker-runs",
        ],
    )
    require_contains(
        "frontend/src/App.tsx",
        [
            "handleRunInboundWorker",
            "运行入站编排",
            "最近入站编排",
            "外部写入：否",
        ],
    )
    print("PASS stage2 trusted inbound worker")


if __name__ == "__main__":
    main()
