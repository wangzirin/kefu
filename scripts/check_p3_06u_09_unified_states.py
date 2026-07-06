#!/usr/bin/env python3
"""Static checks for P3-06U-09 unified frontend state system."""

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
    conversation = read_text("frontend/src/components/conversation/ConversationWorkbenchPanel.tsx")
    styles = read_text("frontend/src/styles.css")
    doc = read_text("docs/P3-06U-09_FRONTEND_STATE_SYSTEM.md")
    browser_script = read_text("scripts/check_p3_06u_09_unified_states.mjs")
    state_sources = app + common_state

    for snippet in [
        "type WorkspaceStateKind",
        "WorkspaceStateNotice",
        "PanelStateNotice",
        "DataSourceBadge",
        "DisabledReason",
        "WorkspaceRuntimeStateStrip",
        'data-state-system="ledger"',
        'data-state-system="notice"',
        'data-state-system="source-badge"',
        "加载中",
        "暂无数据",
        "无权限",
        "配置缺失",
        "接口失败",
        "演示样本",
        "真实服务端数据",
        "真实外发关闭",
        "不自动真实外发",
        "formatAccessDisabledReason",
    ]:
        require(snippet in state_sources, f"unified state source missing snippet: {snippet}")

    require(
        "from \"./components/common/WorkspaceState\"" in app,
        "App should import extracted unified state components from components/common",
    )

    for snippet in [
        'data-state-kind="empty"',
        'data-state-kind="missing_config"',
        'data-source-mode="off"',
        "approveDisabledReason",
        "真实服务端数据",
        "演示样本",
        "真实外发关闭",
        "disabled-reason",
    ]:
        require(snippet in conversation, f"conversation workbench missing state snippet: {snippet}")

    require(app.count("PanelStateNotice") >= 10, "expected broad PanelStateNotice coverage in core panels")
    require(app.count("DataSourceBadge") >= 20, "expected broad DataSourceBadge coverage in core panels")
    require(app.count("DisabledReason") >= 10, "expected disabled reason coverage in core actions")
    require(conversation.count("workspace-state-notice") >= 2, "conversation workbench should use unified notice classes")

    for snippet in [
        ".workspace-state-ledger",
        ".panel-state-row",
        ".data-source-badge",
        ".workspace-state-notice",
        ".workspace-state-icon",
        ".disabled-reason",
        ".workspace-state-notice.tone-loading",
        ".workspace-state-notice.tone-empty",
        ".workspace-state-notice.tone-no-permission",
        ".workspace-state-notice.tone-missing-config",
        ".workspace-state-notice.tone-error",
        ".data-source-badge.mode-demo",
        ".data-source-badge.mode-real",
        ".data-source-badge.mode-off",
        ".data-source-badge.mode-missing_config",
    ]:
        require(snippet in styles, f"styles missing unified state class: {snippet}")

    for phrase in [
        "# P3-06U-09 前端状态体系统一",
        "核心页面落地",
        "真实外发仍保持关闭",
        "P3-06U-10",
        "浏览器烟测",
    ]:
        require(phrase in doc, f"documentation missing phrase: {phrase}")

    for snippet in [
        "p3_06u_09_unified_states",
        "data-state-system",
        "workspace-state-ledger",
        "演示样本",
        "配置缺失",
        "真实外发关闭",
        "desktop-1440",
        "mobile-390",
        "summary.json",
    ]:
        require(snippet in browser_script, f"browser smoke missing snippet: {snippet}")

    print("P3-06U-09 unified state system static checks passed.")


if __name__ == "__main__":
    main()
