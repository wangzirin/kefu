#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[1]
PHASE = "H2W-PACK5"
DEFAULT_OUTPUT_DIR = ROOT / "output/p3_06u_26h2w_pack5_customer_handoff_package"
DOC_PATH = ROOT / "docs/P3-06U-26H2W_PACK5_CUSTOMER_LOCAL_PILOT_HANDOFF_PACKAGE.md"

PACK2_SUMMARY = ROOT / "output/p3_06u_26h2w_pack2_full_stack_startup_rehearsal/summary.json"
PACK3_SUMMARY = ROOT / "output/p3_06u_26h2w_pack3_local_pilot_candidate_readiness/summary.json"
PACK4_SUMMARY = ROOT / "output/p3_06u_26h2w_pack4_delivery_checklist_and_startup_rehearsal/summary.json"
FE4_SUMMARY = ROOT / "output/p3_06u_26h2w_fe4_customer_ui_sealed_candidate/summary.json"
FE4_CLICK_SUMMARY = ROOT / "output/p3_06u_26h2w_fe4_customer_visible_click_qa/summary.json"
RUNTIME_SUMMARY = ROOT / "output/p3_06u_26h2w7d_runtime_pgvector_rehearsal/summary.json"
MODEL1_SUMMARY = ROOT / "output/p3_06u_26h2w_model1_bailian_cost_sample/summary.json"
TRIAL1_SUMMARY = ROOT / "output/p3_06u_26h2w_trial1_internal_100q_rehearsal_report/summary.json"

START_SCRIPT = ROOT / "deploy/start-local-pilot.sh"
CUSTOMER_ENV_TEMPLATE = ROOT / "deploy/customer.env.example"
CUSTOMER_ENV = ROOT / "deploy/customer.env"
COMPOSE_FILES = [ROOT / "deploy/docker-compose.yml", ROOT / "deploy/docker-compose.pilot.yml"]

REQUIRED_CUSTOMER_DOCS = [
    ROOT / "docs/customer/万法常世AI智能客服系统_产品介绍.md",
    ROOT / "docs/customer/万法常世AI智能客服系统_客户使用手册.md",
    ROOT / "docs/customer/万法常世AI智能客服系统_服务体系介绍.md",
    ROOT / "docs/customer/万法常世AI智能客服系统_正式部署后运营模式手册.md",
]

REQUIRED_INTERNAL_DOCS = [
    ROOT / "README.md",
    ROOT / "docs/P3-06U-26H2W_PACK3_LOCAL_PILOT_CANDIDATE_READINESS.md",
    ROOT / "docs/P3-06U-26H2W_PACK4_LOCAL_PILOT_DELIVERY_CHECKLIST.md",
    ROOT / "docs/P3-06U-26H2W_FE4_CUSTOMER_UI_SEALED_CANDIDATE.md",
    ROOT / "docs/PRODUCTIZATION_MASTER_PLAN_LITE_AND_STANDARD.md",
]

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


def _summary_status(path: Path, expected_status: str) -> tuple[bool, str, dict[str, Any]]:
    if not path.exists():
        return False, "missing", {}
    try:
        payload = _read_json(path)
    except json.JSONDecodeError:
        return False, "invalid_json", {}
    status = str(payload.get("status", "missing_status"))
    return status == expected_status, status, payload


def _required_files_present(paths: list[Path]) -> tuple[bool, list[str], list[dict[str, Any]]]:
    missing = [path for path in paths if not path.exists()]
    inventory = [{"path": _display_path(path), "present": path.exists()} for path in paths]
    return not missing, [f"缺少交付文件：{_display_path(path)}" for path in missing], inventory


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
        "budget_guard_enabled": values.get("MODEL_BUDGET_GUARD_ENABLED") == "true",
    }
    blockers = [f"客户环境模板不满足交付门禁：{name}" for name, passed in checks.items() if not passed]
    return not blockers, blockers, checks


