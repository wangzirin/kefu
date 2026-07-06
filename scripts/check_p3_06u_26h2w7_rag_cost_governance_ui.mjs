import fs from "node:fs";
import path from "node:path";
import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";

const rootDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const outputDir = path.resolve(process.env.P3_06U_26H2W7_OUTPUT ?? path.join(rootDir, "output/p3_06u_26h2w7_rag_cost_governance_ui"));
const backendPort = Number(process.env.P3_06U_26H2W7_BACKEND_PORT ?? 8127);
const frontendPort = Number(process.env.P3_06U_26H2W7_FRONTEND_PORT ?? 5227);
const chromePort = Number(process.env.P3_06U_26H2W7_CHROME_PORT ?? 9267);
const backendUrl = `http://127.0.0.1:${backendPort}`;
const frontendBaseUrl = `http://127.0.0.1:${frontendPort}/`;
const chromeEndpoint = `http://127.0.0.1:${chromePort}`;
const dbPath = path.join(outputDir, "h2w7_rag_cost_governance.sqlite");
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
  fs.mkdirSync(outputDir, { recursive: true });
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
      // keep polling
    }
    await delay(300);
  }
  throw new Error(`Timed out waiting for ${url}`);
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

async function seedScenario() {
  const stamp = Date.now();
  const tenantSlug = `h2w7-ui-${stamp}`;
  const email = `h2w7-owner-${stamp}@wanfa.local`;
  const password = `H2W7Owner${stamp}!`;
  const owner = await apiJson("/api/auth/local-setup/owner", {
    method: "POST",
    body: JSON.stringify({
      tenant_slug: tenantSlug,
      tenant_name: "H2W7 检索与成本治理验收空间",
      owner_name: "H2W7 负责人",
      email,
      password
    })
  });
  const token = owner.access_token;
  const tenantId = owner.user.tenant.id;
  const headers = { Authorization: `Bearer ${token}` };
  const rawText = [
    "售后政策：标准产品保修期为三年。",
    "客户超过七天退货时，需要核对订单时间、商品状态和平台规则。",
    "涉及赔偿、投诉、起诉、私下转账或保证收益时必须转人工，不得自动承诺。"
  ].join("\n");
  await apiJson(`/api/tenants/${tenantId}/knowledge-documents`, {
    method: "POST",
    headers,
    body: JSON.stringify({
      title: "H2W7 售后政策手册",
      source_type: "manual_document",
      source_uri: "internal://h2w7/after-sales",
      raw_text: rawText,
      tags: ["售后", "成本治理"],
      status: "active",
      chunk_size: 80,
      chunk_overlap: 10
    })
  });
  await apiJson(`/api/tenants/${tenantId}/knowledge-embedding-provider-smoke-runs`, {
    method: "POST",
    headers,
    body: JSON.stringify({ sample_text: "H2W7 UI smoke 只记录 hash 和成本估算。" })
  });
  const evaluationSet = await apiJson(`/api/tenants/${tenantId}/knowledge-evaluation-sets`, {
    method: "POST",
    headers,
    body: JSON.stringify({
      name: "H2W7 UI 受控题集",
      description: "用于模型页治理摘要渲染 smoke。",
      status: "active",
      evaluation_mode: "customer_service_retrieval",
      cases: [
        {
          question: "标准产品保修期多久",
          expected_terms: ["三年", "保修"],
          expected_source_uri: "internal://h2w7/after-sales",
          required_citation: true
        },
        {
          question: "超过七天退货需要核对什么",
          expected_terms: ["订单时间", "商品状态"],
          expected_source_uri: "internal://h2w7/after-sales",
          required_citation: true
        }
      ]
    })
  });
  await apiJson(`/api/knowledge-evaluation-sets/${evaluationSet.id}/runs`, {
    method: "POST",
    headers,
    body: JSON.stringify({ top_k: 3, low_confidence_threshold: 0.2 })
  });
  return { tenantSlug, email, password };
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
      "--headless=new",
      "--disable-gpu",
      "--no-first-run",
      "--no-default-browser-check",
      `--remote-debugging-port=${chromePort}`,
      `--user-data-dir=${chromeProfile}`,
      "--window-size=1440,1100",
      "about:blank"
    ]
  );
  await waitForHttp(`${chromeEndpoint}/json/version`);
}

