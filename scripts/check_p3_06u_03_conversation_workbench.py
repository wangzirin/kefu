#!/usr/bin/env python3
"""Static checks for P3-06U-03 conversation workbench restructure."""

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
    component = read_text("frontend/src/components/conversation/ConversationWorkbenchPanel.tsx")
    styles = read_text("frontend/src/styles.css")
    doc = read_text("docs/P3-06U-03_CONVERSATION_WORKBENCH_RESTRUCTURE.md")

    require(
        'import { ConversationWorkbenchPanel } from "./components/conversation/ConversationWorkbenchPanel";' in app,
        "App must import the split ConversationWorkbenchPanel component",
    )
    require(
        "function ConversationWorkbenchPanel(" not in app and "function ConversationWorkbenchPanel({" not in app,
        "App must not keep the old inline ConversationWorkbenchPanel implementation",
    )

    for snippet in [
        "export function ConversationWorkbenchPanel",
        "service-desk-layout",
        "service-conversation-list",
        "service-chat-pane",
        "service-reply-dock",
        "auto-reply-record",
        "service-message-stream",
        "真实外发关闭",
        "高置信会话按策略自动回复",
        "AI 正在自动接待，人工无需操作。",
        "转人工",
    ]:
        require(snippet in component, f"conversation component missing snippet: {snippet}")

    for snippet in [
        ".service-desk-layout",
        ".service-conversation-list",
        ".service-chat-pane",
        ".service-reply-dock",
        ".service-inspector",
        ".service-thread-item",
        ".service-avatar",
        ".service-composer-actions",
    ]:
        require(snippet in styles, f"styles missing service desk class: {snippet}")

    for phrase in [
        "# P3-06U-03 接待工作台实用性重构",
        "不改变后端状态机",
        "不打开真实外发",
        "三栏 IM 工作台",
        "会话队列",
        "消息处理区",
        "右侧上下文",
        "审核通过只生成内部待发送草稿",
        "P3-06U-04 运营总览到处理路径打通",
    ]:
        require(phrase in doc, f"documentation missing phrase: {phrase}")

    print("P3-06U-03 conversation workbench checks passed.")


if __name__ == "__main__":
    main()
