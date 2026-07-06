#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = ROOT / "output/p3_06u_26h2w11l_customer_standard_answer_confirmation_pack"
CONFIRMATION_PACK = ROOT / "evals/p3_06u_26h2w11l_customer_standard_answer_confirmation_pack.csv"
STANDARD_ANSWER_TEMPLATE = ROOT / "evals/p3_06u_26h2w11g_customer_standard_answer_template.csv"
H2W11G_SUMMARY = ROOT / "output/p3_06u_26h2w11g_customer_standard_answer_readiness/summary.json"
H2W11J_SUMMARY = ROOT / "output/p3_06u_26h2w11j_gap_final_answer_rehearsal/summary.json"
H2W11J_LABEL_EXPORT = ROOT / "output/p3_06u_26h2w11j_gap_final_answer_rehearsal/gap_final_answer_labels.csv"
H2W11K_SUMMARY = ROOT / "output/p3_06u_26h2w11k_customer_report_gap_rehearsal/summary.json"
DOC_PATH = ROOT / "docs/P3-06U-26H2W11L_CUSTOMER_STANDARD_ANSWER_CONFIRMATION_PACK.md"
PRODUCT_PLAN_PATH = ROOT / "docs/PRODUCTIZATION_MASTER_PLAN_LITE_AND_STANDARD.md"
NETWORK_PLAN_PATH = ROOT / "docs/P3-06U-26H2W_NETWORKED_ENGINEERING_MASTER_PLAN.md"
README_PATH = ROOT / "README.md"

CONFIRMATION_COLUMNS = [
    "confirmation_item_id",
    "source_standard_case_id",
    "source_channel",
    "customer_scenario",
    "customer_question_summary",
    "business_object",
    "standard_answer_for_customer_review",
    "required_terms",
    "forbidden_terms",
    "expected_source_uri",
    "expected_document_title",
    "allow_auto_reply",
    "should_handoff",
    "handoff_reason",
    "risk_level",
    "local_rehearsal_status",
    "final_answer_factuality_status",
    "citation_sufficient",
    "forbidden_commitment_passed",
    "handoff_correct",
    "needs_customer_confirmation",
    "customer_confirmed",
    "customer_reviewer",
    "customer_confirmed_at",
    "customer_revision_request",
    "signoff_scope",
    "not_formal_signoff",
]

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


