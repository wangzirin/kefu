from app.models import AuditEvent


def _create_tenant(client, name: str, slug: str) -> dict:
    res = client.post("/api/tenants", json={"name": name, "slug": slug})
    assert res.status_code == 201
    return res.json()


def _bootstrap_owner(client, tenant: dict, email: str = "owner@example.com") -> tuple[dict, dict, str]:
    role_res = client.post(
        f"/api/tenants/{tenant['id']}/roles",
        json={"code": "owner", "name": "管理员"},
    )
    assert role_res.status_code == 201
    role = role_res.json()

    user_res = client.post(
        f"/api/tenants/{tenant['id']}/users",
        json={
            "name": "王敏",
            "email": email,
            "password": "ChangeMe123!",
        },
    )
    assert user_res.status_code == 201
    user = user_res.json()

    assign_res = client.post(
        f"/api/users/{user['id']}/roles",
        json={"role_id": role["id"]},
    )
    assert assign_res.status_code == 201

    login_res = client.post(
        "/api/auth/login",
        json={
            "tenant_slug": tenant["slug"],
            "email": email,
            "password": "ChangeMe123!",
        },
    )
    assert login_res.status_code == 200
    return role, user, login_res.json()["access_token"]


def test_user_role_team_flow(client) -> None:
    tenant = _create_tenant(client, "演示客户", "accounts-demo")
    _owner_role, owner, token = _bootstrap_owner(client, tenant)
    headers = {"Authorization": f"Bearer {token}"}

    role_res = client.post(
        f"/api/tenants/{tenant['id']}/roles",
        json={"code": "agent", "name": "客服坐席"},
        headers=headers,
    )
    assert role_res.status_code == 201
    role = role_res.json()

    user_res = client.post(
        f"/api/tenants/{tenant['id']}/users",
        json={
            "name": "张明",
            "email": "agent@example.com",
            "password": "ChangeMe123!",
        },
        headers=headers,
    )
    assert user_res.status_code == 201
    user = user_res.json()
    assert user["email"] == "agent@example.com"
    assert "password" not in user
    assert "password_hash" not in user

    assign_res = client.post(
        f"/api/users/{user['id']}/roles",
        json={"role_id": role["id"]},
        headers=headers,
    )
    assert assign_res.status_code == 201
    assert assign_res.json()["role_id"] == role["id"]

    team_res = client.post(
        f"/api/tenants/{tenant['id']}/teams",
        json={"name": "售前接待组", "description": "负责官网和企业微信初次接待"},
        headers=headers,
    )
    assert team_res.status_code == 201
    team = team_res.json()

    member_res = client.post(
        f"/api/teams/{team['id']}/members",
        json={"user_id": user["id"], "role_in_team": "lead"},
        headers=headers,
    )
    assert member_res.status_code == 201
    assert member_res.json()["user_id"] == user["id"]

    users_res = client.get(f"/api/tenants/{tenant['id']}/users", headers=headers)
    roles_res = client.get(f"/api/tenants/{tenant['id']}/roles", headers=headers)
    teams_res = client.get(f"/api/tenants/{tenant['id']}/teams", headers=headers)

    assert users_res.status_code == 200
    assert roles_res.status_code == 200
    assert teams_res.status_code == 200
    assert [item["name"] for item in users_res.json()] == [owner["name"], "张明"]
    assert [item["code"] for item in roles_res.json()] == ["owner", "agent"]
    assert teams_res.json()[0]["name"] == "售前接待组"


def test_duplicate_user_email_is_rejected_inside_tenant(client) -> None:
    tenant = _create_tenant(client, "演示客户", "duplicate-email-demo")
    _owner_role, _owner, token = _bootstrap_owner(client, tenant)
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "name": "张明",
        "email": "agent@example.com",
        "password": "ChangeMe123!",
    }

    first_res = client.post(f"/api/tenants/{tenant['id']}/users", json=payload, headers=headers)
    second_res = client.post(f"/api/tenants/{tenant['id']}/users", json=payload, headers=headers)

    assert first_res.status_code == 201
    assert second_res.status_code == 409


def test_role_and_team_reject_cross_tenant_assignment(client) -> None:
    first = _create_tenant(client, "客户A", "account-a")
    second = _create_tenant(client, "客户B", "account-b")
    _first_role, _first_user, first_token = _bootstrap_owner(client, first, "first@example.com")
    _second_role, user, second_token = _bootstrap_owner(client, second, "second@example.com")
    first_headers = {"Authorization": f"Bearer {first_token}"}
    second_headers = {"Authorization": f"Bearer {second_token}"}

    role = client.post(
        f"/api/tenants/{first['id']}/roles",
        json={"code": "auditor", "name": "审计员"},
        headers=first_headers,
    ).json()
    team = client.post(
        f"/api/tenants/{first['id']}/teams",
        json={"name": "客户A 接待组"},
        headers=first_headers,
    ).json()

    role_res = client.post(
        f"/api/users/{user['id']}/roles",
        json={"role_id": role["id"]},
        headers=second_headers,
    )
    team_res = client.post(
        f"/api/teams/{team['id']}/members",
        json={"user_id": user["id"]},
        headers=first_headers,
    )

    assert role_res.status_code == 404
    assert team_res.status_code == 404


