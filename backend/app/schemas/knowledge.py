from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


KnowledgeStatusPattern = "^(draft|active|archived)$"
KnowledgeGapStatusPattern = "^(open|triaged|in_progress|resolved|rejected|archived)$"
KnowledgeGapSeverityPattern = "^(low|medium|high|critical)$"
KnowledgeGapSourcePattern = "^(human_review|evaluation_run|manual|reply_decision)$"
BusinessObjectTypePattern = "^(product|service|package|course|project|store)$"
FactualityLabelStatusPattern = "^(correct|partially_correct|incorrect|needs_human_review|not_applicable)$"
FinalAnswerSampleSourcePattern = "^(manual_capture|system_capture|dry_run_fixture|imported_sample)$"
CustomerQualityReportSignoffStatusPattern = "^(accepted|accepted_with_notes|needs_rework|rejected)$"
CustomerQualityReportSignoffMethodPattern = "^(local_record|email_confirmation|meeting_confirmation|offline_signature)$"


class KnowledgeCardCreate(BaseModel):
    title: str = Field(min_length=1, max_length=180)
    question: str = Field(default="", max_length=12000)
    answer: str = Field(min_length=1, max_length=24000)
    source_type: str = Field(default="manual", max_length=40)
    source_uri: str = Field(default="", max_length=500)
    tags: list[str] = Field(default_factory=list, max_length=20)
    aliases: list[str] = Field(default_factory=list, max_length=20)
    status: str = Field(default="draft", pattern=KnowledgeStatusPattern)


class KnowledgeCardUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=180)
    question: Optional[str] = Field(default=None, max_length=12000)
    answer: Optional[str] = Field(default=None, min_length=1, max_length=24000)
    source_type: Optional[str] = Field(default=None, max_length=40)
    source_uri: Optional[str] = Field(default=None, max_length=500)
    tags: Optional[list[str]] = Field(default=None, max_length=20)
    aliases: Optional[list[str]] = Field(default=None, max_length=20)
    status: Optional[str] = Field(default=None, pattern=KnowledgeStatusPattern)


class KnowledgeCardRead(BaseModel):
    id: int
    tenant_id: int
    title: str
    question: str
    answer: str
    source_type: str
    source_uri: str
    tags: list[str]
    aliases: list[str]
    status: str
    created_by_id: Optional[int] = None
    updated_by_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class KnowledgeCardList(BaseModel):
    items: list[KnowledgeCardRead]
    page: int
    page_size: int
    total: int


class KnowledgeSearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=4000)
    top_k: int = Field(default=5, ge=1, le=20)
    status: str = Field(default="active", pattern=KnowledgeStatusPattern)
    min_score: float = Field(default=0.0, ge=0)


class KnowledgeSearchMatch(BaseModel):
    card: KnowledgeCardRead
    score: float
    confidence: float
    matched_terms: list[str]


class KnowledgeSearchResponse(BaseModel):
    query: str
    retrieval_mode: str
    total_candidates: int
    matches: list[KnowledgeSearchMatch]


class BusinessObjectCreate(BaseModel):
    type: str = Field(pattern=BusinessObjectTypePattern)
    title: str = Field(min_length=1, max_length=180)
    external_id: str = Field(default="", max_length=120)
    summary: str = Field(default="", max_length=12000)
    attrs_json: dict[str, Any] = Field(default_factory=dict)
    aliases: list[str] = Field(default_factory=list, max_length=30)
    status: str = Field(default="active", pattern=KnowledgeStatusPattern)


class BusinessObjectUpdate(BaseModel):
    type: Optional[str] = Field(default=None, pattern=BusinessObjectTypePattern)
    title: Optional[str] = Field(default=None, min_length=1, max_length=180)
    external_id: Optional[str] = Field(default=None, max_length=120)
    summary: Optional[str] = Field(default=None, max_length=12000)
    attrs_json: Optional[dict[str, Any]] = None
    aliases: Optional[list[str]] = Field(default=None, max_length=30)
    status: Optional[str] = Field(default=None, pattern=KnowledgeStatusPattern)


class BusinessObjectRead(BaseModel):
    id: int
    tenant_id: int
    type: str
    title: str
    external_id: str
    summary: str
    attrs_json: dict[str, Any]
    aliases: list[str]
    knowledge_card_count: int
    status: str
    created_by_id: Optional[int] = None
    updated_by_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class BusinessObjectList(BaseModel):
    items: list[BusinessObjectRead]
    page: int
    page_size: int
    total: int


class ObjectKnowledgeCardCreate(BaseModel):
    question: str = Field(min_length=1, max_length=12000)
    answer: str = Field(min_length=1, max_length=24000)
    trigger_keywords: list[str] = Field(default_factory=list, max_length=30)
    media_refs: list[str] = Field(default_factory=list, max_length=20)
    scope: dict[str, Any] = Field(default_factory=dict)
    source: str = Field(default="manual", max_length=120)
    version: int = Field(default=1, ge=1, le=100000)
    status: str = Field(default="active", pattern=KnowledgeStatusPattern)


