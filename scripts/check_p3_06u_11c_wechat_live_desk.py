#!/usr/bin/env python3
"""Static checks for P3-06U-11C WeChat-style live desk first pass."""

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
    panel = read_text("frontend/src/components/conversation/ConversationWorkbenchPanel.tsx")
    doc = read_text("docs/P3-06U-11C_WECHAT_STYLE_LIVE_DESK_FIRST_PASS.md")

    require(
        'activeSection !== "overview" && activeSection !== "live" ? (' in app,
        "live desk must not render role task paths/runtime strips above the chat workspace",
    )
    require("onRefresh={refreshLiveWorkspaceResources}" in app, "live desk must receive real data refresh action")

    for snippet in [
        ".topbar-live .page-kicker",
        ".topbar-live .connection-card",
        ".workspace-page-live .service-desk-toolbar",
        ".workspace-page-live .section-kicker",
        ".workspace-page-live .service-inline-card",
        "calc(100vh - 132px)",
    ]:
        require(snippet in styles, f"styles missing live desk compaction snippet: {snippet}")

    for snippet in [
        "service-desk-toolbar",
        "auto-reply-record",
        "service-refresh-action",
        "多渠道对话",
    ]:
        require(snippet in panel, f"conversation panel missing live desk snippet: {snippet}")

    for phrase in [
        "# P3-06U-11C 微信式多渠道对话台第一片",
        "普通坐席进入后应先看到客户列表和对话区",
        "本轮没有删除以下路由",
        "导航降级和职责重分配",
    ]:
        require(phrase in doc, f"documentation missing phrase: {phrase}")

    print("P3-06U-11C WeChat-style live desk static checks passed.")


if __name__ == "__main__":
    main()
