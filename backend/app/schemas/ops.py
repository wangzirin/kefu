from datetime import datetime

from pydantic import BaseModel

from app.schemas.inbound_worker import TrustedInboundWorkerRunRecordRead
from app.schemas.worker_heartbeats import WorkerHeartbeatRead


class WorkerHealthSummary(BaseModel):
    total_workers: int
    healthy_workers: int
    stale_workers: int
    failed_workers: int
    running_workers: int
    idle_workers: int
    external_write_enabled: bool
    trusted_inbound_worker_enabled: bool
    requires_attention: bool


class OpsRiskRead(BaseModel):
    code: str
    severity: str
    title: str
    detail: str
    next_action: str


class WorkerHealthDashboardRead(BaseModel):
    tenant_id: int
    generated_at: datetime
    stale_after_seconds: int
    summary: WorkerHealthSummary
    heartbeats: list[WorkerHeartbeatRead]
    recent_trusted_inbound_runs: list[TrustedInboundWorkerRunRecordRead]
    risks: list[OpsRiskRead]
    external_call_performed: bool
    external_platform_write_performed: bool


class OpsDashboardSummaryRead(BaseModel):
    inbound_conversations: int
    inbound_messages: int
    open_reviews: int
    high_risk_reviews: int
    pending_outbox_drafts: int
    ready_outbox_drafts: int
    open_failure_reviews: int
    blocked_delivery_jobs: int
    open_knowledge_gaps: int
    open_tickets: int
    open_leads: int
    average_wait_minutes: int
    ai_draft_coverage: float
    manual_review_pressure: float
    exception_pressure: float
    health_score: int


class OpsDashboardChannelRead(BaseModel):
    channel_id: int
    channel_name: str
    channel_type: str
    inbound_conversations: int
    open_reviews: int
    pending_outbox_drafts: int
    ready_outbox_drafts: int
    open_failure_reviews: int
    blocked_delivery_jobs: int
    workload: int
    exception_count: int


class OpsDashboardFunnelStageRead(BaseModel):
    key: str
    label: str
    count: int


class OpsDashboardTrendBucketRead(BaseModel):
    key: str
    label: str
    inbound: int
    reviews: int
    drafts: int
    exceptions: int


class OpsDashboardQualityRead(BaseModel):
    latest_evaluation_run_id: int | None
    total_cases: int
    hit_rate: float | None
    citation_coverage: float | None
    expected_term_coverage: float | None
    needs_review_rate: float | None
    average_confidence: float | None


class OpsDashboardActionItemRead(BaseModel):
    code: str
    title: str
    detail: str
    severity: str
    href: str
    count: int


class OpsDashboardDataSourceRead(BaseModel):
    mode: str
    label: str
    source: str
    contract_version: str
    aggregation_grain: str
    refresh_model: str
    freshness: str
    completeness: str
    source_tables: list[str]
    excluded_fields: list[str]
    caveats: list[str]
    is_demo: bool
    uses_local_sample: bool
    fallback_reason: str | None


class OpsDashboardSourceWindowRead(BaseModel):
    range: str
    label: str
    start: datetime
    end: datetime
    generated_at: datetime
    timezone: str


class OpsDashboardFilterRead(BaseModel):
    range: str
    channel_id: int | None
    channel_name: str | None
    channel_type: str | None
    is_channel_filtered: bool


class OpsDashboardRead(BaseModel):
    tenant_id: int
    generated_at: datetime
    range: str
    interval_start: datetime
    interval_end: datetime
    channel_id: int | None
    data_mode: str
    data_source: OpsDashboardDataSourceRead
    source_window: OpsDashboardSourceWindowRead
    filters: OpsDashboardFilterRead
    summary: OpsDashboardSummaryRead
    channels: list[OpsDashboardChannelRead]
    funnel: list[OpsDashboardFunnelStageRead]
    trend: list[OpsDashboardTrendBucketRead]
    quality: OpsDashboardQualityRead
    action_items: list[OpsDashboardActionItemRead]
    external_call_performed: bool
    external_platform_write_performed: bool


class OpsAlertRunbookRead(BaseModel):
    summary: str
    first_checks: list[str]
    escalation: str
    suppress_when: str


class OpsAlertRuleRead(BaseModel):
    code: str
    name: str
    category: str
    severity: str
    response_type: str
    status: str
    signal: str
    condition: str
    threshold: str
    duration: str
    current_value: str
    reason: str
    runbook: OpsAlertRunbookRead


class OpsAlertRulesDashboardRead(BaseModel):
    tenant_id: int
    generated_at: datetime
    stale_after_seconds: int
    recent_run_limit: int
    notification_channel_enabled: bool
    notification_sent: bool
    firing_count: int
    page_count: int
    ticket_count: int
    rules: list[OpsAlertRuleRead]
    external_call_performed: bool
    external_platform_write_performed: bool


class OpsMetricRead(BaseModel):
    name: str
    metric_type: str
    value: float
    unit: str
    labels: dict[str, str]
    description: str
    source: str
    status: str


class OpsMetricsSummary(BaseModel):
    total_metrics: int
    firing_alerts: int
    page_alerts: int
    queue_backlog: int
    dead_letter_jobs: int
    failed_worker_runs: int
    open_failure_reviews: int
    external_write_enabled: bool
    ready_for_prometheus_scrape: bool


class OpsMetricsDashboardRead(BaseModel):
    tenant_id: int
    generated_at: datetime
    stale_after_seconds: int
    recent_run_limit: int
    collection_model: str
    scrape_path: str
    summary: OpsMetricsSummary
    metrics: list[OpsMetricRead]
    prometheus_text: str
    external_call_performed: bool
    external_platform_write_performed: bool
