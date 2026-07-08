from datetime import datetime
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.schemas.outbox import OutboxSendAttemptRead


class ChannelConnectorConfigCreate(BaseModel):
    provider: str = Field(min_length=1, max_length=80)
    mode: str = Field(default="noop", pattern="^(noop|official_api)$")
    status: str = Field(default="draft", max_length=32)
    display_name: str = Field(default="", max_length=160)
    capabilities: list[str] = Field(default_factory=list, max_length=20)
    public_config: dict[str, Any] = Field(default_factory=dict)
    webhook_path: str = Field(default="", max_length=300)
    signature_mode: str = Field(default="not_configured", max_length=80)


class ChannelConnectorConfigRead(BaseModel):
    id: int
    tenant_id: int
    channel_id: int
    provider: str
    mode: str
    status: str
    display_name: str
    capabilities: list[str]
    public_config: dict[str, Any]
    webhook_path: str
    signature_mode: str
    secret_status: str
    external_write_enabled: bool
    created_by_id: int | None = None
    updated_by_id: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class ChannelConnectorSecretUpsert(BaseModel):
    secrets: dict[str, str] = Field(default_factory=dict, max_length=20)


class ChannelConnectorSecretStatusRead(BaseModel):
    tenant_id: int
    channel_id: int
    connector_id: int
    provider: str
    status: str
    field_status: dict[str, str]
    secret_included: bool = False


class ChannelConnectorAuthorizationStart(BaseModel):
    provider: str = Field(min_length=1, max_length=80)
    connect_mode: str = Field(default="qr", pattern="^(qr|manual)$")
    redirect_uri: str = Field(default="", max_length=500)


class ChannelConnectorAuthorizationRead(BaseModel):
    tenant_id: int
    channel_id: int
    connector_id: int
    provider: str
    connect_mode: str
    status: str
    authorization_url: str
    qr_payload: str
    state: str
    expires_at: datetime
    next_steps: list[str]
    secret_included: bool = False


class ChannelConnectorVerificationRead(BaseModel):
    tenant_id: int
    channel_id: int
    connector_id: int
    provider: str
    status: str
    missing_fields: list[str]
    webhook_path: str
    external_write_enabled: bool
    secret_included: bool = False


class ChannelAccountCreate(BaseModel):
    connector_id: int | None = None
    provider: str = Field(default="", max_length=80)
    platform: str = Field(default="", max_length=80)
    account_name: str = Field(min_length=1, max_length=160)
    external_account_id: str = Field(default="", max_length=180)
    store_name: str = Field(default="", max_length=160)
    entrypoint_name: str = Field(default="", max_length=160)
    authorization_status: str = Field(default="not_configured", max_length=40)
    access_status: str = Field(default="planned", max_length=40)
    reply_mode: str = Field(
        default="draft_only",
        pattern="^(auto_reply|auto_with_handoff|human_review_first|draft_only|research_draft_only)$",
    )
    health_status: str = Field(default="unknown", max_length=40)
    public_profile: dict[str, Any] = Field(default_factory=dict)


class ChannelAccountRead(BaseModel):
    id: int
    tenant_id: int
    channel_id: int
    connector_id: int | None = None
    provider: str
    platform: str
    account_name: str
    external_account_id: str
    store_name: str
    entrypoint_name: str
    authorization_status: str
    access_status: str
    reply_mode: str
    health_status: str
    public_profile: dict[str, Any]
    created_by_id: int | None = None
    updated_by_id: int | None = None
    last_sync_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class ConnectorSendPlanCreate(BaseModel):
    idempotency_key: str = Field(default="", max_length=180)
    operator_note: str = Field(default="", max_length=4000)


class ConnectorSendPlanRead(OutboxSendAttemptRead):
    pass


class ChannelProviderRead(BaseModel):
    provider: str
    display_name: str
    supported_channel_types: list[str]
    default_signature_mode: str
    webhook_path_template: str
    inbound_event_types: list[str]
    capabilities: dict[str, Any]
    verification_contract: dict[str, Any]
    inbound_event_contract: dict[str, Any]


class ChannelDeliveryReceiptCreate(BaseModel):
    provider: str = Field(min_length=1, max_length=80)
    external_message_id: str = Field(default="", max_length=180)
    delivery_status: str = Field(default="unknown", max_length=40)
    provider_event_id: str = Field(default="", max_length=180)
    raw_payload: dict[str, Any] = Field(default_factory=dict)
    signature_validated: bool = False


