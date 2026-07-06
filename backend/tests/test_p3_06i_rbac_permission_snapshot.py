def _bootstrap_user_with_role(client, *, slug: str, role_code: str, email: str) -> tuple[dict, str, dict]:
    tenant_res = client.post("/api/tenants", json={"name": f"{slug} 客户", "slug": slug})
    assert tenant_res.status_code == 201
    tenant = tenant_res.json()

    role_res = client.post(
        f"/api/tenants/{tenant['id']}/roles",
        json={"code": role_code, "name": role_code},
    )
    assert role_res.status_code == 201
    role = role_res.json()

    user_res = client.post(
        f"/api/tenants/{tenant['id']}/users",
        json={"name": role_code, "email": email, "password": "ChangeMe123!"},
    )
    assert user_res.status_code == 201

    assign_res = client.post(f"/api/users/{user_res.json()['id']}/roles", json={"role_id": role["id"]})
    assert assign_res.status_code == 201

    login_res = client.post(
        "/api/auth/login",
        json={"tenant_slug": slug, "email": email, "password": "ChangeMe123!"},
    )
    assert login_res.status_code == 200
    login = login_res.json()
    return tenant, login["access_token"], login


def test_login_and_me_return_permission_snapshot_for_owner(client) -> None:
    _tenant, token, login = _bootstrap_user_with_role(
        client,
        slug="rbac-snapshot-owner",
        role_code="owner",
        email="snapshot-owner@example.com",
    )

    login_permissions = set(login["user"]["permissions"])
    assert "accounts.manage" in login_permissions
    assert "audit.events.read" in login_permissions
    assert "ops.metrics.read" in login_permissions
    assert "conversation.manage" in login_permissions

    me_res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    me = me_res.json()
    assert me["roles"] == ["owner"]
    assert set(me["permissions"]) == login_permissions


def test_audit_events_use_named_permission_for_admin_and_agent(client) -> None:
    admin_tenant, admin_token, admin_login = _bootstrap_user_with_role(
        client,
        slug="rbac-audit-admin",
        role_code="admin",
        email="snapshot-admin@example.com",
    )
    assert "audit.events.read" in set(admin_login["user"]["permissions"])

    admin_res = client.get(
        f"/api/tenants/{admin_tenant['id']}/audit-events",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert admin_res.status_code == 200

    agent_tenant, agent_token, agent_login = _bootstrap_user_with_role(
        client,
        slug="rbac-audit-agent",
        role_code="agent",
        email="snapshot-agent@example.com",
    )
    agent_permissions = set(agent_login["user"]["permissions"])
    assert "conversation.manage" in agent_permissions
    assert "audit.events.read" not in agent_permissions
    assert "ops.metrics.read" not in agent_permissions

    agent_res = client.get(
        f"/api/tenants/{agent_tenant['id']}/audit-events",
        headers={"Authorization": f"Bearer {agent_token}"},
    )
    assert agent_res.status_code == 403
    assert agent_res.json()["detail"] == "insufficient permission"
