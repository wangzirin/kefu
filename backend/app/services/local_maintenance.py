from __future__ import annotations

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import (
    AuditEvent,
    DiagnosticIntakeRecord,
    DiagnosticRemediationRequest,
    LocalBackupRecord,
    SignedUpdatePackage,
    Tenant,
    utc_now,
)


LOCAL_MAINTENANCE_READINESS_SCHEMA_VERSION = "p3-06u-26h2w8b.local_maintenance_readiness.v1"

_MAINTENANCE_AUDIT_ACTIONS = {
    "diagnostic_bundle.upload_package_created",
    "diagnostic_intake.received",
    "diagnostic_intake.rejected",
    "diagnostic_intake.status_updated",
    "diagnostic_remediation.created",
    "diagnostic_remediation.status_updated",
    "diagnostic_remediation.signed_update_plan_created",
    "signed_update_package.staged",
    "signed_update_package.applied",
    "signed_update_package.rolled_back",
    "signed_update_package.program_dry_run",
    "signed_update_package.strategy_applied",
    "signed_update_package.strategy_rolled_back",
    "local_backup.created",
    "local_backup.verified",
    "local_backup.verification_failed",
    "local_backup.restore_dry_run_created",
    "local_backup.postgres_dry_run_manifest_registered",
    "local_backup.postgres_restore_rehearsal_plan_created",
    "local_backup.postgres_temp_restore_manifest_registered",
    "local_backup.postgres_formal_restore_preflight_registered",
    "local_backup.postgres_formal_restore_execution_dry_run_registered",
    "local_backup.postgres_formal_restore_runbook_registered",
}


