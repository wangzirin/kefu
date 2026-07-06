from datetime import timedelta

from app.core.rbac import allowed_roles_for_permission, permissions_for_roles
from app.models import (
    Channel,
    Contact,
    Conversation,
    DeliveryFailureReview,
    HumanReviewTask,
    KnowledgeEvaluationRun,
    KnowledgeGapItem,
    Message,
    OutboxDeliveryJob,
    OutboxDraft,
    SalesLead,
    SupportTicket,
    WorkflowRun,
    utc_now,
)
from test_p3_06h_rbac_permission_matrix import _bootstrap_user_with_role


def _seed_ops_dashboard_fixture(db_session, tenant_id: int) -> dict[str, int]:
    now = utc_now()
    channel_wecom = Channel(
        tenant_id=tenant_id,
        type="wecom_customer_service",
        name="企业微信客服",
        status="active",
    )
    channel_site = Channel(
        tenant_id=tenant_id,
        type="website",
        name="官网客服",
        status="active",
    )
    contact = Contact(tenant_id=tenant_id, display_name="测试客户")
    db_session.add_all([channel_wecom, channel_site, contact])
    db_session.flush()

    conversation_wecom = Conversation(
        tenant_id=tenant_id,
        channel_id=channel_wecom.id,
        contact_id=contact.id,
        status="human_review",
        priority="high",
        subject="套餐咨询",
        created_at=now - timedelta(hours=2),
        last_message_at=now - timedelta(minutes=24),
    )
    conversation_site = Conversation(
        tenant_id=tenant_id,
        channel_id=channel_site.id,
        contact_id=contact.id,
        status="bot",
        priority="normal",
        subject="售后咨询",
        created_at=now - timedelta(days=2),
        last_message_at=now - timedelta(days=2),
    )
    old_conversation = Conversation(
        tenant_id=tenant_id,
        channel_id=channel_site.id,
        contact_id=contact.id,
        status="bot",
        priority="normal",
        subject="历史咨询",
        created_at=now - timedelta(days=40),
        last_message_at=now - timedelta(days=40),
    )
    db_session.add_all([conversation_wecom, conversation_site, old_conversation])
    db_session.flush()

    message = Message(
        conversation_id=conversation_wecom.id,
        direction="inbound",
        sender_type="customer",
        content="客户问题原文不应出现在聚合接口",
        created_at=now - timedelta(minutes=25),
    )
    old_message = Message(
        conversation_id=old_conversation.id,
        direction="inbound",
        sender_type="customer",
        content="历史消息",
        created_at=now - timedelta(days=40),
    )
    db_session.add_all([message, old_message])
    db_session.flush()

    workflow = WorkflowRun(
        tenant_id=tenant_id,
        conversation_id=conversation_wecom.id,
        trigger_message_id=message.id,
        status="waiting_human",
        created_at=now - timedelta(minutes=23),
    )
    db_session.add(workflow)
    db_session.flush()

    review = HumanReviewTask(
        tenant_id=tenant_id,
        workflow_run_id=workflow.id,
        conversation_id=conversation_wecom.id,
        message_id=message.id,
        status="open",
        reason="low_confidence",
        risk_level="high",
        draft_reply="草稿正文不进入聚合接口",
        created_at=now - timedelta(minutes=22),
    )
    outbox = OutboxDraft(
        tenant_id=tenant_id,
        conversation_id=conversation_wecom.id,
        channel_id=channel_wecom.id,
        contact_id=contact.id,
        source_review_task_id=None,
        source_workflow_run_id=workflow.id,
        source_message_id=message.id,
        status="pending_confirmation",
        delivery_status="not_sent",
        reply_text="待发送正文不进入聚合接口",
        idempotency_key="ops-dashboard-draft",
        created_at=now - timedelta(minutes=18),
        updated_at=now - timedelta(minutes=18),
    )
    ready_outbox = OutboxDraft(
        tenant_id=tenant_id,
        conversation_id=conversation_site.id,
        channel_id=channel_site.id,
        contact_id=contact.id,
        status="ready_to_send",
        delivery_status="not_sent",
        reply_text="官网待发送",
        idempotency_key="ops-dashboard-ready-draft",
        created_at=now - timedelta(days=2),
        updated_at=now - timedelta(days=2),
    )
    db_session.add_all([review, outbox, ready_outbox])
    db_session.flush()

    db_session.add_all(
        [
            DeliveryFailureReview(
                tenant_id=tenant_id,
                channel_id=channel_wecom.id,
                receipt_id=1,
                provider="wecom",
                normalized_status="failed",
                severity="warning",
                review_reason="fixture_failure",
                next_action="manual_review_provider_status",
                status="open",
                created_at=now - timedelta(minutes=12),
                updated_at=now - timedelta(minutes=12),
            ),
            OutboxDeliveryJob(
                tenant_id=tenant_id,
                outbox_draft_id=outbox.id,
                channel_id=channel_wecom.id,
                status="dead_letter",
                idempotency_key="ops-dashboard-job",
                external_write_requested=False,
                created_at=now - timedelta(minutes=10),
                updated_at=now - timedelta(minutes=10),
            ),
            KnowledgeGapItem(
                tenant_id=tenant_id,
                status="open",
                severity="high",
                source_type="evaluation_case",
                source_ref="case-1",
                gap_type="missing_policy",
                source_title="价格政策缺口",
                created_at=now - timedelta(minutes=9),
                updated_at=now - timedelta(minutes=9),
            ),
            SupportTicket(
                tenant_id=tenant_id,
                conversation_id=conversation_wecom.id,
                channel_id=channel_wecom.id,
                contact_id=contact.id,
                subject="需要人工售后",
                status="open",
                priority="high",
                source_ref=f"conversation:{conversation_wecom.id}",
                created_at=now - timedelta(minutes=8),
                updated_at=now - timedelta(minutes=8),
            ),
            SalesLead(
                tenant_id=tenant_id,
                contact_id=contact.id,
                channel_id=channel_wecom.id,
                conversation_id=conversation_wecom.id,
                title="高意向客户",
                stage="new",
                intent_level="hot",
                source_ref=f"conversation:{conversation_wecom.id}",
                created_at=now - timedelta(minutes=7),
                updated_at=now - timedelta(minutes=7),
            ),
            KnowledgeEvaluationRun(
                tenant_id=tenant_id,
                evaluation_set_id=1,
                total_cases=20,
                answered_cases=18,
                passed_cases=15,
                failed_cases=5,
                needs_review_cases=6,
                hit_rate=0.9,
                citation_coverage=0.75,
                expected_term_coverage=0.7,
                average_confidence=0.82,
                summary_payload={"fixture": True},
                created_at=now - timedelta(minutes=5),
            ),
        ]
    )
    db_session.commit()
    return {"wecom_channel_id": channel_wecom.id, "site_channel_id": channel_site.id}


