import { AlertTriangle, Bot, Clipboard, PlayCircle, ShieldCheck } from "lucide-react";
import { useMemo, useState } from "react";

import {
  runRpaCopilotStrategyDryRun,
  type RpaCopilotDryRunResponse,
  type RpaCopilotDryRunRequest
} from "../../api/client";
import { DisabledReason, PanelStateNotice, WorkspaceStateNotice } from "../common/WorkspaceState";


type LabStatus = "idle" | "loading" | "ready" | "error";

const SAMPLE_MESSAGES = [
  "你好，这个订单一般多久发货？",
  "收到后发现质量问题，我要退款，不处理我就投诉。",
  "这个产品能不能放在户外长期暴晒？",
  "能不能再便宜一点，给我最低价我马上拍。",
  "我拍了照片，收到的外包装破损，里面也有划痕，怎么售后？"
];

const CHANNEL_OPTIONS = [
  { value: "manual_import_research", label: "人工导入" },
  { value: "qianniu_research", label: "千牛研究" },
  { value: "pdd_research", label: "拼多多研究" },
  { value: "douyin_research", label: "抖音研究" },
  { value: "jd_research", label: "京东研究" }
];

export function RpaCopilotLabPanel({
  token,
  canRun
}: {
  token?: string;
  canRun: boolean;
}) {
  const [customerName, setCustomerName] = useState("人工导入客户");
  const [channel, setChannel] = useState("manual_import_research");
  const [message, setMessage] = useState(SAMPLE_MESSAGES[0]);
  const [hasAttachment, setHasAttachment] = useState(false);
  const [status, setStatus] = useState<LabStatus>("idle");
  const [statusMessage, setStatusMessage] = useState("");
  const [result, setResult] = useState<RpaCopilotDryRunResponse | null>(null);

  const disabledReason = useMemo(() => {
    if (!token) {
      return "需要正式登录后才能调用后端策略试算接口。";
    }
    if (!canRun) {
      return "当前账号没有会话读取权限，不能运行 RPA 副驾驶试验。";
    }
    if (!message.trim()) {
      return "请先粘贴一条客户消息。";
    }
    return "";
  }, [canRun, message, token]);

  async function runDryRun() {
    if (!token || disabledReason) {
      return;
    }
    setStatus("loading");
    setStatusMessage("");
    try {
      const payload: RpaCopilotDryRunRequest = {
        channel,
        customer_name: customerName.trim() || "人工导入客户",
        text: message.trim(),
        attachments: hasAttachment ? ["manual-attachment://operator-flag"] : [],
        metadata: {
          lab: "p3_06u_12b",
          entrypoint: "frontend_rpa_copilot_lab"
        }
      };
      const nextResult = await runRpaCopilotStrategyDryRun(payload, token);
      setResult(nextResult);
      setStatus("ready");
      setStatusMessage("策略试算完成。");
    } catch (error) {
      setStatus("error");
      setStatusMessage(error instanceof Error ? error.message : "策略试算失败");
    }
  }

  async function copyDraft() {
    if (!result?.draft.text) {
      return;
    }
    await navigator.clipboard.writeText(result.draft.text);
    setStatusMessage("草稿已复制。");
  }

  return (
    <section className="rpa-lab-shell" data-rpa-lab="p3-06u-12b">
      <WorkspaceStateNotice
        kind="external_write_off"
        title="内部实验入口"
        message="本页只做人工粘贴消息后的回复策略试算；不读取平台账号、不保存客户消息、不点击发送。"
      />

      <div className="rpa-boundary-strip" data-rpa-draft-only-boundary="p3-06u-26g" aria-label="RPA draft-only 边界">
        <ShieldCheck size={17} />
        <strong>RPA 研究线：draft-only</strong>
        <span>只允许读取页面上下文、生成草稿、填框和证据采集；RPA 不进入正式默认交付链，真实外发继续关闭。</span>
      </div>

      <section className="rpa-lab-grid">
        <article className="panel rpa-lab-input">
          <div className="panel-heading">
            <div>
              <h2>RPA 副驾驶试验</h2>
              <p>把一条客户消息粘贴进来，查看草稿、引用、转人工原因和下一步动作。</p>
            </div>
            <Bot size={20} />
          </div>
          <div className="rpa-lab-form">
            <label>
              <span>客户名称</span>
              <input value={customerName} onChange={(event) => setCustomerName(event.target.value)} />
            </label>
            <label>
              <span>研究渠道</span>
              <select value={channel} onChange={(event) => setChannel(event.target.value)}>
                {CHANNEL_OPTIONS.map((option) => (
                  <option value={option.value} key={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>
            <label className="rpa-lab-message">
              <span>客户消息</span>
              <textarea value={message} onChange={(event) => setMessage(event.target.value)} rows={8} />
            </label>
            <label className="rpa-lab-toggle">
              <input
                type="checkbox"
                checked={hasAttachment}
                onChange={(event) => setHasAttachment(event.target.checked)}
              />
              <span>包含图片或视频附件</span>
            </label>
            <div className="rpa-lab-samples">
              {SAMPLE_MESSAGES.map((sample) => (
                <button type="button" className="ghost-action" onClick={() => setMessage(sample)} key={sample}>
                  {sample.slice(0, 14)}
                </button>
              ))}
            </div>
            <button type="button" className="primary-action" onClick={() => void runDryRun()} disabled={Boolean(disabledReason) || status === "loading"}>
              <PlayCircle size={17} />
              {status === "loading" ? "试算中" : "运行策略试算"}
            </button>
            <DisabledReason show={Boolean(disabledReason)} reason={disabledReason} />
          </div>
        </article>

        <article className="panel rpa-lab-result">
          <div className="panel-heading">
            <div>
              <h2>策略结果</h2>
              <p>核心看 `delivery_mode`，它决定填草稿、转人工还是补知识。</p>
            </div>
            <ShieldCheck size={20} />
          </div>
          <PanelStateNotice status={status} message={statusMessage} loadingMessage="正在调用后端 dry-run 策略服务。" />
          {result ? (
            <RpaCopilotResult result={result} onCopyDraft={() => void copyDraft()} />
          ) : (
            <div className="rpa-lab-empty">
              <AlertTriangle size={18} />
              <span>等待第一条策略试算。</span>
            </div>
          )}
        </article>
      </section>
    </section>
  );
}

function RpaCopilotResult({
  result,
  onCopyDraft
}: {
  result: RpaCopilotDryRunResponse;
  onCopyDraft: () => void;
}) {
  return (
    <div className="rpa-lab-result-stack">
      <div className="rpa-strategy-card">
        <span>{formatDeliveryMode(result.reply_strategy.delivery_mode)}</span>
        <strong>{formatIntent(result.reply_strategy.intent)}</strong>
        <p>{result.reply_strategy.customer_visible_policy}</p>
      </div>
      <div className="rpa-lab-metrics">
        <Metric label="回答模式" value={formatAnswerMode(result.reply_strategy.answer_mode)} />
        <Metric label="下一步" value={formatNextAction(result.reply_strategy.next_best_action)} />
        <Metric label="置信度" value={`${Math.round(result.draft.confidence * 100)}%`} />
        <Metric label="引用数" value={`${result.draft.citations.length}`} />
      </div>
      <section className="rpa-lab-draft">
        <div>
          <strong>回复草稿</strong>
          <button type="button" className="ghost-action" onClick={onCopyDraft}>
            <Clipboard size={15} />
            复制
          </button>
        </div>
        <p>{result.draft.text}</p>
      </section>
      <section className="rpa-lab-detail-grid">
        <DetailList title="风控原因" items={result.guardrail.reasons.map(formatGuardrailReason)} empty="未触发强制人工" />
        <DetailList title="质量信号" items={result.reply_strategy.quality_signals.map(formatQualitySignal)} empty="暂无质量信号" />
        <DetailList title="引用来源" items={result.draft.citations} empty="未命中引用" />
        <DetailList title="动作计划" items={result.actions.map((action) => formatActionKind(action.kind))} empty="暂无动作" />
      </section>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function DetailList({ title, items, empty }: { title: string; items: string[]; empty: string }) {
  return (
    <div className="rpa-lab-detail">
      <strong>{title}</strong>
      {(items.length ? items : [empty]).map((item) => (
        <span key={item}>{item}</span>
      ))}
    </div>
  );
}

function formatDeliveryMode(value: string) {
  const labels: Record<string, string> = {
    fill_draft_only: "填入草稿",
    human_takeover: "人工接管",
    record_gap: "补知识"
  };
  return labels[value] ?? value;
}

function formatIntent(value: string) {
  const labels: Record<string, string> = {
    shipping_status_or_policy: "物流/发货咨询",
    invoice_request: "发票咨询",
    warranty_or_aftercare: "质保/售后说明",
    price_or_promotion: "价格/活动咨询",
    after_sales_risk: "售后风险",
    policy_or_risk_review: "政策风险复核",
    knowledge_gap_or_uncovered_question: "知识缺口",
    standard_service_question: "标准服务问题"
  };
  return labels[value] ?? value;
}

function formatAnswerMode(value: string) {
  const labels: Record<string, string> = {
    knowledge_draft_with_citation: "知识草稿",
    human_handoff_draft: "接管草稿",
    knowledge_gap_handoff: "缺口接管"
  };
  return labels[value] ?? value;
}

function formatNextAction(value: string) {
  const labels: Record<string, string> = {
    operator_review_and_send: "人工审核发送",
    collect_evidence_and_handoff: "收集证据后接管",
    handoff_with_draft_and_context: "带草稿交接",
    record_knowledge_gap_and_handoff: "记录缺口并接管"
  };
  return labels[value] ?? value;
}

function formatGuardrailReason(value: string) {
  const labels: Record<string, string> = {
    low_confidence: "低置信",
    missing_knowledge: "知识缺失",
    risk_term: "风险词",
    knowledge_card_requires_human: "知识卡要求人工"
  };
  return labels[value] ?? value;
}

function formatQualitySignal(value: string) {
  if (value.startsWith("top_score=")) {
    return `最高命中 ${value.replace("top_score=", "")}`;
  }
  if (value.startsWith("guardrail:")) {
    return `风控：${formatGuardrailReason(value.replace("guardrail:", ""))}`;
  }
  const labels: Record<string, string> = {
    has_knowledge_citation: "有知识引用",
    no_knowledge_hit: "未命中知识",
    has_attachment: "包含附件"
  };
  return labels[value] ?? value;
}

function formatActionKind(value: string) {
  const labels: Record<string, string> = {
    observe_message: "观察消息",
    capture_evidence: "保存证据快照",
    fill_reply_box: "填入回复框",
    mark_needs_human: "标记人工接管",
    record_knowledge_gap: "记录知识缺口"
  };
  return labels[value] ?? value;
}
