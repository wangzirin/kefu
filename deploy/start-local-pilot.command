#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$SCRIPT_DIR/customer.env"

echo "正在启动万法常世客服中台本地试点"
echo ""
echo "请先确认："
echo "1. Docker Desktop 已经安装并启动。"
echo "2. 已复制 deploy/customer.env.example 为 deploy/customer.env。"
echo "3. 已把 deploy/customer.env 里的数据库密码替换为本地随机密码。"
echo ""

if [[ ! -f "$ENV_FILE" ]]; then
  echo "未找到 deploy/customer.env。"
  echo "请先按说明从 customer.env.example 复制一份 customer.env，并填写本地随机数据库密码。"
  echo ""
  read -r -p "按回车键关闭窗口..." _
  exit 1
fi

"$SCRIPT_DIR/start-local-pilot.sh" "$ENV_FILE"

echo ""
echo "前端工作台：http://127.0.0.1:5173"
echo "后端健康检查：http://127.0.0.1:8000/health"
echo "真实外发和入站 worker 默认保持关闭。"
echo ""
read -r -p "按回车键关闭窗口..." _
