from __future__ import annotations

from datetime import datetime
import hashlib
import json
import re
from typing import Any, Callable, TypeVar
from urllib.parse import urlparse

from sqlalchemy import func, select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.audit import add_audit_event
from app.models import (
    AuditEvent,
    BusinessObject,
    Channel,
    ChannelAccount,
    ChannelConnector,
    ChannelDeliveryReceipt,
    Contact,
    Conversation,
    DeliveryFailureReview,
    DiagnosticIntakeRecord,
    DiagnosticRemediationRequest,
    HumanReviewTask,
    KnowledgeCard,
    KnowledgeDocument,
    KnowledgeDocumentChunk,
    KnowledgeDocumentPublication,
    KnowledgeEmbeddingProviderSmokeRun,
    KnowledgeEvaluationCase,
    KnowledgeEvaluationRun,
    KnowledgeEvaluationSet,
    KnowledgeGapItem,
    KnowledgeImportBatch,
    LocalBackupRecord,
    Message,
    ObjectKnowledgeCard,
    OutboxDeliveryJob,
    OutboxDraft,
    OutboxSendAttempt,
    ReplyDecision,
    SalesLead,
    SignedUpdatePackage,
    SupportTicket,
    Tenant,
    TrustedInboundMessageJob,
    TrustedInboundWorkerRunRecord,
    User,
    WorkerHeartbeat,
    WorkflowRun,
    utc_now,
)

T = TypeVar("T")

PACKAGE_SCHEMA_VERSION = "p3-06u-26h2c.v1"
UPLOAD_PACKAGE_SCHEMA_VERSION = "p3-06u-26h2k.v1"
INTAKE_SCHEMA_VERSION = "p3-06u-26h2w5.diagnostic_intake.v1"
REMEDIATION_SCHEMA_VERSION = "p3-06u-26h2w6.diagnostic_remediation.v1"
REMEDIATION_UPDATE_PLAN_SCHEMA_VERSION = "p3-06u-26h2w6b.signed_update_control_plan.v1"
ALLOWED_INTAKE_STATUSES = {"received", "in_review", "resolved", "rejected"}
ALLOWED_REMEDIATION_STATUSES = {
    "draft",
    "in_review",
    "ready_for_customer",
    "update_plan_prepared",
    "delivered",
    "closed",
    "cancelled",
}
ALLOWED_REMEDIATION_TYPES = {
    "knowledge_or_strategy_update",
    "knowledge_update",
    "strategy_update",
    "program_dry_run",
    "backup_restore_review",
}
MAX_DIAGNOSTIC_UPLOAD_PACKAGE_BYTES = 768 * 1024
MAX_DIAGNOSTIC_UPLOAD_PACKAGE_DEPTH = 18
ALLOWED_UPLOAD_PACKAGE_KEYS = {
    "schema_version",
    "filename",
    "generated_at",
    "tenant",
    "authorization",
    "upload_manifest",
    "diagnostic_bundle",
    "safety",
    "warnings",
}
ALLOWED_DIAGNOSTIC_BUNDLE_KEYS = {
    "schema_version",
    "filename",
    "generated_at",
    "tenant",
    "runtime",
    "health",
    "counts",
    "knowledge",
    "quality",
    "channels",
    "queues",
    "workers",
    "recent_errors",
    "recent_changes",
    "safety",
    "warnings",
}

