import fs from "node:fs";
import path from "node:path";

const chromeEndpoint = process.env.CHROME_DEBUGGING_URL ?? "http://127.0.0.1:9227";
const frontendUrl = process.env.FRONTEND_URL ?? "http://127.0.0.1:5182/?demo=1#live";
const outputDir = path.resolve(process.env.P3_06U_26H2W_OUTPUT ?? "output/p3_06u_26h2w_chat_ui");

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

  ws.addEventListener("message", (event) => {
    const msg = JSON.parse(event.data);
    if (!msg.id || !pending.has(msg.id)) return;
    const { resolve, reject } = pending.get(msg.id);
    pending.delete(msg.id);
    if (msg.error) reject(new Error(JSON.stringify(msg.error)));
    else resolve(msg.result || {});
  });

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

fs.mkdirSync(outputDir, { recursive: true });

const target = await createTarget("about:blank");
const cdp = await createCdp(target.webSocketDebuggerUrl);

try {
  await cdp.send("Page.enable");
  await cdp.send("Runtime.enable");
  await cdp.send("Emulation.setDeviceMetricsOverride", {
    width: 1440,
    height: 900,
    deviceScaleFactor: 1,
    mobile: false
  });
  await cdp.send("Page.navigate", { url: frontendUrl });
  const ready = await waitFor(cdp, `Boolean(document.querySelector('[data-chat-ui-slimmed="p3-06u-26h2w"]'))`);
  if (!ready) throw new Error("Chat UI did not reach H2W slimmed state");
  await delay(900);

  const checks = await evalValue(cdp, `(() => {
    const text = document.body.innerText;
    const banned = ['AI 回复建议', '转人工提醒', 'AI 自动回复判断', '转人工判断', '系统门禁', 'AI 建议', 'AI 无法', '预备'];
    const list = document.querySelector('.wechat-session-list');
    const chat = document.querySelector('.wechat-chat-pane');
    const composer = document.querySelector('[data-chat-ui-slimmed="p3-06u-26h2w"]');
    const sendButton = document.querySelector('.composer-send-button');
    const sendRect = sendButton?.getBoundingClientRect();
    return {
      hasSearch: Boolean(document.querySelector('.service-list-search input')),
      hasNoFakeHeaderActions: document.querySelectorAll('.chat-head-action').length === 0,
      hasNoFakeComposerTools: document.querySelectorAll('.composer-tool-button').length === 0,
      hasReadonlyStatus: Boolean(document.querySelector('[data-function-reality="no-fake-chat-actions"]')),
      hasComposer: Boolean(composer),
      hasSendButton: Boolean(sendButton),
      sendButtonLabel: sendButton?.textContent?.trim() ?? '',
      sendButtonFullyVisible: Boolean(sendRect && sendRect.bottom <= innerHeight - 8 && sendRect.right <= innerWidth - 8),
      hasOldCopy: banned.some((item) => text.includes(item)),
      leftWidth: Math.round(list?.getBoundingClientRect().width ?? 0),
      chatWidth: Math.round(chat?.getBoundingClientRect().width ?? 0),
      overflowX: document.documentElement.scrollWidth > innerWidth || document.body.scrollWidth > innerWidth
    };
  })()`);

  if (!checks.hasSearch || !checks.hasNoFakeHeaderActions || !checks.hasNoFakeComposerTools || !checks.hasReadonlyStatus || !checks.hasComposer || !checks.hasSendButton || !checks.sendButtonFullyVisible) {
    throw new Error(`Missing required chat UI parts: ${JSON.stringify(checks)}`);
  }
  if (!checks.sendButtonLabel.includes("保存接管回复")) {
    throw new Error(`Composer button must not imply external send: ${JSON.stringify(checks)}`);
  }
  if (checks.hasOldCopy) {
    throw new Error(`Old AI/review copy still visible: ${JSON.stringify(checks)}`);
  }
  if (checks.leftWidth > 245 || checks.leftWidth < 170) {
    throw new Error(`Conversation list width is out of expected slim range: ${JSON.stringify(checks)}`);
  }
  if (checks.chatWidth < 780 || checks.overflowX) {
    throw new Error(`Chat pane layout is not healthy: ${JSON.stringify(checks)}`);
  }

  const screenshot = await cdp.send("Page.captureScreenshot", {
    format: "png",
    fromSurface: true,
    captureBeyondViewport: false
  });
  const screenshotPath = path.join(outputDir, "desktop-1440-live-chat.png");
  fs.writeFileSync(screenshotPath, Buffer.from(screenshot.data, "base64"));
  fs.writeFileSync(path.join(outputDir, "checks.json"), JSON.stringify(checks, null, 2));
  console.log(`[PASS] P3-06U-26H2W chat visual check passed: ${screenshotPath}`);
} finally {
  cdp.close();
  await closeTarget(target.id);
}
