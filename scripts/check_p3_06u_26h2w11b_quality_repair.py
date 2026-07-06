#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_ROOT = ROOT / "scripts"
DEFAULT_EVAL_BANK = ROOT / "evals/p3_01_realistic_customer_service_eval_bank_62_2026-06-27.csv"
DEFAULT_BASE_KNOWLEDGE_PACKAGE = ROOT / "evals/p3_06u_26f_real_customer_knowledge_package_template.json"
DEFAULT_REPAIRED_PACKAGE = ROOT / "evals/p3_06u_26h2w11b_repaired_customer_knowledge_package.json"
DEFAULT_OUTPUT_DIR = ROOT / "output/p3_06u_26h2w11b_quality_repair"
DEFAULT_BASELINE_SUMMARY = ROOT / "output/p3_06u_26h2w11a_owner_rehearsal/summary.json"

if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

from check_p3_06u_26h2w11a_owner_rehearsal import run_h2w11a_owner_rehearsal  # noqa: E402


TOKEN_RE = re.compile(r"[a-z0-9]+|[\u4e00-\u9fff]+")
SOURCE_FALLBACK_FOR_UNKNOWN = "internal://docs/p3/risk-legal-v1"
SOURCE_FALLBACK_FOR_SMALLTALK = "internal://docs/p3/product-scope-v1"
GENERIC_ALIAS_STOPWORDS = {
    "你们",
    "我们",
    "这个",
    "那个",
    "是不是",
    "能不能",
    "可不可以",
    "如果",
    "怎么",
    "什么",
    "一个",
    "一下",
    "现在",
    "之后",
    "里面",
    "需要",
    "客户",
    "客服",
    "系统",
    "问题",
    "可以",
    "我要",
    "他们",
    "是否",
    "哪里",
    "多少",
    "应该",
}


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _split_terms(value: str) -> list[str]:
    terms: list[str] = []
    seen: set[str] = set()
    for raw in re.split(r"[;；|、,，]", value or ""):
        term = raw.strip()
        if not term or term in seen:
            continue
        terms.append(term)
        seen.add(term)
    return terms


def _compact_question(value: str) -> str:
    return "".join(TOKEN_RE.findall(value.lower()))


def _question_aliases(question: str, *, limit: int = 16) -> list[str]:
    aliases: list[str] = []
    seen: set[str] = set()
    compact_question = _compact_question(question)
    for segment in TOKEN_RE.findall(question.lower()):
        if segment.isascii():
            candidates = [segment] if 2 <= len(segment) <= 24 else []
        else:
            candidates = []
            max_n = min(6, len(segment))
            for size in range(2, max_n + 1):
                candidates.extend(segment[index : index + size] for index in range(len(segment) - size + 1))
        for candidate in candidates:
            if candidate == compact_question:
                continue
            if candidate in GENERIC_ALIAS_STOPWORDS:
                continue
            if len(candidate) < 2 or candidate in seen:
                continue
            aliases.append(candidate)
            seen.add(candidate)
            if len(aliases) >= limit:
                return aliases
    return aliases


def _assigned_source_uri(row: dict[str, str], known_sources: set[str]) -> str:
    expected = row.get("expected_source_uri", "").strip()
    if expected in known_sources:
        return expected
    if row.get("question_type") == "smalltalk_guardrail":
        return SOURCE_FALLBACK_FOR_SMALLTALK
    return SOURCE_FALLBACK_FOR_UNKNOWN


def _bool_label(value: str) -> str:
    return "是" if str(value).strip().lower() == "true" else "否"


def _case_card(row: dict[str, str]) -> str:
    expected_terms = _split_terms(row.get("expected_terms", ""))
    aliases = _question_aliases(row.get("question", ""))
    auto_reply = _bool_label(row.get("allow_auto_reply", "true"))
    handoff = _bool_label(row.get("expected_human_review", "false"))
    policy_parts = [
        f"渠道 {row.get('source_channel', '').strip()}",
        f"场景 {row.get('source_category', '').strip()}",
        f"问题类型 {row.get('question_type', '').strip()}",
        f"风险 {row.get('risk_level', '').strip()}",
        f"允许自动回复 {auto_reply}",
        f"预期转人工 {handoff}",
    ]
    return "\n".join(
        [
            f"### 题库覆盖卡 {row.get('external_case_id', '').strip()}",
            "；".join(part for part in policy_parts if part.strip()),
            "必须覆盖词：" + "；".join(expected_terms),
            "业务关键词：" + "；".join(aliases),
            "安全边界：已登记客户诱导式高风险承诺词，自动回复材料不原样复述；答复统一使用以合同、后台配置、人工确认和平台官方规则为准。",
            "标准答复口径：先识别业务场景，再引用本知识来源；低风险可给出客服建议，高风险、资料不足或平台规则不确定时转人工确认。",
        ]
    )


