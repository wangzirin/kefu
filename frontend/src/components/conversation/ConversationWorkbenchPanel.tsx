import {
  Bot,
  MessageSquare,
  Power,
  RefreshCw,
  Search,
  Send,
  UserRound,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import {
  type ConversationDetail,
  type ConversationInboxItem,
  type ConversationInboxList,
  type ConversationWorkflowActionName,
  type DeliveryFailureReview,
  type HumanReviewInboxItem,
  type MessageRead,
  type OutboxDeliveryJob,
  type OutboxDraft,
  type ReplyDecision,
  type UserPublicProfile
} from "../../api/client";
type ConversationInboxState =
  | { status: "idle"; message: string; data: ConversationInboxList }
  | { status: "loading"; data: ConversationInboxList }
  | { status: "ready"; data: ConversationInboxList }
  | { status: "error"; message: string; data: ConversationInboxList };

type WorkbenchQueueKey =
  | "all"
  | "mine"
  | "needs_review";

interface WorkbenchQueueDefinition {
  key: WorkbenchQueueKey;
  label: string;
  count: number;
  note: string;
  tone: "urgent" | "warning" | "normal" | "success";
}

interface ConversationTimelineEvent {
  id: string;
  kind: "customer" | "agent" | "ai" | "review" | "outbox" | "delivery" | "failure" | "system";
  title: string;
  text: string;
  meta: string;
  href?: string;
}

export interface ChannelIdentitySummary {
  channelId: number;
  platform: string;
  accountName: string;
  storeName: string;
  providerMode: string;
  authorizationStatus: string;
  replyMode: string;
  healthLabel: string;
  lastSyncLabel: string;
}

export interface WorkbenchColleague {
  id: number;
  name: string;
  email?: string;
  role: string;
  status: string;
  activeChats: number;
  avatarDataUrl?: string;
  publicProfile?: Partial<UserPublicProfile>;
}

export interface ConversationWorkbenchPanelProps {
  state: ConversationInboxState;
  reviewItems: HumanReviewInboxItem[];
  replyDecisions: ReplyDecision[];
  replyDecisionStatus: "idle" | "loading" | "ready" | "error";
  outboxDrafts: OutboxDraft[];
  failureReviews: DeliveryFailureReview[];
  deliveryJobs: OutboxDeliveryJob[];
  selectedConversationId: number | null;
  conversationDetail: ConversationDetail | null;
  conversationDetailStatus: "idle" | "loading" | "ready" | "error";
  conversationDetailMessage: string;
  localReplyState: {
    status: "idle" | "sending" | "sent" | "error";
    conversationId: number | null;
    message: string;
  };
  hasToken: boolean;
  currentUserId: number | null;
  canManageConversations: boolean;
  canApproveReviewDraft: boolean;
  canConfirmOutboxDraft: boolean;
  channelIdentities?: Record<number, ChannelIdentitySummary>;
  colleagues?: WorkbenchColleague[];
  targetQueue?: string;
  targetChannelId?: number | null;
  onRefresh: () => void;
  onCreateSafeTestConversation?: () => void;
  onSelectConversation: (conversationId: number) => void;
  onSendLocalReply: (item: ConversationInboxItem, content: string) => void;
  onWorkflowAction: (
    item: ConversationInboxItem,
    action: ConversationWorkflowActionName,
    note?: string,
    targetUserId?: number | null,
    targetTeamId?: number | null
  ) => void;
  onApproveReviewDraft: (item: HumanReviewInboxItem, finalReply: string, resolutionNote: string) => void;
  onConfirmOutboxDraft: (draftId: number) => void;
}

export function ConversationWorkbenchPanel({
  state,
  reviewItems,
  replyDecisions,
  replyDecisionStatus,
  outboxDrafts,
  failureReviews,
  deliveryJobs,
  selectedConversationId,
  conversationDetail,
  conversationDetailStatus,
  conversationDetailMessage,
  localReplyState,
  hasToken,
  currentUserId,
  canManageConversations,
  canApproveReviewDraft,
  canConfirmOutboxDraft,
  channelIdentities = {},
  colleagues = [],
  targetQueue,
  targetChannelId = null,
  onRefresh,
  onCreateSafeTestConversation,
  onSelectConversation,
  onSendLocalReply,
  onWorkflowAction,
  onApproveReviewDraft,
  onConfirmOutboxDraft
}: ConversationWorkbenchPanelProps) {
  const [activeQueue, setActiveQueue] = useState<WorkbenchQueueKey>("all");
  const [editableDraft, setEditableDraft] = useState("");
  const [conversationSearch, setConversationSearch] = useState("");
  const [quickReplyTab, setQuickReplyTab] = useState<"personal" | "customer" | "custom">("personal");
  const [isTransferOpen, setIsTransferOpen] = useState(false);
  const [transferTargetUserId, setTransferTargetUserId] = useState("");
  const [transferNote, setTransferNote] = useState("");
  const [workflowNotice, setWorkflowNotice] = useState("");
  const validTargetQueue = normalizeWorkbenchQueueKey(targetQueue);

  const conversations = state.data.items;
  const scopedConversations = useMemo(
    () =>
      (targetChannelId === null ? conversations : conversations.filter((item) => item.channel_id === targetChannelId))
        .filter((item) => !["closed", "resolved"].includes(item.status)),
    [conversations, targetChannelId]
  );
  const searchedConversations = useMemo(() => {
    const keyword = conversationSearch.trim().toLowerCase();
    if (!keyword) return scopedConversations;
    return scopedConversations.filter((item) => {
      const identity = getChannelIdentity(item, channelIdentities);
      return [
        item.contact_display_name,
        item.subject,
        item.last_message_preview,
        item.channel_name,
        item.channel_type,
        identity.accountName,
        identity.storeName
      ]
        .filter((value): value is string => Boolean(value))
        .some((value) => value.toLowerCase().includes(keyword));
    });
  }, [channelIdentities, conversationSearch, scopedConversations]);
  const reviewByConversation = useMemo(
    () => new Map(reviewItems.map((item) => [item.conversation_id, item])),
    [reviewItems]
  );
  const replyDecisionByConversation = useMemo(() => {
    const result = new Map<number, ReplyDecision>();
    replyDecisions.forEach((decision) => {
      const current = result.get(decision.conversation_id);
      if (!current || compareDecisionFreshness(decision, current) > 0) {
        result.set(decision.conversation_id, decision);
      }
    });
    return result;
  }, [replyDecisions]);
  const draftsByConversation = useMemo(() => {
    const result = new Map<number, OutboxDraft[]>();
    outboxDrafts.forEach((draft) => {
      const drafts = result.get(draft.conversation_id) ?? [];
      drafts.push(draft);
      result.set(draft.conversation_id, drafts);
    });
    return result;
  }, [outboxDrafts]);
  const failuresByDraft = useMemo(() => {
    const result = new Map<number, DeliveryFailureReview[]>();
    failureReviews.forEach((failure) => {
      if (!failure.outbox_draft_id) {
        return;
      }
      const failures = result.get(failure.outbox_draft_id) ?? [];
      failures.push(failure);
      result.set(failure.outbox_draft_id, failures);
    });
    return result;
  }, [failureReviews]);
  const jobsByDraft = useMemo(() => {
    const result = new Map<number, OutboxDeliveryJob[]>();
    deliveryJobs.forEach((job) => {
      const jobs = result.get(job.outbox_draft_id) ?? [];
      jobs.push(job);
      result.set(job.outbox_draft_id, jobs);
    });
    return result;
  }, [deliveryJobs]);

  const hasOpenFailure = (item: ConversationInboxItem) => {
    const drafts = draftsByConversation.get(item.id) ?? [];
    return item.delivery_failure_open_count > 0 || drafts.some((draft) => (failuresByDraft.get(draft.id) ?? []).length > 0);
  };
  const hasKnowledgeGapSignal = (item: ConversationInboxItem) => {
    const review = reviewByConversation.get(item.id);
    const decision = replyDecisionByConversation.get(item.id);
    return (
      decision?.state === "knowledge_gap" ||
      item.next_action.includes("知识") ||
      review?.reason.includes("无知识") ||
      review?.evidence.retrieved_knowledge_count === 0 ||
      (review?.evidence.confidence ?? 1) < 0.45
    );
  };
  const hasManualGateSignal = (item: ConversationInboxItem) => {
    const decision = replyDecisionByConversation.get(item.id);
    return (
      item.human_review_open_count > 0 ||
      decision?.state === "manual_gate_required" ||
      decision?.state === "blocked_by_policy" ||
      decision?.state === "knowledge_gap" ||
      item.assigned_user_id === null ||
      item.sla_status === "breached" ||
      ["critical", "high"].includes(item.priority) ||
      hasKnowledgeGapSignal(item) ||
      hasOpenFailure(item)
    );
  };
  const queueDefinitions: WorkbenchQueueDefinition[] = [
    {
      key: "all",
      label: "全部",
      count: searchedConversations.length,
      note: "当前页会话",
      tone: searchedConversations.length > 0 ? "normal" : "success"
    },
    {
      key: "mine",
      label: "我的",
      count: searchedConversations.filter((item) => item.assigned_user_id === currentUserId && currentUserId !== null).length,
      note: "已分配给当前坐席",
      tone: "normal"
    },
    {
      key: "needs_review",
      label: "转人工",
      count: searchedConversations.filter(hasManualGateSignal).length,
      note: "需要人工接管",
      tone: searchedConversations.some(hasManualGateSignal) ? "urgent" : "success"
    }
  ];
  const queueMatches = (item: ConversationInboxItem) => {
    if (targetChannelId !== null && item.channel_id !== targetChannelId) {
      return false;
    }
    if (activeQueue === "all") return true;
    if (activeQueue === "mine") return item.assigned_user_id === currentUserId && currentUserId !== null;
    return hasManualGateSignal(item);
  };

  const visibleConversations = searchedConversations.filter(queueMatches);
  const selectedConversation =
    visibleConversations.find((item) => item.id === selectedConversationId) ??
    visibleConversations.find((item) => item.sla_status === "breached") ??
    visibleConversations.find((item) => hasManualGateSignal(item)) ??
    visibleConversations[0] ??
    null;

  useEffect(() => {
    if (selectedConversation && selectedConversation.id !== selectedConversationId) {
      onSelectConversation(selectedConversation.id);
    }
  }, [onSelectConversation, selectedConversation?.id, selectedConversationId]);

  const relatedReview = selectedConversation ? reviewByConversation.get(selectedConversation.id) : undefined;
  const relatedReplyDecision = selectedConversation ? replyDecisionByConversation.get(selectedConversation.id) : undefined;
  const relatedDrafts = selectedConversation ? draftsByConversation.get(selectedConversation.id) ?? [] : [];
  const relatedFailures = selectedConversation ? relatedDrafts.flatMap((draft) => failuresByDraft.get(draft.id) ?? []) : [];
  const relatedJobs = relatedDrafts.length > 0 ? relatedDrafts.flatMap((draft) => jobsByDraft.get(draft.id) ?? []) : [];
  const selectedChannelIdentity = selectedConversation ? getChannelIdentity(selectedConversation, channelIdentities) : null;
  const latestDraft = relatedDrafts[0];
  const suggestedReply = relatedReview?.draft_reply || latestDraft?.reply_text || relatedReplyDecision?.draft_reply || "";
  const draftText = suggestedReply || "";
  const knowledgeMatches = relatedReview?.evidence.knowledge_matches ?? [];

  useEffect(() => {
    setEditableDraft(draftText);
    setWorkflowNotice("");
    setIsTransferOpen(false);
    setTransferTargetUserId("");
    setTransferNote("");
  }, [selectedConversation?.id, relatedReview?.id, latestDraft?.id, draftText]);

  useEffect(() => {
    if (!isTransferOpen || transferTargetUserId) {
      return;
    }
    const firstAvailableColleague = colleagues.find((colleague) => colleague.status !== "offline") ?? colleagues[0];
    if (firstAvailableColleague) {
      setTransferTargetUserId(String(firstAvailableColleague.id));
    }
  }, [colleagues, isTransferOpen, transferTargetUserId]);

  useEffect(() => {
    if (validTargetQueue) {
      setActiveQueue(validTargetQueue);
    }
  }, [validTargetQueue]);

  const isLoading = state.status === "loading";
  const pendingCount = scopedConversations.filter((item) => item.last_message_direction === "inbound").length;
  const handoffCount = scopedConversations.filter(hasManualGateSignal).length;
  if (!selectedConversation) {
    return (
      <section className="conversation-workbench-empty" id="workspace-live" aria-label="暂无会话">
        <div className="conversation-empty-illustration" aria-hidden="true">
          <span className="empty-blob" />
          <span className="empty-dot empty-dot-primary" />
          <span className="empty-dot empty-dot-small empty-dot-left" />
          <span className="empty-dot empty-dot-small empty-dot-right" />
          <span className="empty-plus empty-plus-left">+</span>
          <div className="empty-person">
            <span className="empty-person-head" />
            <span className="empty-person-hair" />
            <span className="empty-person-body" />
            <span className="empty-person-arm" />
          </div>
        </div>
        <p>上午好~今天也要元气满满呦!</p>
      </section>
    );
  }

  const timeline = selectedConversation
    ? buildConversationTimeline({
        conversation: selectedConversation,
        review: relatedReview,
        replyDecision: relatedReplyDecision,
        failures: relatedFailures,
        messages: conversationDetail?.id === selectedConversation.id ? conversationDetail.messages : []
      })
    : [];
  const localReplyIsForSelected = localReplyState.conversationId === selectedConversation.id;
  const isSendingLocalReply = localReplyIsForSelected && localReplyState.status === "sending";
  const canSendLocalReply =
    hasToken &&
    canManageConversations &&
    editableDraft.trim().length > 0 &&
    !isLoading &&
    !isSendingLocalReply;
  const canSaveManualDraft =
    Boolean(relatedReview) &&
    hasToken &&
    (canManageConversations || canApproveReviewDraft) &&
    editableDraft.trim().length > 0 &&
    !isLoading &&
    !isSendingLocalReply;
  const sendDisabledReason = !hasToken
    ? "请先登录本地管理员账号，才能写入真实接管状态。"
    : isLoading
      ? "按钮已禁用：正在刷新会话状态。"
      : !canManageConversations
        ? "按钮已禁用：当前账号无权限写入本地会话。"
        : isSendingLocalReply
          ? "正在写入本地会话。"
          : editableDraft.trim().length === 0
            ? "回复内容不能为空。"
            : "";
  const replyTextValue = editableDraft;
  const replyPlaceholder = "输入回复内容。当前只写入本地会话，不发送到外部平台。";
  const selectedChannelLabel = selectedChannelIdentity?.platform || selectedConversation.channel_name || selectedConversation.channel_type;
  const selectedStoreLabel = selectedChannelIdentity?.storeName || selectedChannelIdentity?.accountName || `渠道 #${selectedConversation.channel_id}`;
  const localReplyNotice = localReplyIsForSelected
    ? localReplyState.message
    : conversationDetailStatus === "loading"
      ? conversationDetailMessage
      : "仅本地记录，未发送到外部平台。";
  const visitorLink = `https://kf-preview.local/conversation/${selectedConversation.id}`;
  const quickReplyTemplates = {
    personal: [
      {
        title: "问候",
        items: [
          "您好，请问有什么可以帮您？",
          "请您稍等，我正在帮您核对。",
          "不要着急，我们正在处理，一会答复您。"
        ]
      },
      {
        title: "致歉",
        items: [
          "抱歉让您久等了，我马上为您处理。",
          "这个问题我需要确认一下，再给您准确答复。"
        ]
      },
      {
        title: "追踪",
        items: [
          "方便留一下联系方式吗？我们后续跟进。",
          "我先记录您的需求，稍后同步处理进度。"
        ]
      }
    ],
    customer: [
      {
        title: "客户信息",
        items: [
          `客户：${selectedConversation.contact_display_name || selectedConversation.subject}`,
          `来源：${selectedChannelLabel}`,
          `最近消息：${selectedConversation.last_message_preview || "暂无"}`
        ]
      }
    ],
    custom: [
      {
        title: "自定义",
        items: [
          "产品能力需要结合您的业务场景确认。",
          "报价和套餐以正式方案为准。",
          "隐私、合同、发票问题我会转交专人确认。"
        ]
      }
    ]
  };
  const selectedQuickReplyGroups = quickReplyTemplates[quickReplyTab];
  const selectedTransferColleague = colleagues.find((colleague) => String(colleague.id) === transferTargetUserId) ?? null;
  const canSubmitTransfer =
    hasToken &&
    canManageConversations &&
    selectedTransferColleague !== null &&
    selectedTransferColleague.status !== "offline" &&
    !isLoading;
  const insertQuickReply = (text: string) => {
    setEditableDraft((current) => (current.trim() ? `${current.trim()}\n${text}` : text));
  };
  const handleEndConversation = () => {
    setWorkflowNotice("已关闭对话，客户侧将显示“客服已关闭对话”。");
    onWorkflowAction(selectedConversation, "close", "坐席关闭当前对话，客户侧显示关闭提示。");
  };
  const handleTransferConversation = () => {
    if (!selectedTransferColleague) {
      return;
    }
    const note = transferNote.trim() || `坐席申请转接给 ${selectedTransferColleague.name}`;
    setWorkflowNotice(`已发起转接给 ${selectedTransferColleague.name}。`);
    setIsTransferOpen(false);
    onWorkflowAction(selectedConversation, "transfer", note, selectedTransferColleague.id, null);
  };

  return (
    <section className="conversation-workbench service-desk wechat-service-desk" id="workspace-live" aria-label="多渠道对话台">
      <div className="panel conversation-workbench-shell service-desk-shell">
        <div className="service-desk-toolbar service-desk-toolbar-slim" aria-label="接待台状态">
          <div className="service-toolbar-meta">
            <strong>客服消息</strong>
            <span>{visibleConversations.length} 个会话 · 进线 {pendingCount} · 转人工 {handoffCount}</span>
          </div>
          <div className="service-toolbar-actions">
            <button type="button" className="ghost-action service-refresh-action" onClick={onRefresh} disabled={!hasToken || isLoading}>
              <RefreshCw size={16} />
              {isLoading ? "刷新中" : "刷新"}
            </button>
          </div>
        </div>

        <div className="agent-desk-layout service-desk-layout">
          <aside className="conversation-thread-list conversation-queue-panel service-conversation-list wechat-session-list" aria-label="客户会话列表">
            <div className="service-agent-card" aria-label="当前接待状态">
              <span className="service-agent-avatar" aria-hidden="true">万</span>
              <div>
                <strong>客服小万</strong>
                <span>本地接待台</span>
              </div>
            </div>
            <label className="service-list-search">
              <Search size={15} aria-hidden="true" />
              <input
                type="search"
                value={conversationSearch}
                onChange={(event) => setConversationSearch(event.target.value)}
                placeholder="搜索当前会话"
                aria-label="搜索当前会话列表"
              />
            </label>
            <QueueTabs queues={queueDefinitions} activeQueue={activeQueue} onSelect={setActiveQueue} />
            <div className="service-thread-scroll">
              {visibleConversations.map((item) => (
                <button
                  key={item.id}
                  type="button"
                  className={`thread-list-item thread-list-item-v2 service-thread-item ${item.id === selectedConversation.id ? "is-selected" : ""}`}
                  onClick={() => onSelectConversation(item.id)}
                >
                  <span className="thread-row-head service-thread-compact-head">
                    <span className="service-thread-person">
                      <span className="service-avatar" aria-hidden="true">{getAvatarInitial(item.contact_display_name || item.subject)}</span>
                      <span>
                        <strong>{compactText(item.contact_display_name || `联系人 #${item.contact_id}`, 8)}</strong>
                        <small>{formatChannelShortName(item.channel_name || item.channel_type)}</small>
                      </span>
                    </span>
                    <span className="service-thread-meta">
                      <small>{formatWaitingMinutes(item.waiting_minutes)}</small>
                      {hasManualGateSignal(item) ? <span className="thread-status-dot is-hot">转人工</span> : null}
                      {!hasManualGateSignal(item) && item.sla_status === "breached" ? <span className="thread-status-dot is-hot">超时</span> : null}
                      {!hasManualGateSignal(item) && item.delivery_failure_open_count > 0 ? <span className="thread-status-dot is-hot">异常</span> : null}
                    </span>
                  </span>
                  <small className="service-thread-preview">{item.last_message_preview || item.subject || `会话 #${item.id}`}</small>
                </button>
              ))}
            </div>
          </aside>

          <article className="miduoke-chat-frame" aria-label="当前会话对话框">
            <section className="miduoke-chat-main">
              <header className="miduoke-chat-header">
                <div className="miduoke-chat-title">
                  <strong>{selectedConversation.contact_display_name || selectedConversation.subject}</strong>
                  <span>{selectedChannelLabel} · {selectedStoreLabel}</span>
                </div>
                <div className="miduoke-chat-actions" aria-label="会话工具">
                  <span className="miduoke-transfer-anchor">
                    <button type="button" title="转接同事" onClick={() => setIsTransferOpen((current) => !current)}>
                      <UserRound size={18} />
                    </button>
                    {isTransferOpen ? (
                      <section className="miduoke-transfer-dialog" role="dialog" aria-modal="false" aria-label="转接会话">
                        <header>
                          <strong>转接会话</strong>
                          <button type="button" aria-label="关闭转接窗口" onClick={() => setIsTransferOpen(false)}>×</button>
                        </header>
                        <label>
                          <span>转接给</span>
                          <select
                            value={transferTargetUserId}
                            onChange={(event) => setTransferTargetUserId(event.target.value)}
                          >
                            {colleagues.length === 0 ? <option value="">暂无同事</option> : null}
                            {colleagues.map((colleague) => (
                              <option key={colleague.id} value={colleague.id} disabled={colleague.status === "offline"}>
                                {colleague.name} · {formatColleagueStatus(colleague.status)} · {colleague.activeChats} 个会话
                              </option>
                            ))}
                          </select>
                        </label>
                        <label>
                          <span>转接备注</span>
                          <textarea
                            value={transferNote}
                            onChange={(event) => setTransferNote(event.target.value)}
                            placeholder="填写需要交接的客户背景、已处理事项或注意点"
                            rows={4}
                          />
                        </label>
                        <footer>
                          <button type="button" onClick={() => setIsTransferOpen(false)}>取消</button>
                          <button type="button" className="primary" disabled={!canSubmitTransfer} onClick={handleTransferConversation}>
                            确认转接
                          </button>
                        </footer>
                      </section>
                    ) : null}
                  </span>
                  <button type="button" title="结束对话" onClick={handleEndConversation}>
                    <Power size={18} />
                  </button>
                </div>
              </header>

              <div className="miduoke-visitor-strip">
                <span>正在访问</span>
                <a href={visitorLink}>{visitorLink}</a>
                <strong>IP：本地预览</strong>
              </div>

              <div className="miduoke-message-stream" aria-label="会话消息">
                {timeline.map((event) => (
                  <article key={event.id} className={`miduoke-message is-${event.kind}`}>
                    {event.kind === "system" ? (
                      <div className="miduoke-system-pill">
                        <span>{event.meta}</span>
                        <strong>{event.text}</strong>
                      </div>
                    ) : (
                      <>
                        <span className="miduoke-message-avatar" aria-hidden="true">
                          {event.kind === "customer" ? <UserRound size={18} /> : <Bot size={18} />}
                        </span>
                        <div className="miduoke-message-body">
                          <header>
                            <strong>{event.title}</strong>
                            <span>{event.meta}</span>
                          </header>
                          <p>{event.text}</p>
                        </div>
                      </>
                    )}
                  </article>
                ))}
              </div>

              <footer className="miduoke-composer">
                <textarea
                  value={replyTextValue}
                  onChange={(event) => setEditableDraft(event.target.value)}
                  aria-label="输入消息内容"
                  placeholder="请输入消息内容..."
                />
                <div className="miduoke-composer-foot">
                  <small className={localReplyState.status === "error" && localReplyIsForSelected ? "is-error" : ""}>
                    {workflowNotice || sendDisabledReason || localReplyNotice}
                  </small>
                  <div>
                    {relatedReview ? (
                      <button
                        type="button"
                        className="miduoke-secondary-send"
                        disabled={!canSaveManualDraft}
                        onClick={() => onApproveReviewDraft(relatedReview, editableDraft, "保存人工草稿，未发送到外部平台。")}
                      >
                        保存草稿
                      </button>
                    ) : null}
                    <button
                      type="button"
                      className="miduoke-send"
                      disabled={!canSendLocalReply}
                      onClick={() => onSendLocalReply(selectedConversation, editableDraft)}
                    >
                      {isSendingLocalReply ? "写入中" : "发送"}
                      <Send size={16} />
                    </button>
                  </div>
                </div>
              </footer>
            </section>

            <aside className="miduoke-quick-panel" aria-label="快捷回复">
              <div className="miduoke-quick-tabs">
                <button
                  type="button"
                  className={quickReplyTab === "personal" ? "active" : ""}
                  onClick={() => setQuickReplyTab("personal")}
                >
                  快捷回复
                </button>
                <button
                  type="button"
                  className={quickReplyTab === "customer" ? "active" : ""}
                  onClick={() => setQuickReplyTab("customer")}
                >
                  客户信息
                </button>
                <button
                  type="button"
                  className={quickReplyTab === "custom" ? "active" : ""}
                  onClick={() => setQuickReplyTab("custom")}
                >
                  自定义
                </button>
              </div>
              <label className="miduoke-quick-search">
                <Search size={15} />
                <input placeholder="搜索" />
              </label>
              <div className="miduoke-quick-list">
                {selectedQuickReplyGroups.map((group) => (
                  <section key={group.title}>
                    <strong>{group.title}</strong>
                    {group.items.map((item) => (
                      <button type="button" key={item} onClick={() => insertQuickReply(item)}>
                        <span>丁</span>
                        {item}
                      </button>
                    ))}
                  </section>
                ))}
              </div>
            </aside>
          </article>
        </div>
      </div>
    </section>
  );
}

function QueueTabs({
  queues,
  activeQueue,
  onSelect
}: {
  queues: WorkbenchQueueDefinition[];
  activeQueue: WorkbenchQueueKey;
  onSelect: (queue: WorkbenchQueueKey) => void;
}) {
  const primaryQueueKeys: WorkbenchQueueKey[] = ["all", "mine", "needs_review"];
  const primaryQueues = queues.filter((queue) => primaryQueueKeys.includes(queue.key));
  return (
    <div className="conversation-queue-tabs service-queue-tabs service-queue-filter" aria-label="会话队列筛选">
      <div className="service-primary-queues">
        {primaryQueues.map((queue) => (
          <QueueButton key={queue.key} queue={queue} activeQueue={activeQueue} onSelect={onSelect} />
        ))}
      </div>
    </div>
  );
}

function QueueButton({
  queue,
  activeQueue,
  onSelect
}: {
  queue: WorkbenchQueueDefinition;
  activeQueue: WorkbenchQueueKey;
  onSelect: (queue: WorkbenchQueueKey) => void;
}) {
  return (
    <button
      type="button"
      className={`queue-tab queue-${queue.tone} ${activeQueue === queue.key ? "is-active" : ""}`}
      onClick={() => onSelect(queue.key)}
    >
      <span>{queue.label}</span>
      <strong>{queue.count}</strong>
      <small>{queue.note}</small>
    </button>
  );
}

function compactText(value: string, maxLength: number) {
  const normalized = value.replace(/\s+/g, " ").trim();
  if (normalized.length <= maxLength) return normalized;
  return `${normalized.slice(0, maxLength - 1)}...`;
}

function getAvatarInitial(value: string) {
  return value.trim().slice(0, 1) || "客";
}

function formatWaitingMinutes(value: number) {
  if (value <= 0) return "刚刚";
  if (value < 60) return `${value} 分钟`;
  const hours = Math.floor(value / 60);
  const minutes = value % 60;
  return minutes > 0 ? `${hours} 小时 ${minutes} 分钟` : `${hours} 小时`;
}

function formatSlaLabel(value: string) {
  const labels: Record<string, string> = {
    ok: "SLA 正常",
    warning: "SLA 预警",
    breached: "SLA 超时"
  };
  return labels[value] ?? value;
}

function formatPriorityLabel(value: string) {
  const labels: Record<string, string> = {
    low: "低优先级",
    normal: "普通",
    medium: "中优先级",
    high: "高优先级",
    critical: "严重"
  };
  return labels[value] ?? value;
}

function formatDraftStatusLabel(value: string) {
  const labels: Record<string, string> = {
    pending_confirmation: "已生成回复",
    ready_to_send: "后台已准备",
    sent: "已发送",
    canceled: "已取消",
    failed: "发送失败"
  };
  return labels[value] ?? value;
}

function formatDeliveryStatusLabel(value: string) {
  const labels: Record<string, string> = {
    not_sent: "未外发",
    queued: "排队中",
    sending: "发送中",
    delivered: "已送达",
    failed: "发送失败",
    blocked: "已阻断"
  };
  return labels[value] ?? value;
}

function formatPercent(value: number | null) {
  if (value === null || Number.isNaN(value)) return "-";
  return `${Math.round(value * 100)}%`;
}

function formatDateTime(value: string | null) {
  if (!value) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit"
  });
}

