#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PHASE = "H2W-PILOT7"
SCHEMA_VERSION = "p3-06u-26h2w-pilot7.co_creation_trial_readiness.v1"
DEFAULT_OUTPUT_DIR = ROOT / "output/p3_06u_26h2w_pilot7_co_creation_trial_readiness"
DOC_PATH = ROOT / "docs/P3-06U-26H2W_PILOT7_CO_CREATION_TRIAL_READINESS.md"

SUMMARY_SPECS = {
    "fe6": (
        ROOT / "output/p3_06u_26h2w_fe6_latest_frontend_browser_qa/summary.json",
        {"passed_latest_frontend_browser_qa"},
    ),
    "install4": (
        ROOT / "output/p3_06u_26h2w_install4_packaging_experience_gate/summary.json",
        {"native_packaging_experience_candidate_ready"},
    ),
    "kb3": (
        ROOT / "output/p3_06u_26h2w_kb3_customer_knowledge_center/summary.json",
        {"customer_knowledge_center_productized"},
    ),
    "pilot6": (
        ROOT / "output/p3_06u_26h2w_pilot6_handoff_archive_refresh/summary.json",
        {"pilot_handoff_archive_candidate_v1"},
    ),
    "ops2": (
        ROOT / "output/p3_06u_26h2w_ops2_customer_monthly_ops_report/summary.json",
        {"ready_for_customer_monthly_ops_report_rehearsal"},
    ),
    "pack5": (
        ROOT / "output/p3_06u_26h2w_pack5_customer_handoff_package/summary.json",
        {"ready_for_customer_local_pilot_handoff_candidate"},
    ),
    "kb2": (
        ROOT / "output/p3_06u_26h2w_kb2_post_import_retest_and_signoff_template/summary.json",
        {"ready_for_customer_specific_knowledge_retest_template"},
    ),
    "model1": (
        ROOT / "output/p3_06u_26h2w_model1_bailian_cost_sample/summary.json",
        {"passed_real_small_sample_cost_rehearsal", "guarded_external_call_not_allowed"},
    ),
    "trial1": (
        ROOT / "output/p3_06u_26h2w_trial1_internal_100q_rehearsal_report/summary.json",
        {"passed_internal_rehearsal_report", "passed_internal_rehearsal_report_with_open_gaps"},
    ),
}

NOT_READY_FOR = [
    "正式客户验收签收",
    "真实平台自动外发",
    "企业微信、公众号、抖音、淘宝、京东、拼多多等真实渠道接通",
    "生产 SLA 承诺",
    "已签名 dmg/exe 安装器",
    "RPA 或个人号外挂正式交付",
]


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
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


