#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const rootDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const outputDir =
  process.env.P3_06U_26H2W_FE9_OUTPUT ??
  path.join(rootDir, "output/p3_06u_26h2w_fe9_customer_data_browser_qa");

const appPath = path.join(rootDir, "frontend/src/App.tsx");
const clientPath = path.join(rootDir, "frontend/src/api/client.ts");
const channelPath = path.join(rootDir, "frontend/src/components/channels/ChannelConnectorCenterPanel.tsx");
const fe8SummaryPath = path.join(rootDir, "output/p3_06u_26h2w_fe8_trial_friction_frontend_qa/summary.json");
const data2rSummaryPath = path.join(rootDir, "output/p3_06u_26h2w_data2r_real_customer_materials/summary.json");
const kb6SummaryPath = path.join(rootDir, "output/p3_06u_26h2w_kb6_real_customer_knowledge_retest/summary.json");
const trial3SummaryPath = path.join(rootDir, "output/p3_06u_26h2w_trial3_real_customer_shadow_trial/summary.json");

const schemaVersion = "p3-06u-26h2w-fe9.customer_data_browser_qa.v1";
const forbiddenCustomerTerms = ["H2W", "P3", "dry-run", "provider", "outbox", "sandbox", "rehearsal"];
const overclaims = ["真实外发已开启", "真实渠道已接通", "正式客户验收已完成", "签名安装包已完成", "生产 SLA 已完成"];
const requiredClientFields = [
  "customer_knowledge_retest_status",
  "shadow_trial_status",
  "frontend_customer_qa_status",
  "frontend_product_polish_status",
  "channel_boundary_status",
  "installer_trial_status",
  "pack10_status"
];
const requiredPilotLabels = ["真实资料", "知识复测", "影子试跑", "前端验收", "成品体验", "渠道边界", "安装体验", "交付档案 v2"];

function relative(filePath) {
  return path.relative(rootDir, filePath);
}

function readText(filePath) {
  return fs.existsSync(filePath) ? fs.readFileSync(filePath, "utf8") : "";
}

function readJson(filePath) {
  if (!fs.existsSync(filePath)) return {};
  return JSON.parse(fs.readFileSync(filePath, "utf8"));
}

function functionSlice(source, functionName) {
  const start = source.indexOf(`function ${functionName}`);
  if (start < 0) return "";
  const next = source.indexOf("\nfunction ", start + 20);
  return source.slice(start, next > start ? next : source.length);
}

function writeMarkdown(result) {
  const lines = [
    "# H2W-FE9 客户视角二次浏览器验收门禁",
    "",
    "## 结论",
    "",
    `- 阶段状态：\`${result.status}\``,
    `- 阻断项：\`${result.blockers.length}\` 个`,
    "",
    "## 检查内容",
    "",
    "- 试点准备页展示五大缺口状态。",
    "- 前端类型包含 PACK10 相关聚合字段。",
    "- 渠道页包含人员配置与边界页入口。",
    "- 客户可见区域不出现工程词和越界完成态。",
    "",
    "## 阻断项",
    "",
    ...(result.blockers.length ? result.blockers.map((item) => `- ${item}`) : ["- 无"]),
    ""
  ];
  fs.writeFileSync(path.join(outputDir, "frontend_customer_data_qa_report.md"), lines.join("\n"), "utf8");
}

const appSource = readText(appPath);
const clientSource = readText(clientPath);
const channelSource = readText(channelPath);
const pilotSlice = functionSlice(appSource, "PilotPreparationPanel");
const customerVisiblePilotText = pilotSlice.replace(/[A-Za-z0-9_]*rehearsal[A-Za-z0-9_]*/gi, "");
const fe8 = readJson(fe8SummaryPath);
const data2r = readJson(data2rSummaryPath);
const kb6 = readJson(kb6SummaryPath);
const trial3 = readJson(trial3SummaryPath);
const blockers = [];
const dataWaiting = data2r.status === "waiting_for_real_customer_materials";
const dataInternalSample = data2r.status === "internal_sample_materials_ready_for_rehearsal";
const acceptedDataStatuses = [
  "waiting_for_real_customer_materials",
  "customer_real_materials_ready",
  "internal_sample_materials_ready_for_rehearsal"
];
const acceptedKbStatuses = dataInternalSample
  ? ["customer_knowledge_retest_ready_with_internal_sample"]
  : ["customer_knowledge_retest_ready_with_customer_data"];
