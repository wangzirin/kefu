def _bootstrap_owner(client, slug: str = "connector-demo", email: str = "connector-owner@example.com") -> tuple[dict, str]:
    tenant_res = client.post("/api/tenants", json={"name": f"{slug} 客户", "slug": slug})
    assert tenant_res.status_code == 201
    tenant = tenant_res.json()

    role_res = client.post(
        f"/api/tenants/{tenant['id']}/roles",
        json={"code": "owner", "name": "管理员"},
    )
    assert role_res.status_code == 201
    role = role_res.json()

    user_res = client.post(
        f"/api/tenants/{tenant['id']}/users",
        json={"name": "渠道主管", "email": email, "password": "ChangeMe123!"},
    )
    assert user_res.status_code == 201
    user = user_res.json()

    assign_res = client.post(f"/api/users/{user['id']}/roles", json={"role_id": role["id"]})
    assert assign_res.status_code == 201

    login_res = client.post(
        "/api/auth/login",
        json={"tenant_slug": tenant["slug"], "email": email, "password": "ChangeMe123!"},
    )
    assert login_res.status_code == 200
    return tenant, login_res.json()["access_token"]


def _conversation_with_message(
    client, tenant_id: int, headers: dict, *, channel_type: str = "wecom"
) -> tuple[dict, dict, dict]:
    channel_res = client.post(
        f"/api/tenants/{tenant_id}/channels",
        json={"type": channel_type, "name": "企业微信客服", "reply_mode": "assist", "status": "active"},
    )
    assert channel_res.status_code == 201
    channel = channel_res.json()
    contact = client.post(
        f"/api/tenants/{tenant_id}/contacts",
        json={"display_name": "渠道验证访客"},
    ).json()
    conversation_res = client.post(
        f"/api/tenants/{tenant_id}/conversations",
        headers=headers,
        json={
            "channel_id": channel["id"],
            "contact_id": contact["id"],
            "subject": "渠道发送前置设计",
        },
    )
    assert conversation_res.status_code == 201
    conversation = conversation_res.json()
    message_res = client.post(
        f"/api/conversations/{conversation['id']}/messages",
        headers=headers,
        json={
            "direction": "inbound",
            "sender_type": "visitor",
            "content": "这条回复会真的发到微信吗？",
        },
    )
    assert message_res.status_code == 201
    return channel, conversation, message_res.json()


def _ready_outbox_draft(client, tenant_id: int, headers: dict) -> tuple[dict, dict]:
    channel, conversation, message = _conversation_with_message(client, tenant_id, headers)
    run = client.post(
        f"/api/conversations/{conversation['id']}/workflow-runs",
        headers=headers,
        json={
            "trigger_message_id": message["id"],
            "workflow_type": "customer_reply",
            "current_step": "classify_intent",
            "state_payload": {"source": "connector_contract_test"},
        },
    ).json()
    review = client.post(
        f"/api/workflow-runs/{run['id']}/human-review-tasks",
        headers=headers,
        json={
            "reason": "risk_level_medium",
            "risk_level": "medium",
            "draft_reply": "当前阶段只生成官方渠道发送计划，不会真实外发。",
        },
    ).json()
    approved = client.patch(
        f"/api/human-review-tasks/{review['id']}",
        headers=headers,
        json={
            "decision": "approved",
            "final_reply": "当前阶段只生成官方渠道发送计划，不会真实外发。",
            "resolution_note": "确认 P2-11 不打开外部写入",
        },
    ).json()
    draft = client.post(
        f"/api/human-review-tasks/{approved['id']}/outbox-drafts",
        headers=headers,
        json={},
    ).json()
    ready = client.post(
        f"/api/outbox-drafts/{draft['id']}/confirmation",
        headers=headers,
        json={"confirmation_note": "进入官方 connector 发送计划检查"},
    ).json()
    return channel, ready


