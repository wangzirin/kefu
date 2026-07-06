import fs from "node:fs";
import path from "node:path";
import { pathToFileURL } from "node:url";
import {
  createRpaBrowserAdapter,
  describeRpaBrowserAdapters,
  isLocalTarget,
  loadSelectorProfile
} from "./lib/rpa_browser_adapters.mjs";

const chromeEndpoint = process.env.CHROME_DEBUGGING_URL ?? "http://127.0.0.1:9227";
const backendUrl = (process.env.STANDARD_OPS_BACKEND_URL ?? "http://127.0.0.1:8081").replace(/\/$/, "");
const outputDir = path.resolve(process.env.P3_06U_12E_OUTPUT ?? "output/p3_06u_12e_rpa_browser_reply_feasibility");
const mockPageUrl = pathToFileURL(
  path.resolve("research/rpa_browser_reply_feasibility/mock_platform_workbench.html")
).toString();
const targetUrl = process.env.RPA_TARGET_URL ?? mockPageUrl;
const attachUrlContains = process.env.RPA_ATTACH_URL_CONTAINS ?? "";
const adapterKind = process.env.RPA_BROWSER_ADAPTER ?? "cdp_browser_adapter";
const allowSend = process.env.RPA_ALLOW_SEND === "1";
const sendSafetyAck = process.env.RPA_REAL_PLATFORM_SEND_ACK ?? "";

async function loginLocalDev() {
  const res = await fetch(`${backendUrl}/api/auth/dev-local-login`, { method: "POST" });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`Local dev login failed: ${res.status} ${text}`);
  }
  return res.json();
}

async function runStrategy(message, token, resolvedUrl) {
  const res = await fetch(`${backendUrl}/api/rpa-copilot/strategy-dry-run`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`
    },
    body: JSON.stringify({
      channel: `${message.channel || "mock"}_rpa_browser`,
      customer_name: message.customerName || "测试客户",
      text: message.text,
      attachments: [],
      metadata: {
        entrypoint: "p3_06u_12e_rpa_browser_reply_feasibility",
        browser_adapter: adapterKind,
        target_kind: isLocalTarget(resolvedUrl) ? "local_mock_or_localhost" : "external_browser_page"
      }
    })
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`RPA strategy dry-run failed: ${res.status} ${text}`);
  }
  return res.json();
}

function summarizeStrategy(result) {
  return {
    mode: result.mode,
    delivery_mode: result.reply_strategy.delivery_mode,
    intent: result.reply_strategy.intent,
    next_best_action: result.reply_strategy.next_best_action,
    confidence: result.draft.confidence,
    citation_count: result.draft.citations.length,
    external_write_performed: Boolean(result.audit?.external_write_performed),
    action_external_write_count: result.actions.filter((action) => action.external_write).length
  };
}

function writeAdapterCapabilities() {
  fs.mkdirSync(outputDir, { recursive: true });
  const capabilities = describeRpaBrowserAdapters();
  fs.writeFileSync(path.join(outputDir, "rpa_browser_adapters.json"), JSON.stringify(capabilities, null, 2));
  console.log(JSON.stringify({ status: "passed", capabilities }, null, 2));
}

async function main() {
  fs.mkdirSync(outputDir, { recursive: true });
  if (process.env.RPA_PRINT_ADAPTER_CAPABILITIES === "1") {
    writeAdapterCapabilities();
    return;
  }

  const selectors = loadSelectorProfile(process.env.RPA_SELECTOR_PROFILE);
  const failures = [];
  const adapter = createRpaBrowserAdapter(adapterKind, {
    chromeEndpoint,
    targetUrl,
    attachUrlContains,
    outputDir
  });
  let browserSession = null;

  try {
    browserSession = await adapter.open({ width: 1440, height: 960 });
    await adapter.waitForPlatform(selectors);

    const clickedSession = await adapter.selectUnreadSession(selectors);
    if (!clickedSession) failures.push("RPA could not select unread session");
    await new Promise((resolve) => setTimeout(resolve, 300));

    const observedMessage = await adapter.observeMessage(selectors);
    if (!observedMessage.text) failures.push("RPA did not read latest inbound message");

    const login = failures.length === 0 ? await loginLocalDev() : null;
    const strategy = login ? await runStrategy(observedMessage, login.access_token, browserSession.resolvedUrl) : null;
    const draft = strategy?.draft?.text?.trim() ?? "";
    if (!draft) failures.push("Strategy returned empty draft");
    if (strategy?.audit?.external_write_performed) failures.push("Strategy audit indicates external write");
    if ((strategy?.actions ?? []).some((action) => action.external_write)) {
      failures.push("Strategy returned external-write action");
    }

    const filled = draft ? await adapter.fillDraft(selectors, draft) : false;
    if (!filled) failures.push("RPA could not fill reply editor");
    await adapter.capture("01-draft-filled");

    const sendPolicy = await adapter.applySendPolicy(selectors, { allowSend, sendSafetyAck });
    if (sendPolicy.refusedReason) failures.push(sendPolicy.refusedReason);
    if (allowSend && !sendPolicy.refusedReason) {
      if (!sendPolicy.sendAttempted) failures.push("RPA could not click send button");
      if (browserSession.localTarget && sendPolicy.sentMessageCount < 1) {
        failures.push("Mock send did not append sent message");
      }
    }

    await adapter.capture("02-after-send-policy");

    const finalState = await adapter.finalState(selectors);
    if (!finalState.editorValue.trim()) failures.push("Reply editor is empty at final state");
    if (finalState.overflowX) failures.push("Horizontal overflow detected in mock platform");

    const summary = {
      target: {
        adapter: adapter.kind,
        url: browserSession.resolvedUrl,
        attachedExistingPage: browserSession.attachedExistingPage,
        localTarget: browserSession.localTarget,
        allowSend,
        sendAttempted: sendPolicy.sendAttempted
      },
      observedMessage,
      strategy: strategy ? summarizeStrategy(strategy) : null,
      finalState,
      sentMessageCount: sendPolicy.sentMessageCount,
      sendState: sendPolicy.sendState,
      failures
    };
    fs.writeFileSync(path.join(outputDir, "summary.json"), JSON.stringify(summary, null, 2));
    if (failures.length > 0) {
      for (const failure of failures) console.error(`FAIL ${failure}`);
      process.exitCode = 1;
      return;
    }
    console.log(`P3-06U-12E RPA browser reply feasibility passed. Output: ${outputDir}`);
  } finally {
    await adapter.close?.();
  }
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
