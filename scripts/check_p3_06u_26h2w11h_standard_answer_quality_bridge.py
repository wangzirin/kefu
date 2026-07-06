#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = ROOT / "output/p3_06u_26h2w11h_standard_answer_quality_bridge"
STANDARD_ANSWER_TEMPLATE = ROOT / "evals/p3_06u_26h2w11g_customer_standard_answer_template.csv"
H2W11G_SUMMARY = ROOT / "output/p3_06u_26h2w11g_customer_standard_answer_readiness/summary.json"
H2W11B_SUMMARY = ROOT / "output/p3_06u_26h2w11b_quality_repair/summary.json"
REPAIRED_RERUN_SUMMARY = ROOT / "output/p3_06u_26h2w11b_quality_repair/repaired_h2w11a_rerun/summary.json"
FINAL_ANSWER_LABELS = ROOT / "output/p3_06u_26h2w11b_quality_repair/repaired_h2w11a_rerun/customer_service_eval_run_1_final_answer_labels.csv"
EVAL_CASES = ROOT / "output/p3_06u_26h2w11b_quality_repair/repaired_h2w11a_rerun/customer_service_eval_run_1_cases.csv"
QUALITY_REVIEW = ROOT / "output/p3_06u_26h2w11b_quality_repair/repaired_h2w11a_rerun/customer_service_eval_run_1_review.md"
DOC_PATH = ROOT / "docs/P3-06U-26H2W11H_STANDARD_ANSWER_QUALITY_BRIDGE.md"
PRODUCT_PLAN_PATH = ROOT / "docs/PRODUCTIZATION_MASTER_PLAN_LITE_AND_STANDARD.md"
NETWORK_PLAN_PATH = ROOT / "docs/P3-06U-26H2W_NETWORKED_ENGINEERING_MASTER_PLAN.md"
README_PATH = ROOT / "README.md"


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _split_multi(value: str) -> list[str]:
    return [item.strip() for item in (value or "").replace("；", ";").split(";") if item.strip()]


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _counter_to_dict(counter: Counter[str]) -> dict[str, int]:
    return {key: counter[key] for key in sorted(counter)}


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_report(path: Path, result: dict[str, Any]) -> None:
    bridge = result["bridge"]
    formal = result["formal_accuracy_gate"]
    lines = [
        "# H2W-11H 标准答案质量桥接报告",
        "",
        "## 结论",
        "",
        f"- 桥接状态：{result['status']}",
        f"- 标准答案模板行数：{bridge['standard_answer_rows']}",
        f"- 最终答案标签行数：{bridge['final_answer_label_rows']}",
        f"- 标准答案来源覆盖：{bridge['matched_standard_answer_sources']}/{bridge['standard_answer_source_count']}",
        f"- 正式准确率签收：{'可进入' if formal['ready_for_formal_accuracy_signoff'] else '不可进入'}",
        "",
        "## 当前阻断正式签收的原因",
        "",
    ]
    for reason in formal["blocking_reasons"]:
        lines.append(f"- {reason}")
    lines.extend(
        [
            "",
            "## 来源覆盖",
            "",
            "| 来源 URI | 标准答案模板 | 最终答案标签 | 状态 |",
            "| --- | ---: | ---: | --- |",
        ]
    )
    for item in bridge["source_bridge_rows"]:
        lines.append(
            f"| {item['source_uri']} | {item['standard_answer_rows']} | {item['final_answer_label_rows']} | {item['status']} |"
        )
    lines.extend(
        [
            "",
            "## 质量标签摘要",
            "",
            f"- final_answer_factuality_status：`{bridge['final_answer_factuality_status_counts']}`",
            f"- citation_sufficient：`{bridge['citation_sufficient_counts']}`",
            f"- forbidden_commitment_passed：`{bridge['forbidden_commitment_passed_counts']}`",
            f"- handoff_correct：`{bridge['handoff_correct_counts']}`",
            "",
            "## 边界",
            "",
            "- 本报告不包含原始客户问题。",
            "- 本报告不包含最终答案正文。",
            "- 本报告不调用真实模型。",
            "- 本报告不打开真实外发。",
            "- 本报告不是正式客户准确率签收。",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _boundaries() -> dict[str, bool]:
    return {
        "provider_call_performed": False,
        "external_platform_write_performed": False,
        "real_platform_send_performed": False,
        "formal_customer_signoff_performed": False,
        "electronic_signature_performed": False,
        "real_customer_data_used": False,
        "final_answer_text_exported": False,
        "ready_for_formal_accuracy_signoff": False,
    }


def run_h2w11h_standard_answer_quality_bridge_gate(
    *,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
) -> dict[str, Any]:
    blockers: list[str] = []
    warnings: list[str] = []

    required_files = [
        STANDARD_ANSWER_TEMPLATE,
        H2W11G_SUMMARY,
        H2W11B_SUMMARY,
        REPAIRED_RERUN_SUMMARY,
        FINAL_ANSWER_LABELS,
        EVAL_CASES,
        QUALITY_REVIEW,
        DOC_PATH,
        PRODUCT_PLAN_PATH,
        NETWORK_PLAN_PATH,
        README_PATH,
    ]
    for path in required_files:
        if not path.exists():
            blockers.append(f"required file missing: {path.relative_to(ROOT)}")

    if blockers:
        result = {
            "phase": "H2W-11H",
            "status": "blocked",
            "blockers": blockers,
            "warnings": warnings,
            "boundaries": _boundaries(),
        }
        _write_json(output_dir / "summary.json", result)
        return result

    standard_rows = _read_rows(STANDARD_ANSWER_TEMPLATE)
    final_rows = _read_rows(FINAL_ANSWER_LABELS)
    case_rows = _read_rows(EVAL_CASES)
    h2w11g = _read_json(H2W11G_SUMMARY)
    h2w11b = _read_json(H2W11B_SUMMARY)
    rerun = _read_json(REPAIRED_RERUN_SUMMARY)

    standard_sources = Counter(row["expected_source_uri"].strip() for row in standard_rows if row.get("expected_source_uri"))
    label_sources: Counter[str] = Counter()
    for row in final_rows:
        for source in _split_multi(row.get("citation_uris", "")):
            label_sources[source] += 1
    case_sources = Counter(row.get("top_source_uri", "").strip() for row in case_rows if row.get("top_source_uri"))

    source_bridge_rows: list[dict[str, Any]] = []
    for source_uri in sorted(set(standard_sources) | set(label_sources)):
        standard_count = standard_sources.get(source_uri, 0)
        label_count = label_sources.get(source_uri, 0)
        if standard_count and label_count:
            status = "matched"
        elif standard_count and not label_count:
            status = "missing_in_current_final_answer_labels"
        else:
            status = "label_source_without_standard_answer_template"
        source_bridge_rows.append(
            {
                "source_uri": source_uri,
                "standard_answer_rows": standard_count,
                "final_answer_label_rows": label_count,
                "retrieval_case_rows": case_sources.get(source_uri, 0),
                "status": status,
            }
        )

    text_exported_rows = [
        row.get("external_case_id") or row.get("evaluation_run_case_id") or "unknown"
        for row in final_rows
        if (row.get("final_answer_text") or "").strip()
    ]
    label_status_counter = Counter(row.get("final_answer_factuality_status", "missing") or "missing" for row in final_rows)
    citation_sufficient_counter = Counter(row.get("citation_sufficient", "missing") or "missing" for row in final_rows)
    forbidden_counter = Counter(row.get("forbidden_commitment_passed", "missing") or "missing" for row in final_rows)
    handoff_counter = Counter(row.get("handoff_correct", "missing") or "missing" for row in final_rows)

    matched_standard_sources = sum(1 for source in standard_sources if label_sources.get(source, 0) > 0)
    missing_standard_sources = [source for source in sorted(standard_sources) if label_sources.get(source, 0) == 0]
    customer_confirmed_rows = [row["case_id"] for row in standard_rows if str(row.get("customer_confirmed", "")).lower() == "true"]

    if h2w11g.get("status") != "passed":
        blockers.append("H2W-11G must pass before H2W-11H")
    if h2w11b.get("status") != "completed":
        blockers.append("H2W-11B quality repair must stay completed before H2W-11H")
    repaired = h2w11b.get("repaired_metrics") or {}
    if repaired.get("report_status") != "controlled_trial_ready":
        blockers.append("H2W-11B report_status must stay controlled_trial_ready")
    if not rerun.get("checks", {}).get("evaluation.final_answer_samples_captured"):
        blockers.append("repaired H2W-11A rerun must include final answer samples")
    if text_exported_rows:
        blockers.append(f"final_answer_text must remain redacted in exported label CSV: {text_exported_rows[:5]}")
    if not final_rows:
        blockers.append("final answer labels are empty")
    if not standard_rows:
        blockers.append("standard answer template is empty")

    formal_blocking_reasons = []
    if missing_standard_sources:
        formal_blocking_reasons.append(
            "标准答案模板来源还没有全部出现在当前最终答案标签中；缺口："
            + "、".join(missing_standard_sources)
        )
    if not customer_confirmed_rows:
        formal_blocking_reasons.append("标准答案模板尚无客户确认行，不能进入正式准确率签收")
    if not text_exported_rows:
        formal_blocking_reasons.append("最终答案正文仍按脱敏要求不导出，当前只能做标签桥接，不能做逐字答案比对")
    if h2w11g.get("readiness", {}).get("ready_for_formal_accuracy_signoff") is not True:
        formal_blocking_reasons.append("H2W-11G 已明确 ready_for_formal_accuracy_signoff=false")

    bridge = {
        "standard_answer_rows": len(standard_rows),
        "final_answer_label_rows": len(final_rows),
        "retrieval_case_rows": len(case_rows),
        "standard_answer_source_count": len(standard_sources),
        "final_answer_label_source_count": len(label_sources),
        "matched_standard_answer_sources": matched_standard_sources,
        "missing_standard_answer_sources_in_final_labels": missing_standard_sources,
        "source_bridge_rows": source_bridge_rows,
        "final_answer_text_exported_rows": len(text_exported_rows),
        "final_answer_factuality_status_counts": _counter_to_dict(label_status_counter),
        "citation_sufficient_counts": _counter_to_dict(citation_sufficient_counter),
        "forbidden_commitment_passed_counts": _counter_to_dict(forbidden_counter),
        "handoff_correct_counts": _counter_to_dict(handoff_counter),
    }
    result = {
        "phase": "H2W-11H",
        "status": "passed" if not blockers else "blocked",
        "blockers": blockers,
        "warnings": warnings,
        "bridge": bridge,
        "formal_accuracy_gate": {
            "ready_for_formal_accuracy_signoff": False,
            "blocking_reasons": formal_blocking_reasons,
            "requires_customer_confirmed_standard_answers": True,
            "requires_answer_text_or_secure_comparison_runtime": True,
            "requires_all_standard_sources_in_eval_run": True,
        },
        "upstream": {
            "h2w11g_status": h2w11g.get("status"),
            "h2w11b_status": h2w11b.get("status"),
            "h2w11b_report_status": repaired.get("report_status"),
            "repaired_rerun_status": rerun.get("status"),
        },
        "evidence": {
            "standard_answer_template": {
                "path": str(STANDARD_ANSWER_TEMPLATE.relative_to(ROOT)),
                "sha256": _sha256_file(STANDARD_ANSWER_TEMPLATE),
            },
            "final_answer_labels": {
                "path": str(FINAL_ANSWER_LABELS.relative_to(ROOT)),
                "sha256": _sha256_file(FINAL_ANSWER_LABELS),
            },
            "quality_review": {
                "path": str(QUALITY_REVIEW.relative_to(ROOT)),
                "sha256": _sha256_file(QUALITY_REVIEW),
            },
        },
        "boundaries": _boundaries(),
    }
    _write_json(output_dir / "summary.json", result)
    _write_report(output_dir / "standard_answer_quality_bridge_report.md", result)
    return result


def main() -> None:
    result = run_h2w11h_standard_answer_quality_bridge_gate()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result["blockers"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
