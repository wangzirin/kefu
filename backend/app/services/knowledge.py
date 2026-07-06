import csv
import base64
import hashlib
import html
import io
import json
import math
import re
import zipfile
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from fastapi import HTTPException, status
from sqlalchemy import String, cast, delete, func, or_, select, text
from sqlalchemy.orm import Session

from app.api.tenants import require_tenant
from app.core.audit import add_audit_event
from app.core.auth import CurrentPrincipal
from app.core.config import Settings, get_settings
from app.models import (
    AuditEvent,
    BusinessObject,
    BusinessObjectAlias,
    CustomerMaterialBatch,
    HumanReviewTask,
    KnowledgeCard,
    KnowledgeDocument,
    KnowledgeDocumentChunk,
    KnowledgeDocumentPublication,
    KnowledgeEmbeddingProviderSmokeRun,
    KnowledgeEvaluationCase,
    KnowledgeGapItem,
    KnowledgeEvaluationRun,
    KnowledgeEvaluationRunCase,
    KnowledgeEvaluationSet,
    KnowledgeImportBatch,
    KnowledgeVectorIndexPlan,
    ModelCallRecord,
    Message,
    ObjectKnowledgeCard,
    ReplyCitationSnapshot,
    ReplyDecision,
    User,
)
from app.models.foundation import utc_now
from app.schemas.knowledge import (
    BusinessObjectCreate,
    BusinessObjectList,
    BusinessObjectRead,
    BusinessObjectUpdate,
    CustomerQualityReportActionRead,
    CustomerQualityReportArchiveItemRead,
    CustomerQualityReportArchiveListRead,
    CustomerQualityReportExportRead,
    CustomerQualityReportGapRehearsalEvidenceRead,
    CustomerQualityReportMetricRead,
    CustomerQualityReportRead,
    CustomerQualityReportSectionRead,
    CustomerQualityReportSignoffCreate,
    CustomerQualityReportSignoffListItemRead,
    CustomerQualityReportSignoffListRead,
    CustomerQualityReportSignoffRead,
    KnowledgeCardCreate,
    KnowledgeCardList,
    KnowledgeCardUpdate,
    KnowledgeChunkRead,
    CustomerServiceQuestionBankImportCreate,
    CustomerServiceQuestionBankPrecheckRead,
    KnowledgeDocumentCreate,
    KnowledgeDocumentList,
    KnowledgeDocumentPublishGateCaseRead,
    KnowledgeDocumentPublishGateCreate,
    KnowledgeDocumentPublishGateRead,
    KnowledgeDocumentPublicationList,
    KnowledgeDocumentPublicationRead,
    KnowledgeDocumentRollbackCreate,
    KnowledgeDocumentSearchMatch,
    KnowledgeDocumentSearchRequest,
    KnowledgeDocumentSearchResponse,
    KnowledgeEmbeddingProviderSmokeCreate,
    KnowledgeEmbeddingProviderSmokeRead,
    KnowledgeEvaluationCaseCreate,
    KnowledgeEvaluationCaseRead,
    KnowledgeEvaluationRunCaseRead,
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
    KnowledgeEvaluationRunSummaryRead,
    KnowledgeEvaluationSetCreate,
    KnowledgeEvaluationSetList,
    KnowledgeEvaluationSetRead,
    KnowledgeGapDocumentDraftRead,
    KnowledgeGapList,
    KnowledgeGapRead,
    KnowledgeGapRegressionCaseRead,
    KnowledgeGapSyncCreate,
    KnowledgeGapSyncRead,
    KnowledgeGapUpdate,
    KnowledgeMemoryMeshOverviewRead,
    KnowledgeMeshNodeRead,
    KnowledgeMeshProvenanceStepRead,
    MonthlyQualityReviewActionRead,
    MonthlyQualityReviewCauseRead,
    MonthlyQualityReviewMetricRead,
    MonthlyQualityReviewRead,
    MonthlyOpsReportMetricRead,
    MonthlyOpsReportRead,
    MonthlyOpsReportRiskRead,
    MonthlyOpsReportSectionRead,
    KnowledgeSearchMatch,
    KnowledgeSearchRequest,
    KnowledgeSearchResponse,
    KnowledgeUpdatePackageImportCreate,
    KnowledgeUpdatePackagePayload,
    KnowledgeUpdatePackagePreviewCreate,
    KnowledgeUpdatePackageResultRead,
    KnowledgeUpdatePackageRollbackCreate,
    KnowledgeUpdatePackageRollbackRead,
    KnowledgeUpdatePackageOperationRead,
    KnowledgeVectorIndexPlanCreate,
    KnowledgeVectorIndexPlanRead,
    KnowledgeVectorIndexRebuildCreate,
    KnowledgeVectorIndexRebuildRead,
    ObjectKnowledgeCardCreate,
    ObjectKnowledgeCardList,
    ObjectKnowledgeCardRead,
)
from app.services.local_maintenance import build_local_maintenance_readiness


RETRIEVAL_MODE = "lexical_bm25_v1"
DOCUMENT_RETRIEVAL_MODE = "hybrid_bm25_vector_rerank_v1"
DETERMINISTIC_EMBEDDING_PROVIDER = "deterministic_local"
DETERMINISTIC_EMBEDDING_MODEL = "deterministic-token-vector-v1"
DETERMINISTIC_VECTOR_ENGINE = "deterministic_local_hash_embedding_v1"
OPENAI_COMPATIBLE_EMBEDDING_PROVIDER = "openai_compatible"
DEFAULT_VECTOR_STORE = "sqlite_json_vector_store"
PGVECTOR_VECTOR_STORE = "postgres_pgvector_store_v1"
PGVECTOR_VECTOR_STORE_ALIASES = {"pgvector", "postgres_pgvector", PGVECTOR_VECTOR_STORE}
JSON_VECTOR_RETRIEVAL_BACKEND = "python_json_vector_scan"
PGVECTOR_RETRIEVAL_BACKEND = "postgres_pgvector_exact_cosine_v1"
PGVECTOR_HNSW_RETRIEVAL_BACKEND = "postgres_pgvector_hnsw_cosine_v1"
PGVECTOR_IVFFLAT_RETRIEVAL_BACKEND = "postgres_pgvector_ivfflat_cosine_v1"
DEFAULT_RERANKER = "lexical_overlap_reranker_v1"
TOKEN_RE = re.compile(r"[a-z0-9]+|[\u4e00-\u9fff]+")
SECTION_RE = re.compile(r"^\s{0,3}#{1,6}\s+(.+?)\s*$")
REPORT_CSV_FIELDS_REDACTED = [
    "external_case_id",
    "source_channel",
    "source_category",
    "question_hash",
    "question_type",
    "risk_level",
    "status",
    "failure_reason",
    "knowledge_gap",
    "top_confidence",
    "top_score",
    "top_chunk_id",
    "top_document_id",
    "citation_present",
    "expected_terms_found",
    "full_evidence_recalled_at_5",
    "citation_precision",
    "expected_human_review",
    "predicted_human_review",
    "human_review_prediction_correct",
    "allow_auto_reply",
    "forbidden_term_hits",
    "expected_chunk_ids",
    "returned_chunk_ids_top_k",
    "top_source_uri",
    "top_document_title",
]
HUMAN_REVIEW_KNOWLEDGE_GAP_REASONS = {
    "low_confidence",
    "no_knowledge",
    "missing_knowledge",
    "knowledge_gap",
    "no_hit",
    "retrieval_empty",
}
EVALUATION_KNOWLEDGE_GAP_REASONS = {
    "no_hit",
    "low_confidence",
    "expected_terms_missing",
    "expected_evidence_missing",
    "citation_missing",
    "no_citation",
    "no_answer",
}
KNOWLEDGE_GAP_RESOLUTION_STATUSES = {"resolved", "rejected", "archived"}
KNOWLEDGE_GAP_REMEDIATION_SET_NAME = "知识缺口回归题库"
PUBLISH_GATE_BLOCKING_FAILURE_REASONS = {
    "no_retrieval_hit",
    "no_hit",
    "expected_terms_missing",
    "expected_source_missing",
    "expected_document_missing",
    "expected_evidence_missing",
    "citation_missing",
    "no_citation",
    "low_confidence_needs_review",
    "forbidden_terms_in_evidence",
}
PUBLISH_GATE_SAFE_HANDOFF_REASONS = {"auto_reply_not_allowed", "risk_requires_review"}
KNOWLEDGE_UPDATE_PACKAGE_SCHEMA_VERSION = "wanfa.knowledge_update_package.v1"
KNOWLEDGE_MEMORY_MESH_SCHEMA_VERSION = "p3-06u-26h2w-nc4.knowledge_memory_mesh_overview.v1"


@dataclass(frozen=True)
class EmbeddingProfile:
    provider: str
    model: str
    vector_engine: str
    vector_store: str
    reranker: str
    dimensions: int
    api_base: str
    api_key: str


@dataclass(frozen=True)
class EmbeddingResult:
    profile: EmbeddingProfile
    vector: list[float]
    terms: dict[str, float]
    status: str
    error_message: str = ""
    input_character_count: int = 0
    estimated_input_tokens: int = 0
    latency_ms: int = 0
    pricing_input_per_1k_tokens: float = 0.0
    estimated_cost: float = 0.0
    cost_currency: str = "CNY"
    provider_call_performed: bool = False
    response_metadata: dict | None = None


def _require_same_tenant(db: Session, tenant_id: int, principal: CurrentPrincipal) -> None:
    require_tenant(db, tenant_id)
    if principal.tenant.id != tenant_id:
        raise HTTPException(status_code=404, detail="tenant not found")


def _require_knowledge_manager(principal: CurrentPrincipal) -> None:
    if not {"owner", "admin"}.intersection(principal.roles):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="owner or admin role required",
        )


def _count_rows(db: Session, model: type, *filters: Any) -> int:
    return int(db.scalar(select(func.count(model.id)).where(*filters)) or 0)


def _mesh_node(
    *,
    key: str,
    label: str,
    total_count: int,
    healthy_count: int,
    risk_count: int,
    evidence: str,
    next_action: str,
) -> KnowledgeMeshNodeRead:
    if total_count <= 0:
        status_value = "waiting"
    elif risk_count > 0:
        status_value = "partial"
    else:
        status_value = "ready"
    return KnowledgeMeshNodeRead(
        key=key,
        label=label,
        status=status_value,
        total_count=total_count,
        healthy_count=healthy_count,
        risk_count=risk_count,
        evidence=evidence,
        next_action=next_action,
    )


def _mesh_step(
    *,
    key: str,
    label: str,
    observed_count: int,
    evidence: str,
    blocker: str = "",
    optional: bool = False,
) -> KnowledgeMeshProvenanceStepRead:
    if observed_count > 0:
        status_value = "ready"
    elif optional:
        status_value = "waiting"
    else:
        status_value = "blocked"
    return KnowledgeMeshProvenanceStepRead(
        key=key,
        label=label,
        status=status_value,
        observed_count=observed_count,
        evidence=evidence,
        blocker=blocker,
    )


def _clean_string_list(values: list[str]) -> list[str]:
    cleaned: list[str] = []
    seen: set[str] = set()
    for value in values:
        item = value.strip()
        if not item or item in seen:
            continue
        cleaned.append(item)
        seen.add(item)
    return cleaned


def _clean_int_list(values: list[int]) -> list[int]:
    cleaned: list[int] = []
    seen: set[int] = set()
    for value in values:
        try:
            item = int(value)
        except (TypeError, ValueError):
            continue
        if item <= 0 or item in seen:
            continue
        cleaned.append(item)
        seen.add(item)
    return cleaned


def _short_excerpt(value: str | None, *, limit: int = 240) -> str:
    text_value = re.sub(r"\s+", " ", (value or "").strip())
    if len(text_value) <= limit:
        return text_value
    return text_value[: max(limit - 3, 0)].rstrip() + "..."


def _safe_float(value: object, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_int(value: object, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _ratio(count: int, total: int) -> float:
    if total <= 0:
        return 0.0
    return round(count / total, 4)


def _tokenize(text: str) -> list[str]:
    tokens: list[str] = []
    for segment in TOKEN_RE.findall(text.lower()):
        if segment.isascii():
            tokens.append(segment)
            continue
        tokens.append(segment)
        if len(segment) <= 1:
            continue
        tokens.extend(segment[index : index + 2] for index in range(len(segment) - 1))
        if len(segment) >= 3:
            tokens.extend(segment[index : index + 3] for index in range(len(segment) - 2))
    return tokens


def _meaningful_terms(terms: set[str]) -> set[str]:
    return {term for term in terms if len(term) >= 2 or term.isascii()}


def _card_tokens(card: KnowledgeCard) -> list[str]:
    tokens: list[str] = []
    tokens.extend(_tokenize(card.title) * 3)
    tokens.extend(_tokenize(card.question) * 2)
    tokens.extend(_tokenize(card.answer))
    tokens.extend(_tokenize(" ".join(card.tags)) * 2)
    tokens.extend(_tokenize(" ".join(card.aliases)) * 3)
    return tokens


def _bm25_score(
    query_terms: set[str],
    document_terms: list[str],
    document_frequencies: Counter[str],
    document_count: int,
    average_length: float,
) -> float:
    if not query_terms or not document_terms or document_count == 0:
        return 0.0
    term_counts = Counter(document_terms)
    length = len(document_terms)
    k1 = 1.5
    b = 0.75
    score = 0.0
    for term in query_terms:
        frequency = term_counts.get(term, 0)
        if frequency == 0:
            continue
        df = document_frequencies.get(term, 0)
        idf = math.log(1 + (document_count - df + 0.5) / (df + 0.5))
        denominator = frequency + k1 * (1 - b + b * length / max(average_length, 1))
        score += idf * ((frequency * (k1 + 1)) / denominator)
    return score


def _confidence_from_score(score: float) -> float:
    if score <= 0:
        return 0.0
    return round(min(0.99, score / (score + 4.0)), 4)


def _content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _token_vector(tokens: list[str]) -> dict[str, float]:
    counts = Counter(_meaningful_terms(set(tokens)))
    for token in tokens:
        if token in counts:
            counts[token] += 1
    total = math.sqrt(sum(value * value for value in counts.values())) or 1.0
    return {term: round(value / total, 6) for term, value in counts.most_common(80)}


def _dense_hash_embedding(tokens: list[str], *, dimensions: int) -> list[float]:
    safe_dimensions = max(8, min(dimensions, 4096))
    vector = [0.0] * safe_dimensions
    for token, count in Counter(tokens).items():
        if token not in _meaningful_terms({token}):
            continue
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        bucket = int.from_bytes(digest[:4], "big") % safe_dimensions
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        vector[bucket] += float(count) * sign
    norm = math.sqrt(sum(value * value for value in vector))
    if norm <= 0:
        return vector
    return [round(value / norm, 6) for value in vector]


def _cosine_from_vectors(left: dict[str, float], right: dict[str, float]) -> float:
    if not left or not right:
        return 0.0
    terms = set(left).intersection(right)
    return sum(left[term] * right[term] for term in terms)


def _cosine_from_dense_vectors(left: list[float], right: list[float]) -> float:
    if not left or not right:
        return 0.0
    length = min(len(left), len(right))
    if length == 0:
        return 0.0
    return sum(float(left[index]) * float(right[index]) for index in range(length))


def _normalize_vector_store(value: str) -> str:
    normalized = (value or DEFAULT_VECTOR_STORE).strip()
    if normalized in PGVECTOR_VECTOR_STORE_ALIASES:
        return PGVECTOR_VECTOR_STORE
    return normalized or DEFAULT_VECTOR_STORE


def _is_pgvector_store(value: str) -> bool:
    return _normalize_vector_store(value) == PGVECTOR_VECTOR_STORE


def _database_dialect(db: Session) -> str:
    return db.get_bind().dialect.name


def _estimate_embedding_input_tokens(text: str, tokens: list[str]) -> int:
    # This is an observability estimate, not a billing-grade tokenizer.
    return max(len(tokens), math.ceil(len(text) / 4), 1)


def _embedding_cost(*, estimated_input_tokens: int, settings: Settings) -> float:
    price = max(0.0, float(settings.knowledge_embedding_price_per_1k_tokens))
    if price <= 0:
        return 0.0
    return round((estimated_input_tokens / 1000.0) * price, 8)


def _vector_norm(vector: list[float]) -> float:
    if not vector:
        return 0.0
    return round(math.sqrt(sum(float(value) * float(value) for value in vector)), 6)


def _embedding_quality_checks(result: EmbeddingResult) -> dict:
    vector_norm = _vector_norm(result.vector)
    return {
        "dimension_positive": len(result.vector) > 0,
        "vector_norm": vector_norm,
        "vector_norm_nonzero": vector_norm > 0,
        "provider_status": result.status,
    }


def _retrieval_backend_for_profile(profile: EmbeddingProfile, db: Session) -> str:
    if _is_pgvector_store(profile.vector_store):
        return PGVECTOR_RETRIEVAL_BACKEND
    return JSON_VECTOR_RETRIEVAL_BACKEND


def _require_vector_store_available(profile: EmbeddingProfile, db: Session) -> None:
    if _is_pgvector_store(profile.vector_store) and _database_dialect(db) != "postgresql":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="knowledge vector store pgvector requires PostgreSQL; refusing silent JSON fallback",
        )


def _pgvector_literal(vector: list[float]) -> str:
    return "[" + ",".join(f"{float(value):.8f}" for value in vector) + "]"


def _build_pgvector_candidate_sql() -> str:
    return """
        SELECT
            c.id AS chunk_id,
            c.embedding_pgvector <=> CAST(:query_vector AS vector) AS vector_distance
        FROM knowledge_document_chunks c
        JOIN knowledge_documents d ON d.id = c.document_id
        WHERE c.tenant_id = :tenant_id
          AND c.status = :status
          AND d.status = :status
          AND c.vector_index_status = 'indexed'
          AND c.embedding_provider = :embedding_provider
          AND c.embedding_model = :embedding_model
          AND c.embedding_dimension = :embedding_dimension
          AND c.embedding_pgvector IS NOT NULL
        ORDER BY c.embedding_pgvector <=> CAST(:query_vector AS vector)
        LIMIT :candidate_limit
    """


def _safe_sql_literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _safe_identifier_fragment(value: str) -> str:
    fragment = re.sub(r"[^a-zA-Z0-9]+", "_", value.lower()).strip("_")
    return fragment[:18] or "x"


def _ivfflat_lists(target_chunk_count: int) -> int:
    if target_chunk_count <= 0:
        return 1
    if target_chunk_count <= 1_000_000:
        return max(1, min(32_768, target_chunk_count // 1000 or 1))
    return max(1, int(math.sqrt(target_chunk_count)))


def _index_build_seconds(index_method: str, target_chunk_count: int, embedding_dimension: int) -> int:
    if index_method == "none" or target_chunk_count <= 0:
        return 0
    scale = max(1.0, embedding_dimension / 256.0)
    if index_method == "hnsw":
        return max(30, int((target_chunk_count * math.log2(target_chunk_count + 2) * scale) / 2500))
    if index_method == "ivfflat":
        return max(30, int((target_chunk_count * scale) / 4000))
    return 0


def _index_memory_mb(index_method: str, target_chunk_count: int, embedding_dimension: int) -> int:
    if index_method == "none" or target_chunk_count <= 0:
        return 0
    vector_bytes = max(1, target_chunk_count) * max(1, embedding_dimension) * 4
    multiplier = 2.2 if index_method == "hnsw" else 1.35
    return max(128, int((vector_bytes * multiplier) / (1024 * 1024)))


def _build_pgvector_ann_index_plan(
    *,
    index_method: str,
    target_chunk_count: int,
    embedding_provider: str,
    embedding_model: str,
    embedding_dimension: int,
    concurrent_build: bool,
    status_filter: str = "active",
) -> dict:
    safe_method = index_method if index_method in {"hnsw", "ivfflat"} else "hnsw"
    provider_model_hash = _content_hash(f"{embedding_provider}:{embedding_model}:{embedding_dimension}")[:8]
    index_name = (
        f"ix_kdc_pgvec_{safe_method}_cos_d{embedding_dimension}_"
        f"{_safe_identifier_fragment(embedding_provider)}_{provider_model_hash}"
    )[:62]
    concurrently = " CONCURRENTLY" if concurrent_build else ""
    vector_expression = f"(embedding_pgvector::vector({embedding_dimension})) vector_cosine_ops"
    partial_predicate = "\n    AND ".join(
        [
            "vector_index_status = 'indexed'",
            "embedding_pgvector IS NOT NULL",
            f"status = {_safe_sql_literal(status_filter)}",
            f"embedding_provider = {_safe_sql_literal(embedding_provider)}",
            f"embedding_model = {_safe_sql_literal(embedding_model)}",
            f"embedding_dimension = {int(embedding_dimension)}",
        ]
    )
    if safe_method == "hnsw":
        options = "WITH (m = 16, ef_construction = 64)"
        query_options = {"hnsw.ef_search": 100, "hnsw.iterative_scan": "strict_order"}
        reasons = [
            "HNSW is the default ANN recommendation for medium knowledge bases because it usually has better speed/recall tradeoff than IVFFlat.",
            "Current embedding_pgvector column has no fixed dimension, so the ANN index uses expression indexing with embedding_pgvector::vector(n).",
        ]
    else:
        lists = _ivfflat_lists(target_chunk_count)
        probes = max(1, math.ceil(math.sqrt(lists)))
        options = f"WITH (lists = {lists})"
        query_options = {"ivfflat.lists": lists, "ivfflat.probes": probes, "ivfflat.iterative_scan": "relaxed_order"}
        reasons = [
            "IVFFlat is selected for very large or memory-sensitive knowledge bases; it builds faster and uses less memory than HNSW but needs recall tuning.",
            "IVFFlat lists follow pgvector's starting point: rows / 1000 up to 1M rows, sqrt(rows) above 1M rows.",
        ]
    ddl = (
        f"CREATE INDEX{concurrently} IF NOT EXISTS {index_name}\n"
        "ON knowledge_document_chunks\n"
        f"USING {safe_method} ({vector_expression})\n"
        f"{options}\n"
        f"WHERE {partial_predicate};"
    )
    drop_concurrently = " CONCURRENTLY" if concurrent_build else ""
    return {
        "index_name": index_name,
        "index_method": safe_method,
        "ddl_statements": [ddl],
        "rollback_statements": [f"DROP INDEX{drop_concurrently} IF EXISTS {index_name};"],
        "query_options": query_options,
        "recommendation_reasons": reasons,
        "estimated_build_seconds": _index_build_seconds(safe_method, target_chunk_count, embedding_dimension),
        "estimated_memory_mb": _index_memory_mb(safe_method, target_chunk_count, embedding_dimension),
    }


def _select_vector_index_strategy(
    *,
    requested_strategy: str,
    vector_store: str,
    database_dialect: str,
    target_chunk_count: int,
    embedding_dimension: int,
) -> tuple[str, str, str, list[str]]:
    if not _is_pgvector_store(vector_store):
        return (
            "python_json_exact_scan",
            "none",
            JSON_VECTOR_RETRIEVAL_BACKEND,
            ["Current vector store is JSON vector scan; ANN index is not applicable until PostgreSQL + pgvector is enabled."],
        )
    if database_dialect != "postgresql":
        return (
            "blocked_non_postgresql",
            "none",
            PGVECTOR_RETRIEVAL_BACKEND,
            ["pgvector ANN index planning requires PostgreSQL for execution; this dry-run records the block without silent fallback."],
        )
    if embedding_dimension > 2000:
        return (
            "blocked_unsupported_dimension",
            "none",
            PGVECTOR_RETRIEVAL_BACKEND,
            ["pgvector vector indexes support up to 2000 dimensions for vector; use halfvec, subvector, or dimensionality reduction before ANN."],
        )
    requested = requested_strategy or "auto"
    if requested == "exact" or (requested == "auto" and target_chunk_count < 10_000):
        return (
            "postgres_pgvector_exact_scan",
            "none",
            PGVECTOR_RETRIEVAL_BACKEND,
            ["Exact pgvector scan keeps perfect recall and is cheaper for small knowledge bases under 10000 chunks."],
        )
    if requested == "ivfflat" or (requested == "auto" and target_chunk_count > 500_000):
        return (
            "postgres_pgvector_ivfflat_ann",
            "ivfflat",
            PGVECTOR_IVFFLAT_RETRIEVAL_BACKEND,
            ["IVFFlat is selected for very large or memory-sensitive indexes; it must be recall-tested against exact search."],
        )
    return (
        "postgres_pgvector_hnsw_ann",
        "hnsw",
        PGVECTOR_HNSW_RETRIEVAL_BACKEND,
        ["HNSW is selected for medium-size production RAG because it usually offers a better speed/recall tradeoff than IVFFlat."],
    )


def _pgvector_candidate_scores(
    db: Session,
    *,
    tenant_id: int,
    status_filter: str,
    query_embedding: EmbeddingResult,
    candidate_limit: int,
) -> dict[int, float]:
    _require_vector_store_available(query_embedding.profile, db)
    rows = db.execute(
        text(_build_pgvector_candidate_sql()),
        {
            "tenant_id": tenant_id,
            "status": status_filter,
            "embedding_provider": query_embedding.profile.provider,
            "embedding_model": query_embedding.profile.model,
            "embedding_dimension": len(query_embedding.vector),
            "query_vector": _pgvector_literal(query_embedding.vector),
            "candidate_limit": candidate_limit,
        },
    ).mappings()
    scores: dict[int, float] = {}
    for row in rows:
        distance = float(row["vector_distance"] or 0.0)
        scores[int(row["chunk_id"])] = round(max(0.0, 1.0 - distance), 6)
    return scores


def _write_pgvector_chunk_vector(db: Session, *, chunk_id: int, vector: list[float]) -> None:
    db.execute(
        text(
            """
            UPDATE knowledge_document_chunks
            SET embedding_pgvector = CAST(:embedding_vector AS vector)
            WHERE id = :chunk_id
            """
        ),
        {"chunk_id": chunk_id, "embedding_vector": _pgvector_literal(vector)},
    )


def _resolve_embedding_profile(settings: Settings | None = None) -> EmbeddingProfile:
    settings = settings or get_settings()
    provider = (settings.knowledge_embedding_provider or DETERMINISTIC_EMBEDDING_PROVIDER).strip()
    if provider == "auto":
        provider = (
            OPENAI_COMPATIBLE_EMBEDDING_PROVIDER
            if settings.knowledge_embedding_api_key and settings.knowledge_embedding_api_base
            else DETERMINISTIC_EMBEDDING_PROVIDER
        )
    if provider == DETERMINISTIC_EMBEDDING_PROVIDER:
        model = settings.knowledge_embedding_model or DETERMINISTIC_EMBEDDING_MODEL
        if model == DETERMINISTIC_EMBEDDING_MODEL:
            vector_engine = DETERMINISTIC_VECTOR_ENGINE
        else:
            vector_engine = f"{DETERMINISTIC_VECTOR_ENGINE}:{model}"
    elif provider == OPENAI_COMPATIBLE_EMBEDDING_PROVIDER:
        configured_model = settings.knowledge_embedding_model
        model = (
            "text-embedding-v1"
            if not configured_model or configured_model == DETERMINISTIC_EMBEDDING_MODEL
            else configured_model
        )
        vector_engine = "openai_compatible_embedding_v1"
    else:
        model = settings.knowledge_embedding_model
        vector_engine = f"unsupported_embedding_provider:{provider}"
    return EmbeddingProfile(
        provider=provider,
        model=model,
        vector_engine=vector_engine,
        vector_store=_normalize_vector_store(settings.knowledge_vector_store),
        reranker=settings.knowledge_reranker or DEFAULT_RERANKER,
        dimensions=max(8, settings.knowledge_embedding_dimensions),
        api_base=settings.knowledge_embedding_api_base,
        api_key=settings.knowledge_embedding_api_key,
    )


def _embedding_signature(
    result: EmbeddingResult,
    *,
    terms: dict[str, float],
) -> dict:
    vector_hash = _content_hash(json.dumps(result.vector, ensure_ascii=True, separators=(",", ":")))[:32]
    return {
        "engine": result.profile.vector_engine,
        "provider": result.profile.provider,
        "model": result.profile.model,
        "dimension": len(result.vector),
        "vector_store": result.profile.vector_store,
        "status": result.status,
        "vector_hash": vector_hash,
        "terms": terms,
    }


def _embed_text(text: str, *, settings: Settings | None = None) -> EmbeddingResult:
    settings = settings or get_settings()
    profile = _resolve_embedding_profile(settings)
    tokens = _tokenize(text)
    terms = _token_vector(tokens)
    input_character_count = len(text)
    estimated_input_tokens = _estimate_embedding_input_tokens(text, tokens)
    pricing = max(0.0, float(settings.knowledge_embedding_price_per_1k_tokens))
    cost_currency = settings.knowledge_embedding_cost_currency
    if profile.provider == DETERMINISTIC_EMBEDDING_PROVIDER:
        started_at = perf_counter()
        vector = _dense_hash_embedding(tokens, dimensions=profile.dimensions)
        return EmbeddingResult(
            profile=profile,
            vector=vector,
            terms=terms,
            status="indexed",
            input_character_count=input_character_count,
            estimated_input_tokens=estimated_input_tokens,
            latency_ms=max(0, int((perf_counter() - started_at) * 1000)),
            pricing_input_per_1k_tokens=pricing,
            estimated_cost=_embedding_cost(estimated_input_tokens=estimated_input_tokens, settings=settings),
            cost_currency=cost_currency,
            provider_call_performed=False,
            response_metadata={"usage": {"estimated_input_tokens": estimated_input_tokens}},
        )
    if profile.provider != OPENAI_COMPATIBLE_EMBEDDING_PROVIDER:
        return EmbeddingResult(
            profile=profile,
            vector=[],
            terms=terms,
            status="unavailable",
            error_message=f"unsupported embedding provider: {profile.provider}",
            input_character_count=input_character_count,
            estimated_input_tokens=estimated_input_tokens,
            pricing_input_per_1k_tokens=pricing,
            estimated_cost=_embedding_cost(estimated_input_tokens=estimated_input_tokens, settings=settings),
            cost_currency=cost_currency,
            response_metadata={"usage": {"estimated_input_tokens": estimated_input_tokens}},
        )
    if not profile.api_key:
        return EmbeddingResult(
            profile=profile,
            vector=[],
            terms=terms,
            status="unavailable",
            error_message="embedding provider API key is not configured",
            input_character_count=input_character_count,
            estimated_input_tokens=estimated_input_tokens,
            pricing_input_per_1k_tokens=pricing,
            estimated_cost=_embedding_cost(estimated_input_tokens=estimated_input_tokens, settings=settings),
            cost_currency=cost_currency,
            response_metadata={"usage": {"estimated_input_tokens": estimated_input_tokens}},
        )
    if not profile.api_base:
        return EmbeddingResult(
            profile=profile,
            vector=[],
            terms=terms,
            status="unavailable",
            error_message="embedding provider API base is not configured",
            input_character_count=input_character_count,
            estimated_input_tokens=estimated_input_tokens,
            pricing_input_per_1k_tokens=pricing,
            estimated_cost=_embedding_cost(estimated_input_tokens=estimated_input_tokens, settings=settings),
            cost_currency=cost_currency,
            response_metadata={"usage": {"estimated_input_tokens": estimated_input_tokens}},
        )
    payload = {"model": profile.model, "input": text}
    request = Request(
        profile.api_base.rstrip("/") + "/embeddings",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {profile.api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    started_at = perf_counter()
    try:
        with urlopen(request, timeout=settings.model_http_timeout_seconds) as response:
            raw_body = response.read().decode("utf-8")
        latency_ms = max(0, int((perf_counter() - started_at) * 1000))
        data = json.loads(raw_body)
        rows = data.get("data")
        if not isinstance(rows, list) or not rows:
            raise ValueError("missing embedding data")
        embedding = rows[0].get("embedding") if isinstance(rows[0], dict) else None
        if not isinstance(embedding, list) or not embedding:
            raise ValueError("missing embedding vector")
        vector = [float(value) for value in embedding]
        usage = data.get("usage") if isinstance(data.get("usage"), dict) else {}
        usage_tokens = usage.get("prompt_tokens") or usage.get("total_tokens")
        if isinstance(usage_tokens, int) and usage_tokens > 0:
            estimated_input_tokens = usage_tokens
        return EmbeddingResult(
            profile=profile,
            vector=vector,
            terms=terms,
            status="indexed",
            input_character_count=input_character_count,
            estimated_input_tokens=estimated_input_tokens,
            latency_ms=latency_ms,
            pricing_input_per_1k_tokens=pricing,
            estimated_cost=_embedding_cost(estimated_input_tokens=estimated_input_tokens, settings=settings),
            cost_currency=cost_currency,
            provider_call_performed=True,
            response_metadata={"usage": usage, "data_count": len(rows)},
        )
    except HTTPError as exc:
        return EmbeddingResult(
            profile=profile,
            vector=[],
            terms=terms,
            status="failed",
            error_message=f"HTTP {exc.code}",
            input_character_count=input_character_count,
            estimated_input_tokens=estimated_input_tokens,
            latency_ms=max(0, int((perf_counter() - started_at) * 1000)),
            pricing_input_per_1k_tokens=pricing,
            estimated_cost=_embedding_cost(estimated_input_tokens=estimated_input_tokens, settings=settings),
            cost_currency=cost_currency,
            provider_call_performed=True,
            response_metadata={"usage": {"estimated_input_tokens": estimated_input_tokens}},
        )
    except (URLError, TimeoutError, ValueError, json.JSONDecodeError) as exc:
        return EmbeddingResult(
            profile=profile,
            vector=[],
            terms=terms,
            status="failed",
            error_message=str(exc)[:500],
            input_character_count=input_character_count,
            estimated_input_tokens=estimated_input_tokens,
            latency_ms=max(0, int((perf_counter() - started_at) * 1000)),
            pricing_input_per_1k_tokens=pricing,
            estimated_cost=_embedding_cost(estimated_input_tokens=estimated_input_tokens, settings=settings),
            cost_currency=cost_currency,
            provider_call_performed=True,
            response_metadata={"usage": {"estimated_input_tokens": estimated_input_tokens}},
        )


def _require_embedding_available(result: EmbeddingResult) -> None:
    if result.status != "indexed" or not result.vector:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"knowledge embedding provider unavailable: {result.error_message or result.status}",
        )


def _rerank_score(query: str, meaningful_query_terms: set[str], matched_terms: set[str], content: str) -> float:
    if not meaningful_query_terms:
        return 0.0
    coverage = len(matched_terms) / max(len(meaningful_query_terms), 1)
    phrase_bonus = 0.18 if query.strip() and query.strip() in content else 0.0
    return round(min(1.0, (coverage * 0.82) + phrase_bonus), 4)


def _chunk_citation(*, document: KnowledgeDocument, chunk: KnowledgeDocumentChunk) -> dict:
    return {
        "document_id": document.id,
        "document_title": document.title,
        "chunk_id": chunk.id,
        "chunk_index": chunk.chunk_index,
        "section_title": chunk.section_title,
        "source_uri": chunk.source_uri,
        "char_start": chunk.char_start,
        "char_end": chunk.char_end,
    }


def _chunk_read(document: KnowledgeDocument, chunk: KnowledgeDocumentChunk) -> KnowledgeChunkRead:
    return KnowledgeChunkRead(
        id=chunk.id,
        tenant_id=chunk.tenant_id,
        document_id=chunk.document_id,
        chunk_index=chunk.chunk_index,
        section_title=chunk.section_title,
        page_number=chunk.page_number,
        content=chunk.content,
        content_hash=chunk.content_hash,
        source_uri=chunk.source_uri,
        char_start=chunk.char_start,
        char_end=chunk.char_end,
        token_count=chunk.token_count,
        embedding_signature=chunk.embedding_signature,
        embedding_provider=chunk.embedding_provider,
        embedding_model=chunk.embedding_model,
        embedding_dimension=chunk.embedding_dimension,
        vector_store=chunk.vector_store,
        vector_index_status=chunk.vector_index_status,
        status=chunk.status,
        citation=_chunk_citation(document=document, chunk=chunk),
        created_at=chunk.created_at,
    )


def _evaluation_cases_for_set(
    db: Session,
    evaluation_set_id: int,
    *,
    status_filter: str | None = None,
) -> list[KnowledgeEvaluationCase]:
    query = select(KnowledgeEvaluationCase).where(
        KnowledgeEvaluationCase.evaluation_set_id == evaluation_set_id
    )
    if status_filter:
        query = query.where(KnowledgeEvaluationCase.status == status_filter)
    query = query.order_by(KnowledgeEvaluationCase.priority.asc(), KnowledgeEvaluationCase.id.asc())
    return list(db.scalars(query).all())


def _evaluation_set_read(db: Session, evaluation_set: KnowledgeEvaluationSet) -> KnowledgeEvaluationSetRead:
    cases = _evaluation_cases_for_set(db, evaluation_set.id)
    return KnowledgeEvaluationSetRead(
        id=evaluation_set.id,
        tenant_id=evaluation_set.tenant_id,
        name=evaluation_set.name,
        description=evaluation_set.description,
        status=evaluation_set.status,
        evaluation_mode=evaluation_set.evaluation_mode,
        case_count=len(cases),
        cases=cases,
        created_by_id=evaluation_set.created_by_id,
        updated_by_id=evaluation_set.updated_by_id,
        created_at=evaluation_set.created_at,
        updated_at=evaluation_set.updated_at,
    )


def _run_cases_for_run(db: Session, evaluation_run_id: int) -> list[KnowledgeEvaluationRunCase]:
    return list(
        db.scalars(
            select(KnowledgeEvaluationRunCase)
            .where(KnowledgeEvaluationRunCase.evaluation_run_id == evaluation_run_id)
            .order_by(KnowledgeEvaluationRunCase.id.asc())
        ).all()
    )


def _evaluation_run_read(db: Session, run: KnowledgeEvaluationRun) -> KnowledgeEvaluationRunRead:
    return KnowledgeEvaluationRunRead(
        id=run.id,
        tenant_id=run.tenant_id,
        evaluation_set_id=run.evaluation_set_id,
        run_mode=run.run_mode,
        retrieval_mode=run.retrieval_mode,
        vector_engine=run.vector_engine,
        total_cases=run.total_cases,
        answered_cases=run.answered_cases,
        no_hit_cases=run.no_hit_cases,
        passed_cases=run.passed_cases,
        failed_cases=run.failed_cases,
        needs_review_cases=run.needs_review_cases,
        citation_covered_cases=run.citation_covered_cases,
        expected_term_covered_cases=run.expected_term_covered_cases,
        hit_rate=run.hit_rate,
        citation_coverage=run.citation_coverage,
        expected_term_coverage=run.expected_term_coverage,
        average_confidence=run.average_confidence,
        unsupported_answer_rate=run.unsupported_answer_rate,
        summary_payload=run.summary_payload,
        case_results=[
            KnowledgeEvaluationRunCaseRead.model_validate(case)
            for case in _run_cases_for_run(db, run.id)
        ],
        created_by_id=run.created_by_id,
        created_at=run.created_at,
    )


def _evaluation_run_summary_read(run: KnowledgeEvaluationRun) -> KnowledgeEvaluationRunSummaryRead:
    return KnowledgeEvaluationRunSummaryRead.model_validate(run)


def get_knowledge_evaluation_run(
    db: Session,
    evaluation_run_id: int,
    principal: CurrentPrincipal,
) -> KnowledgeEvaluationRunRead:
    _require_knowledge_manager(principal)
    run = db.get(KnowledgeEvaluationRun, evaluation_run_id)
    if run is None or run.tenant_id != principal.tenant.id:
        raise HTTPException(status_code=404, detail="knowledge evaluation run not found")
    return _evaluation_run_read(db, run)


def list_knowledge_evaluation_runs(
    db: Session,
    evaluation_set_id: int,
    *,
    page: int,
    page_size: int,
    principal: CurrentPrincipal,
) -> KnowledgeEvaluationRunList:
    _require_knowledge_manager(principal)
    evaluation_set = db.get(KnowledgeEvaluationSet, evaluation_set_id)
    if evaluation_set is None or evaluation_set.tenant_id != principal.tenant.id:
        raise HTTPException(status_code=404, detail="knowledge evaluation set not found")

    query = (
        select(KnowledgeEvaluationRun)
        .where(
            KnowledgeEvaluationRun.tenant_id == principal.tenant.id,
            KnowledgeEvaluationRun.evaluation_set_id == evaluation_set_id,
        )
        .order_by(KnowledgeEvaluationRun.created_at.desc(), KnowledgeEvaluationRun.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    count_query = select(func.count(KnowledgeEvaluationRun.id)).where(
        KnowledgeEvaluationRun.tenant_id == principal.tenant.id,
        KnowledgeEvaluationRun.evaluation_set_id == evaluation_set_id,
    )
    return KnowledgeEvaluationRunList(
        items=[_evaluation_run_summary_read(run) for run in db.scalars(query).all()],
        page=page,
        page_size=page_size,
        total=int(db.scalar(count_query) or 0),
    )


FACTUALITY_LABEL_SCHEMA_VERSION = "p3-06u-26h2n.human_factuality_label.v1"
FINAL_ANSWER_SAMPLE_SCHEMA_VERSION = "p3-06u-26h2p.final_answer_sample.v1"
FACTUALITY_BATCH_LABEL_SCHEMA_VERSION = "p3-06u-26h2p.batch_human_factuality_label.v1"
FINAL_ANSWER_LABEL_IO_SCHEMA_VERSION = "p3-06u-26h2r.final_answer_label_io.v1"
FINAL_ANSWER_LABEL_CSV_FIELDS = [
    "evaluation_run_case_id",
    "external_case_id",
    "source_channel",
    "source_category",
    "question_hash",
    "final_answer_text",
    "final_answer_source",
    "citation_uris",
    "final_answer_factuality_status",
    "citation_sufficient",
    "forbidden_commitment_passed",
    "handoff_correct",
    "reviewer_notes",
]
FINAL_ANSWER_LABEL_ALLOWED_STATUSES = {
    "correct",
    "partially_correct",
    "incorrect",
    "needs_human_review",
    "not_applicable",
}
FINAL_ANSWER_CITATION_SNAPSHOT_KINDS = {"final_answer_citation_uri", "final_answer_no_citation"}


def _factuality_score(status_value: str) -> float | None:
    if status_value == "correct":
        return 1.0
    if status_value == "partially_correct":
        return 0.5
    if status_value in {"incorrect", "needs_human_review"}:
        return 0.0
    return None


def _final_answer_sample_summary(cases: list[KnowledgeEvaluationRunCase]) -> dict[str, int | float | bool | str]:
    sampled_cases = 0
    for case in cases:
        payload = case.result_payload if isinstance(case.result_payload, dict) else {}
        answer_quality = payload.get("answer_quality") if isinstance(payload.get("answer_quality"), dict) else {}
        final_answer_sample = (
            payload.get("final_answer_sample")
            if isinstance(payload.get("final_answer_sample"), dict)
            else {}
        )
        if answer_quality.get("final_answer_sample_available") is True or bool(
            final_answer_sample.get("final_answer_hash")
        ):
            sampled_cases += 1

    return {
        "final_answer_sample_available": sampled_cases > 0,
        "final_answer_sampled_cases": sampled_cases,
        "final_answer_sample_coverage": _ratio(sampled_cases, len(cases)),
        "final_answer_sample_schema_version": FINAL_ANSWER_SAMPLE_SCHEMA_VERSION,
        "final_answer_sample_note": (
            f"已采集 {sampled_cases} / {len(cases)} 题最终客服答案样本；样本只用于本地人工标签，不调用模型、不外发。"
            if sampled_cases
            else "当前还没有最终客服答案样本，不能进行完整客服答案事实性评测。"
        ),
    }


def _factuality_label_summary(cases: list[KnowledgeEvaluationRunCase]) -> dict[str, int | float | bool | None | str]:
    labeled_cases = 0
    scored_cases = 0
    score_total = 0.0
    correct_cases = 0
    partially_correct_cases = 0
    incorrect_cases = 0
    needs_human_review_cases = 0
    not_applicable_cases = 0
    citation_sufficient_labeled_cases = 0
    citation_sufficient_cases = 0
    forbidden_commitment_labeled_cases = 0
    forbidden_commitment_passed_cases = 0
    handoff_labeled_cases = 0
    handoff_correct_cases = 0

    for case in cases:
        payload = case.result_payload if isinstance(case.result_payload, dict) else {}
        answer_quality = payload.get("answer_quality") if isinstance(payload.get("answer_quality"), dict) else {}
        if answer_quality.get("final_answer_factuality_measured") is not True:
            continue

        status_value = str(answer_quality.get("final_answer_factuality_status") or "").strip()
        if not status_value:
            continue
        labeled_cases += 1
        if status_value == "correct":
            correct_cases += 1
        elif status_value == "partially_correct":
            partially_correct_cases += 1
        elif status_value == "incorrect":
            incorrect_cases += 1
        elif status_value == "needs_human_review":
            needs_human_review_cases += 1
        elif status_value == "not_applicable":
            not_applicable_cases += 1

        score = _factuality_score(status_value)
        if score is not None:
            scored_cases += 1
            score_total += score

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

    factuality_rate = round(score_total / scored_cases, 4) if scored_cases else None
    return {
        "final_answer_factuality_measured": labeled_cases > 0,
        "final_answer_factuality_rate": factuality_rate,
        "final_answer_factuality_labeled_cases": labeled_cases,
        "final_answer_factuality_scored_cases": scored_cases,
        "final_answer_factuality_correct_cases": correct_cases,
        "final_answer_factuality_partially_correct_cases": partially_correct_cases,
        "final_answer_factuality_incorrect_cases": incorrect_cases,
        "final_answer_factuality_needs_human_review_cases": needs_human_review_cases,
        "final_answer_factuality_not_applicable_cases": not_applicable_cases,
        "final_answer_factuality_label_schema_version": FACTUALITY_LABEL_SCHEMA_VERSION,
        "final_answer_factuality_note": (
            f"已人工标注 {labeled_cases} / {len(cases)} 题；该准确率只代表已标注样本，不代表完整线上准确率。"
            if labeled_cases
            else "当前未做人工事实性标签，不能报告完整客服最终答案准确率。"
        ),
        "citation_sufficient_cases": citation_sufficient_cases,
        "citation_sufficiency_rate": _ratio(citation_sufficient_cases, citation_sufficient_labeled_cases),
        "forbidden_commitment_passed_cases": forbidden_commitment_passed_cases,
        "forbidden_commitment_violation_cases": max(
            0,
            forbidden_commitment_labeled_cases - forbidden_commitment_passed_cases,
        ),
        "forbidden_commitment_violation_rate": _ratio(
            max(0, forbidden_commitment_labeled_cases - forbidden_commitment_passed_cases),
            forbidden_commitment_labeled_cases,
        ),
        "handoff_correct_cases": handoff_correct_cases,
        "handoff_correctness": _ratio(handoff_correct_cases, handoff_labeled_cases),
        "unsupported_answer_rate_measured": labeled_cases > 0,
        "unsupported_answer_rate": (round(1 - factuality_rate, 4) if factuality_rate is not None else None),
    }


def _replace_final_answer_citation_snapshots(
    db: Session,
    run_case: KnowledgeEvaluationRunCase,
    *,
    run: KnowledgeEvaluationRun,
    citation_uris: list[str],
    final_answer_hash: str,
    captured_at: datetime,
) -> None:
    db.execute(
        delete(ReplyCitationSnapshot).where(
            ReplyCitationSnapshot.tenant_id == run_case.tenant_id,
            ReplyCitationSnapshot.evaluation_run_case_id == run_case.id,
            ReplyCitationSnapshot.source_kind.in_(FINAL_ANSWER_CITATION_SNAPSHOT_KINDS),
        )
    )
    provenance_id = f"eval_run:{run.id}:case:{run_case.id}:final_answer_sample"
    if not citation_uris:
        db.add(
            ReplyCitationSnapshot(
                tenant_id=run_case.tenant_id,
                provenance_id=provenance_id,
                evaluation_run_case_id=run_case.id,
                source_kind="final_answer_no_citation",
                source_version=FINAL_ANSWER_SAMPLE_SCHEMA_VERSION,
                content_hash=_content_hash(f"{provenance_id}:no_citation"),
                source_uri="",
                score=0,
                no_citation_reason="final_answer_sample_without_citation",
                citation_payload={
                    "evaluation_run_id": run.id,
                    "evaluation_set_id": run.evaluation_set_id,
                    "final_answer_hash": final_answer_hash,
                    "captured_at": captured_at.isoformat(),
                    "raw_text_logged": False,
                    "model_call_performed": False,
                    "external_platform_write_performed": False,
                },
                created_at=captured_at,
            )
        )
        return

    for index, source_uri in enumerate(citation_uris, start=1):
        document = db.scalar(
            select(KnowledgeDocument)
            .where(
                KnowledgeDocument.tenant_id == run_case.tenant_id,
                KnowledgeDocument.source_uri == source_uri,
            )
            .order_by(KnowledgeDocument.id.desc())
            .limit(1)
        )
        db.add(
            ReplyCitationSnapshot(
                tenant_id=run_case.tenant_id,
                provenance_id=provenance_id,
                evaluation_run_case_id=run_case.id,
                source_kind="final_answer_citation_uri",
                document_id=document.id if document else None,
                source_version=FINAL_ANSWER_SAMPLE_SCHEMA_VERSION,
                content_hash=_content_hash(source_uri),
                source_uri=source_uri,
                score=1,
                no_citation_reason="",
                citation_payload={
                    "evaluation_run_id": run.id,
                    "evaluation_set_id": run.evaluation_set_id,
                    "citation_index": index,
                    "final_answer_hash": final_answer_hash,
                    "document_title": document.title if document else "",
                    "captured_at": captured_at.isoformat(),
                    "raw_text_logged": False,
                    "model_call_performed": False,
                    "external_platform_write_performed": False,
                },
                created_at=captured_at,
            )
        )


def _apply_factuality_label_to_run_case(
    run_case: KnowledgeEvaluationRunCase,
    payload: KnowledgeEvaluationRunCaseFactualityLabelCreate,
    principal: CurrentPrincipal,
    now: datetime,
    *,
    schema_version: str = FACTUALITY_LABEL_SCHEMA_VERSION,
) -> str:
    result_payload = dict(run_case.result_payload or {})
    answer_quality = dict(result_payload.get("answer_quality") or {})
    note_hash = hashlib.sha256(payload.reviewer_notes.encode("utf-8")).hexdigest() if payload.reviewer_notes else ""

    answer_quality.update(
        {
            "scope": "human_labeled_customer_service_answer_quality",
            "final_answer_factuality_status": payload.final_answer_factuality_status,
            "final_answer_factuality_measured": True,
            "human_factuality_label_schema_version": schema_version,
            "human_factuality_labeled_at": now.isoformat(),
            "human_factuality_labeled_by_id": principal.user.id,
            "human_factuality_reviewer_note_hash": note_hash,
            "human_factuality_reviewer_note_length": len(payload.reviewer_notes),
            "note": "人工事实性标签只用于本地质量复盘，不调用模型、不外发、不保存备注明文到审计事件。",
        }
    )
    if payload.citation_sufficient is not None:
        answer_quality["citation_sufficient"] = payload.citation_sufficient
    if payload.forbidden_commitment_passed is not None:
        answer_quality["forbidden_commitment_passed"] = payload.forbidden_commitment_passed
    if payload.handoff_correct is not None:
        answer_quality["handoff_correct"] = payload.handoff_correct

    result_payload["answer_quality"] = answer_quality
    run_case.result_payload = result_payload
    return note_hash


def capture_knowledge_evaluation_run_case_final_answer_sample(
    db: Session,
    run_case_id: int,
    payload: KnowledgeEvaluationRunCaseFinalAnswerSampleCreate,
    principal: CurrentPrincipal,
) -> KnowledgeEvaluationRunCaseFinalAnswerSampleRead:
    _require_knowledge_manager(principal)
    run_case = db.get(KnowledgeEvaluationRunCase, run_case_id)
    if run_case is None or run_case.tenant_id != principal.tenant.id:
        raise HTTPException(status_code=404, detail="knowledge evaluation run case not found")

    run = db.get(KnowledgeEvaluationRun, run_case.evaluation_run_id)
    if run is None or run.tenant_id != principal.tenant.id:
        raise HTTPException(status_code=404, detail="knowledge evaluation run not found")

    now = utc_now()
    text = payload.final_answer_text.strip()
    if not text:
        raise HTTPException(status_code=422, detail="final answer text cannot be blank")
    citation_uris = _clean_string_list(payload.citation_uris)[:50]
    final_answer_hash = _content_hash(text)
    note_hash = hashlib.sha256(payload.reviewer_notes.encode("utf-8")).hexdigest() if payload.reviewer_notes else ""

    result_payload = dict(run_case.result_payload or {})
    answer_quality = dict(result_payload.get("answer_quality") or {})
    result_payload["final_answer_sample"] = {
        "schema_version": FINAL_ANSWER_SAMPLE_SCHEMA_VERSION,
        "final_answer_text": text,
        "final_answer_hash": final_answer_hash,
        "final_answer_length": len(text),
        "final_answer_source": payload.final_answer_source,
        "citation_uris": citation_uris,
        "citation_count": len(citation_uris),
        "answer_author": payload.answer_author.strip(),
        "captured_at": now.isoformat(),
        "captured_by_id": principal.user.id,
        "reviewer_note_hash": note_hash,
        "reviewer_note_length": len(payload.reviewer_notes),
        "model_call_performed": False,
        "external_platform_write_performed": False,
    }
    answer_quality.update(
        {
            "scope": "sampled_customer_service_final_answer_pending_human_label",
            "final_answer_sample_available": True,
            "final_answer_sample_schema_version": FINAL_ANSWER_SAMPLE_SCHEMA_VERSION,
            "final_answer_source": payload.final_answer_source,
            "final_answer_length": len(text),
            "model_call_performed": False,
            "external_platform_write_performed": False,
            "note": "已采集最终客服答案样本；后续需人工标注事实性后才纳入完整客服答案准确率。",
        }
    )
    if not answer_quality.get("final_answer_factuality_measured"):
        answer_quality["final_answer_factuality_status"] = "not_measured_final_answer_sampled"
        answer_quality["final_answer_factuality_measured"] = False

    result_payload["answer_quality"] = answer_quality
    run_case.result_payload = result_payload
    _replace_final_answer_citation_snapshots(
        db,
        run_case,
        run=run,
        citation_uris=citation_uris,
        final_answer_hash=final_answer_hash,
        captured_at=now,
    )

    run_cases = _run_cases_for_run(db, run.id)
    sample_summary = _final_answer_sample_summary(run_cases)
    factuality_summary = _factuality_label_summary(run_cases)
    summary_payload = dict(run.summary_payload or {})
    summary_payload.update(sample_summary)
    summary_payload.update(factuality_summary)
    summary_payload["answer_quality_scope"] = "final_answer_sampled_then_human_labeled_customer_service_quality"
    run.summary_payload = summary_payload
    run.unsupported_answer_rate = (
        factuality_summary["unsupported_answer_rate"]
        if isinstance(factuality_summary["unsupported_answer_rate"], float)
        else None
    )

    add_audit_event(
        db,
        tenant_id=run.tenant_id,
        actor_id=principal.user.id,
        action="knowledge_evaluation_run_case.final_answer_sampled",
        resource_type="knowledge_evaluation_run_case",
        resource_id=str(run_case.id),
        payload={
            "evaluation_run_id": run.id,
            "evaluation_set_id": run.evaluation_set_id,
            "final_answer_hash": final_answer_hash,
            "final_answer_length": len(text),
            "final_answer_source": payload.final_answer_source,
            "citation_count": len(citation_uris),
            "final_answer_sampled_cases": sample_summary["final_answer_sampled_cases"],
            "final_answer_sample_coverage": sample_summary["final_answer_sample_coverage"],
            "reviewer_note_hash": note_hash,
            "reviewer_note_length": len(payload.reviewer_notes),
            "raw_text_included": False,
            "model_call_performed": False,
            "external_platform_write_performed": False,
        },
    )
    db.commit()
    db.refresh(run)
    db.refresh(run_case)
    updated_run = _evaluation_run_read(db, run)
    return KnowledgeEvaluationRunCaseFinalAnswerSampleRead(
        tenant_id=run.tenant_id,
        evaluation_run_id=run.id,
        evaluation_run_case_id=run_case.id,
        final_answer_sampled_cases=int(sample_summary["final_answer_sampled_cases"]),
        final_answer_sample_coverage=float(sample_summary["final_answer_sample_coverage"]),
        total_cases=run.total_cases,
        updated_run=updated_run,
        audit_raw_text_included=False,
        model_call_performed=False,
        external_platform_write_performed=False,
    )


def label_knowledge_evaluation_run_case_factuality(
    db: Session,
    run_case_id: int,
    payload: KnowledgeEvaluationRunCaseFactualityLabelCreate,
    principal: CurrentPrincipal,
) -> KnowledgeEvaluationRunCaseFactualityLabelRead:
    _require_knowledge_manager(principal)
    run_case = db.get(KnowledgeEvaluationRunCase, run_case_id)
    if run_case is None or run_case.tenant_id != principal.tenant.id:
        raise HTTPException(status_code=404, detail="knowledge evaluation run case not found")

    run = db.get(KnowledgeEvaluationRun, run_case.evaluation_run_id)
    if run is None or run.tenant_id != principal.tenant.id:
        raise HTTPException(status_code=404, detail="knowledge evaluation run not found")

    now = utc_now()
    note_hash = _apply_factuality_label_to_run_case(run_case, payload, principal, now)

    run_cases = _run_cases_for_run(db, run.id)
    summary = _factuality_label_summary(run_cases)
    sample_summary = _final_answer_sample_summary(run_cases)
    summary_payload = dict(run.summary_payload or {})
    summary_payload.update(sample_summary)
    summary_payload.update(summary)
    run.summary_payload = summary_payload
    run.unsupported_answer_rate = summary["unsupported_answer_rate"] if isinstance(summary["unsupported_answer_rate"], float) else None

    add_audit_event(
        db,
        tenant_id=run.tenant_id,
        actor_id=principal.user.id,
        action="knowledge_evaluation_run_case.factuality_labeled",
        resource_type="knowledge_evaluation_run_case",
        resource_id=str(run_case.id),
        payload={
            "evaluation_run_id": run.id,
            "evaluation_set_id": run.evaluation_set_id,
            "final_answer_factuality_status": payload.final_answer_factuality_status,
            "final_answer_factuality_labeled_cases": summary["final_answer_factuality_labeled_cases"],
            "final_answer_factuality_rate": summary["final_answer_factuality_rate"],
            "reviewer_note_hash": note_hash,
            "reviewer_note_length": len(payload.reviewer_notes),
            "raw_text_included": False,
            "model_call_performed": False,
            "external_platform_write_performed": False,
        },
    )
    db.commit()
    db.refresh(run)
    db.refresh(run_case)
    updated_run = _evaluation_run_read(db, run)
    return KnowledgeEvaluationRunCaseFactualityLabelRead(
        tenant_id=run.tenant_id,
        evaluation_run_id=run.id,
        evaluation_run_case_id=run_case.id,
        final_answer_factuality_status=payload.final_answer_factuality_status,
        final_answer_factuality_measured=bool(summary["final_answer_factuality_measured"]),
        final_answer_factuality_rate=(
            float(summary["final_answer_factuality_rate"])
            if isinstance(summary["final_answer_factuality_rate"], (int, float))
            else None
        ),
        final_answer_factuality_labeled_cases=int(summary["final_answer_factuality_labeled_cases"]),
        total_cases=run.total_cases,
        updated_run=updated_run,
        raw_text_included=False,
        model_call_performed=False,
        external_platform_write_performed=False,
    )


def batch_label_knowledge_evaluation_run_case_factuality(
    db: Session,
    evaluation_run_id: int,
    payload: KnowledgeEvaluationRunCaseFactualityBatchLabelCreate,
    principal: CurrentPrincipal,
) -> KnowledgeEvaluationRunCaseFactualityBatchLabelRead:
    _require_knowledge_manager(principal)
    run = db.get(KnowledgeEvaluationRun, evaluation_run_id)
    if run is None or run.tenant_id != principal.tenant.id:
        raise HTTPException(status_code=404, detail="knowledge evaluation run not found")

    run_cases = _run_cases_for_run(db, run.id)
    cases_by_id = {case.id: case for case in run_cases}
    missing_ids = sorted({item.evaluation_run_case_id for item in payload.labels if item.evaluation_run_case_id not in cases_by_id})
    if missing_ids:
        raise HTTPException(
            status_code=422,
            detail=f"knowledge evaluation run cases do not belong to this run: {missing_ids}",
        )

    now = utc_now()
    status_counts: Counter[str] = Counter()
    note_hashes: list[str] = []
    for item in payload.labels:
        run_case = cases_by_id[item.evaluation_run_case_id]
        note_hash = _apply_factuality_label_to_run_case(
            run_case,
            item,
            principal,
            now,
            schema_version=FACTUALITY_BATCH_LABEL_SCHEMA_VERSION,
        )
        if note_hash:
            note_hashes.append(note_hash)
        status_counts[item.final_answer_factuality_status] += 1

    run_cases = _run_cases_for_run(db, run.id)
    summary = _factuality_label_summary(run_cases)
    sample_summary = _final_answer_sample_summary(run_cases)
    summary_payload = dict(run.summary_payload or {})
    summary_payload.update(sample_summary)
    summary_payload.update(summary)
    summary_payload["final_answer_factuality_batch_label_schema_version"] = FACTUALITY_BATCH_LABEL_SCHEMA_VERSION
    run.summary_payload = summary_payload
    run.unsupported_answer_rate = summary["unsupported_answer_rate"] if isinstance(summary["unsupported_answer_rate"], float) else None

    add_audit_event(
        db,
        tenant_id=run.tenant_id,
        actor_id=principal.user.id,
        action="knowledge_evaluation_run_case.factuality_batch_labeled",
        resource_type="knowledge_evaluation_run",
        resource_id=str(run.id),
        payload={
            "evaluation_run_id": run.id,
            "evaluation_set_id": run.evaluation_set_id,
            "labeled_cases": len(payload.labels),
            "status_counts": dict(status_counts),
            "final_answer_factuality_labeled_cases": summary["final_answer_factuality_labeled_cases"],
            "final_answer_factuality_rate": summary["final_answer_factuality_rate"],
            "final_answer_sampled_cases": sample_summary["final_answer_sampled_cases"],
            "reviewer_note_hashes": note_hashes[:50],
            "raw_text_included": False,
            "model_call_performed": False,
            "external_platform_write_performed": False,
        },
    )
    db.commit()
    db.refresh(run)
    updated_run = _evaluation_run_read(db, run)
    return KnowledgeEvaluationRunCaseFactualityBatchLabelRead(
        tenant_id=run.tenant_id,
        evaluation_run_id=run.id,
        labeled_cases=len(payload.labels),
        final_answer_factuality_rate=(
            float(summary["final_answer_factuality_rate"])
            if isinstance(summary["final_answer_factuality_rate"], (int, float))
            else None
        ),
        final_answer_factuality_labeled_cases=int(summary["final_answer_factuality_labeled_cases"]),
        total_cases=run.total_cases,
        updated_run=updated_run,
        audit_raw_text_included=False,
        model_call_performed=False,
        external_platform_write_performed=False,
    )


def _refresh_final_answer_label_summary(
    db: Session,
    run: KnowledgeEvaluationRun,
) -> tuple[dict[str, int | float | bool | str], dict[str, int | float | bool | None | str]]:
    run_cases = _run_cases_for_run(db, run.id)
    sample_summary = _final_answer_sample_summary(run_cases)
    factuality_summary = _factuality_label_summary(run_cases)
    summary_payload = dict(run.summary_payload or {})
    summary_payload.update(sample_summary)
    summary_payload.update(factuality_summary)
    summary_payload["answer_quality_scope"] = "final_answer_sampled_then_human_labeled_customer_service_quality"
    summary_payload["final_answer_label_io_schema_version"] = FINAL_ANSWER_LABEL_IO_SCHEMA_VERSION
    run.summary_payload = summary_payload
    run.unsupported_answer_rate = (
        factuality_summary["unsupported_answer_rate"]
        if isinstance(factuality_summary["unsupported_answer_rate"], float)
        else None
    )
    return sample_summary, factuality_summary


def _final_answer_label_bool_text(value: object) -> str:
    if value is True:
        return "true"
    if value is False:
        return "false"
    return ""


def _final_answer_label_parse_bool(value: object, *, row_number: int, field: str, errors: list[dict[str, Any]]) -> bool | None:
    text_value = str(value or "").strip().lower()
    if not text_value:
        return None
    if text_value in {"true", "1", "yes", "y", "是", "通过", "正确"}:
        return True
    if text_value in {"false", "0", "no", "n", "否", "不通过", "错误"}:
        return False
    errors.append({"row": row_number, "field": field, "message": "布尔字段只能填写 true/false、是/否 或 1/0"})
    return None


def _final_answer_label_case_payload(run_case: KnowledgeEvaluationRunCase) -> dict[str, Any]:
    payload = run_case.result_payload if isinstance(run_case.result_payload, dict) else {}
    return payload


def _final_answer_label_row(run_case: KnowledgeEvaluationRunCase, *, include_answer_text: bool) -> dict[str, Any]:
    payload = _final_answer_label_case_payload(run_case)
    answer_quality = payload.get("answer_quality") if isinstance(payload.get("answer_quality"), dict) else {}
    final_answer_sample = (
        payload.get("final_answer_sample") if isinstance(payload.get("final_answer_sample"), dict) else {}
    )
    status_value = str(answer_quality.get("final_answer_factuality_status") or "").strip()
    if status_value not in FINAL_ANSWER_LABEL_ALLOWED_STATUSES:
        status_value = ""
    return {
        "evaluation_run_case_id": run_case.id,
        "external_case_id": payload.get("external_case_id") or "",
        "source_channel": payload.get("source_channel") or "",
        "source_category": payload.get("source_category") or "",
        "question_hash": _report_hash_text(run_case.question or ""),
        "final_answer_text": final_answer_sample.get("final_answer_text") if include_answer_text else "",
        "final_answer_source": final_answer_sample.get("final_answer_source") or "imported_sample",
        "citation_uris": "|".join(_clean_string_list(final_answer_sample.get("citation_uris") or [])),
        "final_answer_factuality_status": status_value,
        "citation_sufficient": _final_answer_label_bool_text(answer_quality.get("citation_sufficient")),
        "forbidden_commitment_passed": _final_answer_label_bool_text(
            answer_quality.get("forbidden_commitment_passed")
        ),
        "handoff_correct": _final_answer_label_bool_text(answer_quality.get("handoff_correct")),
        "reviewer_notes": "",
    }


def export_knowledge_evaluation_run_final_answer_labels(
    db: Session,
    evaluation_run_id: int,
    *,
    export_format: str,
    include_answer_text: bool,
    principal: CurrentPrincipal,
) -> KnowledgeEvaluationRunFinalAnswerLabelExportRead:
    _require_knowledge_manager(principal)
    normalized_format = export_format.strip().lower()
    if normalized_format != "csv":
        raise HTTPException(status_code=422, detail="final answer label export only supports csv in this slice")
    run = db.get(KnowledgeEvaluationRun, evaluation_run_id)
    if run is None or run.tenant_id != principal.tenant.id:
        raise HTTPException(status_code=404, detail="knowledge evaluation run not found")

    run_cases = _run_cases_for_run(db, run.id)
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=FINAL_ANSWER_LABEL_CSV_FIELDS)
    writer.writeheader()
    for run_case in run_cases:
        writer.writerow(_final_answer_label_row(run_case, include_answer_text=include_answer_text))
    body = output.getvalue()
    sample_summary = _final_answer_sample_summary(run_cases)
    factuality_summary = _factuality_label_summary(run_cases)
    summary = {
        "final_answer_sampled_cases": sample_summary["final_answer_sampled_cases"],
        "final_answer_sample_coverage": sample_summary["final_answer_sample_coverage"],
        "final_answer_factuality_labeled_cases": factuality_summary["final_answer_factuality_labeled_cases"],
        "final_answer_factuality_rate": factuality_summary["final_answer_factuality_rate"],
        "question_raw_text_included": False,
        "final_answer_text_included": include_answer_text,
        "raw_text_included": include_answer_text,
    }

    add_audit_event(
        db,
        tenant_id=run.tenant_id,
        actor_id=principal.user.id,
        action="knowledge_evaluation_run.final_answer_labels_exported",
        resource_type="knowledge_evaluation_run",
        resource_id=str(run.id),
        payload={
            "evaluation_run_id": run.id,
            "evaluation_set_id": run.evaluation_set_id,
            "export_format": normalized_format,
            "row_count": len(run_cases),
            "question_raw_text_included": False,
            "final_answer_text_included": include_answer_text,
            "raw_text_included": False,
            "model_call_performed": False,
            "external_platform_write_performed": False,
        },
    )
    db.commit()
    return KnowledgeEvaluationRunFinalAnswerLabelExportRead(
        tenant_id=run.tenant_id,
        evaluation_run_id=run.id,
        evaluation_set_id=run.evaluation_set_id,
        schema_version=FINAL_ANSWER_LABEL_IO_SCHEMA_VERSION,
        export_format=normalized_format,
        filename=f"customer_service_eval_run_{run.id}_final_answer_labels.csv",
        content_type="text/csv; charset=utf-8",
        body=body,
        row_count=len(run_cases),
        raw_text_included=include_answer_text,
        question_raw_text_included=False,
        final_answer_text_included=include_answer_text,
        provider_call_performed=False,
        external_write_performed=False,
        summary=summary,
    )


def _final_answer_label_rows_from_csv(content: str) -> list[dict[str, str]]:
    reader = csv.DictReader(io.StringIO(content))
    if reader.fieldnames is None:
        raise HTTPException(status_code=422, detail="CSV 缺少表头")
    missing_fields = [field for field in FINAL_ANSWER_LABEL_CSV_FIELDS if field not in reader.fieldnames]
    if missing_fields:
        raise HTTPException(status_code=422, detail=f"CSV 缺少字段: {', '.join(missing_fields)}")
    return [dict(row) for row in reader]


def _final_answer_label_case_indexes(
    run_cases: list[KnowledgeEvaluationRunCase],
) -> tuple[dict[int, KnowledgeEvaluationRunCase], dict[str, KnowledgeEvaluationRunCase]]:
    cases_by_id = {case.id: case for case in run_cases}
    cases_by_external_id: dict[str, KnowledgeEvaluationRunCase] = {}
    for run_case in run_cases:
        payload = _final_answer_label_case_payload(run_case)
        external_case_id = str(payload.get("external_case_id") or "").strip()
        if external_case_id:
            cases_by_external_id[external_case_id] = run_case
    return cases_by_id, cases_by_external_id


def _resolve_final_answer_label_row_case(
    row: dict[str, str],
    *,
    row_number: int,
    cases_by_id: dict[int, KnowledgeEvaluationRunCase],
    cases_by_external_id: dict[str, KnowledgeEvaluationRunCase],
    errors: list[dict[str, Any]],
) -> KnowledgeEvaluationRunCase | None:
    raw_case_id = str(row.get("evaluation_run_case_id") or "").strip()
    if raw_case_id:
        try:
            case_id = int(raw_case_id)
        except ValueError:
            errors.append({"row": row_number, "field": "evaluation_run_case_id", "message": "运行用例 ID 必须是数字"})
            return None
        if case_id in cases_by_id:
            return cases_by_id[case_id]

    external_case_id = str(row.get("external_case_id") or "").strip()
    if external_case_id and external_case_id in cases_by_external_id:
        return cases_by_external_id[external_case_id]

    errors.append(
        {
            "row": row_number,
            "field": "evaluation_run_case_id",
            "message": "找不到当前运行中的用例；请保留 external_case_id 或使用本次运行的 case id",
        }
    )
    return None


def _split_final_answer_label_citations(value: object) -> list[str]:
    text_value = str(value or "").strip()
    if not text_value:
        return []
    parts = re.split(r"[|;\n]+", text_value)
    return _clean_string_list(parts)[:50]


def import_knowledge_evaluation_run_final_answer_labels(
    db: Session,
    evaluation_run_id: int,
    payload: KnowledgeEvaluationRunFinalAnswerLabelImportCreate,
    principal: CurrentPrincipal,
) -> KnowledgeEvaluationRunFinalAnswerLabelImportRead:
    _require_knowledge_manager(principal)
    if payload.import_format.strip().lower() != "csv":
        raise HTTPException(status_code=422, detail="final answer label import only supports csv in this slice")
    run = db.get(KnowledgeEvaluationRun, evaluation_run_id)
    if run is None or run.tenant_id != principal.tenant.id:
        raise HTTPException(status_code=404, detail="knowledge evaluation run not found")

    rows = _final_answer_label_rows_from_csv(payload.content)
    run_cases = _run_cases_for_run(db, run.id)
    cases_by_id, cases_by_external_id = _final_answer_label_case_indexes(run_cases)

    errors: list[dict[str, Any]] = []
    warnings: list[str] = []
    matched_rows = 0
    sample_rows = 0
    label_rows = 0
    skipped_rows = 0
    status_counts: Counter[str] = Counter()
    now = utc_now()
    rows_to_apply: list[tuple[KnowledgeEvaluationRunCase, dict[str, Any]]] = []

    for index, row in enumerate(rows, start=2):
        run_case = _resolve_final_answer_label_row_case(
            row,
            row_number=index,
            cases_by_id=cases_by_id,
            cases_by_external_id=cases_by_external_id,
            errors=errors,
        )
        if run_case is None:
            continue

        matched_rows += 1
        final_answer_text = str(row.get("final_answer_text") or "").strip()
        raw_status = str(row.get("final_answer_factuality_status") or "").strip()
        label_status = raw_status if raw_status in FINAL_ANSWER_LABEL_ALLOWED_STATUSES else ""
        if raw_status and not label_status:
            errors.append(
                {
                    "row": index,
                    "field": "final_answer_factuality_status",
                    "message": f"不支持的事实性标签: {raw_status}",
                }
            )
        bool_errors_before = len(errors)
        citation_sufficient = _final_answer_label_parse_bool(
            row.get("citation_sufficient"), row_number=index, field="citation_sufficient", errors=errors
        )
        forbidden_commitment_passed = _final_answer_label_parse_bool(
            row.get("forbidden_commitment_passed"),
            row_number=index,
            field="forbidden_commitment_passed",
            errors=errors,
        )
        handoff_correct = _final_answer_label_parse_bool(
            row.get("handoff_correct"), row_number=index, field="handoff_correct", errors=errors
        )
        if len(errors) > bool_errors_before or (raw_status and not label_status):
            continue

        if not final_answer_text and not label_status:
            skipped_rows += 1
            continue

        rows_to_apply.append(
            (
                run_case,
                {
                    "row_number": index,
                    "final_answer_text": final_answer_text,
                    "final_answer_source": str(row.get("final_answer_source") or "imported_sample").strip(),
                    "citation_uris": _split_final_answer_label_citations(row.get("citation_uris")),
                    "final_answer_factuality_status": label_status,
                    "citation_sufficient": citation_sufficient,
                    "forbidden_commitment_passed": forbidden_commitment_passed,
                    "handoff_correct": handoff_correct,
                    "reviewer_notes": str(row.get("reviewer_notes") or "").strip(),
                },
            )
        )
        if final_answer_text:
            sample_rows += 1
        if label_status:
            label_rows += 1
            status_counts[label_status] += 1

    if not payload.dry_run and not errors:
        for run_case, item in rows_to_apply:
            result_payload = dict(run_case.result_payload or {})
            answer_quality = dict(result_payload.get("answer_quality") or {})
            if item["final_answer_text"]:
                final_answer_source = item["final_answer_source"] or "imported_sample"
                if final_answer_source not in {"manual_capture", "system_capture", "dry_run_fixture", "imported_sample"}:
                    final_answer_source = "imported_sample"
                    warnings.append(f"第 {item['row_number']} 行 final_answer_source 已归一为 imported_sample")
                note_hash = (
                    hashlib.sha256(item["reviewer_notes"].encode("utf-8")).hexdigest()
                    if item["reviewer_notes"]
                    else ""
                )
                result_payload["final_answer_sample"] = {
                    "schema_version": FINAL_ANSWER_SAMPLE_SCHEMA_VERSION,
                    "final_answer_text": item["final_answer_text"],
                    "final_answer_hash": _content_hash(item["final_answer_text"]),
                    "final_answer_length": len(item["final_answer_text"]),
                    "final_answer_source": final_answer_source,
                    "citation_uris": item["citation_uris"],
                    "citation_count": len(item["citation_uris"]),
                    "answer_author": "离线标注导入",
                    "captured_at": now.isoformat(),
                    "captured_by_id": principal.user.id,
                    "reviewer_note_hash": note_hash,
                    "reviewer_note_length": len(item["reviewer_notes"]),
                    "model_call_performed": False,
                    "external_platform_write_performed": False,
                }
                answer_quality.update(
                    {
                        "scope": "imported_customer_service_final_answer_pending_or_labeled",
                        "final_answer_sample_available": True,
                        "final_answer_sample_schema_version": FINAL_ANSWER_SAMPLE_SCHEMA_VERSION,
                        "final_answer_source": final_answer_source,
                        "final_answer_length": len(item["final_answer_text"]),
                        "model_call_performed": False,
                        "external_platform_write_performed": False,
                        "note": "最终客服答案样本来自离线表格导入；未调用模型、未外发。",
                    }
                )
                if not answer_quality.get("final_answer_factuality_measured"):
                    answer_quality["final_answer_factuality_status"] = "not_measured_final_answer_sampled"
                    answer_quality["final_answer_factuality_measured"] = False
                result_payload["answer_quality"] = answer_quality
                run_case.result_payload = result_payload

            if item["final_answer_factuality_status"]:
                label_payload = KnowledgeEvaluationRunCaseFactualityLabelCreate(
                    final_answer_factuality_status=item["final_answer_factuality_status"],
                    citation_sufficient=item["citation_sufficient"],
                    forbidden_commitment_passed=item["forbidden_commitment_passed"],
                    handoff_correct=item["handoff_correct"],
                    reviewer_notes=item["reviewer_notes"],
                )
                _apply_factuality_label_to_run_case(
                    run_case,
                    label_payload,
                    principal,
                    now,
                    schema_version=FINAL_ANSWER_LABEL_IO_SCHEMA_VERSION,
                )

        _refresh_final_answer_label_summary(db, run)
        add_audit_event(
            db,
            tenant_id=run.tenant_id,
            actor_id=principal.user.id,
            action="knowledge_evaluation_run.final_answer_labels_imported",
            resource_type="knowledge_evaluation_run",
            resource_id=str(run.id),
            payload={
                "evaluation_run_id": run.id,
                "evaluation_set_id": run.evaluation_set_id,
                "total_rows": len(rows),
                "matched_rows": matched_rows,
                "sample_rows": sample_rows,
                "label_rows": label_rows,
                "status_counts": dict(status_counts),
                "raw_text_included": False,
                "final_answer_text_imported": sample_rows > 0,
                "model_call_performed": False,
                "external_platform_write_performed": False,
            },
        )
        db.commit()
        db.refresh(run)

    updated_run = _evaluation_run_read(db, run) if not payload.dry_run and not errors else None
    return KnowledgeEvaluationRunFinalAnswerLabelImportRead(
        tenant_id=run.tenant_id,
        evaluation_run_id=run.id,
        evaluation_set_id=run.evaluation_set_id,
        schema_version=FINAL_ANSWER_LABEL_IO_SCHEMA_VERSION,
        import_format="csv",
        dry_run=payload.dry_run,
        imported=(not payload.dry_run and not errors),
        total_rows=len(rows),
        matched_rows=matched_rows,
        sample_rows=sample_rows,
        label_rows=label_rows,
        skipped_rows=skipped_rows,
        validation_errors=errors,
        warnings=warnings,
        status_counts=dict(status_counts),
        updated_run=updated_run,
        audit_raw_text_included=False,
        provider_call_performed=False,
        external_write_performed=False,
    )


MONTHLY_QUALITY_REVIEW_SCHEMA_VERSION = "p3-06u-26h2m.monthly_quality_review.v1"
MONTHLY_OPS_REPORT_SCHEMA_VERSION = "p3-06u-26h2w-ops2.monthly_ops_report.v1"
CUSTOMER_QUALITY_REPORT_SCHEMA_VERSION = "p3-06u-26h2q.customer_quality_report.v1"
CUSTOMER_QUALITY_REPORT_EXPORT_SCHEMA_VERSION = "p3-06u-26h2s.customer_quality_report_export.v1"
CUSTOMER_QUALITY_REPORT_SIGNOFF_SCHEMA_VERSION = "p3-06u-26h2t.customer_quality_report_signoff.v1"
CUSTOMER_QUALITY_REPORT_SIGNOFF_LIST_SCHEMA_VERSION = "p3-06u-26h2u.customer_quality_report_signoff_list.v1"
CUSTOMER_QUALITY_REPORT_ARCHIVE_LIST_SCHEMA_VERSION = "p3-06u-26h2w4.customer_quality_report_archive_list.v1"
CUSTOMER_QUALITY_REPORT_GAP_REHEARSAL_SCHEMA_VERSION = "p3-06u-26h2w11k.gap_rehearsal_evidence.v1"
GAP_REHEARSAL_FORMAL_SIGNOFF_BOUNDARY = "ready_for_formal_accuracy_signoff=false"
STANDARD_OPS_ROOT = Path(__file__).resolve().parents[3]
H2W11J_GAP_REHEARSAL_SUMMARY_PATH = STANDARD_OPS_ROOT / "output/p3_06u_26h2w11j_gap_final_answer_rehearsal/summary.json"


def _month_window(year: int | None, month: int | None) -> tuple[str, datetime, datetime]:
    now = utc_now()
    review_year = year or now.year
    review_month = month or now.month
    if review_month < 1 or review_month > 12:
        raise HTTPException(status_code=422, detail="month must be between 1 and 12")
    if review_year < 2024 or review_year > 2100:
        raise HTTPException(status_code=422, detail="year must be between 2024 and 2100")

    start = datetime(review_year, review_month, 1, tzinfo=timezone.utc)
    if review_month == 12:
        end = datetime(review_year + 1, 1, 1, tzinfo=timezone.utc)
    else:
        end = datetime(review_year, review_month + 1, 1, tzinfo=timezone.utc)
    return f"{review_year:04d}-{review_month:02d}", start, end


def _between_month(column, period_start: datetime, period_end: datetime):
    return column >= period_start, column < period_end


def _count_rows(db: Session, model, *conditions) -> int:
    return int(db.scalar(select(func.count(model.id)).where(*conditions)) or 0)


def _count_by_string_field(db: Session, model, field, *conditions) -> dict[str, int]:
    rows = db.execute(
        select(field, func.count(model.id))
        .where(*conditions)
        .group_by(field)
    ).all()
    return {str(key or "unknown"): int(count or 0) for key, count in rows}


def _format_rate_value(value: float | None) -> str:
    if value is None:
        return "未评"
    return f"{round(float(value) * 100)}%"


def _metric_status(value: float | None, warn: float, danger: float, *, higher_is_better: bool = True) -> str:
    if value is None:
        return "missing"
    if higher_is_better:
        if value < danger:
            return "critical"
        if value < warn:
            return "warning"
        return "ok"
    if value > danger:
        return "critical"
    if value > warn:
        return "warning"
    return "ok"


def _metric(
    key: str,
    label: str,
    value: str,
    numeric_value: float | None,
    status: str,
    detail: str,
) -> MonthlyQualityReviewMetricRead:
    return MonthlyQualityReviewMetricRead(
        key=key,
        label=label,
        value=value,
        numeric_value=numeric_value,
        status=status,
        detail=detail,
    )


def _cause(
    key: str,
    label: str,
    count: int,
    severity: str,
    detail: str,
    next_action: str,
    target_href: str,
) -> MonthlyQualityReviewCauseRead:
    return MonthlyQualityReviewCauseRead(
        key=key,
        label=label,
        count=count,
        severity=severity,
        detail=detail,
        next_action=next_action,
        target_href=target_href,
    )


def _action(
    key: str,
    label: str,
    owner: str,
    priority: str,
    evidence: str,
    next_step: str,
    target_href: str,
    status: str,
) -> MonthlyQualityReviewActionRead:
    return MonthlyQualityReviewActionRead(
        key=key,
        label=label,
        owner=owner,
        priority=priority,
        evidence=evidence,
        next_step=next_step,
        target_href=target_href,
        status=status,
    )


def _latest_monthly_evaluation_run(
    db: Session,
    tenant_id: int,
    period_start: datetime,
    period_end: datetime,
) -> KnowledgeEvaluationRun | None:
    return db.scalar(
        select(KnowledgeEvaluationRun)
        .where(
            KnowledgeEvaluationRun.tenant_id == tenant_id,
            *_between_month(KnowledgeEvaluationRun.created_at, period_start, period_end),
        )
        .order_by(KnowledgeEvaluationRun.created_at.desc(), KnowledgeEvaluationRun.id.desc())
    )


def _previous_evaluation_run(db: Session, latest_run: KnowledgeEvaluationRun | None) -> KnowledgeEvaluationRun | None:
    if latest_run is None:
        return None
    return db.scalar(
        select(KnowledgeEvaluationRun)
        .where(
            KnowledgeEvaluationRun.tenant_id == latest_run.tenant_id,
            KnowledgeEvaluationRun.evaluation_set_id == latest_run.evaluation_set_id,
            KnowledgeEvaluationRun.id != latest_run.id,
            KnowledgeEvaluationRun.created_at < latest_run.created_at,
        )
        .order_by(KnowledgeEvaluationRun.created_at.desc(), KnowledgeEvaluationRun.id.desc())
    )


def _monthly_quality_review_case_counts(db: Session, latest_run: KnowledgeEvaluationRun | None) -> dict[str, int]:
    if latest_run is None:
        return {
            "total_cases": 0,
            "failed_or_review_cases": 0,
            "knowledge_gap_cases": 0,
            "evidence_missing_cases": 0,
            "forbidden_commitment_cases": 0,
            "handoff_incorrect_cases": 0,
        }

    cases = db.scalars(
        select(KnowledgeEvaluationRunCase).where(
            KnowledgeEvaluationRunCase.tenant_id == latest_run.tenant_id,
            KnowledgeEvaluationRunCase.evaluation_run_id == latest_run.id,
        )
    ).all()
    failed_or_review = 0
    knowledge_gap = 0
    evidence_missing = 0
    forbidden_commitment = 0
    handoff_incorrect = 0
    for case in cases:
        payload = case.result_payload if isinstance(case.result_payload, dict) else {}
        answer_quality = payload.get("answer_quality") if isinstance(payload.get("answer_quality"), dict) else {}
        if case.status != "passed" or case.failure_reason:
            failed_or_review += 1
        if case.status == "no_hit" or case.failure_reason in {
            "no_retrieval_hit",
            "no_knowledge_hit",
            "expected_terms_missing",
            "expected_evidence_missing",
        } or payload.get("knowledge_gap") is True:
            knowledge_gap += 1
        if case.failure_reason in {"expected_terms_missing", "expected_evidence_missing"}:
            evidence_missing += 1
        if answer_quality.get("forbidden_commitment_passed") is False:
            forbidden_commitment += 1
        if answer_quality.get("handoff_correct") is False or payload.get("human_review_prediction_correct") is False:
            handoff_incorrect += 1

    return {
        "total_cases": len(cases),
        "failed_or_review_cases": failed_or_review,
        "knowledge_gap_cases": knowledge_gap,
        "evidence_missing_cases": evidence_missing,
        "forbidden_commitment_cases": forbidden_commitment,
        "handoff_incorrect_cases": handoff_incorrect,
    }


def get_monthly_quality_review(
    db: Session,
    tenant_id: int,
    *,
    year: int | None,
    month: int | None,
    principal: CurrentPrincipal,
) -> MonthlyQualityReviewRead:
    _require_same_tenant(db, tenant_id, principal)
    period, period_start, period_end = _month_window(year, month)
    latest_run = _latest_monthly_evaluation_run(db, tenant_id, period_start, period_end)
    previous_run = _previous_evaluation_run(db, latest_run)
    case_counts = _monthly_quality_review_case_counts(db, latest_run)
    summary_payload = latest_run.summary_payload if latest_run and isinstance(latest_run.summary_payload, dict) else {}

    new_gap_count = _count_rows(
        db,
        KnowledgeGapItem,
        KnowledgeGapItem.tenant_id == tenant_id,
        *_between_month(KnowledgeGapItem.created_at, period_start, period_end),
    )
    open_gap_count = _count_rows(
        db,
        KnowledgeGapItem,
        KnowledgeGapItem.tenant_id == tenant_id,
        KnowledgeGapItem.status.in_(["open", "triaged", "in_progress"]),
    )
    resolved_gap_count = _count_rows(
        db,
        KnowledgeGapItem,
        KnowledgeGapItem.tenant_id == tenant_id,
        KnowledgeGapItem.status == "resolved",
        KnowledgeGapItem.resolved_at.is_not(None),
        *_between_month(KnowledgeGapItem.resolved_at, period_start, period_end),
    )
    high_gap_count = _count_rows(
        db,
        KnowledgeGapItem,
        KnowledgeGapItem.tenant_id == tenant_id,
        KnowledgeGapItem.status.in_(["open", "triaged", "in_progress"]),
        KnowledgeGapItem.severity.in_(["high", "critical"]),
    )
    human_review_count = _count_rows(
        db,
        HumanReviewTask,
        HumanReviewTask.tenant_id == tenant_id,
        *_between_month(HumanReviewTask.created_at, period_start, period_end),
    )
    open_human_reviews = _count_rows(
        db,
        HumanReviewTask,
        HumanReviewTask.tenant_id == tenant_id,
        HumanReviewTask.status.in_(["open", "assigned"]),
    )
    high_risk_reviews = _count_rows(
        db,
        HumanReviewTask,
        HumanReviewTask.tenant_id == tenant_id,
        *_between_month(HumanReviewTask.created_at, period_start, period_end),
        HumanReviewTask.risk_level.in_(["high", "critical"]),
    )
    low_confidence_reviews = _count_rows(
        db,
        HumanReviewTask,
        HumanReviewTask.tenant_id == tenant_id,
        *_between_month(HumanReviewTask.created_at, period_start, period_end),
        HumanReviewTask.reason.in_(["low_confidence", "no_knowledge", "weak_evidence"]),
    )
    reply_decision_count = _count_rows(
        db,
        ReplyDecision,
        ReplyDecision.tenant_id == tenant_id,
        *_between_month(ReplyDecision.created_at, period_start, period_end),
    )
    auto_ready_count = _count_rows(
        db,
        ReplyDecision,
        ReplyDecision.tenant_id == tenant_id,
        *_between_month(ReplyDecision.created_at, period_start, period_end),
        ReplyDecision.state == "auto_reply_ready",
    )
    manual_or_blocked_count = _count_rows(
        db,
        ReplyDecision,
        ReplyDecision.tenant_id == tenant_id,
        *_between_month(ReplyDecision.created_at, period_start, period_end),
        ReplyDecision.state.in_(["manual_gate_required", "knowledge_gap", "blocked_by_policy"]),
    )

    total_cases = latest_run.total_cases if latest_run else 0
    human_factuality_measured = bool(summary_payload.get("final_answer_factuality_measured")) if latest_run else False
    human_factuality_rate = summary_payload.get("final_answer_factuality_rate") if human_factuality_measured else None
    auto_reply_rate = auto_ready_count / reply_decision_count if reply_decision_count else None
    gap_closure_rate = resolved_gap_count / (resolved_gap_count + open_gap_count) if (resolved_gap_count + open_gap_count) else None
    hit_delta = (latest_run.hit_rate - previous_run.hit_rate) if latest_run and previous_run else None

    metrics = [
        _metric(
            "question_bank_size",
            "本月题库",
            f"{total_cases} 题",
            float(total_cases),
            "ok" if total_cases >= 50 else "warning" if total_cases > 0 else "missing",
            "小微企业试点建议至少 50-100 条脱敏真实客户问题，低于 50 条不能作为完整准确率依据。",
        ),
        _metric(
            "retrieval_hit_rate",
            "检索命中",
            _format_rate_value(latest_run.hit_rate if latest_run else None),
            latest_run.hit_rate if latest_run else None,
            _metric_status(latest_run.hit_rate if latest_run else None, 0.8, 0.65),
            "只代表知识检索命中，不等同最终客服答案准确率。",
        ),
        _metric(
            "citation_coverage",
            "引用覆盖",
            _format_rate_value(latest_run.citation_coverage if latest_run else None),
            latest_run.citation_coverage if latest_run else None,
            _metric_status(latest_run.citation_coverage if latest_run else None, 0.75, 0.6),
            "回答依据是否能回溯到知识片段或知识卡。",
        ),
        _metric(
            "human_factuality",
            "人工事实性",
            _format_rate_value(human_factuality_rate if isinstance(human_factuality_rate, (int, float)) else None),
            float(human_factuality_rate) if isinstance(human_factuality_rate, (int, float)) else None,
            "ok" if human_factuality_measured else "missing",
            "没有人工事实性标签时，不报告完整客服准确率。",
        ),
        _metric(
            "knowledge_gap_closure",
            "缺口闭环",
            _format_rate_value(gap_closure_rate),
            gap_closure_rate,
            _metric_status(gap_closure_rate, 0.65, 0.4),
            "本月已解决缺口相对当前开放缺口的处理情况。",
        ),
        _metric(
            "auto_reply_rate",
            "自动回复准备率",
            _format_rate_value(auto_reply_rate),
            auto_reply_rate,
            _metric_status(auto_reply_rate, 0.55, 0.35),
            "只统计系统判定可自动回复的决策比例，不代表已经真实外发。",
        ),
    ]

    root_causes = [
        _cause(
            "question_bank_insufficient",
            "真实题库不足",
            1 if total_cases < 50 else 0,
            "warning" if 0 < total_cases < 50 else "critical" if total_cases == 0 else "ok",
            "题库少于 50 条时，只能做方向性验证。",
            "导入 50-100 条真实脱敏问题，并按售前、售后、价格、交付、风险分组。",
            "#evals",
        ),
        _cause(
            "missing_human_factuality_labels",
            "人工事实性标签缺失",
            0 if human_factuality_measured else 1,
            "warning",
            "当前最终答案事实性未由人工标注确认。",
            "抽样标注最终答案是否事实正确、引用是否充分、是否越权承诺。",
            "#quality",
        ),
        _cause(
            "knowledge_gap_backlog",
            "知识缺口未闭环",
            open_gap_count + case_counts["knowledge_gap_cases"],
            "critical" if high_gap_count > 0 else "warning" if open_gap_count > 0 else "ok",
            "开放知识缺口和评测缺口会直接拉低自动回复覆盖。",
            "进入知识缺口，生成知识草稿、补引用来源并加入回归题。",
            "#gaps",
        ),
        _cause(
            "weak_evidence_or_low_confidence",
            "证据弱或置信不足",
            low_confidence_reviews + case_counts["evidence_missing_cases"],
            "warning" if low_confidence_reviews + case_counts["evidence_missing_cases"] else "ok",
            "低置信、弱引用和期望词缺失会导致频繁转人工。",
            "复核低置信样本，调知识片段、检索参数和标准问答。",
            "#quality",
        ),
        _cause(
            "handoff_or_policy_risk",
            "转人工和风险策略需复核",
            high_risk_reviews + case_counts["handoff_incorrect_cases"] + case_counts["forbidden_commitment_cases"],
            "critical" if high_risk_reviews + case_counts["forbidden_commitment_cases"] else "warning" if case_counts["handoff_incorrect_cases"] else "ok",
            "赔付、法务、投诉和敏感承诺仍要优先稳妥转人工。",
            "抽查转人工是否正确，补风险话术和禁用承诺规则。",
            "#reviews",
        ),
    ]
    root_causes.sort(key=lambda item: (item.severity != "critical", item.severity != "warning", -item.count))

    action_items = [
        _action(
            "import_real_question_bank",
            "补齐真实客户题库",
            "运营管理员",
            "P0" if total_cases == 0 else "P1" if total_cases < 50 else "P2",
            f"当前本月题库 {total_cases} 题",
            "导入 50-100 条脱敏真实客户问题，并保留来源分类和期望处理方式。",
            "#evals",
            "done" if total_cases >= 50 else "open",
        ),
        _action(
            "add_human_factuality_labels",
            "补人工事实性标签",
            "客服主管",
            "P0",
            "当前不报告完整客服准确率",
            "对本月样本标注事实正确、引用充分、禁用承诺、转人工正确性。",
            "#quality",
            "done" if human_factuality_measured else "open",
        ),
        _action(
            "close_knowledge_gaps",
            "关闭知识缺口",
            "知识负责人",
            "P1" if open_gap_count else "P2",
            f"开放缺口 {open_gap_count} 个，高风险缺口 {high_gap_count} 个",
            "把开放缺口补成知识卡/文档，并为每个缺口补回归题。",
            "#gaps",
            "open" if open_gap_count else "done",
        ),
        _action(
            "run_same_set_regression",
            "跑同题集回归",
            "知识负责人",
            "P1",
            "需要发布前后使用同一题集比较",
            "知识发布前后固定同一题集，观察命中、引用和转人工正确性变化。",
            "#evals",
            "open" if latest_run is None or previous_run is None else "in_progress",
        ),
        _action(
            "review_auto_reply_threshold",
            "复核自动回复阈值",
            "客服主管",
            "P2",
            f"本月自动回复准备率 {_format_rate_value(auto_reply_rate)}",
            "只在知识命中、引用充分、风险规则通过时自动回复；其余保持转人工。",
            "#quality",
            "open" if manual_or_blocked_count else "done",
        ),
    ]

    return MonthlyQualityReviewRead(
        tenant_id=tenant_id,
        schema_version=MONTHLY_QUALITY_REVIEW_SCHEMA_VERSION,
        period=period,
        period_start=period_start,
        period_end=period_end,
        generated_at=utc_now(),
        latest_evaluation_run_id=latest_run.id if latest_run else None,
        latest_evaluation_set_id=latest_run.evaluation_set_id if latest_run else None,
        previous_evaluation_run_id=previous_run.id if previous_run else None,
        metrics=metrics,
        root_causes=root_causes,
        action_items=action_items,
        knowledge_gap_summary={
            "new_this_month": new_gap_count,
            "open_backlog": open_gap_count,
            "resolved_this_month": resolved_gap_count,
            "high_or_critical_open": high_gap_count,
            **{f"status_{key}": value for key, value in _count_by_string_field(db, KnowledgeGapItem, KnowledgeGapItem.status, KnowledgeGapItem.tenant_id == tenant_id).items()},
        },
        human_review_summary={
            "created_this_month": human_review_count,
            "open_backlog": open_human_reviews,
            "high_or_critical_this_month": high_risk_reviews,
            "low_confidence_this_month": low_confidence_reviews,
            **{f"reason_{key}": value for key, value in _count_by_string_field(db, HumanReviewTask, HumanReviewTask.reason, HumanReviewTask.tenant_id == tenant_id, *_between_month(HumanReviewTask.created_at, period_start, period_end)).items()},
        },
        reply_decision_summary={
            "created_this_month": reply_decision_count,
            "auto_reply_ready": auto_ready_count,
            "manual_or_blocked": manual_or_blocked_count,
            **{f"state_{key}": value for key, value in _count_by_string_field(db, ReplyDecision, ReplyDecision.state, ReplyDecision.tenant_id == tenant_id, *_between_month(ReplyDecision.created_at, period_start, period_end)).items()},
        },
        trend_summary={
            "has_same_set_previous_run": previous_run is not None,
            "hit_rate_delta": hit_delta,
            "latest_hit_rate": latest_run.hit_rate if latest_run else None,
            "previous_hit_rate": previous_run.hit_rate if previous_run else None,
            "latest_needs_review_cases": latest_run.needs_review_cases if latest_run else 0,
            "case_failure_counts": case_counts,
        },
        data_boundaries=[
            "本复盘包为服务端只读聚合，不修改知识库、会话、评测集或渠道配置。",
            "当前完整客服准确率仍未成立；检索命中率、引用覆盖率和人工事实性标签必须分开看。",
            "渠道官方接入验收不纳入本片；真实外发、回执和失败重试继续保持关闭或另行验收。",
            "原始客户问题、聊天原文、草稿全文和敏感联系方式不会出现在本复盘包。",
        ],
        next_review_steps=[
            "先补 50-100 条真实脱敏客户题库。",
            "对本月样本补人工事实性标签。",
            "处理开放知识缺口，并为每个修复项加入回归题。",
            "用同一题集做发布前后对比，形成月度复盘结论。",
        ],
        raw_text_included=False,
        model_call_performed=False,
        external_call_performed=False,
        external_platform_write_performed=False,
    )


def _ops_metric(
    key: str,
    label: str,
    value: str,
    status: str,
    detail: str,
) -> MonthlyOpsReportMetricRead:
    return MonthlyOpsReportMetricRead(
        key=key,
        label=label,
        value=value,
        status=status,
        detail=detail,
    )


def _ops_section(
    key: str,
    title: str,
    status: str,
    summary: str,
    metrics: list[MonthlyOpsReportMetricRead],
    evidence: list[dict[str, Any]],
    next_steps: list[str],
) -> MonthlyOpsReportSectionRead:
    return MonthlyOpsReportSectionRead(
        key=key,
        title=title,
        status=status,
        summary=summary,
        metrics=metrics,
        evidence=evidence,
        next_steps=next_steps,
    )


def _ops_risk(
    key: str,
    label: str,
    severity: str,
    detail: str,
    recommended_action: str,
) -> MonthlyOpsReportRiskRead:
    return MonthlyOpsReportRiskRead(
        key=key,
        label=label,
        severity=severity,
        detail=detail,
        recommended_action=recommended_action,
    )


def _money_value(value: float | None, currency: str = "CNY") -> str:
    amount = float(value or 0.0)
    prefix = "¥" if currency == "CNY" else f"{currency} "
    return f"{prefix}{amount:.4f}"


def _monthly_model_cost_summary(
    db: Session,
    tenant_id: int,
    period_start: datetime,
    period_end: datetime,
) -> dict[str, Any]:
    row = db.execute(
        select(
            func.count(ModelCallRecord.id),
            func.coalesce(func.sum(ModelCallRecord.estimated_cost), 0.0),
            func.coalesce(func.sum(ModelCallRecord.total_units), 0),
            func.coalesce(func.avg(ModelCallRecord.latency_ms), 0.0),
        ).where(
            ModelCallRecord.tenant_id == tenant_id,
            *_between_month(ModelCallRecord.created_at, period_start, period_end),
        )
    ).one()
    status_counts = _count_by_string_field(
        db,
        ModelCallRecord,
        ModelCallRecord.status,
        ModelCallRecord.tenant_id == tenant_id,
        *_between_month(ModelCallRecord.created_at, period_start, period_end),
    )
    provider_counts = _count_by_string_field(
        db,
        ModelCallRecord,
        ModelCallRecord.provider,
        ModelCallRecord.tenant_id == tenant_id,
        *_between_month(ModelCallRecord.created_at, period_start, period_end),
    )
    currency = (
        db.scalar(
            select(ModelCallRecord.currency)
            .where(
                ModelCallRecord.tenant_id == tenant_id,
                *_between_month(ModelCallRecord.created_at, period_start, period_end),
            )
            .order_by(ModelCallRecord.created_at.desc(), ModelCallRecord.id.desc())
        )
        or "CNY"
    )
    return {
        "call_count": int(row[0] or 0),
        "estimated_cost": float(row[1] or 0.0),
        "total_units": int(row[2] or 0),
        "avg_latency_ms": int(float(row[3] or 0.0)),
        "currency": str(currency),
        "status_counts": status_counts,
        "provider_counts": provider_counts,
        "failed_count": sum(
            value
            for key, value in status_counts.items()
            if key not in {"success", "succeeded", "ok", "completed"}
        ),
    }


def _ops_status_from_score(score: int, *, blocked: bool) -> tuple[str, str, str]:
    if blocked:
        return "blocked_missing_upstream_evidence", "证据不足", "待补证据"
    if score >= 85:
        return "ready_for_customer_monthly_ops_report_rehearsal", "可进入月度复盘演练", "健康"
    if score >= 70:
        return "partial_ready_for_customer_monthly_ops_report_rehearsal", "可带风险复盘", "基本稳定"
    return "repair_required_before_customer_monthly_ops_report", "需先修复", "需关注"


def get_monthly_ops_report(
    db: Session,
    tenant_id: int,
    *,
    year: int | None,
    month: int | None,
    principal: CurrentPrincipal,
) -> MonthlyOpsReportRead:
    tenant = require_tenant(db, tenant_id)
    _require_same_tenant(db, tenant_id, principal)
    review = get_monthly_quality_review(db, tenant_id, year=year, month=month, principal=principal)
    model_cost = _monthly_model_cost_summary(db, tenant_id, review.period_start, review.period_end)
    maintenance = build_local_maintenance_readiness(db, tenant=tenant)

    question_bank_size = _metric_value(review, "question_bank_size") or 0
    retrieval_hit_rate = _metric_value(review, "retrieval_hit_rate")
    citation_coverage = _metric_value(review, "citation_coverage")
    human_factuality = _metric_value(review, "human_factuality")
    auto_reply_rate = _metric_value(review, "auto_reply_rate")
    knowledge_gap_closure = _metric_value(review, "knowledge_gap_closure")
    open_gaps = int(review.knowledge_gap_summary.get("open_backlog", 0) or 0)
    high_gaps = int(review.knowledge_gap_summary.get("high_or_critical_open", 0) or 0)
    human_reviews = int(review.human_review_summary.get("created_this_month", 0) or 0)
    manual_or_blocked = int(review.reply_decision_summary.get("manual_or_blocked", 0) or 0)
    maintenance_counts = maintenance.get("counts", {}) if isinstance(maintenance.get("counts"), dict) else {}
    maintenance_ready = maintenance.get("ready_for_customer_maintenance_rehearsal") is True
    model_failed = int(model_cost["failed_count"])

    quality_score = (
        _report_score_part(min(question_bank_size / 50, 1.0), 18)
        + _report_score_part(retrieval_hit_rate, 14)
        + _report_score_part(citation_coverage, 14)
        + _report_score_part(human_factuality, 18)
        + _report_score_part(knowledge_gap_closure, 12)
    )
    maintenance_score = 14 if maintenance_ready else 8 if maintenance_counts else 0
    model_score = 10 if model_cost["call_count"] > 0 and model_failed == 0 else 6 if model_cost["call_count"] > 0 else 4
    health_score = max(0, min(100, quality_score + maintenance_score + model_score))
    blocked = question_bank_size <= 0 or review.latest_evaluation_run_id is None
    report_status, status_label, health_label = _ops_status_from_score(health_score, blocked=blocked)

    monthly_health = _ops_section(
        "monthly_health",
        "本月健康度",
        "blocked" if blocked else "ok" if health_score >= 85 else "warning" if health_score >= 70 else "risk",
        (
            "本月已有基础证据，可作为客户侧月度运维复盘材料。"
            if not blocked
            else "当前缺少月度评测运行或题库证据，只能生成阻断报告。"
        ),
        [
            _ops_metric("health_score", "健康分", f"{health_score}/100", "ok" if health_score >= 85 else "warning", "由回复质量、知识维护、本地维护和成本证据综合计算。"),
            _ops_metric("question_bank_size", "题库规模", f"{int(question_bank_size)} 题", "ok" if question_bank_size >= 50 else "warning", "少于 50 条不能作为正式准确率验收。"),
            _ops_metric("manual_or_blocked", "需人工/阻断", f"{manual_or_blocked} 次", "warning" if manual_or_blocked else "ok", "仅用于发现风险，不代表已真实外发。"),
        ],
        [
            {"source": "monthly_quality_review", "schema_version": review.schema_version, "latest_evaluation_run_id": review.latest_evaluation_run_id},
            {"source": "local_maintenance_readiness", "schema_version": maintenance.get("schema_version"), "maturity_status": maintenance.get("maturity_status")},
        ],
        [
            "先补齐真实脱敏题库与人工事实性标签。",
            "每月固定同一题集复跑，比较命中、引用、转人工和成本趋势。",
        ],
    )
    reply_quality = _ops_section(
        "reply_quality",
        "回复质量",
        "ok" if human_factuality is not None and human_factuality >= 0.8 else "warning",
        "质量口径只看最终客服答案和转人工策略，不把检索命中率直接当准确率。",
        [
            _ops_metric("retrieval_hit_rate", "检索命中", _format_rate_value(retrieval_hit_rate), _metric_status(retrieval_hit_rate, 0.8, 0.65), "知识检索命中率。"),
            _ops_metric("citation_coverage", "引用覆盖", _format_rate_value(citation_coverage), _metric_status(citation_coverage, 0.75, 0.6), "回复依据是否能回溯。"),
            _ops_metric("human_factuality", "人工事实性", _format_rate_value(human_factuality), "ok" if human_factuality is not None and human_factuality >= 0.8 else "missing", "没有人工标签时不报告完整准确率。"),
            _ops_metric("auto_reply_rate", "自动回复准备率", _format_rate_value(auto_reply_rate), _metric_status(auto_reply_rate, 0.55, 0.35), "只代表可自动回复决策，不代表真实平台发送。"),
        ],
        [{"source": "knowledge_evaluation_run", "run_id": review.latest_evaluation_run_id, "set_id": review.latest_evaluation_set_id}],
        [
            "低置信或无引用答案继续转人工。",
            "抽样复核最终答案的事实正确、引用充分、禁用承诺和转人工正确性。",
        ],
    )
    knowledge_maintenance = _ops_section(
        "knowledge_maintenance",
        "知识维护",
        "critical" if high_gaps else "warning" if open_gaps else "ok",
        "把知识缺口、复测结果和下月补充动作放在同一处，方便客户侧维护。",
        [
            _ops_metric("open_gaps", "开放缺口", f"{open_gaps} 个", "warning" if open_gaps else "ok", "开放缺口会降低自动回复覆盖。"),
            _ops_metric("high_gaps", "高风险缺口", f"{high_gaps} 个", "critical" if high_gaps else "ok", "高风险缺口应优先修复。"),
            _ops_metric("gap_closure", "缺口闭环", _format_rate_value(knowledge_gap_closure), _metric_status(knowledge_gap_closure, 0.65, 0.4), "本月缺口解决相对开放缺口的情况。"),
            _ops_metric("human_reviews", "人工复核样本", f"{human_reviews} 条", "warning" if human_reviews else "ok", "用于发现低置信和风险策略问题。"),
        ],
        [{"source": "knowledge_gap_summary", **review.knowledge_gap_summary}],
        [
            "按业务对象补知识卡或文档来源。",
            "每个已修复缺口加入回归题，发布后复跑同题集。",
        ],
    )
    model_cost_section = _ops_section(
        "model_cost",
        "成本用量",
        "warning" if model_failed else "ok",
        "只展示用量、估算成本和降级风险，不展示提示词、客户原文或密钥。",
        [
            _ops_metric("call_count", "模型调用", f"{model_cost['call_count']} 次", "ok" if model_cost["call_count"] else "missing", "本月持久成本台账记录数。"),
            _ops_metric("estimated_cost", "估算成本", _money_value(model_cost["estimated_cost"], model_cost["currency"]), "ok", "以模型调用记录中的价格版本为准。"),
            _ops_metric("total_units", "计费单位", f"{model_cost['total_units']} {('tokens/chars')}", "ok", "不同 provider 可能按 token 或字符计。"),
            _ops_metric("avg_latency", "平均延迟", f"{model_cost['avg_latency_ms']} ms", "warning" if model_cost["avg_latency_ms"] > 3000 else "ok", "只统计已持久化的模型调用记录。"),
        ],
        [{"source": "model_call_records", "status_counts": model_cost["status_counts"], "provider_counts": model_cost["provider_counts"]}],
        [
            "预算超限时先降级模型，再进入确定性知识草稿或转人工。",
            "显式指定 provider 失败不得静默切换为伪成功。",
        ],
    )
    local_maintenance = _ops_section(
        "local_maintenance",
        "本地维护",
        "ok" if maintenance_ready else "warning",
        str(maintenance.get("summary") or "本地维护证据待补齐。"),
        [
            _ops_metric("diagnostic_intake", "诊断包接收", f"{int(maintenance_counts.get('diagnostic_intake_accepted', 0) or 0)} 次", "ok" if maintenance_counts.get("diagnostic_intake_accepted") else "pending", "客户主动授权上传后才进入售后处理。"),
            _ops_metric("signed_update_package", "签名更新包", f"{int(maintenance_counts.get('signed_update_package_total', 0) or 0)} 个", "ok" if maintenance_counts.get("signed_update_package_total") else "pending", "不静默更新，客户管理员确认后应用。"),
            _ops_metric("verified_backup", "校验备份", f"{int(maintenance_counts.get('local_backup_verified', 0) or 0)} 个", "ok" if maintenance_counts.get("local_backup_verified") else "pending", "更新前必须有备份和恢复演练。"),
            _ops_metric("restore_dry_run", "恢复演练", f"{int(maintenance_counts.get('restore_dry_run_total', 0) or 0)} 次", "ok" if maintenance_counts.get("restore_dry_run_total") else "pending", "用于证明更新可回退。"),
        ],
        [{"source": "local_maintenance_readiness", "gates": maintenance.get("gates", []), "counts": maintenance_counts}],
        [str(item) for item in maintenance.get("recommended_next_steps", [])][:4],
    )

    risk_items: list[MonthlyOpsReportRiskRead] = []
    if blocked:
        risk_items.append(_ops_risk("missing_quality_evidence", "缺少月度质量证据", "critical", "没有可用评测运行或题库规模为 0。", "先完成内部题库评测和最终答案采样。"))
    if question_bank_size < 50:
        risk_items.append(_ops_risk("question_bank_insufficient", "题库规模不足", "warning", "少于 50 条题库不能作为完整准确率验收。", "导入 50-100 条脱敏真实问题。"))
    if high_gaps:
        risk_items.append(_ops_risk("high_knowledge_gap", "高风险知识缺口", "critical", f"当前仍有 {high_gaps} 个高风险开放缺口。", "优先补知识并加入回归题。"))
    if human_factuality is None:
        risk_items.append(_ops_risk("missing_human_factuality", "缺少人工事实性标签", "warning", "无法证明最终客服答案事实正确。", "抽样标注事实正确、引用充分和禁用承诺。"))
    if not maintenance_ready:
        risk_items.append(_ops_risk("maintenance_evidence_missing", "本地维护证据不足", "warning", "诊断包、签名更新、备份或恢复演练尚未形成完整证据。", "先完成本地维护演练。"))
    if model_failed:
        risk_items.append(_ops_risk("model_call_failure", "模型调用失败", "warning", f"本月模型失败或非成功状态 {model_failed} 次。", "复核 provider、预算门禁和降级记录。"))

    next_month_actions = [
        "用同一题集做月初/月末质量对比。",
        "把新增知识缺口补成知识卡或文档，并附来源。",
        "检查模型成本是否超过预算，必要时调整自动回复策略。",
        "生成诊断包和备份演练记录，作为下月维护证据。",
    ]
    if blocked:
        next_month_actions.insert(0, "先完成内部题库评测运行，再生成客户侧月度运维报告。")

    return MonthlyOpsReportRead(
        tenant_id=tenant_id,
        schema_version=MONTHLY_OPS_REPORT_SCHEMA_VERSION,
        period=review.period,
        period_start=review.period_start,
        period_end=review.period_end,
        generated_at=utc_now(),
        report_status=report_status,
        status_label=status_label,
        health_score=health_score,
        health_label=health_label,
        monthly_health=monthly_health,
        reply_quality=reply_quality,
        knowledge_maintenance=knowledge_maintenance,
        model_cost=model_cost_section,
        local_maintenance=local_maintenance,
        risk_items=risk_items,
        next_month_actions=next_month_actions,
        upstream_evidence={
            "monthly_quality_review_schema_version": review.schema_version,
            "local_maintenance_schema_version": maintenance.get("schema_version"),
            "latest_evaluation_run_id": review.latest_evaluation_run_id,
            "latest_evaluation_set_id": review.latest_evaluation_set_id,
            "model_call_record_count": model_cost["call_count"],
        },
        data_boundaries=[
            "本报告是客户侧月度运维复盘材料，不是生产 SLA，也不是生产服务等级承诺。",
            "不输出客户原文、草稿全文、密钥、token、数据库密码或平台 payload。",
            "内部演练数据不能写成客户正式签收；真实平台外发继续关闭。",
            "RPA、模拟点击、个人号外挂不进入正式默认交付链。",
        ],
        safety={
            "remote_control_performed": False,
            "silent_update_performed": False,
            "automatic_update_performed": False,
            "automatic_upload_performed": False,
            "raw_customer_text_required": False,
            "manual_transfer_required": True,
            "customer_admin_confirmation_required": True,
        },
        raw_text_included=False,
        draft_text_included=False,
        secret_included=False,
        external_call_performed=False,
        external_platform_write_performed=False,
        real_platform_send_ready=False,
        production_sla_ready=False,
        formal_customer_signoff_ready=False,
    )


def _monthly_metric(review: MonthlyQualityReviewRead, key: str) -> MonthlyQualityReviewMetricRead | None:
    return next((metric for metric in review.metrics if metric.key == key), None)


def _metric_value(review: MonthlyQualityReviewRead, key: str) -> float | None:
    metric = _monthly_metric(review, key)
    return metric.numeric_value if metric else None


def _payload_float(payload: dict[str, Any], key: str) -> float | None:
    value = payload.get(key)
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _report_score_part(value: float | None, weight: int) -> int:
    if value is None:
        return 0
    return int(round(max(0.0, min(1.0, value)) * weight))


def _customer_report_metric(metric: MonthlyQualityReviewMetricRead | None, *, fallback_key: str, fallback_label: str) -> CustomerQualityReportMetricRead:
    if metric is None:
        return CustomerQualityReportMetricRead(
            key=fallback_key,
            label=fallback_label,
            value="待补齐",
            status="missing",
            detail="当前周期没有足够数据形成该指标。",
        )
    return CustomerQualityReportMetricRead(
        key=metric.key,
        label=metric.label,
        value=metric.value,
        status=metric.status,
        detail=metric.detail,
    )


def _customer_report_section(
    key: str,
    title: str,
    status: str,
    summary: str,
    evidence: str,
    next_steps: list[str],
) -> CustomerQualityReportSectionRead:
    return CustomerQualityReportSectionRead(
        key=key,
        title=title,
        status=status,
        summary=summary,
        evidence=evidence,
        next_steps=next_steps,
    )


def _load_h2w11j_gap_rehearsal_evidence() -> CustomerQualityReportGapRehearsalEvidenceRead | None:
    if not H2W11J_GAP_REHEARSAL_SUMMARY_PATH.exists():
        return None
    try:
        payload = json.loads(H2W11J_GAP_REHEARSAL_SUMMARY_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None

    metrics = payload.get("metrics") if isinstance(payload.get("metrics"), dict) else {}
    boundaries = payload.get("boundaries") if isinstance(payload.get("boundaries"), dict) else {}
    if payload.get("phase") != "H2W-11J" or payload.get("status") != "passed":
        return None

    ready_for_review = bool(metrics.get("ready_for_gap_quality_report_review") is True)
    ready_for_signoff = bool(metrics.get("ready_for_formal_accuracy_signoff") is True)
    return CustomerQualityReportGapRehearsalEvidenceRead(
        schema_version=CUSTOMER_QUALITY_REPORT_GAP_REHEARSAL_SCHEMA_VERSION,
        phase=str(payload.get("phase") or "H2W-11J"),
        evidence_source=str(H2W11J_GAP_REHEARSAL_SUMMARY_PATH.relative_to(STANDARD_OPS_ROOT)),
        case_count=int(metrics.get("case_count") or 0),
        auto_reply_label_count=int(metrics.get("auto_reply_label_count") or 0),
        handoff_not_applicable_count=int(metrics.get("handoff_not_applicable_count") or 0),
        auto_reply_factuality_rate=float(metrics.get("auto_reply_factuality_rate") or 0.0),
        citation_sufficient_rate=float(metrics.get("citation_sufficient_rate") or 0.0),
        forbidden_commitment_pass_rate=float(metrics.get("forbidden_commitment_pass_rate") or 0.0),
        handoff_correct_rate=float(metrics.get("handoff_correct_rate") or 0.0),
        ready_for_gap_quality_report_review=ready_for_review,
        ready_for_formal_accuracy_signoff=ready_for_signoff,
        final_answer_text_exported=bool(boundaries.get("final_answer_text_exported") is True),
        provider_call_performed=bool(boundaries.get("provider_call_performed") is True),
        real_platform_send_performed=bool(boundaries.get("real_platform_send_performed") is True),
        external_platform_write_performed=bool(boundaries.get("external_platform_write_performed") is True),
        conclusion=(
            "缺口样本已完成本地确定性最终答案演练，可进入客户质量报告复核。"
            if ready_for_review
            else "缺口样本演练证据不足，暂不能进入客户质量报告复核。"
        ),
        boundary=f"{GAP_REHEARSAL_FORMAL_SIGNOFF_BOUNDARY}；这只是本地演练证据，不是正式客户准确率签收，也不代表真实渠道外发已完成。",
    )


def get_customer_quality_report(
    db: Session,
    tenant_id: int,
    *,
    year: int | None,
    month: int | None,
    principal: CurrentPrincipal,
) -> CustomerQualityReportRead:
    review = get_monthly_quality_review(db, tenant_id, year=year, month=month, principal=principal)
    latest_run = db.get(KnowledgeEvaluationRun, review.latest_evaluation_run_id) if review.latest_evaluation_run_id else None
    summary_payload = latest_run.summary_payload if latest_run and isinstance(latest_run.summary_payload, dict) else {}

    question_bank_size = _metric_value(review, "question_bank_size") or 0
    retrieval_hit_rate = _metric_value(review, "retrieval_hit_rate")
    citation_coverage = _metric_value(review, "citation_coverage")
    human_factuality_rate = _metric_value(review, "human_factuality")
    knowledge_gap_closure = _metric_value(review, "knowledge_gap_closure")
    sample_coverage = _payload_float(summary_payload, "final_answer_sample_coverage")
    sampled_cases = int(summary_payload.get("final_answer_sampled_cases") or 0)
    labeled_cases = int(summary_payload.get("final_answer_factuality_labeled_cases") or 0)
    total_cases = int(latest_run.total_cases if latest_run else question_bank_size)
    open_gap_count = review.knowledge_gap_summary.get("open_backlog", 0)
    high_gap_count = review.knowledge_gap_summary.get("high_or_critical_open", 0)
    human_factuality_measured = human_factuality_rate is not None and labeled_cases > 0
    gap_rehearsal_evidence = _load_h2w11j_gap_rehearsal_evidence()

    score = (
        _report_score_part(min(question_bank_size / 50, 1.0), 20)
        + _report_score_part(sample_coverage, 20)
        + _report_score_part(human_factuality_rate, 25)
        + _report_score_part(citation_coverage, 15)
        + _report_score_part(knowledge_gap_closure, 10)
        + (10 if not any(cause.severity == "critical" and cause.count > 0 for cause in review.root_causes) else 0)
    )

    if question_bank_size < 50:
        report_status = "sample_insufficient"
        status_label = "样本不足"
        conclusion = "当前题库少于 50 条，只适合作为方向性复盘，不能作为客户签收准确率依据。"
    elif sample_coverage is None or sample_coverage < 0.8:
        report_status = "sample_capture_required"
        status_label = "待补最终回复样本"
        conclusion = "题库规模已经具备初步复盘口径，但最终客服回复样本覆盖不足，需要补采样后再确认质量。"
    elif not human_factuality_measured:
        report_status = "human_label_required"
        status_label = "待人工标注"
        conclusion = "已有最终回复样本，但缺少人工事实性标签，暂不能对客户报告完整客服准确率。"
    elif human_factuality_rate is not None and human_factuality_rate >= 0.8 and high_gap_count == 0:
        report_status = "controlled_trial_ready"
        status_label = "可进入受控试点"
        conclusion = "当前样本、最终回复和人工标签已形成初步闭环，可进入受控试点签收，但仍需线上回执继续观察。"
    else:
        report_status = "repair_required"
        status_label = "需要继续修复"
        conclusion = "当前质量闭环已经可解释问题来源，但仍需继续补知识、复核转人工和跑同题集回归。"

    executive_summary = [
        f"本周期共纳入 {total_cases} 条评测题，最终回复采样 {sampled_cases} 条，人工事实性标注 {labeled_cases} 条。",
        f"检索命中为 {_format_rate_value(retrieval_hit_rate)}，引用覆盖为 {_format_rate_value(citation_coverage)}，人工事实性为 {_format_rate_value(human_factuality_rate)}。",
        f"当前开放知识缺口 {open_gap_count} 个，其中高风险或紧急缺口 {high_gap_count} 个。",
        conclusion,
    ]
    if gap_rehearsal_evidence:
        executive_summary.insert(
            3,
            (
                f"缺口样本本地演练 {gap_rehearsal_evidence.case_count} 条，"
                f"自动回复 {gap_rehearsal_evidence.auto_reply_label_count} 条，"
                f"转人工 {gap_rehearsal_evidence.handoff_not_applicable_count} 条；"
                "该证据只用于复核，不作为正式准确率签收。"
            ),
        )

    headline_metrics = [
        _customer_report_metric(_monthly_metric(review, "question_bank_size"), fallback_key="question_bank_size", fallback_label="本月题库"),
        CustomerQualityReportMetricRead(
            key="final_answer_sample_coverage",
            label="最终回复采样",
            value=_format_rate_value(sample_coverage),
            status="ok" if sample_coverage is not None and sample_coverage >= 0.8 else "warning" if sample_coverage else "missing",
            detail="只统计已经保存最终客服回复样本的评测题，样本不足时不做准确率签收。",
        ),
        _customer_report_metric(_monthly_metric(review, "human_factuality"), fallback_key="human_factuality", fallback_label="人工事实性"),
        _customer_report_metric(_monthly_metric(review, "citation_coverage"), fallback_key="citation_coverage", fallback_label="引用覆盖"),
    ]
    if gap_rehearsal_evidence:
        headline_metrics.append(
            CustomerQualityReportMetricRead(
                key="gap_rehearsal_evidence",
                label="缺口演练",
                value=f"{gap_rehearsal_evidence.case_count} 条",
                status="ok" if gap_rehearsal_evidence.ready_for_gap_quality_report_review else "warning",
                detail="来自本地缺口样本演练；不含完整最终答案正文，不代表正式签收。",
            )
        )

    sections = [
        _customer_report_section(
            "sample_and_question_bank",
            "样本与题库",
            "ok" if question_bank_size >= 50 and sampled_cases >= 1 else "warning",
            "题库用于验证客服系统面对真实问题时的知识覆盖、转人工边界和回复质量。",
            f"题库 {total_cases} 条；最终回复样本 {sampled_cases} 条；人工标签 {labeled_cases} 条。",
            [
                "继续保持 50-100 条脱敏真实问题作为月度固定题集。",
                "新增业务或活动上线前，先补对应问题和标准答案。",
            ],
        ),
        _customer_report_section(
            "answer_quality",
            "最终回复质量",
            "ok" if human_factuality_measured and (human_factuality_rate or 0) >= 0.8 else "warning",
            "最终回复质量必须由人工事实性标签确认，不能只看检索命中。",
            f"人工事实性 {_format_rate_value(human_factuality_rate)}；已标注 {labeled_cases} 条。",
            [
                "优先标注事实正确、部分正确、事实有误、应转人工四类结果。",
                "事实有误样本进入知识缺口或风险话术修复。",
            ],
        ),
        _customer_report_section(
            "knowledge_coverage",
            "知识覆盖与引用",
            "ok" if (retrieval_hit_rate or 0) >= 0.8 and (citation_coverage or 0) >= 0.75 else "warning",
            "知识覆盖决定 AI 能否引用可靠依据，也决定自动回复能否放行。",
            f"检索命中 {_format_rate_value(retrieval_hit_rate)}；引用覆盖 {_format_rate_value(citation_coverage)}；开放缺口 {open_gap_count} 个。",
            [
                "把开放缺口补成知识卡或知识文档。",
                "每次知识更新后使用同一题集回归验证。",
            ],
        ),
        _customer_report_section(
            "handoff_and_risk",
            "转人工与风险边界",
            "ok" if high_gap_count == 0 else "warning",
            "赔付、投诉、法务、隐私和无法确认的信息必须优先进入人工处理。",
            f"高风险或紧急知识缺口 {high_gap_count} 个；本报告不包含真实外发回执。",
            [
                "复核应转人工样本是否被正确拦截。",
                "为高风险问题补标准话术和禁用承诺规则。",
            ],
        ),
    ]
    if gap_rehearsal_evidence:
        sections.append(
            _customer_report_section(
                "gap_rehearsal_evidence",
                "缺口样本演练证据",
                "ok" if gap_rehearsal_evidence.ready_for_gap_quality_report_review else "warning",
                "缺口样本已跑成本地确定性最终答案标签，用于补强客户报告复核证据。",
                (
                    f"样本 {gap_rehearsal_evidence.case_count} 条；"
                    f"自动回复事实性 {_format_rate_value(gap_rehearsal_evidence.auto_reply_factuality_rate)}；"
                    f"引用充分 {_format_rate_value(gap_rehearsal_evidence.citation_sufficient_rate)}；"
                    f"转人工正确 {_format_rate_value(gap_rehearsal_evidence.handoff_correct_rate)}。"
                ),
                [
                    "正式签收前仍需客户确认标准答案、真实题库和线上回执。",
                    "保持完整最终答案正文不导出，只保存 hash、标签和边界证据。",
                ],
            )
        )

    action_plan = [
        CustomerQualityReportActionRead(
            key=action.key,
            label=action.label,
            owner=action.owner,
            priority=action.priority,
            status=action.status,
            evidence=action.evidence,
            next_step=action.next_step,
        )
        for action in review.action_items[:5]
    ]
    if gap_rehearsal_evidence and not gap_rehearsal_evidence.ready_for_formal_accuracy_signoff:
        action_plan.append(
            CustomerQualityReportActionRead(
                key="gap_rehearsal_to_formal_signoff",
                label="补齐正式准确率签收依据",
                owner="交付负责人",
                priority="P1",
                status="open",
                evidence="缺口样本本地演练已通过，但仍未进入正式准确率签收。",
                next_step="补客户确认标准答案、真实题库、线上回执和正式报告签收后再进入正式准确率签收。",
            )
        )

    signoff_checklist = [
        "题库达到 50-100 条脱敏真实客户问题。",
        "最终客服回复样本覆盖率达到 80% 以上。",
        "人工事实性标签覆盖关键场景，且错误样本已进入修复队列。",
        "知识缺口完成修复，并用同一题集完成发布前后对比。",
        "真实外发、回执、失败重试和审计闭环完成单独验收后，才进入线上签收。",
    ]
    data_boundaries = [
        *review.data_boundaries,
        "本客户报告不包含原始客户问题、完整回复正文、联系方式、密钥或渠道 payload。",
        "报告可信度不是客服准确率；它只表示当前样本、采样、人工标签和知识闭环是否足以支撑复盘。",
    ]
    if gap_rehearsal_evidence:
        signoff_checklist.append("缺口样本演练只能作为本地复核证据，不能替代客户正式准确率签收。")
        data_boundaries.append("缺口样本演练不调用真实模型、不真实外发、不导出完整最终答案正文。")

    return CustomerQualityReportRead(
        tenant_id=tenant_id,
        schema_version=CUSTOMER_QUALITY_REPORT_SCHEMA_VERSION,
        report_title=f"{review.period} 客服质量报告",
        period=review.period,
        period_start=review.period_start,
        period_end=review.period_end,
        generated_at=utc_now(),
        report_status=report_status,
        report_status_label=status_label,
        report_confidence_score=max(0, min(100, score)),
        quality_conclusion=conclusion,
        executive_summary=executive_summary,
        headline_metrics=headline_metrics,
        sections=sections,
        action_plan=action_plan,
        gap_rehearsal_evidence=gap_rehearsal_evidence,
        signoff_checklist=signoff_checklist,
        data_boundaries=data_boundaries,
        source_monthly_review_schema_version=review.schema_version,
        latest_evaluation_run_id=review.latest_evaluation_run_id,
        latest_evaluation_set_id=review.latest_evaluation_set_id,
        raw_text_included=False,
        model_call_performed=False,
        external_call_performed=False,
        external_platform_write_performed=False,
    )


def _customer_report_html_list(items: list[str]) -> str:
    if not items:
        return "<p class=\"empty\">暂无。</p>"
    return "<ul>" + "".join(f"<li>{html.escape(item)}</li>" for item in items) + "</ul>"


def _render_customer_quality_report_html(report: CustomerQualityReportRead) -> str:
    gap_evidence_html = ""
    if report.gap_rehearsal_evidence:
        evidence = report.gap_rehearsal_evidence
        gap_evidence_html = f"""
    <section class="summary">
      <h2>缺口样本本地演练证据</h2>
      <p>{html.escape(evidence.conclusion)}</p>
      <ul>
        <li>样本 {evidence.case_count} 条；自动回复 {evidence.auto_reply_label_count} 条；转人工 {evidence.handoff_not_applicable_count} 条。</li>
        <li>自动回复事实性 {_format_rate_value(evidence.auto_reply_factuality_rate)}；引用充分 {_format_rate_value(evidence.citation_sufficient_rate)}；禁用承诺通过 {_format_rate_value(evidence.forbidden_commitment_pass_rate)}。</li>
        <li>{html.escape(evidence.boundary)}</li>
      </ul>
    </section>
        """
    metrics = "\n".join(
        f"""
        <article class="metric {html.escape(metric.status)}">
          <span>{html.escape(metric.label)}</span>
          <strong>{html.escape(metric.value)}</strong>
          <small>{html.escape(metric.detail)}</small>
        </article>
        """
        for metric in report.headline_metrics
    )
    sections = "\n".join(
        f"""
        <section class="section {html.escape(section.status)}">
          <div class="section-head">
            <span>{html.escape(section.status)}</span>
            <h3>{html.escape(section.title)}</h3>
          </div>
          <p>{html.escape(section.summary)}</p>
          <small>{html.escape(section.evidence)}</small>
          {_customer_report_html_list(section.next_steps)}
        </section>
        """
        for section in report.sections
    )
    action_plan = "\n".join(
        f"""
        <tr>
          <td>{html.escape(action.priority)}</td>
          <td>{html.escape(action.owner)}</td>
          <td>{html.escape(action.label)}</td>
          <td>{html.escape(action.evidence)}</td>
          <td>{html.escape(action.next_step)}</td>
        </tr>
        """
        for action in report.action_plan
    ) or "<tr><td colspan=\"5\">当前无未关闭动作，继续保持月度抽样和同题集回归。</td></tr>"
    generated_at = report.generated_at.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    period_range = f"{report.period_start.date().isoformat()} 至 {report.period_end.date().isoformat()}"
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{html.escape(report.report_title)}</title>
  <style>
    :root {{
      color-scheme: light;
      --ink: #102033;
      --muted: #5f7086;
      --line: #d8e2ee;
      --soft: #f6f8fb;
      --green: #166534;
      --amber: #92400e;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: #eef3f8;
      color: var(--ink);
      font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", "Microsoft YaHei", sans-serif;
      line-height: 1.65;
    }}
    main {{
      width: min(1120px, calc(100% - 56px));
      margin: 28px auto;
      border: 1px solid var(--line);
      border-radius: 18px;
      background: #fff;
      padding: 34px;
      box-shadow: 0 24px 70px rgba(30, 49, 80, 0.12);
    }}
    header {{ display: grid; grid-template-columns: 1fr auto; gap: 24px; align-items: start; border-bottom: 1px solid var(--line); padding-bottom: 22px; }}
    h1 {{ margin: 0 0 8px; font-size: 30px; line-height: 1.18; }}
    h2 {{ margin: 28px 0 12px; font-size: 20px; }}
    h3 {{ margin: 0; font-size: 16px; }}
    p, ul {{ margin: 0; }}
    small, .muted {{ color: var(--muted); }}
    .score {{
      min-width: 132px;
      border: 1px solid #bbf7d0;
      border-radius: 16px;
      background: #f0fdf4;
      color: var(--green);
      padding: 16px;
      text-align: center;
    }}
    .score.warning {{ border-color: #fde68a; background: #fffbeb; color: var(--amber); }}
    .score b {{ display: block; font-size: 42px; line-height: 1; }}
    .summary {{ display: grid; gap: 12px; margin-top: 22px; border: 1px solid var(--line); border-radius: 14px; background: var(--soft); padding: 18px; }}
    .metrics, .sections {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; }}
    .metric, .section, .boundary, .signoff {{ border: 1px solid var(--line); border-radius: 14px; padding: 16px; background: #fff; }}
    .metric.warning, .metric.missing, .section.warning {{ border-color: #fde68a; background: #fffaf0; }}
    .metric span, .section-head span {{ color: var(--muted); font-size: 12px; font-weight: 700; }}
    .metric strong {{ display: block; margin: 8px 0 4px; font-size: 25px; }}
    .sections {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
    .section {{ display: grid; gap: 8px; }}
    .section-head {{ display: flex; justify-content: space-between; gap: 12px; align-items: start; }}
    table {{ width: 100%; border-collapse: collapse; border: 1px solid var(--line); border-radius: 14px; overflow: hidden; }}
    th, td {{ border-bottom: 1px solid var(--line); padding: 12px; text-align: left; vertical-align: top; font-size: 13px; }}
    th {{ background: var(--soft); color: var(--muted); }}
    tr:last-child td {{ border-bottom: 0; }}
    .two-col {{ display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }}
    .signature-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-top: 12px; }}
    .signature-grid div {{ min-height: 58px; border: 1px dashed #b7c3d2; border-radius: 12px; padding: 10px; color: var(--muted); }}
    footer {{ margin-top: 30px; padding-top: 18px; border-top: 1px solid var(--line); color: var(--muted); font-size: 12px; }}
  </style>
</head>
<body>
  <main>
    <header>
      <div>
        <p class="muted">万法常世智能客服系统 · 客户质量复盘留档</p>
        <h1>{html.escape(report.report_title)}</h1>
        <p>{html.escape(report.quality_conclusion)}</p>
        <small>周期：{html.escape(report.period)}（{html.escape(period_range)}） · 生成时间：{html.escape(generated_at)}</small>
      </div>
      <div class="score {'warning' if report.report_status != 'controlled_trial_ready' else ''}">
        <b>{report.report_confidence_score}</b>
        <span>{html.escape(report.report_status_label)}</span>
      </div>
    </header>

    <section class="summary">
      <h2>摘要</h2>
      {_customer_report_html_list(report.executive_summary)}
    </section>

    <h2>关键指标</h2>
    <section class="metrics">{metrics}</section>

    {gap_evidence_html}

    <h2>复盘结论</h2>
    <section class="sections">{sections}</section>

    <h2>签收前动作</h2>
    <table>
      <thead>
        <tr><th>优先级</th><th>负责人</th><th>动作</th><th>依据</th><th>下一步</th></tr>
      </thead>
      <tbody>{action_plan}</tbody>
    </table>

    <h2>签收检查与边界</h2>
    <section class="two-col">
      <div class="signoff">
        <h3>签收前检查项</h3>
        {_customer_report_html_list(report.signoff_checklist)}
      </div>
      <div class="boundary">
        <h3>数据边界</h3>
        {_customer_report_html_list(report.data_boundaries)}
      </div>
    </section>

    <section class="signoff" style="margin-top: 14px;">
      <h3>签收确认区</h3>
      <p class="muted">本留档件用于试点月度复盘。正式线上签收需要另行确认真实外发、回执、失败重试和审计闭环。</p>
      <div class="signature-grid">
        <div>客户负责人签字 / 日期</div>
        <div>我方交付负责人签字 / 日期</div>
        <div>备注</div>
      </div>
    </section>

    <footer>
      本文件由本地工作台生成；不包含原始客户问题、完整最终回复、人工备注、联系方式、密钥或渠道 payload。
    </footer>
  </main>
</body>
</html>"""


def _xml_escape(value: object) -> str:
    return html.escape(str(value), quote=True)


def _xlsx_column_name(index: int) -> str:
    name = ""
    number = index
    while number:
        number, remainder = divmod(number - 1, 26)
        name = chr(65 + remainder) + name
    return name


def _xlsx_row(row_index: int, values: list[object]) -> str:
    cells = []
    for column_index, value in enumerate(values, start=1):
        ref = f"{_xlsx_column_name(column_index)}{row_index}"
        cells.append(f'<c r="{ref}" t="inlineStr"><is><t>{_xml_escape(value)}</t></is></c>')
    return f'<row r="{row_index}">{"".join(cells)}</row>'


def _render_customer_quality_report_xlsx(report: CustomerQualityReportRead) -> bytes:
    rows: list[list[object]] = [
        ["类型", "项目", "数值", "状态", "说明"],
        ["概览", "报告标题", report.report_title, report.report_status_label, report.quality_conclusion],
        ["概览", "报告周期", report.period, "", f"{report.period_start.date().isoformat()} 至 {report.period_end.date().isoformat()}"],
        ["概览", "生成时间", report.generated_at.astimezone(timezone.utc).isoformat(), "", "UTC 时间"],
        ["概览", "报告可信度", report.report_confidence_score, report.report_status, "不是客服准确率"],
        ["概览", "数据来源", report.source_monthly_review_schema_version, "", "月度复盘摘要"],
        ["概览", "签收边界", "不是正式电子签章", "", "正式电子签章需另接合规电子签服务"],
    ]
    rows.extend(["指标", metric.label, metric.value, metric.status, metric.detail] for metric in report.headline_metrics)
    if report.gap_rehearsal_evidence:
        evidence = report.gap_rehearsal_evidence
        rows.extend(
            [
                ["缺口演练", "样本数", evidence.case_count, evidence.phase, evidence.boundary],
                ["缺口演练", "自动回复事实性", evidence.auto_reply_factuality_rate, "本地演练", "不代表正式准确率签收"],
                ["缺口演练", "引用充分率", evidence.citation_sufficient_rate, "本地演练", evidence.evidence_source],
                ["缺口演练", "正式签收", "不可进入" if not evidence.ready_for_formal_accuracy_signoff else "可进入", "", "正式签收需客户确认标准答案、真实题库和线上回执"],
            ]
        )
    rows.extend(["复盘章节", section.title, section.evidence, section.status, section.summary] for section in report.sections)
    rows.extend(["后续动作", action.label, action.priority, action.status, action.next_step] for action in report.action_plan)
    rows.extend(["签收检查项", item, "", "", "客户确认前需逐条核对"] for item in report.signoff_checklist)
    rows.extend(["数据边界", item, "", "", "报告不包含原始客户问题、完整回复、人工备注或渠道 payload"] for item in report.data_boundaries)
    sheet_rows = "\n".join(_xlsx_row(index, row) for index, row in enumerate(rows, start=1))
    sheet_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <sheetData>{sheet_rows}</sheetData>
</worksheet>"""
    workbook_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
  xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheets>
    <sheet name="客户质量报告明细" sheetId="1" r:id="rId1"/>
  </sheets>
</workbook>"""
    workbook_rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
</Relationships>"""
    package_rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>"""
    content_types = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
  <Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
</Types>"""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", content_types)
        archive.writestr("_rels/.rels", package_rels)
        archive.writestr("xl/workbook.xml", workbook_xml)
        archive.writestr("xl/_rels/workbook.xml.rels", workbook_rels)
        archive.writestr("xl/worksheets/sheet1.xml", sheet_xml)
    return buffer.getvalue()


def _docx_paragraph(text: str, *, style: str | None = None) -> str:
    style_xml = f'<w:pPr><w:pStyle w:val="{_xml_escape(style)}"/></w:pPr>' if style else ""
    return f"<w:p>{style_xml}<w:r><w:t>{_xml_escape(text)}</w:t></w:r></w:p>"


def _render_customer_quality_report_docx(report: CustomerQualityReportRead) -> bytes:
    paragraphs = [
        _docx_paragraph(report.report_title, style="Title"),
        _docx_paragraph(f"周期：{report.period}；生成时间：{report.generated_at.astimezone(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}"),
        _docx_paragraph(f"报告状态：{report.report_status_label}；报告可信度：{report.report_confidence_score}"),
        _docx_paragraph(report.quality_conclusion),
        _docx_paragraph("摘要", style="Heading1"),
        *[_docx_paragraph(f"- {item}") for item in report.executive_summary],
        _docx_paragraph("关键指标", style="Heading1"),
        *[
            _docx_paragraph(f"{metric.label}：{metric.value}（{metric.detail}）")
            for metric in report.headline_metrics
        ],
        _docx_paragraph("复盘结论", style="Heading1"),
    ]
    if report.gap_rehearsal_evidence:
        evidence = report.gap_rehearsal_evidence
        paragraphs.extend(
            [
                _docx_paragraph("缺口样本本地演练证据", style="Heading1"),
                _docx_paragraph(evidence.conclusion),
                _docx_paragraph(
                    f"样本 {evidence.case_count} 条；自动回复 {evidence.auto_reply_label_count} 条；"
                    f"转人工 {evidence.handoff_not_applicable_count} 条；"
                    f"自动回复事实性 {_format_rate_value(evidence.auto_reply_factuality_rate)}；"
                    f"引用充分 {_format_rate_value(evidence.citation_sufficient_rate)}。"
                ),
                _docx_paragraph(evidence.boundary),
            ]
        )
    for section in report.sections:
        paragraphs.append(_docx_paragraph(section.title, style="Heading2"))
        paragraphs.append(_docx_paragraph(f"{section.summary}；依据：{section.evidence}"))
        paragraphs.extend(_docx_paragraph(f"- {item}") for item in section.next_steps)
    paragraphs.append(_docx_paragraph("签收检查与边界", style="Heading1"))
    paragraphs.extend(_docx_paragraph(f"- {item}") for item in report.signoff_checklist)
    paragraphs.append(_docx_paragraph("本地签收记录不是正式电子签章；正式电子签章需要另行接入合规电子签服务。"))
    paragraphs.append(_docx_paragraph("本报告不包含原始客户问题、完整最终回复、人工备注、联系方式、密钥或渠道 payload。"))
    paragraphs.append(_docx_paragraph("数据边界", style="Heading1"))
    paragraphs.extend(_docx_paragraph(f"- {item}") for item in report.data_boundaries)
    document_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    {''.join(paragraphs)}
    <w:sectPr><w:pgSz w:w="11906" w:h="16838"/><w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440"/></w:sectPr>
  </w:body>
</w:document>"""
    styles_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:style w:type="paragraph" w:styleId="Title"><w:name w:val="Title"/><w:rPr><w:b/><w:sz w:val="36"/></w:rPr></w:style>
  <w:style w:type="paragraph" w:styleId="Heading1"><w:name w:val="Heading 1"/><w:rPr><w:b/><w:sz w:val="28"/></w:rPr></w:style>
  <w:style w:type="paragraph" w:styleId="Heading2"><w:name w:val="Heading 2"/><w:rPr><w:b/><w:sz w:val="24"/></w:rPr></w:style>
</w:styles>"""
    package_rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>"""
    content_types = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
</Types>"""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", content_types)
        archive.writestr("_rels/.rels", package_rels)
        archive.writestr("word/document.xml", document_xml)
        archive.writestr("word/styles.xml", styles_xml)
    return buffer.getvalue()


def _customer_quality_report_export_body(
    report: CustomerQualityReportRead, export_format: str
) -> tuple[str, str, str, str, int, str]:
    if export_format == "html":
        body = _render_customer_quality_report_html(report)
        raw = body.encode("utf-8")
        return body, "utf-8", "text/html; charset=utf-8", "html", len(raw), hashlib.sha256(raw).hexdigest()
    if export_format == "xlsx":
        raw = _render_customer_quality_report_xlsx(report)
        return (
            base64.b64encode(raw).decode("ascii"),
            "base64",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "xlsx",
            len(raw),
            hashlib.sha256(raw).hexdigest(),
        )
    if export_format == "docx":
        raw = _render_customer_quality_report_docx(report)
        return (
            base64.b64encode(raw).decode("ascii"),
            "base64",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "docx",
            len(raw),
            hashlib.sha256(raw).hexdigest(),
        )
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="unsupported customer report export format")


def export_customer_quality_report(
    db: Session,
    tenant_id: int,
    *,
    year: int | None,
    month: int | None,
    export_format: str,
    principal: CurrentPrincipal,
) -> CustomerQualityReportExportRead:
    report = get_customer_quality_report(db, tenant_id, year=year, month=month, principal=principal)
    body, body_encoding, content_type, extension, body_bytes, body_hash = _customer_quality_report_export_body(
        report, export_format
    )
    filename = f"wanfa-customer-quality-report-{tenant_id}-{report.period}.{extension}"
    generated_at = utc_now()
    signoff_record = {
        "status": "pending_customer_confirmation",
        "status_label": "待客户确认",
        "report_period": report.period,
        "report_status": report.report_status,
        "report_confidence_score": report.report_confidence_score,
        "generated_at": generated_at.isoformat(),
        "storage_mode": "local_download_and_audit_event",
        "audit_action": "customer_quality_report.exported",
        "manual_signature_required": True,
        "electronic_signature_performed": False,
        "formal_contract_signoff_performed": False,
    }
    audit_event = add_audit_event(
        db,
        tenant_id=tenant_id,
        actor_id=principal.user.id,
        action="customer_quality_report.exported",
        resource_type="customer_quality_report",
        resource_id=report.period,
        payload={
            "schema_version": CUSTOMER_QUALITY_REPORT_EXPORT_SCHEMA_VERSION,
            "report_schema_version": report.schema_version,
            "export_format": export_format,
            "filename": filename,
            "content_type": content_type,
            "body_encoding": body_encoding,
            "body_sha256": body_hash,
            "body_bytes": body_bytes,
            "body_archived": True,
            "body": body,
            "period": report.period,
            "generated_at": generated_at.isoformat(),
            "report_status": report.report_status,
            "report_status_label": report.report_status_label,
            "report_confidence_score": report.report_confidence_score,
            "signoff_status": signoff_record["status"],
            "raw_text_included": False,
            "final_answer_text_included": False,
            "reviewer_notes_included": False,
            "electronic_signature_performed": False,
            "formal_contract_signoff_performed": False,
            "model_call_performed": False,
            "external_call_performed": False,
            "external_platform_write_performed": False,
        },
    )
    db.flush()
    db.commit()
    return CustomerQualityReportExportRead(
        tenant_id=tenant_id,
        schema_version=CUSTOMER_QUALITY_REPORT_EXPORT_SCHEMA_VERSION,
        report_schema_version=report.schema_version,
        export_format=export_format,
        filename=filename,
        content_type=content_type,
        body=body,
        body_encoding=body_encoding,
        body_sha256=body_hash,
        body_bytes=body_bytes,
        period=report.period,
        generated_at=generated_at,
        report_status=report.report_status,
        report_status_label=report.report_status_label,
        signoff_status=signoff_record["status"],
        signoff_record=signoff_record,
        archived=True,
        archive_audit_event_id=audit_event.id,
        raw_text_included=False,
        final_answer_text_included=False,
        reviewer_notes_included=False,
        electronic_signature_performed=False,
        formal_contract_signoff_performed=False,
        model_call_performed=False,
        external_call_performed=False,
        external_platform_write_performed=False,
    )


def _customer_report_archive_item_from_audit_event(event: AuditEvent) -> CustomerQualityReportArchiveItemRead:
    payload = _load_audit_payload(event)
    export_format = str(payload.get("export_format") or "html")
    body = payload.get("body")
    return CustomerQualityReportArchiveItemRead(
        audit_event_id=event.id,
        tenant_id=event.tenant_id,
        schema_version=CUSTOMER_QUALITY_REPORT_ARCHIVE_LIST_SCHEMA_VERSION,
        report_schema_version=str(payload.get("report_schema_version") or CUSTOMER_QUALITY_REPORT_SCHEMA_VERSION),
        export_schema_version=str(payload.get("schema_version") or CUSTOMER_QUALITY_REPORT_EXPORT_SCHEMA_VERSION),
        export_format=export_format,
        filename=str(payload.get("filename") or f"wanfa-customer-quality-report-{event.resource_id}.{export_format}"),
        content_type=str(payload.get("content_type") or "text/html; charset=utf-8"),
        body_encoding=str(payload.get("body_encoding") or ("base64" if export_format in {"xlsx", "docx"} else "utf-8")),
        body_sha256=str(payload.get("body_sha256") or ""),
        body_bytes=int(payload.get("body_bytes") or 0),
        period=str(payload.get("period") or event.resource_id),
        generated_at=event.created_at,
        report_status=str(payload.get("report_status") or "unknown"),
        report_status_label=str(payload.get("report_status_label") or "未读取报告状态"),
        signoff_status=str(payload.get("signoff_status") or "pending_customer_confirmation"),
        body_archived=isinstance(body, str) and bool(body),
        download_supported=isinstance(body, str) and bool(body),
        raw_text_included=False,
        final_answer_text_included=False,
        reviewer_notes_included=False,
        electronic_signature_performed=False,
        formal_contract_signoff_performed=False,
        model_call_performed=False,
        external_call_performed=False,
        external_platform_write_performed=False,
    )


def list_customer_quality_report_archives(
    db: Session,
    tenant_id: int,
    *,
    page: int,
    page_size: int,
    period: str | None,
    principal: CurrentPrincipal,
) -> CustomerQualityReportArchiveListRead:
    _require_same_tenant(db, tenant_id, principal)
    conditions = [
        AuditEvent.tenant_id == tenant_id,
        AuditEvent.action == "customer_quality_report.exported",
        AuditEvent.resource_type == "customer_quality_report",
    ]
    if period:
        conditions.append(AuditEvent.resource_id == period)
    total = int(db.scalar(select(func.count(AuditEvent.id)).where(*conditions)) or 0)
    offset = (page - 1) * page_size
    events = db.scalars(
        select(AuditEvent)
        .where(*conditions)
        .order_by(AuditEvent.created_at.desc(), AuditEvent.id.desc())
        .offset(offset)
        .limit(page_size)
    ).all()
    return CustomerQualityReportArchiveListRead(
        tenant_id=tenant_id,
        schema_version=CUSTOMER_QUALITY_REPORT_ARCHIVE_LIST_SCHEMA_VERSION,
        page=page,
        page_size=page_size,
        total=total,
        items=[_customer_report_archive_item_from_audit_event(event) for event in events],
        raw_text_included=False,
        final_answer_text_included=False,
        reviewer_notes_included=False,
        electronic_signature_performed=False,
        formal_contract_signoff_performed=False,
        model_call_performed=False,
        external_call_performed=False,
        external_platform_write_performed=False,
    )


def download_customer_quality_report_archive(
    db: Session,
    tenant_id: int,
    archive_event_id: int,
    *,
    principal: CurrentPrincipal,
) -> CustomerQualityReportExportRead:
    _require_same_tenant(db, tenant_id, principal)
    event = db.get(AuditEvent, archive_event_id)
    if (
        not event
        or event.tenant_id != tenant_id
        or event.action != "customer_quality_report.exported"
        or event.resource_type != "customer_quality_report"
    ):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="customer quality report archive not found")
    payload = _load_audit_payload(event)
    body = payload.get("body")
    if not isinstance(body, str) or not body:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="archived report body is not available")
    return CustomerQualityReportExportRead(
        tenant_id=tenant_id,
        schema_version=str(payload.get("schema_version") or CUSTOMER_QUALITY_REPORT_EXPORT_SCHEMA_VERSION),
        report_schema_version=str(payload.get("report_schema_version") or CUSTOMER_QUALITY_REPORT_SCHEMA_VERSION),
        export_format=str(payload.get("export_format") or "html"),
        filename=str(payload.get("filename") or f"wanfa-customer-quality-report-{tenant_id}-{event.resource_id}.html"),
        content_type=str(payload.get("content_type") or "text/html; charset=utf-8"),
        body=body,
        body_encoding=str(payload.get("body_encoding") or "utf-8"),
        body_sha256=str(payload.get("body_sha256") or ""),
        body_bytes=int(payload.get("body_bytes") or 0),
        period=str(payload.get("period") or event.resource_id),
        generated_at=event.created_at,
        report_status=str(payload.get("report_status") or "unknown"),
        report_status_label=str(payload.get("report_status_label") or "未读取报告状态"),
        signoff_status=str(payload.get("signoff_status") or "pending_customer_confirmation"),
        signoff_record={
            "status": str(payload.get("signoff_status") or "pending_customer_confirmation"),
            "status_label": "待客户确认",
            "report_period": str(payload.get("period") or event.resource_id),
            "storage_mode": "local_report_archive",
            "audit_action": event.action,
            "manual_signature_required": True,
            "electronic_signature_performed": False,
            "formal_contract_signoff_performed": False,
        },
        archived=True,
        archive_audit_event_id=event.id,
        raw_text_included=False,
        final_answer_text_included=False,
        reviewer_notes_included=False,
        electronic_signature_performed=False,
        formal_contract_signoff_performed=False,
        model_call_performed=False,
        external_call_performed=False,
        external_platform_write_performed=False,
    )


def _customer_report_signoff_status_label(signoff_status: str) -> str:
    return {
        "accepted": "确认通过",
        "accepted_with_notes": "确认通过，有备注",
        "needs_rework": "需要返修后再确认",
        "rejected": "不通过",
    }.get(signoff_status, "待确认")


def _customer_report_signoff_method_label(method: str) -> str:
    return {
        "local_record": "本地记录",
        "email_confirmation": "邮件确认",
        "meeting_confirmation": "会议确认",
        "offline_signature": "线下签字",
    }.get(method, "本地记录")


def _mask_signer_name(name: str) -> str:
    cleaned = name.strip()
    if not cleaned:
        return ""
    if len(cleaned) == 1:
        return "*"
    if len(cleaned) == 2:
        return f"{cleaned[0]}*"
    return f"{cleaned[0]}{'*' * min(len(cleaned) - 2, 4)}{cleaned[-1]}"


def record_customer_quality_report_signoff(
    db: Session,
    tenant_id: int,
    payload: CustomerQualityReportSignoffCreate,
    *,
    year: int | None,
    month: int | None,
    principal: CurrentPrincipal,
) -> CustomerQualityReportSignoffRead:
    report = get_customer_quality_report(db, tenant_id, year=year, month=month, principal=principal)
    recorded_at = utc_now()
    signer_name = payload.signer_name.strip()
    signer_display_name = _mask_signer_name(signer_name)
    signer_name_hash = hashlib.sha256(signer_name.encode("utf-8")).hexdigest()
    notes = payload.notes.strip()
    notes_hash = hashlib.sha256(notes.encode("utf-8")).hexdigest() if notes else ""
    resource_id = f"{report.period}:{principal.user.id}:{recorded_at.strftime('%Y%m%d%H%M%S')}"
    signoff_status_label = _customer_report_signoff_status_label(payload.signoff_status)
    confirmation_method_label = _customer_report_signoff_method_label(payload.confirmation_method)

    add_audit_event(
        db,
        tenant_id=tenant_id,
        actor_id=principal.user.id,
        action="customer_quality_report.signoff_recorded",
        resource_type="customer_quality_report_signoff",
        resource_id=resource_id,
        payload={
            "schema_version": CUSTOMER_QUALITY_REPORT_SIGNOFF_SCHEMA_VERSION,
            "report_schema_version": report.schema_version,
            "export_schema_version": CUSTOMER_QUALITY_REPORT_EXPORT_SCHEMA_VERSION,
            "period": report.period,
            "report_status": report.report_status,
            "report_status_label": report.report_status_label,
            "report_confidence_score": report.report_confidence_score,
            "signoff_status": payload.signoff_status,
            "signoff_status_label": signoff_status_label,
            "signer_display_name": signer_display_name,
            "signer_name_sha256": signer_name_hash,
            "signer_role": payload.signer_role.strip(),
            "signer_organization": payload.signer_organization.strip(),
            "confirmation_method": payload.confirmation_method,
            "confirmation_method_label": confirmation_method_label,
            "notes_recorded": bool(notes),
            "notes_sha256": notes_hash,
            "notes_length": len(notes),
            "customer_confirmation_recorded": True,
            "raw_text_included": False,
            "final_answer_text_included": False,
            "reviewer_notes_included": False,
            "signer_name_raw_included": False,
            "electronic_signature_performed": False,
            "formal_contract_signoff_performed": False,
            "model_call_performed": False,
            "external_call_performed": False,
            "external_platform_write_performed": False,
        },
    )
    db.commit()

    return CustomerQualityReportSignoffRead(
        tenant_id=tenant_id,
        schema_version=CUSTOMER_QUALITY_REPORT_SIGNOFF_SCHEMA_VERSION,
        report_schema_version=report.schema_version,
        export_schema_version=CUSTOMER_QUALITY_REPORT_EXPORT_SCHEMA_VERSION,
        period=report.period,
        report_status=report.report_status,
        report_status_label=report.report_status_label,
        report_confidence_score=report.report_confidence_score,
        signoff_status=payload.signoff_status,
        signoff_status_label=signoff_status_label,
        signer_display_name=signer_display_name,
        signer_role=payload.signer_role.strip(),
        signer_organization=payload.signer_organization.strip(),
        confirmation_method=payload.confirmation_method,
        confirmation_method_label=confirmation_method_label,
        notes_recorded=bool(notes),
        notes_hash=notes_hash,
        notes_length=len(notes),
        recorded_at=recorded_at,
        recorded_by_user_id=principal.user.id,
        audit_action="customer_quality_report.signoff_recorded",
        audit_resource_id=resource_id,
        raw_text_included=False,
        final_answer_text_included=False,
        reviewer_notes_included=False,
        signer_name_raw_included=False,
        electronic_signature_performed=False,
        formal_contract_signoff_performed=False,
        model_call_performed=False,
        external_call_performed=False,
        external_platform_write_performed=False,
    )


def _load_audit_payload(event: AuditEvent) -> dict[str, Any]:
    try:
        payload = json.loads(event.payload or "{}")
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def _signoff_list_item_from_audit_event(event: AuditEvent) -> CustomerQualityReportSignoffListItemRead:
    payload = _load_audit_payload(event)
    signoff_status = str(payload.get("signoff_status") or "accepted_with_notes")
    confirmation_method = str(payload.get("confirmation_method") or "local_record")
    notes_length = payload.get("notes_length")
    report_confidence_score = payload.get("report_confidence_score")
    return CustomerQualityReportSignoffListItemRead(
        audit_event_id=event.id,
        tenant_id=event.tenant_id,
        schema_version=str(payload.get("schema_version") or CUSTOMER_QUALITY_REPORT_SIGNOFF_SCHEMA_VERSION),
        report_schema_version=str(payload.get("report_schema_version") or CUSTOMER_QUALITY_REPORT_SCHEMA_VERSION),
        export_schema_version=str(payload.get("export_schema_version") or CUSTOMER_QUALITY_REPORT_EXPORT_SCHEMA_VERSION),
        period=str(payload.get("period") or event.resource_id.split(":", 1)[0] or ""),
        report_status=str(payload.get("report_status") or "unknown"),
        report_status_label=str(payload.get("report_status_label") or "未读取报告状态"),
        report_confidence_score=int(report_confidence_score) if isinstance(report_confidence_score, int) else 0,
        signoff_status=signoff_status,
        signoff_status_label=str(payload.get("signoff_status_label") or _customer_report_signoff_status_label(signoff_status)),
        signer_display_name=str(payload.get("signer_display_name") or ""),
        signer_role=str(payload.get("signer_role") or ""),
        signer_organization=str(payload.get("signer_organization") or ""),
        confirmation_method=confirmation_method,
        confirmation_method_label=str(
            payload.get("confirmation_method_label") or _customer_report_signoff_method_label(confirmation_method)
        ),
        notes_recorded=bool(payload.get("notes_recorded")),
        notes_hash=str(payload.get("notes_sha256") or ""),
        notes_length=int(notes_length) if isinstance(notes_length, int) else 0,
        recorded_at=event.created_at,
        recorded_by_user_id=event.actor_id,
        audit_action=event.action,
        audit_resource_id=event.resource_id,
        raw_text_included=False,
        final_answer_text_included=False,
        reviewer_notes_included=False,
        signer_name_raw_included=False,
        electronic_signature_performed=False,
        formal_contract_signoff_performed=False,
        model_call_performed=False,
        external_call_performed=False,
        external_platform_write_performed=False,
    )


def list_customer_quality_report_signoffs(
    db: Session,
    tenant_id: int,
    *,
    page: int,
    page_size: int,
    period: str | None,
    principal: CurrentPrincipal,
) -> CustomerQualityReportSignoffListRead:
    _require_same_tenant(db, tenant_id, principal)
    conditions = [
        AuditEvent.tenant_id == tenant_id,
        AuditEvent.action == "customer_quality_report.signoff_recorded",
        AuditEvent.resource_type == "customer_quality_report_signoff",
    ]
    if period:
        conditions.append(AuditEvent.resource_id.like(f"{period}:%"))
    total = int(db.scalar(select(func.count(AuditEvent.id)).where(*conditions)) or 0)
    offset = (page - 1) * page_size
    events = db.scalars(
        select(AuditEvent)
        .where(*conditions)
        .order_by(AuditEvent.created_at.desc(), AuditEvent.id.desc())
        .offset(offset)
        .limit(page_size)
    ).all()
    return CustomerQualityReportSignoffListRead(
        tenant_id=tenant_id,
        schema_version=CUSTOMER_QUALITY_REPORT_SIGNOFF_LIST_SCHEMA_VERSION,
        page=page,
        page_size=page_size,
        total=total,
        items=[_signoff_list_item_from_audit_event(event) for event in events],
        raw_text_included=False,
        final_answer_text_included=False,
        reviewer_notes_included=False,
        signer_name_raw_included=False,
        model_call_performed=False,
        external_call_performed=False,
        external_platform_write_performed=False,
    )


def _report_hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:24]


CUSTOMER_SERVICE_QUESTION_BANK_SCHEMA_VERSION = "p3-06u-26h2o.customer_question_bank.v1"
CUSTOMER_BANK_PHONE_RE = re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)")
CUSTOMER_BANK_EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
CUSTOMER_BANK_CN_ID_RE = re.compile(r"(?<!\d)\d{6}(?:19|20)\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])\d{3}[\dXx](?!\d)")


def _question_bank_sensitive_patterns(case: KnowledgeEvaluationCaseCreate) -> list[str]:
    text = " ".join(
        [
            case.external_case_id,
            case.source_channel,
            case.source_category,
            case.question,
            case.question_type,
            case.expected_source_uri,
            case.expected_document_title,
            case.risk_level,
            case.annotation_notes,
            " ".join(case.expected_terms),
            " ".join(case.forbidden_terms),
        ]
    )
    patterns: list[str] = []
    if CUSTOMER_BANK_PHONE_RE.search(text):
        patterns.append("mainland_mobile")
    if CUSTOMER_BANK_EMAIL_RE.search(text):
        patterns.append("email")
    if CUSTOMER_BANK_CN_ID_RE.search(text):
        patterns.append("cn_id")
    return patterns


def _question_bank_count_map(values: list[str], *, fallback: str = "unspecified") -> dict[str, int]:
    counts = Counter((value.strip() or fallback) for value in values)
    return dict(sorted(counts.items(), key=lambda item: (-item[1], item[0])))


def _build_customer_service_question_bank_result(
    tenant_id: int,
    payload: CustomerServiceQuestionBankImportCreate,
    *,
    imported: bool,
    evaluation_set_id: int | None = None,
) -> CustomerServiceQuestionBankPrecheckRead:
    case_count = len(payload.cases)
    validation_errors: list[str] = []
    sensitive_rows: list[dict[str, Any]] = []
    seen_external_ids: set[str] = set()
    duplicate_external_ids: list[str] = []

    if payload.minimum_case_count > payload.maximum_case_count:
        validation_errors.append("minimum_case_count cannot be greater than maximum_case_count")
    if case_count < payload.minimum_case_count:
        validation_errors.append(
            f"case_count_below_minimum: expected at least {payload.minimum_case_count}, got {case_count}"
        )
    if case_count > payload.maximum_case_count:
        validation_errors.append(
            f"case_count_above_maximum: expected at most {payload.maximum_case_count}, got {case_count}"
        )

    for index, case in enumerate(payload.cases, start=1):
        external_case_id = case.external_case_id.strip()
        if external_case_id:
            if external_case_id in seen_external_ids:
                duplicate_external_ids.append(external_case_id)
            seen_external_ids.add(external_case_id)
        patterns = _question_bank_sensitive_patterns(case)
        if patterns:
            sensitive_rows.append(
                {
                    "row": index,
                    "external_case_id_hash": _report_hash_text(external_case_id) if external_case_id else "",
                    "patterns": patterns,
                }
            )
    if duplicate_external_ids:
        validation_errors.append(f"duplicate_external_case_ids: {len(set(duplicate_external_ids))}")
    if sensitive_rows and not payload.allow_sensitive_rows:
        validation_errors.append("sensitive_rows_detected")

    source_channels = [case.source_channel for case in payload.cases]
    source_categories = [case.source_category for case in payload.cases]
    risk_levels = [case.risk_level or "low" for case in payload.cases]
    question_types = [case.question_type or "standard_customer_question" for case in payload.cases]
    expected_terms_cases = sum(1 for case in payload.cases if _clean_string_list(case.expected_terms))
    source_reference_cases = sum(1 for case in payload.cases if case.expected_source_uri.strip())
    handoff_cases = sum(1 for case in payload.cases if case.expected_human_review)
    auto_reply_blocked_cases = sum(1 for case in payload.cases if not case.allow_auto_reply)
    forbidden_term_cases = sum(1 for case in payload.cases if _clean_string_list(case.forbidden_terms))
    business_object_hash_cases = sum(1 for case in payload.cases if "business_object_hash=" in case.annotation_notes)
    expected_answer_hash_cases = sum(1 for case in payload.cases if "expected_answer_hash=" in case.annotation_notes)

    coverage_summary = {
        "schema_version": CUSTOMER_SERVICE_QUESTION_BANK_SCHEMA_VERSION,
        "source_label": payload.source_label.strip(),
        "case_count": case_count,
        "case_count_target": {
            "minimum": payload.minimum_case_count,
            "maximum": payload.maximum_case_count,
            "within_range": payload.minimum_case_count <= case_count <= payload.maximum_case_count,
        },
        "source_channel_counts": _question_bank_count_map(source_channels),
        "source_category_counts": _question_bank_count_map(source_categories),
        "risk_level_counts": _question_bank_count_map(risk_levels, fallback="low"),
        "question_type_counts": _question_bank_count_map(question_types),
        "source_channel_diversity": len({item.strip() for item in source_channels if item.strip()}),
        "source_category_diversity": len({item.strip() for item in source_categories if item.strip()}),
        "expected_terms_covered_cases": expected_terms_cases,
        "expected_terms_coverage": _ratio(expected_terms_cases, case_count),
        "source_reference_covered_cases": source_reference_cases,
        "source_reference_coverage": _ratio(source_reference_cases, case_count),
        "handoff_expected_cases": handoff_cases,
        "handoff_expected_rate": _ratio(handoff_cases, case_count),
        "auto_reply_blocked_cases": auto_reply_blocked_cases,
        "auto_reply_blocked_rate": _ratio(auto_reply_blocked_cases, case_count),
        "forbidden_term_cases": forbidden_term_cases,
        "forbidden_term_coverage": _ratio(forbidden_term_cases, case_count),
        "business_object_hash_cases": business_object_hash_cases,
        "expected_answer_hash_cases": expected_answer_hash_cases,
        "sensitive_row_count": len(sensitive_rows),
        "raw_question_text_included": False,
        "raw_expected_answer_included": False,
        "provider_call_performed": False,
        "external_platform_write_performed": False,
    }
    case_catalog = [
        {
            "row": index,
            "external_case_id": case.external_case_id.strip(),
            "question_hash": _report_hash_text(case.question.strip()),
            "source_channel": case.source_channel.strip(),
            "source_category": case.source_category.strip(),
            "question_type": case.question_type.strip() or "standard_customer_question",
            "risk_level": case.risk_level.strip() or "low",
            "expected_terms_count": len(_clean_string_list(case.expected_terms)),
            "forbidden_terms_count": len(_clean_string_list(case.forbidden_terms)),
            "expected_human_review": case.expected_human_review,
            "allow_auto_reply": case.allow_auto_reply,
            "source_reference_present": bool(case.expected_source_uri.strip()),
            "business_object_hash_present": "business_object_hash=" in case.annotation_notes,
            "expected_answer_hash_present": "expected_answer_hash=" in case.annotation_notes,
        }
        for index, case in enumerate(payload.cases, start=1)
    ]
    can_import = not validation_errors
    status_value = "imported" if imported else ("ready" if can_import else "blocked")
    return CustomerServiceQuestionBankPrecheckRead(
        tenant_id=tenant_id,
        status=status_value,
        can_import=can_import,
        imported=imported,
        evaluation_set_id=evaluation_set_id,
        case_count=case_count,
        coverage_summary=coverage_summary,
        sensitive_rows=sensitive_rows,
        validation_errors=validation_errors,
        case_catalog=case_catalog,
        raw_text_included=False,
        provider_call_performed=False,
        external_write_performed=False,
    )


def precheck_customer_service_question_bank(
    db: Session,
    tenant_id: int,
    payload: CustomerServiceQuestionBankImportCreate,
    principal: CurrentPrincipal,
) -> CustomerServiceQuestionBankPrecheckRead:
    _require_same_tenant(db, tenant_id, principal)
    _require_knowledge_manager(principal)
    return _build_customer_service_question_bank_result(tenant_id, payload, imported=False)


def import_customer_service_question_bank(
    db: Session,
    tenant_id: int,
    payload: CustomerServiceQuestionBankImportCreate,
    principal: CurrentPrincipal,
) -> CustomerServiceQuestionBankPrecheckRead:
    precheck = precheck_customer_service_question_bank(db, tenant_id, payload, principal)
    if not precheck.can_import:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=precheck.model_dump())

    evaluation_set = create_knowledge_evaluation_set(
        db,
        tenant_id,
        KnowledgeEvaluationSetCreate(
            name=payload.name,
            description=payload.description,
            status=payload.status,
            evaluation_mode=payload.evaluation_mode,
            cases=payload.cases,
        ),
        principal,
    )
    result = _build_customer_service_question_bank_result(
        tenant_id,
        payload,
        imported=True,
        evaluation_set_id=evaluation_set.id,
    )
    add_audit_event(
        db,
        tenant_id=tenant_id,
        actor_id=principal.user.id,
        action="customer_service_question_bank.imported",
        resource_type="knowledge_evaluation_set",
        resource_id=str(evaluation_set.id),
        payload={
            "schema_version": CUSTOMER_SERVICE_QUESTION_BANK_SCHEMA_VERSION,
            "evaluation_set_id": evaluation_set.id,
            "case_count": result.case_count,
            "coverage_summary": result.coverage_summary,
            "validation_error_count": len(result.validation_errors),
            "sensitive_row_count": len(result.sensitive_rows),
            "raw_text_included": False,
            "provider_call_performed": False,
            "external_platform_write_performed": False,
        },
    )
    db.commit()
    return result


def _report_bool_text(value: object) -> str:
    if value is None:
        return ""
    return "true" if bool(value) else "false"


def _report_list_text(value: object) -> str:
    if not value:
        return ""
    if isinstance(value, list):
        return ";".join(str(item) for item in value)
    return str(value)


def _report_case_payload(case: KnowledgeEvaluationRunCaseRead) -> dict:
    payload = case.result_payload or {}
    return payload if isinstance(payload, dict) else {}


def _report_top_match(payload: dict) -> dict:
    top_match = payload.get("top_match") or {}
    return top_match if isinstance(top_match, dict) else {}


def _report_is_knowledge_gap(case: KnowledgeEvaluationRunCaseRead, payload: dict) -> bool:
    if case.failure_reason in {"no_retrieval_hit", "no_knowledge_hit"}:
        return True
    if case.status == "no_hit":
        return True
    if not case.top_chunk_id and case.top_confidence <= 0:
        return True
    returned_chunk_ids = payload.get("returned_chunk_ids_top_k")
    return (
        isinstance(returned_chunk_ids, list)
        and not returned_chunk_ids
        and case.failure_reason.startswith("no_")
    )


def _report_case_row(case: KnowledgeEvaluationRunCaseRead) -> dict:
    payload = _report_case_payload(case)
    top_match = _report_top_match(payload)
    return {
        "external_case_id": payload.get("external_case_id") or "",
        "source_channel": payload.get("source_channel") or "",
        "source_category": payload.get("source_category") or "",
        "question_hash": _report_hash_text(case.question or ""),
        "question_type": payload.get("question_type") or "",
        "risk_level": payload.get("risk_level") or "",
        "status": case.status,
        "failure_reason": case.failure_reason,
        "knowledge_gap": _report_bool_text(_report_is_knowledge_gap(case, payload)),
        "top_confidence": case.top_confidence,
        "top_score": case.top_score,
        "top_chunk_id": case.top_chunk_id or "",
        "top_document_id": case.top_document_id or "",
        "citation_present": _report_bool_text(case.citation_present),
        "expected_terms_found": _report_bool_text(case.expected_terms_found),
        "full_evidence_recalled_at_5": _report_bool_text(payload.get("full_evidence_recalled_at_5")),
        "citation_precision": payload.get("citation_precision") if payload.get("citation_precision") is not None else "",
        "expected_human_review": _report_bool_text(payload.get("expected_human_review")),
        "predicted_human_review": _report_bool_text(payload.get("predicted_human_review")),
        "human_review_prediction_correct": _report_bool_text(payload.get("human_review_prediction_correct")),
        "allow_auto_reply": _report_bool_text(payload.get("allow_auto_reply")),
        "forbidden_term_hits": _report_list_text(payload.get("forbidden_term_hits")),
        "expected_chunk_ids": _report_list_text(payload.get("expected_chunk_ids")),
        "returned_chunk_ids_top_k": _report_list_text(payload.get("returned_chunk_ids_top_k")),
        "top_source_uri": top_match.get("source_uri") or "",
        "top_document_title": top_match.get("document_title") or "",
    }


def _report_rows(run: KnowledgeEvaluationRunRead) -> list[dict]:
    return [_report_case_row(case) for case in run.case_results]


def _report_summary(run: KnowledgeEvaluationRunRead, rows: list[dict]) -> dict:
    summary_payload = run.summary_payload if isinstance(run.summary_payload, dict) else {}
    knowledge_gap_cases = sum(1 for row in rows if row.get("knowledge_gap") == "true")
    human_review_correct_cases = sum(
        1 for row in rows if row.get("human_review_prediction_correct") == "true"
    )
    forbidden_hit_cases = sum(1 for row in rows if row.get("forbidden_term_hits"))
    return {
        "run_id": run.id,
        "evaluation_set_id": run.evaluation_set_id,
        "run_mode": run.run_mode,
        "retrieval_mode": run.retrieval_mode,
        "vector_engine": run.vector_engine,
        "total_cases": run.total_cases,
        "answered_cases": run.answered_cases,
        "no_hit_cases": run.no_hit_cases,
        "passed_cases": run.passed_cases,
        "failed_cases": run.failed_cases,
        "needs_review_cases": run.needs_review_cases,
        "hit_rate": run.hit_rate,
        "citation_coverage": run.citation_coverage,
        "expected_term_coverage": run.expected_term_coverage,
        "average_confidence": run.average_confidence,
        "full_evidence_recall_at_5": summary_payload.get("full_evidence_recall_at_5"),
        "citation_precision": summary_payload.get("citation_precision"),
        "human_review_correctness": summary_payload.get("human_review_correctness"),
        "handoff_correctness": summary_payload.get("handoff_correctness"),
        "knowledge_gap_rate": summary_payload.get("knowledge_gap_rate"),
        "knowledge_gap_cases": knowledge_gap_cases,
        "human_review_correct_cases": human_review_correct_cases,
        "forbidden_term_hits": summary_payload.get("forbidden_term_hits", 0),
        "citation_sufficiency_rate": summary_payload.get("citation_sufficiency_rate"),
        "citation_sufficient_cases": summary_payload.get("citation_sufficient_cases", 0),
        "forbidden_commitment_violation_rate": summary_payload.get("forbidden_commitment_violation_rate"),
        "forbidden_commitment_violation_cases": summary_payload.get("forbidden_commitment_violation_cases", 0),
        "final_answer_factuality_measured": summary_payload.get("final_answer_factuality_measured"),
        "final_answer_factuality_rate": summary_payload.get("final_answer_factuality_rate"),
        "final_answer_factuality_note": summary_payload.get("final_answer_factuality_note"),
        "answer_quality_metrics_version": summary_payload.get("answer_quality_metrics_version") or "",
        "forbidden_hit_cases": forbidden_hit_cases,
        "unsupported_answer_rate": run.unsupported_answer_rate,
        "unsupported_answer_rate_measured": summary_payload.get("unsupported_answer_rate_measured"),
        "customer_service_metrics_version": summary_payload.get("customer_service_metrics_version") or "",
    }


def _report_percent(value: object) -> str:
    if value is None or value == "":
        return "-"
    try:
        return f"{float(value) * 100:.1f}%"
    except (TypeError, ValueError):
        return str(value)


def _markdown_cell(value: object) -> str:
    text_value = "" if value is None else str(value)
    return text_value.replace("|", "\\|").replace("\n", " ")


def _markdown_table(headers: list[str], rows: list[list[object]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(_markdown_cell(item) for item in row) + " |")
    return "\n".join(lines)


def _report_csv_body(rows: list[dict]) -> str:
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=REPORT_CSV_FIELDS_REDACTED)
    writer.writeheader()
    for row in rows:
        writer.writerow({field: row.get(field, "") for field in REPORT_CSV_FIELDS_REDACTED})
    return output.getvalue()


def _report_markdown_body(summary: dict, rows: list[dict]) -> str:
    lines = [
        "# 客服知识检索评测复盘报告",
        "",
        "## 安全边界",
        "",
        "- raw_text_included=false",
        "- provider_call_performed=false",
        "- external_write_performed=false",
        "- 本报告只导出 question_hash、来源元数据和可计算指标，不导出原始问题或命中知识片段原文。",
        "- 当前仍只评测检索证据和人工审核门禁，不生成自由文本答案，因此不把幻觉率记为 0。",
        "",
        "## 运行摘要",
        "",
        _markdown_table(
            ["指标", "值"],
            [
                ["run_id", summary["run_id"]],
                ["evaluation_set_id", summary["evaluation_set_id"]],
                ["run_mode", summary["run_mode"]],
                ["retrieval_mode", summary["retrieval_mode"]],
                ["vector_engine", summary["vector_engine"]],
                ["total_cases", summary["total_cases"]],
                ["passed_cases", summary["passed_cases"]],
                ["needs_review_cases", summary["needs_review_cases"]],
                ["knowledge_gap_cases", summary["knowledge_gap_cases"]],
                ["human_review_correct_cases", summary["human_review_correct_cases"]],
            ],
        ),
        "",
        "## 质量指标",
        "",
        _markdown_table(
            ["指标", "值"],
            [
                ["hit_rate", _report_percent(summary["hit_rate"])],
                ["citation_coverage", _report_percent(summary["citation_coverage"])],
                ["expected_term_coverage", _report_percent(summary["expected_term_coverage"])],
                ["average_confidence", summary["average_confidence"]],
                ["full_evidence_recall_at_5", _report_percent(summary["full_evidence_recall_at_5"])],
                ["citation_precision", _report_percent(summary["citation_precision"])],
                ["citation_sufficiency_rate", _report_percent(summary["citation_sufficiency_rate"])],
                ["human_review_correctness", _report_percent(summary["human_review_correctness"])],
                ["handoff_correctness", _report_percent(summary["handoff_correctness"])],
                ["knowledge_gap_rate", _report_percent(summary["knowledge_gap_rate"])],
                ["forbidden_term_hits", summary["forbidden_term_hits"]],
                ["forbidden_commitment_violation_rate", _report_percent(summary["forbidden_commitment_violation_rate"])],
                ["final_answer_factuality_measured", summary["final_answer_factuality_measured"]],
                ["final_answer_factuality_rate", _report_percent(summary["final_answer_factuality_rate"])],
                ["answer_quality_metrics_version", summary["answer_quality_metrics_version"]],
                ["unsupported_answer_rate", summary["unsupported_answer_rate"]],
            ],
        ),
        "",
        "## 逐题脱敏结果",
        "",
    ]
    if not rows:
        lines.append("当前运行没有逐题结果。")
    else:
        headers = [
            "external_case_id",
            "question_hash",
            "source_channel",
            "source_category",
            "status",
            "failure_reason",
            "knowledge_gap",
            "expected_human_review",
            "predicted_human_review",
        ]
        table_rows = [[row.get(header, "") for header in headers] for row in rows]
        lines.append(_markdown_table(headers, table_rows))
    return "\n".join(lines) + "\n"


def _knowledge_gap_read(gap: KnowledgeGapItem) -> KnowledgeGapRead:
    return KnowledgeGapRead.model_validate(gap)


def _gap_severity_from_human_review(task: HumanReviewTask, state: dict, threshold: float) -> str:
    risk_level = (task.risk_level or state.get("risk_level") or "medium").strip().lower()
    confidence = _safe_float(state.get("confidence"), 0.0)
    retrieved_count = _safe_int(state.get("retrieved_knowledge_count"), 0)
    if risk_level == "critical":
        return "critical"
    if risk_level == "high" or confidence < 0.25:
        return "high"
    if retrieved_count == 0 or confidence < threshold:
        return "medium"
    return "low"


def _gap_severity_from_evaluation_case(run_case: KnowledgeEvaluationRunCase, threshold: float) -> str:
    reason = (run_case.failure_reason or "").strip()
    if reason in {"expected_evidence_missing", "no_hit"}:
        return "high"
    if run_case.top_confidence < min(threshold, 0.35):
        return "high"
    if reason in {"expected_terms_missing", "citation_missing", "no_citation", "low_confidence"}:
        return "medium"
    return "low"


def _existing_knowledge_gap(
    db: Session,
    *,
    tenant_id: int,
    source_type: str,
    source_ref: str,
) -> KnowledgeGapItem | None:
    return db.scalar(
        select(KnowledgeGapItem).where(
            KnowledgeGapItem.tenant_id == tenant_id,
            KnowledgeGapItem.source_type == source_type,
            KnowledgeGapItem.source_ref == source_ref,
        )
    )


def _create_or_reuse_gap(
    db: Session,
    *,
    tenant_id: int,
    source_type: str,
    source_ref: str,
    source_title: str,
    source_excerpt: str,
    question_excerpt: str,
    gap_type: str,
    severity: str,
    expected_terms: list[str],
    evidence_payload: dict,
    principal: CurrentPrincipal,
) -> tuple[KnowledgeGapItem, bool]:
    existing = _existing_knowledge_gap(
        db,
        tenant_id=tenant_id,
        source_type=source_type,
        source_ref=source_ref,
    )
    if existing is not None:
        return existing, False

    now = utc_now()
    gap = KnowledgeGapItem(
        tenant_id=tenant_id,
        status="open",
        severity=severity,
        source_type=source_type,
        source_ref=source_ref,
        source_title=_short_excerpt(source_title, limit=180),
        source_excerpt=_short_excerpt(source_excerpt, limit=360),
        question_excerpt=_short_excerpt(question_excerpt, limit=360),
        gap_type=gap_type,
        expected_terms=_clean_string_list(expected_terms),
        evidence_payload=evidence_payload,
        created_by_id=principal.user.id,
        updated_by_id=principal.user.id,
        created_at=now,
        updated_at=now,
    )
    db.add(gap)
    db.flush()
    return gap, True


def _human_review_task_should_create_gap(task: HumanReviewTask, state: dict, threshold: float) -> bool:
    reason = (task.reason or "").strip().lower()
    confidence = _safe_float(state.get("confidence"), 1.0)
    retrieved_count = _safe_int(state.get("retrieved_knowledge_count"), 0)
    return (
        task.status in {"open", "assigned", "pending"}
        and (
            reason in HUMAN_REVIEW_KNOWLEDGE_GAP_REASONS
            or retrieved_count == 0
            or confidence < threshold
        )
    )


def _knowledge_gap_from_human_review(
    db: Session,
    *,
    tenant_id: int,
    task: HumanReviewTask,
    threshold: float,
    principal: CurrentPrincipal,
) -> tuple[KnowledgeGapItem, bool] | None:
    workflow_run = task.workflow_run
    state = workflow_run.state_payload if workflow_run is not None else {}
    if not isinstance(state, dict) or not _human_review_task_should_create_gap(task, state, threshold):
        return None

    message = db.get(Message, task.message_id) if task.message_id else None
    confidence = _safe_float(state.get("confidence"), 0.0)
    retrieved_count = _safe_int(state.get("retrieved_knowledge_count"), 0)
    if retrieved_count == 0:
        gap_type = "no_knowledge_hit"
    elif confidence < threshold:
        gap_type = "low_confidence"
    else:
        gap_type = (task.reason or "human_review").strip().lower()

    question_excerpt = _short_excerpt(message.content if message is not None else task.draft_reply)
    source_excerpt = _short_excerpt(task.draft_reply or question_excerpt)
    knowledge_matches = state.get("knowledge_matches") if isinstance(state.get("knowledge_matches"), list) else []
    evidence_payload = {
        "human_review_task_id": task.id,
        "workflow_run_id": task.workflow_run_id,
        "conversation_id": task.conversation_id,
        "message_id": task.message_id,
        "reason": task.reason,
        "risk_level": task.risk_level,
        "confidence": confidence,
        "retrieved_knowledge_count": retrieved_count,
        "retrieval_mode": state.get("retrieval_mode") or "",
        "retrieval_engine": state.get("retrieval_engine") or "",
        "knowledge_match_count": len(knowledge_matches),
    }
    return _create_or_reuse_gap(
        db,
        tenant_id=tenant_id,
        source_type="human_review",
        source_ref=f"human_review_task:{task.id}",
        source_title=f"人审任务 #{task.id} · {task.reason or gap_type}",
        source_excerpt=source_excerpt,
        question_excerpt=question_excerpt,
        gap_type=gap_type,
        severity=_gap_severity_from_human_review(task, state, threshold),
        expected_terms=[],
        evidence_payload=evidence_payload,
        principal=principal,
    )


def _evaluation_case_should_create_gap(run_case: KnowledgeEvaluationRunCase, threshold: float) -> bool:
    reason = (run_case.failure_reason or "").strip().lower()
    payload = run_case.result_payload if isinstance(run_case.result_payload, dict) else {}
    return (
        payload.get("knowledge_gap") is True
        or reason in EVALUATION_KNOWLEDGE_GAP_REASONS
        or (run_case.status == "failed" and run_case.top_confidence < threshold)
    )


def _knowledge_gap_from_evaluation_case(
    db: Session,
    *,
    tenant_id: int,
    run_case: KnowledgeEvaluationRunCase,
    threshold: float,
    principal: CurrentPrincipal,
) -> tuple[KnowledgeGapItem, bool] | None:
    if not _evaluation_case_should_create_gap(run_case, threshold):
        return None

    evaluation_case = db.get(KnowledgeEvaluationCase, run_case.evaluation_case_id)
    payload = run_case.result_payload if isinstance(run_case.result_payload, dict) else {}
    reason = (run_case.failure_reason or run_case.status or "evaluation_failed").strip().lower()
    expected_terms = evaluation_case.expected_terms if evaluation_case is not None else []
    evidence_payload = {
        "evaluation_run_id": run_case.evaluation_run_id,
        "evaluation_case_id": run_case.evaluation_case_id,
        "run_case_id": run_case.id,
        "status": run_case.status,
        "failure_reason": run_case.failure_reason,
        "top_confidence": run_case.top_confidence,
        "top_score": run_case.top_score,
        "top_chunk_id": run_case.top_chunk_id,
        "top_document_id": run_case.top_document_id,
        "expected_source_uri": evaluation_case.expected_source_uri if evaluation_case is not None else "",
        "source_channel": getattr(evaluation_case, "source_channel", "") if evaluation_case is not None else "",
        "source_category": getattr(evaluation_case, "source_category", "") if evaluation_case is not None else "",
        "retrieval_mode": payload.get("retrieval_mode") or "",
    }
    return _create_or_reuse_gap(
        db,
        tenant_id=tenant_id,
        source_type="evaluation_run",
        source_ref=f"knowledge_evaluation_run_case:{run_case.id}",
        source_title=f"知识评测失败 #{run_case.id} · {reason}",
        source_excerpt=run_case.failure_reason or run_case.status,
        question_excerpt=run_case.question,
        gap_type=reason,
        severity=_gap_severity_from_evaluation_case(run_case, threshold),
        expected_terms=expected_terms or [],
        evidence_payload=evidence_payload,
        principal=principal,
    )


def list_knowledge_gaps(
    db: Session,
    tenant_id: int,
    *,
    status_filter: str | None,
    severity_filter: str | None,
    source_type: str | None,
    query: str | None,
    page: int,
    page_size: int,
    principal: CurrentPrincipal,
) -> KnowledgeGapList:
    _require_same_tenant(db, tenant_id, principal)
    _require_knowledge_manager(principal)
    filters = [KnowledgeGapItem.tenant_id == tenant_id]
    if status_filter:
        filters.append(KnowledgeGapItem.status == status_filter)
    if severity_filter:
        filters.append(KnowledgeGapItem.severity == severity_filter)
    if source_type:
        filters.append(KnowledgeGapItem.source_type == source_type)
    normalized_query = (query or "").strip()
    if normalized_query:
        keyword = f"%{normalized_query.lower()}%"
        filters.append(
            or_(
                func.lower(KnowledgeGapItem.source_title).like(keyword),
                func.lower(KnowledgeGapItem.source_excerpt).like(keyword),
                func.lower(KnowledgeGapItem.question_excerpt).like(keyword),
                func.lower(KnowledgeGapItem.gap_type).like(keyword),
                func.lower(KnowledgeGapItem.severity).like(keyword),
                func.lower(KnowledgeGapItem.status).like(keyword),
                func.lower(KnowledgeGapItem.source_type).like(keyword),
                func.lower(KnowledgeGapItem.resolution_note).like(keyword),
                func.lower(cast(KnowledgeGapItem.expected_terms, String)).like(keyword),
            )
        )

    total = int(db.scalar(select(func.count(KnowledgeGapItem.id)).where(*filters)) or 0)
    items = list(
        db.scalars(
            select(KnowledgeGapItem)
            .where(*filters)
            .order_by(KnowledgeGapItem.updated_at.desc(), KnowledgeGapItem.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()
    )
    return KnowledgeGapList(
        items=[_knowledge_gap_read(item) for item in items],
        page=page,
        page_size=page_size,
        total=total,
    )


def sync_knowledge_gaps(
    db: Session,
    tenant_id: int,
    payload: KnowledgeGapSyncCreate,
    principal: CurrentPrincipal,
) -> KnowledgeGapSyncRead:
    _require_same_tenant(db, tenant_id, principal)
    _require_knowledge_manager(principal)
    created_count = 0
    existing_count = 0
    scanned_count = 0
    collected: list[KnowledgeGapItem] = []

    if payload.include_human_review and len(collected) < payload.max_items:
        tasks = list(
            db.scalars(
                select(HumanReviewTask)
                .where(HumanReviewTask.tenant_id == tenant_id)
                .order_by(HumanReviewTask.created_at.desc(), HumanReviewTask.id.desc())
                .limit(payload.max_items * 3)
            ).all()
        )
        for task in tasks:
            if len(collected) >= payload.max_items:
                break
            candidate = _knowledge_gap_from_human_review(
                db,
                tenant_id=tenant_id,
                task=task,
                threshold=payload.low_confidence_threshold,
                principal=principal,
            )
            if candidate is None:
                continue
            gap, created = candidate
            scanned_count += 1
            collected.append(gap)
            if created:
                created_count += 1
            else:
                existing_count += 1

    if payload.include_evaluation_runs and len(collected) < payload.max_items:
        query = select(KnowledgeEvaluationRunCase).where(KnowledgeEvaluationRunCase.tenant_id == tenant_id)
        if payload.evaluation_run_id is not None:
            evaluation_run = db.get(KnowledgeEvaluationRun, payload.evaluation_run_id)
            if evaluation_run is None or evaluation_run.tenant_id != tenant_id:
                raise HTTPException(status_code=404, detail="knowledge evaluation run not found")
            query = query.where(KnowledgeEvaluationRunCase.evaluation_run_id == payload.evaluation_run_id)
        run_cases = list(
            db.scalars(
                query.order_by(KnowledgeEvaluationRunCase.created_at.desc(), KnowledgeEvaluationRunCase.id.desc())
                .limit(payload.max_items * 3)
            ).all()
        )
        for run_case in run_cases:
            if len(collected) >= payload.max_items:
                break
            candidate = _knowledge_gap_from_evaluation_case(
                db,
                tenant_id=tenant_id,
                run_case=run_case,
                threshold=payload.low_confidence_threshold,
                principal=principal,
            )
            if candidate is None:
                continue
            gap, created = candidate
            scanned_count += 1
            collected.append(gap)
            if created:
                created_count += 1
            else:
                existing_count += 1

    add_audit_event(
        db,
        tenant_id=tenant_id,
        actor_id=principal.user.id,
        action="knowledge_gap.sync",
        resource_type="knowledge_gap",
        resource_id="batch",
        payload={
            "created_count": created_count,
            "existing_count": existing_count,
            "scanned_count": scanned_count,
            "include_human_review": payload.include_human_review,
            "include_evaluation_runs": payload.include_evaluation_runs,
            "evaluation_run_id": payload.evaluation_run_id,
        },
    )
    db.commit()
    for gap in collected:
        db.refresh(gap)
    return KnowledgeGapSyncRead(
        created_count=created_count,
        existing_count=existing_count,
        scanned_count=scanned_count,
        items=[_knowledge_gap_read(gap) for gap in collected],
    )


def create_knowledge_gap_from_reply_decision(
    db: Session,
    *,
    decision: ReplyDecision,
    message: Message,
    principal: CurrentPrincipal,
) -> tuple[KnowledgeGapItem, bool]:
    if decision.tenant_id != principal.tenant.id or message.id != decision.message_id:
        raise HTTPException(status_code=404, detail="reply decision not found")
    if decision.state != "knowledge_gap":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="reply decision is not a knowledge gap")

    if decision.reason == "no_business_object_match":
        gap_type = "missing_business_object"
        severity = "medium"
    elif decision.reason == "object_matched_no_confident_card":
        gap_type = "missing_object_knowledge_card"
        severity = "high" if decision.confidence < 0.25 else "medium"
    else:
        gap_type = decision.reason or "reply_decision_knowledge_gap"
        severity = "medium"

    decision_note = ""
    if isinstance(decision.decision_payload, dict):
        decision_note = str(decision.decision_payload.get("decision_note") or "")
    gap, created = _create_or_reuse_gap(
        db,
        tenant_id=decision.tenant_id,
        source_type="reply_decision",
        source_ref=f"reply_decision:{decision.id}",
        source_title=f"回复决策 #{decision.id} · {decision.reason}",
        source_excerpt=decision_note,
        question_excerpt=message.content,
        gap_type=gap_type,
        severity=severity,
        expected_terms=decision.matched_terms,
        evidence_payload={
            "reply_decision_id": decision.id,
            "conversation_id": decision.conversation_id,
            "message_id": decision.message_id,
            "channel_id": decision.channel_id,
            "business_object_id": decision.business_object_id,
            "object_knowledge_card_id": decision.object_knowledge_card_id,
            "state": decision.state,
            "reason": decision.reason,
            "confidence": decision.confidence,
            "matched_terms": decision.matched_terms,
            "decision_payload": decision.decision_payload,
        },
        principal=principal,
    )
    add_audit_event(
        db,
        tenant_id=decision.tenant_id,
        actor_id=principal.user.id,
        action="knowledge_gap.created_from_reply_decision" if created else "knowledge_gap.reused_from_reply_decision",
        resource_type="knowledge_gap",
        resource_id=str(gap.id),
        payload={
            "reply_decision_id": decision.id,
            "message_id": decision.message_id,
            "conversation_id": decision.conversation_id,
            "gap_type": gap_type,
            "created": created,
        },
    )
    db.commit()
    db.refresh(gap)
    return gap, created


def update_knowledge_gap(
    db: Session,
    gap_id: int,
    payload: KnowledgeGapUpdate,
    principal: CurrentPrincipal,
) -> KnowledgeGapRead:
    _require_knowledge_manager(principal)
    gap = db.get(KnowledgeGapItem, gap_id)
    if gap is None or gap.tenant_id != principal.tenant.id:
        raise HTTPException(status_code=404, detail="knowledge gap not found")

    changed: dict[str, object] = {}
    fields_set = payload.model_fields_set
    if "status" in fields_set and payload.status is not None:
        gap.status = payload.status
        changed["status"] = payload.status
        if payload.status in KNOWLEDGE_GAP_RESOLUTION_STATUSES:
            gap.resolved_at = utc_now()
            gap.resolved_by_id = principal.user.id
        else:
            gap.resolved_at = None
            gap.resolved_by_id = None
    if "severity" in fields_set and payload.severity is not None:
        gap.severity = payload.severity
        changed["severity"] = payload.severity
    if "assigned_user_id" in fields_set:
        if payload.assigned_user_id is not None:
            user = db.get(User, payload.assigned_user_id)
            if user is None or user.tenant_id != gap.tenant_id:
                raise HTTPException(status_code=404, detail="assigned user not found")
        gap.assigned_user_id = payload.assigned_user_id
        changed["assigned_user_id"] = payload.assigned_user_id
    if "linked_knowledge_card_id" in fields_set:
        if payload.linked_knowledge_card_id is not None:
            card = db.get(KnowledgeCard, payload.linked_knowledge_card_id)
            if card is None or card.tenant_id != gap.tenant_id:
                raise HTTPException(status_code=404, detail="knowledge card not found")
        gap.linked_knowledge_card_id = payload.linked_knowledge_card_id
        changed["linked_knowledge_card_id"] = payload.linked_knowledge_card_id
    if "linked_knowledge_document_id" in fields_set:
        if payload.linked_knowledge_document_id is not None:
            document = db.get(KnowledgeDocument, payload.linked_knowledge_document_id)
            if document is None or document.tenant_id != gap.tenant_id:
                raise HTTPException(status_code=404, detail="knowledge document not found")
        gap.linked_knowledge_document_id = payload.linked_knowledge_document_id
        changed["linked_knowledge_document_id"] = payload.linked_knowledge_document_id
    if "resolution_note" in fields_set and payload.resolution_note is not None:
        gap.resolution_note = payload.resolution_note.strip()
        changed["resolution_note_set"] = bool(gap.resolution_note)

    gap.updated_by_id = principal.user.id
    gap.updated_at = utc_now()
    add_audit_event(
        db,
        tenant_id=gap.tenant_id,
        actor_id=principal.user.id,
        action="knowledge_gap.updated",
        resource_type="knowledge_gap",
        resource_id=str(gap.id),
        payload=changed,
    )
    db.commit()
    db.refresh(gap)
    return _knowledge_gap_read(gap)


def _knowledge_gap_or_404(db: Session, gap_id: int, principal: CurrentPrincipal) -> KnowledgeGapItem:
    _require_knowledge_manager(principal)
    gap = db.get(KnowledgeGapItem, gap_id)
    if gap is None or gap.tenant_id != principal.tenant.id:
        raise HTTPException(status_code=404, detail="knowledge gap not found")
    return gap


def _knowledge_gap_draft_title(gap: KnowledgeGapItem) -> str:
    title_seed = gap.source_title or gap.question_excerpt or gap.gap_type or f"知识缺口 #{gap.id}"
    return _short_excerpt(f"知识缺口补充草稿：{title_seed}", limit=180)


def _knowledge_gap_draft_text(gap: KnowledgeGapItem) -> str:
    expected_terms = _clean_string_list(gap.expected_terms if isinstance(gap.expected_terms, list) else [])
    evidence = gap.evidence_payload if isinstance(gap.evidence_payload, dict) else {}
    expected_source_uri = str(evidence.get("expected_source_uri") or "").strip()
    source_channel = str(evidence.get("source_channel") or "").strip()
    source_category = str(evidence.get("source_category") or "").strip()
    lines = [
        f"# {_knowledge_gap_draft_title(gap)}",
        "",
        "## 客户问题",
        gap.question_excerpt or "待补充客户问题原文。",
        "",
        "## 当前缺口",
        gap.source_excerpt or gap.gap_type or "当前知识库没有给出可直接引用的明确口径。",
        "",
        "## 建议补充口径",
        "请业务负责人在发布前补齐以下内容：",
        "1. 明确适用条件、限制条件和例外情况。",
        "2. 给出客服可直接引用的标准答复，不承诺未确认结果。",
        "3. 如涉及退款、赔付、合同、隐私、投诉或强合规事项，标明是否必须转人工确认。",
        "",
        "## 回答边界",
        "未完成业务审核前，本草稿只用于知识库维护，不进入正式自动回复。",
        "",
        "## 来源线索",
        f"- 缺口编号：{gap.id}",
        f"- 来源类型：{gap.source_type}",
        f"- 来源引用：{gap.source_ref}",
        f"- 缺口类型：{gap.gap_type or '未标注'}",
        f"- 严重度：{gap.severity}",
    ]
    if expected_terms:
        lines.append(f"- 期望覆盖词：{'、'.join(expected_terms)}")
    if expected_source_uri:
        lines.append(f"- 期望来源：{expected_source_uri}")
    if source_channel:
        lines.append(f"- 来源渠道：{source_channel}")
    if source_category:
        lines.append(f"- 来源分类：{source_category}")
    return "\n".join(lines).strip()


def _knowledge_gap_tags(gap: KnowledgeGapItem) -> list[str]:
    tags = ["知识缺口", gap.source_type, gap.gap_type, gap.severity]
    return _clean_string_list([tag for tag in tags if tag])


def _merge_gap_remediation_payload(gap: KnowledgeGapItem, remediation: dict) -> dict:
    payload = gap.evidence_payload if isinstance(gap.evidence_payload, dict) else {}
    next_payload = dict(payload)
    next_payload["remediation"] = {
        **(next_payload.get("remediation") if isinstance(next_payload.get("remediation"), dict) else {}),
        **remediation,
    }
    return next_payload


def _mark_gap_in_progress(gap: KnowledgeGapItem, principal: CurrentPrincipal, resolution_note: str) -> None:
    gap.status = "in_progress"
    if gap.assigned_user_id is None:
        gap.assigned_user_id = principal.user.id
    gap.resolved_at = None
    gap.resolved_by_id = None
    gap.resolution_note = resolution_note
    gap.updated_by_id = principal.user.id
    gap.updated_at = utc_now()


def create_knowledge_gap_document_draft(
    db: Session,
    gap_id: int,
    principal: CurrentPrincipal,
) -> KnowledgeGapDocumentDraftRead:
    gap = _knowledge_gap_or_404(db, gap_id, principal)
    draft_text = _knowledge_gap_draft_text(gap)
    created = False
    document: KnowledgeDocument | None = None
    if gap.linked_knowledge_document_id is not None:
        linked_document = db.get(KnowledgeDocument, gap.linked_knowledge_document_id)
        if linked_document is not None and linked_document.tenant_id == gap.tenant_id:
            document = linked_document
            draft_text = linked_document.raw_text

    if document is None:
        document = create_knowledge_document(
            db,
            gap.tenant_id,
            KnowledgeDocumentCreate(
                title=_knowledge_gap_draft_title(gap),
                source_type="knowledge_gap_remediation",
                source_uri=f"knowledge-gap:{gap.id}",
                raw_text=draft_text,
                tags=_knowledge_gap_tags(gap),
                status="draft",
                chunk_size=900,
                chunk_overlap=120,
            ),
            principal,
        )
        created = True

    gap.linked_knowledge_document_id = document.id
    gap.evidence_payload = _merge_gap_remediation_payload(
        gap,
        {
            "draft_document_id": document.id,
            "draft_document_source_uri": document.source_uri,
            "draft_document_created": created,
            "draft_document_status": document.status,
        },
    )
    _mark_gap_in_progress(gap, principal, f"已生成知识文档草稿 #{document.id}，待业务审核后启用。")
    add_audit_event(
        db,
        tenant_id=gap.tenant_id,
        actor_id=principal.user.id,
        action="knowledge_gap.document_draft_created" if created else "knowledge_gap.document_draft_reused",
        resource_type="knowledge_gap",
        resource_id=str(gap.id),
        payload={
            "document_id": document.id,
            "document_status": document.status,
            "external_write_performed": False,
            "auto_publish_performed": False,
        },
    )
    db.commit()
    db.refresh(gap)
    db.refresh(document)
    return KnowledgeGapDocumentDraftRead(
        gap=_knowledge_gap_read(gap),
        document=document,
        created=created,
        draft_text=draft_text,
    )


def _gap_regression_set(db: Session, gap: KnowledgeGapItem, principal: CurrentPrincipal) -> KnowledgeEvaluationSet:
    now = utc_now()
    evaluation_set = db.scalar(
        select(KnowledgeEvaluationSet).where(
            KnowledgeEvaluationSet.tenant_id == gap.tenant_id,
            KnowledgeEvaluationSet.name == KNOWLEDGE_GAP_REMEDIATION_SET_NAME,
        )
    )
    if evaluation_set is not None:
        if evaluation_set.status != "active":
            evaluation_set.status = "active"
            evaluation_set.updated_by_id = principal.user.id
            evaluation_set.updated_at = now
        return evaluation_set

    evaluation_set = KnowledgeEvaluationSet(
        tenant_id=gap.tenant_id,
        name=KNOWLEDGE_GAP_REMEDIATION_SET_NAME,
        description="由知识缺口闭环自动沉淀的客服检索回归题库。每条题目都应在补齐知识文档后重新运行，验证命中、引用和期望词覆盖。",
        status="active",
        evaluation_mode="customer_service_retrieval",
        created_by_id=principal.user.id,
        updated_by_id=principal.user.id,
        created_at=now,
        updated_at=now,
    )
    db.add(evaluation_set)
    db.flush()
    return evaluation_set


def _gap_regression_priority(gap: KnowledgeGapItem) -> int:
    if gap.severity == "critical":
        return 10
    if gap.severity == "high":
        return 20
    if gap.severity == "medium":
        return 80
    return 120


def _gap_regression_case(
    db: Session,
    gap: KnowledgeGapItem,
    evaluation_set: KnowledgeEvaluationSet,
    principal: CurrentPrincipal,
) -> tuple[KnowledgeEvaluationCase, bool]:
    external_case_id = f"knowledge-gap-{gap.id}"
    existing = db.scalar(
        select(KnowledgeEvaluationCase).where(
            KnowledgeEvaluationCase.tenant_id == gap.tenant_id,
            KnowledgeEvaluationCase.evaluation_set_id == evaluation_set.id,
            KnowledgeEvaluationCase.external_case_id == external_case_id,
        )
    )
    if existing is not None:
        return existing, False

    evidence = gap.evidence_payload if isinstance(gap.evidence_payload, dict) else {}
    linked_document = (
        db.get(KnowledgeDocument, gap.linked_knowledge_document_id)
        if gap.linked_knowledge_document_id is not None
        else None
    )
    expected_source_uri = str(evidence.get("expected_source_uri") or "").strip()
    if not expected_source_uri and linked_document is not None and linked_document.tenant_id == gap.tenant_id:
        expected_source_uri = linked_document.source_uri
    expected_document_title = ""
    if linked_document is not None and linked_document.tenant_id == gap.tenant_id:
        expected_document_title = linked_document.title
    risk_level = gap.severity if gap.severity in {"low", "medium", "high", "critical"} else "medium"
    case = KnowledgeEvaluationCase(
        tenant_id=gap.tenant_id,
        evaluation_set_id=evaluation_set.id,
        external_case_id=external_case_id,
        source_channel=str(evidence.get("source_channel") or "").strip(),
        source_category=str(evidence.get("source_category") or gap.gap_type or "知识缺口").strip(),
        question=gap.question_excerpt or gap.source_excerpt or f"知识缺口 #{gap.id}",
        question_type="knowledge_gap_regression",
        expected_terms=_clean_string_list(gap.expected_terms if isinstance(gap.expected_terms, list) else []),
        expected_source_uri=expected_source_uri,
        expected_document_title=expected_document_title,
        expected_chunk_ids=[],
        must_have_all_evidence=False,
        expected_human_review=bool(evidence.get("expected_human_review") is True),
        allow_auto_reply=not bool(evidence.get("allow_auto_reply") is False),
        forbidden_terms=[],
        risk_level=risk_level,
        annotation_notes=f"由知识缺口 #{gap.id} 自动生成；来源 {gap.source_type}:{gap.source_ref}；补齐知识后需重新运行回归。",
        required_citation=True,
        priority=_gap_regression_priority(gap),
        status="active",
        created_at=utc_now(),
    )
    db.add(case)
    db.flush()
    return case, True


def create_knowledge_gap_regression_case(
    db: Session,
    gap_id: int,
    principal: CurrentPrincipal,
) -> KnowledgeGapRegressionCaseRead:
    gap = _knowledge_gap_or_404(db, gap_id, principal)
    evaluation_set = _gap_regression_set(db, gap, principal)
    evaluation_case, created = _gap_regression_case(db, gap, evaluation_set, principal)
    gap.evidence_payload = _merge_gap_remediation_payload(
        gap,
        {
            "regression_evaluation_set_id": evaluation_set.id,
            "regression_evaluation_case_id": evaluation_case.id,
            "regression_case_created": created,
            "regression_case_status": evaluation_case.status,
        },
    )
    _mark_gap_in_progress(gap, principal, f"已加入知识缺口回归题库 #{evaluation_set.id} / 题目 #{evaluation_case.id}，等待补知识后复测。")
    add_audit_event(
        db,
        tenant_id=gap.tenant_id,
        actor_id=principal.user.id,
        action="knowledge_gap.regression_case_created" if created else "knowledge_gap.regression_case_reused",
        resource_type="knowledge_gap",
        resource_id=str(gap.id),
        payload={
            "evaluation_set_id": evaluation_set.id,
            "evaluation_case_id": evaluation_case.id,
            "external_write_performed": False,
        },
    )
    db.commit()
    db.refresh(gap)
    db.refresh(evaluation_set)
    db.refresh(evaluation_case)
    return KnowledgeGapRegressionCaseRead(
        gap=_knowledge_gap_read(gap),
        evaluation_set=_evaluation_set_read(db, evaluation_set),
        evaluation_case=KnowledgeEvaluationCaseRead.model_validate(evaluation_case),
        created=created,
    )


def _knowledge_document_or_404(db: Session, document_id: int, principal: CurrentPrincipal) -> KnowledgeDocument:
    _require_knowledge_manager(principal)
    document = db.get(KnowledgeDocument, document_id)
    if document is None or document.tenant_id != principal.tenant.id:
        raise HTTPException(status_code=404, detail="knowledge document not found")
    return document


def _linked_gap_for_document(db: Session, document: KnowledgeDocument) -> KnowledgeGapItem | None:
    return db.scalar(
        select(KnowledgeGapItem)
        .where(
            KnowledgeGapItem.tenant_id == document.tenant_id,
            KnowledgeGapItem.linked_knowledge_document_id == document.id,
        )
        .order_by(KnowledgeGapItem.updated_at.desc(), KnowledgeGapItem.id.desc())
    )


def _publish_gate_evaluation_set(
    db: Session,
    document: KnowledgeDocument,
    gap: KnowledgeGapItem | None,
    payload: KnowledgeDocumentPublishGateCreate,
) -> KnowledgeEvaluationSet | None:
    if payload.evaluation_set_id is not None:
        evaluation_set = db.get(KnowledgeEvaluationSet, payload.evaluation_set_id)
        if evaluation_set is None or evaluation_set.tenant_id != document.tenant_id:
            raise HTTPException(status_code=404, detail="knowledge evaluation set not found")
        return evaluation_set

    remediation = {}
    if gap is not None and isinstance(gap.evidence_payload, dict):
        remediation = gap.evidence_payload.get("remediation") if isinstance(gap.evidence_payload.get("remediation"), dict) else {}
    evaluation_set_id = _safe_int(remediation.get("regression_evaluation_set_id"), 0)
    if evaluation_set_id:
        evaluation_set = db.get(KnowledgeEvaluationSet, evaluation_set_id)
        if evaluation_set is not None and evaluation_set.tenant_id == document.tenant_id:
            return evaluation_set

    if gap is None:
        return None
    return db.scalar(
        select(KnowledgeEvaluationSet).where(
            KnowledgeEvaluationSet.tenant_id == document.tenant_id,
            KnowledgeEvaluationSet.name == KNOWLEDGE_GAP_REMEDIATION_SET_NAME,
        )
    )


def _publish_gate_target_case_ids(
    db: Session,
    evaluation_set: KnowledgeEvaluationSet | None,
    gap: KnowledgeGapItem | None,
    payload: KnowledgeDocumentPublishGateCreate,
) -> list[int]:
    if evaluation_set is None:
        return []

    explicit_ids = _clean_int_list(payload.evaluation_case_ids)
    if explicit_ids:
        return explicit_ids

    remediation = {}
    if gap is not None and isinstance(gap.evidence_payload, dict):
        remediation = gap.evidence_payload.get("remediation") if isinstance(gap.evidence_payload.get("remediation"), dict) else {}
    regression_case_id = _safe_int(remediation.get("regression_evaluation_case_id"), 0)
    if regression_case_id:
        return [regression_case_id]

    if payload.evaluation_set_id is not None:
        return [case.id for case in _evaluation_cases_for_set(db, evaluation_set.id, status_filter="active")]
    return []


def _publish_case_read(result: KnowledgeEvaluationRunCaseRead, *, blocking: bool, advisory: bool) -> KnowledgeDocumentPublishGateCaseRead:
    return KnowledgeDocumentPublishGateCaseRead(
        evaluation_case_id=result.evaluation_case_id,
        status=result.status,
        failure_reason=result.failure_reason,
        blocking=blocking,
        advisory=advisory,
        top_confidence=result.top_confidence,
        top_chunk_id=result.top_chunk_id,
        citation_present=result.citation_present,
        expected_terms_found=result.expected_terms_found,
        matched_terms=result.matched_terms,
    )


def _knowledge_document_publication_snapshot(document: KnowledgeDocument) -> dict:
    return {
        "document_id": document.id,
        "title": document.title,
        "source_type": document.source_type,
        "source_uri": document.source_uri,
        "content_hash": document.content_hash,
        "raw_text_hash": hashlib.sha256(document.raw_text.encode("utf-8")).hexdigest(),
        "raw_text_character_count": len(document.raw_text),
        "tags": list(document.tags or []),
        "status": document.status,
        "ingestion_status": document.ingestion_status,
        "chunk_count": document.chunk_count,
        "updated_at": document.updated_at.isoformat() if document.updated_at else None,
    }


def _knowledge_document_publication_read(
    publication: KnowledgeDocumentPublication,
) -> KnowledgeDocumentPublicationRead:
    return KnowledgeDocumentPublicationRead.model_validate(publication)


def _latest_document_publication(
    db: Session,
    document: KnowledgeDocument,
    *,
    status_filter: str | None = None,
) -> KnowledgeDocumentPublication | None:
    query = select(KnowledgeDocumentPublication).where(
        KnowledgeDocumentPublication.tenant_id == document.tenant_id,
        KnowledgeDocumentPublication.document_id == document.id,
    )
    if status_filter is not None:
        query = query.where(KnowledgeDocumentPublication.status == status_filter)
    return db.scalar(query.order_by(KnowledgeDocumentPublication.created_at.desc(), KnowledgeDocumentPublication.id.desc()))


def _create_knowledge_document_publication(
    db: Session,
    *,
    document: KnowledgeDocument,
    gap: KnowledgeGapItem | None,
    principal: CurrentPrincipal,
    publication_type: str,
    publication_status: str,
    from_status: str,
    to_status: str,
    evaluation_set_id: int | None = None,
    evaluation_run_id: int | None = None,
    checked_case_ids: list[int] | None = None,
    case_results: list[KnowledgeDocumentPublishGateCaseRead] | None = None,
    blocking_reasons: list[str] | None = None,
    advisory_reasons: list[str] | None = None,
    checks: dict | None = None,
    document_snapshot: dict | None = None,
    rollback_target_publication_id: int | None = None,
    rollback_reason: str = "",
) -> KnowledgeDocumentPublication:
    previous = _latest_document_publication(db, document)
    publication = KnowledgeDocumentPublication(
        tenant_id=document.tenant_id,
        document_id=document.id,
        gap_id=gap.id if gap is not None else None,
        publication_type=publication_type,
        status=publication_status,
        from_status=from_status,
        to_status=to_status,
        evaluation_set_id=evaluation_set_id,
        evaluation_run_id=evaluation_run_id,
        checked_case_ids=list(checked_case_ids or []),
        case_results=[item.model_dump(mode="json") for item in case_results or []],
        blocking_reasons=list(blocking_reasons or []),
        advisory_reasons=list(advisory_reasons or []),
        checks=dict(checks or {}),
        document_snapshot=dict(document_snapshot or _knowledge_document_publication_snapshot(document)),
        previous_publication_id=previous.id if previous is not None else None,
        rollback_target_publication_id=rollback_target_publication_id,
        rollback_reason=rollback_reason,
        external_write_performed=False,
        model_call_performed=False,
        created_by_id=principal.user.id,
        created_at=utc_now(),
    )
    db.add(publication)
    db.flush()
    return publication


def check_knowledge_document_publish_gate(
    db: Session,
    document_id: int,
    payload: KnowledgeDocumentPublishGateCreate,
    principal: CurrentPrincipal,
    *,
    perform_publish: bool = False,
) -> KnowledgeDocumentPublishGateRead:
    document = _knowledge_document_or_404(db, document_id, principal)
    from_status = document.status
    document_snapshot = _knowledge_document_publication_snapshot(document)
    gap = _linked_gap_for_document(db, document)
    evaluation_set = _publish_gate_evaluation_set(db, document, gap, payload)
    target_case_ids = _publish_gate_target_case_ids(db, evaluation_set, gap, payload)
    blocking_reasons: list[str] = []
    advisory_reasons: list[str] = []
    case_results: list[KnowledgeDocumentPublishGateCaseRead] = []
    run_read: KnowledgeEvaluationRunRead | None = None

    if document.status == "archived":
        blocking_reasons.append("document_archived")
    if document.ingestion_status != "indexed":
        blocking_reasons.append("document_not_indexed")
    if document.chunk_count <= 0:
        blocking_reasons.append("document_has_no_chunks")
    if not document.source_uri.strip():
        blocking_reasons.append("missing_source_uri")
    if evaluation_set is None:
        blocking_reasons.append("missing_regression_set")
    if payload.require_regression_case and not target_case_ids:
        blocking_reasons.append("missing_regression_case")

    if evaluation_set is not None and target_case_ids:
        set_case_ids = {case.id for case in _evaluation_cases_for_set(db, evaluation_set.id)}
        missing_case_ids = [case_id for case_id in target_case_ids if case_id not in set_case_ids]
        if missing_case_ids:
            blocking_reasons.append("regression_case_not_in_set")
        else:
            search_status = payload.search_status or ("draft" if document.status == "draft" else "active")
            run_read = run_knowledge_evaluation_set(
                db,
                evaluation_set.id,
                KnowledgeEvaluationRunCreate(
                    top_k=payload.top_k,
                    min_score=payload.min_score,
                    status="active",
                    search_status=search_status,
                    low_confidence_threshold=payload.low_confidence_threshold,
                ),
                principal,
            )
            target_set = set(target_case_ids)
            target_results = [case for case in run_read.case_results if case.evaluation_case_id in target_set]
            if not target_results:
                blocking_reasons.append("target_cases_not_evaluated")
            answered = 0
            citation_covered = 0
            expected_terms_covered = 0
            for result in target_results:
                if result.top_chunk_id is not None:
                    answered += 1
                if result.citation_present:
                    citation_covered += 1
                if result.expected_terms_found:
                    expected_terms_covered += 1
                reason = (result.failure_reason or "").strip()
                advisory = bool(
                    reason
                    and payload.ignore_safe_handoff_failures
                    and reason in PUBLISH_GATE_SAFE_HANDOFF_REASONS
                )
                blocking = bool(reason) and not advisory
                if blocking and reason not in blocking_reasons:
                    blocking_reasons.append(reason if reason in PUBLISH_GATE_BLOCKING_FAILURE_REASONS else f"evaluation_blocked:{reason}")
                if advisory and reason not in advisory_reasons:
                    advisory_reasons.append(reason)
                case_results.append(_publish_case_read(result, blocking=blocking, advisory=advisory))

            target_total = len(target_results)
            target_hit_rate = _ratio(answered, target_total)
            target_citation_coverage = _ratio(citation_covered, target_total)
            target_expected_term_coverage = _ratio(expected_terms_covered, target_total)
            if target_total > 0 and target_hit_rate < payload.min_hit_rate:
                blocking_reasons.append("hit_rate_below_publish_threshold")
            if target_total > 0 and target_citation_coverage < payload.min_citation_coverage:
                blocking_reasons.append("citation_coverage_below_publish_threshold")
            if target_total > 0 and target_expected_term_coverage < payload.min_expected_term_coverage:
                blocking_reasons.append("expected_term_coverage_below_publish_threshold")
        checked_case_ids = target_case_ids
    else:
        checked_case_ids = target_case_ids

    checks = {
        "document_status": document.status,
        "ingestion_status": document.ingestion_status,
        "chunk_count": document.chunk_count,
        "source_uri_present": bool(document.source_uri.strip()),
        "evaluation_set_id": evaluation_set.id if evaluation_set else None,
        "checked_case_count": len(checked_case_ids),
        "evaluated_case_count": len(case_results),
        "target_hit_rate": _ratio(sum(1 for item in case_results if item.top_chunk_id is not None), len(case_results)),
        "target_citation_coverage": _ratio(sum(1 for item in case_results if item.citation_present), len(case_results)),
        "target_expected_term_coverage": _ratio(sum(1 for item in case_results if item.expected_terms_found), len(case_results)),
        "search_status": payload.search_status or ("draft" if document.status == "draft" else "active"),
        "ignore_safe_handoff_failures": payload.ignore_safe_handoff_failures,
        "external_write_performed": False,
        "model_call_performed": False,
    }
    unique_blocking_reasons = list(dict.fromkeys(blocking_reasons))
    can_publish = not unique_blocking_reasons
    published = False

    if perform_publish and can_publish:
        now = utc_now()
        document.status = "active"
        document.updated_by_id = principal.user.id
        document.updated_at = now
        chunks = list(
            db.scalars(
                select(KnowledgeDocumentChunk).where(
                    KnowledgeDocumentChunk.tenant_id == document.tenant_id,
                    KnowledgeDocumentChunk.document_id == document.id,
                )
            ).all()
        )
        for chunk in chunks:
            chunk.status = "active"

        if gap is not None:
            gap.status = "resolved"
            gap.resolved_at = now
            gap.resolved_by_id = principal.user.id
            gap.updated_by_id = principal.user.id
            gap.updated_at = now
            gap.resolution_note = f"知识文档 #{document.id} 已通过发布门禁并启用；评测运行 #{run_read.id if run_read else '未运行'}。"
            gap.evidence_payload = _merge_gap_remediation_payload(
                gap,
                {
                    "published_document_id": document.id,
                    "published_at": now.isoformat(),
                    "publish_gate_run_id": run_read.id if run_read else None,
                    "publish_gate_passed": True,
                },
            )

        add_audit_event(
            db,
            tenant_id=document.tenant_id,
            actor_id=principal.user.id,
            action="knowledge_document.published",
            resource_type="knowledge_document",
            resource_id=str(document.id),
            payload={
                "evaluation_set_id": evaluation_set.id if evaluation_set else None,
                "evaluation_run_id": run_read.id if run_read else None,
                "checked_case_ids": checked_case_ids,
                "gap_id": gap.id if gap else None,
                "external_write_performed": False,
                "model_call_performed": False,
            },
        )
        db.commit()
        db.refresh(document)
        if gap is not None:
            db.refresh(gap)
        published = True
    elif perform_publish:
        add_audit_event(
            db,
            tenant_id=document.tenant_id,
            actor_id=principal.user.id,
            action="knowledge_document.publish_blocked",
            resource_type="knowledge_document",
            resource_id=str(document.id),
            payload={
                "blocking_reasons": unique_blocking_reasons,
                "advisory_reasons": advisory_reasons,
                "evaluation_set_id": evaluation_set.id if evaluation_set else None,
                "evaluation_run_id": run_read.id if run_read else None,
                "checked_case_ids": checked_case_ids,
                "external_write_performed": False,
                "model_call_performed": False,
            },
        )
        db.commit()

    publication_status = "published" if published else "blocked" if perform_publish else "passed" if can_publish else "blocked"
    publication_type = "publish" if perform_publish else "publish_check"
    publication = _create_knowledge_document_publication(
        db,
        document=document,
        gap=gap,
        principal=principal,
        publication_type=publication_type,
        publication_status=publication_status,
        from_status=from_status,
        to_status=document.status,
        evaluation_set_id=evaluation_set.id if evaluation_set else None,
        evaluation_run_id=run_read.id if run_read else None,
        checked_case_ids=checked_case_ids,
        case_results=case_results,
        blocking_reasons=unique_blocking_reasons,
        advisory_reasons=list(dict.fromkeys(advisory_reasons)),
        checks=checks,
        document_snapshot=document_snapshot,
    )
    add_audit_event(
        db,
        tenant_id=document.tenant_id,
        actor_id=principal.user.id,
        action=f"knowledge_document.{publication_type}_recorded",
        resource_type="knowledge_document_publication",
        resource_id=str(publication.id),
        payload={
            "document_id": document.id,
            "publication_type": publication_type,
            "status": publication_status,
            "external_write_performed": False,
            "model_call_performed": False,
        },
    )
    db.commit()

    message = (
        "知识文档已通过门禁并发布。"
        if published
        else "知识文档通过发布门禁，可发布。"
        if can_publish
        else "知识文档未通过发布门禁，请先处理阻断项。"
    )
    return KnowledgeDocumentPublishGateRead(
        document=document,
        gap=_knowledge_gap_read(gap) if gap is not None else None,
        evaluation_set_id=evaluation_set.id if evaluation_set else None,
        evaluation_run=run_read,
        checked_case_ids=checked_case_ids,
        case_results=case_results,
        can_publish=can_publish,
        published=published,
        blocking_reasons=unique_blocking_reasons,
        advisory_reasons=list(dict.fromkeys(advisory_reasons)),
        checks=checks,
        message=message,
    )


def list_knowledge_document_publications(
    db: Session,
    document_id: int,
    *,
    principal: CurrentPrincipal,
    page: int = 1,
    page_size: int = 20,
) -> KnowledgeDocumentPublicationList:
    document = _knowledge_document_or_404(db, document_id, principal)
    total = db.scalar(
        select(func.count(KnowledgeDocumentPublication.id)).where(
            KnowledgeDocumentPublication.tenant_id == document.tenant_id,
            KnowledgeDocumentPublication.document_id == document.id,
        )
    ) or 0
    items = list(
        db.scalars(
            select(KnowledgeDocumentPublication)
            .where(
                KnowledgeDocumentPublication.tenant_id == document.tenant_id,
                KnowledgeDocumentPublication.document_id == document.id,
            )
            .order_by(KnowledgeDocumentPublication.created_at.desc(), KnowledgeDocumentPublication.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()
    )
    return KnowledgeDocumentPublicationList(
        items=[_knowledge_document_publication_read(item) for item in items],
        page=page,
        page_size=page_size,
        total=total,
    )


def rollback_knowledge_document_publication(
    db: Session,
    document_id: int,
    payload: KnowledgeDocumentRollbackCreate,
    principal: CurrentPrincipal,
) -> KnowledgeDocumentPublicationRead:
    document = _knowledge_document_or_404(db, document_id, principal)
    if document.status == "archived":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="archived document cannot be rolled back")

    target_publication: KnowledgeDocumentPublication | None
    if payload.target_publication_id is not None:
        target_publication = db.get(KnowledgeDocumentPublication, payload.target_publication_id)
        if (
            target_publication is None
            or target_publication.tenant_id != document.tenant_id
            or target_publication.document_id != document.id
        ):
            raise HTTPException(status_code=404, detail="knowledge document publication not found")
    else:
        target_publication = _latest_document_publication(db, document, status_filter="published")

    if target_publication is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="published publication is required before rollback")

    now = utc_now()
    from_status = document.status
    document_snapshot = _knowledge_document_publication_snapshot(document)
    document.status = "draft"
    document.updated_by_id = principal.user.id
    document.updated_at = now
    chunks = list(
        db.scalars(
            select(KnowledgeDocumentChunk).where(
                KnowledgeDocumentChunk.tenant_id == document.tenant_id,
                KnowledgeDocumentChunk.document_id == document.id,
            )
        ).all()
    )
    for chunk in chunks:
        chunk.status = "draft"

    gap = _linked_gap_for_document(db, document)
    checks = {
        "rollback_scope": "document_status_and_chunk_status",
        "content_restored": False,
        "target_publication_id": target_publication.id,
        "target_publication_status": target_publication.status,
        "target_publication_created_at": target_publication.created_at.isoformat()
        if target_publication.created_at
        else None,
        "external_write_performed": False,
        "model_call_performed": False,
    }
    publication = _create_knowledge_document_publication(
        db,
        document=document,
        gap=gap,
        principal=principal,
        publication_type="rollback",
        publication_status="rolled_back",
        from_status=from_status,
        to_status=document.status,
        evaluation_set_id=target_publication.evaluation_set_id,
        evaluation_run_id=target_publication.evaluation_run_id,
        checked_case_ids=target_publication.checked_case_ids,
        case_results=[],
        blocking_reasons=[],
        advisory_reasons=[],
        checks=checks,
        document_snapshot=document_snapshot,
        rollback_target_publication_id=target_publication.id,
        rollback_reason=payload.rollback_reason,
    )

    if gap is not None and gap.status == "resolved":
        gap.status = "in_progress"
        gap.resolved_at = None
        gap.resolved_by_id = None
        gap.updated_by_id = principal.user.id
        gap.updated_at = now
        gap.resolution_note = f"知识文档 #{document.id} 已回滚为草稿；发布记录 #{publication.id}。"
        gap.evidence_payload = _merge_gap_remediation_payload(
            gap,
            {
                "publish_rollback_publication_id": publication.id,
                "publish_rollback_target_publication_id": target_publication.id,
                "publish_rollback_at": now.isoformat(),
                "publish_gate_passed": False,
            },
        )

    add_audit_event(
        db,
        tenant_id=document.tenant_id,
        actor_id=principal.user.id,
        action="knowledge_document.rollback_recorded",
        resource_type="knowledge_document_publication",
        resource_id=str(publication.id),
        payload={
            "document_id": document.id,
            "target_publication_id": target_publication.id,
            "from_status": from_status,
            "to_status": document.status,
            "external_write_performed": False,
            "model_call_performed": False,
        },
    )
    db.commit()
    db.refresh(publication)
    db.refresh(document)
    return _knowledge_document_publication_read(publication)


def export_knowledge_evaluation_run_report(
    db: Session,
    evaluation_run_id: int,
    *,
    report_format: str,
    principal: CurrentPrincipal,
) -> KnowledgeEvaluationRunReportRead:
    normalized_format = report_format.strip().lower()
    if normalized_format not in {"markdown", "csv"}:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="report format must be markdown or csv",
        )
    run = get_knowledge_evaluation_run(db, evaluation_run_id, principal)
    rows = _report_rows(run)
    summary = _report_summary(run, rows)
    if normalized_format == "csv":
        filename = f"customer_service_eval_run_{run.id}_cases.csv"
        content_type = "text/csv; charset=utf-8"
        body = _report_csv_body(rows)
    else:
        filename = f"customer_service_eval_run_{run.id}_review.md"
        content_type = "text/markdown; charset=utf-8"
        body = _report_markdown_body(summary, rows)
    return KnowledgeEvaluationRunReportRead(
        evaluation_run_id=run.id,
        evaluation_set_id=run.evaluation_set_id,
        tenant_id=run.tenant_id,
        report_format=normalized_format,
        filename=filename,
        content_type=content_type,
        body=body,
        raw_text_included=False,
        provider_call_performed=False,
        external_write_performed=False,
        summary=summary,
    )


def _split_document_chunks(raw_text: str, *, chunk_size: int, chunk_overlap: int) -> list[dict]:
    text = raw_text.strip()
    if not text:
        return []
    safe_overlap = min(chunk_overlap, max(chunk_size // 3, 0))
    blocks: list[tuple[str, str, int, int]] = []
    current_section = ""
    cursor = 0
    for raw_block in re.split(r"\n\s*\n", text):
        block = raw_block.strip()
        if not block:
            cursor += len(raw_block) + 2
            continue
        section_match = SECTION_RE.match(block)
        if section_match:
            current_section = section_match.group(1).strip()
        start = text.find(block, cursor)
        if start < 0:
            start = cursor
        end = start + len(block)
        blocks.append((block, current_section, start, end))
        cursor = end

    chunks: list[dict] = []
    for block, section_title, start, end in blocks:
        if len(block) <= chunk_size:
            chunks.append(
                {
                    "content": block,
                    "section_title": section_title,
                    "char_start": start,
                    "char_end": end,
                }
            )
            continue
        offset = 0
        while offset < len(block):
            piece = block[offset : offset + chunk_size].strip()
            if piece:
                piece_start = start + offset
                chunks.append(
                    {
                        "content": piece,
                        "section_title": section_title,
                        "char_start": piece_start,
                        "char_end": piece_start + len(piece),
                    }
                )
            if offset + chunk_size >= len(block):
                break
            offset += max(chunk_size - safe_overlap, 1)
    return chunks


def get_knowledge_memory_mesh_overview(
    db: Session,
    tenant_id: int,
    principal: CurrentPrincipal,
) -> KnowledgeMemoryMeshOverviewRead:
    _require_same_tenant(db, tenant_id, principal)

    material_batches = _count_rows(db, CustomerMaterialBatch, CustomerMaterialBatch.tenant_id == tenant_id)
    healthy_material_batches = _count_rows(
        db,
        CustomerMaterialBatch,
        CustomerMaterialBatch.tenant_id == tenant_id,
        CustomerMaterialBatch.blocker_count == 0,
        CustomerMaterialBatch.desensitization_risk_count == 0,
    )
    risky_material_batches = max(material_batches - healthy_material_batches, 0)

    active_cards = _count_rows(db, KnowledgeCard, KnowledgeCard.tenant_id == tenant_id, KnowledgeCard.status == "active")
    active_object_cards = _count_rows(
        db,
        ObjectKnowledgeCard,
        ObjectKnowledgeCard.tenant_id == tenant_id,
        ObjectKnowledgeCard.status == "active",
    )
    sourced_cards = _count_rows(
        db,
        KnowledgeCard,
        KnowledgeCard.tenant_id == tenant_id,
        KnowledgeCard.status == "active",
        KnowledgeCard.source_uri != "",
    )
    active_objects = _count_rows(
        db,
        BusinessObject,
        BusinessObject.tenant_id == tenant_id,
        BusinessObject.status == "active",
    )

    evaluation_cases = _count_rows(db, KnowledgeEvaluationCase, KnowledgeEvaluationCase.tenant_id == tenant_id)
    evaluation_run_cases = _count_rows(db, KnowledgeEvaluationRunCase, KnowledgeEvaluationRunCase.tenant_id == tenant_id)
    run_case_payloads = db.scalars(
        select(KnowledgeEvaluationRunCase.result_payload).where(KnowledgeEvaluationRunCase.tenant_id == tenant_id)
    )
    labeled_run_cases = sum(
        1
        for payload in run_case_payloads
        if isinstance(payload, dict)
        and (
            payload.get("factuality_label")
            or payload.get("final_answer_factuality_label")
            or payload.get("citation_sufficiency_label")
        )
    )

    gaps_total = _count_rows(db, KnowledgeGapItem, KnowledgeGapItem.tenant_id == tenant_id)
    open_gaps = _count_rows(
        db,
        KnowledgeGapItem,
        KnowledgeGapItem.tenant_id == tenant_id,
        KnowledgeGapItem.status.in_(["open", "triaged", "in_progress"]),
    )
    resolved_gaps = _count_rows(
        db,
        KnowledgeGapItem,
        KnowledgeGapItem.tenant_id == tenant_id,
        KnowledgeGapItem.status == "resolved",
    )
    linked_gaps = _count_rows(
        db,
        KnowledgeGapItem,
        KnowledgeGapItem.tenant_id == tenant_id,
        or_(
            KnowledgeGapItem.linked_knowledge_card_id.is_not(None),
            KnowledgeGapItem.linked_knowledge_document_id.is_not(None),
        ),
    )

    documents = _count_rows(db, KnowledgeDocument, KnowledgeDocument.tenant_id == tenant_id)
    active_documents = _count_rows(
        db,
        KnowledgeDocument,
        KnowledgeDocument.tenant_id == tenant_id,
        KnowledgeDocument.status == "active",
    )
    chunks = _count_rows(db, KnowledgeDocumentChunk, KnowledgeDocumentChunk.tenant_id == tenant_id)
    chunks_with_source_and_hash = _count_rows(
        db,
        KnowledgeDocumentChunk,
        KnowledgeDocumentChunk.tenant_id == tenant_id,
        KnowledgeDocumentChunk.source_uri != "",
        KnowledgeDocumentChunk.content_hash != "",
    )
    published_records = _count_rows(
        db,
        KnowledgeDocumentPublication,
        KnowledgeDocumentPublication.tenant_id == tenant_id,
        KnowledgeDocumentPublication.status.in_(["published", "passed"]),
    )

    reply_decisions = _count_rows(db, ReplyDecision, ReplyDecision.tenant_id == tenant_id)
    reply_decisions_with_provenance = _count_rows(
        db,
        ReplyDecision,
        ReplyDecision.tenant_id == tenant_id,
        ReplyDecision.provenance_id != "",
    )
    draft_decisions = _count_rows(db, ReplyDecision, ReplyDecision.tenant_id == tenant_id, ReplyDecision.draft_reply != "")
    handoff_decisions = _count_rows(
        db,
        ReplyDecision,
        ReplyDecision.tenant_id == tenant_id,
        ReplyDecision.state.in_(["manual_gate_required", "needs_human_review", "handoff_required"]),
    )
    external_write_allowed = _count_rows(
        db,
        ReplyDecision,
        ReplyDecision.tenant_id == tenant_id,
        ReplyDecision.external_write_allowed.is_(True),
    )
    high_confidence_decisions = _count_rows(
        db,
        ReplyDecision,
        ReplyDecision.tenant_id == tenant_id,
        ReplyDecision.confidence >= 0.75,
    )

    citations = _count_rows(db, ReplyCitationSnapshot, ReplyCitationSnapshot.tenant_id == tenant_id)
    citations_with_source_and_hash = _count_rows(
        db,
        ReplyCitationSnapshot,
        ReplyCitationSnapshot.tenant_id == tenant_id,
        ReplyCitationSnapshot.source_uri != "",
        ReplyCitationSnapshot.content_hash != "",
    )
    no_citation_reasons = _count_rows(
        db,
        ReplyCitationSnapshot,
        ReplyCitationSnapshot.tenant_id == tenant_id,
        ReplyCitationSnapshot.no_citation_reason != "",
    )
    citation_provenance_count = int(
        db.scalar(
            select(func.count(func.distinct(ReplyCitationSnapshot.provenance_id))).where(
                ReplyCitationSnapshot.tenant_id == tenant_id,
                ReplyCitationSnapshot.provenance_id != "",
            )
        )
        or 0
    )

    model_calls = _count_rows(db, ModelCallRecord, ModelCallRecord.tenant_id == tenant_id)
    model_calls_with_provenance = _count_rows(
        db,
        ModelCallRecord,
        ModelCallRecord.tenant_id == tenant_id,
        ModelCallRecord.provenance_id != "",
    )

    latest_run = db.scalar(
        select(KnowledgeEvaluationRun)
        .where(KnowledgeEvaluationRun.tenant_id == tenant_id)
        .order_by(KnowledgeEvaluationRun.created_at.desc(), KnowledgeEvaluationRun.id.desc())
        .limit(1)
    )
    final_answer_quality_measured = bool(
        latest_run
        and (
            latest_run.summary_payload.get("final_answer_factuality_measured")
            or latest_run.summary_payload.get("factuality_label_coverage", 0) > 0
        )
    )

    knowledge_card_total = active_cards + active_object_cards + active_documents
    knowledge_card_healthy = sourced_cards + active_object_cards + chunks_with_source_and_hash
    sample_total = evaluation_cases + reply_decisions_with_provenance
    sample_healthy = evaluation_run_cases + reply_decisions_with_provenance
    quality_total = gaps_total + evaluation_run_cases
    quality_healthy = resolved_gaps + labeled_run_cases

    nodes = [
        _mesh_node(
            key="material_batch",
            label="资料批次",
            total_count=material_batches,
            healthy_count=healthy_material_batches,
            risk_count=risky_material_batches,
            evidence="客户资料包、题库和 manifest 的预检结果",
            next_action="资料不足时先补资料来源、脱敏声明和四层知识字段",
        ),
        _mesh_node(
            key="knowledge_card",
            label="知识卡片",
            total_count=knowledge_card_total,
            healthy_count=knowledge_card_healthy,
            risk_count=max(knowledge_card_total - knowledge_card_healthy, 0),
            evidence="标准问答、对象问答、文档 chunk 和来源引用",
            next_action="补 source_uri、content_hash、可引用片段和发布记录",
        ),
        _mesh_node(
            key="business_object",
            label="业务对象",
            total_count=active_objects,
            healthy_count=active_objects,
            risk_count=0,
            evidence="产品、服务、套餐、课程、门店等对象",
            next_action="把问答绑定到具体业务对象，避免泛 FAQ 漂浮",
        ),
        _mesh_node(
            key="question_sample",
            label="真实/样本问题",
            total_count=sample_total,
            healthy_count=sample_healthy,
            risk_count=max(sample_total - sample_healthy, 0),
            evidence="固定评测题、入站样本和带 provenance 的回复决策",
            next_action="没有真实客户问题时只能保持内部样板，不写客户签收",
        ),
        _mesh_node(
            key="quality_label_cause",
            label="质量标签与错因",
            total_count=quality_total,
            healthy_count=quality_healthy,
            risk_count=open_gaps,
            evidence="评测标签、知识缺口、人工驳回和修复结果",
            next_action="把失败样本转成缺口，再补知识并回归验证",
        ),
    ]

    provenance_steps = [
        _mesh_step(
            key="inbound_sample",
            label="入站样本",
            observed_count=reply_decisions_with_provenance,
            evidence="带 provenance_id 的回复决策",
            blocker="没有入站样本时只能做离线题库评测",
            optional=True,
        ),
        _mesh_step(
            key="retrieval_result",
            label="检索结果",
            observed_count=evaluation_run_cases + citations,
            evidence="评测 run case 和引用快照",
            blocker="不能只展示知识条目，需要知道每次问题实际命中了什么",
        ),
        _mesh_step(
            key="citation_chunk",
            label="引用 chunk",
            observed_count=citations_with_source_and_hash + chunks_with_source_and_hash,
            evidence="source_uri、content_hash、document_chunk_id",
            blocker="引用无法追到 chunk/version/hash/source_uri",
        ),
        _mesh_step(
            key="model_call",
            label="模型调用",
            observed_count=model_calls_with_provenance,
            evidence="模型调用台账、成本和降级动作",
            blocker="没有真实模型调用时只能作为确定性本地演练",
            optional=True,
        ),
        _mesh_step(
            key="final_draft",
            label="最终草稿",
            observed_count=draft_decisions,
            evidence="回复决策记录存在草稿，但接口不返回草稿全文",
            blocker="没有最终草稿就不能评估客服答案质量",
            optional=True,
        ),
        _mesh_step(
            key="handoff_reason",
            label="转人工理由",
            observed_count=handoff_decisions,
            evidence="低置信、风险词、禁用承诺或无知识命中",
            blocker="转人工没有理由会影响复盘和客户信任",
            optional=True,
        ),
        _mesh_step(
            key="quality_label",
            label="质量标签",
            observed_count=labeled_run_cases,
            evidence="事实性、引用充分、禁用承诺和转人工正确性标签",
            blocker="只看检索命中，不看最终答案质量",
            optional=True,
        ),
        _mesh_step(
            key="repaired_version",
            label="修复后的知识版本",
            observed_count=published_records + resolved_gaps,
            evidence="发布记录、回滚记录和已解决缺口",
            blocker="失败样本没有转成修复后的知识版本",
            optional=True,
        ),
    ]

    no_citation_high_confidence_guard = (
        high_confidence_decisions == 0
        or citation_provenance_count >= high_confidence_decisions
        or no_citation_reasons > 0
    )
    citation_trace_ready = citations_with_source_and_hash > 0
    document_trace_ready = chunks_with_source_and_hash > 0
    material_ready = healthy_material_batches > 0
    final_quality_ready = final_answer_quality_measured and labeled_run_cases > 0

    readiness = {
        "material_batch_node_ready": material_ready,
        "knowledge_card_node_ready": knowledge_card_total > 0,
        "business_object_node_ready": active_objects > 0,
        "question_sample_node_ready": sample_total > 0,
        "quality_label_node_ready": quality_total > 0,
        "document_chunk_trace_ready": document_trace_ready,
        "reply_citation_trace_ready": citation_trace_ready,
        "final_answer_quality_ready": final_quality_ready,
        "no_citation_high_confidence_guard": no_citation_high_confidence_guard,
        "real_platform_send_ready": False,
        "full_memory_mesh_ready": bool(
            material_ready
            and knowledge_card_total > 0
            and active_objects > 0
            and citation_trace_ready
            and final_quality_ready
        ),
    }

    source_authority = {
        "documents": documents,
        "active_documents": active_documents,
        "chunks": chunks,
        "chunks_with_source_uri_and_hash": chunks_with_source_and_hash,
        "reply_citations": citations,
        "reply_citations_with_source_uri_and_hash": citations_with_source_and_hash,
        "reply_citation_provenance_count": citation_provenance_count,
        "no_citation_reason_count": no_citation_reasons,
        "source_authority_ready": document_trace_ready or citation_trace_ready,
        "conflict_detection_ready": False,
    }

    quality_loop = {
        "evaluation_cases": evaluation_cases,
        "evaluation_run_cases": evaluation_run_cases,
        "latest_run_id": latest_run.id if latest_run else None,
        "latest_run_hit_rate": latest_run.hit_rate if latest_run else None,
        "latest_run_citation_coverage": latest_run.citation_coverage if latest_run else None,
        "final_answer_quality_measured": final_answer_quality_measured,
        "knowledge_gaps": gaps_total,
        "open_gaps": open_gaps,
        "linked_gaps": linked_gaps,
        "resolved_gaps": resolved_gaps,
        "model_calls": model_calls,
        "model_calls_with_provenance": model_calls_with_provenance,
        "external_write_allowed_decisions": external_write_allowed,
    }

    waiting_nodes = [node.label for node in nodes if node.status == "waiting"]
    summary = (
        "知识网络总览已生成；当前展示本地资料、知识、样本、引用、模型和质量闭环的证据链。"
        if not waiting_nodes
        else f"知识网络总览已生成；仍需补齐：{'、'.join(waiting_nodes)}。"
    )

    return KnowledgeMemoryMeshOverviewRead(
        schema_version=KNOWLEDGE_MEMORY_MESH_SCHEMA_VERSION,
        tenant_id=tenant_id,
        generated_at=utc_now(),
        status="knowledge_memory_mesh_overview_ready",
        summary=summary,
        nodes=nodes,
        provenance_steps=provenance_steps,
        source_authority=source_authority,
        quality_loop=quality_loop,
        readiness=readiness,
        boundaries={
            "raw_text_included": False,
            "draft_reply_included": False,
            "real_platform_send_ready": False,
            "formal_customer_signoff_ready": False,
            "scope": "本地知识证据链和质量闭环，不代表真实平台已自动回复",
        },
    )


def require_knowledge_card_for_principal(
    db: Session,
    card_id: int,
    principal: CurrentPrincipal,
) -> KnowledgeCard:
    card = db.get(KnowledgeCard, card_id)
    if card is None or card.tenant_id != principal.tenant.id:
        raise HTTPException(status_code=404, detail="knowledge card not found")
    return card


def create_knowledge_card(
    db: Session,
    tenant_id: int,
    payload: KnowledgeCardCreate,
    principal: CurrentPrincipal,
) -> KnowledgeCard:
    _require_same_tenant(db, tenant_id, principal)
    _require_knowledge_manager(principal)
    now = utc_now()
    card = KnowledgeCard(
        tenant_id=tenant_id,
        title=payload.title.strip(),
        question=payload.question.strip(),
        answer=payload.answer.strip(),
        source_type=payload.source_type.strip() or "manual",
        source_uri=payload.source_uri.strip(),
        tags=_clean_string_list(payload.tags),
        aliases=_clean_string_list(payload.aliases),
        status=payload.status,
        created_by_id=principal.user.id,
        updated_by_id=principal.user.id,
        created_at=now,
        updated_at=now,
    )
    db.add(card)
    db.flush()
    add_audit_event(
        db,
        tenant_id=tenant_id,
        actor_id=principal.user.id,
        action="knowledge_card.created",
        resource_type="knowledge_card",
        resource_id=str(card.id),
        payload={"title": card.title, "status": card.status, "source_type": card.source_type},
    )
    db.commit()
    db.refresh(card)
    return card


def list_knowledge_cards(
    db: Session,
    tenant_id: int,
    *,
    status_filter: str | None,
    page: int,
    page_size: int,
    principal: CurrentPrincipal,
) -> KnowledgeCardList:
    _require_same_tenant(db, tenant_id, principal)
    query = select(KnowledgeCard).where(KnowledgeCard.tenant_id == tenant_id)
    count_query = select(func.count(KnowledgeCard.id)).where(KnowledgeCard.tenant_id == tenant_id)
    if status_filter:
        query = query.where(KnowledgeCard.status == status_filter)
        count_query = count_query.where(KnowledgeCard.status == status_filter)
    query = query.order_by(KnowledgeCard.updated_at.desc(), KnowledgeCard.id.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    return KnowledgeCardList(
        items=list(db.scalars(query).all()),
        page=page,
        page_size=page_size,
        total=int(db.scalar(count_query) or 0),
    )


def update_knowledge_card(
    db: Session,
    card_id: int,
    payload: KnowledgeCardUpdate,
    principal: CurrentPrincipal,
) -> KnowledgeCard:
    _require_knowledge_manager(principal)
    card = require_knowledge_card_for_principal(db, card_id, principal)
    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        if value is None:
            continue
        if field in {"tags", "aliases"}:
            setattr(card, field, _clean_string_list(value))
        elif isinstance(value, str):
            setattr(card, field, value.strip())
        else:
            setattr(card, field, value)
    card.updated_by_id = principal.user.id
    card.updated_at = utc_now()
    add_audit_event(
        db,
        tenant_id=card.tenant_id,
        actor_id=principal.user.id,
        action="knowledge_card.updated",
        resource_type="knowledge_card",
        resource_id=str(card.id),
        payload={"title": card.title, "status": card.status},
    )
    db.commit()
    db.refresh(card)
    return card


def _business_object_read(db: Session, business_object: BusinessObject) -> BusinessObjectRead:
    aliases = list(
        db.scalars(
            select(BusinessObjectAlias.alias)
            .where(BusinessObjectAlias.business_object_id == business_object.id)
            .order_by(BusinessObjectAlias.id.asc())
        ).all()
    )
    knowledge_card_count = int(
        db.scalar(
            select(func.count(ObjectKnowledgeCard.id)).where(
                ObjectKnowledgeCard.business_object_id == business_object.id,
                ObjectKnowledgeCard.status != "archived",
            )
        )
        or 0
    )
    return BusinessObjectRead(
        id=business_object.id,
        tenant_id=business_object.tenant_id,
        type=business_object.type,
        title=business_object.title,
        external_id=business_object.external_id,
        summary=business_object.summary,
        attrs_json=business_object.attrs_json or {},
        aliases=aliases,
        knowledge_card_count=knowledge_card_count,
        status=business_object.status,
        created_by_id=business_object.created_by_id,
        updated_by_id=business_object.updated_by_id,
        created_at=business_object.created_at,
        updated_at=business_object.updated_at,
    )


def _require_business_object_for_principal(
    db: Session,
    business_object_id: int,
    principal: CurrentPrincipal,
) -> BusinessObject:
    business_object = db.get(BusinessObject, business_object_id)
    if business_object is None or business_object.tenant_id != principal.tenant.id:
        raise HTTPException(status_code=404, detail="business object not found")
    return business_object


def create_business_object(
    db: Session,
    tenant_id: int,
    payload: BusinessObjectCreate,
    principal: CurrentPrincipal,
) -> BusinessObjectRead:
    _require_same_tenant(db, tenant_id, principal)
    _require_knowledge_manager(principal)
    now = utc_now()
    business_object = BusinessObject(
        tenant_id=tenant_id,
        type=payload.type,
        title=payload.title.strip(),
        external_id=payload.external_id.strip(),
        summary=payload.summary.strip(),
        attrs_json=payload.attrs_json,
        status=payload.status,
        created_by_id=principal.user.id,
        updated_by_id=principal.user.id,
        created_at=now,
        updated_at=now,
    )
    db.add(business_object)
    db.flush()
    for alias in _clean_string_list(payload.aliases):
        db.add(
            BusinessObjectAlias(
                tenant_id=tenant_id,
                business_object_id=business_object.id,
                alias=alias,
                channel_scope="all",
                created_at=now,
            )
        )
    add_audit_event(
        db,
        tenant_id=tenant_id,
        actor_id=principal.user.id,
        action="business_object.created",
        resource_type="business_object",
        resource_id=str(business_object.id),
        payload={"type": business_object.type, "title": business_object.title, "status": business_object.status},
    )
    db.commit()
    db.refresh(business_object)
    return _business_object_read(db, business_object)


def update_business_object(
    db: Session,
    business_object_id: int,
    payload: BusinessObjectUpdate,
    principal: CurrentPrincipal,
) -> BusinessObjectRead:
    _require_knowledge_manager(principal)
    business_object = _require_business_object_for_principal(db, business_object_id, principal)
    update_data = payload.model_dump(exclude_unset=True)
    now = utc_now()
    if "type" in update_data and update_data["type"] is not None:
        business_object.type = update_data["type"]
    if "title" in update_data and update_data["title"] is not None:
        business_object.title = update_data["title"].strip()
    if "external_id" in update_data and update_data["external_id"] is not None:
        business_object.external_id = update_data["external_id"].strip()
    if "summary" in update_data and update_data["summary"] is not None:
        business_object.summary = update_data["summary"].strip()
    if "attrs_json" in update_data and update_data["attrs_json"] is not None:
        business_object.attrs_json = update_data["attrs_json"]
    if "status" in update_data and update_data["status"] is not None:
        business_object.status = update_data["status"]
    if "aliases" in update_data and update_data["aliases"] is not None:
        db.execute(delete(BusinessObjectAlias).where(BusinessObjectAlias.business_object_id == business_object.id))
        for alias in _clean_string_list(update_data["aliases"]):
            db.add(
                BusinessObjectAlias(
                    tenant_id=business_object.tenant_id,
                    business_object_id=business_object.id,
                    alias=alias,
                    channel_scope="all",
                    created_at=now,
                )
            )
    business_object.updated_by_id = principal.user.id
    business_object.updated_at = now
    add_audit_event(
        db,
        tenant_id=business_object.tenant_id,
        actor_id=principal.user.id,
        action="business_object.updated",
        resource_type="business_object",
        resource_id=str(business_object.id),
        payload={"type": business_object.type, "title": business_object.title, "status": business_object.status},
    )
    db.commit()
    db.refresh(business_object)
    return _business_object_read(db, business_object)


def list_business_objects(
    db: Session,
    tenant_id: int,
    *,
    type_filter: str | None,
    status_filter: str | None,
    page: int,
    page_size: int,
    principal: CurrentPrincipal,
) -> BusinessObjectList:
    _require_same_tenant(db, tenant_id, principal)
    query = select(BusinessObject).where(BusinessObject.tenant_id == tenant_id)
    count_query = select(func.count(BusinessObject.id)).where(BusinessObject.tenant_id == tenant_id)
    if type_filter:
        query = query.where(BusinessObject.type == type_filter)
        count_query = count_query.where(BusinessObject.type == type_filter)
    if status_filter:
        query = query.where(BusinessObject.status == status_filter)
        count_query = count_query.where(BusinessObject.status == status_filter)
    query = query.order_by(BusinessObject.type.asc(), BusinessObject.title.asc(), BusinessObject.id.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    return BusinessObjectList(
        items=[_business_object_read(db, item) for item in db.scalars(query).all()],
        page=page,
        page_size=page_size,
        total=int(db.scalar(count_query) or 0),
    )


def create_object_knowledge_card(
    db: Session,
    business_object_id: int,
    payload: ObjectKnowledgeCardCreate,
    principal: CurrentPrincipal,
) -> ObjectKnowledgeCard:
    _require_knowledge_manager(principal)
    business_object = _require_business_object_for_principal(db, business_object_id, principal)
    now = utc_now()
    card = ObjectKnowledgeCard(
        tenant_id=business_object.tenant_id,
        business_object_id=business_object.id,
        question=payload.question.strip(),
        answer=payload.answer.strip(),
        trigger_keywords=_clean_string_list(payload.trigger_keywords),
        media_refs=_clean_string_list(payload.media_refs),
        scope=payload.scope,
        source=payload.source.strip() or "manual",
        version=payload.version,
        status=payload.status,
        created_by_id=principal.user.id,
        updated_by_id=principal.user.id,
        created_at=now,
        updated_at=now,
    )
    db.add(card)
    db.flush()
    business_object.updated_by_id = principal.user.id
    business_object.updated_at = now
    add_audit_event(
        db,
        tenant_id=business_object.tenant_id,
        actor_id=principal.user.id,
        action="object_knowledge_card.created",
        resource_type="object_knowledge_card",
        resource_id=str(card.id),
        payload={
            "business_object_id": business_object.id,
            "business_object_title": business_object.title,
            "status": card.status,
        },
    )
    db.commit()
    db.refresh(card)
    return card


def list_object_knowledge_cards(
    db: Session,
    business_object_id: int,
    *,
    status_filter: str | None,
    page: int,
    page_size: int,
    principal: CurrentPrincipal,
) -> ObjectKnowledgeCardList:
    business_object = _require_business_object_for_principal(db, business_object_id, principal)
    query = select(ObjectKnowledgeCard).where(ObjectKnowledgeCard.business_object_id == business_object.id)
    count_query = select(func.count(ObjectKnowledgeCard.id)).where(
        ObjectKnowledgeCard.business_object_id == business_object.id
    )
    if status_filter:
        query = query.where(ObjectKnowledgeCard.status == status_filter)
        count_query = count_query.where(ObjectKnowledgeCard.status == status_filter)
    query = query.order_by(ObjectKnowledgeCard.updated_at.desc(), ObjectKnowledgeCard.id.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    return ObjectKnowledgeCardList(
        items=[
            ObjectKnowledgeCardRead.model_validate(item, from_attributes=True)
            for item in db.scalars(query).all()
        ],
        page=page,
        page_size=page_size,
        total=int(db.scalar(count_query) or 0),
    )


def create_knowledge_document(
    db: Session,
    tenant_id: int,
    payload: KnowledgeDocumentCreate,
    principal: CurrentPrincipal,
) -> KnowledgeDocument:
    _require_same_tenant(db, tenant_id, principal)
    _require_knowledge_manager(principal)
    raw_text = payload.raw_text.strip()
    now = utc_now()
    settings = get_settings()
    profile = _resolve_embedding_profile(settings)
    _require_vector_store_available(profile, db)
    chunks = _split_document_chunks(
        raw_text,
        chunk_size=payload.chunk_size,
        chunk_overlap=payload.chunk_overlap,
    )
    chunk_embeddings: list[tuple[dict, list[str], EmbeddingResult]] = []
    for chunk_data in chunks:
        tokens = _tokenize(chunk_data["content"])
        embedding = _embed_text(chunk_data["content"], settings=settings)
        _require_embedding_available(embedding)
        chunk_embeddings.append((chunk_data, tokens, embedding))

    document = KnowledgeDocument(
        tenant_id=tenant_id,
        title=payload.title.strip(),
        source_type=payload.source_type.strip() or "manual_document",
        source_uri=payload.source_uri.strip(),
        raw_text=raw_text,
        content_hash=_content_hash(raw_text),
        tags=_clean_string_list(payload.tags),
        status=payload.status,
        ingestion_status="indexing",
        chunk_count=0,
        created_by_id=principal.user.id,
        updated_by_id=principal.user.id,
        created_at=now,
        updated_at=now,
    )
    db.add(document)
    db.flush()

    for index, (chunk_data, tokens, embedding) in enumerate(chunk_embeddings):
        terms = _token_vector(tokens)
        chunk = KnowledgeDocumentChunk(
            tenant_id=tenant_id,
            document_id=document.id,
            chunk_index=index,
            section_title=chunk_data["section_title"][:180],
            page_number=None,
            content=chunk_data["content"],
            content_hash=_content_hash(chunk_data["content"]),
            source_uri=document.source_uri,
            char_start=chunk_data["char_start"],
            char_end=chunk_data["char_end"],
            token_count=len(tokens),
            embedding_signature=_embedding_signature(embedding, terms=terms),
            embedding_vector=embedding.vector,
            embedding_provider=embedding.profile.provider,
            embedding_model=embedding.profile.model,
            embedding_dimension=len(embedding.vector),
            vector_store=embedding.profile.vector_store,
            vector_index_status=embedding.status,
            status=payload.status,
            created_at=now,
        )
        db.add(chunk)
        db.flush()
        if _is_pgvector_store(embedding.profile.vector_store):
            _write_pgvector_chunk_vector(db, chunk_id=chunk.id, vector=embedding.vector)

    document.chunk_count = len(chunks)
    document.ingestion_status = "indexed"
    document.updated_at = now
    add_audit_event(
        db,
        tenant_id=tenant_id,
        actor_id=principal.user.id,
        action="knowledge_document.imported",
        resource_type="knowledge_document",
        resource_id=str(document.id),
        payload={
            "title": document.title,
            "status": document.status,
            "source_type": document.source_type,
            "source_uri": document.source_uri,
            "chunk_count": document.chunk_count,
            "retrieval_mode": DOCUMENT_RETRIEVAL_MODE,
            "vector_engine": chunk_embeddings[0][2].profile.vector_engine if chunk_embeddings else "",
            "vector_store": chunk_embeddings[0][2].profile.vector_store if chunk_embeddings else "",
            "embedding_provider": chunk_embeddings[0][2].profile.provider if chunk_embeddings else "",
            "embedding_model": chunk_embeddings[0][2].profile.model if chunk_embeddings else "",
            "reranker": chunk_embeddings[0][2].profile.reranker if chunk_embeddings else "",
        },
    )
    db.commit()
    db.refresh(document)
    return document


def list_knowledge_documents(
    db: Session,
    tenant_id: int,
    *,
    status_filter: str | None,
    page: int,
    page_size: int,
    principal: CurrentPrincipal,
) -> KnowledgeDocumentList:
    _require_same_tenant(db, tenant_id, principal)
    query = select(KnowledgeDocument).where(KnowledgeDocument.tenant_id == tenant_id)
    count_query = select(func.count(KnowledgeDocument.id)).where(KnowledgeDocument.tenant_id == tenant_id)
    if status_filter:
        query = query.where(KnowledgeDocument.status == status_filter)
        count_query = count_query.where(KnowledgeDocument.status == status_filter)
    query = query.order_by(KnowledgeDocument.updated_at.desc(), KnowledgeDocument.id.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    return KnowledgeDocumentList(
        items=list(db.scalars(query).all()),
        page=page,
        page_size=page_size,
        total=int(db.scalar(count_query) or 0),
    )


def list_knowledge_document_chunks(
    db: Session,
    document_id: int,
    principal: CurrentPrincipal,
) -> list[KnowledgeChunkRead]:
    document = db.get(KnowledgeDocument, document_id)
    if document is None or document.tenant_id != principal.tenant.id:
        raise HTTPException(status_code=404, detail="knowledge document not found")
    chunks = list(
        db.scalars(
            select(KnowledgeDocumentChunk)
            .where(
                KnowledgeDocumentChunk.tenant_id == document.tenant_id,
                KnowledgeDocumentChunk.document_id == document.id,
            )
            .order_by(KnowledgeDocumentChunk.chunk_index.asc(), KnowledgeDocumentChunk.id.asc())
        ).all()
    )
    return [_chunk_read(document, chunk) for chunk in chunks]


def search_knowledge_documents(
    db: Session,
    tenant_id: int,
    payload: KnowledgeDocumentSearchRequest,
    principal: CurrentPrincipal,
) -> KnowledgeDocumentSearchResponse:
    _require_same_tenant(db, tenant_id, principal)
    settings = get_settings()
    query_embedding = _embed_text(payload.query, settings=settings)
    _require_embedding_available(query_embedding)
    _require_vector_store_available(query_embedding.profile, db)
    retrieval_backend = _retrieval_backend_for_profile(query_embedding.profile, db)
    pgvector_scores: dict[int, float] = {}
    candidate_ids: set[int] | None = None
    if _is_pgvector_store(query_embedding.profile.vector_store):
        pgvector_scores = _pgvector_candidate_scores(
            db,
            tenant_id=tenant_id,
            status_filter=payload.status,
            query_embedding=query_embedding,
            candidate_limit=max(payload.top_k * 8, 30),
        )
        candidate_ids = set(pgvector_scores)

    row_query = (
        select(KnowledgeDocumentChunk, KnowledgeDocument)
        .join(KnowledgeDocument, KnowledgeDocument.id == KnowledgeDocumentChunk.document_id)
        .where(
            KnowledgeDocumentChunk.tenant_id == tenant_id,
            KnowledgeDocumentChunk.status == payload.status,
            KnowledgeDocument.status == payload.status,
        )
        .order_by(KnowledgeDocument.updated_at.desc(), KnowledgeDocumentChunk.chunk_index.asc())
    )
    if candidate_ids is not None:
        if not candidate_ids:
            return KnowledgeDocumentSearchResponse(
                query=payload.query,
                retrieval_mode=DOCUMENT_RETRIEVAL_MODE,
                vector_engine=query_embedding.profile.vector_engine,
                vector_store=query_embedding.profile.vector_store,
                retrieval_backend=retrieval_backend,
                vector_index_status="indexed",
                embedding_provider=query_embedding.profile.provider,
                embedding_model=query_embedding.profile.model,
                reranker=query_embedding.profile.reranker,
                total_candidates=0,
                matches=[],
            )
        row_query = row_query.where(KnowledgeDocumentChunk.id.in_(candidate_ids))
    rows = list(db.execute(row_query).all())
    query_tokens = _tokenize(payload.query)
    query_terms = set(query_tokens)
    meaningful_query_terms = _meaningful_terms(query_terms)
    query_terms_vector = _token_vector(query_tokens)
    query_vector = query_embedding.vector
    chunk_tokens = {chunk.id: _tokenize(chunk.content) for chunk, _ in rows}
    document_frequencies: Counter[str] = Counter()
    for terms in chunk_tokens.values():
        document_frequencies.update(set(terms))
    average_length = (
        sum(len(terms) for terms in chunk_tokens.values()) / len(chunk_tokens)
        if chunk_tokens
        else 0
    )

    matches: list[KnowledgeDocumentSearchMatch] = []
    for chunk, document in rows:
        terms = chunk_tokens[chunk.id]
        bm25_score = _bm25_score(query_terms, terms, document_frequencies, len(rows), average_length)
        vector_score = 0.0
        if chunk.id in pgvector_scores:
            vector_score = pgvector_scores[chunk.id]
        elif isinstance(chunk.embedding_vector, list) and chunk.embedding_vector:
            vector_score = _cosine_from_dense_vectors(query_vector, chunk.embedding_vector)
        vector_terms: dict[str, float] = {}
        if isinstance(chunk.embedding_signature, dict):
            vector_terms = chunk.embedding_signature.get("terms") or {}
        if vector_score <= 0:
            vector_score = _cosine_from_vectors(query_terms_vector, vector_terms)
        matched_terms = _meaningful_terms(query_terms.intersection(set(terms)))
        if len(meaningful_query_terms) > 1 and len(matched_terms) < 1:
            continue
        reranker_score = _rerank_score(payload.query, meaningful_query_terms, matched_terms, chunk.content)
        score = (bm25_score * 0.72) + (vector_score * 2.35) + (reranker_score * 0.35)
        if score <= payload.min_score:
            continue
        matched_terms = sorted(matched_terms, key=lambda term: (-len(term), term))[:20]
        matches.append(
            KnowledgeDocumentSearchMatch(
                chunk_id=chunk.id,
                document_id=document.id,
                document_title=document.title,
                chunk_index=chunk.chunk_index,
                section_title=chunk.section_title,
                source_type=document.source_type,
                source_uri=chunk.source_uri,
                content_preview=chunk.content[:600],
                score=round(score, 4),
                confidence=_confidence_from_score(score),
                bm25_score=round(bm25_score, 4),
                vector_score=round(vector_score, 4),
                reranker_score=round(reranker_score, 4),
                matched_terms=matched_terms,
                citation=_chunk_citation(document=document, chunk=chunk),
            )
        )

    matches.sort(key=lambda match: (match.score, match.confidence, -match.chunk_index), reverse=True)
    return KnowledgeDocumentSearchResponse(
        query=payload.query,
        retrieval_mode=DOCUMENT_RETRIEVAL_MODE,
        vector_engine=query_embedding.profile.vector_engine,
        vector_store=query_embedding.profile.vector_store,
        retrieval_backend=retrieval_backend,
        vector_index_status="indexed",
        embedding_provider=query_embedding.profile.provider,
        embedding_model=query_embedding.profile.model,
        reranker=query_embedding.profile.reranker,
        total_candidates=len(rows),
        matches=matches[: payload.top_k],
    )


def rebuild_knowledge_vector_index(
    db: Session,
    tenant_id: int,
    payload: KnowledgeVectorIndexRebuildCreate,
    principal: CurrentPrincipal,
) -> KnowledgeVectorIndexRebuildRead:
    _require_same_tenant(db, tenant_id, principal)
    _require_knowledge_manager(principal)
    settings = get_settings()
    profile = _resolve_embedding_profile(settings)
    _require_vector_store_available(profile, db)
    retrieval_backend = _retrieval_backend_for_profile(profile, db)

    query = (
        select(KnowledgeDocumentChunk, KnowledgeDocument)
        .join(KnowledgeDocument, KnowledgeDocument.id == KnowledgeDocumentChunk.document_id)
        .where(
            KnowledgeDocumentChunk.tenant_id == tenant_id,
            KnowledgeDocumentChunk.status == payload.status,
            KnowledgeDocument.status == payload.status,
        )
        .order_by(KnowledgeDocument.id.asc(), KnowledgeDocumentChunk.chunk_index.asc())
    )
    if payload.document_id is not None:
        query = query.where(KnowledgeDocument.id == payload.document_id)

    rows = list(db.execute(query).all())
    failure_reasons: list[str] = []
    reindexed_chunks = 0
    failed_chunks = 0
    now = utc_now()
    for chunk, _document in rows:
        tokens = _tokenize(chunk.content)
        terms = _token_vector(tokens)
        embedding = _embed_text(chunk.content, settings=settings)
        if embedding.status != "indexed" or not embedding.vector:
            failed_chunks += 1
            chunk.vector_index_status = "failed"
            reason = embedding.error_message or embedding.status
            if reason not in failure_reasons:
                failure_reasons.append(reason)
            continue
        chunk.embedding_signature = _embedding_signature(embedding, terms=terms)
        chunk.embedding_vector = embedding.vector
        chunk.embedding_provider = embedding.profile.provider
        chunk.embedding_model = embedding.profile.model
        chunk.embedding_dimension = len(embedding.vector)
        chunk.vector_store = embedding.profile.vector_store
        chunk.vector_index_status = "indexed"
        if _is_pgvector_store(embedding.profile.vector_store):
            _write_pgvector_chunk_vector(db, chunk_id=chunk.id, vector=embedding.vector)
        reindexed_chunks += 1

    add_audit_event(
        db,
        tenant_id=tenant_id,
        actor_id=principal.user.id,
        action="knowledge_vector_index.rebuilt",
        resource_type="knowledge_vector_index",
        resource_id=str(payload.document_id or tenant_id),
        payload={
            "document_id": payload.document_id,
            "status": payload.status,
            "vector_store": profile.vector_store,
            "retrieval_backend": retrieval_backend,
            "embedding_provider": profile.provider,
            "embedding_model": profile.model,
            "embedding_dimension": profile.dimensions,
            "reranker": profile.reranker,
            "total_chunks": len(rows),
            "reindexed_chunks": reindexed_chunks,
            "failed_chunks": failed_chunks,
            "failure_reasons": failure_reasons[:10],
            "rebuilt_at": now.isoformat(),
        },
    )
    db.commit()
    return KnowledgeVectorIndexRebuildRead(
        tenant_id=tenant_id,
        document_id=payload.document_id,
        status=payload.status,
        vector_store=profile.vector_store,
        retrieval_backend=retrieval_backend,
        vector_index_status="failed" if failed_chunks else "indexed",
        embedding_provider=profile.provider,
        embedding_model=profile.model,
        embedding_dimension=profile.dimensions,
        reranker=profile.reranker,
        total_chunks=len(rows),
        reindexed_chunks=reindexed_chunks,
        skipped_chunks=0,
        failed_chunks=failed_chunks,
        failure_reasons=failure_reasons[:10],
    )


def create_knowledge_vector_index_plan(
    db: Session,
    tenant_id: int,
    payload: KnowledgeVectorIndexPlanCreate,
    principal: CurrentPrincipal,
) -> KnowledgeVectorIndexPlanRead:
    _require_same_tenant(db, tenant_id, principal)
    _require_knowledge_manager(principal)
    if not payload.dry_run:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="knowledge vector ANN index execution is not implemented; create a dry-run plan first",
        )
    if payload.document_id is not None:
        document = db.get(KnowledgeDocument, payload.document_id)
        if document is None or document.tenant_id != tenant_id:
            raise HTTPException(status_code=404, detail="knowledge document not found")

    settings = get_settings()
    profile = _resolve_embedding_profile(settings)
    dialect = _database_dialect(db)
    count_query = (
        select(func.count(KnowledgeDocumentChunk.id))
        .join(KnowledgeDocument, KnowledgeDocument.id == KnowledgeDocumentChunk.document_id)
        .where(
            KnowledgeDocumentChunk.tenant_id == tenant_id,
            KnowledgeDocumentChunk.status == payload.status,
            KnowledgeDocument.status == payload.status,
        )
    )
    if payload.document_id is not None:
        count_query = count_query.where(KnowledgeDocument.id == payload.document_id)
    actual_chunk_count = int(db.scalar(count_query) or 0)
    target_chunk_count = (
        payload.target_chunk_count_override
        if payload.target_chunk_count_override is not None
        else actual_chunk_count
    )
    selected_strategy, index_method, retrieval_backend, reasons = _select_vector_index_strategy(
        requested_strategy=payload.requested_strategy,
        vector_store=profile.vector_store,
        database_dialect=dialect,
        target_chunk_count=target_chunk_count,
        embedding_dimension=profile.dimensions,
    )
    plan_status = "blocked" if selected_strategy.startswith("blocked_") else "planned"
    ann_plan = {
        "index_name": "",
        "ddl_statements": [],
        "rollback_statements": [],
        "query_options": {},
        "recommendation_reasons": [],
        "estimated_build_seconds": 0,
        "estimated_memory_mb": 0,
    }
    if index_method in {"hnsw", "ivfflat"} and plan_status == "planned":
        ann_plan = _build_pgvector_ann_index_plan(
            index_method=index_method,
            target_chunk_count=target_chunk_count,
            embedding_provider=profile.provider,
            embedding_model=profile.model,
            embedding_dimension=profile.dimensions,
            concurrent_build=payload.concurrent_build,
            status_filter=payload.status,
        )
        reasons.extend(ann_plan["recommendation_reasons"])

    maintenance_window_required = index_method in {"hnsw", "ivfflat"}
    exceeds_requested_window = (
        ann_plan["estimated_build_seconds"] > payload.max_index_build_seconds
        if maintenance_window_required
        else False
    )
    if exceeds_requested_window:
        reasons.append("Estimated ANN build time exceeds requested max_index_build_seconds; split the rebuild or schedule a larger window.")
    safety_checks = {
        "database_dialect": dialect,
        "postgresql_required": _is_pgvector_store(profile.vector_store),
        "postgresql_available": dialect == "postgresql",
        "external_execution_performed": False,
        "dry_run_only": payload.dry_run,
        "concurrent_build": payload.concurrent_build,
        "actual_chunk_count": actual_chunk_count,
        "target_chunk_count": target_chunk_count,
        "embedding_dimension_supported_for_vector_index": profile.dimensions <= 2000,
        "expression_partial_index_required": _is_pgvector_store(profile.vector_store),
        "requires_recall_evaluation_before_activation": maintenance_window_required,
        "estimated_build_seconds_exceeds_window": exceeds_requested_window,
    }
    now = utc_now()
    plan = KnowledgeVectorIndexPlan(
        tenant_id=tenant_id,
        document_id=payload.document_id,
        status_filter=payload.status,
        plan_status=plan_status,
        requested_strategy=payload.requested_strategy,
        selected_strategy=selected_strategy,
        index_method=index_method,
        index_name=ann_plan["index_name"],
        vector_store=profile.vector_store,
        retrieval_backend=retrieval_backend,
        embedding_provider=profile.provider,
        embedding_model=profile.model,
        embedding_dimension=profile.dimensions,
        target_chunk_count=target_chunk_count,
        estimated_build_seconds=ann_plan["estimated_build_seconds"],
        estimated_memory_mb=ann_plan["estimated_memory_mb"],
        maintenance_window=payload.maintenance_window.strip() or "off_peak",
        maintenance_window_required=maintenance_window_required,
        dry_run=True,
        execute_performed=False,
        concurrent_build=payload.concurrent_build,
        ddl_statements=ann_plan["ddl_statements"],
        rollback_statements=ann_plan["rollback_statements"],
        safety_checks=safety_checks,
        recommendation_reasons=reasons[:20],
        query_options=ann_plan["query_options"],
        created_by_id=principal.user.id,
        created_at=now,
    )
    db.add(plan)
    db.flush()
    add_audit_event(
        db,
        tenant_id=tenant_id,
        actor_id=principal.user.id,
        action="knowledge_vector_index.plan_created",
        resource_type="knowledge_vector_index_plan",
        resource_id=str(plan.id),
        payload={
            "document_id": plan.document_id,
            "status": plan.status_filter,
            "plan_status": plan.plan_status,
            "requested_strategy": plan.requested_strategy,
            "selected_strategy": plan.selected_strategy,
            "index_method": plan.index_method,
            "vector_store": plan.vector_store,
            "retrieval_backend": plan.retrieval_backend,
            "embedding_provider": plan.embedding_provider,
            "embedding_model": plan.embedding_model,
            "embedding_dimension": plan.embedding_dimension,
            "target_chunk_count": plan.target_chunk_count,
            "dry_run": plan.dry_run,
            "execute_performed": plan.execute_performed,
        },
    )
    db.commit()
    db.refresh(plan)
    return KnowledgeVectorIndexPlanRead.model_validate(plan)


def _embedding_provider_smoke_read(
    smoke_run: KnowledgeEmbeddingProviderSmokeRun,
) -> KnowledgeEmbeddingProviderSmokeRead:
    return KnowledgeEmbeddingProviderSmokeRead.model_validate(smoke_run)


def run_knowledge_embedding_provider_smoke(
    db: Session,
    tenant_id: int,
    payload: KnowledgeEmbeddingProviderSmokeCreate,
    principal: CurrentPrincipal,
) -> KnowledgeEmbeddingProviderSmokeRead:
    _require_same_tenant(db, tenant_id, principal)
    _require_knowledge_manager(principal)
    settings = get_settings()
    profile = _resolve_embedding_profile(settings)
    if profile.provider == OPENAI_COMPATIBLE_EMBEDDING_PROVIDER and not payload.allow_external_call:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="allow_external_call=true is required before running external embedding provider smoke",
        )

    sample_text = payload.sample_text.strip()
    embedding = _embed_text(sample_text, settings=settings)
    smoke_status = "succeeded" if embedding.status == "indexed" and embedding.vector else embedding.status
    quality_checks = _embedding_quality_checks(embedding)
    now = utc_now()
    smoke_run = KnowledgeEmbeddingProviderSmokeRun(
        tenant_id=tenant_id,
        status=smoke_status,
        purpose=payload.purpose.strip() or "embedding_provider_smoke",
        privacy_level=payload.privacy_level.strip() or "business_internal_no_pii",
        embedding_provider=embedding.profile.provider,
        embedding_model=embedding.profile.model,
        vector_engine=embedding.profile.vector_engine,
        vector_store=embedding.profile.vector_store,
        embedding_dimension=embedding.profile.dimensions,
        output_dimension=len(embedding.vector),
        input_text_hash=_content_hash(sample_text),
        input_character_count=embedding.input_character_count,
        estimated_input_tokens=embedding.estimated_input_tokens,
        latency_ms=embedding.latency_ms,
        pricing_input_per_1k_tokens=embedding.pricing_input_per_1k_tokens,
        estimated_cost=embedding.estimated_cost,
        cost_currency=embedding.cost_currency,
        provider_call_performed=embedding.provider_call_performed,
        raw_text_logged=False,
        quality_checks=quality_checks,
        response_metadata=embedding.response_metadata or {},
        error_message=embedding.error_message,
        created_by_id=principal.user.id,
        created_at=now,
    )
    db.add(smoke_run)
    db.flush()
    add_audit_event(
        db,
        tenant_id=tenant_id,
        actor_id=principal.user.id,
        action="knowledge_embedding_provider_smoke.created",
        resource_type="knowledge_embedding_provider_smoke_run",
        resource_id=str(smoke_run.id),
        payload={
            "status": smoke_run.status,
            "purpose": smoke_run.purpose,
            "privacy_level": smoke_run.privacy_level,
            "embedding_provider": smoke_run.embedding_provider,
            "embedding_model": smoke_run.embedding_model,
            "vector_engine": smoke_run.vector_engine,
            "vector_store": smoke_run.vector_store,
            "output_dimension": smoke_run.output_dimension,
            "estimated_input_tokens": smoke_run.estimated_input_tokens,
            "latency_ms": smoke_run.latency_ms,
            "estimated_cost": smoke_run.estimated_cost,
            "cost_currency": smoke_run.cost_currency,
            "provider_call_performed": smoke_run.provider_call_performed,
            "raw_text_logged": smoke_run.raw_text_logged,
            "quality_checks": smoke_run.quality_checks,
        },
    )
    db.commit()
    db.refresh(smoke_run)
    return _embedding_provider_smoke_read(smoke_run)


def create_knowledge_evaluation_set(
    db: Session,
    tenant_id: int,
    payload: KnowledgeEvaluationSetCreate,
    principal: CurrentPrincipal,
) -> KnowledgeEvaluationSetRead:
    _require_same_tenant(db, tenant_id, principal)
    _require_knowledge_manager(principal)
    now = utc_now()
    evaluation_set = KnowledgeEvaluationSet(
        tenant_id=tenant_id,
        name=payload.name.strip(),
        description=payload.description.strip(),
        status=payload.status,
        evaluation_mode=payload.evaluation_mode,
        created_by_id=principal.user.id,
        updated_by_id=principal.user.id,
        created_at=now,
        updated_at=now,
    )
    db.add(evaluation_set)
    db.flush()
    for item in payload.cases:
        db.add(
            KnowledgeEvaluationCase(
                tenant_id=tenant_id,
                evaluation_set_id=evaluation_set.id,
                external_case_id=item.external_case_id.strip(),
                source_channel=item.source_channel.strip(),
                source_category=item.source_category.strip(),
                question=item.question.strip(),
                question_type=item.question_type.strip() or "standard_customer_question",
                expected_terms=_clean_string_list(item.expected_terms),
                expected_source_uri=item.expected_source_uri.strip(),
                expected_document_title=item.expected_document_title.strip(),
                expected_chunk_ids=_clean_int_list(item.expected_chunk_ids),
                must_have_all_evidence=item.must_have_all_evidence,
                expected_human_review=item.expected_human_review,
                allow_auto_reply=item.allow_auto_reply,
                forbidden_terms=_clean_string_list(item.forbidden_terms),
                risk_level=item.risk_level.strip() or "low",
                annotation_notes=item.annotation_notes.strip(),
                required_citation=item.required_citation,
                priority=item.priority,
                status=item.status,
                created_at=now,
            )
        )
    add_audit_event(
        db,
        tenant_id=tenant_id,
        actor_id=principal.user.id,
        action="knowledge_evaluation_set.created",
        resource_type="knowledge_evaluation_set",
        resource_id=str(evaluation_set.id),
        payload={
            "name": evaluation_set.name,
            "status": evaluation_set.status,
            "evaluation_mode": evaluation_set.evaluation_mode,
            "case_count": len(payload.cases),
        },
    )
    db.commit()
    db.refresh(evaluation_set)
    return _evaluation_set_read(db, evaluation_set)


def _normalized_lookup_key(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().lower())


def _knowledge_update_package_row_count(package: KnowledgeUpdatePackagePayload) -> int:
    return (
        len(package.knowledge_cards)
        + len(package.business_objects)
        + len(package.object_knowledge_cards)
        + len(package.knowledge_documents)
        + len(package.evaluation_sets)
    )


def _knowledge_update_backup_snapshot(db: Session, tenant_id: int) -> dict:
    return {
        "created_at": utc_now().isoformat(),
        "scope": "pre_import_counts_only",
        "counts": {
            "knowledge_cards": int(
                db.scalar(select(func.count(KnowledgeCard.id)).where(KnowledgeCard.tenant_id == tenant_id)) or 0
            ),
            "business_objects": int(
                db.scalar(select(func.count(BusinessObject.id)).where(BusinessObject.tenant_id == tenant_id)) or 0
            ),
            "object_knowledge_cards": int(
                db.scalar(
                    select(func.count(ObjectKnowledgeCard.id)).where(ObjectKnowledgeCard.tenant_id == tenant_id)
                )
                or 0
            ),
            "knowledge_documents": int(
                db.scalar(select(func.count(KnowledgeDocument.id)).where(KnowledgeDocument.tenant_id == tenant_id))
                or 0
            ),
            "evaluation_sets": int(
                db.scalar(
                    select(func.count(KnowledgeEvaluationSet.id)).where(KnowledgeEvaluationSet.tenant_id == tenant_id)
                )
                or 0
            ),
        },
    }


def _existing_business_object_for_package(
    db: Session,
    tenant_id: int,
    *,
    object_type: str,
    title: str,
    external_id: str = "",
) -> BusinessObject | None:
    objects = list(
        db.scalars(
            select(BusinessObject).where(
                BusinessObject.tenant_id == tenant_id,
                BusinessObject.type == object_type,
                BusinessObject.status != "archived",
            )
        ).all()
    )
    normalized_title = _normalized_lookup_key(title)
    normalized_external_id = external_id.strip()
    for item in objects:
        if normalized_external_id and item.external_id == normalized_external_id:
            return item
        if _normalized_lookup_key(item.title) == normalized_title:
            return item
    return None


def _existing_knowledge_card_for_package(db: Session, tenant_id: int, payload: KnowledgeCardCreate) -> KnowledgeCard | None:
    normalized_title = _normalized_lookup_key(payload.title)
    normalized_question = _normalized_lookup_key(payload.question)
    cards = list(
        db.scalars(
            select(KnowledgeCard).where(
                KnowledgeCard.tenant_id == tenant_id,
                KnowledgeCard.status != "archived",
            )
        ).all()
    )
    for card in cards:
        if _normalized_lookup_key(card.title) == normalized_title and _normalized_lookup_key(card.question) == normalized_question:
            return card
    return None


def _existing_object_knowledge_card_for_package(
    db: Session,
    tenant_id: int,
    *,
    business_object_id: int,
    question: str,
) -> ObjectKnowledgeCard | None:
    normalized_question = _normalized_lookup_key(question)
    cards = list(
        db.scalars(
            select(ObjectKnowledgeCard).where(
                ObjectKnowledgeCard.tenant_id == tenant_id,
                ObjectKnowledgeCard.business_object_id == business_object_id,
                ObjectKnowledgeCard.status != "archived",
            )
        ).all()
    )
    for card in cards:
        if _normalized_lookup_key(card.question) == normalized_question:
            return card
    return None


def _existing_knowledge_document_for_package(
    db: Session,
    tenant_id: int,
    payload: KnowledgeDocumentCreate,
) -> KnowledgeDocument | None:
    content_hash = _content_hash(payload.raw_text.strip())
    documents = list(
        db.scalars(
            select(KnowledgeDocument).where(
                KnowledgeDocument.tenant_id == tenant_id,
                KnowledgeDocument.status != "archived",
            )
        ).all()
    )
    normalized_title = _normalized_lookup_key(payload.title)
    source_uri = payload.source_uri.strip()
    for document in documents:
        if document.content_hash == content_hash:
            return document
        if (
            source_uri
            and document.source_uri == source_uri
            and _normalized_lookup_key(document.title) == normalized_title
        ):
            return document
    return None


def _existing_evaluation_set_for_package(
    db: Session,
    tenant_id: int,
    payload: KnowledgeEvaluationSetCreate,
) -> KnowledgeEvaluationSet | None:
    normalized_name = _normalized_lookup_key(payload.name)
    evaluation_sets = list(
        db.scalars(
            select(KnowledgeEvaluationSet).where(
                KnowledgeEvaluationSet.tenant_id == tenant_id,
                KnowledgeEvaluationSet.status != "archived",
            )
        ).all()
    )
    for evaluation_set in evaluation_sets:
        if _normalized_lookup_key(evaluation_set.name) == normalized_name:
            return evaluation_set
    return None


def _package_business_object_ref_map(
    db: Session,
    tenant_id: int,
    package: KnowledgeUpdatePackagePayload,
) -> dict[str, dict]:
    ref_map: dict[str, dict] = {}
    for item in package.business_objects:
        ref = item.ref.strip()
        if not ref:
            continue
        existing = _existing_business_object_for_package(
            db,
            tenant_id,
            object_type=item.type,
            title=item.title,
            external_id=item.external_id,
        )
        ref_map[ref] = {
            "existing_id": existing.id if existing else None,
            "pending": existing is None,
            "type": item.type,
            "title": item.title.strip(),
        }
    return ref_map


def _resolve_package_object_card_target(
    db: Session,
    tenant_id: int,
    package: KnowledgeUpdatePackagePayload,
    card_payload,
) -> dict:
    ref_map = _package_business_object_ref_map(db, tenant_id, package)
    if card_payload.business_object_id:
        existing = db.get(BusinessObject, card_payload.business_object_id)
        if existing and existing.tenant_id == tenant_id and existing.status != "archived":
            return {"business_object_id": existing.id, "pending": False, "title": existing.title, "ref": ""}
        return {"error": "business_object_id not found"}
    ref = card_payload.business_object_ref.strip()
    if ref:
        target = ref_map.get(ref)
        if target:
            return {"business_object_id": target["existing_id"], "pending": target["pending"], "title": target["title"], "ref": ref}
        return {"error": "business_object_ref not found", "ref": ref}
    title = card_payload.business_object_title.strip()
    object_type = card_payload.business_object_type.strip()
    if title and object_type:
        existing = _existing_business_object_for_package(
            db,
            tenant_id,
            object_type=object_type,
            title=title,
        )
        if existing:
            return {"business_object_id": existing.id, "pending": False, "title": existing.title, "ref": ""}
    return {"error": "business object target is required"}


def _knowledge_update_package_operation_counts(operations: list[KnowledgeUpdatePackageOperationRead]) -> dict[str, int]:
    counts = {"create": 0, "skip": 0, "error": 0}
    for operation in operations:
        if operation.action in counts:
            counts[operation.action] += 1
    return counts


def _knowledge_update_safety(*, provider_call_performed: bool = False) -> dict:
    return {
        "external_write_performed": False,
        "provider_call_performed": provider_call_performed,
        "raw_document_text_included_in_response": False,
        "default_external_model_calls_blocked": True,
        "rollback_supported": True,
    }


def _analyze_knowledge_update_package(
    db: Session,
    tenant_id: int,
    package: KnowledgeUpdatePackagePayload,
) -> tuple[list[KnowledgeUpdatePackageOperationRead], list[dict], list[dict], list[str]]:
    operations: list[KnowledgeUpdatePackageOperationRead] = []
    skipped: list[dict] = []
    errors: list[dict] = []
    warnings: list[str] = []

    def add_operation(action: str, resource_type: str, title: str, reason: str, *, ref: str = "", target: dict | None = None) -> None:
        operations.append(
            KnowledgeUpdatePackageOperationRead(
                action=action,
                resource_type=resource_type,
                title=_short_excerpt(title, limit=120),
                reason=reason,
                ref=ref,
                target=target or {},
            )
        )
        if action == "skip":
            skipped.append({"resource_type": resource_type, "title": _short_excerpt(title, limit=120), "reason": reason})
        if action == "error":
            errors.append({"resource_type": resource_type, "title": _short_excerpt(title, limit=120), "reason": reason})

    if package.schema_version != KNOWLEDGE_UPDATE_PACKAGE_SCHEMA_VERSION:
        add_operation(
            "error",
            "package",
            package.package_name,
            f"unsupported schema_version: {package.schema_version}",
        )
        return operations, skipped, errors, warnings

    seen_refs: set[str] = set()
    for item in package.business_objects:
        ref = item.ref.strip()
        if ref:
            if ref in seen_refs:
                add_operation("error", "business_object", item.title, "duplicate business_object ref", ref=ref)
                continue
            seen_refs.add(ref)
        existing = _existing_business_object_for_package(
            db,
            tenant_id,
            object_type=item.type,
            title=item.title,
            external_id=item.external_id,
        )
        if existing:
            add_operation(
                "skip",
                "business_object",
                item.title,
                "same business object already exists",
                ref=ref,
                target={"business_object_id": existing.id},
            )
        else:
            add_operation("create", "business_object", item.title, "new business object", ref=ref)

    for item in package.knowledge_cards:
        existing = _existing_knowledge_card_for_package(db, tenant_id, item)
        if existing:
            add_operation(
                "skip",
                "knowledge_card",
                item.title,
                "same FAQ card already exists",
                target={"knowledge_card_id": existing.id},
            )
        else:
            add_operation("create", "knowledge_card", item.title, "new FAQ card")

    for item in package.object_knowledge_cards:
        target = _resolve_package_object_card_target(db, tenant_id, package, item)
        if target.get("error"):
            add_operation("error", "object_knowledge_card", item.question, target["error"], ref=target.get("ref", ""))
            continue
        business_object_id = target.get("business_object_id")
        if business_object_id:
            existing = _existing_object_knowledge_card_for_package(
                db,
                tenant_id,
                business_object_id=business_object_id,
                question=item.question,
            )
            if existing:
                add_operation(
                    "skip",
                    "object_knowledge_card",
                    item.question,
                    "same object Q&A card already exists",
                    ref=target.get("ref", ""),
                    target={"business_object_id": business_object_id, "object_knowledge_card_id": existing.id},
                )
                continue
        add_operation(
            "create",
            "object_knowledge_card",
            item.question,
            "new object Q&A card",
            ref=target.get("ref", ""),
            target={
                "business_object_id": business_object_id,
                "business_object_ref": target.get("ref", ""),
                "target_pending_create": bool(target.get("pending")),
            },
        )

    for item in package.knowledge_documents:
        if not item.raw_text.strip():
            add_operation("error", "knowledge_document", item.title, "document raw_text is empty after trimming")
            continue
        existing = _existing_knowledge_document_for_package(db, tenant_id, item)
        if existing:
            add_operation(
                "skip",
                "knowledge_document",
                item.title,
                "same document already exists",
                target={"knowledge_document_id": existing.id},
            )
        else:
            add_operation("create", "knowledge_document", item.title, "new knowledge document")

    for item in package.evaluation_sets:
        existing = _existing_evaluation_set_for_package(db, tenant_id, item)
        if existing:
            add_operation(
                "skip",
                "evaluation_set",
                item.name,
                "same evaluation set already exists",
                target={"evaluation_set_id": existing.id},
            )
        else:
            add_operation("create", "evaluation_set", item.name, "new evaluation set")

    if package.knowledge_documents:
        profile = _resolve_embedding_profile(get_settings())
        if profile.provider != DETERMINISTIC_EMBEDDING_PROVIDER:
            warnings.append("external embedding provider is configured; import will require explicit future authorization")
    return operations, skipped, errors, warnings


def _knowledge_update_package_result(
    *,
    tenant_id: int,
    package: KnowledgeUpdatePackagePayload,
    dry_run: bool,
    import_batch_id: int | None,
    operations: list[KnowledgeUpdatePackageOperationRead],
    created: dict[str, list[int]] | None = None,
    skipped: list[dict] | None = None,
    errors: list[dict] | None = None,
    warnings: list[str] | None = None,
    backup_snapshot: dict | None = None,
    provider_call_performed: bool = False,
) -> KnowledgeUpdatePackageResultRead:
    operation_counts = _knowledge_update_package_operation_counts(operations)
    error_items = errors or []
    return KnowledgeUpdatePackageResultRead(
        tenant_id=tenant_id,
        package_id=package.package_id,
        package_name=package.package_name,
        schema_version=package.schema_version,
        dry_run=dry_run,
        can_apply=not error_items,
        import_batch_id=import_batch_id,
        operation_counts=operation_counts,
        operations=operations,
        created=created
        or {
            "knowledge_cards": [],
            "business_objects": [],
            "object_knowledge_cards": [],
            "knowledge_documents": [],
            "evaluation_sets": [],
        },
        skipped=skipped or [],
        errors=error_items,
        warnings=warnings or [],
        backup_snapshot=backup_snapshot or {},
        safety=_knowledge_update_safety(provider_call_performed=provider_call_performed),
    )


def preview_knowledge_update_package(
    db: Session,
    tenant_id: int,
    payload: KnowledgeUpdatePackagePreviewCreate,
    principal: CurrentPrincipal,
) -> KnowledgeUpdatePackageResultRead:
    _require_same_tenant(db, tenant_id, principal)
    _require_knowledge_manager(principal)
    operations, skipped, errors, warnings = _analyze_knowledge_update_package(db, tenant_id, payload.package)
    return _knowledge_update_package_result(
        tenant_id=tenant_id,
        package=payload.package,
        dry_run=True,
        import_batch_id=None,
        operations=operations,
        skipped=skipped,
        errors=errors,
        warnings=warnings,
        backup_snapshot=_knowledge_update_backup_snapshot(db, tenant_id),
    )


def _create_knowledge_document_from_package(
    db: Session,
    tenant_id: int,
    payload: KnowledgeDocumentCreate,
    principal: CurrentPrincipal,
    *,
    now,
) -> KnowledgeDocument:
    raw_text = payload.raw_text.strip()
    settings = get_settings()
    profile = _resolve_embedding_profile(settings)
    if profile.provider != DETERMINISTIC_EMBEDDING_PROVIDER:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="knowledge update package import only allows deterministic local embeddings in this slice",
        )
    _require_vector_store_available(profile, db)
    chunks = _split_document_chunks(raw_text, chunk_size=payload.chunk_size, chunk_overlap=payload.chunk_overlap)
    chunk_embeddings: list[tuple[dict, list[str], EmbeddingResult]] = []
    for chunk_data in chunks:
        tokens = _tokenize(chunk_data["content"])
        embedding = _embed_text(chunk_data["content"], settings=settings)
        _require_embedding_available(embedding)
        chunk_embeddings.append((chunk_data, tokens, embedding))

    document = KnowledgeDocument(
        tenant_id=tenant_id,
        title=payload.title.strip(),
        source_type=payload.source_type.strip() or "knowledge_update_package",
        source_uri=payload.source_uri.strip(),
        raw_text=raw_text,
        content_hash=_content_hash(raw_text),
        tags=_clean_string_list(payload.tags),
        status=payload.status,
        ingestion_status="indexing",
        chunk_count=0,
        created_by_id=principal.user.id,
        updated_by_id=principal.user.id,
        created_at=now,
        updated_at=now,
    )
    db.add(document)
    db.flush()
    for index, (chunk_data, tokens, embedding) in enumerate(chunk_embeddings):
        terms = _token_vector(tokens)
        chunk = KnowledgeDocumentChunk(
            tenant_id=tenant_id,
            document_id=document.id,
            chunk_index=index,
            section_title=chunk_data["section_title"][:180],
            page_number=None,
            content=chunk_data["content"],
            content_hash=_content_hash(chunk_data["content"]),
            source_uri=document.source_uri,
            char_start=chunk_data["char_start"],
            char_end=chunk_data["char_end"],
            token_count=len(tokens),
            embedding_signature=_embedding_signature(embedding, terms=terms),
            embedding_vector=embedding.vector,
            embedding_provider=embedding.profile.provider,
            embedding_model=embedding.profile.model,
            embedding_dimension=len(embedding.vector),
            vector_store=embedding.profile.vector_store,
            vector_index_status=embedding.status,
            status=payload.status,
            created_at=now,
        )
        db.add(chunk)
        db.flush()
        if _is_pgvector_store(embedding.profile.vector_store):
            _write_pgvector_chunk_vector(db, chunk_id=chunk.id, vector=embedding.vector)
    document.chunk_count = len(chunks)
    document.ingestion_status = "indexed"
    document.updated_at = now
    return document


def import_knowledge_update_package(
    db: Session,
    tenant_id: int,
    payload: KnowledgeUpdatePackageImportCreate,
    principal: CurrentPrincipal,
) -> KnowledgeUpdatePackageResultRead:
    _require_same_tenant(db, tenant_id, principal)
    _require_knowledge_manager(principal)
    operations, skipped, errors, warnings = _analyze_knowledge_update_package(db, tenant_id, payload.package)
    if errors:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={"errors": errors})
    if payload.package.knowledge_documents:
        profile = _resolve_embedding_profile(get_settings())
        if profile.provider != DETERMINISTIC_EMBEDDING_PROVIDER:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="knowledge update package import only allows deterministic local embeddings in this slice",
            )

    backup_snapshot = _knowledge_update_backup_snapshot(db, tenant_id)
    now = utc_now()
    batch = KnowledgeImportBatch(
        tenant_id=tenant_id,
        source_file_ref=payload.package.source_diagnostic_filename.strip(),
        object_type="knowledge_update_package",
        row_count=_knowledge_update_package_row_count(payload.package),
        valid_count=0,
        error_count=0,
        status="processing",
        result_payload={
            "package_id": payload.package.package_id,
            "package_name": payload.package.package_name,
            "schema_version": payload.package.schema_version,
            "rollback_status": "pending",
        },
        created_by_id=principal.user.id,
        created_at=now,
    )
    db.add(batch)
    db.flush()

    created = {
        "knowledge_cards": [],
        "business_objects": [],
        "object_knowledge_cards": [],
        "knowledge_documents": [],
        "evaluation_sets": [],
    }
    ref_to_business_object_id: dict[str, int] = {}

    for item in payload.package.business_objects:
        existing = _existing_business_object_for_package(
            db,
            tenant_id,
            object_type=item.type,
            title=item.title,
            external_id=item.external_id,
        )
        if existing:
            if item.ref.strip():
                ref_to_business_object_id[item.ref.strip()] = existing.id
            continue
        business_object = BusinessObject(
            tenant_id=tenant_id,
            type=item.type,
            title=item.title.strip(),
            external_id=item.external_id.strip(),
            summary=item.summary.strip(),
            attrs_json=item.attrs_json,
            status=item.status,
            created_by_id=principal.user.id,
            updated_by_id=principal.user.id,
            created_at=now,
            updated_at=now,
        )
        db.add(business_object)
        db.flush()
        created["business_objects"].append(business_object.id)
        if item.ref.strip():
            ref_to_business_object_id[item.ref.strip()] = business_object.id
        for alias in _clean_string_list(item.aliases):
            db.add(
                BusinessObjectAlias(
                    tenant_id=tenant_id,
                    business_object_id=business_object.id,
                    alias=alias,
                    channel_scope="all",
                    created_at=now,
                )
            )

    for item in payload.package.knowledge_cards:
        if _existing_knowledge_card_for_package(db, tenant_id, item):
            continue
        card = KnowledgeCard(
            tenant_id=tenant_id,
            title=item.title.strip(),
            question=item.question.strip(),
            answer=item.answer.strip(),
            source_type=item.source_type.strip() or "knowledge_update_package",
            source_uri=item.source_uri.strip(),
            tags=_clean_string_list(item.tags),
            aliases=_clean_string_list(item.aliases),
            status=item.status,
            created_by_id=principal.user.id,
            updated_by_id=principal.user.id,
            created_at=now,
            updated_at=now,
        )
        db.add(card)
        db.flush()
        created["knowledge_cards"].append(card.id)

    for item in payload.package.object_knowledge_cards:
        business_object_id = item.business_object_id
        if not business_object_id and item.business_object_ref.strip():
            business_object_id = ref_to_business_object_id.get(item.business_object_ref.strip())
        if not business_object_id and item.business_object_title.strip() and item.business_object_type.strip():
            existing_object = _existing_business_object_for_package(
                db,
                tenant_id,
                object_type=item.business_object_type.strip(),
                title=item.business_object_title.strip(),
            )
            business_object_id = existing_object.id if existing_object else None
        if not business_object_id:
            continue
        if _existing_object_knowledge_card_for_package(
            db,
            tenant_id,
            business_object_id=business_object_id,
            question=item.question,
        ):
            continue
        card = ObjectKnowledgeCard(
            tenant_id=tenant_id,
            business_object_id=business_object_id,
            question=item.question.strip(),
            answer=item.answer.strip(),
            trigger_keywords=_clean_string_list(item.trigger_keywords),
            media_refs=_clean_string_list(item.media_refs),
            scope=item.scope,
            source=item.source.strip() or "knowledge_update_package",
            version=item.version,
            status=item.status,
            created_by_id=principal.user.id,
            updated_by_id=principal.user.id,
            created_at=now,
            updated_at=now,
        )
        db.add(card)
        db.flush()
        created["object_knowledge_cards"].append(card.id)

    for item in payload.package.knowledge_documents:
        if _existing_knowledge_document_for_package(db, tenant_id, item):
            continue
        document = _create_knowledge_document_from_package(db, tenant_id, item, principal, now=now)
        created["knowledge_documents"].append(document.id)

    for item in payload.package.evaluation_sets:
        if _existing_evaluation_set_for_package(db, tenant_id, item):
            continue
        evaluation_set = KnowledgeEvaluationSet(
            tenant_id=tenant_id,
            name=item.name.strip(),
            description=item.description.strip(),
            status=item.status,
            evaluation_mode=item.evaluation_mode,
            created_by_id=principal.user.id,
            updated_by_id=principal.user.id,
            created_at=now,
            updated_at=now,
        )
        db.add(evaluation_set)
        db.flush()
        created["evaluation_sets"].append(evaluation_set.id)
        for case in item.cases:
            db.add(
                KnowledgeEvaluationCase(
                    tenant_id=tenant_id,
                    evaluation_set_id=evaluation_set.id,
                    external_case_id=case.external_case_id.strip(),
                    source_channel=case.source_channel.strip(),
                    source_category=case.source_category.strip(),
                    question=case.question.strip(),
                    question_type=case.question_type.strip() or "standard_customer_question",
                    expected_terms=_clean_string_list(case.expected_terms),
                    expected_source_uri=case.expected_source_uri.strip(),
                    expected_document_title=case.expected_document_title.strip(),
                    expected_chunk_ids=_clean_int_list(case.expected_chunk_ids),
                    must_have_all_evidence=case.must_have_all_evidence,
                    expected_human_review=case.expected_human_review,
                    allow_auto_reply=case.allow_auto_reply,
                    forbidden_terms=_clean_string_list(case.forbidden_terms),
                    risk_level=case.risk_level.strip() or "low",
                    annotation_notes=case.annotation_notes.strip(),
                    required_citation=case.required_citation,
                    priority=case.priority,
                    status=case.status,
                    created_at=now,
                )
            )

    operation_counts = _knowledge_update_package_operation_counts(operations)
    batch.valid_count = operation_counts["create"]
    batch.error_count = 0
    batch.status = "applied"
    batch.result_payload = {
        "package_id": payload.package.package_id,
        "package_name": payload.package.package_name,
        "schema_version": payload.package.schema_version,
        "operation_counts": operation_counts,
        "created": created,
        "skipped": skipped,
        "backup_snapshot": backup_snapshot,
        "rollback_status": "available",
        "safety": _knowledge_update_safety(provider_call_performed=False),
    }
    add_audit_event(
        db,
        tenant_id=tenant_id,
        actor_id=principal.user.id,
        action="knowledge_update_package.imported",
        resource_type="knowledge_import_batch",
        resource_id=str(batch.id),
        payload={
            "package_id": payload.package.package_id,
            "package_name": payload.package.package_name,
            "operation_counts": operation_counts,
            "created_counts": {key: len(value) for key, value in created.items()},
            "external_write_performed": False,
            "provider_call_performed": False,
        },
    )
    db.commit()
    return _knowledge_update_package_result(
        tenant_id=tenant_id,
        package=payload.package,
        dry_run=False,
        import_batch_id=batch.id,
        operations=operations,
        created=created,
        skipped=skipped,
        errors=[],
        warnings=warnings,
        backup_snapshot=backup_snapshot,
        provider_call_performed=False,
    )


def rollback_knowledge_update_package_import(
    db: Session,
    batch_id: int,
    payload: KnowledgeUpdatePackageRollbackCreate,
    principal: CurrentPrincipal,
) -> KnowledgeUpdatePackageRollbackRead:
    _require_knowledge_manager(principal)
    batch = db.get(KnowledgeImportBatch, batch_id)
    if batch is None or batch.tenant_id != principal.tenant.id or batch.object_type != "knowledge_update_package":
        raise HTTPException(status_code=404, detail="knowledge update package import not found")
    result_payload = batch.result_payload or {}
    if result_payload.get("rollback_status") == "rolled_back":
        return KnowledgeUpdatePackageRollbackRead(
            tenant_id=batch.tenant_id,
            import_batch_id=batch.id,
            rollback_status="rolled_back",
            archived_counts=result_payload.get("archived_counts", {}),
            reason=result_payload.get("rollback_reason", payload.reason),
            safety=_knowledge_update_safety(provider_call_performed=False),
        )
    created = result_payload.get("created") or {}
    now = utc_now()
    archived_counts = {
        "knowledge_cards": 0,
        "business_objects": 0,
        "object_knowledge_cards": 0,
        "knowledge_documents": 0,
        "evaluation_sets": 0,
    }

    for card in db.scalars(
        select(KnowledgeCard).where(
            KnowledgeCard.tenant_id == batch.tenant_id,
            KnowledgeCard.id.in_(created.get("knowledge_cards") or [-1]),
        )
    ).all():
        card.status = "archived"
        card.updated_by_id = principal.user.id
        card.updated_at = now
        archived_counts["knowledge_cards"] += 1

    for card in db.scalars(
        select(ObjectKnowledgeCard).where(
            ObjectKnowledgeCard.tenant_id == batch.tenant_id,
            ObjectKnowledgeCard.id.in_(created.get("object_knowledge_cards") or [-1]),
        )
    ).all():
        card.status = "archived"
        card.updated_by_id = principal.user.id
        card.updated_at = now
        archived_counts["object_knowledge_cards"] += 1

    for document in db.scalars(
        select(KnowledgeDocument).where(
            KnowledgeDocument.tenant_id == batch.tenant_id,
            KnowledgeDocument.id.in_(created.get("knowledge_documents") or [-1]),
        )
    ).all():
        document.status = "archived"
        document.updated_by_id = principal.user.id
        document.updated_at = now
        archived_counts["knowledge_documents"] += 1
        for chunk in db.scalars(
            select(KnowledgeDocumentChunk).where(
                KnowledgeDocumentChunk.tenant_id == batch.tenant_id,
                KnowledgeDocumentChunk.document_id == document.id,
            )
        ).all():
            chunk.status = "archived"

    for evaluation_set in db.scalars(
        select(KnowledgeEvaluationSet).where(
            KnowledgeEvaluationSet.tenant_id == batch.tenant_id,
            KnowledgeEvaluationSet.id.in_(created.get("evaluation_sets") or [-1]),
        )
    ).all():
        evaluation_set.status = "archived"
        evaluation_set.updated_by_id = principal.user.id
        evaluation_set.updated_at = now
        archived_counts["evaluation_sets"] += 1
        for case in db.scalars(
            select(KnowledgeEvaluationCase).where(
                KnowledgeEvaluationCase.tenant_id == batch.tenant_id,
                KnowledgeEvaluationCase.evaluation_set_id == evaluation_set.id,
            )
        ).all():
            case.status = "archived"

    for business_object in db.scalars(
        select(BusinessObject).where(
            BusinessObject.tenant_id == batch.tenant_id,
            BusinessObject.id.in_(created.get("business_objects") or [-1]),
        )
    ).all():
        business_object.status = "archived"
        business_object.updated_by_id = principal.user.id
        business_object.updated_at = now
        archived_counts["business_objects"] += 1

    batch.status = "rolled_back"
    result_payload["rollback_status"] = "rolled_back"
    result_payload["rollback_reason"] = payload.reason.strip()
    result_payload["rolled_back_at"] = now.isoformat()
    result_payload["archived_counts"] = archived_counts
    batch.result_payload = result_payload
    add_audit_event(
        db,
        tenant_id=batch.tenant_id,
        actor_id=principal.user.id,
        action="knowledge_update_package.rollback",
        resource_type="knowledge_import_batch",
        resource_id=str(batch.id),
        payload={
            "package_id": result_payload.get("package_id", ""),
            "archived_counts": archived_counts,
            "external_write_performed": False,
            "provider_call_performed": False,
        },
    )
    db.commit()
    return KnowledgeUpdatePackageRollbackRead(
        tenant_id=batch.tenant_id,
        import_batch_id=batch.id,
        rollback_status="rolled_back",
        archived_counts=archived_counts,
        reason=payload.reason.strip(),
        safety=_knowledge_update_safety(provider_call_performed=False),
    )


def list_knowledge_evaluation_sets(
    db: Session,
    tenant_id: int,
    *,
    status_filter: str | None,
    page: int,
    page_size: int,
    principal: CurrentPrincipal,
) -> KnowledgeEvaluationSetList:
    _require_same_tenant(db, tenant_id, principal)
    query = select(KnowledgeEvaluationSet).where(KnowledgeEvaluationSet.tenant_id == tenant_id)
    count_query = select(func.count(KnowledgeEvaluationSet.id)).where(
        KnowledgeEvaluationSet.tenant_id == tenant_id
    )
    if status_filter:
        query = query.where(KnowledgeEvaluationSet.status == status_filter)
        count_query = count_query.where(KnowledgeEvaluationSet.status == status_filter)
    query = query.order_by(KnowledgeEvaluationSet.updated_at.desc(), KnowledgeEvaluationSet.id.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    return KnowledgeEvaluationSetList(
        items=[_evaluation_set_read(db, item) for item in db.scalars(query).all()],
        page=page,
        page_size=page_size,
        total=int(db.scalar(count_query) or 0),
    )


def _case_expected_terms_found(case: KnowledgeEvaluationCase, haystack: str, matched_terms: list[str]) -> bool:
    terms = _clean_string_list(case.expected_terms)
    if not terms:
        return True
    normalized_haystack = haystack.lower()
    normalized_matched = {term.lower() for term in matched_terms}
    return all(term.lower() in normalized_haystack or term.lower() in normalized_matched for term in terms)


def _case_source_covered(case: KnowledgeEvaluationCase, match: KnowledgeDocumentSearchMatch | None) -> bool:
    if not case.expected_source_uri:
        return True
    if match is None:
        return False
    citation_source_uri = ""
    if isinstance(match.citation, dict):
        citation_source_uri = str(match.citation.get("source_uri") or "")
    return case.expected_source_uri in {match.source_uri, citation_source_uri}


def _case_document_covered(case: KnowledgeEvaluationCase, match: KnowledgeDocumentSearchMatch | None) -> bool:
    if not case.expected_document_title:
        return True
    return match is not None and match.document_title == case.expected_document_title


def _case_expected_chunk_ids(case: KnowledgeEvaluationCase) -> list[int]:
    values = case.expected_chunk_ids if isinstance(case.expected_chunk_ids, list) else []
    return _clean_int_list(values)


def _case_returned_chunk_ids(matches: list[KnowledgeDocumentSearchMatch]) -> list[int]:
    return [match.chunk_id for match in matches]


def _case_full_evidence_recalled(
    case: KnowledgeEvaluationCase,
    matches: list[KnowledgeDocumentSearchMatch],
) -> bool:
    expected_chunk_ids = _case_expected_chunk_ids(case)
    if not expected_chunk_ids:
        return True
    returned_chunk_ids = set(_case_returned_chunk_ids(matches))
    return all(chunk_id in returned_chunk_ids for chunk_id in expected_chunk_ids)


def _case_citation_precision(
    case: KnowledgeEvaluationCase,
    matches: list[KnowledgeDocumentSearchMatch],
) -> float | None:
    if not matches:
        return None
    expected_chunk_ids = set(_case_expected_chunk_ids(case))
    relevant_matches = 0
    for match in matches:
        citation_source_uri = ""
        if isinstance(match.citation, dict):
            citation_source_uri = str(match.citation.get("source_uri") or "")
        if expected_chunk_ids and match.chunk_id in expected_chunk_ids:
            relevant_matches += 1
            continue
        if case.expected_source_uri and case.expected_source_uri in {match.source_uri, citation_source_uri}:
            relevant_matches += 1
            continue
        if case.expected_document_title and match.document_title == case.expected_document_title:
            relevant_matches += 1
    return round(relevant_matches / len(matches), 4)


def _case_forbidden_term_hits(
    case: KnowledgeEvaluationCase,
    matches: list[KnowledgeDocumentSearchMatch],
) -> list[str]:
    forbidden_terms = _clean_string_list(case.forbidden_terms if isinstance(case.forbidden_terms, list) else [])
    if not forbidden_terms or not matches:
        return []
    haystack = "\n".join(
        [
            " ".join(
                [
                    match.document_title,
                    match.source_uri,
                    match.section_title,
                    match.content_preview,
                    " ".join(match.matched_terms),
                ]
            )
            for match in matches
        ]
    ).lower()
    return [term for term in forbidden_terms if term.lower() in haystack]


def _case_failure_reason(
    *,
    case: KnowledgeEvaluationCase,
    match: KnowledgeDocumentSearchMatch | None,
    citation_present: bool,
    expected_terms_found: bool,
    source_covered: bool,
    document_covered: bool,
    full_evidence_recalled: bool,
    forbidden_term_hits: list[str],
    low_confidence_threshold: float,
) -> str:
    if match is None:
        return "no_retrieval_hit"
    if not case.allow_auto_reply:
        return "auto_reply_not_allowed"
    if forbidden_term_hits:
        return "forbidden_terms_in_evidence"
    if case.must_have_all_evidence and not full_evidence_recalled:
        return "expected_evidence_missing"
    if case.required_citation and not citation_present:
        return "citation_missing"
    if not expected_terms_found:
        return "expected_terms_missing"
    if not source_covered:
        return "expected_source_missing"
    if not document_covered:
        return "expected_document_missing"
    if case.risk_level in {"high", "critical"} and case.expected_human_review:
        return "risk_requires_review"
    if match.confidence < low_confidence_threshold:
        return "low_confidence_needs_review"
    return ""


def run_knowledge_evaluation_set(
    db: Session,
    evaluation_set_id: int,
    payload: KnowledgeEvaluationRunCreate,
    principal: CurrentPrincipal,
) -> KnowledgeEvaluationRunRead:
    _require_knowledge_manager(principal)
    evaluation_set = db.get(KnowledgeEvaluationSet, evaluation_set_id)
    if evaluation_set is None or evaluation_set.tenant_id != principal.tenant.id:
        raise HTTPException(status_code=404, detail="knowledge evaluation set not found")

    now = utc_now()
    profile = _resolve_embedding_profile()
    _require_vector_store_available(profile, db)
    retrieval_backend = _retrieval_backend_for_profile(profile, db)
    active_cases = _evaluation_cases_for_set(db, evaluation_set.id, status_filter=payload.status)
    search_status = payload.search_status or payload.status
    run = KnowledgeEvaluationRun(
        tenant_id=evaluation_set.tenant_id,
        evaluation_set_id=evaluation_set.id,
        run_mode=evaluation_set.evaluation_mode,
        retrieval_mode=DOCUMENT_RETRIEVAL_MODE,
        vector_engine=profile.vector_engine,
        total_cases=len(active_cases),
        summary_payload={
            "evaluation_scope": f"{evaluation_set.evaluation_mode}_only",
            "unsupported_answer_rate_note": "当前评测只检查检索命中和引用覆盖，不生成自由文本答案，因此不生成自由文本答案的幻觉率暂记为 null。",
            "unsupported_answer_rate_measured": False,
            "embedding_provider": profile.provider,
            "embedding_model": profile.model,
            "vector_store": profile.vector_store,
            "retrieval_backend": retrieval_backend,
            "reranker": profile.reranker,
            "top_k": payload.top_k,
            "min_score": payload.min_score,
            "case_status": payload.status,
            "search_status": search_status,
            "low_confidence_threshold": payload.low_confidence_threshold,
        },
        created_by_id=principal.user.id,
        created_at=now,
    )
    db.add(run)
    db.flush()

    answered_cases = 0
    no_hit_cases = 0
    passed_cases = 0
    failed_cases = 0
    needs_review_cases = 0
    citation_covered_cases = 0
    expected_term_covered_cases = 0
    confidence_total = 0.0
    full_evidence_cases = 0
    full_evidence_covered_cases = 0
    citation_sufficient_cases = 0
    citation_precision_total = 0.0
    citation_precision_cases = 0
    forbidden_term_hits_total = 0
    forbidden_commitment_violation_cases = 0
    human_review_correct_cases = 0

    for case in active_cases:
        search = search_knowledge_documents(
            db,
            evaluation_set.tenant_id,
            KnowledgeDocumentSearchRequest(
                query=case.question,
                top_k=payload.top_k,
                min_score=payload.min_score,
                status=search_status,
            ),
            principal,
        )
        top_match = search.matches[0] if search.matches else None
        returned_chunk_ids_top_k = _case_returned_chunk_ids(search.matches)
        expected_chunk_ids = _case_expected_chunk_ids(case)
        full_evidence_recalled = _case_full_evidence_recalled(case, search.matches)
        if expected_chunk_ids:
            full_evidence_cases += 1
            if full_evidence_recalled:
                full_evidence_covered_cases += 1
        citation_precision = _case_citation_precision(case, search.matches)
        if citation_precision is not None:
            citation_precision_total += citation_precision
            citation_precision_cases += 1
        forbidden_term_hits = _case_forbidden_term_hits(case, search.matches)
        forbidden_term_hits_total += len(forbidden_term_hits)
        if top_match is None:
            no_hit_cases += 1
            matched_terms: list[str] = []
            citation_present = False
            expected_terms_found = False
            source_covered = False
            document_covered = False
            haystack = ""
        else:
            answered_cases += 1
            confidence_total += top_match.confidence
            matched_terms = sorted(
                {
                    term
                    for match in search.matches
                    for term in match.matched_terms
                },
                key=lambda term: (-len(term), term),
            )[:50]
            citation_present = bool(top_match.citation and top_match.citation.get("source_uri"))
            haystack = "\n".join(
                [
                    " ".join(
                        [
                            match.document_title,
                            match.source_uri,
                            match.section_title,
                            match.content_preview,
                            " ".join(match.matched_terms),
                        ]
                    )
                    for match in search.matches
                ]
            )
            expected_terms_found = _case_expected_terms_found(case, haystack, matched_terms)
            source_covered = _case_source_covered(case, top_match)
            document_covered = _case_document_covered(case, top_match)
            if citation_present:
                citation_covered_cases += 1
            if expected_terms_found:
                expected_term_covered_cases += 1

        citation_sufficient = bool(citation_present and full_evidence_recalled and source_covered and document_covered)
        if citation_sufficient:
            citation_sufficient_cases += 1
        forbidden_commitment_passed = len(forbidden_term_hits) == 0
        if not forbidden_commitment_passed:
            forbidden_commitment_violation_cases += 1

        failure_reason = _case_failure_reason(
            case=case,
            match=top_match,
            citation_present=citation_present,
            expected_terms_found=expected_terms_found,
            source_covered=source_covered,
            document_covered=document_covered,
            full_evidence_recalled=full_evidence_recalled,
            forbidden_term_hits=forbidden_term_hits,
            low_confidence_threshold=payload.low_confidence_threshold,
        )
        predicted_human_review = bool(failure_reason)
        expected_human_review = bool(case.expected_human_review or not case.allow_auto_reply)
        human_review_prediction_correct = predicted_human_review == expected_human_review
        answer_quality_failure_reasons = [
            reason
            for reason, failed in [
                ("citation_sufficiency_failed", not citation_sufficient),
                ("forbidden_commitment_detected", not forbidden_commitment_passed),
                ("handoff_prediction_mismatch", not human_review_prediction_correct),
            ]
            if failed
        ]
        if human_review_prediction_correct:
            human_review_correct_cases += 1
        if failure_reason:
            needs_review_cases += 1
            failed_cases += 1
            case_status = "needs_review"
        else:
            passed_cases += 1
            case_status = "passed"

        db.add(
            KnowledgeEvaluationRunCase(
                tenant_id=evaluation_set.tenant_id,
                evaluation_run_id=run.id,
                evaluation_case_id=case.id,
                question=case.question,
                status=case_status,
                top_score=top_match.score if top_match else 0.0,
                top_confidence=top_match.confidence if top_match else 0.0,
                top_chunk_id=top_match.chunk_id if top_match else None,
                top_document_id=top_match.document_id if top_match else None,
                citation_present=citation_present,
                expected_terms_found=expected_terms_found,
                matched_terms=matched_terms,
                failure_reason=failure_reason,
                result_payload={
                    "external_case_id": case.external_case_id,
                    "source_channel": case.source_channel,
                    "source_category": case.source_category,
                    "question_type": case.question_type,
                    "risk_level": case.risk_level,
                    "annotation_notes": case.annotation_notes,
                    "expected_terms": case.expected_terms,
                    "expected_source_uri": case.expected_source_uri,
                    "expected_document_title": case.expected_document_title,
                    "expected_chunk_ids": expected_chunk_ids,
                    "must_have_all_evidence": case.must_have_all_evidence,
                    "returned_chunk_ids_top_k": returned_chunk_ids_top_k,
                    "full_evidence_recalled_at_5": full_evidence_recalled,
                    "citation_precision": citation_precision,
                    "expected_human_review": expected_human_review,
                    "predicted_human_review": predicted_human_review,
                    "human_review_prediction_correct": human_review_prediction_correct,
                    "allow_auto_reply": case.allow_auto_reply,
                    "forbidden_terms": case.forbidden_terms,
                    "forbidden_term_hits": forbidden_term_hits,
                    "answer_quality": {
                        "scope": "retrieval_grounded_answer_quality_gate",
                        "final_answer_factuality_status": "not_measured_final_answer_not_generated",
                        "final_answer_factuality_measured": False,
                        "citation_sufficient": citation_sufficient,
                        "forbidden_commitment_passed": forbidden_commitment_passed,
                        "handoff_correct": human_review_prediction_correct,
                        "gate_passed": not answer_quality_failure_reasons,
                        "failure_reasons": answer_quality_failure_reasons,
                        "note": "P3-06U-26E 第一片只评估证据、禁用承诺和转人工门禁；未生成最终客服答案，事实性需人工标注或后续模型答案评测。",
                    },
                    "required_citation": case.required_citation,
                    "top_match": top_match.model_dump() if top_match else None,
                },
                created_at=now,
            )
        )

    run.answered_cases = answered_cases
    run.no_hit_cases = no_hit_cases
    run.passed_cases = passed_cases
    run.failed_cases = failed_cases
    run.needs_review_cases = needs_review_cases
    run.citation_covered_cases = citation_covered_cases
    run.expected_term_covered_cases = expected_term_covered_cases
    run.hit_rate = _ratio(answered_cases, run.total_cases)
    run.citation_coverage = _ratio(citation_covered_cases, run.total_cases)
    run.expected_term_coverage = _ratio(expected_term_covered_cases, run.total_cases)
    run.average_confidence = round(confidence_total / answered_cases, 4) if answered_cases else 0.0
    run.unsupported_answer_rate = None
    summary_payload = dict(run.summary_payload)
    summary_payload.update(
        {
            "full_evidence_cases": full_evidence_cases,
            "full_evidence_covered_cases": full_evidence_covered_cases,
            "full_evidence_recall_at_5": _ratio(full_evidence_covered_cases, full_evidence_cases),
            "citation_precision": (
                round(citation_precision_total / citation_precision_cases, 4)
                if citation_precision_cases
                else 0.0
            ),
            "citation_precision_cases": citation_precision_cases,
            "human_review_correct_cases": human_review_correct_cases,
            "human_review_correctness": _ratio(human_review_correct_cases, run.total_cases),
            "knowledge_gap_rate": _ratio(no_hit_cases, run.total_cases),
            "forbidden_term_hits": forbidden_term_hits_total,
            "answer_quality_metrics_version": "p3_06u_26e_customer_service_answer_quality_v1",
            "final_answer_factuality_measured": False,
            "final_answer_factuality_rate": None,
            "final_answer_factuality_note": "当前运行未生成最终客服答案，因此不计算完整事实准确率；需真实题库、人工标准答案和最终答案文本后再评。",
            "citation_sufficient_cases": citation_sufficient_cases,
            "citation_sufficiency_rate": _ratio(citation_sufficient_cases, run.total_cases),
            "forbidden_commitment_violation_cases": forbidden_commitment_violation_cases,
            "forbidden_commitment_violation_rate": _ratio(forbidden_commitment_violation_cases, run.total_cases),
            "handoff_correct_cases": human_review_correct_cases,
            "handoff_correctness": _ratio(human_review_correct_cases, run.total_cases),
            "answer_quality_scope": "retrieval_grounded_answer_quality_gate_without_final_generation",
            "customer_service_metrics_version": "p2_22_customer_service_retrieval_v1",
        }
    )
    run.summary_payload = summary_payload
    add_audit_event(
        db,
        tenant_id=evaluation_set.tenant_id,
        actor_id=principal.user.id,
        action="knowledge_evaluation_run.created",
        resource_type="knowledge_evaluation_run",
        resource_id=str(run.id),
        payload={
            "evaluation_set_id": evaluation_set.id,
            "total_cases": run.total_cases,
            "hit_rate": run.hit_rate,
            "citation_coverage": run.citation_coverage,
            "expected_term_coverage": run.expected_term_coverage,
            "needs_review_cases": run.needs_review_cases,
            "full_evidence_recall_at_5": summary_payload["full_evidence_recall_at_5"],
            "human_review_correctness": summary_payload["human_review_correctness"],
            "knowledge_gap_rate": summary_payload["knowledge_gap_rate"],
            "citation_sufficiency_rate": summary_payload["citation_sufficiency_rate"],
            "forbidden_commitment_violation_rate": summary_payload["forbidden_commitment_violation_rate"],
            "handoff_correctness": summary_payload["handoff_correctness"],
            "final_answer_factuality_measured": summary_payload["final_answer_factuality_measured"],
            "answer_quality_metrics_version": summary_payload["answer_quality_metrics_version"],
            "vector_engine": run.vector_engine,
            "vector_store": profile.vector_store,
            "retrieval_backend": retrieval_backend,
            "reranker": profile.reranker,
        },
    )
    db.commit()
    db.refresh(run)
    return _evaluation_run_read(db, run)


def search_knowledge_cards(
    db: Session,
    tenant_id: int,
    payload: KnowledgeSearchRequest,
    principal: CurrentPrincipal,
) -> KnowledgeSearchResponse:
    _require_same_tenant(db, tenant_id, principal)
    cards = list(
        db.scalars(
            select(KnowledgeCard)
            .where(KnowledgeCard.tenant_id == tenant_id, KnowledgeCard.status == payload.status)
            .order_by(KnowledgeCard.updated_at.desc(), KnowledgeCard.id.desc())
        ).all()
    )
    query_terms = set(_tokenize(payload.query))
    meaningful_query_terms = _meaningful_terms(query_terms)
    document_tokens = {card.id: _card_tokens(card) for card in cards}
    document_frequencies: Counter[str] = Counter()
    for terms in document_tokens.values():
        document_frequencies.update(set(terms))
    average_length = (
        sum(len(terms) for terms in document_tokens.values()) / len(document_tokens)
        if document_tokens
        else 0
    )

    matches: list[KnowledgeSearchMatch] = []
    for card in cards:
        terms = document_tokens[card.id]
        score = _bm25_score(query_terms, terms, document_frequencies, len(cards), average_length)
        if score <= payload.min_score:
            continue
        matched_terms = _meaningful_terms(query_terms.intersection(set(terms)))
        if len(meaningful_query_terms) > 1 and len(matched_terms) < 2:
            continue
        matched_terms = sorted(matched_terms, key=lambda term: (-len(term), term))[:20]
        matches.append(
            KnowledgeSearchMatch(
                card=card,
                score=round(score, 4),
                confidence=_confidence_from_score(score),
                matched_terms=matched_terms,
            )
        )

    matches.sort(key=lambda match: (match.score, match.confidence, match.card.updated_at or match.card.created_at), reverse=True)
    return KnowledgeSearchResponse(
        query=payload.query,
        retrieval_mode=RETRIEVAL_MODE,
        total_candidates=len(cards),
        matches=matches[: payload.top_k],
    )
