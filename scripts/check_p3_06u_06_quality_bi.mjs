import fs from "node:fs";
import path from "node:path";

const chromeEndpoint = process.env.CHROME_DEBUGGING_URL ?? "http://127.0.0.1:9224";
const frontendUrl = process.env.FRONTEND_URL ?? "http://127.0.0.1:5178/#quality";
const outputDir = path.resolve(process.env.P3_06U_06_OUTPUT ?? "output/p3_06u_06_quality_bi");

const viewports = [
  { name: "desktop-1440", width: 1440, height: 900, mobile: false },
  { name: "desktop-900", width: 900, height: 900, mobile: false },
  { name: "mobile-390", width: 390, height: 844, mobile: true }
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
        waitFor(method, timeout = 8000) {
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

async function enterDemoQuality(cdp) {
  await delay(500);
  await evalValue(cdp, `(() => {
    const button = Array.from(document.querySelectorAll('button')).find((item) =>
      item.textContent?.includes('开发演示进入')
    );
    if (button) button.click();
    return Boolean(button);
  })()`);
  const appReady = await waitFor(cdp, `Boolean(document.querySelector('.app-shell'))`);
  if (!appReady) return false;
  await evalValue(cdp, `location.hash = '#quality'`);
  const qualityReady = await waitFor(cdp, `Boolean(document.querySelector('[data-quality-smoke="repair-map"]'))`);
  await delay(320);
  return qualityReady;
}

async function capture(cdp, name) {
  const screenshot = await cdp.send("Page.captureScreenshot", {
    format: "png",
    fromSurface: true,
    captureBeyondViewport: false
  });
  fs.writeFileSync(path.join(outputDir, `${name}.png`), Buffer.from(screenshot.data, "base64"));
}

async function inspectQuality(cdp) {
  return evalValue(cdp, `(() => {
    const text = document.body.innerText;
    const repairLinks = Array.from(document.querySelectorAll('[data-quality-context-link="true"]'));
    return {
      href: location.href,
      hash: location.hash,
      hasQualityPanel: Boolean(document.querySelector('[data-quality-smoke="quality-panel"]')),
      hasRepairMap: Boolean(document.querySelector('[data-quality-smoke="repair-map"]')),
      repairPathCount: document.querySelectorAll('[data-quality-repair-key]').length,
      fromQualityLinks: Array.from(document.querySelectorAll('a[href*="from=quality"]')).length,
      firstRepairHref: repairLinks[0]?.getAttribute('href') || '',
      hasRepairCopy: text.includes('修复闭环'),
      hasCauseRanking: text.includes('错因排行'),
      hasTrend: text.includes('题库趋势'),
      hasDrilldown: text.includes('样本下钻'),
      hasAccuracyBoundary: text.includes('不把检索命中当作完整准确率'),
      overflowX: document.documentElement.scrollWidth > innerWidth || document.body.scrollWidth > innerWidth,
      innerWidth,
      bodyText: text.slice(0, 5000)
    };
  })()`);
}

async function clickFirstRepairPath(cdp) {
  const clicked = await evalValue(cdp, `(() => {
    const link = Array.from(document.querySelectorAll('[data-quality-context-link="true"]')).find((item) =>
      (item.getAttribute('href') || '').includes('from=quality')
    );
    if (!link) return false;
    link.click();
    return true;
  })()`);
  if (!clicked) throw new Error("Could not click a from=quality repair path");
  const ready = await waitFor(cdp, `Boolean(document.querySelector('.task-context-banner'))`);
  await delay(300);
  return ready;
}

async function inspectTarget(cdp) {
  return evalValue(cdp, `(() => {
    const text = document.body.innerText;
    return {
      href: location.href,
      hash: location.hash,
      hasTaskBanner: Boolean(document.querySelector('.task-context-banner')),
      hasQualitySource: text.includes('来自质量复盘'),
      hasMatchCount: text.includes('当前匹配'),
      overflowX: document.documentElement.scrollWidth > innerWidth || document.body.scrollWidth > innerWidth,
      bodyText: text.slice(0, 4000)
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
    await cdp.send("Page.navigate", { url: frontendUrl });
    await cdp.waitFor("Page.loadEventFired", 12000).catch(() => undefined);
    const ready = await enterDemoQuality(cdp);
    if (!ready) throw new Error(`${viewport.name}: quality page did not load`);

    const quality = await inspectQuality(cdp);
    await capture(cdp, `${viewport.name}-quality`);
    await evalValue(cdp, `document.querySelector('[data-quality-smoke="repair-map"]')?.scrollIntoView({ block: 'center' })`);
    await delay(250);
    await capture(cdp, `${viewport.name}-repair-map`);
    const targetReady = await clickFirstRepairPath(cdp);
    if (!targetReady) throw new Error(`${viewport.name}: quality repair target did not show task context`);
    const repairTarget = await inspectTarget(cdp);
    await capture(cdp, `${viewport.name}-repair-target`);

    return { viewport, quality, repairTarget };
  } finally {
    cdp.close();
    await closeTarget(target.id);
  }
}

function validate(result) {
  const failures = [];
  const { viewport, quality, repairTarget } = result;
  const prefix = viewport.name;
  if (!quality.hasQualityPanel) failures.push(`${prefix}: missing quality panel`);
  if (!quality.hasRepairMap) failures.push(`${prefix}: missing repair map`);
  if (quality.repairPathCount < 5) failures.push(`${prefix}: expected at least 5 repair paths`);
  if (quality.fromQualityLinks < 5) failures.push(`${prefix}: expected at least 5 from=quality links`);
  if (!quality.firstRepairHref.includes("from=quality")) failures.push(`${prefix}: first repair link lacks from=quality`);
  if (!quality.hasRepairCopy) failures.push(`${prefix}: missing repair loop copy`);
  if (!quality.hasCauseRanking) failures.push(`${prefix}: missing cause ranking`);
  if (!quality.hasTrend) failures.push(`${prefix}: missing trend section`);
  if (!quality.hasDrilldown) failures.push(`${prefix}: missing drilldown section`);
  if (!quality.hasAccuracyBoundary) failures.push(`${prefix}: missing accuracy boundary copy`);
  if (quality.overflowX) failures.push(`${prefix}: quality page has horizontal overflow`);
  if (!repairTarget.hasTaskBanner) failures.push(`${prefix}: repair target missing task context banner`);
  if (!repairTarget.hasQualitySource) failures.push(`${prefix}: repair target does not say 来自质量复盘`);
  if (!repairTarget.hasMatchCount) failures.push(`${prefix}: repair target missing match count`);
  if (repairTarget.overflowX) failures.push(`${prefix}: repair target has horizontal overflow`);
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
    throw new Error(`P3-06U-06 quality BI smoke failed:\\n${failures.join("\\n")}`);
  }
  console.log(`P3-06U-06 quality BI smoke passed. Evidence: ${outputDir}`);
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
