from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


CHECKS = {
    "backend/app/models/foundation.py": [
        "class BusinessObject",
        "class BusinessObjectAlias",
        "class ObjectKnowledgeCard",
        "class KnowledgeImportBatch",
    ],
    "backend/app/schemas/knowledge.py": [
        "BusinessObjectCreate",
        "BusinessObjectRead",
        "ObjectKnowledgeCardCreate",
        "ObjectKnowledgeCardRead",
    ],
    "backend/app/services/knowledge.py": [
        "def create_business_object",
        "def list_business_objects",
        "def create_object_knowledge_card",
        "def list_object_knowledge_cards",
        "business_object.created",
        "object_knowledge_card.created",
    ],
    "backend/app/api/knowledge.py": [
        "/tenants/{tenant_id}/business-objects",
        "/business-objects/{business_object_id}/knowledge-cards",
    ],
    "backend/app/migrations/versions/0023_business_object_knowledge.py": [
        "business_objects",
        "business_object_aliases",
        "object_knowledge_cards",
        "knowledge_import_batches",
    ],
    "frontend/src/api/client.ts": [
        "export interface BusinessObject",
        "export interface ObjectKnowledgeCard",
        "export async function listBusinessObjects",
        "export async function createObjectKnowledgeCard",
    ],
    "frontend/src/App.tsx": [
        "业务对象知识库",
        "对象问答卡",
        "data-business-object-knowledge",
        "AI 客服入门验证包",
    ],
    "frontend/src/styles.css": [
        ".business-knowledge-layout",
        ".business-object-grid",
        ".object-knowledge-list",
    ],
    "docs/P3-06U-19_BUSINESS_OBJECT_KNOWLEDGE_BASE.md": [
        "业务对象知识库底座",
        "P3-06U-20",
        "回复策略状态机",
    ],
}


def main() -> None:
    missing: list[str] = []
    for relative_path, needles in CHECKS.items():
        path = ROOT / relative_path
        if not path.exists():
            missing.append(f"{relative_path}: file missing")
            continue
        content = path.read_text(encoding="utf-8")
        for needle in needles:
            if needle not in content:
                missing.append(f"{relative_path}: missing {needle}")

    if missing:
        raise SystemExit("\n".join(missing))
    print("P3-06U-19 business object knowledge static check passed")


if __name__ == "__main__":
    main()
