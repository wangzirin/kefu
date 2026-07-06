#!/usr/bin/env python3
"""Static checks for P3-06U-26B WeChat-first conversation workbench."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def require(path: str, *needles: str) -> None:
    content = read(path)
    missing = [needle for needle in needles if needle not in content]
    if missing:
        raise SystemExit(f"FAIL {path}: missing {missing}")


def forbid(path: str, *needles: str) -> None:
    content = read(path)
    present = [needle for needle in needles if needle in content]
    if present:
        raise SystemExit(f"FAIL {path}: forbidden {present}")


def main() -> None:
    require(
        "frontend/src/components/conversation/ConversationWorkbenchPanel.tsx",
        'data-wechat-first-workbench="p3-06u-26b"',
        'data-autonomous-reply-workbench="p3-06u-26g2"',
        'data-service-decision-center="p3-06u-26b"',
        "auto-reply-record",
        "AI 自动回复",
        "AI 正在自动接待，人工无需操作。",
        "转人工",
        "真实外发关闭",
    )
    forbid(
        "frontend/src/components/conversation/ConversationWorkbenchPanel.tsx",
        '<details className="service-ai-assist-drawer">',
        'data-service-decision-center="p3-06u-12d"',
        "AI 建议",
        "客户可见回复预案",
        "人工接管 / 异常备注",
        "内部备注",
        "确认发送队列",
        "<summary>更多筛选</summary>",
    )
    require(
        "frontend/src/styles.css",
        "grid-template-columns: minmax(176px, 204px) minmax(0, 1fr)",
        "grid-template-rows: auto minmax(460px, 1fr) auto",
        ".auto-reply-record",
        ".auto-reply-idle-note",
    )
    require(
        "docs/P3-06U-26B_WECHAT_FIRST_CONVERSATION_WORKBENCH.md",
        "# P3-06U-26B 多渠道对话台微信式收束",
        "右侧首屏优先消息流",
        "AI 自动回复记录靠近输入区",
        "全部 / 我的 / 转人工",
        "真实外发继续关闭",
        "不点击任何真实发送按钮",
    )
    print("PASS P3-06U-26B WeChat-first workbench static checks")


if __name__ == "__main__":
    main()
