import { Activity, BarChart3, BookOpen, Download, Route, Search, Send, ShieldCheck } from "lucide-react";
import type { FormEvent } from "react";

import type {
  ConversationInboxList,
  DeliveryFailureReview,
  HumanReviewInboxItem,
  CustomerQualityReport,
  CustomerQualityReportArchiveList,
  CustomerQualityReportSignoffCreate,
  CustomerQualityReportSignoffList,
  KnowledgeEvaluationRun,
  KnowledgeEvaluationRunSummary,
  KnowledgeEvaluationSet,
  KnowledgeGap,
  KnowledgeGapList,
  KnowledgeGapSyncResult,
  MonthlyQualityReview,
  MonthlyOpsReport,
  OnlineReceiptQualitySummary,
  OutboxDeliveryJob,
  OutboxDraft
} from "../../api/client";
import { DataSourceBadge, PREVIEW_DATA_LABEL, REAL_DATA_LABEL, WorkspaceStateNotice } from "../common/WorkspaceState";

type ConversationInboxState =
  | { status: "idle"; message: string; data: ConversationInboxList }
  | { status: "loading"; data: ConversationInboxList }
  | { status: "ready"; data: ConversationInboxList }
  | { status: "error"; message: string; data: ConversationInboxList };

interface KnowledgeEvaluationState {
  status: "idle" | "loading" | "ready" | "error";
  message: string;
  sets: KnowledgeEvaluationSet[];
  lastRun: KnowledgeEvaluationRun | null;
  runsBySet: Record<number, KnowledgeEvaluationRunSummary[]>;
}

