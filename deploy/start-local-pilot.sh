#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
DEFAULT_ENV_FILE="$SCRIPT_DIR/customer.env"
TEMPLATE_ENV_FILE="$SCRIPT_DIR/customer.env.example"

if [[ $# -gt 0 ]]; then
  ENV_FILE="$1"
elif [[ -f "$DEFAULT_ENV_FILE" ]]; then
  ENV_FILE="$DEFAULT_ENV_FILE"
else
  ENV_FILE="$TEMPLATE_ENV_FILE"
fi

if [[ ! -f "$ENV_FILE" ]]; then
  echo "未找到客户本地环境文件：$ENV_FILE" >&2
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
    echo "启动被阻断：${key} 必须为 ${expected}。" >&2
    exit 1
  fi
}

require_empty() {
  local key="$1"
  local actual
  actual="$(get_env_value "$key")"
  if [[ -n "$actual" ]]; then
    echo "启动被阻断：${key} 必须为空。首任负责人必须通过本地界面创建，不能预置默认密码。" >&2
    exit 1
  fi
}

require_command() {
  local command_name="$1"
  local install_hint="$2"
  if ! command -v "$command_name" >/dev/null 2>&1; then
    echo "启动被阻断：未找到 ${command_name}。${install_hint}" >&2
    exit 1
  fi
}

check_disk_space() {
  local required_kb="${WANFA_MIN_FREE_DISK_KB:-2097152}"
  local available_kb
  available_kb="$(df -Pk "$ROOT_DIR" | awk 'NR == 2 {print $4}')"
  if [[ -z "$available_kb" || "$available_kb" -lt "$required_kb" ]]; then
    echo "启动被阻断：本地磁盘剩余空间不足。至少需要 $((required_kb / 1024 / 1024))GB 可用空间。" >&2
    exit 1
  fi
}

check_port_available() {
  local port="$1"
  local label="$2"
  if [[ -z "$port" ]]; then
    return
  fi
  if command -v lsof >/dev/null 2>&1; then
    if lsof -nP -iTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1; then
      echo "启动被阻断：${label}端口 ${port} 已被占用。若服务已启动，请先停止旧实例；否则请在 deploy/customer.env 更换端口。" >&2
      exit 1
    fi
  else
    echo "启动提醒：未找到 lsof，跳过端口占用检查。" >&2
  fi
}

require_value "STANDARD_OPS_DEV_BOOTSTRAP_ENABLED" "false"
require_value "OUTBOX_EXTERNAL_WRITE_ENABLED" "false"
require_value "TRUSTED_INBOUND_WORKER_ENABLED" "false"
require_value "KNOWLEDGE_VECTOR_STORE" "postgres_pgvector_store_v1"
require_empty "ADMIN_BOOTSTRAP_PASSWORD"

POSTGRES_PASSWORD="$(get_env_value "STANDARD_OPS_POSTGRES_PASSWORD")"
DATABASE_URL_VALUE="$(get_env_value "DATABASE_URL")"
if [[ "$POSTGRES_PASSWORD" == "replace-with-local-random-password" || "$DATABASE_URL_VALUE" == *"replace-with-local-random-password"* ]]; then
  if [[ "${WANFA_ALLOW_TEMPLATE_PASSWORD_FOR_REHEARSAL:-false}" != "true" ]]; then
    echo "启动被阻断：请先把 deploy/customer.env 里的数据库密码替换为客户本地随机密码。" >&2
    echo "仅做内部 rehearsal 时，可临时设置 WANFA_ALLOW_TEMPLATE_PASSWORD_FOR_REHEARSAL=true。" >&2
    exit 1
  fi
fi

BACKEND_PORT="$(get_env_value "STANDARD_OPS_BACKEND_PORT")"
FRONTEND_PORT="$(get_env_value "STANDARD_OPS_FRONTEND_PORT")"
POSTGRES_PORT="$(get_env_value "STANDARD_OPS_POSTGRES_PORT")"
REDIS_PORT="$(get_env_value "STANDARD_OPS_REDIS_PORT")"
POSTGRES_DB="$(get_env_value "STANDARD_OPS_POSTGRES_DB")"
POSTGRES_USER="$(get_env_value "STANDARD_OPS_POSTGRES_USER")"
BACKEND_PORT="${BACKEND_PORT:-18080}"
FRONTEND_PORT="${FRONTEND_PORT:-5173}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
REDIS_PORT="${REDIS_PORT:-6379}"
POSTGRES_DB="${POSTGRES_DB:-wanfa_ops}"
POSTGRES_USER="${POSTGRES_USER:-wanfa_ops}"

require_command "docker" "请先安装并启动 Docker Desktop。"

if ! docker info >/dev/null 2>&1; then
  echo "启动被阻断：Docker daemon 不可用。请先启动 Docker Desktop，并确认当前用户可以访问 Docker。" >&2
  exit 1
fi

if ! docker compose version >/dev/null 2>&1; then
  echo "启动被阻断：Docker Compose 不可用。请升级 Docker Desktop 或启用 compose 插件。" >&2
  exit 1
fi

check_disk_space
check_port_available "$POSTGRES_PORT" "PostgreSQL"
check_port_available "$REDIS_PORT" "Redis"
check_port_available "$BACKEND_PORT" "后端"
check_port_available "$FRONTEND_PORT" "前端"

COMPOSE=(
  docker compose
  --env-file "$ENV_FILE"
  -f "$ROOT_DIR/deploy/docker-compose.yml"
  -f "$ROOT_DIR/deploy/docker-compose.pilot.yml"
)

echo "正在检查本地试点配置..."
"${COMPOSE[@]}" config --quiet

echo "正在启动 PostgreSQL/pgvector 与 Redis..."
"${COMPOSE[@]}" up -d --build postgres redis

echo "正在检查 PostgreSQL readiness..."
"${COMPOSE[@]}" exec -T postgres pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB" >/dev/null

echo "正在执行数据库迁移..."
"${COMPOSE[@]}" run --rm backend python -m alembic -c alembic.ini upgrade head

echo "正在确认数据库迁移 head..."
"${COMPOSE[@]}" run --rm backend python -m alembic -c alembic.ini current >/dev/null

echo "正在启动客服中台后端和前端..."
"${COMPOSE[@]}" up -d --build backend frontend

echo "启动完成。"
echo "前端工作台：http://127.0.0.1:${FRONTEND_PORT}"
echo "后端健康检查：http://127.0.0.1:${BACKEND_PORT}/health"
echo "首任负责人请在本地登录页创建；真实外发和入站 worker 默认保持关闭。"
