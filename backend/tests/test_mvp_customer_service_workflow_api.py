from test_channel_connectors_api import _bootstrap_owner


def _headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _create_contact(client, tenant_id: int, headers: dict) -> dict:
    res = client.post(
        f"/api/tenants/{tenant_id}/contacts",
        headers=headers,
        json={"display_name": "测试客户", "phone": "", "wechat": "website:test"},
    )
    assert res.status_code == 201
    return res.json()


def _create_website_channel(client, tenant_id: int, headers: dict) -> dict:
    res = client.post(
        f"/api/tenants/{tenant_id}/channels",
        headers=headers,
        json={"type": "website", "name": "网站客服", "reply_mode": "assist", "status": "active"},
    )
    assert res.status_code == 201
    return res.json()


def _conversation(client, tenant_id: int, headers: dict) -> dict:
    channel = _create_website_channel(client, tenant_id, headers)
    contact = _create_contact(client, tenant_id, headers)
    res = client.post(
        f"/api/tenants/{tenant_id}/conversations",
        headers=headers,
        json={"channel_id": channel["id"], "contact_id": contact["id"], "status": "open", "priority": "normal"},
    )
    assert res.status_code == 201
    return res.json()


def test_mvp_small_talk_auto_replies_on_website_and_stays_visiting(client) -> None:
    tenant, token = _bootstrap_owner(client, "mvp-smalltalk", "mvp-smalltalk@example.com")
    headers = _headers(token)
    conversation = _conversation(client, tenant["id"], headers)

    res = client.post(
        f"/api/conversations/{conversation['id']}/inbound-message-cycle",
        headers=headers,
        json={"direction": "inbound", "sender_type": "visitor", "content": "你好，在吗"},
    )

    assert res.status_code == 201
    body = res.json()
    assert body["ai_cycle"]["state"] == "auto_reply_ready"
    assert body["ai_cycle"]["conversation_status"] == "bot_visiting"
    assert body["ai_cycle"]["outbound_message_id"]


def test_mvp_product_without_knowledge_moves_to_queue_for_agent(client) -> None:
    tenant, token = _bootstrap_owner(client, "mvp-gap", "mvp-gap@example.com")
    headers = _headers(token)
    conversation = _conversation(client, tenant["id"], headers)

    res = client.post(
        f"/api/conversations/{conversation['id']}/inbound-message-cycle",
        headers=headers,
        json={"direction": "inbound", "sender_type": "visitor", "content": "有没有火星基地专属套餐？价格多少"},
    )

    assert res.status_code == 201
    body = res.json()
    assert body["ai_cycle"]["state"] == "knowledge_gap"
    assert body["ai_cycle"]["conversation_status"] == "queued_for_me"
    assert body["ai_cycle"]["outbound_message_id"] is None
    detail = client.get(f"/api/conversations/{conversation['id']}", headers=headers)
    assert detail.status_code == 200
    assert detail.json()["assigned_user_id"] is not None


def test_mvp_product_uses_robot_knowledge_document_chunks(client) -> None:
    tenant, token = _bootstrap_owner(client, "mvp-document-rag", "mvp-document-rag@example.com")
    headers = _headers(token)
    document_res = client.post(
        f"/api/tenants/{tenant['id']}/knowledge-documents",
        headers=headers,
        json={
            "title": "鲲界智餐套餐说明",
            "source_type": "manual_document",
            "source_uri": "robot://knowledge/kj-food-plan",
            "raw_text": "鲲界智餐套餐适合餐饮门店做 AI 客服和私域接待，试点价格为 9980 元，包含网站咨询接入、知识库投喂和基础回复评测。",
            "tags": ["套餐", "价格", "餐饮"],
            "status": "active",
            "chunk_size": 120,
            "chunk_overlap": 0,
        },
    )
    assert document_res.status_code == 201
    conversation = _conversation(client, tenant["id"], headers)

    res = client.post(
        f"/api/conversations/{conversation['id']}/inbound-message-cycle",
        headers=headers,
        json={"direction": "inbound", "sender_type": "visitor", "content": "鲲界智餐套餐价格多少？"},
    )

    assert res.status_code == 201
    body = res.json()
    assert body["ai_cycle"]["state"] == "auto_reply_ready"
    assert body["ai_cycle"]["conversation_status"] == "bot_visiting"
    decisions = client.get(
        f"/api/tenants/{tenant['id']}/reply-decisions?conversation_id={conversation['id']}",
        headers=headers,
    )
    assert decisions.status_code == 200
    payload = decisions.json()["items"][0]["decision_payload"]
    assert payload["reply_branch"] == "product_consulting_rag"
    assert any(match["source_kind"] == "document_chunk" for match in payload["knowledge_matches"])
    assert any(match["source_uri"] == "robot://knowledge/kj-food-plan" for match in payload["knowledge_matches"])


