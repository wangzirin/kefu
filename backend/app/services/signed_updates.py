from __future__ import annotations

import base64
import hashlib
import json
from typing import Any

from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.audit import add_audit_event
from app.core.auth import CurrentPrincipal
from app.core.config import get_settings
from app.models import (
    BusinessObject,
    ChannelAccount,
    ChannelConnector,
    KnowledgeDocument,
    KnowledgeEvaluationSet,
    KnowledgeImportBatch,
    LocalBackupRecord,
    ObjectKnowledgeCard,
    SignedUpdatePackage,
    TenantReplyStrategy,
    Tenant,
    User,
)
from app.models.foundation import utc_now
from app.schemas.knowledge import (
    KnowledgeUpdatePackageImportCreate,
    KnowledgeUpdatePackagePayload,
    KnowledgeUpdatePackageRollbackCreate,
)
from app.schemas.reply_strategy_updates import ReplyStrategyUpdatePackagePayload
from app.schemas.signed_updates import SignedUpdatePackagePayload
from app.services.knowledge import import_knowledge_update_package, rollback_knowledge_update_package_import

CURRENT_APP_VERSION = "0.1.0"
EXPECTED_PRODUCT = "wanfa-standard-ops"


class SignedUpdatePreflightRejected(Exception):
    def __init__(self, preflight_result: dict[str, Any]) -> None:
        self.preflight_result = preflight_result


class SignedUpdatePackageConflict(Exception):
    pass


class SignedUpdatePackageNotFound(Exception):
    pass


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")


def preflight_signed_update_package(
    db: Session,
    *,
    tenant: Tenant,
    package: SignedUpdatePackagePayload,
) -> dict[str, Any]:
    manifest = package.manifest
    warnings = ["当前切片只做签名、摘要、版本和备份预检，不执行更新、不替换程序文件。"]
    errors: list[str] = []

    signature_status = _verify_manifest_signature(package)
    if not signature_status["verified"]:
        errors.append(signature_status["error"] or "更新包签名未通过。")

    checksum_status = _verify_payload_checksum(package)
    if not checksum_status["payload_digest_match"]:
        errors.append("payload 摘要不一致，更新包内容可能已被篡改。")
    if not checksum_status["checksums_payload_match"]:
        errors.append("checksums.json 与 manifest 的 payload 摘要不一致。")

    compatibility = _check_compatibility(package)
    if not compatibility["product_match"]:
        errors.append("产品标识不匹配，不能导入到当前客服系统。")
    if not compatibility["compatible"]:
        errors.append("版本不兼容，不能导入到当前应用版本。")

    backup_plan = _build_backup_plan(db, tenant=tenant, package=package)
    health_checks = _build_health_checks(package)
    operations = [item.model_dump(mode="json") for item in manifest.operations]

    can_stage = (
        signature_status["verified"]
        and checksum_status["payload_digest_match"]
        and checksum_status["checksums_payload_match"]
        and compatibility["compatible"]
        and compatibility["product_match"]
    )

    return {
        "package_id": manifest.package_id,
        "package_name": manifest.package_name,
        "package_type": manifest.package_type,
        "package_version": manifest.package_version,
        "dry_run": True,
        "can_stage": can_stage,
        "can_apply_now": False,
        "current_app_version": CURRENT_APP_VERSION,
        "signature_status": signature_status,
        "checksum_status": checksum_status,
        "compatibility": compatibility,
        "backup_plan": backup_plan,
        "health_checks": health_checks,
        "operations": operations,
        "warnings": warnings,
        "errors": errors,
        "safety": {
            "dry_run_only": True,
            "external_write_performed": False,
            "provider_call_performed": False,
            "program_execution_performed": False,
            "database_migration_performed": False,
            "backup_created": False,
            "raw_customer_text_logged": False,
        },
    }


