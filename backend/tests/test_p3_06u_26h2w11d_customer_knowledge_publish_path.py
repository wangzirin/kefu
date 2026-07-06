import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = ROOT / "scripts" / "check_p3_06u_26h2w11d_customer_knowledge_publish_path.py"


def _load_script():
    spec = importlib.util.spec_from_file_location("check_p3_06u_26h2w11d_customer_knowledge_publish_path", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_h2w11d_static_gate_links_frontend_publish_path_to_repaired_quality_evidence(tmp_path: Path) -> None:
    module = _load_script()

    result = module.run_h2w11d_customer_knowledge_publish_path_static_gate(output_dir=tmp_path)

    assert result["phase"] == "H2W-11D"
    assert result["status"] == "passed"
    assert result["blockers"] == []
    assert result["frontend"]["customer_publish_path_marker"] is True
    assert result["frontend"]["action_count"] >= 7
    assert result["frontend"]["uses_quality_report_state"] is True
    assert result["frontend"]["uses_signoff_state"] is True
    assert result["frontend"]["uses_evaluation_state"] is True
    assert result["h2w11b"]["summary_status"] == "completed"
    assert result["h2w11b"]["report_status"] == "controlled_trial_ready"
    assert result["h2w11b"]["report_confidence_score"] == 90
    assert result["h2w11b"]["case_card_count"] == 62
    assert result["h2w11b"]["expected_term_document_coverage_after"] == 1.0
    assert result["boundaries"]["external_platform_write_performed"] is False
    assert result["boundaries"]["real_platform_send_performed"] is False
    assert result["boundaries"]["formal_customer_signoff_performed"] is False

    assert (tmp_path / "summary.json").exists()
