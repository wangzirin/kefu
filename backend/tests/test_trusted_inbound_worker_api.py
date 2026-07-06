import hashlib
import time
from datetime import timedelta

import pytest
from app.models import TrustedInboundMessageJob, TrustedInboundWorkerRunRecord, WorkflowRun, utc_now
from app.workers import trusted_inbound_orchestrator
from test_channel_connectors_api import _bootstrap_owner, _create_connector


def _sha1_sorted_signature(*parts: str) -> str:
    return hashlib.sha1("".join(sorted(parts)).encode("utf-8")).hexdigest()


def _fresh_timestamp() -> str:
    return str(int(time.time()))


def _create_wecom_channel(client, tenant_id: int) -> dict:
    res = client.post(
        f"/api/tenants/{tenant_id}/channels",
        json={"type": "wecom", "name": "企业微信客服", "reply_mode": "assist", "status": "active"},
    )
    assert res.status_code == 201
    return res.json()


def _create_active_knowledge_card(client, tenant_id: int, headers: dict) -> dict:
    res = client.post(
        f"/api/tenants/{tenant_id}/knowledge-cards",
        headers=headers,
        json={
            "title": "订单进度查询",
            "question": "客户想查询订单进度怎么办？",
            "answer": "请先安抚客户，并引导客户提供订单号，我们会协助查询当前发货和物流进度。",
            "tags": ["订单", "物流"],
            "aliases": ["订单进度", "查订单", "物流进度"],
            "status": "active",
        },
    )
    assert res.status_code == 201
    return res.json()


def _post_verified_trusted_wecom_message(
    client,
    channel_id: int,
    *,
    external_id: str = "worker-message-001",
    content: str = "我想查询订单进度",
) -> dict:
    timestamp = _fresh_timestamp()
    nonce = f"nonce-{external_id}"
    encrypt = f"fixture-wecom-{external_id}"
    signature = _sha1_sorted_signature("p2_13_wecom_token", timestamp, nonce, encrypt)
    res = client.post(
        f"/api/webhooks/wecom/channels/{channel_id}?msg_signature={signature}&timestamp={timestamp}&nonce={nonce}",
        json={
            "event_type": "message",
            "external_message_id": external_id,
            "delivery_status": "received",
            "provider_event_id": f"event-{external_id}",
            "raw_payload": {
                "Encrypt": encrypt,
                "MsgID": external_id,
                "FromUserName": f"external-user-{external_id}",
                "Content": content,
            },
        },
    )
    assert res.status_code == 202
    return res.json()


def _create_business_object_card(client, tenant_id: int, headers: dict) -> tuple[dict, dict]:
    object_res = client.post(
        f"/api/tenants/{tenant_id}/business-objects",
        headers=headers,
        json={
            "type": "product",
            "title": "AI 客服入门验证包",
            "summary": "适合先验证官网客服、核心问答和人工接管流程。",
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
            "trigger_keywords": ["入门验证包", "官网客服", "试点"],
            "scope": {"channels": ["wecom"], "reply_mode": "auto_with_handoff"},
            "source": "manual",
            "status": "active",
        },
    )
    assert card_res.status_code == 201
    return business_object, card_res.json()


