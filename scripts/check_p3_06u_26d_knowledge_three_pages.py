#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


CHECKS = [
    (
        "frontend/src/components/knowledge/KnowledgeWorkspacePage.tsx",
        [
            "export function KnowledgeWorkspacePage",
            'data-knowledge-page-shell={mode}',
            'data-knowledge-primary={mode}',
            'data-knowledge-gap-cause-map="p3-06u-26d"',
            'data-knowledge-regression-compare="p3-06u-26d"',
            "无知识命中",
            "引用不足",
            "期望词缺失",
            "人工驳回",
            "当前知识评测是检索评测，不是完整客服准确率。",
            "不等同完整客服事实准确率",
        ],
    ),
    (
        "frontend/src/App.tsx",
        [
            'import { KnowledgeWorkspacePage } from "./components/knowledge/KnowledgeWorkspacePage";',
            '<KnowledgeWorkspacePage\n            mode="library"',
            '<KnowledgeWorkspacePage\n            mode="gaps"',
            '<KnowledgeWorkspacePage\n            mode="evals"',
            "<KnowledgeDocumentsPanel",
            "<KnowledgeGapPanel",
            "<KnowledgeEvaluationPanel",
        ],
    ),
    (
        "frontend/src/styles.css",
        [
            ".knowledge-page-command",
            ".knowledge-page-metric-strip",
            ".knowledge-page-cause-grid",
            ".knowledge-page-regression-compare",
            ".knowledge-page-empty",
            ".knowledge-page-gaps .knowledge-page-command",
            ".knowledge-page-evals .knowledge-page-command",
        ],
    ),
    (
        "docs/P3-06U-26D_KNOWLEDGE_THREE_PAGE_DEEPENING.md",
        [
            "# P3-06U-26D 知识三页分叉与服务端数据深化",
            "当前知识评测是检索评测，不是完整客服准确率",
            "真实外发继续关闭",
            "RPA 研究线不进入正式默认交付链",
            "P3-06U-26E",
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
    if app.count("<KnowledgeWorkspacePage") < 3:
        failures.append("App.tsx: KnowledgeWorkspacePage should wrap all three knowledge routes")

    component = (ROOT / "frontend/src/components/knowledge/KnowledgeWorkspacePage.tsx").read_text(encoding="utf-8")
    styles = (ROOT / "frontend/src/styles.css").read_text(encoding="utf-8")
    forbidden_needles = [
        "完整客服准确率。\",",
        "真实外发已开启",
        "RPA 已进入正式默认交付",
        "KnowledgeOperationsFlowPanel",
        'data-knowledge-ops-smoke="flow-panel"',
        'data-knowledge-ops-smoke="workflow-stages"',
        ".knowledge-ops-flow",
        ".knowledge-page-actions",
    ]
    for needle in forbidden_needles:
        if needle in component or needle in app or needle in styles:
            failures.append(f"knowledge workspace contains forbidden marker: {needle!r}")

    if failures:
        print("P3-06U-26D static check failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("P3-06U-26D static check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
