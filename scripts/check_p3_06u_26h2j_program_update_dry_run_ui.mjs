import crypto from "node:crypto";
import fs from "node:fs";
import path from "node:path";
import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";

const rootDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const outputDir = path.resolve(
  process.env.P3_06U_26H2J_OUTPUT ?? path.join(rootDir, "output/p3_06u_26h2j_program_update_dry_run_ui")
);
const backendPort = Number(process.env.P3_06U_26H2J_BACKEND_PORT ?? 8097);
const frontendPort = Number(process.env.P3_06U_26H2J_FRONTEND_PORT ?? 5197);
const chromePort = Number(process.env.P3_06U_26H2J_CHROME_PORT ?? 9237);
const backendUrl = `http://127.0.0.1:${backendPort}`;
const frontendUrl = `http://127.0.0.1:${frontendPort}/#settings`;
const chromeEndpoint = `http://127.0.0.1:${chromePort}`;
const dbPath = path.join(outputDir, "program_dry_run_smoke.sqlite");
const backupDir = path.join(outputDir, "local_backups");
const chromeProfile = path.join(outputDir, "chrome-profile");
const screenshotPath = path.join(outputDir, "program-dry-run-update-center.png");
const debugScreenshotPath = path.join(outputDir, "program-dry-run-debug.png");
const debugStatePath = path.join(outputDir, "debug-state.json");
const summaryPath = path.join(outputDir, "summary.json");
const pythonBin = path.join(rootDir, "backend/.venv/bin/python");

const children = [];

function ensureOutputDir() {
  fs.mkdirSync(outputDir, { recursive: true });
  fs.mkdirSync(backupDir, { recursive: true });
  fs.rmSync(chromeProfile, { recursive: true, force: true });
}

function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function stripPemNewlines(value) {
  return value.replace(/\r/g, "");
}

function canonicalJson(value) {
  if (value === null || typeof value !== "object") {
    return JSON.stringify(value);
  }
  if (Array.isArray(value)) {
    return `[${value.map((item) => canonicalJson(item)).join(",")}]`;
  }
  return `{${Object.keys(value)
    .sort()
    .map((key) => `${JSON.stringify(key)}:${canonicalJson(value[key])}`)
    .join(",")}}`;
}

function sha256Hex(value) {
  return crypto.createHash("sha256").update(value).digest("hex");
}