def build_local_maintenance_readiness(db: Session, *, tenant: Tenant) -> dict[str, Any]:
    intake_records = _list_by_created_at(db, DiagnosticIntakeRecord, tenant_id=tenant.id)
    remediation_requests = _list_by_created_at(db, DiagnosticRemediationRequest, tenant_id=tenant.id)
    update_packages = _list_by_created_at(db, SignedUpdatePackage, tenant_id=tenant.id, created_field="staged_at")
    backup_records = _list_by_created_at(db, LocalBackupRecord, tenant_id=tenant.id)
    audit_events = _recent_audit_events(db, tenant_id=tenant.id)

    accepted_intakes = [item for item in intake_records if item.validation_status == "passed" and item.status != "rejected"]
    update_plan_requests = [
        item
        for item in remediation_requests
        if item.status == "update_plan_prepared" or _has_signed_update_plan(item.update_request_manifest)
    ]
    verified_backups = [item for item in backup_records if item.status == "verified" or item.verified_at is not None]
    restore_dry_run_backups = [item for item in backup_records if _restore_dry_run_payload(item)]
    applied_or_rolled_back_packages = [item for item in update_packages if item.status in {"applied", "rolled_back"}]

    counts = {
        "diagnostic_intake_total": len(intake_records),
        "diagnostic_intake_accepted": len(accepted_intakes),
        "diagnostic_intake_rejected": len([item for item in intake_records if item.status == "rejected"]),
        "remediation_request_total": len(remediation_requests),
        "remediation_update_plan_prepared": len(update_plan_requests),
        "signed_update_package_total": len(update_packages),
        "signed_update_package_staged": len([item for item in update_packages if item.status == "staged"]),
        "signed_update_package_applied": len([item for item in update_packages if item.status == "applied"]),
        "signed_update_package_rolled_back": len([item for item in update_packages if item.status == "rolled_back"]),
        "local_backup_total": len(backup_records),
        "local_backup_verified": len(verified_backups),
        "restore_dry_run_total": len(restore_dry_run_backups),
        "maintenance_audit_event_total": _count_maintenance_audit_events(db, tenant_id=tenant.id),
    }

    gates = [
        _gate(
            "diagnostic_bundle",
            "诊断包生成",
            "ready",
            "本地诊断包接口可生成脱敏包；真实上传仍需客户手动授权。",
            {"endpoint": "/diagnostic-bundle", "automatic_upload": False},
        ),
        _gate(
            "diagnostic_intake",
            "售后接收台",
            "passed" if accepted_intakes else "pending",
            "已有可用接收记录。" if accepted_intakes else "还没有客户授权上传包接收证据。",
            {"accepted": len(accepted_intakes), "total": len(intake_records)},
        ),
        _gate(
            "remediation_request",
            "售后处理单",
            "passed" if remediation_requests else "pending",
            "已生成售后处理单。" if remediation_requests else "还没有基于诊断包生成处理单。",
            {"total": len(remediation_requests), "update_plan_prepared": len(update_plan_requests)},
        ),
        _gate(
            "signed_update_plan",
            "受控更新计划",
            "passed" if update_plan_requests else "pending",
            "处理单已绑定签名更新计划。" if update_plan_requests else "还没有处理单到签名更新包的绑定计划。",
            {"prepared": len(update_plan_requests)},
        ),
        _gate(
            "signed_update_package",
            "签名更新包",
            "passed" if update_packages else "pending",
            "已有签名更新包证据。" if update_packages else "还没有预检或暂存过签名更新包。",
            {"total": len(update_packages), "applied_or_rolled_back": len(applied_or_rolled_back_packages)},
        ),
        _gate(
            "local_backup",
            "本地备份点",
            "passed" if verified_backups else "warning" if backup_records else "pending",
            "已有校验通过的本地备份点。"
            if verified_backups
            else "已有备份但未校验。" if backup_records else "还没有本地备份点。",
            {"total": len(backup_records), "verified": len(verified_backups)},
        ),
        _gate(
            "restore_dry_run",
            "恢复演练",
            "passed" if restore_dry_run_backups else "pending",
            "已有恢复 dry-run 演练记录。" if restore_dry_run_backups else "还没有恢复演练证据。",
            {"total": len(restore_dry_run_backups)},
        ),
        _gate(
            "audit_evidence",
            "审计证据",
            "passed" if counts["maintenance_audit_event_total"] > 0 else "pending",
            "已有本地维护审计事件。" if counts["maintenance_audit_event_total"] > 0 else "还没有本地维护审计事件。",
            {"total": counts["maintenance_audit_event_total"]},
        ),
    ]

    blockers = _collect_safety_blockers(
        intake_records=intake_records,
        remediation_requests=remediation_requests,
        update_packages=update_packages,
        backup_records=backup_records,
    )
    required_gate_codes = {
        "diagnostic_intake",
        "remediation_request",
        "signed_update_plan",
        "signed_update_package",
        "local_backup",
        "restore_dry_run",
        "audit_evidence",
    }
    required_gates_passed = all(
        gate["status"] == "passed" for gate in gates if gate["code"] in required_gate_codes
    )
    ready = required_gates_passed and not blockers
    maturity_status = "blocked" if blockers else "ready_for_rehearsal" if ready else "missing_evidence"

    return {
        "schema_version": LOCAL_MAINTENANCE_READINESS_SCHEMA_VERSION,
        "tenant_id": tenant.id,
        "generated_at": utc_now(),
        "maturity_status": maturity_status,
        "ready_for_customer_maintenance_rehearsal": ready,
        "summary": _summary_text(maturity_status),
        "counts": counts,
        "latest": {
            "diagnostic_intake": _diagnostic_intake_summary(intake_records[0]) if intake_records else None,
            "remediation_request": _remediation_summary(remediation_requests[0]) if remediation_requests else None,
            "signed_update_package": _signed_update_summary(update_packages[0]) if update_packages else None,
            "local_backup": _backup_summary(backup_records[0]) if backup_records else None,
        },
        "gates": gates,
        "blockers": blockers,
        "safety": {
            "external_write_performed": False,
            "remote_control_performed": False,
            "silent_update_performed": False,
            "automatic_update_performed": False,
            "automatic_upload_performed": False,
            "raw_customer_text_required": False,
            "manual_transfer_required": True,
            "customer_admin_confirmation_required": True,
            "can_restore_now": False,
            "真实外发继续关闭": True,
        },
        "recommended_next_steps": _recommended_next_steps(gates, blockers),
        "recent_audit_events": [_audit_summary(event) for event in audit_events],
    }


