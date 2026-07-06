#!/usr/bin/env python3
"""Static readiness checks for P3-06N channel delivery RBAC migration."""

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
    api = read_text("backend/app/api/channel_connectors.py")
    test = read_text("backend/tests/test_p3_06n_channel_delivery_rbac.py")
    doc = read_text("docs/P3-06N_CHANNEL_DELIVERY_RBAC.md")

    for permission in [
        '"channel.read"',
        '"channel.connector.manage"',
        '"channel.delivery_receipt.read"',
        '"channel.delivery_receipt.manage"',
        '"outbox.send_plan.manage"',
    ]:
        require(permission in rbac, f"RBAC matrix missing {permission}")

    owner_block = rbac.split('"owner":', 1)[1].split('"admin":', 1)[0]
    admin_block = rbac.split('"admin":', 1)[1].split('"agent":', 1)[0]
    agent_block = rbac.split('"agent":', 1)[1].split('"viewer":', 1)[0]
    viewer_block = rbac.split('"viewer":', 1)[1].split("}", 1)[0]

    for block_name, block in [("owner", owner_block), ("admin", admin_block)]:
        for permission in [
            '"channel.read"',
            '"channel.connector.manage"',
            '"channel.delivery_receipt.read"',
            '"channel.delivery_receipt.manage"',
            '"outbox.send_plan.manage"',
        ]:
            require(permission in block, f"{block_name} should have {permission}")

    for permission in ['"channel.read"', '"channel.delivery_receipt.read"', '"outbox.send_plan.manage"']:
        require(permission in agent_block, f"agent should have {permission}")
    for permission in ['"channel.connector.manage"', '"channel.delivery_receipt.manage"']:
        require(permission not in agent_block, f"agent should not have {permission}")

    require('"channel.read"' in viewer_block, "viewer should keep channel.read")
    for permission in [
        '"channel.connector.manage"',
        '"channel.delivery_receipt.read"',
        '"channel.delivery_receipt.manage"',
        '"outbox.send_plan.manage"',
    ]:
        require(permission not in viewer_block, f"viewer should not have {permission}")

    for snippet in [
        'CHANNEL_READ_PERMISSION = "channel.read"',
        'CHANNEL_CONNECTOR_MANAGE_PERMISSION = "channel.connector.manage"',
        'CHANNEL_DELIVERY_RECEIPT_READ_PERMISSION = "channel.delivery_receipt.read"',
        'CHANNEL_DELIVERY_RECEIPT_MANAGE_PERMISSION = "channel.delivery_receipt.manage"',
        'OUTBOX_SEND_PLAN_MANAGE_PERMISSION = "outbox.send_plan.manage"',
        "require_permission(CHANNEL_READ_PERMISSION)",
        "require_permission(CHANNEL_CONNECTOR_MANAGE_PERMISSION)",
        "require_permission(CHANNEL_DELIVERY_RECEIPT_READ_PERMISSION)",
        "require_permission(CHANNEL_DELIVERY_RECEIPT_MANAGE_PERMISSION)",
        "require_permission(OUTBOX_SEND_PLAN_MANAGE_PERMISSION)",
    ]:
        require(snippet in api, f"channel connectors API missing snippet: {snippet}")
    require(
        "require_current_principal" not in api,
        "channel connectors API should use named permissions or unsigned official webhooks",
    )

    for webhook_name in [
        "receive_wecom_official_xml_channel_webhook",
        "verify_wecom_official_callback_url",
        "receive_official_channel_webhook",
    ]:
        function_block = api.split(f"def {webhook_name}", 1)
        if len(function_block) == 1:
            function_block = api.split(f"async def {webhook_name}", 1)
        require(len(function_block) == 2, f"missing official webhook endpoint {webhook_name}")
        signature_block = function_block[1].split(") ->", 1)[0]
        require("CurrentPrincipal" not in signature_block, f"{webhook_name} should not require bearer principal")
        require("require_permission" not in signature_block, f"{webhook_name} should not use staff RBAC dependency")

    for snippet in [
        "test_channel_delivery_permissions_matrix",
        "test_connector_config_receipt_and_send_plan_permissions",
        "status_code == 401",
        "status_code == 403",
        "insufficient permission",
        "agent_plan.status_code == 201",
        "viewer_plan.status_code == 403",
    ]:
        require(snippet in test, f"P3-06N test missing snippet: {snippet}")

    for phrase in [
        "P3-06N RBAC 第七片",
        "渠道连接器、回执与发送计划权限",
        "channel.connector.manage",
        "channel.delivery_receipt.read",
        "channel.delivery_receipt.manage",
        "outbox.send_plan.manage",
        "官方 webhook 为什么不加普通 RBAC",
        "Secret 引用边界",
    ]:
        require(phrase in doc, f"P3-06N documentation missing phrase: {phrase}")

    print("P3-06N channel delivery RBAC checks passed.")


if __name__ == "__main__":
    main()
