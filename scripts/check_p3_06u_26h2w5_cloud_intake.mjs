import fs from "node:fs";
import path from "node:path";

const chromeEndpoint = process.env.CHROME_DEBUGGING_URL ?? "http://127.0.0.1:9227";
const frontendBaseUrl = process.env.FRONTEND_URL ?? "http://127.0.0.1:5182/";
const apiBaseUrl = process.env.API_URL ?? new URL(frontendBaseUrl).origin;
const outputDir = path.resolve(process.env.P3_06U_26H2W5_OUTPUT ?? "output/p3_06u_26h2w5_cloud_intake_ui");
const tokenStorageKey = "wanfa_standard_ops_access_token";

const viewports = [
  { name: "desktop-1440", width: 1440, height: 900 },
  { name: "desktop-1280", width: 1280, height: 800 },
  { name: "desktop-1180", width: 1180, height: 768 }
];

function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function pageUrl() {
  return `${frontendBaseUrl}#settings`;
}

async function requestJson(pathname, options = {}) {
  const res = await fetch(`${apiBaseUrl}${pathname}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {})
    }
  });
  const body = await res.text();
  const json = body ? JSON.parse(body) : {};
  if (!res.ok) throw new Error(`API ${pathname} failed ${res.status}: ${body}`);
  return json;
}

async function prepareOwnerToken() {
  const stamp = Date.now();
  const tenant = await requestJson("/api/tenants", {
    method: "POST",
    body: JSON.stringify({
      name: `H2W5 售后接收台临时空间 ${stamp}`,
      slug: `h2w5-cloud-intake-${stamp}`
    })
  });
  const role = await requestJson(`/api/tenants/${tenant.id}/roles`, {
    method: "POST",
    body: JSON.stringify({ code: "owner", name: "负责人" })
  });
  const email = `owner-${stamp}@wanfa.local`;
  const password = "ChangeMe123!";
  const user = await requestJson(`/api/tenants/${tenant.id}/users`, {
    method: "POST",
    body: JSON.stringify({
      name: "H2W5 临时负责人",
      email,
      password
    })
  });
  await requestJson(`/api/users/${user.id}/roles`, {
    method: "POST",
    body: JSON.stringify({ role_id: role.id })
  });
  const login = await requestJson("/api/auth/login", {
    method: "POST",
    body: JSON.stringify({
      tenant_slug: tenant.slug,
      email,
      password
    })
  });
  return login.access_token;
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

async function inspect(viewport, token) {
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
    await cdp.send("Page.navigate", { url: new URL(frontendBaseUrl).origin });
    await cdp.waitFor("Page.loadEventFired", 12000).catch(() => undefined);
    await evalValue(cdp, `window.localStorage.setItem(${JSON.stringify(tokenStorageKey)}, ${JSON.stringify(token)})`);
    await cdp.send("Page.navigate", { url: pageUrl() });
    await cdp.waitFor("Page.loadEventFired", 12000).catch(() => undefined);
    const ready = await waitFor(cdp, `Boolean(document.querySelector('[data-h2w5-cloud-intake="p3-06u-26h2w5"]'))`);
    if (!ready) throw new Error(`${viewport.name}: H2W5 cloud intake section did not become ready`);
    await evalValue(
      cdp,
      `document.querySelector('[data-h2w5-cloud-intake="p3-06u-26h2w5"]')?.scrollIntoView({block:"center"})`
    );
    await delay(500);
    const inspected = await evalValue(cdp, `(() => {
      const root = document.documentElement;
      const body = document.body;
      const intakeRoot = document.querySelector('[data-h2w5-cloud-intake="p3-06u-26h2w5"]');
      const text = intakeRoot?.innerText || "";
      const rect = intakeRoot?.getBoundingClientRect();
      return {
        href: location.href,
        hasIntakeRoot: Boolean(intakeRoot),
        hasTextarea: Boolean(intakeRoot?.querySelector("textarea")),
        buttons: Array.from(intakeRoot?.querySelectorAll("button") || []).map((button) => button.innerText.trim()),
        hasList: Boolean(document.querySelector('[data-h2w5-cloud-intake-list="p3-06u-26h2w5"]')),
        hasAuthorizationBoundary: text.includes("客户主动授权"),
        hasRedactionBoundary: text.includes("脱敏包校验"),
        hasNoRemoteControlBoundary: text.includes("不远控客户电脑") || text.includes("不远程控制客户电脑"),
        hasNoAutoUploadBoundary: text.includes("不自动联网采集"),
        hasForbiddenRemoteClaim: text.includes("远程控制客户电脑") && !text.includes("不远程控制客户电脑"),
        rect: rect ? { top: Math.round(rect.top), left: Math.round(rect.left), width: Math.round(rect.width), height: Math.round(rect.height) } : null,
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
    fs.writeFileSync(path.join(outputDir, `${viewport.name}-cloud-intake.png`), Buffer.from(screenshot.data, "base64"));
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
  const buttonText = inspected.buttons.join(" ");
  if (!inspected.hasIntakeRoot) failures.push(`${prefix}: missing cloud intake root`);
  if (!inspected.hasTextarea) failures.push(`${prefix}: missing upload package textarea`);
  if (!buttonText.includes("登记接收")) failures.push(`${prefix}: missing register button`);
  if (!inspected.hasList) failures.push(`${prefix}: missing intake list`);
  if (!inspected.hasAuthorizationBoundary) failures.push(`${prefix}: missing customer authorization boundary`);
  if (!inspected.hasRedactionBoundary) failures.push(`${prefix}: missing redaction check boundary`);
  if (!inspected.hasNoRemoteControlBoundary) failures.push(`${prefix}: missing no remote control boundary`);
  if (!inspected.hasNoAutoUploadBoundary) failures.push(`${prefix}: missing no automatic upload boundary`);
  if (inspected.hasForbiddenRemoteClaim) failures.push(`${prefix}: remote control claim is not negated`);
  if (inspected.overflowX) failures.push(`${prefix}: horizontal overflow (${inspected.scrollWidth} > ${inspected.innerWidth})`);
  if ((inspected.rect?.width ?? 0) < 720) failures.push(`${prefix}: intake section unexpectedly narrow`);
  for (const error of runtimeErrors) failures.push(`${prefix}: runtime error: ${error}`);
  return failures;
}

async function main() {
  fs.mkdirSync(outputDir, { recursive: true });
  const token = await prepareOwnerToken();
  const results = [];
  const failures = [];
  for (const viewport of viewports) {
    const result = await inspect(viewport, token);
    results.push(result);
    failures.push(...validate(result));
  }
  fs.writeFileSync(path.join(outputDir, "summary.json"), JSON.stringify({ results, failures }, null, 2));
  if (failures.length > 0) {
    throw new Error(`H2W5 cloud intake UI smoke failed:\n${failures.join("\n")}`);
  }
  console.log(`H2W5 cloud intake UI smoke passed. Evidence: ${outputDir}`);
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
