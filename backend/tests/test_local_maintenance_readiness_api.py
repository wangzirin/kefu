from app.models import (
    AuditEvent,
    DiagnosticIntakeRecord,
    DiagnosticRemediationRequest,
    LocalBackupRecord,
    SignedUpdatePackage,
    utc_now,
)


def _create_tenant(client, name: str, slug: str) -> dict:
    res = client.post("/api/tenants", json={"name": name, "slug": slug})
    assert res.status_code == 201
    return res.json()


def _bootstrap_user(
    client,
    tenant: dict,
    *,
    role_code: str = "owner",
    email: str = "owner@example.com",
) -> tuple[dict, dict, str]:
    role_res = client.post(
        f"/api/tenants/{tenant['id']}/roles",
        json={"code": role_code, "name": role_code},
    )
    assert role_res.status_code == 201
    role = role_res.json()

    user_res = client.post(
        f"/api/tenants/{tenant['id']}/users",
        json={
            "name": f"{role_code} 用户",
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


def test_owner_reads_local_maintenance_readiness_with_full_evidence(client, db_session) -> None:
    tenant = _create_tenant(client, "本地维护客户", "local-maintenance-ready")
    _role, user, token = _bootstrap_user(client, tenant, email="local-maintenance-owner@example.com")
    now = utc_now()

    intake = DiagnosticIntakeRecord(
        tenant_id=tenant["id"],
        intake_id="intake-ready-001",
        status="in_review",
        validation_status="passed",
        package_filename="wanfa-upload-package.json",
        diagnostic_bundle_filename="wanfa-diagnostic.json",
        package_sha256="a" * 64,
        diagnostic_bundle_sha256="b" * 64,
        package_size_bytes=2048,
        source_channel="manual_transfer",
        authorization_summary={"authorized": True},
        safety={
            "remote_control_performed": False,
            "automatic_upload_performed": False,
            "raw_message_text_included": False,
        },
        package_payload={"diagnostic_bundle": {"filename": "wanfa-diagnostic.json"}},
        received_by_id=user["id"],
    )
    db_session.add(intake)
    db_session.flush()

    package = SignedUpdatePackage(
        tenant_id=tenant["id"],
        package_id="wanfa-update-ready-001",
        package_name="本地知识修复包",
        package_type="knowledge",
        package_version="2026.07.04.test",
        current_app_version="0.1.0",
        status="staged",
        package_digest_sha256="c" * 64,
        package_payload={"manifest": {"package_type": "knowledge"}},
        preflight_result={
            "safety": {
                "external_write_performed": False,
                "silent_update_performed": False,
                "automatic_update_performed": False,
            }
        },
        backup_plan={"resources": ["sqlite_database"]},
        health_checks=[],
        can_apply_now=False,
        backup_required=True,
        backup_created=False,
        staged_by_id=user["id"],
    )
    db_session.add(package)
    db_session.flush()

    remediation = DiagnosticRemediationRequest(
        tenant_id=tenant["id"],
        intake_record_id=intake.id,
        request_id="remediation-ready-001",
        request_type="knowledge_or_strategy_update",
        status="update_plan_prepared",
        priority="normal",
        title="本地知识修复处理单",
        summary="根据脱敏诊断包生成处理建议。",
        recommended_actions=[{"code": "knowledge_update"}],
        update_request_manifest={
            "signed_update_control_plan": {
                "schema_version": "p3-06u-26h2w6b.signed_update_control_plan.v1",
                "signed_update_package": {"id": package.id},
            }
        },
        safety={
            "remote_control_performed": False,
            "silent_update_performed": False,
            "customer_environment_write_performed": False,
        },
        created_by_id=user["id"],
        updated_by_id=user["id"],
    )
    backup = LocalBackupRecord(
        tenant_id=tenant["id"],
        backup_id="local-backup-ready-001",
        backup_type="sqlite_database",
        status="verified",
        file_name="wanfa-local-backup.sqlite3",
        file_path="/redacted/wanfa-local-backup.sqlite3",
        file_size_bytes=4096,
        sha256="d" * 64,
        source_database_label="wanfa-standard-ops.sqlite3",
        source_database_hash="e" * 64,
        restore_mode="manual_rehearsal_only",
        manifest_payload={
            "last_restore_dry_run": {
                "restore_dry_run_id": "restore-dry-run-ready-001",
                "rehearsal_ready": True,
                "can_restore_now": False,
            }
        },
        created_by_id=user["id"],
        created_at=now,
        verified_at=now,
    )
    db_session.add_all(
        [
            remediation,
            backup,
            AuditEvent(
                tenant_id=tenant["id"],
                actor_id=user["id"],
                action="diagnostic_intake.received",
                resource_type="diagnostic_intake",
                resource_id=intake.intake_id,
            ),
            AuditEvent(
                tenant_id=tenant["id"],
                actor_id=user["id"],
                action="diagnostic_remediation.signed_update_plan_created",
                resource_type="diagnostic_remediation",
                resource_id=remediation.request_id,
            ),
            AuditEvent(
                tenant_id=tenant["id"],
                actor_id=user["id"],
                action="local_backup.restore_dry_run_created",
                resource_type="local_backup",
                resource_id=backup.backup_id,
            ),
        ]
    )
    db_session.commit()

    res = client.get(
        f"/api/tenants/{tenant['id']}/local-maintenance/readiness",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert res.status_code == 200
    body = res.json()
    assert body["schema_version"] == "p3-06u-26h2w8b.local_maintenance_readiness.v1"
    assert body["maturity_status"] == "ready_for_rehearsal"
    assert body["ready_for_customer_maintenance_rehearsal"] is True
    assert body["counts"]["diagnostic_intake_accepted"] == 1
    assert body["counts"]["remediation_update_plan_prepared"] == 1
    assert body["counts"]["signed_update_package_total"] == 1
    assert body["counts"]["local_backup_verified"] == 1
    assert body["counts"]["restore_dry_run_total"] == 1
    assert body["blockers"] == []
    assert body["safety"]["external_write_performed"] is False
    assert body["safety"]["silent_update_performed"] is False
    assert body["safety"]["manual_transfer_required"] is True
    assert body["latest"]["signed_update_package"]["can_apply_now"] is False
    assert {gate["code"]: gate["status"] for gate in body["gates"]}["restore_dry_run"] == "passed"


def test_agent_cannot_read_local_maintenance_readiness(client) -> None:
    tenant = _create_tenant(client, "权限客户", "local-maintenance-agent-blocked")
    _role, _user, token = _bootstrap_user(
        client,
        tenant,
        role_code="agent",
        email="local-maintenance-agent@example.com",
    )

    res = client.get(
        f"/api/tenants/{tenant['id']}/local-maintenance/readiness",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert res.status_code == 403
