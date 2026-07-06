#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[1]
PHASE = "H2W-INSTALL1"
DEFAULT_OUTPUT_DIR = ROOT / "output/p3_06u_26h2w_install1_nontechnical_customer_starter"
DOC_PATH = ROOT / "docs/P3-06U-26H2W_INSTALL1_NONTECHNICAL_CUSTOMER_STARTER.md"

PACK5_SUMMARY = ROOT / "output/p3_06u_26h2w_pack5_customer_handoff_package/summary.json"
KB1_SUMMARY = ROOT / "output/p3_06u_26h2w_kb1_customer_specific_knowledge_package_rehearsal/summary.json"
START_SCRIPT = ROOT / "deploy/start-local-pilot.sh"
COMMAND_LAUNCHER = ROOT / "deploy/start-local-pilot.command"
QUICK_START_DOC = ROOT / "docs/customer/万法常世AI客服本地试点启动说明.md"
CUSTOMER_ENV_TEMPLATE = ROOT / "deploy/customer.env.example"
CUSTOMER_ENV = ROOT / "deploy/customer.env"

CommandRunner = Callable[[list[str]], subprocess.CompletedProcess[str]]


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
    return subprocess.run(command, cwd=ROOT, text=True, capture_output=True, timeout=90, check=False)


def _command_ok(command: list[str], runner: CommandRunner) -> tuple[bool, str]:
    try:
        result = runner(command)
    except Exception as exc:  # pragma: no cover - host shell differences
        return False, str(exc)
    output = "\n".join(part for part in [result.stdout.strip(), result.stderr.strip()] if part)
    return result.returncode == 0, output[:1200]


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


def _summary_status(path: Path, expected_status: str) -> tuple[bool, str, dict[str, Any]]:
    if not path.exists():
        return False, "missing", {}
    try:
        payload = _read_json(path)
    except json.JSONDecodeError:
        return False, "invalid_json", {}
    status = str(payload.get("status", "missing_status"))
    return status == expected_status, status, payload


def _customer_env_template_checks(template: Path, concrete_env: Path) -> tuple[bool, list[str], dict[str, bool]]:
    values = _env_map(template)
    checks = {
        "template_exists": template.exists(),
        "concrete_customer_env_not_in_repo": not concrete_env.exists(),
        "dev_bootstrap_disabled": values.get("STANDARD_OPS_DEV_BOOTSTRAP_ENABLED") == "false",
        "external_write_disabled": values.get("OUTBOX_EXTERNAL_WRITE_ENABLED") == "false",
        "worker_disabled": values.get("TRUSTED_INBOUND_WORKER_ENABLED") == "false",
        "admin_bootstrap_password_empty": values.get("ADMIN_BOOTSTRAP_PASSWORD", "") == "",
        "uses_pgvector_store": values.get("KNOWLEDGE_VECTOR_STORE") == "postgres_pgvector_store_v1",
        "database_password_placeholder_for_customer_replacement": values.get("STANDARD_OPS_POSTGRES_PASSWORD")
        == "replace-with-local-random-password",
        "database_url_uses_same_placeholder": "replace-with-local-random-password" in values.get("DATABASE_URL", ""),
        "model_api_keys_empty": values.get("BAILIAN_API_KEY", "") == "" and values.get("DEEPSEEK_API_KEY", "") == "",
    }
    blockers = [f"客户环境模板不满足启动器门禁：{name}" for name, passed in checks.items() if not passed]
    return not blockers, blockers, checks


def _start_script_checks(path: Path) -> tuple[bool, list[str], dict[str, bool]]:
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    checks = {
        "script_exists": path.exists(),
        "uses_customer_env": "customer.env" in text and "customer.env.example" in text,
        "blocks_dev_bootstrap": 'require_value "STANDARD_OPS_DEV_BOOTSTRAP_ENABLED" "false"' in text,
        "blocks_external_write": 'require_value "OUTBOX_EXTERNAL_WRITE_ENABLED" "false"' in text,
        "blocks_inbound_worker": 'require_value "TRUSTED_INBOUND_WORKER_ENABLED" "false"' in text,
        "blocks_default_admin_password": 'require_empty "ADMIN_BOOTSTRAP_PASSWORD"' in text,
        "runs_migration": "python -m alembic -c alembic.ini upgrade head" in text,
        "starts_backend_frontend": "backend frontend" in text,
        "does_not_default_worker_profile": "--profile worker" not in text,
        "does_not_echo_model_keys": "BAILIAN_API_KEY" not in text and "DEEPSEEK_API_KEY" not in text,
    }
    blockers = [f"安全启动脚本不满足启动器门禁：{name}" for name, passed in checks.items() if not passed]
    return not blockers, blockers, checks


