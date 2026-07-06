#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


CSV_FIELDS_REDACTED = [
    "external_case_id",
    "source_channel",
    "source_category",
    "question_hash",
    "question_type",
    "risk_level",
    "status",
    "failure_reason",
    "knowledge_gap",
    "top_confidence",
    "top_score",
    "top_chunk_id",
    "top_document_id",
    "citation_present",
    "expected_terms_found",
    "full_evidence_recalled_at_5",
    "citation_precision",
    "expected_human_review",
    "predicted_human_review",
    "human_review_prediction_correct",
    "allow_auto_reply",
    "forbidden_term_hits",
    "expected_chunk_ids",
    "returned_chunk_ids_top_k",
    "top_source_uri",
    "top_document_title",
]


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:24]


def _load_run(input_path: Path) -> dict[str, Any]:
    if not input_path.exists():
        raise FileNotFoundError(f"input file not found: {input_path}")
    data = json.loads(input_path.read_text(encoding="utf-8"))
    if isinstance(data, dict) and isinstance(data.get("run"), dict):
        return data["run"]
    if not isinstance(data, dict):
        raise ValueError("evaluation run JSON must be an object")
    return data


def _payload(case: dict[str, Any]) -> dict[str, Any]:
    payload = case.get("result_payload") or {}
    return payload if isinstance(payload, dict) else {}


def _as_bool(value: Any) -> bool:
    return bool(value) if value is not None else False


def _bool_text(value: Any) -> str:
    if value is None:
        return ""
    return "true" if bool(value) else "false"


def _list_text(value: Any) -> str:
    if not value:
        return ""
    if isinstance(value, list):
        return ";".join(str(item) for item in value)
    return str(value)


def _case_top_match(payload: dict[str, Any]) -> dict[str, Any]:
    top_match = payload.get("top_match") or {}
    return top_match if isinstance(top_match, dict) else {}


def _is_knowledge_gap(case: dict[str, Any], payload: dict[str, Any]) -> bool:
    failure_reason = str(case.get("failure_reason") or "")
    if failure_reason in {"no_retrieval_hit", "no_knowledge_hit"}:
        return True
    if case.get("status") == "no_hit":
        return True
    if not case.get("top_chunk_id") and float(case.get("top_confidence") or 0) <= 0:
        return True
    returned_chunk_ids = payload.get("returned_chunk_ids_top_k")
    return isinstance(returned_chunk_ids, list) and not returned_chunk_ids and failure_reason.startswith("no_")


def _case_row(case: dict[str, Any], *, include_raw_text: bool) -> dict[str, Any]:
    payload = _payload(case)
    top_match = _case_top_match(payload)
    question = str(case.get("question") or "")
    row = {
        "external_case_id": payload.get("external_case_id") or "",
        "source_channel": payload.get("source_channel") or "",
        "source_category": payload.get("source_category") or "",
        "question_hash": _hash_text(question),
        "question_type": payload.get("question_type") or "",
        "risk_level": payload.get("risk_level") or "",
        "status": case.get("status") or "",
        "failure_reason": case.get("failure_reason") or "",
        "knowledge_gap": _bool_text(_is_knowledge_gap(case, payload)),
        "top_confidence": case.get("top_confidence") if case.get("top_confidence") is not None else "",
        "top_score": case.get("top_score") if case.get("top_score") is not None else "",
        "top_chunk_id": case.get("top_chunk_id") or "",
        "top_document_id": case.get("top_document_id") or "",
        "citation_present": _bool_text(case.get("citation_present")),
        "expected_terms_found": _bool_text(case.get("expected_terms_found")),
        "full_evidence_recalled_at_5": _bool_text(payload.get("full_evidence_recalled_at_5")),
        "citation_precision": payload.get("citation_precision") if payload.get("citation_precision") is not None else "",
        "expected_human_review": _bool_text(payload.get("expected_human_review")),
        "predicted_human_review": _bool_text(payload.get("predicted_human_review")),
        "human_review_prediction_correct": _bool_text(payload.get("human_review_prediction_correct")),
        "allow_auto_reply": _bool_text(payload.get("allow_auto_reply")),
        "forbidden_term_hits": _list_text(payload.get("forbidden_term_hits")),
        "expected_chunk_ids": _list_text(payload.get("expected_chunk_ids")),
        "returned_chunk_ids_top_k": _list_text(payload.get("returned_chunk_ids_top_k")),
        "top_source_uri": top_match.get("source_uri") or "",
        "top_document_title": top_match.get("document_title") or "",
    }
    if include_raw_text:
        row["question"] = question
    return row


