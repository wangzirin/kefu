import fs from "node:fs";
import path from "node:path";

const chromeEndpoint = process.env.CHROME_DEBUGGING_URL ?? "http://127.0.0.1:9227";
const frontendUrl = process.env.FRONTEND_URL ?? "http://127.0.0.1:5182/?demo=1";
const outputDir = path.resolve(process.env.P3_06U_26G_OUTPUT ?? "output/p3_06u_26g_channel_sandbox_rpa_boundary");

const checks = [
  {
    name: "channels-desktop",
    hash: "#channels",
    width: 1440,
    height: 900,
    selector: '[data-channel-sandbox-priority="p3-06u-26g"]',
    requiredText: ["官方 sandbox 优先级", "RPA draft-only", "RPA 不进入正式默认交付链", "真实外发继续关闭", "官方授权"]
  },
  {
    name: "channels-desktop-1180",
    hash: "#channels",
    width: 1180,
    height: 768,
    selector: '[data-channel-sandbox-priority="p3-06u-26g"]',
    requiredText: ["官方 sandbox 优先级", "RPA draft-only", "真实外发继续关闭"]
  }
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
    await delay(200);
  }
  return false;
}

function withHash(baseUrl, hash) {
  const clean = baseUrl.replace(/#.*$/, "");
  return `${clean}${hash}`;
}

async function runCheck(check) {
  const target = await createTarget("about:blank");
  const cdp = await createCdp(target.webSocketDebuggerUrl);
  try {
    await cdp.send("Page.enable");
    await cdp.send("Runtime.enable");
    await cdp.send("Emulation.setDeviceMetricsOverride", {
      width: check.width,
      height: check.height,
      deviceScaleFactor: 1,
      mobile: false
    });
    await cdp.send("Page.navigate", { url: withHash(frontendUrl, check.hash) });
    await waitFor(cdp, `Boolean(document.querySelector(${JSON.stringify(check.selector)}))`);
    await evalValue(cdp, `document.querySelector(${JSON.stringify(check.selector)})?.scrollIntoView({ block: 'center' })`);
    await delay(500);
    const inspected = await evalValue(cdp, `(() => {
      const target = document.querySelector(${JSON.stringify(check.selector)});
      const text = document.body.innerText;
      const rect = target?.getBoundingClientRect();
      return {
        href: location.href,
        hasTarget: Boolean(target),
        text,
        targetRect: rect ? { top: Math.round(rect.top), left: Math.round(rect.left), width: Math.round(rect.width), height: Math.round(rect.height) } : null,
        overflowX: document.documentElement.scrollWidth > innerWidth || document.body.scrollWidth > innerWidth,
        scrollWidth: document.documentElement.scrollWidth,
        innerWidth
      };
    })()`);
    const screenshot = await cdp.send("Page.captureScreenshot", {
      format: "png",
      fromSurface: true,
      captureBeyondViewport: false
    });
    fs.writeFileSync(path.join(outputDir, `${check.name}.png`), Buffer.from(screenshot.data, "base64"));
    const runtimeErrors = cdp.events
      .filter((event) => event.method === "Runtime.exceptionThrown")
      .map((event) => event.params?.exceptionDetails?.exception?.description || event.params?.exceptionDetails?.text || "runtime error");
    return { check, inspected, runtimeErrors };
  } finally {
    cdp.close();
    await closeTarget(target.id);
  }
}

function validate(result) {
  const failures = [];
  const { check, inspected, runtimeErrors } = result;
  if (!inspected.hasTarget) failures.push(`${check.name}: boundary block did not render`);
  for (const text of check.requiredText) {
    if (!inspected.text.includes(text)) failures.push(`${check.name}: missing text ${text}`);
  }
  if (inspected.text.includes("真实外发已开启")) failures.push(`${check.name}: page suggests external write is enabled`);
  if (inspected.overflowX) failures.push(`${check.name}: horizontal overflow (${inspected.scrollWidth} > ${inspected.innerWidth})`);
  for (const error of runtimeErrors) failures.push(`${check.name}: runtime error: ${error}`);
  return failures;
}

async function main() {
  fs.mkdirSync(outputDir, { recursive: true });
  const results = [];
  const failures = [];
  for (const check of checks) {
    const result = await runCheck(check);
    results.push(result);
    failures.push(...validate(result));
  }
  fs.writeFileSync(
    path.join(outputDir, "summary.json"),
    JSON.stringify(
      results.map((result) => ({
        check: result.check,
        inspected: result.inspected,
        runtimeErrors: result.runtimeErrors
      })),
      null,
      2
    )
  );
  if (failures.length) {
    console.error("P3-06U-26G browser check failed:");
    failures.forEach((failure) => console.error(`- ${failure}`));
    process.exit(1);
  }
  console.log(`P3-06U-26G browser check passed. Evidence: ${outputDir}`);
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
