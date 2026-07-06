from app.models import (
    Channel,
    Contact,
    Conversation,
    HumanReviewTask,
    KnowledgeDocument,
    KnowledgeDocumentChunk,
    KnowledgeDocumentPublication,
    KnowledgeEvaluationCase,
    KnowledgeEvaluationRun,
    KnowledgeEvaluationRunCase,
    KnowledgeEvaluationSet,
    KnowledgeGapItem,
    Message,
    WorkflowRun,
)
from test_knowledge_api import _bootstrap_user


def _seed_gap_sources(db_session, tenant_id: int, user_id: int) -> None:
    channel = Channel(
        tenant_id=tenant_id,
        type="wecom",
        name="企业微信测试客服",
        status="active",
    )
    contact = Contact(
        tenant_id=tenant_id,
        display_name="王女士",
        wechat="wx-test-gap",
    )
    db_session.add_all([channel, contact])
    db_session.flush()

    conversation = Conversation(
        tenant_id=tenant_id,
        channel_id=channel.id,
        contact_id=contact.id,
        status="needs_human",
        priority="high",
        subject="退费政策咨询",
    )
    db_session.add(conversation)
    db_session.flush()

    message = Message(
        conversation_id=conversation.id,
        direction="inbound",
        sender_type="customer",
        content="孩子上了两节课后不想继续了，剩余课时能不能退费？",
        external_message_id="msg-gap-001",
    )
    db_session.add(message)
    db_session.flush()

    workflow_run = WorkflowRun(
        tenant_id=tenant_id,
        conversation_id=conversation.id,
        trigger_message_id=message.id,
        status="waiting_human",
        current_step="human_review",
        idempotency_key="gap-workflow-001",
        state_payload={
            "intent": "refund_policy",
            "confidence": 0.19,
            "risk_level": "high",
            "retrieved_knowledge_count": 0,
            "retrieval_mode": "hybrid_bm25_vector_rerank_v1",
            "retrieval_engine": "sqlite_json_vector_store",
            "knowledge_matches": [],
        },
    )
    db_session.add(workflow_run)
    db_session.flush()

    task = HumanReviewTask(
        tenant_id=tenant_id,
        workflow_run_id=workflow_run.id,
        conversation_id=conversation.id,
        message_id=message.id,
        status="open",
        reason="low_confidence",
        risk_level="high",
        draft_reply="当前问题涉及退费政策，知识库没有命中明确规则，建议人工确认后回复。",
    )
    db_session.add(task)

    evaluation_set = KnowledgeEvaluationSet(
        tenant_id=tenant_id,
        name="知识缺口闭环测试题集",
        description="用于验证评测失败能沉淀知识缺口。",
        status="active",
        evaluation_mode="customer_service_retrieval",
        created_by_id=user_id,
        updated_by_id=user_id,
    )
    db_session.add(evaluation_set)
    db_session.flush()

    evaluation_case = KnowledgeEvaluationCase(
        tenant_id=tenant_id,
        evaluation_set_id=evaluation_set.id,
        external_case_id="gap-eval-001",
        source_channel="wecom",
        source_category="退费政策",
        question="课程退费时剩余课时怎么核算？",
        question_type="policy_gap",
        expected_terms=["剩余课时", "退费规则"],
        expected_source_uri="internal://policy/refund",
        expected_document_title="退费政策",
        expected_human_review=True,
        allow_auto_reply=False,
        risk_level="high",
        required_citation=True,
        status="active",
    )
    db_session.add(evaluation_case)
    db_session.flush()

    evaluation_run = KnowledgeEvaluationRun(
        tenant_id=tenant_id,
        evaluation_set_id=evaluation_set.id,
        run_mode="customer_service_retrieval",
        retrieval_mode="hybrid_bm25_vector_rerank_v1",
        vector_engine="deterministic_local_hash_embedding_v1",
        total_cases=1,
        answered_cases=1,
        failed_cases=1,
        average_confidence=0.18,
        summary_payload={"knowledge_gap_rate": 1},
        created_by_id=user_id,
    )
    db_session.add(evaluation_run)
    db_session.flush()

    run_case = KnowledgeEvaluationRunCase(
        tenant_id=tenant_id,
        evaluation_run_id=evaluation_run.id,
        evaluation_case_id=evaluation_case.id,
        question=evaluation_case.question,
        status="failed",
        top_score=0.1,
        top_confidence=0.18,
        citation_present=False,
        expected_terms_found=False,
        matched_terms=[],
        failure_reason="expected_terms_missing",
        result_payload={
            "knowledge_gap": True,
            "retrieval_mode": "hybrid_bm25_vector_rerank_v1",
        },
    )
    db_session.add(run_case)
    db_session.commit()


