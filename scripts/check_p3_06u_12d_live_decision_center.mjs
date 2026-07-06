import fs from "node:fs";
import path from "node:path";

const chromeEndpoint = process.env.CHROME_DEBUGGING_URL ?? "http://127.0.0.1:9227";
const frontendUrl = process.env.FRONTEND_URL ?? "http://127.0.0.1:5181/";
const outputDir = path.resolve(process.env.P3_06U_12D_OUTPUT ?? "output/p3_06u_12d_live_decision_center");

function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function createTarget(url) {
  const res = await fetch(`${chromeEndpoint}/json/new?${encodeURIComponent(url)}`, { method: "PUT" });
  if (!res.ok) throw new Error(`Failed to create Chrome target: ${res.status}`);
  return res.json();
}

async function closeTarget(targetId) {
  await fetch(`${chromeEndpoint}/json/close/${targetId}`).catch(() => undefined);
}

function createCdp(wsUrl) {
  const ws = new WebSocket(wsUrl);
  let id = 0;
  const pending = new Map();
  return new Promise((resolve, reject) => {
    ws.addEventListener("open", () => {
      resolve({
        send(method, params = {}) {
          const callId = ++id;
          ws.send(JSON.stringify({ id: callId, method, params }));
          return new Promise((resolve, reject) => pending.set(callId, { resolve, reject }));
        },
        close() {
          ws.close();
        }
      });
    });
    ws.addEventListener("message", (event) => {
      const msg = JSON.parse(event.data);
      if (msg.id && pending.has(msg.id)) {
        const { resolve, reject } = pending.get(msg.id);
        pending.delete(msg.id);
        if (msg.error) reject(new Error(JSON.stringify(msg.error)));
        else resolve(msg.result || {});
      }
    });
    ws.addEventListener("error", reject);
  });
}

async function evalValue(cdp, expression) {
  const result = await cdp.send("Runtime.evaluate", {
    awaitPromise: true,
    returnByValue: true,
    expression
  });
  if (result.exceptionDetails) throw new Error(JSON.stringify(result.exceptionDetails));
  return result.result.value;
}

async function waitFor(cdp, expression, timeout = 15000) {
  const started = Date.now();
  while (Date.now() - started < timeout) {
    if (await evalValue(cdp, expression)) return true;
    await delay(200);
  }
  return false;
}

async function capture(cdp, name) {
  fs.mkdirSync(outputDir, { recursive: true });
  const screenshot = await cdp.send("Page.captureScreenshot", {
    format: "png",
    fromSurface: true,
    captureBeyondViewport: false
  });
  fs.writeFileSync(path.join(outputDir, `${name}.png`), Buffer.from(screenshot.data, "base64"));
}

async function clickButtonContaining(cdp, text) {
  return evalValue(
    cdp,
    `(() => {
      const button = Array.from(document.querySelectorAll('button')).find((item) => item.textContent?.includes(${JSON.stringify(text)}));
      if (!button || button.disabled) return false;
      button.click();
      return true;
    })()`
  );
}

