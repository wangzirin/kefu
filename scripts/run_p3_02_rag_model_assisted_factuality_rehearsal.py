#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterable, Iterator


ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = ROOT / "backend"
SCRIPTS_ROOT = ROOT / "scripts"
DEFAULT_KNOWLEDGE_PACKAGE = ROOT / "evals" / "p3_01_realistic_knowledge_package_template.json"
DEFAULT_EVAL_BANK = ROOT / "evals" / "p3_01_realistic_customer_service_eval_bank_62_2026-06-27.csv"
DEFAULT_TOP_K = 8

for path in (BACKEND_ROOT, SCRIPTS_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from app.services.model_gateway import (  # noqa: E402
    DETERMINISTIC_PROVIDER,
    ModelDraftKnowledge,
    ModelDraftRequest,
    generate_reply_draft,
)
from import_customer_service_eval_bank import run_customer_service_eval_bank_import  # noqa: E402
from run_p2_24_synthetic_eval_smoke import (  # noqa: E402
    _bootstrap_owner,
    _import_seed_documents,
    _json_response,
    _local_test_client,
    _safe_local_embedding_env,
)
from run_p2_25_chunk_backfill_eval_comparison import (  # noqa: E402
    _build_chunk_backfilled_payload,
    _create_evaluation_set,
    _fetch_chunks_by_source,
    _hash_text,
    _run_evaluation,
)


EXTERNAL_MODEL_PROVIDERS = {"auto", "bailian", "deepseek"}
UNCERTAINTY_TERMS = ("人工确认", "人工审核", "暂时没有找到", "需要补充", "需要确认", "无法依据")
POLICY_RISK_TERMS = (
    "保证转化",
    "保证转化率",
    "保证 ROI",
    "保证最低价",
    "保证不封号",
    "永不出错",
    "无条件退款",
    "马上赔偿",
    "我们全责",
    "删除审计",
    "冒充人工",
)
SAFE_NEGATION_PREFIXES = ("不能", "不得", "不会", "不应", "避免", "禁止", "不直接", "不要")


@contextmanager
def _safe_model_env(*, allow_external_call: bool) -> Iterator[None]:
    keys = [
        "BAILIAN_API_KEY",
        "DEEPSEEK_API_KEY",
        "OUTBOX_EXTERNAL_WRITE_ENABLED",
    ]
    old_values = {key: os.environ.get(key) for key in keys}
    os.environ["OUTBOX_EXTERNAL_WRITE_ENABLED"] = "false"
    if not allow_external_call:
        os.environ["BAILIAN_API_KEY"] = ""
        os.environ["DEEPSEEK_API_KEY"] = ""
    try:
        yield
    finally:
        for key, value in old_values.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def _load_package(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list) or not data:
        raise ValueError("P3 knowledge package must contain a non-empty list")
    return [dict(item) for item in data]


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:24]


def _contains_safe_negation(text: str, term: str) -> bool:
    index = text.find(term)
    if index < 0:
        return False
    window = text[max(0, index - 8) : index]
    return any(prefix in window for prefix in SAFE_NEGATION_PREFIXES)


def _forbidden_hits(text: str, terms: Iterable[str]) -> list[str]:
    hits: list[str] = []
    for raw in terms:
        term = str(raw or "").strip()
        if not term:
            continue
        if term in text and not _contains_safe_negation(text, term):
            hits.append(term)
    return hits


def _policy_risk_hits(text: str) -> list[str]:
    return _forbidden_hits(text, POLICY_RISK_TERMS)


def _top_match_payload(case_result: dict) -> dict:
    payload = case_result.get("result_payload") or {}
    top_match = payload.get("top_match") or {}
    return top_match if isinstance(top_match, dict) else {}


def _knowledge_from_case(case_result: dict) -> list[ModelDraftKnowledge]:
    top_match = _top_match_payload(case_result)
    if not top_match:
        return []
    return [
        ModelDraftKnowledge(
            title=str(top_match.get("document_title") or ""),
            answer=str(top_match.get("content_preview") or ""),
            source_uri=str(top_match.get("source_uri") or ""),
            matched_terms=[str(term) for term in case_result.get("matched_terms") or []],
        )
    ]


