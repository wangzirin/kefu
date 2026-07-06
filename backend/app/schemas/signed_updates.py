from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


SignedUpdatePackageType = Literal["knowledge", "strategy", "program"]


class SignedUpdateOperation(BaseModel):
    target: str = Field(min_length=1, max_length=120)
    action: str = Field(min_length=1, max_length=80)
    count: int = Field(default=0, ge=0)
    summary: str = Field(default="", max_length=500)


class SignedUpdateManifest(BaseModel):
    schema_version: str = Field(default="wanfa.signed_update_manifest.v1")
    package_id: str = Field(min_length=1, max_length=160)
    package_name: str = Field(min_length=1, max_length=180)
    package_type: SignedUpdatePackageType
    package_version: str = Field(min_length=1, max_length=80)
    product: str = Field(default="wanfa-standard-ops", max_length=120)
    released_at: str = Field(default="", max_length=80)
    compatible_app_versions: list[str] = Field(default_factory=list, max_length=40)
    requires_maintenance_window: bool = False
    payload_digest_sha256: str = Field(min_length=64, max_length=64)
    payload_size_bytes: int | None = Field(default=None, ge=0)
    operations: list[SignedUpdateOperation] = Field(default_factory=list, max_length=100)


class SignedUpdateSignature(BaseModel):
    algorithm: Literal["rsa_pkcs1v15_sha256"]
    key_id: str = Field(min_length=1, max_length=120)
    value: str = Field(min_length=1)


class SignedUpdatePackagePayload(BaseModel):
    schema_version: Literal["wanfa.signed_update_package.v1"]
    manifest: SignedUpdateManifest
    payload: dict[str, Any] = Field(default_factory=dict)
    release_notes: str = Field(default="", max_length=20000)
    checksums: dict[str, Any] = Field(default_factory=dict)
    signature: SignedUpdateSignature


class SignedUpdatePreflightCreate(BaseModel):
    package: SignedUpdatePackagePayload


class SignedUpdatePreflightRead(BaseModel):
    package_id: str
    package_name: str
    package_type: SignedUpdatePackageType
    package_version: str
    dry_run: bool
    can_stage: bool
    can_apply_now: bool
    current_app_version: str
    signature_status: dict[str, Any]
    checksum_status: dict[str, Any]
    compatibility: dict[str, Any]
    backup_plan: dict[str, Any]
    health_checks: list[dict[str, Any]]
    operations: list[dict[str, Any]]
    warnings: list[str]
    errors: list[str]
    safety: dict[str, Any]


class SignedUpdateStageCreate(BaseModel):
    package: SignedUpdatePackagePayload


class SignedUpdateApplyCreate(BaseModel):
    reason: str = Field(default="客户管理员确认应用本次签名更新包。", max_length=1000)


class SignedUpdateRollbackCreate(BaseModel):
    reason: str = Field(default="客户管理员确认回滚本次签名更新包。", max_length=1000)


class SignedUpdateProgramDryRunCreate(BaseModel):
    reason: str = Field(default="客户管理员确认只生成程序更新演练计划。", max_length=1000)


class SignedUpdateStagedPackageRead(BaseModel):
    id: int
    package_id: str
    package_name: str
    package_type: SignedUpdatePackageType
    package_version: str
    status: str
    current_app_version: str
    package_digest_sha256: str
    can_apply_now: bool
    backup_required: bool
    backup_created: bool
    preflight_result: dict[str, Any]
    backup_plan: dict[str, Any]
    health_checks: list[dict[str, Any]]
    safety: dict[str, Any]
    knowledge_import_batch_id: int | None = None
    apply_result: dict[str, Any] = Field(default_factory=dict)
    rollback_result: dict[str, Any] = Field(default_factory=dict)
    staged_by_id: int | None
    staged_at: datetime
    applied_at: datetime | None = None
    error_message: str = ""
