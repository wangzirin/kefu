import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = ROOT / "scripts" / "check_p3_06u_26h2w11f_customer_terms_and_path_consolidation.py"


def _load_script():
    spec = importlib.util.spec_from_file_location(
        "check_p3_06u_26h2w11f_customer_terms_and_path_consolidation",
        SCRIPT_PATH,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_h2w11f_static_gate_consolidates_customer_terms_without_new_capability(tmp_path: Path) -> None:
    module = _load_script()

    result = module.run_h2w11f_customer_terms_and_path_consolidation_gate(output_dir=tmp_path)

    assert result["phase"] == "H2W-11F"
    assert result["status"] == "passed"
    assert result["blockers"] == []
    assert result["checks"]["new_customer_terms_present"] is True
    assert result["checks"]["legacy_terms_absent_from_customer_sections"] is True
    assert result["checks"]["h2w11e_browser_gate_updated"] is True
    assert result["checks"]["reality_matrix_updated"] is True
    assert result["checks"]["docs_updated"] is True
    assert result["legacy_found"] == {}
    assert result["boundaries"]["external_platform_write_performed"] is False
    assert result["boundaries"]["real_platform_send_performed"] is False
    assert result["boundaries"]["formal_customer_signoff_performed"] is False
    assert result["boundaries"]["new_backend_capability_added"] is False

    assert (tmp_path / "summary.json").exists()
