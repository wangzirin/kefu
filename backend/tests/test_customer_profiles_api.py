from datetime import timedelta

from sqlalchemy.orm import Session

from app.models import AuditEvent, Channel, Contact, Conversation, Message, SupportTicket
from app.models.foundation import utc_now
from test_knowledge_api import _bootstrap_user


def _auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _seed_contact_conversation(
    db_session: Session,
    *,
    tenant_id: int,
    channel_type: str = "wecom",
    channel_name: str = "企业微信客服",
    contact_name: str = "林女士",
    phone: str = "13800138888",
    wechat: str = "wx_lady_lin",
    subject: str = "标准运营版试点咨询",
    message: str = "我们想先试点企业微信客服，再看标准运营版报价。",
    priority: str = "high",
    minutes_old: int = 25,
) -> Conversation:
    channel = Channel(
        tenant_id=tenant_id,
        type=channel_type,
        name=channel_name,
        reply_mode="assist",
        status="active",
    )
    contact = Contact(tenant_id=tenant_id, display_name=contact_name, phone=phone, wechat=wechat)
    db_session.add_all([channel, contact])
    db_session.flush()
    conversation = Conversation(
        tenant_id=tenant_id,
        channel_id=channel.id,
        contact_id=contact.id,
        status="handoff",
        priority=priority,
        subject=subject,
        last_message_at=utc_now() - timedelta(minutes=minutes_old),
    )
    db_session.add(conversation)
    db_session.flush()
    db_session.add(
        Message(
            conversation_id=conversation.id,
            direction="inbound",
            sender_type="customer",
            content=message,
            external_message_id=f"profile-msg-{conversation.id}",
            created_at=utc_now() - timedelta(minutes=minutes_old),
        )
    )
    db_session.commit()
    db_session.refresh(conversation)
    return conversation


def test_contact_profiles_aggregate_activity_and_mask_agent_sensitive_fields(client, db_session: Session) -> None:
    tenant, owner, owner_token = _bootstrap_user(
        client,
        slug="customer-profile-owner",
        email="customer-profile-owner@example.com",
    )
    owner_headers = _auth_header(owner_token)
    conversation = _seed_contact_conversation(db_session, tenant_id=tenant["id"])
    db_session.add(
        SupportTicket(
            tenant_id=tenant["id"],
            conversation_id=conversation.id,
            channel_id=conversation.channel_id,
            contact_id=conversation.contact_id,
            subject="部署试点跟进",
            description="需要确认试点范围。",
            status="open",
            priority="high",
            source_type="conversation",
            source_ref=f"conversation:{conversation.id}",
            sla_target_minutes=60,
            sla_due_at=utc_now() + timedelta(minutes=60),
            created_by_id=owner["id"],
            updated_by_id=owner["id"],
        )
    )
    db_session.commit()

    no_token = client.get(f"/api/tenants/{tenant['id']}/contact-profiles")
    assert no_token.status_code == 401

    create_lead = client.post(
        f"/api/conversations/{conversation.id}/leads",
        headers=owner_headers,
        json={
            "title": "标准运营版试点商机",
            "summary": "客户希望先试点企业微信客服，再评估标准运营版。",
            "stage": "new",
            "intent_level": "hot",
            "expected_budget": "8-12 万",
            "owner_user_id": owner["id"],
        },
    )
    assert create_lead.status_code == 201
    lead = create_lead.json()
    assert lead["contact_id"] == conversation.contact_id
    assert lead["channel_id"] == conversation.channel_id
    assert lead["source_ref"] == f"conversation:{conversation.id}"

    list_profiles = client.get(
        f"/api/tenants/{tenant['id']}/contact-profiles?query=林&page=1&page_size=10",
        headers=owner_headers,
    )
    assert list_profiles.status_code == 200
    page = list_profiles.json()
    assert page["total"] == 1
    item = page["items"][0]
    assert item["id"] == conversation.contact_id
    assert item["display_name"] == "林女士"
    assert item["phone"] == "13800138888"
    assert item["wechat"] == "wx_lady_lin"
    assert item["conversation_count"] == 1
    assert item["open_conversation_count"] == 1
    assert item["support_ticket_count"] == 1
    assert item["open_support_ticket_count"] == 1
    assert item["lead_count"] == 1
    assert item["active_lead_count"] == 1
    assert item["highest_intent_level"] == "hot"
    assert item["latest_channel_name"] == "企业微信客服"
    assert item["last_message_preview"] == "我们想先试点企业微信客服，再看标准运营版报价。"

    profile_detail = client.get(
        f"/api/contact-profiles/{conversation.contact_id}",
        headers=owner_headers,
    )
    assert profile_detail.status_code == 200
    detail = profile_detail.json()
    assert detail["id"] == conversation.contact_id
    assert detail["recent_conversations"][0]["id"] == conversation.id
    assert detail["open_leads"][0]["id"] == lead["id"]
    assert detail["open_tickets"][0]["subject"] == "部署试点跟进"

    agent_role = client.post(
        f"/api/tenants/{tenant['id']}/roles",
        headers=owner_headers,
        json={"code": "agent", "name": "客服坐席"},
    ).json()
    agent_res = client.post(
        f"/api/tenants/{tenant['id']}/users",
        headers=owner_headers,
        json={"name": "一线坐席", "email": "profile-agent@example.com", "password": "ChangeMe123!"},
    )
    assert agent_res.status_code == 201
    assign_res = client.post(
        f"/api/users/{agent_res.json()['id']}/roles",
        headers=owner_headers,
        json={"role_id": agent_role["id"]},
    )
    assert assign_res.status_code == 201
    login_res = client.post(
        "/api/auth/login",
        json={
            "tenant_slug": tenant["slug"],
            "email": "profile-agent@example.com",
            "password": "ChangeMe123!",
        },
    )
    assert login_res.status_code == 200
    agent_headers = _auth_header(login_res.json()["access_token"])

    agent_detail = client.get(f"/api/contact-profiles/{conversation.contact_id}", headers=agent_headers)
    assert agent_detail.status_code == 200
    masked = agent_detail.json()
    assert masked["phone"] == "138****8888"
    assert masked["wechat"] == "wx_l****_lin"


