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
        "backend/app/workers/trusted_inbound_orchestrator.py",
        "create_reply_decision_for_message",
        "_reply_decision_idempotency_key",
        "_run_reply_decision_branch",
        "create_knowledge_gap_from_reply_decision",
        "outbox_pre_gate_external_write_closed",
        "manual_gate_required",
        "knowledge_gap_created",
        "blocked_by_policy_review",
    )
    require(
        "backend/app/services/knowledge.py",
        "create_knowledge_gap_from_reply_decision",
        "source_type=\"reply_decision\"",
        "source_ref=f\"reply_decision:{decision.id}\"",
        "knowledge_gap.created_from_reply_decision",
    )
    require(
        "backend/app/schemas/inbound_worker.py",
        "reply_decision_id: int | None = None",
        "knowledge_gap_id: int | None = None",
        "outbox_draft_id: int | None = None",
    )
    require(
        "backend/app/schemas/knowledge.py",
        "reply_decision",
    )
    require(
        "backend/app/api/knowledge.py",
        "reply_decision",
    )
    require(
        "backend/tests/test_trusted_inbound_worker_api.py",
        "test_trusted_inbound_worker_syncs_reply_decision_knowledge_gap",
        "test_trusted_inbound_worker_routes_manual_reply_decision_to_human_review",
        "test_trusted_inbound_worker_marks_auto_ready_as_outbox_pre_gate_without_draft",
        "create_reply_decision_for_message",
    )
    require(
        "docs/P3-06U-21_TRUSTED_INBOUND_REPLY_DECISION_LOOP.md",
        "P3-06U-21 可信入站与回复决策闭环第一片",
        "全程保持 `external_write=false`",
        "不创建 `outbox_drafts`",
        "没有真实平台外发",
        "没有真实模型调用",
    )
    print("PASS P3-06U-21 trusted inbound reply decision loop")


if __name__ == "__main__":
    main()