def _list_by_created_at(
    db: Session,
    model: type,
    *,
    tenant_id: int,
    created_field: str = "created_at",
) -> list[Any]:
    order_column = getattr(model, created_field)
    return list(
        db.scalars(
            select(model)
            .where(model.tenant_id == tenant_id)
            .order_by(order_column.desc(), model.id.desc())
        ).all()
    )


def _count_maintenance_audit_events(db: Session, *, tenant_id: int) -> int:
    return int(
        db.scalar(
            select(func.count())
            .select_from(AuditEvent)
            .where(AuditEvent.tenant_id == tenant_id, AuditEvent.action.in_(_MAINTENANCE_AUDIT_ACTIONS))
        )
        or 0
    )


def _recent_audit_events(db: Session, *, tenant_id: int) -> list[AuditEvent]:
    return list(
        db.scalars(
            select(AuditEvent)
            .where(AuditEvent.tenant_id == tenant_id, AuditEvent.action.in_(_MAINTENANCE_AUDIT_ACTIONS))
            .order_by(AuditEvent.created_at.desc(), AuditEvent.id.desc())
            .limit(8)
        ).all()
    )


def _gate(code: str, label: str, status: str, reason: str, evidence: dict[str, Any]) -> dict[str, Any]:
    return {
        "code": code,
        "label": label,
        "status": status,
        "reason": reason,
        "evidence": evidence,
    }


def _has_signed_update_plan(manifest: dict[str, Any] | None) -> bool:
    if not isinstance(manifest, dict):
        return False
    return isinstance(manifest.get("signed_update_control_plan"), dict)


def _restore_dry_run_payload(record: LocalBackupRecord) -> dict[str, Any] | None:
    manifest = record.manifest_payload if isinstance(record.manifest_payload, dict) else {}
    formal_restore_runbook = manifest.get("last_formal_restore_runbook")
    if isinstance(formal_restore_runbook, dict):
        return formal_restore_runbook
    formal_restore_execution_dry_run = manifest.get("last_formal_restore_execution_dry_run")
    if isinstance(formal_restore_execution_dry_run, dict):
        return formal_restore_execution_dry_run
    dry_run = manifest.get("last_restore_dry_run")
    if isinstance(dry_run, dict):
        return dry_run
    rehearsal_plan = manifest.get("last_restore_rehearsal_plan")
    if isinstance(rehearsal_plan, dict):
        return rehearsal_plan
    temp_restore_rehearsal = manifest.get("last_temp_restore_rehearsal")
    if isinstance(temp_restore_rehearsal, dict):
        return temp_restore_rehearsal
    formal_restore_preflight = manifest.get("last_formal_restore_preflight")
    return formal_restore_preflight if isinstance(formal_restore_preflight, dict) else None


def _collect_safety_blockers(
    *,
    intake_records: list[DiagnosticIntakeRecord],
    remediation_requests: list[DiagnosticRemediationRequest],
    update_packages: list[SignedUpdatePackage],
    backup_records: list[LocalBackupRecord],
) -> list[str]:
    blockers: list[str] = []
    for record in intake_records:
        _append_true_safety_blockers(blockers, record.safety, prefix=f"诊断接收 {record.intake_id}")
    for request in remediation_requests:
        _append_true_safety_blockers(blockers, request.safety, prefix=f"处理单 {request.request_id}")
    for package in update_packages:
        _append_true_safety_blockers(
            blockers,
            package.preflight_result.get("safety") if isinstance(package.preflight_result, dict) else {},
            prefix=f"更新包 {package.package_id}",
        )
        if package.error_message:
            blockers.append(f"更新包 {package.package_id} 存在错误：{package.error_message}")
    for backup in backup_records:
        dry_run = _restore_dry_run_payload(backup)
        if dry_run and dry_run.get("can_restore_now") is True:
            blockers.append(f"备份 {backup.backup_id} 的恢复演练错误标记为可直接恢复。")
        if backup.error_message:
            blockers.append(f"备份 {backup.backup_id} 存在错误：{backup.error_message}")
    return blockers


