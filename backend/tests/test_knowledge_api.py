import json


def _bootstrap_user(client, *, slug: str, email: str, role_code: str = "owner") -> tuple[dict, dict, str]:
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
        json={"name": f"{role_code} 用户", "email": email, "password": "ChangeMe123!"},
    )
    assert user_res.status_code == 201
    user = user_res.json()

    assign_res = client.post(f"/api/users/{user['id']}/roles", json={"role_id": role["id"]})
    assert assign_res.status_code == 201

    login_res = client.post(
        "/api/auth/login",
        json={"tenant_slug": tenant["slug"], "email": email, "password": "ChangeMe123!"},
    )
    assert login_res.status_code == 200
    return tenant, user, login_res.json()["access_token"]


def test_owner_can_create_list_and_search_knowledge_cards(client) -> None:
    tenant, _, token = _bootstrap_user(client, slug="knowledge-owner", email="knowledge-owner@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    no_token_res = client.post(
        f"/api/tenants/{tenant['id']}/knowledge-cards",
        json={
            "title": "七天退换货政策",
            "question": "超过七天还能退货吗？",
            "answer": "超过七天是否可以退货，需要结合订单政策、商品状态和售后规则确认。",
            "tags": ["售后", "退款"],
        },
    )
    assert no_token_res.status_code == 401

    card_res = client.post(
        f"/api/tenants/{tenant['id']}/knowledge-cards",
        headers=headers,
        json={
            "title": "七天退换货政策",
            "question": "超过七天还能退货吗？",
            "answer": "超过七天是否可以退货，需要结合订单政策、商品状态和售后规则确认。",
            "source_type": "manual",
            "source_uri": "internal://policy/after-sales",
            "tags": ["售后", "退款"],
            "aliases": ["退货", "售后政策"],
            "status": "active",
        },
    )
    assert card_res.status_code == 201
    card = card_res.json()
    assert card["tenant_id"] == tenant["id"]
    assert card["status"] == "active"
    assert card["tags"] == ["售后", "退款"]

    list_res = client.get(f"/api/tenants/{tenant['id']}/knowledge-cards?status=active", headers=headers)
    assert list_res.status_code == 200
    assert [item["id"] for item in list_res.json()["items"]] == [card["id"]]

    search_res = client.post(
        f"/api/tenants/{tenant['id']}/knowledge-searches",
        headers=headers,
        json={"query": "客户超过七天申请退货怎么办", "top_k": 3},
    )
    assert search_res.status_code == 200
    search = search_res.json()
    assert search["retrieval_mode"] == "lexical_bm25_v1"
    assert search["total_candidates"] == 1
    assert search["matches"][0]["card"]["id"] == card["id"]
    assert search["matches"][0]["score"] > 0
    assert search["matches"][0]["confidence"] > 0
    assert "退货" in search["matches"][0]["matched_terms"]


def test_owner_can_manage_business_objects_and_object_knowledge_cards(client) -> None:
    tenant, _, token = _bootstrap_user(
        client,
        slug="knowledge-business-object",
        email="knowledge-business-object@example.com",
    )
    headers = {"Authorization": f"Bearer {token}"}

    created_objects = []
    for object_type, title, aliases in [
        ("product", "AI 客服入门验证包", ["入门版", "Lite A"]),
        ("service", "企业微信官方接入服务", ["企微接入", "微信客服接入"]),
        ("package", "标准运营版套餐", ["标准版", "运营版"]),
    ]:
        res = client.post(
            f"/api/tenants/{tenant['id']}/business-objects",
            headers=headers,
            json={
                "type": object_type,
                "title": title,
                "summary": f"{title} 的适用场景、边界和交付口径。",
                "aliases": aliases,
                "attrs_json": {"delivery_days": 7, "channels": ["web", "wecom"]},
                "status": "active",
            },
        )
        assert res.status_code == 201
        body = res.json()
        assert body["tenant_id"] == tenant["id"]
        assert body["type"] == object_type
        assert body["aliases"] == aliases
        assert body["knowledge_card_count"] == 0
        created_objects.append(body)

    list_res = client.get(f"/api/tenants/{tenant['id']}/business-objects?status=active", headers=headers)
    assert list_res.status_code == 200
    listed = list_res.json()
    assert listed["total"] == 3
    assert {item["type"] for item in listed["items"]} == {"product", "service", "package"}

    product = next(item for item in created_objects if item["type"] == "product")
    update_res = client.patch(
        f"/api/business-objects/{product['id']}",
        headers=headers,
        json={
            "title": "AI 客服入门验证包升级版",
            "summary": "已通过业务对象编辑接口更新的适用场景和交付口径。",
            "aliases": ["入门升级版", "Lite A Plus"],
            "status": "active",
        },
    )
    assert update_res.status_code == 200
    updated_object = update_res.json()
    assert updated_object["id"] == product["id"]
    assert updated_object["title"] == "AI 客服入门验证包升级版"
    assert updated_object["summary"] == "已通过业务对象编辑接口更新的适用场景和交付口径。"
    assert updated_object["aliases"] == ["入门升级版", "Lite A Plus"]

    refreshed_product = client.get(
        f"/api/tenants/{tenant['id']}/business-objects?type=product",
        headers=headers,
    ).json()
    assert refreshed_product["items"][0]["title"] == "AI 客服入门验证包升级版"
    assert refreshed_product["items"][0]["aliases"] == ["入门升级版", "Lite A Plus"]

    card_res = client.post(
        f"/api/business-objects/{product['id']}/knowledge-cards",
        headers=headers,
        json={
            "question": "入门验证包适合什么客户？",
            "answer": "适合先验证官网客服、核心 FAQ、留资和人工接管流程的中小企业。",
            "trigger_keywords": ["入门验证", "官网客服", "先试用"],
            "scope": {"channels": ["web", "wechat_service"], "reply_mode": "auto_with_handoff"},
            "source": "manual",
            "status": "active",
        },
    )
    assert card_res.status_code == 201
    card = card_res.json()
    assert card["business_object_id"] == product["id"]
    assert card["trigger_keywords"] == ["入门验证", "官网客服", "先试用"]

    object_cards_res = client.get(
        f"/api/business-objects/{product['id']}/knowledge-cards?status=active",
        headers=headers,
    )
    assert object_cards_res.status_code == 200
    assert object_cards_res.json()["items"][0]["question"] == "入门验证包适合什么客户？"

    refreshed_objects = client.get(
        f"/api/tenants/{tenant['id']}/business-objects?type=product",
        headers=headers,
    ).json()
    assert refreshed_objects["items"][0]["knowledge_card_count"] == 1


