from __future__ import annotations

from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import sqlite3
from typing import Any
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.audit import add_audit_event
from app.core.config import get_settings
from app.models import LocalBackupRecord, Tenant, utc_now

BACKUP_SCHEMA_VERSION = "p3-06u-26h2h.local_backup.v1"
RESTORE_DRY_RUN_SCHEMA_VERSION = "p3-06u-26h2l.restore_dry_run.v1"
POSTGRES_BACKUP_DRY_RUN_SCHEMA_VERSION = "p3-06u-26h2w-nc8.postgres_backup_dry_run.v1"
POSTGRES_BACKUP_REGISTRATION_SCHEMA_VERSION = "p3-06u-26h2w-nc10.postgres_backup_manifest_record.v1"
POSTGRES_RESTORE_DRY_RUN_SCHEMA_VERSION = "p3-06u-26h2w-nc10.postgres_restore_readability_dry_run_record.v1"
POSTGRES_RESTORE_REHEARSAL_PLAN_SCHEMA_VERSION = "p3-06u-26h2w-nc11.postgres_restore_rehearsal_plan.v1"
POSTGRES_TEMP_RESTORE_REHEARSAL_SCHEMA_VERSION = (
    "p3-06u-26h2w-nc12.postgres_temp_restore_rehearsal.v1"
)
POSTGRES_TEMP_RESTORE_REGISTRATION_SCHEMA_VERSION = (
    "p3-06u-26h2w-nc12.postgres_temp_restore_manifest_record.v1"
)
POSTGRES_FORMAL_RESTORE_PREFLIGHT_SCHEMA_VERSION = (
    "p3-06u-26h2w-nc13.formal_restore_preflight_approval.v1"
)
POSTGRES_FORMAL_RESTORE_PREFLIGHT_REGISTRATION_SCHEMA_VERSION = (
    "p3-06u-26h2w-nc13.formal_restore_preflight_approval_record.v1"
)
POSTGRES_FORMAL_RESTORE_EXECUTION_DRY_RUN_SCHEMA_VERSION = (
    "p3-06u-26h2w-nc14.formal_restore_execution_dry_run.v1"
)
POSTGRES_FORMAL_RESTORE_EXECUTION_DRY_RUN_REGISTRATION_SCHEMA_VERSION = (
    "p3-06u-26h2w-nc14.formal_restore_execution_dry_run_record.v1"
)
POSTGRES_FORMAL_RESTORE_RUNBOOK_SCHEMA_VERSION = "p3-06u-26h2w-nc15.formal_restore_runbook.v1"
POSTGRES_FORMAL_RESTORE_RUNBOOK_REGISTRATION_SCHEMA_VERSION = (
    "p3-06u-26h2w-nc15.formal_restore_runbook_record.v1"
)

_SENSITIVE_KEY_RE = re.compile(r"(?i)(api[_-]?key|access[_-]?token|refresh[_-]?token|secret|password|encodingaeskey)")
_TEMP_RESTORE_DB_RE = re.compile(r"^wanfa_restore_tmp_[a-z0-9_]{8,64}$")
_FORBIDDEN_TEMP_DB_PARTS = ("prod", "production", "live", "current", "customer", "main", "wanfa_ops")
_FORMAL_RESTORE_APPROVER_ROLE_CODES = {"owner", "admin", "customer_admin", "customer_owner"}


class LocalBackupNotFound(Exception):
    pass


class LocalBackupUnsupported(Exception):
    pass


def create_local_database_backup(
    db: Session,
    *,
    tenant: Tenant,
    actor_id: int,
    reason: str,
) -> dict[str, Any]:
    source_path = _require_sqlite_file_database(db)
    backup_dir = _local_backup_dir()
    backup_dir.mkdir(parents=True, exist_ok=True)
    created_at = utc_now()
    backup_id = f"local-db-{tenant.slug}-{created_at.strftime('%Y%m%d%H%M%S')}-{uuid4().hex[:8]}"
    backup_file_name = f"{backup_id}.sqlite3"
    backup_path = backup_dir / backup_file_name

    _copy_sqlite_database(source_path, backup_path)
    digest = _sha256_file(backup_path)
    size_bytes = backup_path.stat().st_size
    manifest = _build_manifest(
        tenant=tenant,
        backup_id=backup_id,
        backup_file_name=backup_file_name,
        source_path=source_path,
        created_at=created_at,
        reason=reason,
        file_size_bytes=size_bytes,
        sha256=digest,
    )
    manifest_path = backup_path.with_suffix(".manifest.json")
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

    record = LocalBackupRecord(
        tenant_id=tenant.id,
        backup_id=backup_id,
        backup_type="sqlite_database",
        status="created",
        file_name=backup_file_name,
        file_path=str(backup_path),
        file_size_bytes=size_bytes,
        sha256=digest,
        source_database_label=source_path.name,
        source_database_hash=_hash_text(str(source_path.resolve())),
        restore_mode="manual_rehearsal_only",
        manifest_payload=manifest,
        created_by_id=actor_id,
        created_at=created_at,
    )
    db.add(record)
    db.flush()
    add_audit_event(
        db,
        tenant_id=tenant.id,
        action="local_backup.created",
        resource_type="local_backup",
        actor_id=actor_id,
        resource_id=backup_id,
        payload={
            "backup_type": record.backup_type,
            "file_name": record.file_name,
            "file_size_bytes": record.file_size_bytes,
            "sha256": record.sha256,
            "restore_mode": record.restore_mode,
            "external_upload_performed": False,
            "external_write_performed": False,
        },
    )
    db.commit()
    db.refresh(record)
    return _record_payload(record)


def list_local_database_backups(db: Session, *, tenant: Tenant) -> list[dict[str, Any]]:
    query = (
        select(LocalBackupRecord)
        .where(LocalBackupRecord.tenant_id == tenant.id)
        .order_by(LocalBackupRecord.created_at.desc(), LocalBackupRecord.id.desc())
    )
    return [_record_payload(record) for record in db.scalars(query).all()]


def register_postgres_backup_dry_run_manifest(
    db: Session,
    *,
    tenant: Tenant,
    actor_id: int,
    manifest_payload: dict[str, Any],
    reason: str,
) -> dict[str, Any]:
    normalized = _validate_postgres_backup_manifest(manifest_payload)
    now = utc_now()
    created_label = str(normalized.get("created_at") or now.strftime("%Y%m%d%H%M%S"))
    safe_created_label = "".join(char for char in created_label if char.isalnum())[:24] or now.strftime("%Y%m%d%H%M%S")
    backup_sha256 = str(normalized["backup_sha256"])
    backup_id = f"pg-dry-run-{tenant.slug}-{safe_created_label}-{backup_sha256[:8]}"

    existing = db.scalar(
        select(LocalBackupRecord).where(
            LocalBackupRecord.tenant_id == tenant.id,
            LocalBackupRecord.backup_id == backup_id,
        )
    )
    if existing is not None:
        return _record_payload(existing)

    restore_dry_run = _postgres_restore_dry_run_payload(
        backup_id=backup_id,
        tenant=tenant,
        manifest=normalized,
        generated_at=now,
        reason=reason,
    )
    registration = {
        "schema_version": POSTGRES_BACKUP_REGISTRATION_SCHEMA_VERSION,
        "registered_at": now.isoformat(),
        "reason": reason,
        "source": "customer_local_postgres_backup_dry_run_manifest",
        "backup_file_body_stored": False,
        "restore_list_body_stored": False,
        "absolute_path_stored": False,
        "external_upload_performed": False,
    }
    record_manifest = {
        "schema_version": POSTGRES_BACKUP_REGISTRATION_SCHEMA_VERSION,
        "registration": registration,
        "postgres_backup_dry_run_manifest": normalized,
        "last_restore_dry_run": restore_dry_run,
        "safety": {
            **_safety_payload(),
            "backup_file_body_stored": False,
            "restore_list_body_stored": False,
            "live_restore_performed": False,
            "database_file_replaced": False,
        },
    }
    record = LocalBackupRecord(
        tenant_id=tenant.id,
        backup_id=backup_id,
        backup_type="postgres_pg_dump_custom",
        status="verified",
        file_name=str(normalized.get("backup_file") or "postgres.dump"),
        file_path="external_manifest_only",
        file_size_bytes=int(normalized["backup_size_bytes"]),
        sha256=backup_sha256,
        source_database_label="customer-local-postgresql",
        source_database_hash=_hash_text(f"{backup_sha256}:{normalized.get('created_at', '')}:{tenant.slug}"),
        restore_mode="pg_restore_list_rehearsal_only",
        manifest_payload=record_manifest,
        created_by_id=actor_id,
        created_at=now,
        verified_at=now,
    )
    db.add(record)
    db.flush()
    add_audit_event(
        db,
        tenant_id=tenant.id,
        action="local_backup.postgres_dry_run_manifest_registered",
        resource_type="local_backup",
        actor_id=actor_id,
        resource_id=backup_id,
        payload={
            "backup_type": record.backup_type,
            "file_name": record.file_name,
            "file_size_bytes": record.file_size_bytes,
            "sha256": record.sha256,
            "restore_mode": record.restore_mode,
            "pg_dump_completed": normalized.get("pg_dump_completed") is True,
            "pg_restore_list_completed": normalized.get("pg_restore_list_completed") is True,
            "backup_file_body_stored": False,
            "external_upload_performed": False,
            "live_restore_performed": False,
            "database_file_replaced": False,
        },
    )
    db.commit()
    db.refresh(record)
    return _record_payload(record)


