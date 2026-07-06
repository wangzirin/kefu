#!/usr/bin/env python3
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]


REQUIRED_TEXT = {
    "backend/app/models/foundation.py": [
        "class KnowledgeEvaluationSet",
        "class KnowledgeEvaluationCase",
        "class KnowledgeEvaluationRun",
        "class KnowledgeEvaluationRunCase",
        "unsupported_answer_rate",
    ],
    "backend/app/migrations/versions/0010_knowledge_evaluations.py": [
        "knowledge_evaluation_sets",
        "knowledge_evaluation_cases",
        "knowledge_evaluation_runs",
        "knowledge_evaluation_run_cases",
        'down_revision = "0009_knowledge_documents"',
    ],
    "backend/app/schemas/knowledge.py": [
        "KnowledgeEvaluationSetCreate",
        "KnowledgeEvaluationRunCreate",
        "KnowledgeEvaluationRunRead",
        "case_results",
        "expected_term_coverage",
    ],
    "backend/app/services/knowledge.py": [
        "create_knowledge_evaluation_set",
        "run_knowledge_evaluation_set",
        "knowledge_evaluation_set.created",
        "knowledge_evaluation_run.created",
        "unsupported_answer_rate_note",
    ],
    "backend/app/api/knowledge.py": [
        "/tenants/{tenant_id}/knowledge-evaluation-sets",
        "/knowledge-evaluation-sets/{evaluation_set_id}/runs",
    ],
    "backend/tests/test_knowledge_evaluations_api.py": [
        "test_owner_can_create_and_run_document_retrieval_evaluation",
        "test_agent_cannot_create_or_run_knowledge_evaluation_sets",
        "unsupported_answer_rate",
    ],
}


def fail(message: str) -> None:
    print(f"FAIL stage2 knowledge evaluations: {message}")
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
    print("PASS stage2 knowledge evaluations")


if __name__ == "__main__":
    main()
