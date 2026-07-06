import fs from "node:fs";
import path from "node:path";
import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";

const rootDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const outputDir = path.resolve(
  process.env.P3_06U_26H2W_FE6_OUTPUT ?? path.join(rootDir, "output/p3_06u_26h2w_fe6_latest_frontend_browser_qa")
);
const docPath = path.join(rootDir, "docs/P3-06U-26H2W_FE6_LATEST_FRONTEND_BROWSER_QA.md");
const backendPort = Number(process.env.P3_06U_26H2W_FE6_BACKEND_PORT ?? 8166);
const frontendPort = Number(process.env.P3_06U_26H2W_FE6_FRONTEND_PORT ?? 5296);
const chromePort = Number(process.env.P3_06U_26H2W_FE6_CHROME_PORT ?? 9316);
const backendUrl = `http://127.0.0.1:${backendPort}`;
const frontendBaseUrl = `http://127.0.0.1:${frontendPort}/`;
const chromeEndpoint = `http://127.0.0.1:${chromePort}`;
const dbPath = path.join(outputDir, "fe6_latest_frontend_browser_qa.sqlite");
const chromeProfile = path.join(outputDir, "chrome-profile");
const pythonBin = path.join(rootDir, "backend/.venv/bin/python");
const children = [];

const requiredPages = [
  { hash: "#overview", selector: "#workspace-overview", label: "总览", required: ["运营", "渠道"] },
  { hash: "#live", selector: "#workspace-live", label: "接待工作台", required: ["转人工", "客户"] },
  { hash: "#knowledge", selector: "#workspace-knowledge", label: "知识库运营", required: ["业务对象", "标准问答", "导入"] },
  { hash: "#gaps", selector: "[data-knowledge-page-shell=\"gaps\"]", label: "知识缺口", required: ["知识缺口", "错因"] },
  { hash: "#evals", selector: "[data-knowledge-page-shell=\"evals\"]", label: "知识评测", required: ["知识评测", "完整客服事实准确率"] },
  { hash: "#quality", selector: "#workspace-quality", label: "质量复盘", required: ["质量", "月度"] },
  { hash: "#channels", selector: "#workspace-channels", label: "渠道接入", required: ["渠道", "官方"] },
  { hash: "#ops", selector: "#workspace-ops", label: "运维与告警", required: ["运维", "告警"] },
  { hash: "#model", selector: "#workspace-model", label: "自动回复策略", required: ["自动回复", "成本"] },
  { hash: "#settings", selector: "#workspace-settings", label: "账号与本地维护", required: ["诊断", "备份", "更新"] },
  { hash: "#pilot", selector: "#workspace-pilot", label: "试点准备", required: ["试点准备", "客户确认", "不代表正式客户验收"] }
];

const bannedVisibleTerms = ["H2W", "P3-", "dry-run", "provider", "outbox", "sandbox", "connector_noop"];
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
    tenantSlug: `fe6-owner-${stamp}`,
    tenantName: "FE6 最新前端验收空间",
    ownerName: "本地负责人",
    email: `fe6-owner-${stamp}@wanfa.local`,
    password: `FE6Owner${stamp}!`
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
      title: button.getAttribute('title') || '',
      type: button.getAttribute('type') || ''
    }));
    const links = Array.from(document.querySelectorAll('a[href^="#"]')).slice(0, 12).map((link) => ({
      text: (link.textContent || '').replace(/\\s+/g, ' ').trim(),
      href: link.getAttribute('href') || ''
    }));
    return {
      hash: location.hash,
      text,
      requiredPresent: ${JSON.stringify(page.required)}.every((item) => text.includes(item)),
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
  assertCheck(result.requiredPresent, `${page.label} missing required text`, result);
  assertCheck(result.bannedVisibleTerms.length === 0, `${page.label} contains customer-visible engineering terms`, result.bannedVisibleSnippets);
  assertCheck(result.overclaims.length === 0, `${page.label} contains overclaim phrases`, result.overclaims);
  assertCheck(!result.hasHorizontalOverflow, `${page.label} has horizontal overflow`, result);
  assertCheck(result.emptyIconOnlyButtons === 0, `${page.label} contains unlabeled icon-only buttons`, result.visibleButtons);
  await capture(cdp, `fe6-${String(index + 1).padStart(2, "0")}-${page.hash.slice(1)}`);
  return {
    hash: page.hash,
    label: page.label,
    selector: page.selector,
    required_present: result.requiredPresent,
    button_count: result.visibleButtons.length,
    link_count: result.links.length,
    customer_visible_engineering_terms: result.bannedVisibleTerms,
    overclaims: result.overclaims,
    horizontal_overflow: result.hasHorizontalOverflow,
    screenshot: `fe6-${String(index + 1).padStart(2, "0")}-${page.hash.slice(1)}.png`
  };
}

async function inspectPilotStepLinks(cdp) {
  await navigate(cdp, "#pilot");
  await waitForExpression(cdp, "Boolean(document.querySelector('#workspace-pilot'))");
  const links = await evalValue(cdp, `Array.from(document.querySelectorAll('.pilot-step-card a')).map((link) => ({
    text: link.textContent?.trim() || '',
    href: link.getAttribute('href') || ''
  }))`);
  assertCheck(links.length === 6, "pilot page must expose six step links", links);
  const clicked = [];
  for (const link of links) {
    await navigate(cdp, "#pilot");
    await waitForExpression(cdp, "Boolean(document.querySelector('#workspace-pilot'))");
    await evalValue(cdp, `(() => {
      const link = Array.from(document.querySelectorAll('.pilot-step-card a')).find((item) => item.getAttribute('href') === ${JSON.stringify(link.href)});
      link?.click();
      return Boolean(link);
    })()`);
    await delay(700);
    const actual = await evalValue(cdp, "location.hash");
    clicked.push({ text: link.text, expected: link.href, actual });
    assertCheck(actual.startsWith(link.href), "pilot step did not navigate to its real target", { link, actual });
  }
  return clicked;
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
    const pilotStepClicks = await inspectPilotStepLinks(cdp);
    const runtimeErrors = cdp.events
      .filter((event) => event.method === "Runtime.exceptionThrown")
      .map((event) => event.params?.exceptionDetails?.exception?.description || event.params?.exceptionDetails?.text || "runtime error");
    assertCheck(runtimeErrors.length === 0, "runtime errors occurred in FE6 browser QA", runtimeErrors);
    return { pages, pilot_step_clicks: pilotStepClicks, runtime_errors: runtimeErrors };
  } finally {
    cdp.close();
    await fetch(`${chromeEndpoint}/json/close/${target.id}`).catch(() => undefined);
  }
}

function writeMarkdown(result) {
  const lines = [
    "# H2W-FE6 最新前端浏览器复测",
    "",
    "## 结论",
    "",
    `- 阶段状态：\`${result.status}\``,
    `- 真实登录：\`${String(result.owner_login_performed_through_ui)}\``,
    `- 覆盖页面：\`${result.browser.pages.length}\``,
    `- 试点准备六步点击：\`${result.browser.pilot_step_clicks.length}\``,
    "",
    "## 覆盖页面",
    "",
    ...result.browser.pages.map((page) => `- ${page.label}：${page.hash}，按钮 ${page.button_count} 个，截图 \`${page.screenshot}\``),
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
    schema_version: "p3-06u-26h2w-fe6.latest_frontend_browser_qa.v1",
    phase: "H2W-FE6",
    status: "passed_latest_frontend_browser_qa",
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
  console.log(`[PASS] H2W-FE6 latest frontend browser QA passed: ${path.join(outputDir, "summary.json")}`);
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