def verify_local_database_backup(
    db: Session,
    *,
    backup_record_id: int,
    tenant: Tenant,
    actor_id: int,
    reason: str,
) -> dict[str, Any]:
    record = db.get(LocalBackupRecord, backup_record_id)
    if record is None or record.tenant_id != tenant.id:
        raise LocalBackupNotFound("local backup not found")

    backup_path = Path(record.file_path)
    verification = _verify_backup_file(backup_path, expected_sha256=record.sha256)
    now = utc_now()
    manifest = dict(record.manifest_payload or {})
    manifest["last_verification"] = {
        "verified_at": now.isoformat(),
        "reason": reason,
        **verification,
    }
    record.manifest_payload = manifest
    if verification["ok"]:
        record.status = "verified"
        record.verified_at = now
        record.error_message = ""
    else:
        record.status = "verification_failed"
        record.error_message = verification["message"]
    add_audit_event(
        db,
        tenant_id=tenant.id,
        action="local_backup.verified" if verification["ok"] else "local_backup.verification_failed",
        resource_type="local_backup",
        actor_id=actor_id,
        resource_id=record.backup_id,
        payload={
            "backup_id": record.backup_id,
            "status": record.status,
            "integrity_check": verification.get("integrity_check", ""),
            "sha256_match": verification.get("sha256_match", False),
            "restore_mode": record.restore_mode,
        },
    )
    db.commit()
    db.refresh(record)
    return _record_payload(record)


def create_local_database_restore_dry_run(
    db: Session,
    *,
    backup_record_id: int,
    tenant: Tenant,
    actor_id: int,
    reason: str,
) -> dict[str, Any]:
    record = db.get(LocalBackupRecord, backup_record_id)
    if record is None or record.tenant_id != tenant.id:
        raise LocalBackupNotFound("local backup not found")
    if record.backup_type != "sqlite_database":
        raise LocalBackupUnsupported("only SQLite database backups can be rehearsed in this stage")

    source_path = _require_sqlite_file_database(db)
    generated_at = utc_now()
    backup_verification = _verify_backup_file(Path(record.file_path), expected_sha256=record.sha256)
    blockers = []
    if not backup_verification["ok"]:
        blockers.append(backup_verification["message"])
    if record.restore_mode != "manual_rehearsal_only":
        blockers.append(f"unsupported restore mode: {record.restore_mode}")

    rehearsal_ready = len(blockers) == 0
    restore_dry_run_id = f"restore-dry-run-{record.backup_id}-{generated_at.strftime('%Y%m%d%H%M%S')}-{uuid4().hex[:8]}"
    plan = {
        "schema_version": RESTORE_DRY_RUN_SCHEMA_VERSION,
        "restore_dry_run_id": restore_dry_run_id,
        "backup_id": record.backup_id,
        "tenant_id": tenant.id,
        "generated_at": generated_at.isoformat(),
        "dry_run": True,
        "can_restore_now": False,
        "rehearsal_ready": rehearsal_ready,
        "restore_mode": "offline_operator_required",
        "backup_verification": backup_verification,
        "current_database": {
            "dialect": "sqlite",
            "database_label": source_path.name,
            "database_path_hash": _hash_text(str(source_path.resolve())),
            "current_file_exists": source_path.exists(),
            "absolute_path_exposed": False,
        },
        "rehearsal_plan": _restore_rehearsal_steps(),
        "health_checks": _restore_health_checks(backup_verification=backup_verification, rehearsal_ready=rehearsal_ready),
        "blockers": blockers,
        "safety": {
            **_safety_payload(),
            "dry_run": True,
            "can_restore_now": False,
            "rehearsal_ready": rehearsal_ready,
            "service_stopped": False,
            "database_file_replaced": False,
            "database_migration_performed": False,
            "requires_fresh_pre_restore_backup": True,
            "requires_operator_confirmation": True,
            "requires_service_stop_window": True,
        },
        "warnings": [
            "本接口只生成恢复演练计划，不覆盖正在运行的本地数据库。",
            "真实恢复必须由后续独立本机恢复工具在停服务窗口执行。",
            "真实恢复前必须先对当前数据库再创建一个新的物理备份点。",
        ],
        "reason": reason,
    }

    manifest = dict(record.manifest_payload or {})
    manifest["last_restore_dry_run"] = plan
    record.manifest_payload = manifest
    add_audit_event(
        db,
        tenant_id=tenant.id,
        action="local_backup.restore_dry_run_created",
        resource_type="local_backup",
        actor_id=actor_id,
        resource_id=record.backup_id,
        payload={
            "backup_id": record.backup_id,
            "restore_dry_run_id": restore_dry_run_id,
            "rehearsal_ready": rehearsal_ready,
            "can_restore_now": False,
            "live_restore_performed": False,
            "database_file_replaced": False,
            "blockers": blockers,
        },
    )
    db.commit()
    return plan


def create_postgres_restore_rehearsal_plan(
    db: Session,
    *,
    backup_record_id: int,
    tenant: Tenant,
    actor_id: int,
    reason: str,
) -> dict[str, Any]:
    record = db.get(LocalBackupRecord, backup_record_id)
    if record is None or record.tenant_id != tenant.id:
        raise LocalBackupNotFound("local backup not found")

    normalized_manifest, blockers = _validate_postgres_restore_rehearsal_source(record)
    if blockers:
        raise LocalBackupUnsupported("PostgreSQL restore rehearsal plan is blocked: " + "; ".join(blockers))

    generated_at = utc_now()
    plan = _postgres_restore_rehearsal_plan_payload(
        backup_record=record,
        tenant=tenant,
        manifest=normalized_manifest,
        generated_at=generated_at,
        reason=reason,
    )
    manifest_payload = dict(record.manifest_payload or {})
    manifest_payload["last_restore_rehearsal_plan"] = plan
    manifest_payload["postgres_restore_rehearsal_plan"] = plan
    record.manifest_payload = manifest_payload
    add_audit_event(
        db,
        tenant_id=tenant.id,
        action="local_backup.postgres_restore_rehearsal_plan_created",
        resource_type="local_backup",
        actor_id=actor_id,
        resource_id=record.backup_id,
        payload={
            "backup_id": record.backup_id,
            "restore_rehearsal_plan_id": plan["restore_rehearsal_plan_id"],
            "rehearsal_ready": plan["rehearsal_ready"],
            "can_restore_now": False,
            "commands_executed": [],
            "live_restore_performed": False,
            "database_replaced": False,
            "program_files_replaced": False,
            "requires_fresh_pre_restore_backup": True,
            "requires_customer_admin_confirmation": True,
        },
    )
    db.commit()
    db.refresh(record)
    return _record_payload(record)


def register_postgres_temp_restore_rehearsal_manifest(
    db: Session,
    *,
    tenant: Tenant,
    actor_id: int,
    backup_record_id: int,
    manifest_payload: dict[str, Any],
    reason: str,
) -> dict[str, Any]:
    record = db.get(LocalBackupRecord, backup_record_id)
    if record is None or record.tenant_id != tenant.id:
        raise LocalBackupNotFound("local backup not found")

    normalized_manifest = _validate_postgres_temp_restore_rehearsal_manifest(
        manifest_payload,
        backup_record=record,
    )
    generated_at = utc_now()
    rehearsal = _postgres_temp_restore_rehearsal_record_payload(
        backup_record=record,
        tenant=tenant,
        manifest=normalized_manifest,
        generated_at=generated_at,
        reason=reason,
    )
    manifest = dict(record.manifest_payload or {})
    manifest["postgres_temp_restore_rehearsal_manifest"] = normalized_manifest
    manifest["postgres_temp_restore_rehearsal_registration"] = {
        "schema_version": POSTGRES_TEMP_RESTORE_REGISTRATION_SCHEMA_VERSION,
        "registered_at": generated_at.isoformat(),
        "reason": reason,
        "source": "customer_local_postgres_temp_restore_rehearsal_manifest",
        "backup_file_body_stored": False,
        "temp_database_name_stored": False,
        "live_restore_performed": False,
        "database_replaced": False,
        "external_write_performed": False,
    }
    manifest["last_temp_restore_rehearsal"] = rehearsal
    record.manifest_payload = manifest
    add_audit_event(
        db,
        tenant_id=tenant.id,
        action="local_backup.postgres_temp_restore_manifest_registered",
        resource_type="local_backup",
        actor_id=actor_id,
        resource_id=record.backup_id,
        payload={
            "backup_id": record.backup_id,
            "temp_restore_rehearsal_id": rehearsal["temp_restore_rehearsal_id"],
            "backup_sha256": record.sha256,
            "rehearsal_ready": True,
            "can_restore_now": False,
            "restore_mode": "pg_restore_to_temporary_database_only",
            "temp_database_created": True,
            "temp_database_dropped": True,
            "live_restore_performed": False,
            "database_replaced": False,
            "program_files_replaced": False,
            "external_write_enabled": False,
            "trusted_inbound_worker_enabled": False,
        },
    )
    db.commit()
    db.refresh(record)
    return _record_payload(record)


