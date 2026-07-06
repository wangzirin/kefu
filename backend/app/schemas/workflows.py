from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


JsonObject = dict[str, Any]


class WorkflowRunCreate(BaseModel):
    trigger_message_id: Optional[int] = None
    workflow_type: str = Field(default="customer_reply", min_length=1, max_length=80)
    current_step: str = Field(default="classify_intent", min_length=1, max_length=80)
    idempotency_key: str = Field(default="", max_length=160)
    state_payload: JsonObject = Field(default_factory=dict)


class WorkflowRunRead(BaseModel):
    id: int
    tenant_id: int
    conversation_id: int
    trigger_message_id: Optional[int] = None
    workflow_type: str
    status: str
    current_step: str
    idempotency_key: str
    state_payload: JsonObject
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class WorkflowCheckpointCreate(BaseModel):
    step_name: str = Field(min_length=1, max_length=80)
    status: str = Field(min_length=1, max_length=32)
    state_payload: JsonObject = Field(default_factory=dict)
    input_summary: str = Field(default="", max_length=4000)
    output_summary: str = Field(default="", max_length=4000)
    error_message: str = Field(default="", max_length=4000)


class WorkflowCheckpointRead(BaseModel):
    id: int
    workflow_run_id: int
    step_name: str
    status: str
    state_payload: JsonObject
    input_summary: str
    output_summary: str
    error_message: str
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class WorkflowStepAttemptCreate(BaseModel):
    step_name: str = Field(min_length=1, max_length=80)
    status: str = Field(min_length=1, max_length=32)
    attempt_number: Optional[int] = None
    input_summary: str = Field(default="", max_length=4000)
    output_summary: str = Field(default="", max_length=4000)
    error_message: str = Field(default="", max_length=4000)


class WorkflowStepAttemptRead(BaseModel):
    id: int
    workflow_run_id: int
    step_name: str
    attempt_number: int
    status: str
    input_summary: str
    output_summary: str
    error_message: str
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class HumanReviewTaskCreate(BaseModel):
    reason: str = Field(min_length=1, max_length=120)
    risk_level: str = Field(default="medium", max_length=32)
    draft_reply: str = Field(default="", max_length=12000)
    assigned_user_id: Optional[int] = None


class HumanReviewTaskResolve(BaseModel):
    decision: str = Field(pattern="^(approved|rejected)$")
    final_reply: str = Field(default="", max_length=12000)
    resolution_note: str = Field(default="", max_length=4000)


class HumanReviewTaskRead(BaseModel):
    id: int
    tenant_id: int
    workflow_run_id: int
    conversation_id: int
    message_id: Optional[int] = None
    status: str
    reason: str
    risk_level: str
    draft_reply: str
    final_reply: str
    assigned_user_id: Optional[int] = None
    reviewer_id: Optional[int] = None
    resolution_note: str
    created_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class HumanReviewConversationRead(BaseModel):
    id: int
    channel_id: int
    contact_id: int
    assigned_user_id: Optional[int] = None
    assigned_team_id: Optional[int] = None
    status: str
    priority: str
    subject: str
    last_message_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class HumanReviewMessageRead(BaseModel):
    id: int
    conversation_id: int
    direction: str
    sender_type: str
    content: str
    external_message_id: str
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class HumanReviewWorkflowRead(BaseModel):
    id: int
    workflow_type: str
    status: str
    current_step: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class HumanReviewEvidenceRead(BaseModel):
    intent: str = ""
    retrieved_knowledge_count: int = 0
    confidence: Optional[float] = None
    risk_level: str = ""
    draft_source: str = ""
    retrieval_mode: str = ""
    retrieval_engine: str = ""
    knowledge_matches: list[JsonObject] = Field(default_factory=list)
    model_call: Optional[JsonObject] = None
    auto_reply_threshold: Optional[float] = None


class HumanReviewInboxItemRead(HumanReviewTaskRead):
    conversation: HumanReviewConversationRead
    trigger_message: Optional[HumanReviewMessageRead] = None
    workflow: HumanReviewWorkflowRead
    evidence: HumanReviewEvidenceRead


class WorkflowRunDetail(WorkflowRunRead):
    checkpoints: list[WorkflowCheckpointRead] = []
    step_attempts: list[WorkflowStepAttemptRead] = []
    human_review_tasks: list[HumanReviewTaskRead] = []
