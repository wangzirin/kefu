from fastapi import HTTPException, status
import hmac
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.audit import add_audit_event
from app.core.auth import CurrentPrincipal
from app.models import (
    Channel,
    ChannelAccount,
    ChannelConnector,
    ChannelDeliveryReceipt,
    Contact,
    Conversation,
    DeliveryFailureReview,
    Message,
    OutboxDraft,
    OutboxSendAttempt,
    Tenant,
    WorkflowRun,
)
from app.models.foundation import utc_now
from app.schemas.channel_connectors import (
    ChannelConnectorConfigCreate,
    ChannelAccountCreate,
    ChannelDeliveryReceiptCreate,
    ChannelWebhookEventCreate,
    ConnectorSendPlanCreate,
    WebsiteWidgetMessageCreate,
)
from app.services.channel_provider_registry import (
    get_channel_provider_contract,
    list_channel_provider_contracts,
    normalize_provider,
)
from app.services.channel_secret_store import connector_secret_status, resolve_webhook_secret_material
from app.services.channel_webhook_verifier import verify_channel_webhook_request
from app.services.wecom_callback_crypto import (
    WecomCallbackCryptoError,
    decrypt_wecom_payload,
    extract_wecom_encrypt_from_xml,
    parse_wecom_xml,
)
from app.services.delivery_failures import attach_delivery_normalization_and_review
from app.services.trusted_inbound_messages import TrustedInboundResult, create_trusted_inbound_message_if_ready


READY_TO_SEND = "ready_to_send"
NOT_SENT = "not_sent"
CONNECTOR_NOOP = "connector_noop"
BLOCKED = "blocked"
SENSITIVE_CONFIG_KEYS = ("secret", "token", "password", "private", "aeskey", "encodingaeskey", "app_key")
SENSITIVE_WEBHOOK_PAYLOAD_KEYS = (
    "authorization",
    "cookie",
    "msg_signature",
    "signature",
    "token",
    "password",
    "secret",
    "app_secret",
    "encrypt",
)


def _resolve_website_widget_tenant(
    db: Session,
    *,
    tenant_id: int | None,
    tenant_slug: str = "",
) -> Tenant:
    tenant = None
    if tenant_id is not None:
        tenant = db.get(Tenant, tenant_id)
    if tenant is None and tenant_slug:
        tenant = db.scalar(select(Tenant).where(Tenant.slug == tenant_slug))
    if tenant is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="tenant not found")
    return tenant


def _find_website_widget_contact(db: Session, *, tenant_id: int, visitor_id: str) -> Contact | None:
    clean_visitor_id = visitor_id.strip()
    if not clean_visitor_id:
        return None
    return db.scalar(
        select(Contact).where(
            Contact.tenant_id == tenant_id,
            Contact.wechat == f"website:{clean_visitor_id}"[:80],
        )
    )


def _find_latest_website_widget_conversation(
    db: Session,
    *,
    tenant_id: int,
    contact_id: int,
) -> Conversation | None:
    return db.scalar(
        select(Conversation)
        .join(Channel, Channel.id == Conversation.channel_id)
        .where(
            Conversation.tenant_id == tenant_id,
            Conversation.contact_id == contact_id,
            Channel.type == "website",
        )
        .order_by(Conversation.last_message_at.desc(), Conversation.id.desc())
    )


def _require_channel_for_principal(db: Session, channel_id: int, principal: CurrentPrincipal) -> Channel:
    channel = db.get(Channel, channel_id)
    if channel is None or channel.tenant_id != principal.tenant.id:
        raise HTTPException(status_code=404, detail="channel not found")
    return channel


def _sanitize_public_config(public_config: dict) -> dict:
    sanitized = {}
    for key, value in public_config.items():
        lowered = str(key).lower()
        if any(marker in lowered for marker in SENSITIVE_CONFIG_KEYS):
            sanitized[key] = "[redacted]"
            continue
        sanitized[key] = value
    return sanitized


def _sanitize_webhook_payload(value):
    if isinstance(value, dict):
        sanitized = {}
        for key, item in value.items():
            lowered = str(key).lower()
            if any(marker in lowered for marker in SENSITIVE_WEBHOOK_PAYLOAD_KEYS):
                sanitized[key] = "[redacted]"
                continue
            sanitized[key] = _sanitize_webhook_payload(item)
        return sanitized
    if isinstance(value, list):
        return [_sanitize_webhook_payload(item) for item in value]
    return value


def _get_channel_connector(db: Session, channel: Channel) -> ChannelConnector | None:
    return db.scalar(
        select(ChannelConnector).where(
            ChannelConnector.tenant_id == channel.tenant_id,
            ChannelConnector.channel_id == channel.id,
        )
    )


def list_channel_provider_registry() -> list[dict]:
    return list_channel_provider_contracts()


