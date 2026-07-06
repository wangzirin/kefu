from datetime import timedelta

from app.models import TrustedInboundWorkerRunRecord, WorkerHeartbeat, utc_now
from test_channel_connectors_api import _bootstrap_owner


def test_ops_worker_health_dashboard_summarizes_heartbeats_and_recent_runs(client, db_session) -> None:
    tenant, token = _bootstrap_owner(client, slug="ops-worker-health", email="ops-health@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    now = utc_now()
    db_session.add_all(
        [
            WorkerHeartbeat(
                tenant_id=tenant["id"],
                worker_type="trusted_inbound_orchestrator",
                worker_id="healthy-worker",
                status="idle",
                last_heartbeat_at=now,
                last_run_record_id=2,
                last_run_mode="model_assisted",
                loops_completed=12,
                metadata_payload={"last_summary": {"processed": 4, "external_write": False}},
            ),
            WorkerHeartbeat(
                tenant_id=tenant["id"],
                worker_type="trusted_inbound_orchestrator",
                worker_id="stale-worker",
                status="running",
                last_heartbeat_at=now - timedelta(seconds=600),
                loops_completed=3,
                metadata_payload={"last_summary": {"processed": 0, "external_write": False}},
            ),
            WorkerHeartbeat(
                tenant_id=tenant["id"],
                worker_type="trusted_inbound_orchestrator",
                worker_id="failed-worker",
                status="failed",
                last_heartbeat_at=now,
                last_error="fixture failure",
                loops_completed=5,
            ),
            TrustedInboundWorkerRunRecord(
                tenant_id=tenant["id"],
                worker_id="healthy-worker",
                mode="model_assisted",
                status="succeeded",
                batch_size=20,
                rate_limit_per_minute=60,
                lease_seconds=60,
                scanned=4,
                processed=4,
                succeeded=4,
                failed=0,
                skipped=0,
                rate_limited=0,
                external_write=False,
                request_payload={"source": "fixture"},
                result_payload={"external_write": False},
                started_at=now - timedelta(seconds=20),
                finished_at=now - timedelta(seconds=10),
            ),
        ]
    )
    db_session.commit()

    res = client.get(
        f"/api/tenants/{tenant['id']}/ops/worker-health?stale_after_seconds=120&recent_run_limit=5",
        headers=headers,
    )

    assert res.status_code == 200
    payload = res.json()
    assert payload["tenant_id"] == tenant["id"]
    assert payload["summary"]["total_workers"] == 3
    assert payload["summary"]["healthy_workers"] == 1
    assert payload["summary"]["stale_workers"] == 1
    assert payload["summary"]["failed_workers"] == 1
    assert payload["summary"]["external_write_enabled"] is False
    assert payload["summary"]["requires_attention"] is True
    assert [item["worker_id"] for item in payload["heartbeats"]] == [
        "failed-worker",
        "healthy-worker",
        "stale-worker",
    ]
    assert payload["recent_trusted_inbound_runs"][0]["worker_id"] == "healthy-worker"
    assert payload["recent_trusted_inbound_runs"][0]["external_write"] is False
    assert {risk["code"] for risk in payload["risks"]} >= {"worker_failed", "worker_stale"}
    assert payload["external_call_performed"] is False
    assert payload["external_platform_write_performed"] is False


def test_ops_worker_health_dashboard_reports_no_worker_as_attention(client) -> None:
    tenant, token = _bootstrap_owner(client, slug="ops-no-worker", email="ops-no-worker@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get(f"/api/tenants/{tenant['id']}/ops/worker-health", headers=headers)

    assert res.status_code == 200
    payload = res.json()
    assert payload["summary"]["total_workers"] == 0
    assert payload["summary"]["requires_attention"] is True
    assert payload["risks"][0]["code"] == "no_worker_heartbeat"
    assert payload["recent_trusted_inbound_runs"] == []


def test_ops_worker_health_dashboard_requires_same_tenant(client) -> None:
    owner_a, token_a = _bootstrap_owner(client, slug="ops-tenant-a", email="ops-a@example.com")
    owner_b, _ = _bootstrap_owner(client, slug="ops-tenant-b", email="ops-b@example.com")

    res = client.get(
        f"/api/tenants/{owner_b['id']}/ops/worker-health",
        headers={"Authorization": f"Bearer {token_a}"},
    )

    assert owner_a["id"] != owner_b["id"]
    assert res.status_code == 404
