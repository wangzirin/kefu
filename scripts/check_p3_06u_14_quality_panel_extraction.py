#!/usr/bin/env python3
"""Static checks for P3-06U-14 quality review panel extraction."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_text(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    app = read_text("frontend/src/App.tsx")
    quality_panel = read_text("frontend/src/components/quality/QualityReviewPanel.tsx")
    doc = read_text("docs/P3-06U-14_QUALITY_REVIEW_PANEL_EXTRACTION.md")

    require(
        'from "./components/quality/QualityReviewPanel"' in app,
        "App should import quality panel from components/quality",
    )
    require("function QualityReviewPanel(" not in app, "App should not define QualityReviewPanel after extraction")
    require("interface QualityIssueBreakdown" not in app, "App should not keep quality-only issue types")
    require("interface QualityRepairPath" not in app, "App should not keep quality-only repair path types")
    require(
        "export function QualityReviewPanel" in quality_panel,
        "QualityReviewPanel component should be exported from its own file",
    )
    require(
        "export function QualityMetric" in quality_panel,
        "QualityMetric should be exported for the knowledge evaluation report reuse",
    )

    for snippet in [
        'data-quality-smoke="quality-panel"',
        'data-quality-smoke="repair-map"',
        "quality-repair-map",
        "quality-bi-grid",
        "quality-drilldown-panel",
        "准确率必须结合人工标签",
        "buildWorkspaceTaskHref",
    ]:
        require(snippet in quality_panel, f"Quality panel missing expected snippet: {snippet}")

    for phrase in [
        "# P3-06U-14 质量复盘页组件拆分",
        "行为不变，结构变清楚",
        "没有新增真实外发",
        "frontend/src/components/quality/QualityReviewPanel.tsx",
        "npm run typecheck",
    ]:
        require(phrase in doc, f"U14 documentation missing phrase: {phrase}")

    require(len(app.splitlines()) < 11300, "App.tsx should shrink after quality panel extraction")

    print("P3-06U-14 quality panel extraction static checks passed.")


if __name__ == "__main__":
    main()
