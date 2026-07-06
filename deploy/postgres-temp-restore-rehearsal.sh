#!/usr/bin/env bash
set -euo pipefail
umask 077

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
DEFAULT_ENV_FILE="$SCRIPT_DIR/customer.env"
TEMPLATE_ENV_FILE="$SCRIPT_DIR/customer.env.example"
TIMESTAMP="$(date -u +"%Y%m%d%H%M%S")"
OUTPUT_ROOT="${WANFA_POSTGRES_TEMP_RESTORE_REHEARSAL_DIR:-$ROOT_DIR/output/p3_06u_26h2w_nc12_postgres_temp_restore_rehearsal}"
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
  echo "PostgreSQL 临时库恢复演练阻断：未找到客户本地环境文件：$ENV_FILE" >&2
  echo "请先复制 deploy/customer.env.example 为 deploy/customer.env，并填写本地随机数据库密码。" >&2
  exit 1
fi

if [[ -z "$BACKUP_RUN_DIR" || ! -d "$BACKUP_RUN_DIR" ]]; then
  echo "PostgreSQL 临时库恢复演练阻断：请通过第二个参数或 WANFA_POSTGRES_BACKUP_RUN_DIR 指向 NC8 备份演练目录。" >&2
  echo "示例：deploy/postgres-temp-restore-rehearsal.sh deploy/customer.env output/p3_06u_26h2w_nc8_postgres_backup_dry_run/20260706120000" >&2
  exit 1
fi

BACKUP_MANIFEST="$BACKUP_RUN_DIR/manifest.json"
DUMP_FILE="$BACKUP_RUN_DIR/postgres.dump"
if [[ ! -f "$BACKUP_MANIFEST" || ! -s "$DUMP_FILE" ]]; then
  echo "PostgreSQL 临时库恢复演练阻断：备份目录必须包含 manifest.json 和 postgres.dump。" >&2
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
    echo "PostgreSQL 临时库恢复演练阻断：${key} 必须为 ${expected}。" >&2
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
    echo "PostgreSQL 临时库恢复演练阻断：请先把 deploy/customer.env 里的数据库密码替换为客户本地随机密码。" >&2
    echo "仅做内部 rehearsal 时，可临时设置 WANFA_ALLOW_TEMPLATE_PASSWORD_FOR_REHEARSAL=true。" >&2
    exit 1
  fi
fi

if ! command -v docker >/dev/null 2>&1; then
  echo "PostgreSQL 临时库恢复演练阻断：未找到 Docker。请先安装并启动 Docker Desktop。" >&2
  exit 1
fi

if ! docker info >/dev/null 2>&1; then
  echo "PostgreSQL 临时库恢复演练阻断：Docker daemon 不可用。请先启动 Docker Desktop。" >&2
  exit 1
fi

if ! docker compose version >/dev/null 2>&1; then
  echo "PostgreSQL 临时库恢复演练阻断：Docker Compose 不可用。" >&2
  exit 1
fi

POSTGRES_DB="$(get_env_value "STANDARD_OPS_POSTGRES_DB")"
POSTGRES_USER="$(get_env_value "STANDARD_OPS_POSTGRES_USER")"
POSTGRES_DB="${POSTGRES_DB:-wanfa_ops}"
POSTGRES_USER="${POSTGRES_USER:-wanfa_ops}"
TEMP_DATABASE_NAME="${WANFA_TEMP_RESTORE_DATABASE:-wanfa_restore_tmp_${TIMESTAMP}_$((RANDOM + 10000))}"
TEMP_DATABASE_NAME="$(printf '%s' "$TEMP_DATABASE_NAME" | tr '[:upper:]' '[:lower:]')"

if [[ ! "$TEMP_DATABASE_NAME" =~ ^wanfa_restore_tmp_[a-z0-9_]{8,64}$ ]]; then
  echo "PostgreSQL 临时库恢复演练阻断：临时库名必须以 wanfa_restore_tmp_ 开头，且只包含小写字母、数字和下划线。" >&2
  exit 1
fi

case "$TEMP_DATABASE_NAME" in
  *prod*|*production*|*live*|*current*|*customer*|*main*|*wanfa_ops*)
    echo "PostgreSQL 临时库恢复演练阻断：临时库名包含正式库风险词。" >&2
    exit 1
    ;;
esac

if [[ "$TEMP_DATABASE_NAME" == "$POSTGRES_DB" ]]; then
  echo "PostgreSQL 临时库恢复演练阻断：临时库名不能等于当前业务库。" >&2
  exit 1
fi

COMPOSE=(
  docker compose
  --env-file "$ENV_FILE"
  -f "$ROOT_DIR/deploy/docker-compose.yml"
  -f "$ROOT_DIR/deploy/docker-compose.pilot.yml"
)

BACKUP_SHA="$(python3 - "$BACKUP_MANIFEST" <<'PY'
import json
import sys
payload = json.load(open(sys.argv[1], encoding="utf-8"))
print(payload.get("backup_sha256", ""))
PY
)"
ACTUAL_SHA="$(shasum -a 256 "$DUMP_FILE" | awk '{print $1}')"
if [[ "$BACKUP_SHA" != "$ACTUAL_SHA" ]]; then
  echo "PostgreSQL 临时库恢复演练阻断：postgres.dump sha256 与 manifest 不一致。" >&2
  exit 1
