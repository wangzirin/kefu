#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PHASE = "H2W-INSTALL4"
SCHEMA_VERSION = "p3-06u-26h2w-install4.packaging_experience_gate.v1"
DEFAULT_OUTPUT_DIR = ROOT / "output/p3_06u_26h2w_install4_packaging_experience_gate"
DOC_PATH = ROOT / "docs/P3-06U-26H2W_INSTALL4_PACKAGING_EXPERIENCE_GATE.md"

INSTALL3_SUMMARY = ROOT / "output/p3_06u_26h2w_install3_native_app_packaging_gate/summary.json"
VERSION_FILE = ROOT / "installers/VERSION.json"
EXPERIENCE_CHECKLIST = ROOT / "installers/INSTALL4_EXPERIENCE_CHECKLIST.md"
LOGS_README = ROOT / "installers/logs/README.md"
MACOS_ICON_NOTES = ROOT / "installers/macos/APP_ICON_NOTES.md"
WINDOWS_ICON_NOTES = ROOT / "installers/windows/APP_ICON_NOTES.md"
MACOS_UNINSTALL = ROOT / "installers/macos/uninstall-notes.md"
WINDOWS_UNINSTALL = ROOT / "installers/windows/uninstall-notes.md"
MACOS_HEALTH = ROOT / "installers/macos/health-check.sh"
WINDOWS_HEALTH = ROOT / "installers/windows/HealthCheck-WanfaCustomerService.ps1"
MACOS_UPGRADE = ROOT / "installers/macos/prepare-upgrade-backup.sh"
WINDOWS_UPGRADE = ROOT / "installers/windows/Prepare-UpgradeBackup.ps1"

OVERCLAIM_PHRASES = [
    "正式 dmg 已完成",
    "正式 exe 已完成",
    "正式安装器已完成",
    "签名安装包已完成",
    "完整桌面安装器已完成",
    "真实外发已开启",
    "静默更新已开启",
    "远控客户电脑",
]

UNSAFE_PATTERNS = [
    "OUTBOX_EXTERNAL_WRITE_ENABLED=true",
    "TRUSTED_INBOUND_WORKER_ENABLED=true",
    "STANDARD_OPS_DEV_BOOTSTRAP_ENABLED=true",
    "ADMIN_BOOTSTRAP_PASSWORD=admin",
    "BAILIAN_API_KEY=",
    "DEEPSEEK_API_KEY=",
    "ACCESS_TOKEN=",
    "SECRET_KEY=",
]


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _contains_all(text: str, markers: list[str]) -> bool:
    return all(marker in text for marker in markers)


def _scan(paths: list[Path], patterns: list[str]) -> dict[str, list[str]]:
    findings: dict[str, list[str]] = {}
    for path in paths:
        text = _read_text(path)
        hits = [pattern for pattern in patterns if pattern in text]
        if hits:
            findings[_display_path(path)] = hits
    return findings


