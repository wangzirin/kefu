from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def require(path: str, *needles: str) -> None:
    content = read(path)
    missing = [needle for needle in needles if needle not in content]
    if missing:
        raise SystemExit(f"FAIL {path}: missing {missing}")


def main() -> None:
    require(
        "frontend/src/api/client.ts",
        "export type ReplyDecisionState",
        "export interface ReplyDecision",
        "export async function listReplyDecisions",
        "reply_decision_id: number | null",
        "knowledge_gap_id: number | null",
        "outbox_draft_id: number | null",
    )
    require(
        "frontend/src/App.tsx",
        "listReplyDecisions",
        "type ReplyDecision",
        "ReplyDecisionStateView",
        "refreshReplyDecisions",
        "const replyDecisions: ReplyDecision[]",
        "replyDecisions={replyDecisions}",
        "replyDecisionStatus={replyDecisionState.status}",
        "demo.replyDecisions",
        "formatDemoReplyDecisionNextAction",
    )
    require(
        "frontend/src/components/conversation/ConversationWorkbenchPanel.tsx",
        "replyDecisions: ReplyDecision[]",
        "replyDecisionByConversation",
        "data-reply-decision-strip=\"p3-06u-22\"",
        "回复决策",
        "业务对象",
        "知识依据",
        "下一步",
        "外发",
        "formatReplyDecisionStateLabel",
        "formatReplyDecisionReasonLabel",
        "formatReplyDecisionNextAction",
        "formatReplyDecisionObjectLabel",
        "compareDecisionFreshness",
        "replyDecision: relatedReplyDecision",
    )
    require(
        "frontend/src/styles.css",
        ".reply-decision-strip",
        ".reply-decision-strip-grid",
        ".decision-auto-reply-ready",
        ".decision-knowledge-gap",
        "grid-template-columns: minmax(208px, 236px) minmax(0, 1fr)",
    )
    require(
        "docs/P3-06U-22_WORKBENCH_REPLY_DECISION_VISUALIZATION.md",
        "P3-06U-22 工作台回复决策可视化",
        "不打开真实外发",
        "不是完整云朵AI级别",
        "多平台对话台",
        "reply_decisions",
    )
    print("PASS P3-06U-22 workbench reply decision visualization")


if __name__ == "__main__":
    main()
