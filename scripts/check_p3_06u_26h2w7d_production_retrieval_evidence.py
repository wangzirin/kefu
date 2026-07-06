#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PHASE = "H2W-7D"
DEFAULT_OUTPUT_DIR = ROOT / "output/p3_06u_26h2w7d_production_retrieval_evidence"
DOC_PATH = ROOT / "docs/P3-06U-26H2W7D_PRODUCTION_RETRIEVAL_EVIDENCE.md"
H2W11O_SUMMARY = ROOT / "output/p3_06u_26h2w11o_real_customer_eval_bank_import/summary.json"
KNOWLEDGE_SERVICE = ROOT / "backend/app/services/knowledge.py"
PGVECTOR_GATE = ROOT / "scripts/check_stage2_knowledge_pgvector.py"
INDEX_STRATEGY_GATE = ROOT / "scripts/check_stage2_knowledge_vector_index_strategy.py"
PGVECTOR_TESTS = ROOT / "backend/tests/test_knowledge_vector_index_api.py"
STRATEGY_TESTS = ROOT / "backend/tests/test_knowledge_vector_index_strategy_api.py"


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _database_url_is_postgresql() -> bool:
    value = os.environ.get("DATABASE_URL", "")
    return value.startswith("postgresql://") or value.startswith("postgresql+")


def _knowledge_vector_store_is_pgvector() -> bool:
    return os.environ.get("KNOWLEDGE_VECTOR_STORE", "").strip() in {
        "pgvector",
        "postgres_pgvector",
        "postgres_pgvector_store_v1",
    }


