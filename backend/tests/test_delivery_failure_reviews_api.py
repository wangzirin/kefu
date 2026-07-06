from test_channel_connectors_api import _bootstrap_owner, _create_connector, _ready_outbox_draft


def _ready_channel_and_plan(client, tenant_id: int, headers: dict) -> tuple[dict, dict, dict]:
    channel, ready = _ready_outbox_draft(client, tenant_id, headers)
    _create_connector(client, channel["id"], headers)
    plan_res = client.post(
        f"/api/outbox-drafts/{ready['id']}/connector-send-plans",
        headers=headers,
        json={},
    )
    assert plan_res.status_code == 201
    return channel, ready, plan_res.json()


def test_failed_platform_receipt_is_normalized_and_enters_failure_review_queue(client, db_session) -> None:
    from app.models import OutboxSendAttempt

    tenant, token = _bootstrap_owner(
        client,
        slug="delivery-review-rate-limit",
        email="delivery-review-rate-limit@example.com",
    )
    headers = {"Authorization": f"Bearer {token}"}
    channel, ready, plan = _ready_channel_and_plan(client, tenant["id"], headers)

    attempt = db_session.get(OutboxSendAttempt, plan["id"])
    attempt.external_message_id = "official-message-rate-limit-001"
    db_session.commit()

    receipt_res = client.post(
        f"/api/channels/{channel['id']}/delivery-receipts",
        headers=headers,
        json={
            "provider": "wecom",
            "external_message_id": "official-message-rate-limit-001",
            "delivery_status": "failed",
            "provider_event_id": "receipt-rate-limit-001",
            "raw_payload": {
                "MsgID": "official-message-rate-limit-001",
                "Status": "failed",
                "errcode": 45009,
                "errmsg": "api freq out of limit",
            },
        },
    )

    assert receipt_res.status_code == 201
    receipt = receipt_res.json()
    assert receipt["matched_attempt_id"] == plan["id"]
    assert receipt["provider_status"] == "failed"
    assert receipt["provider_error_code"] == "45009"
    assert receipt["normalized_status"] == "rate_limited"
    assert receipt["retryable"] is True
    assert receipt["needs_review"] is True
    assert receipt["next_action"] == "retry_later"

    queue_res = client.get(f"/api/tenants/{tenant['id']}/delivery-failure-reviews", headers=headers)
    assert queue_res.status_code == 200
    [item] = queue_res.json()
    assert item["tenant_id"] == tenant["id"]
    assert item["channel_id"] == channel["id"]
    assert item["receipt_id"] == receipt["id"]
    assert item["matched_attempt_id"] == plan["id"]
    assert item["outbox_draft_id"] == ready["id"]
    assert item["provider"] == "wecom"
    assert item["external_message_id"] == "official-message-rate-limit-001"
    assert item["provider_error_code"] == "45009"
    assert item["normalized_status"] == "rate_limited"
    assert item["review_reason"] == "provider_rate_limited"
    assert item["retryable"] is True
    assert item["next_action"] == "retry_later"
    assert item["status"] == "open"

    resolved_res = client.patch(
        f"/api/delivery-failure-reviews/{item['id']}",
        headers=headers,
        json={"status": "resolved", "resolution_note": "已确认限流，等待队列重试"},
    )
    assert resolved_res.status_code == 200
    resolved = resolved_res.json()
    assert resolved["status"] == "resolved"
    assert resolved["resolved_by_id"] is not None
    assert resolved["resolution_note"] == "已确认限流，等待队列重试"
    assert resolved["resolved_at"] is not None

    open_res = client.get(f"/api/tenants/{tenant['id']}/delivery-failure-reviews?status=open", headers=headers)
    assert open_res.status_code == 200
    assert open_res.json() == []


def test_successful_platform_receipt_is_normalized_without_failure_review(client) -> None:
    tenant, token = _bootstrap_owner(
        client,
        slug="delivery-review-success",
        email="delivery-review-success@example.com",
    )
    headers = {"Authorization": f"Bearer {token}"}
    channel, _, _ = _ready_channel_and_plan(client, tenant["id"], headers)

    receipt_res = client.post(
        f"/api/channels/{channel['id']}/delivery-receipts",
        headers=headers,
        json={
            "provider": "wecom",
            "external_message_id": "official-message-delivered-001",
            "delivery_status": "delivered",
            "provider_event_id": "receipt-delivered-001",
            "raw_payload": {"MsgID": "official-message-delivered-001", "Status": "delivered"},
        },
    )

    assert receipt_res.status_code == 201
    receipt = receipt_res.json()
    assert receipt["normalized_status"] == "delivered"
    assert receipt["retryable"] is False
    assert receipt["needs_review"] is False
    assert receipt["next_action"] == "none"

    queue_res = client.get(f"/api/tenants/{tenant['id']}/delivery-failure-reviews", headers=headers)
    assert queue_res.status_code == 200
    assert queue_res.json() == []


def test_unknown_provider_receipt_status_enters_manual_review_queue(client) -> None:
    tenant, token = _bootstrap_owner(
        client,
        slug="delivery-review-unknown",
        email="delivery-review-unknown@example.com",
    )
    headers = {"Authorization": f"Bearer {token}"}
    channel, _, _ = _ready_channel_and_plan(client, tenant["id"], headers)

    receipt_res = client.post(
        f"/api/channels/{channel['id']}/delivery-receipts",
        headers=headers,
        json={
            "provider": "wecom",
            "external_message_id": "official-message-unknown-001",
            "delivery_status": "provider_new_state",
            "provider_event_id": "receipt-unknown-001",
            "raw_payload": {"MsgID": "official-message-unknown-001", "Status": "provider_new_state"},
        },
    )

    assert receipt_res.status_code == 201
    receipt = receipt_res.json()
    assert receipt["normalized_status"] == "unknown_provider_status"
    assert receipt["retryable"] is False
    assert receipt["needs_review"] is True
    assert receipt["next_action"] == "manual_review_provider_status"

    queue_res = client.get(f"/api/tenants/{tenant['id']}/delivery-failure-reviews", headers=headers)
    assert queue_res.status_code == 200
    [item] = queue_res.json()
    assert item["provider_status"] == "provider_new_state"
    assert item["normalized_status"] == "unknown_provider_status"
    assert item["review_reason"] == "unknown_provider_status"
    assert item["next_action"] == "manual_review_provider_status"