function createSignedProgramPackage(privateKey) {
  const payload = {
    schema_version: "wanfa.program_update_package.v1",
    program_version: "0.1.1",
    bundle: {
      bundle_id: "wanfa-standard-ops-0.1.1-local-smoke",
      platforms: ["darwin-arm64", "win32-x64"],
      size_bytes: 2048,
      sha256: "f".repeat(64)
    },
    files: [
      {
        path: "backend/app/main.py",
        sha256: "a".repeat(64),
        size_bytes: 1024
      },
      {
        path: "frontend/dist/index.html",
        sha256: "b".repeat(64),
        size_bytes: 1024
      }
    ],
    migrations: [
      {
        id: "0030_program_update_placeholder",
        mode: "dry_run_required",
        description: "只生成程序更新演练计划，不执行迁移。"
      }
    ],
    services: ["backend", "frontend"],
    rollback: {
      requires_previous_bundle: true,
      requires_database_backup: true
    }
  };
  const payloadBytes = canonicalJson(payload);
  const manifest = {
    schema_version: "wanfa.signed_update_manifest.v1",
    package_id: "wanfa-update-program-dry-run-ui-001",
    package_name: "本地程序更新演练包",
    package_type: "program",
    package_version: "2026.07.03.program.1",
    product: "wanfa-standard-ops",
    released_at: "2026-07-03T18:00:00+08:00",
    compatible_app_versions: ["0.1.0"],
    requires_maintenance_window: true,
    payload_digest_sha256: sha256Hex(payloadBytes),
    payload_size_bytes: Buffer.byteLength(payloadBytes),
    operations: [
      {
        target: "program_bundle",
        action: "upsert",
        count: 1,
        summary: "程序版本升级演练"
      }
    ]
  };
  const signature = crypto.sign("RSA-SHA256", Buffer.from(canonicalJson(manifest)), privateKey).toString("base64");
  return {
    schema_version: "wanfa.signed_update_package.v1",
    manifest,
    payload,
    release_notes: "本更新包只用于程序更新演练，不替换文件、不执行迁移、不重启服务。",
    checksums: {
      payload_sha256: manifest.payload_digest_sha256
    },
    signature: {
      algorithm: "rsa_pkcs1v15_sha256",
      key_id: "h2j-smoke-release-key",
      value: signature
    }
  };
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
      if (code === 0) {
        resolve(output);
      } else {
        reject(new Error(`${command} ${args.join(" ")} exited ${code}\n${output}`));
      }
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

async function startServices(publicKeyPem) {
  fs.rmSync(dbPath, { force: true });
  await runCommand(pythonBin, ["scripts/repair_local_sqlite_schema.py", "--db", dbPath], {
    cwd: rootDir
  });
  const env = {
    ...process.env,
    DATABASE_URL: `sqlite+pysqlite:///${dbPath}`,
    STANDARD_OPS_ENV: "development",
    STANDARD_OPS_ALLOWED_ORIGINS: `http://127.0.0.1:${frontendPort},http://localhost:${frontendPort}`,
    WANFA_UPDATE_TRUSTED_PUBLIC_KEYS_JSON: JSON.stringify({
      "h2j-smoke-release-key": stripPemNewlines(publicKeyPem)
    }),
    WANFA_LOCAL_BACKUP_DIR: backupDir,
    OUTBOX_EXTERNAL_WRITE_ENABLED: "false"
  };
  spawnLongRunning(
    "backend",
    pythonBin,
    ["-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", String(backendPort)],
    { cwd: path.join(rootDir, "backend"), env }
  );
  await waitForHttp(`${backendUrl}/health`);
  spawnLongRunning(
    "frontend",
    "npm",
    ["run", "dev", "--", "--host", "127.0.0.1", "--port", String(frontendPort)],
    {
      cwd: path.join(rootDir, "frontend"),
      env: {
        ...process.env,
        VITE_API_PROXY_TARGET: backendUrl
      }
    }
  );
  await waitForHttp(`http://127.0.0.1:${frontendPort}/`);
}

function chromeBinary() {
  const candidates = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium"
  ];
  const found = candidates.find((candidate) => fs.existsSync(candidate));
  if (!found) {
    throw new Error("Chrome binary not found");
  }
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
  if (!response.ok) {
    throw new Error(`Failed to create Chrome target: ${response.status}`);
  }
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
  if (result.exceptionDetails) {
    throw new Error(JSON.stringify(result.exceptionDetails));
  }
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

async function runBrowserSmoke(signedPackage) {
  await startChrome();
  const target = await createTarget(frontendUrl);
  const cdp = await createCdp(target.webSocketDebuggerUrl);
  try {
    await cdp.send("Runtime.enable");
    await cdp.send("Page.enable");
    await cdp.send("Emulation.setDeviceMetricsOverride", {
      width: 1440,
      height: 1100,
      deviceScaleFactor: 1,
      mobile: false
    });
    await cdp.waitFor("Page.loadEventFired", 10000).catch(() => undefined);
    await waitForExpression(cdp, "Boolean(document.querySelector('[data-role-smoke=\"local-owner-setup\"]'))");
    const ownerPayload = {
      tenant_slug: `h2j-local-${Date.now()}`,
      tenant_name: "H2J 程序演练本地空间",
      owner_name: "H2J 管理员",
      email: `h2j-owner-${Date.now()}@wanfa.local`,
      password: `H2JSmoke${Date.now()}!`
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
          if (input) {
            setValue(input, value);
          }
        }
        document.querySelector('[data-role-smoke="local-owner-setup"]').click();
        return true;
      })()`
    );
    await waitForExpression(cdp, "location.hash === '#overview' || location.hash === '#settings'", 12000);
    await waitForExpression(cdp, "document.body.innerText.includes('管理员视图') && Boolean(document.querySelector('[data-workspace-nav=\"ops\"]'))", 12000);
    await evalValue(
      cdp,
      `(() => {
        const ops = document.querySelector('[data-workspace-nav="ops"]');
        if (ops) ops.click();
        const settings = document.querySelector('a[data-workspace-nav="settings"], a[href="#settings"]');
        if (settings) settings.click();
        window.history.pushState(null, '', '#settings');
        window.dispatchEvent(new HashChangeEvent('hashchange'));
        return { hash: location.hash, clicked: Boolean(settings), hasOps: Boolean(ops) };
      })()`
    );
    try {
      await waitForExpression(cdp, "Boolean(document.querySelector('[data-role-smoke=\"signed-update-center\"]'))", 12000);
    } catch (error) {
      const debugState = await evalValue(
        cdp,
        `(() => ({
          hash: location.hash,
          title: document.title,
          hasLogin: Boolean(document.querySelector('[data-role-smoke="login-form"]')),
          navSettings: Boolean(document.querySelector('[data-workspace-nav="settings"]')),
          accountPanel: Boolean(document.querySelector('#workspace-settings')),
          bodyText: document.body.innerText.slice(0, 2000)
        }))()`
      );
      fs.writeFileSync(debugStatePath, JSON.stringify(debugState, null, 2));
      await captureScreenshot(cdp, debugScreenshotPath);
      throw error;
    }
    await evalValue(
      cdp,
      `(() => {
        const textarea = document.querySelector('[data-role-smoke="signed-update-package-input"]');
        const setter = Object.getOwnPropertyDescriptor(Object.getPrototypeOf(textarea), 'value')?.set;
        setter.call(textarea, ${JSON.stringify(JSON.stringify(signedPackage, null, 2))});
        textarea.dispatchEvent(new InputEvent('input', { bubbles: true, inputType: 'insertText' }));
        return true;
      })()`
    );
    await evalValue(cdp, "document.querySelector('[data-role-smoke=\"signed-update-preflight\"]').click(); true");
    await waitForExpression(cdp, "document.body.innerText.includes('预检通过')", 12000);
    await waitForExpression(
      cdp,
      "Boolean(document.querySelector('[data-role-smoke=\"signed-update-stage\"]')) && !document.querySelector('[data-role-smoke=\"signed-update-stage\"]').disabled",
      12000
    );
    await evalValue(cdp, "document.querySelector('[data-role-smoke=\"signed-update-stage\"]').click(); true");
    await waitForExpression(cdp, "document.body.innerText.includes('本地程序更新演练包')", 12000);
    await waitForExpression(cdp, "Boolean(document.querySelector('[data-role-smoke=\"signed-update-program-dry-run\"]'))", 12000);
    await evalValue(cdp, "document.querySelector('[data-role-smoke=\"signed-update-program-dry-run\"]').click(); true");
    await waitForExpression(cdp, "Boolean(document.querySelector('[data-role-smoke=\"signed-update-program-dry-run-result\"]'))", 12000);
    const inspection = await evalValue(
      cdp,
      `(() => {
        const result = document.querySelector('[data-role-smoke="signed-update-program-dry-run-result"]');
        const applyButtons = Array.from(document.querySelectorAll('[data-role-smoke="signed-update-apply"]')).map((item) => item.innerText.trim());
        const bodyText = document.body.innerText;
        return {
          resultText: result ? result.innerText : "",
          hasProgramDryRunButton: Boolean(document.querySelector('[data-role-smoke="signed-update-program-dry-run"]')),
          applyButtonCount: applyButtons.length,
          applyButtons,
          containsBlockedActions: bodyText.includes('已阻断'),
          containsMaintenanceWindow: bodyText.includes('需要维护窗口'),
          containsNoFileReplacementCopy: bodyText.includes('不替换文件'),
          statusStillStaged: bodyText.includes('待应用')
        };
      })()`
    );
    if (!inspection.resultText.includes("已生成")) {
      throw new Error(`Program dry-run result is missing generated status: ${inspection.resultText}`);
    }
    if (!inspection.containsBlockedActions || !inspection.containsMaintenanceWindow || !inspection.containsNoFileReplacementCopy) {
      throw new Error(`Program dry-run safety copy is incomplete: ${JSON.stringify(inspection)}`);
    }
    if (inspection.applyButtonCount !== 0) {
      throw new Error(`Program package should not show apply button, got ${inspection.applyButtons.join(", ")}`);
    }
    if (!inspection.statusStillStaged) {
      throw new Error("Program package should remain staged after rehearsal plan");
    }
    await evalValue(
      cdp,
      `(() => {
        document.querySelector('[data-role-smoke="signed-update-program-dry-run-result"]')?.scrollIntoView({ block: 'center' });
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
  const { publicKey, privateKey } = crypto.generateKeyPairSync("rsa", {
    modulusLength: 2048,
    publicKeyEncoding: { type: "spki", format: "pem" },
    privateKeyEncoding: { type: "pkcs8", format: "pem" }
  });
  const signedPackage = createSignedProgramPackage(privateKey);
  await startServices(publicKey);
  const inspection = await runBrowserSmoke(signedPackage);
  fs.writeFileSync(
    summaryPath,
    JSON.stringify(
      {
        ok: true,
        frontendUrl,
        backendUrl,
        screenshot: screenshotPath,
        package_id: signedPackage.manifest.package_id,
        package_type: signedPackage.manifest.package_type,
        private_key_persisted: false,
        token_persisted: false,
        inspection
      },
      null,
      2
    )
  );
  console.log(`PASS p3-06u-26h2j program update dry-run UI smoke`);
  console.log(`summary: ${summaryPath}`);
  console.log(`screenshot: ${screenshotPath}`);
  cleanup();
}

process.on("exit", cleanup);
process.on("SIGINT", () => {
  cleanup();
  process.exit(130);
});
process.on("SIGTERM", () => {
  cleanup();
  process.exit(143);
});

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
