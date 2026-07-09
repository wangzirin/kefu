import hashlib
import hmac
import json
import time

from test_channel_connectors_api import _bootstrap_owner, _conversation_with_message, _create_connector


def _sha1_sorted_signature(*parts: str) -> str:
    return hashlib.sha1("".join(sorted(parts)).encode("utf-8")).hexdigest()


def _website_hmac_signature(secret: str, *, timestamp: str, nonce: str, raw_payload: dict) -> str:
    canonical_payload = json.dumps(raw_payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    signing_base = f"{timestamp}\n{nonce}\n{canonical_payload}".encode("utf-8")
    return hmac.new(secret.encode("utf-8"), signing_base, hashlib.sha256).hexdigest()


def _fresh_timestamp() -> str:
    return str(int(time.time()))


def _create_channel(client, tenant_id: int, *, channel_type: str = "wecom") -> dict:
    res = client.post(
        f"/api/tenants/{tenant_id}/channels",
        json={"type": channel_type, "name": "官方入站测试渠道", "reply_mode": "assist", "status": "active"},
    )
    assert res.status_code == 201
    return res.json()


def test_channel_provider_registry_exposes_official_skeleton_contracts(client) -> None:
    _, token = _bootstrap_owner(client, slug="provider-registry", email="provider-registry@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get("/api/channel-providers", headers=headers)

    assert res.status_code == 200
    providers = {item["provider"]: item for item in res.json()}
    assert {"wecom", "wechat_official_account", "website"}.issubset(providers)
    assert providers["wecom"]["display_name"] == "企业微信客服"
    assert providers["wecom"]["default_signature_mode"] == "wecom_token_aeskey"
    assert providers["wecom"]["webhook_path_template"] == "/api/webhooks/wecom/channels/{channel_id}"
    assert providers["wecom"]["verification_contract"]["requires_secret_store"] is True
    assert providers["wecom"]["verification_contract"]["production_status"] == "official_sandbox_inbound_only"
    assert providers["wecom"]["verification_contract"]["validated_in_current_stage"] is True
    assert providers["wecom"]["capabilities"]["external_write_enabled"] is True


def test_official_webhook_intake_records_untrusted_receipt_without_bearer_token(client) -> None:
    tenant, token = _bootstrap_owner(client, slug="webhook-intake", email="webhook-intake@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    channel, _, _ = _conversation_with_message(client, tenant["id"], headers)
    connector = _create_connector(client, channel["id"], headers)

    res = client.post(
        f"/api/webhooks/wecom/channels/{channel['id']}?msg_signature=placeholder&timestamp=123&nonce=abc",
        json={
            "event_type": "delivery_receipt",
            "external_message_id": "platform-message-002",
            "delivery_status": "delivered",
            "provider_event_id": "event-002",
            "raw_payload": {"MsgID": "platform-message-002", "Status": "delivered"},
        },
    )

    assert res.status_code == 202
    event = res.json()
    assert event["tenant_id"] == tenant["id"]
    assert event["channel_id"] == channel["id"]
    assert event["connector_id"] == connector["id"]
    assert event["provider"] == "wecom"
    assert event["event_type"] == "delivery_receipt"
    assert event["verification_status"] == "secret_not_configured"
    assert event["signature_validated"] is False
    assert event["external_write"] is False
    assert event["next_action"] == "configure_secret_store_before_trusting_webhook"
    assert event["parsed_event"]["status"] == "placeholder_only"
    assert event["parsed_event"]["external_message_id"] == "platform-message-002"

    list_res = client.get(f"/api/channels/{channel['id']}/delivery-receipts", headers=headers)
    assert list_res.status_code == 200
    receipts = list_res.json()
    assert len(receipts) == 1
    receipt = receipts[0]
    assert receipt["id"] == event["receipt_id"]
    assert receipt["verification_status"] == "secret_not_configured"
    assert receipt["signature_validated"] is False
    assert receipt["raw_payload"]["webhook_intake"]["query_keys"] == ["msg_signature", "nonce", "timestamp"]
    assert receipt["raw_payload"]["webhook_intake"]["signature_values_stored"] is False

    audit_res = client.get(f"/api/tenants/{tenant['id']}/audit-events", headers=headers)
    actions = [item["action"] for item in audit_res.json()]
    assert "channel_webhook.placeholder_received" in actions


def test_wecom_fixture_signature_validates_without_storing_signature_value(client) -> None:
    tenant, token = _bootstrap_owner(client, slug="webhook-wecom-valid", email="webhook-wecom-valid@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    channel, _, _ = _conversation_with_message(client, tenant["id"], headers)
    connector = _create_connector(
        client,
        channel["id"],
        headers,
        public_config={
            "corp_id_placeholder": "fixture_only",
            "credential_ref": "p2_13_wecom_fixture",
        },
    )
    assert connector["secret_status"] == "fixture_configured"

    timestamp = _fresh_timestamp()
    nonce = "nonce-wecom-valid"
    encrypt = "fixture-wecom-encrypted-payload"
    signature = _sha1_sorted_signature("p2_13_wecom_token", timestamp, nonce, encrypt)
    res = client.post(
        f"/api/webhooks/wecom/channels/{channel['id']}?msg_signature={signature}&timestamp={timestamp}&nonce={nonce}",
        json={
            "event_type": "message",
            "external_message_id": "wecom-message-001",
            "delivery_status": "received",
            "provider_event_id": "wecom-event-001",
            "raw_payload": {"Encrypt": encrypt, "MsgID": "wecom-message-001"},
        },
    )

    assert res.status_code == 202
    event = res.json()
    assert event["verification_status"] == "signature_validated"
    assert event["signature_validated"] is True
    assert event["external_write"] is False
    assert event["next_action"] == "provide_supported_inbound_message_content_before_creating_message"
    assert event["parsed_event"]["status"] == "verified_receipt_only"
    assert event["parsed_event"]["trusted"] is True
    assert event["parsed_event"]["trusted_message_creation"] is False

    list_res = client.get(f"/api/channels/{channel['id']}/delivery-receipts", headers=headers)
    assert list_res.status_code == 200
    receipt = list_res.json()[0]
    assert receipt["verification_status"] == "signature_validated"
    assert receipt["signature_validated"] is True
    assert receipt["raw_payload"]["webhook_intake"]["signature_values_stored"] is False
    assert receipt["raw_payload"]["webhook_intake"]["secret_status"] == "fixture_configured"
    assert receipt["raw_payload"]["webhook_intake"]["verification_method"] == "wecom_sha1_token_timestamp_nonce_encrypt"
    assert signature not in json.dumps(receipt["raw_payload"], ensure_ascii=False)


def test_verified_wecom_message_webhook_creates_trusted_inbound_message(client) -> None:
    tenant, token = _bootstrap_owner(
        client,
        slug="webhook-trusted-inbound",
        email="webhook-trusted-inbound@example.com",
    )
    headers = {"Authorization": f"Bearer {token}"}
    channel = _create_channel(client, tenant["id"])
    _create_connector(
        client,
        channel["id"],
        headers,
        public_config={
            "corp_id_placeholder": "fixture_only",
            "credential_ref": "p2_13_wecom_fixture",
        },
    )

    timestamp = _fresh_timestamp()
    nonce = "nonce-trusted-inbound"
    encrypt = "fixture-wecom-trusted-inbound"
    signature = _sha1_sorted_signature("p2_13_wecom_token", timestamp, nonce, encrypt)
    res = client.post(
        f"/api/webhooks/wecom/channels/{channel['id']}?msg_signature={signature}&timestamp={timestamp}&nonce={nonce}",
        json={
            "event_type": "message",
            "external_message_id": "wecom-message-trusted-001",
            "delivery_status": "received",
            "provider_event_id": "wecom-event-trusted-001",
            "raw_payload": {
                "Encrypt": encrypt,
                "MsgID": "wecom-message-trusted-001",
                "FromUserName": "external-user-trusted-001",
                "Content": "我想查询订单进度",
            },
        },
    )

    assert res.status_code == 202
    event = res.json()
    assert event["verification_status"] == "signature_validated"
    assert event["signature_validated"] is True
    assert event["parsed_event"]["status"] == "trusted_inbound_message_created"
    assert event["parsed_event"]["trusted_message_creation"] is True
    assert event["parsed_event"]["idempotency_status"] == "created"
    assert event["parsed_event"]["trusted_message_id"] > 0
    assert event["parsed_event"]["conversation_id"] > 0
    assert event["next_action"] == "queue_trusted_inbound_message_for_reply_orchestration"

    conversations = client.get(
        f"/api/tenants/{tenant['id']}/conversations?channel_id={channel['id']}",
        headers=headers,
    ).json()
    assert len(conversations) == 1
    detail = client.get(f"/api/conversations/{event['parsed_event']['conversation_id']}", headers=headers).json()
    assert [message["content"] for message in detail["messages"]] == ["我想查询订单进度"]
    message = detail["messages"][0]
    assert message["id"] == event["parsed_event"]["trusted_message_id"]
    assert message["direction"] == "inbound"
    assert message["sender_type"] == "visitor"
    assert message["external_message_id"] == "wecom-message-trusted-001"

    workflow_res = client.get(f"/api/tenants/{tenant['id']}/workflow-runs", headers=headers)
    assert workflow_res.status_code == 200
    workflows = workflow_res.json()
    assert len(workflows) == 1
    assert workflows[0]["trigger_message_id"] == event["parsed_event"]["trusted_message_id"]

    audit_res = client.get(f"/api/tenants/{tenant['id']}/audit-events", headers=headers)
    actions = [item["action"] for item in audit_res.json()]
    assert "channel_webhook.trusted_inbound_message_created" in actions


def test_verified_wecom_message_after_close_does_not_reopen_conversation(client) -> None:
    tenant, token = _bootstrap_owner(
        client,
        slug="webhook-closed-block",
        email="webhook-closed-block@example.com",
    )
    headers = {"Authorization": f"Bearer {token}"}
    channel = _create_channel(client, tenant["id"])
    _create_connector(
        client,
        channel["id"],
        headers,
        public_config={
            "corp_id_placeholder": "fixture_only",
            "credential_ref": "p2_13_wecom_fixture",
        },
    )

    timestamp = _fresh_timestamp()
    nonce = "nonce-closed-first"
    encrypt = "fixture-wecom-closed-first"
    signature = _sha1_sorted_signature("p2_13_wecom_token", timestamp, nonce, encrypt)
    first = client.post(
        f"/api/webhooks/wecom/channels/{channel['id']}?msg_signature={signature}&timestamp={timestamp}&nonce={nonce}",
        json={
            "event_type": "message",
            "external_message_id": "wecom-message-closed-first",
            "delivery_status": "received",
            "provider_event_id": "wecom-event-closed-first",
            "raw_payload": {
                "Encrypt": encrypt,
                "MsgID": "wecom-message-closed-first",
                "FromUserName": "external-user-closed-block",
                "Content": "第一条进线",
            },
        },
    ).json()
    conversation_id = first["parsed_event"]["conversation_id"]

    close_res = client.post(
        f"/api/conversations/{conversation_id}/workflow-actions",
        headers=headers,
        json={"action": "close", "note": "关闭当前企微会话"},
    )
    assert close_res.status_code == 200
    assert close_res.json()["status"] == "closed"

    timestamp = _fresh_timestamp()
    nonce = "nonce-closed-second"
    encrypt = "fixture-wecom-closed-second"
    signature = _sha1_sorted_signature("p2_13_wecom_token", timestamp, nonce, encrypt)
    second_res = client.post(
        f"/api/webhooks/wecom/channels/{channel['id']}?msg_signature={signature}&timestamp={timestamp}&nonce={nonce}",
        json={
            "event_type": "message",
            "external_message_id": "wecom-message-closed-second",
            "delivery_status": "received",
            "provider_event_id": "wecom-event-closed-second",
            "raw_payload": {
                "Encrypt": encrypt,
                "MsgID": "wecom-message-closed-second",
                "FromUserName": "external-user-closed-block",
                "Content": "关闭后继续发",
            },
        },
    )

    assert second_res.status_code == 202
    second = second_res.json()
    assert second["parsed_event"]["status"] == "closed_conversation_inbound_blocked"
    assert second["parsed_event"]["idempotency_status"] == "blocked_after_close"
    assert second["parsed_event"]["trusted_message_creation"] is False
    assert second["parsed_event"]["trusted_message_id"] is None
    assert second["parsed_event"]["conversation_id"] == conversation_id
    assert second["next_action"] == "conversation_closed_ignore_inbound_until_reopened_by_operator"

    conversations = client.get(
        f"/api/tenants/{tenant['id']}/conversations?channel_id={channel['id']}",
        headers=headers,
    ).json()
    assert [item["id"] for item in conversations] == [conversation_id]
    detail = client.get(f"/api/conversations/{conversation_id}", headers=headers).json()
    assert [message["content"] for message in detail["messages"]] == [
        "第一条进线",
        "客服已关闭对话，本次咨询已结束。",
    ]

    audit_res = client.get(f"/api/tenants/{tenant['id']}/audit-events", headers=headers)
    actions = [item["action"] for item in audit_res.json()]
    assert "channel_webhook.closed_conversation_inbound_blocked" in actions


def test_verified_wecom_message_webhook_replay_does_not_duplicate_message(client) -> None:
    tenant, token = _bootstrap_owner(
        client,
        slug="webhook-trusted-replay",
        email="webhook-trusted-replay@example.com",
    )
    headers = {"Authorization": f"Bearer {token}"}
    channel = _create_channel(client, tenant["id"])
    _create_connector(
        client,
        channel["id"],
        headers,
        public_config={
            "corp_id_placeholder": "fixture_only",
            "credential_ref": "p2_13_wecom_fixture",
        },
    )

    timestamp = _fresh_timestamp()
    nonce = "nonce-trusted-replay"
    encrypt = "fixture-wecom-trusted-replay"
    signature = _sha1_sorted_signature("p2_13_wecom_token", timestamp, nonce, encrypt)
    url = f"/api/webhooks/wecom/channels/{channel['id']}?msg_signature={signature}&timestamp={timestamp}&nonce={nonce}"
    body = {
        "event_type": "message",
        "external_message_id": "wecom-message-replay-001",
        "delivery_status": "received",
        "provider_event_id": "wecom-event-replay-001",
        "raw_payload": {
            "Encrypt": encrypt,
            "MsgID": "wecom-message-replay-001",
            "FromUserName": "external-user-replay-001",
            "Content": "重复回调不要重复建消息",
        },
    }

    first = client.post(url, json=body).json()
    second_res = client.post(url, json=body)

    assert second_res.status_code == 202
    second = second_res.json()
    assert first["parsed_event"]["idempotency_key"] == second["parsed_event"]["idempotency_key"]
    assert second["parsed_event"]["status"] == "duplicate_ignored"
    assert second["parsed_event"]["idempotency_status"] == "duplicate_ignored"
    assert second["parsed_event"]["trusted_message_creation"] is False
    assert second["parsed_event"]["trusted_message_id"] == first["parsed_event"]["trusted_message_id"]
    assert second["next_action"] == "duplicate_webhook_ignored"

    detail = client.get(f"/api/conversations/{first['parsed_event']['conversation_id']}", headers=headers).json()
    assert [message["content"] for message in detail["messages"]] == ["重复回调不要重复建消息"]

    receipts = client.get(f"/api/channels/{channel['id']}/delivery-receipts", headers=headers).json()
    assert len(receipts) == 2
    assert receipts[0]["raw_payload"]["parsed_event"]["idempotency_status"] == "duplicate_ignored"
    assert receipts[1]["raw_payload"]["parsed_event"]["idempotency_status"] == "created"


def test_wecom_fixture_rejects_invalid_signature_as_untrusted(client) -> None:
    tenant, token = _bootstrap_owner(client, slug="webhook-wecom-invalid", email="webhook-wecom-invalid@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    channel, _, _ = _conversation_with_message(client, tenant["id"], headers)
    _create_connector(
        client,
        channel["id"],
        headers,
        public_config={
            "corp_id_placeholder": "fixture_only",
            "credential_ref": "p2_13_wecom_fixture",
        },
    )

    timestamp = _fresh_timestamp()
    res = client.post(
        f"/api/webhooks/wecom/channels/{channel['id']}?msg_signature=bad-signature&timestamp={timestamp}&nonce=nonce-bad",
        json={
            "event_type": "message",
            "external_message_id": "wecom-message-002",
            "delivery_status": "received",
            "provider_event_id": "wecom-event-002",
            "raw_payload": {"Encrypt": "fixture-wecom-encrypted-payload", "MsgID": "wecom-message-002"},
        },
    )

    assert res.status_code == 202
    event = res.json()
    assert event["verification_status"] == "signature_invalid"
    assert event["signature_validated"] is False
    assert event["parsed_event"]["status"] == "placeholder_only"
    assert event["parsed_event"]["trusted"] is False
    assert event["next_action"] == "inspect_official_webhook_signature_or_secret_ref"


def test_invalid_signature_does_not_create_trusted_inbound_message(client) -> None:
    tenant, token = _bootstrap_owner(
        client,
        slug="webhook-untrusted-no-message",
        email="webhook-untrusted-no-message@example.com",
    )
    headers = {"Authorization": f"Bearer {token}"}
    channel = _create_channel(client, tenant["id"])
    _create_connector(
        client,
        channel["id"],
        headers,
        public_config={
            "corp_id_placeholder": "fixture_only",
            "credential_ref": "p2_13_wecom_fixture",
        },
    )

    timestamp = _fresh_timestamp()
    res = client.post(
        f"/api/webhooks/wecom/channels/{channel['id']}?msg_signature=bad-signature&timestamp={timestamp}&nonce=nonce-untrusted",
        json={
            "event_type": "message",
            "external_message_id": "wecom-message-untrusted-001",
            "delivery_status": "received",
            "provider_event_id": "wecom-event-untrusted-001",
            "raw_payload": {
                "Encrypt": "fixture-wecom-untrusted",
                "MsgID": "wecom-message-untrusted-001",
                "FromUserName": "external-user-untrusted-001",
                "Content": "这条不能进入消息流",
            },
        },
    )

    assert res.status_code == 202
    event = res.json()
    assert event["verification_status"] == "signature_invalid"
    assert event["parsed_event"]["trusted_message_creation"] is False
    conversations = client.get(
        f"/api/tenants/{tenant['id']}/conversations?channel_id={channel['id']}",
        headers=headers,
    ).json()
    assert conversations == []


def test_wechat_official_account_plain_fixture_signature_validates(client) -> None:
    tenant, token = _bootstrap_owner(client, slug="webhook-wechat-valid", email="webhook-wechat-valid@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    channel, _, _ = _conversation_with_message(
        client, tenant["id"], headers, channel_type="wechat_official_account"
    )
    _create_connector(
        client,
        channel["id"],
        headers,
        provider="wechat_official_account",
        display_name="微信公众号官方接口占位",
        capabilities=["receive_message"],
        public_config={"app_id_placeholder": "fixture_only", "credential_ref": "p2_13_wechat_fixture"},
        webhook_path=f"/api/webhooks/wechat-official-account/channels/{channel['id']}",
        signature_mode="wechat_token",
    )

    timestamp = _fresh_timestamp()
    nonce = "nonce-wechat-valid"
    signature = _sha1_sorted_signature("p2_13_wechat_token", timestamp, nonce)
    res = client.post(
        f"/api/webhooks/wechat-official-account/channels/{channel['id']}?signature={signature}&timestamp={timestamp}&nonce={nonce}",
        json={
            "event_type": "message",
            "external_message_id": "wechat-message-001",
            "delivery_status": "received",
            "provider_event_id": "wechat-event-001",
            "raw_payload": {"MsgId": "wechat-message-001", "Content": "你好"},
        },
    )

    assert res.status_code == 202
    event = res.json()
    assert event["provider"] == "wechat_official_account"
    assert event["verification_status"] == "signature_validated"
    assert event["signature_validated"] is True
    assert event["parsed_event"]["trusted_message_creation"] is False


def test_website_fixture_hmac_signature_validates(client) -> None:
    tenant, token = _bootstrap_owner(client, slug="webhook-website-valid", email="webhook-website-valid@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    channel, _, _ = _conversation_with_message(client, tenant["id"], headers, channel_type="website")
    _create_connector(
        client,
        channel["id"],
        headers,
        provider="website",
        display_name="官网客服组件",
        capabilities=["receive_message"],
        public_config={"site_id_placeholder": "fixture_only", "credential_ref": "p2_13_website_fixture"},
        webhook_path=f"/api/webhooks/website/channels/{channel['id']}",
        signature_mode="website_hmac_sha256",
    )

    timestamp = _fresh_timestamp()
    nonce = "nonce-website-valid"
    raw_payload = {"message_id": "website-message-001", "text": "官网访客想咨询售后"}
    signature = _website_hmac_signature(
        "p2_13_website_signing_secret",
        timestamp=timestamp,
        nonce=nonce,
        raw_payload=raw_payload,
    )
    res = client.post(
        f"/api/webhooks/website/channels/{channel['id']}?signature={signature}&timestamp={timestamp}&nonce={nonce}",
        json={
            "event_type": "message",
            "delivery_status": "received",
            "provider_event_id": "website-event-001",
            "raw_payload": raw_payload,
        },
    )

    assert res.status_code == 202
    event = res.json()
    assert event["provider"] == "website"
    assert event["external_message_id"] == "website-message-001"
    assert event["verification_status"] == "signature_validated"
    assert event["signature_validated"] is True


def test_webhook_intake_rejects_unknown_or_mismatched_provider(client) -> None:
    tenant, token = _bootstrap_owner(client, slug="webhook-mismatch", email="webhook-mismatch@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    channel, _, _ = _conversation_with_message(client, tenant["id"], headers)
    _create_connector(client, channel["id"], headers)

    unknown_res = client.post(
        f"/api/webhooks/unknown-provider/channels/{channel['id']}",
        json={"event_type": "message", "raw_payload": {"text": "hello"}},
    )
    assert unknown_res.status_code == 404

    mismatch_res = client.post(
        f"/api/webhooks/website/channels/{channel['id']}",
        json={"event_type": "message", "raw_payload": {"text": "hello"}},
    )
    assert mismatch_res.status_code == 404


def test_placeholder_receipt_cannot_self_claim_signature_validation(client) -> None:
    tenant, token = _bootstrap_owner(client, slug="receipt-hardening", email="receipt-hardening@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    channel, _, _ = _conversation_with_message(client, tenant["id"], headers)
    _create_connector(client, channel["id"], headers)

    res = client.post(
        f"/api/channels/{channel['id']}/delivery-receipts",
        headers=headers,
        json={
            "provider": "wecom",
            "external_message_id": "platform-message-003",
            "delivery_status": "delivered",
            "provider_event_id": "event-003",
            "raw_payload": {"MsgID": "platform-message-003", "Status": "delivered"},
            "signature_validated": True,
        },
    )

    assert res.status_code == 201
    receipt = res.json()
    assert receipt["verification_status"] == "not_verified_placeholder"
    assert receipt["signature_validated"] is False
