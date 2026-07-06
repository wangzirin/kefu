#!/usr/bin/env python3
"""Static readiness checks for P3-06K conversation RBAC migration."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_text(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    rbac = read_text("backend/app/core/rbac.py")
    conversations_api = read_text("backend/app/api/conversations.py")
    test = read_text("backend/tests/test_p3_06k_conversation_rbac.py")
    doc = read_text("docs/P3-06K_CONVERSATION_RBAC.md")

    for permission in ['"conversation.read"', '"conversation.manage"']:
        require(permission in rbac, f"RBAC matrix missing {permission}")

    owner_block = rbac.split('"owner":', 1)[1].split('"admin":', 1)[0]
    admin_block = rbac.split('"admin":', 1)[1].split('"agent":', 1)[0]
    agent_block = rbac.split('"agent":', 1)[1].split('"viewer":', 1)[0]
    viewer_block = rbac.split('"viewer":', 1)[1].split("}", 1)[0]
    for block_name, block in [("owner", owner_block), ("admin", admin_block), ("agent", agent_block)]:
        require('"conversation.read"' in block, f"{block_name} should have conversation.read")
        require('"conversation.manage"' in block, f"{block_name} should have conversation.manage")
    require('"conversation.read"' not in viewer_block, "viewer should not have conversation.read yet")
    require('"conversation.manage"' not in viewer_block, "viewer should not have conversation.manage")

    for snippet in [
        'CONVERSATION_READ_PERMISSION = "conversation.read"',
        'CONVERSATION_MANAGE_PERMISSION = "conversation.manage"',
        "require_permission(CONVERSATION_READ_PERMISSION)",
        "require_permission(CONVERSATION_MANAGE_PERMISSION)",
        "_require_principal_tenant",
        "conversation.tenant_id != principal.tenant.id",
    ]:
        require(snippet in conversations_api, f"conversation API missing snippet: {snippet}")

    require(
        "require_current_principal" not in conversations_api,
        "conversation API should use named permissions instead of bare current principal",
    )

    for snippet in [
        "test_conversation_permissions_allow_agent_and_block_viewer",
        "test_conversation_read_and_write_endpoints_require_named_permissions",
        "test_conversation_permission_keeps_cross_tenant_resources_hidden",
        "conversation.read",
        "conversation.manage",
        "insufficient permission",
        "status_code == 401",
        "status_code == 404",
    ]:
        require(snippet in test, f"P3-06K test missing snippet: {snippet}")

    for phrase in [
        "P3-06K RBAC 第四片",
        "会话业务动作权限",
        "conversation.read",
        "conversation.manage",
        "官方平台 webhook 入口不套坐席 bearer token",
        "viewer 仍不能看会话原文",
        "不改数据库结构",
    ]:
        require(phrase in doc, f"P3-06K documentation missing phrase: {phrase}")

    print("P3-06K conversation RBAC checks passed.")


if __name__ == "__main__":
    main()