def _start_script_checks(path: Path) -> tuple[bool, list[str], dict[str, bool]]:
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    checks = {
        "script_exists": path.exists(),
        "uses_customer_env_file": "customer.env" in text and "customer.env.example" in text,
        "blocks_dev_bootstrap": 'require_value "STANDARD_OPS_DEV_BOOTSTRAP_ENABLED" "false"' in text,
        "blocks_external_write": 'require_value "OUTBOX_EXTERNAL_WRITE_ENABLED" "false"' in text,
        "blocks_inbound_worker": 'require_value "TRUSTED_INBOUND_WORKER_ENABLED" "false"' in text,
        "requires_pgvector": 'require_value "KNOWLEDGE_VECTOR_STORE" "postgres_pgvector_store_v1"' in text,
        "blocks_default_admin_password": 'require_empty "ADMIN_BOOTSTRAP_PASSWORD"' in text,
        "blocks_template_password_without_rehearsal_override": "replace-with-local-random-password" in text
        and "WANFA_ALLOW_TEMPLATE_PASSWORD_FOR_REHEARSAL" in text,
        "runs_alembic_migration": "python -m alembic -c alembic.ini upgrade head" in text,
        "does_not_default_worker_profile": "--profile worker" not in text,
        "does_not_echo_model_keys": "BAILIAN_API_KEY" not in text and "DEEPSEEK_API_KEY" not in text,
    }
    blockers = [f"本地启动脚本不满足交付门禁：{name}" for name, passed in checks.items() if not passed]
    return not blockers, blockers, checks


def _compose_files_checks(paths: list[Path]) -> tuple[bool, list[str], dict[str, bool]]:
    existing_text = "\n".join(path.read_text(encoding="utf-8") for path in paths if path.exists())
    checks = {
        "all_compose_files_exist": all(path.exists() for path in paths),
        "postgres_pgvector_service_present": "pgvector/pgvector:pg16" in existing_text,
        "redis_service_present": "redis:7-alpine" in existing_text,
        "backend_service_present": "backend:" in existing_text,
        "frontend_service_present": "frontend:" in existing_text,
        "external_write_disabled_in_pilot": 'OUTBOX_EXTERNAL_WRITE_ENABLED: "false"' in existing_text,
        "worker_disabled_in_pilot": 'TRUSTED_INBOUND_WORKER_ENABLED: "false"' in existing_text,
        "worker_is_profile_gated": 'profiles: ["worker"]' in existing_text,
    }
    blockers = [f"Compose 交付配置不满足门禁：{name}" for name, passed in checks.items() if not passed]
    return not blockers, blockers, checks


