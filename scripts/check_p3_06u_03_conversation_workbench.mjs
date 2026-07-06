import fs from "node:fs";
import path from "node:path";

const chromeEndpoint = process.env.CHROME_DEBUGGING_URL ?? "http://127.0.0.1:9224";
const frontendUrl = process.env.FRONTEND_URL ?? "http://127.0.0.1:5178/#live";
const outputDir = path.resolve(process.env.P3_06U_03_OUTPUT ?? "output/p3_06u_03_conversation_workbench");

const viewports = [
  { name: "desktop-1440", width: 1440, height: 900, mobile: false },
  { name: "narrow-900", width: 900, height: 768, mobile: false },
  { name: "mobile-390", width: 390, height: 844, mobile: true }
];

const inspectExpression = `(() => {
  const root = document.documentElement;
  const body = document.body;
  const desk = document.querySelector('.service-desk');
  const layout = document.querySelector('.service-desk-layout');
  const list = document.querySelector('.service-conversation-list');
  const chat = document.querySelector('.service-chat-pane');
  const dock = document.querySelector('.service-reply-dock');
  const inspector = document.querySelector('.service-inspector');
  const isWechatSimplified = Boolean(document.querySelector('.wechat-service-desk'));
  const directInspector = document.querySelector('.service-desk-layout > .service-inspector');
  const tabs = Array.from(document.querySelectorAll('.service-queue-tabs .queue-tab'));
  const text = body.innerText;
  const rect = (node) => {
    const item = node?.getBoundingClientRect();
    return item ? { top: Math.round(item.top), left: Math.round(item.left), width: Math.round(item.width), height: Math.round(item.height) } : null;
  };
  return {
    hasDesk: Boolean(desk),
    hasLayout: Boolean(layout),
    hasList: Boolean(list),
    hasChat: Boolean(chat),
    hasDock: Boolean(dock),
    hasInspector: Boolean(inspector),
    isWechatSimplified,
    hasDirectInspector: Boolean(directInspector),
    queueTabCount: tabs.length,
    hasExternalSendOffCopy: text.includes('真实外发关闭'),
    hasApproveCopy: text.includes('人工确认放行'),
    hasConfirmCopy: text.includes('确认发送队列'),
    hasGuardrailCopy: text.includes('高置信会话按策略自动回复'),
    listRect: rect(list),
    chatRect: rect(chat),
    inspectorRect: rect(inspector),
    dockRect: rect(dock),
    overflowX: root.scrollWidth > innerWidth || body.scrollWidth > innerWidth,
    documentScrollWidth: root.scrollWidth,
    bodyScrollWidth: body.scrollWidth,
    innerWidth,
    href: location.href
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
  for (let i = 0; i < 80; i += 1) {
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

async function enterLiveDesk(cdp) {
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
      setTimeout(() => { location.hash = '#live'; }, 120);
      return Boolean(button);
    })()`
  });
  return waitForSelector(cdp, ".service-desk");
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
    const demoReady = await enterLiveDesk(cdp);
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

  const requiredBlocks = [
    ["hasDesk", "desk"],
    ["hasLayout", "layout"],
    ["hasList", "conversation list"],
    ["hasChat", "chat pane"],
    ["hasDock", "reply dock"],
  ];
  if (!data.isWechatSimplified) {
    requiredBlocks.push(["hasInspector", "inspector"]);
  }
  for (const [key, label] of requiredBlocks) {
    if (!result.demoReady || !data[key]) {
      failures.push(`${prefix}: missing ${label}`);
    }
  }
  if (data.queueTabCount < 6) {
    failures.push(`${prefix}: expected queue tabs, got ${data.queueTabCount}`);
  }
  for (const [key, label] of [
    ["hasExternalSendOffCopy", "真实外发关闭"],
    ["hasApproveCopy", "人工确认放行"],
    ["hasConfirmCopy", "确认发送队列"],
    ["hasGuardrailCopy", "高置信会话按策略自动回复"],
  ]) {
    if (!data[key]) {
      failures.push(`${prefix}: missing copy ${label}`);
    }
  }
  if (data.overflowX) {
    failures.push(`${prefix}: horizontal page overflow detected`);
  }
  if (!view.mobile) {
    for (const [rectKey, label] of [
      ["listRect", "conversation list"],
      ["chatRect", "chat pane"],
    ]) {
      if (!data[rectKey] || data[rectKey].width < 180 || data[rectKey].height < 280) {
        failures.push(`${prefix}: ${label} is too small`);
      }
    }
    if (!data.isWechatSimplified && (!data.inspectorRect || data.inspectorRect.width < 180 || data.inspectorRect.height < 280)) {
      failures.push(`${prefix}: inspector is too small`);
    }
    if (data.isWechatSimplified && data.hasDirectInspector) {
      failures.push(`${prefix}: old direct third-column inspector should not exist in simplified desk`);
    }
  }
  if (view.name === "desktop-1440" && data.listRect && data.listRect.top > view.height * 0.86) {
    failures.push(`${prefix}: main service desk starts too low in the first viewport`);
  }
  if (view.mobile && data.dockRect && data.dockRect.width > view.width) {
    failures.push(`${prefix}: reply dock wider than viewport`);
  }
  return failures;
}

fs.mkdirSync(outputDir, { recursive: true });

const results = [];
for (const viewport of viewports) {
  results.push(await measure(viewport));
}

const failures = results.flatMap(validate);
fs.writeFileSync(path.join(outputDir, "conversation-workbench-metrics.json"), JSON.stringify(results, null, 2));
fs.writeFileSync(path.join(outputDir, "conversation-workbench-summary.json"), JSON.stringify({ failures, results }, null, 2));

if (failures.length > 0) {
  console.error(JSON.stringify({ status: "failed", failures }, null, 2));
  process.exit(1);
}

console.log(JSON.stringify({ status: "passed", outputDir, checked: viewports.map((item) => item.name) }, null, 2));
