#!/usr/bin/env python3
"""Static readiness checks for P3-06I RBAC permission snapshot and audit migration."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_text(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    auth_schema = read_text("backend/app/schemas/auth.py")
    auth_api = read_text("backend/app/api/auth.py")
    audit_api = read_text("backend/app/api/audit.py")
    frontend_client = read_text("frontend/src/api/client.ts")
    test = read_text("backend/tests/test_p3_06i_rbac_permission_snapshot.py")
    doc = read_text("docs/P3-06I_RBAC_PERMISSION_SNAPSHOT_AND_AUDIT.md")

    for snippet in [
        "permissions: List[str]",
        "Field(default_factory=list)",
    ]:
        require(snippet in auth_schema, f"auth schema missing snippet: {snippet}")

    for snippet in [
        "permissions_for_roles",
        "permissions=sorted(permissions_for_roles(principal.roles))",
        'permissions=sorted(permissions_for_roles(["owner"]))',
    ]:
        require(snippet in auth_api, f"auth API missing permission snapshot snippet: {snippet}")

    require(
        'require_permission("audit.events.read")' in audit_api,
        "audit API should use audit.events.read named permission",
    )
    require(
        'require_any_role("owner", "admin")' not in audit_api,
        "audit API should not use scattered owner/admin role check after P3-06I",
    )
    require("permissions: string[]" in frontend_client, "frontend CurrentUser type missing permissions")

    for snippet in [
        "test_login_and_me_return_permission_snapshot_for_owner",
        "test_audit_events_use_named_permission_for_admin_and_agent",
        "accounts.manage",
        "audit.events.read",
        "insufficient permission",
    ]:
        require(snippet in test, f"P3-06I test missing snippet: {snippet}")

    for phrase in [
        "P3-06I RBAC 第二片",
        "权限快照",
        "audit.events.read",
        "不改账号初始化流程",
        "bootstrap",
        "下一片迁到 `accounts.manage`",
    ]:
        require(phrase in doc, f"P3-06I documentation missing phrase: {phrase}")

    print("P3-06I RBAC permission snapshot checks passed.")


if __name__ == "__main__":
    main()
