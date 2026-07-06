from app.core.rbac import allowed_roles_for_permission, permissions_for_roles
from test_channel_connectors_api import _bootstrap_owner, _create_connector, _ready_outbox_draft
from test_outbox_api import _approved_review_task
from test_p3_06m_customer_ops_rbac import _create_user_with_role


def _auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_outbox_resource_permissions_matrix() -> None:
    assert allowed_roles_for_permission("outbox.draft.read") == ("admin", "agent", "owner")
    assert allowed_roles_for_permission("outbox.draft.manage") == ("admin", "agent", "owner")
    assert allowed_roles_for_permission("outbox.send_attempt.read") == ("admin", "agent", "owner")
    assert allowed_roles_for_permission("outbox.send_attempt.manage") == ("admin", "agent", "owner")
    assert allowed_roles_for_permission("outbox.send_plan.manage") == ("admin", "agent", "owner")
    assert allowed_roles_for_permission("outbox.delivery_job.read") == ("admin", "agent", "owner")
    assert allowed_roles_for_permission("outbox.delivery_job.manage") == ("admin", "owner")
    assert allowed_roles_for_permission("outbox.failure_review.read") == ("admin", "agent", "owner", "viewer")
    assert allowed_roles_for_permission("outbox.failure_review.manage") == ("admin", "agent", "owner")

    agent_permissions = permissions_for_roles(["agent"])
    assert "outbox.draft.manage" in agent_permissions
    assert "outbox.send_attempt.manage" in agent_permissions
    assert "outbox.send_plan.manage" in agent_permissions
    assert "outbox.delivery_job.read" in agent_permissions
    assert "outbox.delivery_job.manage" not in agent_permissions

    viewer_permissions = permissions_for_roles(["viewer"])
    assert "outbox.failure_review.read" in viewer_permissions
    assert "outbox.draft.read" not in viewer_permissions
    assert "outbox.send_attempt.read" not in viewer_permissions
    assert "outbox.delivery_job.read" not in viewer_permissions
    assert "outbox.failure_review.manage" not in viewer_permissions


def test_outbox_draft_and_dry_run_permissions(client) -> None:
    tenant, owner_token = _bootstrap_owner(
        client,
        slug="p3-06p-outbox-draft",
        email="p3-06p-outbox-owner@example.com",
    )
    owner_headers = _auth_header(owner_token)
    _agent, agent_headers = _create_user_with_role(
        client,
        tenant=tenant,
        owner_headers=owner_headers,
        role_code="agent",
        email="p3-06p-outbox-agent@example.com",
    )
    _viewer, viewer_headers = _create_user_with_role(
        client,
        tenant=tenant,
        owner_headers=owner_headers,
        role_code="viewer",
        email="p3-06p-outbox-viewer@example.com",
    )
    _conversation, _message, review = _approved_review_task(client, tenant["id"], owner_headers)

    viewer_create = client.post(
        f"/api/human-review-tasks/{review['id']}/outbox-drafts",
        headers=viewer_headers,
        json={},
    )
    assert viewer_create.status_code == 403
    assert viewer_create.json()["detail"] == "insufficient permission"

    agent_create = client.post(
        f"/api/human-review-tasks/{review['id']}/outbox-drafts",
        headers=agent_headers,
        json={},
    )
    assert agent_create.status_code == 201
    draft = agent_create.json()

    no_token_list = client.get(f"/api/tenants/{tenant['id']}/outbox-drafts")
    viewer_list = client.get(f"/api/tenants/{tenant['id']}/outbox-drafts", headers=viewer_headers)
    agent_list = client.get(f"/api/tenants/{tenant['id']}/outbox-drafts", headers=agent_headers)
    assert no_token_list.status_code == 401
    assert viewer_list.status_code == 403
    assert viewer_list.json()["detail"] == "insufficient permission"
    assert agent_list.status_code == 200
    assert [item["id"] for item in agent_list.json()] == [draft["id"]]

    viewer_confirm = client.post(
        f"/api/outbox-drafts/{draft['id']}/confirmation",
        headers=viewer_headers,
        json={"confirmation_note": "viewer 不应确认"},
    )
    assert viewer_confirm.status_code == 403

    agent_confirm = client.post(
        f"/api/outbox-drafts/{draft['id']}/confirmation",
        headers=agent_headers,
        json={"confirmation_note": "坐席确认进入待发送"},
    )
    assert agent_confirm.status_code == 200
    confirmed = agent_confirm.json()
    assert confirmed["status"] == "ready_to_send"

    viewer_attempts = client.get(f"/api/outbox-drafts/{draft['id']}/send-attempts", headers=viewer_headers)
    viewer_dry_run = client.post(
        f"/api/outbox-drafts/{draft['id']}/send-attempts",
        headers=viewer_headers,
        json={"delivery_mode": "dry_run"},
    )
    assert viewer_attempts.status_code == 403
    assert viewer_dry_run.status_code == 403

    agent_dry_run = client.post(
        f"/api/outbox-drafts/{draft['id']}/send-attempts",
        headers=agent_headers,
        json={"delivery_mode": "dry_run", "operator_note": "权限回归试发"},
    )
    assert agent_dry_run.status_code == 201
    assert agent_dry_run.json()["delivery_mode"] == "dry_run"


