from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class DeliveryFailureReviewRead(BaseModel):
    id: int
    tenant_id: int
    channel_id: int
    connector_id: int | None = None
    receipt_id: int
    matched_attempt_id: int | None = None
    outbox_draft_id: int | None = None
    provider: str
    external_message_id: str
    provider_status: str
    provider_error_code: str
    normalized_status: str
    severity: str
    retryable: bool
    review_reason: str
    next_action: str
    status: str
    resolution_note: str
    resolved_by_id: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    resolved_at: datetime | None = None

    model_config = {"from_attributes": True}


class DeliveryFailureReviewUpdate(BaseModel):
    status: Literal["open", "resolved", "ignored"]
    resolution_note: str = Field(default="", max_length=4000)
