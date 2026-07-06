from __future__ import annotations

import csv
import base64
import hashlib
import io
import json
import re
import zipfile
from pathlib import Path
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.tenants import require_tenant
from app.core.audit import add_audit_event
from app.core.auth import CurrentPrincipal
from app.models import (
    AuditEvent,
    BusinessObject,
    Channel,
    Contact,
    Conversation,
    ConversationEvent,
    CustomerMaterialBatch,
    KnowledgeDocument,
    KnowledgeEvaluationCase,
    KnowledgeEvaluationRun,
    KnowledgeEvaluationSet,
    Message,
    PilotReadinessFact,
    Tenant,
    User,
    utc_now,
)
from app.schemas.pilot import (
    CustomerMaterialHandoffBundleRead,
    CustomerMaterialBatchListRead,
    CustomerMaterialBatchRead,
    CustomerMaterialPrecheckCreate,
    CustomerMaterialPrecheckRead,
    CustomerMaterialTemplatePackageRead,
    KnowledgeConfirmationImportCreate,
    KnowledgeConfirmationImportItemRead,
    KnowledgeConfirmationImportRead,
    PilotReadinessRead,
    PilotReadinessStepRead,
    PilotRuntimeFactRead,
    SafeTestConversationRead,
)
from app.services.local_maintenance import build_local_maintenance_readiness


PILOT_READINESS_SCHEMA_VERSION = "p3-06u-26h2w-pilot0.readiness.v1"
KNOWLEDGE_CONFIRMATION_IMPORT_SCHEMA_VERSION = "p3-06u-26h2w-pilot2.knowledge_confirmation_import.v1"
CUSTOMER_MATERIAL_PRECHECK_SCHEMA_VERSION = "p3-06u-26h2w-data2r4.customer_material_precheck.v1"
CUSTOMER_MATERIAL_TEMPLATE_PACKAGE_SCHEMA_VERSION = (
    "p3-06u-26h2w-data2r5.customer_material_template_package.v1"
)
CUSTOMER_MATERIAL_HANDOFF_BUNDLE_SCHEMA_VERSION = (
    "p3-06u-26h2w-data2r6.customer_material_handoff_bundle.v1"
)
CUSTOMER_MATERIAL_BATCH_LIST_SCHEMA_VERSION = "p3-06u-26h2w-nc3.customer_material_batch_list.v1"
SAFE_TEST_CONVERSATION_SCHEMA_VERSION = "p3-06u-26h2w-fe11.safe_test_conversation.v1"
ROOT = Path(__file__).resolve().parents[3]
TRIAL_CLOSURE_SUMMARY_PATHS = {
    "trial_c0": ROOT / "output/p3_06u_26h2w_trial_c0_co_creation_scope/summary.json",
    "data1": ROOT / "output/p3_06u_26h2w_data1_customer_material_intake/summary.json",
    "deploy1": ROOT / "output/p3_06u_26h2w_deploy1_clean_local_trial/summary.json",
    "kb5": ROOT / "output/p3_06u_26h2w_kb5_customer_knowledge_retest/summary.json",
    "trial2": ROOT / "output/p3_06u_26h2w_trial2_shadow_trial_report/summary.json",
    "fe8": ROOT / "output/p3_06u_26h2w_fe8_trial_friction_frontend_qa/summary.json",
    "pilot7": ROOT / "output/p3_06u_26h2w_pilot7_co_creation_trial_readiness/summary.json",
    "fe7": ROOT / "output/p3_06u_26h2w_fe7_customer_trial_browser_smoke/summary.json",
    "kb4": ROOT / "output/p3_06u_26h2w_kb4_customer_knowledge_trial_loop/summary.json",
    "install5": ROOT / "output/p3_06u_26h2w_install5_local_startup_experience/summary.json",
    "ops3": ROOT / "output/p3_06u_26h2w_ops3_customer_trial_ops_loop/summary.json",
    "pack7": ROOT / "output/p3_06u_26h2w_pack7_trial_handoff_archive_v2/summary.json",
    "pack8": ROOT / "output/p3_06u_26h2w_pack8_trial_package_v1_1/summary.json",
}
REAL_CUSTOMER_MATERIAL_SUMMARY_PATH = (
    ROOT / "output/p3_06u_26h2w_data2_real_customer_material_readiness/summary.json"
)
FIVE_GAP_SUMMARY_PATHS = {
    "material_intake_package": ROOT / "output/p3_06u_26h2w_data2r2_material_intake_package/summary.json",
    "material_validation_fixtures": ROOT / "output/p3_06u_26h2w_data2r3_material_validation_fixtures/summary.json",
    "material_drop_gate": ROOT / "output/p3_06u_26h2w_data2r7_received_file_drop_gate/summary.json",
    "real_customer_material": ROOT / "output/p3_06u_26h2w_data2r_real_customer_materials/summary.json",
    "customer_knowledge_retest": ROOT / "output/p3_06u_26h2w_kb6_real_customer_knowledge_retest/summary.json",
    "shadow_trial": ROOT / "output/p3_06u_26h2w_trial3_real_customer_shadow_trial/summary.json",
    "frontend_customer_qa": ROOT / "output/p3_06u_26h2w_fe9_customer_data_browser_qa/summary.json",
    "frontend_product_polish": ROOT / "output/p3_06u_26h2w_fe10_final_product_polish_gate/summary.json",
    "channel_boundary": ROOT / "output/p3_06u_26h2w_channel2_personnel_boundary/summary.json",
    "installer_trial": ROOT / "output/p3_06u_26h2w_install6_trial_installer_experience/summary.json",
    "pack10": ROOT / "output/p3_06u_26h2w_pack10_customer_data_trial_package/summary.json",
}

_CONFIRMED_STATUSES = {"confirmed", "accepted", "确认通过", "已确认", "通过"}
_ACCEPTED_WITH_NOTES_STATUSES = {"accepted_with_notes", "confirmed_with_notes", "有备注通过", "带备注确认"}
_REVISION_STATUSES = {"needs_revision", "need_revision", "需修订", "需要修订", "需修改"}
_REJECTED_STATUSES = {"rejected", "reject", "已拒绝", "拒绝"}
_PENDING_STATUSES = {"", "pending", "待确认", "未确认"}

_SEVERE_SECRET_PATTERNS = [
    re.compile(
        r"(?i)[\"']?(api[_-]?key|access[_-]?token|refresh[_-]?token|secret|password)[\"']?\s*[:=]\s*[\"']?[A-Za-z0-9_\-]{10,}"
    ),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"(?i)[\"']?encodingaeskey[\"']?\s*[:=]\s*[\"']?[A-Za-z0-9]{20,}"),
]
_PII_PATTERNS = [
    re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)"),
    re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}"),
]
_MATERIAL_FIELDS = [
    "record_type",
    "item_id",
    "business_object",
    "title",
    "question",
    "standard_answer",
    "source_uri",
    "expected_behavior",
    "forbidden_terms",
    "handoff_condition",
    "desensitization_note",
]
_QUESTION_FIELDS = [
    "question_id",
    "question",
    "expected_answer",
    "expected_action",
    "source_uri",
    "business_object",
    "desensitization_note",
]
_REQUIRED_RECORD_TYPES = {
    "business_object",
    "standard_qa",
    "process_policy",
    "forbidden_commitment",
    "handoff_rule",
}
_VALID_MATERIAL_ACTIONS = {"answer_with_reference", "handoff", "reject_forbidden_commitment", "ask_clarifying_question"}
_OVERCLAIM_PHRASES = [
    "正式客户验收已完成",
    "客户正式签收已完成",
    "正式准确率签收已完成",
    "真实外发已开启",
    "真实外发已接通",
    "全渠道已接通",
    "生产 SLA 已完成",
    "签名安装包已完成",
]
_SUMMARY_MAX_AGE_SECONDS = 7 * 24 * 60 * 60
_REAL_CUSTOMER_MATERIAL_READY_STATUSES = {
    "customer_real_materials_ready",
    "real_customer_materials_ready",
    "customer_materials_ready_with_customer_data",
}
_REAL_KNOWLEDGE_RETEST_FACT_KEYS = {
    "kb6.real_customer_knowledge_retest",
    "kb7.customer_knowledge_retest",
    "customer_knowledge_retest",
}
_REAL_KNOWLEDGE_RETEST_READY_STATUSES = {
    "customer_knowledge_retest_ready_with_customer_data",
    "real_customer_knowledge_retest_passed",
    "passed_with_customer_data",
}
_CONFIRMATION_FACT_KEYS = {
    "pilot2.knowledge_confirmation_import",
    "knowledge_confirmation.import",
}
_CONFIRMATION_READY_STATUSES = {
    "passed",
    "passed_with_notes",
    "ready_for_next_retest",
}


def _require_same_tenant(tenant: Tenant, principal: CurrentPrincipal) -> None:
    if principal.tenant.id != tenant.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="tenant not found")


def _count(db: Session, model: type, tenant_id: int) -> int:
    return int(db.scalar(select(func.count(model.id)).where(model.tenant_id == tenant_id)) or 0)


