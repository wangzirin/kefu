export interface TenantSummary {
  id: string;
  name: string;
  slug: string;
  plan: string;
}

export interface UserPublicProfile {
  display_name: string;
  signature: string;
  mobile: string;
  phone: string;
  qq: string;
  wechat: string;
}

export interface UserPersonalSettings {
  system_language: string;
  quick_reply_collapsed: boolean;
  quick_reply_double_click_action: "insert" | "send";
  quick_reply_quote_mode: "replace" | "append";
  show_typing_status: boolean;
  default_translate_language: string;
  message_notifications_enabled: boolean;
  auto_reply_enabled: boolean;
  shortcut_send_key: "enter" | "ctrl_enter";
  service_notifications_enabled: boolean;
}

export interface CurrentUser {
  id: string;
  name: string;
  email: string;
  roles: string[];
  permissions: string[];
  tenant: TenantSummary;
  avatar_data_url: string;
  public_profile: UserPublicProfile;
  personal_settings: UserPersonalSettings;
}

export interface LoginRequest {
  tenant_slug: string;
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: "bearer";
  expires_at: string;
  user: CurrentUser;
}

export interface LocalSetupStatus {
  schema_version: string;
  initialized: boolean;
  tenant_count: number;
  user_count: number;
  can_create_first_owner: boolean;
  setup_mode: string;
  first_owner_creation_locked: boolean;
  web_password_reset_enabled: boolean;
  env: string;
  dev_bootstrap_enabled: boolean;
  external_write_enabled: boolean;
  trusted_inbound_worker_enabled: boolean;
  local_deployment_ready: boolean;
  readiness_checks: string[];
  blockers: string[];
  first_tenant_slug: string | null;
  first_tenant_name: string | null;
}

export interface LocalOwnerSetupRequest {
  tenant_name: string;
  tenant_slug: string;
  owner_name: string;
  email: string;
  password: string;
}

export interface Channel {
  id: number;
  tenant_id: number;
  type: string;
  name: string;
  reply_mode: string;
  status: string;
  created_at: string | null;
}

export interface AccountUser {
  id: number;
  tenant_id: number;
  name: string;
  email: string;
  status: string;
  roles: string[];
  avatar_data_url?: string;
  public_profile?: Partial<UserPublicProfile>;
  created_at: string | null;
}

export interface AccountRole {
  id: number;
  tenant_id: number;
  code: string;
  name: string;
  created_at: string | null;
}

export interface DiagnosticBundle {
  schema_version: string;
  filename: string;
  generated_at: string;
  tenant: Record<string, unknown>;
  runtime: Record<string, unknown>;
  health: Record<string, unknown>;
  counts: Record<string, number>;
  knowledge: Record<string, unknown>;
  quality: Record<string, unknown>;
  channels: Record<string, unknown>;
  queues: Record<string, unknown>;
  workers: Record<string, unknown>;
  recent_errors: Record<string, unknown>[];
  recent_changes: Record<string, unknown>[];
  safety: Record<string, unknown>;
  warnings: string[];
}

export interface DiagnosticUploadPackage {
  schema_version: string;
  filename: string;
  generated_at: string;
  tenant: Record<string, unknown>;
  authorization: Record<string, unknown>;
  upload_manifest: Record<string, unknown>;
  diagnostic_bundle: DiagnosticBundle;
  safety: Record<string, unknown>;
  warnings: string[];
}

export interface DiagnosticIntakeRecord {
  id: number;
  tenant_id: number;
  intake_id: string;
  status: string;
  validation_status: string;
  package_filename: string;
  diagnostic_bundle_filename: string;
  package_sha256: string;
  diagnostic_bundle_sha256: string;
  package_size_bytes: number;
  source_channel: string;
  rejection_reason: string;
  processing_note: string;
  authorization_summary: Record<string, unknown>;
  safety: Record<string, unknown>;
  received_by_id: number | null;
  handled_by_id: number | null;
  created_at: string;
  updated_at: string;
  handled_at: string | null;
  download_supported: boolean;
}

export interface DiagnosticIntakeList {
  schema_version: string;
  items: DiagnosticIntakeRecord[];
}

export interface DiagnosticIntakeDownload {
  schema_version: string;
  intake_id: string;
  filename: string;
  content_type: string;
  body_encoding: string;
  body: string;
  body_sha256: string;
  body_bytes: number;
  safety: Record<string, unknown>;
}

export interface DiagnosticRemediationRequest {
  id: number;
  tenant_id: number;
  intake_record_id: number;
  request_id: string;
  request_type: string;
  status: string;
  priority: string;
  title: string;
  summary: string;
  recommended_actions: Array<Record<string, unknown>>;
  update_request_manifest: Record<string, unknown>;
  safety: Record<string, unknown>;
  created_by_id: number | null;
  updated_by_id: number | null;
  created_at: string;
  updated_at: string;
  download_supported: boolean;
}

export interface DiagnosticRemediationRequestList {
  schema_version: string;
  items: DiagnosticRemediationRequest[];
}

export interface DiagnosticRemediationRequestDownload {
  schema_version: string;
  request_id: string;
  filename: string;
  content_type: string;
  body_encoding: string;
  body: string;
  body_sha256: string;
  body_bytes: number;
  safety: Record<string, unknown>;
}

export interface LocalBackupRecord {
  id: number;
  tenant_id: number;
  backup_id: string;
  backup_type: string;
  status: string;
  file_name: string;
  file_size_bytes: number;
  sha256: string;
  source_database_label: string;
  source_database_hash: string;
  restore_mode: string;
  manifest_payload: Record<string, unknown>;
  safety: Record<string, unknown>;
  created_by_id: number | null;
  created_at: string | null;
  verified_at: string | null;
  error_message: string;
}

export interface LocalBackupRestoreDryRun {
  schema_version: string;
  restore_dry_run_id: string;
  backup_id: string;
  tenant_id: number;
  generated_at: string | null;
  dry_run: boolean;
  can_restore_now: boolean;
  rehearsal_ready: boolean;
  restore_mode: string;
  backup_verification: Record<string, unknown>;
  current_database: Record<string, unknown>;
  rehearsal_plan: Array<Record<string, unknown>>;
  health_checks: Array<Record<string, unknown>>;
  blockers: string[];
  safety: Record<string, unknown>;
  warnings: string[];
}

export interface LocalMaintenanceGate {
  code: string;
  label: string;
  status: "ready" | "passed" | "warning" | "pending" | "blocked" | string;
  reason: string;
  evidence: Record<string, unknown>;
}

export interface LocalMaintenanceReadiness {
  schema_version: string;
  tenant_id: number;
  generated_at: string | null;
  maturity_status: "ready_for_rehearsal" | "missing_evidence" | "blocked" | string;
  ready_for_customer_maintenance_rehearsal: boolean;
  summary: string;
  counts: Record<string, number>;
  latest: Record<string, unknown>;
  gates: LocalMaintenanceGate[];
  blockers: string[];
  safety: Record<string, unknown>;
  recommended_next_steps: string[];
  recent_audit_events: Array<Record<string, unknown>>;
}

export interface PilotReadinessStep {
  code: string;
  title: string;
  status: string;
  summary: string;
  next_action: string;
  target_href: string;
  blockers: string[];
  evidence: Array<Record<string, unknown>>;
}

export interface PilotReadiness {
  schema_version: string;
  tenant_id: number;
  generated_at: string;
  status: "blocked" | "pilot_candidate_ready_with_internal_data" | "pilot_candidate_ready_with_customer_data" | string;
  status_label: string;
  summary: string;
  steps: PilotReadinessStep[];
  blockers: string[];
  evidence_links: Array<Record<string, unknown>>;
  not_ready_for: string[];
  safety: Record<string, unknown>;
  recommended_next_steps: string[];
  trial_closure_status?: string;
  trial_closure_evidence?: Array<Record<string, unknown>>;
  handoff_archive_status?: string;
  pack8_status?: string;
  pack8_evidence?: Array<Record<string, unknown>>;
  material_intake_package_status?: string;
  material_intake_package_evidence?: Array<Record<string, unknown>>;
  material_validation_fixture_status?: string;
  material_validation_fixture_evidence?: Array<Record<string, unknown>>;
  material_drop_gate_status?: string;
  material_drop_gate_evidence?: Array<Record<string, unknown>>;
  real_customer_material_status?: string;
  real_customer_material_evidence?: Array<Record<string, unknown>>;
  customer_knowledge_retest_status?: string;
  customer_knowledge_retest_evidence?: Array<Record<string, unknown>>;
  shadow_trial_status?: string;
  shadow_trial_evidence?: Array<Record<string, unknown>>;
  frontend_customer_qa_status?: string;
  frontend_customer_qa_evidence?: Array<Record<string, unknown>>;
  frontend_product_polish_status?: string;
  frontend_product_polish_evidence?: Array<Record<string, unknown>>;
  channel_boundary_status?: string;
  channel_boundary_evidence?: Array<Record<string, unknown>>;
  installer_trial_status?: string;
  installer_trial_evidence?: Array<Record<string, unknown>>;
  pack10_status?: string;
  pack10_evidence?: Array<Record<string, unknown>>;
  runtime_facts?: Array<Record<string, unknown>>;
  latest_material_batch?: Record<string, unknown> | null;
  customer_data_ready?: boolean;
  customer_data_readiness_source?: string;
  customer_data_ready_blockers?: string[];
  customer_data_ready_evidence?: Array<Record<string, unknown>>;
  summary_evidence_authority?: string;
}

export interface KnowledgeConfirmationImportItem {
  item_id: string;
  section: string;
  item_name: string;
  review_status: string;
  confirmed_by: string;
  confirmed_at: string;
  reviewer_role: string;
  customer_comment: string;
  needs_change: boolean;
  blockers: string[];
}

export interface KnowledgeConfirmationImportResult {
  schema_version: string;
  tenant_id: number;
  imported_at: string;
  filename: string;
  status: string;
  summary: string;
  total_rows: number;
  confirmed_count: number;
  needs_revision_count: number;
  rejected_count: number;
  pending_count: number;
  accepted_with_notes_count: number;
  revision_items: KnowledgeConfirmationImportItem[];
  rejected_items: KnowledgeConfirmationImportItem[];
  pending_items: KnowledgeConfirmationImportItem[];
  blockers: string[];
  desensitization_risks: string[];
  ready_for_next_retest: boolean;
  formal_customer_signoff_ready: boolean;
  system_prefilled_customer_confirmation: boolean;
  safety: Record<string, unknown>;
}

export interface CustomerMaterialPrecheckResult {
  schema_version: string;
  tenant_id: number;
  checked_at: string;
  status: "ready_for_file_drop" | "blocked" | string;
  summary: string;
  blockers: string[];
  metrics: {
    material_rows?: number;
    trial_question_count?: number;
    record_types?: string[];
    question_action_types?: string[];
    minimum_question_count_required?: number;
    [key: string]: unknown;
  };
  readiness: Record<string, unknown>;
  safety: Record<string, unknown>;
  persisted_batch?: Record<string, unknown> | null;
}

export interface CustomerMaterialBatchList {
  schema_version: string;
  tenant_id: number;
  generated_at: string;
  status: string;
  summary: string;
  batches: Array<Record<string, unknown>>;
  latest_batch?: Record<string, unknown> | null;
  counts: Record<string, number>;
  readiness: Record<string, unknown>;
  safety: Record<string, unknown>;
  next_steps: string[];
}

export interface SafeTestConversationResult {
  schema_version: string;
  tenant_id: number;
  conversation_id: number;
  message_id: number;
  channel_id: number;
  contact_id: number;
  target_href: string;
  summary: string;
  external_write_performed: boolean;
  safety: Record<string, unknown>;
}

export interface CustomerMaterialTemplatePackage {
  schema_version: string;
  tenant_id: number;
  generated_at: string;
  status: string;
  summary: string;
  materials_template_csv: string;
  trial_questions_template_csv: string;
  manifest_template_json: string;
  sample_materials_csv: string;
  sample_trial_questions_csv: string;
  sample_manifest_json: string;
  required_received_filenames: Record<string, string>;
  field_guide: Array<{
    file?: string;
    field?: string;
    required?: boolean;
    description?: string;
    example?: string;
    [key: string]: unknown;
  }>;
  next_steps: string[];
  readiness: Record<string, unknown>;
  safety: Record<string, unknown>;
}

export interface CustomerMaterialHandoffBundle {
  schema_version: string;
  tenant_id: number;
  generated_at: string;
  status: string;
  summary: string;
  filename: string;
  content_type: string;
  body_encoding: "base64" | string;
  body: string;
  included_files: string[];
  required_received_filenames: Record<string, string>;
  next_steps: string[];
  readiness: Record<string, unknown>;
  safety: Record<string, unknown>;
}

export interface SignedUpdatePreflightResult {
  package_id: string;
  package_name: string;
  package_type: "knowledge" | "strategy" | "program";
  package_version: string;
  dry_run: boolean;
  can_stage: boolean;
  can_apply_now: boolean;
  current_app_version: string;
  signature_status: Record<string, unknown>;
  checksum_status: Record<string, unknown>;
  compatibility: Record<string, unknown>;
  backup_plan: Record<string, unknown>;
  health_checks: Array<Record<string, unknown>>;
  operations: Array<Record<string, unknown>>;
  warnings: string[];
  errors: string[];
  safety: Record<string, unknown>;
}

export interface SignedUpdateStagedPackage {
  id: number;
  package_id: string;
  package_name: string;
  package_type: "knowledge" | "strategy" | "program";
  package_version: string;
  status: string;
  current_app_version: string;
  package_digest_sha256: string;
  can_apply_now: boolean;
  backup_required: boolean;
  backup_created: boolean;
  preflight_result: Record<string, unknown>;
  backup_plan: Record<string, unknown>;
  health_checks: Array<Record<string, unknown>>;
  safety: Record<string, unknown>;
  knowledge_import_batch_id: number | null;
  apply_result: Record<string, unknown>;
  rollback_result: Record<string, unknown>;
  staged_by_id: number | null;
  staged_at: string | null;
  applied_at: string | null;
  error_message: string;
}

export interface UserRoleAssignment {
  id: number;
  user_id: number;
  role_id: number;
  created_at: string | null;
}

export interface OutboxDraft {
  id: number;
  tenant_id: number;
  conversation_id: number;
  channel_id: number;
  contact_id: number;
  source_review_task_id: number | null;
  source_workflow_run_id: number | null;
  source_message_id: number | null;
  status: string;
  delivery_status: string;
  reply_text: string;
  idempotency_key: string;
  confirmation_note: string;
  cancellation_reason: string;
  created_at: string | null;
  updated_at: string | null;
  confirmed_at: string | null;
  canceled_at: string | null;
  sent_at: string | null;
}

export interface OutboxSendAttempt {
  id: number;
  outbox_draft_id: number;
  attempt_number: number;
  delivery_mode: string;
  provider: string;
  status: string;
  delivery_status: string;
  external_message_id: string;
  request_payload: Record<string, unknown>;
  response_payload: Record<string, unknown>;
  operator_note: string;
  finished_at: string | null;
  sent_at: string | null;
}

export interface OutboxWorkerRun {
  tenant_id: number;
  mode: string;
  scanned: number;
  processed: number;
  succeeded: number;
  failed: number;
  rate_limited: number;
  rate_limited_draft_ids: number[];
  skipped_draft_ids: number[];
  external_write: boolean;
  rate_limit: Record<string, unknown>;
  attempts: OutboxSendAttempt[];
}

export interface OutboxDeliveryJob {
  id: number;
  tenant_id: number;
  outbox_draft_id: number;
  channel_id: number;
  connector_id: number | null;
  status: string;
  priority: number;
  attempts_count: number;
  max_attempts: number;
  locked_by: string;
  locked_at: string | null;
  next_run_at: string | null;
  idempotency_key: string;
  external_write_requested: boolean;
  external_write_permitted: boolean;
  last_attempt_id: number | null;
  last_error: string;
  dead_letter_reason: string;
  created_by_id: number | null;
  created_at: string | null;
  updated_at: string | null;
  completed_at: string | null;
}