class ObjectKnowledgeCardRead(BaseModel):
    id: int
    tenant_id: int
    business_object_id: int
    question: str
    answer: str
    trigger_keywords: list[str]
    media_refs: list[str]
    scope: dict[str, Any]
    source: str
    version: int
    status: str
    created_by_id: Optional[int] = None
    updated_by_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ObjectKnowledgeCardList(BaseModel):
    items: list[ObjectKnowledgeCardRead]
    page: int
    page_size: int
    total: int


class KnowledgeDocumentCreate(BaseModel):
    title: str = Field(min_length=1, max_length=180)
    source_type: str = Field(default="manual_document", max_length=40)
    source_uri: str = Field(default="", max_length=500)
    raw_text: str = Field(min_length=1, max_length=200000)
    tags: list[str] = Field(default_factory=list, max_length=20)
    status: str = Field(default="draft", pattern=KnowledgeStatusPattern)
    chunk_size: int = Field(default=900, ge=80, le=4000)
    chunk_overlap: int = Field(default=120, ge=0, le=1000)


class KnowledgeDocumentRead(BaseModel):
    id: int
    tenant_id: int
    title: str
    source_type: str
    source_uri: str
    content_hash: str
    tags: list[str]
    status: str
    ingestion_status: str
    chunk_count: int
    created_by_id: Optional[int] = None
    updated_by_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class KnowledgeDocumentList(BaseModel):
    items: list[KnowledgeDocumentRead]
    page: int
    page_size: int
    total: int


class KnowledgeChunkRead(BaseModel):
    id: int
    tenant_id: int
    document_id: int
    chunk_index: int
    section_title: str
    page_number: Optional[int] = None
    content: str
    content_hash: str
    source_uri: str
    char_start: int
    char_end: int
    token_count: int
    embedding_signature: dict[str, Any]
    embedding_provider: str
    embedding_model: str
    embedding_dimension: int
    vector_store: str
    vector_index_status: str
    status: str
    citation: dict[str, Any]
    created_at: Optional[datetime] = None


class KnowledgeDocumentSearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=4000)
    top_k: int = Field(default=5, ge=1, le=20)
    status: str = Field(default="active", pattern=KnowledgeStatusPattern)
    min_score: float = Field(default=0.0, ge=0)


class KnowledgeDocumentSearchMatch(BaseModel):
    chunk_id: int
    document_id: int
    document_title: str
    chunk_index: int
    section_title: str
    source_type: str
    source_uri: str
    content_preview: str
    score: float
    confidence: float
    bm25_score: float
    vector_score: float
    reranker_score: float
    matched_terms: list[str]
    citation: dict[str, Any]


class KnowledgeDocumentSearchResponse(BaseModel):
    query: str
    retrieval_mode: str
    vector_engine: str
    vector_store: str
    retrieval_backend: str
    vector_index_status: str
    embedding_provider: str
    embedding_model: str
    reranker: str
    total_candidates: int
    matches: list[KnowledgeDocumentSearchMatch]


class KnowledgeMeshNodeRead(BaseModel):
    key: str
    label: str
    status: str
    total_count: int
    healthy_count: int
    risk_count: int
    evidence: str
    next_action: str


class KnowledgeMeshProvenanceStepRead(BaseModel):
    key: str
    label: str
    status: str
    observed_count: int
    evidence: str
    blocker: str = ""


class KnowledgeMemoryMeshOverviewRead(BaseModel):
    schema_version: str
    tenant_id: int
    generated_at: datetime
    status: str
    summary: str
    nodes: list[KnowledgeMeshNodeRead]
    provenance_steps: list[KnowledgeMeshProvenanceStepRead]
    source_authority: dict[str, Any]
    quality_loop: dict[str, Any]
    readiness: dict[str, Any]
    boundaries: dict[str, Any]


class KnowledgeVectorIndexRebuildCreate(BaseModel):
    status: str = Field(default="active", pattern=KnowledgeStatusPattern)
    document_id: Optional[int] = None


class KnowledgeVectorIndexRebuildRead(BaseModel):
    tenant_id: int
    document_id: Optional[int] = None
    status: str
    vector_store: str
    retrieval_backend: str
    vector_index_status: str
    embedding_provider: str
    embedding_model: str
    embedding_dimension: int
    reranker: str
    total_chunks: int
    reindexed_chunks: int
    skipped_chunks: int
    failed_chunks: int
    failure_reasons: list[str] = Field(default_factory=list)


class KnowledgeVectorIndexPlanCreate(BaseModel):
    status: str = Field(default="active", pattern=KnowledgeStatusPattern)
    document_id: Optional[int] = None
    requested_strategy: str = Field(default="auto", pattern="^(auto|exact|hnsw|ivfflat)$")
    dry_run: bool = True
    concurrent_build: bool = True
    maintenance_window: str = Field(default="off_peak", max_length=80)
    max_index_build_seconds: int = Field(default=900, ge=30, le=86400)
    target_chunk_count_override: Optional[int] = Field(default=None, ge=0, le=10000000)


