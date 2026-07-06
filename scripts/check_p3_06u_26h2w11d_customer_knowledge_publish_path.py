#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = ROOT / "output/p3_06u_26h2w11d_customer_knowledge_publish_path"
APP_PATH = ROOT / "frontend/src/App.tsx"
STYLE_PATH = ROOT / "frontend/src/styles.css"
DOC_PATH = ROOT / "docs/P3-06U-26H2W11D_CUSTOMER_KNOWLEDGE_PUBLISH_PATH.md"
H2W11B_PACKAGE_PATH = ROOT / "evals/p3_06u_26h2w11b_repaired_customer_knowledge_package.json"
H2W11B_SUMMARY_PATH = ROOT / "output/p3_06u_26h2w11b_quality_repair/summary.json"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(_read(path))


def _require_contains(name: str, content: str, needles: list[str]) -> list[str]:
    return [f"{name} missing {needle!r}" for needle in needles if needle not in content]


def _extract_customer_publish_section(app: str) -> str:
    marker = 'data-h2w11d-customer-publish-path="true"'
    start = app.find(marker)
    if start < 0:
        return ""
    end = app.find("</section>", start)
    if end < 0:
        return app[start:]
    return app[start : end + len("</section>")]


def run_h2w11d_customer_knowledge_publish_path_static_gate(
    *,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
) -> dict[str, Any]:
    blockers: list[str] = []
    warnings: list[str] = []

    for path in [APP_PATH, STYLE_PATH, DOC_PATH, H2W11B_PACKAGE_PATH, H2W11B_SUMMARY_PATH]:
        if not path.exists():
            blockers.append(f"required file missing: {path.relative_to(ROOT)}")

    if blockers:
        result = {
            "phase": "H2W-11D",
            "status": "blocked",
            "blockers": blockers,
            "warnings": warnings,
            "boundaries": _boundaries(),
        }
        _write_summary(output_dir, result)
        return result

    app = _read(APP_PATH)
    styles = _read(STYLE_PATH)
    doc = _read(DOC_PATH)
    h2w11b_summary = _load_json(H2W11B_SUMMARY_PATH)
    h2w11b_package = _load_json(H2W11B_PACKAGE_PATH)
    release_section = _extract_customer_publish_section(app)

    blockers.extend(
        _require_contains(
            "frontend/src/App.tsx",
            app,
            [
                'data-h2w11d-customer-publish-path="true"',
                'data-h2w11d-action="convert-customer-intake"',
                'data-h2w11d-action="preview-update-package"',
                'data-h2w11d-action="import-update-package"',
                'data-h2w11d-action="publish-precheck-first-ready-document"',
                'data-h2w11d-action="publish-first-ready-document"',
                'data-h2w11d-action="open-evaluation-page"',
                'data-h2w11d-action="open-quality-report-page"',
                "customerQualityReport={customerQualityReport}",
                "customerQualityReportSignoffs={customerQualityReportSignoffs}",
                "evaluationState={knowledgeEvaluation}",
                "onPreviewUpdatePackage",
                "onImportUpdatePackage",
                "onCheckPublishDocument(firstReadyDocument)",
                "onPublishDocument(firstReadyDocument)",
                "导入资料 → 预检 → 发布 → 复测 → 确认 → 质量报告",
                "真实外发继续关闭",
            ],
        )
    )
    blockers.extend(
        _require_contains(
            "frontend/src/styles.css",
            styles,
            [
                ".customer-knowledge-release-card",
                ".customer-knowledge-release-head",
                ".customer-knowledge-release-steps",
                ".customer-knowledge-release-actions",
                ".release-step-ready",
                ".release-step-warning",
            ],
        )
    )
    blockers.extend(
        _require_contains(
            "H2W-11D section",
            release_section,
            [
                "知识维护总流程",
                "生成资料包",
                "检查资料包",
                "导入知识库",
                "启用前复测",
                "启用知识",
                "查看复测题库",
                "查看质量报告",
                "客户确认记录不是正式验收",
            ],
        )
    )
    blockers.extend(
        _require_contains(
            "docs/P3-06U-26H2W11D_CUSTOMER_KNOWLEDGE_PUBLISH_PATH.md",
            doc,
            [
                "# H2W-11D 客户知识发布闭环前端路径",
                "导入 -> 预检 -> 发布 -> 回归评测 -> 报告 -> 签收",
                "不是正式客户签收完成",
                "真实外发继续关闭",
                "H2W-11B",
            ],
        )
    )

    section_overclaims = [
        "已真实外发",
        "全平台已接通",
        "正式电子签章已完成",
        "合同签收已完成",
        "RPA 自动发送",
        "Hook",
        "Cookie 接管",
    ]
    found_overclaims = [needle for needle in section_overclaims if needle in release_section]
    if found_overclaims:
        blockers.append(f"H2W-11D section contains overclaiming copy: {found_overclaims}")

    quality_repair_status = h2w11b_summary.get("status")
    if quality_repair_status != "completed":
        blockers.append(f"H2W-11B summary status is {quality_repair_status!r}, expected 'completed'")
    if h2w11b_summary.get("blockers") != []:
        blockers.append("H2W-11B summary still has blockers")

    repaired_rehearsal = h2w11b_summary.get("repaired_rehearsal", {})
    report_bundle = repaired_rehearsal.get("customer_quality_report", {})
    report = report_bundle.get("report", {}) if isinstance(report_bundle, dict) else {}
    if report.get("report_status") != "controlled_trial_ready":
        blockers.append("H2W-11B repaired quality report is not controlled_trial_ready")
    if report.get("report_confidence_score") != 90:
        blockers.append("H2W-11B repaired quality report confidence score is not 90")

    alignment = h2w11b_summary.get("knowledge_alignment", {})
    if alignment.get("case_card_count") != 62:
        blockers.append("H2W-11B repaired package does not expose 62 case coverage cards")
    if alignment.get("expected_term_document_coverage_after") != 1.0:
        blockers.append("H2W-11B repaired package expected-term coverage is not 1.0")

    documents = h2w11b_package.get("documents") or h2w11b_package.get("knowledge_documents") or []
    if len(documents) < 7:
        blockers.append("H2W-11B repaired package should keep at least 7 source documents")
    serialized_package = json.dumps(h2w11b_package, ensure_ascii=False)
    if "题库覆盖卡" not in serialized_package:
        blockers.append("H2W-11B repaired package does not include case coverage cards")

    if "当前知识评测仍不是完整线上客服准确率" not in doc:
        warnings.append("doc should keep the knowledge-evaluation boundary highly visible")
    legacy_customer_terms = [
        "客户知识发布闭环",
        "预检更新包",
        "转换客户资料",
        "发布前试跑",
        "确认发布",
        "进入知识评测",
        "本地签收记录不是正式电子签章",
    ]
    leaked_legacy_terms = [term for term in legacy_customer_terms if term in release_section]
    if leaked_legacy_terms:
        blockers.append(f"H2W-11D customer section still contains legacy/internal terms: {leaked_legacy_terms}")

    status = "passed" if not blockers else "blocked"
    result = {
        "phase": "H2W-11D",
        "status": status,
        "blockers": blockers,
        "warnings": warnings,
        "frontend": {
            "customer_publish_path_marker": 'data-h2w11d-customer-publish-path="true"' in app,
            "action_count": release_section.count("data-h2w11d-action="),
            "uses_quality_report_state": "customerQualityReport={customerQualityReport}" in app,
            "uses_signoff_state": "customerQualityReportSignoffs={customerQualityReportSignoffs}" in app,
            "uses_evaluation_state": "evaluationState={knowledgeEvaluation}" in app,
        },
        "h2w11b": {
            "summary_status": quality_repair_status,
            "report_status": report.get("report_status"),
            "report_confidence_score": report.get("report_confidence_score"),
            "case_card_count": alignment.get("case_card_count"),
            "expected_term_document_coverage_after": alignment.get("expected_term_document_coverage_after"),
            "document_count": len(documents),
        },
        "boundaries": _boundaries(),
    }
    _write_summary(output_dir, result)
    return result


def _boundaries() -> dict[str, bool]:
    return {
        "provider_call_performed": False,
        "external_platform_write_performed": False,
        "real_platform_send_performed": False,
        "formal_customer_signoff_performed": False,
        "electronic_signature_performed": False,
        "real_customer_data_used": False,
    }


def _write_summary(output_dir: Path, result: dict[str, Any]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "summary.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    result = run_h2w11d_customer_knowledge_publish_path_static_gate()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result["blockers"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
