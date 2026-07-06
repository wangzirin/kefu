import fs from "node:fs";
import path from "node:path";

const chromeEndpoint = process.env.CHROME_DEBUGGING_URL ?? "http://127.0.0.1:9227";
const frontendUrl = process.env.FRONTEND_URL ?? "http://127.0.0.1:5182/?demo=1#live";
const outputDir = path.resolve(process.env.P3_06U_10B_OUTPUT ?? "output/p3_06u_10b_conversation_workbench_simplification");

const viewports = [
  { name: "desktop-1440", width: 1440, height: 900 },
  { name: "desktop-1280", width: 1280, height: 800 }
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
  await cdp.send("Page.navigate", { url: frontendUrl });
  await cdp.waitFor("Page.loadEventFired", 12000).catch(() => undefined);
  await evalValue(cdp, `localStorage.removeItem('wanfa_standard_ops_access_token'); true`);
  await cdp.send("Page.navigate", { url: frontendUrl });
  await cdp.waitFor("Page.loadEventFired", 12000).catch(() => undefined);
  await delay(450);
  await evalValue(cdp, `(() => {
    const button = Array.from(document.querySelectorAll('button')).find((item) =>
      item.textContent?.includes('开发演示进入')
    );
    if (button) button.click();
    setTimeout(() => { location.hash = '#live'; }, 80);
    return Boolean(button);
  })()`);
  return waitFor(cdp, `Boolean(document.querySelector('.wechat-service-desk'))`);
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
    const stream = document.querySelector('.service-message-stream');
    const autoReplyRecord = document.querySelector('.auto-reply-record, .auto-reply-status-strip');
    const replyDock = document.querySelector('.service-reply-dock');
    const firstThread = document.querySelector('.wechat-session-list .service-thread-item');
    const directInspector = document.querySelector('.service-desk-layout > .service-inspector');
    const topQueue = document.querySelector('.service-desk-shell > .service-queue-tabs');
    const signalStrip = document.querySelector('.service-desk-signal-strip');
    const primaryQueues = document.querySelectorAll('.service-primary-queues .queue-tab');
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
      hasAutoReplyRecord: Boolean(autoReplyRecord),
      hasReplyDock: Boolean(replyDock),
      hasDirectInspector: Boolean(directInspector),
      hasTopQueue: Boolean(topQueue),
      hasSignalStrip: Boolean(signalStrip),
      primaryQueueCount: primaryQueues.length,
      gridTemplateColumns: layout ? getComputedStyle(layout).gridTemplateColumns : '',
      listRect: rect(list),
      chatRect: rect(chat),
      streamRect: rect(stream),
      autoReplyRect: rect(autoReplyRecord),
      replyDockRect: rect(replyDock),
      firstThreadRect: rect(firstThread),
      hasExternalSendOffCopy: text.includes('真实外发关闭'),
      hasQueueCopy: text.includes('全部') && text.includes('我的') && text.includes('转人工'),
      hasAutoReplyCopy: text.includes('AI 自动回复') || text.includes('AI 正在自动接待'),
      hasForbiddenOldCopy:
        text.includes('待审') ||
        text.includes('待发') ||
        text.includes('AI 建议') ||
        text.includes('客户可见回复预案') ||
        text.includes('人工接管 / 异常备注') ||
        text.includes('内部备注') ||
        text.includes('确认发送队列'),
      overflowX: root.scrollWidth > innerWidth || body.scrollWidth > innerWidth,
      documentScrollWidth: root.scrollWidth,
      bodyScrollWidth: body.scrollWidth,
      innerWidth,
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
      mobile: false
    });
    const ready = await enterLive(cdp);
    if (!ready) throw new Error(`${viewport.name}: live desk did not appear`);
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
    ["hasReplyDock", "reply dock"],
    ["hasExternalSendOffCopy", "真实外发关闭"],
    ["hasQueueCopy", "全部 / 我的 / 转人工"],
  ]) {
    if (!inspected[key]) failures.push(`${prefix}: missing ${label}`);
  }
  if (inspected.hasAutoReplyCopy) failures.push(`${prefix}: auto-reply overclaiming copy is visible`);
  if (inspected.hasAutoReplyRecord) failures.push(`${prefix}: old auto-reply status card should not be visible in simplified IM desk`);
  if (inspected.hasForbiddenOldCopy) failures.push(`${prefix}: old review/send copy is visible`);
  if (inspected.hasDirectInspector) failures.push(`${prefix}: old direct third-column inspector still exists`);
  if (inspected.hasTopQueue) failures.push(`${prefix}: queue tabs still live in top shell`);
  if (inspected.hasSignalStrip) failures.push(`${prefix}: old signal strip still exists`);
  if (inspected.primaryQueueCount !== 3) failures.push(`${prefix}: expected 3 primary queue filters`);
  if (inspected.overflowX) failures.push(`${prefix}: horizontal overflow`);
  if (inspected.listRect && inspected.chatRect) {
    if (inspected.chatRect.width <= inspected.listRect.width * 1.35) {
      failures.push(`${prefix}: chat pane should clearly dominate the session list`);
    }
    if (!inspected.gridTemplateColumns.includes(" ")) {
      failures.push(`${prefix}: layout is not a two-column grid`);
    }
    if (!inspected.streamRect || inspected.streamRect.height < 260) {
      failures.push(`${prefix}: message stream is too short for a usable chat pane`);
    }
    if (!inspected.firstThreadRect || inspected.firstThreadRect.height < 70) {
      failures.push(`${prefix}: session list item is compressed and unreadable`);
    }
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
  throw new Error(`P3-06U-10B conversation workbench simplification smoke failed:\\n${failures.join("\\n")}`);
}
console.log(`P3-06U-10B conversation workbench simplification smoke passed. Evidence: ${outputDir}`);
