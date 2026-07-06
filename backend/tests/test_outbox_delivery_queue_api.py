from datetime import timedelta

from app.models import OutboxDeliveryJob
from app.models.foundation import utc_now
from test_channel_connectors_api import _bootstrap_owner, _create_connector, _ready_outbox_draft


def _ready_job(
    client,
    *,
    slug: str,
    email: str,
    db_session=None,
    channel_status: str = "active",
    external_write_requested: bool = False,
):
    tenant, token = _bootstrap_owner(client, slug=slug, email=email)
    headers = {"Authorization": f"Bearer {token}"}
    channel, ready = _ready_outbox_draft(client, tenant["id"], headers)
    if channel_status != "active":
        from app.models import Channel

        assert db_session is not None
        channel_row = db_session.get(Channel, channel["id"])
        channel_row.status = channel_status
        db_session.commit()
        channel["status"] = channel_status
    _create_connector(client, channel["id"], headers)
    job_res = client.post(
        f"/api/outbox-drafts/{ready['id']}/delivery-jobs",
        headers=headers,
        json={"external_write_requested": external_write_requested},
    )
    assert job_res.status_code == 201
    return tenant, headers, channel, ready, job_res.json()


def test_delivery_queue_creates_single_job_and_repeated_runs_do_not_duplicate_attempts(client) -> None:
    tenant, headers, _, ready, job = _ready_job(
        client,
        slug="delivery-queue-idempotent",
        email="delivery-queue-idempotent@example.com",
    )

    duplicate_res = client.post(
        f"/api/outbox-drafts/{ready['id']}/delivery-jobs",
        headers=headers,
        json={},
    )
    assert duplicate_res.status_code == 409
    assert "delivery job already exists" in duplicate_res.json()["detail"]

    run_res = client.post(
        f"/api/tenants/{tenant['id']}/outbox-delivery-queue-runs",
        headers=headers,
        json={"batch_size": 10, "rate_limit_per_minute": 10},
    )
    assert run_res.status_code == 201
    first_run = run_res.json()
    assert first_run["mode"] == "delivery_queue_skeleton"
    assert first_run["processed"] == 1
    assert first_run["succeeded"] == 1
    assert first_run["external_write"] is False
    assert first_run["kill_switch"]["global_external_write_enabled"] is False
    [attempt] = first_run["attempts"]
    assert attempt["outbox_draft_id"] == ready["id"]
    assert attempt["delivery_mode"] == "delivery_queue"
    assert attempt["provider"] == "wecom"
    assert attempt["status"] == "succeeded"
    assert attempt["delivery_status"] == "not_sent"
    assert attempt["request_payload"]["external_write"] is False
    assert attempt["response_payload"]["queue_job_id"] == job["id"]

    second_res = client.post(
        f"/api/tenants/{tenant['id']}/outbox-delivery-queue-runs",
        headers=headers,
        json={"batch_size": 10, "rate_limit_per_minute": 10},
    )
    assert second_res.status_code == 201
    second_run = second_res.json()
    assert second_run["processed"] == 0
    assert second_run["skipped_job_ids"] == []

    attempts_res = client.get(f"/api/outbox-drafts/{ready['id']}/send-attempts", headers=headers)
    assert attempts_res.status_code == 200
    attempts = [item for item in attempts_res.json() if item["delivery_mode"] == "delivery_queue"]
    assert len(attempts) == 1


def test_delivery_queue_kill_switch_blocks_external_write_requested_job_and_creates_review(client) -> None:
    tenant, headers, _, _, job = _ready_job(
        client,
        slug="delivery-queue-kill-switch",
        email="delivery-queue-kill-switch@example.com",
        external_write_requested=True,
    )

    run_res = client.post(
        f"/api/tenants/{tenant['id']}/outbox-delivery-queue-runs",
        headers=headers,
        json={"batch_size": 10, "rate_limit_per_minute": 10},
    )
    assert run_res.status_code == 201
    run = run_res.json()
    assert run["processed"] == 1
    assert run["blocked"] == 1
    assert run["external_write"] is False
    assert run["jobs"][0]["id"] == job["id"]
    assert run["jobs"][0]["status"] == "blocked"
    assert run["attempts"][0]["status"] == "blocked"
    assert run["attempts"][0]["response_payload"]["blocked_reason"] == "external_write_kill_switch"

    reviews_res = client.get(f"/api/tenants/{tenant['id']}/delivery-failure-reviews", headers=headers)
    assert reviews_res.status_code == 200
    [review] = reviews_res.json()
    assert review["normalized_status"] == "permission_denied"
    assert review["provider_error_code"] == "external_write_kill_switch"
    assert review["next_action"] == "check_provider_scope_or_service_market_permission"


