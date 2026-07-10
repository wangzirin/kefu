import base64
import hashlib
import struct
import time

from Crypto.Cipher import AES

from app.models import Channel, ChannelConnector, Contact, Conversation, Message, OutboxDraft
from app.services.channel_senders import _wechat_external_user_id, _wechat_kf_send
from app.services.trusted_inbound_messages import create_trusted_inbound_message_if_ready
from app.services.wechat_kf_api import WechatKfApiResult
from test_channel_connectors_api import _bootstrap_owner, _create_connector


TEST_TOKEN = "p3_05e_wecom_token"
TEST_RECEIVER_ID = "ww-p3-05e-test-corp"
TEST_ENCODING_AES_KEY = base64.b64encode(bytes(range(32))).decode("ascii").rstrip("=")


def _sha1_sorted_signature(*parts: str) -> str:
    return hashlib.sha1("".join(sorted(parts)).encode("utf-8")).hexdigest()


def _pkcs7_pad(value: bytes) -> bytes:
    pad_len = 32 - (len(value) % 32)
    return value + bytes([pad_len]) * pad_len


def _encrypt_wecom_text(plaintext: str, *, receiver_id: str = TEST_RECEIVER_ID) -> str:
    key = base64.b64decode(TEST_ENCODING_AES_KEY + "=")
    msg = plaintext.encode("utf-8")
    payload = b"0123456789abcdef" + struct.pack(">I", len(msg)) + msg + receiver_id.encode("utf-8")
    cipher = AES.new(key, AES.MODE_CBC, key[:16])
    return base64.b64encode(cipher.encrypt(_pkcs7_pad(payload))).decode("ascii")


def _fresh_timestamp() -> str:
    return str(int(time.time()))


def _create_wecom_channel_and_env_connector(client, monkeypatch) -> tuple[dict, dict, str]:
    monkeypatch.setenv("WECOM_SANDBOX_TOKEN", TEST_TOKEN)
    monkeypatch.setenv("WECOM_SANDBOX_ENCODING_AES_KEY", TEST_ENCODING_AES_KEY)
    monkeypatch.setenv("WECOM_SANDBOX_RECEIVER_ID", TEST_RECEIVER_ID)

    tenant, token = _bootstrap_owner(client, slug="p3-05e-wecom", email="p3-05e-wecom@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    channel_res = client.post(
        f"/api/tenants/{tenant['id']}/channels",
        json={"type": "wecom", "name": "万法常世AI客服测试", "reply_mode": "assist", "status": "active"},
    )
    assert channel_res.status_code == 201
    channel = channel_res.json()
    connector = _create_connector(
        client,
        channel["id"],
        headers,
        capabilities=["receive_message", "delivery_receipt"],
        public_config={
            "credential_ref": "env:WECOM_SANDBOX",
            "corp_id_placeholder": "stored_in_env_only",
        },
    )
    assert connector["secret_status"] == "env_configured"
    return tenant, channel, token


def test_wecom_official_url_verification_decrypts_echostr(client, monkeypatch) -> None:
    _, channel, _ = _create_wecom_channel_and_env_connector(client, monkeypatch)

    timestamp = _fresh_timestamp()
    nonce = "p3-05e-url-verify"
    encrypted_echo = _encrypt_wecom_text("p3-05e-echo-ok")
    signature = _sha1_sorted_signature(TEST_TOKEN, timestamp, nonce, encrypted_echo)

    res = client.get(
        f"/api/webhooks/wecom/channels/{channel['id']}",
        params={
            "msg_signature": signature,
            "timestamp": timestamp,
            "nonce": nonce,
            "echostr": encrypted_echo,
        },
    )

    assert res.status_code == 200
    assert res.text == "p3-05e-echo-ok"
    assert res.headers["content-type"].startswith("text/plain")


def test_wecom_official_url_verification_rejects_bad_signature_without_secret_leak(client, monkeypatch) -> None:
    _, channel, _ = _create_wecom_channel_and_env_connector(client, monkeypatch)

    timestamp = _fresh_timestamp()
    encrypted_echo = _encrypt_wecom_text("must-not-be-returned")

    res = client.get(
        f"/api/webhooks/wecom/channels/{channel['id']}",
        params={
            "msg_signature": "bad-signature",
            "timestamp": timestamp,
            "nonce": "p3-05e-url-bad",
            "echostr": encrypted_echo,
        },
    )

    assert res.status_code == 403
    assert TEST_TOKEN not in res.text
    assert TEST_ENCODING_AES_KEY not in res.text
    assert encrypted_echo not in res.text


