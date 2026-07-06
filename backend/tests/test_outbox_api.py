def _bootstrap_owner(client, slug: str = "outbox-demo", email: str = "outbox-owner@example.com") -> tuple[dict, str]:
    tenant_res = client.post("/api/tenants", json={"name": f"{slug} 客户", "slug": slug})
    assert tenant_res.status_code == 201
    tenant = tenant_res.json()

    role_res = client.post(
        f"/api/tenants/{tenant['id']}/roles",
        json={"code": "owner", "name": "管理员"},
    )
    assert role_res.status_code == 201
    role = role_res.json()

    user_res = client.post(
        f"/api/tenants/{tenant['id']}/users",
        json={"name": "发送主管", "email": email, "password": "ChangeMe123!"},
    )
    assert user_res.status_code == 201
    user = user_res.json()

    assign_res = client.post(f"/api/users/{user['id']}/roles", json={"role_id": role["id"]})
    assert assign_res.status_code == 201

    login_res = client.post(
        "/api/auth/login",
        json={"tenant_slug": tenant["slug"], "email": email, "password": "ChangeMe123!"},
    )
    assert login_res.status_code == 200
    return tenant, login_res.json()["access_token"]


def _conversation_with_message(client, tenant_id: int, headers: dict) -> tuple[dict, dict]:
    channel = client.post(
        f"/api/tenants/{tenant_id}/channels",
        json={"type": "web", "name": "官网客服", "reply_mode": "assist", "status": "active"},
    ).json()
    contact = client.post(
        f"/api/tenants/{tenant_id}/contacts",
        json={"display_name": "待发送访客"},
    ).json()
    conversation_res = client.post(
        f"/api/tenants/{tenant_id}/conversations",
        headers=headers,
        json={
            "channel_id": channel["id"],
            "contact_id": contact["id"],
            "subject": "售后政策咨询",
        },
    )
    assert conversation_res.status_code == 201
    conversation = conversation_res.json()
    message_res = client.post(
        f"/api/conversations/{conversation['id']}/messages",
        headers=headers,
        json={
            "direction": "inbound",
            "sender_type": "visitor",
            "content": "超过七天还能退吗？",
        },
    )
    assert message_res.status_code == 201
    return conversation, message_res.json()


def _approved_review_task(client, tenant_id: int, headers: dict) -> tuple[dict, dict, dict]:
    conversation, message = _conversation_with_message(client, tenant_id, headers)
    run_res = client.post(
        f"/api/conversations/{conversation['id']}/workflow-runs",
        headers=headers,
        json={
            "trigger_message_id": message["id"],
            "workflow_type": "customer_reply",
            "current_step": "classify_intent",
            "state_payload": {"source": "inbound_message"},
        },
    )
    assert run_res.status_code == 201
    run = run_res.json()
    review_res = client.post(
        f"/api/workflow-runs/{run['id']}/human-review-tasks",
        headers=headers,
        json={
            "reason": "low_confidence",
            "risk_level": "medium",
            "draft_reply": "超过七天退货需要人工核对。",
        },
    )
    assert review_res.status_code == 201
    review = review_res.json()
    final_reply = "超过七天的订单需要结合商品状态和订单政策核对，我先帮您确认可申请的售后入口。"
    resolve_res = client.patch(
        f"/api/human-review-tasks/{review['id']}",
        headers=headers,
        json={
            "decision": "approved",
            "final_reply": final_reply,
            "resolution_note": "坐席确认可作为发送草稿",
        },
    )
    assert resolve_res.status_code == 200
    return conversation, message, resolve_res.json()


