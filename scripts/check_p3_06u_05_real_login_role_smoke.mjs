import fs from "node:fs";
import path from "node:path";

const chromeEndpoint = process.env.CHROME_DEBUGGING_URL ?? "http://127.0.0.1:9224";
const backendUrl = stripTrailingSlash(process.env.BACKEND_URL ?? "http://127.0.0.1:8081");
const frontendUrl = process.env.FRONTEND_URL ?? "http://127.0.0.1:5178/#overview";
const outputDir = path.resolve(process.env.P3_06U_05_OUTPUT ?? "output/p3_06u_role_smoke");
const tokenStorageKey = "wanfa_standard_ops_access_token";
const password = process.env.P3_06U_05_PASSWORD ?? "WanfaSmoke123!";

const roleExpectations = {
  owner: {
    defaultHash: "#overview",
    roleLabel: "管理员视图",
    nav: ["overview", "live", "conversations", "reviews", "outbox", "tickets", "contacts", "leads", "knowledge", "gaps", "evals", "quality", "channels", "ops", "model", "settings"],
    hidden: [],
    tasks: ["ops-risk-scan", "review-risk-drafts", "outbox-gate", "knowledge-gap-repair", "channel-connector-status"]
  },
  admin: {
    defaultHash: "#overview",
    roleLabel: "运营管理视图",
    nav: ["overview", "live", "conversations", "reviews", "outbox", "tickets", "contacts", "leads", "knowledge", "gaps", "evals", "quality", "channels", "ops", "model", "settings"],
    hidden: [],
    tasks: ["ops-risk-scan", "review-risk-drafts", "outbox-gate", "quality-cause-review", "knowledge-gap-repair"]
  },
  agent: {
    defaultHash: "#overview",
    roleLabel: "坐席视图",
    nav: ["overview", "live", "conversations", "reviews", "outbox", "tickets", "contacts", "leads", "knowledge"],
    hidden: ["quality", "channels", "ops", "model", "settings", "gaps", "evals"],
    tasks: ["live-inbox", "review-risk-drafts", "outbox-gate", "customer-followup", "ticket-sla"],
    disabledActionCheck: {
      hash: "#knowledge",
      text: "仅管理员可导入"
    }
  },
  viewer: {
    defaultHash: "#overview",
    roleLabel: "只读视图",
    nav: ["overview", "quality", "channels"],
    hidden: ["live", "conversations", "reviews", "outbox", "tickets", "contacts", "leads", "knowledge", "gaps", "evals", "ops", "model", "settings"],
    tasks: ["ops-risk-scan", "quality-cause-review", "channel-connector-status"],
    restrictedCheck: {
      hash: "#live",
      expectedRedirect: "#overview"
    }
  }
};

function stripTrailingSlash(value) {
  return value.replace(/\/+$/, "");
}

