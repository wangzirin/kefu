import csv
import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = ROOT / "scripts" / "check_p3_06u_26h2w11l_customer_standard_answer_confirmation_pack.py"


def _load_script():
    spec = importlib.util.spec_from_file_location(
        "check_p3_06u_26h2w11l_customer_standard_answer_confirmation_pack",
        SCRIPT_PATH,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_h2w11l_confirmation_pack_is_ready_but_not_formal_signoff(tmp_path: Path) -> None:
    module = _load_script()
    pack_path = tmp_path / "customer_standard_answer_confirmation_pack.csv"

    result = module.run_h2w11l_customer_standard_answer_confirmation_pack_gate(
        output_dir=tmp_path,
        confirmation_pack_path=pack_path,
    )

    assert result["phase"] == "H2W-11L"
    assert result["status"] == "passed"
    assert result["blockers"] == []
    assert result["metrics"]["confirmation_item_count"] >= 10
    assert result["metrics"]["gap_rehearsed_item_count"] >= 7
    assert result["metrics"]["customer_confirmed_item_count"] == 0
    assert result["readiness"]["ready_for_customer_standard_answer_confirmation_review"] is True
    assert result["readiness"]["ready_for_formal_accuracy_signoff"] is False
    assert result["boundaries"]["formal_customer_signoff_performed"] is False
    assert result["boundaries"]["real_platform_send_performed"] is False
    assert result["boundaries"]["provider_call_performed"] is False
    assert result["boundaries"]["final_answer_text_exported"] is False

    with pack_path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))

    assert rows
    assert all(row["needs_customer_confirmation"] == "true" for row in rows)
    assert all(row["customer_confirmed"] == "false" for row in rows)
    assert all(row["not_formal_signoff"] == "true" for row in rows)
    assert all(not row.get("customer_reviewer") for row in rows)
    assert all(not row.get("customer_confirmed_at") for row in rows)
    assert all("final_answer_text" not in row for row in rows)

    summary = tmp_path / "summary.json"
    report = tmp_path / "customer_standard_answer_confirmation_pack_review.md"
    assert summary.exists()
    assert report.exists()
    assert "不是电子签章" in report.read_text(encoding="utf-8")
