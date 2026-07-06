from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.auth import CurrentPrincipal
from app.core.rbac import require_permission
from app.db.session import get_db
from app.models import KnowledgeCard
from app.schemas.knowledge import (
    BusinessObjectCreate,
    BusinessObjectList,
    BusinessObjectRead,
    BusinessObjectUpdate,
    CustomerQualityReportArchiveListRead,
    CustomerQualityReportExportRead,
    CustomerQualityReportRead,
    CustomerQualityReportSignoffCreate,
    CustomerQualityReportSignoffListRead,
    CustomerQualityReportSignoffRead,
    CustomerServiceQuestionBankImportCreate,
    CustomerServiceQuestionBankPrecheckRead,
    KnowledgeChunkRead,
    KnowledgeCardCreate,
    KnowledgeCardList,
    KnowledgeCardRead,
    KnowledgeCardUpdate,
    KnowledgeDocumentCreate,
    KnowledgeDocumentList,
    KnowledgeDocumentPublishGateCreate,
    KnowledgeDocumentPublishGateRead,
    KnowledgeDocumentPublicationList,
    KnowledgeDocumentPublicationRead,
    KnowledgeDocumentRead,
    KnowledgeDocumentRollbackCreate,
    KnowledgeDocumentSearchRequest,
    KnowledgeDocumentSearchResponse,
    KnowledgeEmbeddingProviderSmokeCreate,
    KnowledgeEmbeddingProviderSmokeRead,
    KnowledgeEvaluationRunCaseFactualityBatchLabelCreate,
    KnowledgeEvaluationRunCaseFactualityBatchLabelRead,
    KnowledgeEvaluationRunCaseFactualityLabelCreate,
    KnowledgeEvaluationRunCaseFactualityLabelRead,
    KnowledgeEvaluationRunCaseFinalAnswerSampleCreate,
    KnowledgeEvaluationRunCaseFinalAnswerSampleRead,
    KnowledgeEvaluationRunFinalAnswerLabelExportRead,
    KnowledgeEvaluationRunFinalAnswerLabelImportCreate,
    KnowledgeEvaluationRunFinalAnswerLabelImportRead,
    KnowledgeEvaluationRunCreate,
    KnowledgeEvaluationRunList,
    KnowledgeEvaluationRunReportRead,
    KnowledgeEvaluationRunRead,
    KnowledgeEvaluationSetCreate,
    KnowledgeEvaluationSetList,
    KnowledgeEvaluationSetRead,
    KnowledgeGapDocumentDraftRead,
    KnowledgeGapList,
    KnowledgeGapRegressionCaseRead,
    KnowledgeGapSyncCreate,
    KnowledgeGapSyncRead,
    KnowledgeGapRead,
    KnowledgeGapUpdate,
    KnowledgeMemoryMeshOverviewRead,
    KnowledgeSearchRequest,
    KnowledgeSearchResponse,
    KnowledgeUpdatePackageImportCreate,
    KnowledgeUpdatePackagePreviewCreate,
    KnowledgeUpdatePackageResultRead,
    KnowledgeUpdatePackageRollbackCreate,
    KnowledgeUpdatePackageRollbackRead,
    KnowledgeVectorIndexPlanCreate,
    KnowledgeVectorIndexPlanRead,
    KnowledgeVectorIndexRebuildCreate,
    KnowledgeVectorIndexRebuildRead,
    MonthlyOpsReportRead,
    MonthlyQualityReviewRead,
    ObjectKnowledgeCardCreate,
    ObjectKnowledgeCardList,
    ObjectKnowledgeCardRead,
)
from app.schemas.llm_ops import LlmOpsReadinessSummary
from app.schemas.rag_governance import RagCostGovernanceSummary
from app.services.knowledge import (
    batch_label_knowledge_evaluation_run_case_factuality,
    capture_knowledge_evaluation_run_case_final_answer_sample,
    create_business_object,
    create_knowledge_card,
    create_knowledge_document,
    create_knowledge_evaluation_set,
    create_knowledge_gap_document_draft,
    create_knowledge_gap_regression_case,
    create_knowledge_vector_index_plan,
    create_object_knowledge_card,
    download_customer_quality_report_archive,
    export_knowledge_evaluation_run_report,
    export_customer_quality_report,
    export_knowledge_evaluation_run_final_answer_labels,
    get_customer_quality_report,
    get_knowledge_memory_mesh_overview,
    get_monthly_ops_report,
    get_monthly_quality_review,
    get_knowledge_evaluation_run,
    import_customer_service_question_bank,
    import_knowledge_evaluation_run_final_answer_labels,
    label_knowledge_evaluation_run_case_factuality,
    check_knowledge_document_publish_gate,
    list_knowledge_gaps,
    list_business_objects,
    list_knowledge_evaluation_runs,
    list_knowledge_evaluation_sets,
    list_knowledge_document_chunks,
    list_knowledge_document_publications,
    list_knowledge_documents,
    list_knowledge_cards,
    list_customer_quality_report_signoffs,
    list_customer_quality_report_archives,
    list_object_knowledge_cards,
    rebuild_knowledge_vector_index,
    rollback_knowledge_update_package_import,
    rollback_knowledge_document_publication,
    run_knowledge_embedding_provider_smoke,
    run_knowledge_evaluation_set,
    precheck_customer_service_question_bank,
    record_customer_quality_report_signoff,
    search_knowledge_documents,
    search_knowledge_cards,
    sync_knowledge_gaps,
    update_knowledge_card,
    update_business_object,
    update_knowledge_gap,
    import_knowledge_update_package,
    preview_knowledge_update_package,
)
from app.services.llm_ops import get_llm_ops_readiness_summary
from app.services.rag_governance import get_rag_cost_governance_summary