function formatColleagueStatus(value: string) {
  const labels: Record<string, string> = {
    online: "在线",
    busy: "忙碌",
    offline: "离线"
  };
  return labels[value] ?? value;
}

function normalizeChannelClass(value: string) {
  return value.toLowerCase().replace(/[^a-z0-9]+/g, "-") || "unknown";
}

function formatChannelShortName(value: string) {
  if (!value) return "渠道";
  return value.replace(/[（(].*?[)）]/g, "").replace(/客服|私信|店铺/g, "").trim() || value;
}

function compareDecisionFreshness(left: ReplyDecision, right: ReplyDecision) {
  const leftTime = getDecisionTime(left);
  const rightTime = getDecisionTime(right);
  if (leftTime !== rightTime) return leftTime - rightTime;
  return left.id - right.id;
}

function getDecisionTime(decision: ReplyDecision) {
  if (!decision.created_at) return 0;
  const date = new Date(decision.created_at);
  return Number.isNaN(date.getTime()) ? 0 : date.getTime();
}

function formatReplyDecisionStateLabel(value: string) {
  const labels: Record<string, string> = {
    auto_reply_ready: "已处理",
    manual_gate_required: "转人工",
    knowledge_gap: "知识缺口",
    blocked_by_policy: "策略阻断",
    draft_only: "草稿"
  };
  return labels[value] ?? "转人工";
}

