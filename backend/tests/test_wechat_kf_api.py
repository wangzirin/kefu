import json

from app.services.channel_secret_store import WebhookSecretMaterial
from app.services.wechat_kf_api import clear_access_token_cache, send_text_message, sync_messages


class _FakeResponse:
    def __init__(self, payload: dict) -> None:
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def read(self) -> bytes:
        return json.dumps(self.payload).encode("utf-8")


def _material() -> WebhookSecretMaterial:
    return WebhookSecretMaterial(
        provider="wechat_kf",
        credential_ref="test",
        token="callback-token",
        encoding_aes_key="encoding-aes-key",
        app_secret="wechat-kf-secret",
        open_kfid="wk-open-kfid",
        receiver_id="ww-test-corp",
        source="test",
    )


def test_sync_messages_uses_official_token_and_cursor_contract(monkeypatch) -> None:
    clear_access_token_cache()
    requests: list[object] = []

    def fake_urlopen(request, timeout):
        requests.append(request)
        if isinstance(request, str):
            return _FakeResponse({"errcode": 0, "access_token": "access-token", "expires_in": 7200})
        return _FakeResponse(
            {"errcode": 0, "errmsg": "ok", "next_cursor": "next-cursor", "has_more": 0, "msg_list": []}
        )

    monkeypatch.setattr("app.services.wechat_kf_api.urlopen", fake_urlopen)
    result = sync_messages(
        material=_material(),
        callback_token="callback-sync-token",
        cursor="current-cursor",
        timeout=3,
    )

    assert result.payload["next_cursor"] == "next-cursor"
    assert "cgi-bin/gettoken" in requests[0]
    sync_request = requests[1]
    assert sync_request.full_url == "https://qyapi.weixin.qq.com/cgi-bin/kf/sync_msg?access_token=access-token"
    assert json.loads(sync_request.data.decode("utf-8")) == {
        "cursor": "current-cursor",
        "token": "callback-sync-token",
        "limit": 1000,
        "voice_format": 0,
        "open_kfid": "wk-open-kfid",
    }


def test_send_text_message_uses_official_wechat_kf_payload(monkeypatch) -> None:
    clear_access_token_cache()
    requests: list[object] = []

    def fake_urlopen(request, timeout):
        requests.append(request)
        if isinstance(request, str):
            return _FakeResponse({"errcode": 0, "access_token": "access-token"})
        return _FakeResponse({"errcode": 0, "errmsg": "ok", "msgid": "provider-message-id"})

    monkeypatch.setattr("app.services.wechat_kf_api.urlopen", fake_urlopen)
    result = send_text_message(
        material=_material(),
        touser="external-user-id",
        open_kfid="wk-open-kfid",
        content="您好，我来帮您处理",
        timeout=3,
    )

    assert result.payload["msgid"] == "provider-message-id"
    send_request = requests[1]
    assert send_request.full_url == "https://qyapi.weixin.qq.com/cgi-bin/kf/send_msg?access_token=access-token"
    assert json.loads(send_request.data.decode("utf-8")) == {
        "touser": "external-user-id",
        "open_kfid": "wk-open-kfid",
        "msgtype": "text",
        "text": {"content": "您好，我来帮您处理"},
    }
