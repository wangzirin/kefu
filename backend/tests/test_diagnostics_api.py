import base64
import hashlib
import json

from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15

from app.models import (
    AuditEvent,
    BusinessObject,
    Channel,
    ChannelAccount,
    Contact,
    Conversation,
    KnowledgeDocument,
    KnowledgeDocumentChunk,
    KnowledgeEvaluationRun,
    KnowledgeEvaluationSet,
    Message,
    OutboxDeliveryJob,
    OutboxDraft,
    TrustedInboundMessageJob,
    User,
    UserRole,
    WorkerHeartbeat,
    utc_now,
)
from app.core.security import hash_password


def _canonical_json(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _signed_knowledge_update_package(private_key: RSA.RsaKey, *, package_id: str) -> dict:
    payload = {
        "schema_version": "wanfa.knowledge_update_package.v1",
        "package_id": f"{package_id}-payload",
        "package_name": "处理单知识修复包",
        "source_diagnostic_filename": "wanfa-diagnostic-remediation.json",
        "notes": "从售后处理单生成的知识修复包，不包含客户聊天原文。",
        "business_objects": [
            {
                "ref": "remediation-lite-package",
                "type": "package",
                "title": "AI客服入门验证包",
                "aliases": ["入门版", "官网客服试点"],
                "summary": "适合官网客服、核心问答、留资和人工接管的小微企业。",
                "status": "active",
            }
        ],
        "object_knowledge_cards": [
            {
                "business_object_ref": "remediation-lite-package",
                "question": "入门验证包是否支持复杂多渠道外发？",
                "answer": "入门验证包先覆盖官网客服和核心问答；复杂多渠道真实外发必须完成官方授权和回执验收。",
                "trigger_keywords": ["入门验证", "多渠道", "外发"],
                "source": "diagnostic_remediation",
                "status": "active",
            }
        ],
        "knowledge_documents": [
            {
                "title": "处理单知识修复说明",
                "source_type": "signed_update_package",
                "source_uri": "internal://remediation/knowledge-update",
                "tags": ["处理单", "知识修复"],
                "status": "active",
                "raw_text": "处理单建议补充客户常问问题，真实外发仍需官方授权和回执闭环。",
            }
        ],
        "evaluation_sets": [],
    }
    manifest = {
        "schema_version": "wanfa.signed_update_manifest.v1",
        "package_id": package_id,
        "package_name": "处理单知识修复包",
        "package_type": "knowledge",
        "package_version": "2026.07.04.h2w6b",
        "product": "wanfa-standard-ops",
        "released_at": "2026-07-04T10:00:00+08:00",
        "compatible_app_versions": ["0.1.0"],
        "requires_maintenance_window": False,
        "payload_digest_sha256": hashlib.sha256(_canonical_json(payload)).hexdigest(),
        "payload_size_bytes": len(_canonical_json(payload)),
        "operations": [
            {
                "target": "knowledge_documents",
                "action": "upsert",
                "count": 2,
                "summary": "补充处理单知识卡和文档",
            }
        ],
    }
    digest = SHA256.new(_canonical_json(manifest))
    signature = base64.b64encode(pkcs1_15.new(private_key).sign(digest)).decode("ascii")
    return {
        "schema_version": "wanfa.signed_update_package.v1",
        "manifest": manifest,
        "payload": payload,
        "release_notes": "处理单知识修复包只通过签名更新中心受控应用。",
        "checksums": {"payload_sha256": manifest["payload_digest_sha256"]},
        "signature": {
            "algorithm": "rsa_pkcs1v15_sha256",
            "key_id": "test-release-key",
            "value": signature,
        },
    }


def _step_status(plan: dict, step_id: str) -> str:
    for step in plan.get("lifecycle_steps", []):
        if step.get("id") == step_id:
            return str(step.get("status"))
    raise AssertionError(f"missing lifecycle step: {step_id}")


def _create_tenant(client, name: str, slug: str) -> dict:
    res = client.post("/api/tenants", json={"name": name, "slug": slug})
    assert res.status_code == 201
    return res.json()


def _bootstrap_owner(client, tenant: dict, email: str = "owner@example.com") -> tuple[dict, dict, str]:
    role_res = client.post(
        f"/api/tenants/{tenant['id']}/roles",
        json={"code": "owner", "name": "负责人"},
    )
    assert role_res.status_code == 201
    role = role_res.json()

    user_res = client.post(
        f"/api/tenants/{tenant['id']}/users",
        json={
            "name": "负责人",
            "email": email,
            "password": "ChangeMe123!",
        },
    )
    assert user_res.status_code == 201
    user = user_res.json()

    assign_res = client.post(
        f"/api/users/{user['id']}/roles",
        json={"role_id": role["id"]},
    )
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
    return role, user, login_res.json()["access_token"]


def _create_role(client, tenant_id: int, code: str, name: str, headers: dict) -> dict:
    res = client.post(f"/api/tenants/{tenant_id}/roles", json={"code": code, "name": name}, headers=headers)
    assert res.status_code == 201
    return res.json()


def test_owner_can_export_diagnostic_bundle_without_raw_sensitive_values(client, db_session) -> None:
    tenant = _create_tenant(client, "本地客户", "diagnostics-safe")
    _owner_role, _owner, token = _bootstrap_owner(client, tenant)
    headers = {"Authorization": f"Bearer {token}"}

    channel = Channel(
        tenant_id=tenant["id"],
        type="douyin",
        name="抖音测试店",
        reply_mode="auto",
        status="active",
    )
    contact = Contact(
        tenant_id=tenant["id"],
        display_name="敏感客户",
        phone="13800138000",
        wechat="wxid_sensitive_customer",
    )
    db_session.add_all([channel, contact])
    db_session.flush()
    channel_account = ChannelAccount(
        tenant_id=tenant["id"],
        channel_id=channel.id,
        provider="douyin",
        platform="douyin",
        account_name="店铺A",
        external_account_id="external-sensitive-id",
        store_name="本地测试店",
        entrypoint_name="私信",
        authorization_status="connected",
        access_status="connected",
        reply_mode="auto",
        health_status="healthy",
        public_profile={"display": "safe"},
    )
    conversation = Conversation(
        tenant_id=tenant["id"],
        channel_id=channel.id,
        contact_id=contact.id,
        status="bot",
        subject="不要导出完整会话",
    )
    db_session.add_all([channel_account, conversation])
    db_session.flush()
    message = Message(
        conversation_id=conversation.id,
        direction="inbound",
        sender_type="customer",
        content="我的手机号是 13800138000，接口凭据 sk-test-sensitive-value 不要泄露。",
        external_message_id="external-message-sensitive-id",
    )
    business_object = BusinessObject(
        tenant_id=tenant["id"],
        type="product",
        title="标准客服包",
        external_id="product-sensitive-id",
        summary="只统计对象，不导出长文。",
    )
    document = KnowledgeDocument(
        tenant_id=tenant["id"],
        title="产品说明",
        raw_text="完整知识库原文也不能进入诊断包。",
        status="active",
        ingestion_status="indexed",
        chunk_count=1,
    )
    db_session.add_all([message, business_object, document])
    db_session.flush()
    chunk = KnowledgeDocumentChunk(
        tenant_id=tenant["id"],
        document_id=document.id,
        chunk_index=0,
        content="知识 chunk 原文也不应该进入诊断包。",
        status="active",
    )
    evaluation_set = KnowledgeEvaluationSet(
        tenant_id=tenant["id"],
        name="客服答案评测",
        status="active",
        evaluation_mode="customer_service_retrieval",
    )
    db_session.add_all([chunk, evaluation_set])
    db_session.flush()
    evaluation_run = KnowledgeEvaluationRun(
        tenant_id=tenant["id"],
        evaluation_set_id=evaluation_set.id,
        run_mode="customer_service_retrieval",
        retrieval_mode="hybrid",
        vector_engine="sqlite_json_vector_store",
        total_cases=3,
        answered_cases=2,
        no_hit_cases=1,
        passed_cases=2,
        failed_cases=1,
        needs_review_cases=1,
        hit_rate=0.67,
        citation_coverage=0.5,
        expected_term_coverage=0.67,
        average_confidence=0.71,
    )
    draft = OutboxDraft(
        tenant_id=tenant["id"],
        conversation_id=conversation.id,
        channel_id=channel.id,
        contact_id=contact.id,
        reply_text="草稿回复原文不应该进入诊断包。",
        idempotency_key="draft-safe-1",
    )
    db_session.add_all([evaluation_run, draft])
    db_session.flush()
    delivery_job = OutboxDeliveryJob(
        tenant_id=tenant["id"],
        outbox_draft_id=draft.id,
        channel_id=channel.id,
        status="failed",
        idempotency_key="delivery-safe-1",
        last_error="Authorization: Bearer sk-test-sensitive-value api_key=abcdefg1234567890",
        dead_letter_reason="provider_failed",
    )
    inbound_job = TrustedInboundMessageJob(
        tenant_id=tenant["id"],
        conversation_id=conversation.id,
        message_id=message.id,
        idempotency_key="inbound-safe-1",
        status="failed",
        last_error="cookie=session-sensitive password=ChangeMe123!",
    )
    heartbeat = WorkerHeartbeat(
        tenant_id=tenant["id"],
        worker_type="trusted_inbound",
        worker_id="worker-1",
        status="failed",
        last_heartbeat_at=utc_now(),
        last_error="token=wanfa_session_sensitive_value_123456789",
    )
    db_session.add_all([delivery_job, inbound_job, heartbeat])
    db_session.commit()

    res = client.get(f"/api/tenants/{tenant['id']}/diagnostic-bundle", headers=headers)

    assert res.status_code == 200
    bundle = res.json()
    serialized = json.dumps(bundle, ensure_ascii=False).lower()
    assert bundle["schema_version"] == "p3-06u-26h2c.v1"
    assert bundle["counts"]["messages"] == 1
    assert bundle["knowledge"]["documents"]["total"] == 1
    assert bundle["quality"]["latest_evaluation"]["total_cases"] == 3
    assert bundle["safety"]["credential_value_findings"] == 0
    assert "草稿回复原文" not in serialized
    assert "完整知识库原文" not in serialized
    assert "13800138000" not in serialized
    assert "wxid_sensitive_customer" not in serialized
    assert "external-sensitive-id" not in serialized
    assert "sk-test-sensitive-value" not in serialized
    assert "wanfa_session_sensitive_value" not in serialized
    assert "api_key" not in serialized
    assert "cookie" not in serialized
    assert "password" not in serialized
    assert "token" not in serialized


def test_agent_cannot_export_diagnostic_bundle(client, db_session) -> None:
    tenant = _create_tenant(client, "权限客户", "diagnostics-permission")
    _owner_role, _owner, owner_token = _bootstrap_owner(client, tenant)
    owner_headers = {"Authorization": f"Bearer {owner_token}"}
    agent_role = _create_role(client, tenant["id"], "agent", "客服", owner_headers)
    user = User(
        tenant_id=tenant["id"],
        name="一线客服",
        email="agent@example.com",
        password_hash=hash_password("ChangeMe123!"),
        status="active",
    )
    db_session.add(user)
    db_session.flush()
    db_session.add(UserRole(user_id=user.id, role_id=agent_role["id"]))
    db_session.commit()

    login = client.post(
        "/api/auth/login",
        json={"tenant_slug": tenant["slug"], "email": "agent@example.com", "password": "ChangeMe123!"},
    )
    assert login.status_code == 200
    agent_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    res = client.get(f"/api/tenants/{tenant['id']}/diagnostic-bundle", headers=agent_headers)

    assert res.status_code == 403


def test_owner_can_create_authorized_diagnostic_upload_package_without_external_upload(client, db_session) -> None:
    tenant = _create_tenant(client, "上传客户", "diagnostics-upload")
    _owner_role, owner, token = _bootstrap_owner(client, tenant)
    headers = {"Authorization": f"Bearer {token}"}

    contact = Contact(
        tenant_id=tenant["id"],
        display_name="客户联系人",
        phone="13800138000",
        wechat="wxid_upload_sensitive",
    )
    db_session.add(contact)
    db_session.commit()

    res = client.post(
        f"/api/tenants/{tenant['id']}/diagnostic-upload-package",
        json={
            "authorization_note": "客户管理员确认授权上传本次脱敏诊断包。",
            "contact_name": "王经理",
            "support_ticket": "SUP-20260703-001",
        },
        headers=headers,
    )

    assert res.status_code == 200
    package = res.json()
    serialized = json.dumps(package, ensure_ascii=False).lower()
    assert package["schema_version"] == "p3-06u-26h2k.v1"
    assert package["authorization"]["authorized_by_user_id"] == owner["id"]
    assert package["authorization"]["authorization_note"] == "客户管理员确认授权上传本次脱敏诊断包。"
    assert package["authorization"]["contact_name"] == "王经理"
    assert package["authorization"]["support_ticket"] == "SUP-20260703-001"
    assert package["upload_manifest"]["transfer_mode"] == "manual_transfer_package"
    assert len(package["upload_manifest"]["diagnostic_bundle_sha256"]) == 64
    assert package["safety"]["external_upload_performed"] is False
    assert package["safety"]["manual_transfer_required"] is True
    assert package["safety"]["customer_authorization_recorded"] is True
    assert package["safety"]["raw_message_text_included"] is False
    assert package["diagnostic_bundle"]["safety"]["local_export_only"] is True
    assert "13800138000" not in serialized
    assert "wxid_upload_sensitive" not in serialized

    audit_actions = [event.action for event in db_session.query(AuditEvent).all()]
    assert "diagnostic_bundle.upload_package_created" in audit_actions


def test_agent_cannot_create_authorized_diagnostic_upload_package(client, db_session) -> None:
    tenant = _create_tenant(client, "上传权限客户", "diagnostics-upload-permission")
    _owner_role, _owner, owner_token = _bootstrap_owner(client, tenant)
    owner_headers = {"Authorization": f"Bearer {owner_token}"}
    agent_role = _create_role(client, tenant["id"], "agent", "客服", owner_headers)
    user = User(
        tenant_id=tenant["id"],
        name="一线客服",
        email="upload-agent@example.com",
        password_hash=hash_password("ChangeMe123!"),
        status="active",
    )
    db_session.add(user)
    db_session.flush()
    db_session.add(UserRole(user_id=user.id, role_id=agent_role["id"]))
    db_session.commit()

    login = client.post(
        "/api/auth/login",
        json={"tenant_slug": tenant["slug"], "email": "upload-agent@example.com", "password": "ChangeMe123!"},
    )
    assert login.status_code == 200
    agent_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    res = client.post(
        f"/api/tenants/{tenant['id']}/diagnostic-upload-package",
        json={"authorization_note": "尝试生成授权上传包"},
        headers=agent_headers,
    )

    assert res.status_code == 403


def test_owner_can_register_diagnostic_intake_record_and_process_it(client, db_session) -> None:
    tenant = _create_tenant(client, "接收台客户", "diagnostics-intake")
    _owner_role, _owner, token = _bootstrap_owner(client, tenant)
    headers = {"Authorization": f"Bearer {token}"}

    package_res = client.post(
        f"/api/tenants/{tenant['id']}/diagnostic-upload-package",
        json={
            "authorization_note": "客户管理员确认授权上传本次脱敏诊断包。",
            "contact_name": "售后联系人",
            "support_ticket": "SUP-INTAKE-001",
        },
        headers=headers,
    )
    assert package_res.status_code == 200
    upload_package = package_res.json()

    intake_res = client.post(
        f"/api/tenants/{tenant['id']}/diagnostic-intake-records",
        json={
            "upload_package": upload_package,
            "source_channel": "manual_transfer",
            "processing_note": "客户主动提供本次脱敏诊断包。",
        },
        headers=headers,
    )

    assert intake_res.status_code == 200
    record = intake_res.json()
    assert record["status"] == "received"
    assert record["validation_status"] == "passed"
    assert record["package_filename"] == upload_package["filename"]
    assert record["diagnostic_bundle_sha256"] == upload_package["upload_manifest"]["diagnostic_bundle_sha256"]
    assert record["safety"]["customer_authorization_recorded"] is True
    assert record["safety"]["remote_control_performed"] is False
    assert record["safety"]["customer_environment_write_performed"] is False
    assert record["download_supported"] is True

    list_res = client.get(f"/api/tenants/{tenant['id']}/diagnostic-intake-records", headers=headers)
    assert list_res.status_code == 200
    listing = list_res.json()
    assert listing["schema_version"] == "p3-06u-26h2w5.diagnostic_intake.v1"
    assert len(listing["items"]) == 1
    assert listing["items"][0]["intake_id"] == record["intake_id"]

    update_res = client.patch(
        f"/api/tenants/{tenant['id']}/diagnostic-intake-records/{record['id']}",
        json={"status": "resolved", "processing_note": "已生成建议更新包，等待客户确认。"},
        headers=headers,
    )
    assert update_res.status_code == 200
    updated = update_res.json()
    assert updated["status"] == "resolved"
    assert updated["handled_by_id"] is not None

    download_res = client.get(
        f"/api/tenants/{tenant['id']}/diagnostic-intake-records/{record['id']}/download",
        headers=headers,
    )
    assert download_res.status_code == 200
    download = download_res.json()
    assert download["intake_id"] == record["intake_id"]
    assert download["filename"] == upload_package["filename"]
    assert download["body_encoding"] == "utf-8"
    assert len(download["body_sha256"]) == 64
    assert download["safety"]["remote_control_performed"] is False
    assert "13800138000" not in download["body"]
    assert "sk-" not in download["body"].lower()

    audit_actions = [event.action for event in db_session.query(AuditEvent).all()]
    assert "diagnostic_intake.received" in audit_actions
    assert "diagnostic_intake.status_updated" in audit_actions


def test_diagnostic_intake_rejects_tampered_or_unsafe_package(client, db_session) -> None:
    tenant = _create_tenant(client, "拒收客户", "diagnostics-intake-reject")
    _owner_role, _owner, token = _bootstrap_owner(client, tenant)
    headers = {"Authorization": f"Bearer {token}"}

    package_res = client.post(
        f"/api/tenants/{tenant['id']}/diagnostic-upload-package",
        json={"authorization_note": "客户管理员确认授权上传本次脱敏诊断包。"},
        headers=headers,
    )
    assert package_res.status_code == 200
    upload_package = package_res.json()
    upload_package["diagnostic_bundle"]["counts"]["messages"] = 999
    upload_package["safety"]["raw_message_text_included"] = True

    intake_res = client.post(
        f"/api/tenants/{tenant['id']}/diagnostic-intake-records",
        json={"upload_package": upload_package, "source_channel": "manual_transfer"},
        headers=headers,
    )

    assert intake_res.status_code == 200
    record = intake_res.json()
    assert record["status"] == "rejected"
    assert record["validation_status"] == "rejected"
    assert "诊断包 sha256 与上传清单不一致" in record["rejection_reason"]
    assert "原始聊天文本" in record["rejection_reason"]
    assert record["safety"]["remote_control_performed"] is False


def test_diagnostic_intake_rejects_malicious_packages_without_persisting_raw_payload(client) -> None:
    tenant = _create_tenant(client, "坏包拒收客户", "diagnostics-intake-hardening")
    _owner_role, _owner, token = _bootstrap_owner(client, tenant)
    headers = {"Authorization": f"Bearer {token}"}

    package_res = client.post(
        f"/api/tenants/{tenant['id']}/diagnostic-upload-package",
        json={"authorization_note": "客户管理员确认授权上传本次脱敏诊断包。"},
        headers=headers,
    )
    assert package_res.status_code == 200
    base_package = package_res.json()

    deeply_nested: dict = {"leaf": "safe"}
    for _ in range(24):
        deeply_nested = {"level": deeply_nested}

    cases = [
        (
            "token",
            {
                **base_package,
                "diagnostic_bundle": {
                    **base_package["diagnostic_bundle"],
                    "recent_errors": [{"message": "Authorization: Bearer sk-malicioussecret123456789"}],
                },
            },
            "sk-malicioussecret",
        ),
        (
            "oversized",
            {**base_package, "warnings": ["X" * (800 * 1024)]},
            "X" * 100,
        ),
        (
            "deep",
            {**base_package, "warnings": [deeply_nested]},
            "leaf",
        ),
        (
            "browser-profile",
            {**base_package, "browser_profile": {"Cookies": "session=wanfa_session_sensitive_value_123"}},
            "wanfa_session_sensitive",
        ),
    ]

    for label, upload_package, forbidden in cases:
        intake_res = client.post(
            f"/api/tenants/{tenant['id']}/diagnostic-intake-records",
            json={
                "upload_package": upload_package,
                "source_channel": "manual_transfer",
                "processing_note": f"测试拒收：{label}",
            },
            headers=headers,
        )
        assert intake_res.status_code == 200
        record = intake_res.json()
        assert record["status"] == "rejected"
        assert record["validation_status"] == "rejected"
        assert record["safety"]["payload_redacted_for_storage"] is True

        download_res = client.get(
            f"/api/tenants/{tenant['id']}/diagnostic-intake-records/{record['id']}/download",
            headers=headers,
        )
        assert download_res.status_code == 200
        body = download_res.json()["body"]
        assert "rejected_upload_summary_only" in body
        assert forbidden not in body
        assert len(body) < 5000


def test_owner_can_create_remediation_request_from_accepted_intake(client, db_session) -> None:
    tenant = _create_tenant(client, "处理单客户", "diagnostics-remediation")
    _owner_role, _owner, token = _bootstrap_owner(client, tenant)
    headers = {"Authorization": f"Bearer {token}"}

    package_res = client.post(
        f"/api/tenants/{tenant['id']}/diagnostic-upload-package",
        json={"authorization_note": "客户管理员确认授权上传本次脱敏诊断包。"},
        headers=headers,
    )
    assert package_res.status_code == 200
    intake_res = client.post(
        f"/api/tenants/{tenant['id']}/diagnostic-intake-records",
        json={"upload_package": package_res.json(), "source_channel": "manual_transfer"},
        headers=headers,
    )
    assert intake_res.status_code == 200
    intake = intake_res.json()

    create_res = client.post(
        f"/api/tenants/{tenant['id']}/diagnostic-intake-records/{intake['id']}/remediation-requests",
        json={
            "request_type": "knowledge_or_strategy_update",
            "title": "知识与策略处理单",
            "summary": "先根据诊断包生成处理建议，不直接改客户环境。",
            "priority": "normal",
        },
        headers=headers,
    )

    assert create_res.status_code == 200
    request = create_res.json()
    assert request["request_type"] == "knowledge_or_strategy_update"
    assert request["status"] == "draft"
    assert request["intake_record_id"] == intake["id"]
    assert request["safety"]["remote_control_performed"] is False
    assert request["safety"]["customer_environment_write_performed"] is False
    assert request["safety"]["automatic_update_performed"] is False
    assert request["safety"]["can_apply_now"] is False
    assert request["update_request_manifest"]["requires_local_backup_before_apply"] is True
    assert request["update_request_manifest"]["can_generate_signed_update_package_now"] is False
    assert any(action["code"] == "prepare_local_backup" for action in request["recommended_actions"])

    list_res = client.get(f"/api/tenants/{tenant['id']}/diagnostic-remediation-requests", headers=headers)
    assert list_res.status_code == 200
    listing = list_res.json()
    assert listing["schema_version"] == "p3-06u-26h2w6.diagnostic_remediation.v1"
    assert len(listing["items"]) == 1
    assert listing["items"][0]["request_id"] == request["request_id"]

    update_res = client.patch(
        f"/api/tenants/{tenant['id']}/diagnostic-remediation-requests/{request['id']}",
        json={"status": "ready_for_customer", "summary": "处理建议已准备，等待客户管理员确认。"},
        headers=headers,
    )
    assert update_res.status_code == 200
    assert update_res.json()["status"] == "ready_for_customer"

    download_res = client.get(
        f"/api/tenants/{tenant['id']}/diagnostic-remediation-requests/{request['id']}/download",
        headers=headers,
    )
    assert download_res.status_code == 200
    download = download_res.json()
    assert download["request_id"] == request["request_id"]
    assert download["content_type"] == "application/json"
    assert download["safety"]["remote_control_performed"] is False
    assert download["safety"]["customer_environment_write_performed"] is False
    assert download["safety"]["can_apply_now"] is False
    assert "silent_update_performed" in download["body"]
    assert "can_generate_signed_update_package_now" in download["body"]

    audit_actions = [event.action for event in db_session.query(AuditEvent).all()]
    assert "diagnostic_remediation.created" in audit_actions
    assert "diagnostic_remediation.status_updated" in audit_actions


def test_owner_can_link_remediation_to_signed_update_plan_and_refresh_status(client, db_session, monkeypatch) -> None:
    tenant = _create_tenant(client, "受控更新客户", "diagnostics-remediation-update-plan")
    _owner_role, _owner, token = _bootstrap_owner(client, tenant)
    headers = {"Authorization": f"Bearer {token}"}

    package_res = client.post(
        f"/api/tenants/{tenant['id']}/diagnostic-upload-package",
        json={"authorization_note": "客户管理员确认授权上传本次脱敏诊断包。"},
        headers=headers,
    )
    assert package_res.status_code == 200
    intake_res = client.post(
        f"/api/tenants/{tenant['id']}/diagnostic-intake-records",
        json={"upload_package": package_res.json(), "source_channel": "manual_transfer"},
        headers=headers,
    )
    assert intake_res.status_code == 200
    intake = intake_res.json()
    remediation_res = client.post(
        f"/api/tenants/{tenant['id']}/diagnostic-intake-records/{intake['id']}/remediation-requests",
        json={"request_type": "knowledge_update", "title": "知识修复处理单"},
        headers=headers,
    )
    assert remediation_res.status_code == 200
    remediation = remediation_res.json()

    private_key = RSA.generate(2048)
    trusted_public_key = private_key.publickey().export_key(format="PEM").decode("utf-8")
    monkeypatch.setenv(
        "WANFA_UPDATE_TRUSTED_PUBLIC_KEYS_JSON",
        json.dumps({"test-release-key": trusted_public_key}),
    )
    signed_package = _signed_knowledge_update_package(private_key, package_id="wanfa-update-remediation-plan-001")
    stage_res = client.post(
        f"/api/tenants/{tenant['id']}/signed-update-package/staged",
        json={"package": signed_package},
        headers=headers,
    )
    assert stage_res.status_code == 201
    staged = stage_res.json()
    assert staged["status"] == "staged"

    plan_res = client.post(
        f"/api/tenants/{tenant['id']}/diagnostic-remediation-requests/{remediation['id']}/signed-update-plan",
        json={
            "signed_update_package_id": staged["id"],
            "operator_note": "客户确认后进入受控更新计划。",
        },
        headers=headers,
    )

    assert plan_res.status_code == 200
    planned = plan_res.json()
    assert planned["status"] == "update_plan_prepared"
    assert planned["safety"]["remote_control_performed"] is False
    assert planned["safety"]["automatic_update_performed"] is False
    assert planned["safety"]["external_write_performed"] is False
    assert planned["safety"]["plan_generated_only"] is True
    assert planned["safety"]["can_apply_now"] is False
    assert any(action["code"] == "link_signed_update_package" for action in planned["recommended_actions"])
    assert any(action["code"] == "verify_local_backup_before_apply" for action in planned["recommended_actions"])
    plan = planned["update_request_manifest"]["signed_update_control_plan"]
    assert plan["schema_version"] == "p3-06u-26h2w6b.signed_update_control_plan.v1"
    assert plan["request_id"] == remediation["request_id"]
    assert plan["signed_update_package"]["id"] == staged["id"]
    assert plan["signed_update_package"]["package_id"] == "wanfa-update-remediation-plan-001"
    assert plan["signed_update_package"]["package_type"] == "knowledge"
    assert plan["signed_update_package"]["status"] == "staged"
    assert plan["can_apply_from_plan_now"] is False
    assert plan["can_rollback_from_plan_now"] is False
    assert plan["safety"]["plan_generated_only"] is True
    assert plan["safety"]["automatic_update_performed"] is False
    assert _step_status(plan, "preflight") == "passed"
    assert _step_status(plan, "stage") == "passed"
    assert _step_status(plan, "apply") == "ready"
    assert _step_status(plan, "rollback") == "planned"

    apply_res = client.post(
        f"/api/signed-update-packages/{staged['id']}/apply",
        json={"reason": "客户管理员确认应用知识修复包。"},
        headers=headers,
    )
    assert apply_res.status_code == 200
    refresh_after_apply = client.post(
        f"/api/tenants/{tenant['id']}/diagnostic-remediation-requests/{remediation['id']}/signed-update-plan",
        json={
            "signed_update_package_id": staged["id"],
            "operator_note": "应用后刷新受控更新计划。",
        },
        headers=headers,
    )
    assert refresh_after_apply.status_code == 200
    applied_plan = refresh_after_apply.json()["update_request_manifest"]["signed_update_control_plan"]
    assert applied_plan["signed_update_package"]["status"] == "applied"
    assert applied_plan["signed_update_package"]["backup_created"] is True
    assert _step_status(applied_plan, "apply") == "passed"
    assert _step_status(applied_plan, "rollback") == "ready"

    rollback_res = client.post(
        f"/api/signed-update-packages/{staged['id']}/rollback",
        json={"reason": "客户管理员确认回滚知识修复包。"},
        headers=headers,
    )
    assert rollback_res.status_code == 200
    refresh_after_rollback = client.post(
        f"/api/tenants/{tenant['id']}/diagnostic-remediation-requests/{remediation['id']}/signed-update-plan",
        json={
            "signed_update_package_id": staged["id"],
            "operator_note": "回滚后刷新受控更新计划。",
        },
        headers=headers,
    )
    assert refresh_after_rollback.status_code == 200
    rolled_plan = refresh_after_rollback.json()["update_request_manifest"]["signed_update_control_plan"]
    assert rolled_plan["signed_update_package"]["status"] == "rolled_back"
    assert _step_status(rolled_plan, "rollback") == "passed"

    audit_actions = [event.action for event in db_session.query(AuditEvent).all()]
    assert "diagnostic_remediation.signed_update_plan_created" in audit_actions
    assert "signed_update_package.applied" in audit_actions
    assert "signed_update_package.rolled_back" in audit_actions


def test_remediation_request_cannot_be_created_from_rejected_intake(client, db_session) -> None:
    tenant = _create_tenant(client, "拒收处理单客户", "diagnostics-remediation-reject")
    _owner_role, _owner, token = _bootstrap_owner(client, tenant)
    headers = {"Authorization": f"Bearer {token}"}

    package_res = client.post(
        f"/api/tenants/{tenant['id']}/diagnostic-upload-package",
        json={"authorization_note": "客户管理员确认授权上传本次脱敏诊断包。"},
        headers=headers,
    )
    assert package_res.status_code == 200
    upload_package = package_res.json()
    upload_package["safety"]["raw_message_text_included"] = True
    intake_res = client.post(
        f"/api/tenants/{tenant['id']}/diagnostic-intake-records",
        json={"upload_package": upload_package, "source_channel": "manual_transfer"},
        headers=headers,
    )
    assert intake_res.status_code == 200
    intake = intake_res.json()
    assert intake["status"] == "rejected"

    create_res = client.post(
        f"/api/tenants/{tenant['id']}/diagnostic-intake-records/{intake['id']}/remediation-requests",
        json={"request_type": "knowledge_update"},
        headers=headers,
    )

    assert create_res.status_code == 422
    assert "rejected" in create_res.json()["detail"]


def test_agent_cannot_use_diagnostic_intake_records(client, db_session) -> None:
    tenant = _create_tenant(client, "接收台权限客户", "diagnostics-intake-permission")
    _owner_role, _owner, owner_token = _bootstrap_owner(client, tenant)
    owner_headers = {"Authorization": f"Bearer {owner_token}"}
    agent_role = _create_role(client, tenant["id"], "agent", "客服", owner_headers)
    user = User(
        tenant_id=tenant["id"],
        name="一线客服",
        email="intake-agent@example.com",
        password_hash=hash_password("ChangeMe123!"),
        status="active",
    )
    db_session.add(user)
    db_session.flush()
    db_session.add(UserRole(user_id=user.id, role_id=agent_role["id"]))
    db_session.commit()

    login = client.post(
        "/api/auth/login",
        json={"tenant_slug": tenant["slug"], "email": "intake-agent@example.com", "password": "ChangeMe123!"},
    )
    assert login.status_code == 200
    agent_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    res = client.get(f"/api/tenants/{tenant['id']}/diagnostic-intake-records", headers=agent_headers)
    assert res.status_code == 403
