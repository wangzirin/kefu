import { Activity, AlertTriangle, Bot, CheckCircle2, RefreshCw, Search, ShieldCheck } from "lucide-react";

export type WorkspaceStateKind =
  | "loading"
  | "empty"
  | "no_permission"
  | "missing_config"
  | "error"
  | "demo"
  | "real"
  | "external_write_off"
  | "info";

export type DataSourceMode = "demo" | "real" | "local" | "off" | "missing_config" | "error";

type LoadableStatus = "idle" | "loading" | "ready" | "error";

export const PREVIEW_DATA_LABEL = "本地数据";
export const REAL_DATA_LABEL = "服务端数据";
export const EXTERNAL_WRITE_OFF_LABEL = "内部记录模式";

function getWorkspaceStateTone(kind: WorkspaceStateKind) {
  return kind.replace(/_/g, "-");
}

function getWorkspaceStateIcon(kind: WorkspaceStateKind) {
  switch (kind) {
    case "loading":
      return <RefreshCw size={16} />;
    case "empty":
      return <Search size={16} />;
    case "no_permission":
      return <ShieldCheck size={16} />;
    case "missing_config":
    case "error":
      return <AlertTriangle size={16} />;
    case "demo":
      return <Bot size={16} />;
    case "real":
      return <CheckCircle2 size={16} />;
    case "external_write_off":
      return <ShieldCheck size={16} />;
    default:
      return <Activity size={16} />;
  }
}

function getWorkspaceStateTitle(kind: WorkspaceStateKind) {
  switch (kind) {
    case "loading":
      return "加载中";
    case "empty":
      return "暂无数据";
    case "no_permission":
      return "无权限";
    case "missing_config":
      return "配置缺失";
    case "error":
      return "接口失败";
    case "demo":
      return PREVIEW_DATA_LABEL;
    case "real":
      return REAL_DATA_LABEL;
    case "external_write_off":
      return EXTERNAL_WRITE_OFF_LABEL;
    default:
      return "状态说明";
  }
}

function inferWorkspaceStateKind(status: LoadableStatus, message: string): WorkspaceStateKind {
  if (status === "loading") {
    return "loading";
  }
  if (status === "error") {
    return "error";
  }
  if (message.includes("无权") || message.includes("仅管理员") || message.includes("正式登录")) {
    return "no_permission";
  }
  if (
    message.includes("配置") ||
    message.includes("未配置") ||
    message.includes("Token") ||
    message.includes("EncodingAESKey") ||
    message.includes("可信 IP") ||
    message.includes("回调")
  ) {
    return "missing_config";
  }
  return "info";
}

export function WorkspaceStateNotice({
  kind,
  title,
  message,
  compact = false
}: {
  kind: WorkspaceStateKind;
  title?: string;
  message: string;
  compact?: boolean;
}) {
  return (
    <div
      className={`workspace-state-notice tone-${getWorkspaceStateTone(kind)}${compact ? " compact" : ""}`}
      data-state-system="notice"
      data-state-kind={kind}
      role={kind === "error" ? "alert" : "status"}
    >
      <span className="workspace-state-icon" aria-hidden="true">
        {getWorkspaceStateIcon(kind)}
      </span>
      <div>
        <strong>{title ?? getWorkspaceStateTitle(kind)}</strong>
        <p>{message}</p>
      </div>
    </div>
  );
}

export function PanelStateNotice({
  status,
  message,
  loadingMessage = "正在读取服务端数据，请稍候。",
  compact = true
}: {
  status: LoadableStatus;
  message?: string;
  loadingMessage?: string;
  compact?: boolean;
}) {
  if (status === "loading") {
    return <WorkspaceStateNotice kind="loading" message={loadingMessage} compact={compact} />;
  }
  if (!message) {
    return null;
  }
  const kind = inferWorkspaceStateKind(status, message);
  return <WorkspaceStateNotice kind={kind} message={message} compact={compact} />;
}

export function DataSourceBadge({ mode, label, detail }: { mode: DataSourceMode; label: string; detail: string }) {
  return (
    <span className={`data-source-badge mode-${mode}`} data-state-system="source-badge" data-source-mode={mode}>
      <strong>{label}</strong>
      <small>{detail}</small>
    </span>
  );
}

export function DisabledReason({ show, reason }: { show: boolean; reason: string }) {
  if (!show) {
    return null;
  }
  return <small className="disabled-reason">{reason}</small>;
}

export function formatAccessDisabledReason({
  hasToken,
  canManage,
  isLoading,
  action = "操作"
}: {
  hasToken: boolean;
  canManage: boolean;
  isLoading: boolean;
  action?: string;
}) {
  if (isLoading) {
    return `${action}暂不可用：正在加载数据。`;
  }
  if (!hasToken) {
    return `${action}暂不可用：请先登录本地管理员账号后连接租户服务端数据。`;
  }
  if (!canManage) {
    return `${action}暂不可用：当前账号无权限，请由管理员开通对应权限。`;
  }
  return "";
}
