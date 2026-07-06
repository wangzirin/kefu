import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = ROOT / "scripts" / "run_p2_25_chunk_backfill_eval_comparison.py"


def _load_comparison_script():
    spec = importlib.util.spec_from_file_location("run_p2_25_chunk_backfill_eval_comparison", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_p2_25_chunk_backfill_makes_full_evidence_recall_interpretable() -> None:
    module = _load_comparison_script()

    result = module.run_p2_25_chunk_backfill_eval_comparison(
        seed_documents_path=ROOT / "evals" / "p2_24_seed_knowledge_documents.json",
        eval_bank_path=ROOT / "evals" / "customer_service_eval_bank_synthetic_80_2026-06-26.csv",
        top_k=5,
        low_confidence_threshold=0.2,
    )

    assert result["status"] == "completed"
    assert result["phase"] == "P2-25"
    assert result["raw_text_logged"] is False
    assert result["provider_call_performed"] is False
    assert result["external_platform_write_performed"] is False
    assert result["baseline_run"]["summary_payload"]["full_evidence_cases"] == 0
    assert result["chunk_backfilled_run"]["summary_payload"]["full_evidence_cases"] >= 60
    assert result["chunk_backfill"]["bound_case_count"] >= 60
    assert result["comparison"]["full_evidence_case_delta"] >= 60
    assert result["chunk_backfilled_run"]["summary_payload"]["full_evidence_recall_at_5"] is not None
    assert result["reports"]["markdown"]["raw_text_included"] is False
    assert result["reports"]["csv"]["external_write_performed"] is False
    assert "标准版和专业版有什么区别" not in result["reports"]["markdown"]["body_preview"]
    assert result["chunk_backfill"]["case_catalog_sample"][0]["question_hash"]
    assert "question" not in result["chunk_backfill"]["case_catalog_sample"][0]
