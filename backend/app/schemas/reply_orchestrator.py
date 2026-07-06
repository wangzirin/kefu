from typing import Literal, Optional

from pydantic import BaseModel, Field, model_validator

from app.schemas.workflows import HumanReviewTaskRead, WorkflowRunRead


RiskLevel = Literal["low", "medium", "high", "critical"]
ReplyDecision = Literal["completed", "human_review"]
ReplyMode = Literal["manual", "knowledge_search", "document_rag", "model_assisted"]
ModelProvider = Literal["deterministic", "auto", "bailian", "deepseek"]
ModelCallStatus = Literal["succeeded", "unavailable", "failed", "budget_blocked", "degraded"]


class ReplyOrchestrationCreate(BaseModel):
    mode: ReplyMode = "manual"
    intent: Optional[str] = Field(default=None, min_length=1, max_length=120)
    retrieved_knowledge_count: Optional[int] = Field(default=None, ge=0, le=1000)
    draft_reply: Optional[str] = Field(default=None, min_length=1, max_length=12000)
    confidence: Optional[float] = Field(default=None, ge=0, le=1)
    risk_level: RiskLevel = "low"
    knowledge_query: Optional[str] = Field(default=None, min_length=1, max_length=4000)
    knowledge_top_k: int = Field(default=3, ge=1, le=10)
    model_provider: ModelProvider = "deterministic"
    model_name: str = Field(default="", max_length=120)
    model_temperature: float = Field(default=0.2, ge=0, le=1)
    idempotency_key: str = Field(default="", max_length=160)

    @model_validator(mode="after")
    def require_manual_fields(self) -> "ReplyOrchestrationCreate":
        if self.mode == "manual":
            missing = [
                field
                for field in ("intent", "retrieved_knowledge_count", "draft_reply", "confidence")
                if getattr(self, field) is None
            ]
            if missing:
                raise ValueError(f"manual reply orchestration requires: {', '.join(missing)}")
        return self


class ReplyKnowledgeMatchRead(BaseModel):
    source_kind: str = "knowledge_card"
    card_id: Optional[int] = None
    document_id: Optional[int] = None
    chunk_id: Optional[int] = None
    chunk_index: Optional[int] = None
    title: str
    score: float
    confidence: float
    matched_terms: list[str]
    source_type: str
    source_uri: str
    content_preview: str = ""
    citation: dict = Field(default_factory=dict)


class ReplyModelCallRead(BaseModel):
    provider: str
    model: str
    status: ModelCallStatus
    prompt_summary: str
    prompt_chars: int
    completion_chars: int
    total_chars: int
    error_message: str = ""
    route_name: str = "explicit_provider"
    complexity: str = "standard"
    target_model_tier: str = "standard"
    fallback_chain: list[str] = Field(default_factory=list)
    human_review_required: bool = False
    route_reasons: list[str] = Field(default_factory=list)
    estimated_cost: float = 0.0
    cost_currency: str = "CNY"
    pricing_source: str = ""
    pricing_version: str = ""
    budget_status: str = "not_evaluated"
    budget_reason: str = ""
    budget_action: str = ""


class ReplyOrchestrationRead(BaseModel):
    decision: ReplyDecision
    reason: str
    workflow_run: WorkflowRunRead
    human_review_task: Optional[HumanReviewTaskRead] = None
    draft_reply: str
    knowledge_matches: list[ReplyKnowledgeMatchRead] = Field(default_factory=list)
    model_call: Optional[ReplyModelCallRead] = None
