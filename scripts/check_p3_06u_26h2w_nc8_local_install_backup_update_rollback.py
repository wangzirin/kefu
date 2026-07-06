#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from lib.h2w_pack8_common import ROOT, base_result, display_path, scan_text_file, write_json, write_markdown_report


PHASE = "H2W-NC8"
SCHEMA_VERSION = "p3-06u-26h2w-nc8.local_install_backup_update_rollback.v1"
DEFAULT_OUTPUT_DIR = ROOT / "output/p3_06u_26h2w_nc8_local_install_backup_update_rollback"
DOC_PATH = ROOT / "docs/P3-06U-26H2W_NC8_LOCAL_INSTALL_BACKUP_UPDATE_ROLLBACK.md"

START_SCRIPT = ROOT / "deploy/start-local-pilot.sh"
POSTGRES_BACKUP_SCRIPT = ROOT / "deploy/postgres-backup-dry-run.sh"
SIGNED_UPDATES_SERVICE = ROOT / "backend/app/services/signed_updates.py"
SIGNED_UPDATES_TEST = ROOT / "backend/tests/test_signed_update_packages_api.py"
LOCAL_BACKUPS_SERVICE = ROOT / "backend/app/services/local_backups.py"
INSTALLER_VERSION = ROOT / "installers/VERSION.json"
PG_DRY_RUN_OUTPUT_ROOT = ROOT / "output/p3_06u_26h2w_nc8_postgres_backup_dry_run"

START_SCRIPT_MARKERS = [
    "docker info",
    "docker compose version",
    "check_disk_space",
    "check_port_available",
    "pg_isready",
    "alembic -c alembic.ini current",
    'require_value "OUTBOX_EXTERNAL_WRITE_ENABLED" "false"',
    'require_value "TRUSTED_INBOUND_WORKER_ENABLED" "false"',
    'require_value "KNOWLEDGE_VECTOR_STORE" "postgres_pgvector_store_v1"',
]

POSTGRES_BACKUP_SCRIPT_MARKERS = [
    "p3-06u-26h2w-nc8.postgres_backup_dry_run.v1",
    "pg_dump -Fc",
    "pg_restore --list",
    '"live_restore_performed": false',
    '"database_replaced": false',
    '"external_write_enabled": false',
    '"trusted_inbound_worker_enabled": false',
    "manual_restore_window_required",
]

SIGNED_UPDATE_MARKERS = [
    "_require_verified_local_backup_before_apply",
    "verified local backup and restore dry-run evidence",
    "LocalBackupRecord.status == \"verified\"",
    "database_file_replaced",
    "signed_update_package.rolled_back",
    "signed_update_package.strategy_rolled_back",
]

SIGNED_UPDATE_TEST_MARKERS = [
    "test_apply_signed_update_requires_verified_backup_restore_dry_run",
    "_insert_verified_local_backup_restore_dry_run",
    "尝试绕过备份应用签名知识包",
    "verified local backup and restore dry-run evidence",
]

LOCAL_BACKUP_MARKERS = [
    "local_backup.restore_dry_run_created",
    '"can_restore_now": False',
    '"database_file_replaced": False',
    '"requires_fresh_pre_restore_backup": True',
    "真实恢复前必须先对当前数据库再创建一个新的物理备份点",
]

FORBIDDEN_BACKUP_SCRIPT_PATTERNS = [
    ("执行真实恢复", re.compile(r"pg_restore\s+[^\\n|&;]*\s-d\s", re.IGNORECASE)),
    ("直接执行 psql 恢复", re.compile(r"psql\s+[^\\n|&;]*\s(-f|<)", re.IGNORECASE)),
    ("删除数据库卷", re.compile(r"docker\s+volume\s+rm|down\s+-v", re.IGNORECASE)),
]

OVERCLAIM_PHRASES = [
    "正式签名安装包已完成",
    "签名 dmg/exe 已完成",
    "真实外发已接通",
    "PostgreSQL 真实恢复已完成",
    "自动静默更新已完成",
    "远控客户电脑已完成",
]


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def _missing_markers(path: Path, markers: list[str], label: str) -> list[str]:
    text = _text(path)
    return [f"{label} 缺少门禁标记：{marker}" for marker in markers if marker not in text]


def _latest_postgres_dry_run_manifest(root: Path) -> dict[str, Any]:
    manifests = sorted(root.glob("*/manifest.json"), key=lambda item: item.stat().st_mtime, reverse=True)
    if not manifests:
        return {
            "executed": False,
            "manifest_path": "",
            "status": "not_executed_in_this_workspace",
        }
    path = manifests[0]
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {
            "executed": True,
            "manifest_path": display_path(path),
            "status": "invalid_json",
        }
    return {
        "executed": True,
        "manifest_path": display_path(path),
        "status": payload.get("status", "missing_status"),
        "live_restore_performed": payload.get("live_restore_performed"),
        "database_replaced": payload.get("database_replaced"),
        "pg_dump_completed": payload.get("pg_dump_completed"),
        "pg_restore_list_completed": payload.get("pg_restore_list_completed"),
        "backup_size_bytes": payload.get("backup_size_bytes"),
    }


def _scan_overclaims(paths: list[Path]) -> list[str]:
    blockers: list[str] = []
    for path in paths:
        if not path.exists():
            continue
        text = _text(path)
        for phrase in OVERCLAIM_PHRASES:
            if phrase in text:
                blockers.append(f"{display_path(path)} 出现 NC8 越界表述：{phrase}")
        blockers.extend(scan_text_file(path))
    return blockers


