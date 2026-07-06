#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const rootDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const outputDir =
  process.env.P3_06U_26H2W_FE8_OUTPUT ??
  path.join(rootDir, "output/p3_06u_26h2w_fe8_trial_friction_frontend_qa");

const appPath = path.join(rootDir, "frontend/src/App.tsx");
const clientPath = path.join(rootDir, "frontend/src/api/client.ts");
const fe7SummaryPath = path.join(rootDir, "output/p3_06u_26h2w_fe7_customer_trial_browser_smoke/summary.json");

const schemaVersion = "p3-06u-26h2w-fe8.trial_friction_frontend_qa.v1";
const requiredEvidenceCodes = ["trial_c0", "data1", "deploy1", "kb5", "trial2", "fe8", "pack8"];
const requiredLabels = ["试跑范围", "资料接收", "干净部署", "知识复测", "影子试跑", "前端复核", "交付档案 v1.1"];
const forbiddenCustomerTerms = ["H2W", "P3", "dry-run", "provider", "outbox", "sandbox"];
const overclaims = ["真实外发已开启", "真实渠道已接通", "正式客户验收已完成", "签名安装包已完成", "生产 SLA 已完成"];

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
    "# H2W-FE8 试跑摩擦前端复核",
    "",
    "## 结论",
    "",
    `- 阶段状态：\`${result.status}\``,
    `- 阻断项：\`${result.blockers.length}\` 个`,
    "",
    "## 检查内容",
    "",
    "- PACK8 七项证据进入试点准备页。",
    "- 客户可见试点页不出现 H2W、P3、dry-run、provider、outbox、sandbox、rehearsal 等工程词。",
    "- 不出现真实外发、真实渠道、正式验收、签名安装包或生产 SLA 的越界完成口径。",
    "- FE7 浏览器真实登录试跑证据仍有效。",
    "",
    "## 阻断项",
    "",
    ...(result.blockers.length ? result.blockers.map((item) => `- ${item}`) : ["- 无"]),
    ""
  ];
  fs.writeFileSync(path.join(outputDir, "frontend_friction_report.md"), lines.join("\n"), "utf8");
}

const appSource = readText(appPath);
const clientSource = readText(clientPath);
const pilotSlice = functionSlice(appSource, "PilotPreparationPanel");
const fe7 = readJson(fe7SummaryPath);
const blockers = [];

if (fe7.status !== "passed_customer_trial_browser_smoke") {
  blockers.push(`FE7 浏览器试跑证据状态不满足：${fe7.status ?? "missing"}`);
}
for (const code of requiredEvidenceCodes) {
  if (!pilotSlice.includes(code)) blockers.push(`试点准备页缺少 PACK8 证据 code：${code}`);
}
for (const label of requiredLabels) {
  if (!pilotSlice.includes(label)) blockers.push(`试点准备页缺少客户可读标签：${label}`);
}
if (!clientSource.includes("pack8_status") || !clientSource.includes("pack8_evidence")) {
  blockers.push("PilotReadiness 类型缺少 pack8_status / pack8_evidence 字段");
}
for (const term of forbiddenCustomerTerms) {
  if (pilotSlice.includes(term)) blockers.push(`试点准备页客户可见区域包含工程词：${term}`);
}
for (const phrase of overclaims) {
  if (pilotSlice.includes(phrase)) blockers.push(`试点准备页包含越界完成口径：${phrase}`);
}
if (!pilotSlice.includes("不会把内部演练写成正式验收") && !pilotSlice.includes("不把内部演练写成正式验收")) {
  blockers.push("试点准备页缺少内部演练不等于正式验收的边界提示");
}

const result = {
  schema_version: schemaVersion,
  phase: "H2W-FE8",
  status: blockers.length ? "blocked" : "trial_frontend_friction_resolved",
  blockers: [...new Set(blockers)].sort(),
  evidence_paths: [relative(fe7SummaryPath), relative(appPath), relative(clientPath), "output/p3_06u_26h2w_fe8_trial_friction_frontend_qa/frontend_friction_report.md"],
  customer_data_used: false,
  internal_sample_used: true,
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
    fe7_status: fe7.status ?? "missing",
    requiredEvidenceCodes,
    requiredLabels,
    forbiddenCustomerTerms
  }
};

fs.mkdirSync(outputDir, { recursive: true });
fs.writeFileSync(path.join(outputDir, "summary.json"), JSON.stringify(result, null, 2), "utf8");
writeMarkdown(result);
console.log(JSON.stringify(result, null, 2));
if (result.status === "blocked") process.exit(1);