class KnowledgeVectorIndexPlanRead(BaseModel):
    id: int
    tenant_id: int
    document_id: Optional[int] = None
    status_filter: str
    plan_status: str
    requested_strategy: str
    selected_strategy: str
    index_method: str
    index_name: str
    vector_store: str
    retrieval_backend: str
    embedding_provider: str
    embedding_model: str
    embedding_dimension: int
    target_chunk_count: int
    estimated_build_seconds: int
    estimated_memory_mb: int
    maintenance_window: str
    maintenance_window_required: bool
    dry_run: bool
    execute_performed: bool
    concurrent_build: bool
    ddl_statements: list[str]
    rollback_statements: list[str]
    safety_checks: dict[str, Any]
    recommendation_reasons: list[str]
    query_options: dict[str, Any]
    created_by_id: Optional[int] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class KnowledgeEmbeddingProviderSmokeCreate(BaseModel):
    sample_text: str = Field(
        default="公开知识库 embedding provider smoke 测试文本。",
        min_length=1,
        max_length=2000,
    )
    allow_external_call: bool = False
    purpose: str = Field(default="embedding_provider_smoke", max_length=80)
    privacy_level: str = Field(default="business_internal_no_pii", max_length=80)


class KnowledgeEmbeddingProviderSmokeRead(BaseModel):
    id: int
    tenant_id: int
    status: str
    purpose: str
    privacy_level: str
    embedding_provider: str
    embedding_model: str
    vector_engine: str
    vector_store: str
    embedding_dimension: int
    output_dimension: int
    input_text_hash: str
    input_character_count: int
    estimated_input_tokens: int
    latency_ms: int
    pricing_input_per_1k_tokens: float
    estimated_cost: float
    cost_currency: str
    provider_call_performed: bool
    raw_text_logged: bool
    quality_checks: dict[str, Any]
    response_metadata: dict[str, Any]
    error_message: str
    created_by_id: Optional[int] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class KnowledgeEvaluationCaseCreate(BaseModel):
    external_case_id: str = Field(default="", max_length=120)
    source_channel: str = Field(default="", max_length=80)
    source_category: str = Field(default="", max_length=120)
    question: str = Field(min_length=1, max_length=4000)
    question_type: str = Field(default="standard_customer_question", max_length=80)
    expected_terms: list[str] = Field(default_factory=list, max_length=30)
    expected_source_uri: str = Field(default="", max_length=500)
    expected_document_title: str = Field(default="", max_length=180)
    expected_chunk_ids: list[int] = Field(default_factory=list, max_length=50)
    must_have_all_evidence: bool = False
    expected_human_review: bool = False
    allow_auto_reply: bool = True
    forbidden_terms: list[str] = Field(default_factory=list, max_length=30)
    risk_level: str = Field(default="low", max_length=32)
    annotation_notes: str = Field(default="", max_length=2000)
    required_citation: bool = True
    priority: int = Field(default=100, ge=1, le=9999)
    status: str = Field(default="active", pattern=KnowledgeStatusPattern)


class KnowledgeEvaluationSetCreate(BaseModel):
    name: str = Field(min_length=1, max_length=180)
    description: str = Field(default="", max_length=12000)
    status: str = Field(default="draft", pattern=KnowledgeStatusPattern)
    evaluation_mode: str = Field(default="document_retrieval", pattern="^(document_retrieval|customer_service_retrieval)$")
    cases: list[KnowledgeEvaluationCaseCreate] = Field(default_factory=list, max_length=500)


class KnowledgeEvaluationCaseRead(BaseModel):
    id: int
    tenant_id: int
    evaluation_set_id: int
    external_case_id: str
    source_channel: str
    source_category: str
    question: str
    question_type: str
    expected_terms: list[str]
    expected_source_uri: str
    expected_document_title: str
    expected_chunk_ids: list[int]
    must_have_all_evidence: bool
    expected_human_review: bool
    allow_auto_reply: bool
    forbidden_terms: list[str]
    risk_level: str
    annotation_notes: str
    required_citation: bool
    priority: int
    status: str
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class KnowledgeEvaluationSetRead(BaseModel):
    id: int
    tenant_id: int
    name: str
    description: str
    status: str
    evaluation_mode: str
    case_count: int
    cases: list[KnowledgeEvaluationCaseRead] = Field(default_factory=list)
    created_by_id: Optional[int] = None
    updated_by_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class KnowledgeEvaluationSetList(BaseModel):
    items: list[KnowledgeEvaluationSetRead]
    page: int
    page_size: int
    total: int


class CustomerServiceQuestionBankImportCreate(BaseModel):
    name: str = Field(min_length=1, max_length=180)
    description: str = Field(default="", max_length=12000)
    source_label: str = Field(default="customer_desensitized_question_bank", max_length=160)
    status: str = Field(default="active", pattern=KnowledgeStatusPattern)
    evaluation_mode: str = Field(default="customer_service_retrieval", pattern="^(customer_service_retrieval)$")
    minimum_case_count: int = Field(default=50, ge=1, le=500)
    maximum_case_count: int = Field(default=100, ge=1, le=500)
    allow_sensitive_rows: bool = False
    cases: list[KnowledgeEvaluationCaseCreate] = Field(default_factory=list, max_length=500)


