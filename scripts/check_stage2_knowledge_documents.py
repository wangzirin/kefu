#!/usr/bin/env python3
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]


REQUIRED_TEXT = {
    "backend/app/models/foundation.py": [
        "class KnowledgeDocument",
        "class KnowledgeDocumentChunk",
        "embedding_signature",
        "embedding_vector",
        "chunk_count",
    ],
    "backend/app/migrations/versions/0009_knowledge_documents.py": [
        "knowledge_documents",
        "knowledge_document_chunks",
        "uq_knowledge_document_chunks_document_id_chunk_index",
    ],
    "backend/app/schemas/knowledge.py": [
        "KnowledgeDocumentCreate",
        "KnowledgeChunkRead",
        "KnowledgeDocumentSearchResponse",
        "vector_engine",
        "vector_store",
        "citation",
    ],
    "backend/app/services/knowledge.py": [
        "DOCUMENT_RETRIEVAL_MODE",
        "hybrid_bm25_vector_rerank_v1",
        "create_knowledge_document",
        "search_knowledge_documents",
        "deterministic_local_hash_embedding_v1",
    ],
    "backend/app/api/knowledge.py": [
        "/tenants/{tenant_id}/knowledge-documents",
        "/knowledge-documents/{document_id}/chunks",
        "/tenants/{tenant_id}/knowledge-document-searches",
    ],
    "backend/app/schemas/reply_orchestrator.py": [
        "document_rag",
        "source_kind",
        "chunk_id",
        "citation",
    ],
    "backend/app/services/reply_orchestrator.py": [
        "_resolve_document_rag_plan",
        "search_knowledge_documents",
        "document_chunk",
    ],
    "backend/tests/test_knowledge_documents_api.py": [
        "test_owner_can_import_document_and_search_chunk_citations",
        "test_agent_can_search_documents_but_cannot_import_them",
    ],
    "backend/tests/test_reply_orchestrator_api.py": [
        "test_reply_orchestration_can_use_document_rag_chunk_with_citation",
    ],
}


def fail(message: str) -> None:
    print(f"FAIL stage2 knowledge documents: {message}")
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
    print("PASS stage2 knowledge documents")


if __name__ == "__main__":
    main()
