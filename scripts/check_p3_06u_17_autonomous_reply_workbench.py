#!/usr/bin/env python3
"""Static checks for P3-06U-17 autonomous reply workbench refinement."""

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
    doc = read_text("docs/P3-06U-17_YUNDUO_AI_REFERENCE_AND_AUTONOMOUS_REPLY_WORKBENCH.md")

    for snippet in [
        "AI 自动回复",
        "autoReplyGateLabel",
        "requiresManualReplyGate",
        "auto-reply-status-strip",
        "auto-reply-record",
        "AI 正在自动接待，人工无需操作。",
        "转人工提醒",
        "高置信会话按策略自动回复",
        "异常会话进入人工门禁",
    ]:
        require(snippet in component, f"component missing autonomous-reply snippet: {snippet}")

    for removed_snippet in [
        "坐席回复草稿",
        "等待生成",
        "内部备注 / 审核意见",
        "只记内部备注",
        "人工确认放行",
        "确认发送队列",
        "人工接管 / 异常备注",
    ]:
        require(removed_snippet not in component, f"component still contains manual-first copy: {removed_snippet}")

    for snippet in [
        "grid-template-columns: minmax(176px, 204px) minmax(0, 1fr)",
        ".auto-reply-status-strip",
        ".auto-reply-record",
        ".auto-reply-idle-note",
        "grid-template-rows: auto minmax(460px, 1fr) auto",
    ]:
        require(snippet in styles, f"styles missing autonomous-reply snippet: {snippet}")

    for phrase in [
        "# P3-06U-17 云朵AI视频参考与自动回复工作台收束",
        "渠道入站消息 -> 统一会话/消息存储",
        "475 张 1fps 抽帧",
        "商品学习",
        "默认路径应该是 AI 自主回复",
        "所有渠道消息必须进入统一收录层",
        "不把平台接入能力说成已经合规可用",
        "业务对象知识库",
    ]:
        require(phrase in doc, f"documentation missing phrase: {phrase}")

    for path in [
        "output/p3_06u_17_yunduo_ai_reference/sheets/yunduo_keyframes_contact_sheet.png",
        "output/p3_06u_17_yunduo_ai_reference/sheets/yunduo_scenes_contact_sheet.png",
    ]:
        require((ROOT / path).exists(), f"missing extracted video evidence: {path}")

    print("P3-06U-17 autonomous reply workbench checks passed.")


if __name__ == "__main__":
    main()
