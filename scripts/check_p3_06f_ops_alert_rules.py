from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def run_p3_06f_ops_alert_rules_readiness() -> dict:
    checks = {
        "backend/app/api/ops.py": [
            "/ops/alert-rules",
            "OpsAlertRulesDashboardRead",
            "notification_channel_enabled=False",
            "notification_sent=False",
            "external_call_performed=False",
            "external_platform_write_performed=False",
            "trusted_inbound_processing_unavailable",
            "trusted_inbound_rate_limit_saturation",
        ],
        "backend/app/schemas/ops.py": [
            "class OpsAlertRunbookRead",
            "class OpsAlertRuleRead",
            "class OpsAlertRulesDashboardRead",
        ],
        "backend/tests/test_p3_06f_ops_alert_rules_api.py": [
            "test_ops_alert_rules_dashboard_evaluates_worker_alerts",
            "notification_sent",
            "trusted_inbound_worker_stale",
            "trusted_inbound_worker_failed",
        ],
        "frontend/src/api/client.ts": [
            "export interface OpsAlertRulesDashboard",
            "export async function getOpsAlertRulesDashboard",
            "/ops/alert-rules",
        ],
        "frontend/src/App.tsx": [
            "type OpsAlertRulesState",
            "refreshOpsAlertRules",
            "OpsAlertRuleCard",
            "告警规则",
            "notification_channel_enabled",
            "opsAlertRules",
        ],
        "frontend/src/styles.css": [
            ".ops-alert-rule-summary",
            ".ops-alert-rules-grid",
            ".ops-alert-rule-card",
            ".ops-alert-runbook",
        ],
        "frontend/src/data/navigation.ts": [
            'href: "#overview"',
            'href: "#ops"',
            'count: "健康"',
            'count: "运维"',
        ],
        "docs/P3-06F_OPS_ALERT_RULES.md": [
            "告警规则第一片",
            "不会发送企业微信、飞书、短信、邮件或 PagerDuty 通知",
            "不触发模型调用",
            "不写任何外部平台",
        ],
    }
    errors: list[str] = []
    for relative_path, snippets in checks.items():
        path = ROOT / relative_path
        _require(errors, path.exists(), f"missing file: {relative_path}")
        if not path.exists():
            continue
        text = _read(relative_path)
        for snippet in snippets:
            _require(errors, snippet in text, f"missing snippet in {relative_path}: {snippet}")
        if relative_path == "frontend/src/data/navigation.ts":
            _require(errors, 'count: "P3-06F"' not in text, "navigation must not expose P3-06F stage marker")
    return {
        "status": "passed" if not errors else "failed",
        "phase": "P3-06F",
        "check": "ops_alert_rules",
        "notification_channel_enabled": False,
        "notification_sent": False,
        "external_call_performed": False,
        "external_platform_write_performed": False,
        "production_database_write_performed": False,
        "errors": errors,
    }


if __name__ == "__main__":
    result = run_p3_06f_ops_alert_rules_readiness()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result["status"] != "passed":
        raise SystemExit(1)
    print("PASS p3-06f ops alert rules")