def test_owner_can_sync_list_and_update_knowledge_gaps(client, db_session) -> None:
    tenant, user, token = _bootstrap_user(
        client,
        slug="knowledge-gap-owner",
        email="knowledge-gap-owner@example.com",
    )
    headers = {"Authorization": f"Bearer {token}"}
    _seed_gap_sources(db_session, tenant["id"], user["id"])

    sync_res = client.post(
        f"/api/tenants/{tenant['id']}/knowledge-gaps/sync",
        headers=headers,
        json={"low_confidence_threshold": 0.45},
    )
    assert sync_res.status_code == 201
    sync = sync_res.json()
    assert sync["created_count"] == 2
    assert sync["existing_count"] == 0
    assert sync["scanned_count"] == 2
    assert {item["source_type"] for item in sync["items"]} == {"human_review", "evaluation_run"}
    assert {item["status"] for item in sync["items"]} == {"open"}
    assert any(item["gap_type"] == "no_knowledge_hit" for item in sync["items"])
    assert any(item["gap_type"] == "expected_terms_missing" for item in sync["items"])

    duplicate_res = client.post(
        f"/api/tenants/{tenant['id']}/knowledge-gaps/sync",
        headers=headers,
        json={"low_confidence_threshold": 0.45},
    )
    assert duplicate_res.status_code == 201
    duplicate = duplicate_res.json()
    assert duplicate["created_count"] == 0
    assert duplicate["existing_count"] == 2

    list_res = client.get(
        f"/api/tenants/{tenant['id']}/knowledge-gaps?status=open&page=1&page_size=10",
        headers=headers,
    )
    assert list_res.status_code == 200
    gap_list = list_res.json()
    assert gap_list["total"] == 2
    human_gap = next(item for item in gap_list["items"] if item["source_type"] == "human_review")

    filtered_res = client.get(
        f"/api/tenants/{tenant['id']}/knowledge-gaps?status=open&severity=high&source_type=evaluation_run&query=课程退费&page=1&page_size=10",
        headers=headers,
    )
    assert filtered_res.status_code == 200
    filtered = filtered_res.json()
    assert filtered["total"] == 1
    assert filtered["items"][0]["source_type"] == "evaluation_run"
    assert filtered["items"][0]["gap_type"] == "expected_terms_missing"

    update_res = client.patch(
        f"/api/knowledge-gaps/{human_gap['id']}",
        headers=headers,
        json={
            "status": "in_progress",
            "assigned_user_id": user["id"],
            "resolution_note": "正在补充退费政策知识卡。",
        },
    )
    assert update_res.status_code == 200
    updated = update_res.json()
    assert updated["status"] == "in_progress"
    assert updated["assigned_user_id"] == user["id"]
    assert updated["resolution_note"] == "正在补充退费政策知识卡。"
    assert updated["resolved_at"] is None

    resolved_res = client.patch(
        f"/api/knowledge-gaps/{human_gap['id']}",
        headers=headers,
        json={"status": "resolved", "resolution_note": "已补充退费政策文档并加入回归评测。"},
    )
    assert resolved_res.status_code == 200
    resolved = resolved_res.json()
    assert resolved["status"] == "resolved"
    assert resolved["resolved_by_id"] == user["id"]
    assert resolved["resolved_at"] is not None