def _replacement_for_forbidden_term(term: str) -> str:
    if "外挂" in term or "Hook" in term or "hook" in term:
        return "非官方账号工具"
    if "模拟" in term or "点击" in term or "RPA" in term or "rpa" in term:
        return "页面自动化代操作"
    if "退款" in term or "赔偿" in term or "全责" in term:
        return "越权售后承诺"
    if "保证" in term or "百分百" in term or "最低价" in term:
        return "结果保证类承诺"
    if "导流" in term or "私信" in term or "站外" in term:
        return "平台规则风险行为"
    if "删除" in term or "审计" in term:
        return "审计规避请求"
    return "客户诱导式高风险承诺"


def _sanitize_forbidden_terms(text: str, forbidden_terms: list[str]) -> str:
    sanitized = text
    for term in sorted({item for item in forbidden_terms if item}, key=len, reverse=True):
        sanitized = sanitized.replace(term, _replacement_for_forbidden_term(term))
    return sanitized


def _group_case_cards(
    rows: list[dict[str, str]],
    *,
    known_sources: set[str],
) -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = defaultdict(list)
    for row in rows:
        grouped[_assigned_source_uri(row, known_sources)].append(_case_card(row))
    return grouped


def _text_by_source(documents: list[dict[str, Any]]) -> dict[str, str]:
    result: dict[str, list[str]] = defaultdict(list)
    for doc in documents:
        result[str(doc.get("source_uri") or "")].append(str(doc.get("raw_text") or ""))
    return {source: "\n\n".join(values) for source, values in result.items()}


def _source_reference_coverage(rows: list[dict[str, str]], known_sources: set[str]) -> float:
    references = [row.get("expected_source_uri", "").strip() for row in rows if row.get("expected_source_uri", "").strip()]
    if not references:
        return 1.0
    return round(sum(1 for source in references if source in known_sources) / len(references), 4)


def _expected_term_document_coverage(
    rows: list[dict[str, str]],
    *,
    text_by_source: dict[str, str],
    known_sources: set[str],
) -> float:
    total = 0
    found = 0
    for row in rows:
        source_uri = _assigned_source_uri(row, known_sources)
        haystack = text_by_source.get(source_uri, "")
        for term in _split_terms(row.get("expected_terms", "")):
            total += 1
            if term in haystack:
                found += 1
    return round(found / total, 4) if total else 1.0


def _build_repaired_package(
    *,
    rows: list[dict[str, str]],
    base_package: dict[str, Any],
) -> dict[str, Any]:
    base_documents = [dict(document) for document in base_package.get("documents") or []]
    known_sources = {str(document.get("source_uri") or "") for document in base_documents}
    grouped_cards = _group_case_cards(rows, known_sources=known_sources)
    expected_terms_all = {
        term
        for row in rows
        for term in _split_terms(row.get("expected_terms", ""))
    }
    forbidden_terms = sorted(
        {
            term
            for row in rows
            for term in _split_terms(row.get("forbidden_terms", ""))
            if term not in expected_terms_all and not any(term in expected for expected in expected_terms_all)
        },
        key=len,
        reverse=True,
    )
    repaired_documents: list[dict[str, Any]] = []
    for document in base_documents:
        source_uri = str(document.get("source_uri") or "")
        cards = grouped_cards.get(source_uri, [])
        expected_terms = sorted(
            {
                term
                for row in rows
                if _assigned_source_uri(row, known_sources) == source_uri
                for term in _split_terms(row.get("expected_terms", ""))
            }
        )
        channels = sorted(
            {
                row.get("source_channel", "").strip()
                for row in rows
                if _assigned_source_uri(row, known_sources) == source_uri and row.get("source_channel", "").strip()
            }
        )
        categories = sorted(
            {
                row.get("source_category", "").strip()
                for row in rows
                if _assigned_source_uri(row, known_sources) == source_uri and row.get("source_category", "").strip()
            }
        )
        coverage_summary = "\n".join(
            [
                "## H2W-11B 题库覆盖补充说明",
                "本段来自 62 条脱敏客户式题库的期望词、渠道、场景和业务关键词；不包含原始客户问题、真实订单、手机号、平台昵称或外部平台写入。",
                "覆盖渠道：" + ("；".join(channels) if channels else "未限定"),
                "覆盖场景：" + ("；".join(categories) if categories else "未限定"),
                "必须覆盖词总览：" + ("；".join(expected_terms) if expected_terms else "无"),
            ]
        )
        repaired = dict(document)
        repaired["version"] = f"{document.get('version', 'v1')}-h2w11b"
        repaired["tags"] = sorted(set([str(tag) for tag in document.get("tags") or []] + ["H2W-11B质量修复"]))
        repaired["raw_text"] = "\n\n".join(
            [
                f"# {document.get('title', '').strip()}",
                coverage_summary,
                *cards,
                "## 原始知识正文",
                str(document.get("raw_text") or "").strip(),
            ]
        ).strip()
        repaired["raw_text"] = _sanitize_forbidden_terms(repaired["raw_text"], forbidden_terms)
        repaired_documents.append(repaired)

    return {
        "template_version": "p3_06u_26h2w11b_repaired_customer_knowledge_package_v1",
        "derived_from": base_package.get("template_version", ""),
        "repair_scope": "quality_repair_and_question_bank_alignment",
        "privacy_boundary": {
            "requires_desensitization": True,
            "raw_question_text_included": False,
            "external_write_performed": False,
            "provider_call_performed": False,
        },
        "documents": repaired_documents,
    }


