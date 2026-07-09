import json

from app.services import knowledge as knowledge_service
from test_knowledge_api import _bootstrap_user


def test_owner_can_run_deterministic_embedding_provider_smoke(client) -> None:
    tenant, _, token = _bootstrap_user(
        client,
        slug="knowledge-embedding-smoke",
        email="knowledge-embedding-smoke@example.com",
    )
    headers = {"Authorization": f"Bearer {token}"}

    smoke_res = client.post(
        f"/api/tenants/{tenant['id']}/knowledge-embedding-provider-smoke-runs",
        headers=headers,
        json={"sample_text": "这是一段公开的知识库 embedding smoke 测试文本。"},
    )

    assert smoke_res.status_code == 201
    smoke = smoke_res.json()
    assert smoke["tenant_id"] == tenant["id"]
    assert smoke["status"] == "succeeded"
    assert smoke["embedding_provider"] == "deterministic_local"
    assert smoke["embedding_model"] == "deterministic-token-vector-v1"
    assert smoke["vector_engine"] == "deterministic_local_hash_embedding_v1"
    assert smoke["output_dimension"] > 0
    assert smoke["input_character_count"] > 0
    assert smoke["estimated_input_tokens"] > 0
    assert smoke["latency_ms"] >= 0
    assert smoke["estimated_cost"] == 0
    assert smoke["raw_text_logged"] is False
    assert smoke["input_text_hash"]
    assert "测试文本" not in json.dumps(smoke, ensure_ascii=False)
    assert smoke["quality_checks"]["dimension_positive"] is True
    assert smoke["quality_checks"]["vector_norm_nonzero"] is True


def test_agent_cannot_run_embedding_provider_smoke(client) -> None:
    tenant, _, owner_token = _bootstrap_user(
        client,
        slug="knowledge-embedding-smoke-agent",
        email="knowledge-embedding-smoke-agent-owner@example.com",
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
        json={"name": "客服坐席", "email": "knowledge-embedding-smoke-agent@example.com", "password": "ChangeMe123!"},
    ).json()
    client.post(f"/api/users/{agent['id']}/roles", headers=owner_headers, json={"role_id": agent_role["id"]})
    login = client.post(
        "/api/auth/login",
        json={
            "tenant_slug": tenant["slug"],
            "email": "knowledge-embedding-smoke-agent@example.com",
            "password": "ChangeMe123!",
        },
    ).json()

    forbidden_res = client.post(
        f"/api/tenants/{tenant['id']}/knowledge-embedding-provider-smoke-runs",
        headers={"Authorization": f"Bearer {login['access_token']}"},
        json={"sample_text": "坐席不能触发 provider smoke。"},
    )
    assert forbidden_res.status_code == 403


def test_external_embedding_provider_smoke_requires_explicit_allow(client, monkeypatch) -> None:
    monkeypatch.setenv("KNOWLEDGE_EMBEDDING_PROVIDER", "openai_compatible")
    monkeypatch.setenv("KNOWLEDGE_EMBEDDING_API_BASE", "https://provider.example/v1")
    monkeypatch.setenv("KNOWLEDGE_EMBEDDING_API_KEY", "test-key-not-real")
    tenant, _, token = _bootstrap_user(
        client,
        slug="knowledge-embedding-smoke-external-blocked",
        email="knowledge-embedding-smoke-external-blocked@example.com",
    )
    headers = {"Authorization": f"Bearer {token}"}

    smoke_res = client.post(
        f"/api/tenants/{tenant['id']}/knowledge-embedding-provider-smoke-runs",
        headers=headers,
        json={"sample_text": "外部 provider smoke 必须显式允许。"},
    )

    assert smoke_res.status_code == 409
    assert "allow_external_call" in smoke_res.json()["detail"]


