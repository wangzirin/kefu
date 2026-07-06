import { Activity, RefreshCw, ShieldCheck } from "lucide-react";
import type { ReactNode } from "react";

import { DataSourceBadge, EXTERNAL_WRITE_OFF_LABEL, PREVIEW_DATA_LABEL, REAL_DATA_LABEL } from "../common/WorkspaceState";

export type KnowledgeWorkspaceMode = "library" | "gaps" | "evals";

interface KnowledgeDocumentLike {
  id: number;
  status: string;
  ingestion_status: string;
}

interface KnowledgeGapLike {
  id: number;
  status: string;
  severity: string;
  gap_type: string;
  source_type: string;
  linked_knowledge_document_id: number | null;
  metadata?: Record<string, unknown>;
}

interface KnowledgeEvaluationRunLike {
  hit_rate: number;
  citation_coverage: number;
  expected_term_coverage: number;
  needs_review_cases: number;
  summary_payload: Record<string, unknown>;
  case_results: Array<{
    status: string;
    failure_reason: string;
    citation_present: boolean;
    expected_terms_found: boolean;
  }>;
}

interface KnowledgeDocumentStateLike {
  status: string;
  message: string;
  businessObjects: unknown[];
  objectCardsByObject: Record<number, unknown[]>;
  documents: KnowledgeDocumentLike[];
  publicationsByDocument: Record<number, Array<{ status: string; created_at: string | null }>>;
}

interface KnowledgeGapStateLike {
  status: string;
  message: string;
  data: {
    items: KnowledgeGapLike[];
    total: number;
  };
  lastSync: {
    created_count: number;
    existing_count: number;
    scanned_count: number;
  } | null;
}

interface KnowledgeEvaluationStateLike {
  status: string;
  message: string;
  sets: unknown[];
  lastRun: KnowledgeEvaluationRunLike | null;
}

interface KnowledgeMeshNodeLike {
  key: string;
  label: string;
  status: string;
  total_count: number;
  healthy_count: number;
  risk_count: number;
  evidence: string;
  next_action: string;
}

interface KnowledgeMeshStepLike {
  key: string;
  label: string;
  status: string;
  observed_count: number;
  evidence: string;
  blocker: string;
}

interface KnowledgeMemoryMeshOverviewLike {
  status: string;
  summary: string;
  nodes: KnowledgeMeshNodeLike[];
  provenance_steps: KnowledgeMeshStepLike[];
  source_authority: Record<string, unknown>;
  quality_loop: Record<string, unknown>;
  readiness: Record<string, unknown>;
  boundaries: Record<string, unknown>;
}

interface KnowledgeMemoryMeshStateLike {
  status: string;
  message: string;
  data: KnowledgeMemoryMeshOverviewLike | null;
}

interface KnowledgeWorkspacePageProps {
  mode: KnowledgeWorkspaceMode;
  documentState: KnowledgeDocumentStateLike;
  gapState: KnowledgeGapStateLike;
  evaluationState: KnowledgeEvaluationStateLike;
  meshState: KnowledgeMemoryMeshStateLike;
  hasToken: boolean;
  canManage: boolean;
  onRefreshMesh: () => void;
  children: ReactNode;
}

const MODE_COPY: Record<
  KnowledgeWorkspaceMode,
  {
    eyebrow: string;
    title: string;
    description: string;
  }
> = {
  library: {
    eyebrow: "知识库运营",
    title: "维护可被客服引用的业务知识",
    description: "管理业务对象、问答卡、文档片段、引用来源、发布记录和回滚状态。这里负责把知识写对、写清楚、可追溯。"
  },
  gaps: {
    eyebrow: "知识缺口",
    title: "把错因变成可修复的知识任务",
    description: "集中处理无命中、低置信、缺引用、人工驳回和评测失败问题。这里负责找出为什么答不好，并推动补知识、入回归、发布验证。"
  },
  evals: {
    eyebrow: "知识评测",
    title: "用固定题集守住发布质量",
    description: "跟踪检索命中率、引用覆盖率、期望词覆盖率和发布前后变化。这里评估的是检索与引用质量，不等同完整客服事实准确率。"
  }
};

