from __future__ import annotations

from typing import Any

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.tenants import require_tenant
from app.core.auth import CurrentPrincipal
from app.core.config import get_settings
from app.models import (
    BusinessObject,
    CustomerMaterialBatch,
    KnowledgeCard,
    KnowledgeDocument,
    KnowledgeDocumentChunk,
    KnowledgeEmbeddingProviderSmokeRun,
    KnowledgeEvaluationCase,
    KnowledgeEvaluationRun,
    KnowledgeEvaluationRunCase,
    KnowledgeEvaluationSet,
    KnowledgeVectorIndexPlan,
    ModelCallRecord,
    ObjectKnowledgeCard,
    ReplyCitationSnapshot,
    ReplyDecision,
    TenantReplyStrategy,
)
from app.schemas.rag_governance import (
    RagCostGovernanceSummary,
    RagGovernanceAnswerQuality,
    RagGovernanceGate,
    RagGovernanceLatestEvaluation,
    RagGovernanceLatestProviderSmoke,
    RagGovernanceMetric,
    RagGovernanceModelPolicy,
    RagProductionRetrievalReadiness,
    RagGovernanceVectorProfile,
)


SCHEMA_VERSION = "p3-06u-26h2w7.rag_cost_governance_summary.v1"
PRODUCTION_VECTOR_STORE = "postgres_pgvector_store_v1"
PGVECTOR_VECTOR_STORE_ALIASES = {"pgvector", "postgres_pgvector", PRODUCTION_VECTOR_STORE}


def _require_same_tenant(tenant_id: int, principal: CurrentPrincipal) -> None:
    if principal.tenant.id != tenant_id:
        raise HTTPException(status_code=404, detail="tenant not found")


def _count(db: Session, model: type, tenant_id: int, *criteria) -> int:
    statement = select(func.count()).select_from(model).where(model.tenant_id == tenant_id, *criteria)
    return int(db.scalar(statement) or 0)


def _latest(db: Session, model: type, tenant_id: int):
    return db.scalar(select(model).where(model.tenant_id == tenant_id).order_by(model.id.desc()).limit(1))


def _metric(label: str, value: int | float | str | None, unit: str = "", note: str = "") -> RagGovernanceMetric:
    return RagGovernanceMetric(label=label, value=value, unit=unit, note=note)


def _ratio(numerator: int | float, denominator: int | float) -> float | None:
    if not denominator:
        return None
    return round(float(numerator) / float(denominator), 4)


def _gate(code: str, label: str, status: str, reason: str, evidence: dict[str, Any]) -> RagGovernanceGate:
    return RagGovernanceGate(code=code, label=label, status=status, reason=reason, evidence=evidence)


def _latest_vector_plan(plan: KnowledgeVectorIndexPlan | None) -> dict[str, Any] | None:
    if plan is None:
        return None
    return {
        "plan_id": plan.id,
        "plan_status": plan.plan_status,
        "selected_strategy": plan.selected_strategy,
        "index_method": plan.index_method,
        "vector_store": plan.vector_store,
        "retrieval_backend": plan.retrieval_backend,
        "target_chunk_count": plan.target_chunk_count,
        "dry_run": plan.dry_run,
        "execute_performed": plan.execute_performed,
        "created_at": plan.created_at,
    }


def _reply_policy_payload(strategy: TenantReplyStrategy | None) -> dict[str, Any]:
    if strategy is None or not isinstance(strategy.strategy_payload, dict):
        return {}
    reply_policy = strategy.strategy_payload.get("reply_policy")
    if not isinstance(reply_policy, dict):
        return {}
    return reply_policy


def _recent_model_call_record_count(db: Session, tenant_id: int) -> int:
    return _count(db, ModelCallRecord, tenant_id)


def _estimated_model_call_cost(db: Session, tenant_id: int) -> float:
    value = db.scalar(
        select(func.coalesce(func.sum(ModelCallRecord.estimated_cost), 0.0)).where(
            ModelCallRecord.tenant_id == tenant_id
        )
    )
    return float(value or 0.0)


