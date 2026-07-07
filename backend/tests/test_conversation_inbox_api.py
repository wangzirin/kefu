from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models import Conversation, ConversationEvent, HumanReviewTask, Message, OutboxDraft, Role, User, UserRole, WorkflowRun
from app.models.foundation import utc_now


def _bootstrap_owner(client, *, slug: str = "inbox-demo") -> tuple[dict, dict, str]:
    tenant_res = client.post("/api/tenants", json={"name": "收件箱客户", "slug": slug})
    assert tenant_res.status_code == 201
    tenant = tenant_res.json()

    role_res = client.post(
        f"/api/tenants/{tenant['id']}/roles",
        json={"code": "owner", "name": "负责人"},
    )
    assert role_res.status_code == 201
    role = role_res.json()

    user_res = client.post(
        f"/api/tenants/{tenant['id']}/users",
        json={"name": "运营负责人", "email": f"{slug}@example.com", "password": "ChangeMe123!"},
    )
    assert user_res.status_code == 201
    user = user_res.json()

    assign_res = client.post(f"/api/users/{user['id']}/roles", json={"role_id": role["id"]})
    assert assign_res.status_code == 201

    login_res = client.post(
        "/api/auth/login",
        json={
            "tenant_slug": tenant["slug"],
            "email": f"{slug}@example.com",
            "password": "ChangeMe123!",
        },
    )
    assert login_res.status_code == 200
    return tenant, user, login_res.json()["access_token"]


def _create_channel(client, tenant_id: int, *, name: str = "官网客服") -> dict:
    response = client.post(
        f"/api/tenants/{tenant_id}/channels",
        json={"type": "web", "name": name, "reply_mode": "assist", "status": "active"},
    )
    assert response.status_code == 201
    return response.json()


def _create_contact(client, tenant_id: int, *, name: str) -> dict:
    response = client.post(
        f"/api/tenants/{tenant_id}/contacts",
        json={"display_name": name},
    )
    assert response.status_code == 201
    return response.json()


def _create_user_and_token(
    client, db_session: Session, tenant: dict, *, name: str, email: str
) -> tuple[dict, str]:
    role = Role(tenant_id=tenant["id"], code="agent", name="客服坐席")
    db_session.add(role)
    db_session.flush()
    user_model = User(
        tenant_id=tenant["id"],
        name=name,
        email=email.strip().lower(),
        password_hash=hash_password("ChangeMe123!"),
    )
    db_session.add(user_model)
    db_session.flush()
    db_session.add(UserRole(user_id=user_model.id, role_id=role.id))
    db_session.commit()
    db_session.refresh(user_model)
    login_res = client.post(
        "/api/auth/login",
        json={"tenant_slug": tenant["slug"], "email": email, "password": "ChangeMe123!"},
    )
    assert login_res.status_code == 200
    return {
        "id": user_model.id,
        "tenant_id": user_model.tenant_id,
        "name": user_model.name,
        "email": user_model.email,
        "status": user_model.status,
    }, login_res.json()["access_token"]


def _create_conversation_with_inbound(
    client,
    db_session: Session,
    *,
    tenant_id: int,
    channel_id: int,
    contact_id: int,
    subject: str,
    status: str = "bot",
    priority: str = "normal",
    content: str,
    minutes_old: int,
    headers: dict,
) -> tuple[dict, dict]:
    conversation_res = client.post(
        f"/api/tenants/{tenant_id}/conversations",
        headers=headers,
        json={
            "channel_id": channel_id,
            "contact_id": contact_id,
            "subject": subject,
            "status": status,
            "priority": priority,
        },
    )
    assert conversation_res.status_code == 201
    conversation = conversation_res.json()
    message_res = client.post(
        f"/api/conversations/{conversation['id']}/messages",
        headers=headers,
        json={"direction": "inbound", "sender_type": "visitor", "content": content},
    )
    assert message_res.status_code == 201
    message = message_res.json()

    created_at = utc_now() - timedelta(minutes=minutes_old)
    message_model = db_session.get(Message, message["id"])
    conversation_model = db_session.get(Conversation, conversation["id"])
    assert message_model is not None
    assert conversation_model is not None
    message_model.created_at = created_at
    conversation_model.last_message_at = created_at
    db_session.commit()
    return conversation, message


