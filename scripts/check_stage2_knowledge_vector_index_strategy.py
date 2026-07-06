#!/usr/bin/env python3
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]


REQUIRED_TEXT = {
    "backend/app/migrations/versions/0014_knowledge_vector_index_plans.py": [
        'revision = "0014_vector_index_plan"',
        'down_revision = "0013_embedding_smoke"',
        "knowledge_vector_index_plans",
        "ix_knowledge_vector_index_plans_strategy",
    ],
    "backend/app/models/foundation.py": [
        "class KnowledgeVectorIndexPlan",
        "__tablename__ = \"knowledge_vector_index_plans\"",
        "ddl_statements",
        "rollback_statements",
        "execute_performed",
    ],
    "backend/app/schemas/knowledge.py": [
        "KnowledgeVectorIndexPlanCreate",
        "KnowledgeVectorIndexPlanRead",
        "requested_strategy",
        "target_chunk_count_override",
    ],
    "backend/app/api/knowledge.py": [
        "knowledge-vector-index/plans",
        "KnowledgeVectorIndexPlanRead",
        "create_knowledge_vector_index_plan",
    ],
    "backend/app/services/knowledge.py": [
        "_build_pgvector_ann_index_plan",
        "postgres_pgvector_hnsw_cosine_v1",
        "postgres_pgvector_ivfflat_cosine_v1",
        "embedding_pgvector::vector",
        "vector_cosine_ops",
        "knowledge_vector_index.plan_created",
        "DROP INDEX",
        "external_execution_performed",
    ],
    "backend/tests/test_knowledge_vector_index_strategy_api.py": [
        "test_owner_can_create_json_vector_index_strategy_plan",
        "test_pgvector_plan_blocks_non_postgresql_without_executing",
        "test_pgvector_ann_index_plan_uses_expression_partial_indexes_and_rollback",
    ],
}


def fail(message: str) -> None:
    print(f"FAIL stage2 knowledge vector index strategy: {message}")
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
    print("PASS stage2 knowledge vector index strategy")


if __name__ == "__main__":
    main()
