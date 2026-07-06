import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = ROOT / "scripts" / "run_p2_26_retrieval_quality_comparison.py"


def _load_comparison_script():
    spec = importlib.util.spec_from_file_location("run_p2_26_retrieval_quality_comparison", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_p2_26_compares_retrieval_top_k_without_external_actions(tmp_path: Path) -> None:
    module = _load_comparison_script()

    result = module.run_p2_26_retrieval_quality_comparison(
        seed_documents_path=ROOT / "evals" / "p2_24_seed_knowledge_documents.json",
        eval_bank_path=ROOT / "evals" / "customer_service_eval_bank_synthetic_80_2026-06-26.csv",
        top_ks=(5, 8, 10),
        low_confidence_threshold=0.2,
        output_dir=tmp_path,
    )

    assert result["status"] == "completed"
    assert result["phase"] == "P2-26"
    assert result["raw_text_logged"] is False
    assert result["provider_call_performed"] is False
    assert result["external_platform_write_performed"] is False
    assert result["internal_database_write_performed"] is True
    assert result["chunk_backfill"]["bound_case_count"] >= 60

    runs_by_top_k = {item["top_k"]: item for item in result["runs"]}
    assert set(runs_by_top_k) == {5, 8, 10}
    baseline = runs_by_top_k[5]
    best = result["best_run"]
    assert baseline["total_cases"] == 80
    assert baseline["full_evidence_cases"] >= 60
    assert baseline["full_evidence_recall_at_k"] >= 0.5
    assert best["top_k"] in {5, 8, 10}
    assert best["full_evidence_recall_at_k"] >= baseline["full_evidence_recall_at_k"]
    assert max(item["full_evidence_recall_at_k"] for item in result["runs"]) >= baseline["full_evidence_recall_at_k"]
    assert result["recommendation"]["candidate_default_top_k"] == 8
    assert result["recommendation"]["candidate_recall_pool_top_k"] in {10, 12}

    case_delta = result["case_delta"]
    assert case_delta["baseline_top_k"] == 5
    assert case_delta["initial_failed_case_count"] > 0
    assert case_delta["baseline_failed_recovered_count"] >= 0
    assert case_delta["still_missing_case_count"] >= 0
    assert "question" not in (case_delta["improved_cases"][0] if case_delta["improved_cases"] else {})
    assert "question_hash" in case_delta["failed_case_sample"][0]

    assert result["reports"]["best_markdown"]["raw_text_included"] is False
    assert result["reports"]["best_csv"]["external_write_performed"] is False
    assert "标准版和专业版有什么区别" not in result["reports"]["best_markdown"]["body_preview"]

    serialized = json.dumps(result, ensure_ascii=False)
    assert "标准版和专业版有什么区别" not in serialized
    assert (tmp_path / "p2_26_retrieval_quality_comparison_summary.json").exists()
    assert (tmp_path / "p2_26_retrieval_quality_comparison.md").exists()
    assert (tmp_path / "p2_26_failed_case_delta.csv").exists()