def test_legacy_wecom_callback_url_verification_uses_env_without_connector(client, monkeypatch) -> None:
    monkeypatch.setenv("WECOM_CALLBACK_TOKEN", TEST_TOKEN)
    monkeypatch.setenv("WECOM_CALLBACK_ENCODING_AES_KEY", TEST_ENCODING_AES_KEY)
    monkeypatch.setenv("WECOM_CALLBACK_RECEIVER_ID", TEST_RECEIVER_ID)

    timestamp = _fresh_timestamp()
    nonce = "p3-05e-legacy-url-verify"
    encrypted_echo = _encrypt_wecom_text("legacy-wecom-echo-ok")
    signature = _sha1_sorted_signature(TEST_TOKEN, timestamp, nonce, encrypted_echo)

    res = client.get(
        "/wecom/callback",
        params={
            "msg_signature": signature,
            "timestamp": timestamp,
            "nonce": nonce,
            "echostr": encrypted_echo,
        },
    )

    assert res.status_code == 200
    assert res.text == "legacy-wecom-echo-ok"
    assert res.headers["content-type"].startswith("text/plain")


def test_wecom_official_xml_message_decrypts_and_creates_trusted_inbound_message(client, monkeypatch) -> None:
    tenant, channel, token = _create_wecom_channel_and_env_connector(client, monkeypatch)
    headers = {"Authorization": f"Bearer {token}"}

    inner_xml = """
<xml>
  <ToUserName><![CDATA[kf-p3-05e-open-kfid]]></ToUserName>
  <FromUserName><![CDATA[external-user-p3-05e-001]]></FromUserName>
  <CreateTime>1710000000</CreateTime>
  <MsgType><![CDATA[text]]></MsgType>
  <Content><![CDATA[我想了解试点部署怎么开始]]></Content>
  <MsgId>wecom-p3-05e-message-001</MsgId>
</xml>
""".strip()
    encrypt = _encrypt_wecom_text(inner_xml)
    timestamp = _fresh_timestamp()
    nonce = "p3-05e-xml-message"
    signature = _sha1_sorted_signature(TEST_TOKEN, timestamp, nonce, encrypt)
    outer_xml = f"""
<xml>
  <ToUserName><![CDATA[{TEST_RECEIVER_ID}]]></ToUserName>
  <Encrypt><![CDATA[{encrypt}]]></Encrypt>
  <AgentID><![CDATA[p3-05e-agent]]></AgentID>
</xml>
""".strip()

    res = client.post(
        f"/api/webhooks/wecom/channels/{channel['id']}?msg_signature={signature}&timestamp={timestamp}&nonce={nonce}",
        content=outer_xml,
        headers={"Content-Type": "application/xml"},
    )

    assert res.status_code == 202
    event = res.json()
    assert event["verification_status"] == "signature_validated"
    assert event["signature_validated"] is True
    assert event["external_write"] is False
    assert event["parsed_event"]["status"] == "trusted_inbound_message_created"
    assert event["parsed_event"]["trusted_message_creation"] is True
    assert event["parsed_event"]["external_message_id"] == "wecom-p3-05e-message-001"
    assert event["next_action"] == "queue_trusted_inbound_message_for_reply_orchestration"

    detail = client.get(f"/api/conversations/{event['parsed_event']['conversation_id']}", headers=headers).json()
    assert [message["content"] for message in detail["messages"]] == ["我想了解试点部署怎么开始"]
    assert detail["messages"][0]["external_message_id"] == "wecom-p3-05e-message-001"

    receipts = client.get(f"/api/channels/{channel['id']}/delivery-receipts", headers=headers).json()
    assert len(receipts) >= 1
    stored = next(item["raw_payload"] for item in receipts if item["verification_status"] == "signature_validated")
    assert stored["webhook_intake"]["secret_status"] == "env_configured"
    assert stored["webhook_intake"]["official_xml_decrypted"] is True
    assert stored["webhook_intake"]["signature_values_stored"] is False
    assert signature not in str(stored)
    assert encrypt not in str(stored)
    assert TEST_TOKEN not in str(stored)
    assert TEST_ENCODING_AES_KEY not in str(stored)

    workflow_res = client.get(f"/api/tenants/{tenant['id']}/workflow-runs", headers=headers)
    assert workflow_res.status_code == 200
    assert workflow_res.json()


