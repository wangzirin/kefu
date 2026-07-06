import fs from "node:fs";
import path from "node:path";

const chromeEndpoint = process.env.CHROME_DEBUGGING_URL ?? "http://127.0.0.1:9227";
const frontendBaseUrl = process.env.FRONTEND_URL ?? "http://127.0.0.1:5182/?demo=1";
const outputDir = path.resolve(process.env.P3_06U_26H2W3D_OUTPUT ?? "output/p3_06u_26h2w3d_online_receipt_quality_ui");

const viewports = [
  { name: "desktop-1440", width: 1440, height: 900 },
  { name: "desktop-1280", width: 1280, height: 800 },
  { name: "desktop-1180", width: 1180, height: 768 }
];

function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function pageUrl() {
  return `${frontendBaseUrl}#quality`;
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

async function inspect(viewport) {
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
    await cdp.send("Page.navigate", { url: pageUrl() });
    await cdp.waitFor("Page.loadEventFired", 12000).catch(() => undefined);
    const ready = await waitFor(cdp, `Boolean(document.querySelector('[data-h2w3d-online-receipt-quality="p3-06u-26h2w3d"]'))`);
    if (!ready) throw new Error(`${viewport.name}: online receipt quality section did not become ready`);
    await delay(500);
    const inspected = await evalValue(cdp, `(() => {
      const root = document.documentElement;
      const body = document.body;
      const section = document.querySelector('[data-h2w3d-online-receipt-quality="p3-06u-26h2w3d"]');
      const text = section?.innerText || "";
      const panelText = document.querySelector('[data-quality-smoke="quality-panel"]')?.innerText || "";
      const rect = section?.getBoundingClientRect();
      return {
        href: location.href,
        hasSection: Boolean(section),
        hasBoundary: text.includes("完整客服答案准确率") || panelText.includes("完整客服答案准确率"),
        hasNoFullAccuracyClaim: panelText.includes("不展示完整线上准确率"),
        hasExternalWriteOff: panelText.includes("真实外发继续关闭"),
        hasProviderBreakdown: Boolean(section?.querySelector(".h2w3-provider-breakdown")),
        gateCount: section?.querySelectorAll(".h2w3-receipt-gate").length || 0,
        sectionRect: rect ? { top: Math.round(rect.top), left: Math.round(rect.left), width: Math.round(rect.width), height: Math.round(rect.height) } : null,
        overflowX: root.scrollWidth > innerWidth || body.scrollWidth > innerWidth,
        scrollWidth: root.scrollWidth,
        innerWidth
      };
    })()`);
    const screenshot = await cdp.send("Page.captureScreenshot", {
      format: "png",
      fromSurface: true,
      captureBeyondViewport: false
    });
    fs.writeFileSync(path.join(outputDir, `${viewport.name}-quality-receipt.png`), Buffer.from(screenshot.data, "base64"));
    const runtimeErrors = cdp.events
      .filter((event) => event.method === "Runtime.exceptionThrown")
      .map((event) => event.params?.exceptionDetails?.exception?.description || event.params?.exceptionDetails?.text || "runtime error");
    return { viewport, inspected, runtimeErrors };
  } finally {
    cdp.close();
    await closeTarget(target.id);
  }
}

function validate(result) {
  const { viewport, inspected, runtimeErrors } = result;
  const prefix = viewport.name;
  const failures = [];
  if (!inspected.hasSection) failures.push(`${prefix}: missing online receipt section`);
  if (!inspected.hasBoundary) failures.push(`${prefix}: missing full accuracy boundary`);
  if (!inspected.hasNoFullAccuracyClaim) failures.push(`${prefix}: missing no-full-online-accuracy text`);
  if (!inspected.hasExternalWriteOff) failures.push(`${prefix}: missing external-write-off text`);
  if (!inspected.hasProviderBreakdown) failures.push(`${prefix}: missing provider breakdown`);
  if (inspected.gateCount < 5) failures.push(`${prefix}: expected at least 5 receipt gates`);
  if (inspected.overflowX) failures.push(`${prefix}: horizontal overflow (${inspected.scrollWidth} > ${inspected.innerWidth})`);
  if ((inspected.sectionRect?.width ?? 0) < 720) failures.push(`${prefix}: receipt section unexpectedly narrow`);
  for (const error of runtimeErrors) failures.push(`${prefix}: runtime error: ${error}`);
  return failures;
}

async function main() {
  fs.mkdirSync(outputDir, { recursive: true });
  const results = [];
  const failures = [];
  for (const viewport of viewports) {
    const result = await inspect(viewport);
    results.push(result);
    failures.push(...validate(result));
  }
  fs.writeFileSync(
    path.join(outputDir, "summary.json"),
    JSON.stringify(
      results.map((result) => ({
        viewport: result.viewport.name,
        inspected: result.inspected,
        runtimeErrors: result.runtimeErrors
      })),
      null,
      2
    )
  );
  if (failures.length) {
    console.error("P3-06U-26H2W3D browser check failed:");
    failures.forEach((failure) => console.error(`- ${failure}`));
    process.exit(1);
  }
  console.log(`P3-06U-26H2W3D browser check passed. Evidence: ${outputDir}`);
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