def register_postgres_formal_restore_preflight_approval(
    db: Session,
    *,
    tenant: Tenant,
    actor_id: int,
    backup_record_id: int,
    confirmation_payload: dict[str, Any],
    reason: str,
) -> dict[str, Any]:
    record = db.get(LocalBackupRecord, backup_record_id)
    if record is None or record.tenant_id != tenant.id:
        raise LocalBackupNotFound("local backup not found")

    normalized_confirmation = _validate_postgres_formal_restore_preflight_confirmation(
        confirmation_payload,
        backup_record=record,
    )
    generated_at = utc_now()
    preflight = _postgres_formal_restore_preflight_record_payload(
        backup_record=record,
        tenant=tenant,
        confirmation=normalized_confirmation,
        generated_at=generated_at,
        reason=reason,
    )
    manifest = dict(record.manifest_payload or {})
    manifest["postgres_formal_restore_preflight_confirmation"] = normalized_confirmation
    manifest["postgres_formal_restore_preflight_registration"] = {
        "schema_version": POSTGRES_FORMAL_RESTORE_PREFLIGHT_REGISTRATION_SCHEMA_VERSION,
        "registered_at": generated_at.isoformat(),
        "reason": reason,
        "source": "customer_admin_formal_restore_preflight_confirmation",
        "backup_file_body_stored": False,
        "customer_signature_body_stored": False,
        "live_restore_performed": False,
        "database_replaced": False,
        "external_write_performed": False,
    }
    manifest["last_formal_restore_preflight"] = preflight
    record.manifest_payload = manifest
    add_audit_event(
        db,
        tenant_id=tenant.id,
        action="local_backup.postgres_formal_restore_preflight_registered",
        resource_type="local_backup",
        actor_id=actor_id,
        resource_id=record.backup_id,
        payload={
            "backup_id": record.backup_id,
            "formal_restore_preflight_id": preflight["formal_restore_preflight_id"],
            "backup_sha256": record.sha256,
            "formal_restore_sop_ready": True,
            "manual_restore_window_ready": True,
            "can_execute_restore_now": False,
            "can_execute_restore_in_app": False,
            "requires_final_operator_confirmation": True,
            "live_restore_performed": False,
            "database_replaced": False,
            "program_files_replaced": False,
            "external_write_enabled": False,
            "trusted_inbound_worker_enabled": False,
        },
    )
    db.commit()
    db.refresh(record)
    return _record_payload(record)


def register_postgres_formal_restore_execution_dry_run_manifest(
    db: Session,
    *,
    tenant: Tenant,
    actor_id: int,
    backup_record_id: int,
    manifest_payload: dict[str, Any],
    reason: str,
) -> dict[str, Any]:
    record = db.get(LocalBackupRecord, backup_record_id)
    if record is None or record.tenant_id != tenant.id:
        raise LocalBackupNotFound("local backup not found")

    normalized_manifest = _validate_postgres_formal_restore_execution_dry_run_manifest(
        manifest_payload,
        backup_record=record,
    )
    generated_at = utc_now()
    dry_run = _postgres_formal_restore_execution_dry_run_record_payload(
        backup_record=record,
        tenant=tenant,
        manifest=normalized_manifest,
        generated_at=generated_at,
        reason=reason,
    )
    manifest = dict(record.manifest_payload or {})
    manifest["postgres_formal_restore_execution_dry_run_manifest"] = normalized_manifest
    manifest["postgres_formal_restore_execution_dry_run_registration"] = {
        "schema_version": POSTGRES_FORMAL_RESTORE_EXECUTION_DRY_RUN_REGISTRATION_SCHEMA_VERSION,
        "registered_at": generated_at.isoformat(),
        "reason": reason,
        "source": "operator_formal_restore_execution_dry_run_manifest",
        "restore_command_preview_stored": False,
        "raw_restore_command_stored": False,
        "backup_file_body_stored": False,
        "live_restore_performed": False,
        "database_replaced": False,
        "external_write_performed": False,
    }
    manifest["last_formal_restore_execution_dry_run"] = dry_run
    record.manifest_payload = manifest
    add_audit_event(
        db,
        tenant_id=tenant.id,
        action="local_backup.postgres_formal_restore_execution_dry_run_registered",
        resource_type="local_backup",
        actor_id=actor_id,
        resource_id=record.backup_id,
        payload={
            "backup_id": record.backup_id,
            "formal_restore_execution_dry_run_id": dry_run["formal_restore_execution_dry_run_id"],
            "backup_sha256": record.sha256,
            "formal_restore_execution_dry_run_ready": True,
            "restore_command_preview_hash_count": len(normalized_manifest["restore_command_preview_hashes"]),
            "restore_commands_rendered_not_executed": True,
            "can_execute_restore_now": False,
            "can_execute_restore_in_app": False,
            "restore_execution_performed": False,
            "raw_restore_command_stored": False,
            "live_restore_performed": False,
            "database_replaced": False,
            "program_files_replaced": False,
            "external_write_enabled": False,
            "trusted_inbound_worker_enabled": False,
            "pg_restore_executed_on_live_database": False,
        },
    )
    db.commit()
    db.refresh(record)
    return _record_payload(record)


def register_postgres_formal_restore_runbook(
    db: Session,
    *,
    tenant: Tenant,
    actor_id: int,
    backup_record_id: int,
    runbook_payload: dict[str, Any],
    reason: str,
) -> dict[str, Any]:
    record = db.get(LocalBackupRecord, backup_record_id)
    if record is None or record.tenant_id != tenant.id:
        raise LocalBackupNotFound("local backup not found")

    normalized_runbook = _validate_postgres_formal_restore_runbook(
        runbook_payload,
        backup_record=record,
    )
    generated_at = utc_now()
    runbook = _postgres_formal_restore_runbook_record_payload(
        backup_record=record,
        tenant=tenant,
        runbook=normalized_runbook,
        generated_at=generated_at,
        reason=reason,
    )
    manifest = dict(record.manifest_payload or {})
    manifest["postgres_formal_restore_runbook_payload"] = normalized_runbook
    manifest["postgres_formal_restore_runbook_registration"] = {
        "schema_version": POSTGRES_FORMAL_RESTORE_RUNBOOK_REGISTRATION_SCHEMA_VERSION,
        "registered_at": generated_at.isoformat(),
        "reason": reason,
        "source": "operator_formal_restore_runbook",
        "manual_execution_only": True,
        "restore_command_preview_hashes_stored": True,
        "restore_command_preview_stored": False,
        "raw_restore_command_stored": False,
        "backup_file_body_stored": False,
        "live_restore_performed": False,
        "database_replaced": False,
        "external_write_performed": False,
    }
    manifest["last_formal_restore_runbook"] = runbook
    record.manifest_payload = manifest
    add_audit_event(
        db,
        tenant_id=tenant.id,
        action="local_backup.postgres_formal_restore_runbook_registered",
        resource_type="local_backup",
        actor_id=actor_id,
        resource_id=record.backup_id,
        payload={
            "backup_id": record.backup_id,
            "formal_restore_runbook_id": runbook["formal_restore_runbook_id"],
            "backup_sha256": record.sha256,
            "formal_restore_runbook_ready": True,
            "manual_execution_only": True,
            "restore_command_preview_hash_count": len(normalized_runbook["restore_command_preview_hashes"]),
            "can_execute_restore_now": False,
            "can_execute_restore_in_app": False,
            "restore_execution_performed": False,
            "raw_restore_command_stored": False,
            "live_restore_performed": False,
            "database_replaced": False,
            "program_files_replaced": False,
            "external_write_enabled": False,
            "trusted_inbound_worker_enabled": False,
            "pg_restore_executed_on_live_database": False,
        },
    )
    db.commit()
    db.refresh(record)
    return _record_payload(record)


def _require_sqlite_file_database(db: Session) -> Path:
    bind = db.get_bind()
    if bind.dialect.name != "sqlite":
        raise LocalBackupUnsupported("local SQLite file database is required for this backup rehearsal")
    database = bind.url.database
    if not database or database == ":memory:":
        raise LocalBackupUnsupported("in-memory SQLite database cannot create a durable physical backup")
    source_path = Path(database)
    if not source_path.is_absolute():
        source_path = Path.cwd() / source_path
    source_path = source_path.resolve()
    if not source_path.exists() or not source_path.is_file():
        raise LocalBackupUnsupported("SQLite database file was not found")
    return source_path


def _validate_postgres_backup_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(manifest, dict):
        raise LocalBackupUnsupported("PostgreSQL backup dry-run manifest must be a JSON object")
    blockers: list[str] = []
    if manifest.get("schema_version") != POSTGRES_BACKUP_DRY_RUN_SCHEMA_VERSION:
        blockers.append("schema_version mismatch")
    if manifest.get("status") != "postgres_backup_restore_readability_dry_run_ready":
        blockers.append("status must be postgres_backup_restore_readability_dry_run_ready")
    for key in ("pg_dump_completed", "pg_restore_list_completed"):
        if manifest.get(key) is not True:
            blockers.append(f"{key} must be true")
    for key in (
        "live_restore_performed",
        "database_replaced",
        "program_files_replaced",
        "external_write_enabled",
        "trusted_inbound_worker_enabled",
    ):
        if manifest.get(key) is not False:
            blockers.append(f"{key} must be false")
    backup_sha256 = str(manifest.get("backup_sha256") or "")
    if not re.fullmatch(r"[a-fA-F0-9]{64}", backup_sha256):
        blockers.append("backup_sha256 must be a 64-char sha256 hex digest")
    backup_size = _positive_int(manifest.get("backup_size_bytes"))
    if backup_size is None:
        blockers.append("backup_size_bytes must be positive")
    restore_list_size = _positive_int(manifest.get("restore_list_size_bytes"))
    if restore_list_size is None:
        blockers.append("restore_list_size_bytes must be positive")
    for key in ("backup_file", "restore_list_file"):
        value = str(manifest.get(key) or "")
        if not value:
            blockers.append(f"{key} is required")
        if "/" in value or "\\" in value or value in {".", ".."}:
            blockers.append(f"{key} must be a file name, not a path")
    if _contains_sensitive_key(manifest):
        blockers.append("manifest contains sensitive key names")
    if blockers:
        raise LocalBackupUnsupported("invalid PostgreSQL backup dry-run manifest: " + "; ".join(blockers))
    normalized = dict(manifest)
    normalized["backup_sha256"] = backup_sha256.lower()
    normalized["backup_size_bytes"] = int(backup_size or 0)
    normalized["restore_list_size_bytes"] = int(restore_list_size or 0)
    return normalized


