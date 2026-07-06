from datetime import timedelta

from app.models import (
    ChannelDeliveryReceipt,
    DeliveryFailureReview,
    OutboxDeliveryJob,
    TrustedInboundWorkerRunRecord,
    WorkerHeartbeat,
    utc_now,
)
from test_channel_connectors_api import _bootstrap_owner, _create_connector, _ready_outbox_draft


def _metric(payload: dict, name: str, **labels: str) -> dict:
    for item in payload["metrics"]:
        if item["name"] != name:
            continue
        if all(item["labels"].get(key) == value for key, value in labels.items()):
            return item
    raise AssertionError(f"metric not found: {name} {labels}")


def test_ops_metrics_dashboard_exports_worker_queue_and_alert_metrics(client, db_session) -> None:
    tenant, token = _bootstrap_owner(client, slug="ops-metrics", email="ops-metrics@example.com")
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
                loops_completed=12,
            ),
            WorkerHeartbeat(
                tenant_id=tenant["id"],
                worker_type="trusted_inbound_orchestrator",
                worker_id="failed-worker",
                status="failed",
                last_heartbeat_at=now - timedelta(seconds=20),
                last_error="fixture failed heartbeat",
                loops_completed=3,
            ),
            TrustedInboundWorkerRunRecord(
                tenant_id=tenant["id"],
                worker_id="failed-worker",
                mode="model_assisted",
                status="failed",
                batch_size=20,
                rate_limit_per_minute=60,
                lease_seconds=60,
                scanned=3,
                processed=2,
                succeeded=1,
                failed=1,
                skipped=0,
                rate_limited=2,
                external_write=False,
                request_payload={"source": "fixture"},
                result_payload={"external_write": False},
                error_message="fixture run failure",
                started_at=now - timedelta(seconds=30),
                finished_at=now - timedelta(seconds=10),
            ),
        ]
    )
    db_session.commit()

    channel, ready = _ready_outbox_draft(client, tenant["id"], headers)
    _create_connector(client, channel["id"], headers)
    job_res = client.post(
        f"/api/outbox-drafts/{ready['id']}/delivery-jobs",
        headers=headers,
        json={"external_write_requested": True},
    )
    assert job_res.status_code == 201
    job = db_session.get(OutboxDeliveryJob, job_res.json()["id"])
    job.status = "dead_letter"
    job.dead_letter_reason = "fixture dead letter"

    receipt = ChannelDeliveryReceipt(
        tenant_id=tenant["id"],
        channel_id=channel["id"],
        provider="wecom",
        delivery_status="failed",
        normalized_status="failed",
        needs_review=True,
        raw_payload={"fixture": True},
    )
    db_session.add(receipt)
    db_session.flush()
    db_session.add(
        DeliveryFailureReview(
            tenant_id=tenant["id"],
            channel_id=channel["id"],
            receipt_id=receipt.id,
            provider="wecom",
            normalized_status="failed",
            severity="warning",
            review_reason="fixture_delivery_failure",
            next_action="manual_review_provider_status",
            status="open",
        )
    )
    db_session.commit()

    res = client.get(
        f"/api/tenants/{tenant['id']}/ops/metrics?stale_after_seconds=120&recent_run_limit=5",
        headers=headers,
    )

    assert res.status_code == 200
    payload = res.json()
    assert payload["tenant_id"] == tenant["id"]
    assert payload["collection_model"] == "pull_json_or_prometheus_text_preview"
    assert payload["scrape_path"] == f"/api/tenants/{tenant['id']}/ops/metrics"
    assert payload["summary"]["dead_letter_jobs"] == 1
    assert payload["summary"]["failed_worker_runs"] == 1
    assert payload["summary"]["open_failure_reviews"] == 1
    assert payload["summary"]["external_write_enabled"] is False
    assert payload["external_call_performed"] is False
    assert payload["external_platform_write_performed"] is False

    assert _metric(payload, "wanfa_worker_failed")["value"] == 1
    assert _metric(payload, "wanfa_ops_alert_rules_page")["value"] >= 1
    assert _metric(payload, "wanfa_trusted_inbound_runs_rate_limited_recent")["value"] == 2
    dead_letter = _metric(payload, "wanfa_outbox_delivery_jobs", status="dead_letter")
    assert dead_letter["value"] == 1
    assert dead_letter["status"] == "critical"
    open_reviews = _metric(payload, "wanfa_delivery_failure_reviews", status="open")
    assert open_reviews["value"] == 1
    assert open_reviews["status"] == "warning"
    assert "# HELP wanfa_worker_failed" in payload["prometheus_text"]
    assert 'wanfa_outbox_delivery_jobs{status="dead_letter"' in payload["prometheus_text"]


def test_ops_metrics_dashboard_requires_same_tenant(client) -> None:
    tenant_a, token_a = _bootstrap_owner(client, slug="ops-metrics-a", email="ops-metrics-a@example.com")
    tenant_b, _ = _bootstrap_owner(client, slug="ops-metrics-b", email="ops-metrics-b@example.com")

    res = client.get(
        f"/api/tenants/{tenant_b['id']}/ops/metrics",
        headers={"Authorization": f"Bearer {token_a}"},
    )

    assert tenant_a["id"] != tenant_b["id"]
    assert res.status_code == 404
