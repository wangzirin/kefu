#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
import io
import json
import sys
from pathlib import Path
from typing import Any, Iterable, Sequence


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_ROOT = ROOT / "scripts"
DEFAULT_SEED_DOCUMENTS = ROOT / "evals" / "p2_24_seed_knowledge_documents.json"
DEFAULT_EVAL_BANK = ROOT / "evals" / "customer_service_eval_bank_synthetic_80_2026-06-26.csv"
DEFAULT_TOP_KS = (5, 8, 10, 12)

if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

from import_customer_service_eval_bank import run_customer_service_eval_bank_import  # noqa: E402
from run_p2_24_synthetic_eval_smoke import (  # noqa: E402
    _bootstrap_owner,
    _compact_report,
    _import_seed_documents,
    _json_response,
    _local_test_client,
    _safe_local_embedding_env,
)
from run_p2_25_chunk_backfill_eval_comparison import (  # noqa: E402
    _build_chunk_backfilled_payload,
    _compact_run_with_customer_metrics,
    _create_evaluation_set,
    _fetch_chunks_by_source,
    _hash_text,
    _run_evaluation,
)


def _normalize_top_ks(top_ks: Iterable[int]) -> tuple[int, ...]:
    values: list[int] = []
    for top_k in top_ks:
        value = int(top_k)
        if value < 1 or value > 20:
            raise ValueError("top_k must be between 1 and 20")
        if value not in values:
            values.append(value)
    if not values:
        raise ValueError("at least one top_k value is required")
    return tuple(values)


def _parse_top_ks(value: str) -> tuple[int, ...]:
    return _normalize_top_ks(int(part.strip()) for part in value.replace(";", ",").split(",") if part.strip())


def _float_metric(value: Any) -> float:
    return round(float(value or 0), 4)


def _run_summary(run: dict, *, top_k: int) -> dict:
    summary = run["summary_payload"]
    return {
        "run_id": run["id"],
        "top_k": top_k,
        "total_cases": run["total_cases"],
        "answered_cases": run["answered_cases"],
        "no_hit_cases": run["no_hit_cases"],
        "passed_cases": run["passed_cases"],
        "needs_review_cases": run["needs_review_cases"],
        "hit_rate": run["hit_rate"],
        "citation_coverage": run["citation_coverage"],
        "expected_term_coverage": run["expected_term_coverage"],
        "average_confidence": run["average_confidence"],
        "unsupported_answer_rate": run["unsupported_answer_rate"],
        "full_evidence_cases": summary.get("full_evidence_cases"),
        "full_evidence_covered_cases": summary.get("full_evidence_covered_cases"),
        "full_evidence_recall_at_k": summary.get("full_evidence_recall_at_5"),
        "legacy_metric_field": "full_evidence_recall_at_5",
        "citation_precision": summary.get("citation_precision"),
        "citation_precision_cases": summary.get("citation_precision_cases"),
        "human_review_correctness": run.get("human_review_correctness"),
        "knowledge_gap_rate": run.get("knowledge_gap_rate"),
        "forbidden_term_hits": run.get("forbidden_term_hits"),
        "embedding_provider": summary.get("embedding_provider"),
        "vector_store": summary.get("vector_store"),
        "retrieval_backend": summary.get("retrieval_backend"),
        "reranker": summary.get("reranker"),
        "low_confidence_threshold": summary.get("low_confidence_threshold"),
    }


def _best_recall_run(runs: Sequence[dict]) -> dict:
    return max(
        runs,
        key=lambda item: (
            _float_metric(item.get("full_evidence_recall_at_k")),
            _float_metric(item.get("citation_precision")),
            _float_metric(item.get("expected_term_coverage")),
            -int(item.get("needs_review_cases") or 0),
            -int(item.get("top_k") or 0),
        ),
    )


