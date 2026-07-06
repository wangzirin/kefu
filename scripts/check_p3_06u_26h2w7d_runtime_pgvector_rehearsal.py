#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any, Callable

from smoke_pgvector_ann_indexes import SmokeConfig, run_smoke


ROOT = Path(__file__).resolve().parents[1]
PHASE = "H2W-7D-runtime"
DEFAULT_OUTPUT_DIR = ROOT / "output/p3_06u_26h2w7d_runtime_pgvector_rehearsal"
DOC_PATH = ROOT / "docs/P3-06U-26H2W7D_RUNTIME_PGVECTOR_REHEARSAL.md"
STATIC_7D_SUMMARY = ROOT / "output/p3_06u_26h2w7d_production_retrieval_evidence/summary.json"
H2W11O_SUMMARY = ROOT / "output/p3_06u_26h2w11o_real_customer_eval_bank_import/summary.json"
COMPOSE_FILES = [ROOT / "deploy/docker-compose.yml", ROOT / "deploy/docker-compose.pilot.yml"]
CUSTOMER_ENV = ROOT / "deploy/customer.env.example"
DEFAULT_DOCKER_DATABASE_URL = "postgresql+psycopg://wanfa_ops:change-me-before-pilot@127.0.0.1:5432/wanfa_ops"

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
    except Exception as exc:  # pragma: no cover - defensive for local CLI differences
        return False, str(exc)
    output = "\n".join(part for part in [result.stdout.strip(), result.stderr.strip()] if part)
    return result.returncode == 0, output[:1200]


def _database_url_is_postgresql() -> bool:
    value = os.environ.get("DATABASE_URL", "")
    return value.startswith("postgresql://") or value.startswith("postgresql+")


def _knowledge_store_is_pgvector() -> bool:
    return os.environ.get("KNOWLEDGE_VECTOR_STORE", "").strip() in {
        "pgvector",
        "postgres_pgvector",
        "postgres_pgvector_store_v1",
    }


def _customer_template_uses_pgvector() -> bool:
    if not CUSTOMER_ENV.exists():
        return False
    text = CUSTOMER_ENV.read_text(encoding="utf-8")
    return "KNOWLEDGE_VECTOR_STORE=postgres_pgvector_store_v1" in text


def _compose_declares_pgvector() -> bool:
    return any("pgvector/pgvector" in path.read_text(encoding="utf-8") for path in COMPOSE_FILES if path.exists())