interface KnowledgeGapState {
  status: "idle" | "loading" | "ready" | "error";
  message: string;
  data: KnowledgeGapList;
  lastSync: KnowledgeGapSyncResult | null;
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

interface OnlineReceiptQualityState {
  status: "idle" | "loading" | "ready" | "error";
  message: string;
  data: OnlineReceiptQualitySummary | null;
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

type WorkspaceTaskSource = "overview" | "quality" | "knowledge";

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
  | "settings";

interface QualityIssueBreakdown {
  key: string;
  label: string;
  count: number;
  detail: string;
  action: string;
  href: string;
  tone: "urgent" | "warning" | "normal" | "success";
}

interface QualityFunnelStep {
  label: string;
  count: number;
  note: string;
  href: string;
}

interface QualityDrillSample {
  id: string;
  source: string;
  title: string;
  excerpt: string;
  cause: string;
  action: string;
  href: string;
  tone: "urgent" | "warning" | "normal";
}

interface QualityRepairPath {
  key: string;
  label: string;
  source: string;
  evidence: string;
  owner: string;
  next: string;
  href: string;
  count: number;
  progress: number;
  tone: "urgent" | "warning" | "normal" | "success";
}

function getWorkspaceSectionHash(section: WorkspaceSection) {
  return `#${section}`;
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

function getTimeValue(value: string | null) {
  if (!value) {
    return 0;
  }
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? 0 : date.getTime();
}

function formatPercent(value: number | null) {
  if (value === null || Number.isNaN(value)) {
    return "-";
  }
  return `${Math.round(value * 100)}%`;
}

function formatRate(count: number, total: number) {
  if (total <= 0) {
    return "-";
  }
  return `${Math.round((count / total) * 100)}%`;
}

function formatFileSize(bytes: number) {
  if (!Number.isFinite(bytes) || bytes <= 0) {
    return "大小未知";
  }
  if (bytes < 1024) {
    return `${bytes} B`;
  }
  if (bytes < 1024 * 1024) {
    return `${(bytes / 1024).toFixed(1)} KB`;
  }
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function formatReportExportFormat(value: string) {
  const labels: Record<string, string> = {
    html: "HTML 留档",
    xlsx: "XLSX 明细",
    docx: "DOCX 报告"
  };
  return labels[value] ?? value.toUpperCase();
}

function getRecordNumber(source: Record<string, unknown>, key: string): number | null {
  const value = source[key];
  return typeof value === "number" && Number.isFinite(value) ? value : null;
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

function formatReviewSignalStatus(value: string) {
  const labels: Record<string, string> = {
    ok: "正常",
    warning: "需关注",
    critical: "优先处理",
    missing: "待补齐",
    open: "待处理",
    in_progress: "处理中",
    done: "已完成"
  };
  return labels[value] ?? value;
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

export function QualityMetric({ label, value, note }: { label: string; value: string; note: string }) {
  return (
    <div className="quality-metric">
      <span>{label}</span>
      <strong>{value}</strong>
      <small>{note}</small>
    </div>
  );
}

export function QualityReviewPanel({
  conversationInbox,
  reviewItems,
  outboxDrafts,
  failureReviews,
  deliveryJobs,
  knowledgeEvaluation,
  monthlyQualityReview,
  monthlyOpsReport,
  onlineReceiptQuality,
  customerQualityReport,
  customerQualityReportArchives,
  customerQualityReportSignoffs,
  knowledgeGaps,
  onExportCustomerQualityReport,
  onDownloadCustomerQualityReportArchive,
  onRecordCustomerQualityReportSignoff,
  canRecordCustomerQualityReportSignoff = false
}: {
  conversationInbox: ConversationInboxState;
  reviewItems: HumanReviewInboxItem[];
  outboxDrafts: OutboxDraft[];
  failureReviews: DeliveryFailureReview[];
  deliveryJobs: OutboxDeliveryJob[];
  knowledgeEvaluation: KnowledgeEvaluationState;
  monthlyQualityReview: MonthlyQualityReviewState;
  monthlyOpsReport: MonthlyOpsReportState;
  onlineReceiptQuality: OnlineReceiptQualityState;
  customerQualityReport: CustomerQualityReportState;
  customerQualityReportArchives: CustomerQualityReportArchiveState;
  customerQualityReportSignoffs: CustomerQualityReportSignoffState;
  knowledgeGaps: KnowledgeGapState;
  onExportCustomerQualityReport?: (format: "html" | "xlsx" | "docx") => void;
  onDownloadCustomerQualityReportArchive?: (archiveEventId: number) => void;
  onRecordCustomerQualityReportSignoff?: (payload: CustomerQualityReportSignoffCreate) => void;
  canRecordCustomerQualityReportSignoff?: boolean;
}) {
  const conversations = conversationInbox.data.items;
  const totalConversations = Math.max(conversationInbox.data.total, conversations.length, reviewItems.length);
  const highRiskReviews = reviewItems.filter((item) => ["high", "critical"].includes(item.risk_level)).length;
  const lowConfidenceReviews = reviewItems.filter((item) => (item.evidence.confidence ?? 0) < 0.55).length;
  const noKnowledgeReviews = reviewItems.filter((item) => item.evidence.retrieved_knowledge_count === 0).length;
  const strongEvidenceReviews = reviewItems.filter((item) => {
    const confidence = item.evidence.confidence ?? 0;
    return confidence >= 0.7 && item.evidence.retrieved_knowledge_count > 0 && !["high", "critical"].includes(item.risk_level);
  }).length;
  const pendingDrafts = outboxDrafts.filter((draft) => draft.status === "pending_confirmation").length;
  const readyDrafts = outboxDrafts.filter((draft) => ["ready_to_send", "queued"].includes(draft.status)).length;
  const blockedJobs = deliveryJobs.filter((job) =>
    ["blocked", "dead_letter", "dead_lettered", "failed"].includes(job.status)
  ).length;
  const retryJobs = deliveryJobs.filter((job) => ["retry_scheduled", "queued", "running"].includes(job.status)).length;
  const breachedConversations = conversations.filter((item) => item.sla_status === "breached").length;
  const unassignedConversations = conversations.filter((item) => item.assigned_user_id === null).length;
  const latestRun = knowledgeEvaluation.lastRun;
  const inferredKnowledgeGapCases = latestRun
    ? latestRun.case_results.filter((item) =>
        ["no_hit", "expected_terms_missing", "expected_evidence_missing"].includes(item.failure_reason)
      ).length
    : 0;
  const knowledgeGapCases = knowledgeGaps.data.total || inferredKnowledgeGapCases;
  const allRunSummaries = Array.from(new Map(Object.values(knowledgeEvaluation.runsBySet)
    .flat()
    .map((run) => [run.id, run])).values())
    .sort((left, right) => getTimeValue(right.created_at) - getTimeValue(left.created_at));
  const previousRun = latestRun
    ? allRunSummaries.find((run) => run.id !== latestRun.id && run.evaluation_set_id === latestRun.evaluation_set_id)
    : null;
  const hitDelta = latestRun && previousRun ? latestRun.hit_rate - previousRun.hit_rate : null;
  const evaluationFailureCases = latestRun
    ? latestRun.case_results.filter((item) => item.status !== "passed" || Boolean(item.failure_reason))
    : [];
  const evidenceMissingCases = latestRun
    ? latestRun.case_results.filter((item) =>
        ["expected_evidence_missing", "expected_terms_missing"].includes(item.failure_reason)
      ).length
    : 0;
  const openKnowledgeGaps = knowledgeGaps.data.items.filter((item) =>
    ["open", "triaged", "in_progress"].includes(item.status)
  ).length;
  const needsDraftKnowledge = knowledgeGaps.data.items.filter((item) => {
    const remediation = knowledgeGapRemediationPayload(item);
    return ["open", "triaged", "in_progress"].includes(item.status) && !remediation.knowledge_document_id;
  }).length;
  const needsRegression = knowledgeGaps.data.items.filter((item) => {
    const remediation = knowledgeGapRemediationPayload(item);
    return ["open", "triaged", "in_progress"].includes(item.status) && !remediation.regression_evaluation_case_id;
  }).length;
  const qualityTaskHref = (
    section: WorkspaceSection,
    params: {
      task: string;
      title: string;
      description: string;
      status?: string;
      queue?: string;
      emptyText?: string;
    }
  ) =>
    buildWorkspaceTaskHref(section, {
      source: "quality",
      task: params.task,
      title: params.title,
      description: params.description,
      range: "7d",
      channelId: null,
      channelLabel: "全部渠道",
      status: params.status,
      queue: params.queue,
      emptyText: params.emptyText
    });
  const qualityLinks = {
    conversations: qualityTaskHref("live", {
      task: "live-inbound",
      title: "核对质量复盘关联会话",
      description: "先看最近进入质量复盘的会话池，确认问题是否集中在某个渠道、班次或话题。",
      queue: "all",
      emptyText: "近 7 天没有可关联的会话样本。"
    }),
    knowledgeGap: qualityTaskHref("gaps", {
      task: "quality-knowledge-gap",
      title: "补齐知识缺口",
      description: "来自质量复盘的无知识命中、题库失败和证据缺失信号，优先生成知识草稿并加入回归题。",
      status: "open",
      emptyText: "当前没有待处理知识缺口，可先运行题库或复核人审样本。"
    }),
    lowConfidence: qualityTaskHref("live", {
      task: "quality-low-confidence",
      title: "复核低置信会话",
      description: "回到接待工作台，只看需要人工接管的低置信、弱引用或期望词缺失会话。",
      queue: "needs_review",
      emptyText: "当前没有低置信转人工会话。"
    }),
    highRisk: qualityTaskHref("live", {
      task: "quality-high-risk",
      title: "复核高风险会话",
      description: "赔付、法务、投诉和敏感承诺类问题回到接待工作台转人工处理，并沉淀风险话术。",
      queue: "high_risk",
      emptyText: "当前没有高风险转人工会话。"
    }),
    channelFailure: qualityTaskHref("channels", {
      task: "quality-channel-failure",
      title: "处理渠道与外发异常",
      description: "把失败回执、限流、授权异常和队列阻断集中到渠道中心复盘；真实外发仍保持关闭。",
      status: "open",
      emptyText: "当前没有打开的渠道失败复盘项。"
    }),
    pendingSend: qualityTaskHref("live", {
      task: "quality-pending-send",
      title: "查看待确认回复",
      description: "在接待工作台核对已生成但仍未完成发送前确认的回复，避免审核通过被误解为已外发。",
      queue: "pending_outbox",
      emptyText: "当前没有待确认回复。"
    }),
    slaRouting: qualityTaskHref("live", {
      task: "high-risk-conversations",
      title: "处理 SLA 与分配风险",
      description: "从质量复盘回到接待工作台，优先领取超时或未分配会话。",
      queue: "risk",
      emptyText: "当前没有高风险或超时会话。"
    }),
    regression: qualityTaskHref("evals", {
      task: "quality-regression",
      title: "补充回归验证",
      description: "将已定位错因加入固定题集，发布知识前后都用同一题集复测，避免只看单次命中率。",
      status: "needs_regression",
      emptyText: "当前没有待补回归题的缺口。"
    }),
    finalAnswerLabels: qualityTaskHref("evals", {
      task: "quality-final-answer-labels",
      title: "补最终回复样本和人工标签",
      description: "先保存最终客服回复样本，再标注事实正确、引用充分、禁用承诺和转人工正确性。",
      status: "needs_label",
      emptyText: "当前没有待标注的最终回复样本。"
    }),
    knowledgeRepair: qualityTaskHref("knowledge", {
      task: "quality-knowledge-repair",
      title: "按错因修复知识库",
      description: "把错误样本回写为业务对象、标准问答、流程政策或禁用承诺规则。",
      status: "draft",
      emptyText: "当前没有从质量复盘带入的知识修复任务。"
    }),
    replyStrategy: qualityTaskHref("knowledge", {
      task: "quality-reply-strategy",
      title: "调整自动回复策略",
      description: "把客户可理解的自动回复策略写入知识运营页：高置信自动回复，风险和低置信转人工。",
      status: "policy",
      emptyText: "当前没有待调整的自动回复策略。"
    })
  };
  const rootCauses: QualityIssueBreakdown[] = [
    {
      key: "no-knowledge",
      label: "知识没有覆盖",
      count: knowledgeGapCases + noKnowledgeReviews,
      detail: "无知识命中、题库无命中或缺少期望证据。",
      action: "补文档草稿并加入回归题",
      href: qualityLinks.knowledgeGap,
      tone: (knowledgeGapCases + noKnowledgeReviews > 0 ? "warning" : "success") as QualityIssueBreakdown["tone"]
    },
    {
      key: "low-confidence",
      label: "回答置信不足",
      count: lowConfidenceReviews + evidenceMissingCases,
      detail: "草稿置信低、引用弱或期望词缺失。",
      action: "核对提示词、检索参数和知识片段",
      href: qualityLinks.lowConfidence,
      tone: (lowConfidenceReviews + evidenceMissingCases > 0 ? "warning" : "success") as QualityIssueBreakdown["tone"]
    },
    {
      key: "high-risk",
      label: "高风险需人工",
      count: highRiskReviews,
      detail: "赔付、法务、投诉和敏感承诺不适合自动放行。",
      action: "保持人审并补风险话术",
      href: qualityLinks.highRisk,
      tone: (highRiskReviews > 0 ? "urgent" : "success") as QualityIssueBreakdown["tone"]
    },
    {
      key: "delivery-failure",
      label: "渠道或外发异常",
      count: failureReviews.length + blockedJobs,
      detail: "回执异常、队列阻断、外发开关或授权问题。",
      action: "处理失败复盘和渠道配置",
      href: qualityLinks.channelFailure,
      tone: (failureReviews.length + blockedJobs > 0 ? "urgent" : "success") as QualityIssueBreakdown["tone"]
    },
    {
      key: "pending-send",
      label: "回复未闭环",
      count: pendingDrafts + readyDrafts + retryJobs,
      detail: "已准备回复还没有完成接管确认或链路检查。",
      action: "复核接待记录和链路状态",
      href: qualityLinks.pendingSend,
      tone: (pendingDrafts + readyDrafts + retryJobs > 0 ? "warning" : "success") as QualityIssueBreakdown["tone"]
    },
    {
      key: "sla-routing",
      label: "分配和时效风险",
      count: breachedConversations + unassignedConversations,
      detail: "会话未分配或 SLA 超时会放大客户体验风险。",
      action: "领取会话、补团队分配和 SLA 处理",
      href: qualityLinks.slaRouting,
      tone: (breachedConversations > 0 ? "urgent" : breachedConversations + unassignedConversations > 0 ? "warning" : "success") as QualityIssueBreakdown["tone"]
    }
  ].sort((left, right) => right.count - left.count);
  const issueTotal = rootCauses.reduce((total, item) => total + item.count, 0);
  const boundedProgress = (value: number) => Math.max(0, Math.min(100, value));
  const knowledgeDraftProgress = openKnowledgeGaps > 0
    ? boundedProgress(Math.round(((openKnowledgeGaps - needsDraftKnowledge) / openKnowledgeGaps) * 100))
    : 100;
  const regressionProgress = latestRun && latestRun.total_cases > 0
    ? boundedProgress(Math.round((1 - latestRun.needs_review_cases / latestRun.total_cases) * 100))
    : issueTotal > 0
      ? 0
      : 100;
  const channelRepairProgress = deliveryJobs.length > 0
    ? boundedProgress(Math.round(((deliveryJobs.length - blockedJobs) / deliveryJobs.length) * 100))
    : failureReviews.length > 0
      ? 20
      : 100;
  const outboxGateProgress = pendingDrafts + readyDrafts + retryJobs > 0
    ? boundedProgress(Math.round((readyDrafts / Math.max(pendingDrafts + readyDrafts + retryJobs, 1)) * 100))
    : 100;
  const repairPaths: QualityRepairPath[] = [
    {
      key: "knowledge-coverage",
      label: "补齐知识覆盖",
      source: `${knowledgeGapCases + noKnowledgeReviews} 个无知识或证据缺失信号`,
      evidence: `待草稿 ${needsDraftKnowledge} · 待回归 ${needsRegression}`,
      owner: "知识负责人",
      next: "进入知识缺口，生成草稿并加入回归题",
      href: qualityLinks.knowledgeGap,
      count: knowledgeGapCases + noKnowledgeReviews,
      progress: knowledgeDraftProgress,
      tone: (knowledgeGapCases + noKnowledgeReviews > 0 ? "warning" : "success") as QualityRepairPath["tone"]
    },
    {
      key: "review-evidence",
      label: "复核低置信证据",
      source: `${lowConfidenceReviews + evidenceMissingCases} 个低置信或弱引用信号`,
      evidence: latestRun ? `引用覆盖 ${formatPercent(latestRun.citation_coverage)} · 需复盘 ${latestRun.needs_review_cases}` : "等待固定题集运行",
      owner: "运营管理员",
      next: "进入接待台，先核引用再决定补知识或改话术",
      href: qualityLinks.lowConfidence,
      count: lowConfidenceReviews + evidenceMissingCases,
      progress: latestRun ? boundedProgress(Math.round(latestRun.citation_coverage * 100)) : lowConfidenceReviews > 0 ? 25 : 100,
      tone: (lowConfidenceReviews + evidenceMissingCases > 0 ? "warning" : "success") as QualityRepairPath["tone"]
    },
    {
      key: "risk-policy",
      label: "沉淀风险话术",
      source: `${highRiskReviews} 个高风险人审样本`,
      evidence: "赔付、法务、投诉、敏感承诺继续转人工",
      owner: "客服主管",
      next: "进入接待台，保留人工门禁并补风险标准话术",
      href: qualityLinks.highRisk,
      count: highRiskReviews,
      progress: highRiskReviews > 0 ? 35 : 100,
      tone: (highRiskReviews > 0 ? "urgent" : "success") as QualityRepairPath["tone"]
    },
    {
      key: "channel-exception",
      label: "处理渠道异常",
      source: `${failureReviews.length + blockedJobs} 个失败复盘或阻断队列`,
      evidence: "回执异常、授权异常、限流和外部发送受控都要可追踪",
      owner: "交付/售后",
      next: "进入渠道中心，确认官方授权、回调和队列状态",
      href: qualityLinks.channelFailure,
      count: failureReviews.length + blockedJobs,
      progress: channelRepairProgress,
      tone: (failureReviews.length + blockedJobs > 0 ? "urgent" : "success") as QualityRepairPath["tone"]
    },
    {
      key: "regression-loop",
      label: "补充回归验证",
      source: `${needsRegression + evaluationFailureCases.length} 个待复测信号`,
      evidence: latestRun && previousRun
        ? `同题集变化 ${formatSignedPercent(hitDelta ?? 0)}`
        : "需要建立同题集前后对比",
      owner: "知识负责人",
      next: "进入评测页，用固定题集验证发布前后变化",
      href: qualityLinks.regression,
      count: needsRegression + evaluationFailureCases.length,
      progress: regressionProgress,
      tone: (needsRegression + evaluationFailureCases.length > 0 ? "warning" : "success") as QualityRepairPath["tone"]
    },
    {
      key: "send-gate",
      label: "清理回复闭环",
      source: `${pendingDrafts + readyDrafts + retryJobs} 个待确认或待复核任务`,
      evidence: "回复准备完成不等于已外发，真实发送仍需独立授权和回执",
      owner: "坐席/管理员",
      next: "进入接待台，确认接管记录和链路状态",
      href: qualityLinks.pendingSend,
      count: pendingDrafts + readyDrafts + retryJobs,
      progress: outboxGateProgress,
      tone: (pendingDrafts + readyDrafts + retryJobs > 0 ? "warning" : "success") as QualityRepairPath["tone"]
    }
  ].sort((left, right) => right.count - left.count);
  const repairAverage = repairPaths.length > 0
    ? Math.round(repairPaths.reduce((total, item) => total + item.progress, 0) / repairPaths.length)
    : 100;
  const funnelSteps: QualityFunnelStep[] = [
    { label: "入站会话", count: totalConversations, note: "当前筛选会话池", href: qualityLinks.conversations },
    { label: "转人工会话", count: reviewItems.length, note: "低置信、高风险或无知识", href: qualityLinks.lowConfidence },
    { label: "可用回复", count: strongEvidenceReviews + pendingDrafts, note: "有证据或已完成接管准备", href: qualityLinks.pendingSend },
    { label: "待确认回复", count: pendingDrafts + readyDrafts, note: "外发前仍需授权和回执", href: qualityLinks.pendingSend },
    { label: "链路检查", count: deliveryJobs.length, note: "幂等、限流、回执占位", href: qualityLinks.pendingSend },
    { label: "失败复盘", count: failureReviews.length + blockedJobs, note: "异常回执和阻断项", href: qualityLinks.channelFailure }
  ];
  const funnelMax = Math.max(...funnelSteps.map((item) => item.count), 1);
  const trendRuns = allRunSummaries.slice(0, 6).reverse();
  const channelNames = Array.from(new Set(conversations.map((item) => item.channel_name || item.channel_type || "未知渠道")));
  const channelRows = channelNames.map((channelName) => {
    const channelConversations = conversations.filter((item) => (item.channel_name || item.channel_type || "未知渠道") === channelName);
    const channelReviewCount = channelConversations.reduce((total, item) => total + item.human_review_open_count, 0);
    const channelFailureCount = channelConversations.reduce((total, item) => total + item.delivery_failure_open_count, 0)
      + failureReviews.filter((item) => String(item.channel_id) === String(channelConversations[0]?.channel_id ?? "")).length;
    return {
      channelName,
      total: channelConversations.length,
      reviews: channelReviewCount,
      failures: channelFailureCount,
      sla: channelConversations.filter((item) => item.sla_status === "breached").length
    };
  }).sort((left, right) => (right.failures + right.reviews + right.sla) - (left.failures + left.reviews + left.sla));
  const channelMax = Math.max(...channelRows.map((item) => item.total + item.reviews + item.failures + item.sla), 1);
  const gapStatusLabels = [
    { key: "open", label: "待处理" },
    { key: "triaged", label: "已分诊" },
    { key: "in_progress", label: "处理中" },
    { key: "resolved", label: "已解决" }
  ];
  const gapSourceRows = [
    { key: "human_review", label: "人审缺口" },
    { key: "evaluation_run", label: "评测缺口" },
    { key: "manual", label: "手动缺口" }
  ].map((row) => ({
    ...row,
    cells: gapStatusLabels.map((status) =>
      knowledgeGaps.data.items.filter((gap) => gap.source_type === row.key && gap.status === status.key).length
    )
  }));
  const matrixRows = [
    { key: "critical", label: "紧急" },
    { key: "high", label: "高" },
    { key: "medium", label: "中" },
    { key: "low", label: "低" }
  ].map((risk) => {
    const items = reviewItems.filter((item) => item.risk_level === risk.key);
    return {
      ...risk,
      noKnowledge: items.filter((item) => item.evidence.retrieved_knowledge_count === 0).length,
      weak: items.filter((item) => item.evidence.retrieved_knowledge_count > 0 && (item.evidence.confidence ?? 0) < 0.55).length,
      strong: items.filter((item) => item.evidence.retrieved_knowledge_count > 0 && (item.evidence.confidence ?? 0) >= 0.55).length
    };
  });
  const drillSamples: QualityDrillSample[] = [
    ...reviewItems.slice(0, 3).map((item) => ({
      id: `review-${item.id}`,
      source: "人审",
      title: `人审 #${item.id} · ${formatPriorityLabel(item.risk_level)}`,
      excerpt: item.trigger_message?.content || item.conversation.subject || item.draft_reply,
      cause: item.evidence.retrieved_knowledge_count === 0 ? "无知识命中" : `置信 ${formatPercent(item.evidence.confidence)}`,
      action: item.evidence.retrieved_knowledge_count === 0 ? "补知识后再审核" : "核对草稿和引用证据",
      href: item.evidence.retrieved_knowledge_count === 0 ? qualityLinks.knowledgeGap : qualityLinks.lowConfidence,
      tone: ["critical", "high"].includes(item.risk_level) ? "urgent" : "warning"
    } as QualityDrillSample)),
    ...knowledgeGaps.data.items.slice(0, 3).map((gap) => ({
      id: `gap-${gap.id}`,
      source: "缺口",
      title: `${formatKnowledgeGapSource(gap.source_type)} #${gap.id}`,
      excerpt: gap.question_excerpt || gap.source_excerpt || gap.source_title,
      cause: `${gap.gap_type} · ${formatKnowledgeGapStatus(gap.status)}`,
      action: knowledgeGapRegressionCaseId(gap) ? "等待回归验证" : "生成草稿并加入回归",
      href: qualityLinks.knowledgeGap,
      tone: ["critical", "high"].includes(gap.severity) ? "urgent" : "warning"
    } as QualityDrillSample)),
    ...failureReviews.slice(0, 2).map((failure) => ({
      id: `failure-${failure.id}`,
      source: "渠道",
      title: `失败复盘 #${failure.id}`,
      excerpt: failure.review_reason || failure.provider_status || failure.normalized_status,
      cause: failure.provider_error_code || failure.normalized_status,
      action: failure.next_action || "人工复核渠道状态",
      href: qualityLinks.channelFailure,
      tone: failure.severity === "critical" || failure.severity === "high" ? "urgent" : "normal"
    } as QualityDrillSample)),
    ...evaluationFailureCases.slice(0, 3).map((item) => ({
      id: `eval-${item.id}`,
      source: "题库",
      title: `评测样本 #${item.id}`,
      excerpt: item.question,
      cause: item.failure_reason || item.status,
      action: "回到知识文档和回归题修复",
      href: qualityLinks.regression,
      tone: "warning"
    } as QualityDrillSample))
  ].slice(0, 8);
  const monthlyReview = monthlyQualityReview.data;
  const opsReport = monthlyOpsReport.data;
  const monthlyMetricHighlights = monthlyReview?.metrics.slice(0, 4) ?? [];
  const monthlyOpenActions = monthlyReview?.action_items
    .filter((item) => item.status !== "done")
    .slice(0, 4) ?? [];
  const monthlyRootCauses = monthlyReview?.root_causes
    .filter((item) => item.count > 0 || item.severity === "critical" || item.severity === "warning")
    .slice(0, 4) ?? [];
  const customerReport = customerQualityReport.data;
  const customerReportSections = customerReport?.sections.slice(0, 4) ?? [];
  const customerReportActions = customerReport?.action_plan.filter((item) => item.status !== "done").slice(0, 3) ?? [];
  const gapRehearsalEvidence = customerReport?.gap_rehearsal_evidence ?? null;
  const latestSummaryPayload = latestRun?.summary_payload ?? {};
  const finalAnswerSampledCases = getRecordNumber(latestSummaryPayload, "final_answer_sampled_cases") ?? 0;
  const finalAnswerSampleCoverage = getRecordNumber(latestSummaryPayload, "final_answer_sample_coverage");
  const finalAnswerFactualityLabeledCases = getRecordNumber(latestSummaryPayload, "final_answer_factuality_labeled_cases") ?? 0;
  const finalAnswerFactualityRate = getRecordNumber(latestSummaryPayload, "final_answer_factuality_rate");
  const finalAnswerFactualityMeasured = finalAnswerFactualityLabeledCases > 0 && finalAnswerFactualityRate !== null;
  const finalAnswerCorrectCases = getRecordNumber(latestSummaryPayload, "final_answer_factuality_correct_cases") ?? 0;
  const finalAnswerNeedsHumanCases = getRecordNumber(latestSummaryPayload, "final_answer_factuality_needs_human_review_cases") ?? 0;
  const finalAnswerIncorrectCases = getRecordNumber(latestSummaryPayload, "final_answer_factuality_incorrect_cases") ?? 0;
  const finalAnswerPartialCases = getRecordNumber(latestSummaryPayload, "final_answer_factuality_partially_correct_cases") ?? 0;
  const onlineReceiptSummary = onlineReceiptQuality.data;
  const onlineReceiptObserved = Boolean(onlineReceiptSummary && onlineReceiptSummary.receipt_total > 0);
  const receiptGateRows = onlineReceiptSummary?.quality_gates ?? [];
  const receiptProviderRows = onlineReceiptSummary?.provider_breakdown.slice(0, 4) ?? [];
  const h2w3LoopCards = [
    {
      key: "sample",
      label: "最终回复样本",
      value: latestRun ? `${finalAnswerSampledCases}/${latestRun.total_cases}` : "待采集",
      detail: finalAnswerSampleCoverage !== null ? `采样覆盖 ${formatPercent(finalAnswerSampleCoverage)}` : "先在知识评测页保存最终客服回复样本",
      href: qualityLinks.finalAnswerLabels,
      state: finalAnswerSampleCoverage !== null && finalAnswerSampleCoverage >= 0.8 ? "ok" : "warning"
    },
    {
      key: "label",
      label: "人工事实性标签",
      value: finalAnswerFactualityMeasured ? formatPercent(finalAnswerFactualityRate) : "未成立",
      detail: `${finalAnswerFactualityLabeledCases} 条已标注；未标注前不报完整准确率`,
      href: qualityLinks.finalAnswerLabels,
      state: finalAnswerFactualityMeasured ? "ok" : "critical"
    },
    {
      key: "cause",
      label: "错因定位",
      value: `${issueTotal}`,
      detail: "按无知识、弱证据、风险策略、渠道异常和回复闭环归类",
      href: qualityLinks.knowledgeGap,
      state: issueTotal > 0 ? "warning" : "ok"
    },
    {
      key: "repair",
      label: "知识修复入口",
      value: `${openKnowledgeGaps}`,
      detail: "错误样本回到知识缺口、知识草稿和自动回复策略",
      href: qualityLinks.knowledgeRepair,
      state: openKnowledgeGaps > 0 ? "warning" : "ok"
    },
    {
      key: "regression",
      label: "发布后回归",
      value: latestRun && previousRun ? formatSignedPercent(hitDelta ?? 0) : "待同题集",
      detail: "发布前后必须使用同一题集复测，不能只看单次命中",
      href: qualityLinks.regression,
      state: latestRun && previousRun ? "ok" : "warning"
    },
    {
      key: "receipt",
      label: "线上回执",
      value: onlineReceiptObserved ? `${onlineReceiptSummary?.receipt_total ?? 0} 条` : "未接入",
      detail: onlineReceiptObserved
        ? `送达 ${formatPercent(onlineReceiptSummary?.delivery_success_rate ?? null)} · 失败复盘 ${onlineReceiptSummary?.open_failure_reviews ?? 0}`
        : "真实外发继续关闭，不展示完整线上准确率",
      href: qualityLinks.channelFailure,
      state: onlineReceiptObserved ? "warning" : "muted"
    }
  ];
  const h2w3CauseRows = [
    {
      key: "correct",
      label: "正确",
      count: finalAnswerCorrectCases,
      detail: "事实正确且引用充分的最终回复",
      tone: "ok"
    },
    {
      key: "partial",
      label: "部分正确",
      count: finalAnswerPartialCases,
      detail: "可回答但需要补充限制条件或引用",
      tone: "warning"
    },
    {
      key: "incorrect",
      label: "错误",
      count: finalAnswerIncorrectCases,
      detail: "进入知识缺口或标准话术修复",
      tone: "critical"
    },
    {
      key: "handoff",
      label: "需人工",
      count: finalAnswerNeedsHumanCases,
      detail: "转人工判断正确时不计为知识回答成功",
      tone: "warning"
    }
  ];
  const h2w3RepairActions = [
    {
      label: "补知识缺口",
      detail: "无知识、知识过旧、引用不足的样本进入缺口池",
      href: qualityLinks.knowledgeGap
    },
    {
      label: "编辑知识库",
      detail: "补业务对象、标准问答、流程政策和禁用承诺",
      href: qualityLinks.knowledgeRepair
    },
    {
      label: "调整自动回复策略",
      detail: "把高风险、低置信和无法确认的问题转人工",
      href: qualityLinks.replyStrategy
    },
    {
      label: "跑回归验证",
      detail: "用同一题集验证知识发布前后变化",
      href: qualityLinks.regression
    }
  ];
  const canSubmitCustomerReportSignoff = Boolean(
    canRecordCustomerQualityReportSignoff &&
      onRecordCustomerQualityReportSignoff &&
      customerReport &&
      customerQualityReport.status !== "loading"
  );

  function handleCustomerReportSignoffSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!canSubmitCustomerReportSignoff || !onRecordCustomerQualityReportSignoff) {
      return;
    }
    const data = new FormData(event.currentTarget);
    onRecordCustomerQualityReportSignoff({
      signoff_status: String(data.get("signoff_status") || "accepted_with_notes") as CustomerQualityReportSignoffCreate["signoff_status"],
      signer_name: String(data.get("signer_name") || "").trim(),
      signer_role: String(data.get("signer_role") || "").trim(),
      signer_organization: String(data.get("signer_organization") || "").trim(),
      confirmation_method: String(data.get("confirmation_method") || "local_record") as CustomerQualityReportSignoffCreate["confirmation_method"],
      notes: String(data.get("notes") || "").trim()
    });
    event.currentTarget.reset();
  }

  return (
    <section className="panel quality-review-panel" id="workspace-quality" aria-label="质量复盘" data-quality-smoke="quality-panel">
      <div className="panel-heading">
        <div>
          <h2>质量诊断</h2>
          <p>把低置信、无知识、高风险、外发异常和题库失败集中到一张运营看板，直接指向会话、知识、渠道和回归动作。</p>
        </div>
        <BarChart3 size={20} />
      </div>

      <div className="panel-state-row" aria-label="质量诊断数据状态">
        <DataSourceBadge
          mode={conversationInbox.status === "ready" ? "real" : "demo"}
          label={conversationInbox.status === "ready" ? REAL_DATA_LABEL : PREVIEW_DATA_LABEL}
          detail={conversationInbox.status === "ready" ? "汇总会话、人审、缺口、评测和发送队列" : "当前主要用于展示质量复盘结构"}
        />
        <DataSourceBadge
          mode="local"
          label="质量口径"
          detail="准确率必须结合人工标签，当前 BI 不把检索命中当作完整准确率"
        />
      </div>

      <div className="quality-command-strip" aria-label="质量诊断摘要">
        <article>
          <span>主要错因</span>
          <strong>{rootCauses[0]?.label ?? "暂无异常"}</strong>
          <small>{rootCauses[0]?.count ?? 0} 个信号</small>
        </article>
        <article>
          <span>题库趋势</span>
          <strong>{latestRun && previousRun ? formatSignedPercent(hitDelta ?? 0) : "待建立"}</strong>
          <small>{latestRun ? `最近命中 ${formatPercent(latestRun.hit_rate)}` : "尚未运行题库"}</small>
        </article>
        <article>
          <span>修复队列</span>
          <strong>{needsDraftKnowledge + needsRegression}</strong>
          <small>{needsDraftKnowledge} 草稿 / {needsRegression} 回归</small>
        </article>
        <article>
          <span>准确率口径</span>
          <strong>待人工标签</strong>
          <small>不把检索命中当作完整准确率</small>
        </article>
      </div>

      <section
        className="h2w3-quality-loop"
        data-h2w3-quality-loop="true"
        data-h2w3-boundary="no-full-online-accuracy"
        aria-label="线上回执与准确率闭环"
      >
        <div className="h2w3-quality-loop-head">
          <div>
            <span>质量闭环</span>
            <strong>线上回执与准确率闭环</strong>
            <p>当前先使用本地样本质量和人工标签质量推进闭环；真实平台回执未接入前，不展示完整线上准确率，也不声明完整客服答案准确率。</p>
          </div>
          <b>{onlineReceiptObserved ? "回执待核对" : "真实外发继续关闭"}</b>
        </div>
        <div className="h2w3-loop-grid">
          {h2w3LoopCards.map((card) => (
            <a
              key={card.key}
              className={`h2w3-loop-card ${card.state}`}
              href={card.href}
              data-h2w3-loop-step={card.key}
            >
              <span>{card.label}</span>
              <strong>{card.value}</strong>
              <small>{card.detail}</small>
            </a>
          ))}
        </div>
        <div
          className="h2w3-receipt-evidence"
          data-h2w3d-online-receipt-quality="p3-06u-26h2w3d"
          aria-label="线上回执闭环证据"
        >
          {onlineReceiptQuality.status === "loading" ? (
            <WorkspaceStateNotice kind="loading" message="正在同步线上回执闭环。" compact />
          ) : onlineReceiptQuality.status === "error" ? (
            <WorkspaceStateNotice kind="error" message={onlineReceiptQuality.message || "无法读取线上回执闭环。"} compact />
          ) : onlineReceiptSummary ? (
            <>
              <div className="h2w3-receipt-boundary">
                <span>{onlineReceiptSummary.accuracy_scope_label}</span>
                <p>{onlineReceiptSummary.accuracy_boundary}</p>
              </div>
              <div className="h2w3-receipt-gates">
                {receiptGateRows.map((gate) => (
                  <article key={gate.key} className={`h2w3-receipt-gate ${gate.status}`}>
                    <span>{gate.label}</span>
                    <strong>{gate.status === "ok" ? "已通过" : gate.status === "missing" ? "未成立" : "需关注"}</strong>
                    <small>{gate.detail}</small>
                    <em>{gate.stop_condition}</em>
                  </article>
                ))}
              </div>
              <div className="h2w3-provider-breakdown">
                {receiptProviderRows.length > 0 ? (
                  receiptProviderRows.map((provider) => (
                    <article key={provider.provider}>
                      <span>{provider.provider}</span>
                      <strong>{provider.receipt_count} 条</strong>
                      <small>
                        匹配 {provider.matched_receipts} · 送达 {formatPercent(provider.delivery_success_rate)} · 复盘 {provider.needs_review}
                      </small>
                    </article>
                  ))
                ) : (
                  <WorkspaceStateNotice kind="empty" message="当前没有平台回执分布；正式接入后按渠道展示送达、失败和匹配情况。" compact />
                )}
              </div>
            </>
          ) : (
            <WorkspaceStateNotice kind="empty" message="正式登录后读取线上回执闭环；真实外发继续关闭。" compact />
          )}
        </div>
        <div className="h2w3-quality-closure">
          <div className="h2w3-label-breakdown" data-h2w3-loop-step="sample-to-label">
            <div className="section-title-row">
              <ShieldCheck size={17} />
              <strong>人工标签结果</strong>
            </div>
            {h2w3CauseRows.map((row) => (
              <div key={row.key} className={`h2w3-label-row ${row.tone}`}>
                <span>
                  <strong>{row.label}</strong>
                  <small>{row.detail}</small>
                </span>
                <b>{row.count}</b>
              </div>
            ))}
          </div>
          <div className="h2w3-repair-actions" data-h2w3-loop-step="cause-to-repair">
            <div className="section-title-row">
              <BookOpen size={17} />
              <strong>错因修复入口</strong>
            </div>
            {h2w3RepairActions.map((action) => (
              <a key={action.label} href={action.href}>
                <span>{action.label}</span>
                <small>{action.detail}</small>
              </a>
            ))}
          </div>
          <div className="h2w3-regression-note" data-h2w3-loop-step="post-publish-regression">
            <div className="section-title-row">
              <Activity size={17} />
              <strong>回归验收门禁</strong>
            </div>
            <p>知识发布前后必须使用同一题集复测；错因只看得到但不能进入修复时，本轮质量闭环不算通过。</p>
            <ul>
              <li>样本质量、人工标签质量、真实线上回执分开展示。</li>
              <li>检索命中率不能替代最终客服答案正确率。</li>
              <li>真实平台外发需要官方授权、测试白名单、回执、失败重试和审计闭环。</li>
            </ul>
          </div>
        </div>
      </section>

      <section className="monthly-quality-review" data-quality-smoke="monthly-review">
        <div className="section-title-row">
          <Activity size={18} />
          <strong>本月复盘包</strong>
          {monthlyReview ? <small>{monthlyReview.period}</small> : null}
        </div>
        {monthlyQualityReview.status === "loading" ? (
          <WorkspaceStateNotice kind="loading" message="正在生成本月质量复盘包。" compact />
        ) : monthlyQualityReview.status === "error" ? (
          <WorkspaceStateNotice kind="error" message={monthlyQualityReview.message || "无法读取本月质量复盘包。"} compact />
        ) : monthlyReview ? (
          <>
            <div className="monthly-review-metrics">
              {monthlyMetricHighlights.map((metric) => (
                <article key={metric.key} className={`monthly-review-metric ${metric.status}`}>
                  <span>{metric.label}</span>
                  <strong>{metric.value}</strong>
                  <small>{metric.detail}</small>
                  <b>{formatReviewSignalStatus(metric.status)}</b>
                </article>
              ))}
            </div>
            <div className="monthly-review-body">
              <div>
                <h3>主要问题</h3>
                <div className="monthly-review-cause-list">
                  {monthlyRootCauses.length > 0 ? monthlyRootCauses.map((cause) => (
                    <a key={cause.key} href={cause.target_href} className={`monthly-review-cause ${cause.severity}`}>
                      <span>
                        <strong>{cause.label}</strong>
                        <small>{cause.detail}</small>
                      </span>
                      <b>{cause.count}</b>
                      <em>{cause.next_action}</em>
                    </a>
                  )) : (
                    <WorkspaceStateNotice kind="empty" message="本月暂无高优先级质量问题。" compact />
                  )}
                </div>
              </div>
              <div>
                <h3>下一步动作</h3>
                <div className="monthly-review-action-list">
                  {monthlyOpenActions.length > 0 ? monthlyOpenActions.map((action) => (
                    <a key={action.key} href={action.target_href} className={`monthly-review-action ${action.status}`}>
                      <span>
                        <small>{action.owner} · {action.priority}</small>
                        <strong>{action.label}</strong>
                      </span>
                      <p>{action.evidence}</p>
                      <b>{action.next_step}</b>
                    </a>
                  )) : (
                    <WorkspaceStateNotice kind="empty" message="本月复盘动作已完成，继续保持同题集回归。" compact />
                  )}
                </div>
              </div>
            </div>
            <div className="monthly-review-boundary">
              <span>边界</span>
              <p>{monthlyReview.data_boundaries[1] ?? "完整客服准确率必须结合真实题库和人工事实性标签确认。"}</p>
            </div>
          </>
        ) : (
          <WorkspaceStateNotice kind="empty" message="正式登录后会生成本月质量复盘包。" compact />
        )}
      </section>

      <section className="monthly-ops-report" id="monthly-ops-report" data-quality-smoke="monthly-ops-report">
        <div className="section-title-row">
          <ShieldCheck size={18} />
          <strong>月度运维报告</strong>
          {opsReport ? <small>{opsReport.period}</small> : null}
        </div>
        {monthlyOpsReport.status === "loading" ? (
          <WorkspaceStateNotice kind="loading" message="正在汇总本月运维报告。" compact />
        ) : monthlyOpsReport.status === "error" ? (
          <WorkspaceStateNotice kind="error" message={monthlyOpsReport.message || "无法读取本月运维报告。"} compact />
        ) : opsReport ? (
          <>
            <div className="monthly-ops-hero">
              <div>
                <span>{opsReport.status_label}</span>
                <strong>{opsReport.health_score}/100</strong>
                <small>{opsReport.health_label}</small>
              </div>
              <p>{opsReport.monthly_health.summary}</p>
            </div>
            <div className="monthly-ops-grid">
              {[opsReport.reply_quality, opsReport.knowledge_maintenance, opsReport.model_cost, opsReport.local_maintenance].map((section) => (
                <article key={section.key} className={`monthly-ops-card ${section.status}`}>
                  <div>
                    <span>{section.title}</span>
                    <strong>{formatReviewSignalStatus(section.status)}</strong>
                  </div>
                  <p>{section.summary}</p>
                  <div className="monthly-ops-metrics">
                    {section.metrics.slice(0, 3).map((metric) => (
                      <span key={metric.key}>
                        <b>{metric.value}</b>
                        {metric.label}
                      </span>
                    ))}
                  </div>
                </article>
              ))}
            </div>
            <div className="monthly-ops-bottom">
              <div>
                <h3>风险事项</h3>
                {opsReport.risk_items.length > 0 ? (
                  <div className="monthly-ops-risk-list">
                    {opsReport.risk_items.slice(0, 4).map((risk) => (
                      <span key={risk.key} className={`is-${risk.severity}`}>
                        <b>{risk.label}</b>
                        {risk.recommended_action}
                      </span>
                    ))}
                  </div>
                ) : (
                  <WorkspaceStateNotice kind="empty" message="当前没有高优先级运维风险。" compact />
                )}
              </div>
              <div>
                <h3>下月建议</h3>
                <ul>
                  {opsReport.next_month_actions.slice(0, 4).map((action) => (
                    <li key={action}>{action}</li>
                  ))}
                </ul>
              </div>
            </div>
            <div className="monthly-review-boundary">
              <span>边界</span>
              <p>{opsReport.data_boundaries[0] ?? "月度运维报告是试跑复盘材料，不是生产服务等级承诺。"}</p>
            </div>
          </>
        ) : (
          <WorkspaceStateNotice kind="empty" message="负责人账号登录后可生成本月运维报告。" compact />
        )}
      </section>

      <section className="customer-quality-report" data-quality-smoke="customer-quality-report">
        <div className="customer-report-head">
          <div>
            <span>客户可读质量报告</span>
            <strong>{customerReport?.report_title ?? "等待生成质量报告"}</strong>
            <small>用于客户月度复盘和试跑确认；不展示原始客户问题、完整回复或渠道密钥。</small>
          </div>
          {customerReport ? (
            <div className="customer-report-head-actions">
              <div className="customer-report-export-buttons" data-h2w4-report-export="p3-06u-26h2w4">
                {(["html", "xlsx", "docx"] as const).map((format) => (
                  <button
                    key={format}
                    type="button"
                    className="ghost-action"
                    data-customer-report-export-format={format}
                    onClick={() => onExportCustomerQualityReport?.(format)}
                    disabled={!onExportCustomerQualityReport || customerQualityReport.status === "loading"}
                  >
                    <Download size={15} />
                    <span>{formatReportExportFormat(format)}</span>
                  </button>
                ))}
              </div>
              <div className={`customer-report-score ${customerReport.report_status}`}>
                <b>{customerReport.report_confidence_score}</b>
                <span>{customerReport.report_status_label}</span>
              </div>
            </div>
          ) : null}
        </div>
        {customerQualityReport.status === "loading" ? (
          <WorkspaceStateNotice kind="loading" message="正在生成客户质量报告。" compact />
        ) : customerQualityReport.status === "error" ? (
          <WorkspaceStateNotice kind="error" message={customerQualityReport.message || "无法读取客户质量报告。"} compact />
        ) : customerReport ? (
          <>
            {customerQualityReport.message ? (
              <div className="customer-report-export-status" data-customer-report-export-status="p3-06u-26h2s">
                {customerQualityReport.message}
              </div>
            ) : null}
            <div className="customer-report-summary">
              <p>{customerReport.quality_conclusion}</p>
              <ul>
                {customerReport.executive_summary.slice(0, 3).map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
            <div className="customer-report-metrics">
              {customerReport.headline_metrics.map((metric) => (
                <article key={metric.key} className={metric.status}>
                  <span>{metric.label}</span>
                  <strong>{metric.value}</strong>
                  <small>{metric.detail}</small>
                </article>
              ))}
            </div>
            {gapRehearsalEvidence ? (
              <section
                className={`customer-report-gap-evidence ${gapRehearsalEvidence.ready_for_gap_quality_report_review ? "ok" : "warning"}`}
                data-h2w11k-gap-rehearsal-evidence="p3-06u-26h2w11k"
              >
                <div>
                  <span>缺口样本本地演练证据</span>
                  <strong>{gapRehearsalEvidence.case_count} 条样本已复核</strong>
                  <p>{gapRehearsalEvidence.conclusion}</p>
                </div>
                <div className="customer-report-gap-evidence-grid">
                  <article>
                    <span>自动回复</span>
                    <b>{gapRehearsalEvidence.auto_reply_label_count} 条</b>
                    <small>事实性 {formatPercent(gapRehearsalEvidence.auto_reply_factuality_rate)}</small>
                  </article>
                  <article>
                    <span>转人工</span>
                    <b>{gapRehearsalEvidence.handoff_not_applicable_count} 条</b>
                    <small>正确率 {formatPercent(gapRehearsalEvidence.handoff_correct_rate)}</small>
                  </article>
                  <article>
                    <span>引用与禁用承诺</span>
                    <b>{formatPercent(gapRehearsalEvidence.citation_sufficient_rate)}</b>
                    <small>禁用承诺通过 {formatPercent(gapRehearsalEvidence.forbidden_commitment_pass_rate)}</small>
                  </article>
                </div>
                <p className="customer-report-gap-evidence-boundary">
                  {gapRehearsalEvidence.boundary}
                  {" "}这不是正式线上准确率确认。
                  {gapRehearsalEvidence.final_answer_text_exported ? " 当前证据异常：完整最终答案正文被导出。" : " 当前证据不导出完整最终答案正文。"}
                </p>
              </section>
            ) : null}
            <div className="customer-report-sections">
              {customerReportSections.map((section) => (
                <article key={section.key} className={section.status}>
                  <span>{formatReviewSignalStatus(section.status)}</span>
                  <strong>{section.title}</strong>
                  <p>{section.summary}</p>
                  <small>{section.evidence}</small>
                  <ul>
                    {section.next_steps.slice(0, 2).map((step) => (
                      <li key={step}>{step}</li>
                    ))}
                  </ul>
                </article>
              ))}
            </div>
            <div className="customer-report-actions">
              <strong>试跑确认前动作</strong>
              {customerReportActions.length > 0 ? customerReportActions.map((action) => (
                <article key={action.key}>
                  <span>{action.owner} · {action.priority}</span>
                  <b>{action.label}</b>
                  <small>{action.evidence}</small>
                  <p>{action.next_step}</p>
                </article>
              )) : (
                <WorkspaceStateNotice kind="empty" message="当前客户报告动作已完成，继续保持同题集回归和月度抽样。" compact />
              )}
            </div>
            <div className="customer-report-boundary">
              <span>确认边界</span>
              <p>{customerReport.signoff_checklist[customerReport.signoff_checklist.length - 1]}</p>
            </div>
            <form
              className="customer-report-signoff-form"
              data-customer-report-signoff="p3-06u-26h2t"
              onSubmit={handleCustomerReportSignoffSubmit}
            >
              <div className="customer-report-signoff-head">
                <div>
                  <span>客户确认记录</span>
                  <strong>记录本期报告确认结果</strong>
                </div>
                <small>本记录进入本地审计；不是正式电子签章，也不代表真实渠道外发已验收。</small>
              </div>
              <div className="customer-report-signoff-grid">
                <label>
                  <span>确认结果</span>
                  <select name="signoff_status" defaultValue="accepted_with_notes" disabled={!canSubmitCustomerReportSignoff}>
                    <option value="accepted">确认通过</option>
                    <option value="accepted_with_notes">确认通过，有备注</option>
                    <option value="needs_rework">需要返修后再确认</option>
                    <option value="rejected">不通过</option>
                  </select>
                </label>
                <label>
                  <span>确认方式</span>
                  <select name="confirmation_method" defaultValue="local_record" disabled={!canSubmitCustomerReportSignoff}>
                    <option value="local_record">本地记录</option>
                    <option value="email_confirmation">邮件确认</option>
                    <option value="meeting_confirmation">会议确认</option>
                    <option value="offline_signature">线下签字</option>
                  </select>
                </label>
                <label>
                  <span>确认人</span>
                  <input name="signer_name" placeholder="填写姓名" maxLength={80} required disabled={!canSubmitCustomerReportSignoff} />
                </label>
                <label>
                  <span>角色</span>
                  <input name="signer_role" placeholder="负责人 / 运营 / 店长" maxLength={80} disabled={!canSubmitCustomerReportSignoff} />
                </label>
                <label>
                  <span>单位</span>
                  <input name="signer_organization" placeholder="公司或门店名称" maxLength={120} disabled={!canSubmitCustomerReportSignoff} />
                </label>
              </div>
              <label className="customer-report-signoff-note">
                <span>备注</span>
                <textarea
                  name="notes"
                  placeholder="只填写结论性备注；系统只在审计中保存备注摘要，不保存备注原文。"
                  maxLength={1000}
                  rows={3}
                  disabled={!canSubmitCustomerReportSignoff}
                />
              </label>
              <div className="customer-report-signoff-actions">
                <button type="submit" className="primary-action" disabled={!canSubmitCustomerReportSignoff}>
                  记录客户确认
                </button>
                {!canRecordCustomerQualityReportSignoff ? (
                  <small>仅负责人账号可记录客户确认结果。</small>
                ) : (
                  <small data-customer-report-signoff-boundary="p3-06u-26h2t">真实外发、线上回执和正式电子签章仍需单独验收。</small>
                )}
              </div>
            </form>
            <section className="customer-report-archive-list" data-h2w4-report-archives="p3-06u-26h2w4">
              <div className="customer-report-signoff-list-head">
                <div>
                  <span>报告归档</span>
                  <strong>{customerQualityReportArchives.data?.total ?? 0} 份</strong>
                </div>
                <small>{customerQualityReportArchives.status === "loading" ? "正在同步" : customerQualityReportArchives.message}</small>
              </div>
              <p className="customer-report-archive-boundary">
                归档文件用于月度复盘和客户确认留存；不包含原始客户问题、完整回复或人工备注原文，也不是正式电子签章。
              </p>
              {customerQualityReportArchives.status === "error" ? (
                <WorkspaceStateNotice kind="error" message={customerQualityReportArchives.message} compact />
              ) : customerQualityReportArchives.data && customerQualityReportArchives.data.items.length > 0 ? (
                <div className="customer-report-archive-items">
                  {customerQualityReportArchives.data.items.slice(0, 6).map((item) => (
                    <article key={item.audit_event_id}>
                      <div>
                        <strong>{formatReportExportFormat(item.export_format)}</strong>
                        <span>{item.filename}</span>
                      </div>
                      <p>{item.period} · {item.report_status_label} · {formatDateTime(item.generated_at)}</p>
                      <small>{formatFileSize(item.body_bytes)} · SHA256 {item.body_sha256 ? item.body_sha256.slice(0, 12) : "未记录"} · 审计号 #{item.audit_event_id}</small>
                      <button
                        type="button"
                        className="ghost-action"
                        onClick={() => onDownloadCustomerQualityReportArchive?.(item.audit_event_id)}
                        disabled={!item.download_supported || !onDownloadCustomerQualityReportArchive || customerQualityReportArchives.status === "loading"}
                      >
                        <Download size={14} />
                        <span>{item.download_supported ? "下载" : "不可下载"}</span>
                      </button>
                    </article>
                  ))}
                </div>
              ) : (
                <WorkspaceStateNotice kind="empty" message="当前还没有导出的客户报告。导出 HTML、XLSX 或 DOCX 后会进入本地归档。" compact />
              )}
            </section>
            <section className="customer-report-signoff-list" data-customer-report-signoff-list="p3-06u-26h2u">
              <div className="customer-report-signoff-list-head">
                <div>
                  <span>最近确认记录</span>
                  <strong>{customerQualityReportSignoffs.data?.total ?? 0} 条</strong>
                </div>
                <small>{customerQualityReportSignoffs.status === "loading" ? "正在同步" : customerQualityReportSignoffs.message}</small>
              </div>
              {customerQualityReportSignoffs.status === "error" ? (
                <WorkspaceStateNotice kind="error" message={customerQualityReportSignoffs.message} compact />
              ) : customerQualityReportSignoffs.data && customerQualityReportSignoffs.data.items.length > 0 ? (
                <div className="customer-report-signoff-list-items">
                  {customerQualityReportSignoffs.data.items.slice(0, 5).map((item) => (
                    <article key={item.audit_event_id}>
                      <div>
                        <strong>{item.period} · {item.signoff_status_label}</strong>
                        <span>{item.confirmation_method_label} · {formatDateTime(item.recorded_at)}</span>
                      </div>
                      <p>{item.signer_display_name || "确认人已脱敏"}{item.signer_role ? ` · ${item.signer_role}` : ""}{item.signer_organization ? ` · ${item.signer_organization}` : ""}</p>
                      <small>{item.notes_recorded ? `已记录备注摘要，长度 ${item.notes_length} 字` : "未记录备注"} · 审计号 #{item.audit_event_id}</small>
                    </article>
                  ))}
                </div>
              ) : (
                <WorkspaceStateNotice kind="empty" message="当前还没有客户确认记录。记录后会进入本地审计留档。" compact />
              )}
            </section>
          </>
        ) : (
          <WorkspaceStateNotice kind="empty" message="正式登录后会生成客户可读质量报告。" compact />
        )}
      </section>

      <div className="quality-repair-map" aria-label="错因到知识修复闭环" data-quality-smoke="repair-map">
        <article className="quality-repair-score">
          <span>修复闭环</span>
          <strong>{repairAverage}%</strong>
          <small>按缺口草稿、引用覆盖、渠道异常、回归验证和发送门禁综合估算</small>
          <div className="quality-repair-score-bar" aria-hidden="true">
            <i style={{ width: `${repairAverage}%` }} />
          </div>
          <p>这是运营处理进度，不是完整准确率；准确率仍需要真实题库和人工事实性标签共同确认。</p>
        </article>
        <div className="quality-repair-path-list" role="list">
          {repairPaths.map((item) => (
            <a
              key={item.key}
              className={`quality-repair-path ${item.tone}`}
              href={item.href}
              data-quality-repair-key={item.key}
              data-quality-context-link="true"
            >
              <span className="quality-repair-path-head">
                <span>
                  <small>{item.owner}</small>
                  <strong>{item.label}</strong>
                </span>
                <b>{item.count}</b>
              </span>
              <p>{item.source}</p>
              <em>{item.evidence}</em>
              <span className="quality-repair-path-progress" aria-label={`${item.label} 闭环进度 ${item.progress}%`}>
                <i style={{ width: `${Math.max(6, item.progress)}%` }} />
                <b>{item.progress}%</b>
              </span>
              <span className="quality-repair-next">{item.next}</span>
            </a>
          ))}
        </div>
      </div>

      <div className="quality-metric-grid compact">
        <QualityMetric label="强证据命中" value={formatRate(strongEvidenceReviews, reviewItems.length)} note={`${strongEvidenceReviews}/${reviewItems.length || 0} 条人审样本`} />
        <QualityMetric label="引用覆盖" value={latestRun ? formatPercent(latestRun.citation_coverage) : "-"} note={latestRun ? `${latestRun.citation_covered_cases}/${latestRun.total_cases} 道题` : "等待题库运行"} />
        <QualityMetric label="转人工" value={formatRate(reviewItems.length, totalConversations)} note={`${reviewItems.length}/${totalConversations || 0} 条会话`} />
        <QualityMetric label="知识缺口" value={`${knowledgeGapCases + noKnowledgeReviews}`} note="缺口闭环 + 无知识人审样本" />
        <QualityMetric label="待确认草稿" value={`${pendingDrafts}`} note="人工批准后仍需发送前确认" />
        <QualityMetric label="失败复盘" value={`${failureReviews.length + blockedJobs}`} note="回执异常和队列阻断" />
        <QualityMetric label="高风险" value={`${highRiskReviews}`} note="赔付、法务、投诉或敏感问题" />
        <QualityMetric label="人工标签" value="未完成" note="缺少事实性标签，不报完整准确率" />
      </div>

      <div className="quality-bi-grid">
        <article className="quality-chart-card quality-pareto-card">
          <div className="section-title-row">
            <BarChart3 size={18} />
            <strong>错因排行</strong>
          </div>
          <div className="pareto-list" role="list">
            {rootCauses.map((item) => (
              <a key={item.key} className={`pareto-row ${item.tone}`} href={item.href}>
                <span className="pareto-label">
                  <strong>{item.label}</strong>
                  <small>{item.detail}</small>
                </span>
                <span className="pareto-track" aria-label={`${item.label} ${item.count} 个信号`}>
                  <i style={{ width: `${Math.max(6, issueTotal ? Math.round((item.count / issueTotal) * 100) : 0)}%` }} />
                </span>
                <span className="pareto-count">{item.count}</span>
              </a>
            ))}
          </div>
        </article>

        <article className="quality-chart-card">
          <div className="section-title-row">
            <Route size={18} />
            <strong>质量漏斗</strong>
          </div>
          <div className="quality-funnel" role="list">
            {funnelSteps.map((step) => (
              <a key={step.label} className="funnel-step" href={step.href}>
                <span>
                  <strong>{step.label}</strong>
                  <small>{step.note}</small>
                </span>
                <b>{step.count}</b>
                <i style={{ width: `${Math.max(6, Math.round((step.count / funnelMax) * 100))}%` }} />
              </a>
            ))}
          </div>
        </article>

        <article className="quality-chart-card">
          <div className="section-title-row">
            <Activity size={18} />
            <strong>题库趋势</strong>
          </div>
          <div className="quality-trend-bars" role="list" aria-label="题库回归趋势">
            {trendRuns.length > 0 ? trendRuns.map((run, index) => (
              <div key={`${run.id}-${index}`} className="trend-point">
                <span style={{ height: `${Math.max(8, Math.round(run.hit_rate * 100))}%` }} />
                <small>{formatDateTime(run.created_at)}</small>
                <strong>{formatPercent(run.hit_rate)}</strong>
              </div>
            )) : (
              <WorkspaceStateNotice
                kind="empty"
                message="尚未有题库运行。先在评测页运行固定题集，再回到这里观察趋势。"
                compact
              />
            )}
          </div>
          <p className="quality-card-note">
            {latestRun && previousRun
              ? `最近同题集命中率变化 ${formatSignedPercent(hitDelta ?? 0)}。仍需人工事实性标签确认答案是否正确。`
              : "缺少同题集上一轮对比，当前只展示最近检索质量信号。"}
          </p>
        </article>

        <article className="quality-chart-card">
          <div className="section-title-row">
            <Send size={18} />
            <strong>渠道异常分布</strong>
          </div>
          <div className="channel-stack-list" role="list">
            {channelRows.slice(0, 6).map((row) => {
              const totalSignals = row.total + row.reviews + row.failures + row.sla;
              return (
                <a key={row.channelName} className="channel-stack-row" href="#channels">
                  <span>
                    <strong>{formatChannelShortName(row.channelName)}</strong>
                    <small>会话 {row.total} · 人审 {row.reviews} · 异常 {row.failures} · 超时 {row.sla}</small>
                  </span>
                  <em aria-hidden="true">
                    <i className="stack-normal" style={{ width: `${Math.round((row.total / channelMax) * 100)}%` }} />
                    <i className="stack-warning" style={{ width: `${Math.round((row.reviews / channelMax) * 100)}%` }} />
                    <i className="stack-danger" style={{ width: `${Math.round(((row.failures + row.sla) / channelMax) * 100)}%` }} />
                  </em>
                  <b>{totalSignals}</b>
                </a>
              );
            })}
          </div>
        </article>

        <article className="quality-chart-card">
          <div className="section-title-row">
            <BookOpen size={18} />
            <strong>知识缺口热力</strong>
          </div>
          <div className="gap-heatmap" role="table" aria-label="知识缺口状态热力">
            <div className="gap-heatmap-head" role="row">
              <span role="columnheader">来源</span>
              {gapStatusLabels.map((status) => <span key={status.key} role="columnheader">{status.label}</span>)}
            </div>
            {gapSourceRows.map((row) => (
              <div key={row.key} className="gap-heatmap-row" role="row">
                <strong role="cell">{row.label}</strong>
                {row.cells.map((count, index) => (
                  <span key={`${row.key}-${gapStatusLabels[index].key}`} role="cell" className={count > 2 ? "hot" : count > 0 ? "warm" : ""}>
                    {count}
                  </span>
                ))}
              </div>
            ))}
          </div>
        </article>

        <article className="quality-chart-card">
          <div className="section-title-row">
            <ShieldCheck size={18} />
            <strong>人审矩阵</strong>
          </div>
          <div className="review-matrix" role="table" aria-label="人审风险和证据矩阵">
            <div className="review-matrix-head" role="row">
              <span role="columnheader">风险</span>
              <span role="columnheader">无知识</span>
              <span role="columnheader">弱证据</span>
              <span role="columnheader">可核对</span>
            </div>
            {matrixRows.map((row) => (
              <div key={row.key} className="review-matrix-row" role="row">
                <strong role="cell">{row.label}</strong>
                <span role="cell" className={row.noKnowledge > 0 ? "hot" : ""}>{row.noKnowledge}</span>
                <span role="cell" className={row.weak > 0 ? "warm" : ""}>{row.weak}</span>
                <span role="cell" className={row.strong > 0 ? "ok" : ""}>{row.strong}</span>
              </div>
            ))}
          </div>
        </article>
      </div>

      <div className="quality-drilldown-panel">
        <div className="section-title-row">
          <Search size={18} />
          <strong>样本下钻</strong>
        </div>
        <div className="quality-sample-grid">
          {drillSamples.length > 0 ? drillSamples.map((sample) => (
            <a key={sample.id} className={`quality-sample-card ${sample.tone}`} href={sample.href}>
              <span>{sample.source}</span>
              <strong>{sample.title}</strong>
              <p>{sample.excerpt}</p>
              <small>错因：{sample.cause}</small>
              <b>{sample.action}</b>
            </a>
          )) : (
            <WorkspaceStateNotice
              kind="empty"
              message="当前没有可下钻样本。正式环境需要接入真实会话、人审、缺口和题库运行。"
              compact
            />
          )}
        </div>
      </div>

      <div className="quality-repair-strip" aria-label="质量修复动作">
        {repairPaths.slice(0, 5).map((item) => (
          <a key={item.key} href={item.href}>
            <span>{item.label}</span>
            <strong>{item.next}</strong>
          </a>
        ))}
      </div>
    </section>
  );
}