def _case_rows(run: dict[str, Any], *, include_raw_text: bool) -> list[dict[str, Any]]:
    return [
        _case_row(case, include_raw_text=include_raw_text)
        for case in run.get("case_results", [])
        if isinstance(case, dict)
    ]


def _summary(run: dict[str, Any], rows: list[dict[str, Any]]) -> dict[str, Any]:
    summary_payload = run.get("summary_payload") or {}
    if not isinstance(summary_payload, dict):
        summary_payload = {}
    total_cases = int(run.get("total_cases") or len(rows))
    knowledge_gap_cases = sum(1 for row in rows if row["knowledge_gap"] == "true")
    human_review_correct_cases = sum(1 for row in rows if row["human_review_prediction_correct"] == "true")
    forbidden_hit_cases = sum(1 for row in rows if row["forbidden_term_hits"])
    return {
        "run_id": run.get("id"),
        "evaluation_set_id": run.get("evaluation_set_id"),
        "run_mode": run.get("run_mode") or "",
        "retrieval_mode": run.get("retrieval_mode") or "",
        "vector_engine": run.get("vector_engine") or "",
        "total_cases": total_cases,
        "answered_cases": int(run.get("answered_cases") or 0),
        "no_hit_cases": int(run.get("no_hit_cases") or 0),
        "passed_cases": int(run.get("passed_cases") or 0),
        "failed_cases": int(run.get("failed_cases") or 0),
        "needs_review_cases": int(run.get("needs_review_cases") or 0),
        "hit_rate": run.get("hit_rate"),
        "citation_coverage": run.get("citation_coverage"),
        "expected_term_coverage": run.get("expected_term_coverage"),
        "average_confidence": run.get("average_confidence"),
        "full_evidence_recall_at_5": summary_payload.get("full_evidence_recall_at_5"),
        "citation_precision": summary_payload.get("citation_precision"),
        "human_review_correctness": summary_payload.get("human_review_correctness"),
        "knowledge_gap_rate": summary_payload.get("knowledge_gap_rate"),
        "knowledge_gap_cases": knowledge_gap_cases,
        "human_review_correct_cases": human_review_correct_cases,
        "forbidden_term_hits": summary_payload.get("forbidden_term_hits", 0),
        "forbidden_hit_cases": forbidden_hit_cases,
        "unsupported_answer_rate": run.get("unsupported_answer_rate"),
        "unsupported_answer_rate_measured": summary_payload.get("unsupported_answer_rate_measured"),
        "customer_service_metrics_version": summary_payload.get("customer_service_metrics_version") or "",
    }


def _write_csv(path: Path, rows: list[dict[str, Any]], *, include_raw_text: bool) -> None:
    fieldnames = list(CSV_FIELDS_REDACTED)
    if include_raw_text:
        fieldnames.insert(4, "question")
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def _percent(value: Any) -> str:
    if value is None or value == "":
        return "-"
    try:
        return f"{float(value) * 100:.1f}%"
    except (TypeError, ValueError):
        return str(value)


def _review_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    priority_rows = [
        row
        for row in rows
        if row["status"] != "passed" or row["knowledge_gap"] == "true" or row["human_review_prediction_correct"] == "false"
    ]
    return priority_rows[:20]


def _markdown_table(headers: list[str], rows: list[list[Any]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(item) if item is not None else "" for item in row) + " |")
    return "\n".join(lines)


