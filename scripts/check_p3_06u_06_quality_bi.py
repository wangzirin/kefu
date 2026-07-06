#!/usr/bin/env python3
"""Static checks for P3-06U-06 quality BI repair loop."""

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
    quality_source = f"{app}\n{quality_panel}"
    styles = read_text("frontend/src/styles.css")
    doc = read_text("docs/P3-06U-06_QUALITY_BI_REPAIR_LOOP.md")
    browser_script = read_text("scripts/check_p3_06u_06_quality_bi.mjs")

    for snippet in [
        'type WorkspaceTaskSource = "overview" | "quality"',
        'source: "quality"',
        "qualityTaskHref",
        "quality-knowledge-gap",
        "quality-low-confidence",
        "quality-channel-failure",
        "quality-regression",
        'data-quality-smoke="repair-map"',
        'data-quality-context-link="true"',
        "repairPaths",
        "修复闭环",
        "不把检索命中当作完整准确率",
        "来自质量复盘",
    ]:
        require(snippet in quality_source, f"Quality BI source missing repair loop snippet: {snippet}")

    for snippet in [
        ".quality-repair-map",
        ".quality-repair-score",
        ".quality-repair-path-list",
        ".quality-repair-path-progress",
        ".quality-repair-next",
        "@media (max-width: 1180px)",
        "@media (max-width: 960px)",
    ]:
        require(snippet in styles, f"styles missing quality repair class or breakpoint: {snippet}")

    for phrase in [
        "# P3-06U-06 质量复盘 BI 与知识修复闭环",
        "错因定位 -> 进入修复 -> 回归验证",
        "补齐知识覆盖",
        "复核低置信证据",
        "处理渠道异常",
        "补充回归验证",
        "from=quality",
        "真实外发仍保持关闭",
        "P3-06U-07",
    ]:
        require(phrase in doc, f"documentation missing phrase: {phrase}")

    for snippet in [
        "data-quality-smoke",
        "from=quality",
        "来自质量复盘",
        "desktop-1440",
        "desktop-900",
        "mobile-390",
        "output/p3_06u_06_quality_bi",
        "summary.json",
    ]:
        require(snippet in browser_script, f"browser smoke missing snippet: {snippet}")

    print("P3-06U-06 quality BI repair loop static checks passed.")


if __name__ == "__main__":
    main()
