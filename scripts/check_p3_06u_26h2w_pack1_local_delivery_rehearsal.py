#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[1]
PHASE = "H2W-PACK1"
DEFAULT_OUTPUT_DIR = ROOT / "output/p3_06u_26h2w_pack1_local_delivery_rehearsal"
DOC_PATH = ROOT / "docs/P3-06U-26H2W_PACK1_LOCAL_DELIVERY_REHEARSAL.md"
CUSTOMER_ENV = ROOT / "deploy/customer.env.example"
COMPOSE_FILES = [ROOT / "deploy/docker-compose.yml", ROOT / "deploy/docker-compose.pilot.yml"]
LOCAL_MAINTENANCE_UI = ROOT / "output/p3_06u_26h2w8b_local_maintenance_ui/summary.json"
FE3_SUMMARY = ROOT / "output/p3_06u_26h2w_fe3_frontend_browser_workflow_qa/summary.json"
H2W7D_RUNTIME = ROOT / "output/p3_06u_26h2w7d_runtime_pgvector_rehearsal/summary.json"

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
    return subprocess.run(command, cwd=ROOT, text=True, capture_output=True, timeout=60, check=False)


def _command_ok(command: list[str], runner: CommandRunner) -> tuple[bool, str]:
    try:
        result = runner(command)
    except Exception as exc:  # pragma: no cover
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


def _contains_all(path: Path, markers: list[str]) -> tuple[bool, list[str]]:
    if not path.exists():
        return False, markers
    text = path.read_text(encoding="utf-8")
    missing = [marker for marker in markers if marker not in text]
    return not missing, missing


