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


PHASE = "H2W-NC12"
SCHEMA_VERSION = "p3-06u-26h2w-nc12.postgres_temp_restore_rehearsal_gate.v1"
DEFAULT_OUTPUT_DIR = ROOT / "output/p3_06u_26h2w_nc12_postgres_temp_restore_rehearsal"
DOC_PATH = ROOT / "docs/P3-06U-26H2W_NC12_POSTGRES_TEMP_RESTORE_REHEARSAL.md"

NC11_SUMMARY = ROOT / "output/p3_06u_26h2w_nc11_postgres_restore_rehearsal_plan/summary.json"
LOCAL_BACKUPS_SERVICE = ROOT / "backend/app/services/local_backups.py"
LOCAL_BACKUPS_API = ROOT / "backend/app/api/local_backups.py"
LOCAL_BACKUPS_SCHEMA = ROOT / "backend/app/schemas/local_backups.py"
LOCAL_MAINTENANCE_SERVICE = ROOT / "backend/app/services/local_maintenance.py"
LOCAL_BACKUPS_TEST = ROOT / "backend/tests/test_local_backups_api.py"
POSTGRES_TEMP_RESTORE_SCRIPT = ROOT / "deploy/postgres-temp-restore-rehearsal.sh"

SERVICE_MARKERS = [
    "POSTGRES_TEMP_RESTORE_REHEARSAL_SCHEMA_VERSION",
    "POSTGRES_TEMP_RESTORE_REGISTRATION_SCHEMA_VERSION",
    "register_postgres_temp_restore_rehearsal_manifest",
    "_validate_postgres_temp_restore_rehearsal_manifest",
    "_postgres_temp_restore_rehearsal_record_payload",
    "last_temp_restore_rehearsal",
    "postgres_temp_restore_rehearsal_manifest",
    "local_backup.postgres_temp_restore_manifest_registered",
    "pg_restore_to_temporary_database_only",
    "temp_database_name_hash",
    "commands_executed_on_live_database",
    "can_restore_now",
]

API_MARKERS = [
    "/tenants/{tenant_id}/local-backups/postgres-temp-restore-manifests",
    "LocalPostgresTempRestoreManifestRegister",
    "register_postgres_temp_restore_rehearsal_manifest",
]

SCHEMA_MARKERS = [
    "class LocalPostgresTempRestoreManifestRegister",
    "backup_record_id: int",
    "客户管理员登记 PostgreSQL 临时库恢复演练证据",
]

MAINTENANCE_MARKERS = [
    "local_backup.postgres_temp_restore_manifest_registered",
    "last_temp_restore_rehearsal",
]

TEST_MARKERS = [
    "test_owner_can_register_postgres_temp_restore_manifest_without_live_restore",
    "test_postgres_temp_restore_manifest_rejects_live_or_unsafe_database",
    "temp_database_name must use a safe wanfa_restore_tmp_ prefix",
    "commands_executed_on_live_database",
]

SCRIPT_MARKERS = [
    "p3-06u-26h2w-nc12.postgres_temp_restore_rehearsal.v1",
    "WANFA_POSTGRES_BACKUP_RUN_DIR",
    "wanfa_restore_tmp_",
    "createdb",
    "pg_restore --clean",
    "dropdb",
    '"live_restore_performed": False',
    '"live_database_replaced": False',
    '"database_replaced": False',
    '"commands_executed_on_live_database": False',
]

OVERCLAIMS = [
    "PostgreSQL 真实恢复已完成",
    "客户现场恢复已完成",
    "真实数据库已替换",
    "真实外发已接通",
    "生产 SLA 已完成",
    "正式签名安装包已完成",
]


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def _missing_markers(path: Path, markers: list[str], label: str) -> list[str]:
    text = _text(path)
    return [f"{label} 缺少标记：{marker}" for marker in markers if marker not in text]


def _latest_temp_restore_manifest() -> dict[str, Any]:
    root = ROOT / "output/p3_06u_26h2w_nc12_postgres_temp_restore_rehearsal"
    manifests = sorted(root.glob("*/manifest.json"), key=lambda item: item.stat().st_mtime, reverse=True)
    if not manifests:
        return {
            "present": False,
            "status": "waiting_customer_machine_postgres_temp_restore_rehearsal",
            "manifest_path": "",
        }
    path = manifests[0]
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {
            "present": True,
            "status": "invalid_json",
            "manifest_path": display_path(path),
        }
    return {
        "present": True,
        "status": payload.get("status", "missing_status"),
        "manifest_path": display_path(path),
        "temp_database_created": payload.get("temp_database_created"),
        "pg_restore_into_temp_completed": payload.get("pg_restore_into_temp_completed"),
        "health_checks_completed": payload.get("health_checks_completed"),
        "temp_database_dropped": payload.get("temp_database_dropped"),
        "live_restore_performed": payload.get("live_restore_performed"),
        "database_replaced": payload.get("database_replaced"),
        "commands_executed_on_live_database": payload.get("commands_executed_on_live_database"),
    }


def _scan_overclaims(paths: list[Path]) -> list[str]:
    blockers: list[str] = []
    for path in paths:
        if not path.exists():
            continue
        text = _text(path)
        for phrase in OVERCLAIMS:
            if phrase in text:
                blockers.append(f"{display_path(path)} 出现 NC12 越界表述：{phrase}")
        blockers.extend(scan_text_file(path))
    return blockers


