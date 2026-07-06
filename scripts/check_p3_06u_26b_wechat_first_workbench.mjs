import fs from "node:fs";
import path from "node:path";

const chromeEndpoint = process.env.CHROME_DEBUGGING_URL ?? "http://127.0.0.1:9227";
const frontendUrl = process.env.FRONTEND_URL ?? "http://127.0.0.1:5182/?demo=1#live";
const outputDir = path.resolve(process.env.P3_06U_26B_OUTPUT ?? "output/p3_06u_26b_wechat_first_workbench");

const viewports = [
  { name: "desktop-1440", width: 1440, height: 900 },
  { name: "desktop-1280", width: 1280, height: 800 },
  { name: "desktop-1180", width: 1180, height: 768 }
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
    await cdp.send("Page.navigate", { url: frontendUrl });
    await cdp.waitFor("Page.loadEventFired", 12000).catch(() => undefined);
    const ready = await waitFor(cdp, `Boolean(document.querySelector('[data-wechat-first-workbench="p3-06u-26b"]'))`);
    if (!ready) throw new Error(`${viewport.name}: P3-06U-26B workbench did not become ready`);
    await evalValue(cdp, `document.querySelector('#workspace-live')?.scrollIntoView({ block: 'start' })`);
    await delay(450);
    const inspected = await evalValue(cdp, `(() => {
      const rect = (selector) => {
        const node = document.querySelector(selector);
        const item = node?.getBoundingClientRect();
        return item ? { top: Math.round(item.top), left: Math.round(item.left), width: Math.round(item.width), height: Math.round(item.height), bottom: Math.round(item.bottom) } : null;
      };
      const text = document.body.innerText;
      const root = document.documentElement;
      const body = document.body;
      return {
        href: location.href,
        text,
        hasDesk: Boolean(document.querySelector('.wechat-service-desk')),
        hasList: Boolean(document.querySelector('.wechat-session-list')),
        hasChat: Boolean(document.querySelector('.wechat-chat-pane')),
        hasAutonomousMarker: Boolean(document.querySelector('[data-autonomous-reply-workbench="p3-06u-26g2"]')),
        hasAutoReplyRecord: Boolean(document.querySelector('.auto-reply-record, .auto-reply-status-strip')),
        hasMessageStream: Boolean(document.querySelector('.service-message-stream')),
        hasReplyDock: Boolean(document.querySelector('.service-reply-dock')),
        listRect: rect('.wechat-session-list'),
        chatRect: rect('.wechat-chat-pane'),
        streamRect: rect('.service-message-stream'),
        autoReplyRect: rect('.auto-reply-record, .auto-reply-status-strip'),
        replyDockRect: rect('.service-reply-dock'),
        hasQueueCopy: text.includes('全部') && text.includes('我的') && text.includes('转人工'),
        hasAutoReplyCopy: text.includes('AI 自动回复') || text.includes('AI 正在自动接待'),
        hasHandoffCopy: text.includes('转人工'),
        hasExternalWriteOff: text.includes('真实外发关闭'),
        hasForbiddenOldCopy:
          text.includes('演示模式') ||
          text.includes('演示样本') ||
          text.includes('开发演示身份') ||
          text.includes('待审') ||
          text.includes('待发') ||
          text.includes('AI 建议') ||
          text.includes('客户可见回复预案') ||
          text.includes('人工接管 / 异常备注') ||
          text.includes('内部备注') ||
          text.includes('确认发送队列'),
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
    fs.writeFileSync(path.join(outputDir, `${viewport.name}.png`), Buffer.from(screenshot.data, "base64"));
    const runtimeErrors = cdp.events
      .filter((event) => event.method === "Runtime.exceptionThrown")
      .map((event) => event.params?.exceptionDetails?.exception?.description || event.params?.exceptionDetails?.text || "runtime error");
    return { viewport, inspected, runtimeErrors };
  } finally {
    cdp.close();
    await closeTarget(target.id);
  }
}

function validate({ viewport, inspected, runtimeErrors }) {
  const failures = [];
  const prefix = viewport.name;
  for (const [key, label] of [
    ["hasDesk", "desk"],
    ["hasList", "session list"],
    ["hasChat", "chat pane"],
    ["hasAutonomousMarker", "autonomous workbench marker"],
    ["hasAutoReplyRecord", "auto reply record"],
    ["hasMessageStream", "message stream"],
    ["hasReplyDock", "reply dock"],
    ["hasQueueCopy", "queue copy"],
    ["hasAutoReplyCopy", "auto reply copy"],
    ["hasHandoffCopy", "handoff copy"],
    ["hasExternalWriteOff", "external write boundary"],
  ]) {
    if (!inspected[key]) failures.push(`${prefix}: missing ${label}`);
  }
  if (inspected.hasForbiddenOldCopy) failures.push(`${prefix}: old internal demo copy is visible`);
  if (inspected.overflowX) failures.push(`${prefix}: horizontal overflow (${inspected.scrollWidth} > ${inspected.innerWidth})`);
  for (const error of runtimeErrors) failures.push(`${prefix}: runtime error: ${error}`);
  if (inspected.listRect?.width > 218) failures.push(`${prefix}: session list is too wide (${inspected.listRect.width}px)`);
  if (inspected.listRect && inspected.chatRect && inspected.chatRect.width <= inspected.listRect.width * 2) {
    failures.push(`${prefix}: chat pane should dominate session list`);
  }
  if (!inspected.streamRect || inspected.streamRect.height < 300) {
    failures.push(`${prefix}: message stream is too short`);
  }
  if (inspected.streamRect && inspected.streamRect.top > viewport.height * 0.42) {
    failures.push(`${prefix}: message stream starts too low in first viewport`);
  }
  if (inspected.streamRect && inspected.autoReplyRect && inspected.autoReplyRect.top <= inspected.streamRect.top) {
    failures.push(`${prefix}: auto reply status should sit after message stream`);
  }
  if (inspected.autoReplyRect && inspected.replyDockRect && (inspected.autoReplyRect.top < inspected.replyDockRect.top || inspected.autoReplyRect.bottom > inspected.replyDockRect.bottom)) {
    failures.push(`${prefix}: auto reply status is not inside reply dock`);
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
if (failures.length) {
  console.error(failures.join("\n"));
  process.exit(1);
}
console.log(`PASS p3_06u_26b_wechat_first_workbench ${outputDir}`);
