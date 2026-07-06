#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def require_contains(path: str, needles: list[str]) -> None:
    content = read(path)
    missing = [needle for needle in needles if needle not in content]
    if missing:
        raise AssertionError(f"{path} missing required markers: {missing}")


def require_absent(path: str, needles: list[str]) -> None:
    content = read(path)
    found = [needle for needle in needles if needle in content]
    if found:
        raise AssertionError(f"{path} contains overclaiming markers: {found}")


def main() -> None:
    require_contains(
        "backend/app/schemas/knowledge.py",
        [
            "CustomerQualityReportArchiveItemRead",
            "CustomerQualityReportArchiveListRead",
            "body_encoding: str",
            "body_sha256: str",
            "body_bytes: int",
            "archive_audit_event_id",
            "electronic_signature_performed",
            "formal_contract_signoff_performed",
        ],
    )
    require_contains(
        "backend/app/services/knowledge.py",
        [
            "zipfile",
            "base64",
            "_render_customer_quality_report_xlsx",
            "_render_customer_quality_report_docx",
            "_customer_quality_report_export_body",
            "CUSTOMER_QUALITY_REPORT_ARCHIVE_LIST_SCHEMA_VERSION",
            "list_customer_quality_report_archives",
            "download_customer_quality_report_archive",
            '"body_archived": True',
            '"formal_contract_signoff_performed": False',
            "不是正式电子签章",
        ],
    )
    require_contains(
        "backend/app/api/knowledge.py",
        [
            'pattern="^(html|xlsx|docx)$"',
            "/tenants/{tenant_id}/customer-quality-report/archives",
            "/tenants/{tenant_id}/customer-quality-report/archives/{archive_event_id}/download",
            "QUALITY_READ_PERMISSION",
        ],
    )
    require_contains(
        "backend/tests/test_knowledge_evaluations_api.py",
        [
            "format=xlsx",
            "format=docx",
            "zipfile.ZipFile",
            "customer-quality-report/archives",
            "download",
            "formal_contract_signoff_performed",
            "不包含原始客户问题",
        ],
    )
    require_contains(
        "frontend/src/api/client.ts",
        [
            "CustomerQualityReportArchiveItem",
            "CustomerQualityReportArchiveList",
            "listCustomerQualityReportArchives",
            "downloadCustomerQualityReportArchive",
            'format?: "html" | "xlsx" | "docx"',
            "body_encoding",
            "body_sha256",
            "archive_audit_event_id",
        ],
    )
    require_contains(
        "frontend/src/App.tsx",
        [
            "CustomerQualityReportArchiveState",
            "refreshCustomerQualityReportArchives",
            "handleDownloadCustomerQualityReportArchive",
            "downloadCustomerQualityReportFile",
            "decodeBase64ToBytes",
            "downloadCustomerQualityReportArchive",
            "不是正式电子签章",
            "p3-06u-26h2w4.customer_quality_report_archive_list.v1",
        ],
    )
    require_contains(
        "frontend/src/components/quality/QualityReviewPanel.tsx",
        [
            'data-h2w4-report-export="p3-06u-26h2w4"',
            'data-h2w4-report-archives="p3-06u-26h2w4"',
            "HTML 留档",
            "XLSX 明细",
            "DOCX 报告",
            "报告归档",
            "不是正式电子签章",
            "不可下载",
        ],
    )
    require_contains(
        "frontend/src/styles.css",
        [
            ".customer-report-export-buttons",
            ".customer-report-archive-list",
            ".customer-report-archive-items",
        ],
    )
    require_contains(
        "docs/P3-06U-26H2W4_REPORT_EXPORTS_AND_ARCHIVE_FIRST_SLICE.md",
        [
            "# P3-06U-26H2W4 报告导出与归档第一片",
            "HTML",
            "XLSX",
            "DOCX",
            "不是正式电子签章",
            "真实外发继续关闭",
            "停止门禁",
        ],
    )
    require_contains(
        "docs/FRONTEND_FUNCTION_REALITY_MATRIX.md",
        [
            "P3-06U-26H2W4",
            "报告归档",
            "XLSX 明细",
            "DOCX 报告",
            "不是正式电子签章",
        ],
    )
    require_absent(
        "docs/P3-06U-26H2W4_REPORT_EXPORTS_AND_ARCHIVE_FIRST_SLICE.md",
        [
            "已完成正式电子签章",
            "具备法律签章效力",
            "全平台准确率已签收",
        ],
    )
    print("P3-06U-26H2W4 report export/archive static check passed.")


if __name__ == "__main__":
    main()