def test_owner_can_turn_knowledge_gap_into_document_draft_and_regression_case(client, db_session) -> None:
    tenant, user, token = _bootstrap_user(
        client,
        slug="knowledge-gap-remediation",
        email="knowledge-gap-remediation@example.com",
    )
    headers = {"Authorization": f"Bearer {token}"}
    _seed_gap_sources(db_session, tenant["id"], user["id"])

    sync_res = client.post(
        f"/api/tenants/{tenant['id']}/knowledge-gaps/sync",
        headers=headers,
        json={"low_confidence_threshold": 0.45},
    )
    assert sync_res.status_code == 201
    gaps = sync_res.json()["items"]
    human_gap = next(item for item in gaps if item["source_type"] == "human_review")
    eval_gap = next(item for item in gaps if item["source_type"] == "evaluation_run")

    draft_res = client.post(f"/api/knowledge-gaps/{human_gap['id']}/document-drafts", headers=headers)
    assert draft_res.status_code == 201
    draft_payload = draft_res.json()
    assert draft_payload["created"] is True
    assert draft_payload["document"]["status"] == "draft"
    assert draft_payload["document"]["source_type"] == "knowledge_gap_remediation"
    assert draft_payload["document"]["source_uri"] == f"knowledge-gap:{human_gap['id']}"
    assert draft_payload["document"]["ingestion_status"] == "indexed"
    assert draft_payload["gap"]["status"] == "in_progress"
    assert draft_payload["gap"]["assigned_user_id"] == user["id"]
    assert draft_payload["gap"]["linked_knowledge_document_id"] == draft_payload["document"]["id"]
    assert "客户问题" in draft_payload["draft_text"]
    assert "待业务审核" in draft_payload["gap"]["resolution_note"]

    duplicate_draft_res = client.post(f"/api/knowledge-gaps/{human_gap['id']}/document-drafts", headers=headers)
    assert duplicate_draft_res.status_code == 201
    duplicate_draft = duplicate_draft_res.json()
    assert duplicate_draft["created"] is False
    assert duplicate_draft["document"]["id"] == draft_payload["document"]["id"]

    regression_res = client.post(f"/api/knowledge-gaps/{eval_gap['id']}/regression-cases", headers=headers)
    assert regression_res.status_code == 201
    regression = regression_res.json()
    assert regression["created"] is True
    assert regression["evaluation_set"]["name"] == "知识缺口回归题库"
    assert regression["evaluation_set"]["status"] == "active"
    assert regression["evaluation_set"]["evaluation_mode"] == "customer_service_retrieval"
    assert regression["evaluation_case"]["external_case_id"] == f"knowledge-gap-{eval_gap['id']}"
    assert regression["evaluation_case"]["question"] == eval_gap["question_excerpt"]
    assert regression["evaluation_case"]["expected_terms"] == ["剩余课时", "退费规则"]
    assert regression["evaluation_case"]["expected_source_uri"] == "internal://policy/refund"
    assert regression["evaluation_case"]["source_channel"] == "wecom"
    assert regression["evaluation_case"]["source_category"] == "退费政策"
    assert regression["evaluation_case"]["required_citation"] is True
    assert regression["gap"]["status"] == "in_progress"
    assert regression["gap"]["evidence_payload"]["remediation"]["regression_evaluation_case_id"] == regression["evaluation_case"]["id"]

    duplicate_regression_res = client.post(f"/api/knowledge-gaps/{eval_gap['id']}/regression-cases", headers=headers)
    assert duplicate_regression_res.status_code == 201
    duplicate_regression = duplicate_regression_res.json()
    assert duplicate_regression["created"] is False
    assert duplicate_regression["evaluation_case"]["id"] == regression["evaluation_case"]["id"]


