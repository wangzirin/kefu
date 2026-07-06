#!/usr/bin/env python3
"""Static readiness checks for P3-06O frontend button permissions."""

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
    styles = read_text("frontend/src/styles.css")
    doc = read_text("docs/P3-06O_FRONTEND_BUTTON_PERMISSIONS.md")
    master = read_text("docs/PRODUCTIZATION_MASTER_PLAN_LITE_AND_STANDARD.md")
    superpowers_plan = read_text("docs/superpowers/plans/2026-06-27-roadmap-correction-and-p3-pilot-loop.md")

    for snippet in [
        "const PERMISSIONS = {",
        "type PermissionValue =",
        "function hasPermission(user: CurrentUser | null | undefined, permission: PermissionValue)",
        'conversationManage: "conversation.manage"',
        'ticketManage: "ticket.manage"',
        'leadManage: "lead.manage"',
        'knowledgeManage: "knowledge.manage"',
        'channelConnectorManage: "channel.connector.manage"',
        'outboxDraftManage: "outbox.draft.manage"',
        'outboxSendAttemptManage: "outbox.send_attempt.manage"',
        'outboxSendPlanManage: "outbox.send_plan.manage"',
        'outboxDeliveryJobManage: "outbox.delivery_job.manage"',
        'outboxFailureReviewManage: "outbox.failure_review.manage"',
    ]:
        require(snippet in app, f"App permissions layer missing snippet: {snippet}")

    require(
        'auth.user.roles.includes("owner") || auth.user.roles.includes("admin")' not in app,
        "App should not keep old owner/admin coarse canManage check for action buttons",
    )
    require(
        "function canManageKnowledge(user: CurrentUser) {\n  return hasPermission(user, PERMISSIONS.knowledgeManage);\n}" in app,
        "canManageKnowledge should read user.permissions",
    )

    for prop in [
        "canManageConversations",
        "canManageTickets",
        "canManageLeads",
        "canManageConnector",
        "canManageSendPlan",
        "canManageKnowledgeWorkspace",
    ]:
        require(prop in app, f"App missing frontend permission prop/value: {prop}")

    for guard in [
        "hasPermission(auth.user, PERMISSIONS.conversationManage)",
        "hasPermission(auth.user, PERMISSIONS.ticketManage)",
        "hasPermission(auth.user, PERMISSIONS.leadManage)",
        "hasPermission(auth.user, PERMISSIONS.knowledgeManage)",
        "hasPermission(auth.user, PERMISSIONS.outboxDraftManage)",
        "hasPermission(auth.user, PERMISSIONS.outboxSendAttemptManage)",
        "hasPermission(auth.user, PERMISSIONS.outboxSendPlanManage)",
        "hasPermission(auth.user, PERMISSIONS.outboxDeliveryJobManage)",
        "hasPermission(auth.user, PERMISSIONS.outboxFailureReviewManage)",
        "hasPermission(auth.user, PERMISSIONS.channelConnectorManage)",
    ]:
        require(guard in app, f"App handler guard missing: {guard}")

    for disabled_snippet in [
        "disabled={!canManageConversations || !canClaimConversation",
        "disabled={!canManageConversations || !canWorkConversation",
        "disabled={!hasToken || !canManageConversations || isLoading",
        "disabled={!canManageTickets || !canUpdateTicket",
        "disabled={!hasToken || !canManageTickets || isLoading",
        "disabled={!canManageLeads || !canUpdateLead",
        "disabled={!hasToken || !canManageLeads || isLoading",
        "disabled={!hasToken || !canImport || isLoading}",
        "disabled={!hasToken || !canManage || isLoading}",
        "disabled={!hasToken || !canManageSendAttempt || isLoading",
        "disabled={!hasToken || !canManageDeliveryJob || isLoading",
        "disabled={!hasToken || !canManageFailureReview || isLoading",
    ]:
        require(disabled_snippet in app, f"Button disabled state missing permission gate: {disabled_snippet}")

    require(
        "if (hasPermission(auth.user, PERMISSIONS.channelConnectorManage)) {\n        await ensureNoopChannelConnector" in app,
        "Connector auto-ensure should only run for channel.connector.manage users",
    )
    require(
        "需管理员预先配置连接器" in app and "outbox-action-hint" in app,
        "Outbox should explain connector admin prerequisite to send-plan users",
    )
    require(".outbox-action-hint" in styles, "CSS should style outbox permission hint")

    for phrase in [
        "P3-06O 前端按钮级权限第一片",
        "user.permissions",
        "conversation.manage",
        "ticket.manage",
        "lead.manage",
        "knowledge.manage",
        "outbox.send_plan.manage",
        "channel.connector.manage",
        "双层防线",
        "真正的安全边界仍以后端",
    ]:
        require(phrase in doc, f"P3-06O documentation missing phrase: {phrase}")

    for phrase in [
        "P3-06O",
        "前端按钮级权限",
        "scripts/check_p3_06o_frontend_button_permissions.py",
        "docs/P3-06O_FRONTEND_BUTTON_PERMISSIONS.md",
    ]:
        require(phrase in master, f"Product master missing P3-06O phrase: {phrase}")
        require(phrase in superpowers_plan, f"Superpowers plan missing P3-06O phrase: {phrase}")

    print("P3-06O frontend button permission checks passed.")


if __name__ == "__main__":
    main()