def _answer_quality_from_latest_run(
    db: Session,
    tenant_id: int,
    latest_evaluation: KnowledgeEvaluationRun | None,
) -> RagGovernanceAnswerQuality:
    if latest_evaluation is None:
        return RagGovernanceAnswerQuality(
            latest_evaluation_run_id=None,
            total_cases=0,
            final_answer_sampled_cases=0,
            final_answer_sample_coverage=0,
            final_answer_factuality_labeled_cases=0,
            final_answer_factuality_rate=None,
            citation_sufficient_labeled_cases=0,
            citation_sufficiency_rate=None,
            forbidden_commitment_labeled_cases=0,
            forbidden_commitment_pass_rate=None,
            handoff_labeled_cases=0,
            handoff_correctness=None,
            citation_snapshot_count=0,
            no_citation_snapshot_count=0,
            complete_accuracy_measured=False,
            quality_source="not_recorded_yet",
            note="当前还没有评测运行，只能证明检索与回复链路尚未进入答案质量验收。",
        )

    cases = db.scalars(
        select(KnowledgeEvaluationRunCase)
        .where(
            KnowledgeEvaluationRunCase.tenant_id == tenant_id,
            KnowledgeEvaluationRunCase.evaluation_run_id == latest_evaluation.id,
        )
        .order_by(KnowledgeEvaluationRunCase.id.asc())
    ).all()
    total_cases = len(cases)
    sampled_cases = 0
    labeled_cases = 0
    scored_cases = 0
    score_total = 0.0
    citation_sufficient_labeled_cases = 0
    citation_sufficient_cases = 0
    forbidden_commitment_labeled_cases = 0
    forbidden_commitment_passed_cases = 0
    handoff_labeled_cases = 0
    handoff_correct_cases = 0

    for case in cases:
        result_payload = case.result_payload if isinstance(case.result_payload, dict) else {}
        answer_quality = result_payload.get("answer_quality") if isinstance(result_payload.get("answer_quality"), dict) else {}
        final_answer_sample = (
            result_payload.get("final_answer_sample")
            if isinstance(result_payload.get("final_answer_sample"), dict)
            else {}
        )
        if answer_quality.get("final_answer_sample_available") is True or bool(
            final_answer_sample.get("final_answer_hash")
        ):
            sampled_cases += 1

        if answer_quality.get("final_answer_factuality_measured") is not True:
            continue

        status_value = str(answer_quality.get("final_answer_factuality_status") or "").strip()
        if not status_value:
            continue
        labeled_cases += 1
        if status_value == "correct":
            scored_cases += 1
            score_total += 1.0
        elif status_value == "partially_correct":
            scored_cases += 1
            score_total += 0.5
        elif status_value in {"incorrect", "needs_human_review"}:
            scored_cases += 1

        if isinstance(answer_quality.get("citation_sufficient"), bool):
            citation_sufficient_labeled_cases += 1
            if answer_quality["citation_sufficient"] is True:
                citation_sufficient_cases += 1
        if isinstance(answer_quality.get("forbidden_commitment_passed"), bool):
            forbidden_commitment_labeled_cases += 1
            if answer_quality["forbidden_commitment_passed"] is True:
                forbidden_commitment_passed_cases += 1
        if isinstance(answer_quality.get("handoff_correct"), bool):
            handoff_labeled_cases += 1
            if answer_quality["handoff_correct"] is True:
                handoff_correct_cases += 1

    run_case_ids = [case.id for case in cases]
    citation_snapshot_count = 0
    no_citation_snapshot_count = 0
    if run_case_ids:
        citation_snapshot_count = int(
            db.scalar(
                select(func.count(ReplyCitationSnapshot.id)).where(
                    ReplyCitationSnapshot.tenant_id == tenant_id,
                    ReplyCitationSnapshot.evaluation_run_case_id.in_(run_case_ids),
                )
            )
            or 0
        )
        no_citation_snapshot_count = int(
            db.scalar(
                select(func.count(ReplyCitationSnapshot.id)).where(
                    ReplyCitationSnapshot.tenant_id == tenant_id,
                    ReplyCitationSnapshot.evaluation_run_case_id.in_(run_case_ids),
                    ReplyCitationSnapshot.no_citation_reason != "",
                )
            )
            or 0
        )

    final_answer_factuality_rate = _ratio(score_total, scored_cases)
    complete_accuracy_measured = (
        total_cases > 0
        and sampled_cases == total_cases
        and labeled_cases == total_cases
        and citation_sufficient_labeled_cases == total_cases
        and forbidden_commitment_labeled_cases == total_cases
        and handoff_labeled_cases == total_cases
    )
    return RagGovernanceAnswerQuality(
        latest_evaluation_run_id=latest_evaluation.id,
        total_cases=total_cases,
        final_answer_sampled_cases=sampled_cases,
        final_answer_sample_coverage=_ratio(sampled_cases, total_cases) or 0,
        final_answer_factuality_labeled_cases=labeled_cases,
        final_answer_factuality_rate=final_answer_factuality_rate,
        citation_sufficient_labeled_cases=citation_sufficient_labeled_cases,
        citation_sufficiency_rate=_ratio(citation_sufficient_cases, citation_sufficient_labeled_cases),
        forbidden_commitment_labeled_cases=forbidden_commitment_labeled_cases,
        forbidden_commitment_pass_rate=_ratio(forbidden_commitment_passed_cases, forbidden_commitment_labeled_cases),
        handoff_labeled_cases=handoff_labeled_cases,
        handoff_correctness=_ratio(handoff_correct_cases, handoff_labeled_cases),
        citation_snapshot_count=citation_snapshot_count,
        no_citation_snapshot_count=no_citation_snapshot_count,
        complete_accuracy_measured=complete_accuracy_measured,
        quality_source="knowledge_evaluation_run_cases.result_payload_and_reply_citation_snapshots",
        note=(
            "已完成最终客服答案采样、人工事实性标签和引用快照闭环。"
            if complete_accuracy_measured
            else "当前知识评测仍不能等同完整客服准确率；需要最终答案样本、人工标签、引用快照全部覆盖后才可封版。"
        ),
    )


