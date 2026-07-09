import pytest

from test_knowledge_api import _bootstrap_user


@pytest.fixture(autouse=True)
def _use_deterministic_embedding_provider(monkeypatch) -> None:
    monkeypatch.setenv("KNOWLEDGE_EMBEDDING_PROVIDER", "deterministic_local")
    monkeypatch.setenv("KNOWLEDGE_EMBEDDING_MODEL", "deterministic-token-vector-v1")
    monkeypatch.setenv("KNOWLEDGE_EMBEDDING_DIMENSIONS", "64")
    monkeypatch.setenv("KNOWLEDGE_RERANKER", "lexical_overlap_reranker_v1")


DOCUMENT_TEXT = """
# 售后政策手册

七天无理由退货适用于未拆封、未影响二次销售的标准商品。超过七天以后，系统不能直接承诺无理由退货。

如果客户超过七天申请退货，需要先核对订单时间、商品状态、是否存在质量问题以及平台售后规则。

# 保修政策

标准产品保修期为三年。保修期内如果出现非人为质量问题，可以安排检测、维修或换新。
""".strip()


def test_owner_can_import_document_and_search_chunk_citations(client) -> None:
    tenant, _, token = _bootstrap_user(
        client,
        slug="knowledge-doc-owner",
        email="knowledge-doc-owner@example.com",
    )
    headers = {"Authorization": f"Bearer {token}"}

    no_token_res = client.post(
        f"/api/tenants/{tenant['id']}/knowledge-documents",
        json={
            "title": "售后政策手册",
            "source_type": "manual_document",
            "raw_text": DOCUMENT_TEXT,
            "status": "active",
        },
    )
    assert no_token_res.status_code == 401

    document_res = client.post(
        f"/api/tenants/{tenant['id']}/knowledge-documents",
        headers=headers,
        json={
            "title": "售后政策手册",
            "source_type": "manual_document",
            "source_uri": "internal://docs/after-sales-v1",
            "raw_text": DOCUMENT_TEXT,
            "tags": ["售后", "保修"],
            "status": "active",
            "chunk_size": 90,
            "chunk_overlap": 10,
        },
    )
    assert document_res.status_code == 201
    document = document_res.json()
    assert document["tenant_id"] == tenant["id"]
    assert document["title"] == "售后政策手册"
    assert document["status"] == "active"
    assert document["chunk_count"] >= 3
    assert document["ingestion_status"] == "indexed"

    chunks_res = client.get(f"/api/knowledge-documents/{document['id']}/chunks", headers=headers)
    assert chunks_res.status_code == 200
    chunks = chunks_res.json()
    assert len(chunks) == document["chunk_count"]
    assert chunks[0]["document_id"] == document["id"]
    assert chunks[0]["chunk_index"] == 0
    assert chunks[0]["source_uri"] == "internal://docs/after-sales-v1"
    assert chunks[0]["content"]
    assert chunks[0]["citation"]["document_title"] == "售后政策手册"

    search_res = client.post(
        f"/api/tenants/{tenant['id']}/knowledge-document-searches",
        headers=headers,
        json={"query": "超过七天退货需要核对什么", "top_k": 3},
    )
    assert search_res.status_code == 200
    search = search_res.json()
    assert search["retrieval_mode"] == "hybrid_bm25_vector_rerank_v1"
    assert search["vector_engine"] == "deterministic_local_hash_embedding_v1"
    assert search["vector_store"] == "sqlite_json_vector_store"
    assert search["embedding_provider"] == "deterministic_local"
    assert search["reranker"] == "lexical_overlap_reranker_v1"
    assert search["total_candidates"] == document["chunk_count"]
    assert search["matches"]
    top = search["matches"][0]
    assert top["document_id"] == document["id"]
    assert top["chunk_id"] in [chunk["id"] for chunk in chunks]
    assert top["score"] > 0
    assert top["confidence"] > 0
    assert top["reranker_score"] >= 0
    assert "七天" in top["content_preview"] or "退货" in top["content_preview"]
    assert top["citation"]["source_uri"] == "internal://docs/after-sales-v1"
    assert top["citation"]["chunk_index"] == top["chunk_index"]


