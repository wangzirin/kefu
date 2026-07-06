import fs from "node:fs";
import path from "node:path";

const chromeEndpoint = process.env.CHROME_DEBUGGING_URL ?? "http://127.0.0.1:9227";
const frontendUrl = process.env.FRONTEND_URL ?? "http://127.0.0.1:5182/?demo=1";
const outputDir = path.resolve(process.env.P3_06U_24_OUTPUT ?? "output/p3_06u_24_knowledge_split");

const routes = [
  {
    hash: "#knowledge",
    marker: "library",
    mustInclude: ["知识库运营", "业务对象", "问答卡", "文档片段", "真实外发关闭"]
  },
  {
    hash: "#gaps",
    marker: "gaps",
    mustInclude: ["知识缺口", "错因", "修复", "无命中", "缺引用", "真实外发关闭"]
  },
  {
    hash: "#evals",
    marker: "evals",
    mustInclude: ["知识评测", "发布前后变化", "不等同完整客服事实准确率", "检索与引用质量", "真实外发关闭"]
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

async function createTarget(url) {
  const res = await fetch(`${chromeEndpoint}/json/new?${encodeURIComponent(url)}`, { method: "PUT" });
  if (!res.ok) {
    throw new Error(`Failed to create Chrome target: ${res.status}`);
  }
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
        send(method, params = {}) {
          const callId = ++id;
          ws.send(JSON.stringify({ id: callId, method, params }));
          return new Promise((resolve, reject) => pending.set(callId, { resolve, reject }));
        },
        waitFor(method, timeout = 10000) {
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
  if (result.exceptionDetails) {
    throw new Error(JSON.stringify(result.exceptionDetails));
  }
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

async function capture(cdp, name) {
  const screenshot = await cdp.send("Page.captureScreenshot", {
    format: "png",
    fromSurface: true,
    captureBeyondViewport: false
  });
  fs.writeFileSync(path.join(outputDir, `${name}.png`), Buffer.from(screenshot.data, "base64"));
}

async function enterDemoWorkspace(cdp, viewport) {
  const hasWorkspace = await waitFor(
    cdp,
    `Boolean(document.querySelector('.app-shell')) || Boolean(document.querySelector('.login-shell'))`,
    12000
  );
  if (!hasWorkspace) {
    throw new Error(`${viewport.name}: app did not render login shell or workspace shell`);
  }
  const inWorkspace = await evalValue(cdp, `Boolean(document.querySelector('.app-shell'))`);
  if (inWorkspace) {
    return true;
  }
  const clicked = await evalValue(cdp, `(() => {
    const button = Array.from(document.querySelectorAll('button')).find((item) =>
      item.textContent?.includes('测试账号进入') || item.textContent?.includes('开发演示进入')
    );
    if (button) button.click();
    return Boolean(button);
  })()`);
  if (!clicked) {
    throw new Error(`${viewport.name}: demo entry button was not found`);
  }
  return waitFor(cdp, `Boolean(document.querySelector('.app-shell'))`, 12000);
}

async function inspectRoute(cdp, route, viewport) {
  await evalValue(cdp, `location.hash = ${JSON.stringify(route.hash)}`);
  const ready = await waitFor(cdp, `Boolean(document.querySelector('[data-knowledge-primary="${route.marker}"]'))`);
  if (!ready) {
    throw new Error(`${viewport.name} ${route.hash}: primary knowledge panel did not appear`);
  }
  await delay(350);
  await evalValue(cdp, `window.scrollTo(0, 0)`);
  await delay(160);
  await capture(cdp, `${viewport.name}-${route.marker}`);
  return evalValue(cdp, `(() => {
    const primary = document.querySelector('[data-knowledge-primary="${route.marker}"]');
    const flow = document.querySelector('[data-knowledge-ops-smoke="flow-panel"]');
    const firstPanel = document.querySelector('.workspace-page-grid.stacked > .panel');
    const primaryRect = primary?.getBoundingClientRect();
    const flowRect = flow?.getBoundingClientRect();
    const firstText = firstPanel?.textContent || '';
    const primaryText = primary?.textContent || '';
    const body = document.body;
    const root = document.documentElement;
    return {
      hash: location.hash,
      title: primary?.querySelector('h2')?.textContent?.trim() || '',
      firstPanelIsPrimary: firstPanel === primary,
      primaryTop: primaryRect ? Math.round(primaryRect.top) : null,
      flowTop: flowRect ? Math.round(flowRect.top) : null,
      flowBelowPrimary: flowRect && primaryRect ? flowRect.top > primaryRect.top + 120 : true,
      primaryText,
      firstText: firstText.slice(0, 1500),
      hasHorizontalOverflow: root.scrollWidth > innerWidth || body.scrollWidth > innerWidth,
      hasNoSharedFlowPanel: !flow,
      markerCount: document.querySelectorAll('[data-knowledge-primary]').length,
      innerWidth
    };
  })()`);
}

async function inspectChannelIdentity(cdp, viewport) {
  await evalValue(cdp, `location.hash = '#live'`);
  const ready = await waitFor(cdp, `Boolean(document.querySelector('#workspace-live'))`);
  if (!ready) {
    throw new Error(`${viewport.name}: live workspace did not appear`);
  }
  await delay(350);
  await capture(cdp, `${viewport.name}-live-channel-identity`);
  return evalValue(cdp, `(() => {
    const text = document.body.innerText;
    return {
      hash: location.hash,
      hasDesk: Boolean(document.querySelector('#workspace-live')),
      hasChannelAccountCopy: text.includes('微信客服') || text.includes('未登记入口') || text.includes('官网可用'),
      hasReplyModeCopy: text.includes('自动回复') || text.includes('只生成草稿') || text.includes('先审后发'),
      hasNoHorizontalOverflow: !(document.documentElement.scrollWidth > innerWidth || document.body.scrollWidth > innerWidth)
    };
  })()`);
}

async function runViewport(viewport) {
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
    await cdp.send("Page.navigate", { url: frontendUrl });
    await cdp.waitFor("Page.loadEventFired", 12000).catch(() => undefined);
    const appReady = await enterDemoWorkspace(cdp, viewport);
    if (!appReady) {
      throw new Error(`${viewport.name}: app shell did not load`);
    }
    const routeResults = [];
    for (const route of routes) {
      routeResults.push({ route, inspected: await inspectRoute(cdp, route, viewport) });
    }
    const channelIdentity = await inspectChannelIdentity(cdp, viewport);
    return { viewport, routeResults, channelIdentity };
  } finally {
    cdp.close();
    await closeTarget(target.id);
  }
}

function validate(result) {
  const failures = [];
  const prefix = result.viewport.name;
  for (const { route, inspected } of result.routeResults) {
    const routePrefix = `${prefix} ${route.hash}`;
    if (inspected.hasHorizontalOverflow) failures.push(`${routePrefix}: horizontal overflow`);
    if (inspected.markerCount < 1) failures.push(`${routePrefix}: missing route primary marker`);
    if (!inspected.hasNoSharedFlowPanel) failures.push(`${routePrefix}: shared flow panel should not appear in split knowledge routes`);
    for (const text of route.mustInclude) {
      if (!inspected.primaryText.includes(text)) failures.push(`${routePrefix}: missing primary text ${text}`);
    }
  }
  if (!result.channelIdentity.hasDesk) failures.push(`${prefix} #live: missing live desk`);
  if (!result.channelIdentity.hasChannelAccountCopy) failures.push(`${prefix} #live: missing channel account identity copy`);
  if (!result.channelIdentity.hasReplyModeCopy) failures.push(`${prefix} #live: missing reply mode copy`);
  if (!result.channelIdentity.hasNoHorizontalOverflow) failures.push(`${prefix} #live: horizontal overflow`);
  return failures;
}

fs.mkdirSync(outputDir, { recursive: true });
const results = [];
for (const viewport of viewports) {
  results.push(await runViewport(viewport));
}
const failures = results.flatMap(validate);
fs.writeFileSync(path.join(outputDir, "summary.json"), JSON.stringify({ ok: failures.length === 0, failures, results }, null, 2));
if (failures.length > 0) {
  console.error(`P3-06U-24 knowledge split check failed:\n${failures.join("\n")}`);
  process.exit(1);
}
console.log(`P3-06U-24 knowledge split check passed. Output: ${outputDir}`);
