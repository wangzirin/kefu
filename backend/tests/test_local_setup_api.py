from app.models import AuthSession, Role, Tenant, User, UserRole


def _force_local_delivery_env(monkeypatch) -> None:
    monkeypatch.setenv("STANDARD_OPS_ENV", "pilot")
    monkeypatch.setenv("STANDARD_OPS_DEV_BOOTSTRAP_ENABLED", "false")
    monkeypatch.setenv("OUTBOX_EXTERNAL_WRITE_ENABLED", "false")
    monkeypatch.setenv("TRUSTED_INBOUND_WORKER_ENABLED", "false")


def test_local_setup_status_starts_uninitialized(client, monkeypatch) -> None:
    _force_local_delivery_env(monkeypatch)

    res = client.get("/api/auth/local-setup/status")
    assert res.status_code == 200
    body = res.json()
    assert body == {
        "schema_version": "p3-06u-26h2w8a.local_setup_status.v1",
        "initialized": False,
        "tenant_count": 0,
        "user_count": 0,
        "can_create_first_owner": True,
        "setup_mode": "create_first_owner",
        "first_owner_creation_locked": False,
        "web_password_reset_enabled": False,
        "env": "pilot",
        "dev_bootstrap_enabled": False,
        "external_write_enabled": False,
        "trusted_inbound_worker_enabled": False,
        "local_deployment_ready": True,
        "readiness_checks": [
            "first_owner_creation_open",
            "web_password_reset_disabled",
            "no_default_password",
            "external_write_disabled",
            "dev_bootstrap_disabled",
            "trusted_inbound_worker_disabled",
        ],
        "blockers": [],
        "first_tenant_slug": None,
        "first_tenant_name": None,
    }


def test_create_local_owner_bootstraps_tenant_roles_user_and_session(client, db_session, monkeypatch) -> None:
    _force_local_delivery_env(monkeypatch)

    res = client.post(
        "/api/auth/local-setup/owner",
        json={
            "tenant_name": "本地客服工作台",
            "tenant_slug": "wanfa-local",
            "owner_name": "本地负责人",
            "email": "owner@wanfa.local",
            "password": "ChangeMe123!",
        },
    )
    assert res.status_code == 201
    body = res.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"].startswith("wanfa_session_")
    assert body["user"]["tenant"]["slug"] == "wanfa-local"
    assert body["user"]["name"] == "本地负责人"
    assert body["user"]["roles"] == ["owner"]
    assert "knowledge.manage" in body["user"]["permissions"]

    assert db_session.query(Tenant).count() == 1
    assert db_session.query(User).count() == 1
    assert db_session.query(AuthSession).count() == 1
    assert db_session.query(UserRole).count() == 1
    assert {role.code for role in db_session.query(Role).all()} == {"owner", "admin", "agent", "viewer"}

    status_res = client.get("/api/auth/local-setup/status")
    assert status_res.status_code == 200
    status_body = status_res.json()
    assert status_body["initialized"] is True
    assert status_body["can_create_first_owner"] is False
    assert status_body["setup_mode"] == "login_only"
    assert status_body["first_owner_creation_locked"] is True
    assert status_body["web_password_reset_enabled"] is False
    assert status_body["local_deployment_ready"] is True
    assert status_body["blockers"] == []
    assert status_body["first_tenant_slug"] == "wanfa-local"
    assert status_body["first_tenant_name"] == "本地客服工作台"


def test_local_setup_status_reports_delivery_blockers(client, monkeypatch) -> None:
    monkeypatch.setenv("STANDARD_OPS_ENV", "pilot")
    monkeypatch.setenv("STANDARD_OPS_DEV_BOOTSTRAP_ENABLED", "true")
    monkeypatch.setenv("OUTBOX_EXTERNAL_WRITE_ENABLED", "true")
    monkeypatch.setenv("TRUSTED_INBOUND_WORKER_ENABLED", "true")

    res = client.get("/api/auth/local-setup/status")
    assert res.status_code == 200
    body = res.json()
    assert body["local_deployment_ready"] is False
    assert body["dev_bootstrap_enabled"] is True
    assert body["external_write_enabled"] is True
    assert body["trusted_inbound_worker_enabled"] is True
    assert body["blockers"] == [
        "external_write_enabled",
        "dev_bootstrap_enabled",
        "trusted_inbound_worker_enabled",
    ]


def test_local_setup_blocks_second_owner_after_initialized(client, monkeypatch) -> None:
    _force_local_delivery_env(monkeypatch)

    first = client.post(
        "/api/auth/local-setup/owner",
        json={
            "tenant_name": "本地客服工作台",
            "tenant_slug": "wanfa-local",
            "owner_name": "本地管理员",
            "email": "owner@wanfa.local",
            "password": "ChangeMe123!",
        },
    )
    assert first.status_code == 201

    second = client.post(
        "/api/auth/local-setup/owner",
        json={
            "tenant_name": "第二工作台",
            "tenant_slug": "wanfa-second",
            "owner_name": "第二管理员",
            "email": "second@wanfa.local",
            "password": "ChangeMe123!",
        },
    )
    assert second.status_code == 409
    assert second.json()["detail"] == "local workspace already initialized"


def test_local_setup_rejects_invalid_slug(client) -> None:
    res = client.post(
        "/api/auth/local-setup/owner",
        json={
            "tenant_name": "本地客服工作台",
            "tenant_slug": "万法 本地",
            "owner_name": "本地管理员",
            "email": "owner@wanfa.local",
            "password": "ChangeMe123!",
        },
    )
    assert res.status_code == 422


def test_local_owner_creation_blocks_unsafe_customer_mode_flags(client, monkeypatch) -> None:
    monkeypatch.setenv("STANDARD_OPS_ENV", "pilot")
    monkeypatch.setenv("STANDARD_OPS_DEV_BOOTSTRAP_ENABLED", "true")
    monkeypatch.setenv("OUTBOX_EXTERNAL_WRITE_ENABLED", "true")
    monkeypatch.setenv("TRUSTED_INBOUND_WORKER_ENABLED", "true")

    res = client.post(
        "/api/auth/local-setup/owner",
        json={
            "tenant_name": "本地客服工作台",
            "tenant_slug": "wanfa-local",
            "owner_name": "本地管理员",
            "email": "owner@wanfa.local",
            "password": "ChangeMe123!",
        },
    )

    assert res.status_code == 409
    detail = res.json()["detail"]
    assert detail["message"] == "local deployment safety blockers"
    assert detail["blockers"] == [
        "external_write_enabled",
        "dev_bootstrap_enabled",
        "trusted_inbound_worker_enabled",
    ]
