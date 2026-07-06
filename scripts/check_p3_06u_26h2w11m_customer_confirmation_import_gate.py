#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PHASE = "H2W-11M"
DEFAULT_OUTPUT_DIR = ROOT / "output/p3_06u_26h2w11m_customer_confirmation_import_gate"
H2W11L_PACK = ROOT / "evals/p3_06u_26h2w11l_customer_standard_answer_confirmation_pack.csv"
RETURN_TEMPLATE = ROOT / "evals/p3_06u_26h2w11m_customer_confirmation_return_template.csv"
DEFAULT_RETURN_FILE = ROOT / "evals/p3_06u_26h2w11m_customer_confirmation_return_received.csv"
H2W11L_SUMMARY = ROOT / "output/p3_06u_26h2w11l_customer_standard_answer_confirmation_pack/summary.json"
DOC_PATH = ROOT / "docs/P3-06U-26H2W11M_CUSTOMER_CONFIRMATION_IMPORT_GATE.md"
PRODUCT_PLAN_PATH = ROOT / "docs/PRODUCTIZATION_MASTER_PLAN_LITE_AND_STANDARD.md"
NETWORK_PLAN_PATH = ROOT / "docs/P3-06U-26H2W_NETWORKED_ENGINEERING_MASTER_PLAN.md"
README_PATH = ROOT / "README.md"

RETURN_COLUMNS = [
    "confirmation_item_id",
    "source_standard_case_id",
    "customer_question_summary",
    "business_object",
    "standard_answer_for_customer_review",
    "required_terms",
    "forbidden_terms",
    "expected_source_uri",
    "allow_auto_reply",
    "should_handoff",
    "risk_level",
    "customer_decision",
    "customer_confirmed",
    "customer_reviewer",
    "customer_reviewer_role",
    "customer_confirmed_at",
    "customer_revision_request",
    "not_formal_signoff",
]

VALID_DECISIONS = {"pending", "approved", "revise", "reject"}
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


