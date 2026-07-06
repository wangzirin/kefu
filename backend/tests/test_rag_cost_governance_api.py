from app.models import ModelCallRecord, utc_now

from test_knowledge_api import _bootstrap_user
from test_knowledge_documents_api import DOCUMENT_TEXT


def test_owner_can_read_rag_cost_governance_summary_without_external_calls(client) -> None:
    tenant, _, token = _bootstrap_user(
        client,
        slug="rag-cost-governance-owner",
        email="rag-cost-governance-owner@example.com",
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
            "tags": ["售后", "保修"],
            "status": "active",
            "chunk_size": 90,
            "chunk_overlap": 10,
        },
    )
    assert document_res.status_code == 201

    smoke_res = client.post(
        f"/api/tenants/{tenant['id']}/knowledge-embedding-provider-smoke-runs",
        headers=headers,
        json={"sample_text": "H2W7 治理摘要只记录 hash、token、耗时和成本估算。"},
    )
    assert smoke_res.status_code == 201

    set_res = client.post(
        f"/api/tenants/{tenant['id']}/knowledge-evaluation-sets",
        headers=headers,
        json={
            "name": "H2W7 受控题集",
            "description": "小题集只用于治理摘要 smoke，不代表完整商用准确率。",
            "status": "active",
            "evaluation_mode": "customer_service_retrieval",
            "cases": [
                {
                    "question": "标准产品保修期多久",
                    "expected_terms": ["三年", "保修"],
                    "expected_source_uri": "internal://docs/after-sales-v1",
                    "required_citation": True,
                },
                {
                    "question": "超过七天退货需要核对什么",
                    "expected_terms": ["订单时间", "商品状态"],
                    "expected_source_uri": "internal://docs/after-sales-v1",
                    "required_citation": True,
                },
            ],
        },
    )
    assert set_res.status_code == 201
    evaluation_set = set_res.json()
    run_res = client.post(
        f"/api/knowledge-evaluation-sets/{evaluation_set['id']}/runs",
        headers=headers,
        json={"top_k": 3, "low_confidence_threshold": 0.2},
    )
    assert run_res.status_code == 201
    run = run_res.json()
    first_case_id = run["case_results"][0]["id"]
    second_case_id = run["case_results"][1]["id"]
    first_sample_res = client.patch(
        f"/api/knowledge-evaluation-run-cases/{first_case_id}/final-answer-sample",
        headers=headers,
        json={
            "final_answer_text": "标准产品保修期为三年，具体以售后政策手册为准。",
            "citation_uris": ["internal://docs/after-sales-v1"],
            "answer_author": "本地客服工作台",
        },
    )
    assert first_sample_res.status_code == 200
    second_sample_res = client.patch(
        f"/api/knowledge-evaluation-run-cases/{second_case_id}/final-answer-sample",
        headers=headers,
        json={
            "final_answer_text": "超过七天退货时，需要先核对订单时间、商品状态和售后规则。",
            "citation_uris": ["internal://docs/after-sales-v1"],
            "answer_author": "本地客服工作台",
        },
    )
    assert second_sample_res.status_code == 200
    label_res = client.patch(
        f"/api/knowledge-evaluation-runs/{run['id']}/factuality-labels/batch",
        headers=headers,
        json={
            "labels": [
                {
                    "evaluation_run_case_id": first_case_id,
                    "final_answer_factuality_status": "correct",
                    "citation_sufficient": True,
                    "forbidden_commitment_passed": True,
                    "handoff_correct": True,
                },
                {
                    "evaluation_run_case_id": second_case_id,
                    "final_answer_factuality_status": "correct",
                    "citation_sufficient": True,
                    "forbidden_commitment_passed": True,
                    "handoff_correct": True,
                },
            ]
        },
    )
    assert label_res.status_code == 200

    summary_res = client.get(
        f"/api/tenants/{tenant['id']}/rag-cost-governance-summary",
        headers=headers,
    )

    assert summary_res.status_code == 200
    summary = summary_res.json()
    assert summary["schema_version"] == "p3-06u-26h2w7.rag_cost_governance_summary.v1"
    assert summary["tenant_id"] == tenant["id"]
    assert summary["maturity_status"] == "candidate"
    assert summary["safety"]["model_call_performed"] is False
    assert summary["safety"]["external_write_performed"] is False
    assert summary["vector_profile"]["indexed_chunk_count"] > 0
    assert summary["latest_evaluation"]["run_id"] == run["id"]
    assert summary["latest_provider_smoke"]["run_id"] == smoke_res.json()["id"]
    assert summary["answer_quality"]["latest_evaluation_run_id"] == run["id"]
    assert summary["answer_quality"]["final_answer_sampled_cases"] == 2
    assert summary["answer_quality"]["final_answer_sample_coverage"] == 1
    assert summary["answer_quality"]["final_answer_factuality_labeled_cases"] == 2
    assert summary["answer_quality"]["final_answer_factuality_rate"] == 1
    assert summary["answer_quality"]["citation_snapshot_count"] == 2
    assert summary["answer_quality"]["complete_accuracy_measured"] is True
    assert summary["production_readiness"]["status"] == "blocked"
    assert summary["production_readiness"]["production_switch_allowed"] is False
    assert summary["production_readiness"]["pgvector_runtime_ready"] is False
    assert summary["production_readiness"]["real_customer_material_ready"] is False
    assert summary["production_readiness"]["customer_material_batch_status"] == "not_submitted"
    assert summary["production_readiness"]["customer_material_question_count"] == 0
    assert summary["production_readiness"]["customer_question_bank_ready"] is False
    assert summary["production_readiness"]["final_answer_quality_ready"] is False
    assert summary["production_readiness"]["embedding_cost_record_ready"] is True
    assert summary["production_readiness"]["model_cost_record_ready"] is False
    assert summary["production_readiness"]["safety"]["production_retrieval_path_switched"] is False
    assert summary["production_readiness"]["safety"]["internal_sample_unlocks_production_retrieval"] is False
    assert any("真实客户资料" in blocker for blocker in summary["production_readiness"]["blockers"])
    assert "production_retrieval_switch" in summary["production_readiness"]["not_ready_for"]
    gates = {gate["code"]: gate for gate in summary["gates"]}
    assert gates["knowledge_base_ready"]["status"] == "passed"
    assert gates["retrieval_evaluation"]["status"] == "passed"
    assert gates["final_answer_quality"]["status"] == "passed"
    assert gates["customer_question_bank"]["status"] == "warning"
    assert gates["model_call_cost_governance"]["status"] == "blocked"
    assert gates["model_budget_policy"]["status"] == "passed"
    assert summary["model_policy"]["recent_model_call_record_count"] == 0
    assert summary["model_policy"]["cost_source"] == "not_recorded_yet"
    assert summary["model_policy"]["budget_guard_enabled"] is True
    assert summary["model_policy"]["single_call_budget_limit"] == 0
    assert summary["model_policy"]["pricing_source"] == "operator_config_default_estimate_not_provider_bill"
    assert summary["model_policy"]["pricing_version"] == "local-estimate-2026-07"