function frontendWithHash(hash) {
  const url = new URL(frontendUrl);
  url.hash = hash.replace(/^#/, "");
  return url.toString();
}

function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function ensureOutputDir() {
  fs.mkdirSync(outputDir, { recursive: true });
}

async function requestApi(pathname, options = {}, token) {
  const headers = new Headers(options.headers ?? {});
  if (options.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }
  const response = await fetch(`${backendUrl}${pathname}`, { ...options, headers });
  if (!response.ok) {
    let detail = "";
    try {
      const body = await response.json();
      detail = body?.detail ? `: ${body.detail}` : "";
    } catch {
      detail = "";
    }
    throw new Error(`${pathname} failed: ${response.status}${detail}`);
  }
  return response.json();
}

async function waitForBackend() {
  const started = Date.now();
  while (Date.now() - started < 12000) {
    try {
      const health = await requestApi("/health");
      if (health.status === "ok") return;
    } catch {
      await delay(350);
    }
  }
  throw new Error(`Backend is not ready at ${backendUrl}`);
}

async function seedTenantAndUsers() {
  await waitForBackend();
  const suffix = `${Date.now()}-${Math.random().toString(16).slice(2, 8)}`;
  const tenantSlug = `p3-06u-05-${suffix}`;
  const tenant = await requestApi("/api/tenants", {
    method: "POST",
    body: JSON.stringify({
      name: "P3-06U 真实角色 Smoke 租户",
      slug: tenantSlug,
      plan: "standard_ops"
    })
  });

  const ownerRole = await requestApi(`/api/tenants/${tenant.id}/roles`, {
    method: "POST",
    body: JSON.stringify({ code: "owner", name: "Owner" })
  });
  const ownerUser = await requestApi(`/api/tenants/${tenant.id}/users`, {
    method: "POST",
    body: JSON.stringify({
      name: "Smoke Owner",
      email: `owner-${suffix}@example.com`,
      password,
      status: "active"
    })
  });
  await requestApi(`/api/users/${ownerUser.id}/roles`, {
    method: "POST",
    body: JSON.stringify({ role_id: ownerRole.id })
  });
  const ownerLogin = await requestApi("/api/auth/login", {
    method: "POST",
    body: JSON.stringify({
      tenant_slug: tenantSlug,
      email: ownerUser.email,
      password
    })
  });

  const users = {
    owner: {
      tenantSlug,
      email: ownerUser.email,
      password,
      expectedRole: "owner"
    }
  };

  for (const role of ["admin", "agent", "viewer"]) {
    const createdRole = await requestApi(`/api/tenants/${tenant.id}/roles`, {
      method: "POST",
      body: JSON.stringify({ code: role, name: role[0].toUpperCase() + role.slice(1) })
    }, ownerLogin.access_token);
    const createdUser = await requestApi(`/api/tenants/${tenant.id}/users`, {
      method: "POST",
      body: JSON.stringify({
        name: `Smoke ${role}`,
        email: `${role}-${suffix}@example.com`,
        password,
        status: "active"
      })
    }, ownerLogin.access_token);
    await requestApi(`/api/users/${createdUser.id}/roles`, {
      method: "POST",
      body: JSON.stringify({ role_id: createdRole.id })
    }, ownerLogin.access_token);
    users[role] = {
      tenantSlug,
      email: createdUser.email,
      password,
      expectedRole: role
    };
  }

  return { tenant, users };
}

async function createTarget(url) {
  const res = await fetch(`${chromeEndpoint}/json/new?${encodeURIComponent(url)}`, { method: "PUT" });
  if (!res.ok) {
    throw new Error(`Failed to create Chrome target: ${res.status}`);
  }
  return res.json();
}

async function closeTarget(targetId) {
  await fetch(`${chromeEndpoint}/json/close/${targetId}`).catch(() => undefined);
}

function createCdp(wsUrl, onEvent = () => undefined) {
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
    if (msg.method) {
      events.push(msg);
      onEvent(msg);
    }
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
  if (result.exceptionDetails) {
    throw new Error(JSON.stringify(result.exceptionDetails));
  }
  return result.result.value;
}

async function waitFor(cdp, expression, timeout = 12000) {
  const started = Date.now();
  while (Date.now() - started < timeout) {
    if (await evalValue(cdp, expression)) return true;
    await delay(180);
  }
  return false;
}

async function setInput(cdp, selector, value, fallbackName) {
  for (let attempt = 0; attempt < 30; attempt += 1) {
    const ok = await evalValue(cdp, `(() => {
      const input =
        document.querySelector(${JSON.stringify(selector)}) ||
        ${fallbackName ? `document.querySelector('input[name="${fallbackName}"]')` : "null"};
      if (!input) return false;
      const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')?.set;
      setter?.call(input, ${JSON.stringify(value)});
      input.dispatchEvent(new Event('input', { bubbles: true }));
      input.dispatchEvent(new Event('change', { bubbles: true }));
      return true;
    })()`);
    if (ok) return;
    await delay(120);
  }
  const selectors = await evalValue(cdp, `Array.from(document.querySelectorAll('input')).map((input) => ({
    name: input.getAttribute('name'),
    roleSmoke: input.getAttribute('data-role-smoke'),
    placeholder: input.getAttribute('placeholder')
  }))`);
  throw new Error(`Input not found: ${selector}. Current inputs: ${JSON.stringify(selectors)}`);
}

async function capture(cdp, name) {
  const screenshot = await cdp.send("Page.captureScreenshot", {
    format: "png",
    fromSurface: true,
    captureBeyondViewport: false
  });
  fs.writeFileSync(path.join(outputDir, `${name}.png`), Buffer.from(screenshot.data, "base64"));
}

async function loginThroughForm(cdp, credentials) {
  await cdp.send("Page.navigate", { url: frontendWithHash("#overview") });
  await cdp.waitFor("Page.loadEventFired", 12000).catch(() => undefined);
  await waitFor(cdp, `document.readyState === 'complete' || document.querySelector('[data-role-smoke="login-form"], .workspace')`);
  await evalValue(cdp, `window.localStorage.removeItem(${JSON.stringify(tokenStorageKey)}); true;`);
  await cdp.send("Page.navigate", { url: frontendWithHash("#overview") });
  await cdp.waitFor("Page.loadEventFired", 12000).catch(() => undefined);

  const loginReady = await waitFor(
    cdp,
    `Boolean(
      document.querySelector('[data-role-smoke="login-form"]') &&
      document.querySelector('[data-role-smoke="tenant-slug"]') &&
      document.querySelector('[data-role-smoke="email"]') &&
      document.querySelector('[data-role-smoke="password"]')
    )`
  );
  if (!loginReady) {
    throw new Error("Login form did not render");
  }

  await setInput(cdp, '[data-role-smoke="tenant-slug"]', credentials.tenantSlug, "tenant_slug");
  await setInput(cdp, '[data-role-smoke="email"]', credentials.email, "email");
  await setInput(cdp, '[data-role-smoke="password"]', credentials.password, "password");
  await evalValue(cdp, `document.querySelector('[data-role-smoke="login-submit"]')?.click(); true;`);

  const workspaceReady = await waitFor(cdp, `Boolean(document.querySelector('.workspace'))`, 15000);
  if (!workspaceReady) {
    const text = await evalValue(cdp, `document.body.innerText`);
    throw new Error(`Workspace did not render after login. Body: ${text.slice(0, 1000)}`);
  }
  await delay(900);
}

async function inspectPage(cdp) {
  return evalValue(cdp, `(async () => {
    const token = window.localStorage.getItem(${JSON.stringify(tokenStorageKey)});
    let me = null;
    let meStatus = null;
    try {
      const response = await fetch('/api/auth/me', {
        headers: token ? { Authorization: 'Bearer ' + token } : {}
      });
      meStatus = response.status;
      me = response.ok ? await response.json() : null;
    } catch (error) {
      meStatus = 'fetch-error';
    }
    const text = document.body.innerText;
    const navSections = Array.from(new Set(
      Array.from(document.querySelectorAll('[data-workspace-nav]'))
        .map((item) => item.getAttribute('data-workspace-nav'))
        .filter(Boolean)
    ));
    const taskIds = Array.from(document.querySelectorAll('[data-role-task-id]')).map((item) =>
      item.getAttribute('data-role-task-id')
    );
    return {
      href: location.href,
      hash: location.hash,
      tokenPresent: Boolean(token),
      meStatus,
      me,
      navSections,
      taskIds,
      taskLabels: Array.from(document.querySelectorAll('.role-task-copy strong')).map((item) => item.textContent?.trim() ?? ''),
      roleLabel: document.querySelector('.role-task-paths-heading strong')?.textContent?.trim() ?? '',
      disabledButtonTexts: Array.from(document.querySelectorAll('button:disabled')).map((button) => button.textContent?.trim().replace(/\\s+/g, ' ') ?? '').filter(Boolean),
      noPermissionMessage: text.includes(${JSON.stringify("当前账号无权读取此模块，请联系管理员开通权限。")}),
      hasWorkspace: Boolean(document.querySelector('.workspace')),
      hasLoginForm: Boolean(document.querySelector('[data-role-smoke="login-form"]')),
      overflowX: document.documentElement.scrollWidth > innerWidth || document.body.scrollWidth > innerWidth,
      bodyText: text.slice(0, 7000)
    };
  })()`);
}

async function runRoleSmoke(role, credentials) {
  const apiResponses = [];
  const target = await createTarget("about:blank");
  const cdp = await createCdp(target.webSocketDebuggerUrl, (msg) => {
    if (msg.method !== "Network.responseReceived") return;
    const response = msg.params?.response;
    if (!response?.url?.includes("/api/")) return;
    apiResponses.push({
      url: response.url,
      status: response.status
    });
  });

  try {
    await cdp.send("Page.enable");
    await cdp.send("Runtime.enable");
    await cdp.send("Network.enable");
    await cdp.send("Emulation.setDeviceMetricsOverride", {
      width: 1440,
      height: 900,
      deviceScaleFactor: 1,
      mobile: false
    });

    await loginThroughForm(cdp, credentials);
    const expected = roleExpectations[role];
    await waitFor(cdp, `location.hash === ${JSON.stringify(expected.defaultHash)}`, 6000);
    const defaultPage = await inspectPage(cdp);
    await capture(cdp, `${role}-default`);

    let permissionPage = null;
    if (expected.disabledActionCheck) {
      await cdp.send("Page.navigate", { url: frontendWithHash(expected.disabledActionCheck.hash) });
      await cdp.waitFor("Page.loadEventFired", 12000).catch(() => undefined);
      await waitFor(cdp, `location.hash === ${JSON.stringify(expected.disabledActionCheck.hash)}`);
      await delay(600);
      permissionPage = await inspectPage(cdp);
      await capture(cdp, `${role}-permission-note`);
    }

    let restrictedPage = null;
    if (expected.restrictedCheck) {
      await cdp.send("Page.navigate", { url: frontendWithHash(expected.restrictedCheck.hash) });
      await cdp.waitFor("Page.loadEventFired", 12000).catch(() => undefined);
      await waitFor(cdp, `location.hash === ${JSON.stringify(expected.restrictedCheck.expectedRedirect)}`, 6000);
      await delay(500);
      restrictedPage = await inspectPage(cdp);
      await capture(cdp, `${role}-restricted-redirect`);
    }

    await evalValue(cdp, `document.querySelector('[data-role-smoke="logout-button"]')?.click(); true;`);
    const loginReady = await waitFor(cdp, `Boolean(document.querySelector('[data-role-smoke="login-form"]'))`, 8000);
    const logoutState = await evalValue(cdp, `({
      loginReady: ${String(loginReady)},
      tokenPresent: Boolean(window.localStorage.getItem(${JSON.stringify(tokenStorageKey)})),
      text: document.body.innerText.slice(0, 1000)
    })`);

    return {
      role,
      defaultPage,
      permissionPage,
      restrictedPage,
      logoutState,
      apiResponses,
      unexpected403: apiResponses.filter((item) => item.status === 403)
    };
  } finally {
    cdp.close();
    await closeTarget(target.id);
  }
}

function validateRoleResult(result) {
  const failures = [];
  const expected = roleExpectations[result.role];
  const page = result.defaultPage;
  const prefix = result.role;

  if (!page.hasWorkspace || !page.tokenPresent) {
    failures.push(`${prefix}: workspace or token missing after login`);
  }
  if (page.meStatus !== 200 || !page.me) {
    failures.push(`${prefix}: /api/auth/me did not return current user with token`);
  }
  if (!page.me?.roles?.includes(result.role)) {
    failures.push(`${prefix}: logged-in user roles mismatch: ${JSON.stringify(page.me?.roles)}`);
  }
  if (page.hash !== expected.defaultHash) {
    failures.push(`${prefix}: default hash should be ${expected.defaultHash}, got ${page.hash}`);
  }
  if (page.roleLabel !== expected.roleLabel) {
    failures.push(`${prefix}: role label should be ${expected.roleLabel}, got ${page.roleLabel}`);
  }
  for (const section of expected.nav) {
    if (!page.navSections.includes(section)) {
      failures.push(`${prefix}: expected nav section missing: ${section}`);
    }
  }
  for (const section of expected.hidden) {
    if (page.navSections.includes(section)) {
      failures.push(`${prefix}: hidden nav section should not be visible: ${section}`);
    }
  }
  for (const taskId of expected.tasks) {
    if (!page.taskIds.includes(taskId)) {
      failures.push(`${prefix}: expected role task missing: ${taskId}`);
    }
  }
  if (page.taskIds.length !== expected.tasks.length) {
    failures.push(`${prefix}: expected ${expected.tasks.length} task paths, got ${page.taskIds.length}`);
  }
  if (page.overflowX) {
    failures.push(`${prefix}: horizontal overflow detected on default page`);
  }
  if (expected.disabledActionCheck) {
    const text = [
      ...(result.permissionPage?.disabledButtonTexts ?? []),
      result.permissionPage?.bodyText ?? ""
    ].join("\n");
    if (!text.includes(expected.disabledActionCheck.text)) {
      failures.push(`${prefix}: disabled action explanation missing: ${expected.disabledActionCheck.text}`);
    }
  }
  if (expected.restrictedCheck && result.restrictedPage?.hash !== expected.restrictedCheck.expectedRedirect) {
    failures.push(`${prefix}: restricted path should redirect to ${expected.restrictedCheck.expectedRedirect}, got ${result.restrictedPage?.hash}`);
  }
  if (!result.logoutState.loginReady || result.logoutState.tokenPresent) {
    failures.push(`${prefix}: logout should return to login screen and clear token`);
  }
  if (result.unexpected403.length > 0) {
    failures.push(`${prefix}: unexpected 403 responses: ${result.unexpected403.map((item) => item.url).join(", ")}`);
  }

  return failures;
}

async function main() {
  ensureOutputDir();
  const seeded = await seedTenantAndUsers();
  const results = [];
  for (const role of ["owner", "admin", "agent", "viewer"]) {
    results.push(await runRoleSmoke(role, seeded.users[role]));
  }

  const failures = results.flatMap(validateRoleResult);
  const summary = {
    tenant: seeded.tenant,
    backendUrl,
    frontendUrl,
    roles: results.map((result) => ({
      role: result.role,
      defaultHash: result.defaultPage.hash,
      currentUserRoles: result.defaultPage.me?.roles ?? [],
      navSections: result.defaultPage.navSections,
      taskIds: result.defaultPage.taskIds,
      disabledButtonTexts: result.permissionPage?.disabledButtonTexts ?? [],
      restrictedHash: result.restrictedPage?.hash ?? null,
      logoutClearedToken: !result.logoutState.tokenPresent,
      api403Count: result.unexpected403.length
    })),
    failures
  };
  fs.writeFileSync(path.join(outputDir, "summary.json"), JSON.stringify(summary, null, 2));

  if (failures.length > 0) {
    for (const failure of failures) {
      console.error(`FAIL ${failure}`);
    }
    process.exitCode = 1;
    return;
  }
  console.log(`P3-06U-05 real login role smoke passed. Output: ${outputDir}`);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
