import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = ROOT / "scripts" / "run_p3_02_rag_model_assisted_factuality_rehearsal.py"


def _load_script():
    spec = importlib.util.spec_from_file_location("run_p3_02_rag_model_assisted_factuality_rehearsal", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_p3_02_factuality_rehearsal_runs_without_external_actions(tmp_path: Path) -> None:
    module = _load_script()

    result = module.run_p3_02_factuality_rehearsal(
        knowledge_package_path=ROOT / "evals" / "p3_01_realistic_knowledge_package_template.json",
        eval_bank_path=ROOT / "evals" / "p3_01_realistic_customer_service_eval_bank_62_2026-06-27.csv",
        top_k=8,
        output_dir=tmp_path,
    )

    assert result["status"] == "completed"
    assert result["phase"] == "P3-02"
    assert result["raw_text_logged"] is False
    assert result["provider_call_performed"] is False
    assert result["external_platform_write_performed"] is False
    assert result["internal_database_write_performed"] is True
    assert result["evaluation_set"]["case_count"] == 62
    assert result["summary"]["total_cases"] == 62
    assert result["summary"]["answer_supported_by_citations_cases"] > 0
    assert result["summary"]["answer_requires_human_review_cases"] >= 25
    assert result["summary"]["manual_factuality_labels_collected"] == 0
    assert result["manual_review_contract"]["manual_factuality_label_required"] is True
    assert result["manual_review_contract"]["llm_judge_used"] is False
    assert {"supported", "partially_supported", "unsupported", "unsafe", "needs_policy"}.issuperset(
        result["summary"]["recommended_factuality_label_counts"]
    )

    first_case = result["cases"][0]
    assert "question_hash" in first_case
    assert "draft_hash" in first_case
    assert "question" not in first_case
    assert "draft_text" not in first_case
    assert first_case["manual_factuality_label_status"] == "pending_manual_review"

    serialized = json.dumps(result, ensure_ascii=False)
    assert "你们这个智能客服适合只有官网入口的小团队先试吗" not in serialized
    assert "根据已审核知识" not in serialized
    assert (tmp_path / "p3_02_factuality_rehearsal_summary.json").exists()
    assert (tmp_path / "p3_02_factuality_rehearsal.md").exists()
    assert (tmp_path / "p3_02_factuality_rehearsal_cases.csv").exists()


def test_p3_02_blocks_external_provider_without_explicit_allow() -> None:
    module = _load_script()

    result = module.run_p3_02_factuality_rehearsal(provider="bailian", allow_external_call=False, limit=2)

    assert result["status"] == "blocked_external_call_not_allowed"
    assert result["provider_call_performed"] is False
    assert result["raw_text_logged"] is False


def test_p3_02_requires_limit_for_external_provider_when_allowed() -> None:
    module = _load_script()

    result = module.run_p3_02_factuality_rehearsal(provider="bailian", allow_external_call=True, limit=None)

    assert result["status"] == "blocked_missing_limit_for_external_call"
    assert result["provider_call_performed"] is False
