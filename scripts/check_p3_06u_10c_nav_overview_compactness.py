#!/usr/bin/env python3
"""Static checks for P3-06U-10C default overview and compact navigation."""

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
    doc = read_text("docs/P3-06U-10C_NAV_OVERVIEW_COMPACTNESS.md")

    require('visibleTo: ["owner", "admin", "agent", "viewer"]' in navigation, "overview must be visible to agent")
    require('return "#overview";' in navigation, "default navigation must return overview")
    require('return "#live";' not in navigation, "default navigation must not return live")

    for snippet in [
        "expandedNavGroups",
        "ChevronDown",
        "aria-expanded",
        'nav-child-list${isExpanded ? " expanded" : " collapsed"}',
        'activeSection !== "overview"',
        'window.history.replaceState(null, "", "#overview")',
    ]:
        require(snippet in app, f"App missing compact navigation snippet: {snippet}")

    for removed in ["<em>{group.description}</em>", "<small>{group.count}</small>", "<small>{item.count}</small>"]:
        require(removed not in app, f"sidebar still renders secondary navigation copy: {removed}")

    for snippet in [
        "grid-template-columns: 224px minmax(0, 1fr)",
        ".nav-child-list.collapsed",
        ".nav-child-list.expanded",
        ".nav-chevron",
        ".topbar-overview p",
        "display: none;",
        "#workspace-overview .command-head",
        ".ops-bi-title p",
        ".ops-bi-source-contract",
    ]:
        require(snippet in styles, f"styles missing compact overview snippet: {snippet}")

    for phrase in [
        "# P3-06U-10C 默认总览与侧栏收束",
        "默认落到“运营总览”",
        "左侧导航收窄",
        "默认折叠",
        "真实登录说明",
        "不启用真实平台外发",
    ]:
        require(phrase in doc, f"documentation missing phrase: {phrase}")

    print("P3-06U-10C nav overview compactness static checks passed.")


if __name__ == "__main__":
    main()