def _append_true_safety_blockers(blockers: list[str], safety: Any, *, prefix: str) -> None:
    if not isinstance(safety, dict):
        return
    risky_keys = {
        "external_write_performed": "发生外部写入",
        "external_platform_write_performed": "发生外部平台写入",
        "remote_control_performed": "发生远程控制",
        "silent_update_performed": "发生静默更新",
        "automatic_update_performed": "发生自动更新",
        "automatic_upload_performed": "发生自动上传",
        "raw_message_text_included": "包含原始聊天文本",
        "direct_customer_identifiers_included": "包含直接客户标识",
        "full_channel_payloads_included": "包含完整渠道原始包",
    }
    for key, label in risky_keys.items():
        if safety.get(key) is True:
            blockers.append(f"{prefix}：{label}。")


def _summary_text(maturity_status: str) -> str:
    if maturity_status == "ready_for_rehearsal":
        return "本地维护链路已有完整演练证据，可以进入客户本地试点前复核。"
    if maturity_status == "blocked":
        return "本地维护链路发现安全或执行阻断项，必须先修复再进入试点。"
    return "本地维护链路仍缺少必要证据，不能作为已闭环能力对外说明。"


def _recommended_next_steps(gates: list[dict[str, Any]], blockers: list[str]) -> list[str]:
    if blockers:
        return ["先处理阻断项，再继续做本地维护演练。"]
    steps: list[str] = []
    for gate in gates:
        if gate["status"] == "pending":
            steps.append(f"补齐：{gate['label']}。")
        elif gate["status"] == "warning":
            steps.append(f"复核：{gate['label']}。")
    if not steps:
        steps.append("进入 50-100 条真实题库与本地维护联动 rehearsal。")
    return steps[:6]


def _diagnostic_intake_summary(record: DiagnosticIntakeRecord) -> dict[str, Any]:
    return {
        "id": record.id,
        "intake_id": record.intake_id,
        "status": record.status,
        "validation_status": record.validation_status,
        "package_filename": record.package_filename,
        "created_at": record.created_at,
        "updated_at": record.updated_at,
    }


def _remediation_summary(request: DiagnosticRemediationRequest) -> dict[str, Any]:
    return {
        "id": request.id,
        "request_id": request.request_id,
        "status": request.status,
        "priority": request.priority,
        "title": request.title,
        "has_signed_update_plan": _has_signed_update_plan(request.update_request_manifest),
        "created_at": request.created_at,
        "updated_at": request.updated_at,
    }


def _signed_update_summary(package: SignedUpdatePackage) -> dict[str, Any]:
    return {
        "id": package.id,
        "package_id": package.package_id,
        "package_name": package.package_name,
        "package_type": package.package_type,
        "package_version": package.package_version,
        "status": package.status,
        "backup_created": package.backup_created,
        "can_apply_now": package.can_apply_now,
        "staged_at": package.staged_at,
        "applied_at": package.applied_at,
    }


def _backup_summary(record: LocalBackupRecord) -> dict[str, Any]:
    dry_run = _restore_dry_run_payload(record)
    return {
        "id": record.id,
        "backup_id": record.backup_id,
        "status": record.status,
        "file_name": record.file_name,
        "file_size_bytes": record.file_size_bytes,
        "restore_mode": record.restore_mode,
        "has_restore_dry_run": dry_run is not None,
        "restore_dry_run_ready": dry_run.get("rehearsal_ready") if dry_run else None,
        "created_at": record.created_at,
        "verified_at": record.verified_at,
    }


def _audit_summary(event: AuditEvent) -> dict[str, Any]:
    return {
        "id": event.id,
        "action": event.action,
        "resource_type": event.resource_type,
        "resource_id": event.resource_id,
        "created_at": event.created_at,
    }
