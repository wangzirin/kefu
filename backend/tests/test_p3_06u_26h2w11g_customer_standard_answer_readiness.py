import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = ROOT / "scripts" / "check_p3_06u_26h2w11g_customer_standard_answer_readiness.py"


def _load_script():
    spec = importlib.util.spec_from_file_location(
        "check_p3_06u_26h2w11g_customer_standard_answer_readiness",
        SCRIPT_PATH,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_h2w11g_standard_answer_gate_keeps_accuracy_signoff_honest(tmp_path: Path) -> None:
    module = _load_script()

    result = module.run_h2w11g_customer_standard_answer_readiness_gate(output_dir=tmp_path)

    assert result["phase"] == "H2W-11G"
    assert result["status"] == "passed"
    assert result["blockers"] == []
    assert result["metrics"]["row_count"] >= 10
    assert result["metrics"]["handoff_count"] >= 2
    assert result["metrics"]["auto_reply_count"] >= 6
    assert result["upstream"]["h2w11f_status"] == "passed"
    assert result["upstream"]["h2w11b_report_status"] == "controlled_trial_ready"
    assert result["readiness"]["ready_for_customer_standard_answer_collection"] is True
    assert result["readiness"]["ready_for_formal_accuracy_signoff"] is False
    assert result["readiness"]["raw_question_text_required"] is False
    assert result["readiness"]["real_customer_confirmation_required_next"] is True
    assert result["boundaries"]["real_customer_data_used"] is False
    assert result["boundaries"]["external_platform_write_performed"] is False
    assert result["boundaries"]["real_platform_send_performed"] is False

    assert (tmp_path / "summary.json").exists()
