def _bootstrap_owner(
    client, *, slug: str = "workflow-demo", email: str = "workflow-owner@example.com"
) -> tuple[dict, str]:
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
        json={"name": "流程管理员", "email": email, "password": "ChangeMe123!"},
    )
    assert user_res.status_code == 201
    user = user_res.json()

    assign_res = client.post(f"/api/users/{user['id']}/roles", json={"role_id": role["id"]})
    assert assign_res.status_code == 201

    login_res = client.post(
        "/api/auth/login",
        json={
            "tenant_slug": tenant["slug"],
            "email": email,
            "password": "ChangeMe123!",
        },
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
        json={"display_name": "低置信访客"},
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
            "content": "如果超过七天还能退吗？",
        },
    )
    assert message_res.status_code == 201
    return conversation, message_res.json()


def _create_active_knowledge_card(client, tenant_id: int, headers: dict, *, title: str, answer: str) -> dict:
    res = client.post(
        f"/api/tenants/{tenant_id}/knowledge-cards",
        headers=headers,
        json={
            "title": title,
            "question": "超过七天还能退货吗？",
            "answer": answer,
            "tags": ["售后", "退款"],
            "aliases": ["退货", "售后政策", "七天退换货"],
            "status": "active",
        },
    )
    assert res.status_code == 201
    return res.json()


def test_workflow_run_checkpoint_and_human_review_flow(client) -> None:
    tenant, token = _bootstrap_owner(client)
    headers = {"Authorization": f"Bearer {token}"}
    conversation, message = _conversation_with_message(client, tenant["id"], headers)

    no_token_res = client.post(
        f"/api/conversations/{conversation['id']}/workflow-runs",
        json={"trigger_message_id": message["id"], "workflow_type": "customer_reply"},
    )
    assert no_token_res.status_code == 401

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
    assert run["tenant_id"] == tenant["id"]
    assert run["conversation_id"] == conversation["id"]
    assert run["trigger_message_id"] == message["id"]
    assert run["status"] == "running"

    attempt_res = client.post(
        f"/api/workflow-runs/{run['id']}/step-attempts",
        headers=headers,
        json={
            "step_name": "retrieve_knowledge",
            "status": "succeeded",
            "input_summary": "退换货政策问题",
            "output_summary": "命中 2 条候选知识",
        },
    )
    assert attempt_res.status_code == 201
    assert attempt_res.json()["attempt_number"] == 1

    checkpoint_res = client.post(
        f"/api/workflow-runs/{run['id']}/checkpoints",
        headers=headers,
        json={
            "step_name": "risk_check",
            "status": "waiting_human",
            "state_payload": {"confidence": 0.42, "risk": "policy_uncertain"},
            "input_summary": "模型草稿置信度不足",
            "output_summary": "进入人工审核",
        },
    )
    assert checkpoint_res.status_code == 201
    assert checkpoint_res.json()["state_payload"]["confidence"] == 0.42

    review_res = client.post(
        f"/api/workflow-runs/{run['id']}/human-review-tasks",
        headers=headers,
        json={
            "reason": "low_confidence",
            "risk_level": "medium",
            "draft_reply": "超过七天的退货需要结合商品状态和订单政策确认。",
        },
    )
    assert review_res.status_code == 201
    review = review_res.json()
    assert review["status"] == "open"
    assert review["conversation_id"] == conversation["id"]

    open_tasks = client.get(
        f"/api/tenants/{tenant['id']}/human-review-tasks?status=open",
        headers=headers,
    )
    assert open_tasks.status_code == 200
    assert [task["id"] for task in open_tasks.json()] == [review["id"]]

    detail_res = client.get(f"/api/workflow-runs/{run['id']}", headers=headers)
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert detail["status"] == "waiting_human"
    assert detail["current_step"] == "human_review"
    assert len(detail["step_attempts"]) == 1
    assert len(detail["checkpoints"]) == 1
    assert len(detail["human_review_tasks"]) == 1

    resolve_res = client.patch(
        f"/api/human-review-tasks/{review['id']}",
        headers=headers,
        json={
            "decision": "approved",
            "final_reply": "超过七天是否能退，需要看订单对应的售后政策和商品状态，我可以先帮您核对订单信息。",
            "resolution_note": "改为不承诺直接退款",
        },
    )
    assert resolve_res.status_code == 200
    resolved = resolve_res.json()
    assert resolved["status"] == "approved"
    assert resolved["reviewer_id"] is not None
    assert resolved["resolved_at"] is not None

    closed_detail = client.get(f"/api/workflow-runs/{run['id']}", headers=headers).json()
    assert closed_detail["status"] == "completed"
    assert closed_detail["current_step"] == "record_result"

    audit_res = client.get(f"/api/tenants/{tenant['id']}/audit-events", headers=headers)
    actions = [event["action"] for event in audit_res.json()]
    assert "workflow_run.created" in actions
    assert "human_review.approved" in actions