def _write_markdown(path: Path, result: dict[str, Any]) -> None:
    readiness = result["readiness"]
    lines = [
        "# H2W-PACK5 客户本地试点交付包",
        "",
        "## 结论",
        "",
        f"- 阶段状态：`{result['status']}`",
        f"- 可作为客户本地试点交付包候选：`{str(readiness['ready_for_customer_local_pilot_handoff_candidate']).lower()}`",
        f"- PACK4 安全启动入口就绪：`{str(readiness['pack4_startup_ready']).lower()}`",
        f"- FE4 客户可见界面就绪：`{str(readiness['fe4_customer_ui_ready']).lower()}`",
        f"- FE4 浏览器点击 QA 通过：`{str(readiness['fe4_browser_click_ready']).lower()}`",
        f"- 客户资料文档齐备：`{str(readiness['customer_docs_ready']).lower()}`",
        f"- 部署文件齐备且安全：`{str(readiness['deploy_files_ready']).lower()}`",
        "",
        "## 交付对象",
        "",
        "本阶段面向小微企业本地受控试点。交付目标是让试点客户能在本机或局域网内启动客服中台、创建首任负责人、导入资料、查看会话与质量页面，并把诊断包、备份和更新流程纳入后续售后闭环。",
        "",
        "## 交付包包含",
        "",
    ]
    for item in result["package_inventory"]:
        lines.append(f"- `{item['path']}`：{'已存在' if item['present'] else '缺失'}")
    lines.extend(
        [
            "",
            "## 客户启动步骤",
            "",
            "1. 安装并启动 Docker Desktop。",
            "2. 复制 `deploy/customer.env.example` 为 `deploy/customer.env`。",
            "3. 替换 `STANDARD_OPS_POSTGRES_PASSWORD` 和 `DATABASE_URL` 中的模板数据库密码。",
            "4. 运行 `deploy/start-local-pilot.sh deploy/customer.env`。",
            "5. 在本地登录页创建首任负责人账号；系统不预置默认管理员密码。",
            "6. 进入账号与本地维护页，先做一次诊断包和备份演练，再进入知识导入和试点操作。",
            "",
            "## 停止门禁",
            "",
            "- 缺 PACK3、PACK4、FE4 或 FE4 浏览器点击证据时，不交付给客户试用。",
            "- `deploy/customer.env` 不应进入交付仓库；客户只能从模板复制并在本地填写。",
            "- 客户模板里出现真实模型 key、默认管理员密码、真实外发开启或入站 worker 开启时，立即阻断。",
            "- 启动脚本没有数据库迁移、没有阻断模板密码、或默认启用 worker profile 时，立即阻断。",
            "- 当前交付不包含真实平台自动外发、企业渠道真实上线、正式准确率签收或生产 SLA。",
            "",
            "## 运维交接",
            "",
            "- 客户本地问题优先通过诊断包、备份、更新包预检和审计记录排查。",
            "- 命中率下降先走知识补充、标准答案修订、禁用承诺和转人工规则复测，不直接归因于模型失效。",
            "- 程序更新必须先备份、预检、应用、健康检查，再保留回滚记录。",
            "",
            "## 阻断项",
            "",
        ]
    )
    lines.extend([f"- {item}" for item in result["blockers"]] or ["- 无"])
    lines.extend(["", "## 警告", ""])
    lines.extend([f"- {item}" for item in result["warnings"]] or ["- 无"])
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
            "- `customer_specific_knowledge_ready=false`",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_h2w_pack5_customer_handoff_package(
    *,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    doc_path: Path = DOC_PATH,
    pack2_summary: Path = PACK2_SUMMARY,
    pack3_summary: Path = PACK3_SUMMARY,
    pack4_summary: Path = PACK4_SUMMARY,
    fe4_summary: Path = FE4_SUMMARY,
    fe4_click_summary: Path = FE4_CLICK_SUMMARY,
    runtime_summary: Path = RUNTIME_SUMMARY,
    model1_summary: Path = MODEL1_SUMMARY,
    trial1_summary: Path = TRIAL1_SUMMARY,
    start_script: Path = START_SCRIPT,
    customer_env_template: Path = CUSTOMER_ENV_TEMPLATE,
    concrete_customer_env: Path = CUSTOMER_ENV,
    compose_files: list[Path] | None = None,
    required_customer_docs: list[Path] | None = None,
    required_internal_docs: list[Path] | None = None,
    runner: CommandRunner = _run_command,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = output_dir / "summary.json"
    compose_files = compose_files or COMPOSE_FILES
    required_customer_docs = required_customer_docs or REQUIRED_CUSTOMER_DOCS
    required_internal_docs = required_internal_docs or REQUIRED_INTERNAL_DOCS

    blockers: list[str] = []
    warnings: list[str] = []

    expected_summaries = {
        "pack2": (pack2_summary, "passed_full_stack_backend_startup_rehearsal"),
        "pack3": (pack3_summary, "ready_for_local_controlled_pilot_candidate"),
        "pack4": (pack4_summary, "ready_for_customer_local_pilot_startup_rehearsal"),
        "fe4": (fe4_summary, "ready_for_customer_visible_ui_candidate"),
        "fe4_browser_click": (fe4_click_summary, "passed_customer_visible_click_qa"),
        "runtime_pgvector": (runtime_summary, "ready_for_runtime_rehearsal"),
        "model1_cost": (model1_summary, "passed_real_small_sample_cost_rehearsal"),
        "trial1_internal_100q": (trial1_summary, "passed_internal_rehearsal_report"),
    }
    summary_checks: dict[str, dict[str, Any]] = {}
    summary_payloads: dict[str, dict[str, Any]] = {}
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

    fe4_click = summary_payloads.get("fe4_browser_click", {})
    if fe4_click:
        if fe4_click.get("owner_login_performed_through_ui") is not True:
            blockers.append("FE4 浏览器点击 QA 未证明通过真实登录页创建负责人")
        if fe4_click.get("demo_mode_used") is True:
            blockers.append("FE4 浏览器点击 QA 使用了演示模式，不能作为客户交付证据")
        if fe4_click.get("external_platform_write_performed") is not False:
            blockers.append("FE4 浏览器点击 QA 未确认真实外发关闭")

    pack3 = summary_payloads.get("pack3", {})
    if pack3 and pack3.get("readiness", {}).get("formal_customer_signoff_ready") is not False:
        blockers.append("PACK3 上游没有保持正式客户签收为 false")
    pack4 = summary_payloads.get("pack4", {})
    if pack4 and pack4.get("readiness", {}).get("desktop_installer_ready") is not False:
        blockers.append("PACK4 上游没有保持完整桌面安装器为 false")
    trial1 = summary_payloads.get("trial1_internal_100q", {})
    if trial1 and trial1.get("boundaries", {}).get("internal_rehearsal_not_customer_signoff") is not True:
        blockers.append("TRIAL1 没有明确内部演练不是客户签收")

    customer_docs_ready, customer_doc_blockers, customer_docs_inventory = _required_files_present(required_customer_docs)
    internal_docs_ready, internal_doc_blockers, internal_docs_inventory = _required_files_present(required_internal_docs)
    deploy_files_ready, deploy_file_blockers, deploy_inventory = _required_files_present(
        [start_script, customer_env_template, *compose_files]
    )
    blockers.extend(customer_doc_blockers)
    blockers.extend(internal_doc_blockers)
    blockers.extend(deploy_file_blockers)

    env_ready, env_blockers, env_checks = _customer_env_template_checks(customer_env_template, concrete_customer_env)
    start_ready, start_blockers, start_checks = _start_script_checks(start_script)
    compose_ready, compose_blockers, compose_checks = _compose_files_checks(compose_files)
    blockers.extend(env_blockers)
    blockers.extend(start_blockers)
    blockers.extend(compose_blockers)

    syntax_ready = False
    syntax_output = ""
    if start_script.exists():
        syntax_ready, syntax_output = _command_ok(["bash", "-n", str(start_script)], runner)
        if not syntax_ready:
            blockers.append("本地启动脚本 bash -n 未通过")
    else:
        blockers.append("本地启动脚本不存在，无法执行 bash -n")

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

    package_inventory = [
        *deploy_inventory,
        *customer_docs_inventory,
        *internal_docs_inventory,
    ]

    ready = (
        all(check["passed"] for check in summary_checks.values())
        and customer_docs_ready
        and internal_docs_ready
        and deploy_files_ready
        and env_ready
        and start_ready
        and compose_ready
        and syntax_ready
        and compose_config_ready
        and not blockers
    )
    status = "ready_for_customer_local_pilot_handoff_candidate" if ready else "blocked"

    result = {
        "phase": PHASE,
        "status": status,
        "readiness": {
            "ready_for_customer_local_pilot_handoff_candidate": ready,
            "pack4_startup_ready": summary_checks["pack4"]["passed"],
            "fe4_customer_ui_ready": summary_checks["fe4"]["passed"],
            "fe4_browser_click_ready": summary_checks["fe4_browser_click"]["passed"],
            "customer_docs_ready": customer_docs_ready,
            "internal_docs_ready": internal_docs_ready,
            "deploy_files_ready": deploy_files_ready,
            "customer_env_template_safe": env_ready,
            "start_script_safe": start_ready and syntax_ready,
            "compose_safe": compose_ready and compose_config_ready,
            "formal_customer_signoff_ready": False,
            "real_platform_send_ready": False,
            "desktop_installer_ready": False,
            "customer_specific_knowledge_ready": False,
            "enterprise_channel_ready": False,
        },
        "checks": {
            "summaries": summary_checks,
            "customer_env_template": env_checks,
            "start_script": start_checks,
            "compose": compose_checks,
        },
        "command_observations": {
            "bash_syntax": syntax_output,
            "compose_config": compose_output,
        },
        "package_inventory": package_inventory,
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
            "H2W-KB1：准备客户专属知识包导入与签收 rehearsal。",
            "H2W-INSTALL1：如面向非技术客户，制作桌面安装器/启动器专项。",
            "H2W-OPS1：补客户月度运维复盘和诊断包处理 SOP 的交付演练。",
        ],
        "evidence": {
            "summary_json": {"path": _display_path(summary_path)},
            "markdown": {"path": _display_path(doc_path)},
            "pack4_summary": {"path": _display_path(pack4_summary), "present": pack4_summary.exists()},
            "fe4_summary": {"path": _display_path(fe4_summary), "present": fe4_summary.exists()},
            "fe4_click_summary": {"path": _display_path(fe4_click_summary), "present": fe4_click_summary.exists()},
            "start_script": {"path": _display_path(start_script), "present": start_script.exists()},
            "customer_env_template": {"path": _display_path(customer_env_template), "present": customer_env_template.exists()},
        },
        "boundaries": {
            "internal_rehearsal_not_customer_signoff": True,
            "real_platform_send_performed": False,
            "enterprise_channel_scope_included": False,
            "rpa_formal_delivery_included": False,
            "formal_customer_signoff_performed": False,
            "desktop_installer_ready": False,
            "customer_specific_knowledge_ready": False,
        },
    }
    _write_json(summary_path, result)
    _write_markdown(doc_path, result)
    return result


def main() -> int:
    result = run_h2w_pack5_customer_handoff_package()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if result["status"] == "blocked" else 0


if __name__ == "__main__":
    raise SystemExit(main())
