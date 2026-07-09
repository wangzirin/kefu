from __future__ import annotations

from dataclasses import dataclass
import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import Channel, ChannelConnector, Contact, Conversation, Message, OutboxDraft
from app.models.foundation import utc_now
from app.services.channel_provider_registry import normalize_provider
from app.services.channel_secret_store import resolve_webhook_secret_material


@dataclass(frozen=True)
class ChannelSendResult:
    status: str
    delivery_status: str
    external_message_id: str = ""
    response_payload: dict | None = None
    error_message: str = ""
    retryable: bool = False


def _website_send(db: Session, *, draft: OutboxDraft, connector: ChannelConnector) -> ChannelSendResult:
    now = utc_now()
    message = Message(
        conversation_id=draft.conversation_id,
        direction="outbound",
        sender_type="ai",
        content=draft.reply_text.strip(),
        external_message_id=f"website-ai-{draft.conversation_id}-{draft.id}",
        created_at=now,
    )
    db.add(message)
    conversation = db.get(Conversation, draft.conversation_id)
    if conversation is not None:
        conversation.status = "bot_visiting"
        conversation.last_message_at = now
    draft.delivery_status = "sent"
    draft.sent_at = now
    draft.updated_at = now
    db.flush()
    return ChannelSendResult(
        status="succeeded",
        delivery_status="sent",
        external_message_id=message.external_message_id,
        response_payload={
            "provider": "website",
            "message_id": message.id,
            "external_write": True,
            "connector_id": connector.id,
        },
    )


def _wechat_external_user_id(db: Session, draft: OutboxDraft) -> str:
    contact = db.get(Contact, draft.contact_id)
    if contact is not None and contact.wechat:
        provider_prefix, separator, external_id = contact.wechat.partition(":")
        if separator and normalize_provider(provider_prefix) in {"wechat_kf", "wecom"} and external_id:
            return external_id
        if not separator:
            return contact.wechat
    source = db.get(Message, draft.source_message_id) if draft.source_message_id else None
    if source and source.external_message_id:
        return source.external_message_id
    conversation = db.get(Conversation, draft.conversation_id)
    if conversation is None:
        return ""
    # Trusted inbound creation stores the platform id as message.external_message_id for official channels.
    last_inbound = (
        db.query(Message)
        .filter(Message.conversation_id == conversation.id, Message.direction == "inbound")
        .order_by(Message.created_at.desc(), Message.id.desc())
        .first()
    )
    return last_inbound.external_message_id if last_inbound else ""


def _wechat_kf_send(db: Session, *, draft: OutboxDraft, connector: ChannelConnector) -> ChannelSendResult:
    resolution = resolve_webhook_secret_material(provider="wechat_kf", public_config=connector.public_config)
    if resolution.material is None:
        return ChannelSendResult(
            status="failed",
            delivery_status="not_sent",
            error_message=f"wechat_kf secret unavailable: {resolution.status}",
            response_payload={"secret_status": resolution.status, "secret_included": False},
            retryable=False,
        )
    material = resolution.material
    touser = _wechat_external_user_id(db, draft)
    open_kfid = material.open_kfid or str((connector.public_config or {}).get("open_kfid") or "")
    if not touser or not open_kfid or not material.receiver_id or not material.app_secret:
        return ChannelSendResult(
            status="failed",
            delivery_status="not_sent",
            error_message="wechat_kf missing touser/open_kfid/corp_id/secret",
            response_payload={
                "missing_touser": not bool(touser),
                "missing_open_kfid": not bool(open_kfid),
                "missing_corp_id": not bool(material.receiver_id),
                "missing_secret": not bool(material.app_secret),
                "secret_included": False,
            },
            retryable=False,
        )
    settings = get_settings()
    try:
        token_query = urlencode({"corpid": material.receiver_id, "corpsecret": material.app_secret})
        with urlopen(
            f"https://qyapi.weixin.qq.com/cgi-bin/gettoken?{token_query}",
            timeout=settings.model_http_timeout_seconds,
        ) as response:
            token_body = json.loads(response.read().decode("utf-8"))
        access_token = str(token_body.get("access_token") or "")
        if not access_token:
            return ChannelSendResult(
                status="failed",
                delivery_status="not_sent",
                error_message=f"wechat_kf token error: {token_body.get('errmsg') or token_body.get('errcode')}",
                response_payload={"provider_response": _safe_provider_response(token_body), "secret_included": False},
                retryable=True,
            )
        payload = {
            "touser": touser,
            "open_kfid": open_kfid,
            "msgtype": "text",
            "text": {"content": draft.reply_text.strip()},
        }
        request = Request(
            f"https://qyapi.weixin.qq.com/cgi-bin/kf/send_msg?access_token={access_token}",
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(request, timeout=settings.model_http_timeout_seconds) as response:
            send_body = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        return ChannelSendResult(
            status="failed",
            delivery_status="failed",
            error_message=f"wechat_kf HTTP {exc.code}",
            response_payload={"secret_included": False},
            retryable=True,
        )
    except (URLError, TimeoutError, ValueError, json.JSONDecodeError) as exc:
        return ChannelSendResult(
            status="failed",
            delivery_status="failed",
            error_message=f"wechat_kf send failed: {str(exc)[:200]}",
            response_payload={"secret_included": False},
            retryable=True,
        )
    errcode = int(send_body.get("errcode") or 0)
    if errcode != 0:
        return ChannelSendResult(
            status="failed",
            delivery_status="failed",
            error_message=f"wechat_kf provider error: {errcode} {send_body.get('errmsg') or ''}".strip(),
            response_payload={"provider_response": _safe_provider_response(send_body), "secret_included": False},
            retryable=errcode in {-1, 45009, 45047, 40001, 42001},
        )
    now = utc_now()
    draft.delivery_status = "sent"
    draft.sent_at = now
    draft.updated_at = now
    conversation = db.get(Conversation, draft.conversation_id)
    if conversation is not None:
        conversation.status = "bot_visiting"
        conversation.last_message_at = now
    return ChannelSendResult(
        status="succeeded",
        delivery_status="sent",
        external_message_id=str(send_body.get("msgid") or f"wechat-kf-{draft.id}"),
        response_payload={"provider_response": _safe_provider_response(send_body), "secret_included": False},
    )


def _safe_provider_response(payload: dict) -> dict:
    return {key: value for key, value in payload.items() if key not in {"access_token"}}


def send_outbox_draft(
    db: Session,
    *,
    draft: OutboxDraft,
    channel: Channel,
    connector: ChannelConnector,
) -> ChannelSendResult:
    provider = normalize_provider(connector.provider or channel.type)
    if provider == "website" or channel.type in {"website", "web"}:
        return _website_send(db, draft=draft, connector=connector)
    if provider in {"wechat_kf", "wecom"} or channel.type in {"wechat_kf", "wechat_customer_service", "wecom"}:
        return _wechat_kf_send(db, draft=draft, connector=connector)
    return ChannelSendResult(
        status="failed",
        delivery_status="not_sent",
        error_message=f"external sender not implemented for provider={provider}",
        response_payload={"provider": provider, "external_write": False},
        retryable=False,
    )