def test_approved_review_can_create_and_confirm_outbox_draft_without_sending(client) -> None:
    tenant, token = _bootstrap_owner(client)
    headers = {"Authorization": f"Bearer {token}"}
    conversation, message, review = _approved_review_task(client, tenant["id"], headers)

    create_res = client.post(
        f"/api/human-review-tasks/{review['id']}/outbox-drafts",
        headers=headers,
        json={},
    )

    assert create_res.status_code == 201
    draft = create_res.json()
    assert draft["tenant_id"] == tenant["id"]
    assert draft["conversation_id"] == conversation["id"]
    assert draft["source_review_task_id"] == review["id"]
    assert draft["source_workflow_run_id"] == review["workflow_run_id"]
    assert draft["source_message_id"] == message["id"]
    assert draft["reply_text"] == review["final_reply"]
    assert draft["status"] == "pending_confirmation"
    assert draft["delivery_status"] == "not_sent"
    assert draft["confirmed_at"] is None
    assert draft["sent_at"] is None
    assert draft["idempotency_key"] == f"human_review_task:{review['id']}:final_reply"

    duplicate_res = client.post(
        f"/api/human-review-tasks/{review['id']}/outbox-drafts",
        headers=headers,
        json={},
    )
    assert duplicate_res.status_code == 409

    list_res = client.get(
        f"/api/tenants/{tenant['id']}/outbox-drafts?status=pending_confirmation",
        headers=headers,
    )
    assert list_res.status_code == 200
    assert [item["id"] for item in list_res.json()] == [draft["id"]]

    confirm_res = client.post(
        f"/api/outbox-drafts/{draft['id']}/confirmation",
        headers=headers,
        json={"confirmation_note": "已核对政策和语气，进入待发送队列"},
    )
    assert confirm_res.status_code == 200
    confirmed = confirm_res.json()
    assert confirmed["status"] == "ready_to_send"
    assert confirmed["delivery_status"] == "not_sent"
    assert confirmed["confirmed_by_id"] is not None
    assert confirmed["confirmed_at"] is not None
    assert confirmed["confirmation_note"] == "已核对政策和语气，进入待发送队列"
    assert confirmed["sent_at"] is None

    ready_res = client.get(
        f"/api/tenants/{tenant['id']}/outbox-drafts?status=ready_to_send",
        headers=headers,
    )
    assert ready_res.status_code == 200
    assert [item["id"] for item in ready_res.json()] == [draft["id"]]

    audit_res = client.get(f"/api/tenants/{tenant['id']}/audit-events", headers=headers)
    actions = [event["action"] for event in audit_res.json()]
    assert "outbox_draft.created" in actions
    assert "outbox_draft.ready_to_send" in actions


