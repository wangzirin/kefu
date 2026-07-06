#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PHASE = "H2W-PILOT0"
SCHEMA_VERSION = "p3-06u-26h2w-pilot0.readiness_gate.v1"
DEFAULT_OUTPUT_DIR = ROOT / "output/p3_06u_26h2w_pilot0_readiness"
DOC_PATH = ROOT / "docs/P3-06U-26H2W_PILOT0_READINESS_LEDGER.md"

SUMMARY_SPECS = {
    "pack5": (
        ROOT / "output/p3_06u_26h2w_pack5_customer_handoff_package/summary.json",
        {"ready_for_customer_local_pilot_handoff_candidate"},
    ),
    "fe4": (
        ROOT / "output/p3_06u_26h2w_fe4_customer_ui_sealed_candidate/summary.json",
        {"ready_for_customer_visible_ui_candidate"},
    ),
    "kb2": (
        ROOT / "output/p3_06u_26h2w_kb2_post_import_retest_and_signoff_template/summary.json",
        {"ready_for_customer_specific_knowledge_retest_template"},
    ),
    "ops2": (
        ROOT / "output/p3_06u_26h2w_ops2_customer_monthly_ops_report/summary.json",
        {"ready_for_customer_monthly_ops_report_rehearsal"},
    ),
    "install2": (
        ROOT / "output/p3_06u_26h2w_install2_native_installer_readiness/summary.json",
        {"native_wrapper_candidate_ready"},
    ),
    "trial1": (
        ROOT / "output/p3_06u_26h2w_trial1_internal_100q_rehearsal_report/summary.json",
        {"passed_internal_rehearsal_report", "passed_internal_rehearsal_report_with_open_gaps"},
    ),
    "model1": (
        ROOT / "output/p3_06u_26h2w_model1_bailian_cost_sample/summary.json",
        {"passed_real_small_sample_cost_rehearsal", "guarded_external_call_not_allowed"},
    ),
    "runtime7d": (
        ROOT / "output/p3_06u_26h2w7d_runtime_pgvector_rehearsal/summary.json",
        {"ready_for_runtime_rehearsal"},
    ),
}


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _flag(payload: dict[str, Any], *path: str) -> Any:
    current: Any = payload
    for key in path:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def _load_summary(path: Path, expected_statuses: set[str], name: str) -> tuple[dict[str, Any], dict[str, Any], list[str]]:
    check = {
        "name": name,
        "path": _display_path(path),
        "present": path.exists(),
        "expected_statuses": sorted(expected_statuses),
        "actual_status": "missing",
        "passed": False,
    }
    if not path.exists():
        return {}, check, [f"{name} summary 缺失：{_display_path(path)}"]
    try:
        payload = _read_json(path)
    except json.JSONDecodeError:
        check["actual_status"] = "invalid_json"
        return {}, check, [f"{name} summary 不是有效 JSON：{_display_path(path)}"]
    actual = str(payload.get("status") or "missing_status")
    check["actual_status"] = actual
    check["passed"] = actual in expected_statuses
    if not check["passed"]:
        return payload, check, [f"{name} 状态不满足：期望 {sorted(expected_statuses)}，实际 {actual}"]
    return payload, check, []


def _boundary_blockers(name: str, payload: dict[str, Any]) -> list[str]:
    checks = {
        "真实平台自动外发": (
            _flag(payload, "readiness", "real_platform_send_ready") is True
            or _flag(payload, "boundaries", "real_platform_send_performed") is True
            or _flag(payload, "boundaries", "external_platform_write_performed") is True
        ),
        "正式客户签收": (
            _flag(payload, "readiness", "formal_customer_signoff_ready") is True
            or _flag(payload, "boundaries", "formal_customer_signoff_performed") is True
            or _flag(payload, "readiness", "formal_accuracy_signoff") is True
        ),
        "签名安装包": (
            _flag(payload, "readiness", "signed_dmg_exe_ready") is True
            or _flag(payload, "readiness", "desktop_installer_ready") is True
            or _flag(payload, "readiness", "native_installer_ready") is True
        ),
        "生产 SLA": (
            _flag(payload, "readiness", "production_sla_ready") is True
            or _flag(payload, "boundaries", "production_sla_ready") is True
        ),
        "远程控制或静默更新": (
            _flag(payload, "boundaries", "remote_control_performed") is True
            or _flag(payload, "boundaries", "silent_update_performed") is True
            or _flag(payload, "boundaries", "automatic_update_performed") is True
        ),
    }
    return [f"{name} 上游越界写成 ready 或已完成：{label}" for label, failed in checks.items() if failed]


