from datetime import timedelta

from app.models import TrustedInboundWorkerRunRecord, WorkerHeartbeat, utc_now
from test_channel_connectors_api import _bootstrap_owner


def test_ops_alert_rules_dashboard_evaluates_worker_alerts(client, db_session) -> None:
    tenant, token = _bootstrap_owner(client, slug="ops-alert-rules", email="ops-alerts@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    now = utc_now()
    db_session.add_all(
        [
            WorkerHeartbeat(
                tenant_id=tenant["id"],
                worker_type="trusted_inbound_orchestrator",
                worker_id="stale-worker",
                status="running",
                last_heartbeat_at=now - timedelta(seconds=600),
                loops_completed=4,
            ),
            WorkerHeartbeat(
                tenant_id=tenant["id"],
                worker_type="trusted_inbound_orchestrator",
                worker_id="failed-worker",
                status="failed",
                last_heartbeat_at=now,
                last_error="fixture failure",
                loops_completed=2,
            ),
            TrustedInboundWorkerRunRecord(
                tenant_id=tenant["id"],
                worker_id="failed-worker",
                mode="model_assisted",
                status="failed",
                batch_size=20,
                rate_limit_per_minute=60,
                lease_seconds=60,
                scanned=2,
                processed=1,
                succeeded=0,
                failed=1,
                skipped=1,
                rate_limited=0,
                external_write=False,
                request_payload={"source": "fixture"},
                result_payload={"external_write": False},
                error_message="fixture run failure",
                started_at=now - timedelta(seconds=40),
                finished_at=now - timedelta(seconds=30),
            ),
        ]
    )
    db_session.commit()

    res = client.get(
        f"/api/tenants/{tenant['id']}/ops/alert-rules?stale_after_seconds=120&recent_run_limit=5",
        headers=headers,
    )

    assert res.status_code == 200
    payload = res.json()
    assert payload["tenant_id"] == tenant["id"]
    assert payload["notification_channel_enabled"] is False
    assert payload["notification_sent"] is False
    assert payload["external_call_performed"] is False
    assert payload["external_platform_write_performed"] is False
    rules = {rule["code"]: rule for rule in payload["rules"]}
    assert rules["trusted_inbound_worker_stale"]["status"] == "firing"
    assert rules["trusted_inbound_worker_stale"]["response_type"] == "ticket"
    assert "stale-worker" in rules["trusted_inbound_worker_stale"]["current_value"]
    assert rules["trusted_inbound_worker_failed"]["status"] == "firing"
    assert rules["trusted_inbound_worker_failed"]["response_type"] == "page"
    assert rules["trusted_inbound_recent_run_failed"]["status"] == "firing"
    assert rules["trusted_inbound_recent_run_failed"]["runbook"]["first_checks"]
    assert payload["firing_count"] >= 3
    assert payload["page_count"] >= 1


def test_ops_alert_rules_dashboard_reports_no_heartbeat(client) -> None:
    tenant, token = _bootstrap_owner(client, slug="ops-alert-no-heartbeat", email="ops-alert-no-heartbeat@example.com")

    res = client.get(
        f"/api/tenants/{tenant['id']}/ops/alert-rules",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert res.status_code == 200
    payload = res.json()
    rules = {rule["code"]: rule for rule in payload["rules"]}
    assert rules["worker_heartbeat_missing"]["status"] == "firing"
    assert rules["worker_heartbeat_missing"]["severity"] == "warning"
    assert "Docker Compose worker profile" in rules["worker_heartbeat_missing"]["runbook"]["first_checks"][0]
    assert payload["firing_count"] >= 1


def test_ops_alert_rules_dashboard_requires_same_tenant(client) -> None:
    tenant_a, token_a = _bootstrap_owner(client, slug="ops-alert-tenant-a", email="ops-alert-a@example.com")
    tenant_b, _ = _bootstrap_owner(client, slug="ops-alert-tenant-b", email="ops-alert-b@example.com")

    res = client.get(
        f"/api/tenants/{tenant_b['id']}/ops/alert-rules",
        headers={"Authorization": f"Bearer {token_a}"},
    )

    assert tenant_a["id"] != tenant_b["id"]
    assert res.status_code == 404
