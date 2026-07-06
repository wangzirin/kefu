#!/usr/bin/env python3
"""Static readiness checks for P3-06G ops metrics export."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_text(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    api = read_text("backend/app/api/ops.py")
    schemas = read_text("backend/app/schemas/ops.py")
    client = read_text("frontend/src/api/client.ts")
    app = read_text("frontend/src/App.tsx")
    styles = read_text("frontend/src/styles.css")
    test = read_text("backend/tests/test_p3_06g_ops_metrics_api.py")
    doc = read_text("docs/P3-06G_OPS_METRICS_EXPORT.md")

    for snippet in [
        "OpsMetricRead",
        "OpsMetricsSummary",
        "OpsMetricsDashboardRead",
        "prometheus_text",
        "ready_for_prometheus_scrape",
    ]:
        require(snippet in schemas, f"schemas missing metrics snippet: {snippet}")

    for snippet in [
        '"/tenants/{tenant_id}/ops/metrics"',
        "get_ops_metrics_dashboard",
        "_build_ops_metrics",
        "_build_prometheus_text",
        "wanfa_worker_failed",
        "wanfa_outbox_delivery_jobs",
        "wanfa_delivery_failure_reviews_open",
        "external_call_performed=False",
        "external_platform_write_performed=False",
    ]:
        require(snippet in api, f"ops API missing metrics snippet: {snippet}")

    for snippet in [
        "OpsMetricsDashboard",
        "OpsMetricsSummary",
        "OpsMetric",
        "getOpsMetricsDashboard",
        "/ops/metrics",
    ]:
        require(snippet in client, f"frontend client missing metrics snippet: {snippet}")

    for snippet in [
        "OpsMetricsState",
        "opsMetrics",
        "指标出口",
        "采集文本预览",
        "formatMetricDisplayValue",
        "formatMetricLabels",
        "refreshOpsMetrics",
    ]:
        require(snippet in app, f"App missing metrics snippet: {snippet}")

    for snippet in [
        ".ops-metrics-grid",
        ".ops-metrics-layout",
        ".ops-metric-row",
        ".ops-prometheus-preview",
    ]:
        require(snippet in styles, f"styles missing metrics snippet: {snippet}")

    for snippet in [
        "test_ops_metrics_dashboard_exports_worker_queue_and_alert_metrics",
        "test_ops_metrics_dashboard_requires_same_tenant",
        "wanfa_outbox_delivery_jobs",
        "prometheus_text",
    ]:
        require(snippet in test, f"test missing metrics snippet: {snippet}")

    for phrase in [
        "P3-06G 指标出口第一片",
        "只读指标出口",
        "不发送真实通知",
        "不执行真实外发",
        "Prometheus",
        "RBAC 收口第一片",
    ]:
        require(phrase in doc, f"documentation missing phrase: {phrase}")

    print("P3-06G ops metrics export checks passed.")


if __name__ == "__main__":
    main()
