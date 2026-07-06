import crypto from "node:crypto";
import fs from "node:fs";
import path from "node:path";
import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";

const rootDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const outputDir = path.resolve(
  process.env.P3_06U_26H2W8B_OUTPUT ?? path.join(rootDir, "output/p3_06u_26h2w8b_local_maintenance_ui")
);
const backendPort = Number(process.env.P3_06U_26H2W8B_BACKEND_PORT ?? 8138);
const frontendPort = Number(process.env.P3_06U_26H2W8B_FRONTEND_PORT ?? 5238);
const chromePort = Number(process.env.P3_06U_26H2W8B_CHROME_PORT ?? 9278);
const backendUrl = `http://127.0.0.1:${backendPort}`;
const frontendBaseUrl = `http://127.0.0.1:${frontendPort}/`;
const chromeEndpoint = `http://127.0.0.1:${chromePort}`;
const dbPath = path.join(outputDir, "h2w8b_local_maintenance.sqlite");
const localBackupDir = path.join(outputDir, "local-backups");
const chromeProfile = path.join(outputDir, "chrome-profile");
const pythonBin = path.join(rootDir, "backend/.venv/bin/python");
const tokenStorageKey = "wanfa_standard_ops_access_token";
const children = [];

function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function canonicalJson(value) {
  if (value === null || typeof value !== "object") return JSON.stringify(value);
  if (Array.isArray(value)) return `[${value.map((item) => canonicalJson(item)).join(",")}]`;
  return `{${Object.keys(value)
    .sort()
    .map((key) => `${JSON.stringify(key)}:${canonicalJson(value[key])}`)
    .join(",")}}`;
}

