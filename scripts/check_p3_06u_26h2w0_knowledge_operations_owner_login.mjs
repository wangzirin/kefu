import fs from "node:fs";
import path from "node:path";
import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";

const rootDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const outputDir = path.resolve(
  process.env.P3_06U_26H2W0_KNOWLEDGE_OUTPUT ??
    path.join(rootDir, "output/p3_06u_26h2w0_knowledge_operations_owner_login")
);
const backendPort = Number(process.env.P3_06U_26H2W0_KNOWLEDGE_BACKEND_PORT ?? 8112);
const frontendPort = Number(process.env.P3_06U_26H2W0_KNOWLEDGE_FRONTEND_PORT ?? 5212);
const chromePort = Number(process.env.P3_06U_26H2W0_KNOWLEDGE_CHROME_PORT ?? 9252);
const backendUrl = `http://127.0.0.1:${backendPort}`;
const frontendBaseUrl = `http://127.0.0.1:${frontendPort}/`;
const chromeEndpoint = `http://127.0.0.1:${chromePort}`;
const dbPath = path.join(outputDir, "h2w0_knowledge_operations.sqlite");
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
        OUTBOX_EXTERNAL_WRITE_ENABLED: "false"
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
    tenantSlug: `h2w0-knowledge-${stamp}`,
    tenantName: "H2W0 知识操作验收空间",
    ownerName: "H2W0 知识负责人",
    email: `h2w0-knowledge-${stamp}@wanfa.local`,
    password: `H2W0Knowledge${stamp}!`
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
  await delay(700);
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

function buildKnowledgeUpdatePackage(stamp) {
  return {
    schema_version: "wanfa.knowledge_update_package.v1",
    package_id: `pkg-h2w0-${stamp}`,
    package_name: `H2W0 知识更新包 ${stamp}`,
    source_diagnostic_filename: `diagnostic-h2w0-${stamp}.json`,
    notes: "H2W0 浏览器门禁生成的脱敏知识更新包，不包含真实客户原文。",
    business_objects: [
      {
        ref: `pkg-service-${stamp}`,
        type: "service",
        title: `验收服务包 ${stamp}`,
        aliases: [`验收服务${stamp}`, "浏览器门禁"],
        summary: "用于验证知识更新包能通过前端预检和导入。",
        status: "active"
      }
    ],
    object_knowledge_cards: [
      {
        business_object_ref: `pkg-service-${stamp}`,
        question: `验收服务包 ${stamp} 怎么开通？`,
        answer: "先确认客户场景、授权范围和知识包，再安排本地部署与回归测试。",
        trigger_keywords: ["验收服务", "开通", "本地部署"],
        source: "knowledge_update_package",
        status: "active"
      }
    ],
    knowledge_documents: [
      {
        title: `H2W0 更新包政策 ${stamp}`,
        source_type: "knowledge_update_package",
        source_uri: `internal://h2w0/package-policy/${stamp}`,
        tags: ["H2W0", "更新包"],
        status: "active",
        raw_text: "知识更新包导入后，只能更新本地知识库和回归题，不触发外部平台发送。"
      }
    ],
    evaluation_sets: [
      {
        name: `H2W0 更新包回归题 ${stamp}`,
        description: "验证更新包导入后评测集被创建。",
        status: "active",
        evaluation_mode: "customer_service_retrieval",
        cases: [
          {
            external_case_id: `h2w0-${stamp}-001`,
            question: "知识更新包导入后会自动给客户发消息吗？",
            expected_terms: ["不触发外部平台发送", "本地知识库"],
            expected_source_uri: `internal://h2w0/package-policy/${stamp}`,
            forbidden_terms: ["已经发到微信"],
            expected_human_review: false,
            allow_auto_reply: true,
            status: "active"
          }
        ]
      }
    ]
  };
}