def stage_signed_update_package(
    db: Session,
    *,
    tenant: Tenant,
    package: SignedUpdatePackagePayload,
    actor_id: int | None,
) -> dict[str, Any]:
    preflight_result = preflight_signed_update_package(db, tenant=tenant, package=package)
    if not preflight_result["can_stage"]:
        raise SignedUpdatePreflightRejected(preflight_result)

    package_payload = package.model_dump(mode="json")
    package_digest = hashlib.sha256(canonical_json_bytes(package_payload)).hexdigest()
    manifest = package.manifest
    existing = (
        db.query(SignedUpdatePackage)
        .filter(
            SignedUpdatePackage.tenant_id == tenant.id,
            SignedUpdatePackage.package_id == manifest.package_id,
        )
        .one_or_none()
    )
    if existing is not None:
        if existing.package_digest_sha256 != package_digest:
            raise SignedUpdatePackageConflict("same package_id already staged with different content")
        return _staged_update_payload(existing)

    staged = SignedUpdatePackage(
        tenant_id=tenant.id,
        package_id=manifest.package_id,
        package_name=manifest.package_name,
        package_type=manifest.package_type,
        package_version=manifest.package_version,
        current_app_version=preflight_result["current_app_version"],
        status="staged",
        package_digest_sha256=package_digest,
        package_payload=package_payload,
        preflight_result=preflight_result,
        backup_plan=preflight_result["backup_plan"],
        health_checks=preflight_result["health_checks"],
        can_apply_now=False,
        backup_required=bool(preflight_result["backup_plan"].get("required", True)),
        backup_created=False,
        staged_by_id=actor_id,
    )
    db.add(staged)
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise SignedUpdatePackageConflict("signed update package already staged") from exc
    add_audit_event(
        db,
        tenant_id=tenant.id,
        action="signed_update_package.staged",
        resource_type="signed_update_package",
        actor_id=actor_id,
        resource_id=str(staged.id),
        payload={
            "package_id": staged.package_id,
            "package_type": staged.package_type,
            "package_version": staged.package_version,
            "can_apply_now": staged.can_apply_now,
            "backup_created": staged.backup_created,
        },
    )
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise SignedUpdatePackageConflict("signed update package already staged") from exc
    db.refresh(staged)
    return _staged_update_payload(staged)


def list_staged_update_packages(db: Session, *, tenant: Tenant) -> list[dict[str, Any]]:
    packages = (
        db.query(SignedUpdatePackage)
        .filter(SignedUpdatePackage.tenant_id == tenant.id)
        .order_by(SignedUpdatePackage.id)
        .all()
    )
    return [_staged_update_payload(item) for item in packages]


def apply_staged_signed_update_package(
    db: Session,
    *,
    signed_update_package_id: int,
    principal: CurrentPrincipal,
    reason: str,
) -> dict[str, Any]:
    package = _get_signed_update_for_principal(db, signed_update_package_id, principal)
    if package.status == "applied":
        return _staged_update_payload(package)
    if package.status == "rolled_back":
        raise SignedUpdatePackageConflict("signed update package has already been rolled back")
    if package.status != "staged":
        raise SignedUpdatePackageConflict("signed update package is not staged")
    if package.package_type not in {"knowledge", "strategy"}:
        raise SignedUpdatePackageConflict(
            "program update is not supported in this slice; only signed knowledge and strategy packages can be applied"
        )
    _require_verified_local_backup_before_apply(db, tenant_id=package.tenant_id)
    if package.package_type == "strategy":
        return _apply_strategy_update_package(db, package=package, principal=principal, reason=reason)

    raw_payload = (package.package_payload or {}).get("payload") or {}
    knowledge_payload = KnowledgeUpdatePackagePayload.model_validate(raw_payload)
    apply_result = import_knowledge_update_package(
        db,
        package.tenant_id,
        KnowledgeUpdatePackageImportCreate(package=knowledge_payload),
        principal,
    )

    # import_knowledge_update_package commits internally, so refetch before persisting signed-package metadata.
    package = _get_signed_update_for_principal(db, signed_update_package_id, principal)
    now = utc_now()
    apply_payload = apply_result.model_dump(mode="json")
    backup_plan = dict(package.backup_plan or {})
    backup_plan.update(
        {
            "created": True,
            "created_at": now.isoformat(),
            "scope": "knowledge_update_package_import_batch",
            "snapshot": apply_payload.get("backup_snapshot", {}),
            "knowledge_import_batch_id": apply_result.import_batch_id,
            "apply_reason": reason.strip(),
        }
    )
    preflight_result = _merge_preflight_payload(
        package.preflight_result,
        {
            "apply_result": apply_payload,
            "safety": _signed_update_safety(backup_created=True, dry_run_only=False),
        },
    )
    package.status = "applied"
    package.backup_created = True
    package.can_apply_now = False
    package.applied_at = now
    package.error_message = ""
    package.backup_plan = backup_plan
    package.preflight_result = preflight_result
    package.health_checks = _mark_apply_health_checks(package.health_checks or [])
    add_audit_event(
        db,
        tenant_id=package.tenant_id,
        actor_id=principal.user.id,
        action="signed_update_package.applied",
        resource_type="signed_update_package",
        resource_id=str(package.id),
        payload={
            "package_id": package.package_id,
            "package_type": package.package_type,
            "package_version": package.package_version,
            "knowledge_import_batch_id": apply_result.import_batch_id,
            "external_write_performed": False,
            "program_execution_performed": False,
        },
    )
    db.commit()
    db.refresh(package)
    return _staged_update_payload(package)


