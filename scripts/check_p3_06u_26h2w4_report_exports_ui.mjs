import fs from "node:fs";
import path from "node:path";

const chromeEndpoint = process.env.CHROME_DEBUGGING_URL ?? "http://127.0.0.1:9227";
const frontendBaseUrl = process.env.FRONTEND_URL ?? "http://127.0.0.1:5182/?demo=1";
const outputDir = path.resolve(process.env.P3_06U_26H2W4_OUTPUT ?? "output/p3_06u_26h2w4_report_exports_ui");

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
    const ready = await waitFor(cdp, `Boolean(document.querySelector('[data-h2w4-report-export="p3-06u-26h2w4"]'))`);
    if (!ready) throw new Error(`${viewport.name}: H2W4 report export section did not become ready`);
    await delay(500);
    const inspected = await evalValue(cdp, `(() => {
      const root = document.documentElement;
      const body = document.body;
      const exportRoot = document.querySelector('[data-h2w4-report-export="p3-06u-26h2w4"]');
      const archiveRoot = document.querySelector('[data-h2w4-report-archives="p3-06u-26h2w4"]');
      const panelText = document.querySelector('[data-quality-smoke="quality-panel"]')?.innerText || "";
      const exportRect = exportRoot?.getBoundingClientRect();
      const archiveRect = archiveRoot?.getBoundingClientRect();
      return {
        href: location.href,
        hasExportRoot: Boolean(exportRoot),
        hasArchiveRoot: Boolean(archiveRoot),
        exportButtons: Array.from(exportRoot?.querySelectorAll("button") || []).map((button) => button.innerText.trim()),
        archiveItemCount: archiveRoot?.querySelectorAll(".customer-report-archive-items article").length || 0,
        hasSignatureBoundary: panelText.includes("不是正式电子签章"),
        hasNoRawTextBoundary: panelText.includes("不展示原始客户问题") || panelText.includes("不包含原始客户问题"),
        exportRect: exportRect ? { top: Math.round(exportRect.top), left: Math.round(exportRect.left), width: Math.round(exportRect.width), height: Math.round(exportRect.height) } : null,
        archiveRect: archiveRect ? { top: Math.round(archiveRect.top), left: Math.round(archiveRect.left), width: Math.round(archiveRect.width), height: Math.round(archiveRect.height) } : null,
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
    fs.writeFileSync(path.join(outputDir, `${viewport.name}-report-exports.png`), Buffer.from(screenshot.data, "base64"));
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
  const buttonText = inspected.exportButtons.join(" ");
  if (!inspected.hasExportRoot) failures.push(`${prefix}: missing report export root`);
  if (!inspected.hasArchiveRoot) failures.push(`${prefix}: missing report archive root`);
  for (const label of ["HTML 留档", "XLSX 明细", "DOCX 报告"]) {
    if (!buttonText.includes(label)) failures.push(`${prefix}: missing export button ${label}`);
  }
  if (inspected.archiveItemCount < 1) failures.push(`${prefix}: expected at least one archive row`);
  if (!inspected.hasSignatureBoundary) failures.push(`${prefix}: missing not-formal-e-signature boundary`);
  if (!inspected.hasNoRawTextBoundary) failures.push(`${prefix}: missing no raw customer question boundary`);
  if (inspected.overflowX) failures.push(`${prefix}: horizontal overflow (${inspected.scrollWidth} > ${inspected.innerWidth})`);
  if ((inspected.archiveRect?.width ?? 0) < 720) failures.push(`${prefix}: archive section unexpectedly narrow`);
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
  fs.writeFileSync(path.join(outputDir, "summary.json"), JSON.stringify({ results, failures }, null, 2));
  if (failures.length > 0) {
    throw new Error(`H2W4 report export UI smoke failed:\n${failures.join("\n")}`);
  }
  console.log(`H2W4 report export UI smoke passed. Evidence: ${outputDir}`);
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