async function performKnowledgeUiActions(cdp, stamp) {
  const objectTitle = `H2W0 手动对象 ${stamp}`;
  const objectTitleUpdated = `H2W0 手动对象已编辑 ${stamp}`;
  const cardQuestion = `H2W0 对象问答 ${stamp} 适合谁？`;
  const cardAnswer = "适合用来证明前端按钮会调用真实后端接口并刷新服务端数据。";
  const documentTitle = `H2W0 手动知识文档 ${stamp}`;
  const documentUri = `internal://h2w0/manual-doc/${stamp}`;
  const packagePayload = buildKnowledgeUpdatePackage(stamp);

  await navigate(cdp, "#knowledge");
  await waitForExpression(cdp, "Boolean(document.querySelector('#workspace-knowledge'))");
  await delay(1200);
  await capture(cdp, "knowledge-before-actions");

  const businessResult = await evalValue(cdp, `(() => {
    const setField = (selector, value) => {
      const element = document.querySelector(selector);
      if (!element) throw new Error('missing field ' + selector);
      const prototype = element instanceof HTMLTextAreaElement ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype;
      const setter = Object.getOwnPropertyDescriptor(prototype, 'value').set;
      setter.call(element, value);
      element.dispatchEvent(new Event('input', { bubbles: true }));
      element.dispatchEvent(new Event('change', { bubbles: true }));
    };
    setField('[data-knowledge-field="business-object-title"]', ${JSON.stringify(objectTitle)});
    setField('[data-knowledge-field="business-object-aliases"]', ${JSON.stringify(`手动对象${stamp}，门禁对象`)});
    setField('[data-knowledge-field="business-object-summary"]', '通过浏览器创建的业务对象，用于验证前后端契约。');
    document.querySelector('[data-knowledge-action="create-business-object"]').click();
    return true;
  })()`);
  assertCheck(businessResult === true, "business object action did not execute");
  await waitForExpression(cdp, `document.body.innerText.includes(${JSON.stringify(objectTitle)})`, 20000);

  const businessEditResult = await evalValue(cdp, `(() => {
    const objectButton = Array.from(document.querySelectorAll('.business-object-card')).find((item) => item.textContent?.includes(${JSON.stringify(objectTitle)}));
    objectButton?.click();
    const editButton = document.querySelector('[data-knowledge-action="edit-business-object"]');
    if (!editButton) throw new Error('missing edit business object button');
    editButton.click();
    const setField = (selector, value) => {
      const element = document.querySelector(selector);
      if (!element) throw new Error('missing field ' + selector);
      const prototype = element instanceof HTMLTextAreaElement ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype;
      const setter = Object.getOwnPropertyDescriptor(prototype, 'value').set;
      setter.call(element, value);
      element.dispatchEvent(new Event('input', { bubbles: true }));
      element.dispatchEvent(new Event('change', { bubbles: true }));
    };
    setField('[data-knowledge-field="business-object-title"]', ${JSON.stringify(objectTitleUpdated)});
    setField('[data-knowledge-field="business-object-aliases"]', ${JSON.stringify(`编辑对象${stamp}，门禁已编辑`)});
    setField('[data-knowledge-field="business-object-summary"]', '已通过浏览器编辑业务对象并写入后端。');
    document.querySelector('[data-knowledge-action="create-business-object"]').click();
    return true;
  })()`);
  assertCheck(businessEditResult === true, "business object edit action did not execute");
  await waitForExpression(cdp, `document.body.innerText.includes(${JSON.stringify(objectTitleUpdated)})`, 20000);

  const objectSelectResult = await evalValue(cdp, `(() => {
    const button = Array.from(document.querySelectorAll('.business-object-card')).find((item) => item.textContent?.includes(${JSON.stringify(objectTitleUpdated)}));
    if (!button) throw new Error('missing edited business object card');
    button.click();
    return true;
  })()`);
  assertCheck(objectSelectResult === true, "edited business object was not selected before card create");
  await waitForExpression(cdp, `Boolean(Array.from(document.querySelectorAll('.business-object-card.selected')).find((item) => item.textContent?.includes(${JSON.stringify(objectTitleUpdated)})))`, 10000);

  const cardResult = await evalValue(cdp, `(() => {
    const setField = (selector, value) => {
      const element = document.querySelector(selector);
      if (!element) throw new Error('missing field ' + selector);
      const prototype = element instanceof HTMLTextAreaElement ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype;
      const setter = Object.getOwnPropertyDescriptor(prototype, 'value').set;
      setter.call(element, value);
      element.dispatchEvent(new Event('input', { bubbles: true }));
      element.dispatchEvent(new Event('change', { bubbles: true }));
    };
    setField('[data-knowledge-field="object-card-question"]', ${JSON.stringify(cardQuestion)});
    setField('[data-knowledge-field="object-card-answer"]', ${JSON.stringify(cardAnswer)});
    setField('[data-knowledge-field="object-card-keywords"]', 'H2W0，门禁，真实后端');
    document.querySelector('[data-knowledge-action="create-object-card"]').click();
    return true;
  })()`);
  assertCheck(cardResult === true, "object knowledge card action did not execute");
  await waitForExpression(cdp, `document.body.innerText.includes(${JSON.stringify(cardQuestion)})`, 20000);

  const documentResult = await evalValue(cdp, `(() => {
    const setField = (selector, value) => {
      const element = document.querySelector(selector);
      if (!element) throw new Error('missing field ' + selector);
      const prototype = element instanceof HTMLTextAreaElement ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype;
      const setter = Object.getOwnPropertyDescriptor(prototype, 'value').set;
      setter.call(element, value);
      element.dispatchEvent(new Event('input', { bubbles: true }));
      element.dispatchEvent(new Event('change', { bubbles: true }));
    };
    setField('[data-knowledge-field="document-title"]', ${JSON.stringify(documentTitle)});
    setField('[data-knowledge-field="document-source-uri"]', ${JSON.stringify(documentUri)});
    setField('[data-knowledge-field="document-tags"]', 'H2W0，手动导入，门禁');
    setField('[data-knowledge-field="document-raw-text"]', '适用问题：如何验证知识导入。标准答案：通过前端提交后端落库并刷新列表。禁止承诺：不能写成已经外发。引用来源：H2W0 本地门禁。');
    document.querySelector('[data-knowledge-action="import-document"]').click();
    return true;
  })()`);
  assertCheck(documentResult === true, "knowledge document action did not execute");
  await waitForExpression(cdp, `document.body.innerText.includes(${JSON.stringify(documentTitle)})`, 20000);

  await capture(cdp, "knowledge-after-manual-create");

  const packageJson = JSON.stringify(packagePayload, null, 2);
  const previewResult = await evalValue(cdp, `(() => {
    const textarea = document.querySelector('[data-knowledge-update-package-field="json"]');
    if (!textarea) throw new Error('missing update package textarea');
    const setter = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value').set;
    setter.call(textarea, ${JSON.stringify(packageJson)});
    textarea.dispatchEvent(new Event('input', { bubbles: true }));
    textarea.dispatchEvent(new Event('change', { bubbles: true }));
    const button = Array.from(document.querySelectorAll('button')).find((item) => item.textContent?.includes('检查资料包'));
    if (!button) throw new Error('missing preview button');
    button.click();
    return true;
  })()`);
  assertCheck(previewResult === true, "knowledge update package preview action did not execute");
  await waitForExpression(cdp, `document.body.innerText.includes('预检通过') && document.body.innerText.includes(${JSON.stringify(packagePayload.package_name)})`, 20000);
  await capture(cdp, "knowledge-package-preview");

  const importResult = await evalValue(cdp, `(() => {
    const button = Array.from(document.querySelectorAll('button')).find((item) => item.textContent?.includes('导入资料包'));
    if (!button) throw new Error('missing import button');
    button.click();
    return true;
  })()`);
  assertCheck(importResult === true, "knowledge update package import action did not execute");
  await waitForExpression(cdp, `document.body.innerText.includes('已导入知识资料包') && document.body.innerText.includes(${JSON.stringify(packagePayload.business_objects[0].title)})`, 25000);
  await capture(cdp, "knowledge-after-package-import");

  const uiState = await evalValue(cdp, `(() => {
    const text = document.body.innerText;
    return {
      hasBusinessObject: text.includes(${JSON.stringify(objectTitle)}),
      hasEditedBusinessObject: text.includes(${JSON.stringify(objectTitleUpdated)}),
      hasObjectCard: text.includes(${JSON.stringify(cardQuestion)}),
      hasDocument: text.includes(${JSON.stringify(documentTitle)}),
      hasPackagePreview: text.includes('预检通过') || text.includes(${JSON.stringify(packagePayload.package_name)}),
      hasPackageImport: text.includes('已导入知识资料包') || text.includes('已导入'),
      hasDiffResult: Boolean(document.querySelector('[data-knowledge-update-package-result="diff"]')),
      hasOverclaim: ['已自动发送', '已接通全渠道', '已完成线上准确率', '已上传云端', '已正式签收'].some((item) => text.includes(item)),
      hasHorizontalOverflow: document.documentElement.scrollWidth > innerWidth || document.body.scrollWidth > innerWidth
    };
  })()`);
  assertCheck(uiState.hasEditedBusinessObject && uiState.hasObjectCard && uiState.hasDocument, "knowledge manual UI operations missing rendered data", uiState);
  assertCheck(uiState.hasPackagePreview && uiState.hasPackageImport && uiState.hasDiffResult, "knowledge package UI operations missing rendered result", uiState);
  assertCheck(!uiState.hasOverclaim, "knowledge page contains banned overclaim copy", uiState);
  assertCheck(!uiState.hasHorizontalOverflow, "knowledge page has horizontal overflow", uiState);

  return {
    stamp,
    objectTitle,
    objectTitleUpdated,
    cardQuestion,
    documentTitle,
    documentUri,
    packageId: packagePayload.package_id,
    packageName: packagePayload.package_name,
    packageBusinessObjectTitle: packagePayload.business_objects[0].title,
    packageDocumentTitle: packagePayload.knowledge_documents[0].title,
    uiState
  };
}

