import csv
import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = ROOT / "scripts" / "check_p3_06u_26h2w11i_standard_answer_gap_eval_plan.py"


def _load_script():
    spec = importlib.util.spec_from_file_location(
        "check_p3_06u_26h2w11i_standard_answer_gap_eval_plan",
        SCRIPT_PATH,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_h2w11i_generates_gap_eval_input_without_claiming_signoff(tmp_path: Path) -> None:
    module = _load_script()
    gap_cases = tmp_path / "gap_cases.csv"
    label_plan = tmp_path / "label_plan.csv"

    result = module.run_h2w11i_standard_answer_gap_eval_plan_gate(
        output_dir=tmp_path,
        gap_eval_cases_path=gap_cases,
        gap_label_plan_path=label_plan,
    )

    assert result["phase"] == "H2W-11I"
    assert result["status"] == "passed"
    assert result["blockers"] == []
    assert result["coverage"]["missing_source_count_from_h2w11h"] >= 6
    assert result["coverage"]["gap_eval_case_rows"] >= result["coverage"]["missing_source_count_from_h2w11h"]
    assert result["coverage"]["covered_missing_source_count"] == result["coverage"]["missing_source_count_from_h2w11h"]
    assert result["coverage"]["missing_sources_without_candidate"] == []
    assert result["coverage"]["ready_for_next_final_answer_eval_run"] is True
    assert result["coverage"]["ready_for_formal_accuracy_signoff"] is False
    assert result["boundaries"]["real_customer_data_used"] is False
    assert result["boundaries"]["real_platform_send_performed"] is False
    assert result["boundaries"]["final_answer_text_exported"] is False
    assert result["boundaries"]["final_answer_eval_run_performed"] is False
    assert result["boundaries"]["ready_for_formal_accuracy_signoff"] is False

    rows = list(csv.DictReader(gap_cases.open("r", encoding="utf-8", newline="")))
    labels = list(csv.DictReader(label_plan.open("r", encoding="utf-8", newline="")))
    assert len(rows) == result["coverage"]["gap_eval_case_rows"]
    assert len(labels) == result["coverage"]["gap_label_plan_rows"]
    assert all(row["standard_answer_sha256"] for row in rows)
    assert all(row["customer_confirmed"] == "false" for row in rows)
    assert all(row["final_answer_text_must_not_be_exported"] == "true" for row in labels)

    report = tmp_path / "standard_answer_gap_eval_plan.md"
    assert report.exists()
    report_text = report.read_text(encoding="utf-8")
    assert "不是正式客户准确率签收" in report_text
    assert "不代表下一轮评测已经执行" in report_text