def _write_rows(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
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


def _bool(value: str) -> bool:
    return str(value).strip().lower() == "true"


def _looks_like_iso_date(value: str) -> bool:
    value = value.strip()
    if not value:
        return False
    candidates = [value]
    if value.endswith("Z"):
        candidates.append(value[:-1] + "+00:00")
    for candidate in candidates:
        try:
            datetime.fromisoformat(candidate)
            return True
        except ValueError:
            continue
    return False


def _contains_pii(row: dict[str, str]) -> list[str]:
    scoped_fields = [
        "customer_question_summary",
        "business_object",
        "standard_answer_for_customer_review",
        "customer_reviewer",
        "customer_revision_request",
    ]
    haystack = "\n".join(str(row.get(field) or "") for field in scoped_fields)
    return [name for name, pattern in PII_PATTERNS.items() if pattern.search(haystack)]


def _is_internal_rehearsal_row(row: dict[str, str]) -> bool:
    reviewer = (row.get("customer_reviewer") or "").strip()
    role = (row.get("customer_reviewer_role") or "").strip()
    combined = f"{reviewer} {role}"
    return any(term in combined for term in ("内部演练", "内部业务模拟", "非客户签收"))


def _build_return_template_rows(pack_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for row in pack_rows:
        rows.append(
            {
                "confirmation_item_id": row.get("confirmation_item_id", ""),
                "source_standard_case_id": row.get("source_standard_case_id", ""),
                "customer_question_summary": row.get("customer_question_summary", ""),
                "business_object": row.get("business_object", ""),
                "standard_answer_for_customer_review": row.get("standard_answer_for_customer_review", ""),
                "required_terms": row.get("required_terms", ""),
                "forbidden_terms": row.get("forbidden_terms", ""),
                "expected_source_uri": row.get("expected_source_uri", ""),
                "allow_auto_reply": row.get("allow_auto_reply", "false"),
                "should_handoff": row.get("should_handoff", "false"),
                "risk_level": row.get("risk_level", ""),
                "customer_decision": "pending",
                "customer_confirmed": "false",
                "customer_reviewer": "",
                "customer_reviewer_role": "",
                "customer_confirmed_at": "",
                "customer_revision_request": "",
                "not_formal_signoff": "true",
            }
        )
    return rows


def _validate_return_rows(
    *,
    pack_rows: list[dict[str, str]],
    return_rows: list[dict[str, str]],
) -> tuple[list[str], list[str], dict[str, Any]]:
    blockers: list[str] = []
    warnings: list[str] = []
    expected_by_id = {row.get("confirmation_item_id", ""): row for row in pack_rows}
    seen_ids: set[str] = set()

    approved_rows: list[dict[str, str]] = []
    revise_rows: list[dict[str, str]] = []
    reject_rows: list[dict[str, str]] = []
    pending_rows: list[dict[str, str]] = []
    internal_rehearsal_rows: list[dict[str, str]] = []

    if len(return_rows) != len(pack_rows):
        blockers.append(
            f"return file row count {len(return_rows)} does not match confirmation pack {len(pack_rows)}"
        )

    for row in return_rows:
        missing_columns = [column for column in RETURN_COLUMNS if column not in row]
        item_id = row.get("confirmation_item_id", "")
        if missing_columns:
            blockers.append(f"{item_id or 'unknown'} missing return columns: {missing_columns}")
        if not item_id or item_id not in expected_by_id:
            blockers.append(f"unknown confirmation_item_id: {item_id or 'empty'}")
            continue
        if item_id in seen_ids:
            blockers.append(f"duplicate confirmation_item_id in return file: {item_id}")
        seen_ids.add(item_id)

        expected = expected_by_id[item_id]
        if row.get("source_standard_case_id") != expected.get("source_standard_case_id"):
            blockers.append(f"{item_id} source_standard_case_id changed")
        if row.get("standard_answer_for_customer_review") != expected.get("standard_answer_for_customer_review"):
            blockers.append(f"{item_id} standard_answer_for_customer_review changed; use revision_request instead")
        if row.get("required_terms") != expected.get("required_terms"):
            blockers.append(f"{item_id} required_terms changed; use revision_request instead")
        if row.get("forbidden_terms") != expected.get("forbidden_terms"):
            blockers.append(f"{item_id} forbidden_terms changed; use revision_request instead")
        if row.get("expected_source_uri") != expected.get("expected_source_uri"):
            blockers.append(f"{item_id} expected_source_uri changed; use revision_request instead")
        if row.get("not_formal_signoff") != "true":
            blockers.append(f"{item_id} must keep not_formal_signoff=true")

        decision = (row.get("customer_decision") or "").strip().lower()
        if decision not in VALID_DECISIONS:
            blockers.append(f"{item_id} customer_decision must be one of {sorted(VALID_DECISIONS)}")
        confirmed = _bool(row.get("customer_confirmed", ""))
        reviewer = (row.get("customer_reviewer") or "").strip()
        reviewer_role = (row.get("customer_reviewer_role") or "").strip()
        confirmed_at = (row.get("customer_confirmed_at") or "").strip()
        revision_request = (row.get("customer_revision_request") or "").strip()

        if confirmed and decision != "approved":
            blockers.append(f"{item_id} customer_confirmed=true requires customer_decision=approved")
        if decision == "approved" and not confirmed:
            blockers.append(f"{item_id} approved row must set customer_confirmed=true")
        if confirmed and (not reviewer or not reviewer_role or not _looks_like_iso_date(confirmed_at)):
            blockers.append(f"{item_id} confirmed row requires reviewer, role and ISO confirmed_at")
        if confirmed and revision_request:
            blockers.append(f"{item_id} confirmed row cannot also carry revision request")
        if decision in {"revise", "reject"} and not revision_request:
            blockers.append(f"{item_id} {decision} row requires customer_revision_request")

        pii = _contains_pii(row)
        if pii:
            blockers.append(f"{item_id} has PII-like content: {pii}")

        if decision == "approved":
            approved_rows.append(row)
        elif decision == "revise":
            revise_rows.append(row)
        elif decision == "reject":
            reject_rows.append(row)
        else:
            pending_rows.append(row)
        if _is_internal_rehearsal_row(row):
            internal_rehearsal_rows.append(row)

    missing_ids = sorted(set(expected_by_id) - seen_ids)
    if missing_ids:
        blockers.append(f"return file missing confirmation items: {missing_ids}")

    metrics = {
        "expected_item_count": len(pack_rows),
        "return_item_count": len(return_rows),
        "approved_item_count": len(approved_rows),
        "revise_item_count": len(revise_rows),
        "reject_item_count": len(reject_rows),
        "pending_item_count": len(pending_rows),
        "customer_confirmed_item_count": sum(1 for row in return_rows if _bool(row.get("customer_confirmed", ""))),
        "all_items_approved": len(approved_rows) == len(pack_rows) and bool(pack_rows),
        "internal_rehearsal_item_count": len(internal_rehearsal_rows),
        "real_customer_confirmed_item_count": sum(
            1
            for row in return_rows
            if _bool(row.get("customer_confirmed", "")) and not _is_internal_rehearsal_row(row)
        ),
    }
    if revise_rows or reject_rows:
        warnings.append("customer returned revision or reject rows; create a revised standard answer pack before signoff")
    if internal_rehearsal_rows:
        warnings.append(
            "return file contains internal rehearsal confirmations; keep formal customer signoff false"
        )
    return blockers, warnings, metrics


def _write_review(path: Path, result: dict[str, Any]) -> None:
    metrics = result.get("metrics", {})
    lines = [
        "# H2W-11M 客户标准答案确认结果导入门禁",
        "",
        "## 结论",
        "",
        f"- 门禁状态：{result['status']}",
        f"- 客户返回文件是否存在：{str(result['readiness']['customer_return_file_present']).lower()}",
        f"- 待确认条目：{metrics.get('expected_item_count', 0)}",
        f"- 已确认条目：{metrics.get('customer_confirmed_item_count', 0)}",
        f"- 内部演练确认条目：{metrics.get('internal_rehearsal_item_count', 0)}",
        f"- 全部批准：{str(metrics.get('all_items_approved', False)).lower()}",
        f"- 可导入客户确认结果：{str(result['readiness']['ready_for_confirmed_standard_answer_import']).lower()}",
        f"- 可进入正式准确率签收：{str(result['readiness']['ready_for_formal_accuracy_signoff']).lower()}",
        "",
        "## 当前真实状态",
        "",
        "- 已生成客户返回模板。",
        "- 如果没有客户真实返回文件，本阶段只表示导入门禁已准备好。",
        "- 不伪造客户确认，不预填真实客户确认人和确认时间。",
        "- 内部演练确认可以用于跑通工程链路，但不能写成真实客户签收。",
        "",
        "## 停止门禁",
        "",
        "- `customer_return_file_present=false` 时，不能写成客户已确认。",
        "- 任何条目出现 `revise` 或 `reject`，必须先修订标准答案包。",
        "- 即使全部标准答案确认，也仍不是正式客户准确率签收。",
        "- 真实外发继续关闭。",
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
        "customer_confirmation_fabricated": False,
        "internal_rehearsal_confirmation_used": False,
        "real_customer_confirmation_performed": False,
        "ready_for_formal_accuracy_signoff": False,
    }


def run_h2w11m_customer_confirmation_import_gate(
    *,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    return_template_path: Path = RETURN_TEMPLATE,
    return_file_path: Path = DEFAULT_RETURN_FILE,
) -> dict[str, Any]:
    blockers: list[str] = []
    warnings: list[str] = []
    for path in [H2W11L_PACK, H2W11L_SUMMARY, DOC_PATH, PRODUCT_PLAN_PATH, NETWORK_PLAN_PATH, README_PATH]:
        if not path.exists():
            blockers.append(f"required file missing: {_display_path(path)}")

    if blockers:
        result = {
            "phase": PHASE,
            "status": "blocked",
            "blockers": blockers,
            "warnings": warnings,
            "metrics": {},
            "readiness": {
                "customer_return_file_present": return_file_path.exists(),
                "ready_for_customer_return_collection": False,
                "ready_for_confirmed_standard_answer_import": False,
                "ready_for_formal_accuracy_signoff": False,
            },
            "boundaries": _boundaries(),
        }
        _write_json(output_dir / "summary.json", result)
        return result

    h2w11l = _read_json(H2W11L_SUMMARY)
    pack_rows = _read_rows(H2W11L_PACK)
    if h2w11l.get("status") != "passed":
        blockers.append("H2W-11L must pass before H2W-11M")
    if h2w11l.get("readiness", {}).get("ready_for_formal_accuracy_signoff") is not False:
        blockers.append("H2W-11L must keep ready_for_formal_accuracy_signoff=false")
    if any(row.get("customer_confirmed") != "false" for row in pack_rows):
        blockers.append("H2W-11L confirmation pack must keep customer_confirmed=false before return import")

    template_rows = _build_return_template_rows(pack_rows)
    _write_rows(return_template_path, RETURN_COLUMNS, template_rows)

    return_file_present = return_file_path.exists()
    imported_metrics: dict[str, Any] = {
        "expected_item_count": len(pack_rows),
        "return_item_count": 0,
        "approved_item_count": 0,
        "revise_item_count": 0,
        "reject_item_count": 0,
        "pending_item_count": len(pack_rows),
        "customer_confirmed_item_count": 0,
        "all_items_approved": False,
    }
    validated_return_path: Path | None = None

    if return_file_present:
        return_rows = _read_rows(return_file_path)
        return_blockers, return_warnings, imported_metrics = _validate_return_rows(
            pack_rows=pack_rows,
            return_rows=return_rows,
        )
        blockers.extend(return_blockers)
        warnings.extend(return_warnings)
        if not return_blockers:
            validated_return_path = output_dir / "validated_customer_confirmation_return.csv"
            _write_rows(validated_return_path, RETURN_COLUMNS, return_rows)

    ready_for_import = (
        return_file_present
        and not blockers
        and imported_metrics.get("all_items_approved") is True
    )
    internal_rehearsal_used = bool(imported_metrics.get("internal_rehearsal_item_count"))
    real_customer_confirmation_performed = bool(imported_metrics.get("real_customer_confirmed_item_count"))

    evidence: dict[str, Any] = {
        "source_confirmation_pack": {
            "path": _display_path(H2W11L_PACK),
            "sha256": _sha256_file(H2W11L_PACK),
        },
        "return_template": {
            "path": _display_path(return_template_path),
            "sha256": _sha256_file(return_template_path),
        },
    }
    if return_file_present:
        evidence["customer_return_file"] = {
            "path": _display_path(return_file_path),
            "sha256": _sha256_file(return_file_path),
        }
    if validated_return_path:
        evidence["validated_return_file"] = {
            "path": _display_path(validated_return_path),
            "sha256": _sha256_file(validated_return_path),
        }

    result = {
        "phase": PHASE,
        "status": "passed" if not blockers else "blocked",
        "blockers": blockers,
        "warnings": warnings,
        "metrics": imported_metrics,
        "readiness": {
            "customer_return_file_present": return_file_present,
            "internal_rehearsal_confirmation_used": internal_rehearsal_used,
            "real_customer_confirmation_performed": real_customer_confirmation_performed,
            "ready_for_customer_return_collection": not blockers,
            "ready_for_confirmed_standard_answer_import": ready_for_import,
            "ready_for_formal_accuracy_signoff": False,
            "requires_real_question_bank": True,
            "requires_online_receipts": True,
            "requires_formal_report_signoff": True,
            "requires_production_retrieval_evidence": True,
        },
        "evidence": evidence,
        "boundaries": _boundaries(),
        "next_actions": [
            "把返回模板交给客户或业务负责人逐条确认。",
            "收到真实返回文件后复跑本门禁。",
            "全部标准答案确认后，仍需真实题库、线上回执、正式报告签收和生产级检索证据。",
        ],
    }
    result["boundaries"]["internal_rehearsal_confirmation_used"] = internal_rehearsal_used
    result["boundaries"]["real_customer_confirmation_performed"] = real_customer_confirmation_performed
    _write_json(output_dir / "summary.json", result)
    _write_review(output_dir / "customer_confirmation_import_gate_review.md", result)
    return result


def main() -> int:
    result = run_h2w11m_customer_confirmation_import_gate()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
