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


PHASE = "H2W-NC10"
SCHEMA_VERSION = "p3-06u-26h2w-nc10.postgres_backup_evidence_registration.v1"
DEFAULT_OUTPUT_DIR = ROOT / "output/p3_06u_26h2w_nc10_postgres_backup_evidence_registration"
DOC_PATH = ROOT / "docs/P3-06U-26H2W_NC10_POSTGRES_BACKUP_EVIDENCE_REGISTRATION.md"

NC8_SUMMARY = ROOT / "output/p3_06u_26h2w_nc8_local_install_backup_update_rollback/summary.json"
LOCAL_BACKUPS_SERVICE = ROOT / "backend/app/services/local_backups.py"
LOCAL_BACKUPS_API = ROOT / "backend/app/api/local_backups.py"
LOCAL_BACKUPS_SCHEMA = ROOT / "backend/app/schemas/local_backups.py"
LOCAL_MAINTENANCE_SERVICE = ROOT / "backend/app/services/local_maintenance.py"
LOCAL_BACKUPS_TEST = ROOT / "backend/tests/test_local_backups_api.py"
POSTGRES_BACKUP_SCRIPT = ROOT / "deploy/postgres-backup-dry-run.sh"

SERVICE_MARKERS = [
    "register_postgres_backup_dry_run_manifest",
    "POSTGRES_BACKUP_DRY_RUN_SCHEMA_VERSION",
    "POSTGRES_BACKUP_REGISTRATION_SCHEMA_VERSION",
    "POSTGRES_RESTORE_DRY_RUN_SCHEMA_VERSION",
    "local_backup.postgres_dry_run_manifest_registered",
    "postgres_pg_dump_custom",
    "pg_restore_list_rehearsal_only",
    "backup_file_body_stored",
    "live_restore_performed",
    "database_file_replaced",
]

API_MARKERS = [
    "/tenants/{tenant_id}/local-backups/postgres-dry-run-manifests",
    "LocalPostgresBackupManifestRegister",
    "register_postgres_backup_dry_run_manifest",
]

SCHEMA_MARKERS = [
    "class LocalPostgresBackupManifestRegister",
    "manifest_payload: dict[str, Any]",
]

MAINTENANCE_MARKERS = [
    "local_backup.postgres_dry_run_manifest_registered",
]

TEST_MARKERS = [
    "test_owner_can_register_postgres_backup_dry_run_manifest",
    "test_postgres_backup_manifest_rejects_restore_or_secret_fields",
    "live_restore_performed must be false",
    "sensitive key",
]

SCRIPT_MARKERS = [
    "p3-06u-26h2w-nc8.postgres_backup_dry_run.v1",
    "pg_dump -Fc",
    "pg_restore --list",
    '"live_restore_performed": false',
    '"database_replaced": false',
]

OVERCLAIMS = [
    "客户现场 PostgreSQL 备份已完成",
    "PostgreSQL 真实恢复已完成",
    "正式签名安装包已完成",
    "真实外发已接通",
    "生产 SLA 已完成",
]


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def _missing_markers(path: Path, markers: list[str], label: str) -> list[str]:
    text = _text(path)
    return [f"{label} 缺少标记：{marker}" for marker in markers if marker not in text]


def _latest_postgres_manifest() -> dict[str, Any]:
    root = ROOT / "output/p3_06u_26h2w_nc8_postgres_backup_dry_run"
    manifests = sorted(root.glob("*/manifest.json"), key=lambda item: item.stat().st_mtime, reverse=True)
    if not manifests:
        return {
            "present": False,
            "status": "waiting_customer_machine_postgres_backup_dry_run",
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
        "pg_dump_completed": payload.get("pg_dump_completed"),
        "pg_restore_list_completed": payload.get("pg_restore_list_completed"),
        "live_restore_performed": payload.get("live_restore_performed"),
        "database_replaced": payload.get("database_replaced"),
        "backup_size_bytes": payload.get("backup_size_bytes"),
    }


def _scan_overclaims(paths: list[Path]) -> list[str]:
    blockers: list[str] = []
    for path in paths:
        if not path.exists():
            continue
        text = _text(path)
        for phrase in OVERCLAIMS:
            if phrase in text:
                blockers.append(f"{display_path(path)} 出现 NC10 越界表述：{phrase}")
        blockers.extend(scan_text_file(path))
    return blockers


