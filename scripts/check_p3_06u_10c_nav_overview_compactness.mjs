import fs from "node:fs";
import path from "node:path";

const chromeEndpoint = process.env.CHROME_DEBUGGING_URL ?? "http://127.0.0.1:9227";
const frontendUrl = process.env.FRONTEND_URL ?? "http://127.0.0.1:5181/";
const outputDir = path.resolve(process.env.P3_06U_10C_OUTPUT ?? "output/p3_06u_10c_nav_overview_compactness");

function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function createTarget(url) {
  const res = await fetch(`${chromeEndpoint}/json/new?${encodeURIComponent(url)}`, { method: "PUT" });
  if (!res.ok) {
    throw new Error(`Failed to create Chrome target: ${res.status}`);
  }
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
        send(method, params = {}) {
          const callId = ++id;
          ws.send(JSON.stringify({ id: callId, method, params }));
          return new Promise((resolve, reject) => pending.set(callId, { resolve, reject }));
        },
        waitFor(method, timeout = 8000) {
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
  if (result.exceptionDetails) {
    throw new Error(JSON.stringify(result.exceptionDetails));
  }
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

async function capture(cdp, name) {
  fs.mkdirSync(outputDir, { recursive: true });
  const screenshot = await cdp.send("Page.captureScreenshot", {
    format: "png",
    fromSurface: true,
    captureBeyondViewport: false
  });
  fs.writeFileSync(path.join(outputDir, `${name}.png`), Buffer.from(screenshot.data, "base64"));
}

async function runViewport(width, height, name) {
  const target = await createTarget(frontendUrl);
  const cdp = await createCdp(target.webSocketDebuggerUrl);
  try {
    await cdp.send("Page.enable");
    await cdp.send("Runtime.enable");
    await cdp.send("Emulation.setDeviceMetricsOverride", {
      width,
      height,
      deviceScaleFactor: 1,
      mobile: width < 700
    });
    await cdp.waitFor("Page.loadEventFired", 12000).catch(() => undefined);
    await waitFor(cdp, `Boolean(document.querySelector('[data-role-smoke="login-form"], .workspace'))`);
    await evalValue(cdp, `window.localStorage.removeItem("wanfa_standard_ops_access_token"); true;`);
    await cdp.send("Page.navigate", { url: frontendUrl });
    await cdp.waitFor("Page.loadEventFired", 12000).catch(() => undefined);
    await waitFor(cdp, `Boolean(document.querySelector('[data-role-smoke="login-form"]'))`);
    await evalValue(cdp, `document.querySelector('.ghost-action')?.click(); true;`);
    await waitFor(cdp, `Boolean(document.querySelector('.workspace-overview')) && location.hash === "#overview"`, 15000);
    await delay(900);

    const beforeExpand = await evalValue(cdp, `(() => {
      const sidebar = document.querySelector('.sidebar');
      const workspace = document.querySelector('.workspace');
      const workbenchGroup = Array.from(document.querySelectorAll('.nav-group-link'))
        .find((item) => item.textContent?.includes('工作台'));
      const workbenchChildren = workbenchGroup?.closest('.nav-group')?.querySelector('.nav-child-list');
      const firstChart = document.querySelector('.ops-bi-command-center, .ops-bi-signal-strip, .ops-chart-trend');
      const roleTaskPaths = document.querySelector('.role-task-paths');
      const demoBanner = document.querySelector('.demo-banner');
      const runtimeStrip = document.querySelector('.workspace-state-ledger');
      const sidebarRect = sidebar?.getBoundingClientRect();
      const chartRect = firstChart?.getBoundingClientRect();
      return {
        hash: location.hash,
        sidebarWidth: sidebarRect?.width ?? 0,
        workspaceTop: workspace?.getBoundingClientRect().top ?? null,
        workbenchExpanded: workbenchGroup?.getAttribute('aria-expanded') ?? null,
        childListDisplay: workbenchChildren ? getComputedStyle(workbenchChildren).display : null,
        hasRoleTaskPaths: Boolean(roleTaskPaths),
        hasDemoBanner: Boolean(demoBanner),
        hasRuntimeStrip: Boolean(runtimeStrip),
        chartTop: chartRect?.top ?? null,
        chartVisible: Boolean(chartRect && chartRect.top < innerHeight && chartRect.bottom > 0),
        overflowX: document.documentElement.scrollWidth > innerWidth || document.body.scrollWidth > innerWidth
      };
    })()`);

    await evalValue(cdp, `Array.from(document.querySelectorAll('.nav-group-link')).find((item) => item.textContent?.includes('工作台'))?.click(); true;`);
    await delay(250);
    const afterExpand = await evalValue(cdp, `(() => {
      const workbenchGroup = Array.from(document.querySelectorAll('.nav-group-link'))
        .find((item) => item.textContent?.includes('工作台'));
      const childLabels = Array.from(workbenchGroup?.closest('.nav-group')?.querySelectorAll('.nav-child-list a') ?? [])
        .filter((item) => getComputedStyle(item).display !== 'none')
        .map((item) => item.textContent?.trim() ?? '');
      return {
        workbenchExpanded: workbenchGroup?.getAttribute('aria-expanded') ?? null,
        childLabels
      };
    })()`);

    await capture(cdp, `${name}-overview`);
    return { viewport: { width, height, name }, beforeExpand, afterExpand };
  } finally {
    cdp.close();
    await closeTarget(target.id);
  }
}

async function main() {
  fs.mkdirSync(outputDir, { recursive: true });
  const results = [
    await runViewport(1440, 960, "desktop"),
    await runViewport(390, 1000, "mobile")
  ];
  const failures = [];
  for (const result of results) {
    const prefix = result.viewport.name;
    if (result.beforeExpand.hash !== "#overview") failures.push(`${prefix}: should land on overview`);
    if (result.viewport.width >= 700 && result.beforeExpand.sidebarWidth > 240) {
      failures.push(`${prefix}: sidebar too wide: ${result.beforeExpand.sidebarWidth}`);
    }
    if (result.beforeExpand.hasRoleTaskPaths) failures.push(`${prefix}: overview should not show role task paths`);
    if (result.beforeExpand.hasDemoBanner) failures.push(`${prefix}: overview should not show demo banner`);
    if (result.beforeExpand.hasRuntimeStrip) failures.push(`${prefix}: overview should not show runtime strip`);
    if (!result.beforeExpand.chartVisible) failures.push(`${prefix}: overview BI must be visible in first viewport`);
    if (result.beforeExpand.overflowX) failures.push(`${prefix}: horizontal overflow detected`);
    if (result.viewport.width >= 700 && result.beforeExpand.workbenchExpanded !== "false") {
      failures.push(`${prefix}: workbench group should be collapsed before click`);
    }
    if (result.viewport.width >= 700 && result.afterExpand.workbenchExpanded !== "true") {
      failures.push(`${prefix}: workbench group should expand after click`);
    }
    for (const label of ["多渠道对话台", "人工审核", "待发送草稿", "工单/SLA"]) {
      if (result.viewport.width >= 700 && !result.afterExpand.childLabels.join(" ").includes(label)) {
        failures.push(`${prefix}: expanded workbench missing ${label}`);
      }
    }
  }

  const summary = { results, failures };
  fs.writeFileSync(path.join(outputDir, "summary.json"), JSON.stringify(summary, null, 2));
  if (failures.length > 0) {
    for (const failure of failures) console.error(`FAIL ${failure}`);
    process.exitCode = 1;
    return;
  }
  console.log(`P3-06U-10C nav overview compactness browser check passed. Output: ${outputDir}`);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
