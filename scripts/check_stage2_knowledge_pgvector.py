#!/usr/bin/env python3
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]


REQUIRED_TEXT = {
    "backend/app/migrations/versions/0012_knowledge_pgvector_query_path.py": [
        'revision = "0012_knowledge_pgvector"',
        'down_revision = "0011_knowledge_embedding_index"',
        "embedding_pgvector vector",
        "ix_knowledge_document_chunks_pgvector_scope",
    ],
    "backend/app/schemas/knowledge.py": [
        "KnowledgeVectorIndexRebuildCreate",
        "KnowledgeVectorIndexRebuildRead",
        "retrieval_backend",
        "vector_index_status",
    ],
    "backend/app/api/knowledge.py": [
        "knowledge-vector-index/rebuilds",
        "KnowledgeVectorIndexRebuildRead",
        "rebuild_knowledge_vector_index",
    ],
    "backend/app/services/knowledge.py": [
        "PGVECTOR_VECTOR_STORE",
        "postgres_pgvector_store_v1",
        "postgres_pgvector_exact_cosine_v1",
        "_build_pgvector_candidate_sql",
        "<=> CAST(:query_vector AS vector)",
        "_require_vector_store_available",
        "knowledge_vector_index.rebuilt",
    ],
    "backend/tests/test_knowledge_vector_index_api.py": [
        "test_owner_can_rebuild_knowledge_vector_index",
        "test_explicit_pgvector_store_requires_postgresql_without_silent_fallback",
        "test_pgvector_candidate_sql_filters_scope_before_similarity",
    ],
    "frontend/src/api/client.ts": [
        "KnowledgeVectorIndexRebuild",
        "rebuildKnowledgeVectorIndex",
        "retrieval_backend",
    ],
}


def fail(message: str) -> None:
    print(f"FAIL stage2 knowledge pgvector: {message}")
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
    print("PASS stage2 knowledge pgvector")


if __name__ == "__main__":
    main()