async function main() {
  fs.mkdirSync(outputDir, { recursive: true });
  const target = await createTarget(`${frontendUrl.replace(/#.*$/, "")}#live`);
  const cdp = await createCdp(target.webSocketDebuggerUrl);
  const failures = [];
  try {
    await cdp.send("Page.enable");
    await cdp.send("Runtime.enable");
    await cdp.send("Emulation.setDeviceMetricsOverride", {
      width: 1440,
      height: 960,
      deviceScaleFactor: 1,
      mobile: false
    });
    await waitFor(cdp, "document.readyState === 'complete'");
    await evalValue(cdp, `localStorage.removeItem('wanfa_standard_ops_access_token'); location.hash = '#live'; location.reload(); true;`);
    await waitFor(cdp, `Boolean(document.querySelector('[data-role-smoke="login-form"]'))`);

    const loginClicked = await clickButtonContaining(cdp, "本地测试进入");
    if (!loginClicked) failures.push("failed to click local dev login");
    await waitFor(cdp, `Boolean(document.querySelector('#workspace-live'))`);

    const liveReady = await evalValue(cdp, `(() => ({
      hash: location.hash,
      hasLive: Boolean(document.querySelector('#workspace-live')),
      hasDecisionCenter: Boolean(document.querySelector('[data-service-decision-center="p3-06u-12d"]')),
      hasLogin: Boolean(document.querySelector('[data-role-smoke="login-form"]'))
    }))()`);
    if (liveReady.hash !== "#live") failures.push(`expected #live after login, got ${liveReady.hash}`);
    if (!liveReady.hasLive) failures.push("live workbench not rendered");
    if (!liveReady.hasDecisionCenter) failures.push("decision center not rendered");
    if (liveReady.hasLogin) failures.push("login form still visible after local dev login");

    if (failures.length === 0) {
      const strategyClicked = await clickButtonContaining(cdp, "试算当前会话");
      if (!strategyClicked) failures.push("failed to click strategy dry-run");
      await waitFor(cdp, `document.querySelector('[data-service-decision-center="p3-06u-12d"]')?.innerText.includes('策略试算完成')`);
    }

    const applyClicked = await clickButtonContaining(cdp, "带入回复框");
    if (!applyClicked) failures.push("failed to apply strategy draft into composer");
    await delay(500);

    const state = await evalValue(cdp, `(() => {
      const bodyText = document.body.innerText;
      const decision = document.querySelector('[data-service-decision-center="p3-06u-12d"]');
      const rawEnumTokens = [
        'fill_draft_only',
        'human_takeover',
        'record_gap',
        'operator_review_and_send',
        'collect_evidence_and_handoff',
        'record_knowledge_gap_and_handoff',
        'handoff_with_draft_and_context',
        'low_confidence',
        'missing_knowledge',
        'risk_term',
        'human_required_by_knowledge',
        'no_knowledge_hit'
      ].filter((token) => bodyText.includes(token));
      const labels = ['坐席判断', 'AI 草稿', '人审原因', '知识依据', '下一步', '安全门禁'];
      const decisionText = decision?.innerText ?? '';
      return {
        hash: location.hash,
        decisionText,
        labelsPresent: labels.filter((label) => decisionText.includes(label)),
        oldInlineContextCount: document.querySelectorAll('.service-inline-context').length,
        oldStrategySummaryCount: document.querySelectorAll('.service-strategy-summary').length,
        oldInlineWarningCount: document.querySelectorAll('.service-inline-warning').length,
        oldNextActionStripCount: document.querySelectorAll('.conversation-decision-strip.service-next-action').length,
        rawEnumTokens,
        hasExternalWriteTrue: bodyText.includes('external_write": true') || bodyText.includes('真实外发已开启'),
        draftValue: document.querySelector('textarea[aria-label="编辑 AI 草稿"]')?.value ?? '',
        noteValue: document.querySelector('textarea[aria-label="填写内部备注或审核意见"]')?.value ?? '',
        overflowX: document.documentElement.scrollWidth > innerWidth || document.body.scrollWidth > innerWidth
      };
    })()`);

    if (state.labelsPresent.length !== 6) failures.push(`decision labels missing: ${state.labelsPresent.join(", ")}`);
    if (state.oldInlineContextCount !== 0) failures.push(`old inline context still rendered: ${state.oldInlineContextCount}`);
    if (state.oldStrategySummaryCount !== 0) failures.push(`old strategy summary still rendered: ${state.oldStrategySummaryCount}`);
    if (state.oldInlineWarningCount !== 0) failures.push(`old warning strip still rendered: ${state.oldInlineWarningCount}`);
    if (state.oldNextActionStripCount !== 0) failures.push(`old next action strip still rendered: ${state.oldNextActionStripCount}`);
    if (state.rawEnumTokens.length > 0) failures.push(`raw enum tokens leaked: ${state.rawEnumTokens.join(", ")}`);
    if (state.hasExternalWriteTrue) failures.push("page suggests external write is enabled");
    if (!state.draftValue.trim()) failures.push("composer draft stayed empty after applying strategy draft");
    if (!state.noteValue.includes("回复策略试算")) failures.push("internal note did not record strategy draft application");
    if (state.overflowX) failures.push("horizontal overflow detected");

    await capture(cdp, "live-decision-center");

    const summary = { liveReady, state, failures };
    fs.writeFileSync(path.join(outputDir, "summary.json"), JSON.stringify(summary, null, 2));
    if (failures.length > 0) {
      for (const failure of failures) console.error(`FAIL ${failure}`);
      process.exitCode = 1;
      return;
    }
    console.log(`P3-06U-12D live decision center browser check passed. Output: ${outputDir}`);
  } finally {
    cdp.close();
    await closeTarget(target.id);
  }
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
