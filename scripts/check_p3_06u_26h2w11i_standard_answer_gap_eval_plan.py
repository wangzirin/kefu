#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = ROOT / "output/p3_06u_26h2w11i_standard_answer_gap_eval_plan"
STANDARD_ANSWER_TEMPLATE = ROOT / "evals/p3_06u_26h2w11g_customer_standard_answer_template.csv"
H2W11H_SUMMARY = ROOT / "output/p3_06u_26h2w11h_standard_answer_quality_bridge/summary.json"
H2W11H_REPORT = ROOT / "output/p3_06u_26h2w11h_standard_answer_quality_bridge/standard_answer_quality_bridge_report.md"
GAP_EVAL_CASES = ROOT / "evals/p3_06u_26h2w11i_standard_answer_gap_eval_cases.csv"
GAP_LABEL_PLAN = ROOT / "evals/p3_06u_26h2w11i_standard_answer_gap_label_plan.csv"
DOC_PATH = ROOT / "docs/P3-06U-26H2W11I_STANDARD_ANSWER_GAP_EVAL_PLAN.md"
PRODUCT_PLAN_PATH = ROOT / "docs/PRODUCTIZATION_MASTER_PLAN_LITE_AND_STANDARD.md"
NETWORK_PLAN_PATH = ROOT / "docs/P3-06U-26H2W_NETWORKED_ENGINEERING_MASTER_PLAN.md"
README_PATH = ROOT / "README.md"

