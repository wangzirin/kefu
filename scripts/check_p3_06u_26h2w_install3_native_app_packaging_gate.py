#!/usr/bin/env python3
from __future__ import annotations

import json
import plistlib
import subprocess
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[1]
PHASE = "H2W-INSTALL3"
SCHEMA_VERSION = "p3-06u-26h2w-install3.native_app_packaging_gate.v1"
DEFAULT_OUTPUT_DIR = ROOT / "output/p3_06u_26h2w_install3_native_app_packaging_gate"
DOC_PATH = ROOT / "docs/P3-06U-26H2W_INSTALL3_NATIVE_APP_PACKAGING_GATE.md"

INSTALLERS_DIR = ROOT / "installers"
MACOS_DIR = INSTALLERS_DIR / "macos"
WINDOWS_DIR = INSTALLERS_DIR / "windows"
VERSION_FILE = INSTALLERS_DIR / "VERSION.json"
LOGS_DIR = INSTALLERS_DIR / "logs"

INSTALL2_SUMMARY = ROOT / "output/p3_06u_26h2w_install2_native_installer_readiness/summary.json"
PILOT5_SUMMARY = ROOT / "output/p3_06u_26h2w_pilot5_installer_next_fork_decision/summary.json"

CommandRunner = Callable[[list[str]], subprocess.CompletedProcess[str]]

OVERCLAIM_PHRASES = [
    "正式 dmg 已完成",
    "正式 exe 已完成",
    "正式安装器已完成",
    "完整桌面安装器已完成",
    "签名安装包已完成",
    "真实外发已开启",
    "真实平台自动外发已接通",
    "生产 SLA 已完成",
]

