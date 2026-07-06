import fs from "node:fs";
import path from "node:path";
import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";

const rootDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const outputDir = path.resolve(
  process.env.P3_06U_26H2W_PILOT4_OUTPUT ?? path.join(rootDir, "output/p3_06u_26h2w_pilot4_customer_trial_rehearsal")
);
const docPath = path.join(rootDir, "docs/P3-06U-26H2W_PILOT4_CUSTOMER_TRIAL_REHEARSAL.md");
const backendPort = Number(process.env.P3_06U_26H2W_PILOT4_BACKEND_PORT ?? 8154);
const frontendPort = Number(process.env.P3_06U_26H2W_PILOT4_FRONTEND_PORT ?? 5284);
const chromePort = Number(process.env.P3_06U_26H2W_PILOT4_CHROME_PORT ?? 9304);
const backendUrl = `http://127.0.0.1:${backendPort}`;
const frontendBaseUrl = `http://127.0.0.1:${frontendPort}/`;
const chromeEndpoint = `http://127.0.0.1:${chromePort}`;
const dbPath = path.join(outputDir, "pilot4_customer_trial_rehearsal.sqlite");
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

async function seedOwner() {
  const stamp = Date.now();
  const credentials = {
    tenantSlug: `pilot4-owner-${stamp}`,
    tenantName: "PILOT4 本地试点演练空间",
    ownerName: "本地负责人",
    email: `pilot4-owner-${stamp}@wanfa.local`,
    password: `Pilot4Owner${stamp}!`
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
  const result = await cdp.send("Runtime.evaluate", {
    awaitPromise: true,
    returnByValue: true,
    expression
  });
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

function withHash(hash) {
  return `${frontendBaseUrl.replace(/#.*$/, "")}${hash}`;
}

async function navigate(cdp, hash) {
  await cdp.send("Page.navigate", { url: withHash(hash) });
  await delay(900);
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
  await waitForExpression(cdp, "Boolean(document.querySelector('#workspace-overview')) && !document.querySelector('[data-role-smoke=\"login-form\"]')", 25000);
}

async function inspectPilotPage(cdp) {
  await navigate(cdp, "#pilot");
  await waitForExpression(cdp, "Boolean(document.querySelector('#workspace-pilot'))");
  await evalValue(cdp, `(() => {
    const refresh = Array.from(document.querySelectorAll('button')).find((button) => button.textContent?.includes('刷新状态'));
    refresh?.click();
    return Boolean(refresh);
  })()`);
  await delay(800);
  const page = await evalValue(cdp, `(() => {
    const text = document.body.innerText;
    const stepLinks = Array.from(document.querySelectorAll('.pilot-step-card a')).map((link) => ({
      text: link.textContent?.trim() || '',
      href: link.getAttribute('href') || ''
    }));
    return {
      hasPilotPage: Boolean(document.querySelector('#workspace-pilot')),
      hasSixSteps: document.querySelectorAll('.pilot-step-card').length === 6,
      stepLinks,
      hasWaitingConfirmation: text.includes('等待客户确认表') || text.includes('待确认'),
      hasNoFormalSignoff: text.includes('不代表正式客户验收') || text.includes('不会标记为已确认'),
      hasBannedEngineeringTerm: ['H2W', 'P3-', 'dry-run', 'provider', 'outbox', 'sandbox'].some((item) => text.includes(item)),
      hasOverclaim: ['已正式签收', '正式客户验收已完成', '真实外发已开启', '签名安装包已完成'].some((item) => text.includes(item)),
      hasHorizontalOverflow: document.documentElement.scrollWidth > innerWidth || document.body.scrollWidth > innerWidth
    };
  })()`);
  assertCheck(page.hasSixSteps, "pilot page does not show six preparation steps", page);
  assertCheck(page.hasWaitingConfirmation && page.hasNoFormalSignoff, "pilot page missing confirmation boundary copy", page);
  assertCheck(!page.hasBannedEngineeringTerm && !page.hasOverclaim, "pilot page contains engineering terms or overclaims", page);
  assertCheck(!page.hasHorizontalOverflow, "pilot page has horizontal overflow", page);
  await capture(cdp, "pilot4-preparation");

  const clicked = [];
  for (const link of page.stepLinks) {
    if (!link.href.startsWith("#")) continue;
    await navigate(cdp, "#pilot");
    await waitForExpression(cdp, "Boolean(document.querySelector('#workspace-pilot'))");
    await evalValue(cdp, `(() => {
      const link = Array.from(document.querySelectorAll('.pilot-step-card a')).find((item) => item.getAttribute('href') === ${JSON.stringify(link.href)});
      link?.click();
      return Boolean(link);
    })()`);
    await delay(700);
    const current = await evalValue(cdp, "location.hash");
    clicked.push({ label: link.text, expected: link.href, actual: current });
    assertCheck(current.startsWith(link.href), "pilot step link did not navigate to target", { link, current });
  }
  return { ...page, clicked };
}

async function exerciseConfirmationImport(cdp) {
  await navigate(cdp, "#pilot");
  await waitForExpression(cdp, "Boolean(document.querySelector('#pilot-confirmation-import textarea'))");
  const csv = [
    "signoff_item_id,section,item_name,review_status,confirmed_by,confirmed_role,confirmed_at,revision_note",
    "item-001,知识复测,售后规则,pending,,,,等待客户真实回填"
  ].join("\\n");
  await evalValue(cdp, `(() => {
    const textarea = document.querySelector('#pilot-confirmation-import textarea');
    const setter = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value').set;
    setter.call(textarea, ${JSON.stringify(csv)});
    textarea.dispatchEvent(new Event('input', { bubbles: true }));
    textarea.dispatchEvent(new Event('change', { bubbles: true }));
    const button = Array.from(document.querySelectorAll('#pilot-confirmation-import button')).find((item) => item.textContent?.includes('校验确认表'));
    button?.click();
    return Boolean(button);
  })()`);
  await waitForExpression(cdp, "document.body.innerText.includes('待确认') || document.body.innerText.includes('等待客户确认')", 15000);
  return evalValue(cdp, `(() => {
    const text = document.body.innerText;
    return {
      importClicked: true,
      pendingVisible: text.includes('待确认') || text.includes('等待客户确认'),
      formalSignoffClaimed: text.includes('正式客户验收已完成') || text.includes('已正式签收'),
      systemPrefilledClaimed: text.includes('系统已替客户确认')
    };
  })()`);
}

async function inspectSupportPages(cdp) {
  const checks = [
    { hash: "#quality", selector: "#workspace-quality", required: ["质量", "月度"] },
    { hash: "#settings", selector: "#workspace-settings", required: ["诊断", "备份", "更新"] },
    { hash: "#knowledge", selector: "#workspace-knowledge", required: ["知识", "业务"] }
  ];
  const pages = [];
  for (const check of checks) {
    await navigate(cdp, check.hash);
    await waitForExpression(cdp, `Boolean(document.querySelector(${JSON.stringify(check.selector)}))`);
    const result = await evalValue(cdp, `(() => {
      const text = document.body.innerText;
      return {
        hash: location.hash,
        selectorPresent: Boolean(document.querySelector(${JSON.stringify(check.selector)})),
        requiredPresent: ${JSON.stringify(check.required)}.every((item) => text.includes(item)),
        hasOverclaim: ['已正式签收', '真实外发已开启', '生产 SLA 已完成', '签名安装包已完成'].some((item) => text.includes(item)),
        hasHorizontalOverflow: document.documentElement.scrollWidth > innerWidth || document.body.scrollWidth > innerWidth
      };
    })()`);
    assertCheck(result.selectorPresent && result.requiredPresent, "support page missing required customer-trial content", { check, result });
    assertCheck(!result.hasOverclaim && !result.hasHorizontalOverflow, "support page contains overclaim or overflow", { check, result });
    pages.push(result);
  }
  await capture(cdp, "pilot4-settings-maintenance");
  return pages;
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
    const pilot = await inspectPilotPage(cdp);
    const confirmation = await exerciseConfirmationImport(cdp);
    assertCheck(confirmation.pendingVisible, "confirmation import did not remain in waiting state", confirmation);
    assertCheck(!confirmation.formalSignoffClaimed && !confirmation.systemPrefilledClaimed, "confirmation import overclaimed customer signoff", confirmation);
    const pages = await inspectSupportPages(cdp);
    const runtimeErrors = cdp.events
      .filter((event) => event.method === "Runtime.exceptionThrown")
      .map((event) => event.params?.exceptionDetails?.exception?.description || event.params?.exceptionDetails?.text || "runtime error");
    assertCheck(runtimeErrors.length === 0, "runtime errors occurred in PILOT4 browser rehearsal", runtimeErrors);
    return { pilot, confirmation, pages, runtimeErrors };
  } finally {
    cdp.close();
    await fetch(`${chromeEndpoint}/json/close/${target.id}`).catch(() => undefined);
  }
}

function writeMarkdown(result) {
  const lines = [
    "# H2W-PILOT4 客户本地试点端到端演练",
    "",
    "## 结论",
    "",
    fLine("阶段状态", result.status),
    fLine("真实登录", String(result.owner_login_performed_through_ui)),
    fLine("试点准备六步点击", `${result.browser.pilot.clicked.length} 个入口已点击`),
    "",
    "## 边界",
    "",
    "- 当前是本地试点 rehearsal，不是正式客户验收。",
    "- 真实外发、真实渠道、生产 SLA 和签名安装包仍未完成。",
    "- 客户确认表可以导入 pending 状态，但系统不会替客户确认或签收。",
    "",
    "## 证据",
    "",
    `- 截图：${path.relative(rootDir, path.join(outputDir, "pilot4-preparation.png"))}`,
    `- 截图：${path.relative(rootDir, path.join(outputDir, "pilot4-settings-maintenance.png"))}`,
    `- Summary：${path.relative(rootDir, path.join(outputDir, "summary.json"))}`
  ];
  fs.writeFileSync(docPath, `${lines.join("\n")}\n`, "utf-8");
}

function fLine(label, value) {
  return `- ${label}：\`${value}\``;
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
    schema_version: "p3-06u-26h2w-pilot4.customer_trial_rehearsal.v1",
    phase: "H2W-PILOT4",
    status: "passed_customer_local_trial_rehearsal",
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
    browser
  };
  fs.writeFileSync(path.join(outputDir, "summary.json"), JSON.stringify(result, null, 2));
  writeMarkdown(result);
  console.log(`[PASS] H2W-PILOT4 customer local trial rehearsal passed: ${path.join(outputDir, "summary.json")}`);
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
