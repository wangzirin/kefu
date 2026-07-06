#!/usr/bin/env python3
"""Static readiness checks for P3-06P outbox resource RBAC migration."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_text(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def role_block(rbac: str, role: str, next_role: str | None) -> str:
    marker = f'"{role}":'
    block = rbac.split(marker, 1)[1]
    if next_role is None:
        return block.split("}", 1)[0]
    return block.split(f'"{next_role}":', 1)[0]


def main() -> None:
    rbac = read_text("backend/app/core/rbac.py")
    outbox_api = read_text("backend/app/api/outbox.py")
    failures_api = read_text("backend/app/api/delivery_failures.py")
    app = read_text("frontend/src/App.tsx")
    test = read_text("backend/tests/test_p3_06p_outbox_resource_rbac.py")
    doc = read_text("docs/P3-06P_OUTBOX_RESOURCE_RBAC.md")
    master = read_text("docs/PRODUCTIZATION_MASTER_PLAN_LITE_AND_STANDARD.md")
    superpowers_plan = read_text("docs/superpowers/plans/2026-06-27-roadmap-correction-and-p3-pilot-loop.md")

    permissions = [
        '"outbox.draft.read"',
        '"outbox.draft.manage"',
        '"outbox.send_attempt.read"',
        '"outbox.send_attempt.manage"',
        '"outbox.delivery_job.read"',
        '"outbox.delivery_job.manage"',
        '"outbox.failure_review.read"',
        '"outbox.failure_review.manage"',
    ]
    for permission in permissions:
        require(permission in rbac, f"RBAC matrix missing {permission}")

    owner_block = role_block(rbac, "owner", "admin")
    admin_block = role_block(rbac, "admin", "agent")
    agent_block = role_block(rbac, "agent", "viewer")
    viewer_block = role_block(rbac, "viewer", None)

    for block_name, block in [("owner", owner_block), ("admin", admin_block)]:
        for permission in permissions:
            require(permission in block, f"{block_name} should have {permission}")

    for permission in [
        '"outbox.draft.read"',
        '"outbox.draft.manage"',
        '"outbox.send_attempt.read"',
        '"outbox.send_attempt.manage"',
        '"outbox.delivery_job.read"',
        '"outbox.failure_review.read"',
        '"outbox.failure_review.manage"',
    ]:
        require(permission in agent_block, f"agent should have {permission}")
    require('"outbox.delivery_job.manage"' not in agent_block, "agent should not manage delivery jobs")

    require('"outbox.failure_review.read"' in viewer_block, "viewer should read failure reviews")
    for permission in [
        '"outbox.draft.read"',
        '"outbox.draft.manage"',
        '"outbox.send_attempt.read"',
        '"outbox.send_attempt.manage"',
        '"outbox.delivery_job.read"',
        '"outbox.delivery_job.manage"',
        '"outbox.failure_review.manage"',
    ]:
        require(permission not in viewer_block, f"viewer should not have {permission}")

    for snippet in [
        'OUTBOX_DRAFT_READ_PERMISSION = "outbox.draft.read"',
        'OUTBOX_DRAFT_MANAGE_PERMISSION = "outbox.draft.manage"',
        'OUTBOX_SEND_ATTEMPT_READ_PERMISSION = "outbox.send_attempt.read"',
        'OUTBOX_SEND_ATTEMPT_MANAGE_PERMISSION = "outbox.send_attempt.manage"',
        'OUTBOX_DELIVERY_JOB_READ_PERMISSION = "outbox.delivery_job.read"',
        'OUTBOX_DELIVERY_JOB_MANAGE_PERMISSION = "outbox.delivery_job.manage"',
        "require_permission(OUTBOX_DRAFT_READ_PERMISSION)",
        "require_permission(OUTBOX_DRAFT_MANAGE_PERMISSION)",
        "require_permission(OUTBOX_SEND_ATTEMPT_READ_PERMISSION)",
        "require_permission(OUTBOX_SEND_ATTEMPT_MANAGE_PERMISSION)",
        "require_permission(OUTBOX_DELIVERY_JOB_READ_PERMISSION)",
        "require_permission(OUTBOX_DELIVERY_JOB_MANAGE_PERMISSION)",
    ]:
        require(snippet in outbox_api, f"outbox API missing snippet: {snippet}")
    require("require_current_principal" not in outbox_api, "outbox API should use named permissions")

    for snippet in [
        'OUTBOX_FAILURE_REVIEW_READ_PERMISSION = "outbox.failure_review.read"',
        'OUTBOX_FAILURE_REVIEW_MANAGE_PERMISSION = "outbox.failure_review.manage"',
        "require_permission(OUTBOX_FAILURE_REVIEW_READ_PERMISSION)",
        "require_permission(OUTBOX_FAILURE_REVIEW_MANAGE_PERMISSION)",
    ]:
        require(snippet in failures_api, f"delivery failures API missing snippet: {snippet}")
    require("require_current_principal" not in failures_api, "delivery failures API should use named permissions")

    for snippet in [
        'outboxDraftManage: "outbox.draft.manage"',
        'outboxSendAttemptManage: "outbox.send_attempt.manage"',
        'outboxSendPlanManage: "outbox.send_plan.manage"',
        'outboxDeliveryJobManage: "outbox.delivery_job.manage"',
        'outboxFailureReviewManage: "outbox.failure_review.manage"',
        "PERMISSIONS.outboxDraftManage",
        "PERMISSIONS.outboxSendAttemptManage",
        "PERMISSIONS.outboxDeliveryJobManage",
        "PERMISSIONS.outboxFailureReviewManage",
        "canManageDraft={canManageOutboxDraft}",
        "canManageSendAttempt={canManageOutboxSendAttempt}",
        "canManageDeliveryJob={canManageOutboxDeliveryJob}",
        "canManageFailureReview={canManageFailureReview}",
        "disabled={!hasToken || !canManageDeliveryJob || isLoading || isQueueLoading}",
        "disabled={!hasToken || !canManageSendAttempt || isLoading}",
        "disabled={!hasToken || !canManageFailureReview || isLoading}",
    ]:
        require(snippet in app, f"App missing P3-06P permission snippet: {snippet}")

    for snippet in [
        "test_outbox_resource_permissions_matrix",
        "test_outbox_draft_and_dry_run_permissions",
        "test_delivery_job_queue_and_failure_review_permissions",
        "viewer_create.status_code == 403",
        "agent_dry_run.status_code == 201",
        "agent_job.status_code == 403",
        "viewer_reviews.status_code == 200",
        "viewer_resolve.status_code == 403",
        "agent_resolve.status_code == 200",
    ]:
        require(snippet in test, f"P3-06P test missing snippet: {snippet}")

    for phrase in [
        "P3-06P RBAC 第八片",
        "出站资源与失败复盘权限",
        "outbox.draft.manage",
        "outbox.send_attempt.manage",
        "outbox.delivery_job.manage",
        "outbox.failure_review.manage",
        "全局发送队列只允许 owner/admin",
        "真正安全边界仍以后端",
    ]:
        require(phrase in doc, f"P3-06P documentation missing phrase: {phrase}")

    for phrase in [
        "P3-06P",
        "outbox 剩余资源权限",
        "docs/P3-06P_OUTBOX_RESOURCE_RBAC.md",
        "scripts/check_p3_06p_outbox_resource_rbac.py",
        "backend/tests/test_p3_06p_outbox_resource_rbac.py",
    ]:
        require(phrase in master, f"Product master missing P3-06P phrase: {phrase}")
        require(phrase in superpowers_plan, f"Superpowers plan missing P3-06P phrase: {phrase}")

    print("P3-06P outbox resource RBAC checks passed.")


if __name__ == "__main__":
    main()
