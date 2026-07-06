#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def run_p3_06e_ops_worker_health_readiness(root: Path = ROOT) -> dict:
    required_files = [
        "backend/app/api/ops.py",
        "backend/app/schemas/ops.py",
        "backend/tests/test_p3_06e_ops_worker_health_api.py",
        "frontend/src/api/client.ts",
        "frontend/src/App.tsx",
        "frontend/src/styles.css",
        "frontend/src/data/navigation.ts",
        "docs/P3-06E_OPS_WORKER_HEALTH_PANEL.md",
    ]
    errors: list[str] = []
    for relative in required_files:
        if not (root / relative).exists():
            errors.append(f"missing required file: {relative}")

    if errors:
        return _result(errors)

    api_text = _read(root / "backend/app/api/ops.py")
    schema_text = _read(root / "backend/app/schemas/ops.py")
    main_text = _read(root / "backend/app/main.py")
    client_text = _read(root / "frontend/src/api/client.ts")
    app_text = _read(root / "frontend/src/App.tsx")
    nav_text = _read(root / "frontend/src/data/navigation.ts")
    css_text = _read(root / "frontend/src/styles.css")
    doc_text = _read(root / "docs/P3-06E_OPS_WORKER_HEALTH_PANEL.md")
    test_text = _read(root / "backend/tests/test_p3_06e_ops_worker_health_api.py")

    required_snippets = [
        (api_text, "/tenants/{tenant_id}/ops/worker-health", "ops worker health route missing"),
        (api_text, 'require_any_role("owner", "admin")', "ops route must require owner/admin"),
        (api_text, "external_call_performed=False", "ops route must declare no external call"),
        (api_text, "external_platform_write_performed=False", "ops route must declare no external write"),
        (schema_text, "class WorkerHealthDashboardRead", "ops dashboard schema missing"),
        (schema_text, "WorkerHeartbeatRead", "ops schema must include heartbeat list"),
        (schema_text, "TrustedInboundWorkerRunRecordRead", "ops schema must include recent run list"),
        (main_text, "app.include_router(ops.router)", "ops router not included in app"),
        (client_text, "getWorkerHealthDashboard", "frontend client missing ops health fetcher"),
        (app_text, 'case "ops"', "frontend ops workspace route missing"),
        (app_text, "OpsWorkerHealthPanel", "ops panel component missing"),
        (nav_text, 'href: "#ops"', "navigation missing ops entry"),
        (nav_text, 'count: "P3-06E"', "navigation stage must be P3-06E"),
        (css_text, ".ops-health-strip", "ops health styles missing"),
        (css_text, ".ops-table", "ops table styles missing"),
        (doc_text, "不触发模型调用", "doc must state no model calls"),
        (doc_text, "不写外部平台", "doc must state no external platform write"),
        (test_text, "test_ops_worker_health_dashboard_summarizes_heartbeats_and_recent_runs", "focused test missing"),
    ]
    for text, snippet, message in required_snippets:
        if snippet not in text:
            errors.append(message)

    return _result(errors)


def _result(errors: list[str]) -> dict:
    return {
        "status": "failed" if errors else "passed",
        "phase": "P3-06E",
        "check": "ops_worker_health_panel",
        "external_call_performed": False,
        "external_platform_write_performed": False,
        "production_database_write_performed": False,
        "errors": errors,
    }


def main() -> int:
    result = run_p3_06e_ops_worker_health_readiness()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result["status"] != "passed":
        return 1
    print("PASS p3-06e ops worker health")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
