import { AlertTriangle, PlusCircle, RefreshCw, Route, ShieldCheck, Store, UsersRound } from "lucide-react";
import { useMemo, useState } from "react";
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

export function ChannelConnectorCenterPanel({
  reviewItems,
  outboxDrafts,
  failureReviews,
  deliveryJobs,
  workerRun,
  channelAccountState,
  hasToken,
  canManageConnector,
  onConfigureChannelAccount,
  onRefreshChannelAccounts
}: {
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
            {"message" in channelAccountState && channelAccountState.message ? (
              <p className={`channel-account-state-note ${channelAccountState.status}`}>{channelAccountState.message}</p>
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
