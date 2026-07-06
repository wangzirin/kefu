import base64
import hashlib
import struct
import time

from Crypto.Cipher import AES

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
    assert len(receipts) == 1
    stored = receipts[0]["raw_payload"]
    assert stored["webhook_intake"]["secret_status"] == "env_configured"
    assert stored["webhook_intake"]["official_xml_decrypted"] is True
    assert stored["webhook_intake"]["signature_values_stored"] is False
    assert signature not in str(stored)
    assert encrypt not in str(stored)
    assert TEST_TOKEN not in str(stored)
    assert TEST_ENCODING_AES_KEY not in str(stored)

    workflow_res = client.get(f"/api/tenants/{tenant['id']}/workflow-runs", headers=headers)
    assert workflow_res.status_code == 200
    assert workflow_res.json() == []
