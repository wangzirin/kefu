from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


REQUIRED_MARKERS = {
    "backend/app/api/knowledge.py": [
        "rag-cost-governance-summary",
        "RagCostGovernanceSummary",
        "OPS_METRICS_READ_PERMISSION",
    ],
    "backend/app/services/rag_governance.py": [
        "p3-06u-26h2w7.rag_cost_governance_summary.v1",
        "model_call_performed",
        "external_write_performed",
        "model_call_cost_governance",
        "production_vector_store",
        "customer_question_bank",
    ],
    "backend/app/schemas/rag_governance.py": [
        "class RagCostGovernanceSummary",
        "class RagGovernanceGate",
        "class RagProductionRetrievalReadiness",
        "ready_for_controlled_pilot",
    ],
    "backend/tests/test_rag_cost_governance_api.py": [
        "test_owner_can_read_rag_cost_governance_summary_without_external_calls",
        "production_readiness",
        "model_call_performed",
        "external_write_performed",
        "model_call_cost_governance",
        "test_agent_cannot_read_rag_cost_governance_summary",
    ],
    "frontend/src/api/client.ts": [
        "RagCostGovernanceSummary",
        "getRagCostGovernanceSummary",
        "/rag-cost-governance-summary",
    ],
    "frontend/src/App.tsx": [
        "RagCostGovernanceState",
        "refreshRagCostGovernance",
        "data-rag-cost-governance",
        "生产检索准备度",
    ],
    "docs/P3-06U-26H2W7_RAG_COST_GOVERNANCE_FIRST_SLICE.md": [
        "不是完整生产级 RAG 完成态",
        "没有调用真实大模型",
        "没有真实平台外发",
        "客服模型调用成本",
        "停止门禁",
    ],
    "docs/FRONTEND_FUNCTION_REALITY_MATRIX.md": [
        "检索与成本治理",
        "生产检索准备度",
        "不是完整模型成本报表",
    ],
    "docs/PRODUCTIZATION_MASTER_PLAN_LITE_AND_STANDARD.md": [
        "H2W-7A 生产级 RAG 与模型成本治理第一片",
        "当前模型调用成本记录仍是阻断项",
    ],
}


def main() -> None:
    failures: list[str] = []
    for relative_path, markers in REQUIRED_MARKERS.items():
        path = ROOT / relative_path
        if not path.exists():
            failures.append(f"missing file: {relative_path}")
            continue
        text = path.read_text(encoding="utf-8")
        for marker in markers:
            if marker not in text:
                failures.append(f"{relative_path}: missing marker {marker!r}")

    if failures:
        raise SystemExit("\n".join(failures))
    print("P3-06U-26H2W7 rag cost governance static gate passed.")


if __name__ == "__main__":
    main()
