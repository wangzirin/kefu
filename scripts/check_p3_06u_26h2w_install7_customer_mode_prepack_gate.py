#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from lib.h2w_pack8_common import ROOT, base_result, display_path, read_json, scan_text_file, write_json, write_markdown_report


PHASE = "H2W-INSTALL7"
SCHEMA_VERSION = "p3-06u-26h2w-install7.customer_mode_prepack_gate.v1"
DEFAULT_OUTPUT_DIR = ROOT / "output/p3_06u_26h2w_install7_customer_mode_prepack_gate"
DOC_PATH = ROOT / "docs/P3-06U-26H2W_INSTALL7_CUSTOMER_MODE_PREPACK_GATE.md"
INSTALL6_SUMMARY = ROOT / "output/p3_06u_26h2w_install6_trial_installer_experience/summary.json"

START_SCRIPT = ROOT / "deploy/start-local-pilot.sh"
COMMAND_WRAPPER = ROOT / "deploy/start-local-pilot.command"
CUSTOMER_ENV_TEMPLATE = ROOT / "deploy/customer.env.example"
PILOT_COMPOSE = ROOT / "deploy/docker-compose.pilot.yml"
VERSION_FILE = ROOT / "installers/VERSION.json"

REQUIRED_FILES = [
    START_SCRIPT,
    COMMAND_WRAPPER,
    CUSTOMER_ENV_TEMPLATE,
    PILOT_COMPOSE,
    VERSION_FILE,
    ROOT / "installers/macos/preflight.sh",
    ROOT / "installers/macos/health-check.sh",
    ROOT / "installers/macos/uninstall-notes.md",
    ROOT / "installers/windows/Start-WanfaCustomerService.ps1",
    ROOT / "installers/windows/HealthCheck-WanfaCustomerService.ps1",
    ROOT / "installers/windows/uninstall-notes.md",
    ROOT / "installers/logs/README.md",
    ROOT / "docs/customer/万法常世AI客服本地试跑启动体验说明.md",
]

REQUIRED_ENV_VALUES = {
    "STANDARD_OPS_DEV_BOOTSTRAP_ENABLED": "false",
    "OUTBOX_EXTERNAL_WRITE_ENABLED": "false",
    "TRUSTED_INBOUND_WORKER_ENABLED": "false",
    "KNOWLEDGE_VECTOR_STORE": "postgres_pgvector_store_v1",
    "ADMIN_BOOTSTRAP_PASSWORD": "",
    "ADMIN_BOOTSTRAP_EMAIL": "",
    "BAILIAN_API_KEY": "",
    "DEEPSEEK_API_KEY": "",
}

START_SCRIPT_MARKERS = [
    'require_value "STANDARD_OPS_DEV_BOOTSTRAP_ENABLED" "false"',
    'require_value "OUTBOX_EXTERNAL_WRITE_ENABLED" "false"',
    'require_value "TRUSTED_INBOUND_WORKER_ENABLED" "false"',
    'require_value "KNOWLEDGE_VECTOR_STORE" "postgres_pgvector_store_v1"',
    'require_empty "ADMIN_BOOTSTRAP_PASSWORD"',
    "replace-with-local-random-password",
    "docker compose",
    'up -d --build postgres redis',
    'up -d --build backend frontend',
]

PREFLIGHT_MARKERS = [
    "Docker Desktop",
    'Require-EnvValue "STANDARD_OPS_DEV_BOOTSTRAP_ENABLED" "false"',
    'Require-EnvValue "OUTBOX_EXTERNAL_WRITE_ENABLED" "false"',
    'Require-EnvValue "TRUSTED_INBOUND_WORKER_ENABLED" "false"',
    'Require-EnvEmpty "ADMIN_BOOTSTRAP_PASSWORD"',
]

MAC_PREFLIGHT_MARKERS = [
    "Docker Desktop",
    'require_env_value "STANDARD_OPS_DEV_BOOTSTRAP_ENABLED" "false"',
    'require_env_value "OUTBOX_EXTERNAL_WRITE_ENABLED" "false"',
    'require_env_value "TRUSTED_INBOUND_WORKER_ENABLED" "false"',
    'require_env_empty "ADMIN_BOOTSTRAP_PASSWORD"',
]

FALSE_VERSION_BOUNDARIES = [
    "signed_dmg_exe_ready",
    "desktop_installer_ready",
    "native_installer_ready",
    "real_platform_send_ready",
    "silent_update_ready",
    "remote_control_ready",
]

