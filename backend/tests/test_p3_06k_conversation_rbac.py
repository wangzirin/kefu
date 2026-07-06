from app.core.rbac import allowed_roles_for_permission, permissions_for_roles


def _create_tenant(client, *, slug: str) -> dict:
    res = client.post("/api/tenants", json={"name": f"{slug} 客户", "slug": slug})
    assert res.status_code == 201
    return res.json()


def _bootstrap_owner(client, tenant: dict) -> tuple[dict, dict, str]:
    role_res = client.post(
        f"/api/tenants/{tenant['id']}/roles",
        json={"code": "owner", "name": "负责人"},
    )
    assert role_res.status_code == 201
    role = role_res.json()

    user_res = client.post(
        f"/api/tenants/{tenant['id']}/users",
        json={"name": "负责人", "email": f"{tenant['slug']}-owner@example.com", "password": "ChangeMe123!"},
    )
    assert user_res.status_code == 201
    user = user_res.json()

    assign_res = client.post(f"/api/users/{user['id']}/roles", json={"role_id": role["id"]})
    assert assign_res.status_code == 201

    login_res = client.post(
        "/api/auth/login",
        json={
            "tenant_slug": tenant["slug"],
            "email": f"{tenant['slug']}-owner@example.com",
            "password": "ChangeMe123!",
        },
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


def _create_channel_and_contact(client, tenant_id: int) -> tuple[dict, dict]:
    channel_res = client.post(
        f"/api/tenants/{tenant_id}/channels",
        json={"type": "web", "name": "官网客服", "reply_mode": "assist", "status": "active"},
    )
    assert channel_res.status_code == 201
    contact_res = client.post(
        f"/api/tenants/{tenant_id}/contacts",
        json={"display_name": "权限测试访客"},
    )
    assert contact_res.status_code == 201
    return channel_res.json(), contact_res.json()


def _create_conversation_with_message(client, tenant_id: int, headers: dict) -> tuple[dict, dict]:
    channel, contact = _create_channel_and_contact(client, tenant_id)
    conversation_res = client.post(
        f"/api/tenants/{tenant_id}/conversations",
        headers=headers,
        json={
            "channel_id": channel["id"],
            "contact_id": contact["id"],
            "subject": "权限收口测试",
        },
    )
    assert conversation_res.status_code == 201
    conversation = conversation_res.json()
    message_res = client.post(
        f"/api/conversations/{conversation['id']}/messages",
        headers=headers,
        json={"direction": "inbound", "sender_type": "visitor", "content": "请问试点怎么开始？"},
    )
    assert message_res.status_code == 201
    return conversation, message_res.json()


def test_conversation_permissions_allow_agent_and_block_viewer() -> None:
    expected = ("admin", "agent", "owner")
    assert allowed_roles_for_permission("conversation.read") == expected
    assert allowed_roles_for_permission("conversation.manage") == expected
    assert "conversation.read" in permissions_for_roles(["agent"])
    assert "conversation.manage" in permissions_for_roles(["agent"])
    assert "conversation.read" not in permissions_for_roles(["viewer"])
    assert "conversation.manage" not in permissions_for_roles(["viewer"])


def test_conversation_read_and_write_endpoints_require_named_permissions(client) -> None:
    tenant = _create_tenant(client, slug="rbac-conversation")
    _owner_role, _owner, owner_token = _bootstrap_owner(client, tenant)
    owner_headers = {"Authorization": f"Bearer {owner_token}"}
    agent, agent_token = _create_user_with_role(
        client,
        tenant=tenant,
        role_code="agent",
        email="conversation-agent@example.com",
        owner_token=owner_token,
    )
    _viewer, viewer_token = _create_user_with_role(
        client,
        tenant=tenant,
        role_code="viewer",
        email="conversation-viewer@example.com",
        owner_token=owner_token,
    )
    agent_headers = {"Authorization": f"Bearer {agent_token}"}
    viewer_headers = {"Authorization": f"Bearer {viewer_token}"}
    conversation, _message = _create_conversation_with_message(client, tenant["id"], owner_headers)

    no_token_list = client.get(f"/api/tenants/{tenant['id']}/conversations")
    assert no_token_list.status_code == 401

    viewer_list = client.get(f"/api/tenants/{tenant['id']}/conversations", headers=viewer_headers)
    viewer_detail = client.get(f"/api/conversations/{conversation['id']}", headers=viewer_headers)
    viewer_message = client.post(
        f"/api/conversations/{conversation['id']}/messages",
        headers=viewer_headers,
        json={"direction": "inbound", "sender_type": "visitor", "content": "viewer 不应写消息"},
    )
    viewer_assignment = client.patch(
        f"/api/conversations/{conversation['id']}/assignment",
        headers=viewer_headers,
        json={"assigned_user_id": None},
    )
    assert viewer_list.status_code == 403
    assert viewer_list.json()["detail"] == "insufficient permission"
    assert viewer_detail.status_code == 403
    assert viewer_message.status_code == 403
    assert viewer_assignment.status_code == 403

    agent_list = client.get(f"/api/tenants/{tenant['id']}/conversations", headers=agent_headers)
    agent_detail = client.get(f"/api/conversations/{conversation['id']}", headers=agent_headers)
    agent_message = client.post(
        f"/api/conversations/{conversation['id']}/messages",
        headers=agent_headers,
        json={"direction": "inbound", "sender_type": "visitor", "content": "agent 可以追加会话消息"},
    )
    agent_claim = client.post(
        f"/api/conversations/{conversation['id']}/workflow-actions",
        headers=agent_headers,
        json={"action": "claim", "note": "坐席接手"},
    )
    assert agent_list.status_code == 200
    assert [item["id"] for item in agent_list.json()] == [conversation["id"]]
    assert agent_detail.status_code == 200
    assert agent_message.status_code == 201
    assert agent_claim.status_code == 200
    assert agent_claim.json()["assigned_user_id"] == agent["id"]


def test_conversation_permission_keeps_cross_tenant_resources_hidden(client) -> None:
    first = _create_tenant(client, slug="rbac-conversation-first")
    _first_role, _first_owner, first_token = _bootstrap_owner(client, first)
    second = _create_tenant(client, slug="rbac-conversation-second")
    _second_role, _second_owner, second_token = _bootstrap_owner(client, second)
    first_headers = {"Authorization": f"Bearer {first_token}"}
    second_headers = {"Authorization": f"Bearer {second_token}"}

    second_conversation, _message = _create_conversation_with_message(client, second["id"], second_headers)

    cross_detail = client.get(f"/api/conversations/{second_conversation['id']}", headers=first_headers)
    cross_message = client.post(
        f"/api/conversations/{second_conversation['id']}/messages",
        headers=first_headers,
        json={"direction": "inbound", "sender_type": "visitor", "content": "不能跨租户写入"},
    )
    cross_list = client.get(f"/api/tenants/{second['id']}/conversations", headers=first_headers)

    assert first["id"] != second["id"]
    assert cross_detail.status_code == 404
    assert cross_message.status_code == 404
    assert cross_list.status_code == 404
