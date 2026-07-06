import fs from "node:fs";
import path from "node:path";
import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";

const rootDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const outputDir = path.resolve(process.env.P3_06U_26H2R_OUTPUT ?? path.join(rootDir, "output/p3_06u_26h2r_final_answer_label_io"));
const backendPort = Number(process.env.P3_06U_26H2R_BACKEND_PORT ?? 8107);
const frontendPort = Number(process.env.P3_06U_26H2R_FRONTEND_PORT ?? 5207);
const chromePort = Number(process.env.P3_06U_26H2R_CHROME_PORT ?? 9247);
const backendUrl = `http://127.0.0.1:${backendPort}`;
const frontendUrl = `http://127.0.0.1:${frontendPort}/#evals`;
const chromeEndpoint = `http://127.0.0.1:${chromePort}`;
const dbPath = path.join(outputDir, "final_answer_label_io_smoke.sqlite");
const chromeProfile = path.join(outputDir, "chrome-profile");
const screenshotPath = path.join(outputDir, "final-answer-label-io.png");
const summaryPath = path.join(outputDir, "summary.json");
const pythonBin = path.join(rootDir, "backend/.venv/bin/python");
const children = [];

const DOCUMENT_TEXT = `
# 售后政策手册
标准产品保修期为三年。客户咨询退换货时，需要结合订单时间、商品状态、是否存在质量问题和平台规则核对。
涉及赔付、承诺、隐私、合同争议和投诉升级的问题，应转人工处理，不能承诺百分百赔付或立即退款。
`;

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
  spawnLongRunning("frontend", "npm", ["run", "dev", "--", "--host", "127.0.0.1", "--port", String(frontendPort), "--strictPort"], {
    cwd: path.join(rootDir, "frontend"),
    env: { ...process.env, VITE_API_PROXY_TARGET: backendUrl }
  });
  await waitForHttp(`http://127.0.0.1:${frontendPort}/`);
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

