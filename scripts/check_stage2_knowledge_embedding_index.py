#!/usr/bin/env python3
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]


REQUIRED_TEXT = {
    "backend/app/core/config.py": [
        "knowledge_embedding_provider",
        "knowledge_embedding_api_base",
        "knowledge_embedding_api_key",
        "knowledge_vector_store",
        "knowledge_reranker",
    ],
    ".env.example": [
        "KNOWLEDGE_EMBEDDING_PROVIDER=deterministic_local",
        "KNOWLEDGE_VECTOR_STORE=sqlite_json_vector_store",
        "KNOWLEDGE_RERANKER=lexical_overlap_reranker_v1",
    ],
    "backend/app/models/foundation.py": [
        "embedding_vector",
        "embedding_provider",
        "embedding_model",
        "embedding_dimension",
        "vector_index_status",
    ],
    "backend/app/migrations/versions/0011_knowledge_embedding_index.py": [
        'revision = "0011_knowledge_embedding_index"',
        'down_revision = "0010_knowledge_evaluations"',
        "CREATE EXTENSION IF NOT EXISTS vector",
        "embedding_vector",
        "vector_index_status",
    ],
    "backend/app/schemas/knowledge.py": [
        "embedding_provider",
        "embedding_model",
        "embedding_dimension",
        "vector_store",
        "reranker_score",
    ],
    "backend/app/services/knowledge.py": [
        "EmbeddingProfile",
        "DETERMINISTIC_VECTOR_ENGINE",
        "hybrid_bm25_vector_rerank_v1",
        "openai_compatible",
        "_dense_hash_embedding",
        "_require_embedding_available",
        "lexical_overlap_reranker_v1",
    ],
    "backend/tests/test_knowledge_documents_api.py": [
        "test_document_embedding_index_records_provider_vector_store_and_reranker",
        "test_explicit_external_embedding_provider_missing_key_rejects_import",
        "hybrid_bm25_vector_rerank_v1",
        "deterministic_local_hash_embedding_v1",
    ],
}


def fail(message: str) -> None:
    print(f"FAIL stage2 knowledge embedding index: {message}")
    sys.exit(1)


def main() -> None:
    for path, fragments in REQUIRED_TEXT.items():
        full_path = ROOT / path
        if not full_path.exists():
            fail(f"missing file: {path}")
        content = full_path.read_text(encoding="utf-8")
        missing = [fragment for fragment in fragments if fragment not in content]
        if missing:
            fail(f"missing fragment in {path}: {', '.join(missing)}")
    print("PASS stage2 knowledge embedding index")


if __name__ == "__main__":
    main()