def _recommended_operational_run(runs: Sequence[dict]) -> dict:
    baseline = runs[0]
    baseline_recall = _float_metric(baseline.get("full_evidence_recall_at_k"))
    baseline_precision = _float_metric(baseline.get("citation_precision"))
    candidates = [
        run
        for run in runs
        if _float_metric(run.get("full_evidence_recall_at_k")) >= baseline_recall + 0.05
        and _float_metric(run.get("citation_precision")) >= baseline_precision - 0.08
        and int(run.get("forbidden_term_hits") or 0) <= 2
    ]
    if not candidates:
        candidates = [baseline]
    return max(
        candidates,
        key=lambda item: (
            _float_metric(item.get("full_evidence_recall_at_k")),
            _float_metric(item.get("expected_term_coverage")),
            _float_metric(item.get("citation_precision")),
            -int(item.get("forbidden_term_hits") or 0),
            -int(item.get("top_k") or 0),
        ),
    )


def _case_compact(case: dict, *, top_k: int) -> dict:
    payload = case.get("result_payload") or {}
    expected_chunk_ids = payload.get("expected_chunk_ids") if isinstance(payload.get("expected_chunk_ids"), list) else []
    returned_chunk_ids = (
        payload.get("returned_chunk_ids_top_k")
        if isinstance(payload.get("returned_chunk_ids_top_k"), list)
        else []
    )
    return {
        "top_k": top_k,
        "external_case_id": payload.get("external_case_id") or "",
        "question_hash": _hash_text(case.get("question") or ""),
        "source_channel": payload.get("source_channel") or "",
        "source_category": payload.get("source_category") or "",
        "question_type": payload.get("question_type") or "",
        "risk_level": payload.get("risk_level") or "",
        "expected_source_uri": payload.get("expected_source_uri") or "",
        "expected_document_title": payload.get("expected_document_title") or "",
        "expected_chunk_ids_count": len(expected_chunk_ids),
        "returned_chunk_ids_count": len(returned_chunk_ids),
        "status": case.get("status") or "",
        "failure_reason": case.get("failure_reason") or "",
        "top_chunk_id": case.get("top_chunk_id"),
        "top_document_id": case.get("top_document_id"),
        "top_score": case.get("top_score"),
        "top_confidence": case.get("top_confidence"),
        "full_evidence_recalled": bool(payload.get("full_evidence_recalled_at_5")),
        "citation_precision": payload.get("citation_precision"),
        "expected_human_review": bool(payload.get("expected_human_review")),
        "predicted_human_review": bool(payload.get("predicted_human_review")),
        "human_review_prediction_correct": bool(payload.get("human_review_prediction_correct")),
        "allow_auto_reply": bool(payload.get("allow_auto_reply")),
        "forbidden_term_hit_count": len(payload.get("forbidden_term_hits") or []),
    }


def _case_map(raw_run: dict, *, top_k: int) -> dict[str, dict]:
    cases: dict[str, dict] = {}
    for case in raw_run.get("case_results", []):
        item = _case_compact(case, top_k=top_k)
        external_case_id = str(item.get("external_case_id") or "")
        if external_case_id:
            cases[external_case_id] = item
    return cases


