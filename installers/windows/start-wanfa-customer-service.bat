@echo off
setlocal

echo 正在启动万法常世客服中台
echo 真实外发、入站 worker 和静默更新默认保持关闭。
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Start-WanfaCustomerService.ps1"
if errorlevel 1 (
  echo.
  echo 启动失败，请根据上方提示检查 Docker Desktop 和 deploy\customer.env。
  pause
  exit /b 1
)

echo.
echo 启动完成。
pause