def rollback_applied_signed_update_package(
    db: Session,
    *,
    signed_update_package_id: int,
    principal: CurrentPrincipal,
    reason: str,
) -> dict[str, Any]:
    package = _get_signed_update_for_principal(db, signed_update_package_id, principal)
    if package.status == "rolled_back":
        return _staged_update_payload(package)
    if package.status != "applied":
        raise SignedUpdatePackageConflict("only applied signed update packages can be rolled back")
    if package.package_type == "strategy":
        return _rollback_strategy_update_package(db, package=package, principal=principal, reason=reason)
    if package.package_type != "knowledge":
        raise SignedUpdatePackageConflict("only signed knowledge and strategy packages can be rolled back in this slice")
    knowledge_import_batch_id = _knowledge_import_batch_id(package)
    if knowledge_import_batch_id is None:
        raise SignedUpdatePackageConflict("signed update package has no knowledge import batch to roll back")

    rollback_result = rollback_knowledge_update_package_import(
        db,
        knowledge_import_batch_id,
        KnowledgeUpdatePackageRollbackCreate(reason=reason),
        principal,
    )

    # rollback_knowledge_update_package_import commits internally, so refetch before updating package status.
    package = _get_signed_update_for_principal(db, signed_update_package_id, principal)
    rollback_payload = rollback_result.model_dump(mode="json")
    preflight_result = _merge_preflight_payload(
        package.preflight_result,
        {
            "rollback_result": rollback_payload,
            "safety": _signed_update_safety(backup_created=package.backup_created, dry_run_only=False),
        },
    )
    backup_plan = dict(package.backup_plan or {})
    backup_plan["rollback_status"] = rollback_result.rollback_status
    backup_plan["rollback_reason"] = reason.strip()
    backup_plan["rolled_back_at"] = utc_now().isoformat()
    package.status = "rolled_back"
    package.can_apply_now = False
    package.error_message = ""
    package.backup_plan = backup_plan
    package.preflight_result = preflight_result
    package.health_checks = _append_health_check(
        package.health_checks or [],
        {
            "id": "rollback",
            "label": "知识包回滚",
            "required": True,
            "status": "passed",
            "message": "已通过导入批次归档本次创建的知识对象。",
        },
    )
    add_audit_event(
        db,
        tenant_id=package.tenant_id,
        actor_id=principal.user.id,
        action="signed_update_package.rolled_back",
        resource_type="signed_update_package",
        resource_id=str(package.id),
        payload={
            "package_id": package.package_id,
            "knowledge_import_batch_id": knowledge_import_batch_id,
            "rollback_status": rollback_result.rollback_status,
            "external_write_performed": False,
            "program_execution_performed": False,
        },
    )
    db.commit()
    db.refresh(package)
    return _staged_update_payload(package)