export interface OutboxDeliveryQueueRun {
  tenant_id: number;
  mode: string;
  scanned: number;
  processed: number;
  succeeded: number;
  failed: number;
  blocked: number;
  retry_scheduled: number;
  dead_lettered: number;
  rate_limited: number;
  rate_limited_job_ids: number[];
  skipped_job_ids: number[];
  external_write: boolean;
  kill_switch: Record<string, unknown>;
  attempts: OutboxSendAttempt[];
  jobs: OutboxDeliveryJob[];
}

export interface DeliveryFailureReview {
  id: number;
  tenant_id: number;
  channel_id: number;
  connector_id: number | null;
  receipt_id: number;
  matched_attempt_id: number | null;
  outbox_draft_id: number | null;
  provider: string;
  external_message_id: string;
  provider_status: string;
  provider_error_code: string;
  normalized_status: string;
  severity: string;
  retryable: boolean;
  review_reason: string;
  next_action: string;
  status: string;
  resolution_note: string;
  resolved_by_id: number | null;
  created_at: string | null;
  updated_at: string | null;
  resolved_at: string | null;
}

export interface TrustedInboundWorkerItem {
  message_id: number;
  conversation_id: number;
  status: string;
  idempotency_key: string;
  workflow_run_id: number | null;
  reply_decision_id: number | null;
  knowledge_gap_id: number | null;
  outbox_draft_id: number | null;
  human_review_task_id: number | null;
  decision: string;
  reason: string;
  error_message: string;
  next_action: string;
}

export interface TrustedInboundWorkerRun {
  tenant_id: number;
  mode: string;
  scanned: number;
  processed: number;
  succeeded: number;
  failed: number;
  skipped: number;
  rate_limited: number;
  skipped_message_ids: number[];
  rate_limited_message_ids: number[];
  external_write: boolean;
  rate_limit: Record<string, unknown>;
  items: TrustedInboundWorkerItem[];
}

export interface WorkerHeartbeat {
  id: number;
  tenant_id: number;
  worker_type: string;
  worker_id: string;
  status: string;
  health_status: string;
  last_heartbeat_at: string | null;
  last_run_record_id: number | null;
  last_run_mode: string;
  last_error: string;
  loops_completed: number;
  metadata_payload: Record<string, unknown>;
  created_at: string | null;
  updated_at: string | null;
}

export interface TrustedInboundWorkerRunRecord {
  id: number;
  tenant_id: number;
  worker_id: string;
  mode: string;
  status: string;
  batch_size: number;
  rate_limit_per_minute: number;
  lease_seconds: number;
  scanned: number;
  processed: number;
  succeeded: number;
  failed: number;
  skipped: number;
  rate_limited: number;
  external_write: boolean;
  request_payload: Record<string, unknown>;
  result_payload: Record<string, unknown>;
  error_message: string;
  created_by_id: number | null;
  started_at: string | null;
  finished_at: string | null;
}

export interface RpaCopilotDryRunRequest {
  channel: string;
  customer_name: string;
  text: string;
  attachments?: string[];
  metadata?: Record<string, string>;
}

export interface RpaCopilotMessage {
  message_id: string;
  channel: string;
  customer_name: string;
  text: string;
  received_at: string;
  attachments: string[];
  metadata: Record<string, string>;
}

export interface RpaCopilotKnowledgeHit {
  card_id: string;
  title: string;
  score: number;
  answer: string;
  source: string;
  risk_tags: string[];
}

export interface RpaCopilotDraft {
  text: string;
  route: string;
  confidence: number;
  citations: string[];
  missing_knowledge: boolean;
}

export interface RpaCopilotGuardrail {
  status: string;
  reasons: string[];
  allow_auto_send: boolean;
}

export interface RpaCopilotReplyStrategy {
  intent: string;
  answer_mode: string;
  delivery_mode: string;
  customer_visible_policy: string;
  next_best_action: string;
  quality_signals: string[];
}

export interface RpaCopilotAction {
  kind: string;
  target: string;
  payload: Record<string, unknown>;
  external_write: boolean;
}

export interface RpaCopilotDryRunResponse {
  tenant_id: number;
  operator_user_id: number;
  mode: "research_dry_run";
  message: RpaCopilotMessage;
  hits: RpaCopilotKnowledgeHit[];
  draft: RpaCopilotDraft;
  guardrail: RpaCopilotGuardrail;
  reply_strategy: RpaCopilotReplyStrategy;
  actions: RpaCopilotAction[];
  audit: Record<string, unknown>;
}

export interface WorkerHealthSummary {
  total_workers: number;
  healthy_workers: number;
  stale_workers: number;
  failed_workers: number;
  running_workers: number;
  idle_workers: number;
  external_write_enabled: boolean;
  trusted_inbound_worker_enabled: boolean;
  requires_attention: boolean;
}

export interface OpsRisk {
  code: string;
  severity: string;
  title: string;
  detail: string;
  next_action: string;
}

export interface WorkerHealthDashboard {
  tenant_id: number;
  generated_at: string;
  stale_after_seconds: number;
  summary: WorkerHealthSummary;
  heartbeats: WorkerHeartbeat[];
  recent_trusted_inbound_runs: TrustedInboundWorkerRunRecord[];
  risks: OpsRisk[];
  external_call_performed: boolean;
  external_platform_write_performed: boolean;
}

export interface BusinessOpsDashboardSummary {
  inbound_conversations: number;
  inbound_messages: number;
  open_reviews: number;
  high_risk_reviews: number;
  pending_outbox_drafts: number;
  ready_outbox_drafts: number;
  open_failure_reviews: number;
  blocked_delivery_jobs: number;
  open_knowledge_gaps: number;
  open_tickets: number;
  open_leads: number;
  average_wait_minutes: number;
  ai_draft_coverage: number;
  manual_review_pressure: number;
  exception_pressure: number;
  health_score: number;
}

export interface BusinessOpsDashboardChannel {
  channel_id: number;
  channel_name: string;
  channel_type: string;
  inbound_conversations: number;
  open_reviews: number;
  pending_outbox_drafts: number;
  ready_outbox_drafts: number;
  open_failure_reviews: number;
  blocked_delivery_jobs: number;
  workload: number;
  exception_count: number;
}

export interface BusinessOpsDashboardFunnelStage {
  key: string;
  label: string;
  count: number;
}

export interface BusinessOpsDashboardTrendBucket {
  key: string;
  label: string;
  inbound: number;
  reviews: number;
  drafts: number;
  exceptions: number;
}

export interface BusinessOpsDashboardQuality {
  latest_evaluation_run_id: number | null;
  total_cases: number;
  hit_rate: number | null;
  citation_coverage: number | null;
  expected_term_coverage: number | null;
  needs_review_rate: number | null;
  average_confidence: number | null;
}

export interface BusinessOpsDashboardActionItem {
  code: string;
  title: string;
  detail: string;
  severity: string;
  href: string;
  count: number;
}

export interface BusinessOpsDashboardDataSource {
  mode: string;
  label: string;
  source: string;
  contract_version: string;
  aggregation_grain: string;
  refresh_model: string;
  freshness: string;
  completeness: string;
  source_tables: string[];
  excluded_fields: string[];
  caveats: string[];
  is_demo: boolean;
  uses_local_sample: boolean;
  fallback_reason: string | null;
}

export interface BusinessOpsDashboardSourceWindow {
  range: "today" | "7d" | "30d";
  label: string;
  start: string;
  end: string;
  generated_at: string;
  timezone: string;
}

export interface BusinessOpsDashboardFilters {
  range: "today" | "7d" | "30d";
  channel_id: number | null;
  channel_name: string | null;
  channel_type: string | null;
  is_channel_filtered: boolean;
}

export interface BusinessOpsDashboard {
  tenant_id: number;
  generated_at: string;
  range: "today" | "7d" | "30d";
  interval_start: string;
  interval_end: string;
  channel_id: number | null;
  data_mode: string;
  data_source: BusinessOpsDashboardDataSource;
  source_window: BusinessOpsDashboardSourceWindow;
  filters: BusinessOpsDashboardFilters;
  summary: BusinessOpsDashboardSummary;
  channels: BusinessOpsDashboardChannel[];
  funnel: BusinessOpsDashboardFunnelStage[];
  trend: BusinessOpsDashboardTrendBucket[];
  quality: BusinessOpsDashboardQuality;
  action_items: BusinessOpsDashboardActionItem[];
  external_call_performed: boolean;
  external_platform_write_performed: boolean;
}

export interface OpsAlertRunbook {
  summary: string;
  first_checks: string[];
  escalation: string;
  suppress_when: string;
}

export interface OpsAlertRule {
  code: string;
  name: string;
  category: string;
  severity: string;
  response_type: string;
  status: string;
  signal: string;
  condition: string;
  threshold: string;
  duration: string;
  current_value: string;
  reason: string;
  runbook: OpsAlertRunbook;
}

export interface OpsAlertRulesDashboard {
  tenant_id: number;
  generated_at: string;
  stale_after_seconds: number;
  recent_run_limit: number;
  notification_channel_enabled: boolean;
  notification_sent: boolean;
  firing_count: number;
  page_count: number;
  ticket_count: number;
  rules: OpsAlertRule[];
  external_call_performed: boolean;
  external_platform_write_performed: boolean;
}

export interface OpsMetric {
  name: string;
  metric_type: string;
  value: number;
  unit: string;
  labels: Record<string, string>;
  description: string;
  source: string;
  status: string;
}

export interface OpsMetricsSummary {
  total_metrics: number;
  firing_alerts: number;
  page_alerts: number;
  queue_backlog: number;
  dead_letter_jobs: number;
  failed_worker_runs: number;
  open_failure_reviews: number;
  external_write_enabled: boolean;
  ready_for_prometheus_scrape: boolean;
}

export interface OpsMetricsDashboard {
  tenant_id: number;
  generated_at: string;
  stale_after_seconds: number;
  recent_run_limit: number;
  collection_model: string;
  scrape_path: string;
  summary: OpsMetricsSummary;
  metrics: OpsMetric[];
  prometheus_text: string;
  external_call_performed: boolean;
  external_platform_write_performed: boolean;
}

export interface ConversationInboxItem {
  id: number;
  tenant_id: number;
  channel_id: number;
  channel_type: string;
  channel_name: string;
  contact_id: number;
  contact_display_name: string;
  assigned_user_id: number | null;
  assigned_team_id: number | null;
  status: string;
  priority: string;
  subject: string;
  last_message_at: string | null;
  created_at: string | null;
  last_message_preview: string;
  last_message_direction: string | null;
  last_customer_message_at: string | null;
  waiting_minutes: number;
  sla_status: string;
  sla_due_at: string | null;
  human_review_open_count: number;
  outbox_pending_count: number;
  delivery_failure_open_count: number;
  next_action: string;
}

export interface ConversationInboxList {
  items: ConversationInboxItem[];
  page: number;
  page_size: number;
  total: number;
}

export interface MessageRead {
  id: number;
  conversation_id: number;
  direction: "inbound" | "outbound";
  sender_type: string;
  content: string;
  external_message_id: string;
  created_at: string | null;
}

export interface MessageCreatePayload {
  direction: "inbound" | "outbound";
  sender_type: string;
  content: string;
  external_message_id?: string;
}

export interface ConversationDetail {
  id: number;
  tenant_id: number;
  channel_id: number;
  contact_id: number;
  assigned_user_id: number | null;
  assigned_team_id: number | null;
  status: string;
  priority: string;
  subject: string;
  last_message_at: string | null;
  created_at: string | null;
  messages: MessageRead[];
}

export interface SupportTicket {
  id: number;
  tenant_id: number;
  conversation_id: number;
  channel_id: number;
  channel_name: string;
  channel_type: string;
  contact_id: number;
  contact_display_name: string;
  subject: string;
  description: string;
  status: string;
  priority: string;
  source_type: string;
  source_ref: string;
  assigned_user_id: number | null;
  assigned_team_id: number | null;
  sla_target_minutes: number;
  sla_due_at: string | null;
  sla_status: string;
  resolution_note: string;
  created_by_id: number | null;
  updated_by_id: number | null;
  resolved_by_id: number | null;
  created_at: string | null;
  updated_at: string | null;
  resolved_at: string | null;
}

export interface SupportTicketList {
  items: SupportTicket[];
  page: number;
  page_size: number;
  total: number;
}