def test_owner_can_read_knowledge_memory_mesh_overview_without_raw_text(client) -> None:
    tenant, _, token = _bootstrap_user(
        client,
        slug="knowledge-memory-mesh",
        email="knowledge-memory-mesh@example.com",
    )
    headers = {"Authorization": f"Bearer {token}"}

    object_res = client.post(
        f"/api/tenants/{tenant['id']}/business-objects",
        headers=headers,
        json={
            "type": "service",
            "title": "本地试跑服务",
            "summary": "用于验证知识导入、复测和质量复盘的本地服务。",
            "aliases": ["试跑包"],
            "status": "active",
        },
    )
    assert object_res.status_code == 201

    raw_text = "售后流程说明：客户申请退款时，需要先核对订单、服务进度和不可承诺事项。"
    document_res = client.post(
        f"/api/tenants/{tenant['id']}/knowledge-documents",
        headers=headers,
        json={
            "title": "售后流程说明",
            "source_type": "customer_csv",
            "source_uri": "internal://customer-materials/after-sales",
            "raw_text": raw_text,
            "tags": ["售后", "流程"],
            "status": "active",
            "chunk_size": 80,
            "chunk_overlap": 0,
        },
    )
    assert document_res.status_code == 201
    assert document_res.json()["chunk_count"] >= 1

    overview_res = client.get(
        f"/api/tenants/{tenant['id']}/knowledge-memory-mesh-overview",
        headers=headers,
    )
    assert overview_res.status_code == 200
    overview = overview_res.json()
    assert overview["schema_version"] == "p3-06u-26h2w-nc4.knowledge_memory_mesh_overview.v1"
    assert overview["status"] == "knowledge_memory_mesh_overview_ready"
    assert overview["boundaries"]["raw_text_included"] is False
    assert overview["boundaries"]["real_platform_send_ready"] is False
    assert overview["readiness"]["real_platform_send_ready"] is False
    assert overview["readiness"]["full_memory_mesh_ready"] is False
    assert overview["source_authority"]["chunks_with_source_uri_and_hash"] >= 1
    assert {"资料批次", "知识卡片", "业务对象", "真实/样本问题", "质量标签与错因"}.issubset(
        {item["label"] for item in overview["nodes"]}
    )
    assert {"入站样本", "检索结果", "引用 chunk", "模型调用", "最终草稿", "转人工理由", "质量标签", "修复后的知识版本"}.issubset(
        {item["label"] for item in overview["provenance_steps"]}
    )
    assert raw_text not in json.dumps(overview, ensure_ascii=False)


