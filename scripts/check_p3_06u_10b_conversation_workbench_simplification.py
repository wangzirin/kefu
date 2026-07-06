#!/usr/bin/env python3
"""Static checks for P3-06U-10B conversation workbench simplification."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_text(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    component = read_text("frontend/src/components/conversation/ConversationWorkbenchPanel.tsx")
    styles = read_text("frontend/src/styles.css")
    doc = read_text("docs/P3-06U-10B_CONVERSATION_WORKBENCH_WECHAT_SIMPLIFICATION.md")

    for snippet in [
        "wechat-service-desk",
        "service-desk-toolbar",
        "service-source-pill",
        "wechat-session-list",
        "wechat-chat-pane",
        "service-primary-queues",
        "真实外发关闭",
        "auto-reply-record",
        "AI 正在自动接待，人工无需操作。",
        "转人工",
    ]:
        require(snippet in component, f"conversation component missing simplification snippet: {snippet}")

    for removed_snippet in [
        "conversation-command-strip service-desk-signal-strip",
        'role="tab"',
        "inspector-tabs",
    ]:
        require(removed_snippet not in component, f"conversation component still contains old heavy UI snippet: {removed_snippet}")

    for snippet in [
        ".agent-desk-layout.service-desk-layout",
        "grid-template-columns: minmax(176px, 204px) minmax(0, 1fr)",
        ".service-primary-queues",
        ".auto-reply-record",
        ".wechat-chat-pane .timeline-event",
    ]:
        require(snippet in styles, f"styles missing simplification snippet: {snippet}")

    for phrase in [
        "# P3-06U-10B 多渠道对话台微信式收束",
        "微信式双栏接待台",
        "不打开真实外发",
        "队列筛选位于左侧会话列表",
        "右侧独立上下文栏不再作为第三列常驻",
        "1440 和 1280 桌面视口无横向溢出",
    ]:
        require(phrase in doc, f"documentation missing phrase: {phrase}")

    print("P3-06U-10B conversation workbench simplification static checks passed.")


if __name__ == "__main__":
    main()