async function seedData() {
  const stamp = Date.now();
  const owner = await apiJson("/api/auth/local-setup/owner", {
    method: "POST",
    body: JSON.stringify({
      tenant_slug: `h2r-label-${stamp}`,
      tenant_name: "H2R 标注导入导出空间",
      owner_name: "H2R 管理员",
      email: `h2r-owner-${stamp}@wanfa.local`,
      password: `H2RSmoke${stamp}!`
    })
  });
  const token = owner.access_token;
  const tenantId = owner.user.tenant.id;
  const headers = { Authorization: `Bearer ${token}` };

  await apiJson(`/api/tenants/${tenantId}/knowledge-documents`, {
    method: "POST",
    headers,
    body: JSON.stringify({
      title: "售后政策手册",
      source_type: "manual_document",
      source_uri: "internal://docs/after-sales-v1",
      raw_text: DOCUMENT_TEXT,
      tags: ["售后", "保修"],
      status: "active",
      chunk_size: 90,
      chunk_overlap: 10
    })
  });
  const evaluationSet = await apiJson(`/api/tenants/${tenantId}/knowledge-evaluation-sets`, {
    method: "POST",
    headers,
    body: JSON.stringify({
      name: "H2R 最终回复标注题集",
      description: "用于验证最终回复样本与人工标签导入导出。",
      status: "active",
      evaluation_mode: "customer_service_retrieval",
      cases: [
        {
          external_case_id: "h2r-final-answer-001",
          source_channel: "web",
          source_category: "售后",
          question: "标准产品保修期多久",
          expected_terms: ["三年", "保修"],
          expected_source_uri: "internal://docs/after-sales-v1",
          expected_human_review: false,
          allow_auto_reply: true
        },
        {
          external_case_id: "h2r-final-answer-002",
          source_channel: "web",
          source_category: "风险售后",
          question: "客户要求马上承诺赔付怎么办",
          expected_terms: ["人工", "核对"],
          expected_human_review: true,
          allow_auto_reply: false,
          risk_level: "high"
        }
      ]
    })
  });
  const run = await apiJson(`/api/knowledge-evaluation-sets/${evaluationSet.id}/runs`, {
    method: "POST",
    headers,
    body: JSON.stringify({ top_k: 5, low_confidence_threshold: 0.2 })
  });
  const firstCase = run.case_results[0];
  const secondCase = run.case_results[1];
  await apiJson(`/api/knowledge-evaluation-run-cases/${firstCase.id}/final-answer-sample`, {
    method: "PATCH",
    headers,
    body: JSON.stringify({
      final_answer_text: "标准产品保修期为三年；退换货需要结合订单时间和商品状态核对。",
      final_answer_source: "manual_capture",
      citation_uris: ["internal://docs/after-sales-v1"],
      answer_author: "本地客服工作台"
    })
  });
  await apiJson(`/api/knowledge-evaluation-run-cases/${secondCase.id}/final-answer-sample`, {
    method: "PATCH",
    headers,
    body: JSON.stringify({
      final_answer_text: "这个问题涉及赔付承诺，需要人工客服核对订单和售后规则后处理。",
      final_answer_source: "manual_capture",
      citation_uris: ["internal://docs/after-sales-v1"],
      answer_author: "本地客服工作台"
    })
  });
  await apiJson(`/api/knowledge-evaluation-runs/${run.id}/factuality-labels/batch`, {
    method: "PATCH",
    headers,
    body: JSON.stringify({
      labels: [
        {
          evaluation_run_case_id: firstCase.id,
          final_answer_factuality_status: "correct",
          citation_sufficient: true,
          forbidden_commitment_passed: true,
          handoff_correct: true
        },
        {
          evaluation_run_case_id: secondCase.id,
          final_answer_factuality_status: "needs_human_review",
          citation_sufficient: true,
          forbidden_commitment_passed: true,
          handoff_correct: true
        }
      ]
    })
  });
  return { token, tenantId, evaluationSetId: evaluationSet.id, runId: run.id };
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

async function runBrowserSmoke(seed) {
  await startChrome();
  const target = await createTarget("about:blank");
  const cdp = await createCdp(target.webSocketDebuggerUrl);
  try {
    await cdp.send("Runtime.enable");
    await cdp.send("Page.enable");
    await cdp.send("Page.addScriptToEvaluateOnNewDocument", {
      source: `window.localStorage.setItem('wanfa_standard_ops_access_token', ${JSON.stringify(seed.token)});`
    });
    await cdp.send("Emulation.setDeviceMetricsOverride", { width: 1440, height: 1000, deviceScaleFactor: 1, mobile: false });
    await cdp.send("Page.navigate", { url: frontendUrl });
    await waitForExpression(cdp, "document.body.innerText.includes('知识评测中心')", 12000);
    await waitForExpression(cdp, "Array.from(document.querySelectorAll('button')).some((button) => button.textContent.includes('查看详情'))", 12000);
    await evalValue(cdp, `(() => {
      const button = Array.from(document.querySelectorAll('button')).find((item) => item.textContent.includes('查看详情'));
      button?.click();
      return true;
    })()`);
    await waitForExpression(cdp, "Boolean(document.querySelector('[data-final-answer-label-io=\"p3-06u-26h2r\"]'))", 12000);
    await evalValue(cdp, `(() => {
      const panel = document.querySelector('[data-final-answer-label-io="p3-06u-26h2r"]');
      const button = Array.from(panel.querySelectorAll('button')).find((item) => item.textContent.includes('导出 CSV'));
      button?.click();
      return true;
    })()`);
    await waitForExpression(cdp, "document.querySelector('[data-final-answer-label-io=\"p3-06u-26h2r\"] textarea')?.value.includes('question_hash')", 12000);
    await evalValue(cdp, `(() => {
      const panel = document.querySelector('[data-final-answer-label-io="p3-06u-26h2r"]');
      const button = Array.from(panel.querySelectorAll('button')).find((item) => item.textContent.includes('预检 CSV'));
      button?.click();
      return true;
    })()`);
    await waitForExpression(cdp, "document.body.innerText.includes('预检通过')", 12000);
    await evalValue(cdp, `(() => {
      const panel = document.querySelector('[data-final-answer-label-io="p3-06u-26h2r"]');
      const button = Array.from(panel.querySelectorAll('button')).find((item) => item.textContent.includes('导入标签'));
      button?.click();
      return true;
    })()`);
    await waitForExpression(cdp, "document.body.innerText.includes('已导入')", 12000);
    const inspection = await evalValue(cdp, `(() => {
      const panel = document.querySelector('[data-final-answer-label-io="p3-06u-26h2r"]');
      const text = panel?.innerText || '';
      const csvValue = panel?.querySelector('textarea')?.value || '';
      const body = document.body.innerText;
      return {
        hasPanel: Boolean(panel),
        hasTitle: text.includes('离线标注表'),
        hasExport: text.includes('导出 CSV'),
        hasPrecheck: body.includes('预检通过'),
        hasImported: body.includes('已导入'),
        hasQuestionHash: csvValue.includes('question_hash'),
        rawQuestionLeaked: csvValue.includes('客户要求马上承诺赔付怎么办'),
        externalWriteEnabled: body.includes('真实外发已开启')
      };
    })()`);
    if (!inspection.hasPanel || !inspection.hasTitle || !inspection.hasExport || !inspection.hasImported || !inspection.hasQuestionHash) {
      throw new Error(`Final answer label IO UI missing expected content: ${JSON.stringify(inspection)}`);
    }
    if (inspection.rawQuestionLeaked || inspection.externalWriteEnabled) {
      throw new Error(`Final answer label IO UI leaked unsafe state: ${JSON.stringify(inspection)}`);
    }
    await evalValue(cdp, `document.querySelector('[data-final-answer-label-io="p3-06u-26h2r"]')?.scrollIntoView({ block: 'center' }); true`);
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
  const seed = await seedData();
  const inspection = await runBrowserSmoke(seed);
  fs.writeFileSync(summaryPath, JSON.stringify({
    ok: true,
    frontendUrl,
    backendUrl,
    tenant_id: seed.tenantId,
    evaluation_set_id: seed.evaluationSetId,
    evaluation_run_id: seed.runId,
    screenshot: screenshotPath,
    token_persisted: false,
    model_call_performed: false,
    external_platform_write_performed: false,
    inspection
  }, null, 2));
  console.log("PASS p3-06u-26h2r final answer label IO UI smoke");
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
    fs.rmSync(dbPath, { force: true });
  });