def _command_launcher_checks(path: Path) -> tuple[bool, list[str], dict[str, bool]]:
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    checks = {
        "launcher_exists": path.exists(),
        "calls_safe_start_script": "start-local-pilot.sh" in text,
        "uses_customer_env": "customer.env" in text,
        "mentions_customer_env_template": "customer.env.example" in text,
        "mentions_docker_desktop": "Docker Desktop" in text,
        "shows_local_frontend_url": "http://127.0.0.1:5173" in text,
        "shows_external_write_closed": "真实外发" in text and "关闭" in text,
        "keeps_terminal_open": "read -r -p" in text,
        "does_not_auto_create_customer_env": "cp " not in text and "copy " not in text,
        "does_not_enable_worker_profile": "--profile worker" not in text
        and "TRUSTED_INBOUND_WORKER_ENABLED=true" not in text,
        "does_not_echo_model_keys": "BAILIAN_API_KEY" not in text and "DEEPSEEK_API_KEY" not in text,
    }
    blockers = [f"双击启动器不满足门禁：{name}" for name, passed in checks.items() if not passed]
    return not blockers, blockers, checks


def _customer_copy_checks(paths: list[Path]) -> tuple[bool, list[str], dict[str, bool]]:
    combined = "\n".join(path.read_text(encoding="utf-8") for path in paths if path.exists())
    overclaim_phrases = [
        "完整桌面安装器已完成",
        "正式安装器已完成",
        "正式客户签收已完成",
        "真实平台自动外发已接通",
        "真实外发已开启",
        "企业微信已接通",
        "抖音已接通",
        "淘宝已接通",
        "生产级 SLA 已完成",
    ]
    checks = {
        "quick_start_doc_exists": all(path.exists() for path in paths),
        "mentions_docker_desktop": "Docker Desktop" in combined,
        "mentions_customer_env_template": "customer.env.example" in combined,
        "mentions_customer_env": "customer.env" in combined,
        "mentions_command_launcher": "start-local-pilot.command" in combined,
        "mentions_first_owner": "首任负责人" in combined,
        "mentions_external_write_closed": "真实外发默认关闭" in combined or "真实外发" in combined and "关闭" in combined,
        "mentions_diagnostic_and_backup": "诊断包" in combined and "备份" in combined,
        "no_default_password_claim": "默认管理员密码" not in combined or "不预置默认管理员密码" in combined,
        "no_overclaim_phrases": not any(phrase in combined for phrase in overclaim_phrases),
    }
    blockers = [f"客户启动说明不满足门禁：{name}" for name, passed in checks.items() if not passed]
    return not blockers, blockers, checks