def configure_channel_connector(
    db: Session,
    *,
    channel_id: int,
    payload: ChannelConnectorConfigCreate,
    principal: CurrentPrincipal,
) -> ChannelConnector:
    channel = _require_channel_for_principal(db, channel_id, principal)
    now = utc_now()
    connector = _get_channel_connector(db, channel)
    if connector is None:
        connector = ChannelConnector(
            tenant_id=channel.tenant_id,
            channel_id=channel.id,
            created_by_id=principal.user.id,
            created_at=now,
        )
        db.add(connector)
    connector.provider = payload.provider
    connector.mode = payload.mode
    connector.status = payload.status
    connector.display_name = payload.display_name
    connector.capabilities = payload.capabilities
    sanitized_public_config = _sanitize_public_config(payload.public_config)
    connector.public_config = sanitized_public_config
    connector.webhook_path = payload.webhook_path
    connector.signature_mode = payload.signature_mode
    connector.secret_status = connector_secret_status(provider=payload.provider, public_config=sanitized_public_config)
    connector.external_write_enabled = False
    connector.updated_by_id = principal.user.id
    connector.updated_at = now
    db.flush()
    add_audit_event(
        db,
        tenant_id=connector.tenant_id,
        actor_id=principal.user.id,
        action="channel_connector.configured",
        resource_type="channel_connector",
        resource_id=str(connector.id),
        payload={
            "channel_id": connector.channel_id,
            "provider": connector.provider,
            "mode": connector.mode,
            "status": connector.status,
            "external_write_enabled": False,
            "secret_status": connector.secret_status,
        },
    )
    db.commit()
    db.refresh(connector)
    return connector


def get_channel_connector(
    db: Session,
    *,
    channel_id: int,
    principal: CurrentPrincipal,
) -> ChannelConnector:
    channel = _require_channel_for_principal(db, channel_id, principal)
    connector = _get_channel_connector(db, channel)
    if connector is None:
        raise HTTPException(status_code=404, detail="channel connector not found")
    return connector


def list_channel_accounts(
    db: Session,
    *,
    tenant_id: int,
    principal: CurrentPrincipal,
) -> list[ChannelAccount]:
    if tenant_id != principal.tenant.id:
        raise HTTPException(status_code=404, detail="tenant not found")
    query = (
        select(ChannelAccount)
        .where(ChannelAccount.tenant_id == tenant_id)
        .order_by(ChannelAccount.channel_id, ChannelAccount.id)
    )
    return list(db.scalars(query).all())


def configure_channel_account(
    db: Session,
    *,
    channel_id: int,
    payload: ChannelAccountCreate,
    principal: CurrentPrincipal,
) -> ChannelAccount:
    channel = _require_channel_for_principal(db, channel_id, principal)
    connector: ChannelConnector | None = None
    if payload.connector_id is not None:
        connector = db.get(ChannelConnector, payload.connector_id)
        if connector is None or connector.tenant_id != channel.tenant_id or connector.channel_id != channel.id:
            raise HTTPException(status_code=404, detail="channel connector not found")
    now = utc_now()
    account_name = payload.account_name.strip()
    entrypoint_name = payload.entrypoint_name.strip()
    account = db.scalar(
        select(ChannelAccount).where(
            ChannelAccount.tenant_id == channel.tenant_id,
            ChannelAccount.channel_id == channel.id,
            ChannelAccount.account_name == account_name,
            ChannelAccount.entrypoint_name == entrypoint_name,
        )
    )
    if account is None:
        account = ChannelAccount(
            tenant_id=channel.tenant_id,
            channel_id=channel.id,
            account_name=account_name,
            entrypoint_name=entrypoint_name,
            created_by_id=principal.user.id,
            created_at=now,
        )
        db.add(account)
    account.connector_id = connector.id if connector else payload.connector_id
    account.provider = payload.provider.strip() or (connector.provider if connector else channel.type)
    account.platform = payload.platform.strip() or channel.name or channel.type
    account.external_account_id = payload.external_account_id.strip()
    account.store_name = payload.store_name.strip()
    account.authorization_status = payload.authorization_status
    account.access_status = payload.access_status
    account.reply_mode = payload.reply_mode
    account.health_status = payload.health_status
    account.public_profile = _sanitize_public_config(payload.public_profile)
    account.updated_by_id = principal.user.id
    account.updated_at = now
    db.flush()
    add_audit_event(
        db,
        tenant_id=account.tenant_id,
        actor_id=principal.user.id,
        action="channel_account.configured",
        resource_type="channel_account",
        resource_id=str(account.id),
        payload={
            "channel_id": account.channel_id,
            "connector_id": account.connector_id,
            "provider": account.provider,
            "platform": account.platform,
            "authorization_status": account.authorization_status,
            "access_status": account.access_status,
            "reply_mode": account.reply_mode,
            "external_write_enabled": False,
        },
    )
    db.commit()
    db.refresh(account)
    return account


def _next_attempt_number(db: Session, draft_id: int) -> int:
    current = db.scalar(
        select(func.max(OutboxSendAttempt.attempt_number)).where(OutboxSendAttempt.outbox_draft_id == draft_id)
    )
    return (current or 0) + 1


