#!/usr/bin/env python3
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]


REQUIRED_TEXT = {
    "backend/app/core/config.py": [
        "knowledge_embedding_price_per_1k_tokens",
        "knowledge_embedding_cost_currency",
    ],
    ".env.example": [
        "KNOWLEDGE_EMBEDDING_PRICE_PER_1K_TOKENS=0",
        "KNOWLEDGE_EMBEDDING_COST_CURRENCY=CNY",
    ],
    "backend/app/models/foundation.py": [
        "KnowledgeEmbeddingProviderSmokeRun",
        "knowledge_embedding_provider_smoke_runs",
        "input_text_hash",
        "estimated_input_tokens",
        "estimated_cost",
        "raw_text_logged",
    ],
    "backend/app/models/__init__.py": [
        "KnowledgeEmbeddingProviderSmokeRun",
    ],
    "backend/app/migrations/versions/0013_knowledge_embedding_provider_smoke.py": [
        'revision = "0013_embedding_smoke"',
        'down_revision = "0012_knowledge_pgvector"',
        "knowledge_embedding_provider_smoke_runs",
        "ix_knowledge_embedding_smoke_tenant_created",
    ],
    "backend/app/schemas/knowledge.py": [
        "KnowledgeEmbeddingProviderSmokeCreate",
        "KnowledgeEmbeddingProviderSmokeRead",
        "allow_external_call",
        "raw_text_logged",
        "response_metadata",
    ],
    "backend/app/api/knowledge.py": [
        "knowledge-embedding-provider-smoke-runs",
        "KnowledgeEmbeddingProviderSmokeRead",
        "run_knowledge_embedding_provider_smoke",
    ],
    "backend/app/services/knowledge.py": [
        "run_knowledge_embedding_provider_smoke",
        "knowledge_embedding_provider_smoke.created",
        "allow_external_call=true",
        "_embedding_cost",
        "_embedding_quality_checks",
        "raw_text_logged=False",
    ],
    "backend/tests/test_knowledge_embedding_provider_smoke_api.py": [
        "test_owner_can_run_deterministic_embedding_provider_smoke",
        "test_external_embedding_provider_smoke_requires_explicit_allow",
        "test_openai_compatible_embedding_provider_smoke_records_cost_latency_without_raw_text",
        "不保存原文",
    ],
}


def fail(message: str) -> None:
    print(f"FAIL stage2 knowledge embedding provider smoke: {message}")
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
    print("PASS stage2 knowledge embedding provider smoke")


if __name__ == "__main__":
    main()
