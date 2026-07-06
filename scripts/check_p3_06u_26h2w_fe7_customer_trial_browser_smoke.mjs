import fs from "node:fs";
import path from "node:path";
import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";

const rootDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const outputDir = path.resolve(
  process.env.P3_06U_26H2W_FE7_OUTPUT ?? path.join(rootDir, "output/p3_06u_26h2w_fe7_customer_trial_browser_smoke")
);
const docPath = path.join(rootDir, "docs/P3-06U-26H2W_FE7_CUSTOMER_TRIAL_BROWSER_SMOKE.md");
const backendPort = Number(process.env.P3_06U_26H2W_FE7_BACKEND_PORT ?? 8177);
const frontendPort = Number(process.env.P3_06U_26H2W_FE7_FRONTEND_PORT ?? 5307);
const chromePort = Number(process.env.P3_06U_26H2W_FE7_CHROME_PORT ?? 9327);
const backendUrl = `http://127.0.0.1:${backendPort}`;
const frontendBaseUrl = `http://127.0.0.1:${frontendPort}/`;
const chromeEndpoint = `http://127.0.0.1:${chromePort}`;
const dbPath = path.join(outputDir, "fe7_customer_trial_browser_smoke.sqlite");
const chromeProfile = path.join(outputDir, "chrome-profile");
const pythonBin = path.join(rootDir, "backend/.venv/bin/python");
const children = [];

const requiredPages = [
  { hash: "#pilot", selector: "#workspace-pilot", label: "试点准备", required: ["试点准备", "试跑封版证据", "交付档案"] },
  { hash: "#knowledge", selector: "#workspace-knowledge", label: "知识中心", required: ["客户知识中心", "导入资料", "预检", "发布", "复测", "确认", "质量报告"] },
  { hash: "#quality", selector: "#workspace-quality", label: "质量复盘", required: ["质量", "月度"] },
  { hash: "#settings", selector: "#workspace-settings", label: "账号与本地维护", required: ["账号与本地维护", "诊断", "备份", "更新"] }
];

const bannedVisibleTerms = ["H2W", "P3-", "dry-run", "provider", "outbox", "sandbox", "rehearsal"];
const overclaimPhrases = [
  "正式客户验收已完成",
  "已正式签收",
  "真实外发已开启",
  "全渠道已接通",
  "签名安装包已完成",
  "生产 SLA 已完成"
];

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
  const log = fs.createWriteStream(path.join(outputDir, `${name}.log`), { flags: "a" });
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
      // Keep polling.
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
    headers: { "content-type": "application/json", ...(options.headers ?? {}) }
  });
  const text = await response.text();
  const body = text ? JSON.parse(text) : null;
  if (!response.ok) throw new Error(`API ${url} failed ${response.status}: ${text}`);
  return body;
}