def test_mvp_business_hours_question_uses_knowledge_document(client) -> None:
    tenant, token = _bootstrap_owner(client, "mvp-business-hours-rag", "mvp-business-hours-rag@example.com")
    headers = _headers(token)
    document_res = client.post(
        f"/api/tenants/{tenant['id']}/knowledge-documents",
        headers=headers,
        json={
            "title": "营业时间",
            "source_type": "manual_document",
            "source_uri": "robot://knowledge/business-hours",
            "raw_text": "营业时间是 9:00-18:00。客服在这个时间段内接待客户咨询。",
            "tags": ["营业时间", "客服"],
            "status": "active",
            "chunk_size": 120,
            "chunk_overlap": 0,
        },
    )
    assert document_res.status_code == 201
    conversation = _conversation(client, tenant["id"], headers)

    res = client.post(
        f"/api/conversations/{conversation['id']}/inbound-message-cycle",
        headers=headers,
        json={"direction": "inbound", "sender_type": "visitor", "content": "你们几点上班？"},
    )

    assert res.status_code == 201
    body = res.json()
    assert body["ai_cycle"]["state"] == "auto_reply_ready"
    assert body["ai_cycle"]["conversation_status"] == "bot_visiting"
    detail = client.get(f"/api/conversations/{conversation['id']}", headers=headers)
    assert detail.status_code == 200
    messages = detail.json()["messages"]
    assert any(message["sender_type"] == "ai" and "9:00-18:00" in message["content"] for message in messages)
    decisions = client.get(
        f"/api/tenants/{tenant['id']}/reply-decisions?conversation_id={conversation['id']}",
        headers=headers,
    )
    assert decisions.status_code == 200
    payload = decisions.json()["items"][0]["decision_payload"]
    assert payload["reply_branch"] == "product_consulting_rag"
    assert any(match["source_uri"] == "robot://knowledge/business-hours" for match in payload["knowledge_matches"])


def test_mvp_claim_moves_queued_conversation_to_mine(client) -> None:
    tenant, token = _bootstrap_owner(client, "mvp-claim", "mvp-claim@example.com")
    headers = _headers(token)
    conversation = _conversation(client, tenant["id"], headers)
    client.post(
        f"/api/conversations/{conversation['id']}/inbound-message-cycle",
        headers=headers,
        json={"direction": "inbound", "sender_type": "visitor", "content": "我要投诉，转人工"},
    )

    claim = client.post(f"/api/conversations/{conversation['id']}/claim", headers=headers)

    assert claim.status_code == 200
    assert claim.json()["status"] == "assigned_to_me"


def test_agent_must_claim_before_replying_to_queued_conversation(client) -> None:
    tenant, token = _bootstrap_owner(client, "mvp-claim-before-reply", "mvp-claim-before-reply@example.com")
    headers = _headers(token)
    conversation = _conversation(client, tenant["id"], headers)
    client.post(
        f"/api/conversations/{conversation['id']}/inbound-message-cycle",
        headers=headers,
        json={"direction": "inbound", "sender_type": "visitor", "content": "我要投诉，转人工处理"},
    )

    reply = client.post(
        f"/api/conversations/{conversation['id']}/agent-replies",
        headers=headers,
        json={"content": "您好，我来帮您处理。"},
    )

    assert reply.status_code == 409
    assert reply.json()["detail"] == "claim conversation before replying"


def test_claimed_agent_reply_is_visible_to_website_visitor(client) -> None:
    tenant, token = _bootstrap_owner(client, "mvp-agent-reply", "mvp-agent-reply@example.com")
    headers = _headers(token)
    conversation = _conversation(client, tenant["id"], headers)
    client.post(
        f"/api/conversations/{conversation['id']}/inbound-message-cycle",
        headers=headers,
        json={"direction": "inbound", "sender_type": "visitor", "content": "我要投诉，转人工"},
    )
    claim = client.post(f"/api/conversations/{conversation['id']}/claim", headers=headers)
    assert claim.status_code == 200

    reply = client.post(
        f"/api/conversations/{conversation['id']}/agent-replies",
        headers=headers,
        json={"content": "您好，我来帮您处理。"},
    )

    assert reply.status_code == 201
    assert reply.json()["sender_type"] == "agent"
    detail = client.get(f"/api/conversations/{conversation['id']}", headers=headers)
    assert detail.status_code == 200
    body = detail.json()
    assert body["status"] == "assigned_to_me"
    assert any(message["content"] == "您好，我来帮您处理。" for message in body["messages"])