def create_program_update_dry_run(
    db: Session,
    *,
    signed_update_package_id: int,
    principal: CurrentPrincipal,
    reason: str,
) -> dict[str, Any]:
    package = _get_signed_update_for_principal(db, signed_update_package_id, principal)
    if package.package_type != "program":
        raise SignedUpdatePackageConflict("only signed program packages can create a program update rehearsal plan")
    if package.status != "staged":
        raise SignedUpdatePackageConflict("only staged program packages can create a program update rehearsal plan")

    now = utc_now()
    raw_payload = (package.package_payload or {}).get("payload") or {}
    manifest = ((package.package_payload or {}).get("manifest") or {})
    payload_summary = _program_update_payload_summary(raw_payload)
    dry_run_result = {
        "dry_run_status": "planned",
        "package_id": package.package_id,
        "package_name": package.package_name,
        "package_version": package.package_version,
        "current_app_version": package.current_app_version,
        "target_program_version": payload_summary["program_version"],
        "requires_maintenance_window": bool(
            manifest.get("requires_maintenance_window")
            or (package.backup_plan or {}).get("maintenance_window_required")
            or True
        ),
        "generated_at": now.isoformat(),
        "reason": reason.strip(),
        "payload_summary": payload_summary,
        "planned_steps": [
            {
                "id": "verify_signature_and_checksum",
                "label": "校验签名和摘要",
                "status": "planned",
                "description": "确认更新包来自可信发布方，且 payload 没有被篡改。",
            },
            {
                "id": "create_local_backup",
                "label": "创建本地备份点",
                "status": "required_before_apply",
                "description": "程序更新前必须完成数据库物理备份和完整性校验。",
            },
            {
                "id": "check_file_inventory",
                "label": "核对程序文件清单",
                "status": "planned",
                "description": "只读取文件路径、摘要和大小，当前不会写入或替换任何程序文件。",
            },
            {
                "id": "migration_compatibility_rehearsal",
                "label": "迁移兼容性演练",
                "status": "planned",
                "description": "只生成迁移演练计划，当前不会执行数据库迁移。",
            },
            {
                "id": "maintenance_window_confirmation",
                "label": "确认维护窗口",
                "status": "required_before_apply",
                "description": "程序更新需要客户管理员确认停机、重启和回滚窗口。",
            },
            {
                "id": "post_update_smoke_plan",
                "label": "生成更新后 smoke 清单",
                "status": "planned",
                "description": "列出更新后应检查的登录、知识库、工作台和更新中心接口。",
            },
            {
                "id": "rollback_plan",
                "label": "生成回滚方案",
                "status": "planned",
                "description": "确认需要上一版本程序包和更新前数据库备份。",
            },
        ],
        "blocked_actions": [
            "replace_program_files",
            "execute_migrations",
            "restart_service",
            "external_write",
            "provider_call",
            "delete_existing_bundle",
        ],
        "safety": _signed_update_safety(backup_created=False, dry_run_only=True),
    }
    backup_plan = dict(package.backup_plan or {})
    backup_plan["program_dry_run"] = {
        "created": True,
        "created_at": now.isoformat(),
        "requires_manual_backup_before_real_apply": True,
        "maintenance_window_required": dry_run_result["requires_maintenance_window"],
        "real_apply_enabled": False,
    }
    package.backup_plan = backup_plan
    package.preflight_result = _merge_preflight_payload(
        package.preflight_result,
        {
            "program_dry_run_result": dry_run_result,
            "safety": _signed_update_safety(backup_created=False, dry_run_only=True),
        },
    )
    package.health_checks = _append_health_check(
        package.health_checks or [],
        {
            "id": "program_update_dry_run",
            "label": "程序更新演练计划",
            "required": True,
            "status": "passed",
            "message": "已生成程序更新演练计划；未替换文件、未执行迁移、未重启服务。",
        },
    )
    package.can_apply_now = False
    package.backup_created = False
    package.error_message = ""
    add_audit_event(
        db,
        tenant_id=package.tenant_id,
        actor_id=principal.user.id,
        action="signed_update_package.program_dry_run",
        resource_type="signed_update_package",
        resource_id=str(package.id),
        payload={
            "package_id": package.package_id,
            "package_type": package.package_type,
            "package_version": package.package_version,
            "dry_run_status": dry_run_result["dry_run_status"],
            "real_apply_enabled": False,
            "external_write_performed": False,
            "program_execution_performed": False,
            "database_migration_performed": False,
        },
    )
    db.commit()
    db.refresh(package)
    return _staged_update_payload(package)


def _apply_strategy_update_package(
    db: Session,
    *,
    package: SignedUpdatePackage,
    principal: CurrentPrincipal,
    reason: str,
) -> dict[str, Any]:
    raw_payload = (package.package_payload or {}).get("payload") or {}
    strategy_payload = ReplyStrategyUpdatePackagePayload.model_validate(raw_payload)
    strategy_json = strategy_payload.model_dump(mode="json")
    current_strategy = (
        db.query(TenantReplyStrategy)
        .filter(TenantReplyStrategy.tenant_id == package.tenant_id)
        .one_or_none()
    )
    previous_snapshot = _strategy_snapshot(current_strategy)
    now = utc_now()
    if current_strategy is None:
        current_strategy = TenantReplyStrategy(
            tenant_id=package.tenant_id,
            created_at=now,
        )
        db.add(current_strategy)
    current_strategy.strategy_id = strategy_payload.strategy_id
    current_strategy.strategy_version = strategy_payload.strategy_version
    current_strategy.status = "active"
    current_strategy.strategy_payload = strategy_json
    current_strategy.previous_strategy_payload = previous_snapshot
    current_strategy.signed_update_package_id = package.id
    current_strategy.updated_by_id = principal.user.id
    current_strategy.updated_at = now

    reply_policy = strategy_json.get("reply_policy", {})
    apply_payload = {
        "apply_status": "applied",
        "strategy_id": strategy_payload.strategy_id,
        "strategy_version": strategy_payload.strategy_version,
        "notes": strategy_payload.notes,
        "reply_policy": reply_policy,
        "model_routing": strategy_json.get("model_routing", {}),
        "previous_strategy_existed": bool(previous_snapshot.get("existed")),
        "apply_reason": reason.strip(),
        "external_write_performed": False,
        "provider_call_performed": False,
        "program_execution_performed": False,
        "database_migration_performed": False,
    }
    backup_plan = dict(package.backup_plan or {})
    backup_plan.update(
        {
            "created": True,
            "created_at": now.isoformat(),
            "scope": "reply_strategy_config_snapshot",
            "previous_strategy": previous_snapshot,
            "strategy_id": strategy_payload.strategy_id,
            "strategy_version": strategy_payload.strategy_version,
            "apply_reason": reason.strip(),
        }
    )
    package.status = "applied"
    package.backup_created = True
    package.can_apply_now = False
    package.applied_at = now
    package.error_message = ""
    package.backup_plan = backup_plan
    package.preflight_result = _merge_preflight_payload(
        package.preflight_result,
        {
            "apply_result": apply_payload,
            "safety": _signed_update_safety(backup_created=True, dry_run_only=False),
        },
    )
    package.health_checks = _mark_strategy_apply_health_checks(package.health_checks or [])
    add_audit_event(
        db,
        tenant_id=package.tenant_id,
        actor_id=principal.user.id,
        action="signed_update_package.strategy_applied",
        resource_type="signed_update_package",
        resource_id=str(package.id),
        payload={
            "package_id": package.package_id,
            "package_type": package.package_type,
            "strategy_id": strategy_payload.strategy_id,
            "strategy_version": strategy_payload.strategy_version,
            "external_write_performed": False,
            "program_execution_performed": False,
        },
    )
    db.commit()
    db.refresh(package)
    return _staged_update_payload(package)


