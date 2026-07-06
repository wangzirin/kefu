import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = ROOT / "scripts" / "check_p3_06u_26h2w11h_standard_answer_quality_bridge.py"


def _load_script():
    spec = importlib.util.spec_from_file_location(
        "check_p3_06u_26h2w11h_standard_answer_quality_bridge",
        SCRIPT_PATH,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_h2w11h_bridge_report_exposes_standard_answer_gaps_without_signoff(tmp_path: Path) -> None:
    module = _load_script()

    result = module.run_h2w11h_standard_answer_quality_bridge_gate(output_dir=tmp_path)

    assert result["phase"] == "H2W-11H"
    assert result["status"] == "passed"
    assert result["blockers"] == []
    assert result["bridge"]["standard_answer_rows"] >= 10
    assert result["bridge"]["final_answer_label_rows"] >= 50
    assert result["bridge"]["matched_standard_answer_sources"] >= 2
    assert result["bridge"]["missing_standard_answer_sources_in_final_labels"]
    assert result["bridge"]["final_answer_text_exported_rows"] == 0
    assert result["formal_accuracy_gate"]["ready_for_formal_accuracy_signoff"] is False
    assert result["formal_accuracy_gate"]["blocking_reasons"]
    assert result["upstream"]["h2w11g_status"] == "passed"
    assert result["upstream"]["h2w11b_report_status"] == "controlled_trial_ready"
    assert result["boundaries"]["real_customer_data_used"] is False
    assert result["boundaries"]["real_platform_send_performed"] is False
    assert result["boundaries"]["final_answer_text_exported"] is False

    assert (tmp_path / "summary.json").exists()
    report = tmp_path / "standard_answer_quality_bridge_report.md"
    assert report.exists()
    assert "不是正式客户准确率签收" in report.read_text(encoding="utf-8")
