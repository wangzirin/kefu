#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const rootDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const outputDir = path.join(rootDir, "output/p3_06u_26h2w_fe11_safe_test_conversation_gate");
const schemaVersion = "p3-06u-26h2w-fe11.safe_test_conversation_gate.v1";

const files = {
  app: path.join(rootDir, "frontend/src/App.tsx"),
  client: path.join(rootDir, "frontend/src/api/client.ts"),
  workbench: path.join(rootDir, "frontend/src/components/conversation/ConversationWorkbenchPanel.tsx"),
  channels: path.join(rootDir, "frontend/src/components/channels/ChannelConnectorCenterPanel.tsx"),
  pilotApi: path.join(rootDir, "backend/app/api/pilot.py"),
  pilotService: path.join(rootDir, "backend/app/services/pilot.py")
};

function relative(filePath) {
  return path.relative(rootDir, filePath);
}

function readText(filePath) {
  return fs.existsSync(filePath) ? fs.readFileSync(filePath, "utf8") : "";
}

const sources = Object.fromEntries(Object.entries(files).map(([key, filePath]) => [key, readText(filePath)]));
const blockers = [];
const required = {
  app: ["createSafeTestConversation", "handleCreateSafeTestConversation", "onCreateSafeTestConversation"],
  client: ["SafeTestConversationResult", "pilot-safe-test-conversation"],
  workbench: ["生成本地测试会话", "只写入本地数据库", "onCreateSafeTestConversation"],
  channels: ["授权验收后自动接待", "只生成本地建议"],
  pilotApi: ["pilot-safe-test-conversation", "conversation.manage"],
  pilotService: ["SAFE_TEST_CONVERSATION_SCHEMA_VERSION", "external_write_performed\": False", "fe11.safe_test_conversation"]
};

for (const [key, markers] of Object.entries(required)) {
  for (const marker of markers) {
    if (!sources[key].includes(marker)) blockers.push(`${key} 缺少标记：${marker}`);
  }
}
for (const forbidden of ["自动回复+转人工", ">自动回复<", "真实外发已开启", "真实渠道已接通"]) {
  if (sources.workbench.includes(forbidden) || sources.channels.includes(forbidden)) {
    blockers.push(`客户可见前端仍包含越界或旧表达：${forbidden}`);
  }
}

const result = {
  schema_version: schemaVersion,
  phase: "H2W-FE11",
  status: blockers.length ? "blocked" : "fe11_safe_test_conversation_ready",
  blockers: [...new Set(blockers)].sort(),
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
    "真实渠道接通",
    "生产 SLA 承诺",
    "已签名 dmg/exe 安装器"
  ],
  evidence_paths: Object.values(files).map(relative).concat(["output/p3_06u_26h2w_fe11_safe_test_conversation_gate/summary.json"])
};

fs.mkdirSync(outputDir, { recursive: true });
fs.writeFileSync(path.join(outputDir, "summary.json"), JSON.stringify(result, null, 2), "utf8");
fs.writeFileSync(
  path.join(outputDir, "fe11_safe_test_conversation_report.md"),
  [
    "# H2W-FE11 安全测试会话门禁",
    "",
    `- 阶段状态：\`${result.status}\``,
    `- 阻断项：\`${result.blockers.length}\` 个`,
    "",
    "## 阻断项",
    "",
    ...(result.blockers.length ? result.blockers.map((item) => `- ${item}`) : ["- 无"]),
    ""
  ].join("\n"),
  "utf8"
);
console.log(JSON.stringify(result, null, 2));
if (result.status === "blocked") process.exit(1);
