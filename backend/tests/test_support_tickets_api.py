from datetime import timedelta

from sqlalchemy.orm import Session

from app.models import AuditEvent, Channel, Contact, Conversation, ConversationEvent, Message, SupportTicket
from app.models.foundation import utc_now
from test_knowledge_api import _bootstrap_user


def _auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _seed_conversation(
    db_session: Session,
    *,
    tenant_id: int,
    channel_type: str = "wecom",
    channel_name: str = "企业微信测试客服",
    contact_name: str = "周先生",
    subject: str = "标准运营版部署咨询",
    priority: str = "high",
    message: str = "我们想接入企业微信客服，并确认 SLA 和人工接管方式。",
) -> Conversation:
    channel = Channel(
        tenant_id=tenant_id,
        type=channel_type,
        name=channel_name,
        reply_mode="assist",
        status="active",
    )
    contact = Contact(tenant_id=tenant_id, display_name=contact_name, wechat="wx-support-ticket-test")
    db_session.add_all([channel, contact])
    db_session.flush()
    conversation = Conversation(
        tenant_id=tenant_id,
        channel_id=channel.id,
        contact_id=contact.id,
        status="handoff",
        priority=priority,
        subject=subject,
        last_message_at=utc_now() - timedelta(minutes=20),
    )
    db_session.add(conversation)
    db_session.flush()
    db_session.add(
        Message(
            conversation_id=conversation.id,
            direction="inbound",
            sender_type="customer",
            content=message,
            external_message_id=f"support-ticket-msg-{conversation.id}",
        )
    )
    db_session.commit()
    db_session.refresh(conversation)
    return conversation


def test_owner_can_create_list_and_resolve_support_ticket_from_conversation(client, db_session: Session) -> None:
    tenant, user, token = _bootstrap_user(
        client,
        slug="support-ticket-owner",
        email="support-ticket-owner@example.com",
    )
    headers = _auth_header(token)
    conversation = _seed_conversation(db_session, tenant_id=tenant["id"])

    no_token = client.post(
        f"/api/conversations/{conversation.id}/support-tickets",
        json={"priority": "high"},
    )
    assert no_token.status_code == 401

    create_res = client.post(
        f"/api/conversations/{conversation.id}/support-tickets",
        headers=headers,
        json={
            "subject": "标准运营版部署与 SLA 跟进",
            "description": "客户希望确认部署方式和服务响应边界。",
            "priority": "high",
            "sla_target_minutes": 60,
            "assigned_user_id": user["id"],
        },
    )
    assert create_res.status_code == 201
    created = create_res.json()
    assert created["tenant_id"] == tenant["id"]
    assert created["conversation_id"] == conversation.id
    assert created["channel_id"] == conversation.channel_id
    assert created["contact_id"] == conversation.contact_id
    assert created["status"] == "open"
    assert created["priority"] == "high"
    assert created["assigned_user_id"] == user["id"]
    assert created["sla_target_minutes"] == 60
    assert created["sla_status"] == "ok"
    assert created["source_type"] == "conversation"
    assert created["source_ref"] == f"conversation:{conversation.id}"
    assert created["sla_due_at"] is not None

    ticket_model = db_session.get(SupportTicket, created["id"])
    assert ticket_model is not None
    ticket_model.sla_due_at = utc_now() - timedelta(minutes=1)
    db_session.commit()

    breached_res = client.get(
        f"/api/tenants/{tenant['id']}/support-tickets?sla=breached&page=1&page_size=10",
        headers=headers,
    )
    assert breached_res.status_code == 200
    breached_page = breached_res.json()
    assert breached_page["total"] == 1
    assert breached_page["items"][0]["id"] == created["id"]
    assert breached_page["items"][0]["sla_status"] == "breached"

    duplicate_res = client.post(
        f"/api/conversations/{conversation.id}/support-tickets",
        headers=headers,
        json={"priority": "urgent"},
    )
    assert duplicate_res.status_code == 200
    assert duplicate_res.json()["id"] == created["id"]
    assert duplicate_res.json()["priority"] == "high"

    list_res = client.get(
        f"/api/tenants/{tenant['id']}/support-tickets?status=open&page=1&page_size=10",
        headers=headers,
    )
    assert list_res.status_code == 200
    page = list_res.json()
    assert page["page"] == 1
    assert page["page_size"] == 10
    assert page["total"] == 1
    assert page["items"][0]["id"] == created["id"]
    assert page["items"][0]["contact_display_name"] == "周先生"
    assert page["items"][0]["channel_name"] == "企业微信测试客服"

    update_res = client.patch(
        f"/api/support-tickets/{created['id']}",
        headers=headers,
        json={
            "status": "in_progress",
            "priority": "urgent",
            "resolution_note": "已安排实施顾问跟进。",
        },
    )
    assert update_res.status_code == 200
    updated = update_res.json()
    assert updated["status"] == "in_progress"
    assert updated["priority"] == "urgent"
    assert updated["resolution_note"] == "已安排实施顾问跟进。"

    resolved_res = client.patch(
        f"/api/support-tickets/{created['id']}",
        headers=headers,
        json={"status": "resolved", "resolution_note": "已确认部署范围并转入交付排期。"},
    )
    assert resolved_res.status_code == 200
    resolved = resolved_res.json()
    assert resolved["status"] == "resolved"
    assert resolved["sla_status"] == "completed"
    assert resolved["resolved_by_id"] == user["id"]
    assert resolved["resolved_at"] is not None

    reopen_without_action = client.patch(
        f"/api/support-tickets/{created['id']}",
        headers=headers,
        json={"status": "in_progress"},
    )
    assert reopen_without_action.status_code == 409

    audit_actions = [event.action for event in db_session.query(AuditEvent).all()]
    assert "support_ticket.created" in audit_actions
    assert "support_ticket.updated" in audit_actions
    event_actions = [event.event_type for event in db_session.query(ConversationEvent).all()]
    assert "support_ticket.created" in event_actions
    assert "support_ticket.updated" in event_actions


