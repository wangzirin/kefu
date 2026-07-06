import fs from "node:fs";
import path from "node:path";

const chromeEndpoint = process.env.CHROME_DEBUGGING_URL ?? "http://127.0.0.1:9224";
const frontendUrl = process.env.FRONTEND_URL ?? "http://127.0.0.1:5178/";
const outputDir = path.resolve(process.env.P3_06U_09_OUTPUT ?? "output/p3_06u_09_unified_states");

const viewports = [
  { name: "desktop-1440", width: 1440, height: 900, mobile: false },
  { name: "mobile-390", width: 390, height: 844, mobile: true }
];

const sections = [
  { hash: "overview", selector: ".workspace-page-overview", minStateCount: 3 },
  { hash: "live", selector: "#workspace-live", minStateCount: 4 },
  { hash: "reviews", selector: "#workspace-reviews", minStateCount: 5 },
  { hash: "knowledge", selector: "#workspace-knowledge", minStateCount: 6 },
  { hash: "gaps", selector: "#workspace-knowledge-gaps", minStateCount: 6 },
  { hash: "evals", selector: "#workspace-evals", minStateCount: 6 },
  { hash: "quality", selector: "#workspace-quality", minStateCount: 5 },
  { hash: "outbox", selector: "#workspace-outbox", minStateCount: 6 },
  { hash: "channels", selector: '[data-channel-connector-smoke="center"]', minStateCount: 6 },
  { hash: "ops", selector: "#workspace-ops", minStateCount: 6 }
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

async function enterDemo(cdp) {
  await cdp.send("Page.navigate", { url: frontendUrl });
  await cdp.waitFor("Page.loadEventFired", 12000).catch(() => undefined);
  await evalValue(cdp, `localStorage.removeItem('wanfa_standard_ops_access_token'); true`);
  await cdp.send("Page.navigate", { url: frontendUrl });
  await cdp.waitFor("Page.loadEventFired", 12000).catch(() => undefined);
  await delay(450);
  await evalValue(cdp, `(() => {
    const button = Array.from(document.querySelectorAll('button')).find((item) =>
      item.textContent?.includes('开发演示进入')
    );
    if (button) button.click();
    return Boolean(button);
  })()`);
  return waitFor(cdp, `Boolean(document.querySelector('.app-shell'))`);
}

async function capture(cdp, name) {
  const screenshot = await cdp.send("Page.captureScreenshot", {
    format: "png",
    fromSurface: true,
    captureBeyondViewport: false
  });
  fs.writeFileSync(path.join(outputDir, `${name}.png`), Buffer.from(screenshot.data, "base64"));
}

async function inspectSection(cdp, section) {
  await evalValue(cdp, `location.hash = '#${section.hash}'`);
  const ready = await waitFor(cdp, `Boolean(document.querySelector(${JSON.stringify(section.selector)}))`);
  if (!ready) {
    throw new Error(`${section.hash}: page selector did not appear`);
  }
  await delay(320);
  await evalValue(cdp, `document.querySelector(${JSON.stringify(section.selector)})?.scrollIntoView({ block: 'start' })`);
  await delay(160);
  return evalValue(cdp, `(() => {
    const text = document.body.innerText;
    const page = document.querySelector(${JSON.stringify(section.selector)});
    const stateNodes = Array.from(document.querySelectorAll('[data-state-system]'));
    const pageStateNodes = page ? Array.from(page.querySelectorAll('[data-state-system]')) : [];
    return {
      hash: location.hash,
      selector: ${JSON.stringify(section.selector)},
      hasLedger: Boolean(document.querySelector('[data-state-system="ledger"]')),
      stateCount: stateNodes.length,
      pageStateCount: pageStateNodes.length,
      noticeCount: document.querySelectorAll('[data-state-system="notice"]').length,
      sourceBadgeCount: document.querySelectorAll('[data-state-system="source-badge"]').length,
      disabledReasonCount: document.querySelectorAll('.disabled-reason').length,
      hasDemo: text.includes('演示样本'),
      hasMissingConfig: text.includes('配置缺失'),
      hasRealData: text.includes('真实服务端数据'),
      hasExternalWriteOff: text.includes('真实外发关闭') && text.includes('不自动真实外发'),
      hasLoadingCopy: text.includes('加载中'),
      hasEmptyCopy: text.includes('暂无数据') || text.includes('暂无'),
      hasNoPermissionCopy: text.includes('无权限') || text.includes('仅管理员') || text.includes('正式登录'),
      hasErrorCopy: text.includes('接口失败') || text.includes('连接检查失败'),
      overflowX: document.documentElement.scrollWidth > innerWidth || document.body.scrollWidth > innerWidth,
      innerWidth,
      bodyText: text.slice(0, 5000)
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
      mobile: viewport.mobile
    });
    const demoReady = await enterDemo(cdp);
    if (!demoReady) throw new Error(`${viewport.name}: demo app did not load`);

    const sectionResults = [];
    for (const section of sections) {
      const inspected = await inspectSection(cdp, section);
      await capture(cdp, `${viewport.name}-${section.hash}`);
      sectionResults.push({ section, inspected });
    }
    return { viewport, sectionResults };
  } finally {
    cdp.close();
    await closeTarget(target.id);
  }
}

function validate(result) {
  const failures = [];
  for (const { section, inspected } of result.sectionResults) {
    const prefix = `${result.viewport.name}:${section.hash}`;
    if (!inspected.hasLedger) failures.push(`${prefix}: missing workspace-state-ledger`);
    if (inspected.stateCount < section.minStateCount) failures.push(`${prefix}: too few state system nodes`);
    if (!inspected.hasDemo) failures.push(`${prefix}: missing 演示样本 copy`);
    if (!inspected.hasMissingConfig) failures.push(`${prefix}: missing 配置缺失 copy`);
    if (!inspected.hasExternalWriteOff) failures.push(`${prefix}: missing 真实外发关闭 copy`);
    if (inspected.overflowX) failures.push(`${prefix}: horizontal overflow`);
  }
  const allTextFlags = result.sectionResults.reduce(
    (acc, item) => ({
      noPermission: acc.noPermission || item.inspected.hasNoPermissionCopy,
      realData: acc.realData || item.inspected.hasRealData,
      disabledReason: acc.disabledReason || item.inspected.disabledReasonCount > 0
    }),
    { noPermission: false, realData: false, disabledReason: false }
  );
  if (!allTextFlags.noPermission) failures.push(`${result.viewport.name}: missing 无权限/正式登录 copy across smoke pages`);
  if (!allTextFlags.realData) failures.push(`${result.viewport.name}: missing 真实服务端数据 copy across smoke pages`);
  if (!allTextFlags.disabledReason) failures.push(`${result.viewport.name}: missing disabled reason copy across smoke pages`);
  return failures;
}

async function main() {
  fs.mkdirSync(outputDir, { recursive: true });
  const results = [];
  for (const viewport of viewports) {
    results.push(await runViewport(viewport));
  }
  const failures = results.flatMap(validate);
  fs.writeFileSync(path.join(outputDir, "summary.json"), JSON.stringify({ ok: failures.length === 0, failures, results }, null, 2));
  if (failures.length > 0) {
    throw new Error(`P3-06U-09 unified states smoke failed:\\n${failures.join("\\n")}`);
  }
  console.log(`P3-06U-09 unified states smoke passed. Evidence: ${outputDir}`);
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