def _create_connector(
    client,
    channel_id: int,
    headers: dict,
    *,
    provider: str = "wecom",
    display_name: str = "企业微信客服官方接口占位",
    capabilities: list[str] | None = None,
    public_config: dict | None = None,
    webhook_path: str | None = None,
    signature_mode: str = "wecom_token_aeskey",
) -> dict:
    default_public_config = public_config
    if default_public_config is None and provider == "wecom":
        default_public_config = {
            "enterprise_name": "测试企业",
            "corp_id": "ww_test_corp",
            "agent_id": "1000001",
            "callback_url": webhook_path or f"/api/webhooks/{provider}/channels/{channel_id}",
        }
    res = client.post(
        f"/api/channels/{channel_id}/connector-config",
        headers=headers,
        json={
            "provider": provider,
            "mode": "noop",
            "status": "ready",
            "display_name": display_name,
            "capabilities": capabilities or ["send_text", "delivery_receipt"],
            "public_config": default_public_config or {"corp_id_placeholder": "configured_in_secret_store"},
            "webhook_path": webhook_path or f"/api/webhooks/{provider}/channels/{channel_id}",
            "signature_mode": signature_mode,
        },
    )
    assert res.status_code == 201
    return res.json()


def test_channel_connector_config_and_noop_send_plan_never_external_writes(client) -> None:
    tenant, token = _bootstrap_owner(client)
    headers = {"Authorization": f"Bearer {token}"}
    channel, ready = _ready_outbox_draft(client, tenant["id"], headers)

    connector = _create_connector(client, channel["id"], headers)

    assert connector["tenant_id"] == tenant["id"]
    assert connector["channel_id"] == channel["id"]
    assert connector["provider"] == "wecom"
    assert connector["mode"] == "noop"
    assert connector["status"] == "ready"
    assert connector["external_write_enabled"] is False
    assert connector["secret_status"] == "not_configured"
    assert "secret" not in connector
    assert connector["webhook_path"].endswith(f"/channels/{channel['id']}")
    assert connector["signature_mode"] == "wecom_token_aeskey"

    get_res = client.get(f"/api/channels/{channel['id']}/connector-config", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["id"] == connector["id"]

    plan_res = client.post(
        f"/api/outbox-drafts/{ready['id']}/connector-send-plans",
        headers=headers,
        json={},
    )

    assert plan_res.status_code == 201
    attempt = plan_res.json()
    assert attempt["outbox_draft_id"] == ready["id"]
    assert attempt["delivery_mode"] == "connector_noop"
    assert attempt["provider"] == "wecom"
    assert attempt["status"] == "blocked"
    assert attempt["delivery_status"] == "not_sent"
    assert attempt["external_message_id"] == ""
    assert attempt["sent_at"] is None
    assert attempt["request_payload"]["external_write"] is False
    assert attempt["request_payload"]["connector"]["mode"] == "noop"
    assert attempt["response_payload"]["external_write"] is False
    assert attempt["response_payload"]["official_api_enabled"] is False
    assert "external_delivery_disabled" in attempt["response_payload"]["blocked_reasons"]
    assert attempt["response_payload"]["receipt_contract"]["status"] == "placeholder"
    assert attempt["response_payload"]["retry_contract"]["queue"] == "not_configured"
    assert attempt["response_payload"]["webhook_requirements"]["signature_required"] is True

    audit_res = client.get(f"/api/tenants/{tenant['id']}/audit-events", headers=headers)
    actions = [event["action"] for event in audit_res.json()]
    assert "channel_connector.configured" in actions
    assert "channel_connector.send_plan_created" in actions


def test_ai_service_status_and_connector_secrets_never_return_plaintext(client, monkeypatch, tmp_path) -> None:
    tenant, token = _bootstrap_owner(
        client,
        slug="connector-secret-status",
        email="connector-secret-status@example.com",
    )
    headers = {"Authorization": f"Bearer {token}"}
    monkeypatch.delenv("BAILIAN_API_KEY", raising=False)
    status_res = client.get(f"/api/tenants/{tenant['id']}/ai-service-status", headers=headers)
    assert status_res.status_code == 200
    status_body = status_res.json()
    assert status_body["status"] == "not_configured"
    assert status_body["secret_included"] is False
    assert "key" not in str(status_body).lower()

    monkeypatch.setenv("BAILIAN_API_KEY", "test-only-placeholder")
    ready_res = client.get(f"/api/tenants/{tenant['id']}/ai-service-status", headers=headers)
    assert ready_res.status_code == 200
    ready_body = ready_res.json()
    assert ready_body["status"] == "ready"
    assert ready_body["secret_included"] is False
    assert "test-only-placeholder" not in str(ready_body)

    monkeypatch.setattr(
        "app.services.channel_secret_store._secret_store_path",
        lambda: tmp_path / "local_channel_secrets.json",
    )
    channel, _ready = _ready_outbox_draft(client, tenant["id"], headers)
    _create_connector(client, channel["id"], headers)
    secret_res = client.post(
        f"/api/channels/{channel['id']}/connector-secrets",
        headers=headers,
        json={
            "secrets": {
                "token": "token-should-not-return",
                "encoding_aes_key": "aes-should-not-return",
                "app_secret": "secret-should-not-return",
            }
        },
    )
    assert secret_res.status_code == 200
    secret_body = secret_res.json()
    assert secret_body["status"] == "configured"
    assert secret_body["secret_included"] is False
    assert secret_body["field_status"] == {
        "app_secret": "configured",
        "encoding_aes_key": "configured",
        "token": "configured",
    }
    assert "should-not-return" not in str(secret_body)

    verification_res = client.post(f"/api/channels/{channel['id']}/connector-verification", headers=headers)
    assert verification_res.status_code == 200
    verification = verification_res.json()
    assert verification["status"] == "verified"
    assert verification["external_write_enabled"] is False
    assert verification["secret_included"] is False


def test_connector_secrets_upsert_creates_missing_wecom_connector(client, monkeypatch, tmp_path) -> None:
    tenant, token = _bootstrap_owner(
        client,
        slug="connector-secret-fallback",
        email="connector-secret-fallback@example.com",
    )
    headers = {"Authorization": f"Bearer {token}"}
    monkeypatch.setattr(
        "app.services.channel_secret_store._secret_store_path",
        lambda: tmp_path / "local_channel_secrets.json",
    )
    channel_res = client.post(
        f"/api/tenants/{tenant['id']}/channels",
        headers=headers,
        json={"type": "wecom", "name": "企业微信", "reply_mode": "assist", "status": "active"},
    )
    assert channel_res.status_code == 201
    channel = channel_res.json()

    secret_res = client.post(
        f"/api/channels/{channel['id']}/connector-secrets",
        headers=headers,
        json={
            "secrets": {
                "token": "fixed-wecom-token",
                "encoding_aes_key": "abcdefghijklmnopqrstuvwxyzABCDEFG1234567",
            }
        },
    )

    assert secret_res.status_code == 200
    secret_status = secret_res.json()
    assert secret_status["provider"] == "wecom"
    assert secret_status["status"] == "configured"
    assert secret_status["field_status"] == {
        "encoding_aes_key": "configured",
        "token": "configured",
    }

    connector_res = client.get(f"/api/channels/{channel['id']}/connector-config", headers=headers)
    assert connector_res.status_code == 200
    connector = connector_res.json()
    assert connector["provider"] == "wecom"
    assert connector["signature_mode"] == "wecom_token_aeskey"
    assert connector["public_config"]["credential_ref"] == f"local:channel_connector:{connector['id']}"


def test_channel_connector_authorization_session_supports_qr_only_for_wechat_providers(client) -> None:
    tenant, token = _bootstrap_owner(
        client,
        slug="connector-authorization-session",
        email="connector-authorization-session@example.com",
    )
    headers = {"Authorization": f"Bearer {token}"}
    website_channel = client.post(
        f"/api/tenants/{tenant['id']}/channels",
        headers=headers,
        json={"type": "website", "name": "官网", "reply_mode": "assist", "status": "planned"},
    ).json()
    wechat_channel = client.post(
        f"/api/tenants/{tenant['id']}/channels",
        headers=headers,
        json={"type": "wechat_kf", "name": "微信客服", "reply_mode": "assist", "status": "planned"},
    ).json()

    website_qr = client.post(
        f"/api/channels/{website_channel['id']}/connector-authorization",
        headers=headers,
        json={"provider": "website", "connect_mode": "qr"},
    )
    assert website_qr.status_code == 409

    auth_res = client.post(
        f"/api/channels/{wechat_channel['id']}/connector-authorization",
        headers=headers,
        json={"provider": "wechat_kf", "connect_mode": "qr", "redirect_uri": "http://127.0.0.1:5177/#channels"},
    )
    assert auth_res.status_code == 200
    auth_body = auth_res.json()
    assert auth_body["provider"] == "wechat_kf"
    assert auth_body["connect_mode"] == "qr"
    assert auth_body["status"] == "pending"
    assert auth_body["secret_included"] is False
    assert "state=" in auth_body["authorization_url"]
    assert "should-not-return" not in str(auth_body)

    connector_res = client.get(f"/api/channels/{wechat_channel['id']}/connector-config", headers=headers)
    assert connector_res.status_code == 200
    connector = connector_res.json()
    assert connector["status"] == "auth_pending"
    assert connector["public_config"]["authorization"]["status"] == "pending"
    assert connector["external_write_enabled"] is False


def test_public_website_widget_message_enters_conversation_inbox(client) -> None:
    tenant, token = _bootstrap_owner(
        client,
        slug="website-widget-public",
        email="website-widget-public@example.com",
    )
    headers = {"Authorization": f"Bearer {token}"}

    widget_res = client.post(
        "/api/public/website-widget/messages",
        json={
            "tenant_id": tenant["id"],
            "component_id": "website-widget",
            "visitor_id": "visitor-public-001",
            "visitor_name": "官网访客",
            "text": "我想咨询餐饮门店怎么接入 AI 客服",
            "page_url": "https://example.com/",
            "page_title": "餐饮行业 AI 转型专家",
        },
    )

    assert widget_res.status_code == 201
    widget = widget_res.json()
    assert widget["tenant_id"] == tenant["id"]
    assert widget["status"] == "trusted_inbound_message_created"
    assert widget["conversation_id"]
    assert widget["message_id"]
    assert widget["is_new_conversation"] is True
    assert widget["conversation_status"] == "queued_for_me"

    second_widget_res = client.post(
        "/api/public/website-widget/messages",
        json={
            "tenant_id": tenant["id"],
            "component_id": "website-widget",
            "visitor_id": "visitor-public-001",
            "visitor_name": "官网访客",
            "text": "我再补充一句",
            "page_url": "https://example.com/",
            "page_title": "餐饮行业 AI 转型专家",
        },
    )
    assert second_widget_res.status_code == 201
    second_widget = second_widget_res.json()
    assert second_widget["conversation_id"] == widget["conversation_id"]
    assert second_widget["is_new_conversation"] is False

    inbox_res = client.get(f"/api/tenants/{tenant['id']}/conversation-inbox", headers=headers)
    assert inbox_res.status_code == 200
    inbox = inbox_res.json()
    assert inbox["total"] >= 1
    assert any(item["id"] == widget["conversation_id"] for item in inbox["items"])

    reply_res = client.post(
        f"/api/conversations/{widget['conversation_id']}/messages",
        headers=headers,
        json={
            "direction": "outbound",
            "sender_type": "agent",
            "content": "您好，网站客服已经收到您的咨询。",
            "external_message_id": "",
        },
    )
    assert reply_res.status_code == 201
    reply = reply_res.json()

    poll_res = client.get(
        "/api/public/website-widget/messages",
        params={
            "tenant_id": tenant["id"],
            "visitor_id": "visitor-public-001",
            "after_id": widget["message_id"],
        },
    )
    assert poll_res.status_code == 200
    poll = poll_res.json()
    assert poll["conversation_id"] == widget["conversation_id"]
    assert poll["conversation_status"] == "queued_for_me"
    assert poll["messages"] == [
        {
            "id": reply["id"],
            "conversation_id": widget["conversation_id"],
            "direction": "outbound",
            "sender_type": "agent",
            "content": "您好，网站客服已经收到您的咨询。",
            "created_at": reply["created_at"],
        }
    ]

    empty_poll_res = client.get(
        "/api/public/website-widget/messages",
        params={
            "tenant_id": tenant["id"],
            "visitor_id": "visitor-public-001",
            "after_id": reply["id"],
        },
    )
    assert empty_poll_res.status_code == 200
    assert empty_poll_res.json()["messages"] == []

    close_res = client.post(
        f"/api/conversations/{widget['conversation_id']}/workflow-actions",
        headers=headers,
        json={"action": "close", "note": "网站会话已结束"},
    )
    assert close_res.status_code == 200
    assert close_res.json()["status"] == "closed"

    closed_poll_res = client.get(
        "/api/public/website-widget/messages",
        params={
            "tenant_id": tenant["id"],
            "visitor_id": "visitor-public-001",
            "after_id": reply["id"],
        },
    )
    assert closed_poll_res.status_code == 200
    closed_poll = closed_poll_res.json()
    assert closed_poll["conversation_id"] == widget["conversation_id"]
    assert closed_poll["conversation_status"] == "closed"
    assert closed_poll["messages"][0]["sender_type"] == "system"
    assert closed_poll["messages"][0]["content"] == "客服已关闭对话，本次咨询已结束。"

    closed_send_res = client.post(
        "/api/public/website-widget/messages",
        json={
            "tenant_id": tenant["id"],
            "component_id": "website-widget",
            "visitor_id": "visitor-public-001",
            "visitor_name": "官网访客",
            "text": "关闭后还能发吗",
            "page_url": "https://example.com/",
            "page_title": "餐饮行业 AI 转型专家",
        },
    )
    assert closed_send_res.status_code == 409
    assert closed_send_res.json()["detail"] == "conversation closed"

    continue_res = client.post(
        "/api/public/website-widget/messages",
        json={
            "tenant_id": tenant["id"],
            "component_id": "website-widget",
            "visitor_id": "visitor-public-001",
            "visitor_name": "官网访客",
            "text": "我想继续咨询",
            "page_url": "https://example.com/",
            "page_title": "餐饮行业 AI 转型专家",
            "reopen_action": "continue_chat",
        },
    )
    assert continue_res.status_code == 201
    continued = continue_res.json()
    assert continued["is_new_conversation"] is True
    assert continued["conversation_id"] != widget["conversation_id"]
    assert continued["conversation_status"] == "bot_visiting"

    continue_poll_res = client.get(
        "/api/public/website-widget/messages",
        params={
            "tenant_id": tenant["id"],
            "visitor_id": "visitor-public-001",
            "after_id": continued["message_id"],
        },
    )
    assert continue_poll_res.status_code == 200
    continue_poll = continue_poll_res.json()
    assert continue_poll["conversation_id"] == continued["conversation_id"]
    assert continue_poll["conversation_status"] == "bot_visiting"
    assert continue_poll["messages"][0]["sender_type"] == "agent"
    assert continue_poll["messages"][0]["content"] == "您好，已为您重新接入客服，请问还有什么可以帮您？"

    continue_close_res = client.post(
        f"/api/conversations/{continued['conversation_id']}/workflow-actions",
        headers=headers,
        json={"action": "close", "note": "继续咨询结束"},
    )
    assert continue_close_res.status_code == 200

    leave_message_res = client.post(
        "/api/public/website-widget/messages",
        json={
            "tenant_id": tenant["id"],
            "component_id": "website-widget",
            "visitor_id": "visitor-public-001",
            "visitor_name": "官网访客",
            "text": "请回电，我的电话是 13800000000",
            "page_url": "https://example.com/",
            "page_title": "餐饮行业 AI 转型专家",
            "reopen_action": "leave_message",
        },
    )
    assert leave_message_res.status_code == 201
    leave_message = leave_message_res.json()
    assert leave_message["is_new_conversation"] is True
    assert leave_message["conversation_id"] != continued["conversation_id"]


def test_website_widget_auto_replies_only_after_published_knowledge_and_model_ready(client, monkeypatch) -> None:
    tenant, token = _bootstrap_owner(
        client,
        slug="website-widget-ai-cycle",
        email="website-widget-ai-cycle@example.com",
    )
    headers = {"Authorization": f"Bearer {token}"}
    import_res = client.post(
        f"/api/tenants/{tenant['id']}/knowledge-imports",
        headers=headers,
        json={
            "source_file_ref": "template://website-ai-cycle",
            "rows": [
                {
                    "business_object": "餐饮门店 AI 客服接入",
                    "question": "餐饮门店怎么接入 AI 客服",
                    "answer": "餐饮门店可以先接入网站客服组件，再导入门店常见问题，负责人发布后启用 AI 接待。",
                    "trigger_keywords": ["餐饮门店", "AI客服", "接入", "网站客服"],
                    "channel_scope": "website",
                    "risk_level": "normal",
                    "status": "active",
                }
            ],
        },
    )
    assert import_res.status_code == 201
    import_batch = import_res.json()
    publish_res = client.post(
        f"/api/tenants/{tenant['id']}/knowledge-publications",
        headers=headers,
        json={"import_batch_id": import_batch["id"], "note": "发布网站 AI 自动回复资料"},
    )
    assert publish_res.status_code == 201

    monkeypatch.setenv("BAILIAN_API_KEY", "test-only-placeholder")

    def _fake_generate_reply_draft(request):
        return ModelDraftResult(
            provider="bailian",
            model="qwen-plus",
            status="succeeded",
            draft_text="餐饮门店可以先接入网站客服组件，再导入常见问题，负责人发布后启用 AI 接待。",
            prompt_summary="test",
            prompt_chars=120,
            completion_chars=40,
            total_chars=160,
        )

    monkeypatch.setattr("app.services.ai_reply_cycle.generate_reply_draft", _fake_generate_reply_draft)
    widget_res = client.post(
        "/api/public/website-widget/messages",
        json={
            "tenant_id": tenant["id"],
            "component_id": "website-widget",
            "visitor_id": "visitor-ai-cycle-001",
            "visitor_name": "官网访客",
            "text": "餐饮门店怎么接入 AI 客服？",
            "page_url": "https://example.com/",
            "page_title": "餐饮行业 AI 转型专家",
        },
    )

    assert widget_res.status_code == 201
    widget = widget_res.json()
    assert widget["conversation_status"] == "bot_visiting"
    poll_res = client.get(
        "/api/public/website-widget/messages",
        params={
            "tenant_id": tenant["id"],
            "visitor_id": "visitor-ai-cycle-001",
            "after_id": widget["message_id"],
        },
    )
    assert poll_res.status_code == 200
    messages = poll_res.json()["messages"]
    assert len(messages) == 1
    assert messages[0]["sender_type"] == "ai"
    assert "负责人发布" in messages[0]["content"]
    assert "启用 AI 接待" in messages[0]["content"]


def test_public_website_widget_script_is_hosted(client) -> None:
    res = client.get("/Web/js/customer-widget.js")

    assert res.status_code == 200
    assert "javascript" in res.headers["content-type"]
    assert "window._WANFA" in res.text
    assert "/api/public/website-widget/messages" in res.text


def test_channel_account_identity_config_is_readable_and_does_not_enable_external_write(client) -> None:
    tenant, token = _bootstrap_owner(client, slug="channel-account-demo", email="channel-account@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    channel, _ready = _ready_outbox_draft(client, tenant["id"], headers)
    connector = _create_connector(client, channel["id"], headers)

    account_res = client.post(
        f"/api/channels/{channel['id']}/channel-accounts",
        headers=headers,
        json={
            "connector_id": connector["id"],
            "provider": "wecom",
            "platform": "微信客服",
            "account_name": "万法常世AI客服测试",
            "external_account_id": "kf-demo-001",
            "store_name": "企业微信客服账号",
            "entrypoint_name": "微信客服链接",
            "authorization_status": "sandbox_configuring",
            "access_status": "callback_pending",
            "reply_mode": "human_review_first",
            "health_status": "configuring",
            "public_profile": {
                "visible_scope": "测试部门",
                "access_token": "should-not-be-stored",
            },
        },
    )

    assert account_res.status_code == 201
    account = account_res.json()
    assert account["tenant_id"] == tenant["id"]
    assert account["channel_id"] == channel["id"]
    assert account["connector_id"] == connector["id"]
    assert account["platform"] == "微信客服"
    assert account["account_name"] == "万法常世AI客服测试"
    assert account["store_name"] == "企业微信客服账号"
    assert account["entrypoint_name"] == "微信客服链接"
    assert account["authorization_status"] == "sandbox_configuring"
    assert account["access_status"] == "callback_pending"
    assert account["reply_mode"] == "human_review_first"
    assert account["public_profile"]["access_token"] == "[redacted]"
    assert "external_write_enabled" not in account

    list_res = client.get(f"/api/tenants/{tenant['id']}/channel-accounts", headers=headers)
    assert list_res.status_code == 200
    accounts = list_res.json()
    assert [item["id"] for item in accounts] == [account["id"]]
    assert accounts[0]["public_profile"]["access_token"] == "[redacted]"

    audit_res = client.get(f"/api/tenants/{tenant['id']}/audit-events", headers=headers)
    audit_events = audit_res.json()
    channel_account_events = [event for event in audit_events if event["action"] == "channel_account.configured"]
    assert channel_account_events
    assert "external_write_enabled" in channel_account_events[-1]["payload"]


def test_connector_send_plan_requires_configured_connector(client) -> None:
    tenant, token = _bootstrap_owner(client, slug="connector-missing", email="connector-missing@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    _, ready = _ready_outbox_draft(client, tenant["id"], headers)

    plan_res = client.post(
        f"/api/outbox-drafts/{ready['id']}/connector-send-plans",
        headers=headers,
        json={},
    )

    assert plan_res.status_code == 409
    assert "channel connector must be configured" in plan_res.json()["detail"]


def test_channel_delivery_receipt_placeholder_records_unmatched_event_without_claiming_verification(client) -> None:
    tenant, token = _bootstrap_owner(client, slug="connector-receipt", email="connector-receipt@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    channel, _ = _ready_outbox_draft(client, tenant["id"], headers)
    _create_connector(client, channel["id"], headers)

    receipt_res = client.post(
        f"/api/channels/{channel['id']}/delivery-receipts",
        headers=headers,
        json={
            "provider": "wecom",
            "external_message_id": "platform-message-001",
            "delivery_status": "delivered",
            "provider_event_id": "event-001",
            "raw_payload": {"MsgID": "platform-message-001", "Status": "delivered"},
            "signature_validated": False,
        },
    )

    assert receipt_res.status_code == 201
    receipt = receipt_res.json()
    assert receipt["tenant_id"] == tenant["id"]
    assert receipt["channel_id"] == channel["id"]
    assert receipt["provider"] == "wecom"
    assert receipt["external_message_id"] == "platform-message-001"
    assert receipt["delivery_status"] == "delivered"
    assert receipt["verification_status"] == "not_verified_placeholder"
    assert receipt["signature_validated"] is False
    assert receipt["matched_attempt_id"] is None
    assert receipt["raw_payload"]["Status"] == "delivered"

    list_res = client.get(f"/api/channels/{channel['id']}/delivery-receipts", headers=headers)
    assert list_res.status_code == 200
    assert [item["id"] for item in list_res.json()] == [receipt["id"]]

    audit_res = client.get(f"/api/tenants/{tenant['id']}/audit-events", headers=headers)
    actions = [event["action"] for event in audit_res.json()]
    assert "channel_delivery_receipt.placeholder_recorded" in actions


def test_online_receipt_quality_summary_is_bounded_and_does_not_claim_full_accuracy(client) -> None:
    tenant, token = _bootstrap_owner(client, slug="receipt-quality-demo", email="receipt-quality@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    channel, _ = _ready_outbox_draft(client, tenant["id"], headers)
    _create_connector(client, channel["id"], headers)

    delivered_res = client.post(
        f"/api/channels/{channel['id']}/delivery-receipts",
        headers=headers,
        json={
            "provider": "wecom",
            "external_message_id": "receipt-delivered-001",
            "delivery_status": "delivered",
            "provider_event_id": "event-delivered-001",
            "raw_payload": {"Status": "delivered", "secret": "must-not-appear-in-summary"},
        },
    )
    assert delivered_res.status_code == 201

    rate_limited_res = client.post(
        f"/api/channels/{channel['id']}/delivery-receipts",
        headers=headers,
        json={
            "provider": "wecom",
            "external_message_id": "receipt-rate-limited-001",
            "delivery_status": "rate_limited",
            "provider_event_id": "event-rate-limited-001",
            "raw_payload": {"errcode": "45009", "errmsg": "too many requests"},
        },
    )
    assert rate_limited_res.status_code == 201

    summary_res = client.get(
        f"/api/tenants/{tenant['id']}/online-receipt-quality-summary",
        headers=headers,
    )

    assert summary_res.status_code == 200
    summary = summary_res.json()
    assert summary["schema_version"] == "p3-06u-26h2w3d.online_receipt_quality.v1"
    assert summary["receipt_total"] == 2
    assert summary["delivered_or_read"] == 1
    assert summary["failed_or_review"] == 1
    assert summary["open_failure_reviews"] == 1
    assert summary["delivery_success_rate"] == 0.5
    assert summary["failure_review_rate"] == 0.5
    assert summary["raw_payload_included"] is False
    assert summary["customer_accuracy_completed"] is False
    assert summary["real_platform_receipts_required_for_full_accuracy"] is True
    assert summary["model_call_performed"] is False
    assert summary["external_call_performed"] is False
    assert summary["external_platform_write_performed"] is False
    assert summary["real_external_write_performed"] is False
    assert "完整客服答案准确率" in summary["accuracy_scope_label"]
    assert "真实外发继续关闭" in summary["accuracy_boundary"]
    assert "must-not-appear-in-summary" not in str(summary)

    gates = {item["key"]: item for item in summary["quality_gates"]}
    assert gates["receipt_ingestion"]["status"] == "ok"
    assert gates["attempt_match"]["status"] == "missing"
    assert gates["signature_verification"]["status"] == "missing"
    assert gates["customer_accuracy"]["status"] == "missing"
    assert "不展示完整线上准确率" in gates["customer_accuracy"]["stop_condition"]

    provider = summary["provider_breakdown"][0]
    assert provider["provider"] == "wecom"
    assert provider["receipt_count"] == 2
    assert provider["delivered_or_read"] == 1
    assert provider["needs_review"] == 1


def test_channel_connector_config_is_tenant_isolated(client) -> None:
    tenant, token = _bootstrap_owner(client, slug="connector-isolated-a", email="connector-a@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    channel, _ = _ready_outbox_draft(client, tenant["id"], headers)
    _create_connector(client, channel["id"], headers)

    _, other_token = _bootstrap_owner(client, slug="connector-isolated-b", email="connector-b@example.com")
    other_headers = {"Authorization": f"Bearer {other_token}"}

    get_res = client.get(f"/api/channels/{channel['id']}/connector-config", headers=other_headers)
    assert get_res.status_code == 404

    receipt_res = client.post(
        f"/api/channels/{channel['id']}/delivery-receipts",
        headers=other_headers,
        json={
            "provider": "wecom",
            "external_message_id": "cross-tenant-message",
            "delivery_status": "delivered",
        },
    )
    assert receipt_res.status_code == 404
from app.services.model_gateway import ModelDraftResult
