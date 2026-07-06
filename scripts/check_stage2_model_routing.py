#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


REQUIRED = {
    "backend/app/core/config.py": [
        "bailian_fast_model",
        "bailian_standard_model",
        "bailian_premium_model",
        "deepseek_fallback_model",
    ],
    "backend/app/services/model_gateway.py": [
        "ModelRouteDecision",
        "select_model_route",
        "simple_fast",
        "standard_support",
        "premium_guarded",
        "deterministic_safe_fallback",
        "human_review_required",
        "fallback_chain",
    ],
    "backend/app/services/reply_orchestrator.py": [
        "route_name=result.route_name",
        "target_model_tier=result.target_model_tier",
        "route_reasons=result.route_reasons",
        "confidence=routed_confidence",
    ],
    "backend/app/schemas/reply_orchestrator.py": [
        "route_name",
        "complexity",
        "target_model_tier",
        "fallback_chain",
        "human_review_required",
        "route_reasons",
    ],
    "backend/tests/test_model_routing_policy.py": [
        "test_auto_route_selects_fast_bailian_model_for_simple_low_risk",
        "test_auto_route_selects_standard_bailian_model_for_normal_customer_question",
        "test_auto_route_selects_premium_guarded_model_for_high_risk_or_complex_question",
        "test_auto_route_falls_back_to_deterministic_without_external_keys",
    ],
    "backend/tests/test_reply_orchestrator_api.py": [
        "test_reply_orchestration_auto_route_records_model_tier_and_human_review_guard",
        "route_name",
        "target_model_tier",
        "fallback_chain",
    ],
    ".env.example": [
        "BAILIAN_FAST_MODEL=qwen3.6-flash",
        "BAILIAN_STANDARD_MODEL=qwen3.7-plus",
        "BAILIAN_PREMIUM_MODEL=qwen3.7-max",
        "DEEPSEEK_FALLBACK_MODEL=deepseek-v4-flash",
    ],
    "README.md": [
        "P2-19",
        "模型路由",
        "simple_fast",
        "standard_support",
        "premium_guarded",
    ],
    "docs/STAGE2_WORKFLOW_FOUNDATION.md": [
        "P2-19",
        "模型路由",
        "qwen3.7-plus",
        "真实模型质量验收",
    ],
}


def main() -> None:
    missing: list[str] = []
    for relative_path, fragments in REQUIRED.items():
        path = ROOT / relative_path
        if not path.exists():
            missing.append(f"{relative_path}: file missing")
            continue
        content = path.read_text(encoding="utf-8")
        for fragment in fragments:
            if fragment not in content:
                missing.append(f"{relative_path}: missing {fragment!r}")
    if missing:
        raise SystemExit("FAIL stage2 model routing:\n" + "\n".join(missing))
    print("PASS stage2 model routing")


if __name__ == "__main__":
    main()