class CustomerServiceQuestionBankPrecheckRead(BaseModel):
    tenant_id: int
    status: str
    can_import: bool
    imported: bool
    evaluation_set_id: Optional[int] = None
    case_count: int
    coverage_summary: dict[str, Any]
    sensitive_rows: list[dict[str, Any]]
    validation_errors: list[str]
    case_catalog: list[dict[str, Any]]
    raw_text_included: bool
    provider_call_performed: bool
    external_write_performed: bool


class KnowledgeEvaluationRunCreate(BaseModel):
    top_k: int = Field(default=5, ge=1, le=20)
    min_score: float = Field(default=0.0, ge=0)
    status: str = Field(default="active", pattern=KnowledgeStatusPattern)
    search_status: Optional[str] = Field(default=None, pattern=KnowledgeStatusPattern)
    low_confidence_threshold: float = Field(default=0.45, ge=0, le=1)


class KnowledgeEvaluationRunCaseRead(BaseModel):
    id: int
    tenant_id: int
    evaluation_run_id: int
    evaluation_case_id: int
    question: str
    status: str
    top_score: float
    top_confidence: float
    top_chunk_id: Optional[int] = None
    top_document_id: Optional[int] = None
    citation_present: bool
    expected_terms_found: bool
    matched_terms: list[str]
    failure_reason: str
    result_payload: dict[str, Any]
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class KnowledgeEvaluationRunRead(BaseModel):
    id: int
    tenant_id: int
    evaluation_set_id: int
    run_mode: str
    retrieval_mode: str
    vector_engine: str
    total_cases: int
    answered_cases: int
    no_hit_cases: int
    passed_cases: int
    failed_cases: int
    needs_review_cases: int
    citation_covered_cases: int
    expected_term_covered_cases: int
    hit_rate: float
    citation_coverage: float
    expected_term_coverage: float
    average_confidence: float
    unsupported_answer_rate: Optional[float] = None
    summary_payload: dict[str, Any]
    case_results: list[KnowledgeEvaluationRunCaseRead]
    created_by_id: Optional[int] = None
    created_at: Optional[datetime] = None


class KnowledgeEvaluationRunSummaryRead(BaseModel):
    id: int
    tenant_id: int
    evaluation_set_id: int
    run_mode: str
    retrieval_mode: str
    vector_engine: str
    total_cases: int
    answered_cases: int
    no_hit_cases: int
    passed_cases: int
    failed_cases: int
    needs_review_cases: int
    citation_covered_cases: int
    expected_term_covered_cases: int
    hit_rate: float
    citation_coverage: float
    expected_term_coverage: float
    average_confidence: float
    unsupported_answer_rate: Optional[float] = None
    summary_payload: dict[str, Any]
    created_by_id: Optional[int] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class KnowledgeEvaluationRunList(BaseModel):
    items: list[KnowledgeEvaluationRunSummaryRead]
    page: int
    page_size: int
    total: int


class KnowledgeEvaluationRunReportRead(BaseModel):
    evaluation_run_id: int
    evaluation_set_id: int
    tenant_id: int
    report_format: str
    filename: str
    content_type: str
    body: str
    raw_text_included: bool
    provider_call_performed: bool
    external_write_performed: bool
    summary: dict[str, Any]


class KnowledgeEvaluationRunCaseFactualityLabelCreate(BaseModel):
    final_answer_factuality_status: str = Field(pattern=FactualityLabelStatusPattern)
    citation_sufficient: Optional[bool] = None
    forbidden_commitment_passed: Optional[bool] = None
    handoff_correct: Optional[bool] = None
    reviewer_notes: str = Field(default="", max_length=2000)


class KnowledgeEvaluationRunCaseFinalAnswerSampleCreate(BaseModel):
    final_answer_text: str = Field(min_length=1, max_length=8000)
    final_answer_source: str = Field(default="manual_capture", pattern=FinalAnswerSampleSourcePattern)
    citation_uris: list[str] = Field(default_factory=list, max_length=50)
    answer_author: str = Field(default="", max_length=120)
    reviewer_notes: str = Field(default="", max_length=2000)


class KnowledgeEvaluationRunCaseFinalAnswerSampleRead(BaseModel):
    tenant_id: int
    evaluation_run_id: int
    evaluation_run_case_id: int
    final_answer_sampled_cases: int
    final_answer_sample_coverage: float
    total_cases: int
    updated_run: KnowledgeEvaluationRunRead
    audit_raw_text_included: bool
    model_call_performed: bool
    external_platform_write_performed: bool


class KnowledgeEvaluationRunCaseFactualityBatchLabelItem(BaseModel):
    evaluation_run_case_id: int
    final_answer_factuality_status: str = Field(pattern=FactualityLabelStatusPattern)
    citation_sufficient: Optional[bool] = None
    forbidden_commitment_passed: Optional[bool] = None
    handoff_correct: Optional[bool] = None
    reviewer_notes: str = Field(default="", max_length=2000)


