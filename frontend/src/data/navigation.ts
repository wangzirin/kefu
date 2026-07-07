export type NavigationRole = "owner" | "admin" | "agent" | "viewer";

export interface NavigationItem {
  label: string;
  href: string;
  count: string;
  active?: boolean;
  visibleTo?: NavigationRole[];
  hiddenFromSidebar?: boolean;
}

export interface NavigationGroup {
  label: string;
  href: string;
  count: string;
  description: string;
  icon: string;
  items: NavigationItem[];
  visibleTo?: NavigationRole[];
}

export interface RoleTaskPath {
  id: string;
  label: string;
  href: string;
  intent: string;
  outcome: string;
  visibleTo: NavigationRole[];
}

export const navigationGroups: NavigationGroup[] = [
  {
    label: "对话",
    href: "#live",
    count: "坐席",
    description: "当前接待、人工审核和待发送",
    icon: "message",
    visibleTo: ["owner", "admin", "agent"],
    items: [
      { label: "当前对话", href: "#live", count: "接待", active: false },
      { label: "我的会话", href: "#conversations", count: "收件箱", active: false, hiddenFromSidebar: true },
      { label: "人工审核", href: "#reviews", count: "审核", active: false, hiddenFromSidebar: true },
      { label: "待发送草稿", href: "#outbox", count: "草稿", active: false, hiddenFromSidebar: true }
    ]
  },
  {
    label: "客户管理",
    href: "#contacts",
    count: "客户",
    description: "联系人画像和商机线索",
    icon: "customers",
    visibleTo: ["owner", "admin", "agent"],
    items: [
      { label: "客户资料", href: "#contacts", count: "画像", active: false },
      { label: "线索跟进", href: "#leads", count: "线索", active: false }
    ]
  },
  {
    label: "工单管理",
    href: "#tickets",
    count: "工单",
    description: "超时、升级和售后处理",
    icon: "tickets",
    visibleTo: ["owner", "admin", "agent"],
    items: [{ label: "工单/SLA", href: "#tickets", count: "处理", active: false }]
  },
  {
    label: "统计报表",
    href: "#overview",
    count: "报表",
    description: "运营总览、质量复盘和交付报告",
    icon: "report",
    visibleTo: ["owner", "admin", "agent", "viewer"],
    items: [
      { label: "运营总览", href: "#overview", count: "总览", active: false },
      { label: "质量复盘", href: "#quality", count: "质量", active: false }
    ]
  },
  {
    label: "机器人",
    href: "#knowledge",
    count: "知识",
    description: "知识库、缺口、评测和自动回复策略",
    icon: "bot",
    visibleTo: ["owner", "admin", "agent"],
    items: [
      { label: "知识库", href: "#knowledge", count: "文档", active: false },
      { label: "知识缺口", href: "#gaps", count: "修复", active: false, visibleTo: ["owner", "admin"] },
      { label: "知识评测", href: "#evals", count: "评测", active: false, visibleTo: ["owner", "admin"] },
      { label: "自动回复策略", href: "#model", count: "策略", active: false, visibleTo: ["owner", "admin"] }
    ]
  },
  {
    label: "企微助手",
    href: "#channels",
    count: "企微",
    description: "渠道账号、官方接入和回调验证",
    icon: "wecom",
    visibleTo: ["owner", "admin", "viewer"],
    items: [{ label: "渠道接入", href: "#channels", count: "状态", active: false }]
  },
  {
    label: "线索表单",
    href: "#pilot",
    count: "表单",
    description: "资料导入、预检和交付准备",
    icon: "form",
    visibleTo: ["owner", "admin", "viewer"],
    items: [{ label: "本地试运行准备", href: "#pilot", count: "资料", active: false }]
  },
  {
    label: "消息中心",
    href: "#ops",
    count: "消息",
    description: "告警、任务和运维通知",
    icon: "notice",
    visibleTo: ["owner", "admin"],
    items: [{ label: "运维与告警", href: "#ops", count: "通知", active: false }]
  },
  {
    label: "设置中心",
    href: "#settings",
    count: "设置",
    description: "账号、本地维护、备份和更新",
    icon: "settings",
    visibleTo: ["owner", "admin"],
    items: [
      { label: "账号与本地维护", href: "#settings", count: "维护", active: false },
      { label: "模型路由", href: "#model", count: "模型", active: false },
      { label: "运维健康", href: "#ops", count: "健康", active: false }
    ]
  }
];