async function createCdpClient() {
  const newPage = await fetch(`${chromeEndpoint}/json/new?${encodeURIComponent(frontendBaseUrl)}`, { method: "PUT" });
  const page = await newPage.json();
  const ws = new WebSocket(page.webSocketDebuggerUrl);
  await new Promise((resolve, reject) => {
    ws.addEventListener("open", resolve, { once: true });
    ws.addEventListener("error", reject, { once: true });
  });
  let id = 0;
  const pending = new Map();
  ws.addEventListener("message", (event) => {
    const message = JSON.parse(event.data);
    if (message.id && pending.has(message.id)) {
      const { resolve, reject } = pending.get(message.id);
      pending.delete(message.id);
      if (message.error) reject(new Error(JSON.stringify(message.error)));
      else resolve(message.result);
    }
  });
  function send(method, params = {}) {
    const callId = ++id;
    ws.send(JSON.stringify({ id: callId, method, params }));
    return new Promise((resolve, reject) => pending.set(callId, { resolve, reject }));
  }
  return { send, close: () => ws.close() };
}

async function waitForText(cdp, text, timeoutMs = 20000) {
  const started = Date.now();
  let lastBodyText = "";
  while (Date.now() - started < timeoutMs) {
    const result = await cdp.send("Runtime.evaluate", {
      expression: `document.body ? document.body.innerText : ""`,
      returnByValue: true
    });
    lastBodyText = String(result.result.value ?? "");
    if (lastBodyText.includes(text)) return lastBodyText;
    await delay(400);
  }
  const locationResult = await cdp.send("Runtime.evaluate", {
    expression: `location.href`,
    returnByValue: true
  });
  throw new Error(
    `Timed out waiting for text: ${text}\nURL: ${locationResult.result.value}\nBody: ${lastBodyText.slice(0, 1200)}`
  );
}

async function fillLoginForm(cdp, credentials) {
  await waitForText(cdp, "登录工作台");
  const result = await cdp.send("Runtime.evaluate", {
    expression: `(() => {
      const values = ${JSON.stringify(credentials)};
      const setInputValue = (selector, value) => {
        const element = document.querySelector(selector);
        if (!element) return false;
        const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, "value").set;
        setter.call(element, value);
        element.dispatchEvent(new Event("input", { bubbles: true }));
        element.dispatchEvent(new Event("change", { bubbles: true }));
        return true;
      };
      const filled = [
        setInputValue('[data-role-smoke="tenant-slug"]', values.tenantSlug),
        setInputValue('[data-role-smoke="email"]', values.email),
        setInputValue('[data-role-smoke="password"]', values.password)
      ];
      const submit = document.querySelector('[data-role-smoke="login-submit"]');
      if (!submit) return { ok: false, filled, reason: "submit_missing" };
      submit.click();
      return { ok: filled.every(Boolean), filled };
    })()`,
    returnByValue: true
  });
  if (!result.result.value?.ok) {
    throw new Error(`Unable to fill login form: ${JSON.stringify(result.result.value)}`);
  }
}

async function verifyUi(credentials) {
  await startChrome();
  const cdp = await createCdpClient();
  try {
    await cdp.send("Page.enable");
    await cdp.send("Runtime.enable");
    await cdp.send("Page.navigate", { url: `${frontendBaseUrl}#model` });
    await fillLoginForm(cdp, credentials);
    const bodyText = await waitForText(cdp, "检索与成本治理");
    const checks = {
      hasGovernanceTitle: bodyText.includes("检索与成本治理"),
      hasGateLabel: bodyText.includes("H2W7 门禁") || bodyText.includes("客服模型调用成本"),
      hasModelCostGap: bodyText.includes("客服模型调用成本") && bodyText.includes("阻断"),
      hasExternalWriteOff: bodyText.includes("真实外发") && bodyText.includes("关闭")
    };
    const marker = await cdp.send("Runtime.evaluate", {
      expression: `Boolean(document.querySelector('[data-rag-cost-governance="p3-06u-26h2w7"]'))`,
      returnByValue: true
    });
    checks.hasDataMarker = Boolean(marker.result.value);
    const failed = Object.entries(checks).filter(([, value]) => !value);
    if (failed.length) {
      throw new Error(`UI checks failed: ${JSON.stringify({ checks, excerpt: bodyText.slice(0, 1200) }, null, 2)}`);
    }
    const screenshot = await cdp.send("Page.captureScreenshot", { format: "png", captureBeyondViewport: true });
    fs.writeFileSync(path.join(outputDir, "desktop-1440-rag-cost-governance.png"), Buffer.from(screenshot.data, "base64"));
    fs.writeFileSync(path.join(outputDir, "summary.json"), JSON.stringify({ checks }, null, 2));
  } finally {
    cdp.close();
  }
}

async function main() {
  try {
    await startServices();
    const credentials = await seedScenario();
    await verifyUi(credentials);
    console.log(`P3-06U-26H2W7 UI smoke passed. Output: ${outputDir}`);
  } finally {
    for (const child of children.reverse()) {
      child.kill("SIGTERM");
    }
  }
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