def _build_gates(
    *,
    active_document_count: int,
    indexed_chunk_count: int,
    pgvector_chunk_count: int,
    active_evaluation_case_count: int,
    latest_evaluation: KnowledgeEvaluationRun | None,
    latest_smoke: KnowledgeEmbeddingProviderSmokeRun | None,
    latest_plan: KnowledgeVectorIndexPlan | None,
    recent_model_call_record_count: int,
    model_budget_guard_enabled: bool,
    model_pricing_source: str,
    model_pricing_version: str,
    answer_quality: RagGovernanceAnswerQuality,
) -> list[RagGovernanceGate]:
    gates: list[RagGovernanceGate] = []
    gates.append(
        _gate(
            "knowledge_base_ready",
            "知识库基础",
            "passed" if active_document_count > 0 and indexed_chunk_count > 0 else "blocked",
            "已有启用文档和已索引片段" if active_document_count > 0 and indexed_chunk_count > 0 else "缺少启用文档或已索引片段",
            {"active_documents": active_document_count, "indexed_chunks": indexed_chunk_count},
        )
    )
    gates.append(
        _gate(
            "customer_question_bank",
            "真实题库规模",
            "passed" if active_evaluation_case_count >= 50 else "warning" if active_evaluation_case_count > 0 else "blocked",
            "题库达到 50 条以上"
            if active_evaluation_case_count >= 50
            else "题库不足 50 条，不能代表稳定商用准确率",
            {"active_evaluation_cases": active_evaluation_case_count, "minimum_controlled_pilot_cases": 50},
        )
    )
    evaluation_passed = (
        latest_evaluation is not None
        and latest_evaluation.total_cases > 0
        and latest_evaluation.hit_rate >= 0.8
        and latest_evaluation.citation_coverage >= 0.8
    )
    gates.append(
        _gate(
            "retrieval_evaluation",
            "检索评测",
            "passed" if evaluation_passed else "warning" if latest_evaluation is not None else "blocked",
            "最近评测命中率和引用覆盖达到受控试点线"
            if evaluation_passed
            else "最近评测不足以证明完整客服准确率",
            {
                "latest_run_id": latest_evaluation.id if latest_evaluation else None,
                "hit_rate": latest_evaluation.hit_rate if latest_evaluation else 0,
                "citation_coverage": latest_evaluation.citation_coverage if latest_evaluation else 0,
            },
        )
    )
    production_vector_ready = pgvector_chunk_count > 0 or (
        latest_plan is not None and latest_plan.vector_store == PRODUCTION_VECTOR_STORE and latest_plan.execute_performed
    )
    gates.append(
        _gate(
            "production_vector_store",
            "生产级向量库",
            "passed" if production_vector_ready else "warning" if indexed_chunk_count > 0 else "blocked",
            "已有 pgvector 片段或已执行生产索引计划"
            if production_vector_ready
            else "当前仍以本地 JSON/SQLite 向量扫描为主，不能写成生产级向量库完成",
            {
                "pgvector_chunks": pgvector_chunk_count,
                "indexed_chunks": indexed_chunk_count,
                "latest_vector_plan_id": latest_plan.id if latest_plan else None,
                "latest_vector_plan_executed": latest_plan.execute_performed if latest_plan else False,
            },
        )
    )
    gates.append(
        _gate(
            "embedding_provider_cost",
            "检索模型成本记录",
            "passed" if latest_smoke is not None else "blocked",
            "已有模型服务商测试的用量、耗时和费用估算记录"
            if latest_smoke is not None
            else "尚未形成检索模型服务商成本记录",
            {
                "latest_smoke_id": latest_smoke.id if latest_smoke else None,
                "provider_call_performed": latest_smoke.provider_call_performed if latest_smoke else False,
                "estimated_cost": latest_smoke.estimated_cost if latest_smoke else 0,
            },
        )
    )
    gates.append(
        _gate(
            "model_call_cost_governance",
            "客服模型调用成本",
            "passed" if recent_model_call_record_count > 0 else "blocked",
            "已有客服回复模型调用记录"
            if recent_model_call_record_count > 0
            else "还没有按模型服务商、模型和回复策略记录客服模型调用成本，不能展示完整成本治理",
            {"recent_model_call_record_count": recent_model_call_record_count},
        )
    )
    gates.append(
        _gate(
            "model_budget_policy",
            "模型预算门禁",
            "passed" if model_budget_guard_enabled and model_pricing_source and model_pricing_version else "blocked",
            "已有预算门禁配置和价格来源版本"
            if model_budget_guard_enabled and model_pricing_source and model_pricing_version
            else "缺少预算门禁或价格来源版本，不能进入模型成本治理封版",
            {
                "budget_guard_enabled": model_budget_guard_enabled,
                "pricing_source": model_pricing_source,
                "pricing_version": model_pricing_version,
            },
        )
    )
    answer_quality_passed = (
        answer_quality.complete_accuracy_measured
        and (answer_quality.final_answer_factuality_rate or 0) >= 0.8
        and (answer_quality.citation_sufficiency_rate or 0) >= 0.8
        and (answer_quality.forbidden_commitment_pass_rate or 0) >= 0.95
        and (answer_quality.handoff_correctness or 0) >= 0.8
    )
    gates.append(
        _gate(
            "final_answer_quality",
            "最终答案质量",
            "passed" if answer_quality_passed else "warning",
            "最终客服答案事实性、引用、禁用承诺和转人工标签达到受控试点线"
            if answer_quality_passed
            else "当前评测仍偏检索口径，不能把它写成完整客服准确率",
            {
                "latest_evaluation_run_id": answer_quality.latest_evaluation_run_id,
                "total_cases": answer_quality.total_cases,
                "sampled_cases": answer_quality.final_answer_sampled_cases,
                "labeled_cases": answer_quality.final_answer_factuality_labeled_cases,
                "factuality_rate": answer_quality.final_answer_factuality_rate,
                "citation_sufficiency_rate": answer_quality.citation_sufficiency_rate,
                "citation_snapshot_count": answer_quality.citation_snapshot_count,
                "complete_accuracy_measured": answer_quality.complete_accuracy_measured,
            },
        )
    )
    return gates


