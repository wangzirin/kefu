import fs from "node:fs";
import path from "node:path";

const chromeEndpoint = process.env.CHROME_DEBUGGING_URL ?? "http://127.0.0.1:9224";
const frontendUrl = process.env.FRONTEND_URL ?? "http://127.0.0.1:5176/#overview";
const outputDir = path.resolve(process.env.P3_06T_SCROLL_OUTPUT ?? "output/p3_06t_layout_after");

const viewports = [
  { name: "desktop-1440", width: 1440, height: 900, shell: "workspace" },
  { name: "desktop-1280", width: 1280, height: 800, shell: "workspace" },
  { name: "desktop-1024", width: 1024, height: 768, shell: "workspace" },
  { name: "narrow-900", width: 900, height: 768, shell: "workspace" },
  { name: "narrow-760", width: 760, height: 768, shell: "workspace" },
  { name: "boundary-721", width: 721, height: 768, shell: "workspace" },
  { name: "boundary-720", width: 720, height: 768, shell: "page" },
  { name: "mobile-390", width: 390, height: 844, shell: "page" }
];

const inspectExpression = `(() => {
  const w = document.querySelector('.workspace');
  const s = document.querySelector('.sidebar');
  const shell = document.querySelector('.app-shell');
  const root = document.documentElement;
  return {
    hasWorkspace: Boolean(w),
    hasSidebar: Boolean(s),
    visibleHeading: document.querySelector('h1,h2')?.textContent ?? null,
    width: innerWidth,
    height: innerHeight,
    bodyScrollY: window.scrollY,
    bodyScrollHeight: document.scrollingElement?.scrollHeight ?? root.scrollHeight,
    bodyClientHeight: document.scrollingElement?.clientHeight ?? root.clientHeight,
    workspaceScrollTop: w?.scrollTop ?? null,
    workspaceScrollHeight: w?.scrollHeight ?? null,
    workspaceClientHeight: w?.clientHeight ?? null,
    sidebarTop: s?.getBoundingClientRect().top ?? null,
    sidebarBottom: s?.getBoundingClientRect().bottom ?? null,
    shellHeight: shell?.getBoundingClientRect().height ?? null,
    overflowX: root.scrollWidth > innerWidth || document.body.scrollWidth > innerWidth,
    documentScrollWidth: root.scrollWidth,
    bodyScrollWidth: document.body.scrollWidth,
    bodyOverflowY: getComputedStyle(document.body).overflowY,
    workspaceOverflowY: w ? getComputedStyle(w).overflowY : null,
    sidebarOverflowY: s ? getComputedStyle(s).overflowY : null,
    mediaNarrowDesktop: matchMedia('(min-width: 721px) and (max-width: 960px)').matches
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

async function waitForWorkspace(cdp) {
  for (let i = 0; i < 60; i += 1) {
    const result = await cdp.send("Runtime.evaluate", {
      awaitPromise: true,
      returnByValue: true,
      expression: "Boolean(document.querySelector('.workspace'))"
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
        item.textContent?.includes('开发演示进入')
      );
      if (button) {
        button.click();
      }
      return Boolean(button);
    })()`
  });
  return waitForWorkspace(cdp);
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
      mobile: viewport.width <= 560
    });
    await cdp.send("Page.navigate", { url: frontendUrl });
    await cdp.waitFor("Page.loadEventFired", 12000).catch(() => undefined);
    const demoReady = await enterDemo(cdp);
    await delay(700);

    const before = await cdp.send("Runtime.evaluate", {
      awaitPromise: true,
      returnByValue: true,
      expression: inspectExpression
    });
    const after = await cdp.send("Runtime.evaluate", {
      awaitPromise: true,
      returnByValue: true,
      expression: `(async () => {
        const w = document.querySelector('.workspace');
        window.scrollTo(0, 900);
        if (w) {
          w.scrollTo(0, 900);
        }
        await new Promise((resolve) => requestAnimationFrame(() => setTimeout(resolve, 120)));
        return ${inspectExpression};
      })()`
    });
    const screenshot = await cdp.send("Page.captureScreenshot", {
      format: "png",
      fromSurface: true,
      captureBeyondViewport: false
    });
    fs.writeFileSync(path.join(outputDir, `${viewport.name}-after.png`), Buffer.from(screenshot.data, "base64"));
    return {
      viewport,
      demoReady,
      before: before.result.value,
      after: after.result.value
    };
  } finally {
    cdp.close();
    await closeTarget(target.id);
  }
}

function validate(result) {
  const after = result.after;
  const prefix = result.viewport.name;
  const failures = [];

  if (!result.demoReady || !after.hasWorkspace || !after.hasSidebar) {
    failures.push(`${prefix}: workspace/sidebar not ready`);
  }
  if (after.overflowX) {
    failures.push(`${prefix}: horizontal overflow detected`);
  }
  if (result.viewport.shell === "workspace") {
    if (after.bodyScrollY !== 0) {
      failures.push(`${prefix}: bodyScrollY expected 0, got ${after.bodyScrollY}`);
    }
    if ((after.workspaceScrollTop ?? 0) < 800) {
      failures.push(`${prefix}: workspaceScrollTop expected >=800, got ${after.workspaceScrollTop}`);
    }
    if (Math.abs((after.sidebarTop ?? 999) - 0) > 1) {
      failures.push(`${prefix}: sidebarTop expected 0, got ${after.sidebarTop}`);
    }
    if (after.workspaceOverflowY !== "auto") {
      failures.push(`${prefix}: workspaceOverflowY expected auto, got ${after.workspaceOverflowY}`);
    }
  } else {
    if (after.bodyScrollY < 800) {
      failures.push(`${prefix}: mobile/page bodyScrollY expected >=800, got ${after.bodyScrollY}`);
    }
    if (after.workspaceOverflowY !== "visible") {
      failures.push(`${prefix}: mobile/page workspaceOverflowY expected visible, got ${after.workspaceOverflowY}`);
    }
  }
  return failures;
}

fs.mkdirSync(outputDir, { recursive: true });

const results = [];
for (const viewport of viewports) {
  results.push(await measure(viewport));
}

const failures = results.flatMap(validate);
fs.writeFileSync(path.join(outputDir, "scroll-metrics.json"), JSON.stringify(results, null, 2));
fs.writeFileSync(path.join(outputDir, "scroll-summary.json"), JSON.stringify({ failures, results }, null, 2));

if (failures.length > 0) {
  console.error(JSON.stringify({ status: "failed", failures }, null, 2));
  process.exit(1);
}

console.log(JSON.stringify({ status: "passed", outputDir, checked: viewports.map((item) => item.name) }, null, 2));