def test_ops_dashboard_permission_matrix() -> None:
    assert allowed_roles_for_permission("dashboard.read") == ("admin", "owner", "viewer")
    assert "dashboard.read" in permissions_for_roles(["owner"])
    assert "dashboard.read" in permissions_for_roles(["admin"])
    assert "dashboard.read" in permissions_for_roles(["viewer"])
    assert "dashboard.read" not in permissions_for_roles(["agent"])


def test_ops_dashboard_aggregates_business_signals_without_raw_text(client, db_session) -> None:
    tenant, token = _bootstrap_user_with_role(
        client,
        slug="ops-dashboard-owner",
        role_code="owner",
        email="ops-dashboard-owner@example.com",
    )
    channel_ids = _seed_ops_dashboard_fixture(db_session, tenant["id"])

    res = client.get(
        f"/api/tenants/{tenant['id']}/ops/dashboard?range=today",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert res.status_code == 200
    payload = res.json()
    assert payload["tenant_id"] == tenant["id"]
    assert payload["range"] == "today"
    assert payload["data_mode"] == "server_aggregation"
    assert payload["data_source"] == {
        "mode": "server_aggregation",
        "label": "服务端聚合",
        "source": "standard_ops_operational_tables",
        "contract_version": "p3_06t_02_v1",
        "aggregation_grain": "tenant_range_channel_aggregate",
        "refresh_model": "request_time_read",
        "freshness": "request_time_read",
        "completeness": "complete",
        "source_tables": [
            "conversations",
            "messages",
            "human_review_tasks",
            "outbox_drafts",
            "delivery_failure_reviews",
            "outbox_delivery_jobs",
            "knowledge_gap_items",
            "support_tickets",
            "sales_leads",
            "knowledge_evaluation_runs",
        ],
        "excluded_fields": [
            "messages.content",
            "human_review_tasks.draft_reply",
            "outbox_drafts.reply_text",
            "contacts.phone",
            "contacts.email",
            "sales_leads.contact_value",
            "delivery_receipts.raw_payload",
            "channel_connectors.public_config",
        ],
        "caveats": [
            "即时读侧聚合，不是历史数仓或物化统计表。",
            "仅返回计数、比例、时间窗口和动作摘要，不返回客户原文或出站草稿全文。",
            "channel_id 筛选只统计该渠道关联的会话、草稿、失败复盘、工单和线索；知识缺口只在全部渠道视图统计。",
        ],
        "is_demo": False,
        "uses_local_sample": False,
        "fallback_reason": None,
    }
    assert payload["source_window"]["range"] == "today"
    assert payload["source_window"]["label"] == "今日 00:00 至当前"
    assert payload["source_window"]["start"] == payload["interval_start"]
    assert payload["source_window"]["end"] == payload["interval_end"]
    assert payload["source_window"]["generated_at"] == payload["generated_at"]
    assert payload["source_window"]["timezone"] == "UTC"
    assert payload["filters"] == {
        "range": "today",
        "channel_id": None,
        "channel_name": None,
        "channel_type": None,
        "is_channel_filtered": False,
    }
    assert payload["summary"]["inbound_conversations"] == 1
    assert payload["summary"]["inbound_messages"] == 1
    assert payload["summary"]["open_reviews"] == 1
    assert payload["summary"]["high_risk_reviews"] == 1
    assert payload["summary"]["pending_outbox_drafts"] == 1
    assert payload["summary"]["ready_outbox_drafts"] == 0
    assert payload["summary"]["open_failure_reviews"] == 1
    assert payload["summary"]["blocked_delivery_jobs"] == 1
    assert payload["summary"]["open_knowledge_gaps"] == 1
    assert payload["summary"]["open_tickets"] == 1
    assert payload["summary"]["open_leads"] == 1
    assert 0 <= payload["summary"]["health_score"] <= 100
    assert payload["quality"]["latest_evaluation_run_id"] is not None
    assert payload["quality"]["hit_rate"] == 0.9
    assert len(payload["funnel"]) >= 4
    assert len(payload["trend"]) >= 4
    assert payload["action_items"]
    assert payload["external_call_performed"] is False
    assert payload["external_platform_write_performed"] is False

    by_channel = {row["channel_id"]: row for row in payload["channels"]}
    assert by_channel[channel_ids["wecom_channel_id"]]["open_reviews"] == 1
    assert by_channel[channel_ids["wecom_channel_id"]]["exception_count"] == 2
    assert str(payload).find("客户问题原文") == -1
    assert str(payload).find("草稿正文") == -1
    assert str(payload).find("待发送正文") == -1
    for excluded_field in payload["data_source"]["excluded_fields"]:
        assert excluded_field


def test_ops_dashboard_channel_filter_and_same_tenant_guard(client, db_session) -> None:
    tenant_a, token_a = _bootstrap_user_with_role(
        client,
        slug="ops-dashboard-tenant-a",
        role_code="owner",
        email="ops-dashboard-a@example.com",
    )
    tenant_b, _ = _bootstrap_user_with_role(
        client,
        slug="ops-dashboard-tenant-b",
        role_code="owner",
        email="ops-dashboard-b@example.com",
    )
    channel_ids = _seed_ops_dashboard_fixture(db_session, tenant_a["id"])

    filtered_res = client.get(
        (
            f"/api/tenants/{tenant_a['id']}/ops/dashboard"
            f"?range=30d&channel_id={channel_ids['site_channel_id']}"
        ),
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert filtered_res.status_code == 200
    filtered = filtered_res.json()
    assert filtered["summary"]["inbound_conversations"] == 1
    assert filtered["summary"]["ready_outbox_drafts"] == 1
    assert filtered["summary"]["open_reviews"] == 0
    assert filtered["data_mode"] == "server_aggregation"
    assert filtered["filters"] == {
        "range": "30d",
        "channel_id": channel_ids["site_channel_id"],
        "channel_name": "官网客服",
        "channel_type": "website",
        "is_channel_filtered": True,
    }
    assert filtered["source_window"]["range"] == "30d"
    assert filtered["data_source"]["contract_version"] == "p3_06t_02_v1"
    assert filtered["data_source"]["aggregation_grain"] == "tenant_range_channel_aggregate"
    assert filtered["data_source"]["uses_local_sample"] is False
    assert [row["channel_id"] for row in filtered["channels"]] == [channel_ids["site_channel_id"]]

    missing_channel_res = client.get(
        f"/api/tenants/{tenant_a['id']}/ops/dashboard?channel_id=999999",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert missing_channel_res.status_code == 404

    invalid_range_res = client.get(
        f"/api/tenants/{tenant_a['id']}/ops/dashboard?range=90d",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert invalid_range_res.status_code == 422

    cross_tenant_res = client.get(
        f"/api/tenants/{tenant_b['id']}/ops/dashboard",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert tenant_a["id"] != tenant_b["id"]
    assert cross_tenant_res.status_code == 404


def test_ops_dashboard_viewer_can_read_but_agent_is_blocked(client, db_session) -> None:
    viewer_tenant, viewer_token = _bootstrap_user_with_role(
        client,
        slug="ops-dashboard-viewer",
        role_code="viewer",
        email="ops-dashboard-viewer@example.com",
    )
    _seed_ops_dashboard_fixture(db_session, viewer_tenant["id"])
    viewer_res = client.get(
        f"/api/tenants/{viewer_tenant['id']}/ops/dashboard",
        headers={"Authorization": f"Bearer {viewer_token}"},
    )
    assert viewer_res.status_code == 200

    agent_tenant, agent_token = _bootstrap_user_with_role(
        client,
        slug="ops-dashboard-agent",
        role_code="agent",
        email="ops-dashboard-agent@example.com",
    )
    agent_res = client.get(
        f"/api/tenants/{agent_tenant['id']}/ops/dashboard",
        headers={"Authorization": f"Bearer {agent_token}"},
    )
    assert agent_res.status_code == 403

    no_token_res = client.get(f"/api/tenants/{viewer_tenant['id']}/ops/dashboard")
    assert no_token_res.status_code == 401