def test_sales_leads_are_idempotent_filterable_and_tenant_scoped(client, db_session: Session) -> None:
    tenant, owner, owner_token = _bootstrap_user(
        client,
        slug="sales-lead-owner",
        email="sales-lead-owner@example.com",
    )
    other_tenant, _, other_token = _bootstrap_user(
        client,
        slug="sales-lead-other",
        email="sales-lead-other@example.com",
    )
    owner_headers = _auth_header(owner_token)
    other_headers = _auth_header(other_token)
    conversation = _seed_contact_conversation(
        db_session,
        tenant_id=tenant["id"],
        contact_name="陈总",
        phone="13900139999",
        wechat="wx_boss_chen",
        message="我们要接公众号和企业微信，预算大概十五万。",
    )

    no_token = client.post(
        f"/api/conversations/{conversation.id}/leads",
        json={"intent_level": "hot"},
    )
    assert no_token.status_code == 401

    create_res = client.post(
        f"/api/conversations/{conversation.id}/leads",
        headers=owner_headers,
        json={
            "title": "多入口标准运营版商机",
            "summary": "客户希望接公众号和企业微信，预算大概十五万。",
            "stage": "contacted",
            "intent_level": "hot",
            "expected_budget": "15 万",
            "owner_user_id": owner["id"],
            "next_follow_up_at": "2026-07-03T10:00:00+00:00",
        },
    )
    assert create_res.status_code == 201
    created = create_res.json()
    assert created["tenant_id"] == tenant["id"]
    assert created["stage"] == "contacted"
    assert created["intent_level"] == "hot"

    duplicate = client.post(
        f"/api/conversations/{conversation.id}/leads",
        headers=owner_headers,
        json={"intent_level": "warm", "expected_budget": "5 万"},
    )
    assert duplicate.status_code == 200
    assert duplicate.json()["id"] == created["id"]
    assert duplicate.json()["intent_level"] == "hot"

    list_res = client.get(
        f"/api/tenants/{tenant['id']}/leads?intent=hot&stage=contacted&page=1&page_size=10",
        headers=owner_headers,
    )
    assert list_res.status_code == 200
    page = list_res.json()
    assert page["total"] == 1
    assert page["items"][0]["id"] == created["id"]
    assert page["items"][0]["contact_display_name"] == "陈总"
    assert page["items"][0]["latest_message_preview"] == "我们要接公众号和企业微信，预算大概十五万。"

    update_res = client.patch(
        f"/api/leads/{created['id']}",
        headers=owner_headers,
        json={
            "stage": "proposal",
            "summary": "已约产品演示，准备标准运营版报价。",
            "next_step": "发送报价方案并确认试点入口。",
        },
    )
    assert update_res.status_code == 200
    updated = update_res.json()
    assert updated["stage"] == "proposal"
    assert updated["summary"] == "已约产品演示，准备标准运营版报价。"
    assert updated["next_step"] == "发送报价方案并确认试点入口。"

    cross_tenant_list = client.get(f"/api/tenants/{other_tenant['id']}/leads", headers=owner_headers)
    assert cross_tenant_list.status_code == 404

    cross_tenant_patch = client.patch(
        f"/api/leads/{created['id']}",
        headers=other_headers,
        json={"stage": "lost"},
    )
    assert cross_tenant_patch.status_code == 404

    audit_actions = [event.action for event in db_session.query(AuditEvent).all()]
    assert "sales_lead.created" in audit_actions
    assert "sales_lead.updated" in audit_actions
