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


PHASE = "H2W-NC14"
SCHEMA_VERSION = "p3-06u-26h2w-nc14.formal_restore_execution_dry_run_gate.v1"
DEFAULT_OUTPUT_DIR = ROOT / "output/p3_06u_26h2w_nc14_formal_restore_execution_dry_run"
DOC_PATH = ROOT / "docs/P3-06U-26H2W_NC14_FORMAL_RESTORE_EXECUTION_DRY_RUN.md"

NC13_SUMMARY = ROOT / "output/p3_06u_26h2w_nc13_formal_restore_preflight/summary.json"
LOCAL_BACKUPS_SERVICE = ROOT / "backend/app/services/local_backups.py"
LOCAL_BACKUPS_API = ROOT / "backend/app/api/local_backups.py"
LOCAL_BACKUPS_SCHEMA = ROOT / "backend/app/schemas/local_backups.py"
LOCAL_MAINTENANCE_SERVICE = ROOT / "backend/app/services/local_maintenance.py"
LOCAL_BACKUPS_TEST = ROOT / "backend/tests/test_local_backups_api.py"
POSTGRES_FORMAL_RESTORE_DRY_RUN_SCRIPT = ROOT / "deploy/postgres-formal-restore-dry-run.sh"

SERVICE_MARKERS = [
    "POSTGRES_FORMAL_RESTORE_EXECUTION_DRY_RUN_SCHEMA_VERSION",
    "POSTGRES_FORMAL_RESTORE_EXECUTION_DRY_RUN_REGISTRATION_SCHEMA_VERSION",
    "register_postgres_formal_restore_execution_dry_run_manifest",
    "_validate_postgres_formal_restore_execution_dry_run_manifest",
    "_postgres_formal_restore_execution_dry_run_record_payload",
    "last_formal_restore_execution_dry_run",
    "postgres_formal_restore_execution_dry_run_manifest",
    "local_backup.postgres_formal_restore_execution_dry_run_registered",
    "raw_restore_command_stored",
    "restore_command_preview_hashes",
    "can_execute_restore_in_app",
    "pg_restore_executed_on_live_database",
]

API_MARKERS = [
    "/tenants/{tenant_id}/local-backups/postgres-formal-restore-execution-dry-run",
    "LocalPostgresFormalRestoreExecutionDryRunRegister",
    "register_postgres_formal_restore_execution_dry_run_manifest",
]

SCHEMA_MARKERS = [
    "class LocalPostgresFormalRestoreExecutionDryRunRegister",
    "backup_record_id: int",
    "manifest_payload: dict[str, Any]",
    "客户管理员登记 PostgreSQL 正式恢复执行 dry-run 证据",
]

MAINTENANCE_MARKERS = [
    "local_backup.postgres_formal_restore_execution_dry_run_registered",
    "last_formal_restore_execution_dry_run",
]

TEST_MARKERS = [
    "test_owner_can_register_postgres_formal_restore_execution_dry_run_without_running_restore",
    "test_postgres_formal_restore_execution_dry_run_requires_preflight_and_rejects_live_flags",
    "last_formal_restore_preflight is required",
    "pg_restore_executed_on_live_database must be false",
    "raw_restore_command_stored",
]

