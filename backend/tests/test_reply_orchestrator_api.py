from sqlalchemy import select

from app.models import ModelCallRecord, ReplyCitationSnapshot


def _bootstrap_owner(client, slug: str, email: str) -> tuple[dict, str]:
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
        json={"name": "客服主管", "email": email, "password": "ChangeMe123!"},
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


def _conversation_with_message(
    client,
    tenant_id: int,
    headers: dict,
    *,
    content: str = "超过七天还能退货吗？",
    direction: str = "inbound",
) -> tuple[dict, dict]:
    channel = client.post(
        f"/api/tenants/{tenant_id}/channels",
        json={"type": "web", "name": "官网客服", "reply_mode": "assist", "status": "active"},
    ).json()
    contact = client.post(
        f"/api/tenants/{tenant_id}/contacts",
        json={"display_name": "测试访客"},
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
        json={"direction": direction, "sender_type": "visitor", "content": content},
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


def _create_active_knowledge_document(client, tenant_id: int, headers: dict) -> dict:
    res = client.post(
        f"/api/tenants/{tenant_id}/knowledge-documents",
        headers=headers,
        json={
            "title": "保修政策手册",
            "source_type": "manual_document",
            "source_uri": "internal://docs/warranty-v1",
            "raw_text": (
                "标准产品保修期为三年。保修期内如果出现非人为质量问题，"
                "可以安排检测、维修或换新。人为损坏不属于免费保修范围。"
            ),
            "tags": ["保修", "售后"],
            "status": "active",
            "chunk_size": 80,
        },
    )
    assert res.status_code == 201
    return res.json()


def test_reply_orchestration_completes_high_confidence_low_risk_message(client) -> None:
    tenant, token = _bootstrap_owner(client, "reply-auto", "reply-auto@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    conversation, message = _conversation_with_message(client, tenant["id"], headers)

    no_token_res = client.post(
        f"/api/messages/{message['id']}/reply-orchestrations",
        json={
            "intent": "after_sales_policy",
            "retrieved_knowledge_count": 3,
            "draft_reply": "超过七天是否可以退货，需要结合订单政策和商品状态确认。我可以先帮您核对订单。",
            "confidence": 0.88,
            "risk_level": "low",
        },
    )
    assert no_token_res.status_code == 401

    res = client.post(
        f"/api/messages/{message['id']}/reply-orchestrations",
        headers=headers,
        json={
            "intent": "after_sales_policy",
            "retrieved_knowledge_count": 3,
            "draft_reply": "超过七天是否可以退货，需要结合订单政策和商品状态确认。我可以先帮您核对订单。",
            "confidence": 0.88,
            "risk_level": "low",
        },
    )

    assert res.status_code == 201
    result = res.json()
    assert result["decision"] == "completed"
    assert result["reason"] == "high_confidence_low_risk"
    assert result["human_review_task"] is None
    assert result["draft_reply"].startswith("超过七天")
    assert result["workflow_run"]["tenant_id"] == tenant["id"]
    assert result["workflow_run"]["conversation_id"] == conversation["id"]
    assert result["workflow_run"]["trigger_message_id"] == message["id"]
    assert result["workflow_run"]["status"] == "completed"
    assert result["workflow_run"]["current_step"] == "record_result"

    detail_res = client.get(f"/api/workflow-runs/{result['workflow_run']['id']}", headers=headers)
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert [attempt["step_name"] for attempt in detail["step_attempts"]] == [
        "classify_intent",
        "retrieve_knowledge",
        "draft_reply",
        "risk_check",
    ]
    assert detail["checkpoints"][0]["status"] == "completed"
    assert detail["checkpoints"][0]["state_payload"]["confidence"] == 0.88


def test_reply_orchestration_can_generate_draft_from_knowledge_search(client) -> None:
    tenant, token = _bootstrap_owner(client, "reply-knowledge", "reply-knowledge@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    answer = "超过七天是否可以退货，需要结合订单政策、商品状态和售后规则确认。"
    card = _create_active_knowledge_card(
        client,
        tenant["id"],
        headers,
        title="七天退换货政策",
        answer=answer,
    )
    _, message = _conversation_with_message(client, tenant["id"], headers, content="客户超过七天申请退货怎么办？")

    res = client.post(
        f"/api/messages/{message['id']}/reply-orchestrations",
        headers=headers,
        json={
            "mode": "knowledge_search",
            "intent": "after_sales_policy",
            "knowledge_top_k": 3,
        },
    )

    assert res.status_code == 201
    result = res.json()
    assert result["decision"] == "completed"
    assert result["reason"] == "high_confidence_low_risk"
    assert result["draft_reply"] == answer
    assert result["knowledge_matches"][0]["card_id"] == card["id"]
    assert result["knowledge_matches"][0]["title"] == "七天退换货政策"

    detail = client.get(f"/api/workflow-runs/{result['workflow_run']['id']}", headers=headers).json()
    assert detail["state_payload"]["retrieval_mode"] == "knowledge_search"
    assert detail["state_payload"]["retrieved_knowledge_count"] == 1
    assert detail["state_payload"]["knowledge_matches"][0]["card_id"] == card["id"]
    assert detail["step_attempts"][1]["step_name"] == "retrieve_knowledge"
    assert "lexical_bm25_v1" in detail["step_attempts"][1]["output_summary"]


def test_reply_orchestration_can_use_document_rag_chunk_with_citation(client) -> None:
    tenant, token = _bootstrap_owner(client, "reply-document-rag", "reply-document-rag@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    document = _create_active_knowledge_document(client, tenant["id"], headers)
    _, message = _conversation_with_message(client, tenant["id"], headers, content="产品保修期多久？")

    res = client.post(
        f"/api/messages/{message['id']}/reply-orchestrations",
        headers=headers,
        json={
            "mode": "document_rag",
            "intent": "warranty_policy",
            "knowledge_top_k": 3,
        },
    )

    assert res.status_code == 201
    result = res.json()
    assert result["decision"] == "completed"
    assert result["reason"] == "high_confidence_low_risk"
    assert "三年" in result["draft_reply"]
    assert result["knowledge_matches"][0]["source_kind"] == "document_chunk"
    assert result["knowledge_matches"][0]["document_id"] == document["id"]
    assert result["knowledge_matches"][0]["chunk_id"] is not None
    assert result["knowledge_matches"][0]["source_uri"] == "internal://docs/warranty-v1"

    detail = client.get(f"/api/workflow-runs/{result['workflow_run']['id']}", headers=headers).json()
    assert detail["state_payload"]["retrieval_mode"] == "document_rag"
    assert detail["state_payload"]["retrieval_engine"] == "hybrid_bm25_vector_rerank_v1"
    assert detail["state_payload"]["knowledge_matches"][0]["source_kind"] == "document_chunk"
    assert detail["state_payload"]["knowledge_matches"][0]["citation"]["source_uri"] == "internal://docs/warranty-v1"


def test_reply_orchestration_creates_human_review_for_low_confidence(client) -> None:
    tenant, token = _bootstrap_owner(client, "reply-review", "reply-review@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    _, message = _conversation_with_message(client, tenant["id"], headers, content="你们这个退款到底怎么保证？")

    res = client.post(
        f"/api/messages/{message['id']}/reply-orchestrations",
        headers=headers,
        json={
            "intent": "refund_dispute",
            "retrieved_knowledge_count": 1,
            "draft_reply": "退款需要结合订单状态进一步确认。",
            "confidence": 0.46,
            "risk_level": "medium",
        },
    )

    assert res.status_code == 201
    result = res.json()
    assert result["decision"] == "human_review"
    assert result["reason"] == "low_confidence"
    assert result["workflow_run"]["status"] == "waiting_human"
    assert result["workflow_run"]["current_step"] == "human_review"
    assert result["human_review_task"]["status"] == "open"
    assert result["human_review_task"]["reason"] == "low_confidence"
    assert result["human_review_task"]["risk_level"] == "medium"
    assert result["human_review_task"]["draft_reply"] == "退款需要结合订单状态进一步确认。"

    open_tasks = client.get(
        f"/api/tenants/{tenant['id']}/human-review-tasks?status=open",
        headers=headers,
    )
    assert open_tasks.status_code == 200
    assert [task["id"] for task in open_tasks.json()] == [result["human_review_task"]["id"]]


def test_reply_orchestration_sends_no_knowledge_search_hit_to_human_review(client) -> None:
    tenant, token = _bootstrap_owner(client, "reply-search-empty", "reply-search-empty@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    _, message = _conversation_with_message(client, tenant["id"], headers, content="你们有没有火星基地专属套餐？")

    res = client.post(
        f"/api/messages/{message['id']}/reply-orchestrations",
        headers=headers,
        json={
            "mode": "knowledge_search",
            "intent": "unknown_product_policy",
            "knowledge_top_k": 3,
        },
    )

    assert res.status_code == 201
    result = res.json()
    assert result["decision"] == "human_review"
    assert result["reason"] == "no_knowledge_hit"
    assert result["knowledge_matches"] == []
    assert result["workflow_run"]["status"] == "waiting_human"
    assert result["human_review_task"]["reason"] == "no_knowledge_hit"


def test_reply_orchestration_can_generate_model_assisted_draft_from_knowledge(client, db_session) -> None:
    tenant, token = _bootstrap_owner(client, "reply-model", "reply-model@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    answer = "超过七天是否可以退货，需要结合订单政策、商品状态和售后规则确认。"
    card = _create_active_knowledge_card(
        client,
        tenant["id"],
        headers,
        title="七天退换货政策",
        answer=answer,
    )
    _, message = _conversation_with_message(client, tenant["id"], headers, content="客户超过七天申请退货怎么办？")

    res = client.post(
        f"/api/messages/{message['id']}/reply-orchestrations",
        headers=headers,
        json={
            "mode": "model_assisted",
            "intent": "after_sales_policy",
            "knowledge_top_k": 3,
            "model_provider": "deterministic",
        },
    )

    assert res.status_code == 201
    result = res.json()
    assert result["decision"] == "completed"
    assert result["reason"] == "high_confidence_low_risk"
    assert result["draft_reply"] != answer
    assert "根据已审核知识" in result["draft_reply"]
    assert "超过七天" in result["draft_reply"]
    assert result["knowledge_matches"][0]["card_id"] == card["id"]
    assert result["model_call"]["provider"] == "deterministic"
    assert result["model_call"]["status"] == "succeeded"
    assert result["model_call"]["prompt_summary"] == "intent=after_sales_policy, knowledge_matches=1"

    detail = client.get(f"/api/workflow-runs/{result['workflow_run']['id']}", headers=headers).json()
    assert detail["state_payload"]["draft_source"] == "model_gateway"
    assert detail["state_payload"]["model_call"]["provider"] == "deterministic"
    assert detail["state_payload"]["model_call"]["model"] == "deterministic-local-draft-v1"
    assert detail["state_payload"]["model_call"]["route_name"] == "explicit_provider"
    assert detail["state_payload"]["model_call"]["complexity"] == "standard"
    assert detail["state_payload"]["provenance_id"].startswith(f"rp_t{tenant['id']}_m{message['id']}_")
    assert "model_gateway/deterministic" in detail["step_attempts"][2]["input_summary"]

    model_record = db_session.scalar(
        select(ModelCallRecord).where(
            ModelCallRecord.tenant_id == tenant["id"],
            ModelCallRecord.provenance_id == detail["state_payload"]["provenance_id"],
        )
    )
    assert model_record is not None
    assert model_record.workflow_run_id == result["workflow_run"]["id"]
    assert model_record.provider == "deterministic"
    assert model_record.model == "deterministic-local-draft-v1"
    assert model_record.status == "succeeded"
    assert model_record.total_units > 0
    assert model_record.raw_text_logged is False
    assert model_record.pricing_source == "deterministic_no_external_cost"

    citation_snapshot = db_session.scalar(
        select(ReplyCitationSnapshot).where(
            ReplyCitationSnapshot.tenant_id == tenant["id"],
            ReplyCitationSnapshot.provenance_id == detail["state_payload"]["provenance_id"],
        )
    )
    assert citation_snapshot is not None
    assert citation_snapshot.workflow_run_id == result["workflow_run"]["id"]
    assert citation_snapshot.source_kind == "knowledge_card"
    assert citation_snapshot.knowledge_card_id == card["id"]


def test_reply_orchestration_sends_unavailable_model_provider_to_human_review(client, monkeypatch) -> None:
    monkeypatch.delenv("BAILIAN_API_KEY", raising=False)
    tenant, token = _bootstrap_owner(client, "reply-model-missing", "reply-model-missing@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    answer = "超过七天是否可以退货，需要结合订单政策、商品状态和售后规则确认。"
    _create_active_knowledge_card(
        client,
        tenant["id"],
        headers,
        title="七天退换货政策",
        answer=answer,
    )
    _, message = _conversation_with_message(client, tenant["id"], headers, content="客户超过七天申请退货怎么办？")

    res = client.post(
        f"/api/messages/{message['id']}/reply-orchestrations",
        headers=headers,
        json={
            "mode": "model_assisted",
            "intent": "after_sales_policy",
            "knowledge_top_k": 3,
            "model_provider": "bailian",
        },
    )

    assert res.status_code == 201
    result = res.json()
    assert result["decision"] == "human_review"
    assert result["reason"] == "model_unavailable"
    assert result["knowledge_matches"]
    assert result["model_call"]["provider"] == "bailian"
    assert result["model_call"]["status"] == "unavailable"
    assert "API key" in result["model_call"]["error_message"]
    assert result["human_review_task"]["reason"] == "model_unavailable"


def test_reply_orchestration_blocks_explicit_provider_when_single_call_budget_is_exceeded(
    client,
    db_session,
    monkeypatch,
) -> None:
    def fail_urlopen(*args, **kwargs):  # pragma: no cover - the assertion is that this is never reached
        raise AssertionError("external model call should be blocked by budget before urlopen")

    monkeypatch.setenv("BAILIAN_API_KEY", "test-bailian-key")
    monkeypatch.setenv("MODEL_PRICE_BAILIAN_STANDARD_PER_1K_UNITS", "10")
    monkeypatch.setenv("MODEL_BUDGET_SINGLE_CALL_LIMIT_CNY", "0.001")
    monkeypatch.setattr("app.services.model_gateway.urlopen", fail_urlopen)

    tenant, token = _bootstrap_owner(client, "reply-budget-block", "reply-budget-block@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    _create_active_knowledge_card(
        client,
        tenant["id"],
        headers,
        title="七天退换货政策",
        answer="超过七天是否可以退货，需要结合订单政策、商品状态和售后规则确认。",
    )
    _, message = _conversation_with_message(client, tenant["id"], headers, content="客户超过七天申请退货怎么办？")

    res = client.post(
        f"/api/messages/{message['id']}/reply-orchestrations",
        headers=headers,
        json={
            "mode": "model_assisted",
            "intent": "after_sales_policy",
            "knowledge_top_k": 3,
            "model_provider": "bailian",
        },
    )

    assert res.status_code == 201
    result = res.json()
    assert result["decision"] == "human_review"
    assert result["reason"] == "model_budget_limited"
    assert result["draft_reply"].startswith("当前模型预算不足")
    assert result["model_call"]["provider"] == "bailian"
    assert result["model_call"]["status"] == "budget_blocked"
    assert result["model_call"]["estimated_cost"] == 0
    assert result["model_call"]["budget_reason"] == "single_call_budget_exceeded"
    assert result["model_call"]["budget_action"] == "budget_blocked"
    detail = client.get(f"/api/workflow-runs/{result['workflow_run']['id']}", headers=headers).json()
    assert detail["state_payload"]["draft_source"] == "model_budget_limited"

    record = db_session.scalar(
        select(ModelCallRecord).where(
            ModelCallRecord.tenant_id == tenant["id"],
            ModelCallRecord.workflow_run_id == result["workflow_run"]["id"],
        )
    )
    assert record is not None
    assert record.status == "budget_blocked"
    assert record.estimated_cost == 0
    assert record.pricing_source == "budget_block_no_external_cost"
    assert record.degrade_action == "budget_blocked"
    assert record.budget_policy_snapshot["single_call_limit"] == 0.001
    assert record.budget_policy_snapshot["estimated_call_cost"] > 0
    assert record.budget_policy_snapshot["pricing_source"] == "operator_config_default_estimate_not_provider_bill"
    assert record.metadata_payload["budget_reason"] == "single_call_budget_exceeded"


def test_reply_orchestration_auto_route_degrades_to_deterministic_when_budget_is_exceeded(
    client,
    db_session,
    monkeypatch,
) -> None:
    def fail_urlopen(*args, **kwargs):  # pragma: no cover - the assertion is that this is never reached
        raise AssertionError("auto route should degrade before external urlopen")

    monkeypatch.setenv("BAILIAN_API_KEY", "test-bailian-key")
    monkeypatch.setenv("MODEL_PRICE_BAILIAN_STANDARD_PER_1K_UNITS", "10")
    monkeypatch.setenv("MODEL_BUDGET_SINGLE_CALL_LIMIT_CNY", "0.001")
    monkeypatch.setattr("app.services.model_gateway.urlopen", fail_urlopen)

    tenant, token = _bootstrap_owner(client, "reply-budget-degrade", "reply-budget-degrade@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    _create_active_knowledge_card(
        client,
        tenant["id"],
        headers,
        title="七天退换货政策",
        answer="超过七天是否可以退货，需要结合订单政策、商品状态和售后规则确认。",
    )
    _, message = _conversation_with_message(client, tenant["id"], headers, content="客户超过七天申请退货怎么办？")

    res = client.post(
        f"/api/messages/{message['id']}/reply-orchestrations",
        headers=headers,
        json={
            "mode": "model_assisted",
            "intent": "after_sales_policy",
            "knowledge_top_k": 3,
            "model_provider": "auto",
        },
    )

    assert res.status_code == 201
    result = res.json()
    assert result["decision"] == "human_review"
    assert result["reason"] == "model_budget_limited"
    assert result["draft_reply"].startswith("根据已审核知识")
    assert result["model_call"]["provider"] == "deterministic"
    assert result["model_call"]["status"] == "degraded"
    assert result["model_call"]["budget_action"] == "budget_degraded_to_deterministic"
    assert "budget_limited_original_provider=bailian" in result["model_call"]["route_reasons"]

    record = db_session.scalar(
        select(ModelCallRecord).where(
            ModelCallRecord.tenant_id == tenant["id"],
            ModelCallRecord.workflow_run_id == result["workflow_run"]["id"],
        )
    )
    assert record is not None
    assert record.provider == "deterministic"
    assert record.status == "degraded"
    assert record.estimated_cost == 0
    assert record.pricing_source == "deterministic_no_external_cost"
    assert record.degrade_action == "budget_degraded_to_deterministic"
    assert record.budget_policy_snapshot["estimated_call_cost"] > 0


def test_reply_orchestration_auto_route_records_model_tier_and_human_review_guard(client, monkeypatch) -> None:
    monkeypatch.delenv("BAILIAN_API_KEY", raising=False)
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    tenant, token = _bootstrap_owner(client, "reply-model-route", "reply-model-route@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    _create_active_knowledge_card(
        client,
        tenant["id"],
        headers,
        title="投诉赔付边界",
        answer="涉及赔付、法律承诺或投诉升级时，只能说明会记录并由专人核实，不能直接承诺赔偿。",
    )
    _, message = _conversation_with_message(
        client,
        tenant["id"],
        headers,
        content="客户投诉要起诉并要求我们马上承诺赔偿，应该怎么回复？",
    )

    res = client.post(
        f"/api/messages/{message['id']}/reply-orchestrations",
        headers=headers,
        json={
            "mode": "model_assisted",
            "intent": "complaint_legal_refund_dispute",
            "knowledge_top_k": 3,
            "risk_level": "high",
            "model_provider": "auto",
        },
    )

    assert res.status_code == 201
    result = res.json()
    assert result["decision"] == "human_review"
    assert result["reason"] == "risk_level_high"
    assert result["model_call"]["provider"] == "deterministic"
    assert result["model_call"]["route_name"] == "deterministic_safe_fallback"
    assert result["model_call"]["complexity"] == "high_risk"
    assert result["model_call"]["target_model_tier"] == "premium"
    assert result["model_call"]["human_review_required"] is True
    assert "no_external_model_key_configured" in result["model_call"]["route_reasons"]

    detail = client.get(f"/api/workflow-runs/{result['workflow_run']['id']}", headers=headers).json()
    assert detail["state_payload"]["model_call"]["fallback_chain"][0].startswith("bailian:qwen3.7-max")


def test_reply_orchestration_requires_human_review_when_no_knowledge_hit(client) -> None:
    tenant, token = _bootstrap_owner(client, "reply-no-knowledge", "reply-no-knowledge@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    _, message = _conversation_with_message(client, tenant["id"], headers, content="你们有没有一个很特殊的隐藏套餐？")

    res = client.post(
        f"/api/messages/{message['id']}/reply-orchestrations",
        headers=headers,
        json={
            "intent": "unknown_product_policy",
            "retrieved_knowledge_count": 0,
            "draft_reply": "我需要进一步确认这个问题。",
            "confidence": 0.91,
            "risk_level": "low",
        },
    )

    assert res.status_code == 201
    result = res.json()
    assert result["decision"] == "human_review"
    assert result["reason"] == "no_knowledge_hit"
    assert result["workflow_run"]["status"] == "waiting_human"
    assert result["human_review_task"]["reason"] == "no_knowledge_hit"


def test_reply_orchestration_rejects_cross_tenant_and_outbound_messages(client) -> None:
    first, token = _bootstrap_owner(client, "reply-first", "reply-first@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    second, second_token = _bootstrap_owner(client, "reply-second", "reply-second@example.com")
    second_headers = {"Authorization": f"Bearer {second_token}"}
    _, other_message = _conversation_with_message(client, second["id"], second_headers)

    cross_tenant_res = client.post(
        f"/api/messages/{other_message['id']}/reply-orchestrations",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "intent": "after_sales_policy",
            "retrieved_knowledge_count": 2,
            "draft_reply": "我来帮您核对。",
            "confidence": 0.9,
            "risk_level": "low",
        },
    )
    assert first["id"] != second["id"]
    assert cross_tenant_res.status_code == 404

    _, outbound_message = _conversation_with_message(
        client,
        first["id"],
        headers,
        content="这是一条坐席已经发出的消息。",
        direction="outbound",
    )
    outbound_res = client.post(
        f"/api/messages/{outbound_message['id']}/reply-orchestrations",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "intent": "agent_reply",
            "retrieved_knowledge_count": 0,
            "draft_reply": "不应对出站消息再编排回复。",
            "confidence": 0.91,
            "risk_level": "low",
        },
    )
    assert outbound_res.status_code == 409