def _write_markdown(path: Path, result: dict[str, Any]) -> None:
    lines = [
        "# H2W-INSTALL4 安装候选体验门禁",
        "",
        "## 结论",
        "",
        f"- 阶段状态：`{result['status']}`",
        f"- 原生包装体验候选：`{str(result['readiness']['native_packaging_experience_candidate_ready']).lower()}`",
        f"- 已签名 dmg/exe：`{str(result['readiness']['signed_dmg_exe_ready']).lower()}`",
        "",
        "## 本阶段补强",
        "",
        "- 固定客户启动、健康检查、日志、升级前备份和卸载清理说明。",
        "- 固定 macOS / Windows 图标候选规范，但不生成正式图标或签名安装包。",
        "- 保持真实外发、静默更新、远控客户电脑和默认密码全部关闭。",
        "",
        "## 阻断项",
        "",
    ]
    lines.extend([f"- {item}" for item in result["blockers"]] or ["- 无"])
    lines.extend(
        [
            "",
            "## 固定边界",
            "",
            "- `signed_dmg_exe_ready=false`",
            "- `desktop_installer_ready=false`",
            "- `native_installer_ready=false`",
            "- `real_platform_send_ready=false`",
            "- `silent_update_ready=false`",
            "- `remote_control_ready=false`",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_h2w_install4_packaging_experience_gate(
    *,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    doc_path: Path = DOC_PATH,
    install3_summary: Path = INSTALL3_SUMMARY,
) -> dict[str, Any]:
    blockers: list[str] = []
    warnings: list[str] = []

    install3 = _read_json(install3_summary)
    if install3.get("status") != "native_app_packaging_candidate_ready":
        blockers.append(f"INSTALL3 上游状态不满足：{install3.get('status') or 'missing'}")

    version = _read_json(VERSION_FILE)
    boundaries = version.get("boundaries") if isinstance(version.get("boundaries"), dict) else {}
    checks = {
        "version_file_exists": VERSION_FILE.exists(),
        "version_keeps_install3_phase": version.get("phase") == "H2W-INSTALL3",
        "version_marks_install4_experience_phase": version.get("experience_phase") == PHASE,
        "signed_dmg_exe_ready_false": boundaries.get("signed_dmg_exe_ready") is False,
        "desktop_installer_ready_false": boundaries.get("desktop_installer_ready") is False,
        "native_installer_ready_false": boundaries.get("native_installer_ready") is False,
        "real_platform_send_ready_false": boundaries.get("real_platform_send_ready") is False,
        "silent_update_ready_false": boundaries.get("silent_update_ready") is False,
        "remote_control_ready_false": boundaries.get("remote_control_ready") is False,
        "experience_checklist_exists": EXPERIENCE_CHECKLIST.exists(),
        "experience_checklist_mentions_customer_env": _contains_all(_read_text(EXPERIENCE_CHECKLIST), ["deploy/customer.env", "首任负责人", "真实外发"]),
        "experience_checklist_keeps_signed_false": "signed_dmg_exe_ready=false" in _read_text(EXPERIENCE_CHECKLIST),
        "logs_readme_blocks_secrets": _contains_all(_read_text(LOGS_README), ["数据库密码", "模型 key", "平台 token", "客户原文"]),
        "macos_icon_notes_exists": MACOS_ICON_NOTES.exists() and "不生成正式 `.icns`" in _read_text(MACOS_ICON_NOTES),
        "windows_icon_notes_exists": WINDOWS_ICON_NOTES.exists() and "不生成正式 `.ico`" in _read_text(WINDOWS_ICON_NOTES),
        "macos_uninstall_notes_exist": MACOS_UNINSTALL.exists() and "清理前必须先导出备份" in _read_text(MACOS_UNINSTALL),
        "windows_uninstall_notes_exist": WINDOWS_UNINSTALL.exists() and "清理前必须先导出备份" in _read_text(WINDOWS_UNINSTALL),
        "macos_health_blocks_external_write": 'require_env_value "OUTBOX_EXTERNAL_WRITE_ENABLED" "false"' in _read_text(MACOS_HEALTH),
        "windows_health_blocks_external_write": 'Require-EnvValue "OUTBOX_EXTERNAL_WRITE_ENABLED" "false"' in _read_text(WINDOWS_HEALTH),
        "macos_upgrade_manifest_only": "database_backup_exported_by_this_script" in _read_text(MACOS_UPGRADE),
        "windows_upgrade_manifest_only": "database_backup_exported_by_this_script" in _read_text(WINDOWS_UPGRADE),
    }
    blockers.extend([f"INSTALL4 体验门禁不满足：{name}" for name, passed in checks.items() if not passed])

    scan_paths = [
        EXPERIENCE_CHECKLIST,
        LOGS_README,
        MACOS_ICON_NOTES,
        WINDOWS_ICON_NOTES,
        MACOS_UNINSTALL,
        WINDOWS_UNINSTALL,
        MACOS_HEALTH,
        WINDOWS_HEALTH,
        MACOS_UPGRADE,
        WINDOWS_UPGRADE,
    ]
    overclaims = _scan(scan_paths, OVERCLAIM_PHRASES)
    unsafe = _scan(scan_paths, UNSAFE_PATTERNS)
    for path, hits in overclaims.items():
        blockers.append(f"{path} 包含安装器越界承诺：{', '.join(hits)}")
    for path, hits in unsafe.items():
        blockers.append(f"{path} 包含不安全安装器配置：{', '.join(hits)}")

    result = {
        "schema_version": SCHEMA_VERSION,
        "phase": PHASE,
        "status": "blocked" if blockers else "native_packaging_experience_candidate_ready",
        "checks": checks,
        "blockers": sorted(set(blockers)),
        "warnings": warnings,
        "readiness": {
            "native_packaging_experience_candidate_ready": not blockers,
            "signed_dmg_exe_ready": False,
            "desktop_installer_ready": False,
            "native_installer_ready": False,
            "real_platform_send_ready": False,
            "silent_update_ready": False,
            "remote_control_ready": False,
        },
        "boundaries": {
            "secret_written_by_installer": False,
            "default_admin_password_created": False,
            "real_platform_send_performed": False,
            "silent_update_performed": False,
            "remote_control_performed": False,
        },
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    _write_json(output_dir / "summary.json", result)
    _write_markdown(doc_path, result)
    return result


def main() -> int:
    result = run_h2w_install4_packaging_experience_gate()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] != "blocked" else 1


if __name__ == "__main__":
    raise SystemExit(main())
