from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class LocalBackupCreate(BaseModel):
    reason: str = Field(default="客户管理员手动创建本地数据库备份点。", max_length=1000)


class LocalBackupVerifyCreate(BaseModel):
    reason: str = Field(default="客户管理员执行本地备份完整性校验。", max_length=1000)


class LocalBackupRestoreDryRunCreate(BaseModel):
    reason: str = Field(default="客户管理员执行本地恢复工具演练。", max_length=1000)


class LocalPostgresBackupManifestRegister(BaseModel):
    manifest_payload: dict[str, Any]
    reason: str = Field(default="客户管理员登记 PostgreSQL 备份可读性演练证据。", max_length=1000)


class LocalPostgresRestoreRehearsalPlanCreate(BaseModel):
    reason: str = Field(default="客户管理员生成 PostgreSQL 恢复演练计划。", max_length=1000)


class LocalPostgresTempRestoreManifestRegister(BaseModel):
    backup_record_id: int
    manifest_payload: dict[str, Any]
    reason: str = Field(default="客户管理员登记 PostgreSQL 临时库恢复演练证据。", max_length=1000)


class LocalPostgresFormalRestorePreflightRegister(BaseModel):
    backup_record_id: int
    confirmation_payload: dict[str, Any]
    reason: str = Field(default="客户管理员登记 PostgreSQL 正式恢复前确认门禁。", max_length=1000)


class LocalPostgresFormalRestoreExecutionDryRunRegister(BaseModel):
    backup_record_id: int
    manifest_payload: dict[str, Any]
    reason: str = Field(default="客户管理员登记 PostgreSQL 正式恢复执行 dry-run 证据。", max_length=1000)


class LocalPostgresFormalRestoreRunbookRegister(BaseModel):
    backup_record_id: int
    runbook_payload: dict[str, Any]
    reason: str = Field(default="客户管理员登记 PostgreSQL 正式恢复 SOP 与停机编排门禁。", max_length=1000)


class LocalBackupRead(BaseModel):
    id: int
    tenant_id: int
    backup_id: str
    backup_type: str
    status: str
    file_name: str
    file_size_bytes: int
    sha256: str
    source_database_label: str
    source_database_hash: str
    restore_mode: str
    manifest_payload: dict[str, Any]
    safety: dict[str, Any]
    created_by_id: int | None
    created_at: datetime
    verified_at: datetime | None = None
    error_message: str = ""


class LocalBackupRestoreDryRunRead(BaseModel):
    schema_version: str
    restore_dry_run_id: str
    backup_id: str
    tenant_id: int
    generated_at: datetime
    dry_run: bool
    can_restore_now: bool
    rehearsal_ready: bool
    restore_mode: str
    backup_verification: dict[str, Any]
    current_database: dict[str, Any]
    rehearsal_plan: list[dict[str, Any]]
    health_checks: list[dict[str, Any]]
    blockers: list[str]
    safety: dict[str, Any]
    warnings: list[str]