def _case_delta(*, case_maps: dict[int, dict[str, dict]], top_ks: Sequence[int]) -> dict:
    baseline_top_k = top_ks[0]
    baseline_cases = case_maps[baseline_top_k]
    compared_top_ks = list(top_ks[1:])

    initial_failed = [
        case
        for case in baseline_cases.values()
        if int(case.get("expected_chunk_ids_count") or 0) > 0 and not case.get("full_evidence_recalled")
    ]
    improved_cases: list[dict] = []
    still_missing_cases: list[dict] = []
    regressed_cases: list[dict] = []

    for case in initial_failed:
        external_case_id = str(case["external_case_id"])
        first_recovered: dict | None = None
        for top_k in compared_top_ks:
            compared = case_maps.get(top_k, {}).get(external_case_id)
            if compared and compared.get("full_evidence_recalled"):
                first_recovered = compared
                break
        row = {
            "external_case_id": external_case_id,
            "question_hash": case["question_hash"],
            "source_channel": case["source_channel"],
            "source_category": case["source_category"],
            "question_type": case["question_type"],
            "risk_level": case["risk_level"],
            "expected_source_uri": case["expected_source_uri"],
            "expected_chunk_ids_count": case["expected_chunk_ids_count"],
            "baseline_top_k": baseline_top_k,
            "baseline_failure_reason": case["failure_reason"],
            "baseline_returned_chunk_ids_count": case["returned_chunk_ids_count"],
            "baseline_citation_precision": case["citation_precision"],
        }
        if first_recovered:
            row.update(
                {
                    "outcome": "recovered",
                    "first_recovered_top_k": first_recovered["top_k"],
                    "first_recovered_failure_reason": first_recovered["failure_reason"],
                    "first_recovered_citation_precision": first_recovered["citation_precision"],
                    "first_recovered_returned_chunk_ids_count": first_recovered["returned_chunk_ids_count"],
                }
            )
            improved_cases.append(row)
        else:
            max_top_k = top_ks[-1]
            final_case = case_maps.get(max_top_k, {}).get(external_case_id, case)
            row.update(
                {
                    "outcome": "still_missing",
                    "first_recovered_top_k": "",
                    "final_top_k": max_top_k,
                    "final_failure_reason": final_case["failure_reason"],
                    "final_citation_precision": final_case["citation_precision"],
                    "final_returned_chunk_ids_count": final_case["returned_chunk_ids_count"],
                }
            )
            still_missing_cases.append(row)

    for case in baseline_cases.values():
        if not case.get("full_evidence_recalled"):
            continue
        external_case_id = str(case["external_case_id"])
        regressed_at = [
            top_k
            for top_k in compared_top_ks
            if case_maps.get(top_k, {}).get(external_case_id)
            and not case_maps[top_k][external_case_id].get("full_evidence_recalled")
        ]
        if regressed_at:
            regressed_cases.append(
                {
                    "external_case_id": external_case_id,
                    "question_hash": case["question_hash"],
                    "source_category": case["source_category"],
                    "baseline_top_k": baseline_top_k,
                    "regressed_at_top_ks": regressed_at,
                }
            )

    return {
        "baseline_top_k": baseline_top_k,
        "compared_top_ks": compared_top_ks,
        "initial_failed_case_count": len(initial_failed),
        "baseline_failed_recovered_count": len(improved_cases),
        "still_missing_case_count": len(still_missing_cases),
        "regressed_case_count": len(regressed_cases),
        "failed_case_sample": initial_failed[:10],
        "improved_cases": improved_cases,
        "still_missing_cases": still_missing_cases,
        "regressed_cases": regressed_cases,
    }


def _failed_delta_csv(case_delta: dict) -> str:
    output = io.StringIO()
    fields = [
        "external_case_id",
        "question_hash",
        "source_channel",
        "source_category",
        "question_type",
        "risk_level",
        "expected_source_uri",
        "expected_chunk_ids_count",
        "outcome",
        "baseline_top_k",
        "baseline_failure_reason",
        "baseline_returned_chunk_ids_count",
        "baseline_citation_precision",
        "first_recovered_top_k",
        "first_recovered_failure_reason",
        "first_recovered_citation_precision",
        "first_recovered_returned_chunk_ids_count",
        "final_top_k",
        "final_failure_reason",
        "final_citation_precision",
        "final_returned_chunk_ids_count",
    ]
    writer = csv.DictWriter(output, fieldnames=fields)
    writer.writeheader()
    for row in case_delta["improved_cases"] + case_delta["still_missing_cases"]:
        writer.writerow({field: row.get(field, "") for field in fields})
    return output.getvalue()