UNSAFE_PATTERNS = [
    "OUTBOX_EXTERNAL_WRITE_ENABLED=true",
    "TRUSTED_INBOUND_WORKER_ENABLED=true",
    "STANDARD_OPS_DEV_BOOTSTRAP_ENABLED=true",
    "--profile worker",
    "ADMIN_BOOTSTRAP_PASSWORD=admin",
    "ADMIN_BOOTSTRAP_PASSWORD=password",
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


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _run_command(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=ROOT, text=True, capture_output=True, timeout=60, check=False)


def _command_ok(command: list[str], runner: CommandRunner) -> tuple[bool, str]:
    try:
        result = runner(command)
    except Exception as exc:  # pragma: no cover
        return False, str(exc)
    output = "\n".join(part for part in [result.stdout.strip(), result.stderr.strip()] if part)
    return result.returncode == 0, output[:1200]


def _summary_status(path: Path, expected_status: str) -> tuple[bool, str, dict[str, Any]]:
    if not path.exists():
        return False, "missing", {}
    try:
        payload = _read_json(path)
    except json.JSONDecodeError:
        return False, "invalid_json", {}
    actual = str(payload.get("status") or "missing_status")
    return actual == expected_status, actual, payload


def _scan_files(paths: list[Path], *, patterns: list[str]) -> dict[str, list[str]]:
    findings: dict[str, list[str]] = {}
    for path in paths:
        if not path.exists():
            findings[_display_path(path)] = ["missing"]
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        hits = [pattern for pattern in patterns if pattern in text]
        if hits:
            findings[_display_path(path)] = hits
    return findings


def _version_checks() -> tuple[bool, list[str], dict[str, bool]]:
    payload: dict[str, Any] = {}
    if VERSION_FILE.exists():
        try:
            payload = _read_json(VERSION_FILE)
        except json.JSONDecodeError:
            payload = {}
    boundaries = payload.get("boundaries", {}) if isinstance(payload, dict) else {}
    checks = {
        "version_file_exists": VERSION_FILE.exists(),
        "schema_version_present": bool(payload.get("schema_version")),
        "phase_is_install3": payload.get("phase") == PHASE,
        "package_version_present": bool(payload.get("package_version")),
        "signed_dmg_exe_ready_false": boundaries.get("signed_dmg_exe_ready") is False,
        "desktop_installer_ready_false": boundaries.get("desktop_installer_ready") is False,
        "native_installer_ready_false": boundaries.get("native_installer_ready") is False,
        "real_platform_send_ready_false": boundaries.get("real_platform_send_ready") is False,
        "silent_update_ready_false": boundaries.get("silent_update_ready") is False,
        "remote_control_ready_false": boundaries.get("remote_control_ready") is False,
    }
    blockers = [f"版本文件不满足 INSTALL3 门禁：{name}" for name, passed in checks.items() if not passed]
    return not blockers, blockers, checks


def _plist_checks(path: Path) -> tuple[bool, list[str], dict[str, bool]]:
    payload: dict[str, Any] = {}
    if path.exists():
        try:
            payload = plistlib.loads(path.read_bytes())
        except Exception:
            payload = {}
    checks = {
        "info_plist_exists": path.exists(),
        "bundle_identifier_present": bool(payload.get("CFBundleIdentifier")),
        "bundle_executable_matches": payload.get("CFBundleExecutable") == "WanfaCustomerService",
        "bundle_short_version_present": bool(payload.get("CFBundleShortVersionString")),
        "bundle_package_type_app": payload.get("CFBundlePackageType") == "APPL",
    }
    blockers = [f"macOS .app Info.plist 不满足门禁：{name}" for name, passed in checks.items() if not passed]
    return not blockers, blockers, checks


def _macos_checks(*, runner: CommandRunner) -> tuple[bool, list[str], dict[str, bool]]:
    app_dir = MACOS_DIR / "WanfaCustomerService.app"
    app_exec = app_dir / "Contents/MacOS/WanfaCustomerService"
    info_plist = app_dir / "Contents/Info.plist"
    health = MACOS_DIR / "health-check.sh"
    upgrade = MACOS_DIR / "prepare-upgrade-backup.sh"

    app_exec_text = app_exec.read_text(encoding="utf-8", errors="replace") if app_exec.exists() else ""
    health_text = health.read_text(encoding="utf-8", errors="replace") if health.exists() else ""
    upgrade_text = upgrade.read_text(encoding="utf-8", errors="replace") if upgrade.exists() else ""

    app_bash_ok, _ = _command_ok(["bash", "-n", str(app_exec)], runner) if app_exec.exists() else (False, "")
    health_bash_ok, _ = _command_ok(["bash", "-n", str(health)], runner) if health.exists() else (False, "")
    upgrade_bash_ok, _ = _command_ok(["bash", "-n", str(upgrade)], runner) if upgrade.exists() else (False, "")
    plist_ok, plist_blockers, plist_checks = _plist_checks(info_plist)

    checks = {
        "app_dir_exists": app_dir.exists(),
        "app_exec_exists": app_exec.exists(),
        "app_exec_bash_syntax_ok": app_bash_ok,
        "app_exec_calls_command_launcher": "WanfaCustomerService.command" in app_exec_text,
        "app_exec_does_not_create_customer_env": "cp " not in app_exec_text and "copy " not in app_exec_text.lower(),
        "health_script_exists": health.exists(),
        "health_script_bash_syntax_ok": health_bash_ok,
        "health_checks_docker": "docker info" in health_text and "Docker Desktop" in health_text,
        "health_checks_backend_health_url": "/health" in health_text and "curl --fail" in health_text,
        "health_blocks_external_write": 'require_env_value "OUTBOX_EXTERNAL_WRITE_ENABLED" "false"' in health_text,
        "health_blocks_worker": 'require_env_value "TRUSTED_INBOUND_WORKER_ENABLED" "false"' in health_text,
        "health_blocks_dev_bootstrap": 'require_env_value "STANDARD_OPS_DEV_BOOTSTRAP_ENABLED" "false"' in health_text,
        "upgrade_preflight_exists": upgrade.exists(),
        "upgrade_preflight_bash_syntax_ok": upgrade_bash_ok,
        "upgrade_writes_manifest": "manifest.json" in upgrade_text,
        "upgrade_does_not_export_database": '"database_backup_exported_by_this_script": false' in upgrade_text,
        "upgrade_requires_app_backup_next": "账号与本地维护" in upgrade_text and "生成备份" in upgrade_text,
    }
    checks.update(plist_checks)
    blockers = plist_blockers + [f"macOS 原生包装候选不满足门禁：{name}" for name, passed in checks.items() if not passed]
    return not blockers and plist_ok, blockers, checks


def _windows_checks() -> tuple[bool, list[str], dict[str, bool]]:
    health = WINDOWS_DIR / "HealthCheck-WanfaCustomerService.ps1"
    upgrade = WINDOWS_DIR / "Prepare-UpgradeBackup.ps1"
    health_text = health.read_text(encoding="utf-8", errors="replace") if health.exists() else ""
    upgrade_text = upgrade.read_text(encoding="utf-8", errors="replace") if upgrade.exists() else ""
    checks = {
        "health_script_exists": health.exists(),
        "health_checks_docker": "docker info" in health_text and "Docker Desktop" in health_text,
        "health_checks_backend_health_url": "/health" in health_text and "Invoke-WebRequest" in health_text,
        "health_blocks_external_write": 'Require-EnvValue "OUTBOX_EXTERNAL_WRITE_ENABLED" "false"' in health_text,
        "health_blocks_worker": 'Require-EnvValue "TRUSTED_INBOUND_WORKER_ENABLED" "false"' in health_text,
        "health_blocks_dev_bootstrap": 'Require-EnvValue "STANDARD_OPS_DEV_BOOTSTRAP_ENABLED" "false"' in health_text,
        "upgrade_preflight_exists": upgrade.exists(),
        "upgrade_writes_manifest": "manifest.json" in upgrade_text and "ConvertTo-Json" in upgrade_text,
        "upgrade_does_not_export_database": "database_backup_exported_by_this_script = $false" in upgrade_text,
        "upgrade_requires_app_backup_next": "账号与本地维护" in upgrade_text and "生成本地备份" in upgrade_text,
        "upgrade_does_not_copy_customer_env": "Copy-Item" not in upgrade_text and "Set-Content $EnvFile" not in upgrade_text,
    }
    blockers = [f"Windows 原生包装候选不满足门禁：{name}" for name, passed in checks.items() if not passed]
    return not blockers, blockers, checks


def _logs_checks() -> tuple[bool, list[str], dict[str, bool]]:
    readme = LOGS_DIR / "README.md"
    text = readme.read_text(encoding="utf-8", errors="replace") if readme.exists() else ""
    checks = {
        "logs_dir_exists": LOGS_DIR.exists(),
        "logs_gitkeep_exists": (LOGS_DIR / ".gitkeep").exists(),
        "logs_readme_exists": readme.exists(),
        "logs_readme_blocks_secrets": "禁止保存" in text and "数据库密码" in text and "模型 key" in text,
        "logs_readme_allows_non_sensitive_evidence": "健康检查摘要" in text and "版本号" in text,
    }
    blockers = [f"安装器日志目录不满足门禁：{name}" for name, passed in checks.items() if not passed]
    return not blockers, blockers, checks


def _write_markdown(path: Path, result: dict[str, Any]) -> None:
    readiness = result["readiness"]
    lines = [
        "# H2W-INSTALL3 原生包装候选门禁",
        "",
        "## 结论",
        "",
        f"- 阶段状态：`{result['status']}`",
        f"- macOS `.app` 包装候选：`{str(readiness['macos_app_wrapper_candidate_ready']).lower()}`",
        f"- Windows 健康检查与升级预检候选：`{str(readiness['windows_launcher_candidate_ready']).lower()}`",
        f"- 安装器健康检查候选：`{str(readiness['health_check_candidate_ready']).lower()}`",
        f"- 升级前备份预检候选：`{str(readiness['upgrade_backup_preflight_ready']).lower()}`",
        f"- 已签名 dmg/exe：`{str(readiness['signed_dmg_exe_ready']).lower()}`",
        "",
        "## 本阶段实际完成",
        "",
        "- 新增 macOS `.app` 包装骨架，仍调用现有安全启动脚本。",
        "- 新增安装器版本文件和本地非敏感日志目录。",
        "- 新增 macOS / Windows 健康检查脚本。",
        "- 新增 macOS / Windows 升级前备份预检脚本，只生成 manifest，不复制数据库、不读取密钥、不静默更新。",
        "",
        "## 阻断项",
        "",
    ]
    lines.extend([f"- {item}" for item in result["blockers"]] or ["- 无"])
    lines.extend(["", "## 固定边界", ""])
    lines.extend(
        [
            "- `signed_dmg_exe_ready=false`",
            "- `desktop_installer_ready=false`",
            "- `native_installer_ready=false`",
            "- `real_platform_send_performed=false`",
            "- `silent_update_performed=false`",
            "- `remote_control_performed=false`",
            "- `secret_written_by_installer=false`",
            "- `default_admin_password_created=false`",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_h2w_install3_native_app_packaging_gate(
    *,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    doc_path: Path = DOC_PATH,
    install2_summary: Path = INSTALL2_SUMMARY,
    pilot5_summary: Path = PILOT5_SUMMARY,
    runner: CommandRunner = _run_command,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = output_dir / "summary.json"
    blockers: list[str] = []
    warnings: list[str] = []

    install2_ok, install2_status, install2_payload = _summary_status(install2_summary, "native_wrapper_candidate_ready")
    pilot5_ok, pilot5_status, pilot5_payload = _summary_status(pilot5_summary, "installer_next_fork_decision_ready")
    if not install2_ok:
        blockers.append(f"INSTALL2 上游证据未就绪：期望 native_wrapper_candidate_ready，实际 {install2_status}")
    if not pilot5_ok:
        blockers.append(f"PILOT5 上游证据未就绪：期望 installer_next_fork_decision_ready，实际 {pilot5_status}")
    if install2_payload.get("readiness", {}).get("signed_dmg_exe_ready") is True:
        blockers.append("INSTALL2 越界记录为已签名安装包 ready")
    if pilot5_payload.get("decision", {}).get("enter_native_installer_track") is False:
        blockers.append("PILOT5 未允许进入原生安装器专项")

    version_ready, version_blockers, version_checks = _version_checks()
    macos_ready, macos_blockers, macos_checks = _macos_checks(runner=runner)
    windows_ready, windows_blockers, windows_checks = _windows_checks()
    logs_ready, logs_blockers, logs_checks = _logs_checks()
    blockers.extend(version_blockers)
    blockers.extend(macos_blockers)
    blockers.extend(windows_blockers)
    blockers.extend(logs_blockers)

    scanned_files = [
        VERSION_FILE,
        LOGS_DIR / "README.md",
        MACOS_DIR / "WanfaCustomerService.app/Contents/Info.plist",
        MACOS_DIR / "WanfaCustomerService.app/Contents/MacOS/WanfaCustomerService",
        MACOS_DIR / "health-check.sh",
        MACOS_DIR / "prepare-upgrade-backup.sh",
        WINDOWS_DIR / "HealthCheck-WanfaCustomerService.ps1",
        WINDOWS_DIR / "Prepare-UpgradeBackup.ps1",
        MACOS_DIR / "uninstall-notes.md",
        WINDOWS_DIR / "uninstall-notes.md",
    ]
    unsafe_hits = _scan_files(scanned_files, patterns=UNSAFE_PATTERNS)
    if unsafe_hits:
        blockers.append(f"INSTALL3 候选文件包含不安全开关或敏感键名：{unsafe_hits}")
    overclaim_hits = _scan_files(scanned_files, patterns=OVERCLAIM_PHRASES)
    if overclaim_hits:
        blockers.append(f"INSTALL3 候选文件包含越界承诺：{overclaim_hits}")

    health_check_candidate_ready = (
        macos_checks.get("health_script_exists") is True
        and macos_checks.get("health_script_bash_syntax_ok") is True
        and windows_checks.get("health_script_exists") is True
        and macos_checks.get("health_checks_backend_health_url") is True
        and windows_checks.get("health_checks_backend_health_url") is True
    )
    upgrade_backup_preflight_ready = (
        macos_checks.get("upgrade_preflight_exists") is True
        and macos_checks.get("upgrade_preflight_bash_syntax_ok") is True
        and windows_checks.get("upgrade_preflight_exists") is True
        and macos_checks.get("upgrade_does_not_export_database") is True
        and windows_checks.get("upgrade_does_not_export_database") is True
    )
    ready = (
        install2_ok
        and pilot5_ok
        and version_ready
        and macos_ready
        and windows_ready
        and logs_ready
        and health_check_candidate_ready
        and upgrade_backup_preflight_ready
        and not blockers
    )
    status = "native_app_packaging_candidate_ready" if ready else "blocked"
    result = {
        "phase": PHASE,
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "readiness": {
            "macos_app_wrapper_candidate_ready": macos_ready,
            "windows_launcher_candidate_ready": windows_ready,
            "health_check_candidate_ready": health_check_candidate_ready,
            "upgrade_backup_preflight_ready": upgrade_backup_preflight_ready,
            "installer_version_file_ready": version_ready,
            "installer_logs_policy_ready": logs_ready,
            "signed_dmg_exe_ready": False,
            "desktop_installer_ready": False,
            "native_installer_ready": False,
            "real_platform_send_ready": False,
            "silent_update_ready": False,
            "remote_control_ready": False,
        },
        "checks": {
            "install2": {
                "path": _display_path(install2_summary),
                "expected_status": "native_wrapper_candidate_ready",
                "actual_status": install2_status,
                "passed": install2_ok,
            },
            "pilot5": {
                "path": _display_path(pilot5_summary),
                "expected_status": "installer_next_fork_decision_ready",
                "actual_status": pilot5_status,
                "passed": pilot5_ok,
            },
            "version": version_checks,
            "macos": macos_checks,
            "windows": windows_checks,
            "logs": logs_checks,
        },
        "blockers": blockers,
        "warnings": warnings,
        "evidence": {
            "summary_json": {"path": _display_path(summary_path)},
            "markdown": {"path": _display_path(doc_path)},
            "version_file": {"path": _display_path(VERSION_FILE), "present": VERSION_FILE.exists()},
            "macos_app": {"path": _display_path(MACOS_DIR / "WanfaCustomerService.app"), "present": (MACOS_DIR / "WanfaCustomerService.app").exists()},
            "windows_health": {"path": _display_path(WINDOWS_DIR / "HealthCheck-WanfaCustomerService.ps1"), "present": (WINDOWS_DIR / "HealthCheck-WanfaCustomerService.ps1").exists()},
        },
        "boundaries": {
            "signed_dmg_exe_ready": False,
            "desktop_installer_ready": False,
            "native_installer_ready": False,
            "real_platform_send_performed": False,
            "trusted_inbound_worker_enabled_by_default": False,
            "customer_env_created_or_modified": False,
            "secret_written_by_installer": False,
            "default_admin_password_created": False,
            "remote_control_performed": False,
            "silent_update_performed": False,
            "database_backup_exported_by_preflight_script": False,
        },
        "not_ready_for": [
            "Apple/Windows 代码签名",
            "正式 dmg/exe 安装包",
            "静默安装或静默更新",
            "自动填写客户本地密码或模型凭据",
            "真实平台外发",
            "生产 SLA",
        ],
    }
    _write_json(summary_path, result)
    _write_markdown(doc_path, result)
    return result


def main() -> int:
    result = run_h2w_install3_native_app_packaging_gate()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if result["status"] == "blocked" else 0


if __name__ == "__main__":
    raise SystemExit(main())
