from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import shutil


ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = ROOT / "scripts" / "check_p3_05c_channel_autoreply_readiness.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("check_p3_05c_channel_autoreply_readiness", SCRIPT_PATH)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _copy_required_tree(tmp_path: Path) -> Path:
    root = tmp_path / "standard_ops"
    (root / "docs").mkdir(parents=True)
    (root / "backend" / "app" / "services").mkdir(parents=True)
    (root / "backend" / "app" / "workers").mkdir(parents=True)

    for relative in [
        "docs/channel_autoreply_readiness_matrix.json",
        "docs/P3-05C_OFFICIAL_CHANNEL_AUTOREPLY_READINESS.md",
        "backend/app/services/channel_provider_registry.py",
        "backend/app/services/channel_connectors.py",
        "backend/app/workers/outbox_sender.py",
        ".env.example",
    ]:
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, target)
    return root


def test_p3_05c_current_project_passes() -> None:
    module = _load_module()

    result = module.run_check(ROOT)

    assert result["status"] == "passed"
    assert result["production_autoreply_ready_count"] == 0
    assert result["real_external_write_enabled"] is False
    assert result["external_platform_write_performed"] is False
    assert result["channel_count"] >= 9


def test_p3_05c_rejects_marking_pinduoduo_ready(tmp_path: Path) -> None:
    module = _load_module()
    root = _copy_required_tree(tmp_path)
    matrix_path = root / "docs" / "channel_autoreply_readiness_matrix.json"
    matrix = json.loads(matrix_path.read_text(encoding="utf-8"))
    for channel in matrix["channels"]:
        if channel["provider"] == "pinduoduo":
            channel["official_autoreply_feasibility"] = "confirmed_yes"
            channel["production_autoreply_ready"] = True
    matrix_path.write_text(json.dumps(matrix, ensure_ascii=False, indent=2), encoding="utf-8")

    result = module.run_check(root)

    assert result["status"] == "failed"
    joined = "\n".join(result["errors"])
    assert "pinduoduo must remain not_publicly_verified" in joined
    assert "pinduoduo must not be marked production_autoreply_ready" in joined


def test_p3_05c_rejects_external_write_enabled_by_default(tmp_path: Path) -> None:
    module = _load_module()
    root = _copy_required_tree(tmp_path)
    env_path = root / ".env.example"
    env_text = env_path.read_text(encoding="utf-8").replace(
        "OUTBOX_EXTERNAL_WRITE_ENABLED=false",
        "OUTBOX_EXTERNAL_WRITE_ENABLED=true",
    )
    env_path.write_text(env_text, encoding="utf-8")

    result = module.run_check(root)

    assert result["status"] == "failed"
    assert ".env.example must default OUTBOX_EXTERNAL_WRITE_ENABLED=false" in result["errors"]
