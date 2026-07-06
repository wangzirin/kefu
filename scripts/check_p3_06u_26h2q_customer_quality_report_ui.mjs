import fs from "node:fs";
import path from "node:path";
import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";

const rootDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const outputDir = path.resolve(process.env.P3_06U_26H2Q_OUTPUT ?? path.join(rootDir, "output/p3_06u_26h2q_customer_quality_report_ui"));
const backendPort = Number(process.env.P3_06U_26H2Q_BACKEND_PORT ?? 8106);
const frontendPort = Number(process.env.P3_06U_26H2Q_FRONTEND_PORT ?? 5206);
const chromePort = Number(process.env.P3_06U_26H2Q_CHROME_PORT ?? 9246);
const backendUrl = `http://127.0.0.1:${backendPort}`;
const frontendUrl = `http://127.0.0.1:${frontendPort}/#quality`;
const chromeEndpoint = `http://127.0.0.1:${chromePort}`;
const dbPath = path.join(outputDir, "customer_quality_report_smoke.sqlite");
const chromeProfile = path.join(outputDir, "chrome-profile");
const screenshotPath = path.join(outputDir, "customer-quality-report.png");
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
    child.stdout.on("data", (chunk) => { output += chunk.toString(); });
    child.stderr.on("data", (chunk) => { output += chunk.toString(); });
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
  spawnLongRunning("frontend", "npm", ["run", "dev", "--", "--host", "127.0.0.1", "--port", String(frontendPort)], {
    cwd: path.join(rootDir, "frontend"),
    env: { ...process.env, VITE_API_PROXY_TARGET: backendUrl }
  });
  await waitForHttp(`http://127.0.0.1:${frontendPort}/`);
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
        const waiter = pending.get(msg.id);
        pending.delete(msg.id);
        if (msg.error) waiter.reject(new Error(JSON.stringify(msg.error)));
        else waiter.resolve(msg.result || {});
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

async function waitForExpression(cdp, expression, timeoutMs = 12000) {
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

async function runBrowserSmoke() {
  await startChrome();
  const target = await createTarget(frontendUrl);
  const cdp = await createCdp(target.webSocketDebuggerUrl);
  try {
    await cdp.send("Runtime.enable");
    await cdp.send("Page.enable");
    await cdp.send("Emulation.setDeviceMetricsOverride", { width: 1440, height: 1000, deviceScaleFactor: 1, mobile: false });
    await cdp.send("Page.navigate", { url: frontendUrl });
    await waitForExpression(cdp, "Boolean(document.querySelector('[data-role-smoke=\"local-owner-setup\"]'))");
    const stamp = Date.now();
    const ownerPayload = {
      tenant_slug: `h2q-quality-${stamp}`,
      tenant_name: "H2Q 客户质量报告空间",
      owner_name: "H2Q 管理员",
      email: `h2q-owner-${stamp}@wanfa.local`,
      password: `H2QSmoke${stamp}!`
    };
    await evalValue(cdp, `(() => {
      const data = ${JSON.stringify(ownerPayload)};
      const setValue = (input, value) => {
        const setter = Object.getOwnPropertyDescriptor(Object.getPrototypeOf(input), 'value')?.set;
        setter.call(input, value);
        input.dispatchEvent(new InputEvent('input', { bubbles: true, inputType: 'insertText', data: String(value) }));
      };
      for (const [name, value] of Object.entries(data)) {
        const input = document.querySelector('[name="' + name + '"]');
        if (input) setValue(input, value);
      }
      document.querySelector('[data-role-smoke="local-owner-setup"]').click();
      return true;
    })()`);
    await waitForExpression(cdp, "document.body.innerText.includes('管理员视图')", 12000);
    await evalValue(cdp, `(() => {
      const link = document.querySelector('a[data-workspace-nav="quality"], a[href="#quality"]');
      if (link) link.click();
      window.history.pushState(null, '', '#quality');
      window.dispatchEvent(new HashChangeEvent('hashchange'));
      return true;
    })()`);
    await waitForExpression(cdp, "Boolean(document.querySelector('[data-quality-smoke=\"customer-quality-report\"]'))", 12000);
    await waitForExpression(cdp, "document.querySelector('[data-quality-smoke=\"customer-quality-report\"]')?.innerText.includes('客户可读质量报告')", 12000);
    const inspection = await evalValue(cdp, `(() => {
      const panel = document.querySelector('[data-quality-smoke="customer-quality-report"]');
      const text = panel?.innerText || '';
      const body = document.body.innerText;
      return {
        hasPanel: Boolean(panel),
        hasReportTitle: text.includes('客服质量报告'),
        hasBoundary: text.includes('不展示原始客户问题') || text.includes('签收边界'),
        hasSampleWarning: text.includes('样本不足') || text.includes('待补'),
        hasMetric: text.includes('最终回复采样') || text.includes('人工事实性'),
        rawPasswordVisible: body.includes('H2QSmoke'),
        externalWriteEnabled: body.includes('真实外发已开启')
      };
    })()`);
    if (!inspection.hasPanel || !inspection.hasReportTitle || !inspection.hasBoundary || !inspection.hasSampleWarning || !inspection.hasMetric) {
      throw new Error(`Customer quality report UI missing expected content: ${JSON.stringify(inspection)}`);
    }
    if (inspection.rawPasswordVisible || inspection.externalWriteEnabled) {
      throw new Error(`Customer quality report UI leaked unsafe state: ${JSON.stringify(inspection)}`);
    }
    await evalValue(cdp, `document.querySelector('[data-quality-smoke="customer-quality-report"]')?.scrollIntoView({ block: 'center' }); true`);
    await delay(400);
    await captureScreenshot(cdp);
    return inspection;
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
  await startServices();
  const inspection = await runBrowserSmoke();
  fs.writeFileSync(summaryPath, JSON.stringify({
    ok: true,
    frontendUrl,
    backendUrl,
    screenshot: screenshotPath,
    token_persisted: false,
    model_call_performed: false,
    external_platform_write_performed: false,
    inspection
  }, null, 2));
  console.log("PASS p3-06u-26h2q customer quality report UI smoke");
  console.log(`summary: ${summaryPath}`);
  console.log(`screenshot: ${screenshotPath}`);
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
  });