def _rollback_strategy_update_package(
    db: Session,
    *,
    package: SignedUpdatePackage,
    principal: CurrentPrincipal,
    reason: str,
) -> dict[str, Any]:
    current_strategy = (
        db.query(TenantReplyStrategy)
        .filter(TenantReplyStrategy.tenant_id == package.tenant_id)
        .one_or_none()
    )
    previous_snapshot = (package.backup_plan or {}).get("previous_strategy") or {}
    now = utc_now()
    if previous_snapshot.get("existed"):
        if current_strategy is None:
            current_strategy = TenantReplyStrategy(
                tenant_id=package.tenant_id,
                created_at=now,
            )
            db.add(current_strategy)
        current_strategy.strategy_id = str(previous_snapshot.get("strategy_id") or "")
        current_strategy.strategy_version = str(previous_snapshot.get("strategy_version") or "")
        current_strategy.status = str(previous_snapshot.get("status") or "active")
        current_strategy.strategy_payload = dict(previous_snapshot.get("strategy_payload") or {})
        current_strategy.previous_strategy_payload = dict((package.preflight_result or {}).get("apply_result") or {})
        current_strategy.signed_update_package_id = None
        current_strategy.updated_by_id = principal.user.id
        current_strategy.updated_at = now
        rollback_status = "restored_previous_strategy"
    else:
        if current_strategy is not None:
            current_strategy.status = "inactive"
            current_strategy.strategy_id = ""
            current_strategy.strategy_version = ""
            current_strategy.previous_strategy_payload = _strategy_snapshot(current_strategy)
            current_strategy.strategy_payload = {}
            current_strategy.signed_update_package_id = None
            current_strategy.updated_by_id = principal.user.id
            current_strategy.updated_at = now
        rollback_status = "disabled_strategy"

    rollback_payload = {
        "rollback_status": rollback_status,
        "rollback_reason": reason.strip(),
        "rolled_back_at": now.isoformat(),
        "previous_strategy_existed": bool(previous_snapshot.get("existed")),
        "external_write_performed": False,
        "provider_call_performed": False,
        "program_execution_performed": False,
        "database_migration_performed": False,
    }
    backup_plan = dict(package.backup_plan or {})
    backup_plan["rollback_status"] = rollback_status
    backup_plan["rollback_reason"] = reason.strip()
    backup_plan["rolled_back_at"] = now.isoformat()
    package.status = "rolled_back"
    package.can_apply_now = False
    package.error_message = ""
    package.backup_plan = backup_plan
    package.preflight_result = _merge_preflight_payload(
        package.preflight_result,
        {
            "rollback_result": rollback_payload,
            "safety": _signed_update_safety(backup_created=package.backup_created, dry_run_only=False),
        },
    )
    package.health_checks = _append_health_check(
        package.health_checks or [],
        {
            "id": "strategy_rollback",
            "label": "策略包回滚",
            "required": True,
            "status": "passed",
            "message": "已恢复上一份回复策略配置，或关闭本次新增策略。",
        },
    )
    add_audit_event(
        db,
        tenant_id=package.tenant_id,
        actor_id=principal.user.id,
        action="signed_update_package.strategy_rolled_back",
        resource_type="signed_update_package",
        resource_id=str(package.id),
        payload={
            "package_id": package.package_id,
            "rollback_status": rollback_status,
            "external_write_performed": False,
            "program_execution_performed": False,
        },
    )
    db.commit()
    db.refresh(package)
    return _staged_update_payload(package)