def test_wechat_kf_manual_connector_url_verification_and_message_enters_service_desk(client, monkeypatch, tmp_path, db_session) -> None:
    monkeypatch.setattr(
        "app.services.channel_secret_store._secret_store_path",
        lambda: tmp_path / "local_channel_secrets.json",
    )
    tenant, token = _bootstrap_owner(client, slug="wechat-kf-manual", email="wechat-kf-manual@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    channel_res = client.post(
        f"/api/tenants/{tenant['id']}/channels",
        json={"type": "wechat_kf", "name": "微信客服", "reply_mode": "assist", "status": "active"},
    )
    assert channel_res.status_code == 201
    channel = channel_res.json()
    connector = _create_connector(
        client,
        channel["id"],
        headers,
        provider="wechat_kf",
        display_name="微信客服",
        capabilities=["receive_message", "draft_reply"],
        public_config={
            "enterprise_name": "测试企业",
            "corp_id": TEST_RECEIVER_ID,
            "callback_url": f"/api/webhooks/wechat-kf/channels/{channel['id']}",
        },
        webhook_path=f"/api/webhooks/wechat-kf/channels/{channel['id']}",
        signature_mode="wechat_kf_token_aeskey",
    )
    assert connector["provider"] == "wechat_kf"
    secret_res = client.post(
        f"/api/channels/{channel['id']}/connector-secrets",
        headers=headers,
        json={
            "secrets": {
                "token": TEST_TOKEN,
                "encoding_aes_key": TEST_ENCODING_AES_KEY,
                "corp_id": TEST_RECEIVER_ID,
                "open_kfid": "kf-test-open-kfid",
                "app_secret": "wechat-kf-secret-only-for-test",
            }
        },
    )
    assert secret_res.status_code == 200
    assert secret_res.json()["status"] == "configured"
    verify_res = client.post(f"/api/channels/{channel['id']}/connector-verification", headers=headers)
    assert verify_res.status_code == 200
    assert verify_res.json()["status"] == "verified"

    timestamp = _fresh_timestamp()
    nonce = "wechat-kf-url-verify"
    encrypted_echo = _encrypt_wecom_text("wechat-kf-echo-ok")
    signature = _sha1_sorted_signature(TEST_TOKEN, timestamp, nonce, encrypted_echo)
    url_res = client.get(
        "/wechat-kf/callback",
        params={
            "msg_signature": signature,
            "timestamp": timestamp,
            "nonce": nonce,
            "echostr": encrypted_echo,
        },
    )
    assert url_res.status_code == 200
    assert url_res.text == "wechat-kf-echo-ok"

    inner_xml = """
<xml>
  <ToUserName><![CDATA[kf-test-open-kfid]]></ToUserName>
  <FromUserName><![CDATA[external-wechat-kf-user-001]]></FromUserName>
  <CreateTime>1710000000</CreateTime>
  <MsgType><![CDATA[text]]></MsgType>
  <Content><![CDATA[我想咨询微信客服接入测试]]></Content>
  <MsgId>wechat-kf-message-001</MsgId>
</xml>
""".strip()
    encrypt = _encrypt_wecom_text(inner_xml)
    timestamp = _fresh_timestamp()
    nonce = "wechat-kf-message"
    signature = _sha1_sorted_signature(TEST_TOKEN, timestamp, nonce, encrypt)
    outer_xml = f"""
<xml>
  <ToUserName><![CDATA[{TEST_RECEIVER_ID}]]></ToUserName>
  <Encrypt><![CDATA[{encrypt}]]></Encrypt>
</xml>
""".strip()
    post_res = client.post(
        f"/wechat-kf/callback?msg_signature={signature}&timestamp={timestamp}&nonce={nonce}",
        content=outer_xml,
        headers={"Content-Type": "application/xml"},
    )
    assert post_res.status_code == 202
    event = post_res.json()
    assert event["provider"] == "wechat_kf"
    assert event["verification_status"] == "signature_validated"
    assert event["signature_validated"] is True
    assert event["parsed_event"]["status"] == "trusted_inbound_message_created"
    assert event["parsed_event"]["trusted_message_creation"] is True
    assert event["parsed_event"]["external_message_id"] == "wechat-kf-message-001"
    assert event["external_write"] is False

    detail = client.get(f"/api/conversations/{event['parsed_event']['conversation_id']}", headers=headers).json()
    contents = [message["content"] for message in detail["messages"]]
    assert "我想咨询微信客服接入测试" in contents
    assert detail["messages"][0]["external_message_id"] == "wechat-kf-message-001"

    claim_res = client.post(f"/api/conversations/{event['parsed_event']['conversation_id']}/claim", headers=headers)
    assert claim_res.status_code == 200
    reply_res = client.post(
        f"/api/conversations/{event['parsed_event']['conversation_id']}/agent-replies",
        headers=headers,
        json={"content": "您好，我来帮您处理"},
    )
    assert reply_res.status_code == 201
    assert reply_res.json()["sender_type"] == "agent"
    drafts_res = client.get(f"/api/tenants/{tenant['id']}/outbox-drafts", headers=headers)
    assert drafts_res.status_code == 200
    agent_draft = next(item for item in drafts_res.json() if item["source_message_id"] == reply_res.json()["id"])
    db_session.expire_all()
    draft_row = db_session.get(OutboxDraft, agent_draft["id"])
    assert draft_row is not None
    assert _wechat_external_user_id(db_session, draft_row) == "external-wechat-kf-user-001"
    jobs_res = client.get(f"/api/tenants/{tenant['id']}/outbox-delivery-jobs", headers=headers)
    assert jobs_res.status_code == 200
    agent_job = next(item for item in jobs_res.json() if item["outbox_draft_id"] == agent_draft["id"])
    assert agent_job["status"] == "blocked"
    attempts_res = client.get(f"/api/outbox-drafts/{agent_draft['id']}/send-attempts", headers=headers)
    assert attempts_res.status_code == 200
    [attempt] = attempts_res.json()
    assert attempt["status"] == "blocked"
    assert attempt["response_payload"]["blocked_reason"] == "external_write_kill_switch"

    receipts = client.get(f"/api/channels/{channel['id']}/delivery-receipts", headers=headers).json()
    stored = next(item["raw_payload"] for item in receipts if item["verification_status"] == "signature_validated")
    assert stored["webhook_intake"]["official_xml_decrypted"] is True
    assert stored["webhook_intake"]["signature_values_stored"] is False
    assert signature not in str(stored)
    assert encrypt not in str(stored)
    assert TEST_TOKEN not in str(stored)
    assert TEST_ENCODING_AES_KEY not in str(stored)