UNSAFE_PATTERNS = [
    ("开发入口开启", re.compile(r"(?m)^[ \t]*STANDARD_OPS_DEV_BOOTSTRAP_ENABLED[ \t]*=[ \t]*true[ \t]*(?:#.*)?$", re.IGNORECASE)),
    ("真实外发开启", re.compile(r"(?m)^[ \t]*OUTBOX_EXTERNAL_WRITE_ENABLED[ \t]*=[ \t]*true[ \t]*(?:#.*)?$", re.IGNORECASE)),
    ("入站 worker 默认开启", re.compile(r"(?m)^[ \t]*TRUSTED_INBOUND_WORKER_ENABLED[ \t]*=[ \t]*true[ \t]*(?:#.*)?$", re.IGNORECASE)),
    ("预置管理员密码", re.compile(r"(?m)^[ \t]*ADMIN_BOOTSTRAP_PASSWORD[ \t]*=[ \t]*[^#\s][^\n#]*", re.IGNORECASE)),
    ("百炼密钥被写入", re.compile(r"(?m)^[ \t]*BAILIAN_API_KEY[ \t]*=[ \t]*sk-[A-Za-z0-9]", re.IGNORECASE)),
    ("DeepSeek 密钥被写入", re.compile(r"(?m)^[ \t]*DEEPSEEK_API_KEY[ \t]*=[ \t]*sk-[A-Za-z0-9]", re.IGNORECASE)),
]

