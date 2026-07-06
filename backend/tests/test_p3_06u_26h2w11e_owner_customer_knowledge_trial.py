import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = ROOT / "scripts" / "check_p3_06u_26h2w11e_owner_customer_knowledge_trial.py"


def _load_script():
    spec = importlib.util.spec_from_file_location("check_p3_06u_26h2w11e_owner_customer_knowledge_trial", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_h2w11e_static_gate_requires_real_owner_login_and_customer_knowledge_trial(tmp_path: Path) -> None:
    module = _load_script()

    result = module.run_h2w11e_owner_customer_knowledge_trial_static_gate(output_dir=tmp_path)

    assert result["phase"] == "H2W-11E"
    assert result["status"] == "passed"
    assert result["blockers"] == []
    assert result["checks"]["uses_real_login_form"] is True
    assert result["checks"]["checks_customer_publish_actions"] is True
    assert result["checks"]["checks_linked_pages"] is True
    assert result["checks"]["verifies_server_persistence"] is True
    assert result["checks"]["updates_reality_matrix"] is True
    assert result["checks"]["updates_master_plan"] is True
    assert result["boundaries"]["external_platform_write_performed"] is False
    assert result["boundaries"]["real_platform_send_performed"] is False
    assert result["boundaries"]["formal_customer_signoff_performed"] is False
    assert result["boundaries"]["real_customer_data_used"] is False

    assert (tmp_path / "summary.json").exists()
