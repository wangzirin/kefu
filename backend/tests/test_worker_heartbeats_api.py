from datetime import timedelta

from app.models import TrustedInboundMessageJob, WorkerHeartbeat, WorkflowRun, utc_now
from test_channel_connectors_api import _bootstrap_owner, _create_connector
from test_trusted_inbound_worker_api import (
    _create_active_knowledge_card,
    _create_wecom_channel,
    _post_verified_trusted_wecom_message,
)


def test_worker_heartbeat_health_marks_healthy_stale_and_failed(client, db_session) -> None:
    tenant, token = _bootstrap_owner(client, slug="worker-heartbeats", email="heartbeats@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    now = utc_now()
    db_session.add_all(
        [
            WorkerHeartbeat(
                tenant_id=tenant["id"],
                worker_type="trusted_inbound_orchestrator",
                worker_id="live-worker",
                status="idle",
                last_heartbeat_at=now,
                loops_completed=3,
            ),
            WorkerHeartbeat(
                tenant_id=tenant["id"],
                worker_type="trusted_inbound_orchestrator",
                worker_id="stale-worker",
                status="running",
                last_heartbeat_at=now - timedelta(seconds=120),
            ),
            WorkerHeartbeat(
                tenant_id=tenant["id"],
                worker_type="trusted_inbound_orchestrator",
                worker_id="failed-worker",
                status="failed",
                last_heartbeat_at=now,
                last_error="synthetic failure",
            ),
        ]
    )
    db_session.commit()

    res = client.get(
        f"/api/tenants/{tenant['id']}/worker-heartbeats?stale_after_seconds=60",
        headers=headers,
    )

    assert res.status_code == 200
    by_worker = {item["worker_id"]: item for item in res.json()}
    assert by_worker["live-worker"]["status"] == "idle"
    assert by_worker["live-worker"]["health_status"] == "healthy"
    assert by_worker["live-worker"]["loops_completed"] == 3
    assert by_worker["stale-worker"]["status"] == "running"
    assert by_worker["stale-worker"]["health_status"] == "stale"
    assert by_worker["failed-worker"]["status"] == "failed"
    assert by_worker["failed-worker"]["health_status"] == "failed"
    assert by_worker["failed-worker"]["last_error"] == "synthetic failure"


def test_trusted_inbound_worker_loop_writes_heartbeat_and_runs_once(client, db_session) -> None:
    tenant, token = _bootstrap_owner(client, slug="trusted-loop", email="trusted-loop@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    channel = _create_wecom_channel(client, tenant["id"])
    _create_connector(
        client,
        channel["id"],
        headers,
        public_config={
            "corp_id_placeholder": "fixture_only",
            "credential_ref": "p2_13_wecom_fixture",
        },
    )
    _create_active_knowledge_card(client, tenant["id"], headers)
    webhook_event = _post_verified_trusted_wecom_message(client, channel["id"], external_id="loop-message-001")
    message_id = webhook_event["parsed_event"]["trusted_message_id"]

    res = client.post(
        f"/api/tenants/{tenant['id']}/trusted-inbound-worker-loop-runs",
        headers=headers,
        json={
            "iterations": 1,
            "sleep_seconds": 0,
            "batch_size": 5,
            "rate_limit_per_minute": 60,
            "worker_id": "trusted-loop-worker-1",
            "lease_seconds": 30,
        },
    )

    assert res.status_code == 201
    payload = res.json()
    assert payload["tenant_id"] == tenant["id"]
    assert payload["worker_id"] == "trusted-loop-worker-1"
    assert payload["worker_type"] == "trusted_inbound_orchestrator"
    assert payload["iterations_requested"] == 1
    assert payload["iterations_completed"] == 1
    assert payload["failed_iterations"] == 0
    assert payload["total_processed"] == 1
    assert payload["total_succeeded"] == 1
    assert payload["external_write"] is False
    assert payload["run_record_ids"]
    assert payload["heartbeat"]["status"] == "idle"
    assert payload["heartbeat"]["health_status"] == "healthy"
    assert payload["heartbeat"]["loops_completed"] == 1
    assert payload["heartbeat"]["last_run_record_id"] == payload["run_record_ids"][-1]

    job = db_session.query(TrustedInboundMessageJob).filter_by(message_id=message_id).one()
    assert job.status == "succeeded"
    assert job.locked_by == "trusted-loop-worker-1"

    heartbeats = client.get(f"/api/tenants/{tenant['id']}/worker-heartbeats", headers=headers).json()
    assert [item["worker_id"] for item in heartbeats] == ["trusted-loop-worker-1"]


def test_two_trusted_inbound_worker_loops_do_not_duplicate_claims(client, db_session) -> None:
    tenant, token = _bootstrap_owner(client, slug="trusted-loop-two-workers", email="trusted-loop-two@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    channel = _create_wecom_channel(client, tenant["id"])
    _create_connector(
        client,
        channel["id"],
        headers,
        public_config={
            "corp_id_placeholder": "fixture_only",
            "credential_ref": "p2_13_wecom_fixture",
        },
    )
    _create_active_knowledge_card(client, tenant["id"], headers)
    first = _post_verified_trusted_wecom_message(client, channel["id"], external_id="loop-two-worker-001")
    second = _post_verified_trusted_wecom_message(client, channel["id"], external_id="loop-two-worker-002")
    message_ids = {
        first["parsed_event"]["trusted_message_id"],
        second["parsed_event"]["trusted_message_id"],
    }

    first_res = client.post(
        f"/api/tenants/{tenant['id']}/trusted-inbound-worker-loop-runs",
        headers=headers,
        json={
            "iterations": 1,
            "sleep_seconds": 0,
            "batch_size": 1,
            "rate_limit_per_minute": 60,
            "worker_id": "trusted-loop-worker-a",
            "lease_seconds": 30,
        },
    )
    second_res = client.post(
        f"/api/tenants/{tenant['id']}/trusted-inbound-worker-loop-runs",
        headers=headers,
        json={
            "iterations": 1,
            "sleep_seconds": 0,
            "batch_size": 5,
            "rate_limit_per_minute": 60,
            "worker_id": "trusted-loop-worker-b",
            "lease_seconds": 30,
        },
    )

    assert first_res.status_code == 201
    assert second_res.status_code == 201
    assert first_res.json()["total_processed"] == 1
    assert second_res.json()["total_processed"] == 1

    runs = db_session.query(WorkflowRun).filter(WorkflowRun.trigger_message_id.in_(message_ids)).all()
    assert len(runs) == 2
    assert {run.trigger_message_id for run in runs} == message_ids

    heartbeats = client.get(f"/api/tenants/{tenant['id']}/worker-heartbeats", headers=headers).json()
    by_worker = {item["worker_id"]: item for item in heartbeats}
    assert by_worker["trusted-loop-worker-a"]["loops_completed"] == 1
    assert by_worker["trusted-loop-worker-b"]["loops_completed"] == 1
    assert all(item["health_status"] == "healthy" for item in by_worker.values())