router = APIRouter(prefix="/api", tags=["knowledge"])

KNOWLEDGE_READ_PERMISSION = "knowledge.read"
KNOWLEDGE_MANAGE_PERMISSION = "knowledge.manage"
QUALITY_READ_PERMISSION = "quality.read"
CUSTOMER_REPORT_SIGNOFF_PERMISSION = "accounts.manage"
OPS_METRICS_READ_PERMISSION = "ops.metrics.read"


@router.post(
    "/tenants/{tenant_id}/knowledge-cards",
    response_model=KnowledgeCardRead,
    status_code=status.HTTP_201_CREATED,
)
def create_tenant_knowledge_card(
    tenant_id: int,
    payload: KnowledgeCardCreate,
    principal: CurrentPrincipal = Depends(require_permission(KNOWLEDGE_MANAGE_PERMISSION)),
    db: Session = Depends(get_db),
) -> KnowledgeCard:
    return create_knowledge_card(db, tenant_id, payload, principal)


@router.get("/tenants/{tenant_id}/knowledge-cards", response_model=KnowledgeCardList)
def list_tenant_knowledge_cards(
    tenant_id: int,
    status_filter: str | None = Query(default=None, alias="status", pattern="^(draft|active|archived)$"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    principal: CurrentPrincipal = Depends(require_permission(KNOWLEDGE_READ_PERMISSION)),
    db: Session = Depends(get_db),
) -> KnowledgeCardList:
    return list_knowledge_cards(
        db,
        tenant_id,
        status_filter=status_filter,
        page=page,
        page_size=page_size,
        principal=principal,
    )


@router.get(
    "/tenants/{tenant_id}/rag-cost-governance-summary",
    response_model=RagCostGovernanceSummary,
)
def get_tenant_rag_cost_governance_summary(
    tenant_id: int,
    principal: CurrentPrincipal = Depends(require_permission(OPS_METRICS_READ_PERMISSION)),
    db: Session = Depends(get_db),
) -> RagCostGovernanceSummary:
    return get_rag_cost_governance_summary(db, tenant_id, principal)


@router.get(
    "/tenants/{tenant_id}/llm-ops-readiness",
    response_model=LlmOpsReadinessSummary,
)
def get_tenant_llm_ops_readiness(
    tenant_id: int,
    principal: CurrentPrincipal = Depends(require_permission(OPS_METRICS_READ_PERMISSION)),
    db: Session = Depends(get_db),
) -> LlmOpsReadinessSummary:
    return get_llm_ops_readiness_summary(db, tenant_id, principal)


@router.get(
    "/tenants/{tenant_id}/knowledge-memory-mesh-overview",
    response_model=KnowledgeMemoryMeshOverviewRead,
)
def get_tenant_knowledge_memory_mesh_overview(
    tenant_id: int,
    principal: CurrentPrincipal = Depends(require_permission(KNOWLEDGE_READ_PERMISSION)),
    db: Session = Depends(get_db),
) -> KnowledgeMemoryMeshOverviewRead:
    return get_knowledge_memory_mesh_overview(db, tenant_id, principal)


@router.patch("/knowledge-cards/{card_id}", response_model=KnowledgeCardRead)
def patch_knowledge_card(
    card_id: int,
    payload: KnowledgeCardUpdate,
    principal: CurrentPrincipal = Depends(require_permission(KNOWLEDGE_MANAGE_PERMISSION)),
    db: Session = Depends(get_db),
) -> KnowledgeCard:
    return update_knowledge_card(db, card_id, payload, principal)


@router.post(
    "/tenants/{tenant_id}/business-objects",
    response_model=BusinessObjectRead,
    status_code=status.HTTP_201_CREATED,
)
def create_tenant_business_object(
    tenant_id: int,
    payload: BusinessObjectCreate,
    principal: CurrentPrincipal = Depends(require_permission(KNOWLEDGE_MANAGE_PERMISSION)),
    db: Session = Depends(get_db),
) -> BusinessObjectRead:
    return create_business_object(db, tenant_id, payload, principal)


@router.patch("/business-objects/{business_object_id}", response_model=BusinessObjectRead)
def update_tenant_business_object(
    business_object_id: int,
    payload: BusinessObjectUpdate,
    principal: CurrentPrincipal = Depends(require_permission(KNOWLEDGE_MANAGE_PERMISSION)),
    db: Session = Depends(get_db),
) -> BusinessObjectRead:
    return update_business_object(db, business_object_id, payload, principal)


@router.get("/tenants/{tenant_id}/business-objects", response_model=BusinessObjectList)
def list_tenant_business_objects(
    tenant_id: int,
    type_filter: str | None = Query(
        default=None,
        alias="type",
        pattern="^(product|service|package|course|project|store)$",
    ),
    status_filter: str | None = Query(default=None, alias="status", pattern="^(draft|active|archived)$"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    principal: CurrentPrincipal = Depends(require_permission(KNOWLEDGE_READ_PERMISSION)),
    db: Session = Depends(get_db),
) -> BusinessObjectList:
    return list_business_objects(
        db,
        tenant_id,
        type_filter=type_filter,
        status_filter=status_filter,
        page=page,
        page_size=page_size,
        principal=principal,
    )


@router.post(
    "/business-objects/{business_object_id}/knowledge-cards",
    response_model=ObjectKnowledgeCardRead,
    status_code=status.HTTP_201_CREATED,
)
def create_business_object_knowledge_card(
    business_object_id: int,
    payload: ObjectKnowledgeCardCreate,
    principal: CurrentPrincipal = Depends(require_permission(KNOWLEDGE_MANAGE_PERMISSION)),
    db: Session = Depends(get_db),
) -> ObjectKnowledgeCardRead:
    return create_object_knowledge_card(db, business_object_id, payload, principal)


@router.get(
    "/business-objects/{business_object_id}/knowledge-cards",
    response_model=ObjectKnowledgeCardList,
)
def list_business_object_knowledge_cards(
    business_object_id: int,
    status_filter: str | None = Query(default=None, alias="status", pattern="^(draft|active|archived)$"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    principal: CurrentPrincipal = Depends(require_permission(KNOWLEDGE_READ_PERMISSION)),
    db: Session = Depends(get_db),
) -> ObjectKnowledgeCardList:
    return list_object_knowledge_cards(
        db,
        business_object_id,
        status_filter=status_filter,
        page=page,
        page_size=page_size,
        principal=principal,
    )


@router.post(
    "/tenants/{tenant_id}/knowledge-documents",
    response_model=KnowledgeDocumentRead,
    status_code=status.HTTP_201_CREATED,
)
def create_tenant_knowledge_document(
    tenant_id: int,
    payload: KnowledgeDocumentCreate,
    principal: CurrentPrincipal = Depends(require_permission(KNOWLEDGE_MANAGE_PERMISSION)),
    db: Session = Depends(get_db),
):
    return create_knowledge_document(db, tenant_id, payload, principal)


@router.get("/tenants/{tenant_id}/knowledge-documents", response_model=KnowledgeDocumentList)
def list_tenant_knowledge_documents(
    tenant_id: int,
    status_filter: str | None = Query(default=None, alias="status", pattern="^(draft|active|archived)$"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    principal: CurrentPrincipal = Depends(require_permission(KNOWLEDGE_READ_PERMISSION)),
    db: Session = Depends(get_db),
) -> KnowledgeDocumentList:
    return list_knowledge_documents(
        db,
        tenant_id,
        status_filter=status_filter,
        page=page,
        page_size=page_size,
        principal=principal,
    )


@router.get("/knowledge-documents/{document_id}/chunks", response_model=list[KnowledgeChunkRead])
def list_tenant_knowledge_document_chunks(
    document_id: int,
    principal: CurrentPrincipal = Depends(require_permission(KNOWLEDGE_READ_PERMISSION)),
    db: Session = Depends(get_db),
) -> list[KnowledgeChunkRead]:
    return list_knowledge_document_chunks(db, document_id, principal)


@router.post(
    "/knowledge-documents/{document_id}/publish-checks",
    response_model=KnowledgeDocumentPublishGateRead,
    status_code=status.HTTP_201_CREATED,
)
def create_knowledge_document_publish_check(
    document_id: int,
    payload: KnowledgeDocumentPublishGateCreate,
    principal: CurrentPrincipal = Depends(require_permission(KNOWLEDGE_MANAGE_PERMISSION)),
    db: Session = Depends(get_db),
) -> KnowledgeDocumentPublishGateRead:
    return check_knowledge_document_publish_gate(
        db,
        document_id,
        payload,
        principal,
        perform_publish=False,
    )


@router.post(
    "/knowledge-documents/{document_id}/publication",
    response_model=KnowledgeDocumentPublishGateRead,
    status_code=status.HTTP_201_CREATED,
)
def publish_knowledge_document(
    document_id: int,
    payload: KnowledgeDocumentPublishGateCreate,
    principal: CurrentPrincipal = Depends(require_permission(KNOWLEDGE_MANAGE_PERMISSION)),
    db: Session = Depends(get_db),
) -> KnowledgeDocumentPublishGateRead:
    return check_knowledge_document_publish_gate(
        db,
        document_id,
        payload,
        principal,
        perform_publish=True,
    )


@router.get(
    "/knowledge-documents/{document_id}/publications",
    response_model=KnowledgeDocumentPublicationList,
)
def list_tenant_knowledge_document_publications(
    document_id: int,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    principal: CurrentPrincipal = Depends(require_permission(KNOWLEDGE_MANAGE_PERMISSION)),
    db: Session = Depends(get_db),
) -> KnowledgeDocumentPublicationList:
    return list_knowledge_document_publications(
        db,
        document_id,
        principal=principal,
        page=page,
        page_size=page_size,
    )


@router.post(
    "/knowledge-documents/{document_id}/rollback",
    response_model=KnowledgeDocumentPublicationRead,
    status_code=status.HTTP_201_CREATED,
)
def rollback_tenant_knowledge_document_publication(
    document_id: int,
    payload: KnowledgeDocumentRollbackCreate,
    principal: CurrentPrincipal = Depends(require_permission(KNOWLEDGE_MANAGE_PERMISSION)),
    db: Session = Depends(get_db),
) -> KnowledgeDocumentPublicationRead:
    return rollback_knowledge_document_publication(db, document_id, payload, principal)


@router.post(
    "/tenants/{tenant_id}/knowledge-document-searches",
    response_model=KnowledgeDocumentSearchResponse,
)
def create_tenant_knowledge_document_search(
    tenant_id: int,
    payload: KnowledgeDocumentSearchRequest,
    principal: CurrentPrincipal = Depends(require_permission(KNOWLEDGE_READ_PERMISSION)),
    db: Session = Depends(get_db),
) -> KnowledgeDocumentSearchResponse:
    return search_knowledge_documents(db, tenant_id, payload, principal)


@router.post(
    "/tenants/{tenant_id}/knowledge-vector-index/rebuilds",
    response_model=KnowledgeVectorIndexRebuildRead,
    status_code=status.HTTP_201_CREATED,
)
def create_tenant_knowledge_vector_index_rebuild(
    tenant_id: int,
    payload: KnowledgeVectorIndexRebuildCreate,
    principal: CurrentPrincipal = Depends(require_permission(KNOWLEDGE_MANAGE_PERMISSION)),
    db: Session = Depends(get_db),
) -> KnowledgeVectorIndexRebuildRead:
    return rebuild_knowledge_vector_index(db, tenant_id, payload, principal)


@router.post(
    "/tenants/{tenant_id}/knowledge-vector-index/plans",
    response_model=KnowledgeVectorIndexPlanRead,
    status_code=status.HTTP_201_CREATED,
)
def create_tenant_knowledge_vector_index_plan(
    tenant_id: int,
    payload: KnowledgeVectorIndexPlanCreate,
    principal: CurrentPrincipal = Depends(require_permission(KNOWLEDGE_MANAGE_PERMISSION)),
    db: Session = Depends(get_db),
) -> KnowledgeVectorIndexPlanRead:
    return create_knowledge_vector_index_plan(db, tenant_id, payload, principal)


@router.post(
    "/tenants/{tenant_id}/knowledge-embedding-provider-smoke-runs",
    response_model=KnowledgeEmbeddingProviderSmokeRead,
    status_code=status.HTTP_201_CREATED,
)
def create_tenant_knowledge_embedding_provider_smoke_run(
    tenant_id: int,
    payload: KnowledgeEmbeddingProviderSmokeCreate,
    principal: CurrentPrincipal = Depends(require_permission(KNOWLEDGE_MANAGE_PERMISSION)),
    db: Session = Depends(get_db),
) -> KnowledgeEmbeddingProviderSmokeRead:
    return run_knowledge_embedding_provider_smoke(db, tenant_id, payload, principal)


@router.post(
    "/tenants/{tenant_id}/knowledge-update-package/previews",
    response_model=KnowledgeUpdatePackageResultRead,
)
def preview_tenant_knowledge_update_package(
    tenant_id: int,
    payload: KnowledgeUpdatePackagePreviewCreate,
    principal: CurrentPrincipal = Depends(require_permission(KNOWLEDGE_MANAGE_PERMISSION)),
    db: Session = Depends(get_db),
) -> KnowledgeUpdatePackageResultRead:
    return preview_knowledge_update_package(db, tenant_id, payload, principal)


@router.post(
    "/tenants/{tenant_id}/knowledge-update-package-imports",
    response_model=KnowledgeUpdatePackageResultRead,
    status_code=status.HTTP_201_CREATED,
)
def import_tenant_knowledge_update_package(
    tenant_id: int,
    payload: KnowledgeUpdatePackageImportCreate,
    principal: CurrentPrincipal = Depends(require_permission(KNOWLEDGE_MANAGE_PERMISSION)),
    db: Session = Depends(get_db),
) -> KnowledgeUpdatePackageResultRead:
    return import_knowledge_update_package(db, tenant_id, payload, principal)


@router.post(
    "/knowledge-update-package-imports/{import_batch_id}/rollback",
    response_model=KnowledgeUpdatePackageRollbackRead,
    status_code=status.HTTP_201_CREATED,
)
def rollback_tenant_knowledge_update_package_import(
    import_batch_id: int,
    payload: KnowledgeUpdatePackageRollbackCreate,
    principal: CurrentPrincipal = Depends(require_permission(KNOWLEDGE_MANAGE_PERMISSION)),
    db: Session = Depends(get_db),
) -> KnowledgeUpdatePackageRollbackRead:
    return rollback_knowledge_update_package_import(db, import_batch_id, payload, principal)


@router.post(
    "/tenants/{tenant_id}/knowledge-evaluation-sets",
    response_model=KnowledgeEvaluationSetRead,
    status_code=status.HTTP_201_CREATED,
)
def create_tenant_knowledge_evaluation_set(
    tenant_id: int,
    payload: KnowledgeEvaluationSetCreate,
    principal: CurrentPrincipal = Depends(require_permission(KNOWLEDGE_MANAGE_PERMISSION)),
    db: Session = Depends(get_db),
) -> KnowledgeEvaluationSetRead:
    return create_knowledge_evaluation_set(db, tenant_id, payload, principal)


@router.get(
    "/tenants/{tenant_id}/knowledge-evaluation-sets",
    response_model=KnowledgeEvaluationSetList,
)
def list_tenant_knowledge_evaluation_sets(
    tenant_id: int,
    status_filter: str | None = Query(default=None, alias="status", pattern="^(draft|active|archived)$"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    principal: CurrentPrincipal = Depends(require_permission(KNOWLEDGE_MANAGE_PERMISSION)),
    db: Session = Depends(get_db),
) -> KnowledgeEvaluationSetList:
    return list_knowledge_evaluation_sets(
        db,
        tenant_id,
        status_filter=status_filter,
        page=page,
        page_size=page_size,
        principal=principal,
    )


@router.post(
    "/tenants/{tenant_id}/customer-service-question-banks/precheck",
    response_model=CustomerServiceQuestionBankPrecheckRead,
)
def precheck_tenant_customer_service_question_bank(
    tenant_id: int,
    payload: CustomerServiceQuestionBankImportCreate,
    principal: CurrentPrincipal = Depends(require_permission(KNOWLEDGE_MANAGE_PERMISSION)),
    db: Session = Depends(get_db),
) -> CustomerServiceQuestionBankPrecheckRead:
    return precheck_customer_service_question_bank(db, tenant_id, payload, principal)


@router.post(
    "/tenants/{tenant_id}/customer-service-question-banks/import",
    response_model=CustomerServiceQuestionBankPrecheckRead,
    status_code=status.HTTP_201_CREATED,
)
def import_tenant_customer_service_question_bank(
    tenant_id: int,
    payload: CustomerServiceQuestionBankImportCreate,
    principal: CurrentPrincipal = Depends(require_permission(KNOWLEDGE_MANAGE_PERMISSION)),
    db: Session = Depends(get_db),
) -> CustomerServiceQuestionBankPrecheckRead:
    return import_customer_service_question_bank(db, tenant_id, payload, principal)


@router.post(
    "/knowledge-evaluation-sets/{evaluation_set_id}/runs",
    response_model=KnowledgeEvaluationRunRead,
    status_code=status.HTTP_201_CREATED,
)
def create_knowledge_evaluation_set_run(
    evaluation_set_id: int,
    payload: KnowledgeEvaluationRunCreate,
    principal: CurrentPrincipal = Depends(require_permission(KNOWLEDGE_MANAGE_PERMISSION)),
    db: Session = Depends(get_db),
) -> KnowledgeEvaluationRunRead:
    return run_knowledge_evaluation_set(db, evaluation_set_id, payload, principal)


@router.get(
    "/knowledge-evaluation-sets/{evaluation_set_id}/runs",
    response_model=KnowledgeEvaluationRunList,
)
def list_knowledge_evaluation_set_runs(
    evaluation_set_id: int,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    principal: CurrentPrincipal = Depends(require_permission(KNOWLEDGE_MANAGE_PERMISSION)),
    db: Session = Depends(get_db),
) -> KnowledgeEvaluationRunList:
    return list_knowledge_evaluation_runs(
        db,
        evaluation_set_id,
        page=page,
        page_size=page_size,
        principal=principal,
    )


@router.get(
    "/knowledge-evaluation-runs/{evaluation_run_id}",
    response_model=KnowledgeEvaluationRunRead,
)
def get_knowledge_evaluation_run_detail(
    evaluation_run_id: int,
    principal: CurrentPrincipal = Depends(require_permission(KNOWLEDGE_MANAGE_PERMISSION)),
    db: Session = Depends(get_db),
) -> KnowledgeEvaluationRunRead:
    return get_knowledge_evaluation_run(db, evaluation_run_id, principal)


@router.get(
    "/knowledge-evaluation-runs/{evaluation_run_id}/report",
    response_model=KnowledgeEvaluationRunReportRead,
)
def export_knowledge_evaluation_run_report_detail(
    evaluation_run_id: int,
    report_format: str = Query(default="markdown", alias="format", pattern="^(markdown|csv)$"),
    principal: CurrentPrincipal = Depends(require_permission(KNOWLEDGE_MANAGE_PERMISSION)),
    db: Session = Depends(get_db),
) -> KnowledgeEvaluationRunReportRead:
    return export_knowledge_evaluation_run_report(
        db,
        evaluation_run_id,
        report_format=report_format,
        principal=principal,
    )


@router.patch(
    "/knowledge-evaluation-run-cases/{run_case_id}/final-answer-sample",
    response_model=KnowledgeEvaluationRunCaseFinalAnswerSampleRead,
)
def patch_knowledge_evaluation_run_case_final_answer_sample(
    run_case_id: int,
    payload: KnowledgeEvaluationRunCaseFinalAnswerSampleCreate,
    principal: CurrentPrincipal = Depends(require_permission(KNOWLEDGE_MANAGE_PERMISSION)),
    db: Session = Depends(get_db),
) -> KnowledgeEvaluationRunCaseFinalAnswerSampleRead:
    return capture_knowledge_evaluation_run_case_final_answer_sample(
        db,
        run_case_id,
        payload,
        principal,
    )


@router.patch(
    "/knowledge-evaluation-run-cases/{run_case_id}/factuality-label",
    response_model=KnowledgeEvaluationRunCaseFactualityLabelRead,
)
def patch_knowledge_evaluation_run_case_factuality_label(
    run_case_id: int,
    payload: KnowledgeEvaluationRunCaseFactualityLabelCreate,
    principal: CurrentPrincipal = Depends(require_permission(KNOWLEDGE_MANAGE_PERMISSION)),
    db: Session = Depends(get_db),
) -> KnowledgeEvaluationRunCaseFactualityLabelRead:
    return label_knowledge_evaluation_run_case_factuality(
        db,
        run_case_id,
        payload,
        principal,
    )


@router.patch(
    "/knowledge-evaluation-runs/{evaluation_run_id}/factuality-labels/batch",
    response_model=KnowledgeEvaluationRunCaseFactualityBatchLabelRead,
)
def patch_knowledge_evaluation_run_case_factuality_labels_batch(
    evaluation_run_id: int,
    payload: KnowledgeEvaluationRunCaseFactualityBatchLabelCreate,
    principal: CurrentPrincipal = Depends(require_permission(KNOWLEDGE_MANAGE_PERMISSION)),
    db: Session = Depends(get_db),
) -> KnowledgeEvaluationRunCaseFactualityBatchLabelRead:
    return batch_label_knowledge_evaluation_run_case_factuality(
        db,
        evaluation_run_id,
        payload,
        principal,
    )


@router.get(
    "/knowledge-evaluation-runs/{evaluation_run_id}/final-answer-labels/export",
    response_model=KnowledgeEvaluationRunFinalAnswerLabelExportRead,
)
def export_knowledge_evaluation_run_final_answer_labels_detail(
    evaluation_run_id: int,
    export_format: str = Query(default="csv", alias="format", pattern="^csv$"),
    include_answer_text: bool = Query(default=True),
    principal: CurrentPrincipal = Depends(require_permission(KNOWLEDGE_MANAGE_PERMISSION)),
    db: Session = Depends(get_db),
) -> KnowledgeEvaluationRunFinalAnswerLabelExportRead:
    return export_knowledge_evaluation_run_final_answer_labels(
        db,
        evaluation_run_id,
        export_format=export_format,
        include_answer_text=include_answer_text,
        principal=principal,
    )


@router.post(
    "/knowledge-evaluation-runs/{evaluation_run_id}/final-answer-labels/imports",
    response_model=KnowledgeEvaluationRunFinalAnswerLabelImportRead,
)
def import_knowledge_evaluation_run_final_answer_labels_detail(
    evaluation_run_id: int,
    payload: KnowledgeEvaluationRunFinalAnswerLabelImportCreate,
    principal: CurrentPrincipal = Depends(require_permission(KNOWLEDGE_MANAGE_PERMISSION)),
    db: Session = Depends(get_db),
) -> KnowledgeEvaluationRunFinalAnswerLabelImportRead:
    return import_knowledge_evaluation_run_final_answer_labels(
        db,
        evaluation_run_id,
        payload,
        principal,
    )


@router.get(
    "/tenants/{tenant_id}/monthly-quality-review",
    response_model=MonthlyQualityReviewRead,
)
def get_tenant_monthly_quality_review(
    tenant_id: int,
    year: int | None = Query(default=None, ge=2024, le=2100),
    month: int | None = Query(default=None, ge=1, le=12),
    principal: CurrentPrincipal = Depends(require_permission(QUALITY_READ_PERMISSION)),
    db: Session = Depends(get_db),
) -> MonthlyQualityReviewRead:
    return get_monthly_quality_review(
        db,
        tenant_id,
        year=year,
        month=month,
        principal=principal,
    )


@router.get(
    "/tenants/{tenant_id}/monthly-ops-report",
    response_model=MonthlyOpsReportRead,
)
def get_tenant_monthly_ops_report(
    tenant_id: int,
    year: int | None = Query(default=None, ge=2024, le=2100),
    month: int | None = Query(default=None, ge=1, le=12),
    principal: CurrentPrincipal = Depends(require_permission(OPS_METRICS_READ_PERMISSION)),
    db: Session = Depends(get_db),
) -> MonthlyOpsReportRead:
    return get_monthly_ops_report(
        db,
        tenant_id,
        year=year,
        month=month,
        principal=principal,
    )


@router.get(
    "/tenants/{tenant_id}/customer-quality-report",
    response_model=CustomerQualityReportRead,
)
def get_tenant_customer_quality_report(
    tenant_id: int,
    year: int | None = Query(default=None, ge=2024, le=2100),
    month: int | None = Query(default=None, ge=1, le=12),
    principal: CurrentPrincipal = Depends(require_permission(QUALITY_READ_PERMISSION)),
    db: Session = Depends(get_db),
) -> CustomerQualityReportRead:
    return get_customer_quality_report(
        db,
        tenant_id,
        year=year,
        month=month,
        principal=principal,
    )


@router.get(
    "/tenants/{tenant_id}/customer-quality-report/export",
    response_model=CustomerQualityReportExportRead,
)
def export_tenant_customer_quality_report(
    tenant_id: int,
    year: int | None = Query(default=None, ge=2024, le=2100),
    month: int | None = Query(default=None, ge=1, le=12),
    export_format: str = Query(default="html", alias="format", pattern="^(html|xlsx|docx)$"),
    principal: CurrentPrincipal = Depends(require_permission(QUALITY_READ_PERMISSION)),
    db: Session = Depends(get_db),
) -> CustomerQualityReportExportRead:
    return export_customer_quality_report(
        db,
        tenant_id,
        year=year,
        month=month,
        export_format=export_format,
        principal=principal,
    )


@router.get(
    "/tenants/{tenant_id}/customer-quality-report/archives",
    response_model=CustomerQualityReportArchiveListRead,
)
def list_tenant_customer_quality_report_archives(
    tenant_id: int,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=8, ge=1, le=50),
    period: str | None = Query(default=None, pattern=r"^\d{4}-\d{2}$"),
    principal: CurrentPrincipal = Depends(require_permission(QUALITY_READ_PERMISSION)),
    db: Session = Depends(get_db),
) -> CustomerQualityReportArchiveListRead:
    return list_customer_quality_report_archives(
        db,
        tenant_id,
        page=page,
        page_size=page_size,
        period=period,
        principal=principal,
    )


@router.get(
    "/tenants/{tenant_id}/customer-quality-report/archives/{archive_event_id}/download",
    response_model=CustomerQualityReportExportRead,
)
def download_tenant_customer_quality_report_archive(
    tenant_id: int,
    archive_event_id: int,
    principal: CurrentPrincipal = Depends(require_permission(QUALITY_READ_PERMISSION)),
    db: Session = Depends(get_db),
) -> CustomerQualityReportExportRead:
    return download_customer_quality_report_archive(
        db,
        tenant_id,
        archive_event_id,
        principal=principal,
    )


@router.post(
    "/tenants/{tenant_id}/customer-quality-report/signoffs",
    response_model=CustomerQualityReportSignoffRead,
    status_code=status.HTTP_201_CREATED,
)
def record_tenant_customer_quality_report_signoff(
    tenant_id: int,
    payload: CustomerQualityReportSignoffCreate,
    year: int | None = Query(default=None, ge=2024, le=2100),
    month: int | None = Query(default=None, ge=1, le=12),
    principal: CurrentPrincipal = Depends(require_permission(CUSTOMER_REPORT_SIGNOFF_PERMISSION)),
    db: Session = Depends(get_db),
) -> CustomerQualityReportSignoffRead:
    return record_customer_quality_report_signoff(
        db,
        tenant_id,
        payload,
        year=year,
        month=month,
        principal=principal,
    )


@router.get(
    "/tenants/{tenant_id}/customer-quality-report/signoffs",
    response_model=CustomerQualityReportSignoffListRead,
)
def list_tenant_customer_quality_report_signoffs(
    tenant_id: int,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=8, ge=1, le=50),
    period: str | None = Query(default=None, pattern=r"^\d{4}-\d{2}$"),
    principal: CurrentPrincipal = Depends(require_permission(CUSTOMER_REPORT_SIGNOFF_PERMISSION)),
    db: Session = Depends(get_db),
) -> CustomerQualityReportSignoffListRead:
    return list_customer_quality_report_signoffs(
        db,
        tenant_id,
        page=page,
        page_size=page_size,
        period=period,
        principal=principal,
    )


@router.get("/tenants/{tenant_id}/knowledge-gaps", response_model=KnowledgeGapList)
def list_tenant_knowledge_gaps(
    tenant_id: int,
    status_filter: str | None = Query(
        default=None,
        alias="status",
        pattern="^(open|triaged|in_progress|resolved|rejected|archived)$",
    ),
    severity_filter: str | None = Query(
        default=None,
        alias="severity",
        pattern="^(low|medium|high|critical)$",
    ),
    source_type: str | None = Query(default=None, pattern="^(human_review|evaluation_run|manual|reply_decision)$"),
    query: str | None = Query(default=None, max_length=120),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    principal: CurrentPrincipal = Depends(require_permission(KNOWLEDGE_MANAGE_PERMISSION)),
    db: Session = Depends(get_db),
) -> KnowledgeGapList:
    return list_knowledge_gaps(
        db,
        tenant_id,
        status_filter=status_filter,
        severity_filter=severity_filter,
        source_type=source_type,
        query=query,
        page=page,
        page_size=page_size,
        principal=principal,
    )


@router.post(
    "/tenants/{tenant_id}/knowledge-gaps/sync",
    response_model=KnowledgeGapSyncRead,
    status_code=status.HTTP_201_CREATED,
)
def sync_tenant_knowledge_gaps(
    tenant_id: int,
    payload: KnowledgeGapSyncCreate,
    principal: CurrentPrincipal = Depends(require_permission(KNOWLEDGE_MANAGE_PERMISSION)),
    db: Session = Depends(get_db),
) -> KnowledgeGapSyncRead:
    return sync_knowledge_gaps(db, tenant_id, payload, principal)


@router.patch("/knowledge-gaps/{gap_id}", response_model=KnowledgeGapRead)
def patch_knowledge_gap(
    gap_id: int,
    payload: KnowledgeGapUpdate,
    principal: CurrentPrincipal = Depends(require_permission(KNOWLEDGE_MANAGE_PERMISSION)),
    db: Session = Depends(get_db),
) -> KnowledgeGapRead:
    return update_knowledge_gap(db, gap_id, payload, principal)


@router.post(
    "/knowledge-gaps/{gap_id}/document-drafts",
    response_model=KnowledgeGapDocumentDraftRead,
    status_code=status.HTTP_201_CREATED,
)
def create_knowledge_gap_document_draft_detail(
    gap_id: int,
    principal: CurrentPrincipal = Depends(require_permission(KNOWLEDGE_MANAGE_PERMISSION)),
    db: Session = Depends(get_db),
) -> KnowledgeGapDocumentDraftRead:
    return create_knowledge_gap_document_draft(db, gap_id, principal)


@router.post(
    "/knowledge-gaps/{gap_id}/regression-cases",
    response_model=KnowledgeGapRegressionCaseRead,
    status_code=status.HTTP_201_CREATED,
)
def create_knowledge_gap_regression_case_detail(
    gap_id: int,
    principal: CurrentPrincipal = Depends(require_permission(KNOWLEDGE_MANAGE_PERMISSION)),
    db: Session = Depends(get_db),
) -> KnowledgeGapRegressionCaseRead:
    return create_knowledge_gap_regression_case(db, gap_id, principal)


@router.post(
    "/tenants/{tenant_id}/knowledge-searches",
    response_model=KnowledgeSearchResponse,
)
def create_tenant_knowledge_search(
    tenant_id: int,
    payload: KnowledgeSearchRequest,
    principal: CurrentPrincipal = Depends(require_permission(KNOWLEDGE_READ_PERMISSION)),
    db: Session = Depends(get_db),
) -> KnowledgeSearchResponse:
    return search_knowledge_cards(db, tenant_id, payload, principal)
