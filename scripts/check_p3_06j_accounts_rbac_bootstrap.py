#!/usr/bin/env python3
"""Static readiness checks for P3-06J account RBAC and bootstrap protection."""

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
    accounts_api = read_text("backend/app/api/accounts.py")
    test = read_text("backend/tests/test_p3_06j_accounts_rbac_bootstrap.py")
    doc = read_text("docs/P3-06J_ACCOUNTS_RBAC_BOOTSTRAP.md")

    require('"accounts.manage"' in rbac, "RBAC matrix missing accounts.manage")
    owner_block = rbac.split('"owner":', 1)[1].split('"admin":', 1)[0]
    admin_block = rbac.split('"admin":', 1)[1].split('"agent":', 1)[0]
    require('"accounts.manage"' in owner_block, "owner should have accounts.manage")
    require('"accounts.manage"' not in admin_block, "admin should not have accounts.manage in P3-06J")

    for snippet in [
        "ACCOUNTS_MANAGE_PERMISSION = \"accounts.manage\"",
        "principal_has_permission(principal, ACCOUNTS_MANAGE_PERMISSION)",
        'detail="insufficient permission"',
        "_tenant_has_users",
        "_tenant_has_roles",
        "_tenant_has_user_roles",
    ]:
        require(snippet in accounts_api, f"accounts API missing snippet: {snippet}")

    require(
        "owner or admin role required" not in accounts_api,
        "accounts API should no longer use owner/admin role error",
    )

    for snippet in [
        "test_accounts_manage_permission_is_owner_only",
        "test_accounts_bootstrap_allows_first_role_user_and_assignment_without_token",
        "test_accounts_manage_permission_blocks_no_token_and_admin_after_bootstrap",
        "test_accounts_manage_permission_allows_owner_to_manage_team_members",
        "insufficient permission",
    ]:
        require(snippet in test, f"P3-06J test missing snippet: {snippet}")

    for phrase in [
        "P3-06J RBAC 第三片",
        "accounts.manage",
        "Bootstrap 保护",
        "owner-only",
        "一次性安装 token",
        "不新增数据库迁移",
    ]:
        require(phrase in doc, f"P3-06J documentation missing phrase: {phrase}")

    print("P3-06J account RBAC bootstrap checks passed.")


if __name__ == "__main__":
    main()