def test_wechat_kf_notification_syncs_real_customer_message_once(client, monkeypatch, tmp_path, db_session) -> None:
    monkeypatch.setattr(
        "app.services.channel_secret_store._secret_store_path",
        lambda: tmp_path / "local_channel_secrets.json",
    )
    tenant, token = _bootstrap_owner(client, slug="wechat-kf-sync", email="wechat-kf-sync@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    channel = client.post(
        f"/api/tenants/{tenant['id']}/channels",
        json={"type": "wechat_kf", "name": "微信客服", "reply_mode": "assist", "status": "active"},
    ).json()
    _create_connector(
        client,
        channel["id"],
        headers,
        provider="wechat_kf",
        display_name="微信客服",
        capabilities=["receive_message", "draft_reply"],
        public_config={"corp_id": TEST_RECEIVER_ID},
        webhook_path=f"/api/webhooks/wechat-kf/channels/{channel['id']}",
        signature_mode="wechat_kf_token_aeskey",
    )
    secret_res = client.post(
        f"/api/channels/{channel['id']}/connector-secrets",
        headers=headers,
        json={
            "secrets": {
                "token": TEST_TOKEN,
                "encoding_aes_key": TEST_ENCODING_AES_KEY,
                "corp_id": TEST_RECEIVER_ID,
                "open_kfid": "kf-sync-open-kfid",
                "app_secret": "wechat-kf-sync-secret",
            }
        },
    )
    assert secret_res.status_code == 200

    sync_calls: list[dict] = []

    def fake_sync_messages(**kwargs):
        sync_calls.append(kwargs)
        return WechatKfApiResult(
            payload={
                "errcode": 0,
                "errmsg": "ok",
                "next_cursor": "cursor-after-message-001",
                "has_more": 0,
                "msg_list": [
                    {
                        "msgid": "wechat-kf-synced-message-001",
                        "open_kfid": "kf-sync-open-kfid",
                        "external_userid": "external-wechat-kf-sync-user-001",
                        "send_time": 1710000000,
                        "origin": 3,
                        "msgtype": "text",
                        "text": {"content": "这是一条通过同步接口取得的客户消息"},
                    },
                    {
                        "msgid": "wechat-kf-agent-origin-message",
                        "open_kfid": "kf-sync-open-kfid",
                        "external_userid": "external-wechat-kf-sync-user-001",
                        "send_time": 1710000001,
                        "origin": 5,
                        "msgtype": "text",
                        "text": {"content": "企业微信客户端坐席消息不应当作客户入站"},
                    },
                ],
            }
        )

    monkeypatch.setattr("app.services.channel_connectors.sync_messages", fake_sync_messages)
    inner_xml = """
<xml>
  <ToUserName><![CDATA[ww-p3-05e-test-corp]]></ToUserName>
  <CreateTime>1710000000</CreateTime>
  <Event><![CDATA[kf_msg_or_event]]></Event>
  <Token><![CDATA[wechat-kf-callback-sync-token]]></Token>
</xml>
""".strip()
    encrypt = _encrypt_wecom_text(inner_xml)
    timestamp = _fresh_timestamp()
    nonce = "wechat-kf-sync-notification"
    signature = _sha1_sorted_signature(TEST_TOKEN, timestamp, nonce, encrypt)
    outer_xml = f"<xml><Encrypt><![CDATA[{encrypt}]]></Encrypt></xml>"
    callback_url = (
        f"/api/webhooks/wechat-kf/channels/{channel['id']}"
        f"?msg_signature={signature}&timestamp={timestamp}&nonce={nonce}"
    )

    first = client.post(callback_url, content=outer_xml, headers={"Content-Type": "application/xml"})
    assert first.status_code == 200
    assert first.text == "success"
    assert sync_calls[0]["cursor"] == ""

    second = client.post(callback_url, content=outer_xml, headers={"Content-Type": "application/xml"})
    assert second.status_code == 200
    assert second.text == "success"
    assert sync_calls[1]["cursor"] == "cursor-after-message-001"

    inbound_messages = db_session.query(Message).filter(Message.direction == "inbound").all()
    assert [item.external_message_id for item in inbound_messages] == ["wechat-kf-synced-message-001"]
    assert inbound_messages[0].content == "这是一条通过同步接口取得的客户消息"
    connector = db_session.query(ChannelConnector).filter(ChannelConnector.channel_id == channel["id"]).one()
    assert connector.public_config["wechat_kf_sync_cursor"] == "cursor-after-message-001"
    assert connector.public_config["open_kfid"] == "kf-sync-open-kfid"
    public_connector = client.get(f"/api/channels/{channel['id']}/connector-config", headers=headers).json()
    assert "wechat_kf_sync_cursor" not in public_connector["public_config"]