fi

echo "正在检查本地试点 compose 配置..."
"${COMPOSE[@]}" config --quiet

echo "正在检查 PostgreSQL readiness..."
"${COMPOSE[@]}" exec -T postgres pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB" >/dev/null

existing="$("${COMPOSE[@]}" exec -T postgres psql -U "$POSTGRES_USER" -d postgres -Atc "SELECT 1 FROM pg_database WHERE datname = '$TEMP_DATABASE_NAME'" | tr -d '[:space:]')"
if [[ "$existing" == "1" ]]; then
  echo "PostgreSQL 临时库恢复演练阻断：临时库已存在，请换一个 WANFA_TEMP_RESTORE_DATABASE。" >&2
  exit 1
fi

TEMP_CREATED="false"
cleanup_temp_database() {
  if [[ "$TEMP_CREATED" == "true" ]]; then
    "${COMPOSE[@]}" exec -T postgres dropdb -U "$POSTGRES_USER" --if-exists "$TEMP_DATABASE_NAME" >/dev/null 2>&1 || true
  fi
}
trap cleanup_temp_database EXIT

mkdir -p "$RUN_DIR"
RESTORE_LOG="$RUN_DIR/pg_restore_temp.log"
HEALTH_LOG="$RUN_DIR/health_checks.txt"
MANIFEST_FILE="$RUN_DIR/manifest.json"

echo "正在创建临时 PostgreSQL 数据库：$TEMP_DATABASE_NAME"
"${COMPOSE[@]}" exec -T postgres createdb -U "$POSTGRES_USER" "$TEMP_DATABASE_NAME"
TEMP_CREATED="true"

echo "正在把备份恢复到临时库..."
cat "$DUMP_FILE" | "${COMPOSE[@]}" exec -T postgres sh -c \
  "cat > /tmp/wanfa-nc12-temp-restore.dump && pg_restore --clean --if-exists --no-owner --no-privileges -U '$POSTGRES_USER' -d '$TEMP_DATABASE_NAME' /tmp/wanfa-nc12-temp-restore.dump && rm -f /tmp/wanfa-nc12-temp-restore.dump" \
  > "$RESTORE_LOG" 2>&1

echo "正在执行临时库健康检查..."
"${COMPOSE[@]}" exec -T postgres psql -U "$POSTGRES_USER" -d "$TEMP_DATABASE_NAME" -Atc "SELECT 1;" > "$HEALTH_LOG"
RESTORED_TABLE_COUNT="$("${COMPOSE[@]}" exec -T postgres psql -U "$POSTGRES_USER" -d "$TEMP_DATABASE_NAME" -Atc "SELECT count(*) FROM information_schema.tables WHERE table_schema NOT IN ('pg_catalog','information_schema');" | tr -d '[:space:]')"
if [[ -z "$RESTORED_TABLE_COUNT" || "$RESTORED_TABLE_COUNT" == "0" ]]; then
  echo "PostgreSQL 临时库恢复演练阻断：临时库没有可见业务表。" >&2
  exit 1
fi

echo "正在删除临时 PostgreSQL 数据库..."
"${COMPOSE[@]}" exec -T postgres dropdb -U "$POSTGRES_USER" "$TEMP_DATABASE_NAME"
TEMP_CREATED="false"

python3 - "$MANIFEST_FILE" "$BACKUP_SHA" "$TEMP_DATABASE_NAME" "$RESTORED_TABLE_COUNT" <<'PY'
import json
import sys
from datetime import datetime, timezone

manifest_file, backup_sha, temp_database_name, restored_table_count = sys.argv[1:5]
payload = {
    "schema_version": "p3-06u-26h2w-nc12.postgres_temp_restore_rehearsal.v1",
    "created_at": datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
    "status": "postgres_temp_restore_rehearsal_ready",
    "restore_mode": "temporary_database_rehearsal_only",
    "backup_sha256": backup_sha,
    "temp_database_name": temp_database_name,
    "temp_database_created": True,
    "pg_restore_into_temp_completed": True,
    "health_checks_completed": True,
    "temp_database_dropped": True,
    "restored_table_count": int(restored_table_count),
    "health_check_count": 5,
    "live_restore_performed": False,
    "live_database_replaced": False,
    "database_replaced": False,
    "program_files_replaced": False,
    "external_write_enabled": False,
    "trusted_inbound_worker_enabled": False,
    "commands_executed_on_live_database": False,
    "backup_file_body_stored": False,
    "next_step": "将本 manifest 登记到系统；正式恢复仍需维护窗口、恢复前二次备份、客户管理员确认和回滚路径。",
}
with open(manifest_file, "w", encoding="utf-8") as handle:
    json.dump(payload, handle, ensure_ascii=False, indent=2)
PY

echo "PostgreSQL 临时库恢复演练完成：$RUN_DIR"
echo "已恢复到临时库、完成健康检查并删除临时库；未替换真实数据库、未开启真实外发。"
