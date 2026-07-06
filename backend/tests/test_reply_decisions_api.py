from sqlalchemy import select

from app.models import ReplyCitationSnapshot


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
    content: str,
    direction: str = "inbound",
) -> tuple[dict, dict]:
    channel_res = client.post(
        f"/api/tenants/{tenant_id}/channels",
        json={"type": "web", "name": "官网客服", "reply_mode": "assist", "status": "active"},
    )
    assert channel_res.status_code == 201
    channel = channel_res.json()
    contact_res = client.post(
        f"/api/tenants/{tenant_id}/contacts",
        json={"display_name": "测试访客"},
    )
    assert contact_res.status_code == 201
    contact = contact_res.json()
    conversation_res = client.post(
        f"/api/tenants/{tenant_id}/conversations",
        headers=headers,
        json={
            "channel_id": channel["id"],
            "contact_id": contact["id"],
            "subject": "入门验证咨询",
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


def _create_object_card(client, tenant_id: int, headers: dict) -> tuple[dict, dict]:
    object_res = client.post(
        f"/api/tenants/{tenant_id}/business-objects",
        headers=headers,
        json={
            "type": "product",
            "title": "AI 客服入门验证包",
            "summary": "适合先验证官网客服、核心问答、留资和人工接管流程。",
            "aliases": ["入门验证包", "Lite A", "官网客服试点"],
            "attrs_json": {"delivery_days": 7},
            "status": "active",
        },
    )
    assert object_res.status_code == 201
    business_object = object_res.json()
    card_res = client.post(
        f"/api/business-objects/{business_object['id']}/knowledge-cards",
        headers=headers,
        json={
            "question": "入门验证包适合什么客户？",
            "answer": "入门验证包适合先验证官网客服、核心问题自动回复、线索收集和人工接管流程的中小企业。",
            "trigger_keywords": ["入门验证包", "官网客服", "先试用"],
            "scope": {"channels": ["web"], "reply_mode": "auto_with_handoff"},
            "source": "manual",
            "status": "active",
        },
    )
    assert card_res.status_code == 201
    return business_object, card_res.json()


def test_reply_decision_marks_high_confidence_object_card_as_ready_draft_only(client, db_session) -> None:
    tenant, token = _bootstrap_owner(client, "reply-decision-ready", "reply-decision-ready@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    business_object, card = _create_object_card(client, tenant["id"], headers)
    conversation, message = _conversation_with_message(
        client,
        tenant["id"],
        headers,
        content="入门验证包适合什么客户？",
    )

    res = client.post(
        f"/api/messages/{message['id']}/reply-decisions",
        headers=headers,
        json={},
    )

    assert res.status_code == 201
    result = res.json()
    assert result["tenant_id"] == tenant["id"]
    assert result["conversation_id"] == conversation["id"]
    assert result["message_id"] == message["id"]
    assert result["business_object_id"] == business_object["id"]
    assert result["object_knowledge_card_id"] == card["id"]
    assert result["provenance_id"].startswith(f"rp_t{tenant['id']}_m{message['id']}_")
    assert result["state"] == "auto_reply_ready"
    assert result["reason"] == "object_card_high_confidence"
    assert result["delivery_mode"] == "draft_only"
    assert result["external_write_allowed"] is False
    assert result["confidence"] >= 0.72
    assert result["draft_reply"].startswith("入门验证包适合")
    assert "入门验证包" in result["matched_terms"]
    assert result["decision_payload"]["external_write_allowed_after_gate"] is False
    assert result["decision_payload"]["provenance"]["provenance_id"] == result["provenance_id"]
    assert result["decision_payload"]["provenance"]["reply_decision_id"] == result["id"]

    snapshot = db_session.scalar(
        select(ReplyCitationSnapshot).where(
            ReplyCitationSnapshot.tenant_id == tenant["id"],
            ReplyCitationSnapshot.provenance_id == result["provenance_id"],
        )
    )
    assert snapshot is not None
    assert snapshot.source_kind == "object_knowledge_card"
    assert snapshot.object_knowledge_card_id == card["id"]
    assert snapshot.reply_decision_id == result["id"]
    assert snapshot.content_hash
    assert snapshot.citation_payload["answer_hash"] == snapshot.content_hash

    idempotent_res = client.post(
        f"/api/messages/{message['id']}/reply-decisions",
        headers=headers,
        json={},
    )
    assert idempotent_res.status_code == 201
    assert idempotent_res.json()["id"] == result["id"]
    assert idempotent_res.json()["provenance_id"] == result["provenance_id"]

    listed_res = client.get(
        f"/api/tenants/{tenant['id']}/reply-decisions?state=auto_reply_ready",
        headers=headers,
    )
    assert listed_res.status_code == 200
    listed = listed_res.json()
    assert listed["total"] == 1
    assert listed["items"][0]["id"] == result["id"]


def test_reply_decision_records_knowledge_gap_when_object_is_missing(client, db_session) -> None:
    tenant, token = _bootstrap_owner(client, "reply-decision-gap", "reply-decision-gap@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    _, message = _conversation_with_message(
        client,
        tenant["id"],
        headers,
        content="你们有没有火星基地专属套餐？",
    )

    res = client.post(f"/api/messages/{message['id']}/reply-decisions", headers=headers, json={})

    assert res.status_code == 201
    result = res.json()
    assert result["state"] == "knowledge_gap"
    assert result["reason"] == "no_business_object_match"
    assert result["business_object_id"] is None
    assert result["object_knowledge_card_id"] is None
    assert result["draft_reply"] == ""
    assert result["delivery_mode"] == "human_review"
    snapshot = db_session.scalar(
        select(ReplyCitationSnapshot).where(
            ReplyCitationSnapshot.tenant_id == tenant["id"],
            ReplyCitationSnapshot.provenance_id == result["provenance_id"],
        )
    )
    assert snapshot is not None
    assert snapshot.source_kind == "no_citation"
    assert snapshot.no_citation_reason == "knowledge_gap:no_business_object_match"


def test_reply_decision_blocks_policy_risk_even_when_object_matches(client) -> None:
    tenant, token = _bootstrap_owner(client, "reply-decision-blocked", "reply-decision-blocked@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    business_object, _ = _create_object_card(client, tenant["id"], headers)
    _, message = _conversation_with_message(
        client,
        tenant["id"],
        headers,
        content="我想买入门验证包，但是要绕过平台私下转账可以吗？",
    )

    res = client.post(f"/api/messages/{message['id']}/reply-decisions", headers=headers, json={})

    assert res.status_code == 201
    result = res.json()
    assert result["state"] == "blocked_by_policy"
    assert result["reason"] == "blocked_policy_terms"
    assert result["business_object_id"] == business_object["id"]
    assert result["draft_reply"] == ""
    assert result["delivery_mode"] == "blocked"
    assert set(result["matched_terms"]).intersection({"私下转账", "绕过平台"})


def test_reply_decision_requires_manual_gate_for_legal_risk_terms(client) -> None:
    tenant, token = _bootstrap_owner(client, "reply-decision-review", "reply-decision-review@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    _create_object_card(client, tenant["id"], headers)
    _, message = _conversation_with_message(
        client,
        tenant["id"],
        headers,
        content="入门验证包如果让我被投诉起诉了你们怎么赔偿？",
    )

    res = client.post(f"/api/messages/{message['id']}/reply-decisions", headers=headers, json={})

    assert res.status_code == 201
    result = res.json()
    assert result["state"] == "manual_gate_required"
    assert result["reason"] == "manual_review_terms"
    assert result["delivery_mode"] == "human_review"
    assert result["draft_reply"].startswith("入门验证包适合")
    assert set(result["matched_terms"]).intersection({"投诉", "起诉", "赔偿"})


def test_reply_decision_rejects_cross_tenant_and_outbound_messages(client) -> None:
    first, first_token = _bootstrap_owner(client, "reply-decision-first", "reply-decision-first@example.com")
    second, second_token = _bootstrap_owner(client, "reply-decision-second", "reply-decision-second@example.com")
    first_headers = {"Authorization": f"Bearer {first_token}"}
    second_headers = {"Authorization": f"Bearer {second_token}"}
    _, other_message = _conversation_with_message(
        client,
        second["id"],
        second_headers,
        content="入门验证包适合什么客户？",
    )

    cross_res = client.post(
        f"/api/messages/{other_message['id']}/reply-decisions",
        headers=first_headers,
        json={},
    )
    assert first["id"] != second["id"]
    assert cross_res.status_code == 404

    _, outbound_message = _conversation_with_message(
        client,
        first["id"],
        first_headers,
        content="这是一条已经发出的坐席回复。",
        direction="outbound",
    )
    outbound_res = client.post(
        f"/api/messages/{outbound_message['id']}/reply-decisions",
        headers=first_headers,
        json={},
    )
    assert outbound_res.status_code == 409