export const roleTaskPaths: RoleTaskPath[] = [
  {
    id: "ops-risk-scan",
    label: "判断今日风险",
    href: "#overview",
    intent: "先看进线、接待状态、转人工和异常",
    outcome: "确认今天是否需要收紧接待节奏",
    visibleTo: ["owner", "admin", "viewer"]
  },
  {
    id: "pilot-trial-readiness",
    label: "准备本地试运行",
    href: "#pilot",
    intent: "按资料、复测、客户确认和交付档案检查试跑是否可交付",
    outcome: "明确客户还缺什么、哪些证据可下载、哪些边界不能承诺",
    visibleTo: ["owner", "admin", "viewer"]
  },
  {
    id: "review-risk-drafts",
    label: "处理转人工",
    href: "#live?from=overview&task=handoff-conversations&title=处理转人工会话&description=只筛选需要人工接管的会话&range=today&channel_id=all&channel_label=全部渠道&queue=needs_review&empty=当前没有转人工会话",
    intent: "处理低置信、高风险、无知识或渠道异常导致的转人工会话",
    outcome: "人工只接管例外，普通问题由策略处理",
    visibleTo: ["owner", "admin", "agent"]
  },
  {
    id: "outbox-gate",
    label: "抽查接待记录",
    href: "#live?from=overview&task=reply-monitor&title=抽查接待记录&description=查看各渠道会话、知识命中和转人工状态&range=today&channel_id=all&channel_label=全部渠道&queue=all&empty=当前没有可查看会话",
    intent: "抽查会话记录、渠道来源和知识命中",
    outcome: "确认普通问题按策略处理，例外问题进入转人工",
    visibleTo: ["owner", "admin", "agent"]
  },
  {
    id: "live-inbox",
    label: "接待客户会话",
    href: "#live",
    intent: "查看客户消息和接待状态",
    outcome: "普通问题按策略处理，例外问题人工接管",
    visibleTo: ["owner", "admin", "agent"]
  },
  {
    id: "customer-followup",
    label: "跟进客户线索",
    href: "#leads",
    intent: "处理报价、试点、部署和采购咨询",
    outcome: "把客服咨询变成可跟进线索",
    visibleTo: ["owner", "admin", "agent"]
  },
  {
    id: "ticket-sla",
    label: "跟进工单时效",
    href: "#live?from=overview&task=ticket-sla&title=跟进超时会话&description=先在接待工作台处理超时和待接管会话，必要时再建工单&range=today&channel_id=all&channel_label=全部渠道&queue=sla_breached&empty=当前没有 SLA 超时会话",
    intent: "先从接待工作台查看超时客户、负责人和下一步动作",
    outcome: "需要长期跟进时再沉淀为工单",
    visibleTo: ["owner", "admin", "agent"]
  },
  {
    id: "quality-cause-review",
    label: "复盘质量错因",
    href: "#quality",
    intent: "查看低置信、转人工、异常和题库失败",
    outcome: "定位需要修复的知识或渠道问题",
    visibleTo: ["owner", "admin", "viewer"]
  },
  {
    id: "knowledge-gap-repair",
    label: "修复知识缺口",
    href: "#gaps",
    intent: "从错因和失败题沉淀补知识待办",
    outcome: "补完后回归验证，减少重复转人工",
    visibleTo: ["owner", "admin"]
  },
  {
    id: "channel-connector-status",
    label: "检查渠道接入",
    href: "#channels",
    intent: "查看官方通道、回调验证和失败复盘",
    outcome: "明确接入进度和阻塞原因",
    visibleTo: ["owner", "admin", "viewer"]
  },
  {
    id: "ops-health-check",
    label: "检查运维健康",
    href: "#ops",
    intent: "查看 worker、告警规则、指标和外发开关",
    outcome: "确认部署链路可维护",
    visibleTo: ["owner", "admin"]
  }
];

export const navigation = navigationGroups.flatMap((group) => group.items);

export function getNavigationGroupsForRoles(roles: string[]) {
  return navigationGroups
    .filter((group) => canAccessNavigation(roles, group.visibleTo))
    .map((group) => ({
      ...group,
      items: group.items.filter((item) => canAccessNavigation(roles, item.visibleTo))
    }))
    .filter((group) => group.items.length > 0);
}

export function getRoleTaskPathsForRoles(roles: string[]) {
  const limits: Partial<Record<NavigationRole, number>> = {
    owner: 5,
    admin: 5,
    agent: 5,
    viewer: 3
  };
  const roleKey: NavigationRole =
    hasRole(roles, ["owner"])
      ? "owner"
      : hasRole(roles, ["admin"])
        ? "admin"
        : hasRole(roles, ["agent"])
          ? "agent"
          : "viewer";
  const priority: Record<NavigationRole, string[]> = {
    owner: ["pilot-trial-readiness", "ops-risk-scan", "review-risk-drafts", "outbox-gate", "knowledge-gap-repair"],
    admin: ["pilot-trial-readiness", "ops-risk-scan", "review-risk-drafts", "outbox-gate", "quality-cause-review"],
    agent: ["live-inbox", "review-risk-drafts", "outbox-gate", "customer-followup", "ticket-sla"],
    viewer: ["pilot-trial-readiness", "ops-risk-scan", "quality-cause-review"]
  };
  const rank = new Map(priority[roleKey].map((id, index) => [id, index]));
  return roleTaskPaths
    .filter((path) => canAccessNavigation(roles, path.visibleTo))
    .sort((left, right) => (rank.get(left.id) ?? 99) - (rank.get(right.id) ?? 99))
    .slice(0, limits[roleKey] ?? 3);
}

export function getDefaultNavigationHrefForRoles(roles: string[]) {
  return hasRole(roles, ["owner", "admin", "agent"]) ? "#live" : "#overview";
}

function canAccessNavigation(roles: string[], visibleTo?: NavigationRole[]) {
  if (!visibleTo || visibleTo.length === 0) {
    return true;
  }
  return hasRole(roles, visibleTo);
}

function hasRole(roles: string[], allowed: readonly string[]) {
  return roles.some((role) => allowed.includes(role));
}

export const overviewCards = [
  { label: "会话中台", value: "入站", note: "可信入站编排进入人审", kind: "conversation" },
  { label: "知识库", value: "知识", note: "文档、引用与检索评测", kind: "knowledge" },
  { label: "模型路由", value: "网关", note: "可审计草稿，失败转人工", kind: "model" },
  { label: "出站链路", value: "队列", note: "幂等、限流、重试与熔断", kind: "route" }
];

export const queues = [
  { name: "待人工接管", count: 0, owner: "handoff" },
  { name: "低置信复盘", count: 0, owner: "review" },
  { name: "高意向线索", count: 0, owner: "sales" },
  { name: "发送失败", count: 0, owner: "delivery" }
];