def test_delivery_job_queue_and_failure_review_permissions(client, db_session) -> None:
    from app.models import OutboxSendAttempt

    tenant, owner_token = _bootstrap_owner(
        client,
        slug="p3-06p-delivery-job",
        email="p3-06p-delivery-owner@example.com",
    )
    owner_headers = _auth_header(owner_token)
    _agent, agent_headers = _create_user_with_role(
        client,
        tenant=tenant,
        owner_headers=owner_headers,
        role_code="agent",
        email="p3-06p-delivery-agent@example.com",
    )
    _viewer, viewer_headers = _create_user_with_role(
        client,
        tenant=tenant,
        owner_headers=owner_headers,
        role_code="viewer",
        email="p3-06p-delivery-viewer@example.com",
    )
    channel, ready = _ready_outbox_draft(client, tenant["id"], owner_headers)
    _create_connector(client, channel["id"], owner_headers)

    agent_job = client.post(f"/api/outbox-drafts/{ready['id']}/delivery-jobs", headers=agent_headers, json={})
    assert agent_job.status_code == 403
    assert agent_job.json()["detail"] == "insufficient permission"

    owner_job = client.post(f"/api/outbox-drafts/{ready['id']}/delivery-jobs", headers=owner_headers, json={})
    assert owner_job.status_code == 201
    job = owner_job.json()

    viewer_jobs = client.get(f"/api/tenants/{tenant['id']}/outbox-delivery-jobs", headers=viewer_headers)
    agent_jobs = client.get(f"/api/tenants/{tenant['id']}/outbox-delivery-jobs", headers=agent_headers)
    assert viewer_jobs.status_code == 403
    assert agent_jobs.status_code == 200
    assert [item["id"] for item in agent_jobs.json()] == [job["id"]]

    agent_queue_run = client.post(
        f"/api/tenants/{tenant['id']}/outbox-delivery-queue-runs",
        headers=agent_headers,
        json={"batch_size": 10, "rate_limit_per_minute": 10},
    )
    assert agent_queue_run.status_code == 403

    owner_queue_run = client.post(
        f"/api/tenants/{tenant['id']}/outbox-delivery-queue-runs",
        headers=owner_headers,
        json={"batch_size": 10, "rate_limit_per_minute": 10},
    )
    assert owner_queue_run.status_code == 201

    plan_res = client.post(
        f"/api/outbox-drafts/{ready['id']}/connector-send-plans",
        headers=agent_headers,
        json={"operator_note": "坐席仍可生成受控发送计划"},
    )
    assert plan_res.status_code == 201
    attempt = db_session.get(OutboxSendAttempt, plan_res.json()["id"])
    attempt.external_message_id = "p3-06p-official-failed-001"
    db_session.commit()

    receipt_res = client.post(
        f"/api/channels/{channel['id']}/delivery-receipts",
        headers=owner_headers,
        json={
            "provider": "wecom",
            "external_message_id": "p3-06p-official-failed-001",
            "delivery_status": "failed",
            "provider_event_id": "p3-06p-receipt-001",
            "raw_payload": {"MsgID": "p3-06p-official-failed-001", "Status": "failed", "errcode": 45009},
        },
    )
    assert receipt_res.status_code == 201

    no_token_reviews = client.get(f"/api/tenants/{tenant['id']}/delivery-failure-reviews")
    viewer_reviews = client.get(f"/api/tenants/{tenant['id']}/delivery-failure-reviews", headers=viewer_headers)
    assert no_token_reviews.status_code == 401
    assert viewer_reviews.status_code == 200
    [review] = viewer_reviews.json()
    assert review["provider_error_code"] == "45009"

    viewer_resolve = client.patch(
        f"/api/delivery-failure-reviews/{review['id']}",
        headers=viewer_headers,
        json={"status": "resolved", "resolution_note": "viewer 不应处理"},
    )
    assert viewer_resolve.status_code == 403

    agent_resolve = client.patch(
        f"/api/delivery-failure-reviews/{review['id']}",
        headers=agent_headers,
        json={"status": "resolved", "resolution_note": "坐席完成失败复盘"},
    )
    assert agent_resolve.status_code == 200
    assert agent_resolve.json()["resolved_by_id"] is not None