def test_agent_can_search_but_cannot_write_knowledge_cards(client) -> None:
    tenant, _, owner_token = _bootstrap_user(
        client,
        slug="knowledge-agent",
        email="knowledge-owner-agent@example.com",
        role_code="owner",
    )
    owner_headers = {"Authorization": f"Bearer {owner_token}"}
    agent_role = client.post(
        f"/api/tenants/{tenant['id']}/roles",
        headers=owner_headers,
        json={"code": "agent", "name": "客服坐席"},
    ).json()
    agent_res = client.post(
        f"/api/tenants/{tenant['id']}/users",
        headers=owner_headers,
        json={"name": "客服坐席", "email": "knowledge-agent@example.com", "password": "ChangeMe123!"},
    )
    assert agent_res.status_code == 201
    assign_res = client.post(
        f"/api/users/{agent_res.json()['id']}/roles",
        headers=owner_headers,
        json={"role_id": agent_role["id"]},
    )
    assert assign_res.status_code == 201
    login_res = client.post(
        "/api/auth/login",
        json={
            "tenant_slug": tenant["slug"],
            "email": "knowledge-agent@example.com",
            "password": "ChangeMe123!",
        },
    )
    agent_headers = {"Authorization": f"Bearer {login_res.json()['access_token']}"}

    card_res = client.post(
        f"/api/tenants/{tenant['id']}/knowledge-cards",
        headers=owner_headers,
        json={
            "title": "发票开具规则",
            "question": "可以开电子发票吗？",
            "answer": "可以开电子发票，通常需要提供抬头和税号。",
            "tags": ["发票"],
            "status": "active",
        },
    )
    assert card_res.status_code == 201

    forbidden_write = client.post(
        f"/api/tenants/{tenant['id']}/knowledge-cards",
        headers=agent_headers,
        json={
            "title": "坐席不能直接新增",
            "question": "坐席可以写知识吗？",
            "answer": "不能。",
        },
    )
    assert forbidden_write.status_code == 403

    search_res = client.post(
        f"/api/tenants/{tenant['id']}/knowledge-searches",
        headers=agent_headers,
        json={"query": "电子发票怎么开", "top_k": 5},
    )
    assert search_res.status_code == 200
    assert search_res.json()["matches"][0]["card"]["title"] == "发票开具规则"

    forbidden_object_write = client.post(
        f"/api/tenants/{tenant['id']}/business-objects",
        headers=agent_headers,
        json={
            "type": "product",
            "title": "坐席不能新增的商品",
            "summary": "坐席没有知识管理写权限。",
        },
    )
    assert forbidden_object_write.status_code == 403

    business_object_res = client.post(
        f"/api/tenants/{tenant['id']}/business-objects",
        headers=owner_headers,
        json={
            "type": "service",
            "title": "安装指导服务",
            "summary": "由管理员维护的服务对象。",
            "status": "active",
        },
    )
    assert business_object_res.status_code == 201
    list_objects_res = client.get(f"/api/tenants/{tenant['id']}/business-objects", headers=agent_headers)
    assert list_objects_res.status_code == 200
    assert list_objects_res.json()["items"][0]["title"] == "安装指导服务"

    forbidden_object_card_write = client.post(
        f"/api/business-objects/{business_object_res.json()['id']}/knowledge-cards",
        headers=agent_headers,
        json={"question": "坐席可以写对象卡吗？", "answer": "不能。"},
    )
    assert forbidden_object_card_write.status_code == 403


def test_knowledge_search_respects_tenant_and_status_boundaries(client) -> None:
    first, _, first_token = _bootstrap_user(
        client,
        slug="knowledge-first",
        email="knowledge-first@example.com",
    )
    second, _, second_token = _bootstrap_user(
        client,
        slug="knowledge-second",
        email="knowledge-second@example.com",
    )
    first_headers = {"Authorization": f"Bearer {first_token}"}
    second_headers = {"Authorization": f"Bearer {second_token}"}

    active_res = client.post(
        f"/api/tenants/{first['id']}/knowledge-cards",
        headers=first_headers,
        json={
            "title": "企业微信客服接入",
            "question": "怎么接企业微信客服？",
            "answer": "企业微信客服应走官方 API、回调验签和授权配置。",
            "tags": ["企业微信", "渠道"],
            "status": "active",
        },
    )
    assert active_res.status_code == 201

    archived_res = client.post(
        f"/api/tenants/{first['id']}/knowledge-cards",
        headers=first_headers,
        json={
            "title": "旧版个人微信外挂方案",
            "question": "可以用个人微信外挂吗？",
            "answer": "旧方案已废弃，不能作为正式交付路径。",
            "tags": ["风险"],
            "status": "archived",
        },
    )
    assert archived_res.status_code == 201

    cross_tenant_create = client.post(
        f"/api/tenants/{second['id']}/knowledge-cards",
        headers=first_headers,
        json={"title": "越权知识", "question": "能写吗？", "answer": "不能。"},
    )
    assert cross_tenant_create.status_code == 404

    first_search = client.post(
        f"/api/tenants/{first['id']}/knowledge-searches",
        headers=first_headers,
        json={"query": "企业微信客服官方 API 怎么接", "top_k": 5},
    )
    assert first_search.status_code == 200
    assert [match["card"]["title"] for match in first_search.json()["matches"]] == ["企业微信客服接入"]

    archived_search = client.post(
        f"/api/tenants/{first['id']}/knowledge-searches",
        headers=first_headers,
        json={"query": "个人微信外挂", "top_k": 5},
    )
    assert archived_search.status_code == 200
    assert archived_search.json()["matches"] == []

    cross_tenant_search = client.post(
        f"/api/tenants/{first['id']}/knowledge-searches",
        headers=second_headers,
        json={"query": "企业微信客服", "top_k": 5},
    )
    assert cross_tenant_search.status_code == 404
