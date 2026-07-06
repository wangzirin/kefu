#!/usr/bin/env python3
"""Static checks for P3-06U-02 role task paths."""

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
    styles = read_text("frontend/src/styles.css")
    doc = read_text("docs/P3-06U-02_ROLE_TASK_PATHS.md")

    for snippet in [
        "export interface RoleTaskPath",
        "export const roleTaskPaths",
        "getRoleTaskPathsForRoles",
        "ops-risk-scan",
        "live-inbox",
        "review-risk-drafts",
        "outbox-gate",
        "quality-cause-review",
        "knowledge-gap-repair",
        "channel-connector-status",
        "ops-health-check",
    ]:
        require(snippet in navigation, f"navigation missing role task path snippet: {snippet}")

    require(
        'agent: ["live-inbox", "review-risk-drafts", "outbox-gate", "customer-followup", "ticket-sla"]'
        in navigation,
        "agent task path must start with live inbox and preserve five practical tasks",
    )
    require(
        'viewer: ["ops-risk-scan", "quality-cause-review", "channel-connector-status"]'
        in navigation,
        "viewer task path must be read-oriented and limited to three tasks",
    )

    for snippet in [
        "visibleTaskPaths",
        "RoleTaskPathStrip",
        "getRoleTaskPathMetric",
        "role-task-paths",
        "role-task-path-grid",
        "role-task-metric",
        "aria-current",
    ]:
        require(snippet in app, f"App missing role task path snippet: {snippet}")

    for snippet in [
        ".role-task-paths",
        ".role-task-path-grid",
        ".role-task-path",
        ".role-task-path.is-active",
        ".role-task-path.is-urgent",
        ".role-task-metric",
        "scroll-snap-type: x proximity",
    ]:
        require(snippet in styles, f"styles missing role task path snippet: {snippet}")

    for phrase in [
        "# P3-06U-02 角色化任务路径重排",
        "owner",
        "admin",
        "agent",
        "viewer",
        "接待客户会话",
        "确认待发送",
        "真实外发继续关闭",
        "不替代后端 RBAC",
        "P3-06U-03 接待工作台实用性重构",
    ]:
        require(phrase in doc, f"documentation missing phrase: {phrase}")

    forbidden_fragments = [
        'count: "P3-06UI"',
        'count: "P3-06F"',
        'count: "RAG"',
        'value: "RAG"',
        "产品施工入口",
        "当前仍是规划态",
    ]
    for fragment in forbidden_fragments:
        require(fragment not in navigation + app, f"customer-facing UI still exposes internal wording: {fragment}")

    print("P3-06U-02 role task path checks passed.")


if __name__ == "__main__":
    main()
