import csv
import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"


def _load_script(filename: str):
    sys.path.insert(0, str(SCRIPTS))
    spec = importlib.util.spec_from_file_location(filename.removesuffix(".py"), SCRIPTS / filename)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_real_eval_bank(path: Path, *, rows: int = 50) -> None:
    fieldnames = [
        "external_case_id",
        "source_channel",
        "source_category",
        "question",
        "expected_answer",
        "business_object",
        "must_include",
        "must_not_include",
        "handoff_expected",
        "allow_auto_reply",
        "source_reference",
        "risk_level",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for index in range(rows):
            writer.writerow(
                {
                    "external_case_id": f"real-case-{index + 1:03d}",
                    "source_channel": "wecom",
                    "source_category": "售前咨询",
                    "question": f"客户询问第 {index + 1} 个试点问题，已脱敏。",
                    "expected_answer": f"按试点资料回答第 {index + 1} 个问题，说明交付范围和人工边界。",
                    "business_object": f"试点套餐 {index % 5 + 1}",
                    "must_include": "交付范围；人工边界",
                    "must_not_include": "百分百保证；无限服务",
                    "handoff_expected": "false",
                    "allow_auto_reply": "true",
                    "source_reference": f"internal://customer-knowledge/package-{index % 7 + 1}",
                    "risk_level": "low",
                }
            )


def test_h2w11n_waits_for_real_customer_return_without_faking_confirmation(tmp_path: Path) -> None:
    module = _load_script("check_p3_06u_26h2w11n_customer_confirmation_import.py")

    result = module.run_h2w11n_customer_confirmation_import(
        output_dir=tmp_path,
        return_file_path=tmp_path / "missing_customer_return.csv",
    )

    assert result["status"] == "waiting_for_customer_return"
    assert result["readiness"]["customer_return_file_present"] is False
    assert result["readiness"]["ready_for_confirmed_standard_answer_import"] is False
    assert result["readiness"]["ready_for_formal_accuracy_signoff"] is False
    assert result["boundaries"]["customer_confirmation_fabricated"] is False
    assert (tmp_path / "summary.json").exists()


def test_h2w11o_and_11p_accept_real_sized_desensitized_bank(tmp_path: Path) -> None:
    bank = tmp_path / "real_customer_bank.csv"
    _write_real_eval_bank(bank, rows=50)

    h2w11o = _load_script("check_p3_06u_26h2w11o_real_customer_eval_bank_import.py")
    h2w11o_output = tmp_path / "h2w11o"
    o_result = h2w11o.run_h2w11o_real_customer_eval_bank_import(
        input_file=bank,
        output_dir=h2w11o_output,
    )

    assert o_result["status"] == "passed"
    assert o_result["readiness"]["ready_for_final_answer_sampling"] is True
    assert o_result["metrics"]["row_count"] == 50
    assert o_result["metrics"]["sensitive_row_count"] == 0
    assert o_result["boundaries"]["raw_question_text_exported"] is False

    h2w11p = _load_script("check_p3_06u_26h2w11p_final_answer_sampling.py")
    p_result = h2w11p.run_h2w11p_final_answer_sampling(
        input_file=bank,
        h2w11o_summary=h2w11o_output / "summary.json",
        output_dir=tmp_path / "h2w11p",
    )

    assert p_result["status"] == "passed"
    assert p_result["metrics"]["sample_count"] == 50
    assert p_result["metrics"]["final_answer_factuality_rate"] == 1.0
    assert p_result["metrics"]["citation_sufficient_rate"] == 1.0
    assert p_result["readiness"]["ready_for_customer_quality_report_candidate"] is True
    assert p_result["readiness"]["ready_for_formal_accuracy_signoff"] is False
    assert p_result["boundaries"]["final_answer_text_exported"] is False


def test_h2w10a_waits_for_real_wecom_console_conditions(monkeypatch, tmp_path: Path) -> None:
    module = _load_script("check_p3_06u_26h2w10a_wecom_official_sandbox_readiness.py")
    for key in [
        "WECOM_CORP_ID",
        "WECOM_TOKEN",
        "WECOM_ENCODING_AES_KEY",
        "WECOM_SANDBOX_RECEIVER_ID",
        "WECOM_SANDBOX_TOKEN",
        "WECOM_SANDBOX_ENCODING_AES_KEY",
        "WECOM_CALLBACK_URL",
        "PUBLIC_HTTPS_CALLBACK_URL",
        "WECOM_TRUSTED_IP_CONFIRMED",
    ]:
        monkeypatch.delenv(key, raising=False)

    result = module.run_h2w10a_wecom_official_sandbox_readiness(output_dir=tmp_path)

    assert result["status"] == "waiting_for_official_sandbox_conditions"
    assert result["readiness"]["provider_contract_ready"] is True
    assert result["readiness"]["external_write_kill_switch_ready"] is True
    assert result["readiness"]["ready_for_official_sandbox_run"] is False
    assert result["boundaries"]["real_platform_send_performed"] is False
    assert result["boundaries"]["secret_values_logged"] is False


def test_h2w7d_requires_real_bank_and_postgres_before_production_switch(tmp_path: Path, monkeypatch) -> None:
    module = _load_script("check_p3_06u_26h2w7d_production_retrieval_evidence.py")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("KNOWLEDGE_VECTOR_STORE", raising=False)

    result = module.run_h2w7d_production_retrieval_evidence(
        output_dir=tmp_path,
        h2w11o_summary=tmp_path / "missing_h2w11o_summary.json",
    )

    assert result["status"] == "blocked_waiting_for_real_bank_or_postgres"
    assert result["readiness"]["pgvector_code_ready"] is True
    assert result["readiness"]["ann_strategy_ready"] is True
    assert result["readiness"]["ready_for_production_retrieval_switch"] is False
    assert result["boundaries"]["sqlite_json_disguised_as_production_vector_store"] is False
    assert result["boundaries"]["production_retrieval_path_switched"] is False
