from app.core.rbac import allowed_roles_for_permission, permissions_for_roles
from test_knowledge_api import _bootstrap_user


def _create_user_with_role(
    client,
    *,
    tenant: dict,
    owner_headers: dict,
    role_code: str,
    email: str,
) -> tuple[dict, dict]:
    role_res = client.post(
        f"/api/tenants/{tenant['id']}/roles",
        headers=owner_headers,
        json={"code": role_code, "name": role_code},
    )
    assert role_res.status_code == 201
    role = role_res.json()

    user_res = client.post(
        f"/api/tenants/{tenant['id']}/users",
        headers=owner_headers,
        json={"name": role_code, "email": email, "password": "ChangeMe123!"},
    )
    assert user_res.status_code == 201
    user = user_res.json()

    assign_res = client.post(
        f"/api/users/{user['id']}/roles",
        headers=owner_headers,
        json={"role_id": role["id"]},
    )
    assert assign_res.status_code == 201

    login_res = client.post(
        "/api/auth/login",
        json={"tenant_slug": tenant["slug"], "email": email, "password": "ChangeMe123!"},
    )
    assert login_res.status_code == 200
    return user, {"Authorization": f"Bearer {login_res.json()['access_token']}"}


def test_knowledge_permissions_matrix() -> None:
    assert allowed_roles_for_permission("knowledge.read") == ("admin", "agent", "owner")
    assert allowed_roles_for_permission("knowledge.manage") == ("admin", "owner")
    assert "knowledge.read" in permissions_for_roles(["agent"])
    assert "knowledge.manage" not in permissions_for_roles(["agent"])
    assert "knowledge.read" not in permissions_for_roles(["viewer"])
    assert "knowledge.manage" not in permissions_for_roles(["viewer"])


def test_agent_can_read_knowledge_but_cannot_manage_it_and_viewer_is_blocked(client) -> None:
    tenant, _owner, owner_token = _bootstrap_user(
        client,
        slug="knowledge-rbac",
        email="knowledge-rbac-owner@example.com",
    )
    owner_headers = {"Authorization": f"Bearer {owner_token}"}
    _admin, admin_headers = _create_user_with_role(
        client,
        tenant=tenant,
        owner_headers=owner_headers,
        role_code="admin",
        email="knowledge-rbac-admin@example.com",
    )
    _agent, agent_headers = _create_user_with_role(
        client,
        tenant=tenant,
        owner_headers=owner_headers,
        role_code="agent",
        email="knowledge-rbac-agent@example.com",
    )
    _viewer, viewer_headers = _create_user_with_role(
        client,
        tenant=tenant,
        owner_headers=owner_headers,
        role_code="viewer",
        email="knowledge-rbac-viewer@example.com",
    )

    no_token_res = client.get(f"/api/tenants/{tenant['id']}/knowledge-cards")
    assert no_token_res.status_code == 401

    owner_card_res = client.post(
        f"/api/tenants/{tenant['id']}/knowledge-cards",
        headers=owner_headers,
        json={
            "title": "企业微信客服接入",
            "question": "企业微信客服怎么接入？",
            "answer": "使用官方微信客服 API、回调验签和可信入站流程。",
            "tags": ["企业微信", "渠道"],
            "status": "active",
        },
    )
    assert owner_card_res.status_code == 201

    admin_create_res = client.post(
        f"/api/tenants/{tenant['id']}/knowledge-cards",
        headers=admin_headers,
        json={
            "title": "售后政策",
            "question": "售后政策怎么查？",
            "answer": "以正式知识库文档和人工审核结论为准。",
            "tags": ["售后"],
            "status": "active",
        },
    )
    assert admin_create_res.status_code == 201

    agent_list_res = client.get(f"/api/tenants/{tenant['id']}/knowledge-cards", headers=agent_headers)
    agent_search_res = client.post(
        f"/api/tenants/{tenant['id']}/knowledge-searches",
        headers=agent_headers,
        json={"query": "企业微信客服接入", "top_k": 3},
    )
    agent_create_res = client.post(
        f"/api/tenants/{tenant['id']}/knowledge-cards",
        headers=agent_headers,
        json={"title": "坐席不能写", "question": "能写吗？", "answer": "不能。"},
    )
    viewer_list_res = client.get(f"/api/tenants/{tenant['id']}/knowledge-cards", headers=viewer_headers)

    assert agent_list_res.status_code == 200
    assert agent_list_res.json()["total"] == 2
    assert agent_search_res.status_code == 200
    assert agent_search_res.json()["matches"]
    assert agent_create_res.status_code == 403
    assert agent_create_res.json()["detail"] == "insufficient permission"
    assert viewer_list_res.status_code == 403
    assert viewer_list_res.json()["detail"] == "insufficient permission"


def test_knowledge_read_permission_keeps_cross_tenant_hidden(client) -> None:
    first, _first_owner, first_token = _bootstrap_user(
        client,
        slug="knowledge-rbac-first",
        email="knowledge-rbac-first@example.com",
    )
    second, _second_owner, second_token = _bootstrap_user(
        client,
        slug="knowledge-rbac-second",
        email="knowledge-rbac-second@example.com",
    )
    first_headers = {"Authorization": f"Bearer {first_token}"}
    second_headers = {"Authorization": f"Bearer {second_token}"}

    create_res = client.post(
        f"/api/tenants/{second['id']}/knowledge-cards",
        headers=second_headers,
        json={
            "title": "第二租户知识",
            "question": "只能第二租户看吗？",
            "answer": "是。",
            "status": "active",
        },
    )
    assert create_res.status_code == 201

    cross_list_res = client.get(f"/api/tenants/{second['id']}/knowledge-cards", headers=first_headers)
    cross_search_res = client.post(
        f"/api/tenants/{second['id']}/knowledge-searches",
        headers=first_headers,
        json={"query": "第二租户知识", "top_k": 3},
    )
    own_empty_res = client.get(f"/api/tenants/{first['id']}/knowledge-cards", headers=first_headers)

    assert cross_list_res.status_code == 404
    assert cross_search_res.status_code == 404
    assert own_empty_res.status_code == 200
    assert own_empty_res.json()["total"] == 0
