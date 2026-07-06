#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

from lib.h2w_pack8_common import (
    ROOT,
    base_result,
    load_expected_summary,
    scan_text_file,
    write_json,
    write_markdown_report,
)


PHASE = "H2W-NC11"
SCHEMA_VERSION = "p3-06u-26h2w-nc11.postgres_restore_rehearsal_plan_gate.v1"
DEFAULT_OUTPUT_DIR = ROOT / "output/p3_06u_26h2w_nc11_postgres_restore_rehearsal_plan"
DOC_PATH = ROOT / "docs/P3-06U-26H2W_NC11_POSTGRES_RESTORE_REHEARSAL_PLAN.md"

NC10_SUMMARY = ROOT / "output/p3_06u_26h2w_nc10_postgres_backup_evidence_registration/summary.json"
LOCAL_BACKUPS_SERVICE = ROOT / "backend/app/services/local_backups.py"
LOCAL_BACKUPS_API = ROOT / "backend/app/api/local_backups.py"
LOCAL_BACKUPS_SCHEMA = ROOT / "backend/app/schemas/local_backups.py"
LOCAL_MAINTENANCE_SERVICE = ROOT / "backend/app/services/local_maintenance.py"
LOCAL_BACKUPS_TEST = ROOT / "backend/tests/test_local_backups_api.py"

SERVICE_MARKERS = [
    "POSTGRES_RESTORE_REHEARSAL_PLAN_SCHEMA_VERSION",
    "create_postgres_restore_rehearsal_plan",
    "_validate_postgres_restore_rehearsal_source",
    "_postgres_restore_rehearsal_plan_payload",
    "last_restore_rehearsal_plan",
    "postgres_restore_rehearsal_plan",
    "local_backup.postgres_restore_rehearsal_plan_created",
    "commands_executed",
    "requires_temporary_restore_first",
    "live_restore_performed",
    "database_replaced",
    "program_files_replaced",
]

API_MARKERS = [
    "/local-backups/{local_backup_id}/postgres-restore-rehearsal-plan",
    "LocalPostgresRestoreRehearsalPlanCreate",
    "create_postgres_restore_rehearsal_plan",
]

SCHEMA_MARKERS = [
    "class LocalPostgresRestoreRehearsalPlanCreate",
    "客户管理员生成 PostgreSQL 恢复演练计划",
]

MAINTENANCE_MARKERS = [
    "local_backup.postgres_restore_rehearsal_plan_created",
    "last_restore_rehearsal_plan",
]

TEST_MARKERS = [
    "test_owner_can_create_postgres_restore_rehearsal_plan_without_running_restore",
    "test_postgres_restore_rehearsal_plan_rejects_tampered_manifest",
    "commands_executed",
    "requires_temporary_restore_first",
    "database_replaced must be false",
]

OVERCLAIMS = [
    "PostgreSQL 真实恢复已完成",
    "客户现场恢复已完成",
    "真实数据库已替换",
    "正式签名安装包已完成",
    "真实外发已接通",
    "生产 SLA 已完成",
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
                blockers.append(f"{path.relative_to(ROOT)} 出现 NC11 越界表述：{phrase}")
        blockers.extend(scan_text_file(path))
    return blockers


def run_nc11(output_dir: Path = DEFAULT_OUTPUT_DIR, doc_path: Path = DOC_PATH) -> dict:
    blockers: list[str] = []
    _nc10_payload, nc10_status, nc10_errors = load_expected_summary(
        "NC10 PostgreSQL 备份证据登记",
        NC10_SUMMARY,
        {
            "postgres_backup_evidence_registration_ready_waiting_customer_pg_run",
            "postgres_backup_evidence_registration_ready_with_customer_pg_manifest",
        },
    )
    blockers.extend(nc10_errors)

    required_files = [
        LOCAL_BACKUPS_SERVICE,
        LOCAL_BACKUPS_API,
        LOCAL_BACKUPS_SCHEMA,
        LOCAL_MAINTENANCE_SERVICE,
        LOCAL_BACKUPS_TEST,
    ]
    for path in required_files:
        if not path.exists():
            blockers.append(f"NC11 必需文件缺失：{path.relative_to(ROOT)}")

    blockers.extend(_missing_markers(LOCAL_BACKUPS_SERVICE, SERVICE_MARKERS, "本地备份服务"))
    blockers.extend(_missing_markers(LOCAL_BACKUPS_API, API_MARKERS, "本地备份 API"))
    blockers.extend(_missing_markers(LOCAL_BACKUPS_SCHEMA, SCHEMA_MARKERS, "本地备份 schema"))
    blockers.extend(_missing_markers(LOCAL_MAINTENANCE_SERVICE, MAINTENANCE_MARKERS, "本地维护总账"))
    blockers.extend(_missing_markers(LOCAL_BACKUPS_TEST, TEST_MARKERS, "本地备份测试"))
    blockers.extend(_scan_overclaims(required_files))

    service_text = _text(LOCAL_BACKUPS_SERVICE)
    if "subprocess" in service_text:
        blockers.append("NC11 服务端不应通过 subprocess 执行恢复命令")

    result = base_result(
        SCHEMA_VERSION,
        PHASE,
        "postgres_restore_rehearsal_plan_ready_no_live_restore" if not blockers else "blocked",
        blockers,
    )
    result["upstreams"] = {"nc10": nc10_status}
    result["readiness"] = {
        "postgres_restore_rehearsal_plan_api_ready": not _missing_markers(
            LOCAL_BACKUPS_API, API_MARKERS, "本地备份 API"
        ),
        "postgres_restore_rehearsal_plan_service_ready": not _missing_markers(
            LOCAL_BACKUPS_SERVICE, SERVICE_MARKERS, "本地备份服务"
        ),
        "local_maintenance_counts_restore_plan_audit": not _missing_markers(
            LOCAL_MAINTENANCE_SERVICE, MAINTENANCE_MARKERS, "本地维护总账"
        ),
        "commands_executed_by_service": False,
        "live_restore_performed": False,
        "database_replaced": False,
        "program_files_replaced": False,
        "real_platform_send_ready": False,
        "requires_fresh_pre_restore_backup": True,
        "requires_customer_admin_confirmation": True,
    }
    result["implementation_notes"] = [
        "新增 PostgreSQL 恢复演练计划接口，基于已登记的 pg_dump/pg_restore --list manifest 生成计划。",
        "计划会写入 LocalBackupRecord 的 last_restore_rehearsal_plan / postgres_restore_rehearsal_plan。",
        "服务端只做计划、校验和审计，不执行 pg_restore，不替换数据库，不保存 dump 文件本体。",
        "本地维护总账已纳入 postgres_restore_rehearsal_plan_created 审计事件。",
    ]
    result["remaining_risks"] = [
        "客户现场 PostgreSQL 真实备份 manifest 仍可能未提供，NC11 只能证明计划接口和门禁就绪。",
        "真实恢复工具、临时库恢复、停机窗口、恢复后二次健康检查仍未变成自动化执行流程。",
        "正式签名安装包、真实渠道、真实外发、生产 SLA 和移动端仍未完成。",
    ]

    output_dir.mkdir(parents=True, exist_ok=True)
    write_json(output_dir / "summary.json", result)
    write_markdown_report(
        doc_path,
        "P3-06U-26 H2W-NC11 PostgreSQL 恢复演练计划",
        result,
        [
            ("本轮补强", result["implementation_notes"]),
            ("安全边界", [f"{key}: {value}" for key, value in result["readiness"].items()]),
            ("剩余风险", result["remaining_risks"]),
        ],
    )
    return result


def main() -> None:
    result = run_nc11()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result["blockers"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
