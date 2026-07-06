import fs from "node:fs";
import path from "node:path";

const chromeEndpoint = process.env.CHROME_DEBUGGING_URL ?? "http://127.0.0.1:9227";
const frontendUrl = process.env.FRONTEND_URL ?? "http://127.0.0.1:5181/";
const outputDir = path.resolve(process.env.P3_06U_12B_OUTPUT ?? "output/p3_06u_12b_rpa_copilot_lab_entry");

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
    await waitFor(cdp, `Boolean(document.querySelector('[data-rpa-lab="p3-06u-12b"], [data-role-smoke="login-form"]'))`);
    const initial = await evalValue(cdp, `(() => ({
      hash: location.hash,
      hasLab: Boolean(document.querySelector('[data-rpa-lab="p3-06u-12b"]')),
      hasLogin: Boolean(document.querySelector('[data-role-smoke="login-form"]')),
      hasRolePaths: Boolean(document.querySelector('.role-task-paths')),
      hasRuntimeStrip: Boolean(document.querySelector('.workspace-state-ledger')),
      activeNavText: document.querySelector('.nav-group.active')?.textContent?.trim() ?? '',
      tokenPresent: Boolean(localStorage.getItem('wanfa_standard_ops_access_token'))
    }))()`);
    if (initial.hasLogin || !initial.tokenPresent) {
      failures.push("Chrome profile has no valid local login token; cannot run authenticated RPA lab browser smoke.");
    }
    if (initial.hash !== "#rpa-lab") failures.push(`expected #rpa-lab, got ${initial.hash}`);
    if (!initial.hasLab) failures.push("RPA lab panel not rendered");
    if (initial.hasRolePaths) failures.push("RPA lab should not show role task paths");
    if (initial.hasRuntimeStrip) failures.push("RPA lab should not show runtime strip");

    if (failures.length === 0) {
      await evalValue(cdp, `Array.from(document.querySelectorAll('button')).find((button) => button.textContent?.includes('运行策略试算'))?.click(); true;`);
      await waitFor(cdp, `Boolean(document.querySelector('.rpa-strategy-card'))`, 15000);
      await delay(500);
    }
    const afterRun = await evalValue(cdp, `(() => {
      const card = document.querySelector('.rpa-strategy-card');
      const bodyText = document.body.innerText;
      return {
        hasStrategyCard: Boolean(card),
        strategyText: card?.textContent?.trim() ?? '',
        hasExternalWriteTrue: bodyText.includes('external_write": true') || bodyText.includes('真实外发已开启'),
        hasDraft: Boolean(document.querySelector('.rpa-lab-draft')),
        overflowX: document.documentElement.scrollWidth > innerWidth || document.body.scrollWidth > innerWidth
      };
    })()`);
    if (failures.length === 0 && !afterRun.hasStrategyCard) failures.push("strategy card did not render after dry-run");
    if (failures.length === 0 && !afterRun.hasDraft) failures.push("draft panel did not render after dry-run");
    if (afterRun.hasExternalWriteTrue) failures.push("page suggests external write is enabled");
    if (afterRun.overflowX) failures.push("horizontal overflow detected on RPA lab page");

    await capture(cdp, "desktop-rpa-lab");
    const summary = { initial, afterRun, failures };
    fs.writeFileSync(path.join(outputDir, "summary.json"), JSON.stringify(summary, null, 2));
    if (failures.length > 0) {
      for (const failure of failures) console.error(`FAIL ${failure}`);
      process.exitCode = 1;
      return;
    }
    console.log(`P3-06U-12B RPA copilot lab browser check passed. Output: ${outputDir}`);
  } finally {
    cdp.close();
    await closeTarget(target.id);
  }
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
