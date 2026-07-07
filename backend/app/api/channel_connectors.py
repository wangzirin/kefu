from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from app.core.auth import CurrentPrincipal
from app.core.rbac import require_permission
from app.db.session import get_db
from app.models import ChannelAccount, ChannelConnector, ChannelDeliveryReceipt, OutboxSendAttempt
from app.schemas.channel_connectors import (
    ChannelAccountCreate,
    ChannelAccountRead,
    ChannelConnectorConfigCreate,
    ChannelConnectorConfigRead,
    ChannelDeliveryReceiptCreate,
    ChannelDeliveryReceiptRead,
    ChannelProviderRead,
    ChannelWebhookEventCreate,
    ChannelWebhookEventRead,
    ConnectorSendPlanCreate,
    ConnectorSendPlanRead,
    OnlineReceiptQualitySummaryRead,
    WebsiteWidgetConversationRead,
    WebsiteWidgetMessageCreate,
    WebsiteWidgetMessageRead,
)
from app.services.channel_connectors import (
    configure_channel_account,
    configure_channel_connector,
    create_channel_delivery_receipt,
    create_connector_send_plan,
    get_channel_connector,
    get_online_receipt_quality_summary,
    list_channel_accounts,
    list_channel_delivery_receipts,
    list_channel_provider_registry,
    list_website_widget_conversation_messages,
    receive_channel_webhook_event,
    receive_website_widget_message,
    receive_wecom_official_xml_webhook,
    verify_wecom_callback_url,
)

router = APIRouter(prefix="/api", tags=["channel-connectors"])

CHANNEL_READ_PERMISSION = "channel.read"
CHANNEL_CONNECTOR_MANAGE_PERMISSION = "channel.connector.manage"
CHANNEL_DELIVERY_RECEIPT_READ_PERMISSION = "channel.delivery_receipt.read"
CHANNEL_DELIVERY_RECEIPT_MANAGE_PERMISSION = "channel.delivery_receipt.manage"
QUALITY_READ_PERMISSION = "quality.read"
OUTBOX_SEND_PLAN_MANAGE_PERMISSION = "outbox.send_plan.manage"


@router.get("/channel-providers", response_model=list[ChannelProviderRead])
def list_tenant_channel_providers(
    principal: CurrentPrincipal = Depends(require_permission(CHANNEL_READ_PERMISSION)),
) -> list[dict]:
    _ = principal
    return list_channel_provider_registry()


@router.get("/tenants/{tenant_id}/channel-accounts", response_model=list[ChannelAccountRead])
def list_tenant_channel_accounts(
    tenant_id: int,
    principal: CurrentPrincipal = Depends(require_permission(CHANNEL_READ_PERMISSION)),
    db: Session = Depends(get_db),
) -> list[ChannelAccount]:
    return list_channel_accounts(db, tenant_id=tenant_id, principal=principal)


@router.post(
    "/channels/{channel_id}/channel-accounts",
    response_model=ChannelAccountRead,
    status_code=status.HTTP_201_CREATED,
)
def configure_tenant_channel_account(
    channel_id: int,
    payload: ChannelAccountCreate,
    principal: CurrentPrincipal = Depends(require_permission(CHANNEL_CONNECTOR_MANAGE_PERMISSION)),
    db: Session = Depends(get_db),
):
    return configure_channel_account(db, channel_id=channel_id, payload=payload, principal=principal)


@router.post(
    "/channels/{channel_id}/connector-config",
    response_model=ChannelConnectorConfigRead,
    status_code=status.HTTP_201_CREATED,
)
def configure_tenant_channel_connector(
    channel_id: int,
    payload: ChannelConnectorConfigCreate,
    principal: CurrentPrincipal = Depends(require_permission(CHANNEL_CONNECTOR_MANAGE_PERMISSION)),
    db: Session = Depends(get_db),
) -> ChannelConnector:
    return configure_channel_connector(db, channel_id=channel_id, payload=payload, principal=principal)


@router.get("/channels/{channel_id}/connector-config", response_model=ChannelConnectorConfigRead)
def get_tenant_channel_connector(
    channel_id: int,
    principal: CurrentPrincipal = Depends(require_permission(CHANNEL_READ_PERMISSION)),
    db: Session = Depends(get_db),
) -> ChannelConnector:
    return get_channel_connector(db, channel_id=channel_id, principal=principal)


@router.post(
    "/public/website-widget/messages",
    response_model=WebsiteWidgetMessageRead,
    status_code=status.HTTP_201_CREATED,
)
def receive_public_website_widget_message(
    payload: WebsiteWidgetMessageCreate,
    db: Session = Depends(get_db),
) -> dict:
    return receive_website_widget_message(db, payload=payload)