def test_owner_can_classify_disable_and_delete_documents(client) -> None:
    tenant, _, token = _bootstrap_user(
        client,
        slug="knowledge-doc-category",
        email="knowledge-doc-category@example.com",
    )
    headers = {"Authorization": f"Bearer {token}"}

    presale_res = client.post(
        f"/api/tenants/{tenant['id']}/knowledge-documents",
        headers=headers,
        json={
            "title": "售前套餐资料",
            "source_type": "manual_document",
            "category": "售前",
            "raw_text": "基础套餐包含网站咨询接入和智能客服接待。",
            "status": "active",
            "chunk_size": 120,
        },
    )
    after_sales_res = client.post(
        f"/api/tenants/{tenant['id']}/knowledge-documents",
        headers=headers,
        json={
            "title": "售后退款资料",
            "source_type": "manual_document",
            "category": "售后",
            "raw_text": "退款需要核对订单号、付款时间和商品状态。",
            "status": "active",
            "chunk_size": 120,
        },
    )
    assert presale_res.status_code == 201
    assert after_sales_res.status_code == 201
    presale = presale_res.json()
    after_sales = after_sales_res.json()

    category_search = client.post(
        f"/api/tenants/{tenant['id']}/knowledge-document-searches",
        headers=headers,
        json={"query": "退款要核对什么", "category": "售后", "top_k": 5},
    )
    assert category_search.status_code == 200
    assert {match["document_id"] for match in category_search.json()["matches"]} == {after_sales["id"]}

    disabled_res = client.patch(
        f"/api/knowledge-documents/{after_sales['id']}",
        headers=headers,
        json={"status": "draft"},
    )
    assert disabled_res.status_code == 200
    assert disabled_res.json()["status"] == "draft"

    disabled_search = client.post(
        f"/api/tenants/{tenant['id']}/knowledge-document-searches",
        headers=headers,
        json={"query": "退款要核对什么", "category": "售后", "top_k": 5},
    )
    assert disabled_search.status_code == 200
    assert disabled_search.json()["matches"] == []

    delete_res = client.delete(f"/api/knowledge-documents/{presale['id']}", headers=headers)
    assert delete_res.status_code == 200
    assert delete_res.json()["id"] == presale["id"]

    list_res = client.get(f"/api/tenants/{tenant['id']}/knowledge-documents", headers=headers)
    assert list_res.status_code == 200
    assert presale["id"] not in {item["id"] for item in list_res.json()["items"]}
    chunks_res = client.get(f"/api/knowledge-documents/{presale['id']}/chunks", headers=headers)
    assert chunks_res.status_code == 404


def test_document_title_question_and_edited_answer_are_searchable(client) -> None:
    tenant, _, token = _bootstrap_user(
        client,
        slug="knowledge-doc-question-edit",
        email="knowledge-doc-question-edit@example.com",
    )
    headers = {"Authorization": f"Bearer {token}"}

    document_res = client.post(
        f"/api/tenants/{tenant['id']}/knowledge-documents",
        headers=headers,
        json={
            "title": "标准版价格是多少",
            "source_type": "manual_document",
            "category": "售前",
            "raw_text": "标准版每月 299 元，包含网站在线咨询和智能客服接待。",
            "status": "active",
            "chunk_size": 120,
        },
    )
    assert document_res.status_code == 201
    document = document_res.json()
    assert document["raw_text"].startswith("标准版每月")

    title_search = client.post(
        f"/api/tenants/{tenant['id']}/knowledge-document-searches",
        headers=headers,
        json={"query": "价格", "category": "售前", "top_k": 5},
    )
    assert title_search.status_code == 200
    assert title_search.json()["matches"]
    assert title_search.json()["matches"][0]["document_id"] == document["id"]

    update_res = client.patch(
        f"/api/knowledge-documents/{document['id']}",
        headers=headers,
        json={
            "title": "标准版价格是多少",
            "category": "售前",
            "raw_text": "标准版调整为每月 399 元，包含网站在线咨询、智能客服接待和转人工记录。",
        },
    )
    assert update_res.status_code == 200
    assert "399" in update_res.json()["raw_text"]

    edited_search = client.post(
        f"/api/tenants/{tenant['id']}/knowledge-document-searches",
        headers=headers,
        json={"query": "399", "category": "售前", "top_k": 5},
    )
    assert edited_search.status_code == 200
    assert edited_search.json()["matches"][0]["document_id"] == document["id"]
    assert "399" in edited_search.json()["matches"][0]["content_preview"]


