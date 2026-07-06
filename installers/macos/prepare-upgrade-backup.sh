#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
ENV_FILE="${1:-$ROOT_DIR/deploy/customer.env}"
VERSION_FILE="$ROOT_DIR/installers/VERSION.json"
LOG_ROOT="$ROOT_DIR/installers/logs/upgrade-preflight"
TIMESTAMP="$(date -u +"%Y%m%dT%H%M%SZ")"
RUN_DIR="$LOG_ROOT/$TIMESTAMP"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "升级前预检阻断：未找到客户本地环境文件 $ENV_FILE" >&2
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
    echo "升级前预检阻断：${key} 必须为 ${expected}。" >&2
    exit 1
  fi
}

require_env_value "STANDARD_OPS_DEV_BOOTSTRAP_ENABLED" "false"
require_env_value "OUTBOX_EXTERNAL_WRITE_ENABLED" "false"
require_env_value "TRUSTED_INBOUND_WORKER_ENABLED" "false"

mkdir -p "$RUN_DIR"
ENV_SHA="$(shasum -a 256 "$ENV_FILE" | awk '{print $1}')"
VERSION_SHA="missing"
if [[ -f "$VERSION_FILE" ]]; then
  VERSION_SHA="$(shasum -a 256 "$VERSION_FILE" | awk '{print $1}')"
fi

cat > "$RUN_DIR/manifest.json" <<JSON
{
  "schema_version": "p3-06u-26h2w-install3.upgrade_preflight.v1",
  "created_at": "$TIMESTAMP",
  "env_file_present": true,
  "env_file_sha256": "$ENV_SHA",
  "version_file_sha256": "$VERSION_SHA",
  "external_write_enabled": false,
  "trusted_inbound_worker_enabled": false,
  "development_bootstrap_enabled": false,
  "database_backup_exported_by_this_script": false,
  "backup_required_before_upgrade": true,
  "next_step": "请先在客服中台的账号与本地维护页面生成备份，再执行更新包预检。"
}
JSON

cat > "$RUN_DIR/NEXT_STEPS.md" <<'MARKDOWN'
# 升级前预检下一步

本脚本只生成升级前预检证据，不复制数据库、不读取模型密钥、不替客户静默升级。

下一步：

1. 打开客服中台。
2. 进入“账号与本地维护”。
3. 生成本地备份。
4. 完成更新包预检。
5. 如预检失败，保留本目录下的 manifest 给售后排查。
MARKDOWN

echo "升级前预检完成：$RUN_DIR"
echo "本脚本未复制数据库、未读取密钥、未执行静默更新。"
