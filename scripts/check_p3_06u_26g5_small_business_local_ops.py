#!/usr/bin/env python3
"""Static checks for P3-06U-26G5 small-business knowledge and local ops simplification."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_text(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def require_all(text: str, snippets: list[str], label: str) -> None:
    for snippet in snippets:
        require(snippet in text, f"{label} missing required snippet: {snippet}")


def main() -> None:
    app = read_text("frontend/src/App.tsx")
    navigation = read_text("frontend/src/data/navigation.ts")
    client = read_text("frontend/src/api/client.ts")
    api = read_text("backend/app/api/knowledge.py")
    service = read_text("backend/app/services/knowledge.py")
    doc = read_text("docs/P3-06U-26G5_SMALL_BUSINESS_LOCAL_OPS_AND_KNOWLEDGE_SIMPLIFICATION.md")

    require('"实验室"' not in navigation, "visible lab navigation should be removed")
    require("#rpa-lab" not in navigation, "RPA lab hash should not appear in navigation")
    require("RpaCopilotLabPanel" not in app, "RPA lab panel should not be routed from App")
    require('"rpa-lab"' not in app, "RPA lab workspace section and aliases should be removed from App")

    require_all(
        client,
        [
            "query?: string;",
            "search.set(\"query\", query);",
            "severity?: string;",
            "source_type?: string;",
        ],
        "frontend API client",
    )
    require_all(
        app,
        [
            "function KnowledgeGapFilterToolbar",
            'data-knowledge-gap-server-filters="p3-06u-26g5"',
            "服务端筛选 / 已加载",
            "source_type: view.sourceType",
            "query: view.query",
            "pagedResultFromServer<KnowledgeGap>(state.data)",
        ],
        "frontend knowledge gap panel",
    )
    require_all(
        api,
        [
            "query: str | None = Query(default=None, max_length=120)",
            "query=query",
        ],
        "knowledge gap API",
    )
    require_all(
        service,
        [
            "query: str | None",
            "normalized_query = (query or \"\").strip()",
            "KnowledgeGapItem.question_excerpt",
            "KnowledgeGapItem.source_excerpt",
            "KnowledgeGapItem.expected_terms",
        ],
        "knowledge gap service",
    )
    require_all(
        doc,
        [
            "# P3-06U-26G5 小微企业本地化运维与知识运营简化",
            "RPA 副驾驶实验室",
            "从中台侧边栏和主路由下线",
            "首次启动注册",
            "诊断包",
            "签名更新包",
            "不建议做真正的“完全免登录”",
            "本轮没有开启真实平台外发",
        ],
        "G5 doc",
    )

    print("P3-06U-26G5 small-business local ops check passed.")


if __name__ == "__main__":
    main()