def test_openai_compatible_embedding_provider_smoke_records_cost_latency_without_raw_text(
    client,
    monkeypatch,
) -> None:
    monkeypatch.setenv("KNOWLEDGE_EMBEDDING_PROVIDER", "openai_compatible")
    monkeypatch.setenv("KNOWLEDGE_EMBEDDING_API_BASE", "https://provider.example/v1")
    monkeypatch.setenv("KNOWLEDGE_EMBEDDING_API_KEY", "test-key-not-real")
    monkeypatch.setenv("KNOWLEDGE_EMBEDDING_MODEL", "test-embedding-model")
    monkeypatch.setenv("KNOWLEDGE_EMBEDDING_PRICE_PER_1K_TOKENS", "0.02")
    monkeypatch.setenv("KNOWLEDGE_EMBEDDING_COST_CURRENCY", "CNY")

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self) -> bytes:
            return json.dumps(
                {
                    "data": [{"embedding": [0.1, 0.2, 0.3, 0.4]}],
                    "usage": {"prompt_tokens": 12, "total_tokens": 12},
                }
            ).encode("utf-8")

    calls: list[dict] = []

    def fake_urlopen(request, timeout):
        calls.append({"url": request.full_url, "timeout": timeout})
        return FakeResponse()

    monkeypatch.setattr("app.services.knowledge.urlopen", fake_urlopen)
    tenant, _, token = _bootstrap_user(
        client,
        slug="knowledge-embedding-smoke-openai-compatible",
        email="knowledge-embedding-smoke-openai-compatible@example.com",
    )
    headers = {"Authorization": f"Bearer {token}"}

    smoke_res = client.post(
        f"/api/tenants/{tenant['id']}/knowledge-embedding-provider-smoke-runs",
        headers=headers,
        json={
            "sample_text": "真实 provider smoke 只记录 hash、耗时、token 与成本估算，不保存原文。",
            "allow_external_call": True,
        },
    )

    assert smoke_res.status_code == 201
    smoke = smoke_res.json()
    assert calls == [{"url": "https://provider.example/v1/embeddings", "timeout": 20.0}]
    assert smoke["status"] == "succeeded"
    assert smoke["embedding_provider"] == "openai_compatible"
    assert smoke["embedding_model"] == "test-embedding-model"
    assert smoke["output_dimension"] == 4
    assert smoke["estimated_input_tokens"] == 12
    assert smoke["pricing_input_per_1k_tokens"] == 0.02
    assert smoke["cost_currency"] == "CNY"
    assert smoke["estimated_cost"] == 0.00024
    assert smoke["provider_call_performed"] is True
    assert smoke["raw_text_logged"] is False
    assert "不保存原文" not in json.dumps(smoke, ensure_ascii=False)
    assert smoke["response_metadata"]["usage"]["prompt_tokens"] == 12


def test_local_bge_m3_embedding_provider_smoke_uses_flagembedding_without_raw_text(
    client,
    monkeypatch,
) -> None:
    monkeypatch.setenv("KNOWLEDGE_EMBEDDING_PROVIDER", "local_bge_m3")
    monkeypatch.setenv("KNOWLEDGE_EMBEDDING_MODEL", "BAAI/bge-m3")

    class FakeBgeM3Model:
        def encode(self, texts, **kwargs):
            assert texts == ["BGE-M3 本地开源 embedding smoke。"]
            assert kwargs == {"return_dense": True, "return_sparse": False, "return_colbert_vecs": False}
            return {"dense_vecs": [[0.1, 0.2, 0.3, 0.4]]}

    monkeypatch.setattr(knowledge_service, "_load_bge_m3_model", lambda model_name: FakeBgeM3Model())
    tenant, _, token = _bootstrap_user(
        client,
        slug="knowledge-embedding-smoke-bge-m3",
        email="knowledge-embedding-smoke-bge-m3@example.com",
    )
    headers = {"Authorization": f"Bearer {token}"}

    smoke_res = client.post(
        f"/api/tenants/{tenant['id']}/knowledge-embedding-provider-smoke-runs",
        headers=headers,
        json={"sample_text": "BGE-M3 本地开源 embedding smoke。"},
    )

    assert smoke_res.status_code == 201
    smoke = smoke_res.json()
    assert smoke["status"] == "succeeded"
    assert smoke["embedding_provider"] == "local_bge_m3"
    assert smoke["embedding_model"] == "BAAI/bge-m3"
    assert smoke["vector_engine"] == "flagembedding_bge_m3_dense_v1"
    assert smoke["embedding_dimension"] == 1024
    assert smoke["output_dimension"] == 4
    assert smoke["provider_call_performed"] is False
    assert smoke["raw_text_logged"] is False
    assert "本地开源" not in json.dumps(smoke, ensure_ascii=False)
    assert smoke["response_metadata"]["runtime"] == "FlagEmbedding.BGEM3FlagModel"


def test_local_bge_m3_embedding_provider_smoke_reports_missing_dependency(
    client,
    monkeypatch,
) -> None:
    monkeypatch.setenv("KNOWLEDGE_EMBEDDING_PROVIDER", "local_bge_m3")
    monkeypatch.setattr(
        knowledge_service,
        "_load_bge_m3_model",
        lambda _model_name: (_ for _ in ()).throw(RuntimeError("FlagEmbedding is not installed.")),
    )
    tenant, _, token = _bootstrap_user(
        client,
        slug="knowledge-embedding-smoke-bge-m3-missing",
        email="knowledge-embedding-smoke-bge-m3-missing@example.com",
    )
    headers = {"Authorization": f"Bearer {token}"}

    smoke_res = client.post(
        f"/api/tenants/{tenant['id']}/knowledge-embedding-provider-smoke-runs",
        headers=headers,
        json={"sample_text": "检查缺失依赖时不能保存原文。"},
    )

    assert smoke_res.status_code == 201
    smoke = smoke_res.json()
    assert smoke["status"] == "unavailable"
    assert smoke["embedding_provider"] == "local_bge_m3"
    assert smoke["output_dimension"] == 0
    assert "FlagEmbedding is not installed" in smoke["error_message"]
    assert "不能保存原文" not in json.dumps(smoke, ensure_ascii=False)
