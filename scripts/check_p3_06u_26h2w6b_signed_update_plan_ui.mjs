import crypto from "node:crypto";
import fs from "node:fs";
import path from "node:path";
import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";

const rootDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const outputDir = path.resolve(process.env.P3_06U_26H2W6B_OUTPUT ?? path.join(rootDir, "output/p3_06u_26h2w6b_signed_update_plan_ui"));
const backendPort = Number(process.env.P3_06U_26H2W6B_BACKEND_PORT ?? 8126);
const frontendPort = Number(process.env.P3_06U_26H2W6B_FRONTEND_PORT ?? 5226);
const chromePort = Number(process.env.P3_06U_26H2W6B_CHROME_PORT ?? 9266);
const backendUrl = `http://127.0.0.1:${backendPort}`;
const frontendBaseUrl = `http://127.0.0.1:${frontendPort}/`;
const chromeEndpoint = `http://127.0.0.1:${chromePort}`;
const dbPath = path.join(outputDir, "h2w6b_signed_update_plan.sqlite");
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

function createSignedKnowledgePackage(privateKeyPem) {
  const payload = {
    schema_version: "wanfa.knowledge_update_package.v1",
    package_id: "h2w6b-ui-knowledge-payload",
    package_name: "H2W6B UI 知识修复包",
    source_diagnostic_filename: "wanfa-diagnostic-remediation.json",
    notes: "浏览器 smoke 使用的处理单知识修复包。",
    business_objects: [
      {
        ref: "h2w6b-lite-package",
        type: "package",
        title: "AI客服入门验证包",
        aliases: ["入门版", "试点版"],
        summary: "用于验证官网客服、核心问答、留资和人工接管。",
        status: "active"
      }
    ],
    object_knowledge_cards: [
      {
        business_object_ref: "h2w6b-lite-package",
        question: "试点版能不能自动外发到所有平台？",
        answer: "试点版默认只在授权渠道内受控回复；真实平台外发必须经过官方授权、白名单、回执和审计验收。",
        trigger_keywords: ["试点", "外发", "平台"],
        source: "h2w6b_ui_smoke",
        status: "active"
      }
    ],
    knowledge_documents: [
      {
        title: "H2W6B UI smoke 知识文档",
        source_type: "signed_update_package",
        source_uri: "internal://h2w6b/ui-smoke",
        tags: ["H2W6B", "受控更新计划"],
        status: "active",
        raw_text: "受控更新计划只绑定处理单和签名包状态，不自动应用更新，也不打开真实外发。"
      }
    ],
    evaluation_sets: []
  };
  const payloadJson = canonicalJson(payload);
  const manifest = {
    schema_version: "wanfa.signed_update_manifest.v1",
    package_id: "h2w6b-ui-knowledge-update",
    package_name: "H2W6B UI 知识修复包",
    package_type: "knowledge",
    package_version: "2026.07.04.h2w6b.ui",
    product: "wanfa-standard-ops",
    released_at: "2026-07-04T10:00:00+08:00",
    compatible_app_versions: ["0.1.0"],
    requires_maintenance_window: false,
    payload_digest_sha256: sha256Hex(payloadJson),
    payload_size_bytes: Buffer.byteLength(payloadJson),
    operations: [
      {
        target: "knowledge_documents",
        action: "upsert",
        count: 1,
        summary: "补充 H2W6B UI smoke 知识文档"
      }
    ]
  };
  const manifestJson = canonicalJson(manifest);
  const signature = crypto.sign("RSA-SHA256", Buffer.from(manifestJson), privateKeyPem).toString("base64");
  return {
    schema_version: "wanfa.signed_update_package.v1",
    manifest,
    payload,
    release_notes: "H2W6B UI smoke 使用；只验证计划绑定。",
    checksums: { payload_sha256: manifest.payload_digest_sha256 },
    signature: {
      algorithm: "rsa_pkcs1v15_sha256",
      key_id: "h2w6b-ui-key",
      value: signature
    }
  };
}