def _postgres_restore_dry_run_payload(
    *,
    backup_id: str,
    tenant: Tenant,
    manifest: dict[str, Any],
    generated_at: datetime,
    reason: str,
) -> dict[str, Any]:
    return {
        "schema_version": POSTGRES_RESTORE_DRY_RUN_SCHEMA_VERSION,
        "restore_dry_run_id": f"pg-restore-list-{backup_id}",
        "backup_id": backup_id,
        "tenant_id": tenant.id,
        "generated_at": generated_at.isoformat(),
        "dry_run": True,
        "can_restore_now": False,
        "rehearsal_ready": True,
        "restore_mode": "pg_restore_list_rehearsal_only",
        "backup_verification": {
            "ok": True,
            "sha256_match": True,
            "integrity_check": "pg_restore_list_ok",
            "pg_dump_completed": manifest.get("pg_dump_completed") is True,
            "pg_restore_list_completed": manifest.get("pg_restore_list_completed") is True,
        },
        "current_database": {
            "dialect": "postgresql",
            "database_label": "customer-local-postgresql",
            "database_path_hash": "",
            "absolute_path_exposed": False,
        },
        "rehearsal_plan": [
            {
                "step": "read_pg_restore_list",
                "label": "读取 PostgreSQL 备份清单",
                "description": "已通过 pg_restore --list 校验备份文件可读；本系统只登记 manifest，不保存 dump 文件。",
                "performed": True,
                "required": True,
            },
            {
                "step": "manual_restore_window_required",
                "label": "真实恢复需维护窗口",
                "description": "真实恢复必须另开停机窗口、创建恢复前备份并由客户管理员确认。",
                "performed": False,
                "required": True,
            },
        ],
        "health_checks": [
            {"name": "pg_dump_completed", "status": "pass", "required": True},
            {"name": "pg_restore_list_completed", "status": "pass", "required": True},
            {"name": "live_restore_not_performed", "status": "pass", "required": True},
            {"name": "database_not_replaced", "status": "pass", "required": True},
        ],
        "blockers": [],
        "safety": {
            **_safety_payload(),
            "dry_run": True,
            "can_restore_now": False,
            "rehearsal_ready": True,
            "service_stopped": False,
            "database_file_replaced": False,
            "live_restore_performed": False,
            "requires_fresh_pre_restore_backup": True,
            "requires_operator_confirmation": True,
            "requires_service_stop_window": True,
            "backup_file_body_stored": False,
        },
        "warnings": [
            "当前只登记 PostgreSQL 备份可读性演练 manifest，不保存备份文件本体。",
            "真实恢复必须另开维护窗口，并由客户管理员确认。",
        ],
        "reason": reason,
    }


def _validate_postgres_restore_rehearsal_source(record: LocalBackupRecord) -> tuple[dict[str, Any], list[str]]:
    blockers: list[str] = []
    if record.backup_type != "postgres_pg_dump_custom":
        blockers.append("backup_type must be postgres_pg_dump_custom")
    if record.status != "verified":
        blockers.append("backup status must be verified")
    if record.restore_mode != "pg_restore_list_rehearsal_only":
        blockers.append("restore_mode must be pg_restore_list_rehearsal_only")
    if record.file_path != "external_manifest_only":
        blockers.append("PostgreSQL backup file body must not be stored by the service")

    manifest_payload = record.manifest_payload if isinstance(record.manifest_payload, dict) else {}
    pg_manifest = manifest_payload.get("postgres_backup_dry_run_manifest")
    if not isinstance(pg_manifest, dict):
        blockers.append("registered PostgreSQL dry-run manifest is missing")
        return {}, blockers

    try:
        normalized = _validate_postgres_backup_manifest(pg_manifest)
    except LocalBackupUnsupported as exc:
        blockers.append(str(exc))
        normalized = {}

    last_restore_dry_run = manifest_payload.get("last_restore_dry_run")
    if not isinstance(last_restore_dry_run, dict):
        blockers.append("last_restore_dry_run summary is missing")
    elif last_restore_dry_run.get("can_restore_now") is not False:
        blockers.append("last_restore_dry_run must keep can_restore_now=false")

    safety = manifest_payload.get("safety") if isinstance(manifest_payload.get("safety"), dict) else {}
    for key in (
        "live_restore_performed",
        "database_file_replaced",
        "backup_file_body_stored",
        "restore_list_body_stored",
    ):
        if safety.get(key) is not False:
            blockers.append(f"safety.{key} must be false")

    if _contains_sensitive_key(manifest_payload):
        blockers.append("manifest payload contains sensitive key names")
    return normalized, blockers


def _postgres_restore_rehearsal_plan_payload(
    *,
    backup_record: LocalBackupRecord,
    tenant: Tenant,
    manifest: dict[str, Any],
    generated_at: datetime,
    reason: str,
) -> dict[str, Any]:
    return {
        "schema_version": POSTGRES_RESTORE_REHEARSAL_PLAN_SCHEMA_VERSION,
        "restore_rehearsal_plan_id": (
            f"pg-restore-plan-{backup_record.backup_id}-{generated_at.strftime('%Y%m%d%H%M%S')}-{uuid4().hex[:8]}"
        ),
        "backup_id": backup_record.backup_id,
        "tenant_id": tenant.id,
        "generated_at": generated_at.isoformat(),
        "dry_run": True,
        "can_restore_now": False,
        "rehearsal_ready": True,
        "restore_mode": "pg_restore_manual_rehearsal_plan_only",
        "commands_executed": [],
        "backup_verification": {
            "ok": True,
            "sha256_match": True,
            "integrity_check": "pg_restore_list_ok",
            "backup_sha256": manifest.get("backup_sha256"),
            "backup_size_bytes": manifest.get("backup_size_bytes"),
            "pg_dump_completed": manifest.get("pg_dump_completed") is True,
            "pg_restore_list_completed": manifest.get("pg_restore_list_completed") is True,
            "backup_file_body_stored": False,
        },
        "rehearsal_plan": [
            {
                "step": "freeze_customer_window",
                "label": "确认客户维护窗口",
                "description": "真实恢复只能在客户明确授权的停机维护窗口内进行。",
                "performed": False,
                "required": True,
            },
            {
                "step": "create_fresh_pre_restore_backup",
                "label": "恢复前二次备份",
                "description": "恢复前必须先对当前数据库再创建一个新的备份点，用于失败回退。",
                "performed": False,
                "required": True,
            },
            {
                "step": "stop_application_services",
                "label": "停止本地服务",
                "description": "停止后端、前端壳层、后台任务和真实外发 worker，避免运行中写入。",
                "performed": False,
                "required": True,
            },
            {
                "step": "restore_to_temporary_database_first",
                "label": "先恢复到临时库",
                "description": "正式恢复前先恢复到临时 PostgreSQL 数据库，并运行健康检查。",
                "performed": False,
                "required": True,
            },
            {
                "step": "run_post_restore_health_checks",
                "label": "恢复后健康检查",
                "description": "检查登录、租户、账号、知识库、备份记录和关键 API 状态。",
                "performed": False,
                "required": True,
            },
            {
                "step": "customer_admin_confirmation",
                "label": "客户管理员确认",
                "description": "恢复结果必须由客户管理员确认后才允许进入下一步。",
                "performed": False,
                "required": True,
            },
            {
                "step": "rollback_if_health_failed",
                "label": "失败回退",
                "description": "如健康检查失败，使用恢复前二次备份回退。",
                "performed": False,
                "required": True,
            },
        ],
        "health_checks": [
            {"name": "pg_restore_list_completed", "status": "pass", "required": True},
            {"name": "live_restore_not_performed", "status": "pass", "required": True},
            {"name": "database_not_replaced", "status": "pass", "required": True},
            {"name": "temporary_database_restore", "status": "pending", "required": True},
            {"name": "post_restore_login_check", "status": "pending", "required": True},
            {"name": "customer_admin_confirmation", "status": "pending", "required": True},
        ],
        "blockers": [],
        "safety": {
            **_safety_payload(),
            "dry_run": True,
            "can_restore_now": False,
            "service_stopped": False,
            "database_replaced": False,
            "database_file_replaced": False,
            "database_migration_performed": False,
            "program_files_replaced": False,
            "live_restore_performed": False,
            "requires_fresh_pre_restore_backup": True,
            "requires_customer_admin_confirmation": True,
            "requires_service_stop_window": True,
            "requires_temporary_restore_first": True,
            "backup_file_body_stored": False,
            "commands_executed": [],
        },
        "warnings": [
            "本接口只生成 PostgreSQL 恢复演练计划，不执行 pg_restore。",
            "真实恢复必须另开维护窗口，并先恢复到临时库完成健康检查。",
            "真实恢复前必须创建当前库二次备份，并保留回滚路径。",
        ],
        "reason": reason,
    }


