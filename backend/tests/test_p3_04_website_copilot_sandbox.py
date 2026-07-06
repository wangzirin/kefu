import hashlib
import hmac
import json
import time

from test_channel_connectors_api import _bootstrap_owner, _create_connector


def _fresh_timestamp() -> str:
    return str(int(time.time()))


def _website_hmac_signature(secret: str, *, timestamp: str, nonce: str, raw_payload: dict) -> str:
    canonical_payload = json.dumps(raw_payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    signing_base = f"{timestamp}\n{nonce}\n{canonical_payload}".encode("utf-8")
    return hmac.new(secret.encode("utf-8"), signing_base, hashlib.sha256).hexdigest()


def _create_website_channel(client, tenant_id: int) -> dict:
    res = client.post(
        f"/api/tenants/{tenant_id}/channels",
        json={"type": "website", "name": "官网客服沙盒", "reply_mode": "assist", "status": "active"},
    )
    assert res.status_code == 201
    return res.json()


def _create_website_connector(client, channel_id: int, headers: dict) -> dict:
    return _create_connector(
        client,
        channel_id,
        headers,
        provider="website",
        display_name="官网客服沙盒组件",
        capabilities=["receive_message", "delivery_receipt", "sandbox_send_plan"],
        public_config={
            "site_id_placeholder": "p3_04_website_sandbox",
            "credential_ref": "p2_13_website_fixture",
            "external_write": "disabled",
        },
        webhook_path=f"/api/webhooks/website/channels/{channel_id}",
        signature_mode="website_hmac_sha256",
    )


def _create_active_knowledge_card(client, tenant_id: int, headers: dict) -> dict:
    res = client.post(
        f"/api/tenants/{tenant_id}/knowledge-cards",
        headers=headers,
        json={
            "title": "官网客服试点上线周期",
            "question": "官网客服试点上线周期多久，需要准备什么资料？",
            "answer": "官网客服试点通常需要 1-2 周。启动前需要提供产品资料、售后政策、常见问题、人工接待规则和可用的官网接入位置。",
            "tags": ["官网客服", "试点上线", "交付周期", "资料准备"],
            "aliases": ["官网客服试点", "试点上线周期", "需要准备什么资料"],
            "status": "active",
            "source_type": "internal_policy",
            "source_uri": "internal://p3-04/website-sandbox-onboarding",
        },
    )
    assert res.status_code == 201
    return res.json()


def _post_website_webhook(client, channel_id: int, *, raw_payload: dict, provider_event_id: str, signature: str, nonce: str):
    timestamp = _fresh_timestamp()
    return client.post(
        f"/api/webhooks/website/channels/{channel_id}?signature={signature}&timestamp={timestamp}&nonce={nonce}",
        json={
            "event_type": "message",
            "delivery_status": "received",
            "provider_event_id": provider_event_id,
            "raw_payload": raw_payload,
        },
    )


def test_p3_04_website_sandbox_copilot_loop_is_gated_and_auditable(client) -> None:
    tenant, token = _bootstrap_owner(
        client,
        slug="p3-04-website-sandbox",
        email="p3-04-website-sandbox@example.com",
    )
    headers = {"Authorization": f"Bearer {token}"}
    channel = _create_website_channel(client, tenant["id"])
    connector = _create_website_connector(client, channel["id"], headers)
    assert connector["provider"] == "website"
    assert connector["secret_status"] == "fixture_configured"
    assert connector["external_write_enabled"] is False

    invalid_payload = {
        "message_id": "website-sandbox-invalid-001",
        "visitor_id": "visitor-invalid-001",
        "visitor_name": "错签访客",
        "text": "这条错签消息不能进入客服消息流",
    }
    invalid_res = _post_website_webhook(
        client,
        channel["id"],
        raw_payload=invalid_payload,
        provider_event_id="website-sandbox-invalid-event-001",
        signature="bad-signature",
        nonce="nonce-invalid-001",
    )
    assert invalid_res.status_code == 202
    invalid_event = invalid_res.json()
    assert invalid_event["verification_status"] == "signature_invalid"
    assert invalid_event["signature_validated"] is False
    assert invalid_event["parsed_event"]["trusted_message_creation"] is False
    assert client.get(
        f"/api/tenants/{tenant['id']}/conversations?channel_id={channel['id']}",
        headers=headers,
    ).json() == []

    trusted_payload = {
        "message_id": "website-sandbox-message-001",
        "visitor_id": "visitor-p3-04-001",
        "visitor_name": "官网试点访客",
        "text": "官网客服试点上线周期多久，需要准备什么资料？",
    }
    timestamp = _fresh_timestamp()
    nonce = "nonce-valid-001"
    signature = _website_hmac_signature(
        "p2_13_website_signing_secret",
        timestamp=timestamp,
        nonce=nonce,
        raw_payload=trusted_payload,
    )
    valid_url = (
        f"/api/webhooks/website/channels/{channel['id']}?"
        f"signature={signature}&timestamp={timestamp}&nonce={nonce}"
    )
    webhook_body = {
        "event_type": "message",
        "delivery_status": "received",
        "provider_event_id": "website-sandbox-event-001",
        "raw_payload": trusted_payload,
    }
    valid_res = client.post(valid_url, json=webhook_body)
    assert valid_res.status_code == 202
    valid_event = valid_res.json()
    assert valid_event["verification_status"] == "signature_validated"
    assert valid_event["signature_validated"] is True
    assert valid_event["external_write"] is False
    assert valid_event["parsed_event"]["status"] == "trusted_inbound_message_created"
    assert valid_event["parsed_event"]["trusted_message_creation"] is True
    assert valid_event["parsed_event"]["idempotency_status"] == "created"
    assert valid_event["next_action"] == "queue_trusted_inbound_message_for_reply_orchestration"
    trusted_message_id = valid_event["parsed_event"]["trusted_message_id"]
    conversation_id = valid_event["parsed_event"]["conversation_id"]

    replay_res = client.post(valid_url, json=webhook_body)
    assert replay_res.status_code == 202
    replay_event = replay_res.json()
    assert replay_event["parsed_event"]["status"] == "duplicate_ignored"
    assert replay_event["parsed_event"]["trusted_message_creation"] is False
    assert replay_event["parsed_event"]["trusted_message_id"] == trusted_message_id

    conversation = client.get(f"/api/conversations/{conversation_id}", headers=headers).json()
    assert [message["content"] for message in conversation["messages"]] == [
        "官网客服试点上线周期多久，需要准备什么资料？"
    ]

    _create_active_knowledge_card(client, tenant["id"], headers)
    worker_res = client.post(
        f"/api/tenants/{tenant['id']}/trusted-inbound-worker-runs",
        headers=headers,
        json={
            "batch_size": 5,
            "rate_limit_per_minute": 60,
            "mode": "model_assisted",
            "risk_level": "medium",
            "knowledge_top_k": 3,
            "model_provider": "deterministic",
        },
    )
    assert worker_res.status_code == 201
    worker_run = worker_res.json()
    assert worker_run["processed"] == 1
    assert worker_run["succeeded"] == 1
    assert worker_run["failed"] == 0
    assert worker_run["external_write"] is False
    [worker_item] = worker_run["items"]
    assert worker_item["message_id"] == trusted_message_id
    assert worker_item["reply_decision_id"] > 0
    assert worker_item["decision"] == "knowledge_gap"
    assert worker_item["reason"] == "no_business_object_match"
    assert worker_item["knowledge_gap_id"] > 0
    assert worker_item["human_review_task_id"] is None
    assert worker_item["outbox_draft_id"] is None
    assert worker_item["next_action"] == "review_knowledge_gap"

    inbox_res = client.get(f"/api/tenants/{tenant['id']}/human-review-inbox", headers=headers)
    assert inbox_res.status_code == 200
    assert inbox_res.json() == []

    gaps_res = client.get(
        f"/api/tenants/{tenant['id']}/knowledge-gaps?source_type=reply_decision",
        headers=headers,
    )
    assert gaps_res.status_code == 200
    gaps = gaps_res.json()
    assert gaps["total"] == 1
    assert gaps["items"][0]["id"] == worker_item["knowledge_gap_id"]
    assert gaps["items"][0]["source_ref"] == f"reply_decision:{worker_item['reply_decision_id']}"

    drafts_res = client.get(f"/api/tenants/{tenant['id']}/outbox-drafts", headers=headers)
    assert drafts_res.status_code == 200
    assert drafts_res.json() == []

    workflow_detail = client.get(f"/api/workflow-runs/{worker_item['workflow_run_id']}", headers=headers)
    assert workflow_detail.status_code == 200
    workflow = workflow_detail.json()
    assert workflow["state_payload"]["reply_decision"]["state"] == "knowledge_gap"
    assert workflow["state_payload"]["reply_decision"]["reason"] == "no_business_object_match"
    assert workflow["state_payload"]["knowledge_gap_id"] == worker_item["knowledge_gap_id"]

    receipts = client.get(f"/api/channels/{channel['id']}/delivery-receipts", headers=headers).json()
    assert len(receipts) == 3
    receipt_statuses = {receipt["verification_status"] for receipt in receipts}
    assert {"signature_invalid", "signature_validated"}.issubset(receipt_statuses)
    parsed_statuses = {receipt["raw_payload"]["parsed_event"]["status"] for receipt in receipts}
    assert {"placeholder_only", "trusted_inbound_message_created", "duplicate_ignored"}.issubset(parsed_statuses)
    assert signature not in json.dumps(receipts, ensure_ascii=False)
    assert all(receipt["raw_payload"]["webhook_intake"]["signature_values_stored"] is False for receipt in receipts)

    audit_actions = [event["action"] for event in client.get(f"/api/tenants/{tenant['id']}/audit-events", headers=headers).json()]
    assert "channel_webhook.trusted_inbound_message_created" in audit_actions
    assert "channel_webhook.duplicate_ignored" in audit_actions
    assert "reply_decision.created" in audit_actions
    assert "knowledge_gap.created_from_reply_decision" in audit_actions
    assert "trusted_inbound_worker.orchestrated" in audit_actions
    assert "outbox_draft.created" not in audit_actions
    assert "channel_connector.send_plan_created" not in audit_actions
