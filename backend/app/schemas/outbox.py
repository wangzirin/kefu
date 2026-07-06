from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class OutboxDraftCreateFromReview(BaseModel):
    idempotency_key: str = Field(default="", max_length=180)


class OutboxDraftConfirm(BaseModel):
    confirmation_note: str = Field(default="", max_length=4000)


class OutboxDraftCancel(BaseModel):
    cancellation_reason: str = Field(default="", max_length=4000)


class OutboxSendAttemptCreate(BaseModel):
    delivery_mode: str = Field(default="dry_run", max_length=32)
    idempotency_key: str = Field(default="", max_length=180)
    operator_note: str = Field(default="", max_length=4000)


class OutboxSendAttemptRead(BaseModel):
    id: int
    tenant_id: int
    outbox_draft_id: int
    conversation_id: int
    channel_id: int
    contact_id: int
    attempt_number: int
    delivery_mode: str
    provider: str
    status: str
    delivery_status: str
    idempotency_key: str
    external_message_id: str
    request_payload: dict[str, Any]
    response_payload: dict[str, Any]
    error_message: str
    operator_note: str
    created_by_id: int | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    sent_at: datetime | None = None

    model_config = {"from_attributes": True}


class OutboxWorkerRunCreate(BaseModel):
    batch_size: int | None = Field(default=None, ge=1, le=100)
    rate_limit_per_minute: int | None = Field(default=None, ge=0, le=600)
    max_attempts: int | None = Field(default=None, ge=1, le=10)


class OutboxWorkerRunRead(BaseModel):
    tenant_id: int
    mode: str
    scanned: int
    processed: int
    succeeded: int
    failed: int
    rate_limited: int
    rate_limited_draft_ids: list[int]
    skipped_draft_ids: list[int]
    external_write: bool
    rate_limit: dict[str, Any]
    attempts: list[OutboxSendAttemptRead]


class OutboxDeliveryJobCreate(BaseModel):
    idempotency_key: str = Field(default="", max_length=180)
    priority: int = Field(default=100, ge=0, le=1000)
    max_attempts: int | None = Field(default=None, ge=1, le=10)
    external_write_requested: bool = False


class OutboxDeliveryJobRead(BaseModel):
    id: int
    tenant_id: int
    outbox_draft_id: int
    channel_id: int
    connector_id: int | None = None
    status: str
    priority: int
    attempts_count: int
    max_attempts: int
    locked_by: str
    locked_at: datetime | None = None
    next_run_at: datetime | None = None
    idempotency_key: str
    external_write_requested: bool
    external_write_permitted: bool
    last_attempt_id: int | None = None
    last_error: str
    dead_letter_reason: str
    created_by_id: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    completed_at: datetime | None = None

    model_config = {"from_attributes": True}


class OutboxDeliveryQueueRunCreate(BaseModel):
    batch_size: int | None = Field(default=None, ge=1, le=100)
    rate_limit_per_minute: int | None = Field(default=None, ge=0, le=600)
    max_attempts: int | None = Field(default=None, ge=1, le=10)
    worker_id: str = Field(default="api_delivery_queue_worker", max_length=120)
    lease_seconds: int = Field(default=60, ge=1, le=3600)


class OutboxDeliveryQueueRunRead(BaseModel):
    tenant_id: int
    mode: str
    scanned: int
    processed: int
    succeeded: int
    failed: int
    blocked: int
    retry_scheduled: int
    dead_lettered: int
    rate_limited: int
    rate_limited_job_ids: list[int]
    skipped_job_ids: list[int]
    external_write: bool
    kill_switch: dict[str, Any]
    attempts: list[OutboxSendAttemptRead]
    jobs: list[OutboxDeliveryJobRead]


class OutboxDraftRead(BaseModel):
    id: int
    tenant_id: int
    conversation_id: int
    channel_id: int
    contact_id: int
    source_review_task_id: int | None = None
    source_workflow_run_id: int | None = None
    source_message_id: int | None = None
    status: str
    delivery_status: str
    reply_text: str
    idempotency_key: str
    confirmation_note: str
    cancellation_reason: str
    created_by_id: int | None = None
    confirmed_by_id: int | None = None
    canceled_by_id: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    confirmed_at: datetime | None = None
    canceled_at: datetime | None = None
    sent_at: datetime | None = None

    model_config = {"from_attributes": True}
