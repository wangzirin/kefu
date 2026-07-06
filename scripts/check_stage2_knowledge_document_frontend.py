#!/usr/bin/env python3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def require_contains(path: str, snippets: list[str]) -> None:
    text = (ROOT / path).read_text(encoding="utf-8")
    missing = [snippet for snippet in snippets if snippet not in text]
    if missing:
        raise SystemExit(f"{path} missing: {', '.join(missing)}")


def main() -> None:
    require_contains(
        "frontend/src/api/client.ts",
        [
            "KnowledgeDocument",
            "KnowledgeDocumentSearchResponse",
            "createKnowledgeDocument",
            "listKnowledgeDocuments",
            "listKnowledgeDocumentChunks",
            "searchKnowledgeDocuments",
        ],
    )
    require_contains(
        "frontend/src/App.tsx",
        [
            "KnowledgeDocumentsPanel",
            "知识文档运营",
            "导入知识文档",
            "文档片段检索",
            "引用来源",
            "deterministic_local_hash_embedding_v1",
            "lexical_overlap_reranker_v1",
            "onImportDocument",
            "onSearchDocuments",
        ],
    )
    require_contains(
        "frontend/src/styles.css",
        [
            ".knowledge-panel",
            ".knowledge-layout",
            ".knowledge-form",
            ".knowledge-document-list",
            ".knowledge-search-results",
            ".citation-line",
        ],
    )
    print("PASS stage2 knowledge document frontend")


if __name__ == "__main__":
    main()
