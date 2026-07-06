import csv
import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"


def _load_script(filename: str):
    sys.path.insert(0, str(SCRIPTS))
    spec = importlib.util.spec_from_file_location(filename.removesuffix(".py"), SCRIPTS / filename)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _nc18_summary(
    tmp_path: Path,
    status: str = "redteam_fact_ingest_ready_internal_sample_visible_to_llm_ops",
) -> Path:
    path = tmp_path / "nc18-summary.json"
    path.write_text(
        json.dumps(
            {
                "status": status,
                "llm_ops_redteam": {
                    "readiness": "ready_for_controlled_pilot",
                    "internal_sample_only": True,
                    "redteam_case_count": 25,
                    "redteam_labeled_cases": 25,
                },
            }
        ),
        encoding="utf-8",
    )
    return path


def test_nc19_generates_customer_redteam_report_flow_without_faking_signoff(tmp_path: Path) -> None:
    module = _load_script("check_p3_06u_26h2w_nc19_customer_redteam_report_flow.py")
    eval_dir = tmp_path / "evals"
    output_dir = tmp_path / "out"
    doc_path = tmp_path / "report.md"

    result = module.run_nc19_customer_redteam_report_flow_gate(
        eval_dir=eval_dir,
        output_dir=output_dir,
        nc18_summary_path=_nc18_summary(tmp_path),
        doc_path=doc_path,
    )

    assert result["status"] == "customer_redteam_report_flow_ready_waiting_customer_data"
    assert result["readiness"]["template_package_ready"] is True
    assert result["readiness"]["real_customer_redteam_case_bank_ready"] is False
    assert result["readiness"]["real_model_output_labels_ready"] is False
    assert result["readiness"]["formal_security_signoff_ready"] is False
    assert result["boundaries"]["customer_data_used"] is False
    assert result["boundaries"]["internal_sample_used"] is False
    assert result["upstream"]["nc18_fact_ingest_ready"] is True
    assert result["upstream"]["nc18_internal_sample_only"] is True
    assert "正式客户红队安全签收" in result["not_ready_for"]

    case_template = eval_dir / "customer_redteam_cases_template.csv"
    label_template = eval_dir / "customer_redteam_labeled_results_template.csv"
    manifest_template = eval_dir / "customer_redteam_manifest_template.json"
    report_template = output_dir / "customer_redteam_security_report_template.md"
    assert case_template.exists()
    assert label_template.exists()
    assert manifest_template.exists()
    assert report_template.exists()
    assert doc_path.exists()

    with case_template.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 5
    assert {row["category"] for row in rows} == {
        "prompt_injection",
        "jailbreak",
        "privacy_leak",
        "forbidden_commitment",
        "over_permission",
    }
    assert all(row["sample_row_only"] == "true" for row in rows)
    assert all(row["allow_auto_reply"] == "false" for row in rows)

    report_text = report_template.read_text(encoding="utf-8")
    assert "等待客户资料" in report_text
    assert "正式客户红队安全签收已完成" not in report_text


def test_nc19_blocks_without_nc18_redteam_fact_ingest(tmp_path: Path) -> None:
    module = _load_script("check_p3_06u_26h2w_nc19_customer_redteam_report_flow.py")

    result = module.run_nc19_customer_redteam_report_flow_gate(
        eval_dir=tmp_path / "evals",
        output_dir=tmp_path / "out",
        nc18_summary_path=_nc18_summary(tmp_path, status="blocked"),
        doc_path=tmp_path / "report.md",
    )

    assert result["status"] == "blocked"
    assert result["readiness"]["template_package_ready"] is False
    assert result["upstream"]["nc18_fact_ingest_ready"] is False
    assert any("NC18" in blocker for blocker in result["blockers"])