function formatReplyDecisionReasonLabel(value: string) {
  const labels: Record<string, string> = {
    object_card_high_confidence: "业务对象和知识卡高置信命中",
    manual_review_terms: "命中需要人工确认的话术或场景",
    no_business_object_match: "未识别到可用业务对象",
    no_knowledge_card_match: "未命中可引用知识卡",
    low_confidence: "置信度不足",
    blocked_policy_terms: "命中策略阻断词",
    external_write_disabled: "真实外发开关关闭"
  };
  return labels[value] ?? (value || "等待决策原因");
}

function formatReplyDeliveryModeLabel(value: string) {
  const labels: Record<string, string> = {
    draft_only: "只生成草稿",
    human_review: "转人工",
    external_write_allowed: "允许外发",
    blocked: "禁止外发"
  };
  return labels[value] ?? "转人工";
}

function formatReplyDecisionNextAction(decision: ReplyDecision) {
  if (decision.state === "auto_reply_ready") return "进入外发前置门禁";
  if (decision.state === "manual_gate_required") return "转人工接管";
  if (decision.state === "knowledge_gap") return "补业务对象知识";
  if (decision.state === "blocked_by_policy") return "策略复核";
  return "转人工复核";
}

function formatReplyDecisionGateLabel(decision: ReplyDecision) {
  if (decision.state === "auto_reply_ready") return "已处理";
  if (decision.state === "manual_gate_required") return "异常转人工";
  if (decision.state === "knowledge_gap") return "知识缺口";
  if (decision.state === "blocked_by_policy") return "策略阻断";
  return "仅生成草稿";
}

