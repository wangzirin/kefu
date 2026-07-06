#!/usr/bin/env python3

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from import_customer_service_eval_bank import run_customer_service_eval_bank_import  # noqa: E402


BANK_PATH = ROOT / "evals/p3_01_realistic_customer_service_eval_bank_62_2026-06-27.csv"
KNOWLEDGE_PACKAGE_PATH = ROOT / "evals/p3_06u_26f_real_customer_knowledge_package_template.json"
OUTPUT_DIR = ROOT / "output/p3_06u_26h2w11_rehearsal_preflight"
SUMMARY_PATH = OUTPUT_DIR / "summary.json"

REQUIRED_CAPABILITY_FILES = {
    "question_bank_import_ui": ROOT / "scripts/check_p3_06u_26h2o_customer_question_bank_import_ui.mjs",
    "quality_report_ui": ROOT / "scripts/check_p3_06u_26h2q_customer_quality_report_ui.mjs",
    "report_signoff_ui": ROOT / "scripts/check_p3_06u_26h2t_customer_report_signoff_ui.mjs",
    "report_signoff_list_ui": ROOT / "scripts/check_p3_06u_26h2u_customer_report_signoff_list_ui.mjs",
    "local_maintenance_ui": ROOT / "scripts/check_p3_06u_26h2w8b_local_maintenance_ui.mjs",
    "local_maintenance_readiness": ROOT / "scripts/check_p3_06u_26h2w8b_local_maintenance_readiness.py",
    "knowledge_package_api_test": ROOT / "backend/tests/test_knowledge_update_packages_api.py",
    "quality_report_export_script": ROOT / "scripts/export_customer_service_eval_report.py",
}

H2W8B_EVIDENCE_FILES = {
    "summary": ROOT / "output/p3_06u_26h2w8b_local_maintenance_ui/summary.json",
    "screenshot": ROOT / "output/p3_06u_26h2w8b_local_maintenance_ui/desktop-1440-local-maintenance-ready.png",
}


def _load_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return [dict(row) for row in csv.DictReader(file)]


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _count_by(rows: list[dict[str, str]], field: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        key = (row.get(field) or "unspecified").strip() or "unspecified"
        counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items()))