def _validate_postgres_temp_restore_rehearsal_manifest(
    manifest: dict[str, Any],
    *,
    backup_record: LocalBackupRecord,
) -> dict[str, Any]:
    blockers: list[str] = []
    if not isinstance(manifest, dict):
        raise LocalBackupUnsupported("PostgreSQL temp restore rehearsal manifest must be a JSON object")
    if backup_record.backup_type != "postgres_pg_dump_custom":
        blockers.append("backup_type must be postgres_pg_dump_custom")
    if backup_record.status != "verified":
        blockers.append("backup status must be verified")
    if backup_record.restore_mode != "pg_restore_list_rehearsal_only":
        blockers.append("restore_mode must be pg_restore_list_rehearsal_only")
    if backup_record.file_path != "external_manifest_only":
        blockers.append("PostgreSQL backup file body must not be stored by the service")
    if manifest.get("schema_version") != POSTGRES_TEMP_RESTORE_REHEARSAL_SCHEMA_VERSION:
        blockers.append("schema_version mismatch")
    if manifest.get("status") != "postgres_temp_restore_rehearsal_ready":
        blockers.append("status must be postgres_temp_restore_rehearsal_ready")
    if manifest.get("restore_mode") != "temporary_database_rehearsal_only":
        blockers.append("restore_mode must be temporary_database_rehearsal_only")

    backup_sha256 = str(manifest.get("backup_sha256") or "")
    if backup_sha256.lower() != str(backup_record.sha256).lower():
        blockers.append("backup_sha256 must match the registered backup record")
    if not re.fullmatch(r"[a-fA-F0-9]{64}", backup_sha256):
        blockers.append("backup_sha256 must be a 64-char sha256 hex digest")

    temp_database_name = str(manifest.get("temp_database_name") or "")
    if not _is_safe_temp_restore_database_name(temp_database_name):
        blockers.append("temp_database_name must use a safe wanfa_restore_tmp_ prefix")

    for key in (
        "temp_database_created",
        "pg_restore_into_temp_completed",
        "health_checks_completed",
        "temp_database_dropped",
    ):
        if manifest.get(key) is not True:
            blockers.append(f"{key} must be true")
    for key in (
        "live_restore_performed",
        "live_database_replaced",
        "database_replaced",
        "program_files_replaced",
        "external_write_enabled",
        "trusted_inbound_worker_enabled",
        "commands_executed_on_live_database",
        "backup_file_body_stored",
    ):
        if manifest.get(key) is not False:
            blockers.append(f"{key} must be false")
    restored_table_count = _positive_int(manifest.get("restored_table_count"))
    if restored_table_count is None:
        blockers.append("restored_table_count must be positive")
    health_check_count = _positive_int(manifest.get("health_check_count"))
    if health_check_count is None:
        blockers.append("health_check_count must be positive")
    if _contains_sensitive_key(manifest):
        blockers.append("manifest contains sensitive key names")

    if blockers:
        raise LocalBackupUnsupported("invalid PostgreSQL temp restore rehearsal manifest: " + "; ".join(blockers))

    normalized = dict(manifest)
    normalized["backup_sha256"] = backup_sha256.lower()
    normalized["restored_table_count"] = int(restored_table_count or 0)
    normalized["health_check_count"] = int(health_check_count or 0)
    normalized["temp_database_name_hash"] = _hash_text(temp_database_name)
    normalized["temp_database_name_stored"] = False
    normalized.pop("temp_database_name", None)
    return normalized


def _is_safe_temp_restore_database_name(name: str) -> bool:
    lowered = name.lower()
    if not _TEMP_RESTORE_DB_RE.fullmatch(lowered):
        return False
    return not any(part in lowered for part in _FORBIDDEN_TEMP_DB_PARTS)


def _postgres_temp_restore_rehearsal_record_payload(
    *,
    backup_record: LocalBackupRecord,
    tenant: Tenant,
    manifest: dict[str, Any],
    generated_at: datetime,
    reason: str,
) -> dict[str, Any]:
    return {
        "schema_version": POSTGRES_TEMP_RESTORE_REGISTRATION_SCHEMA_VERSION,
        "temp_restore_rehearsal_id": (
            f"pg-temp-restore-{backup_record.backup_id}-{generated_at.strftime('%Y%m%d%H%M%S')}-{uuid4().hex[:8]}"
        ),
        "source_manifest_schema_version": POSTGRES_TEMP_RESTORE_REHEARSAL_SCHEMA_VERSION,
        "backup_id": backup_record.backup_id,
        "tenant_id": tenant.id,
        "generated_at": generated_at.isoformat(),
        "dry_run": True,
        "can_restore_now": False,
        "rehearsal_ready": True,
        "restore_mode": "pg_restore_to_temporary_database_only",
        "backup_verification": {
            "ok": True,
            "sha256_match": True,
            "backup_sha256": manifest.get("backup_sha256"),
            "backup_file_body_stored": False,
        },
        "temporary_database": {
            "name_hash": manifest.get("temp_database_name_hash"),
            "name_stored": False,
            "created": True,
            "restored": True,
            "dropped": True,
            "restored_table_count": manifest.get("restored_table_count"),
        },
        "health_checks": [
            {"name": "temp_database_created", "status": "pass", "required": True},
            {"name": "pg_restore_into_temp_completed", "status": "pass", "required": True},
            {"name": "health_checks_completed", "status": "pass", "required": True},
            {"name": "temp_database_dropped", "status": "pass", "required": True},
            {"name": "live_restore_not_performed", "status": "pass", "required": True},
            {"name": "database_not_replaced", "status": "pass", "required": True},
        ],
        "blockers": [],
        "safety": {
            **_safety_payload(),
            "dry_run": True,
            "can_restore_now": False,
            "rehearsal_ready": True,
            "restore_mode": "pg_restore_to_temporary_database_only",
            "backup_file_body_stored": False,
            "temp_database_name_stored": False,
            "live_restore_performed": False,
            "database_replaced": False,
            "program_files_replaced": False,
            "external_write_enabled": False,
            "trusted_inbound_worker_enabled": False,
            "commands_executed_on_live_database": False,
            "requires_fresh_pre_restore_backup": True,
            "requires_customer_admin_confirmation": True,
            "requires_service_stop_window": True,
        },
        "warnings": [
            "该证据只说明备份曾恢复到临时 PostgreSQL 数据库并通过健康检查。",
            "系统没有替换真实数据库，也没有执行正式恢复。",
            "正式恢复仍需要维护窗口、恢复前二次备份、客户管理员确认和回滚路径。",
        ],
        "reason": reason,
    }


def _validate_postgres_formal_restore_preflight_confirmation(
    confirmation: dict[str, Any],
    *,
    backup_record: LocalBackupRecord,
) -> dict[str, Any]:
    blockers: list[str] = []
    if not isinstance(confirmation, dict):
        raise LocalBackupUnsupported("PostgreSQL formal restore preflight confirmation must be a JSON object")
    if backup_record.backup_type != "postgres_pg_dump_custom":
        blockers.append("backup_type must be postgres_pg_dump_custom")
    if backup_record.status != "verified":
        blockers.append("backup status must be verified")
    if backup_record.restore_mode != "pg_restore_list_rehearsal_only":
        blockers.append("restore_mode must be pg_restore_list_rehearsal_only")
    if backup_record.file_path != "external_manifest_only":
        blockers.append("PostgreSQL backup file body must not be stored by the service")
    if confirmation.get("schema_version") != POSTGRES_FORMAL_RESTORE_PREFLIGHT_SCHEMA_VERSION:
        blockers.append("schema_version mismatch")
    if confirmation.get("status") != "formal_restore_preflight_approval_ready":
        blockers.append("status must be formal_restore_preflight_approval_ready")

    manifest = backup_record.manifest_payload if isinstance(backup_record.manifest_payload, dict) else {}
    restore_plan = manifest.get("last_restore_rehearsal_plan")
    if not isinstance(restore_plan, dict):
        blockers.append("last_restore_rehearsal_plan is required before formal restore preflight")
    elif restore_plan.get("can_restore_now") is not False:
        blockers.append("last_restore_rehearsal_plan.can_restore_now must be false")

    temp_restore = manifest.get("last_temp_restore_rehearsal")
    if not isinstance(temp_restore, dict):
        blockers.append("last_temp_restore_rehearsal is required before formal restore preflight")
    else:
        if temp_restore.get("rehearsal_ready") is not True:
            blockers.append("last_temp_restore_rehearsal.rehearsal_ready must be true")
        safety = temp_restore.get("safety") if isinstance(temp_restore.get("safety"), dict) else {}
        for key in (
            "live_restore_performed",
            "database_replaced",
            "program_files_replaced",
            "external_write_enabled",
            "trusted_inbound_worker_enabled",
            "commands_executed_on_live_database",
        ):
            if safety.get(key) is not False:
                blockers.append(f"last_temp_restore_rehearsal.safety.{key} must be false")

    backup_sha256 = str(confirmation.get("backup_sha256") or "").lower()
    if backup_sha256 != str(backup_record.sha256).lower():
        blockers.append("backup_sha256 must match the registered backup record")
    if not re.fullmatch(r"[a-f0-9]{64}", backup_sha256):
        blockers.append("backup_sha256 must be a 64-char sha256 hex digest")

    approver_role = str(confirmation.get("approver_role") or "").strip().lower()
    if approver_role not in _FORMAL_RESTORE_APPROVER_ROLE_CODES:
        blockers.append("approver_role must be owner/admin/customer_admin/customer_owner")
    approver_identifier_hash = str(confirmation.get("approver_identifier_hash") or "").lower()
    if not re.fullmatch(r"[a-f0-9]{64}", approver_identifier_hash):
        blockers.append("approver_identifier_hash must be a 64-char sha256 hex digest")

    required_true = (
        "maintenance_window_approved",
        "service_stop_window_acknowledged",
        "fresh_pre_restore_backup_required",
        "temporary_restore_verified",
        "post_restore_health_check_plan_acknowledged",
        "rollback_plan_acknowledged",
        "customer_admin_confirmed",
        "final_operator_confirmation_required",
    )
    for key in required_true:
        if confirmation.get(key) is not True:
            blockers.append(f"{key} must be true")
    required_false = (
        "live_restore_performed",
        "database_replaced",
        "program_files_replaced",
        "external_write_enabled",
        "trusted_inbound_worker_enabled",
        "real_platform_send_enabled",
        "commands_executed_on_live_database",
        "backup_file_body_stored",
        "raw_customer_signature_stored",
        "automatic_restore_enabled",
    )
    for key in required_false:
        if confirmation.get(key) is not False:
            blockers.append(f"{key} must be false")
    maintenance_window_id = str(confirmation.get("maintenance_window_id") or "").strip()
    if len(maintenance_window_id) < 8:
        blockers.append("maintenance_window_id is required")
    approval_time = str(confirmation.get("approval_time") or "").strip()
    if len(approval_time) < 10:
        blockers.append("approval_time is required")
    if _contains_sensitive_key(confirmation):
        blockers.append("confirmation contains sensitive key names")

    if blockers:
        raise LocalBackupUnsupported("invalid PostgreSQL formal restore preflight confirmation: " + "; ".join(blockers))

    normalized = dict(confirmation)
    normalized["backup_sha256"] = backup_sha256
    normalized["approver_role"] = approver_role
    normalized["approver_identifier_hash"] = approver_identifier_hash
    normalized["maintenance_window_id_hash"] = _hash_text(maintenance_window_id)
    normalized["maintenance_window_id_stored"] = False
    normalized["approval_time"] = approval_time
    normalized.pop("maintenance_window_id", None)
    return normalized


