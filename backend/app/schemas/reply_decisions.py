from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


ReplyDecisionState = Literal[
    "auto_reply_ready",
    "manual_gate_required",
    "knowledge_gap",
    "blocked_by_policy",
    "draft_only",
]
ReplyDeliveryMode = Literal["draft_only", "human_review", "external_write_allowed", "blocked"]


class ReplyDecisionCreate(BaseModel):
    auto_reply_threshold: float = Field(default=0.72, ge=0, le=1)
    manual_review_threshold: float = Field(default=0.45, ge=0, le=1)
    external_write_allowed: bool = False
    force_draft_only: bool = True
    idempotency_key: str = Field(default="", max_length=180)


class ReplyDecisionRead(BaseModel):
    id: int
    tenant_id: int
    conversation_id: int
    message_id: int
    channel_id: int
    business_object_id: Optional[int] = None
    object_knowledge_card_id: Optional[int] = None
    workflow_run_id: Optional[int] = None
    provenance_id: str = ""
    state: ReplyDecisionState
    reason: str
    confidence: float
    delivery_mode: ReplyDeliveryMode
    draft_reply: str
    matched_terms: list[str]
    decision_payload: dict
    external_write_allowed: bool
    idempotency_key: str
    created_by_id: Optional[int] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ReplyDecisionList(BaseModel):
    items: list[ReplyDecisionRead]
    page: int
    page_size: int
    total: int
