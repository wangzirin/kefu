import fs from "node:fs";
import path from "node:path";
import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";

const rootDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const outputDir = path.resolve(
  process.env.P3_06U_26H2W11E_OUTPUT ??
    path.join(rootDir, "output/p3_06u_26h2w11e_owner_customer_knowledge_trial")
);
const backendPort = Number(process.env.P3_06U_26H2W11E_BACKEND_PORT ?? 8116);
const frontendPort = Number(process.env.P3_06U_26H2W11E_FRONTEND_PORT ?? 5216);
const chromePort = Number(process.env.P3_06U_26H2W11E_CHROME_PORT ?? 9256);
const backendUrl = `http://127.0.0.1:${backendPort}`;
const frontendBaseUrl = `http://127.0.0.1:${frontendPort}/`;
const chromeEndpoint = `http://127.0.0.1:${chromePort}`;
const dbPath = path.join(outputDir, "h2w11e_owner_customer_knowledge_trial.sqlite");
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

async function waitForHttp(url, timeoutMs = 25000) {
  const started = Date.now();
  while (Date.now() - started < timeoutMs) {
    try {
      const response = await fetch(url);
      if (response.ok) return;
    } catch {
      await delay(300);
    }
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
        OUTBOX_EXTERNAL_WRITE_ENABLED: "false",
        WECOM_TRUSTED_INBOUND_ENABLED: "false",
        STANDARD_OPS_DEMO_BOOTSTRAP: "false"
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
    tenantSlug: `h2w11e-owner-${stamp}`,
    tenantName: "H2W11E 客户知识试用空间",
    ownerName: "H2W11E 负责人",
    email: `h2w11e-owner-${stamp}@wanfa.local`,
    password: `H2W11EOwner${stamp}!`
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
  return {
    credentials,
    owner,
    tenantId: owner.user.tenant.id,
    token: owner.access_token
  };
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

async function waitForExpression(cdp, expression, timeoutMs = 15000) {
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
    tokenStored: Boolean(window.localStorage.getItem('wanfa_standard_ops_access_token')),
    hasLoginForm: Boolean(document.querySelector('[data-role-smoke="login-form"]'))
  }))()`);
}

async function checkH2W11DKnowledgePath(cdp) {
  await navigate(cdp, "#knowledge");
  await waitForExpression(cdp, "Boolean(document.querySelector('#workspace-knowledge'))");
  await waitForExpression(cdp, "Boolean(document.querySelector('[data-h2w11d-customer-publish-path=\"true\"]'))");
  await evalValue(cdp, `document.querySelector('[data-h2w11d-customer-publish-path="true"]').scrollIntoView({ block: 'center' })`);
  await delay(400);
  await capture(cdp, "01-knowledge-publish-path-before-clicks");

  const initialState = await evalValue(cdp, `(() => {
    const section = document.querySelector('[data-h2w11d-customer-publish-path="true"]');
    const actions = Array.from(section.querySelectorAll('[data-h2w11d-action]')).map((item) => {
      const rect = item.getBoundingClientRect();
      return {
        action: item.getAttribute('data-h2w11d-action'),
        text: item.innerText.trim(),
        tag: item.tagName.toLowerCase(),
        disabled: Boolean(item.disabled),
        visible: rect.width > 0 && rect.height > 0,
        inViewport: rect.bottom > 0 && rect.top < innerHeight && rect.right > 0 && rect.left < innerWidth
      };
    });
    const text = document.body.innerText;
    return {
      actionCount: actions.length,
      actions,
      hasReleaseHeading: text.includes('知识维护总流程'),
      hasStepCopy: text.includes('导入资料 → 预检 → 发布 → 复测 → 确认 → 质量报告'),
      hasExternalWriteBoundary: text.includes('真实外发继续关闭'),
      hasCustomerConfirmationBoundary: text.includes('客户确认记录不是正式验收'),
      visibleOverclaims: ['已真实外发', '全平台已接通', '正式电子签章已完成', '合同签收已完成', 'RPA 自动发送', 'Hook', 'Cookie 接管'].filter((item) => text.includes(item)),
      legacyTerms: ['客户知识发布闭环', '预检更新包', '转换客户资料', '发布前试跑', '确认发布', '进入知识评测', '本地签收记录不是正式电子签章'].filter((item) => text.includes(item)),
      horizontalOverflow: document.documentElement.scrollWidth > innerWidth || document.body.scrollWidth > innerWidth
    };
  })()`);
  assertCheck(initialState.actionCount >= 7, "H2W-11D customer publish path should expose seven actions", initialState);
  assertCheck(
    initialState.actions.every((action) => action.text.length > 0 && action.visible),
    "H2W-11D actions should be visible and have text labels",
    initialState.actions
  );
  assertCheck(initialState.hasReleaseHeading && initialState.hasStepCopy, "customer publish path heading or step copy missing", initialState);
  assertCheck(initialState.hasExternalWriteBoundary && initialState.hasCustomerConfirmationBoundary, "customer publish path boundary copy missing", initialState);
  assertCheck(initialState.visibleOverclaims.length === 0, "customer publish path contains overclaiming copy", initialState.visibleOverclaims);
  assertCheck(initialState.legacyTerms.length === 0, "customer publish path still exposes legacy/internal terms", initialState.legacyTerms);
  assertCheck(!initialState.horizontalOverflow, "knowledge page has horizontal overflow before clicks", initialState);

  await evalValue(cdp, `document.querySelector('[data-h2w11d-action="convert-customer-intake"]').click()`);
  await waitForExpression(cdp, `document.body.innerText.includes('已生成知识资料包')`, 15000);
  await capture(cdp, "02-knowledge-after-convert");

  await evalValue(cdp, `document.querySelector('[data-h2w11d-action="preview-update-package"]').click()`);
  await waitForExpression(
    cdp,
    `Boolean(document.querySelector('[data-knowledge-update-package-result="diff"]')) && (document.body.innerText.includes('预检通过') || document.body.innerText.includes('可导入'))`,
    20000
  );
  await capture(cdp, "03-knowledge-after-preview");

  await evalValue(cdp, `document.querySelector('[data-h2w11d-action="import-update-package"]').click()`);
  await waitForExpression(cdp, `document.body.innerText.includes('已导入知识资料包') || document.body.innerText.includes('已导入')`, 25000);
  await capture(cdp, "04-knowledge-after-import");

  const afterImportState = await evalValue(cdp, `(() => {
    const text = document.body.innerText;
    const section = document.querySelector('[data-h2w11d-customer-publish-path="true"]');
    const publishButtons = ['publish-precheck-first-ready-document', 'publish-first-ready-document'].map((key) => {
      const element = section.querySelector('[data-h2w11d-action="' + key + '"]');
      return { key, text: element?.innerText.trim() ?? '', disabled: Boolean(element?.disabled) };
    });
    return {
      hasImportResult: text.includes('已导入知识资料包') || text.includes('已导入'),
      hasDiffResult: Boolean(document.querySelector('[data-knowledge-update-package-result="diff"]')),
      hasCustomerIntake: text.includes('客户资料整理'),
      hasKnowledgeGuide: text.includes('客户知识维护向导'),
      hasUpdatePackage: text.includes('知识资料包'),
      publishButtons,
      visibleOverclaims: ['已真实外发', '全平台已接通', '正式电子签章已完成', '合同签收已完成', 'RPA 自动发送', 'Hook', 'Cookie 接管'].filter((item) => text.includes(item)),
      legacyTerms: ['客户资料导入助手', '知识更新包', '预检差异', '导入更新包', '转换为更新包'].filter((item) => text.includes(item)),
      horizontalOverflow: document.documentElement.scrollWidth > innerWidth || document.body.scrollWidth > innerWidth
    };
  })()`);
  assertCheck(afterImportState.hasImportResult && afterImportState.hasDiffResult, "knowledge import result not visible after owner operation", afterImportState);
  assertCheck(afterImportState.hasCustomerIntake && afterImportState.hasKnowledgeGuide, "knowledge page core customer maintenance areas missing", afterImportState);
  assertCheck(afterImportState.visibleOverclaims.length === 0, "knowledge page contains overclaiming copy after import", afterImportState.visibleOverclaims);
  assertCheck(afterImportState.legacyTerms.length === 0, "knowledge page still exposes legacy/internal terms after import", afterImportState.legacyTerms);
  assertCheck(!afterImportState.horizontalOverflow, "knowledge page has horizontal overflow after import", afterImportState);

  return { initialState, afterImportState };
}

async function checkLinkedPages(cdp) {
  const pages = [];
  const pageChecks = [
    {
      hash: "#evals",
      selector: "#workspace-evals",
      screenshot: "05-evaluation-page",
      requiredText: ["知识评测中心", "不等同完整事实准确率"],
      bannedText: ["完整线上准确率已完成", "客户准确率已签收", "真实外发已开启"]
    },
    {
      hash: "#quality",
      selector: "#workspace-quality",
      screenshot: "06-quality-report-page",
      requiredText: ["质量诊断", "客户可读质量报告", "不是正式电子签章"],
      bannedText: ["正式电子签章已完成", "合同签收已完成", "真实渠道外发已经验收"]
    },
    {
      hash: "#gaps",
      selector: "#workspace-knowledge-gaps",
      screenshot: "07-knowledge-gap-page",
      requiredText: ["知识缺口", "补知识", "回归"],
      bannedText: ["自动修复已完成", "无需人工确认", "真实外发已开启"]
    }
  ];

  for (const check of pageChecks) {
    await navigate(cdp, check.hash);
    await waitForExpression(cdp, `Boolean(document.querySelector(${JSON.stringify(check.selector)}))`);
    await capture(cdp, check.screenshot);
    const state = await evalValue(cdp, `(() => {
      const text = document.body.innerText;
      return {
        hash: location.hash,
        requiredMissing: ${JSON.stringify(check.requiredText)}.filter((item) => !text.includes(item)),
        bannedFound: ${JSON.stringify(check.bannedText)}.filter((item) => text.includes(item)),
        hasHorizontalOverflow: document.documentElement.scrollWidth > innerWidth || document.body.scrollWidth > innerWidth,
        emptyIconButtons: Array.from(document.querySelectorAll('button')).filter((button) => {
          const rect = button.getBoundingClientRect();
          return rect.width > 0 && rect.height > 0 && button.innerText.trim().length === 0 && !button.getAttribute('aria-label');
        }).length
      };
    })()`);
    assertCheck(state.requiredMissing.length === 0, `${check.hash} missing required customer-facing text`, state);
    assertCheck(state.bannedFound.length === 0, `${check.hash} contains overclaiming text`, state);
    assertCheck(!state.hasHorizontalOverflow, `${check.hash} has horizontal overflow`, state);
    pages.push(state);
  }
  return pages;
}

async function verifyServerData(seed) {
  const headers = { Authorization: `Bearer ${seed.token}` };
  const [businessObjects, documents, evaluationSets] = await Promise.all([
    apiJson(`/api/tenants/${seed.tenantId}/business-objects?status=active`, { headers }),
    apiJson(`/api/tenants/${seed.tenantId}/knowledge-documents?status=active`, { headers }),
    apiJson(`/api/tenants/${seed.tenantId}/knowledge-evaluation-sets?status=active`, { headers })
  ]);
  assertCheck(businessObjects.total > 0, "customer knowledge import did not persist business objects", businessObjects);
  assertCheck(documents.total > 0, "customer knowledge import did not persist documents", documents);
  assertCheck(evaluationSets.total > 0, "customer knowledge import did not persist evaluation sets", evaluationSets);
  return {
    business_object_total: businessObjects.total,
    knowledge_document_total: documents.total,
    evaluation_set_total: evaluationSets.total,
    sample_business_objects: businessObjects.items.slice(0, 3).map((item) => item.title),
    sample_documents: documents.items.slice(0, 3).map((item) => item.title),
    sample_evaluation_sets: evaluationSets.items.slice(0, 3).map((item) => item.name)
  };
}

async function runBrowserTrial(seed) {
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
    assertCheck(login.tokenStored && !login.hasLoginForm, "owner login did not establish authenticated workspace", login);
    const customerKnowledgePath = await checkH2W11DKnowledgePath(cdp);
    const linkedPages = await checkLinkedPages(cdp);
    const serverVerification = await verifyServerData(seed);
    const runtimeErrors = cdp.events
      .filter((event) => event.method === "Runtime.exceptionThrown")
      .map((event) => event.params?.exceptionDetails?.exception?.description || event.params?.exceptionDetails?.text || "runtime error");
    assertCheck(runtimeErrors.length === 0, "runtime errors occurred in H2W-11E browser trial", runtimeErrors);
    return { login, customerKnowledgePath, linkedPages, serverVerification, runtimeErrors };
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
  const seed = await seedOwner();
  const browser = await runBrowserTrial(seed);
  const summaryPath = path.join(outputDir, "summary.json");
  fs.writeFileSync(
    summaryPath,
    JSON.stringify(
      {
        ok: true,
        phase: "H2W-11E",
        frontendUrl: frontendBaseUrl,
        backendUrl,
        tenant_id: seed.tenantId,
        owner_login_performed_through_ui: true,
        demo_mode_used: false,
        customer_publish_path_actions_checked: true,
        customer_publish_path_clicked_through_ui: true,
        linked_pages_checked: ["#evals", "#quality", "#gaps"],
        server_persistence_verified: true,
        external_platform_write_performed: false,
        real_platform_send_performed: false,
        model_call_performed: false,
        formal_customer_signoff_performed: false,
        electronic_signature_performed: false,
        real_customer_data_used: false,
        browser
      },
      null,
      2
    )
  );
  console.log(`[PASS] H2W-11E owner customer knowledge trial passed: ${summaryPath}`);
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
