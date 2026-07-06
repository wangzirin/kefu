Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RootDir = Resolve-Path (Join-Path $ScriptDir "..\..")
$EnvFile = Join-Path $RootDir "deploy\customer.env"

function Read-EnvValue {
  param([string]$Key)
  if (-not (Test-Path $EnvFile)) { return "" }
  $line = Get-Content $EnvFile | Where-Object { $_ -match "^\s*$Key=" } | Select-Object -Last 1
  if (-not $line) { return "" }
  return (($line -split "=", 2)[1]).Trim().Trim('"').Trim("'")
}

function Require-EnvValue {
  param([string]$Key, [string]$Expected)
  $actual = Read-EnvValue $Key
  if ($actual -ne $Expected) {
    throw "预检失败：$Key 必须为 $Expected。"
  }
}

function Require-EnvEmpty {
  param([string]$Key)
  $actual = Read-EnvValue $Key
  if ($actual.Length -gt 0) {
    throw "预检失败：$Key 必须为空，首任负责人需要在本地界面创建。"
  }
}

Write-Host "正在启动万法常世客服中台"
Write-Host "真实外发、入站 worker 和静默更新默认保持关闭。"

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
  throw "预检失败：未找到 Docker，请先安装并启动 Docker Desktop。"
}

docker info | Out-Null

if (-not (Test-Path $EnvFile)) {
  throw "预检失败：未找到 deploy\customer.env。请客户从 deploy\customer.env.example 复制后本地填写。"
}

Require-EnvValue "STANDARD_OPS_DEV_BOOTSTRAP_ENABLED" "false"
Require-EnvValue "OUTBOX_EXTERNAL_WRITE_ENABLED" "false"
Require-EnvValue "TRUSTED_INBOUND_WORKER_ENABLED" "false"
Require-EnvValue "KNOWLEDGE_VECTOR_STORE" "postgres_pgvector_store_v1"
Require-EnvEmpty "ADMIN_BOOTSTRAP_PASSWORD"

$postgresPassword = Read-EnvValue "STANDARD_OPS_POSTGRES_PASSWORD"
$databaseUrl = Read-EnvValue "DATABASE_URL"
if ($postgresPassword -eq "replace-with-local-random-password" -or $databaseUrl.Contains("replace-with-local-random-password")) {
  throw "预检失败：请先把 deploy\customer.env 中的数据库密码替换为客户本地随机密码。"
}

$composeFiles = @(
  "--env-file", $EnvFile,
  "-f", (Join-Path $RootDir "deploy\docker-compose.yml"),
  "-f", (Join-Path $RootDir "deploy\docker-compose.pilot.yml")
)

docker compose @composeFiles config --quiet
docker compose @composeFiles up -d --build postgres redis
docker compose @composeFiles run --rm backend python -m alembic -c alembic.ini upgrade head
docker compose @composeFiles up -d --build backend frontend

Write-Host ""
Write-Host "前端工作台：http://127.0.0.1:5173"
Write-Host "后端健康检查：http://127.0.0.1:18080/health"
Write-Host "首任负责人请在本地登录页创建。"
