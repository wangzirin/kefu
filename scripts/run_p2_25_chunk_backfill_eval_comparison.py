#!/usr/bin/env python3

from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import io
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_ROOT = ROOT / "scripts"
DEFAULT_SEED_DOCUMENTS = ROOT / "evals" / "p2_24_seed_knowledge_documents.json"
DEFAULT_EVAL_BANK = ROOT / "evals" / "customer_service_eval_bank_synthetic_80_2026-06-26.csv"

if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

from import_customer_service_eval_bank import run_customer_service_eval_bank_import  # noqa: E402
from run_p2_24_synthetic_eval_smoke import (  # noqa: E402
    _bootstrap_owner,
    _compact_report,
    _compact_run,
    _import_seed_documents,
    _json_response,
    _local_test_client,
    _safe_local_embedding_env,
)


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:24]


def _normalize(text: Any) -> str:
    return str(text or "").strip().lower()


def _fetch_chunks_by_source(client, *, token: str, imported_documents: list[dict]) -> tuple[dict[str, list[dict]], list[dict]]:
    headers = {"Authorization": f"Bearer {token}"}
    chunks_by_source: dict[str, list[dict]] = {}
    chunk_catalog: list[dict] = []
    for document in imported_documents:
        chunks = _json_response(
            client.get(f"/api/knowledge-documents/{document['id']}/chunks", headers=headers),
            expected_status=200,
            label=f"list chunks for {document['source_uri']}",
        )
        for chunk in chunks:
            source_uri = str(chunk["source_uri"])
            chunks_by_source.setdefault(source_uri, []).append(chunk)
            chunk_catalog.append(
                {
                    "document_id": chunk["document_id"],
                    "document_title": chunk["citation"]["document_title"],
                    "source_uri": source_uri,
                    "chunk_id": chunk["id"],
                    "chunk_index": chunk["chunk_index"],
                    "section_title": chunk["section_title"],
                    "content_hash": chunk["content_hash"],
                    "token_count": chunk["token_count"],
                    "vector_index_status": chunk["vector_index_status"],
                }
            )
    for chunks in chunks_by_source.values():
        chunks.sort(key=lambda item: (int(item["chunk_index"]), int(item["id"])))
    chunk_catalog.sort(key=lambda item: (item["source_uri"], item["chunk_index"], item["chunk_id"]))
    return chunks_by_source, chunk_catalog


def _select_expected_chunk_ids(case: dict, chunks_by_source: dict[str, list[dict]]) -> tuple[list[int], str, list[str]]:
    source_uri = str(case.get("expected_source_uri") or "").strip()
    if not source_uri:
        return [], "no_expected_source_uri", []
    chunks = chunks_by_source.get(source_uri, [])
    if not chunks:
        return [], "source_uri_not_imported", []

    expected_terms = [str(term).strip() for term in case.get("expected_terms") or [] if str(term).strip()]
    selected: list[int] = []
    covered_terms: set[str] = set()
    for chunk in chunks:
        content = _normalize(chunk.get("content"))
        hits = [term for term in expected_terms if _normalize(term) in content]
        if hits:
            selected.append(int(chunk["id"]))
            covered_terms.update(hits)

    if selected:
        return selected, "expected_terms_in_source_chunks", sorted(covered_terms)

    # Source-only fallback keeps chunk recall interpretable for cases whose terms are
    # intentionally broader than the seed text, while still avoiding result-derived IDs.
    return [int(chunks[0]["id"])], "source_uri_first_chunk_fallback", []


