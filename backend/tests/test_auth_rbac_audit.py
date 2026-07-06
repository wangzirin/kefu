from app.models import AuditEvent, AuthSession


def _tenant(client) -> dict:
    res = client.post("/api/tenants", json={"name": "安全演示客户", "slug": "secure-demo"})
    assert res.status_code == 201
    return res.json()


def _role(client, tenant_id: int, code: str, name: str) -> dict:
    res = client.post(
        f"/api/tenants/{tenant_id}/roles",
        json={"code": code, "name": name},
    )
    assert res.status_code == 201
    return res.json()


def _user(client, tenant_id: int, name: str, email: str) -> dict:
    res = client.post(
        f"/api/tenants/{tenant_id}/users",
        json={"name": name, "email": email, "password": "ChangeMe123!"},
    )
    assert res.status_code == 201
    return res.json()


def _assign(client, user_id: int, role_id: int) -> None:
    res = client.post(f"/api/users/{user_id}/roles", json={"role_id": role_id})
    assert res.status_code == 201


def test_login_me_and_owner_audit_flow(client, db_session) -> None:
    tenant = _tenant(client)
    owner_role = _role(client, tenant["id"], "owner", "管理员")
    owner = _user(client, tenant["id"], "王敏", "owner@example.com")
    _assign(client, owner["id"], owner_role["id"])

    login_res = client.post(
        "/api/auth/login",
        json={
            "tenant_slug": tenant["slug"],
            "email": "OWNER@example.com",
            "password": "ChangeMe123!",
        },
    )
    assert login_res.status_code == 200
    login = login_res.json()
    token = login["access_token"]
    assert login["token_type"] == "bearer"
    assert login["user"]["name"] == "王敏"
    assert login["user"]["roles"] == ["owner"]

    session = db_session.query(AuthSession).one()
    assert session.token_hash != token
    assert token not in session.token_hash

    me_res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    assert me_res.json()["email"] == "owner@example.com"

    audit_res = client.get(
        f"/api/tenants/{tenant['id']}/audit-events",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert audit_res.status_code == 200
    actions = [event["action"] for event in audit_res.json()]
    assert "auth.login" in actions
    assert "user.created" in actions


def test_login_rejects_wrong_password(client) -> None:
    tenant = _tenant(client)
    _user(client, tenant["id"], "王敏", "owner@example.com")

    res = client.post(
        "/api/auth/login",
        json={
            "tenant_slug": tenant["slug"],
            "email": "owner@example.com",
            "password": "WrongPassword123!",
        },
    )
    assert res.status_code == 401


def test_login_rate_limits_repeated_wrong_password_and_audits_failures(client, db_session) -> None:
    tenant = _tenant(client)
    _user(client, tenant["id"], "王敏", "rate-limit-owner@example.com")

    payload = {
        "tenant_slug": tenant["slug"],
        "email": "rate-limit-owner@example.com",
        "password": "WrongPassword123!",
    }
    statuses = [client.post("/api/auth/login", json=payload).status_code for _ in range(5)]
    assert statuses == [401, 401, 401, 401, 429]

    blocked = client.post("/api/auth/login", json={**payload, "password": "ChangeMe123!"})
    assert blocked.status_code == 429

    events = db_session.query(AuditEvent).filter(AuditEvent.action == "auth.login_failed").all()
    assert len(events) >= 5
    serialized = "\n".join(event.payload for event in events)
    assert "rate-limit-owner@example.com" not in serialized
    assert "WrongPassword123" not in serialized
    assert "rate_limited" in serialized


def test_dev_local_login_returns_real_local_workspace_token(client, db_session, monkeypatch) -> None:
    monkeypatch.setenv("STANDARD_OPS_ENV", "development")
    monkeypatch.setenv("STANDARD_OPS_DEV_BOOTSTRAP_ENABLED", "true")
    tenant_res = client.post("/api/tenants", json={"name": "本地开发客户空间", "slug": "wanfa-local-dev"})
    assert tenant_res.status_code == 201
    tenant = tenant_res.json()
    owner_role = _role(client, tenant["id"], "owner", "空间负责人")
    owner = _user(client, tenant["id"], "本地真实测试负责人", "real-test@wanfa.local")
    _assign(client, owner["id"], owner_role["id"])

    res = client.post("/api/auth/dev-local-login")
    assert res.status_code == 200
    body = res.json()
    assert body["token_type"] == "bearer"
    assert body["user"]["tenant"]["slug"] == "wanfa-local-dev"
    assert body["user"]["email"] == "real-test@wanfa.local"
    assert body["user"]["roles"] == ["owner"]

    session = db_session.query(AuthSession).one()
    assert session.token_hash != body["access_token"]


def test_dev_local_login_is_disabled_outside_development(client, monkeypatch) -> None:
    monkeypatch.setenv("STANDARD_OPS_ENV", "production")
    monkeypatch.setenv("STANDARD_OPS_DEV_BOOTSTRAP_ENABLED", "false")

    res = client.post("/api/auth/dev-local-login")
    assert res.status_code == 403


def test_current_user_requires_real_token_in_customer_mode_even_if_dev_flag_is_misconfigured(client, monkeypatch) -> None:
    monkeypatch.setenv("STANDARD_OPS_ENV", "pilot")
    monkeypatch.setenv("STANDARD_OPS_DEV_BOOTSTRAP_ENABLED", "true")

    res = client.get("/api/auth/me")

    assert res.status_code == 401


def test_audit_events_require_token_and_privileged_role(client) -> None:
    tenant = _tenant(client)
    agent_role = _role(client, tenant["id"], "agent", "客服坐席")
    agent = _user(client, tenant["id"], "李华", "agent@example.com")
    _assign(client, agent["id"], agent_role["id"])

    no_token = client.get(f"/api/tenants/{tenant['id']}/audit-events")
    assert no_token.status_code == 401

    login_res = client.post(
        "/api/auth/login",
        json={
            "tenant_slug": tenant["slug"],
            "email": "agent@example.com",
            "password": "ChangeMe123!",
        },
    )
    token = login_res.json()["access_token"]
    agent_res = client.get(
        f"/api/tenants/{tenant['id']}/audit-events",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert agent_res.status_code == 403
