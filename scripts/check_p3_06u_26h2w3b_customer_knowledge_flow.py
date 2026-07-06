#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def require_contains(path: str, needles: list[str]) -> None:
    content = read(path)
    missing = [needle for needle in needles if needle not in content]
    if missing:
        raise AssertionError(f"{path} missing required markers: {missing}")


def require_absent(path: str, needles: list[str]) -> None:
    content = read(path)
    found = [needle for needle in needles if needle in content]
    if found:
        raise AssertionError(f"{path} contains retired or overclaiming markers: {found}")


def main() -> None:
    require_contains(
        "frontend/src/App.tsx",
        [
            'data-h2w3b-customer-knowledge-flow="true"',
            'data-h2w3b-step="business-object"',
            'data-h2w3b-step="standard-qa"',
            'data-h2w3b-step="process-policy"',
            'data-h2w3b-step="risk-rules"',
            'data-h2w3b-enable-flow="true"',
            "客户知识维护向导",
            "按四步把业务资料变成可用回复",
            "导入知识文档",
            "启用与回归检查",
            "自动回复处理方式",
            "高置信问题生成回复草稿",
            "真实发送继续受渠道授权控制",
        ],
    )
    require_contains(
        "frontend/src/styles.css",
        [
            ".customer-knowledge-center",
            ".customer-knowledge-layer-grid",
            ".customer-knowledge-publish-flow",
            ".reply-decision-state-card",
            ".knowledge-edit-checklist",
        ],
    )
    require_contains(
        "docs/FRONTEND_FUNCTION_REALITY_MATRIX.md",
        [
            "P3-06U-26H2W3B",
            "知识运营四步维护流程",
            "导入知识文档",
            "自动回复处理方式",
        ],
    )
    require_contains(
        "docs/P3-06U-26H2W3B_CUSTOMER_KNOWLEDGE_MAINTENANCE_FLOW.md",
        [
            "# P3-06U-26H2W3B 客户知识维护四步流程收束",
            "真实外发继续关闭",
            "不重写后端知识模型",
            "知识评测仍不是完整线上客服准确率",
        ],
    )

    retired_visible_copy = [
        "编辑知识草稿",
        "自动回复状态机",
        "AI 回复预案",
        "知识更新路径",
        "符合策略的回复自动处理",
    ]
    require_absent("frontend/src/App.tsx", retired_visible_copy)
    require_absent("frontend/src/styles.css", [".knowledge-update-path"])
    require_absent("docs/FRONTEND_FUNCTION_REALITY_MATRIX.md", ["“编辑知识草稿”命名不准"])

    print("P3-06U-26H2W3B customer knowledge flow static check passed.")


if __name__ == "__main__":
    main()
