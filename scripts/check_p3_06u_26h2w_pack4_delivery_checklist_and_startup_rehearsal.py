#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[1]
PHASE = "H2W-PACK4"
DEFAULT_OUTPUT_DIR = ROOT / "output/p3_06u_26h2w_pack4_delivery_checklist_and_startup_rehearsal"
DOC_PATH = ROOT / "docs/P3-06U-26H2W_PACK4_LOCAL_PILOT_DELIVERY_CHECKLIST.md"
PACK3_SUMMARY = ROOT / "output/p3_06u_26h2w_pack3_local_pilot_candidate_readiness/summary.json"
START_SCRIPT = ROOT / "deploy/start-local-pilot.sh"
CUSTOMER_ENV_TEMPLATE = ROOT / "deploy/customer.env.example"
COMPOSE_FILES = [ROOT / "deploy/docker-compose.yml", ROOT / "deploy/docker-compose.pilot.yml"]

CommandRunner = Callable[[list[str]], subprocess.CompletedProcess[str]]


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _run_command(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=ROOT, text=True, capture_output=True, timeout=90, check=False)


def _command_ok(command: list[str], runner: CommandRunner) -> tuple[bool, str]:
    try:
        result = runner(command)
    except Exception as exc:  # pragma: no cover - host CLI differences
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


def _start_script_checks(path: Path) -> tuple[bool, list[str], dict[str, bool]]:
    if not path.exists():
        return False, [f"缺少本地试点启动脚本：{_display_path(path)}"], {}
    text = path.read_text(encoding="utf-8")
    checks = {
        "uses_customer_env": "customer.env" in text and "customer.env.example" in text,
        "checks_dev_bootstrap_off": 'require_value "STANDARD_OPS_DEV_BOOTSTRAP_ENABLED" "false"' in text,
        "checks_external_write_off": 'require_value "OUTBOX_EXTERNAL_WRITE_ENABLED" "false"' in text,
        "checks_worker_off": 'require_value "TRUSTED_INBOUND_WORKER_ENABLED" "false"' in text,
        "checks_pgvector_store": 'require_value "KNOWLEDGE_VECTOR_STORE" "postgres_pgvector_store_v1"' in text,
        "blocks_default_admin_password": 'require_empty "ADMIN_BOOTSTRAP_PASSWORD"' in text,
        "blocks_template_database_password": "replace-with-local-random-password" in text
        and "WANFA_ALLOW_TEMPLATE_PASSWORD_FOR_REHEARSAL" in text,
        "runs_alembic_migration": "python -m alembic -c alembic.ini upgrade head" in text,
        "starts_only_core_services": "postgres redis" in text and "backend frontend" in text,
        "does_not_enable_worker_profile": "--profile worker" not in text,
        "does_not_echo_secrets": "BAILIAN_API_KEY" not in text and "DEEPSEEK_API_KEY" not in text,
    }
    blockers = [f"启动脚本缺少或违反门禁：{name}" for name, passed in checks.items() if not passed]
    return not blockers, blockers, checks


def _customer_env_template_checks(path: Path) -> tuple[bool, list[str], dict[str, bool]]:
    if not path.exists():
        return False, [f"缺少客户环境模板：{_display_path(path)}"], {}
    values = _env_map(path)
    checks = {
        "dev_bootstrap_disabled": values.get("STANDARD_OPS_DEV_BOOTSTRAP_ENABLED") == "false",
        "external_write_disabled": values.get("OUTBOX_EXTERNAL_WRITE_ENABLED") == "false",
        "worker_disabled": values.get("TRUSTED_INBOUND_WORKER_ENABLED") == "false",
        "admin_bootstrap_password_empty": values.get("ADMIN_BOOTSTRAP_PASSWORD", "") == "",
        "uses_pgvector_store": values.get("KNOWLEDGE_VECTOR_STORE") == "postgres_pgvector_store_v1",
        "database_password_is_template_not_secret": values.get("STANDARD_OPS_POSTGRES_PASSWORD")
        == "replace-with-local-random-password",
        "database_url_uses_template_password": "replace-with-local-random-password" in values.get("DATABASE_URL", ""),
        "model_keys_empty": values.get("BAILIAN_API_KEY", "") == "" and values.get("DEEPSEEK_API_KEY", "") == "",
    }
    blockers = [f"客户环境模板缺少或违反门禁：{name}" for name, passed in checks.items() if not passed]
    return not blockers, blockers, checks