def _comparison_markdown(result: dict) -> str:
    lines = [
        "# P2-26 检索质量参数对比",
        "",
        "本报告使用合成脱敏题库和合成 seed 知识文档，不包含真实客户资料；未调用外部模型，未写外部平台。",
        "",
        "## 运行摘要",
        "",
        "| top_k | full_evidence_recall_at_k | full_evidence_covered_cases | citation_precision | expected_term_coverage | human_review_correctness | needs_review_cases |",
        "| ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for run in result["runs"]:
        lines.append(
            "| {top_k} | {recall} | {covered}/{full_cases} | {precision} | {term} | {human} | {review} |".format(
                top_k=run["top_k"],
                recall=run["full_evidence_recall_at_k"],
                covered=run["full_evidence_covered_cases"],
                full_cases=run["full_evidence_cases"],
                precision=run["citation_precision"],
                term=run["expected_term_coverage"],
                human=run["human_review_correctness"],
                review=run["needs_review_cases"],
            )
        )
    case_delta = result["case_delta"]
    best = result["best_run"]
    best_recall = result["best_recall_run"]
    lines.extend(
        [
            "",
            "## 失败题变化",
            "",
            f"- 基线 top_k：{case_delta['baseline_top_k']}",
            f"- 基线完整证据未召回题数：{case_delta['initial_failed_case_count']}",
            f"- 扩大 top-k 后转为完整召回题数：{case_delta['baseline_failed_recovered_count']}",
            f"- 到最大 top-k 仍未完整召回题数：{case_delta['still_missing_case_count']}",
            f"- 扩大 top-k 后回退题数：{case_delta['regressed_case_count']}",
            "",
            "## 当前建议",
            "",
            f"- 生产默认推荐 top_k：{best['top_k']}。",
            f"- 最高召回候选 top_k：{best_recall['top_k']}。",
            "- `full_evidence_recall_at_k` 由后端历史字段 `full_evidence_recall_at_5` 映射而来；本轮实际 top-k 已在每行单独记录。",
            "- 如果扩大 top-k 明显提升召回但 citation_precision 下滑，后续应引入更细的重排策略，而不是无上限加大召回条数。",
            "- 仍未完整召回的题，优先进入 seed 文档补充、chunk 粒度调整和期望词标注复核，而不是直接进入模型生成。",
            "",
        ]
    )
    return "\n".join(lines)


def run_p2_26_retrieval_quality_comparison(
    *,
    seed_documents_path: Path | str = DEFAULT_SEED_DOCUMENTS,
    eval_bank_path: Path | str = DEFAULT_EVAL_BANK,
    top_ks: Iterable[int] = DEFAULT_TOP_KS,
    low_confidence_threshold: float = 0.2,
    output_dir: Path | str | None = None,
) -> dict:
    seed_path = Path(seed_documents_path)
    bank_path = Path(eval_bank_path)
    normalized_top_ks = _normalize_top_ks(top_ks)

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
            name="P2-26 合成脱敏客服验收题库检索参数对比",
            description="P2-26 本地对比：复用 P2-25 chunk 回填逻辑，对多个 top_k 运行同一题库；不含真实客户资料。",
            status="active",
            create=False,
        )
        if import_result["status"] != "validated":
            raise RuntimeError(f"evaluation bank validation failed: {import_result}")
        backfilled_payload, backfill_summary = _build_chunk_backfilled_payload(
            import_result["payload"],
            chunks_by_source,
        )
        evaluation_set = _create_evaluation_set(
            client,
            tenant_id=tenant["id"],
            token=token,
            payload=backfilled_payload,
            label="create P2-26 chunk-backfilled evaluation set",
        )

        raw_runs_by_top_k: dict[int, dict] = {}
        runs: list[dict] = []
        case_maps: dict[int, dict[str, dict]] = {}
        for top_k in normalized_top_ks:
            raw_run = _run_evaluation(
                client,
                evaluation_set_id=evaluation_set["id"],
                token=token,
                top_k=top_k,
                low_confidence_threshold=low_confidence_threshold,
            )
            compact_run = _compact_run_with_customer_metrics(raw_run)
            raw_runs_by_top_k[top_k] = raw_run
            runs.append(_run_summary(compact_run, top_k=top_k))
            case_maps[top_k] = _case_map(raw_run, top_k=top_k)

        best_recall = _best_recall_run(runs)
        best = _recommended_operational_run(runs)
        best_raw_run = raw_runs_by_top_k[int(best["top_k"])]
        headers = {"Authorization": f"Bearer {token}"}
        markdown_report = _json_response(
            client.get(f"/api/knowledge-evaluation-runs/{best_raw_run['id']}/report?format=markdown", headers=headers),
            expected_status=200,
            label="export P2-26 best markdown report",
        )
        csv_report = _json_response(
            client.get(f"/api/knowledge-evaluation-runs/{best_raw_run['id']}/report?format=csv", headers=headers),
            expected_status=200,
            label="export P2-26 best csv report",
        )

    case_delta = _case_delta(case_maps=case_maps, top_ks=normalized_top_ks)
    result = {
        "status": "completed",
        "phase": "P2-26",
        "seed_documents_file": str(seed_path),
        "eval_bank_file": str(bank_path),
        "raw_text_logged": False,
        "provider_call_performed": False,
        "external_platform_write_performed": False,
        "internal_database_write_performed": True,
        "top_ks": list(normalized_top_ks),
        "seed_document_count": len(imported["documents"]),
        "seed_chunk_count": imported["chunk_count"],
        "chunk_catalog_count": len(chunk_catalog),
        "chunk_catalog_sample": chunk_catalog[:8],
        "evaluation_set": {
            "id": evaluation_set["id"],
            "case_count": evaluation_set["case_count"],
            "evaluation_mode": evaluation_set["evaluation_mode"],
        },
        "chunk_backfill": {
            key: value
            for key, value in backfill_summary.items()
            if key != "case_catalog"
        },
        "runs": runs,
        "best_run": best,
        "best_recall_run": best_recall,
        "case_delta": case_delta,
        "reports": {
            "best_markdown": _compact_report(markdown_report),
            "best_csv": _compact_report(csv_report),
        },
        "recommendation": {
            "candidate_default_top_k": best["top_k"],
            "candidate_recall_pool_top_k": best_recall["top_k"],
            "recommendation_logic": (
                "默认推荐优先要求完整证据召回相对基线至少提升 5 个百分点、citation_precision "
                "相对基线下降不超过 8 个百分点、禁用词证据命中不超过 2；最高召回候选只用于召回池或重排实验。"
            ),
            "do_not_interpret_unsupported_answer_rate_as_hallucination_rate": True,
            "next_step": (
                "Review still_missing_cases first; separate knowledge-document gaps, chunk granularity problems, "
                "lexical recall noise and reranker weakness before moving to model-assisted answer generation."
            ),
        },
    }
    if output_dir is not None:
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        for pattern in ("customer_service_eval_run_*_review.md", "customer_service_eval_run_*_cases.csv"):
            for stale_report in out.glob(pattern):
                stale_report.unlink()
        (out / "p2_26_retrieval_quality_comparison_summary.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        (out / "p2_26_retrieval_quality_comparison.md").write_text(
            _comparison_markdown(result),
            encoding="utf-8",
        )
        (out / "p2_26_failed_case_delta.csv").write_text(
            _failed_delta_csv(case_delta),
            encoding="utf-8",
        )
        (out / markdown_report["filename"]).write_text(markdown_report["body"], encoding="utf-8")
        (out / csv_report["filename"]).write_text(csv_report["body"], encoding="utf-8")
        result["output_dir"] = str(out)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Run P2-26 retrieval top-k quality comparison locally.")
    parser.add_argument("--seed-documents", type=Path, default=DEFAULT_SEED_DOCUMENTS)
    parser.add_argument("--eval-bank", type=Path, default=DEFAULT_EVAL_BANK)
    parser.add_argument("--top-ks", type=_parse_top_ks, default=DEFAULT_TOP_KS)
    parser.add_argument("--low-confidence-threshold", type=float, default=0.2)
    parser.add_argument("--output-dir", type=Path, default=None)
    args = parser.parse_args()

    result = run_p2_26_retrieval_quality_comparison(
        seed_documents_path=args.seed_documents,
        eval_bank_path=args.eval_bank,
        top_ks=args.top_ks,
        low_confidence_threshold=args.low_confidence_threshold,
        output_dir=args.output_dir,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