def test_customer_service_synonym_query_generates_final_answer_from_right_document(client) -> None:
    tenant, _, token = _bootstrap_user(
        client,
        slug="knowledge-doc-business-hours",
        email="knowledge-doc-business-hours@example.com",
    )
    headers = {"Authorization": f"Bearer {token}"}

    bluetooth_res = client.post(
        f"/api/tenants/{tenant['id']}/knowledge-documents",
        headers=headers,
        json={
            "title": "配对之后蓝牙还是连接不上，且蓝牙闪烁蓝灯",
            "source_type": "manual_document",
            "raw_text": "让门店配对的时候把设备离蓝牙弄得更近些，还是不行的话按设备顶部音量键。",
            "status": "active",
            "chunk_size": 120,
        },
    )
    assert bluetooth_res.status_code == 201
    hours_res = client.post(
        f"/api/tenants/{tenant['id']}/knowledge-documents",
        headers=headers,
        json={
            "title": "营业时间",
            "source_type": "manual_document",
            "raw_text": "营业时间是 9:00-18:00。客服在这个时间段内接待客户咨询。",
            "status": "active",
            "chunk_size": 120,
        },
    )
    assert hours_res.status_code == 201
    hours = hours_res.json()

    search_res = client.post(
        f"/api/tenants/{tenant['id']}/knowledge-document-searches",
        headers=headers,
        json={"query": "你们什么时候上班", "top_k": 3},
    )

    assert search_res.status_code == 200
    search = search_res.json()
    assert search["matches"]
    assert search["matches"][0]["document_id"] == hours["id"]
    assert "9:00" in search["final_answer"]
    assert "18:00" in search["final_answer"]
    assert "蓝牙" not in search["final_answer"]


def test_customer_service_search_returns_safe_answer_when_no_knowledge_hit(client) -> None:
    tenant, _, token = _bootstrap_user(
        client,
        slug="knowledge-doc-no-hit-safe-answer",
        email="knowledge-doc-no-hit-safe-answer@example.com",
    )
    headers = {"Authorization": f"Bearer {token}"}

    search_res = client.post(
        f"/api/tenants/{tenant['id']}/knowledge-document-searches",
        headers=headers,
        json={"query": "你们支持火星基地专属套餐吗", "top_k": 3},
    )

    assert search_res.status_code == 200
    search = search_res.json()
    assert search["matches"] == []
    assert search["final_answer_status"] == "safe_no_knowledge_response"
    assert "关于您提到的“你们支持火星基地专属套餐吗”" in search["final_answer"]
    assert "当前的知识库中暂时还没有收录相关信息" in search["final_answer"]
    assert "避免给您错误引导" in search["final_answer"]
    assert search["knowledge_gap_required"] is True
    assert search["final_answer_citations"] == []


def test_agent_can_search_documents_but_cannot_import_them(client) -> None:
    tenant, _, owner_token = _bootstrap_user(
        client,
        slug="knowledge-doc-agent",
        email="knowledge-doc-agent-owner@example.com",
        role_code="owner",
    )
    owner_headers = {"Authorization": f"Bearer {owner_token}"}
    agent_role = client.post(
        f"/api/tenants/{tenant['id']}/roles",
        headers=owner_headers,
        json={"code": "agent", "name": "客服坐席"},
    ).json()
    agent = client.post(
        f"/api/tenants/{tenant['id']}/users",
        headers=owner_headers,
        json={"name": "客服坐席", "email": "knowledge-doc-agent@example.com", "password": "ChangeMe123!"},
    ).json()
    client.post(f"/api/users/{agent['id']}/roles", headers=owner_headers, json={"role_id": agent_role["id"]})
    login = client.post(
        "/api/auth/login",
        json={
            "tenant_slug": tenant["slug"],
            "email": "knowledge-doc-agent@example.com",
            "password": "ChangeMe123!",
        },
    ).json()
    agent_headers = {"Authorization": f"Bearer {login['access_token']}"}

    create_res = client.post(
        f"/api/tenants/{tenant['id']}/knowledge-documents",
        headers=owner_headers,
        json={
            "title": "保修政策手册",
            "source_type": "manual_document",
            "raw_text": DOCUMENT_TEXT,
            "status": "active",
            "chunk_size": 120,
        },
    )
    assert create_res.status_code == 201

    forbidden_res = client.post(
        f"/api/tenants/{tenant['id']}/knowledge-documents",
        headers=agent_headers,
        json={
            "title": "坐席不能导入",
            "source_type": "manual_document",
            "raw_text": "坐席不能直接导入正式文档。",
        },
    )
    assert forbidden_res.status_code == 403

    search_res = client.post(
        f"/api/tenants/{tenant['id']}/knowledge-document-searches",
        headers=agent_headers,
        json={"query": "保修期多久", "top_k": 5},
    )
    assert search_res.status_code == 200
    assert search_res.json()["matches"][0]["document_title"] == "保修政策手册"


