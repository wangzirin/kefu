#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TEMPLATE = ROOT / "evals/p3_06u_26h2w11g_customer_standard_answer_template.csv"
DEFAULT_OUTPUT_DIR = ROOT / "output/p3_06u_26h2w11g_customer_standard_answer_readiness"
H2W11B_SUMMARY = ROOT / "output/p3_06u_26h2w11b_quality_repair/summary.json"
H2W11F_SUMMARY = ROOT / "output/p3_06u_26h2w11f_customer_terms_and_path_consolidation/summary.json"
H2W11B_PACKAGE = ROOT / "evals/p3_06u_26h2w11b_repaired_customer_knowledge_package.json"
DOC_PATH = ROOT / "docs/P3-06U-26H2W11G_CUSTOMER_STANDARD_ANSWER_READINESS.md"
PRODUCT_PLAN_PATH = ROOT / "docs/PRODUCTIZATION_MASTER_PLAN_LITE_AND_STANDARD.md"
NETWORK_PLAN_PATH = ROOT / "docs/P3-06U-26H2W_NETWORKED_ENGINEERING_MASTER_PLAN.md"
README_PATH = ROOT / "README.md"

REQUIRED_COLUMNS = [
    "case_id",
    "source_channel",
    "customer_scenario",
    "customer_question_summary",
    "business_object",
    "standard_answer",
    "required_terms",
    "forbidden_terms",
    "expected_source_uri",
    "expected_document_title",
    "allow_auto_reply",
    "should_handoff",
    "handoff_reason",
    "risk_level",
    "required_citation",
    "answer_owner",
    "last_reviewed_at",
    "sample_origin",
    "customer_confirmed",
    "annotation_notes",
]

OVERCLAIMS = [
    "真实外发已开启",
    "已接通全渠道",
    "正式签收已完成",
    "生产上线已完成",
    "正式电子签章已完成",
    "合同签收已完成",
    "完整线上准确率已完成",
]
PII_PATTERNS = {
    "phone": re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)"),
    "email": re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
    "id_card": re.compile(r"(?<!\d)\d{17}[\dXx](?!\d)"),
}


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _read_rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), [dict(row) for row in reader]


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


def _bool(value: str) -> bool:
    return str(value).strip().lower() == "true"


def _check_pii(row: dict[str, str]) -> list[str]:
    findings: list[str] = []
    scoped_fields = [
        "customer_question_summary",
        "business_object",
        "standard_answer",
        "annotation_notes",
    ]
    haystack = "\n".join(str(row.get(field) or "") for field in scoped_fields)
    for name, pattern in PII_PATTERNS.items():
        if pattern.search(haystack):
            findings.append(name)
    return findings


def _validate_rows(rows: list[dict[str, str]]) -> tuple[list[str], dict[str, Any]]:
    blockers: list[str] = []
    source_counter: dict[str, int] = {}
    handoff_count = 0
    auto_reply_count = 0
    risk_counter: dict[str, int] = {}

    seen_case_ids: set[str] = set()
    for index, row in enumerate(rows, start=2):
        if None in row:
            blockers.append(f"row {index} has extra CSV cells beyond declared columns: {row[None]}")

        case_id = str(row.get("case_id") or "").strip()
        if not case_id:
            blockers.append(f"row {index} missing case_id")
        elif case_id in seen_case_ids:
            blockers.append(f"duplicate case_id: {case_id}")
        seen_case_ids.add(case_id)

        required_missing = [column for column in REQUIRED_COLUMNS if column not in row]
        if required_missing:
            blockers.append(f"row {index} missing columns: {required_missing}")
            continue

        standard_answer = str(row.get("standard_answer") or "").strip()
        required_terms = _split_terms(str(row.get("required_terms") or ""))
        forbidden_terms = _split_terms(str(row.get("forbidden_terms") or ""))
        source_uri = str(row.get("expected_source_uri") or "").strip()
        should_handoff = _bool(str(row.get("should_handoff") or ""))
        allow_auto_reply = _bool(str(row.get("allow_auto_reply") or ""))
        required_citation = _bool(str(row.get("required_citation") or ""))
        customer_confirmed = _bool(str(row.get("customer_confirmed") or ""))
        sample_origin = str(row.get("sample_origin") or "").strip()
        risk_level = str(row.get("risk_level") or "").strip()

        source_counter[source_uri or "missing"] = source_counter.get(source_uri or "missing", 0) + 1
        risk_counter[risk_level or "missing"] = risk_counter.get(risk_level or "missing", 0) + 1
        handoff_count += int(should_handoff)
        auto_reply_count += int(allow_auto_reply)

        if len(standard_answer) < 18:
            blockers.append(f"{case_id} standard_answer too short")
        if not required_terms:
            blockers.append(f"{case_id} required_terms empty")
        if required_citation and not source_uri:
            blockers.append(f"{case_id} required_citation=true but expected_source_uri empty")
        if should_handoff and allow_auto_reply:
            blockers.append(f"{case_id} cannot be both allow_auto_reply=true and should_handoff=true")
        if should_handoff and not str(row.get("handoff_reason") or "").strip():
            blockers.append(f"{case_id} should_handoff=true but handoff_reason empty")
        if sample_origin not in {"synthetic_template", "deidentified_template"}:
            blockers.append(f"{case_id} sample_origin must stay template/deidentified, got {sample_origin!r}")
        if customer_confirmed:
            blockers.append(f"{case_id} customer_confirmed must remain false before real customer confirmation")
        for term in forbidden_terms:
            if term and term in standard_answer:
                blockers.append(f"{case_id} standard_answer repeats forbidden term {term!r}")
        overclaims = [term for term in OVERCLAIMS if term in standard_answer]
        if overclaims:
            blockers.append(f"{case_id} standard_answer contains overclaiming copy: {overclaims}")
        pii_findings = _check_pii(row)
        if pii_findings:
            blockers.append(f"{case_id} may contain PII-like values: {pii_findings}")

    metrics = {
        "row_count": len(rows),
        "source_count": len([key for key in source_counter if key != "missing"]),
        "source_counter": source_counter,
        "handoff_count": handoff_count,
        "auto_reply_count": auto_reply_count,
        "risk_counter": risk_counter,
    }
    return blockers, metrics


