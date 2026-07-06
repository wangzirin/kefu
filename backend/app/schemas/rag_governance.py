from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel


class RagGovernanceMetric(BaseModel):
    label: str
    value: int | float | str | None
    unit: str = ""
    note: str = ""


class RagGovernanceGate(BaseModel):
    code: str
    label: str
    status: Literal["passed", "warning", "blocked"]
    reason: str
    evidence: dict[str, Any] = {}


class RagGovernanceLatestEvaluation(BaseModel):
    run_id: int | None
    evaluation_set_id: int | None
    run_mode: str
    total_cases: int
    hit_rate: float
    citation_coverage: float
    expected_term_coverage: float
    unsupported_answer_rate: float | None
    created_at: datetime | None = None


class RagGovernanceLatestProviderSmoke(BaseModel):
    run_id: int | None
    status: str
    embedding_provider: str
    embedding_model: str
    vector_store: str
    estimated_input_tokens: int
    estimated_cost: float
    cost_currency: str
    provider_call_performed: bool
    created_at: datetime | None = None


class RagGovernanceVectorProfile(BaseModel):
    configured_embedding_provider: str
    configured_embedding_model: str
    configured_vector_store: str
    configured_reranker: str
    indexed_chunk_count: int
    pgvector_chunk_count: int
    sqlite_vector_chunk_count: int
    latest_vector_index_plan: dict[str, Any] | None = None


class RagGovernanceModelPolicy(BaseModel):
    strategy_status: str
    strategy_version: str
    auto_reply_threshold: float | None
    manual_review_threshold: float | None
    force_draft_only: bool
    blocked_policy_terms_count: int
    manual_review_terms_count: int
    recent_reply_decision_count: int
    recent_model_call_record_count: int
    estimated_model_cost: float | None
    cost_currency: str
    cost_source: str
    budget_guard_enabled: bool = False
    daily_budget_limit: float = 0.0
    monthly_budget_limit: float = 0.0
    single_call_budget_limit: float = 0.0
    pricing_source: str = ""
    pricing_version: str = ""


class RagGovernanceAnswerQuality(BaseModel):
    latest_evaluation_run_id: int | None
    total_cases: int
    final_answer_sampled_cases: int
    final_answer_sample_coverage: float
    final_answer_factuality_labeled_cases: int
    final_answer_factuality_rate: float | None
    citation_sufficient_labeled_cases: int
    citation_sufficiency_rate: float | None
    forbidden_commitment_labeled_cases: int
    forbidden_commitment_pass_rate: float | None
    handoff_labeled_cases: int
    handoff_correctness: float | None
    citation_snapshot_count: int
    no_citation_snapshot_count: int
    complete_accuracy_measured: bool
    quality_source: str
    note: str


class RagProductionRetrievalReadiness(BaseModel):
    status: Literal["blocked", "candidate", "ready_for_controlled_pilot"]
    production_switch_allowed: bool
    postgres_runtime_ready: bool
    pgvector_runtime_ready: bool
    configured_pgvector: bool
    indexed_chunk_count: int
    pgvector_chunk_count: int
    sqlite_vector_chunk_count: int
    real_customer_material_ready: bool
    customer_material_batch_status: str
    customer_material_question_count: int
    customer_question_bank_ready: bool
    active_evaluation_cases: int
    retrieval_evaluation_ready: bool
    final_answer_quality_ready: bool
    embedding_cost_record_ready: bool
    model_cost_record_ready: bool
    budget_policy_ready: bool
    blockers: list[str]
    not_ready_for: list[str]
    retrieval_strategy_rules: dict[str, str]
    safety: dict[str, Any]


class RagCostGovernanceSummary(BaseModel):
    tenant_id: int
    schema_version: str
    maturity_status: Literal["blocked", "candidate", "ready_for_controlled_pilot"]
    summary: str
    knowledge_metrics: list[RagGovernanceMetric]
    vector_profile: RagGovernanceVectorProfile
    latest_evaluation: RagGovernanceLatestEvaluation
    latest_provider_smoke: RagGovernanceLatestProviderSmoke
    model_policy: RagGovernanceModelPolicy
    answer_quality: RagGovernanceAnswerQuality
    production_readiness: RagProductionRetrievalReadiness
    gates: list[RagGovernanceGate]
    recommended_next_steps: list[str]
    safety: dict[str, Any]
