import fs from "node:fs";
import path from "node:path";

const chromeEndpoint = process.env.CHROME_DEBUGGING_URL ?? "http://127.0.0.1:9227";
const frontendUrl = process.env.FRONTEND_URL ?? "http://127.0.0.1:5181/";
const outputDir = path.resolve(process.env.P3_06U_12C_OUTPUT ?? "output/p3_06u_12c_login_route_and_live_strategy");

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
  return new Promise((resolve, reject) => {
    ws.addEventListener("open", () => {
      resolve({
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
    ws.addEventListener("message", (event) => {
      const msg = JSON.parse(event.data);
      if (msg.id && pending.has(msg.id)) {
        const { resolve, reject } = pending.get(msg.id);
        pending.delete(msg.id);
        if (msg.error) reject(new Error(JSON.stringify(msg.error)));
        else resolve(msg.result || {});
      }
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

async function waitFor(cdp, expression, timeout = 15000) {
  const started = Date.now();
  while (Date.now() - started < timeout) {
    if (await evalValue(cdp, expression)) return true;
    await delay(200);
  }
  return false;
}

async function capture(cdp, name) {
  fs.mkdirSync(outputDir, { recursive: true });
  const screenshot = await cdp.send("Page.captureScreenshot", {
    format: "png",
    fromSurface: true,
    captureBeyondViewport: false
  });
  fs.writeFileSync(path.join(outputDir, `${name}.png`), Buffer.from(screenshot.data, "base64"));
}

async function clickButtonContaining(cdp, text) {
  return evalValue(
    cdp,
    `(() => {
      const button = Array.from(document.querySelectorAll('button')).find((item) => item.textContent?.includes(${JSON.stringify(text)}));
      if (!button) return false;
      button.click();
      return true;
    })()`
  );
}

async function main() {
  fs.mkdirSync(outputDir, { recursive: true });
  const target = await createTarget(`${frontendUrl.replace(/#.*$/, "")}#rpa-lab`);
  const cdp = await createCdp(target.webSocketDebuggerUrl);
  const failures = [];
  try {
    await cdp.send("Page.enable");
    await cdp.send("Runtime.enable");
    await cdp.send("Emulation.setDeviceMetricsOverride", {
      width: 1440,
      height: 960,
      deviceScaleFactor: 1,
      mobile: false
    });
    await waitFor(cdp, "document.readyState === 'complete'");
    await evalValue(cdp, `localStorage.removeItem('wanfa_standard_ops_access_token'); location.hash = '#rpa-lab'; location.reload(); true;`);
    await waitFor(cdp, `Boolean(document.querySelector('[data-role-smoke="login-form"]'))`);

    const loginState = await evalValue(cdp, `(() => ({
      hash: location.hash,
      tenant: document.querySelector('[data-role-smoke="tenant-slug"]')?.value ?? '',
      email: document.querySelector('[data-role-smoke="email"]')?.value ?? '',
      hasLocalDevButton: Array.from(document.querySelectorAll('button')).some((button) => button.textContent?.includes('本地测试进入'))
    }))()`);
    if (loginState.hash !== "#rpa-lab") failures.push(`login should preserve #rpa-lab, got ${loginState.hash}`);
    if (loginState.tenant !== "wanfa-local-dev") failures.push(`login tenant default mismatch: ${loginState.tenant}`);
    if (loginState.email !== "real-test@wanfa.local") failures.push(`login email default mismatch: ${loginState.email}`);
    if (!loginState.hasLocalDevButton) failures.push("local dev login button missing");

    if (failures.length === 0) {
      const clicked = await clickButtonContaining(cdp, "本地测试进入");
      if (!clicked) failures.push("failed to click local dev login button");
      await waitFor(cdp, `Boolean(document.querySelector('[data-rpa-lab="p3-06u-12b"]'))`);
    }

    const labState = await evalValue(cdp, `(() => ({
      hash: location.hash,
      hasLab: Boolean(document.querySelector('[data-rpa-lab="p3-06u-12b"]')),
      hasLogin: Boolean(document.querySelector('[data-role-smoke="login-form"]')),
      tokenPresent: Boolean(localStorage.getItem('wanfa_standard_ops_access_token'))
    }))()`);
    if (labState.hash !== "#rpa-lab") failures.push(`after login should remain #rpa-lab, got ${labState.hash}`);
    if (!labState.hasLab) failures.push("RPA lab not rendered after local dev login");
    if (labState.hasLogin) failures.push("login form still visible after local dev login");
    if (!labState.tokenPresent) failures.push("token missing after local dev login");

    if (failures.length === 0) {
      await clickButtonContaining(cdp, "运行策略试算");
      await waitFor(cdp, `Boolean(document.querySelector('.rpa-strategy-card'))`);
    }
    await capture(cdp, "rpa-lab-after-local-login");

    await evalValue(cdp, `location.hash = '#live'; true;`);
    await waitFor(cdp, `Boolean(document.querySelector('#workspace-live'))`);
    await clickButtonContaining(cdp, "试算当前会话");
    await waitFor(cdp, `Boolean(document.querySelector('.service-strategy-grid'))`);
    await delay(500);
    const liveState = await evalValue(cdp, `(() => {
      const bodyText = document.body.innerText;
      return {
        hash: location.hash,
        hasLive: Boolean(document.querySelector('#workspace-live')),
        hasStrategyGrid: Boolean(document.querySelector('.service-strategy-grid')),
        strategyText: document.querySelector('.service-strategy-summary')?.textContent?.trim() ?? '',
        hasExternalWriteTrue: bodyText.includes('external_write": true') || bodyText.includes('真实外发已开启'),
        overflowX: document.documentElement.scrollWidth > innerWidth || document.body.scrollWidth > innerWidth
      };
    })()`);
    if (liveState.hash !== "#live") failures.push(`expected #live, got ${liveState.hash}`);
    if (!liveState.hasLive) failures.push("live workbench not rendered");
    if (!liveState.hasStrategyGrid) failures.push("live strategy dry-run summary did not render");
    if (liveState.hasExternalWriteTrue) failures.push("page suggests external write is enabled");
    if (liveState.overflowX) failures.push("horizontal overflow detected");
    await capture(cdp, "live-workbench-strategy-summary");

    const summary = { loginState, labState, liveState, failures };
    fs.writeFileSync(path.join(outputDir, "summary.json"), JSON.stringify(summary, null, 2));
    if (failures.length > 0) {
      for (const failure of failures) console.error(`FAIL ${failure}`);
      process.exitCode = 1;
      return;
    }
    console.log(`P3-06U-12C login route and live strategy browser check passed. Output: ${outputDir}`);
  } finally {
    cdp.close();
    await closeTarget(target.id);
  }
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
