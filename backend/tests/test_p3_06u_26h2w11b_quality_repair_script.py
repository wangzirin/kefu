import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = ROOT / "scripts" / "check_p3_06u_26h2w11b_quality_repair.py"


def _load_script():
    spec = importlib.util.spec_from_file_location("check_p3_06u_26h2w11b_quality_repair", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_h2w11b_generates_repaired_package_and_reruns_rehearsal_without_external_actions(tmp_path: Path) -> None:
    module = _load_script()
    repaired_package_path = tmp_path / "repaired_knowledge_package.json"
    output_dir = tmp_path / "h2w11b"

    result = module.run_h2w11b_quality_repair(
        repaired_package_path=repaired_package_path,
        output_dir=output_dir,
    )

    assert result["phase"] == "H2W-11B"
    assert result["status"] in {"completed", "completed_with_remaining_quality_work"}
    assert result["blockers"] == []
    assert result["boundaries"]["provider_call_performed"] is False
    assert result["boundaries"]["external_platform_write_performed"] is False
    assert result["boundaries"]["real_platform_send_performed"] is False
    assert result["boundaries"]["real_customer_data_used"] is False

    alignment = result["knowledge_alignment"]
    assert alignment["repaired_package_exists"] is True
    assert alignment["source_reference_coverage_after"] == 1.0
    assert alignment["expected_term_document_coverage_after"] == 1.0
    assert alignment["case_card_count"] == 62
    assert alignment["question_text_included_in_repaired_package"] is False

    rerun = result["repaired_rehearsal"]
    assert rerun["status"] == "completed"
    assert rerun["evaluation"]["updated_run"]["total_cases"] == 62
    assert rerun["boundaries"]["provider_call_performed"] is False
    assert rerun["boundaries"]["external_platform_write_performed"] is False

    package = json.loads(repaired_package_path.read_text(encoding="utf-8"))
    assert len(package["documents"]) >= 7
    serialized_package = json.dumps(package, ensure_ascii=False)
    assert "题库覆盖卡" in serialized_package
    assert "禁用承诺：" not in serialized_package
    assert "你们这个智能客服适合只有官网入口的小团队先试吗" not in serialized_package

    serialized = json.dumps(result, ensure_ascii=False)
    assert "H2W11AOwner123!" not in serialized
    assert "access_token" not in serialized
    assert "你们这个智能客服适合只有官网入口的小团队先试吗" not in serialized