function sha256Hex(value) {
  return crypto.createHash("sha256").update(value).digest("hex");
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

async function waitForHttp(url, timeoutMs = 30000) {
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

function createSignedKnowledgePackage(privateKeyPem) {
  const payload = {
    schema_version: "wanfa.knowledge_update_package.v1",
    package_id: "h2w8b-ui-knowledge-payload",
    package_name: "H2W8B 本地维护知识修复包",
    source_diagnostic_filename: "wanfa-diagnostic-h2w8b.json",
    notes: "浏览器 smoke 使用的本地维护知识修复包。",
    business_objects: [
      {
        ref: "h2w8b-local-maintenance",
        type: "service",
        title: "本地维护闭环",
        aliases: ["诊断包", "备份恢复", "签名更新"],
        summary: "用于验证本地诊断、售后接收、更新计划、备份和恢复演练。",
        status: "active"
      }
    ],
    object_knowledge_cards: [
      {
        business_object_ref: "h2w8b-local-maintenance",
        question: "客户本地部署后如何维护？",
        answer:
          "客户可在本地工作台生成诊断包、登记售后接收、校验签名更新包，并在更新前创建备份和恢复演练；真实外发继续关闭。",
        trigger_keywords: ["本地维护", "诊断包", "更新"],
        source: "h2w8b_ui_smoke",
        status: "active"
      }
    ],
    knowledge_documents: [
      {
        title: "H2W8B 本地维护 smoke 知识文档",
        source_type: "signed_update_package",
        source_uri: "internal://h2w8b/local-maintenance",
        tags: ["H2W8B", "本地维护"],
        status: "active",
        raw_text:
          "本地维护闭环必须包含诊断接收、售后处理单、签名更新包、已校验备份、恢复演练和审计证据；不能自动上传、远控或静默更新。"
      }
    ],
    evaluation_sets: []
  };
  const payloadJson = canonicalJson(payload);
  const manifest = {
    schema_version: "wanfa.signed_update_manifest.v1",
    package_id: "h2w8b-ui-knowledge-update",
    package_name: "H2W8B 本地维护知识修复包",
    package_type: "knowledge",
    package_version: "2026.07.04.h2w8b.ui",
    product: "wanfa-standard-ops",
    released_at: "2026-07-04T15:00:00+08:00",
    compatible_app_versions: ["0.1.0"],
    requires_maintenance_window: false,
    payload_digest_sha256: sha256Hex(payloadJson),
    payload_size_bytes: Buffer.byteLength(payloadJson),
    operations: [
      {
        target: "knowledge_documents",
        action: "upsert",
        count: 1,
        summary: "补充本地维护闭环知识说明"
      }
    ]
  };
  const manifestJson = canonicalJson(manifest);
  const signature = crypto.sign("RSA-SHA256", Buffer.from(manifestJson), privateKeyPem).toString("base64");
  return {
    schema_version: "wanfa.signed_update_package.v1",
    manifest,
    payload,
    release_notes: "H2W8B UI smoke 使用；只验证本地维护闭环。",
    checksums: { payload_sha256: manifest.payload_digest_sha256 },
    signature: {
      algorithm: "rsa_pkcs1v15_sha256",
      key_id: "h2w8b-ui-key",
      value: signature
    }
  };
}

async function startServices(trustedPublicKeyJson) {
  fs.mkdirSync(outputDir, { recursive: true });
  fs.rmSync(chromeProfile, { recursive: true, force: true });
  fs.rmSync(dbPath, { force: true });
  fs.rmSync(localBackupDir, { recursive: true, force: true });
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
        WANFA_UPDATE_TRUSTED_PUBLIC_KEYS_JSON: trustedPublicKeyJson,
        WANFA_LOCAL_BACKUP_DIR: localBackupDir,
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

async function seedOwnerAndUploadPackage() {
  const stamp = Date.now();
  const credentials = {
    tenantSlug: `h2w8b-ui-${stamp}`,
    tenantName: "H2W8B 本地维护验收空间",
    email: `h2w8b-owner-${stamp}@wanfa.local`,
    password: `H2W8BOwner${stamp}!`
  };
  const owner = await apiJson("/api/auth/local-setup/owner", {
    method: "POST",
    body: JSON.stringify({
      tenant_slug: credentials.tenantSlug,
      tenant_name: credentials.tenantName,
      owner_name: "H2W8B 负责人",
      email: credentials.email,
      password: credentials.password
    })
  });
  const token = owner.access_token;
  const tenantId = owner.user.tenant.id;
  const uploadPackage = await apiJson(`/api/tenants/${tenantId}/diagnostic-upload-package`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify({ authorization_note: "客户管理员确认授权上传本次 H2W8B 脱敏诊断包。" })
  });
  return { credentials, tenantId, token, uploadPackage };
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
      "--window-size=1440,1000",
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

async function closeTarget(targetId) {
  await fetch(`${chromeEndpoint}/json/close/${targetId}`).catch(() => undefined);
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
        else waiter.resolve(msg.result ?? {});
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
        waitFor(method, timeout = 12000) {
          return new Promise((resolve, reject) => {
            const existingIndex = events.findIndex((item) => item.method === method);
            if (existingIndex >= 0) {
              resolve(events.splice(existingIndex, 1)[0]);
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

async function waitFor(cdp, expression, timeout = 20000) {
  const started = Date.now();
  while (Date.now() - started < timeout) {
    if (await evalValue(cdp, expression)) return true;
    await delay(250);
  }
  return false;
}

async function waitForOrThrow(cdp, expression, label, timeout = 20000) {
  const ok = await waitFor(cdp, expression, timeout);
  if (!ok) {
    const body = await evalValue(cdp, `document.body?.innerText?.slice(0, 1500) || ""`);
    const href = await evalValue(cdp, `location.href`);
    throw new Error(`Timed out waiting for ${label}\nURL: ${href}\nBody: ${body}`);
  }
}

async function fillInput(cdp, selector, value) {
  const ok = await evalValue(
    cdp,
    `(() => {
      const element = document.querySelector(${JSON.stringify(selector)});
      if (!element) return false;
      const proto = element instanceof HTMLTextAreaElement ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype;
      const setter = Object.getOwnPropertyDescriptor(proto, "value").set;
      setter.call(element, ${JSON.stringify(value)});
      element.dispatchEvent(new Event("input", { bubbles: true }));
      element.dispatchEvent(new Event("change", { bubbles: true }));
      return true;
    })()`
  );
  if (!ok) throw new Error(`Unable to fill selector ${selector}`);
}

async function clickSelector(cdp, selector, label) {
  await waitForOrThrow(
    cdp,
    `Boolean(document.querySelector(${JSON.stringify(selector)})) && !document.querySelector(${JSON.stringify(selector)}).disabled`,
    label
  );
  const clicked = await evalValue(
    cdp,
    `(() => {
      const element = document.querySelector(${JSON.stringify(selector)});
      if (!element || element.disabled) return false;
      element.scrollIntoView({ block: "center", inline: "nearest" });
      element.click();
      return true;
    })()`
  );
  if (!clicked) throw new Error(`Unable to click ${label}`);
}

async function loginThroughUi(cdp, credentials) {
  await waitForOrThrow(cdp, `document.body?.innerText?.includes("登录工作台")`, "login page");
  await fillInput(cdp, '[data-role-smoke="tenant-slug"]', credentials.tenantSlug);
  await fillInput(cdp, '[data-role-smoke="email"]', credentials.email);
  await fillInput(cdp, '[data-role-smoke="password"]', credentials.password);
  await clickSelector(cdp, '[data-role-smoke="login-submit"]', "login submit");
  await waitForOrThrow(cdp, `document.body?.innerText?.includes("账号与本地维护")`, "settings page after login", 25000);
}

async function runUiFlow({ credentials, uploadPackage, signedPackage }) {
  const target = await createTarget(`${frontendBaseUrl}#settings`);
  const cdp = await createCdp(target.webSocketDebuggerUrl);
  try {
    await cdp.send("Page.enable");
    await cdp.send("Runtime.enable");
    await cdp.send("Emulation.setDeviceMetricsOverride", {
      width: 1440,
      height: 1000,
      deviceScaleFactor: 1,
      mobile: false
    });
    await cdp.send("Page.navigate", { url: `${frontendBaseUrl}#settings` });
    await cdp.waitFor("Page.loadEventFired", 12000).catch(() => undefined);
    await evalValue(cdp, `window.localStorage.removeItem(${JSON.stringify(tokenStorageKey)}); true`);
    await cdp.send("Page.navigate", { url: `${frontendBaseUrl}#settings` });
    await cdp.waitFor("Page.loadEventFired", 12000).catch(() => undefined);
    await loginThroughUi(cdp, credentials);
    await waitForOrThrow(cdp, `Boolean(document.querySelector('[data-h2w8b-local-maintenance="p3-06u-26h2w8b"]'))`, "local maintenance card");

    await fillInput(cdp, '[data-role-smoke="diagnostic-intake-package-input"]', JSON.stringify(uploadPackage, null, 2));
    await clickSelector(cdp, '[data-h2w5-cloud-intake-action="register"]', "register diagnostic intake");
    await waitForOrThrow(cdp, `document.body?.innerText?.includes("上传包已接收并登记") || Boolean(document.querySelector(".diagnostic-intake-item"))`, "accepted intake");

    await clickSelector(cdp, '[data-h2w6-remediation-action="create"]', "create remediation request");
    await waitForOrThrow(cdp, `document.body?.innerText?.includes("售后处理单已生成") || Boolean(document.querySelector(".diagnostic-remediation-item"))`, "remediation request");

    await fillInput(cdp, '[data-role-smoke="signed-update-package-input"]', JSON.stringify(signedPackage, null, 2));
    await clickSelector(cdp, '[data-role-smoke="signed-update-preflight"]', "signed update preflight");
    await waitForOrThrow(cdp, `document.querySelector('[data-role-smoke="signed-update-result"]')?.innerText?.includes("签名 通过")`, "signed update preflight result");
    await clickSelector(cdp, '[data-role-smoke="signed-update-stage"]', "stage signed update");
    await waitForOrThrow(cdp, `Boolean(document.querySelector('[data-role-smoke="signed-update-staged-staged"]'))`, "staged signed update");

    await clickSelector(cdp, '[data-role-smoke="local-backup-create"]', "create local backup");
    await waitForOrThrow(cdp, `Boolean(document.querySelector(".local-backup-item"))`, "local backup item");
    await clickSelector(cdp, '[data-role-smoke="local-backup-verify"]', "verify local backup");
    await waitForOrThrow(cdp, `document.querySelector(".local-backup-list")?.innerText?.includes("已校验")`, "verified local backup");
    await clickSelector(cdp, '[data-role-smoke="local-restore-dry-run"]', "create restore dry run");
    await waitForOrThrow(cdp, `Boolean(document.querySelector('[data-role-smoke="local-restore-dry-run-result"]')) && document.body?.innerText?.includes("只生成计划")`, "restore dry run result");

    await clickSelector(cdp, '[data-h2w6b-remediation-action="create-plan"]', "create signed update control plan");
    await waitForOrThrow(cdp, `Boolean(document.querySelector('[data-h2w6b-remediation-plan="p3-06u-26h2w6b"]'))`, "signed update control plan");
    await waitForOrThrow(
      cdp,
      `document.querySelector('[data-h2w8b-local-maintenance="p3-06u-26h2w8b"]')?.innerText?.includes("可进入维护演练")`,
      "ready local maintenance ledger",
      25000
    );

    await evalValue(cdp, `document.querySelector('[data-h2w8b-local-maintenance="p3-06u-26h2w8b"]')?.scrollIntoView({ block: "center" }); true`);
    const inspected = await evalValue(
      cdp,
      `(() => {
        const card = document.querySelector('[data-h2w8b-local-maintenance="p3-06u-26h2w8b"]');
        const bodyText = document.body?.innerText || "";
        const root = document.documentElement;
        return {
          hasMaintenanceCard: Boolean(card),
          cardText: card?.innerText || "",
          hasReadyMaturity: card?.innerText.includes("可进入维护演练") || false,
          hasEvidenceComplete: card?.innerText.includes("证据完整") || false,
          hasIntake: card?.innerText.includes("接收") || false,
          hasPlan: card?.innerText.includes("更新计划") || false,
          hasPackage: card?.innerText.includes("更新包") || false,
          hasBackup: card?.innerText.includes("已验备份") || false,
          hasRestoreDryRun: card?.innerText.includes("恢复演练") || false,
          hasForbiddenClaim:
            bodyText.includes("自动上传已上线") ||
            bodyText.includes("已远程控制客户电脑") ||
            bodyText.includes("静默更新已完成") ||
            bodyText.includes("真实外发已接通"),
          overflowX: root.scrollWidth > innerWidth,
          scrollWidth: root.scrollWidth,
          innerWidth
        };
      })()`
    );
    const screenshot = await cdp.send("Page.captureScreenshot", {
      format: "png",
      fromSurface: true,
      captureBeyondViewport: true
    });
    fs.writeFileSync(path.join(outputDir, "desktop-1440-local-maintenance-ready.png"), Buffer.from(screenshot.data, "base64"));
    const runtimeErrors = cdp.events
      .filter((event) => event.method === "Runtime.exceptionThrown")
      .map((event) => event.params?.exceptionDetails?.exception?.description || event.params?.exceptionDetails?.text || "runtime error");
    return { inspected, runtimeErrors };
  } finally {
    cdp.close();
    await closeTarget(target.id);
  }
}

async function main() {
  fs.mkdirSync(outputDir, { recursive: true });
  const { privateKey, publicKey } = crypto.generateKeyPairSync("rsa", { modulusLength: 2048 });
  const privateKeyPem = privateKey.export({ type: "pkcs1", format: "pem" }).toString();
  const publicKeyPem = publicKey.export({ type: "pkcs1", format: "pem" }).toString();
  const trustedPublicKeyJson = JSON.stringify({ "h2w8b-ui-key": publicKeyPem });
  const signedPackage = createSignedKnowledgePackage(privateKeyPem);
  await startServices(trustedPublicKeyJson);
  const scenario = await seedOwnerAndUploadPackage();
  await startChrome();
  const uiResult = await runUiFlow({
    credentials: scenario.credentials,
    uploadPackage: scenario.uploadPackage,
    signedPackage
  });
  const apiReadiness = await apiJson(`/api/tenants/${scenario.tenantId}/local-maintenance/readiness`, {
    headers: { Authorization: `Bearer ${scenario.token}` }
  });
  const summary = {
    ui: uiResult,
    api_readiness: {
      schema_version: apiReadiness.schema_version,
      maturity_status: apiReadiness.maturity_status,
      ready_for_customer_maintenance_rehearsal: apiReadiness.ready_for_customer_maintenance_rehearsal,
      counts: apiReadiness.counts,
      blocker_count: apiReadiness.blockers.length,
      safety: apiReadiness.safety
    },
    boundaries: {
      browser_logged_in_through_real_form: true,
      external_write_enabled: false,
      real_platform_send_performed: false,
      remote_control_performed: false,
      silent_update_performed: false
    }
  };
  if (!uiResult.inspected.hasMaintenanceCard || !uiResult.inspected.hasReadyMaturity) {
    throw new Error(`local maintenance card is not ready: ${JSON.stringify(uiResult.inspected, null, 2)}`);
  }
  if (!uiResult.inspected.hasEvidenceComplete) throw new Error("local maintenance evidence badge did not become complete");
  if (uiResult.inspected.hasForbiddenClaim) throw new Error("forbidden automatic/remote claim detected");
  if (uiResult.inspected.overflowX) throw new Error(`horizontal overflow: ${JSON.stringify(uiResult.inspected)}`);
  if (uiResult.runtimeErrors.length > 0) throw new Error(`runtime errors: ${uiResult.runtimeErrors.join("\n")}`);
  if (apiReadiness.maturity_status !== "ready_for_rehearsal") {
    throw new Error(`api readiness is not ready_for_rehearsal: ${JSON.stringify(summary.api_readiness, null, 2)}`);
  }
  if (apiReadiness.ready_for_customer_maintenance_rehearsal !== true) {
    throw new Error("api readiness did not allow customer maintenance rehearsal");
  }
  if (apiReadiness.blockers.length > 0) {
    throw new Error(`api readiness has blockers: ${apiReadiness.blockers.join("; ")}`);
  }
  fs.writeFileSync(path.join(outputDir, "summary.json"), JSON.stringify(summary, null, 2), "utf-8");
  console.log(`H2W8B local maintenance UI smoke passed. Output: ${outputDir}`);
}

async function cleanup() {
  for (const child of children.reverse()) child.kill("SIGTERM");
  await delay(500);
  fs.rmSync(chromeProfile, { recursive: true, force: true });
  fs.rmSync(dbPath, { force: true });
  fs.rmSync(localBackupDir, { recursive: true, force: true });
}

main()
  .catch((error) => {
    console.error(error);
    process.exitCode = 1;
  })
  .finally(() => cleanup());
