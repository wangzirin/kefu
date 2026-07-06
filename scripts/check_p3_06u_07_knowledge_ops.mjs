import fs from "node:fs";
import path from "node:path";

const chromeEndpoint = process.env.CHROME_DEBUGGING_URL ?? "http://127.0.0.1:9227";
const frontendUrl = process.env.FRONTEND_URL ?? "http://127.0.0.1:5182/?demo=1";
const outputDir = path.resolve(process.env.P3_06U_07_OUTPUT ?? "output/p3_06u_07_knowledge_ops");

const pages = [
  {
    name: "knowledge",
    hash: "#knowledge",
    shell: "library",
    requiredText: ["知识库运营", "维护可被客服引用的业务知识", "业务对象", "问答卡", "版本和审核状态"],
    requiredSelector: '[data-knowledge-ops-smoke="edit-checklist"]'
  },
  {
    name: "gaps",
    hash: "#gaps",
    shell: "gaps",
    requiredText: ["知识缺口", "把错因变成可修复的知识任务", "无知识命中", "引用不足", "人工驳回"],
    requiredSelector: '[data-knowledge-gap-cause-map="p3-06u-26d"]'
  },
  {
    name: "evals",
    hash: "#evals",
    shell: "evals",
    requiredText: ["知识评测", "发布前后对比入口", "不等同完整客服事实准确率", "检索命中，不是完整准确率"],
    requiredSelector: '[data-knowledge-regression-compare="p3-06u-26d"]'
  }
];

const viewports = [
  { name: "desktop-1440", width: 1440, height: 900 },
  { name: "desktop-1280", width: 1280, height: 800 },
  { name: "desktop-1180", width: 1180, height: 768 }
];

