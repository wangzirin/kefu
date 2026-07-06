from __future__ import annotations

from pydantic import BaseModel, Field, model_validator


class ReplyPolicyUpdate(BaseModel):
    auto_reply_threshold: float | None = Field(default=None, ge=0, le=1)
    manual_review_threshold: float | None = Field(default=None, ge=0, le=1)
    blocked_policy_terms: list[str] = Field(default_factory=list, max_length=100)
    manual_review_terms: list[str] = Field(default_factory=list, max_length=100)
    force_draft_only: bool | None = None

    @model_validator(mode="after")
    def validate_threshold_order(self) -> "ReplyPolicyUpdate":
        if (
            self.auto_reply_threshold is not None
            and self.manual_review_threshold is not None
            and self.manual_review_threshold > self.auto_reply_threshold
        ):
            raise ValueError("manual_review_threshold cannot be greater than auto_reply_threshold")
        return self


class ModelRoutingUpdate(BaseModel):
    default_provider: str = Field(default="auto", max_length=80)
    fast_model: str = Field(default="", max_length=160)
    standard_model: str = Field(default="", max_length=160)
    premium_model: str = Field(default="", max_length=160)
    fallback_provider: str = Field(default="", max_length=80)


class ReplyStrategyUpdatePackagePayload(BaseModel):
    schema_version: str = Field(default="wanfa.reply_strategy_update.v1")
    strategy_id: str = Field(min_length=1, max_length=160)
    strategy_version: str = Field(min_length=1, max_length=80)
    notes: str = Field(default="", max_length=2000)
    reply_policy: ReplyPolicyUpdate = Field(default_factory=ReplyPolicyUpdate)
    model_routing: ModelRoutingUpdate = Field(default_factory=ModelRoutingUpdate)
