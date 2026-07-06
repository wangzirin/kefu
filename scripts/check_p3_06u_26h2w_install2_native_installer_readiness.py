#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[1]
PHASE = "H2W-INSTALL2"
SCHEMA_VERSION = "p3-06u-26h2w-install2.native_installer_readiness.v1"
DEFAULT_OUTPUT_DIR = ROOT / "output/p3_06u_26h2w_install2_native_installer_readiness"
DOC_PATH = ROOT / "docs/P3-06U-26H2W_INSTALL2_NATIVE_INSTALLER_READINESS.md"

MACOS_DIR = ROOT / "installers/macos"
WINDOWS_DIR = ROOT / "installers/windows"
INSTALL1_SUMMARY = ROOT / "output/p3_06u_26h2w_install1_nontechnical_customer_starter/summary.json"
START_SCRIPT = ROOT / "deploy/start-local-pilot.sh"
CUSTOMER_ENV_TEMPLATE = ROOT / "deploy/customer.env.example"
CUSTOMER_ENV = ROOT / "deploy/customer.env"

CommandRunner = Callable[[list[str]], subprocess.CompletedProcess[str]]

OVERCLAIM_PHRASES = [
    "正式 dmg 已完成",
    "正式 exe 已完成",
    "正式安装器已完成",
    "完整桌面安装器已完成",
    "生产 SLA 已完成",
    "正式客户签收已完成",
    "真实平台自动外发已接通",
    "真实外发已开启",
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


def _env_map(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


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


def _macos_checks(*, runner: CommandRunner) -> tuple[bool, list[str], dict[str, bool]]:
    preflight = MACOS_DIR / "preflight.sh"
    launcher = MACOS_DIR / "WanfaCustomerService.command"
    readme = MACOS_DIR / "README.md"
    uninstall = MACOS_DIR / "uninstall-notes.md"
    preflight_text = preflight.read_text(encoding="utf-8") if preflight.exists() else ""
    launcher_text = launcher.read_text(encoding="utf-8") if launcher.exists() else ""
    bash_preflight_ok, _ = _command_ok(["bash", "-n", str(preflight)], runner) if preflight.exists() else (False, "")
    bash_launcher_ok, _ = _command_ok(["bash", "-n", str(launcher)], runner) if launcher.exists() else (False, "")
    checks = {
        "directory_exists": MACOS_DIR.exists(),
        "readme_exists": readme.exists(),
        "preflight_exists": preflight.exists(),
        "launcher_exists": launcher.exists(),
        "uninstall_notes_exists": uninstall.exists(),
        "preflight_bash_syntax_ok": bash_preflight_ok,
        "launcher_bash_syntax_ok": bash_launcher_ok,
        "preflight_checks_docker": "docker info" in preflight_text and "Docker Desktop" in preflight_text,
        "preflight_requires_customer_env": "deploy/customer.env" in preflight_text,
        "preflight_blocks_external_write": 'require_env_value "OUTBOX_EXTERNAL_WRITE_ENABLED" "false"' in preflight_text,
        "preflight_blocks_worker": 'require_env_value "TRUSTED_INBOUND_WORKER_ENABLED" "false"' in preflight_text,
        "preflight_blocks_dev_bootstrap": 'require_env_value "STANDARD_OPS_DEV_BOOTSTRAP_ENABLED" "false"' in preflight_text,
        "preflight_blocks_default_admin_password": 'require_env_empty "ADMIN_BOOTSTRAP_PASSWORD"' in preflight_text,
        "preflight_blocks_placeholder_password": "replace-with-local-random-password" in preflight_text,
        "launcher_calls_preflight": "preflight.sh" in launcher_text,
        "launcher_calls_safe_start_script": "deploy/start-local-pilot.sh" in launcher_text,
        "launcher_does_not_create_customer_env": "cp " not in launcher_text and "copy " not in launcher_text,
        "launcher_keeps_terminal_open": "read -r -p" in launcher_text,
    }
    blockers = [f"macOS 候选包装不满足门禁：{name}" for name, passed in checks.items() if not passed]
    return not blockers, blockers, checks


def _windows_checks() -> tuple[bool, list[str], dict[str, bool]]:
    powershell = WINDOWS_DIR / "Start-WanfaCustomerService.ps1"
    bat = WINDOWS_DIR / "start-wanfa-customer-service.bat"
    readme = WINDOWS_DIR / "README.md"
    uninstall = WINDOWS_DIR / "uninstall-notes.md"
    ps_text = powershell.read_text(encoding="utf-8") if powershell.exists() else ""
    bat_text = bat.read_text(encoding="utf-8") if bat.exists() else ""
    checks = {
        "directory_exists": WINDOWS_DIR.exists(),
        "readme_exists": readme.exists(),
        "powershell_exists": powershell.exists(),
        "bat_exists": bat.exists(),
        "uninstall_notes_exists": uninstall.exists(),
        "powershell_checks_docker": "docker info" in ps_text and "Docker Desktop" in ps_text,
        "powershell_requires_customer_env": "deploy\\customer.env" in ps_text or "deploy\\customer.env" in ps_text.replace("/", "\\"),
        "powershell_blocks_external_write": 'Require-EnvValue "OUTBOX_EXTERNAL_WRITE_ENABLED" "false"' in ps_text,
        "powershell_blocks_worker": 'Require-EnvValue "TRUSTED_INBOUND_WORKER_ENABLED" "false"' in ps_text,
        "powershell_blocks_dev_bootstrap": 'Require-EnvValue "STANDARD_OPS_DEV_BOOTSTRAP_ENABLED" "false"' in ps_text,
        "powershell_blocks_default_admin_password": 'Require-EnvEmpty "ADMIN_BOOTSTRAP_PASSWORD"' in ps_text,
        "powershell_blocks_placeholder_password": "replace-with-local-random-password" in ps_text,
        "powershell_uses_safe_compose_files": "docker-compose.pilot.yml" in ps_text and "docker-compose.yml" in ps_text,
        "bat_calls_powershell": "Start-WanfaCustomerService.ps1" in bat_text,
        "bat_does_not_create_customer_env": "copy " not in bat_text.lower() and "xcopy " not in bat_text.lower(),
    }
    blockers = [f"Windows 候选包装不满足门禁：{name}" for name, passed in checks.items() if not passed]
    return not blockers, blockers, checks


def _template_checks() -> tuple[bool, list[str], dict[str, bool]]:
    values = _env_map(CUSTOMER_ENV_TEMPLATE)
    checks = {
        "template_exists": CUSTOMER_ENV_TEMPLATE.exists(),
        "concrete_customer_env_not_in_repo": not CUSTOMER_ENV.exists(),
        "dev_bootstrap_disabled": values.get("STANDARD_OPS_DEV_BOOTSTRAP_ENABLED") == "false",
        "external_write_disabled": values.get("OUTBOX_EXTERNAL_WRITE_ENABLED") == "false",
        "worker_disabled": values.get("TRUSTED_INBOUND_WORKER_ENABLED") == "false",
        "admin_bootstrap_password_empty": values.get("ADMIN_BOOTSTRAP_PASSWORD", "") == "",
        "uses_pgvector_store": values.get("KNOWLEDGE_VECTOR_STORE") == "postgres_pgvector_store_v1",
        "database_password_placeholder": values.get("STANDARD_OPS_POSTGRES_PASSWORD") == "replace-with-local-random-password",
        "model_keys_empty": values.get("BAILIAN_API_KEY", "") == "" and values.get("DEEPSEEK_API_KEY", "") == "",
    }
    blockers = [f"客户环境模板不满足 INSTALL2 门禁：{name}" for name, passed in checks.items() if not passed]
    return not blockers, blockers, checks


def _write_markdown(path: Path, result: dict[str, Any]) -> None:
    readiness = result["readiness"]
    lines = [
        "# H2W-INSTALL2 原生安装器专项门禁",
        "",
        "## 结论",
        "",
        f"- 阶段状态：`{result['status']}`",
        f"- 安装器计划就绪：`{str(readiness['installer_plan_ready']).lower()}`",
        f"- 原生启动包装候选就绪：`{str(readiness['native_wrapper_candidate_ready']).lower()}`",
        f"- 已签名 dmg/exe 就绪：`{str(readiness['signed_dmg_exe_ready']).lower()}`",
        "",
        "## 本阶段实际完成",
        "",
        "- 新增 `installers/macos/` 候选包装目录。",
        "- 新增 `installers/windows/` 候选包装目录。",
        "- 包装层只做预检和启动，不自动创建客户 env、不写密码、不开启真实外发、不启用 worker。",
        "- 本阶段不进行 Apple/Windows 代码签名，不写成正式安装包完成。",
        "",
        "## 阻断项",
        "",
    ]
    lines.extend([f"- {item}" for item in result["blockers"]] or ["- 无"])
    lines.extend(["", "## 固定边界", ""])
    lines.extend(
        [
            "- `desktop_installer_ready=false`",
            "- `native_installer_ready=false`",
            "- `signed_dmg_exe_ready=false`",
            "- `real_platform_send_performed=false`",
            "- `worker_enabled_by_default=false`",
            "- `default_admin_password_created=false`",
            "- `secret_written_by_installer=false`",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_h2w_install2_native_installer_readiness(
    *,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    doc_path: Path = DOC_PATH,
    install1_summary: Path = INSTALL1_SUMMARY,
    runner: CommandRunner = _run_command,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = output_dir / "summary.json"
    blockers: list[str] = []
    warnings: list[str] = []

    install1_ok, install1_status, install1_payload = _summary_status(
        install1_summary,
        "ready_for_nontechnical_customer_startup_rehearsal",
    )
    if not install1_ok:
        blockers.append(f"INSTALL1 上游证据未就绪：期望 ready_for_nontechnical_customer_startup_rehearsal，实际 {install1_status}")
    if install1_payload.get("readiness", {}).get("desktop_installer_ready") is True:
        blockers.append("INSTALL1 越界记录为完整桌面安装器 ready")

    macos_ready, macos_blockers, macos_checks = _macos_checks(runner=runner)
    windows_ready, windows_blockers, windows_checks = _windows_checks()
    template_ready, template_blockers, template_checks = _template_checks()
    blockers.extend(macos_blockers)
    blockers.extend(windows_blockers)
    blockers.extend(template_blockers)

    scanned_files = [
        MACOS_DIR / "README.md",
        MACOS_DIR / "preflight.sh",
        MACOS_DIR / "WanfaCustomerService.command",
        MACOS_DIR / "uninstall-notes.md",
        WINDOWS_DIR / "README.md",
        WINDOWS_DIR / "Start-WanfaCustomerService.ps1",
        WINDOWS_DIR / "start-wanfa-customer-service.bat",
        WINDOWS_DIR / "uninstall-notes.md",
    ]
    unsafe_hits = _scan_files(scanned_files, patterns=UNSAFE_PATTERNS)
    # 空 key 模板只允许出现在 deploy/customer.env.example，不允许出现在安装器包装层。
    if unsafe_hits:
        blockers.append(f"安装器候选文件包含不安全开关或敏感键名：{unsafe_hits}")
    overclaim_hits = _scan_files(scanned_files, patterns=OVERCLAIM_PHRASES)
    if overclaim_hits:
        blockers.append(f"安装器候选文件包含越界承诺：{overclaim_hits}")

    start_script_text = START_SCRIPT.read_text(encoding="utf-8") if START_SCRIPT.exists() else ""
    safe_start_script_reused = "deploy/start-local-pilot.sh" in (MACOS_DIR / "WanfaCustomerService.command").read_text(encoding="utf-8", errors="replace") if (MACOS_DIR / "WanfaCustomerService.command").exists() else False
    if not START_SCRIPT.exists() or 'require_value "OUTBOX_EXTERNAL_WRITE_ENABLED" "false"' not in start_script_text:
        blockers.append("现有安全启动脚本缺失或未检查真实外发关闭")

    ready = install1_ok and macos_ready and windows_ready and template_ready and safe_start_script_reused and not blockers
    status = "native_wrapper_candidate_ready" if ready else "blocked"
    result = {
        "phase": PHASE,
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "readiness": {
            "installer_plan_ready": install1_ok and template_ready,
            "native_wrapper_candidate_ready": ready,
            "signed_dmg_exe_ready": False,
            "desktop_installer_ready": False,
            "native_installer_ready": False,
            "real_platform_send_ready": False,
            "worker_enabled_by_default": False,
            "default_admin_password_created": False,
            "secret_written_by_installer": False,
        },
        "checks": {
            "install1": {
                "path": _display_path(install1_summary),
                "expected_status": "ready_for_nontechnical_customer_startup_rehearsal",
                "actual_status": install1_status,
                "passed": install1_ok,
            },
            "macos": macos_checks,
            "windows": windows_checks,
            "customer_env_template": template_checks,
            "safe_start_script_reused": safe_start_script_reused,
        },
        "blockers": blockers,
        "warnings": warnings,
        "evidence": {
            "summary_json": {"path": _display_path(summary_path)},
            "markdown": {"path": _display_path(doc_path)},
            "macos_dir": {"path": _display_path(MACOS_DIR), "present": MACOS_DIR.exists()},
            "windows_dir": {"path": _display_path(WINDOWS_DIR), "present": WINDOWS_DIR.exists()},
            "install1_summary": {"path": _display_path(install1_summary), "present": install1_summary.exists()},
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
        },
        "not_ready_for": [
            "Apple/Windows 代码签名",
            "正式 dmg/exe 安装包",
            "静默安装或静默更新",
            "自动填写客户本地密码或模型凭据",
            "真实平台外发",
        ],
    }
    _write_json(summary_path, result)
    _write_markdown(doc_path, result)
    return result


def main() -> int:
    result = run_h2w_install2_native_installer_readiness()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if result["status"] == "blocked" else 0


if __name__ == "__main__":
    raise SystemExit(main())
