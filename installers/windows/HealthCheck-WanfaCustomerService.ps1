param(
  [string]$EnvFile = ""
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RootDir = Resolve-Path (Join-Path $ScriptDir "..\..")
if ([string]::IsNullOrWhiteSpace($EnvFile)) {
  $EnvFile = Join-Path $RootDir "deploy\customer.env"
}

if (!(Test-Path $EnvFile)) {
  throw "健康检查阻断：未找到客户本地环境文件 $EnvFile。请先从 deploy\customer.env.example 复制并填写 deploy\customer.env。"
}

function Get-EnvValue([string]$Key) {
  $line = Get-Content $EnvFile | Where-Object { $_ -match "^\s*$Key=" } | Select-Object -Last 1
  if (!$line) { return "" }
  return (($line -split "=", 2)[1]).Trim().Trim('"').Trim("'")
}

function Require-EnvValue([string]$Key, [string]$Expected) {
  $actual = Get-EnvValue $Key
  if ($actual -ne $Expected) {
    throw "健康检查阻断：$Key 必须为 $Expected。"
  }
}

Require-EnvValue "STANDARD_OPS_DEV_BOOTSTRAP_ENABLED" "false"
Require-EnvValue "OUTBOX_EXTERNAL_WRITE_ENABLED" "false"
Require-EnvValue "TRUSTED_INBOUND_WORKER_ENABLED" "false"

try {
  docker info | Out-Null
} catch {
  throw "健康检查阻断：Docker Desktop 未运行或不可访问。"
}

$backendPort = Get-EnvValue "STANDARD_OPS_BACKEND_PORT"
$frontendPort = Get-EnvValue "STANDARD_OPS_FRONTEND_PORT"
if ([string]::IsNullOrWhiteSpace($backendPort)) { $backendPort = "18080" }
if ([string]::IsNullOrWhiteSpace($frontendPort)) { $frontendPort = "5173" }

$healthUrl = "http://127.0.0.1:$backendPort/health"
$frontendUrl = "http://127.0.0.1:$frontendPort"

Invoke-WebRequest -UseBasicParsing -Uri $healthUrl -TimeoutSec 5 | Out-Null

Write-Host "健康检查通过。"
Write-Host "前端地址：$frontendUrl"
Write-Host "后端健康接口：$healthUrl"
Write-Host "真实外发、入站 worker 和开发 bootstrap 均保持关闭。"
