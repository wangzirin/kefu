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
    label: "机器人",
    href: "#knowledge",
    count: "知识",
    description: "导入资料，让机器人引用客服知识",
    icon: "bot",
    visibleTo: ["owner", "admin", "agent"],
    items: [
      { label: "导入资料", href: "#knowledge", count: "资料", active: false },
      { label: "测试召回", href: "#knowledge-recall", count: "召回", active: false },
      { label: "问答测试", href: "#knowledge-qa-test", count: "问答", active: false },
      { label: "模型服务", href: "#bot-model-service", count: "模型", active: false }
    ]
  },
  {
    label: "渠道接入",
    href: "#channels",
    count: "渠道",
    description: "网站、微信生态和企业微信接入",
    icon: "wecom",
    visibleTo: ["owner", "admin", "viewer"],
    items: [
      { label: "网站", href: "#channels?channel=website", count: "网页", active: false },
      { label: "微信客服", href: "#channels?channel=wechat_kf", count: "客服", active: false },
      { label: "企业微信", href: "#channels?channel=wecom", count: "企微", active: false },
      { label: "微信公众号", href: "#channels?channel=wechat_official", count: "公众号", active: false },
      { label: "微信小程序", href: "#channels?channel=wechat_miniapp", count: "小程序", active: false }
    ]
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

export function getDefaultNavigationHrefForRoles(roles: string[]) {
  if (hasRole(roles, ["owner", "admin", "agent"])) return "#live";
  return getNavigationGroupsForRoles(roles)[0]?.items[0]?.href ?? "#live";
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