export function KnowledgeWorkspacePage({
  mode,
  documentState,
  gapState,
  evaluationState,
  meshState,
  hasToken,
  canManage,
  onRefreshMesh,
  children
}: KnowledgeWorkspacePageProps) {
  const copy = MODE_COPY[mode];
  const metrics = buildKnowledgePageMetrics(mode, documentState, gapState, evaluationState);
  const causeCards = buildKnowledgeCauseCards(gapState);
  const latestRun = evaluationState.lastRun;
  const emptyText = getKnowledgeEmptyText(mode, documentState, gapState, evaluationState, hasToken);

  return (
    <section
      className={`workspace-page-grid stacked knowledge-page-shell knowledge-page-${mode}`}
      data-knowledge-page-shell={mode}
      aria-label={copy.eyebrow}
    >
      <section className="knowledge-page-command" data-knowledge-primary={mode}>
        <div className="knowledge-page-command-copy">
          <span className="section-kicker">{copy.eyebrow}</span>
          <h2>{copy.title}</h2>
          <p>{copy.description}</p>
        </div>
        <div className="knowledge-page-state-stack">
          <DataSourceBadge
            mode={hasToken ? "real" : "demo"}
            label={hasToken ? REAL_DATA_LABEL : PREVIEW_DATA_LABEL}
            detail={hasToken ? "优先读取服务端知识、缺口和评测数据" : "仅展示本地初始化数据和工作流结构"}
          />
          <DataSourceBadge
            mode={canManage ? "real" : "off"}
            label={canManage ? "可维护" : "只读"}
            detail={canManage ? "允许创建、同步、发布和回归" : "当前账号不能修改知识数据"}
          />
          <DataSourceBadge
            mode="off"
            label={EXTERNAL_WRITE_OFF_LABEL}
            detail="知识发布只影响内部检索，不自动向外部平台回复"
          />
        </div>
      </section>

      <section className="knowledge-page-metric-strip" aria-label={`${copy.eyebrow}核心指标`}>
        {metrics.map((metric) => (
          <article key={metric.label} className={`knowledge-page-metric ${metric.tone}`}>
            <span>{metric.label}</span>
            <strong>{metric.value}</strong>
            <small>{metric.note}</small>
          </article>
        ))}
      </section>

      <KnowledgeMemoryMeshOverviewCard state={meshState} onRefresh={onRefreshMesh} />

      {mode === "gaps" ? (
        <section className="knowledge-page-cause-grid" data-knowledge-gap-cause-map="p3-06u-26d" aria-label="知识缺口错因地图">
          {causeCards.map((card) => (
            <article key={card.label} className={`knowledge-page-cause ${card.tone}`}>
              <Activity size={17} />
              <div>
                <strong>{card.label}</strong>
                <span>{card.count} 条</span>
                <small>{card.action}</small>
              </div>
            </article>
          ))}
        </section>
      ) : null}

      {mode === "evals" ? (
        <section className="knowledge-page-regression-compare" data-knowledge-regression-compare="p3-06u-26d">
          <div>
            <span>发布前后对比入口</span>
            <strong>{latestRun ? `最近题集命中 ${formatPercent(latestRun.hit_rate)}` : "等待运行固定题集"}</strong>
            <small>
              {latestRun
                ? `引用覆盖 ${formatPercent(latestRun.citation_coverage)} · 期望词覆盖 ${formatPercent(latestRun.expected_term_coverage)} · 需复核 ${latestRun.needs_review_cases}`
                : "当前页面只评估检索、引用和期望词覆盖，完整客服事实准确率需要结合最终回复、人工事实性标签和线上回执再确认。"}
            </small>
          </div>
          <a className="ghost-button compact" href="#gaps">
            <ShieldCheck size={16} />
            失败题转缺口
          </a>
        </section>
      ) : null}

      {emptyText ? (
        <div className="knowledge-page-empty" data-knowledge-page-empty={mode}>
          <strong>{emptyText.title}</strong>
          <small>{emptyText.message}</small>
        </div>
      ) : null}

      {children}
    </section>
  );
}

