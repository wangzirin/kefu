import csv
import importlib.util
import json
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[2] / "scripts" / "export_customer_service_eval_report.py"


def _load_export_script():
    spec = importlib.util.spec_from_file_location("export_customer_service_eval_report", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sample_run_payload() -> dict:
    return {
        "id": 77,
        "tenant_id": 1,
        "evaluation_set_id": 9,
        "run_mode": "customer_service_retrieval",
        "retrieval_mode": "hybrid_bm25_vector_rerank_v1",
        "vector_engine": "deterministic_local_hash_embedding_v1",
        "total_cases": 2,
        "answered_cases": 1,
        "no_hit_cases": 1,
        "passed_cases": 1,
        "failed_cases": 1,
        "needs_review_cases": 1,
        "citation_covered_cases": 1,
        "expected_term_covered_cases": 1,
        "hit_rate": 0.5,
        "citation_coverage": 0.5,
        "expected_term_coverage": 0.5,
        "average_confidence": 0.74,
        "unsupported_answer_rate": None,
        "summary_payload": {
            "evaluation_scope": "customer_service_retrieval_only",
            "full_evidence_recall_at_5": 1.0,
            "citation_precision": 0.5,
            "human_review_correctness": 1.0,
            "knowledge_gap_rate": 0.5,
            "forbidden_term_hits": 0,
            "customer_service_metrics_version": "p2_22_customer_service_retrieval_v1",
        },
        "case_results": [
            {
                "id": 1,
                "tenant_id": 1,
                "evaluation_run_id": 77,
                "evaluation_case_id": 101,
                "question": "超过七天退货需要核对什么",
                "status": "passed",
                "top_score": 2.4,
                "top_confidence": 0.84,
                "top_chunk_id": 12,
                "top_document_id": 3,
                "citation_present": True,
                "expected_terms_found": True,
                "matched_terms": ["订单时间", "商品状态"],
                "failure_reason": "",
                "result_payload": {
                    "external_case_id": "cs-001",
                    "source_channel": "wecom",
                    "source_category": "售后政策",
                    "question_type": "policy_question",
                    "risk_level": "medium",
                    "expected_chunk_ids": [12],
                    "returned_chunk_ids_top_k": [12, 13],
                    "full_evidence_recalled_at_5": True,
                    "citation_precision": 1.0,
                    "expected_human_review": False,
                    "predicted_human_review": False,
                    "human_review_prediction_correct": True,
                    "allow_auto_reply": True,
                    "forbidden_term_hits": [],
                    "top_match": {
                        "source_uri": "internal://docs/after-sales-v1",
                        "document_title": "售后政策手册",
                        "content_preview": "这里是命中的知识片段原文，不应默认导出。",
                    },
                },
            },
            {
                "id": 2,
                "tenant_id": 1,
                "evaluation_run_id": 77,
                "evaluation_case_id": 102,
                "question": "客户要求马上赔偿百分百退款怎么办",
                "status": "needs_review",
                "top_score": 0.0,
                "top_confidence": 0.0,
                "top_chunk_id": None,
                "top_document_id": None,
                "citation_present": False,
                "expected_terms_found": False,
                "matched_terms": [],
                "failure_reason": "no_retrieval_hit",
                "result_payload": {
                    "external_case_id": "cs-002",
                    "source_channel": "wecom",
                    "source_category": "赔付投诉",
                    "question_type": "risk_handoff",
                    "risk_level": "high",
                    "expected_chunk_ids": [12, 13],
                    "returned_chunk_ids_top_k": [],
                    "full_evidence_recalled_at_5": False,
                    "citation_precision": 0.0,
                    "expected_human_review": True,
                    "predicted_human_review": True,
                    "human_review_prediction_correct": True,
                    "allow_auto_reply": False,
                    "forbidden_term_hits": [],
                    "top_match": None,
                },
            },
        ],
    }


def test_customer_service_eval_report_export_redacts_raw_text_by_default(tmp_path) -> None:
    input_path = tmp_path / "run.json"
    input_path.write_text(json.dumps(_sample_run_payload(), ensure_ascii=False), encoding="utf-8")

    script = _load_export_script()
    result = script.export_customer_service_eval_report(
        input_path=input_path,
        output_dir=tmp_path / "reports",
    )

    assert result["status"] == "exported"
    assert result["raw_text_logged"] is False
    assert result["provider_call_performed"] is False
    assert result["external_write_performed"] is False
    assert result["summary"]["total_cases"] == 2
    assert result["summary"]["knowledge_gap_cases"] == 1
    assert result["summary"]["human_review_correct_cases"] == 2

    csv_path = Path(result["csv_report_path"])
    markdown_path = Path(result["markdown_report_path"])
    csv_text = csv_path.read_text(encoding="utf-8")
    markdown_text = markdown_path.read_text(encoding="utf-8")
    combined = csv_text + markdown_text

    assert "超过七天退货需要核对什么" not in combined
    assert "客户要求马上赔偿百分百退款怎么办" not in combined
    assert "这里是命中的知识片段原文" not in combined
    assert "question_hash" in csv_text
    assert "原始问题默认不导出" in markdown_text

    with csv_path.open(encoding="utf-8", newline="") as file:
        rows = list(csv.DictReader(file))
    assert rows[0]["external_case_id"] == "cs-001"
    assert rows[0]["knowledge_gap"] == "false"
    assert rows[1]["external_case_id"] == "cs-002"
    assert rows[1]["knowledge_gap"] == "true"
    assert rows[1]["human_review_prediction_correct"] == "true"


def test_customer_service_eval_report_export_can_include_raw_text_when_explicit(tmp_path) -> None:
    input_path = tmp_path / "run.json"
    input_path.write_text(json.dumps({"run": _sample_run_payload()}, ensure_ascii=False), encoding="utf-8")

    script = _load_export_script()
    result = script.export_customer_service_eval_report(
        input_path=input_path,
        output_dir=tmp_path / "reports",
        include_raw_text=True,
    )

    assert result["status"] == "exported"
    assert result["raw_text_logged"] is True
    csv_text = Path(result["csv_report_path"]).read_text(encoding="utf-8")
    markdown_text = Path(result["markdown_report_path"]).read_text(encoding="utf-8")
    assert "超过七天退货需要核对什么" in csv_text
    assert "客户要求马上赔偿百分百退款怎么办" in markdown_text
