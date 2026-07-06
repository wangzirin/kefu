import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = ROOT / "scripts" / "check_p3_06u_26h2w11a_owner_rehearsal.py"


def _load_script():
    spec = importlib.util.spec_from_file_location("check_p3_06u_26h2w11a_owner_rehearsal", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_h2w11a_owner_rehearsal_runs_full_local_gate_without_external_actions(tmp_path: Path) -> None:
    module = _load_script()

    result = module.run_h2w11a_owner_rehearsal(output_dir=tmp_path)

    assert result["status"] == "completed"
    assert result["phase"] == "H2W-11A"
    assert result["ready_for_h2w11b"] is True
    assert result["blockers"] == []
    assert result["boundaries"]["real_customer_data_used"] is False
    assert result["boundaries"]["provider_call_performed"] is False
    assert result["boundaries"]["external_platform_write_performed"] is False
    assert result["boundaries"]["dev_bootstrap_login_used"] is False
    assert result["boundaries"]["real_password_login_used"] is True

    assert result["owner_login"]["checks"]["created_by_local_setup_owner_endpoint"] is True
    assert result["owner_login"]["checks"]["login_used_password_endpoint"] is True
    assert result["owner_login"]["setup_after"]["first_owner_creation_locked"] is True

    assert result["knowledge_package"]["document_count"] >= 7
    assert result["knowledge_package"]["chunk_count"] >= result["knowledge_package"]["document_count"]
    assert result["knowledge_package"]["safety"]["provider_call_performed"] is False
    assert result["knowledge_package"]["safety"]["external_write_performed"] is False

    assert result["question_bank"]["case_count"] == 62
    assert result["question_bank"]["coverage_summary"]["sensitive_row_count"] == 0
    assert result["evaluation"]["updated_run"]["total_cases"] == 62
    assert result["evaluation"]["updated_run"]["final_answer_sampled_cases"] == 62
    assert result["evaluation"]["final_answer_factuality_labeled_cases"] == 62
    assert result["customer_quality_report"]["signoff"]["signoff_status"] == "accepted_with_notes"
    assert result["customer_quality_report"]["signoff"]["formal_contract_signoff_performed"] is False

    assert (tmp_path / "summary.json").exists()
    assert result["output_files"]["evaluation_markdown"]["bytes"] > 0
    assert result["output_files"]["evaluation_csv"]["bytes"] > 0
    assert result["output_files"]["final_answer_labels_csv"]["bytes"] > 0
    assert result["output_files"]["customer_quality_report_html"]["bytes"] > 0

    serialized = json.dumps(result, ensure_ascii=False)
    assert "H2W11AOwner123!" not in serialized
    assert "access_token" not in serialized
    assert "你们这个智能客服适合只有官网入口的小团队先试吗" not in serialized
    assert "负责人确认本轮为受控演练证据" not in serialized
