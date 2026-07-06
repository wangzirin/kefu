import fs from "node:fs";
import path from "node:path";

const chromeEndpoint = process.env.CHROME_DEBUGGING_URL ?? "http://127.0.0.1:9227";
const frontendUrl = process.env.FRONTEND_URL ?? "http://127.0.0.1:5182/";
const outputDir = path.resolve(process.env.P3_06U_22_OUTPUT ?? "output/p3_06u_22_workbench_reply_decision_visualization");

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
        send(method, params = {}) {
          const callId = ++id;
          ws.send(JSON.stringify({ id: callId, method, params }));
          return new Promise((resolve, reject) => pending.set(callId, { resolve, reject }));
        },
        waitFor(method, timeout = 10000) {
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

async function enterLive(cdp) {
  const url = new URL(frontendUrl);
  const liveUrl = frontendUrl.includes("?demo=1") ? frontendUrl : `${url.origin}/?demo=1#live`;
  await cdp.send("Page.navigate", { url: liveUrl });
  await cdp.waitFor("Page.loadEventFired", 12000).catch(() => undefined);
  await evalValue(cdp, `localStorage.removeItem('wanfa_standard_ops_access_token'); true`);
  await cdp.send("Page.navigate", { url: liveUrl });
  await cdp.waitFor("Page.loadEventFired", 12000).catch(() => undefined);
  await delay(450);
  return waitFor(cdp, `Boolean(document.querySelector('[data-reply-decision-strip="p3-06u-22"]'))`);
}

async function inspect(cdp, viewport) {
  await delay(550);
  await evalValue(cdp, `document.querySelector('#workspace-live')?.scrollIntoView({ block: 'start' })`);
  await delay(180);
  const inspected = await evalValue(cdp, `(() => {
    const root = document.documentElement;
    const body = document.body;
    const layout = document.querySelector('.service-desk-layout');
    const list = document.querySelector('.wechat-session-list');
    const chat = document.querySelector('.wechat-chat-pane');
    const strip = document.querySelector('[data-reply-decision-strip="p3-06u-22"]');
    const stripGrid = document.querySelector('.reply-decision-strip-grid');
    const stream = document.querySelector('.service-message-stream');
    const text = body.innerText;
    const rect = (node) => {
      const item = node?.getBoundingClientRect();
      return item ? { top: Math.round(item.top), left: Math.round(item.left), width: Math.round(item.width), height: Math.round(item.height) } : null;
    };
    return {
      hash: location.hash,
      hasDesk: Boolean(document.querySelector('.wechat-service-desk')),
      hasLayout: Boolean(layout),
      hasList: Boolean(list),
      hasChat: Boolean(chat),
      hasStrip: Boolean(strip),
      hasStripGrid: Boolean(stripGrid),
      listRect: rect(list),
      chatRect: rect(chat),
      stripRect: rect(strip),
      streamRect: rect(stream),
      stripText: strip?.textContent || '',
      gridColumns: layout ? getComputedStyle(layout).gridTemplateColumns : '',
      hasReplyDecisionCopy: text.includes('回复决策'),
      hasBusinessObjectCopy: text.includes('业务对象'),
      hasKnowledgeCopy: text.includes('知识依据'),
      hasNextActionCopy: text.includes('下一步'),
      hasExternalWriteCopy: text.includes('真实外发关闭') || text.includes('外发'),
      hasAutoReadyCopy: text.includes('自动回复预备') || text.includes('AI 自主回复预备'),
      hasTimelineDecision: Array.from(document.querySelectorAll('.service-message')).some((item) => item.textContent?.includes('回复决策')),
      overflowX: root.scrollWidth > innerWidth || body.scrollWidth > innerWidth,
      innerWidth,
      documentScrollWidth: root.scrollWidth,
      bodyScrollWidth: body.scrollWidth,
      viewportName: ${JSON.stringify(viewport.name)}
    };
  })()`);
  const screenshot = await cdp.send("Page.captureScreenshot", {
    format: "png",
    fromSurface: true,
    captureBeyondViewport: false
  });
  fs.writeFileSync(path.join(outputDir, `${viewport.name}.png`), Buffer.from(screenshot.data, "base64"));
  return inspected;
}

async function runViewport(viewport) {
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
    const ready = await enterLive(cdp);
    if (!ready) throw new Error(`${viewport.name}: reply decision strip did not appear`);
    return { viewport, inspected: await inspect(cdp, viewport) };
  } finally {
    cdp.close();
    await closeTarget(target.id);
  }
}

function validate(result) {
  const { viewport, inspected } = result;
  const failures = [];
  const prefix = viewport.name;
  for (const [key, label] of [
    ["hasDesk", "wechat desk"],
    ["hasLayout", "layout"],
    ["hasList", "session list"],
    ["hasChat", "chat pane"],
    ["hasStrip", "reply decision strip"],
    ["hasStripGrid", "reply decision grid"],
    ["hasReplyDecisionCopy", "回复决策 copy"],
    ["hasBusinessObjectCopy", "业务对象 copy"],
    ["hasKnowledgeCopy", "知识依据 copy"],
    ["hasNextActionCopy", "下一步 copy"],
    ["hasExternalWriteCopy", "外发 copy"],
    ["hasTimelineDecision", "timeline reply decision event"]
  ]) {
    if (!inspected[key]) failures.push(`${prefix}: missing ${label}`);
  }
  if (inspected.overflowX) failures.push(`${prefix}: horizontal overflow`);
  if (!viewport.mobile && inspected.listRect && inspected.chatRect) {
    if (inspected.listRect.width > 250) failures.push(`${prefix}: session list is too wide`);
    if (inspected.chatRect.width <= inspected.listRect.width * 1.8) {
      failures.push(`${prefix}: chat pane should dominate the session list`);
    }
    if (!inspected.stripRect || inspected.stripRect.height > 130) {
      failures.push(`${prefix}: reply decision strip is too tall`);
    }
    if (!inspected.streamRect || inspected.streamRect.height < 240) {
      failures.push(`${prefix}: message stream is too short`);
    }
  }
  if (viewport.mobile && inspected.chatRect) {
    if (inspected.chatRect.width > viewport.width) failures.push(`${prefix}: chat pane wider than mobile viewport`);
    if (!inspected.stripRect || inspected.stripRect.width > viewport.width) failures.push(`${prefix}: strip wider than mobile viewport`);
  }
  return failures;
}

fs.mkdirSync(outputDir, { recursive: true });
const results = [];
for (const viewport of viewports) {
  results.push(await runViewport(viewport));
}
const failures = results.flatMap(validate);
fs.writeFileSync(path.join(outputDir, "summary.json"), JSON.stringify({ ok: failures.length === 0, failures, results }, null, 2));
if (failures.length > 0) {
  throw new Error(`P3-06U-22 workbench reply decision visualization smoke failed:\\n${failures.join("\\n")}`);
}
console.log(`P3-06U-22 workbench reply decision visualization smoke passed. Evidence: ${outputDir}`);