def _maturity_from_gates(gates: list[RagGovernanceGate]) -> tuple[str, str]:
    blocked_count = sum(1 for gate in gates if gate.status == "blocked")
    warning_count = sum(1 for gate in gates if gate.status == "warning")
    if blocked_count >= 2:
        return "blocked", "生产级 RAG 与模型成本治理仍有关键缺口，只能作为受控试点前的治理看板。"
    if blocked_count == 1 or warning_count > 0:
        return "candidate", "已经具备部分治理证据，但仍需补足题库、生产向量库或模型成本记录。"
    return "ready_for_controlled_pilot", "门禁全部通过，可进入受控试点验收，不代表全渠道生产外发完成。"


def _database_dialect(db: Session) -> str:
    return db.get_bind().dialect.name


def _real_customer_material_ready(batch: CustomerMaterialBatch | None) -> bool:
    if batch is None:
        return False
    manifest_summary = batch.manifest_summary if isinstance(batch.manifest_summary, dict) else {}
    return (
        batch.status == "customer_real_materials_ready"
        and batch.question_count >= 50
        and batch.blocker_count == 0
        and batch.desensitization_risk_count == 0
        and manifest_summary.get("customer_data_used_declared") is True
        and bool(batch.material_sha256)
        and bool(batch.question_sha256)
        and bool(batch.manifest_sha256)
    )