def _write_markdown(path: Path, summary: dict[str, Any], rows: list[dict[str, Any]], *, include_raw_text: bool) -> None:
    lines = [
        "# 客服知识检索评测复盘报告",
        "",
        "## 安全边界",
        "",
        "- 本报告来自本地评测运行 JSON，不调用模型 provider，不写外部平台。",
        "- 原始问题默认不导出；如启用原文导出，仅用于内部人工复盘，不应进入长期共享材料。",
        "- 当前仍只评测检索证据和人工审核门禁，不生成自由文本答案，因此不把幻觉率记为 0。",
        "",
        "## 运行摘要",
        "",
        _markdown_table(
            ["指标", "值"],
            [
                ["run_id", summary["run_id"]],
                ["evaluation_set_id", summary["evaluation_set_id"]],
                ["run_mode", summary["run_mode"]],
                ["retrieval_mode", summary["retrieval_mode"]],
                ["vector_engine", summary["vector_engine"]],
                ["total_cases", summary["total_cases"]],
                ["passed_cases", summary["passed_cases"]],
                ["needs_review_cases", summary["needs_review_cases"]],
                ["knowledge_gap_cases", summary["knowledge_gap_cases"]],
                ["human_review_correct_cases", summary["human_review_correct_cases"]],
            ],
        ),
        "",
        "## 质量指标",
        "",
        _markdown_table(
            ["指标", "值"],
            [
                ["hit_rate", _percent(summary["hit_rate"])],
                ["citation_coverage", _percent(summary["citation_coverage"])],
                ["expected_term_coverage", _percent(summary["expected_term_coverage"])],
                ["average_confidence", summary["average_confidence"]],
                ["full_evidence_recall_at_5", _percent(summary["full_evidence_recall_at_5"])],
                ["citation_precision", _percent(summary["citation_precision"])],
                ["human_review_correctness", _percent(summary["human_review_correctness"])],
                ["knowledge_gap_rate", _percent(summary["knowledge_gap_rate"])],
                ["forbidden_term_hits", summary["forbidden_term_hits"]],
                ["unsupported_answer_rate", summary["unsupported_answer_rate"]],
            ],
        ),
        "",
        "## 优先复盘题",
        "",
    ]
    review_rows = _review_rows(rows)
    if not review_rows:
        lines.append("当前没有必须优先复盘的题。")
    else:
        headers = [
            "external_case_id",
            "question_hash",
            "source_channel",
            "source_category",
            "status",
            "failure_reason",
            "knowledge_gap",
            "expected_human_review",
            "predicted_human_review",
        ]
        if include_raw_text:
            headers.insert(2, "question")
        table_rows: list[list[Any]] = []
        for row in review_rows:
            table_rows.append([row.get(header, "") for header in headers])
        lines.append(_markdown_table(headers, table_rows))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def export_customer_service_eval_report(
    *,
    input_path: Path | str,
    output_dir: Path | str,
    include_raw_text: bool = False,
) -> dict[str, Any]:
    run = _load_run(Path(input_path))
    rows = _case_rows(run, include_raw_text=include_raw_text)
    summary = _summary(run, rows)

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    run_id = summary["run_id"] or "unknown"
    csv_path = output_path / f"customer_service_eval_run_{run_id}_cases.csv"
    markdown_path = output_path / f"customer_service_eval_run_{run_id}_review.md"

    _write_csv(csv_path, rows, include_raw_text=include_raw_text)
    _write_markdown(markdown_path, summary, rows, include_raw_text=include_raw_text)

    return {
        "status": "exported",
        "input_file": str(Path(input_path)),
        "csv_report_path": str(csv_path),
        "markdown_report_path": str(markdown_path),
        "raw_text_logged": bool(include_raw_text),
        "provider_call_performed": False,
        "external_write_performed": False,
        "summary": summary,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Export customer-service evaluation run reports.")
    parser.add_argument("input_path", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--include-raw-text", action="store_true")
    args = parser.parse_args()

    result = export_customer_service_eval_report(
        input_path=args.input_path,
        output_dir=args.output_dir,
        include_raw_text=args.include_raw_text,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