def test_owner_can_publish_gap_document_after_regression_gate(client, db_session) -> None:
    tenant, user, token = _bootstrap_user(
        client,
        slug="knowledge-gap-publish",
        email="knowledge-gap-publish@example.com",
    )
    headers = {"Authorization": f"Bearer {token}"}
    _seed_gap_sources(db_session, tenant["id"], user["id"])

    sync_res = client.post(
        f"/api/tenants/{tenant['id']}/knowledge-gaps/sync",
        headers=headers,
        json={"low_confidence_threshold": 0.45},
    )
    assert sync_res.status_code == 201
    human_gap = next(item for item in sync_res.json()["items"] if item["source_type"] == "human_review")

    draft_res = client.post(f"/api/knowledge-gaps/{human_gap['id']}/document-drafts", headers=headers)
    assert draft_res.status_code == 201
    document = draft_res.json()["document"]
    assert document["status"] == "draft"

    regression_res = client.post(f"/api/knowledge-gaps/{human_gap['id']}/regression-cases", headers=headers)
    assert regression_res.status_code == 201
    regression_case = regression_res.json()["evaluation_case"]

    check_res = client.post(
        f"/api/knowledge-documents/{document['id']}/publish-checks",
        headers=headers,
        json={"low_confidence_threshold": 0.1},
    )
    assert check_res.status_code == 201
    check_payload = check_res.json()
    assert check_payload["can_publish"] is True
    assert check_payload["published"] is False
    assert check_payload["document"]["status"] == "draft"
    assert check_payload["checked_case_ids"] == [regression_case["id"]]
    assert check_payload["case_results"][0]["blocking"] is False
    assert check_payload["checks"]["search_status"] == "draft"

    check_history_res = client.get(f"/api/knowledge-documents/{document['id']}/publications", headers=headers)
    assert check_history_res.status_code == 200
    check_history = check_history_res.json()
    assert check_history["total"] == 1
    assert check_history["items"][0]["publication_type"] == "publish_check"
    assert check_history["items"][0]["status"] == "passed"
    assert check_history["items"][0]["checked_case_ids"] == [regression_case["id"]]
    assert check_history["items"][0]["case_results"][0]["evaluation_case_id"] == regression_case["id"]

    publish_res = client.post(
        f"/api/knowledge-documents/{document['id']}/publication",
        headers=headers,
        json={"low_confidence_threshold": 0.1},
    )
    assert publish_res.status_code == 201
    publish_payload = publish_res.json()
    assert publish_payload["can_publish"] is True
    assert publish_payload["published"] is True
    assert publish_payload["document"]["status"] == "active"
    assert publish_payload["gap"]["status"] == "resolved"
    assert publish_payload["gap"]["evidence_payload"]["remediation"]["published_document_id"] == document["id"]
    assert publish_payload["evaluation_run"]["id"] > 0

    publish_history_res = client.get(f"/api/knowledge-documents/{document['id']}/publications", headers=headers)
    assert publish_history_res.status_code == 200
    publish_history = publish_history_res.json()
    assert publish_history["total"] == 2
    assert publish_history["items"][0]["publication_type"] == "publish"
    assert publish_history["items"][0]["status"] == "published"
    assert publish_history["items"][0]["from_status"] == "draft"
    assert publish_history["items"][0]["to_status"] == "active"
    assert publish_history["items"][0]["evaluation_run_id"] == publish_payload["evaluation_run"]["id"]
    assert publish_history["items"][0]["document_snapshot"]["status"] == "draft"
    assert "raw_text_hash" in publish_history["items"][0]["document_snapshot"]

    chunks = db_session.query(KnowledgeDocumentChunk).filter_by(document_id=document["id"]).all()
    assert chunks
    assert {chunk.status for chunk in chunks} == {"active"}

    rollback_res = client.post(
        f"/api/knowledge-documents/{document['id']}/rollback",
        headers=headers,
        json={"rollback_reason": "测试发现知识仍需复核，先退回草稿。"},
    )
    assert rollback_res.status_code == 201
    rollback_payload = rollback_res.json()
    assert rollback_payload["publication_type"] == "rollback"
    assert rollback_payload["status"] == "rolled_back"
    assert rollback_payload["from_status"] == "active"
    assert rollback_payload["to_status"] == "draft"
    assert rollback_payload["rollback_target_publication_id"] == publish_history["items"][0]["id"]
    assert rollback_payload["checks"]["content_restored"] is False

    db_session.expire_all()
    rolled_back_document = db_session.get(KnowledgeDocument, document["id"])
    assert rolled_back_document is not None
    assert rolled_back_document.status == "draft"
    chunks = db_session.query(KnowledgeDocumentChunk).filter_by(document_id=document["id"]).all()
    assert {chunk.status for chunk in chunks} == {"draft"}
    gap = db_session.get(KnowledgeGapItem, human_gap["id"])
    assert gap is not None
    assert gap.status == "in_progress"

    final_history = (
        db_session.query(KnowledgeDocumentPublication)
        .filter_by(document_id=document["id"])
        .order_by(KnowledgeDocumentPublication.id.desc())
        .all()
    )
    assert [item.publication_type for item in final_history] == ["rollback", "publish", "publish_check"]