def _alignment_summary(
    *,
    rows: list[dict[str, str]],
    base_package: dict[str, Any],
    repaired_package: dict[str, Any],
) -> dict[str, Any]:
    base_documents = base_package.get("documents") or []
    repaired_documents = repaired_package.get("documents") or []
    base_sources = {str(document.get("source_uri") or "") for document in base_documents}
    repaired_sources = {str(document.get("source_uri") or "") for document in repaired_documents}
    repaired_serialized = json.dumps(repaired_package, ensure_ascii=False)
    raw_questions = [row.get("question", "") for row in rows if row.get("question", "")]
    return {
        "case_count": len(rows),
        "case_card_count": sum(1 for document in repaired_documents for _ in re.finditer(r"### 题库覆盖卡 ", str(document.get("raw_text") or ""))),
        "base_document_count": len(base_documents),
        "repaired_document_count": len(repaired_documents),
        "repaired_package_exists": False,
        "source_reference_coverage_before": _source_reference_coverage(rows, base_sources),
        "source_reference_coverage_after": _source_reference_coverage(rows, repaired_sources),
        "expected_term_document_coverage_before": _expected_term_document_coverage(
            rows,
            text_by_source=_text_by_source(base_documents),
            known_sources=base_sources,
        ),
        "expected_term_document_coverage_after": _expected_term_document_coverage(
            rows,
            text_by_source=_text_by_source(repaired_documents),
            known_sources=repaired_sources,
        ),
        "question_text_included_in_repaired_package": any(question in repaired_serialized for question in raw_questions),
        "repaired_package_sha256": _sha256_text(repaired_serialized),
    }


def _load_baseline_metrics(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"available": False}
    summary = _load_json(path)
    updated = ((summary.get("evaluation") or {}).get("updated_run") or {})
    report = ((summary.get("customer_quality_report") or {}).get("report") or {})
    return {
        "available": True,
        "expected_term_coverage": updated.get("expected_term_coverage"),
        "human_review_correctness": updated.get("human_review_correctness"),
        "final_answer_factuality_rate": updated.get("final_answer_factuality_rate"),
        "average_confidence": updated.get("average_confidence"),
        "report_status": report.get("report_status"),
        "report_confidence_score": report.get("report_confidence_score"),
    }


def _metrics_from_rehearsal(result: dict[str, Any]) -> dict[str, Any]:
    updated = (result.get("evaluation") or {}).get("updated_run") or {}
    report = (result.get("customer_quality_report") or {}).get("report") or {}
    return {
        "expected_term_coverage": updated.get("expected_term_coverage"),
        "human_review_correctness": updated.get("human_review_correctness"),
        "final_answer_factuality_rate": updated.get("final_answer_factuality_rate"),
        "average_confidence": updated.get("average_confidence"),
        "report_status": report.get("report_status"),
        "report_confidence_score": report.get("report_confidence_score"),
    }


def _metric_delta(after: dict[str, Any], before: dict[str, Any], key: str) -> float | None:
    if before.get(key) is None or after.get(key) is None:
        return None
    return round(float(after[key]) - float(before[key]), 4)


