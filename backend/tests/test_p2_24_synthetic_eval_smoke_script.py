import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = ROOT / "scripts" / "run_p2_24_synthetic_eval_smoke.py"


def _load_smoke_script():
    spec = importlib.util.spec_from_file_location("run_p2_24_synthetic_eval_smoke", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_p2_24_synthetic_eval_smoke_runs_without_external_actions() -> None:
    module = _load_smoke_script()

    result = module.run_p2_24_synthetic_eval_smoke(
        seed_documents_path=ROOT / "evals" / "p2_24_seed_knowledge_documents.json",
        eval_bank_path=ROOT / "evals" / "customer_service_eval_bank_synthetic_80_2026-06-26.csv",
        top_k=5,
        low_confidence_threshold=0.2,
    )

    assert result["status"] == "completed"
    assert result["raw_text_logged"] is False
    assert result["provider_call_performed"] is False
    assert result["external_platform_write_performed"] is False
    assert result["internal_database_write_performed"] is True
    assert result["seed_document_count"] >= 9
    assert result["seed_chunk_count"] >= 9
    assert result["evaluation_set"]["case_count"] == 80
    assert result["run"]["total_cases"] == 80
    assert result["run"]["hit_rate"] >= 0.75
    assert result["run"]["citation_coverage"] >= 0.75
    assert result["run"]["human_review_correctness"] >= 0.65
    assert result["run"]["forbidden_term_hits"] == 0
    assert result["run"]["unsupported_answer_rate"] is None
    assert result["run"]["summary_payload"]["unsupported_answer_rate_measured"] is False
    assert result["reports"]["markdown"]["raw_text_included"] is False
    assert result["reports"]["csv"]["raw_text_included"] is False
    assert result["reports"]["markdown"]["provider_call_performed"] is False
    assert result["reports"]["csv"]["external_write_performed"] is False
    assert "标准版和专业版有什么区别" not in result["reports"]["markdown"]["body_preview"]
    assert "cs-syn-001" in result["case_catalog_sample"][0]["external_case_id"]
    assert "question_hash" in result["case_catalog_sample"][0]
