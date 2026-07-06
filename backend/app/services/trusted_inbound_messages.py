from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.audit import add_audit_event
from app.models import Channel, ChannelDeliveryReceipt, Contact, Conversation, ConversationEvent, Message
from app.models.foundation import utc_now


@dataclass(frozen=True)
class TrustedInboundResult:
    status: str
    idempotency_status: str
    idempotency_key: str
    trusted_message_creation: bool = False
    trusted_message_id: int | None = None
    contact_id: int | None = None
    conversation_id: int | None = None
    next_action: str = "build_trusted_inbound_message_pipeline_before_creating_messages"
    detail: str = ""


def build_webhook_idempotency_key(
    *,
    provider: str,
    channel_id: int,
    provider_event_id: str,
    external_message_id: str,
) -> str:
    if provider_event_id:
        return f"provider_event:{provider}:{channel_id}:{provider_event_id}"
    if external_message_id:
        return f"external_message:{provider}:{channel_id}:{external_message_id}"
    return ""


def _pick_first_string(raw_payload: dict[str, Any], keys: tuple[str, ...]) -> str:
    for key in keys:
        value = raw_payload.get(key)
        if value is not None and value != "":
            return str(value)
    return ""


def _message_content(raw_payload: dict[str, Any]) -> str:
    return _pick_first_string(
        raw_payload,
        ("Content", "content", "Text", "text", "message_content", "message_text"),
    ).strip()


def _contact_external_id(raw_payload: dict[str, Any]) -> str:
    return _pick_first_string(
        raw_payload,
        (
            "FromUserName",
            "FromUserId",
            "external_userid",
            "external_user_id",
            "openid",
            "OpenID",
            "user_id",
            "visitor_id",
            "contact_external_id",
        ),
    ).strip()


def _contact_display_name(raw_payload: dict[str, Any], external_contact_id: str) -> str:
    value = _pick_first_string(
        raw_payload,
        ("SenderName", "sender_name", "nickname", "NickName", "visitor_name", "display_name"),
    ).strip()
    if value:
        return value[:120]
    if external_contact_id:
        return f"官方渠道访客 {external_contact_id}"[:120]
    return "官方渠道访客"


def _contact_lookup_key(provider: str, external_contact_id: str) -> str:
    return f"{provider}:{external_contact_id}"[:80]


def _find_existing_contact(
    db: Session,
    *,
    tenant_id: int,
    provider: str,
    external_contact_id: str,
) -> Contact | None:
    if not external_contact_id:
        return None
    return db.scalar(
        select(Contact).where(
            Contact.tenant_id == tenant_id,
            Contact.wechat == _contact_lookup_key(provider, external_contact_id),
        )
    )


def _get_or_create_contact(
    db: Session,
    *,
    tenant_id: int,
    provider: str,
    raw_payload: dict[str, Any],
) -> Contact | None:
    external_contact_id = _contact_external_id(raw_payload)
    if not external_contact_id:
        return None
    existing = _find_existing_contact(
        db,
        tenant_id=tenant_id,
        provider=provider,
        external_contact_id=external_contact_id,
    )
    if existing is not None:
        return existing
    contact = Contact(
        tenant_id=tenant_id,
        display_name=_contact_display_name(raw_payload, external_contact_id),
        wechat=_contact_lookup_key(provider, external_contact_id),
    )
    db.add(contact)
    db.flush()
    return contact


def _get_or_create_conversation(
    db: Session,
    *,
    tenant_id: int,
    channel: Channel,
    contact: Contact,
    provider: str,
) -> Conversation:
    existing = db.scalar(
        select(Conversation)
        .where(
            Conversation.tenant_id == tenant_id,
            Conversation.channel_id == channel.id,
            Conversation.contact_id == contact.id,
            Conversation.status != "closed",
        )
        .order_by(Conversation.last_message_at.desc(), Conversation.id.desc())
    )
    if existing is not None:
        return existing
    now = utc_now()
    conversation = Conversation(
        tenant_id=tenant_id,
        channel_id=channel.id,
        contact_id=contact.id,
        status="bot",
        priority="normal",
        subject=f"{channel.name} 入站咨询"[:180],
        last_message_at=now,
        created_at=now,
    )
    db.add(conversation)
    db.flush()
    db.add(
        ConversationEvent(
            conversation_id=conversation.id,
            event_type="conversation.created_from_trusted_webhook",
            payload=json.dumps(
                {
                    "provider": provider,
                    "channel_id": channel.id,
                    "contact_id": contact.id,
                },
                ensure_ascii=False,
            ),
        )
    )
    return conversation


def _message_from_existing_receipt(receipt: ChannelDeliveryReceipt) -> tuple[int | None, int | None, int | None]:
    parsed_event = (receipt.raw_payload or {}).get("parsed_event", {})
    message_id = parsed_event.get("trusted_message_id")
    conversation_id = parsed_event.get("conversation_id")
    contact_id = parsed_event.get("contact_id")
    return message_id, conversation_id, contact_id