async function seedOwner() {
  const stamp = Date.now();
  const credentials = {
    tenantSlug: `fe7-owner-${stamp}`,
    tenantName: "FE7 客户试跑空间",
    ownerName: "本地负责人",
    email: `fe7-owner-${stamp}@wanfa.local`,
    password: `FE7Owner${stamp}!`
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
  return { credentials, owner, tenantId: owner.user.tenant.id };
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
  const result = await cdp.send("Runtime.evaluate", { awaitPromise: true, returnByValue: true, expression });
  if (result.exceptionDetails) throw new Error(JSON.stringify(result.exceptionDetails));
  return result.result.value;
}

async function waitForExpression(cdp, expression, timeoutMs = 25000) {
  const started = Date.now();
  while (Date.now() - started < timeoutMs) {
    const value = await evalValue(cdp, expression);
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

function assertCheck(condition, message, details) {
  if (!condition) throw new Error(`${message}${details ? `: ${JSON.stringify(details)}` : ""}`);
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
  await waitForExpression(cdp, "Boolean(document.querySelector('#workspace-overview')) && !document.querySelector('[data-role-smoke=\"login-form\"]')", 25000);
}

function withHash(hash) {
  return `${frontendBaseUrl.replace(/#.*$/, "")}${hash}`;
}

async function navigate(cdp, hash) {
  await cdp.send("Page.navigate", { url: withHash(hash) });
  await delay(950);
}

async function inspectPage(cdp, page, index) {
  await navigate(cdp, page.hash);
  await waitForExpression(cdp, `Boolean(document.querySelector(${JSON.stringify(page.selector)}))`);
  const result = await evalValue(cdp, `(() => {
    const text = document.body.innerText;
    const visibleButtons = Array.from(document.querySelectorAll('button')).filter((button) => {
      const rect = button.getBoundingClientRect();
      const style = getComputedStyle(button);
      return rect.width > 0 && rect.height > 0 && style.visibility !== 'hidden' && style.display !== 'none';
    }).map((button) => ({
      text: (button.textContent || '').replace(/\\s+/g, ' ').trim(),
      disabled: button.disabled,
      aria: button.getAttribute('aria-label') || '',
      title: button.getAttribute('title') || ''
    }));
    const links = Array.from(document.querySelectorAll('a[href^="#"]')).map((link) => ({
      text: (link.textContent || '').replace(/\\s+/g, ' ').trim(),
      href: link.getAttribute('href') || ''
    }));
    return {
      hash: location.hash,
      text,
      requiredPresent: ${JSON.stringify(page.required)}.every((item) => text.includes(item)),
      missingRequired: ${JSON.stringify(page.required)}.filter((item) => !text.includes(item)),
      bannedVisibleTerms: ${JSON.stringify(bannedVisibleTerms)}.filter((item) => text.includes(item)),
      bannedVisibleSnippets: Object.fromEntries(${JSON.stringify(bannedVisibleTerms)}.filter((item) => text.includes(item)).map((item) => {
        const index = text.indexOf(item);
        return [item, text.slice(Math.max(0, index - 60), Math.min(text.length, index + item.length + 80))];
      })),
      overclaims: ${JSON.stringify(overclaimPhrases)}.filter((item) => text.includes(item)),
      hasHorizontalOverflow: document.documentElement.scrollWidth > innerWidth || document.body.scrollWidth > innerWidth,
      visibleButtons,
      links,
      emptyIconOnlyButtons: visibleButtons.filter((button) => !button.text && !button.aria && !button.title).length
    };
  })()`);
  assertCheck(result.requiredPresent, `${page.label} missing required text`, result.missingRequired);
  assertCheck(result.bannedVisibleTerms.length === 0, `${page.label} contains customer-visible engineering terms`, result.bannedVisibleSnippets);
  assertCheck(result.overclaims.length === 0, `${page.label} contains overclaim phrases`, result.overclaims);
  assertCheck(!result.hasHorizontalOverflow, `${page.label} has horizontal overflow`, result);
  assertCheck(result.emptyIconOnlyButtons === 0, `${page.label} contains unlabeled icon-only buttons`, result.visibleButtons);
  await capture(cdp, `fe7-${String(index + 1).padStart(2, "0")}-${page.hash.slice(1)}`);
  return {
    hash: page.hash,
    label: page.label,
    required_present: result.requiredPresent,
    button_count: result.visibleButtons.length,
    disabled_button_count: result.visibleButtons.filter((button) => button.disabled).length,
    link_count: result.links.length,
    customer_visible_engineering_terms: result.bannedVisibleTerms,
    overclaims: result.overclaims,
    horizontal_overflow: result.hasHorizontalOverflow,
    screenshot: `fe7-${String(index + 1).padStart(2, "0")}-${page.hash.slice(1)}.png`
  };
}

async function clickSafeCustomerPath(cdp) {
  const actions = [];
  await navigate(cdp, "#pilot");
  await evalValue(cdp, `(() => {
    const button = Array.from(document.querySelectorAll('button')).find((item) => item.textContent?.includes('刷新状态'));
    button?.click();
    return Boolean(button);
  })()`);
  actions.push({ page: "#pilot", action: "刷新状态" });
  await delay(600);

  await navigate(cdp, "#knowledge");
  const knowledgeAction = await evalValue(cdp, `(() => {
    const button = Array.from(document.querySelectorAll('button')).find((item) => item.textContent?.includes('生成资料包'));
    if (button && !button.disabled) {
      button.click();
      return 'clicked';
    }
    return button ? 'disabled' : 'missing';
  })()`);
  actions.push({ page: "#knowledge", action: "生成资料包", result: knowledgeAction });
  await delay(600);

  await navigate(cdp, "#settings");
  const settingLinks = await evalValue(cdp, `Array.from(document.querySelectorAll('a[href="#pilot"], a[href="#monthly-ops-report"]')).map((link) => link.textContent?.trim() || '')`);
  actions.push({ page: "#settings", action: "检查维护入口", result: settingLinks });
  return actions;
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
    await loginThroughUi(cdp, seed.credentials);
    const pages = [];
    for (const [index, page] of requiredPages.entries()) {
      pages.push(await inspectPage(cdp, page, index));
    }
    const customerPathActions = await clickSafeCustomerPath(cdp);
    const runtimeErrors = cdp.events
      .filter((event) => event.method === "Runtime.exceptionThrown")
      .map((event) => event.params?.exceptionDetails?.exception?.description || event.params?.exceptionDetails?.text || "runtime error");
    assertCheck(runtimeErrors.length === 0, "runtime errors occurred in FE7 browser smoke", runtimeErrors);
    return { pages, customer_path_actions: customerPathActions, runtime_errors: runtimeErrors };
  } finally {
    cdp.close();
    await fetch(`${chromeEndpoint}/json/close/${target.id}`).catch(() => undefined);
  }
}

function writeMarkdown(result) {
  const lines = [
    "# H2W-FE7 客户视角端到端前端试跑",
    "",
    "## 结论",
    "",
    `- 阶段状态：\`${result.status}\``,
    `- 真实登录：\`${String(result.owner_login_performed_through_ui)}\``,
    `- 覆盖页面：\`${result.browser.pages.length}\``,
    "",
    "## 覆盖页面",
    "",
    ...result.browser.pages.map((page) => `- ${page.label}：${page.hash}，按钮 ${page.button_count} 个，截图 \`${page.screenshot}\``),
    "",
    "## 点击动作",
    "",
    ...result.browser.customer_path_actions.map((item) => `- ${item.page}：${item.action}`),
    "",
    "## 边界",
    "",
    "- 不做移动端。",
    "- 不启用真实外发。",
    "- 不把内部演练写成客户正式签收。",
    "- 不把安装器候选写成已签名 dmg/exe。",
    "",
    "## 证据",
    "",
    `- Summary：${path.relative(rootDir, path.join(outputDir, "summary.json"))}`
  ];
  fs.writeFileSync(docPath, `${lines.join("\n")}\n`, "utf-8");
}

function cleanup() {
  for (const child of children.reverse()) {
    try {
      child.kill("SIGTERM");
    } catch {
      // Best-effort cleanup.
    }
  }
  children.length = 0;
}

async function main() {
  fs.mkdirSync(outputDir, { recursive: true });
  await startServices();
  const seed = await seedOwner();
  const browser = await runBrowserSmoke(seed);
  const result = {
    schema_version: "p3-06u-26h2w-fe7.customer_trial_browser_smoke.v1",
    phase: "H2W-FE7",
    status: "passed_customer_trial_browser_smoke",
    ok: true,
    frontend_url: frontendBaseUrl,
    backend_url: backendUrl,
    tenant_id: seed.tenantId,
    owner_login_performed_through_ui: true,
    demo_mode_used: false,
    external_platform_write_performed: false,
    real_platform_send_performed: false,
    formal_customer_signoff_performed: false,
    signed_dmg_exe_ready: false,
    mobile_scope_included: false,
    browser
  };
  fs.writeFileSync(path.join(outputDir, "summary.json"), JSON.stringify(result, null, 2));
  writeMarkdown(result);
  console.log(`[PASS] H2W-FE7 customer trial browser smoke passed: ${path.join(outputDir, "summary.json")}`);
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
