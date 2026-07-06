#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PHASE = "H2W-NC2"
SCHEMA_VERSION = "p3-06u-26h2w-nc2.customer_mode_hardening.v1"
OUTPUT_DIR = ROOT / "output/p3_06u_26h2w_nc2_customer_mode_hardening"
DOC_PATH = ROOT / "docs/P3-06U-26H2W_NC2_CUSTOMER_MODE_HARDENING.md"

AUTH_PATH = ROOT / "backend/app/api/auth.py"
DIAGNOSTICS_PATH = ROOT / "backend/app/services/diagnostics.py"
PACK_COMMON_PATH = ROOT / "scripts/lib/h2w_pack8_common.py"
HANDOFF_SCRIPT_PATHS = [
    ROOT / "scripts/check_p3_06u_26h2w_pilot3_handoff_archive.py",
    ROOT / "scripts/check_p3_06u_26h2w_pilot6_handoff_archive_refresh.py",
    ROOT / "scripts/check_p3_06u_26h2w_pack7_trial_handoff_archive_v2.py",
    PACK_COMMON_PATH,
]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_doc(path: Path, result: dict[str, Any]) -> None:
    lines = [
        "# H2W-NC2 客户模式安全硬化",
        "",
        "## 结论",
        "",
        f"- 阶段状态：`{result['status']}`",
        "- 范围：客户本地试跑安全门禁，不打开真实外发，不做真实渠道，不生成签名安装包。",
        "",
        "## 已纳入门禁",
        "",
    ]
    for key, value in result["checks"].items():
        lines.append(f"- {key}：`{value}`")
    lines.extend(["", "## 阻断项", ""])
    lines.extend([f"- {item}" for item in result["blockers"]] or ["- 无"])
    lines.extend(
        [
            "",
            "## 边界",
            "",
            "- 真实平台外发仍关闭。",
            "- 真实渠道闭环仍未完成。",
            "- 诊断包只允许客户主动手动传输，坏包只保存拒收摘要。",
            "- 交付档案禁止包含浏览器 profile、Cookies、History、Login Data、`.git`、`node_modules`。",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_nc2_gate() -> dict[str, Any]:
    blockers: list[str] = []
    auth = _read(AUTH_PATH)
    diagnostics = _read(DIAGNOSTICS_PATH)
    pack_common = _read(PACK_COMMON_PATH)

    checks = {
        "login_failure_limit_present": "LOGIN_FAILURE_LIMIT" in auth and "_login_cooldowns" in auth,
        "login_failure_audit_present": "auth.login_failed" in auth and "email_sha256" in auth,
        "local_owner_safety_blockers_present": "local deployment safety blockers" in auth
        and "_local_setup_safety_blockers" in auth,
        "customer_mode_me_requires_development_for_bootstrap": 'settings.env.strip().lower() != "development"' in auth,
        "diagnostic_package_size_gate_present": "MAX_DIAGNOSTIC_UPLOAD_PACKAGE_BYTES" in diagnostics,
        "diagnostic_package_depth_gate_present": "MAX_DIAGNOSTIC_UPLOAD_PACKAGE_DEPTH" in diagnostics,
        "diagnostic_schema_allowlist_present": "ALLOWED_UPLOAD_PACKAGE_KEYS" in diagnostics
        and "ALLOWED_DIAGNOSTIC_BUNDLE_KEYS" in diagnostics,
        "diagnostic_rejected_payload_summary_only": "rejected_upload_summary_only" in diagnostics
        and "original_payload_not_persisted" in diagnostics,
        "diagnostic_storage_redaction_present": "_sanitize_diagnostic_storage_value" in diagnostics
        and "payload_redacted_for_storage" in diagnostics,
        "pack_common_forbids_browser_sensitive_files": all(
            marker in pack_common for marker in ["Cookies", "History", "Login Data", "browser-profile"]
        ),
    }
    for path in HANDOFF_SCRIPT_PATHS:
        text = _read(path)
        key = f"{path.name}_forbids_browser_sensitive_files"
        checks[key] = all(marker in text for marker in ["Cookies", "History", "Login Data"])

    for name, passed in checks.items():
        if not passed:
            blockers.append(f"{name} 未通过")

    status = "customer_mode_security_hardening_ready" if not blockers else "blocked"
    result = {
        "schema_version": SCHEMA_VERSION,
        "phase": PHASE,
        "status": status,
        "blockers": sorted(set(blockers)),
        "checks": checks,
        "readiness": {
            "customer_mode_security_hardening_ready": not blockers,
            "dev_bootstrap_available_in_customer_mode": False,
            "diagnostic_bad_package_raw_payload_persisted": False,
            "handoff_archive_allows_browser_profile": False,
            "real_platform_send_ready": False,
            "signed_dmg_exe_ready": False,
            "formal_customer_signoff_ready": False,
        },
        "boundaries": {
            "real_platform_send_ready": False,
            "real_channel_closed_loop_ready": False,
            "signed_dmg_exe_ready": False,
            "formal_customer_signoff_ready": False,
        },
        "not_ready_for": [
            "真实平台外发",
            "真实渠道闭环",
            "签名 dmg/exe 安装器",
            "正式客户验收签收",
        ],
        "evidence_paths": [
            str(AUTH_PATH.relative_to(ROOT)),
            str(DIAGNOSTICS_PATH.relative_to(ROOT)),
            str(PACK_COMMON_PATH.relative_to(ROOT)),
            str(DOC_PATH.relative_to(ROOT)),
            str((OUTPUT_DIR / "summary.json").relative_to(ROOT)),
        ],
    }
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    _write_json(OUTPUT_DIR / "summary.json", result)
    _write_doc(DOC_PATH, result)
    return result


def main() -> int:
    result = run_nc2_gate()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] != "blocked" else 1


if __name__ == "__main__":
    raise SystemExit(main())