def _update_workflow_connector_plan_state(db: Session, *, draft: OutboxDraft, attempt: OutboxSendAttempt) -> None:
    if draft.source_workflow_run_id is None:
        return
    run = db.get(WorkflowRun, draft.source_workflow_run_id)
    if run is None:
        return
    run.state_payload = {
        **(run.state_payload or {}),
        "connector_send_plan": {
            "attempt_id": attempt.id,
            "outbox_draft_id": attempt.outbox_draft_id,
            "provider": attempt.provider,
            "delivery_mode": attempt.delivery_mode,
            "status": attempt.status,
            "delivery_status": attempt.delivery_status,
            "external_write": False,
            "finished_at": attempt.finished_at.isoformat() if attempt.finished_at else "",
        },
    }


def create_connector_send_plan(
    db: Session,
    *,
    draft_id: int,
    payload: ConnectorSendPlanCreate,
    principal: CurrentPrincipal,
) -> OutboxSendAttempt:
    draft = db.get(OutboxDraft, draft_id)
    if draft is None or draft.tenant_id != principal.tenant.id:
        raise HTTPException(status_code=404, detail="outbox draft not found")
    if draft.status != READY_TO_SEND:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="outbox draft must be ready to send")
    channel = _require_channel_for_principal(db, draft.channel_id, principal)
    connector = _get_channel_connector(db, channel)
    if connector is None or connector.status != "ready":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="channel connector must be configured")
    idempotency_key = payload.idempotency_key or f"connector_send_plan:{draft.id}:{connector.id}"
    duplicate = db.scalar(
        select(OutboxSendAttempt).where(
            OutboxSendAttempt.tenant_id == draft.tenant_id,
            OutboxSendAttempt.idempotency_key == idempotency_key,
        )
    )
    if duplicate is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="connector send plan already exists")

    now = utc_now()
    attempt_number = _next_attempt_number(db, draft.id)
    signature_required = connector.signature_mode not in {"", "none", "not_configured"}
    request_payload = {
        "external_write": False,
        "delivery_mode": CONNECTOR_NOOP,
        "connector": {
            "id": connector.id,
            "provider": connector.provider,
            "mode": connector.mode,
            "status": connector.status,
            "external_write_enabled": connector.external_write_enabled,
        },
        "channel": {
            "id": channel.id,
            "type": channel.type,
            "name": channel.name,
        },
        "payload_preview": {
            "conversation_id": draft.conversation_id,
            "contact_id": draft.contact_id,
            "text": draft.reply_text,
        },
    }
    response_payload = {
        "external_write": False,
        "official_api_enabled": False,
        "blocked_reasons": ["external_delivery_disabled"],
        "next_action": "configure_official_authorization_before_external_write",
        "receipt_contract": {
            "status": "placeholder",
            "requires_external_message_id": True,
            "webhook_path": connector.webhook_path,
        },
        "retry_contract": {
            "queue": "not_configured",
            "retry_policy": "placeholder_only",
        },
        "webhook_requirements": {
            "signature_required": signature_required,
            "signature_mode": connector.signature_mode,
            "webhook_path": connector.webhook_path,
        },
    }
    attempt = OutboxSendAttempt(
        tenant_id=draft.tenant_id,
        outbox_draft_id=draft.id,
        conversation_id=draft.conversation_id,
        channel_id=draft.channel_id,
        contact_id=draft.contact_id,
        attempt_number=attempt_number,
        delivery_mode=CONNECTOR_NOOP,
        provider=connector.provider,
        status=BLOCKED,
        delivery_status=NOT_SENT,
        idempotency_key=idempotency_key,
        external_message_id="",
        request_payload=request_payload,
        response_payload=response_payload,
        error_message="official channel connector external write is disabled",
        operator_note=payload.operator_note,
        created_by_id=principal.user.id,
        started_at=now,
        finished_at=now,
        sent_at=None,
    )
    db.add(attempt)
    db.flush()
    draft.updated_at = now
    _update_workflow_connector_plan_state(db, draft=draft, attempt=attempt)
    add_audit_event(
        db,
        tenant_id=attempt.tenant_id,
        actor_id=principal.user.id,
        action="channel_connector.send_plan_created",
        resource_type="outbox_send_attempt",
        resource_id=str(attempt.id),
        payload={
            "outbox_draft_id": attempt.outbox_draft_id,
            "channel_id": attempt.channel_id,
            "provider": attempt.provider,
            "delivery_mode": attempt.delivery_mode,
            "external_write": False,
        },
    )
    db.commit()
    db.refresh(attempt)
    return attempt