export interface SalesLead {
  id: number;
  tenant_id: number;
  contact_id: number;
  contact_display_name: string;
  channel_id: number;
  channel_name: string;
  channel_type: string;
  conversation_id: number | null;
  title: string;
  summary: string;
  stage: string;
  intent_level: string;
  expected_budget: string;
  next_step: string;
  owner_user_id: number | null;
  source_type: string;
  source_ref: string;
  latest_message_preview: string;
  next_follow_up_at: string | null;
  closed_at: string | null;
  created_by_id: number | null;
  updated_by_id: number | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface SalesLeadList {
  items: SalesLead[];
  page: number;
  page_size: number;
  total: number;
}

export interface ContactConversationSummary {
  id: number;
  channel_id: number;
  channel_name: string;
  channel_type: string;
  status: string;
  priority: string;
  subject: string;
  last_message_at: string | null;
  last_message_preview: string;
}

export interface ContactTicketSummary {
  id: number;
  subject: string;
  status: string;
  priority: string;
  sla_status: string;
  updated_at: string | null;
}

export interface ContactProfile {
  id: number;
  tenant_id: number;
  display_name: string;
  phone: string;
  wechat: string;
  created_at: string | null;
  conversation_count: number;
  open_conversation_count: number;
  support_ticket_count: number;
  open_support_ticket_count: number;
  lead_count: number;
  active_lead_count: number;
  highest_intent_level: string;
  latest_channel_id: number | null;
  latest_channel_name: string;
  latest_channel_type: string;
  last_message_at: string | null;
  last_message_preview: string;
  next_action: string;
}

export interface ContactProfileDetail extends ContactProfile {
  recent_conversations: ContactConversationSummary[];
  open_leads: SalesLead[];
  open_tickets: ContactTicketSummary[];
}

export interface ContactProfileList {
  items: ContactProfile[];
  page: number;
  page_size: number;
  total: number;
}

export interface ConversationAssignmentResponse {
  id: number;
  tenant_id: number;
  channel_id: number;
  contact_id: number;
  assigned_user_id: number | null;
  assigned_team_id: number | null;
  status: string;
  priority: string;
  subject: string;
  last_message_at: string | null;
  created_at: string | null;
}

export type ConversationWorkflowActionName =
  | "claim"
  | "release"
  | "transfer"
  | "close"
  | "resolve"
  | "follow_up"
  | "wait_customer"
  | "reopen"
  | "note";

export interface KnowledgeDocument {
  id: number;
  tenant_id: number;
  title: string;
  source_type: string;
  source_uri: string;
  content_hash: string;
  tags: string[];
  status: string;
  ingestion_status: string;
  chunk_count: number;
  created_by_id: number | null;
  updated_by_id: number | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface KnowledgeDocumentList {
  items: KnowledgeDocument[];
  page: number;
  page_size: number;
  total: number;
}

export interface KnowledgeDocumentPublishGateCase {
  evaluation_case_id: number;
  status: string;
  failure_reason: string;
  blocking: boolean;
  advisory: boolean;
  top_confidence: number;
  top_chunk_id: number | null;
  citation_present: boolean;
  expected_terms_found: boolean;
  matched_terms: string[];
}

export interface KnowledgeDocumentPublishGateResult {
  document: KnowledgeDocument;
  gap: KnowledgeGap | null;
  evaluation_set_id: number | null;
  evaluation_run: KnowledgeEvaluationRun | null;
  checked_case_ids: number[];
  case_results: KnowledgeDocumentPublishGateCase[];
  can_publish: boolean;
  published: boolean;
  blocking_reasons: string[];
  advisory_reasons: string[];
  checks: Record<string, unknown>;
  message: string;
}

export interface KnowledgeDocumentPublication {
  id: number;
  tenant_id: number;
  document_id: number;
  gap_id: number | null;
  publication_type: string;
  status: string;
  from_status: string;
  to_status: string;
  evaluation_set_id: number | null;
  evaluation_run_id: number | null;
  checked_case_ids: number[];
  case_results: Record<string, unknown>[];
  blocking_reasons: string[];
  advisory_reasons: string[];
  checks: Record<string, unknown>;
  document_snapshot: Record<string, unknown>;
  previous_publication_id: number | null;
  rollback_target_publication_id: number | null;
  rollback_reason: string;
  external_write_performed: boolean;
  model_call_performed: boolean;
  created_by_id: number | null;
  created_at: string | null;
}

export interface KnowledgeDocumentPublicationList {
  items: KnowledgeDocumentPublication[];
  page: number;
  page_size: number;
  total: number;
}

export interface KnowledgeChunk {
  id: number;
  tenant_id: number;
  document_id: number;
  chunk_index: number;
  section_title: string;
  page_number: number | null;
  content: string;
  content_hash: string;
  source_uri: string;
  char_start: number;
  char_end: number;
  token_count: number;
  embedding_signature: Record<string, unknown>;
  status: string;
  citation: Record<string, unknown>;
  created_at: string | null;
}

export interface KnowledgeDocumentSearchMatch {
  chunk_id: number;
  document_id: number;
  document_title: string;
  chunk_index: number;
  section_title: string;
  source_type: string;
  source_uri: string;
  content_preview: string;
  score: number;
  confidence: number;
  bm25_score: number;
  vector_score: number;
  reranker_score: number;
  matched_terms: string[];
  citation: Record<string, unknown>;
}

export interface KnowledgeDocumentSearchResponse {
  query: string;
  retrieval_mode: string;
  vector_engine: string;
  vector_store: string;
  retrieval_backend: string;
  vector_index_status: string;
  embedding_provider: string;
  embedding_model: string;
  reranker: string;
  total_candidates: number;
  matches: KnowledgeDocumentSearchMatch[];
}

export interface KnowledgeMeshNode {
  key: string;
  label: string;
  status: string;
  total_count: number;
  healthy_count: number;
  risk_count: number;
  evidence: string;
  next_action: string;
}

export interface KnowledgeMeshProvenanceStep {
  key: string;
  label: string;
  status: string;
  observed_count: number;
  evidence: string;
  blocker: string;
}

export interface KnowledgeMemoryMeshOverview {
  schema_version: string;
  tenant_id: number;
  generated_at: string;
  status: string;
  summary: string;
  nodes: KnowledgeMeshNode[];
  provenance_steps: KnowledgeMeshProvenanceStep[];
  source_authority: Record<string, unknown>;
  quality_loop: Record<string, unknown>;
  readiness: Record<string, unknown>;
  boundaries: Record<string, unknown>;
}

export type BusinessObjectType = "product" | "service" | "package" | "course" | "project" | "store";
export type KnowledgeStatus = "draft" | "active" | "archived";

export interface BusinessObject {
  id: number;
  tenant_id: number;
  type: BusinessObjectType;
  title: string;
  external_id: string;
  summary: string;
  attrs_json: Record<string, unknown>;
  aliases: string[];
  knowledge_card_count: number;
  status: KnowledgeStatus;
  created_by_id: number | null;
  updated_by_id: number | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface BusinessObjectList {
  items: BusinessObject[];
  page: number;
  page_size: number;
  total: number;
}

export interface ObjectKnowledgeCard {
  id: number;
  tenant_id: number;
  business_object_id: number;
  question: string;
  answer: string;
  trigger_keywords: string[];
  media_refs: string[];
  scope: Record<string, unknown>;
  source: string;
  version: number;
  status: KnowledgeStatus;
  created_by_id: number | null;
  updated_by_id: number | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface ObjectKnowledgeCardList {
  items: ObjectKnowledgeCard[];
  page: number;
  page_size: number;
  total: number;
}

export interface KnowledgeUpdatePackageOperation {
  action: "create" | "skip" | "error" | string;
  resource_type: string;
  title: string;
  reason: string;
  ref: string;
  target: Record<string, unknown>;
}

export interface KnowledgeUpdatePackageResult {
  tenant_id: number;
  package_id: string;
  package_name: string;
  schema_version: string;
  dry_run: boolean;
  can_apply: boolean;
  import_batch_id: number | null;
  operation_counts: Record<"create" | "skip" | "error", number>;
  operations: KnowledgeUpdatePackageOperation[];
  created: Record<string, number[]>;
  skipped: Record<string, unknown>[];
  errors: Record<string, unknown>[];
  warnings: string[];
  backup_snapshot: Record<string, unknown>;
  safety: Record<string, unknown>;
}

export interface TenantReplyPolicy {
  auto_reply_threshold: number | null;
  manual_review_threshold: number | null;
  blocked_policy_terms: string[];
  manual_review_terms: string[];
  force_draft_only: boolean;
}

export interface TenantReplyStrategy {
  tenant_id: number;
  strategy_id: string;
  strategy_version: string;
  status: string;
  reply_policy: TenantReplyPolicy;
  model_routing: Record<string, unknown>;
  updated_by_id: number | null;
  updated_at: string | null;
  created_at: string | null;
  source: string;
  external_write_performed: boolean;
  model_call_performed: boolean;
}

export interface RagGovernanceMetric {
  label: string;
  value: number | string | null;
  unit: string;
  note: string;
}

export interface RagGovernanceGate {
  code: string;
  label: string;
  status: "passed" | "warning" | "blocked";
  reason: string;
  evidence: Record<string, unknown>;
}

export interface RagCostGovernanceSummary {
  tenant_id: number;
  schema_version: string;
  maturity_status: "blocked" | "candidate" | "ready_for_controlled_pilot";
  summary: string;
  knowledge_metrics: RagGovernanceMetric[];
  vector_profile: {
    configured_embedding_provider: string;
    configured_embedding_model: string;
    configured_vector_store: string;
    configured_reranker: string;
    indexed_chunk_count: number;
    pgvector_chunk_count: number;
    sqlite_vector_chunk_count: number;
    latest_vector_index_plan: Record<string, unknown> | null;
  };
  latest_evaluation: {
    run_id: number | null;
    evaluation_set_id: number | null;
    run_mode: string;
    total_cases: number;
    hit_rate: number;
    citation_coverage: number;
    expected_term_coverage: number;
    unsupported_answer_rate: number | null;
    created_at: string | null;
  };
  latest_provider_smoke: {
    run_id: number | null;
    status: string;
    embedding_provider: string;
    embedding_model: string;
    vector_store: string;
    estimated_input_tokens: number;
    estimated_cost: number;
    cost_currency: string;
    provider_call_performed: boolean;
    created_at: string | null;
  };
  model_policy: {
    strategy_status: string;
    strategy_version: string;
    auto_reply_threshold: number | null;
    manual_review_threshold: number | null;
    force_draft_only: boolean;
    blocked_policy_terms_count: number;
    manual_review_terms_count: number;
    recent_reply_decision_count: number;
    recent_model_call_record_count: number;
    estimated_model_cost: number | null;
    cost_currency: string;
    cost_source: string;
    budget_guard_enabled: boolean;
    daily_budget_limit: number;
    monthly_budget_limit: number;
    single_call_budget_limit: number;
    pricing_source: string;
    pricing_version: string;
  };
  answer_quality: {
    latest_evaluation_run_id: number | null;
    total_cases: number;
    final_answer_sampled_cases: number;
    final_answer_sample_coverage: number;
    final_answer_factuality_labeled_cases: number;
    final_answer_factuality_rate: number | null;
    citation_sufficient_labeled_cases: number;
    citation_sufficiency_rate: number | null;
    forbidden_commitment_labeled_cases: number;
    forbidden_commitment_pass_rate: number | null;
    handoff_labeled_cases: number;
    handoff_correctness: number | null;
    citation_snapshot_count: number;
    no_citation_snapshot_count: number;
    complete_accuracy_measured: boolean;
    quality_source: string;
    note: string;
  };
  production_readiness: {
    status: "blocked" | "candidate" | "ready_for_controlled_pilot";
    production_switch_allowed: boolean;
    postgres_runtime_ready: boolean;
    pgvector_runtime_ready: boolean;
    configured_pgvector: boolean;
    indexed_chunk_count: number;
    pgvector_chunk_count: number;
    sqlite_vector_chunk_count: number;
    real_customer_material_ready: boolean;
    customer_material_batch_status: string;
    customer_material_question_count: number;
    customer_question_bank_ready: boolean;
    active_evaluation_cases: number;
    retrieval_evaluation_ready: boolean;
    final_answer_quality_ready: boolean;
    embedding_cost_record_ready: boolean;
    model_cost_record_ready: boolean;
    budget_policy_ready: boolean;
    blockers: string[];
    not_ready_for: string[];
    retrieval_strategy_rules: Record<string, string>;
    safety: Record<string, unknown>;
  };
  gates: RagGovernanceGate[];
  recommended_next_steps: string[];
  safety: Record<string, unknown>;
}

export interface LlmOpsReadinessSummary {
  tenant_id: number;
  schema_version: string;
  status:
    | "blocked"
    | "llm_ops_observability_candidate"
    | "llm_ops_observability_ready_not_redteam_complete"
    | "llm_ops_ready_for_controlled_pilot";
  summary: string;
  model_gateway: {
    gateway_version: string;
    strategy_status: string;
    strategy_version: string;
    prompt_policy_version: string;
    explicit_provider_no_silent_fallback: boolean;
    auto_route_fallback_allowed: boolean;
    force_draft_only: boolean;
    budget_guard_enabled: boolean;
  };
  cost_ledger: {
    model_call_count: number;
    succeeded_count: number;
    failed_count: number;
    degraded_count: number;
    budget_blocked_count: number;
    external_provider_call_count: number;
    deterministic_call_count: number;
    estimated_cost: number;
    currency: string;
    provider_count: number;
    model_count: number;
    pricing_version_count: number;
    missing_pricing_count: number;
    raw_text_logged_count: number;
    average_latency_ms: number | null;
  };
  trace_coverage: {
    reply_decision_count: number;
    reply_decisions_with_provenance: number;
    model_calls_with_provenance: number;
    citation_snapshot_count: number;
    no_citation_snapshot_count: number;
    evaluation_run_count: number;
    final_answer_labeled_cases: number;
    trace_ready: boolean;
    quality_label_ready: boolean;
  };
  redteam_readiness: {
    source: "database_evaluation_tables";
    internal_sample_cases: number;
    internal_sample_only: boolean;
    redteam_case_count: number;
    required_minimum_cases: number;
    required_categories: string[];
    missing_categories: string[];
    category_coverage_ready: boolean;
    prompt_injection_cases: number;
    jailbreak_cases: number;
    privacy_leak_cases: number;
    forbidden_commitment_cases: number;
    over_permission_cases: number;
    redteam_labeled_cases: number;
    all_active_cases_labeled: boolean;
    redteam_failed_cases: number;
    failures_requiring_quality_review: number;
    failures_with_quality_review_items: number;
    unresolved_redteam_failures: number;
    failures_entered_quality_review: boolean;
    readiness: "not_started" | "case_bank_ready" | "labeled_with_failures" | "ready_for_controlled_pilot";
  };
  gates: Array<{
    code: string;
    label: string;
    status: "passed" | "warning" | "blocked";
    reason: string;
    evidence: Record<string, unknown>;
  }>;
  blockers: string[];
  recommended_next_steps: string[];
  not_ready_for: string[];
  safety: Record<string, unknown>;
}

export type ReplyDecisionState =
  | "auto_reply_ready"
  | "manual_gate_required"
  | "knowledge_gap"
  | "blocked_by_policy"
  | "draft_only";

export type ReplyDeliveryMode = "draft_only" | "human_review" | "external_write_allowed" | "blocked";

export interface ReplyDecision {
  id: number;
  tenant_id: number;
  conversation_id: number;
  message_id: number;
  channel_id: number;
  business_object_id: number | null;
  object_knowledge_card_id: number | null;
  workflow_run_id: number | null;
  state: ReplyDecisionState;
  reason: string;
  confidence: number;
  delivery_mode: ReplyDeliveryMode;
  draft_reply: string;
  matched_terms: string[];
  decision_payload: Record<string, unknown>;
  external_write_allowed: boolean;
  idempotency_key: string;
  created_by_id: number | null;
  created_at: string | null;
}

export interface ReplyDecisionList {
  items: ReplyDecision[];
  page: number;
  page_size: number;
  total: number;
}

export interface KnowledgeVectorIndexRebuild {
  tenant_id: number;
  document_id: number | null;
  status: string;
  vector_store: string;
  retrieval_backend: string;
  vector_index_status: string;
  embedding_provider: string;
  embedding_model: string;
  embedding_dimension: number;
  reranker: string;
  total_chunks: number;
  reindexed_chunks: number;
  skipped_chunks: number;
  failed_chunks: number;
  failure_reasons: string[];
}

export interface KnowledgeEvaluationCase {
  id: number;
  tenant_id: number;
  evaluation_set_id: number;
  external_case_id: string;
  source_channel: string;
  source_category: string;
  question: string;
  question_type: string;
  expected_terms: string[];
  expected_source_uri: string;
  expected_document_title: string;
  expected_chunk_ids: number[];
  must_have_all_evidence: boolean;
  expected_human_review: boolean;
  allow_auto_reply: boolean;
  forbidden_terms: string[];
  risk_level: string;
  annotation_notes: string;
  required_citation: boolean;
  priority: number;
  status: string;
  created_at: string | null;
}

export interface KnowledgeEvaluationSet {
  id: number;
  tenant_id: number;
  name: string;
  description: string;
  status: string;
  evaluation_mode: string;
  case_count: number;
  cases: KnowledgeEvaluationCase[];
  created_by_id: number | null;
  updated_by_id: number | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface KnowledgeEvaluationSetList {
  items: KnowledgeEvaluationSet[];
  page: number;
  page_size: number;
  total: number;
}

export interface CustomerServiceQuestionBankCasePayload {
  external_case_id?: string;
  source_channel?: string;
  source_category?: string;
  question: string;
  question_type?: string;
  expected_terms?: string[];
  expected_source_uri?: string;
  expected_document_title?: string;
  expected_chunk_ids?: number[];
  must_have_all_evidence?: boolean;
  expected_human_review?: boolean;
  allow_auto_reply?: boolean;
  forbidden_terms?: string[];
  risk_level?: string;
  annotation_notes?: string;
  required_citation?: boolean;
  priority?: number;
  status?: "draft" | "active" | "archived";
}

export interface CustomerServiceQuestionBankImportPayload {
  name: string;
  description?: string;
  source_label?: string;
  status?: "draft" | "active" | "archived";
  evaluation_mode?: "customer_service_retrieval";
  minimum_case_count?: number;
  maximum_case_count?: number;
  allow_sensitive_rows?: boolean;
  cases: CustomerServiceQuestionBankCasePayload[];
}

export interface CustomerServiceQuestionBankPrecheck {
  tenant_id: number;
  status: string;
  can_import: boolean;
  imported: boolean;
  evaluation_set_id: number | null;
  case_count: number;
  coverage_summary: Record<string, unknown>;
  sensitive_rows: Array<Record<string, unknown>>;
  validation_errors: string[];
  case_catalog: Array<Record<string, unknown>>;
  raw_text_included: boolean;
  provider_call_performed: boolean;
  external_write_performed: boolean;
}

export interface KnowledgeEvaluationRunCase {
  id: number;
  tenant_id: number;
  evaluation_run_id: number;
  evaluation_case_id: number;
  question: string;
  status: string;
  top_score: number;
  top_confidence: number;
  top_chunk_id: number | null;
  top_document_id: number | null;
  citation_present: boolean;
  expected_terms_found: boolean;
  matched_terms: string[];
  failure_reason: string;
  result_payload: Record<string, unknown>;
  created_at: string | null;
}

export interface KnowledgeEvaluationRun {
  id: number;
  tenant_id: number;
  evaluation_set_id: number;
  run_mode: string;
  retrieval_mode: string;
  vector_engine: string;
  total_cases: number;
  answered_cases: number;
  no_hit_cases: number;
  passed_cases: number;
  failed_cases: number;
  needs_review_cases: number;
  citation_covered_cases: number;
  expected_term_covered_cases: number;
  hit_rate: number;
  citation_coverage: number;
  expected_term_coverage: number;
  average_confidence: number;
  unsupported_answer_rate: number | null;
  summary_payload: Record<string, unknown>;
  case_results: KnowledgeEvaluationRunCase[];
  created_by_id: number | null;
  created_at: string | null;
}

export interface KnowledgeEvaluationRunSummary {
  id: number;
  tenant_id: number;
  evaluation_set_id: number;
  run_mode: string;
  retrieval_mode: string;
  vector_engine: string;
  total_cases: number;
  answered_cases: number;
  no_hit_cases: number;
  passed_cases: number;
  failed_cases: number;
  needs_review_cases: number;
  citation_covered_cases: number;
  expected_term_covered_cases: number;
  hit_rate: number;
  citation_coverage: number;
  expected_term_coverage: number;
  average_confidence: number;
  unsupported_answer_rate: number | null;
  summary_payload: Record<string, unknown>;
  created_by_id: number | null;
  created_at: string | null;
}

export interface KnowledgeEvaluationRunList {
  items: KnowledgeEvaluationRunSummary[];
  page: number;
  page_size: number;
  total: number;
}

export interface KnowledgeEvaluationRunReport {
  evaluation_run_id: number;
  evaluation_set_id: number;
  tenant_id: number;
  report_format: "markdown" | "csv";
  filename: string;
  content_type: string;
  body: string;
  raw_text_included: boolean;
  provider_call_performed: boolean;
  external_write_performed: boolean;
  summary: Record<string, unknown>;
}

export type FactualityLabelStatus =
  | "correct"
  | "partially_correct"
  | "incorrect"
  | "needs_human_review"
  | "not_applicable";

export interface KnowledgeEvaluationRunCaseFactualityLabelResult {
  tenant_id: number;
  evaluation_run_id: number;
  evaluation_run_case_id: number;
  final_answer_factuality_status: FactualityLabelStatus;
  final_answer_factuality_measured: boolean;
  final_answer_factuality_rate: number | null;
  final_answer_factuality_labeled_cases: number;
  total_cases: number;
  updated_run: KnowledgeEvaluationRun;
  raw_text_included: boolean;
  model_call_performed: boolean;
  external_platform_write_performed: boolean;
}

export interface KnowledgeEvaluationRunCaseFinalAnswerSampleResult {
  tenant_id: number;
  evaluation_run_id: number;
  evaluation_run_case_id: number;
  final_answer_sampled_cases: number;
  final_answer_sample_coverage: number;
  total_cases: number;
  updated_run: KnowledgeEvaluationRun;
  audit_raw_text_included: boolean;
  model_call_performed: boolean;
  external_platform_write_performed: boolean;
}

export interface KnowledgeEvaluationRunCaseFactualityBatchLabelResult {
  tenant_id: number;
  evaluation_run_id: number;
  labeled_cases: number;
  final_answer_factuality_rate: number | null;
  final_answer_factuality_labeled_cases: number;
  total_cases: number;
  updated_run: KnowledgeEvaluationRun;
  audit_raw_text_included: boolean;
  model_call_performed: boolean;
  external_platform_write_performed: boolean;
}

export interface KnowledgeEvaluationRunFinalAnswerLabelExport {
  tenant_id: number;
  evaluation_run_id: number;
  evaluation_set_id: number;
  schema_version: string;
  export_format: "csv";
  filename: string;
  content_type: string;
  body: string;
  row_count: number;
  raw_text_included: boolean;
  question_raw_text_included: boolean;
  final_answer_text_included: boolean;
  provider_call_performed: boolean;
  external_write_performed: boolean;
  summary: Record<string, unknown>;
}

export interface KnowledgeEvaluationRunFinalAnswerLabelImportResult {
  tenant_id: number;
  evaluation_run_id: number;
  evaluation_set_id: number;
  schema_version: string;
  import_format: "csv";
  dry_run: boolean;
  imported: boolean;
  total_rows: number;
  matched_rows: number;
  sample_rows: number;
  label_rows: number;
  skipped_rows: number;
  validation_errors: Array<Record<string, unknown>>;
  warnings: string[];
  status_counts: Record<string, number>;
  updated_run: KnowledgeEvaluationRun | null;
  audit_raw_text_included: boolean;
  provider_call_performed: boolean;
  external_write_performed: boolean;
}

export interface MonthlyQualityReviewMetric {
  key: string;
  label: string;
  value: string;
  numeric_value: number | null;
  status: "ok" | "warning" | "critical" | "missing" | string;
  detail: string;
}

export interface MonthlyQualityReviewCause {
  key: string;
  label: string;
  count: number;
  severity: "ok" | "warning" | "critical" | string;
  detail: string;
  next_action: string;
  target_href: string;
}

export interface MonthlyQualityReviewAction {
  key: string;
  label: string;
  owner: string;
  priority: string;
  evidence: string;
  next_step: string;
  target_href: string;
  status: "open" | "in_progress" | "done" | string;
}

export interface MonthlyQualityReview {
  tenant_id: number;
  schema_version: string;
  period: string;
  period_start: string;
  period_end: string;
  generated_at: string;
  latest_evaluation_run_id: number | null;
  latest_evaluation_set_id: number | null;
  previous_evaluation_run_id: number | null;
  metrics: MonthlyQualityReviewMetric[];
  root_causes: MonthlyQualityReviewCause[];
  action_items: MonthlyQualityReviewAction[];
  knowledge_gap_summary: Record<string, number>;
  human_review_summary: Record<string, number>;
  reply_decision_summary: Record<string, number>;
  trend_summary: Record<string, unknown>;
  data_boundaries: string[];
  next_review_steps: string[];
  raw_text_included: boolean;
  model_call_performed: boolean;
  external_call_performed: boolean;
  external_platform_write_performed: boolean;
}

export interface MonthlyOpsReportMetric {
  key: string;
  label: string;
  value: string;
  status: "ok" | "warning" | "critical" | "missing" | "pending" | "risk" | "blocked" | string;
  detail: string;
}

export interface MonthlyOpsReportSection {
  key: string;
  title: string;
  status: string;
  summary: string;
  metrics: MonthlyOpsReportMetric[];
  evidence: Array<Record<string, unknown>>;
  next_steps: string[];
}

export interface MonthlyOpsReportRisk {
  key: string;
  label: string;
  severity: "ok" | "warning" | "critical" | string;
  detail: string;
  recommended_action: string;
}

export interface MonthlyOpsReport {
  tenant_id: number;
  schema_version: string;
  period: string;
  period_start: string;
  period_end: string;
  generated_at: string;
  report_status: string;
  status_label: string;
  health_score: number;
  health_label: string;
  monthly_health: MonthlyOpsReportSection;
  reply_quality: MonthlyOpsReportSection;
  knowledge_maintenance: MonthlyOpsReportSection;
  model_cost: MonthlyOpsReportSection;
  local_maintenance: MonthlyOpsReportSection;
  risk_items: MonthlyOpsReportRisk[];
  next_month_actions: string[];
  upstream_evidence: Record<string, unknown>;
  data_boundaries: string[];
  safety: Record<string, unknown>;
  raw_text_included: boolean;
  draft_text_included: boolean;
  secret_included: boolean;
  external_call_performed: boolean;
  external_platform_write_performed: boolean;
  real_platform_send_ready: boolean;
  production_sla_ready: boolean;
  formal_customer_signoff_ready: boolean;
}

export interface OnlineReceiptProviderBreakdown {
  provider: string;
  receipt_count: number;
  matched_receipts: number;
  verified_receipts: number;
  delivered_or_read: number;
  needs_review: number;
  unknown_receipts: number;
  delivery_success_rate: number | null;
}

export interface OnlineReceiptQualityGate {
  key: string;
  label: string;
  status: "ok" | "warning" | "critical" | "missing" | string;
  detail: string;
  stop_condition: string;
}

export interface OnlineReceiptQualitySummary {
  tenant_id: number;
  schema_version: string;
  generated_at: string;
  receipt_total: number;
  matched_receipts: number;
  verified_receipts: number;
  delivered_or_read: number;
  failed_or_review: number;
  unknown_receipts: number;
  open_failure_reviews: number;
  receipt_match_rate: number | null;
  verified_receipt_rate: number | null;
  delivery_success_rate: number | null;
  failure_review_rate: number | null;
  status_by_normalized_status: Record<string, number>;
  provider_breakdown: OnlineReceiptProviderBreakdown[];
  quality_gates: OnlineReceiptQualityGate[];
  accuracy_scope_label: string;
  accuracy_boundary: string;
  raw_payload_included: boolean;
  customer_accuracy_completed: boolean;
  real_platform_receipts_required_for_full_accuracy: boolean;
  model_call_performed: boolean;
  external_call_performed: boolean;
  external_platform_write_performed: boolean;
  real_external_write_performed: boolean;
}

export interface CustomerQualityReportMetric {
  key: string;
  label: string;
  value: string;
  status: "ok" | "warning" | "critical" | "missing" | string;
  detail: string;
}

export interface CustomerQualityReportSection {
  key: string;
  title: string;
  status: "ok" | "warning" | "critical" | "missing" | string;
  summary: string;
  evidence: string;
  next_steps: string[];
}

export interface CustomerQualityReportAction {
  key: string;
  label: string;
  owner: string;
  priority: string;
  status: "open" | "in_progress" | "done" | string;
  evidence: string;
  next_step: string;
}

export interface CustomerQualityReportGapRehearsalEvidence {
  schema_version: string;
  phase: string;
  evidence_source: string;
  case_count: number;
  auto_reply_label_count: number;
  handoff_not_applicable_count: number;
  auto_reply_factuality_rate: number;
  citation_sufficient_rate: number;
  forbidden_commitment_pass_rate: number;
  handoff_correct_rate: number;
  ready_for_gap_quality_report_review: boolean;
  ready_for_formal_accuracy_signoff: boolean;
  final_answer_text_exported: boolean;
  provider_call_performed: boolean;
  real_platform_send_performed: boolean;
  external_platform_write_performed: boolean;
  conclusion: string;
  boundary: string;
}

export interface CustomerQualityReport {
  tenant_id: number;
  schema_version: string;
  report_title: string;
  period: string;
  period_start: string;
  period_end: string;
  generated_at: string;
  report_status: string;
  report_status_label: string;
  report_confidence_score: number;
  quality_conclusion: string;
  executive_summary: string[];
  headline_metrics: CustomerQualityReportMetric[];
  sections: CustomerQualityReportSection[];
  action_plan: CustomerQualityReportAction[];
  gap_rehearsal_evidence?: CustomerQualityReportGapRehearsalEvidence | null;
  signoff_checklist: string[];
  data_boundaries: string[];
  source_monthly_review_schema_version: string;
  latest_evaluation_run_id: number | null;
  latest_evaluation_set_id: number | null;
  raw_text_included: boolean;
  model_call_performed: boolean;
  external_call_performed: boolean;
  external_platform_write_performed: boolean;
}

export interface CustomerQualityReportExport {
  tenant_id: number;
  schema_version: string;
  report_schema_version: string;
  export_format: "html" | "xlsx" | "docx" | string;
  filename: string;
  content_type: string;
  body: string;
  body_encoding: "utf-8" | "base64" | string;
  body_sha256: string;
  body_bytes: number;
  period: string;
  generated_at: string;
  report_status: string;
  report_status_label: string;
  signoff_status: string;
  signoff_record: Record<string, unknown>;
  archived: boolean;
  archive_audit_event_id: number | null;
  raw_text_included: boolean;
  final_answer_text_included: boolean;
  reviewer_notes_included: boolean;
  electronic_signature_performed: boolean;
  formal_contract_signoff_performed: boolean;
  model_call_performed: boolean;
  external_call_performed: boolean;
  external_platform_write_performed: boolean;
}

export interface CustomerQualityReportArchiveItem {
  audit_event_id: number;
  tenant_id: number;
  schema_version: string;
  report_schema_version: string;
  export_schema_version: string;
  export_format: "html" | "xlsx" | "docx" | string;
  filename: string;
  content_type: string;
  body_encoding: "utf-8" | "base64" | string;
  body_sha256: string;
  body_bytes: number;
  period: string;
  generated_at: string;
  report_status: string;
  report_status_label: string;
  signoff_status: string;
  body_archived: boolean;
  download_supported: boolean;
  raw_text_included: boolean;
  final_answer_text_included: boolean;
  reviewer_notes_included: boolean;
  electronic_signature_performed: boolean;
  formal_contract_signoff_performed: boolean;
  model_call_performed: boolean;
  external_call_performed: boolean;
  external_platform_write_performed: boolean;
}

export interface CustomerQualityReportArchiveList {
  tenant_id: number;
  schema_version: string;
  page: number;
  page_size: number;
  total: number;
  items: CustomerQualityReportArchiveItem[];
  raw_text_included: boolean;
  final_answer_text_included: boolean;
  reviewer_notes_included: boolean;
  electronic_signature_performed: boolean;
  formal_contract_signoff_performed: boolean;
  model_call_performed: boolean;
  external_call_performed: boolean;
  external_platform_write_performed: boolean;
}

export interface CustomerQualityReportSignoffCreate {
  signoff_status: "accepted" | "accepted_with_notes" | "needs_rework" | "rejected";
  signer_name: string;
  signer_role?: string;
  signer_organization?: string;
  confirmation_method?: "local_record" | "email_confirmation" | "meeting_confirmation" | "offline_signature";
  notes?: string;
}

export interface CustomerQualityReportSignoff {
  tenant_id: number;
  schema_version: string;
  report_schema_version: string;
  export_schema_version: string;
  period: string;
  report_status: string;
  report_status_label: string;
  report_confidence_score: number;
  signoff_status: string;
  signoff_status_label: string;
  signer_display_name: string;
  signer_role: string;
  signer_organization: string;
  confirmation_method: string;
  confirmation_method_label: string;
  notes_recorded: boolean;
  notes_hash: string;
  notes_length: number;
  recorded_at: string;
  recorded_by_user_id: number;
  audit_action: string;
  audit_resource_id: string;
  raw_text_included: boolean;
  final_answer_text_included: boolean;
  reviewer_notes_included: boolean;
  signer_name_raw_included: boolean;
  electronic_signature_performed: boolean;
  formal_contract_signoff_performed: boolean;
  model_call_performed: boolean;
  external_call_performed: boolean;
  external_platform_write_performed: boolean;
}

export interface CustomerQualityReportSignoffListItem {
  audit_event_id: number;
  tenant_id: number;
  schema_version: string;
  report_schema_version: string;
  export_schema_version: string;
  period: string;
  report_status: string;
  report_status_label: string;
  report_confidence_score: number;
  signoff_status: string;
  signoff_status_label: string;
  signer_display_name: string;
  signer_role: string;
  signer_organization: string;
  confirmation_method: string;
  confirmation_method_label: string;
  notes_recorded: boolean;
  notes_hash: string;
  notes_length: number;
  recorded_at: string;
  recorded_by_user_id: number | null;
  audit_action: string;
  audit_resource_id: string;
  raw_text_included: boolean;
  final_answer_text_included: boolean;
  reviewer_notes_included: boolean;
  signer_name_raw_included: boolean;
  electronic_signature_performed: boolean;
  formal_contract_signoff_performed: boolean;
  model_call_performed: boolean;
  external_call_performed: boolean;
  external_platform_write_performed: boolean;
}

export interface CustomerQualityReportSignoffList {
  tenant_id: number;
  schema_version: string;
  page: number;
  page_size: number;
  total: number;
  items: CustomerQualityReportSignoffListItem[];
  raw_text_included: boolean;
  final_answer_text_included: boolean;
  reviewer_notes_included: boolean;
  signer_name_raw_included: boolean;
  model_call_performed: boolean;
  external_call_performed: boolean;
  external_platform_write_performed: boolean;
}

export interface KnowledgeGap {
  id: number;
  tenant_id: number;
  status: string;
  severity: string;
  source_type: string;
  source_ref: string;
  source_title: string;
  source_excerpt: string;
  question_excerpt: string;
  gap_type: string;
  expected_terms: string[];
  evidence_payload: Record<string, unknown>;
  linked_knowledge_card_id: number | null;
  linked_knowledge_document_id: number | null;
  assigned_user_id: number | null;
  created_by_id: number | null;
  updated_by_id: number | null;
  resolved_by_id: number | null;
  resolution_note: string;
  created_at: string | null;
  updated_at: string | null;
  resolved_at: string | null;
}

export interface KnowledgeGapList {
  items: KnowledgeGap[];
  page: number;
  page_size: number;
  total: number;
}

export interface KnowledgeGapSyncResult {
  created_count: number;
  existing_count: number;
  scanned_count: number;
  items: KnowledgeGap[];
}

export interface KnowledgeGapDocumentDraftResult {
  gap: KnowledgeGap;
  document: KnowledgeDocument;
  created: boolean;
  draft_text: string;
}

export interface KnowledgeGapRegressionCaseResult {
  gap: KnowledgeGap;
  evaluation_set: KnowledgeEvaluationSet;
  evaluation_case: KnowledgeEvaluationCase;
  created: boolean;
}

export interface ChannelConnectorConfig {
  id: number;
  tenant_id: number;
  channel_id: number;
  provider: string;
  mode: string;
  status: string;
  display_name: string;
  capabilities: string[];
  public_config: Record<string, unknown>;
  webhook_path: string;
  signature_mode: string;
  secret_status: string;
  external_write_enabled: boolean;
  created_at: string | null;
  updated_at: string | null;
}

export interface ChannelAccount {
  id: number;
  tenant_id: number;
  channel_id: number;
  connector_id: number | null;
  provider: string;
  platform: string;
  account_name: string;
  external_account_id: string;
  store_name: string;
  entrypoint_name: string;
  authorization_status: string;
  access_status: string;
  reply_mode: string;
  health_status: string;
  public_profile: Record<string, unknown>;
  created_by_id: number | null;
  updated_by_id: number | null;
  last_sync_at: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface ChannelAccountPayload {
  connector_id?: number | null;
  provider?: string;
  platform?: string;
  account_name: string;
  external_account_id?: string;
  store_name?: string;
  entrypoint_name?: string;
  authorization_status?: string;
  access_status?: string;
  reply_mode?: string;
  health_status?: string;
  public_profile?: Record<string, unknown>;
}

export interface HumanReviewConversation {
  id: number;
  channel_id: number;
  contact_id: number;
  assigned_user_id: number | null;
  assigned_team_id: number | null;
  status: string;
  priority: string;
  subject: string;
  last_message_at: string | null;
  created_at: string | null;
}

export interface HumanReviewMessage {
  id: number;
  conversation_id: number;
  direction: string;
  sender_type: string;
  content: string;
  external_message_id: string;
  created_at: string | null;
}

export interface HumanReviewWorkflow {
  id: number;
  workflow_type: string;
  status: string;
  current_step: string;
  created_at: string | null;
  updated_at: string | null;
}

export interface HumanReviewEvidence {
  intent: string;
  retrieved_knowledge_count: number;
  confidence: number | null;
  risk_level: string;
  draft_source: string;
  retrieval_mode: string;
  retrieval_engine: string;
  knowledge_matches: Record<string, unknown>[];
  model_call: Record<string, unknown> | null;
  auto_reply_threshold: number | null;
}

export interface HumanReviewInboxItem {
  id: number;
  tenant_id: number;
  workflow_run_id: number;
  conversation_id: number;
  message_id: number | null;
  status: string;
  reason: string;
  risk_level: string;
  draft_reply: string;
  final_reply: string;
  assigned_user_id: number | null;
  reviewer_id: number | null;
  resolution_note: string;
  created_at: string | null;
  resolved_at: string | null;
  conversation: HumanReviewConversation;
  trigger_message: HumanReviewMessage | null;
  workflow: HumanReviewWorkflow;
  evidence: HumanReviewEvidence;
}

async function requestJson<T>(
  path: string,
  options: RequestInit = {},
  token?: string
): Promise<T> {
  const response = await fetchWithAuth(path, options, token);
  if (!response.ok) {
    await throwRequestError(path, response);
  }
  return response.json() as Promise<T>;
}

async function fetchWithAuth(path: string, options: RequestInit = {}, token?: string): Promise<Response> {
  const headers = new Headers(options.headers);
  if (options.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }
  return fetch(path, { ...options, headers });
}

async function throwRequestError(path: string, response: Response): Promise<never> {
  let detail = "";
  try {
    const errorBody = await response.json();
    detail = typeof errorBody.detail === "string" ? `: ${errorBody.detail}` : "";
  } catch {
    detail = "";
  }
  throw new Error(`${path} request failed: ${response.status}${detail}`);
}

export async function getHealth() {
  return requestJson("/api/health");
}

export async function getCurrentUser(token?: string): Promise<CurrentUser> {
  return requestJson<CurrentUser>("/api/auth/me", {}, token);
}

export async function updateCurrentUserProfile(
  token: string,
  payload: {
    name?: string;
    avatar_data_url?: string;
    public_profile: UserPublicProfile;
  }
): Promise<CurrentUser> {
  return requestJson<CurrentUser>(
    "/api/auth/me/profile",
    {
      method: "PATCH",
      body: JSON.stringify(payload)
    },
    token
  );
}

export async function updateCurrentUserSettings(
  token: string,
  personalSettings: UserPersonalSettings
): Promise<CurrentUser> {
  return requestJson<CurrentUser>(
    "/api/auth/me/settings",
    {
      method: "PATCH",
      body: JSON.stringify({ personal_settings: personalSettings })
    },
    token
  );
}

export async function changeCurrentUserPassword(
  token: string,
  payload: { current_password: string; new_password: string }
): Promise<CurrentUser> {
  return requestJson<CurrentUser>(
    "/api/auth/me/password",
    {
      method: "POST",
      body: JSON.stringify(payload)
    },
    token
  );
}

export async function login(payload: LoginRequest): Promise<LoginResponse> {
  return requestJson<LoginResponse>("/api/auth/login", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export async function loginLocalDev(): Promise<LoginResponse> {
  return requestJson<LoginResponse>("/api/auth/dev-local-login", {
    method: "POST"
  });
}

export async function getLocalSetupStatus(): Promise<LocalSetupStatus> {
  return requestJson<LocalSetupStatus>("/api/auth/local-setup/status");
}

export async function createLocalOwner(payload: LocalOwnerSetupRequest): Promise<LoginResponse> {
  return requestJson<LoginResponse>("/api/auth/local-setup/owner", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export async function listHumanReviewInbox(
  tenantId: string | number,
  token: string,
  status = "open"
): Promise<HumanReviewInboxItem[]> {
  return requestJson<HumanReviewInboxItem[]>(
    `/api/tenants/${tenantId}/human-review-inbox?status=${encodeURIComponent(status)}`,
    {},
    token
  );
}

export async function getConversationDetail(conversationId: number, token: string): Promise<ConversationDetail> {
  return requestJson<ConversationDetail>(`/api/conversations/${conversationId}`, {}, token);
}

export async function createConversationMessage(
  conversationId: number,
  token: string,
  payload: MessageCreatePayload
): Promise<MessageRead> {
  return requestJson<MessageRead>(
    `/api/conversations/${conversationId}/messages`,
    {
      method: "POST",
      body: JSON.stringify({
        external_message_id: "",
        ...payload
      })
    },
    token
  );
}

export async function resolveHumanReviewTask(
  taskId: number,
  token: string,
  payload: { decision: "approved" | "rejected"; final_reply?: string; resolution_note?: string }
): Promise<HumanReviewInboxItem> {
  return requestJson<HumanReviewInboxItem>(
    `/api/human-review-tasks/${taskId}`,
    {
      method: "PATCH",
      body: JSON.stringify({
        decision: payload.decision,
        final_reply: payload.final_reply ?? "",
        resolution_note: payload.resolution_note ?? ""
      })
    },
    token
  );
}

export async function createOutboxDraftFromReview(taskId: number, token: string): Promise<OutboxDraft> {
  return requestJson<OutboxDraft>(
    `/api/human-review-tasks/${taskId}/outbox-drafts`,
    {
      method: "POST",
      body: JSON.stringify({})
    },
    token
  );
}

export async function listOutboxDrafts(tenantId: string | number, token: string): Promise<OutboxDraft[]> {
  return requestJson<OutboxDraft[]>(`/api/tenants/${tenantId}/outbox-drafts`, {}, token);
}

export async function confirmOutboxDraft(draftId: number, token: string): Promise<OutboxDraft> {
  return requestJson<OutboxDraft>(
    `/api/outbox-drafts/${draftId}/confirmation`,
    {
      method: "POST",
      body: JSON.stringify({
        confirmation_note: "前端工作台确认进入待发送"
      })
    },
    token
  );
}

export async function listOutboxSendAttempts(draftId: number, token: string): Promise<OutboxSendAttempt[]> {
  return requestJson<OutboxSendAttempt[]>(`/api/outbox-drafts/${draftId}/send-attempts`, {}, token);
}

export async function createDryRunSendAttempt(draftId: number, token: string): Promise<OutboxSendAttempt> {
  return requestJson<OutboxSendAttempt>(
    `/api/outbox-drafts/${draftId}/send-attempts`,
    {
      method: "POST",
      body: JSON.stringify({
        delivery_mode: "dry_run",
        operator_note: "前端工作台触发模拟发送"
      })
    },
    token
  );
}

export async function getChannelConnectorConfig(channelId: number, token: string): Promise<ChannelConnectorConfig> {
  return requestJson<ChannelConnectorConfig>(`/api/channels/${channelId}/connector-config`, {}, token);
}

export async function listTenantChannels(tenantId: string | number, token: string): Promise<Channel[]> {
  return requestJson<Channel[]>(`/api/tenants/${tenantId}/channels`, {}, token);
}

export async function listTenantUsers(tenantId: string | number, token: string): Promise<AccountUser[]> {
  return requestJson<AccountUser[]>(`/api/tenants/${tenantId}/users`, {}, token);
}

export async function listTenantRoles(tenantId: string | number, token: string): Promise<AccountRole[]> {
  return requestJson<AccountRole[]>(`/api/tenants/${tenantId}/roles`, {}, token);
}

export async function getDiagnosticBundle(tenantId: string | number, token: string): Promise<DiagnosticBundle> {
  return requestJson<DiagnosticBundle>(`/api/tenants/${tenantId}/diagnostic-bundle`, {}, token);
}

export async function createDiagnosticUploadPackage(
  tenantId: string | number,
  token: string,
  payload: {
    authorization_note?: string;
    contact_name?: string;
    support_ticket?: string;
  } = {}
): Promise<DiagnosticUploadPackage> {
  return requestJson<DiagnosticUploadPackage>(
    `/api/tenants/${tenantId}/diagnostic-upload-package`,
    {
      method: "POST",
      body: JSON.stringify({
        authorization_note: payload.authorization_note ?? "客户管理员确认授权上传本次脱敏诊断包。",
        contact_name: payload.contact_name ?? "",
        support_ticket: payload.support_ticket ?? ""
      })
    },
    token
  );
}

export async function createDiagnosticIntakeRecord(
  tenantId: string | number,
  token: string,
  payload: {
    upload_package: Record<string, unknown>;
    source_channel?: string;
    processing_note?: string;
  }
): Promise<DiagnosticIntakeRecord> {
  return requestJson<DiagnosticIntakeRecord>(
    `/api/tenants/${tenantId}/diagnostic-intake-records`,
    {
      method: "POST",
      body: JSON.stringify({
        upload_package: payload.upload_package,
        source_channel: payload.source_channel ?? "manual_transfer",
        processing_note: payload.processing_note ?? ""
      })
    },
    token
  );
}

export async function listDiagnosticIntakeRecords(
  tenantId: string | number,
  token: string
): Promise<DiagnosticIntakeList> {
  return requestJson<DiagnosticIntakeList>(`/api/tenants/${tenantId}/diagnostic-intake-records`, {}, token);
}

export async function updateDiagnosticIntakeRecord(
  tenantId: string | number,
  token: string,
  recordId: number,
  payload: {
    status: string;
    processing_note?: string;
  }
): Promise<DiagnosticIntakeRecord> {
  return requestJson<DiagnosticIntakeRecord>(
    `/api/tenants/${tenantId}/diagnostic-intake-records/${recordId}`,
    {
      method: "PATCH",
      body: JSON.stringify({
        status: payload.status,
        processing_note: payload.processing_note ?? ""
      })
    },
    token
  );
}

export async function downloadDiagnosticIntakeRecord(
  tenantId: string | number,
  token: string,
  recordId: number
): Promise<DiagnosticIntakeDownload> {
  return requestJson<DiagnosticIntakeDownload>(
    `/api/tenants/${tenantId}/diagnostic-intake-records/${recordId}/download`,
    {},
    token
  );
}

export async function createDiagnosticRemediationRequest(
  tenantId: string | number,
  token: string,
  intakeRecordId: number,
  payload: {
    request_type?: string;
    title?: string;
    summary?: string;
    priority?: string;
  } = {}
): Promise<DiagnosticRemediationRequest> {
  return requestJson<DiagnosticRemediationRequest>(
    `/api/tenants/${tenantId}/diagnostic-intake-records/${intakeRecordId}/remediation-requests`,
    {
      method: "POST",
      body: JSON.stringify({
        request_type: payload.request_type ?? "knowledge_or_strategy_update",
        title: payload.title ?? "",
        summary: payload.summary ?? "",
        priority: payload.priority ?? "normal"
      })
    },
    token
  );
}

export async function listDiagnosticRemediationRequests(
  tenantId: string | number,
  token: string
): Promise<DiagnosticRemediationRequestList> {
  return requestJson<DiagnosticRemediationRequestList>(
    `/api/tenants/${tenantId}/diagnostic-remediation-requests`,
    {},
    token
  );
}

export async function updateDiagnosticRemediationRequest(
  tenantId: string | number,
  token: string,
  requestId: number,
  payload: {
    status: string;
    summary?: string;
  }
): Promise<DiagnosticRemediationRequest> {
  return requestJson<DiagnosticRemediationRequest>(
    `/api/tenants/${tenantId}/diagnostic-remediation-requests/${requestId}`,
    {
      method: "PATCH",
      body: JSON.stringify({
        status: payload.status,
        summary: payload.summary ?? ""
      })
    },
    token
  );
}

export async function downloadDiagnosticRemediationRequest(
  tenantId: string | number,
  token: string,
  requestId: number
): Promise<DiagnosticRemediationRequestDownload> {
  return requestJson<DiagnosticRemediationRequestDownload>(
    `/api/tenants/${tenantId}/diagnostic-remediation-requests/${requestId}/download`,
    {},
    token
  );
}

export async function createDiagnosticRemediationUpdatePlan(
  tenantId: string | number,
  token: string,
  requestId: number,
  payload: {
    signed_update_package_id: number;
    operator_note?: string;
  }
): Promise<DiagnosticRemediationRequest> {
  return requestJson<DiagnosticRemediationRequest>(
    `/api/tenants/${tenantId}/diagnostic-remediation-requests/${requestId}/signed-update-plan`,
    {
      method: "POST",
      body: JSON.stringify({
        signed_update_package_id: payload.signed_update_package_id,
        operator_note: payload.operator_note ?? "客户管理员确认进入受控更新计划。"
      })
    },
    token
  );
}

export async function listLocalBackups(
  tenantId: string | number,
  token: string
): Promise<LocalBackupRecord[]> {
  return requestJson<LocalBackupRecord[]>(`/api/tenants/${tenantId}/local-backups`, {}, token);
}

export async function createLocalBackup(
  tenantId: string | number,
  token: string,
  reason = "客户管理员手动创建本地数据库备份点。"
): Promise<LocalBackupRecord> {
  return requestJson<LocalBackupRecord>(
    `/api/tenants/${tenantId}/local-backups`,
    {
      method: "POST",
      body: JSON.stringify({ reason })
    },
    token
  );
}

export async function verifyLocalBackup(
  backupId: string | number,
  token: string,
  reason = "客户管理员执行本地备份完整性校验。"
): Promise<LocalBackupRecord> {
  return requestJson<LocalBackupRecord>(
    `/api/local-backups/${backupId}/verify`,
    {
      method: "POST",
      body: JSON.stringify({ reason })
    },
    token
  );
}

export async function createLocalBackupRestoreDryRun(
  backupId: string | number,
  token: string,
  reason = "客户管理员执行本地恢复工具演练。"
): Promise<LocalBackupRestoreDryRun> {
  return requestJson<LocalBackupRestoreDryRun>(
    `/api/local-backups/${backupId}/restore-dry-run`,
    {
      method: "POST",
      body: JSON.stringify({ reason })
    },
    token
  );
}

export async function getLocalMaintenanceReadiness(
  tenantId: string | number,
  token: string
): Promise<LocalMaintenanceReadiness> {
  return requestJson<LocalMaintenanceReadiness>(
    `/api/tenants/${tenantId}/local-maintenance/readiness`,
    {},
    token
  );
}

export async function preflightSignedUpdatePackage(
  tenantId: string | number,
  token: string,
  packagePayload: unknown
): Promise<SignedUpdatePreflightResult> {
  return requestJson<SignedUpdatePreflightResult>(
    `/api/tenants/${tenantId}/signed-update-package/preflights`,
    {
      method: "POST",
      body: JSON.stringify({ package: packagePayload })
    },
    token
  );
}

export async function stageSignedUpdatePackage(
  tenantId: string | number,
  token: string,
  packagePayload: unknown
): Promise<SignedUpdateStagedPackage> {
  return requestJson<SignedUpdateStagedPackage>(
    `/api/tenants/${tenantId}/signed-update-package/staged`,
    {
      method: "POST",
      body: JSON.stringify({ package: packagePayload })
    },
    token
  );
}

export async function listStagedSignedUpdatePackages(
  tenantId: string | number,
  token: string
): Promise<SignedUpdateStagedPackage[]> {
  return requestJson<SignedUpdateStagedPackage[]>(
    `/api/tenants/${tenantId}/signed-update-package/staged`,
    {},
    token
  );
}

export async function applyStagedSignedUpdatePackage(
  packageId: string | number,
  token: string,
  reason = "客户管理员确认备份并应用本次签名更新包。"
): Promise<SignedUpdateStagedPackage> {
  return requestJson<SignedUpdateStagedPackage>(
    `/api/signed-update-packages/${packageId}/apply`,
    {
      method: "POST",
      body: JSON.stringify({ reason })
    },
    token
  );
}

export async function createProgramUpdateDryRun(
  packageId: string | number,
  token: string,
  reason = "客户管理员确认只生成程序更新演练计划。"
): Promise<SignedUpdateStagedPackage> {
  return requestJson<SignedUpdateStagedPackage>(
    `/api/signed-update-packages/${packageId}/program-dry-run`,
    {
      method: "POST",
      body: JSON.stringify({ reason })
    },
    token
  );
}

export async function rollbackStagedSignedUpdatePackage(
  packageId: string | number,
  token: string,
  reason = "客户管理员确认回滚本次签名更新包。"
): Promise<SignedUpdateStagedPackage> {
  return requestJson<SignedUpdateStagedPackage>(
    `/api/signed-update-packages/${packageId}/rollback`,
    {
      method: "POST",
      body: JSON.stringify({ reason })
    },
    token
  );
}

export async function createTenantUser(
  tenantId: string | number,
  token: string,
  payload: { name: string; email: string; password: string; status?: "active" | "inactive" }
): Promise<AccountUser> {
  return requestJson<AccountUser>(
    `/api/tenants/${tenantId}/users`,
    {
      method: "POST",
      body: JSON.stringify({
        name: payload.name,
        email: payload.email,
        password: payload.password,
        status: payload.status ?? "active"
      })
    },
    token
  );
}

export async function assignUserRole(
  userId: number,
  token: string,
  payload: { role_id: number }
): Promise<UserRoleAssignment> {
  return requestJson<UserRoleAssignment>(
    `/api/users/${userId}/roles`,
    {
      method: "POST",
      body: JSON.stringify(payload)
    },
    token
  );
}

export async function updateUserStatus(
  userId: number,
  token: string,
  status: "active" | "inactive"
): Promise<AccountUser> {
  return requestJson<AccountUser>(
    `/api/users/${userId}/status`,
    {
      method: "PATCH",
      body: JSON.stringify({ status })
    },
    token
  );
}

export async function resetUserPassword(
  userId: number,
  token: string,
  newPassword: string
): Promise<AccountUser> {
  return requestJson<AccountUser>(
    `/api/users/${userId}/password-reset`,
    {
      method: "POST",
      body: JSON.stringify({ new_password: newPassword })
    },
    token
  );
}

export async function listChannelAccounts(tenantId: string | number, token: string): Promise<ChannelAccount[]> {
  return requestJson<ChannelAccount[]>(`/api/tenants/${tenantId}/channel-accounts`, {}, token);
}

export async function configureChannelAccount(
  channelId: number,
  token: string,
  payload: ChannelAccountPayload
): Promise<ChannelAccount> {
  return requestJson<ChannelAccount>(
    `/api/channels/${channelId}/channel-accounts`,
    {
      method: "POST",
      body: JSON.stringify(payload)
    },
    token
  );
}

export async function configureNoopChannelConnector(
  channelId: number,
  token: string
): Promise<ChannelConnectorConfig> {
  return requestJson<ChannelConnectorConfig>(
    `/api/channels/${channelId}/connector-config`,
    {
      method: "POST",
      body: JSON.stringify({
        provider: "wecom",
        mode: "noop",
        status: "ready",
        display_name: "企业微信客服官方接口占位",
        capabilities: ["send_text", "delivery_receipt"],
        public_config: {
          official_authorization: "pending",
          external_write: "disabled"
        },
        webhook_path: `/api/webhooks/wecom/channels/${channelId}`,
        signature_mode: "wecom_token_aeskey"
      })
    },
    token
  );
}

export async function ensureNoopChannelConnector(channelId: number, token: string): Promise<ChannelConnectorConfig> {
  return configureNoopChannelConnector(channelId, token);
}

export async function createConnectorSendPlan(draftId: number, token: string): Promise<OutboxSendAttempt> {
  return requestJson<OutboxSendAttempt>(
    `/api/outbox-drafts/${draftId}/connector-send-plans`,
    {
      method: "POST",
      body: JSON.stringify({
        operator_note: "前端工作台生成官方渠道连接器发送计划"
      })
    },
    token
  );
}

export async function createOutboxDeliveryJob(draftId: number, token: string): Promise<OutboxDeliveryJob> {
  return requestJson<OutboxDeliveryJob>(
    `/api/outbox-drafts/${draftId}/delivery-jobs`,
    {
      method: "POST",
      body: JSON.stringify({
        external_write_requested: false,
        priority: 100
      })
    },
    token
  );
}

export async function listOutboxDeliveryJobs(
  tenantId: string | number,
  token: string
): Promise<OutboxDeliveryJob[]> {
  return requestJson<OutboxDeliveryJob[]>(`/api/tenants/${tenantId}/outbox-delivery-jobs`, {}, token);
}

export async function runOutboxDeliveryQueue(
  tenantId: string | number,
  token: string
): Promise<OutboxDeliveryQueueRun> {
  return requestJson<OutboxDeliveryQueueRun>(
    `/api/tenants/${tenantId}/outbox-delivery-queue-runs`,
    {
      method: "POST",
      body: JSON.stringify({
        batch_size: 20,
        rate_limit_per_minute: 60,
        max_attempts: 3,
        worker_id: "frontend_delivery_queue_worker"
      })
    },
    token
  );
}

export async function runOutboxWorker(tenantId: string | number, token: string): Promise<OutboxWorkerRun> {
  return requestJson<OutboxWorkerRun>(
    `/api/tenants/${tenantId}/outbox-worker-runs`,
    {
      method: "POST",
      body: JSON.stringify({
        batch_size: 20,
        rate_limit_per_minute: 60,
        max_attempts: 3
      })
    },
    token
  );
}

export async function listDeliveryFailureReviews(
  tenantId: string | number,
  token: string,
  status = "open"
): Promise<DeliveryFailureReview[]> {
  return requestJson<DeliveryFailureReview[]>(
    `/api/tenants/${tenantId}/delivery-failure-reviews?status=${encodeURIComponent(status)}`,
    {},
    token
  );
}

export async function resolveDeliveryFailureReview(
  reviewId: number,
  token: string,
  payload: { status: "resolved" | "ignored"; resolution_note?: string }
): Promise<DeliveryFailureReview> {
  return requestJson<DeliveryFailureReview>(
    `/api/delivery-failure-reviews/${reviewId}`,
    {
      method: "PATCH",
      body: JSON.stringify({
        status: payload.status,
        resolution_note: payload.resolution_note ?? ""
      })
    },
    token
  );
}

export async function runTrustedInboundWorker(
  tenantId: string | number,
  token: string
): Promise<TrustedInboundWorkerRun> {
  return requestJson<TrustedInboundWorkerRun>(
    `/api/tenants/${tenantId}/trusted-inbound-worker-runs`,
    {
      method: "POST",
      body: JSON.stringify({
        batch_size: 20,
        rate_limit_per_minute: 60,
        mode: "model_assisted",
        risk_level: "medium",
        knowledge_top_k: 3,
        model_provider: "deterministic"
      })
    },
    token
  );
}

export async function getWorkerHealthDashboard(
  tenantId: string | number,
  token: string,
  params: { stale_after_seconds?: number; recent_run_limit?: number } = {}
): Promise<WorkerHealthDashboard> {
  const search = new URLSearchParams({
    stale_after_seconds: String(params.stale_after_seconds ?? 120),
    recent_run_limit: String(params.recent_run_limit ?? 10)
  });
  return requestJson<WorkerHealthDashboard>(
    `/api/tenants/${tenantId}/ops/worker-health?${search.toString()}`,
    {},
    token
  );
}

export async function getBusinessOpsDashboard(
  tenantId: string | number,
  token: string,
  params: { range?: "today" | "7d" | "30d"; channel_id?: number | null } = {}
): Promise<BusinessOpsDashboard> {
  const search = new URLSearchParams({
    range: params.range ?? "today"
  });
  if (params.channel_id !== undefined && params.channel_id !== null) {
    search.set("channel_id", String(params.channel_id));
  }
  return requestJson<BusinessOpsDashboard>(
    `/api/tenants/${tenantId}/ops/dashboard?${search.toString()}`,
    {},
    token
  );
}

export async function getOpsAlertRulesDashboard(
  tenantId: string | number,
  token: string,
  params: { stale_after_seconds?: number; recent_run_limit?: number } = {}
): Promise<OpsAlertRulesDashboard> {
  const search = new URLSearchParams({
    stale_after_seconds: String(params.stale_after_seconds ?? 120),
    recent_run_limit: String(params.recent_run_limit ?? 10)
  });
  return requestJson<OpsAlertRulesDashboard>(
    `/api/tenants/${tenantId}/ops/alert-rules?${search.toString()}`,
    {},
    token
  );
}

export async function getOpsMetricsDashboard(
  tenantId: string | number,
  token: string,
  params: { stale_after_seconds?: number; recent_run_limit?: number } = {}
): Promise<OpsMetricsDashboard> {
  const search = new URLSearchParams({
    stale_after_seconds: String(params.stale_after_seconds ?? 120),
    recent_run_limit: String(params.recent_run_limit ?? 10)
  });
  return requestJson<OpsMetricsDashboard>(
    `/api/tenants/${tenantId}/ops/metrics?${search.toString()}`,
    {},
    token
  );
}

export async function listConversationInbox(
  tenantId: string | number,
  token: string,
  params: {
    status?: string;
    query?: string;
    page?: number;
    page_size?: number;
    assigned?: string;
    sla?: string;
    sort?: string;
    priority?: string;
    channel_id?: number | null;
  } = {}
): Promise<ConversationInboxList> {
  const search = new URLSearchParams({
    status: params.status ?? "all",
    query: params.query ?? "",
    page: String(params.page ?? 1),
    page_size: String(params.page_size ?? 20),
    assigned: params.assigned ?? "all",
    sla: params.sla ?? "all",
    sort: params.sort ?? "last_message_desc",
    priority: params.priority ?? "all"
  });
  if (params.channel_id != null) {
    search.set("channel_id", String(params.channel_id));
  }
  return requestJson<ConversationInboxList>(`/api/tenants/${tenantId}/conversation-inbox?${search.toString()}`, {}, token);
}

export async function updateConversationAssignment(
  conversationId: number,
  token: string,
  payload: { assigned_user_id?: number | null; assigned_team_id?: number | null; status?: string }
): Promise<ConversationAssignmentResponse> {
  return requestJson<ConversationAssignmentResponse>(
    `/api/conversations/${conversationId}/assignment`,
    {
      method: "PATCH",
      body: JSON.stringify(payload)
    },
    token
  );
}

export async function applyConversationWorkflowAction(
  conversationId: number,
  token: string,
  payload: {
    action: ConversationWorkflowActionName;
    target_user_id?: number | null;
    target_team_id?: number | null;
    note?: string;
  }
): Promise<ConversationAssignmentResponse> {
  return requestJson<ConversationAssignmentResponse>(
    `/api/conversations/${conversationId}/workflow-actions`,
    {
      method: "POST",
      body: JSON.stringify(payload)
    },
    token
  );
}

export async function listSupportTickets(
  tenantId: string | number,
  token: string,
  params: {
    status?: string;
    priority?: string;
    assigned?: string;
    sla?: string;
    query?: string;
    page?: number;
    page_size?: number;
  } = {}
): Promise<SupportTicketList> {
  const search = new URLSearchParams({
    page: String(params.page ?? 1),
    page_size: String(params.page_size ?? 20),
    assigned: params.assigned ?? "all",
    sla: params.sla ?? "all"
  });
  if (params.status && params.status !== "all") {
    search.set("status", params.status);
  }
  if (params.priority && params.priority !== "all") {
    search.set("priority", params.priority);
  }
  if (params.query?.trim()) {
    search.set("query", params.query.trim());
  }
  return requestJson<SupportTicketList>(`/api/tenants/${tenantId}/support-tickets?${search.toString()}`, {}, token);
}

export async function createSupportTicketFromConversation(
  conversationId: number,
  token: string,
  payload: {
    subject?: string;
    description?: string;
    priority?: "low" | "normal" | "high" | "urgent";
    assigned_user_id?: number | null;
    assigned_team_id?: number | null;
    sla_target_minutes?: number | null;
  } = {}
): Promise<SupportTicket> {
  return requestJson<SupportTicket>(
    `/api/conversations/${conversationId}/support-tickets`,
    {
      method: "POST",
      body: JSON.stringify(payload)
    },
    token
  );
}

export async function updateSupportTicket(
  ticketId: number,
  token: string,
  payload: {
    subject?: string;
    description?: string;
    status?: "open" | "in_progress" | "pending_customer" | "resolved" | "closed" | "canceled";
    priority?: "low" | "normal" | "high" | "urgent";
    assigned_user_id?: number | null;
    assigned_team_id?: number | null;
    sla_target_minutes?: number | null;
    resolution_note?: string;
  }
): Promise<SupportTicket> {
  return requestJson<SupportTicket>(
    `/api/support-tickets/${ticketId}`,
    {
      method: "PATCH",
      body: JSON.stringify(payload)
    },
    token
  );
}

export async function listContactProfiles(
  tenantId: string | number,
  token: string,
  params: {
    query?: string;
    page?: number;
    page_size?: number;
  } = {}
): Promise<ContactProfileList> {
  const search = new URLSearchParams({
    query: params.query ?? "",
    page: String(params.page ?? 1),
    page_size: String(params.page_size ?? 20)
  });
  return requestJson<ContactProfileList>(`/api/tenants/${tenantId}/contact-profiles?${search.toString()}`, {}, token);
}

export async function getContactProfile(contactId: number, token: string): Promise<ContactProfileDetail> {
  return requestJson<ContactProfileDetail>(`/api/contact-profiles/${contactId}`, {}, token);
}

export async function listSalesLeads(
  tenantId: string | number,
  token: string,
  params: {
    stage?: string;
    intent?: string;
    owner?: string;
    query?: string;
    page?: number;
    page_size?: number;
  } = {}
): Promise<SalesLeadList> {
  const search = new URLSearchParams({
    stage: params.stage ?? "all",
    intent: params.intent ?? "all",
    owner: params.owner ?? "all",
    query: params.query ?? "",
    page: String(params.page ?? 1),
    page_size: String(params.page_size ?? 20)
  });
  return requestJson<SalesLeadList>(`/api/tenants/${tenantId}/leads?${search.toString()}`, {}, token);
}

export async function createSalesLeadFromConversation(
  conversationId: number,
  token: string,
  payload: {
    title?: string;
    summary?: string;
    stage?: "new" | "contacted" | "proposal" | "won" | "invalid" | "lost";
    intent_level?: "cold" | "warm" | "hot";
    expected_budget?: string;
    next_step?: string;
    owner_user_id?: number | null;
    next_follow_up_at?: string | null;
  } = {}
): Promise<SalesLead> {
  return requestJson<SalesLead>(
    `/api/conversations/${conversationId}/leads`,
    {
      method: "POST",
      body: JSON.stringify(payload)
    },
    token
  );
}

export async function updateSalesLead(
  leadId: number,
  token: string,
  payload: {
    title?: string;
    summary?: string;
    stage?: "new" | "contacted" | "proposal" | "won" | "invalid" | "lost";
    intent_level?: "cold" | "warm" | "hot";
    expected_budget?: string;
    next_step?: string;
    owner_user_id?: number | null;
    next_follow_up_at?: string | null;
  }
): Promise<SalesLead> {
  return requestJson<SalesLead>(
    `/api/leads/${leadId}`,
    {
      method: "PATCH",
      body: JSON.stringify(payload)
    },
    token
  );
}

export async function listKnowledgeDocuments(
  tenantId: string | number,
  token: string,
  status = "active"
): Promise<KnowledgeDocumentList> {
  return requestJson<KnowledgeDocumentList>(
    `/api/tenants/${tenantId}/knowledge-documents?status=${encodeURIComponent(status)}`,
    {},
    token
  );
}

export async function getKnowledgeMemoryMeshOverview(
  tenantId: string | number,
  token: string
): Promise<KnowledgeMemoryMeshOverview> {
  return requestJson<KnowledgeMemoryMeshOverview>(
    `/api/tenants/${tenantId}/knowledge-memory-mesh-overview`,
    {},
    token
  );
}

export async function createKnowledgeDocument(
  tenantId: string | number,
  token: string,
  payload: {
    title: string;
    source_type?: string;
    source_uri?: string;
    raw_text: string;
    tags?: string[];
    status?: "draft" | "active" | "archived";
    chunk_size?: number;
    chunk_overlap?: number;
  }
): Promise<KnowledgeDocument> {
  return requestJson<KnowledgeDocument>(
    `/api/tenants/${tenantId}/knowledge-documents`,
    {
      method: "POST",
      body: JSON.stringify({
        source_type: "manual_document",
        source_uri: "",
        tags: [],
        status: "active",
        chunk_size: 900,
        chunk_overlap: 120,
        ...payload
      })
    },
    token
  );
}

export async function listKnowledgeDocumentChunks(documentId: number, token: string): Promise<KnowledgeChunk[]> {
  return requestJson<KnowledgeChunk[]>(`/api/knowledge-documents/${documentId}/chunks`, {}, token);
}

export async function checkKnowledgeDocumentPublishGate(
  documentId: number,
  token: string,
  payload: {
    evaluation_set_id?: number | null;
    evaluation_case_ids?: number[];
    top_k?: number;
    min_score?: number;
    search_status?: "draft" | "active" | "archived" | null;
    low_confidence_threshold?: number;
    min_hit_rate?: number;
    min_citation_coverage?: number;
    min_expected_term_coverage?: number;
    require_regression_case?: boolean;
    ignore_safe_handoff_failures?: boolean;
  } = {}
): Promise<KnowledgeDocumentPublishGateResult> {
  return requestJson<KnowledgeDocumentPublishGateResult>(
    `/api/knowledge-documents/${documentId}/publish-checks`,
    {
      method: "POST",
      body: JSON.stringify(payload)
    },
    token
  );
}

export async function publishKnowledgeDocument(
  documentId: number,
  token: string,
  payload: {
    evaluation_set_id?: number | null;
    evaluation_case_ids?: number[];
    top_k?: number;
    min_score?: number;
    search_status?: "draft" | "active" | "archived" | null;
    low_confidence_threshold?: number;
    min_hit_rate?: number;
    min_citation_coverage?: number;
    min_expected_term_coverage?: number;
    require_regression_case?: boolean;
    ignore_safe_handoff_failures?: boolean;
  } = {}
): Promise<KnowledgeDocumentPublishGateResult> {
  return requestJson<KnowledgeDocumentPublishGateResult>(
    `/api/knowledge-documents/${documentId}/publication`,
    {
      method: "POST",
      body: JSON.stringify(payload)
    },
    token
  );
}

export async function listKnowledgeDocumentPublications(
  documentId: number,
  token: string
): Promise<KnowledgeDocumentPublicationList> {
  return requestJson<KnowledgeDocumentPublicationList>(
    `/api/knowledge-documents/${documentId}/publications?page=1&page_size=8`,
    {},
    token
  );
}

export async function rollbackKnowledgeDocumentPublication(
  documentId: number,
  token: string,
  payload: { target_publication_id?: number | null; rollback_reason?: string } = {}
): Promise<KnowledgeDocumentPublication> {
  return requestJson<KnowledgeDocumentPublication>(
    `/api/knowledge-documents/${documentId}/rollback`,
    {
      method: "POST",
      body: JSON.stringify(payload)
    },
    token
  );
}

export async function searchKnowledgeDocuments(
  tenantId: string | number,
  token: string,
  payload: { query: string; top_k?: number; status?: "draft" | "active" | "archived"; min_score?: number }
): Promise<KnowledgeDocumentSearchResponse> {
  return requestJson<KnowledgeDocumentSearchResponse>(
    `/api/tenants/${tenantId}/knowledge-document-searches`,
    {
      method: "POST",
      body: JSON.stringify({
        top_k: 5,
        status: "active",
        min_score: 0,
        ...payload
      })
    },
    token
  );
}

export async function listBusinessObjects(
  tenantId: string | number,
  token: string,
  params: { type?: BusinessObjectType | "all"; status?: KnowledgeStatus | "all" } = {}
): Promise<BusinessObjectList> {
  const searchParams = new URLSearchParams();
  if (params.type && params.type !== "all") {
    searchParams.set("type", params.type);
  }
  if (params.status && params.status !== "all") {
    searchParams.set("status", params.status);
  }
  const query = searchParams.toString();
  return requestJson<BusinessObjectList>(
    `/api/tenants/${tenantId}/business-objects${query ? `?${query}` : ""}`,
    {},
    token
  );
}

export async function createBusinessObject(
  tenantId: string | number,
  token: string,
  payload: {
    type: BusinessObjectType;
    title: string;
    external_id?: string;
    summary?: string;
    attrs_json?: Record<string, unknown>;
    aliases?: string[];
    status?: KnowledgeStatus;
  }
): Promise<BusinessObject> {
  return requestJson<BusinessObject>(
    `/api/tenants/${tenantId}/business-objects`,
    {
      method: "POST",
      body: JSON.stringify({
        external_id: "",
        summary: "",
        attrs_json: {},
        aliases: [],
        status: "active",
        ...payload
      })
    },
    token
  );
}

export async function updateBusinessObject(
  businessObjectId: number,
  token: string,
  payload: {
    type?: BusinessObjectType;
    title?: string;
    external_id?: string;
    summary?: string;
    attrs_json?: Record<string, unknown>;
    aliases?: string[];
    status?: KnowledgeStatus;
  }
): Promise<BusinessObject> {
  return requestJson<BusinessObject>(
    `/api/business-objects/${businessObjectId}`,
    {
      method: "PATCH",
      body: JSON.stringify(payload)
    },
    token
  );
}

export async function listObjectKnowledgeCards(
  businessObjectId: number,
  token: string,
  params: { status?: KnowledgeStatus | "all" } = {}
): Promise<ObjectKnowledgeCardList> {
  const searchParams = new URLSearchParams();
  if (params.status && params.status !== "all") {
    searchParams.set("status", params.status);
  }
  const query = searchParams.toString();
  return requestJson<ObjectKnowledgeCardList>(
    `/api/business-objects/${businessObjectId}/knowledge-cards${query ? `?${query}` : ""}`,
    {},
    token
  );
}

export async function createObjectKnowledgeCard(
  businessObjectId: number,
  token: string,
  payload: {
    question: string;
    answer: string;
    trigger_keywords?: string[];
    media_refs?: string[];
    scope?: Record<string, unknown>;
    source?: string;
    version?: number;
    status?: KnowledgeStatus;
  }
): Promise<ObjectKnowledgeCard> {
  return requestJson<ObjectKnowledgeCard>(
    `/api/business-objects/${businessObjectId}/knowledge-cards`,
    {
      method: "POST",
      body: JSON.stringify({
        trigger_keywords: [],
        media_refs: [],
        scope: {},
        source: "manual",
        version: 1,
        status: "active",
        ...payload
      })
    },
    token
  );
}

export async function previewKnowledgeUpdatePackage(
  tenantId: string | number,
  token: string,
  packagePayload: unknown
): Promise<KnowledgeUpdatePackageResult> {
  return requestJson<KnowledgeUpdatePackageResult>(
    `/api/tenants/${tenantId}/knowledge-update-package/previews`,
    {
      method: "POST",
      body: JSON.stringify({ package: packagePayload })
    },
    token
  );
}

export async function importKnowledgeUpdatePackage(
  tenantId: string | number,
  token: string,
  packagePayload: unknown
): Promise<KnowledgeUpdatePackageResult> {
  return requestJson<KnowledgeUpdatePackageResult>(
    `/api/tenants/${tenantId}/knowledge-update-package-imports`,
    {
      method: "POST",
      body: JSON.stringify({ package: packagePayload })
    },
    token
  );
}

export async function getTenantReplyStrategy(
  tenantId: string | number,
  token: string
): Promise<TenantReplyStrategy> {
  return requestJson<TenantReplyStrategy>(`/api/tenants/${tenantId}/reply-strategy`, {}, token);
}

export async function getRagCostGovernanceSummary(
  tenantId: string | number,
  token: string
): Promise<RagCostGovernanceSummary> {
  return requestJson<RagCostGovernanceSummary>(
    `/api/tenants/${tenantId}/rag-cost-governance-summary`,
    {},
    token
  );
}

export async function getLlmOpsReadinessSummary(
  tenantId: string | number,
  token: string
): Promise<LlmOpsReadinessSummary> {
  return requestJson<LlmOpsReadinessSummary>(`/api/tenants/${tenantId}/llm-ops-readiness`, {}, token);
}

export async function updateTenantReplyStrategy(
  tenantId: string | number,
  token: string,
  payload: {
    auto_reply_threshold?: number | null;
    manual_review_threshold?: number | null;
    blocked_policy_terms?: string[];
    manual_review_terms?: string[];
    force_draft_only?: boolean;
  }
): Promise<TenantReplyStrategy> {
  return requestJson<TenantReplyStrategy>(
    `/api/tenants/${tenantId}/reply-strategy`,
    {
      method: "PATCH",
      body: JSON.stringify({
        blocked_policy_terms: [],
        manual_review_terms: [],
        force_draft_only: false,
        ...payload
      })
    },
    token
  );
}

export async function createReplyDecision(
  messageId: number,
  token: string,
  payload: {
    auto_reply_threshold?: number;
    manual_review_threshold?: number;
    external_write_allowed?: boolean;
    force_draft_only?: boolean;
    idempotency_key?: string;
  } = {}
): Promise<ReplyDecision> {
  return requestJson<ReplyDecision>(
    `/api/messages/${messageId}/reply-decisions`,
    {
      method: "POST",
      body: JSON.stringify({
        auto_reply_threshold: 0.72,
        manual_review_threshold: 0.45,
        external_write_allowed: false,
        force_draft_only: true,
        ...payload
      })
    },
    token
  );
}

export async function listReplyDecisions(
  tenantId: string | number,
  token: string,
  params: { state?: ReplyDecisionState | "all"; conversation_id?: number; page?: number; page_size?: number } = {}
): Promise<ReplyDecisionList> {
  const searchParams = new URLSearchParams({
    page: String(params.page ?? 1),
    page_size: String(params.page_size ?? 50)
  });
  if (params.state && params.state !== "all") {
    searchParams.set("state", params.state);
  }
  if (params.conversation_id) {
    searchParams.set("conversation_id", String(params.conversation_id));
  }
  return requestJson<ReplyDecisionList>(
    `/api/tenants/${tenantId}/reply-decisions?${searchParams.toString()}`,
    {},
    token
  );
}

export async function rebuildKnowledgeVectorIndex(
  tenantId: string | number,
  token: string,
  payload: { status?: "draft" | "active" | "archived"; document_id?: number | null } = {}
): Promise<KnowledgeVectorIndexRebuild> {
  return requestJson<KnowledgeVectorIndexRebuild>(
    `/api/tenants/${tenantId}/knowledge-vector-index/rebuilds`,
    {
      method: "POST",
      body: JSON.stringify({
        status: "active",
        ...payload
      })
    },
    token
  );
}

export async function listKnowledgeEvaluationSets(
  tenantId: string | number,
  token: string,
  status = "active"
): Promise<KnowledgeEvaluationSetList> {
  return requestJson<KnowledgeEvaluationSetList>(
    `/api/tenants/${tenantId}/knowledge-evaluation-sets?status=${encodeURIComponent(status)}`,
    {},
    token
  );
}

export async function createKnowledgeEvaluationSet(
  tenantId: string | number,
  token: string,
  payload: {
    name: string;
    description?: string;
    status?: "draft" | "active" | "archived";
    evaluation_mode?: "document_retrieval" | "customer_service_retrieval";
    cases: Array<{
      external_case_id?: string;
      source_channel?: string;
      source_category?: string;
      question: string;
      question_type?: string;
      expected_terms?: string[];
      expected_source_uri?: string;
      expected_document_title?: string;
      expected_chunk_ids?: number[];
      must_have_all_evidence?: boolean;
      expected_human_review?: boolean;
      allow_auto_reply?: boolean;
      forbidden_terms?: string[];
      risk_level?: string;
      annotation_notes?: string;
      required_citation?: boolean;
      priority?: number;
      status?: "draft" | "active" | "archived";
    }>;
  }
): Promise<KnowledgeEvaluationSet> {
  return requestJson<KnowledgeEvaluationSet>(
    `/api/tenants/${tenantId}/knowledge-evaluation-sets`,
    {
      method: "POST",
      body: JSON.stringify({
        description: "",
        status: "active",
        evaluation_mode: "document_retrieval",
        ...payload
      })
    },
    token
  );
}

export async function precheckCustomerServiceQuestionBank(
  tenantId: string | number,
  token: string,
  payload: CustomerServiceQuestionBankImportPayload
): Promise<CustomerServiceQuestionBankPrecheck> {
  return requestJson<CustomerServiceQuestionBankPrecheck>(
    `/api/tenants/${tenantId}/customer-service-question-banks/precheck`,
    {
      method: "POST",
      body: JSON.stringify(payload)
    },
    token
  );
}

export async function importCustomerServiceQuestionBank(
  tenantId: string | number,
  token: string,
  payload: CustomerServiceQuestionBankImportPayload
): Promise<CustomerServiceQuestionBankPrecheck> {
  return requestJson<CustomerServiceQuestionBankPrecheck>(
    `/api/tenants/${tenantId}/customer-service-question-banks/import`,
    {
      method: "POST",
      body: JSON.stringify(payload)
    },
    token
  );
}

export async function runKnowledgeEvaluationSet(
  evaluationSetId: number,
  token: string,
  payload: {
    top_k?: number;
    min_score?: number;
    status?: "draft" | "active" | "archived";
    search_status?: "draft" | "active" | "archived";
    low_confidence_threshold?: number;
  } = {}
): Promise<KnowledgeEvaluationRun> {
  return requestJson<KnowledgeEvaluationRun>(
    `/api/knowledge-evaluation-sets/${evaluationSetId}/runs`,
    {
      method: "POST",
      body: JSON.stringify({
        top_k: 5,
        min_score: 0,
        status: "active",
        low_confidence_threshold: 0.45,
        ...payload
      })
    },
    token
  );
}

export async function listKnowledgeEvaluationRuns(
  evaluationSetId: number,
  token: string,
  page = 1,
  pageSize = 20
): Promise<KnowledgeEvaluationRunList> {
  return requestJson<KnowledgeEvaluationRunList>(
    `/api/knowledge-evaluation-sets/${evaluationSetId}/runs?page=${page}&page_size=${pageSize}`,
    {},
    token
  );
}

export async function getKnowledgeEvaluationRun(
  evaluationRunId: number,
  token: string
): Promise<KnowledgeEvaluationRun> {
  return requestJson<KnowledgeEvaluationRun>(
    `/api/knowledge-evaluation-runs/${evaluationRunId}`,
    {},
    token
  );
}

export async function exportKnowledgeEvaluationRunReport(
  evaluationRunId: number,
  token: string,
  reportFormat: "markdown" | "csv" = "markdown"
): Promise<KnowledgeEvaluationRunReport> {
  return requestJson<KnowledgeEvaluationRunReport>(
    `/api/knowledge-evaluation-runs/${evaluationRunId}/report?format=${reportFormat}`,
    {},
    token
  );
}

export async function labelKnowledgeEvaluationRunCaseFactuality(
  evaluationRunCaseId: number,
  token: string,
  payload: {
    final_answer_factuality_status: FactualityLabelStatus;
    citation_sufficient?: boolean;
    forbidden_commitment_passed?: boolean;
    handoff_correct?: boolean;
    reviewer_notes?: string;
  }
): Promise<KnowledgeEvaluationRunCaseFactualityLabelResult> {
  return requestJson<KnowledgeEvaluationRunCaseFactualityLabelResult>(
    `/api/knowledge-evaluation-run-cases/${evaluationRunCaseId}/factuality-label`,
    {
      method: "PATCH",
      body: JSON.stringify({
        reviewer_notes: "",
        ...payload
      })
    },
    token
  );
}

export async function captureKnowledgeEvaluationRunCaseFinalAnswerSample(
  evaluationRunCaseId: number,
  token: string,
  payload: {
    final_answer_text: string;
    final_answer_source?: "manual_capture" | "system_capture" | "dry_run_fixture" | "imported_sample";
    citation_uris?: string[];
    answer_author?: string;
    reviewer_notes?: string;
  }
): Promise<KnowledgeEvaluationRunCaseFinalAnswerSampleResult> {
  return requestJson<KnowledgeEvaluationRunCaseFinalAnswerSampleResult>(
    `/api/knowledge-evaluation-run-cases/${evaluationRunCaseId}/final-answer-sample`,
    {
      method: "PATCH",
      body: JSON.stringify({
        final_answer_source: "manual_capture",
        citation_uris: [],
        answer_author: "本地客服工作台",
        reviewer_notes: "",
        ...payload
      })
    },
    token
  );
}

export async function batchLabelKnowledgeEvaluationRunCaseFactuality(
  evaluationRunId: number,
  token: string,
  payload: {
    labels: Array<{
      evaluation_run_case_id: number;
      final_answer_factuality_status: FactualityLabelStatus;
      citation_sufficient?: boolean;
      forbidden_commitment_passed?: boolean;
      handoff_correct?: boolean;
      reviewer_notes?: string;
    }>;
  }
): Promise<KnowledgeEvaluationRunCaseFactualityBatchLabelResult> {
  return requestJson<KnowledgeEvaluationRunCaseFactualityBatchLabelResult>(
    `/api/knowledge-evaluation-runs/${evaluationRunId}/factuality-labels/batch`,
    {
      method: "PATCH",
      body: JSON.stringify(payload)
    },
    token
  );
}

export async function exportKnowledgeEvaluationRunFinalAnswerLabels(
  evaluationRunId: number,
  token: string,
  options: { includeAnswerText?: boolean } = {}
): Promise<KnowledgeEvaluationRunFinalAnswerLabelExport> {
  const search = new URLSearchParams({ format: "csv" });
  if (options.includeAnswerText === false) search.set("include_answer_text", "false");
  return requestJson<KnowledgeEvaluationRunFinalAnswerLabelExport>(
    `/api/knowledge-evaluation-runs/${evaluationRunId}/final-answer-labels/export?${search.toString()}`,
    {},
    token
  );
}

export async function importKnowledgeEvaluationRunFinalAnswerLabels(
  evaluationRunId: number,
  token: string,
  payload: {
    content: string;
    dry_run?: boolean;
  }
): Promise<KnowledgeEvaluationRunFinalAnswerLabelImportResult> {
  return requestJson<KnowledgeEvaluationRunFinalAnswerLabelImportResult>(
    `/api/knowledge-evaluation-runs/${evaluationRunId}/final-answer-labels/imports`,
    {
      method: "POST",
      body: JSON.stringify({
        import_format: "csv",
        dry_run: true,
        ...payload
      })
    },
    token
  );
}

export async function getMonthlyQualityReview(
  tenantId: string | number,
  token: string,
  options: { year?: number; month?: number } = {}
): Promise<MonthlyQualityReview> {
  const search = new URLSearchParams();
  if (options.year) search.set("year", String(options.year));
  if (options.month) search.set("month", String(options.month));
  const query = search.toString();
  return requestJson<MonthlyQualityReview>(
    `/api/tenants/${tenantId}/monthly-quality-review${query ? `?${query}` : ""}`,
    {},
    token
  );
}

export async function getMonthlyOpsReport(
  tenantId: string | number,
  token: string,
  options: { year?: number; month?: number } = {}
): Promise<MonthlyOpsReport> {
  const search = new URLSearchParams();
  if (options.year) search.set("year", String(options.year));
  if (options.month) search.set("month", String(options.month));
  const query = search.toString();
  return requestJson<MonthlyOpsReport>(
    `/api/tenants/${tenantId}/monthly-ops-report${query ? `?${query}` : ""}`,
    {},
    token
  );
}

export async function getPilotReadiness(
  tenantId: string | number,
  token: string
): Promise<PilotReadiness> {
  return requestJson<PilotReadiness>(`/api/tenants/${tenantId}/pilot-readiness`, {}, token);
}

export async function importKnowledgeConfirmationCsv(
  tenantId: string | number,
  token: string,
  payload: { filename: string; csv_text: string }
): Promise<KnowledgeConfirmationImportResult> {
  return requestJson<KnowledgeConfirmationImportResult>(
    `/api/tenants/${tenantId}/knowledge-confirmations/imports`,
    {
      method: "POST",
      body: JSON.stringify(payload)
    },
    token
  );
}

export async function precheckCustomerMaterialPackage(
  tenantId: string | number,
  token: string,
  payload: { materials_csv: string; trial_questions_csv: string; manifest_json: string }
): Promise<CustomerMaterialPrecheckResult> {
  return requestJson<CustomerMaterialPrecheckResult>(
    `/api/tenants/${tenantId}/customer-materials/precheck`,
    {
      method: "POST",
      body: JSON.stringify(payload)
    },
    token
  );
}

export async function getCustomerMaterialBatches(
  tenantId: string | number,
  token: string
): Promise<CustomerMaterialBatchList> {
  return requestJson<CustomerMaterialBatchList>(
    `/api/tenants/${tenantId}/customer-materials/batches`,
    {},
    token
  );
}

export async function createSafeTestConversation(
  tenantId: string | number,
  token: string
): Promise<SafeTestConversationResult> {
  return requestJson<SafeTestConversationResult>(
    `/api/tenants/${tenantId}/pilot-safe-test-conversation`,
    {
      method: "POST"
    },
    token
  );
}

export async function getCustomerMaterialTemplatePackage(
  tenantId: string | number,
  token: string
): Promise<CustomerMaterialTemplatePackage> {
  return requestJson<CustomerMaterialTemplatePackage>(
    `/api/tenants/${tenantId}/customer-materials/template-package`,
    {},
    token
  );
}

export async function getCustomerMaterialHandoffBundle(
  tenantId: string | number,
  token: string
): Promise<CustomerMaterialHandoffBundle> {
  return requestJson<CustomerMaterialHandoffBundle>(
    `/api/tenants/${tenantId}/customer-materials/handoff-bundle`,
    {},
    token
  );
}

export async function getCustomerQualityReport(
  tenantId: string | number,
  token: string,
  options: { year?: number; month?: number } = {}
): Promise<CustomerQualityReport> {
  const search = new URLSearchParams();
  if (options.year) search.set("year", String(options.year));
  if (options.month) search.set("month", String(options.month));
  const query = search.toString();
  return requestJson<CustomerQualityReport>(
    `/api/tenants/${tenantId}/customer-quality-report${query ? `?${query}` : ""}`,
    {},
    token
  );
}

export async function getOnlineReceiptQualitySummary(
  tenantId: string | number,
  token: string
): Promise<OnlineReceiptQualitySummary> {
  return requestJson<OnlineReceiptQualitySummary>(
    `/api/tenants/${tenantId}/online-receipt-quality-summary`,
    {},
    token
  );
}

export async function exportCustomerQualityReport(
  tenantId: string | number,
  token: string,
  options: { year?: number; month?: number; format?: "html" | "xlsx" | "docx" } = {}
): Promise<CustomerQualityReportExport> {
  const search = new URLSearchParams();
  if (options.year) search.set("year", String(options.year));
  if (options.month) search.set("month", String(options.month));
  search.set("format", options.format ?? "html");
  return requestJson<CustomerQualityReportExport>(
    `/api/tenants/${tenantId}/customer-quality-report/export?${search.toString()}`,
    {},
    token
  );
}

export async function listCustomerQualityReportArchives(
  tenantId: string | number,
  token: string,
  options: { page?: number; pageSize?: number; period?: string } = {}
): Promise<CustomerQualityReportArchiveList> {
  const search = new URLSearchParams();
  if (options.page) search.set("page", String(options.page));
  if (options.pageSize) search.set("page_size", String(options.pageSize));
  if (options.period) search.set("period", options.period);
  const query = search.toString();
  return requestJson<CustomerQualityReportArchiveList>(
    `/api/tenants/${tenantId}/customer-quality-report/archives${query ? `?${query}` : ""}`,
    {},
    token
  );
}

export async function downloadCustomerQualityReportArchive(
  tenantId: string | number,
  token: string,
  archiveEventId: number
): Promise<CustomerQualityReportExport> {
  return requestJson<CustomerQualityReportExport>(
    `/api/tenants/${tenantId}/customer-quality-report/archives/${archiveEventId}/download`,
    {},
    token
  );
}

export async function recordCustomerQualityReportSignoff(
  tenantId: string | number,
  token: string,
  payload: CustomerQualityReportSignoffCreate,
  options: { year?: number; month?: number } = {}
): Promise<CustomerQualityReportSignoff> {
  const search = new URLSearchParams();
  if (options.year) search.set("year", String(options.year));
  if (options.month) search.set("month", String(options.month));
  const query = search.toString();
  return requestJson<CustomerQualityReportSignoff>(
    `/api/tenants/${tenantId}/customer-quality-report/signoffs${query ? `?${query}` : ""}`,
    {
      method: "POST",
      body: JSON.stringify(payload)
    },
    token
  );
}

export async function listCustomerQualityReportSignoffs(
  tenantId: string | number,
  token: string,
  options: { page?: number; pageSize?: number; period?: string } = {}
): Promise<CustomerQualityReportSignoffList> {
  const search = new URLSearchParams();
  if (options.page) search.set("page", String(options.page));
  if (options.pageSize) search.set("page_size", String(options.pageSize));
  if (options.period) search.set("period", options.period);
  const query = search.toString();
  return requestJson<CustomerQualityReportSignoffList>(
    `/api/tenants/${tenantId}/customer-quality-report/signoffs${query ? `?${query}` : ""}`,
    {},
    token
  );
}

export async function listKnowledgeGaps(
  tenantId: string | number,
  token: string,
  params: {
    status?: string;
    severity?: string;
    source_type?: string;
    query?: string;
    page?: number;
    page_size?: number;
  } = {}
): Promise<KnowledgeGapList> {
  const search = new URLSearchParams({
    page: String(params.page ?? 1),
    page_size: String(params.page_size ?? 50)
  });
  if (params.status && params.status !== "all") {
    search.set("status", params.status);
  }
  if (params.severity && params.severity !== "all") {
    search.set("severity", params.severity);
  }
  if (params.source_type && params.source_type !== "all") {
    search.set("source_type", params.source_type);
  }
  const query = params.query?.trim();
  if (query) {
    search.set("query", query);
  }
  return requestJson<KnowledgeGapList>(`/api/tenants/${tenantId}/knowledge-gaps?${search.toString()}`, {}, token);
}

export async function syncKnowledgeGaps(
  tenantId: string | number,
  token: string
): Promise<KnowledgeGapSyncResult> {
  return requestJson<KnowledgeGapSyncResult>(
    `/api/tenants/${tenantId}/knowledge-gaps/sync`,
    {
      method: "POST",
      body: JSON.stringify({
        include_human_review: true,
        include_evaluation_runs: true,
        low_confidence_threshold: 0.45,
        max_items: 100
      })
    },
    token
  );
}

export async function updateKnowledgeGap(
  gapId: number,
  token: string,
  payload: {
    status?: "open" | "triaged" | "in_progress" | "resolved" | "rejected" | "archived";
    severity?: "low" | "medium" | "high" | "critical";
    assigned_user_id?: number | null;
    resolution_note?: string;
    linked_knowledge_card_id?: number | null;
    linked_knowledge_document_id?: number | null;
  }
): Promise<KnowledgeGap> {
  return requestJson<KnowledgeGap>(
    `/api/knowledge-gaps/${gapId}`,
    {
      method: "PATCH",
      body: JSON.stringify(payload)
    },
    token
  );
}

export async function createKnowledgeGapDocumentDraft(
  gapId: number,
  token: string
): Promise<KnowledgeGapDocumentDraftResult> {
  return requestJson<KnowledgeGapDocumentDraftResult>(
    `/api/knowledge-gaps/${gapId}/document-drafts`,
    { method: "POST" },
    token
  );
}

export async function createKnowledgeGapRegressionCase(
  gapId: number,
  token: string
): Promise<KnowledgeGapRegressionCaseResult> {
  return requestJson<KnowledgeGapRegressionCaseResult>(
    `/api/knowledge-gaps/${gapId}/regression-cases`,
    { method: "POST" },
    token
  );
}

export async function runRpaCopilotStrategyDryRun(
  payload: RpaCopilotDryRunRequest,
  token: string
): Promise<RpaCopilotDryRunResponse> {
  return requestJson<RpaCopilotDryRunResponse>(
    "/api/rpa-copilot/strategy-dry-run",
    {
      method: "POST",
      body: JSON.stringify(payload)
    },
    token
  );
}