const acceptedTrialStatuses = dataInternalSample
  ? ["shadow_trial_ready_with_internal_sample"]
  : ["shadow_trial_ready_with_customer_data"];

if (fe8.status !== "trial_frontend_friction_resolved") {
  blockers.push(`FE8 上游状态不满足：${fe8.status ?? "missing"}`);
}
if (!acceptedDataStatuses.includes(data2r.status)) {
  blockers.push(`DATA2R 状态不可用：${data2r.status ?? "missing"}`);
}
if (!dataWaiting) {
  if (!acceptedKbStatuses.includes(kb6.status)) {
    blockers.push(`KB6 真实客户知识复测状态不满足：${kb6.status ?? "missing"}`);
  }
  if (!acceptedTrialStatuses.includes(trial3.status)) {
    blockers.push(`TRIAL3 真实客户影子试跑状态不满足：${trial3.status ?? "missing"}`);
  }
}
for (const field of requiredClientFields) {
  if (!clientSource.includes(field)) blockers.push(`PilotReadiness 类型缺少字段：${field}`);
}
for (const label of requiredPilotLabels) {
  if (!pilotSlice.includes(label)) blockers.push(`试点准备页缺少五大缺口客户可读标签：${label}`);
}
if (!channelSource.includes("人员与边界") || !channelSource.includes("接待人员") || !channelSource.includes("知识维护人")) {
  blockers.push("渠道页缺少人员配置与边界说明入口");
}
for (const term of forbiddenCustomerTerms) {
  if (customerVisiblePilotText.includes(term)) blockers.push(`试点准备页客户可见区域包含工程词：${term}`);
}
for (const phrase of overclaims) {
  if (customerVisiblePilotText.includes(phrase)) blockers.push(`试点准备页包含越界完成口径：${phrase}`);
}

const result = {
  schema_version: schemaVersion,
  phase: "H2W-FE9",
  status: blockers.length
    ? "blocked"
    : dataWaiting
      ? "waiting_for_real_customer_materials"
      : dataInternalSample
        ? "passed_internal_sample_browser_qa"
        : "passed_customer_data_browser_qa",
  blockers: [...new Set(blockers)].sort(),
  evidence_paths: [
    relative(fe8SummaryPath),
    relative(data2rSummaryPath),
    relative(kb6SummaryPath),
    relative(trial3SummaryPath),
    relative(appPath),
    relative(clientPath),
    relative(channelPath),
    "output/p3_06u_26h2w_fe9_customer_data_browser_qa/frontend_customer_data_qa_report.md"
  ],
  customer_data_used: !dataWaiting && !dataInternalSample && !blockers.length,
  internal_sample_used: dataInternalSample && !blockers.length,
  boundaries: {
    formal_customer_signoff_ready: false,
    real_platform_send_ready: false,
    signed_dmg_exe_ready: false,
    production_sla_ready: false,
    rpa_formal_delivery_enabled: false
  },
  not_ready_for: [
    "正式客户验收签收",
    "真实平台自动外发",
    "企业微信、公众号、抖音、淘宝、京东、拼多多等真实渠道接通",
    "生产 SLA 承诺",
    "已签名 dmg/exe 安装器",
    "RPA 或个人号外挂正式交付"
  ],
  checks: {
    fe8_status: fe8.status ?? "missing",
    data2r_status: data2r.status ?? "missing",
    kb6_status: kb6.status ?? "missing",
    trial3_status: trial3.status ?? "missing",
    data_waiting: dataWaiting,
    requiredClientFields,
    requiredPilotLabels
  }
};

fs.mkdirSync(outputDir, { recursive: true });
fs.writeFileSync(path.join(outputDir, "summary.json"), JSON.stringify(result, null, 2), "utf8");
writeMarkdown(result);
console.log(JSON.stringify(result, null, 2));
if (result.status === "blocked") process.exit(1);