def _source_matches_expected(payload: dict, top_match: dict) -> bool:
    expected_source_uri = str(payload.get("expected_source_uri") or "")
    if not expected_source_uri:
        return False
    source_uri = str(top_match.get("source_uri") or "")
    citation = top_match.get("citation") if isinstance(top_match.get("citation"), dict) else {}
    citation_source_uri = str(citation.get("source_uri") or "")
    return expected_source_uri in {source_uri, citation_source_uri}


def _suggested_label(
    *,
    supported: bool,
    forbidden_hits: list[str],
    evidence_missing: bool,
    expected_terms_found: bool,
) -> str:
    if forbidden_hits:
        return "unsafe"
    if evidence_missing:
        return "needs_policy"
    if supported and expected_terms_found:
        return "supported"
    if supported:
        return "partially_supported"
    return "unsupported"


def _score_case(case_result: dict, *, provider: str) -> dict:
    payload = case_result.get("result_payload") or {}
    top_match = _top_match_payload(case_result)
    knowledge = _knowledge_from_case(case_result)
    risk_level = str(payload.get("risk_level") or "low")
    question_type = str(payload.get("question_type") or "standard_customer_question")
    draft = generate_reply_draft(
        ModelDraftRequest(
            user_message=str(case_result.get("question") or ""),
            intent=question_type,
            knowledge=knowledge,
            provider=provider,
            confidence=float(case_result.get("top_confidence") or 0.0),
            risk_level=risk_level,
        )
    )
    draft_text = draft.draft_text or ""
    expected_terms = [str(term) for term in payload.get("expected_terms") or []]
    forbidden_terms = [str(term) for term in payload.get("forbidden_terms") or []]
    all_forbidden_hits = sorted(set(_forbidden_hits(draft_text, forbidden_terms) + _policy_risk_hits(draft_text)))
    evidence_missing = not bool(top_match) or not str(payload.get("expected_source_uri") or "")
    source_supported = bool(top_match) and (
        _source_matches_expected(payload, top_match) or not str(payload.get("expected_source_uri") or "")
    )
    expected_terms_found = bool(case_result.get("expected_terms_found"))
    uncertainty_when_missing = (not evidence_missing) or any(term in draft_text for term in UNCERTAINTY_TERMS)
    supported = (
        draft.status == "succeeded"
        and source_supported
        and bool(case_result.get("citation_present"))
        and not all_forbidden_hits
    )
    requires_review = bool(
        draft.human_review_required
        or payload.get("expected_human_review")
        or not payload.get("allow_auto_reply", True)
        or evidence_missing
        or risk_level in {"high", "critical"}
        or all_forbidden_hits
    )
    does_not_invent = bool(
        not all_forbidden_hits
        and (supported or (evidence_missing and uncertainty_when_missing))
        and not (not supported and expected_terms and not expected_terms_found and not requires_review)
    )
    recommended_label = _suggested_label(
        supported=supported,
        forbidden_hits=all_forbidden_hits,
        evidence_missing=evidence_missing,
        expected_terms_found=expected_terms_found,
    )
    return {
        "external_case_id": payload.get("external_case_id") or "",
        "question_hash": _hash_text(str(case_result.get("question") or "")),
        "source_channel": payload.get("source_channel") or "",
        "source_category": payload.get("source_category") or "",
        "question_type": question_type,
        "risk_level": risk_level,
        "expected_source_uri": payload.get("expected_source_uri") or "",
        "top_source_uri": top_match.get("source_uri") or "",
        "top_document_title": top_match.get("document_title") or "",
        "draft_hash": _hash(draft_text),
        "draft_chars": len(draft_text),
        "model_provider": draft.provider,
        "model_name": draft.model,
        "model_status": draft.status,
        "route_name": draft.route_name,
        "route_human_review_required": bool(draft.human_review_required),
        "answer_supported_by_citations": supported,
        "answer_has_forbidden_commitment": bool(all_forbidden_hits),
        "answer_requires_human_review": requires_review,
        "answer_mentions_uncertainty_when_evidence_missing": uncertainty_when_missing,
        "answer_does_not_invent_policy": does_not_invent,
        "recommended_factuality_label": recommended_label,
        "manual_factuality_label": "",
        "manual_factuality_label_required": True,
        "manual_factuality_label_status": "pending_manual_review",
        "forbidden_commitment_hits": all_forbidden_hits,
        "evidence_missing": evidence_missing,
        "expected_terms_found": expected_terms_found,
        "citation_present": bool(case_result.get("citation_present")),
        "failure_reason": case_result.get("failure_reason") or "",
    }


