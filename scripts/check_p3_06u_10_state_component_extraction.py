#!/usr/bin/env python3
"""Static checks for P3-06U-10 frontend state component extraction."""

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
    common_state = read_text("frontend/src/components/common/WorkspaceState.tsx")
    u09_check = read_text("scripts/check_p3_06u_09_unified_states.py")
    doc = read_text("docs/P3-06U-10_FRONTEND_STATE_COMPONENT_EXTRACTION.md")

    require(
        "from \"./components/common/WorkspaceState\"" in app,
        "App should import unified state components from components/common",
    )
    require("function WorkspaceStateNotice" not in app, "App should not define WorkspaceStateNotice after extraction")
    require("function PanelStateNotice" not in app, "App should not define PanelStateNotice after extraction")
    require("function DataSourceBadge" not in app, "App should not define DataSourceBadge after extraction")
    require("function DisabledReason" not in app, "App should not define DisabledReason after extraction")
    require("function WorkspaceRuntimeStateStrip" not in app, "App should not define WorkspaceRuntimeStateStrip after extraction")
    require("type WorkspaceStateKind" not in app, "App should not define WorkspaceStateKind after extraction")
    require("type DataSourceMode" not in app, "App should not define DataSourceMode after extraction")

    for snippet in [
        "export type WorkspaceStateKind",
        "export type DataSourceMode",
        "export function WorkspaceStateNotice",
        "export function PanelStateNotice",
        "export function DataSourceBadge",
        "export function DisabledReason",
        "export function formatAccessDisabledReason",
        "export function WorkspaceRuntimeStateStrip",
        'data-state-system="ledger"',
        'data-state-system="notice"',
        'data-state-system="source-badge"',
    ]:
        require(snippet in common_state, f"WorkspaceState.tsx missing exported snippet: {snippet}")

    for snippet in [
        "WorkspaceRuntimeStateStrip",
        "PanelStateNotice",
        "DataSourceBadge",
        "DisabledReason",
        "formatAccessDisabledReason",
    ]:
        require(app.count(snippet) >= 2, f"App should still use extracted component/helper: {snippet}")

    require(
        "frontend/src/components/common/WorkspaceState.tsx" in u09_check,
        "P3-06U-09 static check should understand extracted common state file",
    )

    for phrase in [
        "# P3-06U-10 前端组件和状态结构拆分第一片",
        "行为不变，结构变清楚",
        "不改真实外发开关",
        "components/common/WorkspaceState.tsx",
    ]:
        require(phrase in doc, f"U10 documentation missing phrase: {phrase}")

    require(len(app.splitlines()) < 11850, "App.tsx should shrink after state component extraction")

    print("P3-06U-10 state component extraction static checks passed.")


if __name__ == "__main__":
    main()
