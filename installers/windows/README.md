# Windows 原生安装器候选结构

本目录是 H2W-INSTALL2 的 Windows 启动候选，不是已签名的正式 `.exe`。

## 当前文件

- `Start-WanfaCustomerService.ps1`：PowerShell 启动候选。
- `start-wanfa-customer-service.bat`：双击入口，调用 PowerShell。
- `uninstall-notes.md`：客户手动清理说明。

## 固定边界

- 不自动创建 `deploy/customer.env`。
- 不写入数据库密码或模型凭据。
- 不开启真实外发。
- 不启用入站 worker。
- 不做静默更新。
- `signed_dmg_exe_ready=false`。
