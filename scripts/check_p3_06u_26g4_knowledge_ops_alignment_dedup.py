#!/usr/bin/env python3
"""P3-06U-26G4 knowledge ops alignment and dedupe checks."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def main() -> int:
    failures: list[str] = []
    app = read("frontend/src/App.tsx")
    page = read("frontend/src/components/knowledge/KnowledgeWorkspacePage.tsx")
    styles = read("frontend/src/styles.css")
    client = read("frontend/src/api/client.ts")
    backend = read("backend/app/api/knowledge.py")
    doc_path = ROOT / "docs/P3-06U-26G4_KNOWLEDGE_OPS_ALIGNMENT_AND_DEDUP_AUDIT.md"
    doc = doc_path.read_text(encoding="utf-8") if doc_path.exists() else ""

    required_frontend = [
        '<KnowledgeWorkspacePage\n            mode="library"',
        '<KnowledgeWorkspacePage\n            mode="gaps"',
        '<KnowledgeWorkspacePage\n            mode="evals"',
        "<KnowledgeDocumentsPanel",
        "<KnowledgeGapPanel",
        "<KnowledgeEvaluationPanel",
        'data-knowledge-page-shell={mode}',
        'data-knowledge-gap-cause-map="p3-06u-26d"',
        'data-knowledge-regression-compare="p3-06u-26d"',
        'data-knowledge-ops-smoke="edit-checklist"',
    ]
    for snippet in required_frontend:
        if snippet not in app and snippet not in page:
            failures.append(f"missing frontend alignment marker: {snippet}")

    required_api_client = [
        "export async function listKnowledgeDocuments",
        "export async function listKnowledgeDocumentChunks",
        "export async function createBusinessObject",
        "export async function listKnowledgeEvaluationSets",
        "export async function listKnowledgeEvaluationRuns",
        "export async function listKnowledgeGaps",
    ]
    for snippet in required_api_client:
        if snippet not in client:
            failures.append(f"missing frontend api client function: {snippet}")

    required_backend = [
        '"/tenants/{tenant_id}/business-objects"',
        '"/business-objects/{business_object_id}/knowledge-cards"',
        '"/tenants/{tenant_id}/knowledge-documents"',
        '"/knowledge-documents/{document_id}/chunks"',
        '"/knowledge-documents/{document_id}/publish-checks"',
        '"/knowledge-documents/{document_id}/publication"',
        '"/knowledge-documents/{document_id}/rollback"',
        '"/tenants/{tenant_id}/knowledge-evaluation-sets"',
        '"/knowledge-evaluation-sets/{evaluation_set_id}/runs"',
        '"/knowledge-evaluation-runs/{evaluation_run_id}"',
        '"/tenants/{tenant_id}/knowledge-gaps"',
        '"/tenants/{tenant_id}/knowledge-gaps/sync"',
        '"/knowledge-gaps/{gap_id}"',
        '"/knowledge-gaps/{gap_id}/document-drafts"',
        '"/knowledge-gaps/{gap_id}/regression-cases"',
    ]
    for snippet in required_backend:
        if snippet not in backend:
            failures.append(f"missing backend knowledge endpoint: {snippet}")

    retired = [
        "KnowledgeOperationsFlowPanel",
        'data-knowledge-ops-smoke="flow-panel"',
        'data-knowledge-ops-smoke="workflow-stages"',
        'data-knowledge-ops-smoke="publish-gate"',
        'data-knowledge-ops-smoke="regression-impact"',
        ".knowledge-ops-flow",
        ".knowledge-ops-stage-grid",
        ".knowledge-page-actions",
    ]
    for snippet in retired:
        if snippet in app or snippet in page or snippet in styles:
            failures.append(f"retired duplicate artifact still present: {snippet}")

    required_doc = [
        "# P3-06U-26G4 知识运营前后端对齐与去重审验",
        "知识库运营",
        "知识缺口",
        "知识评测",
        "前后端对齐",
        "重复入口",
        "KnowledgeOperationsFlowPanel",
        "当前知识评测是检索评测，不是完整客服准确率",
        "真实外发继续关闭",
    ]
    if not doc_path.exists():
        failures.append(f"missing document: {doc_path.relative_to(ROOT)}")
    else:
        for phrase in required_doc:
            if phrase not in doc:
                failures.append(f"diagnosis document missing phrase: {phrase}")

    if failures:
        print("P3-06U-26G4 knowledge ops alignment/dedupe check failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("P3-06U-26G4 knowledge ops alignment/dedupe check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