def test_ai_stops_for_claimed_conversation_without_affecting_other_conversations(client) -> None:
    tenant, token = _bootstrap_owner(client, "mvp-ai-stops-after-claim", "mvp-ai-stops-after-claim@example.com")
    headers = _headers(token)
    claimed = _conversation(client, tenant["id"], headers)
    other = _conversation(client, tenant["id"], headers)
    client.post(
        f"/api/conversations/{claimed['id']}/inbound-message-cycle",
        headers=headers,
        json={"direction": "inbound", "sender_type": "visitor", "content": "我要投诉，转人工"},
    )
    claim = client.post(f"/api/conversations/{claimed['id']}/claim", headers=headers)
    assert claim.status_code == 200

    claimed_follow_up = client.post(
        f"/api/conversations/{claimed['id']}/inbound-message-cycle",
        headers=headers,
        json={"direction": "inbound", "sender_type": "visitor", "content": "我补充一下我的问题"},
    )
    other_message = client.post(
        f"/api/conversations/{other['id']}/inbound-message-cycle",
        headers=headers,
        json={"direction": "inbound", "sender_type": "visitor", "content": "你好"},
    )

    assert claimed_follow_up.status_code == 201
    assert claimed_follow_up.json()["ai_cycle"]["status"] == "skipped"
    assert claimed_follow_up.json()["ai_cycle"]["reason"] == "conversation_claimed_by_agent"
    detail = client.get(f"/api/conversations/{claimed['id']}", headers=headers)
    assert detail.status_code == 200
    assert all(message["sender_type"] != "ai" for message in detail.json()["messages"][-1:])
    assert other_message.status_code == 201
    assert other_message.json()["ai_cycle"]["state"] == "auto_reply_ready"
    assert other_message.json()["ai_cycle"]["conversation_status"] == "bot_visiting"


def test_close_conversation_exits_three_columns_and_adds_customer_notice(client) -> None:
    tenant, token = _bootstrap_owner(client, "mvp-close", "mvp-close@example.com")
    headers = _headers(token)
    conversation = _conversation(client, tenant["id"], headers)
    client.post(
        f"/api/conversations/{conversation['id']}/inbound-message-cycle",
        headers=headers,
        json={"direction": "inbound", "sender_type": "visitor", "content": "我要投诉，转人工"},
    )
    client.post(f"/api/conversations/{conversation['id']}/claim", headers=headers)

    close = client.post(
        f"/api/conversations/{conversation['id']}/workflow-actions",
        headers=headers,
        json={"action": "close"},
    )

    assert close.status_code == 200
    assert close.json()["status"] == "closed"
    detail = client.get(f"/api/conversations/{conversation['id']}", headers=headers)
    assert detail.status_code == 200
    messages = detail.json()["messages"]
    assert any(message["sender_type"] == "system" and "已关闭对话" in message["content"] for message in messages)


def test_mvp_three_column_status_filters_are_current_agent_scoped(client) -> None:
    tenant, owner_token = _bootstrap_owner(client, "mvp-three-columns", "mvp-three-columns@example.com")
    owner_headers = _headers(owner_token)
    me_res = client.get("/api/auth/me", headers=owner_headers)
    assert me_res.status_code == 200
    current_user_id = int(me_res.json()["id"])

    visiting = _conversation(client, tenant["id"], owner_headers)
    queued_for_me = _conversation(client, tenant["id"], owner_headers)
    claimed_by_me = _conversation(client, tenant["id"], owner_headers)
    other_queue = _conversation(client, tenant["id"], owner_headers)
    closed = _conversation(client, tenant["id"], owner_headers)

    assert client.patch(
        f"/api/conversations/{visiting['id']}/assignment",
        headers=owner_headers,
        json={"assigned_user_id": None, "status": "bot_visiting"},
    ).status_code == 200
    assert client.patch(
        f"/api/conversations/{queued_for_me['id']}/assignment",
        headers=owner_headers,
        json={"assigned_user_id": current_user_id, "status": "queued_for_me"},
    ).status_code == 200
    assert client.patch(
        f"/api/conversations/{claimed_by_me['id']}/assignment",
        headers=owner_headers,
        json={"assigned_user_id": current_user_id, "status": "assigned_to_me"},
    ).status_code == 200
    assert client.patch(
        f"/api/conversations/{other_queue['id']}/assignment",
        headers=owner_headers,
        json={"assigned_user_id": None, "status": "queued_for_me"},
    ).status_code == 200
    assert client.post(
        f"/api/conversations/{closed['id']}/workflow-actions",
        headers=owner_headers,
        json={"action": "close"},
    ).status_code == 200

    visiting_res = client.get(
        f"/api/tenants/{tenant['id']}/conversation-inbox?status=bot_visiting",
        headers=owner_headers,
    )
    queued_res = client.get(
        f"/api/tenants/{tenant['id']}/conversation-inbox?status=queued_for_me&assigned=mine",
        headers=owner_headers,
    )
    mine_res = client.get(
        f"/api/tenants/{tenant['id']}/conversation-inbox?status=assigned_to_me&assigned=mine",
        headers=owner_headers,
    )

    assert visiting_res.status_code == 200
    assert {item["id"] for item in visiting_res.json()["items"]} == {visiting["id"]}
    assert queued_res.status_code == 200
    assert {item["id"] for item in queued_res.json()["items"]} == {queued_for_me["id"]}
    assert mine_res.status_code == 200
    assert {item["id"] for item in mine_res.json()["items"]} == {claimed_by_me["id"]}