def _build_production_readiness(
    *,
    db: Session,
    tenant_id: int,
    settings,
    indexed_chunk_count: int,
    pgvector_chunk_count: int,
    sqlite_vector_chunk_count: int,
    active_evaluation_case_count: int,
    latest_evaluation: KnowledgeEvaluationRun | None,
    latest_smoke: KnowledgeEmbeddingProviderSmokeRun | None,
    latest_plan: KnowledgeVectorIndexPlan | None,
    recent_model_call_record_count: int,
    model_budget_guard_enabled: bool,
    model_pricing_source: str,
    model_pricing_version: str,
    answer_quality: RagGovernanceAnswerQuality,
) -> RagProductionRetrievalReadiness:
    configured_vector_store = (settings.knowledge_vector_store or "").strip()
    configured_pgvector = configured_vector_store in PGVECTOR_VECTOR_STORE_ALIASES
    postgres_runtime_ready = _database_dialect(db) == "postgresql"
    pgvector_runtime_ready = postgres_runtime_ready and (
        configured_pgvector
        or pgvector_chunk_count > 0
        or bool(
            latest_plan
            and latest_plan.vector_store == PRODUCTION_VECTOR_STORE
            and latest_plan.execute_performed
        )
    )
    customer_question_bank_ready = active_evaluation_case_count >= 50
    retrieval_evaluation_ready = bool(
        latest_evaluation
        and latest_evaluation.total_cases >= 50
        and latest_evaluation.hit_rate >= 0.8
        and latest_evaluation.citation_coverage >= 0.8
    )
    final_answer_quality_ready = bool(
        answer_quality.complete_accuracy_measured
        and answer_quality.total_cases >= 50
        and (answer_quality.final_answer_factuality_rate or 0) >= 0.8
        and (answer_quality.citation_sufficiency_rate or 0) >= 0.8
        and (answer_quality.forbidden_commitment_pass_rate or 0) >= 0.95
        and (answer_quality.handoff_correctness or 0) >= 0.8
    )
    embedding_cost_record_ready = bool(
        latest_smoke
        and latest_smoke.estimated_input_tokens > 0
        and latest_smoke.embedding_provider
        and latest_smoke.embedding_model
        and latest_smoke.vector_store
    )
    model_cost_record_ready = recent_model_call_record_count > 0
    budget_policy_ready = bool(model_budget_guard_enabled and model_pricing_source and model_pricing_version)

    # The production retrieval gate is intentionally stricter than the engineering
    # rehearsal gates: internal sample question banks can prove mechanics, but they
    # must not unlock a customer-facing production retrieval switch.
    latest_material_batch = db.scalar(
        select(CustomerMaterialBatch)
        .where(CustomerMaterialBatch.tenant_id == tenant_id)
        .order_by(CustomerMaterialBatch.id.desc())
        .limit(1)
    )
    real_customer_material_ready = _real_customer_material_ready(latest_material_batch)
    customer_material_batch_status = latest_material_batch.status if latest_material_batch else "not_submitted"
    customer_material_question_count = latest_material_batch.question_count if latest_material_batch else 0

    blockers: list[str] = []
    if not pgvector_runtime_ready:
        blockers.append("尚未在 PostgreSQL + pgvector 运行环境中证明生产候选检索。")
    if not real_customer_material_ready:
        blockers.append("尚未形成 50 条以上、已脱敏且声明为真实客户资料的资料批次，内部样板不能解锁生产检索。")
    if not customer_question_bank_ready:
        blockers.append("启用题库少于 50 条，不能作为生产检索评测基线。")
    if not retrieval_evaluation_ready:
        blockers.append("最近评测未达到 50 题以上且命中率、引用覆盖均超过 80% 的受控线。")
    if not final_answer_quality_ready:
        blockers.append("最终客服答案事实性、引用充分、禁用承诺和转人工标签未形成完整覆盖。")
    if not embedding_cost_record_ready:
        blockers.append("检索 embedding 的 provider、model、用量和成本证据不完整。")
    if not model_cost_record_ready:
        blockers.append("客服回复模型调用成本仍没有持久记录。")
    if not budget_policy_ready:
        blockers.append("模型预算门禁或价格来源版本不完整。")

    production_switch_allowed = not blockers
    status_value = (
        "ready_for_controlled_pilot"
        if production_switch_allowed
        else "candidate"
        if len(blockers) <= 2 and indexed_chunk_count > 0
        else "blocked"
    )
    not_ready_for = [
        "formal_accuracy_signoff",
        "real_platform_send",
        "production_sla",
        "signed_installer",
    ]
    if not production_switch_allowed:
        not_ready_for.insert(0, "production_retrieval_switch")

    return RagProductionRetrievalReadiness(
        status=status_value,
        production_switch_allowed=production_switch_allowed,
        postgres_runtime_ready=postgres_runtime_ready,
        pgvector_runtime_ready=pgvector_runtime_ready,
        configured_pgvector=configured_pgvector,
        indexed_chunk_count=indexed_chunk_count,
        pgvector_chunk_count=pgvector_chunk_count,
        sqlite_vector_chunk_count=sqlite_vector_chunk_count,
        real_customer_material_ready=real_customer_material_ready,
        customer_material_batch_status=customer_material_batch_status,
        customer_material_question_count=customer_material_question_count,
        customer_question_bank_ready=customer_question_bank_ready,
        active_evaluation_cases=active_evaluation_case_count,
        retrieval_evaluation_ready=retrieval_evaluation_ready,
        final_answer_quality_ready=final_answer_quality_ready,
        embedding_cost_record_ready=embedding_cost_record_ready,
        model_cost_record_ready=model_cost_record_ready,
        budget_policy_ready=budget_policy_ready,
        blockers=blockers,
        not_ready_for=not_ready_for,
        retrieval_strategy_rules={
            "exact_scan": "小于 10,000 个片段或回归基线优先 exact scan，保证召回可解释。",
            "hnsw": "10,000 到 500,000 个片段优先 HNSW，进入生产候选前必须和 exact scan 对照召回。",
            "ivfflat": "超过 500,000 个片段或内存敏感场景可选 IVFFlat，但必须调 lists/probes 并保留回滚方案。",
            "fallback": "pgvector、embedding 或重排失败时不得静默伪成功，只能降级为确定性知识草稿或转人工。",
        },
        safety={
            "sqlite_json_disguised_as_production_vector_store": False,
            "production_retrieval_path_switched": False,
            "paid_embedding_call_performed": False,
            "external_platform_write_performed": False,
            "raw_customer_text_returned": False,
            "internal_sample_unlocks_production_retrieval": False,
        },
    )


