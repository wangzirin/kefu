def _bootstrap_owner(client, tenant: dict) -> dict[str, str]:
    role_res = client.post(
        f"/api/tenants/{tenant['id']}/roles",
        json={"code": "owner", "name": "管理员"},
    )
    assert role_res.status_code == 201
    role = role_res.json()
    user_res = client.post(
        f"/api/tenants/{tenant['id']}/users",
        json={"name": "管理员", "email": f"{tenant['slug']}@example.com", "password": "ChangeMe123!"},
    )
    assert user_res.status_code == 201
    assign_res = client.post(f"/api/users/{user_res.json()['id']}/roles", json={"role_id": role["id"]})
    assert assign_res.status_code == 201
    login_res = client.post(
        "/api/auth/login",
        json={"tenant_slug": tenant["slug"], "email": f"{tenant['slug']}@example.com", "password": "ChangeMe123!"},
    )
    assert login_res.status_code == 200
    return {"Authorization": f"Bearer {login_res.json()['access_token']}"}


def test_tenant_channel_contact_conversation_message_flow(client) -> None:
    tenant_res = client.post(
        "/api/tenants",
        json={"name": "演示客户", "slug": "demo-client", "plan": "standard_ops"},
    )
    assert tenant_res.status_code == 201
    tenant = tenant_res.json()
    assert tenant["id"] == 1
    headers = _bootstrap_owner(client, tenant)

    channel_res = client.post(
        f"/api/tenants/{tenant['id']}/channels",
        json={"type": "web", "name": "官网客服", "reply_mode": "auto", "status": "active"},
    )
    assert channel_res.status_code == 201
    channel = channel_res.json()

    contact_res = client.post(
        f"/api/tenants/{tenant['id']}/contacts",
        json={"display_name": "测试访客", "phone": "13800000000"},
    )
    assert contact_res.status_code == 201
    contact = contact_res.json()

    conversation_res = client.post(
        f"/api/tenants/{tenant['id']}/conversations",
        headers=headers,
        json={
            "channel_id": channel["id"],
            "contact_id": contact["id"],
            "subject": "咨询标准运营版",
            "status": "handoff",
        },
    )
    assert conversation_res.status_code == 201
    conversation = conversation_res.json()
    assert conversation["status"] == "handoff"

    message_res = client.post(
        f"/api/conversations/{conversation['id']}/messages",
        headers=headers,
        json={
            "direction": "inbound",
            "sender_type": "visitor",
            "content": "你好，我想了解智能客服",
        },
    )
    assert message_res.status_code == 201

    list_res = client.get(f"/api/tenants/{tenant['id']}/conversations?status=handoff", headers=headers)
    assert list_res.status_code == 200
    assert len(list_res.json()) == 1

    detail_res = client.get(f"/api/conversations/{conversation['id']}", headers=headers)
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert detail["messages"][0]["content"] == "你好，我想了解智能客服"


def test_local_agent_reply_message_is_tenant_scoped_and_updates_conversation(client) -> None:
    tenant = client.post(
        "/api/tenants",
        json={"name": "本地回复客户", "slug": "local-reply-client", "plan": "standard_ops"},
    ).json()
    headers = _bootstrap_owner(client, tenant)
    channel = client.post(
        f"/api/tenants/{tenant['id']}/channels",
        json={"type": "web", "name": "官网客服", "reply_mode": "auto", "status": "active"},
    ).json()
    contact = client.post(
        f"/api/tenants/{tenant['id']}/contacts",
        json={"display_name": "本地访客"},
    ).json()
    conversation = client.post(
        f"/api/tenants/{tenant['id']}/conversations",
        headers=headers,
        json={"channel_id": channel["id"], "contact_id": contact["id"], "status": "handoff"},
    ).json()

    empty_res = client.post(
        f"/api/conversations/{conversation['id']}/messages",
        headers=headers,
        json={"direction": "outbound", "sender_type": "agent", "content": "", "external_message_id": ""},
    )
    assert empty_res.status_code == 422

    reply_res = client.post(
        f"/api/conversations/{conversation['id']}/messages",
        headers=headers,
        json={
            "direction": "outbound",
            "sender_type": "agent",
            "content": "这是本地坐席回复，只写入本地会话。",
            "external_message_id": "",
        },
    )
    assert reply_res.status_code == 201
    reply = reply_res.json()
    assert reply["direction"] == "outbound"
    assert reply["sender_type"] == "agent"
    assert reply["external_message_id"] == ""

    detail = client.get(f"/api/conversations/{conversation['id']}", headers=headers).json()
    assert detail["messages"][-1]["content"] == "这是本地坐席回复，只写入本地会话。"
    assert detail["last_message_at"] == reply["created_at"]

    other = client.post("/api/tenants", json={"name": "其它客户", "slug": "other-local-reply"}).json()
    other_headers = _bootstrap_owner(client, other)
    cross_res = client.post(
        f"/api/conversations/{conversation['id']}/messages",
        headers=other_headers,
        json={"direction": "outbound", "sender_type": "agent", "content": "不能跨租户写入"},
    )
    assert cross_res.status_code == 404


def test_conversation_rejects_cross_tenant_channel(client) -> None:
    first = client.post("/api/tenants", json={"name": "客户A", "slug": "a"}).json()
    second = client.post("/api/tenants", json={"name": "客户B", "slug": "b"}).json()
    second_headers = _bootstrap_owner(client, second)
    channel = client.post(
        f"/api/tenants/{first['id']}/channels",
        json={"type": "web", "name": "A 官网"},
    ).json()
    contact = client.post(
        f"/api/tenants/{second['id']}/contacts",
        json={"display_name": "B 访客"},
    ).json()

    res = client.post(
        f"/api/tenants/{second['id']}/conversations",
        headers=second_headers,
        json={"channel_id": channel["id"], "contact_id": contact["id"]},
    )
    assert res.status_code == 404
