from datetime import timedelta

from sqlalchemy.orm import Session

from app.core.rbac import allowed_roles_for_permission, permissions_for_roles
from app.models import Channel, Contact, Conversation, Message
from app.models.foundation import utc_now
from test_knowledge_api import _bootstrap_user


def _auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _create_user_with_role(
    client,
    *,
    tenant: dict,
    owner_headers: dict,
    role_code: str,
    email: str,
) -> tuple[dict, dict]:
    role_res = client.post(
        f"/api/tenants/{tenant['id']}/roles",
        headers=owner_headers,
        json={"code": role_code, "name": role_code},
    )
    assert role_res.status_code == 201
    role = role_res.json()

    user_res = client.post(
        f"/api/tenants/{tenant['id']}/users",
        headers=owner_headers,
        json={"name": role_code, "email": email, "password": "ChangeMe123!"},
    )
    assert user_res.status_code == 201
    user = user_res.json()

    assign_res = client.post(
        f"/api/users/{user['id']}/roles",
        headers=owner_headers,
        json={"role_id": role["id"]},
    )
    assert assign_res.status_code == 201

    login_res = client.post(
        "/api/auth/login",
        json={"tenant_slug": tenant["slug"], "email": email, "password": "ChangeMe123!"},
    )
    assert login_res.status_code == 200
    return user, _auth_header(login_res.json()["access_token"])


def _seed_customer_conversation(
    db_session: Session,
    *,
    tenant_id: int,
    suffix: str,
    contact_name: str = "权限测试客户",
) -> Conversation:
    channel = Channel(
        tenant_id=tenant_id,
        type="wecom",
        name=f"企业微信客服-{suffix}",
        reply_mode="assist",
        status="active",
    )
    contact = Contact(
        tenant_id=tenant_id,
        display_name=contact_name,
        phone="13800138888",
        wechat=f"wx_customer_{suffix}",
    )
    db_session.add_all([channel, contact])
    db_session.flush()
    conversation = Conversation(
        tenant_id=tenant_id,
        channel_id=channel.id,
        contact_id=contact.id,
        status="handoff",
        priority="high",
        subject=f"标准运营版权限收口-{suffix}",
        last_message_at=utc_now() - timedelta(minutes=10),
    )
    db_session.add(conversation)
    db_session.flush()
    db_session.add(
        Message(
            conversation_id=conversation.id,
            direction="inbound",
            sender_type="customer",
            content="我们想试点企业微信客服，并确认工单、线索和人工接管方式。",
            external_message_id=f"p3-06m-msg-{suffix}",
            created_at=utc_now() - timedelta(minutes=10),
        )
    )
    db_session.commit()
    db_session.refresh(conversation)
    return conversation


def test_customer_ops_permissions_matrix() -> None:
    expected = ("admin", "agent", "owner")
    assert allowed_roles_for_permission("ticket.read") == expected
    assert allowed_roles_for_permission("ticket.manage") == expected
    assert allowed_roles_for_permission("customer.read") == expected
    assert allowed_roles_for_permission("lead.read") == expected
    assert allowed_roles_for_permission("lead.manage") == expected

    agent_permissions = permissions_for_roles(["agent"])
    assert {"ticket.read", "ticket.manage", "customer.read", "lead.read", "lead.manage"}.issubset(
        agent_permissions
    )
    viewer_permissions = permissions_for_roles(["viewer"])
    assert "ticket.read" not in viewer_permissions
    assert "customer.read" not in viewer_permissions
    assert "lead.read" not in viewer_permissions


