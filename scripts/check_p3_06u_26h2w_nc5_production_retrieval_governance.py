#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PHASE = "H2W-NC5"
OUTPUT_DIR = ROOT / "output/p3_06u_26h2w_nc5_production_retrieval_governance"
DOC_PATH = ROOT / "docs/P3-06U-26H2W_NC5_PRODUCTION_RETRIEVAL_GOVERNANCE.md"

FILES = {
    "schema": ROOT / "backend/app/schemas/rag_governance.py",
    "service": ROOT / "backend/app/services/rag_governance.py",
    "api": ROOT / "backend/app/api/knowledge.py",
    "backend_test": ROOT / "backend/tests/test_rag_cost_governance_api.py",
    "frontend_client": ROOT / "frontend/src/api/client.ts",
    "frontend_app": ROOT / "frontend/src/App.tsx",
    "h2w7_gate": ROOT / "scripts/check_p3_06u_26h2w7_rag_cost_governance.py",
    "vector_strategy_test": ROOT / "backend/tests/test_knowledge_vector_index_strategy_api.py",
    "vector_index_test": ROOT / "backend/tests/test_knowledge_vector_index_api.py",
}

SUMMARY_FILES = {
    "h2w7d_static": ROOT / "output/p3_06u_26h2w7d_production_retrieval_evidence/summary.json",
    "h2w7d_runtime": ROOT / "output/p3_06u_26h2w7d_runtime_pgvector_rehearsal/summary.json",
    "trial1": ROOT / "output/p3_06u_26h2w_trial1_internal_100q_rehearsal_report/summary.json",
    "model1": ROOT / "output/p3_06u_26h2w_model1_bailian_cost_sample/summary.json",
    "nc4": ROOT / "output/p3_06u_26h2w_nc4_knowledge_memory_mesh_overview/summary.json",
    "data2": ROOT / "output/p3_06u_26h2w_data2_real_customer_material_readiness/summary.json",
    "pack12": ROOT / "output/p3_06u_26h2w_pack12_customer_data_rerun_orchestrator/summary.json",
}


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_markdown(path: Path, result: dict[str, Any]) -> None:
    lines = [
        "# H2W-NC5 生产级检索与评测治理",
        "",
        "## 结论",
        "",
        f"- 阶段状态：`{result['status']}`",
        f"- 治理层 ready：`{str(result['readiness']['governance_layer_ready']).lower()}`",
        f"- 允许切生产检索：`{str(result['readiness']['production_retrieval_switch_allowed']).lower()}`",
        f"- pgvector runtime ready：`{str(result['readiness']['pgvector_runtime_ready']).lower()}`",
        f"- 题库与影子试跑 ready：`{str(result['readiness']['trial_evidence_ready']).lower()}`",
        f"- 真实客户资料 ready：`{str(result['readiness']['real_customer_data_ready']).lower()}`",
        f"- 真实资料链路重跑 ready：`{str(result['readiness']['customer_data_rerun_ready']).lower()}`",
        f"- 模型成本证据 ready：`{str(result['readiness']['model_cost_evidence_ready']).lower()}`",
        f"- NC4 知识证据链 ready：`{str(result['readiness']['knowledge_memory_mesh_overview_ready']).lower()}`",
        "",
        "## 当前阻断项",
        "",
    ]
    lines.extend([f"- {item}" for item in result["blockers"]] or ["- 无"])
    lines.extend(
        [
            "",
            "## 已纳入的证据",
            "",
        ]
    )
    for key, item in result["evidence"].items():
        lines.append(f"- {key}: `{item['path']}`，存在：`{str(item['present']).lower()}`")
    lines.extend(
        [
            "",
            "## 固定边界",
            "",
            "- 本阶段只是生产检索治理层 ready，不代表生产检索已切换。",
            "- SQLite/JSON 检索不能伪装成生产向量库。",
            "- 没有真实客户题库、pgvector runtime、最终答案质量和成本记录时，不允许写正式准确率或生产 SLA。",
            "- 真实外发、真实渠道、正式客户签收和签名安装包仍保持关闭或未完成。",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_nc5_gate(*, output_dir: Path = OUTPUT_DIR) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = output_dir / "summary.json"
    blockers: list[str] = []

    required_markers = {
        "schema": [
            "class RagProductionRetrievalReadiness",
            "production_switch_allowed",
            "retrieval_strategy_rules",
            "real_customer_material_ready",
        ],
        "service": [
            "_build_production_readiness",
            "CustomerMaterialBatch",
            "_real_customer_material_ready",
            "pgvector_runtime_ready",
            "real_customer_material_ready",
            "customer_question_bank_ready",
            "final_answer_quality_ready",
            "sqlite_json_disguised_as_production_vector_store",
        ],
        "api": ["rag-cost-governance-summary", "RagCostGovernanceSummary"],
        "backend_test": [
            "production_readiness",
            "production_switch_allowed",
            "pgvector_runtime_ready",
            "real_customer_material_ready",
            "model_cost_record_ready",
        ],
        "frontend_client": ["production_readiness", "RagCostGovernanceSummary"],
        "frontend_app": [
            "生产检索准备度",
            "真实资料",
            "答案质量与成本",
            "production_readiness",
        ],
        "h2w7_gate": ["class RagProductionRetrievalReadiness", "生产检索准备度"],
        "vector_strategy_test": [
            "test_pgvector_plan_blocks_non_postgresql_without_executing",
            "test_pgvector_ann_index_plan_uses_expression_partial_indexes_and_rollback",
        ],
        "vector_index_test": [
            "test_explicit_pgvector_store_requires_postgresql_without_silent_fallback",
            "test_pgvector_candidate_sql_filters_scope_before_similarity",
        ],
    }
    marker_ready: dict[str, bool] = {}
    for key, markers in required_markers.items():
        path = FILES[key]
        text = _read(path)
        ready = path.exists() and all(marker in text for marker in markers)
        marker_ready[key] = ready
        if not ready:
            blockers.append(f"{_display_path(path)} 缺少 NC5 必需标记")

    h2w7d_static = _read_json(SUMMARY_FILES["h2w7d_static"])
    h2w7d_runtime = _read_json(SUMMARY_FILES["h2w7d_runtime"])
    trial1 = _read_json(SUMMARY_FILES["trial1"])
    model1 = _read_json(SUMMARY_FILES["model1"])
    nc4 = _read_json(SUMMARY_FILES["nc4"])
    data2 = _read_json(SUMMARY_FILES["data2"])
    pack12 = _read_json(SUMMARY_FILES["pack12"])

    h2w7d_static_ready = bool(h2w7d_static.get("readiness", {}).get("pgvector_code_ready")) and bool(
        h2w7d_static.get("readiness", {}).get("ann_strategy_ready")
    )
    pgvector_runtime_ready = h2w7d_runtime.get("status") == "ready_for_runtime_rehearsal"
    trial_evidence_ready = str(trial1.get("status", "")).startswith("passed_internal_rehearsal_report")
    model_cost_evidence_ready = model1.get("status") == "passed_real_small_sample_cost_rehearsal"
    knowledge_memory_mesh_overview_ready = nc4.get("status") == "knowledge_memory_mesh_overview_ready"
    real_customer_data_ready = bool(
        data2.get("customer_data_used") is True
        and data2.get("internal_sample_used") is False
        and data2.get("readiness", {}).get("customer_real_materials_ready") is True
    )
    customer_data_rerun_ready = bool(
        pack12.get("customer_data_used") is True
        and pack12.get("internal_sample_used") is False
        and pack12.get("readiness", {}).get("customer_data_rerun_complete") is True
    )
    internal_sample_only = bool(
        data2.get("internal_sample_used") is True
        or pack12.get("internal_sample_used") is True
        or trial1.get("readiness", {}).get("internal_100q_bank_ready") is True
    )

    if not h2w7d_static_ready:
        blockers.append("H2W-7D 静态 pgvector/ANN 证据未 ready。")
    if not pgvector_runtime_ready:
        blockers.append("PostgreSQL + pgvector runtime rehearsal 未 ready，不能切生产检索。")
    if not trial_evidence_ready:
        blockers.append("内部 100 题/最终答案试跑证据未 ready，不能判断答案质量。")
    if not real_customer_data_ready:
        blockers.append("当前没有真实客户资料批次；内部样板不能解锁生产检索或客户资料版封包。")
    if not customer_data_rerun_ready:
        blockers.append("真实客户资料链路尚未完成 DATA -> KB -> TRIAL -> PACK 重跑。")
    if internal_sample_only:
        blockers.append("当前证据含内部样板/演练数据，不能写成正式客户签收或生产检索切换。")
    if not model_cost_evidence_ready:
        blockers.append("真实模型小样本成本证据未 ready；默认不调用付费模型是允许边界，但不能写成本治理封版。")
    if not knowledge_memory_mesh_overview_ready:
        blockers.append("NC4 知识证据链总览未 ready。")

    governance_layer_ready = all(marker_ready.values()) and h2w7d_static_ready and knowledge_memory_mesh_overview_ready
    production_switch_allowed = (
        governance_layer_ready
        and pgvector_runtime_ready
        and trial_evidence_ready
        and real_customer_data_ready
        and customer_data_rerun_ready
        and model_cost_evidence_ready
    )
    status = (
        "production_retrieval_governance_ready_for_switch"
        if production_switch_allowed
        else "production_retrieval_governance_ready_not_production_switch"
        if governance_layer_ready
        else "blocked"
    )

    result = {
        "phase": PHASE,
        "status": status,
        "readiness": {
            "governance_layer_ready": governance_layer_ready,
            "production_retrieval_switch_allowed": production_switch_allowed,
            "h2w7d_static_ready": h2w7d_static_ready,
            "pgvector_runtime_ready": pgvector_runtime_ready,
            "trial_evidence_ready": trial_evidence_ready,
            "real_customer_data_ready": real_customer_data_ready,
            "customer_data_rerun_ready": customer_data_rerun_ready,
            "internal_sample_only": internal_sample_only,
            "model_cost_evidence_ready": model_cost_evidence_ready,
            "knowledge_memory_mesh_overview_ready": knowledge_memory_mesh_overview_ready,
        },
        "marker_ready": marker_ready,
        "blockers": blockers,
        "not_ready_for": [
            "formal_accuracy_signoff",
            "real_platform_send",
            "real_channel_closure",
            "production_sla",
            "signed_installer",
        ]
        + ([] if production_switch_allowed else ["production_retrieval_switch"]),
        "evidence": {
            "summary_json": {"path": _display_path(summary_path), "present": True},
            **{
                key: {"path": _display_path(path), "present": path.exists()}
                for key, path in SUMMARY_FILES.items()
            },
        },
        "boundaries": {
            "production_retrieval_path_switched": False,
            "sqlite_json_disguised_as_production_vector_store": False,
            "paid_embedding_call_performed": False,
            "real_platform_send_performed": False,
            "formal_accuracy_signoff_performed": False,
        },
    }
    _write_json(summary_path, result)
    _write_markdown(DOC_PATH, result)
    return result


def main() -> int:
    result = run_nc5_gate()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if result["status"] == "blocked" else 0


if __name__ == "__main__":
    raise SystemExit(main())