class KnowledgeEvaluationRunCaseFactualityBatchLabelCreate(BaseModel):
    labels: list[KnowledgeEvaluationRunCaseFactualityBatchLabelItem] = Field(min_length=1, max_length=200)


class KnowledgeEvaluationRunCaseFactualityBatchLabelRead(BaseModel):
    tenant_id: int
    evaluation_run_id: int
    labeled_cases: int
    final_answer_factuality_rate: Optional[float] = None
    final_answer_factuality_labeled_cases: int
    total_cases: int
    updated_run: KnowledgeEvaluationRunRead
    audit_raw_text_included: bool
    model_call_performed: bool
    external_platform_write_performed: bool


class KnowledgeEvaluationRunCaseFactualityLabelRead(BaseModel):
    tenant_id: int
    evaluation_run_id: int
    evaluation_run_case_id: int
    final_answer_factuality_status: str
    final_answer_factuality_measured: bool
    final_answer_factuality_rate: Optional[float] = None
    final_answer_factuality_labeled_cases: int
    total_cases: int
    updated_run: KnowledgeEvaluationRunRead
    raw_text_included: bool
    model_call_performed: bool
    external_platform_write_performed: bool


class KnowledgeEvaluationRunFinalAnswerLabelExportRead(BaseModel):
    tenant_id: int
    evaluation_run_id: int
    evaluation_set_id: int
    schema_version: str
    export_format: str
    filename: str
    content_type: str
    body: str
    row_count: int
    raw_text_included: bool
    question_raw_text_included: bool
    final_answer_text_included: bool
    provider_call_performed: bool
    external_write_performed: bool
    summary: dict[str, Any]


class KnowledgeEvaluationRunFinalAnswerLabelImportCreate(BaseModel):
    import_format: str = Field(default="csv", pattern="^csv$")
    content: str = Field(min_length=1, max_length=2_000_000)
    dry_run: bool = True


class KnowledgeEvaluationRunFinalAnswerLabelImportRead(BaseModel):
    tenant_id: int
    evaluation_run_id: int
    evaluation_set_id: int
    schema_version: str
    import_format: str
    dry_run: bool
    imported: bool
    total_rows: int
    matched_rows: int
    sample_rows: int
    label_rows: int
    skipped_rows: int
    validation_errors: list[dict[str, Any]]
    warnings: list[str]
    status_counts: dict[str, int]
    updated_run: Optional[KnowledgeEvaluationRunRead] = None
    audit_raw_text_included: bool
    provider_call_performed: bool
    external_write_performed: bool


class KnowledgeUpdatePackageBusinessObjectCreate(BusinessObjectCreate):
    ref: str = Field(default="", max_length=120)


class KnowledgeUpdatePackageObjectKnowledgeCardCreate(ObjectKnowledgeCardCreate):
    business_object_ref: str = Field(default="", max_length=120)
    business_object_id: Optional[int] = None
    business_object_type: str = Field(default="", max_length=40)
    business_object_title: str = Field(default="", max_length=180)


class KnowledgeUpdatePackagePayload(BaseModel):
    schema_version: str = Field(max_length=80)
    package_id: str = Field(min_length=1, max_length=160)
    package_name: str = Field(min_length=1, max_length=180)
    source_diagnostic_filename: str = Field(default="", max_length=300)
    notes: str = Field(default="", max_length=4000)
    knowledge_cards: list[KnowledgeCardCreate] = Field(default_factory=list, max_length=500)
    business_objects: list[KnowledgeUpdatePackageBusinessObjectCreate] = Field(default_factory=list, max_length=300)
    object_knowledge_cards: list[KnowledgeUpdatePackageObjectKnowledgeCardCreate] = Field(
        default_factory=list,
        max_length=1000,
    )
    knowledge_documents: list[KnowledgeDocumentCreate] = Field(default_factory=list, max_length=100)
    evaluation_sets: list[KnowledgeEvaluationSetCreate] = Field(default_factory=list, max_length=50)


class KnowledgeUpdatePackagePreviewCreate(BaseModel):
    package: KnowledgeUpdatePackagePayload


class KnowledgeUpdatePackageImportCreate(BaseModel):
    package: KnowledgeUpdatePackagePayload


class KnowledgeUpdatePackageOperationRead(BaseModel):
    action: str
    resource_type: str
    title: str
    reason: str
    ref: str = ""
    target: dict[str, Any] = Field(default_factory=dict)


class KnowledgeUpdatePackageResultRead(BaseModel):
    tenant_id: int
    package_id: str
    package_name: str
    schema_version: str
    dry_run: bool
    can_apply: bool
    import_batch_id: Optional[int] = None
    operation_counts: dict[str, int]
    operations: list[KnowledgeUpdatePackageOperationRead]
    created: dict[str, list[int]]
    skipped: list[dict[str, Any]]
    errors: list[dict[str, Any]]
    warnings: list[str]
    backup_snapshot: dict[str, Any]
    safety: dict[str, Any]


