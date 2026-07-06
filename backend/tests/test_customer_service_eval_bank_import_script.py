import csv
import importlib.util
import json
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[2] / "scripts" / "import_customer_service_eval_bank.py"
SYNTHETIC_BANK_PATH = (
    Path(__file__).resolve().parents[2] / "evals" / "customer_service_eval_bank_synthetic_80_2026-06-26.csv"
)
P3_REALISTIC_BANK_PATH = (
    Path(__file__).resolve().parents[2] / "evals" / "p3_01_realistic_customer_service_eval_bank_62_2026-06-27.csv"
)
P3_06U_26F_TEMPLATE_PATH = (
    Path(__file__).resolve().parents[2] / "evals" / "p3_06u_26f_real_customer_eval_bank_template.csv"
)


def _load_import_script():
    spec = importlib.util.spec_from_file_location("import_customer_service_eval_bank", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_customer_service_eval_bank_csv_dry_run_builds_payload_without_logging_raw_questions(tmp_path) -> None:
    csv_path = tmp_path / "customer_eval_bank.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "external_case_id",
                "source_channel",
                "source_category",
                "question",
                "question_type",
                "expected_terms",
                "expected_source_uri",
                "expected_document_title",
                "expected_chunk_ids",
                "must_have_all_evidence",
                "expected_human_review",
                "allow_auto_reply",
                "forbidden_terms",
                "risk_level",
                "required_citation",
                "priority",
                "status",
                "annotation_notes",
            ],
        )
        writer.writeheader()
        writer.writerow(
            {
                "external_case_id": "cs-001",
                "source_channel": "wecom",
                "source_category": "售后政策",
                "question": "超过七天退货需要核对什么",
                "question_type": "policy_question",
                "expected_terms": "订单时间;商品状态",
                "expected_source_uri": "internal://docs/after-sales-v1",
                "expected_document_title": "售后政策手册",
                "expected_chunk_ids": "12;13",
                "must_have_all_evidence": "true",
                "expected_human_review": "false",
                "allow_auto_reply": "true",
                "forbidden_terms": "马上赔偿;百分百退款",
                "risk_level": "medium",
                "required_citation": "true",
                "priority": "20",
                "status": "active",
                "annotation_notes": "脱敏样例。",
            }
        )

    script = _load_import_script()
    result = script.run_customer_service_eval_bank_import(
        input_path=csv_path,
        name="客服脱敏题库",
        description="50-100 题正式导入前的样例。",
    )

    assert result["status"] == "validated"
    assert result["raw_text_logged"] is False
    assert result["provider_call_performed"] is False
    assert result["summary"]["total_cases"] == 1
    assert result["summary"]["risk_level_counts"] == {"medium": 1}
    assert result["payload"]["evaluation_mode"] == "customer_service_retrieval"
    assert result["payload"]["cases"][0]["external_case_id"] == "cs-001"
    assert result["payload"]["cases"][0]["expected_terms"] == ["订单时间", "商品状态"]
    assert result["payload"]["cases"][0]["expected_chunk_ids"] == [12, 13]
    dumped_summary = json.dumps(
        {
            "summary": result["summary"],
            "case_catalog": result["case_catalog"],
        },
        ensure_ascii=False,
    )
    assert "超过七天退货需要核对什么" not in dumped_summary
    assert "question_hash" in result["case_catalog"][0]


def test_customer_service_eval_bank_blocks_high_confidence_pii_by_default(tmp_path) -> None:
    csv_path = tmp_path / "customer_eval_bank_pii.csv"
    csv_path.write_text(
        "\n".join(
            [
                "external_case_id,question,expected_terms",
                "cs-pii-001,我的手机号是13812345678你帮我查一下订单,订单",
            ]
        ),
        encoding="utf-8",
    )

    script = _load_import_script()
    result = script.run_customer_service_eval_bank_import(
        input_path=csv_path,
        name="含隐私题库",
    )

    assert result["status"] == "blocked_sensitive_rows"
    assert result["payload"] is None
    assert result["summary"]["sensitive_row_count"] == 1
    assert result["raw_text_logged"] is False
    dumped = json.dumps(result, ensure_ascii=False)
    assert "13812345678" not in dumped
    assert "我的手机号" not in dumped


def test_synthetic_customer_service_eval_bank_fixture_is_validated_without_external_actions() -> None:
    script = _load_import_script()
    result = script.run_customer_service_eval_bank_import(
        input_path=SYNTHETIC_BANK_PATH,
        name="P2-23 合成脱敏客户客服验收题库 80题",
        description="真实业务语境的合成脱敏题库，不含真实客户身份或真实订单资料。",
    )

    assert result["status"] == "validated"
    assert result["raw_text_logged"] is False
    assert result["provider_call_performed"] is False
    assert result["external_write_performed"] is False
    assert result["summary"]["total_cases"] == 80
    assert result["summary"]["sensitive_row_count"] == 0
    assert result["summary"]["raw_question_text_in_summary"] is False
    assert len(result["summary"]["source_channel_counts"]) >= 8
    assert result["summary"]["question_type_counts"]["knowledge_gap"] == 4
    assert result["summary"]["question_type_counts"]["b2b_integration"] == 8
    assert result["summary"]["risk_level_counts"]["critical"] == 3
    assert result["summary"]["human_review_expected_cases"] >= 50
    assert result["summary"]["auto_reply_blocked_cases"] >= 50
    assert result["payload"]["evaluation_mode"] == "customer_service_retrieval"
    assert result["payload"]["cases"][0]["external_case_id"] == "cs-syn-001"
    assert result["payload"]["cases"][-1]["external_case_id"] == "cs-syn-080"

    summary_dump = json.dumps(
        {"summary": result["summary"], "case_catalog": result["case_catalog"]},
        ensure_ascii=False,
    )
    assert "你们标准版和专业版主要差在哪" not in summary_dump
    assert "直播间临时口播承诺" not in summary_dump
    assert "question_hash" in summary_dump


