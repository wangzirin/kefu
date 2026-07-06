from __future__ import annotations

from test_p3_06h_rbac_permission_matrix import _bootstrap_user_with_role


def _auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_rpa_copilot_strategy_dry_run_handles_standard_question(client) -> None:
    tenant, token = _bootstrap_user_with_role(
        client,
        slug="rpa-copilot-agent",
        role_code="agent",
        email="rpa-copilot-agent@example.com",
    )

    response = client.post(
        "/api/rpa-copilot/strategy-dry-run",
        headers=_auth_header(token),
        json={
            "channel": "manual_import_research",
            "customer_name": "测试客户",
            "text": "你好，这个订单一般多久发货？",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["tenant_id"] == tenant["id"]
    assert payload["mode"] == "research_dry_run"
    assert payload["reply_strategy"]["intent"] == "shipping_status_or_policy"
    assert payload["reply_strategy"]["delivery_mode"] == "fill_draft_only"
    assert payload["reply_strategy"]["next_best_action"] == "operator_review_and_send"
    assert payload["draft"]["citations"]
    assert payload["audit"]["external_write_performed"] is False
    assert payload["audit"]["auto_send_enabled"] is False
    assert payload["audit"]["persisted_to_database"] is False
    assert all(action["external_write"] is False for action in payload["actions"])


def test_rpa_copilot_strategy_dry_run_routes_complaint_to_human(client) -> None:
    _, token = _bootstrap_user_with_role(
        client,
        slug="rpa-copilot-owner",
        role_code="owner",
        email="rpa-copilot-owner@example.com",
    )

    response = client.post(
        "/api/rpa-copilot/strategy-dry-run",
        headers=_auth_header(token),
        json={
            "channel": "manual_import_research",
            "customer_name": "投诉客户",
            "text": "收到后发现质量问题，我要退款，不处理我就投诉。",
            "attachments": ["demo-image://damaged-package"],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["guardrail"]["status"] == "needs_human"
    assert "risk_term" in payload["guardrail"]["reasons"]
    assert payload["reply_strategy"]["delivery_mode"] == "human_takeover"
    assert payload["reply_strategy"]["next_best_action"] == "collect_evidence_and_handoff"
    assert any(signal == "has_attachment" for signal in payload["reply_strategy"]["quality_signals"])
    assert not any(action["kind"] == "click_send" for action in payload["actions"])


def test_rpa_copilot_strategy_dry_run_records_gap_for_missing_knowledge(client) -> None:
    _, token = _bootstrap_user_with_role(
        client,
        slug="rpa-copilot-admin",
        role_code="admin",
        email="rpa-copilot-admin@example.com",
    )

    response = client.post(
        "/api/rpa-copilot/strategy-dry-run",
        headers=_auth_header(token),
        json={
            "channel": "manual_import_research",
            "customer_name": "缺口客户",
            "text": "这个产品能不能放在户外长期暴晒？",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["draft"]["missing_knowledge"] is True
    assert payload["reply_strategy"]["delivery_mode"] == "record_gap"
    assert payload["reply_strategy"]["next_best_action"] == "record_knowledge_gap_and_handoff"
    assert any(action["kind"] == "record_knowledge_gap" for action in payload["actions"])


def test_rpa_copilot_strategy_dry_run_requires_conversation_read_permission(client) -> None:
    _, viewer_token = _bootstrap_user_with_role(
        client,
        slug="rpa-copilot-viewer",
        role_code="viewer",
        email="rpa-copilot-viewer@example.com",
    )

    response = client.post(
        "/api/rpa-copilot/strategy-dry-run",
        headers=_auth_header(viewer_token),
        json={"text": "你好，这个订单一般多久发货？"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "insufficient permission"

    no_token_response = client.post(
        "/api/rpa-copilot/strategy-dry-run",
        json={"text": "你好，这个订单一般多久发货？"},
    )
    assert no_token_response.status_code == 401
