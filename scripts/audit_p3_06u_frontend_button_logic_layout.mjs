import fs from "node:fs";
import path from "node:path";
import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";

const rootDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const outputDir = path.resolve(
  process.env.WANFA_FRONTEND_AUDIT_OUTPUT ??
    path.join(rootDir, "output/p3_06u_frontend_button_logic_layout_audit")
);
const frontendBaseUrl = process.env.WANFA_FRONTEND_URL ?? "http://127.0.0.1:5182/";
const backendUrl = process.env.WANFA_BACKEND_URL ?? "http://127.0.0.1:8081";
const chromePort = Number(process.env.WANFA_FRONTEND_AUDIT_CHROME_PORT ?? 9357);
const chromeEndpoint = `http://127.0.0.1:${chromePort}`;
const chromeProfile = path.join(outputDir, "chrome-profile");
const children = [];

const credentials = {
  tenantSlug: process.env.AUDIT_TENANT_SLUG ?? "wanfa-local-dev",
  email: process.env.AUDIT_EMAIL ?? "real-test@wanfa.local",
  password: process.env.AUDIT_PASSWORD ?? "WanfaTest2026!"
};

const pages = [
  { hash: "#overview", selector: "#workspace-overview", label: "运营总览" },
  { hash: "#pilot", selector: "#workspace-pilot", label: "本地试运行准备" },
  { hash: "#live", selector: "#workspace-live", label: "接待工作台" },
  { hash: "#contacts", selector: "#workspace-contacts", label: "联系人中心" },
  { hash: "#leads", selector: "#workspace-leads", label: "线索跟进" },
  { hash: "#knowledge", selector: "#workspace-knowledge", label: "知识库运营" },
  { hash: "#gaps", selector: "[data-knowledge-page-shell=\"gaps\"]", label: "知识缺口" },
  { hash: "#evals", selector: "[data-knowledge-page-shell=\"evals\"]", label: "知识评测" },
  { hash: "#quality", selector: "#workspace-quality", label: "质量复盘" },
  { hash: "#channels", selector: "#workspace-channels", label: "渠道接入" },
  { hash: "#model", selector: "#workspace-model", label: "自动回复策略" },
  { hash: "#ops", selector: "#workspace-ops, #workspace-operations, #workspace-ops-health", label: "运维与告警" },
  { hash: "#settings", selector: "#workspace-settings", label: "账号与本地维护" }
];

const riskyClickTerms = [
  "删除",
  "清空",
  "重置",
  "恢复",
  "回滚",
  "应用更新包",
  "确认恢复",
  "注销",
  "退出登录"
];

const customerVisibleEngineeringTerms = [
  "H2W",
  "P3-",
  "dry-run",
  "provider",
  "outbox",
  "sandbox",
  "rehearsal",
  "connector_noop"
];

const confusingTerms = ["试点准备", "保存接管回复"];

function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function spawnLongRunning(name, command, args) {
  fs.mkdirSync(outputDir, { recursive: true });
  const log = fs.createWriteStream(path.join(outputDir, `${name}.log`), { flags: "a" });
  const child = spawn(command, args, { cwd: rootDir, stdio: ["ignore", "pipe", "pipe"] });
  children.push(child);
  child.stdout.pipe(log);
  child.stderr.pipe(log);
  return child;
}

function chromeBinary() {
  const candidates = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium"
  ];
  const found = candidates.find((candidate) => fs.existsSync(candidate));
  if (!found) throw new Error("Chrome binary not found");
  return found;
}

async function waitForHttp(url, timeoutMs = 30000) {
  const started = Date.now();
  while (Date.now() - started < timeoutMs) {
    try {
      const response = await fetch(url);
      if (response.ok) return;
    } catch {
      // keep polling
    }
    await delay(250);
  }
  throw new Error(`Timed out waiting for ${url}`);
}

async function startChrome() {
  fs.rmSync(chromeProfile, { recursive: true, force: true });
  fs.mkdirSync(chromeProfile, { recursive: true });
  spawnLongRunning("chrome", chromeBinary(), [
    `--remote-debugging-port=${chromePort}`,
    `--user-data-dir=${chromeProfile}`,
    "--headless=new",
    "--disable-gpu",
    "--no-first-run",
    "--no-default-browser-check",
    "about:blank"
  ]);
  await waitForHttp(`${chromeEndpoint}/json/version`);
}