def test_rag_cost_governance_reads_persistent_model_call_records(client, db_session) -> None:
    tenant, _, token = _bootstrap_user(
        client,
        slug="rag-cost-governance-model-record",
        email="rag-cost-governance-model-record@example.com",
    )
    headers = {"Authorization": f"Bearer {token}"}
    db_session.add(
        ModelCallRecord(
            tenant_id=tenant["id"],
            provenance_id="rp_cost_governance_example",
            idempotency_key="rag-cost-governance-model-record:v1",
            provider="bailian",
            model="qwen-plus",
            route_name="standard_support",
            target_model_tier="standard",
            complexity="standard",
            status="succeeded",
            input_units=800,
            output_units=220,
            total_units=1020,
            unit_type="tokens",
            estimated_cost=0.0123,
            currency="CNY",
            pricing_source="operator_price_table_2026_07",
            pricing_version="2026-07",
            raw_text_logged=False,
            created_at=utc_now(),
        )
    )
    db_session.commit()

    summary_res = client.get(
        f"/api/tenants/{tenant['id']}/rag-cost-governance-summary",
        headers=headers,
    )

    assert summary_res.status_code == 200
    summary = summary_res.json()
    gates = {gate["code"]: gate for gate in summary["gates"]}
    assert gates["model_call_cost_governance"]["status"] == "passed"
    assert summary["model_policy"]["recent_model_call_record_count"] == 1
    assert summary["model_policy"]["estimated_model_cost"] == 0.0123
    assert summary["model_policy"]["cost_source"] == "model_call_records"
    assert summary["production_readiness"]["model_cost_record_ready"] is True
    assert summary["production_readiness"]["real_customer_material_ready"] is False


def test_agent_cannot_read_rag_cost_governance_summary(client) -> None:
    tenant, _, owner_token = _bootstrap_user(
        client,
        slug="rag-cost-governance-agent",
        email="rag-cost-governance-agent-owner@example.com",
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
        json={"name": "客服坐席", "email": "rag-cost-governance-agent@example.com", "password": "ChangeMe123!"},
    ).json()
    client.post(f"/api/users/{agent['id']}/roles", headers=owner_headers, json={"role_id": agent_role["id"]})
    login = client.post(
        "/api/auth/login",
        json={
            "tenant_slug": tenant["slug"],
            "email": "rag-cost-governance-agent@example.com",
            "password": "ChangeMe123!",
        },
    ).json()

    forbidden_res = client.get(
        f"/api/tenants/{tenant['id']}/rag-cost-governance-summary",
        headers={"Authorization": f"Bearer {login['access_token']}"},
    )

    assert forbidden_res.status_code == 403
