import fs from "node:fs";
import path from "node:path";

const chromeEndpoint = process.env.CHROME_DEBUGGING_URL ?? "http://127.0.0.1:9224";
const frontendUrl = process.env.FRONTEND_URL ?? "http://127.0.0.1:5182/?demo=1#overview";
const outputDir = path.resolve(process.env.P3_06T_03_BI_OUTPUT ?? "output/p3_06t_03_bi_overview");

const viewports = [
  { name: "desktop-1440", width: 1440, height: 900 },
  { name: "desktop-1280", width: 1280, height: 800 },
  { name: "desktop-1180", width: 1180, height: 768 }
];

const inspectExpression = `(() => {
  const root = document.documentElement;
  const workspace = document.querySelector('.workspace');
  const sidebar = document.querySelector('.sidebar');
  const commandCenter = document.querySelector('.ops-bi-command-center');
  const controlBar = document.querySelector('.ops-bi-control-bar');
  const healthPanel = document.querySelector('.ops-bi-health-panel');
  const trendPanel = document.querySelector('.ops-bi-trend-panel');
  const priorityPanel = document.querySelector('.ops-bi-priority-panel');
  const signalStrip = document.querySelector('.ops-bi-signal-strip');
  const commandRect = commandCenter?.getBoundingClientRect();
  const signalRect = signalStrip?.getBoundingClientRect();
  const healthScore = Number(document.querySelector('.ops-bi-score-ring strong')?.textContent ?? NaN);
  const signalCards = Array.from(document.querySelectorAll('.ops-bi-signal-card'));
  const charts = Array.from(document.querySelectorAll('.ops-chart'));
	  const actionRows = Array.from(document.querySelectorAll('.ops-bi-action-row'));
	  const contractPills = Array.from(document.querySelectorAll('.ops-bi-source-contract em'));
	  const text = document.body.innerText;
	  return {
    title: document.querySelector('.ops-bi-title strong')?.textContent ?? null,
    hasWorkspace: Boolean(workspace),
    hasSidebar: Boolean(sidebar),
    hasControlBar: Boolean(controlBar),
    hasCommandCenter: Boolean(commandCenter),
    hasHealthPanel: Boolean(healthPanel),
    hasTrendPanel: Boolean(trendPanel),
    hasPriorityPanel: Boolean(priorityPanel),
    signalCount: signalCards.length,
    chartCount: charts.length,
	    actionCount: actionRows.length,
	    contractPillCount: contractPills.length,
	    hasRemovedOverviewTail:
	      text.includes('人工池快照') ||
	      text.includes('待人工审核') ||
	      text.includes('待发送确认') ||
	      text.includes('工单超时') ||
	      text.includes('今日队列入口') ||
	      Boolean(document.querySelector('.queue-board')) ||
	      Boolean(document.querySelector('#workspace-overview-channel-health')),
	    healthScore,
    commandCenterTop: commandRect ? Math.round(commandRect.top) : null,
    commandCenterBottom: commandRect ? Math.round(commandRect.bottom) : null,
    signalStripTop: signalRect ? Math.round(signalRect.top) : null,
    signalStripBottom: signalRect ? Math.round(signalRect.bottom) : null,
    viewportHeight: innerHeight,
    overflowX: root.scrollWidth > innerWidth || document.body.scrollWidth > innerWidth,
    documentScrollWidth: root.scrollWidth,
    bodyScrollWidth: document.body.scrollWidth,
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
  await delay(700);
  await cdp.send("Runtime.evaluate", {
    awaitPromise: true,
    returnByValue: true,
    expression: `(() => {
	      const button = Array.from(document.querySelectorAll('button')).find((item) =>
	        item.textContent?.includes('测试账号进入') ||
	        item.textContent?.includes('预览工作台') ||
	        item.textContent?.includes('开发演示进入')
	      );
      if (button) {
        button.click();
      }
      return Boolean(button);
    })()`
  });
  return waitForSelector(cdp, ".ops-bi-command-center");
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
      mobile: false
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

  if (!result.demoReady || !data.hasWorkspace) {
    failures.push(`${prefix}: demo workspace did not render`);
  }
  if (!data.hasControlBar || !data.hasCommandCenter || !data.hasHealthPanel || !data.hasTrendPanel || !data.hasPriorityPanel) {
    failures.push(`${prefix}: BI command shell incomplete`);
  }
  if (data.signalCount < 4) {
    failures.push(`${prefix}: expected 4 signal cards, got ${data.signalCount}`);
  }
  if (data.chartCount < 4) {
    failures.push(`${prefix}: expected at least 4 chart containers, got ${data.chartCount}`);
  }
  if (data.actionCount < 3) {
    failures.push(`${prefix}: expected 3 priority actions, got ${data.actionCount}`);
  }
  if (data.hasRemovedOverviewTail) {
    failures.push(`${prefix}: removed manual-pool/work-queue overview tail is still visible`);
  }
  if (!Number.isFinite(data.healthScore) || data.healthScore < 0 || data.healthScore > 100) {
    failures.push(`${prefix}: health score invalid (${data.healthScore})`);
  }
  if (data.contractPillCount < 3) {
    failures.push(`${prefix}: data contract pills missing`);
  }
  if (data.overflowX) {
    failures.push(`${prefix}: horizontal overflow detected`);
  }
  if (!view.mobile && view.width >= 1200 && data.commandCenterBottom !== null && data.commandCenterBottom > view.height + 280) {
    failures.push(`${prefix}: command center too deep for wide first screen (${data.commandCenterBottom}/${view.height})`);
  }
  if (!view.mobile && view.width < 1200 && data.signalStripBottom !== null && data.signalStripBottom > view.height + 120) {
    failures.push(`${prefix}: signal strip too deep for narrow desktop (${data.signalStripBottom}/${view.height})`);
  }
  if (!view.mobile && view.width < 1200 && data.commandCenterTop !== null && data.commandCenterTop > view.height + 320) {
    failures.push(`${prefix}: command center entry too deep for narrow desktop (${data.commandCenterTop}/${view.height})`);
  }
  return failures;
}

fs.mkdirSync(outputDir, { recursive: true });

const results = [];
for (const viewport of viewports) {
  results.push(await measure(viewport));
}

const failures = results.flatMap(validate);
fs.writeFileSync(path.join(outputDir, "bi-overview-metrics.json"), JSON.stringify(results, null, 2));
fs.writeFileSync(path.join(outputDir, "bi-overview-summary.json"), JSON.stringify({ failures, results }, null, 2));

if (failures.length > 0) {
  console.error(JSON.stringify({ status: "failed", failures }, null, 2));
  process.exit(1);
}

console.log(JSON.stringify({ status: "passed", outputDir, checked: viewports.map((item) => item.name) }, null, 2));
