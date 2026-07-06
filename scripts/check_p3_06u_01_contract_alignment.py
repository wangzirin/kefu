#!/usr/bin/env python3
"""Static checks for P3-06U-01 frontend/backend contract alignment."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_text(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    navigation = read_text("frontend/src/data/navigation.ts")
    app = read_text("frontend/src/App.tsx")
    matrix = read_text("docs/P3-06U-01_FRONTEND_BACKEND_CONTRACT_MATRIX.md")
    p3_06t_03 = read_text("docs/P3-06T-03_OPS_BI_COMMAND_CENTER_REDESIGN.md")

    forbidden_navigation_fragments = [
        'count: "P3-06UI"',
        'count: "P3-06F"',
        'count: "规划"',
        'count: "RAG"',
        'value: "RAG"',
    ]
    for fragment in forbidden_navigation_fragments:
        require(fragment not in navigation, f"navigation still exposes internal label: {fragment}")

    for fragment in ["产品施工入口", "当前仍是规划态", "当前保持规划态"]:
        require(fragment not in app, f"App still exposes planning/engineering wording: {fragment}")

    required_navigation_fragments = [
        'count: "今日"',
        'description: "经营信号"',
        'label: "知识缺口"',
        'label: "连接器状态"',
        'count: "健康"',
        'count: "安全"',
    ]
    for fragment in required_navigation_fragments:
        require(fragment in navigation, f"navigation missing customer-facing label: {fragment}")

    required_doc_sections = [
        "# P3-06U-01 前后端契约与页面路径盘点",
        "## 1. 工程控制卡",
        "## 2. 当前真实阶段",
        "## 3. 角色与权限基线",
        "## 4. 页面契约矩阵",
        "## 5. 第一批错位点",
        "## 6. 本轮已修复",
        "## 7. 下一步施工建议",
    ]
    for section in required_doc_sections:
        require(section in matrix, f"contract matrix missing section: {section}")

    required_routes = [
        "#overview",
        "#live",
        "#conversations",
        "#reviews",
        "#outbox",
        "#contacts",
        "#leads",
        "#tickets",
        "#knowledge",
        "#gaps",
        "#evals",
        "#quality",
        "#channels",
        "#ops",
        "#model",
        "#settings",
    ]
    for route in required_routes:
        require(route in matrix, f"contract matrix missing route: {route}")

    required_apis = [
        "GET /api/tenants/{tenant_id}/ops/dashboard",
        "GET /api/tenants/{tenant_id}/conversation-inbox",
        "PATCH /api/human-review-tasks/{task_id}",
        "GET /api/tenants/{tenant_id}/outbox-drafts",
        "GET /api/tenants/{tenant_id}/knowledge-documents",
        "GET /api/channel-providers",
        "GET /api/tenants/{tenant_id}/ops/worker-health",
    ]
    for api in required_apis:
        require(api in matrix, f"contract matrix missing API: {api}")

    for key in ["U01-01", "U01-02", "U01-03", "U01-04", "U01-10"]:
        require(key in matrix, f"first mismatch list missing: {key}")

    require("Next stage: P3-06T-04" not in p3_06t_03, "P3-06T-03 handoff still points to stale P3-06T-04")
    require("P3-06U-02 角色化任务路径重排" in p3_06t_03, "P3-06T-03 handoff should point to P3-06U")

    print("P3-06U-01 contract alignment checks passed.")


if __name__ == "__main__":
    main()