def _write_markdown(path: Path, result: dict[str, Any]) -> None:
    readiness = result["readiness"]
    lines = [
        "# H2W-INSTALL1 非技术客户本地启动器 rehearsal",
        "",
        "## 结论",
        "",
        f"- 阶段状态：`{result['status']}`",
        f"- 非技术客户启动器 rehearsal 就绪：`{str(readiness['ready_for_nontechnical_customer_startup_rehearsal']).lower()}`",
        f"- 完整桌面安装器就绪：`{str(readiness['desktop_installer_ready']).lower()}`",
        f"- 原生安装包就绪：`{str(readiness['native_installer_ready']).lower()}`",
        f"- 正式客户签收就绪：`{str(readiness['formal_customer_signoff_ready']).lower()}`",
        f"- 真实平台外发就绪：`{str(readiness['real_platform_send_ready']).lower()}`",
        "",
        "## 本阶段实际完成",
        "",
        "- 新增 macOS 双击启动包装器 `deploy/start-local-pilot.command`。",
        "- 新增客户可读启动说明 `docs/customer/万法常世AI客服本地试点启动说明.md`。",
        "- 新增 INSTALL1 门禁脚本，检查 PACK5、KB1、安全启动脚本、客户环境模板、启动器和客户说明。",
        "- 启动器只调用现有 `deploy/start-local-pilot.sh`，不自动创建客户环境文件、不填写密码、不启用 worker、不打开真实外发。",
        "",
        "## 客户启动路径",
        "",
        "1. 安装并启动 Docker Desktop。",
        "2. 复制 `deploy/customer.env.example` 为 `deploy/customer.env`。",
        "3. 替换本地随机数据库密码。",
        "4. 双击 `deploy/start-local-pilot.command`。",
        "5. 打开 `http://127.0.0.1:5173` 创建首任负责人。",
        "6. 先生成诊断包和备份，再导入知识资料。",
        "",
        "## 停止门禁",
        "",
        "- PACK5 或 KB1 上游证据缺失时，不进入本地试点交付。",
        "- 启动器绕过安全启动脚本、自动写入客户 env、启用 worker profile、展示真实外发已开启时，立即阻断。",
        "- 客户说明出现正式签收、真实平台已接通、完整安装器已完成等越界承诺时，立即阻断。",
        "- `deploy/customer.env` 不应进入仓库；客户只能从模板复制并在本地填写。",
        "",
        "## 阻断项",
        "",
    ]
    lines.extend([f"- {item}" for item in result["blockers"]] or ["- 无"])
    lines.extend(["", "## 不可对外承诺", ""])
    lines.extend([f"- {item}" for item in result["not_ready_for"]])
    lines.extend(
        [
            "",
            "## 固定边界",
            "",
            "- `real_platform_send_performed=false`",
            "- `enterprise_channel_scope_included=false`",
            "- `rpa_formal_delivery_included=false`",
            "- `formal_customer_signoff_performed=false`",
            "- `desktop_installer_ready=false`",
            "- `native_installer_ready=false`",
            "- `customer_env_created_or_modified=false`",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_h2w_install1_nontechnical_customer_starter(
    *,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    doc_path: Path = DOC_PATH,
    pack5_summary: Path = PACK5_SUMMARY,
    kb1_summary: Path = KB1_SUMMARY,
    start_script: Path = START_SCRIPT,
    command_launcher: Path = COMMAND_LAUNCHER,
    quick_start_doc: Path = QUICK_START_DOC,
    customer_env_template: Path = CUSTOMER_ENV_TEMPLATE,
    concrete_customer_env: Path = CUSTOMER_ENV,
    runner: CommandRunner = _run_command,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = output_dir / "summary.json"
    blockers: list[str] = []
    warnings: list[str] = []

    summary_checks: dict[str, dict[str, Any]] = {}
    summary_payloads: dict[str, dict[str, Any]] = {}
    expected_summaries = {
        "pack5": (pack5_summary, "ready_for_customer_local_pilot_handoff_candidate"),
        "kb1": (kb1_summary, "ready_for_customer_specific_knowledge_package_rehearsal"),
    }
    for name, (path, expected_status) in expected_summaries.items():
        ok, actual_status, payload = _summary_status(path, expected_status)
        summary_checks[name] = {
            "path": _display_path(path),
            "expected_status": expected_status,
            "actual_status": actual_status,
            "passed": ok,
        }
        summary_payloads[name] = payload
        if not ok:
            blockers.append(f"{name} 上游证据未就绪：期望 {expected_status}，实际 {actual_status}")

    pack5 = summary_payloads.get("pack5", {})
    if pack5:
        readiness = pack5.get("readiness", {})
        if readiness.get("desktop_installer_ready") is not False:
            blockers.append("PACK5 没有保持完整桌面安装器为 false")
        if readiness.get("formal_customer_signoff_ready") is not False:
            blockers.append("PACK5 没有保持正式客户签收为 false")
        if readiness.get("real_platform_send_ready") is not False:
            blockers.append("PACK5 没有保持真实外发为 false")
    kb1 = summary_payloads.get("kb1", {})
    if kb1:
        readiness = kb1.get("readiness", {})
        if readiness.get("customer_specific_knowledge_ready") is not False:
            blockers.append("KB1 被越界写成客户专属知识库正式 ready")
        if readiness.get("formal_customer_signoff_ready") is not False:
            blockers.append("KB1 没有保持正式客户签收为 false")

    env_ready, env_blockers, env_checks = _customer_env_template_checks(customer_env_template, concrete_customer_env)
    start_ready, start_blockers, start_checks = _start_script_checks(start_script)
    launcher_ready, launcher_blockers, launcher_checks = _command_launcher_checks(command_launcher)
    copy_ready, copy_blockers, copy_checks = _customer_copy_checks([quick_start_doc])
    blockers.extend(env_blockers)
    blockers.extend(start_blockers)
    blockers.extend(launcher_blockers)
    blockers.extend(copy_blockers)

    start_syntax_ready = False
    start_syntax_output = ""
    launcher_syntax_ready = False
    launcher_syntax_output = ""
    if start_script.exists():
        start_syntax_ready, start_syntax_output = _command_ok(["bash", "-n", str(start_script)], runner)
        if not start_syntax_ready:
            blockers.append("安全启动脚本 bash -n 未通过")
    else:
        blockers.append("安全启动脚本不存在")
    if command_launcher.exists():
        launcher_syntax_ready, launcher_syntax_output = _command_ok(["bash", "-n", str(command_launcher)], runner)
        if not launcher_syntax_ready:
            blockers.append("双击启动器 bash -n 未通过")
    else:
        blockers.append("双击启动器不存在")

    ready = (
        all(check["passed"] for check in summary_checks.values())
        and env_ready
        and start_ready
        and launcher_ready
        and copy_ready
        and start_syntax_ready
        and launcher_syntax_ready
        and not blockers
    )
    status = "ready_for_nontechnical_customer_startup_rehearsal" if ready else "blocked"
    result = {
        "phase": PHASE,
        "status": status,
        "readiness": {
            "ready_for_nontechnical_customer_startup_rehearsal": ready,
            "pack5_handoff_ready": summary_checks["pack5"]["passed"],
            "kb1_package_rehearsal_ready": summary_checks["kb1"]["passed"],
            "customer_env_template_safe": env_ready,
            "start_script_safe": start_ready and start_syntax_ready,
            "command_launcher_safe": launcher_ready and launcher_syntax_ready,
            "customer_quick_start_ready": copy_ready,
            "desktop_installer_ready": False,
            "native_installer_ready": False,
            "formal_customer_signoff_ready": False,
            "real_platform_send_ready": False,
            "enterprise_channel_ready": False,
        },
        "checks": {
            "summaries": summary_checks,
            "customer_env_template": env_checks,
            "start_script": start_checks,
            "command_launcher": launcher_checks,
            "customer_copy": copy_checks,
        },
        "command_observations": {
            "start_script_bash_syntax": start_syntax_output,
            "command_launcher_bash_syntax": launcher_syntax_output,
        },
        "blockers": blockers,
        "warnings": warnings,
        "not_ready_for": [
            "完整 macOS dmg / Windows exe 安装器",
            "正式客户准确率签收",
            "真实平台自动外发",
            "企业微信/微信客服/抖音/淘宝/京东/拼多多真实渠道上线",
            "客户专属知识库正式验收",
            "生产环境长期监控、告警和 SLA",
        ],
        "evidence": {
            "summary_json": {"path": _display_path(summary_path)},
            "markdown": {"path": _display_path(doc_path)},
            "command_launcher": {"path": _display_path(command_launcher), "present": command_launcher.exists()},
            "quick_start_doc": {"path": _display_path(quick_start_doc), "present": quick_start_doc.exists()},
            "start_script": {"path": _display_path(start_script), "present": start_script.exists()},
            "pack5_summary": {"path": _display_path(pack5_summary), "present": pack5_summary.exists()},
            "kb1_summary": {"path": _display_path(kb1_summary), "present": kb1_summary.exists()},
        },
        "boundaries": {
            "internal_rehearsal_not_customer_signoff": True,
            "real_platform_send_performed": False,
            "enterprise_channel_scope_included": False,
            "rpa_formal_delivery_included": False,
            "formal_customer_signoff_performed": False,
            "desktop_installer_ready": False,
            "native_installer_ready": False,
            "customer_env_created_or_modified": False,
            "provider_call_performed": False,
        },
        "next_recommended_steps": [
            "H2W-OPS1：售后运维交接演练，串联诊断包、备份、签名更新包、应用、回滚和审计。",
            "H2W-KB2：客户专属知识包导入后复测报告与签收模板，不伪造客户签收。",
            "H2W-INSTALL2：如确实需要，再评估 macOS dmg / Windows exe 原生安装器。",
        ],
    }
    _write_json(summary_path, result)
    _write_markdown(doc_path, result)
    return result


def main() -> int:
    result = run_h2w_install1_nontechnical_customer_starter()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if result["status"] == "blocked" else 0


if __name__ == "__main__":
    raise SystemExit(main())
