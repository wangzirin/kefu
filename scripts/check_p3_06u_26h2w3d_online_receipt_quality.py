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
        raise AssertionError(f"{path} contains forbidden overclaim markers: {found}")


def main() -> None:
    require_contains(
        "backend/app/schemas/channel_connectors.py",
        [
            "OnlineReceiptQualitySummaryRead",
            "raw_payload_included: bool",
            "customer_accuracy_completed: bool",
            "real_platform_receipts_required_for_full_accuracy: bool",
            "real_external_write_performed: bool",
        ],
    )
    require_contains(
        "backend/app/services/channel_connectors.py",
        [
            "get_online_receipt_quality_summary",
            "p3-06u-26h2w3d.online_receipt_quality.v1",
            "线上回执链路覆盖率，不是完整客服答案准确率",
            "真实外发继续关闭",
            '"raw_payload_included": False',
            '"customer_accuracy_completed": False',
            '"external_platform_write_performed": False',
            '"real_external_write_performed": False',
        ],
    )
    require_contains(
        "backend/app/api/channel_connectors.py",
        [
            "/tenants/{tenant_id}/online-receipt-quality-summary",
            "OnlineReceiptQualitySummaryRead",
            "QUALITY_READ_PERMISSION",
        ],
    )
    require_contains(
        "backend/tests/test_channel_connectors_api.py",
        [
            "test_online_receipt_quality_summary_is_bounded_and_does_not_claim_full_accuracy",
            "must-not-appear-in-summary",
            "customer_accuracy_completed",
            "real_external_write_performed",
        ],
    )
    require_contains(
        "frontend/src/api/client.ts",
        [
            "OnlineReceiptQualitySummary",
            "getOnlineReceiptQualitySummary",
            "/api/tenants/${tenantId}/online-receipt-quality-summary",
        ],
    )
    require_contains(
        "frontend/src/App.tsx",
        [
            "OnlineReceiptQualityState",
            "refreshOnlineReceiptQuality",
            "getOnlineReceiptQualitySummary",
            "onlineReceiptQuality",
            "真实外发继续关闭",
        ],
    )
    require_contains(
        "frontend/src/components/quality/QualityReviewPanel.tsx",
        [
            'data-h2w3d-online-receipt-quality="p3-06u-26h2w3d"',
            "线上回执闭环证据",
            "完整客服答案准确率",
            "真实外发继续关闭",
            "不展示完整线上准确率",
        ],
    )
    require_contains(
        "frontend/src/styles.css",
        [
            ".h2w3-receipt-evidence",
            ".h2w3-receipt-gates",
            ".h2w3-provider-breakdown",
        ],
    )
    require_contains(
        "docs/P3-06U-26H2W3D_ONLINE_RECEIPT_ACCURACY_LOOP_FIRST_SLICE.md",
        [
            "# P3-06U-26H2W3D 线上回执与准确率闭环第一片",
            "不把检索命中率、回执送达率、样本评测结果包装成完整客服准确率",
            "真实外发继续关闭",
            "停止门禁",
            "raw_payload_included=true",
            "customer_accuracy_completed=true",
        ],
    )
    require_contains(
        "docs/FRONTEND_FUNCTION_REALITY_MATRIX.md",
        [
            "P3-06U-26H2W3D",
            "线上回执闭环证据",
            "回执链路覆盖",
            "完整客服答案准确率",
        ],
    )
    require_absent(
        "docs/P3-06U-26H2W3D_ONLINE_RECEIPT_ACCURACY_LOOP_FIRST_SLICE.md",
        [
            "完整线上准确率已完成",
            "已接通所有真实平台",
            "真实外发已开启",
            "无需人工标签",
        ],
    )
    print("P3-06U-26H2W3D online receipt quality static check passed.")


if __name__ == "__main__":
    main()