def test_agent_can_manage_customer_ops_and_viewer_is_blocked(client, db_session: Session) -> None:
    tenant, _owner, owner_token = _bootstrap_user(
        client,
        slug="p3-06m-customer-ops",
        email="p3-06m-owner@example.com",
    )
    owner_headers = _auth_header(owner_token)
    agent, agent_headers = _create_user_with_role(
        client,
        tenant=tenant,
        owner_headers=owner_headers,
        role_code="agent",
        email="p3-06m-agent@example.com",
    )
    _viewer, viewer_headers = _create_user_with_role(
        client,
        tenant=tenant,
        owner_headers=owner_headers,
        role_code="viewer",
        email="p3-06m-viewer@example.com",
    )
    conversation = _seed_customer_conversation(db_session, tenant_id=tenant["id"], suffix="agent")

    no_token_ticket_list = client.get(f"/api/tenants/{tenant['id']}/support-tickets")
    assert no_token_ticket_list.status_code == 401

    viewer_ticket_list = client.get(f"/api/tenants/{tenant['id']}/support-tickets", headers=viewer_headers)
    viewer_ticket_create = client.post(
        f"/api/conversations/{conversation.id}/support-tickets",
        headers=viewer_headers,
        json={"priority": "high"},
    )
    viewer_profile_list = client.get(f"/api/tenants/{tenant['id']}/contact-profiles", headers=viewer_headers)
    viewer_lead_list = client.get(f"/api/tenants/{tenant['id']}/leads", headers=viewer_headers)
    viewer_lead_create = client.post(
        f"/api/conversations/{conversation.id}/leads",
        headers=viewer_headers,
        json={"intent_level": "hot"},
    )

    for response in (
        viewer_ticket_list,
        viewer_ticket_create,
        viewer_profile_list,
        viewer_lead_list,
        viewer_lead_create,
    ):
        assert response.status_code == 403
        assert response.json()["detail"] == "insufficient permission"

    ticket_create = client.post(
        f"/api/conversations/{conversation.id}/support-tickets",
        headers=agent_headers,
        json={"priority": "high", "description": "客户咨询试点和人工接管。"},
    )
    assert ticket_create.status_code == 201
    ticket = ticket_create.json()
    assert ticket["assigned_user_id"] == agent["id"]

    ticket_update = client.patch(
        f"/api/support-tickets/{ticket['id']}",
        headers=agent_headers,
        json={"status": "pending_customer", "resolution_note": "已向客户补问试点入口。"},
    )
    assert ticket_update.status_code == 200
    assert ticket_update.json()["status"] == "pending_customer"

    lead_create = client.post(
        f"/api/conversations/{conversation.id}/leads",
        headers=agent_headers,
        json={"intent_level": "hot", "expected_budget": "6-8 万", "next_step": "约演示"},
    )
    assert lead_create.status_code == 201
    lead = lead_create.json()
    assert lead["owner_user_id"] == agent["id"]

    lead_update = client.patch(
        f"/api/leads/{lead['id']}",
        headers=agent_headers,
        json={"stage": "proposal", "next_step": "准备试点报价"},
    )
    assert lead_update.status_code == 200
    assert lead_update.json()["stage"] == "proposal"

    profile_detail = client.get(f"/api/contact-profiles/{conversation.contact_id}", headers=agent_headers)
    assert profile_detail.status_code == 200
    profile = profile_detail.json()
    assert profile["phone"] == "138****8888"
    assert profile["open_tickets"][0]["id"] == ticket["id"]
    assert profile["open_leads"][0]["id"] == lead["id"]

    owner_ticket_list = client.get(f"/api/tenants/{tenant['id']}/support-tickets", headers=owner_headers)
    owner_lead_list = client.get(f"/api/tenants/{tenant['id']}/leads", headers=owner_headers)
    assert owner_ticket_list.status_code == 200
    assert owner_ticket_list.json()["total"] == 1
    assert owner_lead_list.status_code == 200
    assert owner_lead_list.json()["total"] == 1


def test_customer_ops_permissions_keep_cross_tenant_resources_hidden(client, db_session: Session) -> None:
    first_tenant, _first_owner, first_token = _bootstrap_user(
        client,
        slug="p3-06m-first",
        email="p3-06m-first-owner@example.com",
    )
    second_tenant, _second_owner, second_token = _bootstrap_user(
        client,
        slug="p3-06m-second",
        email="p3-06m-second-owner@example.com",
    )
    first_headers = _auth_header(first_token)
    second_headers = _auth_header(second_token)
    second_conversation = _seed_customer_conversation(
        db_session,
        tenant_id=second_tenant["id"],
        suffix="second",
        contact_name="第二租户客户",
    )

    ticket_res = client.post(
        f"/api/conversations/{second_conversation.id}/support-tickets",
        headers=second_headers,
        json={"priority": "normal"},
    )
    assert ticket_res.status_code == 201
    lead_res = client.post(
        f"/api/conversations/{second_conversation.id}/leads",
        headers=second_headers,
        json={"intent_level": "warm"},
    )
    assert lead_res.status_code == 201

    cross_ticket_list = client.get(
        f"/api/tenants/{second_tenant['id']}/support-tickets",
        headers=first_headers,
    )
    cross_ticket_patch = client.patch(
        f"/api/support-tickets/{ticket_res.json()['id']}",
        headers=first_headers,
        json={"status": "in_progress"},
    )
    cross_profile_detail = client.get(f"/api/contact-profiles/{second_conversation.contact_id}", headers=first_headers)
    cross_lead_list = client.get(f"/api/tenants/{second_tenant['id']}/leads", headers=first_headers)
    cross_lead_patch = client.patch(
        f"/api/leads/{lead_res.json()['id']}",
        headers=first_headers,
        json={"stage": "lost"},
    )

    assert cross_ticket_list.status_code == 404
    assert cross_ticket_patch.status_code == 404
    assert cross_profile_detail.status_code == 404
    assert cross_lead_list.status_code == 404
    assert cross_lead_patch.status_code == 404