def _latest_audit_event(db: Session, tenant_id: int, action: str) -> AuditEvent | None:
    return db.scalar(
        select(AuditEvent)
        .where(AuditEvent.tenant_id == tenant_id, AuditEvent.action == action)
        .order_by(AuditEvent.created_at.desc(), AuditEvent.id.desc())
    )


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _pilot_fact_read(fact: PilotReadinessFact) -> PilotRuntimeFactRead:
    return PilotRuntimeFactRead(
        fact_key=fact.fact_key,
        status=fact.status,
        source=fact.source,
        evidence_path=fact.evidence_path,
        payload=fact.payload or {},
        not_ready_for=fact.not_ready_for or [],
        created_at=fact.created_at,
        updated_at=fact.updated_at,
    )


def _material_batch_read(batch: CustomerMaterialBatch) -> CustomerMaterialBatchRead:
    return CustomerMaterialBatchRead(
        id=batch.id,
        batch_code=batch.batch_code,
        status=batch.status,
        material_row_count=batch.material_row_count,
        question_count=batch.question_count,
        record_type_coverage=batch.record_type_coverage or [],
        question_action_coverage=batch.question_action_coverage or [],
        blocker_count=batch.blocker_count,
        desensitization_risk_count=batch.desensitization_risk_count,
        created_at=batch.created_at,
    )


def _latest_runtime_facts(db: Session, tenant_id: int) -> list[PilotReadinessFact]:
    return list(
        db.scalars(
            select(PilotReadinessFact)
            .where(PilotReadinessFact.tenant_id == tenant_id)
            .order_by(PilotReadinessFact.updated_at.desc(), PilotReadinessFact.id.desc())
            .limit(30)
        )
    )


def _latest_material_batch(db: Session, tenant_id: int) -> CustomerMaterialBatch | None:
    return db.scalar(
        select(CustomerMaterialBatch)
        .where(CustomerMaterialBatch.tenant_id == tenant_id)
        .order_by(CustomerMaterialBatch.created_at.desc(), CustomerMaterialBatch.id.desc())
    )


def _material_batches(db: Session, tenant_id: int, limit: int = 12) -> list[CustomerMaterialBatch]:
    return list(
        db.scalars(
            select(CustomerMaterialBatch)
            .where(CustomerMaterialBatch.tenant_id == tenant_id)
            .order_by(CustomerMaterialBatch.created_at.desc(), CustomerMaterialBatch.id.desc())
            .limit(limit)
        )
    )


