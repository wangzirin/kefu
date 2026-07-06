#!/usr/bin/env python3
"""Static readiness checks for P3-06M customer-ops RBAC migration."""

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
    tickets_api = read_text("backend/app/api/support_tickets.py")
    customers_api = read_text("backend/app/api/customer_profiles.py")
    test = read_text("backend/tests/test_p3_06m_customer_ops_rbac.py")
    doc = read_text("docs/P3-06M_CUSTOMER_OPS_RBAC.md")

    for permission in [
        '"ticket.read"',
        '"ticket.manage"',
        '"customer.read"',
        '"lead.read"',
        '"lead.manage"',
    ]:
        require(permission in rbac, f"RBAC matrix missing {permission}")

    owner_block = rbac.split('"owner":', 1)[1].split('"admin":', 1)[0]
    admin_block = rbac.split('"admin":', 1)[1].split('"agent":', 1)[0]
    agent_block = rbac.split('"agent":', 1)[1].split('"viewer":', 1)[0]
    viewer_block = rbac.split('"viewer":', 1)[1].split("}", 1)[0]
    for block_name, block in [("owner", owner_block), ("admin", admin_block), ("agent", agent_block)]:
        for permission in [
            '"ticket.read"',
            '"ticket.manage"',
            '"customer.read"',
            '"lead.read"',
            '"lead.manage"',
        ]:
            require(permission in block, f"{block_name} should have {permission}")
    for permission in ['"ticket.read"', '"ticket.manage"', '"customer.read"', '"lead.read"', '"lead.manage"']:
        require(permission not in viewer_block, f"viewer should not have {permission}")

    for snippet in [
        'TICKET_READ_PERMISSION = "ticket.read"',
        'TICKET_MANAGE_PERMISSION = "ticket.manage"',
        "require_permission(TICKET_READ_PERMISSION)",
        "require_permission(TICKET_MANAGE_PERMISSION)",
    ]:
        require(snippet in tickets_api, f"support tickets API missing snippet: {snippet}")
    require(
        "require_current_principal" not in tickets_api,
        "support tickets API should use named permissions instead of bare current principal",
    )

    for snippet in [
        'CUSTOMER_READ_PERMISSION = "customer.read"',
        'LEAD_READ_PERMISSION = "lead.read"',
        'LEAD_MANAGE_PERMISSION = "lead.manage"',
        "require_permission(CUSTOMER_READ_PERMISSION)",
        "require_permission(LEAD_READ_PERMISSION)",
        "require_permission(LEAD_MANAGE_PERMISSION)",
    ]:
        require(snippet in customers_api, f"customer profiles API missing snippet: {snippet}")
    require(
        "require_current_principal" not in customers_api,
        "customer profiles API should use named permissions instead of bare current principal",
    )

    for snippet in [
        "test_customer_ops_permissions_matrix",
        "test_agent_can_manage_customer_ops_and_viewer_is_blocked",
        "test_customer_ops_permissions_keep_cross_tenant_resources_hidden",
        "insufficient permission",
        "status_code == 401",
        "status_code == 404",
        "138****8888",
    ]:
        require(snippet in test, f"P3-06M test missing snippet: {snippet}")

    for phrase in [
        "P3-06M RBAC 第六片",
        "工单、客户画像与线索权限",
        "ticket.read",
        "ticket.manage",
        "customer.read",
        "lead.read",
        "lead.manage",
        "viewer 暂不开放客户画像",
        "为什么渠道配置后置",
    ]:
        require(phrase in doc, f"P3-06M documentation missing phrase: {phrase}")

    print("P3-06M customer-ops RBAC checks passed.")


if __name__ == "__main__":
    main()
