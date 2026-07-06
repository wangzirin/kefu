import importlib.util
import json
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
EVAL_FIXTURE = ROOT / "evals/p3_06u_26h2w_nc17_redteam_shadow_trial"


def _load_script(filename: str):
    sys.path.insert(0, str(SCRIPTS))
    spec = importlib.util.spec_from_file_location(filename.removesuffix(".py"), SCRIPTS / filename)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _copy_eval_fixture(tmp_path: Path) -> Path:
    target = tmp_path / "evals"
    shutil.copytree(EVAL_FIXTURE, target)
    return target


def _nc17_summary(
    tmp_path: Path,
    status: str = "redteam_shadow_trial_internal_sample_ready_not_customer_security_signoff",
) -> Path:
    path = tmp_path / "nc17-summary.json"
    path.write_text(json.dumps({"status": status}), encoding="utf-8")
    return path


def test_nc18_ingests_nc17_redteam_pack_into_llm_ops_fact_tables(tmp_path: Path) -> None:
    module = _load_script("check_p3_06u_26h2w_nc18_redteam_fact_ingest.py")
    eval_dir = _copy_eval_fixture(tmp_path)

    result = module.run_nc18_redteam_fact_ingest_gate(
        eval_dir=eval_dir,
        output_dir=tmp_path / "out",
        nc17_summary_path=_nc17_summary(tmp_path),
        doc_path=tmp_path / "report.md",
    )

    assert result["status"] == "redteam_fact_ingest_ready_internal_sample_visible_to_llm_ops"
    assert result["metrics"]["imported_case_count"] == 25
    assert result["metrics"]["imported_label_count"] == 25
    assert result["metrics"]["pilot_fact_written"] is True
    assert result["llm_ops_redteam"]["source"] == "database_evaluation_tables"
    assert result["llm_ops_redteam"]["redteam_case_count"] == 25
    assert result["llm_ops_redteam"]["redteam_labeled_cases"] == 25
    assert result["llm_ops_redteam"]["readiness"] == "ready_for_controlled_pilot"
    assert result["llm_ops_redteam"]["internal_sample_cases"] == 25
    assert result["llm_ops_redteam"]["internal_sample_only"] is True
    assert result["readiness"]["frontend_existing_card_can_display"] is True
    assert result["boundaries"]["raw_attack_vector_persisted"] is False
    assert result["boundaries"]["real_model_call_performed"] is False
    assert result["boundaries"]["real_platform_send_enabled"] is False
    assert result["database_fact"]["fact_key"] == "h2w_nc18_redteam_fact_ingest"
    assert "诱导忽略客服规则" not in json.dumps(result, ensure_ascii=False)
    assert (tmp_path / "out/summary.json").exists()
    assert (tmp_path / "report.md").exists()


def test_nc18_blocks_when_nc17_shadow_trial_is_not_ready(tmp_path: Path) -> None:
    module = _load_script("check_p3_06u_26h2w_nc18_redteam_fact_ingest.py")
    eval_dir = _copy_eval_fixture(tmp_path)

    result = module.run_nc18_redteam_fact_ingest_gate(
        eval_dir=eval_dir,
        output_dir=tmp_path / "out",
        nc17_summary_path=_nc17_summary(tmp_path, status="blocked"),
        doc_path=tmp_path / "report.md",
    )

    assert result["status"] == "blocked"
    assert result["metrics"]["imported_case_count"] == 0
    assert result["readiness"]["nc17_redteam_shadow_trial_ready"] is False
    assert result["readiness"]["database_evaluation_cases_ready"] is False
    assert any("NC17" in blocker for blocker in result["blockers"])