def _boundaries() -> dict[str, bool]:
    return {
        "provider_call_performed": False,
        "external_platform_write_performed": False,
        "real_platform_send_performed": False,
        "formal_customer_signoff_performed": False,
        "electronic_signature_performed": False,
        "real_customer_data_used": False,
        "ready_for_formal_accuracy_signoff": False,
    }


def _write_summary(output_dir: Path, result: dict[str, Any]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "summary.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")


def run_h2w11g_customer_standard_answer_readiness_gate(
    *,
    template_path: Path = DEFAULT_TEMPLATE,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
) -> dict[str, Any]:
    blockers: list[str] = []
    warnings: list[str] = []

    required_files = [
        template_path,
        H2W11B_SUMMARY,
        H2W11F_SUMMARY,
        H2W11B_PACKAGE,
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
            "phase": "H2W-11G",
            "status": "blocked",
            "blockers": blockers,
            "warnings": warnings,
            "boundaries": _boundaries(),
        }
        _write_summary(output_dir, result)
        return result

    h2w11b = _read_json(H2W11B_SUMMARY)
    h2w11f = _read_json(H2W11F_SUMMARY)
    columns, rows = _read_rows(template_path)
    doc = _read_text(DOC_PATH)
    product_plan = _read_text(PRODUCT_PLAN_PATH)
    network_plan = _read_text(NETWORK_PLAN_PATH)
    readme = _read_text(README_PATH)

    missing_columns = [column for column in REQUIRED_COLUMNS if column not in columns]
    extra_required_order_issues = columns[: len(REQUIRED_COLUMNS)] != REQUIRED_COLUMNS
    if missing_columns:
        blockers.append(f"standard answer template missing columns: {missing_columns}")
    if extra_required_order_issues:
        blockers.append("standard answer template column order should start with REQUIRED_COLUMNS")
    if len(rows) < 10:
        blockers.append("standard answer template needs at least 10 controlled sample rows")

    row_blockers, metrics = _validate_rows(rows)
    blockers.extend(row_blockers)

    if h2w11f.get("status") != "passed":
        blockers.append("H2W-11F must pass before H2W-11G")
    if h2w11b.get("status") != "completed":
        blockers.append("H2W-11B quality repair must be completed before H2W-11G")
    repaired = h2w11b.get("repaired_metrics") or {}
    alignment = h2w11b.get("knowledge_alignment") or {}
    if repaired.get("report_status") != "controlled_trial_ready":
        blockers.append("H2W-11B report_status must be controlled_trial_ready")
    if repaired.get("final_answer_factuality_rate") != 1.0:
        blockers.append("H2W-11B repaired final_answer_factuality_rate must be 1.0")
    if alignment.get("case_card_count", 0) < 50:
        blockers.append("H2W-11B should keep 50-100 controlled rehearsal cases")

    required_doc_terms = [
        "# H2W-11G 客户标准答案口径准备",
        "不是正式客户准确率签收",
        "客户标准答案口径",
        "最终客服答案质量",
        "真实外发继续关闭",
        "真实客户原始数据仍未使用",
        "停止门禁",
    ]
    for term in required_doc_terms:
        if term not in doc:
            blockers.append(f"H2W-11G doc missing {term!r}")
    for name, content in [
        ("README.md", readme),
        ("PRODUCTIZATION_MASTER_PLAN_LITE_AND_STANDARD.md", product_plan),
        ("P3-06U-26H2W_NETWORKED_ENGINEERING_MASTER_PLAN.md", network_plan),
    ]:
        if "H2W-11G" not in content or "客户标准答案" not in content:
            blockers.append(f"{name} missing H2W-11G customer standard answer record")

    result = {
        "phase": "H2W-11G",
        "status": "passed" if not blockers else "blocked",
        "blockers": blockers,
        "warnings": warnings,
        "template": {
            "path": str(template_path.relative_to(ROOT)),
            "columns": columns,
            "required_columns": REQUIRED_COLUMNS,
            "sha256": __import__("hashlib").sha256(template_path.read_bytes()).hexdigest(),
        },
        "metrics": metrics,
        "upstream": {
            "h2w11f_status": h2w11f.get("status"),
            "h2w11b_status": h2w11b.get("status"),
            "h2w11b_report_status": repaired.get("report_status"),
            "h2w11b_report_confidence_score": repaired.get("report_confidence_score"),
            "h2w11b_case_card_count": alignment.get("case_card_count"),
        },
        "readiness": {
            "ready_for_customer_standard_answer_collection": not blockers,
            "ready_for_formal_accuracy_signoff": False,
            "raw_question_text_required": False,
            "real_customer_confirmation_required_next": True,
        },
        "boundaries": _boundaries(),
    }
    _write_summary(output_dir, result)
    return result


def main() -> None:
    result = run_h2w11g_customer_standard_answer_readiness_gate()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result["blockers"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