class KnowledgeUpdatePackageRollbackCreate(BaseModel):
    reason: str = Field(default="客户管理员确认回滚本次知识更新包。", max_length=1000)


class KnowledgeUpdatePackageRollbackRead(BaseModel):
    tenant_id: int
    import_batch_id: int
    rollback_status: str
    archived_counts: dict[str, int]
    reason: str
    safety: dict[str, Any]


class KnowledgeDocumentPublishGateCreate(BaseModel):
    evaluation_set_id: Optional[int] = None
    evaluation_case_ids: list[int] = Field(default_factory=list, max_length=100)
    top_k: int = Field(default=8, ge=1, le=20)
    min_score: float = Field(default=0.0, ge=0)
    search_status: Optional[str] = Field(default=None, pattern=KnowledgeStatusPattern)
    low_confidence_threshold: float = Field(default=0.45, ge=0, le=1)
    min_hit_rate: float = Field(default=1.0, ge=0, le=1)
    min_citation_coverage: float = Field(default=1.0, ge=0, le=1)
    min_expected_term_coverage: float = Field(default=1.0, ge=0, le=1)
    require_regression_case: bool = True
    ignore_safe_handoff_failures: bool = True


class KnowledgeDocumentPublishGateCaseRead(BaseModel):
    evaluation_case_id: int
    status: str
    failure_reason: str
    blocking: bool
    advisory: bool
    top_confidence: float
    top_chunk_id: Optional[int] = None
    citation_present: bool
    expected_terms_found: bool
    matched_terms: list[str]


class KnowledgeDocumentPublishGateRead(BaseModel):
    document: KnowledgeDocumentRead
    gap: Optional["KnowledgeGapRead"] = None
    evaluation_set_id: Optional[int] = None
    evaluation_run: Optional[KnowledgeEvaluationRunRead] = None
    checked_case_ids: list[int]
    case_results: list[KnowledgeDocumentPublishGateCaseRead]
    can_publish: bool
    published: bool
    blocking_reasons: list[str]
    advisory_reasons: list[str]
    checks: dict[str, Any]
    message: str


class KnowledgeDocumentPublicationRead(BaseModel):
    id: int
    tenant_id: int
    document_id: int
    gap_id: Optional[int] = None
    publication_type: str
    status: str
    from_status: str
    to_status: str
    evaluation_set_id: Optional[int] = None
    evaluation_run_id: Optional[int] = None
    checked_case_ids: list[int]
    case_results: list[dict[str, Any]]
    blocking_reasons: list[str]
    advisory_reasons: list[str]
    checks: dict[str, Any]
    document_snapshot: dict[str, Any]
    previous_publication_id: Optional[int] = None
    rollback_target_publication_id: Optional[int] = None
    rollback_reason: str
    external_write_performed: bool
    model_call_performed: bool
    created_by_id: Optional[int] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class KnowledgeDocumentPublicationList(BaseModel):
    items: list[KnowledgeDocumentPublicationRead]
    page: int
    page_size: int
    total: int


class MonthlyQualityReviewMetricRead(BaseModel):
    key: str
    label: str
    value: str
    numeric_value: Optional[float] = None
    status: str
    detail: str


class MonthlyQualityReviewCauseRead(BaseModel):
    key: str
    label: str
    count: int
    severity: str
    detail: str
    next_action: str
    target_href: str


class MonthlyQualityReviewActionRead(BaseModel):
    key: str
    label: str
    owner: str
    priority: str
    evidence: str
    next_step: str
    target_href: str
    status: str


class MonthlyQualityReviewRead(BaseModel):
    tenant_id: int
    schema_version: str
    period: str
    period_start: datetime
    period_end: datetime
    generated_at: datetime
    latest_evaluation_run_id: Optional[int] = None
    latest_evaluation_set_id: Optional[int] = None
    previous_evaluation_run_id: Optional[int] = None
    metrics: list[MonthlyQualityReviewMetricRead]
    root_causes: list[MonthlyQualityReviewCauseRead]
    action_items: list[MonthlyQualityReviewActionRead]
    knowledge_gap_summary: dict[str, int]
    human_review_summary: dict[str, int]
    reply_decision_summary: dict[str, int]
    trend_summary: dict[str, Any]
    data_boundaries: list[str]
    next_review_steps: list[str]
    raw_text_included: bool
    model_call_performed: bool
    external_call_performed: bool
    external_platform_write_performed: bool


class MonthlyOpsReportMetricRead(BaseModel):
    key: str
    label: str
    value: str
    status: str
    detail: str


class MonthlyOpsReportSectionRead(BaseModel):
    key: str
    title: str
    status: str
    summary: str
    metrics: list[MonthlyOpsReportMetricRead]
    evidence: list[dict[str, Any]]
    next_steps: list[str]


class MonthlyOpsReportRiskRead(BaseModel):
    key: str
    label: str
    severity: str
    detail: str
    recommended_action: str


