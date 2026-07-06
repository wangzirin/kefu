import fs from "node:fs";
import path from "node:path";

const chromeEndpoint = process.env.CHROME_DEBUGGING_URL ?? "http://127.0.0.1:9227";
const frontendBaseUrl = process.env.FRONTEND_BASE_URL ?? "http://127.0.0.1:5182";
const outputDir = path.resolve(process.env.P3_06U_26A_OUTPUT ?? "output/p3_06u_26a_customer_facing_copy");
const forbiddenTerms = ["演示", "演示模式", "演示样本", "开发演示身份", "开发演示进入", "本地测试进入"];

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

async function inspectPage(name, url, waitExpression, prepareExpression = null) {
  const target = await createTarget("about:blank");
  const cdp = await createCdp(target.webSocketDebuggerUrl);
  try {
    await cdp.send("Page.enable");
    await cdp.send("Runtime.enable");
    await cdp.send("Network.enable");
    await cdp.send("Emulation.setDeviceMetricsOverride", {
      width: 1440,
      height: 900,
      deviceScaleFactor: 1,
      mobile: false
    });
    await cdp.send("Page.navigate", { url });
    await cdp.waitFor("Page.loadEventFired", 12000).catch(() => undefined);
    if (prepareExpression) {
      await evalValue(cdp, prepareExpression);
      await cdp.waitFor("Page.loadEventFired", 12000).catch(() => undefined);
    }
    const ready = await waitFor(cdp, waitExpression);
    const inspected = await evalValue(cdp, `(() => ({
      href: location.href,
      bodyText: document.body.innerText,
      hasLogin: Boolean(document.querySelector('[data-role-smoke="login-form"]')),
      hasDesk: Boolean(document.querySelector('.wechat-service-desk')),
      hasPreviewButton: Boolean(document.querySelector('[data-role-smoke="preview-workspace"]')),
      hasLocalDevButton: Boolean(document.querySelector('[data-role-smoke="local-dev-login"]')),
      hasExternalWriteOff: document.body.innerText.includes('真实外发关闭'),
      hasPreviewData: document.body.innerText.includes('样例数据') || document.body.innerText.includes('预览工作区')
    }))()`);
    const screenshot = await cdp.send("Page.captureScreenshot", {
      format: "png",
      fromSurface: true,
      captureBeyondViewport: false
    });
    fs.writeFileSync(path.join(outputDir, `${name}.png`), Buffer.from(screenshot.data, "base64"));
    const runtimeErrors = cdp.events
      .filter((event) => event.method === "Runtime.exceptionThrown")
      .map((event) => event.params?.exceptionDetails?.exception?.description || event.params?.exceptionDetails?.text || "runtime error");
    return { name, ready, inspected, runtimeErrors };
  } finally {
    cdp.close();
    await closeTarget(target.id);
  }
}

function validate(result) {
  const failures = [];
  const text = result.inspected.bodyText || "";
  if (!result.ready) failures.push(`${result.name}: page did not become ready`);
  for (const term of forbiddenTerms) {
    if (text.includes(term)) failures.push(`${result.name}: forbidden term visible: ${term}`);
  }
  result.runtimeErrors.forEach((error) => failures.push(`${result.name}: runtime error: ${error}`));
  return failures;
}

fs.mkdirSync(outputDir, { recursive: true });
const login = await inspectPage(
  "login",
  frontendBaseUrl,
  `Boolean(document.querySelector('[data-role-smoke="login-form"]'))`,
  `localStorage.removeItem('wanfa_standard_ops_access_token'); location.href='${frontendBaseUrl}/'; true`
);
const preview = await inspectPage(
  "preview-live",
  `${frontendBaseUrl}/?demo=1#live`,
  `Boolean(document.querySelector('.wechat-service-desk'))`
);

const failures = [
  ...validate(login),
  ...validate(preview)
];
if (!login.inspected.hasLogin || !login.inspected.hasPreviewButton || !login.inspected.hasLocalDevButton) {
  failures.push("login: expected login form and stable smoke buttons");
}
if (!preview.inspected.hasDesk || !preview.inspected.hasExternalWriteOff || !preview.inspected.hasPreviewData) {
  failures.push("preview-live: expected desk, external write boundary, and preview data copy");
}

const summary = { ok: failures.length === 0, failures, results: [login, preview] };
fs.writeFileSync(path.join(outputDir, "summary.json"), JSON.stringify(summary, null, 2));
if (failures.length) {
  console.error(failures.join("\n"));
  process.exit(1);
}
console.log(`PASS p3_06u_26a_customer_facing_copy ${outputDir}`);
