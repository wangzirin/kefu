def _create_tenant(client, *, slug: str) -> dict:
    res = client.post("/api/tenants", json={"name": f"{slug} 客户", "slug": slug})
    assert res.status_code == 201
    return res.json()


def _bootstrap_owner(client, tenant: dict, *, email: str = "owner@example.com") -> str:
    role_res = client.post(
        f"/api/tenants/{tenant['id']}/roles",
        json={"code": "owner", "name": "owner"},
    )
    assert role_res.status_code == 201
    role = role_res.json()

    user_res = client.post(
        f"/api/tenants/{tenant['id']}/users",
        json={"name": "owner", "email": email, "password": "ChangeMe123!"},
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
    return login_res.json()["access_token"]


def _create_user_with_role(
    client,
    *,
    tenant: dict,
    role_code: str,
    email: str,
    owner_token: str,
) -> str:
    owner_headers = {"Authorization": f"Bearer {owner_token}"}
    role_res = client.post(
        f"/api/tenants/{tenant['id']}/roles",
        json={"code": role_code, "name": role_code},
        headers=owner_headers,
    )
    assert role_res.status_code == 201
    role = role_res.json()

    user_res = client.post(
        f"/api/tenants/{tenant['id']}/users",
        json={"name": role_code, "email": email, "password": "ChangeMe123!"},
        headers=owner_headers,
    )
    assert user_res.status_code == 201
    user = user_res.json()

    assign_res = client.post(
        f"/api/users/{user['id']}/roles",
        json={"role_id": role["id"]},
        headers=owner_headers,
    )
    assert assign_res.status_code == 201

    login_res = client.post(
        "/api/auth/login",
        json={"tenant_slug": tenant["slug"], "email": email, "password": "ChangeMe123!"},
    )
    assert login_res.status_code == 200
    return login_res.json()["access_token"]


def test_production_mode_blocks_dev_bootstrap_and_foundation_without_token(client, monkeypatch) -> None:
    tenant = _create_tenant(client, slug="p3-06r-prod-guard")

    monkeypatch.setenv("STANDARD_OPS_ENV", "pilot")
    monkeypatch.setenv("STANDARD_OPS_DEV_BOOTSTRAP_ENABLED", "false")

    me_res = client.get("/api/auth/me")
    create_tenant_res = client.post("/api/tenants", json={"name": "blocked", "slug": "blocked"})
    list_tenants_res = client.get("/api/tenants")
    create_channel_res = client.post(
        f"/api/tenants/{tenant['id']}/channels",
        json={"type": "web", "name": "blocked channel"},
    )
    list_channels_res = client.get(f"/api/tenants/{tenant['id']}/channels")
    create_contact_res = client.post(
        f"/api/tenants/{tenant['id']}/contacts",
        json={"display_name": "blocked contact"},
    )
    list_contacts_res = client.get(f"/api/tenants/{tenant['id']}/contacts")

    assert me_res.status_code == 401
    assert create_tenant_res.status_code == 401
    assert list_tenants_res.status_code == 401
    assert create_channel_res.status_code == 401
    assert list_channels_res.status_code == 401
    assert create_contact_res.status_code == 401
    assert list_contacts_res.status_code == 401


def test_foundation_permissions_match_owner_agent_viewer_boundaries(client) -> None:
    tenant = _create_tenant(client, slug="p3-06r-foundation-rbac")
    owner_token = _bootstrap_owner(client, tenant)
    agent_token = _create_user_with_role(
        client,
        tenant=tenant,
        role_code="agent",
        email="agent@example.com",
        owner_token=owner_token,
    )
    viewer_token = _create_user_with_role(
        client,
        tenant=tenant,
        role_code="viewer",
        email="viewer@example.com",
        owner_token=owner_token,
    )
    owner_headers = {"Authorization": f"Bearer {owner_token}"}
    agent_headers = {"Authorization": f"Bearer {agent_token}"}
    viewer_headers = {"Authorization": f"Bearer {viewer_token}"}

    owner_channel_res = client.post(
        f"/api/tenants/{tenant['id']}/channels",
        json={"type": "web", "name": "官网客服", "reply_mode": "assist", "status": "active"},
        headers=owner_headers,
    )
    assert owner_channel_res.status_code == 201

    agent_channel_res = client.post(
        f"/api/tenants/{tenant['id']}/channels",
        json={"type": "web", "name": "agent should not create channel"},
        headers=agent_headers,
    )
    assert agent_channel_res.status_code == 403

    agent_contact_res = client.post(
        f"/api/tenants/{tenant['id']}/contacts",
        json={"display_name": "坐席创建联系人"},
        headers=agent_headers,
    )
    assert agent_contact_res.status_code == 201

    viewer_channel_list_res = client.get(f"/api/tenants/{tenant['id']}/channels", headers=viewer_headers)
    viewer_contact_create_res = client.post(
        f"/api/tenants/{tenant['id']}/contacts",
        json={"display_name": "viewer should not create contact"},
        headers=viewer_headers,
    )
    viewer_contact_list_res = client.get(f"/api/tenants/{tenant['id']}/contacts", headers=viewer_headers)

    assert viewer_channel_list_res.status_code == 200
    assert viewer_contact_create_res.status_code == 403
    assert viewer_contact_list_res.status_code == 403


def test_workflow_worker_and_reply_use_named_permissions(client) -> None:
    tenant = _create_tenant(client, slug="p3-06r-workflow-rbac")
    owner_token = _bootstrap_owner(client, tenant)
    agent_token = _create_user_with_role(
        client,
        tenant=tenant,
        role_code="agent",
        email="workflow-agent@example.com",
        owner_token=owner_token,
    )
    viewer_token = _create_user_with_role(
        client,
        tenant=tenant,
        role_code="viewer",
        email="workflow-viewer@example.com",
        owner_token=owner_token,
    )
    owner_headers = {"Authorization": f"Bearer {owner_token}"}
    agent_headers = {"Authorization": f"Bearer {agent_token}"}
    viewer_headers = {"Authorization": f"Bearer {viewer_token}"}

    channel = client.post(
        f"/api/tenants/{tenant['id']}/channels",
        json={"type": "web", "name": "官网客服", "reply_mode": "assist", "status": "active"},
        headers=owner_headers,
    ).json()
    contact = client.post(
        f"/api/tenants/{tenant['id']}/contacts",
        json={"display_name": "测试访客"},
        headers=agent_headers,
    ).json()
    conversation = client.post(
        f"/api/tenants/{tenant['id']}/conversations",
        headers=agent_headers,
        json={"channel_id": channel["id"], "contact_id": contact["id"], "subject": "售后政策咨询"},
    ).json()
    message = client.post(
        f"/api/conversations/{conversation['id']}/messages",
        headers=agent_headers,
        json={"direction": "inbound", "sender_type": "visitor", "content": "超过七天还能退吗？"},
    ).json()

    viewer_inbox_res = client.get(f"/api/tenants/{tenant['id']}/human-review-inbox", headers=viewer_headers)
    agent_reply_res = client.post(
        f"/api/messages/{message['id']}/reply-orchestrations",
        headers=agent_headers,
        json={
            "intent": "after_sales_policy",
            "retrieved_knowledge_count": 1,
            "draft_reply": "超过七天需要结合订单政策和商品状态确认。",
            "confidence": 0.8,
            "risk_level": "low",
        },
    )
    agent_worker_res = client.post(
        f"/api/tenants/{tenant['id']}/trusted-inbound-worker-runs",
        headers=agent_headers,
        json={"batch_size": 1, "model_provider": "deterministic"},
    )
    owner_worker_res = client.post(
        f"/api/tenants/{tenant['id']}/trusted-inbound-worker-runs",
        headers=owner_headers,
        json={"batch_size": 1, "model_provider": "deterministic"},
    )

    assert viewer_inbox_res.status_code == 403
    assert agent_reply_res.status_code == 201
    assert agent_worker_res.status_code == 403
    assert owner_worker_res.status_code == 201