class MonthlyOpsReportRead(BaseModel):
    tenant_id: int
    schema_version: str
    period: str
    period_start: datetime
    period_end: datetime
    generated_at: datetime
    report_status: str
    status_label: str
    health_score: int
    health_label: str
    monthly_health: MonthlyOpsReportSectionRead
    reply_quality: MonthlyOpsReportSectionRead
    knowledge_maintenance: MonthlyOpsReportSectionRead
    model_cost: MonthlyOpsReportSectionRead
    local_maintenance: MonthlyOpsReportSectionRead
    risk_items: list[MonthlyOpsReportRiskRead]
    next_month_actions: list[str]
    upstream_evidence: dict[str, Any]
    data_boundaries: list[str]
    safety: dict[str, Any]
    raw_text_included: bool
    draft_text_included: bool
    secret_included: bool
    external_call_performed: bool
    external_platform_write_performed: bool
    real_platform_send_ready: bool
    production_sla_ready: bool
    formal_customer_signoff_ready: bool


class CustomerQualityReportMetricRead(BaseModel):
    key: str
    label: str
    value: str
    status: str
    detail: str


class CustomerQualityReportSectionRead(BaseModel):
    key: str
    title: str
    status: str
    summary: str
    evidence: str
    next_steps: list[str]


class CustomerQualityReportActionRead(BaseModel):
    key: str
    label: str
    owner: str
    priority: str
    status: str
    evidence: str
    next_step: str


class CustomerQualityReportGapRehearsalEvidenceRead(BaseModel):
    schema_version: str
    phase: str
    evidence_source: str
    case_count: int
    auto_reply_label_count: int
    handoff_not_applicable_count: int
    auto_reply_factuality_rate: float
    citation_sufficient_rate: float
    forbidden_commitment_pass_rate: float
    handoff_correct_rate: float
    ready_for_gap_quality_report_review: bool
    ready_for_formal_accuracy_signoff: bool
    final_answer_text_exported: bool
    provider_call_performed: bool
    real_platform_send_performed: bool
    external_platform_write_performed: bool
    conclusion: str
    boundary: str


class CustomerQualityReportRead(BaseModel):
    tenant_id: int
    schema_version: str
    report_title: str
    period: str
    period_start: datetime
    period_end: datetime
    generated_at: datetime
    report_status: str
    report_status_label: str
    report_confidence_score: int
    quality_conclusion: str
    executive_summary: list[str]
    headline_metrics: list[CustomerQualityReportMetricRead]
    sections: list[CustomerQualityReportSectionRead]
    action_plan: list[CustomerQualityReportActionRead]
    gap_rehearsal_evidence: Optional[CustomerQualityReportGapRehearsalEvidenceRead] = None
    signoff_checklist: list[str]
    data_boundaries: list[str]
    source_monthly_review_schema_version: str
    latest_evaluation_run_id: Optional[int] = None
    latest_evaluation_set_id: Optional[int] = None
    raw_text_included: bool
    model_call_performed: bool
    external_call_performed: bool
    external_platform_write_performed: bool


class CustomerQualityReportExportRead(BaseModel):
    tenant_id: int
    schema_version: str
    report_schema_version: str
    export_format: str
    filename: str
    content_type: str
    body: str
    body_encoding: str = "utf-8"
    body_sha256: str = ""
    body_bytes: int = 0
    period: str
    generated_at: datetime
    report_status: str
    report_status_label: str
    signoff_status: str
    signoff_record: dict[str, Any]
    archived: bool = False
    archive_audit_event_id: Optional[int] = None
    raw_text_included: bool
    final_answer_text_included: bool
    reviewer_notes_included: bool
    electronic_signature_performed: bool = False
    formal_contract_signoff_performed: bool = False
    model_call_performed: bool
    external_call_performed: bool
    external_platform_write_performed: bool


class CustomerQualityReportArchiveItemRead(BaseModel):
    audit_event_id: int
    tenant_id: int
    schema_version: str
    report_schema_version: str
    export_schema_version: str
    export_format: str
    filename: str
    content_type: str
    body_encoding: str
    body_sha256: str
    body_bytes: int
    period: str
    generated_at: datetime
    report_status: str
    report_status_label: str
    signoff_status: str
    body_archived: bool
    download_supported: bool
    raw_text_included: bool
    final_answer_text_included: bool
    reviewer_notes_included: bool
    electronic_signature_performed: bool
    formal_contract_signoff_performed: bool
    model_call_performed: bool
    external_call_performed: bool
    external_platform_write_performed: bool


class CustomerQualityReportArchiveListRead(BaseModel):
    tenant_id: int
    schema_version: str
    page: int
    page_size: int
    total: int
    items: list[CustomerQualityReportArchiveItemRead]
    raw_text_included: bool
    final_answer_text_included: bool
    reviewer_notes_included: bool
    electronic_signature_performed: bool
    formal_contract_signoff_performed: bool
    model_call_performed: bool
    external_call_performed: bool
    external_platform_write_performed: bool