def test_wechat_kf_new_message_after_close_creates_new_conversation(client, db_session) -> None:
    tenant, _token = _bootstrap_owner(
        client,
        slug="wechat-kf-reopen-after-close",
        email="wechat-kf-reopen-after-close@example.com",
    )
    channel_data = client.post(
        f"/api/tenants/{tenant['id']}/channels",
        json={"type": "wechat_kf", "name": "微信客服", "reply_mode": "assist", "status": "active"},
    ).json()
    channel = db_session.get(Channel, channel_data["id"])
    contact = Contact(
        tenant_id=tenant["id"],
        display_name="重复咨询微信客户",
        wechat="wechat_kf:external-reopen-user-001",
    )
    db_session.add(contact)
    db_session.flush()
    closed = Conversation(
        tenant_id=tenant["id"],
        channel_id=channel.id,
        contact_id=contact.id,
        status="closed",
        priority="normal",
        subject="已结束的微信客服会话",
    )
    db_session.add(closed)
    db_session.commit()

    result = create_trusted_inbound_message_if_ready(
        db_session,
        channel=channel,
        provider="wechat_kf",
        event_type="message",
        provider_event_id="",
        external_message_id="wechat-kf-message-after-close-001",
        raw_payload={
            "external_userid": "external-reopen-user-001",
            "Content": "结束后再次咨询",
            "open_kfid": "wk-reopen-001",
        },
    )
    db_session.commit()

    assert result.status == "trusted_inbound_message_created"
    assert result.conversation_id != closed.id
    reopened = db_session.get(Conversation, result.conversation_id)
    assert reopened.status == "bot_visiting"
    assert reopened.contact_id == contact.id
    assert db_session.get(Conversation, closed.id).status == "closed"
    message = db_session.get(Message, result.trusted_message_id)
    assert message.content == "结束后再次咨询"


