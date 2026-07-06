#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = ROOT / "output/p3_06u_26h2w11k_customer_report_gap_rehearsal"
H2W11J_SUMMARY = ROOT / "output/p3_06u_26h2w11j_gap_final_answer_rehearsal/summary.json"
H2W11J_LABEL_EXPORT = ROOT / "output/p3_06u_26h2w11j_gap_final_answer_rehearsal/gap_final_answer_labels.csv"
SCHEMA_PATH = ROOT / "backend/app/schemas/knowledge.py"
SERVICE_PATH = ROOT / "backend/app/services/knowledge.py"
CLIENT_PATH = ROOT / "frontend/src/api/client.ts"
QUALITY_PANEL_PATH = ROOT / "frontend/src/components/quality/QualityReviewPanel.tsx"
STYLE_PATH = ROOT / "frontend/src/styles.css"
DOC_PATH = ROOT / "docs/P3-06U-26H2W11K_CUSTOMER_REPORT_GAP_REHEARSAL_EVIDENCE.md"
PRODUCT_PLAN_PATH = ROOT / "docs/PRODUCTIZATION_MASTER_PLAN_LITE_AND_STANDARD.md"
NETWORK_PLAN_PATH = ROOT / "docs/P3-06U-26H2W_NETWORKED_ENGINEERING_MASTER_PLAN.md"
README_PATH = ROOT / "README.md"


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def _require_tokens(path: Path, tokens: list[str], blockers: list[str]) -> None:
    if not path.exists():
        blockers.append(f"required file missing: {_display_path(path)}")
        return
    text = _read_text(path)
    for token in tokens:
        if token not in text:
            blockers.append(f"{_display_path(path)} missing token: {token}")


def run_h2w11k_customer_report_gap_rehearsal_gate(
    *, output_dir: Path = DEFAULT_OUTPUT_DIR
) -> dict[str, Any]:
    blockers: list[str] = []
    warnings: list[str] = []

    for path in [
        H2W11J_SUMMARY,
        H2W11J_LABEL_EXPORT,
        SCHEMA_PATH,
        SERVICE_PATH,
        CLIENT_PATH,
        QUALITY_PANEL_PATH,
        STYLE_PATH,
        DOC_PATH,
        PRODUCT_PLAN_PATH,
        NETWORK_PLAN_PATH,
        README_PATH,
    ]:
        if not path.exists():
            blockers.append(f"required file missing: {_display_path(path)}")

    upstream: dict[str, Any] = {}
    metrics: dict[str, Any] = {}
    boundaries: dict[str, Any] = {}
    if H2W11J_SUMMARY.exists():
        upstream = _read_json(H2W11J_SUMMARY)
        metrics = upstream.get("metrics") if isinstance(upstream.get("metrics"), dict) else {}
        boundaries = upstream.get("boundaries") if isinstance(upstream.get("boundaries"), dict) else {}
        if upstream.get("phase") != "H2W-11J":
            blockers.append("H2W-11J summary phase mismatch")
        if upstream.get("status") != "passed":
            blockers.append("H2W-11J summary must be passed before H2W-11K")
        if int(metrics.get("case_count") or 0) < 7:
            blockers.append("H2W-11J summary must include at least 7 gap cases")
        if metrics.get("ready_for_gap_quality_report_review") is not True:
            blockers.append("H2W-11J must be ready for gap quality report review")
        if metrics.get("ready_for_formal_accuracy_signoff") is not False:
            blockers.append("H2W-11J must keep formal accuracy signoff false")
        for key in [
            "provider_call_performed",
            "real_platform_send_performed",
            "external_platform_write_performed",
            "final_answer_text_exported",
        ]:
            if boundaries.get(key) is not False:
                blockers.append(f"H2W-11J boundary must remain false: {key}")

    if H2W11J_LABEL_EXPORT.exists():
        rows = _read_rows(H2W11J_LABEL_EXPORT)
        if not rows:
            blockers.append("H2W-11J label export is empty")
        if any((row.get("final_answer_text") or "").strip() for row in rows):
            blockers.append("H2W-11J label export must not include final_answer_text")
        if any(row.get("customer_confirmed") != "false" for row in rows):
            blockers.append("H2W-11J label export must keep customer_confirmed=false")

    _require_tokens(
        SCHEMA_PATH,
        [
            "CustomerQualityReportGapRehearsalEvidenceRead",
            "gap_rehearsal_evidence",
            "ready_for_formal_accuracy_signoff",
            "final_answer_text_exported",
        ],
        blockers,
    )
    _require_tokens(
        SERVICE_PATH,
        [
            "H2W11J_GAP_REHEARSAL_SUMMARY_PATH",
            "_load_h2w11j_gap_rehearsal_evidence",
            "gap_rehearsal_evidence",
            "缺口样本演练证据",
            "ready_for_formal_accuracy_signoff=false",
            "不真实外发",
        ],
        blockers,
    )
    _require_tokens(
        CLIENT_PATH,
        [
            "CustomerQualityReportGapRehearsalEvidence",
            "gap_rehearsal_evidence",
            "ready_for_formal_accuracy_signoff",
        ],
        blockers,
    )
    _require_tokens(
        QUALITY_PANEL_PATH,
        [
            "gapRehearsalEvidence",
            "data-h2w11k-gap-rehearsal-evidence",
            "缺口样本本地演练证据",
            "不是正式准确率签收",
            "不导出完整最终答案正文",
        ],
        blockers,
    )
    _require_tokens(
        STYLE_PATH,
        [
            ".customer-report-gap-evidence",
            ".customer-report-gap-evidence-grid",
        ],
        blockers,
    )
    _require_tokens(
        DOC_PATH,
        [
            "# H2W-11K 客户质量报告缺口演练证据汇入",
            "不是正式客户准确率签收",
            "真实外发继续关闭",
            "客户确认标准答案",
        ],
        blockers,
    )
    for path in [PRODUCT_PLAN_PATH, NETWORK_PLAN_PATH, README_PATH]:
        _require_tokens(
            path,
            [
                "H2W-11K",
                "缺口演练",
                "不是正式客户准确率签收",
            ],
            blockers,
        )

    result = {
        "phase": "H2W-11K",
        "status": "passed" if not blockers else "blocked",
        "blockers": blockers,
        "warnings": warnings,
        "metrics": {
            "upstream_case_count": int(metrics.get("case_count") or 0),
            "upstream_auto_reply_label_count": int(metrics.get("auto_reply_label_count") or 0),
            "upstream_handoff_not_applicable_count": int(metrics.get("handoff_not_applicable_count") or 0),
            "ready_for_gap_quality_report_review": metrics.get("ready_for_gap_quality_report_review") is True,
            "ready_for_formal_accuracy_signoff": False,
        },
        "boundaries": {
            "customer_report_gap_rehearsal_evidence_added": not blockers,
            "formal_customer_signoff_performed": False,
            "real_platform_send_performed": False,
            "provider_call_performed": False,
            "final_answer_text_exported": False,
        },
        "next_actions": [
            "继续补真实客户确认标准答案、真实题库、线上回执和正式报告签收。",
            "不要把 H2W-11K 本地演练证据写成正式准确率签收。",
        ],
    }
    _write_json(output_dir / "summary.json", result)
    return result


def main() -> int:
    result = run_h2w11k_customer_report_gap_rehearsal_gate()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