def test_trusted_inbound_worker_syncs_reply_decision_knowledge_gap(client) -> None:
    tenant, token = _bootstrap_owner(client, slug="trusted-worker", email="trusted-worker@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    channel = _create_wecom_channel(client, tenant["id"])
    _create_connector(
        client,
        channel["id"],
        headers,
        public_config={
            "corp_id_placeholder": "fixture_only",
            "credential_ref": "p2_13_wecom_fixture",
        },
    )
    webhook_event = _post_verified_trusted_wecom_message(client, channel["id"])
    message_id = webhook_event["parsed_event"]["trusted_message_id"]

    before_runs = client.get(f"/api/tenants/{tenant['id']}/workflow-runs", headers=headers)
    assert before_runs.status_code == 200
    assert before_runs.json() == []

    run_res = client.post(
        f"/api/tenants/{tenant['id']}/trusted-inbound-worker-runs",
        headers=headers,
        json={
            "batch_size": 5,
            "rate_limit_per_minute": 60,
            "mode": "model_assisted",
            "risk_level": "medium",
            "knowledge_top_k": 3,
        },
    )

    assert run_res.status_code == 201
    worker_run = run_res.json()
    assert worker_run["tenant_id"] == tenant["id"]
    assert worker_run["mode"] == "trusted_inbound_orchestrator"
    assert worker_run["scanned"] == 1
    assert worker_run["processed"] == 1
    assert worker_run["succeeded"] == 1
    assert worker_run["failed"] == 0
    assert worker_run["skipped"] == 0
    assert worker_run["rate_limited"] == 0
    assert worker_run["external_write"] is False
    [item] = worker_run["items"]
    assert item["message_id"] == message_id
    assert item["status"] == "succeeded"
    assert item["reply_decision_id"] > 0
    assert item["knowledge_gap_id"] > 0
    assert item["human_review_task_id"] is None
    assert item["decision"] == "knowledge_gap"
    assert item["reason"] == "no_business_object_match"
    assert item["workflow_run_id"] > 0
    assert item["idempotency_key"] == f"trusted_inbound_message:{message_id}:reply_orchestration"

    inbox_res = client.get(f"/api/tenants/{tenant['id']}/human-review-inbox", headers=headers)
    assert inbox_res.status_code == 200
    assert inbox_res.json() == []

    gaps_res = client.get(
        f"/api/tenants/{tenant['id']}/knowledge-gaps?source_type=reply_decision",
        headers=headers,
    )
    assert gaps_res.status_code == 200
    gaps = gaps_res.json()
    assert gaps["total"] == 1
    assert gaps["items"][0]["id"] == item["knowledge_gap_id"]
    assert gaps["items"][0]["source_ref"] == f"reply_decision:{item['reply_decision_id']}"

    workflow_detail = client.get(f"/api/workflow-runs/{item['workflow_run_id']}", headers=headers).json()
    assert workflow_detail["idempotency_key"] == item["idempotency_key"]
    assert workflow_detail["state_payload"]["trusted_inbound_worker"]["message_id"] == message_id
    assert workflow_detail["state_payload"]["trusted_inbound_worker"]["external_write"] is False
    assert workflow_detail["state_payload"]["reply_decision"]["state"] == "knowledge_gap"
    assert workflow_detail["state_payload"]["knowledge_gap_id"] == item["knowledge_gap_id"]

    second_run_res = client.post(
        f"/api/tenants/{tenant['id']}/trusted-inbound-worker-runs",
        headers=headers,
        json={"batch_size": 5, "rate_limit_per_minute": 60},
    )
    assert second_run_res.status_code == 201
    second_run = second_run_res.json()
    assert second_run["processed"] == 0
    assert second_run["skipped"] == 1
    assert second_run["skipped_message_ids"] == [message_id]

    workflow_runs = client.get(f"/api/tenants/{tenant['id']}/workflow-runs", headers=headers).json()
    assert [run["id"] for run in workflow_runs] == [item["workflow_run_id"]]


def test_trusted_inbound_worker_routes_manual_reply_decision_to_human_review(client) -> None:
    tenant, token = _bootstrap_owner(client, slug="trusted-worker-manual", email="trusted-worker-manual@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    channel = _create_wecom_channel(client, tenant["id"])
    _create_connector(
        client,
        channel["id"],
        headers,
        public_config={"corp_id_placeholder": "fixture_only", "credential_ref": "p2_13_wecom_fixture"},
    )
    _create_business_object_card(client, tenant["id"], headers)
    webhook_event = _post_verified_trusted_wecom_message(
        client,
        channel["id"],
        external_id="worker-manual-gate",
        content="入门验证包如果被投诉起诉了你们怎么赔偿？",
    )
    message_id = webhook_event["parsed_event"]["trusted_message_id"]

    run_res = client.post(
        f"/api/tenants/{tenant['id']}/trusted-inbound-worker-runs",
        headers=headers,
        json={"batch_size": 5, "rate_limit_per_minute": 60},
    )

    assert run_res.status_code == 201
    item = run_res.json()["items"][0]
    assert item["message_id"] == message_id
    assert item["reply_decision_id"] > 0
    assert item["decision"] == "manual_gate_required"
    assert item["reason"] == "manual_review_terms"
    assert item["human_review_task_id"] > 0
    assert item["knowledge_gap_id"] is None
    assert item["next_action"] == "await_human_review"

    inbox = client.get(f"/api/tenants/{tenant['id']}/human-review-inbox", headers=headers).json()
    assert len(inbox) == 1
    assert inbox[0]["id"] == item["human_review_task_id"]
    assert inbox[0]["trigger_message"]["id"] == message_id
    assert inbox[0]["evidence"]["draft_source"] == "object_knowledge_card"
    assert inbox[0]["evidence"]["retrieved_knowledge_count"] == 1


def test_trusted_inbound_worker_marks_auto_ready_as_outbox_pre_gate_without_draft(client) -> None:
    tenant, token = _bootstrap_owner(client, slug="trusted-worker-auto", email="trusted-worker-auto@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    channel = _create_wecom_channel(client, tenant["id"])
    _create_connector(
        client,
        channel["id"],
        headers,
        public_config={"corp_id_placeholder": "fixture_only", "credential_ref": "p2_13_wecom_fixture"},
    )
    _create_business_object_card(client, tenant["id"], headers)
    webhook_event = _post_verified_trusted_wecom_message(
        client,
        channel["id"],
        external_id="worker-auto-ready",
        content="入门验证包适合什么客户？",
    )

    run_res = client.post(
        f"/api/tenants/{tenant['id']}/trusted-inbound-worker-runs",
        headers=headers,
        json={"batch_size": 5, "rate_limit_per_minute": 60},
    )

    assert run_res.status_code == 201
    item = run_res.json()["items"][0]
    assert item["message_id"] == webhook_event["parsed_event"]["trusted_message_id"]
    assert item["reply_decision_id"] > 0
    assert item["decision"] == "auto_reply_ready"
    assert item["reason"] == "object_card_high_confidence"
    assert item["human_review_task_id"] is None
    assert item["knowledge_gap_id"] is None
    assert item["outbox_draft_id"] is None
    assert item["next_action"] == "await_outbox_pre_gate"

    workflow_detail = client.get(f"/api/workflow-runs/{item['workflow_run_id']}", headers=headers).json()
    assert workflow_detail["state_payload"]["outbox_pre_gate"]["eligible"] is True
    assert workflow_detail["state_payload"]["outbox_pre_gate"]["external_write"] is False
    assert workflow_detail["state_payload"]["outbox_pre_gate"]["reason"] == "external_write_closed"
    assert client.get(f"/api/tenants/{tenant['id']}/outbox-drafts", headers=headers).json() == []


def test_trusted_inbound_worker_respects_rate_limit_without_creating_workflow(client) -> None:
    tenant, token = _bootstrap_owner(client, slug="trusted-worker-limit", email="trusted-worker-limit@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    channel = _create_wecom_channel(client, tenant["id"])
    _create_connector(
        client,
        channel["id"],
        headers,
        public_config={
            "corp_id_placeholder": "fixture_only",
            "credential_ref": "p2_13_wecom_fixture",
        },
    )
    _post_verified_trusted_wecom_message(client, channel["id"], external_id="worker-message-limited")

    run_res = client.post(
        f"/api/tenants/{tenant['id']}/trusted-inbound-worker-runs",
        headers=headers,
        json={"batch_size": 5, "rate_limit_per_minute": 0},
    )

    assert run_res.status_code == 201
    worker_run = run_res.json()
    assert worker_run["scanned"] == 1
    assert worker_run["processed"] == 0
    assert worker_run["rate_limited"] == 1
    assert worker_run["items"] == []

    workflow_runs = client.get(f"/api/tenants/{tenant['id']}/workflow-runs", headers=headers).json()
    assert workflow_runs == []


def test_trusted_inbound_worker_ignores_untrusted_webhook_receipts(client) -> None:
    tenant, token = _bootstrap_owner(client, slug="trusted-worker-untrusted", email="trusted-worker-untrusted@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    channel = _create_wecom_channel(client, tenant["id"])
    _create_connector(
        client,
        channel["id"],
        headers,
        public_config={
            "corp_id_placeholder": "fixture_only",
            "credential_ref": "p2_13_wecom_fixture",
        },
    )
    timestamp = _fresh_timestamp()
    invalid = client.post(
        f"/api/webhooks/wecom/channels/{channel['id']}?msg_signature=bad-signature&timestamp={timestamp}&nonce=bad",
        json={
            "event_type": "message",
            "external_message_id": "untrusted-message-worker",
            "delivery_status": "received",
            "provider_event_id": "event-untrusted-message-worker",
            "raw_payload": {
                "Encrypt": "fixture-untrusted-worker",
                "MsgID": "untrusted-message-worker",
                "FromUserName": "external-untrusted-worker",
                "Content": "这条错签消息不能触发编排",
            },
        },
    )
    assert invalid.status_code == 202
    assert invalid.json()["signature_validated"] is False

    run_res = client.post(
        f"/api/tenants/{tenant['id']}/trusted-inbound-worker-runs",
        headers=headers,
        json={"batch_size": 5},
    )

    assert run_res.status_code == 201
    worker_run = run_res.json()
    assert worker_run["scanned"] == 0
    assert worker_run["processed"] == 0
    assert worker_run["items"] == []
    assert client.get(f"/api/tenants/{tenant['id']}/workflow-runs", headers=headers).json() == []


def test_trusted_inbound_worker_records_run_and_message_job_lease(client, db_session) -> None:
    tenant, token = _bootstrap_owner(client, slug="trusted-worker-run-record", email="trusted-worker-run@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    channel = _create_wecom_channel(client, tenant["id"])
    _create_connector(
        client,
        channel["id"],
        headers,
        public_config={
            "corp_id_placeholder": "fixture_only",
            "credential_ref": "p2_13_wecom_fixture",
        },
    )
    _create_active_knowledge_card(client, tenant["id"], headers)
    webhook_event = _post_verified_trusted_wecom_message(client, channel["id"], external_id="worker-run-record-001")
    message_id = webhook_event["parsed_event"]["trusted_message_id"]

    run_res = client.post(
        f"/api/tenants/{tenant['id']}/trusted-inbound-worker-runs",
        headers=headers,
        json={
            "batch_size": 5,
            "rate_limit_per_minute": 60,
            "worker_id": "api-worker-record-test",
            "lease_seconds": 30,
        },
    )

    assert run_res.status_code == 201
    payload = run_res.json()
    assert payload["run_record_id"] > 0
    assert payload["worker_id"] == "api-worker-record-test"
    assert payload["lease"]["atomic_claim"] is True
    assert payload["lease"]["lease_seconds"] == 30
    assert payload["lease"]["claimed"] == 1
    assert payload["lease"]["fresh_locked_skipped"] == 0
    assert payload["lease"]["stale_locked_reclaimed"] == 0
    assert payload["succeeded"] == 1
    assert payload["items"][0]["job_id"] > 0

    record = db_session.get(TrustedInboundWorkerRunRecord, payload["run_record_id"])
    assert record is not None
    assert record.status == "completed"
    assert record.worker_id == "api-worker-record-test"
    assert record.scanned == 1
    assert record.processed == 1
    assert record.succeeded == 1
    assert record.failed == 0
    assert record.external_write is False
    assert record.result_payload["lease"]["claimed"] == 1

    list_res = client.get(f"/api/tenants/{tenant['id']}/trusted-inbound-worker-runs", headers=headers)
    assert list_res.status_code == 200
    [run_record] = list_res.json()
    assert run_record["id"] == payload["run_record_id"]
    assert run_record["status"] == "completed"
    assert run_record["worker_id"] == "api-worker-record-test"
    assert run_record["lease_seconds"] == 30
    assert run_record["result_payload"]["lease"]["claimed"] == 1

    job = db_session.get(TrustedInboundMessageJob, payload["items"][0]["job_id"])
    assert job is not None
    assert job.message_id == message_id
    assert job.status == "succeeded"
    assert job.attempts_count == 1
    assert job.locked_by == "api-worker-record-test"
    assert job.workflow_run_id == payload["items"][0]["workflow_run_id"]


def test_trusted_inbound_worker_skips_fresh_lock_and_reclaims_stale_lock(client, db_session) -> None:
    tenant, token = _bootstrap_owner(client, slug="trusted-worker-lease", email="trusted-worker-lease@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    channel = _create_wecom_channel(client, tenant["id"])
    _create_connector(
        client,
        channel["id"],
        headers,
        public_config={
            "corp_id_placeholder": "fixture_only",
            "credential_ref": "p2_13_wecom_fixture",
        },
    )
    _create_active_knowledge_card(client, tenant["id"], headers)
    fresh_event = _post_verified_trusted_wecom_message(client, channel["id"], external_id="worker-fresh-lock")
    stale_event = _post_verified_trusted_wecom_message(client, channel["id"], external_id="worker-stale-lock")
    fresh_message_id = fresh_event["parsed_event"]["trusted_message_id"]
    stale_message_id = stale_event["parsed_event"]["trusted_message_id"]
    now = utc_now()
    fresh_job = TrustedInboundMessageJob(
        tenant_id=tenant["id"],
        conversation_id=fresh_event["parsed_event"]["conversation_id"],
        message_id=fresh_message_id,
        idempotency_key=f"trusted_inbound_message:{fresh_message_id}:reply_orchestration",
        status="locked",
        attempts_count=1,
        locked_by="another-live-worker",
        locked_at=now,
    )
    stale_job = TrustedInboundMessageJob(
        tenant_id=tenant["id"],
        conversation_id=stale_event["parsed_event"]["conversation_id"],
        message_id=stale_message_id,
        idempotency_key=f"trusted_inbound_message:{stale_message_id}:reply_orchestration",
        status="locked",
        attempts_count=1,
        locked_by="dead-worker",
        locked_at=now - timedelta(seconds=120),
    )
    db_session.add_all([fresh_job, stale_job])
    db_session.commit()

    run_res = client.post(
        f"/api/tenants/{tenant['id']}/trusted-inbound-worker-runs",
        headers=headers,
        json={
            "batch_size": 5,
            "rate_limit_per_minute": 60,
            "worker_id": "lease-test-worker",
            "lease_seconds": 30,
        },
    )

    assert run_res.status_code == 201
    payload = run_res.json()
    assert payload["scanned"] == 2
    assert payload["processed"] == 1
    assert payload["succeeded"] == 1
    assert payload["skipped"] == 1
    assert payload["skipped_message_ids"] == [fresh_message_id]
    assert payload["lease"]["fresh_locked_skipped"] == 1
    assert payload["lease"]["stale_locked_reclaimed"] == 1
    assert payload["items"][0]["message_id"] == stale_message_id

    db_session.refresh(fresh_job)
    db_session.refresh(stale_job)
    assert fresh_job.status == "locked"
    assert fresh_job.locked_by == "another-live-worker"
    assert stale_job.status == "succeeded"
    assert stale_job.locked_by == "lease-test-worker"
    assert stale_job.attempts_count == 2


def test_trusted_inbound_worker_replays_failed_message_job(client, db_session, monkeypatch: pytest.MonkeyPatch) -> None:
    tenant, token = _bootstrap_owner(client, slug="trusted-worker-replay", email="trusted-worker-replay@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    channel = _create_wecom_channel(client, tenant["id"])
    _create_connector(
        client,
        channel["id"],
        headers,
        public_config={
            "corp_id_placeholder": "fixture_only",
            "credential_ref": "p2_13_wecom_fixture",
        },
    )
    _create_active_knowledge_card(client, tenant["id"], headers)
    webhook_event = _post_verified_trusted_wecom_message(client, channel["id"], external_id="worker-replay-failed")
    message_id = webhook_event["parsed_event"]["trusted_message_id"]
    original_create_decision = trusted_inbound_orchestrator.create_reply_decision_for_message

    def fail_once(*args, **kwargs):
        raise RuntimeError("synthetic replay failure")

    monkeypatch.setattr(trusted_inbound_orchestrator, "create_reply_decision_for_message", fail_once)
    failed_res = client.post(
        f"/api/tenants/{tenant['id']}/trusted-inbound-worker-runs",
        headers=headers,
        json={
            "batch_size": 5,
            "rate_limit_per_minute": 60,
            "worker_id": "replay-worker-fail",
            "lease_seconds": 30,
        },
    )
    assert failed_res.status_code == 201
    failed_payload = failed_res.json()
    assert failed_payload["processed"] == 1
    assert failed_payload["failed"] == 1
    assert failed_payload["items"][0]["status"] == "failed"

    job = db_session.query(TrustedInboundMessageJob).filter_by(message_id=message_id).one()
    assert job.status == "failed"
    assert job.last_error == "synthetic replay failure"
    assert job.attempts_count == 1
    assert db_session.query(WorkflowRun).filter_by(trigger_message_id=message_id).all() == []

    monkeypatch.setattr(trusted_inbound_orchestrator, "create_reply_decision_for_message", original_create_decision)
    replay_res = client.post(
        f"/api/tenants/{tenant['id']}/trusted-inbound-worker-runs",
        headers=headers,
        json={
            "batch_size": 5,
            "rate_limit_per_minute": 60,
            "worker_id": "replay-worker-success",
            "lease_seconds": 30,
        },
    )

    assert replay_res.status_code == 201
    replay_payload = replay_res.json()
    assert replay_payload["processed"] == 1
    assert replay_payload["succeeded"] == 1
    assert replay_payload["items"][0]["message_id"] == message_id
    db_session.refresh(job)
    assert job.status == "succeeded"
    assert job.locked_by == "replay-worker-success"
    assert job.attempts_count == 2
    assert job.last_error == ""
