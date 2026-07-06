import csv
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


def _nc16_summary(tmp_path: Path, status: str = "redteam_closure_gate_ready_internal_fixtures_only") -> Path:
    path = tmp_path / "nc16-summary.json"
    path.write_text(json.dumps({"status": status}), encoding="utf-8")
    return path


def _copy_eval_fixture(tmp_path: Path) -> Path:
    target = tmp_path / "evals"
    shutil.copytree(EVAL_FIXTURE, target)
    return target


def test_nc17_redteam_shadow_trial_accepts_internal_sample_package(tmp_path: Path) -> None:
    module = _load_script("check_p3_06u_26h2w_nc17_redteam_shadow_trial.py")
    eval_dir = _copy_eval_fixture(tmp_path)

    result = module.run_nc17_redteam_shadow_trial_gate(
        eval_dir=eval_dir,
        output_dir=tmp_path / "out",
        nc16_summary_path=_nc16_summary(tmp_path),
        doc_path=tmp_path / "report.md",
    )

    assert result["status"] == "redteam_shadow_trial_internal_sample_ready_not_customer_security_signoff"
    assert result["metrics"]["case_count"] == 25
    assert result["metrics"]["label_count"] == 25
    assert set(result["metrics"]["category_counts"].values()) == {5}
    assert result["metrics"]["handoff_correct_rate"] == 1.0
    assert result["metrics"]["forbidden_commitment_pass_rate"] == 1.0
    assert result["metrics"]["citation_sufficient_rate"] == 1.0
    assert result["metrics"]["unsafe_label_count"] == 0
    assert result["readiness"]["formal_security_signoff_ready"] is False
    assert result["readiness"]["real_model_call_performed"] is False
    assert result["boundaries"]["customer_data_used"] is False
    assert result["boundaries"]["internal_sample_used"] is True
    assert (tmp_path / "out/summary.json").exists()
    assert (tmp_path / "report.md").exists()


def test_nc17_redteam_shadow_trial_blocks_without_nc16_ready(tmp_path: Path) -> None:
    module = _load_script("check_p3_06u_26h2w_nc17_redteam_shadow_trial.py")
    eval_dir = _copy_eval_fixture(tmp_path)

    result = module.run_nc17_redteam_shadow_trial_gate(
        eval_dir=eval_dir,
        output_dir=tmp_path / "out",
        nc16_summary_path=_nc16_summary(tmp_path, status="blocked"),
        doc_path=tmp_path / "report.md",
    )

    assert result["status"] == "blocked"
    assert result["readiness"]["nc16_closure_rule_ready"] is False
    assert any("NC16" in blocker for blocker in result["blockers"])


def test_nc17_redteam_shadow_trial_blocks_label_mismatch(tmp_path: Path) -> None:
    module = _load_script("check_p3_06u_26h2w_nc17_redteam_shadow_trial.py")
    eval_dir = _copy_eval_fixture(tmp_path)
    label_file = eval_dir / "redteam_labeled_shadow_results.csv"
    rows = list(csv.DictReader(label_file.read_text(encoding="utf-8").splitlines()))
    rows[0]["case_id"] = "rt-nc17-unknown"
    with label_file.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    result = module.run_nc17_redteam_shadow_trial_gate(
        eval_dir=eval_dir,
        output_dir=tmp_path / "out",
        nc16_summary_path=_nc16_summary(tmp_path),
        doc_path=tmp_path / "report.md",
    )

    assert result["status"] == "blocked"
    assert any("缺少标签" in blocker for blocker in result["blockers"])
    assert any("未知样本" in blocker for blocker in result["blockers"])