PII_PATTERNS = {
    "phone": re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)"),
    "email": re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
    "id_card": re.compile(r"(?<!\d)\d{17}[\dXx](?!\d)"),
}


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _write_rows(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def _check_pii(row: dict[str, str]) -> list[str]:
    scoped = [
        row.get("customer_question_summary", ""),
        row.get("business_object", ""),
        row.get("standard_answer", ""),
        row.get("annotation_notes", ""),
    ]
    haystack = "\n".join(scoped)
    return [name for name, pattern in PII_PATTERNS.items() if pattern.search(haystack)]


def _bool_text(value: str) -> str:
    return "true" if str(value).strip().lower() == "true" else "false"


def _write_report(path: Path, result: dict[str, Any]) -> None:
    coverage = result["coverage"]
    lines = [
        "# H2W-11I 标准答案缺口评测输入包",
        "",
        "## 结论",
        "",
        f"- 门禁状态：{result['status']}",
        f"- H2W-11H 缺口来源数：{coverage['missing_source_count_from_h2w11h']}",
        f"- 本轮生成缺口评测样本：{coverage['gap_eval_case_rows']}",
        f"- 已覆盖缺口来源：{coverage['covered_missing_source_count']}/{coverage['missing_source_count_from_h2w11h']}",
        f"- 可进入下一轮最终答案评测：{coverage['ready_for_next_final_answer_eval_run']}",
        f"- 正式准确率签收：{'可进入' if result['boundaries']['ready_for_formal_accuracy_signoff'] else '不可进入'}",
        "",
        "## 缺口来源",
        "",
    ]
    for source_uri in coverage["covered_missing_sources"]:
        rows_for_source = [row for row in result["gap_eval_cases"] if row["expected_source_uri"] == source_uri]
        lines.append(f"- {source_uri}：{len(rows_for_source)} 条待补评测样本")
    lines.extend(
        [
            "",
            "## 输出文件",
            "",
            f"- `{result['evidence']['gap_eval_cases']['path']}`",
            f"- `{result['evidence']['gap_label_plan']['path']}`",
            "",
            "## 边界",
            "",
            "- 本输入包不包含原始客户问题。",
            "- 本输入包不包含最终客服答案正文。",
            "- 本输入包不代表下一轮评测已经执行。",
            "- 本输入包不调用真实模型。",
            "- 本输入包不打开真实外发。",
            "- 本输入包不是正式客户准确率签收。",
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
        "final_answer_eval_run_performed": False,
        "ready_for_formal_accuracy_signoff": False,
    }


def run_h2w11i_standard_answer_gap_eval_plan_gate(
    *,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    gap_eval_cases_path: Path = GAP_EVAL_CASES,
    gap_label_plan_path: Path = GAP_LABEL_PLAN,
) -> dict[str, Any]:
    blockers: list[str] = []
    warnings: list[str] = []

    required_files = [
        STANDARD_ANSWER_TEMPLATE,
        H2W11H_SUMMARY,
        H2W11H_REPORT,
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
            "phase": "H2W-11I",
            "status": "blocked",
            "blockers": blockers,
            "warnings": warnings,
            "boundaries": _boundaries(),
        }
        _write_json(output_dir / "summary.json", result)
        return result

    bridge = _read_json(H2W11H_SUMMARY)
    standard_rows = _read_rows(STANDARD_ANSWER_TEMPLATE)
    missing_sources = bridge.get("bridge", {}).get("missing_standard_answer_sources_in_final_labels") or []
    missing_source_set = set(missing_sources)

    if bridge.get("status") != "passed":
        blockers.append("H2W-11H must pass before H2W-11I")
    if bridge.get("formal_accuracy_gate", {}).get("ready_for_formal_accuracy_signoff") is not False:
        blockers.append("H2W-11H must still mark formal accuracy signoff as false before gap planning")
    if not missing_sources:
        blockers.append("H2W-11H did not expose missing standard answer sources; H2W-11I has nothing to plan")

    gap_rows: list[dict[str, str]] = []
    label_plan_rows: list[dict[str, str]] = []
    seen_gap_ids: set[str] = set()
    for row in standard_rows:
        source_uri = (row.get("expected_source_uri") or "").strip()
        if source_uri not in missing_source_set:
            continue
        case_id = (row.get("case_id") or "").strip()
        gap_id = f"h2w11i-gap-{case_id.replace('h2w11g-', '')}"
        if gap_id in seen_gap_ids:
            blockers.append(f"duplicate gap case id: {gap_id}")
        seen_gap_ids.add(gap_id)

        pii = _check_pii(row)
        if pii:
            blockers.append(f"{case_id} contains PII-like value in template fields: {pii}")
        if _bool_text(row.get("customer_confirmed", "")) == "true":
            blockers.append(f"{case_id} customer_confirmed must remain false before real customer confirmation")

        standard_answer = row.get("standard_answer", "")
        forbidden_terms = row.get("forbidden_terms", "")
        for term in re.split(r"[;；|、,，]", forbidden_terms or ""):
            term = term.strip()
            if term and term in standard_answer:
                blockers.append(f"{case_id} standard_answer repeats forbidden term {term!r}")

        requires_secure_text = "true"
        if _bool_text(row.get("should_handoff", "")) == "true":
            next_action = "next_eval_should_verify_handoff_gate"
            expected_factuality_status = "not_applicable_if_handoff_correct"
            requires_secure_text = "false"
        else:
            next_action = "next_eval_should_generate_or_capture_final_answer_label"
            expected_factuality_status = "requires_manual_fact_label"

        gap_rows.append(
            {
                "gap_case_id": gap_id,
                "source_standard_case_id": case_id,
                "source_channel": row.get("source_channel", ""),
                "customer_scenario": row.get("customer_scenario", ""),
                "customer_question_summary": row.get("customer_question_summary", ""),
                "business_object": row.get("business_object", ""),
                "expected_source_uri": source_uri,
                "expected_document_title": row.get("expected_document_title", ""),
                "required_terms": row.get("required_terms", ""),
                "forbidden_terms": forbidden_terms,
                "allow_auto_reply": _bool_text(row.get("allow_auto_reply", "")),
                "should_handoff": _bool_text(row.get("should_handoff", "")),
                "handoff_reason": row.get("handoff_reason", ""),
                "risk_level": row.get("risk_level", ""),
                "required_citation": _bool_text(row.get("required_citation", "")),
                "standard_answer_sha256": _sha256_text(standard_answer),
                "customer_confirmed": _bool_text(row.get("customer_confirmed", "")),
                "sample_origin": row.get("sample_origin", ""),
                "next_eval_action": next_action,
            }
        )
        label_plan_rows.append(
            {
                "gap_case_id": gap_id,
                "expected_source_uri": source_uri,
                "expected_final_answer_factuality_status": expected_factuality_status,
                "expected_citation_sufficient": "true",
                "expected_forbidden_commitment_passed": "true",
                "expected_handoff_correct": "true",
                "requires_final_answer_sample": "true",
                "requires_secure_text_comparison_runtime": requires_secure_text,
                "final_answer_text_must_not_be_exported": "true",
            }
        )

    covered_sources = sorted({row["expected_source_uri"] for row in gap_rows})
    missing_without_candidate = sorted(missing_source_set - set(covered_sources))
    if missing_without_candidate:
        blockers.append(f"missing sources have no gap eval case candidates: {missing_without_candidate}")
    if len(gap_rows) < len(missing_source_set):
        blockers.append("gap eval case rows must be at least one per missing source")
    if not gap_rows:
        blockers.append("gap eval case plan is empty")

    gap_case_fieldnames = [
        "gap_case_id",
        "source_standard_case_id",
        "source_channel",
        "customer_scenario",
        "customer_question_summary",
        "business_object",
        "expected_source_uri",
        "expected_document_title",
        "required_terms",
        "forbidden_terms",
        "allow_auto_reply",
        "should_handoff",
        "handoff_reason",
        "risk_level",
        "required_citation",
        "standard_answer_sha256",
        "customer_confirmed",
        "sample_origin",
        "next_eval_action",
    ]
    label_plan_fieldnames = [
        "gap_case_id",
        "expected_source_uri",
        "expected_final_answer_factuality_status",
        "expected_citation_sufficient",
        "expected_forbidden_commitment_passed",
        "expected_handoff_correct",
        "requires_final_answer_sample",
        "requires_secure_text_comparison_runtime",
        "final_answer_text_must_not_be_exported",
    ]

    _write_rows(gap_eval_cases_path, gap_rows, gap_case_fieldnames)
    _write_rows(gap_label_plan_path, label_plan_rows, label_plan_fieldnames)

    coverage = {
        "missing_source_count_from_h2w11h": len(missing_sources),
        "missing_sources_from_h2w11h": missing_sources,
        "gap_eval_case_rows": len(gap_rows),
        "gap_label_plan_rows": len(label_plan_rows),
        "covered_missing_source_count": len(covered_sources),
        "covered_missing_sources": covered_sources,
        "missing_sources_without_candidate": missing_without_candidate,
        "ready_for_next_final_answer_eval_run": bool(gap_rows and not missing_without_candidate and not blockers),
        "ready_for_formal_accuracy_signoff": False,
    }
    result = {
        "phase": "H2W-11I",
        "status": "passed" if not blockers else "blocked",
        "blockers": blockers,
        "warnings": warnings,
        "coverage": coverage,
        "gap_eval_cases": gap_rows,
        "evidence": {
            "h2w11h_summary": {
                "path": str(H2W11H_SUMMARY.relative_to(ROOT)),
                "sha256": _sha256_file(H2W11H_SUMMARY),
            },
            "standard_answer_template": {
                "path": str(STANDARD_ANSWER_TEMPLATE.relative_to(ROOT)),
                "sha256": _sha256_file(STANDARD_ANSWER_TEMPLATE),
            },
            "gap_eval_cases": {
                "path": _display_path(gap_eval_cases_path),
                "sha256": _sha256_file(gap_eval_cases_path),
            },
            "gap_label_plan": {
                "path": _display_path(gap_label_plan_path),
                "sha256": _sha256_file(gap_label_plan_path),
            },
        },
        "boundaries": _boundaries(),
    }
    _write_json(output_dir / "summary.json", result)
    _write_report(output_dir / "standard_answer_gap_eval_plan.md", result)
    return result


def main() -> None:
    result = run_h2w11i_standard_answer_gap_eval_plan_gate()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result["blockers"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
