import fs from "node:fs";
import path from "node:path";

export const defaultSelectors = {
  platformRoot: '[data-rpa-platform="mock-customer-service"]',
  unreadSession: '[data-rpa="session"][data-unread="true"]',
  activeCustomerName: '[data-rpa="active-customer-name"]',
  activeChannel: '[data-rpa="active-channel"]',
  latestInboundMessage: '[data-rpa="latest-inbound-message"]',
  replyEditor: '[data-rpa="reply-editor"]',
  sendButton: '[data-rpa="send-button"]',
  sendState: '[data-rpa="send-state"]',
  sentMessage: '[data-rpa="sent-message"]'
};

export function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export function isLocalTarget(url) {
  return url.startsWith("file://") || url.startsWith("http://127.0.0.1") || url.startsWith("http://localhost");
}

export function loadSelectorProfile(profilePath) {
  if (!profilePath) {
    return defaultSelectors;
  }
  const parsed = JSON.parse(fs.readFileSync(path.resolve(profilePath), "utf8"));
  return { ...defaultSelectors, ...parsed };
}

export function describeRpaBrowserAdapters() {
  return [
    {
      adapter: "cdp_browser_adapter",
      status: "implemented",
      transport: "Chrome DevTools Protocol",
      canAttachToExistingDebugTarget: true,
      canOperateCurrentNonDebugChromeWindow: false,
      defaultDeliveryMode: "fill_draft_only",
      sendAllowedByDefault: false,
      realPlatformSendRequiresAck: true,
      persistsRawPrivateMessages: false,
      notes: [
        "Use this adapter for local mock pages and Chrome profiles launched with remote debugging.",
        "It can fill a draft and can only click send when RPA_ALLOW_SEND=1 and the local/ack guard passes."
      ]
    },
    {
      adapter: "accessibility_browser_adapter",
      status: "contract_only_fail_closed",
      transport: "macOS Accessibility / operator-mediated Computer Use",
      canAttachToExistingDebugTarget: false,
      canOperateCurrentNonDebugChromeWindow: true,
      defaultDeliveryMode: "fill_draft_only",
      sendAllowedByDefault: false,
      realPlatformSendRequiresAck: true,
      persistsRawPrivateMessages: false,
      notes: [
        "Use this adapter boundary for already logged-in real browser pages that are not exposed through CDP.",
        "The standalone Node runner intentionally does not operate Accessibility yet; live use must stay operator-mediated and draft-only."
      ]
    }
  ];
}

async function createTarget(chromeEndpoint, url) {
  const res = await fetch(`${chromeEndpoint}/json/new?${encodeURIComponent(url)}`, { method: "PUT" });
  if (!res.ok) throw new Error(`Failed to create Chrome target: ${res.status}`);
  return res.json();
}

async function listTargets(chromeEndpoint) {
  const res = await fetch(`${chromeEndpoint}/json`);
  if (!res.ok) throw new Error(`Failed to list Chrome targets: ${res.status}`);
  return res.json();
}

async function closeTarget(chromeEndpoint, targetId) {
  await fetch(`${chromeEndpoint}/json/close/${targetId}`).catch(() => undefined);
}