def _build_chunk_backfilled_payload(base_payload: dict, chunks_by_source: dict[str, list[dict]]) -> tuple[dict, dict]:
    payload = copy.deepcopy(base_payload)
    payload["name"] = "P2-25 chunk id 回填版合成客服验收题库"
    payload["description"] = (
        "P2-25 本地对比：在 P2-23 合成脱敏题库基础上，根据 P2-24 seed 文档导入后的实际 chunk id "
        "动态回填 expected_chunk_ids，用于让 full_evidence_recall_at_5 变成可解释指标；不含真实客户资料。"
    )

    bound_case_count = 0
    unbound_case_count = 0
    term_matched_case_count = 0
    source_fallback_case_count = 0
    no_expected_source_uri_count = 0
    source_uri_not_imported_count = 0
    total_expected_chunk_links = 0
    max_expected_chunks_per_case = 0
    case_catalog: list[dict] = []

    for case in payload["cases"]:
        chunk_ids, strategy, covered_terms = _select_expected_chunk_ids(case, chunks_by_source)
        case["expected_chunk_ids"] = chunk_ids
        if chunk_ids:
            bound_case_count += 1
            total_expected_chunk_links += len(chunk_ids)
            max_expected_chunks_per_case = max(max_expected_chunks_per_case, len(chunk_ids))
        else:
            unbound_case_count += 1
        if strategy == "expected_terms_in_source_chunks":
            term_matched_case_count += 1
        elif strategy == "source_uri_first_chunk_fallback":
            source_fallback_case_count += 1
        elif strategy == "no_expected_source_uri":
            no_expected_source_uri_count += 1
        elif strategy == "source_uri_not_imported":
            source_uri_not_imported_count += 1

        case_catalog.append(
            {
                "external_case_id": case["external_case_id"],
                "source_channel": case["source_channel"],
                "source_category": case["source_category"],
                "question_hash": _hash_text(case["question"]),
                "expected_source_uri": case["expected_source_uri"],
                "expected_terms_count": len(case["expected_terms"]),
                "expected_terms_covered_count": len(covered_terms),
                "expected_chunk_ids_count": len(chunk_ids),
                "binding_strategy": strategy,
                "risk_level": case["risk_level"],
                "expected_human_review": case["expected_human_review"],
                "allow_auto_reply": case["allow_auto_reply"],
            }
        )

    summary = {
        "total_cases": len(payload["cases"]),
        "bound_case_count": bound_case_count,
        "unbound_case_count": unbound_case_count,
        "term_matched_case_count": term_matched_case_count,
        "source_fallback_case_count": source_fallback_case_count,
        "no_expected_source_uri_count": no_expected_source_uri_count,
        "source_uri_not_imported_count": source_uri_not_imported_count,
        "total_expected_chunk_links": total_expected_chunk_links,
        "max_expected_chunks_per_case": max_expected_chunks_per_case,
        "case_catalog_sample": case_catalog[:8],
        "case_catalog": case_catalog,
    }
    return payload, summary


def _create_evaluation_set(client, *, tenant_id: int, token: str, payload: dict, label: str) -> dict:
    return _json_response(
        client.post(
            f"/api/tenants/{tenant_id}/knowledge-evaluation-sets",
            headers={"Authorization": f"Bearer {token}"},
            json=payload,
        ),
        expected_status=201,
        label=label,
    )


def _run_evaluation(client, *, evaluation_set_id: int, token: str, top_k: int, low_confidence_threshold: float) -> dict:
    return _json_response(
        client.post(
            f"/api/knowledge-evaluation-sets/{evaluation_set_id}/runs",
            headers={"Authorization": f"Bearer {token}"},
            json={"top_k": top_k, "low_confidence_threshold": low_confidence_threshold},
        ),
        expected_status=201,
        label=f"run evaluation set {evaluation_set_id}",
    )


def _compact_run_with_customer_metrics(run: dict) -> dict:
    compact = _compact_run(run)
    source_summary = run.get("summary_payload") or {}
    compact["summary_payload"].update(
        {
            "full_evidence_cases": source_summary.get("full_evidence_cases"),
            "full_evidence_covered_cases": source_summary.get("full_evidence_covered_cases"),
            "full_evidence_recall_at_5": source_summary.get("full_evidence_recall_at_5"),
            "citation_precision": source_summary.get("citation_precision"),
            "citation_precision_cases": source_summary.get("citation_precision_cases"),
        }
    )
    return compact


def _metric_delta(after: float | int | None, before: float | int | None) -> float:
    return round(float(after or 0) - float(before or 0), 4)


def _build_comparison(*, baseline: dict, backfilled: dict) -> dict:
    baseline_summary = baseline["summary_payload"]
    backfilled_summary = backfilled["summary_payload"]
    return {
        "baseline_run_id": baseline["id"],
        "chunk_backfilled_run_id": backfilled["id"],
        "full_evidence_case_delta": int(backfilled_summary.get("full_evidence_cases") or 0)
        - int(baseline_summary.get("full_evidence_cases") or 0),
        "full_evidence_recall_at_5_delta": _metric_delta(
            backfilled_summary.get("full_evidence_recall_at_5"),
            baseline_summary.get("full_evidence_recall_at_5"),
        ),
        "citation_precision_delta": _metric_delta(
            backfilled_summary.get("citation_precision"),
            baseline_summary.get("citation_precision"),
        ),
        "expected_term_coverage_delta": _metric_delta(
            backfilled.get("expected_term_coverage"),
            baseline.get("expected_term_coverage"),
        ),
        "human_review_correctness_delta": _metric_delta(
            backfilled.get("human_review_correctness"),
            baseline.get("human_review_correctness"),
        ),
        "interpretation": (
            "P2-25 的核心收益不是直接提高回答质量，而是让 full_evidence_recall_at_5 "
            "从不可解释的 0 变成基于实际 chunk id 的可审计指标。"
        ),
    }


