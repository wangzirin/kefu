import fs from "node:fs";
import path from "node:path";

const chromeEndpoint = process.env.CHROME_DEBUGGING_URL ?? "http://127.0.0.1:9224";
const frontendUrl = process.env.FRONTEND_URL ?? "http://127.0.0.1:5178/#overview";
const outputDir = path.resolve(process.env.P3_06U_04_OUTPUT ?? "output/p3_06u_04_overview_action_paths");

const viewports = [
  { name: "desktop-1440", width: 1440, height: 900, mobile: false },
  { name: "mobile-390", width: 390, height: 844, mobile: true }
];

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

async function enterDemo(cdp) {
  await delay(500);
  await evalValue(cdp, `(() => {
    const button = Array.from(document.querySelectorAll('button')).find((item) =>
      item.textContent?.includes('开发演示进入')
    );
    if (button) button.click();
    location.hash = '#overview';
    return Boolean(button);
  })()`);
  const ready = await waitFor(cdp, `Boolean(document.querySelector('.ops-bi-action-row'))`);
  await delay(320);
  return ready;
}

async function clickAction(cdp, title) {
  const ok = await evalValue(cdp, `(() => {
    const link = Array.from(document.querySelectorAll('.ops-bi-action-row')).find((item) =>
      item.textContent?.includes(${JSON.stringify(title)})
    );
    if (!link) return false;
    link.click();
    return true;
  })()`);
  if (!ok) throw new Error(`Could not find action: ${title}`);
  await waitFor(cdp, `Boolean(document.querySelector('.task-context-banner'))`);
  await delay(300);
}

async function capture(cdp, name) {
  const screenshot = await cdp.send("Page.captureScreenshot", {
    format: "png",
    fromSurface: true,
    captureBeyondViewport: false
  });
  fs.writeFileSync(path.join(outputDir, `${name}.png`), Buffer.from(screenshot.data, "base64"));
}

async function inspectPage(cdp) {
  return evalValue(cdp, `(() => {
    const text = document.body.innerText;
    const activeQueue = document.querySelector('.service-queue-tabs .queue-tab.is-active')?.textContent?.trim() || '';
    const listToolbarStatus = Array.from(document.querySelectorAll('.list-toolbar select')).map((item) => item.value);
    const hrefs = Array.from(document.querySelectorAll('.ops-bi-action-row')).map((item) => item.getAttribute('href') || '');
    return {
      href: location.href,
      hash: location.hash,
      hasTaskBanner: Boolean(document.querySelector('.task-context-banner')),
      hasOverviewSource: text.includes('来自运营总览'),
      hasEmptyCopy: text.includes('本时间窗口暂无对应任务') || text.includes('本时间窗口暂无'),
      activeQueue,
      listToolbarStatus,
      actionHrefs: hrefs,
      overflowX: document.documentElement.scrollWidth > innerWidth || document.body.scrollWidth > innerWidth,
      innerWidth,
      bodyText: text.slice(0, 5000)
    };
  })()`);
}

async function runViewport(viewport) {
  const target = await createTarget("about:blank");
  const cdp = await createCdp(target.webSocketDebuggerUrl);
  const results = {};
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
    if (!demoReady) throw new Error(`${viewport.name}: demo overview did not load`);
    results.overview = await inspectPage(cdp);
    await capture(cdp, `${viewport.name}-overview`);

    await clickAction(cdp, "审核高风险会话");
    results.live = await inspectPage(cdp);
    await capture(cdp, `${viewport.name}-live-high-risk`);

    await cdp.send("Page.navigate", { url: frontendUrl });
    await cdp.waitFor("Page.loadEventFired", 12000).catch(() => undefined);
    await enterDemo(cdp);
    await clickAction(cdp, "确认待发送草稿");
    results.outbox = await inspectPage(cdp);
    await capture(cdp, `${viewport.name}-outbox-pending`);

    await cdp.send("Page.navigate", { url: frontendUrl });
    await cdp.waitFor("Page.loadEventFired", 12000).catch(() => undefined);
    await enterDemo(cdp);
    await clickAction(cdp, "修复知识缺口");
    results.gaps = await inspectPage(cdp);
    await capture(cdp, `${viewport.name}-gaps-open`);

    await cdp.send("Page.navigate", { url: frontendUrl });
    await cdp.waitFor("Page.loadEventFired", 12000).catch(() => undefined);
    await enterDemo(cdp);
    await clickAction(cdp, "复盘渠道异常");
    results.channels = await inspectPage(cdp);
    await capture(cdp, `${viewport.name}-channels-open`);

    return { viewport, results };
  } finally {
    cdp.close();
    await closeTarget(target.id);
  }
}

function validate(viewportResult) {
  const failures = [];
  const { viewport, results } = viewportResult;
  const prefix = viewport.name;
  const overviewHrefs = results.overview.actionHrefs.join("\\n");
  for (const token of ["from=overview", "high-risk-conversations", "pending-outbox", "knowledge-gaps", "channel-exceptions"]) {
    if (!overviewHrefs.includes(token)) failures.push(`${prefix}: overview action hrefs missing ${token}`);
  }
  const expectations = [
    ["live", "#live?", "高风险会话队列"],
    ["outbox", "#outbox?", "待确认发送草稿"],
    ["gaps", "#gaps?", "知识缺口修复"],
    ["channels", "#channels?", "渠道异常复盘"]
  ];
  for (const [key, hash, title] of expectations) {
    const data = results[key];
    if (!data.hash.includes(hash)) failures.push(`${prefix}: ${key} hash did not preserve query context`);
    if (!data.hasTaskBanner || !data.hasOverviewSource || !data.bodyText.includes(title)) {
      failures.push(`${prefix}: ${key} missing task context banner for ${title}`);
    }
    if (data.overflowX) failures.push(`${prefix}: ${key} has horizontal overflow`);
  }
  if (!results.live.activeQueue.includes("高风险")) {
    failures.push(`${prefix}: live desk did not activate high-risk queue`);
  }
  if (!results.outbox.listToolbarStatus.includes("pending_confirmation")) {
    failures.push(`${prefix}: outbox did not switch to pending confirmation status`);
  }
  if (!results.gaps.listToolbarStatus.includes("open")) {
    failures.push(`${prefix}: knowledge gaps did not switch to open status`);
  }
  if (!results.channels.listToolbarStatus.includes("open")) {
    failures.push(`${prefix}: channels failure review did not switch to open status`);
  }
  return failures;
}

fs.mkdirSync(outputDir, { recursive: true });

const viewportResults = [];
for (const viewport of viewports) {
  viewportResults.push(await runViewport(viewport));
}

const failures = viewportResults.flatMap(validate);
fs.writeFileSync(path.join(outputDir, "overview-action-paths-summary.json"), JSON.stringify(viewportResults, null, 2));

if (failures.length > 0) {
  console.error(JSON.stringify({ status: "failed", failures }, null, 2));
  process.exit(1);
}

console.log(JSON.stringify({ status: "passed", outputDir, checked: viewports.map((item) => item.name) }, null, 2));
