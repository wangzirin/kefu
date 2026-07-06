import fs from "node:fs";
import path from "node:path";

const chromeEndpoint = process.env.CHROME_DEBUGGING_URL ?? "http://127.0.0.1:9224";
const frontendUrl = process.env.FRONTEND_URL ?? "http://127.0.0.1:5178/#overview";
const outputDir = path.resolve(process.env.P3_06U_02_OUTPUT ?? "output/p3_06u_02_role_task_paths");

const viewports = [
  { name: "desktop-1440", width: 1440, height: 900, mobile: false },
  { name: "narrow-900", width: 900, height: 768, mobile: false },
  { name: "mobile-390", width: 390, height: 844, mobile: true }
];

const inspectExpression = `(() => {
  const root = document.documentElement;
  const workspace = document.querySelector('.workspace');
  const sidebar = document.querySelector('.sidebar');
  const strip = document.querySelector('.role-task-paths');
  const taskRows = Array.from(document.querySelectorAll('.role-task-path'));
  const activeRows = Array.from(document.querySelectorAll('.role-task-path.is-active'));
  const labels = taskRows.map((item) => item.querySelector('.role-task-copy strong')?.textContent?.trim() ?? '');
  const metrics = taskRows.map((item) => item.querySelector('.role-task-metric strong')?.textContent?.trim() ?? '');
  const stripRect = strip?.getBoundingClientRect();
  const firstTaskRect = taskRows[0]?.getBoundingClientRect();
  return {
    hasWorkspace: Boolean(workspace),
    hasSidebar: Boolean(sidebar),
    hasStrip: Boolean(strip),
    heading: document.querySelector('.role-task-paths-heading strong')?.textContent?.trim() ?? null,
    taskCount: taskRows.length,
    activeCount: activeRows.length,
    labels,
    metrics,
    stripTop: stripRect ? Math.round(stripRect.top) : null,
    stripBottom: stripRect ? Math.round(stripRect.bottom) : null,
    firstTaskTop: firstTaskRect ? Math.round(firstTaskRect.top) : null,
    firstTaskWidth: firstTaskRect ? Math.round(firstTaskRect.width) : null,
    overflowX: root.scrollWidth > innerWidth || document.body.scrollWidth > innerWidth,
    documentScrollWidth: root.scrollWidth,
    bodyScrollWidth: document.body.scrollWidth,
    innerWidth,
    workspaceOverflowY: workspace ? getComputedStyle(workspace).overflowY : null,
    sidebarTop: sidebar?.getBoundingClientRect().top ?? null
  };
})()`;

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
      if (msg.error) {
        reject(new Error(JSON.stringify(msg.error)));
      } else {
        resolve(msg.result || {});
      }
      return;
    }
    if (msg.method) {
      events.push(msg);
    }
  });

  return new Promise((resolve, reject) => {
    ws.addEventListener("open", () => {
      resolve({
        send(method, params = {}) {
          const callId = ++id;
          ws.send(JSON.stringify({ id: callId, method, params }));
          return new Promise((resolve, reject) => {
            pending.set(callId, { resolve, reject });
          });
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

async function waitForSelector(cdp, selector) {
  for (let i = 0; i < 70; i += 1) {
    const result = await cdp.send("Runtime.evaluate", {
      awaitPromise: true,
      returnByValue: true,
      expression: `Boolean(document.querySelector(${JSON.stringify(selector)}))`
    });
    if (result.result.value) {
      return true;
    }
    await delay(200);
  }
  return false;
}

async function enterDemo(cdp) {
  await delay(600);
  await cdp.send("Runtime.evaluate", {
    awaitPromise: true,
    returnByValue: true,
    expression: `(() => {
      const button = Array.from(document.querySelectorAll('button')).find((item) =>
        item.textContent?.includes('开发演示进入')
      );
      if (button) {
        button.click();
      }
      return Boolean(button);
    })()`
  });
  return waitForSelector(cdp, ".role-task-paths");
}

async function measure(viewport) {
  const target = await createTarget("about:blank");
  const cdp = await createCdp(target.webSocketDebuggerUrl);
  try {
    await cdp.send("Page.enable");
    await cdp.send("Runtime.enable");
    await cdp.send("Emulation.setDeviceMetricsOverride", {
      width: viewport.width,
      height: viewport.height,
      deviceScaleFactor: 1,
      mobile: viewport.mobile
    });
    await cdp.send("Page.navigate", { url: frontendUrl });
    await cdp.waitFor("Page.loadEventFired", 12000).catch(() => undefined);
    const demoReady = await enterDemo(cdp);
    await delay(900);

    const inspection = await cdp.send("Runtime.evaluate", {
      awaitPromise: true,
      returnByValue: true,
      expression: inspectExpression
    });
    const screenshot = await cdp.send("Page.captureScreenshot", {
      format: "png",
      fromSurface: true,
      captureBeyondViewport: false
    });
    fs.writeFileSync(path.join(outputDir, `${viewport.name}.png`), Buffer.from(screenshot.data, "base64"));
    return {
      viewport,
      demoReady,
      inspection: inspection.result.value
    };
  } finally {
    cdp.close();
    await closeTarget(target.id);
  }
}

function validate(result) {
  const view = result.viewport;
  const data = result.inspection;
  const failures = [];
  const prefix = view.name;

  if (!result.demoReady || !data.hasWorkspace || !data.hasStrip) {
    failures.push(`${prefix}: role task path strip did not render`);
  }
  if (data.taskCount !== 5) {
    failures.push(`${prefix}: demo owner/admin view should expose 5 task paths, got ${data.taskCount}`);
  }
  for (const label of ["判断今日风险", "处理高风险草稿", "确认待发送", "修复知识缺口", "检查渠道接入"]) {
    if (!data.labels.includes(label)) {
      failures.push(`${prefix}: missing role task label ${label}`);
    }
  }
  if (data.activeCount < 1) {
    failures.push(`${prefix}: active task path state missing`);
  }
  if (data.metrics.some((item) => !item)) {
    failures.push(`${prefix}: task metrics should not be blank`);
  }
  if (data.overflowX) {
    failures.push(`${prefix}: horizontal page overflow detected`);
  }
  if (!view.mobile && data.stripTop !== null && data.stripTop > view.height * 0.55) {
    failures.push(`${prefix}: task path strip is too deep (${data.stripTop}/${view.height})`);
  }
  if (view.mobile && data.firstTaskWidth !== null && data.firstTaskWidth > view.width) {
    failures.push(`${prefix}: first mobile task card wider than viewport`);
  }
  if (view.mobile && data.firstTaskTop !== null && data.firstTaskTop > view.height) {
    failures.push(`${prefix}: first mobile task card is not visible before scrolling (${data.firstTaskTop}/${view.height})`);
  }
  return failures;
}

fs.mkdirSync(outputDir, { recursive: true });

const results = [];
for (const viewport of viewports) {
  results.push(await measure(viewport));
}

const failures = results.flatMap(validate);
fs.writeFileSync(path.join(outputDir, "role-task-path-metrics.json"), JSON.stringify(results, null, 2));
fs.writeFileSync(path.join(outputDir, "role-task-path-summary.json"), JSON.stringify({ failures, results }, null, 2));

if (failures.length > 0) {
  console.error(JSON.stringify({ status: "failed", failures }, null, 2));
  process.exit(1);
}

console.log(JSON.stringify({ status: "passed", outputDir, checked: viewports.map((item) => item.name) }, null, 2));
