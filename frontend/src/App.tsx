import {
  Activity,
  AlertTriangle,
  Archive,
  Bot,
  BookOpen,
  BarChart3,
  Bell,
  BriefcaseBusiness,
  ChevronDown,
  CheckCircle2,
  ClipboardCheck,
  FileText,
  History,
  KeyRound,
  LogIn,
  LogOut,
  Mail,
  Menu,
  MessageSquare,
  RefreshCw,
  Route,
  Search,
  Send,
  Settings,
  ShieldCheck,
  Upload,
  UserPlus,
  Users
} from "lucide-react";
import { lazy, Suspense, useEffect, useMemo, useRef, useState } from "react";
import type { ChangeEvent, FormEvent, ReactElement } from "react";

import {
  applyStagedSignedUpdatePackage,
  applyConversationWorkflowAction,
  assignUserRole,
  batchLabelKnowledgeEvaluationRunCaseFactuality,
  configureChannelConnector,
  configureChannelAccount,
  confirmOutboxDraft,
  createLocalBackup,
  createLocalOwner,
  changeCurrentUserPassword,
  createConnectorSendPlan,
  createDiagnosticUploadPackage,
  createDiagnosticIntakeRecord,
  createDiagnosticRemediationRequest,
  createDiagnosticRemediationUpdatePlan,
  createTenantUser,
  createKnowledgeEvaluationSet,
  createLocalBackupRestoreDryRun,
  createBusinessObject,
  createKnowledgeDocument,
  createKnowledgeImport,
  createKnowledgeGapDocumentDraft,
  createKnowledgeGapRegressionCase,
  createAgentReply,
  createConversationMessage,
  createObjectKnowledgeCard,
  createOutboxDeliveryJob,
  createOutboxDraftFromReview,
  createProgramUpdateDryRun,
  createSafeTestConversation,
  createSalesLeadFromConversation,
  createSupportTicketFromConversation,
  createDryRunSendAttempt,
  ensureNoopChannelConnector,
  exportCustomerQualityReport,
  downloadCustomerQualityReportArchive,
  downloadDiagnosticIntakeRecord,
  downloadDiagnosticRemediationRequest,
  checkKnowledgeDocumentPublishGate,
  recordCustomerQualityReportSignoff,
  exportKnowledgeEvaluationRunFinalAnswerLabels,
  exportKnowledgeEvaluationRunReport,
  getContactProfile,
  getBusinessOpsDashboard,
  getDiagnosticBundle,
  getLocalMaintenanceReadiness,
  getLocalSetupStatus,
  getOpsAlertRulesDashboard,
  getOpsMetricsDashboard,
  getWorkerHealthDashboard,
  getKnowledgeEvaluationRun,
  getAiServiceStatus,
  getKnowledgeMemoryMeshOverview,
  getCustomerQualityReport,
  getMonthlyQualityReview,
  getMonthlyOpsReport,
  getOnlineReceiptQualitySummary,
  getPilotReadiness,
  getCustomerMaterialBatches,
  getCustomerMaterialHandoffBundle,
  getCustomerMaterialTemplatePackage,
  getConversationDetail,
  getLlmOpsReadinessSummary,
  getRagCostGovernanceSummary,
  getTenantReplyStrategy,
  importKnowledgeUpdatePackage,
  importKnowledgeEvaluationRunFinalAnswerLabels,
  importKnowledgeConfirmationCsv,
  precheckCustomerMaterialPackage,
  importCustomerServiceQuestionBank,
  getCurrentUser,
  labelKnowledgeEvaluationRunCaseFactuality,
  captureKnowledgeEvaluationRunCaseFinalAnswerSample,
  listChannelAccounts,
  listTenantRoles,
  listTenantUsers,
  listTenantChannels,
  listContactProfiles,
  listConversationInbox,
  listDeliveryFailureReviews,
  listHumanReviewInbox,
  listKnowledgeGaps,
  listBusinessObjects,
  listKnowledgeDocumentChunks,
  listKnowledgeDocuments,
  listKnowledgeDocumentPublications,
  listKnowledgeEvaluationRuns,
  listKnowledgeEvaluationSets,
  listCustomerQualityReportArchives,
  listCustomerQualityReportSignoffs,
  listDiagnosticIntakeRecords,
  listDiagnosticRemediationRequests,
  listLocalBackups,
  listObjectKnowledgeCards,
  listOutboxDeliveryJobs,
  listOutboxDrafts,
  listOutboxSendAttempts,
  listReplyDecisions,
  listSalesLeads,
  listStagedSignedUpdatePackages,
  listSupportTickets,
  login,
  loginLocalDev,
  preflightSignedUpdatePackage,
  publishKnowledgeDocument,
  publishKnowledgeImport,
  previewKnowledgeUpdatePackage,
  precheckKnowledgeImport,
  precheckCustomerServiceQuestionBank,
  resolveDeliveryFailureReview,
  resolveHumanReviewTask,
  runOutboxDeliveryQueue,
  runOutboxWorker,
  runKnowledgeEvaluationSet,
  runKnowledgeImportSample,
  runTrustedInboundWorker,
  rollbackKnowledgeDocumentPublication,
  rollbackStagedSignedUpdatePackage,
  searchKnowledgeDocuments,
  startChannelConnectorAuthorization,
  syncKnowledgeGaps,
  stageSignedUpdatePackage,
  resetUserPassword,
  updateCurrentUserProfile,
  updateCurrentUserSettings,
  updateKnowledgeGap,
  updateBusinessObject,
  updateSalesLead,
  updateSupportTicket,
  updateDiagnosticIntakeRecord,
  updateDiagnosticRemediationRequest,
  updateTenantReplyStrategy,
  upsertChannelConnectorSecrets,
  deleteChannelConnectorSecrets,
  deleteChannelAccountConnection,
  verifyChannelConnector,
  updateUserStatus,
  verifyLocalBackup,
  type AccountRole,
  type AccountUser,
  type BusinessOpsDashboard,
  type BusinessObject,
  type BusinessObjectType,
  type AiServiceStatus,
  type Channel,
  type ChannelAccount,
  type ChannelAccountPayload,
  type ChannelConnectorConfig,
  type ChannelConnectorAuthorization,
  type ChannelConnectorSecretStatus,
  type ChannelConnectorVerification,
  type ContactProfile,
  type ContactProfileDetail,
  type ContactProfileList,
  type ConversationWorkflowActionName,
  type ConversationDetail,
  type ConversationInboxItem,
  type ConversationInboxList,
  type ContactConversationSummary,
  type ContactTicketSummary,
  type CurrentUser,
  type CustomerServiceQuestionBankImportPayload,
  type CustomerServiceQuestionBankPrecheck,
  type DeliveryFailureReview,
  type DiagnosticBundle,
  type DiagnosticIntakeDownload,
  type DiagnosticIntakeRecord,
  type DiagnosticRemediationRequest,
  type DiagnosticRemediationRequestDownload,
  type DiagnosticUploadPackage,
  type HumanReviewInboxItem,
  type KnowledgeChunk,
  type KnowledgeDocument,
  type KnowledgeDocumentPublication,
  type KnowledgeDocumentPublishGateResult,
  type KnowledgeDocumentSearchResponse,
  type KnowledgeUpdatePackageResult,
  type FactualityLabelStatus,
  type KnowledgeEvaluationRun,
  type KnowledgeEvaluationRunCase,
  type KnowledgeEvaluationRunFinalAnswerLabelImportResult,
  type KnowledgeEvaluationRunReport,
  type KnowledgeEvaluationRunSummary,
  type KnowledgeEvaluationSet,
  type KnowledgeGap,
  type KnowledgeGapDocumentDraftResult,
  type KnowledgeGapList,
  type KnowledgeGapRegressionCaseResult,
  type KnowledgeGapSyncResult,
  type KnowledgeImportBatch,
  type KnowledgeImportPrecheck,
  type KnowledgeImportSampleRun,
  type KnowledgeImportTemplateRow,
  type KnowledgePublication,
  type KnowledgeMemoryMeshOverview,
  type LocalOwnerSetupRequest,
  type LocalBackupRecord,
  type LocalBackupRestoreDryRun,
  type LocalMaintenanceReadiness,
  type LocalSetupStatus,
  type LoginRequest,
  type UserPersonalSettings,
  type UserPublicProfile,
  type CustomerQualityReport,
  type CustomerQualityReportExport,
  type CustomerQualityReportArchiveList,
  type CustomerQualityReportSignoffCreate,
  type CustomerQualityReportSignoffList,
  type MonthlyQualityReview,
  type MonthlyOpsReport,
  type OnlineReceiptQualitySummary,
  type PilotReadiness,
  type CustomerMaterialBatchList,
  type KnowledgeConfirmationImportResult,
  type CustomerMaterialHandoffBundle,
  type CustomerMaterialPrecheckResult,
  type CustomerMaterialTemplatePackage,
  type OpsAlertRulesDashboard,
  type OpsAlertRule,
  type OpsMetric,
  type OpsMetricsDashboard,
  type ObjectKnowledgeCard,
  type OutboxDeliveryJob,
  type OutboxDeliveryQueueRun,
  type OutboxDraft,
  type OutboxSendAttempt,
  type OpsRisk,
  type LlmOpsReadinessSummary,
  type ReplyDecision,
  type RagCostGovernanceSummary,
  type SalesLead,
  type SafeTestConversationResult,
  type SalesLeadList,
  type SignedUpdatePreflightResult,
  type SignedUpdateStagedPackage,
  type SupportTicket,
  type SupportTicketList,
  type TenantReplyStrategy,
  type OutboxWorkerRun,
  type TrustedInboundWorkerRun,
  type TrustedInboundWorkerRunRecord,
  type WorkerHealthDashboard,
  type WorkerHeartbeat
} from "./api/client";
import {
  getDefaultNavigationHrefForRoles,
  getNavigationGroupsForRoles,
  getRoleTaskPathsForRoles,
  type RoleTaskPath
} from "./data/navigation";
import {
  DataSourceBadge,
  DisabledReason,
  EXTERNAL_WRITE_OFF_LABEL,
  PanelStateNotice,
  PREVIEW_DATA_LABEL,
  REAL_DATA_LABEL,
  WorkspaceRuntimeStateStrip,
  WorkspaceStateNotice,
  formatAccessDisabledReason
} from "./components/common/WorkspaceState";
import {
  ConversationWorkbenchPanel,
  type ChannelIdentitySummary,
  type WorkbenchColleague
} from "./components/conversation/ConversationWorkbenchPanel";
import { ChannelConnectorCenterPanel } from "./components/channels/ChannelConnectorCenterPanel";
import { KnowledgeWorkspacePage } from "./components/knowledge/KnowledgeWorkspacePage";
import { QualityMetric, QualityReviewPanel } from "./components/quality/QualityReviewPanel";
import type { EChartsOption } from "echarts";
import type { WorkspacePageComponent } from "./pages/workspace/types";

type AgentPresenceStatus = "online" | "away" | "busy" | "invisible";
type AccountMenuModal = "accountInfo" | "personalSettings" | "changePassword";
type PersonalSettingsTab = "basic" | "message" | "autoReply" | "shortcuts" | "serviceNotice";

const agentPresenceOptions: Array<{
  key: AgentPresenceStatus;
  label: string;
  tone: AgentPresenceStatus;
  leaveReasons?: string[];
}> = [
  { key: "online", label: "在线", tone: "online" },
  { key: "away", label: "离开", tone: "away", leaveReasons: ["会议", "就餐", "休息", "其他"] },
  { key: "busy", label: "忙碌", tone: "busy" },
  { key: "invisible", label: "隐身", tone: "invisible" }
];

const defaultPublicProfile: UserPublicProfile = {
  display_name: "",
  signature: "",
  mobile: "",
  phone: "",
  qq: "",
  wechat: ""
};

const defaultPersonalSettings: UserPersonalSettings = {
  system_language: "zh-CN",
  quick_reply_collapsed: false,
  quick_reply_double_click_action: "insert",
  quick_reply_quote_mode: "replace",
  show_typing_status: true,
  default_translate_language: "en",
  message_notifications_enabled: true,
  auto_reply_enabled: false,
  shortcut_send_key: "enter",
  service_notifications_enabled: true
};

function getConnectorSignatureMode(provider: string) {
  const modes: Record<string, string> = {
    website: "website_hmac_sha256",
    wechat_kf: "wechat_kf_token_aeskey",
    wecom: "wecom_token_aeskey",
    wechat_official_account: "wechat_token",
    wechat_official: "wechat_token",
    wechat_miniapp: "wechat_token"
  };
  return modes[provider] ?? "wechat_token_aeskey";
}

function normalizePublicProfile(profile?: Partial<UserPublicProfile> | null): UserPublicProfile {
  return { ...defaultPublicProfile, ...(profile ?? {}) };
}

function normalizePersonalSettings(settings?: Partial<UserPersonalSettings> | null): UserPersonalSettings {
  return { ...defaultPersonalSettings, ...(settings ?? {}) };
}

const OpsDashboardChart = lazy(() =>
  import("./components/OpsDashboardChart").then((module) => ({ default: module.OpsDashboardChart }))
);
const workspacePageComponents: Partial<Record<WorkspaceSection, WorkspacePageComponent>> = {
  overview: lazy(() => import("./pages/workspace/OverviewPage")),
  conversations: lazy(() => import("./pages/workspace/ConversationPage")),
  tickets: lazy(() => import("./pages/workspace/TicketsPage")),
  live: lazy(() => import("./pages/workspace/LivePage")),
  reviews: lazy(() => import("./pages/workspace/ReviewsPage")),
  outbox: lazy(() => import("./pages/workspace/OutboxPage")),
  contacts: lazy(() => import("./pages/workspace/ContactsPage")),
  leads: lazy(() => import("./pages/workspace/LeadsPage")),
  knowledge: lazy(() => import("./pages/workspace/KnowledgePage")),
  gaps: lazy(() => import("./pages/workspace/GapsPage")),
  channels: lazy(() => import("./pages/workspace/ChannelsPage")),
  ops: lazy(() => import("./pages/workspace/OpsPage")),
  model: lazy(() => import("./pages/workspace/ModelPage")),
  pilot: lazy(() => import("./pages/workspace/PilotPage")),
  settings: lazy(() => import("./pages/workspace/SettingsPage")),
  evals: lazy(() => import("./pages/workspace/EvalsPage")),
  quality: lazy(() => import("./pages/workspace/QualityPage"))
};

function WorkspaceRouteLoading() {
  return <div className="workspace-route-loading" role="status">页面加载中</div>;
}

const TOKEN_STORAGE_KEY = "wanfa_standard_ops_access_token";
const NO_PERMISSION_MESSAGE = "当前账号无权读取此模块，请联系管理员开通权限。";

const PERMISSIONS = {
  dashboardRead: "dashboard.read",
  qualityRead: "quality.read",
  channelRead: "channel.read",
  channelManage: "channel.manage",
  conversationRead: "conversation.read",
  conversationManage: "conversation.manage",
  ticketRead: "ticket.read",
  ticketManage: "ticket.manage",
  customerRead: "customer.read",
  customerManage: "customer.manage",
  leadRead: "lead.read",
  leadManage: "lead.manage",
  knowledgeRead: "knowledge.read",
  knowledgeManage: "knowledge.manage",
  channelConnectorManage: "channel.connector.manage",
  opsWorkerHealthRead: "ops.worker_health.read",
  opsAlertRulesRead: "ops.alert_rules.read",
  opsMetricsRead: "ops.metrics.read",
  outboxDraftRead: "outbox.draft.read",
  outboxDraftManage: "outbox.draft.manage",
  outboxSendAttemptRead: "outbox.send_attempt.read",
  outboxSendAttemptManage: "outbox.send_attempt.manage",
  outboxSendPlanManage: "outbox.send_plan.manage",
  outboxDeliveryJobRead: "outbox.delivery_job.read",
  outboxDeliveryJobManage: "outbox.delivery_job.manage",
  outboxFailureReviewRead: "outbox.failure_review.read",
  outboxFailureReviewManage: "outbox.failure_review.manage",
  accountsManage: "accounts.manage",
  updatesManage: "updates.manage"
} as const;

type PermissionValue = (typeof PERMISSIONS)[keyof typeof PERMISSIONS];

function hasPermission(user: CurrentUser | null | undefined, permission: PermissionValue) {
  return Boolean(user?.permissions?.includes(permission));
}

function canReadConversations(user: CurrentUser | null | undefined) {
  return hasPermission(user, PERMISSIONS.conversationRead);
}

function canManageConversations(user: CurrentUser | null | undefined) {
  return hasPermission(user, PERMISSIONS.conversationManage);
}

function canReadTickets(user: CurrentUser | null | undefined) {
  return hasPermission(user, PERMISSIONS.ticketRead);
}

function canManageTickets(user: CurrentUser | null | undefined) {
  return hasPermission(user, PERMISSIONS.ticketManage);
}

function canReadCustomers(user: CurrentUser | null | undefined) {
  return hasPermission(user, PERMISSIONS.customerRead);
}

function canReadLeads(user: CurrentUser | null | undefined) {
  return hasPermission(user, PERMISSIONS.leadRead);
}

function canManageLeads(user: CurrentUser | null | undefined) {
  return hasPermission(user, PERMISSIONS.leadManage);
}

function canReadKnowledgeDocuments(user: CurrentUser | null | undefined) {
  return hasPermission(user, PERMISSIONS.knowledgeRead);
}

function hasKnowledgeManagePermission(user: CurrentUser | null | undefined) {
  return hasPermission(user, PERMISSIONS.knowledgeManage);
}

function canReadKnowledgeEvaluations(user: CurrentUser | null | undefined) {
  return hasKnowledgeManagePermission(user);
}

function canReadKnowledgeGaps(user: CurrentUser | null | undefined) {
  return hasKnowledgeManagePermission(user);
}

function canReadOutboxDrafts(user: CurrentUser | null | undefined) {
  return hasPermission(user, PERMISSIONS.outboxDraftRead) && hasPermission(user, PERMISSIONS.outboxSendAttemptRead);
}

function canReadOutboxDeliveryJobs(user: CurrentUser | null | undefined) {
  return hasPermission(user, PERMISSIONS.outboxDeliveryJobRead);
}

function canReadFailureReviews(user: CurrentUser | null | undefined) {
  return hasPermission(user, PERMISSIONS.outboxFailureReviewRead);
}

function canRunInboundWorker(user: CurrentUser | null | undefined) {
  return hasPermission(user, PERMISSIONS.channelManage);
}

function canReadChannels(user: CurrentUser | null | undefined) {
  return hasPermission(user, PERMISSIONS.channelRead);
}

function canReadDashboard(user: CurrentUser | null | undefined) {
  return hasPermission(user, PERMISSIONS.dashboardRead);
}

function canReadQualityReview(user: CurrentUser | null | undefined) {
  return hasPermission(user, PERMISSIONS.qualityRead);
}

function canReadOpsWorkerHealth(user: CurrentUser | null | undefined) {
  return hasPermission(user, PERMISSIONS.opsWorkerHealthRead);
}

function canReadOpsAlertRules(user: CurrentUser | null | undefined) {
  return hasPermission(user, PERMISSIONS.opsAlertRulesRead);
}

function canReadOpsMetrics(user: CurrentUser | null | undefined) {
  return hasPermission(user, PERMISSIONS.opsMetricsRead);
}

function canManageAccounts(user: CurrentUser | null | undefined) {
  return hasPermission(user, PERMISSIONS.accountsManage);
}

function canManageSignedUpdates(user: CurrentUser | null | undefined) {
  return hasPermission(user, PERMISSIONS.updatesManage);
}

type ConnectionState =
  | { status: "loading"; user?: CurrentUser; error?: string }
  | { status: "ready"; user: CurrentUser; mode: "token" | "demo"; error?: string }
  | { status: "error"; user?: CurrentUser; error: string };

type AuthViewState =
  | { status: "checking" }
  | { status: "login"; error?: string }
  | { status: "submitting"; error?: string }
  | { status: "ready"; user: CurrentUser; token?: string; mode: "token" | "demo" }
  | { status: "error"; error: string };

type OutboxState =
  | { status: "idle"; message: string }
  | { status: "loading"; drafts: OutboxDraft[]; attemptsByDraft: Record<number, OutboxSendAttempt[]> }
  | { status: "ready"; drafts: OutboxDraft[]; attemptsByDraft: Record<number, OutboxSendAttempt[]> }
  | { status: "error"; message: string; drafts: OutboxDraft[]; attemptsByDraft: Record<number, OutboxSendAttempt[]> };

type ReviewInboxState =
  | { status: "idle"; message: string }
  | { status: "loading"; items: HumanReviewInboxItem[] }
  | { status: "ready"; items: HumanReviewInboxItem[] }
  | { status: "error"; message: string; items: HumanReviewInboxItem[] };

type ReplyDecisionStateView =
  | { status: "idle"; message: string; items: ReplyDecision[] }
  | { status: "loading"; items: ReplyDecision[] }
  | { status: "ready"; items: ReplyDecision[] }
  | { status: "error"; message: string; items: ReplyDecision[] };

type ChannelAccountState =
  | { status: "idle"; message: string; channels: Channel[]; accounts: ChannelAccount[] }
  | { status: "loading"; channels: Channel[]; accounts: ChannelAccount[] }
  | { status: "ready"; channels: Channel[]; accounts: ChannelAccount[] }
  | { status: "error"; message: string; channels: Channel[]; accounts: ChannelAccount[] };

type FailureReviewState =
  | { status: "idle"; message: string }
  | { status: "loading"; items: DeliveryFailureReview[] }
  | { status: "ready"; items: DeliveryFailureReview[] }
  | { status: "error"; message: string; items: DeliveryFailureReview[] };

type DeliveryQueueState =
  | { status: "idle"; message: string }
  | { status: "loading"; jobs: OutboxDeliveryJob[] }
  | { status: "ready"; jobs: OutboxDeliveryJob[] }
  | { status: "error"; message: string; jobs: OutboxDeliveryJob[] };

type OpsWorkerHealthState =
  | { status: "idle"; message: string; data: WorkerHealthDashboard | null }
  | { status: "loading"; data: WorkerHealthDashboard | null }
  | { status: "ready"; data: WorkerHealthDashboard }
  | { status: "error"; message: string; data: WorkerHealthDashboard | null };

type BusinessOpsDashboardState =
  | { status: "idle"; message: string; data: BusinessOpsDashboard | null }
  | { status: "loading"; data: BusinessOpsDashboard | null }
  | { status: "ready"; data: BusinessOpsDashboard }
  | { status: "error"; message: string; data: BusinessOpsDashboard | null };

type OnlineReceiptQualityState =
  | { status: "idle"; message: string; data: OnlineReceiptQualitySummary | null }
  | { status: "loading"; message: string; data: OnlineReceiptQualitySummary | null }
  | { status: "ready"; message: string; data: OnlineReceiptQualitySummary }
  | { status: "error"; message: string; data: OnlineReceiptQualitySummary | null };

type OpsAlertRulesState =
  | { status: "idle"; message: string; data: OpsAlertRulesDashboard | null }
  | { status: "loading"; data: OpsAlertRulesDashboard | null }
  | { status: "ready"; data: OpsAlertRulesDashboard }
  | { status: "error"; message: string; data: OpsAlertRulesDashboard | null };

type OpsMetricsState =
  | { status: "idle"; message: string; data: OpsMetricsDashboard | null }
  | { status: "loading"; data: OpsMetricsDashboard | null }
  | { status: "ready"; data: OpsMetricsDashboard }
  | { status: "error"; message: string; data: OpsMetricsDashboard | null };

type AccountManagementState =
  | { status: "idle"; message: string; users: AccountUser[]; roles: AccountRole[] }
  | { status: "loading"; message?: string; users: AccountUser[]; roles: AccountRole[] }
  | { status: "ready"; message?: string; users: AccountUser[]; roles: AccountRole[] }
  | { status: "error"; message: string; users: AccountUser[]; roles: AccountRole[] };

type DiagnosticExportState =
  | { status: "idle"; message: string; lastFilename?: string }
  | { status: "loading"; message: string; lastFilename?: string }
  | { status: "ready"; message: string; lastFilename: string }
  | { status: "error"; message: string; lastFilename?: string };

type DiagnosticIntakeState =
  | { status: "idle"; message: string; records: DiagnosticIntakeRecord[] }
  | { status: "loading"; message: string; records: DiagnosticIntakeRecord[] }
  | { status: "ready"; message: string; records: DiagnosticIntakeRecord[] }
  | { status: "error"; message: string; records: DiagnosticIntakeRecord[] };

type DiagnosticRemediationState =
  | { status: "idle"; message: string; requests: DiagnosticRemediationRequest[] }
  | { status: "loading"; message: string; requests: DiagnosticRemediationRequest[] }
  | { status: "ready"; message: string; requests: DiagnosticRemediationRequest[] }
  | { status: "error"; message: string; requests: DiagnosticRemediationRequest[] };

type SignedUpdatePreflightState =
  | { status: "idle"; message: string; result: SignedUpdatePreflightResult | null }
  | { status: "loading"; message: string; result: SignedUpdatePreflightResult | null }
  | { status: "ready"; message: string; result: SignedUpdatePreflightResult }
  | { status: "error"; message: string; result: SignedUpdatePreflightResult | null };

type SignedUpdateStageState =
  | { status: "idle"; message: string; packages: SignedUpdateStagedPackage[] }
  | { status: "loading"; message: string; packages: SignedUpdateStagedPackage[] }
  | { status: "ready"; message: string; packages: SignedUpdateStagedPackage[] }
  | { status: "error"; message: string; packages: SignedUpdateStagedPackage[] };

type LocalBackupState =
  | { status: "idle"; message: string; backups: LocalBackupRecord[] }
  | { status: "loading"; message: string; backups: LocalBackupRecord[] }
  | { status: "ready"; message: string; backups: LocalBackupRecord[] }
  | { status: "error"; message: string; backups: LocalBackupRecord[] };

type LocalMaintenanceReadinessState =
  | { status: "idle"; message: string; data: LocalMaintenanceReadiness | null }
  | { status: "loading"; message: string; data: LocalMaintenanceReadiness | null }
  | { status: "ready"; message: string; data: LocalMaintenanceReadiness }
  | { status: "error"; message: string; data: LocalMaintenanceReadiness | null };

type PilotReadinessState =
  | { status: "idle"; message: string; data: PilotReadiness | null }
  | { status: "loading"; message: string; data: PilotReadiness | null }
  | { status: "ready"; message: string; data: PilotReadiness }
  | { status: "error"; message: string; data: PilotReadiness | null };

type KnowledgeConfirmationImportState =
  | { status: "idle"; message: string; result: KnowledgeConfirmationImportResult | null }
  | { status: "loading"; message: string; result: KnowledgeConfirmationImportResult | null }
  | { status: "ready"; message: string; result: KnowledgeConfirmationImportResult }
  | { status: "error"; message: string; result: KnowledgeConfirmationImportResult | null };

type CustomerMaterialPrecheckState =
  | { status: "idle"; message: string; result: CustomerMaterialPrecheckResult | null }
  | { status: "loading"; message: string; result: CustomerMaterialPrecheckResult | null }
  | { status: "ready"; message: string; result: CustomerMaterialPrecheckResult }
  | { status: "error"; message: string; result: CustomerMaterialPrecheckResult | null };

type CustomerMaterialBatchListState =
  | { status: "idle"; message: string; data: CustomerMaterialBatchList | null }
  | { status: "loading"; message: string; data: CustomerMaterialBatchList | null }
  | { status: "ready"; message: string; data: CustomerMaterialBatchList }
  | { status: "error"; message: string; data: CustomerMaterialBatchList | null };

type CustomerMaterialTemplatePackageState =
  | { status: "idle"; message: string; data: CustomerMaterialTemplatePackage | null }
  | { status: "loading"; message: string; data: CustomerMaterialTemplatePackage | null }
  | { status: "ready"; message: string; data: CustomerMaterialTemplatePackage }
  | { status: "error"; message: string; data: CustomerMaterialTemplatePackage | null };

type CustomerMaterialHandoffBundleState =
  | { status: "idle"; message: string; data: CustomerMaterialHandoffBundle | null }
  | { status: "loading"; message: string; data: CustomerMaterialHandoffBundle | null }
  | { status: "ready"; message: string; data: CustomerMaterialHandoffBundle }
  | { status: "error"; message: string; data: CustomerMaterialHandoffBundle | null };

type ConversationInboxState =
  | { status: "idle"; message: string; data: ConversationInboxList }
  | { status: "loading"; data: ConversationInboxList }
  | { status: "ready"; data: ConversationInboxList }
  | { status: "error"; message: string; data: ConversationInboxList };

type ConversationDetailState =
  | { status: "idle"; message: string; data: ConversationDetail | null }
  | { status: "loading"; message: string; data: ConversationDetail | null }
  | { status: "ready"; message: string; data: ConversationDetail }
  | { status: "error"; message: string; data: ConversationDetail | null };

type LocalReplyState =
  | { status: "idle"; conversationId: number | null; message: string }
  | { status: "sending"; conversationId: number; message: string }
  | { status: "sent"; conversationId: number; message: string }
  | { status: "error"; conversationId: number | null; message: string };

type SupportTicketState =
  | { status: "idle"; message: string; data: SupportTicketList }
  | { status: "loading"; data: SupportTicketList }
  | { status: "ready"; message?: string; data: SupportTicketList }
  | { status: "error"; message: string; data: SupportTicketList };

type ContactProfileState =
  | { status: "idle"; message: string; data: ContactProfileList; detail: ContactProfileDetail | null }
  | { status: "loading"; data: ContactProfileList; detail: ContactProfileDetail | null }
  | { status: "ready"; message?: string; data: ContactProfileList; detail: ContactProfileDetail | null }
  | { status: "error"; message: string; data: ContactProfileList; detail: ContactProfileDetail | null };

type SalesLeadState =
  | { status: "idle"; message: string; data: SalesLeadList }
  | { status: "loading"; data: SalesLeadList }
  | { status: "ready"; message?: string; data: SalesLeadList }
  | { status: "error"; message: string; data: SalesLeadList };

interface ConversationInboxFilters {
  assigned: string;
  sla: string;
  sort: string;
  priority: string;
  channelId?: number | null;
}

interface SupportTicketFilters {
  assigned: string;
  sla: string;
  priority: string;
}

interface SalesLeadFilters {
  intent: string;
  owner: string;
}

interface KnowledgeWorkbenchState {
  status: "idle" | "loading" | "ready" | "error";
  message: string;
  businessObjects: BusinessObject[];
  objectCardsByObject: Record<number, ObjectKnowledgeCard[]>;
  documents: KnowledgeDocument[];
  chunksByDocument: Record<number, KnowledgeChunk[]>;
  publicationsByDocument: Record<number, KnowledgeDocumentPublication[]>;
  searchResult: KnowledgeDocumentSearchResponse | null;
}

interface KnowledgeMemoryMeshState {
  status: "idle" | "loading" | "ready" | "error";
  message: string;
  data: KnowledgeMemoryMeshOverview | null;
}

interface TenantReplyStrategyState {
  status: "idle" | "loading" | "ready" | "error";
  message: string;
  data: TenantReplyStrategy | null;
}

interface RagCostGovernanceState {
  status: "idle" | "loading" | "ready" | "error";
  message: string;
  data: RagCostGovernanceSummary | null;
}

interface LlmOpsReadinessState {
  status: "idle" | "loading" | "ready" | "error";
  message: string;
  data: LlmOpsReadinessSummary | null;
}

interface ReplyStrategyDraft {
  blockedPolicyTerms: string;
  manualReviewTerms: string;
  forceDraftOnly: boolean;
}

interface BusinessObjectDraft {
  editingId: number | null;
  type: BusinessObjectType;
  title: string;
  aliases: string;
  summary: string;
}

interface ObjectKnowledgeCardDraft {
  businessObjectId: number | null;
  question: string;
  answer: string;
  triggerKeywords: string;
}

interface KnowledgeDocumentDraft {
  title: string;
  sourceUri: string;
  tags: string;
  rawText: string;
}

interface KnowledgeUpdatePackageDraft {
  text: string;
  result: KnowledgeUpdatePackageResult | null;
  status: "idle" | "loading" | "ready" | "error";
  message: string;
}

interface KnowledgeTemplateImportDraft {
  sourceFileRef: string;
  text: string;
  status: "idle" | "loading" | "ready" | "error";
  message: string;
  precheck: KnowledgeImportPrecheck | null;
  importBatch: KnowledgeImportBatch | null;
  sampleRun: KnowledgeImportSampleRun | null;
  publication: KnowledgePublication | null;
}

interface AiServiceStatusState {
  status: "idle" | "loading" | "ready" | "error";
  message: string;
  data: AiServiceStatus | null;
}

interface ChannelConnectorSelfServiceState {
  status: "idle" | "loading" | "ready" | "error";
  message: string;
  config: ChannelConnectorConfig | null;
  authorization: ChannelConnectorAuthorization | null;
  secretStatus: ChannelConnectorSecretStatus | null;
  verification: ChannelConnectorVerification | null;
}

interface KnowledgeEvaluationState {
  status: "idle" | "loading" | "ready" | "error";
  message: string;
  sets: KnowledgeEvaluationSet[];
  lastRun: KnowledgeEvaluationRun | null;
  runsBySet: Record<number, KnowledgeEvaluationRunSummary[]>;
}

interface MonthlyQualityReviewState {
  status: "idle" | "loading" | "ready" | "error";
  message: string;
  data: MonthlyQualityReview | null;
}

interface MonthlyOpsReportState {
  status: "idle" | "loading" | "ready" | "error";
  message: string;
  data: MonthlyOpsReport | null;
}

interface CustomerQualityReportState {
  status: "idle" | "loading" | "ready" | "error";
  message: string;
  data: CustomerQualityReport | null;
}

interface CustomerQualityReportArchiveState {
  status: "idle" | "loading" | "ready" | "error";
  message: string;
  data: CustomerQualityReportArchiveList | null;
}

interface CustomerQualityReportSignoffState {
  status: "idle" | "loading" | "ready" | "error";
  message: string;
  data: CustomerQualityReportSignoffList | null;
}

interface KnowledgeEvaluationDraft {
  name: string;
  description: string;
  evaluationMode: "document_retrieval" | "customer_service_retrieval";
  casesText: string;
}

interface CustomerQuestionBankDraft {
  text: string;
  result: CustomerServiceQuestionBankPrecheck | null;
  status: "idle" | "loading" | "ready" | "error";
  message: string;
}

interface FinalAnswerLabelImportDraft {
  text: string;
  result: KnowledgeEvaluationRunFinalAnswerLabelImportResult | null;
  status: "idle" | "loading" | "ready" | "error";
  message: string;
}

interface KnowledgeGapState {
  status: "idle" | "loading" | "ready" | "error";
  message: string;
  data: KnowledgeGapList;
  lastSync: KnowledgeGapSyncResult | null;
}

interface RoleTaskPathMetric {
  value: string;
  note: string;
  tone: "urgent" | "warning" | "normal" | "success";
}

interface RoleTaskPathMetrics {
  reviewItems: HumanReviewInboxItem[];
  outboxDrafts: OutboxDraft[];
  failureReviews: DeliveryFailureReview[];
  deliveryJobs: OutboxDeliveryJob[];
  supportTickets: SupportTicketState;
  salesLeads: SalesLeadState;
  knowledgeGaps: KnowledgeGapState;
  businessOpsDashboard: BusinessOpsDashboardState;
}

type WorkspaceTaskSource = "overview" | "quality" | "knowledge";

interface WorkspaceTaskContext {
  source: WorkspaceTaskSource;
  targetSection: WorkspaceSection;
  task: string;
  title: string;
  description: string;
  range: string;
  channelId: number | null;
  channelLabel: string;
  status?: string;
  queue?: string;
  emptyText: string;
}

type WorkspaceSection =
  | "overview"
  | "conversations"
  | "tickets"
  | "live"
  | "reviews"
  | "outbox"
  | "contacts"
  | "leads"
  | "knowledge"
  | "gaps"
  | "channels"
  | "model"
  | "evals"
  | "quality"
  | "ops"
  | "pilot"
  | "settings";

interface ListViewState {
  query: string;
  status: string;
  severity?: string;
  sourceType?: string;
  page: number;
  pageSize: number;
}

interface StatusOption {
  label: string;
  value: string;
}

interface PagedResult<T> {
  items: T[];
  total: number;
  page: number;
  pageCount: number;
  start: number;
  end: number;
}

const DEFAULT_PAGE_SIZE = 6;
const EMPTY_CONVERSATION_INBOX: ConversationInboxList = {
  items: [],
  page: 1,
  page_size: 8,
  total: 0
};

const EMPTY_SUPPORT_TICKET_LIST: SupportTicketList = {
  items: [],
  page: 1,
  page_size: 8,
  total: 0
};

const EMPTY_CONTACT_PROFILE_LIST: ContactProfileList = {
  items: [],
  page: 1,
  page_size: 8,
  total: 0
};

const EMPTY_SALES_LEAD_LIST: SalesLeadList = {
  items: [],
  page: 1,
  page_size: 8,
  total: 0
};

const EMPTY_KNOWLEDGE_GAP_LIST: KnowledgeGapList = {
  items: [],
  page: 1,
  page_size: 50,
  total: 0
};

const DEFAULT_KNOWLEDGE_UPDATE_PACKAGE_TEXT = JSON.stringify(
  {
    schema_version: "wanfa.knowledge_update_package.v1",
    package_id: "pkg-local-knowledge-fix-001",
    package_name: "本地知识修复包",
    source_diagnostic_filename: "wanfa-diagnostic-local.json",
    notes: "用于补充业务对象、标准问答、政策文档和回归题。",
    business_objects: [
      {
        ref: "starter-package",
        type: "package",
        title: "AI客服入门验证包",
        aliases: ["入门版", "官网客服试点"],
        summary: "适合先验证官网客服、核心问答、留资和转人工的小微企业。",
        status: "active"
      }
    ],
    object_knowledge_cards: [
      {
        business_object_ref: "starter-package",
        question: "入门验证包适合什么客户？",
        answer: "适合先验证官网客服、核心问题、留资和转人工流程的小微企业。复杂多渠道自动外发需要后续授权。",
        trigger_keywords: ["入门验证", "官网客服", "小微企业"],
        source: "knowledge_update_package",
        status: "active"
      }
    ],
    knowledge_documents: [
      {
        title: "售后退换政策",
        source_type: "knowledge_update_package",
        source_uri: "internal://policy/after-sales",
        tags: ["流程政策", "售后", "退换"],
        status: "active",
        raw_text: "客户咨询七天退换时，应先确认订单状态、商品状态和平台规则。不能承诺无条件退款。"
      },
      {
        title: "禁用承诺与转人工规则",
        source_type: "knowledge_update_package",
        source_uri: "internal://policy/reply-risk-rules",
        tags: ["禁用承诺", "转人工规则", "风险门禁"],
        status: "active",
        raw_text: "命中私下转账、绕过平台、保证收益、无条件退款等说法时不得自动回复；命中投诉、起诉、赔偿、举报、差评、封号等说法时转人工接待。"
      }
    ],
    evaluation_sets: [
      {
        name: "知识更新回归题集",
        description: "导入知识包后用于检查核心问题是否能命中。",
        status: "active",
        evaluation_mode: "customer_service_retrieval",
        cases: [
          {
            external_case_id: "local-fix-001",
            question: "超过七天还能退货吗？",
            expected_terms: ["订单状态", "商品状态", "平台规则"],
            expected_source_uri: "internal://policy/after-sales",
            forbidden_terms: ["无条件退款"],
            expected_human_review: false,
            allow_auto_reply: true,
            status: "active"
          }
        ]
      }
    ]
  },
  null,
  2
);

const DEFAULT_CUSTOMER_KNOWLEDGE_INTAKE_CSV = [
  "资料类型,对象类型,对象名称,别名,客户问题,标准答案,流程标题,流程正文,禁用承诺词,转人工词,回归问题,期望词,禁止词,来源",
  "标准问答,package,AI客服入门验证包,\"入门版;官网客服试点\",入门验证包适合什么客户？,适合先验证官网客服、核心问题、留资和转人工流程的小微企业。复杂多渠道自动外发需要后续授权。,,,,,入门验证包适合什么客户？,\"官网客服;转人工\",,客户确认模板",
  "流程政策,,, ,,,售后退换政策,客户咨询七天退换时，应先确认订单状态、商品状态和平台规则。不能承诺无条件退款。,无条件退款,\"投诉;起诉;赔偿\",超过七天还能退货吗？,\"订单状态;商品状态;平台规则\",无条件退款,售后政策手册",
  "风险规则,,,,,,,,\"私下转账;绕过平台;保证收益\",\"投诉;举报;差评\",客户要求私下转账可以吗？,\"转人工;平台规则\",私下转账,风险规则表"
].join("\n");

const DEFAULT_KNOWLEDGE_TEMPLATE_IMPORT_TEXT = [
  "business_object,question,answer,trigger_keywords,channel_scope,risk_level,forbidden_commitments,handoff_rule,source_note,status",
  "餐饮门店 AI 客服接入,餐饮门店怎么接入 AI 客服,餐饮门店可以先接入网站客服组件，再导入门店常见问题，负责人发布后启用 AI 接待,\"餐饮门店;AI客服;接入;网站客服\",website,normal,,,本地测试资料,active",
  "售后退款规则,我要投诉并要求退款赔偿,投诉、退款、赔偿类问题需要人工客服核实订单、责任边界和平台规则后处理,\"投诉;退款;赔偿\",website,blocked,\"无条件退款;保证赔偿\",命中投诉退款赔偿必须转人工,风险规则测试,active"
].join("\n");

function buildDefaultCustomerQuestionBankText() {
  const channels = ["web_widget", "wecom", "douyin", "taobao", "xiaohongshu"];
  const categories = ["售前咨询", "交付部署", "售后退款", "隐私安全", "知识缺口"];
  const risks = ["low", "medium", "high"];
  return JSON.stringify(
    {
      name: "客户试点脱敏题库 50 题",
      description: "用于导入客户真实问题的脱敏样例。正式使用时请替换为客户确认后的 50-100 条问题。",
      source_label: "local_desensitized_bank_sample",
      minimum_case_count: 50,
      maximum_case_count: 100,
      evaluation_mode: "customer_service_retrieval",
      cases: Array.from({ length: 50 }, (_, index) => {
        const caseNumber = index + 1;
        const handoff = index % 5 === 0;
        return {
          external_case_id: `sample-bank-${String(caseNumber).padStart(3, "0")}`,
          source_channel: channels[index % channels.length],
          source_category: categories[index % categories.length],
          question: `客户第${caseNumber}个脱敏问题：套餐范围、交付步骤和售后边界怎么确认？`,
          question_type: handoff ? "risk_handoff" : "standard_customer_question",
          expected_terms: ["套餐范围", "交付步骤", "人工确认"],
          expected_source_uri: `internal://customer-bank/source-${index % 4}`,
          expected_document_title: "客户试点知识包",
          expected_human_review: handoff,
          allow_auto_reply: !handoff,
          forbidden_terms: index % 4 === 0 ? ["保证效果"] : [],
          risk_level: risks[index % risks.length],
          annotation_notes: `business_object_hash=bo${String(caseNumber).padStart(3, "0")};expected_answer_hash=ans${String(caseNumber).padStart(3, "0")};真实答案已脱敏后另行保管`,
          required_citation: true,
          priority: caseNumber,
          status: "active"
        };
      })
    },
    null,
    2
  );
}

const DEFAULT_CUSTOMER_QUESTION_BANK_TEXT = buildDefaultCustomerQuestionBankText();

const DEFAULT_SIGNED_UPDATE_PACKAGE_TEXT = JSON.stringify(
  {
    schema_version: "wanfa.signed_update_package.v1",
    manifest: {
      schema_version: "wanfa.signed_update_manifest.v1",
      package_id: "wanfa-update-local-sample",
      package_name: "本地知识修复签名包示例",
      package_type: "knowledge",
      package_version: "2026.07.sample",
      product: "wanfa-standard-ops",
      released_at: "2026-07-03T10:00:00+08:00",
      compatible_app_versions: ["0.1.0"],
      requires_maintenance_window: false,
      payload_digest_sha256: "0000000000000000000000000000000000000000000000000000000000000000",
      payload_size_bytes: 0,
      operations: [
        {
          target: "knowledge_documents",
          action: "upsert",
          count: 1,
          summary: "示例：补充一条知识文档"
        }
      ]
    },
    payload: {
      operations: [
        {
          target: "knowledge_documents",
          action: "upsert",
          count: 1,
          summary: "示例 payload。真实包由售后工具生成。"
        }
      ]
    },
    release_notes: "这是预检示例。真实更新包需要有效签名和 payload 摘要。",
    checksums: {
      payload_sha256: "0000000000000000000000000000000000000000000000000000000000000000"
    },
    signature: {
      algorithm: "rsa_pkcs1v15_sha256",
      key_id: "release-key-id",
      value: "ZmFrZV9zaWduYXR1cmU="
    }
  },
  null,
  2
);

export function App() {
  const [connection, setConnection] = useState<ConnectionState>({ status: "loading" });
  const [auth, setAuth] = useState<AuthViewState>({ status: "checking" });
  const [localSetupStatus, setLocalSetupStatus] = useState<LocalSetupStatus | null>(null);
  const [activeSection, setActiveSection] = useState<WorkspaceSection>(() => getInitialWorkspaceSection());
  const [workspaceHash, setWorkspaceHash] = useState(() => (typeof window === "undefined" ? "" : window.location.hash));
  const [expandedNavGroups, setExpandedNavGroups] = useState<Record<string, boolean>>({});
  const [isMessageCenterOpen, setIsMessageCenterOpen] = useState(false);
  const [isAccountMenuOpen, setIsAccountMenuOpen] = useState(false);
  const [activeAccountMenuModal, setActiveAccountMenuModal] = useState<AccountMenuModal | null>(null);
  const [personalSettingsTab, setPersonalSettingsTab] = useState<PersonalSettingsTab>("basic");
  const [accountProfileForm, setAccountProfileForm] = useState<{
    name: string;
    avatar_data_url: string;
    public_profile: UserPublicProfile;
  }>({ name: "", avatar_data_url: "", public_profile: defaultPublicProfile });
  const [personalSettingsForm, setPersonalSettingsForm] = useState<UserPersonalSettings>(defaultPersonalSettings);
  const [passwordForm, setPasswordForm] = useState({ current: "", next: "", confirm: "" });
  const [passwordNotice, setPasswordNotice] = useState("");
  const [accountModalNotice, setAccountModalNotice] = useState("");
  const [accountModalSaving, setAccountModalSaving] = useState(false);
  const [isPresenceMenuOpen, setIsPresenceMenuOpen] = useState(false);
  const [agentPresenceStatus, setAgentPresenceStatus] = useState<AgentPresenceStatus>("online");
  const [agentLeaveReason, setAgentLeaveReason] = useState("会议");
  const [dialogueScope, setDialogueScope] = useState<"current" | "recent" | "colleagues">("current");
  const [selectedLiveColleagueId, setSelectedLiveColleagueId] = useState<number | null>(null);
  const [dialogueSearch, setDialogueSearch] = useState("");
  const [collapsedDialogueSections, setCollapsedDialogueSections] = useState<Record<string, boolean>>({});
  const [overviewTaskContext, setOverviewTaskContext] = useState<WorkspaceTaskContext | null>(() =>
    parseWorkspaceTaskContext(typeof window === "undefined" ? "" : window.location.hash)
  );
  const workspaceRef = useRef<HTMLElement | null>(null);
  const [reviewInbox, setReviewInbox] = useState<ReviewInboxState>({
    status: "idle",
    message: "等待正式登录"
  });
  const [replyDecisionState, setReplyDecisionState] = useState<ReplyDecisionStateView>({
    status: "idle",
    message: "等待正式登录",
    items: []
  });
  const [channelIdentityById, setChannelIdentityById] = useState<Record<number, ChannelIdentitySummary>>({});
  const [channelAccountState, setChannelAccountState] = useState<ChannelAccountState>({
    status: "idle",
    message: "等待正式登录",
    channels: [],
    accounts: []
  });
  const [conversationInbox, setConversationInbox] = useState<ConversationInboxState>({
    status: "idle",
    message: "等待正式登录",
    data: EMPTY_CONVERSATION_INBOX
  });
  const [conversationDetail, setConversationDetail] = useState<ConversationDetailState>({
    status: "idle",
    message: "等待选择会话",
    data: null
  });
  const [localReplyState, setLocalReplyState] = useState<LocalReplyState>({
    status: "idle",
    conversationId: null,
    message: "本地会话回复尚未发送"
  });
  const [supportTickets, setSupportTickets] = useState<SupportTicketState>({
    status: "idle",
    message: "等待正式登录",
    data: EMPTY_SUPPORT_TICKET_LIST
  });
  const [contactProfiles, setContactProfiles] = useState<ContactProfileState>({
    status: "idle",
    message: "等待正式登录",
    data: EMPTY_CONTACT_PROFILE_LIST,
    detail: null
  });
  const [salesLeads, setSalesLeads] = useState<SalesLeadState>({
    status: "idle",
    message: "等待正式登录",
    data: EMPTY_SALES_LEAD_LIST
  });
  const [outbox, setOutbox] = useState<OutboxState>({
    status: "idle",
    message: "等待正式登录"
  });
  const [failureReviews, setFailureReviews] = useState<FailureReviewState>({
    status: "idle",
    message: "等待正式登录"
  });
  const [deliveryQueue, setDeliveryQueue] = useState<DeliveryQueueState>({
    status: "idle",
    message: "等待正式登录"
  });
  const [opsWorkerHealth, setOpsWorkerHealth] = useState<OpsWorkerHealthState>({
    status: "idle",
    message: "等待正式登录",
    data: null
  });
  const [businessOpsDashboard, setBusinessOpsDashboard] = useState<BusinessOpsDashboardState>({
    status: "idle",
    message: "等待正式登录",
    data: null
  });
  const [opsAlertRules, setOpsAlertRules] = useState<OpsAlertRulesState>({
    status: "idle",
    message: "等待正式登录",
    data: null
  });
  const [opsMetrics, setOpsMetrics] = useState<OpsMetricsState>({
    status: "idle",
    message: "等待正式登录",
    data: null
  });
  const [accountManagement, setAccountManagement] = useState<AccountManagementState>({
    status: "idle",
    message: "等待正式登录",
    users: [],
    roles: []
  });
  const [diagnosticExport, setDiagnosticExport] = useState<DiagnosticExportState>({
    status: "idle",
    message: "尚未生成诊断包"
  });
  const [diagnosticIntake, setDiagnosticIntake] = useState<DiagnosticIntakeState>({
    status: "idle",
    message: "尚未同步售后接收记录",
    records: []
  });
  const [diagnosticRemediation, setDiagnosticRemediation] = useState<DiagnosticRemediationState>({
    status: "idle",
    message: "尚未同步处理单",
    requests: []
  });
  const [signedUpdatePreflight, setSignedUpdatePreflight] = useState<SignedUpdatePreflightState>({
    status: "idle",
    message: "尚未校验更新包",
    result: null
  });
  const [signedUpdateStage, setSignedUpdateStage] = useState<SignedUpdateStageState>({
    status: "idle",
    message: "尚未同步暂存更新包",
    packages: []
  });
  const [localBackupState, setLocalBackupState] = useState<LocalBackupState>({
    status: "idle",
    message: "尚未创建本地备份点",
    backups: []
  });
  const [localRestoreDryRun, setLocalRestoreDryRun] = useState<LocalBackupRestoreDryRun | null>(null);
  const [localMaintenanceReadiness, setLocalMaintenanceReadiness] = useState<LocalMaintenanceReadinessState>({
    status: "idle",
    message: "尚未同步本地维护闭环",
    data: null
  });
  const [knowledgeWorkbench, setKnowledgeWorkbench] = useState<KnowledgeWorkbenchState>({
    status: "idle",
    message: "等待正式登录",
    businessObjects: [],
    objectCardsByObject: {},
    documents: [],
    chunksByDocument: {},
    publicationsByDocument: {},
    searchResult: null
  });
  const [knowledgeMemoryMesh, setKnowledgeMemoryMesh] = useState<KnowledgeMemoryMeshState>({
    status: "idle",
    message: "等待正式登录",
    data: null
  });
  const [knowledgeEvaluation, setKnowledgeEvaluation] = useState<KnowledgeEvaluationState>({
    status: "idle",
    message: "等待正式登录",
    sets: [],
    lastRun: null,
    runsBySet: {}
  });
  const [monthlyQualityReview, setMonthlyQualityReview] = useState<MonthlyQualityReviewState>({
    status: "idle",
    message: "等待正式登录",
    data: null
  });
  const [monthlyOpsReport, setMonthlyOpsReport] = useState<MonthlyOpsReportState>({
    status: "idle",
    message: "等待正式登录",
    data: null
  });
  const [pilotReadiness, setPilotReadiness] = useState<PilotReadinessState>({
    status: "idle",
    message: "等待正式登录",
    data: null
  });
  const [knowledgeConfirmationImport, setKnowledgeConfirmationImport] = useState<KnowledgeConfirmationImportState>({
    status: "idle",
    message: "等待客户确认表",
    result: null
  });
  const [customerMaterialPrecheck, setCustomerMaterialPrecheck] = useState<CustomerMaterialPrecheckState>({
    status: "idle",
    message: "等待资料包预检",
    result: null
  });
  const [customerMaterialBatches, setCustomerMaterialBatches] = useState<CustomerMaterialBatchListState>({
    status: "idle",
    message: "等待读取资料批次",
    data: null
  });
  const [customerMaterialTemplatePackage, setCustomerMaterialTemplatePackage] =
    useState<CustomerMaterialTemplatePackageState>({
      status: "idle",
      message: "等待加载资料模板",
      data: null
    });
  const [customerMaterialHandoffBundle, setCustomerMaterialHandoffBundle] =
    useState<CustomerMaterialHandoffBundleState>({
      status: "idle",
      message: "等待生成资料回传包",
      data: null
    });
  const [onlineReceiptQuality, setOnlineReceiptQuality] = useState<OnlineReceiptQualityState>({
    status: "idle",
    message: "等待正式登录",
    data: null
  });
  const [customerQualityReport, setCustomerQualityReport] = useState<CustomerQualityReportState>({
    status: "idle",
    message: "等待正式登录",
    data: null
  });
  const [customerQualityReportArchives, setCustomerQualityReportArchives] = useState<CustomerQualityReportArchiveState>({
    status: "idle",
    message: "等待正式登录",
    data: null
  });
  const [customerQualityReportSignoffs, setCustomerQualityReportSignoffs] = useState<CustomerQualityReportSignoffState>({
    status: "idle",
    message: "等待正式登录",
    data: null
  });
  const [knowledgeGaps, setKnowledgeGaps] = useState<KnowledgeGapState>({
    status: "idle",
    message: "等待正式登录",
    data: EMPTY_KNOWLEDGE_GAP_LIST,
    lastSync: null
  });
  const [knowledgeDraft, setKnowledgeDraft] = useState<KnowledgeDocumentDraft>({
    title: "",
    sourceUri: "",
    tags: "",
    rawText: ""
  });
  const [knowledgeUpdatePackageDraft, setKnowledgeUpdatePackageDraft] = useState<KnowledgeUpdatePackageDraft>({
    text: DEFAULT_KNOWLEDGE_UPDATE_PACKAGE_TEXT,
    result: null,
    status: "idle",
    message: "等待导入知识资料包"
  });
  const [knowledgeTemplateImportDraft, setKnowledgeTemplateImportDraft] = useState<KnowledgeTemplateImportDraft>({
    sourceFileRef: "frontend://knowledge-template-v1",
    text: DEFAULT_KNOWLEDGE_TEMPLATE_IMPORT_TEXT,
    status: "idle",
    message: "等待表格资料预检",
    precheck: null,
    importBatch: null,
    sampleRun: null,
    publication: null
  });
  const [aiServiceStatus, setAiServiceStatus] = useState<AiServiceStatusState>({
    status: "idle",
    message: "等待正式登录",
    data: null
  });
  const [channelConnectorSelfService, setChannelConnectorSelfService] = useState<ChannelConnectorSelfServiceState>({
    status: "idle",
    message: "等待选择渠道并配置连接器",
    config: null,
    authorization: null,
    secretStatus: null,
    verification: null
  });
  const [tenantReplyStrategy, setTenantReplyStrategy] = useState<TenantReplyStrategyState>({
    status: "idle",
    message: "等待正式登录",
    data: null
  });
  const [ragCostGovernance, setRagCostGovernance] = useState<RagCostGovernanceState>({
    status: "idle",
    message: "等待正式登录",
    data: null
  });
  const [llmOpsReadiness, setLlmOpsReadiness] = useState<LlmOpsReadinessState>({
    status: "idle",
    message: "等待正式登录",
    data: null
  });
  const [replyStrategyDraft, setReplyStrategyDraft] = useState<ReplyStrategyDraft>({
    blockedPolicyTerms: "私下转账，绕过平台，保证收益，百分百保证",
    manualReviewTerms: "投诉，起诉，赔偿，举报，差评，封号",
    forceDraftOnly: false
  });
  const [businessObjectDraft, setBusinessObjectDraft] = useState<BusinessObjectDraft>({
    editingId: null,
    type: "product",
    title: "",
    aliases: "",
    summary: ""
  });
  const [objectKnowledgeCardDraft, setObjectKnowledgeCardDraft] = useState<ObjectKnowledgeCardDraft>({
    businessObjectId: null,
    question: "",
    answer: "",
    triggerKeywords: ""
  });
  const [evaluationDraft, setEvaluationDraft] = useState<KnowledgeEvaluationDraft>({
    name: "",
    description: "",
    evaluationMode: "customer_service_retrieval",
    casesText: ""
  });
  const [customerQuestionBankDraft, setCustomerQuestionBankDraft] = useState<CustomerQuestionBankDraft>({
    text: DEFAULT_CUSTOMER_QUESTION_BANK_TEXT,
    result: null,
    status: "idle",
    message: "等待预检真实客户题库包"
  });
  const [finalAnswerLabelImportDraft, setFinalAnswerLabelImportDraft] = useState<FinalAnswerLabelImportDraft>({
    text: "",
    result: null,
    status: "idle",
    message: "等待粘贴最终回复样本与人工标签 CSV"
  });
  const [knowledgeSearchQuery, setKnowledgeSearchQuery] = useState("");
  const [lastWorkerRun, setLastWorkerRun] = useState<OutboxWorkerRun | null>(null);
  const [lastDeliveryQueueRun, setLastDeliveryQueueRun] = useState<OutboxDeliveryQueueRun | null>(null);
  const [lastInboundWorkerRun, setLastInboundWorkerRun] = useState<TrustedInboundWorkerRun | null>(null);
  const [selectedReviewId, setSelectedReviewId] = useState<number | null>(null);
  const [selectedLiveConversationId, setSelectedLiveConversationId] = useState<number | null>(null);
  const liveAutoRefreshInFlightRef = useRef(false);
  const [locallyClosedConversationIds, setLocallyClosedConversationIds] = useState<Set<number>>(() => new Set());
  const [conversationInboxView, setConversationInboxView] = useState<ListViewState>(() => createListViewState(8));
  const [conversationInboxFilters, setConversationInboxFilters] = useState<ConversationInboxFilters>({
    assigned: "all",
    sla: "all",
    sort: "waiting_desc",
    priority: "all"
  });
  const [supportTicketListView, setSupportTicketListView] = useState<ListViewState>(() => createListViewState(8));
  const [supportTicketFilters, setSupportTicketFilters] = useState<SupportTicketFilters>({
    assigned: "all",
    sla: "all",
    priority: "all"
  });
  const [contactProfileListView, setContactProfileListView] = useState<ListViewState>(() => createListViewState(8));
  const [salesLeadListView, setSalesLeadListView] = useState<ListViewState>(() => createListViewState(8));
  const [salesLeadFilters, setSalesLeadFilters] = useState<SalesLeadFilters>({
    intent: "all",
    owner: "all"
  });
  const [reviewListView, setReviewListView] = useState<ListViewState>(() => createListViewState());
  const [outboxListView, setOutboxListView] = useState<ListViewState>(() => createListViewState());
  const [failureListView, setFailureListView] = useState<ListViewState>(() => createListViewState());
  const [knowledgeDocumentListView, setKnowledgeDocumentListView] = useState<ListViewState>(() => createListViewState());
  const [knowledgeGapListView, setKnowledgeGapListView] = useState<ListViewState>(() => createListViewState(8));
  const [evaluationSetListView, setEvaluationSetListView] = useState<ListViewState>(() => createListViewState(4));
  const [evaluationResultListView, setEvaluationResultListView] = useState<ListViewState>(() => createListViewState(8));
  const authRoles = auth.status === "ready" ? auth.user.roles : [];
  const navigationRoleKey = authRoles.join("|");
  const visibleNavigationGroups = useMemo(
    () => getNavigationGroupsForRoles(authRoles),
    [navigationRoleKey]
  );
  const visibleTaskPaths = useMemo(
    () => getRoleTaskPathsForRoles(authRoles),
    [navigationRoleKey]
  );
  const defaultWorkspaceSection = useMemo(
    () => getWorkspaceSectionFromHash(getDefaultNavigationHrefForRoles(authRoles)),
    [navigationRoleKey]
  );
  const channelIdentities = useMemo(
    () => ({
      ...buildChannelIdentityFallbacks(conversationInbox.data.items),
      ...channelIdentityById
    }),
    [conversationInbox.data.items, channelIdentityById]
  );

  async function refreshConnection(token?: string, mode: "token" | "demo" = "token"): Promise<CurrentUser | null> {
    setConnection((current) => ({ status: "loading", user: current.user }));
    try {
      const user = await getCurrentUser(token);
      setConnection({ status: "ready", user, mode });
      setAuth({ status: "ready", user, token, mode });
      return user;
    } catch (error) {
      const message = error instanceof Error ? error.message : "无法连接后端";
      setConnection((current) => ({ status: "error", user: current.user, error: message }));
      setAuth({ status: "login", error: message });
      return null;
    }
  }

  async function refreshLocalSetupState() {
    try {
      const status = await getLocalSetupStatus();
      setLocalSetupStatus(status);
      return status;
    } catch {
      setLocalSetupStatus(null);
      return null;
    }
  }

  async function refreshChannelAccounts(tenantId: string, token: string) {
    setChannelAccountState((current) => ({
      status: "loading",
      channels: current.channels,
      accounts: current.accounts
    }));
    try {
      const [channels, accounts] = await Promise.all([listTenantChannels(tenantId, token), listChannelAccounts(tenantId, token)]);
      setChannelAccountState({
        status: "ready",
        channels,
        accounts
      });
      setChannelIdentityById(buildChannelIdentityFromAccounts(accounts));
    } catch (error) {
      const message = error instanceof Error ? error.message : "无法读取渠道账号配置";
      setChannelAccountState((current) => ({
        status: "error",
        message,
        channels: current.channels,
        accounts: current.accounts
      }));
      setChannelIdentityById({});
    }
  }

  async function refreshAccountManagement(tenantId: string, token: string) {
    setAccountManagement((current) => ({
      status: "loading",
      users: current.users,
      roles: current.roles
    }));
    try {
      const [users, roles] = await Promise.all([listTenantUsers(tenantId, token), listTenantRoles(tenantId, token)]);
      setAccountManagement({
        status: "ready",
        message: "账号信息已同步",
        users: users.map(normalizeAccountUser),
        roles
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : "无法读取本地账号与角色";
      setAccountManagement((current) => ({
        status: "error",
        message,
        users: current.users,
        roles: current.roles
      }));
    }
  }

  async function refreshSignedUpdatePackages(tenantId: string, token: string) {
    setSignedUpdateStage((current) => ({
      status: "loading",
      message: "正在同步暂存更新包",
      packages: current.packages
    }));
    try {
      const packages = await listStagedSignedUpdatePackages(tenantId, token);
      setSignedUpdateStage({
        status: "ready",
        message: packages.length > 0 ? "暂存更新包已同步" : "当前没有暂存更新包",
        packages
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : "无法读取暂存更新包";
      setSignedUpdateStage((current) => ({
        status: "error",
        message,
        packages: current.packages
      }));
    }
  }

  async function refreshLocalBackups(tenantId: string, token: string) {
    setLocalBackupState((current) => ({
      status: "loading",
      message: "正在同步本地备份点",
      backups: current.backups
    }));
    try {
      const backups = await listLocalBackups(tenantId, token);
      setLocalBackupState({
        status: "ready",
        message: backups.length > 0 ? "本地备份点已同步" : "当前还没有本地备份点",
        backups
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : "无法读取本地备份点";
      setLocalBackupState((current) => ({
        status: "error",
        message,
        backups: current.backups
      }));
    }
  }

  async function refreshLocalMaintenanceReadiness(tenantId: string, token: string) {
    setLocalMaintenanceReadiness((current) => ({
      status: "loading",
      message: "正在同步本地维护闭环",
      data: current.data
    }));
    try {
      const data = await getLocalMaintenanceReadiness(tenantId, token);
      setLocalMaintenanceReadiness({
        status: "ready",
        message: data.ready_for_customer_maintenance_rehearsal ? "本地维护闭环具备演练证据" : "本地维护闭环仍缺少证据",
        data
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : "无法读取本地维护闭环";
      setLocalMaintenanceReadiness((current) => ({
        status: "error",
        message,
        data: current.data
      }));
    }
  }

  async function refreshDiagnosticIntakes(tenantId: string, token: string) {
    setDiagnosticIntake((current) => ({
      status: "loading",
      message: "正在同步售后接收记录",
      records: current.records
    }));
    try {
      const result = await listDiagnosticIntakeRecords(tenantId, token);
      setDiagnosticIntake({
        status: "ready",
        message: result.items.length > 0 ? "售后接收记录已同步" : "当前还没有接收记录",
        records: result.items
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : "无法读取售后接收记录";
      setDiagnosticIntake((current) => ({
        status: "error",
        message,
        records: current.records
      }));
    }
  }

  async function refreshDiagnosticRemediations(tenantId: string, token: string) {
    setDiagnosticRemediation((current) => ({
      status: "loading",
      message: "正在同步售后处理单",
      requests: current.requests
    }));
    try {
      const result = await listDiagnosticRemediationRequests(tenantId, token);
      setDiagnosticRemediation({
        status: "ready",
        message: result.items.length > 0 ? "售后处理单已同步" : "当前还没有处理单",
        requests: result.items
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : "无法读取售后处理单";
      setDiagnosticRemediation((current) => ({
        status: "error",
        message,
        requests: current.requests
      }));
    }
  }

  useEffect(() => {
    if (isDemoPreviewRequested()) {
      void enterDemo();
      return;
    }
    const storedToken = window.localStorage.getItem(TOKEN_STORAGE_KEY);
    if (!storedToken) {
      setConnection({ status: "error", error: "尚未登录" });
      setAuth({ status: "login" });
      void refreshLocalSetupState();
      return;
    }
    void refreshConnection(storedToken, "token");
  }, []);

  useEffect(() => {
    const syncActiveSection = () => {
      const currentHash = window.location.hash;
      const requestedSection = getWorkspaceSectionFromHash(currentHash);
      const nextSection =
        auth.status === "ready"
          ? getAccessibleWorkspaceSection(requestedSection, visibleNavigationGroups, defaultWorkspaceSection)
          : requestedSection;
      if (nextSection !== requestedSection) {
        window.history.replaceState(null, "", getWorkspaceSectionHash(nextSection));
      }
      const nextTaskContext = nextSection === requestedSection ? parseWorkspaceTaskContext(currentHash) : null;
      setWorkspaceHash(currentHash);
      setActiveSection(nextSection);
      setOverviewTaskContext(nextTaskContext && nextTaskContext.targetSection === nextSection ? nextTaskContext : null);
      if (workspaceRef.current && window.matchMedia("(min-width: 721px)").matches) {
        workspaceRef.current.scrollTo({ top: 0, behavior: "auto" });
      } else {
        window.scrollTo({ top: 0, behavior: "auto" });
      }
    };
    syncActiveSection();
    window.addEventListener("hashchange", syncActiveSection);
    return () => window.removeEventListener("hashchange", syncActiveSection);
  }, [auth.status, defaultWorkspaceSection, navigationRoleKey, visibleNavigationGroups]);

  useEffect(() => {
    const activeGroup = visibleNavigationGroups.find((group) =>
      group.items.some((item) => getWorkspaceSectionFromHash(item.href) === activeSection)
    );
    if (!activeGroup || activeGroup.items.length <= 1) {
      return;
    }
    setExpandedNavGroups((current) =>
      current[activeGroup.label] ? current : { ...current, [activeGroup.label]: true }
    );
  }, [activeSection, navigationRoleKey, visibleNavigationGroups]);

  const overviewTaskContextKey = overviewTaskContext
    ? [
        overviewTaskContext.targetSection,
        overviewTaskContext.task,
        overviewTaskContext.range,
        overviewTaskContext.channelId ?? "all",
        overviewTaskContext.status ?? "",
        overviewTaskContext.queue ?? ""
      ].join("|")
    : "";

  useEffect(() => {
    if (!overviewTaskContext || overviewTaskContext.targetSection !== activeSection) {
      return;
    }
    if (overviewTaskContext.targetSection === "reviews" && overviewTaskContext.status) {
      setReviewListView((current) => ({
        ...current,
        status: overviewTaskContext.status ?? current.status,
        page: 1
      }));
    }
    if (overviewTaskContext.targetSection === "outbox" && overviewTaskContext.status) {
      setOutboxListView((current) => ({
        ...current,
        status: overviewTaskContext.status ?? current.status,
        page: 1
      }));
    }
    if (overviewTaskContext.targetSection === "gaps" && overviewTaskContext.status) {
      setKnowledgeGapListView((current) => ({
        ...current,
        status: overviewTaskContext.status ?? current.status,
        page: 1
      }));
    }
    if (overviewTaskContext.targetSection === "channels" && overviewTaskContext.status) {
      setFailureListView((current) => ({
        ...current,
        status: overviewTaskContext.status ?? current.status,
        page: 1
      }));
    }
  }, [activeSection, overviewTaskContextKey]);

  async function refreshOutbox(tenantId: string, token: string) {
    setOutbox((current) => ({
      status: "loading",
      drafts: "drafts" in current ? current.drafts : [],
      attemptsByDraft: "attemptsByDraft" in current ? current.attemptsByDraft : {}
    }));
    try {
      const drafts = (await listOutboxDrafts(tenantId, token)).filter((draft) =>
        ["pending_confirmation", "ready_to_send"].includes(draft.status)
      );
      const attemptPairs = await Promise.all(
        drafts.map(async (draft) => [draft.id, await listOutboxSendAttempts(draft.id, token)] as const)
      );
      setOutbox({
        status: "ready",
        drafts,
        attemptsByDraft: Object.fromEntries(attemptPairs)
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : "无法读取待发送草稿";
      setOutbox({
        status: "error",
        message,
        drafts: [],
        attemptsByDraft: {}
      });
    }
  }

  async function refreshReviewInbox(tenantId: string, token: string) {
    setReviewInbox((current) => ({
      status: "loading",
      items: "items" in current ? current.items : []
    }));
    try {
      const items = await listHumanReviewInbox(tenantId, token);
      setReviewInbox({ status: "ready", items });
    } catch (error) {
      const message = error instanceof Error ? error.message : "无法读取人工审核收件箱";
      setReviewInbox({ status: "error", message, items: [] });
    }
  }

  async function refreshReplyDecisions(tenantId: string, token: string) {
    setReplyDecisionState((current) => ({
      status: "loading",
      items: "items" in current ? current.items : []
    }));
    try {
      const data = await listReplyDecisions(tenantId, token, { page_size: 100 });
      setReplyDecisionState({ status: "ready", items: data.items });
    } catch (error) {
      const message = error instanceof Error ? error.message : "无法读取回复决策";
      setReplyDecisionState({ status: "error", message, items: [] });
    }
  }

  async function refreshConversationInbox(
    tenantId: string,
    token: string,
    view: ListViewState = conversationInboxView,
    filters: ConversationInboxFilters = conversationInboxFilters,
    options: { silent?: boolean } = {}
  ) {
    if (!options.silent) {
      setConversationInbox((current) => ({
        status: "loading",
        data: current.data
      }));
    }
    try {
      const data = await listConversationInbox(tenantId, token, {
        status: view.status,
        query: view.query,
        page: view.page,
        page_size: view.pageSize,
        assigned: filters.assigned,
        sla: filters.sla,
        sort: filters.sort,
        priority: filters.priority,
        channel_id: filters.channelId ?? null
      });
      setConversationInbox({ status: "ready", data: filterLocallyClosedConversations(data) });
    } catch (error) {
      const message = error instanceof Error ? error.message : "无法读取会话收件箱";
      setConversationInbox((current) => ({
        status: "error",
        message,
        data: current.data
      }));
    }
  }

  function filterLocallyClosedConversations(data: ConversationInboxList): ConversationInboxList {
    if (locallyClosedConversationIds.size === 0) {
      return data;
    }
    const items = data.items.filter((item) => !locallyClosedConversationIds.has(item.id));
    return {
      ...data,
      items,
      total: Math.max(0, data.total - (data.items.length - items.length))
    };
  }

  function hideConversationLocally(conversationId: number) {
    setLocallyClosedConversationIds((current) => {
      const next = new Set(current);
      next.add(conversationId);
      return next;
    });
    setConversationInbox((current) => {
      const removed = current.data.items.some((conversation) => conversation.id === conversationId);
      return {
        ...current,
        data: {
          ...current.data,
          total: Math.max(0, current.data.total - (removed ? 1 : 0)),
          items: current.data.items.filter((conversation) => conversation.id !== conversationId)
        }
      };
    });
    if (selectedLiveConversationId === conversationId) {
      setSelectedLiveConversationId(null);
    }
  }

  async function refreshConversationDetail(
    conversationId: number,
    token: string,
    options: { silent?: boolean } = {}
  ) {
    if (!options.silent) {
      setConversationDetail((current) => ({
        status: "loading",
        message: "正在读取当前会话消息",
        data: current.data?.id === conversationId ? current.data : null
      }));
    }
    try {
      const data = await getConversationDetail(conversationId, token);
      setConversationDetail({
        status: "ready",
        message: "当前会话消息已同步",
        data
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : "无法读取当前会话消息";
      setConversationDetail((current) => ({
        status: "error",
        message,
        data: current.data?.id === conversationId ? current.data : null
      }));
    }
  }

  async function handleSendLocalConversationReply(item: ConversationInboxItem, content: string) {
    const trimmed = content.trim();
    if (!trimmed) {
      setLocalReplyState({
        status: "error",
        conversationId: item.id,
        message: "回复内容不能为空"
      });
      return;
    }
    if (auth.status === "ready" && auth.mode === "demo") {
      setLocalReplyState({
        status: "sent",
        conversationId: item.id,
        message: "预览模式已模拟发送：仅更新界面提示，未写入后端，也未发送到外部平台。"
      });
      return;
    }
    if (auth.status !== "ready" || !auth.token || !canManageConversations(auth.user)) {
      setLocalReplyState({
        status: "error",
        conversationId: item.id,
        message: "当前账号没有写入本地会话的权限"
      });
      return;
    }
    setLocalReplyState({
      status: "sending",
      conversationId: item.id,
      message: item.channel_type === "website" ? "正在发送到网站访客" : "正在写入本地会话记录"
    });
    try {
      await createAgentReply(item.id, auth.token, { content: trimmed });
      await refreshConversationDetail(item.id, auth.token);
      await refreshConversationInbox(auth.user.tenant.id, auth.token, conversationInboxView, conversationInboxFilters);
      setLocalReplyState({
        status: "sent",
        conversationId: item.id,
        message: item.channel_type === "website" ? "已发送到网站访客。" : "已写入本地会话，未发送到外部平台。"
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : "本地会话写入失败";
      setLocalReplyState({
        status: "error",
        conversationId: item.id,
        message
      });
    }
  }

  async function refreshSupportTickets(
    tenantId: string,
    token: string,
    view: ListViewState = supportTicketListView,
    filters: SupportTicketFilters = supportTicketFilters
  ) {
    setSupportTickets((current) => ({
      status: "loading",
      data: current.data
    }));
    try {
      const data = await listSupportTickets(tenantId, token, {
        status: view.status,
        query: view.query,
        page: view.page,
        page_size: view.pageSize,
        assigned: filters.assigned,
        sla: filters.sla,
        priority: filters.priority
      });
      setSupportTickets({ status: "ready", data });
    } catch (error) {
      const message = error instanceof Error ? error.message : "无法读取工单列表";
      setSupportTickets((current) => ({
        status: "error",
        message,
        data: current.data
      }));
    }
  }

  async function refreshContactProfiles(
    tenantId: string,
    token: string,
    view: ListViewState = contactProfileListView,
    selectedContactId?: number | null
  ) {
    setContactProfiles((current) => ({
      status: "loading",
      data: current.data,
      detail: current.detail
    }));
    try {
      const data = await listContactProfiles(tenantId, token, {
        query: view.query,
        page: view.page,
        page_size: view.pageSize
      });
      const detailId = selectedContactId ?? contactProfiles.detail?.id ?? data.items[0]?.id ?? null;
      const detail = detailId ? await getContactProfile(detailId, token) : null;
      setContactProfiles({ status: "ready", data, detail });
    } catch (error) {
      const message = error instanceof Error ? error.message : "无法读取联系人画像";
      setContactProfiles((current) => ({
        status: "error",
        message,
        data: current.data,
        detail: current.detail
      }));
    }
  }

  async function refreshSalesLeads(
    tenantId: string,
    token: string,
    view: ListViewState = salesLeadListView,
    filters: SalesLeadFilters = salesLeadFilters
  ) {
    setSalesLeads((current) => ({
      status: "loading",
      data: current.data
    }));
    try {
      const data = await listSalesLeads(tenantId, token, {
        stage: view.status,
        intent: filters.intent,
        owner: filters.owner,
        query: view.query,
        page: view.page,
        page_size: view.pageSize
      });
      setSalesLeads({ status: "ready", data });
    } catch (error) {
      const message = error instanceof Error ? error.message : "无法读取线索列表";
      setSalesLeads((current) => ({
        status: "error",
        message,
        data: current.data
      }));
    }
  }

  async function refreshFailureReviews(tenantId: string, token: string) {
    setFailureReviews((current) => ({
      status: "loading",
      items: "items" in current ? current.items : []
    }));
    try {
      const items = await listDeliveryFailureReviews(tenantId, token);
      setFailureReviews({ status: "ready", items });
    } catch (error) {
      const message = error instanceof Error ? error.message : "无法读取失败复盘队列";
      setFailureReviews({ status: "error", message, items: [] });
    }
  }

  async function refreshDeliveryQueue(tenantId: string, token: string) {
    setDeliveryQueue((current) => ({
      status: "loading",
      jobs: "jobs" in current ? current.jobs : []
    }));
    try {
      const jobs = await listOutboxDeliveryJobs(tenantId, token);
      setDeliveryQueue({ status: "ready", jobs });
    } catch (error) {
      const message = error instanceof Error ? error.message : "无法读取发送队列";
      setDeliveryQueue({ status: "error", message, jobs: [] });
    }
  }

  async function refreshBusinessOpsDashboard(
    tenantId: string,
    token: string,
    params: { range?: OpsRangeKey; channel_id?: number | null } = {}
  ) {
    setBusinessOpsDashboard((current) => ({
      status: "loading",
      data: current.data
    }));
    try {
      const data = await getBusinessOpsDashboard(tenantId, token, {
        range: params.range ?? "today",
        channel_id: params.channel_id ?? null
      });
      setBusinessOpsDashboard({ status: "ready", data });
    } catch (error) {
      const message = error instanceof Error ? error.message : "无法读取运营总览";
      setBusinessOpsDashboard((current) => ({
        status: "error",
        message,
        data: current.data
      }));
    }
  }

  async function refreshOpsWorkerHealth(tenantId: string, token: string) {
    setOpsWorkerHealth((current) => ({
      status: "loading",
      data: current.data
    }));
    try {
      const data = await getWorkerHealthDashboard(tenantId, token, {
        stale_after_seconds: 120,
        recent_run_limit: 10
      });
      setOpsWorkerHealth({ status: "ready", data });
    } catch (error) {
      const message = error instanceof Error ? error.message : "无法读取后台进程健康状态";
      setOpsWorkerHealth((current) => ({
        status: "error",
        message,
        data: current.data
      }));
    }
  }

  async function refreshOpsAlertRules(tenantId: string, token: string) {
    setOpsAlertRules((current) => ({
      status: "loading",
      data: current.data
    }));
    try {
      const data = await getOpsAlertRulesDashboard(tenantId, token, {
        stale_after_seconds: 120,
        recent_run_limit: 10
      });
      setOpsAlertRules({ status: "ready", data });
    } catch (error) {
      const message = error instanceof Error ? error.message : "无法读取告警规则评估";
      setOpsAlertRules((current) => ({
        status: "error",
        message,
        data: current.data
      }));
    }
  }

  async function refreshOpsMetrics(tenantId: string, token: string) {
    setOpsMetrics((current) => ({
      status: "loading",
      data: current.data
    }));
    try {
      const data = await getOpsMetricsDashboard(tenantId, token, {
        stale_after_seconds: 120,
        recent_run_limit: 10
      });
      setOpsMetrics({ status: "ready", data });
    } catch (error) {
      const message = error instanceof Error ? error.message : "无法读取指标出口";
      setOpsMetrics((current) => ({
        status: "error",
        message,
        data: current.data
      }));
    }
  }

  async function refreshKnowledgeDocuments(tenantId: string, token: string, includePublicationHistory = false) {
    setKnowledgeWorkbench((current) => ({
      ...current,
      status: "loading",
      message: ""
    }));
    try {
      const [documentList, businessObjectList] = await Promise.all([
        listKnowledgeDocuments(tenantId, token),
        listBusinessObjects(tenantId, token, { status: "active" })
      ]);
      const previewDocuments = documentList.items.slice(0, 5);
      const previewBusinessObjects = businessObjectList.items.slice(0, 5);
      const chunkPairs = await Promise.all(
        previewDocuments.slice(0, 3).map(async (document) => [document.id, await listKnowledgeDocumentChunks(document.id, token)] as const)
      );
      const objectCardPairs = await Promise.all(
        previewBusinessObjects.map(async (item) => [item.id, (await listObjectKnowledgeCards(item.id, token, { status: "active" })).items] as const)
      );
      const publicationPairs = includePublicationHistory
        ? await Promise.all(
            previewDocuments.map(async (document) => {
              const publicationList = await listKnowledgeDocumentPublications(document.id, token);
              return [document.id, publicationList.items] as const;
            })
          )
        : [];
      setKnowledgeWorkbench((current) => ({
        status: "ready",
        message: "",
        businessObjects: businessObjectList.items,
        objectCardsByObject: {
          ...current.objectCardsByObject,
          ...Object.fromEntries(objectCardPairs)
        },
        documents: documentList.items,
        chunksByDocument: {
          ...current.chunksByDocument,
          ...Object.fromEntries(chunkPairs)
        },
        publicationsByDocument: includePublicationHistory
          ? {
              ...current.publicationsByDocument,
              ...Object.fromEntries(publicationPairs)
            }
          : {},
        searchResult: current.searchResult
      }));
    } catch (error) {
      const message = error instanceof Error ? error.message : "无法读取知识文档";
      setKnowledgeWorkbench((current) => ({
        ...current,
        status: "error",
        message,
        businessObjects: [],
        objectCardsByObject: {},
        documents: [],
        publicationsByDocument: {}
      }));
    }
  }

  async function refreshKnowledgeMemoryMeshOverview(tenantId: string, token: string) {
    setKnowledgeMemoryMesh((current) => ({
      status: "loading",
      message: "",
      data: current.data
    }));
    try {
      const data = await getKnowledgeMemoryMeshOverview(tenantId, token);
      setKnowledgeMemoryMesh({
        status: "ready",
        message: data.summary,
        data
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : "无法读取知识网络总览";
      setKnowledgeMemoryMesh((current) => ({
        status: "error",
        message,
        data: current.data
      }));
    }
  }

  async function refreshTenantReplyStrategy(tenantId: string, token: string) {
    setTenantReplyStrategy((current) => ({
      ...current,
      status: "loading",
      message: ""
    }));
    try {
      const data = await getTenantReplyStrategy(tenantId, token);
      setTenantReplyStrategy({
        status: "ready",
        message: data.status === "active" ? "已读取自动回复策略" : "当前尚未配置自动回复策略",
        data
      });
      setReplyStrategyDraft({
        blockedPolicyTerms: data.reply_policy.blocked_policy_terms.join("，"),
        manualReviewTerms: data.reply_policy.manual_review_terms.join("，"),
        forceDraftOnly: data.reply_policy.force_draft_only
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : "无法读取自动回复策略";
      setTenantReplyStrategy({
        status: "error",
        message,
        data: null
      });
    }
  }

  async function refreshRagCostGovernance(tenantId: string, token: string) {
    setRagCostGovernance((current) => ({
      ...current,
      status: "loading",
      message: ""
    }));
    try {
      const data = await getRagCostGovernanceSummary(tenantId, token);
      setRagCostGovernance({
        status: "ready",
        message: data.summary,
        data
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : "无法读取检索与成本治理状态";
      setRagCostGovernance({
        status: "error",
        message,
        data: null
      });
    }
  }

  async function refreshLlmOpsReadiness(tenantId: string, token: string) {
    setLlmOpsReadiness((current) => ({
      ...current,
      status: "loading",
      message: ""
    }));
    try {
      const data = await getLlmOpsReadinessSummary(tenantId, token);
      setLlmOpsReadiness({
        status: "ready",
        message: data.summary,
        data
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : "无法读取模型观测与安全状态";
      setLlmOpsReadiness({
        status: "error",
        message,
        data: null
      });
    }
  }

  async function refreshAiServiceStatus(tenantId: string, token: string) {
    setAiServiceStatus((current) => ({
      ...current,
      status: "loading",
      message: ""
    }));
    try {
      const data = await getAiServiceStatus(tenantId, token);
      setAiServiceStatus({
        status: "ready",
        message: data.customer_visible_detail || data.label,
        data
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : "无法读取 AI 服务状态";
      setAiServiceStatus({
        status: "error",
        message,
        data: null
      });
    }
  }

  async function refreshKnowledgeEvaluations(tenantId: string, token: string, canReadRuns: boolean) {
    setKnowledgeEvaluation((current) => ({
      ...current,
      status: "loading",
      message: ""
    }));
    try {
      const evaluationSets = await listKnowledgeEvaluationSets(tenantId, token);
      const runEntries = canReadRuns
        ? await Promise.all(
            evaluationSets.items.map(async (item) => {
              const runs = await listKnowledgeEvaluationRuns(item.id, token);
              return [item.id, runs.items] as const;
            })
          )
        : [];
      setKnowledgeEvaluation((current) => ({
        status: "ready",
        message: "",
        sets: evaluationSets.items,
        lastRun: current.lastRun,
        runsBySet: Object.fromEntries(runEntries)
      }));
    } catch (error) {
      const message = error instanceof Error ? error.message : "无法读取知识评测集";
      setKnowledgeEvaluation((current) => ({
        ...current,
        status: "error",
        message,
        sets: [],
        runsBySet: {}
      }));
    }
  }

  async function refreshMonthlyQualityReview(tenantId: string, token: string) {
    setMonthlyQualityReview((current) => ({
      ...current,
      status: "loading",
      message: ""
    }));
    try {
      const data = await getMonthlyQualityReview(tenantId, token);
      setMonthlyQualityReview({
        status: "ready",
        message: "",
        data
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : "无法读取月度质量复盘";
      setMonthlyQualityReview({
        status: "error",
        message,
        data: null
      });
    }
  }

  async function refreshMonthlyOpsReport(tenantId: string, token: string) {
    setMonthlyOpsReport((current) => ({
      ...current,
      status: "loading",
      message: ""
    }));
    try {
      const data = await getMonthlyOpsReport(tenantId, token);
      setMonthlyOpsReport({
        status: "ready",
        message: "",
        data
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : "无法读取月度运维报告";
      setMonthlyOpsReport({
        status: "error",
        message,
        data: null
      });
    }
  }

  async function refreshPilotReadiness(tenantId: string, token: string) {
    setPilotReadiness((current) => ({
      ...current,
      status: "loading",
      message: ""
    }));
    try {
      const data = await getPilotReadiness(tenantId, token);
      setPilotReadiness({
        status: "ready",
        message: data.summary,
        data
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : "无法读取试点准备状态";
      setPilotReadiness({
        status: "error",
        message,
        data: null
      });
    }
  }

  async function refreshCustomerMaterialBatches(tenantId: string, token: string) {
    setCustomerMaterialBatches((current) => ({
      ...current,
      status: "loading",
      message: "正在读取资料批次"
    }));
    try {
      const data = await getCustomerMaterialBatches(tenantId, token);
      setCustomerMaterialBatches({
        status: "ready",
        message: data.summary,
        data
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : "无法读取资料批次";
      setCustomerMaterialBatches({
        status: "error",
        message,
        data: null
      });
    }
  }

  async function handleImportKnowledgeConfirmation(filename: string, csvText: string) {
    if (auth.status !== "ready" || !auth.token || !hasKnowledgeManagePermission(auth.user)) {
      setKnowledgeConfirmationImport({
        status: "error",
        message: "当前账号没有导入确认表权限。",
        result: null
      });
      return;
    }
    setKnowledgeConfirmationImport((current) => ({
      ...current,
      status: "loading",
      message: "正在校验客户确认表"
    }));
    try {
      const result = await importKnowledgeConfirmationCsv(auth.user.tenant.id, auth.token, {
        filename,
        csv_text: csvText
      });
      setKnowledgeConfirmationImport({
        status: "ready",
        message: result.summary,
        result
      });
      await refreshPilotReadiness(auth.user.tenant.id, auth.token);
    } catch (error) {
      const message = error instanceof Error ? error.message : "客户确认表导入失败";
      setKnowledgeConfirmationImport({
        status: "error",
        message,
        result: null
      });
    }
  }

  async function handleLoadCustomerMaterialTemplatePackage() {
    if (auth.status !== "ready" || !auth.token || !hasKnowledgeManagePermission(auth.user)) {
      setCustomerMaterialTemplatePackage({
        status: "error",
        message: "当前账号没有资料模板权限。",
        data: null
      });
      return;
    }
    setCustomerMaterialTemplatePackage((current) => ({
      ...current,
      status: "loading",
      message: "正在加载资料模板"
    }));
    try {
      const data = await getCustomerMaterialTemplatePackage(auth.user.tenant.id, auth.token);
      setCustomerMaterialTemplatePackage({
        status: "ready",
        message: data.summary,
        data
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : "资料模板加载失败";
      setCustomerMaterialTemplatePackage({
        status: "error",
        message,
        data: null
      });
    }
  }

  async function handleDownloadCustomerMaterialHandoffBundle() {
    if (auth.status !== "ready" || !auth.token || !hasKnowledgeManagePermission(auth.user)) {
      setCustomerMaterialHandoffBundle({
        status: "error",
        message: "当前账号没有资料回传包权限。",
        data: null
      });
      return;
    }
    setCustomerMaterialHandoffBundle((current) => ({
      ...current,
      status: "loading",
      message: "正在生成资料回传包"
    }));
    try {
      const data = await getCustomerMaterialHandoffBundle(auth.user.tenant.id, auth.token);
      if (data.body_encoding === "base64") {
        downloadBinaryFile(decodeBase64ToBytes(data.body), data.filename, data.content_type);
      } else {
        downloadTextFile(data.body, data.filename, data.content_type);
      }
      setCustomerMaterialHandoffBundle({
        status: "ready",
        message: data.summary,
        data
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : "资料回传包生成失败";
      setCustomerMaterialHandoffBundle({
        status: "error",
        message,
        data: null
      });
    }
  }

  async function handlePrecheckCustomerMaterials(materialsCsv: string, questionsCsv: string, manifestJson: string) {
    if (auth.status !== "ready" || !auth.token || !hasKnowledgeManagePermission(auth.user)) {
      setCustomerMaterialPrecheck({
        status: "error",
        message: "当前账号没有资料预检权限。",
        result: null
      });
      return;
    }
    setCustomerMaterialPrecheck((current) => ({
      ...current,
      status: "loading",
      message: "正在预检资料包"
    }));
    try {
      const result = await precheckCustomerMaterialPackage(auth.user.tenant.id, auth.token, {
        materials_csv: materialsCsv,
        trial_questions_csv: questionsCsv,
        manifest_json: manifestJson
      });
      setCustomerMaterialPrecheck({
        status: "ready",
        message: result.summary,
        result
      });
      await refreshPilotReadiness(auth.user.tenant.id, auth.token);
      await refreshCustomerMaterialBatches(auth.user.tenant.id, auth.token);
    } catch (error) {
      const message = error instanceof Error ? error.message : "资料包预检失败";
      setCustomerMaterialPrecheck({
        status: "error",
        message,
        result: null
      });
    }
  }

  async function refreshOnlineReceiptQuality(tenantId: string, token: string) {
    setOnlineReceiptQuality((current) => ({
      ...current,
      status: "loading",
      message: ""
    }));
    try {
      const data = await getOnlineReceiptQualitySummary(tenantId, token);
      setOnlineReceiptQuality({
        status: "ready",
        message: "已同步线上回执闭环口径",
        data
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : "无法读取线上回执闭环";
      setOnlineReceiptQuality((current) => ({
        status: "error",
        message,
        data: current.data
      }));
    }
  }

  async function refreshCustomerQualityReport(tenantId: string, token: string) {
    setCustomerQualityReport((current) => ({
      ...current,
      status: "loading",
      message: ""
    }));
    try {
      const data = await getCustomerQualityReport(tenantId, token);
      setCustomerQualityReport({
        status: "ready",
        message: "",
        data
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : "无法读取客户质量报告";
      setCustomerQualityReport({
        status: "error",
        message,
        data: null
      });
    }
  }

  async function refreshCustomerQualityReportSignoffs(tenantId: string, token: string) {
    setCustomerQualityReportSignoffs((current) => ({
      ...current,
      status: "loading",
      message: ""
    }));
    try {
      const data = await listCustomerQualityReportSignoffs(tenantId, token, { page: 1, pageSize: 8 });
      setCustomerQualityReportSignoffs({
        status: "ready",
        message: data.total > 0 ? `已同步 ${data.total} 条客户确认记录` : "当前还没有客户确认记录",
        data
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : "无法读取客户确认记录";
      setCustomerQualityReportSignoffs({
        status: "error",
        message,
        data: null
      });
    }
  }

  async function refreshCustomerQualityReportArchives(tenantId: string, token: string, period?: string) {
    setCustomerQualityReportArchives((current) => ({
      ...current,
      status: "loading",
      message: ""
    }));
    try {
      const data = await listCustomerQualityReportArchives(tenantId, token, { page: 1, pageSize: 8, period });
      setCustomerQualityReportArchives({
        status: "ready",
        message: data.total > 0 ? `已归档 ${data.total} 份报告文件` : "当前还没有报告归档文件",
        data
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : "无法读取客户报告归档";
      setCustomerQualityReportArchives({
        status: "error",
        message,
        data: null
      });
    }
  }

  async function handleExportCustomerQualityReport(format: "html" | "xlsx" | "docx") {
    if (auth.status !== "ready" || !auth.token || !canReadQualityReview(auth.user)) {
      return;
    }
    setCustomerQualityReport((current) => ({
      ...current,
      status: current.data ? "ready" : "loading",
      message: "正在生成客户质量报告留档"
    }));
    try {
      const report = await exportCustomerQualityReport(auth.user.tenant.id, auth.token, { format });
      downloadCustomerQualityReportFile(report);
      void refreshCustomerQualityReportArchives(auth.user.tenant.id, auth.token, report.period);
      setCustomerQualityReport((current) => ({
        ...current,
        status: "ready",
        message: `已导出 ${report.filename} 并写入本地归档；这不是正式电子签章。`
      }));
    } catch (error) {
      const message = error instanceof Error ? error.message : "导出客户质量报告失败";
      setCustomerQualityReport((current) => ({
        ...current,
        status: "error",
        message
      }));
    }
  }

  async function handleDownloadCustomerQualityReportArchive(archiveEventId: number) {
    if (auth.status !== "ready" || !auth.token || !canReadQualityReview(auth.user)) {
      return;
    }
    setCustomerQualityReportArchives((current) => ({
      ...current,
      status: current.data ? "ready" : "loading",
      message: "正在下载历史报告归档"
    }));
    try {
      const report = await downloadCustomerQualityReportArchive(auth.user.tenant.id, auth.token, archiveEventId);
      downloadCustomerQualityReportFile(report);
      setCustomerQualityReportArchives((current) => ({
        ...current,
        status: "ready",
        message: `已下载 ${report.filename}；归档仍是本地留档，不是正式电子签章。`
      }));
    } catch (error) {
      const message = error instanceof Error ? error.message : "下载历史报告归档失败";
      setCustomerQualityReportArchives((current) => ({
        ...current,
        status: "error",
        message
      }));
    }
  }

  async function handleRecordCustomerQualityReportSignoff(payload: CustomerQualityReportSignoffCreate) {
    if (auth.status !== "ready" || !auth.token || !canManageAccounts(auth.user)) {
      return;
    }
    setCustomerQualityReport((current) => ({
      ...current,
      status: current.data ? "ready" : "loading",
      message: "正在记录客户确认结果"
    }));
    try {
      const signoff = await recordCustomerQualityReportSignoff(auth.user.tenant.id, auth.token, payload);
      void refreshCustomerQualityReportSignoffs(auth.user.tenant.id, auth.token);
      setCustomerQualityReport((current) => ({
        ...current,
        status: "ready",
        message: `已记录 ${signoff.period} 客户确认：${signoff.signoff_status_label}，签收人 ${signoff.signer_display_name}。`
      }));
    } catch (error) {
      const message = error instanceof Error ? error.message : "记录客户确认结果失败";
      setCustomerQualityReport((current) => ({
        ...current,
        status: "error",
        message
      }));
    }
  }

  async function refreshKnowledgeGaps(tenantId: string, token: string, view: ListViewState = knowledgeGapListView) {
    setKnowledgeGaps((current) => ({
      ...current,
      status: "loading",
      message: ""
    }));
    try {
      const data = await listKnowledgeGaps(tenantId, token, {
        ...knowledgeGapListParams(view)
      });
      setKnowledgeGaps((current) => ({
        status: "ready",
        message: current.lastSync
          ? `最近同步：新增 ${current.lastSync.created_count} 条，已存在 ${current.lastSync.existing_count} 条`
          : "",
        data,
        lastSync: current.lastSync
      }));
    } catch (error) {
      const message = error instanceof Error ? error.message : "无法读取知识缺口";
      setKnowledgeGaps((current) => ({
        ...current,
        status: "error",
        message
      }));
    }
  }

  function resetUnavailableWorkspaceResources(user: CurrentUser) {
    if (!canReadConversations(user)) {
      setConversationInbox({
        status: "idle",
        message: NO_PERMISSION_MESSAGE,
        data: EMPTY_CONVERSATION_INBOX
      });
      setConversationDetail({
        status: "idle",
        message: NO_PERMISSION_MESSAGE,
        data: null
      });
      setLocalReplyState({
        status: "idle",
        conversationId: null,
        message: NO_PERMISSION_MESSAGE
      });
      setReviewInbox({ status: "idle", message: NO_PERMISSION_MESSAGE });
      setReplyDecisionState({ status: "idle", message: NO_PERMISSION_MESSAGE, items: [] });
      setLastInboundWorkerRun(null);
      setSelectedReviewId(null);
    }
    if (!canReadTickets(user)) {
      setSupportTickets({
        status: "idle",
        message: NO_PERMISSION_MESSAGE,
        data: EMPTY_SUPPORT_TICKET_LIST
      });
    }
    if (!canReadCustomers(user)) {
      setContactProfiles({
        status: "idle",
        message: NO_PERMISSION_MESSAGE,
        data: EMPTY_CONTACT_PROFILE_LIST,
        detail: null
      });
    }
    if (!canReadLeads(user)) {
      setSalesLeads({
        status: "idle",
        message: NO_PERMISSION_MESSAGE,
        data: EMPTY_SALES_LEAD_LIST
      });
    }
    if (!canReadOutboxDrafts(user)) {
      setOutbox({ status: "idle", message: NO_PERMISSION_MESSAGE });
      setLastWorkerRun(null);
    }
    if (!canReadOutboxDeliveryJobs(user)) {
      setDeliveryQueue({ status: "idle", message: NO_PERMISSION_MESSAGE });
      setLastDeliveryQueueRun(null);
    }
    if (!canReadFailureReviews(user)) {
      setFailureReviews({ status: "idle", message: NO_PERMISSION_MESSAGE });
    }
    if (!canReadChannels(user)) {
      setChannelIdentityById({});
      setChannelAccountState({
        status: "idle",
        message: NO_PERMISSION_MESSAGE,
        channels: [],
        accounts: []
      });
    }
    if (!canReadDashboard(user)) {
      setBusinessOpsDashboard({ status: "idle", message: NO_PERMISSION_MESSAGE, data: null });
    }
    if (!canReadOpsWorkerHealth(user)) {
      setOpsWorkerHealth({ status: "idle", message: NO_PERMISSION_MESSAGE, data: null });
    }
    if (!canReadOpsAlertRules(user)) {
      setOpsAlertRules({ status: "idle", message: NO_PERMISSION_MESSAGE, data: null });
    }
    if (!canReadOpsMetrics(user)) {
      setOpsMetrics({ status: "idle", message: NO_PERMISSION_MESSAGE, data: null });
      setDiagnosticExport({ status: "idle", message: NO_PERMISSION_MESSAGE });
      setRagCostGovernance({ status: "idle", message: NO_PERMISSION_MESSAGE, data: null });
      setLlmOpsReadiness({ status: "idle", message: NO_PERMISSION_MESSAGE, data: null });
      setMonthlyOpsReport({ status: "idle", message: NO_PERMISSION_MESSAGE, data: null });
    }
    if (!canManageAccounts(user)) {
      setAccountManagement({
        status: "idle",
        message: NO_PERMISSION_MESSAGE,
        users: [],
        roles: []
      });
    }
    if (!canManageSignedUpdates(user)) {
      setSignedUpdatePreflight({
        status: "idle",
        message: NO_PERMISSION_MESSAGE,
        result: null
      });
      setSignedUpdateStage({
        status: "idle",
        message: NO_PERMISSION_MESSAGE,
        packages: []
      });
      setLocalBackupState({
        status: "idle",
        message: NO_PERMISSION_MESSAGE,
        backups: []
      });
      setLocalRestoreDryRun(null);
      setLocalMaintenanceReadiness({
        status: "idle",
        message: NO_PERMISSION_MESSAGE,
        data: null
      });
    }
    if (!canReadKnowledgeDocuments(user)) {
      setKnowledgeWorkbench({
        status: "idle",
        message: NO_PERMISSION_MESSAGE,
        businessObjects: [],
        objectCardsByObject: {},
        documents: [],
        chunksByDocument: {},
        publicationsByDocument: {},
        searchResult: null
      });
      setTenantReplyStrategy({
        status: "idle",
        message: NO_PERMISSION_MESSAGE,
        data: null
      });
      setKnowledgeMemoryMesh({
        status: "idle",
        message: NO_PERMISSION_MESSAGE,
        data: null
      });
    }
    if (!canReadKnowledgeEvaluations(user)) {
      setKnowledgeEvaluation({
        status: "idle",
        message: NO_PERMISSION_MESSAGE,
        sets: [],
        lastRun: null,
        runsBySet: {}
      });
    }
    if (!canReadQualityReview(user)) {
      setMonthlyQualityReview({
        status: "idle",
        message: NO_PERMISSION_MESSAGE,
        data: null
      });
      setOnlineReceiptQuality({
        status: "idle",
        message: NO_PERMISSION_MESSAGE,
        data: null
      });
      setCustomerQualityReport({
        status: "idle",
        message: NO_PERMISSION_MESSAGE,
        data: null
      });
      setCustomerQualityReportArchives({
        status: "idle",
        message: NO_PERMISSION_MESSAGE,
        data: null
      });
    }
    if (!canManageAccounts(user)) {
      setCustomerQualityReportSignoffs({
        status: "idle",
        message: NO_PERMISSION_MESSAGE,
        data: null
      });
    }
    if (!canReadKnowledgeGaps(user)) {
      setKnowledgeGaps({
        status: "idle",
        message: NO_PERMISSION_MESSAGE,
        data: EMPTY_KNOWLEDGE_GAP_LIST,
        lastSync: null
      });
    }
  }

  function refreshAllowedWorkspaceResources(user: CurrentUser, token: string) {
    const tenantId = user.tenant.id;
    resetUnavailableWorkspaceResources(user);
    if (canReadConversations(user)) {
      void refreshConversationInbox(tenantId, token);
      void refreshReviewInbox(tenantId, token);
      void refreshReplyDecisions(tenantId, token);
      void refreshAiServiceStatus(tenantId, token);
    }
    if (canReadTickets(user)) {
      void refreshSupportTickets(tenantId, token);
    }
    if (canReadCustomers(user)) {
      void refreshContactProfiles(tenantId, token);
    }
    if (canReadLeads(user)) {
      void refreshSalesLeads(tenantId, token);
    }
    if (canReadOutboxDrafts(user)) {
      void refreshOutbox(tenantId, token);
    }
    if (canReadFailureReviews(user)) {
      void refreshFailureReviews(tenantId, token);
    }
    if (canReadChannels(user)) {
      void refreshChannelAccounts(tenantId, token);
    }
    if (canReadOutboxDeliveryJobs(user)) {
      void refreshDeliveryQueue(tenantId, token);
    }
    if (canReadDashboard(user)) {
      void refreshBusinessOpsDashboard(tenantId, token);
    }
    if (canReadOpsWorkerHealth(user)) {
      void refreshOpsWorkerHealth(tenantId, token);
    }
    if (canReadOpsAlertRules(user)) {
      void refreshOpsAlertRules(tenantId, token);
    }
    if (canReadOpsMetrics(user)) {
      void refreshOpsMetrics(tenantId, token);
      void refreshDiagnosticIntakes(tenantId, token);
      void refreshDiagnosticRemediations(tenantId, token);
      void refreshRagCostGovernance(tenantId, token);
      void refreshLlmOpsReadiness(tenantId, token);
      void refreshMonthlyOpsReport(tenantId, token);
      void refreshPilotReadiness(tenantId, token);
    }
    if (canManageAccounts(user)) {
      void refreshAccountManagement(tenantId, token);
      void refreshCustomerQualityReportSignoffs(tenantId, token);
    }
    if (canManageSignedUpdates(user)) {
      void refreshSignedUpdatePackages(tenantId, token);
      void refreshLocalBackups(tenantId, token);
      void refreshLocalMaintenanceReadiness(tenantId, token);
    }
    if (canReadKnowledgeDocuments(user)) {
      void refreshKnowledgeDocuments(tenantId, token, hasKnowledgeManagePermission(user));
      void refreshKnowledgeMemoryMeshOverview(tenantId, token);
      void refreshTenantReplyStrategy(tenantId, token);
    }
    if (canReadKnowledgeEvaluations(user)) {
      void refreshKnowledgeEvaluations(tenantId, token, true);
    }
    if (canReadQualityReview(user)) {
      void refreshMonthlyQualityReview(tenantId, token);
      void refreshOnlineReceiptQuality(tenantId, token);
      void refreshCustomerQualityReport(tenantId, token);
      void refreshCustomerQualityReportArchives(tenantId, token);
    }
    if (canReadKnowledgeGaps(user)) {
      void refreshKnowledgeGaps(tenantId, token);
    }
  }

  function refreshLiveWorkspaceResources() {
    if (auth.status !== "ready" || !auth.token) {
      return;
    }
    const liveTargetChannelId =
      overviewTaskContext?.targetSection === "live" ? overviewTaskContext.channelId : null;
    if (canReadConversations(auth.user)) {
      void refreshConversationInbox(auth.user.tenant.id, auth.token, conversationInboxView, {
        ...conversationInboxFilters,
        channelId: liveTargetChannelId
      });
      void refreshReviewInbox(auth.user.tenant.id, auth.token);
      void refreshReplyDecisions(auth.user.tenant.id, auth.token);
    }
    if (canReadChannels(auth.user)) {
      void refreshChannelAccounts(auth.user.tenant.id, auth.token);
    }
    if (canReadOutboxDrafts(auth.user)) {
      void refreshOutbox(auth.user.tenant.id, auth.token);
    }
    if (canReadFailureReviews(auth.user)) {
      void refreshFailureReviews(auth.user.tenant.id, auth.token);
    }
    if (canReadOutboxDeliveryJobs(auth.user)) {
      void refreshDeliveryQueue(auth.user.tenant.id, auth.token);
    }
    if (canReadQualityReview(auth.user)) {
      void refreshMonthlyQualityReview(auth.user.tenant.id, auth.token);
      void refreshOnlineReceiptQuality(auth.user.tenant.id, auth.token);
      void refreshCustomerQualityReport(auth.user.tenant.id, auth.token);
    }
    if (canReadOpsMetrics(auth.user)) {
      void refreshMonthlyOpsReport(auth.user.tenant.id, auth.token);
    }
    if (canManageAccounts(auth.user)) {
      void refreshCustomerQualityReportSignoffs(auth.user.tenant.id, auth.token);
    }
  }

  async function handleCreateSafeTestConversation(): Promise<SafeTestConversationResult | null> {
    if (auth.status !== "ready" || !auth.token || !canManageConversation) {
      return null;
    }
    try {
      const result = await createSafeTestConversation(auth.user.tenant.id, auth.token);
      await refreshConversationInbox(auth.user.tenant.id, auth.token, conversationInboxView, conversationInboxFilters);
      await refreshPilotReadiness(auth.user.tenant.id, auth.token);
      setSelectedLiveConversationId(result.conversation_id);
      setActiveSection("live");
      return result;
    } catch (error) {
      const message = error instanceof Error ? error.message : "无法生成本地测试会话";
      setConversationInbox((current) => ({
        status: "error",
        message,
        data: current.data
      }));
      return null;
    }
  }

  async function refreshConnectionAndAllowedResources() {
    if (auth.status !== "ready") {
      return;
    }
    const refreshedUser = await refreshConnection(auth.token, auth.mode);
    if (auth.token && refreshedUser) {
      refreshAllowedWorkspaceResources(refreshedUser, auth.token);
    }
  }

  useEffect(() => {
    if (auth.status !== "ready") {
      return;
    }
    if (!auth.token) {
      if (auth.mode === "demo") {
        const demo = createDemoWorkspace();
        setReviewInbox({ status: "ready", items: demo.reviewItems });
        setReplyDecisionState({ status: "ready", items: demo.replyDecisions });
        setChannelIdentityById(demo.channelIdentities);
        setChannelAccountState({
          status: "idle",
          message: "当前为本地初始化数据；正式配置需登录后读取渠道账号 / 店铺登记。",
          channels: [],
          accounts: []
        });
        setConversationInbox({ status: "ready", data: demo.conversationInbox });
        setSupportTickets({ status: "ready", message: "当前为本地初始化工单，正式数据来自会话生成和坐席处理。", data: demo.supportTickets });
        setContactProfiles({
          status: "ready",
          message: "当前为本地初始化联系人画像，正式数据来自客户身份、会话、工单和线索聚合。",
          data: demo.contactProfiles,
          detail: demo.contactProfileDetail
        });
        setSalesLeads({
          status: "ready",
          message: "当前为本地初始化线索池，正式线索由会话生成并进入跟进闭环。",
          data: demo.salesLeads
        });
        setOutbox({ status: "ready", drafts: demo.outboxDrafts, attemptsByDraft: demo.attemptsByDraft });
        setFailureReviews({ status: "ready", items: demo.failureReviews });
        setDeliveryQueue({ status: "ready", jobs: demo.deliveryJobs });
        setBusinessOpsDashboard({ status: "idle", message: "当前使用本地样本聚合", data: null });
        setOpsWorkerHealth({ status: "ready", data: demo.opsWorkerHealth });
        setOpsAlertRules({ status: "ready", data: demo.opsAlertRules });
        setOpsMetrics({ status: "ready", data: demo.opsMetrics });
        setAccountManagement({
          status: "idle",
          message: "正式登录后可管理本地人员账号",
          users: [],
          roles: []
        });
        setDiagnosticExport({ status: "idle", message: "正式登录后可导出本地诊断包" });
        setKnowledgeWorkbench({
          status: "ready",
          message: "当前为本地初始化数据，不代表已连接真实外部平台。",
          businessObjects: demo.businessObjects,
          objectCardsByObject: demo.objectCardsByObject,
          documents: demo.knowledgeDocuments,
          chunksByDocument: demo.chunksByDocument,
          publicationsByDocument: demo.publicationsByDocument,
          searchResult: demo.searchResult
        });
        setTenantReplyStrategy({
          status: "ready",
          message: "当前为本地初始化策略，正式登录后读取本地数据库。",
          data: {
            tenant_id: 1,
            strategy_id: "local-initial-reply-policy",
            strategy_version: "demo",
            status: "active",
            reply_policy: {
              auto_reply_threshold: null,
              manual_review_threshold: null,
              blocked_policy_terms: ["私下转账", "绕过平台", "保证收益"],
              manual_review_terms: ["投诉", "起诉", "赔偿", "差评"],
              force_draft_only: false
            },
            model_routing: {},
            updated_by_id: 1,
            updated_at: new Date().toISOString(),
            created_at: new Date().toISOString(),
            source: "local_initial_data",
            external_write_performed: false,
            model_call_performed: false
          }
        });
        setReplyStrategyDraft({
          blockedPolicyTerms: "私下转账，绕过平台，保证收益",
          manualReviewTerms: "投诉，起诉，赔偿，差评",
          forceDraftOnly: false
        });
        setKnowledgeEvaluation({
          status: "ready",
          message: "当前为本地初始化评测，不消耗真实模型调用。",
          sets: demo.evaluationSets,
          lastRun: demo.evaluationRun,
          runsBySet: demo.runsBySet
        });
        setOnlineReceiptQuality({
          status: "ready",
          message: "当前为本地初始化回执样本，真实外发继续关闭。",
          data: demo.onlineReceiptQuality
        });
        setCustomerQualityReport({
          status: "ready",
          message: "当前为本地初始化质量报告，正式报告来自质量复盘和人工标签。",
          data: demo.customerQualityReport
        });
        setCustomerQualityReportArchives({
          status: "ready",
          message: "当前为本地初始化报告归档，正式归档来自导出审计。",
          data: demo.customerQualityReportArchives
        });
        setCustomerQualityReportSignoffs({
          status: "ready",
          message: "当前为本地初始化客户确认记录，正式记录来自负责人签收表单。",
          data: demo.customerQualityReportSignoffs
        });
        setKnowledgeGaps({
          status: "ready",
          message: "当前为本地初始化缺口，真实缺口来自人审和评测失败同步。",
          data: demo.knowledgeGaps,
          lastSync: demo.knowledgeGapSync
        });
        setLastWorkerRun(demo.outboxWorkerRun);
        setLastDeliveryQueueRun(demo.deliveryQueueRun);
        setLastInboundWorkerRun(demo.inboundWorkerRun);
        setSelectedReviewId(demo.reviewItems[0]?.id ?? null);
        return;
      }
      setOutbox({ status: "idle", message: "正式登录后可读取待发送草稿" });
      setReviewInbox({ status: "idle", message: "正式登录后可读取人工审核收件箱" });
      setReplyDecisionState({ status: "idle", message: "正式登录后可读取回复决策", items: [] });
      setConversationInbox({
        status: "idle",
        message: "正式登录后可读取会话收件箱",
        data: EMPTY_CONVERSATION_INBOX
      });
      setConversationDetail({
        status: "idle",
        message: "正式登录后可读取当前会话消息",
        data: null
      });
      setLocalReplyState({
        status: "idle",
        conversationId: null,
        message: "正式登录后可写入本地会话回复"
      });
      setSupportTickets({
        status: "idle",
        message: "正式登录后可读取工单/SLA",
        data: EMPTY_SUPPORT_TICKET_LIST
      });
      setContactProfiles({
        status: "idle",
        message: "正式登录后可读取联系人画像",
        data: EMPTY_CONTACT_PROFILE_LIST,
        detail: null
      });
      setSalesLeads({
        status: "idle",
        message: "正式登录后可读取线索池",
        data: EMPTY_SALES_LEAD_LIST
      });
      setFailureReviews({ status: "idle", message: "正式登录后可读取失败复盘队列" });
      setDeliveryQueue({ status: "idle", message: "正式登录后可读取发送队列" });
      setOpsWorkerHealth({ status: "idle", message: "正式登录后可读取后台进程健康状态", data: null });
      setOpsAlertRules({ status: "idle", message: "正式登录后可读取告警规则评估", data: null });
      setOpsMetrics({ status: "idle", message: "正式登录后可读取指标出口", data: null });
      setAccountManagement({
        status: "idle",
        message: "正式登录后可管理本地人员账号",
        users: [],
        roles: []
      });
      setKnowledgeWorkbench({
        status: "idle",
        message: "正式登录后可读取知识文档",
        businessObjects: [],
        objectCardsByObject: {},
        documents: [],
        chunksByDocument: {},
        publicationsByDocument: {},
        searchResult: null
      });
      setKnowledgeEvaluation({
        status: "idle",
        message: "正式登录后可读取知识评测集",
        sets: [],
        lastRun: null,
        runsBySet: {}
      });
      setOnlineReceiptQuality({
        status: "idle",
        message: "正式登录后可读取线上回执闭环",
        data: null
      });
      setKnowledgeGaps({
        status: "idle",
        message: "正式登录后可读取知识缺口",
        data: EMPTY_KNOWLEDGE_GAP_LIST,
        lastSync: null
      });
      setLastWorkerRun(null);
      setLastDeliveryQueueRun(null);
      setLastInboundWorkerRun(null);
      return;
    }
    refreshAllowedWorkspaceResources(auth.user, auth.token);
  }, [auth.status === "ready" ? `${auth.mode}:${auth.token ?? "demo"}` : auth.status]);

  useEffect(() => {
    if (auth.status !== "ready" || !auth.token) {
      return;
    }
    if (!["live", "conversations", "reviews", "outbox"].includes(activeSection)) {
      return;
    }
    refreshLiveWorkspaceResources();
  }, [activeSection, auth.status === "ready" ? auth.token : "", navigationRoleKey]);

  useEffect(() => {
    if (auth.status !== "ready" || !auth.token || !selectedLiveConversationId || !canReadConversations(auth.user)) {
      setConversationDetail({
        status: "idle",
        message: selectedLiveConversationId ? "当前账号无权读取会话消息" : "等待选择会话",
        data: null
      });
      return;
    }
    void refreshConversationDetail(selectedLiveConversationId, auth.token);
  }, [auth.status === "ready" ? auth.token : "", auth.status === "ready" ? auth.user.id : "", selectedLiveConversationId]);

  useEffect(() => {
    if (activeSection !== "live" || auth.status !== "ready" || !auth.token || !canReadConversations(auth.user)) {
      return;
    }
    const token = auth.token;
    const tenantId = auth.user.tenant.id;
    let stopped = false;
    const pollLiveWorkspace = async () => {
      if (stopped || liveAutoRefreshInFlightRef.current) {
        return;
      }
      liveAutoRefreshInFlightRef.current = true;
      try {
        await refreshConversationInbox(
          tenantId,
          token,
          conversationInboxView,
          conversationInboxFilters,
          { silent: true }
        );
        if (selectedLiveConversationId) {
          await refreshConversationDetail(selectedLiveConversationId, token, { silent: true });
        }
      } finally {
        liveAutoRefreshInFlightRef.current = false;
      }
    };
    const intervalId = window.setInterval(() => {
      void pollLiveWorkspace();
    }, 2500);
    void pollLiveWorkspace();
    return () => {
      stopped = true;
      window.clearInterval(intervalId);
    };
  }, [
    activeSection,
    auth.status === "ready" ? auth.token : "",
    auth.status === "ready" ? auth.user.id : "",
    auth.status === "ready" ? auth.user.tenant.id : "",
    selectedLiveConversationId,
    conversationInboxView.page,
    conversationInboxView.pageSize,
    conversationInboxView.query,
    conversationInboxView.status,
    conversationInboxFilters.assigned,
    conversationInboxFilters.channelId,
    conversationInboxFilters.priority,
    conversationInboxFilters.sla,
    conversationInboxFilters.sort
  ]);

  function handleConversationInboxViewChange(nextView: ListViewState) {
    setConversationInboxView(nextView);
    if (auth.status === "ready" && auth.token && canReadConversations(auth.user)) {
      void refreshConversationInbox(auth.user.tenant.id, auth.token, nextView, conversationInboxFilters);
    }
  }

  function handleConversationInboxFiltersChange(nextFilters: ConversationInboxFilters) {
    const nextView = { ...conversationInboxView, page: 1 };
    setConversationInboxFilters(nextFilters);
    setConversationInboxView(nextView);
    if (auth.status === "ready" && auth.token && canReadConversations(auth.user)) {
      void refreshConversationInbox(auth.user.tenant.id, auth.token, nextView, nextFilters);
    }
  }

  function handleSupportTicketListViewChange(nextView: ListViewState) {
    setSupportTicketListView(nextView);
    if (auth.status === "ready" && auth.token && canReadTickets(auth.user)) {
      void refreshSupportTickets(auth.user.tenant.id, auth.token, nextView, supportTicketFilters);
    }
  }

  function handleSupportTicketFiltersChange(nextFilters: SupportTicketFilters) {
    const nextView = { ...supportTicketListView, page: 1 };
    setSupportTicketFilters(nextFilters);
    setSupportTicketListView(nextView);
    if (auth.status === "ready" && auth.token && canReadTickets(auth.user)) {
      void refreshSupportTickets(auth.user.tenant.id, auth.token, nextView, nextFilters);
    }
  }

  function handleContactProfileListViewChange(nextView: ListViewState) {
    setContactProfileListView(nextView);
    if (auth.status === "ready" && auth.token && canReadCustomers(auth.user)) {
      void refreshContactProfiles(auth.user.tenant.id, auth.token, nextView);
    } else {
      setContactProfiles((current) => ({
        ...current,
        detail: buildContactProfileDetailFromLocal(
          current.data.items[0] ?? null,
          conversationInbox.data.items,
          salesLeads.data.items,
          supportTickets.data.items
        )
      }));
    }
  }

  async function handleSelectContactProfile(contactId: number) {
    if (auth.status === "ready" && auth.token) {
      setContactProfiles((current) => ({
        status: "loading",
        data: current.data,
        detail: current.detail
      }));
      try {
        const detail = await getContactProfile(contactId, auth.token);
        setContactProfiles((current) => ({
          status: "ready",
          data: current.data,
          detail
        }));
      } catch (error) {
        const message = error instanceof Error ? error.message : "读取联系人详情失败";
        setContactProfiles((current) => ({
          status: "error",
          message,
          data: current.data,
          detail: current.detail
        }));
      }
      return;
    }
    setContactProfiles((current) => {
      const profile = current.data.items.find((item) => item.id === contactId) ?? current.data.items[0] ?? null;
      return {
        ...current,
        detail: buildContactProfileDetailFromLocal(
          profile,
          conversationInbox.data.items,
          salesLeads.data.items,
          supportTickets.data.items
        )
      };
    });
  }

  function handleSalesLeadListViewChange(nextView: ListViewState) {
    setSalesLeadListView(nextView);
    if (auth.status === "ready" && auth.token && canReadLeads(auth.user)) {
      void refreshSalesLeads(auth.user.tenant.id, auth.token, nextView, salesLeadFilters);
    }
  }

  function handleSalesLeadFiltersChange(nextFilters: SalesLeadFilters) {
    const nextView = { ...salesLeadListView, page: 1 };
    setSalesLeadFilters(nextFilters);
    setSalesLeadListView(nextView);
    if (auth.status === "ready" && auth.token && canReadLeads(auth.user)) {
      void refreshSalesLeads(auth.user.tenant.id, auth.token, nextView, nextFilters);
    }
  }

  function handleKnowledgeGapListViewChange(nextView: ListViewState) {
    setKnowledgeGapListView(nextView);
    if (auth.status === "ready" && auth.token && canReadKnowledgeGaps(auth.user)) {
      void refreshKnowledgeGaps(auth.user.tenant.id, auth.token, nextView);
    }
  }

  async function handleSyncKnowledgeGaps() {
    if (auth.status !== "ready" || !auth.token || !hasPermission(auth.user, PERMISSIONS.knowledgeManage)) {
      return;
    }
    setKnowledgeGaps((current) => ({
      ...current,
      status: "loading",
      message: "正在从人审和评测失败同步知识缺口"
    }));
    try {
      const syncResult = await syncKnowledgeGaps(auth.user.tenant.id, auth.token);
      const data = await listKnowledgeGaps(auth.user.tenant.id, auth.token, {
        ...knowledgeGapListParams(knowledgeGapListView)
      });
      setKnowledgeGaps({
        status: "ready",
        message: `同步完成：新增 ${syncResult.created_count} 条，已存在 ${syncResult.existing_count} 条，扫描 ${syncResult.scanned_count} 条来源`,
        data,
        lastSync: syncResult
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : "同步知识缺口失败";
      setKnowledgeGaps((current) => ({
        ...current,
        status: "error",
        message
      }));
    }
  }

  async function handleUpdateKnowledgeGap(
    gap: KnowledgeGap,
    statusValue: "open" | "triaged" | "in_progress" | "resolved" | "rejected" | "archived"
  ) {
    if (auth.status !== "ready" || !auth.token || !hasPermission(auth.user, PERMISSIONS.knowledgeManage)) {
      return;
    }
    setKnowledgeGaps((current) => ({
      ...current,
      status: "loading",
      message: `正在更新缺口 #${gap.id}`
    }));
    try {
      await updateKnowledgeGap(gap.id, auth.token, {
        status: statusValue,
        assigned_user_id: statusValue === "in_progress" ? Number(auth.user.id) : gap.assigned_user_id,
        resolution_note:
          statusValue === "resolved"
            ? "已完成知识补充或确认不需补充，等待下一轮题库回归。"
            : gap.resolution_note
      });
      await refreshKnowledgeGaps(auth.user.tenant.id, auth.token, knowledgeGapListView);
    } catch (error) {
      const message = error instanceof Error ? error.message : "更新知识缺口失败";
      setKnowledgeGaps((current) => ({
        ...current,
        status: "error",
        message
      }));
    }
  }

  async function handleCreateKnowledgeGapDocumentDraft(gap: KnowledgeGap) {
    if (auth.status !== "ready" || !auth.token || !hasPermission(auth.user, PERMISSIONS.knowledgeManage)) {
      return;
    }
    setKnowledgeGaps((current) => ({
      ...current,
      status: "loading",
      message: `正在为缺口 #${gap.id} 生成知识草稿`
    }));
    try {
      const result: KnowledgeGapDocumentDraftResult = await createKnowledgeGapDocumentDraft(gap.id, auth.token);
      const data = await listKnowledgeGaps(auth.user.tenant.id, auth.token, {
        ...knowledgeGapListParams(knowledgeGapListView)
      });
      setKnowledgeGaps((current) => ({
        status: "ready",
        message: result.created
          ? `已生成知识草稿 #${result.document.id}，状态为草稿，需审核后启用`
          : `已复用知识草稿 #${result.document.id}，未重复创建`,
        data,
        lastSync: current.lastSync
      }));
      await refreshKnowledgeDocuments(auth.user.tenant.id, auth.token, true);
    } catch (error) {
      const message = error instanceof Error ? error.message : "生成知识草稿失败";
      setKnowledgeGaps((current) => ({
        ...current,
        status: "error",
        message
      }));
    }
  }

  async function handleCreateKnowledgeGapRegressionCase(gap: KnowledgeGap) {
    if (auth.status !== "ready" || !auth.token || !hasPermission(auth.user, PERMISSIONS.knowledgeManage)) {
      return;
    }
    setKnowledgeGaps((current) => ({
      ...current,
      status: "loading",
      message: `正在把缺口 #${gap.id} 加入回归题库`
    }));
    try {
      const result: KnowledgeGapRegressionCaseResult = await createKnowledgeGapRegressionCase(gap.id, auth.token);
      const data = await listKnowledgeGaps(auth.user.tenant.id, auth.token, {
        ...knowledgeGapListParams(knowledgeGapListView)
      });
      setKnowledgeGaps((current) => ({
        status: "ready",
        message: result.created
          ? `已加入回归题库：${result.evaluation_set.name} / 题目 #${result.evaluation_case.id}`
          : `已复用回归题：${result.evaluation_set.name} / 题目 #${result.evaluation_case.id}`,
        data,
        lastSync: current.lastSync
      }));
      await refreshKnowledgeEvaluations(auth.user.tenant.id, auth.token, true);
    } catch (error) {
      const message = error instanceof Error ? error.message : "加入回归题库失败";
      setKnowledgeGaps((current) => ({
        ...current,
        status: "error",
        message
      }));
    }
  }

  async function handleConversationWorkflowAction(
    item: ConversationInboxItem,
    action: ConversationWorkflowActionName,
    note?: string,
    targetUserId?: number | null,
    targetTeamId?: number | null
  ) {
    if (auth.status === "ready" && auth.mode === "demo") {
      setConversationInbox((current) => ({
        ...current,
        data: {
          ...current.data,
          items: current.data.items
            .filter((conversation) => action !== "close" || conversation.id !== item.id)
            .map((conversation) =>
              conversation.id === item.id
                ? {
                    ...conversation,
                    status: action === "resolve" ? "resolved" : action === "close" ? "closed" : conversation.status,
                    assigned_user_id:
                      action === "release"
                        ? null
                        : action === "transfer"
                          ? targetUserId ?? conversation.assigned_user_id
                          : conversation.assigned_user_id,
                    next_action: note?.trim() || conversationActionNote(action)
                  }
                : conversation
            )
        }
      }));
      if (action === "close" && selectedLiveConversationId === item.id) {
        hideConversationLocally(item.id);
      }
      return;
    }
    if (auth.status !== "ready" || !auth.token || !hasPermission(auth.user, PERMISSIONS.conversationManage)) {
      return;
    }
    if (action === "close") {
      hideConversationLocally(item.id);
    } else {
      setConversationInbox((current) => ({
        status: "loading",
        data: current.data
      }));
    }
    try {
      await applyConversationWorkflowAction(item.id, auth.token, {
        action,
        target_user_id: targetUserId,
        target_team_id: targetTeamId,
        note: note?.trim() || conversationActionNote(action)
      });
      await refreshConversationInbox(auth.user.tenant.id, auth.token, conversationInboxView, conversationInboxFilters);
      if (action === "close") {
        hideConversationLocally(item.id);
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : "会话动作失败";
      setConversationInbox((current) => ({
        status: "error",
        message,
        data: current.data
      }));
    }
  }

  async function handlePublishKnowledgeGapDocument(gap: KnowledgeGap) {
    if (
      auth.status !== "ready" ||
      !auth.token ||
      !gap.linked_knowledge_document_id ||
      !hasPermission(auth.user, PERMISSIONS.knowledgeManage)
    ) {
      return;
    }
    setKnowledgeGaps((current) => ({
      ...current,
      status: "loading",
      message: `正在校验并发布知识文档 #${gap.linked_knowledge_document_id}`
    }));
    try {
      const result: KnowledgeDocumentPublishGateResult = await publishKnowledgeDocument(
        gap.linked_knowledge_document_id,
        auth.token,
        {
          top_k: 8,
          low_confidence_threshold: 0.35
        }
      );
      await refreshKnowledgeGaps(auth.user.tenant.id, auth.token, {
        status: knowledgeGapListView.status,
        query: knowledgeGapListView.query,
        page: knowledgeGapListView.page,
        pageSize: knowledgeGapListView.pageSize
      });
      await refreshKnowledgeDocuments(auth.user.tenant.id, auth.token, true);
      await refreshKnowledgeEvaluations(auth.user.tenant.id, auth.token, true);
      setKnowledgeGaps((current) => ({
        ...current,
        status: result.can_publish ? "ready" : "error",
        message: result.published
          ? `已发布知识文档 #${result.document.id}，并完成回归门禁。`
          : `${result.message} 阻断项：${result.blocking_reasons.join("、") || "无"}`
      }));
    } catch (error) {
      const message = error instanceof Error ? error.message : "知识发布门禁失败";
      setKnowledgeGaps((current) => ({
        ...current,
        status: "error",
        message
      }));
    }
  }

  async function handleCheckKnowledgeDocumentPublishGate(document: KnowledgeDocument) {
    if (auth.status !== "ready" || !auth.token || !hasPermission(auth.user, PERMISSIONS.knowledgeManage)) {
      return;
    }
    setKnowledgeWorkbench((current) => ({
      ...current,
      status: "loading",
      message: `正在用样题试跑知识文档 #${document.id}`
    }));
    try {
      const result = await checkKnowledgeDocumentPublishGate(document.id, auth.token, {
        top_k: 8,
        low_confidence_threshold: 0.35,
        search_status: document.status === "draft" ? "draft" : "active",
        ignore_safe_handoff_failures: true
      });
      await refreshKnowledgeDocuments(auth.user.tenant.id, auth.token, true);
      await refreshKnowledgeEvaluations(auth.user.tenant.id, auth.token, true);
      setKnowledgeWorkbench((current) => ({
        ...current,
        status: result.can_publish ? "ready" : "error",
        message: result.can_publish
          ? `样题试跑通过：文档 #${result.document.id} 可以进入发布确认。`
          : `样题试跑未通过：${result.blocking_reasons.join("、") || result.message}`
      }));
    } catch (error) {
      const message = error instanceof Error ? error.message : "知识发布前样题试跑失败";
      setKnowledgeWorkbench((current) => ({
        ...current,
        status: "error",
        message
      }));
    }
  }

  async function handlePublishKnowledgeDocument(document: KnowledgeDocument) {
    if (auth.status !== "ready" || !auth.token || !hasPermission(auth.user, PERMISSIONS.knowledgeManage)) {
      return;
    }
    setKnowledgeWorkbench((current) => ({
      ...current,
      status: "loading",
      message: `正在确认发布知识文档 #${document.id}`
    }));
    try {
      const result = await publishKnowledgeDocument(document.id, auth.token, {
        top_k: 8,
        low_confidence_threshold: 0.35,
        search_status: document.status === "draft" ? "draft" : "active",
        ignore_safe_handoff_failures: true
      });
      await refreshKnowledgeDocuments(auth.user.tenant.id, auth.token, true);
      await refreshKnowledgeEvaluations(auth.user.tenant.id, auth.token, true);
      setKnowledgeWorkbench((current) => ({
        ...current,
        status: result.published ? "ready" : "error",
        message: result.published
          ? `发布成功：文档 #${result.document.id} 已进入 active 检索范围，外部平台发送仍保持关闭。`
          : `发布被阻断：${result.blocking_reasons.join("、") || result.message}`
      }));
    } catch (error) {
      const message = error instanceof Error ? error.message : "知识文档发布失败";
      setKnowledgeWorkbench((current) => ({
        ...current,
        status: "error",
        message
      }));
    }
  }

  async function handleCreateSupportTicket(item: ConversationInboxItem) {
    if (auth.status !== "ready" || !auth.token || !hasPermission(auth.user, PERMISSIONS.ticketManage)) {
      return;
    }
    setSupportTickets((current) => ({
      status: "loading",
      data: current.data
    }));
    try {
      await createSupportTicketFromConversation(item.id, auth.token, {
        subject: item.subject || `${item.contact_display_name || "客户"} · 工单跟进`,
        description: item.last_message_preview || "由会话收件箱生成的客服工单。",
        priority: normalizeTicketPriority(item.priority),
        assigned_user_id: auth.mode === "token" ? Number(auth.user.id) : null
      });
      await Promise.all([
        refreshSupportTickets(auth.user.tenant.id, auth.token, supportTicketListView, supportTicketFilters),
        refreshConversationInbox(auth.user.tenant.id, auth.token, conversationInboxView, conversationInboxFilters)
      ]);
    } catch (error) {
      const message = error instanceof Error ? error.message : "生成工单失败";
      setSupportTickets((current) => ({
        status: "error",
        message,
        data: current.data
      }));
    }
  }

  async function handleUpdateSupportTicketStatus(
    ticket: SupportTicket,
    statusValue: "in_progress" | "pending_customer" | "resolved"
  ) {
    if (auth.status !== "ready" || !auth.token || !hasPermission(auth.user, PERMISSIONS.ticketManage)) {
      return;
    }
    setSupportTickets((current) => ({
      status: "loading",
      data: current.data
    }));
    try {
      await updateSupportTicket(ticket.id, auth.token, {
        status: statusValue,
        assigned_user_id: ticket.assigned_user_id ?? Number(auth.user.id),
        resolution_note: supportTicketActionNote(statusValue)
      });
      await refreshSupportTickets(auth.user.tenant.id, auth.token, supportTicketListView, supportTicketFilters);
    } catch (error) {
      const message = error instanceof Error ? error.message : "更新工单失败";
      setSupportTickets((current) => ({
        status: "error",
        message,
        data: current.data
      }));
    }
  }

  async function handleCreateSalesLead(item: ConversationInboxItem) {
    if (auth.status !== "ready" || !auth.token || !hasPermission(auth.user, PERMISSIONS.leadManage)) {
      return;
    }
    setSalesLeads((current) => ({
      status: "loading",
      data: current.data
    }));
    try {
      await createSalesLeadFromConversation(item.id, auth.token, {
        title: item.subject || `${item.contact_display_name || "客户"} · 线索跟进`,
        summary: item.last_message_preview || "由会话收件箱生成的销售线索。",
        stage: "new",
        intent_level: normalizeLeadIntentFromConversation(item),
        expected_budget: "",
        next_step: "先由坐席确认需求、预算、交付时间和决策人。",
        owner_user_id: auth.mode === "token" ? Number(auth.user.id) : null
      });
      await Promise.all([
        refreshSalesLeads(auth.user.tenant.id, auth.token, salesLeadListView, salesLeadFilters),
        refreshContactProfiles(auth.user.tenant.id, auth.token, contactProfileListView, item.contact_id),
        refreshConversationInbox(auth.user.tenant.id, auth.token, conversationInboxView, conversationInboxFilters)
      ]);
    } catch (error) {
      const message = error instanceof Error ? error.message : "生成线索失败";
      setSalesLeads((current) => ({
        status: "error",
        message,
        data: current.data
      }));
    }
  }

  async function handleUpdateSalesLeadStage(
    lead: SalesLead,
    stage: "contacted" | "proposal" | "won" | "invalid" | "lost"
  ) {
    if (auth.status !== "ready" || !auth.token || !hasPermission(auth.user, PERMISSIONS.leadManage)) {
      return;
    }
    setSalesLeads((current) => ({
      status: "loading",
      data: current.data
    }));
    try {
      await updateSalesLead(lead.id, auth.token, {
        stage,
        owner_user_id: lead.owner_user_id ?? Number(auth.user.id),
        next_step: leadStageActionNote(stage)
      });
      await Promise.all([
        refreshSalesLeads(auth.user.tenant.id, auth.token, salesLeadListView, salesLeadFilters),
        refreshContactProfiles(auth.user.tenant.id, auth.token, contactProfileListView, lead.contact_id)
      ]);
    } catch (error) {
      const message = error instanceof Error ? error.message : "更新线索失败";
      setSalesLeads((current) => ({
        status: "error",
        message,
        data: current.data
      }));
    }
  }

  async function handleSaveBusinessObject() {
    if (auth.status !== "ready" || !auth.token || !hasPermission(auth.user, PERMISSIONS.knowledgeManage)) {
      return;
    }
    const title = businessObjectDraft.title.trim();
    if (!title) {
      setKnowledgeWorkbench((current) => ({
        ...current,
        status: "error",
        message: "业务对象名称不能为空"
      }));
      return;
    }
    setKnowledgeWorkbench((current) => ({
      ...current,
      status: "loading",
      message: ""
    }));
    try {
      const payload = {
        type: businessObjectDraft.type,
        title,
        summary: businessObjectDraft.summary.trim(),
        aliases: splitFreeTextList(businessObjectDraft.aliases),
        status: "active" as const
      };
      if (businessObjectDraft.editingId) {
        await updateBusinessObject(businessObjectDraft.editingId, auth.token, payload);
      } else {
        await createBusinessObject(auth.user.tenant.id, auth.token, payload);
      }
      setBusinessObjectDraft({ editingId: null, type: "product", title: "", aliases: "", summary: "" });
      await refreshKnowledgeDocuments(auth.user.tenant.id, auth.token, true);
    } catch (error) {
      const message = error instanceof Error ? error.message : "保存业务对象失败";
      setKnowledgeWorkbench((current) => ({
        ...current,
        status: "error",
        message
      }));
    }
  }

  async function handleCreateObjectKnowledgeCard() {
    if (auth.status !== "ready" || !auth.token || !hasPermission(auth.user, PERMISSIONS.knowledgeManage)) {
      return;
    }
    const businessObjectId = objectKnowledgeCardDraft.businessObjectId ?? knowledgeWorkbench.businessObjects[0]?.id ?? null;
    const question = objectKnowledgeCardDraft.question.trim();
    const answer = objectKnowledgeCardDraft.answer.trim();
    if (!businessObjectId || !question || !answer) {
      setKnowledgeWorkbench((current) => ({
        ...current,
        status: "error",
        message: "请选择业务对象，并填写问题和标准答案"
      }));
      return;
    }
    setKnowledgeWorkbench((current) => ({
      ...current,
      status: "loading",
      message: ""
    }));
    try {
      await createObjectKnowledgeCard(businessObjectId, auth.token, {
        question,
        answer,
        trigger_keywords: splitFreeTextList(objectKnowledgeCardDraft.triggerKeywords),
        scope: { channels: ["all"], reply_mode: "auto_with_handoff" },
        source: "manual",
        status: "active"
      });
      setObjectKnowledgeCardDraft({
        businessObjectId,
        question: "",
        answer: "",
        triggerKeywords: ""
      });
      await refreshKnowledgeDocuments(auth.user.tenant.id, auth.token, true);
    } catch (error) {
      const message = error instanceof Error ? error.message : "创建对象知识卡失败";
      setKnowledgeWorkbench((current) => ({
        ...current,
        status: "error",
        message
      }));
    }
  }

  function parseKnowledgeUpdatePackageDraft(): unknown | null {
    try {
      return JSON.parse(knowledgeUpdatePackageDraft.text);
    } catch {
      setKnowledgeUpdatePackageDraft((current) => ({
        ...current,
        status: "error",
        message: "资料包内容格式不正确，请检查逗号、引号和括号。"
      }));
      return null;
    }
  }

  async function handlePreviewKnowledgeUpdatePackage() {
    if (auth.status !== "ready" || !auth.token || !hasPermission(auth.user, PERMISSIONS.knowledgeManage)) {
      return;
    }
    const packagePayload = parseKnowledgeUpdatePackageDraft();
    if (!packagePayload) {
      return;
    }
    setKnowledgeUpdatePackageDraft((current) => ({
      ...current,
      status: "loading",
      message: "正在检查知识资料包"
    }));
    try {
      const result = await previewKnowledgeUpdatePackage(auth.user.tenant.id, auth.token, packagePayload);
      setKnowledgeUpdatePackageDraft((current) => ({
        ...current,
        result,
        status: "ready",
        message: result.can_apply
          ? `预检通过：将新增 ${result.operation_counts.create} 项，跳过 ${result.operation_counts.skip} 项。`
          : `预检发现 ${result.operation_counts.error} 个问题，请修正后再导入。`
      }));
    } catch (error) {
      const message = error instanceof Error ? error.message : "知识资料包检查失败";
      setKnowledgeUpdatePackageDraft((current) => ({
        ...current,
        status: "error",
        message
      }));
    }
  }

  async function handleImportKnowledgeUpdatePackage() {
    if (auth.status !== "ready" || !auth.token || !hasPermission(auth.user, PERMISSIONS.knowledgeManage)) {
      return;
    }
    const packagePayload = parseKnowledgeUpdatePackageDraft();
    if (!packagePayload) {
      return;
    }
    setKnowledgeUpdatePackageDraft((current) => ({
      ...current,
      status: "loading",
      message: "正在导入知识资料包"
    }));
    try {
      const result = await importKnowledgeUpdatePackage(auth.user.tenant.id, auth.token, packagePayload);
      setKnowledgeUpdatePackageDraft((current) => ({
        ...current,
        result,
        status: "ready",
        message: `已导入知识资料包：新增 ${result.operation_counts.create} 项，跳过 ${result.operation_counts.skip} 项。`
      }));
      await Promise.all([
        refreshKnowledgeDocuments(auth.user.tenant.id, auth.token, true),
        refreshKnowledgeEvaluations(auth.user.tenant.id, auth.token, true)
      ]);
      if (canReadOpsMetrics(auth.user)) {
        await Promise.all([
          refreshRagCostGovernance(auth.user.tenant.id, auth.token),
          refreshLlmOpsReadiness(auth.user.tenant.id, auth.token)
        ]);
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : "知识资料包导入失败";
      setKnowledgeUpdatePackageDraft((current) => ({
        ...current,
        status: "error",
        message
      }));
    }
  }

  function getKnowledgeTemplateRowsOrSetError(): KnowledgeImportTemplateRow[] {
    const rows = parseKnowledgeTemplateImportRows(knowledgeTemplateImportDraft.text);
    if (rows.length === 0) {
      setKnowledgeTemplateImportDraft((current) => ({
        ...current,
        status: "error",
        message: "表格资料为空，请保留表头并至少填写一行。"
      }));
    }
    return rows;
  }

  async function handlePrecheckKnowledgeTemplateImport() {
    if (auth.status !== "ready" || !auth.token || !hasPermission(auth.user, PERMISSIONS.knowledgeManage)) {
      return;
    }
    const rows = getKnowledgeTemplateRowsOrSetError();
    if (rows.length === 0) return;
    setKnowledgeTemplateImportDraft((current) => ({
      ...current,
      status: "loading",
      message: "正在预检表格资料"
    }));
    try {
      const result = await precheckKnowledgeImport(auth.user.tenant.id, auth.token, {
        source_file_ref: knowledgeTemplateImportDraft.sourceFileRef,
        rows
      });
      setKnowledgeTemplateImportDraft((current) => ({
        ...current,
        precheck: result,
        status: result.can_import ? "ready" : "error",
        message: result.can_import
          ? `预检通过：${result.valid_count}/${result.row_count} 行可导入，警告 ${result.warning_count} 条。`
          : `预检阻断：错误 ${result.error_count} 条，请修正后再导入。`
      }));
    } catch (error) {
      const message = error instanceof Error ? error.message : "表格资料预检失败";
      setKnowledgeTemplateImportDraft((current) => ({ ...current, status: "error", message }));
    }
  }

  async function handleCreateKnowledgeTemplateImport() {
    if (auth.status !== "ready" || !auth.token || !hasPermission(auth.user, PERMISSIONS.knowledgeManage)) {
      return;
    }
    const rows = getKnowledgeTemplateRowsOrSetError();
    if (rows.length === 0) return;
    setKnowledgeTemplateImportDraft((current) => ({
      ...current,
      status: "loading",
      message: "正在导入为草稿批次"
    }));
    try {
      const result = await createKnowledgeImport(auth.user.tenant.id, auth.token, {
        source_file_ref: knowledgeTemplateImportDraft.sourceFileRef,
        rows
      });
      setKnowledgeTemplateImportDraft((current) => ({
        ...current,
        importBatch: result,
        sampleRun: null,
        publication: null,
        status: result.status === "draft" ? "ready" : "error",
        message: result.status === "draft"
          ? `已导入草稿批次 #${result.id}，请继续样题试跑。`
          : `导入批次 #${result.id} 状态为 ${result.status}，请先修正预检错误。`
      }));
    } catch (error) {
      const message = error instanceof Error ? error.message : "表格资料导入失败";
      setKnowledgeTemplateImportDraft((current) => ({ ...current, status: "error", message }));
    }
  }

  async function handleRunKnowledgeTemplateSample() {
    if (auth.status !== "ready" || !auth.token || !hasPermission(auth.user, PERMISSIONS.knowledgeManage)) {
      return;
    }
    const importId = knowledgeTemplateImportDraft.importBatch?.id;
    if (!importId) {
      setKnowledgeTemplateImportDraft((current) => ({
        ...current,
        status: "error",
        message: "请先导入草稿批次，再进行样题试跑。"
      }));
      return;
    }
    setKnowledgeTemplateImportDraft((current) => ({
      ...current,
      status: "loading",
      message: "正在样题试跑"
    }));
    try {
      const result = await runKnowledgeImportSample(auth.user.tenant.id, importId, auth.token);
      setKnowledgeTemplateImportDraft((current) => ({
        ...current,
        sampleRun: result,
        status: result.can_publish ? "ready" : "error",
        message: result.can_publish
          ? `试跑通过：命中 ${result.hit_cases}，低置信 ${result.low_confidence_cases}，风险阻断 ${result.blocked_cases}。`
          : "试跑未通过，请修正资料后重新导入。"
      }));
    } catch (error) {
      const message = error instanceof Error ? error.message : "样题试跑失败";
      setKnowledgeTemplateImportDraft((current) => ({ ...current, status: "error", message }));
    }
  }

  async function handlePublishKnowledgeTemplateImport() {
    if (auth.status !== "ready" || !auth.token || !hasPermission(auth.user, PERMISSIONS.knowledgeManage)) {
      return;
    }
    const importId = knowledgeTemplateImportDraft.importBatch?.id;
    if (!importId) {
      setKnowledgeTemplateImportDraft((current) => ({
        ...current,
        status: "error",
        message: "请先导入草稿批次，再发布资料。"
      }));
      return;
    }
    setKnowledgeTemplateImportDraft((current) => ({
      ...current,
      status: "loading",
      message: "正在发布资料版本"
    }));
    try {
      const result = await publishKnowledgeImport(auth.user.tenant.id, auth.token, {
        import_batch_id: importId,
        note: "前端资料中心发布"
      });
      setKnowledgeTemplateImportDraft((current) => ({
        ...current,
        publication: result,
        status: "ready",
        message: result.message
      }));
      await Promise.all([
        refreshKnowledgeDocuments(auth.user.tenant.id, auth.token, true),
        refreshKnowledgeMemoryMeshOverview(auth.user.tenant.id, auth.token)
      ]);
    } catch (error) {
      const message = error instanceof Error ? error.message : "资料发布失败";
      setKnowledgeTemplateImportDraft((current) => ({ ...current, status: "error", message }));
    }
  }

  async function handleSaveTenantReplyStrategy() {
    if (auth.status !== "ready" || !auth.token || !hasPermission(auth.user, PERMISSIONS.knowledgeManage)) {
      return;
    }
    const blockedPolicyTerms = splitFreeTextList(replyStrategyDraft.blockedPolicyTerms);
    const manualReviewTerms = splitFreeTextList(replyStrategyDraft.manualReviewTerms);
    if (blockedPolicyTerms.length === 0 && manualReviewTerms.length === 0) {
      setTenantReplyStrategy((current) => ({
        ...current,
        status: "error",
        message: "请至少填写一个禁止承诺词或转人工词"
      }));
      return;
    }
    setTenantReplyStrategy((current) => ({
      ...current,
      status: "loading",
      message: "正在保存自动回复策略"
    }));
    try {
      const data = await updateTenantReplyStrategy(auth.user.tenant.id, auth.token, {
        blocked_policy_terms: blockedPolicyTerms,
        manual_review_terms: manualReviewTerms,
        force_draft_only: replyStrategyDraft.forceDraftOnly
      });
      setTenantReplyStrategy({
        status: "ready",
        message: "自动回复策略已保存，后续回复决策会读取这些规则。",
        data
      });
      await Promise.all([
        refreshReplyDecisions(auth.user.tenant.id, auth.token),
        canReadOpsMetrics(auth.user)
          ? Promise.all([
              refreshRagCostGovernance(auth.user.tenant.id, auth.token),
              refreshLlmOpsReadiness(auth.user.tenant.id, auth.token)
            ])
          : Promise.resolve()
      ]);
    } catch (error) {
      const message = error instanceof Error ? error.message : "保存自动回复策略失败";
      setTenantReplyStrategy((current) => ({
        ...current,
        status: "error",
        message
      }));
    }
  }

  async function handleImportKnowledgeDocument() {
    if (auth.status !== "ready" || !auth.token || !hasPermission(auth.user, PERMISSIONS.knowledgeManage)) {
      return;
    }
    const title = knowledgeDraft.title.trim();
    const rawText = knowledgeDraft.rawText.trim();
    if (!title || !rawText) {
      setKnowledgeWorkbench((current) => ({
        ...current,
        status: "error",
        message: "标题和正文不能为空"
      }));
      return;
    }
    setKnowledgeWorkbench((current) => ({
      ...current,
      status: "loading",
      message: ""
    }));
    try {
      await createKnowledgeDocument(auth.user.tenant.id, auth.token, {
        title,
        raw_text: rawText,
        source_uri: knowledgeDraft.sourceUri.trim(),
        tags: knowledgeDraft.tags
          .split(/[,，\n]/)
          .map((tag) => tag.trim())
          .filter(Boolean),
        status: "active"
      });
      setKnowledgeDraft({ title: "", sourceUri: "", tags: "", rawText: "" });
      await refreshKnowledgeDocuments(auth.user.tenant.id, auth.token, true);
    } catch (error) {
      const message = error instanceof Error ? error.message : "导入知识文档失败";
      setKnowledgeWorkbench((current) => ({
        ...current,
        status: "error",
        message
      }));
    }
  }

  async function handleSearchKnowledgeDocuments() {
    if (auth.status !== "ready" || !auth.token || !canReadKnowledgeDocuments(auth.user)) {
      return;
    }
    const query = knowledgeSearchQuery.trim();
    if (!query) {
      setKnowledgeWorkbench((current) => ({
        ...current,
        status: "error",
        message: "请输入要检索的问题"
      }));
      return;
    }
    setKnowledgeWorkbench((current) => ({
      ...current,
      status: "loading",
      message: ""
    }));
    try {
      const searchResult = await searchKnowledgeDocuments(auth.user.tenant.id, auth.token, {
        query,
        top_k: 5
      });
      setKnowledgeWorkbench((current) => ({
        ...current,
        status: "ready",
        message: "",
        searchResult
      }));
    } catch (error) {
      const message = error instanceof Error ? error.message : "文档片段检索失败";
      setKnowledgeWorkbench((current) => ({
        ...current,
        status: "error",
        message
      }));
    }
  }

  async function handleCreateKnowledgeEvaluationSet() {
    if (auth.status !== "ready" || !auth.token || !hasPermission(auth.user, PERMISSIONS.knowledgeManage)) {
      return;
    }
    const name = evaluationDraft.name.trim();
    const cases = parseEvaluationCases(evaluationDraft.casesText);
    if (!name || cases.length === 0) {
      setKnowledgeEvaluation((current) => ({
        ...current,
        status: "error",
        message: "评测集名称和至少一道题不能为空"
      }));
      return;
    }
    setKnowledgeEvaluation((current) => ({
      ...current,
      status: "loading",
      message: ""
    }));
    try {
      await createKnowledgeEvaluationSet(auth.user.tenant.id, auth.token, {
        name,
        description: evaluationDraft.description.trim(),
        evaluation_mode: evaluationDraft.evaluationMode,
        cases
      });
      setEvaluationDraft({ name: "", description: "", evaluationMode: "customer_service_retrieval", casesText: "" });
      await refreshKnowledgeEvaluations(auth.user.tenant.id, auth.token, true);
    } catch (error) {
      const message = error instanceof Error ? error.message : "创建知识评测集失败";
      setKnowledgeEvaluation((current) => ({
        ...current,
        status: "error",
        message
      }));
    }
  }

  function parseCustomerQuestionBankDraft(): CustomerServiceQuestionBankImportPayload | null {
    try {
      const parsed = JSON.parse(customerQuestionBankDraft.text);
      const source = parsed && typeof parsed === "object" && parsed.payload && Array.isArray(parsed.payload.cases) ? parsed.payload : parsed;
      if (!source || typeof source !== "object" || !Array.isArray(source.cases)) {
        throw new Error("题库 JSON 必须包含 cases 数组");
      }
      return {
        name: String(source.name || "客户脱敏题库").trim(),
        description: String(source.description || "").trim(),
        source_label: String(source.source_label || "customer_question_bank_json").trim(),
        status: source.status === "draft" || source.status === "archived" ? source.status : "active",
        evaluation_mode: "customer_service_retrieval",
        minimum_case_count: Number(source.minimum_case_count ?? 50),
        maximum_case_count: Number(source.maximum_case_count ?? 100),
        allow_sensitive_rows: Boolean(source.allow_sensitive_rows),
        cases: source.cases
      };
    } catch (error) {
      const message = error instanceof Error ? error.message : "题库 JSON 解析失败";
      setCustomerQuestionBankDraft((current) => ({
        ...current,
        status: "error",
        message,
        result: null
      }));
      return null;
    }
  }

  async function handlePrecheckCustomerQuestionBank() {
    if (auth.status !== "ready" || !auth.token || !hasPermission(auth.user, PERMISSIONS.knowledgeManage)) {
      return;
    }
    const payload = parseCustomerQuestionBankDraft();
    if (!payload) {
      return;
    }
    setCustomerQuestionBankDraft((current) => ({
      ...current,
      status: "loading",
      message: "正在预检客户题库包"
    }));
    try {
      const result = await precheckCustomerServiceQuestionBank(auth.user.tenant.id, auth.token, payload);
      setCustomerQuestionBankDraft((current) => ({
        ...current,
        status: result.can_import ? "ready" : "error",
        result,
        message: result.can_import
          ? `预检通过：${result.case_count} 题，可导入为客服评测集。`
          : `预检阻断：${result.validation_errors.join("；") || "请检查题库数量、敏感信息和重复编号。"}`
      }));
    } catch (error) {
      const message = error instanceof Error ? error.message : "客户题库预检失败";
      setCustomerQuestionBankDraft((current) => ({
        ...current,
        status: "error",
        message
      }));
    }
  }

  async function handleImportCustomerQuestionBank() {
    if (auth.status !== "ready" || !auth.token || !hasPermission(auth.user, PERMISSIONS.knowledgeManage)) {
      return;
    }
    const payload = parseCustomerQuestionBankDraft();
    if (!payload) {
      return;
    }
    setCustomerQuestionBankDraft((current) => ({
      ...current,
      status: "loading",
      message: "正在导入客户题库包"
    }));
    try {
      const result = await importCustomerServiceQuestionBank(auth.user.tenant.id, auth.token, payload);
      setCustomerQuestionBankDraft((current) => ({
        ...current,
        status: "ready",
        result,
        message: `已导入 ${result.case_count} 题，评测集 #${result.evaluation_set_id} 已创建。`
      }));
      await refreshKnowledgeEvaluations(auth.user.tenant.id, auth.token, true);
    } catch (error) {
      const message = error instanceof Error ? error.message : "客户题库导入失败";
      setCustomerQuestionBankDraft((current) => ({
        ...current,
        status: "error",
        message
      }));
    }
  }

  async function handleRollbackKnowledgeDocument(document: KnowledgeDocument) {
    if (auth.status !== "ready" || !auth.token || !hasPermission(auth.user, PERMISSIONS.knowledgeManage)) {
      return;
    }
    setKnowledgeWorkbench((current) => ({
      ...current,
      status: "loading",
      message: `正在回滚知识文档 #${document.id}`
    }));
    try {
      const result = await rollbackKnowledgeDocumentPublication(document.id, auth.token, {
        rollback_reason: "运营台人工触发：先退回草稿，暂停进入正式检索范围。"
      });
      await refreshKnowledgeDocuments(auth.user.tenant.id, auth.token, true);
      await refreshKnowledgeGaps(auth.user.tenant.id, auth.token, {
        status: knowledgeGapListView.status,
        query: knowledgeGapListView.query,
        page: knowledgeGapListView.page,
        pageSize: knowledgeGapListView.pageSize
      });
      setKnowledgeWorkbench((current) => ({
        ...current,
        status: "ready",
        message: `已回滚知识文档 #${document.id}，发布记录 #${result.id}；该文档已退出 active 检索范围。`
      }));
    } catch (error) {
      const message = error instanceof Error ? error.message : "知识文档回滚失败";
      setKnowledgeWorkbench((current) => ({
        ...current,
        status: "error",
        message
      }));
    }
  }

  async function handleRunKnowledgeEvaluation(setId: number) {
    if (auth.status !== "ready" || !auth.token || !hasPermission(auth.user, PERMISSIONS.knowledgeManage)) {
      return;
    }
    setKnowledgeEvaluation((current) => ({
      ...current,
      status: "loading",
      message: ""
    }));
    try {
      const run = await runKnowledgeEvaluationSet(setId, auth.token, {
        top_k: 5,
        low_confidence_threshold: 0.45
      });
      setKnowledgeEvaluation((current) => ({
        status: "ready",
        message: "",
        sets: current.sets,
        lastRun: run,
        runsBySet: {
          ...current.runsBySet,
          [setId]: [
            toKnowledgeEvaluationRunSummary(run),
            ...(current.runsBySet[setId] ?? []).filter((item) => item.id !== run.id)
          ].slice(0, 20)
        }
      }));
      if (canReadOpsMetrics(auth.user)) {
        await Promise.all([
          refreshRagCostGovernance(auth.user.tenant.id, auth.token),
          refreshLlmOpsReadiness(auth.user.tenant.id, auth.token)
        ]);
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : "运行知识评测失败";
      setKnowledgeEvaluation((current) => ({
        ...current,
        status: "error",
        message
      }));
    }
  }

  async function handleLoadKnowledgeEvaluationRun(runId: number) {
    if (auth.status !== "ready" || !auth.token || !hasPermission(auth.user, PERMISSIONS.knowledgeManage)) {
      return;
    }
    setKnowledgeEvaluation((current) => ({
      ...current,
      status: "loading",
      message: ""
    }));
    try {
      const run = await getKnowledgeEvaluationRun(runId, auth.token);
      setKnowledgeEvaluation((current) => ({
        ...current,
        status: "ready",
        message: "",
        lastRun: run
      }));
    } catch (error) {
      const message = error instanceof Error ? error.message : "读取评测运行详情失败";
      setKnowledgeEvaluation((current) => ({
        ...current,
        status: "error",
        message
      }));
    }
  }

  async function handleLabelEvaluationRunCaseFactuality(runCase: KnowledgeEvaluationRunCase, statusValue: FactualityLabelStatus) {
    if (auth.status !== "ready" || !auth.token || !hasPermission(auth.user, PERMISSIONS.knowledgeManage)) {
      return;
    }
    setKnowledgeEvaluation((current) => ({
      ...current,
      status: "loading",
      message: "正在保存人工事实性标签"
    }));
    try {
      const answerQuality = readRecordPayload(runCase.result_payload, "answer_quality");
      const result = await labelKnowledgeEvaluationRunCaseFactuality(runCase.id, auth.token, {
        final_answer_factuality_status: statusValue,
        citation_sufficient: readBooleanPayload(answerQuality ?? {}, "citation_sufficient") ?? undefined,
        forbidden_commitment_passed: readBooleanPayload(answerQuality ?? {}, "forbidden_commitment_passed") ?? undefined,
        handoff_correct: readBooleanPayload(answerQuality ?? {}, "handoff_correct") ?? undefined
      });
      const updatedRun = result.updated_run;
      setKnowledgeEvaluation((current) => ({
        ...current,
        status: "ready",
        message: `已标注 ${result.final_answer_factuality_labeled_cases}/${result.total_cases} 题；当前人工事实性 ${result.final_answer_factuality_rate === null ? "未评" : formatPercent(result.final_answer_factuality_rate)}`,
        lastRun: updatedRun,
        runsBySet: {
          ...current.runsBySet,
          [updatedRun.evaluation_set_id]: [
            toKnowledgeEvaluationRunSummary(updatedRun),
            ...(current.runsBySet[updatedRun.evaluation_set_id] ?? []).filter((item) => item.id !== updatedRun.id)
          ].slice(0, 20)
        }
      }));
      void refreshMonthlyQualityReview(auth.user.tenant.id, auth.token);
      void refreshCustomerQualityReport(auth.user.tenant.id, auth.token);
    } catch (error) {
      const message = error instanceof Error ? error.message : "保存人工事实性标签失败";
      setKnowledgeEvaluation((current) => ({
        ...current,
        status: "error",
        message
      }));
    }
  }

  async function handleCaptureEvaluationRunCaseFinalAnswerSample(runCase: KnowledgeEvaluationRunCase, finalAnswerText: string) {
    if (auth.status !== "ready" || !auth.token || !hasPermission(auth.user, PERMISSIONS.knowledgeManage)) {
      return;
    }
    const trimmedText = finalAnswerText.trim();
    if (!trimmedText) {
      setKnowledgeEvaluation((current) => ({
        ...current,
        status: "error",
        message: "请先填写最终客服回复样本"
      }));
      return;
    }
    setKnowledgeEvaluation((current) => ({
      ...current,
      status: "loading",
      message: "正在保存最终客服回复样本"
    }));
    try {
      const citationUris = extractCitationUrisFromRunCase(runCase);
      const result = await captureKnowledgeEvaluationRunCaseFinalAnswerSample(runCase.id, auth.token, {
        final_answer_text: trimmedText,
        final_answer_source: "manual_capture",
        citation_uris: citationUris,
        answer_author: "本地客服工作台"
      });
      const updatedRun = result.updated_run;
      setKnowledgeEvaluation((current) => ({
        ...current,
        status: "ready",
        message: `已采样 ${result.final_answer_sampled_cases}/${result.total_cases} 题最终回复；覆盖率 ${formatPercent(result.final_answer_sample_coverage)}`,
        lastRun: updatedRun,
        runsBySet: {
          ...current.runsBySet,
          [updatedRun.evaluation_set_id]: [
            toKnowledgeEvaluationRunSummary(updatedRun),
            ...(current.runsBySet[updatedRun.evaluation_set_id] ?? []).filter((item) => item.id !== updatedRun.id)
          ].slice(0, 20)
        }
      }));
    } catch (error) {
      const message = error instanceof Error ? error.message : "保存最终客服回复样本失败";
      setKnowledgeEvaluation((current) => ({
        ...current,
        status: "error",
        message
      }));
    }
  }

  async function handleBatchLabelSampledFactuality(run: KnowledgeEvaluationRun, statusValue: FactualityLabelStatus) {
    if (auth.status !== "ready" || !auth.token || !hasPermission(auth.user, PERMISSIONS.knowledgeManage)) {
      return;
    }
    const sampledCases = run.case_results.filter(hasFinalAnswerSample);
    if (sampledCases.length === 0) {
      setKnowledgeEvaluation((current) => ({
        ...current,
        status: "error",
        message: "当前运行还没有最终回复样本，不能批量标注事实性"
      }));
      return;
    }
    setKnowledgeEvaluation((current) => ({
      ...current,
      status: "loading",
      message: "正在批量保存人工事实性标签"
    }));
    try {
      const result = await batchLabelKnowledgeEvaluationRunCaseFactuality(run.id, auth.token, {
        labels: sampledCases.map((runCase) => {
          const answerQuality = readRecordPayload(runCase.result_payload, "answer_quality");
          return {
            evaluation_run_case_id: runCase.id,
            final_answer_factuality_status: statusValue,
            citation_sufficient: readBooleanPayload(answerQuality ?? {}, "citation_sufficient") ?? undefined,
            forbidden_commitment_passed: readBooleanPayload(answerQuality ?? {}, "forbidden_commitment_passed") ?? undefined,
            handoff_correct: readBooleanPayload(answerQuality ?? {}, "handoff_correct") ?? undefined,
            reviewer_notes: `批量标注：${formatFactualityLabelStatus(statusValue)}`
          };
        })
      });
      const updatedRun = result.updated_run;
      setKnowledgeEvaluation((current) => ({
        ...current,
        status: "ready",
        message: `已批量标注 ${result.labeled_cases} 题；当前人工事实性 ${result.final_answer_factuality_rate === null ? "未评" : formatPercent(result.final_answer_factuality_rate)}`,
        lastRun: updatedRun,
        runsBySet: {
          ...current.runsBySet,
          [updatedRun.evaluation_set_id]: [
            toKnowledgeEvaluationRunSummary(updatedRun),
            ...(current.runsBySet[updatedRun.evaluation_set_id] ?? []).filter((item) => item.id !== updatedRun.id)
          ].slice(0, 20)
        }
      }));
      void refreshMonthlyQualityReview(auth.user.tenant.id, auth.token);
      void refreshCustomerQualityReport(auth.user.tenant.id, auth.token);
    } catch (error) {
      const message = error instanceof Error ? error.message : "批量保存人工事实性标签失败";
      setKnowledgeEvaluation((current) => ({
        ...current,
        status: "error",
        message
      }));
    }
  }

  async function handleExportKnowledgeEvaluationRunReport(runId: number, reportFormat: "markdown" | "csv") {
    if (auth.status !== "ready" || !auth.token || !hasPermission(auth.user, PERMISSIONS.knowledgeManage)) {
      return;
    }
    setKnowledgeEvaluation((current) => ({
      ...current,
      status: "loading",
      message: "正在生成脱敏评测报告"
    }));
    try {
      const report = await exportKnowledgeEvaluationRunReport(runId, auth.token, reportFormat);
      downloadKnowledgeEvaluationReport(report);
      setKnowledgeEvaluation((current) => ({
        ...current,
        status: "ready",
        message: `已生成 ${report.filename}`
      }));
    } catch (error) {
      const message = error instanceof Error ? error.message : "导出脱敏评测报告失败";
      setKnowledgeEvaluation((current) => ({
        ...current,
        status: "error",
        message
      }));
    }
  }

  async function handleExportFinalAnswerLabels(runId: number) {
    if (auth.status !== "ready" || !auth.token || !hasPermission(auth.user, PERMISSIONS.knowledgeManage)) {
      return;
    }
    setKnowledgeEvaluation((current) => ({
      ...current,
      status: "loading",
      message: "正在生成最终回复样本与人工标签 CSV"
    }));
    try {
      const report = await exportKnowledgeEvaluationRunFinalAnswerLabels(runId, auth.token);
      downloadTextFile(report.body, report.filename, report.content_type);
      setFinalAnswerLabelImportDraft({
        text: report.body,
        result: null,
        status: "ready",
        message: `已生成 ${report.row_count} 行 CSV，可离线标注后再粘贴导入。`
      });
      setKnowledgeEvaluation((current) => ({
        ...current,
        status: "ready",
        message: `已生成 ${report.filename}`
      }));
    } catch (error) {
      const message = error instanceof Error ? error.message : "导出最终回复样本与标签失败";
      setKnowledgeEvaluation((current) => ({
        ...current,
        status: "error",
        message
      }));
    }
  }

  async function handlePrecheckFinalAnswerLabels(runId: number) {
    if (auth.status !== "ready" || !auth.token || !hasPermission(auth.user, PERMISSIONS.knowledgeManage)) {
      return;
    }
    if (!finalAnswerLabelImportDraft.text.trim()) {
      setFinalAnswerLabelImportDraft((current) => ({
        ...current,
        status: "error",
        message: "请先粘贴最终回复样本与人工标签 CSV"
      }));
      return;
    }
    setFinalAnswerLabelImportDraft((current) => ({
      ...current,
      status: "loading",
      message: "正在预检 CSV"
    }));
    try {
      const result = await importKnowledgeEvaluationRunFinalAnswerLabels(runId, auth.token, {
        content: finalAnswerLabelImportDraft.text,
        dry_run: true
      });
      setFinalAnswerLabelImportDraft((current) => ({
        ...current,
        status: result.validation_errors.length > 0 ? "error" : "ready",
        result,
        message:
          result.validation_errors.length > 0
            ? `预检发现 ${result.validation_errors.length} 个问题`
            : `预检通过：匹配 ${result.matched_rows}/${result.total_rows} 行，样本 ${result.sample_rows} 行，标签 ${result.label_rows} 行。`
      }));
    } catch (error) {
      const message = error instanceof Error ? error.message : "预检最终回复样本与标签失败";
      setFinalAnswerLabelImportDraft((current) => ({
        ...current,
        status: "error",
        message
      }));
    }
  }

  async function handleImportFinalAnswerLabels(runId: number) {
    if (auth.status !== "ready" || !auth.token || !hasPermission(auth.user, PERMISSIONS.knowledgeManage)) {
      return;
    }
    if (!finalAnswerLabelImportDraft.text.trim()) {
      setFinalAnswerLabelImportDraft((current) => ({
        ...current,
        status: "error",
        message: "请先粘贴最终回复样本与人工标签 CSV"
      }));
      return;
    }
    setFinalAnswerLabelImportDraft((current) => ({
      ...current,
      status: "loading",
      message: "正在导入 CSV"
    }));
    try {
      const result = await importKnowledgeEvaluationRunFinalAnswerLabels(runId, auth.token, {
        content: finalAnswerLabelImportDraft.text,
        dry_run: false
      });
      setFinalAnswerLabelImportDraft((current) => ({
        ...current,
        status: result.imported ? "ready" : "error",
        result,
        message: result.imported
          ? `已导入：样本 ${result.sample_rows} 行，标签 ${result.label_rows} 行。`
          : `导入未执行：请先修正 ${result.validation_errors.length} 个问题。`
      }));
      if (result.updated_run) {
        const updatedRun = result.updated_run;
        setKnowledgeEvaluation((current) => ({
          ...current,
          status: "ready",
          message: `已导入最终回复样本与人工标签：${result.sample_rows} 条样本，${result.label_rows} 条标签。`,
          lastRun: updatedRun,
          runsBySet: {
            ...current.runsBySet,
            [updatedRun.evaluation_set_id]: [
              toKnowledgeEvaluationRunSummary(updatedRun),
              ...(current.runsBySet[updatedRun.evaluation_set_id] ?? []).filter((item) => item.id !== updatedRun.id)
            ].slice(0, 20)
          }
        }));
        void refreshMonthlyQualityReview(auth.user.tenant.id, auth.token);
        void refreshCustomerQualityReport(auth.user.tenant.id, auth.token);
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : "导入最终回复样本与标签失败";
      setFinalAnswerLabelImportDraft((current) => ({
        ...current,
        status: "error",
        message
      }));
    }
  }

  async function handleReviewApprove(
    item: HumanReviewInboxItem,
    options?: { finalReply?: string; resolutionNote?: string }
  ) {
    if (
      auth.status !== "ready" ||
      !auth.token ||
      !hasPermission(auth.user, PERMISSIONS.conversationManage) ||
      !hasPermission(auth.user, PERMISSIONS.outboxDraftManage)
    ) {
      return;
    }
    const finalReply = (options?.finalReply ?? item.draft_reply).trim();
    if (!finalReply) {
      setReviewInbox((current) => ({
        status: "error",
        message: "当前审核任务没有草稿回复，暂不能直接生成发送草稿",
        items: "items" in current ? current.items : []
      }));
      return;
    }
    setReviewInbox((current) => ({
      status: "loading",
      items: "items" in current ? current.items : []
    }));
    try {
      await resolveHumanReviewTask(item.id, auth.token, {
        decision: "approved",
        final_reply: finalReply,
        resolution_note: options?.resolutionNote?.trim() || "前端工作台批准并进入发送草稿"
      });
      await createOutboxDraftFromReview(item.id, auth.token);
      await Promise.all([
        refreshReviewInbox(auth.user.tenant.id, auth.token),
        refreshOutbox(auth.user.tenant.id, auth.token),
        refreshDeliveryQueue(auth.user.tenant.id, auth.token),
        refreshFailureReviews(auth.user.tenant.id, auth.token)
      ]);
    } catch (error) {
      const message = error instanceof Error ? error.message : "批准审核任务失败";
      setReviewInbox((current) => ({
        status: "error",
        message,
        items: "items" in current ? current.items : []
      }));
    }
  }

  async function handleReviewReject(item: HumanReviewInboxItem) {
    if (auth.status !== "ready" || !auth.token || !hasPermission(auth.user, PERMISSIONS.conversationManage)) {
      return;
    }
    setReviewInbox((current) => ({
      status: "loading",
      items: "items" in current ? current.items : []
    }));
    try {
      await resolveHumanReviewTask(item.id, auth.token, {
        decision: "rejected",
        resolution_note: "前端工作台拒绝该回复草稿"
      });
      await refreshReviewInbox(auth.user.tenant.id, auth.token);
    } catch (error) {
      const message = error instanceof Error ? error.message : "拒绝审核任务失败";
      setReviewInbox((current) => ({
        status: "error",
        message,
        items: "items" in current ? current.items : []
      }));
    }
  }

  async function handleConfirmDraft(draftId: number) {
    if (auth.status !== "ready" || !auth.token || !hasPermission(auth.user, PERMISSIONS.outboxDraftManage)) {
      return;
    }
    setOutbox((current) => ({
      status: "loading",
      drafts: "drafts" in current ? current.drafts : [],
      attemptsByDraft: "attemptsByDraft" in current ? current.attemptsByDraft : {}
    }));
    try {
      await confirmOutboxDraft(draftId, auth.token);
      await Promise.all([
        refreshOutbox(auth.user.tenant.id, auth.token),
        refreshDeliveryQueue(auth.user.tenant.id, auth.token),
        refreshFailureReviews(auth.user.tenant.id, auth.token)
      ]);
    } catch (error) {
      const message = error instanceof Error ? error.message : "确认待发送失败";
      setOutbox((current) => ({
        status: "error",
        message,
        drafts: "drafts" in current ? current.drafts : [],
        attemptsByDraft: "attemptsByDraft" in current ? current.attemptsByDraft : {}
      }));
    }
  }

  async function handleDryRun(draftId: number) {
    if (auth.status !== "ready" || !auth.token || !hasPermission(auth.user, PERMISSIONS.outboxSendAttemptManage)) {
      return;
    }
    setOutbox((current) => ({
      status: "loading",
      drafts: "drafts" in current ? current.drafts : [],
      attemptsByDraft: "attemptsByDraft" in current ? current.attemptsByDraft : {}
    }));
    try {
      await createDryRunSendAttempt(draftId, auth.token);
      await Promise.all([
        refreshOutbox(auth.user.tenant.id, auth.token),
        refreshDeliveryQueue(auth.user.tenant.id, auth.token),
        refreshFailureReviews(auth.user.tenant.id, auth.token)
      ]);
    } catch (error) {
      const message = error instanceof Error ? error.message : "模拟发送失败";
      setOutbox((current) => ({
        status: "error",
        message,
        drafts: "drafts" in current ? current.drafts : [],
        attemptsByDraft: "attemptsByDraft" in current ? current.attemptsByDraft : {}
      }));
    }
  }

  async function handleConnectorPlan(draft: OutboxDraft) {
    if (auth.status !== "ready" || !auth.token || !hasPermission(auth.user, PERMISSIONS.outboxSendPlanManage)) {
      return;
    }
    setOutbox((current) => ({
      status: "loading",
      drafts: "drafts" in current ? current.drafts : [],
      attemptsByDraft: "attemptsByDraft" in current ? current.attemptsByDraft : {}
    }));
    try {
      if (hasPermission(auth.user, PERMISSIONS.channelConnectorManage)) {
        await ensureNoopChannelConnector(draft.channel_id, auth.token);
      }
      await createConnectorSendPlan(draft.id, auth.token);
      await Promise.all([
        refreshOutbox(auth.user.tenant.id, auth.token),
        refreshDeliveryQueue(auth.user.tenant.id, auth.token),
        refreshFailureReviews(auth.user.tenant.id, auth.token)
      ]);
    } catch (error) {
      const message = error instanceof Error ? error.message : "生成官方渠道发送计划失败";
      setOutbox((current) => ({
        status: "error",
        message,
        drafts: "drafts" in current ? current.drafts : [],
        attemptsByDraft: "attemptsByDraft" in current ? current.attemptsByDraft : {}
      }));
    }
  }

  async function handleRunWorker() {
    if (auth.status !== "ready" || !auth.token || !hasPermission(auth.user, PERMISSIONS.outboxSendAttemptManage)) {
      return;
    }
    setOutbox((current) => ({
      status: "loading",
      drafts: "drafts" in current ? current.drafts : [],
      attemptsByDraft: "attemptsByDraft" in current ? current.attemptsByDraft : {}
    }));
    try {
      const result = await runOutboxWorker(auth.user.tenant.id, auth.token);
      setLastWorkerRun(result);
      await Promise.all([
        refreshOutbox(auth.user.tenant.id, auth.token),
        refreshDeliveryQueue(auth.user.tenant.id, auth.token),
        refreshFailureReviews(auth.user.tenant.id, auth.token)
      ]);
    } catch (error) {
      const message = error instanceof Error ? error.message : "发送检查失败";
      setOutbox((current) => ({
        status: "error",
        message,
        drafts: "drafts" in current ? current.drafts : [],
        attemptsByDraft: "attemptsByDraft" in current ? current.attemptsByDraft : {}
      }));
    }
  }

  async function handleCreateDeliveryJob(draft: OutboxDraft) {
    if (auth.status !== "ready" || !auth.token || !hasPermission(auth.user, PERMISSIONS.outboxDeliveryJobManage)) {
      return;
    }
    setDeliveryQueue((current) => ({
      status: "loading",
      jobs: "jobs" in current ? current.jobs : []
    }));
    try {
      if (hasPermission(auth.user, PERMISSIONS.channelConnectorManage)) {
        await ensureNoopChannelConnector(draft.channel_id, auth.token);
      }
      await createOutboxDeliveryJob(draft.id, auth.token);
      await Promise.all([
        refreshOutbox(auth.user.tenant.id, auth.token),
        refreshDeliveryQueue(auth.user.tenant.id, auth.token),
        refreshFailureReviews(auth.user.tenant.id, auth.token)
      ]);
    } catch (error) {
      const message = error instanceof Error ? error.message : "创建发送队列任务失败";
      setDeliveryQueue((current) => ({
        status: "error",
        message,
        jobs: "jobs" in current ? current.jobs : []
      }));
    }
  }

  async function handleRunDeliveryQueue() {
    if (auth.status !== "ready" || !auth.token || !hasPermission(auth.user, PERMISSIONS.outboxDeliveryJobManage)) {
      return;
    }
    setDeliveryQueue((current) => ({
      status: "loading",
      jobs: "jobs" in current ? current.jobs : []
    }));
    try {
      const result = await runOutboxDeliveryQueue(auth.user.tenant.id, auth.token);
      setLastDeliveryQueueRun(result);
      await Promise.all([
        refreshOutbox(auth.user.tenant.id, auth.token),
        refreshDeliveryQueue(auth.user.tenant.id, auth.token),
        refreshFailureReviews(auth.user.tenant.id, auth.token)
      ]);
    } catch (error) {
      const message = error instanceof Error ? error.message : "运行发送队列失败";
      setDeliveryQueue((current) => ({
        status: "error",
        message,
        jobs: "jobs" in current ? current.jobs : []
      }));
    }
  }

  async function handleRunInboundWorker() {
    if (auth.status !== "ready" || !auth.token || !canRunInboundWorker(auth.user)) {
      return;
    }
    setReviewInbox((current) => ({
      status: "loading",
      items: "items" in current ? current.items : []
    }));
    try {
      const result = await runTrustedInboundWorker(auth.user.tenant.id, auth.token);
      setLastInboundWorkerRun(result);
      await refreshReviewInbox(auth.user.tenant.id, auth.token);
    } catch (error) {
      const message = error instanceof Error ? error.message : "入站编排失败";
      setReviewInbox((current) => ({
        status: "error",
        message,
        items: "items" in current ? current.items : []
      }));
    }
  }

  async function handleConfigureChannelAccount(channelId: number, payload: ChannelAccountPayload) {
    if (auth.status !== "ready" || !auth.token) {
      throw new Error("需要正式登录后才能配置渠道账号");
    }
    const account = await configureChannelAccount(channelId, auth.token, payload);
    await refreshChannelAccounts(auth.user.tenant.id, auth.token);
    return account;
  }

  async function handleDeleteChannelAccountConnection(accountId: number) {
    if (auth.status !== "ready" || !auth.token || !hasPermission(auth.user, PERMISSIONS.channelConnectorManage)) {
      throw new Error("当前账号无权删除渠道接入");
    }
    setChannelConnectorSelfService((current) => ({ ...current, status: "loading", message: "正在删除渠道接入" }));
    try {
      const result = await deleteChannelAccountConnection(accountId, auth.token);
      await refreshChannelAccounts(auth.user.tenant.id, auth.token);
      await refreshConversationInbox(auth.user.tenant.id, auth.token, conversationInboxView, conversationInboxFilters);
      setChannelConnectorSelfService((current) => ({
        ...current,
        config: result.connector_disabled ? null : current.config,
        secretStatus: result.connector_disabled ? null : current.secretStatus,
        verification: null,
        status: "ready",
        message: "渠道接入已删除，后续消息不会进入工作台。"
      }));
      return result;
    } catch (error) {
      const message = error instanceof Error ? error.message : "删除渠道接入失败";
      setChannelConnectorSelfService((current) => ({ ...current, status: "error", message }));
      throw error;
    }
  }

  async function handleConfigureChannelConnector(channelId: number, provider: string, publicConfig: Record<string, unknown> = {}) {
    if (auth.status !== "ready" || !auth.token || !hasPermission(auth.user, PERMISSIONS.channelConnectorManage)) {
      throw new Error("当前账号无权配置渠道连接器");
    }
    setChannelConnectorSelfService((current) => ({
      ...current,
      status: "loading",
      message: "正在保存连接器配置"
    }));
    try {
      const normalizedProvider = provider || "website";
      const providerLabels: Record<string, string> = {
        website: "网站",
        wechat_kf: "微信客服",
        wecom: "企业微信",
        wechat_official_account: "微信公众号",
        wechat_official: "微信公众号",
        wechat_miniapp: "微信小程序"
      };
      const config = await configureChannelConnector(channelId, auth.token, {
        provider: normalizedProvider,
        mode: "noop",
        status: "draft",
        display_name: providerLabels[normalizedProvider] ?? normalizedProvider,
        capabilities: ["receive_inbound", "draft_reply"],
        public_config: {
          self_service_configured: true,
          external_write: "disabled",
          configured_from: "channel_console",
          ...publicConfig
        },
        webhook_path: `/api/webhooks/${normalizedProvider.replace(/_/g, "-")}/channels/${channelId}`,
        signature_mode: getConnectorSignatureMode(normalizedProvider)
      });
      setChannelConnectorSelfService((current) => ({
        ...current,
        config,
        status: "ready",
        message: "连接器配置已保存，真实外发仍关闭。"
      }));
      return config;
    } catch (error) {
      const message = error instanceof Error ? error.message : "保存连接器配置失败";
      setChannelConnectorSelfService((current) => ({ ...current, status: "error", message }));
      throw error;
    }
  }

  async function handleStartChannelConnectorAuthorization(channelId: number, provider: string, connectMode: "qr" | "manual" = "qr") {
    if (auth.status !== "ready" || !auth.token || !hasPermission(auth.user, PERMISSIONS.channelConnectorManage)) {
      throw new Error("当前账号无权发起渠道授权");
    }
    setChannelConnectorSelfService((current) => ({
      ...current,
      status: "loading",
      message: connectMode === "qr" ? "正在创建扫码授权会话" : "正在记录手动接入会话"
    }));
    try {
      const authorization = await startChannelConnectorAuthorization(channelId, auth.token, {
        provider,
        connect_mode: connectMode,
        redirect_uri: typeof window !== "undefined" ? window.location.href : ""
      });
      setChannelConnectorSelfService((current) => ({
        ...current,
        authorization,
        status: "ready",
        message: connectMode === "qr" ? "扫码授权入口已生成，完成授权后请回到工作台验证配置。" : "手动接入会话已记录。"
      }));
      return authorization;
    } catch (error) {
      const message = error instanceof Error ? error.message : "创建渠道授权会话失败";
      setChannelConnectorSelfService((current) => ({ ...current, status: "error", message }));
      throw error;
    }
  }

  async function handleUpsertChannelConnectorSecrets(channelId: number, secrets: Record<string, string>) {
    if (auth.status !== "ready" || !auth.token || !hasPermission(auth.user, PERMISSIONS.channelConnectorManage)) {
      throw new Error("当前账号无权配置渠道密钥");
    }
    setChannelConnectorSelfService((current) => ({
      ...current,
      status: "loading",
      message: "正在保存密钥状态"
    }));
    try {
      const secretStatus = await upsertChannelConnectorSecrets(channelId, auth.token, { secrets });
      setChannelConnectorSelfService((current) => ({
        ...current,
        secretStatus,
        status: "ready",
        message: "密钥已保存，前端不会回显明文。"
      }));
      return secretStatus;
    } catch (error) {
      const message = error instanceof Error ? error.message : "保存渠道密钥失败";
      setChannelConnectorSelfService((current) => ({ ...current, status: "error", message }));
      throw error;
    }
  }

  async function handleDeleteChannelConnectorSecrets(channelId: number) {
    if (auth.status !== "ready" || !auth.token || !hasPermission(auth.user, PERMISSIONS.channelConnectorManage)) {
      throw new Error("当前账号无权清空渠道密钥");
    }
    setChannelConnectorSelfService((current) => ({ ...current, status: "loading", message: "正在清空密钥" }));
    try {
      const secretStatus = await deleteChannelConnectorSecrets(channelId, auth.token);
      setChannelConnectorSelfService((current) => ({
        ...current,
        secretStatus,
        verification: null,
        status: "ready",
        message: "密钥已清空。"
      }));
      return secretStatus;
    } catch (error) {
      const message = error instanceof Error ? error.message : "清空渠道密钥失败";
      setChannelConnectorSelfService((current) => ({ ...current, status: "error", message }));
      throw error;
    }
  }

  async function handleVerifyChannelConnector(channelId: number) {
    if (auth.status !== "ready" || !auth.token || !hasPermission(auth.user, PERMISSIONS.channelConnectorManage)) {
      throw new Error("当前账号无权验证渠道配置");
    }
    setChannelConnectorSelfService((current) => ({ ...current, status: "loading", message: "正在验证渠道配置" }));
    try {
      const verification = await verifyChannelConnector(channelId, auth.token);
      setChannelConnectorSelfService((current) => ({
        ...current,
        verification,
        status: verification.status === "verified" ? "ready" : "error",
        message: verification.status === "verified"
          ? "配置完整，默认仍不真实外发。"
          : `配置未完成：${verification.missing_fields.join("、") || verification.status}`
      }));
      return verification;
    } catch (error) {
      const message = error instanceof Error ? error.message : "验证渠道配置失败";
      setChannelConnectorSelfService((current) => ({ ...current, status: "error", message }));
      throw error;
    }
  }

  async function handleCreateAccountUser(payload: {
    name: string;
    email: string;
    password: string;
    roleId: number | null;
  }) {
    if (auth.status !== "ready" || !auth.token || !canManageAccounts(auth.user)) {
      throw new Error("当前账号无权管理本地人员");
    }
    setAccountManagement((current) => ({
      status: "loading",
      users: current.users,
      roles: current.roles
    }));
    try {
      const user = await createTenantUser(auth.user.tenant.id, auth.token, {
        name: payload.name,
        email: payload.email,
        password: payload.password,
        status: "active"
      });
      if (payload.roleId) {
        await assignUserRole(user.id, auth.token, { role_id: payload.roleId });
      }
      await refreshAccountManagement(auth.user.tenant.id, auth.token);
      setAccountManagement((current) => ({
        ...current,
        status: "ready",
        message: "人员账号已创建，密码不会在系统内明文留存"
      }));
    } catch (error) {
      const message = error instanceof Error ? error.message : "创建人员账号失败";
      setAccountManagement((current) => ({
        status: "error",
        message,
        users: current.users,
        roles: current.roles
      }));
      throw error;
    }
  }

  async function handleUpdateAccountUserStatus(user: AccountUser, status: "active" | "inactive") {
    if (auth.status !== "ready" || !auth.token || !canManageAccounts(auth.user)) {
      throw new Error("当前账号无权管理本地人员");
    }
    setAccountManagement((current) => ({
      status: "loading",
      users: current.users,
      roles: current.roles
    }));
    try {
      await updateUserStatus(user.id, auth.token, status);
      await refreshAccountManagement(auth.user.tenant.id, auth.token);
      setAccountManagement((current) => ({
        ...current,
        status: "ready",
        message: status === "active" ? "人员账号已启用" : "人员账号已停用，未过期登录会话已撤销"
      }));
    } catch (error) {
      const message = error instanceof Error ? error.message : "更新人员状态失败";
      setAccountManagement((current) => ({
        status: "error",
        message,
        users: current.users,
        roles: current.roles
      }));
      throw error;
    }
  }

  async function handleResetAccountUserPassword(user: AccountUser, newPassword: string) {
    if (auth.status !== "ready" || !auth.token || !canManageAccounts(auth.user)) {
      throw new Error("当前账号无权管理本地人员");
    }
    setAccountManagement((current) => ({
      status: "loading",
      users: current.users,
      roles: current.roles
    }));
    try {
      await resetUserPassword(user.id, auth.token, newPassword);
      await refreshAccountManagement(auth.user.tenant.id, auth.token);
      setAccountManagement((current) => ({
        ...current,
        status: "ready",
        message: "密码已重置，该人员需要使用新密码重新登录"
      }));
    } catch (error) {
      const message = error instanceof Error ? error.message : "重置密码失败";
      setAccountManagement((current) => ({
        status: "error",
        message,
        users: current.users,
        roles: current.roles
      }));
      throw error;
    }
  }

  async function handleExportDiagnosticBundle() {
    if (auth.status !== "ready" || !auth.token || !canReadOpsMetrics(auth.user)) {
      throw new Error("当前账号无权导出本地诊断包");
    }
    setDiagnosticExport((current) => ({
      status: "loading",
      message: "正在生成本地诊断包",
      lastFilename: current.lastFilename
    }));
    try {
      const bundle = await getDiagnosticBundle(auth.user.tenant.id, auth.token);
      downloadDiagnosticBundle(bundle);
      setDiagnosticExport({
        status: "ready",
        message: "诊断包已生成并下载",
        lastFilename: bundle.filename
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : "生成诊断包失败";
      setDiagnosticExport((current) => ({
        status: "error",
        message,
        lastFilename: current.lastFilename
      }));
      throw error;
    }
  }

  async function handleCreateDiagnosticUploadPackage() {
    if (auth.status !== "ready" || !auth.token || !canReadOpsMetrics(auth.user)) {
      throw new Error("当前账号无权生成授权上传包");
    }
    setDiagnosticExport((current) => ({
      status: "loading",
      message: "正在生成授权上传包",
      lastFilename: current.lastFilename
    }));
    try {
      const uploadPackage = await createDiagnosticUploadPackage(auth.user.tenant.id, auth.token, {
        authorization_note: "客户管理员确认授权上传本次脱敏诊断包。"
      });
      downloadDiagnosticUploadPackage(uploadPackage);
      setDiagnosticExport({
        status: "ready",
        message: "授权上传包已生成并下载",
        lastFilename: uploadPackage.filename
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : "生成授权上传包失败";
      setDiagnosticExport((current) => ({
        status: "error",
        message,
        lastFilename: current.lastFilename
      }));
      throw error;
    }
  }

  async function handleCreateDiagnosticIntakeRecord(uploadPackageText: string) {
    if (auth.status !== "ready" || !auth.token || !canReadOpsMetrics(auth.user)) {
      throw new Error("当前账号无权登记售后接收记录");
    }
    let uploadPackage: Record<string, unknown>;
    try {
      uploadPackage = JSON.parse(uploadPackageText) as Record<string, unknown>;
    } catch {
      throw new Error("请粘贴有效的授权上传包 JSON。");
    }
    setDiagnosticIntake((current) => ({
      status: "loading",
      message: "正在登记售后接收记录",
      records: current.records
    }));
    try {
      const record = await createDiagnosticIntakeRecord(auth.user.tenant.id, auth.token, {
        upload_package: uploadPackage,
        source_channel: "manual_transfer",
        processing_note: "客户主动提交脱敏授权上传包。"
      });
      if (canManageSignedUpdates(auth.user)) {
        await refreshLocalMaintenanceReadiness(auth.user.tenant.id, auth.token);
      }
      setDiagnosticIntake((current) => ({
        status: "ready",
        message: record.status === "rejected" ? "上传包已拒收并记录原因" : "上传包已接收并登记",
        records: [record, ...current.records.filter((item) => item.id !== record.id)]
      }));
    } catch (error) {
      const message = error instanceof Error ? error.message : "登记售后接收记录失败";
      setDiagnosticIntake((current) => ({
        status: "error",
        message,
        records: current.records
      }));
      throw error;
    }
  }

  async function handleUpdateDiagnosticIntakeRecord(record: DiagnosticIntakeRecord, status: string, note: string) {
    if (auth.status !== "ready" || !auth.token || !canManageSignedUpdates(auth.user)) {
      throw new Error("当前账号无权更新售后接收状态");
    }
    setDiagnosticIntake((current) => ({
      status: "loading",
      message: "正在更新售后接收状态",
      records: current.records
    }));
    try {
      const updated = await updateDiagnosticIntakeRecord(auth.user.tenant.id, auth.token, record.id, {
        status,
        processing_note: note
      });
      setDiagnosticIntake((current) => ({
        status: "ready",
        message: "售后接收状态已更新",
        records: current.records.map((item) => (item.id === updated.id ? updated : item))
      }));
    } catch (error) {
      const message = error instanceof Error ? error.message : "更新售后接收状态失败";
      setDiagnosticIntake((current) => ({
        status: "error",
        message,
        records: current.records
      }));
      throw error;
    }
  }

  async function handleDownloadDiagnosticIntakeRecord(record: DiagnosticIntakeRecord) {
    if (auth.status !== "ready" || !auth.token || !canReadOpsMetrics(auth.user)) {
      throw new Error("当前账号无权下载售后接收包");
    }
    const download = await downloadDiagnosticIntakeRecord(auth.user.tenant.id, auth.token, record.id);
    downloadDiagnosticIntakePackage(download);
  }

  async function handleCreateDiagnosticRemediationRequest(record: DiagnosticIntakeRecord) {
    if (auth.status !== "ready" || !auth.token || !canManageSignedUpdates(auth.user)) {
      throw new Error("当前账号无权生成售后处理单");
    }
    setDiagnosticRemediation((current) => ({
      status: "loading",
      message: "正在生成售后处理单",
      requests: current.requests
    }));
    try {
      const request = await createDiagnosticRemediationRequest(auth.user.tenant.id, auth.token, record.id, {
        request_type: "knowledge_or_strategy_update",
        title: `售后处理单：${record.package_filename}`,
        summary: "根据客户主动授权上传的脱敏诊断包生成处理建议；不远程控制客户电脑，不直接应用更新。"
      });
      await refreshLocalMaintenanceReadiness(auth.user.tenant.id, auth.token);
      setDiagnosticRemediation((current) => ({
        status: "ready",
        message: "售后处理单已生成",
        requests: [request, ...current.requests.filter((item) => item.id !== request.id)]
      }));
      setDiagnosticIntake((current) => ({
        status: current.status,
        message: current.message,
        records: current.records.map((item) =>
          item.id === record.id ? { ...item, status: item.status === "received" ? "in_review" : item.status } : item
        )
      }));
    } catch (error) {
      const message = error instanceof Error ? error.message : "生成售后处理单失败";
      setDiagnosticRemediation((current) => ({
        status: "error",
        message,
        requests: current.requests
      }));
      throw error;
    }
  }

  async function handleUpdateDiagnosticRemediationRequest(request: DiagnosticRemediationRequest, status: string) {
    if (auth.status !== "ready" || !auth.token || !canManageSignedUpdates(auth.user)) {
      throw new Error("当前账号无权更新售后处理单");
    }
    setDiagnosticRemediation((current) => ({
      status: "loading",
      message: "正在更新售后处理单",
      requests: current.requests
    }));
    try {
      const updated = await updateDiagnosticRemediationRequest(auth.user.tenant.id, auth.token, request.id, {
        status,
        summary: request.summary
      });
      setDiagnosticRemediation((current) => ({
        status: "ready",
        message: "售后处理单状态已更新",
        requests: current.requests.map((item) => (item.id === updated.id ? updated : item))
      }));
    } catch (error) {
      const message = error instanceof Error ? error.message : "更新售后处理单失败";
      setDiagnosticRemediation((current) => ({
        status: "error",
        message,
        requests: current.requests
      }));
      throw error;
    }
  }

  async function handleDownloadDiagnosticRemediationRequest(request: DiagnosticRemediationRequest) {
    if (auth.status !== "ready" || !auth.token || !canManageSignedUpdates(auth.user)) {
      throw new Error("当前账号无权下载售后处理包");
    }
    const download = await downloadDiagnosticRemediationRequest(auth.user.tenant.id, auth.token, request.id);
    downloadDiagnosticRemediationPackage(download);
  }

  async function handleCreateDiagnosticRemediationUpdatePlan(
    request: DiagnosticRemediationRequest,
    packageItem: SignedUpdateStagedPackage
  ) {
    if (auth.status !== "ready" || !auth.token || !canManageSignedUpdates(auth.user)) {
      throw new Error("当前账号无权生成受控更新计划");
    }
    setDiagnosticRemediation((current) => ({
      status: "loading",
      message: "正在生成受控更新计划",
      requests: current.requests
    }));
    try {
      const updated = await createDiagnosticRemediationUpdatePlan(auth.user.tenant.id, auth.token, request.id, {
        signed_update_package_id: packageItem.id,
        operator_note: `售后处理单绑定更新包：${packageItem.package_name}。计划只记录状态，不自动应用。`
      });
      await refreshSignedUpdatePackages(auth.user.tenant.id, auth.token);
      await refreshLocalMaintenanceReadiness(auth.user.tenant.id, auth.token);
      setDiagnosticRemediation((current) => ({
        status: "ready",
        message: `已生成受控更新计划：${packageItem.package_name}`,
        requests: current.requests.map((item) => (item.id === updated.id ? updated : item))
      }));
    } catch (error) {
      const message = error instanceof Error ? error.message : "生成受控更新计划失败";
      setDiagnosticRemediation((current) => ({
        status: "error",
        message,
        requests: current.requests
      }));
      throw error;
    }
  }

  async function handleCreateLocalBackup() {
    if (auth.status !== "ready" || !auth.token || !canManageSignedUpdates(auth.user)) {
      throw new Error("当前账号无权创建本地备份点");
    }
    setLocalBackupState((current) => ({
      status: "loading",
      message: "正在创建本地数据库备份点",
      backups: current.backups
    }));
    try {
      const backup = await createLocalBackup(
        auth.user.tenant.id,
        auth.token,
        "客户管理员在本地更新中心手动创建数据库备份点。"
      );
      await refreshLocalBackups(auth.user.tenant.id, auth.token);
      await refreshLocalMaintenanceReadiness(auth.user.tenant.id, auth.token);
      setLocalBackupState((current) => ({
        status: "ready",
        message: `已创建备份点：${backup.file_name}`,
        backups: current.backups
      }));
    } catch (error) {
      const message = error instanceof Error ? error.message : "创建本地备份点失败";
      setLocalBackupState((current) => ({
        status: "error",
        message,
        backups: current.backups
      }));
      throw error;
    }
  }

  async function handleVerifyLocalBackup(backup: LocalBackupRecord) {
    if (auth.status !== "ready" || !auth.token || !canManageSignedUpdates(auth.user)) {
      throw new Error("当前账号无权校验本地备份点");
    }
    setLocalBackupState((current) => ({
      status: "loading",
      message: `正在校验备份点：${backup.file_name}`,
      backups: current.backups
    }));
    try {
      const verified = await verifyLocalBackup(
        backup.id,
        auth.token,
        "客户管理员在本地更新中心校验数据库备份点。"
      );
      await refreshLocalBackups(auth.user.tenant.id, auth.token);
      await refreshLocalMaintenanceReadiness(auth.user.tenant.id, auth.token);
      setLocalBackupState((current) => ({
        status: "ready",
        message: `校验结果：${formatLocalBackupStatus(verified.status)}`,
        backups: current.backups
      }));
    } catch (error) {
      const message = error instanceof Error ? error.message : "校验本地备份点失败";
      setLocalBackupState((current) => ({
        status: "error",
        message,
        backups: current.backups
      }));
      throw error;
    }
  }

  async function handleCreateLocalBackupRestoreDryRun(backup: LocalBackupRecord) {
    if (auth.status !== "ready" || !auth.token || !canManageSignedUpdates(auth.user)) {
      throw new Error("当前账号无权生成本地恢复演练");
    }
    setLocalBackupState((current) => ({
      status: "loading",
      message: `正在生成恢复演练：${backup.file_name}`,
      backups: current.backups
    }));
    try {
      const plan = await createLocalBackupRestoreDryRun(
        backup.id,
        auth.token,
        "客户管理员在本地更新中心执行恢复工具演练。"
      );
      setLocalRestoreDryRun(plan);
      await refreshLocalBackups(auth.user.tenant.id, auth.token);
      await refreshLocalMaintenanceReadiness(auth.user.tenant.id, auth.token);
      setLocalBackupState((current) => ({
        status: "ready",
        message: plan.rehearsal_ready ? "恢复演练计划已生成" : "恢复演练存在阻断项",
        backups: current.backups
      }));
    } catch (error) {
      const message = error instanceof Error ? error.message : "生成本地恢复演练失败";
      setLocalBackupState((current) => ({
        status: "error",
        message,
        backups: current.backups
      }));
      throw error;
    }
  }

  async function handlePreflightSignedUpdatePackage(rawPackageText: string) {
    if (auth.status !== "ready" || !auth.token || !canManageSignedUpdates(auth.user)) {
      throw new Error("当前账号无权校验签名更新包");
    }
    let parsedPackage: unknown;
    try {
      parsedPackage = JSON.parse(rawPackageText);
    } catch {
      setSignedUpdatePreflight((current) => ({
        status: "error",
        message: "更新包内容不是合法 JSON",
        result: current.result
      }));
      throw new Error("更新包内容不是合法 JSON");
    }
    setSignedUpdatePreflight((current) => ({
      status: "loading",
      message: "正在校验签名、摘要、版本兼容和备份计划",
      result: current.result
    }));
    try {
      const result = await preflightSignedUpdatePackage(auth.user.tenant.id, auth.token, parsedPackage);
      setSignedUpdatePreflight({
        status: "ready",
        message: result.can_stage ? "预检通过，可以进入客户确认和备份流程" : "预检未通过，不能暂存更新包",
        result
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : "签名更新包预检失败";
      setSignedUpdatePreflight((current) => ({
        status: "error",
        message,
        result: current.result
      }));
      throw error;
    }
  }

  async function handleStageSignedUpdatePackage(rawPackageText: string) {
    if (auth.status !== "ready" || !auth.token || !canManageSignedUpdates(auth.user)) {
      throw new Error("当前账号无权暂存签名更新包");
    }
    let parsedPackage: unknown;
    try {
      parsedPackage = JSON.parse(rawPackageText);
    } catch {
      setSignedUpdateStage((current) => ({
        status: "error",
        message: "更新包内容不是合法 JSON",
        packages: current.packages
      }));
      throw new Error("更新包内容不是合法 JSON");
    }
    setSignedUpdateStage((current) => ({
      status: "loading",
      message: "正在校验并暂存更新包",
      packages: current.packages
    }));
    try {
      const staged = await stageSignedUpdatePackage(auth.user.tenant.id, auth.token, parsedPackage);
      await refreshSignedUpdatePackages(auth.user.tenant.id, auth.token);
      await refreshLocalMaintenanceReadiness(auth.user.tenant.id, auth.token);
      setSignedUpdateStage((current) => ({
        status: "ready",
        message: `更新包已暂存：${staged.package_name}`,
        packages: current.packages
      }));
    } catch (error) {
      const message = error instanceof Error ? error.message : "签名更新包暂存失败";
      setSignedUpdateStage((current) => ({
        status: "error",
        message,
        packages: current.packages
      }));
      throw error;
    }
  }

  async function handleApplySignedUpdatePackage(packageItem: SignedUpdateStagedPackage) {
    if (auth.status !== "ready" || !auth.token || !canManageSignedUpdates(auth.user)) {
      throw new Error("当前账号无权应用签名更新包");
    }
    setSignedUpdateStage((current) => ({
      status: "loading",
      message: `正在为 ${packageItem.package_name} 创建备份并应用更新`,
      packages: current.packages
    }));
    try {
      const applied = await applyStagedSignedUpdatePackage(
        packageItem.id,
        auth.token,
        "客户管理员在本地更新中心确认备份并应用签名更新包。"
      );
      await refreshSignedUpdatePackages(auth.user.tenant.id, auth.token);
      await refreshLocalMaintenanceReadiness(auth.user.tenant.id, auth.token);
      setSignedUpdateStage((current) => ({
        status: "ready",
        message: `已应用：${applied.package_name}`,
        packages: current.packages
      }));
    } catch (error) {
      const message = error instanceof Error ? error.message : "应用签名更新包失败";
      setSignedUpdateStage((current) => ({
        status: "error",
        message,
        packages: current.packages
      }));
      throw error;
    }
  }

  async function handleCreateProgramUpdateDryRun(packageItem: SignedUpdateStagedPackage) {
    if (auth.status !== "ready" || !auth.token || !canManageSignedUpdates(auth.user)) {
      throw new Error("当前账号无权生成程序更新演练计划");
    }
    setSignedUpdateStage((current) => ({
      status: "loading",
      message: `正在生成 ${packageItem.package_name} 的程序更新演练计划`,
      packages: current.packages
    }));
    try {
      const planned = await createProgramUpdateDryRun(
        packageItem.id,
        auth.token,
        "客户管理员在本地更新中心确认只生成程序更新演练计划。"
      );
      await refreshSignedUpdatePackages(auth.user.tenant.id, auth.token);
      await refreshLocalMaintenanceReadiness(auth.user.tenant.id, auth.token);
      setSignedUpdateStage((current) => ({
        status: "ready",
        message: `已生成演练计划：${planned.package_name}`,
        packages: current.packages
      }));
    } catch (error) {
      const message = error instanceof Error ? error.message : "生成程序更新演练计划失败";
      setSignedUpdateStage((current) => ({
        status: "error",
        message,
        packages: current.packages
      }));
      throw error;
    }
  }

  async function handleRollbackSignedUpdatePackage(packageItem: SignedUpdateStagedPackage) {
    if (auth.status !== "ready" || !auth.token || !canManageSignedUpdates(auth.user)) {
      throw new Error("当前账号无权回滚签名更新包");
    }
    setSignedUpdateStage((current) => ({
      status: "loading",
      message: `正在回滚 ${packageItem.package_name}`,
      packages: current.packages
    }));
    try {
      const rolledBack = await rollbackStagedSignedUpdatePackage(
        packageItem.id,
        auth.token,
        "客户管理员在本地更新中心确认回滚本次签名更新包。"
      );
      await refreshSignedUpdatePackages(auth.user.tenant.id, auth.token);
      await refreshLocalMaintenanceReadiness(auth.user.tenant.id, auth.token);
      setSignedUpdateStage((current) => ({
        status: "ready",
        message: `已回滚：${rolledBack.package_name}`,
        packages: current.packages
      }));
    } catch (error) {
      const message = error instanceof Error ? error.message : "回滚签名更新包失败";
      setSignedUpdateStage((current) => ({
        status: "error",
        message,
        packages: current.packages
      }));
      throw error;
    }
  }

  async function handleLogin(payload: LoginRequest) {
    setAuth({ status: "submitting" });
    setConnection({ status: "loading" });
    try {
      const result = await login(payload);
      const nextSection = getPostAuthWorkspaceSection(result.user.roles, window.location.hash);
      window.localStorage.setItem(TOKEN_STORAGE_KEY, result.access_token);
      setConnection({ status: "ready", user: result.user, mode: "token" });
      setChannelIdentityById({});
      setChannelAccountState({ status: "idle", message: "等待刷新渠道账号", channels: [], accounts: [] });
      setAccountManagement({ status: "idle", message: "等待刷新账号治理", users: [], roles: [] });
      setAuth({
        status: "ready",
        user: result.user,
        token: result.access_token,
        mode: "token"
      });
      window.history.replaceState(null, "", getWorkspaceSectionHash(nextSection));
      setActiveSection(nextSection);
    } catch (error) {
      const message = error instanceof Error ? error.message : "登录失败";
      setConnection({ status: "error", error: message });
      setAuth({ status: "login", error: "租户、邮箱或密码不正确" });
    }
  }

  async function handleLocalPreviewLogin() {
    setAuth({ status: "submitting" });
    setConnection({ status: "loading" });
    try {
      const result = await loginLocalDev();
      const nextSection = getPostAuthWorkspaceSection(result.user.roles, window.location.hash);
      window.localStorage.setItem(TOKEN_STORAGE_KEY, result.access_token);
      setConnection({ status: "ready", user: result.user, mode: "token" });
      setChannelIdentityById({});
      setChannelAccountState({ status: "idle", message: "等待刷新渠道账号", channels: [], accounts: [] });
      setAccountManagement({ status: "idle", message: "等待刷新账号治理", users: [], roles: [] });
      setAuth({
        status: "ready",
        user: result.user,
        token: result.access_token,
        mode: "token"
      });
      window.history.replaceState(null, "", getWorkspaceSectionHash(nextSection));
      setActiveSection(nextSection);
    } catch (error) {
      const message = error instanceof Error ? error.message : "本地预览登录失败";
      setConnection({ status: "error", error: message });
      setAuth({ status: "login", error: "本地预览入口不可用，请使用负责人账号登录。" });
    }
  }

  async function handleCreateLocalOwner(payload: LocalOwnerSetupRequest) {
    setAuth({ status: "submitting" });
    setConnection({ status: "loading" });
    try {
      const result = await createLocalOwner(payload);
      window.localStorage.setItem(TOKEN_STORAGE_KEY, result.access_token);
      void refreshLocalSetupState();
      setConnection({ status: "ready", user: result.user, mode: "token" });
      setChannelIdentityById({});
      setChannelAccountState({ status: "idle", message: "等待刷新渠道账号", channels: [], accounts: [] });
      setAuth({
        status: "ready",
        user: result.user,
        token: result.access_token,
        mode: "token"
      });
      window.history.replaceState(null, "", getWorkspaceSectionHash("overview"));
      setActiveSection("overview");
    } catch (error) {
      const message = error instanceof Error ? error.message : "初始化本地负责人失败";
      const friendlyMessage = message.includes("already initialized")
        ? "本地工作台已经初始化，请使用已有账号登录。"
        : message.includes("tenant slug")
          ? "租户标识只能使用小写字母、数字和短横线。"
          : "初始化本地负责人失败，请检查邮箱、密码和后端服务。";
      setConnection({ status: "error", error: message });
      setAuth({ status: "login", error: friendlyMessage });
      void refreshLocalSetupState();
    }
  }

  async function enterDemo() {
    window.localStorage.removeItem(TOKEN_STORAGE_KEY);
    const user = createDemoCurrentUser();
    setConnection({ status: "ready", user, mode: "demo" });
    setAuth({ status: "ready", user, mode: "demo" });
    const nextSection = getPostAuthWorkspaceSection(user.roles, window.location.hash);
    window.history.replaceState(null, "", getWorkspaceSectionHash(nextSection));
    setActiveSection(nextSection);
  }

  function logout() {
    window.localStorage.removeItem(TOKEN_STORAGE_KEY);
    setConnection({ status: "error", error: "尚未登录" });
    setAuth({ status: "login" });
    void refreshLocalSetupState();
    setReviewInbox({ status: "idle", message: "等待正式登录" });
    setChannelIdentityById({});
    setChannelAccountState({ status: "idle", message: "等待正式登录", channels: [], accounts: [] });
    setAccountManagement({ status: "idle", message: "等待正式登录", users: [], roles: [] });
    setSupportTickets({ status: "idle", message: "等待正式登录", data: EMPTY_SUPPORT_TICKET_LIST });
    setContactProfiles({ status: "idle", message: "等待正式登录", data: EMPTY_CONTACT_PROFILE_LIST, detail: null });
    setSalesLeads({ status: "idle", message: "等待正式登录", data: EMPTY_SALES_LEAD_LIST });
    setOutbox({ status: "idle", message: "等待正式登录" });
      setFailureReviews({ status: "idle", message: "等待正式登录" });
      setDeliveryQueue({ status: "idle", message: "等待正式登录" });
      setKnowledgeWorkbench({
        status: "idle",
        message: "等待正式登录",
        businessObjects: [],
        objectCardsByObject: {},
        documents: [],
        chunksByDocument: {},
        publicationsByDocument: {},
        searchResult: null
      });
      setKnowledgeEvaluation({
        status: "idle",
        message: "等待正式登录",
        sets: [],
        lastRun: null,
        runsBySet: {}
      });
      setPilotReadiness({ status: "idle", message: "等待正式登录", data: null });
      setKnowledgeConfirmationImport({ status: "idle", message: "等待客户确认表", result: null });
      setRagCostGovernance({
        status: "idle",
        message: "等待正式登录",
        data: null
      });
      setLastWorkerRun(null);
      setLastDeliveryQueueRun(null);
      setLastInboundWorkerRun(null);
  }

  async function handleResolveFailureReview(item: DeliveryFailureReview) {
    if (auth.status !== "ready" || !auth.token || !hasPermission(auth.user, PERMISSIONS.outboxFailureReviewManage)) {
      return;
    }
    setFailureReviews((current) => ({
      status: "loading",
      items: "items" in current ? current.items : []
    }));
    try {
      await resolveDeliveryFailureReview(item.id, auth.token, {
        status: "resolved",
        resolution_note: `已跟进：${item.next_action}`
      });
      await refreshFailureReviews(auth.user.tenant.id, auth.token);
    } catch (error) {
      const message = error instanceof Error ? error.message : "处理失败复盘项失败";
      setFailureReviews((current) => ({
        status: "error",
        message,
        items: "items" in current ? current.items : []
      }));
    }
  }

  if (auth.status === "checking" || auth.status === "login" || auth.status === "submitting" || auth.status === "error") {
    return (
      <LoginScreen
        loading={auth.status === "checking" || auth.status === "submitting"}
        error={"error" in auth ? auth.error : undefined}
        setupStatus={localSetupStatus}
        onLogin={(payload) => void handleLogin(payload)}
        onLocalPreviewLogin={() => void handleLocalPreviewLogin()}
        onCreateLocalOwner={(payload) => void handleCreateLocalOwner(payload)}
      />
    );
  }

  const reviewItems = "items" in reviewInbox ? reviewInbox.items : [];
  const replyDecisions = "items" in replyDecisionState ? replyDecisionState.items : [];
  const outboxDrafts = "drafts" in outbox ? outbox.drafts : [];
  const failureReviewItems = "items" in failureReviews ? failureReviews.items : [];
  const deliveryJobs = "jobs" in deliveryQueue ? deliveryQueue.jobs : [];
  const selectedReview =
    reviewItems.find((item) => item.id === selectedReviewId) ??
    reviewItems.find((item) => ["high", "critical"].includes(item.risk_level)) ??
    reviewItems[0] ??
    null;
  const taskPathMetrics: RoleTaskPathMetrics = {
    reviewItems,
    outboxDrafts,
    failureReviews: failureReviewItems,
    deliveryJobs,
    supportTickets,
    salesLeads,
    knowledgeGaps,
    businessOpsDashboard
  };
  const pageMeta = getWorkspacePageMeta(activeSection);
  const canManageConversation = canManageConversations(auth.user);
  const canManageTicket = canManageTickets(auth.user);
  const canManageLead = canManageLeads(auth.user);
  const canManageKnowledgeWorkspace = hasKnowledgeManagePermission(auth.user);
  const canRunInboundWorkerWorkspace = canRunInboundWorker(auth.user);
  const canManageChannelConnector = hasPermission(auth.user, PERMISSIONS.channelConnectorManage);
  const canManageOutboxDraft = hasPermission(auth.user, PERMISSIONS.outboxDraftManage);
  const canManageOutboxSendAttempt = hasPermission(auth.user, PERMISSIONS.outboxSendAttemptManage);
  const canManageOutboxSendPlan = hasPermission(auth.user, PERMISSIONS.outboxSendPlanManage);
  const canManageOutboxDeliveryJob = hasPermission(auth.user, PERMISSIONS.outboxDeliveryJobManage);
  const canManageFailureReview = hasPermission(auth.user, PERMISSIONS.outboxFailureReviewManage);
  const liveConversationsForWorkspace = conversationInbox.data.items;
  const liveColleagueSummaries = (
    accountManagement.users.length > 1
      ? accountManagement.users
          .filter((user) => Number(user.id) !== Number(auth.user.id))
          .slice(0, 6)
          .map((user, index) => ({
            id: Number(user.id),
            name: normalizePublicProfile(user.public_profile).display_name || user.name || user.email || `同事 ${index + 1}`,
            email: user.email,
            role: user.roles?.join(" / ") || "客服",
            status: user.status === "disabled" || user.status === "inactive" ? "offline" : index % 3 === 1 ? "busy" : "online",
            activeChats: liveConversationsForWorkspace.filter((item) => item.assigned_user_id === Number(user.id)).length,
            avatarDataUrl: user.avatar_data_url || "",
            publicProfile: normalizePublicProfile(user.public_profile)
          }))
      : [
          { id: 201, name: "客服小林", email: "xiaolin@example.local", role: "售前客服", status: "online", activeChats: 3, avatarDataUrl: "", publicProfile: defaultPublicProfile },
          { id: 202, name: "客服小周", email: "xiaozhou@example.local", role: "售后客服", status: "busy", activeChats: 6, avatarDataUrl: "", publicProfile: defaultPublicProfile },
          { id: 203, name: "客服小陈", email: "xiaochen@example.local", role: "值班主管", status: "online", activeChats: 1, avatarDataUrl: "", publicProfile: defaultPublicProfile },
          { id: 204, name: "客服小何", email: "xiaohe@example.local", role: "工单支持", status: "offline", activeChats: 0, avatarDataUrl: "", publicProfile: defaultPublicProfile }
        ]
  ) as WorkbenchColleague[];
  const selectedLiveColleague =
    liveColleagueSummaries.find((colleague) => colleague.id === selectedLiveColleagueId) ??
    liveColleagueSummaries[0] ??
    null;
  const overviewTaskMatchCount = overviewTaskContext
    ? getWorkspaceTaskMatchCount(overviewTaskContext, {
        conversationItems: conversationInbox.data.items,
        reviewItems,
        outboxDrafts,
        failureReviews: failureReviewItems,
        deliveryJobs,
        knowledgeGaps: knowledgeGaps.data.items,
        knowledgeDocuments: knowledgeWorkbench.documents,
        knowledgePublications: Object.values(knowledgeWorkbench.publicationsByDocument).flat(),
        knowledgeEvaluation
      })
    : null;
  const WorkspacePage = workspacePageComponents[activeSection] ?? null;
  const workspacePageContext = {
    Components: {
      AccountManagementPanel,
      ChannelConnectorCenterPanel,
      ContactProfilesPanel,
      ConversationInboxPanel,
      ConversationWorkbenchPanel,
      KnowledgeDocumentsPanel,
      KnowledgeEvaluationPanel,
      KnowledgeGapPanel,
      KnowledgeWorkspacePage,
      LiveColleagueProfilePanel,
      ModelRoutingPanel,
      OpsWorkerHealthPanel,
      OutboxPanel,
      PilotPreparationPanel,
      QualityReviewPanel,
      ReviewEvidenceDetail,
      ReviewInboxPanel,
      SalesLeadPanel,
      SupportTicketPanel,
      WorkbenchCommandCenter
    },
    accountManagement,
    activeSection,
    auth,
    businessObjectDraft,
    businessOpsDashboard,
    canManageAccounts,
    canManageChannelConnector,
    canManageConversation,
    canManageKnowledgeWorkspace,
    canManageLead,
    canManageOutboxDeliveryJob,
    canManageOutboxDraft,
    canManageOutboxSendAttempt,
    canManageOutboxSendPlan,
    canManageSignedUpdates,
    canManageTicket,
    canReadChannels,
    canReadConversations,
    canReadCustomers,
    canReadDashboard,
    canReadKnowledgeDocuments,
    canReadKnowledgeEvaluations,
    canReadKnowledgeGaps,
    canReadLeads,
    canReadOpsAlertRules,
    canReadOpsMetrics,
    canReadOpsWorkerHealth,
    canReadOutboxDeliveryJobs,
    canReadOutboxDrafts,
    canReadTickets,
    canRunInboundWorkerWorkspace,
    channelAccountState,
    channelIdentities,
    contactProfileListView,
    contactProfiles,
    conversationDetail,
    conversationInbox,
    conversationInboxFilters,
    conversationInboxView,
    customerMaterialBatches,
    customerMaterialHandoffBundle,
    customerMaterialPrecheck,
    customerMaterialTemplatePackage,
    customerQualityReport,
    customerQualityReportArchives,
    customerQualityReportSignoffs,
    customerQuestionBankDraft,
    deliveryJobs,
    deliveryQueue,
    dialogueScope,
    diagnosticExport,
    diagnosticIntake,
    diagnosticRemediation,
    evaluationDraft,
    evaluationResultListView,
    evaluationSetListView,
    failureReviewItems,
    finalAnswerLabelImportDraft,
    getChannelEntryIdFromHash,
    handleApplySignedUpdatePackage,
    handleBatchLabelSampledFactuality,
    handleCaptureEvaluationRunCaseFinalAnswerSample,
    handleCheckKnowledgeDocumentPublishGate,
    handleConfigureChannelAccount,
    handleDeleteChannelAccountConnection,
    handleConfigureChannelConnector,
    handleConfirmDraft,
    handleConnectorPlan,
    handleContactProfileListViewChange,
    handleConversationInboxFiltersChange,
    handleConversationInboxViewChange,
    handleConversationWorkflowAction,
    handleCreateAccountUser,
    handleCreateBusinessObject: handleSaveBusinessObject,
    handleCreateDeliveryJob,
    handleCreateDiagnosticIntakeRecord,
    handleCreateDiagnosticRemediationRequest,
    handleCreateDiagnosticRemediationUpdatePlan,
    handleCreateDiagnosticUploadPackage,
    handleCreateKnowledgeEvaluationSet,
    handleCreateKnowledgeGapDocumentDraft,
    handleCreateKnowledgeGapRegressionCase,
    handleCreateLocalBackup,
    handleCreateLocalBackupRestoreDryRun,
    handleCreateObjectKnowledgeCard,
    handleCreateProgramUpdateDryRun,
    handleCreateSafeTestConversation,
    handleCreateSalesLead,
    handleCreateSupportTicket,
    handleDownloadCustomerMaterialHandoffBundle,
    handleDownloadCustomerQualityReportArchive,
    handleDownloadDiagnosticIntakeRecord,
    handleDownloadDiagnosticRemediationRequest,
    handleDryRun,
    handleExportCustomerQualityReport,
    handleExportFinalAnswerLabels,
    handleExportKnowledgeEvaluationRunReport,
    handleExportDiagnosticBundle,
    handleImportCustomerQuestionBank,
    handleImportKnowledgeConfirmation,
    handleImportKnowledgeDocument,
    handleImportKnowledgeUpdatePackage,
    handleImportFinalAnswerLabels,
    handlePrecheckKnowledgeTemplateImport,
    handleCreateKnowledgeTemplateImport,
    handleRunKnowledgeTemplateSample,
    handlePublishKnowledgeTemplateImport,
    handleLabelEvaluationRunCaseFactuality,
    handleLoadCustomerMaterialTemplatePackage,
    handleLoadKnowledgeEvaluationRun,
    handlePrecheckCustomerMaterials,
    handlePrecheckCustomerQuestionBank,
    handlePrecheckFinalAnswerLabels,
    handlePreflightSignedUpdatePackage,
    handlePreviewKnowledgeUpdatePackage,
    handlePublishKnowledgeDocument,
    handlePublishKnowledgeGapDocument,
    handleRecordCustomerQualityReportSignoff,
    handleResetAccountUserPassword,
    handleReviewApprove,
    handleReviewReject,
    handleRollbackKnowledgeDocument,
    handleRollbackSignedUpdatePackage,
    handleRunDeliveryQueue,
    handleRunInboundWorker,
    handleRunKnowledgeEvaluation,
    handleRunWorker,
    handleSalesLeadFiltersChange,
    handleSalesLeadListViewChange,
    handleSaveBusinessObject,
    handleSaveTenantReplyStrategy,
    handleSearchKnowledgeDocuments,
    handleSelectContactProfile,
    handleSendLocalConversationReply,
    handleStageSignedUpdatePackage,
    handleStartChannelConnectorAuthorization,
    handleUpsertChannelConnectorSecrets,
    handleDeleteChannelConnectorSecrets,
    handleVerifyChannelConnector,
    handleSupportTicketFiltersChange,
    handleSupportTicketListViewChange,
    handleSyncKnowledgeGaps,
    handleUpdateAccountUserStatus,
    handleUpdateDiagnosticIntakeRecord,
    handleUpdateDiagnosticRemediationRequest,
    handleUpdateKnowledgeGap,
    handleUpdateSalesLeadStage,
    handleUpdateSupportTicketStatus,
    handleVerifyLocalBackup,
    hasKnowledgeManagePermission,
    knowledgeConfirmationImport,
    knowledgeDocumentListView,
    knowledgeDraft,
    knowledgeTemplateImportDraft,
    knowledgeEvaluation,
    knowledgeGapListView,
    knowledgeGaps,
    knowledgeMemoryMesh,
    knowledgeSearchQuery,
    knowledgeUpdatePackageDraft,
    knowledgeWorkbench,
    lastDeliveryQueueRun,
    lastInboundWorkerRun,
    lastWorkerRun,
    liveColleagueSummaries,
    llmOpsReadiness,
    aiServiceStatus,
    channelConnectorSelfService,
    localBackupState,
    localMaintenanceReadiness,
    localReplyState,
    localRestoreDryRun,
    monthlyOpsReport,
    monthlyQualityReview,
    objectKnowledgeCardDraft,
    onlineReceiptQuality,
    opsAlertRules,
    opsMetrics,
    opsWorkerHealth,
    outbox,
    outboxDrafts,
    outboxListView,
    overviewTaskContext,
    pilotReadiness,
    ragCostGovernance,
    refreshAccountManagement,
    refreshBusinessOpsDashboard,
    refreshChannelAccounts,
    refreshContactProfiles,
    refreshCustomerMaterialBatches,
    refreshDeliveryQueue,
    refreshDiagnosticIntakes,
    refreshDiagnosticRemediations,
    refreshKnowledgeDocuments,
    refreshKnowledgeEvaluations,
    refreshKnowledgeGaps,
    refreshKnowledgeMemoryMeshOverview,
    refreshLiveWorkspaceResources,
    refreshLlmOpsReadiness,
    refreshLocalBackups,
    refreshLocalMaintenanceReadiness,
    refreshOpsAlertRules,
    refreshOpsMetrics,
    refreshOpsWorkerHealth,
    refreshOutbox,
    refreshPilotReadiness,
    refreshRagCostGovernance,
    refreshReviewInbox,
    refreshSalesLeads,
    refreshSignedUpdatePackages,
    refreshSupportTickets,
    replyDecisionState,
    replyDecisions,
    replyStrategyDraft,
    reviewInbox,
    reviewItems,
    reviewListView,
    salesLeadFilters,
    salesLeadListView,
    salesLeads,
    selectedLiveColleague,
    selectedLiveConversationId,
    selectedReview,
    setBusinessObjectDraft,
    setCustomerQuestionBankDraft,
    setEvaluationDraft,
    setEvaluationResultListView,
    setEvaluationSetListView,
    setFinalAnswerLabelImportDraft,
    setKnowledgeDocumentListView,
    setKnowledgeDraft,
    setKnowledgeSearchQuery,
    setKnowledgeTemplateImportDraft,
    setKnowledgeUpdatePackageDraft,
    setObjectKnowledgeCardDraft,
    setOutboxListView,
    setReplyStrategyDraft,
    setReviewListView,
    setSelectedLiveConversationId,
    setSelectedReviewId,
    signedUpdatePreflight,
    signedUpdateStage,
    supportTicketFilters,
    supportTicketListView,
    supportTickets,
    tenantReplyStrategy,
    workspaceHash
  };
  const workspaceContent = WorkspacePage ? (
    <Suspense fallback={<WorkspaceRouteLoading />}>
      <WorkspacePage ctx={workspacePageContext} />
    </Suspense>
  ) : null;

  const utilityNavigationLabels = new Set(["消息中心", "设置中心"]);
  const primaryNavigationGroups = visibleNavigationGroups
    .filter((group) => !utilityNavigationLabels.has(group.label))
    .filter(
      (group, index, groups) =>
        groups.findIndex((candidate) => candidate.href === group.href) === index
    );
  const messageCenterGroup = visibleNavigationGroups.find((group) => group.label === "消息中心");
  const settingsGroup = visibleNavigationGroups.find((group) => group.label === "设置中心");
  const activeNavigationGroup =
    visibleNavigationGroups.find((group) =>
      group.items.some((item) => getWorkspaceSectionFromHash(item.href) === activeSection)
    ) ??
    primaryNavigationGroups.find((group) => getWorkspaceSectionFromHash(group.href) === activeSection) ??
    primaryNavigationGroups[0];
  const activeSecondaryItems = (activeNavigationGroup?.items ?? []).filter((item) => !item.hiddenFromSidebar);
  const liveConversations = conversationInbox.data.items;
  const parsedCurrentUserId = Number(auth.user.id);
  const liveCurrentUserId = Number.isFinite(parsedCurrentUserId) ? parsedCurrentUserId : null;
  const isLiveConversationActive = (item: ConversationInboxItem) => !["closed", "resolved"].includes(item.status);
  const isLiveQueuedConversation = (item: ConversationInboxItem) =>
    isLiveConversationActive(item) && item.assigned_user_id === null;
  const isLiveMineConversation = (item: ConversationInboxItem) =>
    isLiveConversationActive(item) && liveCurrentUserId !== null && item.assigned_user_id === liveCurrentUserId;
  const isLiveVisitingConversation = (item: ConversationInboxItem) =>
    isLiveConversationActive(item) && !isLiveQueuedConversation(item) && !isLiveMineConversation(item);
  const livePreviewConversation =
    liveConversations.find((item) => item.id === selectedLiveConversationId) ??
    liveConversations.find((item) => liveCurrentUserId !== null && item.assigned_user_id === liveCurrentUserId) ??
    liveConversations[0] ??
    null;
  const livePreviewTitle = livePreviewConversation
    ? livePreviewConversation.contact_display_name || livePreviewConversation.subject || `客户 #${livePreviewConversation.contact_id}`
    : "";
  const livePreviewChannel = livePreviewConversation
    ? livePreviewConversation.channel_name || livePreviewConversation.channel_type || "访客"
    : "";
  const liveColleagues = liveColleagueSummaries;
  const normalizedDialogueSearch = dialogueSearch.trim().toLowerCase();
  const matchesDialogueSearch = (item: ConversationInboxItem) => {
    if (!normalizedDialogueSearch) {
      return true;
    }
    return [
      item.contact_display_name,
      item.subject,
      item.last_message_preview,
      item.channel_name,
      item.channel_type
    ]
      .filter((value): value is string => Boolean(value))
      .some((value) => value.toLowerCase().includes(normalizedDialogueSearch));
  };
  const matchesColleagueSearch = (colleague: { name: string; role: string; status: string }) => {
    if (!normalizedDialogueSearch) {
      return true;
    }
    return [colleague.name, colleague.role, formatColleagueStatus(colleague.status)]
      .some((value) => value.toLowerCase().includes(normalizedDialogueSearch));
  };
  const liveCurrentConversations = liveConversations
    .filter(isLiveConversationActive)
    .filter(matchesDialogueSearch);
  const liveRecentConversations = [...liveConversations]
    .filter(matchesDialogueSearch)
    .sort((left, right) => {
      const leftTime = left.last_message_at ? new Date(left.last_message_at).getTime() : 0;
      const rightTime = right.last_message_at ? new Date(right.last_message_at).getTime() : 0;
      return rightTime - leftTime;
    });
  const liveVisibleColleagues = liveColleagues.filter(matchesColleagueSearch);
  const liveQueuedConversations = liveCurrentConversations.filter(isLiveQueuedConversation);
  const liveMineConversations = liveCurrentConversations.filter(isLiveMineConversation);
  const liveVisitConversations = liveCurrentConversations.filter(isLiveVisitingConversation);
  const activePresenceOption =
    agentPresenceOptions.find((option) => option.key === agentPresenceStatus) ?? agentPresenceOptions[0];
  const activePresenceLabel =
    agentPresenceStatus === "away" ? `${activePresenceOption.label} · ${agentLeaveReason}` : activePresenceOption.label;
  const toggleDialogueSection = (section: string) => {
    setCollapsedDialogueSections((current) => ({ ...current, [section]: !current[section] }));
  };
  const applyUpdatedCurrentUser = (user: CurrentUser) => {
    setAuth((current) => current.status === "ready" ? { ...current, user } : current);
    setConnection((current) => current.status === "ready" ? { ...current, user } : current);
  };
  const isCurrentSessionExpired = (error: unknown) =>
    error instanceof Error && error.message.includes("401") && error.message.includes("valid bearer token required");
  const requireFreshLogin = () => {
    window.localStorage.removeItem(TOKEN_STORAGE_KEY);
    setConnection({ status: "error", error: "登录已失效，请重新登录" });
    setAuth({ status: "login", error: "登录已失效，请重新登录后再保存账号设置。" });
  };
  const openAccountMenuModal = (modal: AccountMenuModal) => {
    setAccountModalNotice("");
    setAccountModalSaving(false);
    setActiveAccountMenuModal(modal);
    setIsAccountMenuOpen(false);
    setIsMessageCenterOpen(false);
    setIsPresenceMenuOpen(false);
    if (modal === "accountInfo") {
      setAccountProfileForm({
        name: auth.user.name || "",
        avatar_data_url: auth.user.avatar_data_url || "",
        public_profile: normalizePublicProfile(auth.user.public_profile)
      });
    }
    if (modal === "personalSettings") {
      setPersonalSettingsForm(normalizePersonalSettings(auth.user.personal_settings));
    }
    if (modal === "changePassword") {
      setPasswordForm({ current: "", next: "", confirm: "" });
      setPasswordNotice("");
    }
  };
  const closeAccountMenuModal = () => {
    setActiveAccountMenuModal(null);
    setPasswordNotice("");
  };
  const accountRoleLabel = getWorkspaceRoleLabel(auth.user.roles);
  const accountDisplayName = auth.user.name || auth.user.email || "admin";
  const accountLoginName = auth.user.email?.split("@")[0] || auth.user.name || auth.user.id || "admin";
  const accountAvatarUrl = auth.user.avatar_data_url || "";
  const accountAvatarInitial = getAvatarInitial(
    normalizePublicProfile(auth.user.public_profile).display_name || accountDisplayName || accountLoginName
  );
  const accountPublicProfile = normalizePublicProfile(accountProfileForm.public_profile);
  const updateAccountPublicProfileField = (field: keyof UserPublicProfile, value: string) => {
    setAccountProfileForm((current) => ({
      ...current,
      public_profile: { ...current.public_profile, [field]: value }
    }));
  };
  const updatePersonalSettingField = <Key extends keyof UserPersonalSettings>(field: Key, value: UserPersonalSettings[Key]) => {
    setPersonalSettingsForm((current) => ({ ...current, [field]: value }));
  };
  const handleAvatarFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) {
      return;
    }
    const allowedTypes = new Set(["image/png", "image/jpeg", "image/gif"]);
    if (!allowedTypes.has(file.type)) {
      setAccountModalNotice("头像只支持 jpg、gif、png 格式。");
      return;
    }
    if (file.size > 500 * 1024) {
      setAccountModalNotice("头像图片大小不能超过 500KB。");
      return;
    }
    const reader = new FileReader();
    reader.onload = () => {
      const result = typeof reader.result === "string" ? reader.result : "";
      setAccountProfileForm((current) => ({ ...current, avatar_data_url: result }));
      setAccountModalNotice("头像已选择，点击保存资料后生效。");
    };
    reader.onerror = () => setAccountModalNotice("读取头像失败，请重新选择图片。");
    reader.readAsDataURL(file);
  };
  const handleSaveAccountProfile = async () => {
    if (!accountProfileForm.name.trim()) {
      setAccountModalNotice("登录名不能为空。");
      return;
    }
    if (auth.mode === "demo" || !auth.token) {
      const user = {
        ...auth.user,
        name: accountProfileForm.name.trim(),
        avatar_data_url: accountProfileForm.avatar_data_url,
        public_profile: normalizePublicProfile(accountProfileForm.public_profile)
      };
      applyUpdatedCurrentUser(user);
      setAccountModalNotice("演示模式已更新当前界面；正式登录后会保存到后端。");
      return;
    }
    try {
      setAccountModalSaving(true);
      setAccountModalNotice("");
      const user = await updateCurrentUserProfile(auth.token, {
        name: accountProfileForm.name.trim(),
        avatar_data_url: accountProfileForm.avatar_data_url,
        public_profile: normalizePublicProfile(accountProfileForm.public_profile)
      });
      applyUpdatedCurrentUser(user);
      setAccountProfileForm({
        name: user.name || "",
        avatar_data_url: user.avatar_data_url || "",
        public_profile: normalizePublicProfile(user.public_profile)
      });
      setAccountModalNotice("账号信息已保存。");
    } catch (error) {
      if (isCurrentSessionExpired(error)) {
        requireFreshLogin();
        setAccountModalNotice("登录已失效，请重新登录后再保存账号信息。");
        return;
      }
      setAccountModalNotice(error instanceof Error ? error.message : "账号信息保存失败。");
    } finally {
      setAccountModalSaving(false);
    }
  };
  const handleSavePersonalSettings = async () => {
    if (auth.mode === "demo" || !auth.token) {
      const user = { ...auth.user, personal_settings: normalizePersonalSettings(personalSettingsForm) };
      applyUpdatedCurrentUser(user);
      setAccountModalNotice("演示模式已更新当前界面；正式登录后会保存到后端。");
      return;
    }
    try {
      setAccountModalSaving(true);
      setAccountModalNotice("");
      const user = await updateCurrentUserSettings(auth.token, normalizePersonalSettings(personalSettingsForm));
      applyUpdatedCurrentUser(user);
      setPersonalSettingsForm(normalizePersonalSettings(user.personal_settings));
      setAccountModalNotice("个人设置已保存。");
    } catch (error) {
      if (isCurrentSessionExpired(error)) {
        requireFreshLogin();
        setAccountModalNotice("登录已失效，请重新登录后再保存个人设置。");
        return;
      }
      setAccountModalNotice(error instanceof Error ? error.message : "个人设置保存失败。");
    } finally {
      setAccountModalSaving(false);
    }
  };
  const handlePasswordConfirm = async () => {
    if (!passwordForm.current || !passwordForm.next || !passwordForm.confirm) {
      setPasswordNotice("请完整填写当前密码、新密码和确认密码。");
      return;
    }
    if (passwordForm.next !== passwordForm.confirm) {
      setPasswordNotice("两次输入的新密码不一致。");
      return;
    }
    if (auth.mode === "demo" || !auth.token) {
      setPasswordNotice("演示模式不能修改真实密码，请正式登录后操作。");
      return;
    }
    try {
      setAccountModalSaving(true);
      setPasswordNotice("");
      const user = await changeCurrentUserPassword(auth.token, {
        current_password: passwordForm.current,
        new_password: passwordForm.next
      });
      applyUpdatedCurrentUser(user);
      setPasswordNotice("密码已修改。");
      setPasswordForm({ current: "", next: "", confirm: "" });
    } catch (error) {
      if (isCurrentSessionExpired(error)) {
        requireFreshLogin();
        setPasswordNotice("登录已失效，请重新登录后再修改密码。");
        return;
      }
      setPasswordNotice(error instanceof Error ? error.message : "密码修改失败。");
    } finally {
      setAccountModalSaving(false);
    }
  };

  return (
    <main className="app-shell">
      <aside className="desk-sidebar" aria-label="客服工作台导航">
        <div className="icon-rail">
          <div className="presence-menu-anchor">
            <button
              type="button"
              className={`rail-avatar is-${activePresenceOption.tone}${isPresenceMenuOpen ? " active" : ""}`}
              aria-label={`当前坐席状态：${activePresenceLabel}`}
              title={`当前坐席状态：${activePresenceLabel}`}
              aria-expanded={isPresenceMenuOpen}
              onClick={() => {
                setIsPresenceMenuOpen((current) => !current);
                setIsAccountMenuOpen(false);
                setIsMessageCenterOpen(false);
              }}
            >
              {accountAvatarUrl ? (
                <img src={accountAvatarUrl} alt="" />
              ) : (
                <span>{accountAvatarInitial}</span>
              )}
              <i aria-hidden="true" />
            </button>
            {isPresenceMenuOpen ? (
              <div className="presence-menu-popover" role="menu" aria-label="坐席状态">
                {agentPresenceOptions.map((option) => (
                  <div key={option.key} className="presence-menu-group">
                    <button
                      type="button"
                      role="menuitemradio"
                      aria-checked={agentPresenceStatus === option.key}
                      className={agentPresenceStatus === option.key ? "active" : ""}
                      onClick={() => {
                        setAgentPresenceStatus(option.key);
                        setIsPresenceMenuOpen(option.key === "away");
                      }}
                    >
                      <span className={`presence-dot is-${option.tone}`} aria-hidden="true" />
                      <span>{option.label}</span>
                    </button>
                    {option.leaveReasons && agentPresenceStatus === "away" ? (
                      <div className="presence-submenu" role="group" aria-label="离开原因">
                        {option.leaveReasons.map((reason) => (
                          <button
                            type="button"
                            key={reason}
                            role="menuitemradio"
                            aria-checked={agentLeaveReason === reason}
                            className={agentLeaveReason === reason ? "active" : ""}
                            onClick={() => {
                              setAgentPresenceStatus("away");
                              setAgentLeaveReason(reason);
                              setIsPresenceMenuOpen(false);
                            }}
                          >
                            {reason}
                          </button>
                        ))}
                      </div>
                    ) : null}
                  </div>
                ))}
              </div>
            ) : null}
          </div>
          <nav className="rail-nav" aria-label="一级模块">
            {primaryNavigationGroups.map((group) => {
              const isGroupActive = group.items.some((item) => getWorkspaceSectionFromHash(item.href) === activeSection);
              return (
                <a
                  key={group.label}
                  href={group.href}
                  className={`rail-button${isGroupActive ? " active" : ""}`}
                  data-workspace-nav={getWorkspaceSectionFromHash(group.href)}
                  aria-label={group.label}
                  title={group.label}
                  onClick={() => setIsPresenceMenuOpen(false)}
                >
                  {getNavigationIcon(group.icon)}
                </a>
              );
            })}
          </nav>
          <div className="rail-bottom">
            {messageCenterGroup ? (
              <button
                type="button"
                className={`rail-button${isMessageCenterOpen ? " active" : ""}`}
                aria-label="消息中心"
                title="消息中心"
                onClick={() => {
                  setIsMessageCenterOpen(true);
                  setIsAccountMenuOpen(false);
                  setIsPresenceMenuOpen(false);
                }}
              >
                {getNavigationIcon(messageCenterGroup.icon)}
              </button>
            ) : null}
            {settingsGroup ? (
              <a
                href={settingsGroup.href}
                className={`rail-button${getWorkspaceSectionFromHash(settingsGroup.href) === activeSection ? " active" : ""}`}
                data-workspace-nav={getWorkspaceSectionFromHash(settingsGroup.href)}
                aria-label="设置中心"
                title="设置中心"
                onClick={() => setIsPresenceMenuOpen(false)}
              >
                {getNavigationIcon(settingsGroup.icon)}
              </a>
            ) : null}
            <div className="account-menu-anchor">
              <button
                type="button"
                className={`rail-button rail-menu-button${isAccountMenuOpen ? " active" : ""}`}
                aria-label="主菜单"
                title="主菜单"
                aria-expanded={isAccountMenuOpen}
                onClick={() => {
                  setIsAccountMenuOpen((current) => !current);
                  setIsMessageCenterOpen(false);
                  setIsPresenceMenuOpen(false);
                }}
              >
                <Menu size={20} />
              </button>
              {isAccountMenuOpen ? (
                <div className="account-menu-popover" role="menu" aria-label="主菜单">
                  <button type="button" role="menuitem" onClick={() => openAccountMenuModal("accountInfo")}>账号信息</button>
                  <button type="button" role="menuitem" onClick={() => openAccountMenuModal("personalSettings")}>个人设置</button>
                  <button type="button" role="menuitem" onClick={() => openAccountMenuModal("changePassword")}>修改密码</button>
                  <button type="button" role="menuitem" onClick={logout}>退出系统</button>
                </div>
              ) : null}
            </div>
          </div>
        </div>

        {activeSection === "live" ? (
          <div className="dialogue-panel" aria-label="对话队列">
            <label className="dialogue-search" aria-label="搜索对话">
              <Search size={14} />
              <input
                type="search"
                value={dialogueSearch}
                onChange={(event) => setDialogueSearch(event.target.value)}
                placeholder="搜索"
              />
            </label>
            <div className="dialogue-tabs" role="tablist" aria-label="对话范围">
              <button
                type="button"
                className={dialogueScope === "current" ? "active" : ""}
                role="tab"
                aria-selected={dialogueScope === "current"}
                onClick={() => setDialogueScope("current")}
              >
                当前
              </button>
              <button
                type="button"
                className={dialogueScope === "recent" ? "active" : ""}
                role="tab"
                aria-selected={dialogueScope === "recent"}
                onClick={() => setDialogueScope("recent")}
              >
                最近
              </button>
              <button
                type="button"
                className={dialogueScope === "colleagues" ? "active" : ""}
                role="tab"
                aria-selected={dialogueScope === "colleagues"}
                onClick={() => setDialogueScope("colleagues")}
              >
                同事
              </button>
              <button type="button" className="dialogue-more" aria-label="刷新对话" title="刷新对话" onClick={refreshLiveWorkspaceResources}>
                <RefreshCw size={13} />
              </button>
            </div>
            <div className="dialogue-queue-list">
              {dialogueScope === "colleagues" ? (
                <section className="dialogue-colleague-list" aria-label="同事在线状态">
                  <div className="dialogue-section-note">当前只展示其他客服同事，不混入客户会话。</div>
                  {liveVisibleColleagues.length > 0 ? liveVisibleColleagues.map((colleague) => (
                    <button
                      type="button"
                      className={`dialogue-colleague-card${colleague.id === selectedLiveColleague?.id ? " active" : ""}`}
                      key={colleague.id}
                      onClick={() => setSelectedLiveColleagueId(colleague.id)}
                    >
                      <span className={`colleague-status-dot is-${colleague.status}`} aria-hidden="true" />
                      <span>
                        <strong>{colleague.name}</strong>
                        <small>{colleague.role} · {formatColleagueStatus(colleague.status)} · {colleague.activeChats} 个会话</small>
                      </span>
                    </button>
                  )) : (
                    <p className="dialogue-empty">没有匹配的客服同事。</p>
                  )}
                </section>
              ) : dialogueScope === "recent" ? (
                <section className="dialogue-section">
                  <div className="dialogue-section-note">最近按最后一条消息时间排序，包含已结束和当前会话。</div>
                  {liveRecentConversations.length > 0 ? liveRecentConversations.slice(0, 18).map((item) => (
                    <button
                      key={`recent-${item.id}`}
                      type="button"
                      className={`dialogue-card${item.id === selectedLiveConversationId ? " active" : ""}`}
                      onClick={() => setSelectedLiveConversationId(item.id)}
                    >
                      <span className="dialogue-card-avatar" aria-hidden="true">
                        <MessageSquare size={17} />
                      </span>
                      <span className="dialogue-card-copy">
                        <span className="dialogue-card-head">
                          <strong>{item.contact_display_name || item.subject || `客户 #${item.contact_id}`}</strong>
                          <em>{formatDateTime(item.last_message_at)}</em>
                        </span>
                        <small>{item.last_message_preview || item.channel_name || "最近对话"}</small>
                      </span>
                      {item.status === "resolved" ? <b>已结</b> : item.human_review_open_count > 0 ? <i aria-label="待处理消息">1</i> : null}
                    </button>
                  )) : (
                    <p className="dialogue-empty">没有匹配的最近会话。</p>
                  )}
                </section>
              ) : (
                <>
                  <section className="dialogue-section">
                    <button
                      type="button"
                      className="dialogue-section-title"
                      aria-expanded={!collapsedDialogueSections.queued}
                      onClick={() => toggleDialogueSection("queued")}
                      title="尚未分配给任何坐席、等待领取或分配的会话"
                    >
                      <ChevronDown className={collapsedDialogueSections.queued ? "collapsed" : ""} size={13} />
                      <span>排队中</span>
                      {liveQueuedConversations.length > 0 ? <small>{liveQueuedConversations.length}</small> : null}
                    </button>
                    {!collapsedDialogueSections.queued && liveQueuedConversations.length > 0
                      ? liveQueuedConversations.map((item) => (
                          <button
                            key={`queued-${item.id}`}
                            type="button"
                            className={`dialogue-card${item.id === selectedLiveConversationId ? " active" : ""}`}
                            onClick={() => setSelectedLiveConversationId(item.id)}
                          >
                            <span className="dialogue-card-avatar" aria-hidden="true">
                              <MessageSquare size={17} />
                            </span>
                            <span className="dialogue-card-copy">
                              <span className="dialogue-card-head">
                                <strong>{item.contact_display_name || item.subject || `客户 #${item.contact_id}`}</strong>
                                <em>{formatDateTime(item.last_message_at)}</em>
                              </span>
                              <small>{item.last_message_preview || item.channel_name || "你好"}</small>
                            </span>
                            {item.human_review_open_count > 0 ? <i aria-label="待处理消息">1</i> : null}
                          </button>
                        ))
                      : null}
                  </section>
                  <section className="dialogue-section">
                    <button
                      type="button"
                      className="dialogue-section-title"
                      aria-expanded={!collapsedDialogueSections.mine}
                      onClick={() => toggleDialogueSection("mine")}
                      title="已经分配给当前坐席、需要你继续处理的会话"
                    >
                      <ChevronDown className={collapsedDialogueSections.mine ? "collapsed" : ""} size={13} />
                      <span>{liveMineConversations.length > 0 ? `我的对话 (${liveMineConversations.length})` : "我的对话"}</span>
                    </button>
                    {!collapsedDialogueSections.mine && liveMineConversations.length > 0
                      ? liveMineConversations.map((item) => (
                          <button
                            key={`mine-${item.id}`}
                            type="button"
                            className={`dialogue-card${item.id === selectedLiveConversationId ? " active" : ""}`}
                            onClick={() => setSelectedLiveConversationId(item.id)}
                          >
                            <span className="dialogue-card-avatar" aria-hidden="true">
                              <MessageSquare size={17} />
                            </span>
                            <span className="dialogue-card-copy">
                              <span className="dialogue-card-head">
                                <strong>{item.contact_display_name || item.subject || `客户 #${item.contact_id}`}</strong>
                                <em>{formatDateTime(item.last_message_at)}</em>
                              </span>
                              <small>{item.last_message_preview || item.channel_name || "你好"}</small>
                            </span>
                            {item.human_review_open_count > 0 ? <i aria-label="待处理消息">1</i> : null}
                          </button>
                        ))
                      : null}
                  </section>
                  <section className="dialogue-section">
                    <button
                      type="button"
                      className="dialogue-section-title"
                      aria-expanded={!collapsedDialogueSections.visiting}
                      onClick={() => toggleDialogueSection("visiting")}
                      title="仍在线浏览或活跃但未必已经进入人工接待的访客"
                    >
                      <ChevronDown className={collapsedDialogueSections.visiting ? "collapsed" : ""} size={13} />
                      <span>访问中</span>
                      {liveVisitConversations.length > 0 ? <small>{liveVisitConversations.length}</small> : null}
                    </button>
                    {!collapsedDialogueSections.visiting && liveVisitConversations.length > 0
                      ? liveVisitConversations
                          .slice(0, 8)
                          .map((item) => (
                            <button
                              key={`visiting-${item.id}`}
                              type="button"
                              className={`dialogue-card${item.id === selectedLiveConversationId ? " active" : ""}`}
                              onClick={() => setSelectedLiveConversationId(item.id)}
                            >
                              <span className="dialogue-card-avatar" aria-hidden="true">
                                <MessageSquare size={17} />
                              </span>
                              <span className="dialogue-card-copy">
                                <span className="dialogue-card-head">
                                  <strong>{item.contact_display_name || item.subject || `客户 #${item.contact_id}`}</strong>
                                  <em>{formatDateTime(item.last_message_at)}</em>
                                </span>
                                <small>{item.last_message_preview || item.channel_name || "正在访问"}</small>
                              </span>
                            </button>
                          ))
                      : null}
                  </section>
                </>
              )}
            </div>
          </div>
        ) : (
          <div className="module-panel">
            <div className="module-search" aria-label="模块搜索">
              <Search size={15} />
              <span>搜索</span>
            </div>
            <div className="module-heading">
              <strong>{activeNavigationGroup?.label ?? "工作台"}</strong>
              <small>{activeNavigationGroup?.description ?? getWorkspaceRoleHint(auth.user.roles)}</small>
            </div>
            <div className="nav-role-summary compact" aria-label="当前工作台视图">
              <strong>{getWorkspaceRoleLabel(auth.user.roles)}</strong>
              <span>{getWorkspaceRoleHint(auth.user.roles)}</span>
            </div>
            <nav className="module-nav" aria-label={`${activeNavigationGroup?.label ?? "当前模块"}二级菜单`}>
              {activeSecondaryItems.length > 0 ? (
                activeSecondaryItems.map((item) => (
                  <a
                    key={item.label}
                    href={item.href}
                    className={isSecondaryNavigationItemActive(item.href, activeSection, workspaceHash) ? "active" : ""}
                    data-workspace-nav={getWorkspaceSectionFromHash(item.href)}
                  >
                    <span>{item.label}</span>
                    <small>{item.count}</small>
                  </a>
                ))
              ) : (
                <span className="module-empty">当前模块暂无二级菜单</span>
              )}
            </nav>
          </div>
        )}
      </aside>

      <section className={`workspace workspace-${activeSection}`} ref={workspaceRef}>
        {activeSection !== "channels" ? (
          <header className={`topbar${activeSection === "overview" ? " topbar-overview" : ""}${activeSection === "live" ? " topbar-live" : ""}`}>
            <div>
              <span className="page-kicker">{pageMeta.kicker}</span>
              <h1>{pageMeta.title}</h1>
              <p>{pageMeta.description}</p>
            </div>
            <div className="topbar-actions">
              <ConnectionCard connection={connection} />
              <button
                type="button"
                className="primary-action"
                onClick={() => void refreshConnectionAndAllowedResources()}
                disabled={connection.status === "loading"}
              >
                <RefreshCw size={17} />
                {connection.status === "loading" ? "连接中" : "检查连接"}
              </button>
              <button type="button" className="ghost-action" data-role-smoke="logout-button" onClick={logout}>
                <LogOut size={17} />
                退出
              </button>
            </div>
          </header>
        ) : null}

        {activeSection !== "overview" && activeSection !== "live" && activeSection !== "channels" ? (
          <RoleTaskPathStrip
            paths={visibleTaskPaths}
            activeSection={activeSection}
            roleLabel={getWorkspaceRoleLabel(auth.user.roles)}
            metrics={taskPathMetrics}
          />
        ) : null}

        {activeSection !== "overview" && activeSection !== "live" && activeSection !== "channels" ? (
          <WorkspaceRuntimeStateStrip
            mode={auth.mode}
            connectionStatus={connection.status}
            compact={false}
          />
        ) : null}

        <section className={`workspace-page workspace-page-${activeSection}${activeSection === "overview" ? " workspace-page-overview" : ""}`} aria-label={pageMeta.title}>
          {overviewTaskContext && overviewTaskContext.targetSection === activeSection ? (
            <WorkspaceTaskContextBanner
              context={overviewTaskContext}
              matchCount={overviewTaskMatchCount}
              onClear={() => {
                window.location.hash = getWorkspaceSectionHash(activeSection);
              }}
            />
          ) : null}
          {workspaceContent}
        </section>
      </section>

      {activeAccountMenuModal ? (
        <div className="account-modal-backdrop" role="presentation">
          <section
            className={`account-modal account-modal-${activeAccountMenuModal}`}
            role="dialog"
            aria-modal="true"
            aria-label={activeAccountMenuModal === "accountInfo" ? "账号信息" : activeAccountMenuModal === "personalSettings" ? "个人设置" : "修改密码"}
          >
            <header className="account-modal-header">
              <strong>{activeAccountMenuModal === "accountInfo" ? "账号信息" : activeAccountMenuModal === "personalSettings" ? "个人设置" : "修改密码"}</strong>
              <button type="button" aria-label="关闭" onClick={closeAccountMenuModal}>×</button>
            </header>

            {activeAccountMenuModal === "accountInfo" ? (
              <div className="account-info-modal-body">
                <p className="account-info-tip">
                  <span>!</span>
                  除登录名和角色信息外，其余信息都会展示给对话中的客户。
                </p>
                <div className="account-info-layout">
                  <div className="account-info-avatar" aria-hidden="true">
                    {accountProfileForm.avatar_data_url ? (
                      <img src={accountProfileForm.avatar_data_url} alt="" />
                    ) : (
                      <span>{getAvatarInitial(accountPublicProfile.display_name || accountProfileForm.name || accountLoginName)}</span>
                    )}
                  </div>
                  <div className="account-info-profile">
                    <label className="account-outline-button">
                      <Upload size={15} />
                      更换头像
                      <input type="file" accept=".jpg,.jpeg,.gif,.png,image/jpeg,image/gif,image/png" onChange={handleAvatarFileChange} />
                    </label>
                    <small>*支持.jpg .gif .png格式的图片，大小不超过500KB</small>
                  </div>
                </div>
                <dl className="account-info-list">
                  <div>
                    <dt>登录名：</dt>
                    <dd>
                      <input
                        value={accountProfileForm.name}
                        onChange={(event) => setAccountProfileForm((current) => ({ ...current, name: event.target.value }))}
                        aria-label="登录名"
                      />
                    </dd>
                  </div>
                  <div>
                    <dt>角色信息：</dt>
                    <dd>{accountRoleLabel}</dd>
                  </div>
                  <div>
                    <dt>对外昵称：</dt>
                    <dd>
                      <input
                        value={accountPublicProfile.display_name}
                        placeholder="-"
                        onChange={(event) => updateAccountPublicProfileField("display_name", event.target.value)}
                        aria-label="对外昵称"
                      />
                    </dd>
                  </div>
                  <div>
                    <dt>自定义签名：</dt>
                    <dd>
                      <input
                        value={accountPublicProfile.signature}
                        placeholder="-"
                        onChange={(event) => updateAccountPublicProfileField("signature", event.target.value)}
                        aria-label="自定义签名"
                      />
                    </dd>
                  </div>
                  <div>
                    <dt>手机：</dt>
                    <dd>
                      <input
                        value={accountPublicProfile.mobile}
                        placeholder="-"
                        onChange={(event) => updateAccountPublicProfileField("mobile", event.target.value)}
                        aria-label="手机"
                      />
                    </dd>
                  </div>
                  <div>
                    <dt>座机：</dt>
                    <dd>
                      <input
                        value={accountPublicProfile.phone}
                        placeholder="-"
                        onChange={(event) => updateAccountPublicProfileField("phone", event.target.value)}
                        aria-label="座机"
                      />
                    </dd>
                  </div>
                  <div>
                    <dt>邮箱：</dt>
                    <dd>{auth.user.email || "-"}</dd>
                  </div>
                  <div>
                    <dt>QQ：</dt>
                    <dd>
                      <input
                        value={accountPublicProfile.qq}
                        placeholder="-"
                        onChange={(event) => updateAccountPublicProfileField("qq", event.target.value)}
                        aria-label="QQ"
                      />
                    </dd>
                  </div>
                  <div>
                    <dt>微信：</dt>
                    <dd>
                      <input
                        value={accountPublicProfile.wechat}
                        placeholder="-"
                        onChange={(event) => updateAccountPublicProfileField("wechat", event.target.value)}
                        aria-label="微信"
                      />
                    </dd>
                  </div>
                </dl>
                <footer className="account-modal-footer">
                  <span>{accountModalNotice}</span>
                  <button type="button" className="primary" disabled={accountModalSaving} onClick={() => void handleSaveAccountProfile()}>
                    {accountModalSaving ? "保存中" : "保存资料"}
                  </button>
                </footer>
              </div>
            ) : null}

            {activeAccountMenuModal === "personalSettings" ? (
              <div className="personal-settings-modal-body">
                <nav className="personal-settings-tabs" aria-label="个人设置分类">
                  {[
                    { key: "basic", label: "基础设置" },
                    { key: "message", label: "消息提醒" },
                    { key: "autoReply", label: "自动回复" },
                    { key: "shortcuts", label: "快捷键" },
                    { key: "serviceNotice", label: "服务通知" }
                  ].map((tab) => (
                    <button
                      type="button"
                      key={tab.key}
                      className={personalSettingsTab === tab.key ? "active" : ""}
                      onClick={() => setPersonalSettingsTab(tab.key as PersonalSettingsTab)}
                    >
                      {tab.label}
                    </button>
                  ))}
                </nav>
                {personalSettingsTab === "basic" ? (
                  <div className="personal-settings-section">
                    <label>
                      <span>系统语言</span>
                      <select
                        value={personalSettingsForm.system_language}
                        onChange={(event) => updatePersonalSettingField("system_language", event.target.value)}
                      >
                        <option value="zh-CN">中文简体</option>
                        <option value="en">English</option>
                      </select>
                    </label>
                    <fieldset>
                      <legend>快捷回复</legend>
                      <label className="check-row">
                        <input
                          type="checkbox"
                          checked={personalSettingsForm.quick_reply_collapsed}
                          onChange={(event) => updatePersonalSettingField("quick_reply_collapsed", event.target.checked)}
                        />
                        全部折叠
                      </label>
                    </fieldset>
                    <fieldset>
                      <legend>双击快捷回复</legend>
                      <label className="radio-row">
                        <input
                          type="radio"
                          name="quick-reply-action"
                          checked={personalSettingsForm.quick_reply_double_click_action === "insert"}
                          onChange={() => updatePersonalSettingField("quick_reply_double_click_action", "insert")}
                        />
                        显示在消息输入框中
                      </label>
                      <label className="radio-row">
                        <input
                          type="radio"
                          name="quick-reply-action"
                          checked={personalSettingsForm.quick_reply_double_click_action === "send"}
                          onChange={() => updatePersonalSettingField("quick_reply_double_click_action", "send")}
                        />
                        直接发送给客人
                      </label>
                    </fieldset>
                    <fieldset>
                      <legend>引用方式</legend>
                      <label className="radio-row">
                        <input
                          type="radio"
                          name="quote-mode"
                          checked={personalSettingsForm.quick_reply_quote_mode === "replace"}
                          onChange={() => updatePersonalSettingField("quick_reply_quote_mode", "replace")}
                        />
                        覆盖引用，引用新快捷回复时词条内容会覆盖输入框中已有内容
                      </label>
                      <label className="radio-row">
                        <input
                          type="radio"
                          name="quote-mode"
                          checked={personalSettingsForm.quick_reply_quote_mode === "append"}
                          onChange={() => updatePersonalSettingField("quick_reply_quote_mode", "append")}
                        />
                        叠加引用，引用新快捷回复时词条内容会累加至输入框
                      </label>
                    </fieldset>
                    <fieldset>
                      <legend>输入状态</legend>
                      <label className="check-row">
                        <input
                          type="checkbox"
                          checked={personalSettingsForm.show_typing_status}
                          onChange={(event) => updatePersonalSettingField("show_typing_status", event.target.checked)}
                        />
                        允许客人看到我的输入状态
                      </label>
                    </fieldset>
                    <div className="personal-settings-subhead">
                      <strong>翻译</strong>
                      <button type="button">用量统计</button>
                    </div>
                    <label>
                      <span>默认目标语言</span>
                      <select
                        value={personalSettingsForm.default_translate_language}
                        onChange={(event) => updatePersonalSettingField("default_translate_language", event.target.value)}
                      >
                        <option value="en">英语</option>
                        <option value="ja">日语</option>
                        <option value="ko">韩语</option>
                        <option value="zh-CN">中文简体</option>
                      </select>
                    </label>
                    <footer className="account-modal-footer">
                      <span>{accountModalNotice}</span>
                      <button type="button" className="primary" disabled={accountModalSaving} onClick={() => void handleSavePersonalSettings()}>
                        {accountModalSaving ? "保存中" : "保存设置"}
                      </button>
                    </footer>
                  </div>
                ) : (
                  <div className="personal-settings-placeholder">
                    <FileText size={32} />
                    <span>{personalSettingsTab === "message" ? "暂无消息提醒配置" : personalSettingsTab === "autoReply" ? "暂无自动回复配置" : personalSettingsTab === "shortcuts" ? "暂无快捷键配置" : "暂无服务通知配置"}</span>
                  </div>
                )}
              </div>
            ) : null}

            {activeAccountMenuModal === "changePassword" ? (
              <div className="change-password-modal-body">
                <label>
                  <span>当前密码</span>
                  <input
                    type="password"
                    value={passwordForm.current}
                    placeholder="请输入当前密码"
                    onChange={(event) => setPasswordForm((current) => ({ ...current, current: event.target.value }))}
                  />
                </label>
                <label>
                  <span>新密码</span>
                  <input
                    type="password"
                    value={passwordForm.next}
                    placeholder="请输入新密码"
                    onChange={(event) => setPasswordForm((current) => ({ ...current, next: event.target.value }))}
                  />
                </label>
                <label>
                  <span>确认密码</span>
                  <input
                    type="password"
                    value={passwordForm.confirm}
                    placeholder="请输入确认密码"
                    onChange={(event) => setPasswordForm((current) => ({ ...current, confirm: event.target.value }))}
                  />
                </label>
                {passwordNotice ? <p className="change-password-notice">{passwordNotice}</p> : null}
                <footer>
                  <button type="button" className="primary" disabled={accountModalSaving} onClick={() => void handlePasswordConfirm()}>
                    {accountModalSaving ? "提交中" : "确定"}
                  </button>
                  <button type="button" disabled={accountModalSaving} onClick={closeAccountMenuModal}>取消</button>
                </footer>
              </div>
            ) : null}
          </section>
        </div>
      ) : null}

      {isMessageCenterOpen ? (
        <div className="message-center-backdrop" role="presentation" onClick={() => setIsMessageCenterOpen(false)}>
          <section
            className="message-center-modal"
            role="dialog"
            aria-modal="true"
            aria-label="消息中心"
            onClick={(event) => event.stopPropagation()}
          >
            <header>
              <strong>消息中心</strong>
              <button type="button" aria-label="关闭消息中心" onClick={() => setIsMessageCenterOpen(false)}>×</button>
            </header>
            <div className="message-center-empty">
              <FileText size={34} />
              <span>暂无数据</span>
            </div>
          </section>
        </div>
      ) : null}
    </main>
  );
}

function RoleTaskPathStrip({
  paths,
  activeSection,
  roleLabel,
  metrics
}: {
  paths: RoleTaskPath[];
  activeSection: WorkspaceSection;
  roleLabel: string;
  metrics: RoleTaskPathMetrics;
}) {
  if (paths.length === 0) {
    return null;
  }

  return (
    <section className="role-task-paths" aria-label={`${roleLabel}任务路径`}>
      <div className="role-task-paths-heading">
        <span>今日任务路径</span>
        <strong>{roleLabel}</strong>
      </div>
      <div className="role-task-path-grid">
        {paths.map((path, index) => {
          const section = getWorkspaceSectionFromHash(path.href);
          const metric = getRoleTaskPathMetric(path.id, metrics);
          return (
            <a
              key={path.id}
              className={`role-task-path is-${metric.tone}${section === activeSection ? " is-active" : ""}`}
              data-role-task-id={path.id}
              href={path.href}
              aria-current={section === activeSection ? "page" : undefined}
            >
              <span className="role-task-index">{String(index + 1).padStart(2, "0")}</span>
              <span className="role-task-copy">
                <strong>{path.label}</strong>
                <small>{path.intent}</small>
              </span>
              <span className="role-task-metric" aria-label={`${path.label}当前状态`}>
                <strong>{metric.value}</strong>
                <small>{metric.note}</small>
              </span>
            </a>
          );
        })}
      </div>
    </section>
  );
}

function getRoleTaskPathMetric(id: string, metrics: RoleTaskPathMetrics): RoleTaskPathMetric {
  const highRiskReviews = metrics.reviewItems.filter((item) => ["high", "critical"].includes(item.risk_level)).length;
  const openReviews = metrics.reviewItems.length;
  const pendingDrafts = metrics.outboxDrafts.filter((draft) => draft.status === "pending_confirmation").length;
  const readyDrafts = metrics.outboxDrafts.filter((draft) => draft.status === "ready_to_send").length;
  const channelExceptions =
    metrics.failureReviews.length +
    metrics.deliveryJobs.filter((job) => ["blocked", "dead_letter", "dead_lettered", "failed"].includes(job.status)).length;
  const openTickets = "data" in metrics.supportTickets ? metrics.supportTickets.data.total : 0;
  const openLeads = "data" in metrics.salesLeads ? metrics.salesLeads.data.total : 0;
  const openKnowledgeGaps = "data" in metrics.knowledgeGaps ? metrics.knowledgeGaps.data.total : 0;
  const dashboardHealth = metrics.businessOpsDashboard.data?.summary.health_score ?? null;
  const inboundConversations = metrics.businessOpsDashboard.data?.summary.inbound_conversations ?? openReviews + pendingDrafts + readyDrafts;

  switch (id) {
    case "ops-risk-scan":
      return {
        value: dashboardHealth === null ? `${inboundConversations}` : `${dashboardHealth}`,
        note: dashboardHealth === null ? "今日信号" : "健康分",
        tone: dashboardHealth === null || dashboardHealth >= 82 ? "success" : dashboardHealth >= 68 ? "warning" : "urgent"
      };
    case "review-risk-drafts":
      return {
        value: `${highRiskReviews}/${openReviews}`,
        note: "高风险/待审",
        tone: highRiskReviews > 0 ? "urgent" : openReviews > 0 ? "warning" : "success"
      };
    case "outbox-gate":
      return {
        value: `${pendingDrafts + readyDrafts}`,
        note: "待发门禁",
        tone: pendingDrafts + readyDrafts > 0 ? "warning" : "success"
      };
    case "live-inbox":
      return {
        value: `${inboundConversations}`,
        note: "会话信号",
        tone: openReviews > 0 ? "warning" : "success"
      };
    case "customer-followup":
      return {
        value: `${openLeads}`,
        note: "线索",
        tone: openLeads > 0 ? "normal" : "success"
      };
    case "ticket-sla":
      return {
        value: `${openTickets}`,
        note: "工单",
        tone: openTickets > 0 ? "warning" : "success"
      };
    case "quality-cause-review":
      return {
        value: `${highRiskReviews + channelExceptions + openKnowledgeGaps}`,
        note: "错因信号",
        tone: highRiskReviews + channelExceptions + openKnowledgeGaps > 0 ? "warning" : "success"
      };
    case "knowledge-gap-repair":
      return {
        value: `${openKnowledgeGaps}`,
        note: "知识缺口",
        tone: openKnowledgeGaps > 0 ? "warning" : "success"
      };
    case "channel-connector-status":
      return {
        value: `${channelExceptions}`,
        note: "渠道异常",
        tone: channelExceptions > 0 ? "urgent" : "success"
      };
    case "ops-health-check":
      return {
        value: metrics.businessOpsDashboard.status === "loading" ? "刷新中" : "只读",
        note: "运维状态",
        tone: metrics.businessOpsDashboard.status === "error" ? "warning" : "normal"
      };
    default:
      return { value: "查看", note: "下一步", tone: "normal" };
  }
}

function getInitialWorkspaceSection(): WorkspaceSection {
  if (typeof window === "undefined") {
    return "overview";
  }
  return getWorkspaceSectionFromHash(window.location.hash);
}

function isDemoPreviewRequested() {
  if (typeof window === "undefined") {
    return false;
  }
  return new URLSearchParams(window.location.search).get("demo") === "1";
}

function createDemoCurrentUser(): CurrentUser {
  return {
    id: "1",
    name: "演示负责人",
    email: "demo@wanfa.local",
    roles: ["owner"],
    permissions: Object.values(PERMISSIONS),
    tenant: {
      id: "demo-tenant",
      name: "万法常世演示工作台",
      slug: "wanfa-demo",
      plan: "standard_ops"
    },
    avatar_data_url: "",
    public_profile: defaultPublicProfile,
    personal_settings: defaultPersonalSettings
  };
}

function getNavigationIcon(icon: string): ReactElement {
  const size = 18;
  const icons: Record<string, ReactElement> = {
    message: <MessageSquare size={size} />,
    customers: <Users size={size} />,
    tickets: <BriefcaseBusiness size={size} />,
    inbox: <Mail size={size} />,
    history: <History size={size} />,
    report: <BarChart3 size={size} />,
    bot: <Bot size={size} />,
    marketing: <UserPlus size={size} />,
    wecom: <ShieldCheck size={size} />,
    sms: <Send size={size} />,
    form: <FileText size={size} />,
    notice: <Bell size={size} />,
    settings: <Settings size={size} />,
    menu: <Menu size={size} />
  };
  return icons[icon] ?? <Menu size={size} />;
}

function getWorkspaceSectionFromHash(hash: string): WorkspaceSection {
  const value = getWorkspaceHashPath(hash);
  const aliases: Record<string, WorkspaceSection> = {
    overview: "overview",
    conversations: "conversations",
    tickets: "tickets",
    sla: "tickets",
    "support-tickets": "tickets",
    live: "live",
    desk: "live",
    reviews: "reviews",
    outbox: "outbox",
    contacts: "contacts",
    leads: "leads",
    knowledge: "knowledge",
    gaps: "gaps",
    "knowledge-gaps": "gaps",
    channels: "channels",
    sandbox: "channels",
    failures: "channels",
    model: "model",
    evals: "evals",
    quality: "quality",
    bi: "quality",
    ops: "ops",
    operations: "ops",
    health: "ops",
    pilot: "pilot",
    settings: "settings"
  };
  return aliases[value] ?? "overview";
}

function getChannelEntryIdFromHash(hash: string) {
  const channel = getWorkspaceHashParams(hash).get("channel");
  return ["website", "wechat_kf", "wecom", "wechat_official", "wechat_miniapp"].includes(channel ?? "")
    ? channel ?? "website"
    : "website";
}

function isSecondaryNavigationItemActive(href: string, activeSection: WorkspaceSection, currentHash: string) {
  if (getWorkspaceSectionFromHash(href) !== activeSection) {
    return false;
  }
  if (activeSection !== "channels") {
    return true;
  }
  return getChannelEntryIdFromHash(href) === getChannelEntryIdFromHash(currentHash);
}

function buildChannelIdentityFallbacks(items: ConversationInboxItem[]): Record<number, ChannelIdentitySummary> {
  const result: Record<number, ChannelIdentitySummary> = {};
  items.forEach((item) => {
    if (result[item.channel_id]) {
      return;
    }
    result[item.channel_id] = {
      channelId: item.channel_id,
      platform: item.channel_name || item.channel_type || `渠道 #${item.channel_id}`,
      accountName: item.channel_name || item.channel_type || `账号 #${item.channel_id}`,
      storeName: item.channel_name || item.channel_type || "未登记入口",
      providerMode: "unknown",
      authorizationStatus: "unknown",
      replyMode: "draft_only",
      healthLabel: item.sla_status === "breached" ? "需处理" : "待确认",
      lastSyncLabel: formatDateTime(item.last_message_at)
    };
  });
  return result;
}

function buildChannelIdentityFromAccounts(accounts: ChannelAccount[]): Record<number, ChannelIdentitySummary> {
  const result: Record<number, ChannelIdentitySummary> = {};
  accounts.forEach((account) => {
    if (result[account.channel_id]) {
      return;
    }
    result[account.channel_id] = {
      channelId: account.channel_id,
      platform: account.platform || formatChannelAccountProvider(account.provider) || `渠道 #${account.channel_id}`,
      accountName: account.account_name || `账号 #${account.channel_id}`,
      storeName: account.store_name || account.entrypoint_name || "未登记入口",
      providerMode: account.access_status || "unknown",
      authorizationStatus: account.authorization_status || "unknown",
      replyMode: account.reply_mode || "draft_only",
      healthLabel: formatChannelAccountHealth(account),
      lastSyncLabel: account.last_sync_at ? formatDateTime(account.last_sync_at) : "尚未同步"
    };
  });
  return result;
}

function formatChannelAccountProvider(value: string) {
  const labels: Record<string, string> = {
    wecom: "微信客服",
    official_account: "公众号",
    douyin: "抖音",
    taobao: "淘宝",
    jd: "京东",
    pdd: "拼多多",
    website: "官网"
  };
  return labels[value] ?? value;
}

function formatChannelAccountHealth(account: ChannelAccount) {
  const accessLabels: Record<string, string> = {
    active: "可用",
    ready: "可用",
    website_ready: "官网可用",
    callback_pending: "待回调验证",
    sandbox_configuring: "配置中",
    official_configuring: "待官方授权",
    rpa_research_only: "仅研究",
    planned: "待配置",
    disabled: "已停用"
  };
  const healthLabels: Record<string, string> = {
    healthy: "健康",
    configuring: "配置中",
    degraded: "需处理",
    blocked: "阻断",
    unknown: "待确认"
  };
  const fallback = account.access_status || account.health_status || "待确认";
  return accessLabels[account.access_status] ?? healthLabels[account.health_status] ?? fallback;
}

function getWorkspaceHashPath(hash: string) {
  return hash.replace(/^#/, "").split("?")[0].split("&")[0];
}

function getWorkspaceHashParams(hash: string) {
  const query = hash.includes("?") ? hash.slice(hash.indexOf("?") + 1) : "";
  return new URLSearchParams(query);
}

function parseWorkspaceTaskContext(hash: string): WorkspaceTaskContext | null {
  const params = getWorkspaceHashParams(hash);
  const source = params.get("from");
  if ((source !== "overview" && source !== "quality" && source !== "knowledge") || !params.get("task")) {
    return null;
  }
  const targetSection = getWorkspaceSectionFromHash(hash);
  const channelIdValue = params.get("channel_id");
  const channelId = channelIdValue && channelIdValue !== "all" ? Number(channelIdValue) : null;
  return {
    source,
    targetSection,
    task: params.get("task") ?? "overview-task",
    title: params.get("title") ?? (source === "quality" ? "处理质量复盘任务" : "处理运营总览任务"),
    description: params.get("description") ?? formatWorkspaceTaskSourceFallbackDescription(source),
    range: params.get("range") ?? "today",
    channelId: Number.isFinite(channelId) ? channelId : null,
    channelLabel: params.get("channel_label") ?? (channelId ? `渠道 #${channelId}` : "全部渠道"),
    status: params.get("status") || undefined,
    queue: params.get("queue") || undefined,
    emptyText: params.get("empty") ?? "本时间窗口暂无对应任务。"
  };
}

function buildWorkspaceTaskHref(
  section: WorkspaceSection,
  params: {
    task: string;
    title: string;
    description: string;
    range: string;
    channelId: number | null;
    channelLabel: string;
    source?: WorkspaceTaskSource;
    status?: string;
    queue?: string;
    emptyText?: string;
  }
) {
  const query = new URLSearchParams();
  query.set("from", params.source ?? "overview");
  query.set("task", params.task);
  query.set("title", params.title);
  query.set("description", params.description);
  query.set("range", params.range);
  query.set("channel_id", params.channelId === null ? "all" : String(params.channelId));
  query.set("channel_label", params.channelLabel);
  if (params.status) query.set("status", params.status);
  if (params.queue) query.set("queue", params.queue);
  if (params.emptyText) query.set("empty", params.emptyText);
  return `${getWorkspaceSectionHash(section)}?${query.toString()}`;
}

function formatWorkspaceTaskSourceFallbackDescription(source: WorkspaceTaskSource) {
  if (source === "quality") {
    return "该入口来自质量复盘，目标页已按错因和修复上下文收口。";
  }
  if (source === "knowledge") {
    return "该入口来自知识运营流程，目标页已按补知识、回归和发布门禁上下文收口。";
  }
  return "该入口来自运营总览，目标页已按当前处理上下文收口。";
}

function formatOpsRangeLabel(value: string) {
  if (value === "7d") return "近 7 天";
  if (value === "30d") return "近 30 天";
  return "今日";
}

function formatWorkspaceTaskQueueLabel(value: string) {
  const labels: Record<string, string> = {
    high_risk: "高风险",
    needs_review: "待审核",
    delivery_failed: "发送异常",
    pending_outbox: "待发送",
    no_knowledge: "无知识",
    sla_breached: "超时",
    all: "全部"
  };
  return labels[value] ?? value;
}

function formatWorkspaceTaskStatusLabel(value: string) {
  const labels: Record<string, string> = {
    no_knowledge: "无知识命中",
    low_confidence: "低置信",
    high_risk: "高风险",
    needs_regression: "待回归",
    citation_weak: "引用弱",
    pending_confirmation: "待确认",
    ready_to_send: "待发送",
    open: "待处理",
    draft: "草稿",
    active: "已启用",
    published: "已发布",
    blocked: "已阻断",
    severe: "严重",
    retryable: "可重试",
    manual: "需人工",
    all: "全部"
  };
  return labels[value] ?? value;
}

function getWorkspaceTaskMatchCount(
  context: WorkspaceTaskContext,
  data: {
    conversationItems: ConversationInboxItem[];
    reviewItems: HumanReviewInboxItem[];
    outboxDrafts: OutboxDraft[];
    failureReviews: DeliveryFailureReview[];
    deliveryJobs: OutboxDeliveryJob[];
    knowledgeGaps: KnowledgeGap[];
    knowledgeDocuments?: KnowledgeDocument[];
    knowledgePublications?: KnowledgeDocumentPublication[];
    knowledgeEvaluation?: KnowledgeEvaluationState;
  }
) {
  const matchesChannel = (channelId: number) => context.channelId === null || context.channelId === channelId;
  if (context.task === "live-inbound") {
    return data.conversationItems.filter((item) => matchesChannel(item.channel_id)).length;
  }
  if (context.task === "high-risk-conversations") {
    return data.conversationItems.filter((item) => matchesChannel(item.channel_id) && ["critical", "high"].includes(item.priority)).length;
  }
  if (context.task === "high-risk-reviews") {
    return data.reviewItems.filter((item) => matchesChannel(item.conversation.channel_id) && ["critical", "high"].includes(item.risk_level)).length;
  }
  if (context.task === "pending-outbox") {
    return data.outboxDrafts.filter((draft) => matchesChannel(draft.channel_id) && draft.status === (context.status ?? "pending_confirmation")).length;
  }
  if (context.task === "knowledge-gaps") {
    return data.knowledgeGaps.filter((gap) =>
      context.status ? gap.status === context.status : ["open", "triaged", "in_progress"].includes(gap.status)
    ).length;
  }
  if (context.task === "channel-exceptions") {
    const failureCount = data.failureReviews.filter((item) => matchesChannel(item.channel_id) && item.status === "open").length;
    const blockedCount = data.deliveryJobs.filter(
      (job) => matchesChannel(job.channel_id) && ["blocked", "dead_letter", "dead_lettered", "failed"].includes(job.status)
    ).length;
    return failureCount + blockedCount;
  }
  if (context.task === "quality-knowledge-gap") {
    return data.knowledgeGaps.filter((gap) =>
      context.status ? gap.status === context.status : ["open", "triaged", "in_progress"].includes(gap.status)
    ).length;
  }
  if (context.task === "quality-low-confidence") {
    return data.reviewItems.filter((item) =>
      matchesChannel(item.conversation.channel_id) && (item.evidence.confidence ?? 0) < 0.55
    ).length;
  }
  if (context.task === "quality-high-risk") {
    return data.reviewItems.filter((item) =>
      matchesChannel(item.conversation.channel_id) && ["critical", "high"].includes(item.risk_level)
    ).length;
  }
  if (context.task === "quality-channel-failure") {
    const failureCount = data.failureReviews.filter((item) => matchesChannel(item.channel_id) && item.status === "open").length;
    const blockedCount = data.deliveryJobs.filter(
      (job) => matchesChannel(job.channel_id) && ["blocked", "dead_letter", "dead_lettered", "failed"].includes(job.status)
    ).length;
    return failureCount + blockedCount;
  }
  if (context.task === "quality-pending-send") {
    return data.outboxDrafts.filter((draft) =>
      matchesChannel(draft.channel_id) && ["pending_confirmation", "ready_to_send", "queued"].includes(draft.status)
    ).length;
  }
  if (context.task === "quality-regression") {
    return data.knowledgeGaps.filter((gap) => {
      const remediation = knowledgeGapRemediationPayload(gap);
      return ["open", "triaged", "in_progress"].includes(gap.status) && !remediation.regression_evaluation_case_id;
    }).length;
  }
  if (context.task === "knowledge-quality-cause") {
    return data.knowledgeGaps.filter((gap) => ["open", "triaged", "in_progress"].includes(gap.status)).length;
  }
  if (context.task === "knowledge-gap-draft") {
    return data.knowledgeGaps.filter((gap) =>
      ["open", "triaged", "in_progress"].includes(gap.status) && !gap.linked_knowledge_document_id
    ).length;
  }
  if (context.task === "knowledge-document-edit") {
    return (data.knowledgeDocuments ?? []).filter((document) =>
      context.status ? document.status === context.status : document.status === "draft" || document.ingestion_status === "processing"
    ).length;
  }
  if (context.task === "knowledge-regression-gate") {
    return data.knowledgeGaps.filter((gap) => {
      const remediation = knowledgeGapRemediationPayload(gap);
      return ["open", "triaged", "in_progress"].includes(gap.status) && !remediation.regression_evaluation_case_id;
    }).length;
  }
  if (context.task === "knowledge-publication-history") {
    const publicationCount = (data.knowledgePublications ?? []).filter((publication) =>
      context.status ? publication.status === context.status : true
    ).length;
    if (publicationCount > 0) {
      return publicationCount;
    }
    return (data.knowledgeDocuments ?? []).filter((document) =>
      context.status ? document.status === context.status : document.status === "active"
    ).length;
  }
  return null;
}

function getWorkspaceSectionHash(section: WorkspaceSection) {
  return `#${section}`;
}

function getAccessibleWorkspaceSection(
  requestedSection: WorkspaceSection,
  groups: ReturnType<typeof getNavigationGroupsForRoles>,
  fallbackSection: WorkspaceSection
) {
  return isWorkspaceSectionVisible(requestedSection, groups) ? requestedSection : fallbackSection;
}

function getPostAuthWorkspaceSection(roles: string[], currentHash: string) {
  const requestedSection = getWorkspaceSectionFromHash(currentHash);
  const groups = getNavigationGroupsForRoles(roles);
  const fallbackSection = getWorkspaceSectionFromHash(getDefaultNavigationHrefForRoles(roles));
  return getAccessibleWorkspaceSection(requestedSection, groups, fallbackSection);
}

function isWorkspaceSectionVisible(section: WorkspaceSection, groups: ReturnType<typeof getNavigationGroupsForRoles>) {
  return groups.some((group) =>
    group.items.some((item) => getWorkspaceSectionFromHash(item.href) === section)
  );
}

function getWorkspaceRoleLabel(roles: string[]) {
  if (hasWorkspaceRole(roles, ["owner"])) {
    return "管理员视图";
  }
  if (hasWorkspaceRole(roles, ["admin"])) {
    return "运营管理视图";
  }
  if (hasWorkspaceRole(roles, ["agent"])) {
    return "坐席视图";
  }
  if (hasWorkspaceRole(roles, ["viewer"])) {
    return "只读视图";
  }
  return "受限视图";
}

function getWorkspaceRoleHint(roles: string[]) {
  if (hasWorkspaceRole(roles, ["owner", "admin"])) {
    return "可见运营、知识、渠道和管理运维";
  }
  if (hasWorkspaceRole(roles, ["agent"])) {
    return "先看总览，再进入接待";
  }
  if (hasWorkspaceRole(roles, ["viewer"])) {
    return "仅保留总览与复盘入口";
  }
  return "仅显示可访问入口";
}

function hasWorkspaceRole(roles: string[], allowed: readonly string[]) {
  return roles.some((role) => allowed.includes(role));
}

function getWorkspacePageMeta(section: WorkspaceSection) {
  const meta: Record<WorkspaceSection, { title: string; kicker: string; description: string }> = {
    overview: {
      title: "运营总览",
      kicker: "全局信号",
      description: "只展示今日队列、会话预览、渠道健康和风险证据，不再把所有业务模块堆在一页。"
    },
    conversations: {
      title: "会话收件箱",
      kicker: "坐席处理",
      description: "按客户等待、SLA、渠道、接管状态和下一步动作统一排队。"
    },
    tickets: {
      title: "工单/SLA",
      kicker: "服务闭环",
      description: "把需要持续跟进的会话沉淀为工单，跟踪负责人、状态、SLA 到期和解决结果。"
    },
    live: {
      title: "多渠道对话台",
      kicker: "坐席主界面",
      description: "用会话列表、对话流和转人工状态承接日常客服处理；样例渠道不代表真实平台已接通。"
    },
    reviews: {
      title: "人工审核",
      kicker: "回复放行",
      description: "集中核对低置信、高风险、无知识命中和模型异常的回复草稿。"
    },
    outbox: {
      title: "待发送草稿",
      kicker: "发送前门禁",
      description: "管理待确认草稿、发送计划、发送队列和外发关闭边界。"
    },
    contacts: {
      title: "联系人中心",
      kicker: "客户画像",
      description: "聚合客户身份、最近会话、工单、线索和下一步动作，让坐席先理解客户再回复。"
    },
    leads: {
      title: "线索跟进",
      kicker: "转化管理",
      description: "把报价、试点、部署和采购类咨询沉淀为线索，跟踪负责人、阶段和转化结果。"
    },
    knowledge: {
      title: "知识库运营",
      kicker: "文档与引用",
      description: "导入文档、查看分块、检索证据，并为回复提供可追溯引用。"
    },
    gaps: {
      title: "知识缺口闭环",
      kicker: "运营待办",
      description: "从低置信人审和题库失败沉淀缺口，分派处理、补知识、再回归，不把问题停留在报表里。"
    },
    channels: {
      title: "渠道接入",
      kicker: "官方通道",
      description: "展示官方通道接入状态、回调验证、渠道健康和失败复盘；真实外发仍保持关闭。"
    },
    model: {
      title: "模型路由",
      kicker: "决策链路",
      description: "展示当前模型组合、路由边界和转人工门禁，避免把模型能力说成自动回复已上线。"
    },
    evals: {
      title: "质量评测",
      kicker: "题集回归",
      description: "用固定题集检查检索命中、引用覆盖、期望词覆盖和需复盘问题。"
    },
    quality: {
      title: "质量诊断",
      kicker: "运营分析",
      description: "跟踪低置信、无知识、高风险、外发异常和题库失败，定位错因并推动知识、渠道和审核动作。"
    },
    ops: {
      title: "运维与告警",
      kicker: "后台进程",
      description: "查看 worker 心跳、最近运行、失败风险、外发开关和只读告警规则，服务部署后的远程排障。"
    },
    pilot: {
      title: "本地试运行准备",
      kicker: "交付前检查",
      description: "按资料导入、知识复测和交付档案收束本地试运行候选。"
    },
    settings: {
      title: "账号与本地维护",
      kicker: "本地治理",
      description: "管理本地账号、角色、密码、诊断包、备份和签名更新包；未完成授权和验收前不会触发真实外部动作。"
    }
  };
  return meta[section];
}

function PlanningWorkspacePanel({
  id,
  title,
  icon,
  description,
  items
}: {
  id: string;
  title: string;
  icon: ReactElement;
  description: string;
  items: string[];
}) {
  return (
    <section className="panel planning-panel" id={id} aria-label={title}>
      <div className="panel-heading">
        <div>
          <h2>{title}</h2>
          <p>{description}</p>
        </div>
        {icon}
      </div>
      <div className="planning-grid">
        {items.map((item, index) => (
          <article key={item} className="planning-card">
            <span>{String(index + 1).padStart(2, "0")}</span>
            <p>{item}</p>
          </article>
        ))}
      </div>
      <p className="inline-notice">未完成授权、验收和管理员确认前，本页不会触发真实外部动作。</p>
    </section>
  );
}

function ModelRoutingPanel({
  latestEvaluationRun,
  reviewItems,
  outboxDrafts,
  ragGovernance,
  llmOpsReadiness,
  hasToken,
  onRefresh
}: {
  latestEvaluationRun: KnowledgeEvaluationRun | null;
  reviewItems: HumanReviewInboxItem[];
  outboxDrafts: OutboxDraft[];
  ragGovernance: RagCostGovernanceState;
  llmOpsReadiness: LlmOpsReadinessState;
  hasToken: boolean;
  onRefresh: () => void;
}) {
  const lowConfidence = reviewItems.filter((item) => (item.evidence.confidence ?? 0) < 0.55).length;
  const pendingDrafts = outboxDrafts.filter((draft) => draft.status === "pending_confirmation").length;
  const governance = ragGovernance.data;
  const llmOps = llmOpsReadiness.data;
  const productionReadiness = governance?.production_readiness;
  const metricByLabel = new Map(governance?.knowledge_metrics.map((metric) => [metric.label, metric]) ?? []);
  const gateStatusLabel = {
    passed: "通过",
    warning: "待加强",
    blocked: "阻断"
  } as const;
  const maturityLabel = {
    blocked: "未达标",
    candidate: "候选",
    ready_for_controlled_pilot: "可试点"
  } as const;
  const productionStatusLabel = {
    blocked: "未就绪",
    candidate: "候选",
    ready_for_controlled_pilot: "可试点"
  } as const;
  const maturityTone =
    governance?.maturity_status === "ready_for_controlled_pilot"
      ? "is-good"
      : governance?.maturity_status === "candidate"
        ? "is-warning"
        : "is-danger";
  const llmOpsTone =
    llmOps?.status === "llm_ops_ready_for_controlled_pilot"
      ? "is-good"
      : llmOps?.status === "blocked"
        ? "is-danger"
        : "is-warning";
  const llmOpsStatusLabel = {
    blocked: "阻断",
    llm_ops_observability_candidate: "候选",
    llm_ops_observability_ready_not_redteam_complete: "待红队",
    llm_ops_ready_for_controlled_pilot: "可试点"
  } as const;
  const routes = [
    {
      name: "高置信 FAQ",
      model: "不调大模型",
      policy: "命中标准答案且风险低时直接生成可审草稿"
    },
    {
      name: "普通客服问题",
      model: "百炼 / 千问",
      policy: "结合知识证据生成回复建议，进入人工确认或外发前置门禁"
    },
    {
      name: "复杂或高风险问题",
      model: "高阶模型或转人工",
      policy: "投诉、赔付、法务、合同和隐私问题优先转人工"
    },
    {
      name: "模型不可用",
      model: "降级转人工",
      policy: "不静默伪装成功，进入人工接管和失败复盘"
    }
  ];

  return (
    <section className="panel model-routing-panel" id="workspace-model" aria-label="自动回复策略">
      <div className="panel-heading">
        <div>
          <h2>自动回复策略</h2>
          <p>按问题置信度、风险等级和证据覆盖选择路径；当前只把模型产物作为可审草稿。</p>
        </div>
        <button className="icon-button" type="button" onClick={onRefresh} disabled={!hasToken || ragGovernance.status === "loading"} title="刷新治理状态">
          <RefreshCw size={16} />
        </button>
      </div>
      <div className="quality-metric-grid">
        <QualityMetric label="低置信转人工" value={`${lowConfidence}`} note="当前进入人工接管的低置信样例" />
        <QualityMetric label="待确认回复" value={`${pendingDrafts}`} note="模型生成内容仍需人工确认" />
        <QualityMetric
          label="最近命中"
          value={latestEvaluationRun ? formatPercent(latestEvaluationRun.hit_rate) : "-"}
          note={latestEvaluationRun ? `复盘 ${latestEvaluationRun.needs_review_cases} 题` : "尚未运行评测"}
        />
        <QualityMetric label="真实外发" value="关闭" note="模型回答不会直接发到外部平台" />
      </div>
      <div className="rag-governance-grid" data-rag-cost-governance="p3-06u-26h2w7">
        <article className="rag-governance-card">
          <div className="rag-governance-card-head">
            <span>生产检索准备度</span>
            <strong className={`status-pill ${maturityTone}`}>
              {productionReadiness
                ? productionStatusLabel[productionReadiness.status]
                : governance
                  ? maturityLabel[governance.maturity_status]
                  : ragGovernance.status === "loading"
                    ? "读取中"
                    : "未读取"}
            </strong>
          </div>
          <p>
            {productionReadiness
              ? productionReadiness.production_switch_allowed
                ? "生产候选检索、答案质量和成本门禁已具备受控试点条件。"
                : productionReadiness.blockers[0] ?? "生产检索仍在补证据，当前不能切换为正式生产检索。"
              : governance?.summary ?? ragGovernance.message}
          </p>
          <div className="rag-governance-metrics">
            <span>启用文档：{metricByLabel.get("启用文档")?.value ?? "-"}</span>
            <span>已索引片段：{metricByLabel.get("已索引片段")?.value ?? "-"}</span>
            <span>生产向量：{productionReadiness?.pgvector_runtime_ready ? "已具备" : "未就绪"}</span>
            <span>
              真实资料：
              {productionReadiness?.real_customer_material_ready
                ? "已就绪"
                : `${productionReadiness?.customer_material_question_count ?? 0}/50`}
            </span>
            <span>题库基线：{productionReadiness?.customer_question_bank_ready ? "已达标" : `${productionReadiness?.active_evaluation_cases ?? 0}/50`}</span>
          </div>
        </article>
        <article className="rag-governance-card">
          <div className="rag-governance-card-head">
            <span>向量与评测</span>
            <Bot size={18} />
          </div>
          <p>
            {governance
              ? `${governance.vector_profile.configured_vector_store} / ${governance.vector_profile.configured_reranker}`
              : "等待读取检索配置"}
          </p>
          <div className="rag-governance-metrics">
            <span>命中率：{governance ? formatPercent(governance.latest_evaluation.hit_rate) : "-"}</span>
            <span>引用覆盖：{governance ? formatPercent(governance.latest_evaluation.citation_coverage) : "-"}</span>
            <span>检索模型：{governance?.latest_provider_smoke.embedding_model || "-"}</span>
            <span>
              检索成本：
              {governance ? `${governance.latest_provider_smoke.estimated_cost} ${governance.latest_provider_smoke.cost_currency}` : "-"}
            </span>
          </div>
        </article>
        <article className="rag-governance-card">
          <div className="rag-governance-card-head">
            <span>答案质量与成本</span>
            <strong className={`status-pill ${productionReadiness?.final_answer_quality_ready ? "is-good" : "is-warning"}`}>
              {productionReadiness?.final_answer_quality_ready ? "已达线" : "待补证据"}
            </strong>
          </div>
          <p>{governance?.answer_quality.note ?? "需要最终回复样本、人工事实性标签、引用充分性和转人工正确性一起验收。"}</p>
          <div className="rag-governance-metrics">
            <span>答案采样：{governance ? formatPercent(governance.answer_quality.final_answer_sample_coverage) : "-"}</span>
            <span>事实正确：{governance?.answer_quality.final_answer_factuality_rate !== null && governance ? formatPercent(governance.answer_quality.final_answer_factuality_rate) : "-"}</span>
            <span>成本记录：{productionReadiness?.model_cost_record_ready ? "已记录" : "待补"}</span>
            <span>预算策略：{productionReadiness?.budget_policy_ready ? "已配置" : "待配置"}</span>
          </div>
        </article>
        <article className="rag-governance-card" data-llm-ops-readiness="nc6">
          <div className="rag-governance-card-head">
            <span>模型观测与红队</span>
            <strong className={`status-pill ${llmOps ? llmOpsTone : "is-warning"}`}>
              {llmOps ? llmOpsStatusLabel[llmOps.status] : llmOpsReadiness.status === "loading" ? "读取中" : "未读取"}
            </strong>
          </div>
          <p>{llmOps?.summary ?? llmOpsReadiness.message ?? "等待读取模型成本、链路追踪和安全题库状态。"}</p>
          <div className="rag-governance-metrics">
            <span>
              调用记录：
              {llmOps ? `${llmOps.cost_ledger.model_call_count} 次` : "-"}
            </span>
            <span>
              估算成本：
              {llmOps ? `${llmOps.cost_ledger.estimated_cost} ${llmOps.cost_ledger.currency}` : "-"}
            </span>
            <span>链路证据：{llmOps?.trace_coverage.trace_ready ? "已贯穿" : "待补齐"}</span>
            <span>安全题集：{llmOps ? `${llmOps.redteam_readiness.redteam_case_count} 题` : "-"}</span>
            <span>人工标签：{llmOps ? `${llmOps.redteam_readiness.redteam_labeled_cases} 题` : "-"}</span>
            <span>题集来源：{llmOps ? (llmOps.redteam_readiness.internal_sample_only ? "内部样本" : "客户资料") : "-"}</span>
            <span>
              类目覆盖：
              {llmOps ? (llmOps.redteam_readiness.category_coverage_ready ? "已覆盖" : `待补 ${llmOps.redteam_readiness.missing_categories.length} 类`) : "-"}
            </span>
            <span>原文落库：{llmOps?.cost_ledger.raw_text_logged_count ? "需处理" : "未发现"}</span>
          </div>
        </article>
      </div>
      {governance ? (
        <div className="rag-gate-list" aria-label="检索与成本门禁">
          {governance.gates.map((gate) => (
            <article key={gate.code} className={`rag-gate-card is-${gate.status}`}>
              <span>{gate.label}</span>
              <strong>{gateStatusLabel[gate.status]}</strong>
              <p>{gate.reason}</p>
            </article>
          ))}
        </div>
      ) : null}
      {llmOps ? (
        <div className="rag-gate-list" aria-label="模型观测与安全门禁">
          {llmOps.gates.map((gate) => (
            <article key={gate.code} className={`rag-gate-card is-${gate.status}`}>
              <span>{gate.label}</span>
              <strong>{gateStatusLabel[gate.status]}</strong>
              <p>{gate.reason}</p>
            </article>
          ))}
        </div>
      ) : null}
      <div className="route-map-grid">
        {routes.map((route) => (
          <article key={route.name} className="route-card">
            <span>{route.name}</span>
            <strong>{route.model}</strong>
            <p>{route.policy}</p>
          </article>
        ))}
      </div>
      {governance?.recommended_next_steps.length ? (
        <div className="inline-notice">
          下一步：{governance.recommended_next_steps.slice(0, 2).join("；")}
        </div>
      ) : null}
      <p className="inline-notice">自动回复策略页展示的是当前决策边界，不代表已经完成模型成本报表、本地模型推理或全渠道自动回复。</p>
    </section>
  );
}

function LiveColleagueProfilePanel({ colleague }: { colleague: WorkbenchColleague }) {
  const profile = normalizePublicProfile(colleague.publicProfile);
  const displayName = profile.display_name || colleague.name;
  const fields = [
    { label: "对外昵称", value: profile.display_name },
    { label: "座机", value: profile.phone },
    { label: "手机", value: profile.mobile },
    { label: "邮箱", value: colleague.email },
    { label: "QQ", value: profile.qq },
    { label: "微信", value: profile.wechat }
  ];
  return (
    <section className="live-colleague-profile-panel" aria-label="同事资料">
      <div className="live-colleague-profile-card">
        <header>
          <div>
            <h2>{displayName}</h2>
            <span>{colleague.role} · {formatColleagueStatus(colleague.status)} · {colleague.activeChats} 个会话</span>
          </div>
          <div className="live-colleague-profile-avatar" aria-hidden="true">
            {colleague.avatarDataUrl ? <img src={colleague.avatarDataUrl} alt="" /> : <Users size={34} />}
          </div>
        </header>
        <dl>
          {fields.map((field) => (
            <div key={field.label}>
              <dt>{field.label}:</dt>
              <dd>{field.value?.trim() || "-"}</dd>
            </div>
          ))}
        </dl>
      </div>
    </section>
  );
}

function ConversationInboxPanel({
  state,
  listView,
  filters,
  hasToken,
  currentUserId,
  canManageConversations,
  onListViewChange,
  onFiltersChange,
  onRefresh,
  onWorkflowAction
}: {
  state: ConversationInboxState;
  listView: ListViewState;
  filters: ConversationInboxFilters;
  hasToken: boolean;
  currentUserId: number | null;
  canManageConversations: boolean;
  onListViewChange: (view: ListViewState) => void;
  onFiltersChange: (filters: ConversationInboxFilters) => void;
  onRefresh: () => void;
  onWorkflowAction: (item: ConversationInboxItem, action: ConversationWorkflowActionName) => void;
}) {
  const isLoading = state.status === "loading";
  const message =
    state.status === "idle" ? state.message : state.status === "error" ? state.message : "";
  const serverPaged = hasToken;
  const localPaged = useMemo(
    () =>
      getPagedItems(state.data.items, listView, {
        statusMatcher: (item, status) => item.status === status || item.sla_status === status,
        searchText: (item) => [
          item.subject,
          item.contact_display_name,
          item.channel_name,
          item.channel_type,
          item.status,
          item.priority,
          item.sla_status,
          item.last_message_preview,
          item.next_action
        ]
      }),
    [state.data.items, listView]
  );
  const result = serverPaged
    ? pagedResultFromServer(state.data)
    : localPaged;
  const breachedCount = state.data.items.filter((item) => item.sla_status === "breached").length;
  const waitingCount = state.data.items.filter((item) => item.last_message_direction === "inbound").length;

  return (
    <section className="panel conversation-inbox-panel" id="workspace-conversations" aria-label="会话收件箱">
      <div className="panel-heading">
        <div>
          <h2>会话收件箱</h2>
          <p>按客户等待、SLA、渠道、接管状态和下一步动作统一排队。</p>
        </div>
        <div className="panel-actions">
          <button type="button" className="ghost-action" onClick={onRefresh} disabled={!hasToken || isLoading}>
            <RefreshCw size={17} />
            {isLoading ? "刷新中" : "刷新"}
          </button>
        </div>
      </div>

      {message ? <p className="inline-notice">{message}</p> : null}

      <div className="conversation-inbox-summary">
        <OpsMetric label="当前会话" value={state.data.total} note={hasToken ? "服务端分页后的总量" : "本地初始化会话总量"} />
        <OpsMetric label="客户等待" value={waitingCount} note={hasToken ? "当前页最近一条为客户入站" : "本地初始化数据最近一条为客户入站"} />
        <OpsMetric label="SLA 超时" value={breachedCount} note="当前页或本地初始化数据中的超时项" />
        <OpsMetric
          label="待审核"
          value={state.data.items.reduce((total, item) => total + item.human_review_open_count, 0)}
          note={hasToken ? "当前页关联 open 人审任务" : "本地初始化数据关联 open 人审任务"}
        />
      </div>

      <ListToolbar
        view={listView}
        total={state.data.total}
        filteredTotal={result.total}
        statusOptions={[
          { label: "全部状态", value: "all" },
          { label: "机器人接待", value: "bot" },
          { label: "人工接管", value: "handoff" },
          { label: "等待人工", value: "waiting_human" },
          { label: "进行中", value: "open" }
        ]}
        searchPlaceholder="搜索客户、会话主题、最后消息、下一步动作"
        onChange={onListViewChange}
      />

      <div className="conversation-filter-grid">
        <label className="list-filter">
          接管
          <select
            value={filters.assigned}
            onChange={(event) => onFiltersChange({ ...filters, assigned: event.target.value })}
            disabled={!hasToken}
          >
            <option value="all">全部</option>
            <option value="mine">我的</option>
            <option value="assigned">已分配</option>
            <option value="unassigned">未分配</option>
          </select>
        </label>
        <label className="list-filter">
          SLA
          <select
            value={filters.sla}
            onChange={(event) => onFiltersChange({ ...filters, sla: event.target.value })}
            disabled={!hasToken}
          >
            <option value="all">全部</option>
            <option value="breached">超时</option>
            <option value="warning">临近</option>
            <option value="ok">正常</option>
            <option value="idle">无等待</option>
          </select>
        </label>
        <label className="list-filter">
          优先级
          <select
            value={filters.priority}
            onChange={(event) => onFiltersChange({ ...filters, priority: event.target.value })}
            disabled={!hasToken}
          >
            <option value="all">全部</option>
            <option value="critical">严重</option>
            <option value="high">高</option>
            <option value="medium">中</option>
            <option value="normal">普通</option>
            <option value="low">低</option>
          </select>
        </label>
        <label className="list-filter">
          排序
          <select
            value={filters.sort}
            onChange={(event) => onFiltersChange({ ...filters, sort: event.target.value })}
            disabled={!hasToken}
          >
            <option value="waiting_desc">等待优先</option>
            <option value="last_message_desc">最新消息</option>
            <option value="priority_desc">风险优先</option>
          </select>
        </label>
      </div>

      {result.items.length === 0 && state.status === "ready" ? (
        <p className="inline-notice">当前筛选下没有会话。</p>
      ) : null}

      <div className="conversation-inbox-list">
        {result.items.map((item) => (
          <article key={item.id} className={`conversation-inbox-row sla-${item.sla_status}`}>
            <div className="conversation-inbox-copy">
              <div className="conversation-inbox-head">
                <div>
                  <strong>{item.contact_display_name || `联系人 #${item.contact_id}`}</strong>
                  <span>{item.subject || `会话 #${item.id}`}</span>
                </div>
                <small>{item.channel_name || item.channel_type || `渠道 #${item.channel_id}`}</small>
              </div>
              <p>{item.last_message_preview || "暂无消息内容"}</p>
              <div className="attempt-line">
                <span className={`sla-pill sla-${item.sla_status}`}>{formatSlaLabel(item.sla_status)}</span>
                <span>等待 {formatWaitingMinutes(item.waiting_minutes)}</span>
                <span>{formatPriorityLabel(item.priority)}</span>
                <span>待审 {item.human_review_open_count}</span>
                <span>待发 {item.outbox_pending_count}</span>
                {item.delivery_failure_open_count > 0 ? <span className="retry-pill">失败 {item.delivery_failure_open_count}</span> : null}
              </div>
              <div className="conversation-next-action">
                <Route size={16} />
                <span>{item.next_action}</span>
              </div>
            </div>
            <div className="conversation-inbox-actions">
              <span>{item.assigned_user_id ? `坐席 #${item.assigned_user_id}` : "未分配"}</span>
              <div className="conversation-action-grid">
                <button
                  type="button"
                  className="primary-action"
                  onClick={() => onWorkflowAction(item, item.status === "resolved" ? "reopen" : "claim")}
                  disabled={!canManageConversations || !canClaimConversation(item, currentUserId, hasToken, isLoading)}
                >
                  <MessageSquare size={17} />
                  {item.status === "resolved" ? "重开" : "领取"}
                </button>
                <button
                  type="button"
                  className="ghost-action"
                  onClick={() => onWorkflowAction(item, "wait_customer")}
                  disabled={!canManageConversations || !canWorkConversation(item, hasToken, isLoading)}
                >
                  <Route size={16} />
                  等客户
                </button>
                <button
                  type="button"
                  className="ghost-action"
                  onClick={() => onWorkflowAction(item, "resolve")}
                  disabled={!canManageConversations || !canWorkConversation(item, hasToken, isLoading)}
                >
                  <CheckCircle2 size={16} />
                  解决
                </button>
                <button
                  type="button"
                  className="ghost-action"
                  onClick={() => onWorkflowAction(item, "release")}
                  disabled={!canManageConversations || !canReleaseConversation(item, hasToken, isLoading)}
                >
                  <LogOut size={16} />
                  释放
                </button>
              </div>
              <a className="ghost-link" href="#live?queue=needs_review">查看转人工会话</a>
            </div>
          </article>
        ))}
      </div>
      <PaginationControls result={result} view={listView} onChange={onListViewChange} />
    </section>
  );
}

function SupportTicketPanel({
  state,
  conversationState,
  listView,
  filters,
  hasToken,
  currentUserId,
  canManageTickets,
  onListViewChange,
  onFiltersChange,
  onRefresh,
  onCreateFromConversation,
  onUpdateStatus
}: {
  state: SupportTicketState;
  conversationState: ConversationInboxState;
  listView: ListViewState;
  filters: SupportTicketFilters;
  hasToken: boolean;
  currentUserId: number | null;
  canManageTickets: boolean;
  onListViewChange: (view: ListViewState) => void;
  onFiltersChange: (filters: SupportTicketFilters) => void;
  onRefresh: () => void;
  onCreateFromConversation: (item: ConversationInboxItem) => void;
  onUpdateStatus: (ticket: SupportTicket, statusValue: "in_progress" | "pending_customer" | "resolved") => void;
}) {
  const [selectedTicketId, setSelectedTicketId] = useState<number | null>(null);
  const isLoading = state.status === "loading";
  const message = "message" in state ? state.message ?? "" : "";
  const serverPaged = hasToken;
  const localPaged = useMemo(
    () =>
      getPagedItems(state.data.items, listView, {
        statusMatcher: (ticket, statusValue) => ticket.status === statusValue || ticket.sla_status === statusValue,
        searchText: (ticket) => [
          ticket.subject,
          ticket.description,
          ticket.contact_display_name,
          ticket.channel_name,
          ticket.priority,
          ticket.status,
          ticket.sla_status,
          ticket.source_ref,
          ticket.resolution_note
        ]
      }),
    [state.data.items, listView]
  );
  const result = serverPaged ? pagedResultFromServer(state.data) : localPaged;
  const selectedTicket =
    result.items.find((ticket) => ticket.id === selectedTicketId) ??
    result.items.find((ticket) => ticket.sla_status === "breached") ??
    result.items.find((ticket) => ticket.status !== "resolved") ??
    result.items[0] ??
    null;

  useEffect(() => {
    if (selectedTicket && selectedTicket.id !== selectedTicketId) {
      setSelectedTicketId(selectedTicket.id);
    }
    if (!selectedTicket && selectedTicketId !== null) {
      setSelectedTicketId(null);
    }
  }, [selectedTicket?.id, selectedTicketId]);

  const currentPageTickets = state.data.items;
  const activeTickets = currentPageTickets.filter((ticket) => ["open", "in_progress", "pending_customer"].includes(ticket.status));
  const warningTickets = currentPageTickets.filter((ticket) => ticket.sla_status === "warning").length;
  const breachedTickets = currentPageTickets.filter((ticket) => ticket.sla_status === "breached").length;
  const completedTickets = currentPageTickets.filter((ticket) => ["resolved", "closed", "canceled"].includes(ticket.status)).length;
  const ticketConversationIds = new Set(state.data.items.map((ticket) => ticket.conversation_id));
  const candidateConversations = conversationState.data.items
    .filter((item) => !ticketConversationIds.has(item.id))
    .filter((item) => item.status !== "resolved")
    .slice(0, 6);

  return (
    <section className="panel support-ticket-panel" id="workspace-support-tickets" aria-label="工单/SLA">
      <div className="panel-heading">
        <div>
          <h2>工单/SLA</h2>
          <p>从需要持续跟进的会话生成工单，跟踪负责人、状态、SLA 到期和解决结果。</p>
        </div>
        <div className="panel-actions">
          <button type="button" className="ghost-action" onClick={onRefresh} disabled={!hasToken || isLoading}>
            <RefreshCw size={17} />
            {isLoading ? "刷新中" : "刷新"}
          </button>
        </div>
      </div>

      {message ? <p className="inline-notice">{message}</p> : null}

      <div className="ticket-metric-grid">
        <OpsMetric label="当前工单" value={state.data.total} note={hasToken ? "服务端筛选后的总量" : "样例工单总量"} />
        <OpsMetric label="处理中" value={activeTickets.length} note="当前页开放、处理中、等客户" />
        <OpsMetric label="临近/超时" value={warningTickets + breachedTickets} note={`临近 ${warningTickets} · 超时 ${breachedTickets}`} />
        <OpsMetric label="已完成" value={completedTickets} note="当前页已解决、关闭或取消" />
      </div>

      <div className="ticket-workbench-layout">
        <div className="ticket-list-column">
          <div className="workbench-column-title">
            <div>
              <strong>工单队列</strong>
              <span>分页列表，按状态、SLA、负责人和优先级处理</span>
            </div>
            <small>{result.total} 条</small>
          </div>

          <ListToolbar
            view={listView}
            total={state.data.total}
            filteredTotal={result.total}
            statusOptions={[
              { label: "全部状态", value: "all" },
              { label: "待处理", value: "open" },
              { label: "处理中", value: "in_progress" },
              { label: "等客户", value: "pending_customer" },
              { label: "已解决", value: "resolved" }
            ]}
            searchPlaceholder="搜索工单主题、客户、渠道、备注"
            onChange={onListViewChange}
          />

          <div className="ticket-filter-grid">
            <label className="list-filter">
              负责人
              <select
                value={filters.assigned}
                onChange={(event) => onFiltersChange({ ...filters, assigned: event.target.value })}
                disabled={!hasToken}
              >
                <option value="all">全部</option>
                <option value="mine">我的</option>
                <option value="assigned">已分配</option>
                <option value="unassigned">未分配</option>
              </select>
            </label>
            <label className="list-filter">
              SLA
              <select
                value={filters.sla}
                onChange={(event) => onFiltersChange({ ...filters, sla: event.target.value })}
                disabled={!hasToken}
              >
                <option value="all">全部</option>
                <option value="breached">超时</option>
                <option value="warning">临近</option>
                <option value="ok">正常</option>
                <option value="paused">暂停</option>
                <option value="completed">完成</option>
              </select>
            </label>
            <label className="list-filter">
              优先级
              <select
                value={filters.priority}
                onChange={(event) => onFiltersChange({ ...filters, priority: event.target.value })}
                disabled={!hasToken}
              >
                <option value="all">全部</option>
                <option value="urgent">紧急</option>
                <option value="high">高</option>
                <option value="normal">普通</option>
                <option value="low">低</option>
              </select>
            </label>
          </div>

          {result.items.length === 0 && state.status === "ready" ? (
            <p className="inline-notice">当前筛选条件下没有工单。</p>
          ) : null}

          <div className="ticket-list">
            {result.items.map((ticket) => (
              <button
                key={ticket.id}
                type="button"
                className={`ticket-list-item sla-${ticket.sla_status} ${selectedTicket?.id === ticket.id ? "active" : ""}`}
                onClick={() => setSelectedTicketId(ticket.id)}
              >
                <span className={`sla-pill sla-${ticket.sla_status}`}>{formatSlaLabel(ticket.sla_status)}</span>
                <strong>{ticket.subject || `工单 #${ticket.id}`}</strong>
                <small>{ticket.contact_display_name || `联系人 #${ticket.contact_id}`} · {ticket.channel_name || ticket.channel_type}</small>
                <p>{ticket.description || "没有工单描述"}</p>
                <div className="attempt-line">
                  <span>{formatTicketStatus(ticket.status)}</span>
                  <span>{formatPriorityLabel(ticket.priority)}</span>
                  <span>{formatSlaTarget(ticket.sla_target_minutes)}</span>
                  <span>{ticket.assigned_user_id ? `负责人 #${ticket.assigned_user_id}` : "未分配"}</span>
                </div>
              </button>
            ))}
          </div>
          <PaginationControls result={result} view={listView} onChange={onListViewChange} />
        </div>

        <aside className="ticket-detail-panel">
          {selectedTicket ? (
            <>
              <div className="workbench-column-title">
                <div>
                  <strong>{selectedTicket.subject || `工单 #${selectedTicket.id}`}</strong>
                  <span>来源会话 #{selectedTicket.conversation_id} · {selectedTicket.source_ref}</span>
                </div>
                <span className={`sla-pill sla-${selectedTicket.sla_status}`}>{formatSlaLabel(selectedTicket.sla_status)}</span>
              </div>
              <div className="ticket-detail-grid">
                <div>
                  <span>客户</span>
                  <strong>{selectedTicket.contact_display_name || `联系人 #${selectedTicket.contact_id}`}</strong>
                </div>
                <div>
                  <span>渠道</span>
                  <strong>{selectedTicket.channel_name || selectedTicket.channel_type || `渠道 #${selectedTicket.channel_id}`}</strong>
                </div>
                <div>
                  <span>负责人</span>
                  <strong>{selectedTicket.assigned_user_id ? `坐席 #${selectedTicket.assigned_user_id}` : "未分配"}</strong>
                </div>
                <div>
                  <span>优先级</span>
                  <strong>{formatPriorityLabel(selectedTicket.priority)}</strong>
                </div>
                <div>
                  <span>SLA 目标</span>
                  <strong>{formatSlaTarget(selectedTicket.sla_target_minutes)}</strong>
                </div>
                <div>
                  <span>到期时间</span>
                  <strong>{formatDateTime(selectedTicket.sla_due_at)}</strong>
                </div>
              </div>
              <div className="ticket-description">
                <span>处理说明</span>
                <p>{selectedTicket.description || "没有处理说明"}</p>
              </div>
              {selectedTicket.resolution_note ? (
                <div className="ticket-description">
                  <span>最近备注</span>
                  <p>{selectedTicket.resolution_note}</p>
                </div>
              ) : null}
              <div className="ticket-action-bar">
                <button
                  type="button"
                  className="ghost-action"
                  disabled={!canManageTickets || !canUpdateTicket(selectedTicket, hasToken, isLoading)}
                  onClick={() => onUpdateStatus(selectedTicket, "in_progress")}
                >
                  <Route size={16} />
                  处理中
                </button>
                <button
                  type="button"
                  className="ghost-action"
                  disabled={!canManageTickets || !canUpdateTicket(selectedTicket, hasToken, isLoading)}
                  onClick={() => onUpdateStatus(selectedTicket, "pending_customer")}
                >
                  <MessageSquare size={16} />
                  等客户
                </button>
                <button
                  type="button"
                  className="primary-action"
                  disabled={!canManageTickets || !canUpdateTicket(selectedTicket, hasToken, isLoading)}
                  onClick={() => onUpdateStatus(selectedTicket, "resolved")}
                >
                  <CheckCircle2 size={17} />
                  解决工单
                </button>
              </div>
              <div className="ticket-audit-note">
                <FileText size={16} />
                <span>
                  创建 {formatDateTime(selectedTicket.created_at)} · 更新 {formatDateTime(selectedTicket.updated_at)}
                  {currentUserId ? ` · 当前坐席 #${currentUserId}` : ""}
                </span>
              </div>
            </>
          ) : (
            <div className="empty-detail">
              <FileText size={22} />
              <strong>没有可查看的工单</strong>
              <span>从下方会话候选中生成第一张工单，或调整筛选条件。</span>
            </div>
          )}

          <div className="ticket-candidate-box">
            <div className="workbench-column-title">
              <div>
                <strong>可生成工单的会话</strong>
                <span>只展示当前已加载会话，真实生产应由会话详情页触发</span>
              </div>
            </div>
            {candidateConversations.length === 0 ? (
              <p className="inline-notice">当前页没有新的会话候选。</p>
            ) : (
              candidateConversations.map((item) => (
                <div key={item.id} className="ticket-candidate-row">
                  <div>
                    <strong>{item.contact_display_name || `联系人 #${item.contact_id}`}</strong>
                    <span>{item.subject || item.last_message_preview || `会话 #${item.id}`}</span>
                  </div>
                  <button
                    type="button"
                    className="ghost-action"
                    disabled={!hasToken || !canManageTickets || isLoading}
                    onClick={() => onCreateFromConversation(item)}
                  >
                    生成工单
                  </button>
                </div>
              ))
            )}
          </div>
        </aside>
      </div>
    </section>
  );
}

function ContactProfilesPanel({
  state,
  listView,
  hasToken,
  onListViewChange,
  onRefresh,
  onSelect
}: {
  state: ContactProfileState;
  listView: ListViewState;
  hasToken: boolean;
  onListViewChange: (view: ListViewState) => void;
  onRefresh: () => void;
  onSelect: (contactId: number) => void;
}) {
  const isLoading = state.status === "loading";
  const message = "message" in state ? state.message ?? "" : "";
  const localPaged = useMemo(
    () =>
      getPagedItems(state.data.items, listView, {
        searchText: (profile) => [
          profile.display_name,
          profile.phone,
          profile.wechat,
          profile.latest_channel_name,
          profile.latest_channel_type,
          profile.highest_intent_level,
          profile.last_message_preview,
          profile.next_action
        ]
      }),
    [state.data.items, listView]
  );
  const result = hasToken ? pagedResultFromServer(state.data) : localPaged;
  const detail =
    state.detail ??
    buildContactProfileDetailFromLocal(result.items[0] ?? state.data.items[0] ?? null, [], [], []);
  const activeProfiles = state.data.items.filter(
    (profile) => profile.open_conversation_count > 0 || profile.active_lead_count > 0 || profile.open_support_ticket_count > 0
  );
  const hotProfiles = state.data.items.filter((profile) => profile.highest_intent_level === "hot");
  const openTickets = state.data.items.reduce((sum, profile) => sum + profile.open_support_ticket_count, 0);

  return (
    <section className="panel contact-profile-panel" id="workspace-contacts" aria-label="客户资料与商机记录">
      <div className="panel-heading">
        <div>
          <h2>客户资料与会话记录</h2>
          <p>轻量沉淀客户基础资料、最近会话、标签和备注，帮助坐席接手时快速理解上下文。</p>
        </div>
        <div className="panel-actions">
          <button type="button" className="ghost-action" onClick={onRefresh} disabled={!hasToken || isLoading}>
            <RefreshCw size={17} />
            {isLoading ? "刷新中" : "刷新"}
          </button>
        </div>
      </div>

      {message ? <p className="inline-notice">{message}</p> : null}

      <div className="ticket-metric-grid">
        <OpsMetric label="客户资料" value={state.data.total} note={hasToken ? "服务端客户资料总量" : "本地样例资料"} />
        <OpsMetric label="近期互动" value={activeProfiles.length} note="有开放会话或待跟进记录" />
        <OpsMetric label="高关注" value={hotProfiles.length} note="近期意向较高的客户" />
        <OpsMetric label="待处理记录" value={openTickets} note="当前已加载的待处理事项" />
      </div>

      <div className="contact-profile-layout">
        <div className="profile-list-column">
              <div className="workbench-column-title">
                <div>
                  <strong>客户列表</strong>
                  <span>按姓名、联系方式、渠道和最近问题检索</span>
                </div>
            <small>{result.total} 条</small>
          </div>

          <ListToolbar
            view={listView}
            total={state.data.total}
            filteredTotal={result.total}
            statusOptions={[{ label: "全部联系人", value: "all" }]}
            searchPlaceholder="搜索联系人、渠道、最近问题、下一步动作"
            onChange={onListViewChange}
          />

          {result.items.length === 0 && state.status === "ready" ? (
            <p className="inline-notice">当前筛选条件下没有联系人。</p>
          ) : null}

          <div className="profile-list">
            {result.items.map((profile) => (
              <button
                key={profile.id}
                type="button"
                className={`profile-list-item ${detail?.id === profile.id ? "active" : ""}`}
                onClick={() => onSelect(profile.id)}
              >
                <span className={`intent-pill intent-${profile.highest_intent_level || "cold"}`}>
                  {formatLeadIntent(profile.highest_intent_level)}
                </span>
                <strong>{profile.display_name || `联系人 #${profile.id}`}</strong>
                <small>{profile.latest_channel_name || profile.latest_channel_type || "暂无渠道"} · {formatDateTime(profile.last_message_at)}</small>
                <p>{profile.last_message_preview || "暂无最近消息"}</p>
                <div className="attempt-line">
                  <span>会话 {profile.conversation_count}</span>
                  <span>待处理 {profile.open_support_ticket_count + profile.active_lead_count}</span>
                </div>
              </button>
            ))}
          </div>
          <PaginationControls result={result} view={listView} onChange={onListViewChange} />
        </div>

        <aside className="profile-detail-panel">
          {detail ? (
            <>
              <div className="workbench-column-title">
                <div>
                  <strong>{detail.display_name || `联系人 #${detail.id}`}</strong>
                  <span>{detail.latest_channel_name || detail.latest_channel_type || "暂无最近渠道"}</span>
                </div>
                <span className={`intent-pill intent-${detail.highest_intent_level || "cold"}`}>
                  {formatLeadIntent(detail.highest_intent_level)}
                </span>
              </div>

              <div className="ticket-detail-grid">
                <div>
                  <span>手机号</span>
                  <strong>{detail.phone || "未记录"}</strong>
                </div>
                <div>
                  <span>微信</span>
                  <strong>{detail.wechat || "未记录"}</strong>
                </div>
                <div>
                  <span>会话</span>
                  <strong>{detail.open_conversation_count}</strong>
                </div>
                <div>
                  <span>待跟进</span>
                  <strong>{detail.active_lead_count}</strong>
                </div>
              </div>

              <div className="ticket-description">
                <span>备注 / 下一步</span>
                <p>{detail.next_action || "保持观察，等待新的客户入站或坐席跟进。"}</p>
              </div>

              <ProfileTimeline
                title="最近会话"
                emptyText="暂无最近会话"
                items={detail.recent_conversations.map((item) => ({
                  id: item.id,
                  title: item.subject || `会话 #${item.id}`,
                  subtitle: `${item.channel_name || item.channel_type} · ${formatTicketStatus(item.status)}`,
                  body: item.last_message_preview || "没有最近消息",
                  meta: `${formatPriorityLabel(item.priority)} · ${formatDateTime(item.last_message_at)}`
                }))}
              />

              <div className="profile-tag-note">
                <span>标签</span>
                <div>
                  <strong>{formatLeadIntent(detail.highest_intent_level)}</strong>
                  <strong>{detail.latest_channel_name || detail.latest_channel_type || "暂无渠道"}</strong>
                  {detail.active_lead_count > 0 ? <strong>需跟进</strong> : null}
                </div>
                <small>这里先作为轻量客户资料，不替代完整 CRM。</small>
              </div>
            </>
          ) : (
            <div className="empty-detail">
              <MessageSquare size={22} />
              <strong>没有可查看的联系人</strong>
              <span>当渠道产生可信入站后，联系人会自动形成画像。</span>
            </div>
          )}
        </aside>
      </div>
    </section>
  );
}

function ProfileTimeline({
  title,
  emptyText,
  items
}: {
  title: string;
  emptyText: string;
  items: Array<{ id: number; title: string; subtitle: string; body: string; meta: string }>;
}) {
  return (
    <div className="profile-timeline">
      <div className="workbench-column-title">
        <div>
          <strong>{title}</strong>
          <span>{items.length} 条</span>
        </div>
      </div>
      {items.length === 0 ? (
        <p className="inline-notice">{emptyText}</p>
      ) : (
        items.map((item) => (
          <article key={`${title}-${item.id}`} className="profile-timeline-item">
            <div>
              <strong>{item.title}</strong>
              <span>{item.subtitle}</span>
            </div>
            <p>{item.body}</p>
            <small>{item.meta}</small>
          </article>
        ))
      )}
    </div>
  );
}

function SalesLeadPanel({
  state,
  conversationState,
  listView,
  filters,
  hasToken,
  currentUserId,
  canManageLeads,
  onListViewChange,
  onFiltersChange,
  onRefresh,
  onCreateFromConversation,
  onUpdateStage
}: {
  state: SalesLeadState;
  conversationState: ConversationInboxState;
  listView: ListViewState;
  filters: SalesLeadFilters;
  hasToken: boolean;
  currentUserId: number | null;
  canManageLeads: boolean;
  onListViewChange: (view: ListViewState) => void;
  onFiltersChange: (filters: SalesLeadFilters) => void;
  onRefresh: () => void;
  onCreateFromConversation: (item: ConversationInboxItem) => void;
  onUpdateStage: (lead: SalesLead, stage: "contacted" | "proposal" | "won" | "invalid" | "lost") => void;
}) {
  const isLoading = state.status === "loading";
  const message = "message" in state ? state.message ?? "" : "";
  const serverPaged = hasToken;
  const localPaged = useMemo(
    () =>
      getPagedItems(state.data.items, listView, {
        statusMatcher: (lead, statusValue) => lead.stage === statusValue || lead.intent_level === statusValue,
        searchText: (lead) => [
          lead.title,
          lead.summary,
          lead.contact_display_name,
          lead.channel_name,
          lead.stage,
          lead.intent_level,
          lead.expected_budget,
          lead.next_step,
          lead.latest_message_preview
        ]
      }),
    [state.data.items, listView]
  );
  const result = serverPaged ? pagedResultFromServer(state.data) : localPaged;
  const existingConversationIds = new Set(state.data.items.map((lead) => lead.conversation_id).filter(Boolean));
  const candidateConversations = conversationState.data.items
    .filter((item) => !existingConversationIds.has(item.id))
    .filter((item) => item.status !== "resolved")
    .filter((item) =>
      ["报价", "试点", "部署", "价格", "合同", "采购", "预算", "方案"].some((keyword) =>
        `${item.subject} ${item.last_message_preview}`.includes(keyword)
      ) || ["critical", "high"].includes(item.priority)
    )
    .slice(0, 6);
  const activeLeads = state.data.items.filter((lead) => ["new", "contacted", "proposal"].includes(lead.stage));
  const hotLeads = state.data.items.filter((lead) => lead.intent_level === "hot");
  const wonLeads = state.data.items.filter((lead) => lead.stage === "won");
  const leadActionTitle = (lead: SalesLead, targetStage: "contacted" | "proposal" | "won" | "invalid", label: string) => {
    if (!hasToken) return `${label}不可用：请先登录本地账号后读取真实线索。`;
    if (!canManageLeads) return `${label}不可用：当前账号没有线索管理权限。`;
    if (isLoading) return `${label}不可用：正在同步线索数据。`;
    if (lead.stage === targetStage) return `${label}不可用：当前线索已经是该阶段。`;
    if (["won", "invalid", "lost"].includes(lead.stage)) return `${label}不可用：已结束线索需要重新打开后再调整。`;
    return `将线索标记为${label}。`;
  };

  return (
    <section className="panel sales-lead-panel" id="workspace-leads" aria-label="商机记录与下一步">
      <div className="panel-heading">
        <div>
          <h2>商机记录与下一步</h2>
          <p>只记录客服会话里出现的购买、报价、部署和合作意向，方便安排下一步联系。</p>
        </div>
        <div className="panel-actions">
          <button type="button" className="ghost-action" onClick={onRefresh} disabled={!hasToken || isLoading}>
            <RefreshCw size={17} />
            {isLoading ? "刷新中" : "刷新"}
          </button>
        </div>
      </div>

      {message ? <p className="inline-notice">{message}</p> : null}

      <div className="ticket-metric-grid">
        <OpsMetric label="商机记录" value={state.data.total} note={hasToken ? "服务端筛选后的总量" : "本地样例记录"} />
        <OpsMetric label="跟进中" value={activeLeads.length} note="新线索、已联系、待报价" />
        <OpsMetric label="高意向" value={hotLeads.length} note="需要优先联系和复核报价" />
        <OpsMetric label="已成交" value={wonLeads.length} note="当前已加载数据中的成交数" />
      </div>

      <div className="lead-workbench-layout">
        <div className="lead-list-column">
          <div className="workbench-column-title">
            <div>
              <strong>线索池</strong>
              <span>按阶段、意向和关键词筛选</span>
            </div>
            <small>{result.total} 条</small>
          </div>

          <ListToolbar
            view={listView}
            total={state.data.total}
            filteredTotal={result.total}
            statusOptions={[
              { label: "全部阶段", value: "all" },
              { label: "新线索", value: "new" },
              { label: "已联系", value: "contacted" },
              { label: "待报价", value: "proposal" },
              { label: "已成交", value: "won" },
              { label: "无效", value: "invalid" },
              { label: "流失", value: "lost" }
            ]}
            searchPlaceholder="搜索客户、需求、下一步动作"
            onChange={onListViewChange}
          />

          <div className="ticket-filter-grid lightweight-filter-grid">
            <label className="list-filter">
              意向
              <select
                value={filters.intent}
                onChange={(event) => onFiltersChange({ ...filters, intent: event.target.value })}
                disabled={!hasToken}
              >
                <option value="all">全部</option>
                <option value="hot">高意向</option>
                <option value="warm">中意向</option>
                <option value="cold">低意向</option>
              </select>
            </label>
          </div>

          {result.items.length === 0 && state.status === "ready" ? (
            <p className="inline-notice">当前筛选条件下没有线索。</p>
          ) : null}

          <div className="lead-list">
            {result.items.map((lead) => (
              <article key={lead.id} className={`lead-list-item intent-${lead.intent_level || "cold"}`}>
                <div className="lead-row-head">
                  <div>
                    <span className={`intent-pill intent-${lead.intent_level || "cold"}`}>{formatLeadIntent(lead.intent_level)}</span>
                    <strong>{lead.title || `线索 #${lead.id}`}</strong>
                    <small>{lead.contact_display_name || `联系人 #${lead.contact_id}`} · {lead.channel_name || lead.channel_type}</small>
                  </div>
                  <span className="stage-pill">{formatLeadStage(lead.stage)}</span>
                </div>
                <p>{lead.summary || lead.latest_message_preview || "没有线索摘要"}</p>
                <div className="attempt-line">
                  <span>{lead.owner_user_id ? `负责人 #${lead.owner_user_id}` : "未分配"}</span>
                  <span>{formatDateTime(lead.updated_at)}</span>
                  {currentUserId ? <span>当前坐席 #{currentUserId}</span> : null}
                </div>
                <div className="lead-next-step">
                  <span>下一步</span>
                  <p>{lead.next_step || "确认需求、预算、决策人和上线时间。"}</p>
                </div>
                <div className="ticket-action-bar">
                  <button
                    type="button"
                    className="ghost-action"
                    disabled={!canManageLeads || !canUpdateLead(lead, hasToken, isLoading)}
                    title={leadActionTitle(lead, "contacted", "已联系")}
                    aria-label={leadActionTitle(lead, "contacted", "已联系")}
                    onClick={() => onUpdateStage(lead, "contacted")}
                  >
                    已联系
                  </button>
                  <button
                    type="button"
                    className="ghost-action"
                    disabled={!canManageLeads || !canUpdateLead(lead, hasToken, isLoading)}
                    title={leadActionTitle(lead, "proposal", "待报价")}
                    aria-label={leadActionTitle(lead, "proposal", "待报价")}
                    onClick={() => onUpdateStage(lead, "proposal")}
                  >
                    待报价
                  </button>
                  <button
                    type="button"
                    className="primary-action"
                    disabled={!canManageLeads || !canUpdateLead(lead, hasToken, isLoading)}
                    title={leadActionTitle(lead, "won", "成交")}
                    aria-label={leadActionTitle(lead, "won", "成交")}
                    onClick={() => onUpdateStage(lead, "won")}
                  >
                    成交
                  </button>
                  <button
                    type="button"
                    className="ghost-action"
                    disabled={!canManageLeads || !canUpdateLead(lead, hasToken, isLoading)}
                    title={leadActionTitle(lead, "invalid", "无效")}
                    aria-label={leadActionTitle(lead, "invalid", "无效")}
                    onClick={() => onUpdateStage(lead, "invalid")}
                  >
                    无效
                  </button>
                </div>
              </article>
            ))}
          </div>
          <PaginationControls result={result} view={listView} onChange={onListViewChange} />
        </div>

        <aside className="lead-candidate-panel">
          <div className="workbench-column-title">
            <div>
              <strong>可转线索的会话</strong>
              <span>从当前会话中提取报价、部署、采购等明确意向</span>
            </div>
          </div>
          {candidateConversations.length === 0 ? (
            <p className="inline-notice">当前页没有新的线索候选。</p>
          ) : (
            candidateConversations.map((item) => (
              <div key={item.id} className="ticket-candidate-row">
                <div>
                  <strong>{item.contact_display_name || `联系人 #${item.contact_id}`}</strong>
                  <span>{item.subject || item.last_message_preview || `会话 #${item.id}`}</span>
                </div>
                <button
                  type="button"
                  className="ghost-action"
                  disabled={!hasToken || !canManageLeads || isLoading}
                  onClick={() => onCreateFromConversation(item)}
                >
                  生成线索
                </button>
              </div>
            ))
          )}
          <div className="ticket-description">
            <span>真实边界</span>
            <p>本页只负责沉淀客服发现的商机，不替代企业已有销售系统。后续如需对接，应通过客户授权的数据同步完成。</p>
          </div>
        </aside>
      </div>
    </section>
  );
}

function CopilotSandboxPanel({
  reviewItems,
  outboxDrafts,
  deliveryJobs,
  workerRun,
  hasToken,
  canRunInboundWorker,
  onRunInboundWorker
}: {
  reviewItems: HumanReviewInboxItem[];
  outboxDrafts: OutboxDraft[];
  deliveryJobs: OutboxDeliveryJob[];
  workerRun: TrustedInboundWorkerRun | null;
  hasToken: boolean;
  canRunInboundWorker: boolean;
  onRunInboundWorker: () => void;
}) {
  const pendingDrafts = outboxDrafts.filter((draft) => draft.status === "pending_confirmation").length;
  const readyDrafts = outboxDrafts.filter((draft) => draft.status === "ready_to_send").length;
  const openReviews = reviewItems.filter((item) => item.status === "open").length;
  const sandboxSteps = [
    {
      label: "验签入站",
      value: "官网",
      note: "HMAC 验签，错签只入回执"
    },
    {
      label: "AI 建议",
      value: workerRun ? `${workerRun.processed}` : "待跑",
      note: "只生成草稿，进入人工审核"
    },
    {
      label: "人工审核",
      value: `${openReviews}`,
      note: "坐席批准后才生成待发送"
    },
    {
      label: "Outbox",
      value: `${pendingDrafts}/${readyDrafts}`,
      note: "待确认 / 已待发送"
    }
  ];

  return (
    <section className="panel sandbox-panel" id="workspace-sandbox" aria-label="官网 Copilot 沙盒">
      <div className="panel-heading">
        <div>
          <h2>官网 Copilot 沙盒</h2>
          <p>单渠道试点链路：可信入站、AI 草稿、人工审核、待发送草稿和外发门禁。</p>
        </div>
        <div className="panel-actions">
          <button
            type="button"
            className="primary-action"
            onClick={onRunInboundWorker}
            disabled={!hasToken || !canRunInboundWorker}
          >
            <Bot size={17} />
            运行入站编排
          </button>
        </div>
      </div>

      <div className="sandbox-layout">
        <div className="sandbox-step-grid">
          {sandboxSteps.map((step) => (
            <article key={step.label} className="sandbox-step">
              <span>{step.label}</span>
              <strong>{step.value}</strong>
              <small>{step.note}</small>
            </article>
          ))}
        </div>

        <article className="sandbox-guardrail">
          <div className="section-title-row">
            <ShieldCheck size={18} />
            <strong>外发门禁</strong>
          </div>
          <dl className="detail-list">
            <div>
              <dt>通道</dt>
              <dd>官网客服沙盒</dd>
            </div>
            <div>
              <dt>发送</dt>
              <dd>真实外发关闭，渠道计划只保留本地记录</dd>
            </div>
            <div>
              <dt>队列</dt>
              <dd>{deliveryJobs.length} 个任务，均不请求外部写入</dd>
            </div>
          </dl>
        </article>

        <article className="sandbox-run">
          <div className="section-title-row">
            <Route size={18} />
            <strong>最近编排</strong>
          </div>
          {workerRun ? (
            <p>
              扫描 {workerRun.scanned} 条，处理 {workerRun.processed} 条，成功 {workerRun.succeeded} 条，跳过{" "}
              {workerRun.skipped} 条，外部写入关闭。
            </p>
          ) : (
            <p>等待官网沙盒可信入站消息。</p>
          )}
        </article>
      </div>
    </section>
  );
}

function DemoModeBanner({ compact = false }: { compact?: boolean }) {
  return (
    <section className={`demo-banner${compact ? " compact" : ""}`} aria-label="本地数据说明">
      <div>
        <strong>本地工作台</strong>
        <span>页面展示的是本地初始化数据，用于检查中控台结构、分页和队列体验；不会读取客户真实消息，也不会向任何平台外发。</span>
      </div>
      <small>正式试点请使用租户账号登录后接入真实知识库与官方渠道。</small>
    </section>
  );
}

function WorkspaceTaskContextBanner({
  context,
  matchCount,
  onClear
}: {
  context: WorkspaceTaskContext;
  matchCount: number | null;
  onClear: () => void;
}) {
  const chips = [
    formatOpsRangeLabel(context.range),
    context.channelLabel,
    context.queue ? `队列：${formatWorkspaceTaskQueueLabel(context.queue)}` : null,
    context.status ? `状态：${formatWorkspaceTaskStatusLabel(context.status)}` : null
  ].filter(Boolean);
  const sourceLabel = context.source === "quality"
    ? "质量复盘"
    : context.source === "knowledge"
      ? "知识运营"
      : "运营总览";

  return (
    <aside className="task-context-banner" aria-label={`来自${sourceLabel}的处理上下文`}>
      <div>
        <span>来自{sourceLabel}</span>
        <strong>{context.title}</strong>
        <p>{context.description}</p>
        <div className="task-context-chips">
          {chips.map((chip) => (
            <em key={chip}>{chip}</em>
          ))}
        </div>
        {matchCount === 0 ? <small className="task-context-empty">{context.emptyText}</small> : null}
      </div>
      <div className="task-context-meta">
        <span>当前匹配</span>
        <strong>{matchCount ?? "-"}</strong>
        <button type="button" className="ghost-action" onClick={onClear}>
          清除筛选
        </button>
      </div>
    </aside>
  );
}

function WorkbenchCommandCenter({
  businessOpsDashboard,
  dashboardStatus,
  dashboardMessage,
  reviewItems,
  outboxDrafts,
  failureReviews,
  deliveryJobs,
  latestEvaluationRun,
  onRequestBusinessOpsDashboard
}: {
  businessOpsDashboard: BusinessOpsDashboard | null;
  dashboardStatus: BusinessOpsDashboardState["status"];
  dashboardMessage: string | null;
  reviewItems: HumanReviewInboxItem[];
  outboxDrafts: OutboxDraft[];
  failureReviews: DeliveryFailureReview[];
  deliveryJobs: OutboxDeliveryJob[];
  latestEvaluationRun: KnowledgeEvaluationRun | null;
  onRequestBusinessOpsDashboard: (params: { range: OpsRangeKey; channel_id: number | null }) => void;
}) {
  return (
    <section className="command-center" id="workspace-overview" aria-label="坐席工作台总览">
      <div className="command-head">
        <div>
          <span className="section-kicker">今日经营</span>
          <h2>运营态势</h2>
        </div>
        <div className="command-status">
          <span>真实外发关闭</span>
          <strong>{deliveryJobs.length} 个队列任务</strong>
        </div>
      </div>

      <MerchantOpsOverview
        businessOpsDashboard={businessOpsDashboard}
        dashboardStatus={dashboardStatus}
        dashboardMessage={dashboardMessage}
        reviewItems={reviewItems}
        outboxDrafts={outboxDrafts}
        failureReviews={failureReviews}
        deliveryJobs={deliveryJobs}
        latestEvaluationRun={latestEvaluationRun}
        onRequestDashboard={onRequestBusinessOpsDashboard}
      />
    </section>
  );
}

type OpsRangeKey = "today" | "7d" | "30d";

const OPS_RANGE_OPTIONS: Array<{ key: OpsRangeKey; label: string }> = [
  { key: "today", label: "今日" },
  { key: "7d", label: "近 7 天" },
  { key: "30d", label: "近 30 天" }
];

function OpsChartFrame({ children }: { children: ReactElement }) {
  return (
    <Suspense fallback={<div className="ops-chart ops-chart-loading" role="status">图表加载中</div>}>
      {children}
    </Suspense>
  );
}

function MerchantOpsOverview({
  businessOpsDashboard,
  dashboardStatus,
  dashboardMessage,
  reviewItems,
  outboxDrafts,
  failureReviews,
  deliveryJobs,
  latestEvaluationRun,
  onRequestDashboard
}: {
  businessOpsDashboard: BusinessOpsDashboard | null;
  dashboardStatus: BusinessOpsDashboardState["status"];
  dashboardMessage: string | null;
  reviewItems: HumanReviewInboxItem[];
  outboxDrafts: OutboxDraft[];
  failureReviews: DeliveryFailureReview[];
  deliveryJobs: OutboxDeliveryJob[];
  latestEvaluationRun: KnowledgeEvaluationRun | null;
  onRequestDashboard: (params: { range: OpsRangeKey; channel_id: number | null }) => void;
}) {
  const [selectedRange, setSelectedRange] = useState<OpsRangeKey>("today");
  const [selectedChannel, setSelectedChannel] = useState("all");
  const now = Date.now();
  const rangeStart = getOpsRangeStart(selectedRange, now);

  const channelOptions = useMemo(() => {
    if (businessOpsDashboard?.range === selectedRange && businessOpsDashboard.channels.length > 0) {
      const totalCount =
        businessOpsDashboard.summary.inbound_conversations +
        businessOpsDashboard.summary.open_reviews +
        businessOpsDashboard.summary.pending_outbox_drafts +
        businessOpsDashboard.summary.ready_outbox_drafts +
        businessOpsDashboard.summary.open_failure_reviews +
        businessOpsDashboard.summary.blocked_delivery_jobs;
      return [
        { key: "all", label: "全部渠道", count: totalCount },
        ...businessOpsDashboard.channels.slice(0, 6).map((channel) => ({
          key: `channel-${channel.channel_id}`,
          label: channel.channel_name || formatOpsChannelLabel(channel.channel_id),
          count: channel.workload + channel.exception_count + channel.inbound_conversations
        }))
      ];
    }
    const channelCounts = new Map<number, number>();
    const addChannel = (channelId: number) => {
      channelCounts.set(channelId, (channelCounts.get(channelId) ?? 0) + 1);
    };

    reviewItems.forEach((item) => addChannel(item.conversation.channel_id));
    outboxDrafts.forEach((draft) => addChannel(draft.channel_id));
    failureReviews.forEach((review) => addChannel(review.channel_id));
    deliveryJobs.forEach((job) => addChannel(job.channel_id));

    return [
      { key: "all", label: "全部渠道", count: reviewItems.length + outboxDrafts.length + failureReviews.length + deliveryJobs.length },
      ...Array.from(channelCounts.entries())
        .sort((left, right) => right[1] - left[1])
        .slice(0, 5)
        .map(([channelId, count]) => ({
          key: `channel-${channelId}`,
          label: formatOpsChannelLabel(channelId),
          count
        }))
    ];
  }, [businessOpsDashboard, deliveryJobs, failureReviews, outboxDrafts, reviewItems, selectedRange]);

  const selectedChannelId = selectedChannel === "all" ? null : Number(selectedChannel.replace("channel-", ""));
  const requestDashboard = (range: OpsRangeKey, channelId: number | null) => {
    onRequestDashboard({ range, channel_id: channelId });
  };
  const handleRangeSelect = (range: OpsRangeKey) => {
    setSelectedRange(range);
    requestDashboard(range, selectedChannelId);
  };
  const handleChannelSelect = (key: string) => {
    const nextChannelId = key === "all" ? null : Number(key.replace("channel-", ""));
    setSelectedChannel(key);
    requestDashboard(selectedRange, nextChannelId);
  };
  const matchesChannel = (channelId: number) => selectedChannelId === null || selectedChannelId === channelId;
  const withinRange = (value: string | null) => {
    const timeValue = getTimeValue(value);
    return timeValue === 0 || timeValue >= rangeStart;
  };

  const scopedReviewItems = reviewItems.filter(
    (item) => matchesChannel(item.conversation.channel_id) && withinRange(item.created_at ?? item.conversation.last_message_at)
  );
  const scopedOutboxDrafts = outboxDrafts.filter(
    (draft) => matchesChannel(draft.channel_id) && withinRange(draft.created_at ?? draft.updated_at)
  );
  const scopedFailureReviews = failureReviews.filter(
    (review) => matchesChannel(review.channel_id) && withinRange(review.created_at ?? review.updated_at)
  );
  const scopedDeliveryJobs = deliveryJobs.filter(
    (job) => matchesChannel(job.channel_id) && withinRange(job.created_at ?? job.updated_at ?? job.next_run_at)
  );

  const highRiskCount = scopedReviewItems.filter((item) => ["high", "critical"].includes(item.risk_level)).length;
  const pendingDrafts = scopedOutboxDrafts.filter((draft) => draft.status === "pending_confirmation").length;
  const readyDrafts = scopedOutboxDrafts.filter((draft) => draft.status === "ready_to_send").length;
  const blockedJobs = scopedDeliveryJobs.filter((job) =>
    ["blocked", "dead_letter", "dead_lettered", "failed"].includes(job.status)
  ).length;
  const retryJobs = scopedDeliveryJobs.filter((job) => ["retry_scheduled", "pending"].includes(job.status)).length;
  const channelExceptionCount = scopedFailureReviews.length + blockedJobs;
  const knowledgeGaps = latestEvaluationRun
    ? latestEvaluationRun.case_results.filter((item) =>
        ["no_hit", "expected_terms_missing", "expected_evidence_missing"].includes(item.failure_reason)
      ).length
    : 0;
  const workloadTotal = Math.max(1, scopedReviewItems.length + scopedOutboxDrafts.length);
  const totalSignals =
    scopedReviewItems.length + scopedOutboxDrafts.length + scopedFailureReviews.length + scopedDeliveryJobs.length;
  const averageWaitMinutes = scopedReviewItems.length
    ? Math.max(
        1,
        Math.round(
          scopedReviewItems.reduce((sum, item) => {
            const lastMessageAt = getTimeValue(item.conversation.last_message_at);
            return sum + (lastMessageAt ? Math.max(0, now - lastMessageAt) / 60000 : 0);
          }, 0) / scopedReviewItems.length
        )
      )
    : 0;
  const aiDraftCoverage = scopedOutboxDrafts.length / workloadTotal;
  const manualReviewPressure = scopedReviewItems.length / workloadTotal;
  const exceptionPressure = channelExceptionCount / Math.max(1, totalSignals);
  const knowledgeGapPressure = latestEvaluationRun ? knowledgeGaps / Math.max(1, latestEvaluationRun.total_cases) : 0;
  const healthScore = Math.max(
    0,
    Math.min(100, Math.round((1 - manualReviewPressure * 0.36 - exceptionPressure * 0.32 - knowledgeGapPressure * 0.32) * 100))
  );
  const activeOpsDashboard =
    businessOpsDashboard?.range === selectedRange && businessOpsDashboard.channel_id === selectedChannelId
      ? businessOpsDashboard
      : null;
  const dashboardSummary = activeOpsDashboard?.summary ?? null;
  const dashboardQuality = activeOpsDashboard?.quality ?? null;
  const displayInboundConversations = dashboardSummary?.inbound_conversations ?? scopedReviewItems.length + scopedOutboxDrafts.length;
  const displayInboundMessages = dashboardSummary?.inbound_messages ?? 0;
  const displayHighRiskCount = dashboardSummary?.high_risk_reviews ?? highRiskCount;
  const displayPendingDrafts = dashboardSummary?.pending_outbox_drafts ?? pendingDrafts;
  const displayReadyDrafts = dashboardSummary?.ready_outbox_drafts ?? readyDrafts;
  const displayOpenReviews = dashboardSummary?.open_reviews ?? scopedReviewItems.length;
  const displayDraftTotal = displayPendingDrafts + displayReadyDrafts;
  const displayChannelExceptionCount =
    dashboardSummary ? dashboardSummary.open_failure_reviews + dashboardSummary.blocked_delivery_jobs : channelExceptionCount;
  const displayKnowledgeGaps = dashboardSummary?.open_knowledge_gaps ?? knowledgeGaps;
  const displayAverageWaitMinutes = dashboardSummary?.average_wait_minutes ?? averageWaitMinutes;
  const displayAiDraftCoverage = dashboardSummary?.ai_draft_coverage ?? aiDraftCoverage;
  const displayManualReviewPressure = dashboardSummary?.manual_review_pressure ?? manualReviewPressure;
  const displayExceptionPressure = dashboardSummary?.exception_pressure ?? exceptionPressure;
  const displayHealthScore = dashboardSummary?.health_score ?? healthScore;
  const displayRiskLoad = displayHighRiskCount + displayChannelExceptionCount + displayKnowledgeGaps;
  const healthTone = displayHealthScore >= 82 ? "success" : displayHealthScore >= 68 ? "watch" : "risk";
  const healthLabel = displayHealthScore >= 82 ? "稳定" : displayHealthScore >= 68 ? "关注" : "高压";
  const healthCopy =
    displayHealthScore >= 82
      ? "接待链路运行平稳，继续保持抽检、知识补齐和外发授权门禁。"
      : displayHealthScore >= 68
        ? "转人工或异常信号开始抬升，优先处理高风险会话和知识缺口。"
        : "当前压力偏高，建议暂停扩量，先定位错因并收紧外发开关。";
  const rangeLabel = OPS_RANGE_OPTIONS.find((item) => item.key === selectedRange)?.label ?? "当前";
  const selectedChannelLabel = selectedChannel === "all"
    ? "全部渠道"
    : activeOpsDashboard?.filters.channel_name ??
      channelOptions.find((item) => item.key === selectedChannel)?.label ??
      (selectedChannelId === null ? "全部渠道" : `渠道 #${selectedChannelId}`);
  const dashboardFallbackReason =
    dashboardStatus === "error" && dashboardMessage
      ? `服务端聚合读取失败：${dashboardMessage}。当前显示已加载数据的本地汇总。`
      : businessOpsDashboard && businessOpsDashboard.range !== selectedRange
      ? "当前时间范围尚未刷新服务端聚合，显示已加载数据的本地汇总。"
      : businessOpsDashboard && businessOpsDashboard.channel_id !== selectedChannelId
        ? "当前渠道筛选尚未刷新服务端聚合，显示已加载数据的本地汇总。"
        : "未读取到服务端运营聚合，显示预览或已加载样本。";
  const dashboardDataMode =
    activeOpsDashboard?.data_source.label ??
    (dashboardStatus === "loading" ? "刷新中 · 本地汇总" : businessOpsDashboard ? "本地筛选样本" : "本地样本");
  const dashboardSourceLine = activeOpsDashboard
    ? `${activeOpsDashboard.data_source.label} · ${activeOpsDashboard.source_window.label} · ${activeOpsDashboard.filters.is_channel_filtered ? activeOpsDashboard.filters.channel_name ?? "已筛选渠道" : "全部渠道"} · ${activeOpsDashboard.data_source.contract_version}`
    : `${dashboardDataMode} · ${rangeLabel} · ${selectedChannelLabel}`;
  const dashboardSourceDescription = activeOpsDashboard
    ? `当前首页使用后端运营聚合接口，来源为 ${activeOpsDashboard.data_source.source}，聚合粒度为 ${activeOpsDashboard.data_source.aggregation_grain}，不包含客户原文、AI 草稿正文或出站草稿全文。`
    : dashboardFallbackReason;
  const dashboardContractPills = activeOpsDashboard
    ? [
        `窗口：${activeOpsDashboard.source_window.label}`,
        `刷新：${activeOpsDashboard.data_source.refresh_model}`,
        `源表：${activeOpsDashboard.data_source.source_tables.length} 类`,
        `排除敏感字段：${activeOpsDashboard.data_source.excluded_fields.length} 项`
      ]
    : [
        dashboardStatus === "loading" ? "服务端聚合刷新中" : "本地汇总",
        rangeLabel,
        selectedChannelLabel
      ];
  const dashboardFilterProof = activeOpsDashboard
    ? `服务端已按 ${rangeLabel} / ${
        activeOpsDashboard.filters.is_channel_filtered
          ? activeOpsDashboard.filters.channel_name ?? selectedChannelLabel
          : "全部渠道"
      } 返回聚合结果`
    : `当前选择 ${rangeLabel} / ${selectedChannelLabel}，${dashboardFallbackReason}`;
  const taskHref = (
    section: WorkspaceSection,
    task: string,
    title: string,
    description: string,
    options: { status?: string; queue?: string; emptyText?: string } = {}
  ) =>
    buildWorkspaceTaskHref(section, {
      task,
      title,
      description,
      range: selectedRange,
      channelId: selectedChannelId,
      channelLabel: selectedChannelLabel,
      status: options.status,
      queue: options.queue,
      emptyText: options.emptyText
    });
  const highRiskLiveHref = taskHref(
    "live",
    "high-risk-conversations",
    "高风险会话队列",
    "从运营总览进入接待工作台，只看当前时间窗和渠道上下文下的高风险会话。",
    {
      queue: "high_risk",
      emptyText: "本时间窗口暂无高风险会话。可切回全部队列继续抽检。"
    }
  );
  const liveInboundHref = taskHref(
    "live",
    "live-inbound",
    "入站会话队列",
    "从运营总览进入接待工作台，保留当前时间窗和渠道上下文。",
    {
      queue: "all",
      emptyText: "本时间窗口暂无入站会话。"
    }
  );
  const highRiskReviewHref = taskHref(
    "live",
    "high-risk-reviews",
    "高风险会话队列",
    "从运营总览进入接待工作台，只看赔付、投诉、法务或敏感承诺类高风险会话。",
    {
      queue: "high_risk",
      emptyText: "本时间窗口暂无高风险会话。"
    }
  );
  const pendingOutboxHref = taskHref(
    "live",
    "pending-outbox",
    "待确认回复",
    "从运营总览进入接待工作台，只看仍需人工确认的回复；真实外发继续关闭。",
    {
      queue: "pending_outbox",
      emptyText: "本时间窗口暂无待确认回复。"
    }
  );
  const knowledgeGapsHref = taskHref(
    "gaps",
    "knowledge-gaps",
    "知识缺口修复",
    "从运营总览进入知识缺口，把无知识命中、期望证据缺失和低置信问题转成修复任务。",
    {
      status: "open",
      emptyText: "本时间窗口暂无待处理知识缺口。"
    }
  );
  const channelExceptionsHref = taskHref(
    "channels",
    "channel-exceptions",
    "渠道异常复盘",
    "从运营总览进入渠道接入中心，只看失败复盘、阻断队列和官方接入阻塞。",
    {
      status: "open",
      emptyText: "本时间窗口暂无渠道异常或失败复盘任务。"
    }
  );
  const commandTiles = [
    {
      label: "入站会话",
      value: displayInboundConversations,
      note: displayInboundMessages ? `${displayInboundMessages} 条消息` : `${displayOpenReviews} 条转人工`,
      status: selectedChannelLabel,
      href: liveInboundHref,
      tone: "default"
    },
    {
      label: "AI 覆盖",
      value: formatPercent(displayAiDraftCoverage),
      note: `${displayDraftTotal} 条草稿/待确认`,
      status: displayAiDraftCoverage >= 0.6 ? "覆盖良好" : "覆盖偏低",
      href: highRiskReviewHref,
      tone: displayAiDraftCoverage >= 0.6 ? "success" : "watch"
    },
    {
      label: "人工压力",
      value: formatPercent(displayManualReviewPressure),
      note: `${displayAverageWaitMinutes} 分钟平均等待`,
      status: displayHighRiskCount > 0 ? `${displayHighRiskCount} 条高风险` : "风险正常",
      href: highRiskReviewHref,
      tone: displayHighRiskCount > 0 ? "risk" : "default"
    },
    {
      label: "待修复缺口",
      value: displayRiskLoad,
      note: `渠道 ${displayChannelExceptionCount} · 知识 ${displayKnowledgeGaps}`,
      status: displayRiskLoad > 0 ? "需复盘" : "暂无新增",
      href: displayChannelExceptionCount > displayKnowledgeGaps ? channelExceptionsHref : knowledgeGapsHref,
      tone: displayRiskLoad > 0 ? "risk" : "success"
    }
  ];
  const riskSegments = [
    {
      label: "高风险会话",
      count: displayHighRiskCount,
      progress: Math.min(100, Math.round((displayHighRiskCount / Math.max(1, displayOpenReviews)) * 100))
    },
    {
      label: "渠道异常",
      count: displayChannelExceptionCount,
      progress: Math.min(100, Math.round(displayExceptionPressure * 100))
    },
    {
      label: "知识缺口",
      count: displayKnowledgeGaps,
      progress: Math.min(100, Math.round(knowledgeGapPressure * 100))
    }
  ];
  const priorityActions = [
    {
      title: "查看高风险会话",
      note: displayHighRiskCount > 0 ? "先看可能投诉、事实不确定和高价值线索" : "当前保持抽检即可",
      count: displayHighRiskCount,
      href: highRiskLiveHref,
      tone: displayHighRiskCount > 0 ? "risk" : "default"
    },
    {
      title: "确认待处理回复",
      note: displayPendingDrafts > 0 ? "正式外发前仍需授权和回执" : "回复池暂时没有积压",
      count: displayPendingDrafts,
      href: pendingOutboxHref,
      tone: displayPendingDrafts > 0 ? "watch" : "default"
    },
    {
      title: "修复知识缺口",
      note: displayKnowledgeGaps > 0 ? "补知识、改 FAQ，并加入回归题" : "暂未发现新的知识缺口",
      count: displayKnowledgeGaps,
      href: knowledgeGapsHref,
      tone: displayKnowledgeGaps > 0 ? "risk" : "default"
    },
    {
      title: "复盘渠道异常",
      note: displayChannelExceptionCount > 0 ? "检查回执异常、授权阻塞和队列失败" : "渠道异常池暂时清空",
      count: displayChannelExceptionCount,
      href: channelExceptionsHref,
      tone: displayChannelExceptionCount > 0 ? "risk" : "default"
    }
  ];
  const metricCards = [
    {
      label: "入站与待办",
      value: displayInboundConversations + displayOpenReviews + displayDraftTotal,
      badge: dashboardDataMode,
      note: displayInboundMessages
        ? `${displayInboundMessages} 条入站消息 · ${displayOpenReviews} 转人工`
        : `${displayOpenReviews} 转人工 · ${displayPendingDrafts} 待确认 · ${displayReadyDrafts} 待回执`,
      progress: Math.min(
        100,
        Math.round(((displayInboundConversations + displayOpenReviews + displayDraftTotal) / Math.max(1, totalSignals)) * 100)
      ),
      href: liveInboundHref,
      tone: "default"
    },
    {
      label: "AI 草稿覆盖",
      value: formatPercent(displayAiDraftCoverage),
      badge: "草稿池",
      note: `${displayDraftTotal}/${Math.max(1, displayDraftTotal + displayOpenReviews)} 条已有草稿或待确认`,
      progress: Math.round(displayAiDraftCoverage * 100),
      href: highRiskReviewHref,
      tone: "success"
    },
    {
      label: "转人工压力",
      value: formatPercent(displayManualReviewPressure),
      badge: `${displayAverageWaitMinutes} 分钟`,
      note: displayHighRiskCount > 0 ? `${displayHighRiskCount} 条高风险优先` : "当前无高风险会话",
      progress: Math.round(displayManualReviewPressure * 100),
      href: highRiskReviewHref,
      tone: displayHighRiskCount > 0 ? "risk" : "warning"
    },
    {
      label: "异常与缺口",
      value: displayChannelExceptionCount + displayKnowledgeGaps,
      badge: "待复盘",
      note: `渠道 ${displayChannelExceptionCount} · 知识 ${displayKnowledgeGaps}`,
      progress: Math.min(100, Math.round((displayExceptionPressure + knowledgeGapPressure) * 100)),
      href: displayChannelExceptionCount > displayKnowledgeGaps ? channelExceptionsHref : knowledgeGapsHref,
      tone: displayChannelExceptionCount + displayKnowledgeGaps > 0 ? "risk" : "success"
    }
  ];
  const funnelStages = activeOpsDashboard
    ? activeOpsDashboard.funnel.map((item) => ({ label: item.label, count: item.count }))
    : [
        { label: "入站样本", count: scopedReviewItems.length + scopedOutboxDrafts.length },
        { label: "AI 已草拟", count: scopedOutboxDrafts.length },
        { label: "转人工", count: scopedReviewItems.length },
        { label: "待确认回复", count: pendingDrafts }
      ];
  const channelRows = activeOpsDashboard?.channels.length
    ? activeOpsDashboard.channels.map((channel) => ({
        channelId: channel.channel_id,
        label: channel.channel_name || formatOpsChannelLabel(channel.channel_id),
        shortLabel: (channel.channel_name || formatOpsChannelLabel(channel.channel_id)).replace("客服", "").replace("店铺", ""),
        count: channel.workload + channel.inbound_conversations,
        exceptionCount: channel.exception_count
      }))
    : buildOpsChannelRows(scopedReviewItems, scopedOutboxDrafts, scopedFailureReviews, scopedDeliveryJobs);
  const qualityRows = [
    { label: "知识命中", value: dashboardQuality?.hit_rate ?? latestEvaluationRun?.hit_rate ?? null },
    { label: "引用覆盖", value: dashboardQuality?.citation_coverage ?? latestEvaluationRun?.citation_coverage ?? null },
    { label: "期望词覆盖", value: dashboardQuality?.expected_term_coverage ?? latestEvaluationRun?.expected_term_coverage ?? null },
    {
      label: "人工复盘占比",
      value:
        dashboardQuality?.needs_review_rate ??
        (latestEvaluationRun ? latestEvaluationRun.needs_review_cases / Math.max(1, latestEvaluationRun.total_cases) : null)
    }
  ];
  const trendBuckets = activeOpsDashboard
    ? activeOpsDashboard.trend.map((item) => ({
        label: item.label,
        review: item.reviews,
        draft: item.drafts,
        exception: item.exceptions
      }))
    : buildOpsTrendBuckets(
        [
          ...scopedReviewItems.map((item) => ({ time: item.created_at ?? item.conversation.last_message_at, type: "review" as const })),
          ...scopedOutboxDrafts.map((draft) => ({ time: draft.created_at ?? draft.updated_at, type: "draft" as const })),
          ...scopedFailureReviews.map((review) => ({ time: review.created_at ?? review.updated_at, type: "exception" as const }))
        ],
        rangeStart,
        now,
        selectedRange
      );
  const trendOption = useMemo<EChartsOption>(
    () => ({
      color: ["#1d6fdb", "#17845a", "#c43d32"],
      tooltip: { trigger: "axis" },
      grid: { top: 26, right: 12, bottom: 26, left: 34 },
      xAxis: {
        type: "category",
        boundaryGap: false,
        data: trendBuckets.map((item) => item.label),
        axisLine: { lineStyle: { color: "#dbe2ee" } },
        axisLabel: { color: "#657085", fontSize: 11 }
      },
      yAxis: {
        type: "value",
        minInterval: 1,
        splitLine: { lineStyle: { color: "#edf2f8" } },
        axisLabel: { color: "#657085", fontSize: 11 }
      },
      series: [
        {
          name: "转人工",
          type: "line",
          smooth: true,
          symbolSize: 6,
          areaStyle: { opacity: 0.12 },
          data: trendBuckets.map((item) => item.review)
        },
        {
          name: "AI 草稿",
          type: "line",
          smooth: true,
          symbolSize: 6,
          areaStyle: { opacity: 0.1 },
          data: trendBuckets.map((item) => item.draft)
        },
        {
          name: "异常",
          type: "line",
          smooth: true,
          symbolSize: 6,
          data: trendBuckets.map((item) => item.exception)
        }
      ]
    }),
    [trendBuckets]
  );
  const funnelOption = useMemo<EChartsOption>(
    () => ({
      color: ["#1558b0"],
      tooltip: { trigger: "axis", axisPointer: { type: "shadow" } },
      grid: { top: 12, right: 14, bottom: 22, left: 78 },
      xAxis: {
        type: "value",
        minInterval: 1,
        splitLine: { lineStyle: { color: "#edf2f8" } },
        axisLabel: { color: "#657085", fontSize: 11 }
      },
      yAxis: {
        type: "category",
        inverse: true,
        data: funnelStages.map((item) => item.label),
        axisLabel: { color: "#42526b", fontWeight: 700 }
      },
      series: [
        {
          name: "数量",
          type: "bar",
          barWidth: 15,
          data: funnelStages.map((item) => item.count),
          itemStyle: { borderRadius: [0, 8, 8, 0] }
        }
      ]
    }),
    [funnelStages]
  );
  const channelOption = useMemo<EChartsOption>(
    () => ({
      color: ["#1d6fdb", "#c43d32"],
      tooltip: { trigger: "axis", axisPointer: { type: "shadow" } },
      legend: { top: 0, right: 0, textStyle: { color: "#657085" } },
      grid: { top: 34, right: 12, bottom: 28, left: 42 },
      xAxis: {
        type: "category",
        data: channelRows.map((item) => item.shortLabel),
        axisLine: { lineStyle: { color: "#dbe2ee" } },
        axisLabel: { color: "#657085", fontSize: 11 }
      },
      yAxis: {
        type: "value",
        minInterval: 1,
        splitLine: { lineStyle: { color: "#edf2f8" } },
        axisLabel: { color: "#657085", fontSize: 11 }
      },
      series: [
        {
          name: "处理量",
          type: "bar",
          stack: "channel",
          barWidth: 18,
          data: channelRows.map((item) => item.count),
          itemStyle: { borderRadius: [7, 7, 0, 0] }
        },
        {
          name: "异常",
          type: "bar",
          stack: "channel",
          barWidth: 18,
          data: channelRows.map((item) => item.exceptionCount)
        }
      ]
    }),
    [channelRows]
  );
  const qualityOption = useMemo<EChartsOption>(
    () => ({
      color: ["#1558b0"],
      radar: {
        radius: "68%",
        splitNumber: 4,
        axisName: { color: "#657085", fontSize: 11 },
        indicator: qualityRows.map((row) => ({ name: row.label, max: 1 }))
      },
      series: [
        {
          type: "radar",
          areaStyle: { opacity: 0.16 },
          lineStyle: { width: 2 },
          symbolSize: 5,
          data: [
            {
              name: "质量信号",
              value: qualityRows.map((row) => (row.value === null ? 0 : Number(row.value.toFixed(2))))
            }
          ]
        }
      ]
    }),
    [qualityRows]
  );

  return (
    <div className="ops-bi-shell" aria-label="运营总览 BI 指挥舱">
      <div className="ops-bi-control-bar">
        <div className="ops-bi-title">
          <span>运营指挥舱 · {dashboardDataMode}</span>
          <strong>服务压力、AI 覆盖和风险缺口</strong>
          <p>{dashboardSourceDescription}</p>
          <div className="ops-bi-source-contract" aria-label="运营总览数据口径">
            {dashboardContractPills.map((pill) => (
              <em key={pill}>{pill}</em>
            ))}
          </div>
          {activeOpsDashboard?.data_source.caveats[0] ? (
            <small className="ops-bi-source-caveat">{activeOpsDashboard.data_source.caveats[0]}</small>
          ) : null}
        </div>
        <div className="ops-bi-filter-stack" aria-label="运营总览筛选">
          <div className="ops-bi-range" aria-label="时间范围">
            <span>时间范围</span>
            <div>
              {OPS_RANGE_OPTIONS.map((option) => (
                <button
                  key={option.key}
                  type="button"
                  className={selectedRange === option.key ? "active" : ""}
                  aria-pressed={selectedRange === option.key}
                  onClick={() => handleRangeSelect(option.key)}
                >
                  {option.label}
                </button>
              ))}
            </div>
          </div>
          <div className="ops-bi-range" aria-label="渠道筛选">
            <span>渠道筛选</span>
            <div>
              {channelOptions.map((option) => (
                <button
                  key={option.key}
                  type="button"
                  className={selectedChannel === option.key ? "active" : ""}
                  aria-pressed={selectedChannel === option.key}
                  onClick={() => handleChannelSelect(option.key)}
                >
                  {option.label}
                </button>
              ))}
            </div>
          </div>
          <div
            className={`ops-bi-filter-proof ${activeOpsDashboard ? "is-aligned" : "is-fallback"}`}
            data-filter-alignment={activeOpsDashboard ? "server-aligned" : "local-fallback"}
          >
            {dashboardStatus === "loading" ? "服务端聚合刷新中，当前暂保留上一版可用数据。" : dashboardFilterProof}
          </div>
        </div>
      </div>

      <div className="ops-bi-signal-strip" aria-label="核心经营信号">
        {commandTiles.map((tile) => (
          <a key={tile.label} className={`ops-bi-signal-card tone-${tile.tone}`} href={tile.href}>
            <span>{tile.label}</span>
            <strong>{tile.value}</strong>
            <small>{tile.note}</small>
            <em>{tile.status}</em>
          </a>
        ))}
      </div>

      <section className="ops-bi-command-center" aria-label="运营态势">
        <article className={`ops-bi-health-panel tone-${healthTone}`}>
          <div className="ops-bi-panel-head">
            <span>运营健康</span>
            <em>{healthLabel}</em>
          </div>
          <div
            className="ops-bi-score-ring"
            style={{
              background: `conic-gradient(#1558b0 ${displayHealthScore}%, #e7edf5 ${displayHealthScore}% 100%)`
            }}
            aria-label={`运营健康度 ${displayHealthScore} 分`}
          >
            <div>
              <strong>{displayHealthScore}</strong>
              <small>/100</small>
            </div>
          </div>
          <p>{healthCopy}</p>
          <div className="ops-bi-risk-stack" aria-label="风险组成">
            {riskSegments.map((segment) => (
              <div key={segment.label} className="ops-bi-risk-row">
                <span>{segment.label}</span>
                <div aria-hidden="true"><i style={{ width: `${Math.max(4, segment.progress)}%` }} /></div>
                <strong>{segment.count}</strong>
              </div>
            ))}
          </div>
        </article>

        <article className="ops-bi-trend-panel">
          <div className="ops-bi-card-head">
            <div>
              <span>实时压力趋势</span>
              <strong>{rangeLabel} · {selectedChannelLabel}</strong>
            </div>
            <small>{dashboardSourceLine}</small>
          </div>
          <OpsChartFrame>
            <OpsDashboardChart option={trendOption} className="ops-chart-trend" ariaLabel="当前样本转人工、AI 草稿和异常趋势" />
          </OpsChartFrame>
          <div className="ops-bi-trend-legend" aria-label="趋势摘要">
            <span><i className="tone-review" />转人工 {displayOpenReviews}</span>
            <span><i className="tone-draft" />AI 草稿 {displayDraftTotal}</span>
            <span><i className="tone-exception" />异常 {displayChannelExceptionCount}</span>
          </div>
        </article>

        <aside className="ops-bi-priority-panel" aria-label="今日优先动作">
          <div className="ops-bi-card-head">
            <div>
              <span>优先动作</span>
              <strong>今天最该处理什么</strong>
            </div>
            <small>{dashboardSourceLine}</small>
          </div>
          <div className="ops-bi-action-list">
            {priorityActions.map((action) => (
              <a key={action.title} className={`ops-bi-action-row tone-${action.tone}`} href={action.href}>
                <span>
                  <strong>{action.title}</strong>
                  <small>{action.note}</small>
                </span>
                <em>{action.count}</em>
              </a>
            ))}
          </div>
        </aside>
      </section>

      <div className="ops-bi-metric-grid">
        {metricCards.map((metric) => (
          <a key={metric.label} className={`ops-bi-metric tone-${metric.tone}`} href={metric.href}>
            <div className="ops-bi-metric-top">
              <span>{metric.label}</span>
              <em>{metric.badge}</em>
            </div>
            <strong>{metric.value}</strong>
            <div className="ops-bi-meter" aria-hidden="true">
              <i style={{ width: `${Math.max(6, metric.progress)}%` }} />
            </div>
            <small>{metric.note}</small>
          </a>
        ))}
      </div>

      <div className="ops-bi-chart-grid">
        <article className="ops-bi-card">
          <div className="ops-bi-card-head">
            <div>
              <span>处理漏斗</span>
              <strong>试点链路状态</strong>
            </div>
            <small>{dashboardSourceLine}</small>
          </div>
          <OpsChartFrame>
            <OpsDashboardChart option={funnelOption} className="ops-chart-compact" ariaLabel="试点链路处理漏斗" />
          </OpsChartFrame>
        </article>

        <article className="ops-bi-card">
          <div className="ops-bi-card-head">
            <div>
              <span>渠道矩阵</span>
              <strong>入口状态与异常压力</strong>
            </div>
            <small>{displayChannelExceptionCount > 0 ? `${displayChannelExceptionCount} 个异常待复盘` : "暂无异常"}</small>
          </div>
          <OpsChartFrame>
            <OpsDashboardChart option={channelOption} className="ops-chart-compact" ariaLabel="渠道处理量和异常压力" />
          </OpsChartFrame>
        </article>

        <article className="ops-bi-card">
          <div className="ops-bi-card-head">
            <div>
              <span>质量诊断</span>
              <strong>知识与事实性信号</strong>
            </div>
            <small>{dashboardQuality?.total_cases ? `最近题库 ${dashboardQuality.total_cases} 题` : latestEvaluationRun ? `最近题库 ${latestEvaluationRun.total_cases} 题` : "尚未运行题库"}</small>
          </div>
          <OpsChartFrame>
            <OpsDashboardChart option={qualityOption} className="ops-chart-compact" ariaLabel="知识与事实性质量雷达" />
          </OpsChartFrame>
          <div className="ops-bi-quality-pills">
            {qualityRows.map((row) => (
              <span key={row.label}>
                {row.label}
                <strong>{row.value === null ? "-" : formatPercent(row.value)}</strong>
              </span>
            ))}
          </div>
        </article>
      </div>

    </div>
  );
}

function OpsMetric({ label, value, note }: { label: string; value: number; note: string }) {
  return (
    <div className="ops-metric">
      <span>{label}</span>
      <strong>{value}</strong>
      <small>{note}</small>
    </div>
  );
}

function ChannelHealthTable({
  failureReviews,
  deliveryJobs,
  latestEvaluationRun
}: {
  failureReviews: DeliveryFailureReview[];
  deliveryJobs: OutboxDeliveryJob[];
  latestEvaluationRun: KnowledgeEvaluationRun | null;
}) {
  const blockedJobs = deliveryJobs.filter((job) =>
    ["blocked", "dead_letter", "dead_lettered", "failed"].includes(job.status)
  ).length;
  const rows = [
    {
      channel: "官网客服沙盒",
      inbound: "已可内部编排",
      outbound: "外发关闭",
      risk: failureReviews.length > 0 ? `${failureReviews.length} 个复盘项` : "暂无异常",
      next: "继续白名单试点"
    },
    {
      channel: "企业微信客服",
      inbound: "官方测试",
      outbound: "待 URL 验证",
      risk: "需公网 HTTPS、Token、AESKey",
      next: "先过回调验证"
    },
    {
      channel: "公众号 / 电商",
      inbound: "待授权",
      outbound: "未打开",
      risk: "只走官方接口或服务商授权",
      next: "签约后逐渠道接入"
    },
    {
      channel: "质量评测",
      inbound: latestEvaluationRun ? `运行 #${latestEvaluationRun.id}` : "未运行",
      outbound: "不外发",
      risk: blockedJobs > 0 ? `${blockedJobs} 个阻断队列` : "无阻断",
      next: latestEvaluationRun ? `复盘 ${latestEvaluationRun.needs_review_cases} 题` : "导入客户题库"
    }
  ];

  return (
    <div className="channel-health-table" role="table" aria-label="渠道健康明细">
      <div className="channel-health-head" role="row">
        <span role="columnheader">通道</span>
        <span role="columnheader">入站</span>
        <span role="columnheader">出站</span>
        <span role="columnheader">风险</span>
        <span role="columnheader">下一步</span>
      </div>
      {rows.map((row) => (
        <div key={row.channel} className="channel-health-row" role="row">
          <span role="cell"><strong>{row.channel}</strong></span>
          <span role="cell">{row.inbound}</span>
          <span role="cell">{row.outbound}</span>
          <span role="cell">{row.risk}</span>
          <span role="cell">{row.next}</span>
        </div>
      ))}
    </div>
  );
}

function ReviewEvidenceDetail({
  item,
  outboxDrafts,
  failureReviews,
  deliveryJobs,
  onSelectReview
}: {
  item: HumanReviewInboxItem | null;
  outboxDrafts: OutboxDraft[];
  failureReviews: DeliveryFailureReview[];
  deliveryJobs: OutboxDeliveryJob[];
  onSelectReview: (item: HumanReviewInboxItem) => void;
}) {
  if (!item) {
    return (
      <article className="case-detail-empty" aria-label="会话处置详情">
        <MessageSquare size={22} />
        <strong>暂无待处置会话</strong>
        <p>当前没有 open 人工审核任务。真实渠道接入前，可先通过可信入站 worker 或测试题库产生待审核草稿。</p>
      </article>
    );
  }

  const relatedDraft = outboxDrafts.find(
    (draft) => draft.source_review_task_id === item.id || draft.source_workflow_run_id === item.workflow_run_id
  );
  const relatedJob = relatedDraft
    ? deliveryJobs.find((job) => job.outbox_draft_id === relatedDraft.id)
    : undefined;
  const relatedFailure = relatedDraft
    ? failureReviews.find((failure) => failure.outbox_draft_id === relatedDraft.id)
    : undefined;
  const knowledgeMatches = item.evidence.knowledge_matches.slice(0, 4);

  return (
    <article className="case-detail" aria-label="会话处置详情">
      <div className="case-detail-head">
        <div>
          <span className="section-kicker">会话处置详情</span>
          <h2>{item.conversation.subject || `会话 #${item.conversation.id}`}</h2>
        </div>
        <button type="button" className="ghost-action" onClick={() => onSelectReview(item)}>
          <Search size={17} />
          当前证据
        </button>
      </div>

      <div className="case-status-line">
        <span className={`risk-pill risk-${item.risk_level}`}>{item.risk_level}</span>
        <span>转人工：{item.reason}</span>
        <span>流程：{item.workflow.status} / {item.workflow.current_step}</span>
      </div>

      <div className="case-message-grid">
        <section>
          <span>原始入站</span>
          <p>{item.trigger_message?.content ?? "没有关联入站消息"}</p>
        </section>
        <section>
          <span>AI 草稿</span>
          <p>{item.draft_reply || "暂无草稿"}</p>
        </section>
      </div>

      <div className="case-fact-grid">
        <section className="case-fact-block">
          <div className="section-title-row">
            <BookOpen size={18} />
            <strong>引用证据</strong>
          </div>
          {knowledgeMatches.length === 0 ? (
            <p className="inline-notice">没有可展示的知识引用，应进入知识缺口复盘。</p>
          ) : (
            <div className="citation-list">
              {knowledgeMatches.map((match, index) => (
                <article key={`${item.id}-match-${index}`} className="citation-card">
                  <strong>{readRecordString(match, "title") || `证据 ${index + 1}`}</strong>
                  <span>{readRecordString(match, "source_uri") || readRecordString(match, "source") || "未填写来源"}</span>
                  <p>{readRecordString(match, "answer") || readRecordString(match, "content_preview") || "未返回证据摘要"}</p>
                </article>
              ))}
            </div>
          )}
        </section>

        <section className="case-fact-block">
          <div className="section-title-row">
            <Bot size={18} />
            <strong>模型与出站状态</strong>
          </div>
          <dl className="detail-list">
            <div>
              <dt>模型状态</dt>
              <dd>{formatModelCallDetail(item.evidence.model_call)}</dd>
            </div>
            <div>
              <dt>检索模式</dt>
              <dd>{item.evidence.retrieval_mode || item.evidence.retrieval_engine || "未记录"}</dd>
            </div>
            <div>
              <dt>发送记录</dt>
              <dd>{formatOutboxStatus(relatedDraft, relatedJob, relatedFailure)}</dd>
            </div>
          </dl>
        </section>
      </div>

      <div className="audit-chain" aria-label="审计链">
        <div className="section-title-row">
          <ShieldCheck size={18} />
          <strong>审计链</strong>
        </div>
        <ol>
          <li>入站消息 #{item.message_id ?? "-"} 进入会话 #{item.conversation_id}</li>
          <li>处理流程 #{item.workflow_run_id} 当前步骤：{item.workflow.current_step}</li>
          <li>Human review #{item.id} 状态：{item.status}</li>
          <li>{relatedDraft ? `发送记录 #${relatedDraft.id}：${relatedDraft.status} / ${relatedDraft.delivery_status}` : "尚未生成发送记录"}</li>
          <li>外部写入保持关闭</li>
        </ol>
      </div>
    </article>
  );
}

function KnowledgeDocumentsPanel({
  state,
  evaluationState,
  customerQualityReport,
  customerQualityReportSignoffs,
  updatePackageDraft,
  templateImportDraft,
  aiServiceStatus,
  replyStrategyState,
  replyStrategyDraft,
  businessObjectDraft,
  objectKnowledgeCardDraft,
  draft,
  searchQuery,
  listView,
  hasToken,
  canImport,
  onBusinessObjectDraftChange,
  onUpdatePackageDraftChange,
  onTemplateImportDraftChange,
  onReplyStrategyDraftChange,
  onObjectKnowledgeCardDraftChange,
  onDraftChange,
  onSearchQueryChange,
  onListViewChange,
  onCreateBusinessObject,
  onPreviewUpdatePackage,
  onImportUpdatePackage,
  onPrecheckTemplateImport,
  onCreateTemplateImport,
  onRunTemplateSample,
  onPublishTemplateImport,
  onSaveReplyStrategy,
  onCreateObjectKnowledgeCard,
  onImportDocument,
  onSearchDocuments,
  onCheckPublishDocument,
  onPublishDocument,
  onRollbackDocument,
  onRefresh
}: {
  state: KnowledgeWorkbenchState;
  evaluationState: KnowledgeEvaluationState;
  customerQualityReport: CustomerQualityReportState;
  customerQualityReportSignoffs: CustomerQualityReportSignoffState;
  updatePackageDraft: KnowledgeUpdatePackageDraft;
  templateImportDraft: KnowledgeTemplateImportDraft;
  aiServiceStatus: AiServiceStatusState;
  replyStrategyState: TenantReplyStrategyState;
  replyStrategyDraft: ReplyStrategyDraft;
  businessObjectDraft: BusinessObjectDraft;
  objectKnowledgeCardDraft: ObjectKnowledgeCardDraft;
  draft: KnowledgeDocumentDraft;
  searchQuery: string;
  listView: ListViewState;
  hasToken: boolean;
  canImport: boolean;
  onBusinessObjectDraftChange: (draft: BusinessObjectDraft) => void;
  onUpdatePackageDraftChange: (draft: KnowledgeUpdatePackageDraft) => void;
  onTemplateImportDraftChange: (draft: KnowledgeTemplateImportDraft) => void;
  onReplyStrategyDraftChange: (draft: ReplyStrategyDraft) => void;
  onObjectKnowledgeCardDraftChange: (draft: ObjectKnowledgeCardDraft) => void;
  onDraftChange: (draft: KnowledgeDocumentDraft) => void;
  onSearchQueryChange: (query: string) => void;
  onListViewChange: (view: ListViewState) => void;
  onCreateBusinessObject: () => void;
  onPreviewUpdatePackage: () => void;
  onImportUpdatePackage: () => void;
  onPrecheckTemplateImport: () => void;
  onCreateTemplateImport: () => void;
  onRunTemplateSample: () => void;
  onPublishTemplateImport: () => void;
  onSaveReplyStrategy: () => void;
  onCreateObjectKnowledgeCard: () => void;
  onImportDocument: () => void;
  onSearchDocuments: () => void;
  onCheckPublishDocument: (document: KnowledgeDocument) => void;
  onPublishDocument: (document: KnowledgeDocument) => void;
  onRollbackDocument: (document: KnowledgeDocument) => void;
  onRefresh: () => void;
}) {
  const isLoading = state.status === "loading";
  const searchResult = state.searchResult;
  const [customerKnowledgeIntakeText, setCustomerKnowledgeIntakeText] = useState(DEFAULT_CUSTOMER_KNOWLEDGE_INTAKE_CSV);
  const importDisabledReason = formatAccessDisabledReason({
    hasToken,
    canManage: canImport,
    isLoading,
    action: "导入知识文档"
  });
  const businessObjectDisabledReason = formatAccessDisabledReason({
    hasToken,
    canManage: canImport,
    isLoading,
    action: "新增业务对象"
  });
  const objectCardDisabledReason = formatAccessDisabledReason({
    hasToken,
    canManage: canImport,
    isLoading,
    action: "绑定对象问答卡"
  });
  const updatePackageDisabledReason = formatAccessDisabledReason({
    hasToken,
    canManage: canImport,
    isLoading: isLoading || updatePackageDraft.status === "loading",
    action: "导入知识资料包"
  });
  const replyStrategyDisabledReason = formatAccessDisabledReason({
    hasToken,
    canManage: canImport,
    isLoading: replyStrategyState.status === "loading",
    action: "保存自动回复策略"
  });
  const searchDisabledReason = isLoading
    ? "检索暂不可用：正在加载知识库。"
    : !hasToken
      ? "检索暂不可用：请先登录本地管理员账号后读取真实知识库。"
      : "";
  const businessObjectOptions: Array<{ label: string; value: BusinessObjectType }> = [
    { label: "商品", value: "product" },
    { label: "服务", value: "service" },
    { label: "套餐", value: "package" },
    { label: "课程", value: "course" },
    { label: "项目", value: "project" },
    { label: "门店", value: "store" }
  ];
  const selectedBusinessObjectId =
    objectKnowledgeCardDraft.businessObjectId ?? state.businessObjects[0]?.id ?? null;
  const selectedBusinessObject = state.businessObjects.find((item) => item.id === selectedBusinessObjectId) ?? null;
  const updatePackageResult = updatePackageDraft.result;
  const updatePackageIsLoading = updatePackageDraft.status === "loading";
  const objectCardTotal = useMemo(
    () => Object.values(state.objectCardsByObject).reduce((total, cards) => total + cards.length, 0),
    [state.objectCardsByObject]
  );
  const policyDocuments = useMemo(
    () =>
      state.documents.filter((document) => {
        const text = `${document.title} ${document.source_type} ${document.tags.join(" ")}`;
        return /流程|政策|售后|发票|质保|退款|退换|服务记录|policy/i.test(text);
      }),
    [state.documents]
  );
  const ruleDocuments = useMemo(
    () =>
      state.documents.filter((document) => {
        const text = `${document.title} ${document.source_type} ${document.tags.join(" ")}`;
        return /禁用|禁止|承诺|转人工|人工|投诉|赔付|风险|法务|规则/i.test(text);
      }),
    [state.documents]
  );
  const persistedReplyPolicy = replyStrategyState.data?.reply_policy ?? null;
  const replyPolicyRuleCount =
    (persistedReplyPolicy?.blocked_policy_terms.length ?? 0) +
    (persistedReplyPolicy?.manual_review_terms.length ?? 0);
  const pagedDocuments = useMemo(
    () =>
      getPagedItems(state.documents, listView, {
        statusMatcher: (document, status) => document.status === status || document.ingestion_status === status,
        searchText: (document) => [
          document.title,
          document.source_uri,
          document.source_type,
          document.status,
          document.ingestion_status,
          document.tags.join(" ")
        ]
      }),
    [state.documents, listView]
  );
  const publicationRecords = useMemo(
    () => Object.values(state.publicationsByDocument).flat(),
    [state.publicationsByDocument]
  );
  const publishedDocumentCount = state.documents.filter((document) => document.status === "active").length;
  const readyDraftCount = state.documents.filter(
    (document) => document.status === "draft" && document.ingestion_status === "indexed"
  ).length;
  const passedPrecheckCount = publicationRecords.filter(
    (publication) => publication.publication_type === "publish_check" && publication.status === "passed"
  ).length;
  const blockedPublicationCount = publicationRecords.filter((publication) => publication.status === "blocked").length;
  const firstReadyDocument =
    state.documents.find((document) => document.status === "draft" && document.ingestion_status === "indexed") ?? null;
  const firstReadyDocumentActionTitle = !hasToken
    ? "请先登录本地账号后再操作知识启用流程。"
    : !canImport
      ? "当前账号没有知识库管理权限。"
      : isLoading
        ? "正在同步知识库数据，请稍候。"
        : !firstReadyDocument
          ? "暂无完成索引的草稿文档，请先导入资料并完成索引。"
          : `可对《${firstReadyDocument.title}》执行启用前复测或启用。`;
  const latestEvaluationRun = evaluationState.lastRun;
  const latestCustomerReport = customerQualityReport.data;
  const latestCustomerSignoff = customerQualityReportSignoffs.data?.items[0] ?? null;
  const customerKnowledgeIntakePackage = useMemo(
    () => buildCustomerKnowledgeUpdatePackageFromCsv(customerKnowledgeIntakeText),
    [customerKnowledgeIntakeText]
  );
  const templateImportRows = useMemo(
    () => parseKnowledgeTemplateImportRows(templateImportDraft.text),
    [templateImportDraft.text]
  );
  const customerKnowledgeIntakeCounts = {
    businessObjects: customerKnowledgeIntakePackage.business_objects.length,
    objectCards: customerKnowledgeIntakePackage.object_knowledge_cards.length,
    documents: customerKnowledgeIntakePackage.knowledge_documents.length,
    cases: customerKnowledgeIntakePackage.evaluation_sets.reduce((total, set) => total + set.cases.length, 0)
  };
  const customerPublishStepState = [
    {
      key: "intake",
      label: "资料整理",
      value: `${customerKnowledgeIntakeCounts.businessObjects} 对象 / ${customerKnowledgeIntakeCounts.objectCards} 问答`,
      note: "客户可按模板填入业务对象、标准问答、流程政策和风险规则。",
      tone: customerKnowledgeIntakeCounts.businessObjects > 0 || customerKnowledgeIntakeCounts.objectCards > 0 ? "ready" : "waiting"
    },
    {
      key: "package",
      label: "检查导入",
      value: updatePackageResult
        ? updatePackageResult.import_batch_id
          ? `已导入 #${updatePackageResult.import_batch_id}`
          : updatePackageResult.can_apply
            ? "检查可导入"
            : "检查需修正"
        : updatePackageDraft.text.trim()
          ? "等待检查"
          : "待生成资料包",
      note: updatePackageResult
        ? `新增 ${updatePackageResult.operation_counts.create ?? 0}，跳过 ${updatePackageResult.operation_counts.skip ?? 0}，错误 ${updatePackageResult.operation_counts.error ?? 0}`
        : "检查会先展示新增、跳过和错误项，不会直接改库。",
      tone: updatePackageResult?.import_batch_id ? "ready" : updatePackageResult?.can_apply ? "warning" : "waiting"
    },
    {
      key: "publish",
      label: "启用知识",
      value: `${publishedDocumentCount} 启用 / ${readyDraftCount} 待发布`,
      note: firstReadyDocument ? `可先复测：${firstReadyDocument.title}` : "文档完成索引后才能启用前复测。",
      tone: publishedDocumentCount > 0 ? "ready" : readyDraftCount > 0 ? "warning" : "waiting"
    },
    {
      key: "evaluation",
      label: "复测题库",
      value: latestEvaluationRun ? `命中 ${formatPercent(latestEvaluationRun.hit_rate)}` : "待运行题集",
      note: latestEvaluationRun
        ? `引用 ${formatPercent(latestEvaluationRun.citation_coverage)}，需复核 ${latestEvaluationRun.needs_review_cases} 题`
        : "用固定客户题库检查发布前后质量，不等同线上准确率。",
      tone: latestEvaluationRun ? (latestEvaluationRun.needs_review_cases > 0 ? "warning" : "ready") : "waiting"
    },
    {
      key: "report",
      label: "质量报告",
      value: latestCustomerReport
        ? `${latestCustomerReport.report_status_label || latestCustomerReport.report_status} · ${latestCustomerReport.report_confidence_score}`
        : "待生成报告",
      note: latestCustomerReport?.quality_conclusion || customerQualityReport.message || "报告会读取评测、知识和签收口径。",
      tone: latestCustomerReport?.report_status === "controlled_trial_ready" ? "ready" : latestCustomerReport ? "warning" : "waiting"
    },
    {
      key: "signoff",
      label: "客户确认",
      value: latestCustomerSignoff ? latestCustomerSignoff.signoff_status_label : `${customerQualityReportSignoffs.data?.total ?? 0} 条记录`,
      note: latestCustomerSignoff
        ? `${latestCustomerSignoff.signer_display_name} · ${latestCustomerSignoff.confirmation_method_label}`
        : "本地确认记录不是正式验收，合同或电子签另走线下流程。",
      tone: latestCustomerSignoff ? "ready" : "waiting"
    }
  ];

  function applyCustomerKnowledgeIntakePackage() {
    const hasAnyItem = Object.values(customerKnowledgeIntakeCounts).some((count) => count > 0);
    if (!hasAnyItem) {
      onUpdatePackageDraftChange({
        ...updatePackageDraft,
        result: null,
        status: "error",
        message: "客户资料模板没有可转换的业务对象、问答、文档或回归题，请先补充内容。"
      });
      return;
    }
    onUpdatePackageDraftChange({
      ...updatePackageDraft,
      text: JSON.stringify(customerKnowledgeIntakePackage, null, 2),
      result: null,
      status: "ready",
      message: "已生成知识资料包，请继续点击“检查资料包”确认新增、跳过和错误项。"
    });
  }

  return (
    <section className="panel knowledge-panel" id="workspace-knowledge" aria-label="知识库运营" data-knowledge-primary="library">
      <div className="panel-heading">
        <div>
          <h2>知识库运营</h2>
          <p>维护业务对象、标准问答、文档草稿和引用来源，让客服回复能从可追溯知识里生成。</p>
        </div>
        <div className="panel-actions">
          <button type="button" className="ghost-action" onClick={onRefresh} disabled={!hasToken || isLoading}>
            <RefreshCw size={17} />
            {isLoading ? "刷新中" : "刷新"}
          </button>
        </div>
      </div>

      <div className="panel-state-row" aria-label="知识文档数据状态">
        <DataSourceBadge
          mode={hasToken ? "real" : "demo"}
          label={hasToken ? REAL_DATA_LABEL : PREVIEW_DATA_LABEL}
          detail={hasToken ? "读取租户知识文档与发布记录" : "登录后读取租户知识数据"}
        />
        <DataSourceBadge
          mode="local"
          label="本地检索口径"
          detail="当前为确定性本地检索占位，生产向量库仍需专项验收"
        />
      </div>

      <PanelStateNotice status={state.status} message={state.message} loadingMessage="正在读取知识文档、片段和发布记录。" />

      <section className="customer-knowledge-intake-card" data-ai-workbench-template-import="true">
        <div className="knowledge-section-title">
          <Upload size={18} />
          <strong>表格资料导入与发布</strong>
        </div>
        <div className="customer-intake-grid">
          <article>
            <span>AI 服务</span>
            <strong>{aiServiceStatus.data?.label ?? (aiServiceStatus.status === "loading" ? "读取中" : "未读取")}</strong>
            <small>{aiServiceStatus.data?.customer_visible_detail ?? aiServiceStatus.message}</small>
          </article>
          <article>
            <span>表格行</span>
            <strong>{templateImportRows.length} 行</strong>
            <small>导入后先成为草稿批次，发布前不会进入 AI 自动回复。</small>
          </article>
          <article>
            <span>预检结果</span>
            <strong>{templateImportDraft.precheck ? `${templateImportDraft.precheck.valid_count}/${templateImportDraft.precheck.row_count}` : "待预检"}</strong>
            <small>{templateImportDraft.precheck ? `错误 ${templateImportDraft.precheck.error_count} · 警告 ${templateImportDraft.precheck.warning_count}` : "检查必填、重复、风险等级和状态。"}</small>
          </article>
          <article>
            <span>发布版本</span>
            <strong>{templateImportDraft.publication ? `v${templateImportDraft.publication.version}` : "未发布"}</strong>
            <small>{templateImportDraft.importBatch ? `草稿批次 #${templateImportDraft.importBatch.id}` : "发布后 AI 才引用 active 标准问答。"}</small>
          </article>
        </div>
        <label className="field">
          <span>表格内容</span>
          <textarea
            value={templateImportDraft.text}
            onChange={(event) =>
              onTemplateImportDraftChange({
                ...templateImportDraft,
                text: event.target.value,
                status: "idle",
                message: "表格已修改，请重新预检。",
                precheck: null,
                importBatch: null,
                sampleRun: null,
                publication: null
              })
            }
            rows={7}
            spellCheck={false}
            disabled={!hasToken || templateImportDraft.status === "loading"}
          />
        </label>
        <div className="knowledge-form-grid">
          <label>
            <span>来源标识</span>
            <input
              value={templateImportDraft.sourceFileRef}
              onChange={(event) => onTemplateImportDraftChange({ ...templateImportDraft, sourceFileRef: event.target.value })}
              disabled={!hasToken || templateImportDraft.status === "loading"}
            />
          </label>
        </div>
        <div className="customer-knowledge-release-actions">
          <button type="button" className="secondary-action" onClick={onPrecheckTemplateImport} disabled={!hasToken || !canImport || templateImportDraft.status === "loading"}>
            <Search size={16} />
            预检表格
          </button>
          <button type="button" className="secondary-action" onClick={onCreateTemplateImport} disabled={!hasToken || !canImport || templateImportDraft.status === "loading"}>
            <Upload size={16} />
            导入草稿
          </button>
          <button type="button" className="secondary-action" onClick={onRunTemplateSample} disabled={!hasToken || !canImport || templateImportDraft.status === "loading" || !templateImportDraft.importBatch}>
            <Search size={16} />
            样题试跑
          </button>
          <button type="button" className="primary-action" onClick={onPublishTemplateImport} disabled={!hasToken || !canImport || templateImportDraft.status === "loading" || !templateImportDraft.importBatch}>
            <CheckCircle2 size={16} />
            发布给 AI
          </button>
        </div>
        <PanelStateNotice status={templateImportDraft.status} message={templateImportDraft.message} loadingMessage="正在处理表格资料。" />
        {templateImportDraft.sampleRun ? (
          <div className="knowledge-result-note">
            试跑：命中 {templateImportDraft.sampleRun.hit_cases} · 低置信 {templateImportDraft.sampleRun.low_confidence_cases} · 风险阻断 {templateImportDraft.sampleRun.blocked_cases}
          </div>
        ) : null}
      </section>

      <section
        className="customer-knowledge-center"
        data-h2w2-knowledge-center="true"
        data-h2w3b-customer-knowledge-flow="true"
        data-h2w-kb3-knowledge-center="true"
      >
        <div className="customer-knowledge-center-head">
          <div>
            <span>客户知识中心</span>
            <strong>按四层资料维护客服知识</strong>
          </div>
          <small>先整理业务对象、标准问答、流程政策、禁用承诺与转人工规则；启用前先复测，不会触发外部平台发送。</small>
        </div>
        <div className="customer-knowledge-layer-grid">
          <article data-h2w2-layer="business-object" data-h2w3b-step="business-object">
            <span>第一步</span>
            <strong>业务对象</strong>
            <p>商品、服务、套餐、课程和门店先建对象，再补别名，让系统知道客户在问哪一类业务。</p>
            <em>{state.businessObjects.length} 个对象</em>
          </article>
          <article data-h2w2-layer="standard-qa" data-h2w3b-step="standard-qa">
            <span>第二步</span>
            <strong>标准问答</strong>
            <p>把常见问法、标准答案和触发关键词绑定到对象上，高置信问题才进入可用回复候选。</p>
            <em>{objectCardTotal} 张问答卡</em>
          </article>
          <article data-h2w2-layer="process-policy" data-h2w3b-step="process-policy">
            <span>第三步</span>
            <strong>流程政策</strong>
            <p>售后、发票、退款、质保和服务流程用文档或更新包导入，发布前先做差异预检和样题试跑。</p>
            <em>{policyDocuments.length} 份政策文档</em>
          </article>
          <article data-h2w2-layer="risk-rules" data-h2w3b-step="risk-rules">
            <span>第四步</span>
            <strong>禁用承诺与转人工规则</strong>
            <p>风险词会进入自动回复策略；客户消息命中后转人工或阻断，避免承诺赔付、绕平台或高风险话术。</p>
            <em>{replyPolicyRuleCount || ruleDocuments.length} 条规则</em>
          </article>
        </div>
      </section>

      <section className="customer-knowledge-publish-flow" data-h2w2-publish-flow="true" data-h2w3b-enable-flow="true">
        <div className="knowledge-section-title">
          <CheckCircle2 size={18} />
          <strong>启用与回归检查</strong>
        </div>
        <div className="customer-knowledge-publish-grid">
          <article data-h2w2-publish-step="select-policy">
            <span>选择待启用文档</span>
            <strong>{readyDraftCount} 份可试跑</strong>
            <small>完成索引的文档才能进入样题试跑；没有来源、没有片段或没有题库会被阻断。</small>
          </article>
          <article data-h2w2-publish-step="precheck-samples">
            <span>回归题检查</span>
            <strong>{passedPrecheckCount} 次通过</strong>
            <small>检查命中、引用、期望词和转人工规则；这是发布门禁，不是完整客服准确率。</small>
          </article>
          <article data-h2w2-publish-step="version-record">
            <span>版本记录</span>
            <strong>{publishedDocumentCount} 份启用</strong>
            <small>发布后写入版本、发布人、门禁结果和回滚记录；回滚只暂停 active 检索。</small>
          </article>
          <article data-h2w2-publish-boundary="no-external-write">
            <span>安全边界</span>
            <strong>{blockedPublicationCount} 条阻断</strong>
            <small>知识发布只影响本地检索库，不会触发网站、微信客服、企业微信、公众号或小程序真实外发。</small>
          </article>
        </div>
      </section>

      <section className="customer-knowledge-release-card" data-h2w11d-customer-publish-path="true">
        <div className="customer-knowledge-release-head">
          <div>
            <span>知识维护总流程</span>
            <strong>导入资料 → 预检 → 发布 → 复测 → 确认 → 质量报告</strong>
          </div>
          <small>
            这里会更新本地知识库、评测记录和质量报告；真实外发继续关闭。客户确认记录不是正式验收，正式渠道发送必须另走授权和白名单。
          </small>
        </div>
        <div className="customer-knowledge-release-steps" aria-label="知识维护总流程状态">
          {customerPublishStepState.map((step, index) => (
            <article key={step.key} className={`release-step release-step-${step.tone}`}>
              <span>{String(index + 1).padStart(2, "0")} · {step.label}</span>
              <strong>{step.value}</strong>
              <small>{step.note}</small>
            </article>
          ))}
        </div>
        <div className="customer-knowledge-release-actions">
          <button
            type="button"
            className="secondary-action"
            data-h2w11d-action="convert-customer-intake"
            onClick={applyCustomerKnowledgeIntakePackage}
            disabled={!hasToken || updatePackageIsLoading}
          >
            <Upload size={16} />
            生成资料包
          </button>
          <button
            type="button"
            className="secondary-action"
            data-h2w11d-action="preview-update-package"
            onClick={onPreviewUpdatePackage}
            disabled={!hasToken || !canImport || updatePackageIsLoading}
          >
            <Search size={16} />
            检查资料包
          </button>
          <button
            type="button"
            className="primary-action"
            data-h2w11d-action="import-update-package"
            onClick={onImportUpdatePackage}
            disabled={!hasToken || !canImport || updatePackageIsLoading}
          >
            <Upload size={16} />
            导入知识库
          </button>
          <button
            type="button"
            className="secondary-action"
            data-h2w11d-action="publish-precheck-first-ready-document"
            onClick={() => {
              if (firstReadyDocument) {
                onCheckPublishDocument(firstReadyDocument);
              }
            }}
            disabled={!hasToken || !canImport || isLoading || !firstReadyDocument}
            title={firstReadyDocumentActionTitle}
            aria-label={firstReadyDocumentActionTitle}
          >
            <Search size={16} />
            启用前复测
          </button>
          <button
            type="button"
            className="primary-action"
            data-h2w11d-action="publish-first-ready-document"
            onClick={() => {
              if (firstReadyDocument) {
                onPublishDocument(firstReadyDocument);
              }
            }}
            disabled={!hasToken || !canImport || isLoading || !firstReadyDocument}
            title={firstReadyDocumentActionTitle}
            aria-label={firstReadyDocumentActionTitle}
          >
            <CheckCircle2 size={16} />
            启用知识
          </button>
          <a className="ghost-link" data-h2w11d-action="open-evaluation-page" href="#evals">
            查看复测题库
          </a>
          <a className="ghost-link" data-h2w11d-action="open-quality-report-page" href="#quality">
            查看质量报告
          </a>
        </div>
      </section>

      <section className="customer-knowledge-intake-card" data-h2w3c-customer-intake="true">
        <div className="knowledge-section-title">
          <Upload size={18} />
          <strong>客户资料整理</strong>
        </div>
        <p>
          先让客户按表格模板整理业务对象、标准问答、流程政策和风险规则；系统会生成知识资料包，再进入检查和导入流程。
          CSV 模板可直接转换为资料包；XLSX 模板用于客户填写，试跑 v1 先另存为 CSV 后导入。PDF、DOCX 原件只作为来源留档。
        </p>
        <div className="customer-intake-grid">
          <article>
            <span>CSV 模板</span>
            <strong>可直接转换</strong>
            <small>适合从 Excel 或表格软件另存为 CSV 后粘贴；转换后复用资料包检查。</small>
          </article>
          <article>
            <span>XLSX 模板</span>
            <strong>试跑入口</strong>
            <small>交付档案提供同列名模板；本地试跑 v1 先另存为 CSV 后导入。</small>
          </article>
          <article>
            <span>资料包草稿</span>
            <strong>真实检查 / 导入</strong>
            <small>转换结果会写入下方资料包内容，不会跳过检查直接入库。</small>
          </article>
          <article>
            <span>PDF / DOCX</span>
            <strong>先做来源留档</strong>
            <small>当前不承诺自动解析；需要先转成模板字段或由人工整理后导入。</small>
          </article>
          <article>
            <span>确认口径</span>
            <strong>导入不等于启用</strong>
            <small>完成检查、导入、复测和启用后，才能进入客户确认记录。</small>
          </article>
        </div>
        <label className="field">
          <span>客户资料 CSV</span>
          <textarea
            data-h2w3c-customer-intake-field="csv"
            value={customerKnowledgeIntakeText}
            onChange={(event) => setCustomerKnowledgeIntakeText(event.target.value)}
            rows={7}
          />
        </label>
        <div className="customer-intake-actions">
          <button
            type="button"
            className="secondary-action"
            data-h2w3c-action="download-customer-intake-csv"
            onClick={() =>
              downloadTextFile(
                customerKnowledgeIntakeText,
                "万法常世_客户知识资料导入模板.csv",
                "text/csv;charset=utf-8"
              )
            }
          >
            <FileText size={16} />
            下载 CSV 模板
          </button>
          <button
            type="button"
            className="primary-action"
            data-h2w3c-action="convert-customer-intake"
            onClick={applyCustomerKnowledgeIntakePackage}
          >
            <Upload size={16} />
            生成资料包
          </button>
          <span>
            将生成 {customerKnowledgeIntakeCounts.businessObjects} 个对象、{customerKnowledgeIntakeCounts.objectCards} 张问答卡、
            {customerKnowledgeIntakeCounts.documents} 份文档、{customerKnowledgeIntakeCounts.cases} 道回归题。
          </span>
        </div>
      </section>

      <section className="reply-policy-editor-card" data-h2w2-reply-policy-editor="true">
        <div className="knowledge-section-title">
          <ShieldCheck size={18} />
          <strong>自动回复策略</strong>
        </div>
        <p>
          这里维护的词会写入本地自动回复策略。命中禁止承诺词时不自动回复；命中转人工词时进入人工接待。
        </p>
        <div className="field-grid two-cols">
          <label className="field">
            <span>禁止承诺词</span>
            <textarea
              data-h2w2-field="blocked-policy-terms"
              value={replyStrategyDraft.blockedPolicyTerms}
              onChange={(event) =>
                onReplyStrategyDraftChange({
                  ...replyStrategyDraft,
                  blockedPolicyTerms: event.target.value
                })
              }
              placeholder="私下转账，绕过平台，保证收益，无条件退款"
              rows={4}
              disabled={!hasToken || replyStrategyState.status === "loading"}
            />
          </label>
          <label className="field">
            <span>转人工词</span>
            <textarea
              data-h2w2-field="manual-review-terms"
              value={replyStrategyDraft.manualReviewTerms}
              onChange={(event) =>
                onReplyStrategyDraftChange({
                  ...replyStrategyDraft,
                  manualReviewTerms: event.target.value
                })
              }
              placeholder="投诉，起诉，赔偿，举报，差评，封号"
              rows={4}
              disabled={!hasToken || replyStrategyState.status === "loading"}
            />
          </label>
        </div>
        <label className="reply-policy-toggle">
          <input
            type="checkbox"
            checked={replyStrategyDraft.forceDraftOnly}
            onChange={(event) =>
              onReplyStrategyDraftChange({
                ...replyStrategyDraft,
                forceDraftOnly: event.target.checked
              })
            }
            disabled={!hasToken || replyStrategyState.status === "loading"}
          />
          <span>暂时只生成回复草稿，不自动发送</span>
        </label>
        <div className="reply-policy-save-row">
          <button
            type="button"
            className="secondary-action"
            data-h2w2-action="save-reply-strategy"
            onClick={onSaveReplyStrategy}
            disabled={!hasToken || !canImport || replyStrategyState.status === "loading"}
          >
            <CheckCircle2 size={16} />
            保存自动回复策略
          </button>
          <span>
            {replyStrategyState.status === "ready" && replyStrategyState.data
              ? `当前版本：${replyStrategyState.data.strategy_version || "本地策略"}`
              : replyStrategyState.message}
          </span>
        </div>
        <DisabledReason show={Boolean(replyStrategyDisabledReason)} reason={replyStrategyDisabledReason} />
        {replyStrategyState.message ? (
          <PanelStateNotice
            status={replyStrategyState.status === "idle" ? "ready" : replyStrategyState.status}
            message={replyStrategyState.message}
            compact
          />
        ) : null}
      </section>

      <section className="knowledge-update-package-card" data-knowledge-update-package="p3-06u-26h2d">
        <div className="knowledge-section-title">
          <Upload size={18} />
          <strong>知识资料包导入</strong>
        </div>
        <p>
          用于导入新增业务对象、标准问答、政策文档和回归题。先检查资料包，确认新增、跳过和错误项后再导入；导入过程不会触发外部平台发送。
        </p>
        <label className="field">
          <span>资料包内容</span>
          <textarea
            data-knowledge-update-package-field="json"
            value={updatePackageDraft.text}
            onChange={(event) =>
              onUpdatePackageDraftChange({
                ...updatePackageDraft,
                text: event.target.value,
                status: "idle",
                message: "已修改，请重新检查资料包"
              })
            }
            rows={12}
            disabled={!hasToken || updatePackageIsLoading}
          />
        </label>
        <div className="knowledge-update-package-actions">
          <button
            type="button"
            className="secondary-action"
            onClick={onPreviewUpdatePackage}
            disabled={!hasToken || !canImport || updatePackageIsLoading}
          >
            <Search size={16} />
            检查资料包
          </button>
          <button
            type="button"
            className="primary-action"
            onClick={onImportUpdatePackage}
            disabled={!hasToken || !canImport || updatePackageIsLoading}
          >
            <Upload size={16} />
            导入资料包
          </button>
        </div>
        <DisabledReason show={Boolean(updatePackageDisabledReason)} reason={updatePackageDisabledReason} />
        {updatePackageDraft.message ? (
          <PanelStateNotice
            status={updatePackageDraft.status === "idle" ? "ready" : updatePackageDraft.status}
            message={updatePackageDraft.message}
            compact
          />
        ) : null}
        {updatePackageResult ? (
          <div className="knowledge-update-package-result" data-knowledge-update-package-result="diff">
            <div className="knowledge-update-package-summary">
              <article>
                <span>新增</span>
                <strong>{updatePackageResult.operation_counts.create ?? 0}</strong>
              </article>
              <article>
                <span>跳过</span>
                <strong>{updatePackageResult.operation_counts.skip ?? 0}</strong>
              </article>
              <article>
                <span>错误</span>
                <strong>{updatePackageResult.operation_counts.error ?? 0}</strong>
              </article>
              <article>
                <span>导入批次</span>
                <strong>{updatePackageResult.import_batch_id ? `#${updatePackageResult.import_batch_id}` : "预检"}</strong>
              </article>
            </div>
            <div className="knowledge-update-package-meta">
              <span>{updatePackageResult.package_name}</span>
              <span>{updatePackageResult.schema_version}</span>
              <span>{updatePackageResult.dry_run ? "仅预检" : "已导入"}</span>
              <span>{updatePackageResult.can_apply ? "可应用" : "需修正"}</span>
            </div>
            {updatePackageResult.operations.length > 0 ? (
              <div className="knowledge-update-package-ops">
                {updatePackageResult.operations.slice(0, 8).map((operation, index) => (
                  <article key={`${operation.resource_type}-${operation.title}-${index}`} className={`op-${operation.action}`}>
                    <span>{formatKnowledgeUpdateResourceType(operation.resource_type)}</span>
                    <strong>{operation.title}</strong>
                    <small>{formatKnowledgeUpdateAction(operation.action)} · {operation.reason}</small>
                  </article>
                ))}
              </div>
            ) : null}
            {updatePackageResult.warnings.length > 0 ? (
              <div className="knowledge-update-package-warnings">
                {updatePackageResult.warnings.map((warning) => (
                  <span key={warning}>{warning}</span>
                ))}
              </div>
            ) : null}
          </div>
        ) : null}
      </section>

      <div className="business-knowledge-layout">
        <form
          className="business-object-form"
          onSubmit={(event) => {
            event.preventDefault();
            onCreateBusinessObject();
          }}
        >
          <div className="knowledge-section-title">
            <Bot size={18} />
            <strong>{businessObjectDraft.editingId ? "编辑业务对象" : "业务对象知识库"}</strong>
          </div>
          <p className="form-hint">先维护商品、服务或套餐，再为每个对象挂标准问答；客服回复、质检复盘和知识缺口都会回到对象层。</p>
          <div className="field-grid two-cols">
            <label className="field">
              <span>对象类型</span>
              <select
                value={businessObjectDraft.type}
                onChange={(event) =>
                  onBusinessObjectDraftChange({
                    ...businessObjectDraft,
                    type: event.target.value as BusinessObjectType
                  })
                }
                disabled={!hasToken || isLoading}
              >
                {businessObjectOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>
            <label className="field">
              <span>对象名称</span>
              <input
                data-knowledge-field="business-object-title"
                value={businessObjectDraft.title}
                onChange={(event) => onBusinessObjectDraftChange({ ...businessObjectDraft, title: event.target.value })}
                placeholder="例如：AI 客服入门验证包"
                disabled={!hasToken || isLoading}
              />
            </label>
          </div>
          <label className="field">
            <span>别名 / 触发说法</span>
            <input
              data-knowledge-field="business-object-aliases"
              value={businessObjectDraft.aliases}
              onChange={(event) => onBusinessObjectDraftChange({ ...businessObjectDraft, aliases: event.target.value })}
              placeholder="入门版，Lite A，官网客服试点"
              disabled={!hasToken || isLoading}
            />
          </label>
          <label className="field">
            <span>对象说明</span>
            <textarea
              data-knowledge-field="business-object-summary"
              value={businessObjectDraft.summary}
              onChange={(event) => onBusinessObjectDraftChange({ ...businessObjectDraft, summary: event.target.value })}
              placeholder="适用客户、交付边界、禁止承诺、推荐话术"
              rows={4}
              disabled={!hasToken || isLoading}
            />
          </label>
          <button type="submit" className="primary-action" data-knowledge-action="create-business-object" disabled={!hasToken || !canImport || isLoading}>
            <BookOpen size={17} />
            {businessObjectDraft.editingId ? "更新业务对象" : "新增业务对象"}
          </button>
          {businessObjectDraft.editingId ? (
            <button
              type="button"
              className="secondary-action"
              data-knowledge-action="cancel-edit-business-object"
              onClick={() => onBusinessObjectDraftChange({ editingId: null, type: "product", title: "", aliases: "", summary: "" })}
            >
              取消编辑
            </button>
          ) : null}
          <DisabledReason show={Boolean(businessObjectDisabledReason)} reason={businessObjectDisabledReason} />
        </form>

        <div className="business-object-board">
          <div className="knowledge-section-title">
            <FileText size={18} />
            <strong>对象问答卡</strong>
          </div>
          {state.businessObjects.length === 0 ? (
            <WorkspaceStateNotice
              kind={hasToken ? "empty" : "demo"}
              title="暂无业务对象"
              message="先创建商品、服务或套餐对象，再补充对应的标准问答。"
              compact
            />
          ) : (
            <div className="business-object-grid" data-business-object-knowledge="object-list">
              {state.businessObjects.slice(0, 8).map((item) => {
                const cards = state.objectCardsByObject[item.id] ?? [];
                const selected = item.id === selectedBusinessObjectId;
                return (
                  <button
                    key={item.id}
                    type="button"
                    className={`business-object-card ${selected ? "selected" : ""}`}
                    onClick={() =>
                      onObjectKnowledgeCardDraftChange({
                        ...objectKnowledgeCardDraft,
                        businessObjectId: item.id
                      })
                    }
                  >
                    <span>{formatBusinessObjectType(item.type)}</span>
                    <strong>{item.title}</strong>
                    <small>{item.aliases.length > 0 ? item.aliases.slice(0, 3).join(" / ") : "未配置别名"}</small>
                    <em>{cards.length || item.knowledge_card_count} 张问答卡</em>
                  </button>
                );
              })}
            </div>
          )}
          {selectedBusinessObject ? (
            <div className="business-object-edit-row">
              <button
                type="button"
                className="secondary-action"
                data-knowledge-action="edit-business-object"
                onClick={() =>
                  onBusinessObjectDraftChange({
                    editingId: selectedBusinessObject.id,
                    type: selectedBusinessObject.type,
                    title: selectedBusinessObject.title,
                    aliases: selectedBusinessObject.aliases.join("，"),
                    summary: selectedBusinessObject.summary
                  })
                }
              >
                编辑业务对象
              </button>
            </div>
          ) : null}

          <form
            className="object-knowledge-form"
            onSubmit={(event) => {
              event.preventDefault();
              onCreateObjectKnowledgeCard();
            }}
          >
            <label className="field">
              <span>所属对象</span>
              <select
                value={selectedBusinessObjectId ?? ""}
                onChange={(event) =>
                  onObjectKnowledgeCardDraftChange({
                    ...objectKnowledgeCardDraft,
                    businessObjectId: event.target.value ? Number(event.target.value) : null
                  })
                }
                disabled={!hasToken || isLoading || state.businessObjects.length === 0}
              >
                {state.businessObjects.map((item) => (
                  <option key={item.id} value={item.id}>
                    {formatBusinessObjectType(item.type)} · {item.title}
                  </option>
                ))}
              </select>
            </label>
            <label className="field">
              <span>客户会怎么问</span>
              <input
                data-knowledge-field="object-card-question"
                value={objectKnowledgeCardDraft.question}
                onChange={(event) =>
                  onObjectKnowledgeCardDraftChange({ ...objectKnowledgeCardDraft, question: event.target.value })
                }
                placeholder="例如：入门验证包适合什么客户？"
                disabled={!hasToken || isLoading}
              />
            </label>
            <label className="field">
              <span>标准答案</span>
              <textarea
                data-knowledge-field="object-card-answer"
                value={objectKnowledgeCardDraft.answer}
                onChange={(event) =>
                  onObjectKnowledgeCardDraftChange({ ...objectKnowledgeCardDraft, answer: event.target.value })
                }
                placeholder="直接可用于客服回复的答案，同时写清楚不能承诺的部分。"
                rows={4}
                disabled={!hasToken || isLoading}
              />
            </label>
            <label className="field">
              <span>触发关键词</span>
              <input
                data-knowledge-field="object-card-keywords"
                value={objectKnowledgeCardDraft.triggerKeywords}
                onChange={(event) =>
                  onObjectKnowledgeCardDraftChange({
                    ...objectKnowledgeCardDraft,
                    triggerKeywords: event.target.value
                  })
                }
                placeholder="试点，入门，官网客服"
                disabled={!hasToken || isLoading}
              />
            </label>
            <button
              type="submit"
              className="secondary-action"
              data-knowledge-action="create-object-card"
              disabled={!hasToken || !canImport || isLoading || state.businessObjects.length === 0}
            >
              绑定问答卡
            </button>
            <DisabledReason
              show={Boolean(objectCardDisabledReason) || state.businessObjects.length === 0}
              reason={state.businessObjects.length === 0 ? "请先新增一个业务对象，再绑定标准问答卡。" : objectCardDisabledReason}
            />
            {selectedBusinessObject ? (
              <div className="object-knowledge-list">
                {(state.objectCardsByObject[selectedBusinessObject.id] ?? []).slice(0, 3).map((card) => (
                  <article key={card.id}>
                    <strong>{card.question}</strong>
                    <p>{card.answer}</p>
                    <small>{card.trigger_keywords.length > 0 ? card.trigger_keywords.join(" / ") : "未配置关键词"}</small>
                  </article>
                ))}
              </div>
            ) : null}
          </form>
        </div>
      </div>

      <section className="reply-decision-state-card" aria-label="自动回复处理方式" data-reply-decision-state-machine="p3-06u-20">
        <div className="knowledge-section-title">
          <ShieldCheck size={18} />
          <strong>自动回复处理方式</strong>
        </div>
        <p>
          客户消息会先命中业务对象，再匹配对象问答卡；高置信问题生成回复草稿，风险、低置信和未覆盖问题会进入转人工或知识缺口。
          真实发送动作由渠道授权、白名单和转人工策略共同控制。
        </p>
        <div className="reply-decision-flow">
          <article>
            <span>1</span>
            <strong>业务对象</strong>
            <small>商品、服务、套餐和别名先被识别，避免只靠散乱 FAQ。</small>
          </article>
          <article>
            <span>2</span>
            <strong>对象问答卡</strong>
            <small>问题、触发关键词和标准答案共同决定置信度。</small>
          </article>
          <article>
            <span>3</span>
            <strong>风险门禁</strong>
            <small>投诉、赔付、法务或平台风险词会转人工或直接阻断。</small>
          </article>
          <article>
            <span>4</span>
            <strong>处理控制</strong>
            <small>符合策略的回复进入可用草稿；真实发送继续受渠道授权控制。</small>
          </article>
        </div>
        <div className="reply-decision-state-grid">
          <article className="state-ready">
            <span>可自动回复</span>
            <strong>高置信对象问答卡</strong>
            <small>生成可直接使用的回复，并记录命中来源。</small>
          </article>
          <article className="state-review">
            <span>转人工</span>
            <strong>低置信或风险词</strong>
            <small>进入坐席复核，保留草稿和原因。</small>
          </article>
          <article className="state-gap">
            <span>知识缺口</span>
            <strong>无对象或无可信卡</strong>
            <small>回到知识运营补对象、别名或问答卡。</small>
          </article>
          <article className="state-blocked">
            <span>策略阻断</span>
            <strong>平台/合规风险</strong>
            <small>不生成可用回复，保留复盘原因。</small>
          </article>
        </div>
      </section>

      <div className="knowledge-layout">
        <form
          className="knowledge-form"
          onSubmit={(event) => {
            event.preventDefault();
            onImportDocument();
          }}
        >
          <div className="knowledge-section-title">
            <Upload size={18} />
            <strong>导入知识文档</strong>
          </div>
          <div className="knowledge-edit-checklist" data-knowledge-ops-smoke="edit-checklist">
            <span>发布前必须写清</span>
            <ul>
              <li>适用问题</li>
              <li>标准答案</li>
              <li>禁止承诺</li>
              <li>引用来源</li>
              <li>生效范围</li>
              <li>版本和审核状态</li>
            </ul>
          </div>
          <label className="field">
            <span>文档标题</span>
            <input
              data-knowledge-field="document-title"
              value={draft.title}
              onChange={(event) => onDraftChange({ ...draft, title: event.target.value })}
              placeholder="例如：售后质保政策"
              disabled={!hasToken || isLoading}
            />
          </label>
          <label className="field">
            <span>来源链接</span>
            <input
              data-knowledge-field="document-source-uri"
              value={draft.sourceUri}
              onChange={(event) => onDraftChange({ ...draft, sourceUri: event.target.value })}
              placeholder="官网、手册、内部文档地址"
              disabled={!hasToken || isLoading}
            />
          </label>
          <label className="field">
            <span>标签</span>
            <input
              data-knowledge-field="document-tags"
              value={draft.tags}
              onChange={(event) => onDraftChange({ ...draft, tags: event.target.value })}
              placeholder="售后，质保，发票"
              disabled={!hasToken || isLoading}
            />
          </label>
          <label className="field">
            <span>正文</span>
            <textarea
              data-knowledge-field="document-raw-text"
              value={draft.rawText}
              onChange={(event) => onDraftChange({ ...draft, rawText: event.target.value })}
              placeholder={"适用问题：客户会怎么问？\n标准答案：可以直接引用的回答是什么？\n禁止承诺：哪些赔付、时效或结果不能承诺？\n引用来源：来自哪份官网、手册或内部政策？\n生效范围：适用于哪些渠道、产品和时间范围？"}
              disabled={!hasToken || isLoading}
              rows={8}
            />
          </label>
          <button type="submit" className="primary-action" data-knowledge-action="import-document" disabled={!hasToken || !canImport || isLoading}>
            <FileText size={17} />
            {canImport ? "导入知识文档" : "仅管理员可导入"}
          </button>
          <DisabledReason show={Boolean(importDisabledReason)} reason={importDisabledReason} />
        </form>

        <div className="knowledge-document-list">
          <div className="knowledge-section-title">
            <BookOpen size={18} />
            <strong>已索引文档</strong>
          </div>
          {state.documents.length === 0 && state.status === "ready" ? (
            <WorkspaceStateNotice
              kind="empty"
              title="暂无数据"
              message="暂无 active 知识文档。导入、审核并发布后，文档才会进入客服检索链路。"
              compact
            />
          ) : null}
          <ListToolbar
            view={listView}
            total={state.documents.length}
            filteredTotal={pagedDocuments.total}
            statusOptions={[
              { label: "全部", value: "all" },
              { label: "已启用", value: "active" },
              { label: "草稿", value: "draft" },
              { label: "已归档", value: "archived" },
              { label: "已索引", value: "indexed" },
              { label: "处理中", value: "processing" }
            ]}
            searchPlaceholder="搜索文档标题、来源、标签"
            onChange={onListViewChange}
          />
          {pagedDocuments.items.map((document) => {
            const chunks = state.chunksByDocument[document.id] ?? [];
            const publications = state.publicationsByDocument[document.id] ?? [];
            const latestPublication = publications[0] ?? null;
            const hasPublishedRecord = publications.some((publication) => publication.status === "published");
            const latestCaseResults = latestPublication?.case_results ?? [];
            return (
              <article key={document.id} className="knowledge-document-row">
                <div className="knowledge-document-head">
                  <div>
                    <strong>{document.title}</strong>
                    <span>{document.status} · {document.ingestion_status} · {document.chunk_count} 个片段</span>
                  </div>
                  <small>{formatTags(document.tags)}</small>
                </div>
                <p className="citation-line">
                  引用来源：{document.source_uri || "未填写来源"} · hash {document.content_hash.slice(0, 10)}
                </p>
                <div className="publication-card">
                  {latestPublication ? (
                    <>
                      <div className="publication-card-head">
                        <div>
                          <span>最新发布记录</span>
                          <strong>
                            {formatPublicationType(latestPublication.publication_type)} ·{" "}
                            {formatPublicationStatus(latestPublication.status)}
                          </strong>
                        </div>
                        <small>
                          #{latestPublication.id} · {formatDateTime(latestPublication.created_at)}
                        </small>
                      </div>
                      <div className="publication-grid">
                        <div>
                          <span>状态流转</span>
                          <strong>
                            {latestPublication.from_status || "-"} → {latestPublication.to_status || "-"}
                          </strong>
                        </div>
                        <div>
                          <span>回归运行</span>
                          <strong>
                            {latestPublication.evaluation_run_id
                              ? `#${latestPublication.evaluation_run_id}`
                              : "未运行"}
                          </strong>
                        </div>
                        <div>
                          <span>阻断项</span>
                          <strong>
                            {latestPublication.blocking_reasons.length > 0
                              ? latestPublication.blocking_reasons.slice(0, 2).join(" / ")
                              : "无"}
                          </strong>
                        </div>
                      </div>
                      {latestCaseResults.length > 0 ? (
                        <div className="publication-case-list">
                          {latestCaseResults.slice(0, 3).map((item, index) => (
                            <span key={`${latestPublication.id}-${index}`}>
                              题 {publicationCaseValue(item, "evaluation_case_id")}：
                              {publicationCaseValue(item, "status")}
                              {publicationCaseValue(item, "blocking") === "true" ? " · 阻断" : ""}
                            </span>
                          ))}
                        </div>
                      ) : (
                        <p className="publication-empty">本次记录没有逐题门禁结果。</p>
                      )}
                      <div className="publication-actions">
                        <button
                          type="button"
                          className="ghost-action danger-action"
                          disabled={!hasToken || !canImport || isLoading || !hasPublishedRecord || document.status !== "active"}
                          title={
                            !hasToken
                              ? "请先登录本地账号后再回滚知识。"
                              : !canImport
                                ? "当前账号没有知识库管理权限。"
                                : isLoading
                                  ? "正在同步知识库数据，请稍候。"
                                  : !hasPublishedRecord
                                    ? "该文档尚无发布记录，不能回滚。"
                                    : document.status !== "active"
                                      ? "只有已启用的知识文档才能回滚为草稿。"
                                      : "回滚为草稿只暂停本地检索，不会恢复旧正文。"
                          }
                          aria-label="回滚为草稿：只暂停本地检索，不恢复旧正文"
                          onClick={() => onRollbackDocument(document)}
                        >
                          <RefreshCw size={16} />
                          回滚为草稿
                        </button>
                        <span>
                          回滚只暂停 active 检索，不恢复旧正文；完整版本 diff 属于下一阶段。
                        </span>
                      </div>
                    </>
                  ) : (
                    <p className="publication-empty">尚无发布门禁记录；草稿发布前会自动生成审计记录。</p>
                  )}
                </div>
                <div className="knowledge-document-publish-actions" data-h2w2-document-publish-actions="true">
                  <button
                    type="button"
                    className="secondary-action"
                    data-h2w2-action="publish-precheck"
                    disabled={!hasToken || !canImport || isLoading || document.ingestion_status !== "indexed"}
                    onClick={() => onCheckPublishDocument(document)}
                    title={document.ingestion_status !== "indexed" ? "文档完成索引后才能试跑样题" : "调用发布前门禁并写入检查记录"}
                  >
                    <Search size={16} />
                    发布前样题试跑
                  </button>
                  <button
                    type="button"
                    className="primary-action"
                    data-h2w2-action="publish-document"
                    disabled={!hasToken || !canImport || isLoading || document.status !== "draft" || document.ingestion_status !== "indexed"}
                    onClick={() => onPublishDocument(document)}
                    title={document.status === "active" ? "这份知识已经启用" : "发布通过后进入本地 active 检索范围"}
                  >
                    <CheckCircle2 size={16} />
                    {document.status === "active" ? "已启用" : "确认发布版本"}
                  </button>
                  <span>发布只更新本地知识库和版本记录；真实渠道外发继续关闭。</span>
                </div>
                {chunks.slice(0, 2).map((chunk) => (
                  <p key={chunk.id} className="knowledge-chunk-preview">
                    片段 {chunk.chunk_index}：{chunk.content.slice(0, 120)}
                    {chunk.content.length > 120 ? "..." : ""}
                  </p>
                ))}
              </article>
            );
          })}
          <PaginationControls result={pagedDocuments} view={listView} onChange={onListViewChange} />
        </div>
      </div>

      <div className="knowledge-search">
        <div className="knowledge-section-title">
          <Search size={18} />
          <strong>文档片段检索</strong>
        </div>
        <div className="knowledge-search-controls">
          <input
            value={searchQuery}
            onChange={(event) => onSearchQueryChange(event.target.value)}
            placeholder="输入客户问题，检查召回片段和引用来源"
            disabled={!hasToken || isLoading}
          />
          <button type="button" className="primary-action" onClick={onSearchDocuments} disabled={!hasToken || isLoading}>
            <Search size={17} />
            检索
          </button>
        </div>
        <DisabledReason show={Boolean(searchDisabledReason)} reason={searchDisabledReason} />

        {searchResult ? (
          <div className="knowledge-search-results">
            <div className="retrieval-summary">
              <span>{searchResult.retrieval_mode}</span>
              <span>{searchResult.vector_engine}</span>
              <span>候选 {searchResult.total_candidates}</span>
            </div>
            {searchResult.matches.length === 0 ? (
              <WorkspaceStateNotice
                kind="empty"
                message="没有命中文档片段，应进入知识缺口复盘，补充标准答案、适用问题和引用来源。"
                compact
              />
            ) : null}
            {searchResult.matches.map((match) => (
              <article key={`${match.document_id}-${match.chunk_id}`} className="knowledge-search-row">
                <div className="knowledge-document-head">
                  <div>
                    <strong>{match.document_title}</strong>
                    <span>
                      片段 {match.chunk_index} · 置信度 {formatPercent(match.confidence)} · 综合分{" "}
                      {match.score.toFixed(2)}
                    </span>
                  </div>
                  <small>BM25 {match.bm25_score.toFixed(2)} · 向量占位 {match.vector_score.toFixed(2)}</small>
                </div>
                <p>{match.content_preview}</p>
                <p className="citation-line">引用来源：{formatCitation(match.citation)}</p>
                {match.matched_terms.length > 0 ? (
                  <div className="evidence-strip">
                    {match.matched_terms.slice(0, 8).map((term) => (
                      <span key={term}>{term}</span>
                    ))}
                  </div>
                ) : null}
              </article>
            ))}
          </div>
        ) : (
          <WorkspaceStateNotice
            kind={hasToken ? "info" : "demo"}
            title={hasToken ? "状态说明" : PREVIEW_DATA_LABEL}
            message="尚未运行文档检索；当前引擎是 deterministic_local_hash_embedding_v1 + lexical_overlap_reranker_v1，不代表生产向量库。"
            compact
          />
        )}
      </div>
    </section>
  );
}

type KnowledgeGapActionStatus = "open" | "triaged" | "in_progress" | "resolved" | "rejected" | "archived";

function KnowledgeGapPanel({
  state,
  listView,
  hasToken,
  canManage,
  onListViewChange,
  onRefresh,
  onSync,
  onUpdate,
  onCreateDocumentDraft,
  onCreateRegressionCase,
  onPublishDocument
}: {
  state: KnowledgeGapState;
  listView: ListViewState;
  hasToken: boolean;
  canManage: boolean;
  onListViewChange: (view: ListViewState) => void;
  onRefresh: () => void;
  onSync: () => void;
  onUpdate: (gap: KnowledgeGap, statusValue: KnowledgeGapActionStatus) => void;
  onCreateDocumentDraft: (gap: KnowledgeGap) => void;
  onCreateRegressionCase: (gap: KnowledgeGap) => void;
  onPublishDocument: (gap: KnowledgeGap) => void;
}) {
  const isLoading = state.status === "loading";
  const syncDisabledReason = formatAccessDisabledReason({
    hasToken,
    canManage,
    isLoading,
    action: "同步知识缺口"
  });
  const pagedResult = pagedResultFromServer<KnowledgeGap>(state.data);
  const openItems = state.data.items.filter((gap) => ["open", "triaged", "in_progress"].includes(gap.status));
  const severeItems = state.data.items.filter((gap) => ["high", "critical"].includes(gap.severity));
  const humanReviewItems = state.data.items.filter((gap) => gap.source_type === "human_review");
  const evaluationItems = state.data.items.filter((gap) => gap.source_type === "evaluation_run");
  const gapBaseDisabledTitle = (action: string) => {
    if (!hasToken) return `${action}不可用：请先登录本地账号后读取知识缺口。`;
    if (!canManage) return `${action}不可用：当前账号没有知识运营权限。`;
    if (isLoading) return `${action}不可用：正在同步知识缺口。`;
    return "";
  };
  const gapActionTitle = (
    gap: KnowledgeGap,
    action: "draft" | "regression" | "publish" | "in_progress" | "resolved" | "rejected",
    regressionCaseId: string,
    publishedDocumentId: string
  ) => {
    const base = gapBaseDisabledTitle(
      action === "draft"
        ? "生成草稿"
        : action === "regression"
          ? "加入回归"
          : action === "publish"
            ? "发布知识"
            : action === "in_progress"
              ? "标记处理中"
              : action === "resolved"
                ? "标记已解决"
                : "不需补充"
    );
    if (base) return base;
    if (action === "draft") {
      return gap.linked_knowledge_document_id ? "该缺口已生成知识草稿，无需重复生成。" : "为该知识缺口生成本地知识草稿。";
    }
    if (action === "regression") {
      return regressionCaseId ? "该缺口已加入回归题库，无需重复加入。" : "把该缺口加入回归题库，后续用于复测。";
    }
    if (action === "publish") {
      if (publishedDocumentId) return "该缺口关联知识已发布，无需重复发布。";
      if (!gap.linked_knowledge_document_id) return "请先生成知识草稿，再发布知识。";
      if (!regressionCaseId) return "请先加入回归题库，再发布知识。";
      return "发布关联知识，并保留发布前门禁记录。";
    }
    if (action === "in_progress") {
      return gap.status === "in_progress" ? "该缺口已经是处理中状态。" : "把该缺口标记为处理中。";
    }
    if (action === "resolved") {
      return gap.status === "resolved" ? "该缺口已经标记为已解决。" : "确认知识已补齐并标记为已解决。";
    }
    return gap.status === "rejected" ? "该缺口已经标记为不需补充。" : "确认该缺口不需要补充知识。";
  };

  return (
    <section className="panel knowledge-gap-panel" id="workspace-knowledge-gaps" aria-label="知识缺口处理" data-knowledge-primary="gaps">
      <div className="panel-heading">
        <div>
          <h2>知识缺口处理</h2>
          <p>把无知识命中、低置信和评测失败变成可分派、可生成草稿、可加入回归的修复待办。</p>
        </div>
        <div className="panel-actions">
          <button type="button" className="ghost-action" onClick={onRefresh} disabled={!hasToken || isLoading}>
            <RefreshCw size={17} />
            {isLoading ? "刷新中" : "刷新"}
          </button>
          <button type="button" className="primary-action" onClick={onSync} disabled={!hasToken || !canManage || isLoading}>
            <Bot size={17} />
            {canManage ? "同步缺口" : "仅管理员可同步"}
          </button>
        </div>
      </div>

      <div className="panel-state-row" aria-label="知识缺口数据状态">
        <DataSourceBadge
          mode={hasToken ? "real" : "demo"}
          label={hasToken ? REAL_DATA_LABEL : PREVIEW_DATA_LABEL}
          detail={hasToken ? "读取人审、评测和知识缺口闭环" : "仅展示样例缺口处理流程"}
        />
        <DataSourceBadge
          mode="off"
          label={EXTERNAL_WRITE_OFF_LABEL}
          detail="缺口修复只影响内部知识发布和回归，不触发外部回复"
        />
      </div>

      <PanelStateNotice status={state.status} message={state.message} loadingMessage="正在读取知识缺口和修复状态。" />
      <DisabledReason show={Boolean(syncDisabledReason)} reason={syncDisabledReason} />

      <div className="gap-metric-grid">
        <QualityMetric label="当前缺口" value={`${state.data.total}`} note="当前筛选条件下的缺口总量" />
        <QualityMetric label="待处理" value={`${openItems.length}`} note="已加载页中的开放、分诊和处理中缺口" />
        <QualityMetric label="高严重度" value={`${severeItems.length}`} note="高风险、低置信或核心证据缺失" />
        <QualityMetric label="来源构成" value={`${humanReviewItems.length}/${evaluationItems.length}`} note="人审来源 / 评测来源" />
      </div>

      {state.lastSync ? (
        <div className="gap-sync-summary" aria-live="polite">
          <div>
            <span>最近同步</span>
            <strong>新增 {state.lastSync.created_count} 条</strong>
          </div>
          <small>
            已存在 {state.lastSync.existing_count} · 扫描来源 {state.lastSync.scanned_count} · 外部平台写入：否
          </small>
        </div>
      ) : null}

      <KnowledgeGapFilterToolbar
        view={listView}
        total={state.data.items.length}
        filteredTotal={pagedResult.total}
        onChange={onListViewChange}
      />

      {pagedResult.items.length === 0 && state.status === "ready" ? (
        <WorkspaceStateNotice
          kind="empty"
          message={listView.status === "open"
            ? "本时间窗口暂无对应任务，当前筛选条件下没有待处理知识缺口。"
            : "当前筛选条件下没有知识缺口。"}
          compact
        />
      ) : null}

      <div className="knowledge-gap-list">
        {pagedResult.items.map((gap) => {
          const regressionCaseId = knowledgeGapRegressionCaseId(gap);
          const publishedDocumentId = knowledgeGapPublishedDocumentId(gap);
          return (
          <article key={gap.id} className={`knowledge-gap-row severity-${gap.severity}`}>
            <div className="knowledge-gap-head">
              <div>
                <span className={`source-pill source-${gap.source_type}`}>{formatKnowledgeGapSource(gap.source_type)}</span>
                <strong>{gap.source_title || `知识缺口 #${gap.id}`}</strong>
              </div>
              <div className="gap-status-stack">
                <span>{formatKnowledgeGapStatus(gap.status)}</span>
                <small>{formatKnowledgeGapSeverity(gap.severity)}</small>
              </div>
            </div>

            <div className="knowledge-gap-body">
              <div>
                <span>客户问题</span>
                <p>{gap.question_excerpt || "没有问题摘录"}</p>
              </div>
              <div>
                <span>处理线索</span>
                <p>{gap.source_excerpt || gap.gap_type || "没有来源摘要"}</p>
              </div>
            </div>

            <div className="gap-evidence-strip">
              <span>{gap.gap_type || "unknown_gap"}</span>
              <span>{formatKnowledgeGapEvidence(gap)}</span>
              <span>{gap.expected_terms.length > 0 ? gap.expected_terms.join(" / ") : "未声明期望词"}</span>
              <span>{gap.assigned_user_id ? `负责人 #${gap.assigned_user_id}` : "未分派"}</span>
              <span>{gap.linked_knowledge_document_id ? `草稿文档 #${gap.linked_knowledge_document_id}` : "未生成草稿"}</span>
              <span>{regressionCaseId ? `回归题 #${regressionCaseId}` : "未入回归"}</span>
              <span>{publishedDocumentId ? `已发布 #${publishedDocumentId}` : "未发布"}</span>
            </div>

            <div className="gap-actions">
              <button
                type="button"
                className="ghost-action"
                disabled={!hasToken || !canManage || isLoading || Boolean(gap.linked_knowledge_document_id)}
                title={gapActionTitle(gap, "draft", regressionCaseId, publishedDocumentId)}
                aria-label={gapActionTitle(gap, "draft", regressionCaseId, publishedDocumentId)}
                onClick={() => onCreateDocumentDraft(gap)}
              >
                <FileText size={17} />
                {gap.linked_knowledge_document_id ? "已有草稿" : "生成草稿"}
              </button>
              <button
                type="button"
                className="ghost-action"
                disabled={!hasToken || !canManage || isLoading || Boolean(regressionCaseId)}
                title={gapActionTitle(gap, "regression", regressionCaseId, publishedDocumentId)}
                aria-label={gapActionTitle(gap, "regression", regressionCaseId, publishedDocumentId)}
                onClick={() => onCreateRegressionCase(gap)}
              >
                <BookOpen size={17} />
                {regressionCaseId ? "已入题库" : "加入回归"}
              </button>
              <button
                type="button"
                className="primary-action"
                disabled={
                  !hasToken ||
                  !canManage ||
                  isLoading ||
                  !gap.linked_knowledge_document_id ||
                  !regressionCaseId ||
                  Boolean(publishedDocumentId)
                }
                title={gapActionTitle(gap, "publish", regressionCaseId, publishedDocumentId)}
                aria-label={gapActionTitle(gap, "publish", regressionCaseId, publishedDocumentId)}
                onClick={() => onPublishDocument(gap)}
              >
                <ShieldCheck size={17} />
                {publishedDocumentId ? "已发布" : "发布知识"}
              </button>
              <button
                type="button"
                className="ghost-action"
                disabled={!hasToken || !canManage || isLoading || gap.status === "in_progress"}
                title={gapActionTitle(gap, "in_progress", regressionCaseId, publishedDocumentId)}
                aria-label={gapActionTitle(gap, "in_progress", regressionCaseId, publishedDocumentId)}
                onClick={() => onUpdate(gap, "in_progress")}
              >
                标记处理中
              </button>
              <button
                type="button"
                className="primary-action"
                disabled={!hasToken || !canManage || isLoading || gap.status === "resolved"}
                title={gapActionTitle(gap, "resolved", regressionCaseId, publishedDocumentId)}
                aria-label={gapActionTitle(gap, "resolved", regressionCaseId, publishedDocumentId)}
                onClick={() => onUpdate(gap, "resolved")}
              >
                <CheckCircle2 size={17} />
                标记已解决
              </button>
              <button
                type="button"
                className="ghost-action"
                disabled={!hasToken || !canManage || isLoading || gap.status === "rejected"}
                title={gapActionTitle(gap, "rejected", regressionCaseId, publishedDocumentId)}
                aria-label={gapActionTitle(gap, "rejected", regressionCaseId, publishedDocumentId)}
                onClick={() => onUpdate(gap, "rejected")}
              >
                不需补充
              </button>
              <a className="ghost-link" href={gap.source_type === "evaluation_run" ? "#evals" : "#live?queue=needs_review"}>
                看来源
              </a>
            </div>
          </article>
          );
        })}
      </div>

      <PaginationControls result={pagedResult} view={listView} onChange={onListViewChange} />
    </section>
  );
}

function KnowledgeEvaluationPanel({
  state,
  draft,
  questionBankDraft,
  labelImportDraft,
  setListView,
  resultListView,
  hasToken,
  canManage,
  onDraftChange,
  onQuestionBankDraftChange,
  onLabelImportDraftChange,
  onPrecheckQuestionBank,
  onImportQuestionBank,
  onSetListViewChange,
  onResultListViewChange,
  onCreateSet,
  onRunSet,
  onLoadRun,
  onLabelFactuality,
  onCaptureFinalAnswerSample,
  onBatchLabelSampledFactuality,
  onExportReport,
  onExportFinalAnswerLabels,
  onPrecheckFinalAnswerLabels,
  onImportFinalAnswerLabels,
  onRefresh
}: {
  state: KnowledgeEvaluationState;
  draft: KnowledgeEvaluationDraft;
  questionBankDraft: CustomerQuestionBankDraft;
  labelImportDraft: FinalAnswerLabelImportDraft;
  setListView: ListViewState;
  resultListView: ListViewState;
  hasToken: boolean;
  canManage: boolean;
  onDraftChange: (draft: KnowledgeEvaluationDraft) => void;
  onQuestionBankDraftChange: (draft: CustomerQuestionBankDraft) => void;
  onLabelImportDraftChange: (draft: FinalAnswerLabelImportDraft) => void;
  onPrecheckQuestionBank: () => void;
  onImportQuestionBank: () => void;
  onSetListViewChange: (view: ListViewState) => void;
  onResultListViewChange: (view: ListViewState) => void;
  onCreateSet: () => void;
  onRunSet: (setId: number) => void;
  onLoadRun: (runId: number) => void;
  onLabelFactuality: (runCase: KnowledgeEvaluationRunCase, statusValue: FactualityLabelStatus) => void;
  onCaptureFinalAnswerSample: (runCase: KnowledgeEvaluationRunCase, finalAnswerText: string) => void;
  onBatchLabelSampledFactuality: (run: KnowledgeEvaluationRun, statusValue: FactualityLabelStatus) => void;
  onExportReport: (runId: number, reportFormat: "markdown" | "csv") => void;
  onExportFinalAnswerLabels: (runId: number) => void;
  onPrecheckFinalAnswerLabels: (runId: number) => void;
  onImportFinalAnswerLabels: (runId: number) => void;
  onRefresh: () => void;
}) {
  const isLoading = state.status === "loading";
  const run = state.lastRun;
  const [finalAnswerDrafts, setFinalAnswerDrafts] = useState<Record<number, string>>({});
  const createSetDisabledReason = formatAccessDisabledReason({
    hasToken,
    canManage,
    isLoading,
    action: "创建评测集"
  });
  const pagedSets = useMemo(
    () =>
      getPagedItems(state.sets, setListView, {
        statusMatcher: (item, status) => item.status === status || item.evaluation_mode === status,
        searchText: (item) => [
          item.name,
          item.description,
          item.status,
          item.evaluation_mode,
          ...item.cases.map((testCase) => testCase.question)
        ]
      }),
    [state.sets, setListView]
  );
  const pagedResults = useMemo(
    () =>
      getPagedItems(run?.case_results ?? [], resultListView, {
        statusMatcher: (result, status) => {
          if (status === "needs_review") {
            return Boolean(result.failure_reason) || !result.citation_present || !result.expected_terms_found;
          }
          if (status === "no_citation") {
            return !result.citation_present;
          }
          if (status === "missing_terms") {
            return !result.expected_terms_found;
          }
          return result.status === status || result.failure_reason === status;
        },
        searchText: (result) => [
          result.question,
          result.status,
          result.failure_reason,
          result.matched_terms.join(" ")
        ]
      }),
    [run, resultListView]
  );
  const answerQualitySummary = run ? buildAnswerQualitySummary(run) : null;
  const sampledResultCount = run?.case_results.filter(hasFinalAnswerSample).length ?? 0;

  return (
    <section className="panel evaluation-panel" id="workspace-evals" aria-label="知识评测中心" data-knowledge-primary="evals">
      <div className="panel-heading">
        <div>
          <h2>知识评测中心</h2>
          <p>用固定题集反复检查检索命中、引用覆盖、期望词覆盖和发布前后的质量变化。</p>
        </div>
        <div className="panel-actions">
          <button type="button" className="ghost-action" onClick={onRefresh} disabled={!hasToken || isLoading}>
            <RefreshCw size={17} />
            {isLoading ? "刷新中" : "刷新"}
          </button>
        </div>
      </div>

      <div className="panel-state-row" aria-label="知识评测数据状态">
        <DataSourceBadge
          mode={hasToken ? "real" : "demo"}
          label={hasToken ? REAL_DATA_LABEL : PREVIEW_DATA_LABEL}
          detail={hasToken ? "读取固定题集、运行历史和逐题结果" : "仅展示评测闭环样例"}
        />
        <DataSourceBadge
          mode="local"
          label="质量口径"
          detail="命中率、引用覆盖、期望词覆盖不等同完整事实准确率"
        />
      </div>

      <PanelStateNotice status={state.status} message={state.message} loadingMessage="正在读取评测集和最近运行结果。" />

      <div className="evaluation-layout">
        <div className="evaluation-left-column">
          <form
            className="evaluation-form"
            onSubmit={(event) => {
              event.preventDefault();
              onCreateSet();
            }}
          >
            <div className="knowledge-section-title">
              <BarChart3 size={18} />
              <strong>创建评测集</strong>
            </div>
            <label className="field">
              <span>评测集名称</span>
              <input
                value={draft.name}
                onChange={(event) => onDraftChange({ ...draft, name: event.target.value })}
                placeholder="例如：售后政策核心题集"
                disabled={!hasToken || isLoading}
              />
            </label>
            <label className="field">
              <span>说明</span>
              <input
                value={draft.description}
                onChange={(event) => onDraftChange({ ...draft, description: event.target.value })}
                placeholder="本组题目覆盖的业务范围"
                disabled={!hasToken || isLoading}
              />
            </label>
            <label className="field">
              <span>评测口径</span>
              <select
                value={draft.evaluationMode}
                onChange={(event) =>
                  onDraftChange({
                    ...draft,
                    evaluationMode: event.target.value as KnowledgeEvaluationDraft["evaluationMode"]
                  })
                }
                disabled={!hasToken || isLoading}
              >
                <option value="customer_service_retrieval">客服答案质量口径</option>
                <option value="document_retrieval">文档检索口径</option>
              </select>
            </label>
            <label className="field">
              <span>题目</span>
              <textarea
                value={draft.casesText}
                onChange={(event) => onDraftChange({ ...draft, casesText: event.target.value })}
                placeholder={"标准产品保修期多久 | 三年，保修 | internal://docs/after-sales-v1 | 立即赔付 | 否 | 是 | 售后政策\n客户要求百分百退款怎么办 | 订单时间，商品状态 | internal://docs/after-sales-v1 | 百分百退款，马上赔偿 | 转人工 | 否 | 高风险售后"}
                disabled={!hasToken || isLoading}
                rows={7}
              />
            </label>
            <small className="form-hint">
              格式：问题 | 必含事实点 | 引用来源 | 禁用承诺词 | 是否转人工 | 是否允许自动回复 | 业务分类。当前不会生成最终客服答案。
            </small>
            <button type="submit" className="primary-action" disabled={!hasToken || !canManage || isLoading}>
              <CheckCircle2 size={17} />
              {canManage ? "创建评测集" : "仅管理员可创建"}
            </button>
            <DisabledReason show={Boolean(createSetDisabledReason)} reason={createSetDisabledReason} />
          </form>
          <CustomerQuestionBankImportPanel
            draft={questionBankDraft}
            disabled={!hasToken || !canManage || isLoading || questionBankDraft.status === "loading"}
            disabledReason={createSetDisabledReason}
            onChange={onQuestionBankDraftChange}
            onPrecheck={onPrecheckQuestionBank}
            onImport={onImportQuestionBank}
          />
        </div>

        <div className="evaluation-set-list">
          <div className="knowledge-section-title">
            <BookOpen size={18} />
            <strong>评测集列表</strong>
          </div>
          {state.sets.length === 0 && state.status === "ready" ? (
            <WorkspaceStateNotice
              kind="empty"
              message="暂无 active 评测集。先创建固定题集，后续才能判断知识发布前后的质量变化。"
              compact
            />
          ) : null}
          <ListToolbar
            view={setListView}
            total={state.sets.length}
            filteredTotal={pagedSets.total}
            statusOptions={[
              { label: "全部", value: "all" },
              { label: "已启用", value: "active" },
              { label: "草稿", value: "draft" },
              { label: "已归档", value: "archived" },
              { label: "客服质量", value: "customer_service_retrieval" },
              { label: "检索评测", value: "document_retrieval" }
            ]}
            searchPlaceholder="搜索评测集、说明、题目"
            onChange={onSetListViewChange}
          />
          {pagedSets.items.map((item) => (
            <article key={item.id} className="evaluation-case-row">
              <div className="knowledge-document-head">
                <div>
                  <strong>{item.name}</strong>
                  <span>
                    {item.status} · {item.evaluation_mode} · {item.case_count} 题
                  </span>
                </div>
                <button
                  type="button"
                  className="ghost-action"
                  onClick={() => onRunSet(item.id)}
                  disabled={!hasToken || !canManage || isLoading || item.case_count === 0}
                >
                  <Activity size={17} />
                  运行评测
                </button>
              </div>
              {item.description ? <p>{item.description}</p> : null}
              <div className="evidence-strip">
                {item.cases.slice(0, 4).map((testCase) => (
                  <span key={testCase.id}>{testCase.question}</span>
                ))}
              </div>
              <div className="evaluation-run-history" aria-label={`${item.name} 历史运行`}>
                <div className="knowledge-section-title">
                  <Activity size={17} />
                  <strong>最近运行</strong>
                </div>
                {(state.runsBySet[item.id] ?? []).length === 0 ? (
                  <WorkspaceStateNotice kind="empty" message="暂无历史运行。运行一次后这里会展示同题集对比入口。" compact />
                ) : (
                  (state.runsBySet[item.id] ?? []).slice(0, 4).map((historyRun) => (
                    <article key={historyRun.id} className="evaluation-run-row">
                      <div>
                        <strong>运行 #{historyRun.id}</strong>
                        <span>
                          {formatDateTime(historyRun.created_at)} · 命中 {formatPercent(historyRun.hit_rate)} · 复盘 {historyRun.needs_review_cases}
                        </span>
                      </div>
                      <button
                        type="button"
                        className="ghost-action"
                        onClick={() => onLoadRun(historyRun.id)}
                        disabled={!hasToken || !canManage || isLoading}
                      >
                        查看详情
                      </button>
                    </article>
                  ))
                )}
              </div>
            </article>
          ))}
          <PaginationControls result={pagedSets} view={setListView} onChange={onSetListViewChange} />
        </div>
      </div>

      {run ? (
        <div className="evaluation-report" aria-live="polite">
          <div className="evaluation-report-head">
            <div>
              <strong>当前运行 #{run.id}</strong>
              <span>
                {formatDateTime(run.created_at)} · {run.run_mode}
              </span>
            </div>
            <div className="evaluation-report-actions">
              <small>评测集 #{run.evaluation_set_id}</small>
              <button
                type="button"
                className="ghost-action"
                onClick={() => onExportReport(run.id, "markdown")}
                disabled={!hasToken || !canManage || isLoading}
              >
                <FileText size={17} />
                下载报告
              </button>
              <button
                type="button"
                className="ghost-action"
                onClick={() => onExportReport(run.id, "csv")}
                disabled={!hasToken || !canManage || isLoading}
              >
                CSV
              </button>
            </div>
          </div>
          <div className="quality-metric-grid">
            <QualityMetric label="命中率" value={formatPercent(run.hit_rate)} note={`${run.answered_cases}/${run.total_cases} 题命中`} />
            <QualityMetric label="引用覆盖" value={formatPercent(run.citation_coverage)} note={`${run.citation_covered_cases}/${run.total_cases} 题有引用`} />
            <QualityMetric label="期望词覆盖" value={formatPercent(run.expected_term_coverage)} note={`${run.expected_term_covered_cases}/${run.total_cases} 题覆盖`} />
            <QualityMetric label="需复盘" value={`${run.needs_review_cases}`} note={`平均置信度 ${formatPercent(run.average_confidence)}`} />
          </div>
          {answerQualitySummary ? (
            <section className="answer-quality-gate" data-answer-quality-gate="p3-06u-26e">
              <div className="knowledge-section-title">
                <ShieldCheck size={18} />
                <strong>客服答案质量门禁</strong>
              </div>
              <div className="answer-quality-grid">
                <article className="answer-quality-card">
                  <span>最终答案事实性</span>
                  <strong>{answerQualitySummary.factualityMeasured ? formatPercent(answerQualitySummary.factualityRate) : "未评"}</strong>
                  <small>{answerQualitySummary.factualityNote}</small>
                </article>
                <article className="answer-quality-card">
                  <span>引用充分</span>
                  <strong>{formatPercent(answerQualitySummary.citationSufficiencyRate)}</strong>
                  <small>
                    {answerQualitySummary.citationSufficientCases}/{run.total_cases} 题满足证据门禁
                  </small>
                </article>
                <article className="answer-quality-card">
                  <span>禁用承诺</span>
                  <strong>{answerQualitySummary.forbiddenViolationCases} 命中</strong>
                  <small>证据层违规率 {formatPercent(answerQualitySummary.forbiddenViolationRate)}；最终答案承诺仍待后续评测。</small>
                </article>
                <article className="answer-quality-card">
                  <span>转人工正确性</span>
                  <strong>{formatPercent(answerQualitySummary.handoffCorrectness)}</strong>
                  <small>
                    {answerQualitySummary.handoffCorrectCases}/{run.total_cases} 题门禁判断正确
                  </small>
                </article>
              </div>
              <p>
                当前只把最终答案事实性标记为“未评”，并把引用充分、禁用承诺、转人工正确性接入可视化门禁；不调用模型、不外发、不把检索命中率包装成完整准确率。
              </p>
              <div className="final-answer-batch-panel" data-final-answer-batch-label="p3-06u-26h2p">
                <div>
                  <strong>最终回复样本</strong>
                  <span>
                    已采样 {sampledResultCount}/{run.total_cases} 题；批量标签只处理已采样样本。
                  </span>
                </div>
                <div className="factuality-label-buttons">
                  <button
                    type="button"
                    className="tiny-action positive"
                    disabled={!hasToken || !canManage || isLoading || sampledResultCount === 0}
                    onClick={() => onBatchLabelSampledFactuality(run, "correct")}
                  >
                    批量标为事实正确
                  </button>
                  <button
                    type="button"
                    className="tiny-action warning"
                    disabled={!hasToken || !canManage || isLoading || sampledResultCount === 0}
                    onClick={() => onBatchLabelSampledFactuality(run, "needs_human_review")}
                  >
                    批量标为应转人工
                  </button>
                </div>
              </div>
              <FinalAnswerLabelImportPanel
                run={run}
                draft={labelImportDraft}
                disabled={!hasToken || !canManage || isLoading || labelImportDraft.status === "loading"}
                onChange={onLabelImportDraftChange}
                onExport={onExportFinalAnswerLabels}
                onPrecheck={onPrecheckFinalAnswerLabels}
                onImport={onImportFinalAnswerLabels}
              />
            </section>
          ) : null}
          <div className="retrieval-summary">
            <span>{run.retrieval_mode}</span>
            <span>{run.vector_engine}</span>
            <span>unsupported_answer_rate：{run.unsupported_answer_rate === null ? "未评生成答案" : formatPercent(run.unsupported_answer_rate)}</span>
          </div>
          <ListToolbar
            view={resultListView}
            total={run.case_results.length}
            filteredTotal={pagedResults.total}
            statusOptions={[
              { label: "全部", value: "all" },
              { label: "通过", value: "passed" },
              { label: "需复盘", value: "needs_review" },
              { label: "缺引用", value: "no_citation" },
              { label: "缺期望词", value: "missing_terms" },
              { label: "无命中", value: "no_hit" }
            ]}
            searchPlaceholder="搜索题目、失败原因、命中词"
            onChange={onResultListViewChange}
          />
          <div className="evaluation-results">
            {pagedResults.items.map((result) => (
              <article key={result.id} className="evaluation-result-row">
                <div className="knowledge-document-head">
                  <div>
                    <strong>{result.question}</strong>
                    <span>
                      {result.status} · 置信度 {formatPercent(result.top_confidence)} · 分数 {result.top_score.toFixed(2)}
                    </span>
                  </div>
                  <small>
                    文档 {result.top_document_id ?? "-"} · 片段 {result.top_chunk_id ?? "-"}
                  </small>
                </div>
                <div className="attempt-line">
                  <span className={result.citation_present ? "connector-pill" : "retry-pill"}>
                    {result.citation_present ? "引用存在" : "缺少引用"}
                  </span>
                  <span className={result.expected_terms_found ? "connector-pill" : "retry-pill"}>
                    {result.expected_terms_found ? "期望词覆盖" : "期望词缺失"}
                  </span>
                  {result.failure_reason ? <span className="retry-pill">{result.failure_reason}</span> : null}
                </div>
                <AnswerQualityCaseBadges result={result} />
                <FinalAnswerSampleEditor
                  result={result}
                  value={finalAnswerDrafts[result.id] ?? getFinalAnswerSampleText(result)}
                  disabled={!hasToken || !canManage || isLoading}
                  onChange={(value) =>
                    setFinalAnswerDrafts((current) => ({
                      ...current,
                      [result.id]: value
                    }))
                  }
                  onSave={(value) => onCaptureFinalAnswerSample(result, value)}
                />
                <FactualityLabelActions
                  result={result}
                  disabled={!hasToken || !canManage || isLoading}
                  onLabel={(statusValue) => onLabelFactuality(result, statusValue)}
                />
                {result.matched_terms.length > 0 ? (
                  <div className="evidence-strip">
                    {result.matched_terms.slice(0, 8).map((term) => (
                      <span key={term}>{term}</span>
                    ))}
                  </div>
                ) : null}
              </article>
            ))}
          </div>
          <PaginationControls result={pagedResults} view={resultListView} onChange={onResultListViewChange} />
        </div>
      ) : (
        <WorkspaceStateNotice
          kind={hasToken ? "empty" : "demo"}
          title={hasToken ? "暂无数据" : PREVIEW_DATA_LABEL}
          message="尚未运行评测；当前只统计检索质量，不评估生成答案事实性。"
          compact
        />
      )}
    </section>
  );
}

function FinalAnswerLabelImportPanel({
  run,
  draft,
  disabled,
  onChange,
  onExport,
  onPrecheck,
  onImport
}: {
  run: KnowledgeEvaluationRun;
  draft: FinalAnswerLabelImportDraft;
  disabled: boolean;
  onChange: (draft: FinalAnswerLabelImportDraft) => void;
  onExport: (runId: number) => void;
  onPrecheck: (runId: number) => void;
  onImport: (runId: number) => void;
}) {
  const result = draft.result;
  const hasErrors = (result?.validation_errors.length ?? 0) > 0;
  const canImport = Boolean(result && !result.dry_run && result.imported) ? false : Boolean(result && !hasErrors);
  return (
    <section className="final-answer-label-import" data-final-answer-label-io="p3-06u-26h2r">
      <div className="final-answer-sample-head">
        <div>
          <strong>离线标注表</strong>
          <span>导出 CSV 后可在表格里补最终回复和人工标签，再粘贴回当前运行。</span>
          <small>不会导出原始客户问题；CSV 会包含最终回复样本，适合本地授权标注。</small>
        </div>
        <button type="button" className="ghost-action" onClick={() => onExport(run.id)} disabled={disabled}>
          <FileText size={16} />
          导出 CSV
        </button>
      </div>
      <label className="field">
        <span>样本与标签 CSV</span>
        <textarea
          value={draft.text}
          onChange={(event) =>
            onChange({
              ...draft,
              text: event.target.value,
              result: null,
              status: "idle",
              message: "CSV 已修改，请重新预检。"
            })
          }
          rows={6}
          spellCheck={false}
          disabled={disabled}
          placeholder="evaluation_run_case_id,external_case_id,source_channel,source_category,question_hash,final_answer_text,..."
        />
      </label>
      <div className="final-answer-label-actions">
        <button type="button" className="ghost-action" onClick={() => onPrecheck(run.id)} disabled={disabled || !draft.text.trim()}>
          <ShieldCheck size={16} />
          预检 CSV
        </button>
        <button type="button" className="primary-action" onClick={() => onImport(run.id)} disabled={disabled || !canImport}>
          <Upload size={16} />
          导入标签
        </button>
      </div>
      <PanelStateNotice status={draft.status} message={draft.message} loadingMessage="正在处理最终回复样本与人工标签 CSV。" compact />
      {result ? (
        <div className="final-answer-label-summary">
          <span>总行数 {result.total_rows}</span>
          <span>匹配 {result.matched_rows}</span>
          <span>样本 {result.sample_rows}</span>
          <span>标签 {result.label_rows}</span>
          <span>跳过 {result.skipped_rows}</span>
        </div>
      ) : null}
      {result?.validation_errors.length ? (
        <div className="question-bank-errors">
          {result.validation_errors.slice(0, 4).map((error, index) => (
            <span key={index}>
              第 {String(error.row ?? "-")} 行：{String(error.message ?? "字段不符合要求")}
            </span>
          ))}
        </div>
      ) : null}
    </section>
  );
}

function CustomerQuestionBankImportPanel({
  draft,
  disabled,
  disabledReason,
  onChange,
  onPrecheck,
  onImport
}: {
  draft: CustomerQuestionBankDraft;
  disabled: boolean;
  disabledReason: string;
  onChange: (draft: CustomerQuestionBankDraft) => void;
  onPrecheck: () => void;
  onImport: () => void;
}) {
  const result = draft.result;
  const summary = result?.coverage_summary ?? {};
  const target = readRecordPayload(summary, "case_count_target") ?? {};
  const sourceChannels = readRecordPayload(summary, "source_channel_counts") ?? {};
  const riskLevels = readRecordPayload(summary, "risk_level_counts") ?? {};
  const expectedTermsCoverage = readNumberPayload(summary, "expected_terms_coverage");
  const sourceReferenceCoverage = readNumberPayload(summary, "source_reference_coverage");
  const handoffRate = readNumberPayload(summary, "handoff_expected_rate");
  const withinRange = readBooleanPayload(target, "within_range");
  const channelSummary = Object.entries(sourceChannels)
    .slice(0, 5)
    .map(([key, value]) => `${key} ${value}`)
    .join(" / ");
  const riskSummary = Object.entries(riskLevels)
    .slice(0, 5)
    .map(([key, value]) => `${key} ${value}`)
    .join(" / ");
  return (
    <section className="customer-question-bank-panel" data-question-bank-import="p3-06u-26h2o">
      <div className="knowledge-section-title">
        <Upload size={18} />
        <strong>客户题库导入</strong>
      </div>
      <p>
        粘贴由脱敏表格转换后的 JSON 题库包。系统先检查 50-100 题数量、敏感信息、渠道分布、风险分布和引用覆盖，再导入为客服质量评测集。
      </p>
      <label className="field">
        <span>题库 JSON</span>
        <textarea
          value={draft.text}
          onChange={(event) =>
            onChange({
              ...draft,
              text: event.target.value,
              result: null,
              status: "idle",
              message: "题库内容已修改，请重新预检。"
            })
          }
          rows={9}
          spellCheck={false}
          disabled={disabled}
        />
      </label>
      <div className="question-bank-actions">
        <button
          type="button"
          className="ghost-action"
          onClick={onPrecheck}
          disabled={disabled}
          title={disabledReason || "预检客户题库包。"}
          aria-label={disabledReason || "预检客户题库包"}
        >
          <ShieldCheck size={17} />
          预检题库
        </button>
        <button
          type="button"
          className="primary-action"
          onClick={onImport}
          disabled={disabled || !result?.can_import}
          title={disabledReason || (!result?.can_import ? "请先通过题库预检，再导入题库。" : "导入已通过预检的客户题库。")}
          aria-label={disabledReason || (!result?.can_import ? "导入题库不可用，请先通过题库预检" : "导入已通过预检的客户题库")}
        >
          <CheckCircle2 size={17} />
          导入题库
        </button>
      </div>
      <DisabledReason show={Boolean(disabledReason)} reason={disabledReason} />
      <PanelStateNotice status={draft.status} message={draft.message} loadingMessage="正在检查客户题库包。" />
      {result ? (
        <div className="question-bank-result" data-question-bank-result="p3-06u-26h2o">
          <div className="quality-metric-grid compact">
            <QualityMetric label="题量" value={`${result.case_count}`} note={withinRange ? "符合 50-100 题范围" : "题量不在范围内"} />
            <QualityMetric label="事实点覆盖" value={formatPercent(expectedTermsCoverage)} note="每题 expected_terms 覆盖率" />
            <QualityMetric label="引用来源" value={formatPercent(sourceReferenceCoverage)} note="每题 source_reference 覆盖率" />
            <QualityMetric label="转人工样本" value={formatPercent(handoffRate)} note="用于检验转人工边界" />
          </div>
          <div className="question-bank-summary-grid">
            <span>渠道：{channelSummary || "未填写"}</span>
            <span>风险：{riskSummary || "未填写"}</span>
            <span>敏感命中：{result.sensitive_rows.length}</span>
            <span>原文回显：{result.raw_text_included ? "有风险" : "关闭"}</span>
          </div>
          {result.validation_errors.length > 0 ? (
            <div className="question-bank-errors">
              <AlertTriangle size={16} />
              <span>{result.validation_errors.join("；")}</span>
            </div>
          ) : null}
          {result.imported ? <span className="connector-pill">已导入评测集 #{result.evaluation_set_id}</span> : null}
        </div>
      ) : null}
      <small className="form-hint">
        本入口不调用模型、不写外部平台、不上传诊断包；导入后仍需运行评测并对最终答案做人工事实性标签。
      </small>
    </section>
  );
}

interface AnswerQualitySummary {
  factualityMeasured: boolean;
  factualityRate: number | null;
  factualityNote: string;
  citationSufficiencyRate: number | null;
  citationSufficientCases: number;
  forbiddenViolationRate: number | null;
  forbiddenViolationCases: number;
  handoffCorrectness: number | null;
  handoffCorrectCases: number;
}

function buildAnswerQualitySummary(run: KnowledgeEvaluationRun): AnswerQualitySummary {
  const payload = run.summary_payload;
  return {
    factualityMeasured: readBooleanPayload(payload, "final_answer_factuality_measured") ?? false,
    factualityRate: readNumberPayload(payload, "final_answer_factuality_rate"),
    factualityNote:
      readStringPayload(payload, "final_answer_factuality_note") ||
      "当前未生成最终客服答案，不能把检索命中率当作完整事实准确率。",
    citationSufficiencyRate: readNumberPayload(payload, "citation_sufficiency_rate"),
    citationSufficientCases: readNumberPayload(payload, "citation_sufficient_cases") ?? 0,
    forbiddenViolationRate: readNumberPayload(payload, "forbidden_commitment_violation_rate"),
    forbiddenViolationCases: readNumberPayload(payload, "forbidden_commitment_violation_cases") ?? 0,
    handoffCorrectness: readNumberPayload(payload, "handoff_correctness") ?? readNumberPayload(payload, "human_review_correctness"),
    handoffCorrectCases: readNumberPayload(payload, "handoff_correct_cases") ?? readNumberPayload(payload, "human_review_correct_cases") ?? 0
  };
}

function getFinalAnswerSampleRecord(result: KnowledgeEvaluationRunCase): Record<string, unknown> {
  return readRecordPayload(result.result_payload, "final_answer_sample") ?? {};
}

function getFinalAnswerSampleText(result: KnowledgeEvaluationRunCase): string {
  return readStringPayload(getFinalAnswerSampleRecord(result), "final_answer_text");
}

function hasFinalAnswerSample(result: KnowledgeEvaluationRunCase): boolean {
  const answerQuality = readRecordPayload(result.result_payload, "answer_quality") ?? {};
  return (
    readBooleanPayload(answerQuality, "final_answer_sample_available") === true ||
    Boolean(readStringPayload(getFinalAnswerSampleRecord(result), "final_answer_hash")) ||
    Boolean(getFinalAnswerSampleText(result))
  );
}

function extractCitationUrisFromRunCase(result: KnowledgeEvaluationRunCase): string[] {
  const payload = result.result_payload;
  const topMatch = readRecordPayload(payload, "top_match") ?? {};
  const citation = readRecordPayload(topMatch, "citation") ?? {};
  return Array.from(
    new Set(
      [
        readStringPayload(payload, "expected_source_uri"),
        readStringPayload(topMatch, "source_uri"),
        readStringPayload(citation, "source_uri")
      ].filter(Boolean)
    )
  );
}

function FinalAnswerSampleEditor({
  result,
  value,
  disabled,
  onChange,
  onSave
}: {
  result: KnowledgeEvaluationRunCase;
  value: string;
  disabled: boolean;
  onChange: (value: string) => void;
  onSave: (value: string) => void;
}) {
  const sample = getFinalAnswerSampleRecord(result);
  const savedText = getFinalAnswerSampleText(result);
  const sampleSource = readStringPayload(sample, "final_answer_source") || "manual_capture";
  const sampleLength = readNumberPayload(sample, "final_answer_length") ?? savedText.length;
  const hasSample = hasFinalAnswerSample(result);

  return (
    <div className="final-answer-sample-editor" data-final-answer-sample="p3-06u-26h2p">
      <div className="final-answer-sample-head">
        <div>
          <span>最终客服回复样本</span>
          <strong>{hasSample ? "已采样" : "待采样"}</strong>
          <small>
            {hasSample ? `${sampleSource} · ${sampleLength} 字` : "用于后续人工事实性标签，不调用模型、不外发"}
          </small>
        </div>
        <button
          type="button"
          className="tiny-action positive"
          disabled={disabled || !value.trim()}
          onClick={() => onSave(value)}
        >
          保存样本
        </button>
      </div>
      <textarea
        value={value}
        rows={3}
        disabled={disabled}
        onChange={(event) => onChange(event.target.value)}
        placeholder="粘贴或录入本题最终客服回复，用于人工判断事实是否正确。"
      />
    </div>
  );
}

function AnswerQualityCaseBadges({ result }: { result: KnowledgeEvaluationRunCase }) {
  const answerQuality = readRecordPayload(result.result_payload, "answer_quality");
  if (!answerQuality) {
    return null;
  }
  const citationSufficient = readBooleanPayload(answerQuality, "citation_sufficient");
  const forbiddenPassed = readBooleanPayload(answerQuality, "forbidden_commitment_passed");
  const handoffCorrect = readBooleanPayload(answerQuality, "handoff_correct");
  const factualityStatus = readStringPayload(answerQuality, "final_answer_factuality_status") || "not_measured";
  return (
    <div className="answer-quality-badges" data-answer-quality-case="p3-06u-26e">
      <span className="neutral-pill">事实性：{factualityStatus.includes("not_measured") ? "未评" : factualityStatus}</span>
      <span className={citationSufficient ? "connector-pill" : "retry-pill"}>引用充分：{citationSufficient ? "通过" : "需复核"}</span>
      <span className={forbiddenPassed ? "connector-pill" : "retry-pill"}>禁用承诺：{forbiddenPassed ? "未命中" : "命中"}</span>
      <span className={handoffCorrect ? "connector-pill" : "retry-pill"}>转人工：{handoffCorrect ? "正确" : "需复核"}</span>
    </div>
  );
}

function formatFactualityLabelStatus(statusValue: string) {
  switch (statusValue) {
    case "correct":
      return "事实正确";
    case "partially_correct":
      return "部分正确";
    case "incorrect":
      return "事实有误";
    case "needs_human_review":
      return "应转人工";
    case "not_applicable":
      return "不适用";
    case "not_measured_final_answer_not_generated":
    case "not_measured":
      return "未标注";
    default:
      return statusValue || "未标注";
  }
}

function FactualityLabelActions({
  result,
  disabled,
  onLabel
}: {
  result: KnowledgeEvaluationRunCase;
  disabled: boolean;
  onLabel: (statusValue: FactualityLabelStatus) => void;
}) {
  const answerQuality = readRecordPayload(result.result_payload, "answer_quality");
  const currentStatus = readStringPayload(answerQuality ?? {}, "final_answer_factuality_status") || "not_measured";
  const measured = readBooleanPayload(answerQuality ?? {}, "final_answer_factuality_measured") ?? false;
  const labelOptions: Array<{ value: FactualityLabelStatus; label: string; tone: string }> = [
    { value: "correct", label: "事实正确", tone: "positive" },
    { value: "partially_correct", label: "部分正确", tone: "neutral" },
    { value: "incorrect", label: "事实有误", tone: "danger" },
    { value: "needs_human_review", label: "应转人工", tone: "warning" }
  ];

  return (
    <div className="factuality-label-actions" data-factuality-label-actions="p3-06u-26h2n">
      <div>
        <span>人工事实性标签</span>
        <strong>{formatFactualityLabelStatus(currentStatus)}</strong>
        <small>{measured ? "已纳入月度质量复盘" : "标注后才计算最终答案事实性"}</small>
      </div>
      <div className="factuality-label-buttons">
        {labelOptions.map((option) => (
          <button
            key={option.value}
            type="button"
            className={`tiny-action ${option.tone}`}
            onClick={() => onLabel(option.value)}
            disabled={disabled || currentStatus === option.value}
          >
            {option.label}
          </button>
        ))}
      </div>
    </div>
  );
}

function readNumberPayload(payload: Record<string, unknown>, key: string): number | null {
  const value = payload[key];
  if (typeof value === "number" && Number.isFinite(value)) {
    return value;
  }
  if (typeof value === "string" && value.trim()) {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : null;
  }
  return null;
}

function readBooleanPayload(payload: Record<string, unknown>, key: string): boolean | null {
  const value = payload[key];
  if (typeof value === "boolean") {
    return value;
  }
  if (typeof value === "string") {
    if (["true", "1", "yes", "是"].includes(value.toLowerCase())) {
      return true;
    }
    if (["false", "0", "no", "否"].includes(value.toLowerCase())) {
      return false;
    }
  }
  return null;
}

function readStringPayload(payload: Record<string, unknown>, key: string): string {
  const value = payload[key];
  return typeof value === "string" ? value : "";
}

function readRecordPayload(payload: Record<string, unknown>, key: string): Record<string, unknown> | null {
  const value = payload[key];
  if (value && typeof value === "object" && !Array.isArray(value)) {
    return value as Record<string, unknown>;
  }
  return null;
}

function ListToolbar({
  view,
  total,
  filteredTotal,
  statusOptions,
  searchPlaceholder,
  onChange
}: {
  view: ListViewState;
  total: number;
  filteredTotal: number;
  statusOptions: StatusOption[];
  searchPlaceholder: string;
  onChange: (view: ListViewState) => void;
}) {
  return (
    <div className="list-toolbar" aria-label="列表筛选">
      <label className="list-search">
        <Search size={16} />
        <input
          value={view.query}
          onChange={(event) => onChange({ ...view, query: event.target.value, page: 1 })}
          placeholder={searchPlaceholder}
          type="search"
        />
      </label>
      <label className="list-filter">
        <span>状态</span>
        <select
          value={view.status}
          onChange={(event) => onChange({ ...view, status: event.target.value, page: 1 })}
        >
          {statusOptions.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </label>
      <label className="list-filter">
        <span>每页</span>
        <select
          value={view.pageSize}
          onChange={(event) => onChange({ ...view, pageSize: Number(event.target.value), page: 1 })}
        >
          {[4, 6, 8, 12, 20].map((pageSize) => (
            <option key={pageSize} value={pageSize}>
              {pageSize}
            </option>
          ))}
        </select>
      </label>
      <div className="list-count">
        <strong>{filteredTotal}</strong>
        <span>已筛选 / 已加载 {total}</span>
      </div>
    </div>
  );
}

function KnowledgeGapFilterToolbar({
  view,
  total,
  filteredTotal,
  onChange
}: {
  view: ListViewState;
  total: number;
  filteredTotal: number;
  onChange: (view: ListViewState) => void;
}) {
  const statusOptions: StatusOption[] = [
    { label: "全部", value: "all" },
    { label: "待处理", value: "open" },
    { label: "已分诊", value: "triaged" },
    { label: "处理中", value: "in_progress" },
    { label: "已解决", value: "resolved" },
    { label: "已驳回", value: "rejected" },
    { label: "已归档", value: "archived" }
  ];
  const severityOptions: StatusOption[] = [
    { label: "全部", value: "all" },
    { label: "严重", value: "critical" },
    { label: "高", value: "high" },
    { label: "中", value: "medium" },
    { label: "低", value: "low" }
  ];
  const sourceOptions: StatusOption[] = [
    { label: "全部", value: "all" },
    { label: "转人工", value: "human_review" },
    { label: "评测失败", value: "evaluation_run" },
    { label: "回复决策", value: "reply_decision" },
    { label: "手动记录", value: "manual" }
  ];

  return (
    <div className="list-toolbar knowledge-gap-filter-toolbar" aria-label="知识缺口服务端筛选" data-knowledge-gap-server-filters="p3-06u-26g5">
      <label className="list-search">
        <Search size={16} />
        <input
          value={view.query}
          onChange={(event) => onChange({ ...view, query: event.target.value, page: 1 })}
          placeholder="搜索问题、错因、来源、期望词"
          type="search"
        />
      </label>
      <label className="list-filter">
        <span>状态</span>
        <select value={view.status} onChange={(event) => onChange({ ...view, status: event.target.value, page: 1 })}>
          {statusOptions.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </label>
      <label className="list-filter">
        <span>严重度</span>
        <select
          value={view.severity ?? "all"}
          onChange={(event) => onChange({ ...view, severity: event.target.value, page: 1 })}
        >
          {severityOptions.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </label>
      <label className="list-filter">
        <span>来源</span>
        <select
          value={view.sourceType ?? "all"}
          onChange={(event) => onChange({ ...view, sourceType: event.target.value, page: 1 })}
        >
          {sourceOptions.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </label>
      <label className="list-filter">
        <span>每页</span>
        <select
          value={view.pageSize}
          onChange={(event) => onChange({ ...view, pageSize: Number(event.target.value), page: 1 })}
        >
          {[4, 6, 8, 12, 20].map((pageSize) => (
            <option key={pageSize} value={pageSize}>
              {pageSize}
            </option>
          ))}
        </select>
      </label>
      <div className="list-count">
        <strong>{filteredTotal}</strong>
        <span>服务端筛选 / 已加载 {total}</span>
      </div>
    </div>
  );
}

function PaginationControls<T>({
  result,
  view,
  onChange
}: {
  result: PagedResult<T>;
  view: ListViewState;
  onChange: (view: ListViewState) => void;
}) {
  if (result.total === 0) {
    return null;
  }
  const atFirstPage = result.page <= 1;
  const atLastPage = result.page >= result.pageCount;
  return (
    <div className="pagination-bar" aria-label="分页">
      <span>
        第 {result.start}-{result.end} 条 / 共 {result.total} 条
      </span>
      <div className="pagination-actions">
        <button
          type="button"
          className="ghost-action"
          onClick={() => onChange({ ...view, page: Math.max(1, result.page - 1) })}
          disabled={atFirstPage}
          title={atFirstPage ? "当前已经是第一页，不能继续向前翻页。" : "查看上一页"}
          aria-label={atFirstPage ? "上一页不可用，当前已经是第一页" : "查看上一页"}
        >
          上一页
        </button>
        <strong>
          {result.page} / {result.pageCount}
        </strong>
        <button
          type="button"
          className="ghost-action"
          onClick={() => onChange({ ...view, page: Math.min(result.pageCount, result.page + 1) })}
          disabled={atLastPage}
          title={atLastPage ? "当前已经是最后一页，不能继续向后翻页。" : "查看下一页"}
          aria-label={atLastPage ? "下一页不可用，当前已经是最后一页" : "查看下一页"}
        >
          下一页
        </button>
      </div>
    </div>
  );
}

function PilotPreparationPanel({
  pilotReadiness,
  localMaintenanceReadiness,
  monthlyOpsReport,
  knowledgeConfirmationImport,
  customerMaterialPrecheck,
  customerMaterialBatches,
  customerMaterialTemplatePackage,
  customerMaterialHandoffBundle,
  canImportConfirmation,
  onRefresh,
  onImportKnowledgeConfirmation,
  onPrecheckCustomerMaterials,
  onLoadCustomerMaterialBatches,
  onLoadCustomerMaterialTemplatePackage,
  onDownloadCustomerMaterialHandoffBundle
}: {
  pilotReadiness: PilotReadinessState;
  localMaintenanceReadiness: LocalMaintenanceReadinessState;
  monthlyOpsReport: MonthlyOpsReportState;
  knowledgeConfirmationImport: KnowledgeConfirmationImportState;
  customerMaterialPrecheck: CustomerMaterialPrecheckState;
  customerMaterialBatches: CustomerMaterialBatchListState;
  customerMaterialTemplatePackage: CustomerMaterialTemplatePackageState;
  customerMaterialHandoffBundle: CustomerMaterialHandoffBundleState;
  canImportConfirmation: boolean;
  onRefresh: () => void;
  onImportKnowledgeConfirmation: (filename: string, csvText: string) => void;
  onPrecheckCustomerMaterials: (materialsCsv: string, questionsCsv: string, manifestJson: string) => void;
  onLoadCustomerMaterialBatches: () => void;
  onLoadCustomerMaterialTemplatePackage: () => void;
  onDownloadCustomerMaterialHandoffBundle: () => void;
}) {
  const [confirmationFilename, setConfirmationFilename] = useState("customer_knowledge_confirmation.csv");
  const [confirmationText, setConfirmationText] = useState("");
  const [materialsCsv, setMaterialsCsv] = useState("");
  const [questionsCsv, setQuestionsCsv] = useState("");
  const [manifestJson, setManifestJson] = useState("");
  const readiness = pilotReadiness.data;
  const maintenance = localMaintenanceReadiness.data;
  const report = monthlyOpsReport.data;
  const importResult = knowledgeConfirmationImport.result;
  const materialPrecheckResult = customerMaterialPrecheck.result;
  const materialTemplatePackage = customerMaterialTemplatePackage.data;
  const materialBatchList = customerMaterialBatches.data;
  const latestMaterialBatch = materialBatchList?.latest_batch ?? readiness?.latest_material_batch ?? null;
  const [materialFileMessage, setMaterialFileMessage] = useState("");
  const batchStatusLabel: Record<string, string> = {
    waiting_for_material_precheck: "等待预检",
    material_precheck_batches_available: "已有通过预检批次",
    precheck_passed_waiting_file_drop: "预检通过，等待回传落位",
    blocked_latest_material_precheck: "最近预检被阻断",
    blocked_precheck_failed: "预检阻断",
    customer_real_materials_ready: "客户资料已通过资料门禁",
    material_batches_recorded: "已有资料批次"
  };
  const statusLabel: Record<string, string> = {
    blocked: "存在阻断",
    pilot_candidate_ready_with_internal_data: "内部资料试点候选",
    pilot_candidate_ready_with_customer_data: "客户资料试点候选"
  };
  const trialClosureStatusLabel: Record<string, string> = {
    waiting_for_trial_closure_evidence: "等待试跑证据",
    blocked: "存在阻断",
    co_creation_trial_v1_candidate: "试跑封版候选",
    co_creation_trial_v1_1_candidate_with_internal_data: "试跑包 v1.1 候选",
    co_creation_trial_v1_1_candidate_with_customer_data: "客户资料试跑包 v1.1 候选"
  };
  const realMaterialStatusLabel: Record<string, string> = {
    not_checked: "等待资料门禁",
    missing: "等待资料门禁",
    waiting_for_real_customer_materials: "等待真实脱敏资料",
    customer_real_materials_ready: "真实脱敏资料已就绪",
    internal_sample_materials_ready_for_rehearsal: "内部样板资料已就绪",
    blocked: "真实资料存在阻断"
  };
  const fiveGapStatusLabel: Record<string, string> = {
    not_checked: "待生成",
    not_generated: "待生成",
    missing: "待生成",
    blocked: "存在阻断",
    material_intake_package_ready: "资料接收包就绪",
    material_validation_fixtures_passed: "资料门禁校验通过",
    received_file_drop_ready_waiting_customer_files: "等待回传文件",
    received_files_present_pending_data2r_validation: "文件已落位，待校验",
    received_files_validated_ready_for_pack12_rerun: "文件已校验，可重跑",
    received_internal_sample_files_validated_ready_for_pack12_rerun: "样板文件已校验，可重跑",
    blocked_waiting_real_customer_materials: "等待真实资料",
    waiting_for_real_customer_materials: "等待真实资料",
    customer_real_materials_ready: "真实资料就绪",
    internal_sample_materials_ready_for_rehearsal: "内部样板就绪",
    customer_knowledge_retest_ready_with_customer_data: "真实资料复测通过",
    customer_knowledge_retest_ready_with_internal_sample: "样板复测通过",
    shadow_trial_ready_with_customer_data: "真实资料影子试跑通过",
    shadow_trial_ready_with_internal_sample: "样板影子试跑通过",
    passed_customer_data_browser_qa: "二次验收通过",
    passed_internal_sample_browser_qa: "样板二次验收通过",
    frontend_final_product_polish_ready: "成品感就绪",
    channel_personnel_boundary_ready: "人员边界就绪",
    trial_installer_experience_candidate_ready: "安装体验候选",
    customer_data_local_trial_package_v2_candidate: "交付档案 v2 候选",
    internal_sample_local_trial_package_v2_candidate: "样板交付档案 v2 候选"
  };
  const stepStatusLabel: Record<string, string> = {
    ready: "已就绪",
    passed: "已验证",
    pending: "待补齐",
    blocked: "阻断",
    warning: "需复核"
  };
  const steps = readiness?.steps ?? [
    {
      code: "local_environment",
      title: "本地环境",
      status: localMaintenanceReadiness.status === "ready" ? "ready" : "pending",
      summary: maintenance?.summary ?? "等待读取本地维护状态。",
      next_action: "进入账号与本地维护查看环境状态。",
      target_href: "#settings",
      blockers: [],
      evidence: []
    },
    {
      code: "owner_account",
      title: "账号负责人",
      status: "pending",
      summary: "等待负责人账号与本地权限状态。",
      next_action: "创建或核对负责人账号。",
      target_href: "#settings",
      blockers: [],
      evidence: []
    },
    {
      code: "knowledge_materials",
      title: "知识资料",
      status: "pending",
      summary: "等待知识库资料导入。",
      next_action: "进入知识库运营导入业务资料。",
      target_href: "#knowledge",
      blockers: [],
      evidence: []
    },
    {
      code: "retest_confirmation",
      title: "复测确认",
      status: importResult?.ready_for_next_retest ? "ready" : "pending",
      summary: importResult?.summary ?? "等待客户回填确认表。",
      next_action: "导入客户回填确认表。",
      target_href: "#evals",
      blockers: importResult?.blockers ?? [],
      evidence: []
    },
    {
      code: "quality_monthly_ops",
      title: "质量与月报",
      status: report ? "ready" : "pending",
      summary: report?.monthly_health.summary ?? "等待质量复盘和月度运维报告。",
      next_action: "进入质量复盘查看月报。",
      target_href: "#quality",
      blockers: [],
      evidence: []
    },
    {
      code: "diagnostics_backup_update",
      title: "诊断、备份与更新",
      status: maintenance?.ready_for_customer_maintenance_rehearsal ? "ready" : "pending",
      summary: maintenance?.summary ?? "等待诊断包、备份和更新证据。",
      next_action: "进入账号与本地维护补齐证据。",
      target_href: "#settings",
      blockers: maintenance?.blockers ?? [],
      evidence: []
    }
  ];
  const closureEvidenceLabels: Record<string, string> = {
    trial_c0: "试跑范围",
    data1: "资料接收",
    deploy1: "干净部署",
    kb5: "知识复测",
    trial2: "影子试跑",
    fe8: "前端复核",
    pilot7: "封版总门禁",
    fe7: "前端试跑",
    kb4: "知识闭环",
    install5: "本地启动",
    ops3: "运维闭环",
    pack7: "交付档案",
    pack8: "交付档案 v1.1"
  };
  const closureStatusLabel = (status: unknown) => {
    if (typeof status !== "string") return "等待生成";
    if (status === "missing") return "等待生成";
    if (status === "invalid_json") return "证据异常";
    if (status === "blocked") return "存在阻断";
    if (status.includes("ready") || status.includes("passed") || status.includes("candidate")) return "已形成候选";
    return status;
  };
  const trialClosureEvidence = readiness?.pack8_evidence?.length
    ? readiness.pack8_evidence
    : readiness?.trial_closure_evidence ?? [];
  const fiveGapCards = [
    {
      label: "真实资料",
      status: readiness?.real_customer_material_status ?? "not_checked",
      detail: "固定接收清单、脱敏声明和 50-100 条真实问题。"
    },
    {
      label: "回传落位",
      status: readiness?.material_drop_gate_status ?? "not_checked",
      detail: "检查三份固定回传文件是否放到接收目录，并给出下一步校验动作。"
    },
    {
      label: "知识复测",
      status: readiness?.customer_knowledge_retest_status ?? "not_checked",
      detail: "按最终客服答案、引用、禁用承诺和转人工规则复测。"
    },
    {
      label: "影子试跑",
      status: readiness?.shadow_trial_status ?? "not_checked",
      detail: "真实外发关闭，只生成草稿、建议和质量报告。"
    },
    {
      label: "前端验收",
      status: readiness?.frontend_customer_qa_status ?? "not_checked",
      detail: "客户视角二次点击，检查假按钮、重复入口和越界文案。"
    },
    {
      label: "成品体验",
      status: readiness?.frontend_product_polish_status ?? "not_checked",
      detail: "收束排版、状态、空态、错误态和前后端表达一致性。"
    },
    {
      label: "渠道边界",
      status: readiness?.channel_boundary_status ?? "not_checked",
      detail: "只展示官方接入条件、人员配置和未接通原因。"
    },
    {
      label: "安装体验",
      status: readiness?.installer_trial_status ?? "not_checked",
      detail: "桌面启动候选，继续保持签名安装包未完成。"
    },
    {
      label: "交付档案 v2",
      status: readiness?.pack10_status ?? "not_generated",
      detail: "聚合五大缺口证据；客户资料未回传前不生成客户数据包。"
    }
  ];
  const loadSampleMaterials = () => {
    if (!materialTemplatePackage) return;
    setMaterialsCsv(materialTemplatePackage.sample_materials_csv);
    setQuestionsCsv(materialTemplatePackage.sample_trial_questions_csv);
    setManifestJson(materialTemplatePackage.sample_manifest_json);
  };
  const loadTextFileIntoDraft = async (
    event: ChangeEvent<HTMLInputElement>,
    setter: (value: string) => void,
    label: string
  ) => {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) return;
    const lowerName = file.name.toLowerCase();
    const allowed = lowerName.endsWith(".csv") || lowerName.endsWith(".json") || lowerName.endsWith(".txt");
    if (!allowed) {
      setMaterialFileMessage(`${label} 只读取 CSV、JSON 或 TXT 文本文件；XLSX、PDF、DOCX 请先按模板整理后再导入。`);
      return;
    }
    if (file.size > 900_000) {
      setMaterialFileMessage(`${label} 文件超过本地预检上限，请拆分或脱敏压缩后再试。`);
      return;
    }
    const text = await file.text();
    setter(text);
    setMaterialFileMessage(`已读取 ${file.name}，请检查内容后再执行资料预检。`);
  };
  const readBatchString = (record: Record<string, unknown> | null | undefined, key: string) => {
    const value = record?.[key];
    return typeof value === "string" ? value : "";
  };
  const readBatchNumber = (record: Record<string, unknown> | null | undefined, key: string) => {
    const value = record?.[key];
    return typeof value === "number" ? value : 0;
  };
  const downloadMaterialTemplates = () => {
    if (!materialTemplatePackage) return;
    downloadTextFile(
      materialTemplatePackage.materials_template_csv,
      "customer_materials_template.csv",
      "text/csv;charset=utf-8"
    );
    downloadTextFile(
      materialTemplatePackage.trial_questions_template_csv,
      "customer_trial_questions_template.csv",
      "text/csv;charset=utf-8"
    );
    downloadTextFile(
      materialTemplatePackage.manifest_template_json,
      "customer_material_manifest_template.json",
      "application/json;charset=utf-8"
    );
  };

  const templatePackageDisabledTitle = !canImportConfirmation
    ? "当前账号没有资料导入权限，请使用负责人账号或联系负责人授权。"
    : customerMaterialTemplatePackage.status === "loading"
      ? "正在加载资料模板，请稍候。"
      : "加载知识资料、试跑问题和资料说明三份模板。";
  const materialTemplateRequiredTitle = !materialTemplatePackage
    ? "请先点击“加载资料模板”，模板加载后才能使用示例资料和下载模板。"
    : "模板已加载，可以继续操作。";
  const handoffBundleDisabledTitle = !canImportConfirmation
    ? "当前账号没有下载资料回传包权限，请使用负责人账号或联系负责人授权。"
    : customerMaterialHandoffBundle.status === "loading"
      ? "正在生成资料回传包，请稍候。"
      : "下载客户回传所需的三份资料文件包。";
  const materialBatchDisabledTitle = !canImportConfirmation
    ? "当前账号没有查看资料批次权限，请使用负责人账号或联系负责人授权。"
    : customerMaterialBatches.status === "loading"
      ? "正在读取资料批次，请稍候。"
      : "刷新最近的资料预检批次。";
  const materialPrecheckDisabledTitle = !canImportConfirmation
    ? "当前账号没有资料预检权限，请使用负责人账号或联系负责人授权。"
    : customerMaterialPrecheck.status === "loading"
      ? "正在校验资料包，请稍候。"
      : !materialsCsv.trim() || !questionsCsv.trim() || !manifestJson.trim()
        ? "请先填入知识资料、试跑问题和资料说明三份内容。"
        : "开始资料预检。";
  const confirmationImportDisabledTitle = !canImportConfirmation
    ? "当前账号没有导入客户确认表权限，请使用负责人账号或联系负责人授权。"
    : knowledgeConfirmationImport.status === "loading"
      ? "正在校验客户确认表，请稍候。"
      : !confirmationText.trim()
        ? "请先粘贴客户回填后的确认表内容。"
        : "校验客户确认表。";

  return (
    <section className="workspace-page-grid stacked pilot-preparation-page" id="workspace-pilot">
      <article className={`panel pilot-readiness-hero is-${readiness?.status ?? "loading"}`}>
        <div className="panel-heading">
          <div>
            <span className="eyebrow">本地试运行</span>
            <h2>本地试运行准备</h2>
            <p>
              先完成三件事：导入资料、运行复测、导出交付档案。本页只展示本地试运行状态，不代表正式上线或客户验收。
            </p>
          </div>
          <ShieldCheck size={20} />
        </div>
        <div className="pilot-readiness-summary">
          <div>
            <span>当前状态</span>
            <strong>{readiness ? statusLabel[readiness.status] ?? readiness.status : pilotReadiness.message}</strong>
            <small>{readiness?.summary ?? "登录后读取当前租户的本地试运行准备状态。"}</small>
          </div>
          <button type="button" className="secondary-action" onClick={onRefresh}>
            刷新状态
          </button>
        </div>
        <div className="pilot-primary-action-grid" aria-label="本地试运行三步">
          <a href="#pilot-material-precheck">
            <strong>导入资料</strong>
            <span>按模板放入知识资料和问题。</span>
          </a>
          <a href="#evals">
            <strong>运行复测</strong>
            <span>检查答案、引用和转人工边界。</span>
          </a>
          <a href="#pilot-handoff-archive">
            <strong>导出交付档案</strong>
            <span>整理试运行证据和边界说明。</span>
          </a>
        </div>
        {readiness?.not_ready_for.length ? (
          <div className="pilot-boundary-strip">
            {readiness.not_ready_for.slice(0, 5).map((item) => (
              <span key={item}>{item}</span>
            ))}
          </div>
        ) : null}
      </article>

      <article className="panel pilot-readiness-evidence" id="pilot-handoff-archive">
        <div className="panel-heading">
          <div>
            <span className="eyebrow">试跑封版证据</span>
            <h2>{trialClosureStatusLabel[readiness?.trial_closure_status ?? ""] ?? "等待试跑证据"}</h2>
            <p>这里汇总试跑范围、资料接收、干净部署、知识复测、影子试跑、前端复核和交付档案，只展示真实生成的证据状态。</p>
          </div>
          <Archive size={20} />
        </div>
        <div className="pilot-confirmation-metrics">
          {(trialClosureEvidence.length ? trialClosureEvidence : [
            { code: "trial_c0", status: "missing" },
            { code: "data1", status: "missing" },
            { code: "deploy1", status: "missing" },
            { code: "kb5", status: "missing" },
            { code: "trial2", status: "missing" },
            { code: "fe8", status: "missing" },
            { code: "pack8", status: "missing" }
          ]).map((item) => {
            const code = typeof item.code === "string" ? item.code : "unknown";
            return (
              <span key={code}>
                <strong>{closureStatusLabel(item.status)}</strong>
                {closureEvidenceLabels[code] ?? "封版证据"}
              </span>
            );
          })}
        </div>
        <p className="pilot-result-copy">没有生成证据时显示等待生成；不会把内部演练、真实外发或签名安装器写成完成。</p>
        <p className="pilot-result-copy">
          下一轮真实资料：
          {realMaterialStatusLabel[readiness?.real_customer_material_status ?? "not_checked"] ??
            readiness?.real_customer_material_status ??
            "等待资料门禁"}
          。客户资料未回传前，本页保持内部样板候选口径。
        </p>
        <div className="pilot-material-intake-box" aria-label="真实资料接收包说明">
          <div>
            <span className="eyebrow">资料接收包</span>
            <strong>回传三份文件后才进入客户资料试跑</strong>
            <p>
              请先整理知识资料 CSV、试跑问题 CSV 和资料说明 JSON。问题不少于 50 条，必须脱敏，并包含期望答案、来源说明、禁用承诺和转人工规则。
            </p>
            <small>
              当前资料包状态：
              {fiveGapStatusLabel[readiness?.material_intake_package_status ?? "not_checked"] ??
                readiness?.material_intake_package_status ??
                "待生成"}
            </small>
            <small>
              资料门禁校验：
              {fiveGapStatusLabel[readiness?.material_validation_fixture_status ?? "not_checked"] ??
                readiness?.material_validation_fixture_status ??
                "待生成"}
            </small>
            <small>
              回传文件落位：
              {fiveGapStatusLabel[readiness?.material_drop_gate_status ?? "not_checked"] ??
                readiness?.material_drop_gate_status ??
                "待生成"}
            </small>
          </div>
          <ul>
            <li>知识资料 CSV：产品、服务、流程政策、禁用承诺、转人工规则。</li>
            <li>试跑问题 CSV：50-100 条脱敏客户问题和期望动作。</li>
            <li>资料说明 JSON：提供人角色、脱敏声明、真实外发关闭确认。</li>
          </ul>
        </div>
        <div className="pilot-five-gap-grid" aria-label="五大缺口完成状态">
          {fiveGapCards.map((item) => (
            <div key={item.label} className={`pilot-five-gap-card is-${item.status}`}>
              <span>{item.label}</span>
              <strong>{fiveGapStatusLabel[item.status] ?? item.status}</strong>
              <small>{item.detail}</small>
            </div>
          ))}
        </div>
      </article>

      <div className="pilot-step-grid" aria-label="试点准备六步">
        {steps.map((step, index) => (
          <article key={step.code} className={`pilot-step-card is-${step.status}`}>
            <div className="pilot-step-index">{String(index + 1).padStart(2, "0")}</div>
            <div>
              <span>{stepStatusLabel[step.status] ?? step.status}</span>
              <h3>{step.title}</h3>
              <p>{step.summary}</p>
              {step.blockers.length ? (
                <ul>
                  {step.blockers.slice(0, 2).map((blocker) => (
                    <li key={blocker}>{blocker}</li>
                  ))}
                </ul>
              ) : null}
              <a href={step.target_href}>{step.next_action}</a>
            </div>
          </article>
        ))}
      </div>

      <section className="workspace-page-grid two-column">
        <article className="panel pilot-material-precheck-panel" id="pilot-material-precheck">
          <div className="panel-heading">
            <div>
              <span className="eyebrow">资料预检</span>
              <h2>校验试跑资料包</h2>
              <p>先粘贴三份资料做格式和脱敏检查；预检不会保存原始资料，也不会标记为客户确认完成。</p>
            </div>
            <ShieldCheck size={20} />
          </div>
          <div className="pilot-template-box" aria-label="资料模板">
            <div>
              <strong>先拿模板，再准备资料</strong>
              <p>模板包含知识资料、试跑问题和资料说明三份文件。示例只用于熟悉格式，不代表真实客户资料已就绪。</p>
            </div>
            <div className="pilot-template-actions">
              <button
                type="button"
                className="secondary-action"
                disabled={!canImportConfirmation || customerMaterialTemplatePackage.status === "loading"}
                title={templatePackageDisabledTitle}
                aria-label={templatePackageDisabledTitle}
                onClick={onLoadCustomerMaterialTemplatePackage}
              >
                加载资料模板
              </button>
              <button
                type="button"
                className="secondary-action"
                disabled={!materialTemplatePackage}
                title={materialTemplateRequiredTitle}
                aria-label={materialTemplateRequiredTitle}
                onClick={loadSampleMaterials}
              >
                填入示例资料
              </button>
              <button
                type="button"
                className="secondary-action"
                disabled={!materialTemplatePackage}
                title={materialTemplateRequiredTitle}
                aria-label={materialTemplateRequiredTitle}
                onClick={downloadMaterialTemplates}
              >
                下载三份模板
              </button>
              <button
                type="button"
                className="secondary-action"
                disabled={!canImportConfirmation || customerMaterialHandoffBundle.status === "loading"}
                title={handoffBundleDisabledTitle}
                aria-label={handoffBundleDisabledTitle}
                onClick={onDownloadCustomerMaterialHandoffBundle}
              >
                下载回传文件包
              </button>
              <button
                type="button"
                className="secondary-action"
                disabled={!canImportConfirmation || customerMaterialBatches.status === "loading"}
                title={materialBatchDisabledTitle}
                aria-label={materialBatchDisabledTitle}
                onClick={onLoadCustomerMaterialBatches}
              >
                刷新资料批次
              </button>
            </div>
          </div>
          {customerMaterialBatches.status !== "idle" ? (
            <PanelStateNotice
              status={customerMaterialBatches.status}
              message={customerMaterialBatches.message}
              loadingMessage="正在读取资料批次。"
              compact
            />
          ) : null}
          {customerMaterialTemplatePackage.status !== "idle" ? (
            <PanelStateNotice
              status={customerMaterialTemplatePackage.status}
              message={customerMaterialTemplatePackage.message}
              loadingMessage="正在加载资料模板。"
              compact
            />
          ) : null}
          {customerMaterialHandoffBundle.status !== "idle" ? (
            <PanelStateNotice
              status={customerMaterialHandoffBundle.status}
              message={customerMaterialHandoffBundle.message}
              loadingMessage="正在生成资料回传包。"
              compact
            />
          ) : null}
          {materialTemplatePackage ? (
            <div className="pilot-field-guide" aria-label="资料字段说明">
              <div className="pilot-field-guide-heading">
                <strong>字段说明</strong>
                <span>
                  接收文件：
                  {Object.values(materialTemplatePackage.required_received_filenames).join("、")}
                </span>
              </div>
              <div className="pilot-field-guide-grid">
                {materialTemplatePackage.field_guide.slice(0, 8).map((item) => (
                  <div key={`${item.file}-${item.field}`} className="pilot-field-guide-item">
                    <span>{item.required ? "必填" : "可选"}</span>
                    <strong>{item.field}</strong>
                    <p>{item.description}</p>
                    {item.example ? <small>示例：{item.example}</small> : null}
                  </div>
                ))}
              </div>
            </div>
          ) : null}
          <label>
            知识资料 CSV
            <textarea
              value={materialsCsv}
              onChange={(event) => setMaterialsCsv(event.target.value)}
              placeholder="粘贴知识资料 CSV：业务对象、标准问答、流程政策、禁用承诺、转人工规则"
              rows={5}
              disabled={!canImportConfirmation || customerMaterialPrecheck.status === "loading"}
            />
            <div className="pilot-file-loader">
              <span>从本地 CSV 填入</span>
              <input
                type="file"
                accept=".csv,text/csv,text/plain"
                aria-label="从本地 CSV 填入知识资料"
                title="从本地 CSV 填入知识资料"
                disabled={!canImportConfirmation || customerMaterialPrecheck.status === "loading"}
                onChange={(event) => void loadTextFileIntoDraft(event, setMaterialsCsv, "知识资料")}
              />
            </div>
          </label>
          <label>
            试跑问题 CSV
            <textarea
              value={questionsCsv}
              onChange={(event) => setQuestionsCsv(event.target.value)}
              placeholder="粘贴 50-100 条脱敏问题、期望答案、期望动作和引用来源"
              rows={5}
              disabled={!canImportConfirmation || customerMaterialPrecheck.status === "loading"}
            />
            <div className="pilot-file-loader">
              <span>从本地 CSV 填入</span>
              <input
                type="file"
                accept=".csv,text/csv,text/plain"
                aria-label="从本地 CSV 填入试跑问题"
                title="从本地 CSV 填入试跑问题"
                disabled={!canImportConfirmation || customerMaterialPrecheck.status === "loading"}
                onChange={(event) => void loadTextFileIntoDraft(event, setQuestionsCsv, "试跑问题")}
              />
            </div>
          </label>
          <label>
            资料说明 JSON
            <textarea
              value={manifestJson}
              onChange={(event) => setManifestJson(event.target.value)}
              placeholder='{"provided_by_role":"负责人","desensitization_owner_role":"运营负责人","desensitization_statement":"资料已脱敏","customer_data_used":true,"real_platform_send_enabled":false}'
              rows={5}
              disabled={!canImportConfirmation || customerMaterialPrecheck.status === "loading"}
            />
            <div className="pilot-file-loader">
              <span>从本地 JSON 填入</span>
              <input
                type="file"
                accept=".json,application/json,text/plain"
                aria-label="从本地 JSON 填入资料说明"
                title="从本地 JSON 填入资料说明"
                disabled={!canImportConfirmation || customerMaterialPrecheck.status === "loading"}
                onChange={(event) => void loadTextFileIntoDraft(event, setManifestJson, "资料说明")}
              />
            </div>
          </label>
          {materialFileMessage ? <p className="pilot-result-copy compact">{materialFileMessage}</p> : null}
          <button
            type="button"
            className="primary-action"
            disabled={
              !canImportConfirmation ||
              customerMaterialPrecheck.status === "loading" ||
              !materialsCsv.trim() ||
              !questionsCsv.trim() ||
              !manifestJson.trim()
            }
            onClick={() => onPrecheckCustomerMaterials(materialsCsv, questionsCsv, manifestJson)}
            title={materialPrecheckDisabledTitle}
            aria-label={materialPrecheckDisabledTitle}
          >
            开始资料预检
          </button>
          {customerMaterialPrecheck.status !== "idle" ? (
            <PanelStateNotice
              status={customerMaterialPrecheck.status}
              message={customerMaterialPrecheck.message}
              loadingMessage="正在校验资料包。"
            />
          ) : null}
        </article>

        <article className="panel pilot-material-precheck-result">
          <div className="panel-heading">
            <div>
              <span className="eyebrow">预检结果</span>
              <h2>资料接收状态</h2>
              <p>通过预检后，仍需把资料放入固定接收目录，再进入正式资料门禁。</p>
            </div>
            <ClipboardCheck size={20} />
          </div>
          {materialPrecheckResult ? (
            <>
              <div className="pilot-confirmation-metrics">
                <span>
                  <strong>{Number(materialPrecheckResult.metrics.material_rows ?? 0)}</strong>
                  资料行
                </span>
                <span>
                  <strong>{Number(materialPrecheckResult.metrics.trial_question_count ?? 0)}</strong>
                  试跑问题
                </span>
                <span>
                  <strong>{(materialPrecheckResult.metrics.record_types ?? []).length}</strong>
                  知识类型
                </span>
                <span>
                  <strong>{materialPrecheckResult.blockers.length}</strong>
                  阻断项
                </span>
              </div>
              {materialPrecheckResult.blockers.length ? (
                <ul className="pilot-result-list">
                  {materialPrecheckResult.blockers.slice(0, 6).map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              ) : (
                <p className="pilot-result-copy">{materialPrecheckResult.summary}</p>
              )}
              <small className="pilot-boundary-note">
                原始资料未保存；真实外发关闭；正式确认仍需客户回填确认表。
              </small>
            </>
          ) : (
            <div className="empty-state">
              <ShieldCheck size={22} />
              <strong>等待资料包预检</strong>
              <span>先检查字段、脱敏、禁用承诺和转人工规则，再进入正式接收目录。</span>
            </div>
          )}
          <div className="pilot-batch-history" aria-label="资料批次历史">
            <div className="pilot-batch-heading">
              <div>
                <strong>资料批次</strong>
                <span>{materialBatchList?.summary ?? "刷新后查看最近的资料预检批次。"}</span>
              </div>
              <button
                type="button"
                className="ghost-action"
                disabled={!canImportConfirmation || customerMaterialBatches.status === "loading"}
                title={materialBatchDisabledTitle}
                aria-label={materialBatchDisabledTitle}
                onClick={onLoadCustomerMaterialBatches}
              >
                刷新
              </button>
            </div>
            {latestMaterialBatch ? (
              <div className={`pilot-latest-batch is-${readBatchString(latestMaterialBatch, "status")}`}>
                <span>{batchStatusLabel[readBatchString(latestMaterialBatch, "status")] ?? readBatchString(latestMaterialBatch, "status")}</span>
                <strong>{readBatchString(latestMaterialBatch, "batch_code")}</strong>
                <small>
                  资料 {readBatchNumber(latestMaterialBatch, "material_row_count")} 行 · 问题{" "}
                  {readBatchNumber(latestMaterialBatch, "question_count")} 条 · 阻断{" "}
                  {readBatchNumber(latestMaterialBatch, "blocker_count")} 项 · 风险{" "}
                  {readBatchNumber(latestMaterialBatch, "desensitization_risk_count")} 项
                </small>
              </div>
            ) : (
              <p className="pilot-result-copy compact">暂无资料批次。请先加载模板、准备资料并执行预检。</p>
            )}
            {materialBatchList?.batches?.length ? (
              <div className="pilot-batch-list">
                {materialBatchList.batches.slice(0, 5).map((batch) => {
                  const id = readBatchNumber(batch, "id");
                  const statusValue = readBatchString(batch, "status");
                  return (
                    <div key={`${id}-${readBatchString(batch, "batch_code")}`} className="pilot-batch-row">
                      <span>{batchStatusLabel[statusValue] ?? statusValue}</span>
                      <strong>{readBatchString(batch, "batch_code")}</strong>
                      <small>
                        资料 {readBatchNumber(batch, "material_row_count")} / 问题{" "}
                        {readBatchNumber(batch, "question_count")} / 阻断{" "}
                        {readBatchNumber(batch, "blocker_count")} / 风险{" "}
                        {readBatchNumber(batch, "desensitization_risk_count")}
                      </small>
                    </div>
                  );
                })}
              </div>
            ) : null}
            <small className="pilot-boundary-note">批次列表只显示统计和状态；不返回客户原文、标准答案全文、密钥或平台消息。</small>
          </div>
        </article>
      </section>

      <section className="workspace-page-grid two-column">
        <article className="panel pilot-confirmation-panel" id="pilot-confirmation-import">
          <div className="panel-heading">
            <div>
              <span className="eyebrow">复测确认</span>
              <h2>导入客户确认表</h2>
              <p>只接受客户回填的确认表；系统不会替客户填写确认人、确认时间或同意状态。</p>
            </div>
            <FileText size={20} />
          </div>
          <label>
            文件名
            <input
              value={confirmationFilename}
              onChange={(event) => setConfirmationFilename(event.target.value)}
              placeholder="customer_knowledge_confirmation.csv"
              disabled={!canImportConfirmation || knowledgeConfirmationImport.status === "loading"}
            />
          </label>
          <label>
            CSV 内容
            <textarea
              value={confirmationText}
              onChange={(event) => setConfirmationText(event.target.value)}
              placeholder="粘贴客户回填后的确认表内容"
              rows={8}
              disabled={!canImportConfirmation || knowledgeConfirmationImport.status === "loading"}
            />
          </label>
          <button
            type="button"
            className="primary-action"
            disabled={!canImportConfirmation || knowledgeConfirmationImport.status === "loading" || !confirmationText.trim()}
            title={confirmationImportDisabledTitle}
            aria-label={confirmationImportDisabledTitle}
            onClick={() => onImportKnowledgeConfirmation(confirmationFilename, confirmationText)}
          >
            校验确认表
          </button>
          {knowledgeConfirmationImport.status !== "idle" ? (
            <PanelStateNotice
              status={knowledgeConfirmationImport.status}
              message={knowledgeConfirmationImport.message}
              loadingMessage="正在校验客户确认表。"
            />
          ) : null}
        </article>

        <article className="panel pilot-confirmation-result">
          <div className="panel-heading">
            <div>
              <span className="eyebrow">确认结果</span>
              <h2>复测入口状态</h2>
              <p>确认结果只作为下一轮复测依据，不代表正式客户验收。</p>
            </div>
            <CheckCircle2 size={20} />
          </div>
          {importResult ? (
            <>
              <div className="pilot-confirmation-metrics">
                <span>
                  <strong>{importResult.confirmed_count}</strong>
                  已确认
                </span>
                <span>
                  <strong>{importResult.needs_revision_count}</strong>
                  需修订
                </span>
                <span>
                  <strong>{importResult.rejected_count}</strong>
                  已拒绝
                </span>
                <span>
                  <strong>{importResult.pending_count}</strong>
                  待确认
                </span>
              </div>
              {importResult.blockers.length ? (
                <ul className="pilot-result-list">
                  {importResult.blockers.slice(0, 4).map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              ) : (
                <p className="pilot-result-copy">{importResult.summary}</p>
              )}
            </>
          ) : (
            <div className="empty-state">
              <FileText size={22} />
              <strong>等待客户确认表</strong>
              <span>客户回填后再导入；没有回填文件时不会标记为已确认。</span>
            </div>
          )}
        </article>
      </section>
    </section>
  );
}

function AccountManagementPanel({
  state,
  diagnosticExport,
  diagnosticIntake,
  diagnosticRemediation,
  localMaintenanceReadiness,
  localBackupState,
  localRestoreDryRun,
  signedUpdatePreflight,
  signedUpdateStage,
  currentUser,
  hasToken,
  onCreateUser,
  onUpdateUserStatus,
  onResetUserPassword,
  onExportDiagnosticBundle,
  onCreateDiagnosticUploadPackage,
  onCreateDiagnosticIntakeRecord,
  onUpdateDiagnosticIntakeRecord,
  onDownloadDiagnosticIntakeRecord,
  onCreateDiagnosticRemediationRequest,
  onUpdateDiagnosticRemediationRequest,
  onDownloadDiagnosticRemediationRequest,
  onCreateDiagnosticRemediationUpdatePlan,
  onCreateLocalBackup,
  onVerifyLocalBackup,
  onCreateLocalBackupRestoreDryRun,
  onPreflightSignedUpdatePackage,
  onStageSignedUpdatePackage,
  onApplySignedUpdatePackage,
  onCreateProgramUpdateDryRun,
  onRollbackSignedUpdatePackage,
  onRefresh
}: {
  state: AccountManagementState;
  diagnosticExport: DiagnosticExportState;
  diagnosticIntake: DiagnosticIntakeState;
  diagnosticRemediation: DiagnosticRemediationState;
  localMaintenanceReadiness: LocalMaintenanceReadinessState;
  localBackupState: LocalBackupState;
  localRestoreDryRun: LocalBackupRestoreDryRun | null;
  signedUpdatePreflight: SignedUpdatePreflightState;
  signedUpdateStage: SignedUpdateStageState;
  currentUser: CurrentUser | null;
  hasToken: boolean;
  onCreateUser: (payload: { name: string; email: string; password: string; roleId: number | null }) => Promise<void>;
  onUpdateUserStatus: (user: AccountUser, status: "active" | "inactive") => Promise<void>;
  onResetUserPassword: (user: AccountUser, newPassword: string) => Promise<void>;
  onExportDiagnosticBundle: () => Promise<void>;
  onCreateDiagnosticUploadPackage: () => Promise<void>;
  onCreateDiagnosticIntakeRecord: (uploadPackageText: string) => Promise<void>;
  onUpdateDiagnosticIntakeRecord: (record: DiagnosticIntakeRecord, status: string, note: string) => Promise<void>;
  onDownloadDiagnosticIntakeRecord: (record: DiagnosticIntakeRecord) => Promise<void>;
  onCreateDiagnosticRemediationRequest: (record: DiagnosticIntakeRecord) => Promise<void>;
  onUpdateDiagnosticRemediationRequest: (request: DiagnosticRemediationRequest, status: string) => Promise<void>;
  onDownloadDiagnosticRemediationRequest: (request: DiagnosticRemediationRequest) => Promise<void>;
  onCreateDiagnosticRemediationUpdatePlan: (
    request: DiagnosticRemediationRequest,
    packageItem: SignedUpdateStagedPackage
  ) => Promise<void>;
  onCreateLocalBackup: () => Promise<void>;
  onVerifyLocalBackup: (backup: LocalBackupRecord) => Promise<void>;
  onCreateLocalBackupRestoreDryRun: (backup: LocalBackupRecord) => Promise<void>;
  onPreflightSignedUpdatePackage: (rawPackageText: string) => Promise<void>;
  onStageSignedUpdatePackage: (rawPackageText: string) => Promise<void>;
  onApplySignedUpdatePackage: (packageItem: SignedUpdateStagedPackage) => Promise<void>;
  onCreateProgramUpdateDryRun: (packageItem: SignedUpdateStagedPackage) => Promise<void>;
  onRollbackSignedUpdatePackage: (packageItem: SignedUpdateStagedPackage) => Promise<void>;
  onRefresh: () => void;
}) {
  const canManage = hasToken && canManageAccounts(currentUser);
  const canExportDiagnostics = hasToken && canReadOpsMetrics(currentUser);
  const canManageUpdates = hasToken && canManageSignedUpdates(currentUser);
  const defaultRoleId = String(
    state.roles.find((role) => role.code === "agent")?.id ?? state.roles[0]?.id ?? ""
  );
  const [draft, setDraft] = useState({ name: "", email: "", password: "", roleId: "" });
  const [resetDraft, setResetDraft] = useState({ userId: "", password: "" });
  const [signedUpdateText, setSignedUpdateText] = useState(DEFAULT_SIGNED_UPDATE_PACKAGE_TEXT);
  const [diagnosticIntakeText, setDiagnosticIntakeText] = useState("");
  const [diagnosticIntakeNote, setDiagnosticIntakeNote] = useState("");
  const [remediationPlanSelection, setRemediationPlanSelection] = useState<Record<number, string>>({});
  const [localError, setLocalError] = useState("");
  const isLoading = state.status === "loading";

  useEffect(() => {
    if (!draft.roleId && defaultRoleId) {
      setDraft((current) => ({ ...current, roleId: defaultRoleId }));
    }
  }, [defaultRoleId, draft.roleId]);

  const activeUsers = state.users.filter((user) => user.status === "active").length;
  const ownerUsers = state.users.filter((user) => accountUserRoles(user).includes("owner")).length;
  const inactiveUsers = state.users.filter((user) => user.status !== "active").length;
  const resetTarget = state.users.find((user) => String(user.id) === resetDraft.userId) ?? null;
  const selectedRoleId = draft.roleId ? Number(draft.roleId) : null;
  const message =
    state.status === "idle" || state.status === "error" || state.status === "loading" ? state.message : state.message ?? "";
  const signedUpdateResult = signedUpdatePreflight.result;
  const signedUpdateSignatureOk = signedUpdateResult?.signature_status["verified"] === true;
  const signedUpdateChecksumOk = signedUpdateResult?.checksum_status["payload_digest_match"] === true;
  const signedUpdateCompatible = signedUpdateResult?.compatibility["compatible"] === true;
  const signedUpdateBackupResources = Array.isArray(signedUpdateResult?.backup_plan["resources"])
    ? signedUpdateResult.backup_plan["resources"].map((item) => String(item))
    : [];
  const maintenanceReadiness = localMaintenanceReadiness.data;
  const maintenanceCounts = maintenanceReadiness?.counts ?? {};
  const maintenancePrimaryGates =
    maintenanceReadiness?.gates.filter((gate) =>
      ["diagnostic_intake", "remediation_request", "signed_update_plan", "local_backup", "restore_dry_run"].includes(
        gate.code
      )
    ) ?? [];

  async function exportBundle() {
    setLocalError("");
    try {
      await onExportDiagnosticBundle();
    } catch (error) {
      setLocalError(error instanceof Error ? error.message : "生成诊断包失败");
    }
  }

  async function createDiagnosticUpload() {
    setLocalError("");
    try {
      await onCreateDiagnosticUploadPackage();
    } catch (error) {
      setLocalError(error instanceof Error ? error.message : "生成授权上传包失败");
    }
  }

  async function submitDiagnosticIntake(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLocalError("");
    if (!diagnosticIntakeText.trim()) {
      setLocalError("请粘贴客户主动提供的授权上传包 JSON。");
      return;
    }
    try {
      await onCreateDiagnosticIntakeRecord(diagnosticIntakeText);
      setDiagnosticIntakeText("");
    } catch (error) {
      setLocalError(error instanceof Error ? error.message : "登记售后接收记录失败");
    }
  }

  async function updateDiagnosticIntake(record: DiagnosticIntakeRecord, status: string) {
    setLocalError("");
    try {
      await onUpdateDiagnosticIntakeRecord(record, status, diagnosticIntakeNote);
      setDiagnosticIntakeNote("");
    } catch (error) {
      setLocalError(error instanceof Error ? error.message : "更新售后接收记录失败");
    }
  }

  async function downloadDiagnosticIntake(record: DiagnosticIntakeRecord) {
    setLocalError("");
    try {
      await onDownloadDiagnosticIntakeRecord(record);
    } catch (error) {
      setLocalError(error instanceof Error ? error.message : "下载售后接收包失败");
    }
  }

  async function createDiagnosticRemediation(record: DiagnosticIntakeRecord) {
    setLocalError("");
    try {
      await onCreateDiagnosticRemediationRequest(record);
    } catch (error) {
      setLocalError(error instanceof Error ? error.message : "生成售后处理单失败");
    }
  }

  async function updateDiagnosticRemediation(request: DiagnosticRemediationRequest, status: string) {
    setLocalError("");
    try {
      await onUpdateDiagnosticRemediationRequest(request, status);
    } catch (error) {
      setLocalError(error instanceof Error ? error.message : "更新售后处理单失败");
    }
  }

  async function downloadDiagnosticRemediation(request: DiagnosticRemediationRequest) {
    setLocalError("");
    try {
      await onDownloadDiagnosticRemediationRequest(request);
    } catch (error) {
      setLocalError(error instanceof Error ? error.message : "下载售后处理包失败");
    }
  }

  async function createRemediationUpdatePlan(request: DiagnosticRemediationRequest) {
    setLocalError("");
    const selectedPackageId = remediationPlanSelection[request.id] || String(signedUpdateStage.packages[0]?.id ?? "");
    const packageItem = signedUpdateStage.packages.find((item) => String(item.id) === selectedPackageId) ?? null;
    if (!packageItem) {
      setLocalError("请先在下方暂存一个签名更新包，再生成受控更新计划。");
      return;
    }
    try {
      await onCreateDiagnosticRemediationUpdatePlan(request, packageItem);
    } catch (error) {
      setLocalError(error instanceof Error ? error.message : "生成受控更新计划失败");
    }
  }

  async function createBackup() {
    setLocalError("");
    try {
      await onCreateLocalBackup();
    } catch (error) {
      setLocalError(error instanceof Error ? error.message : "创建本地备份点失败");
    }
  }

  async function verifyBackup(backup: LocalBackupRecord) {
    setLocalError("");
    try {
      await onVerifyLocalBackup(backup);
    } catch (error) {
      setLocalError(error instanceof Error ? error.message : "校验本地备份点失败");
    }
  }

  async function createRestoreDryRun(backup: LocalBackupRecord) {
    setLocalError("");
    try {
      await onCreateLocalBackupRestoreDryRun(backup);
    } catch (error) {
      setLocalError(error instanceof Error ? error.message : "生成本地恢复演练失败");
    }
  }

  async function submitSignedUpdatePreflight(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLocalError("");
    if (!signedUpdateText.trim()) {
      setLocalError("请粘贴 .wanfa-update 更新包 JSON 内容。");
      return;
    }
    try {
      await onPreflightSignedUpdatePackage(signedUpdateText);
    } catch (error) {
      setLocalError(error instanceof Error ? error.message : "签名更新包预检失败");
    }
  }

  async function stageCurrentSignedUpdatePackage() {
    setLocalError("");
    if (!signedUpdateText.trim()) {
      setLocalError("请粘贴 .wanfa-update 更新包 JSON 内容。");
      return;
    }
    try {
      await onStageSignedUpdatePackage(signedUpdateText);
    } catch (error) {
      setLocalError(error instanceof Error ? error.message : "签名更新包暂存失败");
    }
  }

  async function submitCreate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLocalError("");
    if (!draft.name.trim() || !draft.email.trim() || draft.password.length < 8) {
      setLocalError("请填写姓名、邮箱，并设置至少 8 位密码。");
      return;
    }
    try {
      await onCreateUser({
        name: draft.name.trim(),
        email: draft.email.trim(),
        password: draft.password,
        roleId: selectedRoleId
      });
      setDraft({ name: "", email: "", password: "", roleId: defaultRoleId });
    } catch (error) {
      setLocalError(error instanceof Error ? error.message : "创建人员账号失败");
    }
  }

  async function submitReset(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLocalError("");
    if (!resetTarget || resetDraft.password.length < 8) {
      setLocalError("请选择人员，并设置至少 8 位新密码。");
      return;
    }
    try {
      await onResetUserPassword(resetTarget, resetDraft.password);
      setResetDraft({ userId: "", password: "" });
    } catch (error) {
      setLocalError(error instanceof Error ? error.message : "重置密码失败");
    }
  }

  async function applySignedUpdatePackage(item: SignedUpdateStagedPackage) {
    setLocalError("");
    try {
      await onApplySignedUpdatePackage(item);
    } catch (error) {
      setLocalError(error instanceof Error ? error.message : "应用签名更新包失败");
    }
  }

  async function createProgramDryRun(item: SignedUpdateStagedPackage) {
    setLocalError("");
    try {
      await onCreateProgramUpdateDryRun(item);
    } catch (error) {
      setLocalError(error instanceof Error ? error.message : "生成程序更新演练计划失败");
    }
  }

  async function rollbackSignedUpdatePackage(item: SignedUpdateStagedPackage) {
    setLocalError("");
    try {
      await onRollbackSignedUpdatePackage(item);
    } catch (error) {
      setLocalError(error instanceof Error ? error.message : "回滚签名更新包失败");
    }
  }

  function formatSignedUpdateStatus(status: string) {
    const labels: Record<string, string> = {
      staged: "待应用",
      applied: "已应用",
      rolled_back: "已回滚",
      failed: "失败"
    };
    return labels[status] ?? status;
  }

  function formatSignedUpdateType(type: SignedUpdateStagedPackage["package_type"]) {
    const labels: Record<SignedUpdateStagedPackage["package_type"], string> = {
      knowledge: "知识包",
      strategy: "策略包",
      program: "程序包"
    };
    return labels[type];
  }

  function formatDiagnosticIntakeStatus(status: string) {
    const labels: Record<string, string> = {
      received: "已接收",
      in_review: "处理中",
      resolved: "已结束",
      rejected: "已拒收"
    };
    return labels[status] ?? status;
  }

  function formatDiagnosticRemediationStatus(status: string) {
    const labels: Record<string, string> = {
      draft: "待复核",
      in_review: "处理中",
      ready_for_customer: "待客户确认",
      update_plan_prepared: "已生成更新计划",
      delivered: "已回传",
      closed: "已关闭",
      cancelled: "已取消"
    };
    return labels[status] ?? status;
  }

  function formatSignedUpdatePlanStepStatus(status: string) {
    const labels: Record<string, string> = {
      passed: "已通过",
      ready: "待确认",
      planned: "待执行",
      blocked: "阻断",
      dry_run_only: "仅演练",
      manual_only: "人工处理"
    };
    return labels[status] ?? status;
  }

  function formatLocalMaintenanceMaturity(status: string) {
    const labels: Record<string, string> = {
      ready_for_rehearsal: "可进入维护演练",
      missing_evidence: "证据不足",
      blocked: "存在阻断"
    };
    return labels[status] ?? status;
  }

  function formatLocalMaintenanceGateStatus(status: string) {
    const labels: Record<string, string> = {
      ready: "可用",
      passed: "已验证",
      warning: "需复核",
      pending: "待补齐",
      blocked: "阻断"
    };
    return labels[status] ?? status;
  }

  return (
    <article className="panel account-management-panel" id="workspace-settings">
      <div className="panel-heading">
        <div>
          <span className="eyebrow">本地治理</span>
          <h2>账号与本地维护</h2>
          <p>负责人在这里管理本地账号、诊断包、备份、更新包和恢复演练。所有维护动作都需要人工确认和审计记录。</p>
        </div>
        <Users size={20} />
      </div>

      {message && canManage ? (
        <PanelStateNotice status={state.status} message={message} loadingMessage="正在同步本地账号与角色。" />
      ) : null}

      {!canManage && !canExportDiagnostics ? (
        <div className="empty-state">
          <ShieldCheck size={22} />
          <strong>当前账号没有人员管理权限</strong>
          <span>请使用负责人账号登录，或由负责人授予账号管理、运维指标权限。</span>
        </div>
      ) : null}

      {!canManage && canExportDiagnostics ? (
        <div className="empty-state">
          <ShieldCheck size={22} />
          <strong>当前账号可导出诊断包</strong>
          <span>人员新增、停用和重置密码仍需要负责人权限。</span>
        </div>
      ) : null}

      {canManageUpdates ? (
        <section
          className={`local-maintenance-card is-${maintenanceReadiness?.maturity_status ?? "unknown"}`}
          aria-label="本地维护闭环"
          data-h2w8b-local-maintenance="p3-06u-26h2w8b"
        >
          <div className="local-maintenance-heading">
            <div>
              <span>本地维护闭环</span>
              <strong>
                {maintenanceReadiness
                  ? formatLocalMaintenanceMaturity(maintenanceReadiness.maturity_status)
                  : localMaintenanceReadiness.message}
              </strong>
              <small>
                {maintenanceReadiness
                  ? maintenanceReadiness.summary
                  : "用于汇总诊断接收、处理单、签名更新、备份、恢复演练和审计证据。"}
              </small>
            </div>
            <span className={maintenanceReadiness?.ready_for_customer_maintenance_rehearsal ? "is-good" : "is-warning"}>
              {maintenanceReadiness?.ready_for_customer_maintenance_rehearsal ? "证据完整" : "继续补证据"}
            </span>
          </div>
          <a className="local-maintenance-report-link" href="#quality?focus=monthly-ops-report">
            查看本月运维报告
          </a>
          <a className="local-maintenance-report-link" href="#pilot">
            进入本地试运行准备
          </a>
          <div className="local-maintenance-metrics">
            <span>
              <strong>{maintenanceCounts.diagnostic_intake_accepted ?? 0}</strong>
              接收
            </span>
            <span>
              <strong>{maintenanceCounts.remediation_update_plan_prepared ?? 0}</strong>
              更新计划
            </span>
            <span>
              <strong>{maintenanceCounts.signed_update_package_total ?? 0}</strong>
              更新包
            </span>
            <span>
              <strong>{maintenanceCounts.local_backup_verified ?? 0}</strong>
              已验备份
            </span>
            <span>
              <strong>{maintenanceCounts.restore_dry_run_total ?? 0}</strong>
              恢复演练
            </span>
          </div>
          {maintenancePrimaryGates.length > 0 ? (
            <div className="local-maintenance-gates">
              {maintenancePrimaryGates.map((gate) => (
                <span key={gate.code} className={`is-${gate.status}`}>
                  {gate.label} · {formatLocalMaintenanceGateStatus(gate.status)}
                </span>
              ))}
            </div>
          ) : null}
          {maintenanceReadiness?.blockers.length ? (
            <ul className="local-maintenance-blockers">
              {maintenanceReadiness.blockers.slice(0, 4).map((blocker) => (
                <li key={blocker}>{blocker}</li>
              ))}
            </ul>
          ) : maintenanceReadiness?.recommended_next_steps.length ? (
            <div className="local-maintenance-next">
              {maintenanceReadiness.recommended_next_steps.slice(0, 3).map((step) => (
                <span key={step}>{step}</span>
              ))}
            </div>
          ) : null}
        </section>
      ) : null}

      {canManage ? (
        <>
          <div className="account-summary-grid" aria-label="账号治理摘要">
            <div className="account-summary-card">
              <span>全部账号</span>
              <strong>{state.users.length}</strong>
            </div>
            <div className="account-summary-card">
              <span>启用中</span>
              <strong>{activeUsers}</strong>
            </div>
            <div className="account-summary-card">
              <span>负责人</span>
              <strong>{ownerUsers}</strong>
            </div>
            <div className="account-summary-card">
              <span>已停用</span>
              <strong>{inactiveUsers}</strong>
            </div>
          </div>

          <div className="account-management-grid">
            <form className="account-form" onSubmit={(event) => void submitCreate(event)}>
              <div className="subsection-heading">
                <div>
                  <h3>新增人员</h3>
                  <p>用于给客服、运营或负责人创建本地登录账号。</p>
                </div>
                <UserPlus size={18} />
              </div>
              <label>
                姓名
                <input
                  value={draft.name}
                  onChange={(event) => setDraft((current) => ({ ...current, name: event.target.value }))}
                  placeholder="例如：客服小张"
                  disabled={isLoading}
                />
              </label>
              <label>
                邮箱
                <input
                  type="email"
                  value={draft.email}
                  onChange={(event) => setDraft((current) => ({ ...current, email: event.target.value }))}
                  placeholder="name@example.com"
                  disabled={isLoading}
                />
              </label>
              <label>
                初始密码
                <input
                  type="password"
                  value={draft.password}
                  onChange={(event) => setDraft((current) => ({ ...current, password: event.target.value }))}
                  placeholder="至少 8 位"
                  minLength={8}
                  disabled={isLoading}
                />
              </label>
              <label>
                角色
                <select
                  value={draft.roleId}
                  onChange={(event) => setDraft((current) => ({ ...current, roleId: event.target.value }))}
                  disabled={isLoading || state.roles.length === 0}
                >
                  {state.roles.length === 0 ? <option value="">暂无角色</option> : null}
                  {state.roles.map((role) => (
                    <option key={role.id} value={String(role.id)}>
                      {formatAccountRoleName(role.code, role.name)}
                    </option>
                  ))}
                </select>
              </label>
              <button type="submit" className="primary-action" disabled={isLoading}>
                创建账号
              </button>
            </form>

            <form className="account-form" onSubmit={(event) => void submitReset(event)}>
              <div className="subsection-heading">
                <div>
                  <h3>重置密码</h3>
                  <p>人员忘记密码或交接账号时使用；重置后旧会话会失效。</p>
                </div>
                <KeyRound size={18} />
              </div>
              <label>
                人员
                <select
                  value={resetDraft.userId}
                  onChange={(event) => setResetDraft((current) => ({ ...current, userId: event.target.value }))}
                  disabled={isLoading || state.users.length === 0}
                >
                  <option value="">选择人员</option>
                  {state.users.map((user) => (
                    <option key={user.id} value={String(user.id)}>
                      {user.name} · {user.email}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                新密码
                <input
                  type="password"
                  value={resetDraft.password}
                  onChange={(event) => setResetDraft((current) => ({ ...current, password: event.target.value }))}
                  placeholder="至少 8 位"
                  minLength={8}
                  disabled={isLoading}
                />
              </label>
              <button
                type="submit"
                className="ghost-action"
                disabled={isLoading || !resetDraft.userId}
                title={
                  isLoading
                    ? "正在同步账号数据，请稍候。"
                    : !resetDraft.userId
                      ? "请先选择需要重置密码的人员。"
                      : "重置所选人员密码，重置后旧会话会失效。"
                }
                aria-label={
                  isLoading
                    ? "重置密码不可用，正在同步账号数据"
                    : !resetDraft.userId
                      ? "重置密码不可用，请先选择人员"
                      : "重置所选人员密码"
                }
              >
                重置密码
              </button>
              <button type="button" className="ghost-action" onClick={onRefresh} disabled={isLoading}>
                刷新账号
              </button>
            </form>
          </div>

          <div className="account-table-wrap">
            <table className="account-table">
              <thead>
                <tr>
                  <th>人员</th>
                  <th>角色</th>
                  <th>状态</th>
                  <th>创建时间</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                {state.users.map((user) => {
                  const nextStatus = user.status === "active" ? "inactive" : "active";
                  const isSelf = currentUser?.id === String(user.id);
                  const wouldDisableLastOwner = isSelf && accountUserRoles(user).includes("owner") && ownerUsers <= 1;
                  return (
                    <tr key={user.id}>
                      <td>
                        <strong>{user.name}</strong>
                        <span>{user.email}</span>
                      </td>
                      <td>
                        <div className="role-chip-list">
                          {accountUserRoles(user).length > 0 ? (
                            accountUserRoles(user).map((role) => <span key={role}>{formatRoleCodeLabel(role)}</span>)
                          ) : (
                            <span>未分配</span>
                          )}
                        </div>
                      </td>
                      <td>
                        <span className={`status-pill ${user.status === "active" ? "is-good" : "is-muted"}`}>
                          {user.status === "active" ? "启用中" : "已停用"}
                        </span>
                      </td>
                      <td>{formatDateTime(user.created_at)}</td>
                      <td>
                        <button
                          type="button"
                          className="ghost-action"
                          onClick={() => void onUpdateUserStatus(user, nextStatus)}
                          disabled={isLoading || wouldDisableLastOwner}
                          title={
                            isLoading
                              ? "正在同步账号数据，请稍候。"
                              : wouldDisableLastOwner
                                ? "不能停用当前唯一负责人账号，请先创建或指定另一位负责人。"
                                : nextStatus === "active"
                                  ? "启用该人员账号。"
                                  : "停用该人员账号，未过期登录会话会失效。"
                          }
                          aria-label={
                            isLoading
                              ? "账号状态操作不可用，正在同步账号数据"
                              : wouldDisableLastOwner
                                ? "停用不可用，不能停用当前唯一负责人账号"
                                : nextStatus === "active"
                                  ? "启用该人员账号"
                                  : "停用该人员账号"
                          }
                        >
                          {nextStatus === "active" ? "启用" : "停用"}
                        </button>
                      </td>
                    </tr>
                  );
                })}
                {state.users.length === 0 ? (
                  <tr>
                    <td colSpan={5}>当前还没有可管理的人员账号。</td>
                  </tr>
                ) : null}
              </tbody>
            </table>
          </div>
        </>
      ) : null}

      {canExportDiagnostics ? (
        <section className="diagnostic-export-card" aria-label="本地诊断包">
          <div className="subsection-heading">
            <div>
              <h3>本地诊断包</h3>
              <p>导出运行状态、知识库规模、评测摘要、渠道状态、队列和近期错误摘要；不包含密钥、登录凭据和完整聊天原文。</p>
            </div>
            <FileText size={18} />
          </div>
          <div className="diagnostic-export-body">
            <div>
              <span>最近状态</span>
              <strong>{diagnosticExport.message}</strong>
              {diagnosticExport.lastFilename ? <small>{diagnosticExport.lastFilename}</small> : null}
            </div>
            <div className="diagnostic-export-actions">
              <button
                type="button"
                className="primary-action"
                onClick={() => void exportBundle()}
                disabled={diagnosticExport.status === "loading"}
              >
                {diagnosticExport.status === "loading" ? "正在生成" : "生成并下载"}
              </button>
              <button
                type="button"
                className="ghost-action"
                data-role-smoke="diagnostic-upload-package"
                onClick={() => void createDiagnosticUpload()}
                disabled={diagnosticExport.status === "loading"}
              >
                授权上传包
              </button>
            </div>
          </div>
        </section>
      ) : null}

      {canExportDiagnostics ? (
        <section
          className="diagnostic-intake-card"
          aria-label="售后接收台"
          data-h2w5-cloud-intake="p3-06u-26h2w5"
        >
          <div className="subsection-heading">
            <div>
              <h3>售后接收台</h3>
              <p>用于登记客户主动提供的授权上传包，校验脱敏、授权和摘要；这里只接收诊断资料，不远程控制客户电脑。</p>
            </div>
            <Upload size={18} />
          </div>
          <form className="diagnostic-intake-form" onSubmit={(event) => void submitDiagnosticIntake(event)}>
            <label>
              授权上传包 JSON
              <textarea
                data-role-smoke="diagnostic-intake-package-input"
                value={diagnosticIntakeText}
                onChange={(event) => setDiagnosticIntakeText(event.target.value)}
                placeholder="粘贴客户主动提供的 wanfa-diagnostic-upload-*.json 内容"
                rows={5}
                disabled={diagnosticIntake.status === "loading"}
              />
            </label>
            <div className="diagnostic-intake-actions">
              <button
                type="submit"
                className="primary-action"
                data-h2w5-cloud-intake-action="register"
                disabled={diagnosticIntake.status === "loading"}
              >
                {diagnosticIntake.status === "loading" ? "正在登记" : "登记接收"}
              </button>
              <span>{diagnosticIntake.message}</span>
            </div>
          </form>

          <div className="diagnostic-intake-boundary">
            <span>客户主动授权</span>
            <span>脱敏包校验</span>
            <span>不远控客户电脑</span>
            <span>不自动联网采集</span>
          </div>

          <label className="diagnostic-intake-note">
            处理备注
            <input
              value={diagnosticIntakeNote}
              onChange={(event) => setDiagnosticIntakeNote(event.target.value)}
              placeholder="例如：已生成知识更新建议，等待客户确认"
            />
          </label>

          <div className="diagnostic-intake-list" data-h2w5-cloud-intake-list="p3-06u-26h2w5">
            {diagnosticIntake.records.length === 0 ? (
              <div className="empty-state compact">
                <FileText size={18} />
                <strong>还没有售后接收记录</strong>
                <span>客户生成授权上传包后，可由售后在这里登记和校验。</span>
              </div>
            ) : (
              diagnosticIntake.records.map((record) => (
                <div className="diagnostic-intake-item" key={record.id}>
                  <div className="diagnostic-intake-main">
                    <strong>{record.package_filename}</strong>
                    <span>
                      {formatDateTime(record.created_at)} · {formatByteSize(record.package_size_bytes)} · {record.source_channel}
                    </span>
                    <small>摘要 {record.package_sha256.slice(0, 12)} · 诊断包 {record.diagnostic_bundle_sha256.slice(0, 12)}</small>
                    {record.rejection_reason ? <em>{record.rejection_reason}</em> : null}
                  </div>
                  <div className="diagnostic-intake-side">
                    <span className={`status-pill ${record.status === "rejected" ? "is-danger" : record.status === "resolved" ? "is-good" : "is-muted"}`}>
                      {formatDiagnosticIntakeStatus(record.status)}
                    </span>
                    <button
                      type="button"
                      className="ghost-action"
                      onClick={() => void downloadDiagnosticIntake(record)}
                      disabled={!record.download_supported}
                    >
                      下载包
                    </button>
                    {canManageUpdates && record.validation_status === "passed" && record.status !== "rejected" ? (
                      <button
                        type="button"
                        className="ghost-action"
                        data-h2w6-remediation-action="create"
                        onClick={() => void createDiagnosticRemediation(record)}
                        disabled={diagnosticRemediation.status === "loading"}
                      >
                        生成处理单
                      </button>
                    ) : null}
                    {canManageUpdates ? (
                      <>
                        <button type="button" className="ghost-action" onClick={() => void updateDiagnosticIntake(record, "in_review")}>
                          处理中
                        </button>
                        <button type="button" className="ghost-action" onClick={() => void updateDiagnosticIntake(record, "resolved")}>
                          标记结束
                        </button>
                      </>
                    ) : null}
                  </div>
                </div>
              ))
            )}
          </div>

          <div className="diagnostic-remediation-card" data-h2w6-remediation="p3-06u-26h2w6">
            <div className="subsection-heading compact">
              <div>
                <h4>处理回传包</h4>
                <p>把已通过校验的诊断包转成可审计处理建议；不静默更新，不远程修改客户环境。</p>
              </div>
              <ShieldCheck size={16} />
            </div>
            <div className="diagnostic-intake-boundary">
              <span>需要人工复核</span>
              <span>更新前必须备份</span>
              <span>客户管理员确认</span>
              <span>不静默更新</span>
            </div>
            <span className="diagnostic-remediation-message">{diagnosticRemediation.message}</span>
            {diagnosticRemediation.requests.length === 0 ? (
              <div className="empty-state compact">
                <FileText size={18} />
                <strong>还没有处理单</strong>
                <span>从已接收的诊断包生成处理单后，可下载回传包交给客户确认。</span>
              </div>
            ) : (
              <div className="diagnostic-remediation-list">
                {diagnosticRemediation.requests.slice(0, 4).map((request) => {
                  const updatePlan = readRecordPayload(request.update_request_manifest, "signed_update_control_plan");
                  const linkedPackage = updatePlan ? readRecordPayload(updatePlan, "signed_update_package") : null;
                  const lifecycleSteps = Array.isArray(updatePlan?.["lifecycle_steps"])
                    ? updatePlan["lifecycle_steps"].filter(
                        (value): value is Record<string, unknown> =>
                          Boolean(value) && typeof value === "object" && !Array.isArray(value)
                      )
                    : [];
                  const selectedPackageId =
                    remediationPlanSelection[request.id] || String(signedUpdateStage.packages[0]?.id ?? "");
                  const planStatusClass =
                    request.status === "ready_for_customer" || request.status === "update_plan_prepared"
                      ? "is-good"
                      : "is-muted";
                  return (
                    <div className="diagnostic-remediation-item" key={request.id}>
                      <div className="diagnostic-intake-main">
                        <strong>{request.title || request.request_id}</strong>
                        <span>
                          {formatDateTime(request.created_at)} · {request.request_type} · {request.priority}
                        </span>
                        <small>{request.summary}</small>
                        {updatePlan ? (
                          <div className="diagnostic-remediation-plan" data-h2w6b-remediation-plan="p3-06u-26h2w6b">
                            <div className="diagnostic-remediation-plan-title">
                              <strong>{readRecordString(linkedPackage ?? {}, "package_name") || "受控更新计划"}</strong>
                              <span>
                                {formatSignedUpdateType(
                                  (readRecordString(linkedPackage ?? {}, "package_type") as SignedUpdateStagedPackage["package_type"]) ||
                                    "knowledge"
                                )}
                                {" · "}
                                {formatSignedUpdateStatus(readRecordString(linkedPackage ?? {}, "status") || "staged")}
                                {" · 只生成计划"}
                              </span>
                            </div>
                            <div className="diagnostic-remediation-plan-steps">
                              {lifecycleSteps.slice(0, 5).map((step) => (
                                <span key={readRecordString(step, "id")} data-step-status={readRecordString(step, "status")}>
                                  {readRecordString(step, "label") || readRecordString(step, "id")}：
                                  {formatSignedUpdatePlanStepStatus(readRecordString(step, "status"))}
                                </span>
                              ))}
                            </div>
                          </div>
                        ) : null}
                      </div>
                      <div className="diagnostic-intake-side">
                        <span className={`status-pill ${planStatusClass}`}>{formatDiagnosticRemediationStatus(request.status)}</span>
                        {canManageUpdates ? (
                          <>
                            {signedUpdateStage.packages.length > 0 ? (
                              <select
                                className="diagnostic-remediation-package-select"
                                value={selectedPackageId}
                                onChange={(event) =>
                                  setRemediationPlanSelection((current) => ({
                                    ...current,
                                    [request.id]: event.target.value
                                  }))
                                }
                                disabled={diagnosticRemediation.status === "loading"}
                              >
                                {signedUpdateStage.packages.map((item) => (
                                  <option key={item.id} value={String(item.id)}>
                                    {item.package_name} · {formatSignedUpdateStatus(item.status)}
                                  </option>
                                ))}
                              </select>
                            ) : (
                              <small className="diagnostic-remediation-plan-hint">先暂存签名更新包</small>
                            )}
                            <button
                              type="button"
                              className="ghost-action"
                              data-h2w6b-remediation-action="create-plan"
                              onClick={() => void createRemediationUpdatePlan(request)}
                              disabled={diagnosticRemediation.status === "loading" || signedUpdateStage.packages.length === 0}
                            >
                              {updatePlan ? "刷新计划" : "生成计划"}
                            </button>
                            <button
                              type="button"
                              className="ghost-action"
                              onClick={() => void updateDiagnosticRemediation(request, "ready_for_customer")}
                              disabled={diagnosticRemediation.status === "loading"}
                            >
                              待客户确认
                            </button>
                            <button
                              type="button"
                              className="ghost-action"
                              data-h2w6-remediation-action="download"
                              onClick={() => void downloadDiagnosticRemediation(request)}
                              disabled={!request.download_supported}
                            >
                              下载回传包
                            </button>
                          </>
                        ) : null}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </section>
      ) : null}

      {canManageUpdates ? (
        <section className="local-backup-card" aria-label="本地备份点">
          <div className="subsection-heading">
            <div>
              <h3>本地备份点</h3>
              <p>用于更新前创建数据库物理备份，并校验备份文件完整性。当前只做备份和恢复演练，不直接覆盖正在运行的本地库。</p>
            </div>
            <ShieldCheck size={18} />
          </div>
          <div className="local-backup-toolbar">
            <div>
              <span>最近状态</span>
              <strong>{localBackupState.message}</strong>
            </div>
            <button
              type="button"
              className="primary-action"
              data-role-smoke="local-backup-create"
              onClick={() => void createBackup()}
              disabled={localBackupState.status === "loading"}
            >
              {localBackupState.status === "loading" ? "处理中" : "创建备份点"}
            </button>
          </div>
          {localBackupState.backups.length > 0 ? (
            <div className="local-backup-list">
              {localBackupState.backups.slice(0, 3).map((backup) => (
                <div key={backup.id} className="local-backup-item">
                  <div className="local-backup-main">
                    <strong>{backup.file_name}</strong>
                    <small>
                      {formatDateTime(backup.created_at)} · {formatByteSize(backup.file_size_bytes)} ·{" "}
                      {backup.sha256.slice(0, 12)}
                    </small>
                    {backup.error_message ? <small className="is-danger">{backup.error_message}</small> : null}
                  </div>
                  <div className="local-backup-badges">
                    <span>{formatLocalBackupStatus(backup.status)}</span>
                    <span>{backup.restore_mode === "manual_rehearsal_only" ? "恢复演练" : backup.restore_mode}</span>
                  </div>
                  <div className="local-backup-actions">
                    <button
                      type="button"
                      className="ghost-action"
                      data-role-smoke="local-backup-verify"
                      onClick={() => void verifyBackup(backup)}
                      disabled={localBackupState.status === "loading"}
                    >
                      校验
                    </button>
                    <button
                      type="button"
                      className="ghost-action"
                      data-role-smoke="local-restore-dry-run"
                      onClick={() => void createRestoreDryRun(backup)}
                      disabled={localBackupState.status === "loading"}
                    >
                      恢复演练
                    </button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="signed-update-empty">当前还没有本地备份点。导入知识包、策略包或程序包前，建议先创建并校验备份。</p>
          )}
          {localRestoreDryRun ? (
            <div className="local-backup-restore-plan" data-role-smoke="local-restore-dry-run-result">
              <div className="restore-plan-heading">
                <div>
                  <span>恢复演练</span>
                  <strong>{localRestoreDryRun.rehearsal_ready ? "计划已就绪" : "存在阻断项"}</strong>
                  <small>
                    {localRestoreDryRun.backup_id} · {formatDateTime(localRestoreDryRun.generated_at)}
                  </small>
                </div>
                <span className={localRestoreDryRun.can_restore_now ? "is-bad" : "is-good"}>
                  {localRestoreDryRun.can_restore_now ? "可执行恢复" : "只生成计划"}
                </span>
              </div>
              {localRestoreDryRun.blockers.length > 0 ? (
                <div className="restore-plan-blockers">
                  {localRestoreDryRun.blockers.map((blocker) => (
                    <span key={blocker}>{blocker}</span>
                  ))}
                </div>
              ) : null}
              <div className="restore-plan-grid">
                {localRestoreDryRun.health_checks.slice(0, 4).map((check) => (
                  <span key={String(check.name)}>
                    {formatRestoreCheckName(String(check.name))}：{formatRestoreCheckStatus(String(check.status))}
                  </span>
                ))}
              </div>
              <ol className="restore-plan-steps">
                {localRestoreDryRun.rehearsal_plan.slice(0, 4).map((step) => (
                  <li key={String(step.step)}>
                    <strong>{String(step.label ?? step.step)}</strong>
                    <span>{String(step.description ?? "")}</span>
                  </li>
                ))}
              </ol>
            </div>
          ) : null}
        </section>
      ) : null}

      {canManageUpdates ? (
        <section className="signed-update-card" aria-label="签名更新包预检" data-role-smoke="signed-update-center">
          <div className="subsection-heading">
            <div>
              <h3>签名更新包预检</h3>
              <p>用于校验我们回传的 `.wanfa-update` 包。这里只检查签名、摘要、版本兼容和备份计划，不执行程序更新。</p>
            </div>
            <ShieldCheck size={18} />
          </div>
          <form className="signed-update-form" onSubmit={(event) => void submitSignedUpdatePreflight(event)}>
            <label>
              更新包内容
              <textarea
                data-role-smoke="signed-update-package-input"
                value={signedUpdateText}
                onChange={(event) => setSignedUpdateText(event.target.value)}
                rows={10}
                spellCheck={false}
                disabled={signedUpdatePreflight.status === "loading"}
              />
            </label>
            <div className="signed-update-actions">
              <button
                type="submit"
                className="primary-action"
                data-role-smoke="signed-update-preflight"
                disabled={signedUpdatePreflight.status === "loading"}
              >
                {signedUpdatePreflight.status === "loading" ? "正在预检" : "校验更新包"}
              </button>
              <button
                type="button"
                className="ghost-action"
                data-role-smoke="signed-update-stage"
                onClick={() => void stageCurrentSignedUpdatePackage()}
                disabled={signedUpdatePreflight.status === "loading" || signedUpdateStage.status === "loading"}
              >
                {signedUpdateStage.status === "loading" ? "正在暂存" : "暂存更新包"}
              </button>
              <button
                type="button"
                className="ghost-action"
                onClick={() => setSignedUpdateText(DEFAULT_SIGNED_UPDATE_PACKAGE_TEXT)}
                disabled={signedUpdatePreflight.status === "loading"}
              >
                恢复示例
              </button>
            </div>
          </form>

          <div
            className={`signed-update-result ${signedUpdateResult?.can_stage ? "is-pass" : "is-blocked"}`}
            data-role-smoke="signed-update-result"
          >
            <div>
              <span>预检状态</span>
              <strong>{signedUpdatePreflight.message}</strong>
              {signedUpdateResult ? (
                <small>
                  {signedUpdateResult.package_name} · {signedUpdateResult.package_version} · 当前版本{" "}
                  {signedUpdateResult.current_app_version}
                </small>
              ) : null}
            </div>
            <div className="signed-update-check-grid">
              <span className={signedUpdateSignatureOk ? "is-good" : "is-bad"}>签名 {signedUpdateSignatureOk ? "通过" : "未通过"}</span>
              <span className={signedUpdateChecksumOk ? "is-good" : "is-bad"}>摘要 {signedUpdateChecksumOk ? "一致" : "异常"}</span>
              <span className={signedUpdateCompatible ? "is-good" : "is-bad"}>版本 {signedUpdateCompatible ? "兼容" : "不兼容"}</span>
              <span className={signedUpdateResult?.can_apply_now ? "is-bad" : "is-good"}>执行 已关闭</span>
            </div>
            {signedUpdateBackupResources.length > 0 ? (
              <small>备份范围：{signedUpdateBackupResources.slice(0, 6).join("、")}</small>
            ) : null}
            {signedUpdateResult?.errors.length ? (
              <ul className="signed-update-list">
                {signedUpdateResult.errors.map((error) => (
                  <li key={error}>{error}</li>
                ))}
              </ul>
            ) : null}
            {signedUpdateResult?.warnings.length ? (
              <ul className="signed-update-list muted">
                {signedUpdateResult.warnings.map((warning) => (
                  <li key={warning}>{warning}</li>
                ))}
              </ul>
            ) : null}
          </div>

          <div className="signed-update-staged">
            <div className="subsection-heading compact">
              <div>
                <h4>已暂存更新包</h4>
                <p>{signedUpdateStage.message}</p>
              </div>
            </div>
            {signedUpdateStage.packages.length > 0 ? (
              <div className="signed-update-staged-list">
                {signedUpdateStage.packages.map((item) => {
                  const supportedApplyPackage = item.package_type === "knowledge" || item.package_type === "strategy";
                  const strategyVersion = readRecordString(item.apply_result, "strategy_version");
                  const programDryRunResult = readRecordPayload(item.preflight_result, "program_dry_run_result");
                  const programDryRunStatus = programDryRunResult
                    ? readRecordString(programDryRunResult, "dry_run_status")
                    : "";
                  const programTargetVersion = programDryRunResult
                    ? readRecordString(programDryRunResult, "target_program_version")
                    : "";
                  const programRequiresWindow = programDryRunResult?.["requires_maintenance_window"] === true;
                  const programBlockedActions = Array.isArray(programDryRunResult?.["blocked_actions"])
                    ? programDryRunResult["blocked_actions"].map((value) => String(value))
                    : [];
                  const programPlannedSteps = Array.isArray(programDryRunResult?.["planned_steps"])
                    ? programDryRunResult["planned_steps"].filter(
                        (value): value is Record<string, unknown> =>
                          Boolean(value) && typeof value === "object" && !Array.isArray(value)
                      )
                    : [];
                  const canApplyPackage =
                    item.status === "staged" && supportedApplyPackage && signedUpdateStage.status !== "loading";
                  const canCreateProgramDryRun =
                    item.status === "staged" && item.package_type === "program" && signedUpdateStage.status !== "loading";
                  const canRollbackPackage = item.status === "applied" && signedUpdateStage.status !== "loading";
                  return (
                    <div key={item.id} className="signed-update-staged-item" data-role-smoke={`signed-update-staged-${item.status}`}>
                      <div className="signed-update-staged-main">
                        <strong>{item.package_name}</strong>
                        <small>
                          {formatSignedUpdateType(item.package_type)} · {item.package_version} · 暂存于{" "}
                          {formatDateTime(item.staged_at)}
                        </small>
                        {item.knowledge_import_batch_id ? (
                          <small>知识导入批次：#{item.knowledge_import_batch_id}</small>
                        ) : null}
                        {strategyVersion ? <small>策略版本：{strategyVersion}</small> : null}
                        {programDryRunResult ? (
                          <div className="signed-update-program-plan" data-role-smoke="signed-update-program-dry-run-result">
                            <small>
                              演练计划：{programDryRunStatus === "planned" ? "已生成" : programDryRunStatus || "已记录"}
                              {programTargetVersion ? ` · 目标版本 ${programTargetVersion}` : ""}
                              {programRequiresWindow ? " · 需要维护窗口" : ""}
                            </small>
                            {programPlannedSteps.length > 0 ? (
                              <ul className="signed-update-list muted">
                                {programPlannedSteps.slice(0, 3).map((step) => (
                                  <li key={readRecordString(step, "id") || readRecordString(step, "label")}>
                                    {readRecordString(step, "label") || "程序更新演练步骤"}
                                  </li>
                                ))}
                              </ul>
                            ) : null}
                            {programBlockedActions.length > 0 ? (
                              <small>已阻断：{programBlockedActions.slice(0, 5).join("、")}</small>
                            ) : null}
                          </div>
                        ) : null}
                      </div>
                      <div className="signed-update-staged-badges">
                        <span>{formatSignedUpdateStatus(item.status)}</span>
                        <span>{item.backup_created ? "已备份" : "未备份"}</span>
                        <span>{item.safety["external_write_performed"] === true ? "存在外发" : "无外发"}</span>
                      </div>
                      <div className="signed-update-staged-actions">
                        {item.package_type === "program" ? (
                          <>
                            <span className="signed-update-note">程序包只生成演练计划，不替换文件</span>
                            {item.status === "staged" ? (
                              <button
                                type="button"
                                className="ghost-action"
                                data-role-smoke="signed-update-program-dry-run"
                                onClick={() => void createProgramDryRun(item)}
                                disabled={!canCreateProgramDryRun}
                              >
                                生成演练计划
                              </button>
                            ) : null}
                          </>
                        ) : null}
                        {item.status === "staged" && supportedApplyPackage ? (
                          <button
                            type="button"
                            className="primary-action"
                            data-role-smoke="signed-update-apply"
                            onClick={() => void applySignedUpdatePackage(item)}
                            disabled={!canApplyPackage}
                          >
                            备份并应用
                          </button>
                        ) : null}
                        {item.status === "applied" ? (
                          <button
                            type="button"
                            className="ghost-action"
                            data-role-smoke="signed-update-rollback"
                            onClick={() => void rollbackSignedUpdatePackage(item)}
                            disabled={!canRollbackPackage}
                          >
                            回滚
                          </button>
                        ) : null}
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <p className="signed-update-empty">当前没有暂存更新包。预检通过后可先暂存，后续再进入备份和回滚流程。</p>
            )}
          </div>
        </section>
      ) : null}

      {localError ? <div className="form-error">{localError}</div> : null}
    </article>
  );
}

function OpsWorkerHealthPanel({
  state,
  alertRulesState,
  metricsState,
  hasToken,
  onRefresh
}: {
  state: OpsWorkerHealthState;
  alertRulesState: OpsAlertRulesState;
  metricsState: OpsMetricsState;
  hasToken: boolean;
  onRefresh: () => void;
}) {
  const data = state.data;
  const alertRules = alertRulesState.data;
  const opsMetrics = metricsState.data;
  const summary = data?.summary;
  const isLoading = state.status === "loading" || alertRulesState.status === "loading" || metricsState.status === "loading";
  const message =
    state.status === "idle" ? state.message : state.status === "error" ? state.message : "";
  const alertRulesMessage =
    alertRulesState.status === "idle"
      ? alertRulesState.message
      : alertRulesState.status === "error"
        ? alertRulesState.message
        : "";
  const metricsMessage =
    metricsState.status === "idle"
      ? metricsState.message
      : metricsState.status === "error"
        ? metricsState.message
        : "";
  const healthCards = summary
    ? [
        {
          label: "健康 worker",
          value: `${summary.healthy_workers}/${summary.total_workers}`,
          note: summary.total_workers ? "最近心跳在阈值内" : "尚未写入心跳",
          tone: summary.healthy_workers === summary.total_workers && summary.total_workers > 0 ? "success" : "warning"
        },
        {
          label: "异常 worker",
          value: `${summary.failed_workers + summary.stale_workers}`,
          note: `失败 ${summary.failed_workers} · 超时 ${summary.stale_workers}`,
          tone: summary.failed_workers > 0 ? "urgent" : summary.stale_workers > 0 ? "warning" : "success"
        },
        {
          label: "循环次数",
          value: `${data.heartbeats.reduce((sum, item) => sum + item.loops_completed, 0)}`,
          note: "累计 heartbeat loop 计数",
          tone: "normal"
        },
        {
          label: "真实外发",
          value: summary.external_write_enabled ? "已开启" : "关闭",
          note: summary.external_write_enabled ? "需要确认正式授权" : "当前不会写外部平台",
          tone: summary.external_write_enabled ? "urgent" : "success"
        }
      ]
    : [];
  const highlightedMetrics = opsMetrics
    ? [...opsMetrics.metrics]
        .sort((left, right) => {
          const priority = { critical: 0, warning: 1, ok: 2 };
          return (priority[left.status as keyof typeof priority] ?? 3) - (priority[right.status as keyof typeof priority] ?? 3);
        })
        .slice(0, 8)
    : [];
  const prometheusPreview = opsMetrics
    ? sanitizeCustomerVisibleOpsText(opsMetrics.prometheus_text.trim().split("\n").slice(0, 18).join("\n"))
    : "";

  return (
    <section className="workspace-page-grid stacked ops-workspace" id="workspace-ops">
      <article className="panel operation-health">
        <div className="panel-heading">
          <div>
            <h2>后台进程健康</h2>
            <p>只读查看可信入站 worker 的心跳、最近运行和风险，不触发模型调用或外部平台写入。</p>
          </div>
          <div className="panel-actions">
            <button type="button" className="ghost-action" onClick={onRefresh} disabled={!hasToken || isLoading}>
              <RefreshCw size={17} />
              {isLoading ? "刷新中" : "刷新"}
            </button>
          </div>
        </div>

        <div className="panel-state-row" aria-label="运维数据状态">
          <DataSourceBadge
            mode={hasToken ? "real" : "demo"}
            label={hasToken ? REAL_DATA_LABEL : PREVIEW_DATA_LABEL}
            detail={hasToken ? "读取 worker、告警和指标接口" : "正式登录后可查看真实后台进程健康状态"}
          />
          <DataSourceBadge
            mode="off"
            label="真实外发关闭"
            detail="运维页只读查看，不触发模型调用或外部平台写入"
          />
        </div>
        <PanelStateNotice status={state.status} message={message} loadingMessage="正在读取后台进程健康状态。" />
        {!hasToken ? (
          <WorkspaceStateNotice
            kind="no_permission"
            message="正式登录后可查看真实后台进程健康状态。"
            compact
          />
        ) : null}
        <PanelStateNotice status={alertRulesState.status} message={alertRulesMessage} loadingMessage="正在读取告警规则。" />
        <PanelStateNotice status={metricsState.status} message={metricsMessage} loadingMessage="正在读取指标出口。" />

        {summary ? (
          <>
            <div className="ops-health-strip">
              {healthCards.map((item) => (
                <article key={item.label} className={`ops-health-card tone-${item.tone}`}>
                  <span>{item.label}</span>
                  <strong>{item.value}</strong>
                  <small>{item.note}</small>
                </article>
              ))}
            </div>

            <div className="ops-alert-strip">
              <div className={summary.requires_attention ? "ops-status-card is-warning" : "ops-status-card is-healthy"}>
                {summary.requires_attention ? <AlertTriangle size={20} /> : <CheckCircle2 size={20} />}
                <div>
                  <strong>{summary.requires_attention ? "需要处理" : "运行正常"}</strong>
                  <span>
                    stale 阈值 {data.stale_after_seconds} 秒 · 可信入站 worker 配置：
                    {summary.trusted_inbound_worker_enabled ? "已启用" : "未启用"}
                  </span>
                </div>
              </div>
              <div className="ops-status-card">
                <ShieldCheck size={20} />
                <div>
                  <strong>外部动作边界</strong>
                  <span>
                    外部调用：{data.external_call_performed ? "有" : "无"} · 外部平台写入：
                    {data.external_platform_write_performed ? "有" : "无"}
                  </span>
                </div>
              </div>
            </div>
          </>
        ) : null}
      </article>

      {alertRules ? (
        <article className="panel ops-table-panel ops-alert-rules-panel">
          <div className="panel-heading compact">
            <div>
              <h2>告警规则</h2>
              <p>只读评估当前是否需要处理；本阶段不接真实通知通道。</p>
            </div>
            <AlertTriangle size={20} />
          </div>
          <div className="ops-alert-rule-summary">
            <article className={alertRules.firing_count ? "ops-health-card tone-warning" : "ops-health-card tone-success"}>
              <span>触发规则</span>
              <strong>{alertRules.firing_count}</strong>
              <small>page {alertRules.page_count} · ticket {alertRules.ticket_count}</small>
            </article>
            <article className="ops-health-card tone-success">
              <span>通知通道</span>
              <strong>{alertRules.notification_channel_enabled ? "已配置" : "未接入"}</strong>
              <small>{alertRules.notification_sent ? "本次已通知" : "本次未发送任何通知"}</small>
            </article>
            <article className="ops-health-card tone-success">
              <span>外部动作</span>
              <strong>{alertRules.external_platform_write_performed ? "有写入" : "无写入"}</strong>
              <small>模型调用：{alertRules.external_call_performed ? "有" : "无"}</small>
            </article>
          </div>
          <div className="ops-alert-rules-grid">
            {alertRules.rules.map((rule) => (
              <OpsAlertRuleCard key={rule.code} rule={rule} />
            ))}
          </div>
        </article>
      ) : (
        <article className="panel ops-table-panel">
          <WorkspaceStateNotice
            kind="empty"
            message="暂无告警规则评估。正式登录后可读取规则目录和当前触发状态。"
            compact
          />
        </article>
      )}

      {opsMetrics ? (
        <article className="panel ops-table-panel ops-metrics-panel">
          <div className="panel-heading compact">
            <div>
              <h2>指标出口</h2>
              <p>面向 Prometheus 或云监控的只读采集草案；当前只生成 JSON 与文本预览。</p>
            </div>
            <BarChart3 size={20} />
          </div>
          <div className="ops-metrics-grid">
            <article className={opsMetrics.summary.page_alerts ? "ops-health-card tone-urgent" : "ops-health-card tone-success"}>
              <span>立即处理</span>
              <strong>{opsMetrics.summary.page_alerts}</strong>
              <small>触发规则 {opsMetrics.summary.firing_alerts}</small>
            </article>
            <article className={opsMetrics.summary.queue_backlog ? "ops-health-card tone-warning" : "ops-health-card tone-success"}>
              <span>队列积压</span>
              <strong>{opsMetrics.summary.queue_backlog}</strong>
              <small>待处理、锁定或重试任务</small>
            </article>
            <article className={opsMetrics.summary.dead_letter_jobs ? "ops-health-card tone-urgent" : "ops-health-card tone-success"}>
              <span>死信任务</span>
              <strong>{opsMetrics.summary.dead_letter_jobs}</strong>
              <small>外发失败后需人工复盘</small>
            </article>
            <article className={opsMetrics.summary.open_failure_reviews ? "ops-health-card tone-warning" : "ops-health-card tone-success"}>
              <span>失败复盘</span>
              <strong>{opsMetrics.summary.open_failure_reviews}</strong>
              <small>当前打开的复盘项</small>
            </article>
          </div>
          <div className="ops-metrics-layout">
            <div className="ops-metric-list" aria-label="重点指标">
              {highlightedMetrics.map((metric) => (
                <article key={`${metric.name}:${JSON.stringify(metric.labels)}`} className={`ops-metric-row ${metric.status}`}>
                  <div>
                    <strong>{sanitizeCustomerVisibleOpsText(metric.name)}</strong>
                    <small>{sanitizeCustomerVisibleOpsText(metric.source)}</small>
                  </div>
                  <span>{formatMetricLabels(metric.labels)}</span>
                  <b>{formatMetricDisplayValue(metric)}</b>
                  <em>{formatMetricStatusLabel(metric.status)}</em>
                </article>
              ))}
            </div>
            <div className="ops-prometheus-card">
              <div>
                <strong>采集文本预览</strong>
                <span>{opsMetrics.scrape_path}</span>
              </div>
              <pre className="ops-prometheus-preview">{prometheusPreview}</pre>
            </div>
          </div>
        </article>
      ) : (
        <article className="panel ops-table-panel">
          <WorkspaceStateNotice
            kind="empty"
            message="暂无指标出口。正式登录后可读取 JSON 指标和采集文本预览。"
            compact
          />
        </article>
      )}

      <section className="workspace-page-grid two-column">
        <article className="panel ops-table-panel">
          <div className="panel-heading compact">
            <div>
              <h2>Worker 心跳</h2>
              <p>按 worker 实例查看状态、健康、最近心跳和错误。</p>
            </div>
            <Activity size={20} />
          </div>
          {data && data.heartbeats.length > 0 ? (
            <div className="ops-table" role="table" aria-label="Worker 心跳列表">
              <div className="ops-table-head" role="row">
                <span role="columnheader">实例</span>
                <span role="columnheader">健康</span>
                <span role="columnheader">最近心跳</span>
                <span role="columnheader">最近运行</span>
              </div>
              {data.heartbeats.map((item) => (
                <div key={`${item.worker_type}:${item.worker_id}`} className="ops-table-row" role="row">
                  <span role="cell">
                    <strong>{item.worker_id}</strong>
                    <small>{item.worker_type}</small>
                  </span>
                  <span role="cell">
                    <b className={`ops-health-pill ${item.health_status}`}>{formatWorkerHealthLabel(item.health_status)}</b>
                    <small>{item.status}</small>
                  </span>
                  <span role="cell">{formatDateTime(item.last_heartbeat_at)}</span>
                  <span role="cell">
                    <strong>{item.last_run_record_id ? `#${item.last_run_record_id}` : "暂无"}</strong>
                    <small>{item.last_error || `${item.last_run_mode || "未记录"} · 循环 ${item.loops_completed}`}</small>
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <WorkspaceStateNotice kind="empty" message="暂无 worker heartbeat。请先启动 worker profile 后再刷新。" compact />
          )}
        </article>

        <article className="panel ops-risk-panel">
          <div className="panel-heading compact">
            <div>
              <h2>风险与动作</h2>
              <p>把失败、超时和开关风险转成可排障动作。</p>
            </div>
            <AlertTriangle size={20} />
          </div>
          {data && data.risks.length > 0 ? (
            <div className="ops-risk-list">
              {data.risks.map((risk, index) => (
                <article key={`${risk.code}-${index}`} className={`ops-risk-card ${risk.severity}`}>
                  <div>
                    <span>{formatRiskSeverityLabel(risk.severity)}</span>
                    <strong>{risk.title}</strong>
                  </div>
                  <p>{risk.detail}</p>
                  <small>{risk.next_action}</small>
                </article>
              ))}
            </div>
          ) : (
            <WorkspaceStateNotice kind="empty" message="当前没有需要处理的 worker 风险。" compact />
          )}
        </article>
      </section>

      <article className="panel ops-table-panel">
        <div className="panel-heading compact">
          <div>
            <h2>最近入站运行</h2>
            <p>用于排查可信入站消息是否被扫描、处理、跳过、限流或失败。</p>
          </div>
          <Bot size={20} />
        </div>
        {data && data.recent_trusted_inbound_runs.length > 0 ? (
          <div className="ops-table ops-run-table" role="table" aria-label="最近可信入站 worker 运行记录">
            <div className="ops-table-head" role="row">
              <span role="columnheader">运行</span>
              <span role="columnheader">状态</span>
              <span role="columnheader">处理结果</span>
              <span role="columnheader">外部写入</span>
              <span role="columnheader">时间</span>
            </div>
            {data.recent_trusted_inbound_runs.map((run) => (
              <div key={run.id} className="ops-table-row" role="row">
                <span role="cell">
                  <strong>#{run.id}</strong>
                  <small>{run.worker_id}</small>
                </span>
                <span role="cell">
                  <b className={`ops-health-pill ${run.status}`}>{run.status}</b>
                  <small>{run.mode}</small>
                </span>
                <span role="cell">
                  扫描 {run.scanned} · 处理 {run.processed} · 成功 {run.succeeded} · 失败 {run.failed}
                </span>
                <span role="cell">{run.external_write ? "是" : "否"}</span>
                <span role="cell">{formatDateTime(run.started_at)}</span>
              </div>
            ))}
          </div>
        ) : (
          <WorkspaceStateNotice kind="empty" message="暂无可信入站 worker 运行记录。" compact />
        )}
      </article>
    </section>
  );
}

function OpsAlertRuleCard({ rule }: { rule: OpsAlertRule }) {
  const firstChecks = rule.runbook.first_checks.slice(0, 3);
  return (
    <article className={`ops-alert-rule-card ${rule.status} ${rule.severity}`}>
      <div className="ops-alert-rule-head">
        <div>
          <span>{formatAlertResponseTypeLabel(rule.response_type)} · {formatRiskSeverityLabel(rule.severity)}</span>
          <strong>{rule.name}</strong>
        </div>
        <b className={`ops-health-pill ${rule.status}`}>{formatAlertStatusLabel(rule.status)}</b>
      </div>
      <p>{rule.reason}</p>
      <dl className="ops-alert-rule-meta">
        <div>
          <dt>信号</dt>
          <dd>{rule.signal}</dd>
        </div>
        <div>
          <dt>当前值</dt>
          <dd>{rule.current_value}</dd>
        </div>
        <div>
          <dt>阈值</dt>
          <dd>{rule.threshold} · {rule.duration}</dd>
        </div>
      </dl>
      <div className="ops-alert-runbook">
        <span>首查步骤</span>
        <ol>
          {firstChecks.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ol>
        <small>{rule.runbook.escalation}</small>
      </div>
    </article>
  );
}

function ReviewInboxPanel({
  state,
  workerRun,
  listView,
  hasToken,
  canManageConversations,
  canRunInboundWorker,
  canManageOutboxDraft,
  selectedReviewId,
  onListViewChange,
  onRefresh,
  onRunInboundWorker,
  onSelect,
  onApprove,
  onReject
}: {
  state: ReviewInboxState;
  workerRun: TrustedInboundWorkerRun | null;
  listView: ListViewState;
  hasToken: boolean;
  canManageConversations: boolean;
  canRunInboundWorker: boolean;
  canManageOutboxDraft: boolean;
  selectedReviewId: number | null;
  onListViewChange: (view: ListViewState) => void;
  onRefresh: () => void;
  onRunInboundWorker: () => void;
  onSelect: (item: HumanReviewInboxItem) => void;
  onApprove: (item: HumanReviewInboxItem) => void;
  onReject: (item: HumanReviewInboxItem) => void;
}) {
  const items = "items" in state ? state.items : [];
  const pagedItems = useMemo(
    () =>
      getPagedItems(items, listView, {
        statusMatcher: (item, status) => {
          if (status === "high_risk") {
            return ["high", "critical"].includes(item.risk_level);
          }
          if (status === "low_confidence") {
            return (item.evidence.confidence ?? 0) < 0.55;
          }
          if (status === "no_knowledge") {
            return item.evidence.retrieved_knowledge_count === 0;
          }
          return item.status === status;
        },
        searchText: (item) => [
          item.reason,
          item.risk_level,
          item.conversation.subject,
          item.trigger_message?.content,
          item.draft_reply,
          item.evidence.intent,
          item.evidence.draft_source
        ]
      }),
    [items, listView]
  );
  const isLoading = state.status === "loading";
  const message =
    state.status === "idle" ? state.message : state.status === "error" ? state.message : "";
  const runInboundDisabledReason = formatAccessDisabledReason({
    hasToken,
    canManage: canRunInboundWorker,
    isLoading,
    action: "运行入站编排"
  });
  const approveDisabledReason = formatAccessDisabledReason({
    hasToken,
    canManage: canManageConversations && canManageOutboxDraft,
    isLoading,
    action: "批准审核草稿"
  });

  return (
    <article className="panel review-panel" id="workspace-reviews">
      <div className="panel-heading">
        <div>
          <h2>人工审核收件箱</h2>
          <p>集中处理低置信、无知识命中、模型不可用和高风险回复。</p>
        </div>
        <div className="panel-actions">
          <button
            type="button"
            className="ghost-action"
            onClick={onRunInboundWorker}
            disabled={!hasToken || !canRunInboundWorker || isLoading}
          >
            <Bot size={17} />
            运行入站编排
          </button>
          <button type="button" className="ghost-action" onClick={onRefresh} disabled={!hasToken || isLoading}>
            <RefreshCw size={17} />
            {isLoading ? "刷新中" : "刷新"}
          </button>
        </div>
      </div>

      <div className="panel-state-row" aria-label="人工审核数据状态">
        <DataSourceBadge
          mode={hasToken ? "real" : "demo"}
          label={hasToken ? REAL_DATA_LABEL : PREVIEW_DATA_LABEL}
          detail={hasToken ? "读取人审任务、证据和 AI 草稿" : "仅展示样例审核池结构"}
        />
        <DataSourceBadge
          mode="off"
          label="真实外发关闭"
          detail="批准只进入待发送门禁，不自动真实外发"
        />
      </div>

      <PanelStateNotice status={state.status} message={message} loadingMessage="正在读取人工审核任务。" />
      <DisabledReason show={Boolean(runInboundDisabledReason)} reason={runInboundDisabledReason} />
      <DisabledReason show={Boolean(approveDisabledReason)} reason={approveDisabledReason} />

      {workerRun ? (
        <div className="worker-summary" aria-live="polite">
          <div>
            <span>最近入站编排</span>
            <strong>处理 {workerRun.processed} 条</strong>
          </div>
          <small>
            扫描 {workerRun.scanned} · 成功 {workerRun.succeeded} · 失败 {workerRun.failed} · 跳过{" "}
            {workerRun.skipped} · 限流 {workerRun.rate_limited} · 外部写入：否
          </small>
        </div>
      ) : null}

      {items.length === 0 && state.status === "ready" ? (
        <WorkspaceStateNotice
          kind="empty"
          message="暂无待人工审核任务。低置信、无知识命中、高风险或模型不可用时会进入这里。"
          compact
        />
      ) : null}

      <ListToolbar
        view={listView}
        total={items.length}
        filteredTotal={pagedItems.total}
        statusOptions={[
          { label: "全部", value: "all" },
          { label: "待审核", value: "open" },
          { label: "高风险", value: "high_risk" },
          { label: "低置信", value: "low_confidence" },
          { label: "无知识命中", value: "no_knowledge" }
        ]}
        searchPlaceholder="搜索会话、客户问题、草稿、意图"
        onChange={onListViewChange}
      />

      <div className="review-list">
        {pagedItems.items.map((item) => {
          const approveItemDisabledReason = !hasToken
            ? "按钮已禁用：请先登录本地管理员账号后写入真实审核状态。"
            : isLoading
              ? "按钮已禁用：正在刷新审核任务。"
              : !canManageConversations || !canManageOutboxDraft
                ? "按钮已禁用：当前账号缺少会话处理或待发送草稿权限。"
                : !item.draft_reply.trim()
                  ? "按钮已禁用：当前审核任务没有可批准的回复草稿。"
                  : "";
          return (
          <article key={item.id} className={`review-row ${item.id === selectedReviewId ? "is-selected" : ""}`}>
            <div className="review-row-head">
              <div>
                <strong>审核 #{item.id}</strong>
                <span>{item.reason} · {item.risk_level}</span>
              </div>
              <small>{item.workflow.status} · {item.workflow.current_step}</small>
            </div>
            <div className="review-context">
              <span>{item.conversation.subject || `会话 #${item.conversation.id}`}</span>
              <p>{item.trigger_message?.content ?? "没有关联入站消息"}</p>
            </div>
            <div className="review-draft">
              <span>回复草稿</span>
              <p>{item.draft_reply || "暂无草稿"}</p>
            </div>
            <div className="evidence-strip">
              <span>置信度 {formatPercent(item.evidence.confidence)}</span>
              <span>知识 {item.evidence.retrieved_knowledge_count}</span>
              <span>{item.evidence.draft_source || "unknown_source"}</span>
              <span>{formatModelCallLabel(item.evidence.model_call)}</span>
            </div>
            <div className="review-actions">
              <button
                type="button"
                className="ghost-action"
                disabled={!hasToken || isLoading}
                onClick={() => onSelect(item)}
              >
                <Search size={17} />
                查看证据
              </button>
              <button
                type="button"
                className="primary-action"
                disabled={
                  !hasToken ||
                  !canManageConversations ||
                  !canManageOutboxDraft ||
                  isLoading ||
                  !item.draft_reply.trim()
                }
                onClick={() => onApprove(item)}
              >
                <CheckCircle2 size={17} />
                批准入待发送
              </button>
              <button
                type="button"
                className="ghost-action"
                disabled={!hasToken || !canManageConversations || isLoading}
                onClick={() => onReject(item)}
              >
                拒绝
              </button>
              <DisabledReason show={Boolean(approveItemDisabledReason)} reason={approveItemDisabledReason} />
            </div>
          </article>
          );
        })}
      </div>
      <PaginationControls result={pagedItems} view={listView} onChange={onListViewChange} />
    </article>
  );
}

function OutboxPanel({
  state,
  workerRun,
  deliveryQueue,
  deliveryQueueRun,
  listView,
  hasToken,
  canManageConnector,
  canManageDraft,
  canManageSendAttempt,
  canManageSendPlan,
  canManageDeliveryJob,
  onListViewChange,
  onRefresh,
  onRunWorker,
  onRunDeliveryQueue,
  onDryRun,
  onConnectorPlan,
  onCreateDeliveryJob,
  onConfirm
}: {
  state: OutboxState;
  workerRun: OutboxWorkerRun | null;
  deliveryQueue: DeliveryQueueState;
  deliveryQueueRun: OutboxDeliveryQueueRun | null;
  listView: ListViewState;
  hasToken: boolean;
  canManageConnector: boolean;
  canManageDraft: boolean;
  canManageSendAttempt: boolean;
  canManageSendPlan: boolean;
  canManageDeliveryJob: boolean;
  onListViewChange: (view: ListViewState) => void;
  onRefresh: () => void;
  onRunWorker: () => void;
  onRunDeliveryQueue: () => void;
  onDryRun: (draftId: number) => void;
  onConnectorPlan: (draft: OutboxDraft) => void;
  onCreateDeliveryJob: (draft: OutboxDraft) => void;
  onConfirm: (draftId: number) => void;
}) {
  const drafts = "drafts" in state ? state.drafts : [];
  const attemptsByDraft = "attemptsByDraft" in state ? state.attemptsByDraft : {};
  const deliveryJobs = "jobs" in deliveryQueue ? deliveryQueue.jobs : [];
  const jobsByDraft = Object.fromEntries(deliveryJobs.map((job) => [job.outbox_draft_id, job]));
  const pagedDrafts = useMemo(
    () =>
      getPagedItems(drafts, listView, {
        statusMatcher: (draft, status) => {
          if (status === "queued") {
            return Boolean(jobsByDraft[draft.id]);
          }
          if (status === "has_attempt") {
            return (attemptsByDraft[draft.id] ?? []).length > 0;
          }
          return draft.status === status || draft.delivery_status === status;
        },
        searchText: (draft) => [
          draft.reply_text,
          draft.status,
          draft.delivery_status,
          draft.confirmation_note,
          draft.cancellation_reason,
          `草稿 ${draft.id}`,
          `会话 ${draft.conversation_id}`
        ]
      }),
    [drafts, listView, attemptsByDraft, jobsByDraft]
  );
  const isLoading = state.status === "loading";
  const isQueueLoading = deliveryQueue.status === "loading";
  const message =
    state.status === "idle" ? state.message : state.status === "error" ? state.message : "";
  const queueMessage =
    deliveryQueue.status === "idle" ? deliveryQueue.message : deliveryQueue.status === "error" ? deliveryQueue.message : "";
  const runQueueDisabledReason = formatAccessDisabledReason({
    hasToken,
    canManage: canManageDeliveryJob,
    isLoading: isLoading || isQueueLoading,
    action: "运行发送队列"
  });
  const runWorkerDisabledReason = formatAccessDisabledReason({
    hasToken,
    canManage: canManageSendAttempt,
    isLoading,
    action: "运行发送检查"
  });

  return (
    <section className="panel outbox-panel" id="workspace-outbox" aria-label="待发送草稿">
      <div className="panel-heading">
        <div>
          <h2>待发送草稿</h2>
          <p>显示待确认、已确认、模拟发送、官方渠道计划和回执前置状态；当前不真实外发。</p>
        </div>
        <div className="panel-actions">
          <button
            type="button"
            className="ghost-action"
            onClick={onRunDeliveryQueue}
            disabled={!hasToken || !canManageDeliveryJob || isLoading || isQueueLoading}
          >
            <Activity size={17} />
            运行发送队列
          </button>
          <button
            type="button"
            className="ghost-action"
            onClick={onRunWorker}
            disabled={!hasToken || !canManageSendAttempt || isLoading}
          >
            <Route size={17} />
            运行发送检查
          </button>
          <button type="button" className="ghost-action" onClick={onRefresh} disabled={!hasToken || isLoading}>
            <RefreshCw size={17} />
            {isLoading ? "刷新中" : "刷新"}
          </button>
        </div>
      </div>

      <div className="panel-state-row" aria-label="待发送数据状态">
        <DataSourceBadge
          mode={hasToken ? "real" : "demo"}
          label={hasToken ? REAL_DATA_LABEL : PREVIEW_DATA_LABEL}
          detail={hasToken ? "读取发送草稿、发送计划和队列任务" : "仅展示样例发送准备流程"}
        />
        <DataSourceBadge
          mode="off"
          label="真实外发关闭"
          detail="当前只生成发送计划、本地演练和队列记录，不自动真实外发"
        />
      </div>

      <PanelStateNotice status={state.status} message={message} loadingMessage="正在读取待发送草稿和发送记录。" />
      <PanelStateNotice status={deliveryQueue.status} message={queueMessage} loadingMessage="正在读取发送队列状态。" />
      <DisabledReason show={Boolean(runQueueDisabledReason)} reason={runQueueDisabledReason} />
      <DisabledReason show={Boolean(runWorkerDisabledReason)} reason={runWorkerDisabledReason} />

      <div className="worker-summary-grid">
        {workerRun ? (
        <div className="worker-summary" aria-live="polite">
          <div>
            <span>最近发送检查</span>
            <strong>处理 {workerRun.processed} 条</strong>
          </div>
          <small>
            扫描 {workerRun.scanned} · 成功 {workerRun.succeeded} · 失败 {workerRun.failed} · 限流{" "}
            {workerRun.rate_limited} · 外部写入：否
          </small>
        </div>
        ) : null}

        {deliveryQueueRun ? (
          <div className="worker-summary queue-summary" aria-live="polite">
            <div>
              <span>最近发送队列</span>
              <strong>处理 {deliveryQueueRun.processed} 条</strong>
            </div>
            <small>
              成功 {deliveryQueueRun.succeeded} · 阻断 {deliveryQueueRun.blocked} · 重试{" "}
              {deliveryQueueRun.retry_scheduled} · 死信 {deliveryQueueRun.dead_lettered} · 外部写入：否
            </small>
          </div>
        ) : null}
      </div>

      {drafts.length === 0 && state.status === "ready" ? (
        <WorkspaceStateNotice
          kind="empty"
          message="暂无待发送草稿。AI 草稿通过人工审核后，才会进入这里等待发送前确认。"
          compact
        />
      ) : null}

      <ListToolbar
        view={listView}
        total={drafts.length}
        filteredTotal={pagedDrafts.total}
        statusOptions={[
          { label: "全部", value: "all" },
          { label: "待确认", value: "pending_confirmation" },
          { label: "待发送", value: "ready_to_send" },
          { label: "已入队列", value: "queued" },
          { label: "已有记录", value: "has_attempt" }
        ]}
        searchPlaceholder="搜索草稿、状态、会话编号"
        onChange={onListViewChange}
      />

      <div className="outbox-list">
        {pagedDrafts.items.map((draft) => {
          const attempts = attemptsByDraft[draft.id] ?? [];
          const queueJob = jobsByDraft[draft.id];
          const latestAttempt = attempts.length > 0 ? attempts[attempts.length - 1] : undefined;
          const connectorAttempt = attempts.find((attempt) => attempt.delivery_mode === "connector_noop");
          const canConfirm = hasToken && canManageDraft && !isLoading && draft.status === "pending_confirmation";
          const canDryRun = hasToken && canManageSendAttempt && !isLoading && draft.status === "ready_to_send" && attempts.length === 0;
          const canConnectorPlan = hasToken && canManageSendPlan && !isLoading && draft.status === "ready_to_send" && !connectorAttempt;
          const canCreateDeliveryJob =
            hasToken &&
            canManageDeliveryJob &&
            !isLoading &&
            !isQueueLoading &&
            draft.status === "ready_to_send" &&
            !queueJob;
          const connectorPermissionNote = canManageConnector ? "可自动检查连接器" : "需管理员预先配置连接器";
          const latestAttemptLabel =
            latestAttempt?.delivery_mode === "connector_noop"
              ? "渠道计划"
              : latestAttempt?.delivery_mode === "delivery_queue"
                ? "发送队列"
              : latestAttempt?.provider === "dry_run_worker"
                ? "发送检查"
                : "模拟发送";
          const actionLabel =
            draft.status === "pending_confirmation"
              ? "确认待发送"
              : latestAttempt
                ? latestAttempt.delivery_mode === "connector_noop"
                  ? "已有发送记录"
                  : latestAttempt.provider === "dry_run_worker"
                    ? "已检查"
                    : "已模拟"
                : "模拟发送";
          const actionIcon = draft.status === "pending_confirmation" ? <CheckCircle2 size={17} /> : <Send size={17} />;
          const primaryActionReason = !hasToken
            ? "按钮已禁用：请先登录本地管理员账号后写入真实待发送状态。"
            : isLoading
              ? "按钮已禁用：正在刷新草稿状态。"
              : draft.status === "pending_confirmation" && !canManageDraft
                ? "按钮已禁用：当前账号无权限确认草稿。"
                : draft.status === "ready_to_send" && !canManageSendAttempt
                  ? "按钮已禁用：当前账号无权限运行发送检查。"
                  : !canConfirm && !canDryRun
                    ? `按钮已禁用：当前草稿状态为 ${draft.status}，不满足确认或发送检查条件。`
                    : "";
          return (
            <article key={draft.id} className="outbox-row">
              <div className="outbox-copy">
                <div className="outbox-meta">
                  <span>草稿 #{draft.id}</span>
                  <small>{draft.status} · {draft.delivery_status}</small>
                </div>
                <p>{draft.reply_text}</p>
                <div className="attempt-line">
                  {latestAttempt ? (
                    <span>
                      {latestAttemptLabel} #{latestAttempt.attempt_number} · {latestAttempt.status} ·{" "}
                      {latestAttempt.delivery_status}
                    </span>
                  ) : (
                    <span>未执行模拟发送</span>
                  )}
                  {connectorAttempt ? (
                    <span className="connector-pill">
                      官方计划 #{connectorAttempt.attempt_number} · 外部写入：否
                    </span>
                  ) : null}
                  {queueJob ? (
                    <span className="connector-pill">
                      队列 #{queueJob.id} · {queueJob.status} · 尝试 {queueJob.attempts_count}/{queueJob.max_attempts}
                    </span>
                  ) : null}
                </div>
              </div>
              <div className="outbox-actions">
                <button
                  type="button"
                  className="primary-action"
                  onClick={() => {
                    if (draft.status === "pending_confirmation") {
                      onConfirm(draft.id);
                      return;
                    }
                    onDryRun(draft.id);
                  }}
                  disabled={!canConfirm && !canDryRun}
                >
                  {actionIcon}
                  {actionLabel}
                </button>
                <button
                  type="button"
                  className="ghost-action"
                  onClick={() => onConnectorPlan(draft)}
                  disabled={!canConnectorPlan}
                >
                  <Route size={17} />
                  {connectorAttempt ? "已生成计划" : "生成渠道计划"}
                </button>
                <button
                  type="button"
                  className="ghost-action"
                  onClick={() => onCreateDeliveryJob(draft)}
                  disabled={!canCreateDeliveryJob}
                >
                  <Activity size={17} />
                  {queueJob ? "已入队列" : "加入发送队列"}
                </button>
                {!canManageConnector && canManageSendPlan ? (
                  <small className="outbox-action-hint">{connectorPermissionNote}</small>
                ) : null}
                <DisabledReason show={Boolean(primaryActionReason)} reason={primaryActionReason} />
              </div>
            </article>
          );
        })}
      </div>
      <PaginationControls result={pagedDrafts} view={listView} onChange={onListViewChange} />
    </section>
  );
}

function FailureReviewPanel({
  state,
  listView,
  hasToken,
  canManageFailureReview,
  onListViewChange,
  onRefresh,
  onResolve
}: {
  state: FailureReviewState;
  listView: ListViewState;
  hasToken: boolean;
  canManageFailureReview: boolean;
  onListViewChange: (view: ListViewState) => void;
  onRefresh: () => void;
  onResolve: (item: DeliveryFailureReview) => void;
}) {
  const items = "items" in state ? state.items : [];
  const pagedItems = useMemo(
    () =>
      getPagedItems(items, listView, {
        statusMatcher: (item, status) => {
          if (status === "retryable") {
            return item.retryable;
          }
          if (status === "manual") {
            return !item.retryable;
          }
          if (status === "severe") {
            return ["high", "critical"].includes(item.severity);
          }
          return item.status === status || item.normalized_status === status || item.severity === status;
        },
        searchText: (item) => [
          item.provider,
          item.provider_status,
          item.provider_error_code,
          item.normalized_status,
          item.severity,
          item.review_reason,
          item.next_action,
          item.external_message_id
        ]
      }),
    [items, listView]
  );
  const isLoading = state.status === "loading";
  const message =
    state.status === "idle" ? state.message : state.status === "error" ? state.message : "";
  const resolveDisabledReason = formatAccessDisabledReason({
    hasToken,
    canManage: canManageFailureReview,
    isLoading,
    action: "处理失败复盘"
  });

  return (
    <section className="panel outbox-panel failure-panel" id="workspace-failures" aria-label="失败复盘队列">
      <div className="panel-heading">
        <div>
          <h2>失败复盘队列</h2>
          <p>集中查看平台回执异常、限流、授权失败和未知状态；当前只做内部复盘，不自动重发。</p>
        </div>
        <div className="panel-actions">
          <button type="button" className="ghost-action" onClick={onRefresh} disabled={!hasToken || isLoading}>
            <RefreshCw size={17} />
            {isLoading ? "刷新中" : "刷新"}
          </button>
        </div>
      </div>

      <div className="panel-state-row" aria-label="失败复盘数据状态">
        <DataSourceBadge
          mode={hasToken ? "real" : "demo"}
          label={hasToken ? REAL_DATA_LABEL : PREVIEW_DATA_LABEL}
          detail={hasToken ? "读取平台回执、错误归因和下一步动作" : "仅展示样例失败复盘结构"}
        />
        <DataSourceBadge
          mode="off"
          label="真实外发关闭"
          detail="复盘动作只关闭内部待办，不自动重发平台消息"
        />
      </div>

      <PanelStateNotice status={state.status} message={message} loadingMessage="正在读取失败复盘队列。" />
      <DisabledReason show={Boolean(resolveDisabledReason)} reason={resolveDisabledReason} />
      {items.length === 0 && state.status === "ready" ? (
        <WorkspaceStateNotice
          kind="empty"
          message="暂无待处理失败。出现平台回执异常、限流或队列阻断后，会在这里形成复盘项。"
          compact
        />
      ) : null}

      <ListToolbar
        view={listView}
        total={items.length}
        filteredTotal={pagedItems.total}
        statusOptions={[
          { label: "全部", value: "all" },
          { label: "待处理", value: "open" },
          { label: "严重", value: "severe" },
          { label: "可重试", value: "retryable" },
          { label: "需人工", value: "manual" }
        ]}
        searchPlaceholder="搜索平台、错误码、复盘原因、下一步"
        onChange={onListViewChange}
      />

      <div className="outbox-list">
        {pagedItems.items.map((item) => (
          <article key={item.id} className="outbox-row failure-row">
            <div className="outbox-copy">
              <div className="outbox-meta">
                <span>复盘 #{item.id}</span>
                <small>
                  {item.provider} · {item.normalized_status} · {item.severity}
                </small>
              </div>
              <p>
                平台状态：{item.provider_status || "unknown"}
                {item.provider_error_code ? ` · 错误码：${item.provider_error_code}` : ""} · 消息：
                {item.external_message_id || "未匹配平台消息"}
              </p>
              <div className="attempt-line">
                <span>{item.review_reason}</span>
                <span className={item.retryable ? "retry-pill" : "connector-pill"}>
                  {item.retryable ? "可重试" : "需人工确认"} · {item.next_action}
                </span>
              </div>
            </div>
            <div className="outbox-actions">
              <button
                type="button"
                className="primary-action"
                onClick={() => onResolve(item)}
                disabled={!hasToken || !canManageFailureReview || isLoading}
              >
                <CheckCircle2 size={17} />
                标记完成
              </button>
            </div>
          </article>
        ))}
      </div>
      <PaginationControls result={pagedItems} view={listView} onChange={onListViewChange} />
    </section>
  );
}

function createListViewState(pageSize = DEFAULT_PAGE_SIZE): ListViewState {
  return {
    query: "",
    status: "all",
    severity: "all",
    sourceType: "all",
    page: 1,
    pageSize
  };
}

function knowledgeGapListParams(view: ListViewState) {
  return {
    status: view.status,
    severity: view.severity,
    source_type: view.sourceType,
    query: view.query,
    page: view.page,
    page_size: view.pageSize
  };
}

function pagedResultFromServer<T>(data: { items: T[]; page: number; page_size: number; total: number }): PagedResult<T> {
  const pageSize = Math.max(1, data.page_size);
  const pageCount = Math.max(1, Math.ceil(data.total / pageSize));
  const start = data.total === 0 ? 0 : (data.page - 1) * pageSize + 1;
  return {
    items: data.items,
    total: data.total,
    page: data.page,
    pageCount,
    start,
    end: Math.min(data.total, start + data.items.length - 1)
  };
}

function getPagedItems<T>(
  items: T[],
  view: ListViewState,
  options: {
    statusMatcher?: (item: T, status: string) => boolean;
    searchText: (item: T) => Array<string | number | null | undefined>;
  }
): PagedResult<T> {
  const query = view.query.trim().toLowerCase();
  const filtered = items.filter((item) => {
    const statusMatches =
      view.status === "all" || (options.statusMatcher ? options.statusMatcher(item, view.status) : true);
    if (!statusMatches) {
      return false;
    }
    if (!query) {
      return true;
    }
    return options.searchText(item).some((value) => String(value ?? "").toLowerCase().includes(query));
  });
  const pageSize = Math.max(1, view.pageSize || DEFAULT_PAGE_SIZE);
  const pageCount = Math.max(1, Math.ceil(filtered.length / pageSize));
  const page = Math.min(Math.max(1, view.page), pageCount);
  const startIndex = (page - 1) * pageSize;
  const paged = filtered.slice(startIndex, startIndex + pageSize);
  return {
    items: paged,
    total: filtered.length,
    page,
    pageCount,
    start: filtered.length === 0 ? 0 : startIndex + 1,
    end: Math.min(filtered.length, startIndex + paged.length)
  };
}

function formatWaitingMinutes(value: number) {
  if (value <= 0) {
    return "无";
  }
  if (value < 60) {
    return `${value} 分钟`;
  }
  const hours = Math.floor(value / 60);
  const minutes = value % 60;
  return minutes > 0 ? `${hours} 小时 ${minutes} 分钟` : `${hours} 小时`;
}

function formatSlaLabel(value: string) {
  if (value === "breached") {
    return "SLA 超时";
  }
  if (value === "warning") {
    return "SLA 临近";
  }
  if (value === "ok") {
    return "SLA 正常";
  }
  if (value === "paused") {
    return "SLA 暂停";
  }
  if (value === "completed") {
    return "SLA 完成";
  }
  return "SLA 未开始";
}

function formatPriorityLabel(value: string) {
  const labels: Record<string, string> = {
    critical: "严重",
    urgent: "紧急",
    high: "高优先",
    medium: "中优先",
    normal: "普通",
    low: "低优先"
  };
  return labels[value] ?? value;
}

function conversationActionNote(action: ConversationWorkflowActionName) {
  const notes: Record<ConversationWorkflowActionName, string> = {
    claim: "坐席领取会话",
    release: "坐席释放会话回公共池",
    transfer: "坐席转派会话",
    close: "坐席关闭对话",
    resolve: "坐席标记会话已解决",
    follow_up: "坐席标记会话需跟进",
    wait_customer: "坐席标记等待客户回复",
    reopen: "坐席重新打开会话",
    note: "坐席补充会话备注"
  };
  return notes[action];
}

function normalizeTicketPriority(value: string): "low" | "normal" | "high" | "urgent" {
  if (value === "critical" || value === "urgent") {
    return "urgent";
  }
  if (value === "high") {
    return "high";
  }
  if (value === "low") {
    return "low";
  }
  return "normal";
}

function supportTicketActionNote(statusValue: "in_progress" | "pending_customer" | "resolved") {
  const notes: Record<"in_progress" | "pending_customer" | "resolved", string> = {
    in_progress: "坐席已接手处理该工单。",
    pending_customer: "已向客户补充提问，等待客户进一步回复。",
    resolved: "工单已完成处理，等待后续抽检或客户追问。"
  };
  return notes[statusValue];
}

function formatTicketStatus(value: string) {
  const labels: Record<string, string> = {
    open: "待处理",
    in_progress: "处理中",
    pending_customer: "等客户",
    resolved: "已解决",
    closed: "已关闭",
    canceled: "已取消"
  };
  return labels[value] ?? value;
}

function formatLeadStage(value: string) {
  const labels: Record<string, string> = {
    new: "新线索",
    contacted: "已联系",
    proposal: "待报价",
    won: "已成交",
    invalid: "无效",
    lost: "流失"
  };
  return labels[value] ?? value;
}

function formatLeadIntent(value: string) {
  const labels: Record<string, string> = {
    hot: "高意向",
    warm: "中意向",
    cold: "低意向"
  };
  return labels[value] ?? "未判断";
}

function normalizeLeadIntentFromConversation(item: ConversationInboxItem): "cold" | "warm" | "hot" {
  const text = `${item.subject} ${item.last_message_preview}`;
  if (["报价", "价格", "合同", "采购", "预算", "付款", "私有化"].some((keyword) => text.includes(keyword))) {
    return "hot";
  }
  if (["试点", "部署", "方案", "接入", "展示"].some((keyword) => text.includes(keyword))) {
    return "warm";
  }
  if (["critical", "high"].includes(item.priority)) {
    return "warm";
  }
  return "cold";
}

function leadStageActionNote(stage: "contacted" | "proposal" | "won" | "invalid" | "lost") {
  const notes: Record<"contacted" | "proposal" | "won" | "invalid" | "lost", string> = {
    contacted: "已完成首次联系，下一步确认预算、决策人和上线时间。",
    proposal: "已进入方案或报价阶段，下一步补齐报价边界和交付范围。",
    won: "线索已成交，下一步进入交付建档和客户成功移交。",
    invalid: "线索暂不符合目标客户或需求不成立，后续仅保留记录。",
    lost: "线索流失，后续复盘原因并优化知识库和报价口径。"
  };
  return notes[stage];
}

function canUpdateLead(lead: SalesLead, hasToken: boolean, isLoading: boolean) {
  if (!hasToken || isLoading) {
    return false;
  }
  return !["won", "invalid", "lost"].includes(lead.stage);
}

function buildContactProfileDetailFromLocal(
  profile: ContactProfile | null,
  conversations: ConversationInboxItem[],
  leads: SalesLead[],
  tickets: SupportTicket[]
): ContactProfileDetail | null {
  if (!profile) {
    return null;
  }
  const recentConversations: ContactConversationSummary[] = conversations
    .filter((item) => item.contact_id === profile.id)
    .slice(0, 8)
    .map((item) => ({
      id: item.id,
      channel_id: item.channel_id,
      channel_name: item.channel_name,
      channel_type: item.channel_type,
      status: item.status,
      priority: item.priority,
      subject: item.subject,
      last_message_at: item.last_message_at,
      last_message_preview: item.last_message_preview
    }));
  const openLeads = leads
    .filter((lead) => lead.contact_id === profile.id)
    .filter((lead) => ["new", "contacted", "proposal"].includes(lead.stage))
    .slice(0, 8);
  const openTickets: ContactTicketSummary[] = tickets
    .filter((ticket) => ticket.contact_id === profile.id)
    .filter((ticket) => ["open", "in_progress", "pending_customer"].includes(ticket.status))
    .slice(0, 8)
    .map((ticket) => ({
      id: ticket.id,
      subject: ticket.subject,
      status: ticket.status,
      priority: ticket.priority,
      sla_status: ticket.sla_status,
      updated_at: ticket.updated_at
    }));
  return {
    ...profile,
    recent_conversations: recentConversations,
    open_leads: openLeads,
    open_tickets: openTickets
  };
}

function formatSlaTarget(minutes: number) {
  if (minutes < 60) {
    return `${minutes} 分钟`;
  }
  const hours = Math.floor(minutes / 60);
  const rest = minutes % 60;
  if (hours < 24) {
    return rest > 0 ? `${hours} 小时 ${rest} 分钟` : `${hours} 小时`;
  }
  const days = Math.floor(hours / 24);
  const dayHours = hours % 24;
  return dayHours > 0 ? `${days} 天 ${dayHours} 小时` : `${days} 天`;
}

function canUpdateTicket(ticket: SupportTicket, hasToken: boolean, isLoading: boolean) {
  if (!hasToken || isLoading) {
    return false;
  }
  return !["resolved", "closed", "canceled"].includes(ticket.status);
}

function canClaimConversation(
  item: ConversationInboxItem,
  currentUserId: number | null,
  hasToken: boolean,
  isLoading: boolean
) {
  if (!hasToken || isLoading || !currentUserId || Number.isNaN(currentUserId)) {
    return false;
  }
  if (item.status === "resolved") {
    return true;
  }
  return item.assigned_user_id === null || item.assigned_user_id === currentUserId;
}

function canWorkConversation(item: ConversationInboxItem, hasToken: boolean, isLoading: boolean) {
  return hasToken && !isLoading && item.status !== "resolved";
}

function canReleaseConversation(item: ConversationInboxItem, hasToken: boolean, isLoading: boolean) {
  return hasToken && !isLoading && item.assigned_user_id !== null && item.status !== "resolved";
}

function parseEvaluationCases(text: string) {
  return text
    .split(/\n+/)
    .map((line, index) => {
      const [
        questionPart,
        termsPart = "",
        sourcePart = "",
        forbiddenPart = "",
        handoffPart = "",
        autoReplyPart = "",
        sourceCategoryPart = ""
      ] = line.split("|").map((item) => item.trim());
      const expectedTerms = termsPart
        .split(/[,，、]/)
        .map((term) => term.trim())
        .filter(Boolean);
      const forbiddenTerms = splitFreeTextList(forbiddenPart);
      const expectedHumanReview = parseBooleanIntent(handoffPart);
      const allowAutoReply = autoReplyPart ? parseBooleanIntent(autoReplyPart) : !expectedHumanReview;
      return {
        external_case_id: `ui-case-${index + 1}`,
        source_channel: "manual",
        source_category: sourceCategoryPart,
        question: questionPart,
        question_type: expectedHumanReview ? "risk_handoff" : "standard_customer_question",
        expected_terms: expectedTerms,
        expected_source_uri: sourcePart,
        expected_human_review: expectedHumanReview,
        allow_auto_reply: allowAutoReply,
        forbidden_terms: forbiddenTerms,
        risk_level: expectedHumanReview || forbiddenTerms.length > 0 ? "high" : "low",
        required_citation: true,
        priority: (index + 1) * 10,
        status: "active" as const
      };
    })
    .filter((item) => item.question);
}

function parseBooleanIntent(value: string) {
  const normalized = value.trim().toLowerCase();
  if (!normalized) {
    return false;
  }
  return ["1", "true", "yes", "y", "是", "需要", "转人工", "人工", "禁止自动"].includes(normalized);
}

function parseCustomerKnowledgeCsv(text: string): Record<string, string>[] {
  const rows = text
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean)
    .map(parseCsvLine);
  const [headers = [], ...dataRows] = rows;
  return dataRows
    .map((row) =>
      headers.reduce<Record<string, string>>((record, header, index) => {
        record[header.trim()] = row[index]?.trim() ?? "";
        return record;
      }, {})
    )
    .filter((record) => Object.values(record).some(Boolean));
}

function parseCsvLine(line: string): string[] {
  const result: string[] = [];
  let current = "";
  let inQuotes = false;
  for (let index = 0; index < line.length; index += 1) {
    const char = line[index];
    const next = line[index + 1];
    if (char === '"' && inQuotes && next === '"') {
      current += '"';
      index += 1;
      continue;
    }
    if (char === '"') {
      inQuotes = !inQuotes;
      continue;
    }
    if (char === "," && !inQuotes) {
      result.push(current);
      current = "";
      continue;
    }
    current += char;
  }
  result.push(current);
  return result;
}

function buildCustomerKnowledgeUpdatePackageFromCsv(text: string) {
  const rows = parseCustomerKnowledgeCsv(text);
  const businessObjectsByRef = new Map<
    string,
    {
      ref: string;
      type: BusinessObjectType;
      title: string;
      aliases: string[];
      summary: string;
      status: "active";
    }
  >();
  const objectCards: Array<{
    business_object_ref: string;
    question: string;
    answer: string;
    trigger_keywords: string[];
    source: string;
    status: "active";
  }> = [];
  const knowledgeDocuments: Array<{
    title: string;
    source_type: string;
    source_uri: string;
    tags: string[];
    status: "active";
    raw_text: string;
  }> = [];
  const evaluationCases: Array<{
    external_case_id: string;
    question: string;
    expected_terms: string[];
    expected_source_uri: string;
    forbidden_terms: string[];
    expected_human_review: boolean;
    allow_auto_reply: boolean;
    status: "active";
  }> = [];

  rows.forEach((row, index) => {
    const typeText = row["资料类型"] || "标准问答";
    const objectTitle = row["对象名称"];
    const objectType = normalizeBusinessObjectType(row["对象类型"]);
    const ref = objectTitle ? slugifyKnowledgeRef(objectTitle, `object-${index + 1}`) : "";
    const source = row["来源"] || "客户资料模板";
    const aliases = splitFreeTextList(row["别名"] || "");
    const question = row["客户问题"];
    const answer = row["标准答案"];
    const processTitle = row["流程标题"];
    const processBody = row["流程正文"];
    const blockedTerms = splitFreeTextList(row["禁用承诺词"] || "");
    const handoffTerms = splitFreeTextList(row["转人工词"] || "");
    const regressionQuestion = row["回归问题"];
    const expectedTerms = splitFreeTextList(row["期望词"] || "");
    const forbiddenTerms = splitFreeTextList(row["禁止词"] || "");

    if (objectTitle && ref && !businessObjectsByRef.has(ref)) {
      businessObjectsByRef.set(ref, {
        ref,
        type: objectType,
        title: objectTitle,
        aliases,
        summary: answer || processBody || `${objectTitle} 的客户资料对象。`,
        status: "active"
      });
    }
    if (objectTitle && question && answer && ref) {
      objectCards.push({
        business_object_ref: ref,
        question,
        answer,
        trigger_keywords: splitFreeTextList(`${aliases.join(";")};${expectedTerms.join(";")}`),
        source,
        status: "active"
      });
    }
    if (processTitle || processBody || blockedTerms.length > 0 || handoffTerms.length > 0) {
      const title = processTitle || (typeText.includes("风险") ? "禁用承诺与转人工规则" : "客户流程政策");
      const rawTextParts = [
        processBody,
        blockedTerms.length > 0 ? `禁用承诺：${blockedTerms.join("、")}` : "",
        handoffTerms.length > 0 ? `转人工规则：${handoffTerms.join("、")}` : ""
      ].filter(Boolean);
      knowledgeDocuments.push({
        title,
        source_type: "customer_intake_template",
        source_uri: source || `customer-intake://row-${index + 1}`,
        tags: [typeText, ...blockedTerms.length ? ["禁用承诺"] : [], ...handoffTerms.length ? ["转人工规则"] : []],
        status: "active",
        raw_text: rawTextParts.join("\n")
      });
    }
    if (regressionQuestion) {
      evaluationCases.push({
        external_case_id: `customer-intake-${index + 1}`,
        question: regressionQuestion,
        expected_terms: expectedTerms,
        expected_source_uri: source,
        forbidden_terms: forbiddenTerms,
        expected_human_review: handoffTerms.length > 0 || forbiddenTerms.length > 0,
        allow_auto_reply: handoffTerms.length === 0 && forbiddenTerms.length === 0,
        status: "active"
      });
    }
  });

  const timestamp = new Date().toISOString().slice(0, 10).replace(/-/g, "");
  return {
    schema_version: "wanfa.knowledge_update_package.v1",
    package_id: `pkg-customer-intake-${timestamp}`,
    package_name: "客户资料导入包",
    source_diagnostic_filename: "customer-knowledge-intake.csv",
    notes: "由客户资料整理流程生成。导入前必须先检查资料包；导入不会触发外部平台发送。",
    business_objects: Array.from(businessObjectsByRef.values()),
    object_knowledge_cards: objectCards,
    knowledge_documents: knowledgeDocuments,
    evaluation_sets: [
      {
        name: "客户资料导入回归题集",
        description: "用于检查本次客户资料导入后，核心问题是否能命中对应知识。",
        status: "active",
        evaluation_mode: "customer_service_retrieval",
        cases: evaluationCases
      }
    ].filter((set) => set.cases.length > 0)
  };
}

function normalizeBusinessObjectType(value: string): BusinessObjectType {
  const normalized = value.trim().toLowerCase();
  if (["product", "商品"].includes(normalized)) return "product";
  if (["service", "服务"].includes(normalized)) return "service";
  if (["course", "课程"].includes(normalized)) return "course";
  if (["project", "项目"].includes(normalized)) return "project";
  if (["store", "门店"].includes(normalized)) return "store";
  return "package";
}

function slugifyKnowledgeRef(value: string, fallback: string) {
  const ascii = value
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9\u4e00-\u9fff]+/g, "-")
    .replace(/^-+|-+$/g, "");
  return ascii || fallback;
}

function splitFreeTextList(text: string): string[] {
  const seen = new Set<string>();
  return text
    .split(/[,，、;\n]/)
    .map((item) => item.trim())
    .filter((item) => {
      if (!item || seen.has(item)) {
        return false;
      }
      seen.add(item);
      return true;
    });
}

function splitTemplateImportLine(line: string): string[] {
  const cells: string[] = [];
  let current = "";
  let quoted = false;
  for (let index = 0; index < line.length; index += 1) {
    const char = line[index];
    const next = line[index + 1];
    if (char === "\"" && quoted && next === "\"") {
      current += "\"";
      index += 1;
      continue;
    }
    if (char === "\"") {
      quoted = !quoted;
      continue;
    }
    if (!quoted && (char === "," || char === "\t")) {
      cells.push(current.trim());
      current = "";
      continue;
    }
    current += char;
  }
  cells.push(current.trim());
  return cells;
}

function parseKnowledgeTemplateImportRows(text: string): KnowledgeImportTemplateRow[] {
  const lines = text
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean);
  if (lines.length <= 1) {
    return [];
  }
  const headers = splitTemplateImportLine(lines[0]).map((header) => header.trim());
  return lines.slice(1).map((line) => {
    const cells = splitTemplateImportLine(line);
    const valueFor = (field: string) => cells[headers.indexOf(field)] ?? "";
    return {
      business_object: valueFor("business_object"),
      question: valueFor("question"),
      answer: valueFor("answer"),
      trigger_keywords: splitFreeTextList(valueFor("trigger_keywords")),
      channel_scope: valueFor("channel_scope") || "website",
      risk_level: (valueFor("risk_level") || "normal") as KnowledgeImportTemplateRow["risk_level"],
      forbidden_commitments: splitFreeTextList(valueFor("forbidden_commitments")),
      handoff_rule: valueFor("handoff_rule"),
      source_note: valueFor("source_note"),
      status: (valueFor("status") || "active") as KnowledgeImportTemplateRow["status"]
    };
  });
}

function formatBusinessObjectType(value: BusinessObjectType | string) {
  const labels: Record<string, string> = {
    product: "商品",
    service: "服务",
    package: "套餐",
    course: "课程",
    project: "项目",
    store: "门店"
  };
  return labels[value] ?? value;
}

function formatKnowledgeUpdateResourceType(value: string) {
  const labels: Record<string, string> = {
    package: "更新包",
    knowledge_card: "通用问答",
    business_object: "业务对象",
    object_knowledge_card: "对象问答",
    knowledge_document: "知识文档",
    evaluation_set: "回归题集"
  };
  return labels[value] ?? value;
}

function formatKnowledgeUpdateAction(value: string) {
  const labels: Record<string, string> = {
    create: "新增",
    skip: "跳过",
    error: "错误"
  };
  return labels[value] ?? value;
}

function toKnowledgeEvaluationRunSummary(run: KnowledgeEvaluationRun): KnowledgeEvaluationRunSummary {
  const { case_results: _caseResults, ...summary } = run;
  return summary;
}

function downloadTextFile(body: string, filename: string, contentType: string) {
  const blob = new Blob([body], { type: contentType });
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
}

function downloadBinaryFile(bytes: Uint8Array, filename: string, contentType: string) {
  const arrayBuffer = bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength) as ArrayBuffer;
  const blob = new Blob([arrayBuffer], { type: contentType });
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
}

function decodeBase64ToBytes(value: string) {
  const binary = window.atob(value);
  const bytes = new Uint8Array(binary.length);
  for (let index = 0; index < binary.length; index += 1) {
    bytes[index] = binary.charCodeAt(index);
  }
  return bytes;
}

function downloadCustomerQualityReportFile(report: CustomerQualityReportExport) {
  if (report.body_encoding === "base64") {
    downloadBinaryFile(decodeBase64ToBytes(report.body), report.filename, report.content_type);
    return;
  }
  downloadTextFile(report.body, report.filename, report.content_type);
}

function downloadKnowledgeEvaluationReport(report: KnowledgeEvaluationRunReport) {
  downloadTextFile(report.body, report.filename, report.content_type);
}

function downloadDiagnosticBundle(bundle: DiagnosticBundle) {
  const blob = new Blob([JSON.stringify(bundle, null, 2)], { type: "application/json;charset=utf-8" });
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = bundle.filename || "wanfa-diagnostic.json";
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
}

function downloadDiagnosticUploadPackage(uploadPackage: DiagnosticUploadPackage) {
  const blob = new Blob([JSON.stringify(uploadPackage, null, 2)], { type: "application/json;charset=utf-8" });
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = uploadPackage.filename || "wanfa-diagnostic-upload.json";
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
}

function downloadDiagnosticIntakePackage(download: DiagnosticIntakeDownload) {
  downloadTextFile(download.body, download.filename || "wanfa-diagnostic-intake.json", `${download.content_type};charset=utf-8`);
}

function downloadDiagnosticRemediationPackage(download: DiagnosticRemediationRequestDownload) {
  downloadTextFile(download.body, download.filename || "wanfa-diagnostic-remediation.json", `${download.content_type};charset=utf-8`);
}

function normalizeAccountUser(user: AccountUser): AccountUser {
  return { ...user, roles: accountUserRoles(user) };
}

function accountUserRoles(user: AccountUser): string[] {
  return Array.isArray(user.roles) ? user.roles : [];
}

function formatRoleCodeLabel(value: string) {
  const labels: Record<string, string> = {
    owner: "负责人",
    admin: "管理员",
    agent: "客服",
    viewer: "只读"
  };
  return labels[value] ?? value;
}

function formatAccountRoleName(code: string, name: string) {
  const label = formatRoleCodeLabel(code);
  return label === code ? name : label;
}

function formatLocalBackupStatus(value: string) {
  const labels: Record<string, string> = {
    created: "已创建",
    verified: "已校验",
    verification_failed: "校验失败",
    failed: "失败"
  };
  return labels[value] ?? value;
}

function formatRestoreCheckName(value: string) {
  const labels: Record<string, string> = {
    backup_sha256_match: "摘要一致",
    backup_sqlite_integrity: "备份完整",
    offline_restore_tool_available: "恢复工具",
    fresh_pre_restore_backup: "二次备份",
    operator_confirmation: "人工确认",
    dry_run_rehearsal_ready: "演练状态"
  };
  return labels[value] ?? value;
}

function formatRestoreCheckStatus(value: string) {
  const labels: Record<string, string> = {
    pass: "通过",
    blocked: "阻断",
    pending: "待执行",
    warning: "需确认"
  };
  return labels[value] ?? value;
}

function formatByteSize(value: number) {
  if (!Number.isFinite(value) || value <= 0) {
    return "0 B";
  }
  if (value < 1024) {
    return `${value} B`;
  }
  if (value < 1024 * 1024) {
    return `${(value / 1024).toFixed(1)} KB`;
  }
  return `${(value / 1024 / 1024).toFixed(1)} MB`;
}

function formatDateTime(value: string | null) {
  if (!value) {
    return "时间未知";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return new Intl.DateTimeFormat("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit"
  }).format(date);
}

function formatColleagueStatus(value: string) {
  const labels: Record<string, string> = {
    online: "在线",
    busy: "忙碌",
    offline: "离线"
  };
  return labels[value] ?? value;
}

function getAvatarInitial(value: string) {
  const trimmed = value.trim();
  if (!trimmed) return "客";
  return trimmed.slice(0, 1).toUpperCase();
}

function formatWorkerHealthLabel(value: string) {
  const labels: Record<string, string> = {
    healthy: "健康",
    stale: "超时",
    failed: "失败",
    running: "运行中",
    idle: "空闲"
  };
  return labels[value] ?? value;
}

function formatRiskSeverityLabel(value: string) {
  const labels: Record<string, string> = {
    critical: "严重",
    warning: "警告",
    info: "提示"
  };
  return labels[value] ?? value;
}

function formatAlertStatusLabel(value: string) {
  const labels: Record<string, string> = {
    firing: "需处理",
    ok: "正常",
    muted: "已静默"
  };
  return labels[value] ?? value;
}

function formatAlertResponseTypeLabel(value: string) {
  const labels: Record<string, string> = {
    page: "立即处理",
    ticket: "跟进处理"
  };
  return labels[value] ?? value;
}

function formatMetricStatusLabel(value: string) {
  const labels: Record<string, string> = {
    critical: "严重",
    warning: "关注",
    ok: "正常"
  };
  return labels[value] ?? value;
}

function formatMetricLabels(labels: Record<string, string>) {
  const entries = Object.entries(labels).filter(([key]) => key !== "tenant_id");
  if (entries.length === 0) {
    return "租户级";
  }
  return entries.map(([key, value]) => `${sanitizeCustomerVisibleOpsText(key)}=${sanitizeCustomerVisibleOpsText(value)}`).join(" · ");
}

function formatMetricDisplayValue(metric: OpsMetric) {
  const value = Number.isInteger(metric.value) ? String(metric.value) : metric.value.toFixed(2);
  return metric.unit === "boolean" ? (metric.value ? "是" : "否") : `${value} ${metric.unit}`;
}

function sanitizeCustomerVisibleOpsText(value: string) {
  return value
    .replace(/outbox/g, "send_queue")
    .replace(/dry_run/g, "local_check")
    .replace(/provider/g, "channel");
}

function getTimeValue(value: string | null) {
  if (!value) {
    return 0;
  }
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? 0 : date.getTime();
}

function formatRelativeWait(value: string | null) {
  const timeValue = getTimeValue(value);
  if (!timeValue) {
    return "时间未知";
  }
  const minutes = Math.max(1, Math.round((Date.now() - timeValue) / 60000));
  if (minutes < 60) {
    return `${minutes} 分钟`;
  }
  const hours = Math.round(minutes / 60);
  if (hours < 24) {
    return `${hours} 小时`;
  }
  return `${Math.round(hours / 24)} 天`;
}

function formatPercent(value: number | null) {
  if (value === null || Number.isNaN(value)) {
    return "-";
  }
  return `${Math.round(value * 100)}%`;
}

function getOpsRangeStart(range: OpsRangeKey, now: number) {
  if (range === "today") {
    const startOfDay = new Date(now);
    startOfDay.setHours(0, 0, 0, 0);
    return startOfDay.getTime();
  }
  const days = range === "7d" ? 7 : 30;
  return now - days * 24 * 60 * 60 * 1000;
}

function formatOpsChannelLabel(channelId: number) {
  const labels: Record<number, string> = {
    101: "微信客服",
    102: "抖音店铺",
    103: "淘宝客服",
    104: "京东客服",
    105: "拼多多客服",
    106: "官网客服"
  };
  return labels[channelId] ?? `渠道 #${channelId}`;
}

function buildOpsChannelRows(
  reviewItems: HumanReviewInboxItem[],
  outboxDrafts: OutboxDraft[],
  failureReviews: DeliveryFailureReview[],
  deliveryJobs: OutboxDeliveryJob[]
) {
  const rows = new Map<number, { channelId: number; label: string; shortLabel: string; count: number; exceptionCount: number }>();
  const ensureRow = (channelId: number) => {
    const existing = rows.get(channelId);
    if (existing) {
      return existing;
    }
    const label = formatOpsChannelLabel(channelId);
    const row = {
      channelId,
      label,
      shortLabel: label.replace("客服", "").replace("店铺", ""),
      count: 0,
      exceptionCount: 0
    };
    rows.set(channelId, row);
    return row;
  };

  reviewItems.forEach((item) => {
    ensureRow(item.conversation.channel_id).count += 1;
  });
  outboxDrafts.forEach((draft) => {
    ensureRow(draft.channel_id).count += 1;
  });
  deliveryJobs.forEach((job) => {
    const row = ensureRow(job.channel_id);
    row.count += 1;
    if (["blocked", "dead_letter", "dead_lettered", "failed"].includes(job.status)) {
      row.exceptionCount += 1;
    }
  });
  failureReviews.forEach((review) => {
    const row = ensureRow(review.channel_id);
    row.count += 1;
    row.exceptionCount += 1;
  });

  const result = Array.from(rows.values()).sort((left, right) => right.count - left.count).slice(0, 6);
  return result.length > 0
    ? result
    : [{ channelId: 0, label: "暂无渠道样本", shortLabel: "暂无", count: 0, exceptionCount: 0 }];
}

function buildOpsTrendBuckets(
  events: Array<{ time: string | null; type: "review" | "draft" | "exception" }>,
  rangeStart: number,
  now: number,
  range: OpsRangeKey
) {
  const bucketCount = 6;
  const bucketMs = Math.max(1, (now - rangeStart) / bucketCount);
  const buckets = Array.from({ length: bucketCount }, (_, index) => {
    const bucketStart = rangeStart + index * bucketMs;
    return {
      label: formatOpsTrendBucketLabel(bucketStart, range),
      review: 0,
      draft: 0,
      exception: 0
    };
  });

  events.forEach((event) => {
    const timeValue = getTimeValue(event.time);
    if (!timeValue || timeValue < rangeStart || timeValue > now) {
      return;
    }
    const bucketIndex = Math.min(bucketCount - 1, Math.max(0, Math.floor((timeValue - rangeStart) / bucketMs)));
    buckets[bucketIndex][event.type] += 1;
  });

  return buckets;
}

function formatOpsTrendBucketLabel(timeValue: number, range: OpsRangeKey) {
  const date = new Date(timeValue);
  if (range === "today") {
    return `${String(date.getHours()).padStart(2, "0")}:00`;
  }
  return `${date.getMonth() + 1}/${date.getDate()}`;
}

function formatRate(count: number, total: number) {
  if (total <= 0) {
    return "-";
  }
  return `${Math.round((count / total) * 100)}%`;
}

function formatSignedPercent(value: number) {
  const rounded = Math.round(value * 100);
  if (rounded === 0) {
    return "0%";
  }
  return `${rounded > 0 ? "+" : ""}${rounded}%`;
}

function formatChannelShortName(value: string) {
  if (!value) {
    return "渠道";
  }
  return value.replace(/[（(].*?[)）]/g, "").replace(/客服|私信|店铺/g, "").trim() || value;
}

function formatTags(tags: string[]) {
  return tags.length > 0 ? tags.join(" / ") : "未标记";
}

function formatCitation(citation: Record<string, unknown>) {
  const sourceUri = typeof citation.source_uri === "string" ? citation.source_uri : "";
  const pageNumber = typeof citation.page_number === "number" ? `第 ${citation.page_number} 页` : "";
  const chunkIndex = typeof citation.chunk_index === "number" ? `片段 ${citation.chunk_index}` : "";
  return [pageNumber, chunkIndex, sourceUri || "未填写来源"].filter(Boolean).join(" · ");
}

function formatKnowledgeGapSource(value: string) {
  const labels: Record<string, string> = {
    human_review: "人审来源",
    evaluation_run: "评测来源",
    manual: "手动创建"
  };
  return labels[value] ?? value;
}

function formatKnowledgeGapStatus(value: string) {
  const labels: Record<string, string> = {
    open: "待处理",
    triaged: "已分诊",
    in_progress: "处理中",
    resolved: "已解决",
    rejected: "不需补充",
    archived: "已归档"
  };
  return labels[value] ?? value;
}

function formatKnowledgeGapSeverity(value: string) {
  const labels: Record<string, string> = {
    low: "低",
    medium: "中",
    high: "高",
    critical: "紧急"
  };
  return `严重度：${labels[value] ?? value}`;
}

function formatKnowledgeGapEvidence(gap: KnowledgeGap) {
  const evidence = gap.evidence_payload;
  const confidence = typeof evidence.top_confidence === "number"
    ? evidence.top_confidence
    : typeof evidence.confidence === "number"
      ? evidence.confidence
      : null;
  const retrievedCount =
    typeof evidence.retrieved_knowledge_count === "number"
      ? `知识 ${evidence.retrieved_knowledge_count}`
      : typeof evidence.top_score === "number"
        ? `分数 ${evidence.top_score.toFixed(2)}`
        : "";
  const confidenceText = confidence === null ? "" : `置信 ${formatPercent(confidence)}`;
  return [retrievedCount, confidenceText].filter(Boolean).join(" · ") || "证据待核对";
}

function formatPublicationType(value: string) {
  const labels: Record<string, string> = {
    publish_check: "发布前检查",
    publish: "正式发布",
    rollback: "回滚"
  };
  return labels[value] ?? value;
}

function formatPublicationStatus(value: string) {
  const labels: Record<string, string> = {
    passed: "已通过",
    blocked: "已阻断",
    published: "已发布",
    rolled_back: "已回滚"
  };
  return labels[value] ?? value;
}

function publicationCaseValue(item: Record<string, unknown>, key: string) {
  const value = item[key];
  if (typeof value === "boolean") {
    return value ? "true" : "false";
  }
  if (typeof value === "number") {
    return String(value);
  }
  if (typeof value === "string") {
    return value || "-";
  }
  return "-";
}

function knowledgeGapRemediationPayload(gap: KnowledgeGap): Record<string, unknown> {
  const remediation = gap.evidence_payload.remediation;
  return remediation && typeof remediation === "object" && !Array.isArray(remediation)
    ? (remediation as Record<string, unknown>)
    : {};
}

function knowledgeGapRegressionCaseId(gap: KnowledgeGap): string {
  const remediation = knowledgeGapRemediationPayload(gap);
  const value = remediation.regression_evaluation_case_id;
  return typeof value === "number" || typeof value === "string" ? String(value) : "";
}

function knowledgeGapPublishedDocumentId(gap: KnowledgeGap): string {
  const remediation = knowledgeGapRemediationPayload(gap);
  const value = remediation.published_document_id;
  return typeof value === "number" || typeof value === "string" ? String(value) : "";
}

function createDemoWorkspace() {
  const now = Date.now();
  const risks = ["critical", "high", "medium", "low"];
  const reasons = ["低置信回复", "价格与优惠需人工确认", "售后赔付风险", "无知识命中", "客户要求人工接待"];
  const intents = ["报价咨询", "售后政策", "试点部署", "发票合同", "渠道接入", "产品能力"];
  const demoChannels = [
    { id: 101, type: "wecom_demo", name: "微信客服样例" },
    { id: 102, type: "douyin_demo", name: "抖音店铺样例" },
    { id: 103, type: "taobao_demo", name: "淘宝客服样例" },
    { id: 104, type: "jd_demo", name: "京东客服样例" },
    { id: 105, type: "pdd_demo", name: "拼多多客服样例" },
    { id: 106, type: "website", name: "官网客服" }
  ];
  const channelIdentities: Record<number, ChannelIdentitySummary> = {
    101: {
      channelId: 101,
      platform: "微信客服",
      accountName: "万法常世AI客服测试",
      storeName: "企业微信客服账号",
      providerMode: "official_api",
      authorizationStatus: "sandbox_configuring",
      replyMode: "human_review_first",
      healthLabel: "等待URL验证",
      lastSyncLabel: PREVIEW_DATA_LABEL
    },
    102: {
      channelId: 102,
      platform: "抖音",
      accountName: "EricLee抖音测试号",
      storeName: "抖音私信 / 抖店客服",
      providerMode: "rpa_research",
      authorizationStatus: "rpa_research_only",
      replyMode: "research_draft_only",
      healthLabel: "只做草稿试验",
      lastSyncLabel: PREVIEW_DATA_LABEL
    },
    103: {
      channelId: 103,
      platform: "淘宝",
      accountName: "万法常世淘宝客服测试",
      storeName: "淘宝店铺客服",
      providerMode: "official_api",
      authorizationStatus: "official_configuring",
      replyMode: "draft_only",
      healthLabel: "等待服务商授权",
      lastSyncLabel: PREVIEW_DATA_LABEL
    },
    104: {
      channelId: 104,
      platform: "京东",
      accountName: "万法常世京东客服测试",
      storeName: "京东店铺客服",
      providerMode: "official_api",
      authorizationStatus: "official_configuring",
      replyMode: "draft_only",
      healthLabel: "等待店铺授权",
      lastSyncLabel: PREVIEW_DATA_LABEL
    },
    105: {
      channelId: 105,
      platform: "拼多多",
      accountName: "万法常世拼多多客服测试",
      storeName: "拼多多店铺客服",
      providerMode: "official_api",
      authorizationStatus: "official_configuring",
      replyMode: "draft_only",
      healthLabel: "等待授权确认",
      lastSyncLabel: PREVIEW_DATA_LABEL
    },
    106: {
      channelId: 106,
      platform: "官网",
      accountName: "万法常世官网客服",
      storeName: "官网嵌入式客服入口",
      providerMode: "website_widget",
      authorizationStatus: "website_ready",
      replyMode: "auto_with_handoff",
      healthLabel: "样例可用",
      lastSyncLabel: PREVIEW_DATA_LABEL
    }
  };
  const reviewItems: HumanReviewInboxItem[] = Array.from({ length: 18 }, (_, index) => {
    const id = 1001 + index;
    const riskLevel = risks[index % risks.length];
    const createdAt = new Date(now - (index + 1) * 11 * 60 * 1000).toISOString();
    const channel = demoChannels[index % demoChannels.length];
    return {
      id,
      tenant_id: 1,
      workflow_run_id: 3001 + index,
      conversation_id: 2001 + index,
      message_id: 5001 + index,
      status: "open",
      reason: reasons[index % reasons.length],
      risk_level: riskLevel,
      draft_reply: `您好，关于“${intents[index % intents.length]}”，我先根据当前知识库整理了可核对回复：${index % 2 === 0 ? "可以先说明标准范围，再邀请客户留下联系方式。" : "需要坐席确认客户场景后再发送。"} `,
      final_reply: "",
      assigned_user_id: index % 3 === 0 ? 1 : null,
      reviewer_id: null,
      resolution_note: "",
      created_at: createdAt,
      resolved_at: null,
      conversation: {
        id: 2001 + index,
        channel_id: channel.id,
        contact_id: 7001 + index,
        assigned_user_id: index % 3 === 0 ? 1 : null,
        assigned_team_id: 10 + (index % 2),
        status: index % 4 === 0 ? "waiting_human" : "bot_assisting",
        priority: riskLevel,
        subject: `客户 ${index + 1} · ${intents[index % intents.length]}`,
        last_message_at: createdAt,
        created_at: new Date(now - (index + 2) * 18 * 60 * 1000).toISOString()
      },
      trigger_message: {
        id: 5001 + index,
        conversation_id: 2001 + index,
        direction: "inbound",
        sender_type: "customer",
        content: demoQuestionForIndex(index),
        external_message_id: `demo-inbound-${id}`,
        created_at: createdAt
      },
      workflow: {
        id: 3001 + index,
        workflow_type: "trusted_inbound_copilot",
        status: "waiting_human_review",
        current_step: index % 4 === 0 ? "handoff_required" : "draft_generated",
        created_at: createdAt,
        updated_at: createdAt
      },
      evidence: {
        intent: intents[index % intents.length],
        retrieved_knowledge_count: index % 5 === 0 ? 0 : 2 + (index % 4),
        confidence: index % 5 === 0 ? 0.34 : 0.52 + (index % 4) * 0.09,
        risk_level: riskLevel,
        draft_source: index % 3 === 0 ? "qwen_route" : "faq_plus_rag",
        retrieval_mode: "bm25_vector_hybrid_shadow",
        retrieval_engine: "standard_ops_local_index",
        knowledge_matches: index % 5 === 0
          ? []
          : [
              {
                title: "试点部署服务说明",
                source_uri: "internal://docs/pilot-deployment",
                content_preview: "试点部署先完成知识库、人工审核、外发门禁和白名单测试。",
                answer: "试点阶段默认保留人工审核与外发确认。"
              },
              {
                title: "售后与发票政策",
                source_uri: "internal://docs/service-policy",
                content_preview: "退款、赔付、合同、发票类问题应进入人工确认。",
                answer: "高风险问题不能直接自动外发。"
              }
            ],
        model_call: {
          provider: "bailian",
          model: index % 2 === 0 ? "qwen-plus" : "qwen-turbo",
          route_name: index % 4 === 0 ? "risk_guarded" : "standard_support",
          status: "drafted"
        },
        auto_reply_threshold: 0.76
      }
    };
  });

  const outboxDrafts: OutboxDraft[] = Array.from({ length: 16 }, (_, index) => {
    const ready = index % 2 === 0;
    const channel = demoChannels[index % demoChannels.length];
    return {
      id: 4001 + index,
      tenant_id: 1,
      conversation_id: reviewItems[index % reviewItems.length].conversation_id,
      channel_id: channel.id,
      contact_id: 7001 + index,
      source_review_task_id: index < reviewItems.length ? reviewItems[index].id : null,
      source_workflow_run_id: index < reviewItems.length ? reviewItems[index].workflow_run_id : null,
      source_message_id: index < reviewItems.length ? reviewItems[index].message_id : null,
      status: ready ? "ready_to_send" : "pending_confirmation",
      delivery_status: ready ? "queued_pending" : "needs_confirmation",
      reply_text: `样例草稿 ${index + 1}：已基于知识库整理回复，真实外发前仍需人工确认。`,
      idempotency_key: `demo-outbox-${index + 1}`,
      confirmation_note: ready ? "样例：已确认进入待发送" : "",
      cancellation_reason: "",
      created_at: new Date(now - (index + 1) * 9 * 60 * 1000).toISOString(),
      updated_at: new Date(now - (index + 1) * 7 * 60 * 1000).toISOString(),
      confirmed_at: ready ? new Date(now - (index + 1) * 5 * 60 * 1000).toISOString() : null,
      canceled_at: null,
      sent_at: null
    };
  });

  const attemptsByDraft: Record<number, OutboxSendAttempt[]> = Object.fromEntries(
    outboxDrafts.map((draft, index) => {
      const attempts: OutboxSendAttempt[] =
        draft.status === "ready_to_send" && index % 3 !== 1
          ? [
              {
                id: 6001 + index,
                outbox_draft_id: draft.id,
                attempt_number: 1,
                delivery_mode: index % 3 === 0 ? "connector_noop" : "dry_run",
                provider: index % 3 === 0 ? "wecom_noop" : "dry_run_worker",
                status: "succeeded",
                delivery_status: "planned_not_sent",
                external_message_id: "",
                request_payload: { external_write: false },
                response_payload: { accepted: true, demo: true },
                operator_note: "本地初始化数据：未请求外部平台写入",
                finished_at: new Date(now - (index + 1) * 4 * 60 * 1000).toISOString(),
                sent_at: null
              }
            ]
          : [];
      return [draft.id, attempts];
    })
  );

  const readyDrafts = outboxDrafts.filter((draft) => draft.status === "ready_to_send");
  const deliveryJobs: OutboxDeliveryJob[] = readyDrafts.slice(0, 12).map((draft, index) => ({
    id: 8001 + index,
    tenant_id: 1,
    outbox_draft_id: draft.id,
    channel_id: draft.channel_id,
    connector_id: null,
    status: index % 6 === 0 ? "blocked" : index % 5 === 0 ? "retry_scheduled" : "pending",
    priority: 100 + index,
    attempts_count: index % 3,
    max_attempts: 3,
    locked_by: "",
    locked_at: null,
    next_run_at: new Date(now + (index + 1) * 10 * 60 * 1000).toISOString(),
    idempotency_key: `demo-delivery-job-${index + 1}`,
    external_write_requested: false,
    external_write_permitted: false,
    last_attempt_id: attemptsByDraft[draft.id]?.[0]?.id ?? null,
    last_error: index % 6 === 0 ? "external_write_disabled" : "",
    dead_letter_reason: "",
    created_by_id: 1,
    created_at: draft.created_at,
    updated_at: draft.updated_at,
    completed_at: null
  }));

  const failureReviews: DeliveryFailureReview[] = Array.from({ length: 8 }, (_, index) => ({
    id: 9001 + index,
    tenant_id: 1,
    channel_id: demoChannels[index % demoChannels.length].id,
    connector_id: null,
    receipt_id: 9101 + index,
    matched_attempt_id: 6001 + index,
    outbox_draft_id: outboxDrafts[index]?.id ?? null,
    provider: index % 2 === 0 ? "wecom_noop" : "website_widget",
    external_message_id: `demo-receipt-${index + 1}`,
    provider_status: index % 2 === 0 ? "rate_limited" : "blocked",
    provider_error_code: index % 2 === 0 ? "45009" : "EXTERNAL_WRITE_DISABLED",
    normalized_status: index % 2 === 0 ? "rate_limited" : "blocked",
    severity: index % 3 === 0 ? "high" : "medium",
    retryable: index % 2 === 0,
    review_reason: index % 2 === 0 ? "平台限流，需要延后重试" : "真实外发总开关关闭",
    next_action: index % 2 === 0 ? "检查配额与重试时间" : "确认上线审批和白名单",
    status: "open",
    resolution_note: "",
    resolved_by_id: null,
    created_at: new Date(now - (index + 1) * 14 * 60 * 1000).toISOString(),
    updated_at: new Date(now - (index + 1) * 8 * 60 * 1000).toISOString(),
    resolved_at: null
  }));

  const conversationInboxItems: ConversationInboxItem[] = reviewItems.map((item, index) => {
    const channel = demoChannels[index % demoChannels.length];
    const waitingMinutes = Math.max(1, Math.round((now - getTimeValue(item.conversation.last_message_at)) / 60000));
    const relatedDrafts = outboxDrafts.filter((draft) => draft.conversation_id === item.conversation_id);
    const relatedFailures = failureReviews.filter((failure) =>
      relatedDrafts.some((draft) => draft.id === failure.outbox_draft_id)
    );
    const slaStatus = waitingMinutes >= 60 ? "breached" : waitingMinutes >= 30 ? "warning" : "ok";
    return {
      id: item.conversation_id,
      tenant_id: item.tenant_id,
      channel_id: item.conversation.channel_id,
      channel_type: channel.type,
      channel_name: channel.name,
      contact_id: item.conversation.contact_id,
      contact_display_name: `客户 ${index + 1}`,
      assigned_user_id: item.conversation.assigned_user_id,
      assigned_team_id: item.conversation.assigned_team_id,
      status: item.conversation.status === "bot_assisting" ? "bot" : item.conversation.status,
      priority: item.conversation.priority,
      subject: item.conversation.subject,
      last_message_at: item.conversation.last_message_at,
      created_at: item.conversation.created_at,
      last_message_preview: item.trigger_message?.content ?? "",
      last_message_direction: "inbound",
      last_customer_message_at: item.conversation.last_message_at,
      waiting_minutes: waitingMinutes,
      sla_status: slaStatus,
      sla_due_at: new Date(getTimeValue(item.conversation.last_message_at) + 30 * 60 * 1000).toISOString(),
      human_review_open_count: item.status === "open" ? 1 : 0,
      outbox_pending_count: relatedDrafts.filter((draft) =>
        ["pending_confirmation", "ready_to_send"].includes(draft.status)
      ).length,
      delivery_failure_open_count: relatedFailures.length,
      next_action: relatedFailures.length > 0
        ? "处理发送失败"
        : item.status === "open"
          ? "审核 AI 草稿"
          : relatedDrafts.length > 0
            ? "确认待发送草稿"
            : "接待客户或触发 AI 回复"
    };
  });

  const supportTicketItems: SupportTicket[] = conversationInboxItems.slice(0, 12).map((item, index) => {
    const statusCycle = ["open", "in_progress", "pending_customer", "resolved"];
    const status = statusCycle[index % statusCycle.length];
    const priority = normalizeTicketPriority(item.priority);
    const targetMinutes = priority === "urgent" ? 30 : priority === "high" ? 60 : priority === "low" ? 1440 : 240;
    const dueAt =
      status === "resolved"
        ? new Date(now - (index + 1) * 30 * 60 * 1000).toISOString()
        : index % 5 === 0
          ? new Date(now - 18 * 60 * 1000).toISOString()
          : index % 4 === 0
            ? new Date(now + 8 * 60 * 1000).toISOString()
            : new Date(now + targetMinutes * 60 * 1000).toISOString();
    const slaStatus =
      status === "resolved"
        ? "completed"
        : status === "pending_customer"
          ? "paused"
          : getTimeValue(dueAt) <= now
            ? "breached"
            : getTimeValue(dueAt) <= now + 15 * 60 * 1000
              ? "warning"
              : "ok";
    return {
      id: 17001 + index,
      tenant_id: item.tenant_id,
      conversation_id: item.id,
      channel_id: item.channel_id,
      channel_name: item.channel_name,
      channel_type: item.channel_type,
      contact_id: item.contact_id,
      contact_display_name: item.contact_display_name,
      subject: item.subject || `工单 ${index + 1}`,
      description: item.last_message_preview || "由样例会话生成的客服工单，用于展示 SLA 与坐席处理流。",
      status,
      priority,
      source_type: "conversation",
      source_ref: `conversation:${item.id}`,
      assigned_user_id: index % 3 === 0 ? 1 : null,
      assigned_team_id: null,
      sla_target_minutes: targetMinutes,
      sla_due_at: dueAt,
      sla_status: slaStatus,
      resolution_note: status === "resolved" ? "样例：已完成处理并等待质量抽检。" : "",
      created_by_id: 1,
      updated_by_id: 1,
      resolved_by_id: status === "resolved" ? 1 : null,
      created_at: new Date(now - (index + 1) * 38 * 60 * 1000).toISOString(),
      updated_at: new Date(now - (index + 1) * 12 * 60 * 1000).toISOString(),
      resolved_at: status === "resolved" ? new Date(now - (index + 1) * 8 * 60 * 1000).toISOString() : null
    };
  });

  const salesLeadItems: SalesLead[] = conversationInboxItems.slice(0, 10).map((item, index) => {
    const stageCycle = ["new", "contacted", "proposal", "won", "invalid"];
    const stage = stageCycle[index % stageCycle.length];
    const intentLevel = index % 4 === 0 ? "hot" : index % 3 === 0 ? "cold" : "warm";
    return {
      id: 18001 + index,
      tenant_id: item.tenant_id,
      contact_id: item.contact_id,
      contact_display_name: item.contact_display_name,
      channel_id: item.channel_id,
      channel_name: item.channel_name,
      channel_type: item.channel_type,
      conversation_id: item.id,
      title: `${item.contact_display_name || `客户 ${index + 1}`} · ${index % 2 === 0 ? "试点部署咨询" : "报价方案跟进"}`,
      summary: item.last_message_preview || "由样例会话生成的线索摘要。",
      stage,
      intent_level: intentLevel,
      expected_budget: index % 4 === 0 ? "5-15 万试点预算待确认" : index % 3 === 0 ? "预算未明确" : "2-6 万入门试点",
      next_step:
        stage === "won"
          ? "移交交付并建立客户成功跟进记录。"
          : stage === "proposal"
            ? "补齐需求边界后发送正式报价。"
            : "确认预算、决策人、渠道范围和上线时间。",
      owner_user_id: index % 3 === 0 ? 1 : null,
      source_type: "conversation",
      source_ref: `conversation:${item.id}`,
      latest_message_preview: item.last_message_preview,
      next_follow_up_at: new Date(now + (index + 1) * 24 * 60 * 60 * 1000).toISOString(),
      closed_at: ["won", "invalid", "lost"].includes(stage) ? new Date(now - (index + 1) * 10 * 60 * 1000).toISOString() : null,
      created_by_id: 1,
      updated_by_id: 1,
      created_at: new Date(now - (index + 1) * 42 * 60 * 1000).toISOString(),
      updated_at: new Date(now - (index + 1) * 16 * 60 * 1000).toISOString()
    };
  });

  const contactProfileItems: ContactProfile[] = conversationInboxItems.slice(0, 12).map((item, index) => {
    const contactLeads = salesLeadItems.filter((lead) => lead.contact_id === item.contact_id);
    const contactTickets = supportTicketItems.filter((ticket) => ticket.contact_id === item.contact_id);
    const activeLeadCount = contactLeads.filter((lead) => ["new", "contacted", "proposal"].includes(lead.stage)).length;
    const openTicketCount = contactTickets.filter((ticket) =>
      ["open", "in_progress", "pending_customer"].includes(ticket.status)
    ).length;
    return {
      id: item.contact_id,
      tenant_id: item.tenant_id,
      display_name: item.contact_display_name,
      phone: `138****${String(8800 + index).slice(-4)}`,
      wechat: `wx_demo_${index + 1}`,
      created_at: item.created_at,
      conversation_count: conversationInboxItems.filter((conversation) => conversation.contact_id === item.contact_id).length,
      open_conversation_count: item.status === "resolved" ? 0 : 1,
      support_ticket_count: contactTickets.length,
      open_support_ticket_count: openTicketCount,
      lead_count: contactLeads.length,
      active_lead_count: activeLeadCount,
      highest_intent_level:
        contactLeads.some((lead) => lead.intent_level === "hot")
          ? "hot"
          : contactLeads.some((lead) => lead.intent_level === "warm")
            ? "warm"
            : "cold",
      latest_channel_id: item.channel_id,
      latest_channel_name: item.channel_name,
      latest_channel_type: item.channel_type,
      last_message_at: item.last_message_at,
      last_message_preview: item.last_message_preview,
      next_action:
        openTicketCount > 0
          ? "优先处理开放工单和 SLA。"
          : activeLeadCount > 0
            ? "推进线索并确认预算、决策人和上线时间。"
            : item.human_review_open_count > 0
              ? "审核 AI 草稿后再回复客户。"
              : "保持观察，等待新入站或定期回访。"
    };
  });
  const contactProfileDetail = buildContactProfileDetailFromLocal(
    contactProfileItems[0] ?? null,
    conversationInboxItems,
    salesLeadItems,
    supportTicketItems
  );

  const businessObjects: BusinessObject[] = [
    {
      id: 9001,
      tenant_id: 1,
      type: "product",
      title: "AI 客服入门验证包",
      external_id: "lite-a",
      summary: "适合先验证官网客服、核心 FAQ、留资和人工接管流程的中小企业。",
      attrs_json: { delivery_days: 7, channels: ["web", "wechat_service"] },
      aliases: ["入门版", "Lite A", "官网客服试点"],
      knowledge_card_count: 2,
      status: "active",
      created_by_id: 1,
      updated_by_id: 1,
      created_at: new Date(now - 5 * 24 * 60 * 60 * 1000).toISOString(),
      updated_at: new Date(now - 2 * 60 * 60 * 1000).toISOString()
    },
    {
      id: 9002,
      tenant_id: 1,
      type: "service",
      title: "企业微信官方接入服务",
      external_id: "wecom-service",
      summary: "用于通过官方微信客服能力接入收发消息、验签、人工审核和白名单外发测试。",
      attrs_json: { require_domain: true, official_api_only: true },
      aliases: ["企微接入", "微信客服接入", "官方接口"],
      knowledge_card_count: 1,
      status: "active",
      created_by_id: 1,
      updated_by_id: 1,
      created_at: new Date(now - 4 * 24 * 60 * 60 * 1000).toISOString(),
      updated_at: new Date(now - 90 * 60 * 1000).toISOString()
    },
    {
      id: 9003,
      tenant_id: 1,
      type: "package",
      title: "标准运营版套餐",
      external_id: "standard-ops",
      summary: "面向已有稳定咨询量的企业，包含知识库、评测、对话台、告警和运维视图。",
      attrs_json: { delivery_days: 21, includes_bi: true },
      aliases: ["标准版", "运营版", "客服中台"],
      knowledge_card_count: 1,
      status: "active",
      created_by_id: 1,
      updated_by_id: 1,
      created_at: new Date(now - 3 * 24 * 60 * 60 * 1000).toISOString(),
      updated_at: new Date(now - 45 * 60 * 1000).toISOString()
    }
  ];

  const objectCardsByObject: Record<number, ObjectKnowledgeCard[]> = {
    9001: [
      {
        id: 9101,
        tenant_id: 1,
        business_object_id: 9001,
        question: "入门验证包适合什么客户？",
        answer: "适合先验证官网客服、核心 FAQ、留资和人工接管流程的中小企业；暂不承诺复杂多渠道和高并发。",
        trigger_keywords: ["入门验证", "官网客服", "先试用"],
        media_refs: [],
        scope: { channels: ["web", "wechat_service"], reply_mode: "auto_with_handoff" },
        source: "demo",
        version: 1,
        status: "active",
        created_by_id: 1,
        updated_by_id: 1,
        created_at: new Date(now - 2 * 24 * 60 * 60 * 1000).toISOString(),
        updated_at: new Date(now - 2 * 60 * 60 * 1000).toISOString()
      },
      {
        id: 9102,
        tenant_id: 1,
        business_object_id: 9001,
        question: "入门验证包是否包含企业微信接入？",
        answer: "可以做官方链路的沙盒验证和配置指导；正式商用需要已备案域名、可信 IP 和客户管理员授权。",
        trigger_keywords: ["企业微信", "企微", "微信客服"],
        media_refs: [],
        scope: { channels: ["wechat_service"], reply_mode: "safe_handoff_when_missing_config" },
        source: "demo",
        version: 1,
        status: "active",
        created_by_id: 1,
        updated_by_id: 1,
        created_at: new Date(now - 28 * 60 * 60 * 1000).toISOString(),
        updated_at: new Date(now - 80 * 60 * 1000).toISOString()
      }
    ],
    9002: [
      {
        id: 9103,
        tenant_id: 1,
        business_object_id: 9002,
        question: "企业微信接入为什么需要公网 HTTPS 回调？",
        answer: "企业微信服务器需要把客户消息推送到客服系统；回调地址必须稳定可访问，并完成 URL 验证、签名校验和消息解密。",
        trigger_keywords: ["回调", "URL", "EncodingAESKey"],
        media_refs: [],
        scope: { channels: ["wechat_service"], reply_mode: "human_review_before_send" },
        source: "demo",
        version: 1,
        status: "active",
        created_by_id: 1,
        updated_by_id: 1,
        created_at: new Date(now - 26 * 60 * 60 * 1000).toISOString(),
        updated_at: new Date(now - 60 * 60 * 1000).toISOString()
      }
    ],
    9003: [
      {
        id: 9104,
        tenant_id: 1,
        business_object_id: 9003,
        question: "标准运营版和入门验证包有什么区别？",
        answer: "标准运营版增加正式知识库治理、评测集、质量复盘、告警和运营数据视图，更适合作为持续客服中台。",
        trigger_keywords: ["标准版", "区别", "升级"],
        media_refs: [],
        scope: { channels: ["all"], reply_mode: "auto_with_handoff" },
        source: "demo",
        version: 1,
        status: "active",
        created_by_id: 1,
        updated_by_id: 1,
        created_at: new Date(now - 22 * 60 * 60 * 1000).toISOString(),
        updated_at: new Date(now - 42 * 60 * 1000).toISOString()
      }
    ]
  };

  const replyDecisionTemplates = [
    {
      state: "auto_reply_ready",
      reason: "object_card_high_confidence",
      businessObjectId: 9001,
      cardId: 9101,
      confidence: 0.88,
      deliveryMode: "draft_only"
    },
    {
      state: "manual_gate_required",
      reason: "manual_review_terms",
      businessObjectId: 9002,
      cardId: 9103,
      confidence: 0.72,
      deliveryMode: "human_review"
    },
    {
      state: "knowledge_gap",
      reason: "no_business_object_match",
      businessObjectId: null,
      cardId: null,
      confidence: 0.18,
      deliveryMode: "human_review"
    },
    {
      state: "blocked_by_policy",
      reason: "blocked_policy_terms",
      businessObjectId: 9003,
      cardId: null,
      confidence: 0.12,
      deliveryMode: "blocked"
    },
    {
      state: "draft_only",
      reason: "external_write_disabled",
      businessObjectId: 9003,
      cardId: 9104,
      confidence: 0.8,
      deliveryMode: "draft_only"
    }
  ] as const;
  const replyDecisions: ReplyDecision[] = conversationInboxItems.map((item, index) => {
    const template = replyDecisionTemplates[index % replyDecisionTemplates.length];
    const businessObject = template.businessObjectId
      ? businessObjects.find((object) => object.id === template.businessObjectId) ?? null
      : null;
    const knowledgeCard =
      template.businessObjectId && template.cardId
        ? objectCardsByObject[template.businessObjectId]?.find((card) => card.id === template.cardId) ?? null
        : null;
    const review = reviewItems[index % reviewItems.length];
    const state = template.state as ReplyDecision["state"];
    const deliveryMode = template.deliveryMode as ReplyDecision["delivery_mode"];
    const draftReply =
      state === "knowledge_gap" || state === "blocked_by_policy"
        ? ""
        : knowledgeCard?.answer || review.draft_reply || "您好，当前问题已生成回复草稿，真实发送前会按渠道授权和转人工策略把关。";
    return {
      id: 19001 + index,
      tenant_id: item.tenant_id,
      conversation_id: item.id,
      message_id: review.message_id ?? 5001 + index,
      channel_id: item.channel_id,
      business_object_id: businessObject?.id ?? null,
      object_knowledge_card_id: knowledgeCard?.id ?? null,
      workflow_run_id: review.workflow_run_id,
      state,
      reason: template.reason,
      confidence: template.confidence,
      delivery_mode: deliveryMode,
      draft_reply: draftReply,
      matched_terms: knowledgeCard?.trigger_keywords.slice(0, 2) ?? [],
      decision_payload: {
        source: "demo_reply_decision",
        message_preview: item.last_message_preview,
        business_object: businessObject
          ? {
              id: businessObject.id,
              type: businessObject.type,
              title: businessObject.title,
              external_id: businessObject.external_id
            }
          : null,
        knowledge_card: knowledgeCard
          ? {
              id: knowledgeCard.id,
              question: knowledgeCard.question,
              source: knowledgeCard.source
            }
          : null,
        outbox_pre_gate:
          state === "auto_reply_ready"
            ? {
                eligible: true,
                external_write: false,
                reason: "external_write_disabled"
              }
            : null
      },
      external_write_allowed: false,
      idempotency_key: `demo-reply-decision-${item.id}`,
      created_by_id: 1,
      created_at: new Date(now - (index + 1) * 6 * 60 * 1000).toISOString()
    };
  });

  const knowledgeDocuments: KnowledgeDocument[] = Array.from({ length: 14 }, (_, index) => ({
    id: 10001 + index,
    tenant_id: 1,
    title: ["售后质保政策", "试点部署说明", "价格套餐边界", "企业微信接入步骤", "高风险话术规则"][index % 5] + ` ${index + 1}`,
    source_type: "manual_document",
    source_uri: `internal://docs/demo-${index + 1}`,
    content_hash: `demo${index + 1}abcdef1234567890`,
    tags: ["售前", "售后", "渠道", "风控"].slice(0, 1 + (index % 4)),
    status: index % 7 === 0 ? "draft" : "active",
    ingestion_status: index % 6 === 0 ? "processing" : "indexed",
    chunk_count: 3 + (index % 5),
    created_by_id: 1,
    updated_by_id: 1,
    created_at: new Date(now - (index + 1) * 36 * 60 * 1000).toISOString(),
    updated_at: new Date(now - (index + 1) * 20 * 60 * 1000).toISOString()
  }));

  const chunksByDocument: Record<number, KnowledgeChunk[]> = Object.fromEntries(
    knowledgeDocuments.map((document, index) => [
      document.id,
      [0, 1].map((chunkIndex) => ({
        id: 11001 + index * 10 + chunkIndex,
        tenant_id: 1,
        document_id: document.id,
        chunk_index: chunkIndex,
        section_title: chunkIndex === 0 ? "适用范围" : "处理边界",
        page_number: null,
        content: `${document.title} 的样例片段：用于说明知识库引用、人工审核和外发门禁。`,
        content_hash: `chunk${document.id}${chunkIndex}`,
        source_uri: document.source_uri,
        char_start: chunkIndex * 120,
        char_end: chunkIndex * 120 + 90,
        token_count: 42,
        embedding_signature: { provider: "deterministic_demo" },
        status: "active",
        citation: { source_uri: document.source_uri, chunk_index: chunkIndex },
        created_at: document.created_at
      }))
    ])
  );

  const publicationsByDocument: Record<number, KnowledgeDocumentPublication[]> = Object.fromEntries(
    knowledgeDocuments.map((document, index) => {
      const createdAt = new Date(now - (index + 1) * 22 * 60 * 1000).toISOString();
      const caseResults = [
        {
          evaluation_case_id: 13001 + index,
          status: index % 6 === 0 ? "needs_review" : "passed",
          failure_reason: index % 6 === 0 ? "expected_terms_missing" : "",
          blocking: index % 6 === 0,
          advisory: false,
          top_confidence: index % 6 === 0 ? 0.38 : 0.74,
          top_chunk_id: chunksByDocument[document.id][0]?.id ?? null,
          citation_present: index % 6 !== 0,
          expected_terms_found: index % 6 !== 0,
          matched_terms: ["人工审核", "知识库"]
        }
      ];
      const common = {
        tenant_id: 1,
        document_id: document.id,
        gap_id: index % 5 === 0 ? 16001 + (index % 5) : null,
        from_status: document.status === "active" ? "draft" : "active",
        to_status: document.status,
        evaluation_set_id: 12001,
        evaluation_run_id: 15001,
        checked_case_ids: [13001 + index],
        case_results: caseResults,
        blocking_reasons: index % 6 === 0 ? ["expected_terms_missing"] : [],
        advisory_reasons: [],
        checks: {
          target_hit_rate: index % 6 === 0 ? 0 : 1,
          target_citation_coverage: index % 6 === 0 ? 0 : 1,
          external_write_performed: false,
          model_call_performed: false
        },
        document_snapshot: {
          title: document.title,
          status: document.status === "active" ? "draft" : document.status,
          content_hash: document.content_hash,
          raw_text_hash: `demo-raw-hash-${document.id}`,
          chunk_count: document.chunk_count
        },
        external_write_performed: false,
        model_call_performed: false,
        created_by_id: 1,
        created_at: createdAt
      };
      if (document.status === "draft" && index % 7 === 0) {
        return [
          document.id,
          [
            {
              id: 17001 + index,
              ...common,
              publication_type: "rollback",
              status: "rolled_back",
              rollback_target_publication_id: 17101 + index,
              previous_publication_id: 17101 + index,
              rollback_reason: "样例：复核后回退草稿"
            }
          ]
        ] as const;
      }
      return [
        document.id,
        [
          {
            id: 17001 + index,
            ...common,
            publication_type: document.status === "active" ? "publish" : "publish_check",
            status: document.status === "active" ? "published" : index % 6 === 0 ? "blocked" : "passed",
            rollback_target_publication_id: null,
            previous_publication_id: null,
            rollback_reason: ""
          }
        ]
      ] as const;
    })
  );

  const evaluationSets: KnowledgeEvaluationSet[] = Array.from({ length: 5 }, (_, index) => ({
    id: 12001 + index,
    tenant_id: 1,
    name: `样例评测集 ${index + 1}`,
    description: "覆盖报价、售后、渠道接入和外发边界的样例题。",
    status: "active",
    evaluation_mode: "customer_service_retrieval",
    case_count: 8 + index,
    cases: Array.from({ length: 5 }, (__, caseIndex) => ({
      id: 13001 + index * 10 + caseIndex,
      tenant_id: 1,
      evaluation_set_id: 12001 + index,
      external_case_id: `demo-eval-${index + 1}-${caseIndex + 1}`,
      source_channel: ["企业微信", "官网", "小红书", "抖音", "淘宝"][caseIndex % 5],
      source_category: ["售前咨询", "售后政策", "渠道接入"][caseIndex % 3],
      question: demoQuestionForIndex(index + caseIndex),
      question_type: "demo_customer_service_question",
      expected_terms: ["人工审核", "知识库", "外发关闭"].slice(0, 1 + (caseIndex % 3)),
      expected_source_uri: "internal://docs/demo-1",
      expected_document_title: "试点部署说明",
      expected_chunk_ids: [],
      must_have_all_evidence: false,
      expected_human_review: caseIndex % 4 === 0,
      allow_auto_reply: caseIndex % 4 !== 0,
      forbidden_terms: [],
      risk_level: caseIndex % 4 === 0 ? "high" : "medium",
      annotation_notes: "样例题，不含真实客户身份。",
      required_citation: true,
      priority: (caseIndex + 1) * 10,
      status: "active",
      created_at: new Date(now - (caseIndex + 1) * 30 * 60 * 1000).toISOString()
    })),
    created_by_id: 1,
    updated_by_id: 1,
    created_at: new Date(now - (index + 1) * 50 * 60 * 1000).toISOString(),
    updated_at: new Date(now - (index + 1) * 35 * 60 * 1000).toISOString()
  }));

  const caseResults: KnowledgeEvaluationRunCase[] = Array.from({ length: 22 }, (_, index) => {
    const failed = index % 5 === 0;
    const citationSufficient = !failed && index % 4 !== 0;
    const handoffCorrect = failed ? true : index % 6 !== 0;
    return {
      id: 14001 + index,
      tenant_id: 1,
      evaluation_run_id: 15001,
      evaluation_case_id: 13001 + index,
      question: demoQuestionForIndex(index),
      status: failed ? "needs_review" : "passed",
      top_score: failed ? 0.32 : 0.71 + (index % 4) * 0.04,
      top_confidence: failed ? 0.28 : 0.64 + (index % 4) * 0.06,
      top_chunk_id: failed ? null : 11001 + index,
      top_document_id: failed ? null : knowledgeDocuments[index % knowledgeDocuments.length].id,
      citation_present: !failed,
      expected_terms_found: index % 4 !== 0,
      matched_terms: failed ? [] : ["人工审核", "知识库", "外发关闭"].slice(0, 1 + (index % 3)),
      failure_reason: failed ? "no_hit" : index % 4 === 0 ? "expected_terms_missing" : "",
      result_payload: {
        demo: true,
        answer_quality: {
          final_answer_factuality_status: "not_measured_final_answer_not_generated",
          final_answer_factuality_measured: false,
          citation_sufficient: citationSufficient,
          forbidden_commitment_passed: true,
          handoff_correct: handoffCorrect,
          gate_passed: citationSufficient && handoffCorrect,
          failure_reasons: [
            ...(!citationSufficient ? ["citation_sufficiency_failed"] : []),
            ...(!handoffCorrect ? ["handoff_prediction_mismatch"] : [])
          ],
          note: "预览数据只展示客服质量门禁结构，不生成最终答案。"
        }
      },
      created_at: new Date(now - (index + 1) * 3 * 60 * 1000).toISOString()
    };
  });
  const citationSufficientCases = caseResults.filter((item) => readRecordPayload(item.result_payload, "answer_quality")?.citation_sufficient === true).length;
  const handoffCorrectCases = caseResults.filter((item) => readRecordPayload(item.result_payload, "answer_quality")?.handoff_correct === true).length;

  const evaluationRun: KnowledgeEvaluationRun = {
    id: 15001,
    tenant_id: 1,
    evaluation_set_id: evaluationSets[0].id,
    run_mode: "demo_rehearsal",
    retrieval_mode: "bm25_vector_hybrid_shadow",
    vector_engine: "deterministic_local_hash_embedding_v1",
    total_cases: caseResults.length,
    answered_cases: caseResults.filter((item) => item.status === "passed").length,
    no_hit_cases: caseResults.filter((item) => item.failure_reason === "no_hit").length,
    passed_cases: caseResults.filter((item) => item.status === "passed").length,
    failed_cases: caseResults.filter((item) => item.status !== "passed").length,
    needs_review_cases: caseResults.filter((item) => item.status !== "passed" || item.failure_reason).length,
    citation_covered_cases: caseResults.filter((item) => item.citation_present).length,
    expected_term_covered_cases: caseResults.filter((item) => item.expected_terms_found).length,
    hit_rate: caseResults.filter((item) => item.status === "passed").length / caseResults.length,
    citation_coverage: caseResults.filter((item) => item.citation_present).length / caseResults.length,
    expected_term_coverage: caseResults.filter((item) => item.expected_terms_found).length / caseResults.length,
    average_confidence: 0.68,
    unsupported_answer_rate: null,
    summary_payload: {
      demo: true,
      note: "不评生成答案事实性",
      answer_quality_metrics_version: "p3_06u_26e_customer_service_answer_quality_v1",
      final_answer_factuality_measured: false,
      final_answer_factuality_rate: null,
      final_answer_factuality_note: "预览数据未生成最终客服答案，因此不计算完整事实准确率。",
      citation_sufficient_cases: citationSufficientCases,
      citation_sufficiency_rate: citationSufficientCases / caseResults.length,
      forbidden_commitment_violation_cases: 0,
      forbidden_commitment_violation_rate: 0,
      handoff_correct_cases: handoffCorrectCases,
      handoff_correctness: handoffCorrectCases / caseResults.length,
      answer_quality_scope: "preview_retrieval_grounded_answer_quality_gate_without_final_generation"
    },
    case_results: caseResults,
    created_by_id: 1,
    created_at: new Date(now - 18 * 60 * 1000).toISOString()
  };

  const humanReviewGaps: KnowledgeGap[] = reviewItems
    .filter((item) => item.evidence.retrieved_knowledge_count === 0 || (item.evidence.confidence ?? 0) < 0.45)
    .slice(0, 5)
    .map((item, index) => ({
      id: 16001 + index,
      tenant_id: 1,
      status: index % 3 === 0 ? "in_progress" : "open",
      severity: item.risk_level,
      source_type: "human_review",
      source_ref: `human_review_task:${item.id}`,
      source_title: `人审任务 #${item.id} · ${item.reason}`,
      source_excerpt: item.draft_reply,
      question_excerpt: item.trigger_message?.content ?? item.conversation.subject,
      gap_type: item.evidence.retrieved_knowledge_count === 0 ? "no_knowledge_hit" : "low_confidence",
      expected_terms: [],
      evidence_payload: {
        human_review_task_id: item.id,
        workflow_run_id: item.workflow_run_id,
        conversation_id: item.conversation_id,
        message_id: item.message_id,
        confidence: item.evidence.confidence,
        retrieved_knowledge_count: item.evidence.retrieved_knowledge_count,
        retrieval_mode: item.evidence.retrieval_mode
      },
      linked_knowledge_card_id: null,
      linked_knowledge_document_id: null,
      assigned_user_id: index % 3 === 0 ? 1 : null,
      created_by_id: 1,
      updated_by_id: 1,
      resolved_by_id: null,
      resolution_note: index % 3 === 0 ? "正在补充政策边界和回归题。" : "",
      created_at: item.created_at,
      updated_at: item.created_at,
      resolved_at: null
    }));
  const evaluationGaps: KnowledgeGap[] = caseResults
    .filter((item) => ["no_hit", "expected_terms_missing", "expected_evidence_missing"].includes(item.failure_reason))
    .slice(0, 5)
    .map((item, index) => ({
      id: 16101 + index,
      tenant_id: 1,
      status: index % 4 === 0 ? "triaged" : "open",
      severity: item.failure_reason === "no_hit" ? "high" : "medium",
      source_type: "evaluation_run",
      source_ref: `knowledge_evaluation_run_case:${item.id}`,
      source_title: `知识评测失败 #${item.id} · ${item.failure_reason}`,
      source_excerpt: item.failure_reason || item.status,
      question_excerpt: item.question,
      gap_type: item.failure_reason || "evaluation_failed",
      expected_terms: ["人工审核", "知识库", "引用来源"].slice(0, 1 + (index % 3)),
      evidence_payload: {
        evaluation_run_id: item.evaluation_run_id,
        evaluation_case_id: item.evaluation_case_id,
        run_case_id: item.id,
        top_confidence: item.top_confidence,
        top_score: item.top_score,
        top_chunk_id: item.top_chunk_id,
        top_document_id: item.top_document_id
      },
      linked_knowledge_card_id: null,
      linked_knowledge_document_id: null,
      assigned_user_id: null,
      created_by_id: 1,
      updated_by_id: 1,
      resolved_by_id: null,
      resolution_note: "",
      created_at: item.created_at,
      updated_at: item.created_at,
      resolved_at: null
    }));
  const knowledgeGapItems: KnowledgeGap[] = [...humanReviewGaps, ...evaluationGaps].sort(
    (left, right) => getTimeValue(right.created_at) - getTimeValue(left.created_at)
  );
  const knowledgeGaps: KnowledgeGapList = {
    items: knowledgeGapItems,
    page: 1,
    page_size: 50,
    total: knowledgeGapItems.length
  };
  const knowledgeGapSync: KnowledgeGapSyncResult = {
    created_count: knowledgeGapItems.length,
    existing_count: 0,
    scanned_count: knowledgeGapItems.length,
    items: knowledgeGapItems
  };

  const allAttempts = Object.values(attemptsByDraft).flat();
  const outboxWorkerRun: OutboxWorkerRun = {
    tenant_id: 1,
    mode: "dry_run",
    scanned: outboxDrafts.length,
    processed: allAttempts.length,
    succeeded: allAttempts.length,
    failed: 0,
    rate_limited: 0,
    rate_limited_draft_ids: [],
    skipped_draft_ids: [],
    external_write: false,
    rate_limit: { per_minute: 60 },
    attempts: allAttempts
  };
  const deliveryQueueRun: OutboxDeliveryQueueRun = {
    tenant_id: 1,
    mode: "dry_run",
    scanned: deliveryJobs.length,
    processed: deliveryJobs.length,
    succeeded: deliveryJobs.filter((job) => job.status === "pending").length,
    failed: 0,
    blocked: deliveryJobs.filter((job) => job.status === "blocked").length,
    retry_scheduled: deliveryJobs.filter((job) => job.status === "retry_scheduled").length,
    dead_lettered: 0,
    rate_limited: 0,
    rate_limited_job_ids: [],
    skipped_job_ids: [],
    external_write: false,
    kill_switch: { external_write_enabled: false },
    attempts: allAttempts,
    jobs: deliveryJobs
  };
  const inboundWorkerRun: TrustedInboundWorkerRun = {
    tenant_id: 1,
    mode: "model_assisted_demo",
    scanned: reviewItems.length,
    processed: reviewItems.length,
    succeeded: reviewItems.length,
    failed: 0,
    skipped: 0,
    rate_limited: 0,
    skipped_message_ids: [],
    rate_limited_message_ids: [],
    external_write: false,
    rate_limit: { per_minute: 60 },
    items: reviewItems.map((item) => {
      const decision = replyDecisions.find((entry) => entry.conversation_id === item.conversation_id);
      const gap = knowledgeGapItems.find((entry) => entry.evidence_payload.conversation_id === item.conversation_id);
      const draft = outboxDrafts.find((entry) => entry.conversation_id === item.conversation_id);
      return {
        message_id: item.message_id ?? 0,
        conversation_id: item.conversation_id,
        status: decision?.state === "auto_reply_ready" ? "reply_decision_ready" : "human_review_created",
        idempotency_key: `demo-inbound-${item.id}`,
        workflow_run_id: item.workflow_run_id,
        reply_decision_id: decision?.id ?? null,
        knowledge_gap_id: decision?.state === "knowledge_gap" ? gap?.id ?? null : null,
        outbox_draft_id: decision?.state === "auto_reply_ready" ? draft?.id ?? null : null,
        human_review_task_id: decision?.state === "auto_reply_ready" ? null : item.id,
        decision: decision?.state ?? "manual_gate_required",
        reason: decision?.reason ?? item.reason,
        error_message: "",
        next_action: decision ? formatDemoReplyDecisionNextAction(decision.state) : "坐席审核草稿和证据"
      };
    })
  };
  const workerHeartbeats: WorkerHeartbeat[] = [
    {
      id: 18001,
      tenant_id: 1,
      worker_type: "trusted_inbound_orchestrator",
      worker_id: "demo-trusted-inbound-worker",
      status: "idle",
      health_status: "healthy",
      last_heartbeat_at: new Date(now - 45 * 1000).toISOString(),
      last_run_record_id: 19001,
      last_run_mode: "model_assisted",
      last_error: "",
      loops_completed: 18,
      metadata_payload: {
        last_summary: {
          scanned: inboundWorkerRun.scanned,
          processed: inboundWorkerRun.processed,
          external_write: false
        }
      },
      created_at: new Date(now - 80 * 60 * 1000).toISOString(),
      updated_at: new Date(now - 45 * 1000).toISOString()
    },
    {
      id: 18002,
      tenant_id: 1,
      worker_type: "trusted_inbound_orchestrator",
      worker_id: "demo-standby-worker",
      status: "running",
      health_status: "stale",
      last_heartbeat_at: new Date(now - 6 * 60 * 1000).toISOString(),
      last_run_record_id: 19000,
      last_run_mode: "model_assisted",
      last_error: "",
      loops_completed: 5,
      metadata_payload: {
        last_summary: {
          scanned: 0,
          processed: 0,
          external_write: false
        }
      },
      created_at: new Date(now - 2 * 60 * 60 * 1000).toISOString(),
      updated_at: new Date(now - 6 * 60 * 1000).toISOString()
    }
  ];
  const recentTrustedInboundRuns: TrustedInboundWorkerRunRecord[] = [
    {
      id: 19001,
      tenant_id: 1,
      worker_id: "demo-trusted-inbound-worker",
      mode: "model_assisted",
      status: "succeeded",
      batch_size: 20,
      rate_limit_per_minute: 60,
      lease_seconds: 60,
      scanned: inboundWorkerRun.scanned,
      processed: inboundWorkerRun.processed,
      succeeded: inboundWorkerRun.succeeded,
      failed: inboundWorkerRun.failed,
      skipped: inboundWorkerRun.skipped,
      rate_limited: inboundWorkerRun.rate_limited,
      external_write: false,
      request_payload: { demo: true },
      result_payload: { external_write: false },
      error_message: "",
      created_by_id: 1,
      started_at: new Date(now - 2 * 60 * 1000).toISOString(),
      finished_at: new Date(now - 90 * 1000).toISOString()
    },
    {
      id: 19000,
      tenant_id: 1,
      worker_id: "demo-standby-worker",
      mode: "model_assisted",
      status: "succeeded",
      batch_size: 5,
      rate_limit_per_minute: 60,
      lease_seconds: 60,
      scanned: 0,
      processed: 0,
      succeeded: 0,
      failed: 0,
      skipped: 0,
      rate_limited: 0,
      external_write: false,
      request_payload: { demo: true },
      result_payload: { external_write: false },
      error_message: "",
      created_by_id: 1,
      started_at: new Date(now - 9 * 60 * 1000).toISOString(),
      finished_at: new Date(now - 9 * 60 * 1000 + 800).toISOString()
    }
  ];
  const opsRisks: OpsRisk[] = [
    {
      code: "worker_stale",
      severity: "warning",
      title: "demo-standby-worker 心跳超时",
      detail: "样例备用 worker 最近心跳超过 120 秒，用于展示排障入口。",
      next_action: "正式环境应检查 worker 容器、日志和最近运行记录。"
    }
  ];
  const opsWorkerHealth: WorkerHealthDashboard = {
    tenant_id: 1,
    generated_at: new Date(now).toISOString(),
    stale_after_seconds: 120,
    summary: {
      total_workers: workerHeartbeats.length,
      healthy_workers: workerHeartbeats.filter((item) => item.health_status === "healthy").length,
      stale_workers: workerHeartbeats.filter((item) => item.health_status === "stale").length,
      failed_workers: workerHeartbeats.filter((item) => item.health_status === "failed").length,
      running_workers: workerHeartbeats.filter((item) => item.status === "running").length,
      idle_workers: workerHeartbeats.filter((item) => item.status === "idle").length,
      external_write_enabled: false,
      trusted_inbound_worker_enabled: true,
      requires_attention: true
    },
    heartbeats: workerHeartbeats,
    recent_trusted_inbound_runs: recentTrustedInboundRuns,
    risks: opsRisks,
    external_call_performed: false,
    external_platform_write_performed: false
  };
  const demoAlertRules: OpsAlertRule[] = [
    {
      code: "trusted_inbound_processing_unavailable",
      name: "可信入站处理不可用",
      category: "worker",
      severity: "critical",
      response_type: "page",
      status: "ok",
      signal: "worker_heartbeats.summary",
      condition: "worker enabled AND healthy_workers == 0",
      threshold: "0 healthy worker",
      duration: "连续 2 个评估窗口",
      current_value: "healthy=1 total=2",
      reason: "预览环境仍有一个 healthy worker。",
      runbook: {
        summary: "恢复至少一个 healthy worker 后再扩大真实入站试点。",
        first_checks: ["查看 worker heartbeat。", "检查容器状态和最近运行记录。", "用测试租户发送可信入站 smoke。"],
        escalation: "影响真实入站处理时升级给后端负责人和交付负责人。",
        suppress_when: "计划维护窗口或未启用可信入站 worker。"
      }
    },
    {
      code: "trusted_inbound_worker_stale",
      name: "可信入站 worker 心跳超时",
      category: "worker",
      severity: "warning",
      response_type: "ticket",
      status: "firing",
      signal: "worker_heartbeats.health_status",
      condition: "health_status == stale",
      threshold: ">120s",
      duration: "连续 1 个采样窗口",
      current_value: "demo-standby-worker",
      reason: "样例备用 worker 心跳超过阈值。",
      runbook: {
        summary: "确认 worker 是否卡住、退出或网络不可达。",
        first_checks: ["查看最后心跳时间。", "检查容器日志。", "重启 worker 后观察新心跳。"],
        escalation: "重启后仍 stale 时升级给后端负责人。",
        suppress_when: "计划维护窗口内临时静默。"
      }
    },
    {
      code: "external_write_boundary_breach",
      name: "真实外发边界风险",
      category: "safety",
      severity: "critical",
      response_type: "page",
      status: "ok",
      signal: "OUTBOX_EXTERNAL_WRITE_ENABLED / worker_run.external_write",
      condition: "external write enabled OR recent run external_write == true",
      threshold: "false expected before authorization",
      duration: "立即",
      current_value: "config=disabled runs_with_write=0",
      reason: "预览环境没有真实外发配置或外部写入记录。",
      runbook: {
        summary: "核对授权和白名单，再确认是否允许真实发送。",
        first_checks: ["确认客户授权。", "确认白名单。", "未授权时关闭外发开关。"],
        escalation: "未授权开启时升级给项目负责人。",
        suppress_when: "正式白名单测试窗口内。"
      }
    },
    {
      code: "trusted_inbound_rate_limit_saturation",
      name: "可信入站限流饱和",
      category: "worker_run",
      severity: "warning",
      response_type: "ticket",
      status: "ok",
      signal: "trusted_inbound_worker_runs.rate_limited",
      condition: "3/5 recent runs rate_limited > 0 OR rate_limited >= processed",
      threshold: ">=3 recent runs or single saturated run",
      duration: "最近 5 次运行窗口",
      current_value: "rate_limited_runs=0 saturated_runs=0",
      reason: "样例运行记录没有明显限流饱和。",
      runbook: {
        summary: "确认限流来自模型、入站 worker 配置还是渠道平台。",
        first_checks: ["查看最近 5 次 run。", "确认限流配置。", "必要时降低批大小。"],
        escalation: "连续限流且影响响应时升级给运维和模型负责人。",
        suppress_when: "压测或预览环境主动降低限流阈值。"
      }
    }
  ];
  const opsAlertRules: OpsAlertRulesDashboard = {
    tenant_id: 1,
    generated_at: new Date(now).toISOString(),
    stale_after_seconds: 120,
    recent_run_limit: 10,
    notification_channel_enabled: false,
    notification_sent: false,
    firing_count: demoAlertRules.filter((rule) => rule.status === "firing").length,
    page_count: demoAlertRules.filter((rule) => rule.status === "firing" && rule.response_type === "page").length,
    ticket_count: demoAlertRules.filter((rule) => rule.status === "firing" && rule.response_type === "ticket").length,
    rules: demoAlertRules,
    external_call_performed: false,
    external_platform_write_performed: false
  };
  const demoOpsMetrics: OpsMetric[] = [
    {
      name: "wanfa_worker_total",
      metric_type: "gauge",
      value: workerHeartbeats.length,
      unit: "workers",
      labels: { tenant_id: "1" },
      description: "Total registered worker heartbeat rows for the tenant.",
      source: "worker_heartbeats",
      status: "ok"
    },
    {
      name: "wanfa_worker_stale",
      metric_type: "gauge",
      value: 1,
      unit: "workers",
      labels: { tenant_id: "1" },
      description: "Workers whose heartbeat exceeded the stale threshold.",
      source: "worker_heartbeats.health_status",
      status: "warning"
    },
    {
      name: "wanfa_ops_alert_rules_firing",
      metric_type: "gauge",
      value: opsAlertRules.firing_count,
      unit: "rules",
      labels: { tenant_id: "1" },
      description: "Currently firing operations alert rules.",
      source: "ops.alert_rules",
      status: "warning"
    },
    {
      name: "wanfa_queue_backlog_total",
      metric_type: "gauge",
      value: deliveryJobs.filter((job) => ["queued", "retry_scheduled", "locked"].includes(job.status)).length,
      unit: "jobs",
      labels: { tenant_id: "1" },
      description: "Total queued, retry-scheduled, or locked jobs across outbound and trusted inbound queues.",
      source: "回复链路任务 + 入站消息任务",
      status: "warning"
    },
    {
      name: "回复链路任务",
      metric_type: "gauge",
      value: deliveryJobs.filter((job) => job.status === "queued").length,
      unit: "jobs",
      labels: { tenant_id: "1", status: "queued" },
      description: "Outbound delivery job count by bounded status label.",
      source: "回复链路任务状态",
      status: "warning"
    },
    {
      name: "异常回复链路任务",
      metric_type: "gauge",
      value: 0,
      unit: "jobs",
      labels: { tenant_id: "1" },
      description: "Outbound delivery jobs that reached dead-letter state.",
      source: "回复链路任务状态",
      status: "ok"
    },
    {
      name: "wanfa_delivery_failure_reviews_open",
      metric_type: "gauge",
      value: failureReviews.filter((item) => item.status === "open").length,
      unit: "reviews",
      labels: { tenant_id: "1" },
      description: "Open delivery failure reviews requiring human action.",
      source: "delivery_failure_reviews.status",
      status: "warning"
    },
    {
      name: "wanfa_external_write_enabled",
      metric_type: "gauge",
      value: 0,
      unit: "boolean",
      labels: { tenant_id: "1" },
      description: "Whether the global external platform write switch is enabled.",
      source: "OUTBOX_EXTERNAL_WRITE_ENABLED",
      status: "ok"
    }
  ];
  const opsMetrics: OpsMetricsDashboard = {
    tenant_id: 1,
    generated_at: new Date(now).toISOString(),
    stale_after_seconds: 120,
    recent_run_limit: 10,
    collection_model: "pull_json_or_prometheus_text_preview",
    scrape_path: "/api/tenants/1/ops/metrics",
    summary: {
      total_metrics: demoOpsMetrics.length,
      firing_alerts: opsAlertRules.firing_count,
      page_alerts: opsAlertRules.page_count,
      queue_backlog: deliveryJobs.filter((job) => ["queued", "retry_scheduled", "locked"].includes(job.status)).length,
      dead_letter_jobs: 0,
      failed_worker_runs: recentTrustedInboundRuns.filter((run) => run.status === "failed" || run.failed > 0).length,
      open_failure_reviews: failureReviews.filter((item) => item.status === "open").length,
      external_write_enabled: false,
      ready_for_prometheus_scrape: true
    },
    metrics: demoOpsMetrics,
    prometheus_text: [
      "# HELP wanfa_worker_stale Workers whose heartbeat exceeded the stale threshold.",
      "# TYPE wanfa_worker_stale gauge",
      'wanfa_worker_stale{tenant_id="1"} 1',
      "# HELP wanfa_ops_alert_rules_firing Currently firing operations alert rules.",
      "# TYPE wanfa_ops_alert_rules_firing gauge",
      `wanfa_ops_alert_rules_firing{tenant_id="1"} ${opsAlertRules.firing_count}`,
      "# HELP wanfa_queue_backlog_total Total queued, retry-scheduled, or locked jobs across outbound and trusted inbound queues.",
      "# TYPE wanfa_queue_backlog_total gauge",
      `wanfa_queue_backlog_total{tenant_id="1"} ${deliveryJobs.filter((job) => ["queued", "retry_scheduled", "locked"].includes(job.status)).length}`,
      "# HELP wanfa_external_write_enabled Whether the global external platform write switch is enabled.",
      "# TYPE wanfa_external_write_enabled gauge",
      'wanfa_external_write_enabled{tenant_id="1"} 0'
    ].join("\n"),
    external_call_performed: false,
    external_platform_write_performed: false
  };
  const onlineReceiptQuality: OnlineReceiptQualitySummary = {
    tenant_id: 1,
    schema_version: "p3-06u-26h2w3d.online_receipt_quality.v1",
    generated_at: new Date(now).toISOString(),
    receipt_total: 8,
    matched_receipts: 6,
    verified_receipts: 0,
    delivered_or_read: 6,
    failed_or_review: failureReviews.filter((item) => item.status === "open").length,
    unknown_receipts: 0,
    open_failure_reviews: failureReviews.filter((item) => item.status === "open").length,
    receipt_match_rate: 0.75,
    verified_receipt_rate: 0,
    delivery_success_rate: 0.75,
    failure_review_rate: 0.25,
    status_by_normalized_status: {
      delivered: 6,
      rate_limited: 1,
      permission_denied: 1
    },
    provider_breakdown: [
      {
        provider: "wecom",
        receipt_count: 3,
        matched_receipts: 2,
        verified_receipts: 0,
        delivered_or_read: 2,
        needs_review: 1,
        unknown_receipts: 0,
        delivery_success_rate: 0.6667
      },
      {
        provider: "douyin",
        receipt_count: 3,
        matched_receipts: 2,
        verified_receipts: 0,
        delivered_or_read: 2,
        needs_review: 1,
        unknown_receipts: 0,
        delivery_success_rate: 0.6667
      },
      {
        provider: "xiaohongshu",
        receipt_count: 2,
        matched_receipts: 2,
        verified_receipts: 0,
        delivered_or_read: 2,
        needs_review: 0,
        unknown_receipts: 0,
        delivery_success_rate: 1
      }
    ],
    quality_gates: [
      {
        key: "receipt_ingestion",
        label: "回执入库",
        status: "ok",
        detail: "本地样本已生成 8 条回执口径。",
        stop_condition: "没有任何回执入库时，不能声称已具备线上链路观测。"
      },
      {
        key: "attempt_match",
        label: "回执匹配",
        status: "warning",
        detail: "6/8 条回执已匹配到发送尝试。",
        stop_condition: "真实平台回执不能稳定匹配发送记录前，不进入真实外发验收。"
      },
      {
        key: "signature_verification",
        label: "签名验证",
        status: "missing",
        detail: "本地样本没有官方签名验证。",
        stop_condition: "未完成官方回调签名或 AES 验证时，只能作为内部样本回执。"
      },
      {
        key: "failure_review",
        label: "失败复盘",
        status: failureReviews.some((item) => item.status === "open") ? "warning" : "ok",
        detail: `${failureReviews.filter((item) => item.status === "open").length} 条失败复盘仍打开。`,
        stop_condition: "失败回执不能进入复盘、重试或人工处理时，闭环不通过。"
      },
      {
        key: "customer_accuracy",
        label: "完整客服准确率",
        status: "missing",
        detail: "本地样本只展示回执链路覆盖，不展示完整客服答案准确率。",
        stop_condition: "缺少真实题库、最终回复样本、人工事实性标签和真实平台回执时，不展示完整线上准确率。"
      }
    ],
    accuracy_scope_label: "线上回执链路覆盖率，不是完整客服答案准确率",
    accuracy_boundary: "当前只统计本地归一回执、失败复盘和匹配情况；真实外发继续关闭，完整准确率需要官方授权渠道、真实回执、最终答案样本和人工事实性标签。",
    raw_payload_included: false,
    customer_accuracy_completed: false,
    real_platform_receipts_required_for_full_accuracy: true,
    model_call_performed: false,
    external_call_performed: false,
    external_platform_write_performed: false,
    real_external_write_performed: false
  };
  const reportPeriod = new Date(now).toISOString().slice(0, 7);
  const customerQualityReport: CustomerQualityReport = {
    tenant_id: 1,
    schema_version: "p3-06u-26h2q.customer_quality_report.v1",
    report_title: `${reportPeriod} 客服质量复盘报告`,
    period: reportPeriod,
    period_start: `${reportPeriod}-01`,
    period_end: `${reportPeriod}-28`,
    generated_at: new Date(now).toISOString(),
    report_status: "human_label_required",
    report_status_label: "需补人工标签",
    report_confidence_score: 62,
    quality_conclusion: "本地样本已具备题库、回执和知识缺口的复盘口径，但仍缺真实客户题库、最终回复事实性标签和官方渠道回执。",
    executive_summary: [
      "当前只展示受控试点质量结构，不代表完整线上客服准确率。",
      "知识缺口已能回到知识库运营和自动回复策略。",
      "报告导出和客户确认只做本地归档，不是正式电子签章。"
    ],
    headline_metrics: [
      { key: "sample", label: "样本题", value: `${evaluationRun.total_cases}`, status: "warning", detail: "预览题集，还不是客户真实题库" },
      { key: "hit", label: "引用覆盖", value: formatPercent(evaluationRun.citation_coverage), status: "ok", detail: "按本地评测样本计算" },
      { key: "receipt", label: "回执覆盖", value: formatPercent(onlineReceiptQuality.receipt_match_rate), status: "warning", detail: "本地回执样本，不是官方线上回执" },
      { key: "signoff", label: "确认状态", value: "待确认", status: "missing", detail: "客户确认记录需负责人填写" }
    ],
    sections: [
      {
        key: "knowledge",
        title: "知识命中",
        status: "warning",
        summary: "知识引用覆盖已形成基础，但低置信和无知识样本仍需补业务对象与标准问答。",
        evidence: "来自知识评测、人工审核样本和知识缺口池。",
        next_steps: ["补充业务对象知识", "用同一题集回归验证"]
      },
      {
        key: "handoff",
        title: "转人工边界",
        status: "warning",
        summary: "高风险、低置信和无法确认的问题应进入人工处理。",
        evidence: "策略样本中包含投诉、赔付和外发边界。",
        next_steps: ["调整自动回复处理方式", "补禁用承诺规则"]
      },
      {
        key: "receipt",
        title: "线上回执",
        status: "missing",
        summary: "当前只有本地回执样本，尚未接入正式官方渠道回执。",
        evidence: "真实外发继续关闭。",
        next_steps: ["完成官方授权", "建立回执匹配和失败复盘"]
      },
      {
        key: "archive",
        title: "报告归档",
        status: "ok",
        summary: "报告可导出为 HTML、XLSX、DOCX 并写入本地审计归档。",
        evidence: "归档文件不包含原始客户问题、完整回复或人工备注明文。",
        next_steps: ["客户确认后记录本地确认结果", "需要法律效力时另接电子签服务"]
      }
    ],
    action_plan: [
      {
        key: "labels",
        label: "补人工事实性标签",
        owner: "运营负责人",
        priority: "P0",
        status: "open",
        evidence: "最终回复事实性样本不足",
        next_step: "导入 50-100 条真实脱敏客户题库并标注"
      },
      {
        key: "knowledge",
        label: "修复高频知识缺口",
        owner: "知识运营",
        priority: "P1",
        status: "in_progress",
        evidence: "低置信和无知识样本仍存在",
        next_step: "补业务对象、标准问答和流程政策"
      }
    ],
    signoff_checklist: [
      "报告已脱敏，不展示原始客户问题。",
      "完整线上准确率仍需真实题库、最终回复、人工事实性标签和官方渠道回执。",
      "本地确认记录不是正式电子签章。"
    ],
    data_boundaries: [
      "不包含原始客户问题、完整回复、人工备注或渠道密钥。",
      "本地样本只能用于界面预览和流程校验。"
    ],
    source_monthly_review_schema_version: "p3-06u-26h2m.monthly_quality_review.v1",
    latest_evaluation_run_id: evaluationRun.id,
    latest_evaluation_set_id: evaluationSets[0].id,
    raw_text_included: false,
    model_call_performed: false,
    external_call_performed: false,
    external_platform_write_performed: false
  };
  const customerQualityReportArchives: CustomerQualityReportArchiveList = {
    tenant_id: 1,
    schema_version: "p3-06u-26h2w4.customer_quality_report_archive_list.v1",
    page: 1,
    page_size: 8,
    total: 3,
    items: ["html", "xlsx", "docx"].map((format, index) => ({
      audit_event_id: 18001 + index,
      tenant_id: 1,
      schema_version: "p3-06u-26h2w4.customer_quality_report_archive_list.v1",
      report_schema_version: customerQualityReport.schema_version,
      export_schema_version: "p3-06u-26h2s.customer_quality_report_export.v1",
      export_format: format,
      filename: `wanfa-customer-quality-report-demo-${reportPeriod}.${format}`,
      content_type:
        format === "xlsx"
          ? "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
          : format === "docx"
            ? "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            : "text/html; charset=utf-8",
      body_encoding: format === "html" ? "utf-8" : "base64",
      body_sha256: `demo-${format}-sha256`,
      body_bytes: format === "html" ? 8192 : format === "xlsx" ? 12288 : 15360,
      period: reportPeriod,
      generated_at: new Date(now - index * 18 * 60 * 1000).toISOString(),
      report_status: customerQualityReport.report_status,
      report_status_label: customerQualityReport.report_status_label,
      signoff_status: "pending_customer_confirmation",
      body_archived: true,
      download_supported: false,
      raw_text_included: false,
      final_answer_text_included: false,
      reviewer_notes_included: false,
      electronic_signature_performed: false,
      formal_contract_signoff_performed: false,
      model_call_performed: false,
      external_call_performed: false,
      external_platform_write_performed: false
    })),
    raw_text_included: false,
    final_answer_text_included: false,
    reviewer_notes_included: false,
    electronic_signature_performed: false,
    formal_contract_signoff_performed: false,
    model_call_performed: false,
    external_call_performed: false,
    external_platform_write_performed: false
  };
  const customerQualityReportSignoffs: CustomerQualityReportSignoffList = {
    tenant_id: 1,
    schema_version: "p3-06u-26h2u.customer_quality_report_signoff_list.v1",
    page: 1,
    page_size: 8,
    total: 1,
    items: [
      {
        audit_event_id: 18101,
        tenant_id: 1,
        schema_version: "p3-06u-26h2u.customer_quality_report_signoff_list.v1",
        report_schema_version: customerQualityReport.schema_version,
        export_schema_version: "p3-06u-26h2s.customer_quality_report_export.v1",
        period: reportPeriod,
        report_status: customerQualityReport.report_status,
        report_status_label: customerQualityReport.report_status_label,
        report_confidence_score: customerQualityReport.report_confidence_score,
        signoff_status: "accepted_with_notes",
        signoff_status_label: "确认通过，有备注",
        signer_display_name: "李**",
        signer_role: "运营负责人",
        signer_organization: "本地样本企业",
        confirmation_method: "meeting_confirmation",
        confirmation_method_label: "会议确认",
        notes_recorded: true,
        notes_hash: "demo-notes-hash",
        notes_length: 18,
        recorded_at: new Date(now - 45 * 60 * 1000).toISOString(),
        recorded_by_user_id: 1,
        audit_action: "customer_quality_report.signoff_recorded",
        audit_resource_id: reportPeriod,
        raw_text_included: false,
        final_answer_text_included: false,
        reviewer_notes_included: false,
        signer_name_raw_included: false,
        electronic_signature_performed: false,
        formal_contract_signoff_performed: false,
        model_call_performed: false,
        external_call_performed: false,
        external_platform_write_performed: false
      }
    ],
    raw_text_included: false,
    final_answer_text_included: false,
    reviewer_notes_included: false,
    signer_name_raw_included: false,
    model_call_performed: false,
    external_call_performed: false,
    external_platform_write_performed: false
  };

  return {
    reviewItems,
    conversationInbox: {
      items: conversationInboxItems,
      page: 1,
      page_size: 8,
      total: conversationInboxItems.length
    },
    supportTickets: {
      items: supportTicketItems,
      page: 1,
      page_size: 8,
      total: supportTicketItems.length
    },
    contactProfiles: {
      items: contactProfileItems,
      page: 1,
      page_size: 8,
      total: contactProfileItems.length
    },
    contactProfileDetail,
    salesLeads: {
      items: salesLeadItems,
      page: 1,
      page_size: 8,
      total: salesLeadItems.length
    },
    outboxDrafts,
    attemptsByDraft,
    failureReviews,
    deliveryJobs,
    businessObjects,
    objectCardsByObject,
    knowledgeDocuments,
    chunksByDocument,
    publicationsByDocument,
    searchResult: {
      query: "试点部署怎么保证不乱回复",
      retrieval_mode: "bm25_vector_hybrid_shadow",
      vector_engine: "deterministic_local_hash_embedding_v1",
      vector_store: "local_demo",
      retrieval_backend: "demo_index",
      vector_index_status: "shadow",
      embedding_provider: "deterministic",
      embedding_model: "local_hash",
      reranker: "lexical_overlap_reranker_v1",
      total_candidates: 5,
      matches: knowledgeDocuments.slice(0, 5).map((document, index) => ({
        chunk_id: chunksByDocument[document.id][0].id,
        document_id: document.id,
        document_title: document.title,
        chunk_index: 0,
        section_title: "适用范围",
        source_type: document.source_type,
        source_uri: document.source_uri,
        content_preview: `${document.title}：样例检索结果，正式环境需要客户知识库和回归题集验证。`,
        score: 0.88 - index * 0.07,
        confidence: 0.82 - index * 0.06,
        bm25_score: 0.75 - index * 0.05,
        vector_score: 0.61 - index * 0.04,
        reranker_score: 0.7 - index * 0.04,
        matched_terms: ["试点", "人工审核", "知识库"].slice(0, 1 + (index % 3)),
        citation: { source_uri: document.source_uri, chunk_index: 0 }
      }))
    } satisfies KnowledgeDocumentSearchResponse,
    evaluationSets,
    evaluationRun,
    runsBySet: Object.fromEntries(evaluationSets.map((item) => [item.id, [toKnowledgeEvaluationRunSummary(evaluationRun)]])),
    knowledgeGaps,
    knowledgeGapSync,
    customerQualityReport,
    customerQualityReportArchives,
    customerQualityReportSignoffs,
    replyDecisions,
    channelIdentities,
    outboxWorkerRun,
    deliveryQueueRun,
    inboundWorkerRun,
    onlineReceiptQuality,
    opsWorkerHealth,
    opsAlertRules,
    opsMetrics
  };
}

function formatDemoReplyDecisionNextAction(value: ReplyDecision["state"]) {
  const labels: Record<ReplyDecision["state"], string> = {
    auto_reply_ready: "AI 已生成可回复建议",
    manual_gate_required: "坐席审核草稿和证据",
    knowledge_gap: "补业务对象知识",
    blocked_by_policy: "策略复核",
    draft_only: "仅生成草稿"
  };
  return labels[value];
}

function demoQuestionForIndex(index: number) {
  const questions = [
    "你们这个智能客服能不能直接接企业微信自动回复？",
    "如果客户问退款赔付，AI 会不会自己承诺？",
    "试点版多久可以上线，需要准备哪些资料？",
    "知识库更新后怎么判断准确率有没有下降？",
    "报价和套餐边界能不能让 AI 自动解释？",
    "客户问合同、发票、隐私合规时怎么处理？",
    "如果渠道接口限流或者失败，中台怎么提醒？",
    "官网客服和企业微信客服的数据能不能统一审核？"
  ];
  return questions[index % questions.length];
}

function readRecordString(record: Record<string, unknown>, key: string) {
  const value = record[key];
  if (typeof value === "string") {
    return value;
  }
  if (typeof value === "number" || typeof value === "boolean") {
    return String(value);
  }
  return "";
}

function formatModelCallLabel(modelCall: Record<string, unknown> | null) {
  if (!modelCall) {
    return "未调用模型";
  }
  const provider = readRecordString(modelCall, "provider") || "provider";
  const status = readRecordString(modelCall, "status") || "unknown";
  return `${provider} · ${status}`;
}

function formatModelCallDetail(modelCall: Record<string, unknown> | null) {
  if (!modelCall) {
    return "未记录模型调用";
  }
  const provider = readRecordString(modelCall, "provider") || "provider";
  const model = readRecordString(modelCall, "model") || "model";
  const routeName = readRecordString(modelCall, "route_name");
  const status = readRecordString(modelCall, "status") || "unknown";
  return [provider, model, routeName, status].filter(Boolean).join(" / ");
}

function formatOutboxStatus(
  draft: OutboxDraft | undefined,
  job: OutboxDeliveryJob | undefined,
  failure: DeliveryFailureReview | undefined
) {
  if (!draft) {
    return "尚未生成待发送草稿";
  }
  const parts = [`草稿 #${draft.id}`, draft.status, draft.delivery_status];
  if (job) {
    parts.push(`队列 #${job.id} ${job.status}`);
  }
  if (failure) {
    parts.push(`失败复盘 #${failure.id} ${failure.normalized_status}`);
  }
  return parts.join(" / ");
}

function LoginScreen({
  loading,
  error,
  onLogin,
  onLocalPreviewLogin,
  onCreateLocalOwner,
  setupStatus
}: {
  loading: boolean;
  error?: string;
  onLogin: (payload: LoginRequest) => void;
  onLocalPreviewLogin: () => void;
  onCreateLocalOwner: (payload: LocalOwnerSetupRequest) => void;
  setupStatus: LocalSetupStatus | null;
}) {
  const [tenantName, setTenantName] = useState("本地客服工作台");
  const [tenantSlug, setTenantSlug] = useState("wanfa-local");
  const [ownerName, setOwnerName] = useState("负责人");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const canCreateFirstOwner = setupStatus?.can_create_first_owner ?? true;
  const isInitialized = setupStatus?.initialized ?? false;
  const canUseLocalPreview = Boolean(setupStatus?.dev_bootstrap_enabled && !canCreateFirstOwner);
  const readinessItems = setupStatus
    ? [
        {
          key: "external-write",
          label: setupStatus.external_write_enabled ? "真实外发未关闭" : "真实外发已关闭",
          state: setupStatus.external_write_enabled ? "blocked" : "ready"
        },
        {
          key: "dev-bootstrap",
          label: setupStatus.dev_bootstrap_enabled ? "开发入口仍开启" : "开发入口已关闭",
          state: setupStatus.dev_bootstrap_enabled ? "blocked" : "ready"
        },
        {
          key: "owner-lock",
          label: setupStatus.first_owner_creation_locked ? "首任负责人入口已锁定" : "可创建首任负责人",
          state: "ready"
        },
        {
          key: "password-reset",
          label: setupStatus.web_password_reset_enabled ? "网页端允许重置密码" : "无身份重置已关闭",
          state: setupStatus.web_password_reset_enabled ? "blocked" : "ready"
        }
      ]
    : [];

  useEffect(() => {
    if (!setupStatus?.initialized) {
      return;
    }
    if (setupStatus.first_tenant_slug) {
      setTenantSlug(setupStatus.first_tenant_slug);
    }
    if (setupStatus.first_tenant_name) {
      setTenantName(setupStatus.first_tenant_name);
    }
  }, [setupStatus?.initialized, setupStatus?.first_tenant_slug, setupStatus?.first_tenant_name]);

  return (
    <main className="login-page">
      <section className="login-shell" aria-label="标准运营版登录">
        <div className="login-brand">
          <div className="brand-mark">万</div>
          <div>
            <strong>万法常世</strong>
            <span>客服中台 标准运营版</span>
          </div>
        </div>
        <form
          className="login-panel"
          data-role-smoke="login-form"
          onSubmit={(event) => {
            event.preventDefault();
            if (canCreateFirstOwner) {
              onCreateLocalOwner({
                tenant_name: tenantName.trim() || "本地客服工作台",
                tenant_slug: tenantSlug.trim(),
                owner_name: ownerName.trim() || "负责人",
                email: email.trim(),
                password
              });
            } else {
              onLogin({
                tenant_slug: tenantSlug.trim(),
                email: email.trim(),
                password
              });
            }
          }}
        >
          <div className="login-heading">
            <h1>登录工作台</h1>
            <p>
              {isInitialized
                ? "本地工作台已经完成初始化，请使用已有账号登录。"
                : "第一次本地部署时，先创建第一个负责人账号。"}
            </p>
          </div>

          {setupStatus ? (
            <div
              className={`local-setup-status ${setupStatus.local_deployment_ready ? "is-ready" : "is-blocked"}`}
              data-local-setup-status="p3-06u-26h2w8a"
            >
              <strong>{canCreateFirstOwner ? "本地工作台尚未初始化" : "本地工作台已初始化"}</strong>
              <span>
                租户 {setupStatus.tenant_count} 个 · 账号 {setupStatus.user_count} 个
                {canCreateFirstOwner ? " · 可以创建第一个负责人" : " · 请使用已有账号登录"}
              </span>
              <div className="local-setup-checks" aria-label="本地部署安全检查">
                {readinessItems.map((item) => (
                  <span className={`local-setup-chip is-${item.state}`} key={item.key}>
                    {item.label}
                  </span>
                ))}
              </div>
              {setupStatus.blockers.length ? (
                <span>当前环境仍有 {setupStatus.blockers.length} 项安全门禁未关闭，仅适合本机研发验证。</span>
              ) : null}
            </div>
          ) : null}

          <label className="field">
            <span>租户标识</span>
            <input
              autoComplete="organization"
              name="tenant_slug"
              data-role-smoke="tenant-slug"
              value={tenantSlug}
              onChange={(event) => setTenantSlug(event.target.value)}
              placeholder="tenant-slug"
              required
            />
          </label>

          {canCreateFirstOwner ? (
            <>
              <label className="field">
                <span>租户名称</span>
                <input
                  autoComplete="organization-title"
                  name="tenant_name"
                  data-role-smoke="tenant-name"
                  value={tenantName}
                  onChange={(event) => setTenantName(event.target.value)}
                  placeholder="本地客服工作台"
                />
              </label>

              <label className="field">
                <span>负责人姓名</span>
                <input
                  autoComplete="name"
                  name="owner_name"
                  data-role-smoke="owner-name"
                  value={ownerName}
                  onChange={(event) => setOwnerName(event.target.value)}
                  placeholder="负责人"
                />
              </label>
            </>
          ) : null}

          <label className="field">
            <span>邮箱</span>
            <input
              autoComplete="email"
              name="email"
              data-role-smoke="email"
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder="name@example.com"
              required
            />
          </label>

          <label className="field">
            <span>密码</span>
            <input
              autoComplete="current-password"
              name="password"
              data-role-smoke="password"
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder={canCreateFirstOwner ? "设置至少 8 位密码" : "输入密码"}
              required
            />
          </label>

          {error ? <p className="login-error">{error}</p> : null}

          <div className="login-actions">
            <button
              type="submit"
              className="primary-action"
              data-role-smoke={canCreateFirstOwner ? "local-owner-setup" : "login-submit"}
              disabled={loading || (canCreateFirstOwner && password.length < 8)}
            >
              <LogIn size={17} />
              {loading ? (canCreateFirstOwner ? "创建中" : "登录中") : canCreateFirstOwner ? "创建负责人并进入" : "登录"}
            </button>
            {canUseLocalPreview ? (
              <button
                type="button"
                className="ghost-action"
                data-role-smoke="local-preview-login"
                disabled={loading}
                onClick={onLocalPreviewLogin}
              >
                进入本地预览
              </button>
            ) : null}
          </div>
          <p className="login-footnote">
            {canCreateFirstOwner
              ? "知识库、会话记录和渠道配置都绑定到这个本地租户；密码由你在这里首次设置，系统不会预置默认密码。"
              : "如果忘记负责人密码，需要在本机执行密码重置脚本；网页端不会提供无身份重置入口。"}
          </p>
        </form>
      </section>
    </main>
  );
}

function ConnectionCard({ connection }: { connection: ConnectionState }) {
  const isReady = connection.status === "ready";
  const icon = isReady ? <CheckCircle2 size={18} /> : <AlertTriangle size={18} />;
  const title = isReady
    ? connection.mode === "demo" ? "本地工作台" : "后端已连接"
    : connection.status === "loading" ? "正在检查后端" : "后端连接异常";
  const user = connection.user;

  return (
    <section
      className={`connection-card ${isReady ? "is-ready" : "is-warning"}`}
      aria-live="polite"
    >
      <div className="connection-title">
        {icon}
        <strong>{title}</strong>
      </div>
      {user ? (
        <div className="connection-meta">
          <span>{user.tenant.name}</span>
          <small>{user.name} · {user.roles.join(" / ")}</small>
        </div>
      ) : (
        <div className="connection-meta">
          <span>等待身份接口</span>
          <small>{connection.error ?? "正在读取当前工作空间"}</small>
        </div>
      )}
    </section>
  );
}