def _bindings_csv(case_catalog: list[dict]) -> str:
    output = io.StringIO()
    fields = [
        "external_case_id",
        "source_channel",
        "source_category",
        "question_hash",
        "expected_source_uri",
        "expected_terms_count",
        "expected_terms_covered_count",
        "expected_chunk_ids_count",
        "binding_strategy",
        "risk_level",
        "expected_human_review",
        "allow_auto_reply",
    ]
    writer = csv.DictWriter(output, fieldnames=fields)
    writer.writeheader()
    for item in case_catalog:
        writer.writerow({field: item.get(field, "") for field in fields})
    return output.getvalue()


def _comparison_markdown(result: dict) -> str:
    baseline = result["baseline_run"]
    backfilled = result["chunk_backfilled_run"]
    comparison = result["comparison"]
    binding = result["chunk_backfill"]
    return "\n".join(
        [
            "# P2-25 chunk id 回填评测对比",
            "",
            "本报告使用合成脱敏题库和合成 seed 知识文档，不包含真实客户资料；未调用外部模型，未写外部平台。",
            "",
            "## 运行摘要",
            "",
            "| 指标 | 原始题库 | chunk 回填题库 | 变化 |",
            "| --- | ---: | ---: | ---: |",
            f"| full_evidence_cases | {baseline['summary_payload']['full_evidence_cases']} | {backfilled['summary_payload']['full_evidence_cases']} | {comparison['full_evidence_case_delta']} |",
            f"| full_evidence_recall_at_5 | {baseline['summary_payload']['full_evidence_recall_at_5']} | {backfilled['summary_payload']['full_evidence_recall_at_5']} | {comparison['full_evidence_recall_at_5_delta']} |",
            f"| citation_precision | {baseline['summary_payload']['citation_precision']} | {backfilled['summary_payload']['citation_precision']} | {comparison['citation_precision_delta']} |",
            f"| expected_term_coverage | {baseline['expected_term_coverage']} | {backfilled['expected_term_coverage']} | {comparison['expected_term_coverage_delta']} |",
            f"| human_review_correctness | {baseline['human_review_correctness']} | {backfilled['human_review_correctness']} | {comparison['human_review_correctness_delta']} |",
            "",
            "## 回填覆盖",
            "",
            f"- 总题数：{binding['total_cases']}",
            f"- 已绑定 chunk id 题数：{binding['bound_case_count']}",
            f"- 未绑定题数：{binding['unbound_case_count']}",
            f"- 基于期望词命中绑定：{binding['term_matched_case_count']}",
            f"- 基于 source_uri 首块兜底绑定：{binding['source_fallback_case_count']}",
            f"- 缺少 expected_source_uri：{binding['no_expected_source_uri_count']}",
            "",
            "## 解释",
            "",
            comparison["interpretation"],
            "",
            "这一步仍然不评测自由文本答案，因此 `unsupported_answer_rate` 继续不能解释为幻觉率。",
            "",
        ]
    )