def create_channel_delivery_receipt(
    db: Session,
    *,
    channel_id: int,
    payload: ChannelDeliveryReceiptCreate,
    principal: CurrentPrincipal,
) -> ChannelDeliveryReceipt:
    channel = _require_channel_for_principal(db, channel_id, principal)
    connector = _get_channel_connector(db, channel)
    if connector is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="channel connector must be configured")
    matched_attempt = None
    if payload.external_message_id:
        matched_attempt = db.scalar(
            select(OutboxSendAttempt).where(
                OutboxSendAttempt.tenant_id == channel.tenant_id,
                OutboxSendAttempt.provider == payload.provider,
                OutboxSendAttempt.external_message_id == payload.external_message_id,
            )
        )
    receipt = ChannelDeliveryReceipt(
        tenant_id=channel.tenant_id,
        channel_id=channel.id,
        connector_id=connector.id,
        matched_attempt_id=matched_attempt.id if matched_attempt else None,
        provider=payload.provider,
        external_message_id=payload.external_message_id,
        delivery_status=payload.delivery_status,
        provider_event_id=payload.provider_event_id,
        verification_status="not_verified_placeholder",
        signature_validated=False,
        raw_payload=payload.raw_payload,
        received_at=utc_now(),
    )
    db.add(receipt)
    db.flush()
    review = attach_delivery_normalization_and_review(db, receipt=receipt, actor_id=principal.user.id)
    add_audit_event(
        db,
        tenant_id=receipt.tenant_id,
        actor_id=principal.user.id,
        action="channel_delivery_receipt.placeholder_recorded",
        resource_type="channel_delivery_receipt",
        resource_id=str(receipt.id),
        payload={
            "channel_id": receipt.channel_id,
            "provider": receipt.provider,
            "delivery_status": receipt.delivery_status,
            "normalized_status": receipt.normalized_status,
            "needs_review": receipt.needs_review,
            "failure_review_id": review.id if review else None,
            "verification_status": receipt.verification_status,
            "matched_attempt_id": receipt.matched_attempt_id,
        },
    )
    db.commit()
    db.refresh(receipt)
    return receipt


def _require_webhook_connector(
    db: Session,
    *,
    provider: str,
    channel_id: int,
) -> tuple[Channel, ChannelConnector, dict]:
    contract = get_channel_provider_contract(provider)
    if contract is None:
        raise HTTPException(status_code=404, detail="channel provider not found")
    channel = db.get(Channel, channel_id)
    if channel is None:
        raise HTTPException(status_code=404, detail="channel webhook connector not found")
    connector = _get_channel_connector(db, channel)
    if connector is None or normalize_provider(connector.provider) != contract["provider"]:
        raise HTTPException(status_code=404, detail="channel webhook connector not found")
    return channel, connector, contract


def _webhook_verification_http_status(verification_status: str) -> int:
    if verification_status in {"signature_invalid", "timestamp_expired"}:
        return status.HTTP_403_FORBIDDEN
    if verification_status in {"secret_not_configured", "secret_reference_unresolved", "secret_env_missing_fields"}:
        return status.HTTP_503_SERVICE_UNAVAILABLE
    return status.HTTP_400_BAD_REQUEST


def _resolve_connector_secret_or_raise(connector: ChannelConnector):
    secret_resolution = resolve_webhook_secret_material(
        provider=connector.provider,
        public_config=connector.public_config,
    )
    if secret_resolution.material is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="wecom webhook secret is not configured",
        )
    return secret_resolution.material


def verify_wecom_callback_url(
    db: Session,
    *,
    channel_id: int,
    query_params: dict[str, str],
) -> str:
    _channel, connector, _contract = _require_webhook_connector(db, provider="wecom", channel_id=channel_id)
    encrypted_echo = str(query_params.get("echostr", "")).strip()
    if not encrypted_echo:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="echostr is required")
    verification = verify_channel_webhook_request(
        connector=connector,
        raw_payload={"Encrypt": encrypted_echo},
        query_params=query_params,
    )
    if not verification.signature_validated:
        raise HTTPException(
            status_code=_webhook_verification_http_status(verification.status),
            detail="wecom callback url verification failed",
        )
    material = _resolve_connector_secret_or_raise(connector)
    try:
        decrypted = decrypt_wecom_payload(
            encrypted_text=encrypted_echo,
            encoding_aes_key=material.encoding_aes_key,
            expected_receiver_id=material.receiver_id,
        )
    except WecomCallbackCryptoError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="wecom callback url decrypt failed",
        ) from exc
    return decrypted.plaintext


def _provider_event_id_from_wecom_payload(raw_payload: dict) -> str:
    return _pick_first_string(raw_payload, ("EventID", "event_id", "MsgId", "MsgID"))


def _event_type_from_wecom_payload(raw_payload: dict) -> str:
    if _pick_first_string(raw_payload, ("MsgType", "msgtype")).lower() == "text":
        return "message"
    if _pick_first_string(raw_payload, ("Content", "content")):
        return "message"
    if _pick_first_string(raw_payload, ("Event", "event")):
        return "customer_event"
    return "message"