def _staged_update_payload(package: SignedUpdatePackage) -> dict[str, Any]:
    preflight_result = package.preflight_result or {}
    backup_plan = package.backup_plan or {}
    safety = dict(
        preflight_result.get(
            "safety",
            {
                "dry_run_only": True,
                "external_write_performed": False,
                "provider_call_performed": False,
                "program_execution_performed": False,
                "database_migration_performed": False,
                "backup_created": False,
                "raw_customer_text_logged": False,
            },
        )
    )
    if package.backup_created:
        safety["backup_created"] = True
    if package.status in {"applied", "rolled_back"}:
        safety["dry_run_only"] = False
    return {
        "id": package.id,
        "package_id": package.package_id,
        "package_name": package.package_name,
        "package_type": package.package_type,
        "package_version": package.package_version,
        "status": package.status,
        "current_app_version": package.current_app_version,
        "package_digest_sha256": package.package_digest_sha256,
        "can_apply_now": package.can_apply_now,
        "backup_required": package.backup_required,
        "backup_created": package.backup_created,
        "preflight_result": preflight_result,
        "backup_plan": backup_plan,
        "health_checks": package.health_checks or [],
        "safety": safety,
        "knowledge_import_batch_id": _knowledge_import_batch_id(package),
        "apply_result": preflight_result.get("apply_result", {}),
        "rollback_result": preflight_result.get("rollback_result", {}),
        "staged_by_id": package.staged_by_id,
        "staged_at": package.staged_at,
        "applied_at": package.applied_at,
        "error_message": package.error_message,
    }


def _get_signed_update_for_principal(
    db: Session,
    signed_update_package_id: int,
    principal: CurrentPrincipal,
) -> SignedUpdatePackage:
    package = (
        db.query(SignedUpdatePackage)
        .filter(
            SignedUpdatePackage.id == signed_update_package_id,
            SignedUpdatePackage.tenant_id == principal.tenant.id,
        )
        .one_or_none()
    )
    if package is None:
        raise SignedUpdatePackageNotFound("signed update package not found")
    return package


def _knowledge_import_batch_id(package: SignedUpdatePackage) -> int | None:
    backup_plan = package.backup_plan or {}
    value = backup_plan.get("knowledge_import_batch_id")
    if value is None:
        apply_result = (package.preflight_result or {}).get("apply_result") or {}
        value = apply_result.get("import_batch_id")
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _require_verified_local_backup_before_apply(db: Session, *, tenant_id: int) -> None:
    backups = (
        db.query(LocalBackupRecord)
        .filter(
            LocalBackupRecord.tenant_id == tenant_id,
            LocalBackupRecord.status == "verified",
        )
        .order_by(LocalBackupRecord.verified_at.desc().nullslast(), LocalBackupRecord.id.desc())
        .all()
    )
    for backup in backups:
        restore_dry_run = (backup.manifest_payload or {}).get("last_restore_dry_run") or {}
        if (
            backup.file_size_bytes > 0
            and len(backup.sha256 or "") == 64
            and restore_dry_run.get("rehearsal_ready") is True
            and restore_dry_run.get("can_restore_now") is False
            and (restore_dry_run.get("safety") or {}).get("database_file_replaced") is False
        ):
            return
    raise SignedUpdatePackageConflict(
        "signed update apply requires a verified local backup and restore dry-run evidence before applying"
    )


def _strategy_snapshot(strategy: TenantReplyStrategy | None) -> dict[str, Any]:
    if strategy is None:
        return {"existed": False}
    return {
        "existed": True,
        "strategy_id": strategy.strategy_id,
        "strategy_version": strategy.strategy_version,
        "status": strategy.status,
        "strategy_payload": strategy.strategy_payload or {},
    }


def _signed_update_safety(*, backup_created: bool, dry_run_only: bool) -> dict[str, Any]:
    return {
        "dry_run_only": dry_run_only,
        "external_write_performed": False,
        "provider_call_performed": False,
        "program_execution_performed": False,
        "database_migration_performed": False,
        "backup_created": backup_created,
        "raw_customer_text_logged": False,
    }