def test_knowledge_document_publication_blocks_without_regression_case(client) -> None:
    tenant, _, token = _bootstrap_user(
        client,
        slug="knowledge-publish-blocked",
        email="knowledge-publish-blocked@example.com",
    )
    headers = {"Authorization": f"Bearer {token}"}
    document_res = client.post(
        f"/api/tenants/{tenant['id']}/knowledge-documents",
        headers=headers,
        json={
            "title": "没有回归题的草稿",
            "source_type": "manual_document",
            "source_uri": "internal://draft/no-regression",
            "raw_text": "这是一份还没有绑定客服回归题的知识草稿，不能直接进入正式检索范围。",
            "status": "draft",
            "chunk_size": 120,
        },
    )
    assert document_res.status_code == 201
    document = document_res.json()

    publish_res = client.post(
        f"/api/knowledge-documents/{document['id']}/publication",
        headers=headers,
        json={},
    )
    assert publish_res.status_code == 201
    payload = publish_res.json()
    assert payload["can_publish"] is False
    assert payload["published"] is False
    assert "missing_regression_set" in payload["blocking_reasons"]
    assert "missing_regression_case" in payload["blocking_reasons"]
    assert payload["document"]["status"] == "draft"

    publication_history_res = client.get(f"/api/knowledge-documents/{document['id']}/publications", headers=headers)
    assert publication_history_res.status_code == 200
    publication_history = publication_history_res.json()
    assert publication_history["total"] == 1
    assert publication_history["items"][0]["publication_type"] == "publish"
    assert publication_history["items"][0]["status"] == "blocked"
    assert "missing_regression_case" in publication_history["items"][0]["blocking_reasons"]


def test_knowledge_gaps_enforce_manager_role_and_tenant_boundary(client, db_session) -> None:
    tenant, user, owner_token = _bootstrap_user(
        client,
        slug="knowledge-gap-boundary",
        email="knowledge-gap-boundary-owner@example.com",
    )
    owner_headers = {"Authorization": f"Bearer {owner_token}"}
    _seed_gap_sources(db_session, tenant["id"], user["id"])
    sync_res = client.post(
        f"/api/tenants/{tenant['id']}/knowledge-gaps/sync",
        headers=owner_headers,
        json={},
    )
    assert sync_res.status_code == 201
    gap_id = sync_res.json()["items"][0]["id"]

    agent_role = client.post(
        f"/api/tenants/{tenant['id']}/roles",
        headers=owner_headers,
        json={"code": "agent", "name": "客服坐席"},
    ).json()
    agent_res = client.post(
        f"/api/tenants/{tenant['id']}/users",
        headers=owner_headers,
        json={"name": "客服坐席", "email": "knowledge-gap-agent@example.com", "password": "ChangeMe123!"},
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
            "email": "knowledge-gap-agent@example.com",
            "password": "ChangeMe123!",
        },
    )
    agent_headers = {"Authorization": f"Bearer {login_res.json()['access_token']}"}

    agent_list_res = client.get(f"/api/tenants/{tenant['id']}/knowledge-gaps", headers=agent_headers)
    assert agent_list_res.status_code == 403
    agent_update_res = client.patch(
        f"/api/knowledge-gaps/{gap_id}",
        headers=agent_headers,
        json={"status": "resolved"},
    )
    assert agent_update_res.status_code == 403
    agent_draft_res = client.post(f"/api/knowledge-gaps/{gap_id}/document-drafts", headers=agent_headers)
    assert agent_draft_res.status_code == 403
    agent_regression_res = client.post(f"/api/knowledge-gaps/{gap_id}/regression-cases", headers=agent_headers)
    assert agent_regression_res.status_code == 403

    other_tenant, _, other_token = _bootstrap_user(
        client,
        slug="knowledge-gap-other",
        email="knowledge-gap-other@example.com",
    )
    other_headers = {"Authorization": f"Bearer {other_token}"}
    cross_list_res = client.get(f"/api/tenants/{tenant['id']}/knowledge-gaps", headers=other_headers)
    assert cross_list_res.status_code == 404
    cross_update_res = client.patch(
        f"/api/knowledge-gaps/{gap_id}",
        headers=other_headers,
        json={"status": "resolved"},
    )
    assert cross_update_res.status_code == 404
    cross_draft_res = client.post(f"/api/knowledge-gaps/{gap_id}/document-drafts", headers=other_headers)
    assert cross_draft_res.status_code == 404
    cross_regression_res = client.post(f"/api/knowledge-gaps/{gap_id}/regression-cases", headers=other_headers)
    assert cross_regression_res.status_code == 404
    own_empty_list_res = client.get(f"/api/tenants/{other_tenant['id']}/knowledge-gaps", headers=other_headers)
    assert own_empty_list_res.status_code == 200
    assert own_empty_list_res.json()["total"] == 0