def test_p3_realistic_customer_service_eval_bank_fixture_is_validated_without_external_actions() -> None:
    script = _load_import_script()
    result = script.run_customer_service_eval_bank_import(
        input_path=P3_REALISTIC_BANK_PATH,
        name="P3-01 真实客户式试点题库样例 62题",
        description="用于验证 P3-01 真实脱敏题库字段、分布和脱敏 dry-run 的客户式样例，不含真实客户身份或真实订单资料。",
    )

    assert result["status"] == "validated"
    assert result["raw_text_logged"] is False
    assert result["provider_call_performed"] is False
    assert result["external_write_performed"] is False
    assert result["summary"]["total_cases"] == 62
    assert result["summary"]["sensitive_row_count"] == 0
    assert result["summary"]["raw_question_text_in_summary"] is False
    assert 50 <= result["summary"]["total_cases"] <= 100
    assert len(result["summary"]["source_channel_counts"]) >= 6
    assert result["summary"]["question_type_counts"]["pre_sales_consultation"] == 10
    assert result["summary"]["question_type_counts"]["pricing_package"] == 8
    assert result["summary"]["question_type_counts"]["delivery_deployment"] == 8
    assert result["summary"]["question_type_counts"]["after_sales_refund"] == 8
    assert result["summary"]["question_type_counts"]["account_invoice_security"] == 6
    assert result["summary"]["question_type_counts"]["channel_compliance"] == 8
    assert result["summary"]["question_type_counts"]["risk_legal"] == 6
    assert result["summary"]["question_type_counts"]["knowledge_gap"] == 4
    assert result["summary"]["question_type_counts"]["smalltalk_guardrail"] == 4
    assert result["summary"]["risk_level_counts"]["critical"] == 3
    assert result["summary"]["human_review_expected_cases"] >= 25
    assert result["summary"]["auto_reply_blocked_cases"] >= 25
    assert result["payload"]["evaluation_mode"] == "customer_service_retrieval"
    assert result["payload"]["cases"][0]["external_case_id"] == "p3-realistic-001"
    assert result["payload"]["cases"][-1]["external_case_id"] == "p3-realistic-062"

    summary_dump = json.dumps(
        {"summary": result["summary"], "case_catalog": result["case_catalog"]},
        ensure_ascii=False,
    )
    assert "你们这个智能客服适合只有官网入口的小团队先试吗" not in summary_dump
    assert "客户说因为机器人回答导致他损失了钱要我们赔" not in summary_dump
    assert "question_hash" in summary_dump


def test_p3_06u_26f_real_customer_template_alias_fields_are_supported() -> None:
    script = _load_import_script()
    result = script.run_customer_service_eval_bank_import(
        input_path=P3_06U_26F_TEMPLATE_PATH,
        name="P3-06U-26F 真实客户题库模板样例",
        description="用于验证 customer_question expected_answer business_object 等客户交付字段。",
    )

    assert result["status"] == "validated"
    assert result["raw_text_logged"] is False
    assert result["provider_call_performed"] is False
    assert result["external_write_performed"] is False
    assert result["summary"]["total_cases"] == 8
    assert result["summary"]["sensitive_row_count"] == 0
    assert result["summary"]["p3_06u_26f_real_customer_template_supported"] is True
    assert result["summary"]["expected_answer_rows"] == 8
    assert result["summary"]["business_object_cases"] == 8
    assert result["summary"]["source_reference_covered_cases"] == 8
    assert result["payload"]["evaluation_mode"] == "customer_service_retrieval"
    assert result["payload"]["cases"][0]["question"] == "我们只有官网吗 可以先不接别的平台吗"
    assert result["payload"]["cases"][0]["expected_terms"] == ["官网客服", "受控试点", "人工接管"]
    assert result["payload"]["cases"][0]["expected_source_uri"] == "internal://docs/p3/product-scope-v1"
    assert result["payload"]["cases"][2]["expected_human_review"] is True
    assert result["payload"]["cases"][2]["allow_auto_reply"] is False
    assert result["payload"]["cases"][2]["forbidden_terms"] == ["私下转账", "绕过平台", "保证优惠"]
    assert "expected_answer_hash=" in result["payload"]["cases"][0]["annotation_notes"]
    assert "business_object_hash=" in result["payload"]["cases"][0]["annotation_notes"]

    summary_dump = json.dumps(
        {"summary": result["summary"], "case_catalog": result["case_catalog"]},
        ensure_ascii=False,
    )
    assert "我们只有官网吗" not in summary_dump
    assert "可以先选择官网客服作为受控试点入口" not in summary_dump
    assert result["case_catalog"][0]["expected_answer_present"] is True
    assert result["case_catalog"][0]["business_object_present"] is True
    assert result["case_catalog"][0]["source_reference_present"] is True