def _program_update_payload_summary(raw_payload: dict[str, Any]) -> dict[str, Any]:
    files = raw_payload.get("files") if isinstance(raw_payload.get("files"), list) else []
    migrations = raw_payload.get("migrations") if isinstance(raw_payload.get("migrations"), list) else []
    services = raw_payload.get("services") if isinstance(raw_payload.get("services"), list) else []
    rollback = raw_payload.get("rollback") if isinstance(raw_payload.get("rollback"), dict) else {}
    bundle = raw_payload.get("bundle") if isinstance(raw_payload.get("bundle"), dict) else {}
    file_paths = [str(item.get("path")) for item in files if isinstance(item, dict) and item.get("path")]
    migration_ids = [str(item.get("id")) for item in migrations if isinstance(item, dict) and item.get("id")]
    return {
        "schema_version": str(raw_payload.get("schema_version") or ""),
        "program_version": str(raw_payload.get("program_version") or bundle.get("version") or ""),
        "bundle_id": str(bundle.get("bundle_id") or ""),
        "bundle_sha256": str(bundle.get("sha256") or ""),
        "file_count": len(files),
        "file_paths": file_paths[:50],
        "migration_count": len(migrations),
        "migration_ids": migration_ids[:50],
        "services": [str(service) for service in services[:20]],
        "requires_previous_bundle": bool(rollback.get("requires_previous_bundle", True)),
        "requires_database_backup": bool(rollback.get("requires_database_backup", True)),
    }


def _merge_preflight_payload(current: dict | None, patch: dict[str, Any]) -> dict[str, Any]:
    merged = dict(current or {})
    merged.update(patch)
    return merged