def _upsert_pilot_fact(
    db: Session,
    *,
    tenant_id: int,
    fact_key: str,
    status_value: str,
    principal: CurrentPrincipal,
    source: str = "database",
    evidence_path: str = "",
    payload: dict[str, Any] | None = None,
    not_ready_for: list[str] | None = None,
) -> PilotReadinessFact:
    now = utc_now()
    fact = db.scalar(
        select(PilotReadinessFact).where(
            PilotReadinessFact.tenant_id == tenant_id,
            PilotReadinessFact.fact_key == fact_key,
        )
    )
    if fact is None:
        fact = PilotReadinessFact(
            tenant_id=tenant_id,
            fact_key=fact_key,
            status=status_value,
            source=source,
            evidence_path=evidence_path,
            payload=payload or {},
            not_ready_for=not_ready_for or [],
            created_by_id=principal.user.id,
            created_at=now,
            updated_at=now,
        )
        db.add(fact)
        return fact

    fact.status = status_value
    fact.source = source
    fact.evidence_path = evidence_path
    fact.payload = payload or {}
    fact.not_ready_for = not_ready_for or []
    fact.created_by_id = principal.user.id
    fact.updated_at = now
    return fact


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def _read_summary_status(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {
            "path": _display_path(path),
            "status": "missing",
            "present": False,
            "blocker_count": 0,
            "authority": "engineering_evidence_only",
        }
    try:
        raw_text = path.read_text(encoding="utf-8")
        payload = json.loads(raw_text)
    except json.JSONDecodeError:
        return {
            "path": _display_path(path),
            "status": "invalid_json",
            "present": True,
            "blocker_count": 1,
            "authority": "engineering_evidence_only",
        }
    stat = path.stat()
    age_seconds = max(0, int(utc_now().timestamp() - stat.st_mtime))
    return {
        "path": _display_path(path),
        "status": str(payload.get("status") or "missing_status"),
        "present": True,
        "schema_version": str(payload.get("schema_version") or ""),
        "sha256": hashlib.sha256(raw_text.encode("utf-8")).hexdigest(),
        "age_seconds": age_seconds,
        "stale": age_seconds > _SUMMARY_MAX_AGE_SECONDS,
        "blocker_count": len(payload.get("blockers", [])) if isinstance(payload.get("blockers"), list) else 0,
        "authority": "engineering_evidence_only",
    }


def _trial_closure_evidence() -> tuple[str, list[dict[str, Any]], str]:
    evidence = [{"code": code, **_read_summary_status(path)} for code, path in TRIAL_CLOSURE_SUMMARY_PATHS.items()]
    statuses = {item["code"]: item["status"] for item in evidence}
    ready_statuses = {
        "trial_c0": {"trial_scope_ready"},
        "data1": {"customer_materials_ready", "internal_sample_only_ready"},
        "deploy1": {"clean_local_trial_rehearsal_passed"},
        "kb5": {"customer_knowledge_retest_ready_with_customer_data", "customer_knowledge_retest_ready_with_internal_data"},
        "trial2": {"shadow_trial_ready_with_customer_data", "shadow_trial_ready_with_internal_data"},
        "fe8": {"trial_frontend_friction_resolved"},
        "pilot7": {
            "co_creation_trial_candidate_ready_with_internal_data",
            "co_creation_trial_candidate_ready_with_customer_data",
        },
        "fe7": {"passed_customer_trial_browser_smoke"},
        "kb4": {"customer_knowledge_trial_loop_ready"},
        "install5": {"local_startup_experience_ready"},
        "ops3": {"customer_trial_ops_loop_ready"},
        "pack7": {"co_creation_trial_handoff_archive_v2_candidate"},
        "pack8": {
            "co_creation_trial_package_v1_1_candidate_with_internal_data",
            "co_creation_trial_package_v1_1_candidate_with_customer_data",
        },
    }
    if any(item["status"] in {"missing", "invalid_json"} for item in evidence):
        status = "waiting_for_trial_closure_evidence"
    elif any(statuses[code] not in expected for code, expected in ready_statuses.items()):
        status = "blocked"
    elif statuses.get("pack8") == "co_creation_trial_package_v1_1_candidate_with_customer_data":
        status = "co_creation_trial_v1_1_candidate_with_customer_data"
    elif statuses.get("pack8") == "co_creation_trial_package_v1_1_candidate_with_internal_data":
        status = "co_creation_trial_v1_1_candidate_with_internal_data"
    else:
        status = "co_creation_trial_v1_candidate"
    return status, evidence, statuses.get("pack8") or statuses.get("pack7", "not_generated")


def _real_customer_material_evidence() -> tuple[str, list[dict[str, Any]]]:
    status = _read_summary_status(REAL_CUSTOMER_MATERIAL_SUMMARY_PATH)
    return status["status"], [status]


def _five_gap_evidence() -> dict[str, tuple[str, list[dict[str, Any]]]]:
    return {
        code: (status["status"], [{"code": code, **status}])
        for code, path in FIVE_GAP_SUMMARY_PATHS.items()
        for status in [_read_summary_status(path)]
    }


def _int_or_zero(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _clean_set(values: Any) -> set[str]:
    if not isinstance(values, list):
        return set()
    return {str(value).strip() for value in values if str(value).strip()}


def _first_fact(
    runtime_facts_by_key: dict[str, PilotReadinessFact],
    fact_keys: set[str],
) -> PilotReadinessFact | None:
    for key in fact_keys:
        fact = runtime_facts_by_key.get(key)
        if fact is not None:
            return fact
    return None


def _customer_material_database_status(
    *,
    material_fact: PilotReadinessFact | None,
    latest_material_batch: CustomerMaterialBatch | None,
) -> tuple[bool, list[str], dict[str, Any]]:
    payload = material_fact.payload if material_fact is not None and isinstance(material_fact.payload, dict) else {}
    question_count = _int_or_zero(payload.get("question_count"))
    material_row_count = _int_or_zero(payload.get("material_row_count"))
    blocker_count = _int_or_zero(payload.get("blocker_count"))
    risk_count = _int_or_zero(payload.get("desensitization_risk_count"))
    record_coverage = _clean_set(payload.get("record_type_coverage"))
    action_coverage = _clean_set(payload.get("question_action_coverage"))

    if latest_material_batch is not None:
        question_count = question_count or latest_material_batch.question_count
        material_row_count = material_row_count or latest_material_batch.material_row_count
        blocker_count = max(blocker_count, latest_material_batch.blocker_count)
        risk_count = max(risk_count, latest_material_batch.desensitization_risk_count)
        record_coverage = record_coverage or _clean_set(latest_material_batch.record_type_coverage)
        action_coverage = action_coverage or _clean_set(latest_material_batch.question_action_coverage)

    status_value = material_fact.status if material_fact is not None else ""
    material_ready = (
        status_value in _REAL_CUSTOMER_MATERIAL_READY_STATUSES
        or payload.get("real_customer_materials_ready") is True
    )
    missing_record_types = sorted(_REQUIRED_RECORD_TYPES - record_coverage)
    invalid_actions = sorted(action_coverage - _VALID_MATERIAL_ACTIONS)
    blockers: list[str] = []
    if not material_ready:
        blockers.append("真实资料批次尚未由数据库事实标记为 ready")
    if material_row_count <= 0:
        blockers.append("真实知识资料行数不足")
    if question_count < 50:
        blockers.append(f"真实题库不足 50 条：当前 {question_count} 条")
    if missing_record_types:
        blockers.append(f"四层知识资料缺少类型：{', '.join(missing_record_types)}")
    if invalid_actions:
        blockers.append(f"题库 expected_action 存在非法值：{', '.join(invalid_actions)}")
    if blocker_count > 0:
        blockers.append(f"资料批次仍有 {blocker_count} 个阻断项")
    if risk_count > 0:
        blockers.append(f"资料批次仍有 {risk_count} 个脱敏或敏感信息风险")

    evidence = {
        "source": "database_fact",
        "fact_key": material_fact.fact_key if material_fact is not None else "missing",
        "status": status_value or "missing",
        "batch_id": latest_material_batch.id if latest_material_batch is not None else None,
        "question_count": question_count,
        "material_row_count": material_row_count,
        "record_type_coverage": sorted(record_coverage),
        "question_action_coverage": sorted(action_coverage),
        "blocker_count": blocker_count,
        "desensitization_risk_count": risk_count,
    }
    return not blockers, blockers, evidence


def _customer_data_readiness_from_database(
    *,
    runtime_facts_by_key: dict[str, PilotReadinessFact],
    latest_material_batch: CustomerMaterialBatch | None,
) -> dict[str, Any]:
    material_fact = runtime_facts_by_key.get("data3.customer_material_batch")
    material_ready, material_blockers, material_evidence = _customer_material_database_status(
        material_fact=material_fact,
        latest_material_batch=latest_material_batch,
    )
    retest_fact = _first_fact(runtime_facts_by_key, _REAL_KNOWLEDGE_RETEST_FACT_KEYS)
    retest_payload = retest_fact.payload if retest_fact is not None and isinstance(retest_fact.payload, dict) else {}
    retest_ready = (
        retest_fact is not None
        and retest_fact.status in _REAL_KNOWLEDGE_RETEST_READY_STATUSES
        and retest_payload.get("customer_data_used") is not False
    )
    confirmation_fact = _first_fact(runtime_facts_by_key, _CONFIRMATION_FACT_KEYS)
    confirmation_payload = (
        confirmation_fact.payload if confirmation_fact is not None and isinstance(confirmation_fact.payload, dict) else {}
    )
    confirmation_ready = (
        confirmation_fact is not None
        and confirmation_fact.status in _CONFIRMATION_READY_STATUSES
        and _int_or_zero(confirmation_payload.get("total_rows")) > 0
        and _int_or_zero(confirmation_payload.get("sensitive_risk_count")) == 0
    )

    blockers = list(material_blockers)
    if not retest_ready:
        blockers.append("真实客户知识复测尚未以数据库 fact 标记通过")
    if not confirmation_ready:
        blockers.append("客户确认导入尚未以数据库 fact 标记为通过或带备注通过")

    evidence = [
        material_evidence,
        {
            "source": "database_fact",
            "fact_key": retest_fact.fact_key if retest_fact is not None else "missing",
            "status": retest_fact.status if retest_fact is not None else "missing",
            "customer_data_used": retest_payload.get("customer_data_used") if retest_fact is not None else None,
        },
        {
            "source": "database_fact",
            "fact_key": confirmation_fact.fact_key if confirmation_fact is not None else "missing",
            "status": confirmation_fact.status if confirmation_fact is not None else "missing",
            "total_rows": confirmation_payload.get("total_rows") if confirmation_fact is not None else None,
            "sensitive_risk_count": confirmation_payload.get("sensitive_risk_count")
            if confirmation_fact is not None
            else None,
        },
    ]
    return {
        "ready": not blockers,
        "source": "database_fact_chain",
        "blockers": sorted(set(blockers)),
        "evidence": evidence,
        "material_ready": material_ready,
        "retest_ready": retest_ready,
        "confirmation_ready": confirmation_ready,
    }


def _step(
    code: str,
    title: str,
    status_value: str,
    summary: str,
    next_action: str,
    target_href: str,
    *,
    blockers: list[str] | None = None,
    evidence: list[dict[str, Any]] | None = None,
) -> PilotReadinessStepRead:
    return PilotReadinessStepRead(
        code=code,
        title=title,
        status=status_value,
        summary=summary,
        next_action=next_action,
        target_href=target_href,
        blockers=blockers or [],
        evidence=evidence or [],
    )


def build_pilot_readiness(
    db: Session,
    *,
    tenant_id: int,
    principal: CurrentPrincipal,
) -> PilotReadinessRead:
    tenant = require_tenant(db, tenant_id)
    _require_same_tenant(tenant, principal)

    maintenance = build_local_maintenance_readiness(db, tenant=tenant)
    maintenance_ready = maintenance.get("ready_for_customer_maintenance_rehearsal") is True
    maintenance_blockers = [str(item) for item in maintenance.get("blockers", [])]
    owner_count = int(
        db.scalar(select(func.count(User.id)).where(User.tenant_id == tenant.id, User.status == "active")) or 0
    )
    business_object_count = _count(db, BusinessObject, tenant.id)
    knowledge_document_count = _count(db, KnowledgeDocument, tenant.id)
    evaluation_set_count = _count(db, KnowledgeEvaluationSet, tenant.id)
    evaluation_case_count = _count(db, KnowledgeEvaluationCase, tenant.id)
    evaluation_run_count = _count(db, KnowledgeEvaluationRun, tenant.id)
    confirmation_event = _latest_audit_event(db, tenant.id, "knowledge_confirmation.imported")
    monthly_ops_event = _latest_audit_event(db, tenant.id, "monthly_ops_report.generated")
    trial_closure_status, trial_closure_evidence, handoff_archive_status = _trial_closure_evidence()
    real_customer_material_status, real_customer_material_evidence = _real_customer_material_evidence()
    five_gap_evidence = _five_gap_evidence()
    runtime_fact_records = _latest_runtime_facts(db, tenant.id)
    runtime_facts = [_pilot_fact_read(fact) for fact in runtime_fact_records]
    runtime_facts_by_key = {fact.fact_key: fact for fact in runtime_fact_records}
    latest_material_batch = _latest_material_batch(db, tenant.id)
    latest_material_batch_read = _material_batch_read(latest_material_batch) if latest_material_batch else None

    material_fact = runtime_facts_by_key.get("data3.customer_material_batch")
    if material_fact is not None:
        real_customer_material_status = material_fact.status
        real_customer_material_evidence = [
            {
                "source": "database_fact",
                "fact_key": material_fact.fact_key,
                "status": material_fact.status,
                "batch_code": (material_fact.payload or {}).get("batch_code"),
                "question_count": (material_fact.payload or {}).get("question_count"),
                "blocker_count": (material_fact.payload or {}).get("blocker_count"),
            }
        ]

    customer_data_readiness = _customer_data_readiness_from_database(
        runtime_facts_by_key=runtime_facts_by_key,
        latest_material_batch=latest_material_batch,
    )
    confirmation_fact = _first_fact(runtime_facts_by_key, _CONFIRMATION_FACT_KEYS)
    confirmation_fact_ready = bool(customer_data_readiness["confirmation_ready"])
    retest_fact_ready = bool(customer_data_readiness["retest_ready"])

    local_ready = maintenance.get("maturity_status") != "blocked"
    knowledge_ready = business_object_count > 0 and knowledge_document_count > 0
    retest_ready = evaluation_case_count >= 50 and evaluation_run_count > 0
    customer_confirmation_ready = confirmation_fact_ready
    quality_ready = evaluation_run_count > 0

    steps = [
        _step(
            "local_environment",
            "本地环境",
            "ready" if local_ready else "blocked",
            "本地环境保持真实外发关闭，维护动作需要人工确认。" if local_ready else "本地环境存在阻断项。",
            "进入账号与本地维护，先处理本地环境阻断。",
            "#settings",
            blockers=maintenance_blockers if not local_ready else [],
            evidence=[{"source": "local_maintenance_readiness", "status": maintenance.get("maturity_status")}],
        ),
        _step(
            "owner_account",
            "账号负责人",
            "ready" if owner_count > 0 else "blocked",
            f"当前租户已有 {owner_count} 个启用账号。" if owner_count > 0 else "还没有可登录负责人账号。",
            "创建首任负责人或由负责人新增本地人员。",
            "#settings",
            blockers=[] if owner_count > 0 else ["缺少启用账号"],
            evidence=[{"source": "users", "active_user_count": owner_count}],
        ),
        _step(
            "knowledge_materials",
            "知识资料",
            "ready" if knowledge_ready else "pending",
            f"业务对象 {business_object_count} 个，知识文档 {knowledge_document_count} 份。"
            if knowledge_ready
            else "需要先导入业务对象、标准问答、流程政策和边界规则。",
            "进入知识库运营，导入或补齐资料。",
            "#knowledge",
            blockers=[] if knowledge_ready else ["知识资料不足"],
            evidence=[
                {"source": "business_objects", "count": business_object_count},
                {"source": "knowledge_documents", "count": knowledge_document_count},
            ],
        ),
        _step(
            "retest_confirmation",
            "复测确认",
            "ready" if customer_confirmation_ready else "pending" if retest_ready else "blocked",
            "已有客户回填确认记录，可进入下一轮复测。"
            if customer_confirmation_ready
            else "内部题库可复测，但客户回填确认尚未导入。"
            if retest_ready
            else "需要先准备至少 50 条脱敏题并完成复测。",
            "进入知识评测，导入客户确认表或继续准备题库。",
            "#evals",
            blockers=[] if customer_confirmation_ready else ["等待客户确认回填"] if retest_ready else ["复测题库或运行证据不足"],
            evidence=[
                {"source": "evaluation_cases", "count": evaluation_case_count},
                {"source": "evaluation_runs", "count": evaluation_run_count},
                {
                    "source": "knowledge_retest_fact",
                    "exists": retest_fact_ready,
                    "status": customer_data_readiness["evidence"][1].get("status"),
                },
                {
                    "source": "knowledge_confirmation_import_fact",
                    "exists": customer_confirmation_ready,
                    "status": confirmation_fact.status if confirmation_fact is not None else "missing",
                },
                {"source": "knowledge_confirmation_import_audit", "exists": confirmation_event is not None},
            ],
        ),
        _step(
            "quality_monthly_ops",
            "质量与月报",
            "ready" if quality_ready else "pending",
            "已有质量运行证据，可生成客户可读的月度运维报告。"
            if quality_ready
            else "需要先跑题库复测，才能生成有意义的质量与月报。",
            "进入质量复盘查看月度报告。",
            "#quality",
            blockers=[] if quality_ready else ["缺少质量运行证据"],
            evidence=[
                {"source": "evaluation_runs", "count": evaluation_run_count},
                {"source": "monthly_ops_report", "exists": monthly_ops_event is not None},
            ],
        ),
        _step(
            "diagnostics_backup_update",
            "诊断、备份与更新",
            "ready" if maintenance_ready else "pending",
            maintenance.get("summary", "汇总诊断包、备份、更新和恢复演练证据。"),
            "进入账号与本地维护，补齐诊断包、备份、更新预检和恢复演练。",
            "#settings",
            blockers=maintenance_blockers if not maintenance_ready else [],
            evidence=[{"source": "local_maintenance_counts", "counts": maintenance.get("counts", {})}],
        ),
    ]

    blockers: list[str] = []
    for item in steps:
        if item.status == "blocked":
            blockers.extend(item.blockers)

    customer_data_ready = bool(customer_data_readiness["ready"])
    if blockers:
        readiness_status = "blocked"
        status_label = "存在阻断"
    elif customer_data_ready:
        readiness_status = "pilot_candidate_ready_with_customer_data"
        status_label = "客户资料试点候选"
    else:
        readiness_status = "pilot_candidate_ready_with_internal_data"
        status_label = "内部资料试点候选"

    return PilotReadinessRead(
        schema_version=PILOT_READINESS_SCHEMA_VERSION,
        tenant_id=tenant.id,
        generated_at=utc_now(),
        status=readiness_status,
        status_label=status_label,
        summary=(
            "当前可作为共创客户本地试点包候选，但仍不是成熟商用全渠道客服系统。"
            if readiness_status != "blocked"
            else "当前还存在阻断项，不能封版为试点包候选。"
        ),
        steps=steps,
        blockers=sorted(set(blockers)),
        evidence_links=[
            {"label": "知识库运营", "href": "#knowledge"},
            {"label": "知识评测", "href": "#evals"},
            {"label": "质量复盘", "href": "#quality"},
            {"label": "账号与本地维护", "href": "#settings"},
        ],
        not_ready_for=[
            "正式客户验收签收",
            "真实平台自动外发",
            "企业微信、抖音、淘宝、京东、拼多多等真实渠道接通",
            "生产 SLA 承诺",
            "已签名 dmg/exe 安装器",
        ],
        safety={
            "real_platform_send_enabled": False,
            "rpa_formal_delivery_enabled": False,
            "remote_control_enabled": False,
            "silent_update_enabled": False,
            "internal_rehearsal_not_formal_signoff": readiness_status != "pilot_candidate_ready_with_customer_data",
        },
        recommended_next_steps=[
            "将真实客户脱敏资料放入 DATA2 接收目录，重跑资料、知识复测和影子试跑门禁。",
            "用客户回填确认表替换内部确认材料。",
            "每次知识发布后固定复测并生成月度运维报告。",
            "封版前导出非敏感试点交付档案。",
        ],
        trial_closure_status=trial_closure_status,
        trial_closure_evidence=trial_closure_evidence,
        handoff_archive_status=handoff_archive_status,
        pack8_status=handoff_archive_status if "v1_1" in handoff_archive_status else "not_generated",
        pack8_evidence=[
            item
            for item in trial_closure_evidence
            if item.get("code") in {"trial_c0", "data1", "deploy1", "kb5", "trial2", "fe8", "pack8"}
        ],
        material_intake_package_status=five_gap_evidence["material_intake_package"][0],
        material_intake_package_evidence=five_gap_evidence["material_intake_package"][1],
        material_validation_fixture_status=five_gap_evidence["material_validation_fixtures"][0],
        material_validation_fixture_evidence=five_gap_evidence["material_validation_fixtures"][1],
        material_drop_gate_status=five_gap_evidence["material_drop_gate"][0],
        material_drop_gate_evidence=five_gap_evidence["material_drop_gate"][1],
        real_customer_material_status=real_customer_material_status,
        real_customer_material_evidence=real_customer_material_evidence,
        customer_knowledge_retest_status=five_gap_evidence["customer_knowledge_retest"][0],
        customer_knowledge_retest_evidence=five_gap_evidence["customer_knowledge_retest"][1],
        shadow_trial_status=five_gap_evidence["shadow_trial"][0],
        shadow_trial_evidence=five_gap_evidence["shadow_trial"][1],
        frontend_customer_qa_status=five_gap_evidence["frontend_customer_qa"][0],
        frontend_customer_qa_evidence=five_gap_evidence["frontend_customer_qa"][1],
        frontend_product_polish_status=five_gap_evidence["frontend_product_polish"][0],
        frontend_product_polish_evidence=five_gap_evidence["frontend_product_polish"][1],
        channel_boundary_status=five_gap_evidence["channel_boundary"][0],
        channel_boundary_evidence=five_gap_evidence["channel_boundary"][1],
        installer_trial_status=five_gap_evidence["installer_trial"][0],
        installer_trial_evidence=five_gap_evidence["installer_trial"][1],
        pack10_status=five_gap_evidence["pack10"][0],
        pack10_evidence=five_gap_evidence["pack10"][1],
        runtime_facts=runtime_facts,
        latest_material_batch=latest_material_batch_read,
        customer_data_ready=customer_data_ready,
        customer_data_readiness_source=customer_data_readiness["source"],
        customer_data_ready_blockers=customer_data_readiness["blockers"],
        customer_data_ready_evidence=customer_data_readiness["evidence"],
        summary_evidence_authority="engineering_evidence_only",
    )


def _value(row: dict[str, str], *names: str) -> str:
    normalized = {key.strip().lower(): value.strip() for key, value in row.items() if key is not None}
    for name in names:
        value = normalized.get(name.lower())
        if value is not None:
            return value
    return ""


def _status_bucket(raw_status: str) -> str:
    status_value = raw_status.strip().lower()
    if raw_status in _CONFIRMED_STATUSES or status_value in _CONFIRMED_STATUSES:
        return "confirmed"
    if raw_status in _ACCEPTED_WITH_NOTES_STATUSES or status_value in _ACCEPTED_WITH_NOTES_STATUSES:
        return "accepted_with_notes"
    if raw_status in _REVISION_STATUSES or status_value in _REVISION_STATUSES:
        return "needs_revision"
    if raw_status in _REJECTED_STATUSES or status_value in _REJECTED_STATUSES:
        return "rejected"
    if raw_status in _PENDING_STATUSES or status_value in _PENDING_STATUSES:
        return "pending"
    return "unknown"


def _bool_from_csv(value: str) -> bool:
    return value.strip().lower() in {"true", "1", "yes", "y", "是", "需要", "需修改"}


def _sensitive_findings(row: dict[str, str], row_index: int) -> list[str]:
    joined = " ".join(str(value or "") for value in row.values())
    findings: list[str] = []
    for pattern in _SEVERE_SECRET_PATTERNS:
        if pattern.search(joined):
            findings.append(f"第 {row_index} 行包含疑似密钥或密码形态")
    for pattern in _PII_PATTERNS:
        if pattern.search(joined):
            findings.append(f"第 {row_index} 行包含疑似个人联系方式")
    return findings


def _raw_text_findings(label: str, text: str) -> list[str]:
    findings: list[str] = []
    for pattern in _SEVERE_SECRET_PATTERNS:
        if pattern.search(text):
            findings.append(f"{label} 包含疑似密钥、密码或 token 字段")
            break
    for pattern in _PII_PATTERNS:
        if pattern.search(text):
            findings.append(f"{label} 包含疑似个人联系方式")
            break
    for phrase in _OVERCLAIM_PHRASES:
        if phrase in text:
            findings.append(f"{label} 包含越界承诺：{phrase}")
    return findings


def _csv_rows_from_text(csv_text: str) -> tuple[list[str], list[dict[str, str]]]:
    reader = csv.DictReader(io.StringIO(csv_text))
    return [field or "" for field in (reader.fieldnames or [])], list(reader)


def _row_has_values(row: dict[str, str], fields: list[str]) -> bool:
    return all(str(row.get(field, "")).strip() for field in fields)


def _csv_text(fieldnames: list[str], rows: list[dict[str, Any]]) -> str:
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({field: row.get(field, "") for field in fieldnames})
    return output.getvalue()


def _material_template_rows() -> list[dict[str, str]]:
    return [
        {
            "record_type": "standard_qa",
            "item_id": "QA-001",
            "business_object": "产品或服务名称",
            "title": "客户会问的问题主题",
            "question": "客户常见问法",
            "standard_answer": "确认后的标准答法",
            "source_uri": "资料来源名称或页码",
            "expected_behavior": "引用资料后回答",
            "forbidden_terms": "不能承诺的词语",
            "handoff_condition": "需要转人工的条件",
            "desensitization_note": "已脱敏",
        }
    ]


def _sample_material_rows() -> list[dict[str, str]]:
    return [
        {
            "record_type": "business_object",
            "item_id": "BO-001",
            "business_object": "基础咨询套餐",
            "title": "业务对象说明",
            "question": "基础咨询套餐包含什么",
            "standard_answer": "基础咨询套餐包含需求沟通、资料整理和一次标准答疑，具体范围以确认后的服务清单为准。",
            "source_uri": "样板资料-服务清单-第1页",
            "expected_behavior": "说明服务范围并提示以确认清单为准",
            "forbidden_terms": "保证成交;永久有效",
            "handoff_condition": "客户要求合同外承诺",
            "desensitization_note": "样板内容，无真实客户信息",
        },
        {
            "record_type": "standard_qa",
            "item_id": "QA-001",
            "business_object": "基础咨询套餐",
            "title": "价格咨询",
            "question": "基础咨询套餐多少钱",
            "standard_answer": "基础咨询套餐的试跑价为 1980 元起，最终价格需要根据资料量和服务范围确认。",
            "source_uri": "样板资料-报价说明-第2页",
            "expected_behavior": "给出起步价并说明需要确认范围",
            "forbidden_terms": "最低价;全网最低",
            "handoff_condition": "客户要求定制报价",
            "desensitization_note": "样板内容，无真实客户信息",
        },
        {
            "record_type": "process_policy",
            "item_id": "POL-001",
            "business_object": "售后流程",
            "title": "售后处理",
            "question": "售后问题怎么处理",
            "standard_answer": "售后问题先记录订单信息和问题类型，再由负责人确认处理方式；涉及退款、赔付或合同变更时转人工。",
            "source_uri": "样板资料-售后政策-第3页",
            "expected_behavior": "先说明流程，再识别是否转人工",
            "forbidden_terms": "立即赔付;无条件退款",
            "handoff_condition": "涉及退款、赔付、投诉升级",
            "desensitization_note": "样板内容，无真实客户信息",
        },
        {
            "record_type": "forbidden_commitment",
            "item_id": "FORBID-001",
            "business_object": "服务边界",
            "title": "禁用承诺",
            "question": "能不能保证一定有效",
            "standard_answer": "不能承诺绝对结果。可以说明服务会按确认流程执行，并建议由人工进一步确认具体条件。",
            "source_uri": "样板资料-服务边界-第4页",
            "expected_behavior": "拒绝绝对化承诺并转向可确认事实",
            "forbidden_terms": "保证一定有效;百分百成功;永久无风险",
            "handoff_condition": "客户持续要求绝对承诺",
            "desensitization_note": "样板内容，无真实客户信息",
        },
        {
            "record_type": "handoff_rule",
            "item_id": "HANDOFF-001",
            "business_object": "人工处理",
            "title": "转人工规则",
            "question": "什么情况需要人工处理",
            "standard_answer": "涉及合同、退款、投诉、价格例外、客户身份核验或资料不完整时，应进入人工处理。",
            "source_uri": "样板资料-转人工规则-第5页",
            "expected_behavior": "识别风险并进入人工处理",
            "forbidden_terms": "自动代签;自动退款",
            "handoff_condition": "合同、退款、投诉、价格例外、身份核验、资料不完整",
            "desensitization_note": "样板内容，无真实客户信息",
        },
    ]


def _question_template_rows() -> list[dict[str, str]]:
    return [
        {
            "question_id": "Q-001",
            "question": "客户脱敏后的真实问法",
            "expected_answer": "确认后的标准答案",
            "expected_action": "answer_with_reference",
            "source_uri": "资料来源名称或页码",
            "business_object": "产品或服务名称",
            "desensitization_note": "已脱敏",
        }
    ]


def _sample_question_rows(count: int = 50) -> list[dict[str, str]]:
    scenarios = [
        (
            "answer_with_reference",
            "基础咨询套餐多少钱",
            "基础咨询套餐的试跑价为 1980 元起，最终价格需要根据资料量和服务范围确认。",
            "基础咨询套餐",
            "样板资料-报价说明-第2页",
        ),
        (
            "handoff",
            "我这边要做合同外的特殊承诺，可以直接答应吗",
            "涉及合同外承诺时需要进入人工处理，不能由系统直接承诺。",
            "服务边界",
            "样板资料-服务边界-第4页",
        ),
        (
            "reject_forbidden_commitment",
            "你们能不能保证百分百成功",
            "不能承诺绝对结果，只能说明已确认的服务流程和可交付范围。",
            "服务边界",
            "样板资料-服务边界-第4页",
        ),
        (
            "ask_clarifying_question",
            "这个怎么弄",
            "需要先确认客户指的是套餐、售后、报价还是资料提交。",
            "基础咨询套餐",
            "样板资料-服务清单-第1页",
        ),
    ]
    rows: list[dict[str, str]] = []
    for index in range(1, count + 1):
        action, question, answer, business_object, source_uri = scenarios[(index - 1) % len(scenarios)]
        rows.append(
            {
                "question_id": f"Q-{index:03d}",
                "question": f"{question}（样板问题 {index:02d}）",
                "expected_answer": answer,
                "expected_action": action,
                "source_uri": source_uri,
                "business_object": business_object,
                "desensitization_note": "样板内容，无真实客户信息",
            }
        )
    return rows


def _template_manifest(customer_data_used: bool) -> dict[str, Any]:
    return {
        "customer_data_used": customer_data_used,
        "customer_alias": "样板客户A",
        "provided_by_role": "客户负责人",
        "provided_at": "2026-07-05T00:00:00+08:00",
        "desensitization_owner_role": "客户资料整理人",
        "desensitization_statement": "资料已完成脱敏，不包含真实个人联系方式、账号、密钥或平台消息原文。",
        "real_platform_send_enabled": False,
        "formal_customer_signoff_ready": False,
        "notes": "示例仅用于熟悉格式；真实试跑必须替换为客户确认后的脱敏资料。",
    }


def _customer_material_field_guide() -> list[dict[str, Any]]:
    return [
        {
            "file": "customer_materials_received.csv",
            "field": "record_type",
            "required": True,
            "description": "资料类型，可填写 business_object、standard_qa、process_policy、forbidden_commitment、handoff_rule。",
            "example": "standard_qa",
        },
        {
            "file": "customer_materials_received.csv",
            "field": "item_id",
            "required": True,
            "description": "资料条目的唯一编号，建议按类型递增。",
            "example": "QA-001",
        },
        {
            "file": "customer_materials_received.csv",
            "field": "business_object",
            "required": True,
            "description": "该条资料对应的产品、服务、门店、套餐或流程名称。",
            "example": "基础咨询套餐",
        },
        {
            "file": "customer_materials_received.csv",
            "field": "standard_answer",
            "required": True,
            "description": "客户已确认可以对外使用的标准答法。",
            "example": "基础咨询套餐包含需求沟通、资料整理和一次标准答疑。",
        },
        {
            "file": "customer_materials_received.csv",
            "field": "source_uri",
            "required": True,
            "description": "答案依据来源，可填写文件名、页码、内部资料编号或政策名称。",
            "example": "样板资料-服务清单-第1页",
        },
        {
            "file": "customer_materials_received.csv",
            "field": "forbidden_terms",
            "required": False,
            "description": "系统不能复述或承诺的词语，多项可用分号分隔。",
            "example": "保证成交;永久有效",
        },
        {
            "file": "customer_materials_received.csv",
            "field": "handoff_condition",
            "required": False,
            "description": "需要进入人工处理的条件。",
            "example": "涉及退款、投诉、合同例外",
        },
        {
            "file": "customer_trial_questions_received.csv",
            "field": "question_id",
            "required": True,
            "description": "试跑问题编号，必须唯一。",
            "example": "Q-001",
        },
        {
            "file": "customer_trial_questions_received.csv",
            "field": "question",
            "required": True,
            "description": "脱敏后的客户真实问法或准真实试跑问法。",
            "example": "基础咨询套餐多少钱",
        },
        {
            "file": "customer_trial_questions_received.csv",
            "field": "expected_action",
            "required": True,
            "description": "期望处理方式，可填写 answer_with_reference、handoff、reject_forbidden_commitment、ask_clarifying_question。",
            "example": "answer_with_reference",
        },
        {
            "file": "customer_material_manifest_received.json",
            "field": "desensitization_statement",
            "required": True,
            "description": "客户资料整理人对脱敏状态的说明。",
            "example": "资料已完成脱敏，不包含真实联系方式、账号或密钥。",
        },
    ]


def get_customer_material_template_package(
    db: Session,
    *,
    tenant_id: int,
    principal: CurrentPrincipal,
) -> CustomerMaterialTemplatePackageRead:
    tenant = require_tenant(db, tenant_id)
    _require_same_tenant(tenant, principal)

    return CustomerMaterialTemplatePackageRead(
        schema_version=CUSTOMER_MATERIAL_TEMPLATE_PACKAGE_SCHEMA_VERSION,
        tenant_id=tenant.id,
        generated_at=utc_now(),
        status="material_template_package_ready",
        summary="资料模板包已生成；示例仅用于熟悉格式，不代表真实客户资料已就绪。",
        materials_template_csv=_csv_text(_MATERIAL_FIELDS, _material_template_rows()),
        trial_questions_template_csv=_csv_text(_QUESTION_FIELDS, _question_template_rows()),
        manifest_template_json=json.dumps(_template_manifest(customer_data_used=False), ensure_ascii=False, indent=2),
        sample_materials_csv=_csv_text(_MATERIAL_FIELDS, _sample_material_rows()),
        sample_trial_questions_csv=_csv_text(_QUESTION_FIELDS, _sample_question_rows()),
        sample_manifest_json=json.dumps(_template_manifest(customer_data_used=True), ensure_ascii=False, indent=2),
        required_received_filenames={
            "materials_csv": "customer_materials_received.csv",
            "trial_questions_csv": "customer_trial_questions_received.csv",
            "manifest_json": "customer_material_manifest_received.json",
        },
        field_guide=_customer_material_field_guide(),
        next_steps=[
            "下载模板并替换示例内容。",
            "至少准备 50 条脱敏试跑问题。",
            "粘贴到资料预检区修正阻断项。",
            "确认无阻断后再按固定文件名放入真实资料接收目录。",
        ],
        readiness={
            "material_template_package_ready": True,
            "raw_materials_persisted": False,
            "real_customer_materials_ready": False,
            "real_platform_send_ready": False,
            "formal_customer_signoff_ready": False,
        },
        safety={
            "sample_package_is_customer_data": False,
            "raw_materials_persisted": False,
            "real_platform_send_performed": False,
            "formal_customer_signoff_ready": False,
        },
    )


def _customer_material_handoff_readme() -> str:
    return "\n".join(
        [
            "# 万法常世 AI 客服资料回传包",
            "",
            "请按包内三个固定文件名填写并回传，不要改名。",
            "",
            "## 文件说明",
            "",
            "- customer_materials_received.csv：填写产品、服务、标准问答、流程政策、禁用承诺和转人工规则。",
            "- customer_trial_questions_received.csv：填写 50-100 条脱敏试跑问题、期望答案、期望动作和来源。",
            "- customer_material_manifest_received.json：填写提供人角色、提供时间、脱敏责任人和脱敏说明。",
            "",
            "## 边界",
            "",
            "- 包内是示例内容和空模板，不代表真实客户资料已就绪。",
            "- 请不要填写手机号、邮箱、账号密码、密钥、平台消息原文或未脱敏订单信息。",
            "- 真实外发默认关闭；资料回传后还需要经过预检、固定目录门禁、复测和客户确认。",
            "",
        ]
    )


def _customer_material_handoff_archive_bytes() -> bytes:
    files = {
        "customer_materials_received.csv": _csv_text(_MATERIAL_FIELDS, _material_template_rows()),
        "customer_trial_questions_received.csv": _csv_text(_QUESTION_FIELDS, _question_template_rows()),
        "customer_material_manifest_received.json": json.dumps(
            _template_manifest(customer_data_used=False),
            ensure_ascii=False,
            indent=2,
        ),
        "README.md": _customer_material_handoff_readme(),
    }
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for filename, body in files.items():
            archive.writestr(filename, body)
    return buffer.getvalue()


def get_customer_material_handoff_bundle(
    db: Session,
    *,
    tenant_id: int,
    principal: CurrentPrincipal,
) -> CustomerMaterialHandoffBundleRead:
    tenant = require_tenant(db, tenant_id)
    _require_same_tenant(tenant, principal)

    included_files = [
        "customer_materials_received.csv",
        "customer_trial_questions_received.csv",
        "customer_material_manifest_received.json",
        "README.md",
    ]
    archive_body = base64.b64encode(_customer_material_handoff_archive_bytes()).decode("ascii")

    return CustomerMaterialHandoffBundleRead(
        schema_version=CUSTOMER_MATERIAL_HANDOFF_BUNDLE_SCHEMA_VERSION,
        tenant_id=tenant.id,
        generated_at=utc_now(),
        status="material_handoff_bundle_ready",
        summary="资料回传包已生成；请替换示例内容后按固定文件名回传。",
        filename="wanfa-customer-material-handoff-bundle.zip",
        content_type="application/zip",
        body_encoding="base64",
        body=archive_body,
        included_files=included_files,
        required_received_filenames={
            "materials_csv": "customer_materials_received.csv",
            "trial_questions_csv": "customer_trial_questions_received.csv",
            "manifest_json": "customer_material_manifest_received.json",
        },
        next_steps=[
            "下载资料回传包。",
            "保持三个固定文件名不变。",
            "替换示例内容并完成脱敏检查。",
            "回传后再进入 DATA2 固定目录门禁。",
        ],
        readiness={
            "material_handoff_bundle_ready": True,
            "raw_materials_persisted": False,
            "real_customer_materials_ready": False,
            "real_platform_send_ready": False,
            "formal_customer_signoff_ready": False,
        },
        safety={
            "sample_package_is_customer_data": False,
            "raw_materials_persisted": False,
            "real_platform_send_performed": False,
            "formal_customer_signoff_ready": False,
        },
    )


def create_safe_test_conversation(
    db: Session,
    *,
    tenant_id: int,
    principal: CurrentPrincipal,
) -> SafeTestConversationRead:
    tenant = require_tenant(db, tenant_id)
    _require_same_tenant(tenant, principal)

    channel = db.scalar(
        select(Channel).where(
            Channel.tenant_id == tenant.id,
            Channel.type == "local_test",
            Channel.name == "本地安全测试入口",
        )
    )
    if channel is None:
        channel = Channel(
            tenant_id=tenant.id,
            type="local_test",
            name="本地安全测试入口",
            reply_mode="assist",
            status="active",
        )
        db.add(channel)
        db.flush()

    contact = db.scalar(
        select(Contact).where(
            Contact.tenant_id == tenant.id,
            Contact.display_name == "本地测试客户",
        )
    )
    if contact is None:
        contact = Contact(
            tenant_id=tenant.id,
            display_name="本地测试客户",
        )
        db.add(contact)
        db.flush()

    now = utc_now()
    conversation = Conversation(
        tenant_id=tenant.id,
        channel_id=channel.id,
        contact_id=contact.id,
        assigned_user_id=None,
        status="bot",
        priority="normal",
        subject="本地安全测试会话",
        last_message_at=now,
        created_at=now,
    )
    db.add(conversation)
    db.flush()

    message = Message(
        conversation_id=conversation.id,
        direction="inbound",
        sender_type="customer",
        content="你好，我想了解标准套餐包含什么、售后怎么处理，如果信息不确定能不能转人工？",
        external_message_id=f"local-safe-test-{tenant.id}-{conversation.id}",
        created_at=now,
    )
    db.add(message)
    db.flush()

    db.add(
        ConversationEvent(
            conversation_id=conversation.id,
            event_type="pilot.safe_test_conversation.created",
            actor_id=principal.user.id,
            payload=json.dumps(
                {
                    "schema_version": SAFE_TEST_CONVERSATION_SCHEMA_VERSION,
                    "channel_type": "local_test",
                    "external_write_performed": False,
                    "purpose": "local_customer_trial_smoke",
                },
                ensure_ascii=False,
            ),
            created_at=now,
        )
    )
    _upsert_pilot_fact(
        db,
        tenant_id=tenant.id,
        fact_key="fe11.safe_test_conversation",
        status_value="safe_test_conversation_available",
        source="database",
        evidence_path=f"conversations:{conversation.id}",
        payload={
            "conversation_id": conversation.id,
            "message_id": message.id,
            "channel_id": channel.id,
            "external_write_performed": False,
        },
        not_ready_for=["真实平台自动外发", "真实渠道上线"],
        principal=principal,
    )
    add_audit_event(
        db,
        tenant_id=tenant.id,
        actor_id=principal.user.id,
        action="pilot.safe_test_conversation.created",
        resource_type="conversation",
        resource_id=str(conversation.id),
        payload={
            "schema_version": SAFE_TEST_CONVERSATION_SCHEMA_VERSION,
            "channel_id": channel.id,
            "message_id": message.id,
            "external_write_performed": False,
            "raw_platform_payload_persisted": False,
        },
    )
    db.commit()
    return SafeTestConversationRead(
        schema_version=SAFE_TEST_CONVERSATION_SCHEMA_VERSION,
        tenant_id=tenant.id,
        conversation_id=conversation.id,
        message_id=message.id,
        channel_id=channel.id,
        contact_id=contact.id,
        target_href=f"#live?conversation={conversation.id}",
        summary="已生成一条本地安全测试会话；该会话只写入本地数据库，不触发真实平台外发。",
        external_write_performed=False,
        safety={
            "local_trial_only": True,
            "real_platform_send_enabled": False,
            "raw_platform_payload_persisted": False,
        },
    )


def precheck_customer_materials(
    db: Session,
    *,
    tenant_id: int,
    payload: CustomerMaterialPrecheckCreate,
    principal: CurrentPrincipal,
) -> CustomerMaterialPrecheckRead:
    tenant = require_tenant(db, tenant_id)
    _require_same_tenant(tenant, principal)

    blockers: list[str] = []
    material_fields, materials = _csv_rows_from_text(payload.materials_csv)
    question_fields, questions = _csv_rows_from_text(payload.trial_questions_csv)
    try:
        manifest = json.loads(payload.manifest_json)
    except json.JSONDecodeError:
        manifest = {}
        blockers.append("资料说明 JSON 不是有效 JSON")

    missing_material_fields = [field for field in _MATERIAL_FIELDS if field not in material_fields]
    missing_question_fields = [field for field in _QUESTION_FIELDS if field not in question_fields]
    if missing_material_fields:
        blockers.append(f"客户知识资料缺少字段：{', '.join(missing_material_fields)}")
    if missing_question_fields:
        blockers.append(f"客户试跑题库缺少字段：{', '.join(missing_question_fields)}")
    if not materials:
        blockers.append("客户知识资料为空")
    if len(questions) < 50:
        blockers.append(f"真实客户脱敏题库不足 50 条：当前 {len(questions)} 条")

    record_types = {row.get("record_type", "").strip() for row in materials if row.get("record_type")}
    missing_record_types = sorted(_REQUIRED_RECORD_TYPES - record_types)
    if missing_record_types:
        blockers.append(f"客户知识资料缺少类型：{', '.join(missing_record_types)}")

    action_types = {row.get("expected_action", "").strip() for row in questions if row.get("expected_action")}
    invalid_actions = sorted(action_types - _VALID_MATERIAL_ACTIONS)
    if invalid_actions:
        blockers.append(f"客户试跑题库存在无法识别的 expected_action：{', '.join(invalid_actions)}")

    for index, row in enumerate(materials, start=2):
        if not _row_has_values(row, ["record_type", "item_id", "business_object", "standard_answer", "source_uri"]):
            blockers.append(f"客户知识资料第 {index} 行缺少必填字段")
            break
    for index, row in enumerate(questions, start=2):
        if not _row_has_values(row, ["question_id", "question", "expected_answer", "expected_action", "source_uri"]):
            blockers.append(f"客户试跑题库第 {index} 行缺少必填字段")
            break

    blockers.extend(_raw_text_findings("客户知识资料 CSV", payload.materials_csv))
    blockers.extend(_raw_text_findings("客户试跑题库 CSV", payload.trial_questions_csv))
    blockers.extend(_raw_text_findings("资料说明 JSON", payload.manifest_json))

    if manifest:
        if manifest.get("customer_data_used") is not True:
            blockers.append("资料说明 JSON 未明确 customer_data_used=true")
        for field in [
            "customer_alias",
            "provided_by_role",
            "provided_at",
            "desensitization_owner_role",
            "desensitization_statement",
        ]:
            if not str(manifest.get(field, "")).strip():
                blockers.append(f"资料说明 JSON 缺少字段：{field}")
        if manifest.get("real_platform_send_enabled") is True:
            blockers.append("资料说明 JSON 越界：real_platform_send_enabled=true")
        if manifest.get("formal_customer_signoff_ready") is True:
            blockers.append("资料说明 JSON 越界：formal_customer_signoff_ready=true")

    metrics = {
        "material_rows": len(materials),
        "trial_question_count": len(questions),
        "record_types": sorted(record_types),
        "question_action_types": sorted(action_types),
        "minimum_question_count_required": 50,
    }
    precheck_passed = not blockers
    checked_at = utc_now()
    sanitized_manifest = {
        "customer_alias_present": bool(str(manifest.get("customer_alias", "")).strip()) if manifest else False,
        "provided_by_role_present": bool(str(manifest.get("provided_by_role", "")).strip()) if manifest else False,
        "provided_at_present": bool(str(manifest.get("provided_at", "")).strip()) if manifest else False,
        "customer_data_used_declared": manifest.get("customer_data_used") is True if manifest else False,
        "real_platform_send_enabled": manifest.get("real_platform_send_enabled") is True if manifest else False,
        "formal_customer_signoff_ready": manifest.get("formal_customer_signoff_ready") is True if manifest else False,
    }
    risk_count = len([item for item in set(blockers) if "疑似" in item or "密钥" in item or "联系方式" in item])
    material_batch = CustomerMaterialBatch(
        tenant_id=tenant.id,
        batch_code=f"material-precheck-{checked_at.strftime('%Y%m%d%H%M%S%f')}",
        status="precheck_passed_waiting_file_drop" if precheck_passed else "blocked_precheck_failed",
        material_sha256=_sha256_text(payload.materials_csv),
        question_sha256=_sha256_text(payload.trial_questions_csv),
        manifest_sha256=_sha256_text(payload.manifest_json),
        material_row_count=len(materials),
        question_count=len(questions),
        record_type_coverage=sorted(record_types),
        question_action_coverage=sorted(action_types),
        blocker_count=len(set(blockers)),
        desensitization_risk_count=risk_count,
        manifest_summary=sanitized_manifest,
        created_by_id=principal.user.id,
        created_at=checked_at,
    )
    db.add(material_batch)
    db.flush()
    _upsert_pilot_fact(
        db,
        tenant_id=tenant.id,
        fact_key="data3.customer_material_batch",
        status_value="waiting_for_real_customer_materials" if precheck_passed else "blocked_real_customer_materials_invalid",
        source="database",
        evidence_path=f"customer_material_batches:{material_batch.id}",
        payload={
            "batch_code": material_batch.batch_code,
            "material_row_count": material_batch.material_row_count,
            "question_count": material_batch.question_count,
            "record_type_coverage": material_batch.record_type_coverage,
            "question_action_coverage": material_batch.question_action_coverage,
            "blocker_count": material_batch.blocker_count,
            "desensitization_risk_count": material_batch.desensitization_risk_count,
            "raw_materials_persisted": False,
            "real_customer_materials_ready": False,
        },
        not_ready_for=[
            "客户资料正式签收",
            "真实平台自动外发",
            "真实渠道上线",
        ],
        principal=principal,
    )
    add_audit_event(
        db,
        tenant_id=tenant.id,
        actor_id=principal.user.id,
        action="customer_materials.prechecked",
        resource_type="customer_materials_precheck",
        resource_id="in_memory_precheck",
        payload={
            "schema_version": CUSTOMER_MATERIAL_PRECHECK_SCHEMA_VERSION,
            "status": "ready_for_file_drop" if precheck_passed else "blocked",
            "metrics": metrics,
            "blocker_count": len(set(blockers)),
            "raw_materials_persisted": False,
            "real_platform_send_ready": False,
            "formal_customer_signoff_ready": False,
        },
    )
    db.commit()
    db.refresh(material_batch)

    return CustomerMaterialPrecheckRead(
        schema_version=CUSTOMER_MATERIAL_PRECHECK_SCHEMA_VERSION,
        tenant_id=tenant.id,
        checked_at=checked_at,
        status="ready_for_file_drop" if precheck_passed else "blocked",
        summary=(
            "资料包预检通过，可以按固定文件名放入真实资料接收目录后再跑正式门禁。"
            if precheck_passed
            else "资料包仍有阻断项，修正后再进入真实资料接收目录。"
        ),
        blockers=sorted(set(blockers)),
        metrics=metrics,
        readiness={
            "material_precheck_passed": precheck_passed,
            "real_customer_materials_ready": False,
            "real_platform_send_ready": False,
            "formal_customer_signoff_ready": False,
            "raw_materials_persisted": False,
        },
        safety={
            "raw_materials_persisted": False,
            "system_prefilled_customer_confirmation": False,
            "real_platform_send_performed": False,
            "formal_customer_signoff_ready": False,
        },
        persisted_batch=_material_batch_read(material_batch),
    )


def list_customer_material_batches(
    db: Session,
    *,
    tenant_id: int,
    principal: CurrentPrincipal,
) -> CustomerMaterialBatchListRead:
    tenant = require_tenant(db, tenant_id)
    _require_same_tenant(tenant, principal)

    batches = _material_batches(db, tenant.id)
    batch_reads = [_material_batch_read(batch) for batch in batches]
    latest = batch_reads[0] if batch_reads else None
    passed_count = len([batch for batch in batches if batch.status == "precheck_passed_waiting_file_drop"])
    blocked_count = len([batch for batch in batches if batch.status == "blocked_precheck_failed"])
    ready_count = len([batch for batch in batches if batch.status in _REAL_CUSTOMER_MATERIAL_READY_STATUSES])
    risk_count = sum(batch.desensitization_risk_count for batch in batches)
    blocker_count = sum(batch.blocker_count for batch in batches)

    if not batches:
        status_value = "waiting_for_material_precheck"
        summary = "还没有资料预检批次。请先加载模板，填入客户脱敏资料后执行预检。"
    elif ready_count:
        status_value = "customer_real_materials_ready"
        summary = "已有数据库事实标记为真实客户资料 ready 的批次；仍需继续复测、确认和生成质量报告。"
    elif latest and latest.status == "precheck_passed_waiting_file_drop":
        status_value = "material_precheck_batches_available"
        summary = "已有通过预检的资料批次，可以把三份回传文件放入固定接收目录后继续正式资料门禁。"
    elif latest and latest.status == "blocked_precheck_failed":
        status_value = "blocked_latest_material_precheck"
        summary = "最近一次资料预检被阻断，请先修正字段、题量、脱敏或越界配置。"
    else:
        status_value = "material_batches_recorded"
        summary = "已有资料预检批次记录，请根据最近批次状态继续处理。"

    return CustomerMaterialBatchListRead(
        schema_version=CUSTOMER_MATERIAL_BATCH_LIST_SCHEMA_VERSION,
        tenant_id=tenant.id,
        generated_at=utc_now(),
        status=status_value,
        summary=summary,
        batches=batch_reads,
        latest_batch=latest,
        counts={
            "total": len(batches),
            "precheck_passed_waiting_file_drop": passed_count,
            "blocked_precheck_failed": blocked_count,
            "customer_real_materials_ready": ready_count,
            "blocker_count": blocker_count,
            "desensitization_risk_count": risk_count,
        },
        readiness={
            "has_precheck_batch": bool(batches),
            "has_file_drop_candidate": passed_count > 0,
            "real_customer_materials_ready": ready_count > 0,
            "raw_materials_persisted": False,
            "formal_customer_signoff_ready": False,
            "real_platform_send_ready": False,
        },
        safety={
            "raw_materials_persisted": False,
            "returns_material_hashes_only": True,
            "returns_question_hashes_only": True,
            "returns_manifest_summary_only": True,
            "real_platform_send_performed": False,
        },
        next_steps=[
            "若最近批次被阻断，先修正资料字段、题量、脱敏风险或越界配置后重新预检。",
            "若最近批次通过预检，将三份回传文件放入固定接收目录，再运行正式资料门禁。",
            "资料门禁通过后，再进入知识导入、复测、客户确认和质量报告流程。",
        ],
    )


def import_knowledge_confirmation_csv(
    db: Session,
    *,
    tenant_id: int,
    payload: KnowledgeConfirmationImportCreate,
    principal: CurrentPrincipal,
) -> KnowledgeConfirmationImportRead:
    tenant = require_tenant(db, tenant_id)
    _require_same_tenant(tenant, principal)

    reader = csv.DictReader(io.StringIO(payload.csv_text))
    rows = list(reader)
    if reader.fieldnames is None or not rows:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="confirmation csv is empty")

    items: list[KnowledgeConfirmationImportItemRead] = []
    blockers: list[str] = []
    risks: list[str] = []
    for index, row in enumerate(rows, start=2):
        item_id = _value(row, "signoff_item_id", "item_id", "confirmation_item_id")
        review_status = _value(row, "review_status", "status", "确认状态")
        bucket = _status_bucket(review_status)
        confirmed_by = _value(row, "confirmed_by", "customer_reviewer", "确认人")
        confirmed_at = _value(row, "confirmed_at", "confirmation_time", "确认时间")
        reviewer_role = _value(row, "reviewer_role", "expected_reviewer", "role", "角色")
        row_blockers: list[str] = []
        if not item_id:
            row_blockers.append(f"第 {index} 行缺少确认项 ID")
        if bucket == "unknown":
            row_blockers.append(f"第 {index} 行确认状态无法识别：{review_status}")
        if bucket in {"confirmed", "accepted_with_notes", "needs_revision", "rejected"}:
            if not confirmed_by:
                row_blockers.append(f"第 {index} 行缺少确认人")
            if not confirmed_at:
                row_blockers.append(f"第 {index} 行缺少确认时间")
        row_risks = _sensitive_findings(row, index)
        risks.extend(row_risks)
        if row_risks:
            row_blockers.extend(row_risks)
        blockers.extend(row_blockers)
        items.append(
            KnowledgeConfirmationImportItemRead(
                item_id=item_id,
                section=_value(row, "section", "分类"),
                item_name=_value(row, "item_name", "name", "确认项"),
                review_status=bucket,
                confirmed_by=confirmed_by,
                confirmed_at=confirmed_at,
                reviewer_role=reviewer_role,
                customer_comment=_value(row, "customer_comment", "comment", "修订意见", "客户意见"),
                needs_change=_bool_from_csv(_value(row, "needs_change", "needs_revision", "是否需修订")),
                blockers=row_blockers,
            )
        )

    confirmed = [item for item in items if item.review_status == "confirmed"]
    accepted_with_notes = [item for item in items if item.review_status == "accepted_with_notes"]
    revisions = [item for item in items if item.review_status == "needs_revision" or item.needs_change]
    rejected = [item for item in items if item.review_status == "rejected"]
    pending = [item for item in items if item.review_status == "pending"]
    ready_for_next_retest = bool(items) and not blockers and not pending and not rejected
    import_status = "ready_for_next_retest" if ready_for_next_retest else "blocked" if blockers else "waiting_customer_confirmation"
    fact_status = (
        "passed_with_notes"
        if ready_for_next_retest and (accepted_with_notes or revisions)
        else "passed"
        if ready_for_next_retest
        else "blocked"
        if blockers
        else "waiting_customer_confirmation"
    )
    _upsert_pilot_fact(
        db,
        tenant_id=tenant.id,
        fact_key="pilot2.knowledge_confirmation_import",
        status_value=fact_status,
        source="database",
        evidence_path=f"knowledge_confirmation_import:{payload.filename}",
        payload={
            "schema_version": KNOWLEDGE_CONFIRMATION_IMPORT_SCHEMA_VERSION,
            "filename": payload.filename,
            "csv_sha256": _sha256_text(payload.csv_text),
            "total_rows": len(items),
            "confirmed_count": len(confirmed),
            "accepted_with_notes_count": len(accepted_with_notes),
            "needs_revision_count": len(revisions),
            "rejected_count": len(rejected),
            "pending_count": len(pending),
            "blocker_count": len(set(blockers)),
            "sensitive_risk_count": len(set(risks)),
            "ready_for_next_retest": ready_for_next_retest,
            "raw_csv_persisted": False,
            "formal_customer_signoff_ready": False,
            "system_prefilled_customer_confirmation": False,
        },
        not_ready_for=[
            "正式客户验收签收",
            "真实平台自动外发",
            "真实渠道上线",
        ],
        principal=principal,
    )

    add_audit_event(
        db,
        tenant_id=tenant.id,
        actor_id=principal.user.id,
        action="knowledge_confirmation.imported",
        resource_type="knowledge_confirmation_import",
        resource_id=payload.filename,
        payload={
            "schema_version": KNOWLEDGE_CONFIRMATION_IMPORT_SCHEMA_VERSION,
            "filename": payload.filename,
            "total_rows": len(items),
            "confirmed_count": len(confirmed),
            "accepted_with_notes_count": len(accepted_with_notes),
            "needs_revision_count": len(revisions),
            "rejected_count": len(rejected),
            "pending_count": len(pending),
            "ready_for_next_retest": ready_for_next_retest,
            "raw_csv_stored": False,
            "formal_customer_signoff_ready": False,
        },
    )
    db.commit()

    return KnowledgeConfirmationImportRead(
        schema_version=KNOWLEDGE_CONFIRMATION_IMPORT_SCHEMA_VERSION,
        tenant_id=tenant.id,
        imported_at=utc_now(),
        filename=payload.filename,
        status=import_status,
        summary=(
            "客户确认表已通过校验，可进入下一轮复测。"
            if ready_for_next_retest
            else "客户确认表仍需补齐确认人、时间、状态或脱敏风险。"
            if blockers
            else "当前仍在等待客户确认完成。"
        ),
        total_rows=len(items),
        confirmed_count=len(confirmed),
        needs_revision_count=len(revisions),
        rejected_count=len(rejected),
        pending_count=len(pending),
        accepted_with_notes_count=len(accepted_with_notes),
        revision_items=revisions,
        rejected_items=rejected,
        pending_items=pending,
        blockers=sorted(set(blockers)),
        desensitization_risks=sorted(set(risks)),
        ready_for_next_retest=ready_for_next_retest,
        formal_customer_signoff_ready=False,
        system_prefilled_customer_confirmation=False,
        safety={
            "raw_csv_persisted": False,
            "system_prefilled_customer_confirmation": False,
            "formal_customer_signoff_ready": False,
            "real_platform_send_performed": False,
        },
    )
