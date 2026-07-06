from app.core.rbac import allowed_roles_for_permission, permissions_for_roles


def _create_tenant(client, *, slug: str) -> dict:
    res = client.post("/api/tenants", json={"name": f"{slug} 客户", "slug": slug})
    assert res.status_code == 201
    return res.json()


def _bootstrap_owner(client, tenant: dict) -> tuple[dict, dict, str]:
    role_res = client.post(
        f"/api/tenants/{tenant['id']}/roles",
        json={"code": "owner", "name": "owner"},
    )
    assert role_res.status_code == 201
    role = role_res.json()

    user_res = client.post(
        f"/api/tenants/{tenant['id']}/users",
        json={"name": "owner", "email": "owner@example.com", "password": "ChangeMe123!"},
    )
    assert user_res.status_code == 201
    user = user_res.json()

    assign_res = client.post(f"/api/users/{user['id']}/roles", json={"role_id": role["id"]})
    assert assign_res.status_code == 201

    login_res = client.post(
        "/api/auth/login",
        json={"tenant_slug": tenant["slug"], "email": "owner@example.com", "password": "ChangeMe123!"},
    )
    assert login_res.status_code == 200
    return role, user, login_res.json()["access_token"]


def _create_user_with_role(
    client,
    *,
    tenant: dict,
    role_code: str,
    email: str,
    owner_token: str,
) -> tuple[dict, str]:
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
    return user, login_res.json()["access_token"]


def test_accounts_manage_permission_is_owner_only() -> None:
    assert allowed_roles_for_permission("accounts.manage") == ("owner",)
    assert "accounts.manage" in permissions_for_roles(["owner"])
    assert "accounts.manage" not in permissions_for_roles(["admin"])
    assert "accounts.manage" not in permissions_for_roles(["agent"])
    assert "accounts.manage" not in permissions_for_roles(["viewer"])


def test_accounts_bootstrap_allows_first_role_user_and_assignment_without_token(client) -> None:
    tenant = _create_tenant(client, slug="rbac-accounts-bootstrap")
    owner_role, owner_user, owner_token = _bootstrap_owner(client, tenant)

    assert owner_role["code"] == "owner"
    assert owner_user["email"] == "owner@example.com"
    assert owner_token


def test_accounts_manage_permission_blocks_no_token_and_admin_after_bootstrap(client) -> None:
    tenant = _create_tenant(client, slug="rbac-accounts-blocks")
    _owner_role, _owner, owner_token = _bootstrap_owner(client, tenant)
    _admin, admin_token = _create_user_with_role(
        client,
        tenant=tenant,
        role_code="admin",
        email="admin@example.com",
        owner_token=owner_token,
    )

    no_token_res = client.post(
        f"/api/tenants/{tenant['id']}/roles",
        json={"code": "agent", "name": "agent"},
    )
    assert no_token_res.status_code == 403
    assert no_token_res.json()["detail"] == "insufficient permission"

    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    admin_users_res = client.get(f"/api/tenants/{tenant['id']}/users", headers=admin_headers)
    admin_team_res = client.post(
        f"/api/tenants/{tenant['id']}/teams",
        json={"name": "admin should not create team"},
        headers=admin_headers,
    )
    assert admin_users_res.status_code == 403
    assert admin_users_res.json()["detail"] == "insufficient permission"
    assert admin_team_res.status_code == 403
    assert admin_team_res.json()["detail"] == "insufficient permission"


def test_accounts_manage_permission_allows_owner_to_manage_team_members(client) -> None:
    tenant = _create_tenant(client, slug="rbac-accounts-owner")
    _owner_role, _owner, owner_token = _bootstrap_owner(client, tenant)
    owner_headers = {"Authorization": f"Bearer {owner_token}"}
    agent, _agent_token = _create_user_with_role(
        client,
        tenant=tenant,
        role_code="agent",
        email="agent@example.com",
        owner_token=owner_token,
    )

    team_res = client.post(
        f"/api/tenants/{tenant['id']}/teams",
        json={"name": "售前接待组"},
        headers=owner_headers,
    )
    assert team_res.status_code == 201
    team = team_res.json()

    member_res = client.post(
        f"/api/teams/{team['id']}/members",
        json={"user_id": agent["id"], "role_in_team": "member"},
        headers=owner_headers,
    )
    assert member_res.status_code == 201
    assert member_res.json()["user_id"] == agent["id"]