def test_conversation_inbox_paginates_searches_and_derives_ops_fields(client, db_session: Session) -> None:
    tenant, user, token = _bootstrap_owner(client)
    headers = {"Authorization": f"Bearer {token}"}
    channel = _create_channel(client, tenant["id"], name="官网客服")
    hot_contact = _create_contact(client, tenant["id"], name="高价值客户")
    refund_contact = _create_contact(client, tenant["id"], name="售后访客")

    hot_conversation, hot_message = _create_conversation_with_inbound(
        client,
        db_session,
        tenant_id=tenant["id"],
        channel_id=channel["id"],
        contact_id=hot_contact["id"],
        subject="标准运营版采购咨询",
        status="handoff",
        priority="high",
        content="我们预算十万，想了解标准运营版怎么部署",
        minutes_old=75,
        headers=headers,
    )
    refund_conversation, _ = _create_conversation_with_inbound(
        client,
        db_session,
        tenant_id=tenant["id"],
        channel_id=channel["id"],
        contact_id=refund_contact["id"],
        subject="退款政策咨询",
        status="bot",
        priority="normal",
        content="订单超过七天还能退款吗",
        minutes_old=10,
        headers=headers,
    )

    run = WorkflowRun(
        tenant_id=tenant["id"],
        conversation_id=hot_conversation["id"],
        trigger_message_id=hot_message["id"],
        workflow_type="customer_reply",
        status="waiting_human",
        current_step="human_review",
    )
    db_session.add(run)
    db_session.flush()
    db_session.add(
        HumanReviewTask(
            tenant_id=tenant["id"],
            workflow_run_id=run.id,
            conversation_id=hot_conversation["id"],
            message_id=hot_message["id"],
            reason="low_confidence",
            risk_level="high",
            draft_reply="可以安排顾问介绍标准运营版部署方式。",
        )
    )
    db_session.add(
        OutboxDraft(
            tenant_id=tenant["id"],
            conversation_id=hot_conversation["id"],
            channel_id=channel["id"],
            contact_id=hot_contact["id"],
            reply_text="您好，可以先确认业务入口和部署方式。",
            idempotency_key="inbox-hot-draft",
        )
    )
    db_session.commit()

    no_token = client.get(f"/api/tenants/{tenant['id']}/conversation-inbox")
    assert no_token.status_code == 401

    page_res = client.get(
        f"/api/tenants/{tenant['id']}/conversation-inbox?page=1&page_size=1&sort=waiting_desc",
        headers=headers,
    )
    assert page_res.status_code == 200
    page = page_res.json()
    assert page["page"] == 1
    assert page["page_size"] == 1
    assert page["total"] == 2
    assert [item["id"] for item in page["items"]] == [hot_conversation["id"]]
    first = page["items"][0]
    assert first["contact_display_name"] == "高价值客户"
    assert first["waiting_minutes"] >= 70
    assert first["sla_status"] == "breached"
    assert first["human_review_open_count"] == 1
    assert first["outbox_pending_count"] == 1
    assert first["next_action"] == "审核 AI 草稿"

    search_res = client.get(
        f"/api/tenants/{tenant['id']}/conversation-inbox?query=退款",
        headers=headers,
    )
    assert search_res.status_code == 200
    assert [item["id"] for item in search_res.json()["items"]] == [refund_conversation["id"]]

    breached_res = client.get(
        f"/api/tenants/{tenant['id']}/conversation-inbox?sla=breached",
        headers=headers,
    )
    assert breached_res.status_code == 200
    assert [item["id"] for item in breached_res.json()["items"]] == [hot_conversation["id"]]

    status_res = client.get(
        f"/api/tenants/{tenant['id']}/conversation-inbox?status=handoff",
        headers=headers,
    )
    assert status_res.status_code == 200
    assert [item["id"] for item in status_res.json()["items"]] == [hot_conversation["id"]]
    assert user["id"] is not None


