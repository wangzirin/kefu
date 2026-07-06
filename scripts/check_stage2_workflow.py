#!/usr/bin/env python3
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]


REQUIRED_PATHS = [
    "backend/app/api/workflows.py",
    "backend/app/schemas/workflows.py",
    "backend/app/services/workflows.py",
    "backend/app/migrations/versions/0002_workflow_foundation.py",
    "backend/tests/test_workflows_api.py",
]

REQUIRED_TEXT = {
    "backend/app/main.py": [
        "app.include_router(workflows.router)",
    ],
    "backend/app/models/foundation.py": [
        "class WorkflowRun",
        "class WorkflowCheckpoint",
        "class WorkflowStepAttempt",
        "class HumanReviewTask",
    ],
    "backend/app/models/__init__.py": [
        "WorkflowRun",
        "WorkflowCheckpoint",
        "WorkflowStepAttempt",
        "HumanReviewTask",
    ],
    "backend/app/api/workflows.py": [
        "/conversations/{conversation_id}/workflow-runs",
        "/workflow-runs/{workflow_run_id}/checkpoints",
        "/workflow-runs/{workflow_run_id}/step-attempts",
        "/workflow-runs/{workflow_run_id}/human-review-tasks",
        "/tenants/{tenant_id}/human-review-tasks",
        "/tenants/{tenant_id}/human-review-inbox",
        "/human-review-tasks/{task_id}",
        "require_current_principal",
    ],
    "backend/app/services/workflows.py": [
        "require_conversation_for_principal",
        "create_workflow_run",
        "add_step_attempt",
        "add_checkpoint",
        "create_human_review_task",
        "list_human_review_inbox",
        "_human_review_evidence_from_state",
        "resolve_human_review_task",
        "workflow_run.created",
        "human_review.",
    ],
    "backend/app/schemas/workflows.py": [
        "class WorkflowRunCreate",
        "class WorkflowRunDetail",
        "class WorkflowCheckpointCreate",
        "class WorkflowStepAttemptCreate",
        "class HumanReviewTaskCreate",
        "class HumanReviewTaskResolve",
        "class HumanReviewInboxItemRead",
        "class HumanReviewEvidenceRead",
    ],
    "backend/app/migrations/versions/0002_workflow_foundation.py": [
        "workflow_runs",
        "workflow_checkpoints",
        "workflow_step_attempts",
        "human_review_tasks",
        'down_revision = "0001_foundation"',
    ],
    "backend/tests/test_workflows_api.py": [
        "test_workflow_run_checkpoint_and_human_review_flow",
        "test_human_review_inbox_enriches_model_and_knowledge_context",
        "test_resolving_human_review_records_final_reply_in_workflow_state",
        "test_workflow_run_rejects_cross_tenant_access",
        "workflow_run.created",
        "human_review.approved",
        "human-review-inbox",
    ],
}


def fail(message: str) -> None:
    print(f"FAIL stage2 workflow: {message}")
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

    print("PASS stage2 workflow")


if __name__ == "__main__":
    main()