def _compose_static_checks(paths: list[Path]) -> tuple[bool, list[str], dict[str, bool]]:
    missing_files = [path for path in paths if not path.exists()]
    if missing_files:
        return False, [f"缺少 compose 文件：{_display_path(path)}" for path in missing_files], {}
    combined = "\n".join(path.read_text(encoding="utf-8") for path in paths)
    checks = {
        "contains_postgres_pgvector": "pgvector/pgvector:pg16" in combined,
        "contains_redis": "redis:7-alpine" in combined,
        "backend_external_write_disabled_in_pilot": 'OUTBOX_EXTERNAL_WRITE_ENABLED: "false"' in combined,
        "backend_worker_disabled_in_pilot": 'TRUSTED_INBOUND_WORKER_ENABLED: "false"' in combined,
        "worker_profile_exists_but_is_profile_gated": 'profiles: ["worker"]' in combined,
        "frontend_service_present": "frontend:" in combined,
        "backend_service_present": "backend:" in combined,
    }
    blockers = [f"compose 静态配置缺少或违反门禁：{name}" for name, passed in checks.items() if not passed]
    return not blockers, blockers, checks


def _write_markdown(path: Path, result: dict[str, Any]) -> None:
    readiness = result["readiness"]
    lines = [
        "# H2W-PACK4 本地试点交付清单与安全启动 rehearsal",
        "",
        "## 结论",
        "",
        f"- 阶段状态：`{result['status']}`",
        f"- PACK3 上游候选已就绪：`{str(readiness['pack3_ready']).lower()}`",
        f"- 客户安全启动脚本已就绪：`{str(readiness['start_script_ready']).lower()}`",
        f"- 客户环境模板已就绪：`{str(readiness['customer_env_template_ready']).lower()}`",
        f"- Compose 静态解析已通过：`{str(readiness['compose_config_ready']).lower()}`",
        f"- worker 默认不启动：`{str(readiness['worker_profile_excluded_by_default']).lower()}`",
        f"- 可进入客户本地试点启动 rehearsal：`{str(readiness['ready_for_customer_local_pilot_startup_rehearsal']).lower()}`",
        "",
        "## 客户本地交付步骤",
        "",
        "1. 安装并启动 Docker Desktop。",
        "2. 复制 `deploy/customer.env.example` 为 `deploy/customer.env`。",
        "3. 把 `STANDARD_OPS_POSTGRES_PASSWORD` 和 `DATABASE_URL` 里的模板密码替换为本地随机密码。",
        "4. 运行 `deploy/start-local-pilot.sh deploy/customer.env`。",
        "5. 打开前端工作台，在登录页创建首任负责人；系统不预置默认管理员密码。",
        "",
        "## 停止门禁",
        "",
        "- 客户环境里开发 bootstrap、真实外发或入站 worker 任一开启，禁止启动。",
        "- 未替换模板数据库密码，禁止启动；只有内部 rehearsal 可显式设置 `WANFA_ALLOW_TEMPLATE_PASSWORD_FOR_REHEARSAL=true`。",
        "- 启动命令不得默认启用 `worker` profile。",
        "- 没有 PACK3 上游候选证据，不进入客户本地试点启动 rehearsal。",
        "- 本阶段不代表完整桌面安装器、正式客户签收、真实渠道上线或生产 SLA。",
        "",
        "## 阻断项",
        "",
    ]
    lines.extend([f"- {item}" for item in result["blockers"]] or ["- 无"])
    lines.extend(["", "## 警告", ""])
    lines.extend([f"- {item}" for item in result["warnings"]] or ["- 无"])
    lines.extend(["", "## 验收证据", ""])
    for name, evidence in result["evidence"].items():
        if isinstance(evidence, dict) and "path" in evidence:
            lines.append(f"- {name}: `{evidence['path']}`")
    lines.extend(["", "## 不可对外承诺", ""])
    lines.extend([f"- {item}" for item in result["not_ready_for"]])
    lines.extend(
        [
            "",
            "## 固定边界",
            "",
            "- `real_platform_send_performed=false`",
            "- `enterprise_channel_scope_included=false`",
            "- `formal_customer_signoff_performed=false`",
            "- `desktop_installer_ready=false`",
            "- `rpa_formal_delivery_included=false`",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_h2w_pack4_delivery_checklist_and_startup_rehearsal(
    *,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    doc_path: Path = DOC_PATH,
    pack3_summary: Path = PACK3_SUMMARY,
    start_script: Path = START_SCRIPT,
    customer_env_template: Path = CUSTOMER_ENV_TEMPLATE,
    compose_files: list[Path] | None = None,
    runner: CommandRunner = _run_command,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = output_dir / "summary.json"
    compose_files = compose_files or COMPOSE_FILES
    blockers: list[str] = []
    warnings: list[str] = []

    pack3_ready = False
    if not pack3_summary.exists():
        blockers.append(f"缺少 PACK3 上游摘要：{_display_path(pack3_summary)}")
    else:
        try:
            pack3 = _read_json(pack3_summary)
            pack3_ready = (
                pack3.get("status") == "ready_for_local_controlled_pilot_candidate"
                and pack3.get("readiness", {}).get("ready_for_local_controlled_pilot_candidate") is True
                and pack3.get("readiness", {}).get("formal_customer_signoff_ready") is False
                and pack3.get("boundaries", {}).get("real_platform_send_performed") is False
            )
        except json.JSONDecodeError:
            blockers.append("PACK3 上游摘要不是合法 JSON")
        if not pack3_ready:
            blockers.append("PACK3 上游候选证据未 ready，不能进入 PACK4")

    start_script_ready, start_script_blockers, start_script_checks = _start_script_checks(start_script)
    customer_env_ready, env_blockers, env_checks = _customer_env_template_checks(customer_env_template)
    compose_static_ready, compose_static_blockers, compose_static_checks = _compose_static_checks(compose_files)
    blockers.extend(start_script_blockers)
    blockers.extend(env_blockers)
    blockers.extend(compose_static_blockers)

    syntax_ready = False
    syntax_output = ""
    if start_script.exists():
        syntax_ready, syntax_output = _command_ok(["bash", "-n", str(start_script)], runner)
        if not syntax_ready:
            blockers.append("本地试点启动脚本 bash -n 未通过")

    compose_config_ready = False
    compose_output = ""
    compose_command = [
        "docker",
        "compose",
        "--env-file",
        str(customer_env_template),
        "-f",
        str(ROOT / "deploy/docker-compose.yml"),
        "-f",
        str(ROOT / "deploy/docker-compose.pilot.yml"),
        "config",
        "--quiet",
    ]
    compose_config_ready, compose_output = _command_ok(compose_command, runner)
    if not compose_config_ready:
        blockers.append("Docker compose 静态配置解析未通过")

    executable_ready = os.access(start_script, os.X_OK) if start_script.exists() else False
    if not executable_ready:
        warnings.append("本地启动脚本尚未具备可执行权限；将尝试在本轮设置 chmod +x")

    worker_profile_excluded = bool(start_script_checks.get("does_not_enable_worker_profile")) and bool(
        start_script_checks.get("starts_only_core_services")
    )
    ready = (
        pack3_ready
        and start_script_ready
        and customer_env_ready
        and compose_static_ready
        and syntax_ready
        and compose_config_ready
        and worker_profile_excluded
        and not blockers
    )
    status = "ready_for_customer_local_pilot_startup_rehearsal" if ready else "blocked"

    result = {
        "phase": PHASE,
        "status": status,
        "readiness": {
            "pack3_ready": pack3_ready,
            "start_script_ready": start_script_ready,
            "start_script_syntax_ready": syntax_ready,
            "start_script_executable": executable_ready,
            "customer_env_template_ready": customer_env_ready,
            "compose_static_ready": compose_static_ready,
            "compose_config_ready": compose_config_ready,
            "worker_profile_excluded_by_default": worker_profile_excluded,
            "ready_for_customer_local_pilot_startup_rehearsal": ready,
            "formal_customer_signoff_ready": False,
            "real_platform_send_ready": False,
            "desktop_installer_ready": False,
        },
        "checks": {
            "start_script": start_script_checks,
            "customer_env_template": env_checks,
            "compose_static": compose_static_checks,
        },
        "command_observations": {
            "bash_syntax": syntax_output,
            "compose_config": compose_output,
        },
        "blockers": blockers,
        "warnings": warnings,
        "not_ready_for": [
            "完整桌面安装器或双击安装包",
            "正式客户准确率签收",
            "真实平台自动外发",
            "企业微信/微信客服/抖音/淘宝/京东/拼多多真实渠道上线",
            "客户专属知识库验收",
            "生产环境长期监控、告警和 SLA",
        ],
        "next_recommended_steps": [
            "H2W-FE4：封版候选 UI 客户视角逐页点击验收，隐藏或禁用无真实动作按钮。",
            "H2W-KB1：替换内部 100 题为某个共创客户授权后的真实脱敏题库。",
            "H2W-INSTALL1：如需交付非技术客户，再把脚本包装为 macOS/Windows 桌面安装器专项。",
        ],
        "evidence": {
            "summary_json": {"path": _display_path(summary_path)},
            "markdown": {"path": _display_path(doc_path)},
            "start_script": {"path": _display_path(start_script), "present": start_script.exists()},
            "customer_env_template": {"path": _display_path(customer_env_template), "present": customer_env_template.exists()},
            "pack3_summary": {"path": _display_path(pack3_summary), "present": pack3_summary.exists()},
        },
        "boundaries": {
            "internal_rehearsal_not_customer_signoff": True,
            "real_platform_send_performed": False,
            "enterprise_channel_scope_included": False,
            "rpa_formal_delivery_included": False,
            "formal_customer_signoff_performed": False,
            "desktop_installer_ready": False,
        },
    }
    _write_json(summary_path, result)
    _write_markdown(doc_path, result)
    return result


def main() -> int:
    result = run_h2w_pack4_delivery_checklist_and_startup_rehearsal()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if result["status"] == "blocked" else 0


if __name__ == "__main__":
    raise SystemExit(main())
