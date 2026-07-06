#!/usr/bin/env python3
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]


REQUIRED_PATHS = [
    "backend/app/api/reply_orchestrator.py",
    "backend/app/schemas/reply_orchestrator.py",
    "backend/app/services/model_gateway.py",
    "backend/app/services/reply_orchestrator.py",
    "backend/tests/test_reply_orchestrator_api.py",
]

REQUIRED_TEXT = {
    "backend/app/main.py": [
        "reply_orchestrator",
        "app.include_router(reply_orchestrator.router)",
    ],
    "backend/app/api/reply_orchestrator.py": [
        "/messages/{message_id}/reply-orchestrations",
        "require_current_principal",
        "orchestrate_reply_for_message",
    ],
    "backend/app/schemas/reply_orchestrator.py": [
        "class ReplyOrchestrationCreate",
        "ReplyMode",
        "knowledge_search",
        "model_assisted",
        "knowledge_query",
        "knowledge_top_k",
        "model_provider",
        "model_temperature",
        "class ReplyKnowledgeMatchRead",
        "class ReplyModelCallRead",
        "class ReplyOrchestrationRead",
        "confidence",
        "risk_level",
        "human_review_task",
        "knowledge_matches",
        "model_call",
    ],
    "backend/app/services/model_gateway.py": [
        "MODEL_GATEWAY_VERSION = \"model_gateway_v1\"",
        "DETERMINISTIC_MODEL = \"deterministic-local-draft-v1\"",
        "ModelDraftRequest",
        "ModelDraftResult",
        "generate_reply_draft",
        "chat/completions",
    ],
    "backend/app/core/config.py": [
        "bailian_api_base",
        "bailian_api_key",
        "bailian_model",
        "deepseek_api_base",
        "deepseek_api_key",
        "deepseek_model",
        "model_http_timeout_seconds",
    ],
    "backend/app/services/reply_orchestrator.py": [
        "AUTO_REPLY_CONFIDENCE_THRESHOLD",
        "require_inbound_message_for_principal",
        "KnowledgeSearchRequest",
        "search_knowledge_cards",
        "generate_reply_draft",
        "ResolvedReplyPlan",
        "_resolve_knowledge_search_plan",
        "_resolve_model_assisted_plan",
        "retrieval_engine",
        "model_unavailable",
        "create_workflow_run",
        "add_step_attempt",
        "add_checkpoint",
        "create_human_review_task",
        "complete_workflow_run",
        "no_knowledge_hit",
    ],
    "backend/app/services/workflows.py": [
        "def complete_workflow_run",
        "workflow_run.completed",
    ],
    "backend/tests/test_reply_orchestrator_api.py": [
        "test_reply_orchestration_completes_high_confidence_low_risk_message",
        "test_reply_orchestration_can_generate_draft_from_knowledge_search",
        "test_reply_orchestration_can_generate_model_assisted_draft_from_knowledge",
        "test_reply_orchestration_sends_unavailable_model_provider_to_human_review",
        "test_reply_orchestration_creates_human_review_for_low_confidence",
        "test_reply_orchestration_sends_no_knowledge_search_hit_to_human_review",
        "test_reply_orchestration_requires_human_review_when_no_knowledge_hit",
        "test_reply_orchestration_rejects_cross_tenant_and_outbound_messages",
    ],
}


def fail(message: str) -> None:
    print(f"FAIL stage2 orchestrator: {message}")
    sys.exit(1)


def main() -> None:
    missing = [path for path in REQUIRED_PATHS if not (ROOT / path).exists()]
    if missing:
        fail("missing files: " + ", ".join(missing))

    for path, fragments in REQUIRED_TEXT.items():
        content = (ROOT / path).read_text(encoding="utf-8")
        for fragment in fragments:
            if fragment not in content:
                fail(f"missing fragment in {path}: {fragment}")

    print("PASS stage2 orchestrator")


if __name__ == "__main__":
    main()