def _write_markdown(path: Path, result: dict[str, Any]) -> None:
    readiness = result["readiness"]
    lines = [
        "# H2W-7D-runtime PostgreSQL + pgvector 运行环境 rehearsal",
        "",
        "## 结论",
        "",
        f"- 阶段状态：`{result['status']}`",
        f"- Docker daemon 可用：`{str(readiness['docker_daemon_ready']).lower()}`",
        f"- Compose 声明 pgvector：`{str(readiness['compose_pgvector_declared']).lower()}`",
        f"- DATABASE_URL 指向 PostgreSQL：`{str(readiness['database_url_postgresql']).lower()}`",
        f"- KNOWLEDGE_VECTOR_STORE 为 pgvector：`{str(readiness['knowledge_vector_store_pgvector']).lower()}`",
        f"- 客户模板使用 pgvector：`{str(readiness['customer_template_pgvector']).lower()}`",
        f"- pgvector ANN runtime smoke：`{str(readiness['runtime_ann_smoke_passed']).lower()}`",
        f"- 7D 静态证据 ready：`{str(readiness['static_7d_evidence_ready']).lower()}`",
        f"- 内部 100 题 ready：`{str(readiness['internal_100q_bank_ready']).lower()}`",
        f"- 可进入 pgvector runtime rehearsal：`{str(readiness['ready_for_runtime_rehearsal']).lower()}`",
        "",
        "## 停止门禁",
        "",
        "- 没有 Docker daemon 或外部 PostgreSQL + pgvector 运行环境时，不写生产级检索完成。",
        "- 非 PostgreSQL 环境必须 fail-closed，不能回退到 SQLite/JSON 还写成 pgvector。",
        "- 内部 100 题可用于工程 rehearsal，但不能写成真实客户题库。",
        "- 本阶段不调用付费 embedding，不切换真实生产查询路径。",
        "",
        "## 阻断项",
        "",
    ]
    lines.extend([f"- {item}" for item in result["blockers"]] or ["- 无"])
    lines.extend(
        [
            "",
            "## 输出",
            "",
            f"- `{result['evidence']['summary_json']['path']}`",
            f"- `{result['evidence']['runtime_ann_smoke_json']['path']}`",
            "",
            "## 边界",
            "",
            "- `production_retrieval_path_switched=false`",
            "- `paid_embedding_call_performed=false`",
            "- `external_platform_write_performed=false`",
            "- `formal_accuracy_signoff_performed=false`",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_h2w7d_runtime_pgvector_rehearsal(
    *,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    runner: CommandRunner = _run_command,
    run_ann_smoke: bool = True,
    database_url: str | None = None,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = output_dir / "summary.json"
    runtime_ann_smoke_path = output_dir / "pgvector_ann_smoke.json"
    blockers: list[str] = []
    warnings: list[str] = []

    docker_ready, docker_output = _command_ok(["docker", "info", "--format", "{{json .ServerVersion}}"], runner)
    compose_config_ready, compose_output = _command_ok(
        ["docker", "compose", "-f", "deploy/docker-compose.yml", "-f", "deploy/docker-compose.pilot.yml", "config", "--quiet"],
        runner,
    )
    compose_pgvector_declared = _compose_declares_pgvector()
    database_url_postgresql = _database_url_is_postgresql()
    knowledge_vector_store_pgvector = _knowledge_store_is_pgvector()
    customer_template_pgvector = _customer_template_uses_pgvector()

    runtime_ann_smoke: dict[str, Any] = {
        "status": "not_run",
        "reason": "run_ann_smoke=false or runtime prerequisites missing",
    }
    runtime_ann_smoke_passed = False
    smoke_database_url = (
        database_url
        or os.environ.get("ANN_SMOKE_DATABASE_URL")
        or os.environ.get("DATABASE_URL")
        or (DEFAULT_DOCKER_DATABASE_URL if docker_ready and compose_config_ready else "")
    )
    if run_ann_smoke and smoke_database_url.startswith("postgresql"):
        try:
            runtime_ann_smoke = run_smoke(
                SmokeConfig(
                    database_url=smoke_database_url,
                    rows=300,
                    dimensions=16,
                    top_k=5,
                    seed=20260704,
                    keep_tables=False,
                )
            )
            runtime_ann_smoke_passed = (
                runtime_ann_smoke.get("status") == "passed"
                and all(float(row.get("recall_at_k") or 0) >= 1.0 for row in runtime_ann_smoke.get("results", []))
                and all(bool(row.get("planner_mentions_index_method")) for row in runtime_ann_smoke.get("results", []))
            )
            _write_json(runtime_ann_smoke_path, runtime_ann_smoke)
        except Exception as exc:
            runtime_ann_smoke = {"status": "failed", "error": str(exc)}
            _write_json(runtime_ann_smoke_path, runtime_ann_smoke)

    static_7d_ready = False
    if STATIC_7D_SUMMARY.exists():
        static_7d = _read_json(STATIC_7D_SUMMARY)
        static_7d_ready = bool(static_7d.get("readiness", {}).get("pgvector_code_ready")) and bool(
            static_7d.get("readiness", {}).get("ann_strategy_ready")
        )
    else:
        blockers.append(f"缺少 7D 静态证据：{_display_path(STATIC_7D_SUMMARY)}")

    internal_100q_ready = False
    if H2W11O_SUMMARY.exists():
        h2w11o = _read_json(H2W11O_SUMMARY)
        internal_100q_ready = (
            h2w11o.get("status") == "passed_internal_rehearsal"
            and h2w11o.get("metrics", {}).get("row_count") == 100
            and h2w11o.get("metrics", {}).get("dataset_source_type") == "internal_synthetic_rehearsal"
        )
    else:
        blockers.append(f"缺少内部 100 题导入证据：{_display_path(H2W11O_SUMMARY)}")

    if not docker_ready and not database_url_postgresql:
        blockers.append("未检测到 Docker daemon，也未检测到外部 PostgreSQL DATABASE_URL")
    if not compose_config_ready:
        warnings.append("docker compose config 未通过或 Docker CLI 不可用；需本地修复后复跑")
    if not compose_pgvector_declared:
        blockers.append("deploy/docker-compose.yml 未声明 pgvector/pgvector")
    if not database_url_postgresql and not runtime_ann_smoke_passed:
        blockers.append("DATABASE_URL 未指向 PostgreSQL，且 pgvector runtime smoke 未通过")
    if not (knowledge_vector_store_pgvector or customer_template_pgvector):
        blockers.append("KNOWLEDGE_VECTOR_STORE 未设置为 pgvector，客户模板也未声明 pgvector")
    if not static_7d_ready:
        blockers.append("7D 静态 pgvector/ANN 证据未 ready")
    if not internal_100q_ready:
        blockers.append("内部 100 条题库未 ready，不能跑本轮检索评测")
    if not runtime_ann_smoke_passed:
        blockers.append("pgvector ANN runtime smoke 未通过，不能写 runtime rehearsal ready")

    ready = not blockers
    result = {
        "phase": PHASE,
        "status": "ready_for_runtime_rehearsal" if ready else "blocked_waiting_for_pgvector_runtime",
        "readiness": {
            "docker_daemon_ready": docker_ready,
            "compose_config_ready": compose_config_ready,
            "compose_pgvector_declared": compose_pgvector_declared,
            "database_url_postgresql": database_url_postgresql,
            "knowledge_vector_store_pgvector": knowledge_vector_store_pgvector,
            "customer_template_pgvector": customer_template_pgvector,
            "runtime_ann_smoke_passed": runtime_ann_smoke_passed,
            "static_7d_evidence_ready": static_7d_ready,
            "internal_100q_bank_ready": internal_100q_ready,
            "ready_for_runtime_rehearsal": ready,
        },
        "blockers": blockers,
        "warnings": warnings,
        "command_observations": {
            "docker_info": docker_output,
            "compose_config": compose_output,
        },
        "evidence": {
            "summary_json": {"path": _display_path(summary_path)},
            "runtime_ann_smoke_json": {"path": _display_path(runtime_ann_smoke_path), "present": runtime_ann_smoke_path.exists()},
            "static_7d_summary": {"path": _display_path(STATIC_7D_SUMMARY), "present": STATIC_7D_SUMMARY.exists()},
            "h2w11o_summary": {"path": _display_path(H2W11O_SUMMARY), "present": H2W11O_SUMMARY.exists()},
        },
        "runtime_ann_smoke": {
            "status": runtime_ann_smoke.get("status"),
            "database": runtime_ann_smoke.get("database"),
            "pgvector_version_before_smoke": runtime_ann_smoke.get("pgvector_version_before_smoke"),
            "results": runtime_ann_smoke.get("results", []),
        },
        "boundaries": {
            "sqlite_json_disguised_as_production_vector_store": False,
            "production_retrieval_path_switched": False,
            "paid_embedding_call_performed": False,
            "external_platform_write_performed": False,
            "formal_accuracy_signoff_performed": False,
            "internal_100q_is_customer_bank": False,
        },
    }
    _write_json(summary_path, result)
    _write_markdown(DOC_PATH, result)
    return result


def main() -> int:
    result = run_h2w7d_runtime_pgvector_rehearsal()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
