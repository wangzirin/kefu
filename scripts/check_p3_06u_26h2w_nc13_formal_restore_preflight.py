#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from lib.h2w_pack8_common import (
    ROOT,
    base_result,
    display_path,
    load_expected_summary,
    scan_text_file,
    write_json,
    write_markdown_report,
)


PHASE = "H2W-NC13"
SCHEMA_VERSION = "p3-06u-26h2w-nc13.formal_restore_preflight_gate.v1"
DEFAULT_OUTPUT_DIR = ROOT / "output/p3_06u_26h2w_nc13_formal_restore_preflight"
DOC_PATH = ROOT / "docs/P3-06U-26H2W_NC13_FORMAL_RESTORE_PREFLIGHT.md"

NC12_SUMMARY = ROOT / "output/p3_06u_26h2w_nc12_postgres_temp_restore_rehearsal/summary.json"
LOCAL_BACKUPS_SERVICE = ROOT / "backend/app/services/local_backups.py"
LOCAL_BACKUPS_API = ROOT / "backend/app/api/local_backups.py"
LOCAL_BACKUPS_SCHEMA = ROOT / "backend/app/schemas/local_backups.py"
LOCAL_MAINTENANCE_SERVICE = ROOT / "backend/app/services/local_maintenance.py"
LOCAL_BACKUPS_TEST = ROOT / "backend/tests/test_local_backups_api.py"

SERVICE_MARKERS = [
    "POSTGRES_FORMAL_RESTORE_PREFLIGHT_SCHEMA_VERSION",
    "POSTGRES_FORMAL_RESTORE_PREFLIGHT_REGISTRATION_SCHEMA_VERSION",
    "register_postgres_formal_restore_preflight_approval",
    "_validate_postgres_formal_restore_preflight_confirmation",
    "_postgres_formal_restore_preflight_record_payload",
    "last_formal_restore_preflight",
    "postgres_formal_restore_preflight_confirmation",
    "local_backup.postgres_formal_restore_preflight_registered",
    "can_execute_restore_now",
    "can_execute_restore_in_app",
    "requires_final_operator_confirmation",
    "commands_executed_on_live_database",
]

API_MARKERS = [
    "/tenants/{tenant_id}/local-backups/postgres-formal-restore-preflight",
    "LocalPostgresFormalRestorePreflightRegister",
    "register_postgres_formal_restore_preflight_approval",
]

SCHEMA_MARKERS = [
    "class LocalPostgresFormalRestorePreflightRegister",
    "backup_record_id: int",
    "confirmation_payload: dict[str, Any]",
    "客户管理员登记 PostgreSQL 正式恢复前确认门禁",
]

MAINTENANCE_MARKERS = [
    "local_backup.postgres_formal_restore_preflight_registered",
    "last_formal_restore_preflight",
]

TEST_MARKERS = [
    "test_owner_can_register_postgres_formal_restore_preflight_without_executing_restore",
    "test_postgres_formal_restore_preflight_requires_temp_restore_and_rejects_live_flags",
    "can_execute_restore_in_app",
    "last_temp_restore_rehearsal is required",
    "live_restore_performed must be false",
]

