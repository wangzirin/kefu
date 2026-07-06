param(
  [string]$EnvFile = ""
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RootDir = Resolve-Path (Join-Path $ScriptDir "..\..")
if ([string]::IsNullOrWhiteSpace($EnvFile)) {
  $EnvFile = Join-Path $RootDir "deploy\customer.env"
}
$VersionFile = Join-Path $RootDir "installers\VERSION.json"
$Timestamp = (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssZ")
$RunDir = Join-Path $RootDir "installers\logs\upgrade-preflight\$Timestamp"

if (!(Test-Path $EnvFile)) {
  throw "升级前预检阻断：未找到客户本地环境文件 $EnvFile。"
}

function Get-EnvValue([string]$Key) {
  $line = Get-Content $EnvFile | Where-Object { $_ -match "^\s*$Key=" } | Select-Object -Last 1
  if (!$line) { return "" }
  return (($line -split "=", 2)[1]).Trim().Trim('"').Trim("'")
}

function Require-EnvValue([string]$Key, [string]$Expected) {
  $actual = Get-EnvValue $Key
  if ($actual -ne $Expected) {
    throw "升级前预检阻断：$Key 必须为 $Expected。"
  }
}

Require-EnvValue "STANDARD_OPS_DEV_BOOTSTRAP_ENABLED" "false"
Require-EnvValue "OUTBOX_EXTERNAL_WRITE_ENABLED" "false"
Require-EnvValue "TRUSTED_INBOUND_WORKER_ENABLED" "false"

New-Item -ItemType Directory -Force -Path $RunDir | Out-Null
$envHash = (Get-FileHash -Algorithm SHA256 $EnvFile).Hash.ToLowerInvariant()
$versionHash = "missing"
if (Test-Path $VersionFile) {
  $versionHash = (Get-FileHash -Algorithm SHA256 $VersionFile).Hash.ToLowerInvariant()
}

$manifest = [ordered]@{
  schema_version = "p3-06u-26h2w-install3.upgrade_preflight.v1"
  created_at = $Timestamp
  env_file_present = $true
  env_file_sha256 = $envHash
  version_file_sha256 = $versionHash
  external_write_enabled = $false
  trusted_inbound_worker_enabled = $false
  development_bootstrap_enabled = $false
  database_backup_exported_by_this_script = $false
  backup_required_before_upgrade = $true
  next_step = "请先在客服中台的账号与本地维护页面生成备份，再执行更新包预检。"
}

$manifest | ConvertTo-Json -Depth 4 | Set-Content -Encoding UTF8 (Join-Path $RunDir "manifest.json")
@"
# 升级前预检下一步

本脚本只生成升级前预检证据，不复制数据库、不读取模型密钥、不替客户静默升级。

下一步：

1. 打开客服中台。
2. 进入“账号与本地维护”。
3. 生成本地备份。
4. 完成更新包预检。
5. 如预检失败，保留本目录下的 manifest 给售后排查。
"@ | Set-Content -Encoding UTF8 (Join-Path $RunDir "NEXT_STEPS.md")

Write-Host "升级前预检完成：$RunDir"
Write-Host "本脚本未复制数据库、未读取密钥、未执行静默更新。"
