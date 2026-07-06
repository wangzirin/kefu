from collections.abc import Generator
import json
from pathlib import Path

from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.db.session import get_db
from app.main import create_app
from app.models import AuditEvent, KnowledgeDocument, LocalBackupRecord


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


@pytest.fixture()
def file_sqlite_client(tmp_path, monkeypatch) -> Generator[tuple[TestClient, Session, Path], None, None]:
    database_path = tmp_path / "wanfa-local-test.sqlite3"
    backup_dir = tmp_path / "local-backups"
    monkeypatch.setenv("WANFA_LOCAL_BACKUP_DIR", str(backup_dir))
    engine = create_engine(
        f"sqlite+pysqlite:///{database_path}",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    session = factory()
    app = create_app()

    def override_db():
        yield session

    app.dependency_overrides[get_db] = override_db
    try:
        yield TestClient(app), session, backup_dir
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


def test_owner_can_create_and_verify_file_sqlite_backup(file_sqlite_client) -> None:
    client, db_session, backup_dir = file_sqlite_client
    tenant = _create_tenant(client, "本地客户", "local-backup-safe")
    _owner_role, _owner, token = _bootstrap_owner(client, tenant, "local-backup-owner@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    db_session.add(
        KnowledgeDocument(
            tenant_id=tenant["id"],
            title="备份测试知识",
            raw_text="用于确认备份文件包含当前本地库数据。",
            status="active",
            ingestion_status="indexed",
            chunk_count=0,
        )
    )
    db_session.commit()

    create_res = client.post(
        f"/api/tenants/{tenant['id']}/local-backups",
        headers=headers,
        json={"reason": "更新包应用前创建本地物理备份。"},
    )

    assert create_res.status_code == 201
    backup = create_res.json()
    assert backup["status"] == "created"
    assert backup["backup_type"] == "sqlite_database"
    assert backup["restore_mode"] == "manual_rehearsal_only"
    assert backup["file_size_bytes"] > 0
    assert len(backup["sha256"]) == 64
    assert "file_path" not in backup
    assert backup["safety"]["external_upload_performed"] is False
    assert backup["safety"]["live_restore_performed"] is False
    assert backup["manifest_payload"]["restore"]["live_restore_performed"] is False
    assert (backup_dir / backup["file_name"]).exists()
    assert (backup_dir / backup["file_name"]).with_suffix(".manifest.json").exists()

    list_res = client.get(f"/api/tenants/{tenant['id']}/local-backups", headers=headers)
    assert list_res.status_code == 200
    assert [item["id"] for item in list_res.json()] == [backup["id"]]

    verify_res = client.post(
        f"/api/local-backups/{backup['id']}/verify",
        headers=headers,
        json={"reason": "售后更新前校验备份可读。"},
    )
    assert verify_res.status_code == 200
    verified = verify_res.json()
    assert verified["status"] == "verified"
    assert verified["verified_at"] is not None
    assert verified["manifest_payload"]["last_verification"]["integrity_check"] == "ok"
    assert verified["manifest_payload"]["last_verification"]["sha256_match"] is True

    events = list(db_session.scalars(select(AuditEvent).order_by(AuditEvent.id)).all())
    assert [event.action for event in events if event.resource_type == "local_backup"] == [
        "local_backup.created",
        "local_backup.verified",
    ]
    audit_payload = json.loads(events[-1].payload)
    assert audit_payload["restore_mode"] == "manual_rehearsal_only"


def _postgres_dry_run_manifest(**overrides) -> dict:
    payload = {
        "schema_version": "p3-06u-26h2w-nc8.postgres_backup_dry_run.v1",
        "created_at": "20260706T120000Z",
        "status": "postgres_backup_restore_readability_dry_run_ready",
        "backup_file": "postgres.dump",
        "backup_sha256": "a" * 64,
        "backup_size_bytes": 4096,
        "restore_list_file": "pg_restore_list.txt",
        "restore_list_size_bytes": 512,
        "pg_dump_completed": True,
        "pg_restore_list_completed": True,
        "live_restore_performed": False,
        "database_replaced": False,
        "program_files_replaced": False,
        "external_write_enabled": False,
        "trusted_inbound_worker_enabled": False,
        "manual_restore_window_required": True,
        "customer_admin_confirmation_required": True,
    }
    payload.update(overrides)
    return payload


def _postgres_temp_restore_manifest(**overrides) -> dict:
    payload = {
        "schema_version": "p3-06u-26h2w-nc12.postgres_temp_restore_rehearsal.v1",
        "created_at": "20260706T123000Z",
        "status": "postgres_temp_restore_rehearsal_ready",
        "restore_mode": "temporary_database_rehearsal_only",
        "backup_sha256": "d" * 64,
        "temp_database_name": "wanfa_restore_tmp_20260706_abcd12ef",
        "temp_database_created": True,
        "pg_restore_into_temp_completed": True,
        "health_checks_completed": True,
        "temp_database_dropped": True,
        "restored_table_count": 12,
        "health_check_count": 5,
        "live_restore_performed": False,
        "live_database_replaced": False,
        "database_replaced": False,
        "program_files_replaced": False,
        "external_write_enabled": False,
        "trusted_inbound_worker_enabled": False,
        "commands_executed_on_live_database": False,
        "backup_file_body_stored": False,
    }
    payload.update(overrides)
    return payload


def _postgres_formal_restore_preflight_confirmation(**overrides) -> dict:
    payload = {
        "schema_version": "p3-06u-26h2w-nc13.formal_restore_preflight_approval.v1",
        "status": "formal_restore_preflight_approval_ready",
        "backup_sha256": "f" * 64,
        "approver_role": "customer_admin",
        "approver_identifier_hash": "1" * 64,
        "maintenance_window_id": "window-20260706-restore",
        "approval_time": "2026-07-06T13:00:00+08:00",
        "maintenance_window_approved": True,
        "service_stop_window_acknowledged": True,
        "fresh_pre_restore_backup_required": True,
        "temporary_restore_verified": True,
        "post_restore_health_check_plan_acknowledged": True,
        "rollback_plan_acknowledged": True,
        "customer_admin_confirmed": True,
        "final_operator_confirmation_required": True,
        "live_restore_performed": False,
        "database_replaced": False,
        "program_files_replaced": False,
        "external_write_enabled": False,
        "trusted_inbound_worker_enabled": False,
        "real_platform_send_enabled": False,
        "commands_executed_on_live_database": False,
        "backup_file_body_stored": False,
        "raw_customer_signature_stored": False,
        "automatic_restore_enabled": False,
    }
    payload.update(overrides)
    return payload


def _postgres_formal_restore_execution_dry_run_manifest(**overrides) -> dict:
    payload = {
        "schema_version": "p3-06u-26h2w-nc14.formal_restore_execution_dry_run.v1",
        "status": "formal_restore_execution_dry_run_ready",
        "restore_mode": "formal_restore_execution_dry_run_only",
        "backup_sha256": "8" * 64,
        "restore_commands_rendered_not_executed": True,
        "restore_command_preview_hashes": ["2" * 64, "3" * 64, "4" * 64],
        "restore_command_preview_stored": False,
        "final_operator_confirmation_required": True,
        "service_stop_required": True,
        "fresh_pre_restore_backup_required": True,
        "post_restore_health_check_required": True,
        "rollback_plan_required": True,
        "manual_restore_window_required": True,
        "live_restore_performed": False,
        "database_replaced": False,
        "program_files_replaced": False,
        "external_write_enabled": False,
        "trusted_inbound_worker_enabled": False,
        "real_platform_send_enabled": False,
        "commands_executed_on_live_database": False,
        "pg_restore_executed_on_live_database": False,
        "automatic_restore_enabled": False,
        "backup_file_body_stored": False,
        "raw_restore_command_stored": False,
    }
    payload.update(overrides)
    return payload


def _postgres_formal_restore_runbook(**overrides) -> dict:
    payload = {
        "schema_version": "p3-06u-26h2w-nc15.formal_restore_runbook.v1",
        "status": "formal_restore_runbook_ready",
        "backup_sha256": "8" * 64,
        "runbook_version": "v1.0",
        "maintenance_window_id_hash": "a" * 64,
        "operator_identifier_hash": "b" * 64,
        "observer_identifier_hash": "c" * 64,
        "restore_command_preview_hashes": ["2" * 64, "3" * 64, "4" * 64],
        "maintenance_window_locked": True,
        "service_stop_sequence_documented": True,
        "fresh_pre_restore_backup_step_required": True,
        "final_operator_confirmation_required": True,
        "restore_command_hashes_reviewed": True,
        "post_restore_health_checks_documented": True,
        "rollback_decision_tree_documented": True,
        "customer_communication_plan_documented": True,
        "manual_execution_only": True,
        "live_restore_performed": False,
        "database_replaced": False,
        "program_files_replaced": False,
        "external_write_enabled": False,
        "trusted_inbound_worker_enabled": False,
        "real_platform_send_enabled": False,
        "commands_executed_on_live_database": False,
        "pg_restore_executed_on_live_database": False,
        "automatic_restore_enabled": False,
        "backup_file_body_stored": False,
        "raw_restore_command_stored": False,
        "restore_command_preview_stored": False,
        "runbook_sensitive_material_stored": False,
    }
    payload.update(overrides)
    return payload


def test_owner_can_register_postgres_backup_dry_run_manifest(client, db_session) -> None:
    tenant = _create_tenant(client, "PG 客户", "postgres-backup-register")
    _owner_role, _owner, token = _bootstrap_owner(client, tenant, "pg-backup-owner@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    res = client.post(
        f"/api/tenants/{tenant['id']}/local-backups/postgres-dry-run-manifests",
        headers=headers,
        json={
            "manifest_payload": _postgres_dry_run_manifest(),
            "reason": "客户本机执行 pg_dump + pg_restore --list 后登记证据。",
        },
    )

    assert res.status_code == 201
    record = res.json()
    assert record["status"] == "verified"
    assert record["backup_type"] == "postgres_pg_dump_custom"
    assert record["restore_mode"] == "pg_restore_list_rehearsal_only"
    assert record["file_size_bytes"] == 4096
    assert record["sha256"] == "a" * 64
    assert record["manifest_payload"]["registration"]["backup_file_body_stored"] is False
    assert record["manifest_payload"]["postgres_backup_dry_run_manifest"]["pg_restore_list_completed"] is True
    restore_dry_run = record["manifest_payload"]["last_restore_dry_run"]
    assert restore_dry_run["rehearsal_ready"] is True
    assert restore_dry_run["can_restore_now"] is False
    assert restore_dry_run["safety"]["database_file_replaced"] is False
    assert restore_dry_run["safety"]["live_restore_performed"] is False
    assert record["safety"]["live_restore_performed"] is False
    assert "file_path" not in record

    list_res = client.get(f"/api/tenants/{tenant['id']}/local-backups", headers=headers)
    assert list_res.status_code == 200
    assert list_res.json()[0]["backup_type"] == "postgres_pg_dump_custom"

    events = list(db_session.scalars(select(AuditEvent).order_by(AuditEvent.id)).all())
    assert "local_backup.postgres_dry_run_manifest_registered" in [event.action for event in events]
    audit_payload = json.loads(events[-1].payload)
    assert audit_payload["backup_file_body_stored"] is False
    assert audit_payload["live_restore_performed"] is False
    assert audit_payload["database_file_replaced"] is False


def test_owner_can_register_postgres_temp_restore_manifest_without_live_restore(client, db_session) -> None:
    tenant = _create_tenant(client, "PG 临时恢复客户", "postgres-temp-restore")
    _owner_role, _owner, token = _bootstrap_owner(client, tenant, "pg-temp-restore-owner@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    register_res = client.post(
        f"/api/tenants/{tenant['id']}/local-backups/postgres-dry-run-manifests",
        headers=headers,
        json={
            "manifest_payload": _postgres_dry_run_manifest(backup_sha256="d" * 64),
            "reason": "客户本机登记 PostgreSQL 备份可读性证据。",
        },
    )
    assert register_res.status_code == 201
    backup = register_res.json()

    temp_restore_res = client.post(
        f"/api/tenants/{tenant['id']}/local-backups/postgres-temp-restore-manifests",
        headers=headers,
        json={
            "backup_record_id": backup["id"],
            "manifest_payload": _postgres_temp_restore_manifest(),
            "reason": "客户本机把备份恢复到临时库并完成健康检查。",
        },
    )

    assert temp_restore_res.status_code == 201
    updated = temp_restore_res.json()
    temp_rehearsal = updated["manifest_payload"]["last_temp_restore_rehearsal"]
    assert temp_rehearsal["schema_version"] == "p3-06u-26h2w-nc12.postgres_temp_restore_manifest_record.v1"
    assert temp_rehearsal["restore_mode"] == "pg_restore_to_temporary_database_only"
    assert temp_rehearsal["can_restore_now"] is False
    assert temp_rehearsal["temporary_database"]["created"] is True
    assert temp_rehearsal["temporary_database"]["dropped"] is True
    assert temp_rehearsal["temporary_database"]["name_stored"] is False
    assert temp_rehearsal["safety"]["live_restore_performed"] is False
    assert temp_rehearsal["safety"]["database_replaced"] is False
    assert temp_rehearsal["safety"]["commands_executed_on_live_database"] is False
    stored_manifest = updated["manifest_payload"]["postgres_temp_restore_rehearsal_manifest"]
    assert "temp_database_name" not in stored_manifest
    assert stored_manifest["temp_database_name_stored"] is False
    assert len(stored_manifest["temp_database_name_hash"]) == 64

    events = list(db_session.scalars(select(AuditEvent).order_by(AuditEvent.id)).all())
    assert "local_backup.postgres_temp_restore_manifest_registered" in [event.action for event in events]
    audit_payload = json.loads(events[-1].payload)
    assert audit_payload["can_restore_now"] is False
    assert audit_payload["temp_database_dropped"] is True
    assert audit_payload["live_restore_performed"] is False
    assert audit_payload["database_replaced"] is False


def test_postgres_temp_restore_manifest_rejects_live_or_unsafe_database(client) -> None:
    tenant = _create_tenant(client, "PG 临时恢复风险客户", "postgres-temp-restore-risk")
    _owner_role, _owner, token = _bootstrap_owner(client, tenant, "pg-temp-risk-owner@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    register_res = client.post(
        f"/api/tenants/{tenant['id']}/local-backups/postgres-dry-run-manifests",
        headers=headers,
        json={"manifest_payload": _postgres_dry_run_manifest(backup_sha256="e" * 64)},
    )
    assert register_res.status_code == 201
    backup = register_res.json()

    live_res = client.post(
        f"/api/tenants/{tenant['id']}/local-backups/postgres-temp-restore-manifests",
        headers=headers,
        json={
            "backup_record_id": backup["id"],
            "manifest_payload": _postgres_temp_restore_manifest(
                backup_sha256="e" * 64,
                live_restore_performed=True,
            ),
        },
    )
    assert live_res.status_code == 409
    assert "live_restore_performed must be false" in live_res.json()["detail"]

    unsafe_db_res = client.post(
        f"/api/tenants/{tenant['id']}/local-backups/postgres-temp-restore-manifests",
        headers=headers,
        json={
            "backup_record_id": backup["id"],
            "manifest_payload": _postgres_temp_restore_manifest(
                backup_sha256="e" * 64,
                temp_database_name="wanfa_ops",
            ),
        },
    )
    assert unsafe_db_res.status_code == 409
    assert "temp_database_name must use a safe wanfa_restore_tmp_ prefix" in unsafe_db_res.json()["detail"]


def test_owner_can_register_postgres_formal_restore_preflight_without_executing_restore(client, db_session) -> None:
    tenant = _create_tenant(client, "PG 正式恢复门禁客户", "postgres-formal-restore-preflight")
    _owner_role, _owner, token = _bootstrap_owner(client, tenant, "pg-formal-preflight-owner@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    register_res = client.post(
        f"/api/tenants/{tenant['id']}/local-backups/postgres-dry-run-manifests",
        headers=headers,
        json={
            "manifest_payload": _postgres_dry_run_manifest(backup_sha256="f" * 64),
            "reason": "客户本机登记 PostgreSQL 备份可读性证据。",
        },
    )
    assert register_res.status_code == 201
    backup = register_res.json()

    plan_res = client.post(
        f"/api/local-backups/{backup['id']}/postgres-restore-rehearsal-plan",
        headers=headers,
        json={"reason": "客户管理员生成 PostgreSQL 恢复演练计划。"},
    )
    assert plan_res.status_code == 200

    temp_restore_res = client.post(
        f"/api/tenants/{tenant['id']}/local-backups/postgres-temp-restore-manifests",
        headers=headers,
        json={
            "backup_record_id": backup["id"],
            "manifest_payload": _postgres_temp_restore_manifest(backup_sha256="f" * 64),
            "reason": "客户本机把备份恢复到临时库并完成健康检查。",
        },
    )
    assert temp_restore_res.status_code == 201

    preflight_res = client.post(
        f"/api/tenants/{tenant['id']}/local-backups/postgres-formal-restore-preflight",
        headers=headers,
        json={
            "backup_record_id": backup["id"],
            "confirmation_payload": _postgres_formal_restore_preflight_confirmation(),
            "reason": "客户管理员登记正式恢复前置确认。",
        },
    )

    assert preflight_res.status_code == 201
    updated = preflight_res.json()
    preflight = updated["manifest_payload"]["last_formal_restore_preflight"]
    assert preflight["schema_version"] == "p3-06u-26h2w-nc13.formal_restore_preflight_approval_record.v1"
    assert preflight["formal_restore_sop_ready"] is True
    assert preflight["manual_restore_window_ready"] is True
    assert preflight["can_execute_restore_now"] is False
    assert preflight["can_execute_restore_in_app"] is False
    assert preflight["restore_execution_performed"] is False
    assert preflight["requires_final_operator_confirmation"] is True
    assert preflight["preflight_requirements"]["maintenance_window_id_stored"] is False
    assert "maintenance_window_id" not in updated["manifest_payload"]["postgres_formal_restore_preflight_confirmation"]
    assert preflight["safety"]["live_restore_performed"] is False
    assert preflight["safety"]["database_replaced"] is False
    assert preflight["safety"]["commands_executed_on_live_database"] is False

    events = list(db_session.scalars(select(AuditEvent).order_by(AuditEvent.id)).all())
    assert "local_backup.postgres_formal_restore_preflight_registered" in [event.action for event in events]
    audit_payload = json.loads(events[-1].payload)
    assert audit_payload["can_execute_restore_now"] is False
    assert audit_payload["can_execute_restore_in_app"] is False
    assert audit_payload["live_restore_performed"] is False
    assert audit_payload["database_replaced"] is False


def test_postgres_formal_restore_preflight_requires_temp_restore_and_rejects_live_flags(client) -> None:
    tenant = _create_tenant(client, "PG 正式恢复风险客户", "postgres-formal-restore-risk")
    _owner_role, _owner, token = _bootstrap_owner(client, tenant, "pg-formal-risk-owner@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    register_res = client.post(
        f"/api/tenants/{tenant['id']}/local-backups/postgres-dry-run-manifests",
        headers=headers,
        json={"manifest_payload": _postgres_dry_run_manifest(backup_sha256="f" * 64)},
    )
    assert register_res.status_code == 201
    backup = register_res.json()

    missing_temp_res = client.post(
        f"/api/tenants/{tenant['id']}/local-backups/postgres-formal-restore-preflight",
        headers=headers,
        json={
            "backup_record_id": backup["id"],
            "confirmation_payload": _postgres_formal_restore_preflight_confirmation(),
        },
    )
    assert missing_temp_res.status_code == 409
    assert "last_restore_rehearsal_plan is required" in missing_temp_res.json()["detail"]
    assert "last_temp_restore_rehearsal is required" in missing_temp_res.json()["detail"]

    plan_res = client.post(
        f"/api/local-backups/{backup['id']}/postgres-restore-rehearsal-plan",
        headers=headers,
        json={"reason": "客户管理员生成 PostgreSQL 恢复演练计划。"},
    )
    assert plan_res.status_code == 200
    temp_restore_res = client.post(
        f"/api/tenants/{tenant['id']}/local-backups/postgres-temp-restore-manifests",
        headers=headers,
        json={
            "backup_record_id": backup["id"],
            "manifest_payload": _postgres_temp_restore_manifest(backup_sha256="f" * 64),
        },
    )
    assert temp_restore_res.status_code == 201

    live_flag_res = client.post(
        f"/api/tenants/{tenant['id']}/local-backups/postgres-formal-restore-preflight",
        headers=headers,
        json={
            "backup_record_id": backup["id"],
            "confirmation_payload": _postgres_formal_restore_preflight_confirmation(
                live_restore_performed=True,
            ),
        },
    )
    assert live_flag_res.status_code == 409
    assert "live_restore_performed must be false" in live_flag_res.json()["detail"]


def test_owner_can_register_postgres_formal_restore_execution_dry_run_without_running_restore(
    client,
    db_session,
) -> None:
    tenant = _create_tenant(client, "PG 正式恢复执行演练客户", "postgres-formal-restore-exec-dry-run")
    _owner_role, _owner, token = _bootstrap_owner(client, tenant, "pg-formal-exec-owner@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    register_res = client.post(
        f"/api/tenants/{tenant['id']}/local-backups/postgres-dry-run-manifests",
        headers=headers,
        json={
            "manifest_payload": _postgres_dry_run_manifest(backup_sha256="8" * 64),
            "reason": "客户本机登记 PostgreSQL 备份可读性证据。",
        },
    )
    assert register_res.status_code == 201
    backup = register_res.json()

    plan_res = client.post(
        f"/api/local-backups/{backup['id']}/postgres-restore-rehearsal-plan",
        headers=headers,
        json={"reason": "客户管理员生成 PostgreSQL 恢复演练计划。"},
    )
    assert plan_res.status_code == 200

    temp_restore_res = client.post(
        f"/api/tenants/{tenant['id']}/local-backups/postgres-temp-restore-manifests",
        headers=headers,
        json={
            "backup_record_id": backup["id"],
            "manifest_payload": _postgres_temp_restore_manifest(backup_sha256="8" * 64),
            "reason": "客户本机把备份恢复到临时库并完成健康检查。",
        },
    )
    assert temp_restore_res.status_code == 201

    preflight_res = client.post(
        f"/api/tenants/{tenant['id']}/local-backups/postgres-formal-restore-preflight",
        headers=headers,
        json={
            "backup_record_id": backup["id"],
            "confirmation_payload": _postgres_formal_restore_preflight_confirmation(backup_sha256="8" * 64),
            "reason": "客户管理员登记正式恢复前置确认。",
        },
    )
    assert preflight_res.status_code == 201

    execution_dry_run_res = client.post(
        f"/api/tenants/{tenant['id']}/local-backups/postgres-formal-restore-execution-dry-run",
        headers=headers,
        json={
            "backup_record_id": backup["id"],
            "manifest_payload": _postgres_formal_restore_execution_dry_run_manifest(),
            "reason": "客户管理员登记正式恢复执行 dry-run 证据。",
        },
    )

    assert execution_dry_run_res.status_code == 201
    updated = execution_dry_run_res.json()
    execution_dry_run = updated["manifest_payload"]["last_formal_restore_execution_dry_run"]
    assert execution_dry_run["schema_version"] == "p3-06u-26h2w-nc14.formal_restore_execution_dry_run_record.v1"
    assert execution_dry_run["formal_restore_execution_dry_run_ready"] is True
    assert execution_dry_run["restore_commands_rendered_not_executed"] is True
    assert execution_dry_run["can_execute_restore_now"] is False
    assert execution_dry_run["can_execute_restore_in_app"] is False
    assert execution_dry_run["restore_execution_performed"] is False
    assert execution_dry_run["restore_command_preview_hashes"] == ["2" * 64, "3" * 64, "4" * 64]
    assert execution_dry_run["restore_command_preview_stored"] is False
    assert execution_dry_run["raw_restore_command_stored"] is False
    assert execution_dry_run["execution_safety"]["pg_restore_executed_on_live_database"] is False
    assert execution_dry_run["execution_safety"]["commands_executed_on_live_database"] is False
    assert execution_dry_run["safety"]["live_restore_performed"] is False
    assert execution_dry_run["safety"]["database_replaced"] is False
    stored_manifest = updated["manifest_payload"]["postgres_formal_restore_execution_dry_run_manifest"]
    assert stored_manifest["restore_command_preview_stored"] is False
    assert stored_manifest["raw_restore_command_stored"] is False

    events = list(db_session.scalars(select(AuditEvent).order_by(AuditEvent.id)).all())
    assert "local_backup.postgres_formal_restore_execution_dry_run_registered" in [
        event.action for event in events
    ]
    audit_payload = json.loads(events[-1].payload)
    assert audit_payload["formal_restore_execution_dry_run_ready"] is True
    assert audit_payload["restore_commands_rendered_not_executed"] is True
    assert audit_payload["can_execute_restore_now"] is False
    assert audit_payload["restore_execution_performed"] is False
    assert audit_payload["raw_restore_command_stored"] is False
    assert audit_payload["pg_restore_executed_on_live_database"] is False


def test_postgres_formal_restore_execution_dry_run_requires_preflight_and_rejects_live_flags(client) -> None:
    tenant = _create_tenant(client, "PG 正式恢复执行风险客户", "postgres-formal-restore-exec-risk")
    _owner_role, _owner, token = _bootstrap_owner(client, tenant, "pg-formal-exec-risk-owner@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    register_res = client.post(
        f"/api/tenants/{tenant['id']}/local-backups/postgres-dry-run-manifests",
        headers=headers,
        json={"manifest_payload": _postgres_dry_run_manifest(backup_sha256="9" * 64)},
    )
    assert register_res.status_code == 201
    backup = register_res.json()

    missing_preflight_res = client.post(
        f"/api/tenants/{tenant['id']}/local-backups/postgres-formal-restore-execution-dry-run",
        headers=headers,
        json={
            "backup_record_id": backup["id"],
            "manifest_payload": _postgres_formal_restore_execution_dry_run_manifest(backup_sha256="9" * 64),
        },
    )
    assert missing_preflight_res.status_code == 409
    assert "last_formal_restore_preflight is required" in missing_preflight_res.json()["detail"]

    plan_res = client.post(
        f"/api/local-backups/{backup['id']}/postgres-restore-rehearsal-plan",
        headers=headers,
        json={"reason": "客户管理员生成 PostgreSQL 恢复演练计划。"},
    )
    assert plan_res.status_code == 200
    temp_restore_res = client.post(
        f"/api/tenants/{tenant['id']}/local-backups/postgres-temp-restore-manifests",
        headers=headers,
        json={
            "backup_record_id": backup["id"],
            "manifest_payload": _postgres_temp_restore_manifest(backup_sha256="9" * 64),
        },
    )
    assert temp_restore_res.status_code == 201
    preflight_res = client.post(
        f"/api/tenants/{tenant['id']}/local-backups/postgres-formal-restore-preflight",
        headers=headers,
        json={
            "backup_record_id": backup["id"],
            "confirmation_payload": _postgres_formal_restore_preflight_confirmation(backup_sha256="9" * 64),
        },
    )
    assert preflight_res.status_code == 201

    live_flag_res = client.post(
        f"/api/tenants/{tenant['id']}/local-backups/postgres-formal-restore-execution-dry-run",
        headers=headers,
        json={
            "backup_record_id": backup["id"],
            "manifest_payload": _postgres_formal_restore_execution_dry_run_manifest(
                backup_sha256="9" * 64,
                pg_restore_executed_on_live_database=True,
            ),
        },
    )
    assert live_flag_res.status_code == 409
    assert "pg_restore_executed_on_live_database must be false" in live_flag_res.json()["detail"]


def test_owner_can_register_postgres_formal_restore_runbook_without_running_restore(
    client,
    db_session,
) -> None:
    tenant = _create_tenant(client, "PG 正式恢复 SOP 客户", "postgres-formal-restore-runbook")
    _owner_role, _owner, token = _bootstrap_owner(client, tenant, "pg-formal-runbook-owner@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    register_res = client.post(
        f"/api/tenants/{tenant['id']}/local-backups/postgres-dry-run-manifests",
        headers=headers,
        json={
            "manifest_payload": _postgres_dry_run_manifest(backup_sha256="8" * 64),
            "reason": "客户本机登记 PostgreSQL 备份可读性证据。",
        },
    )
    assert register_res.status_code == 201
    backup = register_res.json()

    plan_res = client.post(
        f"/api/local-backups/{backup['id']}/postgres-restore-rehearsal-plan",
        headers=headers,
        json={"reason": "客户管理员生成 PostgreSQL 恢复演练计划。"},
    )
    assert plan_res.status_code == 200
    temp_restore_res = client.post(
        f"/api/tenants/{tenant['id']}/local-backups/postgres-temp-restore-manifests",
        headers=headers,
        json={
            "backup_record_id": backup["id"],
            "manifest_payload": _postgres_temp_restore_manifest(backup_sha256="8" * 64),
            "reason": "客户本机把备份恢复到临时库并完成健康检查。",
        },
    )
    assert temp_restore_res.status_code == 201
    preflight_res = client.post(
        f"/api/tenants/{tenant['id']}/local-backups/postgres-formal-restore-preflight",
        headers=headers,
        json={
            "backup_record_id": backup["id"],
            "confirmation_payload": _postgres_formal_restore_preflight_confirmation(backup_sha256="8" * 64),
            "reason": "客户管理员登记正式恢复前置确认。",
        },
    )
    assert preflight_res.status_code == 201
    execution_dry_run_res = client.post(
        f"/api/tenants/{tenant['id']}/local-backups/postgres-formal-restore-execution-dry-run",
        headers=headers,
        json={
            "backup_record_id": backup["id"],
            "manifest_payload": _postgres_formal_restore_execution_dry_run_manifest(),
            "reason": "客户管理员登记正式恢复执行 dry-run 证据。",
        },
    )
    assert execution_dry_run_res.status_code == 201

    runbook_res = client.post(
        f"/api/tenants/{tenant['id']}/local-backups/postgres-formal-restore-runbook",
        headers=headers,
        json={
            "backup_record_id": backup["id"],
            "runbook_payload": _postgres_formal_restore_runbook(),
            "reason": "客户管理员登记正式恢复 SOP 与停机编排门禁。",
        },
    )

    assert runbook_res.status_code == 201
    updated = runbook_res.json()
    runbook = updated["manifest_payload"]["last_formal_restore_runbook"]
    assert runbook["schema_version"] == "p3-06u-26h2w-nc15.formal_restore_runbook_record.v1"
    assert runbook["formal_restore_runbook_ready"] is True
    assert runbook["manual_execution_only"] is True
    assert runbook["can_execute_restore_now"] is False
    assert runbook["can_execute_restore_in_app"] is False
    assert runbook["restore_execution_performed"] is False
    assert runbook["restore_command_preview_hashes"] == ["2" * 64, "3" * 64, "4" * 64]
    assert runbook["restore_command_preview_stored"] is False
    assert runbook["raw_restore_command_stored"] is False
    assert runbook["runbook_requirements"]["maintenance_window_locked"] is True
    assert runbook["runbook_requirements"]["post_restore_health_checks_documented"] is True
    assert runbook["execution_safety"]["pg_restore_executed_on_live_database"] is False
    assert runbook["execution_safety"]["runbook_sensitive_material_stored"] is False
    stored_runbook = updated["manifest_payload"]["postgres_formal_restore_runbook_payload"]
    assert stored_runbook["restore_command_preview_stored"] is False
    assert stored_runbook["raw_restore_command_stored"] is False
    assert stored_runbook["runbook_sensitive_material_stored"] is False

    events = list(db_session.scalars(select(AuditEvent).order_by(AuditEvent.id)).all())
    assert "local_backup.postgres_formal_restore_runbook_registered" in [event.action for event in events]
    audit_payload = json.loads(events[-1].payload)
    assert audit_payload["formal_restore_runbook_ready"] is True
    assert audit_payload["manual_execution_only"] is True
    assert audit_payload["can_execute_restore_now"] is False
    assert audit_payload["restore_execution_performed"] is False
    assert audit_payload["raw_restore_command_stored"] is False
    assert audit_payload["pg_restore_executed_on_live_database"] is False


def test_postgres_formal_restore_runbook_requires_execution_dry_run_and_rejects_live_flags(client) -> None:
    tenant = _create_tenant(client, "PG 正式恢复 SOP 风险客户", "postgres-formal-runbook-risk")
    _owner_role, _owner, token = _bootstrap_owner(client, tenant, "pg-formal-runbook-risk-owner@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    register_res = client.post(
        f"/api/tenants/{tenant['id']}/local-backups/postgres-dry-run-manifests",
        headers=headers,
        json={"manifest_payload": _postgres_dry_run_manifest(backup_sha256="7" * 64)},
    )
    assert register_res.status_code == 201
    backup = register_res.json()

    missing_execution_dry_run_res = client.post(
        f"/api/tenants/{tenant['id']}/local-backups/postgres-formal-restore-runbook",
        headers=headers,
        json={
            "backup_record_id": backup["id"],
            "runbook_payload": _postgres_formal_restore_runbook(backup_sha256="7" * 64),
        },
    )
    assert missing_execution_dry_run_res.status_code == 409
    assert "last_formal_restore_execution_dry_run is required" in missing_execution_dry_run_res.json()["detail"]

    plan_res = client.post(
        f"/api/local-backups/{backup['id']}/postgres-restore-rehearsal-plan",
        headers=headers,
        json={"reason": "客户管理员生成 PostgreSQL 恢复演练计划。"},
    )
    assert plan_res.status_code == 200
    temp_restore_res = client.post(
        f"/api/tenants/{tenant['id']}/local-backups/postgres-temp-restore-manifests",
        headers=headers,
        json={
            "backup_record_id": backup["id"],
            "manifest_payload": _postgres_temp_restore_manifest(backup_sha256="7" * 64),
        },
    )
    assert temp_restore_res.status_code == 201
    preflight_res = client.post(
        f"/api/tenants/{tenant['id']}/local-backups/postgres-formal-restore-preflight",
        headers=headers,
        json={
            "backup_record_id": backup["id"],
            "confirmation_payload": _postgres_formal_restore_preflight_confirmation(backup_sha256="7" * 64),
        },
    )
    assert preflight_res.status_code == 201
    execution_dry_run_res = client.post(
        f"/api/tenants/{tenant['id']}/local-backups/postgres-formal-restore-execution-dry-run",
        headers=headers,
        json={
            "backup_record_id": backup["id"],
            "manifest_payload": _postgres_formal_restore_execution_dry_run_manifest(backup_sha256="7" * 64),
        },
    )
    assert execution_dry_run_res.status_code == 201

    live_flag_res = client.post(
        f"/api/tenants/{tenant['id']}/local-backups/postgres-formal-restore-runbook",
        headers=headers,
        json={
            "backup_record_id": backup["id"],
            "runbook_payload": _postgres_formal_restore_runbook(
                backup_sha256="7" * 64,
                pg_restore_executed_on_live_database=True,
            ),
        },
    )
    assert live_flag_res.status_code == 409
    assert "pg_restore_executed_on_live_database must be false" in live_flag_res.json()["detail"]


def test_owner_can_create_postgres_restore_rehearsal_plan_without_running_restore(client, db_session) -> None:
    tenant = _create_tenant(client, "PG 恢复客户", "postgres-restore-plan")
    _owner_role, _owner, token = _bootstrap_owner(client, tenant, "pg-restore-plan-owner@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    register_res = client.post(
        f"/api/tenants/{tenant['id']}/local-backups/postgres-dry-run-manifests",
        headers=headers,
        json={
            "manifest_payload": _postgres_dry_run_manifest(backup_sha256="b" * 64),
            "reason": "客户本机登记 PostgreSQL 备份可读性证据。",
        },
    )
    assert register_res.status_code == 201
    backup = register_res.json()

    plan_res = client.post(
        f"/api/local-backups/{backup['id']}/postgres-restore-rehearsal-plan",
        headers=headers,
        json={"reason": "客户管理员生成 PostgreSQL 恢复演练计划。"},
    )

    assert plan_res.status_code == 200
    updated = plan_res.json()
    plan = updated["manifest_payload"]["last_restore_rehearsal_plan"]
    assert plan["schema_version"] == "p3-06u-26h2w-nc11.postgres_restore_rehearsal_plan.v1"
    assert plan["backup_id"] == backup["backup_id"]
    assert plan["dry_run"] is True
    assert plan["can_restore_now"] is False
    assert plan["rehearsal_ready"] is True
    assert plan["restore_mode"] == "pg_restore_manual_rehearsal_plan_only"
    assert plan["commands_executed"] == []
    assert plan["backup_verification"]["backup_file_body_stored"] is False
    assert plan["safety"]["live_restore_performed"] is False
    assert plan["safety"]["database_replaced"] is False
    assert plan["safety"]["program_files_replaced"] is False
    assert plan["safety"]["requires_fresh_pre_restore_backup"] is True
    assert plan["safety"]["requires_temporary_restore_first"] is True
    assert any(step["step"] == "restore_to_temporary_database_first" for step in plan["rehearsal_plan"])
    assert updated["manifest_payload"]["postgres_restore_rehearsal_plan"]["restore_rehearsal_plan_id"] == plan[
        "restore_rehearsal_plan_id"
    ]

    events = list(db_session.scalars(select(AuditEvent).order_by(AuditEvent.id)).all())
    assert "local_backup.postgres_restore_rehearsal_plan_created" in [event.action for event in events]
    audit_payload = json.loads(events[-1].payload)
    assert audit_payload["commands_executed"] == []
    assert audit_payload["live_restore_performed"] is False
    assert audit_payload["database_replaced"] is False


def test_postgres_restore_rehearsal_plan_rejects_tampered_manifest(client, db_session) -> None:
    tenant = _create_tenant(client, "PG 恢复风险客户", "postgres-restore-plan-risk")
    _owner_role, _owner, token = _bootstrap_owner(client, tenant, "pg-restore-risk-owner@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    register_res = client.post(
        f"/api/tenants/{tenant['id']}/local-backups/postgres-dry-run-manifests",
        headers=headers,
        json={"manifest_payload": _postgres_dry_run_manifest(backup_sha256="c" * 64)},
    )
    assert register_res.status_code == 201
    backup = register_res.json()

    record = db_session.get(LocalBackupRecord, backup["id"])
    assert record is not None
    manifest = dict(record.manifest_payload)
    pg_manifest = dict(manifest["postgres_backup_dry_run_manifest"])
    pg_manifest["database_replaced"] = True
    manifest["postgres_backup_dry_run_manifest"] = pg_manifest
    record.manifest_payload = manifest
    db_session.commit()

    plan_res = client.post(
        f"/api/local-backups/{backup['id']}/postgres-restore-rehearsal-plan",
        headers=headers,
        json={"reason": "被篡改 manifest 不应生成恢复计划。"},
    )

    assert plan_res.status_code == 409
    assert "database_replaced must be false" in plan_res.json()["detail"]


def test_postgres_backup_manifest_rejects_restore_or_secret_fields(client) -> None:
    tenant = _create_tenant(client, "PG 风险客户", "postgres-backup-risk")
    _owner_role, _owner, token = _bootstrap_owner(client, tenant, "pg-risk-owner@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    restored_res = client.post(
        f"/api/tenants/{tenant['id']}/local-backups/postgres-dry-run-manifests",
        headers=headers,
        json={"manifest_payload": _postgres_dry_run_manifest(live_restore_performed=True)},
    )
    assert restored_res.status_code == 409
    assert "live_restore_performed must be false" in restored_res.json()["detail"]

    secret_res = client.post(
        f"/api/tenants/{tenant['id']}/local-backups/postgres-dry-run-manifests",
        headers=headers,
        json={"manifest_payload": _postgres_dry_run_manifest(database_password="should-not-be-here")},
    )
    assert secret_res.status_code == 409
    assert "sensitive key" in secret_res.json()["detail"]


def test_owner_can_create_restore_dry_run_without_replacing_database(file_sqlite_client) -> None:
    client, db_session, backup_dir = file_sqlite_client
    tenant = _create_tenant(client, "恢复客户", "local-restore-dry-run")
    _owner_role, _owner, token = _bootstrap_owner(client, tenant, "restore-owner@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    create_res = client.post(
        f"/api/tenants/{tenant['id']}/local-backups",
        headers=headers,
        json={"reason": "恢复演练前创建备份点。"},
    )
    assert create_res.status_code == 201
    backup = create_res.json()

    dry_run_res = client.post(
        f"/api/local-backups/{backup['id']}/restore-dry-run",
        headers=headers,
        json={"reason": "客户管理员执行本地恢复工具演练。"},
    )

    assert dry_run_res.status_code == 200
    plan = dry_run_res.json()
    assert plan["schema_version"] == "p3-06u-26h2l.restore_dry_run.v1"
    assert plan["backup_id"] == backup["backup_id"]
    assert plan["dry_run"] is True
    assert plan["can_restore_now"] is False
    assert plan["rehearsal_ready"] is True
    assert plan["restore_mode"] == "offline_operator_required"
    assert plan["backup_verification"]["sha256_match"] is True
    assert plan["backup_verification"]["integrity_check"] == "ok"
    assert plan["current_database"]["absolute_path_exposed"] is False
    serialized_plan = json.dumps(plan)
    assert str(backup_dir) not in serialized_plan
    assert "/pytest-" not in serialized_plan
    assert "wanfa-local-test.sqlite3" in serialized_plan
    assert plan["safety"]["live_restore_performed"] is False
    assert plan["safety"]["database_file_replaced"] is False
    assert plan["safety"]["service_stopped"] is False
    assert plan["safety"]["requires_fresh_pre_restore_backup"] is True
    assert any(step["step"] == "replace_database_file_offline" and step["performed"] is False for step in plan["rehearsal_plan"])

    events = list(db_session.scalars(select(AuditEvent).order_by(AuditEvent.id)).all())
    assert "local_backup.restore_dry_run_created" in [event.action for event in events]
    dry_run_audit = next(event for event in events if event.action == "local_backup.restore_dry_run_created")
    audit_payload = json.loads(dry_run_audit.payload)
    assert audit_payload["can_restore_now"] is False
    assert audit_payload["live_restore_performed"] is False
    assert audit_payload["database_file_replaced"] is False


def test_in_memory_sqlite_backup_is_blocked(client) -> None:
    tenant = _create_tenant(client, "内存库客户", "local-backup-memory-blocked")
    _owner_role, _owner, token = _bootstrap_owner(client, tenant, "memory-backup-owner@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    res = client.post(
        f"/api/tenants/{tenant['id']}/local-backups",
        headers=headers,
        json={"reason": "内存库不应该生成假备份。"},
    )

    assert res.status_code == 409
    assert "in-memory SQLite database cannot create a durable physical backup" in res.json()["detail"]


def test_agent_cannot_manage_local_backups(file_sqlite_client) -> None:
    client, _db_session, _backup_dir = file_sqlite_client
    tenant = _create_tenant(client, "权限客户", "local-backup-agent-blocked")
    _owner_role, _owner, owner_token = _bootstrap_owner(client, tenant, "backup-owner@example.com")
    owner_headers = {"Authorization": f"Bearer {owner_token}"}
    agent_role = client.post(
        f"/api/tenants/{tenant['id']}/roles",
        headers=owner_headers,
        json={"code": "agent", "name": "客服坐席"},
    ).json()
    agent = client.post(
        f"/api/tenants/{tenant['id']}/users",
        headers=owner_headers,
        json={"name": "客服坐席", "email": "backup-agent@example.com", "password": "ChangeMe123!"},
    ).json()
    client.post(f"/api/users/{agent['id']}/roles", headers=owner_headers, json={"role_id": agent_role["id"]})
    login = client.post(
        "/api/auth/login",
        json={
            "tenant_slug": tenant["slug"],
            "email": "backup-agent@example.com",
            "password": "ChangeMe123!",
        },
    )
    agent_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    res = client.post(
        f"/api/tenants/{tenant['id']}/local-backups",
        headers=agent_headers,
        json={"reason": "普通客服不应创建备份。"},
    )

    assert res.status_code == 403

    create_res = client.post(
        f"/api/tenants/{tenant['id']}/local-backups",
        headers=owner_headers,
        json={"reason": "负责人创建备份供权限测试。"},
    )
    assert create_res.status_code == 201
    backup = create_res.json()

    dry_run_res = client.post(
        f"/api/local-backups/{backup['id']}/restore-dry-run",
        headers=agent_headers,
        json={"reason": "普通客服不应生成恢复演练。"},
    )

    assert dry_run_res.status_code == 403
