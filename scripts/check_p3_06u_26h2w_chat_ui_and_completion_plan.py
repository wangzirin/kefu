#!/usr/bin/env python3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "P3-06U-26H2W_ENGINEERING_COMPLETION_AND_CUSTOMER_KNOWLEDGE_CENTER_PLAN.md"
WORKBENCH = ROOT / "frontend" / "src" / "components" / "conversation" / "ConversationWorkbenchPanel.tsx"
STYLES = ROOT / "frontend" / "src" / "styles.css"
NAVIGATION = ROOT / "frontend" / "src" / "data" / "navigation.ts"


def require_contains(text: str, needle: str, label: str) -> None:
    if needle not in text:
        raise SystemExit(f"[FAIL] {label} missing: {needle}")


def require_absent(text: str, needle: str, label: str) -> None:
    if needle in text:
        raise SystemExit(f"[FAIL] {label} still contains banned copy: {needle}")


def main() -> None:
    if not DOC.exists():
        raise SystemExit(f"[FAIL] missing document: {DOC}")

    doc = DOC.read_text(encoding="utf-8")
    component = WORKBENCH.read_text(encoding="utf-8")
    styles = STYLES.read_text(encoding="utf-8")
    navigation = NAVIGATION.read_text(encoding="utf-8")

    for needle in [
        "P3-06U-26H2W 工程完善推进与客户知识建设中心计划",
        "真实 IM 消息流暂缓",
        "线上回执与准确率闭环",
        "XLSX、PDF、DOCX",
        "云接收台",
        "真实更新、恢复和回滚",
        "生产级 RAG",
        "四层知识建设中心",
        "客户知识发布流程",
        "自动回复策略",
        "真实外发继续关闭",
        "RPA 研究线只做内部可行性判断"
    ]:
        require_contains(doc, needle, "H2W plan")

    for marker in [
        'data-chat-ui-slimmed="p3-06u-26h2w"',
        'data-function-reality="no-fake-chat-actions"',
        "service-list-search",
        "service-chat-composer",
        "客服消息",
        "真实外发关闭",
        "保存接管回复"
    ]:
        require_contains(component, marker, "ConversationWorkbenchPanel")

    for marker in [
        ".service-agent-card",
        ".service-list-search",
        ".service-chat-readonly-status",
        ".service-chat-composer",
        ".composer-send-button"
    ]:
        require_contains(styles, marker, "styles")

    banned_component_copy = [
        "chat-head-action",
        "composer-tool-button",
        "历史记录",
        "设为星标",
        "发送图片",
        "添加附件",
        "AI 自主回复预备",
        "自动回复预备",
        "AI 回复建议",
        "转人工提醒",
        "AI 自动回复判断",
        "转人工判断",
        "系统门禁",
        "AI 建议",
        "AI 接管",
        "最近 AI",
        "AI 已生成",
        "AI 无法",
        "预备"
    ]
    for banned in banned_component_copy:
        require_absent(component, banned, "ConversationWorkbenchPanel")

    require_absent(navigation, "查看客户消息、AI 自动回复和转人工提醒", "navigation")
    require_absent(navigation, "AI 无法稳妥回复", "navigation")

    print("[PASS] P3-06U-26H2W chat UI slimming and completion plan checks passed")


if __name__ == "__main__":
    main()