def _load_h2w8b_summary(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = _load_json(path)
    return data if isinstance(data, dict) else {}


def _build_summary() -> dict[str, Any]:
    bank_result = run_customer_service_eval_bank_import(
        input_path=BANK_PATH,
        name="H2W-11 前置演练客户式题库 62 题",
        description="用于 H2W-11 前置 rehearsal 的脱敏客户式题库；不是正式客户原始数据。",
        create=False,
    )
    bank_rows = _load_csv_rows(BANK_PATH)
    package = _load_json(KNOWLEDGE_PACKAGE_PATH)
    package_docs = package.get("documents") if isinstance(package.get("documents"), list) else []
    package_source_uris = {
        str(item.get("source_uri") or "").strip()
        for item in package_docs
        if str(item.get("source_uri") or "").strip()
    }
    bank_source_uris = {
        str(row.get("expected_source_uri") or row.get("source_reference") or "").strip()
        for row in bank_rows
        if str(row.get("expected_source_uri") or row.get("source_reference") or "").strip()
    }
    missing_source_uris = sorted(bank_source_uris - package_source_uris)
    capability_files = {name: path.exists() for name, path in REQUIRED_CAPABILITY_FILES.items()}
    h2w8b_evidence = {name: path.exists() for name, path in H2W8B_EVIDENCE_FILES.items()}
    h2w8b_summary = _load_h2w8b_summary(H2W8B_EVIDENCE_FILES["summary"])
    h2w8b_api_readiness = (
        h2w8b_summary.get("api_readiness") if isinstance(h2w8b_summary.get("api_readiness"), dict) else {}
    )
    h2w8b_boundaries = (
        h2w8b_summary.get("boundaries") if isinstance(h2w8b_summary.get("boundaries"), dict) else {}
    )

    bank_summary = bank_result.get("summary") or {}
    privacy_boundary = package.get("privacy_boundary") if isinstance(package.get("privacy_boundary"), dict) else {}
    checks = {
        "question_bank_validated": bank_result.get("status") == "validated",
        "question_bank_50_to_100_cases": 50 <= int(bank_summary.get("total_cases") or 0) <= 100,
        "question_bank_no_sensitive_rows": int(bank_summary.get("sensitive_row_count") or 0) == 0,
        "question_bank_customer_service_mode": (bank_result.get("payload") or {}).get("evaluation_mode") == "customer_service_retrieval",
        "knowledge_package_template_exists": KNOWLEDGE_PACKAGE_PATH.exists(),
        "knowledge_package_has_minimum_documents": len(package_docs) >= 7,
        "knowledge_package_covers_question_sources": not missing_source_uris,
        "knowledge_package_privacy_flags_closed": privacy_boundary.get("external_write_performed") is False
        and privacy_boundary.get("provider_call_performed") is False
        and privacy_boundary.get("requires_desensitization") is True,
        "capability_files_present": all(capability_files.values()),
        "h2w8b_evidence_present": all(h2w8b_evidence.values()),
        "h2w8b_evidence_ready": h2w8b_api_readiness.get("ready_for_customer_maintenance_rehearsal") is True
        and h2w8b_api_readiness.get("maturity_status") == "ready_for_rehearsal"
        and h2w8b_api_readiness.get("blocker_count") == 0
        and h2w8b_boundaries.get("real_platform_send_performed") is False,
    }
    blockers = [name for name, passed in checks.items() if not passed]
    warnings: list[str] = []
    if int(bank_summary.get("expected_answer_rows") or 0) == 0:
        warnings.append("当前 62 题客户式题库没有 expected_answer 字段；正式签收前仍需补最终答案样本或客户确认口径。")
    if bank_result.get("external_write_performed") is not False:
        warnings.append("题库校验脚本的外部写入标记异常，应保持 false。")

    return {
        "schema_version": "p3-06u-26h2w11.rehearsal_preflight.v1",
        "status": "ready_for_h2w11_preflight_rehearsal" if not blockers else "blocked",
        "ready": not blockers,
        "checks": checks,
        "blockers": blockers,
        "warnings": warnings,
        "question_bank": {
            "path": str(BANK_PATH),
            "total_cases": bank_summary.get("total_cases"),
            "source_channel_counts": _count_by(bank_rows, "source_channel"),
            "source_category_counts": _count_by(bank_rows, "source_category"),
            "risk_level_counts": bank_summary.get("risk_level_counts"),
            "human_review_expected_cases": bank_summary.get("human_review_expected_cases"),
            "auto_reply_blocked_cases": bank_summary.get("auto_reply_blocked_cases"),
            "sensitive_row_count": bank_summary.get("sensitive_row_count"),
            "raw_question_text_in_summary": bank_summary.get("raw_question_text_in_summary"),
            "provider_call_performed": bank_result.get("provider_call_performed"),
            "external_write_performed": bank_result.get("external_write_performed"),
        },
        "knowledge_package": {
            "path": str(KNOWLEDGE_PACKAGE_PATH),
            "template_version": package.get("template_version"),
            "document_count": len(package_docs),
            "covered_source_uri_count": len(bank_source_uris & package_source_uris),
            "missing_source_uris": missing_source_uris,
            "privacy_boundary": privacy_boundary,
        },
        "capability_files": {name: str(path) for name, path in REQUIRED_CAPABILITY_FILES.items()},
        "capability_files_present": capability_files,
        "h2w8b_evidence": {name: str(path) for name, path in H2W8B_EVIDENCE_FILES.items()},
        "h2w8b_evidence_present": h2w8b_evidence,
        "h2w8b_summary": {
            "ready": h2w8b_api_readiness.get("ready_for_customer_maintenance_rehearsal"),
            "maturity_status": h2w8b_api_readiness.get("maturity_status"),
            "blocker_count": h2w8b_api_readiness.get("blocker_count"),
            "real_platform_send_performed": h2w8b_boundaries.get("real_platform_send_performed"),
        },
        "boundaries": {
            "real_customer_data_used": False,
            "provider_call_performed": False,
            "external_platform_write_performed": False,
            "formal_customer_signoff_performed": False,
            "production_rag_completed": False,
        },
        "next_actions": [
            "用当前 62 题客户式题库跑一次负责人真实登录 rehearsal。",
            "为演练运行采集最终客服答案样本，并补人工事实性、引用充分性、禁用承诺和转人工正确性标签。",
            "导出客户可读质量报告，走本地签收记录；仍不冒充电子签章或合同签收。",
            "把本地维护总账作为 rehearsal 的运维证据，不触发真实上传、远控、静默更新或真实程序替换。",
        ],
    }


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    summary = _build_summary()
    SUMMARY_PATH.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if summary["ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