def test_conversation_assignment_requires_same_tenant_and_supports_mine_filter(client, db_session: Session) -> None:
    tenant, user, token = _bootstrap_owner(client, slug="inbox-assignment")
    other_tenant, other_user, other_token = _bootstrap_owner(client, slug="inbox-other")
    headers = {"Authorization": f"Bearer {token}"}
    other_headers = {"Authorization": f"Bearer {other_token}"}
    channel = _create_channel(client, tenant["id"])
    contact = _create_contact(client, tenant["id"], name="待分配访客")
    conversation, _ = _create_conversation_with_inbound(
        client,
        db_session,
        tenant_id=tenant["id"],
        channel_id=channel["id"],
        contact_id=contact["id"],
        subject="需要人工接待",
        content="请安排一个真人顾问联系我",
        minutes_old=5,
        headers=headers,
    )

    other_channel = _create_channel(client, other_tenant["id"])
    other_contact = _create_contact(client, other_tenant["id"], name="其他租户访客")
    other_conversation, _ = _create_conversation_with_inbound(
        client,
        db_session,
        tenant_id=other_tenant["id"],
        channel_id=other_channel["id"],
        contact_id=other_contact["id"],
        subject="其他租户会话",
        content="不能被当前租户读取",
        minutes_old=5,
        headers=other_headers,
    )

    no_token = client.patch(
        f"/api/conversations/{conversation['id']}/assignment",
        json={"assigned_user_id": user["id"]},
    )
    assert no_token.status_code == 401

    wrong_user = client.patch(
        f"/api/conversations/{conversation['id']}/assignment",
        headers=headers,
        json={"assigned_user_id": other_user["id"]},
    )
    assert wrong_user.status_code == 404

    cross_tenant_patch = client.patch(
        f"/api/conversations/{other_conversation['id']}/assignment",
        headers=headers,
        json={"assigned_user_id": user["id"]},
    )
    assert cross_tenant_patch.status_code == 404

    assign_res = client.patch(
        f"/api/conversations/{conversation['id']}/assignment",
        headers=headers,
        json={"assigned_user_id": user["id"], "status": "handoff"},
    )
    assert assign_res.status_code == 200
    assigned = assign_res.json()
    assert assigned["assigned_user_id"] == user["id"]
    assert assigned["status"] == "handoff"

    mine_res = client.get(
        f"/api/tenants/{tenant['id']}/conversation-inbox?assigned=mine",
        headers=headers,
    )
    assert mine_res.status_code == 200
    assert [item["id"] for item in mine_res.json()["items"]] == [conversation["id"]]

    cross_tenant_list = client.get(
        f"/api/tenants/{other_tenant['id']}/conversation-inbox",
        headers=headers,
    )
    assert cross_tenant_list.status_code == 404


