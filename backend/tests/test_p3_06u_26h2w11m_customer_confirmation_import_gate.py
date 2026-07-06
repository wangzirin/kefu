import csv
import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = ROOT / "scripts" / "check_p3_06u_26h2w11m_customer_confirmation_import_gate.py"


def _load_script():
    spec = importlib.util.spec_from_file_location(
        "check_p3_06u_26h2w11m_customer_confirmation_import_gate",
        SCRIPT_PATH,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_h2w11m_generates_return_template_without_faking_customer_confirmation(tmp_path: Path) -> None:
    module = _load_script()
    template_path = tmp_path / "customer_confirmation_return_template.csv"
    missing_return_file = tmp_path / "customer_confirmation_return_received.csv"

    result = module.run_h2w11m_customer_confirmation_import_gate(
        output_dir=tmp_path,
        return_template_path=template_path,
        return_file_path=missing_return_file,
    )

    assert result["phase"] == "H2W-11M"
    assert result["status"] == "passed"
    assert result["blockers"] == []
    assert result["readiness"]["customer_return_file_present"] is False
    assert result["readiness"]["ready_for_customer_return_collection"] is True
    assert result["readiness"]["ready_for_confirmed_standard_answer_import"] is False
    assert result["readiness"]["ready_for_formal_accuracy_signoff"] is False
    assert result["boundaries"]["customer_confirmation_fabricated"] is False
    assert result["boundaries"]["real_platform_send_performed"] is False

    with template_path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))

    assert rows
    assert len(rows) == result["metrics"]["expected_item_count"]
    assert all(row["customer_decision"] == "pending" for row in rows)
    assert all(row["customer_confirmed"] == "false" for row in rows)
    assert all(row["not_formal_signoff"] == "true" for row in rows)
    assert all(not row["customer_reviewer"] for row in rows)
    assert all(not row["customer_confirmed_at"] for row in rows)

    summary = tmp_path / "summary.json"
    review = tmp_path / "customer_confirmation_import_gate_review.md"
    assert summary.exists()
    assert review.exists()
    assert "不伪造客户确认" in review.read_text(encoding="utf-8")


def test_h2w11m_accepts_complete_customer_return_but_still_blocks_formal_signoff(tmp_path: Path) -> None:
    module = _load_script()
    template_path = tmp_path / "customer_confirmation_return_template.csv"
    return_file = tmp_path / "customer_confirmation_return_received.csv"

    first_result = module.run_h2w11m_customer_confirmation_import_gate(
        output_dir=tmp_path,
        return_template_path=template_path,
        return_file_path=return_file,
    )
    assert first_result["status"] == "passed"

    with template_path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))

    for row in rows:
        row["customer_decision"] = "approved"
        row["customer_confirmed"] = "true"
        row["customer_reviewer"] = "业务负责人A"
        row["customer_reviewer_role"] = "业务负责人"
        row["customer_confirmed_at"] = "2026-07-04T10:00:00+08:00"

    with return_file.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=module.RETURN_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    result = module.run_h2w11m_customer_confirmation_import_gate(
        output_dir=tmp_path,
        return_template_path=template_path,
        return_file_path=return_file,
    )

    assert result["status"] == "passed"
    assert result["blockers"] == []
    assert result["readiness"]["customer_return_file_present"] is True
    assert result["readiness"]["ready_for_confirmed_standard_answer_import"] is True
    assert result["readiness"]["ready_for_formal_accuracy_signoff"] is False
    assert result["metrics"]["all_items_approved"] is True
    assert result["metrics"]["customer_confirmed_item_count"] == len(rows)
    assert (tmp_path / "validated_customer_confirmation_return.csv").exists()