def _write_markdown(path: Path, result: dict[str, Any]) -> None:
    readiness = result["readiness"]
    lines = [
        "# H2W-PACK1 本地交付封版 rehearsal",
        "",
        "## 结论",
        "",
        f"- 阶段状态：`{result['status']}`",
        f"- 客户环境模板安全：`{str(readiness['customer_env_template_ready']).lower()}`",
        f"- Compose 静态配置可解析：`{str(readiness['compose_config_ready']).lower()}`",
        f"- 本地维护 UI 证据 ready：`{str(readiness['local_maintenance_ui_ready']).lower()}`",
        f"- 前端 FE3 ready：`{str(readiness['fe3_ready']).lower()}`",
        f"- pgvector runtime ready：`{str(readiness['pgvector_runtime_ready']).lower()}`",
        f"- Docker daemon 可启动演练：`{str(readiness['docker_daemon_ready']).lower()}`",
        f"- 可作为本地试点包候选：`{str(readiness['ready_for_local_pilot_package_candidate']).lower()}`",
        "",
        "## 停止门禁",
        "",
        "- 客户模板必须关闭开发 bootstrap、关闭真实外发，并且不能内置默认管理员密码。",
        "- 客户必须能通过界面看到诊断、备份、恢复、更新与回滚 rehearsal 入口。",
        "- Docker/pgvector runtime 未跑通时，只能写封版候选，不写完整本地交付完成。",
        "- 本阶段不新增远控客户电脑能力，不自动上传客户数据。",
        "",
        "## 阻断项",
        "",
    ]
    lines.extend([f"- {item}" for item in result["blockers"]] or ["- 无"])
    lines.extend(["", "## 警告", ""])
    lines.extend([f"- {item}" for item in result["warnings"]] or ["- 无"])
    lines.extend(
        [
            "",
            "## 输出",
            "",
            f"- `{result['evidence']['summary_json']['path']}`",
            "",
            "## 边界",
            "",
            "- `customer_remote_control_added=false`",
            "- `automatic_upload_enabled=false`",
            "- `real_platform_send_performed=false`",
            "- `formal_customer_signoff_performed=false`",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_h2w_pack1_local_delivery_rehearsal(
    *,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    customer_env: Path = CUSTOMER_ENV,
    local_maintenance_summary: Path = LOCAL_MAINTENANCE_UI,
    fe3_summary: Path = FE3_SUMMARY,
    h2w7d_runtime_summary: Path = H2W7D_RUNTIME,
    runner: CommandRunner = _run_command,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = output_dir / "summary.json"
    blockers: list[str] = []
    warnings: list[str] = []

    env_values = _env_map(customer_env)
    customer_env_template_ready = bool(env_values)
    if not customer_env.exists():
        blockers.append(f"缺少客户封版环境模板：{_display_path(customer_env)}")
    else:
        if env_values.get("STANDARD_OPS_DEV_BOOTSTRAP_ENABLED") != "false":
            blockers.append("客户模板未关闭 STANDARD_OPS_DEV_BOOTSTRAP_ENABLED")
            customer_env_template_ready = False
        if env_values.get("OUTBOX_EXTERNAL_WRITE_ENABLED") != "false":
            blockers.append("客户模板未关闭 OUTBOX_EXTERNAL_WRITE_ENABLED")
            customer_env_template_ready = False
        if env_values.get("ADMIN_BOOTSTRAP_PASSWORD"):
            blockers.append("客户模板仍包含默认管理员密码；首任负责人必须由界面创建")
            customer_env_template_ready = False
        if env_values.get("KNOWLEDGE_VECTOR_STORE") != "postgres_pgvector_store_v1":
            blockers.append("客户模板未指向 pgvector 知识库候选")
            customer_env_template_ready = False

    docker_ready, docker_output = _command_ok(["docker", "info", "--format", "{{json .ServerVersion}}"], runner)
    compose_ready, compose_output = _command_ok(
        ["docker", "compose", "-f", "deploy/docker-compose.yml", "-f", "deploy/docker-compose.pilot.yml", "config", "--quiet"],
        runner,
    )
    if not compose_ready:
        blockers.append("Docker compose 静态配置未通过")
    if not docker_ready:
        warnings.append("Docker daemon 未启动，无法完成真实空库启动 rehearsal")

    compose_markers_ready = True
    for compose_file in COMPOSE_FILES:
        ok, missing = _contains_all(compose_file, ["OUTBOX_EXTERNAL_WRITE_ENABLED", "postgres", "redis", "frontend", "backend"])
        if not ok:
            compose_markers_ready = False
            blockers.append(f"{_display_path(compose_file)} 缺少封版包标记：{', '.join(missing)}")

    local_maintenance_ready = False
    if local_maintenance_summary.exists():
        local_data = _read_json(local_maintenance_summary)
        local_maintenance_ready = (
            local_data.get("api_readiness", {}).get("maturity_status") == "ready_for_rehearsal"
            and local_data.get("boundaries", {}).get("real_platform_send_performed") is False
        )
    if not local_maintenance_ready:
        blockers.append("本地维护 UI/API rehearsal 证据未 ready")

    fe3_ready = False
    if fe3_summary.exists():
        fe3_ready = _read_json(fe3_summary).get("status") == "passed"
    if not fe3_ready:
        warnings.append("FE3 前端真实工作流 QA 尚未通过或尚未运行")

    pgvector_runtime_ready = False
    if h2w7d_runtime_summary.exists():
        pgvector_runtime_ready = _read_json(h2w7d_runtime_summary).get("status") == "ready_for_runtime_rehearsal"
    if not pgvector_runtime_ready:
        warnings.append("pgvector runtime rehearsal 尚未 ready；封版包只能作为候选，不能写生产级检索完成")

    ready_candidate = customer_env_template_ready and compose_ready and compose_markers_ready and local_maintenance_ready and fe3_ready
    if blockers:
        status = "blocked"
    elif ready_candidate and docker_ready and pgvector_runtime_ready:
        status = "passed_local_package_runtime_rehearsal_ready"
    elif ready_candidate:
        status = "passed_local_package_candidate_with_runtime_pending"
    else:
        status = "waiting_for_package_evidence"

    result = {
        "phase": PHASE,
        "status": status,
        "readiness": {
            "customer_env_template_ready": customer_env_template_ready,
            "compose_config_ready": compose_ready,
            "compose_markers_ready": compose_markers_ready,
            "local_maintenance_ui_ready": local_maintenance_ready,
            "fe3_ready": fe3_ready,
            "pgvector_runtime_ready": pgvector_runtime_ready,
            "docker_daemon_ready": docker_ready,
            "ready_for_local_pilot_package_candidate": ready_candidate and not blockers,
        },
        "blockers": blockers,
        "warnings": warnings,
        "command_observations": {
            "docker_info": docker_output,
            "compose_config": compose_output,
        },
        "evidence": {
            "summary_json": {"path": _display_path(summary_path)},
            "customer_env_template": {"path": _display_path(customer_env), "present": customer_env.exists()},
            "local_maintenance_summary": {"path": _display_path(local_maintenance_summary), "present": local_maintenance_summary.exists()},
            "fe3_summary": {"path": _display_path(fe3_summary), "present": fe3_summary.exists()},
            "h2w7d_runtime_summary": {"path": _display_path(h2w7d_runtime_summary), "present": h2w7d_runtime_summary.exists()},
        },
        "boundaries": {
            "customer_remote_control_added": False,
            "automatic_upload_enabled": False,
            "real_platform_send_performed": False,
            "formal_customer_signoff_performed": False,
            "development_bootstrap_allowed_in_customer_template": False,
        },
    }
    _write_json(summary_path, result)
    _write_markdown(DOC_PATH, result)
    return result


def main() -> int:
    result = run_h2w_pack1_local_delivery_rehearsal()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if result["status"] == "blocked" else 0


if __name__ == "__main__":
    raise SystemExit(main())