SCRIPT_MARKERS = [
    "p3-06u-26h2w-nc14.formal_restore_execution_dry_run.v1",
    "WANFA_POSTGRES_BACKUP_RUN_DIR",
    "restore_commands_rendered_not_executed",
    "restore_command_preview_hashes",
    "restore_command_preview_stored",
    "raw_restore_command_stored",
    '"live_restore_performed": False',
    '"database_replaced": False',
    '"commands_executed_on_live_database": False',
    '"pg_restore_executed_on_live_database": False',
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


def _latest_execution_dry_run_manifest() -> dict[str, Any]:
    root = ROOT / "output/p3_06u_26h2w_nc14_formal_restore_execution_dry_run"
    manifests = sorted(root.glob("*/manifest.json"), key=lambda item: item.stat().st_mtime, reverse=True)
    if not manifests:
        return {
            "present": False,
            "status": "waiting_customer_machine_formal_restore_execution_dry_run_manifest",
            "manifest_path": "",
        }
    path = manifests[0]
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"present": True, "status": "invalid_json", "manifest_path": display_path(path)}
    return {
        "present": True,
        "status": payload.get("status", "missing_status"),
        "manifest_path": display_path(path),
        "restore_commands_rendered_not_executed": payload.get("restore_commands_rendered_not_executed"),
        "restore_command_preview_hashes": payload.get("restore_command_preview_hashes"),
        "restore_command_preview_stored": payload.get("restore_command_preview_stored"),
        "raw_restore_command_stored": payload.get("raw_restore_command_stored"),
        "live_restore_performed": payload.get("live_restore_performed"),
        "database_replaced": payload.get("database_replaced"),
        "commands_executed_on_live_database": payload.get("commands_executed_on_live_database"),
        "pg_restore_executed_on_live_database": payload.get("pg_restore_executed_on_live_database"),
    }


def _scan_overclaims(paths: list[Path]) -> list[str]:
    blockers: list[str] = []
    for path in paths:
        if not path.exists():
            continue
        text = _text(path)
        for phrase in OVERCLAIMS:
            if phrase in text:
                blockers.append(f"{display_path(path)} 出现 NC14 越界表述：{phrase}")
        blockers.extend(scan_text_file(path))
    return blockers


