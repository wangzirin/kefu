from test_knowledge_api import _bootstrap_user
from test_knowledge_documents_api import DOCUMENT_TEXT

from app.services.knowledge import _build_pgvector_ann_index_plan


def test_owner_can_create_json_vector_index_strategy_plan(client) -> None:
    tenant, _, token = _bootstrap_user(
        client,
        slug="knowledge-vector-plan",
        email="knowledge-vector-plan@example.com",
    )
    headers = {"Authorization": f"Bearer {token}"}

    document_res = client.post(
        f"/api/tenants/{tenant['id']}/knowledge-documents",
        headers=headers,
        json={
            "title": "索引策略测试文档",
            "source_type": "manual_document",
            "source_uri": "internal://docs/vector-plan",
            "raw_text": DOCUMENT_TEXT,
            "status": "active",
            "chunk_size": 90,
            "chunk_overlap": 10,
        },
    )
    assert document_res.status_code == 201
    document = document_res.json()

    plan_res = client.post(
        f"/api/tenants/{tenant['id']}/knowledge-vector-index/plans",
        headers=headers,
        json={"status": "active", "document_id": document["id"], "requested_strategy": "auto"},
    )
    assert plan_res.status_code == 201
    plan = plan_res.json()
    assert plan["tenant_id"] == tenant["id"]
    assert plan["document_id"] == document["id"]
    assert plan["plan_status"] == "planned"
    assert plan["selected_strategy"] == "python_json_exact_scan"
    assert plan["index_method"] == "none"
    assert plan["vector_store"] == "sqlite_json_vector_store"
    assert plan["retrieval_backend"] == "python_json_vector_scan"
    assert plan["target_chunk_count"] == document["chunk_count"]
    assert plan["dry_run"] is True
    assert plan["execute_performed"] is False
    assert plan["ddl_statements"] == []
    assert plan["rollback_statements"] == []
    assert plan["safety_checks"]["external_execution_performed"] is False


def test_agent_cannot_create_vector_index_strategy_plan(client) -> None:
    tenant, _, owner_token = _bootstrap_user(
        client,
        slug="knowledge-vector-plan-agent",
        email="knowledge-vector-plan-agent-owner@example.com",
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
        json={"name": "客服坐席", "email": "knowledge-vector-plan-agent@example.com", "password": "ChangeMe123!"},
    ).json()
    client.post(f"/api/users/{agent['id']}/roles", headers=owner_headers, json={"role_id": agent_role["id"]})
    login = client.post(
        "/api/auth/login",
        json={
            "tenant_slug": tenant["slug"],
            "email": "knowledge-vector-plan-agent@example.com",
            "password": "ChangeMe123!",
        },
    ).json()

    forbidden_res = client.post(
        f"/api/tenants/{tenant['id']}/knowledge-vector-index/plans",
        headers={"Authorization": f"Bearer {login['access_token']}"},
        json={"status": "active", "requested_strategy": "auto"},
    )
    assert forbidden_res.status_code == 403


def test_pgvector_plan_blocks_non_postgresql_without_executing(client, monkeypatch) -> None:
    monkeypatch.setenv("KNOWLEDGE_VECTOR_STORE", "postgres_pgvector_store_v1")
    tenant, _, token = _bootstrap_user(
        client,
        slug="knowledge-vector-plan-blocked",
        email="knowledge-vector-plan-blocked@example.com",
    )
    headers = {"Authorization": f"Bearer {token}"}

    plan_res = client.post(
        f"/api/tenants/{tenant['id']}/knowledge-vector-index/plans",
        headers=headers,
        json={"status": "active", "requested_strategy": "hnsw"},
    )
    assert plan_res.status_code == 201
    plan = plan_res.json()
    assert plan["plan_status"] == "blocked"
    assert plan["selected_strategy"] == "blocked_non_postgresql"
    assert plan["vector_store"] == "postgres_pgvector_store_v1"
    assert plan["dry_run"] is True
    assert plan["execute_performed"] is False
    assert plan["ddl_statements"] == []
    assert "requires PostgreSQL" in " ".join(plan["recommendation_reasons"])


def test_pgvector_ann_index_plan_uses_expression_partial_indexes_and_rollback() -> None:
    hnsw = _build_pgvector_ann_index_plan(
        index_method="hnsw",
        target_chunk_count=50_000,
        embedding_provider="deterministic_local",
        embedding_model="deterministic-token-vector-v1",
        embedding_dimension=64,
        concurrent_build=True,
    )
    hnsw_sql = "\n".join(hnsw["ddl_statements"])
    assert "CREATE INDEX CONCURRENTLY IF NOT EXISTS" in hnsw_sql
    assert "USING hnsw" in hnsw_sql
    assert "(embedding_pgvector::vector(64)) vector_cosine_ops" in hnsw_sql
    assert "embedding_provider = 'deterministic_local'" in hnsw_sql
    assert "embedding_model = 'deterministic-token-vector-v1'" in hnsw_sql
    assert "embedding_dimension = 64" in hnsw_sql
    assert "WITH (m = 16, ef_construction = 64)" in hnsw_sql
    assert hnsw["query_options"]["hnsw.ef_search"] == 100
    assert hnsw["rollback_statements"] == [f"DROP INDEX CONCURRENTLY IF EXISTS {hnsw['index_name']};"]

    ivfflat = _build_pgvector_ann_index_plan(
        index_method="ivfflat",
        target_chunk_count=2_000_000,
        embedding_provider="bailian_dashscope",
        embedding_model="text-embedding-v4",
        embedding_dimension=1536,
        concurrent_build=True,
    )
    ivf_sql = "\n".join(ivfflat["ddl_statements"])
    assert "USING ivfflat" in ivf_sql
    assert "(embedding_pgvector::vector(1536)) vector_cosine_ops" in ivf_sql
    assert "WITH (lists = 1414)" in ivf_sql
    assert ivfflat["query_options"]["ivfflat.probes"] == 38
