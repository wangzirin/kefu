from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class DiagnosticBundleRead(BaseModel):
    schema_version: str
    filename: str
    generated_at: datetime
    tenant: dict[str, Any]
    runtime: dict[str, Any]
    health: dict[str, Any]
    counts: dict[str, int]
    knowledge: dict[str, Any]
    quality: dict[str, Any]
    channels: dict[str, Any]
    queues: dict[str, Any]
    workers: dict[str, Any]
    recent_errors: list[dict[str, Any]]
    recent_changes: list[dict[str, Any]]
    safety: dict[str, Any]
    warnings: list[str]


class DiagnosticUploadPackageCreate(BaseModel):
    authorization_note: str = Field(default="客户管理员确认授权上传本次脱敏诊断包。", max_length=1000)
    contact_name: str = Field(default="", max_length=120)
    support_ticket: str = Field(default="", max_length=120)


class DiagnosticUploadPackageRead(BaseModel):
    schema_version: str
    filename: str
    generated_at: datetime
    tenant: dict[str, Any]
    authorization: dict[str, Any]
    upload_manifest: dict[str, Any]
    diagnostic_bundle: DiagnosticBundleRead
    safety: dict[str, Any]
    warnings: list[str]


class DiagnosticIntakeCreate(BaseModel):
    upload_package: dict[str, Any]
    source_channel: str = Field(default="manual_transfer", max_length=80)
    processing_note: str = Field(default="", max_length=1000)


class DiagnosticIntakeStatusUpdate(BaseModel):
    status: str = Field(default="in_review", max_length=40)
    processing_note: str = Field(default="", max_length=1000)


class DiagnosticIntakeRecordRead(BaseModel):
    id: int
    tenant_id: int
    intake_id: str
    status: str
    validation_status: str
    package_filename: str
    diagnostic_bundle_filename: str
    package_sha256: str
    diagnostic_bundle_sha256: str
    package_size_bytes: int
    source_channel: str
    rejection_reason: str
    processing_note: str
    authorization_summary: dict[str, Any]
    safety: dict[str, Any]
    received_by_id: int | None
    handled_by_id: int | None
    created_at: datetime
    updated_at: datetime
    handled_at: datetime | None
    download_supported: bool


class DiagnosticIntakeListRead(BaseModel):
    schema_version: str
    items: list[DiagnosticIntakeRecordRead]


class DiagnosticIntakeDownloadRead(BaseModel):
    schema_version: str
    intake_id: str
    filename: str
    content_type: str
    body_encoding: str
    body: str
    body_sha256: str
    body_bytes: int
    safety: dict[str, Any]


class DiagnosticRemediationRequestCreate(BaseModel):
    request_type: str = Field(default="knowledge_or_strategy_update", max_length=60)
    title: str = Field(default="", max_length=220)
    summary: str = Field(default="", max_length=1200)
    priority: str = Field(default="normal", max_length=30)


class DiagnosticRemediationRequestStatusUpdate(BaseModel):
    status: str = Field(default="in_review", max_length=40)
    summary: str = Field(default="", max_length=1200)


class DiagnosticRemediationUpdatePlanCreate(BaseModel):
    signed_update_package_id: int
    operator_note: str = Field(default="客户管理员确认进入受控更新计划。", max_length=1000)


class DiagnosticRemediationRequestRead(BaseModel):
    id: int
    tenant_id: int
    intake_record_id: int
    request_id: str
    request_type: str
    status: str
    priority: str
    title: str
    summary: str
    recommended_actions: list[dict[str, Any]]
    update_request_manifest: dict[str, Any]
    safety: dict[str, Any]
    created_by_id: int | None
    updated_by_id: int | None
    created_at: datetime
    updated_at: datetime
    download_supported: bool


class DiagnosticRemediationRequestListRead(BaseModel):
    schema_version: str
    items: list[DiagnosticRemediationRequestRead]


class DiagnosticRemediationRequestDownloadRead(BaseModel):
    schema_version: str
    request_id: str
    filename: str
    content_type: str
    body_encoding: str
    body: str
    body_sha256: str
    body_bytes: int
    safety: dict[str, Any]


class LocalMaintenanceReadinessRead(BaseModel):
    schema_version: str
    tenant_id: int
    generated_at: datetime
    maturity_status: str
    ready_for_customer_maintenance_rehearsal: bool
    summary: str
    counts: dict[str, int]
    latest: dict[str, Any]
    gates: list[dict[str, Any]]
    blockers: list[str]
    safety: dict[str, Any]
    recommended_next_steps: list[str]
    recent_audit_events: list[dict[str, Any]]
