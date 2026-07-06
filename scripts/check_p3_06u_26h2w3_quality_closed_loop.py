#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def require(text: str, needle: str, label: str) -> None:
    if needle not in text:
        raise AssertionError(f"missing {label}: {needle}")


def main() -> None:
    panel = read("frontend/src/components/quality/QualityReviewPanel.tsx")
    styles = read("frontend/src/styles.css")
    api_client = read("frontend/src/api/client.ts")
    backend_tests = read("backend/tests/test_knowledge_evaluations_api.py")
    doc = read("docs/P3-06U-26H2W3_QUALITY_CLOSED_LOOP_FIRST_SLICE.md")

    required_panel_markers = [
        'data-h2w3-quality-loop="true"',
        'data-h2w3-boundary="no-full-online-accuracy"',
        'data-h2w3-loop-step={card.key}',
        'data-h2w3-loop-step="sample-to-label"',
        'data-h2w3-loop-step="cause-to-repair"',
        'data-h2w3-loop-step="post-publish-regression"',
        "真实外发继续关闭",
        "不展示完整线上准确率",
        "检索命中率不能替代最终客服答案正确率",
        "样本质量、人工标签质量、真实线上回执分开展示",
        "质量-final-answer-labels".replace("质量-", "quality-"),
        "quality-knowledge-repair",
        "quality-reply-strategy",
    ]
    for needle in required_panel_markers:
        require(panel, needle, "H2W-3 panel marker")

    for needle in [
        ".h2w3-quality-loop",
        ".h2w3-loop-grid",
        ".h2w3-quality-closure",
        ".h2w3-label-breakdown",
        ".h2w3-repair-actions",
        ".h2w3-regression-note",
    ]:
        require(styles, needle, "H2W-3 styles")

    for needle in [
        "captureKnowledgeEvaluationRunCaseFinalAnswerSample",
        "labelKnowledgeEvaluationRunCaseFactuality",
        "batchLabelKnowledgeEvaluationRunCaseFactuality",
        "getMonthlyQualityReview",
        "getCustomerQualityReport",
        "recordCustomerQualityReportSignoff",
    ]:
        require(api_client, needle, "frontend API client")

    for needle in [
        "/final-answer-sample",
        "/factuality-labels/batch",
        "/monthly-quality-review",
        "/customer-quality-report",
        "final_answer_factuality_rate",
        "external_platform_write_performed",
    ]:
        require(backend_tests, needle, "backend quality test")

    for needle in [
        "P3-06U-26H2W3 线上回执与准确率闭环第一片",
        "本地样本质量",
        "人工标签质量",
        "停止门禁",
        "没有真实平台回执却写成线上全量准确率，立即停止",
    ]:
        require(doc, needle, "H2W-3 doc")

    print("P3-06U-26H2W3 quality closed-loop static gate passed.")


if __name__ == "__main__":
    main()