def test_support_ticket_tenant_boundary_and_agent_assignment_rules(client, db_session: Session) -> None:
    tenant, owner, owner_token = _bootstrap_user(
        client,
        slug="support-ticket-agent",
        email="support-ticket-agent-owner@example.com",
    )
    other_tenant, _, other_token = _bootstrap_user(
        client,
        slug="support-ticket-other",
        email="support-ticket-other-owner@example.com",
    )
    owner_headers = _auth_header(owner_token)
    other_headers = _auth_header(other_token)

    agent_role = client.post(
        f"/api/tenants/{tenant['id']}/roles",
        headers=owner_headers,
        json={"code": "agent", "name": "客服坐席"},
    ).json()
    agent_res = client.post(
        f"/api/tenants/{tenant['id']}/users",
        headers=owner_headers,
        json={"name": "一线坐席", "email": "support-ticket-agent@example.com", "password": "ChangeMe123!"},
    )
    assert agent_res.status_code == 201
    agent = agent_res.json()
    assign_res = client.post(
        f"/api/users/{agent['id']}/roles",
        headers=owner_headers,
        json={"role_id": agent_role["id"]},
    )
    assert assign_res.status_code == 201
    login_res = client.post(
        "/api/auth/login",
        json={
            "tenant_slug": tenant["slug"],
            "email": "support-ticket-agent@example.com",
            "password": "ChangeMe123!",
        },
    )
    assert login_res.status_code == 200
    agent_headers = _auth_header(login_res.json()["access_token"])

    conversation = _seed_conversation(
        db_session,
        tenant_id=tenant["id"],
        subject="需要客服坐席接手",
        priority="normal",
    )
    ticket_res = client.post(
        f"/api/conversations/{conversation.id}/support-tickets",
        headers=agent_headers,
        json={"priority": "normal"},
    )
    assert ticket_res.status_code == 201
    ticket = ticket_res.json()
    assert ticket["assigned_user_id"] == agent["id"]

    assign_to_owner = client.patch(
        f"/api/support-tickets/{ticket['id']}",
        headers=agent_headers,
        json={"assigned_user_id": owner["id"]},
    )
    assert assign_to_owner.status_code == 403

    wait_customer = client.patch(
        f"/api/support-tickets/{ticket['id']}",
        headers=agent_headers,
        json={"status": "pending_customer", "resolution_note": "已向客户补问订单号。"},
    )
    assert wait_customer.status_code == 200
    assert wait_customer.json()["status"] == "pending_customer"

    cross_tenant_list = client.get(
        f"/api/tenants/{other_tenant['id']}/support-tickets",
        headers=agent_headers,
    )
    assert cross_tenant_list.status_code == 404

    cross_tenant_patch = client.patch(
        f"/api/support-tickets/{ticket['id']}",
        headers=other_headers,
        json={"status": "resolved"},
    )
    assert cross_tenant_patch.status_code == 404
