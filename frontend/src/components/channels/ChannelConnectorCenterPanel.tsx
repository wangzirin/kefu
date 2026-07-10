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
import type { Dispatch, FormEvent, SetStateAction } from "react";

import type {
  Channel,
  ChannelAccount,
  ChannelAccountPayload,
  ChannelConnectorAuthorization,
  ChannelConnectorConfig,
  ChannelConnectorSecretStatus,
  ChannelConnectorVerification,
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
type ChannelConnectMode = "qr" | "manual";

type ChannelAccountState =
  | { status: "idle"; message: string; channels: Channel[]; accounts: ChannelAccount[] }
  | { status: "loading"; channels: Channel[]; accounts: ChannelAccount[] }
  | { status: "ready"; channels: Channel[]; accounts: ChannelAccount[] }
  | { status: "error"; message: string; channels: Channel[]; accounts: ChannelAccount[] };

type ChannelConnectorSelfServiceState = {
  status: "idle" | "loading" | "ready" | "error";
  message: string;
  config: ChannelConnectorConfig | null;
  authorization: ChannelConnectorAuthorization | null;
  secretStatus: ChannelConnectorSecretStatus | null;
  verification: ChannelConnectorVerification | null;
};

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

type ChannelEntryId = "website" | "wechat_kf" | "wecom" | "wechat_official" | "wechat_miniapp";

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
  account?: ChannelAccount;
  channelType?: string;
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
  connectModes: Array<"qr" | "manual">;
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

type ManualConnectorDraft = Record<string, string>;
interface ManualConnectorField {
  name: string;
  label: string;
  placeholder: string;
  kind: "public" | "secret";
  required?: boolean;
  readonly?: boolean;
  readonlyValue?: string;
  systemGenerated?: boolean;
  secretKey?: "token" | "encoding_aes_key" | "app_secret" | "open_kfid" | "webhook_signing_secret";
}

export function ChannelConnectorCenterPanel({
  selectedChannelId,
  reviewItems,
  outboxDrafts,
  failureReviews,
  deliveryJobs,
  workerRun,
  channelAccountState,
  connectorState,
  hasToken,
  canManageConnector,
  onConfigureChannelAccount,
  onCreateTenantChannel,
  onDeleteChannelAccount,
  onConfigureConnector,
  onStartAuthorization,
  onSaveSecrets,
  onDeleteSecrets,
  onVerifyConnector,
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
  connectorState?: ChannelConnectorSelfServiceState;
  hasToken: boolean;
  canManageConnector: boolean;
  onConfigureChannelAccount: (channelId: number, payload: ChannelAccountPayload) => Promise<ChannelAccount>;
  onCreateTenantChannel?: (payload: { type: string; name: string; reply_mode?: string; status?: string }) => Promise<Channel>;
  onDeleteChannelAccount?: (accountId: number) => Promise<unknown>;
  onConfigureConnector?: (channelId: number, provider: string, publicConfig?: Record<string, unknown>) => Promise<ChannelConnectorConfig>;
  onStartAuthorization?: (channelId: number, provider: string, connectMode: "qr" | "manual") => Promise<ChannelConnectorAuthorization>;
  onSaveSecrets?: (channelId: number, secrets: Record<string, string>) => Promise<ChannelConnectorSecretStatus>;
  onDeleteSecrets?: (channelId: number) => Promise<ChannelConnectorSecretStatus>;
  onVerifyConnector?: (channelId: number) => Promise<ChannelConnectorVerification>;
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
  const [secretDraft, setSecretDraft] = useState({
    token: "",
    encodingAesKey: "",
    appSecret: "",
    openKfid: "",
    webhookSigningSecret: ""
  });
  const [manualConnectorDraft, setManualConnectorDraft] = useState<ManualConnectorDraft>({});
  const [wechatKfManualStep, setWechatKfManualStep] = useState<1 | 2 | 3>(1);
  const [connectorActionState, setConnectorActionState] = useState<{ status: "idle" | "saving" | "success" | "error"; message: string }>({
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
  const [connectorGuide, setConnectorGuide] = useState<{ mode: ChannelConnectMode; component: ChannelAccessComponent } | null>(null);
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

  async function submitConnectorConfig(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!accountDraft.channelId) {
      setConnectorActionState({ status: "error", message: "请先选择租户渠道。" });
      return;
    }
    if (!onConfigureConnector) {
      setConnectorActionState({ status: "error", message: "当前页面未接入连接器配置接口。" });
      return;
    }
    setConnectorActionState({ status: "saving", message: "正在保存连接器配置..." });
    try {
      const provider = normalizeProviderForChannelEntry(accountDraft.provider || activeEntry.id);
      await onConfigureConnector(Number(accountDraft.channelId), provider);
      setConnectorActionState({ status: "success", message: "连接器已保存；默认仍只生成草稿或入站，不开启真实外发。" });
    } catch (error) {
      const message = error instanceof Error ? error.message : "保存连接器失败";
      setConnectorActionState({ status: "error", message });
    }
  }

  async function saveConnectorSecrets() {
    if (!accountDraft.channelId || !onSaveSecrets) {
      setConnectorActionState({ status: "error", message: "请先选择租户渠道并保存连接器。" });
      return;
    }
    setConnectorActionState({ status: "saving", message: "正在保存密钥..." });
    try {
      const secrets: Record<string, string> = {
        token: secretDraft.token,
        encoding_aes_key: secretDraft.encodingAesKey,
        app_secret: secretDraft.appSecret,
        open_kfid: secretDraft.openKfid,
        webhook_signing_secret: secretDraft.webhookSigningSecret
      };
      await onSaveSecrets(Number(accountDraft.channelId), secrets);
      setSecretDraft({ token: "", encodingAesKey: "", appSecret: "", openKfid: "", webhookSigningSecret: "" });
      setConnectorActionState({ status: "success", message: "密钥已保存，页面不会回显明文。" });
    } catch (error) {
      const rawMessage = error instanceof Error ? error.message : "保存密钥失败";
      const message = rawMessage.includes("404")
        ? "未找到该渠道连接器。请先点击“手动接入”创建连接器，再保存 Token 和 EncodingAESKey。"
        : rawMessage;
      setConnectorActionState({ status: "error", message });
    }
  }

  function buildManualPublicConfig(entryId: ChannelEntryId, channelId: string | number = accountDraft.channelId || "{channel_id}") {
    const fields = getManualConnectorFields(entryId, channelId);
    const result: Record<string, unknown> = {
      self_service_configured: true,
      external_write: "disabled",
      configured_from: "manual_connector_wizard",
      manual_connect_mode: entryId
    };
    fields
      .filter((field) => field.kind === "public")
      .forEach((field) => {
        result[field.name] = field.readonly ? field.readonlyValue ?? "" : (manualConnectorDraft[field.name] ?? "").trim();
      });
    return result;
  }

  function buildManualSecrets(entryId: ChannelEntryId, channelId: string | number = accountDraft.channelId || "{channel_id}") {
    const fields = getManualConnectorFields(entryId, channelId);
    const result: Record<string, string> = {};
    fields
      .filter((field) => field.kind === "secret")
      .forEach((field) => {
        if (field.secretKey === "token") {
          result.token = secretDraft.token;
        } else if (field.secretKey === "encoding_aes_key") {
          result.encoding_aes_key = secretDraft.encodingAesKey;
        } else if (field.secretKey === "app_secret") {
          result.app_secret = secretDraft.appSecret;
        } else if (field.secretKey === "open_kfid") {
          result.open_kfid = secretDraft.openKfid;
        } else if (field.secretKey === "webhook_signing_secret") {
          result.webhook_signing_secret = secretDraft.webhookSigningSecret;
        }
      });
    return result;
  }

  async function ensureTenantChannelForEntry(entryId: ChannelEntryId): Promise<number | null> {
    if (accountDraft.channelId) {
      return Number(accountDraft.channelId);
    }
    const preferred = findPreferredTenantChannel(entryId);
    if (preferred) {
      setAccountDraft((current) => ({ ...current, channelId: String(preferred.id) }));
      return preferred.id;
    }
    if (!onCreateTenantChannel) {
      setConnectorActionState({ status: "error", message: "当前页面未接入自动创建渠道接口，请先创建租户渠道。" });
      return null;
    }
    const provider = normalizeProviderForChannelEntry(entryId);
    setConnectorActionState({ status: "saving", message: `正在创建${activeEntry.label}渠道...` });
    const channel = await onCreateTenantChannel({
      type: provider,
      name: activeEntry.label,
      reply_mode: "assist",
      status: "planned"
    });
    setAccountDraft((current) => ({
      ...current,
      channelId: String(channel.id),
      provider,
      platform: activeEntry.label,
      storeName: current.storeName || activeEntry.label
    }));
    return channel.id;
  }

  async function saveManualConnectorAndVerify() {
    if (!onConfigureConnector || !onSaveSecrets || !onVerifyConnector) {
      setConnectorActionState({ status: "error", message: "当前页面需要保存与验证接口。" });
      return;
    }
    const provider = normalizeProviderForChannelEntry(accountDraft.provider || activeEntry.id);
    const initialChannelId = accountDraft.channelId || "{channel_id}";
    const requiredMissing = getManualConnectorFields(activeEntry.id, initialChannelId)
      .filter((field) => field.required && !String(getManualConnectorFieldValue(field, manualConnectorDraft, secretDraft) || "").trim())
      .map((field) => field.label);
    if (requiredMissing.length > 0) {
      setConnectorActionState({ status: "error", message: `请先填写必填字段：${requiredMissing.join("、")}` });
      return;
    }
    setConnectorActionState({ status: "saving", message: "正在保存手动接入配置..." });
    try {
      const channelId = await ensureTenantChannelForEntry(activeEntry.id);
      if (!channelId) return;
      const publicConfig = buildManualPublicConfig(activeEntry.id, channelId);
      await onConfigureConnector(channelId, provider, publicConfig);
      await onSaveSecrets(channelId, buildManualSecrets(activeEntry.id, channelId));
      const verification = await onVerifyConnector(channelId);
      const enterpriseName =
        typeof publicConfig.enterprise_name === "string" && publicConfig.enterprise_name.trim()
          ? publicConfig.enterprise_name.trim()
          : activeEntry.label;
      const agentId =
        typeof publicConfig.agent_id === "string" && publicConfig.agent_id.trim()
          ? publicConfig.agent_id.trim()
          : "";
      const externalAccountId = activeEntry.id === "wechat_kf" ? secretDraft.openKfid.trim() : agentId;
      await onConfigureChannelAccount(channelId, {
        provider,
        platform: activeEntry.label,
        account_name: activeEntry.id === "wecom" ? "企业微信自建应用" : `${activeEntry.label}账号`,
        external_account_id: externalAccountId,
        store_name: enterpriseName,
        entrypoint_name: activeEntry.id === "wechat_kf" ? "微信客服手动接入" : activeEntry.id === "wecom" ? "自建应用回调" : "手动接入回调",
        authorization_status: "manual_configured",
        access_status: verification.status === "verified" ? "connected" : "sandbox_configuring",
        reply_mode: "human_review_first",
        health_status: verification.status === "verified" ? "healthy" : "configuring",
        public_profile: publicConfig
      });
      setConnectorActionState({
        status: verification.status === "verified" ? "success" : "error",
        message:
          verification.status === "verified"
            ? "手动接入配置完整，已连到本系统回调入口；真实外发仍需白名单验收。"
            : `配置未完成：${verification.missing_fields.join("、") || verification.status}`
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : "保存并验证手动接入失败";
      setConnectorActionState({ status: "error", message });
    }
  }

  async function prepareWechatKfCallbackStep() {
    if (!onConfigureConnector || !onSaveSecrets) {
      setConnectorActionState({ status: "error", message: "当前页面缺少微信客服连接器接口。" });
      return;
    }
    const enterpriseName = (manualConnectorDraft.enterprise_name || "").trim();
    const corpId = (manualConnectorDraft.corp_id || "").trim();
    if (!enterpriseName || !corpId) {
      setConnectorActionState({ status: "error", message: "请先填写企业简称和企业 ID。" });
      return;
    }
    setConnectorActionState({ status: "saving", message: "正在生成正式回调地址..." });
    try {
      const channelId = await ensureTenantChannelForEntry("wechat_kf");
      if (!channelId) return;
      const publicConfig = buildManualPublicConfig("wechat_kf", channelId);
      await onConfigureConnector(channelId, "wechat_kf", publicConfig);
      await onSaveSecrets(channelId, {
        token: secretDraft.token,
        encoding_aes_key: secretDraft.encodingAesKey
      });
      setWechatKfManualStep(2);
      setConnectorActionState({
        status: "success",
        message: "正式 URL、Token 和 EncodingAESKey 已生成。请复制到微信客服官方后台的“开发配置 → 企业内部接入”。"
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : "生成微信客服回调配置失败";
      setConnectorActionState({ status: "error", message });
    }
  }

  async function clearConnectorSecrets() {
    if (!accountDraft.channelId || !onDeleteSecrets) {
      setConnectorActionState({ status: "error", message: "请先选择租户渠道。" });
      return;
    }
    setConnectorActionState({ status: "saving", message: "正在清空密钥..." });
    try {
      await onDeleteSecrets(Number(accountDraft.channelId));
      setConnectorActionState({ status: "success", message: "密钥已清空。" });
    } catch (error) {
      const message = error instanceof Error ? error.message : "清空密钥失败";
      setConnectorActionState({ status: "error", message });
    }
  }

  async function deleteChannelConnection(component: ChannelAccessComponent) {
    const account = component.account;
    if (!account || !onDeleteChannelAccount) {
      setConnectorActionState({ status: "error", message: "当前记录没有可删除的渠道账号。" });
      return;
    }
    const confirmed = window.confirm(`确认删除“${account.account_name || component.name}”？删除后该渠道消息不会再进入工作台。`);
    if (!confirmed) return;
    setConnectorActionState({ status: "saving", message: "正在删除渠道接入..." });
    try {
      await onDeleteChannelAccount(account.id);
      setConnectorActionState({ status: "success", message: "渠道接入已删除，后续消息不会进入工作台。" });
      setChannelUiNotice("渠道接入已删除。");
    } catch (error) {
      const message = error instanceof Error ? error.message : "删除渠道接入失败";
      setConnectorActionState({ status: "error", message });
      setChannelUiNotice(message);
    }
  }

  async function verifyConnectorConfig() {
    if (!accountDraft.channelId || !onVerifyConnector) {
      setConnectorActionState({ status: "error", message: "请先选择租户渠道并保存连接器。" });
      return;
    }
    setConnectorActionState({ status: "saving", message: "正在验证配置..." });
    try {
      const result = await onVerifyConnector(Number(accountDraft.channelId));
      setConnectorActionState({
        status: result.status === "verified" ? "success" : "error",
        message: result.status === "verified" ? "配置完整，默认不真实外发。" : `配置未完成：${result.missing_fields.join("、") || result.status}`
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : "验证配置失败";
      setConnectorActionState({ status: "error", message });
    }
  }

  function findPreferredTenantChannel(entryId: ChannelEntryId) {
    const provider = normalizeProviderForChannelEntry(entryId);
    const aliases: Record<ChannelEntryId, string[]> = {
      website: ["website", "web", "web_widget"],
      wechat_kf: ["wechat_kf", "wechat_customer_service", "wechat-kf"],
      wecom: ["wecom", "enterprise_wechat", "wecom_demo"],
      wechat_official: ["wechat_official_account", "wechat_official", "wechat_mp", "mp_weixin"],
      wechat_miniapp: ["wechat_miniapp", "miniapp"]
    };
    const allowed = new Set([provider, ...(aliases[entryId] ?? [])].map((item) => item.toLowerCase()));
    return availableChannels.find((channel) => allowed.has(String(channel.type).toLowerCase())) ?? null;
  }

  async function startConnectorAuthorization(connectMode: ChannelConnectMode, component: ChannelAccessComponent) {
    if (activeEntry.id === "website" && connectMode === "manual") {
      ensureSystemGeneratedConnectorSecrets(activeEntry.id);
      openConfig(component);
      return;
    }
    const provider = normalizeProviderForChannelEntry(accountDraft.provider || activeEntry.id);
    const preferredChannel = accountDraft.channelId ? channelById[Number(accountDraft.channelId)] : findPreferredTenantChannel(activeEntry.id);
    const nextChannelId = preferredChannel?.id ? String(preferredChannel.id) : accountDraft.channelId;
    if (activeEntry.id === "wechat_kf" && connectMode === "manual") {
      setWechatKfManualStep(1);
      setManualConnectorDraft({});
      setSecretDraft(createGeneratedSecretDraft("wechat_kf"));
      setConnectorActionState({ status: "idle", message: "第一步：填写微信客服官方后台“企业信息”中的企业简称和企业 ID。" });
    }
    setConnectorGuide({ mode: connectMode, component });
    setSelectedComponentId(component.id);
    setAccountDraft((current) => ({
      ...current,
      channelId: nextChannelId || current.channelId,
      provider,
      platform: activeEntry.label,
      accountName: `${activeEntry.label}测试入口`,
      storeName: activeEntry.label,
      entrypointName: component.name,
      authorizationStatus: connectMode === "qr" ? "authorization_pending" : "sandbox_configuring",
      accessStatus: "sandbox_configuring",
      replyMode: "human_review_first",
      healthStatus: "configuring",
      publicNote: component.description
    }));
    if (connectMode === "manual") {
      ensureSystemGeneratedConnectorSecrets(activeEntry.id);
      if (activeEntry.id === "wechat_kf") {
        setChannelUiNotice("微信客服手动绑定：企业信息 → 回调配置 → 回填 Secret。无需填写 open_kfid。");
        return;
      }
      if (!nextChannelId || !onConfigureConnector) {
        setConnectorActionState({ status: "idle", message: "填写业务字段后，系统会自动创建租户渠道并保存连接器。" });
        setChannelUiNotice("无需手动选择内部渠道；保存并验证时会自动创建对应渠道。");
        return;
      }
      setConnectorActionState({ status: "saving", message: "正在创建手动接入连接器..." });
      try {
        await onConfigureConnector(Number(nextChannelId), provider);
        setConnectorActionState({ status: "success", message: "手动接入连接器已创建，请继续保存密钥并验证配置。" });
        setChannelUiNotice(`已创建“${activeEntry.label}”手动接入连接器，请继续填写密钥和验证配置。`);
      } catch (error) {
        const message = error instanceof Error ? error.message : "创建手动接入连接器失败";
        setConnectorActionState({ status: "error", message });
        setChannelUiNotice(message);
      }
      return;
    }
    setConnectorActionState({
      status: "success",
      message: "扫码接入需要先配置微信客服服务商第三方平台授权应用；当前请使用手动接入完成绑定。"
    });
    setChannelUiNotice("扫码接入待服务商授权应用开通，手动接入现在可以完成绑定。");
    return;
  }

  const activeEntry = CHANNEL_ENTRY_DEFINITIONS.find((entry) => entry.id === activeChannelId) ?? CHANNEL_ENTRY_DEFINITIONS[0];
  const channelAccountComponents = channelAccounts
    .filter((account) => channelAccountMatchesEntry(account, activeEntry.id, channelById[account.channel_id]?.type))
    .map((account) => channelAccountToAccessComponent(account, channelById[account.channel_id]?.type));
  const activeComponents = activeEntry.id === "website" ? websiteComponents : channelAccountComponents;
  const actionComponent = activeComponents[0] ?? activeEntry.components[0];
  const componentTypes = Array.from(new Set(activeComponents.map((component) => component.componentType)));

  useEffect(() => {
    if (!accountDraft.channelId) return;
    setSecretDraft((current) => {
      const generated = createGeneratedSecretDraft(activeEntry.id);
      return {
        ...current,
        token: current.token || generated.token,
        encodingAesKey: current.encodingAesKey || generated.encodingAesKey,
        webhookSigningSecret: current.webhookSigningSecret || generated.webhookSigningSecret
      };
    });
  }, [accountDraft.channelId, activeEntry.id]);

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
  const listedComponents = filteredComponents;
  const channelColumns = getChannelTableColumns(activeEntry.id);
  const channelNotes = getChannelAccessNotes(activeEntry.id);
  const guideSteps = getChannelGuideSteps(activeEntry.id);
  const apiFields = getChannelApiFields(activeEntry.id);
  const backendHooks = getChannelBackendHooks(activeEntry.id);
  const connectModeActions = getChannelConnectModeActions(activeEntry);
  const connectorSecretStatus = connectorState?.secretStatus ?? null;
  const connectorVerification = connectorState?.verification ?? null;
  const connectorAuthorization = connectorState?.authorization ?? null;
  const connectorFieldStatusText = connectorSecretStatus
    ? Object.entries(connectorSecretStatus.field_status).map(([field, status]) => ` ${field}:${status}`).join(" · ")
    : " 尚未保存";
  const connectorVerificationText = connectorVerification
    ? `最近验证：${connectorVerification.status} · webhook ${connectorVerification.webhook_path}`
    : "";
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

  async function copyTextToClipboard(text: string, label = "内容") {
    try {
      await navigator.clipboard.writeText(text);
      setChannelUiNotice(`${label}已复制到剪贴板。`);
    } catch {
      setChannelUiNotice(`当前浏览器不允许直接复制，请手动选择${label}。`);
    }
  }

  function ensureSystemGeneratedConnectorSecrets(entryId: ChannelEntryId) {
    if (entryId === "website") {
      setSecretDraft((current) => ({
        ...current,
        webhookSigningSecret: current.webhookSigningSecret || generateConnectorSecret("whsec", 32)
      }));
      return;
    }
    setSecretDraft((current) => ({
      ...current,
      token: current.token || generateConnectorSecret("mdk", 24),
      encodingAesKey: current.encodingAesKey || generateEncodingAesKey()
    }));
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
        text: "客服已关闭对话，本次咨询已结束。",
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
                {connectModeActions.map((action, index) => (
                  <button
                    key={action.mode}
                    type="button"
                    className={index === 0 ? "miduoke-primary-button" : "miduoke-secondary-button"}
                    onClick={() => void startConnectorAuthorization(action.mode, actionComponent)}
                  >
                    {action.label}
                  </button>
                ))}
                {activeEntry.id === "wechat_official" || activeEntry.id === "wechat_miniapp" ? (
                  <button type="button" className="miduoke-secondary-button" onClick={() => configureComponent(actionComponent)}>
                    全局配置
                  </button>
                ) : null}
                {activeEntry.id === "website" ? (
                  <button type="button" className="miduoke-secondary-button" onClick={() => configureComponent(actionComponent)}>
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
                  listedComponents.map((component) =>
                    renderChannelTableRow(activeEntry.id, component, {
                      onCode: openCodeModal,
                      onPreview: openPreview,
                      onConfig: openConfig,
                      onDelete: deleteChannelConnection
                    })
                  )
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
                <strong>已接后端端口</strong>
                <small>客户按文档配置后，请求会进入这些接口</small>
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
      {connectorGuide ? (
        <div className="miduoke-modal-backdrop" role="presentation">
          <section className="miduoke-modal miduoke-config-modal" role="dialog" aria-modal="true" aria-label={`${activeEntry.label}接入向导`}>
            <header className="miduoke-modal-head">
              <div>
                <h2>{activeEntry.id === "wechat_kf" ? "绑定微信客服" : `${activeEntry.label}${connectorGuide.mode === "qr" ? "扫码接入" : "手动接入"}`}</h2>
                <p>
                  {connectorGuide.mode === "qr"
                    ? "扫码接入需要先开通服务商第三方平台授权应用；当前可用手动接入完成绑定。"
                    : activeEntry.id === "wechat_kf"
                      ? "按三步复制和回填微信客服配置：先填企业信息，再复制 URL、Token、EncodingAESKey 到微信客服后台，最后回填 Secret 并验证。"
                      : "按字段提示填写配置，保存密钥后验证配置。密钥不会回显。"}
                </p>
              </div>
              <button type="button" className="miduoke-icon-button" aria-label="关闭" onClick={() => setConnectorGuide(null)}>
                <X size={18} />
              </button>
            </header>

            <div className="miduoke-config-form">
              {!accountDraft.channelId && !(activeEntry.id === "wechat_kf" && connectorGuide.mode === "manual") ? (
                <div className="wide channel-account-state-note error">
                  <strong>当前还没有可用的{activeEntry.label}渠道</strong>
                  <small>请先由管理员在后台初始化渠道，系统会自动匹配渠道，不需要客户填写内部渠道编号。</small>
                </div>
              ) : null}

              {connectorGuide.mode === "qr" ? (
                <div className="wide channel-account-state-note" data-channel-authorization-guide="qr">
                  <strong>扫码接入准备中</strong>
                  <small>等服务商授权应用配置完成后，这里会直接展示企业微信管理员扫码授权入口；现在请先使用手动接入。</small>
                  <code>当前可用：手动接入 {"->"} 填企业信息 {"->"} 复制回调配置 {"->"} 回填 Secret</code>
                  <div className="miduoke-website-preview" style={{ padding: 16 }}>
                    <div className="miduoke-preview-widget" style={{ width: 180, height: 180, alignItems: "center", justifyContent: "center" }}>
                      <strong>扫码授权</strong>
                      <span>待服务商应用开通</span>
                    </div>
                  </div>
                  <ol>
                    <li>准备已认证企业微信和超级管理员账号。</li>
                    <li>开通微信客服 API 接入能力。</li>
                    <li>服务商授权应用配置完成后，再由管理员扫码授权。</li>
                  </ol>
                </div>
              ) : (
                <>
                  <div className="wide channel-account-state-note" data-channel-manual-fields="true">
                    <strong>{activeEntry.id === "wechat_kf" ? `手动接入 · 第 ${wechatKfManualStep} 步（共 3 步）` : "需要配置的字段"}</strong>
                    <small>
                      {activeEntry.id === "wechat_kf"
                        ? wechatKfManualStep === 1
                          ? "前往微信客服官方后台“企业信息”，复制企业简称和企业 ID。"
                          : wechatKfManualStep === 2
                            ? "前往微信客服“开发配置 → 企业内部接入 → 开始使用”，复制下方 URL、Token 和 EncodingAESKey 后在官方后台点击完成。"
                            : "把微信客服官方后台完成配置后生成的 Secret 回填到下方，点击完成绑定。"
                        : getManualConnectorFields(activeEntry.id, accountDraft.channelId || "{channel_id}")
                            .map((field) => `${field.label}${field.required ? "*" : ""}`)
                            .join("；")}
                    </small>
                  </div>
                  <div className="wide miduoke-manual-field-list">
                    {getManualConnectorFields(activeEntry.id, accountDraft.channelId || "{channel_id}")
                      .filter((field) => {
                        if (activeEntry.id !== "wechat_kf") return true;
                        if (wechatKfManualStep === 1) return ["enterprise_name", "corp_id"].includes(field.name);
                        if (wechatKfManualStep === 2) return ["callback_url", "token", "encoding_aes_key"].includes(field.name);
                        return field.name === "app_secret";
                      })
                      .map((field) => (
                      <div key={field.name} className="miduoke-manual-field-row">
                        <label htmlFor={`manual-${activeEntry.id}-${field.name}`}>
                          {field.label}{field.required ? " *" : ""}
                        </label>
                        <input
                          id={`manual-${activeEntry.id}-${field.name}`}
                          type={field.kind === "secret" && !field.systemGenerated ? "password" : "text"}
                          value={getManualConnectorFieldValue(field, manualConnectorDraft, secretDraft)}
                          onChange={(event) => {
                            if (field.kind === "public") {
                              setManualConnectorDraft((current) => ({ ...current, [field.name]: event.target.value }));
                            } else {
                              updateSecretDraftByKey(field.secretKey, event.target.value, setSecretDraft);
                            }
                          }}
                          placeholder={field.placeholder}
                          readOnly={field.readonly || field.systemGenerated}
                          disabled={!hasToken || !canManageConnector || field.readonly || field.systemGenerated}
                        />
                        <div className="miduoke-manual-field-action">
                          {field.readonly || field.systemGenerated ? (
                            <button
                              type="button"
                              className="ghost-action compact"
                              onClick={() => void copyTextToClipboard(getManualConnectorFieldValue(field, manualConnectorDraft, secretDraft), field.label)}
                            >
                              复制
                            </button>
                          ) : null}
                        </div>
                      </div>
                      ))}
                  </div>
                </>
              )}

              <div className="wide channel-account-state-note" data-channel-guide-hooks="true">
                <strong>后端接口</strong>
                <small>{backendHooks.join(" · ")}</small>
              </div>
            </div>

            {(connectorActionState.message || connectorState?.message) ? (
              <p className={`miduoke-modal-status ${connectorActionState.status === "error" || connectorState?.status === "error" ? "error" : ""}`}>
                {connectorActionState.message || connectorState?.message}
              </p>
            ) : null}

            <footer className="miduoke-modal-actions">
              <button type="button" className="miduoke-secondary-button" onClick={() => setConnectorGuide(null)}>
                关闭
              </button>
              {connectorGuide.mode === "qr" ? (
                <button
                  type="button"
                  className="miduoke-primary-button"
                  onClick={() => void startConnectorAuthorization("manual", connectorGuide.component)}
                  disabled={!hasToken || !canManageConnector || connectorActionState.status === "saving"}
                >
                  使用手动接入
                </button>
              ) : activeEntry.id === "wechat_kf" ? (
                <>
                  {wechatKfManualStep > 1 ? (
                    <button
                      type="button"
                      className="miduoke-secondary-button"
                      onClick={() => setWechatKfManualStep((current) => (current === 3 ? 2 : 1))}
                      disabled={connectorActionState.status === "saving"}
                    >
                      上一步
                    </button>
                  ) : null}
                  <button
                    type="button"
                    className="miduoke-primary-button"
                    onClick={() => {
                      if (wechatKfManualStep === 1) void prepareWechatKfCallbackStep();
                      else if (wechatKfManualStep === 2) setWechatKfManualStep(3);
                      else void saveManualConnectorAndVerify();
                    }}
                    disabled={!hasToken || !canManageConnector || connectorActionState.status === "saving"}
                  >
                    {wechatKfManualStep === 1 ? "下一步" : wechatKfManualStep === 2 ? "已在微信客服完成，下一步" : "完成绑定"}
                  </button>
                </>
              ) : (
                <>
                  <button
                    type="button"
                    className="miduoke-secondary-button"
                    onClick={() => void saveConnectorSecrets()}
                    disabled={!hasToken || !canManageConnector || connectorActionState.status === "saving"}
                  >
                    保存密钥
                  </button>
                  <button
                    type="button"
                    className="miduoke-primary-button"
                    onClick={() => void saveManualConnectorAndVerify()}
                    disabled={!hasToken || !canManageConnector || connectorActionState.status === "saving"}
                  >
                    保存并验证
                  </button>
                </>
              )}
            </footer>
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
          这里用于试跑前明确谁负责接待、谁维护知识、谁处理运维。网站、微信客服、企业微信、微信公众号、微信小程序只展示官方接入条件、所需资料、当前状态和未接通原因。
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
                  placeholder="例如：网站 / 微信客服 / 企业微信"
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
        <div className="channel-account-form-card" data-channel-self-service-connector="true">
          <div className="knowledge-section-title">
            <ShieldCheck size={18} />
            <strong>自助连接器与密钥状态</strong>
          </div>
          <form className="channel-account-form" onSubmit={submitConnectorConfig}>
            <div className="channel-account-form-grid">
              <label>
                <span>租户渠道</span>
                <select
                  value={accountDraft.channelId}
                  onChange={(event) => setAccountDraft((current) => ({ ...current, channelId: event.target.value }))}
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
                <span>Provider</span>
                <input
                  value={normalizeProviderForChannelEntry(accountDraft.provider || activeEntry.id)}
                  onChange={(event) => setAccountDraft((current) => ({ ...current, provider: event.target.value }))}
                  disabled={!hasToken || !canManageConnector}
                />
              </label>
              <label>
                <span>连接器状态</span>
                <input value={connectorState?.config?.status ?? "未保存"} readOnly />
              </label>
              <label>
                <span>密钥状态</span>
                <input value={connectorState?.secretStatus?.status ?? connectorState?.config?.secret_status ?? "missing"} readOnly />
              </label>
            </div>
            <div className="channel-account-form-footer">
              <small>保存连接器只建立自助配置骨架；真实外发保持关闭，密钥不会回显。</small>
              <button type="submit" className="primary-button compact" disabled={!hasToken || !canManageConnector || connectorActionState.status === "saving"}>
                保存连接器
              </button>
            </div>
          </form>
          <div className="channel-account-form-grid">
            <label>
              <span>Token</span>
              <input
                type="password"
                value={secretDraft.token}
                onChange={(event) => setSecretDraft((current) => ({ ...current, token: event.target.value }))}
                placeholder="保存后不回显"
                disabled={!hasToken || !canManageConnector}
              />
            </label>
            <label>
              <span>EncodingAESKey</span>
              <input
                type="password"
                value={secretDraft.encodingAesKey}
                onChange={(event) => setSecretDraft((current) => ({ ...current, encodingAesKey: event.target.value }))}
                placeholder="保存后不回显"
                disabled={!hasToken || !canManageConnector}
              />
            </label>
            <label>
              <span>AppSecret</span>
              <input
                type="password"
                value={secretDraft.appSecret}
                onChange={(event) => setSecretDraft((current) => ({ ...current, appSecret: event.target.value }))}
                placeholder="保存后不回显"
                disabled={!hasToken || !canManageConnector}
              />
            </label>
            <label>
              <span>Webhook Secret</span>
              <input
                type="password"
                value={secretDraft.webhookSigningSecret}
                onChange={(event) => setSecretDraft((current) => ({ ...current, webhookSigningSecret: event.target.value }))}
                placeholder="网站渠道可用"
                disabled={!hasToken || !canManageConnector}
              />
            </label>
          </div>
          <div className="channel-account-form-footer">
            <small>
              字段状态：
              {connectorFieldStatusText}
            </small>
            <div className="channel-config-actions">
              <button type="button" className="secondary-action compact" onClick={saveConnectorSecrets} disabled={!hasToken || !canManageConnector || connectorActionState.status === "saving"}>
                保存密钥
              </button>
              <button type="button" className="ghost-action compact" onClick={verifyConnectorConfig} disabled={!hasToken || !canManageConnector || connectorActionState.status === "saving"}>
                验证配置
              </button>
              <button type="button" className="ghost-action compact" onClick={clearConnectorSecrets} disabled={!hasToken || !canManageConnector || connectorActionState.status === "saving"}>
                清空密钥
              </button>
            </div>
          </div>
          {connectorVerificationText ? (
            <p className="channel-account-state-note success">
              {connectorVerificationText}
            </p>
          ) : null}
          {connectorAuthorization != null ? (
            <div className="channel-account-state-note success" data-channel-authorization-session="true">
              <strong>{connectorAuthorization?.connect_mode === "qr" ? "扫码授权入口已生成" : "手动接入会话已记录"}</strong>
              <small>
                {connectorAuthorization?.provider} · 过期时间 {formatShortDate(connectorAuthorization?.expires_at ?? "")}
              </small>
              <code>{connectorAuthorization?.authorization_url}</code>
              <ol>
                {(connectorAuthorization?.next_steps ?? []).map((step) => (
                  <li key={step}>{step}</li>
                ))}
              </ol>
            </div>
          ) : null}
          {(connectorActionState.message || connectorState?.message) ? (
            <p className={`channel-account-state-note ${connectorActionState.status === "idle" ? connectorState?.status ?? "idle" : connectorActionState.status}`}>
              {connectorActionState.message || connectorState?.message}
            </p>
          ) : null}
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

function channelAccountMatchesEntry(account: ChannelAccount, entryId: ChannelEntryId, channelType = "") {
  const provider = `${account.provider || ""}`.toLowerCase();
  const platform = `${account.platform || ""}`.toLowerCase();
  const type = `${channelType || ""}`.toLowerCase();
  const text = `${provider} ${platform} ${type} ${account.account_name} ${account.store_name} ${account.entrypoint_name}`.toLowerCase();
  const aliases: Record<ChannelEntryId, string[]> = {
    website: ["website", "web_widget", "网站"],
    wechat_kf: ["wechat_kf", "wechat-kf", "微信客服"],
    wecom: ["wecom", "enterprise_wechat", "企业微信", "企微"],
    wechat_official: ["wechat_official", "wechat_official_account", "公众号"],
    wechat_miniapp: ["wechat_miniapp", "miniapp", "小程序"]
  };
  return aliases[entryId].some((alias) => text.includes(alias.toLowerCase()));
}

function channelAccountToAccessComponent(account: ChannelAccount, channelType = ""): ChannelAccessComponent {
  const isHealthy = account.health_status === "healthy" || account.access_status === "connected";
  const isConfiguring = ["sandbox_configuring", "authorization_pending", "planned"].includes(account.access_status);
  const publicNote = typeof account.public_profile?.note === "string" ? account.public_profile.note : "";
  return {
    id: `channel-account-${account.id}`,
    name: account.account_name || account.platform || "已接入账号",
    componentType: account.external_account_id || account.provider || channelType || "官方渠道",
    style: account.provider === "wechat_miniapp" || channelType === "wechat_miniapp" ? "miniapp" : "link",
    mount: account.entrypoint_name || account.store_name || account.platform || "已登记入口",
    status: isHealthy ? "enabled" : isConfiguring ? "draft" : "planned",
    updatedAt: formatShortDate(account.updated_at ?? account.created_at ?? "") || "刚刚",
    description: publicNote || `${account.platform || channelType || "渠道"} · ${formatAccessStatus(account.access_status)}`,
    account,
    channelType
  };
}

function getAccountProfileText(account: ChannelAccount | undefined, key: string, fallback = "未填写") {
  const value = account?.public_profile?.[key];
  return typeof value === "string" && value.trim() ? value.trim() : fallback;
}

function getChannelActionLabels(id: ChannelEntryId) {
  const labels: Record<ChannelEntryId, [string, string, string]> = {
    website: ["查看代码", "预览", "配置"],
    wechat_kf: ["查看回调", "查看会话", "配置"],
    wecom: ["查看回调", "查看会话", "配置"],
    wechat_official: ["查看开发配置", "查看消息", "配置"],
    wechat_miniapp: ["查看配置", "查看会话", "配置"]
  };
  return labels[id];
}

function renderChannelActions(
  id: ChannelEntryId,
  component: ChannelAccessComponent,
  handlers: {
    onCode: (component: ChannelAccessComponent) => void;
    onPreview: (component: ChannelAccessComponent) => void;
    onConfig: (component: ChannelAccessComponent) => void;
    onDelete: (component: ChannelAccessComponent) => void;
  },
) {
  if (id !== "website") {
    return (
      <span className="miduoke-channel-actions">
        <button type="button" className="danger-action" onClick={() => void handlers.onDelete(component)}>
          删除
        </button>
      </span>
    );
  }
  const [codeLabel, previewLabel, configLabel] = getChannelActionLabels(id);
  return (
    <span className="miduoke-channel-actions">
      <button type="button" onClick={() => handlers.onCode(component)}>
        {codeLabel}
      </button>
      <button type="button" onClick={() => handlers.onPreview(component)}>
        {previewLabel}
      </button>
      <button type="button" onClick={() => handlers.onConfig(component)}>
        {configLabel}
      </button>
    </span>
  );
}

function renderChannelTableRow(
  id: ChannelEntryId,
  component: ChannelAccessComponent,
  handlers: {
    onCode: (component: ChannelAccessComponent) => void;
    onPreview: (component: ChannelAccessComponent) => void;
    onConfig: (component: ChannelAccessComponent) => void;
    onDelete: (component: ChannelAccessComponent) => void;
  },
) {
  const account = component.account;
  const platform = account?.platform || component.name;
  const appName = account?.account_name || component.name;
  const externalId = account?.external_account_id || component.componentType;
  const connectedAt = component.updatedAt.replace(" 09:30", " 13:45");
  if (id === "website") {
    return (
      <div key={component.id} className="miduoke-channel-row" role="row" style={{ gridTemplateColumns: getChannelGridTemplate(id) }}>
        <span>
          <ChannelComponentPreviewIcon style={component.style} />
        </span>
        <span>
          <strong>{component.name}</strong>
          <small>{component.componentType}</small>
        </span>
        <span>{component.mount}</span>
        <span>{connectedAt}</span>
        {renderChannelActions(id, component, handlers)}
      </div>
    );
  }
  if (id === "wecom") {
    return (
      <div key={component.id} className="miduoke-channel-row" role="row" style={{ gridTemplateColumns: getChannelGridTemplate(id) }}>
        <span>
          <strong>{platform}</strong>
          <small>{formatAccessStatus(account?.access_status ?? "connected")}</small>
        </span>
        <span>
          <strong>{appName}</strong>
          <small>{formatHealthStatus(account?.health_status ?? "healthy")}</small>
        </span>
        <span>{getAccountProfileText(account, "enterprise_name", account?.store_name || account?.platform || "已保存")}</span>
        <span>{getAccountProfileText(account, "agent_id", externalId || "已保存")}</span>
        <span>{connectedAt}</span>
        {renderChannelActions(id, component, handlers)}
      </div>
    );
  }
  if (id === "wechat_kf") {
    return (
      <div key={component.id} className="miduoke-channel-row" role="row" style={{ gridTemplateColumns: getChannelGridTemplate(id) }}>
        <span>
          <strong>{platform}</strong>
          <small>{appName}</small>
        </span>
        <span>{getAccountProfileText(account, "open_kfid", externalId || "未填写")}</span>
        <span>{formatHealthStatus(account?.health_status ?? "unknown")}</span>
        <span>{formatReplyMode(account?.reply_mode ?? "draft_only")}</span>
        <span>{connectedAt}</span>
        {renderChannelActions(id, component, handlers)}
      </div>
    );
  }
  if (id === "wechat_official") {
    return (
      <div key={component.id} className="miduoke-channel-row" role="row" style={{ gridTemplateColumns: getChannelGridTemplate(id) }}>
        <span>{platform}</span>
        <span>{getAccountProfileText(account, "account_type", "未填写")}</span>
        <span>{formatAuthorizationStatus(account?.authorization_status ?? "not_configured")}</span>
        <span>{getAccountProfileText(account, "followers", "-")}</span>
        <span>{getAccountProfileText(account, "active_followers", "-")}</span>
        <span>{formatAccessStatus(account?.access_status ?? "planned")}</span>
        <span>{connectedAt}</span>
      </div>
    );
  }
  return (
    <div key={component.id} className="miduoke-channel-row" role="row" style={{ gridTemplateColumns: getChannelGridTemplate(id) }}>
      <span>
        <strong>{appName}</strong>
        <small>{platform}</small>
      </span>
      <span>{formatAccessStatus(account?.access_status ?? "planned")}</span>
      <span>{connectedAt}</span>
      {renderChannelActions(id, component, handlers)}
    </div>
  );
}

function getChannelTableTitle(id: ChannelEntryId) {
  const titles: Record<ChannelEntryId, string> = {
    website: "接待组件列表",
    wechat_kf: "微信客服列表",
    wecom: "企业微信列表",
    wechat_official: "公众号列表",
    wechat_miniapp: "微信小程序列表"
  };
  return titles[id];
}

function getChannelSearchPlaceholder(id: ChannelEntryId) {
  const placeholders: Record<ChannelEntryId, string> = {
    website: "请输入组件名称",
    wechat_kf: "搜索微信客服账号",
    wecom: "搜索企业微信应用",
    wechat_official: "搜索公众号",
    wechat_miniapp: "搜索小程序名称"
  };
  return placeholders[id];
}

function getChannelTableColumns(id: ChannelEntryId) {
  const columns: Record<ChannelEntryId, string[]> = {
    website: ["组件样式", "组件名称/类型", "挂载位置", "更新时间", "操作"],
    wechat_kf: ["微信客服", "open_kfid", "回调状态", "回复模式", "接入时间", "操作"],
    wecom: ["企业微信", "应用名称", "企业名称", "应用ID", "接入时间", "操作"],
    wechat_official: ["公众号", "账号类型", "认证状态", "粉丝数", "互动粉丝数...", "接入方式", "接入时间"],
    wechat_miniapp: ["微信小程序", "接入方式", "接入时间", "操作"]
  };
  return columns[id];
}

function getChannelGridTemplate(id: ChannelEntryId) {
  const templates: Record<ChannelEntryId, string> = {
    website: "170px minmax(180px, 1fr) minmax(150px, 0.8fr) 160px 250px",
    wechat_kf: "190px 180px 150px 150px 150px 210px",
    wecom: "190px 190px 190px 130px 150px 210px",
    wechat_official: "180px 150px 150px 120px 120px 180px 140px",
    wechat_miniapp: "minmax(220px, 1fr) minmax(220px, 1fr) 150px 220px"
  };
  return templates[id];
}

function getChannelAccessNotes(id: ChannelEntryId) {
  const notes: Record<ChannelEntryId, string[]> = {
    website: [],
    wechat_kf: [
      "*手动接入只需从微信客服官方后台取得企业简称、企业 ID 和最后生成的 Secret",
      "*URL、Token、EncodingAESKey 由本系统生成，按三步向导复制到微信客服“开发配置 → 企业内部接入”",
      "*验证通过前只生成草稿或转人工，不自动向微信外发"
    ],
    wecom: ["*本系统保留扫码授权和手动接入两种入口；手动接入更适合独立部署企业"],
    wechat_official: [
      "*你的公众号必须是认证过的微信订阅号或服务号，否则无法正常回复顾客对话",
      "*接入后，之前设置好的菜单、自动回复等功能仍然有效"
    ],
    wechat_miniapp: [
      "*接入前你的小程序需完成认证才能正常使用本功能",
      "*接入后，所有小程序用户的客服消息会被转发到本系统"
    ]
  };
  return notes[id];
}

function getChannelConnectModeActions(entry: ChannelEntryDefinition) {
  return entry.connectModes.map((mode) => ({
    mode,
    label: mode === "qr" ? (entry.id === "wechat_kf" ? "绑定微信客服（扫码，推荐）" : "扫码接入（待开通）") : "手动接入"
  }));
}

function getChannelGuideSteps(id: ChannelEntryId) {
  const steps: Record<ChannelEntryId, string[]> = {
    website: [
      "新建接待组件，确认组件样式和挂载位置。",
      "完成域名校验后，把代码放到网站页面。",
      "上线前先预览组件，确认按钮和聊天链接可打开。"
    ],
    wechat_kf: [
      "推荐使用服务商扫码授权；未配置腾讯服务商应用时可使用三步手动接入。",
      "手动接入在微信客服官方后台完成企业信息、企业内部接入回调与 Secret 回填。",
      "完成入站测试后，再进入白名单自动回复验收。"
    ],
    wecom: [
      "可先填写企业 ID 后扫码授权代开发，也可走企业微信自建应用手动接入。",
      "手动接入需准备 AgentID、Secret、回调 URL、Token、EncodingAESKey 等配置。",
      "完成后测试员工消息是否能进入统一接待。"
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
    wechat_kf: [
      { label: "open_kfid", value: "微信客服账号 ID" },
      { label: "callback_url", value: "接收微信客服消息的回调地址" },
      { label: "token / aes_key", value: "签名校验与消息解密" },
      { label: "app_secret", value: "同步消息和后续发送所需凭据" }
    ],
    wecom: [
      { label: "corp_id / secret", value: "企业与应用凭证" },
      { label: "callback_url", value: "API 接收消息地址" },
      { label: "token / aes_key", value: "签名校验与消息解密" },
      { label: "agent_id", value: "企业微信应用 ID" }
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
    ]
  };
  return fields[id];
}

function getChannelBackendHooks(id: ChannelEntryId) {
  const hooks: Record<ChannelEntryId, string[]> = {
    website: [
      "POST /api/public/website-widget/messages",
      "GET /api/public/website-widget/messages",
      "POST /api/channels/{channel_id}/connector-config",
      "POST /api/channels/{channel_id}/connector-secrets",
      "POST /api/channels/{channel_id}/connector-verification"
    ],
    wechat_kf: [
      "GET /api/webhooks/wechat-kf/channels/{channel_id}",
      "POST /api/webhooks/wechat-kf/channels/{channel_id}",
      "POST /api/channels/{channel_id}/connector-config",
      "POST /api/channels/{channel_id}/connector-secrets",
      "POST /api/channels/{channel_id}/connector-verification"
    ],
    wecom: [
      "GET /api/webhooks/wecom/channels/{channel_id}",
      "POST /api/webhooks/wecom/channels/{channel_id}",
      "POST /api/channels/{channel_id}/connector-config",
      "POST /api/channels/{channel_id}/connector-secrets",
      "POST /api/channels/{channel_id}/connector-verification"
    ],
    wechat_official: [
      "GET /api/webhooks/wechat-official-account/channels/{channel_id}",
      "POST /api/webhooks/wechat-official-account/channels/{channel_id}",
      "POST /api/channels/{channel_id}/connector-config",
      "POST /api/channels/{channel_id}/connector-secrets",
      "POST /api/channels/{channel_id}/connector-verification"
    ],
    wechat_miniapp: [
      "GET /api/webhooks/wechat-miniapp/channels/{channel_id}",
      "POST /api/webhooks/wechat-miniapp/channels/{channel_id}",
      "POST /api/channels/{channel_id}/connector-config",
      "POST /api/channels/{channel_id}/connector-secrets",
      "POST /api/channels/{channel_id}/connector-verification"
    ]
  };
  return hooks[id];
}

function buildWebhookPath(id: ChannelEntryId, channelId: string | number) {
  const sharedWechatCallback = getSharedWechatCallbackUrl(id);
  if ((id === "wechat_kf" || id === "wecom") && sharedWechatCallback) {
    return sharedWechatCallback;
  }
  const providerPath: Record<ChannelEntryId, string> = {
    website: "website",
    wechat_kf: "wechat-kf",
    wecom: "wecom",
    wechat_official: "wechat-official-account",
    wechat_miniapp: "wechat-miniapp"
  };
  const path = `/api/webhooks/${providerPath[id]}/channels/${channelId}`;
  return `${getPublicApiOrigin()}${path}`;
}

function getSharedWechatCallbackUrl(id: ChannelEntryId) {
  const env = import.meta.env as Record<string, string | undefined>;
  if (id === "wechat_kf") {
    return (env.VITE_WECHAT_KF_CALLBACK_URL || "").replace(/\/$/, "");
  }
  if (id === "wecom") {
    return (env.VITE_WECOM_CALLBACK_URL || "").replace(/\/$/, "");
  }
  return "";
}

function getPublicApiOrigin() {
  const env = import.meta.env as Record<string, string | undefined>;
  const configured =
    env.VITE_PUBLIC_API_BASE ||
    env.VITE_API_BASE_URL ||
    env.VITE_API_PROXY_TARGET ||
    "";
  if (configured.trim()) {
    return configured.trim().replace(/\/$/, "");
  }
  if (typeof window !== "undefined") {
    const { protocol, hostname, port, origin } = window.location;
    if ((hostname === "127.0.0.1" || hostname === "localhost") && port && port !== "8000") {
      return `${protocol}//${hostname}:8000`;
    }
    return origin;
  }
  return "";
}

function getManualConnectorFields(id: ChannelEntryId, channelId: string | number): ManualConnectorField[] {
  const callbackUrl = buildWebhookPath(id, channelId);
  const tokenField: ManualConnectorField = {
    name: "token",
    label: "Token",
    placeholder: "系统已生成，请复制到微信后台 Token",
    kind: "secret",
    required: true,
    systemGenerated: true,
    secretKey: "token"
  };
  const aesField: ManualConnectorField = {
    name: "encoding_aes_key",
    label: "EncodingAESKey",
    placeholder: "系统已生成，请复制到微信后台 EncodingAESKey",
    kind: "secret",
    required: true,
    systemGenerated: true,
    secretKey: "encoding_aes_key"
  };
  const appSecretField: ManualConnectorField = {
    name: "app_secret",
    label: "Secret",
    placeholder: "微信后台生成的 Secret / AppSecret，保存后不回显",
    kind: "secret",
    required: true,
    secretKey: "app_secret"
  };
  const definitions: Record<ChannelEntryId, ManualConnectorField[]> = {
    website: [
      { name: "allowed_origin", label: "网站域名", placeholder: "https://example.com", kind: "public", required: true },
      { name: "callback_url", label: "回调 URL", placeholder: callbackUrl, kind: "public", required: true, readonly: true, readonlyValue: callbackUrl },
      {
        ...tokenField,
        name: "webhook_signing_secret",
        label: "Webhook Secret",
        placeholder: "系统已生成，用于网站组件回调签名",
        secretKey: "webhook_signing_secret"
      }
    ],
    wechat_kf: [
      { name: "enterprise_name", label: "企业简称", placeholder: "在微信客服后台「企业信息」获取", kind: "public", required: true },
      { name: "corp_id", label: "企业 ID", placeholder: "例如 wwxxxxxxxxxxxx", kind: "public", required: true },
      { name: "callback_url", label: "URL", placeholder: callbackUrl, kind: "public", required: true, readonly: true, readonlyValue: callbackUrl },
      tokenField,
      aesField,
      appSecretField
    ],
    wecom: [
      { name: "enterprise_name", label: "企业名称", placeholder: "企业微信企业名称", kind: "public", required: true },
      { name: "corp_id", label: "企业 ID", placeholder: "企业微信 CorpID", kind: "public", required: true },
      { name: "agent_id", label: "AgentId", placeholder: "企业微信应用 AgentId", kind: "public", required: true },
      { name: "callback_url", label: "URL", placeholder: callbackUrl, kind: "public", required: true, readonly: true, readonlyValue: callbackUrl },
      tokenField,
      aesField,
      { ...appSecretField, label: "应用 Secret", placeholder: "企业微信自建应用 Secret，保存后不回显" }
    ],
    wechat_official: [
      { name: "account_name", label: "公众号名称", placeholder: "公众号后台显示名称", kind: "public", required: true },
      { name: "app_id", label: "AppID", placeholder: "公众号 AppID", kind: "public", required: true },
      { name: "server_url", label: "服务器地址 URL", placeholder: callbackUrl, kind: "public", required: true, readonly: true, readonlyValue: callbackUrl },
      tokenField,
      { ...aesField, required: false, placeholder: "安全模式需要填写，明文模式可暂不填" },
      { ...appSecretField, label: "AppSecret", required: false, placeholder: "需要调用公众号接口时填写" }
    ],
    wechat_miniapp: [
      { name: "miniapp_name", label: "小程序名称", placeholder: "小程序后台显示名称", kind: "public", required: true },
      { name: "app_id", label: "AppID", placeholder: "小程序 AppID", kind: "public", required: true },
      { name: "server_url", label: "消息推送 URL", placeholder: callbackUrl, kind: "public", required: true, readonly: true, readonlyValue: callbackUrl },
      tokenField,
      aesField,
      { ...appSecretField, label: "AppSecret", placeholder: "小程序 AppSecret，保存后不回显" }
    ]
  };
  return definitions[id];
}

type SecretDraft = {
  token: string;
  encodingAesKey: string;
  appSecret: string;
  openKfid: string;
  webhookSigningSecret: string;
};

function getManualConnectorFieldValue(field: ManualConnectorField, publicDraft: ManualConnectorDraft, secretDraft: SecretDraft) {
  if (field.readonly) {
    return field.readonlyValue ?? "";
  }
  if (field.kind === "public") {
    return publicDraft[field.name] ?? "";
  }
  if (field.secretKey === "token") {
    return secretDraft.token;
  }
  if (field.secretKey === "encoding_aes_key") {
    return secretDraft.encodingAesKey;
  }
  if (field.secretKey === "app_secret") {
    return secretDraft.appSecret;
  }
  if (field.secretKey === "open_kfid") {
    return secretDraft.openKfid;
  }
  if (field.secretKey === "webhook_signing_secret") {
    return secretDraft.webhookSigningSecret;
  }
  return "";
}

function updateSecretDraftByKey(
  key: ManualConnectorField["secretKey"],
  value: string,
  setSecretDraft: Dispatch<SetStateAction<SecretDraft>>
) {
  setSecretDraft((current) => {
    if (key === "token") {
      return { ...current, token: value };
    }
    if (key === "encoding_aes_key") {
      return { ...current, encodingAesKey: value };
    }
    if (key === "app_secret") {
      return { ...current, appSecret: value };
    }
    if (key === "open_kfid") {
      return { ...current, openKfid: value };
    }
    if (key === "webhook_signing_secret") {
      return { ...current, webhookSigningSecret: value };
    }
    return current;
  });
}

function createGeneratedSecretDraft(entryId: ChannelEntryId) {
  if (entryId === "website") {
    return {
      token: "",
      encodingAesKey: "",
      appSecret: "",
      openKfid: "",
      webhookSigningSecret: generateConnectorSecret("whsec", 32)
    };
  }
  return {
    token: generateConnectorSecret("mdk", 24),
    encodingAesKey: generateEncodingAesKey(),
    appSecret: "",
    openKfid: "",
    webhookSigningSecret: ""
  };
}

function generateConnectorSecret(prefix: string, length: number) {
  return `${prefix}${randomString(length)}`;
}

function generateEncodingAesKey() {
  return randomString(43);
}

function randomString(length: number) {
  const alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
  const bytes = new Uint8Array(length);
  if (typeof crypto !== "undefined" && crypto.getRandomValues) {
    crypto.getRandomValues(bytes);
  } else {
    for (let index = 0; index < bytes.length; index += 1) {
      bytes[index] = Math.floor(Math.random() * 256);
    }
  }
  return Array.from(bytes, (byte) => alphabet[byte % alphabet.length]).join("");
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
    connectModes: ["manual"],
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
    id: "wechat_kf",
    label: "微信客服",
    subtitle: "客服链接 / 微信内咨询",
    description: "客户自行在微信客服后台配置回调和密钥后，可把咨询消息接入本工作台；默认先进入草稿或人工确认。",
    componentQuota: 2,
    setupHint: "手动绑定只需按向导从微信客服官方后台复制企业信息、配置回调并回填 Secret。",
    primaryAction: "配置微信客服",
    secondaryAction: "查看回调地址",
    connectModes: ["qr", "manual"],
    components: [
      {
        id: "wechat-kf-link",
        name: "微信客服链接",
        componentType: "链接型",
        style: "link",
        mount: "微信内链接 / 官网按钮",
        status: "draft",
        updatedAt: "2026-07-07 09:30",
        description: "客户点击链接进入微信客服会话，消息接入后由 AI 先接待。"
      },
      {
        id: "wechat-kf-qrcode",
        name: "微信客服二维码",
        componentType: "二维码型",
        style: "qrcode",
        mount: "门店 / 海报 / 帮助中心",
        status: "planned",
        updatedAt: "2026-07-07 09:30",
        description: "客户扫码进入微信客服，未验证前不自动外发。"
      }
    ]
  },
  {
    id: "wecom",
    label: "企业微信",
    subtitle: "企微客户联系 / 回调接入",
    description: "客户自行在企业微信后台配置回调 URL、Token 和 EncodingAESKey；验证通过前只生成草稿或转人工。",
    componentQuota: 2,
    setupHint: "当前先完成自助配置和入站测试，真实外发需要白名单验收。",
    primaryAction: "配置企业微信",
    secondaryAction: "回调配置",
    connectModes: ["manual", "qr"],
    components: [
      {
        id: "wecom-service-link",
        name: "企微客服入口",
        componentType: "链接型",
        style: "link",
        mount: "微信内链接 / 官网按钮",
        status: "draft",
        updatedAt: "2026-07-07 09:30",
        description: "顾客点击入口进入企业微信客服会话。"
      },
      {
        id: "wecom-qrcode",
        name: "企微二维码",
        componentType: "二维码型",
        style: "qrcode",
        mount: "门店 / 海报 / 官网",
        status: "planned",
        updatedAt: "2026-07-07 09:30",
        description: "顾客扫码进入企业微信客服。"
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
    connectModes: ["qr", "manual"],
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
    connectModes: ["qr", "manual"],
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
    const widgetBase = "http://127.0.0.1:8000";
    return `<script type="text/javascript">
  window._WANFA = window._WANFA || function () { (_WANFA.a = _WANFA.a || []).push(arguments); };
  _WANFA("cptid", "${componentId}");
  _WANFA("tenantId", "${tenantId ?? 1}");
  _WANFA("domain", "127.0.0.1:8000");
  _WANFA("apiBase", "${widgetBase}");
  _WANFA("channel", "website");
  _WANFA("mode", "${component?.style === "link" ? "link" : "widget"}");
  _WANFA("position", "${component?.position || "right-bottom"}");
  _WANFA("buttonText", "${component?.buttonText || "在线咨询"}");
  (function (w, d, q, j, s) {
    j = d.createElement(q), s = d.getElementsByTagName(q)[0];
    j.async = true;
    j.charset = "UTF-8";
    j.src = "${widgetBase}/Web/js/customer-widget.js?_=" + Date.now();
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
    requiredBeforeTrial: "必须确认外部发送受控、客户资料已脱敏、试跑结果不作为正式签收"
  },
  {
    role: "接待人员",
    purpose: "处理人工接待和客户追问",
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
    channel: "网站",
    officialCondition: "网站组件、访客标识、入站消息接口和工作台会话状态机。",
    requiredMaterials: "网站域名、组件安装位置、测试访客、自动回复白名单。",
    currentStatus: "优先接入",
    unfinishedReason: "需要先完成资料发布、AI 服务状态和转人工闭环验收。"
  },
  {
    channel: "微信客服",
    officialCondition: "微信客服后台账号、客服链接、回调地址、Token、EncodingAESKey 和 AppSecret。",
    requiredMaterials: "企业主体、企业 ID、微信客服后台生成的 Secret、测试白名单。",
    currentStatus: "配置骨架",
    unfinishedReason: "需要客户在微信客服后台自助填写回调和凭据后验证。"
  },
  {
    channel: "企业微信",
    officialCondition: "企业微信后台应用权限、AgentId、Secret、回调地址、Token 和 EncodingAESKey。",
    requiredMaterials: "企业主体、接待人员、客服链接、测试白名单、官方后台截图。",
    currentStatus: "配置骨架",
    unfinishedReason: "需要客户主体后台授权、可信公网地址和验签解密闭环。"
  },
  {
    channel: "微信公众号",
    officialCondition: "公众号开发配置、消息加解密、客服消息权限和服务号能力。",
    requiredMaterials: "公众号主体、开发者权限、测试号或服务号、消息权限说明。",
    currentStatus: "配置骨架",
    unfinishedReason: "尚未提供公众号后台权限和测试消息回调条件。"
  },
  {
    channel: "微信小程序",
    officialCondition: "小程序 AppID、AppSecret、Token、EncodingAESKey 和咨询入口配置。",
    requiredMaterials: "小程序主体、开发者权限、测试入口、消息能力边界。",
    currentStatus: "配置骨架",
    unfinishedReason: "小程序咨询入口和主动发送边界需要单独验收。"
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
    id: "website",
    channel: "网站",
    formalPath: "第一优先级：网站组件入站、资料发布、AI 回复、转人工和人工回复闭环。",
    currentStatus: "本阶段完整跑通。",
    sandboxPriority: "先完成端到端验收",
    rpaBoundary: "网站渠道也必须受资料发布、模型状态、风险门禁和白名单控制。"
  },
  {
    id: "wechat-kf",
    channel: "微信客服",
    formalPath: "第二优先级：微信客服后台配置、URL 验证、AES 解密、入站标准化。",
    currentStatus: "配置骨架，默认不真实外发。",
    sandboxPriority: "网站闭环后推进",
    rpaBoundary: "不使用个人微信外挂、非官方插件、群控或模拟点击。"
  },
  {
    id: "wecom",
    channel: "企业微信",
    formalPath: "第三优先级：官方回调、URL 验证、AES 解密、入站验签。",
    currentStatus: "配置骨架，真实外发继续关闭。",
    sandboxPriority: "微信客服后推进",
    rpaBoundary: "不使用个人微信外挂、非官方插件、群控或模拟点击。"
  },
  {
    id: "official-account",
    channel: "微信公众号",
    formalPath: "第四优先级：公众号后台开发配置、消息加解密、客服消息权限。",
    currentStatus: "待官方测试号或服务号权限。",
    sandboxPriority: "企业微信后推进",
    rpaBoundary: "不模拟个人微信聊天窗口，不托管个人号。"
  },
  {
    id: "wechat-miniapp",
    channel: "微信小程序",
    formalPath: "第五优先级：小程序咨询入口、开发配置、消息能力边界验收。",
    currentStatus: "配置骨架，默认不真实外发。",
    sandboxPriority: "公众号后推进",
    rpaBoundary: "不承诺无限制主动发送，按微信平台规则验收。"
  }
];

function formatProviderName(value: string) {
  const labels: Record<string, string> = {
    wecom: "企业微信",
    wechat_kf: "微信客服",
    wechat_official_account: "微信公众号",
    wechat_miniapp: "微信小程序",
    official_account: "公众号",
    website: "官网"
  };
  return labels[value] ?? (value || "未登记平台");
}

function normalizeProviderForChannelEntry(value: string) {
  const aliases: Record<string, string> = {
    website: "website",
    wechat_kf: "wechat_kf",
    wecom: "wecom",
    wechat_official: "wechat_official_account",
    wechat_official_account: "wechat_official_account",
    wechat_miniapp: "wechat_miniapp"
  };
  return aliases[value] ?? value;
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
  const callbackBlocker = callbackVerified ? "等待白名单发送测试" : "等待微信客服官方后台发起 URL 验证";

  const wecom: ChannelConnectorCard = {
    id: "wecom-servicer",
    name: "企业微信 / 微信客服",
    category: "第一优先级",
    status: callbackVerified ? "入站链路已产生样例" : "等待自助填写绑定字段",
    tone: callbackVerified ? "warning" : "urgent",
    summary: "用于微信内客服入口、客服链接或二维码。当前只进入转人工和待确认回复流程，不自动写回外部平台。",
    currentBlocker: callbackBlocker,
    officialPath: "企业微信管理后台 -> 应用管理 -> 微信客服 -> 可调用接口的应用 -> 选择企业内部开发或授权应用后配置回调。",
    nextAction: callbackVerified
      ? "继续做白名单发送测试，确认访问凭证、可信 IP、外发开关和转人工放行都成立。"
      : "打开微信客服手动接入，复制系统生成的 URL、Token 和 EncodingAESKey 到微信客服后台，再回填 Secret 后验证。",
    steps: [
      {
        label: "未配置",
        description: "系统默认关闭真实外发，未完成官方接入前只做内部草稿和转人工确认。",
        status: "done",
        evidence: "外发门禁关闭"
      },
      {
        label: "已创建客服账号",
        description: "在微信客服官方后台创建客服账号，并确认名称、头像和可见范围。",
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
        label: "回调 URL 已生成",
        description: "从接入向导复制公网 HTTPS 回调地址，填入微信客服后台。",
        status: callbackVerified ? "done" : "pending",
        evidence: callbackVerified ? "已有入站处理记录" : "手动接入向导中复制"
      },
      {
        label: "等待 URL 验证",
        description: "平台会向 URL 发起验证请求，后端必须完成签名校验、AES 解密和 XML 解析。",
        status: callbackVerified ? "done" : "pending",
        evidence: callbackVerified ? `worker 成功 ${workerRun?.succeeded ?? 0} 条` : "Token 与 EncodingAESKey 由系统生成"
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
        status: callbackVerified ? "已产生入站样例" : "在手动接入向导中复制",
        value: "按所选渠道生成 /api/webhooks/wechat-kf/channels/{channel_id}",
        note: "用于微信客服后台 URL 验证；正式外发能力仍保持关闭。"
      },
      {
        label: "Token",
        status: "由系统生成",
        value: "手动接入向导中复制",
        note: "复制到微信客服后台 Token；保存后前端不回显完整明文。",
        sensitive: true
      },
      {
        label: "EncodingAESKey",
        status: "由系统生成",
        value: "手动接入向导中复制",
        note: "复制到微信客服后台 EncodingAESKey；用于 URL 验证和消息解密。",
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
      id: "website",
      name: "网站",
      summary: "先完成网站组件、访客消息、AI 回复、转人工和人工回复闭环。",
      prerequisites: ["网站域名和组件安装位置", "测试访客和工作台账号", "已发布资料和自动回复白名单"],
      nextAction: "先用网站渠道跑通完整验收链路。"
    },
    {
      id: "wechat-kf",
      name: "微信客服",
      summary: "客户在微信客服后台配置回调和凭据，系统只保存脱敏状态并做验证。",
      prerequisites: ["企业简称和企业 ID", "系统生成的 Token、EncodingAESKey", "微信客服后台生成的 Secret"],
      nextAction: "网站闭环后填写微信客服配置并做入站测试。"
    },
    {
      id: "wechat-official-account",
      name: "微信公众号",
      summary: "适合服务号消息、菜单入口和模板/客服能力。需要公众号后台权限和官方开发配置。",
      prerequisites: ["公众号主体与业务主体一致", "开发者配置、服务器地址和消息加解密完成", "客服消息能力和服务类目符合平台规则"],
      nextAction: "先拿公众号后台管理员权限和测试号，不使用个人微信外挂。"
    },
    {
      id: "wechat-miniapp",
      name: "微信小程序",
      summary: "适合小程序咨询入口，需要明确消息能力和主动发送边界。",
      prerequisites: ["小程序 AppID 和主体", "AppSecret、Token、EncodingAESKey", "咨询入口和测试用户"],
      nextAction: "公众号骨架完成后再推进小程序咨询入口。"
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