def _postgres_formal_restore_preflight_record_payload(
    *,
    backup_record: LocalBackupRecord,
    tenant: Tenant,
    confirmation: dict[str, Any],
    generated_at: datetime,
    reason: str,
) -> dict[str, Any]:
    return {
        "schema_version": POSTGRES_FORMAL_RESTORE_PREFLIGHT_REGISTRATION_SCHEMA_VERSION,
        "formal_restore_preflight_id": (
            f"pg-formal-restore-preflight-{backup_record.backup_id}-"
            f"{generated_at.strftime('%Y%m%d%H%M%S')}-{uuid4().hex[:8]}"
        ),
        "source_confirmation_schema_version": POSTGRES_FORMAL_RESTORE_PREFLIGHT_SCHEMA_VERSION,
        "backup_id": backup_record.backup_id,
        "tenant_id": tenant.id,
        "generated_at": generated_at.isoformat(),
        "formal_restore_sop_ready": True,
        "manual_restore_window_ready": True,
        "can_execute_restore_now": False,
        "can_execute_restore_in_app": False,
        "restore_execution_performed": False,
        "requires_final_operator_confirmation": True,
        "backup_verification": {
            "ok": True,
            "sha256_match": True,
            "backup_sha256": confirmation.get("backup_sha256"),
            "backup_file_body_stored": False,
        },
        "preflight_requirements": {
            "maintenance_window_approved": True,
            "service_stop_window_acknowledged": True,
            "fresh_pre_restore_backup_required": True,
            "temporary_restore_verified": True,
            "post_restore_health_check_plan_acknowledged": True,
            "rollback_plan_acknowledged": True,
            "customer_admin_confirmed": True,
            "final_operator_confirmation_required": True,
            "approver_role": confirmation.get("approver_role"),
            "approver_identifier_hash": confirmation.get("approver_identifier_hash"),
            "maintenance_window_id_hash": confirmation.get("maintenance_window_id_hash"),
            "maintenance_window_id_stored": False,
            "approval_time": confirmation.get("approval_time"),
        },
        "restore_sop": [
            {"step": "verify_nc10_backup_manifest", "status": "pass", "required": True},
            {"step": "verify_nc11_restore_rehearsal_plan", "status": "pass", "required": True},
            {"step": "verify_nc12_temp_restore_rehearsal", "status": "pass", "required": True},
            {"step": "create_fresh_pre_restore_backup", "status": "required_next", "required": True},
            {"step": "stop_application_and_workers", "status": "required_next", "required": True},
            {"step": "final_operator_confirmation", "status": "required_next", "required": True},
            {"step": "manual_restore_execution", "status": "not_implemented_in_app", "required": True},
            {"step": "post_restore_health_checks", "status": "required_next", "required": True},
            {"step": "rollback_if_health_failed", "status": "required_next", "required": True},
        ],
        "safety": {
            **_safety_payload(),
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
        },
        "warnings": [
            "该记录只说明正式恢复前置门禁材料已登记，不执行真实恢复。",
            "真实恢复仍需要恢复前二次备份、停止服务、最终操作员确认和恢复后健康检查。",
            "系统内尚未提供一键替换生产数据库能力。",
        ],
        "reason": reason,
    }


def _validate_postgres_formal_restore_execution_dry_run_manifest(
    manifest: dict[str, Any],
    *,
    backup_record: LocalBackupRecord,
) -> dict[str, Any]:
    blockers: list[str] = []
    if not isinstance(manifest, dict):
        raise LocalBackupUnsupported("PostgreSQL formal restore execution dry-run manifest must be a JSON object")
    if backup_record.backup_type != "postgres_pg_dump_custom":
        blockers.append("backup_type must be postgres_pg_dump_custom")
    if backup_record.status != "verified":
        blockers.append("backup status must be verified")
    if backup_record.restore_mode != "pg_restore_list_rehearsal_only":
        blockers.append("restore_mode must be pg_restore_list_rehearsal_only")
    if backup_record.file_path != "external_manifest_only":
        blockers.append("PostgreSQL backup file body must not be stored by the service")
    if manifest.get("schema_version") != POSTGRES_FORMAL_RESTORE_EXECUTION_DRY_RUN_SCHEMA_VERSION:
        blockers.append("schema_version mismatch")
    if manifest.get("status") != "formal_restore_execution_dry_run_ready":
        blockers.append("status must be formal_restore_execution_dry_run_ready")
    if manifest.get("restore_mode") != "formal_restore_execution_dry_run_only":
        blockers.append("restore_mode must be formal_restore_execution_dry_run_only")

    existing_manifest = backup_record.manifest_payload if isinstance(backup_record.manifest_payload, dict) else {}
    preflight = existing_manifest.get("last_formal_restore_preflight")
    if not isinstance(preflight, dict):
        blockers.append("last_formal_restore_preflight is required before formal restore execution dry-run")
    else:
        for key in ("can_execute_restore_now", "can_execute_restore_in_app", "restore_execution_performed"):
            if preflight.get(key) is not False:
                blockers.append(f"last_formal_restore_preflight.{key} must be false")
        safety = preflight.get("safety") if isinstance(preflight.get("safety"), dict) else {}
        for key in (
            "live_restore_performed",
            "database_replaced",
            "program_files_replaced",
            "external_write_enabled",
            "trusted_inbound_worker_enabled",
            "real_platform_send_enabled",
            "commands_executed_on_live_database",
            "automatic_restore_enabled",
        ):
            if safety.get(key) is not False:
                blockers.append(f"last_formal_restore_preflight.safety.{key} must be false")

    backup_sha256 = str(manifest.get("backup_sha256") or "").lower()
    if backup_sha256 != str(backup_record.sha256).lower():
        blockers.append("backup_sha256 must match the registered backup record")
    if not re.fullmatch(r"[a-f0-9]{64}", backup_sha256):
        blockers.append("backup_sha256 must be a 64-char sha256 hex digest")

    required_true = (
        "restore_commands_rendered_not_executed",
        "final_operator_confirmation_required",
        "service_stop_required",
        "fresh_pre_restore_backup_required",
        "post_restore_health_check_required",
        "rollback_plan_required",
        "manual_restore_window_required",
    )
    for key in required_true:
        if manifest.get(key) is not True:
            blockers.append(f"{key} must be true")
    required_false = (
        "live_restore_performed",
        "database_replaced",
        "program_files_replaced",
        "external_write_enabled",
        "trusted_inbound_worker_enabled",
        "real_platform_send_enabled",
        "commands_executed_on_live_database",
        "pg_restore_executed_on_live_database",
        "automatic_restore_enabled",
        "backup_file_body_stored",
        "raw_restore_command_stored",
        "restore_command_preview_stored",
    )
    for key in required_false:
        if manifest.get(key) is not False:
            blockers.append(f"{key} must be false")

    raw_hashes = manifest.get("restore_command_preview_hashes")
    if not isinstance(raw_hashes, list) or not raw_hashes:
        blockers.append("restore_command_preview_hashes must be a non-empty list")
        command_hashes: list[str] = []
    else:
        command_hashes = [str(item).lower() for item in raw_hashes]
        for item in command_hashes:
            if not re.fullmatch(r"[a-f0-9]{64}", item):
                blockers.append("restore_command_preview_hashes must contain only 64-char sha256 hex digests")
                break
    if _contains_sensitive_key(manifest):
        blockers.append("manifest contains sensitive key names")

    if blockers:
        raise LocalBackupUnsupported(
            "invalid PostgreSQL formal restore execution dry-run manifest: " + "; ".join(blockers)
        )

    normalized = dict(manifest)
    normalized["backup_sha256"] = backup_sha256
    normalized["restore_command_preview_hashes"] = command_hashes
    return normalized