def test_document_embedding_index_records_provider_vector_store_and_reranker(client) -> None:
    tenant, _, token = _bootstrap_user(
        client,
        slug="knowledge-doc-embedding",
        email="knowledge-doc-embedding@example.com",
    )
    headers = {"Authorization": f"Bearer {token}"}

    document_res = client.post(
        f"/api/tenants/{tenant['id']}/knowledge-documents",
        headers=headers,
        json={
            "title": "会员积分规则",
            "source_type": "manual_document",
            "source_uri": "internal://docs/member-points-v1",
            "raw_text": "会员积分可用于兑换优惠券。积分过期时间以会员等级和活动规则为准。",
            "status": "active",
            "chunk_size": 120,
        },
    )
    assert document_res.status_code == 201
    document = document_res.json()

    chunks_res = client.get(f"/api/knowledge-documents/{document['id']}/chunks", headers=headers)
    assert chunks_res.status_code == 200
    chunk = chunks_res.json()[0]
    assert chunk["embedding_provider"] == "deterministic_local"
    assert chunk["embedding_model"] == "deterministic-token-vector-v1"
    assert chunk["embedding_dimension"] > 0
    assert chunk["vector_store"] == "sqlite_json_vector_store"
    assert chunk["vector_index_status"] == "indexed"
    assert chunk["embedding_signature"]["engine"] == "deterministic_local_hash_embedding_v1"

    search_res = client.post(
        f"/api/tenants/{tenant['id']}/knowledge-document-searches",
        headers=headers,
        json={"query": "积分可以兑换什么", "top_k": 3},
    )
    assert search_res.status_code == 200
    search = search_res.json()
    assert search["retrieval_mode"] == "hybrid_bm25_vector_rerank_v1"
    assert search["vector_engine"] == "deterministic_local_hash_embedding_v1"
    assert search["vector_store"] == "sqlite_json_vector_store"
    assert search["embedding_provider"] == "deterministic_local"
    assert search["embedding_model"] == "deterministic-token-vector-v1"
    assert search["reranker"] == "lexical_overlap_reranker_v1"
    assert search["matches"][0]["vector_score"] > 0


def test_explicit_external_embedding_provider_missing_key_rejects_import(client, monkeypatch) -> None:
    monkeypatch.setenv("KNOWLEDGE_EMBEDDING_PROVIDER", "openai_compatible")
    monkeypatch.setenv("KNOWLEDGE_EMBEDDING_API_KEY", "")
    tenant, _, token = _bootstrap_user(
        client,
        slug="knowledge-doc-embedding-missing-key",
        email="knowledge-doc-embedding-missing-key@example.com",
    )
    headers = {"Authorization": f"Bearer {token}"}

    document_res = client.post(
        f"/api/tenants/{tenant['id']}/knowledge-documents",
        headers=headers,
        json={
            "title": "需要真实 embedding 的文档",
            "source_type": "manual_document",
            "raw_text": "显式配置外部 embedding provider 时，缺少 key 不能静默 fallback。",
            "status": "active",
        },
    )
    assert document_res.status_code == 503
    assert "embedding provider" in document_res.json()["detail"]