function KnowledgeMemoryMeshOverviewCard({
  state,
  onRefresh
}: {
  state: KnowledgeMemoryMeshStateLike;
  onRefresh: () => void;
}) {
  const overview = state.data;
  const readiness = overview?.readiness ?? {};
  const fullMeshReady = readBooleanPayload(readiness, "full_memory_mesh_ready") ?? false;
  const citationReady = readBooleanPayload(readiness, "reply_citation_trace_ready") ?? false;
  const finalQualityReady = readBooleanPayload(readiness, "final_answer_quality_ready") ?? false;
  const materialReady = readBooleanPayload(readiness, "material_batch_node_ready") ?? false;
  const liveSendReady = readBooleanPayload(readiness, "real_platform_send_ready") ?? false;

  return (
    <section className="knowledge-memory-mesh" data-knowledge-memory-mesh="nc4">
      <div className="knowledge-memory-mesh-heading">
        <div>
          <span className="section-kicker">知识网络总览</span>
          <h3>资料、知识、引用和质量复盘的一张证据链</h3>
          <p>
            {overview
              ? overview.summary
              : state.status === "error"
                ? state.message
                : "登录后读取本地知识证据链；这里不包含外部平台真实发送结果。"}
          </p>
        </div>
        <button type="button" className="ghost-button compact" onClick={onRefresh}>
          <RefreshCw size={15} />
          刷新
        </button>
      </div>

      <div className="knowledge-memory-mesh-state" aria-label="知识网络关键边界">
        <span className={materialReady ? "ready" : "waiting"}>资料批次 {materialReady ? "已就绪" : "待补齐"}</span>
        <span className={citationReady ? "ready" : "waiting"}>引用链路 {citationReady ? "可追溯" : "待形成"}</span>
        <span className={finalQualityReady ? "ready" : "waiting"}>答案质量 {finalQualityReady ? "已评测" : "待人工标签"}</span>
        <span className={fullMeshReady ? "ready" : "waiting"}>完整网络 {fullMeshReady ? "候选可用" : "尚未完整"}</span>
        <span className={liveSendReady ? "ready" : "off"}>真实外发 {liveSendReady ? "已开启" : "关闭"}</span>
      </div>

      {overview ? (
        <>
          <div className="knowledge-memory-node-grid" aria-label="知识网络节点">
            {overview.nodes.map((node) => (
              <article key={node.key} className={`knowledge-memory-node ${node.status}`}>
                <span>{node.label}</span>
                <strong>{node.total_count}</strong>
                <small>{node.evidence}</small>
                <em>
                  健康 {node.healthy_count} · 风险 {node.risk_count}
                </em>
                <p>{node.next_action}</p>
              </article>
            ))}
          </div>

          <div className="knowledge-memory-chain" aria-label="回复证据链">
            {overview.provenance_steps.map((step) => (
              <article key={step.key} className={`knowledge-memory-step ${step.status}`}>
                <span>{step.label}</span>
                <strong>{step.observed_count}</strong>
                <small>{step.evidence}</small>
                {step.blocker ? <em>{step.blocker}</em> : null}
              </article>
            ))}
          </div>
        </>
      ) : (
        <div className="knowledge-memory-placeholder">
          <strong>{state.status === "loading" ? "正在读取知识网络" : "等待知识网络数据"}</strong>
          <small>刷新后会显示资料批次、知识卡片、业务对象、问题样本、质量标签和引用链路。</small>
        </div>
      )}
    </section>
  );
}

function buildKnowledgePageMetrics(
  mode: KnowledgeWorkspaceMode,
  documentState: KnowledgeDocumentStateLike,
  gapState: KnowledgeGapStateLike,
  evaluationState: KnowledgeEvaluationStateLike
) {
  const documents = documentState.documents;
  const objectCardCount = Object.values(documentState.objectCardsByObject).reduce((total, cards) => total + cards.length, 0);
  const draftDocuments = documents.filter((item) => item.status === "draft").length;
  const publishedRecords = Object.values(documentState.publicationsByDocument)
    .flat()
    .filter((item) => item.status === "published").length;
  const gaps = gapState.data.items;
  const openGaps = gaps.filter((item) => ["open", "triaged", "in_progress"].includes(item.status));
  const severeGaps = gaps.filter((item) => ["high", "critical"].includes(item.severity));
  const missingDraft = openGaps.filter((item) => !item.linked_knowledge_document_id);
  const evalFailureGaps = gaps.filter((item) => item.source_type === "evaluation_run");
  const latestRun = evaluationState.lastRun;

  if (mode === "library") {
    return [
      { label: "业务对象", value: `${documentState.businessObjects.length}`, note: "商品、服务、套餐等对象", tone: "normal" },
      { label: "问答卡", value: `${objectCardCount}`, note: "对象级标准问答", tone: objectCardCount > 0 ? "success" : "warning" },
      { label: "文档", value: `${documents.length}`, note: `${draftDocuments} 份草稿待审核`, tone: draftDocuments > 0 ? "warning" : "normal" },
      { label: "发布记录", value: `${publishedRecords}`, note: "可回滚和可审计", tone: publishedRecords > 0 ? "success" : "normal" }
    ] as const;
  }

  if (mode === "gaps") {
    return [
      { label: "缺口总量", value: `${gapState.data.total}`, note: "服务端当前总量", tone: gapState.data.total > 0 ? "warning" : "success" },
      { label: "待处理", value: `${openGaps.length}`, note: "开放、分诊、处理中", tone: openGaps.length > 0 ? "warning" : "success" },
      { label: "高严重度", value: `${severeGaps.length}`, note: "高风险优先修复", tone: severeGaps.length > 0 ? "urgent" : "success" },
      { label: "待生成草稿", value: `${missingDraft.length}`, note: "需要补知识文档", tone: missingDraft.length > 0 ? "warning" : "success" }
    ] as const;
  }

  const factualityMeasured = readBooleanPayload(latestRun?.summary_payload, "final_answer_factuality_measured") ?? false;
  const citationSufficiencyRate = readNumberPayload(latestRun?.summary_payload, "citation_sufficiency_rate");
  const forbiddenViolationCases = readNumberPayload(latestRun?.summary_payload, "forbidden_commitment_violation_cases");
  const handoffCorrectness = readNumberPayload(latestRun?.summary_payload, "handoff_correctness") ?? readNumberPayload(latestRun?.summary_payload, "human_review_correctness");
  return [
    { label: "答案事实性", value: latestRun ? (factualityMeasured ? "已评" : "未评") : "待运行", note: "最终答案未生成；检索命中，不是完整准确率", tone: factualityMeasured ? "success" : "warning" },
    { label: "引用充分", value: latestRun ? formatPercent(citationSufficiencyRate) : "待运行", note: "证据是否足够支撑回复", tone: citationSufficiencyRate !== null && citationSufficiencyRate >= 0.75 ? "success" : "warning" },
    { label: "禁用承诺", value: latestRun ? `${forbiddenViolationCases ?? 0}` : "待运行", note: "命中禁用承诺需复核", tone: latestRun && (forbiddenViolationCases ?? 0) === 0 ? "success" : "warning" },
    { label: "转人工正确", value: latestRun ? formatPercent(handoffCorrectness) : "待运行", note: "风险/低置信门禁判断", tone: handoffCorrectness !== null && handoffCorrectness >= 0.75 ? "success" : "warning" }
  ] as const;
}

