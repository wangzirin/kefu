#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PHASE = "H2W-INSTALL5"
SCHEMA_VERSION = "p3-06u-26h2w-install5.local_startup_experience.v1"
DEFAULT_OUTPUT_DIR = ROOT / "output/p3_06u_26h2w_install5_local_startup_experience"
DOC_PATH = ROOT / "docs/P3-06U-26H2W_INSTALL5_LOCAL_STARTUP_EXPERIENCE.md"

INSTALL4_SUMMARY = ROOT / "output/p3_06u_26h2w_install4_packaging_experience_gate/summary.json"
CUSTOMER_DOC = ROOT / "docs/customer/万法常世AI客服本地试跑启动体验说明.md"
START_SCRIPT = ROOT / "deploy/start-local-pilot.sh"
START_COMMAND = ROOT / "deploy/start-local-pilot.command"
CUSTOMER_ENV_TEMPLATE = ROOT / "deploy/customer.env.example"
MACOS_PREFLIGHT = ROOT / "installers/macos/preflight.sh"
MACOS_COMMAND = ROOT / "installers/macos/WanfaCustomerService.command"
MACOS_HEALTH = ROOT / "installers/macos/health-check.sh"
MACOS_UNINSTALL = ROOT / "installers/macos/uninstall-notes.md"
WINDOWS_START = ROOT / "installers/windows/Start-WanfaCustomerService.ps1"
WINDOWS_BAT = ROOT / "installers/windows/start-wanfa-customer-service.bat"
WINDOWS_HEALTH = ROOT / "installers/windows/HealthCheck-WanfaCustomerService.ps1"
WINDOWS_UNINSTALL = ROOT / "installers/windows/uninstall-notes.md"
LOGS_README = ROOT / "installers/logs/README.md"
VERSION_FILE = ROOT / "installers/VERSION.json"