async function verifyServerData(seed, expected) {
  const headers = { Authorization: `Bearer ${seed.token}` };
  const [businessObjects, documents, evaluationSets] = await Promise.all([
    apiJson(`/api/tenants/${seed.tenantId}/business-objects?status=active`, { headers }),
    apiJson(`/api/tenants/${seed.tenantId}/knowledge-documents?status=active`, { headers }),
    apiJson(`/api/tenants/${seed.tenantId}/knowledge-evaluation-sets?status=active`, { headers })
  ]);
  const manualBusinessObject = businessObjects.items.find((item) => item.title === expected.objectTitleUpdated);
  const packageBusinessObject = businessObjects.items.find((item) => item.title === expected.packageBusinessObjectTitle);
  assertCheck(Boolean(manualBusinessObject), "manual business object was not persisted", businessObjects);
  assertCheck(
    manualBusinessObject.aliases.includes(`编辑对象${expected.stamp}`),
    "manual business object edit was not persisted",
    manualBusinessObject
  );
  assertCheck(Boolean(packageBusinessObject), "package business object was not persisted", businessObjects);

  const manualCards = await apiJson(`/api/business-objects/${manualBusinessObject.id}/knowledge-cards?status=active`, { headers });
  assertCheck(
    manualCards.items.some((item) => item.question === expected.cardQuestion),
    "manual object knowledge card was not persisted",
    manualCards
  );

  const documentTitles = documents.items.map((item) => item.title);
  assertCheck(documentTitles.includes(expected.documentTitle), "manual knowledge document was not persisted", documents);
  assertCheck(documentTitles.includes(expected.packageDocumentTitle), "package knowledge document was not persisted", documents);
  assertCheck(evaluationSets.total >= 1, "package evaluation set was not persisted", evaluationSets);

  return {
    business_object_total: businessObjects.total,
    knowledge_document_total: documents.total,
    evaluation_set_total: evaluationSets.total,
    manual_business_object_id: manualBusinessObject.id,
    package_business_object_id: packageBusinessObject.id,
    manual_object_card_total: manualCards.total,
    persisted_document_titles: documentTitles
  };
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
    assertCheck(login.tokenStored && !login.hasLoginForm, "owner login did not establish authenticated workspace", login);
    const knowledgeOperations = await performKnowledgeUiActions(cdp, Date.now());
    const serverVerification = await verifyServerData(seed, knowledgeOperations);
    const runtimeErrors = cdp.events
      .filter((event) => event.method === "Runtime.exceptionThrown")
      .map((event) => event.params?.exceptionDetails?.exception?.description || event.params?.exceptionDetails?.text || "runtime error");
    assertCheck(runtimeErrors.length === 0, "runtime errors occurred in knowledge operations smoke", runtimeErrors);
    return { login, knowledgeOperations, serverVerification, runtimeErrors };
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
  const browser = await runBrowserSmoke(seed);
  const summaryPath = path.join(outputDir, "summary.json");
  fs.writeFileSync(
    summaryPath,
    JSON.stringify(
      {
        ok: true,
        frontendUrl: frontendBaseUrl,
        backendUrl,
        tenant_id: seed.tenantId,
        owner_login_performed_through_ui: true,
        demo_mode_used: false,
        knowledge_operations_performed_through_ui: true,
        business_object_create_performed_through_ui: true,
        business_object_update_performed_through_ui: true,
        object_knowledge_card_create_performed_through_ui: true,
        knowledge_document_import_performed_through_ui: true,
        knowledge_update_package_preview_performed_through_ui: true,
        knowledge_update_package_import_performed_through_ui: true,
        server_persistence_verified: true,
        external_platform_write_performed: false,
        model_call_performed: false,
        browser
      },
      null,
      2
    )
  );
  console.log(`[PASS] P3-06U-26H2W-0 knowledge operations owner-login gate passed: ${summaryPath}`);
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
