import fs from "node:fs";
import path from "node:path";
import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";

const rootDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const outputDir = path.resolve(process.env.P3_06U_26H2W_FE4_OUTPUT ?? path.join(rootDir, "output/p3_06u_26h2w_fe4_customer_visible_click_qa"));
const backendPort = Number(process.env.P3_06U_26H2W_FE4_BACKEND_PORT ?? 8144);
const frontendPort = Number(process.env.P3_06U_26H2W_FE4_FRONTEND_PORT ?? 5274);
const chromePort = Number(process.env.P3_06U_26H2W_FE4_CHROME_PORT ?? 9294);
const backendUrl = `http://127.0.0.1:${backendPort}`;
const frontendBaseUrl = `http://127.0.0.1:${frontendPort}/`;
const chromeEndpoint = `http://127.0.0.1:${chromePort}`;
const dbPath = path.join(outputDir, "fe4_customer_visible_click_qa.sqlite");
const chromeProfile = path.join(outputDir, "chrome-profile");
const pythonBin = path.join(rootDir, "backend/.venv/bin/python");
const children = [];

function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function runCommand(command, args, options = {}) {
  return new Promise((resolve, reject) => {
    const child = spawn(command, args, {
      cwd: options.cwd ?? rootDir,
      env: options.env ?? process.env,
      stdio: ["ignore", "pipe", "pipe"]
    });
    let output = "";
    child.stdout.on("data", (chunk) => {
      output += chunk.toString();
    });
    child.stderr.on("data", (chunk) => {
      output += chunk.toString();
    });
    child.on("error", reject);
    child.on("close", (code) => {
      if (code === 0) resolve(output);
      else reject(new Error(`${command} ${args.join(" ")} exited ${code}\n${output}`));
    });
  });
}

function spawnLongRunning(name, command, args, options = {}) {
  const logPath = path.join(outputDir, `${name}.log`);
  const log = fs.createWriteStream(logPath, { flags: "a" });
  const child = spawn(command, args, {
    cwd: options.cwd ?? rootDir,
    env: options.env ?? process.env,
    stdio: ["ignore", "pipe", "pipe"]
  });
  children.push(child);
  child.stdout.pipe(log);
  child.stderr.pipe(log);
  return child;
}

async function waitForHttp(url, timeoutMs = 30000) {
  const started = Date.now();
  while (Date.now() - started < timeoutMs) {
    try {
      const response = await fetch(url);
      if (response.ok) return;
    } catch {
      // Keep polling until the timeout.
    }
    await delay(300);
  }
  throw new Error(`Timed out waiting for ${url}`);
}

async function startServices() {
  fs.mkdirSync(outputDir, { recursive: true });
  fs.rmSync(chromeProfile, { recursive: true, force: true });
  fs.rmSync(dbPath, { force: true });
  await runCommand(pythonBin, ["scripts/repair_local_sqlite_schema.py", "--db", dbPath], { cwd: rootDir });
  spawnLongRunning(
    "backend",
    pythonBin,
    ["-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", String(backendPort)],
    {
      cwd: path.join(rootDir, "backend"),
      env: {
        ...process.env,
        DATABASE_URL: `sqlite+pysqlite:///${dbPath}`,
        STANDARD_OPS_ENV: "development",
        STANDARD_OPS_ALLOWED_ORIGINS: `http://127.0.0.1:${frontendPort},http://localhost:${frontendPort}`,
        STANDARD_OPS_DEV_BOOTSTRAP_ENABLED: "false",
        OUTBOX_EXTERNAL_WRITE_ENABLED: "false",
        TRUSTED_INBOUND_WORKER_ENABLED: "false"
      }
    }
  );
  await waitForHttp(`${backendUrl}/health`);
  spawnLongRunning("frontend", "npm", ["run", "dev", "--", "--host", "127.0.0.1", "--port", String(frontendPort), "--strictPort"], {
    cwd: path.join(rootDir, "frontend"),
    env: { ...process.env, VITE_API_PROXY_TARGET: backendUrl }
  });
  await waitForHttp(frontendBaseUrl);
}

