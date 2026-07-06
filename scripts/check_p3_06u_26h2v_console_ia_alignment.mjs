import fs from "node:fs";
import path from "node:path";

const chromeEndpoint = process.env.CHROME_DEBUGGING_URL ?? "http://127.0.0.1:9227";
const frontendUrl = process.env.FRONTEND_URL ?? "http://127.0.0.1:5182/?demo=1";
const outputDir = path.resolve(process.env.P3_06U_26H2V_OUTPUT ?? "output/p3_06u_26h2v_console_ia_alignment");

const viewports = [
  { name: "desktop-1440", width: 1440, height: 900 },
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

function withHash(baseUrl, hash) {
  return `${baseUrl.replace(/#.*$/, "")}${hash}`;
}

async function navigate(cdp, url) {
  await cdp.send("Page.navigate", { url });
  await delay(700);
}

async function capture(cdp, viewportName, name) {
  const screenshot = await cdp.send("Page.captureScreenshot", {
    format: "png",
    fromSurface: true,
    captureBeyondViewport: false
  });
  fs.writeFileSync(path.join(outputDir, `${viewportName}-${name}.png`), Buffer.from(screenshot.data, "base64"));
}

async function inspectViewport(viewport) {
  const target = await createTarget("about:blank");
  const cdp = await createCdp(target.webSocketDebuggerUrl);
  const checks = {};
  try {
    await cdp.send("Page.enable");
    await cdp.send("Runtime.enable");
    await cdp.send("Emulation.setDeviceMetricsOverride", {
      width: viewport.width,
      height: viewport.height,
      deviceScaleFactor: 1,
      mobile: false
    });

    await navigate(cdp, withHash(frontendUrl, "#overview"));
    await waitFor(cdp, `Boolean(document.querySelector('#workspace-overview .ops-bi-filter-proof'))`);
    await evalValue(cdp, `(() => {
      const clickButton = (label) => {
        const buttons = Array.from(document.querySelectorAll('.ops-bi-filter-stack button'));
        const target = buttons.find((button) => button.textContent?.includes(label));
        target?.click();
      };
      clickButton('近 7 天');
      clickButton('全部渠道');
      return true;
    })()`);
    await delay(600);
    checks.overview = await evalValue(cdp, `(() => {
      const proof = document.querySelector('.ops-bi-filter-proof');
      const text = document.body.innerText;
      return {
        title: document.querySelector('.topbar h1')?.textContent?.trim() ?? '',
        hasProof: Boolean(proof),
        proofMode: proof?.getAttribute('data-filter-alignment') ?? '',
        proofText: proof?.textContent?.trim() ?? '',
        hasRangeActive: Array.from(document.querySelectorAll('.ops-bi-range button.active')).some((button) => button.textContent?.includes('近 7 天')),
        hasChannelFilter: text.includes('渠道筛选'),
        hasOldManualSnapshot: text.includes('人工池快照'),
        hasOldQueueCopy: text.includes('待人工审核') || text.includes('待发送确认') || text.includes('工单超时'),
        overflowX: document.documentElement.scrollWidth > innerWidth || document.body.scrollWidth > innerWidth
      };
    })()`);
    await capture(cdp, viewport.name, "overview");

    await navigate(cdp, withHash(frontendUrl, "#channels"));
    await waitFor(cdp, `Boolean(document.querySelector('.channel-layer-tabs'))`);
    const readChannelLayers = () => evalValue(cdp, `(() => {
      const visible = (selector) => {
        const node = document.querySelector(selector);
        return Boolean(node) && !node.hasAttribute('hidden');
      };
      return {
        accountsVisible: visible('[data-channel-account-manager="p3-06u-26c"]'),
        wecomVisible: visible('[data-channel-layer="wecom"]'),
        officialVisible: visible('.channel-official-grid'),
        boundariesVisible: visible('[data-channel-sandbox-priority="p3-06u-26g"]')
      };
    })()`);
    const clickChannelLayer = async (label) => {
      await evalValue(cdp, `(() => {
        const buttons = Array.from(document.querySelectorAll('.channel-layer-tabs button'));
        buttons.find((item) => item.textContent?.includes(${JSON.stringify(label)}))?.click();
        return true;
      })()`);
      await delay(450);
    };
    const initialLayer = await readChannelLayers();
    await clickChannelLayer('企业微信步骤');
    const wecomLayer = await readChannelLayers();
    await clickChannelLayer('其它官方平台');
    const officialLayer = await readChannelLayers();
    await clickChannelLayer('接入边界');
    const boundaryLayer = await readChannelLayers();
    checks.channels = await evalValue(cdp, `(() => ({
        title: document.querySelector('.topbar h1')?.textContent?.trim() ?? '',
        tabCount: document.querySelectorAll('.channel-layer-tabs button').length,
        initial: null,
        wecom: null,
        official: null,
        boundaries: null,
        hasExternalWriteBoundary: document.body.innerText.includes('真实外发继续关闭') || document.body.innerText.includes('真实外发关闭'),
        overflowX: document.documentElement.scrollWidth > innerWidth || document.body.scrollWidth > innerWidth
      }))()`);
    checks.channels.tabCount = await evalValue(cdp, `document.querySelectorAll('.channel-layer-tabs button').length`);
    checks.channels.initial = initialLayer;
    checks.channels.wecom = wecomLayer;
    checks.channels.official = officialLayer;
    checks.channels.boundaries = boundaryLayer;
    await capture(cdp, viewport.name, "channels");

    const pageChecks = [];
    for (const page of [
      { hash: "#ops", selector: "#workspace-ops", title: "运维与告警" },
      { hash: "#model", selector: "#workspace-model", title: "模型路由" },
      { hash: "#settings", selector: "#workspace-settings", title: "账号安全" }
    ]) {
      await navigate(cdp, withHash(frontendUrl, page.hash));
      await waitFor(cdp, `Boolean(document.querySelector(${JSON.stringify(page.selector)}))`);
      pageChecks.push(await evalValue(cdp, `(() => ({
        hash: location.hash,
        hasPage: Boolean(document.querySelector(${JSON.stringify(page.selector)})),
        title: document.querySelector('.topbar h1')?.textContent?.trim() ?? '',
        hasSharedTabs: Boolean(document.querySelector('.admin-ops-tabs')) || Boolean(document.querySelector('#workspace-admin-ops')),
        overflowX: document.documentElement.scrollWidth > innerWidth || document.body.scrollWidth > innerWidth
      }))()`));
      await capture(cdp, viewport.name, page.hash.replace("#", ""));
    }
    checks.managementPages = pageChecks;

    await navigate(cdp, withHash(frontendUrl, "#live"));
    await waitFor(cdp, `Boolean(document.querySelector('#workspace-live'))`);
    checks.live = await evalValue(cdp, `(() => {
      const text = document.body.innerText;
      return {
        hasDesk: Boolean(document.querySelector('#workspace-live.wechat-service-desk')),
        hasConversationList: Boolean(document.querySelector('.wechat-session-list .service-thread-item')),
        hasChatPane: Boolean(document.querySelector('.wechat-chat-pane')),
        hasMessageStream: Boolean(document.querySelector('.service-message-stream .timeline-event')),
        hasReplyDock: Boolean(document.querySelector('.service-reply-dock')),
        hasPrimaryQueues: Array.from(document.querySelectorAll('.service-primary-queues .queue-tab')).map((item) => item.textContent?.trim() ?? '').join('|'),
        hasForbiddenQueueCopy: text.includes('待审') || text.includes('待发') || text.includes('待审核') || text.includes('待发送草稿'),
        hasOldOverclaim: text.includes('自动回复中') || text.includes('AI 正在自动接待') || text.includes('人工无需操作') || text.includes('系统按渠道配置自动回复'),
        hasDraftOnlyBoundary: text.includes('真实外发关闭') || text.includes('真实外发继续等待渠道授权'),
        hasAiSuggestionCopy: text.includes('AI 建议') || text.includes('AI 回复建议') || text.includes('客户可见回复预案'),
        overflowX: document.documentElement.scrollWidth > innerWidth || document.body.scrollWidth > innerWidth
      };
    })()`);
    await capture(cdp, viewport.name, "live");

    const runtimeErrors = cdp.events
      .filter((event) => event.method === "Runtime.exceptionThrown")
      .map((event) => event.params?.exceptionDetails?.exception?.description || event.params?.exceptionDetails?.text || "runtime error");
    return { viewport, checks, runtimeErrors };
  } finally {
    cdp.close();
    await closeTarget(target.id);
  }
}

function validate(result) {
  const failures = [];
  const prefix = result.viewport.name;
  const overview = result.checks.overview;
  if (!overview?.hasProof) failures.push(`${prefix}: overview filter proof missing`);
  if (!["server-aligned", "local-fallback"].includes(overview?.proofMode)) failures.push(`${prefix}: overview proof mode invalid`);
  if (!overview?.hasRangeActive) failures.push(`${prefix}: overview range active state did not update`);
  if (!overview?.hasChannelFilter) failures.push(`${prefix}: overview channel filter missing`);
  if (overview?.hasOldManualSnapshot) failures.push(`${prefix}: overview still contains manual pool snapshot`);
  if (overview?.hasOldQueueCopy) failures.push(`${prefix}: overview still contains removed queue copy`);
  if (overview?.overflowX) failures.push(`${prefix}: overview horizontal overflow`);

  const channels = result.checks.channels;
  if (channels?.tabCount !== 4) failures.push(`${prefix}: channel layer tab count should be 4`);
  if (!channels?.initial.accountsVisible) failures.push(`${prefix}: channel accounts layer should be default`);
  if (channels?.initial.wecomVisible || channels?.initial.officialVisible || channels?.initial.boundariesVisible) {
    failures.push(`${prefix}: non-default channel layers should start hidden`);
  }
  if (!channels?.wecom.wecomVisible || channels?.wecom.accountsVisible) failures.push(`${prefix}: wecom layer toggle failed`);
  if (!channels?.official.officialVisible || channels?.official.wecomVisible) failures.push(`${prefix}: official layer toggle failed`);
  if (!channels?.boundaries.boundariesVisible || channels?.boundaries.officialVisible) failures.push(`${prefix}: boundary layer toggle failed`);
  if (!channels?.hasExternalWriteBoundary) failures.push(`${prefix}: channel external write boundary missing`);
  if (channels?.overflowX) failures.push(`${prefix}: channels horizontal overflow`);

  for (const page of result.checks.managementPages ?? []) {
    const expectedTitle = page.hash === "#ops" ? "运维与告警" : page.hash === "#model" ? "模型路由" : "账号安全";
    if (!page.hasPage) failures.push(`${prefix}: ${page.hash} page missing`);
    if (page.title !== expectedTitle) failures.push(`${prefix}: ${page.hash} title is ${page.title}, expected ${expectedTitle}`);
    if (page.hasSharedTabs) failures.push(`${prefix}: ${page.hash} still renders shared admin ops tabs`);
    if (page.overflowX) failures.push(`${prefix}: ${page.hash} horizontal overflow`);
  }

  const live = result.checks.live;
  if (!live?.hasDesk) failures.push(`${prefix}: live desk missing`);
  if (!live?.hasConversationList) failures.push(`${prefix}: live desk conversation list missing`);
  if (!live?.hasChatPane) failures.push(`${prefix}: live desk chat pane missing`);
  if (!live?.hasMessageStream) failures.push(`${prefix}: live desk message stream missing`);
  if (!live?.hasReplyDock) failures.push(`${prefix}: live desk reply dock missing`);
  if (!live?.hasPrimaryQueues?.includes("全部") || !live?.hasPrimaryQueues?.includes("我的") || !live?.hasPrimaryQueues?.includes("转人工")) {
    failures.push(`${prefix}: live desk primary queues should be 全部 / 我的 / 转人工`);
  }
  if (live?.hasForbiddenQueueCopy) failures.push(`${prefix}: live desk still exposes old review/send queue copy`);
  if (live?.hasOldOverclaim) failures.push(`${prefix}: live desk still has overclaiming auto-reply copy`);
  if (!live?.hasDraftOnlyBoundary) failures.push(`${prefix}: live desk missing draft-only boundary`);
  if (live?.hasAiSuggestionCopy) failures.push(`${prefix}: live desk still exposes AI suggestion/review planning copy`);
  if (live?.overflowX) failures.push(`${prefix}: live desk horizontal overflow`);

  for (const error of result.runtimeErrors) failures.push(`${prefix}: runtime error: ${error}`);
  return failures;
}

async function main() {
  fs.mkdirSync(outputDir, { recursive: true });
  const results = [];
  const failures = [];
  for (const viewport of viewports) {
    const result = await inspectViewport(viewport);
    results.push(result);
    failures.push(...validate(result));
  }
  fs.writeFileSync(
    path.join(outputDir, "summary.json"),
    JSON.stringify(results, null, 2)
  );
  if (failures.length) {
    console.error("P3-06U-26H2V console IA alignment check failed:");
    failures.forEach((failure) => console.error(`- ${failure}`));
    process.exit(1);
  }
  console.log(`P3-06U-26H2V console IA alignment check passed. Evidence: ${outputDir}`);
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
