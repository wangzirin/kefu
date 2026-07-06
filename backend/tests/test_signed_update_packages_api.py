import base64
import hashlib
import json
from uuid import uuid4

from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15

from app.models import AuditEvent, LocalBackupRecord, TenantReplyStrategy, utc_now


def _canonical_json(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _bootstrap_user(client, *, slug: str, email: str, role_code: str = "owner") -> tuple[dict, dict, str]:
    tenant_res = client.post("/api/tenants", json={"name": f"{slug} 客户", "slug": slug})
    assert tenant_res.status_code == 201
    tenant = tenant_res.json()

    role_res = client.post(
        f"/api/tenants/{tenant['id']}/roles",
        json={"code": role_code, "name": role_code},
    )
    assert role_res.status_code == 201
    role = role_res.json()

    user_res = client.post(
        f"/api/tenants/{tenant['id']}/users",
        json={"name": f"{role_code} 用户", "email": email, "password": "ChangeMe123!"},
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
    return tenant, user, login_res.json()["access_token"]


def _insert_verified_local_backup_restore_dry_run(db_session, tenant_id: int) -> dict:
    backup_id = f"test-local-backup-{uuid4().hex}"
    restore_dry_run = {
        "schema_version": "p3-06u-26h2l.restore_dry_run.v1",
        "restore_dry_run_id": f"restore-dry-run-{backup_id}",
        "backup_id": backup_id,
        "tenant_id": tenant_id,
        "rehearsal_ready": True,
        "can_restore_now": False,
        "safety": {
            "dry_run": True,
            "can_restore_now": False,
            "database_file_replaced": False,
            "live_restore_performed": False,
            "requires_fresh_pre_restore_backup": True,
        },
    }
    now = utc_now()
    record = LocalBackupRecord(
        tenant_id=tenant_id,
        backup_id=backup_id,
        backup_type="sqlite_database",
        status="verified",
        file_name=f"{backup_id}.sqlite3",
        file_path=f"/tmp/{backup_id}.sqlite3",
        file_size_bytes=1024,
        sha256="a" * 64,
        source_database_label="test.sqlite3",
        source_database_hash="b" * 64,
        restore_mode="manual_rehearsal_only",
        manifest_payload={"last_restore_dry_run": restore_dry_run},
        verified_at=now,
        created_at=now,
    )
    db_session.add(record)
    db_session.commit()
    return restore_dry_run


def _knowledge_update_payload() -> dict:
    return {
        "schema_version": "wanfa.knowledge_update_package.v1",
        "package_id": "pkg-signed-after-sales-20260703",
        "package_name": "签名售后知识修复包",
        "source_diagnostic_filename": "wanfa-diagnostic-local-20260703.json",
        "notes": "补充售后政策和回归题，不包含客户聊天原文。",
        "business_objects": [
            {
                "ref": "signed-lite-package",
                "type": "package",
                "title": "AI客服入门验证包",
                "aliases": ["入门版", "官网客服试点"],
                "summary": "适合先验证官网客服、核心问答、留资和转人工的小微企业。",
                "status": "active",
            }
        ],
        "object_knowledge_cards": [
            {
                "business_object_ref": "signed-lite-package",
                "question": "入门验证包适合什么客户？",
                "answer": "适合先验证官网客服、核心问题、留资和转人工流程的小微企业。复杂多渠道自动外发需要后续授权。",
                "trigger_keywords": ["入门验证", "官网客服", "小微企业"],
                "source": "signed_update_package",
                "status": "active",
            }
        ],
        "knowledge_documents": [
            {
                "title": "签名包售后退换政策",
                "source_type": "signed_update_package",
                "source_uri": "internal://policy/signed-after-sales-20260703",
                "tags": ["售后", "退换"],
                "status": "active",
                "raw_text": "客户咨询七天退换时，应先确认订单状态、商品状态和平台规则。不能承诺无条件退款。",
            }
        ],
        "evaluation_sets": [
            {
                "name": "签名包售后知识回归题集",
                "description": "验证签名售后政策是否能被检索命中。",
                "status": "active",
                "evaluation_mode": "customer_service_retrieval",
                "cases": [
                    {
                        "external_case_id": "signed-after-sales-001",
                        "question": "超过七天还能退货吗？",
                        "expected_terms": ["订单状态", "商品状态", "平台规则"],
                        "expected_source_uri": "internal://policy/signed-after-sales-20260703",
                        "forbidden_terms": ["无条件退款"],
                        "expected_human_review": False,
                        "allow_auto_reply": True,
                        "status": "active",
                    }
                ],
            }
        ],
    }


def _strategy_update_payload() -> dict:
    return {
        "schema_version": "wanfa.reply_strategy_update.v1",
        "strategy_id": "local-support-risk-policy",
        "strategy_version": "2026.07.03.strategy.1",
        "notes": "新增本地客服禁用承诺词和更保守的自动回复阈值。",
        "reply_policy": {
            "auto_reply_threshold": 0.82,
            "manual_review_threshold": 0.5,
            "blocked_policy_terms": ["终身保证"],
            "manual_review_terms": ["退一赔三"],
            "force_draft_only": True,
        },
        "model_routing": {
            "default_provider": "auto",
            "fast_model": "qwen3.6-flash",
            "standard_model": "qwen3.7-plus",
            "premium_model": "qwen3.7-max",
            "fallback_provider": "deepseek",
        },
    }


def _program_update_payload() -> dict:
    return {
        "schema_version": "wanfa.program_update_package.v1",
        "program_version": "0.1.1",
        "bundle": {
            "bundle_id": "wanfa-standard-ops-0.1.1-local",
            "platforms": ["darwin-arm64", "win32-x64"],
            "size_bytes": 2048,
            "sha256": "f" * 64,
        },
        "files": [
            {
                "path": "backend/app/main.py",
                "sha256": "a" * 64,
                "size_bytes": 1024,
            },
            {
                "path": "frontend/dist/index.html",
                "sha256": "b" * 64,
                "size_bytes": 1024,
            },
        ],
        "migrations": [
            {
                "id": "0030_program_update_placeholder",
                "mode": "dry_run_required",
                "description": "仅用于程序更新演练，不执行迁移。",
            }
        ],
        "services": ["backend", "frontend"],
        "rollback": {
            "requires_previous_bundle": True,
            "requires_database_backup": True,
        },
    }


def _signed_package(
    private_key: RSA.RsaKey,
    *,
    compatible_versions: list[str] | None = None,
    package_id: str = "wanfa-update-20260703-001",
    package_type: str = "knowledge",
    payload: dict | None = None,
) -> dict:
    payload_value = payload or {
        "operations": [
            {
                "target": "knowledge_documents",
                "action": "upsert",
                "count": 2,
                "summary": "补充售后政策和安装说明",
            }
        ],
        "safety": {
            "external_platform_write_performed": False,
            "provider_call_performed": False,
        },
    }
    manifest = {
        "schema_version": "wanfa.signed_update_manifest.v1",
        "package_id": package_id,
        "package_name": "本地知识与策略修复包",
        "package_type": package_type,
        "package_version": "2026.07.03.1",
        "product": "wanfa-standard-ops",
        "released_at": "2026-07-03T10:00:00+08:00",
        "compatible_app_versions": compatible_versions or ["0.1.0"],
        "requires_maintenance_window": package_type == "program",
        "payload_digest_sha256": hashlib.sha256(_canonical_json(payload_value)).hexdigest(),
        "payload_size_bytes": len(_canonical_json(payload_value)),
        "operations": [
            {
                "target": "reply_policy"
                if package_type == "strategy"
                else "program_bundle"
                if package_type == "program"
                else "knowledge_documents",
                "action": "upsert",
                "count": 1 if package_type in {"strategy", "program"} else 2,
                "summary": "更新回复策略"
                if package_type == "strategy"
                else "程序版本升级演练"
                if package_type == "program"
                else "补充售后政策和安装说明",
            }
        ],
    }
    digest = SHA256.new(_canonical_json(manifest))
    signature = base64.b64encode(pkcs1_15.new(private_key).sign(digest)).decode("ascii")
    return {
        "schema_version": "wanfa.signed_update_package.v1",
        "manifest": manifest,
        "payload": payload_value,
        "release_notes": "本更新包只用于签名预检测试，不执行程序替换。",
        "checksums": {"payload_sha256": manifest["payload_digest_sha256"]},
        "signature": {
            "algorithm": "rsa_pkcs1v15_sha256",
            "key_id": "test-release-key",
            "value": signature,
        },
    }


def _create_object_card(client, tenant_id: int, headers: dict) -> tuple[dict, dict]:
    object_res = client.post(
        f"/api/tenants/{tenant_id}/business-objects",
        headers=headers,
        json={
            "type": "package",
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


def _conversation_with_message(client, tenant_id: int, headers: dict, *, content: str) -> tuple[dict, dict]:
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
        json={"direction": "inbound", "sender_type": "visitor", "content": content},
    )
    assert message_res.status_code == 201
    return conversation, message_res.json()


def test_owner_can_preflight_valid_signed_update_package_without_applying(client, monkeypatch) -> None:
    key = RSA.generate(2048)
    monkeypatch.setenv(
        "WANFA_UPDATE_TRUSTED_PUBLIC_KEYS_JSON",
        json.dumps({"test-release-key": key.publickey().export_key().decode("utf-8")}),
    )
    tenant, _, token = _bootstrap_user(
        client,
        slug="signed-update-valid",
        email="signed-update-valid@example.com",
    )
    headers = {"Authorization": f"Bearer {token}"}

    res = client.post(
        f"/api/tenants/{tenant['id']}/signed-update-package/preflights",
        headers=headers,
        json={"package": _signed_package(key)},
    )

    assert res.status_code == 200
    payload = res.json()
    assert payload["dry_run"] is True
    assert payload["can_stage"] is True
    assert payload["can_apply_now"] is False
    assert payload["signature_status"]["verified"] is True
    assert payload["checksum_status"]["payload_digest_match"] is True
    assert payload["compatibility"]["compatible"] is True
    assert payload["backup_plan"]["required"] is True
    assert "knowledge_documents" in payload["backup_plan"]["resources"]
    assert payload["safety"]["external_write_performed"] is False
    assert payload["safety"]["program_execution_performed"] is False
    assert payload["safety"]["backup_created"] is False


def test_signed_update_preflight_blocks_tampered_payload(client, monkeypatch) -> None:
    key = RSA.generate(2048)
    monkeypatch.setenv(
        "WANFA_UPDATE_TRUSTED_PUBLIC_KEYS_JSON",
        json.dumps({"test-release-key": key.publickey().export_key().decode("utf-8")}),
    )
    tenant, _, token = _bootstrap_user(
        client,
        slug="signed-update-tampered",
        email="signed-update-tampered@example.com",
    )
    package = _signed_package(key)
    package["payload"]["operations"][0]["count"] = 99

    res = client.post(
        f"/api/tenants/{tenant['id']}/signed-update-package/preflights",
        headers={"Authorization": f"Bearer {token}"},
        json={"package": package},
    )

    assert res.status_code == 200
    payload = res.json()
    assert payload["can_stage"] is False
    assert payload["signature_status"]["verified"] is True
    assert payload["checksum_status"]["payload_digest_match"] is False
    assert any("payload 摘要" in error for error in payload["errors"])


def test_signed_update_preflight_blocks_incompatible_app_version(client, monkeypatch) -> None:
    key = RSA.generate(2048)
    monkeypatch.setenv(
        "WANFA_UPDATE_TRUSTED_PUBLIC_KEYS_JSON",
        json.dumps({"test-release-key": key.publickey().export_key().decode("utf-8")}),
    )
    tenant, _, token = _bootstrap_user(
        client,
        slug="signed-update-incompatible",
        email="signed-update-incompatible@example.com",
    )

    res = client.post(
        f"/api/tenants/{tenant['id']}/signed-update-package/preflights",
        headers={"Authorization": f"Bearer {token}"},
        json={"package": _signed_package(key, compatible_versions=["9.9.9"])},
    )

    assert res.status_code == 200
    payload = res.json()
    assert payload["can_stage"] is False
    assert payload["compatibility"]["compatible"] is False
    assert any("版本不兼容" in error for error in payload["errors"])


def test_signed_update_preflight_requires_update_permission(client, monkeypatch) -> None:
    key = RSA.generate(2048)
    monkeypatch.setenv(
        "WANFA_UPDATE_TRUSTED_PUBLIC_KEYS_JSON",
        json.dumps({"test-release-key": key.publickey().export_key().decode("utf-8")}),
    )
    tenant, _, owner_token = _bootstrap_user(
        client,
        slug="signed-update-agent-blocked",
        email="signed-update-owner@example.com",
        role_code="owner",
    )
    owner_headers = {"Authorization": f"Bearer {owner_token}"}
    agent_role = client.post(
        f"/api/tenants/{tenant['id']}/roles",
        headers=owner_headers,
        json={"code": "agent", "name": "客服坐席"},
    ).json()
    agent_res = client.post(
        f"/api/tenants/{tenant['id']}/users",
        headers=owner_headers,
        json={"name": "客服坐席", "email": "signed-update-agent@example.com", "password": "ChangeMe123!"},
    )
    assert agent_res.status_code == 201
    assign_res = client.post(
        f"/api/users/{agent_res.json()['id']}/roles",
        headers=owner_headers,
        json={"role_id": agent_role["id"]},
    )
    assert assign_res.status_code == 201
    agent_login = client.post(
        "/api/auth/login",
        json={
            "tenant_slug": tenant["slug"],
            "email": "signed-update-agent@example.com",
            "password": "ChangeMe123!",
        },
    )
    assert agent_login.status_code == 200

    forbidden = client.post(
        f"/api/tenants/{tenant['id']}/signed-update-package/preflights",
        headers={"Authorization": f"Bearer {agent_login.json()['access_token']}"},
        json={"package": _signed_package(key)},
    )
    assert forbidden.status_code == 403


def test_owner_can_stage_valid_signed_update_package_without_applying(client, monkeypatch) -> None:
    key = RSA.generate(2048)
    monkeypatch.setenv(
        "WANFA_UPDATE_TRUSTED_PUBLIC_KEYS_JSON",
        json.dumps({"test-release-key": key.publickey().export_key().decode("utf-8")}),
    )
    tenant, _, token = _bootstrap_user(
        client,
        slug="signed-update-stage-valid",
        email="signed-update-stage-valid@example.com",
    )
    headers = {"Authorization": f"Bearer {token}"}

    res = client.post(
        f"/api/tenants/{tenant['id']}/signed-update-package/staged",
        headers=headers,
        json={"package": _signed_package(key)},
    )

    assert res.status_code == 201
    payload = res.json()
    assert payload["status"] == "staged"
    assert payload["package_id"] == "wanfa-update-20260703-001"
    assert payload["package_type"] == "knowledge"
    assert payload["can_apply_now"] is False
    assert payload["backup_required"] is True
    assert payload["backup_created"] is False
    assert payload["safety"]["external_write_performed"] is False
    assert payload["safety"]["program_execution_performed"] is False
    assert payload["safety"]["database_migration_performed"] is False

    list_res = client.get(
        f"/api/tenants/{tenant['id']}/signed-update-package/staged",
        headers=headers,
    )
    assert list_res.status_code == 200
    assert [item["package_id"] for item in list_res.json()] == ["wanfa-update-20260703-001"]


def test_stage_signed_update_blocks_tampered_package(client, monkeypatch) -> None:
    key = RSA.generate(2048)
    monkeypatch.setenv(
        "WANFA_UPDATE_TRUSTED_PUBLIC_KEYS_JSON",
        json.dumps({"test-release-key": key.publickey().export_key().decode("utf-8")}),
    )
    tenant, _, token = _bootstrap_user(
        client,
        slug="signed-update-stage-tampered",
        email="signed-update-stage-tampered@example.com",
    )
    package = _signed_package(key)
    package["payload"]["operations"][0]["count"] = 99

    res = client.post(
        f"/api/tenants/{tenant['id']}/signed-update-package/staged",
        headers={"Authorization": f"Bearer {token}"},
        json={"package": package},
    )

    assert res.status_code == 400
    payload = res.json()
    assert payload["detail"]["can_stage"] is False
    assert any("payload 摘要" in error for error in payload["detail"]["errors"])


def test_stage_signed_update_requires_update_permission(client, monkeypatch) -> None:
    key = RSA.generate(2048)
    monkeypatch.setenv(
        "WANFA_UPDATE_TRUSTED_PUBLIC_KEYS_JSON",
        json.dumps({"test-release-key": key.publickey().export_key().decode("utf-8")}),
    )
    tenant, _, owner_token = _bootstrap_user(
        client,
        slug="signed-update-stage-agent-blocked",
        email="signed-update-stage-owner@example.com",
        role_code="owner",
    )
    owner_headers = {"Authorization": f"Bearer {owner_token}"}
    agent_role = client.post(
        f"/api/tenants/{tenant['id']}/roles",
        headers=owner_headers,
        json={"code": "agent", "name": "客服坐席"},
    ).json()
    agent_res = client.post(
        f"/api/tenants/{tenant['id']}/users",
        headers=owner_headers,
        json={"name": "客服坐席", "email": "signed-update-stage-agent@example.com", "password": "ChangeMe123!"},
    )
    assert agent_res.status_code == 201
    assign_res = client.post(
        f"/api/users/{agent_res.json()['id']}/roles",
        headers=owner_headers,
        json={"role_id": agent_role["id"]},
    )
    assert assign_res.status_code == 201
    agent_login = client.post(
        "/api/auth/login",
        json={
            "tenant_slug": tenant["slug"],
            "email": "signed-update-stage-agent@example.com",
            "password": "ChangeMe123!",
        },
    )
    assert agent_login.status_code == 200

    forbidden = client.post(
        f"/api/tenants/{tenant['id']}/signed-update-package/staged",
        headers={"Authorization": f"Bearer {agent_login.json()['access_token']}"},
        json={"package": _signed_package(key)},
    )
    assert forbidden.status_code == 403


def test_owner_can_apply_staged_knowledge_update_package_and_rollback(client, monkeypatch, db_session) -> None:
    key = RSA.generate(2048)
    monkeypatch.setenv(
        "WANFA_UPDATE_TRUSTED_PUBLIC_KEYS_JSON",
        json.dumps({"test-release-key": key.publickey().export_key().decode("utf-8")}),
    )
    tenant, _, token = _bootstrap_user(
        client,
        slug="signed-update-apply-knowledge",
        email="signed-update-apply-knowledge@example.com",
    )
    headers = {"Authorization": f"Bearer {token}"}
    package = _signed_package(
        key,
        package_id="wanfa-update-apply-knowledge-001",
        payload=_knowledge_update_payload(),
    )
    staged_res = client.post(
        f"/api/tenants/{tenant['id']}/signed-update-package/staged",
        headers=headers,
        json={"package": package},
    )
    assert staged_res.status_code == 201, staged_res.json()
    staged = staged_res.json()
    _insert_verified_local_backup_restore_dry_run(db_session, tenant["id"])

    apply_res = client.post(
        f"/api/signed-update-packages/{staged['id']}/apply",
        headers=headers,
        json={"reason": "应用签名知识修复包"},
    )

    assert apply_res.status_code == 200
    applied = apply_res.json()
    assert applied["status"] == "applied"
    assert applied["backup_created"] is True
    assert applied["can_apply_now"] is False
    assert applied["knowledge_import_batch_id"] is not None
    assert applied["backup_plan"]["created"] is True
    assert applied["backup_plan"]["snapshot"]["scope"] == "pre_import_counts_only"
    assert applied["apply_result"]["import_batch_id"] == applied["knowledge_import_batch_id"]
    assert applied["safety"]["external_write_performed"] is False
    assert any(check["status"] == "passed" for check in applied["health_checks"])

    documents_res = client.get(f"/api/tenants/{tenant['id']}/knowledge-documents?status=active", headers=headers)
    assert documents_res.status_code == 200
    assert documents_res.json()["total"] == 1

    rollback_res = client.post(
        f"/api/signed-update-packages/{staged['id']}/rollback",
        headers=headers,
        json={"reason": "回滚签名知识修复包"},
    )
    assert rollback_res.status_code == 200
    rolled_back = rollback_res.json()
    assert rolled_back["status"] == "rolled_back"
    assert rolled_back["rollback_result"]["rollback_status"] == "rolled_back"
    assert rolled_back["safety"]["external_write_performed"] is False

    active_documents_res = client.get(
        f"/api/tenants/{tenant['id']}/knowledge-documents?status=active",
        headers=headers,
    )
    assert active_documents_res.status_code == 200
    assert active_documents_res.json()["total"] == 0

    audit_actions = [event.action for event in db_session.query(AuditEvent).all()]
    assert "signed_update_package.applied" in audit_actions
    assert "signed_update_package.rolled_back" in audit_actions


def test_apply_signed_update_requires_verified_backup_restore_dry_run(client, monkeypatch) -> None:
    key = RSA.generate(2048)
    monkeypatch.setenv(
        "WANFA_UPDATE_TRUSTED_PUBLIC_KEYS_JSON",
        json.dumps({"test-release-key": key.publickey().export_key().decode("utf-8")}),
    )
    tenant, _, token = _bootstrap_user(
        client,
        slug="signed-update-apply-requires-backup",
        email="signed-update-apply-requires-backup@example.com",
    )
    headers = {"Authorization": f"Bearer {token}"}
    staged_res = client.post(
        f"/api/tenants/{tenant['id']}/signed-update-package/staged",
        headers=headers,
        json={
            "package": _signed_package(
                key,
                package_id="wanfa-update-requires-backup-001",
                payload=_knowledge_update_payload(),
            )
        },
    )
    assert staged_res.status_code == 201, staged_res.json()
    staged = staged_res.json()

    apply_res = client.post(
        f"/api/signed-update-packages/{staged['id']}/apply",
        headers=headers,
        json={"reason": "尝试绕过备份应用签名知识包"},
    )

    assert apply_res.status_code == 409
    assert "verified local backup and restore dry-run evidence" in apply_res.json()["detail"]


def test_apply_signed_update_blocks_program_package_in_this_slice(client, monkeypatch) -> None:
    key = RSA.generate(2048)
    monkeypatch.setenv(
        "WANFA_UPDATE_TRUSTED_PUBLIC_KEYS_JSON",
        json.dumps({"test-release-key": key.publickey().export_key().decode("utf-8")}),
    )
    tenant, _, token = _bootstrap_user(
        client,
        slug="signed-update-apply-program-blocked",
        email="signed-update-apply-program-blocked@example.com",
    )
    headers = {"Authorization": f"Bearer {token}"}
    staged = client.post(
        f"/api/tenants/{tenant['id']}/signed-update-package/staged",
        headers=headers,
        json={
            "package": _signed_package(
                key,
                package_id="wanfa-update-program-blocked-001",
                package_type="program",
            )
        },
    ).json()

    apply_res = client.post(
        f"/api/signed-update-packages/{staged['id']}/apply",
        headers=headers,
        json={"reason": "尝试应用程序包"},
    )

    assert apply_res.status_code == 409
    assert "program update is not supported" in apply_res.json()["detail"]


def test_owner_can_create_program_update_dry_run_without_applying(client, monkeypatch, db_session) -> None:
    key = RSA.generate(2048)
    monkeypatch.setenv(
        "WANFA_UPDATE_TRUSTED_PUBLIC_KEYS_JSON",
        json.dumps({"test-release-key": key.publickey().export_key().decode("utf-8")}),
    )
    tenant, _, token = _bootstrap_user(
        client,
        slug="signed-update-program-dry-run",
        email="signed-update-program-dry-run@example.com",
    )
    headers = {"Authorization": f"Bearer {token}"}
    staged_res = client.post(
        f"/api/tenants/{tenant['id']}/signed-update-package/staged",
        headers=headers,
        json={
            "package": _signed_package(
                key,
                package_id="wanfa-update-program-dry-run-001",
                package_type="program",
                payload=_program_update_payload(),
            )
        },
    )
    assert staged_res.status_code == 201, staged_res.json()
    staged = staged_res.json()

    dry_run_res = client.post(
        f"/api/signed-update-packages/{staged['id']}/program-dry-run",
        headers=headers,
        json={"reason": "客户管理员只生成程序更新演练计划。"},
    )

    assert dry_run_res.status_code == 200
    dry_run = dry_run_res.json()
    assert dry_run["status"] == "staged"
    assert dry_run["package_type"] == "program"
    assert dry_run["backup_created"] is False
    assert dry_run["can_apply_now"] is False
    assert dry_run["safety"]["dry_run_only"] is True
    assert dry_run["safety"]["program_execution_performed"] is False
    assert dry_run["safety"]["database_migration_performed"] is False
    assert dry_run["safety"]["external_write_performed"] is False
    assert dry_run["preflight_result"]["program_dry_run_result"]["dry_run_status"] == "planned"
    assert dry_run["preflight_result"]["program_dry_run_result"]["requires_maintenance_window"] is True
    assert "replace_program_files" in dry_run["preflight_result"]["program_dry_run_result"]["blocked_actions"]
    assert any(check["id"] == "program_update_dry_run" and check["status"] == "passed" for check in dry_run["health_checks"])

    apply_res = client.post(
        f"/api/signed-update-packages/{staged['id']}/apply",
        headers=headers,
        json={"reason": "演练后仍尝试真实应用程序包"},
    )
    assert apply_res.status_code == 409
    assert "program update is not supported" in apply_res.json()["detail"]

    audit_actions = [event.action for event in db_session.query(AuditEvent).all()]
    assert "signed_update_package.program_dry_run" in audit_actions
    assert "signed_update_package.applied" not in audit_actions


def test_program_update_dry_run_requires_update_permission(client, monkeypatch) -> None:
    key = RSA.generate(2048)
    monkeypatch.setenv(
        "WANFA_UPDATE_TRUSTED_PUBLIC_KEYS_JSON",
        json.dumps({"test-release-key": key.publickey().export_key().decode("utf-8")}),
    )
    tenant, _, owner_token = _bootstrap_user(
        client,
        slug="signed-update-program-dry-run-agent-blocked",
        email="signed-update-program-dry-run-owner@example.com",
        role_code="owner",
    )
    owner_headers = {"Authorization": f"Bearer {owner_token}"}
    staged = client.post(
        f"/api/tenants/{tenant['id']}/signed-update-package/staged",
        headers=owner_headers,
        json={
            "package": _signed_package(
                key,
                package_id="wanfa-update-program-dry-run-agent-blocked-001",
                package_type="program",
                payload=_program_update_payload(),
            )
        },
    ).json()
    agent_role = client.post(
        f"/api/tenants/{tenant['id']}/roles",
        headers=owner_headers,
        json={"code": "agent", "name": "客服坐席"},
    ).json()
    agent_res = client.post(
        f"/api/tenants/{tenant['id']}/users",
        headers=owner_headers,
        json={"name": "客服坐席", "email": "signed-update-program-dry-run-agent@example.com", "password": "ChangeMe123!"},
    )
    assert agent_res.status_code == 201
    assign_res = client.post(
        f"/api/users/{agent_res.json()['id']}/roles",
        headers=owner_headers,
        json={"role_id": agent_role["id"]},
    )
    assert assign_res.status_code == 201
    agent_login = client.post(
        "/api/auth/login",
        json={
            "tenant_slug": tenant["slug"],
            "email": "signed-update-program-dry-run-agent@example.com",
            "password": "ChangeMe123!",
        },
    )
    assert agent_login.status_code == 200

    forbidden = client.post(
        f"/api/signed-update-packages/{staged['id']}/program-dry-run",
        headers={"Authorization": f"Bearer {agent_login.json()['access_token']}"},
        json={"reason": "坐席尝试生成程序更新演练"},
    )

    assert forbidden.status_code == 403


def test_owner_can_apply_strategy_update_package_and_rollback_policy_effect(client, monkeypatch, db_session) -> None:
    key = RSA.generate(2048)
    monkeypatch.setenv(
        "WANFA_UPDATE_TRUSTED_PUBLIC_KEYS_JSON",
        json.dumps({"test-release-key": key.publickey().export_key().decode("utf-8")}),
    )
    tenant, _, token = _bootstrap_user(
        client,
        slug="signed-update-apply-strategy",
        email="signed-update-apply-strategy@example.com",
    )
    headers = {"Authorization": f"Bearer {token}"}
    _create_object_card(client, tenant["id"], headers)
    _, message = _conversation_with_message(
        client,
        tenant["id"],
        headers,
        content="入门验证包可以终身保证效果吗？",
    )
    package = _signed_package(
        key,
        package_id="wanfa-update-apply-strategy-001",
        package_type="strategy",
        payload=_strategy_update_payload(),
    )
    staged_res = client.post(
        f"/api/tenants/{tenant['id']}/signed-update-package/staged",
        headers=headers,
        json={"package": package},
    )
    assert staged_res.status_code == 201, staged_res.json()
    staged = staged_res.json()
    _insert_verified_local_backup_restore_dry_run(db_session, tenant["id"])

    apply_res = client.post(
        f"/api/signed-update-packages/{staged['id']}/apply",
        headers=headers,
        json={"reason": "应用本地回复策略修复包"},
    )

    assert apply_res.status_code == 200
    applied = apply_res.json()
    assert applied["status"] == "applied"
    assert applied["package_type"] == "strategy"
    assert applied["backup_created"] is True
    assert applied["backup_plan"]["scope"] == "reply_strategy_config_snapshot"
    assert applied["apply_result"]["strategy_version"] == "2026.07.03.strategy.1"
    assert applied["safety"]["external_write_performed"] is False
    assert any(check["status"] == "passed" for check in applied["health_checks"])

    active_strategy = (
        db_session.query(TenantReplyStrategy)
        .filter(TenantReplyStrategy.tenant_id == tenant["id"], TenantReplyStrategy.status == "active")
        .one()
    )
    assert active_strategy.strategy_id == "local-support-risk-policy"
    assert active_strategy.strategy_payload["reply_policy"]["blocked_policy_terms"] == ["终身保证"]

    blocked_decision = client.post(
        f"/api/messages/{message['id']}/reply-decisions",
        headers=headers,
        json={"idempotency_key": "strategy-blocked-after-apply"},
    )
    assert blocked_decision.status_code == 201
    blocked_payload = blocked_decision.json()
    assert blocked_payload["state"] == "blocked_by_policy"
    assert blocked_payload["reason"] == "blocked_policy_terms"
    assert "终身保证" in blocked_payload["decision_payload"]["blocked_terms"]
    assert blocked_payload["decision_payload"]["strategy"]["strategy_version"] == "2026.07.03.strategy.1"

    rollback_res = client.post(
        f"/api/signed-update-packages/{staged['id']}/rollback",
        headers=headers,
        json={"reason": "回滚本地回复策略修复包"},
    )
    assert rollback_res.status_code == 200
    rolled_back = rollback_res.json()
    assert rolled_back["status"] == "rolled_back"
    assert rolled_back["rollback_result"]["rollback_status"] == "disabled_strategy"
    assert rolled_back["safety"]["external_write_performed"] is False

    after_rollback_strategy = db_session.query(TenantReplyStrategy).filter(TenantReplyStrategy.tenant_id == tenant["id"]).one()
    assert after_rollback_strategy.status == "inactive"

    ready_decision = client.post(
        f"/api/messages/{message['id']}/reply-decisions",
        headers=headers,
        json={"idempotency_key": "strategy-ready-after-rollback"},
    )
    assert ready_decision.status_code == 201
    ready_payload = ready_decision.json()
    assert ready_payload["state"] == "auto_reply_ready"
    assert ready_payload["decision_payload"]["strategy"]["strategy_version"] == ""
    assert "终身保证" not in ready_payload["decision_payload"]["blocked_terms"]

    audit_actions = [event.action for event in db_session.query(AuditEvent).all()]
    assert "signed_update_package.strategy_applied" in audit_actions
    assert "signed_update_package.strategy_rolled_back" in audit_actions


def test_apply_signed_update_requires_update_permission(client, monkeypatch) -> None:
    key = RSA.generate(2048)
    monkeypatch.setenv(
        "WANFA_UPDATE_TRUSTED_PUBLIC_KEYS_JSON",
        json.dumps({"test-release-key": key.publickey().export_key().decode("utf-8")}),
    )
    tenant, _, owner_token = _bootstrap_user(
        client,
        slug="signed-update-apply-agent-blocked",
        email="signed-update-apply-owner@example.com",
        role_code="owner",
    )
    owner_headers = {"Authorization": f"Bearer {owner_token}"}
    staged = client.post(
        f"/api/tenants/{tenant['id']}/signed-update-package/staged",
        headers=owner_headers,
        json={
            "package": _signed_package(
                key,
                package_id="wanfa-update-apply-agent-blocked-001",
                payload=_knowledge_update_payload(),
            )
        },
    ).json()
    agent_role = client.post(
        f"/api/tenants/{tenant['id']}/roles",
        headers=owner_headers,
        json={"code": "agent", "name": "客服坐席"},
    ).json()
    agent_res = client.post(
        f"/api/tenants/{tenant['id']}/users",
        headers=owner_headers,
        json={"name": "客服坐席", "email": "signed-update-apply-agent@example.com", "password": "ChangeMe123!"},
    )
    assert agent_res.status_code == 201
    assign_res = client.post(
        f"/api/users/{agent_res.json()['id']}/roles",
        headers=owner_headers,
        json={"role_id": agent_role["id"]},
    )
    assert assign_res.status_code == 201
    agent_login = client.post(
        "/api/auth/login",
        json={
            "tenant_slug": tenant["slug"],
            "email": "signed-update-apply-agent@example.com",
            "password": "ChangeMe123!",
        },
    )
    assert agent_login.status_code == 200

    forbidden = client.post(
        f"/api/signed-update-packages/{staged['id']}/apply",
        headers={"Authorization": f"Bearer {agent_login.json()['access_token']}"},
        json={"reason": "坐席尝试应用"},
    )
    assert forbidden.status_code == 403