def _ratio(count: int, total: int) -> float:
    return round(count / total, 4) if total else 0.0


def _summary(rows: list[dict], *, provider_call_performed: bool, retrieval_run: dict) -> dict:
    total = len(rows)
    supported = sum(1 for row in rows if row["answer_supported_by_citations"])
    forbidden = sum(1 for row in rows if row["answer_has_forbidden_commitment"])
    review_required = sum(1 for row in rows if row["answer_requires_human_review"])
    uncertainty_ok = sum(1 for row in rows if row["answer_mentions_uncertainty_when_evidence_missing"])
    no_invention = sum(1 for row in rows if row["answer_does_not_invent_policy"])
    evidence_missing = sum(1 for row in rows if row["evidence_missing"])
    labels: dict[str, int] = {}
    for row in rows:
        labels[row["recommended_factuality_label"]] = labels.get(row["recommended_factuality_label"], 0) + 1
    return {
        "total_cases": total,
        "answer_supported_by_citations_cases": supported,
        "answer_supported_by_citations_rate": _ratio(supported, total),
        "answer_has_forbidden_commitment_cases": forbidden,
        "answer_has_forbidden_commitment_rate": _ratio(forbidden, total),
        "answer_requires_human_review_cases": review_required,
        "answer_requires_human_review_rate": _ratio(review_required, total),
        "answer_mentions_uncertainty_when_evidence_missing_cases": uncertainty_ok,
        "answer_mentions_uncertainty_when_evidence_missing_rate": _ratio(uncertainty_ok, total),
        "answer_does_not_invent_policy_cases": no_invention,
        "answer_does_not_invent_policy_rate": _ratio(no_invention, total),
        "evidence_missing_cases": evidence_missing,
        "recommended_factuality_label_counts": labels,
        "manual_factuality_labels_collected": 0,
        "manual_factuality_label_required": True,
        "provider_call_performed": provider_call_performed,
        "retrieval_hit_rate": retrieval_run.get("hit_rate"),
        "retrieval_citation_coverage": retrieval_run.get("citation_coverage"),
        "retrieval_expected_term_coverage": retrieval_run.get("expected_term_coverage"),
        "retrieval_human_review_correctness": (retrieval_run.get("summary_payload") or {}).get(
            "human_review_correctness"
        ),
    }


def _cases_csv(rows: list[dict]) -> str:
    fields = [
        "external_case_id",
        "question_hash",
        "source_channel",
        "source_category",
        "question_type",
        "risk_level",
        "expected_source_uri",
        "top_source_uri",
        "top_document_title",
        "draft_hash",
        "draft_chars",
        "model_provider",
        "model_name",
        "model_status",
        "route_name",
        "answer_supported_by_citations",
        "answer_has_forbidden_commitment",
        "answer_requires_human_review",
        "answer_mentions_uncertainty_when_evidence_missing",
        "answer_does_not_invent_policy",
        "recommended_factuality_label",
        "manual_factuality_label",
        "manual_factuality_label_required",
        "manual_factuality_label_status",
        "evidence_missing",
        "expected_terms_found",
        "citation_present",
        "failure_reason",
    ]
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fields)
    writer.writeheader()
    for row in rows:
        writer.writerow({field: row.get(field, "") for field in fields})
    return output.getvalue()


def _markdown_table(headers: list[str], rows: list[list[Any]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(item).replace("|", "\\|").replace("\n", " ") for item in row) + " |")
    return "\n".join(lines)