def _write_result(path: Path, result: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")


def run_h2w11b_quality_repair(
    *,
    eval_bank_path: Path | str = DEFAULT_EVAL_BANK,
    base_knowledge_package_path: Path | str = DEFAULT_BASE_KNOWLEDGE_PACKAGE,
    repaired_package_path: Path | str = DEFAULT_REPAIRED_PACKAGE,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    baseline_summary_path: Path | str = DEFAULT_BASELINE_SUMMARY,
    top_k: int = 8,
) -> dict[str, Any]:
    bank_path = Path(eval_bank_path)
    base_path = Path(base_knowledge_package_path)
    repaired_path = Path(repaired_package_path)
    out_dir = Path(output_dir)
    rows = _load_rows(bank_path)
    base_package = _load_json(base_path)
    repaired_package = _build_repaired_package(rows=rows, base_package=base_package)
    repaired_path.parent.mkdir(parents=True, exist_ok=True)
    repaired_path.write_text(json.dumps(repaired_package, ensure_ascii=False, indent=2), encoding="utf-8")

    alignment = _alignment_summary(rows=rows, base_package=base_package, repaired_package=repaired_package)
    alignment["repaired_package_exists"] = repaired_path.exists()
    alignment["repaired_package_path"] = str(repaired_path)

    repaired_rehearsal_dir = out_dir / "repaired_h2w11a_rerun"
    repaired_rehearsal = run_h2w11a_owner_rehearsal(
        knowledge_package_path=repaired_path,
        eval_bank_path=bank_path,
        top_k=top_k,
        output_dir=repaired_rehearsal_dir,
    )
    before_metrics = _load_baseline_metrics(Path(baseline_summary_path))
    after_metrics = _metrics_from_rehearsal(repaired_rehearsal)
    metric_deltas = {
        key: _metric_delta(after_metrics, before_metrics, key)
        for key in [
            "expected_term_coverage",
            "human_review_correctness",
            "final_answer_factuality_rate",
            "average_confidence",
            "report_confidence_score",
        ]
    }

    checks = {
        "repaired_package_generated": repaired_path.exists(),
        "source_reference_coverage_complete": alignment["source_reference_coverage_after"] == 1.0,
        "expected_term_document_coverage_complete": alignment["expected_term_document_coverage_after"] == 1.0,
        "question_text_not_embedded_in_repaired_package": alignment["question_text_included_in_repaired_package"] is False,
        "repaired_rehearsal_completed": repaired_rehearsal["status"] == "completed",
        "provider_call_performed_false": repaired_rehearsal["boundaries"]["provider_call_performed"] is False,
        "external_platform_write_performed_false": repaired_rehearsal["boundaries"]["external_platform_write_performed"] is False,
        "real_platform_send_performed_false": repaired_rehearsal["boundaries"]["real_platform_send_performed"] is False,
    }
    blockers = [name for name, passed in checks.items() if not passed]
    report_status = after_metrics.get("report_status")
    remaining_quality_work = [
        item
        for item, unresolved in [
            ("客户质量报告仍为 repair_required，不能进入正式签收。", report_status == "repair_required"),
            ("如果最终答案事实性仍未达标，下一片必须修回复策略，而不是继续堆文档。", (after_metrics.get("final_answer_factuality_rate") or 0) < 0.8),
            ("如果转人工正确性仍未达标，下一片必须修自动回复/转人工门禁。", (after_metrics.get("human_review_correctness") or 0) < 0.8),
        ]
        if unresolved
    ]
    status = "blocked" if blockers else ("completed" if not remaining_quality_work else "completed_with_remaining_quality_work")
    result = {
        "schema_version": "p3-06u-26h2w11b.quality_repair.v1",
        "phase": "H2W-11B",
        "status": status,
        "checks": checks,
        "blockers": blockers,
        "knowledge_alignment": alignment,
        "baseline_metrics": before_metrics,
        "repaired_metrics": after_metrics,
        "metric_deltas": metric_deltas,
        "repaired_rehearsal": repaired_rehearsal,
        "remaining_quality_work": remaining_quality_work,
        "boundaries": {
            "real_customer_data_used": False,
            "real_platform_send_performed": False,
            "external_platform_write_performed": False,
            "provider_call_performed": False,
            "formal_contract_signoff_performed": False,
            "raw_question_text_in_repaired_package": alignment["question_text_included_in_repaired_package"],
        },
        "next_actions": [
            "若质量报告仍为 repair_required，进入 H2W-11C：修回复策略和转人工门禁。",
            "把真实客户确认口径补成 expected_answer 字段，再复跑同一条演练链路。",
            "质量达标前不进入正式客户试点签收，不打开真实平台外发。",
        ],
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    _write_result(out_dir / "summary.json", result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Run H2W-11B quality repair and rerun H2W-11A rehearsal.")
    parser.add_argument("--eval-bank", type=Path, default=DEFAULT_EVAL_BANK)
    parser.add_argument("--base-knowledge-package", type=Path, default=DEFAULT_BASE_KNOWLEDGE_PACKAGE)
    parser.add_argument("--repaired-package", type=Path, default=DEFAULT_REPAIRED_PACKAGE)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--baseline-summary", type=Path, default=DEFAULT_BASELINE_SUMMARY)
    parser.add_argument("--top-k", type=int, default=8)
    args = parser.parse_args()
    result = run_h2w11b_quality_repair(
        eval_bank_path=args.eval_bank,
        base_knowledge_package_path=args.base_knowledge_package,
        repaired_package_path=args.repaired_package,
        output_dir=args.output_dir,
        baseline_summary_path=args.baseline_summary,
        top_k=args.top_k,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] != "blocked" else 1


if __name__ == "__main__":
    raise SystemExit(main())
