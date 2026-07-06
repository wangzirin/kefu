#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "正在启动万法常世客服中台"
echo "真实外发、入站 worker 和静默更新默认保持关闭。"
echo ""

"$SCRIPT_DIR/preflight.sh"
"$ROOT_DIR/deploy/start-local-pilot.sh" "$ROOT_DIR/deploy/customer.env"

echo ""
echo "前端工作台：http://127.0.0.1:5173"
echo "后端健康检查：http://127.0.0.1:18080/health"
echo ""
read -r -p "按回车键关闭窗口..." _