def run_nc10(output_dir: Path = DEFAULT_OUTPUT_DIR, doc_path: Path = DOC_PATH) -> dict[str, Any]:
    blockers: list[str] = []
    nc8_payload, nc8_status, nc8_errors = load_expected_summary(
        "NC8 本地安装备份更新回滚",
        NC8_SUMMARY,
        {"local_install_backup_update_rollback_hardened_pg_script_ready"},
    )
    blockers.extend(nc8_errors)

    required_files = [
        LOCAL_BACKUPS_SERVICE,
        LOCAL_BACKUPS_API,
        LOCAL_BACKUPS_SCHEMA,
        LOCAL_MAINTENANCE_SERVICE,
        LOCAL_BACKUPS_TEST,
        POSTGRES_BACKUP_SCRIPT,
    ]
    for path in required_files:
        if not path.exists():
            blockers.append(f"NC10 必需文件缺失：{display_path(path)}")

    blockers.extend(_missing_markers(LOCAL_BACKUPS_SERVICE, SERVICE_MARKERS, "本地备份服务"))
    blockers.extend(_missing_markers(LOCAL_BACKUPS_API, API_MARKERS, "本地备份 API"))
    blockers.extend(_missing_markers(LOCAL_BACKUPS_SCHEMA, SCHEMA_MARKERS, "本地备份 schema"))
    blockers.extend(_missing_markers(LOCAL_MAINTENANCE_SERVICE, MAINTENANCE_MARKERS, "本地维护总账"))
    blockers.extend(_missing_markers(LOCAL_BACKUPS_TEST, TEST_MARKERS, "本地备份测试"))
    blockers.extend(_missing_markers(POSTGRES_BACKUP_SCRIPT, SCRIPT_MARKERS, "PostgreSQL 备份演练脚本"))
    blockers.extend(_scan_overclaims(required_files))

    postgres_manifest = _latest_postgres_manifest()
    if postgres_manifest["present"]:
        if postgres_manifest.get("status") != "postgres_backup_restore_readability_dry_run_ready":
            blockers.append(f"PostgreSQL 备份 manifest 状态异常：{postgres_manifest.get('status')}")
        if postgres_manifest.get("live_restore_performed") is not False:
            blockers.append("PostgreSQL 备份 manifest 未明确 live_restore_performed=false")
        if postgres_manifest.get("database_replaced") is not False:
            blockers.append("PostgreSQL 备份 manifest 未明确 database_replaced=false")

    status = (
        "postgres_backup_evidence_registration_ready_with_customer_pg_manifest"
        if postgres_manifest["present"] and not blockers
        else "postgres_backup_evidence_registration_ready_waiting_customer_pg_run"
    )
    result = base_result(SCHEMA_VERSION, PHASE, status, blockers)
    result["upstreams"] = {"nc8": nc8_status}
    result["readiness"] = {
        "postgres_manifest_registration_api_ready": not _missing_markers(LOCAL_BACKUPS_API, API_MARKERS, "本地备份 API"),
        "postgres_manifest_service_validation_ready": not _missing_markers(
            LOCAL_BACKUPS_SERVICE, SERVICE_MARKERS, "本地备份服务"
        ),
        "local_maintenance_counts_postgres_registration_audit": not _missing_markers(
            LOCAL_MAINTENANCE_SERVICE, MAINTENANCE_MARKERS, "本地维护总账"
        ),
        "customer_machine_pg_dry_run_manifest_present": bool(postgres_manifest["present"]),
        "signed_update_apply_can_use_registered_pg_evidence": "last_restore_dry_run" in _text(LOCAL_BACKUPS_SERVICE),
        "live_restore_performed": False,
        "database_replaced": False,
        "backup_file_body_stored_by_api": False,
    }
    result["postgres_dry_run_manifest"] = postgres_manifest
    result["implementation_notes"] = [
        "新增 PostgreSQL 备份 dry-run manifest 登记接口，只登记 manifest，不保存 dump 文件本体。",
        "登记时校验 pg_dump、pg_restore --list、未真实恢复、未替换数据库、未开启真实外发和 worker。",
        "登记后写入 LocalBackupRecord，并生成 last_restore_dry_run 摘要，供签名更新 apply 备份门禁复用。",
        "本地维护总账已纳入 postgres_dry_run_manifest_registered 审计事件。",
    ]
    result["remaining_risks"] = [
        "当前未在客户 Docker 环境实际运行 pg_dump/pg_restore --list，因此仍等待客户机 PG 备份演练 manifest。",
        "真实恢复工具、停机窗口、恢复前二次备份和客户管理员确认仍未产品化为可执行恢复流程。",
        "正式签名安装包、真实外发、真实渠道和生产 SLA 仍未完成。",
    ]

    output_dir.mkdir(parents=True, exist_ok=True)
    write_json(output_dir / "summary.json", result)
    write_markdown_report(
        doc_path,
        "P3-06U-26 H2W-NC10 PostgreSQL 备份证据登记",
        result,
        [
            ("本轮补强", result["implementation_notes"]),
            ("PostgreSQL manifest 状态", [f"{key}: {value}" for key, value in postgres_manifest.items()]),
            ("剩余风险", result["remaining_risks"]),
        ],
    )
    return result


def main() -> None:
    result = run_nc10()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result["blockers"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