def _load_summary(name: str, path: Path, expected: set[str]) -> tuple[dict[str, Any], dict[str, Any], list[str]]:
    check = {
        "name": name,
        "path": _display_path(path),
        "present": path.exists(),
        "expected_statuses": sorted(expected),
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
    actual_status = str(payload.get("status") or "missing_status")
    check["actual_status"] = actual_status
    check["passed"] = actual_status in expected
    if not check["passed"]:
        return payload, check, [f"{name} 状态不满足：期望 {sorted(expected)}，实际 {actual_status}"]
    return payload, check, []


def _boundary_blockers(name: str, payload: dict[str, Any]) -> list[str]:
    checks = {
        "真实外发已接通或已执行": (
            _flag(payload, "readiness", "real_platform_send_ready") is True
            or _flag(payload, "boundaries", "real_platform_send_performed") is True
            or _flag(payload, "boundaries", "external_platform_write_performed") is True
        ),
        "客户正式签收已完成": (
            _flag(payload, "readiness", "formal_customer_signoff_ready") is True
            or _flag(payload, "readiness", "formal_accuracy_signoff") is True
            or _flag(payload, "boundaries", "formal_customer_signoff_performed") is True
        ),
        "签名安装包已完成": (
            _flag(payload, "readiness", "signed_dmg_exe_ready") is True
            or _flag(payload, "readiness", "desktop_installer_ready") is True
            or _flag(payload, "readiness", "native_installer_ready") is True
        ),
        "生产 SLA 已完成": (
            _flag(payload, "readiness", "production_sla_ready") is True
            or _flag(payload, "boundaries", "production_sla_ready") is True
        ),
        "RPA 正式交付已开启": (
            _flag(payload, "readiness", "rpa_formal_delivery_ready") is True
            or _flag(payload, "boundaries", "rpa_formal_delivery_enabled") is True
        ),
    }
    return [f"{name} 上游越界写成 ready 或已完成：{label}" for label, failed in checks.items() if failed]


def _customer_data_ready(payloads: dict[str, dict[str, Any]]) -> bool:
    pilot6 = payloads.get("pilot6", {})
    kb2 = payloads.get("kb2", {})
    trial1 = payloads.get("trial1", {})
    return (
        _flag(pilot6, "readiness", "pilot_handoff_archive_candidate_v1") is True
        and _flag(kb2, "signoff_boundary", "customer_confirmed") is True
        and _flag(trial1, "readiness", "customer_quality_report_candidate") is True
        and _flag(trial1, "boundaries", "internal_rehearsal_not_customer_signoff") is not True
    )


def _write_markdown(path: Path, result: dict[str, Any]) -> None:
    lines = [
        "# H2W-PILOT7 共创客户本地试跑封版总门禁",
        "",
        "## 结论",
        "",
        f"- 阶段状态：`{result['status']}`",
        f"- 阻断项：`{len(result['blockers'])}` 个",
        "",
        "## 上游证据",
        "",
    ]
    for check in result["checks"]:
        lines.append(f"- {check['name']}：`{check['actual_status']}`，`{check['path']}`")
    lines.extend(["", "## 不可承诺", ""])
    lines.extend(f"- {item}" for item in result["not_ready_for"])
    lines.extend(["", "## 阻断项", ""])
    lines.extend([f"- {item}" for item in result["blockers"]] or ["- 无"])
    lines.extend(
        [
            "",
            "## 固定边界",
            "",
            "- 这是共创客户本地试跑封版候选，不是正式客户验收。",
            "- 内部题库、内部确认文件和演练报告不能写成客户正式签收。",
            "- 真实外发、真实渠道、签名安装器和生产 SLA 继续保持关闭或未完成。",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_h2w_pilot7_co_creation_trial_readiness(
    *,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    doc_path: Path = DOC_PATH,
    summary_specs: dict[str, tuple[Path, set[str]]] = SUMMARY_SPECS,
) -> dict[str, Any]:
    blockers: list[str] = []
    checks: list[dict[str, Any]] = []
    payloads: dict[str, dict[str, Any]] = {}
    evidence_paths: list[str] = []

    for name, (path, expected) in summary_specs.items():
        payload, check, errors = _load_summary(name, path, expected)
        payloads[name] = payload
        checks.append(check)
        evidence_paths.append(check["path"])
        blockers.extend(errors)
        if payload:
            blockers.extend(_boundary_blockers(name, payload))

    if blockers:
        status = "blocked"
    elif _customer_data_ready(payloads):
        status = "co_creation_trial_candidate_ready_with_customer_data"
    else:
        status = "co_creation_trial_candidate_ready_with_internal_data"

    result = {
        "schema_version": SCHEMA_VERSION,
        "phase": PHASE,
        "status": status,
        "checks": checks,
        "blockers": sorted(set(blockers)),
        "boundaries": {
            "formal_customer_signoff_ready": False,
            "real_platform_send_ready": False,
            "signed_dmg_exe_ready": False,
            "production_sla_ready": False,
            "rpa_formal_delivery_enabled": False,
            "internal_rehearsal_not_customer_signoff": status != "co_creation_trial_candidate_ready_with_customer_data",
        },
        "readiness": {
            "co_creation_trial_candidate_ready": status != "blocked",
            "customer_data_ready": status == "co_creation_trial_candidate_ready_with_customer_data",
            "internal_data_only": status == "co_creation_trial_candidate_ready_with_internal_data",
            "formal_customer_signoff_ready": False,
            "real_platform_send_ready": False,
            "signed_dmg_exe_ready": False,
            "production_sla_ready": False,
        },
        "evidence_paths": evidence_paths,
        "not_ready_for": NOT_READY_FOR,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    _write_json(output_dir / "summary.json", result)
    _write_markdown(doc_path, result)
    return result


def main() -> int:
    result = run_h2w_pilot7_co_creation_trial_readiness()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] != "blocked" else 1


if __name__ == "__main__":
    raise SystemExit(main())