def test_wechat_kf_successful_send_preserves_agent_state_and_records_ai_message(
    client, monkeypatch, tmp_path, db_session
) -> None:
    monkeypatch.setattr(
        "app.services.channel_secret_store._secret_store_path",
        lambda: tmp_path / "local_channel_secrets.json",
    )
    tenant, token = _bootstrap_owner(client, slug="wechat-kf-send", email="wechat-kf-send@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    channel_data = client.post(
        f"/api/tenants/{tenant['id']}/channels",
        json={"type": "wechat_kf", "name": "微信客服", "reply_mode": "assist", "status": "active"},
    ).json()
    connector_data = _create_connector(
        client,
        channel_data["id"],
        headers,
        provider="wechat_kf",
        display_name="微信客服",
        public_config={"corp_id": TEST_RECEIVER_ID},
        external_write_enabled=True,
    )
    client.post(
        f"/api/channels/{channel_data['id']}/connector-secrets",
        headers=headers,
        json={
            "secrets": {
                "token": TEST_TOKEN,
                "encoding_aes_key": TEST_ENCODING_AES_KEY,
                "corp_id": TEST_RECEIVER_ID,
                "open_kfid": "kf-send-open-kfid",
                "app_secret": "wechat-kf-send-secret",
            }
        },
    )
    channel = db_session.get(Channel, channel_data["id"])
    connector = db_session.get(ChannelConnector, connector_data["id"])
    contact = Contact(
        tenant_id=tenant["id"],
        display_name="微信客户",
        wechat="wechat_kf:external-send-user-001",
    )
    db_session.add(contact)
    db_session.flush()

    agent_conversation = Conversation(
        tenant_id=tenant["id"],
        channel_id=channel.id,
        contact_id=contact.id,
        assigned_user_id=1,
        status="assigned_to_me",
        priority="normal",
        subject="人工回复",
    )
    db_session.add(agent_conversation)
    db_session.flush()
    agent_message = Message(
        conversation_id=agent_conversation.id,
        direction="outbound",
        sender_type="agent",
        content="您好，我来帮您处理",
        external_message_id="agent-local-001",
    )
    db_session.add(agent_message)
    db_session.flush()
    agent_draft = OutboxDraft(
        tenant_id=tenant["id"],
        conversation_id=agent_conversation.id,
        channel_id=channel.id,
        contact_id=contact.id,
        source_message_id=agent_message.id,
        status="ready_to_send",
        reply_text=agent_message.content,
        idempotency_key="wechat-kf-agent-send-state",
    )
    db_session.add(agent_draft)
    db_session.flush()

    sent_payloads: list[dict] = []

    def fake_send_text_message(**kwargs):
        sent_payloads.append(kwargs)
        return WechatKfApiResult(payload={"errcode": 0, "errmsg": "ok", "msgid": f"sent-{len(sent_payloads)}"})

    monkeypatch.setattr("app.services.channel_senders.send_text_message", fake_send_text_message)
    agent_result = _wechat_kf_send(db_session, draft=agent_draft, connector=connector)
    assert agent_result.status == "succeeded"
    assert agent_conversation.status == "assigned_to_me"
    assert db_session.query(Message).filter(Message.conversation_id == agent_conversation.id).count() == 1

    ai_conversation = Conversation(
        tenant_id=tenant["id"],
        channel_id=channel.id,
        contact_id=contact.id,
        status="bot_visiting",
        priority="normal",
        subject="AI 回复",
    )
    db_session.add(ai_conversation)
    db_session.flush()
    inbound = Message(
        conversation_id=ai_conversation.id,
        direction="inbound",
        sender_type="visitor",
        content="你们几点上班",
        external_message_id="inbound-ai-001",
    )
    db_session.add(inbound)
    db_session.flush()
    ai_draft = OutboxDraft(
        tenant_id=tenant["id"],
        conversation_id=ai_conversation.id,
        channel_id=channel.id,
        contact_id=contact.id,
        source_message_id=inbound.id,
        status="ready_to_send",
        reply_text="营业时间是 9:00-18:00",
        idempotency_key="wechat-kf-ai-send-message",
    )
    db_session.add(ai_draft)
    db_session.flush()
    ai_result = _wechat_kf_send(db_session, draft=ai_draft, connector=connector)
    assert ai_result.status == "succeeded"
    ai_messages = db_session.query(Message).filter(Message.conversation_id == ai_conversation.id).all()
    assert [(item.direction, item.sender_type, item.content) for item in ai_messages] == [
        ("inbound", "visitor", "你们几点上班"),
        ("outbound", "ai", "营业时间是 9:00-18:00"),
    ]
    assert ai_conversation.status == "bot_visiting"
    assert sent_payloads[0]["touser"] == "external-send-user-001"