@router.get(
    "/public/website-widget/messages",
    response_model=WebsiteWidgetConversationRead,
)
def list_public_website_widget_messages(
    tenant_id: int | None = None,
    tenant_slug: str = "",
    visitor_id: str = "",
    after_id: int = 0,
    db: Session = Depends(get_db),
) -> dict:
    return list_website_widget_conversation_messages(
        db,
        tenant_id=tenant_id,
        tenant_slug=tenant_slug,
        visitor_id=visitor_id,
        after_id=after_id,
    )


@router.post(
    "/outbox-drafts/{draft_id}/connector-send-plans",
    response_model=ConnectorSendPlanRead,
    status_code=status.HTTP_201_CREATED,
)
def create_tenant_connector_send_plan(
    draft_id: int,
    payload: ConnectorSendPlanCreate,
    principal: CurrentPrincipal = Depends(require_permission(OUTBOX_SEND_PLAN_MANAGE_PERMISSION)),
    db: Session = Depends(get_db),
) -> OutboxSendAttempt:
    return create_connector_send_plan(db, draft_id=draft_id, payload=payload, principal=principal)


@router.post(
    "/channels/{channel_id}/delivery-receipts",
    response_model=ChannelDeliveryReceiptRead,
    status_code=status.HTTP_201_CREATED,
)
def create_tenant_channel_delivery_receipt(
    channel_id: int,
    payload: ChannelDeliveryReceiptCreate,
    principal: CurrentPrincipal = Depends(require_permission(CHANNEL_DELIVERY_RECEIPT_MANAGE_PERMISSION)),
    db: Session = Depends(get_db),
) -> ChannelDeliveryReceipt:
    return create_channel_delivery_receipt(db, channel_id=channel_id, payload=payload, principal=principal)


@router.post(
    "/webhooks/wecom/channels/{channel_id}",
    response_model=ChannelWebhookEventRead,
    status_code=status.HTTP_202_ACCEPTED,
)
async def receive_wecom_official_xml_channel_webhook(
    channel_id: int,
    request: Request,
    db: Session = Depends(get_db),
) -> dict:
    content_type = request.headers.get("content-type", "").lower()
    if "json" in content_type:
        payload = ChannelWebhookEventCreate.model_validate(await request.json())
        return receive_channel_webhook_event(
            db,
            provider="wecom",
            channel_id=channel_id,
            payload=payload,
            query_params=dict(request.query_params),
        )
    raw_body = (await request.body()).decode("utf-8")
    return receive_wecom_official_xml_webhook(
        db,
        channel_id=channel_id,
        xml_body=raw_body,
        query_params=dict(request.query_params),
    )


@router.get("/webhooks/wecom/channels/{channel_id}", response_class=PlainTextResponse)
def verify_wecom_official_callback_url(
    channel_id: int,
    request: Request,
    db: Session = Depends(get_db),
) -> str:
    return verify_wecom_callback_url(
        db,
        channel_id=channel_id,
        query_params=dict(request.query_params),
    )


@router.post(
    "/webhooks/{provider}/channels/{channel_id}",
    response_model=ChannelWebhookEventRead,
    status_code=status.HTTP_202_ACCEPTED,
)
def receive_official_channel_webhook(
    provider: str,
    channel_id: int,
    request: Request,
    payload: ChannelWebhookEventCreate,
    db: Session = Depends(get_db),
) -> dict:
    return receive_channel_webhook_event(
        db,
        provider=provider,
        channel_id=channel_id,
        payload=payload,
        query_params=dict(request.query_params),
    )


@router.get("/channels/{channel_id}/delivery-receipts", response_model=list[ChannelDeliveryReceiptRead])
def list_tenant_channel_delivery_receipts(
    channel_id: int,
    principal: CurrentPrincipal = Depends(require_permission(CHANNEL_DELIVERY_RECEIPT_READ_PERMISSION)),
    db: Session = Depends(get_db),
) -> list[ChannelDeliveryReceipt]:
    return list_channel_delivery_receipts(db, channel_id=channel_id, principal=principal)


@router.get(
    "/tenants/{tenant_id}/online-receipt-quality-summary",
    response_model=OnlineReceiptQualitySummaryRead,
)
def get_tenant_online_receipt_quality_summary(
    tenant_id: int,
    principal: CurrentPrincipal = Depends(require_permission(QUALITY_READ_PERMISSION)),
    db: Session = Depends(get_db),
) -> dict:
    return get_online_receipt_quality_summary(db, tenant_id=tenant_id, principal=principal)