def run_nc12(output_dir: Path = DEFAULT_OUTPUT_DIR, doc_path: Path = DOC_PATH) -> dict[str, Any]:
    blockers: list[str] = []
    _nc11_payload, nc11_status, nc11_errors = load_expected_summary(
        "NC11 PostgreSQL 恢复演练计划",
        NC11_SUMMARY,
        {"postgres_restore_rehearsal_plan_ready_no_live_restore"},
    )
    blockers.extend(nc11_errors)

    required_files = [
        LOCAL_BACKUPS_SERVICE,
        LOCAL_BACKUPS_API,
        LOCAL_BACKUPS_SCHEMA,
        LOCAL_MAINTENANCE_SERVICE,
        LOCAL_BACKUPS_TEST,
        POSTGRES_TEMP_RESTORE_SCRIPT,
    ]
    for path in required_files:
        if not path.exists():
            blockers.append(f"NC12 必需文件缺失：{display_path(path)}")

    blockers.extend(_missing_markers(LOCAL_BACKUPS_SERVICE, SERVICE_MARKERS, "本地备份服务"))
    blockers.extend(_missing_markers(LOCAL_BACKUPS_API, API_MARKERS, "本地备份 API"))
    blockers.extend(_missing_markers(LOCAL_BACKUPS_SCHEMA, SCHEMA_MARKERS, "本地备份 schema"))
    blockers.extend(_missing_markers(LOCAL_MAINTENANCE_SERVICE, MAINTENANCE_MARKERS, "本地维护总账"))
    blockers.extend(_missing_markers(LOCAL_BACKUPS_TEST, TEST_MARKERS, "本地备份测试"))
    blockers.extend(_missing_markers(POSTGRES_TEMP_RESTORE_SCRIPT, SCRIPT_MARKERS, "PostgreSQL 临时库恢复脚本"))
    blockers.extend(_scan_overclaims(required_files))

    service_text = _text(LOCAL_BACKUPS_SERVICE)
    if "subprocess" in service_text:
        blockers.append("NC12 服务端不应通过 subprocess 执行恢复命令")

    temp_restore_manifest = _latest_temp_restore_manifest()
    if temp_restore_manifest["present"]:
        if temp_restore_manifest.get("status") != "postgres_temp_restore_rehearsal_ready":
            blockers.append(f"PostgreSQL 临时库恢复 manifest 状态异常：{temp_restore_manifest.get('status')}")
        for key in (
            "temp_database_created",
            "pg_restore_into_temp_completed",
            "health_checks_completed",
            "temp_database_dropped",
        ):
            if temp_restore_manifest.get(key) is not True:
                blockers.append(f"PostgreSQL 临时库恢复 manifest 未明确 {key}=true")
        for key in ("live_restore_performed", "database_replaced", "commands_executed_on_live_database"):
            if temp_restore_manifest.get(key) is not False:
                blockers.append(f"PostgreSQL 临时库恢复 manifest 未明确 {key}=false")

    status = (
        "postgres_temp_restore_rehearsal_ready_with_customer_temp_restore_manifest"
        if temp_restore_manifest["present"] and not blockers
        else "postgres_temp_restore_rehearsal_ready_waiting_customer_pg_run"
    )
    result = base_result(SCHEMA_VERSION, PHASE, status if not blockers else "blocked", blockers)
    result["upstreams"] = {"nc11": nc11_status}
    result["readiness"] = {
        "postgres_temp_restore_script_ready": not _missing_markers(
            POSTGRES_TEMP_RESTORE_SCRIPT,
            SCRIPT_MARKERS,
            "PostgreSQL 临时库恢复脚本",
        ),
        "postgres_temp_restore_manifest_api_ready": not _missing_markers(
            LOCAL_BACKUPS_API,
            API_MARKERS,
            "本地备份 API",
        ),
        "postgres_temp_restore_service_validation_ready": not _missing_markers(
            LOCAL_BACKUPS_SERVICE,
            SERVICE_MARKERS,
            "本地备份服务",
        ),
        "local_maintenance_counts_temp_restore_audit": not _missing_markers(
            LOCAL_MAINTENANCE_SERVICE,
            MAINTENANCE_MARKERS,
            "本地维护总账",
        ),
        "customer_machine_temp_restore_manifest_present": bool(temp_restore_manifest["present"]),
        "service_runs_pg_restore": False,
        "live_restore_performed": False,
        "database_replaced": False,
        "program_files_replaced": False,
        "real_platform_send_ready": False,
        "requires_customer_machine_pg_run": True,
    }
    result["postgres_temp_restore_manifest"] = temp_restore_manifest
    result["implementation_notes"] = [
        "新增客户机 PostgreSQL 临时库恢复演练脚本：创建临时库、pg_restore、健康检查、删除临时库。",
        "新增临时库恢复 manifest 登记接口，只登记证据，不保存 dump 文件或执行服务端恢复命令。",
        "服务端校验备份 sha256、临时库安全前缀、健康检查、临时库已删除，以及所有真实恢复/外发开关为 false。",
        "本地维护总账已纳入 postgres_temp_restore_manifest_registered 审计事件。",
    ]
    result["remaining_risks"] = [
        "当前若未在客户 Docker 环境实际运行脚本，仍只能写等待客户机临时库恢复 manifest。",
        "正式恢复执行、停机窗口、恢复前二次备份、客户管理员确认和失败回滚仍未自动化。",
        "真实渠道、真实外发、生产 SLA、签名 dmg/exe 安装器和移动端仍未完成。",
    ]

    output_dir.mkdir(parents=True, exist_ok=True)
    write_json(output_dir / "summary.json", result)
    write_markdown_report(
        doc_path,
        "P3-06U-26 H2W-NC12 PostgreSQL 临时库恢复演练",
        result,
        [
            ("本轮补强", result["implementation_notes"]),
            ("PostgreSQL 临时库恢复 manifest 状态", [f"{key}: {value}" for key, value in temp_restore_manifest.items()]),
            ("剩余风险", result["remaining_risks"]),
        ],
    )
    return result


def main() -> None:
    result = run_nc12()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result["blockers"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
