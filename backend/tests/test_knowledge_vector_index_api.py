from test_knowledge_api import _bootstrap_user
from test_knowledge_documents_api import DOCUMENT_TEXT

from app.services.knowledge import _build_pgvector_candidate_sql


def test_owner_can_rebuild_knowledge_vector_index(client) -> None:
    tenant, _, token = _bootstrap_user(
        client,
        slug="knowledge-vector-rebuild",
        email="knowledge-vector-rebuild@example.com",
    )
    headers = {"Authorization": f"Bearer {token}"}

    document_res = client.post(
        f"/api/tenants/{tenant['id']}/knowledge-documents",
        headers=headers,
        json={
            "title": "售后政策手册",
            "source_type": "manual_document",
            "source_uri": "internal://docs/after-sales-v1",
            "raw_text": DOCUMENT_TEXT,
            "status": "active",
            "chunk_size": 90,
            "chunk_overlap": 10,
        },
    )
    assert document_res.status_code == 201
    document = document_res.json()

    rebuild_res = client.post(
        f"/api/tenants/{tenant['id']}/knowledge-vector-index/rebuilds",
        headers=headers,
        json={"status": "active", "document_id": document["id"]},
    )
    assert rebuild_res.status_code == 201
    rebuild = rebuild_res.json()
    assert rebuild["tenant_id"] == tenant["id"]
    assert rebuild["document_id"] == document["id"]
    assert rebuild["vector_store"] == "sqlite_json_vector_store"
    assert rebuild["retrieval_backend"] == "python_json_vector_scan"
    assert rebuild["embedding_provider"] == "deterministic_local"
    assert rebuild["embedding_model"] == "deterministic-token-vector-v1"
    assert rebuild["vector_index_status"] == "indexed"
    assert rebuild["total_chunks"] == document["chunk_count"]
    assert rebuild["reindexed_chunks"] == document["chunk_count"]
    assert rebuild["failed_chunks"] == 0

    chunks_res = client.get(f"/api/knowledge-documents/{document['id']}/chunks", headers=headers)
    assert chunks_res.status_code == 200
    assert {chunk["vector_index_status"] for chunk in chunks_res.json()} == {"indexed"}


def test_agent_cannot_rebuild_knowledge_vector_index(client) -> None:
    tenant, _, owner_token = _bootstrap_user(
        client,
        slug="knowledge-vector-agent",
        email="knowledge-vector-agent-owner@example.com",
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
        json={"name": "客服坐席", "email": "knowledge-vector-agent@example.com", "password": "ChangeMe123!"},
    ).json()
    client.post(f"/api/users/{agent['id']}/roles", headers=owner_headers, json={"role_id": agent_role["id"]})
    login = client.post(
        "/api/auth/login",
        json={
            "tenant_slug": tenant["slug"],
            "email": "knowledge-vector-agent@example.com",
            "password": "ChangeMe123!",
        },
    ).json()

    forbidden_res = client.post(
        f"/api/tenants/{tenant['id']}/knowledge-vector-index/rebuilds",
        headers={"Authorization": f"Bearer {login['access_token']}"},
        json={"status": "active"},
    )
    assert forbidden_res.status_code == 403


def test_explicit_pgvector_store_requires_postgresql_without_silent_fallback(client, monkeypatch) -> None:
    monkeypatch.setenv("KNOWLEDGE_VECTOR_STORE", "postgres_pgvector_store_v1")
    tenant, _, token = _bootstrap_user(
        client,
        slug="knowledge-pgvector-nonpostgres",
        email="knowledge-pgvector-nonpostgres@example.com",
    )
    headers = {"Authorization": f"Bearer {token}"}

    document_res = client.post(
        f"/api/tenants/{tenant['id']}/knowledge-documents",
        headers=headers,
        json={
            "title": "显式 pgvector 文档",
            "source_type": "manual_document",
            "source_uri": "internal://docs/pgvector-required",
            "raw_text": "显式配置 pgvector 时，非 PostgreSQL 环境不能静默 fallback 到 JSON vector。",
            "status": "active",
        },
    )
    assert document_res.status_code == 503
    assert "pgvector" in document_res.json()["detail"]

    rebuild_res = client.post(
        f"/api/tenants/{tenant['id']}/knowledge-vector-index/rebuilds",
        headers=headers,
        json={"status": "active"},
    )
    assert rebuild_res.status_code == 503
    assert "pgvector" in rebuild_res.json()["detail"]


def test_pgvector_candidate_sql_filters_scope_before_similarity() -> None:
    sql = _build_pgvector_candidate_sql()
    assert "knowledge_document_chunks" in sql
    assert "knowledge_documents" in sql
    assert "c.tenant_id = :tenant_id" in sql
    assert "c.status = :status" in sql
    assert "d.status = :status" in sql
    assert "c.embedding_provider = :embedding_provider" in sql
    assert "c.embedding_model = :embedding_model" in sql
    assert "c.embedding_dimension = :embedding_dimension" in sql
    assert "<=> CAST(:query_vector AS vector)" in sql