def receive_wecom_official_xml_webhook(
    db: Session,
    *,
    channel_id: int,
    xml_body: str,
    query_params: dict[str, str],
) -> dict:
    _channel, connector, _contract = _require_webhook_connector(db, provider="wecom", channel_id=channel_id)
    try:
        outer_payload = parse_wecom_xml(xml_body)
        encrypt = extract_wecom_encrypt_from_xml(xml_body)
    except WecomCallbackCryptoError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="wecom xml payload is invalid") from exc

    verification = verify_channel_webhook_request(
        connector=connector,
        raw_payload={"Encrypt": encrypt},
        query_params=query_params,
    )
    if not verification.signature_validated:
        raise HTTPException(
            status_code=_webhook_verification_http_status(verification.status),
            detail="wecom xml webhook signature verification failed",
        )
    material = _resolve_connector_secret_or_raise(connector)
    try:
        decrypted = decrypt_wecom_payload(
            encrypted_text=encrypt,
            encoding_aes_key=material.encoding_aes_key,
            expected_receiver_id=material.receiver_id,
        )
        raw_payload = parse_wecom_xml(decrypted.plaintext)
    except WecomCallbackCryptoError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="wecom xml decrypt failed") from exc

    raw_payload = {
        **raw_payload,
        "Encrypt": encrypt,
        "_official_xml_decrypted": True,
        "_outer_to_user_name_present": bool(outer_payload.get("ToUserName")),
        "_decrypted_receiver_id_matches": bool(
            not material.receiver_id or hmac.compare_digest(decrypted.receiver_id, material.receiver_id)
        ),
    }
    payload = ChannelWebhookEventCreate(
        event_type=_event_type_from_wecom_payload(raw_payload),
        external_message_id=_pick_first_string(raw_payload, ("MsgID", "MsgId")),
        delivery_status="received",
        provider_event_id=_provider_event_id_from_wecom_payload(raw_payload),
        raw_payload=raw_payload,
    )
    return receive_channel_webhook_event(
        db,
        provider="wecom",
        channel_id=channel_id,
        payload=payload,
        query_params=query_params,
    )


def _pick_first_string(raw_payload: dict, keys: tuple[str, ...]) -> str:
    for key in keys:
        value = raw_payload.get(key)
        if value is not None and value != "":
            return str(value)
    return ""


def _empty_trusted_inbound_result(next_action: str) -> TrustedInboundResult:
    return TrustedInboundResult(
        status="placeholder_only",
        idempotency_status="not_evaluated",
        idempotency_key="",
        next_action=next_action,
    )


def receive_channel_webhook_event(
    db: Session,
    *,
    provider: str,
    channel_id: int,
    payload: ChannelWebhookEventCreate,
    query_params: dict[str, str],
) -> dict:
    channel, connector, contract = _require_webhook_connector(db, provider=provider, channel_id=channel_id)
    verification = verify_channel_webhook_request(
        connector=connector,
        raw_payload=payload.raw_payload,
        query_params=query_params,
    )

    external_message_id = payload.external_message_id or _pick_first_string(
        payload.raw_payload,
        ("MsgID", "MsgId", "msgid", "message_id", "external_message_id", "id"),
    )
    delivery_status = payload.delivery_status or _pick_first_string(
        payload.raw_payload,
        ("Status", "status", "delivery_status"),
    )
    provider_event_id = payload.provider_event_id or _pick_first_string(
        payload.raw_payload,
        ("EventID", "event_id", "provider_event_id"),
    )
    matched_attempt = None
    if external_message_id:
        matched_attempt = db.scalar(
            select(OutboxSendAttempt).where(
                OutboxSendAttempt.tenant_id == channel.tenant_id,
                OutboxSendAttempt.provider == contract["provider"],
                OutboxSendAttempt.external_message_id == external_message_id,
            )
        )
    trusted_inbound = _empty_trusted_inbound_result(verification.next_action)
    if verification.signature_validated:
        trusted_inbound = create_trusted_inbound_message_if_ready(
            db,
            channel=channel,
            provider=contract["provider"],
            event_type=payload.event_type,
            provider_event_id=provider_event_id,
            external_message_id=external_message_id,
            raw_payload=payload.raw_payload,
        )
    parsed_event_status = trusted_inbound.status if verification.signature_validated else "placeholder_only"
    parsed_event = {
        "status": parsed_event_status,
        "trusted": verification.signature_validated,
        "trusted_message_creation": trusted_inbound.trusted_message_creation,
        "trusted_message_id": trusted_inbound.trusted_message_id,
        "contact_id": trusted_inbound.contact_id,
        "conversation_id": trusted_inbound.conversation_id,
        "idempotency_status": trusted_inbound.idempotency_status,
        "idempotency_key": trusted_inbound.idempotency_key,
        "event_type": payload.event_type,
        "external_message_id": external_message_id,
        "delivery_status": delivery_status,
        "provider_event_id": provider_event_id,
        "raw_payload_keys": sorted(payload.raw_payload.keys()),
    }
    stored_payload = {
        "payload": _sanitize_webhook_payload(payload.raw_payload),
        "webhook_intake": {
            "provider": contract["provider"],
            "event_type": payload.event_type,
            "signature_mode": connector.signature_mode,
            "query_keys": sorted(query_params.keys()),
            "signature_values_stored": False,
            "secret_status": connector.secret_status,
            "verification_status": verification.status,
            "verification_method": verification.method,
            "verification_detail": verification.detail,
            "official_xml_decrypted": bool(payload.raw_payload.get("_official_xml_decrypted")),
            "registry_contract_status": contract["verification_contract"]["production_status"],
            "trusted_message_creation": trusted_inbound.trusted_message_creation,
            "trusted_message_id": trusted_inbound.trusted_message_id,
            "conversation_id": trusted_inbound.conversation_id,
            "idempotency_status": trusted_inbound.idempotency_status,
            "idempotency_key": trusted_inbound.idempotency_key,
        },
        "parsed_event": parsed_event,
    }
    receipt = ChannelDeliveryReceipt(
        tenant_id=channel.tenant_id,
        channel_id=channel.id,
        connector_id=connector.id,
        matched_attempt_id=matched_attempt.id if matched_attempt else None,
        provider=contract["provider"],
        external_message_id=external_message_id,
        delivery_status=delivery_status,
        provider_event_id=provider_event_id,
        verification_status=verification.status,
        signature_validated=verification.signature_validated,
        raw_payload=stored_payload,
        received_at=utc_now(),
    )
    db.add(receipt)
    db.flush()
    review = attach_delivery_normalization_and_review(db, receipt=receipt, actor_id=None)
    add_audit_event(
        db,
        tenant_id=receipt.tenant_id,
        actor_id=None,
        action="channel_webhook.placeholder_received",
        resource_type="channel_delivery_receipt",
        resource_id=str(receipt.id),
        payload={
            "channel_id": receipt.channel_id,
            "connector_id": receipt.connector_id,
            "provider": receipt.provider,
            "event_type": payload.event_type,
            "delivery_status": receipt.delivery_status,
            "normalized_status": receipt.normalized_status,
            "needs_review": receipt.needs_review,
            "failure_review_id": review.id if review else None,
            "verification_status": receipt.verification_status,
            "signature_validated": receipt.signature_validated,
            "external_write": False,
            "verification_method": verification.method,
            "trusted_message_creation": trusted_inbound.trusted_message_creation,
            "trusted_message_id": trusted_inbound.trusted_message_id,
            "idempotency_status": trusted_inbound.idempotency_status,
        },
    )
    db.commit()
    db.refresh(receipt)
    return {
        "tenant_id": receipt.tenant_id,
        "channel_id": receipt.channel_id,
        "connector_id": connector.id,
        "receipt_id": receipt.id,
        "provider": receipt.provider,
        "event_type": payload.event_type,
        "external_message_id": receipt.external_message_id,
        "delivery_status": receipt.delivery_status,
        "provider_status": receipt.provider_status,
        "provider_error_code": receipt.provider_error_code,
        "normalized_status": receipt.normalized_status,
        "retryable": receipt.retryable,
        "needs_review": receipt.needs_review,
        "next_action": receipt.next_action,
        "provider_event_id": receipt.provider_event_id,
        "verification_status": receipt.verification_status,
        "signature_validated": receipt.signature_validated,
        "external_write": False,
        "parsed_event": parsed_event,
        "registry_contract": contract,
        "next_action": trusted_inbound.next_action if verification.signature_validated else verification.next_action,
    }