OVERCLAIM_PHRASES = [
    "正式安装包已完成",
    "已签名安装器",
    "签名 dmg/exe 已完成",
    "真实外发已开启",
    "真实外发已接通",
    "全渠道已接通",
    "静默更新已开启",
    "远控客户电脑已完成",
]


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def _parse_env_template(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in _text(path).splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip("\"'")
    return values


def _check_env_template(path: Path) -> list[str]:
    blockers: list[str] = []
    if not path.exists():
        return [f"客户环境模板缺失：{display_path(path)}"]
    values = _parse_env_template(path)
    for key, expected in REQUIRED_ENV_VALUES.items():
        actual = values.get(key)
        if actual != expected:
            blockers.append(f"客户环境模板 {key} 必须为 `{expected}`，实际 `{actual if actual is not None else 'missing'}`")
    for label, pattern in UNSAFE_PATTERNS:
        if pattern.search(_text(path)):
            blockers.append(f"客户环境模板出现危险配置：{label}")
    return blockers


def _check_required_markers(path: Path, markers: list[str], *, label: str) -> list[str]:
    text = _text(path)
    return [f"{label} 缺少门禁标记：{marker}" for marker in markers if marker not in text]


def _check_start_script(path: Path) -> list[str]:
    blockers = _check_required_markers(path, START_SCRIPT_MARKERS, label=display_path(path))
    text = _text(path)
    if "--profile worker" in text:
        blockers.append("客户启动脚本默认启用了 worker profile")
    if re.search(r"up\s+-d\s+--build[^\n]*(trusted-inbound-worker|worker)", text):
        blockers.append("客户启动脚本默认启动了入站 worker")
    if "ADMIN_BOOTSTRAP_PASSWORD" in text and "require_empty \"ADMIN_BOOTSTRAP_PASSWORD\"" not in text:
        blockers.append("客户启动脚本没有强制管理员密码为空")
    return blockers


def _check_pilot_compose(path: Path) -> list[str]:
    text = _text(path)
    blockers: list[str] = []
    required = [
        'STANDARD_OPS_DEV_BOOTSTRAP_ENABLED: "false"',
        'OUTBOX_EXTERNAL_WRITE_ENABLED: "false"',
        'TRUSTED_INBOUND_WORKER_ENABLED: "false"',
        'profiles: ["worker"]',
        "trusted-inbound-worker:",
    ]
    for marker in required:
        if marker not in text:
            blockers.append(f"pilot compose 缺少客户模式门禁：{marker}")
    backend_section = text.split("trusted-inbound-worker:", 1)[0]
    if 'TRUSTED_INBOUND_WORKER_ENABLED: "true"' in backend_section:
        blockers.append("pilot compose 的默认 backend 服务开启了入站 worker")
    return blockers


def _check_version_boundaries(path: Path) -> list[str]:
    payload = read_json(path)
    boundaries = payload.get("boundaries") if isinstance(payload.get("boundaries"), dict) else {}
    blockers: list[str] = []
    for key in FALSE_VERSION_BOUNDARIES:
        if boundaries.get(key) is not False:
            blockers.append(f"installers/VERSION.json 必须保持 {key}=false")
    return blockers


def _scan_overclaims(paths: list[Path]) -> list[str]:
    blockers: list[str] = []
    for path in paths:
        if not path.exists() or path.suffix.lower() not in {".md", ".txt", ".json", ".sh", ".ps1", ".bat", ".yml", ".yaml", ".example"}:
            continue
        text = _text(path)
        for phrase in OVERCLAIM_PHRASES:
            if phrase in text:
                blockers.append(f"{display_path(path)} 出现封包前越界表述：{phrase}")
    return blockers


def run_h2w_install7_customer_mode_prepack_gate(
    *,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    doc_path: Path = DOC_PATH,
    install6_summary: Path = INSTALL6_SUMMARY,
    customer_env_template: Path = CUSTOMER_ENV_TEMPLATE,
    start_script: Path = START_SCRIPT,
    command_wrapper: Path = COMMAND_WRAPPER,
    pilot_compose: Path = PILOT_COMPOSE,
    version_file: Path = VERSION_FILE,
    required_files: list[Path] | None = None,
) -> dict[str, Any]:
    blockers: list[str] = []
    install6 = read_json(install6_summary)
    if install6.get("status") != "trial_installer_experience_candidate_ready":
        blockers.append(f"INSTALL6 上游状态不满足：{install6.get('status') or 'missing'}")

    files = required_files or REQUIRED_FILES
    inventory = [{"path": display_path(path), "present": path.exists()} for path in files]
    blockers.extend([f"客户模式封包文件缺失：{item['path']}" for item in inventory if not item["present"]])

    blockers.extend(_check_env_template(customer_env_template))
    blockers.extend(_check_start_script(start_script))
    blockers.extend(_check_pilot_compose(pilot_compose))
    blockers.extend(_check_version_boundaries(version_file))
    blockers.extend(_check_required_markers(ROOT / "installers/macos/preflight.sh", MAC_PREFLIGHT_MARKERS, label="macOS 预检脚本"))
    blockers.extend(_check_required_markers(ROOT / "installers/windows/Start-WanfaCustomerService.ps1", PREFLIGHT_MARKERS, label="Windows 启动脚本"))

    command_text = _text(command_wrapper)
    if "start-local-pilot.sh" not in command_text:
        blockers.append("双击启动包装器没有委托安全启动脚本 start-local-pilot.sh")

    scan_paths = [path for path in files if path.exists()] + [doc_path]
    for path in scan_paths:
        if path.exists():
            blockers.extend(scan_text_file(path))
    blockers.extend(_scan_overclaims(scan_paths))

    status = "customer_mode_prepack_gate_ready" if not blockers else "blocked"
    result = base_result(SCHEMA_VERSION, PHASE, status, blockers)
    result.update(
        {
            "customer_data_used": False,
            "internal_sample_used": False,
            "inventory": inventory,
            "checks": {
                "install6_status": install6.get("status") or "missing",
                "customer_env_template_checked": customer_env_template.exists(),
                "start_script_checked": start_script.exists(),
                "pilot_compose_checked": pilot_compose.exists(),
                "version_boundaries_checked": version_file.exists(),
            },
            "readiness": {
                "customer_mode_prepack_status": status,
                "customer_mode_prepack_ready": not blockers,
                "dev_bootstrap_enabled": False,
                "default_admin_password_created": False,
                "real_platform_send_ready": False,
                "trusted_inbound_worker_default_enabled": False,
                "worker_profile_default_enabled": False,
                "signed_dmg_exe_ready": False,
                "desktop_installer_ready": False,
                "native_installer_ready": False,
                "silent_update_ready": False,
                "remote_control_ready": False,
            },
            "evidence_paths": [display_path(path) for path in files if path.exists()]
            + [display_path(install6_summary), display_path(doc_path), display_path(output_dir / "summary.json")],
        }
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    write_json(output_dir / "summary.json", result)
    write_markdown_report(
        doc_path,
        "H2W-INSTALL7 封包前客户模式门禁",
        result,
        [
            (
                "客户模式硬边界",
                [
                    "开发登录入口关闭：`STANDARD_OPS_DEV_BOOTSTRAP_ENABLED=false`",
                    "真实外发关闭：`OUTBOX_EXTERNAL_WRITE_ENABLED=false`",
                    "入站 worker 默认关闭：`TRUSTED_INBOUND_WORKER_ENABLED=false`",
                    "首任负责人必须在本地界面创建，模板不预置管理员密码",
                    "安装器仍为候选结构，签名 dmg/exe、静默更新和远控均保持 false",
                ],
            ),
            ("覆盖文件", [item["path"] for item in inventory]),
        ],
    )
    return result


def main() -> int:
    result = run_h2w_install7_customer_mode_prepack_gate()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if result["status"] == "blocked" else 0


if __name__ == "__main__":
    raise SystemExit(main())
