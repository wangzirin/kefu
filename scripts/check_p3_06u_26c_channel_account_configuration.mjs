import fs from "node:fs";
import path from "node:path";

const chromeEndpoint = process.env.CHROME_DEBUGGING_URL ?? "http://127.0.0.1:9227";
const frontendUrl = process.env.FRONTEND_URL ?? "http://127.0.0.1:5182/?demo=1#channels";
const outputDir = path.resolve(process.env.P3_06U_26C_OUTPUT ?? "output/p3_06u_26c_channel_account_configuration");

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
    const ready = await waitFor(cdp, `Boolean(document.querySelector('[data-channel-account-manager="p3-06u-26c"]'))`);
    if (!ready) throw new Error(`${viewport.name}: channel account manager did not become ready`);
    await evalValue(cdp, `document.querySelector('[data-channel-account-manager="p3-06u-26c"]')?.scrollIntoView({ block: 'center' })`);
    await delay(450);
    const inspected = await evalValue(cdp, `(() => {
      const rect = (selector) => {
        const node = document.querySelector(selector);
        const item = node?.getBoundingClientRect();
        return item ? { top: Math.round(item.top), left: Math.round(item.left), width: Math.round(item.width), height: Math.round(item.height), bottom: Math.round(item.bottom) } : null;
      };
      const text = document.body.innerText;
      const root = document.documentElement;
      const body = document.body;
      return {
        href: location.href,
        text,
        hasManager: Boolean(document.querySelector('[data-channel-account-manager="p3-06u-26c"]')),
        hasList: Boolean(document.querySelector('[data-channel-account-list="server"]')),
        hasForm: Boolean(document.querySelector('[data-channel-account-form="server"]')),
        hasRefresh: Boolean(document.querySelector('[data-channel-account-refresh="p3-06u-26c"]')),
        managerRect: rect('[data-channel-account-manager="p3-06u-26c"]'),
        formRect: rect('[data-channel-account-form="server"]'),
        hasTitle: text.includes('渠道账号 / 店铺管理') && text.includes('服务端 channel_accounts 配置'),
        hasBoundary: text.includes('真实外发继续关闭') || text.includes('真实外发关闭'),
        hasSecretBoundary: text.includes('Secret') && text.includes('Token') && text.includes('Cookie'),
        hasEmptyOrList: text.includes('尚未登记服务端渠道账号') || text.includes('需要正式登录后读取渠道账号') || document.querySelectorAll('[data-channel-account-id]').length > 0,
        hasPreviewBoundary: text.includes('正式配置需登录后读取 channel_accounts') || text.includes('正式登录后读取渠道账号'),
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
    fs.writeFileSync(path.join(outputDir, `${viewport.name}.png`), Buffer.from(screenshot.data, "base64"));
    const runtimeErrors = cdp.events
      .filter((event) => event.method === "Runtime.exceptionThrown")
      .map((event) => event.params?.exceptionDetails?.exception?.description || event.params?.exceptionDetails?.text || "runtime error");
    return { viewport, inspected, runtimeErrors };
  } finally {
    cdp.close();
    await closeTarget(target.id);
  }
}

function validate({ viewport, inspected, runtimeErrors }) {
  const failures = [];
  const prefix = viewport.name;
  for (const [key, label] of [
    ["hasManager", "channel account manager"],
    ["hasList", "server account list"],
    ["hasForm", "server account form"],
    ["hasRefresh", "refresh action"],
    ["hasTitle", "manager title"],
    ["hasBoundary", "external write boundary"],
    ["hasSecretBoundary", "secret boundary"],
    ["hasEmptyOrList", "empty/list state"],
    ["hasPreviewBoundary", "preview boundary"]
  ]) {
    if (!inspected[key]) failures.push(`${prefix}: missing ${label}`);
  }
  if (inspected.overflowX) failures.push(`${prefix}: horizontal overflow (${inspected.scrollWidth} > ${inspected.innerWidth})`);
  if (inspected.managerRect?.width < 640) {
    failures.push(`${prefix}: manager is unexpectedly narrow`);
  }
  for (const error of runtimeErrors) failures.push(`${prefix}: runtime error: ${error}`);
  return failures;
}

async function main() {
  fs.mkdirSync(outputDir, { recursive: true });
  const results = [];
  const failures = [];
  for (const viewport of viewports) {
    const result = await runViewport(viewport);
    results.push(result);
    failures.push(...validate(result));
  }
  fs.writeFileSync(
    path.join(outputDir, "summary.json"),
    JSON.stringify(
      results.map((result) => ({
        viewport: result.viewport,
        inspected: result.inspected,
        runtimeErrors: result.runtimeErrors
      })),
      null,
      2
    )
  );
  if (failures.length) {
    console.error("P3-06U-26C browser check failed:");
    failures.forEach((failure) => console.error(`- ${failure}`));
    process.exit(1);
  }
  console.log(`P3-06U-26C browser check passed. Evidence: ${outputDir}`);
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
