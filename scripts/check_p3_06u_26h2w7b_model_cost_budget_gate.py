from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


REQUIRED_MARKERS = {
    "backend/app/core/config.py": [
        "MODEL_BUDGET_GUARD_ENABLED",
        "MODEL_BUDGET_SINGLE_CALL_LIMIT_CNY",
        "MODEL_PRICE_BAILIAN_STANDARD_PER_1K_UNITS",
        "MODEL_BUDGET_PRICING_SOURCE",
    ],
    ".env.example": [
        "MODEL_BUDGET_GUARD_ENABLED",
        "MODEL_BUDGET_SINGLE_CALL_LIMIT_CNY",
        "MODEL_PRICE_BAILIAN_STANDARD_PER_1K_UNITS",
        "Prices are local operator estimates",
    ],
    "backend/app/services/model_budget.py": [
        "class ModelCostEstimate",
        "class ModelBudgetDecision",
        "evaluate_budget",
        "single_call_budget_exceeded",
        "daily_budget_exceeded",
        "monthly_budget_exceeded",
        "price_estimate_not_provider_bill",
    ],
    "backend/app/services/reply_orchestrator.py": [
        "estimate_route_cost",
        "evaluate_budget",
        "budget_blocked",
        "budget_degraded_to_deterministic",
        "model_budget_limited",
    ],
    "backend/app/services/reply_provenance.py": [
        "estimated_cost",
        "pricing_source",
        "budget_policy_snapshot",
        "degrade_action",
        "budget_reason",
    ],
    "backend/app/services/rag_governance.py": [
        "model_budget_policy",
        "budget_guard_enabled",
        "pricing_version",
    ],
    "backend/app/schemas/reply_orchestrator.py": [
        "budget_blocked",
        "degraded",
        "estimated_cost",
        "budget_reason",
    ],
    "backend/app/schemas/rag_governance.py": [
        "budget_guard_enabled",
        "single_call_budget_limit",
        "pricing_source",
    ],
    "backend/tests/test_reply_orchestrator_api.py": [
        "test_reply_orchestration_blocks_explicit_provider_when_single_call_budget_is_exceeded",
        "test_reply_orchestration_auto_route_degrades_to_deterministic_when_budget_is_exceeded",
        "budget_blocked",
        "budget_degraded_to_deterministic",
    ],
    "backend/tests/test_rag_cost_governance_api.py": [
        "model_budget_policy",
        "budget_guard_enabled",
        "pricing_version",
    ],
    "docs/P3-06U-26H2W7B_MODEL_COST_BUDGET_GATE_FIRST_SLICE.md": [
        "H2W-7B",
        "模型调用成本台账",
        "预算门禁",
        "显式 provider 不静默 fallback",
        "真实外发继续关闭",
        "停止门禁",
    ],
    "README.md": [
        "H2W-7B",
        "预算门禁",
        "budget_blocked",
        "degraded",
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
    print("P3-06U-26H2W7B model cost budget gate static check passed.")


if __name__ == "__main__":
    main()
