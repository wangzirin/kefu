#!/usr/bin/env bash
set -euo pipefail
umask 077

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
DEFAULT_ENV_FILE="$SCRIPT_DIR/customer.env"
TEMPLATE_ENV_FILE="$SCRIPT_DIR/customer.env.example"
TIMESTAMP="$(date -u +"%Y%m%dT%H%M%SZ")"
OUTPUT_ROOT="${WANFA_POSTGRES_BACKUP_DRY_RUN_DIR:-$ROOT_DIR/output/p3_06u_26h2w_nc8_postgres_backup_dry_run}"
RUN_DIR="$OUTPUT_ROOT/$TIMESTAMP"

if [[ $# -gt 0 ]]; then
  ENV_FILE="$1"
elif [[ -f "$DEFAULT_ENV_FILE" ]]; then
  ENV_FILE="$DEFAULT_ENV_FILE"
else
  ENV_FILE="$TEMPLATE_ENV_FILE"
fi

if [[ ! -f "$ENV_FILE" ]]; then
  echo "PostgreSQL 备份演练阻断：未找到客户本地环境文件：$ENV_FILE" >&2
  echo "请先复制 deploy/customer.env.example 为 deploy/customer.env，并填写本地随机数据库密码。" >&2
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
    echo "PostgreSQL 备份演练阻断：${key} 必须为 ${expected}。" >&2
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
    echo "PostgreSQL 备份演练阻断：请先把 deploy/customer.env 里的数据库密码替换为客户本地随机密码。" >&2
    echo "仅做内部 rehearsal 时，可临时设置 WANFA_ALLOW_TEMPLATE_PASSWORD_FOR_REHEARSAL=true。" >&2
    exit 1
  fi
fi

if ! command -v docker >/dev/null 2>&1; then
  echo "PostgreSQL 备份演练阻断：未找到 Docker。请先安装并启动 Docker Desktop。" >&2
  exit 1
fi

if ! docker info >/dev/null 2>&1; then
  echo "PostgreSQL 备份演练阻断：Docker daemon 不可用。请先启动 Docker Desktop。" >&2
  exit 1
fi

if ! docker compose version >/dev/null 2>&1; then
  echo "PostgreSQL 备份演练阻断：Docker Compose 不可用。" >&2
  exit 1
fi

POSTGRES_DB="$(get_env_value "STANDARD_OPS_POSTGRES_DB")"
POSTGRES_USER="$(get_env_value "STANDARD_OPS_POSTGRES_USER")"
POSTGRES_DB="${POSTGRES_DB:-wanfa_ops}"
POSTGRES_USER="${POSTGRES_USER:-wanfa_ops}"

COMPOSE=(
  docker compose
  --env-file "$ENV_FILE"
  -f "$ROOT_DIR/deploy/docker-compose.yml"
  -f "$ROOT_DIR/deploy/docker-compose.pilot.yml"
)

echo "正在检查本地试点 compose 配置..."
"${COMPOSE[@]}" config --quiet

echo "正在检查 PostgreSQL readiness..."
"${COMPOSE[@]}" exec -T postgres pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB" >/dev/null

mkdir -p "$RUN_DIR"
DUMP_FILE="$RUN_DIR/postgres.dump"
RESTORE_LIST_FILE="$RUN_DIR/pg_restore_list.txt"
MANIFEST_FILE="$RUN_DIR/manifest.json"

echo "正在导出 PostgreSQL 自定义格式备份..."
"${COMPOSE[@]}" exec -T postgres pg_dump -Fc -U "$POSTGRES_USER" -d "$POSTGRES_DB" > "$DUMP_FILE"

if [[ ! -s "$DUMP_FILE" ]]; then
  echo "PostgreSQL 备份演练阻断：备份文件为空。" >&2
  exit 1
fi

echo "正在校验备份文件可被 pg_restore 读取..."
cat "$DUMP_FILE" | "${COMPOSE[@]}" exec -T postgres sh -c \
  'cat > /tmp/wanfa-nc8-backup-check.dump && pg_restore --list /tmp/wanfa-nc8-backup-check.dump && rm -f /tmp/wanfa-nc8-backup-check.dump' \
  > "$RESTORE_LIST_FILE"

BACKUP_SHA="$(shasum -a 256 "$DUMP_FILE" | awk '{print $1}')"
BACKUP_SIZE="$(wc -c < "$DUMP_FILE" | tr -d '[:space:]')"
RESTORE_LIST_SIZE="$(wc -c < "$RESTORE_LIST_FILE" | tr -d '[:space:]')"

cat > "$MANIFEST_FILE" <<JSON
{
  "schema_version": "p3-06u-26h2w-nc8.postgres_backup_dry_run.v1",
  "created_at": "$TIMESTAMP",
  "status": "postgres_backup_restore_readability_dry_run_ready",
  "backup_file": "postgres.dump",
  "backup_sha256": "$BACKUP_SHA",
  "backup_size_bytes": $BACKUP_SIZE,
  "restore_list_file": "pg_restore_list.txt",
  "restore_list_size_bytes": $RESTORE_LIST_SIZE,
  "pg_dump_completed": true,
  "pg_restore_list_completed": true,
  "live_restore_performed": false,
  "database_replaced": false,
  "program_files_replaced": false,
  "external_write_enabled": false,
  "trusted_inbound_worker_enabled": false,
  "manual_restore_window_required": true,
  "customer_admin_confirmation_required": true,
  "next_step": "如需真实恢复，必须先停服务、创建恢复前备份、由客户管理员确认维护窗口，再按单独恢复 SOP 执行。"
}
JSON

echo "PostgreSQL 备份演练完成：$RUN_DIR"
echo "已生成备份文件和 pg_restore 可读性清单；未执行真实恢复、未替换数据库、未开启真实外发。"