function formatReplyDecisionObjectLabel(decision: ReplyDecision) {
  const businessObject = decision.decision_payload.business_object;
  if (isRecord(businessObject) && typeof businessObject.title === "string" && businessObject.title.trim()) {
    return businessObject.title;
  }
  if (decision.business_object_id) return `业务对象 #${decision.business_object_id}`;
  return "未识别";
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function readRecordString(record: Record<string, unknown>, key: string) {
  const value = record[key];
  return typeof value === "string" ? value : "";
}

function formatModelCallLabel(modelCall: Record<string, unknown> | null) {
  if (!modelCall) return "未调用模型";
  const provider = formatProviderLabel(readRecordString(modelCall, "provider"));
  if (modelCall.external_call_performed === false) {
    return `${provider} · 本地样本`;
  }
  const status = formatModelStatusLabel(readRecordString(modelCall, "status"));
  return `${provider} · ${status}`;
}

function formatModelCallDetail(modelCall: Record<string, unknown> | null) {
  if (!modelCall) return "未记录模型调用";
  const provider = formatProviderLabel(readRecordString(modelCall, "provider"));
  const model = readRecordString(modelCall, "model") || "模型";
  const routeName = readRecordString(modelCall, "route_name");
  const status = formatModelStatusLabel(readRecordString(modelCall, "status"));
  return [provider, model, routeName, status].filter(Boolean).join(" / ");
}

function formatProviderLabel(value: string) {
  const labels: Record<string, string> = {
    bailian: "百炼",
    deepseek: "深度求索",
    local_seed_ai_draft: "本地样本"
  };
  return labels[value] ?? (value || "模型");
}

function formatModelStatusLabel(value: string) {
  const labels: Record<string, string> = {
    succeeded: "已完成",
    success: "已完成",
    failed: "失败",
    timeout: "超时",
    unknown: "未记录状态"
  };
  return labels[value] ?? (value || "未记录状态");
}

function canClaimConversation(
  item: ConversationInboxItem,
  currentUserId: number | null,
  hasToken: boolean,
  isLoading: boolean
) {
  if (!hasToken || isLoading || !currentUserId || Number.isNaN(currentUserId)) return false;
  if (item.status === "resolved") return true;
  return item.assigned_user_id === null || item.assigned_user_id === currentUserId;
}

function canWorkConversation(item: ConversationInboxItem, hasToken: boolean, isLoading: boolean) {
  return hasToken && !isLoading && item.status !== "resolved";
}

function normalizeWorkbenchQueueKey(value: string | undefined): WorkbenchQueueKey | null {
  if (!value) return null;
  if (
    value === "pending_outbox" ||
    value === "high_risk" ||
    value === "no_knowledge" ||
    value === "delivery_failed" ||
    value === "sla_breached"
  ) {
    return "needs_review";
  }
  if (["all", "mine", "needs_review"].includes(value)) {
    return value as WorkbenchQueueKey;
  }
  return null;
}

function getChannelIdentity(
  item: ConversationInboxItem,
  identities: Record<number, ChannelIdentitySummary>
): ChannelIdentitySummary {
  return identities[item.channel_id] ?? {
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
}

function formatAuthorizationStatusLabel(value: string) {
  const labels: Record<string, string> = {
    official_configuring: "官方配置中",
    official_ready: "官方已授权",
    sandbox_configuring: "测试配置中",
    rpa_research_only: "研究试验",
    website_ready: "官网可用",
    manual_import: "手动导入",
    unknown: "待登记"
  };
  return labels[value] ?? value;
}

function formatReplyModeLabel(value: string) {
  const labels: Record<string, string> = {
    auto_with_handoff: "自动回复",
    human_review_first: "先审后发",
    draft_only: "只生成草稿",
    blocked: "禁止外发",
    research_draft_only: "研究草稿"
  };
  return labels[value] ?? value;
}

function buildConversationTimeline({
  conversation,
  review,
  replyDecision,
  failures,
  messages
}: {
  conversation: ConversationInboxItem;
  review: HumanReviewInboxItem | undefined;
  replyDecision: ReplyDecision | undefined;
  failures: DeliveryFailureReview[];
  messages: MessageRead[];
}): ConversationTimelineEvent[] {
  const sortedMessages = [...messages].sort((left, right) => {
    const leftTime = left.created_at ? new Date(left.created_at).getTime() : 0;
    const rightTime = right.created_at ? new Date(right.created_at).getTime() : 0;
    return leftTime - rightTime || left.id - right.id;
  });
  const events: ConversationTimelineEvent[] = sortedMessages.map((message) => {
    const outbound = message.direction === "outbound";
    const kind: ConversationTimelineEvent["kind"] = message.sender_type === "system"
      ? "system"
      : outbound
      ? message.sender_type === "ai"
        ? "ai"
        : "agent"
      : "customer";
    return {
      id: `message-${message.id}`,
      kind,
      title: kind === "system"
        ? "系统消息"
        : outbound
          ? (message.sender_type === "ai" ? "AI 建议" : "坐席")
          : conversation.contact_display_name || `联系人 #${conversation.contact_id}`,
      text: message.content || "空消息",
      meta: `${outbound ? "本地记录" : conversation.channel_name} · ${formatDateTime(message.created_at)}`
    };
  });
  if (events.length === 0) {
    events.push({
      id: `customer-${conversation.id}`,
      kind: "customer",
      title: conversation.contact_display_name || `联系人 #${conversation.contact_id}`,
      text: review?.trigger_message?.content || conversation.last_message_preview || "暂无客户入站内容",
      meta: `${conversation.channel_name} · ${formatDateTime(conversation.last_message_at)}`
    });
  }
  const decisionReply = replyDecision?.draft_reply?.trim();
  if (events.length <= 1 && replyDecision && decisionReply && replyDecision.state === "auto_reply_ready") {
    events.push({
      id: `reply-decision-${replyDecision.id}`,
      kind: "ai",
      title: "客服小万",
      text: decisionReply,
      meta: formatDateTime(replyDecision.created_at)
    });
  } else if (events.length <= 1 && review?.draft_reply) {
    events.push({
      id: `review-${review.id}`,
      kind: "ai",
      title: "客服小万",
      text: review.draft_reply,
      meta: `待接管确认 · ${formatDateTime(review.created_at)}`
    });
  } else if (events.length <= 1 && replyDecision && replyDecision.state !== "auto_reply_ready") {
    events.push({
      id: `reply-decision-${replyDecision.id}`,
      kind: "system",
      title: "系统消息",
      text: replyDecision.state === "knowledge_gap" ? "已识别为知识缺口，需要补充资料后再回复。" : "已进入转人工，请坐席接管当前会话。",
      meta: formatDateTime(replyDecision.created_at)
    });
  }
  if (review && !decisionReply && !review.draft_reply) {
    events.push({
      id: `review-${review.id}`,
      kind: "system",
      title: "系统消息",
      text: "当前没有稳妥回复，需要坐席补充。",
      meta: `${formatPriorityLabel(review.risk_level)} · ${formatDateTime(review.created_at)}`
    });
  }
  failures.slice(0, 1).forEach((failure) => {
    events.push({
      id: `failure-${failure.id}`,
      kind: "system",
      title: "系统消息",
      text: "渠道链路异常，已保留复盘记录，请到渠道中心处理。",
      meta: formatDateTime(failure.created_at)
    });
  });
  return events;
}

function buildConversationNextBestAction({
  conversation,
  review,
  latestDraft,
  jobs,
  failures
}: {
  conversation: ConversationInboxItem;
  review: HumanReviewInboxItem | undefined;
  latestDraft: OutboxDraft | undefined;
  jobs: OutboxDeliveryJob[];
  failures: DeliveryFailureReview[];
}) {
  if (failures.length > 0) return "先处理发送失败和渠道状态";
  if (review?.evidence.retrieved_knowledge_count === 0 || review?.reason.includes("无知识")) return "先补知识库，再人工接管";
  if (review && ["critical", "high"].includes(review.risk_level)) return "高风险会话，人工核对后再答";
  if (review) return "人工接管当前会话";
  if (latestDraft?.status === "pending_confirmation") return "查看待确认回复";
  if (jobs.some((job) => ["blocked", "retry_scheduled"].includes(job.status))) return "复查后台发送状态";
  if (conversation.assigned_user_id === null) return "领取会话并确认客户意图";
  if (conversation.sla_status === "breached") return "优先处理超时会话";
  return conversation.next_action || "继续接待客户";
}