def receive_website_widget_message(
    db: Session,
    *,
    payload: WebsiteWidgetMessageCreate,
) -> dict:
    tenant = _resolve_website_widget_tenant(db, tenant_id=payload.tenant_id, tenant_slug=payload.tenant_slug)

    channel = db.scalar(
        select(Channel).where(
            Channel.tenant_id == tenant.id,
            Channel.type == "website",
            Channel.name == "网站客服",
        )
    )
    if channel is None:
        channel = Channel(
            tenant_id=tenant.id,
            type="website",
            name="网站客服",
            reply_mode="assist",
            status="active",
        )
        db.add(channel)
        db.flush()

    message_index = int(utc_now().timestamp() * 1000)
    visitor_id = payload.visitor_id.strip() or f"website-visitor-{message_index}"
    existing_contact = _find_website_widget_contact(db, tenant_id=tenant.id, visitor_id=visitor_id)
    existing_conversation = (
        _find_latest_website_widget_conversation(db, tenant_id=tenant.id, contact_id=existing_contact.id)
        if existing_contact is not None
        else None
    )
    reopen_action = payload.reopen_action.strip()
    if existing_conversation is not None and existing_conversation.status == "closed" and not reopen_action:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="conversation closed",
        )
    is_new_conversation = existing_conversation is None or existing_conversation.status == "closed"
    raw_payload = {
        "message_id": f"website-widget-{tenant.id}-{payload.component_id}-{message_index}",
        "visitor_id": visitor_id,
        "visitor_name": payload.visitor_name.strip() or "网站访客",
        "text": payload.text.strip(),
        "component_id": payload.component_id,
        "page_url": payload.page_url,
        "page_title": payload.page_title,
        "reopen_action": reopen_action,
    }
    trusted_inbound = create_trusted_inbound_message_if_ready(
        db,
        channel=channel,
        provider="website",
        event_type="message",
        provider_event_id=raw_payload["message_id"],
        external_message_id=raw_payload["message_id"],
        raw_payload=raw_payload,
    )
    greeting_message_id = None
    if (
        reopen_action == "continue_chat"
        and trusted_inbound.conversation_id is not None
        and trusted_inbound.status == "trusted_inbound_message_created"
    ):
        greeting = Message(
            conversation_id=trusted_inbound.conversation_id,
            direction="outbound",
            sender_type="agent",
            content="您好，已为您重新接入客服，请问还有什么可以帮您？",
            external_message_id=f"website-widget-greeting-{tenant.id}-{trusted_inbound.conversation_id}-{message_index}",
            created_at=utc_now(),
        )
        db.add(greeting)
        db.flush()
        greeting_message_id = greeting.id
        conversation = db.get(Conversation, trusted_inbound.conversation_id)
        if conversation is not None:
            conversation.last_message_at = greeting.created_at
    add_audit_event(
        db,
        tenant_id=tenant.id,
        actor_id=None,
        action="website_widget.public_message_received",
        resource_type="conversation",
        resource_id=str(trusted_inbound.conversation_id or ""),
        payload={
            "channel_id": channel.id,
            "component_id": payload.component_id,
            "trusted_message_id": trusted_inbound.trusted_message_id,
            "conversation_id": trusted_inbound.conversation_id,
            "reopen_action": reopen_action,
            "greeting_message_id": greeting_message_id,
            "external_write": False,
        },
    )
    db.commit()
    conversation_status = ""
    if trusted_inbound.conversation_id is not None:
        conversation = db.get(Conversation, trusted_inbound.conversation_id)
        conversation_status = conversation.status if conversation is not None else ""
    return {
        "tenant_id": tenant.id,
        "channel_id": channel.id,
        "contact_id": trusted_inbound.contact_id,
        "conversation_id": trusted_inbound.conversation_id,
        "message_id": trusted_inbound.trusted_message_id,
        "status": trusted_inbound.status,
        "next_action": trusted_inbound.next_action,
        "is_new_conversation": is_new_conversation,
        "conversation_status": conversation_status,
    }