REQUIRED_FILES = [
    CUSTOMER_DOC,
    START_SCRIPT,
    START_COMMAND,
    CUSTOMER_ENV_TEMPLATE,
    MACOS_PREFLIGHT,
    MACOS_COMMAND,
    MACOS_HEALTH,
    MACOS_UNINSTALL,
    WINDOWS_START,
    WINDOWS_BAT,
    WINDOWS_HEALTH,
    WINDOWS_UNINSTALL,
    LOGS_README,
    VERSION_FILE,
]
UNSAFE_PATTERNS = [
    "OUTBOX_EXTERNAL_WRITE_ENABLED=true",
    "TRUSTED_INBOUND_WORKER_ENABLED=true",
    "STANDARD_OPS_DEV_BOOTSTRAP_ENABLED=true",
    "ADMIN_BOOTSTRAP_PASSWORD=admin",
    "BAILIAN_API_KEY=sk-",
    "DEEPSEEK_API_KEY=sk-",
]
OVERCLAIMS = [
    "正式安装包已完成",
    "签名安装包已完成",
    "真实外发已开启",
    "全渠道已接通",
    "静默更新已开启",
    "远控客户电脑已完成",
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


def _contains(path: Path, *markers: str) -> bool:
    text = _read_text(path)
    return all(marker in text for marker in markers)


def _scan(patterns: list[str]) -> dict[str, list[str]]:
    findings: dict[str, list[str]] = {}
    for path in REQUIRED_FILES:
        text = _read_text(path)
        hits = [pattern for pattern in patterns if pattern in text]
        if hits:
            findings[_display_path(path)] = hits
    return findings


def _write_markdown(path: Path, result: dict[str, Any]) -> None:
    lines = [
        "# H2W-INSTALL5 本地启动体验试跑",
        "",
        "## 结论",
        "",
        f"- 阶段状态：`{result['status']}`",
        f"- 本地启动体验：`{str(result['readiness']['local_startup_experience_ready']).lower()}`",
        f"- 签名 dmg/exe：`{str(result['readiness']['signed_dmg_exe_ready']).lower()}`",
        "",
        "## 覆盖范围",
        "",
        "- Docker Desktop 检查。",
        "- 端口占用提示。",
        "- `customer.env` 和数据库密码检查。",
        "- 外发关闭和入站 worker 关闭检查。",
        "- 日志目录、卸载/清理说明。",
        "",
        "## 阻断项",
        "",
    ]
    lines.extend([f"- {item}" for item in result["blockers"]] or ["- 无"])
    lines.extend(["", "## 边界", ""])
    lines.extend(
        [
            "- `signed_dmg_exe_ready=false`",
            "- `real_platform_send_ready=false`",
            "- `silent_update_ready=false`",
            "- `remote_control_ready=false`",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_h2w_install5_local_startup_experience(
    *,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    doc_path: Path = DOC_PATH,
) -> dict[str, Any]:
    blockers: list[str] = []
    install4 = _read_json(INSTALL4_SUMMARY)
    if install4.get("status") != "native_packaging_experience_candidate_ready":
        blockers.append(f"INSTALL4 上游状态不满足：{install4.get('status') or 'missing'}")

    inventory = [{"path": _display_path(path), "present": path.exists()} for path in REQUIRED_FILES]
    blockers.extend([f"启动体验文件缺失：{item['path']}" for item in inventory if not item["present"]])

    checks = {
        "customer_doc_mentions_docker_env_ports_boundaries": _contains(
            CUSTOMER_DOC,
            "Docker Desktop",
            "deploy/customer.env",
            "端口",
            "真实外发关闭",
            "签名 dmg/exe 未完成",
        ),
        "start_script_checks_docker_and_env": _contains(START_SCRIPT, "command -v docker", "deploy/customer.env", "OUTBOX_EXTERNAL_WRITE_ENABLED", "TRUSTED_INBOUND_WORKER_ENABLED"),
        "start_script_blocks_template_password": _contains(START_SCRIPT, "replace-with-local-random-password", "WANFA_ALLOW_TEMPLATE_PASSWORD_FOR_REHEARSAL"),
        "macos_preflight_checks_ports": _contains(MACOS_PREFLIGHT, "BACKEND_PORT", "FRONTEND_PORT", "端口"),
        "macos_health_blocks_external_write": _contains(MACOS_HEALTH, 'require_env_value "OUTBOX_EXTERNAL_WRITE_ENABLED" "false"'),
        "windows_start_checks_docker_env": _contains(WINDOWS_START, "Docker Desktop", "deploy\\customer.env", "OUTBOX_EXTERNAL_WRITE_ENABLED"),
        "windows_health_blocks_external_write": _contains(WINDOWS_HEALTH, 'Require-EnvValue "OUTBOX_EXTERNAL_WRITE_ENABLED" "false"'),
        "uninstall_requires_backup": _contains(MACOS_UNINSTALL, "备份", "诊断包") and _contains(WINDOWS_UNINSTALL, "备份", "诊断包"),
        "logs_readme_blocks_sensitive_data": _contains(LOGS_README, "数据库密码", "模型 key", "平台 token", "客户原文", "浏览器 profile"),
    }
    blockers.extend([f"INSTALL5 启动体验检查不满足：{name}" for name, passed in checks.items() if not passed])

    version = _read_json(VERSION_FILE)
    boundaries = version.get("boundaries") if isinstance(version.get("boundaries"), dict) else {}
    if boundaries.get("signed_dmg_exe_ready") is not False:
        blockers.append("VERSION.json 未保持 signed_dmg_exe_ready=false")
    if boundaries.get("real_platform_send_ready") is not False:
        blockers.append("VERSION.json 未保持 real_platform_send_ready=false")

    for path, hits in _scan(UNSAFE_PATTERNS).items():
        blockers.append(f"{path} 包含不安全启动配置：{', '.join(hits)}")
    for path, hits in _scan(OVERCLAIMS).items():
        blockers.append(f"{path} 包含越界承诺：{', '.join(hits)}")

    result = {
        "schema_version": SCHEMA_VERSION,
        "phase": PHASE,
        "status": "blocked" if blockers else "local_startup_experience_ready",
        "checks": checks,
        "inventory": inventory,
        "blockers": sorted(set(blockers)),
        "readiness": {
            "local_startup_experience_ready": not blockers,
            "signed_dmg_exe_ready": False,
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
    result = run_h2w_install5_local_startup_experience()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] != "blocked" else 1


if __name__ == "__main__":
    raise SystemExit(main())
