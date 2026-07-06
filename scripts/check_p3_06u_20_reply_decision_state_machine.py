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
        "backend/app/models/foundation.py",
        "class ReplyDecision",
        "__tablename__ = \"reply_decisions\"",
        "business_object_id",
        "object_knowledge_card_id",
        "external_write_allowed",
        "idempotency_key",
    )
    require(
        "backend/app/migrations/versions/0024_reply_decisions.py",
        "revision = \"0024_reply_decisions\"",
        "down_revision = \"0023_business_object_knowledge\"",
        "op.create_table(",
        "reply_decisions",
    )
    require(
        "backend/app/services/reply_decisions.py",
        "BLOCKED_POLICY_TERMS",
        "MANUAL_REVIEW_TERMS",
        "auto_reply_ready",
        "manual_gate_required",
        "knowledge_gap",
        "blocked_by_policy",
        "draft_only",
        "reply_decision.created",
        "external_write_allowed_after_gate",
    )
    require(
        "backend/app/api/reply_decisions.py",
        "/messages/{message_id}/reply-decisions",
        "/tenants/{tenant_id}/reply-decisions",
        "CONVERSATION_MANAGE_PERMISSION",
        "CONVERSATION_READ_PERMISSION",
    )
    require(
        "backend/tests/test_reply_decisions_api.py",
        "test_reply_decision_marks_high_confidence_object_card_as_ready_draft_only",
        "test_reply_decision_records_knowledge_gap_when_object_is_missing",
        "test_reply_decision_blocks_policy_risk_even_when_object_matches",
        "test_reply_decision_requires_manual_gate_for_legal_risk_terms",
        "test_reply_decision_rejects_cross_tenant_and_outbound_messages",
    )
    require(
        "frontend/src/api/client.ts",
        "export interface ReplyDecision",
        "createReplyDecision",
        "listReplyDecisions",
    )
    require(
        "frontend/src/App.tsx",
        "data-reply-decision-state-machine=\"p3-06u-20\"",
        "自动回复处理方式",
        "业务对象",
        "对象问答卡",
        "回复草稿",
    )
    require(
        "docs/P3-06U-20_REPLY_DECISION_STATE_MACHINE.md",
        "P3-06U-20 自动回复策略状态机第一片",
        "不发送到微信、企微、抖音、淘宝、京东或拼多多",
        "没有真实模型调用",
        "没有真实平台外发",
        "没有写 outbox",
    )
    print("PASS P3-06U-20 reply decision state machine")


if __name__ == "__main__":
    main()
