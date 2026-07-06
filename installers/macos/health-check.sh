#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
ENV_FILE="${1:-$ROOT_DIR/deploy/customer.env}"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "健康检查阻断：未找到客户本地环境文件 $ENV_FILE" >&2
  echo "请先从 deploy/customer.env.example 复制并填写 deploy/customer.env。" >&2
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

require_env_value() {
  local key="$1"
  local expected="$2"
  local actual
  actual="$(get_env_value "$key")"
  if [[ "$actual" != "$expected" ]]; then
    echo "健康检查阻断：${key} 必须为 ${expected}。" >&2
    exit 1
  fi
}

require_env_value "STANDARD_OPS_DEV_BOOTSTRAP_ENABLED" "false"
require_env_value "OUTBOX_EXTERNAL_WRITE_ENABLED" "false"
require_env_value "TRUSTED_INBOUND_WORKER_ENABLED" "false"

if ! command -v docker >/dev/null 2>&1; then
  echo "健康检查阻断：未找到 Docker。请先安装 Docker Desktop。" >&2
  exit 1
fi

if ! docker info >/dev/null 2>&1; then
  echo "健康检查阻断：Docker Desktop 未运行或不可访问。" >&2
  exit 1
fi

BACKEND_PORT="$(get_env_value "STANDARD_OPS_BACKEND_PORT")"
FRONTEND_PORT="$(get_env_value "STANDARD_OPS_FRONTEND_PORT")"
BACKEND_PORT="${BACKEND_PORT:-18080}"
FRONTEND_PORT="${FRONTEND_PORT:-5173}"
HEALTH_URL="http://127.0.0.1:${BACKEND_PORT}/health"
FRONTEND_URL="http://127.0.0.1:${FRONTEND_PORT}"

if ! command -v curl >/dev/null 2>&1; then
  echo "健康检查阻断：未找到 curl，无法检查本地后端健康接口。" >&2
  exit 1
fi

if ! curl --fail --silent --show-error --max-time 5 "$HEALTH_URL" >/dev/null; then
  echo "健康检查阻断：后端健康接口不可用：$HEALTH_URL" >&2
  exit 1
fi

echo "健康检查通过。"
echo "前端地址：$FRONTEND_URL"
echo "后端健康接口：$HEALTH_URL"
echo "真实外发、入站 worker 和开发 bootstrap 均保持关闭。"