function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function pageUrl(hash) {
  return frontendUrl.includes("#") ? frontendUrl : `${frontendUrl}${hash}`;
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
        waitFor(method, timeout = 12000) {
          return new Promise((resolve, reject) => {
            const existingIndex = events.findIndex((item) => item.method === method);
            if (existingIndex >= 0) {
              resolve(events.splice(existingIndex, 1)[0]);
              return;
            }
            const timer = setTimeout(() => reject(new Error(`Timed out waiting for ${method}`)), timeout);
            const listener = (event) => {
              const msg = JSON.parse(event.data);
              if (msg.method === method) {
                clearTimeout(timer);
                ws.removeEventListener("message", listener);
                resolve(msg);
              }
            };
            ws.addEventListener("message", listener);
          });
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

async function waitFor(cdp, expression, timeout = 12000) {
  const started = Date.now();
  while (Date.now() - started < timeout) {
    if (await evalValue(cdp, expression)) return true;
    await delay(180);
  }
  return false;
}

async function enterDemoWorkspace(cdp) {
  const hasWorkspace = await waitFor(
    cdp,
    `Boolean(document.querySelector('.app-shell')) || Boolean(document.querySelector('.login-shell'))`,
    12000
  );
  if (!hasWorkspace) return false;
  const inWorkspace = await evalValue(cdp, `Boolean(document.querySelector('.app-shell'))`);
  if (inWorkspace) return true;
  await evalValue(cdp, `(() => {
    const button = Array.from(document.querySelectorAll('button')).find((item) =>
      item.textContent?.includes('测试账号进入') || item.textContent?.includes('开发演示进入')
    );
    if (button) button.click();
    return Boolean(button);
  })()`);
  return waitFor(cdp, `Boolean(document.querySelector('.app-shell'))`, 12000);
}

async function capture(cdp, name) {
  const screenshot = await cdp.send("Page.captureScreenshot", {
    format: "png",
    fromSurface: true,
    captureBeyondViewport: false
  });
  fs.writeFileSync(path.join(outputDir, `${name}.png`), Buffer.from(screenshot.data, "base64"));
}

async function inspectPage(page, viewport) {
  const target = await createTarget("about:blank");
  const cdp = await createCdp(target.webSocketDebuggerUrl);
  try {
    await cdp.send("Page.enable");
    await cdp.send("Runtime.enable");
    await cdp.send("Emulation.setDeviceMetricsOverride", {
      width: viewport.width,
      height: viewport.height,
      deviceScaleFactor: 1,
      mobile: false
    });
    await cdp.send("Page.navigate", { url: pageUrl(page.hash) });
    await cdp.waitFor("Page.loadEventFired", 12000).catch(() => undefined);
    const appReady = await enterDemoWorkspace(cdp);
    if (!appReady) throw new Error(`${viewport.name}/${page.name}: app shell did not load`);
    await evalValue(cdp, `location.hash = ${JSON.stringify(page.hash)}`);
    const ready = await waitFor(cdp, `Boolean(document.querySelector('[data-knowledge-page-shell="${page.shell}"]'))`);
    if (!ready) throw new Error(`${viewport.name}/${page.name}: knowledge page shell did not load`);
    await delay(420);
    await evalValue(cdp, `window.scrollTo(0, 0)`);
    await delay(160);
    await capture(cdp, `${viewport.name}-${page.name}`);

    const inspected = await evalValue(cdp, `(() => {
      const root = document.documentElement;
      const body = document.body;
      const shell = document.querySelector('[data-knowledge-page-shell="${page.shell}"]');
      const text = shell?.innerText || document.body.innerText;
      const required = document.querySelector('${page.requiredSelector}');
      return {
        href: location.href,
        hash: location.hash,
        text,
        hasShell: Boolean(shell),
        hasRequiredSelector: Boolean(required),
        hasMetricStrip: Boolean(shell?.querySelector('.knowledge-page-metric-strip')),
        hasNoSharedFlowPanel: !document.querySelector('[data-knowledge-ops-smoke="flow-panel"]'),
        hasNoWorkflowStages: document.querySelectorAll('[data-knowledge-ops-stage]').length === 0,
        hasNoPageHeaderActions: !document.querySelector('.knowledge-page-actions'),
        overflowX: root.scrollWidth > innerWidth || body.scrollWidth > innerWidth,
        scrollWidth: root.scrollWidth,
        innerWidth
      };
    })()`);
    const runtimeErrors = cdp.events
      .filter((event) => event.method === "Runtime.exceptionThrown")
      .map((event) => event.params?.exceptionDetails?.exception?.description || event.params?.exceptionDetails?.text || "runtime error");
    return { page, viewport, inspected, runtimeErrors };
  } finally {
    cdp.close();
    await closeTarget(target.id);
  }
}

function validate(result) {
  const failures = [];
  const { page, viewport, inspected, runtimeErrors } = result;
  const prefix = `${viewport.name}/${page.name}`;
  if (!inspected.hasShell) failures.push(`${prefix}: missing page shell`);
  if (!inspected.hasMetricStrip) failures.push(`${prefix}: missing metric strip`);
  if (!inspected.hasRequiredSelector) failures.push(`${prefix}: missing page-specific section ${page.requiredSelector}`);
  if (!inspected.hasNoSharedFlowPanel) failures.push(`${prefix}: shared knowledge flow panel should be removed`);
  if (!inspected.hasNoWorkflowStages) failures.push(`${prefix}: retired workflow stage links still exist`);
  if (!inspected.hasNoPageHeaderActions) failures.push(`${prefix}: duplicated page header action buttons still exist`);
  if (inspected.overflowX) failures.push(`${prefix}: horizontal overflow (${inspected.scrollWidth} > ${inspected.innerWidth})`);
  for (const text of page.requiredText) {
    if (!inspected.text.includes(text)) failures.push(`${prefix}: missing text ${text}`);
  }
  for (const error of runtimeErrors) failures.push(`${prefix}: runtime error: ${error}`);
  return failures;
}

async function main() {
  fs.mkdirSync(outputDir, { recursive: true });
  const results = [];
  const failures = [];
  for (const viewport of viewports) {
    for (const page of pages) {
      const result = await inspectPage(page, viewport);
      results.push(result);
      failures.push(...validate(result));
    }
  }
  fs.writeFileSync(
    path.join(outputDir, "summary.json"),
    JSON.stringify(
      {
        ok: failures.length === 0,
        failures,
        results: results.map((result) => ({
          page: result.page.name,
          viewport: result.viewport.name,
          inspected: result.inspected,
          runtimeErrors: result.runtimeErrors
        }))
      },
      null,
      2
    )
  );
  if (failures.length > 0) {
    throw new Error(`P3-06U-07 knowledge ops smoke failed:\\n${failures.join("\\n")}`);
  }
  console.log(`P3-06U-07 knowledge ops smoke passed. Evidence: ${outputDir}`);
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