class CustomerQualityReportSignoffCreate(BaseModel):
    signoff_status: str = Field(pattern=CustomerQualityReportSignoffStatusPattern)
    signer_name: str = Field(min_length=1, max_length=80)
    signer_role: str = Field(default="", max_length=80)
    signer_organization: str = Field(default="", max_length=120)
    confirmation_method: str = Field(default="local_record", pattern=CustomerQualityReportSignoffMethodPattern)
    notes: str = Field(default="", max_length=1000)


class CustomerQualityReportSignoffRead(BaseModel):
    tenant_id: int
    schema_version: str
    report_schema_version: str
    export_schema_version: str
    period: str
    report_status: str
    report_status_label: str
    report_confidence_score: int
    signoff_status: str
    signoff_status_label: str
    signer_display_name: str
    signer_role: str
    signer_organization: str
    confirmation_method: str
    confirmation_method_label: str
    notes_recorded: bool
    notes_hash: str
    notes_length: int
    recorded_at: datetime
    recorded_by_user_id: int
    audit_action: str
    audit_resource_id: str
    raw_text_included: bool
    final_answer_text_included: bool
    reviewer_notes_included: bool
    signer_name_raw_included: bool
    electronic_signature_performed: bool
    formal_contract_signoff_performed: bool
    model_call_performed: bool
    external_call_performed: bool
    external_platform_write_performed: bool


class CustomerQualityReportSignoffListItemRead(BaseModel):
    audit_event_id: int
    tenant_id: int
    schema_version: str
    report_schema_version: str
    export_schema_version: str
    period: str
    report_status: str
    report_status_label: str
    report_confidence_score: int
    signoff_status: str
    signoff_status_label: str
    signer_display_name: str
    signer_role: str
    signer_organization: str
    confirmation_method: str
    confirmation_method_label: str
    notes_recorded: bool
    notes_hash: str
    notes_length: int
    recorded_at: datetime
    recorded_by_user_id: Optional[int] = None
    audit_action: str
    audit_resource_id: str
    raw_text_included: bool
    final_answer_text_included: bool
    reviewer_notes_included: bool
    signer_name_raw_included: bool
    electronic_signature_performed: bool
    formal_contract_signoff_performed: bool
    model_call_performed: bool
    external_call_performed: bool
    external_platform_write_performed: bool


class CustomerQualityReportSignoffListRead(BaseModel):
    tenant_id: int
    schema_version: str
    page: int
    page_size: int
    total: int
    items: list[CustomerQualityReportSignoffListItemRead]
    raw_text_included: bool
    final_answer_text_included: bool
    reviewer_notes_included: bool
    signer_name_raw_included: bool
    model_call_performed: bool
    external_call_performed: bool
    external_platform_write_performed: bool


class KnowledgeDocumentRollbackCreate(BaseModel):
    target_publication_id: Optional[int] = None
    rollback_reason: str = Field(default="人工确认后回退为草稿，暂停进入正式检索范围。", max_length=1000)


class KnowledgeGapRead(BaseModel):
    id: int
    tenant_id: int
    status: str
    severity: str
    source_type: str
    source_ref: str
    source_title: str
    source_excerpt: str
    question_excerpt: str
    gap_type: str
    expected_terms: list[str]
    evidence_payload: dict[str, Any]
    linked_knowledge_card_id: Optional[int] = None
    linked_knowledge_document_id: Optional[int] = None
    assigned_user_id: Optional[int] = None
    created_by_id: Optional[int] = None
    updated_by_id: Optional[int] = None
    resolved_by_id: Optional[int] = None
    resolution_note: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class KnowledgeGapList(BaseModel):
    items: list[KnowledgeGapRead]
    page: int
    page_size: int
    total: int


class KnowledgeGapSyncCreate(BaseModel):
    include_human_review: bool = True
    include_evaluation_runs: bool = True
    evaluation_run_id: Optional[int] = None
    low_confidence_threshold: float = Field(default=0.45, ge=0, le=1)
    max_items: int = Field(default=100, ge=1, le=300)


class KnowledgeGapSyncRead(BaseModel):
    created_count: int
    existing_count: int
    scanned_count: int
    items: list[KnowledgeGapRead]


class KnowledgeGapUpdate(BaseModel):
    status: Optional[str] = Field(default=None, pattern=KnowledgeGapStatusPattern)
    severity: Optional[str] = Field(default=None, pattern=KnowledgeGapSeverityPattern)
    assigned_user_id: Optional[int] = None
    resolution_note: Optional[str] = Field(default=None, max_length=12000)
    linked_knowledge_card_id: Optional[int] = None
    linked_knowledge_document_id: Optional[int] = None


class KnowledgeGapDocumentDraftRead(BaseModel):
    gap: KnowledgeGapRead
    document: KnowledgeDocumentRead
    created: bool
    draft_text: str


class KnowledgeGapRegressionCaseRead(BaseModel):
    gap: KnowledgeGapRead
    evaluation_set: KnowledgeEvaluationSetRead
    evaluation_case: KnowledgeEvaluationCaseRead
    created: bool