def list_website_widget_conversation_messages(
    db: Session,
    *,
    tenant_id: int | None,
    tenant_slug: str = "",
    visitor_id: str,
    after_id: int = 0,
) -> dict:
    tenant = _resolve_website_widget_tenant(db, tenant_id=tenant_id, tenant_slug=tenant_slug)
    clean_visitor_id = visitor_id.strip()
    if not clean_visitor_id:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="visitor_id required")

    contact = _find_website_widget_contact(db, tenant_id=tenant.id, visitor_id=clean_visitor_id)
    if contact is None:
        return {
            "tenant_id": tenant.id,
            "channel_id": None,
            "contact_id": None,
            "conversation_id": None,
            "conversation_status": "",
            "messages": [],
        }

    conversation = _find_latest_website_widget_conversation(db, tenant_id=tenant.id, contact_id=contact.id)
    if conversation is None:
        return {
            "tenant_id": tenant.id,
            "channel_id": None,
            "contact_id": contact.id,
            "conversation_id": None,
            "conversation_status": "",
            "messages": [],
        }

    messages = list(
        db.scalars(
            select(Message)
            .where(
                Message.conversation_id == conversation.id,
                Message.id > after_id,
                Message.direction == "outbound",
            )
            .order_by(Message.id.asc())
            .limit(50)
        ).all()
    )
    return {
        "tenant_id": tenant.id,
        "channel_id": conversation.channel_id,
        "contact_id": contact.id,
        "conversation_id": conversation.id,
        "conversation_status": conversation.status,
        "messages": messages,
    }


def list_channel_delivery_receipts(
    db: Session,
    *,
    channel_id: int,
    principal: CurrentPrincipal,
) -> list[ChannelDeliveryReceipt]:
    channel = _require_channel_for_principal(db, channel_id, principal)
    query = (
        select(ChannelDeliveryReceipt)
        .where(ChannelDeliveryReceipt.tenant_id == channel.tenant_id, ChannelDeliveryReceipt.channel_id == channel.id)
        .order_by(ChannelDeliveryReceipt.received_at.desc(), ChannelDeliveryReceipt.id.desc())
    )
    return list(db.scalars(query).all())


def _rate(count: int, total: int) -> float | None:
    if total <= 0:
        return None
    return round(count / total, 4)


def _receipt_gate(
    *,
    key: str,
    label: str,
    status_value: str,
    detail: str,
    stop_condition: str,
) -> dict:
    return {
        "key": key,
        "label": label,
        "status": status_value,
        "detail": detail,
        "stop_condition": stop_condition,
    }


