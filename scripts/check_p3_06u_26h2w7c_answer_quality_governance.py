from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


REQUIRED_MARKERS = {
    "backend/app/schemas/rag_governance.py": [
        "class RagGovernanceAnswerQuality",
        "final_answer_sampled_cases",
        "final_answer_factuality_rate",
        "complete_accuracy_measured",
        "answer_quality: RagGovernanceAnswerQuality",
    ],
    "backend/app/services/rag_governance.py": [
        "_answer_quality_from_latest_run",
        "final_answer_quality",
        "knowledge_evaluation_run_cases.result_payload_and_reply_citation_snapshots",
        "当前知识评测仍不能等同完整客服准确率",
        "citation_snapshot_count",
    ],
    "backend/app/services/knowledge.py": [
        "FINAL_ANSWER_CITATION_SNAPSHOT_KINDS",
        "_replace_final_answer_citation_snapshots",
        "final_answer_citation_uri",
        "final_answer_sample_without_citation",
        "ReplyCitationSnapshot",
    ],
    "backend/tests/test_knowledge_evaluations_api.py": [
        "ReplyCitationSnapshot",
        "final_answer_citation_uri",
        "internal://docs/after-sales-v1",
    ],
    "backend/tests/test_rag_cost_governance_api.py": [
        "answer_quality",
        "final_answer_quality",
        "complete_accuracy_measured",
        "citation_snapshot_count",
    ],
    "docs/P3-06U-26H2W7C_FINAL_ANSWER_QUALITY_FIRST_SLICE.md": [
        "H2W-7C",
        "最终客服答案质量",
        "引用快照",
        "不是完整线上准确率",
        "真实外发继续关闭",
        "停止门禁",
    ],
    "README.md": [
        "H2W-7C",
        "最终答案质量",
        "reply_citation_snapshots",
        "不是完整线上准确率",
    ],
}


def main() -> None:
    failures: list[str] = []
    for relative_path, markers in REQUIRED_MARKERS.items():
        path = ROOT / relative_path
        if not path.exists():
            failures.append(f"missing file: {relative_path}")
            continue
        text = path.read_text(encoding="utf-8")
        for marker in markers:
            if marker not in text:
                failures.append(f"{relative_path}: missing marker {marker!r}")

    if failures:
        raise SystemExit("\n".join(failures))
    print("P3-06U-26H2W7C answer quality governance static check passed.")


if __name__ == "__main__":
    main()
