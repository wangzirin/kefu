#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
ENV_FILE="$ROOT_DIR/deploy/customer.env"

read_env_value() {
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

require_env_value() {
  local key="$1"
  local expected="$2"
  local actual
  actual="$(read_env_value "$key")"
  if [[ "$actual" != "$expected" ]]; then
    echo "预检失败：${key} 必须为 ${expected}。" >&2
    exit 1
  fi
}

require_env_empty() {
  local key="$1"
  local actual
  actual="$(read_env_value "$key")"
  if [[ -n "$actual" ]]; then
    echo "预检失败：${key} 必须为空，首任负责人需要在本地界面创建。" >&2
    exit 1
  fi
}

if ! command -v docker >/dev/null 2>&1; then
  echo "预检失败：未找到 Docker，请先安装并启动 Docker Desktop。" >&2
  exit 1
fi

if ! docker info >/dev/null 2>&1; then
  echo "预检失败：Docker Desktop 未运行或当前用户无权访问 Docker。" >&2
  exit 1
fi

if [[ ! -f "$ENV_FILE" ]]; then
  echo "预检失败：未找到 deploy/customer.env。请客户从 deploy/customer.env.example 复制后本地填写。" >&2
  exit 1
fi

require_env_value "STANDARD_OPS_DEV_BOOTSTRAP_ENABLED" "false"
require_env_value "OUTBOX_EXTERNAL_WRITE_ENABLED" "false"
require_env_value "TRUSTED_INBOUND_WORKER_ENABLED" "false"
require_env_value "KNOWLEDGE_VECTOR_STORE" "postgres_pgvector_store_v1"
require_env_empty "ADMIN_BOOTSTRAP_PASSWORD"

POSTGRES_PASSWORD="$(read_env_value "STANDARD_OPS_POSTGRES_PASSWORD")"
DATABASE_URL_VALUE="$(read_env_value "DATABASE_URL")"
if [[ "$POSTGRES_PASSWORD" == "replace-with-local-random-password" || "$DATABASE_URL_VALUE" == *"replace-with-local-random-password"* ]]; then
  echo "预检失败：请先把 deploy/customer.env 中的数据库密码替换为客户本地随机密码。" >&2
  exit 1
fi

BACKEND_PORT="$(read_env_value "STANDARD_OPS_BACKEND_PORT")"
FRONTEND_PORT="$(read_env_value "STANDARD_OPS_FRONTEND_PORT")"
BACKEND_PORT="${BACKEND_PORT:-18080}"
FRONTEND_PORT="${FRONTEND_PORT:-5173}"

if command -v lsof >/dev/null 2>&1; then
  if lsof -iTCP:"$BACKEND_PORT" -sTCP:LISTEN >/dev/null 2>&1; then
    echo "预检提醒：后端端口 ${BACKEND_PORT} 已被占用，可能是服务已经启动或需要更换端口。" >&2
  fi
  if lsof -iTCP:"$FRONTEND_PORT" -sTCP:LISTEN >/dev/null 2>&1; then
    echo "预检提醒：前端端口 ${FRONTEND_PORT} 已被占用，可能是服务已经启动或需要更换端口。" >&2
  fi
fi

echo "macOS 启动预检通过。"
