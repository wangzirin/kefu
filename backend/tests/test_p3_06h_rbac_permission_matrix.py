from app.core.rbac import allowed_roles_for_permission, permissions_for_roles


def _bootstrap_user_with_role(client, *, slug: str, role_code: str, email: str) -> tuple[dict, str]:
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
    return tenant, login_res.json()["access_token"]


def test_rbac_permission_matrix_maps_ops_permissions_to_owner_and_admin() -> None:
    assert allowed_roles_for_permission("ops.worker_health.read") == ("admin", "owner")
    assert allowed_roles_for_permission("ops.alert_rules.read") == ("admin", "owner")
    assert allowed_roles_for_permission("ops.metrics.read") == ("admin", "owner")
    assert "ops.metrics.read" in permissions_for_roles(["owner"])
    assert "ops.metrics.read" in permissions_for_roles(["admin"])
    assert "ops.metrics.read" not in permissions_for_roles(["agent"])
    assert "ops.metrics.read" not in permissions_for_roles(["viewer"])


def test_ops_metrics_permission_allows_admin_and_blocks_agent(client) -> None:
    admin_tenant, admin_token = _bootstrap_user_with_role(
        client,
        slug="rbac-ops-admin",
        role_code="admin",
        email="rbac-admin@example.com",
    )
    admin_res = client.get(
        f"/api/tenants/{admin_tenant['id']}/ops/metrics",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert admin_res.status_code == 200

    agent_tenant, agent_token = _bootstrap_user_with_role(
        client,
        slug="rbac-ops-agent",
        role_code="agent",
        email="rbac-agent@example.com",
    )
    agent_res = client.get(
        f"/api/tenants/{agent_tenant['id']}/ops/metrics",
        headers={"Authorization": f"Bearer {agent_token}"},
    )
    assert agent_res.status_code == 403
    assert agent_res.json()["detail"] == "insufficient permission"

    no_token_res = client.get(f"/api/tenants/{agent_tenant['id']}/ops/metrics")
    assert no_token_res.status_code == 401
