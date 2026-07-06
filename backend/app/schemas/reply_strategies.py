from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, model_validator


class TenantReplyPolicyRead(BaseModel):
    auto_reply_threshold: Optional[float] = None
    manual_review_threshold: Optional[float] = None
    blocked_policy_terms: list[str] = Field(default_factory=list)
    manual_review_terms: list[str] = Field(default_factory=list)
    force_draft_only: bool = False


class TenantReplyStrategyRead(BaseModel):
    tenant_id: int
    strategy_id: str
    strategy_version: str
    status: str
    reply_policy: TenantReplyPolicyRead
    model_routing: dict
    updated_by_id: Optional[int] = None
    updated_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    source: str
    external_write_performed: bool = False
    model_call_performed: bool = False


class TenantReplyStrategyUpdate(BaseModel):
    auto_reply_threshold: Optional[float] = Field(default=None, ge=0, le=1)
    manual_review_threshold: Optional[float] = Field(default=None, ge=0, le=1)
    blocked_policy_terms: list[str] = Field(default_factory=list, max_length=100)
    manual_review_terms: list[str] = Field(default_factory=list, max_length=100)
    force_draft_only: bool = False

    @model_validator(mode="after")
    def validate_threshold_order(self) -> "TenantReplyStrategyUpdate":
        if (
            self.auto_reply_threshold is not None
            and self.manual_review_threshold is not None
            and self.manual_review_threshold > self.auto_reply_threshold
        ):
            raise ValueError("manual_review_threshold cannot be greater than auto_reply_threshold")
        return self