def _write_markdown(path: Path, result: dict[str, Any]) -> None:
    r = result["readiness"]
    lines = [
        "# H2W-7D 生产级检索与引用证据",
        "",
        "## 结论",
        "",
        f"- 阶段状态：`{result['status']}`",
        f"- pgvector 代码路径：`{str(r['pgvector_code_ready']).lower()}`",
        f"- ANN 索引策略：`{str(r['ann_strategy_ready']).lower()}`",
        f"- 非 PostgreSQL fail-closed：`{str(r['non_postgres_fail_closed_ready']).lower()}`",
        f"- 真实题库可用于评测：`{str(r['real_bank_ready_for_eval']).lower()}`",
        f"- PostgreSQL 运行环境：`{str(r['postgres_runtime_ready']).lower()}`",
        f"- 可切生产检索路径：`{str(r['ready_for_production_retrieval_switch']).lower()}`",
        "",
        "## 策略规则",
        "",
        "- 小于 10,000 chunks：优先 exact scan，保证召回可解释。",
        "- 10,000 到 500,000 chunks：优先 HNSW，召回/延迟折中较稳。",
        "- 大于 500,000 chunks 或内存敏感：可选 IVFFlat，但必须与 exact scan 做召回对照。",
        "- 所有 ANN 索引必须有构建窗口、回滚 SQL 和失败降级。",
        "- 引用必须保留 chunk、version/hash/source_uri，不能只有文档名。",
        "",
        "## 阻断项",
        "",
    ]
    if result["blockers"]:
        lines.extend(f"- {item}" for item in result["blockers"])
    else:
        lines.append("- 无")
    lines.extend(
        [
            "",
            "## 输出",
            "",
            f"- `{result['evidence']['summary_json']['path']}`",
            "",
            "## 边界",
            "",
            "- 本阶段不把 SQLite/JSON 检索包装成生产向量库。",
            "- 没有真实题库评测，不切换生产检索路径。",
            "- 外部 embedding 或 reranker 未记录价格、版本和降级时，不进入生产候选。",
            "- 本阶段不调用付费模型，除非后续单独授权。",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_h2w7d_production_retrieval_evidence(
    *,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    h2w11o_summary: Path = H2W11O_SUMMARY,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = output_dir / "summary.json"
    knowledge = _read(KNOWLEDGE_SERVICE)
    pgvector_gate = _read(PGVECTOR_GATE)
    strategy_gate = _read(INDEX_STRATEGY_GATE)
    pgvector_tests = _read(PGVECTOR_TESTS)
    strategy_tests = _read(STRATEGY_TESTS)

    blockers: list[str] = []
    warnings: list[str] = []
    pgvector_code_ready = all(
        fragment in knowledge
        for fragment in [
            "PGVECTOR_VECTOR_STORE",
            "postgres_pgvector_store_v1",
            "postgres_pgvector_exact_cosine_v1",
            "_build_pgvector_candidate_sql",
            "_require_vector_store_available",
            "embedding_pgvector",
            "source_uri",
            "content_hash",
        ]
    )
    ann_strategy_ready = all(
        fragment in knowledge
        for fragment in [
            "_build_pgvector_ann_index_plan",
            "postgres_pgvector_hnsw_cosine_v1",
            "postgres_pgvector_ivfflat_cosine_v1",
            "DROP INDEX",
            "estimated_build_seconds",
            "estimated_memory_mb",
        ]
    )
    non_postgres_fail_closed_ready = (
        "knowledge vector store pgvector requires PostgreSQL; refusing silent JSON fallback" in knowledge
        and "test_explicit_pgvector_store_requires_postgresql_without_silent_fallback" in pgvector_tests
        and "test_pgvector_plan_blocks_non_postgresql_without_executing" in strategy_tests
    )
    citation_evidence_ready = all(
        fragment in knowledge
        for fragment in ["chunk_id", "source_uri", "content_hash", "embedding_provider", "embedding_model", "vector_store"]
    )
    static_gates_ready = (
        "PASS stage2 knowledge pgvector" in pgvector_gate
        and "PASS stage2 knowledge vector index strategy" in strategy_gate
    )

    for name, ready in {
        "pgvector_code_ready": pgvector_code_ready,
        "ann_strategy_ready": ann_strategy_ready,
        "non_postgres_fail_closed_ready": non_postgres_fail_closed_ready,
        "citation_evidence_ready": citation_evidence_ready,
        "static_gates_ready": static_gates_ready,
    }.items():
        if not ready:
            blockers.append(f"生产检索静态前置条件未满足：{name}")

    real_bank_ready = False
    real_bank_case_count = 0
    if h2w11o_summary.exists():
        h2w11o = _read_json(h2w11o_summary)
        real_bank_ready = bool(h2w11o.get("readiness", {}).get("ready_for_final_answer_sampling"))
        real_bank_case_count = int(h2w11o.get("metrics", {}).get("row_count") or 0)
    if not real_bank_ready:
        blockers.append("H2W-11O 真实 50-100 条脱敏题库尚未 ready，不能做生产检索评测")

    postgres_runtime_ready = _database_url_is_postgresql() and _knowledge_vector_store_is_pgvector()
    if not postgres_runtime_ready:
        blockers.append("当前未检测到 PostgreSQL + pgvector 生产候选运行环境")

    external_embedding_configured = bool(os.environ.get("KNOWLEDGE_EMBEDDING_PROVIDER")) and os.environ.get(
        "KNOWLEDGE_EMBEDDING_PROVIDER"
    ) not in {"deterministic_local", "deterministic"}
    external_embedding_cost_record_ready = all(
        bool(os.environ.get(name))
        for name in [
            "KNOWLEDGE_EMBEDDING_MODEL",
            "KNOWLEDGE_EMBEDDING_PRICE_PER_1K_TOKENS",
            "KNOWLEDGE_EMBEDDING_COST_CURRENCY",
        ]
    )
    if external_embedding_configured and not external_embedding_cost_record_ready:
        blockers.append("外部 embedding 已配置但缺少 model/price/currency 成本记录")

    readiness = {
        "pgvector_code_ready": pgvector_code_ready,
        "ann_strategy_ready": ann_strategy_ready,
        "non_postgres_fail_closed_ready": non_postgres_fail_closed_ready,
        "citation_evidence_ready": citation_evidence_ready,
        "real_bank_ready_for_eval": real_bank_ready,
        "real_bank_case_count": real_bank_case_count,
        "postgres_runtime_ready": postgres_runtime_ready,
        "external_embedding_cost_record_ready": (not external_embedding_configured) or external_embedding_cost_record_ready,
        "ready_for_production_retrieval_switch": not blockers,
    }
    result = {
        "phase": PHASE,
        "status": "passed" if readiness["ready_for_production_retrieval_switch"] else "blocked_waiting_for_real_bank_or_postgres",
        "readiness": readiness,
        "blockers": blockers,
        "warnings": warnings,
        "strategy_rules": {
            "exact_scan": "under_10000_chunks_or_regression_baseline",
            "hnsw": "10000_to_500000_chunks_default_production_candidate",
            "ivfflat": "over_500000_chunks_or_memory_sensitive_requires_exact_recall_comparison",
            "rollback": "DROP INDEX statements must be retained with every index plan",
        },
        "evidence": {
            "summary_json": {"path": _display_path(summary_path)},
            "h2w11o_summary": {"path": _display_path(h2w11o_summary), "present": h2w11o_summary.exists()},
            "knowledge_service": {"path": _display_path(KNOWLEDGE_SERVICE)},
            "pgvector_gate": {"path": _display_path(PGVECTOR_GATE)},
            "index_strategy_gate": {"path": _display_path(INDEX_STRATEGY_GATE)},
            "pgvector_tests": {"path": _display_path(PGVECTOR_TESTS)},
            "strategy_tests": {"path": _display_path(STRATEGY_TESTS)},
        },
        "boundaries": {
            "sqlite_json_disguised_as_production_vector_store": False,
            "production_retrieval_path_switched": False,
            "paid_embedding_call_performed": False,
            "formal_accuracy_signoff_performed": False,
        },
    }
    _write_json(summary_path, result)
    _write_markdown(DOC_PATH, result)
    return result


def main() -> int:
    result = run_h2w7d_production_retrieval_evidence()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if result["status"] == "blocked" else 0


if __name__ == "__main__":
    raise SystemExit(main())