_CREDENTIAL_KV_RE = re.compile(
    r"(?i)\b(authorization|bearer|x-?api-?key|api[_-]?key|access[_-]?key|secret|token|cookie|password|passwd|private[_-]?key|encodingaeskey)\b\s*[:=]\s*([^\s,;]+)"
)
_CREDENTIAL_WORD_RE = re.compile(
    r"(?i)\b(authorization|bearer|x-?api-?key|api[_-]?key|access[_-]?key|secret|token|cookie|password|passwd|private[_-]?key|encodingaeskey)\b"
)
_BEARER_VALUE_RE = re.compile(r"(?i)\bbearer\s+[^\s,;]+")
_COMMON_KEY_VALUE_RE = re.compile(r"(?i)\bsk-[A-Za-z0-9_-]{8,}\b")
_EMAIL_RE = re.compile(r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b")
_PHONE_RE = re.compile(r"\b1[3-9]\d{9}\b")
_LONG_VALUE_RE = re.compile(r"\b[A-Za-z0-9_-]{24,}\b")
_CREDENTIAL_VALUE_SCAN_RE = re.compile(
    r"(?i)(bearer\s+[A-Za-z0-9._~+/-]{8,}|sk-[A-Za-z0-9_-]{8,}|AKIA[A-Za-z0-9]{12,}|AIza[A-Za-z0-9_-]{20,}|wanfa_session_[A-Za-z0-9_-]+)"
)


def build_diagnostic_bundle(db: Session, *, tenant: Tenant, generated_by_user_id: int) -> dict[str, Any]:
    warnings: list[str] = []
    generated_at = utc_now()
    settings = get_settings()

    def safe(label: str, fallback: T, loader: Callable[[], T]) -> T:
        try:
            return loader()
        except SQLAlchemyError as exc:
            warnings.append(f"{label} 采集失败：{redact_sensitive_text(str(exc))}")
            return fallback

    counts = safe("基础计数", {}, lambda: _collect_counts(db, tenant.id))
    bundle: dict[str, Any] = {
        "schema_version": PACKAGE_SCHEMA_VERSION,
        "filename": _diagnostic_filename(tenant.slug, generated_at),
        "generated_at": generated_at,
        "tenant": {
            "id": tenant.id,
            "name": tenant.name,
            "slug": tenant.slug,
            "plan": tenant.plan,
            "status": tenant.status,
        },
        "runtime": safe("运行环境", {}, lambda: _collect_runtime(db, settings)),
        "health": {
            "status": "ok",
            "generated_by_user_id": generated_by_user_id,
            "external_call_performed": False,
            "external_platform_write_performed": False,
        },
        "counts": counts,
        "knowledge": safe("知识库", {}, lambda: _collect_knowledge(db, tenant.id)),
        "quality": safe("质量评测", {}, lambda: _collect_quality(db, tenant.id)),
        "channels": safe("渠道配置", {}, lambda: _collect_channels(db, tenant.id)),
        "queues": safe("队列状态", {}, lambda: _collect_queues(db, tenant.id)),
        "workers": safe("后台进程", {}, lambda: _collect_workers(db, tenant.id)),
        "recent_errors": safe("近期错误", [], lambda: _collect_recent_errors(db, tenant.id)),
        "recent_changes": safe("近期变更", [], lambda: _collect_recent_changes(db, tenant.id)),
        "safety": {
            "credential_value_findings": 0,
            "raw_message_text_included": False,
            "direct_customer_identifiers_included": False,
            "full_channel_payloads_included": False,
            "local_export_only": True,
        },
        "warnings": warnings,
    }
    bundle["safety"]["credential_value_findings"] = _count_credential_value_findings(bundle)
    if bundle["safety"]["credential_value_findings"]:
        bundle["health"]["status"] = "needs_review"
        bundle["warnings"].append("诊断包安全扫描发现疑似凭据值，请先人工复核再对外发送。")
    return bundle


def build_diagnostic_upload_package(
    db: Session,
    *,
    tenant: Tenant,
    generated_by_user_id: int,
    authorization_note: str = "",
    contact_name: str = "",
    support_ticket: str = "",
) -> dict[str, Any]:
    generated_at = utc_now()
    diagnostic_bundle = build_diagnostic_bundle(db, tenant=tenant, generated_by_user_id=generated_by_user_id)
    diagnostic_digest = _stable_json_sha256(diagnostic_bundle)
    upload_allowed = diagnostic_bundle["safety"]["credential_value_findings"] == 0
    upload_status = "ready_for_manual_transfer" if upload_allowed else "needs_review"
    authorization = {
        "authorized_by_user_id": generated_by_user_id,
        "authorization_note": (authorization_note or "客户管理员确认授权上传本次脱敏诊断包。").strip(),
        "contact_name": contact_name.strip(),
        "support_ticket": support_ticket.strip(),
        "authorized_at": generated_at,
        "expires_after_hours": 24,
        "scope": "脱敏诊断包、运行摘要、知识/质量/渠道/队列计数、近期错误摘要",
    }
    package = {
        "schema_version": UPLOAD_PACKAGE_SCHEMA_VERSION,
        "filename": _diagnostic_upload_filename(tenant.slug, generated_at),
        "generated_at": generated_at,
        "tenant": {
            "id": tenant.id,
            "name": tenant.name,
            "slug": tenant.slug,
        },
        "authorization": authorization,
        "upload_manifest": {
            "transfer_mode": "manual_transfer_package",
            "upload_status": upload_status,
            "diagnostic_bundle_filename": diagnostic_bundle["filename"],
            "diagnostic_bundle_sha256": diagnostic_digest,
            "recommended_destination": "我方售后工单或客户确认的安全传输通道",
            "actual_external_upload_performed": False,
            "network_request_performed": False,
        },
        "diagnostic_bundle": diagnostic_bundle,
        "safety": {
            "external_upload_performed": False,
            "network_request_performed": False,
            "manual_transfer_required": True,
            "customer_authorization_recorded": True,
            "raw_message_text_included": False,
            "direct_customer_identifiers_included": False,
            "full_channel_payloads_included": False,
            "credential_value_findings": diagnostic_bundle["safety"]["credential_value_findings"],
            "upload_allowed": upload_allowed,
        },
        "warnings": list(diagnostic_bundle["warnings"]),
    }
    add_audit_event(
        db,
        tenant_id=tenant.id,
        actor_id=generated_by_user_id,
        action="diagnostic_bundle.upload_package_created",
        resource_type="diagnostic_bundle",
        resource_id=diagnostic_bundle["filename"],
        payload={
            "schema_version": UPLOAD_PACKAGE_SCHEMA_VERSION,
            "package_filename": package["filename"],
            "diagnostic_bundle_sha256": diagnostic_digest,
            "transfer_mode": "manual_transfer_package",
            "external_upload_performed": False,
            "support_ticket": support_ticket.strip(),
        },
    )
    return package


def create_diagnostic_intake_record(
    db: Session,
    *,
    tenant: Tenant,
    upload_package: dict[str, Any],
    received_by_user_id: int,
    source_channel: str = "manual_transfer",
    processing_note: str = "",
) -> dict[str, Any]:
    now = utc_now()
    validation = validate_diagnostic_upload_package(upload_package)
    package_sha256 = _stable_json_sha256(upload_package)
    package_size_bytes = len(json.dumps(upload_package, ensure_ascii=False, default=str).encode("utf-8"))
    stored_package_payload = _diagnostic_upload_package_for_storage(
        upload_package,
        validation=validation,
        package_sha256=package_sha256,
        package_size_bytes=package_size_bytes,
    )
    bundle = upload_package.get("diagnostic_bundle") if isinstance(upload_package, dict) else {}
    manifest = upload_package.get("upload_manifest") if isinstance(upload_package, dict) else {}
    authorization = upload_package.get("authorization") if isinstance(upload_package, dict) else {}
    tenant_payload = upload_package.get("tenant") if isinstance(upload_package, dict) else {}
    package_filename = (
        str(upload_package.get("filename") or "unknown-diagnostic-upload.json")
        if isinstance(upload_package, dict)
        else "unknown-diagnostic-upload.json"
    )
    bundle_filename = (
        str(bundle.get("filename") or manifest.get("diagnostic_bundle_filename") or "")
        if isinstance(bundle, dict) and isinstance(manifest, dict)
        else ""
    )
    bundle_sha256 = str(manifest.get("diagnostic_bundle_sha256") or "") if isinstance(manifest, dict) else ""
    intake_id = _diagnostic_intake_id(str(tenant_payload.get("slug") or tenant.slug), now, package_sha256)
    status = "received" if validation["accepted"] else "rejected"
    safety = {
        "customer_authorization_recorded": bool(validation["customer_authorization_recorded"]),
        "credential_value_findings": validation["credential_value_findings"],
        "raw_message_text_included": bool(validation["raw_message_text_included"]),
        "direct_customer_identifiers_included": bool(validation["direct_customer_identifiers_included"]),
        "full_channel_payloads_included": bool(validation["full_channel_payloads_included"]),
        "remote_control_performed": False,
        "customer_environment_write_performed": False,
        "automatic_upload_performed": False,
        "manual_transfer_package_received": True,
        "package_size_bytes": package_size_bytes,
        "package_max_depth": validation["package_max_depth"],
        "payload_redacted_for_storage": True,
    }
    record = DiagnosticIntakeRecord(
        tenant_id=tenant.id,
        intake_id=intake_id,
        status=status,
        validation_status="passed" if validation["accepted"] else "rejected",
        package_filename=package_filename,
        diagnostic_bundle_filename=bundle_filename,
        package_sha256=package_sha256,
        diagnostic_bundle_sha256=bundle_sha256,
        package_size_bytes=package_size_bytes,
        source_channel=source_channel or "manual_transfer",
        rejection_reason=validation["rejection_reason"],
        processing_note=processing_note.strip(),
        authorization_summary={
            "authorized_by_user_id": authorization.get("authorized_by_user_id") if isinstance(authorization, dict) else None,
            "authorized_at": authorization.get("authorized_at") if isinstance(authorization, dict) else None,
            "support_ticket": redact_sensitive_text(str(authorization.get("support_ticket") or ""), limit=120)
            if isinstance(authorization, dict)
            else "",
            "scope": authorization.get("scope") if isinstance(authorization, dict) else "",
        },
        safety=safety,
        package_payload=stored_package_payload,
        received_by_id=received_by_user_id,
        handled_by_id=received_by_user_id if status == "rejected" else None,
        created_at=now,
        updated_at=now,
        handled_at=now if status == "rejected" else None,
    )
    db.add(record)
    db.flush()
    add_audit_event(
        db,
        tenant_id=tenant.id,
        actor_id=received_by_user_id,
        action="diagnostic_intake.received" if validation["accepted"] else "diagnostic_intake.rejected",
        resource_type="diagnostic_intake",
        resource_id=intake_id,
        payload={
            "schema_version": INTAKE_SCHEMA_VERSION,
            "intake_record_id": record.id,
            "status": record.status,
            "validation_status": record.validation_status,
            "package_filename": record.package_filename,
            "package_sha256": record.package_sha256,
            "diagnostic_bundle_sha256": record.diagnostic_bundle_sha256,
            "rejection_reason": record.rejection_reason,
            "remote_control_performed": False,
            "customer_environment_write_performed": False,
        },
    )
    return diagnostic_intake_record_to_read(record)


def validate_diagnostic_upload_package(upload_package: dict[str, Any]) -> dict[str, Any]:
    reasons: list[str] = []
    package_size_bytes = _json_size_bytes(upload_package)
    package_max_depth = _json_max_depth(upload_package)
    if not isinstance(upload_package, dict):
        reasons.append("上传内容不是 JSON 对象。")
        upload_package = {}
    if package_size_bytes > MAX_DIAGNOSTIC_UPLOAD_PACKAGE_BYTES:
        reasons.append(
            f"上传包超过大小上限 {MAX_DIAGNOSTIC_UPLOAD_PACKAGE_BYTES} 字节。"
        )
    if package_max_depth > MAX_DIAGNOSTIC_UPLOAD_PACKAGE_DEPTH:
        reasons.append(
            f"上传包嵌套深度超过上限 {MAX_DIAGNOSTIC_UPLOAD_PACKAGE_DEPTH}。"
        )
    unexpected_top_keys = sorted(set(upload_package) - ALLOWED_UPLOAD_PACKAGE_KEYS)
    if unexpected_top_keys:
        reasons.append("上传包包含不允许字段：" + "、".join(unexpected_top_keys[:8]))
    if upload_package.get("schema_version") != UPLOAD_PACKAGE_SCHEMA_VERSION:
        reasons.append("上传包版本不受支持。")

    authorization = upload_package.get("authorization")
    manifest = upload_package.get("upload_manifest")
    bundle = upload_package.get("diagnostic_bundle")
    safety = upload_package.get("safety")
    bundle_safety = bundle.get("safety") if isinstance(bundle, dict) else {}

    if not isinstance(authorization, dict) or not authorization.get("authorization_note"):
        reasons.append("缺少客户授权记录。")
    if not isinstance(manifest, dict):
        reasons.append("缺少上传清单。")
    if not isinstance(bundle, dict):
        reasons.append("缺少诊断包。")
    else:
        unexpected_bundle_keys = sorted(set(bundle) - ALLOWED_DIAGNOSTIC_BUNDLE_KEYS)
        if unexpected_bundle_keys:
            reasons.append("诊断包包含不允许字段：" + "、".join(unexpected_bundle_keys[:8]))
    if not isinstance(safety, dict):
        reasons.append("缺少安全声明。")

    credential_value_findings = _count_credential_value_findings(upload_package)
    if credential_value_findings:
        reasons.append("安全扫描发现疑似凭据值。")
    customer_authorization_recorded = bool(isinstance(safety, dict) and safety.get("customer_authorization_recorded"))
    if not customer_authorization_recorded:
        reasons.append("安全声明未记录客户主动授权。")
    upload_allowed = bool(isinstance(safety, dict) and safety.get("upload_allowed"))
    if not upload_allowed:
        reasons.append("授权上传包标记为不可上传。")
    raw_message_text_included = bool(
        (isinstance(safety, dict) and safety.get("raw_message_text_included"))
        or (isinstance(bundle_safety, dict) and bundle_safety.get("raw_message_text_included"))
    )
    direct_customer_identifiers_included = bool(
        (isinstance(safety, dict) and safety.get("direct_customer_identifiers_included"))
        or (isinstance(bundle_safety, dict) and bundle_safety.get("direct_customer_identifiers_included"))
    )
    full_channel_payloads_included = bool(
        (isinstance(safety, dict) and safety.get("full_channel_payloads_included"))
        or (isinstance(bundle_safety, dict) and bundle_safety.get("full_channel_payloads_included"))
    )
    if raw_message_text_included:
        reasons.append("安全声明显示包含原始聊天文本。")
    if direct_customer_identifiers_included:
        reasons.append("安全声明显示包含直接客户标识。")
    if full_channel_payloads_included:
        reasons.append("安全声明显示包含完整渠道 payload。")
    if isinstance(manifest, dict) and isinstance(bundle, dict):
        expected_digest = str(manifest.get("diagnostic_bundle_sha256") or "")
        actual_digest = _stable_json_sha256(bundle)
        if not expected_digest or expected_digest != actual_digest:
            reasons.append("诊断包 sha256 与上传清单不一致。")

    return {
        "accepted": len(reasons) == 0,
        "rejection_reason": "；".join(reasons),
        "credential_value_findings": credential_value_findings,
        "customer_authorization_recorded": customer_authorization_recorded,
        "raw_message_text_included": raw_message_text_included,
        "direct_customer_identifiers_included": direct_customer_identifiers_included,
        "full_channel_payloads_included": full_channel_payloads_included,
        "package_size_bytes": package_size_bytes,
        "package_max_depth": package_max_depth,
    }


def _json_size_bytes(value: Any) -> int:
    return len(json.dumps(value, ensure_ascii=False, default=str).encode("utf-8"))


def _json_max_depth(value: Any, depth: int = 0) -> int:
    if isinstance(value, dict):
        if not value:
            return depth + 1
        return max(_json_max_depth(item, depth + 1) for item in value.values())
    if isinstance(value, list):
        if not value:
            return depth + 1
        return max(_json_max_depth(item, depth + 1) for item in value)
    return depth + 1


def _diagnostic_upload_package_for_storage(
    upload_package: dict[str, Any],
    *,
    validation: dict[str, Any],
    package_sha256: str,
    package_size_bytes: int,
) -> dict[str, Any]:
    if validation["accepted"]:
        return _sanitize_diagnostic_storage_value(upload_package)
    package_filename = (
        str(upload_package.get("filename") or "unknown-diagnostic-upload.json")
        if isinstance(upload_package, dict)
        else "unknown-diagnostic-upload.json"
    )
    bundle = upload_package.get("diagnostic_bundle") if isinstance(upload_package, dict) else {}
    bundle_filename = str(bundle.get("filename") or "") if isinstance(bundle, dict) else ""
    manifest = upload_package.get("upload_manifest") if isinstance(upload_package, dict) else {}
    return {
        "schema_version": INTAKE_SCHEMA_VERSION,
        "storage_mode": "rejected_upload_summary_only",
        "original_schema_version": upload_package.get("schema_version") if isinstance(upload_package, dict) else None,
        "package_filename": redact_sensitive_text(package_filename, limit=160),
        "diagnostic_bundle_filename": redact_sensitive_text(bundle_filename, limit=160),
        "package_sha256": package_sha256,
        "package_size_bytes": package_size_bytes,
        "package_max_depth": validation.get("package_max_depth"),
        "diagnostic_bundle_sha256": (
            redact_sensitive_text(str(manifest.get("diagnostic_bundle_sha256") or ""), limit=100)
            if isinstance(manifest, dict)
            else ""
        ),
        "rejection_reason": validation["rejection_reason"],
        "safety": {
            "customer_authorization_recorded": bool(validation["customer_authorization_recorded"]),
            "credential_value_findings": int(validation["credential_value_findings"] or 0),
            "raw_message_text_included": bool(validation["raw_message_text_included"]),
            "direct_customer_identifiers_included": bool(validation["direct_customer_identifiers_included"]),
            "full_channel_payloads_included": bool(validation["full_channel_payloads_included"]),
            "payload_redacted_for_storage": True,
            "original_payload_not_persisted": True,
        },
    }


def _sanitize_diagnostic_storage_value(value: Any) -> Any:
    if isinstance(value, dict):
        sanitized: dict[str, Any] = {}
        for key, item in value.items():
            key_text = str(key)
            if _CREDENTIAL_WORD_RE.search(key_text):
                sanitized[key_text] = "<credential_redacted>"
            else:
                sanitized[key_text] = _sanitize_diagnostic_storage_value(item)
        return sanitized
    if isinstance(value, list):
        return [_sanitize_diagnostic_storage_value(item) for item in value[:500]]
    if isinstance(value, str):
        return redact_sensitive_text(value, limit=1800)
    return value


def list_diagnostic_intake_records(db: Session, *, tenant_id: int) -> dict[str, Any]:
    records = db.scalars(
        select(DiagnosticIntakeRecord)
        .where(DiagnosticIntakeRecord.tenant_id == tenant_id)
        .order_by(DiagnosticIntakeRecord.created_at.desc(), DiagnosticIntakeRecord.id.desc())
    ).all()
    return {
        "schema_version": INTAKE_SCHEMA_VERSION,
        "items": [diagnostic_intake_record_to_read(record) for record in records],
    }


def update_diagnostic_intake_record_status(
    db: Session,
    *,
    tenant_id: int,
    record_id: int,
    status: str,
    processing_note: str,
    handled_by_user_id: int,
) -> dict[str, Any]:
    normalized_status = (status or "").strip()
    if normalized_status not in ALLOWED_INTAKE_STATUSES:
        raise ValueError("unsupported diagnostic intake status")
    record = _get_diagnostic_intake_record(db, tenant_id=tenant_id, record_id=record_id)
    now = utc_now()
    record.status = normalized_status
    record.processing_note = processing_note.strip()
    record.updated_at = now
    if normalized_status in {"resolved", "rejected"}:
        record.handled_by_id = handled_by_user_id
        record.handled_at = now
    add_audit_event(
        db,
        tenant_id=tenant_id,
        actor_id=handled_by_user_id,
        action="diagnostic_intake.status_updated",
        resource_type="diagnostic_intake",
        resource_id=record.intake_id,
        payload={
            "schema_version": INTAKE_SCHEMA_VERSION,
            "status": record.status,
            "processing_note_present": bool(record.processing_note),
            "remote_control_performed": False,
            "customer_environment_write_performed": False,
        },
    )
    return diagnostic_intake_record_to_read(record)


def download_diagnostic_intake_record(db: Session, *, tenant_id: int, record_id: int) -> dict[str, Any]:
    record = _get_diagnostic_intake_record(db, tenant_id=tenant_id, record_id=record_id)
    serialized = json.dumps(record.package_payload, ensure_ascii=False, default=str, sort_keys=True, indent=2)
    body_sha256 = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
    return {
        "schema_version": INTAKE_SCHEMA_VERSION,
        "intake_id": record.intake_id,
        "filename": record.package_filename or f"{record.intake_id}.json",
        "content_type": "application/json",
        "body_encoding": "utf-8",
        "body": serialized,
        "body_sha256": body_sha256,
        "body_bytes": len(serialized.encode("utf-8")),
        "safety": {
            **(record.safety or {}),
            "remote_control_performed": False,
            "customer_environment_write_performed": False,
        },
    }


def create_diagnostic_remediation_request(
    db: Session,
    *,
    tenant_id: int,
    intake_record_id: int,
    created_by_user_id: int,
    request_type: str = "knowledge_or_strategy_update",
    title: str = "",
    summary: str = "",
    priority: str = "normal",
) -> dict[str, Any]:
    normalized_type = (request_type or "knowledge_or_strategy_update").strip()
    if normalized_type not in ALLOWED_REMEDIATION_TYPES:
        raise ValueError("unsupported diagnostic remediation request type")
    record = _get_diagnostic_intake_record(db, tenant_id=tenant_id, record_id=intake_record_id)
    if record.validation_status != "passed" or record.status == "rejected":
        raise ValueError("diagnostic intake record is rejected and cannot create remediation request")
    now = utc_now()
    request_id = _diagnostic_remediation_request_id(record.intake_id, now)
    recommended_actions = _build_remediation_actions(record)
    update_request_manifest = _build_remediation_manifest(record, normalized_type)
    safety = _build_remediation_safety()
    request = DiagnosticRemediationRequest(
        tenant_id=tenant_id,
        intake_record_id=record.id,
        request_id=request_id,
        request_type=normalized_type,
        status="draft",
        priority=(priority or "normal").strip() or "normal",
        title=(title or f"售后处理单：{record.package_filename}").strip()[:220],
        summary=(summary or _build_remediation_summary(record)).strip(),
        recommended_actions=recommended_actions,
        update_request_manifest=update_request_manifest,
        safety=safety,
        created_by_id=created_by_user_id,
        updated_by_id=created_by_user_id,
        created_at=now,
        updated_at=now,
    )
    db.add(request)
    db.flush()
    add_audit_event(
        db,
        tenant_id=tenant_id,
        actor_id=created_by_user_id,
        action="diagnostic_remediation.created",
        resource_type="diagnostic_remediation",
        resource_id=request.request_id,
        payload={
            "schema_version": REMEDIATION_SCHEMA_VERSION,
            "intake_record_id": record.id,
            "request_type": request.request_type,
            "status": request.status,
            "can_generate_signed_update_package_now": False,
            "remote_control_performed": False,
            "customer_environment_write_performed": False,
        },
    )
    return diagnostic_remediation_request_to_read(request)


def list_diagnostic_remediation_requests(db: Session, *, tenant_id: int) -> dict[str, Any]:
    requests = db.scalars(
        select(DiagnosticRemediationRequest)
        .where(DiagnosticRemediationRequest.tenant_id == tenant_id)
        .order_by(DiagnosticRemediationRequest.created_at.desc(), DiagnosticRemediationRequest.id.desc())
    ).all()
    return {
        "schema_version": REMEDIATION_SCHEMA_VERSION,
        "items": [diagnostic_remediation_request_to_read(request) for request in requests],
    }


def update_diagnostic_remediation_request_status(
    db: Session,
    *,
    tenant_id: int,
    request_id: int,
    status: str,
    summary: str,
    updated_by_user_id: int,
) -> dict[str, Any]:
    normalized_status = (status or "").strip()
    if normalized_status not in ALLOWED_REMEDIATION_STATUSES:
        raise ValueError("unsupported diagnostic remediation request status")
    request = _get_diagnostic_remediation_request(db, tenant_id=tenant_id, request_id=request_id)
    request.status = normalized_status
    if summary.strip():
        request.summary = summary.strip()
    request.updated_by_id = updated_by_user_id
    request.updated_at = utc_now()
    add_audit_event(
        db,
        tenant_id=tenant_id,
        actor_id=updated_by_user_id,
        action="diagnostic_remediation.status_updated",
        resource_type="diagnostic_remediation",
        resource_id=request.request_id,
        payload={
            "schema_version": REMEDIATION_SCHEMA_VERSION,
            "status": request.status,
            "summary_present": bool(request.summary),
            "remote_control_performed": False,
            "customer_environment_write_performed": False,
        },
    )
    return diagnostic_remediation_request_to_read(request)


def create_diagnostic_remediation_update_plan(
    db: Session,
    *,
    tenant_id: int,
    request_id: int,
    signed_update_package_id: int,
    updated_by_user_id: int,
    operator_note: str = "",
) -> dict[str, Any]:
    request = _get_diagnostic_remediation_request(db, tenant_id=tenant_id, request_id=request_id)
    package = _get_signed_update_package_for_tenant(
        db,
        tenant_id=tenant_id,
        signed_update_package_id=signed_update_package_id,
    )
    latest_backup = _latest_local_backup_record(db, tenant_id=tenant_id)
    now = utc_now()
    plan = _build_signed_update_control_plan(
        request=request,
        package=package,
        latest_backup=latest_backup,
        generated_at=now,
        operator_note=operator_note,
    )
    manifest = dict(request.update_request_manifest or {})
    manifest["signed_update_control_plan"] = plan
    manifest["can_apply_from_plan_now"] = False
    manifest["requires_local_backup_before_apply"] = True
    manifest["真实外发继续关闭"] = True
    request.update_request_manifest = manifest
    request.recommended_actions = _merge_remediation_actions(
        request.recommended_actions or [],
        [
            {
                "code": "link_signed_update_package",
                "label": "绑定签名更新包",
                "required": True,
                "status": "passed",
                "description": "处理单已经关联到签名更新中心的暂存包；计划刷新只读取包状态，不执行更新。",
            },
            {
                "code": "verify_local_backup_before_apply",
                "label": "应用前校验本地备份",
                "required": True,
                "status": "ready" if latest_backup is not None else "blocked",
                "description": "真实应用前必须有客户本地备份点，并完成完整性校验或人工复核。",
            },
            {
                "code": "apply_or_rehearse_signed_update_package",
                "label": "受控应用或演练更新包",
                "required": True,
                "status": "manual_only",
                "description": "知识包和策略包可由管理员在签名更新中心手动应用；程序包只允许生成演练计划。",
            },
            {
                "code": "rollback_if_needed",
                "label": "必要时执行回滚",
                "required": True,
                "status": "manual_only",
                "description": "已应用的知识包或策略包必须保留可回滚记录；计划接口不会自动回滚。",
            },
        ],
    )
    safety = dict(request.safety or {})
    safety.update(
        {
            "remote_control_performed": False,
            "customer_environment_write_performed": False,
            "automatic_update_performed": False,
            "silent_update_performed": False,
            "network_push_performed": False,
            "external_write_performed": False,
            "plan_generated_only": True,
            "signed_update_package_linked": True,
            "can_apply_now": False,
            "真实外发继续关闭": True,
        }
    )
    request.safety = safety
    request.status = "update_plan_prepared"
    request.updated_by_id = updated_by_user_id
    request.updated_at = now
    add_audit_event(
        db,
        tenant_id=tenant_id,
        actor_id=updated_by_user_id,
        action="diagnostic_remediation.signed_update_plan_created",
        resource_type="diagnostic_remediation",
        resource_id=request.request_id,
        payload={
            "schema_version": REMEDIATION_UPDATE_PLAN_SCHEMA_VERSION,
            "signed_update_package_id": package.id,
            "signed_update_package_status": package.status,
            "signed_update_package_type": package.package_type,
            "can_apply_from_plan_now": False,
            "automatic_update_performed": False,
            "remote_control_performed": False,
            "external_write_performed": False,
        },
    )
    return diagnostic_remediation_request_to_read(request)


def download_diagnostic_remediation_request(db: Session, *, tenant_id: int, request_id: int) -> dict[str, Any]:
    request = _get_diagnostic_remediation_request(db, tenant_id=tenant_id, request_id=request_id)
    body_payload = {
        "schema_version": REMEDIATION_SCHEMA_VERSION,
        "request_id": request.request_id,
        "request_type": request.request_type,
        "status": request.status,
        "priority": request.priority,
        "title": request.title,
        "summary": request.summary,
        "recommended_actions": request.recommended_actions or [],
        "update_request_manifest": request.update_request_manifest or {},
        "safety": {
            **(request.safety or {}),
            "remote_control_performed": False,
            "customer_environment_write_performed": False,
        },
    }
    serialized = json.dumps(body_payload, ensure_ascii=False, default=str, sort_keys=True, indent=2)
    body_sha256 = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
    return {
        "schema_version": REMEDIATION_SCHEMA_VERSION,
        "request_id": request.request_id,
        "filename": f"{request.request_id}.json",
        "content_type": "application/json",
        "body_encoding": "utf-8",
        "body": serialized,
        "body_sha256": body_sha256,
        "body_bytes": len(serialized.encode("utf-8")),
        "safety": body_payload["safety"],
    }


def diagnostic_intake_record_to_read(record: DiagnosticIntakeRecord) -> dict[str, Any]:
    return {
        "id": record.id,
        "tenant_id": record.tenant_id,
        "intake_id": record.intake_id,
        "status": record.status,
        "validation_status": record.validation_status,
        "package_filename": record.package_filename,
        "diagnostic_bundle_filename": record.diagnostic_bundle_filename,
        "package_sha256": record.package_sha256,
        "diagnostic_bundle_sha256": record.diagnostic_bundle_sha256,
        "package_size_bytes": record.package_size_bytes,
        "source_channel": record.source_channel,
        "rejection_reason": record.rejection_reason,
        "processing_note": record.processing_note,
        "authorization_summary": record.authorization_summary or {},
        "safety": record.safety or {},
        "received_by_id": record.received_by_id,
        "handled_by_id": record.handled_by_id,
        "created_at": record.created_at,
        "updated_at": record.updated_at,
        "handled_at": record.handled_at,
        "download_supported": bool(record.package_payload),
    }


def diagnostic_remediation_request_to_read(request: DiagnosticRemediationRequest) -> dict[str, Any]:
    return {
        "id": request.id,
        "tenant_id": request.tenant_id,
        "intake_record_id": request.intake_record_id,
        "request_id": request.request_id,
        "request_type": request.request_type,
        "status": request.status,
        "priority": request.priority,
        "title": request.title,
        "summary": request.summary,
        "recommended_actions": request.recommended_actions or [],
        "update_request_manifest": request.update_request_manifest or {},
        "safety": request.safety or {},
        "created_by_id": request.created_by_id,
        "updated_by_id": request.updated_by_id,
        "created_at": request.created_at,
        "updated_at": request.updated_at,
        "download_supported": True,
    }


def _get_diagnostic_intake_record(db: Session, *, tenant_id: int, record_id: int) -> DiagnosticIntakeRecord:
    record = db.get(DiagnosticIntakeRecord, record_id)
    if record is None or record.tenant_id != tenant_id:
        raise LookupError("diagnostic intake record not found")
    return record


def _get_diagnostic_remediation_request(
    db: Session, *, tenant_id: int, request_id: int
) -> DiagnosticRemediationRequest:
    request = db.get(DiagnosticRemediationRequest, request_id)
    if request is None or request.tenant_id != tenant_id:
        raise LookupError("diagnostic remediation request not found")
    return request


def _get_signed_update_package_for_tenant(
    db: Session, *, tenant_id: int, signed_update_package_id: int
) -> SignedUpdatePackage:
    package = db.get(SignedUpdatePackage, signed_update_package_id)
    if package is None or package.tenant_id != tenant_id:
        raise LookupError("signed update package not found")
    return package


def _latest_local_backup_record(db: Session, *, tenant_id: int) -> LocalBackupRecord | None:
    return db.scalars(
        select(LocalBackupRecord)
        .where(LocalBackupRecord.tenant_id == tenant_id)
        .order_by(LocalBackupRecord.created_at.desc(), LocalBackupRecord.id.desc())
        .limit(1)
    ).one_or_none()


def _build_signed_update_control_plan(
    *,
    request: DiagnosticRemediationRequest,
    package: SignedUpdatePackage,
    latest_backup: LocalBackupRecord | None,
    generated_at: datetime,
    operator_note: str,
) -> dict[str, Any]:
    preflight = package.preflight_result or {}
    backup_summary = _local_backup_summary(latest_backup)
    signed_update_summary = _signed_update_package_summary(package)
    return {
        "schema_version": REMEDIATION_UPDATE_PLAN_SCHEMA_VERSION,
        "generated_at": generated_at.isoformat(),
        "request_id": request.request_id,
        "intake_record_id": request.intake_record_id,
        "operator_note": redact_sensitive_text(operator_note or "客户管理员确认进入受控更新计划。", limit=260),
        "signed_update_package": signed_update_summary,
        "preflight_summary": _signed_update_preflight_summary(preflight),
        "local_backup": backup_summary,
        "lifecycle_steps": _signed_update_lifecycle_steps(package, backup_summary=backup_summary),
        "can_apply_from_plan_now": False,
        "can_rollback_from_plan_now": False,
        "plan_generated_only": True,
        "external_write_performed": False,
        "真实外发继续关闭": True,
        "safety": {
            "remote_control_performed": False,
            "customer_environment_write_performed": False,
            "automatic_update_performed": False,
            "silent_update_performed": False,
            "network_push_performed": False,
            "external_write_performed": False,
            "provider_call_performed": False,
            "program_execution_performed": False,
            "database_migration_performed": False,
            "can_apply_now": False,
            "can_apply_from_plan_now": False,
            "can_rollback_from_plan_now": False,
            "plan_generated_only": True,
            "program_package_apply_supported": False,
        },
        "operator_boundaries": [
            "本计划只绑定处理单和签名更新包状态，不自动应用更新。",
            "真实应用必须由客户管理员在签名更新中心手动确认。",
            "程序包仍只允许生成 dry-run 演练计划，不替换程序文件。",
            "真实平台外发继续关闭；本计划不触达微信、抖音、淘宝、京东或拼多多。",
        ],
    }


def _signed_update_package_summary(package: SignedUpdatePackage) -> dict[str, Any]:
    return {
        "id": package.id,
        "package_id": package.package_id,
        "package_name": package.package_name,
        "package_type": package.package_type,
        "package_version": package.package_version,
        "status": package.status,
        "current_app_version": package.current_app_version,
        "package_digest_sha256": package.package_digest_sha256,
        "backup_required": package.backup_required,
        "backup_created": package.backup_created,
        "can_apply_now": False,
        "staged_at": package.staged_at.isoformat() if package.staged_at else None,
        "applied_at": package.applied_at.isoformat() if package.applied_at else None,
        "error_message": redact_sensitive_text(package.error_message or "", limit=160),
    }


def _signed_update_preflight_summary(preflight: dict[str, Any]) -> dict[str, Any]:
    signature_status = preflight.get("signature_status") if isinstance(preflight, dict) else {}
    checksum_status = preflight.get("checksum_status") if isinstance(preflight, dict) else {}
    compatibility = preflight.get("compatibility") if isinstance(preflight, dict) else {}
    return {
        "signature_verified": bool(_safe_mapping_bool(signature_status, "verified")),
        "payload_digest_match": bool(_safe_mapping_bool(checksum_status, "payload_digest_match")),
        "checksums_payload_match": bool(_safe_mapping_bool(checksum_status, "checksums_payload_match")),
        "compatible": bool(_safe_mapping_bool(compatibility, "compatible")),
        "product_match": bool(_safe_mapping_bool(compatibility, "product_match")),
        "can_stage": bool(preflight.get("can_stage")) if isinstance(preflight, dict) else False,
        "can_apply_now": False,
        "errors": list(preflight.get("errors") or []) if isinstance(preflight, dict) else [],
        "warnings": list(preflight.get("warnings") or []) if isinstance(preflight, dict) else [],
    }


def _safe_mapping_bool(value: Any, key: str) -> bool:
    return bool(value.get(key)) if isinstance(value, dict) else False


def _local_backup_summary(backup: LocalBackupRecord | None) -> dict[str, Any]:
    if backup is None:
        return {
            "required_before_apply": True,
            "latest_backup_found": False,
            "status": "missing",
            "absolute_path_exposed": False,
        }
    return {
        "required_before_apply": True,
        "latest_backup_found": True,
        "id": backup.id,
        "backup_id": backup.backup_id,
        "status": backup.status,
        "backup_type": backup.backup_type,
        "file_name": backup.file_name,
        "file_size_bytes": backup.file_size_bytes,
        "sha256": backup.sha256,
        "source_database_label": backup.source_database_label,
        "restore_mode": backup.restore_mode,
        "created_at": backup.created_at.isoformat() if backup.created_at else None,
        "verified_at": backup.verified_at.isoformat() if backup.verified_at else None,
        "absolute_path_exposed": False,
    }


def _signed_update_lifecycle_steps(
    package: SignedUpdatePackage, *, backup_summary: dict[str, Any]
) -> list[dict[str, Any]]:
    signature_ok = _safe_mapping_bool((package.preflight_result or {}).get("signature_status"), "verified")
    checksum_ok = _safe_mapping_bool((package.preflight_result or {}).get("checksum_status"), "payload_digest_match")
    compatible = _safe_mapping_bool((package.preflight_result or {}).get("compatibility"), "compatible")
    preflight_passed = signature_ok and checksum_ok and compatible
    stage_passed = package.status in {"staged", "applied", "rolled_back"}
    backup_ready = package.backup_created or backup_summary.get("status") in {"created", "verified"}
    apply_status = "blocked"
    if package.package_type == "program":
        apply_status = "dry_run_only"
    elif package.status in {"applied", "rolled_back"}:
        apply_status = "passed"
    elif package.status == "staged" and preflight_passed:
        apply_status = "ready"
    rollback_status = "blocked"
    if package.package_type == "program":
        rollback_status = "dry_run_only"
    elif package.status == "rolled_back":
        rollback_status = "passed"
    elif package.status == "applied":
        rollback_status = "ready"
    elif package.status == "staged":
        rollback_status = "planned"
    return [
        {
            "id": "review_diagnostic",
            "label": "复核诊断处理单",
            "status": "passed",
            "manual_required": True,
        },
        {
            "id": "preflight",
            "label": "校验签名、摘要和版本兼容",
            "status": "passed" if preflight_passed else "blocked",
            "manual_required": False,
        },
        {
            "id": "stage",
            "label": "暂存签名更新包",
            "status": "passed" if stage_passed else "blocked",
            "manual_required": False,
        },
        {
            "id": "local_backup",
            "label": "确认本地备份点",
            "status": "passed" if package.backup_created else ("ready" if backup_ready else "blocked"),
            "manual_required": True,
        },
        {
            "id": "apply",
            "label": "管理员手动应用更新",
            "status": apply_status,
            "manual_required": True,
            "can_execute_from_this_plan": False,
        },
        {
            "id": "rollback",
            "label": "必要时管理员手动回滚",
            "status": rollback_status,
            "manual_required": True,
            "can_execute_from_this_plan": False,
        },
        {
            "id": "quality_regression",
            "label": "更新后质量回归验证",
            "status": "planned",
            "manual_required": True,
        },
    ]


def _merge_remediation_actions(
    current_actions: list[dict[str, Any]], new_actions: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    order: list[str] = []
    for action in [*current_actions, *new_actions]:
        code = str(action.get("code") or "").strip()
        if not code:
            continue
        if code not in merged:
            order.append(code)
        merged[code] = action
    return [merged[code] for code in order]


def _build_remediation_summary(record: DiagnosticIntakeRecord) -> str:
    bundle = record.package_payload.get("diagnostic_bundle") if isinstance(record.package_payload, dict) else {}
    counts = bundle.get("counts") if isinstance(bundle, dict) else {}
    knowledge = bundle.get("knowledge") if isinstance(bundle, dict) else {}
    quality = bundle.get("quality") if isinstance(bundle, dict) else {}
    return (
        "基于客户主动授权上传的脱敏诊断包生成处理单。"
        f"当前知识对象约 {int(counts.get('business_objects') or 0)} 个，"
        f"知识文档约 {int(counts.get('knowledge_documents') or 0)} 份，"
        f"评测集约 {int(counts.get('knowledge_evaluation_sets') or 0)} 个；"
        f"知识摘要状态：{redact_sensitive_text(str(knowledge.get('status') or '未提供'), limit=80)}；"
        f"质量摘要状态：{redact_sensitive_text(str(quality.get('status') or '未提供'), limit=80)}。"
    )


def _build_remediation_actions(record: DiagnosticIntakeRecord) -> list[dict[str, Any]]:
    bundle = record.package_payload.get("diagnostic_bundle") if isinstance(record.package_payload, dict) else {}
    recent_errors = bundle.get("recent_errors") if isinstance(bundle, dict) else []
    quality = bundle.get("quality") if isinstance(bundle, dict) else {}
    actions: list[dict[str, Any]] = [
        {
            "code": "review_diagnostic_summary",
            "label": "复核诊断摘要",
            "required": True,
            "reason": "更新前必须确认诊断包脱敏、授权和摘要均通过。",
        },
        {
            "code": "prepare_local_backup",
            "label": "客户本地先创建备份点",
            "required": True,
            "reason": "任何知识包、策略包或程序包应用前都必须先有可校验备份。",
        },
        {
            "code": "run_preflight_before_apply",
            "label": "更新包先预检再暂存",
            "required": True,
            "reason": "签名、租户、版本和兼容性未通过前不能应用。",
        },
    ]
    if isinstance(recent_errors, list) and recent_errors:
        actions.append(
            {
                "code": "triage_recent_errors",
                "label": "排查近期错误摘要",
                "required": False,
                "reason": f"诊断包提供 {len(recent_errors)} 条近期错误摘要，需要判断是否关联知识或策略更新。",
            }
        )
    if isinstance(quality, dict) and quality:
        actions.append(
            {
                "code": "run_quality_regression",
                "label": "更新后执行质量回归",
                "required": True,
                "reason": "处理单只能生成更新建议，最终是否改善必须用题库和人工标签复验。",
            }
        )
    actions.append(
        {
            "code": "customer_admin_confirmation",
            "label": "客户管理员确认后再应用",
            "required": True,
            "reason": "系统不做静默更新，不远程替客户改环境。",
        }
    )
    return actions


def _build_remediation_manifest(record: DiagnosticIntakeRecord, request_type: str) -> dict[str, Any]:
    return {
        "source_intake_id": record.intake_id,
        "source_package_sha256": record.package_sha256,
        "source_diagnostic_bundle_sha256": record.diagnostic_bundle_sha256,
        "request_type": request_type,
        "supported_next_packages": ["knowledge", "strategy", "program_dry_run"],
        "can_generate_signed_update_package_now": False,
        "requires_human_review": True,
        "requires_customer_admin_confirmation": True,
        "requires_local_backup_before_apply": True,
        "requires_preflight_before_stage": True,
        "rollback_required_after_apply_failure": True,
    }


def _build_remediation_safety() -> dict[str, Any]:
    return {
        "remote_control_performed": False,
        "customer_environment_write_performed": False,
        "automatic_update_performed": False,
        "silent_update_performed": False,
        "network_push_performed": False,
        "can_apply_now": False,
        "manual_transfer_required": True,
        "requires_customer_admin_confirmation": True,
    }


def redact_sensitive_text(value: str, *, limit: int = 260) -> str:
    text_value = str(value or "")
    text_value = _BEARER_VALUE_RE.sub("<credential_redacted>", text_value)
    text_value = _COMMON_KEY_VALUE_RE.sub("<credential_redacted>", text_value)
    text_value = _CREDENTIAL_KV_RE.sub("<credential_redacted>", text_value)
    text_value = _CREDENTIAL_WORD_RE.sub("credential", text_value)
    text_value = _EMAIL_RE.sub("<email_redacted>", text_value)
    text_value = _PHONE_RE.sub("<phone_redacted>", text_value)
    text_value = _LONG_VALUE_RE.sub("<value_redacted>", text_value)
    if len(text_value) > limit:
        return text_value[: limit - 1].rstrip() + "…"
    return text_value


def _diagnostic_filename(slug: str, generated_at: datetime) -> str:
    safe_slug = re.sub(r"[^a-zA-Z0-9-]+", "-", slug).strip("-") or "tenant"
    stamp = generated_at.strftime("%Y%m%d-%H%M%S")
    return f"wanfa-diagnostic-{safe_slug}-{stamp}.json"


def _diagnostic_upload_filename(slug: str, generated_at: datetime) -> str:
    safe_slug = re.sub(r"[^a-zA-Z0-9-]+", "-", slug).strip("-") or "tenant"
    stamp = generated_at.strftime("%Y%m%d-%H%M%S")
    return f"wanfa-diagnostic-upload-{safe_slug}-{stamp}.json"


def _diagnostic_intake_id(slug: str, received_at: datetime, package_sha256: str) -> str:
    safe_slug = re.sub(r"[^a-zA-Z0-9-]+", "-", slug).strip("-") or "tenant"
    stamp = received_at.strftime("%Y%m%d-%H%M%S")
    return f"diag-intake-{safe_slug}-{stamp}-{package_sha256[:8]}"


def _diagnostic_remediation_request_id(intake_id: str, created_at: datetime) -> str:
    stamp = created_at.strftime("%Y%m%d-%H%M%S")
    digest = hashlib.sha256(f"{intake_id}:{stamp}".encode("utf-8")).hexdigest()[:8]
    return f"diag-remediation-{stamp}-{digest}"


def _stable_json_sha256(value: dict[str, Any]) -> str:
    serialized = json.dumps(value, ensure_ascii=False, default=_json_digest_default, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _json_digest_default(value: Any) -> str:
    if isinstance(value, datetime):
        return value.isoformat().replace("+00:00", "Z")
    return str(value)


def _count_credential_value_findings(bundle: dict[str, Any]) -> int:
    serialized = json.dumps(bundle, ensure_ascii=False, default=str)
    return len(_CREDENTIAL_VALUE_SCAN_RE.findall(serialized))


def _collect_runtime(db: Session, settings) -> dict[str, Any]:
    parsed_db = urlparse(settings.database_url)
    parsed_redis = urlparse(settings.redis_url)
    return {
        "app_name": settings.app_name,
        "app_version": "0.1.0",
        "env": settings.env,
        "deploy_mode": "local_app_first_slice",
        "database_engine": parsed_db.scheme.split("+", 1)[0] or "unknown",
        "database_migration": _migration_version(db),
        "redis_configured": bool(parsed_redis.scheme and parsed_redis.hostname),
        "model_provider_configured": {
            "bailian": bool(settings.bailian_api_key),
            "deepseek": bool(settings.deepseek_api_key),
        },
        "knowledge_retrieval": {
            "embedding_provider": settings.knowledge_embedding_provider,
            "embedding_model": redact_sensitive_text(settings.knowledge_embedding_model),
            "embedding_dimensions": settings.knowledge_embedding_dimensions,
            "vector_store": settings.knowledge_vector_store,
            "reranker": settings.knowledge_reranker,
        },
        "outbound_write_enabled": settings.outbox_external_write_enabled,
        "trusted_inbound_worker_enabled": settings.trusted_inbound_worker_enabled,
    }


def _migration_version(db: Session) -> str:
    try:
        value = db.execute(text("select version_num from alembic_version limit 1")).scalar()
    except SQLAlchemyError:
        return "unknown"
    return str(value or "unknown")


def _collect_counts(db: Session, tenant_id: int) -> dict[str, int]:
    models = {
        "users": User,
        "contacts": Contact,
        "channels": Channel,
        "channel_accounts": ChannelAccount,
        "channel_connectors": ChannelConnector,
        "conversations": Conversation,
        "messages": Message,
        "reply_decisions": ReplyDecision,
        "human_review_tasks": HumanReviewTask,
        "support_tickets": SupportTicket,
        "sales_leads": SalesLead,
        "outbox_drafts": OutboxDraft,
        "outbox_delivery_jobs": OutboxDeliveryJob,
        "delivery_receipts": ChannelDeliveryReceipt,
        "delivery_failure_reviews": DeliveryFailureReview,
        "knowledge_cards": KnowledgeCard,
        "business_objects": BusinessObject,
        "object_knowledge_cards": ObjectKnowledgeCard,
        "knowledge_documents": KnowledgeDocument,
        "knowledge_document_chunks": KnowledgeDocumentChunk,
        "knowledge_publications": KnowledgeDocumentPublication,
        "knowledge_gaps": KnowledgeGapItem,
        "knowledge_evaluation_sets": KnowledgeEvaluationSet,
        "knowledge_evaluation_cases": KnowledgeEvaluationCase,
        "knowledge_evaluation_runs": KnowledgeEvaluationRun,
        "workflow_runs": WorkflowRun,
        "worker_heartbeats": WorkerHeartbeat,
    }
    return {name: _count_model(db, model, tenant_id) for name, model in models.items()}


def _collect_knowledge(db: Session, tenant_id: int) -> dict[str, Any]:
    latest_publication = db.scalar(
        select(KnowledgeDocumentPublication)
        .where(KnowledgeDocumentPublication.tenant_id == tenant_id)
        .order_by(KnowledgeDocumentPublication.created_at.desc())
        .limit(1)
    )
    latest_import = db.scalar(
        select(KnowledgeImportBatch)
        .where(KnowledgeImportBatch.tenant_id == tenant_id)
        .order_by(KnowledgeImportBatch.created_at.desc())
        .limit(1)
    )
    return {
        "cards": {
            "total": _count_model(db, KnowledgeCard, tenant_id),
            "by_status": _group_count(db, KnowledgeCard, tenant_id, KnowledgeCard.status),
        },
        "business_objects": {
            "total": _count_model(db, BusinessObject, tenant_id),
            "by_type": _group_count(db, BusinessObject, tenant_id, BusinessObject.type),
            "object_cards_by_status": _group_count(db, ObjectKnowledgeCard, tenant_id, ObjectKnowledgeCard.status),
        },
        "documents": {
            "total": _count_model(db, KnowledgeDocument, tenant_id),
            "chunks": _count_model(db, KnowledgeDocumentChunk, tenant_id),
            "by_status": _group_count(db, KnowledgeDocument, tenant_id, KnowledgeDocument.status),
            "by_ingestion": _group_count(db, KnowledgeDocument, tenant_id, KnowledgeDocument.ingestion_status),
        },
        "gaps": {
            "total": _count_model(db, KnowledgeGapItem, tenant_id),
            "by_status": _group_count(db, KnowledgeGapItem, tenant_id, KnowledgeGapItem.status),
            "by_severity": _group_count(db, KnowledgeGapItem, tenant_id, KnowledgeGapItem.severity),
        },
        "latest_publication": _publication_summary(latest_publication),
        "latest_import_batch": _import_batch_summary(latest_import),
        "raw_text_included": False,
    }


def _collect_quality(db: Session, tenant_id: int) -> dict[str, Any]:
    latest_run = db.scalar(
        select(KnowledgeEvaluationRun)
        .where(KnowledgeEvaluationRun.tenant_id == tenant_id)
        .order_by(KnowledgeEvaluationRun.created_at.desc())
        .limit(1)
    )
    if latest_run is None:
        latest_summary = None
    else:
        latest_summary = {
            "id": latest_run.id,
            "run_mode": latest_run.run_mode,
            "retrieval_mode": latest_run.retrieval_mode,
            "vector_engine": latest_run.vector_engine,
            "total_cases": latest_run.total_cases,
            "answered_cases": latest_run.answered_cases,
            "no_hit_cases": latest_run.no_hit_cases,
            "passed_cases": latest_run.passed_cases,
            "failed_cases": latest_run.failed_cases,
            "needs_review_cases": latest_run.needs_review_cases,
            "hit_rate": latest_run.hit_rate,
            "citation_coverage": latest_run.citation_coverage,
            "expected_term_coverage": latest_run.expected_term_coverage,
            "average_confidence": latest_run.average_confidence,
            "unsupported_answer_rate": latest_run.unsupported_answer_rate,
            "created_at": latest_run.created_at,
        }
    return {
        "sets_by_status": _group_count(db, KnowledgeEvaluationSet, tenant_id, KnowledgeEvaluationSet.status),
        "runs_total": _count_model(db, KnowledgeEvaluationRun, tenant_id),
        "latest_evaluation": latest_summary,
        "case_questions_included": False,
        "case_result_payloads_included": False,
    }


def _collect_channels(db: Session, tenant_id: int) -> dict[str, Any]:
    return {
        "channels_by_type": _group_count(db, Channel, tenant_id, Channel.type),
        "channels_by_status": _group_count(db, Channel, tenant_id, Channel.status),
        "channels_by_reply_mode": _group_count(db, Channel, tenant_id, Channel.reply_mode),
        "accounts_by_provider": _group_count(db, ChannelAccount, tenant_id, ChannelAccount.provider),
        "accounts_by_platform": _group_count(db, ChannelAccount, tenant_id, ChannelAccount.platform),
        "accounts_by_access": _group_count(db, ChannelAccount, tenant_id, ChannelAccount.access_status),
        "accounts_by_reply_mode": _group_count(db, ChannelAccount, tenant_id, ChannelAccount.reply_mode),
        "connectors_by_provider": _group_count(db, ChannelConnector, tenant_id, ChannelConnector.provider),
        "connectors_by_mode": _group_count(db, ChannelConnector, tenant_id, ChannelConnector.mode),
        "connectors_by_status": _group_count(db, ChannelConnector, tenant_id, ChannelConnector.status),
        "external_write_enabled_count": int(
            db.scalar(
                select(func.count(ChannelConnector.id)).where(
                    ChannelConnector.tenant_id == tenant_id,
                    ChannelConnector.external_write_enabled.is_(True),
                )
            )
            or 0
        ),
        "external_account_identifiers_included": False,
        "channel_payloads_included": False,
    }


def _collect_queues(db: Session, tenant_id: int) -> dict[str, Any]:
    return {
        "trusted_inbound_jobs_by_status": _group_count(db, TrustedInboundMessageJob, tenant_id, TrustedInboundMessageJob.status),
        "outbox_drafts_by_status": _group_count(db, OutboxDraft, tenant_id, OutboxDraft.status),
        "outbox_delivery_jobs_by_status": _group_count(db, OutboxDeliveryJob, tenant_id, OutboxDeliveryJob.status),
        "delivery_failure_reviews_by_status": _group_count(db, DeliveryFailureReview, tenant_id, DeliveryFailureReview.status),
        "external_write_requested_jobs": int(
            db.scalar(
                select(func.count(OutboxDeliveryJob.id)).where(
                    OutboxDeliveryJob.tenant_id == tenant_id,
                    OutboxDeliveryJob.external_write_requested.is_(True),
                )
            )
            or 0
        ),
        "external_write_permitted_jobs": int(
            db.scalar(
                select(func.count(OutboxDeliveryJob.id)).where(
                    OutboxDeliveryJob.tenant_id == tenant_id,
                    OutboxDeliveryJob.external_write_permitted.is_(True),
                )
            )
            or 0
        ),
        "draft_reply_text_included": False,
        "provider_payloads_included": False,
    }


def _collect_workers(db: Session, tenant_id: int) -> dict[str, Any]:
    heartbeats = list(
        db.scalars(
            select(WorkerHeartbeat)
            .where(WorkerHeartbeat.tenant_id == tenant_id)
            .order_by(WorkerHeartbeat.updated_at.desc())
            .limit(12)
        ).all()
    )
    return {
        "total": _count_model(db, WorkerHeartbeat, tenant_id),
        "by_type": _group_count(db, WorkerHeartbeat, tenant_id, WorkerHeartbeat.worker_type),
        "by_status": _group_count(db, WorkerHeartbeat, tenant_id, WorkerHeartbeat.status),
        "recent": [
            {
                "worker_type": item.worker_type,
                "status": item.status,
                "last_run_mode": item.last_run_mode,
                "loops_completed": item.loops_completed,
                "last_heartbeat_at": item.last_heartbeat_at,
                "updated_at": item.updated_at,
                "last_error": redact_sensitive_text(item.last_error),
            }
            for item in heartbeats
        ],
    }


def _collect_recent_errors(db: Session, tenant_id: int) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    errors.extend(
        _error_rows(
            db,
            tenant_id,
            WorkerHeartbeat,
            WorkerHeartbeat.last_error,
            "worker_heartbeat",
            status_column=WorkerHeartbeat.status,
            created_column=WorkerHeartbeat.updated_at,
        )
    )
    errors.extend(
        _error_rows(
            db,
            tenant_id,
            OutboxDeliveryJob,
            OutboxDeliveryJob.last_error,
            "outbox_delivery_job",
            status_column=OutboxDeliveryJob.status,
            created_column=OutboxDeliveryJob.updated_at,
        )
    )
    errors.extend(
        _error_rows(
            db,
            tenant_id,
            OutboxSendAttempt,
            OutboxSendAttempt.error_message,
            "outbox_send_attempt",
            status_column=OutboxSendAttempt.status,
            created_column=OutboxSendAttempt.started_at,
        )
    )
    errors.extend(
        _error_rows(
            db,
            tenant_id,
            TrustedInboundMessageJob,
            TrustedInboundMessageJob.last_error,
            "trusted_inbound_message_job",
            status_column=TrustedInboundMessageJob.status,
            created_column=TrustedInboundMessageJob.updated_at,
        )
    )
    errors.extend(
        _error_rows(
            db,
            tenant_id,
            TrustedInboundWorkerRunRecord,
            TrustedInboundWorkerRunRecord.error_message,
            "trusted_inbound_worker_run",
            status_column=TrustedInboundWorkerRunRecord.status,
            created_column=TrustedInboundWorkerRunRecord.started_at,
        )
    )
    errors.extend(
        _error_rows(
            db,
            tenant_id,
            KnowledgeEmbeddingProviderSmokeRun,
            KnowledgeEmbeddingProviderSmokeRun.error_message,
            "knowledge_embedding_smoke_run",
            status_column=KnowledgeEmbeddingProviderSmokeRun.status,
            created_column=KnowledgeEmbeddingProviderSmokeRun.created_at,
        )
    )
    return sorted(errors, key=lambda item: item["created_at"] or "", reverse=True)[:20]


def _collect_recent_changes(db: Session, tenant_id: int) -> list[dict[str, Any]]:
    events = list(
        db.scalars(
            select(AuditEvent)
            .where(AuditEvent.tenant_id == tenant_id)
            .order_by(AuditEvent.created_at.desc())
            .limit(20)
        ).all()
    )
    return [
        {
            "action": event.action,
            "resource_type": event.resource_type,
            "created_at": event.created_at,
        }
        for event in events
    ]


def _error_rows(
    db: Session,
    tenant_id: int,
    model,
    error_column,
    source: str,
    *,
    status_column,
    created_column,
) -> list[dict[str, Any]]:
    rows = list(
        db.execute(
            select(model.id, status_column, error_column, created_column)
            .where(model.tenant_id == tenant_id, error_column != "")
            .order_by(created_column.desc())
            .limit(6)
        ).all()
    )
    return [
        {
            "source": source,
            "record_id": row[0],
            "status": row[1],
            "message": redact_sensitive_text(row[2]),
            "created_at": row[3],
        }
        for row in rows
    ]


def _publication_summary(publication: KnowledgeDocumentPublication | None) -> dict[str, Any] | None:
    if publication is None:
        return None
    return {
        "id": publication.id,
        "document_id": publication.document_id,
        "publication_type": publication.publication_type,
        "status": publication.status,
        "from_status": publication.from_status,
        "to_status": publication.to_status,
        "blocking_reason_count": len(publication.blocking_reasons or []),
        "advisory_reason_count": len(publication.advisory_reasons or []),
        "external_write_performed": publication.external_write_performed,
        "model_call_performed": publication.model_call_performed,
        "created_at": publication.created_at,
    }


def _import_batch_summary(batch: KnowledgeImportBatch | None) -> dict[str, Any] | None:
    if batch is None:
        return None
    return {
        "id": batch.id,
        "object_type": batch.object_type,
        "row_count": batch.row_count,
        "valid_count": batch.valid_count,
        "error_count": batch.error_count,
        "status": batch.status,
        "created_at": batch.created_at,
    }


def _count_model(db: Session, model, tenant_id: int) -> int:
    if model is Message:
        return int(
            db.scalar(
                select(func.count(Message.id))
                .join(Conversation, Conversation.id == Message.conversation_id)
                .where(Conversation.tenant_id == tenant_id)
            )
            or 0
        )
    return int(db.scalar(select(func.count(model.id)).where(model.tenant_id == tenant_id)) or 0)


def _group_count(db: Session, model, tenant_id: int, column) -> dict[str, int]:
    rows = db.execute(
        select(column, func.count(model.id))
        .where(model.tenant_id == tenant_id)
        .group_by(column)
        .order_by(column)
    ).all()
    return {str(key or "unknown"): int(value or 0) for key, value in rows}