async function createTarget(url) {
  const response = await fetch(`${chromeEndpoint}/json/new?${encodeURIComponent(url)}`, { method: "PUT" });
  if (!response.ok) throw new Error(`Failed to create target: ${response.status}`);
  return response.json();
}

function createCdp(wsUrl) {
  const ws = new WebSocket(wsUrl);
  let id = 0;
  const pending = new Map();
  const events = [];
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
    ws.addEventListener("message", (event) => {
      const message = JSON.parse(event.data);
      if (message.id && pending.has(message.id)) {
        const waiter = pending.get(message.id);
        pending.delete(message.id);
        if (message.error) waiter.reject(new Error(JSON.stringify(message.error)));
        else waiter.resolve(message.result || {});
        return;
      }
      if (message.method) events.push(message);
    });
    ws.addEventListener("error", reject);
  });
}

async function evalValue(cdp, expression) {
  const result = await cdp.send("Runtime.evaluate", { expression, awaitPromise: true, returnByValue: true });
  if (result.exceptionDetails) throw new Error(JSON.stringify(result.exceptionDetails));
  return result.result.value;
}

async function waitForExpression(cdp, expression, timeoutMs = 25000) {
  const started = Date.now();
  while (Date.now() - started < timeoutMs) {
    const value = await evalValue(cdp, expression).catch(() => false);
    if (value) return value;
    await delay(250);
  }
  throw new Error(`Timed out waiting for expression: ${expression}`);
}

async function capture(cdp, name) {
  const screenshot = await cdp.send("Page.captureScreenshot", {
    format: "png",
    fromSurface: true,
    captureBeyondViewport: false
  });
  fs.writeFileSync(path.join(outputDir, `${name}.png`), Buffer.from(screenshot.data, "base64"));
}

function withHash(hash) {
  return `${frontendBaseUrl.replace(/#.*$/, "").replace(/\/?$/, "/")}${hash}`;
}

async function loginThroughUi(cdp) {
  await cdp.send("Page.navigate", { url: frontendBaseUrl });
  await waitForExpression(cdp, "Boolean(document.querySelector('[data-role-smoke=\"login-form\"]'))", 25000);
  await evalValue(cdp, `(() => {
    const values = ${JSON.stringify(credentials)};
    const setInput = (selector, value) => {
      const input = document.querySelector(selector);
      if (!input) throw new Error('missing input ' + selector);
      const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;
      setter.call(input, value);
      input.dispatchEvent(new Event('input', { bubbles: true }));
      input.dispatchEvent(new Event('change', { bubbles: true }));
    };
    setInput('[data-role-smoke="tenant-slug"]', values.tenantSlug);
    setInput('[data-role-smoke="email"]', values.email);
    setInput('[data-role-smoke="password"]', values.password);
    document.querySelector('[data-role-smoke="login-form"]').requestSubmit();
    return true;
  })()`);
  await waitForExpression(
    cdp,
    "Boolean(document.querySelector('#workspace-overview')) && !document.querySelector('[data-role-smoke=\"login-form\"]')",
    25000
  );
}

function normalizeText(value) {
  return String(value ?? "").replace(/\s+/g, " ").trim();
}

