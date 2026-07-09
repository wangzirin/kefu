import base64
import hashlib
import struct
import time

from Crypto.Cipher import AES

from app.models import OutboxDraft
from app.services.channel_senders import _wechat_external_user_id
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