def _markdown_report(result: dict) -> str:
    summary = result["summary"]
    sample_rows = result["cases"][:12]
    return "\n".join(
        [
            "# P3-02 生成答案事实性与引用支撑 rehearsal",
            "",
            "## 安全边界",
            "",
            "- raw_text_logged=false",
            f"- provider_call_performed={str(result['provider_call_performed']).lower()}",
            "- external_platform_write_performed=false",
            "- 本报告不导出原始问题、模型草稿正文或客户隐私，只保留 question_hash、draft_hash 和可计算事实性字段。",
            "- manual_factuality_label_status=pending_manual_review；本轮 rehearsal 不把规则判定冒充人工事实性标签。",
            "",
            "## 运行摘要",
            "",
            _markdown_table(
                ["指标", "值"],
                [
                    ["phase", result["phase"]],
                    ["total_cases", summary["total_cases"]],
                    ["answer_supported_by_citations_rate", summary["answer_supported_by_citations_rate"]],
                    ["answer_has_forbidden_commitment_cases", summary["answer_has_forbidden_commitment_cases"]],
                    ["answer_requires_human_review_cases", summary["answer_requires_human_review_cases"]],
                    [
                        "answer_mentions_uncertainty_when_evidence_missing_rate",
                        summary["answer_mentions_uncertainty_when_evidence_missing_rate"],
                    ],
                    ["answer_does_not_invent_policy_rate", summary["answer_does_not_invent_policy_rate"]],
                    ["manual_factuality_labels_collected", summary["manual_factuality_labels_collected"]],
                ],
            ),
            "",
            "## 推荐标签分布",
            "",
            _markdown_table(
                ["recommended_factuality_label", "count"],
                sorted(summary["recommended_factuality_label_counts"].items()),
            ),
            "",
            "## 逐题脱敏样例",
            "",
            _markdown_table(
                [
                    "external_case_id",
                    "question_hash",
                    "risk_level",
                    "supported",
                    "requires_review",
                    "no_invention",
                    "recommended_label",
                ],
                [
                    [
                        row["external_case_id"],
                        row["question_hash"],
                        row["risk_level"],
                        row["answer_supported_by_citations"],
                        row["answer_requires_human_review"],
                        row["answer_does_not_invent_policy"],
                        row["recommended_factuality_label"],
                    ]
                    for row in sample_rows
                ],
            ),
            "",
            "## 下一步",
            "",
            "- 如果要正式验收，必须用客户真实脱敏 50-100 题替换 P3-01 rehearsal bank，并由人工填入 manual_factuality_label。",
            "- 如果要真实调用百炼/千问，必须显式传 `--allow-external-call --limit N`，并记录 usage、延迟和人工复核结果。",
            "- 通过本轮门禁后，优先推进 P3-03 坐席工作台产品化，而不是继续扩展同类离线评测。",
            "",
        ]
    )


def _write_outputs(output_dir: Path, result: dict) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "p3_02_factuality_rehearsal_summary.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (output_dir / "p3_02_factuality_rehearsal.md").write_text(
        _markdown_report(result),
        encoding="utf-8",
    )
    (output_dir / "p3_02_factuality_rehearsal_cases.csv").write_text(
        _cases_csv(result["cases"]),
        encoding="utf-8",
    )