def run_nc8(output_dir: Path = DEFAULT_OUTPUT_DIR, doc_path: Path = DOC_PATH) -> dict[str, Any]:
    blockers: list[str] = []
    required_files = [
        START_SCRIPT,
        POSTGRES_BACKUP_SCRIPT,
        SIGNED_UPDATES_SERVICE,
        SIGNED_UPDATES_TEST,
        LOCAL_BACKUPS_SERVICE,
        INSTALLER_VERSION,
    ]
    for path in required_files:
        if not path.exists():
            blockers.append(f"NC8 必需文件缺失：{display_path(path)}")

    blockers.extend(_missing_markers(START_SCRIPT, START_SCRIPT_MARKERS, "客户本地启动脚本"))
    blockers.extend(_missing_markers(POSTGRES_BACKUP_SCRIPT, POSTGRES_BACKUP_SCRIPT_MARKERS, "PostgreSQL 备份演练脚本"))
    blockers.extend(_missing_markers(SIGNED_UPDATES_SERVICE, SIGNED_UPDATE_MARKERS, "签名更新服务"))
    blockers.extend(_missing_markers(SIGNED_UPDATES_TEST, SIGNED_UPDATE_TEST_MARKERS, "签名更新测试"))
    blockers.extend(_missing_markers(LOCAL_BACKUPS_SERVICE, LOCAL_BACKUP_MARKERS, "本地备份服务"))

    backup_script_text = _text(POSTGRES_BACKUP_SCRIPT)
    for label, pattern in FORBIDDEN_BACKUP_SCRIPT_PATTERNS:
        if pattern.search(backup_script_text):
            blockers.append(f"PostgreSQL 备份演练脚本包含危险恢复动作：{label}")

    postgres_dry_run = _latest_postgres_dry_run_manifest(PG_DRY_RUN_OUTPUT_ROOT)
    if postgres_dry_run.get("executed"):
        if postgres_dry_run.get("status") != "postgres_backup_restore_readability_dry_run_ready":
            blockers.append(f"PostgreSQL 备份演练 manifest 状态异常：{postgres_dry_run.get('status')}")
        if postgres_dry_run.get("live_restore_performed") is not False:
            blockers.append("PostgreSQL 备份演练 manifest 未明确 live_restore_performed=false")
        if postgres_dry_run.get("database_replaced") is not False:
            blockers.append("PostgreSQL 备份演练 manifest 未明确 database_replaced=false")

    blockers.extend(_scan_overclaims([START_SCRIPT, POSTGRES_BACKUP_SCRIPT, SIGNED_UPDATES_SERVICE, LOCAL_BACKUPS_SERVICE]))

    result = base_result(
        SCHEMA_VERSION,
        PHASE,
        "local_install_backup_update_rollback_hardened_pg_script_ready",
        blockers,
    )
    result["readiness"] = {
        "startup_preflight_hardened": not _missing_markers(START_SCRIPT, START_SCRIPT_MARKERS, "客户本地启动脚本"),
        "postgres_backup_dry_run_script_ready": not _missing_markers(
            POSTGRES_BACKUP_SCRIPT, POSTGRES_BACKUP_SCRIPT_MARKERS, "PostgreSQL 备份演练脚本"
        ),
        "postgres_backup_dry_run_executed_in_workspace": bool(postgres_dry_run.get("executed")),
        "signed_update_apply_requires_backup": not _missing_markers(
            SIGNED_UPDATES_SERVICE, SIGNED_UPDATE_MARKERS, "签名更新服务"
        ),
        "rollback_audit_required": "signed_update_package.rolled_back" in _text(SIGNED_UPDATES_SERVICE)
        and "signed_update_package.strategy_rolled_back" in _text(SIGNED_UPDATES_SERVICE),
        "signed_dmg_exe_ready": False,
        "real_platform_send_ready": False,
    }
    result["postgres_dry_run_manifest"] = postgres_dry_run
    result["implementation_notes"] = [
        "启动脚本已增加 Docker daemon、compose、磁盘、端口、DB readiness、迁移 head 与安全开关检查。",
        "新增 PostgreSQL pg_dump/pg_restore --list 备份可读性演练脚本；该脚本不执行真实恢复。",
        "签名知识包/策略包 apply 前必须存在已验证备份和恢复 dry-run 证据。",
        "程序更新仍只支持 dry-run 计划，不替换程序文件、不执行迁移、不重启服务。",
    ]
    result["remaining_risks"] = [
        "PostgreSQL 备份 dry-run 脚本需要在客户本机 Docker 环境实际运行后，才能生成客户现场备份证据。",
        "当前服务端本地备份 API 仍以 SQLite rehearsal 为主；PostgreSQL 物理备份证据登记需要后续继续产品化。",
        "macOS/Windows 仍是启动候选体验，不是签名 dmg/exe 安装器。",
    ]

    output_dir.mkdir(parents=True, exist_ok=True)
    write_json(output_dir / "summary.json", result)
    write_markdown_report(
        doc_path,
        "P3-06U-26 H2W-NC8 本地安装、备份、更新与回滚补强",
        result,
        [
            ("本轮补强", result["implementation_notes"]),
            ("PostgreSQL 备份演练", [f"{k}: {v}" for k, v in postgres_dry_run.items()]),
            ("剩余风险", result["remaining_risks"]),
        ],
    )
    return result


def main() -> None:
    result = run_nc8()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result["blockers"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
