import { spawnSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { pathToFileURL } from "node:url";

const outputRoot = path.resolve(
  process.env.P3_06U_12J_OUTPUT ?? "output/p3_06u_12j_aijiakefu_platform_mock_matrix"
);
const runner = path.resolve("scripts/run_p3_06u_12e_rpa_browser_reply_feasibility.mjs");
const mockPage = path.resolve("research/rpa_browser_reply_feasibility/mock_platform_workbench.html");
const platforms = [
  { id: "douyin", label: "抖音私信样式" },
  { id: "qianniu", label: "淘宝千牛样式" },
  { id: "jingmai", label: "京东京麦样式" },
  { id: "pdd", label: "拼多多样式" }
];

function runPlatform(platform) {
  const outputDir = path.join(outputRoot, platform.id);
  fs.mkdirSync(outputDir, { recursive: true });
  const targetUrl = `${pathToFileURL(mockPage).toString()}?platform=${encodeURIComponent(platform.id)}`;
  const result = spawnSync(process.execPath, [runner], {
    cwd: process.cwd(),
    env: {
      ...process.env,
      P3_06U_12E_OUTPUT: outputDir,
      RPA_TARGET_URL: targetUrl,
      RPA_ALLOW_SEND: "0"
    },
    encoding: "utf8"
  });
  return {
    platform: platform.id,
    label: platform.label,
    outputDir,
    status: result.status === 0 ? "passed" : "failed",
    exitCode: result.status,
    stdout: result.stdout.trim(),
    stderr: result.stderr.trim()
  };
}

function readSummary(outputDir) {
  const summaryPath = path.join(outputDir, "summary.json");
  if (!fs.existsSync(summaryPath)) return null;
  const summary = JSON.parse(fs.readFileSync(summaryPath, "utf8"));
  return {
    observedChannel: summary.observedMessage?.channel ?? "",
    observedCustomerPresent: Boolean(summary.observedMessage?.customerName),
    observedTextPresent: Boolean(summary.observedMessage?.text),
    deliveryMode: summary.strategy?.delivery_mode ?? "",
    nextBestAction: summary.strategy?.next_best_action ?? "",
    externalWritePerformed: Boolean(summary.strategy?.external_write_performed),
    actionExternalWriteCount: summary.strategy?.action_external_write_count ?? null,
    sendAttempted: Boolean(summary.target?.sendAttempted),
    finalEditorFilled: Boolean(summary.finalState?.editorValue?.trim()),
    failures: summary.failures ?? []
  };
}

fs.mkdirSync(outputRoot, { recursive: true });
const results = platforms.map((platform) => {
  const result = runPlatform(platform);
  return {
    ...result,
    summary: readSummary(result.outputDir)
  };
});

const failures = [];
for (const result of results) {
  if (result.status !== "passed") failures.push(`${result.platform}: runner failed`);
  if (!result.summary) {
    failures.push(`${result.platform}: missing summary`);
    continue;
  }
  if (!result.summary.observedTextPresent) failures.push(`${result.platform}: missing observed text`);
  if (!result.summary.finalEditorFilled) failures.push(`${result.platform}: draft not filled`);
  if (result.summary.externalWritePerformed) failures.push(`${result.platform}: external write performed`);
  if (result.summary.actionExternalWriteCount !== 0) {
    failures.push(`${result.platform}: action external write count is not zero`);
  }
  if (result.summary.sendAttempted) failures.push(`${result.platform}: send attempted in draft-only matrix`);
  if (result.summary.failures.length > 0) {
    failures.push(`${result.platform}: ${result.summary.failures.join("; ")}`);
  }
}

const matrix = {
  status: failures.length === 0 ? "passed" : "failed",
  mode: "aijiakefu_reference_platform_mock_matrix",
  scope:
    "Local mock workbench only. This proves our RPA strategy pipeline can run against four platform-shaped surfaces, not that real external platforms are connected.",
  platforms: results,
  failures
};

fs.writeFileSync(path.join(outputRoot, "matrix_summary.json"), JSON.stringify(matrix, null, 2));
console.log(JSON.stringify(matrix, null, 2));

if (failures.length > 0) process.exitCode = 1;