def run_p3_02_factuality_rehearsal(
    *,
    knowledge_package_path: Path | str = DEFAULT_KNOWLEDGE_PACKAGE,
    eval_bank_path: Path | str = DEFAULT_EVAL_BANK,
    top_k: int = DEFAULT_TOP_K,
    limit: int | None = None,
    provider: str = DETERMINISTIC_PROVIDER,
    allow_external_call: bool = False,
    low_confidence_threshold: float = 0.2,
    output_dir: Path | str | None = None,
) -> dict:
    package_path = Path(knowledge_package_path)
    bank_path = Path(eval_bank_path)
    provider = (provider or DETERMINISTIC_PROVIDER).strip()
    if provider in EXTERNAL_MODEL_PROVIDERS and provider != DETERMINISTIC_PROVIDER and not allow_external_call:
        return {
            "status": "blocked_external_call_not_allowed",
            "phase": "P3-02",
            "provider": provider,
            "provider_call_performed": False,
            "raw_text_logged": False,
            "external_platform_write_performed": False,
            "message": "External model providers require --allow-external-call and an explicit --limit.",
        }
    if allow_external_call and (limit is None or int(limit) < 1):
        return {
            "status": "blocked_missing_limit_for_external_call",
            "phase": "P3-02",
            "provider": provider,
            "provider_call_performed": False,
            "raw_text_logged": False,
            "external_platform_write_performed": False,
            "message": "External model calls require an explicit positive --limit.",
        }

    with _safe_local_embedding_env(), _safe_model_env(allow_external_call=allow_external_call), _local_test_client() as client:
        tenant, _, token = _bootstrap_owner(client)
        imported = _import_seed_documents(client, tenant_id=tenant["id"], token=token, path=package_path)
        chunks_by_source, chunk_catalog = _fetch_chunks_by_source(
            client,
            token=token,
            imported_documents=imported["documents"],
        )
        import_result = run_customer_service_eval_bank_import(
            input_path=bank_path,
            name="P3-02 客户式题库事实性 rehearsal",
            description="P3-02 本地 rehearsal：P3-01 客户式题库 + P3 知识包 + deterministic 模型草稿事实性门禁；不含真实客户资料。",
            status="active",
            create=False,
        )
        if import_result["status"] != "validated":
            raise RuntimeError(f"evaluation bank validation failed: {import_result}")
        payload, backfill_summary = _build_chunk_backfilled_payload(import_result["payload"], chunks_by_source)
        payload["name"] = "P3-02 客户式题库事实性 rehearsal"
        payload["description"] = (
            "P3-02 本地 rehearsal：先验证答案是否被引用证据支撑、是否有危险承诺、是否正确进入人工审核。"
            "本题库不是客户真实 50-100 题验收。"
        )
        if limit is not None:
            payload["cases"] = payload["cases"][: int(limit)]
        evaluation_set = _create_evaluation_set(
            client,
            tenant_id=tenant["id"],
            token=token,
            payload=payload,
            label="create P3-02 factuality evaluation set",
        )
        retrieval_run = _run_evaluation(
            client,
            evaluation_set_id=evaluation_set["id"],
            token=token,
            top_k=top_k,
            low_confidence_threshold=low_confidence_threshold,
        )
        cases = [_score_case(case, provider=provider) for case in retrieval_run["case_results"]]

    provider_call_performed = provider != DETERMINISTIC_PROVIDER and allow_external_call
    result = {
        "status": "completed",
        "phase": "P3-02",
        "knowledge_package_file": str(package_path),
        "eval_bank_file": str(bank_path),
        "raw_text_logged": False,
        "provider_call_performed": provider_call_performed,
        "external_platform_write_performed": False,
        "internal_database_write_performed": True,
        "model_provider_requested": provider,
        "top_k": top_k,
        "seed_document_count": len(imported["documents"]),
        "seed_chunk_count": imported["chunk_count"],
        "chunk_catalog_count": len(chunk_catalog),
        "chunk_backfill": {
            key: value
            for key, value in backfill_summary.items()
            if key != "case_catalog"
        },
        "evaluation_set": {
            "id": evaluation_set["id"],
            "case_count": evaluation_set["case_count"],
            "evaluation_mode": evaluation_set["evaluation_mode"],
        },
        "retrieval_run": {
            "id": retrieval_run["id"],
            "run_mode": retrieval_run["run_mode"],
            "retrieval_mode": retrieval_run["retrieval_mode"],
            "vector_engine": retrieval_run["vector_engine"],
            "hit_rate": retrieval_run["hit_rate"],
            "citation_coverage": retrieval_run["citation_coverage"],
            "expected_term_coverage": retrieval_run["expected_term_coverage"],
            "summary_payload": retrieval_run["summary_payload"],
        },
        "summary": _summary(cases, provider_call_performed=provider_call_performed, retrieval_run=retrieval_run),
        "cases": cases,
        "manual_review_contract": {
            "manual_factuality_label_required": True,
            "allowed_manual_factuality_labels": [
                "supported",
                "partially_supported",
                "unsupported",
                "unsafe",
                "needs_policy",
            ],
            "manual_labels_collected_in_this_rehearsal": 0,
            "llm_judge_used": False,
        },
        "next_step": (
            "Use the output cases CSV for human factuality labels, or move to P3-03 workbench productization "
            "after confirming the rehearsal gate is acceptable."
        ),
    }
    if output_dir is not None:
        out = Path(output_dir)
        _write_outputs(out, result)
        result["output_dir"] = str(out)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Run P3-02 model-assisted factuality rehearsal locally.")
    parser.add_argument("--knowledge-package", type=Path, default=DEFAULT_KNOWLEDGE_PACKAGE)
    parser.add_argument("--eval-bank", type=Path, default=DEFAULT_EVAL_BANK)
    parser.add_argument("--top-k", type=int, default=DEFAULT_TOP_K)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--provider", default=DETERMINISTIC_PROVIDER)
    parser.add_argument("--allow-external-call", action="store_true")
    parser.add_argument("--low-confidence-threshold", type=float, default=0.2)
    parser.add_argument("--output-dir", type=Path, default=None)
    args = parser.parse_args()

    result = run_p3_02_factuality_rehearsal(
        knowledge_package_path=args.knowledge_package,
        eval_bank_path=args.eval_bank,
        top_k=args.top_k,
        limit=args.limit,
        provider=args.provider,
        allow_external_call=args.allow_external_call,
        low_confidence_threshold=args.low_confidence_threshold,
        output_dir=args.output_dir,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
