#!/usr/bin/env python3
"""Static checks for P3-06U-16 workbench IA and WeChat-style reduction."""

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
    panel = read_text("frontend/src/components/conversation/ConversationWorkbenchPanel.tsx")
    styles = read_text("frontend/src/styles.css")
    doc = read_text("docs/P3-06U-16_WORKBENCH_IA_AND_WECHAT_STYLE_REDUCTION.md")

    for snippet in [
        "{ label: \"接待工作台\", href: \"#live\"",
        "{ label: \"会话收件箱\", href: \"#conversations\", count: \"后台\", active: false, hiddenFromSidebar: true }",
        "{ label: \"人工审核\", href: \"#reviews\", count: \"后台\", active: false, hiddenFromSidebar: true }",
        "{ label: \"待发送草稿\", href: \"#outbox\", count: \"后台\", active: false, hiddenFromSidebar: true }",
        "{ label: \"工单/SLA\", href: \"#tickets\", count: \"后台\", active: false, hiddenFromSidebar: true }",
        "queue=needs_review",
        "queue=sla_breached",
    ]:
        require(snippet in navigation, f"navigation missing IA reduction snippet: {snippet}")

    for snippet in [
        "const sidebarItems = group.items.filter((item) => !item.hiddenFromSidebar)",
        "pending_outbox: \"待发送\"",
    ]:
        require(snippet in app, f"App missing sidebar/deep-link snippet: {snippet}")

    for snippet in [
        "| \"pending_outbox\"",
        "hasPendingOutboxSignal",
        "service-desk-toolbar",
        "service-source-pill",
        "service-thread-meta",
        "service-thread-preview",
        "service-thread-alerts",
        "auto-reply-record",
        "AI 正在自动接待，人工无需操作。",
        "const primaryQueueKeys: WorkbenchQueueKey[] = [\"all\", \"mine\", \"needs_review\"]",
    ]:
        require(snippet in panel, f"conversation panel missing reduced workbench snippet: {snippet}")

    for removed_snippet in [
        "左侧选客户，右侧处理消息、AI 草稿和人工接管。",
        "service-desk-mode",
        "data-source-badge mode-",
    ]:
        require(removed_snippet not in panel, f"conversation panel still contains old heavy header snippet: {removed_snippet}")

    for snippet in [
        ".service-desk-toolbar",
        ".service-toolbar-meta",
        ".service-source-pill",
        "grid-template-columns: minmax(176px, 204px) minmax(0, 1fr)",
        ".service-thread-meta",
        ".service-thread-preview",
        ".auto-reply-record",
        ".auto-reply-idle-note",
        "grid-template-rows: auto minmax(460px, 1fr) auto",
    ]:
        require(snippet in styles, f"styles missing reduced workbench snippet: {snippet}")

    for phrase in [
        "# P3-06U-16 工作台去重与微信式对话台再瘦身",
        "日常接待只有一个主入口",
        "后台页保留但从左侧主导航隐藏",
        "待审、待发、超时和异常都回到接待工作台队列",
        "本轮不打开真实外发",
    ]:
        require(phrase in doc, f"documentation missing phrase: {phrase}")

    print("P3-06U-16 workbench IA and WeChat-style reduction static checks passed.")


if __name__ == "__main__":
    main()
