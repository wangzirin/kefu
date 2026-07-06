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


def main() -> None:
    require(
        "backend/app/models/foundation.py",
        [
            "class DiagnosticIntakeRecord",
            "diagnostic_intake_records",
            "package_payload",
        ],
    )
    require(
        "backend/app/migrations/versions/0029_diagnostic_intake_records.py",
        [
            "diagnostic_intake_records",
            "uq_diagnostic_intake_records_tenant_intake",
            "ix_diagnostic_intake_records_tenant_status",
        ],
    )
    require(
        "backend/app/services/diagnostics.py",
        [
            "INTAKE_SCHEMA_VERSION",
            "create_diagnostic_intake_record",
            "validate_diagnostic_upload_package",
            "diagnostic_bundle_sha256",
            "customer_authorization_recorded",
            "remote_control_performed",
            "customer_environment_write_performed",
        ],
    )
    require(
        "backend/app/api/diagnostics.py",
        [
            "/diagnostic-intake-records",
            "DiagnosticIntakeCreate",
            "DiagnosticIntakeDownloadRead",
            "UPDATES_MANAGE_PERMISSION",
        ],
    )
    require(
        "backend/tests/test_diagnostics_api.py",
        [
            "test_owner_can_register_diagnostic_intake_record_and_process_it",
            "test_diagnostic_intake_rejects_tampered_or_unsafe_package",
            "test_agent_cannot_use_diagnostic_intake_records",
        ],
    )
    require(
        "frontend/src/api/client.ts",
        [
            "DiagnosticIntakeRecord",
            "createDiagnosticIntakeRecord",
            "listDiagnosticIntakeRecords",
            "updateDiagnosticIntakeRecord",
            "downloadDiagnosticIntakeRecord",
        ],
    )
    require(
        "frontend/src/App.tsx",
        [
            'data-h2w5-cloud-intake="p3-06u-26h2w5"',
            "售后接收台",
            "不远程控制客户电脑",
            "不自动联网采集",
            "handleCreateDiagnosticIntakeRecord",
        ],
    )
    require(
        "docs/P3-06U-26H2W5_CLOUD_INTAKE_FIRST_SLICE.md",
        [
            "P3-06U-26H2W5 云接收台第一片",
            "不是远程控制客户电脑",
            "客户主动授权",
            "真实外发继续关闭",
        ],
    )
    require(
        "docs/FRONTEND_FUNCTION_REALITY_MATRIX.md",
        [
            "P3-06U-26H2W5",
            "售后接收台",
            "登记接收",
            "下载包",
        ],
    )
    print("P3-06U-26H2W5 cloud intake static check passed.")


if __name__ == "__main__":
    main()