def run_p2_25_chunk_backfill_eval_comparison(
    *,
    seed_documents_path: Path | str = DEFAULT_SEED_DOCUMENTS,
    eval_bank_path: Path | str = DEFAULT_EVAL_BANK,
    top_k: int = 5,
    low_confidence_threshold: float = 0.2,
    output_dir: Path | str | None = None,
) -> dict:
    seed_path = Path(seed_documents_path)
    bank_path = Path(eval_bank_path)
    with _safe_local_embedding_env(), _local_test_client() as client:
        tenant, _, token = _bootstrap_owner(client)
        imported = _import_seed_documents(client, tenant_id=tenant["id"], token=token, path=seed_path)
        chunks_by_source, chunk_catalog = _fetch_chunks_by_source(
            client,
            token=token,
            imported_documents=imported["documents"],
        )
        import_result = run_customer_service_eval_bank_import(
            input_path=bank_path,
            name="P2-25 原始合成脱敏客服验收题库基线",
            description="P2-25 本地对比基线：不回填 expected_chunk_ids；不含真实客户资料。",
            status="active",
            create=False,
        )
        if import_result["status"] != "validated":
            raise RuntimeError(f"evaluation bank validation failed: {import_result}")
        baseline_payload = import_result["payload"]
        backfilled_payload, backfill_summary = _build_chunk_backfilled_payload(
            baseline_payload,
            chunks_by_source,
        )

        baseline_set = _create_evaluation_set(
            client,
            tenant_id=tenant["id"],
            token=token,
            payload=baseline_payload,
            label="create baseline evaluation set",
        )
        backfilled_set = _create_evaluation_set(
            client,
            tenant_id=tenant["id"],
            token=token,
            payload=backfilled_payload,
            label="create chunk-backfilled evaluation set",
        )
        baseline_run_raw = _run_evaluation(
            client,
            evaluation_set_id=baseline_set["id"],
            token=token,
            top_k=top_k,
            low_confidence_threshold=low_confidence_threshold,
        )
        backfilled_run_raw = _run_evaluation(
            client,
            evaluation_set_id=backfilled_set["id"],
            token=token,
            top_k=top_k,
            low_confidence_threshold=low_confidence_threshold,
        )
        headers = {"Authorization": f"Bearer {token}"}
        markdown_report = _json_response(
            client.get(f"/api/knowledge-evaluation-runs/{backfilled_run_raw['id']}/report?format=markdown", headers=headers),
            expected_status=200,
            label="export chunk-backfilled markdown report",
        )
        csv_report = _json_response(
            client.get(f"/api/knowledge-evaluation-runs/{backfilled_run_raw['id']}/report?format=csv", headers=headers),
            expected_status=200,
            label="export chunk-backfilled csv report",
        )

    baseline_run = _compact_run_with_customer_metrics(baseline_run_raw)
    backfilled_run = _compact_run_with_customer_metrics(backfilled_run_raw)
    result = {
        "status": "completed",
        "phase": "P2-25",
        "seed_documents_file": str(seed_path),
        "eval_bank_file": str(bank_path),
        "raw_text_logged": False,
        "provider_call_performed": False,
        "external_platform_write_performed": False,
        "internal_database_write_performed": True,
        "seed_document_count": len(imported["documents"]),
        "seed_chunk_count": imported["chunk_count"],
        "chunk_catalog": chunk_catalog,
        "baseline_evaluation_set": {
            "id": baseline_set["id"],
            "case_count": baseline_set["case_count"],
            "evaluation_mode": baseline_set["evaluation_mode"],
        },
        "chunk_backfilled_evaluation_set": {
            "id": backfilled_set["id"],
            "case_count": backfilled_set["case_count"],
            "evaluation_mode": backfilled_set["evaluation_mode"],
        },
        "baseline_run": baseline_run,
        "chunk_backfilled_run": backfilled_run,
        "comparison": _build_comparison(baseline=baseline_run, backfilled=backfilled_run),
        "chunk_backfill": {
            key: value
            for key, value in backfill_summary.items()
            if key != "case_catalog"
        },
        "reports": {
            "markdown": _compact_report(markdown_report),
            "csv": _compact_report(csv_report),
        },
    }
    if output_dir is not None:
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        (out / "p2_25_chunk_backfill_eval_comparison_summary.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        (out / "p2_25_chunk_backfill_eval_comparison.md").write_text(
            _comparison_markdown(result),
            encoding="utf-8",
        )
        (out / "p2_25_chunk_backfill_case_bindings.csv").write_text(
            _bindings_csv(backfill_summary["case_catalog"]),
            encoding="utf-8",
        )
        (out / markdown_report["filename"]).write_text(markdown_report["body"], encoding="utf-8")
        (out / csv_report["filename"]).write_text(csv_report["body"], encoding="utf-8")
        result["output_dir"] = str(out)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Run P2-25 chunk-id backfill comparison locally.")
    parser.add_argument("--seed-documents", type=Path, default=DEFAULT_SEED_DOCUMENTS)
    parser.add_argument("--eval-bank", type=Path, default=DEFAULT_EVAL_BANK)
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--low-confidence-threshold", type=float, default=0.2)
    parser.add_argument("--output-dir", type=Path, default=None)
    args = parser.parse_args()

    result = run_p2_25_chunk_backfill_eval_comparison(
        seed_documents_path=args.seed_documents,
        eval_bank_path=args.eval_bank,
        top_k=args.top_k,
        low_confidence_threshold=args.low_confidence_threshold,
        output_dir=args.output_dir,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
