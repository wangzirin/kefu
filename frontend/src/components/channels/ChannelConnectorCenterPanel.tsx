import {
  Building2,
  Code2,
  Copy,
  Eye,
  Globe2,
  Link2,
  MessageCircle,
  RefreshCw,
  Send,
  Settings,
  Smartphone,
  X,
  AlertTriangle,
  PlusCircle,
  Route,
  ShieldCheck,
  Store,
  UsersRound
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import type { FormEvent } from "react";

import type {
  Channel,
  ChannelAccount,
  ChannelAccountPayload,
  DeliveryFailureReview,
  HumanReviewInboxItem,
  OutboxDeliveryJob,
  OutboxDraft,
  TrustedInboundWorkerRun
} from "../../api/client";
import { DataSourceBadge, EXTERNAL_WRITE_OFF_LABEL, PREVIEW_DATA_LABEL, REAL_DATA_LABEL } from "../common/WorkspaceState";

type ChannelConnectorStepStatus = "done" | "current" | "pending" | "blocked";
type ChannelConnectorTone = "success" | "warning" | "urgent" | "muted";
type ChannelAccessLayer = "accounts" | "people" | "wecom" | "official" | "boundaries";

type ChannelAccountState =
  | { status: "idle"; message: string; channels: Channel[]; accounts: ChannelAccount[] }
  | { status: "loading"; channels: Channel[]; accounts: ChannelAccount[] }
  | { status: "ready"; channels: Channel[]; accounts: ChannelAccount[] }
  | { status: "error"; message: string; channels: Channel[]; accounts: ChannelAccount[] };

interface ChannelAccountDraft {
  channelId: string;
  provider: string;
  platform: string;
  accountName: string;
  externalAccountId: string;
  storeName: string;
  entrypointName: string;
  authorizationStatus: string;
  accessStatus: string;
  replyMode: string;
  healthStatus: string;
  visibleScope: string;
  publicNote: string;
}

interface ChannelConnectorStep {
  label: string;
  description: string;
  status: ChannelConnectorStepStatus;
  evidence?: string;
}

interface ChannelConnectorConfigItem {
  label: string;
  status: string;
  value: string;
  note: string;
  sensitive?: boolean;
}

interface ChannelConnectorCard {
  id: string;
  name: string;
  category: string;
  status: string;
  tone: ChannelConnectorTone;
  summary: string;
  currentBlocker: string;
  officialPath: string;
  nextAction: string;
  steps: ChannelConnectorStep[];
  config: ChannelConnectorConfigItem[];
  blockers: string[];
  prerequisites: string[];
}

interface ChannelSandboxPriority {
  id: string;
  channel: string;
  formalPath: string;
  currentStatus: string;
  sandboxPriority: string;
  rpaBoundary: string;
}

interface ChannelRoleResponsibility {
  role: string;
  purpose: string;
  configOwner: string;
  requiredBeforeTrial: string;
}

interface ChannelBoundaryRequirement {
  channel: string;
  officialCondition: string;
  requiredMaterials: string;
  currentStatus: string;
  unfinishedReason: string;
}

type ChannelEntryId = "website" | "wechat_official" | "wechat_miniapp" | "wecom";

interface ChannelAccessComponent {
  id: string;
  name: string;
  componentType: string;
  style: "widget" | "link" | "menu" | "miniapp" | "qrcode";
  mount: string;
  status: "enabled" | "draft" | "planned";
  updatedAt: string;
  description: string;
  position?: string;
  welcomeText?: string;
  themeColor?: string;
  buttonText?: string;
  allowedOrigin?: string;
}

interface ChannelEntryDefinition {
  id: ChannelEntryId;
  label: string;
  subtitle: string;
  description: string;
  componentQuota: number;
  setupHint: string;
  primaryAction: string;
  secondaryAction: string;
  components: ChannelAccessComponent[];
}

interface CustomerPreviewMessage {
  id: string;
  role: "customer" | "agent" | "system";
  text: string;
  time: string;
}

interface WebsiteComponentConfigDraft {
  name: string;
  componentType: "插件型" | "链接型";
  mount: string;
  welcomeText: string;
  themeColor: string;
  buttonText: string;
  allowedOrigin: string;
}

export function ChannelConnectorCenterPanel({
  selectedChannelId,
  reviewItems,
  outboxDrafts,
  failureReviews,
  deliveryJobs,
  workerRun,
  channelAccountState,
  hasToken,
  canManageConnector,
  onConfigureChannelAccount,
  onRefreshChannelAccounts,
  onCreateSafeTestConversation,
  tenantId
}: {
  selectedChannelId?: string;
  reviewItems: HumanReviewInboxItem[];
  outboxDrafts: OutboxDraft[];
  failureReviews: DeliveryFailureReview[];
  deliveryJobs: OutboxDeliveryJob[];
  workerRun: TrustedInboundWorkerRun | null;
  channelAccountState: ChannelAccountState;
  hasToken: boolean;
  canManageConnector: boolean;
  onConfigureChannelAccount: (channelId: number, payload: ChannelAccountPayload) => Promise<ChannelAccount>;
  onRefreshChannelAccounts: () => void;
  onCreateSafeTestConversation?: () => Promise<unknown | null>;
  tenantId?: string | number;
}) {
  const connectors = buildChannelConnectorCards({
    reviewItems,
    outboxDrafts,
    failureReviews,
    deliveryJobs,
    workerRun,
    hasToken,
    canManageConnector
  });
  const primary = connectors[0];
  const officialOnlyConnectors = connectors.slice(1);
  const readySteps = primary.steps.filter((step) => step.status === "done").length;
  const blockedSteps = primary.steps.filter((step) => step.status === "blocked").length;
  const [accountDraft, setAccountDraft] = useState<ChannelAccountDraft>({
    channelId: "",
    provider: "",
    platform: "",
    accountName: "",
    externalAccountId: "",
    storeName: "",
    entrypointName: "",
    authorizationStatus: "not_configured",
    accessStatus: "planned",
    replyMode: "draft_only",
    healthStatus: "unknown",
    visibleScope: "",
    publicNote: ""
  });
  const [accountSaveState, setAccountSaveState] = useState<{ status: "idle" | "saving" | "success" | "error"; message: string }>({
    status: "idle",
    message: ""
  });
  const [activeLayer, setActiveLayer] = useState<ChannelAccessLayer>("accounts");
  const [activeChannelId, setActiveChannelId] = useState<ChannelEntryId>(() => normalizeChannelEntryId(selectedChannelId));
  const [componentTypeFilter, setComponentTypeFilter] = useState("all");
  const [componentSearch, setComponentSearch] = useState("");
  const [selectedComponentId, setSelectedComponentId] = useState("website-widget");
  const [websiteComponents, setWebsiteComponents] = useState<ChannelAccessComponent[]>(() =>
    CHANNEL_ENTRY_DEFINITIONS.find((entry) => entry.id === "website")?.components ?? []
  );
  const [codeModalComponent, setCodeModalComponent] = useState<ChannelAccessComponent | null>(null);
  const [previewModalComponent, setPreviewModalComponent] = useState<ChannelAccessComponent | null>(null);
  const [configModalComponent, setConfigModalComponent] = useState<ChannelAccessComponent | null>(null);
  const [configDraft, setConfigDraft] = useState<WebsiteComponentConfigDraft>(() =>
    createWebsiteConfigDraft(CHANNEL_ENTRY_DEFINITIONS.find((entry) => entry.id === "website")?.components[0])
  );
  const [previewStartState, setPreviewStartState] = useState<{ status: "idle" | "starting" | "error"; message: string }>({
    status: "idle",
    message: ""
  });
  const [isCustomerPreviewOpen, setIsCustomerPreviewOpen] = useState(true);
  const [customerDraft, setCustomerDraft] = useState("");
  const [customerPreviewMessages, setCustomerPreviewMessages] = useState<CustomerPreviewMessage[]>(DEFAULT_CUSTOMER_PREVIEW_MESSAGES);
  const [channelUiNotice, setChannelUiNotice] = useState("");
  const availableChannels = channelAccountState.channels;
  const channelAccounts = channelAccountState.accounts;
  const channelById = useMemo(() => {
    const result: Record<number, Channel> = {};
    availableChannels.forEach((channel) => {
      result[channel.id] = channel;
    });
    return result;
  }, [availableChannels]);
  const selectedChannel = accountDraft.channelId ? channelById[Number(accountDraft.channelId)] : null;

  useEffect(() => {
    const nextChannelId = normalizeChannelEntryId(selectedChannelId);
    const nextEntry = CHANNEL_ENTRY_DEFINITIONS.find((entry) => entry.id === nextChannelId) ?? CHANNEL_ENTRY_DEFINITIONS[0];
    setActiveChannelId((current) => (current === nextChannelId ? current : nextChannelId));
    setComponentTypeFilter("all");
    setComponentSearch("");
    const nextComponents = nextEntry.id === "website" ? websiteComponents : nextEntry.components;
    setSelectedComponentId(nextComponents[0]?.id ?? "");
    setIsCustomerPreviewOpen(true);
    setChannelUiNotice("");
  }, [selectedChannelId, websiteComponents]);

  async function submitChannelAccount(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!canManageConnector) {
      setAccountSaveState({ status: "error", message: "当前账号没有渠道配置权限。" });
      return;
    }
    if (!hasToken) {
      setAccountSaveState({ status: "error", message: "需要正式登录后才能配置渠道账号。" });
      return;
    }
    if (!accountDraft.channelId || !accountDraft.accountName.trim()) {
      setAccountSaveState({ status: "error", message: "请选择渠道，并填写账号名称。" });
      return;
    }
    setAccountSaveState({ status: "saving", message: "正在保存渠道账号配置..." });
    try {
      const provider = accountDraft.provider.trim() || selectedChannel?.type || "";
      const platform = accountDraft.platform.trim() || selectedChannel?.name || provider;
      await onConfigureChannelAccount(Number(accountDraft.channelId), {
        connector_id: null,
        provider,
        platform,
        account_name: accountDraft.accountName.trim(),
        external_account_id: accountDraft.externalAccountId.trim(),
        store_name: accountDraft.storeName.trim(),
        entrypoint_name: accountDraft.entrypointName.trim(),
        authorization_status: accountDraft.authorizationStatus,
        access_status: accountDraft.accessStatus,
        reply_mode: accountDraft.replyMode,
        health_status: accountDraft.healthStatus,
        public_profile: {
          visible_scope: accountDraft.visibleScope.trim(),
          note: accountDraft.publicNote.trim(),
          external_write: "disabled_by_design"
        }
      });
      setAccountSaveState({ status: "success", message: "已保存渠道账号 / 店铺登记，并回刷对话台来源身份。" });
    } catch (error) {
      const message = error instanceof Error ? error.message : "保存渠道账号失败";
      setAccountSaveState({ status: "error", message });
    }
  }

  const activeEntry = CHANNEL_ENTRY_DEFINITIONS.find((entry) => entry.id === activeChannelId) ?? CHANNEL_ENTRY_DEFINITIONS[0];
  const activeComponents = activeEntry.id === "website" ? websiteComponents : activeEntry.components;
  const componentTypes = Array.from(new Set(activeComponents.map((component) => component.componentType)));
  const filteredComponents = activeComponents.filter((component) => {
    const keyword = componentSearch.trim().toLowerCase();
    const matchesType = componentTypeFilter === "all" || component.componentType === componentTypeFilter;
    const matchesKeyword =
      !keyword ||
      [component.name, component.componentType, component.mount, component.description].some((value) =>
        value.toLowerCase().includes(keyword)
      );
    return matchesType && matchesKeyword;
  });
  const listedComponents = activeEntry.id === "website" ? filteredComponents : [];
  const channelColumns = getChannelTableColumns(activeEntry.id);
  const channelNotes = getChannelAccessNotes(activeEntry.id);
  const guideSteps = getChannelGuideSteps(activeEntry.id);
  const apiFields = getChannelApiFields(activeEntry.id);
  const backendHooks = getChannelBackendHooks(activeEntry.id);
  const selectedComponent =
    activeComponents.find((component) => component.id === selectedComponentId) ??
    activeComponents[0];
  const codeSnippet = buildCustomerAccessSnippet(activeEntry, selectedComponent, tenantId);

  function selectChannel(entry: ChannelEntryDefinition) {
    setActiveChannelId(entry.id);
    setComponentTypeFilter("all");
    setComponentSearch("");
    const nextComponents = entry.id === "website" ? websiteComponents : entry.components;
    setSelectedComponentId(nextComponents[0]?.id ?? "");
    setIsCustomerPreviewOpen(true);
    setChannelUiNotice("");
    if (typeof window !== "undefined") {
      window.history.replaceState(null, "", `#channels?channel=${entry.id}`);
      window.dispatchEvent(new HashChangeEvent("hashchange"));
    }
  }

  function openCodeModal(component: ChannelAccessComponent) {
    setSelectedComponentId(component.id);
    setCodeModalComponent(component);
    setChannelUiNotice(`正在查看“${component.name}”接入代码。`);
  }

  function openPreview(component: ChannelAccessComponent) {
    setSelectedComponentId(component.id);
    setPreviewModalComponent(component);
    setPreviewStartState({ status: "idle", message: "" });
    setChannelUiNotice(`正在预览：${component.name}`);
  }

  function openConfig(component: ChannelAccessComponent) {
    setSelectedComponentId(component.id);
    setConfigModalComponent(component);
    setConfigDraft(createWebsiteConfigDraft(component));
    setAccountDraft((current) => ({
      ...current,
      provider: activeEntry.id,
      platform: activeEntry.label,
      accountName: `${activeEntry.label}测试入口`,
      storeName: activeEntry.label,
      entrypointName: component.name,
      authorizationStatus: "sandbox_configuring",
      accessStatus: "sandbox_configuring",
      replyMode: "human_review_first",
      healthStatus: "configuring",
      publicNote: component.description
    }));
    setChannelUiNotice(`正在配置：${component.name}`);
  }

  function configureComponent(component: ChannelAccessComponent) {
    if (activeEntry.id === "website") {
      openConfig(component);
      return;
    }
    setSelectedComponentId(component.id);
    setAccountDraft((current) => ({
      ...current,
      provider: activeEntry.id,
      platform: activeEntry.label,
      accountName: `${activeEntry.label}测试入口`,
      storeName: activeEntry.label,
      entrypointName: component.name,
      authorizationStatus: "sandbox_configuring",
      accessStatus: "sandbox_configuring",
      replyMode: "human_review_first",
      healthStatus: "configuring",
      publicNote: component.description
    }));
    setChannelUiNotice(`已把“${component.name}”填入前端配置草稿。`);
  }

  async function copySnippet(snippet = codeSnippet) {
    try {
      await navigator.clipboard.writeText(snippet);
      setChannelUiNotice("接入代码已复制到剪贴板。");
    } catch {
      setChannelUiNotice("当前浏览器不允许直接复制，可以手动选择代码。");
    }
  }

  async function startPreviewConversation() {
    if (!hasToken || !onCreateSafeTestConversation) {
      setPreviewStartState({ status: "error", message: "需要登录并具备会话管理权限后才能进入测试对话。" });
      return;
    }
    setPreviewStartState({ status: "starting", message: "正在创建测试对话..." });
    const result = await onCreateSafeTestConversation();
    if (!result) {
      setPreviewStartState({ status: "error", message: "需要登录并具备会话管理权限后才能进入测试对话。" });
      return;
    }
    setPreviewStartState({ status: "idle", message: "" });
    setPreviewModalComponent(null);
  }

  function submitWebsiteConfig(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!configModalComponent) {
      return;
    }
    const now = new Date();
    const nextStyle = configDraft.componentType === "链接型" ? "link" : "widget";
    setWebsiteComponents((current) =>
      current.map((component) =>
        component.id === configModalComponent.id
          ? {
              ...component,
              name: configDraft.name.trim() || component.name,
              componentType: configDraft.componentType,
              style: nextStyle,
              mount: configDraft.mount.trim() || component.mount,
              welcomeText: configDraft.welcomeText.trim(),
              themeColor: configDraft.themeColor.trim() || "#1677ff",
              buttonText: configDraft.buttonText.trim() || "在线咨询",
              allowedOrigin: configDraft.allowedOrigin.trim(),
              position: nextStyle === "widget" ? "right-bottom" : "inline-link",
              updatedAt: formatChannelComponentUpdatedAt(now),
              description:
                nextStyle === "widget"
                  ? "网页右下角浮窗，顾客可直接打开聊天。"
                  : "可复制到按钮、菜单或二维码里的顾客咨询链接。"
            }
          : component
      )
    );
    setConfigModalComponent(null);
    setChannelUiNotice(`已保存“${configDraft.name.trim() || configModalComponent.name}”前端配置，后续可接 connector-config。`);
  }

  function submitCustomerPreview(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const content = customerDraft.trim();
    if (!content) {
      return;
    }
    const now = new Date();
    const time = now.toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" });
    setCustomerPreviewMessages((current) => [
      ...current,
      { id: `customer-${now.getTime()}`, role: "customer", text: content, time },
      {
        id: `agent-${now.getTime()}`,
        role: "agent",
        text: "您好，已收到您的咨询。这里是顾客端预览消息，后续可接入真实会话队列。",
        time
      }
    ]);
    setCustomerDraft("");
  }

  function showClosedNotice() {
    const now = new Date();
    setCustomerPreviewMessages((current) => [
      ...current,
      {
        id: `system-close-${now.getTime()}`,
        role: "system",
        text: "客服已关闭对话",
        time: now.toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" })
      }
    ]);
  }

  return (
    <section
      id="workspace-channels"
      className="channel-access-workbench miduoke-channel-settings"
      data-channel-connector-smoke="center"
      aria-label="渠道接入"
    >
      <main className="channel-access-main">
        <header className="channel-access-topbar">
          <strong>{activeEntry.label}</strong>
        </header>

        <div className="miduoke-channel-layout">
          <div className="miduoke-channel-main">
            <section className="miduoke-access-card" aria-label={`${activeEntry.label}接入说明`}>
              <h2>{activeEntry.id === "wecom" ? "绑定企业微信账号" : `${activeEntry.label}接入`}</h2>
              <p>{activeEntry.description}</p>
              <div className="miduoke-access-actions">
                <button type="button" className="miduoke-primary-button" onClick={() => configureComponent(activeComponents[0])}>
                  {activeEntry.id === "website" ? activeEntry.primaryAction : activeEntry.id === "wechat_official" ? "扫码接入（推荐）" : "扫码接入"}
                </button>
                {activeEntry.id !== "website" ? (
                  <button type="button" className="miduoke-primary-button" onClick={() => configureComponent(activeComponents[0])}>
                    手动接入
                  </button>
                ) : null}
                {activeEntry.id === "wechat_official" || activeEntry.id === "wechat_miniapp" ? (
                  <button type="button" className="miduoke-secondary-button" onClick={() => configureComponent(activeComponents[0])}>
                    全局配置
                  </button>
                ) : null}
                {activeEntry.id === "website" ? (
                  <button type="button" className="miduoke-secondary-button" onClick={() => configureComponent(activeComponents[0])}>
                    {activeEntry.secondaryAction}
                  </button>
                ) : null}
              </div>
              {channelNotes.length ? (
                <div className="miduoke-access-notes">
                  {channelNotes.map((note) => (
                    <p key={note}>{note}</p>
                  ))}
                </div>
              ) : null}
            </section>

            <section className="miduoke-list-card" aria-label={getChannelTableTitle(activeEntry.id)}>
              <div className="miduoke-list-toolbar">
                <div>
                  <h2>{getChannelTableTitle(activeEntry.id)}</h2>
                  {activeEntry.id === "website" ? <small>*还可添加{activeEntry.componentQuota}个组件</small> : null}
                </div>
                <div className="miduoke-search-group">
                  {activeEntry.id === "website" ? (
                    <select value={componentTypeFilter} onChange={(event) => setComponentTypeFilter(event.target.value)}>
                      <option value="all">组件类型</option>
                      {componentTypes.map((type) => (
                        <option key={type} value={type}>
                          {type}
                        </option>
                      ))}
                    </select>
                  ) : null}
                  <input
                    value={componentSearch}
                    onChange={(event) => setComponentSearch(event.target.value)}
                    placeholder={getChannelSearchPlaceholder(activeEntry.id)}
                  />
                  <button type="button" aria-label="搜索">
                    搜索
                  </button>
                </div>
              </div>

              <div className="miduoke-channel-table" role="table">
                <div className="miduoke-channel-row head" role="row" style={{ gridTemplateColumns: getChannelGridTemplate(activeEntry.id) }}>
                  {channelColumns.map((column) => (
                    <span key={column}>{column}</span>
                  ))}
                </div>
                {listedComponents.length ? (
                  listedComponents.map((component) => (
                    <div
                      key={component.id}
                      className="miduoke-channel-row"
                      role="row"
                      style={{ gridTemplateColumns: getChannelGridTemplate(activeEntry.id) }}
                    >
                      <span>
                        <ChannelComponentPreviewIcon style={component.style} />
                      </span>
                      <span>
                        <strong>{component.name}</strong>
                        <small>{component.componentType}</small>
                      </span>
                      <span>{component.mount}</span>
                      <span>{component.updatedAt.replace(" 09:30", " 13:45")}</span>
                      <span className="miduoke-channel-actions">
                        <button type="button" onClick={() => openCodeModal(component)}>
                          查看代码
                        </button>
                        <button type="button" onClick={() => openPreview(component)}>
                          预览
                        </button>
                        <button type="button" onClick={() => openConfig(component)}>
                          配置
                        </button>
                      </span>
                    </div>
                  ))
                ) : (
                  <div className="miduoke-empty-state">
                    <span />
                    <p>暂无数据</p>
                  </div>
                )}
              </div>
              {activeEntry.id === "website" && listedComponents.length ? (
                <div className="miduoke-pagination" aria-label="分页">
                  <button type="button">‹</button>
                  <strong>1</strong>
                  <button type="button">›</button>
                  <span>共{listedComponents.length}条</span>
                  <select defaultValue="5">
                    <option value="5">5 条/页</option>
                    <option value="10">10 条/页</option>
                  </select>
                  <span>跳至</span>
                  <input defaultValue="1" aria-label="页码" />
                  <span>页</span>
                  <button type="button">确定</button>
                </div>
              ) : null}
            </section>
          </div>

          <aside className="miduoke-guide-panel" aria-label={`${activeEntry.label}接入指导`}>
            <h2>接入指导</h2>
            <p>{activeEntry.setupHint}</p>
            <ol>
              {guideSteps.map((step) => (
                <li key={step}>
                  <span>{step}</span>
                </li>
              ))}
            </ol>
            <div className="miduoke-guide-note">
              <strong>当前状态</strong>
              <span>{channelUiNotice || "请按左侧渠道选择对应接入方式，未配置前不会触发真实外发。"}</span>
            </div>
            <div className="miduoke-api-contract" aria-label={`${activeEntry.label}后端接口预留`}>
              <div>
                <strong>后端接口预留</strong>
                <small>按钮后续接这些字段</small>
              </div>
              <dl>
                {apiFields.map((field) => (
                  <div key={field.label}>
                    <dt>{field.label}</dt>
                    <dd>{field.value}</dd>
                  </div>
                ))}
              </dl>
              <div className="miduoke-hook-list">
                {backendHooks.map((hook) => (
                  <code key={hook}>{hook}</code>
                ))}
              </div>
            </div>
          </aside>
        </div>
      </main>
      {codeModalComponent ? (
        <div className="miduoke-modal-backdrop" role="presentation">
          <section className="miduoke-modal miduoke-code-modal" role="dialog" aria-modal="true" aria-label="嵌入网站代码">
            <header className="miduoke-modal-head">
              <div>
                <h2>嵌入网站代码</h2>
                <p>将以下代码嵌入到网站页面 &lt;/body&gt; 标签之前即可。</p>
              </div>
              <button type="button" className="miduoke-icon-button" aria-label="关闭" onClick={() => setCodeModalComponent(null)}>
                <X size={18} />
              </button>
            </header>
            <pre className="miduoke-code-block">
              <code>{buildCustomerAccessSnippet(activeEntry, codeModalComponent, tenantId)}</code>
            </pre>
            <footer className="miduoke-modal-actions">
              <button type="button" className="miduoke-secondary-button" onClick={() => setCodeModalComponent(null)}>
                关闭
              </button>
              <button type="button" className="miduoke-primary-button" onClick={() => void copySnippet(buildCustomerAccessSnippet(activeEntry, codeModalComponent, tenantId))}>
                复制代码
              </button>
            </footer>
          </section>
        </div>
      ) : null}
      {previewModalComponent ? (
        <div className="miduoke-modal-backdrop" role="presentation">
          <section className="miduoke-modal miduoke-preview-modal" role="dialog" aria-modal="true" aria-label="网站客服预览">
            <header className="miduoke-modal-head">
              <div>
                <h2>网站客服预览</h2>
                <p>{previewModalComponent.style === "link" ? "链接版入口会出现在导航、按钮或落地页区域。" : "插件版入口会固定在网站右下角。"}</p>
              </div>
              <button type="button" className="miduoke-icon-button" aria-label="关闭" onClick={() => setPreviewModalComponent(null)}>
                <X size={18} />
              </button>
            </header>
            <div className="miduoke-website-preview">
              <nav>
                <strong>示例官网</strong>
                <span>首页</span>
                <span>产品</span>
                <span>服务</span>
                {previewModalComponent.style === "link" ? (
                  <button type="button" onClick={() => void startPreviewConversation()}>
                    {previewModalComponent.buttonText || "在线咨询"}
                  </button>
                ) : null}
              </nav>
              <main>
                <h3>智能客服接入演示页</h3>
                <p>这里模拟你的真实网站页面，用于确认接待组件的入口位置、按钮文案和顾客点击路径。</p>
                {previewModalComponent.style === "link" ? (
                  <button type="button" className="miduoke-preview-link-entry" onClick={() => void startPreviewConversation()}>
                    {previewModalComponent.buttonText || "在线咨询"}
                  </button>
                ) : null}
              </main>
              {previewModalComponent.style !== "link" ? (
                <div className="miduoke-preview-widget" style={{ borderColor: previewModalComponent.themeColor || "#1677ff" }}>
                  <button
                    type="button"
                    style={{ background: previewModalComponent.themeColor || "#1677ff" }}
                    onClick={() => void startPreviewConversation()}
                  >
                    <MessageCircle size={17} />
                    {previewModalComponent.buttonText || "在线咨询"}
                  </button>
                  <div>
                    <strong>{previewModalComponent.welcomeText || "您好，请问有什么可以帮您？"}</strong>
                    <span>点击按钮后进入对话工作台测试会话。</span>
                  </div>
                </div>
              ) : null}
            </div>
            {previewStartState.status !== "idle" ? (
              <p className={`miduoke-modal-status ${previewStartState.status}`}>{previewStartState.message}</p>
            ) : null}
            <footer className="miduoke-modal-actions">
              <button type="button" className="miduoke-secondary-button" onClick={() => setPreviewModalComponent(null)}>
                关闭
              </button>
              <button type="button" className="miduoke-primary-button" onClick={() => void startPreviewConversation()}>
                {previewStartState.status === "starting" ? "正在进入..." : "开始测试对话"}
              </button>
            </footer>
          </section>
        </div>
      ) : null}
      {configModalComponent ? (
        <div className="miduoke-modal-backdrop" role="presentation">
          <section className="miduoke-modal miduoke-config-modal" role="dialog" aria-modal="true" aria-label="配置网站客服">
            <header className="miduoke-modal-head">
              <div>
                <h2>配置网站客服</h2>
                <p>这些配置会用于后续写入 connector-config 的 public_config.components。</p>
              </div>
              <button type="button" className="miduoke-icon-button" aria-label="关闭" onClick={() => setConfigModalComponent(null)}>
                <X size={18} />
              </button>
            </header>
            <form className="miduoke-config-form" onSubmit={submitWebsiteConfig}>
              <label>
                <span>组件名称</span>
                <input value={configDraft.name} onChange={(event) => setConfigDraft((current) => ({ ...current, name: event.target.value }))} />
              </label>
              <label>
                <span>组件类型</span>
                <select
                  value={configDraft.componentType}
                  onChange={(event) =>
                    setConfigDraft((current) => ({ ...current, componentType: event.target.value as WebsiteComponentConfigDraft["componentType"] }))
                  }
                >
                  <option value="插件型">插件型</option>
                  <option value="链接型">链接型</option>
                </select>
              </label>
              <label>
                <span>挂载位置</span>
                <input value={configDraft.mount} onChange={(event) => setConfigDraft((current) => ({ ...current, mount: event.target.value }))} />
              </label>
              <label>
                <span>欢迎语</span>
                <input
                  value={configDraft.welcomeText}
                  onChange={(event) => setConfigDraft((current) => ({ ...current, welcomeText: event.target.value }))}
                />
              </label>
              <label>
                <span>主题色</span>
                <input
                  type="color"
                  value={configDraft.themeColor}
                  onChange={(event) => setConfigDraft((current) => ({ ...current, themeColor: event.target.value }))}
                />
              </label>
              <label>
                <span>咨询按钮文案</span>
                <input
                  value={configDraft.buttonText}
                  onChange={(event) => setConfigDraft((current) => ({ ...current, buttonText: event.target.value }))}
                />
              </label>
              <label className="wide">
                <span>允许域名</span>
                <input
                  value={configDraft.allowedOrigin}
                  placeholder="https://example.com"
                  onChange={(event) => setConfigDraft((current) => ({ ...current, allowedOrigin: event.target.value }))}
                />
              </label>
              <footer className="miduoke-modal-actions wide">
                <button type="button" className="miduoke-secondary-button" onClick={() => setConfigModalComponent(null)}>
                  取消
                </button>
                <button type="submit" className="miduoke-primary-button">
                  保存配置
                </button>
              </footer>
            </form>
          </section>
        </div>
      ) : null}
    </section>
  );

  return (
    <section id="workspace-channels" className="channel-connector-center" data-channel-connector-smoke="center" aria-label="渠道配置准备与边界说明">
      <div className="panel-heading channel-connector-heading">
        <div>
          <span className="section-kicker">配置准备与边界说明</span>
        <h2>渠道能不能接、还缺什么、谁负责下一步</h2>
          <p>这里用于整理官方接入条件和人员分工。未通过官方验证前，只能记录配置准备状态，不代表平台已经接通。</p>
        </div>
        <div className="channel-connector-summary" data-channel-current-blocker={primary.currentBlocker}>
          <span>当前主通道</span>
          <strong>{primary.name}</strong>
          <small>{readySteps}/{primary.steps.length} 项已准备 · {blockedSteps} 个阻塞</small>
        </div>
      </div>

      <div className="panel-state-row" aria-label="渠道连接器数据状态">
        <DataSourceBadge
          mode={hasToken ? "real" : "demo"}
          label={hasToken ? REAL_DATA_LABEL : PREVIEW_DATA_LABEL}
          detail={hasToken ? "读取渠道配置、入站样例和本地发送演练记录" : "仅展示官方接入路线样例"}
        />
        <DataSourceBadge
          mode={primary.currentBlocker.includes("待配置") ? "missing_config" : "real"}
          label={primary.currentBlocker.includes("待配置") ? "配置缺失" : REAL_DATA_LABEL}
          detail={primary.currentBlocker}
        />
        <DataSourceBadge
          mode="off"
          label={EXTERNAL_WRITE_OFF_LABEL}
          detail="官方验证、入站、白名单测试和审计闭环完成前不自动外发"
        />
      </div>

      <nav className="channel-layer-tabs" aria-label="渠道接入分层">
        {CHANNEL_ACCESS_LAYERS.map((layer) => (
          <button
            key={layer.id}
            type="button"
            className={activeLayer === layer.id ? "is-active" : ""}
            aria-pressed={activeLayer === layer.id}
            onClick={() => setActiveLayer(layer.id)}
          >
            <strong>{layer.label}</strong>
            <span>{layer.description}</span>
          </button>
        ))}
      </nav>

      <section
        className="channel-personnel-boundary"
        data-channel-layer="people"
        hidden={activeLayer !== "people"}
        aria-label="渠道人员配置与边界说明"
      >
        <div className="section-title-row">
          <UsersRound size={18} />
          <strong>人员配置与边界说明</strong>
          <span>配置准备，不代表平台已接通</span>
        </div>
        <p>
          这里用于试跑前明确谁负责接待、谁维护知识、谁处理运维。企业微信、微信客服、公众号、抖音、淘宝、京东、拼多多、小红书都只展示官方接入条件、所需资料、当前状态和未接通原因。
        </p>
        <div className="channel-role-grid" aria-label="渠道试跑角色配置">
          {CHANNEL_ROLE_RESPONSIBILITIES.map((item) => (
            <article key={item.role} className="channel-role-card">
              <span>{item.role}</span>
              <strong>{item.purpose}</strong>
              <small>{item.configOwner}</small>
              <em>{item.requiredBeforeTrial}</em>
            </article>
          ))}
        </div>
        <div className="channel-boundary-checklist" aria-label="官方接入条件与未接通原因">
          <div className="channel-boundary-row head">
            <span>渠道</span>
            <span>官方接入条件</span>
            <span>所需资料</span>
            <span>当前状态 / 未接通原因</span>
          </div>
          {CHANNEL_BOUNDARY_REQUIREMENTS.map((item) => (
            <div key={item.channel} className="channel-boundary-row">
              <span>
                <strong>{item.channel}</strong>
              </span>
              <span>{item.officialCondition}</span>
              <span>{item.requiredMaterials}</span>
              <span>
                <strong>{item.currentStatus}</strong>
                <small>未接通原因：{item.unfinishedReason}</small>
              </span>
            </div>
          ))}
        </div>
      </section>

      <section
        className="channel-access-route-matrix"
        data-channel-sandbox-priority="p3-06u-26g"
        hidden={activeLayer !== "boundaries"}
        aria-label="官方测试接入与 RPA 研究边界"
      >
        <div className="section-title-row">
          <ShieldCheck size={18} />
          <strong>官方测试接入优先级</strong>
          <span>RPA 只做草稿</span>
        </div>
        <p>
          正式交付只接受官方授权、服务商授权或测试白名单接入。RPA 不进入正式默认交付链，只允许读取、生成草稿、填框和证据采集；真实外发继续关闭。
        </p>
        <div className="channel-access-route-table" role="table" aria-label="渠道接入路线矩阵">
          <div className="channel-access-route-row head" role="row">
            <span>渠道</span>
            <span>正式线</span>
            <span>当前状态</span>
            <span>RPA 边界</span>
          </div>
          {CHANNEL_SANDBOX_PRIORITIES.map((item) => (
            <div className="channel-access-route-row" role="row" key={item.id} data-channel-route={item.id}>
              <span>
                <strong>{item.channel}</strong>
                <small>{item.sandboxPriority}</small>
              </span>
              <span>{item.formalPath}</span>
              <span>{item.currentStatus}</span>
              <span>{item.rpaBoundary}</span>
            </div>
          ))}
        </div>
      </section>

      <section
        className="channel-account-manager"
        data-channel-account-manager="p3-06u-26c"
        hidden={activeLayer !== "accounts"}
        aria-label="渠道账号和店铺配置"
      >
        <div className="channel-account-manager-head">
          <div>
            <span className="section-kicker">渠道账号 / 店铺管理</span>
            <h3>渠道账号 / 店铺登记</h3>
            <p>用于登记平台账号、店铺、入口、授权状态和回复模式。这里只保存低敏身份信息，真实外发继续关闭。</p>
          </div>
          <button
            type="button"
            className="ghost-button compact"
            onClick={onRefreshChannelAccounts}
            disabled={!hasToken}
            data-channel-account-refresh="p3-06u-26c"
          >
            <RefreshCw size={15} />
            刷新
          </button>
        </div>

        <div className="channel-account-layout">
          <div className="channel-account-list-card" data-channel-account-list="server">
            <div className="section-title-row">
              <Store size={18} />
              <strong>已登记账号</strong>
              <span>{channelAccountState.status === "loading" ? "刷新中" : `${channelAccounts.length} 个`}</span>
            </div>
            {channelAccounts.length > 0 ? (
              <div className="channel-account-table" role="table" aria-label="服务端渠道账号列表">
                <div className="channel-account-row head" role="row">
                  <span>平台 / 账号</span>
                  <span>店铺 / 入口</span>
                  <span>授权与接入</span>
                  <span>回复模式</span>
                </div>
                {channelAccounts.map((account) => (
                  <div key={account.id} className="channel-account-row" role="row" data-channel-account-id={account.id}>
                    <span>
                      <strong>{account.platform || formatProviderName(account.provider)}</strong>
                      <small>{account.account_name}</small>
                    </span>
                    <span>
                      <strong>{account.store_name || account.entrypoint_name || "未登记入口"}</strong>
                      <small>{account.entrypoint_name || `渠道 #${account.channel_id}`}</small>
                    </span>
                    <span>
                      <strong>{formatAuthorizationStatus(account.authorization_status)}</strong>
                      <small>{formatAccessStatus(account.access_status)} · {formatHealthStatus(account.health_status)}</small>
                    </span>
                    <span>
                      <strong>{formatReplyMode(account.reply_mode)}</strong>
                      <small>{account.last_sync_at ? `同步 ${formatShortDate(account.last_sync_at)}` : "尚未同步"}</small>
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <div className="channel-account-empty" data-channel-account-empty="true">
                <strong>{hasToken ? "尚未登记渠道账号 / 店铺" : "需要正式登录后读取渠道账号"}</strong>
                <small>
                  {hasToken
                    ? "请先选择租户渠道并保存一个账号/店铺身份；配置缺失会明确显示，不再默认伪装成真实平台账号。"
                    : "当前仅展示接入路线样例，正式配置来自 GET /api/tenants/{tenant_id}/channel-accounts。"}
                </small>
              </div>
            )}
            {getChannelAccountStateMessage(channelAccountState) ? (
              <p className={`channel-account-state-note ${channelAccountState.status}`}>{getChannelAccountStateMessage(channelAccountState)}</p>
            ) : null}
          </div>

          <form className="channel-account-form" onSubmit={submitChannelAccount} data-channel-account-form="server">
            <div className="section-title-row">
              <PlusCircle size={18} />
              <strong>登记 / 保存账号身份</strong>
              <span>{canManageConnector ? "可配置" : "只读"}</span>
            </div>
            <div className="channel-account-form-grid">
              <label>
                <span>渠道</span>
                <select
                  value={accountDraft.channelId}
                  onChange={(event) => {
                    const channel = channelById[Number(event.target.value)];
                    setAccountDraft((current) => ({
                      ...current,
                      channelId: event.target.value,
                      provider: channel?.type ?? current.provider,
                      platform: channel?.name ?? current.platform
                    }));
                  }}
                  disabled={!hasToken || !canManageConnector || availableChannels.length === 0}
                >
                  <option value="">选择租户渠道</option>
                  {availableChannels.map((channel) => (
                    <option key={channel.id} value={channel.id}>
                      {channel.name} · {channel.type}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                <span>账号名称</span>
                <input
                  value={accountDraft.accountName}
                  onChange={(event) => setAccountDraft((current) => ({ ...current, accountName: event.target.value }))}
                  placeholder="例如：万法常世AI客服测试"
                  disabled={!hasToken || !canManageConnector}
                />
              </label>
              <label>
                <span>平台</span>
                <input
                  value={accountDraft.platform}
                  onChange={(event) => setAccountDraft((current) => ({ ...current, platform: event.target.value }))}
                  placeholder="例如：微信客服 / 抖音 / 淘宝"
                  disabled={!hasToken || !canManageConnector}
                />
              </label>
              <label>
                <span>店铺 / 入口</span>
                <input
                  value={accountDraft.storeName}
                  onChange={(event) => setAccountDraft((current) => ({ ...current, storeName: event.target.value }))}
                  placeholder="例如：客服链接 / 店铺主账号"
                  disabled={!hasToken || !canManageConnector}
                />
              </label>
              <label>
                <span>入口名称</span>
                <input
                  value={accountDraft.entrypointName}
                  onChange={(event) => setAccountDraft((current) => ({ ...current, entrypointName: event.target.value }))}
                  placeholder="例如：官网浮窗 / 微信客服二维码"
                  disabled={!hasToken || !canManageConnector}
                />
              </label>
              <label>
                <span>外部账号 ID</span>
                <input
                  value={accountDraft.externalAccountId}
                  onChange={(event) =>
                    setAccountDraft((current) => ({ ...current, externalAccountId: event.target.value }))
                  }
                  placeholder="低敏公开标识，非 token"
                  disabled={!hasToken || !canManageConnector}
                />
              </label>
              <label>
                <span>授权状态</span>
                <select
                  value={accountDraft.authorizationStatus}
                  onChange={(event) =>
                    setAccountDraft((current) => ({ ...current, authorizationStatus: event.target.value }))
                  }
                  disabled={!hasToken || !canManageConnector}
                >
                  {AUTHORIZATION_OPTIONS.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                <span>接入状态</span>
                <select
                  value={accountDraft.accessStatus}
                  onChange={(event) => setAccountDraft((current) => ({ ...current, accessStatus: event.target.value }))}
                  disabled={!hasToken || !canManageConnector}
                >
                  {ACCESS_STATUS_OPTIONS.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                <span>回复模式</span>
                <select
                  value={accountDraft.replyMode}
                  onChange={(event) => setAccountDraft((current) => ({ ...current, replyMode: event.target.value }))}
                  disabled={!hasToken || !canManageConnector}
                >
                  {REPLY_MODE_OPTIONS.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                <span>健康状态</span>
                <select
                  value={accountDraft.healthStatus}
                  onChange={(event) => setAccountDraft((current) => ({ ...current, healthStatus: event.target.value }))}
                  disabled={!hasToken || !canManageConnector}
                >
                  {HEALTH_STATUS_OPTIONS.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                <span>可见范围</span>
                <input
                  value={accountDraft.visibleScope}
                  onChange={(event) => setAccountDraft((current) => ({ ...current, visibleScope: event.target.value }))}
                  placeholder="例如：测试部门 / 全部成员"
                  disabled={!hasToken || !canManageConnector}
                />
              </label>
              <label>
                <span>公开备注</span>
                <input
                  value={accountDraft.publicNote}
                  onChange={(event) => setAccountDraft((current) => ({ ...current, publicNote: event.target.value }))}
                  placeholder="不填写密钥、Cookie、Token"
                  disabled={!hasToken || !canManageConnector}
                />
              </label>
            </div>
            <div className="channel-account-form-footer">
              <small>正式平台密钥只允许进入服务端密钥管理；此表单不会保存 Secret、Token、Cookie 或个人号凭据。</small>
              <button type="submit" className="primary-button compact" disabled={!hasToken || !canManageConnector || accountSaveState.status === "saving"}>
                {accountSaveState.status === "saving" ? "保存中" : "保存账号配置"}
              </button>
            </div>
            {accountSaveState.message ? (
              <p className={`channel-account-state-note ${accountSaveState.status}`}>{accountSaveState.message}</p>
            ) : null}
          </form>
        </div>
      </section>

      <section
        className="channel-layer-panel"
        data-channel-layer="wecom"
        hidden={activeLayer !== "wecom"}
        aria-label="企业微信客服接入步骤"
      >
        <div className="channel-primary-card" data-channel-connector-primary="wecom">
          <div className="channel-primary-main">
            <div className="channel-status-title">
              <span className={`channel-status-dot ${primary.tone}`} />
              <div>
                <strong>{primary.status}</strong>
                <small>{primary.summary}</small>
              </div>
            </div>
            <div className="channel-blocker-box">
              <AlertTriangle size={18} />
              <div>
                <span>当前卡点</span>
                <strong>{primary.currentBlocker}</strong>
                <small>{primary.nextAction}</small>
              </div>
            </div>
          </div>
          <div className="channel-setup-track" role="list" aria-label="企业微信客服接入步骤">
            {primary.steps.map((step, index) => (
              <div
                key={step.label}
                className={`channel-setup-step ${step.status}`}
                role="listitem"
                data-channel-connector-step={step.label}
              >
                <span>{index + 1}</span>
                <div>
                  <strong>{step.label}</strong>
                  <small>{step.description}</small>
                  {step.evidence ? <em>{step.evidence}</em> : null}
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="channel-config-grid">
          {primary.config.map((item) => (
            <div key={item.label} className="channel-config-card" data-channel-connector-config={item.label}>
              <span>{item.label}</span>
              <strong>{item.sensitive ? "已隐藏明文" : item.value}</strong>
              <small>{item.sensitive ? `${item.status} · ${item.value}` : item.status}</small>
              <em>{item.note}</em>
            </div>
          ))}
        </div>

        <div className="channel-blocker-grid">
          <article className="channel-blocker-panel">
            <div className="section-title-row">
              <ShieldCheck size={18} />
              <strong>正式商用前置条件</strong>
            </div>
            <ul>
              {primary.blockers.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </article>
          <article className="channel-blocker-panel">
            <div className="section-title-row">
              <Route size={18} />
              <strong>后台配置位置</strong>
            </div>
            <p>{primary.officialPath}</p>
            <small>企业微信后台页面可能随版本调整，但正式接入只走官方接口、开放平台或服务商授权。</small>
          </article>
        </div>
      </section>

      <div className="channel-official-grid" data-channel-official-only="true" hidden={activeLayer !== "official"}>
        {officialOnlyConnectors.map((connector) => (
          <article key={connector.id} className="channel-official-card">
            <div className="channel-status-title">
              <span className={`channel-status-dot ${connector.tone}`} />
              <div>
                <strong>{connector.name}</strong>
                <small>{connector.status}</small>
              </div>
            </div>
            <p>{connector.summary}</p>
            <ul>
              {connector.prerequisites.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
            <em>{connector.nextAction}</em>
          </article>
        ))}
      </div>
    </section>
  );
}

function getChannelTableTitle(id: ChannelEntryId) {
  const titles: Record<ChannelEntryId, string> = {
    website: "接待组件列表",
    wechat_official: "公众号列表",
    wechat_miniapp: "微信小程序列表",
    wecom: "企业微信列表"
  };
  return titles[id];
}

function getChannelSearchPlaceholder(id: ChannelEntryId) {
  const placeholders: Record<ChannelEntryId, string> = {
    website: "请输入组件名称",
    wechat_official: "搜索公众号",
    wechat_miniapp: "搜索小程序名称",
    wecom: "搜索应用名称"
  };
  return placeholders[id];
}

function getChannelTableColumns(id: ChannelEntryId) {
  const columns: Record<ChannelEntryId, string[]> = {
    website: ["组件样式", "组件名称/类型", "挂载位置", "更新时间", "操作"],
    wechat_official: ["公众号", "账号类型", "认证状态", "粉丝数", "互动粉丝数...", "接入方式", "接入时间"],
    wechat_miniapp: ["微信小程序", "接入方式", "接入时间", "操作"],
    wecom: ["企业微信", "应用名称", "企业ID", "应用ID", "接入时间", "操作"]
  };
  return columns[id];
}

function getChannelGridTemplate(id: ChannelEntryId) {
  const templates: Record<ChannelEntryId, string> = {
    website: "170px minmax(180px, 1fr) minmax(150px, 0.8fr) 160px 250px",
    wechat_official: "180px 150px 150px 120px 120px 180px 140px",
    wechat_miniapp: "minmax(220px, 1fr) minmax(220px, 1fr) 150px 220px",
    wecom: "190px 190px 190px 130px 150px 210px"
  };
  return templates[id];
}

function getChannelAccessNotes(id: ChannelEntryId) {
  const notes: Record<ChannelEntryId, string[]> = {
    website: [],
    wechat_official: [
      "*你的公众号必须是认证过的微信订阅号或服务号，否则无法正常回复顾客对话",
      "*接入后，之前设置好的菜单、自动回复等功能仍然有效"
    ],
    wechat_miniapp: [
      "*接入前你的小程序需完成认证才能正常使用本功能",
      "*接入后，所有小程序用户的客服消息会被转发到米多客"
    ],
    wecom: []
  };
  return notes[id];
}

function getChannelGuideSteps(id: ChannelEntryId) {
  const steps: Record<ChannelEntryId, string[]> = {
    website: [
      "新建接待组件，确认组件样式和挂载位置。",
      "完成域名校验后，把代码放到网站页面。",
      "上线前先预览组件，确认按钮和聊天链接可打开。"
    ],
    wechat_official: [
      "使用扫码接入或手动填写公众号开发配置。",
      "确认公众号已认证，并拥有客服消息相关权限。",
      "接入后检查菜单、自动回复和客服消息入口。"
    ],
    wechat_miniapp: [
      "先确认小程序已完成认证并开启客服能力。",
      "通过扫码或手动方式接入小程序。",
      "在小程序页面中配置客服按钮或咨询入口。"
    ],
    wecom: [
      "绑定企业微信账号，选择扫码或手动接入。",
      "准备回调 URL、Token、EncodingAESKey 等配置。",
      "完成后测试员工消息是否能进入统一接待。"
    ]
  };
  return steps[id];
}

function getChannelApiFields(id: ChannelEntryId) {
  const fields: Record<ChannelEntryId, Array<{ label: string; value: string }>> = {
    website: [
      { label: "script_key", value: "网站组件标识" },
      { label: "allowed_origin", value: "域名白名单" },
      { label: "visitor_id", value: "访客会话 ID" },
      { label: "handoff_queue", value: "转人工队列" }
    ],
    wechat_official: [
      { label: "appid / secret", value: "公众号凭证" },
      { label: "server_url", value: "微信服务器回调 URL" },
      { label: "token / aes_key", value: "签名校验与消息解密" },
      { label: "openid", value: "客服消息收件人" }
    ],
    wechat_miniapp: [
      { label: "appid / secret", value: "小程序凭证" },
      { label: "open-type", value: "contact" },
      { label: "session-from", value: "来源透传参数" },
      { label: "message_card", value: "show-message-card / path" }
    ],
    wecom: [
      { label: "corp_id / secret", value: "企业与微信客服凭证" },
      { label: "callback_url", value: "API 接收消息地址" },
      { label: "token / aes_key", value: "签名校验与消息解密" },
      { label: "kf_id", value: "客服账号 / 会话分配" }
    ]
  };
  return fields[id];
}

function getChannelBackendHooks(id: ChannelEntryId) {
  const hooks: Record<ChannelEntryId, string[]> = {
    website: ["POST /api/channels/website/widgets", "POST /api/conversations/visitor"],
    wechat_official: ["POST /api/channels/wechat-official/callback", "POST /api/channels/wechat-official/custom-send"],
    wechat_miniapp: ["POST /api/channels/wechat-miniapp/contact", "POST /api/channels/wechat-miniapp/message-push"],
    wecom: ["POST /api/channels/wecom/callback", "POST /api/channels/wecom/kf/sync"]
  };
  return hooks[id];
}

const DEFAULT_CUSTOMER_PREVIEW_MESSAGES: CustomerPreviewMessage[] = [
  { id: "welcome", role: "agent", text: "您好，这里是在线客服，请问有什么可以帮您？", time: "09:30" },
  { id: "sample", role: "customer", text: "我想了解一下服务怎么接入。", time: "09:31" },
  { id: "reply", role: "agent", text: "可以的，我们先确认接入渠道，再进入人工或自动接待测试。", time: "09:31" }
];

const CHANNEL_ENTRY_DEFINITIONS: ChannelEntryDefinition[] = [
  {
    id: "website",
    label: "网站",
    subtitle: "网页插件 / 聊天链接",
    description:
      "*客户与企业通过接待组件建立联系。通过接待组件，客户可快速向客服发起咨询，企业可把接待组件挂载在不同渠道来全面触达客户。",
    componentQuota: 1,
    setupHint: "适合先做顾客端前端调试，后续可接入真实网站脚本。",
    primaryAction: "新建接待组件",
    secondaryAction: "域名校验设置",
    components: [
      {
        id: "website-widget",
        name: "网页插件",
        componentType: "插件型",
        style: "widget",
        mount: "官网右下角",
        status: "enabled",
        updatedAt: "2026-07-07 09:30",
        description: "网页右下角浮窗，顾客可直接打开聊天。"
      },
      {
        id: "website-link",
        name: "聊天链接",
        componentType: "链接型",
        style: "link",
        mount: "导航 / 按钮 / 落地页",
        status: "enabled",
        updatedAt: "2026-07-07 09:30",
        description: "可复制到按钮、菜单或二维码里的顾客咨询链接。"
      }
    ]
  },
  {
    id: "wechat_official",
    label: "微信公众号",
    subtitle: "菜单入口 / 客服消息",
    description: "通过公众号菜单、自动回复或客服消息入口承接客户咨询；正式接入需要公众号后台开发配置和消息权限。",
    componentQuota: 2,
    setupHint: "当前先预览顾客从公众号菜单进入咨询的效果。",
    primaryAction: "新建公众号入口",
    secondaryAction: "开发配置",
    components: [
      {
        id: "official-menu",
        name: "公众号菜单入口",
        componentType: "菜单型",
        style: "menu",
        mount: "公众号底部菜单",
        status: "draft",
        updatedAt: "2026-07-07 09:30",
        description: "顾客点击公众号菜单后打开客服咨询页。"
      },
      {
        id: "official-keyword",
        name: "关键词咨询链接",
        componentType: "链接型",
        style: "link",
        mount: "自动回复 / 图文",
        status: "planned",
        updatedAt: "2026-07-07 09:30",
        description: "在自动回复或图文里放置咨询入口。"
      }
    ]
  },
  {
    id: "wechat_miniapp",
    label: "微信小程序",
    subtitle: "小程序客服按钮 / 页面入口",
    description: "把客服入口放入小程序页面或订单/服务流程中，便于顾客在微信内直接发起咨询。",
    componentQuota: 2,
    setupHint: "当前先模拟小程序页面中的客服按钮。",
    primaryAction: "新建小程序入口",
    secondaryAction: "页面配置",
    components: [
      {
        id: "miniapp-service-button",
        name: "客服按钮",
        componentType: "小程序组件",
        style: "miniapp",
        mount: "我的 / 订单 / 售后页",
        status: "draft",
        updatedAt: "2026-07-07 09:30",
        description: "顾客在小程序内点击客服按钮进入咨询。"
      },
      {
        id: "miniapp-page-entry",
        name: "咨询页面入口",
        componentType: "页面入口",
        style: "link",
        mount: "活动页 / 帮助中心",
        status: "planned",
        updatedAt: "2026-07-07 09:30",
        description: "把咨询入口嵌入小程序业务页面。"
      }
    ]
  },
  {
    id: "wecom",
    label: "企业微信",
    subtitle: "微信客服链接 / 二维码",
    description: "通过企业微信客服链接、二维码或微信内入口承接客户咨询；正式接入需要回调 URL、Token 和 EncodingAESKey。",
    componentQuota: 2,
    setupHint: "当前先模拟客户从企业微信客服链接进入咨询。",
    primaryAction: "新建企微入口",
    secondaryAction: "回调配置",
    components: [
      {
        id: "wecom-service-link",
        name: "客服链接",
        componentType: "链接型",
        style: "link",
        mount: "微信内链接 / 官网按钮",
        status: "draft",
        updatedAt: "2026-07-07 09:30",
        description: "顾客点击链接进入企业微信客服会话。"
      },
      {
        id: "wecom-qrcode",
        name: "客服二维码",
        componentType: "二维码型",
        style: "qrcode",
        mount: "门店 / 海报 / 官网",
        status: "planned",
        updatedAt: "2026-07-07 09:30",
        description: "顾客扫码进入企业微信客服。"
      }
    ]
  }
];

function ChannelEntryIcon({ id }: { id: ChannelEntryId }) {
  if (id === "website") {
    return <Globe2 size={16} />;
  }
  if (id === "wechat_miniapp") {
    return <Smartphone size={16} />;
  }
  if (id === "wecom") {
    return <Building2 size={16} />;
  }
  return <MessageCircle size={16} />;
}

function ChannelComponentPreviewIcon({ style }: { style: ChannelAccessComponent["style"] }) {
  const icon =
    style === "widget" ? <Code2 size={20} /> :
    style === "miniapp" ? <Smartphone size={20} /> :
    style === "qrcode" ? <Copy size={20} /> :
    style === "menu" ? <MessageCircle size={20} /> :
    <Link2 size={20} />;
  return <i className={`channel-component-icon ${style}`}>{icon}</i>;
}

function formatChannelComponentStatus(status: ChannelAccessComponent["status"]) {
  const labels: Record<ChannelAccessComponent["status"], string> = {
    enabled: "开启",
    draft: "草稿",
    planned: "待配置"
  };
  return labels[status];
}

function normalizeChannelEntryId(value: string | undefined): ChannelEntryId {
  return CHANNEL_ENTRY_DEFINITIONS.some((entry) => entry.id === value) ? (value as ChannelEntryId) : "website";
}

function buildCustomerAccessSnippet(entry: ChannelEntryDefinition, component?: ChannelAccessComponent, tenantId?: string | number) {
  const componentId = component?.id ?? "customer-entry";
  if (entry.id === "website") {
    return `<script type="text/javascript">
  window._WANFA = window._WANFA || function () { (_WANFA.a = _WANFA.a || []).push(arguments); };
  _WANFA("cptid", "${componentId}");
  _WANFA("tenantId", "${tenantId ?? 1}");
  _WANFA("domain", "web.zixunkefu.net");
  _WANFA("apiBase", "https://web.zixunkefu.net");
  _WANFA("channel", "website");
  _WANFA("mode", "${component?.style === "link" ? "link" : "widget"}");
  _WANFA("position", "${component?.position || "right-bottom"}");
  _WANFA("buttonText", "${component?.buttonText || "在线咨询"}");
  (function (w, d, q, j, s) {
    j = d.createElement(q), s = d.getElementsByTagName(q)[0];
    j.async = true;
    j.charset = "UTF-8";
    j.src = ("https:" == document.location.protocol ? "https://" : "http://") + "web.zixunkefu.net/Web/js/customer-widget.js?_=t";
    s.parentNode.insertBefore(j, s);
  })(window, document, "script");
</script>`;
  }
  if (entry.id === "wechat_miniapp") {
    return `<button open-type="contact"
  session-from="${componentId}"
  show-message-card="true">
  在线咨询
</button>`;
  }
  return `https://web.wanfa.local/client/chat?channel=${entry.id}&component=${componentId}`;
}

function createWebsiteConfigDraft(component?: ChannelAccessComponent): WebsiteComponentConfigDraft {
  return {
    name: component?.name ?? "网页插件",
    componentType: component?.componentType === "链接型" ? "链接型" : "插件型",
    mount: component?.mount ?? "官网右下角",
    welcomeText: component?.welcomeText ?? "您好，请问有什么可以帮您？",
    themeColor: component?.themeColor ?? "#1677ff",
    buttonText: component?.buttonText ?? "在线咨询",
    allowedOrigin: component?.allowedOrigin ?? "https://example.com"
  };
}

function formatChannelComponentUpdatedAt(value: Date) {
  const pad = (item: number) => String(item).padStart(2, "0");
  return `${value.getFullYear()}-${pad(value.getMonth() + 1)}-${pad(value.getDate())} ${pad(value.getHours())}:${pad(value.getMinutes())}`;
}

function getChannelAccountStateMessage(state: ChannelAccountState) {
  return "message" in state ? state.message : "";
}

const CHANNEL_ACCESS_LAYERS: Array<{ id: ChannelAccessLayer; label: string; description: string }> = [
  { id: "accounts", label: "账号与入口", description: "登记平台账号、店铺、入口和回复模式" },
  { id: "people", label: "人员与边界", description: "接待、知识、运维角色和未接通原因" },
  { id: "wecom", label: "企业微信步骤", description: "查看当前主通道的配置阻塞" },
  { id: "official", label: "其它官方平台", description: "公众号、电商和内容平台授权前置" },
  { id: "boundaries", label: "接入边界", description: "官方测试接入与 RPA 研究边界" }
];

const CHANNEL_ROLE_RESPONSIBILITIES: ChannelRoleResponsibility[] = [
  {
    role: "负责人",
    purpose: "确认试跑范围、渠道优先级和外发边界",
    configOwner: "通常由老板、运营负责人或项目负责人担任",
    requiredBeforeTrial: "必须确认真实外发关闭、客户资料已脱敏、试跑结果不作为正式签收"
  },
  {
    role: "接待人员",
    purpose: "处理转人工会话和客户追问",
    configOwner: "可按门店、店铺、客服小组或班次配置",
    requiredBeforeTrial: "必须知道哪些情况要接管，以及接管后如何记录处理结果"
  },
  {
    role: "管理员",
    purpose: "管理账号、备份、诊断包、更新包和本地启动",
    configOwner: "建议由客户侧懂电脑的固定人员负责",
    requiredBeforeTrial: "必须保管本地负责人账号，不能使用默认密码或共享密码"
  },
  {
    role: "知识维护人",
    purpose: "维护业务对象、标准问答、流程政策和禁用承诺",
    configOwner: "通常由熟悉产品、售后、课程或门店流程的人负责",
    requiredBeforeTrial: "必须能补充缺失资料，并复核系统给出的知识缺口"
  },
  {
    role: "运维联系人",
    purpose: "在系统异常、命中率下降或升级前后配合上传诊断包",
    configOwner: "可以和管理员同一人，也可以是我方售后对接人",
    requiredBeforeTrial: "必须清楚诊断包不包含密钥、客户原文和平台消息正文"
  }
];

const CHANNEL_BOUNDARY_REQUIREMENTS: ChannelBoundaryRequirement[] = [
  {
    channel: "企业微信 / 微信客服",
    officialCondition: "企业微信后台应用权限、客服账号、回调地址、Token 和 EncodingAESKey。",
    requiredMaterials: "企业主体、接待人员、客服链接、测试白名单、官方后台截图。",
    currentStatus: "配置准备中",
    unfinishedReason: "需要客户主体后台授权、可信公网地址和验签解密闭环。"
  },
  {
    channel: "微信公众号",
    officialCondition: "公众号开发配置、消息加解密、客服消息权限和服务号能力。",
    requiredMaterials: "公众号主体、开发者权限、测试号或服务号、消息权限说明。",
    currentStatus: "未接通",
    unfinishedReason: "尚未提供公众号后台权限和测试消息回调条件。"
  },
  {
    channel: "抖音 / 抖店",
    officialCondition: "抖音开放平台、抖店或飞鸽官方能力，或服务商授权。",
    requiredMaterials: "店铺主体、应用权限包、客服消息权限、服务商授权材料。",
    currentStatus: "未接通",
    unfinishedReason: "尚未确认官方消息接口权限，不使用网页私信模拟发送。"
  },
  {
    channel: "淘宝 / 天猫",
    officialCondition: "开放平台、店铺授权、服务市场或官方客服机器人能力。",
    requiredMaterials: "店铺授权、应用权限、客服机器人权限、测试订单或测试会话。",
    currentStatus: "未接通",
    unfinishedReason: "尚未取得店铺授权和可验收的官方消息接口。"
  },
  {
    channel: "京东",
    officialCondition: "京东开放平台或服务商授权的客服相关接口。",
    requiredMaterials: "店铺主体、开放平台应用、客服权限、测试白名单。",
    currentStatus: "未接通",
    unfinishedReason: "尚未完成平台权限确认和回执审计设计。"
  },
  {
    channel: "拼多多",
    officialCondition: "拼多多开放平台、店铺授权或服务市场能力。",
    requiredMaterials: "店铺授权、消息权限、客服工具权限、测试场景。",
    currentStatus: "未接通",
    unfinishedReason: "尚未取得官方自动回复接口验收条件。"
  },
  {
    channel: "小红书",
    officialCondition: "小红书开放平台、商业私信工具或官方服务商授权。",
    requiredMaterials: "企业主体、账号权限、私信工具权限、官方授权说明。",
    currentStatus: "未接通",
    unfinishedReason: "尚未确认官方消息能力，不使用 Cookie 复用或账号托管。"
  }
];

const AUTHORIZATION_OPTIONS = [
  { value: "not_configured", label: "未配置" },
  { value: "sandbox_configuring", label: "配置准备中" },
  { value: "official_authorized", label: "官方资料已登记（待验证）" },
  { value: "service_provider_authorized", label: "服务商资料已登记（待验证）" },
  { value: "blocked", label: "授权阻断" }
];

const ACCESS_STATUS_OPTIONS = [
  { value: "planned", label: "待配置" },
  { value: "callback_pending", label: "待回调验证" },
  { value: "sandbox_configuring", label: "配置准备中" },
  { value: "active", label: "可进入测试" },
  { value: "disabled", label: "已停用" },
  { value: "rpa_research_only", label: "仅研究" }
];

const REPLY_MODE_OPTIONS = [
  { value: "draft_only", label: "只生成本地建议" },
  { value: "human_review_first", label: "人工接管优先" },
  { value: "auto_with_handoff", label: "授权验收后自动接待" },
  { value: "auto_reply", label: "授权验收后自动接待" },
  { value: "research_draft_only", label: "仅内部研究建议" }
];

const HEALTH_STATUS_OPTIONS = [
  { value: "unknown", label: "待确认" },
  { value: "configuring", label: "配置中" },
  { value: "healthy", label: "人工记录正常" },
  { value: "degraded", label: "需处理" },
  { value: "blocked", label: "阻断" }
];

const CHANNEL_SANDBOX_PRIORITIES: ChannelSandboxPriority[] = [
  {
    id: "wecom",
    channel: "企业微信 / 微信客服",
    formalPath: "第一优先级：官方回调、URL 验证、AES 解密、入站验签、白名单发送。",
    currentStatus: "测试接入优先，真实外发继续关闭。",
    sandboxPriority: "先做单渠道官方测试接入",
    rpaBoundary: "不使用个人微信外挂、非官方插件、群控或模拟点击。"
  },
  {
    id: "official-account",
    channel: "微信公众号",
    formalPath: "第二优先级：公众号后台开发配置、消息加解密、客服消息权限。",
    currentStatus: "待官方测试号或服务号权限。",
    sandboxPriority: "企业微信稳定后再推进",
    rpaBoundary: "不模拟个人微信聊天窗口，不托管个人号。"
  },
  {
    id: "douyin",
    channel: "抖音 / 抖店",
    formalPath: "只走抖音开放平台、抖店/飞鸽官方能力或服务商授权。",
    currentStatus: "未接入，待权限包确认。",
    sandboxPriority: "确认官方消息接口后再测试接入",
    rpaBoundary: "网页私信只能做 draft-only 研究，不能写成商家客服接通。"
  },
  {
    id: "xiaohongshu",
    channel: "小红书",
    formalPath: "只走开放平台、商业私信工具或官方服务商授权。",
    currentStatus: "未接入，待主体与权限确认。",
    sandboxPriority: "低于微信和抖音",
    rpaBoundary: "不使用账号托管、Cookie 复用或后台模拟发送。"
  },
  {
    id: "ecommerce",
    channel: "淘宝 / 天猫 / 京东 / 拼多多",
    formalPath: "只走开放平台、店铺授权、服务市场或客服机器人官方包。",
    currentStatus: "未接入，逐平台验收。",
    sandboxPriority: "先选一个真实试点店铺",
    rpaBoundary: "商家后台 RPA 只允许草稿和证据采集，不默认点击发送。"
  }
];

function formatProviderName(value: string) {
  const labels: Record<string, string> = {
    wecom: "微信客服",
    official_account: "公众号",
    douyin: "抖音",
    taobao: "淘宝",
    jd: "京东",
    pdd: "拼多多",
    website: "官网"
  };
  return labels[value] ?? (value || "未登记平台");
}

function formatAuthorizationStatus(value: string) {
  return AUTHORIZATION_OPTIONS.find((item) => item.value === value)?.label ?? (value || "未配置");
}

function formatAccessStatus(value: string) {
  return ACCESS_STATUS_OPTIONS.find((item) => item.value === value)?.label ?? (value || "待配置");
}

function formatReplyMode(value: string) {
  return REPLY_MODE_OPTIONS.find((item) => item.value === value)?.label ?? (value || "只生成草稿");
}

function formatHealthStatus(value: string) {
  return HEALTH_STATUS_OPTIONS.find((item) => item.value === value)?.label ?? (value || "待确认");
}

function formatShortDate(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit"
  });
}

function buildChannelConnectorCards({
  reviewItems,
  outboxDrafts,
  failureReviews,
  deliveryJobs,
  workerRun,
  hasToken,
  canManageConnector
}: {
  reviewItems: HumanReviewInboxItem[];
  outboxDrafts: OutboxDraft[];
  failureReviews: DeliveryFailureReview[];
  deliveryJobs: OutboxDeliveryJob[];
  workerRun: TrustedInboundWorkerRun | null;
  hasToken: boolean;
  canManageConnector: boolean;
}): ChannelConnectorCard[] {
  const inboundProcessed = Boolean(workerRun && workerRun.processed > 0);
  const inboundSucceeded = Boolean(workerRun && workerRun.succeeded > 0);
  const aiDraftGenerated = reviewItems.length > 0 || outboxDrafts.length > 0;
  const humanReviewEntered = reviewItems.length > 0;
  const whitelistSendPassed = deliveryJobs.some((job) => job.status === "succeeded" && !job.external_write_requested);
  const blockedJobCount = deliveryJobs.filter((job) =>
    ["blocked", "dead_letter", "dead_lettered", "failed"].includes(job.status)
  ).length;
  const failureCount = failureReviews.filter((item) => item.status === "open").length;
  const callbackVerified = inboundSucceeded;
  const callbackBlocker = callbackVerified ? "等待白名单发送测试" : "回调 URL 待配置";

  const wecom: ChannelConnectorCard = {
    id: "wecom-servicer",
    name: "企业微信 / 微信客服",
    category: "第一优先级",
    status: callbackVerified ? "入站链路已产生样例" : "回调 URL 待配置",
    tone: callbackVerified ? "warning" : "urgent",
    summary: "用于微信内客服入口、客服链接或二维码。当前只进入转人工和待确认回复流程，不自动写回外部平台。",
    currentBlocker: callbackBlocker,
    officialPath: "企业微信管理后台 -> 应用管理 -> 微信客服 -> 可调用接口的应用 -> 选择企业内部开发或授权应用后配置回调。",
    nextAction: callbackVerified
      ? "继续做白名单发送测试，确认访问凭证、可信 IP、外发开关和转人工放行都成立。"
      : "先准备公网 HTTPS 回调地址，再在企业微信后台填写 URL、Token、EncodingAESKey 并通过 URL 验证。",
    steps: [
      {
        label: "未配置",
        description: "系统默认关闭真实外发，未完成官方接入前只做内部草稿和转人工确认。",
        status: "done",
        evidence: "外发门禁关闭"
      },
      {
        label: "已创建客服账号",
        description: "在企业微信后台创建微信客服账号，并确认名称、头像和可见范围。",
        status: "done",
        evidence: "后台人工确认"
      },
      {
        label: "已绑定接待人员",
        description: "把接待人员绑定到客服账号，避免客户进入后无人兜底。",
        status: "done",
        evidence: "需客户后台确认"
      },
      {
        label: "已获取链接/二维码",
        description: "获得客服链接或二维码，后续用于个人微信测试入站。",
        status: "done",
        evidence: "仅用于白名单测试"
      },
      {
        label: "回调 URL 待配置",
        description: "把我们提供的公网 HTTPS 回调地址填入企业微信后台。",
        status: callbackVerified ? "done" : "blocked",
        evidence: callbackVerified ? "已有入站处理记录" : "缺公网 HTTPS / URL 验证"
      },
      {
        label: "URL 验证通过",
        description: "平台会向 URL 发起验证请求，后端必须完成签名校验、AES 解密和 XML 解析。",
        status: callbackVerified ? "done" : "pending",
        evidence: callbackVerified ? `worker 成功 ${workerRun?.succeeded ?? 0} 条` : "待官方回调验证"
      },
      {
        label: "已收到入站消息",
        description: "用个人微信打开客服链接发测试消息，系统应记录可信入站消息。",
        status: inboundProcessed ? "done" : "pending",
        evidence: workerRun ? `处理 ${workerRun.processed} 条` : "待个人微信白名单测试"
      },
      {
        label: "已生成 AI 草稿",
        description: "消息进入模型路由和知识检索后，只生成内部草稿，不直接发送。",
        status: aiDraftGenerated ? "done" : "pending",
        evidence: aiDraftGenerated ? `草稿/审核 ${reviewItems.length + outboxDrafts.length} 条` : "待入站消息触发"
      },
      {
        label: "已进入转人工",
        description: "草稿进入接待台，由坐席确认事实、语气和风险。",
        status: humanReviewEntered ? "done" : "pending",
        evidence: humanReviewEntered ? `转人工 ${reviewItems.length} 条` : "待转人工任务生成"
      },
      {
        label: "白名单发送测试通过",
        description: "只对测试白名单执行发送链路验证；正式客户外发需单独授权。",
        status: whitelistSendPassed ? "done" : "pending",
        evidence: whitelistSendPassed ? "已有内部发送演练记录" : `${blockedJobCount + failureCount} 个异常/阻断待处理`
      }
    ],
    config: [
      {
        label: "公网 HTTPS 回调 URL",
        status: callbackVerified ? "已产生入站样例" : "待配置",
        value: "https://<已备案域名>/api/channels/wecom/callback",
        note: "本地公网隧道只适合测试；正式商用建议使用已备案域名和稳定云服务。"
      },
      {
        label: "Token",
        status: "只显示配置状态",
        value: "secret://channel/wecom/token",
        note: "Token 与企业微信后台保持一致，前端不展示明文。",
        sensitive: true
      },
      {
        label: "EncodingAESKey",
        status: "只显示配置状态",
        value: "secret://channel/wecom/aes-key",
        note: "用于消息加解密，必须写入环境变量或密钥管理服务。",
        sensitive: true
      },
      {
        label: "可信 IP",
        status: hasToken && canManageConnector ? "待客户后台放行" : "需管理员处理",
        value: "服务器固定出口 IP",
    note: "调用企业微信服务端能力时通常需要配置可信 IP；本地电脑临时 IP 不适合正式商用。"
      }
    ],
    blockers: [
      "中国大陆正式云部署通常需要已备案域名承载公网 HTTPS 回调。",
      "未配置可信 IP 时，自建应用无法稳定调用企业微信服务端能力。",
      "Token、EncodingAESKey、Secret 只能写入服务端环境变量或密钥管理，不能放到前端。",
      "URL 验证、AES 解密、XML 解析、入站幂等和转人工确认全部通过前，不允许自动真实外发。",
      "白名单测试通过也不等于全量客户自动回复上线。正式开关需要客户书面授权和回滚方案。"
    ],
    prerequisites: []
  };

  const officialOnly = [
    {
      id: "wechat-official-account",
      name: "微信公众号",
      summary: "适合服务号消息、菜单入口和模板/客服能力。需要公众号后台权限和官方开发配置。",
      prerequisites: ["公众号主体与业务主体一致", "开发者配置、服务器地址和消息加解密完成", "客服消息能力和服务类目符合平台规则"],
      nextAction: "先拿公众号后台管理员权限和测试号，不使用个人微信外挂。"
    },
    {
      id: "douyin-shop",
      name: "抖音 / 抖店",
      summary: "适合电商售前售后，但必须确认抖店开放平台、飞鸽/IM 能力和服务商授权范围。",
      prerequisites: ["店铺主体认证", "开放平台应用或服务商授权", "客服消息接口权限包确认"],
      nextAction: "先确认开放平台权限和服务商合同，再做测试接入。"
    },
    {
      id: "xiaohongshu",
      name: "小红书",
      summary: "品牌私信和店铺咨询能力受平台开放范围影响，不能用模拟点击或账号托管替代接口。",
      prerequisites: ["企业号或店铺官方权限", "开放接口或服务商路径确认", "内容合规和人工兜底策略"],
      nextAction: "先确认官方接口是否对当前主体开放。"
    },
    {
      id: "taobao-tmall",
      name: "淘宝 / 天猫",
      summary: "需要走淘宝开放平台、店铺授权和消息/订单相关权限，不把商家后台 RPA 当正式能力。",
      prerequisites: ["店铺授权", "开放平台应用审核", "订单、售后、客服消息权限范围确认"],
      nextAction: "先按店铺主体申请开放平台应用或服务商接入。"
    },
    {
      id: "jd-pdd",
      name: "京东 / 拼多多",
      summary: "电商客服强依赖平台授权、类目权限和服务商生态；正式上线前需单平台逐个验收。",
      prerequisites: ["店铺主体认证", "官方接口或服务商授权", "消息、订单、售后接口权限确认"],
      nextAction: "先选一个真实试点店铺，不同时铺开多个平台。"
    }
  ];

  return [
    wecom,
    ...officialOnly.map<ChannelConnectorCard>((item) => ({
      ...item,
      category: "官方授权待接入",
      status: "未接入",
      tone: "muted",
      currentBlocker: "待官方授权",
      officialPath: "对应平台开放平台 / 商家后台 / 服务商授权后台。",
      steps: [
        {
          label: "未配置",
          description: "尚未完成官方授权和接口权限确认。",
          status: "current"
        },
        {
          label: "官方授权",
          description: "获取平台开放平台应用、店铺授权或服务商授权。",
          status: "pending"
        },
        {
          label: "测试入站",
          description: "先验证入站消息、幂等和转人工确认。",
          status: "pending"
        },
        {
          label: "白名单发送",
          description: "只在平台允许的测试范围内验证发送。",
          status: "pending"
        }
      ],
      config: [],
      blockers: []
    }))
  ];
}
