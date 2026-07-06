#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

from lib.h2w_pack8_common import (
    ROOT,
    base_result,
    display_path,
    load_expected_summary,
    scan_text_file,
    write_json,
    write_markdown_report,
)


PHASE = "H2W-NC15"
SCHEMA_VERSION = "p3-06u-26h2w-nc15.formal_restore_runbook_gate.v1"
DEFAULT_OUTPUT_DIR = ROOT / "output/p3_06u_26h2w_nc15_formal_restore_runbook"
DOC_PATH = ROOT / "docs/P3-06U-26H2W_NC15_FORMAL_RESTORE_RUNBOOK.md"

NC14_SUMMARY = ROOT / "output/p3_06u_26h2w_nc14_formal_restore_execution_dry_run/summary.json"
LOCAL_BACKUPS_SERVICE = ROOT / "backend/app/services/local_backups.py"
LOCAL_BACKUPS_API = ROOT / "backend/app/api/local_backups.py"
LOCAL_BACKUPS_SCHEMA = ROOT / "backend/app/schemas/local_backups.py"
LOCAL_MAINTENANCE_SERVICE = ROOT / "backend/app/services/local_maintenance.py"
LOCAL_BACKUPS_TEST = ROOT / "backend/tests/test_local_backups_api.py"

SERVICE_MARKERS = [
    "POSTGRES_FORMAL_RESTORE_RUNBOOK_SCHEMA_VERSION",
    "POSTGRES_FORMAL_RESTORE_RUNBOOK_REGISTRATION_SCHEMA_VERSION",
    "register_postgres_formal_restore_runbook",
    "_validate_postgres_formal_restore_runbook",
    "_postgres_formal_restore_runbook_record_payload",
    "last_formal_restore_execution_dry_run",
    "last_formal_restore_runbook",
    "postgres_formal_restore_runbook_payload",
    "local_backup.postgres_formal_restore_runbook_registered",
    "manual_execution_only",
    "restore_command_preview_hashes",
    "runbook_sensitive_material_stored",
    "pg_restore_executed_on_live_database",
]

API_MARKERS = [
    "/tenants/{tenant_id}/local-backups/postgres-formal-restore-runbook",
    "LocalPostgresFormalRestoreRunbookRegister",
    "register_postgres_formal_restore_runbook",
]

SCHEMA_MARKERS = [
    "class LocalPostgresFormalRestoreRunbookRegister",
    "backup_record_id: int",
    "runbook_payload: dict[str, Any]",
    "客户管理员登记 PostgreSQL 正式恢复 SOP 与停机编排门禁",
]

MAINTENANCE_MARKERS = [
    "local_backup.postgres_formal_restore_runbook_registered",
    "last_formal_restore_runbook",
]

TEST_MARKERS = [
    "test_owner_can_register_postgres_formal_restore_runbook_without_running_restore",
    "test_postgres_formal_restore_runbook_requires_execution_dry_run_and_rejects_live_flags",
    "last_formal_restore_execution_dry_run is required",
    "pg_restore_executed_on_live_database must be false",
    "runbook_sensitive_material_stored",
]

OVERCLAIMS = [
    "PostgreSQL 真实恢复已完成",
    "客户现场恢复已完成",
    "真实数据库已替换",
    "一键恢复已完成",
    "一键恢复可用",
    "生产恢复已完成",
    "真实外发已接通",
    "生产 SLA 已完成",
    "正式签名安装包已完成",
]


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def _missing_markers(path: Path, markers: list[str], label: str) -> list[str]:
    text = _text(path)
    return [f"{label} 缺少标记：{marker}" for marker in markers if marker not in text]


def _scan_overclaims(paths: list[Path]) -> list[str]:
    blockers: list[str] = []
    for path in paths:
        if not path.exists():
            continue
        text = _text(path)
        for phrase in OVERCLAIMS:
            if phrase in text:
                blockers.append(f"{display_path(path)} 出现 NC15 越界表述：{phrase}")
        blockers.extend(scan_text_file(path))
    return blockers