function createCdp(wsUrl) {
  const ws = new WebSocket(wsUrl);
  let id = 0;
  const pending = new Map();
  return new Promise((resolve, reject) => {
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
    ws.addEventListener("message", (event) => {
      const msg = JSON.parse(event.data);
      if (msg.id && pending.has(msg.id)) {
        const { resolve, reject } = pending.get(msg.id);
        pending.delete(msg.id);
        if (msg.error) reject(new Error(JSON.stringify(msg.error)));
        else resolve(msg.result || {});
      }
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

async function clickSelector(cdp, selector) {
  return evalValue(
    cdp,
    `(() => {
      const selector = ${JSON.stringify(selector)};
      const el = document.querySelector(selector);
      if (!el || el.disabled) return false;
      el.click();
      return true;
    })()`
  );
}

async function fillSelector(cdp, selector, value) {
  return evalValue(
    cdp,
    `(() => {
      const selector = ${JSON.stringify(selector)};
      const value = ${JSON.stringify(value)};
      const el = document.querySelector(selector);
      if (!el) return false;
      el.focus();
      el.value = value;
      el.dispatchEvent(new InputEvent('input', { bubbles: true, inputType: 'insertText', data: value }));
      el.dispatchEvent(new Event('change', { bubbles: true }));
      return true;
    })()`
  );
}

export class CdpBrowserAdapter {
  constructor({ chromeEndpoint, targetUrl, attachUrlContains, outputDir }) {
    this.kind = "cdp_browser_adapter";
    this.chromeEndpoint = chromeEndpoint;
    this.targetUrl = targetUrl;
    this.attachUrlContains = attachUrlContains ?? "";
    this.outputDir = outputDir;
    this.target = null;
    this.cdp = null;
    this.closeWhenDone = false;
    this.resolvedUrl = "";
  }

  async open({ width = 1440, height = 960 } = {}) {
    if (!this.attachUrlContains.trim()) {
      this.target = await createTarget(this.chromeEndpoint, this.targetUrl);
      this.closeWhenDone = true;
      this.resolvedUrl = this.targetUrl;
    } else {
      const targets = await listTargets(this.chromeEndpoint);
      this.target = targets.find(
        (item) =>
          item.type === "page" && typeof item.url === "string" && item.url.includes(this.attachUrlContains)
      );
      if (!this.target) {
        throw new Error(`No open Chrome page matched RPA_ATTACH_URL_CONTAINS=${this.attachUrlContains}`);
      }
      this.closeWhenDone = false;
      this.resolvedUrl = this.target.url;
    }

    this.cdp = await createCdp(this.target.webSocketDebuggerUrl);
    await this.cdp.send("Page.enable");
    await this.cdp.send("Runtime.enable");
    await this.cdp.send("Emulation.setDeviceMetricsOverride", {
      width,
      height,
      deviceScaleFactor: 1,
      mobile: false
    });
    await waitFor(this.cdp, "document.readyState === 'complete'");
    return {
      adapter: this.kind,
      resolvedUrl: this.resolvedUrl,
      attachedExistingPage: !this.closeWhenDone,
      localTarget: isLocalTarget(this.resolvedUrl)
    };
  }

  async waitForPlatform(selectors) {
    return waitFor(this.cdp, `Boolean(document.querySelector(${JSON.stringify(selectors.platformRoot)}))`);
  }

  async selectUnreadSession(selectors) {
    return clickSelector(this.cdp, selectors.unreadSession);
  }

  async observeMessage(selectors) {
    return evalValue(
      this.cdp,
      `(() => {
        const s = ${JSON.stringify(selectors)};
        const text = document.querySelector(s.latestInboundMessage)?.textContent?.trim() ?? "";
        const customerName = document.querySelector(s.activeCustomerName)?.textContent?.trim() ?? "";
        const channel = document.querySelector(s.activeChannel)?.textContent?.trim() ?? "";
        return { text, customerName, channel };
      })()`
    );
  }

  async fillDraft(selectors, draft) {
    return fillSelector(this.cdp, selectors.replyEditor, draft);
  }

  async applySendPolicy(selectors, { allowSend, sendSafetyAck }) {
    let sendAttempted = false;
    let sentMessageCount = 0;
    let sendState = "";
    const realTargetSendAllowed =
      isLocalTarget(this.resolvedUrl) || sendSafetyAck === "I_UNDERSTAND_THIS_CAN_SEND";

    if (allowSend && realTargetSendAllowed) {
      sendAttempted = await clickSelector(this.cdp, selectors.sendButton);
      await delay(300);
      const sendResult = await evalValue(
        this.cdp,
        `(() => {
          const s = ${JSON.stringify(selectors)};
          return {
            sentMessageCount: document.querySelectorAll(s.sentMessage).length,
            sendState: document.querySelector(s.sendState)?.textContent?.trim() ?? ""
          };
        })()`
      );
      sentMessageCount = sendResult.sentMessageCount;
      sendState = sendResult.sendState;
    }

    return {
      sendAttempted,
      sentMessageCount,
      sendState,
      refusedReason:
        allowSend && !realTargetSendAllowed
          ? "RPA_ALLOW_SEND=1 was refused for non-local target without safety ack"
          : ""
    };
  }

  async finalState(selectors) {
    return evalValue(
      this.cdp,
      `(() => {
        const s = ${JSON.stringify(selectors)};
        return {
          editorValue: document.querySelector(s.replyEditor)?.value ?? "",
          sendState: document.querySelector(s.sendState)?.textContent?.trim() ?? "",
          sentMessageCount: document.querySelectorAll(s.sentMessage).length,
          overflowX: document.documentElement.scrollWidth > innerWidth || document.body.scrollWidth > innerWidth
        };
      })()`
    );
  }

  async capture(name) {
    fs.mkdirSync(this.outputDir, { recursive: true });
    const screenshot = await this.cdp.send("Page.captureScreenshot", {
      format: "png",
      fromSurface: true,
      captureBeyondViewport: false
    });
    fs.writeFileSync(path.join(this.outputDir, `${name}.png`), Buffer.from(screenshot.data, "base64"));
  }

  async close() {
    if (this.cdp) {
      this.cdp.close();
    }
    if (this.closeWhenDone && this.target?.id) {
      await closeTarget(this.chromeEndpoint, this.target.id);
    }
  }
}

export class AccessibilityBrowserAdapter {
  constructor() {
    this.kind = "accessibility_browser_adapter";
  }

  async open() {
    throw new Error(
      "accessibility_browser_adapter is contract-only in this standalone Node runner. Use operator-mediated Computer Use for live draft-only probes, or launch a CDP test profile."
    );
  }
}

export function createRpaBrowserAdapter(kind, config) {
  if (kind === "cdp" || kind === "cdp_browser_adapter") {
    return new CdpBrowserAdapter(config);
  }
  if (kind === "accessibility" || kind === "accessibility_browser_adapter") {
    return new AccessibilityBrowserAdapter(config);
  }
  throw new Error(`Unsupported RPA browser adapter: ${kind}`);
}