OVERCLAIMS = [
    "PostgreSQL 真实恢复已完成",
    "客户现场恢复已完成",
    "真实数据库已替换",
    "一键恢复已完成",
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
                blockers.append(f"{display_path(path)} 出现 NC13 越界表述：{phrase}")
        blockers.extend(scan_text_file(path))
    return blockers


def run_nc13(output_dir: Path = DEFAULT_OUTPUT_DIR, doc_path: Path = DOC_PATH) -> dict[str, Any]:
    blockers: list[str] = []
    _nc12_payload, nc12_status, nc12_errors = load_expected_summary(
        "NC12 PostgreSQL 临时库恢复演练",
        NC12_SUMMARY,
        {
            "postgres_temp_restore_rehearsal_ready_waiting_customer_pg_run",
            "postgres_temp_restore_rehearsal_ready_with_customer_temp_restore_manifest",
        },
    )
    blockers.extend(nc12_errors)

    required_files = [
        LOCAL_BACKUPS_SERVICE,
        LOCAL_BACKUPS_API,
        LOCAL_BACKUPS_SCHEMA,
        LOCAL_MAINTENANCE_SERVICE,
        LOCAL_BACKUPS_TEST,
    ]
    for path in required_files:
        if not path.exists():
            blockers.append(f"NC13 必需文件缺失：{display_path(path)}")

    blockers.extend(_missing_markers(LOCAL_BACKUPS_SERVICE, SERVICE_MARKERS, "本地备份服务"))
    blockers.extend(_missing_markers(LOCAL_BACKUPS_API, API_MARKERS, "本地备份 API"))
    blockers.extend(_missing_markers(LOCAL_BACKUPS_SCHEMA, SCHEMA_MARKERS, "本地备份 schema"))
    blockers.extend(_missing_markers(LOCAL_MAINTENANCE_SERVICE, MAINTENANCE_MARKERS, "本地维护总账"))
    blockers.extend(_missing_markers(LOCAL_BACKUPS_TEST, TEST_MARKERS, "本地备份测试"))
    blockers.extend(_scan_overclaims(required_files))

    service_text = _text(LOCAL_BACKUPS_SERVICE)
    if "subprocess" in service_text:
        blockers.append("NC13 服务端不应通过 subprocess 执行恢复命令")

    status = "formal_restore_preflight_gate_ready_no_live_restore" if not blockers else "blocked"
    result = base_result(SCHEMA_VERSION, PHASE, status, blockers)
    result["upstreams"] = {"nc12": nc12_status}
    result["readiness"] = {
        "formal_restore_preflight_api_ready": not _missing_markers(
            LOCAL_BACKUPS_API,
            API_MARKERS,
            "本地备份 API",
        ),
        "formal_restore_preflight_service_validation_ready": not _missing_markers(
            LOCAL_BACKUPS_SERVICE,
            SERVICE_MARKERS,
            "本地备份服务",
        ),
        "local_maintenance_counts_formal_restore_audit": not _missing_markers(
            LOCAL_MAINTENANCE_SERVICE,
            MAINTENANCE_MARKERS,
            "本地维护总账",
        ),
        "requires_nc10_backup_manifest": True,
        "requires_nc11_restore_plan": True,
        "requires_nc12_temp_restore_rehearsal": True,
        "requires_customer_admin_confirmation": True,
        "requires_fresh_pre_restore_backup": True,
        "requires_final_operator_confirmation": True,
        "service_runs_pg_restore": False,
        "live_restore_performed": False,
        "database_replaced": False,
        "real_platform_send_ready": False,
        "can_execute_restore_in_app": False,
    }
    result["implementation_notes"] = [
        "新增 PostgreSQL 正式恢复前置确认登记接口，只登记客户管理员确认包和门禁证据。",
        "服务端要求 NC10 备份 manifest、NC11 恢复计划和 NC12 临时库恢复演练都已经存在。",
        "确认包必须明确维护窗口、停止服务窗口、恢复前二次备份、健康检查、回滚计划和最终操作员确认。",
        "服务端仍不执行 pg_restore、不替换真实数据库、不打开真实外发。",
    ]
    result["remaining_risks"] = [
        "NC13 仍不是正式恢复执行工具；生产恢复命令、停机编排和恢复后自动健康检查尚未实现。",
        "没有客户机实际 NC12 manifest 时，NC13 只能验证代码门禁和等待态。",
        "真实渠道、真实外发、生产 SLA、签名 dmg/exe 安装器和移动端仍未完成。",
    ]

    output_dir.mkdir(parents=True, exist_ok=True)
    write_json(output_dir / "summary.json", result)
    write_markdown_report(
        doc_path,
        "P3-06U-26 H2W-NC13 PostgreSQL 正式恢复前置门禁",
        result,
        [
            ("本轮补强", result["implementation_notes"]),
            ("前置门禁", [f"{key}: {value}" for key, value in result["readiness"].items()]),
            ("剩余风险", result["remaining_risks"]),
        ],
    )
    return result


def main() -> None:
    result = run_nc13()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result["blockers"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
