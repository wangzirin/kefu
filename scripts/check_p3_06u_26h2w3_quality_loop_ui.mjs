import fs from "node:fs";
import path from "node:path";

const chromeEndpoint = process.env.CHROME_DEBUGGING_URL ?? "http://127.0.0.1:9227";
const frontendUrl = process.env.FRONTEND_URL ?? "http://127.0.0.1:5182/?demo=1#quality";
const outputDir = path.resolve(process.env.P3_06U_26H2W3_OUTPUT ?? "output/p3_06u_26h2w3_quality_closed_loop");

const viewports = [
  { name: "desktop-1440", width: 1440, height: 900 },
  { name: "desktop-1180", width: 1180, height: 768 }
];

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

async function waitFor(cdp, expression, timeout = 12000) {
  const started = Date.now();
  while (Date.now() - started < timeout) {
    if (await evalValue(cdp, expression)) return true;
    await delay(180);
  }
  return false;
}

async function capture(cdp, viewportName) {
  const screenshot = await cdp.send("Page.captureScreenshot", {
    format: "png",
    fromSurface: true,
    captureBeyondViewport: false
  });
  fs.writeFileSync(path.join(outputDir, `${viewportName}-quality-loop.png`), Buffer.from(screenshot.data, "base64"));
}

async function inspectViewport(viewport) {
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
    const ready = await waitFor(cdp, `Boolean(document.querySelector('[data-h2w3-quality-loop="true"]'))`);
    if (!ready) throw new Error(`${viewport.name}: H2W-3 quality loop did not render`);
    await delay(700);

    const checks = await evalValue(cdp, `(() => {
      const loop = document.querySelector('[data-h2w3-quality-loop="true"]');
      const cards = Array.from(document.querySelectorAll('[data-h2w3-loop-step]'));
      const cardSteps = cards.map((node) => node.getAttribute('data-h2w3-loop-step'));
      const anchors = Array.from(loop.querySelectorAll('a')).map((node) => ({
        text: node.textContent?.replace(/\\s+/g, ' ').trim() ?? '',
        href: node.getAttribute('href') ?? ''
      }));
      const text = loop.textContent ?? '';
      return {
        title: document.querySelector('.topbar h1')?.textContent?.trim() ?? '',
        boundary: loop.getAttribute('data-h2w3-boundary'),
        cardSteps,
        anchorCount: anchors.length,
        anchors,
        hasSampleQuality: text.includes('本地样本质量'),
        hasManualLabelQuality: text.includes('人工标签质量'),
        hasOnlineReceiptSplit: text.includes('真实线上回执分开展示'),
        hasExternalWriteClosed: text.includes('真实外发继续关闭'),
        hasNoFullAccuracy: text.includes('不展示完整线上准确率'),
        hasRetrievalBoundary: text.includes('检索命中率不能替代最终客服答案正确率'),
        hasRepairStopGate: text.includes('错因只看得到但不能进入修复时，本轮质量闭环不算通过'),
        overflowX: document.documentElement.scrollWidth > innerWidth || document.body.scrollWidth > innerWidth
      };
    })()`);
    await capture(cdp, viewport.name);
    const runtimeErrors = cdp.events
      .filter((event) => event.method === "Runtime.exceptionThrown")
      .map((event) => event.params?.exceptionDetails?.exception?.description || event.params?.exceptionDetails?.text || "runtime error");
    return { viewport, checks, runtimeErrors };
  } finally {
    cdp.close();
    await closeTarget(target.id);
  }
}

function validate(result) {
  const failures = [];
  const { checks } = result;
  const prefix = result.viewport.name;
  const requiredSteps = ["sample", "label", "cause", "repair", "regression", "receipt", "sample-to-label", "cause-to-repair", "post-publish-regression"];
  for (const step of requiredSteps) {
    if (!checks.cardSteps.includes(step)) failures.push(`${prefix}: missing loop step ${step}`);
  }
  if (checks.boundary !== "no-full-online-accuracy") failures.push(`${prefix}: boundary marker invalid`);
  if (checks.anchorCount < 10) failures.push(`${prefix}: expected repair and drilldown anchors`);
  if (!checks.hasSampleQuality) failures.push(`${prefix}: sample quality copy missing`);
  if (!checks.hasManualLabelQuality) failures.push(`${prefix}: manual label quality copy missing`);
  if (!checks.hasOnlineReceiptSplit) failures.push(`${prefix}: online receipt split copy missing`);
  if (!checks.hasExternalWriteClosed) failures.push(`${prefix}: external write closed copy missing`);
  if (!checks.hasNoFullAccuracy) failures.push(`${prefix}: no full online accuracy copy missing`);
  if (!checks.hasRetrievalBoundary) failures.push(`${prefix}: retrieval boundary copy missing`);
  if (!checks.hasRepairStopGate) failures.push(`${prefix}: repair stop gate copy missing`);
  if (checks.overflowX) failures.push(`${prefix}: horizontal overflow`);
  if (result.runtimeErrors.length > 0) failures.push(`${prefix}: runtime errors: ${result.runtimeErrors.join(" | ")}`);
  return failures;
}

async function main() {
  fs.mkdirSync(outputDir, { recursive: true });
  const results = [];
  const failures = [];
  for (const viewport of viewports) {
    const result = await inspectViewport(viewport);
    results.push(result);
    failures.push(...validate(result));
  }
  fs.writeFileSync(path.join(outputDir, "summary.json"), JSON.stringify({ frontendUrl, results, failures }, null, 2));
  if (failures.length > 0) {
    throw new Error(`H2W-3 quality loop UI check failed:\\n${failures.join("\\n")}`);
  }
  console.log(`P3-06U-26H2W3 quality loop UI check passed. Evidence: ${outputDir}`);
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