def test_ready_outbox_draft_can_create_dry_run_send_attempt_without_external_delivery(client) -> None:
    tenant, token = _bootstrap_owner(client, slug="outbox-send", email="outbox-send@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    _, _, review = _approved_review_task(client, tenant["id"], headers)
    draft = client.post(
        f"/api/human-review-tasks/{review['id']}/outbox-drafts",
        headers=headers,
        json={},
    ).json()
    confirmed = client.post(
        f"/api/outbox-drafts/{draft['id']}/confirmation",
        headers=headers,
        json={"confirmation_note": "进入 dry-run 发送检查"},
    ).json()

    attempt_res = client.post(
        f"/api/outbox-drafts/{confirmed['id']}/send-attempts",
        headers=headers,
        json={
            "delivery_mode": "dry_run",
            "operator_note": "只验证发送载荷，不触达外部平台",
        },
    )

    assert attempt_res.status_code == 201
    attempt = attempt_res.json()
    assert attempt["tenant_id"] == tenant["id"]
    assert attempt["outbox_draft_id"] == confirmed["id"]
    assert attempt["attempt_number"] == 1
    assert attempt["delivery_mode"] == "dry_run"
    assert attempt["provider"] == "dry_run"
    assert attempt["status"] == "succeeded"
    assert attempt["delivery_status"] == "not_sent"
    assert attempt["external_message_id"] == ""
    assert attempt["sent_at"] is None
    assert attempt["finished_at"] is not None
    assert attempt["request_payload"]["external_write"] is False
    assert attempt["response_payload"]["external_write"] is False
    assert attempt["response_payload"]["would_send"] is True
    assert attempt["operator_note"] == "只验证发送载荷，不触达外部平台"

    duplicate_res = client.post(
        f"/api/outbox-drafts/{confirmed['id']}/send-attempts",
        headers=headers,
        json={"delivery_mode": "dry_run"},
    )
    assert duplicate_res.status_code == 409

    attempts_res = client.get(
        f"/api/outbox-drafts/{confirmed['id']}/send-attempts",
        headers=headers,
    )
    assert attempts_res.status_code == 200
    assert [item["id"] for item in attempts_res.json()] == [attempt["id"]]

    drafts_res = client.get(
        f"/api/tenants/{tenant['id']}/outbox-drafts?status=ready_to_send",
        headers=headers,
    )
    assert drafts_res.status_code == 200
    [ready_draft] = drafts_res.json()
    assert ready_draft["delivery_status"] == "not_sent"
    assert ready_draft["sent_at"] is None

    audit_res = client.get(f"/api/tenants/{tenant['id']}/audit-events", headers=headers)
    actions = [event["action"] for event in audit_res.json()]
    assert "outbox_send_attempt.dry_run_succeeded" in actions


def test_outbox_worker_dry_run_processes_ready_draft_with_receipt_and_rate_limit_metadata(client) -> None:
    tenant, token = _bootstrap_owner(client, slug="outbox-worker", email="outbox-worker@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    _, _, review = _approved_review_task(client, tenant["id"], headers)
    draft = client.post(
        f"/api/human-review-tasks/{review['id']}/outbox-drafts",
        headers=headers,
        json={},
    ).json()
    confirmed = client.post(
        f"/api/outbox-drafts/{draft['id']}/confirmation",
        headers=headers,
        json={"confirmation_note": "进入 worker dry-run"},
    ).json()

    run_res = client.post(
        f"/api/tenants/{tenant['id']}/outbox-worker-runs",
        headers=headers,
        json={"batch_size": 5, "rate_limit_per_minute": 60, "max_attempts": 3},
    )

    assert run_res.status_code == 201
    run = run_res.json()
    assert run["tenant_id"] == tenant["id"]
    assert run["mode"] == "dry_run_worker"
    assert run["scanned"] == 1
    assert run["processed"] == 1
    assert run["succeeded"] == 1
    assert run["failed"] == 0
    assert run["rate_limited"] == 0
    assert run["external_write"] is False
    assert run["rate_limit"]["per_minute"] == 60
    [attempt] = run["attempts"]
    assert attempt["outbox_draft_id"] == confirmed["id"]
    assert attempt["provider"] == "dry_run_worker"
    assert attempt["status"] == "succeeded"
    assert attempt["delivery_status"] == "not_sent"
    assert attempt["sent_at"] is None
    assert attempt["response_payload"]["external_write"] is False
    assert attempt["response_payload"]["receipt_placeholder"]["status"] == "not_available"
    assert attempt["response_payload"]["retry_placeholder"]["next_action"] == "none"

    list_res = client.get(f"/api/outbox-drafts/{confirmed['id']}/send-attempts", headers=headers)
    assert list_res.status_code == 200
    assert [item["id"] for item in list_res.json()] == [attempt["id"]]

    second_run_res = client.post(
        f"/api/tenants/{tenant['id']}/outbox-worker-runs",
        headers=headers,
        json={"batch_size": 5, "rate_limit_per_minute": 60, "max_attempts": 3},
    )
    assert second_run_res.status_code == 201
    second_run = second_run_res.json()
    assert second_run["scanned"] == 0
    assert second_run["processed"] == 0
    assert second_run["attempts"] == []

    audit_res = client.get(f"/api/tenants/{tenant['id']}/audit-events", headers=headers)
    actions = [event["action"] for event in audit_res.json()]
    assert "outbox_worker.dry_run_succeeded" in actions


def test_outbox_worker_records_failed_attempt_and_retry_placeholder_for_inactive_channel(client, db_session) -> None:
    from app.models import Channel

    tenant, token = _bootstrap_owner(client, slug="outbox-worker-fail", email="outbox-worker-fail@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    _, _, review = _approved_review_task(client, tenant["id"], headers)
    draft = client.post(
        f"/api/human-review-tasks/{review['id']}/outbox-drafts",
        headers=headers,
        json={},
    ).json()
    confirmed = client.post(
        f"/api/outbox-drafts/{draft['id']}/confirmation",
        headers=headers,
        json={"confirmation_note": "测试失败状态"},
    ).json()
    channel = db_session.get(Channel, confirmed["channel_id"])
    channel.status = "paused"
    db_session.commit()

    run_res = client.post(
        f"/api/tenants/{tenant['id']}/outbox-worker-runs",
        headers=headers,
        json={"batch_size": 5, "rate_limit_per_minute": 60, "max_attempts": 3},
    )

    assert run_res.status_code == 201
    run = run_res.json()
    assert run["processed"] == 1
    assert run["succeeded"] == 0
    assert run["failed"] == 1
    [attempt] = run["attempts"]
    assert attempt["status"] == "failed"
    assert attempt["delivery_status"] == "not_sent"
    assert attempt["error_message"] == "channel is not active"
    assert attempt["response_payload"]["retry_placeholder"]["next_action"] == "retry_later"
    assert attempt["response_payload"]["retry_placeholder"]["attempts_remaining"] == 2
    assert attempt["response_payload"]["receipt_placeholder"]["status"] == "not_available"
    assert attempt["sent_at"] is None


def test_outbox_worker_rate_limit_records_unprocessed_ready_drafts_without_attempts(client) -> None:
    tenant, token = _bootstrap_owner(client, slug="outbox-worker-limit", email="outbox-worker-limit@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    ready_draft_ids = []
    for _ in range(2):
        _, _, review = _approved_review_task(client, tenant["id"], headers)
        draft = client.post(
            f"/api/human-review-tasks/{review['id']}/outbox-drafts",
            headers=headers,
            json={},
        ).json()
        confirmed = client.post(
            f"/api/outbox-drafts/{draft['id']}/confirmation",
            headers=headers,
            json={"confirmation_note": "测试限流占位"},
        ).json()
        ready_draft_ids.append(confirmed["id"])

    run_res = client.post(
        f"/api/tenants/{tenant['id']}/outbox-worker-runs",
        headers=headers,
        json={"batch_size": 5, "rate_limit_per_minute": 1, "max_attempts": 3},
    )

    assert run_res.status_code == 201
    run = run_res.json()
    assert run["scanned"] == 2
    assert run["processed"] == 1
    assert run["succeeded"] == 1
    assert run["failed"] == 0
    assert run["rate_limited"] == 1
    assert run["rate_limited_draft_ids"] == [ready_draft_ids[1]]
    assert len(run["attempts"]) == 1
    limited_attempts = client.get(
        f"/api/outbox-drafts/{ready_draft_ids[1]}/send-attempts",
        headers=headers,
    ).json()
    assert limited_attempts == []


def test_outbox_send_attempt_requires_ready_to_send_draft(client) -> None:
    tenant, token = _bootstrap_owner(client, slug="outbox-send-pending", email="outbox-send-pending@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    _, _, review = _approved_review_task(client, tenant["id"], headers)
    draft = client.post(
        f"/api/human-review-tasks/{review['id']}/outbox-drafts",
        headers=headers,
        json={},
    ).json()

    attempt_res = client.post(
        f"/api/outbox-drafts/{draft['id']}/send-attempts",
        headers=headers,
        json={"delivery_mode": "dry_run"},
    )

    assert attempt_res.status_code == 409


def test_outbox_draft_can_be_canceled_before_confirmation(client) -> None:
    tenant, token = _bootstrap_owner(client, slug="outbox-cancel", email="outbox-cancel@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    _, _, review = _approved_review_task(client, tenant["id"], headers)
    draft = client.post(
        f"/api/human-review-tasks/{review['id']}/outbox-drafts",
        headers=headers,
        json={},
    ).json()

    cancel_res = client.post(
        f"/api/outbox-drafts/{draft['id']}/cancellation",
        headers=headers,
        json={"cancellation_reason": "客户已离开，本次不发送"},
    )
    assert cancel_res.status_code == 200
    canceled = cancel_res.json()
    assert canceled["status"] == "canceled"
    assert canceled["cancellation_reason"] == "客户已离开，本次不发送"
    assert canceled["canceled_by_id"] is not None
    assert canceled["canceled_at"] is not None

    confirm_canceled_res = client.post(
        f"/api/outbox-drafts/{draft['id']}/confirmation",
        headers=headers,
        json={"confirmation_note": "不应该允许确认已取消草稿"},
    )
    assert confirm_canceled_res.status_code == 409


def test_outbox_draft_requires_approved_human_review(client) -> None:
    tenant, token = _bootstrap_owner(client, slug="outbox-open", email="outbox-open@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    conversation, message = _conversation_with_message(client, tenant["id"], headers)
    run = client.post(
        f"/api/conversations/{conversation['id']}/workflow-runs",
        headers=headers,
        json={"trigger_message_id": message["id"], "workflow_type": "customer_reply"},
    ).json()
    review = client.post(
        f"/api/workflow-runs/{run['id']}/human-review-tasks",
        headers=headers,
        json={
            "reason": "low_confidence",
            "risk_level": "medium",
            "draft_reply": "仍待人工确认。",
        },
    ).json()

    create_res = client.post(
        f"/api/human-review-tasks/{review['id']}/outbox-drafts",
        headers=headers,
        json={},
    )
    assert create_res.status_code == 409