def _postgres_formal_restore_execution_dry_run_record_payload(
    *,
    backup_record: LocalBackupRecord,
    tenant: Tenant,
    manifest: dict[str, Any],
    generated_at: datetime,
    reason: str,
) -> dict[str, Any]:
    existing_manifest = backup_record.manifest_payload if isinstance(backup_record.manifest_payload, dict) else {}
    preflight = existing_manifest.get("last_formal_restore_preflight")
    preflight_id = preflight.get("formal_restore_preflight_id") if isinstance(preflight, dict) else ""
    return {
        "schema_version": POSTGRES_FORMAL_RESTORE_EXECUTION_DRY_RUN_REGISTRATION_SCHEMA_VERSION,
        "formal_restore_execution_dry_run_id": (
            f"pg-formal-restore-exec-dry-run-{backup_record.backup_id}-"
            f"{generated_at.strftime('%Y%m%d%H%M%S')}-{uuid4().hex[:8]}"
        ),
        "source_manifest_schema_version": POSTGRES_FORMAL_RESTORE_EXECUTION_DRY_RUN_SCHEMA_VERSION,
        "source_preflight_id": preflight_id,
        "backup_id": backup_record.backup_id,
        "tenant_id": tenant.id,
        "generated_at": generated_at.isoformat(),
        "formal_restore_execution_dry_run_ready": True,
        "rehearsal_ready": True,
        "restore_mode": "formal_restore_execution_dry_run_only",
        "restore_commands_rendered_not_executed": True,
        "restore_command_preview_hashes": manifest.get("restore_command_preview_hashes", []),
        "restore_command_preview_stored": False,
        "raw_restore_command_stored": False,
        "can_execute_restore_now": False,
        "can_execute_restore_in_app": False,
        "restore_execution_performed": False,
        "backup_verification": {
            "ok": True,
            "sha256_match": True,
            "backup_sha256": manifest.get("backup_sha256"),
            "backup_file_body_stored": False,
        },
        "execution_requirements": {
            "manual_restore_window_required": True,
            "service_stop_required": True,
            "fresh_pre_restore_backup_required": True,
            "final_operator_confirmation_required": True,
            "post_restore_health_check_required": True,
            "rollback_plan_required": True,
        },
        "execution_safety": {
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
        },
        "safety": {
            **_safety_payload(),
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
        },
        "warnings": [
            "该记录只说明正式恢复执行 dry-run 外壳已生成，不执行真实恢复。",
            "系统只保存恢复命令预览 hash，不保存原始命令文本。",
            "真实恢复仍需要停机窗口、恢复前二次备份、最终操作员确认、健康检查和回滚路径。",
        ],
        "reason": reason,
    }


def _validate_postgres_formal_restore_runbook(
    runbook: dict[str, Any],
    *,
    backup_record: LocalBackupRecord,
) -> dict[str, Any]:
    blockers: list[str] = []
    if not isinstance(runbook, dict):
        raise LocalBackupUnsupported("PostgreSQL formal restore runbook must be a JSON object")
    if backup_record.backup_type != "postgres_pg_dump_custom":
        blockers.append("backup_type must be postgres_pg_dump_custom")
    if backup_record.status != "verified":
        blockers.append("backup status must be verified")
    if backup_record.restore_mode != "pg_restore_list_rehearsal_only":
        blockers.append("restore_mode must be pg_restore_list_rehearsal_only")
    if backup_record.file_path != "external_manifest_only":
        blockers.append("PostgreSQL backup file body must not be stored by the service")
    if runbook.get("schema_version") != POSTGRES_FORMAL_RESTORE_RUNBOOK_SCHEMA_VERSION:
        blockers.append("schema_version mismatch")
    if runbook.get("status") != "formal_restore_runbook_ready":
        blockers.append("status must be formal_restore_runbook_ready")

    existing_manifest = backup_record.manifest_payload if isinstance(backup_record.manifest_payload, dict) else {}
    execution_dry_run = existing_manifest.get("last_formal_restore_execution_dry_run")
    if not isinstance(execution_dry_run, dict):
        blockers.append("last_formal_restore_execution_dry_run is required before formal restore runbook")
    else:
        if execution_dry_run.get("formal_restore_execution_dry_run_ready") is not True:
            blockers.append("last_formal_restore_execution_dry_run.formal_restore_execution_dry_run_ready must be true")
        for key in ("can_execute_restore_now", "can_execute_restore_in_app", "restore_execution_performed"):
            if execution_dry_run.get(key) is not False:
                blockers.append(f"last_formal_restore_execution_dry_run.{key} must be false")
        safety = execution_dry_run.get("execution_safety")
        if not isinstance(safety, dict):
            blockers.append("last_formal_restore_execution_dry_run.execution_safety is required")
        else:
            for key in (
                "live_restore_performed",
                "database_replaced",
                "program_files_replaced",
                "external_write_enabled",
                "trusted_inbound_worker_enabled",
                "real_platform_send_enabled",
                "commands_executed_on_live_database",
                "pg_restore_executed_on_live_database",
                "automatic_restore_enabled",
                "backup_file_body_stored",
                "raw_restore_command_stored",
            ):
                if safety.get(key) is not False:
                    blockers.append(f"last_formal_restore_execution_dry_run.execution_safety.{key} must be false")

    backup_sha256 = str(runbook.get("backup_sha256") or "").lower()
    if backup_sha256 != str(backup_record.sha256).lower():
        blockers.append("backup_sha256 must match the registered backup record")
    if not re.fullmatch(r"[a-f0-9]{64}", backup_sha256):
        blockers.append("backup_sha256 must be a 64-char sha256 hex digest")

    required_true = (
        "maintenance_window_locked",
        "service_stop_sequence_documented",
        "fresh_pre_restore_backup_step_required",
        "final_operator_confirmation_required",
        "restore_command_hashes_reviewed",
        "post_restore_health_checks_documented",
        "rollback_decision_tree_documented",
        "customer_communication_plan_documented",
        "manual_execution_only",
    )
    for key in required_true:
        if runbook.get(key) is not True:
            blockers.append(f"{key} must be true")

    required_false = (
        "live_restore_performed",
        "database_replaced",
        "program_files_replaced",
        "external_write_enabled",
        "trusted_inbound_worker_enabled",
        "real_platform_send_enabled",
        "commands_executed_on_live_database",
        "pg_restore_executed_on_live_database",
        "automatic_restore_enabled",
        "backup_file_body_stored",
        "raw_restore_command_stored",
        "restore_command_preview_stored",
        "runbook_sensitive_material_stored",
    )
    for key in required_false:
        if runbook.get(key) is not False:
            blockers.append(f"{key} must be false")

    raw_hashes = runbook.get("restore_command_preview_hashes")
    if not isinstance(raw_hashes, list) or not raw_hashes:
        blockers.append("restore_command_preview_hashes must be a non-empty list")
        command_hashes: list[str] = []
    else:
        command_hashes = [str(item).lower() for item in raw_hashes]
        for item in command_hashes:
            if not re.fullmatch(r"[a-f0-9]{64}", item):
                blockers.append("restore_command_preview_hashes must contain only 64-char sha256 hex digests")
                break
    dry_run_hashes: list[str] = []
    if isinstance(execution_dry_run, dict):
        raw_dry_run_hashes = execution_dry_run.get("restore_command_preview_hashes")
        if isinstance(raw_dry_run_hashes, list):
            dry_run_hashes = [str(item).lower() for item in raw_dry_run_hashes]
    if dry_run_hashes and command_hashes != dry_run_hashes:
        blockers.append("restore_command_preview_hashes must match last_formal_restore_execution_dry_run")

    runbook_version = str(runbook.get("runbook_version") or "")
    if len(runbook_version) < 3:
        blockers.append("runbook_version is required")
    for key in ("maintenance_window_id_hash", "operator_identifier_hash", "observer_identifier_hash"):
        value = str(runbook.get(key) or "").lower()
        if not re.fullmatch(r"[a-f0-9]{64}", value):
            blockers.append(f"{key} must be a 64-char sha256 hex digest")

    if _contains_sensitive_key(runbook):
        blockers.append("runbook contains sensitive key names")

    if blockers:
        raise LocalBackupUnsupported("invalid PostgreSQL formal restore runbook: " + "; ".join(blockers))

    normalized = dict(runbook)
    normalized["backup_sha256"] = backup_sha256
    normalized["restore_command_preview_hashes"] = command_hashes
    normalized["maintenance_window_id_hash"] = str(runbook["maintenance_window_id_hash"]).lower()
    normalized["operator_identifier_hash"] = str(runbook["operator_identifier_hash"]).lower()
    normalized["observer_identifier_hash"] = str(runbook["observer_identifier_hash"]).lower()
    return normalized