def _write_rows(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CONFIRMATION_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _contains_pii(row: dict[str, str]) -> list[str]:
    scoped = [
        "customer_question_summary",
        "business_object",
        "standard_answer_for_customer_review",
        "customer_reviewer",
        "customer_revision_request",
    ]
    haystack = "\n".join(str(row.get(field) or "") for field in scoped)
    return [name for name, pattern in PII_PATTERNS.items() if pattern.search(haystack)]


def _bool(value: str) -> bool:
    return str(value).strip().lower() == "true"


def _build_confirmation_rows(
    standard_rows: list[dict[str, str]],
    gap_labels: list[dict[str, str]],
) -> list[dict[str, str]]:
    labels_by_standard_case = {
        row.get("source_standard_case_id", "").strip(): row
        for row in gap_labels
        if row.get("source_standard_case_id")
    }
    rows: list[dict[str, str]] = []
    for index, standard in enumerate(standard_rows, start=1):
        case_id = standard.get("case_id", "").strip()
        label = labels_by_standard_case.get(case_id)
        rows.append(
            {
                "confirmation_item_id": f"h2w11l-confirm-{index:03d}",
                "source_standard_case_id": case_id,
                "source_channel": standard.get("source_channel", ""),
                "customer_scenario": standard.get("customer_scenario", ""),
                "customer_question_summary": standard.get("customer_question_summary", ""),
                "business_object": standard.get("business_object", ""),
                "standard_answer_for_customer_review": standard.get("standard_answer", ""),
                "required_terms": standard.get("required_terms", ""),
                "forbidden_terms": standard.get("forbidden_terms", ""),
                "expected_source_uri": standard.get("expected_source_uri", ""),
                "expected_document_title": standard.get("expected_document_title", ""),
                "allow_auto_reply": standard.get("allow_auto_reply", "false"),
                "should_handoff": standard.get("should_handoff", "false"),
                "handoff_reason": standard.get("handoff_reason", ""),
                "risk_level": standard.get("risk_level", ""),
                "local_rehearsal_status": "gap_rehearsed" if label else "standard_answer_only",
                "final_answer_factuality_status": (label or {}).get("final_answer_factuality_status", ""),
                "citation_sufficient": (label or {}).get("citation_sufficient", ""),
                "forbidden_commitment_passed": (label or {}).get("forbidden_commitment_passed", ""),
                "handoff_correct": (label or {}).get("handoff_correct", ""),
                "needs_customer_confirmation": "true",
                "customer_confirmed": "false",
                "customer_reviewer": "",
                "customer_confirmed_at": "",
                "customer_revision_request": "",
                "signoff_scope": "standard_answer_only",
                "not_formal_signoff": "true",
            }
        )
    return rows


def _validate_confirmation_rows(rows: list[dict[str, str]]) -> tuple[list[str], dict[str, Any]]:
    blockers: list[str] = []
    source_uris = {row.get("expected_source_uri", "").strip() for row in rows if row.get("expected_source_uri")}
    rehearsed_rows = [row for row in rows if row.get("local_rehearsal_status") == "gap_rehearsed"]
    auto_reply_rows = [row for row in rows if _bool(row.get("allow_auto_reply", ""))]
    handoff_rows = [row for row in rows if _bool(row.get("should_handoff", ""))]
    customer_confirmed_rows = [row for row in rows if _bool(row.get("customer_confirmed", ""))]

    seen_ids: set[str] = set()
    for row in rows:
        item_id = row.get("confirmation_item_id", "")
        if item_id in seen_ids:
            blockers.append(f"duplicate confirmation_item_id: {item_id}")
        seen_ids.add(item_id)
        missing = [column for column in CONFIRMATION_COLUMNS if column not in row]
        if missing:
            blockers.append(f"{item_id or 'unknown'} missing columns: {missing}")
        if not row.get("source_standard_case_id"):
            blockers.append(f"{item_id} missing source_standard_case_id")
        if not row.get("standard_answer_for_customer_review"):
            blockers.append(f"{item_id} missing standard_answer_for_customer_review")
        if row.get("needs_customer_confirmation") != "true":
            blockers.append(f"{item_id} must keep needs_customer_confirmation=true")
        if row.get("customer_confirmed") != "false":
            blockers.append(f"{item_id} customer_confirmed must remain false before real customer review")
        if row.get("not_formal_signoff") != "true":
            blockers.append(f"{item_id} must keep not_formal_signoff=true")
        if row.get("signoff_scope") != "standard_answer_only":
            blockers.append(f"{item_id} signoff_scope must be standard_answer_only")
        if _bool(row.get("allow_auto_reply", "")) and _bool(row.get("should_handoff", "")):
            blockers.append(f"{item_id} cannot allow auto reply and require handoff at the same time")
        pii = _contains_pii(row)
        if pii:
            blockers.append(f"{item_id} has PII-like content: {pii}")

    metrics = {
        "confirmation_item_count": len(rows),
        "source_uri_count": len(source_uris),
        "gap_rehearsed_item_count": len(rehearsed_rows),
        "standard_answer_only_item_count": len(rows) - len(rehearsed_rows),
        "auto_reply_item_count": len(auto_reply_rows),
        "handoff_item_count": len(handoff_rows),
        "customer_confirmed_item_count": len(customer_confirmed_rows),
        "customer_confirmation_required_item_count": len(rows),
        "all_customer_confirmed": len(customer_confirmed_rows) == len(rows) and bool(rows),
    }
    return blockers, metrics


def _write_report(path: Path, result: dict[str, Any]) -> None:
    metrics = result["metrics"]
    lines = [
        "# H2W-11L 客户标准答案确认输入包",
        "",
        "## 结论",
        "",
        f"- 门禁状态：{result['status']}",
        f"- 待客户确认条目：{metrics['confirmation_item_count']}",
        f"- 已有缺口演练证据条目：{metrics['gap_rehearsed_item_count']}",
        f"- 仅标准答案待确认条目：{metrics['standard_answer_only_item_count']}",
        f"- 自动回复候选：{metrics['auto_reply_item_count']}",
        f"- 转人工候选：{metrics['handoff_item_count']}",
        f"- 当前客户确认条目：{metrics['customer_confirmed_item_count']}",
        f"- 正式准确率签收：{'可进入' if result['readiness']['ready_for_formal_accuracy_signoff'] else '不可进入'}",
        "",
        "## 客户需要确认什么",
        "",
        "- 标准答案是否符合业务事实。",
        "- 必含词是否足够表达关键口径。",
        "- 禁用词是否覆盖不能承诺、不能外发或必须转人工的边界。",
        "- 引用来源是否能作为对外回答依据。",
        "- 是否允许自动回复，还是必须转人工。",
        "",
        "## 输出文件",
        "",
        f"- `{result['evidence']['confirmation_pack']['path']}`",
        "",
        "## 停止门禁",
        "",
        "- `customer_confirmed=false` 时，不能进入正式准确率签收。",
        "- 没有真实题库、线上回执和正式报告签收时，不能写成完整线上准确率。",
        "- 本输入包不是电子签章、合同签收或客户验收。",
        "",
        "## 边界",
        "",
        "- 不调用真实模型 provider。",
        "- 不打开真实外发。",
        "- 不连接真实微信、企微、抖音、淘宝、京东或拼多多。",
        "- 不使用真实客户原始数据。",
    ]
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


def run_h2w11l_customer_standard_answer_confirmation_pack_gate(
    *,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    confirmation_pack_path: Path = CONFIRMATION_PACK,
) -> dict[str, Any]:
    blockers: list[str] = []
    warnings: list[str] = []
    for path in [
        STANDARD_ANSWER_TEMPLATE,
        H2W11G_SUMMARY,
        H2W11J_SUMMARY,
        H2W11J_LABEL_EXPORT,
        H2W11K_SUMMARY,
        DOC_PATH,
        PRODUCT_PLAN_PATH,
        NETWORK_PLAN_PATH,
        README_PATH,
    ]:
        if not path.exists():
            blockers.append(f"required file missing: {_display_path(path)}")

    if blockers:
        result = {
            "phase": "H2W-11L",
            "status": "blocked",
            "blockers": blockers,
            "warnings": warnings,
            "metrics": {},
            "readiness": {
                "ready_for_customer_standard_answer_confirmation_review": False,
                "ready_for_formal_accuracy_signoff": False,
            },
            "boundaries": _boundaries(),
        }
        _write_json(output_dir / "summary.json", result)
        return result

    h2w11g = _read_json(H2W11G_SUMMARY)
    h2w11j = _read_json(H2W11J_SUMMARY)
    h2w11k = _read_json(H2W11K_SUMMARY)
    standard_rows = _read_rows(STANDARD_ANSWER_TEMPLATE)
    gap_labels = _read_rows(H2W11J_LABEL_EXPORT)

    if h2w11g.get("status") != "passed":
        blockers.append("H2W-11G must pass before H2W-11L")
    if h2w11j.get("status") != "passed":
        blockers.append("H2W-11J must pass before H2W-11L")
    if h2w11k.get("status") != "passed":
        blockers.append("H2W-11K must pass before H2W-11L")
    if h2w11k.get("metrics", {}).get("ready_for_formal_accuracy_signoff") is not False:
        blockers.append("H2W-11K must keep ready_for_formal_accuracy_signoff=false")
    if any((row.get("final_answer_text") or "").strip() for row in gap_labels):
        blockers.append("H2W-11J label export must not include final_answer_text")
    if any(row.get("customer_confirmed") != "false" for row in gap_labels):
        blockers.append("H2W-11J label export must keep customer_confirmed=false")

    confirmation_rows = _build_confirmation_rows(standard_rows, gap_labels)
    row_blockers, metrics = _validate_confirmation_rows(confirmation_rows)
    blockers.extend(row_blockers)
    if metrics.get("confirmation_item_count", 0) < 10:
        blockers.append("customer confirmation pack needs at least 10 standard answer items")
    if metrics.get("gap_rehearsed_item_count", 0) < 7:
        blockers.append("customer confirmation pack should include at least 7 gap rehearsal evidence items")

    doc_text = DOC_PATH.read_text(encoding="utf-8")
    for token in [
        "# H2W-11L 客户标准答案确认输入包",
        "不是正式客户准确率签收",
        "customer_confirmed=false",
        "真实外发继续关闭",
    ]:
        if token not in doc_text:
            blockers.append(f"H2W-11L doc missing token: {token}")
    for path in [PRODUCT_PLAN_PATH, NETWORK_PLAN_PATH, README_PATH]:
        text = path.read_text(encoding="utf-8")
        if "H2W-11L" not in text or "客户标准答案确认输入包" not in text:
            blockers.append(f"{_display_path(path)} missing H2W-11L record")

    _write_rows(confirmation_pack_path, confirmation_rows)
    evidence = {
        "confirmation_pack": {
            "path": _display_path(confirmation_pack_path),
            "sha256": _sha256_file(confirmation_pack_path),
        },
        "source_standard_answer_template": {
            "path": _display_path(STANDARD_ANSWER_TEMPLATE),
            "sha256": _sha256_file(STANDARD_ANSWER_TEMPLATE),
        },
        "gap_label_export": {
            "path": _display_path(H2W11J_LABEL_EXPORT),
            "sha256": _sha256_file(H2W11J_LABEL_EXPORT),
        },
    }
    result = {
        "phase": "H2W-11L",
        "status": "passed" if not blockers else "blocked",
        "blockers": blockers,
        "warnings": warnings,
        "metrics": metrics,
        "readiness": {
            "ready_for_customer_standard_answer_confirmation_review": not blockers,
            "ready_for_formal_accuracy_signoff": False,
            "requires_customer_confirmed_standard_answers": True,
            "requires_real_question_bank": True,
            "requires_online_receipts": True,
            "requires_formal_report_signoff": True,
            "requires_production_retrieval_evidence": True,
        },
        "upstream": {
            "h2w11g_status": h2w11g.get("status"),
            "h2w11j_status": h2w11j.get("status"),
            "h2w11k_status": h2w11k.get("status"),
        },
        "evidence": evidence,
        "boundaries": _boundaries(),
        "next_actions": [
            "由客户或业务负责人逐条确认标准答案、禁用承诺和转人工规则。",
            "确认后再进入真实题库、线上回执和正式报告签收专项。",
        ],
    }
    _write_json(output_dir / "summary.json", result)
    _write_report(output_dir / "customer_standard_answer_confirmation_pack_review.md", result)
    return result


def main() -> int:
    result = run_h2w11l_customer_standard_answer_confirmation_pack_gate()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
