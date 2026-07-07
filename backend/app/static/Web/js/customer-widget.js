(function () {
  var currentScript = document.currentScript;
  var commandQueue = window._WANFA && window._WANFA.a || [];
  var config = {};

  for (var i = 0; i < commandQueue.length; i += 1) {
    var command = commandQueue[i];
    if (command && command.length >= 2) {
      config[command[0]] = command[1];
    }
  }

  var componentId = config.cptid || currentScript && currentScript.getAttribute("data-component") || "website-widget";
  var tenantId = config.tenantId || currentScript && currentScript.getAttribute("data-tenant-id") || "";
  var apiBase = (config.apiBase || currentScript && currentScript.getAttribute("data-api-base") || "").replace(/\/$/, "");
  var position = config.position || currentScript && currentScript.getAttribute("data-position") || "right-bottom";
  var mode = config.mode || currentScript && currentScript.getAttribute("data-mode") || "widget";
  var buttonText = config.buttonText || currentScript && currentScript.getAttribute("data-button-text") || "在线咨询";
  var existing = document.querySelector('[data-wanfa-customer-widget="' + componentId + '"]');
  var composerMessagePrefix = "__WANFA_COMPOSER_MESSAGE_V1__";

  if (existing) {
    return;
  }

  var host = document.createElement("div");
  host.setAttribute("data-wanfa-customer-widget", componentId);
  host.style.position = "fixed";
  host.style.zIndex = "2147483000";
  host.style.right = position.indexOf("right") >= 0 ? "24px" : "auto";
  host.style.left = position.indexOf("left") >= 0 ? "24px" : "auto";
  host.style.bottom = "24px";
  document.body.appendChild(host);

  var shadow = host.attachShadow ? host.attachShadow({ mode: "open" }) : host;
  var style = document.createElement("style");
  style.textContent = [
    ":host{all:initial;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI','Microsoft YaHei',sans-serif}",
    ".wanfa-widget{width:320px;color:#142033;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI','Microsoft YaHei',sans-serif}",
    ".wanfa-button{display:flex;align-items:center;gap:8px;margin-left:auto;border:0;border-radius:999px;background:#1677ff;color:#fff;padding:12px 18px;box-shadow:0 14px 30px rgba(22,119,255,.28);font-size:14px;font-weight:700;cursor:pointer}",
    ".wanfa-button:hover{background:#0f63d8}",
    ".wanfa-panel{display:none;width:320px;height:min(520px,calc(100vh - 104px));min-height:360px;margin-bottom:12px;overflow:hidden;border:1px solid #dce6f2;border-radius:12px;background:#fff;box-shadow:0 22px 52px rgba(15,35,64,.22)}",
    ".wanfa-panel.open{display:flex;flex-direction:column}",
    ".wanfa-head{display:flex;align-items:center;justify-content:space-between;background:#1677ff;color:#fff;padding:14px 16px}",
    ".wanfa-head strong{font-size:15px}",
    ".wanfa-close{border:0;background:transparent;color:#fff;font-size:20px;line-height:1;cursor:pointer}",
    ".wanfa-body{flex:1;min-height:0;overflow-y:auto;padding:16px;background:#f8fbff;scroll-behavior:smooth}",
    ".wanfa-msg{margin:0 0 12px;border-radius:10px;background:#fff;color:#23364d;padding:12px 13px;font-size:14px;line-height:1.55;box-shadow:0 1px 0 rgba(15,35,64,.06)}",
    ".wanfa-msg.agent{background:#eaf3ff;color:#153a66}",
    ".wanfa-msg.system{background:#f1f4f8;color:#607086;text-align:center}",
    ".wanfa-rich{display:grid;gap:8px}",
    ".wanfa-rich-text{white-space:pre-wrap;word-break:break-word}",
    ".wanfa-attachment,.wanfa-rating{display:grid;grid-template-columns:34px minmax(0,1fr) auto;gap:8px;align-items:center;border:1px solid rgba(67,104,148,.18);border-radius:8px;background:rgba(255,255,255,.62);padding:8px}",
    ".wanfa-attachment-icon{display:grid;place-items:center;width:34px;height:34px;border-radius:7px;background:#fff;color:#1677ff;font-size:16px}",
    ".wanfa-attachment img{width:34px;height:34px;border-radius:7px;object-fit:cover;background:#fff}",
    ".wanfa-attachment strong,.wanfa-attachment small,.wanfa-rating strong,.wanfa-rating small{display:block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}",
    ".wanfa-attachment strong,.wanfa-rating strong{font-size:13px}",
    ".wanfa-attachment small,.wanfa-rating small{color:#617089;font-size:12px}",
    ".wanfa-attachment a{color:#0b63ce;font-size:12px;font-weight:700;text-decoration:none;white-space:nowrap}",
    ".wanfa-rating-options{grid-column:1/-1;display:flex;gap:6px;flex-wrap:wrap}",
    ".wanfa-rating-options button{border:1px solid #cfe0f6;border-radius:999px;background:#fff;color:#1d4f86;padding:6px 10px;font-size:12px;font-weight:700}",
    ".wanfa-actions{display:none;gap:8px;margin-top:8px}",
    ".wanfa-actions.show{display:flex}",
    ".wanfa-actions button{flex:1;border:1px solid #c9d8ea;border-radius:8px;background:#fff;color:#1d4f86;padding:9px 10px;font-size:13px;font-weight:700;cursor:pointer}",
    ".wanfa-actions button:first-child{border-color:#1677ff;background:#1677ff;color:#fff}",
    ".wanfa-input{display:flex;gap:8px;border-top:1px solid #e7edf5;background:#fff;padding:12px}",
    ".wanfa-input input{flex:1;min-width:0;border:1px solid #d7dfea;border-radius:8px;padding:10px 11px;font-size:13px;outline:none}",
    ".wanfa-input button{border:0;border-radius:8px;background:#1677ff;color:#fff;padding:0 14px;font-size:13px;font-weight:700;cursor:pointer}",
    ".wanfa-input button:disabled{background:#b8c4d2;cursor:not-allowed}",
    ".wanfa-note{margin:10px 0 0;color:#71839a;font-size:12px;line-height:1.45}",
    "@media (max-width:420px){.wanfa-widget,.wanfa-panel{width:calc(100vw - 32px)}.wanfa-panel{height:min(520px,calc(100vh - 96px));min-height:340px}}"
  ].join("");

  var wrapper = document.createElement("div");
  wrapper.className = "wanfa-widget";
  wrapper.innerHTML = [
    '<section class="wanfa-panel" aria-label="网站客服窗口">',
    '  <header class="wanfa-head">',
    "    <strong>在线客服</strong>",
    '    <button type="button" class="wanfa-close" aria-label="关闭">×</button>',
    "  </header>",
    '  <div class="wanfa-body">',
    '    <p class="wanfa-msg">您好，请问有什么可以帮您？</p>',
    '    <p class="wanfa-note">发送后会进入客服工作台的网站客服会话。</p>',
    '    <div class="wanfa-actions" aria-label="会话结束后的操作">',
    '      <button type="button" class="wanfa-continue">继续聊天</button>',
    '      <button type="button" class="wanfa-leave-message">留言</button>',
    "    </div>",
    "  </div>",
    '  <form class="wanfa-input">',
    '    <input type="text" placeholder="请输入你的问题" aria-label="请输入你的问题" />',
    '    <button type="submit">发送</button>',
    "  </form>",
    "</section>",
    '<button type="button" class="wanfa-button" aria-label="打开在线客服">' + buttonText + '</button>'
  ].join("");

  shadow.appendChild(style);
  shadow.appendChild(wrapper);

  var panel = wrapper.querySelector(".wanfa-panel");
  var openButton = wrapper.querySelector(".wanfa-button");
  var closeButton = wrapper.querySelector(".wanfa-close");
  var form = wrapper.querySelector(".wanfa-input");
  var input = wrapper.querySelector(".wanfa-input input");
  var submitButton = wrapper.querySelector(".wanfa-input button");
  var body = wrapper.querySelector(".wanfa-body");
  var actionBar = wrapper.querySelector(".wanfa-actions");
  var continueButton = wrapper.querySelector(".wanfa-continue");
  var leaveMessageButton = wrapper.querySelector(".wanfa-leave-message");
  var pollingStarted = false;
  var lastSeenMessageId = 0;
  var conversationClosed = false;
  var reopenAction = "";
  var reopenPending = false;

  function appendMessage(text, type) {
    var message = document.createElement("p");
    message.className = type ? "wanfa-msg " + type : "wanfa-msg";
    message.textContent = text;
    body.appendChild(message);
    body.scrollTop = body.scrollHeight;
    return message;
  }

  function appendAgentMessage(content) {
    var richContent = parseComposerMessageContent(content || "");
    if (!richContent) {
      appendMessage("客服：" + content, "agent");
      return;
    }
    var message = document.createElement("div");
    message.className = "wanfa-msg agent";
    var rich = document.createElement("div");
    rich.className = "wanfa-rich";
    if (richContent.text) {
      var text = document.createElement("div");
      text.className = "wanfa-rich-text";
      text.textContent = "客服：" + richContent.text;
      rich.appendChild(text);
    }
    for (var i = 0; i < richContent.attachments.length; i += 1) {
      rich.appendChild(createAttachmentNode(richContent.attachments[i]));
    }
    if (richContent.ratingInvite) {
      rich.appendChild(createRatingNode(richContent.ratingInvite));
    }
    if (!rich.childNodes.length) {
      rich.textContent = "客服发送了一条消息";
    }
    message.appendChild(rich);
    body.appendChild(message);
    body.scrollTop = body.scrollHeight;
  }

  function createAttachmentNode(attachment) {
    var node = document.createElement("div");
    node.className = "wanfa-attachment";
    if (attachment.kind === "image" && attachment.dataUrl) {
      var image = document.createElement("img");
      image.alt = "";
      image.src = attachment.dataUrl;
      node.appendChild(image);
    } else {
      var icon = document.createElement("span");
      icon.className = "wanfa-attachment-icon";
      icon.textContent = attachment.kind === "image" ? "图" : "文";
      node.appendChild(icon);
    }
    var copy = document.createElement("span");
    var name = document.createElement("strong");
    name.textContent = attachment.name || "附件";
    var meta = document.createElement("small");
    meta.textContent = (attachment.kind === "image" ? "图片" : "文件") + " · " + formatFileSize(attachment.size || 0)
      + (attachment.inlineStored ? "" : " · 仅记录名称");
    copy.appendChild(name);
    copy.appendChild(meta);
    node.appendChild(copy);
    if (attachment.dataUrl) {
      var link = document.createElement("a");
      link.href = attachment.dataUrl;
      link.download = attachment.name || "attachment";
      link.textContent = "下载";
      node.appendChild(link);
    }
    return node;
  }

  function createRatingNode(invite) {
    var node = document.createElement("div");
    node.className = "wanfa-rating";
    var icon = document.createElement("span");
    icon.className = "wanfa-attachment-icon";
    icon.textContent = "评";
    var copy = document.createElement("span");
    var title = document.createElement("strong");
    title.textContent = invite.title || "服务评价邀请";
    var description = document.createElement("small");
    description.textContent = invite.description || "感谢您的咨询，麻烦对本次服务做个评价。";
    var options = document.createElement("div");
    options.className = "wanfa-rating-options";
    for (var i = 0; i < invite.options.length; i += 1) {
      var option = document.createElement("button");
      option.type = "button";
      option.textContent = invite.options[i];
      options.appendChild(option);
    }
    copy.appendChild(title);
    copy.appendChild(description);
    node.appendChild(icon);
    node.appendChild(copy);
    node.appendChild(options);
    return node;
  }

  function parseComposerMessageContent(content) {
    if (!content || content.indexOf(composerMessagePrefix) !== 0) {
      return null;
    }
    try {
      var raw = JSON.parse(content.slice(composerMessagePrefix.length));
      var attachments = Array.isArray(raw.attachments) ? raw.attachments : [];
      var normalizedAttachments = [];
      for (var i = 0; i < attachments.length; i += 1) {
        if (!attachments[i] || typeof attachments[i] !== "object") {
          continue;
        }
        normalizedAttachments.push({
          kind: attachments[i].kind === "image" ? "image" : "file",
          name: String(attachments[i].name || "附件 " + (i + 1)),
          size: Number(attachments[i].size || 0),
          inlineStored: attachments[i].inlineStored === true || Boolean(sanitizeAttachmentDataUrl(attachments[i].dataUrl)),
          dataUrl: sanitizeAttachmentDataUrl(attachments[i].dataUrl)
        });
      }
      var rawInvite = raw.ratingInvite && typeof raw.ratingInvite === "object" ? raw.ratingInvite : null;
      return {
        text: typeof raw.text === "string" ? raw.text : "",
        attachments: normalizedAttachments,
        ratingInvite: rawInvite ? {
          title: typeof rawInvite.title === "string" ? rawInvite.title : "服务评价邀请",
          description: typeof rawInvite.description === "string" ? rawInvite.description : "感谢您的咨询，麻烦对本次服务做个评价。",
          options: Array.isArray(rawInvite.options) ? rawInvite.options : ["满意", "一般", "不满意"]
        } : null
      };
    } catch (error) {
      return null;
    }
  }

  function sanitizeAttachmentDataUrl(value) {
    if (typeof value !== "string") {
      return "";
    }
    return /^data:[a-z0-9.+-]+\/[a-z0-9.+-]+;base64,/i.test(value) ? value : "";
  }

  function formatFileSize(bytes) {
    if (!bytes || !isFinite(bytes) || bytes <= 0) {
      return "0 B";
    }
    if (bytes < 1024) {
      return bytes + " B";
    }
    var kilobytes = bytes / 1024;
    if (kilobytes < 1024) {
      return (kilobytes >= 10 ? kilobytes.toFixed(0) : kilobytes.toFixed(1)) + " KB";
    }
    var megabytes = kilobytes / 1024;
    if (megabytes < 1024) {
      return (megabytes >= 10 ? megabytes.toFixed(0) : megabytes.toFixed(1)) + " MB";
    }
    return (megabytes / 1024).toFixed(1) + " GB";
  }

  function getVisitorId() {
    var storageKey = "wanfa_visitor_id_" + componentId;
    var visitorId = "";
    try {
      visitorId = window.localStorage && localStorage.getItem(storageKey) || "";
      if (!visitorId) {
        visitorId = "website-" + Date.now() + "-" + Math.random().toString(36).slice(2, 10);
        if (window.localStorage) {
          localStorage.setItem(storageKey, visitorId);
        }
      }
    } catch (error) {
      visitorId = "website-" + Date.now() + "-" + Math.random().toString(36).slice(2, 10);
    }
    return visitorId;
  }

  function getLastSeenStorageKey() {
    return "wanfa_last_seen_message_id_" + componentId + "_" + getVisitorId();
  }

  function loadLastSeenMessageId() {
    try {
      lastSeenMessageId = Number(window.localStorage && localStorage.getItem(getLastSeenStorageKey()) || "0") || 0;
    } catch (error) {
      lastSeenMessageId = lastSeenMessageId || 0;
    }
    return lastSeenMessageId;
  }

  function saveLastSeenMessageId(messageId) {
    if (!messageId || messageId <= lastSeenMessageId) {
      return;
    }
    lastSeenMessageId = messageId;
    try {
      if (window.localStorage) {
        localStorage.setItem(getLastSeenStorageKey(), String(lastSeenMessageId));
      }
    } catch (error) {
      // Local storage may be unavailable on some embedded pages.
    }
  }

  function markConversationClosed() {
    if (reopenPending || reopenAction) {
      return;
    }
    if (conversationClosed) {
      return;
    }
    conversationClosed = true;
    input.disabled = true;
    submitButton.disabled = true;
    input.placeholder = "本次咨询已结束";
    actionBar.classList.add("show");
  }

  function prepareReopen(action) {
    reopenAction = action;
    conversationClosed = false;
    input.disabled = false;
    submitButton.disabled = false;
    actionBar.classList.remove("show");
    if (action === "leave_message") {
      input.placeholder = "请留下问题和联系方式";
      appendMessage("请留下你的问题和联系方式，客服会尽快处理。", "system");
    } else {
      input.placeholder = "请继续输入你的问题";
      appendMessage("正在为你重新接入客服...", "system");
      sendMessageToWorkbench("访客选择继续聊天", "continue_chat", true);
    }
    input.focus();
  }

  function pollAgentMessages() {
    if (!apiBase || !tenantId || !window.fetch) {
      return;
    }
    var visitorId = getVisitorId();
    var afterId = loadLastSeenMessageId();
    var query = "?tenant_id=" + encodeURIComponent(tenantId)
      + "&visitor_id=" + encodeURIComponent(visitorId)
      + "&after_id=" + encodeURIComponent(afterId);
    fetch(apiBase + "/api/public/website-widget/messages" + query)
      .then(function (response) {
        if (!response.ok) {
          throw new Error("HTTP " + response.status);
        }
        return response.json();
      })
      .then(function (result) {
        var messages = result.messages || [];
        for (var i = 0; i < messages.length; i += 1) {
          if (messages[i].sender_type === "system") {
            appendMessage(messages[i].content || "本次咨询已结束", "system");
          } else {
            appendAgentMessage(messages[i].content || "");
          }
          saveLastSeenMessageId(messages[i].id);
        }
        if (result.conversation_status === "closed" && !reopenPending && !reopenAction) {
          if (!conversationClosed && !messages.length) {
            appendMessage("客服已关闭对话，本次咨询已结束。", "system");
          }
          markConversationClosed();
        }
      })
      .catch(function () {
        // Polling failures stay quiet so the visitor can keep typing.
      });
  }

  function startPolling() {
    if (pollingStarted) {
      return;
    }
    pollingStarted = true;
    pollAgentMessages();
    window.setInterval(pollAgentMessages, 3000);
  }

  function openPanel() {
    panel.classList.add("open");
    startPolling();
  }

  function closePanel() {
    panel.classList.remove("open");
  }

  openButton.addEventListener("click", openPanel);
  if (mode === "link") {
    openButton.style.borderRadius = "8px";
  }
  closeButton.addEventListener("click", closePanel);
  continueButton.addEventListener("click", function () {
    prepareReopen("continue_chat");
  });
  leaveMessageButton.addEventListener("click", function () {
    prepareReopen("leave_message");
  });

  function sendMessageToWorkbench(value, action, silentVisitorMessage) {
    if (conversationClosed) {
      appendMessage("本次咨询已结束，请选择继续聊天或留言。", "system");
      return Promise.resolve();
    }
    if (!value) {
      return Promise.resolve();
    }
    if (!silentVisitorMessage) {
      appendMessage("我：" + value);
      input.value = "";
    }
    if (!apiBase || !tenantId || !window.fetch) {
      appendMessage("当前插件还没有配置后端地址或租户 ID，消息暂未进入客服工作台。");
      return Promise.resolve();
    }
    reopenPending = Boolean(action);
    var visitorId = getVisitorId();
    return fetch(apiBase + "/api/public/website-widget/messages", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        tenant_id: Number(tenantId),
        component_id: componentId,
        visitor_id: visitorId,
        visitor_name: "网站访客",
        text: value,
        page_url: window.location.href,
        page_title: document.title,
        reopen_action: action || reopenAction
      })
    })
      .then(function (response) {
        if (response.status === 409) {
          reopenPending = false;
          markConversationClosed();
          appendMessage("客服已关闭对话，本次咨询已结束。", "system");
          throw new Error("conversation closed");
        }
        if (!response.ok) {
          throw new Error("HTTP " + response.status);
        }
        return response.json();
      })
      .then(function (result) {
        saveLastSeenMessageId(result.message_id);
        if (result.is_new_conversation) {
          if ((action || reopenAction) === "leave_message") {
            appendMessage("留言已提交，客服会尽快处理。", "system");
          } else if ((action || reopenAction) === "continue_chat") {
            appendMessage("已重新接入客服，会话 #" + (result.conversation_id || "-") + " 已进入工作台。", "system");
          } else {
            appendMessage("客服已收到，会话 #" + (result.conversation_id || "-") + " 已进入工作台。");
          }
        }
        reopenAction = "";
        reopenPending = false;
        startPolling();
        pollAgentMessages();
      })
      .catch(function (error) {
        reopenPending = false;
        if (error && error.message === "conversation closed") {
          return;
        }
        appendMessage("发送失败，请确认客服后端已启动，并允许当前网站访问。");
      });
  }

  form.addEventListener("submit", function (event) {
    event.preventDefault();
    var value = input.value.trim();
    if (!value) {
      return;
    }
    sendMessageToWorkbench(value, reopenAction, false);
  });
})();
