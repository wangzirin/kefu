import csv
import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = ROOT / "scripts" / "check_p3_06u_26h2w11j_gap_final_answer_rehearsal.py"


def _load_script():
    spec = importlib.util.spec_from_file_location(
        "check_p3_06u_26h2w11j_gap_final_answer_rehearsal",
        SCRIPT_PATH,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_h2w11j_runs_gap_final_answer_rehearsal_without_claiming_signoff(tmp_path: Path) -> None:
    module = _load_script()
    samples = tmp_path / "samples.csv"
    labels = tmp_path / "labels.csv"

    result = module.run_h2w11j_gap_final_answer_rehearsal_gate(
        output_dir=tmp_path,
        sample_export_path=samples,
        label_export_path=labels,
    )

    assert result["phase"] == "H2W-11J"
    assert result["status"] == "passed"
    assert result["blockers"] == []
    assert result["metrics"]["case_count"] >= 7
    assert result["metrics"]["sample_count"] == result["metrics"]["case_count"]
    assert result["metrics"]["label_count"] == result["metrics"]["case_count"]
    assert result["metrics"]["auto_reply_factuality_rate"] == 1.0
    assert result["metrics"]["citation_sufficient_rate"] == 1.0
    assert result["metrics"]["forbidden_commitment_pass_rate"] == 1.0
    assert result["metrics"]["handoff_correct_rate"] == 1.0
    assert result["metrics"]["ready_for_gap_quality_report_review"] is True
    assert result["metrics"]["ready_for_formal_accuracy_signoff"] is False

    assert result["boundaries"]["provider_call_performed"] is False
    assert result["boundaries"]["real_platform_send_performed"] is False
    assert result["boundaries"]["external_platform_write_performed"] is False
    assert result["boundaries"]["final_answer_text_exported"] is False
    assert result["boundaries"]["gap_final_answer_rehearsal_performed"] is True
    assert result["boundaries"]["ready_for_formal_accuracy_signoff"] is False

    sample_rows = list(csv.DictReader(samples.open("r", encoding="utf-8", newline="")))
    label_rows = list(csv.DictReader(labels.open("r", encoding="utf-8", newline="")))
    assert len(sample_rows) == result["metrics"]["case_count"]
    assert len(label_rows) == result["metrics"]["case_count"]
    assert all(row["final_answer_sha256"] for row in sample_rows)
    assert all(row["final_answer_text_exported"] == "false" for row in sample_rows)
    assert all((row["final_answer_text"] or "") == "" for row in label_rows)
    assert all(row["customer_confirmed"] == "false" for row in label_rows)
    assert any(row["final_answer_factuality_status"] == "not_applicable" for row in label_rows)

    report = tmp_path / "gap_final_answer_rehearsal_report.md"
    assert report.exists()
    report_text = report.read_text(encoding="utf-8")
    assert "本地确定性 rehearsal" in report_text
    assert "不是正式客户准确率签收" in report_text