async function startServices(trustedPublicKeyJson) {
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
        WANFA_UPDATE_TRUSTED_PUBLIC_KEYS_JSON: trustedPublicKeyJson,
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

async function seedScenario(signedPackage) {
  const stamp = Date.now();
  const owner = await apiJson("/api/auth/local-setup/owner", {
    method: "POST",
    body: JSON.stringify({
      tenant_slug: `h2w6b-ui-${stamp}`,
      tenant_name: "H2W6B 受控更新计划验收空间",
      owner_name: "H2W6B 负责人",
      email: `h2w6b-owner-${stamp}@wanfa.local`,
      password: `H2W6BOwner${stamp}!`
    })
  });
  const token = owner.access_token;
  const tenantId = owner.user.tenant.id;
  const headers = { Authorization: `Bearer ${token}` };
  const upload = await apiJson(`/api/tenants/${tenantId}/diagnostic-upload-package`, {
    method: "POST",
    headers,
    body: JSON.stringify({ authorization_note: "客户管理员确认授权上传本次脱敏诊断包。" })
  });
  const intake = await apiJson(`/api/tenants/${tenantId}/diagnostic-intake-records`, {
    method: "POST",
    headers,
    body: JSON.stringify({ upload_package: upload, source_channel: "manual_transfer" })
  });
  await apiJson(`/api/tenants/${tenantId}/diagnostic-intake-records/${intake.id}/remediation-requests`, {
    method: "POST",
    headers,
    body: JSON.stringify({ request_type: "knowledge_update", title: "H2W6B UI 处理单" })
  });
  await apiJson(`/api/tenants/${tenantId}/signed-update-package/staged`, {
    method: "POST",
    headers,
    body: JSON.stringify({ package: signedPackage })
  });
  return { token, tenantId };
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

async function waitFor(cdp, expression, timeout = 15000) {
  const started = Date.now();
  while (Date.now() - started < timeout) {
    if (await evalValue(cdp, expression)) return true;
    await delay(200);
  }
  return false;
}

async function inspectUi(token) {
  const target = await createTarget("about:blank");
  const cdp = await createCdp(target.webSocketDebuggerUrl);
  try {
    await cdp.send("Page.enable");
    await cdp.send("Runtime.enable");
    await cdp.send("Emulation.setDeviceMetricsOverride", {
      width: 1440,
      height: 900,
      deviceScaleFactor: 1,
      mobile: false
    });
    await cdp.send("Page.navigate", { url: new URL(frontendBaseUrl).origin });
    await cdp.waitFor("Page.loadEventFired", 12000).catch(() => undefined);
    await evalValue(cdp, `window.localStorage.setItem(${JSON.stringify(tokenStorageKey)}, ${JSON.stringify(token)})`);
    await cdp.send("Page.navigate", { url: `${frontendBaseUrl}#settings` });
    await cdp.waitFor("Page.loadEventFired", 12000).catch(() => undefined);
    const ready = await waitFor(cdp, `Boolean(document.querySelector('[data-h2w6-remediation="p3-06u-26h2w6"]'))`);
    if (!ready) throw new Error("H2W6 remediation section did not render");
    await evalValue(cdp, `document.querySelector('[data-h2w6-remediation="p3-06u-26h2w6"]')?.scrollIntoView({block:"center"})`);
    const hasAction = await waitFor(cdp, `Boolean(document.querySelector('[data-h2w6b-remediation-action="create-plan"]'))`);
    if (!hasAction) throw new Error("H2W6B create-plan action did not render");
    await evalValue(cdp, `document.querySelector('[data-h2w6b-remediation-action="create-plan"]')?.click()`);
    const planned = await waitFor(cdp, `Boolean(document.querySelector('[data-h2w6b-remediation-plan="p3-06u-26h2w6b"]'))`);
    if (!planned) throw new Error("H2W6B plan did not render after click");
    await delay(500);
    const inspected = await evalValue(cdp, `(() => {
      const section = document.querySelector('[data-h2w6-remediation="p3-06u-26h2w6"]');
      const plan = document.querySelector('[data-h2w6b-remediation-plan="p3-06u-26h2w6b"]');
      const text = section?.innerText || "";
      const root = document.documentElement;
      return {
        hasSection: Boolean(section),
        hasPlan: Boolean(plan),
        hasCreateOrRefreshAction: Boolean(document.querySelector('[data-h2w6b-remediation-action="create-plan"]')),
        hasOnlyPlanBoundary: text.includes("只生成计划"),
        hasForbiddenAutoClaim: text.includes("自动更新完成") || text.includes("远程修复完成") || text.includes("真实外发已打开"),
        stepStatuses: Array.from(plan?.querySelectorAll("[data-step-status]") || []).map((node) => node.getAttribute("data-step-status")),
        overflowX: root.scrollWidth > innerWidth,
        scrollWidth: root.scrollWidth,
        innerWidth
      };
    })()`);
    const screenshot = await cdp.send("Page.captureScreenshot", {
      format: "png",
      fromSurface: true,
      captureBeyondViewport: false
    });
    fs.writeFileSync(path.join(outputDir, "desktop-1440-signed-update-plan.png"), Buffer.from(screenshot.data, "base64"));
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
  const privateKeyPem = privateKey.export({ type: "pkcs1", format: "pem" });
  const publicKeyPem = publicKey.export({ type: "pkcs1", format: "pem" });
  const trustedPublicKeyJson = JSON.stringify({ "h2w6b-ui-key": publicKeyPem.toString() });
  const signedPackage = createSignedKnowledgePackage(privateKeyPem.toString());
  await startServices(trustedPublicKeyJson);
  const scenario = await seedScenario(signedPackage);
  await startChrome();
  const result = await inspectUi(scenario.token);
  if (!result.inspected.hasPlan) throw new Error("plan marker missing");
  if (!result.inspected.hasOnlyPlanBoundary) throw new Error("only-plan boundary missing");
  if (result.inspected.hasForbiddenAutoClaim) throw new Error("forbidden automatic/remote claim detected");
  if (result.inspected.overflowX) throw new Error(`horizontal overflow: ${JSON.stringify(result.inspected)}`);
  if (result.runtimeErrors.length > 0) throw new Error(`runtime errors: ${result.runtimeErrors.join("\n")}`);
  fs.writeFileSync(path.join(outputDir, "summary.json"), JSON.stringify(result, null, 2), "utf-8");
  console.log(`H2W6B signed update plan UI smoke passed. Output: ${outputDir}`);
}

main()
  .catch((error) => {
    console.error(error);
    process.exitCode = 1;
  })
  .finally(() => {
    for (const child of children) child.kill("SIGTERM");
  });
