import fs from "node:fs";
import path from "node:path";
import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";

const rootDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const outputDir = path.resolve(
  process.env.P3_06U_26H2O_OUTPUT ?? path.join(rootDir, "output/p3_06u_26h2o_customer_question_bank_import_ui")
);
const backendPort = Number(process.env.P3_06U_26H2O_BACKEND_PORT ?? 8102);
const frontendPort = Number(process.env.P3_06U_26H2O_FRONTEND_PORT ?? 5202);
const chromePort = Number(process.env.P3_06U_26H2O_CHROME_PORT ?? 9242);
const backendUrl = `http://127.0.0.1:${backendPort}`;
const frontendUrl = `http://127.0.0.1:${frontendPort}/#evals`;
const chromeEndpoint = `http://127.0.0.1:${chromePort}`;
const dbPath = path.join(outputDir, "customer_question_bank_smoke.sqlite");
const chromeProfile = path.join(outputDir, "chrome-profile");
const screenshotPath = path.join(outputDir, "customer-question-bank-import.png");
const summaryPath = path.join(outputDir, "summary.json");
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

async function waitForHttp(url, timeoutMs = 20000) {
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

async function requestJson(url, options = {}) {
  const response = await fetch(`${backendUrl}${url}`, {
    ...options,
    headers: {
      "content-type": "application/json",
      ...(options.headers ?? {})
    }
  });
  const bodyText = await response.text();
  const body = bodyText ? JSON.parse(bodyText) : {};
  if (!response.ok) {
    throw new Error(`${options.method ?? "GET"} ${url} failed ${response.status}: ${bodyText}`);
  }
  return body;
}

async function startServices() {
  fs.mkdirSync(outputDir, { recursive: true });
  fs.rmSync(chromeProfile, { recursive: true, force: true });
  fs.rmSync(dbPath, { force: true });
  await runCommand(pythonBin, ["scripts/repair_local_sqlite_schema.py", "--db", dbPath], { cwd: rootDir });
  const backendEnv = {
    ...process.env,
    DATABASE_URL: `sqlite+pysqlite:///${dbPath}`,
    STANDARD_OPS_ENV: "development",
    STANDARD_OPS_ALLOWED_ORIGINS: `http://127.0.0.1:${frontendPort},http://localhost:${frontendPort}`,
    OUTBOX_EXTERNAL_WRITE_ENABLED: "false"
  };
  spawnLongRunning(
    "backend",
    pythonBin,
    ["-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", String(backendPort)],
    { cwd: path.join(rootDir, "backend"), env: backendEnv }
  );
  await waitForHttp(`${backendUrl}/health`);
  spawnLongRunning("frontend", "npm", ["run", "dev", "--", "--host", "127.0.0.1", "--port", String(frontendPort)], {
    cwd: path.join(rootDir, "frontend"),
    env: { ...process.env, VITE_API_PROXY_TARGET: backendUrl }
  });
  await waitForHttp(`http://127.0.0.1:${frontendPort}/`);
}

async function createLocalOwner() {
  const stamp = Date.now();
  const login = await requestJson("/api/auth/local-setup/owner", {
    method: "POST",
    body: JSON.stringify({
      tenant_slug: `h2o-question-bank-${stamp}`,
      tenant_name: "H2O 客户题库导入测试空间",
      owner_name: "H2O 管理员",
      email: `h2o-owner-${stamp}@wanfa.local`,
      password: `H2OSmoke${stamp}!`
    })
  });
  return {
    token: login.access_token,
    tenantId: login.user.tenant.id
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
  return new Promise((resolve, reject) => {
    ws.addEventListener("message", (event) => {
      const msg = JSON.parse(event.data);
      if (msg.id && pending.has(msg.id)) {
        const item = pending.get(msg.id);
        pending.delete(msg.id);
        if (msg.error) item.reject(new Error(JSON.stringify(msg.error)));
        else item.resolve(msg.result || {});
      }
    });
    ws.addEventListener("open", () => {
      resolve({
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

async function captureScreenshot(cdp) {
  const screenshot = await cdp.send("Page.captureScreenshot", {
    format: "png",
    captureBeyondViewport: true
  });
  fs.writeFileSync(screenshotPath, Buffer.from(screenshot.data, "base64"));
}

async function runBrowserSmoke(token) {
  await startChrome();
  const target = await createTarget(frontendUrl);
  const cdp = await createCdp(target.webSocketDebuggerUrl);
  try {
    await cdp.send("Runtime.enable");
    await cdp.send("Page.enable");
    await cdp.send("Emulation.setDeviceMetricsOverride", {
      width: 1440,
      height: 1000,
      deviceScaleFactor: 1,
      mobile: false
    });
    await cdp.send("Page.navigate", { url: frontendUrl });
    await waitForExpression(cdp, "document.readyState === 'complete' || document.readyState === 'interactive'");
    await evalValue(
      cdp,
      `localStorage.setItem('wanfa_standard_ops_access_token', ${JSON.stringify(token)}); location.href = ${JSON.stringify(frontendUrl)}; true`
    );
    await waitForExpression(cdp, "document.body.innerText.includes('知识评测中心')", 15000);
    await waitForExpression(cdp, "Boolean(document.querySelector('[data-question-bank-import=\"p3-06u-26h2o\"]'))", 15000);
    await evalValue(
      cdp,
      `(() => {
        const panel = document.querySelector('[data-question-bank-import="p3-06u-26h2o"]');
        panel?.scrollIntoView({ block: 'center' });
        const button = Array.from(panel?.querySelectorAll('button') || []).find((item) => item.textContent.includes('预检题库'));
        if (!button) return false;
        button.click();
        return true;
      })()`
    );
    await waitForExpression(cdp, "document.body.innerText.includes('预检通过：50 题')", 15000);
    const precheckConfirmed = await evalValue(cdp, "document.body.innerText.includes('预检通过：50 题')");
    await evalValue(
      cdp,
      `(() => {
        const panel = document.querySelector('[data-question-bank-import="p3-06u-26h2o"]');
        const button = Array.from(panel?.querySelectorAll('button') || []).find((item) => item.textContent.includes('导入题库'));
        if (!button || button.disabled) return false;
        button.click();
        return true;
      })()`
    );
    await waitForExpression(cdp, "document.body.innerText.includes('已导入 50 题')", 15000);
    await waitForExpression(cdp, "document.body.innerText.includes('客户试点脱敏题库 50 题')", 15000);
    await captureScreenshot(cdp);
    const inspection = await evalValue(
      cdp,
      `(() => {
        const body = document.body.innerText;
        const result = document.querySelector('[data-question-bank-result="p3-06u-26h2o"]');
        return {
          hasEvals: body.includes('知识评测中心'),
          hasQuestionBankPanel: Boolean(document.querySelector('[data-question-bank-import="p3-06u-26h2o"]')),
          hasPrecheckMessage: ${JSON.stringify(precheckConfirmed)},
          hasImportMessage: body.includes('已导入 50 题'),
          hasResult: Boolean(result),
          resultText: result ? result.innerText : '',
          rawSecretVisible: body.includes('H2OSmoke'),
          unsafeExternalWriteClaim: body.includes('真实外发已开启')
        };
      })()`
    );
    if (!inspection.hasEvals || !inspection.hasQuestionBankPanel || !inspection.hasPrecheckMessage || !inspection.hasImportMessage || !inspection.hasResult) {
      throw new Error(`Customer question bank UI smoke missing expected content: ${JSON.stringify(inspection)}`);
    }
    if (inspection.rawSecretVisible || inspection.unsafeExternalWriteClaim) {
      throw new Error(`Customer question bank UI smoke found unsafe text: ${JSON.stringify(inspection)}`);
    }
    return {
      ...inspection,
      resultText: undefined,
      resultHasRawQuestion: inspection.resultText.includes("客户第1个脱敏问题")
    };
  } finally {
    cdp.close();
    await fetch(`${chromeEndpoint}/json/close/${target.id}`).catch(() => undefined);
  }
}

async function inspectImportedSet(token, tenantId) {
  const sets = await requestJson(`/api/tenants/${tenantId}/knowledge-evaluation-sets`, {
    headers: { authorization: `Bearer ${token}` }
  });
  const imported = sets.items.find((item) => item.name === "客户试点脱敏题库 50 题");
  if (!imported) {
    throw new Error("Imported evaluation set not found");
  }
  return {
    evaluation_set_id: imported.id,
    name: imported.name,
    case_count: imported.case_count
  };
}

function cleanup() {
  for (const child of children.reverse()) {
    try {
      child.kill("SIGTERM");
    } catch {
      // ignore cleanup errors
    }
  }
  for (let attempt = 0; attempt < 6; attempt += 1) {
    try {
      fs.rmSync(chromeProfile, { recursive: true, force: true });
      break;
    } catch (error) {
      if (attempt === 5) {
        throw error;
      }
      Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, 250);
    }
  }
  fs.rmSync(dbPath, { force: true });
}

async function main() {
  try {
    await startServices();
    const owner = await createLocalOwner();
    const inspection = await runBrowserSmoke(owner.token);
    const importedSet = await inspectImportedSet(owner.token, owner.tenantId);
    if (importedSet.case_count !== 50 || inspection.resultHasRawQuestion) {
      throw new Error(`Imported set inspection failed: ${JSON.stringify({ importedSet, inspection })}`);
    }
    const summary = {
      ok: true,
      frontendUrl,
      backendUrl,
      screenshot: screenshotPath,
      tenant_id: owner.tenantId,
      importedSet,
      inspection,
      token_persisted: false,
      raw_result_text_included: false,
      model_call_performed: false,
      external_platform_write_performed: false
    };
    fs.writeFileSync(summaryPath, JSON.stringify(summary, null, 2));
    console.log("PASS p3-06u-26h2o customer question bank import UI smoke");
    console.log(`summary: ${summaryPath}`);
    console.log(`screenshot: ${screenshotPath}`);
  } finally {
    cleanup();
  }
}

main().catch((error) => {
  cleanup();
  console.error(error);
  process.exit(1);
});