def _find_duplicate_message(
    db: Session,
    *,
    tenant_id: int,
    channel_id: int,
    provider: str,
    provider_event_id: str,
    external_message_id: str,
) -> tuple[int | None, int | None, int | None]:
    conditions = [
        ChannelDeliveryReceipt.tenant_id == tenant_id,
        ChannelDeliveryReceipt.channel_id == channel_id,
        ChannelDeliveryReceipt.provider == provider,
        ChannelDeliveryReceipt.signature_validated.is_(True),
    ]
    if provider_event_id:
        conditions.append(ChannelDeliveryReceipt.provider_event_id == provider_event_id)
    elif external_message_id:
        conditions.append(ChannelDeliveryReceipt.external_message_id == external_message_id)
    else:
        return None, None, None
    receipt = db.scalar(select(ChannelDeliveryReceipt).where(*conditions).order_by(ChannelDeliveryReceipt.id.asc()))
    if receipt is not None:
        return _message_from_existing_receipt(receipt)
    if external_message_id:
        message = db.scalar(
            select(Message)
            .join(Conversation, Conversation.id == Message.conversation_id)
            .where(
                Conversation.tenant_id == tenant_id,
                Conversation.channel_id == channel_id,
                Message.external_message_id == external_message_id,
            )
            .order_by(Message.id.asc())
        )
        if message is not None:
            return message.id, message.conversation_id, None
    return None, None, None


def create_trusted_inbound_message_if_ready(
    db: Session,
    *,
    channel: Channel,
    provider: str,
    event_type: str,
    provider_event_id: str,
    external_message_id: str,
    raw_payload: dict[str, Any],
) -> TrustedInboundResult:
    idempotency_key = build_webhook_idempotency_key(
        provider=provider,
        channel_id=channel.id,
        provider_event_id=provider_event_id,
        external_message_id=external_message_id,
    )
    if event_type != "message":
        return TrustedInboundResult(
            status="verified_receipt_only",
            idempotency_status="not_message_event",
            idempotency_key=idempotency_key,
            next_action="map_provider_receipt_or_event_before_creating_message",
        )
    if not idempotency_key:
        return TrustedInboundResult(
            status="verified_receipt_only",
            idempotency_status="idempotency_key_missing",
            idempotency_key="",
            next_action="provide_provider_event_or_external_message_id_before_creating_message",
        )
    message_id, conversation_id, contact_id = _find_duplicate_message(
        db,
        tenant_id=channel.tenant_id,
        channel_id=channel.id,
        provider=provider,
        provider_event_id=provider_event_id,
        external_message_id=external_message_id,
    )
    if message_id is not None:
        add_audit_event(
            db,
            tenant_id=channel.tenant_id,
            actor_id=None,
            action="channel_webhook.duplicate_ignored",
            resource_type="message",
            resource_id=str(message_id),
            payload={
                "channel_id": channel.id,
                "provider": provider,
                "provider_event_id": provider_event_id,
                "external_message_id": external_message_id,
                "idempotency_key": idempotency_key,
            },
        )
        return TrustedInboundResult(
            status="duplicate_ignored",
            idempotency_status="duplicate_ignored",
            idempotency_key=idempotency_key,
            trusted_message_creation=False,
            trusted_message_id=message_id,
            contact_id=contact_id,
            conversation_id=conversation_id,
            next_action="duplicate_webhook_ignored",
        )

    content = _message_content(raw_payload)
    if not content:
        return TrustedInboundResult(
            status="verified_receipt_only",
            idempotency_status="message_content_missing",
            idempotency_key=idempotency_key,
            next_action="provide_supported_inbound_message_content_before_creating_message",
        )
    contact = _get_or_create_contact(db, tenant_id=channel.tenant_id, provider=provider, raw_payload=raw_payload)
    if contact is None:
        return TrustedInboundResult(
            status="verified_receipt_only",
            idempotency_status="contact_identity_missing",
            idempotency_key=idempotency_key,
            next_action="provide_contact_identity_before_creating_message",
        )
    conversation = _get_or_create_conversation(
        db,
        tenant_id=channel.tenant_id,
        channel=channel,
        contact=contact,
        provider=provider,
    )
    now = utc_now()
    message = Message(
        conversation_id=conversation.id,
        direction="inbound",
        sender_type="visitor",
        content=content,
        external_message_id=external_message_id,
        created_at=now,
    )
    conversation.last_message_at = now
    db.add(message)
    db.flush()
    event_payload = {
        "provider": provider,
        "channel_id": channel.id,
        "provider_event_id": provider_event_id,
        "external_message_id": external_message_id,
        "idempotency_key": idempotency_key,
        "trusted_message_id": message.id,
    }
    db.add(
        ConversationEvent(
            conversation_id=conversation.id,
            event_type="message.inbound.trusted_webhook",
            payload=json.dumps(event_payload, ensure_ascii=False),
        )
    )
    add_audit_event(
        db,
        tenant_id=channel.tenant_id,
        actor_id=None,
        action="channel_webhook.trusted_inbound_message_created",
        resource_type="message",
        resource_id=str(message.id),
        payload=event_payload,
    )
    return TrustedInboundResult(
        status="trusted_inbound_message_created",
        idempotency_status="created",
        idempotency_key=idempotency_key,
        trusted_message_creation=True,
        trusted_message_id=message.id,
        contact_id=contact.id,
        conversation_id=conversation.id,
        next_action="queue_trusted_inbound_message_for_reply_orchestration",
    )