async function apiJson(url, options = {}) {
  const response = await fetch(`${backendUrl}${url}`, {
    ...options,
    headers: {
      "content-type": "application/json",
      ...(options.headers ?? {})
    }
  });
  const text = await response.text();
  const body = text ? JSON.parse(text) : null;
  if (!response.ok) {
    throw new Error(`API ${url} failed ${response.status}: ${text}`);
  }
  return body;
}

async function seedOwnerAndConversation() {
  const stamp = Date.now();
  const credentials = {
    tenantSlug: `fe4-owner-${stamp}`,
    tenantName: "FE4 客户可见验收空间",
    ownerName: "本地负责人",
    email: `fe4-owner-${stamp}@wanfa.local`,
    password: `FE4Owner${stamp}!`
  };
  const owner = await apiJson("/api/auth/local-setup/owner", {
    method: "POST",
    body: JSON.stringify({
      tenant_slug: credentials.tenantSlug,
      tenant_name: credentials.tenantName,
      owner_name: credentials.ownerName,
      email: credentials.email,
      password: credentials.password
    })
  });
  const token = owner.access_token;
  const tenantId = owner.user.tenant.id;
  const ownerUserId = Number(owner.user.id);
  const headers = { Authorization: `Bearer ${token}` };

  const channel = await apiJson(`/api/tenants/${tenantId}/channels`, {
    method: "POST",
    headers,
    body: JSON.stringify({
      type: "wecom_service",
      name: "企业微信客服测试通道",
      reply_mode: "draft_only",
      status: "active"
    })
  });
  const contact = await apiJson(`/api/tenants/${tenantId}/contacts`, {
    method: "POST",
    headers,
    body: JSON.stringify({ display_name: "远方好物客户" })
  });
  const conversation = await apiJson(`/api/tenants/${tenantId}/conversations`, {
    method: "POST",
    headers,
    body: JSON.stringify({
      channel_id: channel.id,
      contact_id: contact.id,
      subject: "售后一直没人处理",
      status: "handoff",
      priority: "high",
      assigned_user_id: ownerUserId
    })
  });
  const message = await apiJson(`/api/conversations/${conversation.id}/messages`, {
    method: "POST",
    headers,
    body: JSON.stringify({
      direction: "inbound",
      sender_type: "visitor",
      content: "去年的售后一直拖着不处理，你们是不是没营业了啊？"
    })
  });
  const workflow = await apiJson(`/api/conversations/${conversation.id}/workflow-runs`, {
    method: "POST",
    headers,
    body: JSON.stringify({
      trigger_message_id: message.id,
      workflow_type: "customer_reply",
      current_step: "human_review",
      state_payload: { source: "fe4_customer_visible_click_qa", confidence: 0.38 }
    })
  });
  const review = await apiJson(`/api/workflow-runs/${workflow.id}/human-review-tasks`, {
    method: "POST",
    headers,
    body: JSON.stringify({
      reason: "low_confidence_after_sales",
      risk_level: "high",
      draft_reply: "您好，我先帮您核对售后记录。涉及历史订单处理时效，需要人工确认后再给您准确答复。"
    })
  });

  return { credentials, tenantId, channel, contact, conversation, message, workflow, review };
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

async function startChrome() {
  fs.mkdirSync(chromeProfile, { recursive: true });
  spawnLongRunning(
    "chrome",
    chromeBinary(),
    [
      `--remote-debugging-port=${chromePort}`,
      `--user-data-dir=${chromeProfile}`,
      "--headless=new",
      "--disable-gpu",
      "--no-first-run",
      "--no-default-browser-check",
      "about:blank"
    ],
    { cwd: rootDir }
  );
  await waitForHttp(`${chromeEndpoint}/json/version`);
}

async function createTarget(url) {
  const response = await fetch(`${chromeEndpoint}/json/new?${encodeURIComponent(url)}`, { method: "PUT" });
  if (!response.ok) throw new Error(`Failed to create Chrome target: ${response.status}`);
  return response.json();
}

function createCdp(wsUrl) {
  const ws = new WebSocket(wsUrl);
  let id = 0;
  const pending = new Map();
  const events = [];
  return new Promise((resolve, reject) => {
    ws.addEventListener("message", (event) => {
      const msg = JSON.parse(event.data);
      if (msg.id && pending.has(msg.id)) {
        const waiter = pending.get(msg.id);
        pending.delete(msg.id);
        if (msg.error) waiter.reject(new Error(JSON.stringify(msg.error)));
        else waiter.resolve(msg.result || {});
        return;
      }
      if (msg.method) events.push(msg);
    });
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

async function waitForExpression(cdp, expression, timeoutMs = 20000) {
  const started = Date.now();
  while (Date.now() - started < timeoutMs) {
    const value = await evalValue(cdp, expression);
    if (value) return value;
    await delay(250);
  }
  throw new Error(`Timed out waiting for expression: ${expression}`);
}

function withHash(hash) {
  return `${frontendBaseUrl.replace(/#.*$/, "")}${hash}`;
}

async function navigate(cdp, hash) {
  await cdp.send("Page.navigate", { url: withHash(hash) });
  await delay(800);
}

async function capture(cdp, name) {
  const screenshot = await cdp.send("Page.captureScreenshot", {
    format: "png",
    fromSurface: true,
    captureBeyondViewport: false
  });
  fs.writeFileSync(path.join(outputDir, `${name}.png`), Buffer.from(screenshot.data, "base64"));
}

function assertCheck(condition, message, details) {
  if (!condition) {
    throw new Error(`${message}${details ? `: ${JSON.stringify(details)}` : ""}`);
  }
}

async function loginThroughUi(cdp, credentials) {
  await cdp.send("Page.navigate", { url: frontendBaseUrl });
  await waitForExpression(cdp, "Boolean(document.querySelector('[data-role-smoke=\"login-form\"]'))");
  await evalValue(cdp, `(() => {
    const setInput = (selector, value) => {
      const input = document.querySelector(selector);
      if (!input) throw new Error('missing input ' + selector);
      const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;
      setter.call(input, value);
      input.dispatchEvent(new Event('input', { bubbles: true }));
      input.dispatchEvent(new Event('change', { bubbles: true }));
    };
    setInput('[data-role-smoke="tenant-slug"]', ${JSON.stringify(credentials.tenantSlug)});
    setInput('[data-role-smoke="email"]', ${JSON.stringify(credentials.email)});
    setInput('[data-role-smoke="password"]', ${JSON.stringify(credentials.password)});
    document.querySelector('[data-role-smoke="login-form"]').requestSubmit();
    return true;
  })()`);
  await waitForExpression(cdp, "Boolean(document.querySelector('#workspace-overview')) && !document.querySelector('[data-role-smoke=\"login-form\"]')", 20000);
  return evalValue(cdp, `(() => ({
    hash: location.hash,
    hasLoginForm: Boolean(document.querySelector('[data-role-smoke="login-form"]')),
    hasOverview: Boolean(document.querySelector('#workspace-overview')),
    bodyIncludesTenantName: document.body.innerText.includes(${JSON.stringify(credentials.tenantName)})
  }))()`);
}

async function inspectLivePage(cdp) {
  await navigate(cdp, "#live");
  await waitForExpression(cdp, "Boolean(document.querySelector('#workspace-live'))");
  await delay(900);
  return evalValue(cdp, `(() => {
    const text = document.body.innerText;
    const clickQueue = (label) => {
      const button = Array.from(document.querySelectorAll('.service-queue-filter button')).find((item) => item.textContent?.includes(label));
      button?.click();
      return Boolean(button);
    };
    const hasAll = clickQueue('全部');
    const hasMine = clickQueue('我的');
    const hasHandoff = clickQueue('转人工');
    const search = document.querySelector('.service-list-search input');
    if (search) {
      const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;
      setter.call(search, '远方');
      search.dispatchEvent(new Event('input', { bubbles: true }));
      search.dispatchEvent(new Event('change', { bubbles: true }));
    }
    const sidebarText = document.querySelector('.sidebar')?.innerText || '';
    return {
      hasLive: Boolean(document.querySelector('#workspace-live')),
      hasNoFakeHeaderActions: document.querySelectorAll('.chat-head-action').length === 0,
      hasNoFakeComposerTools: document.querySelectorAll('.composer-tool-button').length === 0,
      hasRealityMarker: Boolean(document.querySelector('[data-function-reality="no-fake-chat-actions"]')),
      hasSearch: Boolean(search),
      hasQueueTabs: hasAll && hasMine && hasHandoff,
      hasSeedConversation: text.includes('远方好物') || text.includes('售后一直没人处理'),
      hasCustomerMessage: text.includes('去年的售后一直拖着不处理'),
      hasSafeReplyButton: Boolean(Array.from(document.querySelectorAll('button')).find((button) => button.textContent?.includes('保存接管回复'))),
      hasHiddenBackendItemsInSidebar: ['会话收件箱', '人工审核', '待发送草稿', '工单/SLA'].some((item) => sidebarText.includes(item)),
      hasBannedCopy: ['历史记录', '设为星标', '发送图片', '添加附件', '已自动发送', '已接通全渠道', '已完成线上准确率', '已上传云端', '已正式签收', 'AI自主回复预备', 'AI 自主回复预备'].some((item) => text.includes(item)),
      hasExternalSendCopy: text.includes('真实外发已开启') || text.includes('已发到微信') || text.includes('已发到抖音'),
      hasHorizontalOverflow: document.documentElement.scrollWidth > innerWidth || document.body.scrollWidth > innerWidth
    };
  })()`);
}

async function inspectPages(cdp) {
  const pageChecks = [
    { hash: "#overview", selector: "#workspace-overview", label: "运营总览", requiredText: "渠道筛选" },
    { hash: "#quality", selector: "#workspace-quality", label: "质量复盘", requiredText: "质量" },
    { hash: "#knowledge", selector: "#workspace-knowledge", label: "知识库运营", requiredText: "业务对象" },
    { hash: "#gaps", selector: "#workspace-knowledge-gaps", label: "知识缺口", requiredText: "知识缺口" },
    { hash: "#evals", selector: "#workspace-evals", label: "知识评测", requiredText: "知识评测" },
    { hash: "#channels", selector: ".channel-layer-tabs", label: "渠道接入", requiredText: "真实外发" },
    { hash: "#ops", selector: "#workspace-ops", label: "运维与告警", requiredText: "告警" },
    { hash: "#model", selector: "#workspace-model", label: "模型路由", requiredText: "模型" },
    { hash: "#settings", selector: "#workspace-settings", label: "账号与本地维护", requiredText: "账号" }
  ];
  const results = [];
  for (const page of pageChecks) {
    await navigate(cdp, page.hash);
    await waitForExpression(cdp, `Boolean(document.querySelector(${JSON.stringify(page.selector)}))`);
    const result = await evalValue(cdp, `(() => {
      const text = document.body.innerText;
      const buttons = Array.from(document.querySelectorAll('button')).filter((button) => {
        const rect = button.getBoundingClientRect();
        return rect.width > 0 && rect.height > 0 && getComputedStyle(button).visibility !== 'hidden';
      });
      return {
        hash: location.hash,
        selectorPresent: Boolean(document.querySelector(${JSON.stringify(page.selector)})),
        hasRequiredText: text.includes(${JSON.stringify(page.requiredText)}),
        hasLoginForm: Boolean(document.querySelector('[data-role-smoke="login-form"]')),
        unlabeledButtonCount: buttons.filter((button) => !(button.textContent || '').trim() && !button.getAttribute('aria-label') && !button.getAttribute('title')).length,
        hasEngineeringTerm: ['Provider：', 'H2W7 门禁', 'connector_noop'].some((item) => text.includes(item)),
        hasOverclaim: ['已自动发送', '已接通全渠道', '已完成线上准确率', '已上传云端', '已正式签收', '真实外发已开启'].some((item) => text.includes(item)),
        hasHorizontalOverflow: document.documentElement.scrollWidth > innerWidth || document.body.scrollWidth > innerWidth
      };
    })()`);
    assertCheck(result.selectorPresent && result.hasRequiredText, `${page.label} page missing required content`, result);
    assertCheck(!result.hasLoginForm, `${page.label} unexpectedly returned to login`, result);
    assertCheck(result.unlabeledButtonCount === 0, `${page.label} has unlabeled visible buttons`, result);
    assertCheck(!result.hasEngineeringTerm, `${page.label} contains customer-visible engineering term`, result);
    assertCheck(!result.hasOverclaim, `${page.label} contains overclaim copy`, result);
    assertCheck(!result.hasHorizontalOverflow, `${page.label} has horizontal overflow`, result);
    results.push({ label: page.label, ...result });
  }
  return results;
}

async function runBrowserSmoke(seed) {
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
    const login = await loginThroughUi(cdp, seed.credentials);
    assertCheck(login.hasOverview && !login.hasLoginForm, "owner login did not enter authenticated workspace", login);

    const live = await inspectLivePage(cdp);
    assertCheck(live.hasNoFakeHeaderActions, "live page still exposes fake header actions", live);
    assertCheck(live.hasNoFakeComposerTools, "live page still exposes fake composer tool buttons", live);
    assertCheck(live.hasRealityMarker, "live page missing function-reality marker", live);
    assertCheck(live.hasSearch && live.hasQueueTabs && live.hasSafeReplyButton, "live page missing required controls", live);
    assertCheck(live.hasSeedConversation && live.hasCustomerMessage, "live page did not render seeded backend conversation", live);
    assertCheck(!live.hasHiddenBackendItemsInSidebar, "sidebar exposes hidden backend workbench items", live);
    assertCheck(!live.hasBannedCopy && !live.hasExternalSendCopy, "live page contains banned or overclaim copy", live);
    assertCheck(!live.hasHorizontalOverflow, "live page has horizontal overflow", live);
    await capture(cdp, "fe4-live-workbench");

    const pages = await inspectPages(cdp);
    await capture(cdp, "fe4-settings-final");
    const runtimeErrors = cdp.events
      .filter((event) => event.method === "Runtime.exceptionThrown")
      .map((event) => event.params?.exceptionDetails?.exception?.description || event.params?.exceptionDetails?.text || "runtime error");
    assertCheck(runtimeErrors.length === 0, "runtime errors occurred in FE4 browser QA", runtimeErrors);
    return { login, live, pages, runtimeErrors };
  } finally {
    cdp.close();
    await fetch(`${chromeEndpoint}/json/close/${target.id}`).catch(() => undefined);
  }
}

function cleanup() {
  for (const child of children.reverse()) {
    try {
      child.kill("SIGTERM");
    } catch {
      // Best-effort cleanup for local smoke processes.
    }
  }
  children.length = 0;
}

async function main() {
  fs.mkdirSync(outputDir, { recursive: true });
  await startServices();
  const seed = await seedOwnerAndConversation();
  const browser = await runBrowserSmoke(seed);
  const summaryPath = path.join(outputDir, "summary.json");
  fs.writeFileSync(
    summaryPath,
    JSON.stringify(
      {
        phase: "H2W-FE4",
        status: "passed_customer_visible_click_qa",
        ok: true,
        frontendUrl: frontendBaseUrl,
        backendUrl,
        tenant_id: seed.tenantId,
        channel_id: seed.channel.id,
        conversation_id: seed.conversation.id,
        message_id: seed.message.id,
        workflow_run_id: seed.workflow.id,
        human_review_task_id: seed.review.id,
        owner_login_performed_through_ui: true,
        demo_mode_used: false,
        external_platform_write_performed: false,
        real_platform_send_performed: false,
        model_call_performed: false,
        formal_customer_signoff_performed: false,
        browser
      },
      null,
      2
    )
  );
  console.log(`[PASS] H2W-FE4 customer-visible browser click QA passed: ${summaryPath}`);
}

main()
  .catch((error) => {
    console.error(error);
    process.exitCode = 1;
  })
  .finally(async () => {
    cleanup();
    await delay(500);
    fs.rmSync(chromeProfile, { recursive: true, force: true });
    fs.rmSync(dbPath, { force: true });
  });
