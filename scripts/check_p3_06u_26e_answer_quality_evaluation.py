#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


CHECKS = [
    (
        "backend/app/services/knowledge.py",
        [
            "answer_quality_metrics_version",
            "p3_06u_26e_customer_service_answer_quality_v1",
            "final_answer_factuality_measured",
            "citation_sufficiency_rate",
            "forbidden_commitment_violation_rate",
            "handoff_correctness",
            '"answer_quality"',
            "not_measured_final_answer_not_generated",
        ],
    ),
    (
        "backend/tests/test_knowledge_evaluations_api.py",
        [
            "p3_06u_26e_customer_service_answer_quality_v1",
            "final_answer_factuality_measured",
            "citation_sufficiency_rate",
            "forbidden_commitment_violation_rate",
            "handoff_correctness",
        ],
    ),
    (
        "frontend/src/App.tsx",
        [
            "evaluationMode",
            "customer_service_retrieval",
            'data-answer-quality-gate="p3-06u-26e"',
            'data-answer-quality-case="p3-06u-26e"',
            "客服答案质量门禁",
            "最终答案事实性",
            "引用充分",
            "禁用承诺",
            "转人工正确性",
            "不调用模型、不外发、不把检索命中率包装成完整准确率",
        ],
    ),
    (
        "frontend/src/components/knowledge/KnowledgeWorkspacePage.tsx",
        [
            "答案事实性",
            "引用充分",
            "禁用承诺",
            "转人工正确",
            "检索命中，不是完整准确率",
        ],
    ),
    (
        "frontend/src/styles.css",
        [
            ".answer-quality-gate",
            ".answer-quality-grid",
            ".answer-quality-card",
            ".answer-quality-badges",
        ],
    ),
    (
        "docs/P3-06U-26E_CUSTOMER_SERVICE_ANSWER_QUALITY_EVALUATION.md",
        [
            "# P3-06U-26E 客服答案质量评测第一片",
            "最终答案事实性",
            "引用充分",
            "禁用承诺",
            "转人工正确性",
            "不生成最终客服答案",
            "不调用真实模型",
            "不打开真实外发",
            "P3-06U-26F",
        ],
    ),
]


def main() -> int:
    failures: list[str] = []
    for relative_path, needles in CHECKS:
        path = ROOT / relative_path
        if not path.exists():
            failures.append(f"missing file: {relative_path}")
            continue
        content = path.read_text(encoding="utf-8")
        for needle in needles:
            if needle not in content:
                failures.append(f"{relative_path}: missing {needle!r}")

    app = (ROOT / "frontend/src/App.tsx").read_text(encoding="utf-8")
    forbidden_needles = [
        "最终答案事实性已完成",
        "完整客服准确率已完成",
        "真实外发已开启",
    ]
    for needle in forbidden_needles:
        if needle in app:
            failures.append(f"frontend contains forbidden completion claim: {needle!r}")

    if failures:
        print("P3-06U-26E static check failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("P3-06U-26E static check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
