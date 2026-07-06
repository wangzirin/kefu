import fs from "node:fs";
import path from "node:path";

const chromeEndpoint = process.env.CHROME_DEBUGGING_URL ?? "http://127.0.0.1:9227";
const frontendUrl = process.env.FRONTEND_URL ?? "http://127.0.0.1:5182/?demo=1#live";
const outputDir = path.resolve(process.env.P3_06U_23_OUTPUT ?? "output/p3_06u_23_channel_identity_preview");

const viewports = [
  { name: "desktop-1440", width: 1440, height: 900, mobile: false },
  { name: "mobile-390", width: 390, height: 844, mobile: true }
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
    await delay(200);
  }
  return false;
}

async function inspectViewport(viewport) {
  const target = await createTarget("about:blank");
  const cdp = await createCdp(target.webSocketDebuggerUrl);
  try {
    await cdp.send("Page.enable");
    await cdp.send("Runtime.enable");
    await cdp.send("Network.enable");
    await cdp.send("Emulation.setDeviceMetricsOverride", {
      width: viewport.width,
      height: viewport.height,
      deviceScaleFactor: 1,
      mobile: viewport.mobile
    });
    await cdp.send("Page.navigate", { url: frontendUrl });
    await cdp.waitFor("Page.loadEventFired", 12000).catch(() => undefined);
    const ready = await waitFor(cdp, `Boolean(document.querySelector('[data-channel-identity-strip="p3-06u-23"]'))`);
    const inspected = await evalValue(cdp, `(() => {
      const identity = document.querySelector('[data-channel-identity-strip="p3-06u-23"]');
      const decision = document.querySelector('[data-reply-decision-strip="p3-06u-22"]');
      const list = document.querySelector('.wechat-session-list');
      const chat = document.querySelector('.wechat-chat-pane');
      const rect = (node) => {
        const item = node?.getBoundingClientRect();
        return item ? { width: Math.round(item.width), height: Math.round(item.height), left: Math.round(item.left), top: Math.round(item.top) } : null;
      };
      return {
        href: location.href,
        hash: location.hash,
        hasLogin: Boolean(document.querySelector('[data-role-smoke="login-form"]')),
        hasDesk: Boolean(document.querySelector('.wechat-service-desk')),
        hasIdentity: Boolean(identity),
        hasDecision: Boolean(decision),
        identityText: identity?.textContent || '',
        bodyText: document.body.innerText,
        listRect: rect(list),
        chatRect: rect(chat),
        overflowX: document.documentElement.scrollWidth > innerWidth || document.body.scrollWidth > innerWidth
      };
    })()`);
    const runtimeErrors = cdp.events
      .filter((event) => event.method === "Runtime.exceptionThrown")
      .map((event) => event.params?.exceptionDetails?.exception?.description || event.params?.exceptionDetails?.text || "runtime error");
    const screenshot = await cdp.send("Page.captureScreenshot", {
      format: "png",
      fromSurface: true,
      captureBeyondViewport: false
    });
    fs.writeFileSync(path.join(outputDir, `${viewport.name}.png`), Buffer.from(screenshot.data, "base64"));
    return { viewport, ready, inspected, runtimeErrors };
  } finally {
    cdp.close();
    await closeTarget(target.id);
  }
}

function validate(result) {
  const failures = [];
  const { viewport, ready, inspected, runtimeErrors } = result;
  const prefix = viewport.name;
  if (!ready || !inspected.hasIdentity) failures.push(`${prefix}: channel identity strip missing`);
  if (!inspected.hasDesk) failures.push(`${prefix}: live desk missing`);
  if (inspected.hasLogin) failures.push(`${prefix}: still stuck on login`);
  if (!inspected.hasDecision) failures.push(`${prefix}: reply decision strip missing`);
  if (!inspected.identityText.includes("平台") || !inspected.identityText.includes("账号") || !inspected.identityText.includes("回复")) {
    failures.push(`${prefix}: identity labels incomplete`);
  }
  if (!inspected.bodyText.includes("万法常世AI客服测试") && !inspected.bodyText.includes("EricLee抖音测试号")) {
    failures.push(`${prefix}: demo account names not rendered`);
  }
  if (inspected.overflowX) failures.push(`${prefix}: horizontal overflow`);
  if (!viewport.mobile && inspected.listRect?.width > 238) failures.push(`${prefix}: session list too wide: ${inspected.listRect.width}`);
  if (!viewport.mobile && inspected.chatRect && inspected.listRect && inspected.chatRect.width <= inspected.listRect.width * 2.8) {
    failures.push(`${prefix}: chat pane should dominate the session list`);
  }
  if (viewport.mobile && inspected.chatRect?.width > viewport.width) failures.push(`${prefix}: chat pane wider than viewport`);
  runtimeErrors.forEach((error) => failures.push(`${prefix}: runtime error: ${error}`));
  return failures;
}

fs.mkdirSync(outputDir, { recursive: true });
const results = [];
for (const viewport of viewports) {
  results.push(await inspectViewport(viewport));
}
const failures = results.flatMap(validate);
fs.writeFileSync(path.join(outputDir, "summary.json"), JSON.stringify({ ok: failures.length === 0, failures, results }, null, 2));
if (failures.length) {
  console.error(failures.join("\n"));
  process.exit(1);
}
console.log(`PASS p3_06u_23_channel_identity_preview ${outputDir}`);