def _customer_data_ready(payloads: dict[str, dict[str, Any]]) -> bool:
    kb2 = payloads.get("kb2", {})
    trial1 = payloads.get("trial1", {})
    return (
        _flag(kb2, "signoff_boundary", "customer_confirmed") is True
        and _flag(trial1, "readiness", "customer_quality_report_candidate") is True
        and _flag(trial1, "boundaries", "internal_rehearsal_not_customer_signoff") is not True
    )


def _write_markdown(path: Path, result: dict[str, Any]) -> None:
    lines = [
        "# H2W-PILOT0 试点封版事实账本",
        "",
        "## 结论",
        "",
        f"- 阶段状态：`{result['status']}`",
        f"- 输出口径：`{result['readiness_status']}`",
        f"- 阻断项：{len(result['blockers'])} 个",
        "",
        "## 上游证据",
        "",
    ]
    for check in result["checks"]:
        lines.append(
            f"- {check['name']}：`{check['actual_status']}`，期望 `{', '.join(check['expected_statuses'])}`，文件 `{check['path']}`"
        )
    lines.extend(
        [
            "",
            "## 继续保持 false 的能力",
            "",
        ]
    )
    lines.extend(f"- {item}" for item in result["not_ready_for"])
    if result["blockers"]:
        lines.extend(["", "## 阻断项", ""])
        lines.extend(f"- {item}" for item in result["blockers"])
    lines.extend(
        [
            "",
            "## 边界",
            "",
            "- 当前只允许输出共创客户本地试点包候选，不写成熟商用全渠道客服系统。",
            "- 内部演练数据不能写成客户正式签收。",
            "- 真实外发、真实渠道、生产 SLA 和签名安装器仍需另开专项。",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_h2w_pilot0_readiness(
    *,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    doc_path: Path = DOC_PATH,
    summary_specs: dict[str, tuple[Path, set[str]]] = SUMMARY_SPECS,
) -> dict[str, Any]:
    blockers: list[str] = []
    checks: list[dict[str, Any]] = []
    payloads: dict[str, dict[str, Any]] = {}
    for name, (path, expected) in summary_specs.items():
        payload, check, errors = _load_summary(path, expected, name)
        payloads[name] = payload
        checks.append(check)
        blockers.extend(errors)
        if payload:
            blockers.extend(_boundary_blockers(name, payload))

    if blockers:
        readiness_status = "blocked"
    elif _customer_data_ready(payloads):
        readiness_status = "pilot_candidate_ready_with_customer_data"
    else:
        readiness_status = "pilot_candidate_ready_with_internal_data"

    result = {
        "schema_version": SCHEMA_VERSION,
        "phase": PHASE,
        "status": "blocked" if blockers else readiness_status,
        "readiness_status": readiness_status,
        "checks": checks,
        "blockers": sorted(set(blockers)),
        "not_ready_for": [
            "正式客户验收签收",
            "真实平台自动外发",
            "企业微信、抖音、淘宝、京东、拼多多等真实渠道接通",
            "生产 SLA 承诺",
            "已签名 dmg/exe 安装器",
        ],
        "readiness": {
            "pilot_candidate_ready": not blockers,
            "customer_data_ready": readiness_status == "pilot_candidate_ready_with_customer_data",
            "internal_data_only": readiness_status == "pilot_candidate_ready_with_internal_data",
            "real_platform_send_ready": False,
            "formal_customer_signoff_ready": readiness_status == "pilot_candidate_ready_with_customer_data",
            "signed_dmg_exe_ready": False,
            "production_sla_ready": False,
        },
        "boundaries": {
            "real_platform_send_performed": False,
            "rpa_formal_delivery_enabled": False,
            "remote_control_performed": False,
            "silent_update_performed": False,
            "internal_rehearsal_not_customer_signoff": readiness_status != "pilot_candidate_ready_with_customer_data",
        },
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    _write_json(output_dir / "summary.json", result)
    _write_markdown(doc_path, result)
    return result


def main() -> int:
    result = run_h2w_pilot0_readiness()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] != "blocked" else 1


if __name__ == "__main__":
    raise SystemExit(main())
