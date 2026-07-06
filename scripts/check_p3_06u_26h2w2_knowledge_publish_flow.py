#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def require_contains(path: str, needle: str) -> None:
    content = read(path)
    if needle not in content:
        raise AssertionError(f"{path} missing required marker: {needle}")


def require_absent(path: str, needles: list[str]) -> None:
    content = read(path)
    for needle in needles:
        if needle in content:
            raise AssertionError(f"{path} contains forbidden overclaim: {needle}")


def main() -> None:
    for path in [
        "frontend/src/App.tsx",
        "frontend/src/styles.css",
        "frontend/src/api/client.ts",
        "backend/app/api/knowledge.py",
        "backend/app/services/knowledge.py",
        "docs/P3-06U-26H2W2_KNOWLEDGE_PUBLISH_FLOW.md",
    ]:
        if not (ROOT / path).exists():
            raise AssertionError(f"missing required file: {path}")

    for needle in [
        "checkKnowledgeDocumentPublishGate",
        "handleCheckKnowledgeDocumentPublishGate",
        "handlePublishKnowledgeDocument",
        'data-h2w2-publish-flow="true"',
        'data-h2w2-publish-step="select-policy"',
        'data-h2w2-publish-step="precheck-samples"',
        'data-h2w2-publish-step="version-record"',
        'data-h2w2-publish-boundary="no-external-write"',
        'data-h2w2-action="publish-precheck"',
        'data-h2w2-action="publish-document"',
        "启用与回归检查",
        "选择待启用文档",
        "回归题检查",
        "发布前样题试跑",
        "确认发布版本",
        "真实渠道外发继续关闭" if "真实渠道外发继续关闭" in read("frontend/src/App.tsx") else "真实发送继续受渠道授权控制",
    ]:
        require_contains("frontend/src/App.tsx", needle)

    for needle in [
        "export async function checkKnowledgeDocumentPublishGate",
        "export async function publishKnowledgeDocument",
        "export async function listKnowledgeDocumentPublications",
    ]:
        require_contains("frontend/src/api/client.ts", needle)

    for needle in [
        "/knowledge-documents/{document_id}/publish-checks",
        "/knowledge-documents/{document_id}/publication",
        "/knowledge-documents/{document_id}/publications",
    ]:
        require_contains("backend/app/api/knowledge.py", needle)

    for needle in [
        "publication_type = \"publish\" if perform_publish else \"publish_check\"",
        "external_write_performed=False",
        "model_call_performed=False",
    ]:
        require_contains("backend/app/services/knowledge.py", needle)

    for needle in [
        ".customer-knowledge-publish-flow",
        ".customer-knowledge-publish-grid",
        ".knowledge-document-publish-actions",
    ]:
        require_contains("frontend/src/styles.css", needle)

    for needle in [
        "H2W-2 客户知识发布流程第二片",
        "发布前样题试跑",
        "发布版本记录",
        "不打开真实外发",
        "不是完整客服准确率",
    ]:
        require_contains("docs/P3-06U-26H2W2_KNOWLEDGE_PUBLISH_FLOW.md", needle)

    require_absent(
        "frontend/src/App.tsx",
        ["已接通全平台", "已自动外发", "完整客服准确率已通过", "真实平台外发已开启"],
    )


if __name__ == "__main__":
    main()
