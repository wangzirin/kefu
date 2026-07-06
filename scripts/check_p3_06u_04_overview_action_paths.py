#!/usr/bin/env python3
"""Static checks for P3-06U-04 overview-to-action path closure."""

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
    conversation = read_text("frontend/src/components/conversation/ConversationWorkbenchPanel.tsx")
    styles = read_text("frontend/src/styles.css")
    doc = read_text("docs/P3-06U-04_OVERVIEW_TO_ACTION_PATHS.md")

    for snippet in [
        "interface WorkspaceTaskContext",
        "parseWorkspaceTaskContext",
        "buildWorkspaceTaskHref",
        "getWorkspaceHashPath(hash)",
        "WorkspaceTaskContextBanner",
        "getWorkspaceTaskMatchCount",
        'params.source ?? "overview"',
        "task\", params.task",
        "本时间窗口暂无对应任务",
        "high-risk-conversations",
        "pending-outbox",
        "knowledge-gaps",
        "channel-exceptions",
        "setReviewListView",
        "setOutboxListView",
        "setKnowledgeGapListView",
        "setFailureListView",
    ]:
        require(snippet in app, f"App missing P3-06U-04 snippet: {snippet}")

    for snippet in [
        "targetQueue?: string",
        "targetChannelId?: number | null",
        "isWorkbenchQueueKey",
        "setActiveQueue(validTargetQueue)",
        "scopedConversations",
        "渠道 #",
    ]:
        require(snippet in conversation, f"Conversation workbench missing context support: {snippet}")

    for snippet in [
        ".task-context-banner",
        ".task-context-chips",
        ".task-context-empty",
        ".task-context-meta",
    ]:
        require(snippet in styles, f"styles missing task context class: {snippet}")

    for phrase in [
        "# P3-06U-04 运营总览到处理路径打通",
        "审核高风险会话",
        "确认待发送草稿",
        "修复知识缺口",
        "复盘渠道异常",
        "不打开真实外发",
        "P3-06U-05 真实登录与角色端到端前端 smoke",
    ]:
        require(phrase in doc, f"documentation missing phrase: {phrase}")

    print("P3-06U-04 overview action path checks passed.")


if __name__ == "__main__":
    main()
