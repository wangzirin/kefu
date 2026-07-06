import fs from "node:fs";
import path from "node:path";
import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";

const rootDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const outputDir = path.resolve(
  process.env.P3_06U_26H2K_OUTPUT ?? path.join(rootDir, "output/p3_06u_26h2k_diagnostic_upload_package_ui")
);
const backendPort = Number(process.env.P3_06U_26H2K_BACKEND_PORT ?? 8098);
const frontendPort = Number(process.env.P3_06U_26H2K_FRONTEND_PORT ?? 5198);
const chromePort = Number(process.env.P3_06U_26H2K_CHROME_PORT ?? 9238);
const backendUrl = `http://127.0.0.1:${backendPort}`;
const frontendUrl = `http://127.0.0.1:${frontendPort}/#settings`;
const chromeEndpoint = `http://127.0.0.1:${chromePort}`;
const dbPath = path.join(outputDir, "diagnostic_upload_smoke.sqlite");
const chromeProfile = path.join(outputDir, "chrome-profile");
const screenshotPath = path.join(outputDir, "diagnostic-upload-package.png");
const summaryPath = path.join(outputDir, "summary.json");
const pythonBin = path.join(rootDir, "backend/.venv/bin/python");
const children = [];

function ensureOutputDir() {
  fs.mkdirSync(outputDir, { recursive: true });
  fs.rmSync(chromeProfile, { recursive: true, force: true });
  for (const file of fs.readdirSync(outputDir)) {
    if (file.startsWith("wanfa-diagnostic-upload-")) {
      fs.rmSync(path.join(outputDir, file), { force: true });
    }
  }
}

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
  child.on("exit", (code) => {
    log.write(`\n[${name}] exited ${code}\n`);
  });
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
  fs.rmSync(dbPath, { force: true });
  await runCommand(pythonBin, ["scripts/repair_local_sqlite_schema.py", "--db", dbPath], {
    cwd: rootDir
  });
  const env = {
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
    { cwd: path.join(rootDir, "backend"), env }
  );
  await waitForHttp(`${backendUrl}/health`);
  spawnLongRunning("frontend", "npm", ["run", "dev", "--", "--host", "127.0.0.1", "--port", String(frontendPort)], {
    cwd: path.join(rootDir, "frontend"),
    env: {
      ...process.env,
      VITE_API_PROXY_TARGET: backendUrl
    }
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
  const events = [];
  ws.addEventListener("message", (event) => {
    const msg = JSON.parse(event.data);
    if (msg.id && pending.has(msg.id)) {
      const { resolve, reject } = pending.get(msg.id);
      pending.delete(msg.id);
      if (msg.error) reject(new Error(JSON.stringify(msg.error)));
      else resolve(msg.result || {});
      return;
    }
    if (msg.method) events.push(msg);
  });
  return new Promise((resolve, reject) => {
    ws.addEventListener("open", () => {
      resolve({
        send(method, params = {}) {
          const callId = ++id;
          ws.send(JSON.stringify({ id: callId, method, params }));
          return new Promise((resolve, reject) => pending.set(callId, { resolve, reject }));
        },
        waitFor(method, timeout = 8000) {
          return new Promise((resolve, reject) => {
            const existing = events.findIndex((item) => item.method === method);
            if (existing >= 0) {
              resolve(events.splice(existing, 1)[0]);
              return;
            }
            const timer = setTimeout(() => reject(new Error(`Timed out waiting for ${method}`)), timeout);
            const listener = (event) => {
              const msg = JSON.parse(event.data);
              if (msg.method === method) {
                clearTimeout(timer);
                ws.removeEventListener("message", listener);
                resolve(msg);
              }
            };
            ws.addEventListener("message", listener);
          });
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

async function captureScreenshot(cdp, filePath) {
  const screenshot = await cdp.send("Page.captureScreenshot", {
    format: "png",
    captureBeyondViewport: true
  });
  fs.writeFileSync(filePath, Buffer.from(screenshot.data, "base64"));
}

async function waitForDownloadedUploadPackage(timeoutMs = 12000) {
  const started = Date.now();
  while (Date.now() - started < timeoutMs) {
    const files = fs
      .readdirSync(outputDir)
      .filter((file) => file.startsWith("wanfa-diagnostic-upload-") && file.endsWith(".json"));
    if (files.length > 0) {
      const filePath = path.join(outputDir, files.sort().at(-1));
      const payload = JSON.parse(fs.readFileSync(filePath, "utf8"));
      return { filePath, payload };
    }
    await delay(250);
  }
  throw new Error("Timed out waiting for diagnostic upload package download");
}

async function runBrowserSmoke() {
  await startChrome();
  const target = await createTarget(frontendUrl);
  const cdp = await createCdp(target.webSocketDebuggerUrl);
  try {
    await cdp.send("Runtime.enable");
    await cdp.send("Page.enable");
    await cdp.send("Browser.setDownloadBehavior", { behavior: "allow", downloadPath: outputDir }).catch(() =>
      cdp.send("Page.setDownloadBehavior", { behavior: "allow", downloadPath: outputDir })
    );
    await cdp.send("Emulation.setDeviceMetricsOverride", {
      width: 1440,
      height: 1000,
      deviceScaleFactor: 1,
      mobile: false
    });
    await cdp.waitFor("Page.loadEventFired", 10000).catch(() => undefined);
    await waitForExpression(cdp, "Boolean(document.querySelector('[data-role-smoke=\"local-owner-setup\"]'))");
    const ownerPayload = {
      tenant_slug: `h2k-local-${Date.now()}`,
      tenant_name: "H2K 诊断上传本地空间",
      owner_name: "H2K 管理员",
      email: `h2k-owner-${Date.now()}@wanfa.local`,
      password: `H2KSmoke${Date.now()}!`
    };
    await evalValue(
      cdp,
      `(() => {
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
      })()`
    );
    await waitForExpression(cdp, "document.body.innerText.includes('管理员视图')", 12000);
    await evalValue(
      cdp,
      `(() => {
        const ops = document.querySelector('[data-workspace-nav="ops"]');
        if (ops) ops.click();
        const settings = document.querySelector('a[data-workspace-nav="settings"], a[href="#settings"]');
        if (settings) settings.click();
        window.history.pushState(null, '', '#settings');
        window.dispatchEvent(new HashChangeEvent('hashchange'));
        return true;
      })()`
    );
    await waitForExpression(cdp, "Boolean(document.querySelector('[data-role-smoke=\"diagnostic-upload-package\"]'))", 12000);
    await evalValue(cdp, "document.querySelector('[data-role-smoke=\"diagnostic-upload-package\"]').click(); true");
    await waitForExpression(cdp, "document.body.innerText.includes('授权上传包已生成并下载')", 12000);
    const download = await waitForDownloadedUploadPackage();
    const serialized = JSON.stringify(download.payload).toLowerCase();
    const inspection = {
      filePath: download.filePath,
      schemaVersion: download.payload.schema_version,
      transferMode: download.payload.upload_manifest?.transfer_mode,
      externalUploadPerformed: download.payload.safety?.external_upload_performed,
      networkRequestPerformed: download.payload.safety?.network_request_performed,
      customerAuthorizationRecorded: download.payload.safety?.customer_authorization_recorded,
      manualTransferRequired: download.payload.safety?.manual_transfer_required,
      hasDiagnosticBundle: Boolean(download.payload.diagnostic_bundle),
      hasDigest: typeof download.payload.upload_manifest?.diagnostic_bundle_sha256 === "string",
      containsSecretMarkers: /private key|access_token|bearer |cookie|password|13800138000|wxid_/i.test(serialized)
    };
    if (inspection.schemaVersion !== "p3-06u-26h2k.v1") {
      throw new Error(`Unexpected upload package schema: ${inspection.schemaVersion}`);
    }
    if (inspection.transferMode !== "manual_transfer_package") {
      throw new Error(`Unexpected transfer mode: ${inspection.transferMode}`);
    }
    if (inspection.externalUploadPerformed !== false || inspection.networkRequestPerformed !== false) {
      throw new Error(`Upload package must not perform external upload: ${JSON.stringify(inspection)}`);
    }
    if (!inspection.customerAuthorizationRecorded || !inspection.manualTransferRequired || !inspection.hasDiagnosticBundle || !inspection.hasDigest) {
      throw new Error(`Upload package missing authorization or bundle evidence: ${JSON.stringify(inspection)}`);
    }
    if (inspection.containsSecretMarkers) {
      throw new Error(`Upload package contains sensitive markers: ${download.filePath}`);
    }
    await evalValue(
      cdp,
      `(() => {
        document.querySelector('[data-role-smoke="diagnostic-upload-package"]')?.scrollIntoView({ block: 'center' });
        return true;
      })()`
    );
    await delay(400);
    await captureScreenshot(cdp, screenshotPath);
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
  ensureOutputDir();
  await startServices();
  const inspection = await runBrowserSmoke();
  fs.writeFileSync(
    summaryPath,
    JSON.stringify(
      {
        ok: true,
        frontendUrl,
        backendUrl,
        screenshot: screenshotPath,
        downloadedUploadPackage: inspection.filePath,
        token_persisted: false,
        external_upload_performed: inspection.externalUploadPerformed,
        network_request_performed: inspection.networkRequestPerformed,
        inspection
      },
      null,
      2
    )
  );
  console.log("PASS p3-06u-26h2k diagnostic upload package UI smoke");
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
