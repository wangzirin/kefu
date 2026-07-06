from typing import Any, Literal

from pydantic import BaseModel


class LlmOpsGate(BaseModel):
    code: str
    label: str
    status: Literal["passed", "warning", "blocked"]
    reason: str
    evidence: dict[str, Any] = {}


class LlmOpsModelGateway(BaseModel):
    gateway_version: str
    strategy_status: str
    strategy_version: str
    prompt_policy_version: str
    explicit_provider_no_silent_fallback: bool
    auto_route_fallback_allowed: bool
    force_draft_only: bool
    budget_guard_enabled: bool


class LlmOpsCostLedger(BaseModel):
    model_call_count: int
    succeeded_count: int
    failed_count: int
    degraded_count: int
    budget_blocked_count: int
    external_provider_call_count: int
    deterministic_call_count: int
    estimated_cost: float
    currency: str
    provider_count: int
    model_count: int
    pricing_version_count: int
    missing_pricing_count: int
    raw_text_logged_count: int
    average_latency_ms: float | None


class LlmOpsTraceCoverage(BaseModel):
    reply_decision_count: int
    reply_decisions_with_provenance: int
    model_calls_with_provenance: int
    citation_snapshot_count: int
    no_citation_snapshot_count: int
    evaluation_run_count: int
    final_answer_labeled_cases: int
    trace_ready: bool
    quality_label_ready: bool


class LlmOpsRedteamReadiness(BaseModel):
    source: Literal["database_evaluation_tables"]
    internal_sample_cases: int
    internal_sample_only: bool
    redteam_case_count: int
    required_minimum_cases: int
    required_categories: list[str]
    missing_categories: list[str]
    category_coverage_ready: bool
    prompt_injection_cases: int
    jailbreak_cases: int
    privacy_leak_cases: int
    forbidden_commitment_cases: int
    over_permission_cases: int
    redteam_labeled_cases: int
    all_active_cases_labeled: bool
    redteam_failed_cases: int
    failures_requiring_quality_review: int
    failures_with_quality_review_items: int
    unresolved_redteam_failures: int
    failures_entered_quality_review: bool
    readiness: Literal["not_started", "case_bank_ready", "labeled_with_failures", "ready_for_controlled_pilot"]


class LlmOpsReadinessSummary(BaseModel):
    tenant_id: int
    schema_version: str
    status: Literal[
        "blocked",
        "llm_ops_observability_candidate",
        "llm_ops_observability_ready_not_redteam_complete",
        "llm_ops_ready_for_controlled_pilot",
    ]
    summary: str
    model_gateway: LlmOpsModelGateway
    cost_ledger: LlmOpsCostLedger
    trace_coverage: LlmOpsTraceCoverage
    redteam_readiness: LlmOpsRedteamReadiness
    gates: list[LlmOpsGate]
    blockers: list[str]
    recommended_next_steps: list[str]
    not_ready_for: list[str]
    safety: dict[str, Any]