def test_conversation_workflow_actions_cover_agent_lifecycle_and_audit_events(
    client, db_session: Session
) -> None:
    tenant, owner, owner_token = _bootstrap_owner(client, slug="inbox-workflow")
    agent, agent_token = _create_user_and_token(
        client,
        db_session,
        tenant,
        name="二线坐席",
        email="inbox-workflow-agent@example.com",
    )
    owner_headers = {"Authorization": f"Bearer {owner_token}"}
    agent_headers = {"Authorization": f"Bearer {agent_token}"}
    channel = _create_channel(client, tenant["id"])
    contact = _create_contact(client, tenant["id"], name="坐席流程访客")
    conversation, _ = _create_conversation_with_inbound(
        client,
        db_session,
        tenant_id=tenant["id"],
        channel_id=channel["id"],
        contact_id=contact["id"],
        subject="想找人工确认报价",
        content="请安排人工跟进这个报价",
        minutes_old=12,
        headers=owner_headers,
    )

    no_token = client.post(
        f"/api/conversations/{conversation['id']}/workflow-actions",
        json={"action": "claim"},
    )
    assert no_token.status_code == 401

    claim_res = client.post(
        f"/api/conversations/{conversation['id']}/workflow-actions",
        headers=owner_headers,
        json={"action": "claim", "note": "我先接手"},
    )
    assert claim_res.status_code == 200
    claimed = claim_res.json()
    assert claimed["assigned_user_id"] == owner["id"]
    assert claimed["status"] == "handoff"

    empty_note = client.post(
        f"/api/conversations/{conversation['id']}/workflow-actions",
        headers=owner_headers,
        json={"action": "note", "note": ""},
    )
    assert empty_note.status_code == 422

    note_res = client.post(
        f"/api/conversations/{conversation['id']}/workflow-actions",
        headers=owner_headers,
        json={"action": "note", "note": "客户需要今天下午回访"},
    )
    assert note_res.status_code == 200
    assert note_res.json()["assigned_user_id"] == owner["id"]

    conflict_claim = client.post(
        f"/api/conversations/{conversation['id']}/workflow-actions",
        headers=agent_headers,
        json={"action": "claim"},
    )
    assert conflict_claim.status_code == 409

    transfer_res = client.post(
        f"/api/conversations/{conversation['id']}/workflow-actions",
        headers=owner_headers,
        json={"action": "transfer", "target_user_id": agent["id"], "note": "转给二线坐席"},
    )
    assert transfer_res.status_code == 200
    transferred = transfer_res.json()
    assert transferred["assigned_user_id"] == agent["id"]
    assert transferred["status"] == "handoff"

    wait_customer_res = client.post(
        f"/api/conversations/{conversation['id']}/workflow-actions",
        headers=agent_headers,
        json={"action": "wait_customer", "note": "已报价，等待客户补充预算"},
    )
    assert wait_customer_res.status_code == 200
    assert wait_customer_res.json()["status"] == "waiting_customer"

    resolve_res = client.post(
        f"/api/conversations/{conversation['id']}/workflow-actions",
        headers=agent_headers,
        json={"action": "resolve", "note": "客户已确认暂缓"},
    )
    assert resolve_res.status_code == 200
    assert resolve_res.json()["status"] == "resolved"

    release_res = client.post(
        f"/api/conversations/{conversation['id']}/workflow-actions",
        headers=agent_headers,
        json={"action": "release", "note": "释放回公共池"},
    )
    assert release_res.status_code == 200
    released = release_res.json()
    assert released["assigned_user_id"] is None
    assert released["status"] == "waiting_human"

    reopen_res = client.post(
        f"/api/conversations/{conversation['id']}/workflow-actions",
        headers=owner_headers,
        json={"action": "reopen", "note": "重新打开跟进"},
    )
    assert reopen_res.status_code == 200
    reopened = reopen_res.json()
    assert reopened["assigned_user_id"] == owner["id"]
    assert reopened["status"] == "handoff"

    close_res = client.post(
        f"/api/conversations/{conversation['id']}/workflow-actions",
        headers=owner_headers,
        json={"action": "close", "note": "关闭当前对话"},
    )
    assert close_res.status_code == 200
    assert close_res.json()["status"] == "closed"
    close_message = db_session.scalar(
        select(Message)
        .where(Message.conversation_id == conversation["id"], Message.sender_type == "system")
        .order_by(Message.id.desc())
    )
    assert close_message is not None
    assert close_message.content == "客服已关闭对话"

    transfer_without_target = client.post(
        f"/api/conversations/{conversation['id']}/workflow-actions",
        headers=owner_headers,
        json={"action": "transfer"},
    )
    assert transfer_without_target.status_code == 422

    events = list(
        db_session.scalars(
            select(ConversationEvent)
            .where(ConversationEvent.conversation_id == conversation["id"])
            .order_by(ConversationEvent.id.asc())
        ).all()
    )
    event_types = [event.event_type for event in events]
    assert "conversation.workflow.claim" in event_types
    assert "conversation.workflow.note" in event_types
    assert "conversation.workflow.transfer" in event_types
    assert "conversation.workflow.wait_customer" in event_types
    assert "conversation.workflow.resolve" in event_types
    assert "conversation.workflow.release" in event_types
    assert "conversation.workflow.reopen" in event_types
    assert "conversation.workflow.close" in event_types
    assert any("客户需要今天下午回访" in event.payload for event in events)
