import csv
import base64
import io
import json
import zipfile

from test_knowledge_api import _bootstrap_user
from test_knowledge_documents_api import DOCUMENT_TEXT
from app.models import (
    AuditEvent,
    Channel,
    Contact,
    Conversation,
    HumanReviewTask,
    KnowledgeEvaluationCase,
    KnowledgeEvaluationRun,
    KnowledgeEvaluationRunCase,
    KnowledgeEvaluationSet,
    KnowledgeGapItem,
    Message,
    ModelCallRecord,
    ReplyCitationSnapshot,
    ReplyDecision,
    WorkflowRun,
)
from app.models.foundation import utc_now


def test_owner_can_create_and_run_document_retrieval_evaluation(client) -> None:
    tenant, _, token = _bootstrap_user(
        client,
        slug="knowledge-eval-owner",
        email="knowledge-eval-owner@example.com",
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

    no_token_res = client.post(
        f"/api/tenants/{tenant['id']}/knowledge-evaluation-sets",
        json={
            "name": "售后政策核心题集",
            "status": "active",
            "cases": [{"question": "保修期多久", "expected_terms": ["三年"]}],
        },
    )
    assert no_token_res.status_code == 401

    set_res = client.post(
        f"/api/tenants/{tenant['id']}/knowledge-evaluation-sets",
        headers=headers,
        json={
            "name": "售后政策核心题集",
            "description": "验证文档检索能否命中售后和保修核心知识。",
            "status": "active",
            "cases": [
                {
                    "question": "标准产品保修期多久",
                    "expected_terms": ["三年", "保修"],
                    "expected_source_uri": "internal://docs/after-sales-v1",
                    "required_citation": True,
                },
                {
                    "question": "超过七天退货需要核对什么",
                    "expected_terms": ["订单时间", "商品状态", "质量问题"],
                    "expected_source_uri": "internal://docs/after-sales-v1",
                    "required_citation": True,
                },
            ],
        },
    )
    assert set_res.status_code == 201
    evaluation_set = set_res.json()
    assert evaluation_set["tenant_id"] == tenant["id"]
    assert evaluation_set["name"] == "售后政策核心题集"
    assert evaluation_set["case_count"] == 2
    assert [case["status"] for case in evaluation_set["cases"]] == ["active", "active"]

    run_res = client.post(
        f"/api/knowledge-evaluation-sets/{evaluation_set['id']}/runs",
        headers=headers,
        json={"top_k": 3, "low_confidence_threshold": 0.2},
    )
    assert run_res.status_code == 201
    run = run_res.json()
    assert run["evaluation_set_id"] == evaluation_set["id"]
    assert run["run_mode"] == "document_retrieval"
    assert run["retrieval_mode"] == "hybrid_bm25_vector_rerank_v1"
    assert run["vector_engine"] == "deterministic_local_hash_embedding_v1"
    assert run["summary_payload"]["vector_store"] == "sqlite_json_vector_store"
    assert run["summary_payload"]["reranker"] == "lexical_overlap_reranker_v1"
    assert run["total_cases"] == 2
    assert run["answered_cases"] == 2
    assert run["hit_rate"] == 1
    assert run["citation_coverage"] == 1
    assert run["expected_term_coverage"] >= 0.5
    assert run["average_confidence"] > 0
    assert run["unsupported_answer_rate"] is None
    assert "不生成自由文本答案" in run["summary_payload"]["unsupported_answer_rate_note"]
    assert len(run["case_results"]) == 2
    assert {case["question"] for case in run["case_results"]} == {
        "标准产品保修期多久",
        "超过七天退货需要核对什么",
    }
    assert all(case["citation_present"] for case in run["case_results"])
    assert all(case["top_score"] > 0 for case in run["case_results"])


def test_customer_service_evaluation_tracks_evidence_review_and_safety_metrics(client) -> None:
    tenant, _, token = _bootstrap_user(
        client,
        slug="knowledge-eval-customer-service",
        email="knowledge-eval-customer-service@example.com",
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
    document = document_res.json()
    chunks_res = client.get(f"/api/knowledge-documents/{document['id']}/chunks", headers=headers)
    assert chunks_res.status_code == 200
    chunks = chunks_res.json()
    return_chunk = next(chunk for chunk in chunks if "订单时间" in chunk["content"])
    warranty_chunk = next(chunk for chunk in chunks if "三年" in chunk["content"])

    set_res = client.post(
        f"/api/tenants/{tenant['id']}/knowledge-evaluation-sets",
        headers=headers,
        json={
            "name": "客服商用验收题集",
            "description": "覆盖多证据召回、人工审核预期、禁用承诺词和知识缺口。",
            "status": "active",
            "evaluation_mode": "customer_service_retrieval",
            "cases": [
                {
                    "external_case_id": "cust-eval-001",
                    "source_channel": "wecom",
                    "source_category": "售后政策",
                    "question": "超过七天退货需要核对什么，标准产品保修期多久",
                    "question_type": "multi_evidence_policy",
                    "expected_terms": ["订单时间", "商品状态", "三年"],
                    "expected_source_uri": "internal://docs/after-sales-v1",
                    "expected_document_title": "售后政策手册",
                    "expected_chunk_ids": [return_chunk["id"], warranty_chunk["id"]],
                    "must_have_all_evidence": True,
                    "expected_human_review": False,
                    "allow_auto_reply": True,
                    "forbidden_terms": ["立即赔付"],
                    "risk_level": "medium",
                    "annotation_notes": "公开合成样例，不含真实客户身份。",
                    "required_citation": True,
                },
                {
                    "external_case_id": "cust-eval-002",
                    "source_channel": "wecom",
                    "source_category": "高风险售后",
                    "question": "超过七天退货时客户要求马上赔偿并承诺百分百退款怎么办",
                    "question_type": "risk_handoff",
                    "expected_terms": ["订单时间", "商品状态"],
                    "expected_source_uri": "internal://docs/after-sales-v1",
                    "expected_document_title": "售后政策手册",
                    "expected_chunk_ids": [return_chunk["id"]],
                    "must_have_all_evidence": True,
                    "expected_human_review": True,
                    "allow_auto_reply": False,
                    "forbidden_terms": ["马上赔偿", "百分百退款"],
                    "risk_level": "high",
                    "annotation_notes": "用于验证赔付承诺必须转人工。",
                    "required_citation": True,
                    "priority": 10,
                },
            ],
        },
    )
    assert set_res.status_code == 201
    evaluation_set = set_res.json()
    assert evaluation_set["evaluation_mode"] == "customer_service_retrieval"
    multi_evidence_case = next(case for case in evaluation_set["cases"] if case["question_type"] == "multi_evidence_policy")
    risk_case = next(case for case in evaluation_set["cases"] if case["question_type"] == "risk_handoff")
    assert multi_evidence_case["external_case_id"] == "cust-eval-001"
    assert multi_evidence_case["source_channel"] == "wecom"
    assert multi_evidence_case["source_category"] == "售后政策"
    assert multi_evidence_case["annotation_notes"] == "公开合成样例，不含真实客户身份。"
    assert multi_evidence_case["expected_chunk_ids"] == [return_chunk["id"], warranty_chunk["id"]]
    assert risk_case["allow_auto_reply"] is False

    run_res = client.post(
        f"/api/knowledge-evaluation-sets/{evaluation_set['id']}/runs",
        headers=headers,
        json={"top_k": 5, "low_confidence_threshold": 0.2},
    )
    assert run_res.status_code == 201
    run = run_res.json()
    summary = run["summary_payload"]
    assert run["run_mode"] == "customer_service_retrieval"
    assert summary["evaluation_scope"] == "customer_service_retrieval_only"
    assert summary["full_evidence_cases"] == 2
    assert summary["full_evidence_covered_cases"] == 2
    assert summary["full_evidence_recall_at_5"] == 1
    assert summary["citation_precision"] > 0
    assert summary["human_review_correctness"] == 1
    assert summary["knowledge_gap_rate"] == 0
    assert summary["forbidden_term_hits"] == 0
    assert summary["answer_quality_metrics_version"] == "p3_06u_26e_customer_service_answer_quality_v1"
    assert summary["final_answer_factuality_measured"] is False
    assert summary["final_answer_factuality_rate"] is None
    assert summary["citation_sufficiency_rate"] == 1
    assert summary["forbidden_commitment_violation_rate"] == 0
    assert summary["handoff_correctness"] == 1
    assert summary["unsupported_answer_rate_measured"] is False

    risky_case = next(case for case in run["case_results"] if case["question"].startswith("超过七天退货时客户"))
    assert risky_case["status"] == "needs_review"
    assert risky_case["failure_reason"] == "auto_reply_not_allowed"
    assert risky_case["result_payload"]["predicted_human_review"] is True
    assert risky_case["result_payload"]["expected_human_review"] is True
    assert risky_case["result_payload"]["full_evidence_recalled_at_5"] is True
    assert risky_case["result_payload"]["answer_quality"]["final_answer_factuality_measured"] is False
    assert risky_case["result_payload"]["answer_quality"]["handoff_correct"] is True
    assert risky_case["result_payload"]["answer_quality"]["forbidden_commitment_passed"] is True
    assert "final_answer_factuality_not_measured" not in risky_case["result_payload"]["answer_quality"]["failure_reasons"]


def test_owner_can_label_evaluation_run_case_factuality_and_update_monthly_review(client, db_session) -> None:
    tenant, _, owner_token = _bootstrap_user(
        client,
        slug="knowledge-factuality-label-owner",
        email="knowledge-factuality-label-owner@example.com",
        role_code="owner",
    )
    owner_headers = {"Authorization": f"Bearer {owner_token}"}

    document_res = client.post(
        f"/api/tenants/{tenant['id']}/knowledge-documents",
        headers=owner_headers,
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

    set_res = client.post(
        f"/api/tenants/{tenant['id']}/knowledge-evaluation-sets",
        headers=owner_headers,
        json={
            "name": "人工事实性标签题集",
            "description": "用于验证最终答案人工标签不会触发模型或外部写入。",
            "status": "active",
            "evaluation_mode": "customer_service_retrieval",
            "cases": [
                {
                    "external_case_id": "fact-label-001",
                    "source_channel": "web",
                    "source_category": "售后",
                    "question": "标准产品保修期多久",
                    "expected_terms": ["三年", "保修"],
                    "expected_source_uri": "internal://docs/after-sales-v1",
                    "expected_human_review": False,
                    "allow_auto_reply": True,
                },
                {
                    "external_case_id": "fact-label-002",
                    "source_channel": "web",
                    "source_category": "风险售后",
                    "question": "客户说要立刻赔付怎么办",
                    "expected_terms": ["人工", "核对"],
                    "expected_human_review": True,
                    "allow_auto_reply": False,
                    "risk_level": "high",
                },
            ],
        },
    )
    assert set_res.status_code == 201
    run_res = client.post(
        f"/api/knowledge-evaluation-sets/{set_res.json()['id']}/runs",
        headers=owner_headers,
        json={"top_k": 5, "low_confidence_threshold": 0.2},
    )
    assert run_res.status_code == 201
    run = run_res.json()
    assert run["summary_payload"]["final_answer_factuality_measured"] is False
    first_case_id = run["case_results"][0]["id"]
    second_case_id = run["case_results"][1]["id"]

    no_token_res = client.patch(
        f"/api/knowledge-evaluation-run-cases/{first_case_id}/factuality-label",
        json={"final_answer_factuality_status": "correct"},
    )
    assert no_token_res.status_code == 401

    agent_role = client.post(
        f"/api/tenants/{tenant['id']}/roles",
        headers=owner_headers,
        json={"code": "agent", "name": "坐席"},
    ).json()
    agent_res = client.post(
        f"/api/tenants/{tenant['id']}/users",
        headers=owner_headers,
        json={"name": "坐席", "email": "fact-label-agent@example.com", "password": "ChangeMe123!"},
    ).json()
    client.post(f"/api/users/{agent_res['id']}/roles", headers=owner_headers, json={"role_id": agent_role["id"]})
    agent_login = client.post(
        "/api/auth/login",
        json={"tenant_slug": tenant["slug"], "email": "fact-label-agent@example.com", "password": "ChangeMe123!"},
    ).json()
    forbidden_res = client.patch(
        f"/api/knowledge-evaluation-run-cases/{first_case_id}/factuality-label",
        headers={"Authorization": f"Bearer {agent_login['access_token']}"},
        json={"final_answer_factuality_status": "correct"},
    )
    assert forbidden_res.status_code == 403

    private_note = "这段人工备注不应该明文进入返回或审计"
    first_label_res = client.patch(
        f"/api/knowledge-evaluation-run-cases/{first_case_id}/factuality-label",
        headers=owner_headers,
        json={
            "final_answer_factuality_status": "correct",
            "citation_sufficient": True,
            "forbidden_commitment_passed": True,
            "handoff_correct": True,
            "reviewer_notes": private_note,
        },
    )
    assert first_label_res.status_code == 200
    first_label = first_label_res.json()
    assert first_label["raw_text_included"] is False
    assert first_label["model_call_performed"] is False
    assert first_label["external_platform_write_performed"] is False
    assert first_label["final_answer_factuality_labeled_cases"] == 1
    assert first_label["final_answer_factuality_rate"] == 1
    assert first_label["updated_run"]["summary_payload"]["final_answer_factuality_measured"] is True
    assert first_label["updated_run"]["summary_payload"]["final_answer_factuality_labeled_cases"] == 1
    assert first_label["updated_run"]["summary_payload"]["unsupported_answer_rate"] == 0

    second_label_res = client.patch(
        f"/api/knowledge-evaluation-run-cases/{second_case_id}/factuality-label",
        headers=owner_headers,
        json={
            "final_answer_factuality_status": "incorrect",
            "citation_sufficient": False,
            "forbidden_commitment_passed": True,
            "handoff_correct": False,
        },
    )
    assert second_label_res.status_code == 200
    second_label = second_label_res.json()
    summary = second_label["updated_run"]["summary_payload"]
    assert second_label["final_answer_factuality_labeled_cases"] == 2
    assert second_label["final_answer_factuality_rate"] == 0.5
    assert summary["final_answer_factuality_correct_cases"] == 1
    assert summary["final_answer_factuality_incorrect_cases"] == 1
    assert summary["citation_sufficiency_rate"] == 0.5
    assert summary["handoff_correctness"] == 0.5
    assert summary["unsupported_answer_rate"] == 0.5

    now = utc_now()
    monthly_res = client.get(
        f"/api/tenants/{tenant['id']}/monthly-quality-review?year={now.year}&month={now.month}",
        headers=owner_headers,
    )
    assert monthly_res.status_code == 200
    monthly = monthly_res.json()
    assert any(metric["key"] == "human_factuality" and metric["value"] == "50%" for metric in monthly["metrics"])
    assert any(cause["key"] == "missing_human_factuality_labels" and cause["count"] == 0 for cause in monthly["root_causes"])
    assert any(action["key"] == "add_human_factuality_labels" and action["status"] == "done" for action in monthly["action_items"])

    serialized_response = str(second_label)
    assert private_note not in serialized_response
    audit_events = db_session.query(AuditEvent).filter(AuditEvent.action == "knowledge_evaluation_run_case.factuality_labeled").all()
    assert len(audit_events) == 2
    audit_payloads = [json.loads(event.payload) if isinstance(event.payload, str) else event.payload for event in audit_events]
    serialized_audit = str(audit_payloads)
    assert private_note not in serialized_audit
    assert all(payload["model_call_performed"] is False for payload in audit_payloads)
    assert all(payload["external_platform_write_performed"] is False for payload in audit_payloads)


def test_owner_can_capture_final_answer_samples_and_batch_label_factuality(client, db_session) -> None:
    tenant, _, owner_token = _bootstrap_user(
        client,
        slug="knowledge-final-answer-sample-owner",
        email="knowledge-final-answer-sample-owner@example.com",
        role_code="owner",
    )
    owner_headers = {"Authorization": f"Bearer {owner_token}"}

    document_res = client.post(
        f"/api/tenants/{tenant['id']}/knowledge-documents",
        headers=owner_headers,
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

    set_res = client.post(
        f"/api/tenants/{tenant['id']}/knowledge-evaluation-sets",
        headers=owner_headers,
        json={
            "name": "最终答案采样题集",
            "description": "用于验证最终客服答案样本和批量人工标签。",
            "status": "active",
            "evaluation_mode": "customer_service_retrieval",
            "cases": [
                {
                    "external_case_id": "final-answer-001",
                    "source_channel": "web",
                    "source_category": "售后",
                    "question": "标准产品保修期多久",
                    "expected_terms": ["三年", "保修"],
                    "expected_source_uri": "internal://docs/after-sales-v1",
                    "expected_human_review": False,
                    "allow_auto_reply": True,
                },
                {
                    "external_case_id": "final-answer-002",
                    "source_channel": "web",
                    "source_category": "风险售后",
                    "question": "客户要求你马上承诺赔付怎么办",
                    "expected_terms": ["人工", "核对"],
                    "expected_human_review": True,
                    "allow_auto_reply": False,
                    "risk_level": "high",
                },
            ],
        },
    )
    assert set_res.status_code == 201
    run_res = client.post(
        f"/api/knowledge-evaluation-sets/{set_res.json()['id']}/runs",
        headers=owner_headers,
        json={"top_k": 5, "low_confidence_threshold": 0.2},
    )
    assert run_res.status_code == 201
    run = run_res.json()
    first_case_id = run["case_results"][0]["id"]
    second_case_id = run["case_results"][1]["id"]

    sample_text = "标准产品保修期为三年；如涉及退换货，需要结合订单时间和商品状态核对。"
    private_note = "这段采样备注不应进入审计明文"
    no_token_sample_res = client.patch(
        f"/api/knowledge-evaluation-run-cases/{first_case_id}/final-answer-sample",
        json={"final_answer_text": sample_text},
    )
    assert no_token_sample_res.status_code == 401

    first_sample_res = client.patch(
        f"/api/knowledge-evaluation-run-cases/{first_case_id}/final-answer-sample",
        headers=owner_headers,
        json={
            "final_answer_text": sample_text,
            "final_answer_source": "manual_capture",
            "citation_uris": ["internal://docs/after-sales-v1"],
            "answer_author": "本地客服工作台",
            "reviewer_notes": private_note,
        },
    )
    assert first_sample_res.status_code == 200
    first_sample = first_sample_res.json()
    assert first_sample["audit_raw_text_included"] is False
    assert first_sample["model_call_performed"] is False
    assert first_sample["external_platform_write_performed"] is False
    assert first_sample["final_answer_sampled_cases"] == 1
    assert first_sample["final_answer_sample_coverage"] == 0.5
    first_case = next(case for case in first_sample["updated_run"]["case_results"] if case["id"] == first_case_id)
    assert first_case["result_payload"]["final_answer_sample"]["final_answer_text"] == sample_text
    assert first_case["result_payload"]["answer_quality"]["final_answer_sample_available"] is True
    assert first_case["result_payload"]["answer_quality"]["final_answer_factuality_status"] == "not_measured_final_answer_sampled"
    first_citation_snapshots = (
        db_session.query(ReplyCitationSnapshot)
        .filter(ReplyCitationSnapshot.evaluation_run_case_id == first_case_id)
        .all()
    )
    assert len(first_citation_snapshots) == 1
    assert first_citation_snapshots[0].source_kind == "final_answer_citation_uri"
    assert first_citation_snapshots[0].source_uri == "internal://docs/after-sales-v1"
    assert first_citation_snapshots[0].no_citation_reason == ""
    assert first_citation_snapshots[0].citation_payload["raw_text_logged"] is False

    second_sample_res = client.patch(
        f"/api/knowledge-evaluation-run-cases/{second_case_id}/final-answer-sample",
        headers=owner_headers,
        json={
            "final_answer_text": "这个问题涉及赔付承诺，需要人工客服核对订单和售后规则后处理。",
            "final_answer_source": "manual_capture",
            "citation_uris": ["internal://docs/after-sales-v1"],
        },
    )
    assert second_sample_res.status_code == 200
    assert second_sample_res.json()["final_answer_sample_coverage"] == 1

    batch_res = client.patch(
        f"/api/knowledge-evaluation-runs/{run['id']}/factuality-labels/batch",
        headers=owner_headers,
        json={
            "labels": [
                {
                    "evaluation_run_case_id": first_case_id,
                    "final_answer_factuality_status": "correct",
                    "citation_sufficient": True,
                    "forbidden_commitment_passed": True,
                    "handoff_correct": True,
                    "reviewer_notes": "事实正确，引用充分。",
                },
                {
                    "evaluation_run_case_id": second_case_id,
                    "final_answer_factuality_status": "needs_human_review",
                    "citation_sufficient": True,
                    "forbidden_commitment_passed": True,
                    "handoff_correct": True,
                    "reviewer_notes": "高风险赔付承诺转人工正确。",
                },
            ]
        },
    )
    assert batch_res.status_code == 200
    batch = batch_res.json()
    assert batch["audit_raw_text_included"] is False
    assert batch["model_call_performed"] is False
    assert batch["external_platform_write_performed"] is False
    assert batch["labeled_cases"] == 2
    assert batch["final_answer_factuality_labeled_cases"] == 2
    assert batch["final_answer_factuality_rate"] == 0.5
    summary = batch["updated_run"]["summary_payload"]
    assert summary["final_answer_sampled_cases"] == 2
    assert summary["final_answer_sample_coverage"] == 1
    assert summary["final_answer_factuality_correct_cases"] == 1
    assert summary["final_answer_factuality_needs_human_review_cases"] == 1
    assert summary["unsupported_answer_rate"] == 0.5

    now = utc_now()
    monthly_res = client.get(
        f"/api/tenants/{tenant['id']}/monthly-quality-review?year={now.year}&month={now.month}",
        headers=owner_headers,
    )
    assert monthly_res.status_code == 200
    monthly = monthly_res.json()
    assert any(metric["key"] == "human_factuality" and metric["value"] == "50%" for metric in monthly["metrics"])

    no_token_report_res = client.get(
        f"/api/tenants/{tenant['id']}/customer-quality-report?year={now.year}&month={now.month}",
    )
    assert no_token_report_res.status_code == 401
    customer_report_res = client.get(
        f"/api/tenants/{tenant['id']}/customer-quality-report?year={now.year}&month={now.month}",
        headers=owner_headers,
    )
    assert customer_report_res.status_code == 200
    customer_report = customer_report_res.json()
    assert customer_report["schema_version"] == "p3-06u-26h2q.customer_quality_report.v1"
    assert customer_report["source_monthly_review_schema_version"] == "p3-06u-26h2m.monthly_quality_review.v1"
    assert customer_report["report_status"] == "sample_insufficient"
    assert customer_report["report_status_label"] == "样本不足"
    assert customer_report["raw_text_included"] is False
    assert customer_report["model_call_performed"] is False
    assert customer_report["external_platform_write_performed"] is False
    assert any(metric["key"] == "final_answer_sample_coverage" and metric["value"] == "100%" for metric in customer_report["headline_metrics"])
    assert any(section["key"] == "answer_quality" for section in customer_report["sections"])
    serialized_customer_report = str(customer_report)
    assert sample_text not in serialized_customer_report
    assert private_note not in serialized_customer_report

    no_token_customer_export_res = client.get(
        f"/api/tenants/{tenant['id']}/customer-quality-report/export?year={now.year}&month={now.month}&format=html",
    )
    assert no_token_customer_export_res.status_code == 401
    customer_export_res = client.get(
        f"/api/tenants/{tenant['id']}/customer-quality-report/export?year={now.year}&month={now.month}&format=html",
        headers=owner_headers,
    )
    assert customer_export_res.status_code == 200
    customer_export = customer_export_res.json()
    assert customer_export["schema_version"] == "p3-06u-26h2s.customer_quality_report_export.v1"
    assert customer_export["report_schema_version"] == "p3-06u-26h2q.customer_quality_report.v1"
    assert customer_export["export_format"] == "html"
    assert customer_export["filename"].endswith(".html")
    assert customer_export["content_type"] == "text/html; charset=utf-8"
    assert customer_export["signoff_status"] == "pending_customer_confirmation"
    assert customer_export["signoff_record"]["storage_mode"] == "local_download_and_audit_event"
    assert customer_export["raw_text_included"] is False
    assert customer_export["final_answer_text_included"] is False
    assert customer_export["reviewer_notes_included"] is False
    assert customer_export["model_call_performed"] is False
    assert customer_export["external_platform_write_performed"] is False
    assert "客户质量复盘留档" in customer_export["body"]
    assert "签收确认区" in customer_export["body"]
    assert "不包含原始客户问题" in customer_export["body"]
    assert "标准产品保修期多久" not in customer_export["body"]
    assert "客户要求你马上承诺赔付怎么办" not in customer_export["body"]
    assert sample_text not in customer_export["body"]
    assert private_note not in customer_export["body"]

    xlsx_export_res = client.get(
        f"/api/tenants/{tenant['id']}/customer-quality-report/export?year={now.year}&month={now.month}&format=xlsx",
        headers=owner_headers,
    )
    assert xlsx_export_res.status_code == 200
    xlsx_export = xlsx_export_res.json()
    assert xlsx_export["export_format"] == "xlsx"
    assert xlsx_export["body_encoding"] == "base64"
    assert xlsx_export["filename"].endswith(".xlsx")
    assert xlsx_export["content_type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    xlsx_bytes = base64.b64decode(xlsx_export["body"])
    with zipfile.ZipFile(io.BytesIO(xlsx_bytes)) as workbook:
        names = set(workbook.namelist())
        assert "[Content_Types].xml" in names
        assert "xl/workbook.xml" in names
        sheet_text = workbook.read("xl/worksheets/sheet1.xml").decode("utf-8")
    assert "报告周期" in sheet_text
    assert "报告可信度" in sheet_text
    assert "不包含原始客户问题" in sheet_text
    assert "标准产品保修期多久" not in sheet_text
    assert "客户要求你马上承诺赔付怎么办" not in sheet_text
    assert sample_text not in sheet_text
    assert private_note not in sheet_text

    docx_export_res = client.get(
        f"/api/tenants/{tenant['id']}/customer-quality-report/export?year={now.year}&month={now.month}&format=docx",
        headers=owner_headers,
    )
    assert docx_export_res.status_code == 200
    docx_export = docx_export_res.json()
    assert docx_export["export_format"] == "docx"
    assert docx_export["body_encoding"] == "base64"
    assert docx_export["filename"].endswith(".docx")
    assert docx_export["content_type"] == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    docx_bytes = base64.b64decode(docx_export["body"])
    with zipfile.ZipFile(io.BytesIO(docx_bytes)) as document:
        names = set(document.namelist())
        assert "[Content_Types].xml" in names
        assert "word/document.xml" in names
        document_xml = document.read("word/document.xml").decode("utf-8")
    assert "客服质量报告" in document_xml
    assert "不是正式电子签章" in document_xml
    assert "原始客户问题" in document_xml
    assert sample_text not in document_xml
    assert private_note not in document_xml

    archives_res = client.get(
        f"/api/tenants/{tenant['id']}/customer-quality-report/archives?page=1&page_size=10&period={customer_export['period']}",
        headers=owner_headers,
    )
    assert archives_res.status_code == 200
    archives = archives_res.json()
    assert archives["schema_version"] == "p3-06u-26h2w4.customer_quality_report_archive_list.v1"
    assert archives["total"] >= 3
    assert archives["raw_text_included"] is False
    assert archives["formal_contract_signoff_performed"] is False
    assert {item["export_format"] for item in archives["items"]} >= {"html", "xlsx", "docx"}
    docx_archive = next(item for item in archives["items"] if item["export_format"] == "docx")
    assert docx_archive["download_supported"] is True
    assert docx_archive["body_archived"] is True
    assert docx_archive["body_sha256"] == docx_export["body_sha256"]

    archived_download_res = client.get(
        f"/api/tenants/{tenant['id']}/customer-quality-report/archives/{docx_archive['audit_event_id']}/download",
        headers=owner_headers,
    )
    assert archived_download_res.status_code == 200
    archived_download = archived_download_res.json()
    assert archived_download["archived"] is True
    assert archived_download["archive_audit_event_id"] == docx_archive["audit_event_id"]
    assert archived_download["body"] == docx_export["body"]
    assert archived_download["body_sha256"] == docx_export["body_sha256"]
    assert archived_download["formal_contract_signoff_performed"] is False

    signoff_note = "客户确认报告可作为本月复盘依据，下月补充抖音样本。"
    no_token_signoff_res = client.post(
        f"/api/tenants/{tenant['id']}/customer-quality-report/signoffs?year={now.year}&month={now.month}",
        json={
            "signoff_status": "accepted_with_notes",
            "signer_name": "张三",
            "signer_role": "运营负责人",
            "signer_organization": "示例门店",
            "confirmation_method": "meeting_confirmation",
            "notes": signoff_note,
        },
    )
    assert no_token_signoff_res.status_code == 401
    signoff_res = client.post(
        f"/api/tenants/{tenant['id']}/customer-quality-report/signoffs?year={now.year}&month={now.month}",
        headers=owner_headers,
        json={
            "signoff_status": "accepted_with_notes",
            "signer_name": "张三",
            "signer_role": "运营负责人",
            "signer_organization": "示例门店",
            "confirmation_method": "meeting_confirmation",
            "notes": signoff_note,
        },
    )
    assert signoff_res.status_code == 201
    signoff = signoff_res.json()
    assert signoff["schema_version"] == "p3-06u-26h2t.customer_quality_report_signoff.v1"
    assert signoff["report_schema_version"] == "p3-06u-26h2q.customer_quality_report.v1"
    assert signoff["export_schema_version"] == "p3-06u-26h2s.customer_quality_report_export.v1"
    assert signoff["period"] == customer_export["period"]
    assert signoff["signoff_status"] == "accepted_with_notes"
    assert signoff["signoff_status_label"] == "确认通过，有备注"
    assert signoff["signer_display_name"] == "张*"
    assert signoff["confirmation_method_label"] == "会议确认"
    assert signoff["notes_recorded"] is True
    assert signoff["notes_length"] == len(signoff_note)
    assert len(signoff["notes_hash"]) == 64
    assert signoff["raw_text_included"] is False
    assert signoff["final_answer_text_included"] is False
    assert signoff["reviewer_notes_included"] is False
    assert signoff["signer_name_raw_included"] is False
    assert signoff["electronic_signature_performed"] is False
    assert signoff["formal_contract_signoff_performed"] is False
    assert signoff["model_call_performed"] is False
    assert signoff["external_platform_write_performed"] is False
    assert "张三" not in str(signoff)
    assert signoff_note not in str(signoff)

    no_token_signoff_list_res = client.get(
        f"/api/tenants/{tenant['id']}/customer-quality-report/signoffs?page=1&page_size=5&period={customer_export['period']}",
    )
    assert no_token_signoff_list_res.status_code == 401
    signoff_list_res = client.get(
        f"/api/tenants/{tenant['id']}/customer-quality-report/signoffs?page=1&page_size=5&period={customer_export['period']}",
        headers=owner_headers,
    )
    assert signoff_list_res.status_code == 200
    signoff_list = signoff_list_res.json()
    assert signoff_list["schema_version"] == "p3-06u-26h2u.customer_quality_report_signoff_list.v1"
    assert signoff_list["total"] == 1
    assert signoff_list["raw_text_included"] is False
    assert signoff_list["final_answer_text_included"] is False
    assert signoff_list["reviewer_notes_included"] is False
    assert signoff_list["signer_name_raw_included"] is False
    assert signoff_list["external_platform_write_performed"] is False
    signoff_item = signoff_list["items"][0]
    assert signoff_item["schema_version"] == "p3-06u-26h2t.customer_quality_report_signoff.v1"
    assert signoff_item["period"] == customer_export["period"]
    assert signoff_item["signoff_status_label"] == "确认通过，有备注"
    assert signoff_item["signer_display_name"] == "张*"
    assert signoff_item["notes_recorded"] is True
    assert signoff_item["notes_length"] == len(signoff_note)
    assert len(signoff_item["notes_hash"]) == 64
    assert signoff_item["audit_action"] == "customer_quality_report.signoff_recorded"
    assert "张三" not in str(signoff_list)
    assert signoff_note not in str(signoff_list)

    no_token_export_res = client.get(
        f"/api/knowledge-evaluation-runs/{run['id']}/final-answer-labels/export?format=csv",
    )
    assert no_token_export_res.status_code == 401
    export_res = client.get(
        f"/api/knowledge-evaluation-runs/{run['id']}/final-answer-labels/export?format=csv",
        headers=owner_headers,
    )
    assert export_res.status_code == 200
    export_payload = export_res.json()
    assert export_payload["schema_version"] == "p3-06u-26h2r.final_answer_label_io.v1"
    assert export_payload["export_format"] == "csv"
    assert export_payload["filename"].endswith("_final_answer_labels.csv")
    assert export_payload["raw_text_included"] is True
    assert export_payload["question_raw_text_included"] is False
    assert export_payload["final_answer_text_included"] is True
    assert export_payload["provider_call_performed"] is False
    assert export_payload["external_write_performed"] is False
    assert "question_hash" in export_payload["body"].splitlines()[0]
    assert "question," not in export_payload["body"].splitlines()[0]
    assert "客户要求你马上承诺赔付怎么办" not in export_payload["body"]
    assert sample_text in export_payload["body"]
    assert private_note not in export_payload["body"]
    exported_rows = list(csv.DictReader(io.StringIO(export_payload["body"])))
    assert len(exported_rows) == 2
    assert {row["external_case_id"] for row in exported_rows} == {"final-answer-001", "final-answer-002"}
    assert {row["final_answer_factuality_status"] for row in exported_rows} == {"correct", "needs_human_review"}

    second_run_res = client.post(
        f"/api/knowledge-evaluation-sets/{set_res.json()['id']}/runs",
        headers=owner_headers,
        json={"top_k": 5, "low_confidence_threshold": 0.2},
    )
    assert second_run_res.status_code == 201
    second_run = second_run_res.json()
    assert second_run["id"] != run["id"]
    assert second_run["summary_payload"].get("final_answer_sampled_cases", 0) == 0

    no_token_import_res = client.post(
        f"/api/knowledge-evaluation-runs/{second_run['id']}/final-answer-labels/imports",
        json={"content": export_payload["body"], "dry_run": True},
    )
    assert no_token_import_res.status_code == 401
    dry_run_import_res = client.post(
        f"/api/knowledge-evaluation-runs/{second_run['id']}/final-answer-labels/imports",
        headers=owner_headers,
        json={"content": export_payload["body"], "dry_run": True},
    )
    assert dry_run_import_res.status_code == 200
    dry_run_import = dry_run_import_res.json()
    assert dry_run_import["dry_run"] is True
    assert dry_run_import["imported"] is False
    assert dry_run_import["total_rows"] == 2
    assert dry_run_import["matched_rows"] == 2
    assert dry_run_import["sample_rows"] == 2
    assert dry_run_import["label_rows"] == 2
    assert dry_run_import["validation_errors"] == []
    assert dry_run_import["status_counts"] == {"correct": 1, "needs_human_review": 1}

    import_res = client.post(
        f"/api/knowledge-evaluation-runs/{second_run['id']}/final-answer-labels/imports",
        headers=owner_headers,
        json={"content": export_payload["body"], "dry_run": False},
    )
    assert import_res.status_code == 200
    imported = import_res.json()
    assert imported["dry_run"] is False
    assert imported["imported"] is True
    assert imported["audit_raw_text_included"] is False
    assert imported["provider_call_performed"] is False
    assert imported["external_write_performed"] is False
    imported_summary = imported["updated_run"]["summary_payload"]
    assert imported_summary["final_answer_sampled_cases"] == 2
    assert imported_summary["final_answer_sample_coverage"] == 1
    assert imported_summary["final_answer_factuality_labeled_cases"] == 2
    assert imported_summary["final_answer_factuality_rate"] == 0.5
    imported_first_case = next(
        case
        for case in imported["updated_run"]["case_results"]
        if case["result_payload"]["external_case_id"] == "final-answer-001"
    )
    assert imported_first_case["result_payload"]["final_answer_sample"]["final_answer_text"] == sample_text
    assert imported_first_case["result_payload"]["answer_quality"]["final_answer_factuality_status"] == "correct"

    sample_audit_events = (
        db_session.query(AuditEvent)
        .filter(AuditEvent.action == "knowledge_evaluation_run_case.final_answer_sampled")
        .all()
    )
    assert len(sample_audit_events) == 2
    batch_audit_events = (
        db_session.query(AuditEvent)
        .filter(AuditEvent.action == "knowledge_evaluation_run_case.factuality_batch_labeled")
        .all()
    )
    assert len(batch_audit_events) == 1
    export_audit_events = (
        db_session.query(AuditEvent)
        .filter(AuditEvent.action == "knowledge_evaluation_run.final_answer_labels_exported")
        .all()
    )
    assert len(export_audit_events) == 1
    import_audit_events = (
        db_session.query(AuditEvent)
        .filter(AuditEvent.action == "knowledge_evaluation_run.final_answer_labels_imported")
        .all()
    )
    assert len(import_audit_events) == 1
    customer_report_export_events = (
        db_session.query(AuditEvent)
        .filter(AuditEvent.action == "customer_quality_report.exported")
        .all()
    )
    assert len(customer_report_export_events) == 3
    customer_report_signoff_events = (
        db_session.query(AuditEvent)
        .filter(AuditEvent.action == "customer_quality_report.signoff_recorded")
        .all()
    )
    assert len(customer_report_signoff_events) == 1
    serialized_audit = str(
        [
            json.loads(event.payload) if isinstance(event.payload, str) else event.payload
            for event in [
                *sample_audit_events,
                *batch_audit_events,
                *export_audit_events,
                *import_audit_events,
                *customer_report_export_events,
                *customer_report_signoff_events,
            ]
        ]
    )
    assert sample_text not in serialized_audit
    assert private_note not in serialized_audit
    assert "标准产品保修期多久" not in serialized_audit
    assert "张三" not in serialized_audit
    assert signoff_note not in serialized_audit
    assert "raw_text_included" in serialized_audit


def _customer_question_bank_cases(count: int, *, sensitive: bool = False) -> list[dict]:
    channels = ["web_widget", "wecom", "douyin", "taobao", "xiaohongshu"]
    categories = ["售前咨询", "交付部署", "售后退款", "隐私安全", "知识缺口"]
    risks = ["low", "medium", "high"]
    cases: list[dict] = []
    for index in range(count):
        case_number = index + 1
        question = f"客户第{case_number}个脱敏问题想了解套餐范围和交付步骤"
        if sensitive and index == 0:
            question = "客户手机号 13800138000 想咨询套餐"
        cases.append(
            {
                "external_case_id": f"real-bank-{case_number:03d}",
                "source_channel": channels[index % len(channels)],
                "source_category": categories[index % len(categories)],
                "question": question,
                "question_type": "standard_customer_question" if index % 5 else "risk_handoff",
                "expected_terms": ["套餐范围", "交付步骤", "人工确认"],
                "expected_source_uri": f"internal://customer-bank/source-{index % 4}",
                "expected_document_title": "客户试点知识包",
                "expected_human_review": index % 5 == 0,
                "allow_auto_reply": index % 5 != 0,
                "forbidden_terms": ["保证效果"] if index % 4 == 0 else [],
                "risk_level": risks[index % len(risks)],
                "annotation_notes": (
                    f"business_object_hash=bo{case_number:03d};"
                    f"expected_answer_hash=ans{case_number:03d};"
                    "真实答案已脱敏后另行保管"
                ),
                "required_citation": True,
                "priority": case_number,
                "status": "active",
            }
        )
    return cases


def test_owner_can_precheck_and_import_50_case_customer_question_bank_without_raw_text(client, db_session) -> None:
    tenant, _, token = _bootstrap_user(
        client,
        slug="customer-bank-owner",
        email="customer-bank-owner@example.com",
        role_code="owner",
    )
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "name": "真实客户题库 50 题第一批",
        "description": "用于验证真实客户题库导入、脱敏和覆盖分布。",
        "source_label": "customer_pilot_batch_001",
        "minimum_case_count": 50,
        "maximum_case_count": 100,
        "cases": _customer_question_bank_cases(50),
    }

    no_token_res = client.post(
        f"/api/tenants/{tenant['id']}/customer-service-question-banks/precheck",
        json=payload,
    )
    assert no_token_res.status_code == 401

    small_res = client.post(
        f"/api/tenants/{tenant['id']}/customer-service-question-banks/precheck",
        headers=headers,
        json={**payload, "cases": _customer_question_bank_cases(49)},
    )
    assert small_res.status_code == 200
    small = small_res.json()
    assert small["can_import"] is False
    assert small["imported"] is False
    assert any("case_count_below_minimum" in item for item in small["validation_errors"])

    sensitive_res = client.post(
        f"/api/tenants/{tenant['id']}/customer-service-question-banks/precheck",
        headers=headers,
        json={**payload, "cases": _customer_question_bank_cases(50, sensitive=True)},
    )
    assert sensitive_res.status_code == 200
    sensitive = sensitive_res.json()
    assert sensitive["can_import"] is False
    assert sensitive["sensitive_rows"][0]["patterns"] == ["mainland_mobile"]
    assert "13800138000" not in str(sensitive)

    precheck_res = client.post(
        f"/api/tenants/{tenant['id']}/customer-service-question-banks/precheck",
        headers=headers,
        json=payload,
    )
    assert precheck_res.status_code == 200
    precheck = precheck_res.json()
    assert precheck["status"] == "ready"
    assert precheck["can_import"] is True
    assert precheck["imported"] is False
    assert precheck["case_count"] == 50
    assert precheck["coverage_summary"]["case_count_target"]["within_range"] is True
    assert precheck["coverage_summary"]["source_channel_diversity"] == 5
    assert precheck["coverage_summary"]["expected_terms_coverage"] == 1
    assert precheck["coverage_summary"]["source_reference_coverage"] == 1
    assert precheck["coverage_summary"]["business_object_hash_cases"] == 50
    assert precheck["coverage_summary"]["expected_answer_hash_cases"] == 50
    assert precheck["raw_text_included"] is False
    assert precheck["provider_call_performed"] is False
    assert precheck["external_write_performed"] is False
    assert "客户第1个脱敏问题" not in str(precheck)

    import_res = client.post(
        f"/api/tenants/{tenant['id']}/customer-service-question-banks/import",
        headers=headers,
        json=payload,
    )
    assert import_res.status_code == 201
    imported = import_res.json()
    assert imported["status"] == "imported"
    assert imported["imported"] is True
    assert imported["evaluation_set_id"] is not None
    assert imported["case_count"] == 50
    assert imported["raw_text_included"] is False
    assert imported["provider_call_performed"] is False
    assert imported["external_write_performed"] is False
    assert "客户第1个脱敏问题" not in str(imported)

    created_set = db_session.get(KnowledgeEvaluationSet, imported["evaluation_set_id"])
    assert created_set is not None
    assert created_set.evaluation_mode == "customer_service_retrieval"
    assert db_session.query(KnowledgeEvaluationCase).filter_by(evaluation_set_id=created_set.id).count() == 50

    audit_events = db_session.query(AuditEvent).filter(AuditEvent.action == "customer_service_question_bank.imported").all()
    assert len(audit_events) == 1
    audit_payload = json.loads(audit_events[0].payload) if isinstance(audit_events[0].payload, str) else audit_events[0].payload
    assert audit_payload["case_count"] == 50
    assert audit_payload["coverage_summary"]["raw_question_text_included"] is False
    assert audit_payload["provider_call_performed"] is False
    assert audit_payload["external_platform_write_performed"] is False
    assert "客户第1个脱敏问题" not in str(audit_payload)


def test_owner_can_read_monthly_quality_review_without_raw_text_or_external_actions(client, db_session) -> None:
    tenant, user, token = _bootstrap_user(
        client,
        slug="monthly-quality-owner",
        email="monthly-quality-owner@example.com",
        role_code="owner",
    )
    owner_headers = {"Authorization": f"Bearer {token}"}
    now = utc_now()

    channel = Channel(tenant_id=tenant["id"], type="web", name="官网客服", status="active")
    contact = Contact(tenant_id=tenant["id"], display_name="本月质量客户")
    db_session.add_all([channel, contact])
    db_session.flush()
    conversation = Conversation(
        tenant_id=tenant["id"],
        channel_id=channel.id,
        contact_id=contact.id,
        status="needs_human",
        priority="high",
        subject="月度复盘会话",
    )
    db_session.add(conversation)
    db_session.flush()
    message = Message(
        conversation_id=conversation.id,
        direction="inbound",
        sender_type="customer",
        content="客户原文不应该出现在月度复盘包里",
        external_message_id="monthly-quality-msg-001",
    )
    db_session.add(message)
    db_session.flush()
    workflow_run = WorkflowRun(
        tenant_id=tenant["id"],
        conversation_id=conversation.id,
        trigger_message_id=message.id,
        status="waiting_human",
        current_step="human_review",
        idempotency_key="monthly-quality-workflow-001",
        state_payload={"confidence": 0.24, "retrieved_knowledge_count": 0},
    )
    db_session.add(workflow_run)
    db_session.flush()
    db_session.add(
        HumanReviewTask(
            tenant_id=tenant["id"],
            workflow_run_id=workflow_run.id,
            conversation_id=conversation.id,
            message_id=message.id,
            status="open",
            reason="low_confidence",
            risk_level="high",
            draft_reply="草稿全文也不应该出现在月度复盘包里",
        )
    )

    evaluation_set = KnowledgeEvaluationSet(
        tenant_id=tenant["id"],
        name="月度质量复盘题集",
        status="active",
        evaluation_mode="customer_service_retrieval",
        created_by_id=user["id"],
        updated_by_id=user["id"],
    )
    db_session.add(evaluation_set)
    db_session.flush()
    evaluation_case = KnowledgeEvaluationCase(
        tenant_id=tenant["id"],
        evaluation_set_id=evaluation_set.id,
        external_case_id="monthly-001",
        source_channel="web",
        source_category="售后",
        question="这个问题文本也不应泄露到月度复盘包",
        question_type="policy_gap",
        expected_terms=["售后规则"],
        expected_human_review=True,
        allow_auto_reply=False,
        risk_level="high",
        status="active",
    )
    db_session.add(evaluation_case)
    db_session.flush()
    evaluation_run = KnowledgeEvaluationRun(
        tenant_id=tenant["id"],
        evaluation_set_id=evaluation_set.id,
        run_mode="customer_service_retrieval",
        retrieval_mode="hybrid_bm25_vector_rerank_v1",
        vector_engine="deterministic_local_hash_embedding_v1",
        total_cases=2,
        answered_cases=1,
        no_hit_cases=1,
        passed_cases=0,
        failed_cases=2,
        needs_review_cases=2,
        citation_covered_cases=1,
        expected_term_covered_cases=0,
        hit_rate=0.5,
        citation_coverage=0.5,
        expected_term_coverage=0,
        average_confidence=0.32,
        summary_payload={
            "answer_quality_metrics_version": "p3_06u_26e_customer_service_answer_quality_v1",
            "final_answer_factuality_measured": False,
            "final_answer_factuality_rate": None,
            "handoff_correctness": 0.5,
        },
        created_by_id=user["id"],
        created_at=now,
    )
    db_session.add(evaluation_run)
    db_session.flush()
    db_session.add(
        KnowledgeEvaluationRunCase(
            tenant_id=tenant["id"],
            evaluation_run_id=evaluation_run.id,
            evaluation_case_id=evaluation_case.id,
            question=evaluation_case.question,
            status="failed",
            top_score=0.1,
            top_confidence=0.22,
            citation_present=False,
            expected_terms_found=False,
            failure_reason="expected_terms_missing",
            result_payload={
                "knowledge_gap": True,
                "human_review_prediction_correct": False,
                "answer_quality": {
                    "final_answer_factuality_measured": False,
                    "handoff_correct": False,
                    "forbidden_commitment_passed": True,
                },
            },
        )
    )
    db_session.add(
        KnowledgeGapItem(
            tenant_id=tenant["id"],
            status="open",
            severity="high",
            source_type="evaluation_run",
            source_ref=str(evaluation_run.id),
            source_title="月度质量缺口",
            source_excerpt="缺口原文不应输出",
            question_excerpt="问题原文不应输出",
            gap_type="expected_terms_missing",
            expected_terms=["售后规则"],
        )
    )
    db_session.add(
        ReplyDecision(
            tenant_id=tenant["id"],
            conversation_id=conversation.id,
            message_id=message.id,
            channel_id=channel.id,
            state="knowledge_gap",
            reason="no_knowledge_card_match",
            confidence=0.2,
            delivery_mode="human_review",
            draft_reply="回复决策草稿也不应输出",
            idempotency_key="monthly-quality-decision-001",
            created_at=now,
        )
    )
    db_session.add(
        ReplyDecision(
            tenant_id=tenant["id"],
            conversation_id=conversation.id,
            message_id=message.id,
            channel_id=channel.id,
            state="auto_reply_ready",
            reason="knowledge_card_match",
            confidence=0.86,
            delivery_mode="draft_only",
            draft_reply="自动回复草稿不应输出",
            idempotency_key="monthly-quality-decision-002",
            created_at=now,
        )
    )
    db_session.add(
        ModelCallRecord(
            tenant_id=tenant["id"],
            channel_id=channel.id,
            conversation_id=conversation.id,
            message_id=message.id,
            provenance_id="monthly-ops-provenance-001",
            request_id="monthly-ops-request-001",
            idempotency_key="monthly-ops-model-001",
            provider="bailian",
            model="qwen-plus",
            route_name="standard_reply",
            target_model_tier="standard",
            complexity="normal",
            status="success",
            input_units=120,
            output_units=80,
            total_units=200,
            unit_type="tokens",
            latency_ms=980,
            estimated_cost=0.012,
            currency="CNY",
            pricing_source="internal_test_fixture",
            pricing_version="2026-07-test",
            budget_policy_snapshot={"max_monthly_cost": 100},
            raw_text_logged=False,
            created_at=now,
        )
    )
    db_session.commit()

    no_token_res = client.get(f"/api/tenants/{tenant['id']}/monthly-quality-review")
    assert no_token_res.status_code == 401

    agent_role = client.post(
        f"/api/tenants/{tenant['id']}/roles",
        headers=owner_headers,
        json={"code": "agent", "name": "坐席"},
    ).json()
    agent_res = client.post(
        f"/api/tenants/{tenant['id']}/users",
        headers=owner_headers,
        json={"name": "坐席", "email": "monthly-quality-agent@example.com", "password": "ChangeMe123!"},
    ).json()
    client.post(f"/api/users/{agent_res['id']}/roles", headers=owner_headers, json={"role_id": agent_role["id"]})
    agent_login = client.post(
        "/api/auth/login",
        json={"tenant_slug": tenant["slug"], "email": "monthly-quality-agent@example.com", "password": "ChangeMe123!"},
    ).json()
    forbidden_res = client.get(
        f"/api/tenants/{tenant['id']}/monthly-quality-review",
        headers={"Authorization": f"Bearer {agent_login['access_token']}"},
    )
    assert forbidden_res.status_code == 403

    review_res = client.get(
        f"/api/tenants/{tenant['id']}/monthly-quality-review?year={now.year}&month={now.month}",
        headers=owner_headers,
    )
    assert review_res.status_code == 200
    body = review_res.json()
    assert body["schema_version"] == "p3-06u-26h2m.monthly_quality_review.v1"
    assert body["latest_evaluation_run_id"] == evaluation_run.id
    assert body["latest_evaluation_set_id"] == evaluation_set.id
    assert body["raw_text_included"] is False
    assert body["model_call_performed"] is False
    assert body["external_call_performed"] is False
    assert body["external_platform_write_performed"] is False
    assert body["knowledge_gap_summary"]["open_backlog"] == 1
    assert body["human_review_summary"]["created_this_month"] == 1
    assert body["reply_decision_summary"]["created_this_month"] == 2
    assert body["reply_decision_summary"]["auto_reply_ready"] == 1
    assert body["trend_summary"]["case_failure_counts"]["knowledge_gap_cases"] == 1
    assert any(metric["key"] == "question_bank_size" and metric["status"] == "warning" for metric in body["metrics"])
    assert any(cause["key"] == "missing_human_factuality_labels" and cause["count"] == 1 for cause in body["root_causes"])
    assert any(action["key"] == "import_real_question_bank" and action["status"] == "open" for action in body["action_items"])
    assert any("渠道官方接入验收不纳入本片" in boundary for boundary in body["data_boundaries"])
    serialized = str(body)
    assert "客户原文不应该出现在月度复盘包里" not in serialized
    assert "草稿全文也不应该出现在月度复盘包里" not in serialized
    assert "问题原文不应泄露到月度复盘包" not in serialized

    ops_no_token_res = client.get(f"/api/tenants/{tenant['id']}/monthly-ops-report")
    assert ops_no_token_res.status_code == 401
    ops_forbidden_res = client.get(
        f"/api/tenants/{tenant['id']}/monthly-ops-report",
        headers={"Authorization": f"Bearer {agent_login['access_token']}"},
    )
    assert ops_forbidden_res.status_code == 403

    ops_res = client.get(
        f"/api/tenants/{tenant['id']}/monthly-ops-report?year={now.year}&month={now.month}",
        headers=owner_headers,
    )
    assert ops_res.status_code == 200
    ops_body = ops_res.json()
    assert ops_body["schema_version"] == "p3-06u-26h2w-ops2.monthly_ops_report.v1"
    assert ops_body["raw_text_included"] is False
    assert ops_body["draft_text_included"] is False
    assert ops_body["secret_included"] is False
    assert ops_body["external_platform_write_performed"] is False
    assert ops_body["real_platform_send_ready"] is False
    assert ops_body["production_sla_ready"] is False
    assert ops_body["formal_customer_signoff_ready"] is False
    assert ops_body["upstream_evidence"]["model_call_record_count"] == 1
    assert ops_body["model_cost"]["metrics"][0]["key"] == "call_count"
    assert any(section["source"] == "model_call_records" for section in ops_body["model_cost"]["evidence"])
    assert any("不是生产 SLA" in boundary for boundary in ops_body["data_boundaries"])
    ops_serialized = str(ops_body)
    assert "客户原文不应该出现在月度复盘包里" not in ops_serialized
    assert "草稿全文也不应该出现在月度复盘包里" not in ops_serialized
    assert "问题原文不应泄露到月度复盘包" not in ops_serialized
    assert "ChangeMe123!" not in ops_serialized


def test_owner_can_read_persisted_customer_service_evaluation_run(client) -> None:
    tenant, _, owner_token = _bootstrap_user(
        client,
        slug="knowledge-eval-run-read",
        email="knowledge-eval-run-read-owner@example.com",
        role_code="owner",
    )
    owner_headers = {"Authorization": f"Bearer {owner_token}"}

    document_res = client.post(
        f"/api/tenants/{tenant['id']}/knowledge-documents",
        headers=owner_headers,
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
    chunks = client.get(f"/api/knowledge-documents/{document['id']}/chunks", headers=owner_headers).json()
    return_chunk = next(chunk for chunk in chunks if "订单时间" in chunk["content"])

    set_res = client.post(
        f"/api/tenants/{tenant['id']}/knowledge-evaluation-sets",
        headers=owner_headers,
        json={
            "name": "客服评测运行读取题集",
            "status": "active",
            "evaluation_mode": "customer_service_retrieval",
            "cases": [
                {
                    "external_case_id": "cust-read-001",
                    "source_channel": "wecom",
                    "source_category": "售后政策",
                    "question": "超过七天退货需要核对什么",
                    "question_type": "policy_question",
                    "expected_terms": ["订单时间", "商品状态"],
                    "expected_source_uri": "internal://docs/after-sales-v1",
                    "expected_chunk_ids": [return_chunk["id"]],
                    "must_have_all_evidence": True,
                    "expected_human_review": False,
                    "allow_auto_reply": True,
                    "risk_level": "medium",
                    "required_citation": True,
                }
            ],
        },
    )
    assert set_res.status_code == 201

    run_res = client.post(
        f"/api/knowledge-evaluation-sets/{set_res.json()['id']}/runs",
        headers=owner_headers,
        json={"top_k": 5, "low_confidence_threshold": 0.2},
    )
    assert run_res.status_code == 201
    created_run = run_res.json()

    no_token_res = client.get(f"/api/knowledge-evaluation-runs/{created_run['id']}")
    assert no_token_res.status_code == 401

    read_res = client.get(f"/api/knowledge-evaluation-runs/{created_run['id']}", headers=owner_headers)
    assert read_res.status_code == 200
    read_run = read_res.json()
    assert read_run["id"] == created_run["id"]
    assert read_run["tenant_id"] == tenant["id"]
    assert read_run["run_mode"] == "customer_service_retrieval"
    assert read_run["summary_payload"]["customer_service_metrics_version"] == "p2_22_customer_service_retrieval_v1"
    assert len(read_run["case_results"]) == 1
    assert read_run["case_results"][0]["result_payload"]["external_case_id"] == "cust-read-001"

    agent_role = client.post(
        f"/api/tenants/{tenant['id']}/roles",
        headers=owner_headers,
        json={"code": "agent", "name": "客服坐席"},
    ).json()
    agent = client.post(
        f"/api/tenants/{tenant['id']}/users",
        headers=owner_headers,
        json={"name": "客服坐席", "email": "knowledge-eval-run-agent@example.com", "password": "ChangeMe123!"},
    ).json()
    client.post(f"/api/users/{agent['id']}/roles", headers=owner_headers, json={"role_id": agent_role["id"]})
    agent_login = client.post(
        "/api/auth/login",
        json={
            "tenant_slug": tenant["slug"],
            "email": "knowledge-eval-run-agent@example.com",
            "password": "ChangeMe123!",
        },
    ).json()
    agent_res = client.get(
        f"/api/knowledge-evaluation-runs/{created_run['id']}",
        headers={"Authorization": f"Bearer {agent_login['access_token']}"},
    )
    assert agent_res.status_code == 403

    other_tenant, _, other_token = _bootstrap_user(
        client,
        slug="knowledge-eval-run-read-other",
        email="knowledge-eval-run-read-other@example.com",
        role_code="owner",
    )
    assert other_tenant["id"] != tenant["id"]
    cross_tenant_res = client.get(
        f"/api/knowledge-evaluation-runs/{created_run['id']}",
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert cross_tenant_res.status_code == 404


def test_owner_can_list_persisted_evaluation_runs_without_case_payload(client) -> None:
    tenant, _, owner_token = _bootstrap_user(
        client,
        slug="knowledge-eval-run-list",
        email="knowledge-eval-run-list-owner@example.com",
        role_code="owner",
    )
    owner_headers = {"Authorization": f"Bearer {owner_token}"}

    document_res = client.post(
        f"/api/tenants/{tenant['id']}/knowledge-documents",
        headers=owner_headers,
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

    set_res = client.post(
        f"/api/tenants/{tenant['id']}/knowledge-evaluation-sets",
        headers=owner_headers,
        json={
            "name": "客服评测历史题集",
            "status": "active",
            "evaluation_mode": "customer_service_retrieval",
            "cases": [
                {
                    "external_case_id": "cust-list-001",
                    "source_channel": "wecom",
                    "source_category": "售后政策",
                    "question": "标准产品保修期多久",
                    "question_type": "policy_question",
                    "expected_terms": ["三年", "保修"],
                    "expected_source_uri": "internal://docs/after-sales-v1",
                    "expected_human_review": False,
                    "allow_auto_reply": True,
                    "risk_level": "low",
                    "required_citation": True,
                }
            ],
        },
    )
    assert set_res.status_code == 201
    evaluation_set = set_res.json()

    first_run = client.post(
        f"/api/knowledge-evaluation-sets/{evaluation_set['id']}/runs",
        headers=owner_headers,
        json={"top_k": 3, "low_confidence_threshold": 0.2},
    ).json()
    second_run = client.post(
        f"/api/knowledge-evaluation-sets/{evaluation_set['id']}/runs",
        headers=owner_headers,
        json={"top_k": 5, "low_confidence_threshold": 0.4},
    ).json()
    assert first_run["id"] != second_run["id"]

    no_token_res = client.get(f"/api/knowledge-evaluation-sets/{evaluation_set['id']}/runs")
    assert no_token_res.status_code == 401

    list_res = client.get(
        f"/api/knowledge-evaluation-sets/{evaluation_set['id']}/runs",
        headers=owner_headers,
    )
    assert list_res.status_code == 200
    payload = list_res.json()
    assert payload["total"] == 2
    assert payload["page"] == 1
    assert payload["page_size"] == 20
    assert [item["id"] for item in payload["items"]] == [second_run["id"], first_run["id"]]
    assert payload["items"][0]["evaluation_set_id"] == evaluation_set["id"]
    assert payload["items"][0]["run_mode"] == "customer_service_retrieval"
    assert payload["items"][0]["summary_payload"]["customer_service_metrics_version"] == "p2_22_customer_service_retrieval_v1"
    assert "case_results" not in payload["items"][0]
    assert "question" not in payload["items"][0]

    paged_res = client.get(
        f"/api/knowledge-evaluation-sets/{evaluation_set['id']}/runs?page=2&page_size=1",
        headers=owner_headers,
    )
    assert paged_res.status_code == 200
    assert [item["id"] for item in paged_res.json()["items"]] == [first_run["id"]]

    agent_role = client.post(
        f"/api/tenants/{tenant['id']}/roles",
        headers=owner_headers,
        json={"code": "agent", "name": "客服坐席"},
    ).json()
    agent = client.post(
        f"/api/tenants/{tenant['id']}/users",
        headers=owner_headers,
        json={"name": "客服坐席", "email": "knowledge-eval-run-list-agent@example.com", "password": "ChangeMe123!"},
    ).json()
    client.post(f"/api/users/{agent['id']}/roles", headers=owner_headers, json={"role_id": agent_role["id"]})
    agent_login = client.post(
        "/api/auth/login",
        json={
            "tenant_slug": tenant["slug"],
            "email": "knowledge-eval-run-list-agent@example.com",
            "password": "ChangeMe123!",
        },
    ).json()
    agent_res = client.get(
        f"/api/knowledge-evaluation-sets/{evaluation_set['id']}/runs",
        headers={"Authorization": f"Bearer {agent_login['access_token']}"},
    )
    assert agent_res.status_code == 403

    other_tenant, _, other_token = _bootstrap_user(
        client,
        slug="knowledge-eval-run-list-other",
        email="knowledge-eval-run-list-other@example.com",
        role_code="owner",
    )
    assert other_tenant["id"] != tenant["id"]
    cross_tenant_res = client.get(
        f"/api/knowledge-evaluation-sets/{evaluation_set['id']}/runs",
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert cross_tenant_res.status_code == 404


def test_owner_can_export_sanitized_evaluation_run_report_without_raw_questions(client) -> None:
    tenant, _, owner_token = _bootstrap_user(
        client,
        slug="knowledge-eval-report-api",
        email="knowledge-eval-report-api-owner@example.com",
        role_code="owner",
    )
    owner_headers = {"Authorization": f"Bearer {owner_token}"}

    document_res = client.post(
        f"/api/tenants/{tenant['id']}/knowledge-documents",
        headers=owner_headers,
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
    chunks = client.get(f"/api/knowledge-documents/{document['id']}/chunks", headers=owner_headers).json()
    return_chunk = next(chunk for chunk in chunks if "订单时间" in chunk["content"])

    set_res = client.post(
        f"/api/tenants/{tenant['id']}/knowledge-evaluation-sets",
        headers=owner_headers,
        json={
            "name": "客服评测报告导出题集",
            "status": "active",
            "evaluation_mode": "customer_service_retrieval",
            "cases": [
                {
                    "external_case_id": "cust-report-001",
                    "source_channel": "wecom",
                    "source_category": "售后政策",
                    "question": "超过七天退货需要核对什么",
                    "question_type": "policy_question",
                    "expected_terms": ["订单时间", "商品状态"],
                    "expected_source_uri": "internal://docs/after-sales-v1",
                    "expected_chunk_ids": [return_chunk["id"]],
                    "must_have_all_evidence": True,
                    "expected_human_review": False,
                    "allow_auto_reply": True,
                    "risk_level": "medium",
                    "required_citation": True,
                }
            ],
        },
    )
    assert set_res.status_code == 201

    run_res = client.post(
        f"/api/knowledge-evaluation-sets/{set_res.json()['id']}/runs",
        headers=owner_headers,
        json={"top_k": 5, "low_confidence_threshold": 0.2},
    )
    assert run_res.status_code == 201
    created_run = run_res.json()

    no_token_res = client.get(f"/api/knowledge-evaluation-runs/{created_run['id']}/report")
    assert no_token_res.status_code == 401

    markdown_res = client.get(
        f"/api/knowledge-evaluation-runs/{created_run['id']}/report?format=markdown",
        headers=owner_headers,
    )
    assert markdown_res.status_code == 200
    markdown_report = markdown_res.json()
    assert markdown_report["evaluation_run_id"] == created_run["id"]
    assert markdown_report["report_format"] == "markdown"
    assert markdown_report["content_type"] == "text/markdown; charset=utf-8"
    assert markdown_report["raw_text_included"] is False
    assert markdown_report["provider_call_performed"] is False
    assert markdown_report["external_write_performed"] is False
    assert markdown_report["summary"]["run_id"] == created_run["id"]
    assert "question_hash" in markdown_report["body"]
    assert "cust-report-001" in markdown_report["body"]
    assert "超过七天退货需要核对什么" not in markdown_report["body"]
    assert "raw_text_included=false" in markdown_report["body"]

    csv_res = client.get(
        f"/api/knowledge-evaluation-runs/{created_run['id']}/report?format=csv",
        headers=owner_headers,
    )
    assert csv_res.status_code == 200
    csv_report = csv_res.json()
    assert csv_report["report_format"] == "csv"
    assert csv_report["content_type"] == "text/csv; charset=utf-8"
    assert csv_report["filename"].endswith("_cases.csv")
    assert "question_hash" in csv_report["body"].splitlines()[0]
    assert "question," not in csv_report["body"].splitlines()[0]
    assert "超过七天退货需要核对什么" not in csv_report["body"]

    agent_role = client.post(
        f"/api/tenants/{tenant['id']}/roles",
        headers=owner_headers,
        json={"code": "agent", "name": "客服坐席"},
    ).json()
    agent = client.post(
        f"/api/tenants/{tenant['id']}/users",
        headers=owner_headers,
        json={"name": "客服坐席", "email": "knowledge-eval-report-api-agent@example.com", "password": "ChangeMe123!"},
    ).json()
    client.post(f"/api/users/{agent['id']}/roles", headers=owner_headers, json={"role_id": agent_role["id"]})
    agent_login = client.post(
        "/api/auth/login",
        json={
            "tenant_slug": tenant["slug"],
            "email": "knowledge-eval-report-api-agent@example.com",
            "password": "ChangeMe123!",
        },
    ).json()
    agent_res = client.get(
        f"/api/knowledge-evaluation-runs/{created_run['id']}/report",
        headers={"Authorization": f"Bearer {agent_login['access_token']}"},
    )
    assert agent_res.status_code == 403

    other_tenant, _, other_token = _bootstrap_user(
        client,
        slug="knowledge-eval-report-api-other",
        email="knowledge-eval-report-api-other@example.com",
        role_code="owner",
    )
    assert other_tenant["id"] != tenant["id"]
    cross_tenant_res = client.get(
        f"/api/knowledge-evaluation-runs/{created_run['id']}/report",
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert cross_tenant_res.status_code == 404


def test_agent_cannot_create_or_run_knowledge_evaluation_sets(client) -> None:
    tenant, _, owner_token = _bootstrap_user(
        client,
        slug="knowledge-eval-agent",
        email="knowledge-eval-agent-owner@example.com",
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
        json={"name": "客服坐席", "email": "knowledge-eval-agent@example.com", "password": "ChangeMe123!"},
    ).json()
    client.post(f"/api/users/{agent['id']}/roles", headers=owner_headers, json={"role_id": agent_role["id"]})
    login = client.post(
        "/api/auth/login",
        json={
            "tenant_slug": tenant["slug"],
            "email": "knowledge-eval-agent@example.com",
            "password": "ChangeMe123!",
        },
    ).json()
    agent_headers = {"Authorization": f"Bearer {login['access_token']}"}

    set_res = client.post(
        f"/api/tenants/{tenant['id']}/knowledge-evaluation-sets",
        headers=owner_headers,
        json={
            "name": "权限题集",
            "status": "active",
            "cases": [{"question": "保修期多久", "expected_terms": ["三年"]}],
        },
    )
    assert set_res.status_code == 201

    forbidden_create = client.post(
        f"/api/tenants/{tenant['id']}/knowledge-evaluation-sets",
        headers=agent_headers,
        json={
            "name": "坐席不能建题集",
            "status": "active",
            "cases": [{"question": "坐席能建吗", "expected_terms": ["不能"]}],
        },
    )
    assert forbidden_create.status_code == 403

    forbidden_run = client.post(
        f"/api/knowledge-evaluation-sets/{set_res.json()['id']}/runs",
        headers=agent_headers,
        json={"top_k": 3},
    )
    assert forbidden_run.status_code == 403