def test_delivery_queue_rate_limit_leaves_due_job_unprocessed_without_attempt(client) -> None:
    tenant, token = _bootstrap_owner(
        client,
        slug="delivery-queue-rate-limit",
        email="delivery-queue-rate-limit@example.com",
    )
    headers = {"Authorization": f"Bearer {token}"}
    first_channel, first_ready = _ready_outbox_draft(client, tenant["id"], headers)
    second_channel, second_ready = _ready_outbox_draft(client, tenant["id"], headers)
    _create_connector(client, first_channel["id"], headers)
    _create_connector(client, second_channel["id"], headers)
    first_job_res = client.post(f"/api/outbox-drafts/{first_ready['id']}/delivery-jobs", headers=headers, json={})
    second_job_res = client.post(f"/api/outbox-drafts/{second_ready['id']}/delivery-jobs", headers=headers, json={})
    assert first_job_res.status_code == 201
    assert second_job_res.status_code == 201
    first_job = first_job_res.json()
    second_job = second_job_res.json()

    run_res = client.post(
        f"/api/tenants/{tenant['id']}/outbox-delivery-queue-runs",
        headers=headers,
        json={"batch_size": 10, "rate_limit_per_minute": 1},
    )

    assert run_res.status_code == 201
    run = run_res.json()
    assert run["processed"] == 1
    assert run["rate_limited"] == 1
    assert run["rate_limited_job_ids"] == [second_job["id"]]
    assert run["jobs"][0]["id"] == first_job["id"]


def test_delivery_queue_skips_fresh_lock_and_reclaims_stale_lock(client, db_session) -> None:
    tenant, token = _bootstrap_owner(
        client,
        slug="delivery-queue-lease",
        email="delivery-queue-lease@example.com",
    )
    headers = {"Authorization": f"Bearer {token}"}
    first_channel, first_ready = _ready_outbox_draft(client, tenant["id"], headers)
    second_channel, second_ready = _ready_outbox_draft(client, tenant["id"], headers)
    _create_connector(client, first_channel["id"], headers)
    _create_connector(client, second_channel["id"], headers)
    first_job_res = client.post(f"/api/outbox-drafts/{first_ready['id']}/delivery-jobs", headers=headers, json={})
    second_job_res = client.post(f"/api/outbox-drafts/{second_ready['id']}/delivery-jobs", headers=headers, json={})
    assert first_job_res.status_code == 201
    assert second_job_res.status_code == 201
    first_job = first_job_res.json()
    second_job = second_job_res.json()

    now = utc_now()
    fresh_locked = db_session.get(OutboxDeliveryJob, first_job["id"])
    stale_locked = db_session.get(OutboxDeliveryJob, second_job["id"])
    assert fresh_locked is not None
    assert stale_locked is not None
    fresh_locked.status = "locked"
    fresh_locked.locked_by = "another-live-worker"
    fresh_locked.locked_at = now
    stale_locked.status = "locked"
    stale_locked.locked_by = "dead-worker"
    stale_locked.locked_at = now - timedelta(seconds=120)
    db_session.commit()

    run_res = client.post(
        f"/api/tenants/{tenant['id']}/outbox-delivery-queue-runs",
        headers=headers,
        json={
            "batch_size": 10,
            "rate_limit_per_minute": 10,
            "lease_seconds": 30,
            "worker_id": "lease-test-worker",
        },
    )
    assert run_res.status_code == 201
    run = run_res.json()
    assert run["processed"] == 1
    assert run["succeeded"] == 1
    assert run["skipped_job_ids"] == [first_job["id"]]
    assert run["jobs"][0]["id"] == second_job["id"]
    assert run["jobs"][0]["locked_by"] == ""
    assert run["kill_switch"]["lease"]["worker_id"] == "lease-test-worker"
    assert run["kill_switch"]["lease"]["lease_seconds"] == 30
    assert run["kill_switch"]["lease"]["active_locked_skipped"] == 1
    assert run["attempts"][0]["request_payload"]["worker_id"] == "lease-test-worker"

    db_session.expire_all()
    fresh_locked_after = db_session.get(OutboxDeliveryJob, first_job["id"])
    stale_locked_after = db_session.get(OutboxDeliveryJob, second_job["id"])
    assert fresh_locked_after is not None
    assert stale_locked_after is not None
    assert fresh_locked_after.status == "locked"
    assert fresh_locked_after.locked_by == "another-live-worker"
    assert stale_locked_after.status == "succeeded"


def test_delivery_queue_retries_then_dead_letters_channel_failure(client, db_session) -> None:
    tenant, headers, _, _, job = _ready_job(
        client,
        slug="delivery-queue-dead-letter",
        email="delivery-queue-dead-letter@example.com",
        db_session=db_session,
        channel_status="paused",
    )

    first_res = client.post(
        f"/api/tenants/{tenant['id']}/outbox-delivery-queue-runs",
        headers=headers,
        json={"batch_size": 10, "rate_limit_per_minute": 10, "max_attempts": 2},
    )
    assert first_res.status_code == 201
    first = first_res.json()
    assert first["processed"] == 1
    assert first["retry_scheduled"] == 1
    assert first["jobs"][0]["status"] == "retry_scheduled"
    assert first["jobs"][0]["attempts_count"] == 1

    second_res = client.post(
        f"/api/tenants/{tenant['id']}/outbox-delivery-queue-runs",
        headers=headers,
        json={"batch_size": 10, "rate_limit_per_minute": 10, "max_attempts": 2},
    )
    assert second_res.status_code == 201
    second = second_res.json()
    assert second["processed"] == 1
    assert second["dead_lettered"] == 1
    assert second["jobs"][0]["id"] == job["id"]
    assert second["jobs"][0]["status"] == "dead_letter"
    assert second["jobs"][0]["dead_letter_reason"] == "channel_not_active"

    reviews_res = client.get(f"/api/tenants/{tenant['id']}/delivery-failure-reviews", headers=headers)
    assert reviews_res.status_code == 200
    [review] = reviews_res.json()
    assert review["normalized_status"] == "failed"
    assert review["review_reason"] == "provider_failed_without_known_code"