def test_team_management_requires_owner_or_admin_after_bootstrap(client) -> None:
    tenant = _create_tenant(client, "权限客户", "team-permission-demo")
    _owner_role, _owner, owner_token = _bootstrap_owner(client, tenant)
    owner_headers = {"Authorization": f"Bearer {owner_token}"}

    agent_role = client.post(
        f"/api/tenants/{tenant['id']}/roles",
        json={"code": "agent", "name": "客服坐席"},
        headers=owner_headers,
    ).json()
    agent = client.post(
        f"/api/tenants/{tenant['id']}/users",
        json={
            "name": "普通坐席",
            "email": "agent@example.com",
            "password": "ChangeMe123!",
        },
        headers=owner_headers,
    ).json()
    client.post(
        f"/api/users/{agent['id']}/roles",
        json={"role_id": agent_role["id"]},
        headers=owner_headers,
    )
    agent_login = client.post(
        "/api/auth/login",
        json={
            "tenant_slug": tenant["slug"],
            "email": "agent@example.com",
            "password": "ChangeMe123!",
        },
    )
    agent_headers = {"Authorization": f"Bearer {agent_login.json()['access_token']}"}

    no_token_res = client.post(
        f"/api/tenants/{tenant['id']}/teams",
        json={"name": "未授权团队"},
    )
    agent_res = client.post(
        f"/api/tenants/{tenant['id']}/teams",
        json={"name": "坐席团队"},
        headers=agent_headers,
    )
    owner_res = client.post(
        f"/api/tenants/{tenant['id']}/teams",
        json={"name": "管理员团队"},
        headers=owner_headers,
    )

    assert no_token_res.status_code == 403
    assert agent_res.status_code == 403
    assert owner_res.status_code == 201


def test_owner_can_manage_local_user_lifecycle_without_leaking_password(client, db_session) -> None:
    tenant = _create_tenant(client, "本地客户", "local-account-lifecycle")
    _owner_role, _owner, token = _bootstrap_owner(client, tenant)
    headers = {"Authorization": f"Bearer {token}"}

    agent_role = client.post(
        f"/api/tenants/{tenant['id']}/roles",
        json={"code": "agent", "name": "客服坐席"},
        headers=headers,
    ).json()
    user_res = client.post(
        f"/api/tenants/{tenant['id']}/users",
        json={"name": "一线客服", "email": "agent@example.com", "password": "ChangeMe123!"},
        headers=headers,
    )
    assert user_res.status_code == 201
    user = user_res.json()
    assert user["roles"] == []
    assert "password" not in user
    assert "password_hash" not in user

    assign_res = client.post(
        f"/api/users/{user['id']}/roles",
        json={"role_id": agent_role["id"]},
        headers=headers,
    )
    assert assign_res.status_code == 201

    users_res = client.get(f"/api/tenants/{tenant['id']}/users", headers=headers)
    assert users_res.status_code == 200
    users = users_res.json()
    agent_row = next(item for item in users if item["email"] == "agent@example.com")
    assert agent_row["roles"] == ["agent"]

    reset_res = client.post(
        f"/api/users/{user['id']}/password-reset",
        json={"new_password": "NewChangeMe123!"},
        headers=headers,
    )
    assert reset_res.status_code == 200
    reset_body = reset_res.json()
    assert reset_body["email"] == "agent@example.com"
    assert "new_password" not in reset_body
    assert "password_hash" not in reset_body

    old_login = client.post(
        "/api/auth/login",
        json={"tenant_slug": tenant["slug"], "email": "agent@example.com", "password": "ChangeMe123!"},
    )
    new_login = client.post(
        "/api/auth/login",
        json={"tenant_slug": tenant["slug"], "email": "agent@example.com", "password": "NewChangeMe123!"},
    )
    assert old_login.status_code == 401
    assert new_login.status_code == 200

    disable_res = client.patch(
        f"/api/users/{user['id']}/status",
        json={"status": "inactive"},
        headers=headers,
    )
    assert disable_res.status_code == 200
    assert disable_res.json()["status"] == "inactive"

    disabled_login = client.post(
        "/api/auth/login",
        json={"tenant_slug": tenant["slug"], "email": "agent@example.com", "password": "NewChangeMe123!"},
    )
    assert disabled_login.status_code == 401

    actions = [event.action for event in db_session.query(AuditEvent).all()]
    assert "user.password_reset" in actions
    assert "user.status_changed" in actions


