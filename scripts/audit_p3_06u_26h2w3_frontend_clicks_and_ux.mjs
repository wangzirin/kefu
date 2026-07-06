import fs from "node:fs";
import path from "node:path";

const chromeEndpoint = process.env.CHROME_DEBUGGING_URL ?? "http://127.0.0.1:9227";
const frontendBaseUrl = process.env.FRONTEND_URL ?? "http://127.0.0.1:5182/?demo=1";
const outputDir = path.resolve(process.env.P3_06U_26H2W3_AUDIT_OUTPUT ?? "output/p3_06u_26h2w3_frontend_deep_audit");

const pages = [
  { hash: "#overview", label: "运营总览", selector: "#workspace-overview" },
  { hash: "#live", label: "客服接待", selector: "#workspace-live" },
  { hash: "#contacts", label: "联系人中心", selector: "#workspace-contacts" },
  { hash: "#leads", label: "线索跟进", selector: "#workspace-leads" },
  { hash: "#knowledge", label: "知识库运营", selector: '[data-knowledge-page-shell="library"]' },
  { hash: "#gaps", label: "知识缺口", selector: '[data-knowledge-page-shell="gaps"]' },
  { hash: "#evals", label: "发布前检查", selector: '[data-knowledge-page-shell="evals"]' },
  { hash: "#quality", label: "质量复盘", selector: "#workspace-quality" },
  { hash: "#channels", label: "渠道接入", selector: '[data-channel-account-manager="p3-06u-26c"]' },
  { hash: "#ops", label: "运维与告警", selector: "#workspace-ops" },
  { hash: "#model", label: "模型路由", selector: "#workspace-model" },
  { hash: "#settings", label: "账号安全", selector: "#workspace-settings" }
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

function withHash(hash) {
  return `${frontendBaseUrl.replace(/#.*$/, "")}${hash}`;
}

async function screenshot(cdp, name) {
  const shot = await cdp.send("Page.captureScreenshot", {
    format: "png",
    fromSurface: true,
    captureBeyondViewport: false
  });
  fs.writeFileSync(path.join(outputDir, `${name}.png`), Buffer.from(shot.data, "base64"));
}

async function clickTextButtons(cdp, labels) {
  const clicked = [];
  for (const label of labels) {
    const didClick = await evalValue(cdp, `(() => {
      const candidates = Array.from(document.querySelectorAll('button, a[href]'));
      const target = candidates.find((node) => (node.textContent || '').replace(/\\s+/g, ' ').trim().includes(${JSON.stringify(label)}));
      if (!target) return false;
      target.click();
      return true;
    })()`);
    if (didClick) {
      clicked.push(label);
      await delay(260);
    }
  }
  return clicked;
}

async function inspectPage(cdp, page) {
  await cdp.send("Page.navigate", { url: withHash(page.hash) });
  await waitFor(cdp, `Boolean(document.querySelector(${JSON.stringify(page.selector)}))`);
  await delay(550);
  let clicked = [];
  if (page.hash === "#overview") clicked = await clickTextButtons(cdp, ["今日", "近 7 天", "近 30 天"]);
  if (page.hash === "#live") clicked = await clickTextButtons(cdp, ["全部", "我的", "转人工"]);
  if (page.hash === "#channels") clicked = await clickTextButtons(cdp, ["账号与入口", "企业微信步骤", "其它官方平台", "接入边界"]);

  const pageName = page.hash.replace("#", "");
  await screenshot(cdp, pageName);
  const data = await evalValue(cdp, `(() => {
    const text = document.body.innerText;
    const buttons = Array.from(document.querySelectorAll('button'));
    const anchors = Array.from(document.querySelectorAll('a[href]'));
    const hiddenBackendLinks = anchors
      .filter((node) => ['#conversations', '#reviews', '#outbox', '#tickets'].some((hash) => (node.getAttribute('href') || '').startsWith(hash)))
      .map((node) => ({ text: (node.textContent || '').replace(/\\s+/g, ' ').trim(), href: node.getAttribute('href') }));
    const buttonStats = {
      total: buttons.length,
      enabled: buttons.filter((button) => !button.disabled).length,
      disabled: buttons.filter((button) => button.disabled).length,
      unlabeled: buttons
        .filter((button) => !((button.textContent || '').trim() || button.getAttribute('aria-label')))
        .map((button) => button.outerHTML.slice(0, 160))
    };
    const longTextBlocks = Array.from(document.querySelectorAll('p, small, li'))
      .map((node) => (node.textContent || '').replace(/\\s+/g, ' ').trim())
      .filter((value) => value.length > 90)
      .slice(0, 8);
    const engineeringTerms = ['H2W', 'P3-06', 'sandbox', 'dry-run', 'outbox', 'API', 'connector_noop']
      .filter((term) => text.includes(term));
    const normalizedText = text
      .replace(/不自动真实外发/g, '')
      .replace(/不会自动真实外发/g, '')
      .replace(/不允许自动真实外发/g, '')
      .replace(/未自动真实外发/g, '')
      .replace(/不展示完整线上准确率/g, '')
      .replace(/不展示线上全量准确率/g, '');
    const overclaimTerms = ['线上全量准确率', '已经接通所有渠道', '自动真实外发', '人工无需操作']
      .filter((term) => normalizedText.includes(term));
    const externalWriteBoundaryTerms = ['不自动真实外发', '不会自动真实外发', '不允许自动真实外发', '真实外发关闭']
      .filter((term) => text.includes(term));
    const root = document.documentElement;
    const liveListItem = document.querySelector('.wechat-session-list .service-thread-item')?.getBoundingClientRect();
    const liveStream = document.querySelector('.wechat-chat-pane .service-message-stream')?.getBoundingClientRect();
    return {
      hash: location.hash,
      title: document.querySelector('.topbar h1')?.textContent?.trim() || document.querySelector('h1,h2')?.textContent?.trim() || '',
      hasPage: Boolean(document.querySelector(${JSON.stringify(page.selector)})),
      overflowX: root.scrollWidth > innerWidth || document.body.scrollWidth > innerWidth,
      runtimeWidth: { scrollWidth: root.scrollWidth, bodyWidth: document.body.scrollWidth, innerWidth },
      buttonStats,
      hiddenBackendLinks,
      longTextBlocks,
      engineeringTerms,
      overclaimTerms,
      externalWriteBoundaryTerms,
      hasPreviewCopy: text.includes('预览') || text.includes('演示'),
      liveListItem: liveListItem ? { width: Math.round(liveListItem.width), height: Math.round(liveListItem.height) } : null,
      liveStream: liveStream ? { width: Math.round(liveStream.width), height: Math.round(liveStream.height) } : null
    };
  })()`);
  return { page, clicked, data };
}

function collectIssues(results, runtimeErrors) {
  const issues = [];
  for (const result of results) {
    const { page, data } = result;
    const prefix = page.label;
    if (!data.hasPage) issues.push({ severity: "P0", page: prefix, issue: "页面主体 selector 未渲染", evidence: page.selector });
    if (data.overflowX) issues.push({ severity: "P1", page: prefix, issue: "出现横向溢出", evidence: JSON.stringify(data.runtimeWidth) });
    if (data.buttonStats.unlabeled.length > 0) {
      issues.push({ severity: "P1", page: prefix, issue: "存在无文本且无 aria-label 的按钮", evidence: data.buttonStats.unlabeled.join(" | ") });
    }
    if (data.hiddenBackendLinks.length > 0 && ["运营总览", "质量复盘"].includes(prefix)) {
      issues.push({
        severity: "P1",
        page: prefix,
        issue: "客户可见页面仍直达隐藏后台路由",
        evidence: data.hiddenBackendLinks.map((item) => `${item.text} -> ${item.href}`).join(" ; ")
      });
    }
    if (data.longTextBlocks.length >= 4) {
      issues.push({
        severity: "P2",
        page: prefix,
        issue: "说明性长文案偏多",
        evidence: data.longTextBlocks.slice(0, 3).join(" / ")
      });
    }
    if (data.engineeringTerms.length > 0 && ["质量复盘", "渠道接入", "运维与告警", "账号安全"].includes(prefix)) {
      issues.push({ severity: "P2", page: prefix, issue: "客户可见区域出现工程术语", evidence: data.engineeringTerms.join(", ") });
    }
    if (data.overclaimTerms.length > 0) {
      issues.push({ severity: "P0", page: prefix, issue: "出现能力过度承诺文案", evidence: data.overclaimTerms.join(", ") });
    }
    if (page.hash === "#live" && data.liveListItem && data.liveListItem.height < 82) {
      issues.push({ severity: "P2", page: prefix, issue: "会话列表项较瘦，信息密度高但可读余量不足", evidence: JSON.stringify(data.liveListItem) });
    }
    if (page.hash === "#live" && data.liveStream && data.liveStream.height < 360) {
      issues.push({ severity: "P1", page: prefix, issue: "消息流区域偏短，底部回复区挤占对话阅读空间", evidence: JSON.stringify(data.liveStream) });
    }
  }
  for (const error of runtimeErrors) {
    issues.push({ severity: "P0", page: "全局", issue: "浏览器运行时报错", evidence: error });
  }
  return issues;
}

async function main() {
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
    const results = [];
    for (const page of pages) {
      results.push(await inspectPage(cdp, page));
    }
    const runtimeErrors = cdp.events
      .filter((event) => event.method === "Runtime.exceptionThrown")
      .map((event) => event.params?.exceptionDetails?.exception?.description || event.params?.exceptionDetails?.text || "runtime error");
    const issues = collectIssues(results, runtimeErrors);
    fs.writeFileSync(path.join(outputDir, "summary.json"), JSON.stringify({ frontendBaseUrl, results, runtimeErrors, issues }, null, 2));
    console.log(`P3-06U-26H2W3 frontend deep click audit completed. Issues: ${issues.length}. Evidence: ${outputDir}`);
    if (runtimeErrors.length > 0) process.exitCode = 1;
  } finally {
    cdp.close();
    await closeTarget(target.id);
  }
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
