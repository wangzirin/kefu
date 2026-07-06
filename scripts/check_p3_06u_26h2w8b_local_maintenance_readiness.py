from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


REQUIRED_MARKERS = {
    "backend/app/services/local_maintenance.py": [
        "p3-06u-26h2w8b.local_maintenance_readiness.v1",
        "ready_for_customer_maintenance_rehearsal",
        "diagnostic_intake_accepted",
        "remediation_update_plan_prepared",
        "signed_update_package_total",
        "local_backup_verified",
        "restore_dry_run_total",
        "external_write_performed",
        "remote_control_performed",
        "silent_update_performed",
        "automatic_upload_performed",
        "can_restore_now",
        "真实外发继续关闭",
    ],
    "backend/app/api/diagnostics.py": [
        "/tenants/{tenant_id}/local-maintenance/readiness",
        "LocalMaintenanceReadinessRead",
        "build_local_maintenance_readiness",
        "UPDATES_MANAGE_PERMISSION",
    ],
    "backend/app/schemas/diagnostics.py": [
        "class LocalMaintenanceReadinessRead",
        "maturity_status",
        "gates",
        "blockers",
        "recent_audit_events",
    ],
    "backend/tests/test_local_maintenance_readiness_api.py": [
        "test_owner_reads_local_maintenance_readiness_with_full_evidence",
        "test_agent_cannot_read_local_maintenance_readiness",
        "ready_for_rehearsal",
        "manual_transfer_required",
    ],
    "frontend/src/api/client.ts": [
        "interface LocalMaintenanceReadiness",
        "interface LocalMaintenanceGate",
        "getLocalMaintenanceReadiness",
        "/local-maintenance/readiness",
    ],
    "frontend/src/App.tsx": [
        "LocalMaintenanceReadinessState",
        "refreshLocalMaintenanceReadiness",
        'data-h2w8b-local-maintenance="p3-06u-26h2w8b"',
        'data-role-smoke="diagnostic-intake-package-input"',
        'data-role-smoke="local-backup-verify"',
        "本地维护闭环",
        "账号与本地维护",
        "继续补证据",
    ],
    "frontend/src/styles.css": [
        ".local-maintenance-card",
        ".local-maintenance-metrics",
        ".local-maintenance-gates",
        ".local-maintenance-blockers",
    ],
    "docs/P3-06U-26H2W8B_LOCAL_MAINTENANCE_READINESS_FIRST_SLICE.md": [
        "H2W-8B",
        "本地维护闭环",
        "ready_for_rehearsal",
        "missing_evidence",
        "blocked",
        "停止门禁",
        "真实外发继续关闭",
    ],
    "scripts/check_p3_06u_26h2w8b_local_maintenance_ui.mjs": [
        "H2W8B local maintenance UI smoke passed",
        "browser_logged_in_through_real_form",
        "diagnostic-intake-package-input",
        "local-backup-verify",
        "local-restore-dry-run-result",
        "ready_for_rehearsal",
        "real_platform_send_performed: false",
    ],
}


FORBIDDEN_MARKERS = {
    "docs/P3-06U-26H2W8B_LOCAL_MAINTENANCE_READINESS_FIRST_SLICE.md": [
        "自动上传已上线",
        "已远程控制客户电脑",
        "静默更新已完成",
        "真实外发已接通",
    ],
}


def read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def main() -> None:
    failures: list[str] = []
    for relative_path, markers in REQUIRED_MARKERS.items():
        path = ROOT / relative_path
        if not path.exists():
            failures.append(f"missing file: {relative_path}")
            continue
        text = read(relative_path)
        for marker in markers:
            if marker not in text:
                failures.append(f"{relative_path}: missing marker {marker!r}")

    for relative_path, markers in FORBIDDEN_MARKERS.items():
        text = read(relative_path)
        for marker in markers:
            if marker in text:
                failures.append(f"{relative_path}: forbidden marker {marker!r}")

    if failures:
        raise SystemExit("\n".join(failures))
    print("P3-06U-26H2W8B local maintenance readiness static gate passed.")


if __name__ == "__main__":
    main()