def test_last_active_owner_cannot_be_disabled(client) -> None:
    tenant = _create_tenant(client, "本地客户", "last-owner-protection")
    _owner_role, owner, token = _bootstrap_owner(client, tenant)
    headers = {"Authorization": f"Bearer {token}"}

    res = client.patch(
        f"/api/users/{owner['id']}/status",
        json={"status": "inactive"},
        headers=headers,
    )
    assert res.status_code == 409
    assert res.json()["detail"] == "cannot disable the last active owner"


def test_agent_cannot_manage_local_accounts(client) -> None:
    tenant = _create_tenant(client, "本地客户", "agent-account-blocked")
    _owner_role, _owner, owner_token = _bootstrap_owner(client, tenant)
    owner_headers = {"Authorization": f"Bearer {owner_token}"}
    agent_role = client.post(
        f"/api/tenants/{tenant['id']}/roles",
        json={"code": "agent", "name": "客服坐席"},
        headers=owner_headers,
    ).json()
    agent = client.post(
        f"/api/tenants/{tenant['id']}/users",
        json={"name": "一线客服", "email": "agent@example.com", "password": "ChangeMe123!"},
        headers=owner_headers,
    ).json()
    client.post(f"/api/users/{agent['id']}/roles", json={"role_id": agent_role["id"]}, headers=owner_headers)
    login = client.post(
        "/api/auth/login",
        json={"tenant_slug": tenant["slug"], "email": "agent@example.com", "password": "ChangeMe123!"},
    )
    agent_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    reset_res = client.post(
        f"/api/users/{agent['id']}/password-reset",
        json={"new_password": "NewChangeMe123!"},
        headers=agent_headers,
    )
    status_res = client.patch(
        f"/api/users/{agent['id']}/status",
        json={"status": "inactive"},
        headers=agent_headers,
    )
    assert reset_res.status_code == 403
    assert status_res.status_code == 403


def test_current_user_profile_settings_and_password_are_real_persisted_actions(client) -> None:
    tenant = _create_tenant(client, "自助账号客户", "self-account-demo")
    _owner_role, _owner, token = _bootstrap_owner(client, tenant, "self-owner@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    profile_res = client.patch(
        "/api/auth/me/profile",
        json={
            "name": "王敏客服",
            "avatar_data_url": "data:image/png;base64,AA==",
            "public_profile": {
                "display_name": "小王",
                "signature": "欢迎咨询",
                "mobile": "13800000000",
                "phone": "020-100000",
                "qq": "10001",
                "wechat": "service-wang",
            },
        },
        headers=headers,
    )
    assert profile_res.status_code == 200
    profile = profile_res.json()
    assert profile["name"] == "王敏客服"
    assert profile["avatar_data_url"].startswith("data:image/png")
    assert profile["public_profile"]["display_name"] == "小王"

    settings_res = client.patch(
        "/api/auth/me/settings",
        json={
            "personal_settings": {
                "system_language": "en",
                "quick_reply_collapsed": True,
                "quick_reply_double_click_action": "send",
                "quick_reply_quote_mode": "append",
                "show_typing_status": False,
                "default_translate_language": "ja",
                "message_notifications_enabled": False,
                "auto_reply_enabled": True,
                "shortcut_send_key": "ctrl_enter",
                "service_notifications_enabled": False,
            }
        },
        headers=headers,
    )
    assert settings_res.status_code == 200
    settings = settings_res.json()["personal_settings"]
    assert settings["system_language"] == "en"
    assert settings["quick_reply_collapsed"] is True
    assert settings["quick_reply_double_click_action"] == "send"
    assert settings["default_translate_language"] == "ja"

    me_res = client.get("/api/auth/me", headers=headers)
    assert me_res.status_code == 200
    me = me_res.json()
    assert me["public_profile"]["wechat"] == "service-wang"
    assert me["personal_settings"]["shortcut_send_key"] == "ctrl_enter"

    wrong_password_res = client.post(
        "/api/auth/me/password",
        json={"current_password": "WrongPassword!", "new_password": "SelfNewPass123!"},
        headers=headers,
    )
    assert wrong_password_res.status_code == 403

    password_res = client.post(
        "/api/auth/me/password",
        json={"current_password": "ChangeMe123!", "new_password": "SelfNewPass123!"},
        headers=headers,
    )
    assert password_res.status_code == 200

    old_login = client.post(
        "/api/auth/login",
        json={"tenant_slug": tenant["slug"], "email": "self-owner@example.com", "password": "ChangeMe123!"},
    )
    new_login = client.post(
        "/api/auth/login",
        json={"tenant_slug": tenant["slug"], "email": "self-owner@example.com", "password": "SelfNewPass123!"},
    )
    assert old_login.status_code == 401
    assert new_login.status_code == 200