def test_human_review_inbox_enriches_model_and_knowledge_context(client, monkeypatch) -> None:
    monkeypatch.delenv("BAILIAN_API_KEY", raising=False)
    tenant, token = _bootstrap_owner(client)
    headers = {"Authorization": f"Bearer {token}"}
    answer = "超过七天是否可以退货，需要结合订单政策、商品状态和售后规则确认。"
    card = _create_active_knowledge_card(
        client,
        tenant["id"],
        headers,
        title="七天退换货政策",
        answer=answer,
    )
    conversation, message = _conversation_with_message(client, tenant["id"], headers)

    orchestration_res = client.post(
        f"/api/messages/{message['id']}/reply-orchestrations",
        headers=headers,
        json={
            "mode": "model_assisted",
            "intent": "after_sales_policy",
            "knowledge_top_k": 3,
            "model_provider": "bailian",
        },
    )
    assert orchestration_res.status_code == 201
    orchestration = orchestration_res.json()
    assert orchestration["decision"] == "human_review"
    task = orchestration["human_review_task"]
    assert task["reason"] == "model_unavailable"

    inbox_res = client.get(
        f"/api/tenants/{tenant['id']}/human-review-inbox?status=open",
        headers=headers,
    )
    assert inbox_res.status_code == 200
    items = inbox_res.json()
    assert [item["id"] for item in items] == [task["id"]]

    item = items[0]
    assert item["reason"] == "model_unavailable"
    assert item["draft_reply"] == "模型服务暂不可用，请人工根据已命中知识确认后回复。"
    assert item["conversation"]["id"] == conversation["id"]
    assert item["conversation"]["subject"] == "售后政策咨询"
    assert item["trigger_message"]["id"] == message["id"]
    assert item["trigger_message"]["content"] == "如果超过七天还能退吗？"
    assert item["workflow"]["id"] == orchestration["workflow_run"]["id"]
    assert item["workflow"]["status"] == "waiting_human"
    assert item["evidence"]["retrieval_engine"] == "lexical_bm25_v1"
    assert item["evidence"]["draft_source"] == "model_gateway_unavailable"
    assert item["evidence"]["confidence"] == 0.0
    assert item["evidence"]["knowledge_matches"][0]["card_id"] == card["id"]
    assert item["evidence"]["knowledge_matches"][0]["title"] == "七天退换货政策"
    assert item["evidence"]["model_call"]["provider"] == "bailian"
    assert item["evidence"]["model_call"]["status"] == "unavailable"
    assert "API key" in item["evidence"]["model_call"]["error_message"]


def test_resolving_human_review_records_final_reply_in_workflow_state(client) -> None:
    tenant, token = _bootstrap_owner(client)
    headers = {"Authorization": f"Bearer {token}"}
    conversation, message = _conversation_with_message(client, tenant["id"], headers)

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

    resolve_res = client.patch(
        f"/api/human-review-tasks/{review['id']}",
        headers=headers,
        json={
            "decision": "approved",
            "final_reply": "超过七天的订单需要结合商品状态和订单政策核对，我先帮您确认可申请的售后入口。",
            "resolution_note": "坐席改写为不承诺直接退款",
        },
    )
    assert resolve_res.status_code == 200
    resolved = resolve_res.json()
    assert resolved["status"] == "approved"
    assert resolved["final_reply"].startswith("超过七天的订单")

    detail_res = client.get(f"/api/workflow-runs/{run['id']}", headers=headers)
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert detail["status"] == "completed"
    assert detail["current_step"] == "record_result"
    assert detail["state_payload"]["human_review"]["decision"] == "approved"
    assert detail["state_payload"]["human_review"]["task_id"] == review["id"]
    assert detail["state_payload"]["human_review"]["reviewer_id"] is not None
    assert detail["state_payload"]["human_review"]["final_reply"].startswith("超过七天的订单")
    assert detail["state_payload"]["human_review"]["resolution_note"] == "坐席改写为不承诺直接退款"


def test_workflow_run_rejects_cross_tenant_access(client) -> None:
    first, token = _bootstrap_owner(client)
    second, second_token = _bootstrap_owner(
        client,
        slug="workflow-other-tenant",
        email="workflow-other@example.com",
    )
    conversation, message = _conversation_with_message(
        client,
        second["id"],
        {"Authorization": f"Bearer {second_token}"},
    )

    res = client.post(
        f"/api/conversations/{conversation['id']}/workflow-runs",
        headers={"Authorization": f"Bearer {token}"},
        json={"trigger_message_id": message["id"], "workflow_type": "customer_reply"},
    )
    assert first["id"] != second["id"]
    assert res.status_code == 404
