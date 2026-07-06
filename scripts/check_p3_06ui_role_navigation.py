#!/usr/bin/env python3
"""Static readiness checks for P3-06UI role-based navigation."""

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
    doc = read_text("docs/P3-06UI_ROLE_BASED_NAVIGATION.md")

    for snippet in [
        'export type NavigationRole = "owner" | "admin" | "agent" | "viewer"',
        "visibleTo?: NavigationRole[]",
        "getNavigationGroupsForRoles",
        "getDefaultNavigationHrefForRoles",
        'visibleTo: ["owner", "admin"]',
        'visibleTo: ["owner", "admin", "agent"]',
        'visibleTo: ["owner", "admin", "viewer"]',
        'return "#live"',
    ]:
        require(snippet in navigation, f"navigation missing role snippet: {snippet}")

    for snippet in [
        "visibleNavigationGroups",
        "getAccessibleWorkspaceSection",
        "isWorkspaceSectionVisible",
        "getWorkspaceRoleLabel",
        "getWorkspaceRoleHint",
        "nav-role-summary",
        "window.history.replaceState",
    ]:
        require(snippet in app, f"App missing role-navigation snippet: {snippet}")

    require("visibleNavigationGroups.map" in app, "sidebar must render role-filtered navigation groups")
    require("navigationGroups.map" not in app, "sidebar should not render unfiltered navigation groups")
    require(".nav-role-summary" in styles, "role summary styling is missing")

    for phrase in [
        "agent",
        "默认入口是 `#live`",
        "完整权限系统已经完成",
        "前端隐藏菜单不是安全边界",
        "后端 RBAC",
    ]:
        require(phrase in doc, f"documentation missing phrase: {phrase}")

    print("P3-06UI role navigation checks passed.")


if __name__ == "__main__":
    main()

