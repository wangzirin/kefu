from app.core.rbac import allowed_roles_for_permission, permissions_for_roles
from test_channel_connectors_api import _bootstrap_owner, _create_connector, _ready_outbox_draft
from test_p3_06m_customer_ops_rbac import _create_user_with_role


def _auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_channel_delivery_permissions_matrix() -> None:
    assert allowed_roles_for_permission("channel.read") == ("admin", "agent", "owner", "viewer")
    assert allowed_roles_for_permission("channel.connector.manage") == ("admin", "owner")
    assert allowed_roles_for_permission("channel.delivery_receipt.read") == ("admin", "agent", "owner")
    assert allowed_roles_for_permission("channel.delivery_receipt.manage") == ("admin", "owner")
    assert allowed_roles_for_permission("outbox.send_plan.manage") == ("admin", "agent", "owner")

    agent_permissions = permissions_for_roles(["agent"])
    assert "channel.read" in agent_permissions
    assert "channel.delivery_receipt.read" in agent_permissions
    assert "outbox.send_plan.manage" in agent_permissions
    assert "channel.connector.manage" not in agent_permissions
    assert "channel.delivery_receipt.manage" not in agent_permissions

    viewer_permissions = permissions_for_roles(["viewer"])
    assert "channel.read" in viewer_permissions
    assert "channel.delivery_receipt.read" not in viewer_permissions
    assert "outbox.send_plan.manage" not in viewer_permissions


def test_connector_config_receipt_and_send_plan_permissions(client) -> None:
    tenant, owner_token = _bootstrap_owner(
        client,
        slug="p3-06n-channel-delivery",
        email="p3-06n-owner@example.com",
    )
    owner_headers = _auth_header(owner_token)
    _agent, agent_headers = _create_user_with_role(
        client,
        tenant=tenant,
        owner_headers=owner_headers,
        role_code="agent",
        email="p3-06n-agent@example.com",
    )
    _viewer, viewer_headers = _create_user_with_role(
        client,
        tenant=tenant,
        owner_headers=owner_headers,
        role_code="viewer",
        email="p3-06n-viewer@example.com",
    )
    channel, ready = _ready_outbox_draft(client, tenant["id"], owner_headers)

    no_token_registry = client.get("/api/channel-providers")
    viewer_registry = client.get("/api/channel-providers", headers=viewer_headers)
    assert no_token_registry.status_code == 401
    assert viewer_registry.status_code == 200

    agent_config = client.post(
        f"/api/channels/{channel['id']}/connector-config",
        headers=agent_headers,
        json={
            "provider": "wecom",
            "mode": "noop",
            "status": "ready",
            "display_name": "坐席不能配置的连接器",
            "public_config": {"credential_ref": "agent_should_not_manage_secrets"},
            "webhook_path": f"/api/webhooks/wecom/channels/{channel['id']}",
            "signature_mode": "wecom_token_aeskey",
        },
    )
    assert agent_config.status_code == 403
    assert agent_config.json()["detail"] == "insufficient permission"

    connector = _create_connector(
        client,
        channel["id"],
        owner_headers,
        public_config={"credential_ref": "p3_06n_placeholder_secret"},
    )
    assert connector["external_write_enabled"] is False

    agent_get = client.get(f"/api/channels/{channel['id']}/connector-config", headers=agent_headers)
    viewer_get = client.get(f"/api/channels/{channel['id']}/connector-config", headers=viewer_headers)
    assert agent_get.status_code == 200
    assert viewer_get.status_code == 200
    assert viewer_get.json()["public_config"]["credential_ref"] == "p3_06n_placeholder_secret"

    viewer_receipts = client.get(f"/api/channels/{channel['id']}/delivery-receipts", headers=viewer_headers)
    assert viewer_receipts.status_code == 403
    assert viewer_receipts.json()["detail"] == "insufficient permission"

    agent_manual_receipt = client.post(
        f"/api/channels/{channel['id']}/delivery-receipts",
        headers=agent_headers,
        json={
            "provider": "wecom",
            "external_message_id": "p3-06n-agent-forbidden",
            "delivery_status": "delivered",
            "raw_payload": {"MsgID": "p3-06n-agent-forbidden", "Status": "delivered"},
        },
    )
    assert agent_manual_receipt.status_code == 403
    assert agent_manual_receipt.json()["detail"] == "insufficient permission"

    owner_receipt = client.post(
        f"/api/channels/{channel['id']}/delivery-receipts",
        headers=owner_headers,
        json={
            "provider": "wecom",
            "external_message_id": "p3-06n-owner-receipt",
            "delivery_status": "delivered",
            "raw_payload": {"MsgID": "p3-06n-owner-receipt", "Status": "delivered"},
        },
    )
    assert owner_receipt.status_code == 201

    agent_receipts = client.get(f"/api/channels/{channel['id']}/delivery-receipts", headers=agent_headers)
    assert agent_receipts.status_code == 200
    assert [item["id"] for item in agent_receipts.json()] == [owner_receipt.json()["id"]]

    agent_plan = client.post(
        f"/api/outbox-drafts/{ready['id']}/connector-send-plans",
        headers=agent_headers,
        json={"operator_note": "坐席可生成官方发送前的安全计划"},
    )
    assert agent_plan.status_code == 201
    assert agent_plan.json()["external_message_id"] == ""
    assert agent_plan.json()["response_payload"]["external_write"] is False

    viewer_plan = client.post(
        f"/api/outbox-drafts/{ready['id']}/connector-send-plans",
        headers=viewer_headers,
        json={"operator_note": "查看角色不能生成发送计划"},
    )
    assert viewer_plan.status_code == 403
    assert viewer_plan.json()["detail"] == "insufficient permission"
