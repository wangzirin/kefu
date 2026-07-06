#!/usr/bin/env python3
"""Static checks for the knowledge operations baseline after P3-06U-26G4 dedupe."""

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
    styles = read_text("frontend/src/styles.css")
    doc = read_text("docs/P3-06U-07_KNOWLEDGE_OPS_PRODUCTIZATION.md")
    browser_script = read_text("scripts/check_p3_06u_07_knowledge_ops.mjs")

    for snippet in [
        'type WorkspaceTaskSource = "overview" | "quality" | "knowledge"',
        'context.source === "knowledge"',
        'data-knowledge-ops-smoke="edit-checklist"',
        "适用问题",
        "禁止承诺",
        "版本和审核状态",
        "<KnowledgeDocumentsPanel",
        "<KnowledgeGapPanel",
        "<KnowledgeEvaluationPanel",
    ]:
        require(snippet in app, f"App missing retained knowledge ops snippet: {snippet}")

    for snippet in [
        "KnowledgeOperationsFlowPanel",
        'data-knowledge-ops-smoke="flow-panel"',
        'data-knowledge-ops-smoke="workflow-stages"',
        'data-knowledge-ops-smoke="publish-gate"',
        'data-knowledge-ops-smoke="regression-impact"',
        ".knowledge-ops-flow",
        ".knowledge-ops-stage-grid",
        ".knowledge-ops-stage",
        ".knowledge-ops-detail-grid",
        ".knowledge-page-actions",
    ]:
        require(snippet not in app and snippet not in styles, f"retired duplicate knowledge ops artifact still present: {snippet}")

    for snippet in [
        ".knowledge-page-command",
        ".knowledge-page-metric-strip",
        ".knowledge-page-cause-grid",
        ".knowledge-page-regression-compare",
        ".knowledge-edit-checklist",
        "@media (max-width: 1180px)",
    ]:
        require(snippet in styles, f"styles missing retained knowledge workspace class: {snippet}")

    for phrase in [
        "# P3-06U-07 知识运营台产品化",
        "P3-06U-26G4",
        "三页独立工作区",
        "不打开真实外发",
    ]:
        require(phrase in doc, f"documentation missing retained/update phrase: {phrase}")

    for snippet in [
        "hasNoSharedFlowPanel",
        "data-knowledge-page-shell",
        "data-knowledge-ops-smoke",
        "output/p3_06u_07_knowledge_ops",
        "summary.json",
    ]:
        require(snippet in browser_script, f"browser smoke missing updated snippet: {snippet}")

    print("P3-06U-07 knowledge ops static checks passed.")


if __name__ == "__main__":
    main()
