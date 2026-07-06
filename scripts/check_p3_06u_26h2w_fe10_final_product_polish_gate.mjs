#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const rootDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const outputDir =
  process.env.P3_06U_26H2W_FE10_OUTPUT ??
  path.join(rootDir, "output/p3_06u_26h2w_fe10_final_product_polish_gate");

const appPath = path.join(rootDir, "frontend/src/App.tsx");
const channelPath = path.join(rootDir, "frontend/src/components/channels/ChannelConnectorCenterPanel.tsx");
const stylesPath = path.join(rootDir, "frontend/src/styles.css");
const fe9SummaryPath = path.join(rootDir, "output/p3_06u_26h2w_fe9_customer_data_browser_qa/summary.json");

const schemaVersion = "p3-06u-26h2w-fe10.final_product_polish_gate.v1";
const forbiddenCustomerTerms = ["H2W", "P3", "dry-run", "provider", "outbox", "sandbox", "rehearsal"];
const overclaims = ["真实外发已开启", "真实渠道已接通", "正式客户验收已完成", "签名安装包已完成", "生产 SLA 已完成"];
const requiredPolishMarkers = [
  "pilot-five-gap-grid",
  "pilot-five-gap-card",
  "channel-personnel-boundary",
  "channel-role-grid",
  "channel-boundary-checklist"
];

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
    "# H2W-FE10 前端最终成品感门禁",
    "",
    "## 结论",
    "",
    `- 阶段状态：\`${result.status}\``,
    `- 阻断项：\`${result.blockers.length}\` 个`,
    "",
    "## 检查内容",
    "",
    "- 试点准备页新增五缺口状态卡片。",
    "- 渠道页新增人员配置与边界说明，并具备对应样式。",
    "- 客户可见区域不出现工程词、假完成态和越界承诺。",
    "",
    "## 阻断项",
    "",
    ...(result.blockers.length ? result.blockers.map((item) => `- ${item}`) : ["- 无"]),
    ""
  ];
  fs.writeFileSync(path.join(outputDir, "frontend_final_polish_report.md"), lines.join("\n"), "utf8");
}

const appSource = readText(appPath);
const channelSource = readText(channelPath);
const styles = readText(stylesPath);
const pilotSlice = functionSlice(appSource, "PilotPreparationPanel");
const customerVisiblePilotText = pilotSlice.replace(/[A-Za-z0-9_]*rehearsal[A-Za-z0-9_]*/gi, "");
const fe9 = readJson(fe9SummaryPath);
const blockers = [];

if (!["waiting_for_real_customer_materials", "passed_customer_data_browser_qa", "passed_internal_sample_browser_qa"].includes(fe9.status)) {
  blockers.push(`FE9 上游状态不满足：${fe9.status ?? "missing"}`);
}
for (const marker of requiredPolishMarkers) {
  if (!pilotSlice.includes(marker) && !channelSource.includes(marker) && !styles.includes(marker)) {
    blockers.push(`缺少前端成品感结构或样式标记：${marker}`);
  }
}
if (!pilotSlice.includes("客户资料未回传前") || !pilotSlice.includes("交付档案 v2")) {
  blockers.push("试点准备页缺少真实资料等待和交付档案 v2 的客户化表达");
}
if (!channelSource.includes("未接通原因") || !channelSource.includes("官方接入条件")) {
  blockers.push("渠道页缺少官方接入条件或未接通原因表达");
}
for (const term of forbiddenCustomerTerms) {
  if (customerVisiblePilotText.includes(term)) blockers.push(`试点准备页客户可见区域包含工程词：${term}`);
}
for (const phrase of overclaims) {
  if (customerVisiblePilotText.includes(phrase) || channelSource.includes(phrase)) {
    blockers.push(`客户可见区域包含越界完成口径：${phrase}`);
  }
}

const result = {
  schema_version: schemaVersion,
  phase: "H2W-FE10",
  status: blockers.length ? "blocked" : "frontend_final_product_polish_ready",
  blockers: [...new Set(blockers)].sort(),
  evidence_paths: [
    relative(fe9SummaryPath),
    relative(appPath),
    relative(channelPath),
    relative(stylesPath),
    "output/p3_06u_26h2w_fe10_final_product_polish_gate/frontend_final_polish_report.md"
  ],
  customer_data_used: false,
  internal_sample_used: false,
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
    fe9_status: fe9.status ?? "missing",
    requiredPolishMarkers
  }
};

fs.mkdirSync(outputDir, { recursive: true });
fs.writeFileSync(path.join(outputDir, "summary.json"), JSON.stringify(result, null, 2), "utf8");
writeMarkdown(result);
console.log(JSON.stringify(result, null, 2));
if (result.status === "blocked") process.exit(1);