def get_online_receipt_quality_summary(
    db: Session,
    *,
    tenant_id: int,
    principal: CurrentPrincipal,
) -> dict:
    if tenant_id != principal.tenant.id:
        raise HTTPException(status_code=404, detail="tenant not found")

    receipts = list(
        db.scalars(
            select(ChannelDeliveryReceipt)
            .where(ChannelDeliveryReceipt.tenant_id == tenant_id)
            .order_by(ChannelDeliveryReceipt.received_at.desc(), ChannelDeliveryReceipt.id.desc())
        ).all()
    )
    failure_reviews = list(
        db.scalars(select(DeliveryFailureReview).where(DeliveryFailureReview.tenant_id == tenant_id)).all()
    )
    total = len(receipts)
    status_counts: dict[str, int] = {}
    provider_counts: dict[str, dict[str, int]] = {}
    for receipt in receipts:
        normalized_status = receipt.normalized_status or "unknown"
        status_counts[normalized_status] = status_counts.get(normalized_status, 0) + 1
        provider = receipt.provider or "unknown"
        provider_row = provider_counts.setdefault(
            provider,
            {
                "receipt_count": 0,
                "matched_receipts": 0,
                "verified_receipts": 0,
                "delivered_or_read": 0,
                "needs_review": 0,
                "unknown_receipts": 0,
            },
        )
        provider_row["receipt_count"] += 1
        if receipt.matched_attempt_id is not None:
            provider_row["matched_receipts"] += 1
        if receipt.signature_validated and receipt.verification_status == "signature_validated":
            provider_row["verified_receipts"] += 1
        if normalized_status in {"delivered", "read"}:
            provider_row["delivered_or_read"] += 1
        if receipt.needs_review:
            provider_row["needs_review"] += 1
        if normalized_status in {"unknown", "unknown_provider_status"}:
            provider_row["unknown_receipts"] += 1

    matched = sum(1 for receipt in receipts if receipt.matched_attempt_id is not None)
    verified = sum(
        1
        for receipt in receipts
        if receipt.signature_validated and receipt.verification_status == "signature_validated"
    )
    delivered_or_read = sum(1 for receipt in receipts if receipt.normalized_status in {"delivered", "read"})
    failed_or_review = sum(1 for receipt in receipts if receipt.needs_review)
    unknown_receipts = sum(
        1
        for receipt in receipts
        if (receipt.normalized_status or "unknown") in {"unknown", "unknown_provider_status"}
    )
    open_failure_reviews = sum(1 for review in failure_reviews if review.status == "open")

    provider_breakdown = [
        {
            "provider": provider,
            **counts,
            "delivery_success_rate": _rate(counts["delivered_or_read"], counts["receipt_count"]),
        }
        for provider, counts in sorted(provider_counts.items())
    ]

    quality_gates = [
        _receipt_gate(
            key="receipt_ingestion",
            label="回执入库",
            status_value="ok" if total > 0 else "missing",
            detail=f"当前已入库 {total} 条渠道回执。",
            stop_condition="没有任何回执入库时，不能声称已具备线上链路观测。",
        ),
        _receipt_gate(
            key="attempt_match",
            label="回执匹配",
            status_value="ok" if matched == total and total > 0 else "warning" if matched > 0 else "missing",
            detail=f"{matched}/{total} 条回执已匹配到发送尝试。",
            stop_condition="真实平台回执不能稳定匹配发送记录前，不进入真实外发验收。",
        ),
        _receipt_gate(
            key="signature_verification",
            label="签名验证",
            status_value="ok" if verified == total and total > 0 else "warning" if verified > 0 else "missing",
            detail=f"{verified}/{total} 条回执具备已验证签名。",
            stop_condition="未完成官方回调签名或 AES 验证时，只能作为内部样本回执。",
        ),
        _receipt_gate(
            key="failure_review",
            label="失败复盘",
            status_value="ok" if failed_or_review == 0 else "warning",
            detail=f"{failed_or_review} 条回执需要复盘，当前打开 {open_failure_reviews} 条失败复盘。",
            stop_condition="失败回执不能进入复盘、重试或人工处理时，闭环不通过。",
        ),
        _receipt_gate(
            key="customer_accuracy",
            label="完整客服准确率",
            status_value="missing",
            detail="本接口只衡量回执链路覆盖，不衡量最终客服答案事实正确率。",
            stop_condition="缺少真实题库、最终回复样本、人工事实性标签和真实平台回执时，不展示完整线上准确率。",
        ),
    ]

    return {
        "tenant_id": tenant_id,
        "schema_version": "p3-06u-26h2w3d.online_receipt_quality.v1",
        "generated_at": utc_now(),
        "receipt_total": total,
        "matched_receipts": matched,
        "verified_receipts": verified,
        "delivered_or_read": delivered_or_read,
        "failed_or_review": failed_or_review,
        "unknown_receipts": unknown_receipts,
        "open_failure_reviews": open_failure_reviews,
        "receipt_match_rate": _rate(matched, total),
        "verified_receipt_rate": _rate(verified, total),
        "delivery_success_rate": _rate(delivered_or_read, total),
        "failure_review_rate": _rate(failed_or_review, total),
        "status_by_normalized_status": dict(sorted(status_counts.items())),
        "provider_breakdown": provider_breakdown,
        "quality_gates": quality_gates,
        "accuracy_scope_label": "线上回执链路覆盖率，不是完整客服答案准确率",
        "accuracy_boundary": "当前只统计本地归一回执、失败复盘和匹配情况；真实外发继续关闭，完整准确率需要官方授权渠道、真实回执、最终答案样本和人工事实性标签。",
        "raw_payload_included": False,
        "customer_accuracy_completed": False,
        "real_platform_receipts_required_for_full_accuracy": True,
        "model_call_performed": False,
        "external_call_performed": False,
        "external_platform_write_performed": False,
        "real_external_write_performed": False,
    }
