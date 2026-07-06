#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    target = ROOT / path
    if not target.exists():
        raise AssertionError(f"missing required file: {path}")
    return target.read_text(encoding="utf-8")


def require(path: str, needles: list[str]) -> None:
    body = read(path)
    missing = [needle for needle in needles if needle not in body]
    if missing:
        raise AssertionError(f"{path} missing: {missing}")


def forbid(path: str, needles: list[str]) -> None:
    body = read(path)
    hits = [needle for needle in needles if needle in body]
    if hits:
        raise AssertionError(f"{path} contains forbidden phrases: {hits}")


def main() -> None:
    require(
        "backend/app/models/foundation.py",
        [
            "class DiagnosticRemediationRequest",
            "diagnostic_remediation_requests",
            "intake_record_id",
            "update_request_manifest",
        ],
    )
    require(
        "backend/app/migrations/versions/0030_diagnostic_remediation_requests.py",
        [
            "diagnostic_remediation_requests",
            "uq_diagnostic_remediation_requests_tenant_request",
            "ix_diagnostic_remediation_requests_tenant_status",
        ],
    )
    require(
        "backend/app/services/diagnostics.py",
        [
            "REMEDIATION_SCHEMA_VERSION",
            "create_diagnostic_remediation_request",
            "download_diagnostic_remediation_request",
            "can_generate_signed_update_package_now",
            "customer_environment_write_performed",
            "silent_update_performed",
            "requires_local_backup_before_apply",
        ],
    )
    require(
        "backend/app/api/diagnostics.py",
        [
            "/remediation-requests",
            "DiagnosticRemediationRequestCreate",
            "DiagnosticRemediationRequestDownloadRead",
            "UPDATES_MANAGE_PERMISSION",
        ],
    )
    require(
        "backend/tests/test_diagnostics_api.py",
        [
            "test_owner_can_create_remediation_request_from_accepted_intake",
            "test_remediation_request_cannot_be_created_from_rejected_intake",
            "can_apply_now",
            "customer_environment_write_performed",
        ],
    )
    require(
        "frontend/src/api/client.ts",
        [
            "DiagnosticRemediationRequest",
            "createDiagnosticRemediationRequest",
            "listDiagnosticRemediationRequests",
            "updateDiagnosticRemediationRequest",
            "downloadDiagnosticRemediationRequest",
        ],
    )
    require(
        "frontend/src/App.tsx",
        [
            'data-h2w6-remediation="p3-06u-26h2w6"',
            "处理回传包",
            "生成处理单",
            "下载回传包",
            "不静默更新",
            "不远程修改客户环境",
        ],
    )
    require(
        "docs/P3-06U-26H2W6_REMEDIATION_GATE_FIRST_SLICE.md",
        [
            "P3-06U-26H2W6 本地更新恢复处理单第一片",
            "不是完整自动更新器",
            "真实外发继续关闭",
            "不远程控制客户电脑",
        ],
    )
    require(
        "docs/FRONTEND_FUNCTION_REALITY_MATRIX.md",
        [
            "P3-06U-26H2W6",
            "生成处理单",
            "下载回传包",
        ],
    )
    forbid(
        "docs/P3-06U-26H2W6_REMEDIATION_GATE_FIRST_SLICE.md",
        [
            "已完成自动更新器",
            "已远程更新客户环境",
            "可以静默更新客户环境",
            "支持静默更新客户环境",
            "真实外发已打开",
        ],
    )
    print("P3-06U-26H2W6 remediation static check passed.")


if __name__ == "__main__":
    main()