function slugify(value) {
  return value.replace(/^#/, "").replace(/[^a-z0-9_-]+/gi, "-").slice(0, 60) || "page";
}

async function navigateToPage(cdp, page) {
  await cdp.send("Page.navigate", { url: withHash(page.hash) });
  await delay(900);
  await waitForExpression(
    cdp,
    `${JSON.stringify(page.selector)}.split(',').some((selector) => Boolean(document.querySelector(selector.trim())))`,
    20000
  );
}

async function inspectPage(cdp, page, pageIndex) {
  await navigateToPage(cdp, page);
  const pageSlug = `${String(pageIndex + 1).padStart(2, "0")}-${slugify(page.hash)}`;
  const pageSelectors = page.selector.split(",").map((selector) => selector.trim()).filter(Boolean);
  const auditPrefix = page.hash.replace("#", "") || "page";
  await capture(cdp, `${pageSlug}-before`);
  const staticResult = await evalValue(cdp, `(() => {
    const visible = (el) => {
      const rect = el.getBoundingClientRect();
      const style = getComputedStyle(el);
      return rect.width > 0 && rect.height > 0 && style.display !== 'none' && style.visibility !== 'hidden';
    };
    const text = document.body.innerText || '';
    const pageSelectors = ${JSON.stringify(pageSelectors)};
    const pageRootSelector = pageSelectors.find((selector) => document.querySelector(selector));
    const pageRoot = pageRootSelector ? document.querySelector(pageRootSelector) : document.body;
    const controls = Array.from(pageRoot.querySelectorAll('button,a[href],[role="button"],input:not([type="hidden"]),select,textarea'))
      .filter(visible)
      .map((el, index) => {
        const rect = el.getBoundingClientRect();
        const label = (el.innerText || el.textContent || el.getAttribute('aria-label') || el.getAttribute('title') || el.getAttribute('placeholder') || el.value || '').replace(/\\s+/g, ' ').trim();
        el.setAttribute('data-audit-id', ${JSON.stringify(auditPrefix)} + '-' + index);
        return {
          audit_id: el.getAttribute('data-audit-id'),
          tag: el.tagName.toLowerCase(),
          role: el.getAttribute('role') || '',
          type: el.getAttribute('type') || '',
          label,
          aria: el.getAttribute('aria-label') || '',
          title: el.getAttribute('title') || '',
          disabled: Boolean(el.disabled || el.getAttribute('aria-disabled') === 'true'),
          href: el.getAttribute('href') || '',
          rect: { x: Math.round(rect.x), y: Math.round(rect.y), width: Math.round(rect.width), height: Math.round(rect.height) }
        };
      });
    const issueElements = Array.from(pageRoot.querySelectorAll('button,a,[role="button"],input,select,textarea,.lead-list-column,.lead-candidate-panel,.profile-list-column,.conversation-queue-panel,.chat-pane-v2,.service-thread-item,.lead-list-item'))
      .filter(visible)
      .map((el) => {
        const rect = el.getBoundingClientRect();
        const style = getComputedStyle(el);
        const label = (el.innerText || el.textContent || el.getAttribute('aria-label') || el.getAttribute('title') || el.getAttribute('placeholder') || '').replace(/\\s+/g, ' ').trim().slice(0, 100);
        const clippedX = el.scrollWidth > el.clientWidth + 2 && ['hidden', 'clip'].includes(style.overflowX);
        const clippedY = el.scrollHeight > el.clientHeight + 2 && ['hidden', 'clip'].includes(style.overflowY);
        const outsideX = rect.left < -1 || rect.right > innerWidth + 1;
        const aboveViewport = rect.bottom < -1;
        // Items below the viewport are expected on scrollable pages, so only
        // horizontal viewport escape and real clipped content are defects here.
        if (!clippedX && !clippedY && !outsideX && !aboveViewport) return null;
        return {
          selector: el.className || el.id || el.tagName.toLowerCase(),
          label,
          clipped_x: clippedX,
          clipped_y: clippedY,
          outside_viewport_x: outsideX,
          above_viewport: aboveViewport,
          rect: { x: Math.round(rect.x), y: Math.round(rect.y), width: Math.round(rect.width), height: Math.round(rect.height), right: Math.round(rect.right), bottom: Math.round(rect.bottom) },
          scroll: { scrollWidth: el.scrollWidth, clientWidth: el.clientWidth, scrollHeight: el.scrollHeight, clientHeight: el.clientHeight }
        };
      }).filter(Boolean);
    const scrollContainers = Array.from(pageRoot.querySelectorAll('*'))
      .filter(visible)
      .filter((el) => el.scrollHeight > el.clientHeight + 16 || el.scrollWidth > el.clientWidth + 16)
      .slice(0, 25)
      .map((el) => ({
        selector: el.className || el.id || el.tagName.toLowerCase(),
        text: (el.innerText || el.textContent || '').replace(/\\s+/g, ' ').trim().slice(0, 80),
        scrollWidth: el.scrollWidth,
        clientWidth: el.clientWidth,
        scrollHeight: el.scrollHeight,
        clientHeight: el.clientHeight,
        overflowX: getComputedStyle(el).overflowX,
        overflowY: getComputedStyle(el).overflowY
      }));
    return {
      url: location.href,
      hash: location.hash,
      text_sample: text.slice(0, 1000),
      controls,
      control_count: controls.length,
      page_scroll: { innerWidth, bodyScrollWidth: document.body.scrollWidth, docScrollWidth: document.documentElement.scrollWidth },
      has_horizontal_overflow: document.body.scrollWidth > innerWidth + 1 || document.documentElement.scrollWidth > innerWidth + 1,
      issue_elements: issueElements,
      scroll_containers: scrollContainers,
      engineering_terms: ${JSON.stringify(customerVisibleEngineeringTerms)}.filter((term) => text.includes(term)),
      confusing_terms: ${JSON.stringify(confusingTerms)}.filter((term) => text.includes(term)),
      unlabeled_icon_controls: controls.filter((item) => !item.label && !item.aria && !item.title).length
    };
  })()`);

  const clickResults = [];
  for (const control of staticResult.controls) {
    const isClickable = control.tag === "button" || control.tag === "a" || control.role === "button";
    if (!isClickable) {
      clickResults.push({ ...control, clicked: false, result: "not-click-target" });
      continue;
    }
    if (control.disabled) {
      clickResults.push({ ...control, clicked: false, result: "disabled" });
      continue;
    }
    const label = normalizeText(`${control.label} ${control.aria} ${control.title}`);
    if (riskyClickTerms.some((term) => label.includes(term))) {
      clickResults.push({ ...control, clicked: false, result: "skipped-risky" });
      continue;
    }
    const before = await evalValue(cdp, "({ hash: location.hash, text: document.body.innerText.slice(0, 4000), title: document.title })");
    const clickResult = await evalValue(cdp, `(() => {
      const el = document.querySelector('[data-audit-id="${control.audit_id}"]');
      if (!el) return { ok: false, reason: 'missing-after-page-mutation' };
      try {
        el.scrollIntoView({ block: 'center', inline: 'center' });
        el.click();
        return { ok: true, reason: 'clicked' };
      } catch (error) {
        return { ok: false, reason: String(error?.message || error) };
      }
    })()`);
    await delay(450);
    const after = await evalValue(cdp, `(() => ({
      hash: location.hash,
      text: document.body.innerText.slice(0, 4000),
      activeModal: Boolean(document.querySelector('[role="dialog"], dialog[open], .modal, .drawer')),
      visibleToast: Array.from(document.querySelectorAll('[role="status"], .toast, .inline-notice, .disabled-reason')).map((el) => (el.innerText || el.textContent || '').replace(/\\s+/g, ' ').trim()).filter(Boolean).slice(-5)
    }))()`);
    clickResults.push({
      ...control,
      clicked: clickResult.ok,
      result: clickResult.reason,
      route_before: before.hash,
      route_after: after.hash,
      text_changed: before.text !== after.text,
      active_modal: after.activeModal,
      visible_messages: after.visibleToast
    });
    if (after.hash && after.hash.split("?")[0] !== page.hash) {
      await navigateToPage(cdp, page);
    }
  }

  await capture(cdp, `${pageSlug}-after`);
  return {
    ...page,
    page_slug: pageSlug,
    screenshots: [`${pageSlug}-before.png`, `${pageSlug}-after.png`],
    static: staticResult,
    clicks: clickResults
  };
}

async function runLocalConversationSendSmoke(cdp) {
  const probeText = `本地审计回复 ${Date.now()}`;
  await navigateToPage(cdp, { hash: "#live", selector: "#workspace-live", label: "接待工作台" });
  const result = await evalValue(cdp, `(() => {
    const root = document.querySelector('#workspace-live');
    if (!root) return { ok: false, reason: 'missing-live-root' };
    const textarea = root.querySelector('textarea');
    if (!textarea) return { ok: false, reason: 'missing-reply-textarea' };
    if (textarea.disabled) return { ok: false, reason: 'reply-textarea-disabled' };
    const text = ${JSON.stringify(probeText)};
    const setter = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value').set;
    setter.call(textarea, text);
    textarea.dispatchEvent(new Event('input', { bubbles: true }));
    textarea.dispatchEvent(new Event('change', { bubbles: true }));
    const buttons = Array.from(root.querySelectorAll('button'));
    const sendButton = buttons.find((button) => (button.innerText || button.textContent || '').includes('发送到本地会话'));
    if (!sendButton) return { ok: false, reason: 'missing-local-send-button' };
    if (sendButton.disabled) return { ok: false, reason: 'local-send-button-disabled', button_title: sendButton.title || '' };
    sendButton.click();
    return { ok: true, reason: 'clicked', probe_text: text };
  })()`);
  if (!result.ok) {
    return result;
  }
  await delay(1200);
  const verified = await evalValue(cdp, `(() => {
    const text = document.querySelector('#workspace-live')?.innerText || '';
    return {
      ok: text.includes(${JSON.stringify(probeText)}) && text.includes('未发送到外部平台'),
      reason: text.includes(${JSON.stringify(probeText)}) ? 'message-visible' : 'message-not-visible',
      probe_text: ${JSON.stringify(probeText)},
      boundary_visible: text.includes('未发送到外部平台')
    };
  })()`);
  await capture(cdp, "local-send-smoke-after");
  return verified;
}

function issue(severity, page, title, evidence, recommendation) {
  return { severity, page, title, evidence, recommendation };
}

function buildIssues(results) {
  const issues = [];
  if (!results.local_send_smoke?.ok) {
    issues.push(issue(
      "P0",
      "接待工作台",
      "本地坐席回复闭环没有跑通",
      results.local_send_smoke ?? { ok: false, reason: "not-run" },
      "接待台必须允许输入回复并写入本地会话，且明确提示未发送到外部平台。"
    ));
  }
  for (const page of results.pages) {
    if (page.static.has_horizontal_overflow) {
      issues.push(issue("P1", page.label, "页面存在横向溢出", page.static.page_scroll, "收紧 grid min-width、表格滚动容器和长文本换行，桌面端也不能横向撑破。"));
    }
    if (page.static.unlabeled_icon_controls > 0) {
      issues.push(issue("P2", page.label, "存在无标签图标按钮", { count: page.static.unlabeled_icon_controls }, "图标按钮必须有 aria-label 或可见文案。"));
    }
    if (page.static.engineering_terms.length > 0) {
      issues.push(issue("P1", page.label, "客户可见工程词仍存在", page.static.engineering_terms, "客户界面改成业务语言，工程状态放内部日志或隐藏诊断。"));
    }
    if (page.static.issue_elements.length > 0) {
      issues.push(issue("P1", page.label, "存在裁切、溢出或视口外元素", page.static.issue_elements.slice(0, 8), "逐个检查被裁切元素，优先修复列表列宽、sticky 面板和按钮组。"));
    }
    const disabledWithoutReason = page.clicks.filter((item) => item.result === "disabled" && !item.title && !item.aria && !item.label.includes("禁用"));
    if (disabledWithoutReason.length > 0) {
      issues.push(issue("P2", page.label, "禁用按钮缺少明确原因", disabledWithoutReason.slice(0, 8), "禁用按钮旁必须解释缺权限、缺资料、未接渠道或外发关闭。"));
    }
  }

  const live = results.pages.find((page) => page.hash === "#live");
  if (live) {
    const saveTakeover = live.clicks.find((item) => normalizeText(item.label).includes("保存接管回复"));
    if (saveTakeover) {
      issues.push(issue(
        "P0",
        "接待工作台",
        "“保存接管回复”不是用户理解的发送动作，且缺少真正人工回复路径",
        saveTakeover,
        "改成清晰双路径：普通本地试跑显示“发送到本地会话”；真实渠道未接通时显示“保存人工回复草稿”。接入渠道后再出现“发送给客户”。"
      ));
    }
    const textarea = live.static.controls.find((item) => item.tag === "textarea");
    if (textarea?.disabled) {
      issues.push(issue(
        "P0",
        "接待工作台",
        "回复输入区经常被禁用，坐席无法主动替代 AI 回复",
        textarea,
        "接待台应允许在本地会话内输入并保存/发送人工消息；自动回复只处理普通问题，转人工或人工接管时必须可编辑。"
      ));
    }
    const localSendButton = live.static.controls.find((item) => normalizeText(item.label).includes("发送到本地会话"));
    if (!localSendButton) {
      issues.push(issue(
        "P0",
        "接待工作台",
        "缺少清晰的本地回复发送按钮",
        { controls: live.static.controls.map((item) => item.label).filter(Boolean).slice(0, 30) },
        "工作台必须显示“发送到本地会话”，真实渠道未接通前不得显示可点击的“发送给客户”。"
      ));
    }
  }

  const pilot = results.pages.find((page) => page.hash === "#pilot");
  if (pilot && pilot.static.confusing_terms.includes("试点准备")) {
    issues.push(issue(
      "P1",
      "试点准备",
      "“试点准备”概念对客户不直观",
      { text_sample: pilot.static.text_sample.slice(0, 500) },
      "改名为“本地试运行准备”或“交付准备”，首屏用一句话说明：检查资料、知识复测、质量报告、诊断备份和交付档案是否齐备。"
    ));
  }

  const contacts = results.pages.find((page) => page.hash === "#contacts");
  const leads = results.pages.find((page) => page.hash === "#leads");
  const contactLeadControlCount = (contacts?.static.control_count ?? 0) + (leads?.static.control_count ?? 0);
  if (contactLeadControlCount > 80) {
    issues.push(issue(
      "P2",
      "客户/线索",
      "客户资料与商机记录的控件仍偏多",
      {
        contacts_buttons: contacts?.static.control_count,
        leads_buttons: leads?.static.control_count
      },
      "当前阶段应继续按轻量客服资料处理，避免把客户资料页做成完整 CRM。"
    ));
  }

  return issues;
}

function writeMarkdown(results) {
  const lines = [
    "# 前端逐按钮逻辑与排版审计",
    "",
    "## 结论",
    "",
    `- 审计状态：${results.status}`,
    `- 前端地址：${frontendBaseUrl}`,
    `- 后端地址：${backendUrl}`,
    `- 覆盖页面：${results.pages.length}`,
    `- 可见控件：${results.totals.controls}`,
    `- 实际点击：${results.totals.clicked}`,
    `- 禁用控件：${results.totals.disabled}`,
    `- 风险跳过：${results.totals.skipped_risky}`,
    `- 本地坐席回复：${results.local_send_smoke?.ok ? "通过" : "未通过"}`,
    `- 问题数量：${results.issues.length}`,
    "",
    "## 高优先级问题",
    "",
    ...results.issues
      .filter((item) => ["P0", "P1"].includes(item.severity))
      .map((item, index) => `${index + 1}. **${item.severity}｜${item.page}｜${item.title}**\n   - 证据：\`${JSON.stringify(item.evidence).slice(0, 500)}\`\n   - 建议：${item.recommendation}`),
    "",
    "## 页面按钮清单摘要",
    "",
    ...results.pages.map((page) => {
      const clicked = page.clicks.filter((item) => item.clicked).length;
      const disabled = page.clicks.filter((item) => item.result === "disabled").length;
      const skipped = page.clicks.filter((item) => item.result === "skipped-risky").length;
      return `- ${page.label} ${page.hash}：控件 ${page.static.control_count}，点击 ${clicked}，禁用 ${disabled}，风险跳过 ${skipped}，截图 ${page.screenshots.map((name) => `\`${name}\``).join("、")}`;
    }),
    "",
    "## 解释",
    "",
    "- 本地试运行准备：用于看资料导入、知识复测、质量/月报、诊断备份和交付档案是否齐备，不代表正式上线。",
    "- 发送到本地会话：当前不是平台发送，只是把坐席回复写入本地会话记录；正式渠道通过前不得显示可点击的“发送给客户”。",
    "- 客户资料与商机记录：当前按轻量客服资料处理，不替代完整 CRM。",
    "",
    "## 证据文件",
    "",
    `- Summary：\`${path.relative(rootDir, path.join(outputDir, "summary.json"))}\``,
    `- Button inventory：\`${path.relative(rootDir, path.join(outputDir, "button_inventory.json"))}\``
  ];
  fs.writeFileSync(path.join(outputDir, "FRONTEND_BUTTON_LOGIC_LAYOUT_AUDIT.md"), `${lines.join("\n")}\n`, "utf-8");
}

function cleanup() {
  for (const child of children.reverse()) {
    try {
      child.kill("SIGTERM");
    } catch {
      // best-effort cleanup
    }
  }
  children.length = 0;
}

async function main() {
  fs.mkdirSync(outputDir, { recursive: true });
  await waitForHttp(`${backendUrl}/health`, 5000);
  await waitForHttp(frontendBaseUrl, 5000);
  await startChrome();
  const target = await createTarget("about:blank");
  const cdp = await createCdp(target.webSocketDebuggerUrl);
  try {
    await cdp.send("Page.enable");
    await cdp.send("Runtime.enable");
    await cdp.send("Emulation.setDeviceMetricsOverride", {
      width: 1440,
      height: 940,
      deviceScaleFactor: 1,
      mobile: false
    });
    await loginThroughUi(cdp);
    const pageResults = [];
    for (const [index, page] of pages.entries()) {
      pageResults.push(await inspectPage(cdp, page, index));
    }
    const localSendSmoke = await runLocalConversationSendSmoke(cdp);
    const runtimeErrors = cdp.events
      .filter((event) => event.method === "Runtime.exceptionThrown")
      .map((event) => event.params?.exceptionDetails?.exception?.description || event.params?.exceptionDetails?.text || "runtime error");
    const buttonInventory = pageResults.flatMap((page) =>
      page.clicks.map((item) => ({
        page: page.label,
        hash: page.hash,
        tag: item.tag,
        label: item.label,
        disabled: item.disabled,
        result: item.result,
        clicked: item.clicked,
        route_after: item.route_after,
        active_modal: item.active_modal
      }))
    );
    fs.writeFileSync(path.join(outputDir, "button_inventory.json"), JSON.stringify(buttonInventory, null, 2));
    const result = {
      schema_version: "p3-06u.frontend_button_logic_layout_audit.v1",
      status: runtimeErrors.length > 0 ? "completed_with_runtime_errors" : "completed_with_findings",
      frontend_url: frontendBaseUrl,
      backend_url: backendUrl,
      login: { tenant_slug: credentials.tenantSlug, email: credentials.email, password_redacted: true },
      pages: pageResults,
      local_send_smoke: localSendSmoke,
      runtime_errors: runtimeErrors,
      totals: {
        controls: buttonInventory.length,
        clicked: buttonInventory.filter((item) => item.clicked).length,
        disabled: buttonInventory.filter((item) => item.result === "disabled").length,
        skipped_risky: buttonInventory.filter((item) => item.result === "skipped-risky").length
      }
    };
    result.issues = buildIssues(result);
    if (result.issues.some((item) => ["P0", "P1"].includes(item.severity))) {
      result.status = "blocked_by_p0_p1";
    } else if (result.runtime_errors.length > 0) {
      result.status = "completed_with_runtime_errors";
    } else {
      result.status = "passed_without_p0_p1";
    }
    fs.writeFileSync(path.join(outputDir, "summary.json"), JSON.stringify(result, null, 2));
    writeMarkdown(result);
    console.log(`[AUDIT] ${result.status}`);
    console.log(`[AUDIT] summary=${path.join(outputDir, "summary.json")}`);
    console.log(`[AUDIT] report=${path.join(outputDir, "FRONTEND_BUTTON_LOGIC_LAYOUT_AUDIT.md")}`);
  } finally {
    cdp.close();
    await fetch(`${chromeEndpoint}/json/close/${target.id}`).catch(() => undefined);
    cleanup();
    await delay(500);
    fs.rmSync(chromeProfile, { recursive: true, force: true });
  }
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
  cleanup();
});
