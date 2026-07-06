#!/usr/bin/env bash
set -euo pipefail
umask 077

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
DEFAULT_ENV_FILE="$SCRIPT_DIR/customer.env"
TEMPLATE_ENV_FILE="$SCRIPT_DIR/customer.env.example"
TIMESTAMP="$(date -u +"%Y%m%d%H%M%S")"
OUTPUT_ROOT="${WANFA_POSTGRES_FORMAL_RESTORE_DRY_RUN_DIR:-$ROOT_DIR/output/p3_06u_26h2w_nc14_formal_restore_execution_dry_run}"
RUN_DIR="$OUTPUT_ROOT/$TIMESTAMP"

if [[ $# -gt 0 ]]; then
  ENV_FILE="$1"
elif [[ -f "$DEFAULT_ENV_FILE" ]]; then
  ENV_FILE="$DEFAULT_ENV_FILE"
else
  ENV_FILE="$TEMPLATE_ENV_FILE"
fi

if [[ $# -gt 1 ]]; then
  BACKUP_RUN_DIR="$2"
else
  BACKUP_RUN_DIR="${WANFA_POSTGRES_BACKUP_RUN_DIR:-}"
fi

if [[ ! -f "$ENV_FILE" ]]; then
  echo "PostgreSQL 正式恢复执行 dry-run 阻断：未找到客户本地环境文件：$ENV_FILE" >&2
  echo "请先复制 deploy/customer.env.example 为 deploy/customer.env，并填写本地随机数据库密码。" >&2
  exit 1
fi

if [[ -z "$BACKUP_RUN_DIR" || ! -d "$BACKUP_RUN_DIR" ]]; then
  echo "PostgreSQL 正式恢复执行 dry-run 阻断：请通过第二个参数或 WANFA_POSTGRES_BACKUP_RUN_DIR 指向 NC8 备份演练目录。" >&2
  echo "示例：deploy/postgres-formal-restore-dry-run.sh deploy/customer.env output/p3_06u_26h2w_nc8_postgres_backup_dry_run/20260706120000" >&2
  exit 1
fi

BACKUP_MANIFEST="$BACKUP_RUN_DIR/manifest.json"
DUMP_FILE="$BACKUP_RUN_DIR/postgres.dump"
if [[ ! -f "$BACKUP_MANIFEST" || ! -s "$DUMP_FILE" ]]; then
  echo "PostgreSQL 正式恢复执行 dry-run 阻断：备份目录必须包含 manifest.json 和 postgres.dump。" >&2
  exit 1
fi

get_env_value() {
  local key="$1"
  local value
  value="$(grep -E "^[[:space:]]*${key}=" "$ENV_FILE" | tail -n 1 | cut -d '=' -f 2- || true)"
  value="${value#"${value%%[![:space:]]*}"}"
  value="${value%"${value##*[![:space:]]}"}"
  value="${value%\"}"
  value="${value#\"}"
  value="${value%\'}"
  value="${value#\'}"
  printf '%s' "$value"
}

require_value() {
  local key="$1"
  local expected="$2"
  local actual
  actual="$(get_env_value "$key")"
  if [[ "$actual" != "$expected" ]]; then
    echo "PostgreSQL 正式恢复执行 dry-run 阻断：${key} 必须为 ${expected}。" >&2
    exit 1
  fi
}

require_value "STANDARD_OPS_DEV_BOOTSTRAP_ENABLED" "false"
require_value "OUTBOX_EXTERNAL_WRITE_ENABLED" "false"
require_value "TRUSTED_INBOUND_WORKER_ENABLED" "false"
require_value "KNOWLEDGE_VECTOR_STORE" "postgres_pgvector_store_v1"

POSTGRES_PASSWORD="$(get_env_value "STANDARD_OPS_POSTGRES_PASSWORD")"
DATABASE_URL_VALUE="$(get_env_value "DATABASE_URL")"
if [[ "$POSTGRES_PASSWORD" == "replace-with-local-random-password" || "$DATABASE_URL_VALUE" == *"replace-with-local-random-password"* ]]; then
  if [[ "${WANFA_ALLOW_TEMPLATE_PASSWORD_FOR_REHEARSAL:-false}" != "true" ]]; then
    echo "PostgreSQL 正式恢复执行 dry-run 阻断：请先把 deploy/customer.env 里的数据库密码替换为客户本地随机密码。" >&2
    echo "仅做内部 rehearsal 时，可临时设置 WANFA_ALLOW_TEMPLATE_PASSWORD_FOR_REHEARSAL=true。" >&2
    exit 1
  fi
fi

BACKUP_SHA="$(python3 - "$BACKUP_MANIFEST" <<'PY'
import json
import sys
payload = json.load(open(sys.argv[1], encoding="utf-8"))
print(payload.get("backup_sha256", ""))
PY
)"
ACTUAL_SHA="$(shasum -a 256 "$DUMP_FILE" | awk '{print $1}')"
if [[ "$BACKUP_SHA" != "$ACTUAL_SHA" ]]; then
  echo "PostgreSQL 正式恢复执行 dry-run 阻断：postgres.dump sha256 与 NC8 manifest 不一致。" >&2
  exit 1
fi

mkdir -p "$RUN_DIR"
MANIFEST_FILE="$RUN_DIR/manifest.json"

python3 - "$MANIFEST_FILE" "$BACKUP_SHA" <<'PY'
import hashlib
import json
import sys
from datetime import datetime, timezone

manifest_file, backup_sha = sys.argv[1:3]
command_intents = [
    "create_fresh_pre_restore_backup",
    "stop_application_and_workers",
    "restore_registered_backup_to_target_database",
    "run_post_restore_health_checks",
    "rollback_from_fresh_backup_if_failed",
]
payload = {
    "schema_version": "p3-06u-26h2w-nc14.formal_restore_execution_dry_run.v1",
    "created_at": datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
    "status": "formal_restore_execution_dry_run_ready",
    "restore_mode": "formal_restore_execution_dry_run_only",
    "backup_sha256": backup_sha,
    "restore_commands_rendered_not_executed": True,
    "restore_command_preview_hashes": [
        hashlib.sha256(item.encode("utf-8")).hexdigest() for item in command_intents
    ],
    "restore_command_preview_stored": False,
    "final_operator_confirmation_required": True,
    "service_stop_required": True,
    "fresh_pre_restore_backup_required": True,
    "post_restore_health_check_required": True,
    "rollback_plan_required": True,
    "manual_restore_window_required": True,
    "live_restore_performed": False,
    "database_replaced": False,
    "program_files_replaced": False,
    "external_write_enabled": False,
    "trusted_inbound_worker_enabled": False,
    "real_platform_send_enabled": False,
    "commands_executed_on_live_database": False,
    "pg_restore_executed_on_live_database": False,
    "automatic_restore_enabled": False,
    "backup_file_body_stored": False,
    "raw_restore_command_stored": False,
    "next_step": (
        "将本 manifest 登记到系统；真实恢复仍需单独停机窗口、恢复前二次备份、"
        "最终操作员确认、恢复后健康检查和失败回滚。"
    ),
}
with open(manifest_file, "w", encoding="utf-8") as handle:
    json.dump(payload, handle, ensure_ascii=False, indent=2)
PY

echo "PostgreSQL 正式恢复执行 dry-run manifest 已生成：$RUN_DIR"
echo "仅生成执行计划证据和命令哈希；未执行 pg_restore、未替换真实数据库、未开启真实外发。"
