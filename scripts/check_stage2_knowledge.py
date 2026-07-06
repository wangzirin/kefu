#!/usr/bin/env python3
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]


REQUIRED_PATHS = [
    "backend/app/api/knowledge.py",
    "backend/app/schemas/knowledge.py",
    "backend/app/services/knowledge.py",
    "backend/app/migrations/versions/0003_knowledge_cards.py",
    "backend/tests/test_knowledge_api.py",
]

REQUIRED_TEXT = {
    "backend/app/main.py": [
        "knowledge",
        "app.include_router(knowledge.router)",
    ],
    "backend/app/models/foundation.py": [
        "class KnowledgeCard",
        "__tablename__ = \"knowledge_cards\"",
    ],
    "backend/app/models/__init__.py": [
        "KnowledgeCard",
    ],
    "backend/app/api/knowledge.py": [
        "/tenants/{tenant_id}/knowledge-cards",
        "/knowledge-cards/{card_id}",
        "/tenants/{tenant_id}/knowledge-searches",
        "require_current_principal",
    ],
    "backend/app/services/knowledge.py": [
        "RETRIEVAL_MODE = \"lexical_bm25_v1\"",
        "create_knowledge_card",
        "list_knowledge_cards",
        "update_knowledge_card",
        "search_knowledge_cards",
        "knowledge_card.created",
        "knowledge_card.updated",
    ],
    "backend/app/schemas/knowledge.py": [
        "class KnowledgeCardCreate",
        "class KnowledgeCardRead",
        "class KnowledgeCardList",
        "class KnowledgeSearchRequest",
        "class KnowledgeSearchResponse",
    ],
    "backend/app/migrations/versions/0003_knowledge_cards.py": [
        "knowledge_cards",
        'down_revision = "0002_workflow_foundation"',
        "ix_knowledge_cards_tenant_status",
    ],
    "backend/tests/test_knowledge_api.py": [
        "test_owner_can_create_list_and_search_knowledge_cards",
        "test_agent_can_search_but_cannot_write_knowledge_cards",
        "test_knowledge_search_respects_tenant_and_status_boundaries",
    ],
}


def fail(message: str) -> None:
    print(f"FAIL stage2 knowledge: {message}")
    sys.exit(1)


def main() -> None:
    missing = [path for path in REQUIRED_PATHS if not (ROOT / path).exists()]
    if missing:
        fail("missing files: " + ", ".join(missing))

    for path, fragments in REQUIRED_TEXT.items():
        content = (ROOT / path).read_text(encoding="utf-8")
        for fragment in fragments:
            if fragment not in content:
                fail(f"missing fragment in {path}: {fragment}")

    print("PASS stage2 knowledge")


if __name__ == "__main__":
    main()
