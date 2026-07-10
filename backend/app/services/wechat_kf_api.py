from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from threading import Lock
from time import monotonic
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from app.services.channel_secret_store import WebhookSecretMaterial


@dataclass(frozen=True)
class WechatKfApiResult:
    payload: dict
    retryable: bool = False


class WechatKfApiError(RuntimeError):
    def __init__(self, message: str, *, retryable: bool = False, error_code: int = 0) -> None:
        super().__init__(message)
        self.retryable = retryable
        self.error_code = error_code


RETRYABLE_ERROR_CODES = {-1, 40001, 40014, 42001, 45009, 45047}
_TOKEN_CACHE: dict[str, tuple[str, float]] = {}
_TOKEN_CACHE_LOCK = Lock()


def _read_json_response(request: Request | str, *, timeout: float) -> dict:
    try:
        with urlopen(request, timeout=timeout) as response:
            body = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        raise WechatKfApiError(f"wechat_kf HTTP {exc.code}", retryable=exc.code >= 500) from exc
    except (URLError, TimeoutError, ValueError, json.JSONDecodeError) as exc:
        raise WechatKfApiError(f"wechat_kf request failed: {str(exc)[:200]}", retryable=True) from exc
    if not isinstance(body, dict):
        raise WechatKfApiError("wechat_kf response is not an object", retryable=True)
    errcode = int(body.get("errcode") or 0)
    if errcode != 0:
        message = f"wechat_kf provider error: {errcode} {body.get('errmsg') or ''}".strip()
        raise WechatKfApiError(
            message,
            retryable=errcode in RETRYABLE_ERROR_CODES,
            error_code=errcode,
        )
    return body


def get_access_token(*, material: WebhookSecretMaterial, timeout: float) -> str:
    if not material.receiver_id or not material.app_secret:
        raise WechatKfApiError("wechat_kf missing corp_id/secret")
    cache_key = f"{material.receiver_id}:{hashlib.sha256(material.app_secret.encode('utf-8')).hexdigest()}"
    now = monotonic()
    with _TOKEN_CACHE_LOCK:
        cached = _TOKEN_CACHE.get(cache_key)
        if cached is not None and cached[1] > now:
            return cached[0]
    query = urlencode({"corpid": material.receiver_id, "corpsecret": material.app_secret})
    body = _read_json_response(
        f"https://qyapi.weixin.qq.com/cgi-bin/gettoken?{query}",
        timeout=timeout,
    )
    access_token = str(body.get("access_token") or "")
    if not access_token:
        raise WechatKfApiError("wechat_kf token response missing access_token", retryable=True)
    expires_in = max(int(body.get("expires_in") or 7200), 60)
    with _TOKEN_CACHE_LOCK:
        _TOKEN_CACHE[cache_key] = (access_token, now + max(expires_in - 300, 30))
    return access_token


def clear_access_token_cache() -> None:
    with _TOKEN_CACHE_LOCK:
        _TOKEN_CACHE.clear()


def _invalidate_access_token(material: WebhookSecretMaterial) -> None:
    cache_key = f"{material.receiver_id}:{hashlib.sha256(material.app_secret.encode('utf-8')).hexdigest()}"
    with _TOKEN_CACHE_LOCK:
        _TOKEN_CACHE.pop(cache_key, None)


def post_api_json(*, path: str, access_token: str, payload: dict, timeout: float) -> WechatKfApiResult:
    request = Request(
        f"https://qyapi.weixin.qq.com/cgi-bin/{path}?access_token={access_token}",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    return WechatKfApiResult(payload=_read_json_response(request, timeout=timeout))


def sync_messages(
    *,
    material: WebhookSecretMaterial,
    callback_token: str,
    cursor: str,
    timeout: float,
    limit: int = 1000,
) -> WechatKfApiResult:
    if not callback_token:
        raise WechatKfApiError("wechat_kf callback event missing sync token")
    payload: dict[str, object] = {
        "cursor": cursor,
        "token": callback_token,
        "limit": max(1, min(limit, 1000)),
        "voice_format": 0,
    }
    if material.open_kfid:
        payload["open_kfid"] = material.open_kfid
    for attempt in range(2):
        access_token = get_access_token(material=material, timeout=timeout)
        try:
            return post_api_json(
                path="kf/sync_msg",
                access_token=access_token,
                payload=payload,
                timeout=timeout,
            )
        except WechatKfApiError as exc:
            if attempt == 0 and exc.error_code in {40001, 40014, 42001}:
                _invalidate_access_token(material)
                continue
            raise
    raise WechatKfApiError("wechat_kf sync failed after token refresh", retryable=True)


def send_text_message(
    *,
    material: WebhookSecretMaterial,
    touser: str,
    open_kfid: str,
    content: str,
    timeout: float,
) -> WechatKfApiResult:
    payload = {
        "touser": touser,
        "open_kfid": open_kfid,
        "msgtype": "text",
        "text": {"content": content},
    }
    for attempt in range(2):
        access_token = get_access_token(material=material, timeout=timeout)
        try:
            return post_api_json(
                path="kf/send_msg",
                access_token=access_token,
                payload=payload,
                timeout=timeout,
            )
        except WechatKfApiError as exc:
            if attempt == 0 and exc.error_code in {40001, 40014, 42001}:
                _invalidate_access_token(material)
                continue
            raise
    raise WechatKfApiError("wechat_kf send failed after token refresh", retryable=True)
