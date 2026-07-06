import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = ROOT / "scripts" / "check_p3_06u_26h2w11k_customer_report_gap_rehearsal.py"


def _load_script():
    spec = importlib.util.spec_from_file_location(
        "check_p3_06u_26h2w11k_customer_report_gap_rehearsal",
        SCRIPT_PATH,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_h2w11k_customer_report_includes_gap_rehearsal_without_claiming_signoff(tmp_path: Path) -> None:
    module = _load_script()

    result = module.run_h2w11k_customer_report_gap_rehearsal_gate(output_dir=tmp_path)

    assert result["phase"] == "H2W-11K"
    assert result["status"] == "passed"
    assert result["blockers"] == []
    assert result["metrics"]["upstream_case_count"] >= 7
    assert result["metrics"]["ready_for_gap_quality_report_review"] is True
    assert result["metrics"]["ready_for_formal_accuracy_signoff"] is False

    assert result["boundaries"]["customer_report_gap_rehearsal_evidence_added"] is True
    assert result["boundaries"]["formal_customer_signoff_performed"] is False
    assert result["boundaries"]["real_platform_send_performed"] is False
    assert result["boundaries"]["provider_call_performed"] is False
    assert result["boundaries"]["final_answer_text_exported"] is False

    summary = tmp_path / "summary.json"
    assert summary.exists()
    text = summary.read_text(encoding="utf-8")
    assert "正式准确率签收" in text
    assert "真实题库" in text
