from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class RpaCopilotDryRunRequest(BaseModel):
    channel: str = Field(default="manual_import_research", min_length=1, max_length=80)
    customer_name: str = Field(default="人工导入客户", min_length=1, max_length=120)
    text: str = Field(min_length=1, max_length=4000)
    attachments: list[str] = Field(default_factory=list, max_length=10)
    metadata: dict[str, str] = Field(default_factory=dict)


class RpaCopilotMessageRead(BaseModel):
    message_id: str
    channel: str
    customer_name: str
    text: str
    received_at: str
    attachments: list[str] = Field(default_factory=list)
    metadata: dict[str, str] = Field(default_factory=dict)


class RpaCopilotKnowledgeHitRead(BaseModel):
    card_id: str
    title: str
    score: float
    answer: str
    source: str
    risk_tags: list[str] = Field(default_factory=list)


class RpaCopilotDraftRead(BaseModel):
    text: str
    route: str
    confidence: float
    citations: list[str] = Field(default_factory=list)
    missing_knowledge: bool = False


class RpaCopilotGuardrailRead(BaseModel):
    status: Literal["draft_only", "needs_human", "blocked"]
    reasons: list[str] = Field(default_factory=list)
    allow_auto_send: bool


class RpaCopilotReplyStrategyRead(BaseModel):
    intent: str
    answer_mode: str
    delivery_mode: str
    customer_visible_policy: str
    next_best_action: str
    quality_signals: list[str] = Field(default_factory=list)


class RpaCopilotActionRead(BaseModel):
    kind: str
    target: str
    payload: dict[str, object] = Field(default_factory=dict)
    external_write: bool = False


class RpaCopilotDryRunResponse(BaseModel):
    tenant_id: int
    operator_user_id: int
    mode: Literal["research_dry_run"] = "research_dry_run"
    message: RpaCopilotMessageRead
    hits: list[RpaCopilotKnowledgeHitRead] = Field(default_factory=list)
    draft: RpaCopilotDraftRead
    guardrail: RpaCopilotGuardrailRead
    reply_strategy: RpaCopilotReplyStrategyRead
    actions: list[RpaCopilotActionRead] = Field(default_factory=list)
    audit: dict[str, object] = Field(default_factory=dict)
