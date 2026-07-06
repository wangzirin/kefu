from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.worker_heartbeats import WorkerHeartbeatRead


InboundWorkerMode = Literal["knowledge_search", "model_assisted"]
InboundWorkerRiskLevel = Literal["low", "medium", "high", "critical"]
InboundWorkerModelProvider = Literal["deterministic", "auto", "bailian", "deepseek"]


class TrustedInboundWorkerRunCreate(BaseModel):
    batch_size: int = Field(default=20, ge=1, le=100)
    rate_limit_per_minute: int = Field(default=60, ge=0, le=600)
    worker_id: str = Field(default="manual_api_worker", min_length=1, max_length=120)
    lease_seconds: int = Field(default=60, ge=1, le=3600)
    mode: InboundWorkerMode = "model_assisted"
    risk_level: InboundWorkerRiskLevel = "medium"
    intent: str = Field(default="general_inquiry", min_length=1, max_length=120)
    knowledge_top_k: int = Field(default=3, ge=1, le=10)
    model_provider: InboundWorkerModelProvider = "deterministic"


class TrustedInboundWorkerItemRead(BaseModel):
    message_id: int
    conversation_id: int
    job_id: int | None = None
    reply_decision_id: int | None = None
    knowledge_gap_id: int | None = None
    outbox_draft_id: int | None = None
    status: str
    idempotency_key: str
    workflow_run_id: int | None = None
    human_review_task_id: int | None = None
    decision: str = ""
    reason: str = ""
    error_message: str = ""
    next_action: str = ""


class TrustedInboundWorkerRunRead(BaseModel):
    run_record_id: int | None = None
    tenant_id: int
    worker_id: str = ""
    mode: str
    scanned: int
    processed: int
    succeeded: int
    failed: int
    skipped: int
    rate_limited: int
    skipped_message_ids: list[int]
    rate_limited_message_ids: list[int]
    external_write: bool
    rate_limit: dict
    lease: dict
    items: list[TrustedInboundWorkerItemRead]


class TrustedInboundWorkerRunRecordRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: int
    worker_id: str
    mode: str
    status: str
    batch_size: int
    rate_limit_per_minute: int
    lease_seconds: int
    scanned: int
    processed: int
    succeeded: int
    failed: int
    skipped: int
    rate_limited: int
    external_write: bool
    request_payload: dict
    result_payload: dict
    error_message: str
    created_by_id: int | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None


class TrustedInboundWorkerLoopRunCreate(TrustedInboundWorkerRunCreate):
    iterations: int = Field(default=1, ge=1, le=50)
    sleep_seconds: float = Field(default=0, ge=0, le=10)
    stale_after_seconds: int = Field(default=120, ge=1, le=3600)


class TrustedInboundWorkerLoopRunRead(BaseModel):
    tenant_id: int
    worker_type: str
    worker_id: str
    iterations_requested: int
    iterations_completed: int
    failed_iterations: int
    total_scanned: int
    total_processed: int
    total_succeeded: int
    total_failed: int
    total_skipped: int
    total_rate_limited: int
    external_write: bool
    run_record_ids: list[int]
    last_run: TrustedInboundWorkerRunRead | None = None
    heartbeat: WorkerHeartbeatRead