def _mark_apply_health_checks(checks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    marked: list[dict[str, Any]] = []
    seen: set[str] = set()
    messages = {
        "api_health": "应用接口已完成服务端处理。",
        "database_session": "知识更新包已写入本地数据库。",
        "backup_restore_point": "已绑定导入前快照和导入批次，可按本次创建对象回滚。",
        "knowledge_regression": "评测集已导入；完整客服答案质量评测需在知识评测页单独运行。",
    }
    for check in checks:
        item = dict(check)
        check_id = str(item.get("id", ""))
        if check_id in {"api_health", "database_session", "backup_restore_point"}:
            item["status"] = "passed"
        elif check_id == "knowledge_regression":
            item["status"] = "ready"
        if check_id in messages:
            item["message"] = messages[check_id]
        if check_id:
            seen.add(check_id)
        marked.append(item)
    for missing_id in ("api_health", "database_session", "backup_restore_point"):
        if missing_id not in seen:
            marked.append(
                {
                    "id": missing_id,
                    "label": messages[missing_id].split("。")[0],
                    "required": True,
                    "status": "passed",
                    "message": messages[missing_id],
                }
            )
    return marked


def _mark_strategy_apply_health_checks(checks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    marked: list[dict[str, Any]] = []
    seen: set[str] = set()
    messages = {
        "api_health": "应用接口已完成服务端处理。",
        "database_session": "策略配置已写入本地数据库。",
        "backup_restore_point": "已保存应用前策略快照，可回滚。",
        "knowledge_regression": "策略已应用；建议在知识评测页重新运行转人工和禁用承诺题。",
    }
    for check in checks:
        item = dict(check)
        check_id = str(item.get("id", ""))
        if check_id in {"api_health", "database_session", "backup_restore_point"}:
            item["status"] = "passed"
        elif check_id == "knowledge_regression":
            item["status"] = "ready"
        if check_id in messages:
            item["message"] = messages[check_id]
        if check_id:
            seen.add(check_id)
        marked.append(item)
    for missing_id in ("api_health", "database_session", "backup_restore_point"):
        if missing_id not in seen:
            marked.append(
                {
                    "id": missing_id,
                    "label": messages[missing_id].split("。")[0],
                    "required": True,
                    "status": "passed",
                    "message": messages[missing_id],
                }
            )
    return marked


def _append_health_check(checks: list[dict[str, Any]], next_check: dict[str, Any]) -> list[dict[str, Any]]:
    return [dict(item) for item in checks if item.get("id") != next_check.get("id")] + [next_check]


def _verify_payload_checksum(package: SignedUpdatePackagePayload) -> dict[str, Any]:
    actual = hashlib.sha256(canonical_json_bytes(package.payload)).hexdigest()
    expected = package.manifest.payload_digest_sha256.lower()
    checksum_expected = str(package.checksums.get("payload_sha256", "")).lower()
    return {
        "payload_digest_match": actual == expected,
        "checksums_payload_match": checksum_expected == expected,
        "expected": expected,
        "actual": actual,
        "checksums_payload_sha256": checksum_expected,
        "payload_size_bytes": len(canonical_json_bytes(package.payload)),
        "declared_payload_size_bytes": package.manifest.payload_size_bytes,
    }


def _verify_manifest_signature(package: SignedUpdatePackagePayload) -> dict[str, Any]:
    signature = package.signature
    status: dict[str, Any] = {
        "verified": False,
        "algorithm": signature.algorithm,
        "key_id": signature.key_id,
        "error": "",
    }
    trusted_keys, key_error = _load_trusted_public_keys()
    if key_error:
        status["error"] = key_error
        return status
    public_key_pem = trusted_keys.get(signature.key_id)
    if not public_key_pem:
        status["error"] = "未找到可信发布公钥，更新包不能通过签名校验。"
        return status
    try:
        public_key = RSA.import_key(public_key_pem)
        signature_bytes = base64.b64decode(signature.value, validate=True)
        manifest_digest = SHA256.new(canonical_json_bytes(package.manifest.model_dump(mode="json")))
        pkcs1_15.new(public_key).verify(manifest_digest, signature_bytes)
    except Exception as exc:  # noqa: BLE001 - crypto import/verify failures share one safe user-facing path.
        status["error"] = f"签名校验失败：{type(exc).__name__}"
        return status
    status["verified"] = True
    return status


def _load_trusted_public_keys() -> tuple[dict[str, str], str]:
    raw = get_settings().signed_update_trusted_public_keys_json
    if not raw:
        return {}, "未配置可信发布公钥，不能接收更新包。"
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return {}, "可信发布公钥配置不是合法 JSON。"
    if not isinstance(parsed, dict):
        return {}, "可信发布公钥配置必须是 key_id 到 PEM 的映射。"
    return {str(key): str(value) for key, value in parsed.items()}, ""


def _check_compatibility(package: SignedUpdatePackagePayload) -> dict[str, Any]:
    versions = [str(item).strip() for item in package.manifest.compatible_app_versions if str(item).strip()]
    product_match = package.manifest.product == EXPECTED_PRODUCT
    compatible = product_match and _version_allowed(CURRENT_APP_VERSION, versions)
    return {
        "compatible": compatible,
        "product_match": product_match,
        "product": package.manifest.product,
        "expected_product": EXPECTED_PRODUCT,
        "current_app_version": CURRENT_APP_VERSION,
        "compatible_app_versions": versions,
    }


def _version_allowed(current_version: str, allowed_versions: list[str]) -> bool:
    if not allowed_versions:
        return False
    if "*" in allowed_versions or current_version in allowed_versions:
        return True
    current_parts = current_version.split(".")
    for allowed in allowed_versions:
        parts = allowed.split(".")
        if len(parts) == 3 and parts[-1].lower() == "x" and current_parts[:2] == parts[:2]:
            return True
    return False


def _build_backup_plan(db: Session, *, tenant: Tenant, package: SignedUpdatePackagePayload) -> dict[str, Any]:
    resources = [
        "database_snapshot",
        "knowledge_documents",
        "business_objects",
        "object_knowledge_cards",
        "evaluation_sets",
        "knowledge_import_batches",
        "channel_accounts",
        "channel_connectors",
    ]
    if package.manifest.package_type == "strategy":
        resources.extend(["tenant_reply_strategies", "reply_policy", "model_routing_policy"])
    if package.manifest.package_type == "program":
        resources.extend(["program_version", "configuration_files"])
    return {
        "required": True,
        "created": False,
        "rollback_required": True,
        "maintenance_window_required": package.manifest.requires_maintenance_window
        or package.manifest.package_type == "program",
        "resources": resources,
        "estimated_counts": {
            "users": _count(db, User, tenant.id),
            "knowledge_documents": _count(db, KnowledgeDocument, tenant.id),
            "business_objects": _count(db, BusinessObject, tenant.id),
            "object_knowledge_cards": _count(db, ObjectKnowledgeCard, tenant.id),
            "evaluation_sets": _count(db, KnowledgeEvaluationSet, tenant.id),
            "knowledge_import_batches": _count(db, KnowledgeImportBatch, tenant.id),
            "channel_accounts": _count(db, ChannelAccount, tenant.id),
            "channel_connectors": _count(db, ChannelConnector, tenant.id),
            "tenant_reply_strategies": _count(db, TenantReplyStrategy, tenant.id),
        },
    }


def _count(db: Session, model, tenant_id: int) -> int:
    return int(db.query(model).filter(model.tenant_id == tenant_id).count())


def _build_health_checks(package: SignedUpdatePackagePayload) -> list[dict[str, Any]]:
    checks = [
        {"id": "api_health", "label": "后端健康检查", "required": True, "status": "planned"},
        {"id": "database_session", "label": "数据库连接检查", "required": True, "status": "planned"},
        {"id": "backup_restore_point", "label": "更新前备份点", "required": True, "status": "planned"},
    ]
    if package.manifest.package_type in {"knowledge", "strategy"}:
        checks.append(
            {"id": "knowledge_regression", "label": "知识/策略回归评测", "required": True, "status": "planned"}
        )
    if package.manifest.package_type == "program":
        checks.extend(
            [
                {"id": "process_version_check", "label": "运行进程版本切换检查", "required": True, "status": "planned"},
                {"id": "post_update_api_smoke", "label": "程序更新后核心接口 smoke", "required": True, "status": "planned"},
            ]
        )
    return checks
