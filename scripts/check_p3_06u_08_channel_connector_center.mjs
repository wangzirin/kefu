import fs from "node:fs";
import path from "node:path";

const chromeEndpoint = process.env.CHROME_DEBUGGING_URL ?? "http://127.0.0.1:9224";
const frontendUrl = process.env.FRONTEND_URL ?? "http://127.0.0.1:5178/#channels";
const outputDir = path.resolve(process.env.P3_06U_08_OUTPUT ?? "output/p3_06u_08_channel_connector_center");

const viewports = [
  { name: "desktop-1440", width: 1440, height: 900, mobile: false },
  { name: "desktop-900", width: 900, height: 900, mobile: false },
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

async function enterDemoChannels(cdp) {
  await delay(500);
  await evalValue(cdp, `(() => {
    const button = Array.from(document.querySelectorAll('button')).find((item) =>
      item.textContent?.includes('开发演示进入')
    );
    if (button) button.click();
    return Boolean(button);
  })()`);
  const appReady = await waitFor(cdp, `Boolean(document.querySelector('.app-shell'))`);
  if (!appReady) return false;
  await evalValue(cdp, `location.hash = '#channels'`);
  const channelsReady = await waitFor(cdp, `Boolean(document.querySelector('[data-channel-connector-smoke="center"]'))`);
  await delay(360);
  return channelsReady;
}

async function capture(cdp, name) {
  const screenshot = await cdp.send("Page.captureScreenshot", {
    format: "png",
    fromSurface: true,
    captureBeyondViewport: false
  });
  fs.writeFileSync(path.join(outputDir, `${name}.png`), Buffer.from(screenshot.data, "base64"));
}

async function inspectChannels(cdp) {
  return evalValue(cdp, `(() => {
    const text = document.body.innerText;
    const stepLabels = Array.from(document.querySelectorAll('[data-channel-connector-step]')).map((item) =>
      item.getAttribute('data-channel-connector-step') || ''
    );
    const configLabels = Array.from(document.querySelectorAll('[data-channel-connector-config]')).map((item) =>
      item.getAttribute('data-channel-connector-config') || ''
    );
    return {
      href: location.href,
      hash: location.hash,
      hasCenter: Boolean(document.querySelector('[data-channel-connector-smoke="center"]')),
      hasPrimary: Boolean(document.querySelector('[data-channel-connector-primary="wecom"]')),
      stepCount: stepLabels.length,
      stepLabels,
      configLabels,
      officialOnlyCards: document.querySelectorAll('[data-channel-official-only="true"] .channel-official-card').length,
      hasCurrentBlocker: Boolean(document.querySelector('[data-channel-current-blocker]')),
      hasSecretMask: text.includes('已隐藏明文') && text.includes('secret://channel/wecom/token'),
      hasCallbackCopy: text.includes('公网 HTTPS 回调 URL') && text.includes('回调 URL 待配置'),
      hasAesCopy: text.includes('EncodingAESKey') && text.includes('Token'),
      hasTrustedIpCopy: text.includes('可信 IP') && text.includes('服务器固定出口 IP'),
      hasNoExternalWriteCopy: text.includes('不默认打开真实外发') || text.includes('不自动真实外发'),
      hasOfficialOnlyCopy: text.includes('公众号') && text.includes('抖音 / 抖店') && text.includes('小红书') && text.includes('淘宝 / 天猫') && text.includes('京东 / 拼多多'),
      hasNoHookCopy: text.includes('个人号外挂') && text.includes('Hook') && text.includes('模拟点击') && text.includes('商家后台群控'),
      hasCommercialBlockers: text.includes('已备案域名') && text.includes('公网 HTTPS') && text.includes('URL 验证') && text.includes('AES 解密'),
      overflowX: document.documentElement.scrollWidth > innerWidth || document.body.scrollWidth > innerWidth,
      innerWidth,
      bodyText: text.slice(0, 6000)
    };
  })()`);
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
    await cdp.send("Page.navigate", { url: frontendUrl });
    await cdp.waitFor("Page.loadEventFired", 12000).catch(() => undefined);
    const ready = await enterDemoChannels(cdp);
    if (!ready) throw new Error(`${viewport.name}: channels page did not load`);

    const channels = await inspectChannels(cdp);
    await capture(cdp, `${viewport.name}-channels`);
    await evalValue(cdp, `document.querySelector('[data-channel-connector-smoke="center"]')?.scrollIntoView({ block: 'start' })`);
    await delay(250);
    await capture(cdp, `${viewport.name}-connector-center`);
    return { viewport, channels };
  } finally {
    cdp.close();
    await closeTarget(target.id);
  }
}

function validate(result) {
  const failures = [];
  const { viewport, channels } = result;
  const prefix = viewport.name;
  const requiredSteps = [
    "未配置",
    "已创建客服账号",
    "已绑定接待人员",
    "已获取链接/二维码",
    "回调 URL 待配置",
    "URL 验证通过",
    "已收到入站消息",
    "已生成 AI 草稿",
    "已进入人工审核",
    "白名单发送测试通过"
  ];
  const requiredConfigs = ["公网 HTTPS 回调 URL", "Token", "EncodingAESKey", "可信 IP"];

  if (!channels.hasCenter) failures.push(`${prefix}: missing connector center`);
  if (!channels.hasPrimary) failures.push(`${prefix}: missing wecom primary connector`);
  if (channels.stepCount < 10) failures.push(`${prefix}: expected 10 wecom steps`);
  for (const step of requiredSteps) {
    if (!channels.stepLabels.includes(step)) failures.push(`${prefix}: missing step ${step}`);
  }
  for (const config of requiredConfigs) {
    if (!channels.configLabels.includes(config)) failures.push(`${prefix}: missing config ${config}`);
  }
  if (channels.officialOnlyCards < 5) failures.push(`${prefix}: expected 5 official-only connector cards`);
  if (!channels.hasCurrentBlocker) failures.push(`${prefix}: missing current blocker marker`);
  if (!channels.hasSecretMask) failures.push(`${prefix}: missing secret mask copy`);
  if (!channels.hasCallbackCopy) failures.push(`${prefix}: missing callback URL copy`);
  if (!channels.hasAesCopy) failures.push(`${prefix}: missing token/aes copy`);
  if (!channels.hasTrustedIpCopy) failures.push(`${prefix}: missing trusted IP copy`);
  if (!channels.hasNoExternalWriteCopy) failures.push(`${prefix}: missing no external write copy`);
  if (!channels.hasOfficialOnlyCopy) failures.push(`${prefix}: missing official-only platform copy`);
  if (!channels.hasNoHookCopy) failures.push(`${prefix}: missing no hook/simulation copy`);
  if (!channels.hasCommercialBlockers) failures.push(`${prefix}: missing commercial blockers`);
  if (channels.overflowX) failures.push(`${prefix}: channels page has horizontal overflow`);
  return failures;
}

async function main() {
  fs.mkdirSync(outputDir, { recursive: true });
  const results = [];
  for (const viewport of viewports) {
    results.push(await runViewport(viewport));
  }
  const failures = results.flatMap(validate);
  fs.writeFileSync(path.join(outputDir, "summary.json"), JSON.stringify({ ok: failures.length === 0, failures, results }, null, 2));
  if (failures.length > 0) {
    throw new Error(`P3-06U-08 channel connector center smoke failed:\\n${failures.join("\\n")}`);
  }
  console.log(`P3-06U-08 channel connector center smoke passed. Evidence: ${outputDir}`);
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