def run_nc14(output_dir: Path = DEFAULT_OUTPUT_DIR, doc_path: Path = DOC_PATH) -> dict[str, Any]:
    blockers: list[str] = []
    _nc13_payload, nc13_status, nc13_errors = load_expected_summary(
        "NC13 PostgreSQL 正式恢复前置门禁",
        NC13_SUMMARY,
        {"formal_restore_preflight_gate_ready_no_live_restore"},
    )
    blockers.extend(nc13_errors)

    required_files = [
        LOCAL_BACKUPS_SERVICE,
        LOCAL_BACKUPS_API,
        LOCAL_BACKUPS_SCHEMA,
        LOCAL_MAINTENANCE_SERVICE,
        LOCAL_BACKUPS_TEST,
        POSTGRES_FORMAL_RESTORE_DRY_RUN_SCRIPT,
    ]
    for path in required_files:
        if not path.exists():
            blockers.append(f"NC14 必需文件缺失：{display_path(path)}")

    blockers.extend(_missing_markers(LOCAL_BACKUPS_SERVICE, SERVICE_MARKERS, "本地备份服务"))
    blockers.extend(_missing_markers(LOCAL_BACKUPS_API, API_MARKERS, "本地备份 API"))
    blockers.extend(_missing_markers(LOCAL_BACKUPS_SCHEMA, SCHEMA_MARKERS, "本地备份 schema"))
    blockers.extend(_missing_markers(LOCAL_MAINTENANCE_SERVICE, MAINTENANCE_MARKERS, "本地维护总账"))
    blockers.extend(_missing_markers(LOCAL_BACKUPS_TEST, TEST_MARKERS, "本地备份测试"))
    blockers.extend(
        _missing_markers(POSTGRES_FORMAL_RESTORE_DRY_RUN_SCRIPT, SCRIPT_MARKERS, "PostgreSQL 正式恢复执行 dry-run 脚本")
    )
    blockers.extend(_scan_overclaims(required_files))

    service_text = _text(LOCAL_BACKUPS_SERVICE)
    if "subprocess" in service_text:
        blockers.append("NC14 服务端不应通过 subprocess 执行恢复命令")

    dry_run_manifest = _latest_execution_dry_run_manifest()
    if dry_run_manifest["present"]:
        if dry_run_manifest.get("status") != "formal_restore_execution_dry_run_ready":
            blockers.append(f"PostgreSQL 正式恢复执行 dry-run manifest 状态异常：{dry_run_manifest.get('status')}")
        if dry_run_manifest.get("restore_commands_rendered_not_executed") is not True:
            blockers.append("PostgreSQL 正式恢复执行 dry-run manifest 未明确 restore_commands_rendered_not_executed=true")
        hashes = dry_run_manifest.get("restore_command_preview_hashes")
        if not isinstance(hashes, list) or not hashes:
            blockers.append("PostgreSQL 正式恢复执行 dry-run manifest 缺少命令预览 hash")
        for key in (
            "restore_command_preview_stored",
            "raw_restore_command_stored",
            "live_restore_performed",
            "database_replaced",
            "commands_executed_on_live_database",
            "pg_restore_executed_on_live_database",
        ):
            if dry_run_manifest.get(key) is not False:
                blockers.append(f"PostgreSQL 正式恢复执行 dry-run manifest 未明确 {key}=false")

    status = "formal_restore_execution_dry_run_ready_no_live_restore"
    result = base_result(SCHEMA_VERSION, PHASE, status if not blockers else "blocked", blockers)
    result["upstreams"] = {"nc13": nc13_status}
    result["latest_customer_machine_manifest"] = dry_run_manifest
    result["readiness"] = {
        "formal_restore_execution_dry_run_script_ready": not _missing_markers(
            POSTGRES_FORMAL_RESTORE_DRY_RUN_SCRIPT,
            SCRIPT_MARKERS,
            "PostgreSQL 正式恢复执行 dry-run 脚本",
        ),
        "formal_restore_execution_dry_run_api_ready": not _missing_markers(
            LOCAL_BACKUPS_API,
            API_MARKERS,
            "本地备份 API",
        ),
        "formal_restore_execution_dry_run_service_validation_ready": not _missing_markers(
            LOCAL_BACKUPS_SERVICE,
            SERVICE_MARKERS,
            "本地备份服务",
        ),
        "local_maintenance_counts_execution_dry_run_audit": not _missing_markers(
            LOCAL_MAINTENANCE_SERVICE,
            MAINTENANCE_MARKERS,
            "本地维护总账",
        ),
        "requires_nc10_backup_manifest": True,
        "requires_nc11_restore_plan": True,
        "requires_nc12_temp_restore_rehearsal": True,
        "requires_nc13_formal_restore_preflight": True,
        "stores_command_hashes_only": True,
        "service_runs_pg_restore": False,
        "live_restore_performed": False,
        "database_replaced": False,
        "real_platform_send_ready": False,
        "can_execute_restore_in_app": False,
    }
    result["implementation_notes"] = [
        "新增 PostgreSQL 正式恢复执行 dry-run 登记接口，只登记执行计划 manifest 和命令预览 hash。",
        "客户机脚本只校验环境与备份 sha，生成 manifest，不执行 pg_restore。",
        "服务端要求 NC13 last_formal_restore_preflight 存在，并继续保持 can_execute_restore_now=false。",
        "服务端仍不保存原始恢复命令、不保存 dump 本体、不替换真实数据库、不打开真实外发。",
    ]
    result["remaining_risks"] = [
        "NC14 仍不是正式恢复执行工具；停机编排、真实 pg_restore、健康检查执行和失败回滚尚未实现。",
        "没有客户机实际 NC8/NC12/NC14 manifest 时，只能验证代码门禁和等待态。",
        "真实渠道、真实外发、生产 SLA、签名 dmg/exe 安装器和移动端仍未完成。",
    ]

    output_dir.mkdir(parents=True, exist_ok=True)
    write_json(output_dir / "summary.json", result)
    write_markdown_report(
        doc_path,
        "P3-06U-26 H2W-NC14 PostgreSQL 正式恢复执行 dry-run 外壳",
        result,
        [
            ("本轮补强", result["implementation_notes"]),
            ("执行门禁", [f"{key}: {value}" for key, value in result["readiness"].items()]),
            ("剩余风险", result["remaining_risks"]),
        ],
    )
    return result


def main() -> None:
    result = run_nc14()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result["blockers"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