class ChannelWebhookEventCreate(BaseModel):
    event_type: str = Field(default="message", max_length=80)
    external_message_id: str = Field(default="", max_length=180)
    delivery_status: str = Field(default="webhook_received", max_length=40)
    provider_event_id: str = Field(default="", max_length=180)
    raw_payload: dict[str, Any] = Field(default_factory=dict)


class WebsiteWidgetMessageCreate(BaseModel):
    tenant_id: int | None = None
    tenant_slug: str = Field(default="", max_length=80)
    component_id: str = Field(default="website-widget", max_length=120)
    visitor_id: str = Field(default="", max_length=120)
    visitor_name: str = Field(default="网站访客", max_length=120)
    text: str = Field(min_length=1, max_length=4000)
    page_url: str = Field(default="", max_length=1000)
    page_title: str = Field(default="", max_length=300)
    reopen_action: str = Field(default="", pattern="^(|continue_chat|leave_message)$")


class WebsiteWidgetMessageRead(BaseModel):
    tenant_id: int
    channel_id: int
    contact_id: int | None = None
    conversation_id: int | None = None
    message_id: int | None = None
    status: str
    next_action: str
    is_new_conversation: bool = False
    conversation_status: str = ""


class WebsiteWidgetConversationMessageRead(BaseModel):
    id: int
    conversation_id: int
    direction: str
    sender_type: str
    content: str
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class WebsiteWidgetConversationRead(BaseModel):
    tenant_id: int
    channel_id: int | None = None
    contact_id: int | None = None
    conversation_id: int | None = None
    conversation_status: str = ""
    messages: list[WebsiteWidgetConversationMessageRead] = Field(default_factory=list)


class ChannelDeliveryReceiptRead(BaseModel):
    id: int
    tenant_id: int
    channel_id: int
    connector_id: int | None = None
    matched_attempt_id: int | None = None
    provider: str
    external_message_id: str
    delivery_status: str
    provider_status: str
    provider_error_code: str
    normalized_status: str
    retryable: bool
    needs_review: bool
    next_action: str
    provider_event_id: str
    verification_status: str
    signature_validated: bool
    raw_payload: dict[str, Any]
    received_at: datetime | None = None

    model_config = {"from_attributes": True}


class OnlineReceiptProviderBreakdownRead(BaseModel):
    provider: str
    receipt_count: int
    matched_receipts: int
    verified_receipts: int
    delivered_or_read: int
    needs_review: int
    unknown_receipts: int
    delivery_success_rate: float | None = None


class OnlineReceiptQualityGateRead(BaseModel):
    key: str
    label: str
    status: str
    detail: str
    stop_condition: str


class OnlineReceiptQualitySummaryRead(BaseModel):
    tenant_id: int
    schema_version: str
    generated_at: datetime
    receipt_total: int
    matched_receipts: int
    verified_receipts: int
    delivered_or_read: int
    failed_or_review: int
    unknown_receipts: int
    open_failure_reviews: int
    receipt_match_rate: float | None = None
    verified_receipt_rate: float | None = None
    delivery_success_rate: float | None = None
    failure_review_rate: float | None = None
    status_by_normalized_status: dict[str, int]
    provider_breakdown: list[OnlineReceiptProviderBreakdownRead]
    quality_gates: list[OnlineReceiptQualityGateRead]
    accuracy_scope_label: str
    accuracy_boundary: str
    raw_payload_included: bool
    customer_accuracy_completed: bool
    real_platform_receipts_required_for_full_accuracy: bool
    model_call_performed: bool
    external_call_performed: bool
    external_platform_write_performed: bool
    real_external_write_performed: bool


class ChannelWebhookEventRead(BaseModel):
    tenant_id: int
    channel_id: int
    connector_id: int
    receipt_id: int
    provider: str
    event_type: str
    external_message_id: str
    delivery_status: str
    provider_status: str
    provider_error_code: str
    normalized_status: str
    retryable: bool
    needs_review: bool
    next_action: str
    provider_event_id: str
    verification_status: str
    signature_validated: bool
    external_write: bool
    parsed_event: dict[str, Any]
    registry_contract: dict[str, Any]