def run_nc15(output_dir: Path = DEFAULT_OUTPUT_DIR, doc_path: Path = DOC_PATH) -> dict:
    blockers: list[str] = []
    _nc14_payload, nc14_status, nc14_errors = load_expected_summary(
        "NC14 PostgreSQL 正式恢复执行 dry-run",
        NC14_SUMMARY,
        {"formal_restore_execution_dry_run_ready_no_live_restore"},
    )
    blockers.extend(nc14_errors)

    required_files = [
        LOCAL_BACKUPS_SERVICE,
        LOCAL_BACKUPS_API,
        LOCAL_BACKUPS_SCHEMA,
        LOCAL_MAINTENANCE_SERVICE,
        LOCAL_BACKUPS_TEST,
    ]
    for path in required_files:
        if not path.exists():
            blockers.append(f"NC15 必需文件缺失：{display_path(path)}")

    blockers.extend(_missing_markers(LOCAL_BACKUPS_SERVICE, SERVICE_MARKERS, "本地备份服务"))
    blockers.extend(_missing_markers(LOCAL_BACKUPS_API, API_MARKERS, "本地备份 API"))
    blockers.extend(_missing_markers(LOCAL_BACKUPS_SCHEMA, SCHEMA_MARKERS, "本地备份 schema"))
    blockers.extend(_missing_markers(LOCAL_MAINTENANCE_SERVICE, MAINTENANCE_MARKERS, "本地维护总账"))
    blockers.extend(_missing_markers(LOCAL_BACKUPS_TEST, TEST_MARKERS, "本地备份测试"))
    blockers.extend(_scan_overclaims(required_files))

    service_text = _text(LOCAL_BACKUPS_SERVICE)
    if "subprocess" in service_text:
        blockers.append("NC15 服务端不应通过 subprocess 执行恢复命令")
    for forbidden in (
        "pg_restore_executed_on_live_database\": True",
        "live_restore_performed\": True",
        "database_replaced\": True",
        "can_execute_restore_in_app\": True",
        "can_execute_restore_now\": True",
    ):
        if forbidden in service_text:
            blockers.append(f"NC15 服务端出现禁止状态：{forbidden}")

    status = "formal_restore_runbook_ready_no_live_restore"
    result = base_result(SCHEMA_VERSION, PHASE, status if not blockers else "blocked", blockers)
    result["upstreams"] = {"nc14": nc14_status}
    result["readiness"] = {
        "formal_restore_runbook_api_ready": not _missing_markers(LOCAL_BACKUPS_API, API_MARKERS, "本地备份 API"),
        "formal_restore_runbook_service_validation_ready": not _missing_markers(
            LOCAL_BACKUPS_SERVICE,
            SERVICE_MARKERS,
            "本地备份服务",
        ),
        "local_maintenance_counts_runbook_audit": not _missing_markers(
            LOCAL_MAINTENANCE_SERVICE,
            MAINTENANCE_MARKERS,
            "本地维护总账",
        ),
        "requires_nc14_execution_dry_run": True,
        "stores_command_hashes_only": True,
        "manual_execution_only": True,
        "service_runs_pg_restore": False,
        "live_restore_performed": False,
        "database_replaced": False,
        "real_platform_send_ready": False,
        "can_execute_restore_now": False,
        "can_execute_restore_in_app": False,
    }
    result["implementation_notes"] = [
        "新增 PostgreSQL 正式恢复 SOP 与停机编排门禁登记接口。",
        "NC15 强制要求 NC14 的正式恢复执行 dry-run 证据存在，并复核命令预览 hash 一致。",
        "登记内容只包含停机窗口、人工确认、恢复前二次备份、恢复后健康检查和回滚路径的门禁状态。",
        "服务端继续不执行 pg_restore、不保存原始恢复命令、不保存 dump 本体、不替换真实数据库、不打开真实外发。",
    ]
    result["remaining_risks"] = [
        "NC15 仍不是正式恢复执行工具；真实恢复只能在线下停机窗口由人工按 SOP 执行。",
        "尚未实现签名安装包、一键恢复、真实渠道闭环、生产 SLA 或移动端。",
        "没有真实客户现场资料时，只能验证 runbook 登记和阻断策略，不能写成客户恢复完成。",
    ]

    output_dir.mkdir(parents=True, exist_ok=True)
    write_json(output_dir / "summary.json", result)
    write_markdown_report(
        doc_path,
        "P3-06U-26 H2W-NC15 PostgreSQL 正式恢复 SOP 与停机编排门禁",
        result,
        [
            ("本轮补强", result["implementation_notes"]),
            ("验收边界", result["remaining_risks"]),
        ],
    )
    return result


def main() -> int:
    result = run_nc15()
    print(result["status"])
    if result["blockers"]:
        for blocker in result["blockers"]:
            print(f"- {blocker}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