def get_rag_cost_governance_summary(
    db: Session,
    tenant_id: int,
    principal: CurrentPrincipal,
) -> RagCostGovernanceSummary:
    require_tenant(db, tenant_id)
    _require_same_tenant(tenant_id, principal)
    settings = get_settings()

    knowledge_card_count = _count(db, KnowledgeCard, tenant_id)
    active_knowledge_card_count = _count(db, KnowledgeCard, tenant_id, KnowledgeCard.status == "active")
    business_object_count = _count(db, BusinessObject, tenant_id)
    object_knowledge_card_count = _count(db, ObjectKnowledgeCard, tenant_id)
    active_document_count = _count(db, KnowledgeDocument, tenant_id, KnowledgeDocument.status == "active")
    draft_document_count = _count(db, KnowledgeDocument, tenant_id, KnowledgeDocument.status == "draft")
    indexed_chunk_count = _count(
        db,
        KnowledgeDocumentChunk,
        tenant_id,
        KnowledgeDocumentChunk.vector_index_status == "indexed",
        KnowledgeDocumentChunk.status == "active",
    )
    pgvector_chunk_count = _count(
        db,
        KnowledgeDocumentChunk,
        tenant_id,
        KnowledgeDocumentChunk.vector_store == PRODUCTION_VECTOR_STORE,
        KnowledgeDocumentChunk.status == "active",
    )
    sqlite_vector_chunk_count = _count(
        db,
        KnowledgeDocumentChunk,
        tenant_id,
        KnowledgeDocumentChunk.vector_store == "sqlite_json_vector_store",
        KnowledgeDocumentChunk.status == "active",
    )
    evaluation_set_count = _count(db, KnowledgeEvaluationSet, tenant_id)
    active_evaluation_case_count = _count(db, KnowledgeEvaluationCase, tenant_id, KnowledgeEvaluationCase.status == "active")
    reply_decision_count = _count(db, ReplyDecision, tenant_id)

    latest_evaluation_run = _latest(db, KnowledgeEvaluationRun, tenant_id)
    latest_provider_smoke = _latest(db, KnowledgeEmbeddingProviderSmokeRun, tenant_id)
    latest_vector_plan = _latest(db, KnowledgeVectorIndexPlan, tenant_id)
    strategy = db.scalar(select(TenantReplyStrategy).where(TenantReplyStrategy.tenant_id == tenant_id))
    reply_policy = _reply_policy_payload(strategy)
    recent_model_call_record_count = _recent_model_call_record_count(db, tenant_id)
    estimated_model_call_cost = _estimated_model_call_cost(db, tenant_id)
    answer_quality = _answer_quality_from_latest_run(db, tenant_id, latest_evaluation_run)
    production_readiness = _build_production_readiness(
        db=db,
        tenant_id=tenant_id,
        settings=settings,
        indexed_chunk_count=indexed_chunk_count,
        pgvector_chunk_count=pgvector_chunk_count,
        sqlite_vector_chunk_count=sqlite_vector_chunk_count,
        active_evaluation_case_count=active_evaluation_case_count,
        latest_evaluation=latest_evaluation_run,
        latest_smoke=latest_provider_smoke,
        latest_plan=latest_vector_plan,
        recent_model_call_record_count=recent_model_call_record_count,
        model_budget_guard_enabled=settings.model_budget_guard_enabled,
        model_pricing_source=settings.model_budget_pricing_source,
        model_pricing_version=settings.model_budget_price_table_version,
        answer_quality=answer_quality,
    )

    latest_evaluation = RagGovernanceLatestEvaluation(
        run_id=latest_evaluation_run.id if latest_evaluation_run else None,
        evaluation_set_id=latest_evaluation_run.evaluation_set_id if latest_evaluation_run else None,
        run_mode=latest_evaluation_run.run_mode if latest_evaluation_run else "",
        total_cases=latest_evaluation_run.total_cases if latest_evaluation_run else 0,
        hit_rate=latest_evaluation_run.hit_rate if latest_evaluation_run else 0,
        citation_coverage=latest_evaluation_run.citation_coverage if latest_evaluation_run else 0,
        expected_term_coverage=latest_evaluation_run.expected_term_coverage if latest_evaluation_run else 0,
        unsupported_answer_rate=latest_evaluation_run.unsupported_answer_rate if latest_evaluation_run else None,
        created_at=latest_evaluation_run.created_at if latest_evaluation_run else None,
    )
    latest_smoke = RagGovernanceLatestProviderSmoke(
        run_id=latest_provider_smoke.id if latest_provider_smoke else None,
        status=latest_provider_smoke.status if latest_provider_smoke else "",
        embedding_provider=latest_provider_smoke.embedding_provider if latest_provider_smoke else "",
        embedding_model=latest_provider_smoke.embedding_model if latest_provider_smoke else "",
        vector_store=latest_provider_smoke.vector_store if latest_provider_smoke else "",
        estimated_input_tokens=latest_provider_smoke.estimated_input_tokens if latest_provider_smoke else 0,
        estimated_cost=latest_provider_smoke.estimated_cost if latest_provider_smoke else 0,
        cost_currency=latest_provider_smoke.cost_currency if latest_provider_smoke else settings.knowledge_embedding_cost_currency,
        provider_call_performed=latest_provider_smoke.provider_call_performed if latest_provider_smoke else False,
        created_at=latest_provider_smoke.created_at if latest_provider_smoke else None,
    )
    gates = _build_gates(
        active_document_count=active_document_count,
        indexed_chunk_count=indexed_chunk_count,
        pgvector_chunk_count=pgvector_chunk_count,
        active_evaluation_case_count=active_evaluation_case_count,
        latest_evaluation=latest_evaluation_run,
        latest_smoke=latest_provider_smoke,
        latest_plan=latest_vector_plan,
        recent_model_call_record_count=recent_model_call_record_count,
        model_budget_guard_enabled=settings.model_budget_guard_enabled,
        model_pricing_source=settings.model_budget_pricing_source,
        model_pricing_version=settings.model_budget_price_table_version,
        answer_quality=answer_quality,
    )
    maturity_status, summary = _maturity_from_gates(gates)
    return RagCostGovernanceSummary(
        tenant_id=tenant_id,
        schema_version=SCHEMA_VERSION,
        maturity_status=maturity_status,
        summary=summary,
        knowledge_metrics=[
            _metric("知识卡", knowledge_card_count, "条", f"启用 {active_knowledge_card_count} 条"),
            _metric("业务对象", business_object_count, "个"),
            _metric("对象问答", object_knowledge_card_count, "条"),
            _metric("启用文档", active_document_count, "份", f"草稿 {draft_document_count} 份"),
            _metric("已索引片段", indexed_chunk_count, "段"),
            _metric("评测集", evaluation_set_count, "个"),
            _metric("启用评测题", active_evaluation_case_count, "题"),
            _metric("回复决策", reply_decision_count, "条"),
        ],
        vector_profile=RagGovernanceVectorProfile(
            configured_embedding_provider=settings.knowledge_embedding_provider,
            configured_embedding_model=settings.knowledge_embedding_model,
            configured_vector_store=settings.knowledge_vector_store,
            configured_reranker=settings.knowledge_reranker,
            indexed_chunk_count=indexed_chunk_count,
            pgvector_chunk_count=pgvector_chunk_count,
            sqlite_vector_chunk_count=sqlite_vector_chunk_count,
            latest_vector_index_plan=_latest_vector_plan(latest_vector_plan),
        ),
        latest_evaluation=latest_evaluation,
        latest_provider_smoke=latest_smoke,
        model_policy=RagGovernanceModelPolicy(
            strategy_status=strategy.status if strategy else "inactive",
            strategy_version=strategy.strategy_version if strategy else "",
            auto_reply_threshold=reply_policy.get("auto_reply_threshold"),
            manual_review_threshold=reply_policy.get("manual_review_threshold"),
            force_draft_only=bool(reply_policy.get("force_draft_only") is True),
            blocked_policy_terms_count=len(reply_policy.get("blocked_policy_terms") or []),
            manual_review_terms_count=len(reply_policy.get("manual_review_terms") or []),
            recent_reply_decision_count=reply_decision_count,
            recent_model_call_record_count=recent_model_call_record_count,
            estimated_model_cost=None if recent_model_call_record_count == 0 else round(estimated_model_call_cost, 6),
            cost_currency=settings.model_budget_cost_currency,
            cost_source="not_recorded_yet" if recent_model_call_record_count == 0 else "model_call_records",
            budget_guard_enabled=settings.model_budget_guard_enabled,
            daily_budget_limit=settings.model_budget_daily_limit_cny,
            monthly_budget_limit=settings.model_budget_monthly_limit_cny,
            single_call_budget_limit=settings.model_budget_single_call_limit_cny,
            pricing_source=settings.model_budget_pricing_source,
            pricing_version=settings.model_budget_price_table_version,
        ),
        answer_quality=answer_quality,
        production_readiness=production_readiness,
        gates=gates,
        recommended_next_steps=[
            "补齐 50-100 条真实脱敏客服题库，并区分售前、售后、价格、风险和转人工样本。",
            "在生产环境切换 pgvector/专用向量库前，先完成索引计划预检、备份和回滚验证。",
            "把最终客服答案采样、人工事实性标签、引用充分性、禁用承诺和转人工正确性纳入每次发布验收。",
            "把低置信、无引用、预算不足和模型失败统一接入自动回复策略的转人工门禁。",
        ],
        safety={
            "model_call_performed": False,
            "external_write_performed": False,
            "raw_customer_text_logged": False,
            "pricing_source": "operator_config_or_provider_usage_only",
            "production_external_reply_enabled": False,
        },
    )