function buildKnowledgeCauseCards(gapState: KnowledgeGapStateLike) {
  const gaps = gapState.data.items;
  const cards = [
    {
      label: "无知识命中",
      count: countBy(gaps, (gap) => gap.gap_type.includes("no_hit") || gap.gap_type.includes("missing")),
      action: "补业务对象、标准问答和引用来源",
      tone: "warning"
    },
    {
      label: "引用不足",
      count: countBy(gaps, (gap) => gap.gap_type.includes("citation") || gap.gap_type.includes("evidence")),
      action: "补来源、片段和可追溯依据",
      tone: "normal"
    },
    {
      label: "期望词缺失",
      count: countBy(gaps, (gap) => gap.gap_type.includes("term") || gap.gap_type.includes("expected")),
      action: "补必须包含事实点和禁用承诺",
      tone: "normal"
    },
    {
      label: "人工驳回",
      count: countBy(gaps, (gap) => gap.source_type === "human_review"),
      action: "复盘坐席驳回原因并修订答案",
      tone: "urgent"
    }
  ] as const;
  return cards.map((card) => ({ ...card, tone: card.count > 0 ? card.tone : "success" }));
}

function getKnowledgeEmptyText(
  mode: KnowledgeWorkspaceMode,
  documentState: KnowledgeDocumentStateLike,
  gapState: KnowledgeGapStateLike,
  evaluationState: KnowledgeEvaluationStateLike,
  hasToken: boolean
) {
  if (!hasToken) {
    return {
      title: "请先登录本地工作台",
      message: "登录租户账号后即可读取服务端知识、缺口和评测数据。"
    };
  }
  if (mode === "library" && documentState.documents.length === 0 && documentState.businessObjects.length === 0) {
    return { title: "知识库尚未初始化", message: "先导入 50-100 条真实脱敏题库和业务对象知识，再进入评测与发布。" };
  }
  if (mode === "gaps" && gapState.data.total === 0) {
    return { title: "当前没有服务端知识缺口", message: "可以从质量复盘、人审驳回和评测失败同步新的缺口。" };
  }
  if (mode === "evals" && evaluationState.sets.length === 0) {
    return { title: "还没有固定评测集", message: "先创建真实客户问题题集；当前知识评测是检索评测，不是完整客服准确率。" };
  }
  return null;
}

function countBy<T>(items: T[], predicate: (item: T) => boolean) {
  return items.reduce((total, item) => total + (predicate(item) ? 1 : 0), 0);
}

function formatPercent(value: number | null) {
  if (value === null || Number.isNaN(value)) {
    return "-";
  }
  return `${Math.round(value * 100)}%`;
}

function readNumberPayload(payload: Record<string, unknown> | null | undefined, key: string): number | null {
  if (!payload) {
    return null;
  }
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

function readBooleanPayload(payload: Record<string, unknown> | null | undefined, key: string): boolean | null {
  if (!payload) {
    return null;
  }
  const value = payload[key];
  return typeof value === "boolean" ? value : null;
}
