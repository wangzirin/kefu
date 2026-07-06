import fs from "node:fs";
import path from "node:path";

const chromeEndpoint = process.env.CHROME_DEBUGGING_URL ?? "http://127.0.0.1:9227";
const frontendUrl = process.env.FRONTEND_URL ?? "http://127.0.0.1:5182/?demo=1";
const outputDir = path.resolve(process.env.P3_06U_26H2W0_OUTPUT ?? "output/p3_06u_26h2w0_frontend_function_reality");

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
  const events = [];

  ws.addEventListener("message", (event) => {
    const msg = JSON.parse(event.data);
    if (msg.id && pending.has(msg.id)) {
      const { resolve, reject } = pending.get(msg.id);
      pending.delete(msg.id);
      if (msg.error) reject(new Error(JSON.stringify(msg.error)));
      else resolve(msg.result || {});
      return;
    }
    if (msg.method) events.push(msg);
  });

  return new Promise((resolve, reject) => {
    ws.addEventListener("open", () => {
      resolve({
        events,
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

async function waitFor(cdp, expression, timeoutMs = 12000) {
  const started = Date.now();
  while (Date.now() - started < timeoutMs) {
    if (await evalValue(cdp, expression)) return true;
    await delay(200);
  }
  return false;
}

function withHash(baseUrl, hash) {
  return `${baseUrl.replace(/#.*$/, "")}${hash}`;
}

async function navigate(cdp, hash) {
  await cdp.send("Page.navigate", { url: withHash(frontendUrl, hash) });
  await delay(700);
}

async function capture(cdp, name) {
  const screenshot = await cdp.send("Page.captureScreenshot", {
    format: "png",
    fromSurface: true,
    captureBeyondViewport: false
  });
  fs.writeFileSync(path.join(outputDir, `${name}.png`), Buffer.from(screenshot.data, "base64"));
}

function assertCheck(condition, message, details) {
  if (!condition) {
    throw new Error(`${message}${details ? `: ${JSON.stringify(details)}` : ""}`);
  }
}

fs.mkdirSync(outputDir, { recursive: true });

const target = await createTarget("about:blank");
const cdp = await createCdp(target.webSocketDebuggerUrl);
const summary = {};

try {
  await cdp.send("Page.enable");
  await cdp.send("Runtime.enable");
  await cdp.send("Emulation.setDeviceMetricsOverride", {
    width: 1440,
    height: 940,
    deviceScaleFactor: 1,
    mobile: false
  });

  await navigate(cdp, "#live");
  const liveReady = await waitFor(cdp, `Boolean(document.querySelector('#workspace-live'))`);
  assertCheck(liveReady, "live workspace did not render");
  await delay(600);
  summary.live = await evalValue(cdp, `(() => {
    const text = document.body.innerText;
    const clickQueue = (label) => {
      const button = Array.from(document.querySelectorAll('.service-queue-filter button')).find((item) => item.textContent?.includes(label));
      button?.click();
      return Boolean(button);
    };
    const hasAll = clickQueue('全部');
    const hasMine = clickQueue('我的');
    const hasHandoff = clickQueue('转人工');
    const search = document.querySelector('.service-list-search input');
    if (search) {
      search.value = '微信';
      search.dispatchEvent(new Event('input', { bubbles: true }));
    }
    return {
      hasLive: Boolean(document.querySelector('#workspace-live')),
      hasNoFakeHeaderActions: document.querySelectorAll('.chat-head-action').length === 0,
      hasNoFakeComposerTools: document.querySelectorAll('.composer-tool-button').length === 0,
      hasReadonlyStatus: Boolean(document.querySelector('[data-function-reality="no-fake-chat-actions"]')),
      hasSearch: Boolean(search),
      hasQueueTabs: hasAll && hasMine && hasHandoff,
      hasComposer: Boolean(document.querySelector('[data-chat-ui-slimmed="p3-06u-26h2w"]')),
      hasSafeReplyButton: Boolean(Array.from(document.querySelectorAll('button')).find((button) => button.textContent?.includes('保存接管回复'))),
      hasBannedCopy: ['历史记录', '设为星标', '发送图片', '添加附件', '已自动发送', '已接通全渠道', '已完成线上准确率', '已上传云端', '已正式签收'].some((item) => text.includes(item)),
      hasExternalSendCopy: text.includes('真实外发已开启') || text.includes('已发到微信') || text.includes('已发到抖音')
    };
  })()`);
  assertCheck(summary.live.hasNoFakeHeaderActions, "live page still exposes fake header actions", summary.live);
  assertCheck(summary.live.hasNoFakeComposerTools, "live page still exposes fake composer tool buttons", summary.live);
  assertCheck(summary.live.hasReadonlyStatus, "live page missing readonly capability status", summary.live);
  assertCheck(summary.live.hasSearch && summary.live.hasQueueTabs && summary.live.hasComposer && summary.live.hasSafeReplyButton, "live page missing required real controls", summary.live);
  assertCheck(!summary.live.hasBannedCopy && !summary.live.hasExternalSendCopy, "live page contains banned overclaim copy", summary.live);
  await capture(cdp, "live-function-reality");

  const pageChecks = [
    { hash: "#overview", selector: "#workspace-overview", label: "运营总览", requiredText: "渠道筛选" },
    { hash: "#quality", selector: "#workspace-quality", label: "质量复盘", requiredText: "客户" },
    { hash: "#knowledge", selector: "#workspace-knowledge", label: "知识库运营", requiredText: "业务对象" },
    { hash: "#gaps", selector: "#workspace-knowledge-gaps", label: "知识缺口", requiredText: "知识缺口" },
    { hash: "#evals", selector: "#workspace-evals", label: "知识评测", requiredText: "知识评测" },
    { hash: "#channels", selector: ".channel-layer-tabs", label: "渠道接入", requiredText: "真实外发" },
    { hash: "#ops", selector: "#workspace-ops", label: "运维与告警", requiredText: "告警" },
    { hash: "#model", selector: "#workspace-model", label: "自动回复策略", requiredText: "模型" },
    { hash: "#settings", selector: "#workspace-settings", label: "账号安全", requiredText: "账号" }
  ];

  summary.pages = [];
  for (const page of pageChecks) {
    await navigate(cdp, page.hash);
    const ready = await waitFor(cdp, `Boolean(document.querySelector(${JSON.stringify(page.selector)}))`);
    assertCheck(ready, `${page.label} page did not render`);
    const result = await evalValue(cdp, `(() => {
      const text = document.body.innerText;
      return {
        hash: location.hash,
        selectorPresent: Boolean(document.querySelector(${JSON.stringify(page.selector)})),
        hasRequiredText: text.includes(${JSON.stringify(page.requiredText)}),
        hasOverclaim: ['已自动发送', '已接通全渠道', '已完成线上准确率', '已上传云端', '已正式签收', '程序包可直接应用'].some((item) => text.includes(item)),
        hasHorizontalOverflow: document.documentElement.scrollWidth > innerWidth || document.body.scrollWidth > innerWidth
      };
    })()`);
    assertCheck(result.selectorPresent && result.hasRequiredText, `${page.label} page missing required content`, result);
    assertCheck(!result.hasOverclaim, `${page.label} page contains overclaim copy`, result);
    assertCheck(!result.hasHorizontalOverflow, `${page.label} page has horizontal overflow`, result);
    summary.pages.push({ label: page.label, ...result });
  }
  await capture(cdp, "settings-final-page");

  const runtimeErrors = cdp.events
    .filter((event) => event.method === "Runtime.exceptionThrown")
    .map((event) => event.params?.exceptionDetails?.exception?.description || event.params?.exceptionDetails?.text || "runtime error");
  summary.runtimeErrors = runtimeErrors;
  assertCheck(runtimeErrors.length === 0, "runtime errors occurred", runtimeErrors);

  const summaryPath = path.join(outputDir, "summary.json");
  fs.writeFileSync(summaryPath, JSON.stringify(summary, null, 2));
  console.log(`[PASS] P3-06U-26H2W-0 frontend function reality browser gate passed: ${summaryPath}`);
} finally {
  cdp.close();
  await closeTarget(target.id);
}