def _postgres_formal_restore_runbook_record_payload(
    *,
    backup_record: LocalBackupRecord,
    tenant: Tenant,
    runbook: dict[str, Any],
    generated_at: datetime,
    reason: str,
) -> dict[str, Any]:
    existing_manifest = backup_record.manifest_payload if isinstance(backup_record.manifest_payload, dict) else {}
    execution_dry_run = existing_manifest.get("last_formal_restore_execution_dry_run")
    execution_dry_run_id = (
        execution_dry_run.get("formal_restore_execution_dry_run_id") if isinstance(execution_dry_run, dict) else ""
    )
    return {
        "schema_version": POSTGRES_FORMAL_RESTORE_RUNBOOK_REGISTRATION_SCHEMA_VERSION,
        "formal_restore_runbook_id": (
            f"pg-formal-restore-runbook-{backup_record.backup_id}-"
            f"{generated_at.strftime('%Y%m%d%H%M%S')}-{uuid4().hex[:8]}"
        ),
        "source_runbook_schema_version": POSTGRES_FORMAL_RESTORE_RUNBOOK_SCHEMA_VERSION,
        "source_execution_dry_run_id": execution_dry_run_id,
        "backup_id": backup_record.backup_id,
        "tenant_id": tenant.id,
        "generated_at": generated_at.isoformat(),
        "runbook_version": runbook.get("runbook_version"),
        "formal_restore_runbook_ready": True,
        "rehearsal_ready": True,
        "restore_mode": "manual_formal_restore_sop_only",
        "manual_execution_only": True,
        "can_execute_restore_now": False,
        "can_execute_restore_in_app": False,
        "restore_execution_performed": False,
        "restore_command_preview_hashes": runbook.get("restore_command_preview_hashes", []),
        "restore_command_preview_stored": False,
        "raw_restore_command_stored": False,
        "backup_verification": {
            "ok": True,
            "sha256_match": True,
            "backup_sha256": runbook.get("backup_sha256"),
            "backup_file_body_stored": False,
        },
        "runbook_requirements": {
            "maintenance_window_locked": True,
            "service_stop_sequence_documented": True,
            "fresh_pre_restore_backup_step_required": True,
            "final_operator_confirmation_required": True,
            "restore_command_hashes_reviewed": True,
            "post_restore_health_checks_documented": True,
            "rollback_decision_tree_documented": True,
            "customer_communication_plan_documented": True,
        },
        "runbook_steps": [
            {"step": "freeze_change_window", "status": "documented", "performed": False},
            {"step": "notify_customer", "status": "documented", "performed": False},
            {"step": "create_fresh_pre_restore_backup", "status": "required_at_execution_time", "performed": False},
            {"step": "stop_application_and_workers", "status": "manual_required", "performed": False},
            {"step": "final_operator_confirmation", "status": "manual_required", "performed": False},
            {"step": "execute_pg_restore", "status": "manual_required_outside_app", "performed": False},
            {"step": "post_restore_health_checks", "status": "manual_required", "performed": False},
            {"step": "rollback_if_unhealthy", "status": "manual_required", "performed": False},
        ],
        "operator_hashes": {
            "maintenance_window_id_hash": runbook.get("maintenance_window_id_hash"),
            "operator_identifier_hash": runbook.get("operator_identifier_hash"),
            "observer_identifier_hash": runbook.get("observer_identifier_hash"),
        },
        "execution_safety": {
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
        },
        "safety": {
            **_safety_payload(),
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
        },
        "warnings": [
            "该记录只说明正式恢复 SOP 与停机编排门禁已登记，不执行真实恢复。",
            "真实恢复只能在停机窗口内由人工按客户确认后的 SOP 执行。",
            "系统仍不保存原始恢复命令、不保存 dump 本体、不替换真实数据库、不打开真实外发。",
        ],
        "reason": reason,
    }


def _positive_int(value: Any) -> int | None:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


def _contains_sensitive_key(value: Any) -> bool:
    if isinstance(value, dict):
        for key, nested in value.items():
            if _SENSITIVE_KEY_RE.search(str(key)):
                return True
            if _contains_sensitive_key(nested):
                return True
    if isinstance(value, list):
        return any(_contains_sensitive_key(item) for item in value)
    return False


def _local_backup_dir() -> Path:
    configured = Path(get_settings().local_backup_dir).expanduser()
    if configured.is_absolute():
        return configured
    return (Path.cwd() / configured).resolve()


def _copy_sqlite_database(source_path: Path, backup_path: Path) -> None:
    if backup_path.exists():
        raise LocalBackupUnsupported("backup file already exists")
    source_uri = f"{source_path.as_uri()}?mode=ro"
    with sqlite3.connect(source_uri, uri=True) as source, sqlite3.connect(str(backup_path)) as target:
        source.backup(target)


def _verify_backup_file(path: Path, *, expected_sha256: str) -> dict[str, Any]:
    if not path.exists() or not path.is_file():
        return {
            "ok": False,
            "message": "backup file is missing",
            "sha256_match": False,
            "integrity_check": "not_run",
        }
    actual_sha256 = _sha256_file(path)
    if actual_sha256 != expected_sha256:
        return {
            "ok": False,
            "message": "backup checksum mismatch",
            "sha256_match": False,
            "integrity_check": "not_run",
        }
    try:
        uri = f"{path.resolve().as_uri()}?mode=ro"
        with sqlite3.connect(uri, uri=True) as connection:
            integrity = str(connection.execute("PRAGMA integrity_check").fetchone()[0])
    except sqlite3.Error as exc:
        return {
            "ok": False,
            "message": f"backup sqlite integrity check failed: {exc}",
            "sha256_match": True,
            "integrity_check": "error",
        }
    return {
        "ok": integrity.lower() == "ok",
        "message": "backup verified" if integrity.lower() == "ok" else f"backup integrity check returned {integrity}",
        "sha256_match": True,
        "integrity_check": integrity,
    }


def _build_manifest(
    *,
    tenant: Tenant,
    backup_id: str,
    backup_file_name: str,
    source_path: Path,
    created_at: datetime,
    reason: str,
    file_size_bytes: int,
    sha256: str,
) -> dict[str, Any]:
    return {
        "schema_version": BACKUP_SCHEMA_VERSION,
        "backup_id": backup_id,
        "backup_type": "sqlite_database",
        "tenant": {
            "id": tenant.id,
            "slug": tenant.slug,
            "name": tenant.name,
        },
        "file": {
            "name": backup_file_name,
            "size_bytes": file_size_bytes,
            "sha256": sha256,
        },
        "source": {
            "database_label": source_path.name,
            "database_path_hash": _hash_text(str(source_path.resolve())),
        },
        "restore": {
            "mode": "manual_rehearsal_only",
            "live_restore_performed": False,
            "requires_service_stop": True,
            "requires_operator_confirmation": True,
        },
        "safety": _safety_payload(),
        "reason": reason,
        "created_at": created_at.isoformat(),
    }


def _record_payload(record: LocalBackupRecord) -> dict[str, Any]:
    return {
        "id": record.id,
        "tenant_id": record.tenant_id,
        "backup_id": record.backup_id,
        "backup_type": record.backup_type,
        "status": record.status,
        "file_name": record.file_name,
        "file_size_bytes": record.file_size_bytes,
        "sha256": record.sha256,
        "source_database_label": record.source_database_label,
        "source_database_hash": record.source_database_hash,
        "restore_mode": record.restore_mode,
        "manifest_payload": record.manifest_payload or {},
        "safety": _safety_payload(),
        "created_by_id": record.created_by_id,
        "created_at": record.created_at,
        "verified_at": record.verified_at,
        "error_message": record.error_message,
    }


def _safety_payload() -> dict[str, Any]:
    return {
        "external_upload_performed": False,
        "external_platform_write_performed": False,
        "model_call_performed": False,
        "live_restore_performed": False,
        "database_file_path_exposed_to_frontend": False,
    }


def _restore_rehearsal_steps() -> list[dict[str, Any]]:
    return [
        {
            "step": "confirm_maintenance_window",
            "label": "确认维护窗口",
            "description": "通知客户当前客服系统将进入离线维护窗口，暂停真实渠道外发和更新操作。",
            "performed": False,
            "required": True,
        },
        {
            "step": "create_fresh_current_backup",
            "label": "创建当前库二次备份",
            "description": "真实恢复前先备份当前正在运行的数据库，用于失败回退。",
            "performed": False,
            "required": True,
        },
        {
            "step": "stop_application_services",
            "label": "停止本地服务",
            "description": "停止后端、前端壳层和后台 worker，避免运行中数据库文件被覆盖。",
            "performed": False,
            "required": True,
        },
        {
            "step": "verify_restore_source",
            "label": "校验恢复源",
            "description": "再次校验备份文件 sha256 和 SQLite integrity_check。",
            "performed": False,
            "required": True,
        },
        {
            "step": "replace_database_file_offline",
            "label": "离线替换数据库文件",
            "description": "由本机恢复工具执行文件替换；当前接口不会执行这一步。",
            "performed": False,
            "required": True,
        },
        {
            "step": "restart_and_health_check",
            "label": "重启并健康检查",
            "description": "重启服务后检查 /health、登录、账号、知识库和最近备份记录。",
            "performed": False,
            "required": True,
        },
        {
            "step": "rollback_if_health_failed",
            "label": "失败回退",
            "description": "如果健康检查失败，使用恢复前二次备份回退。",
            "performed": False,
            "required": True,
        },
    ]


def _restore_health_checks(*, backup_verification: dict[str, Any], rehearsal_ready: bool) -> list[dict[str, Any]]:
    return [
        {
            "name": "backup_sha256_match",
            "status": "pass" if backup_verification.get("sha256_match") else "blocked",
            "required": True,
        },
        {
            "name": "backup_sqlite_integrity",
            "status": "pass" if backup_verification.get("integrity_check") == "ok" else "blocked",
            "required": True,
        },
        {
            "name": "offline_restore_tool_available",
            "status": "pending",
            "required": True,
        },
        {
            "name": "fresh_pre_restore_backup",
            "status": "pending",
            "required": True,
        },
        {
            "name": "operator_confirmation",
            "status": "pending",
            "required": True,
        },
        {
            "name": "dry_run_rehearsal_ready",
            "status": "pass" if rehearsal_ready else "blocked",
            "required": True,
        },
    ]


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _hash_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()
