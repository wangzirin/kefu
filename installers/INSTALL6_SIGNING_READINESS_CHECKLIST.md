# INSTALL6 正式签名安装包下一阶段清单

本文件只定义下一阶段要补齐的签名安装包条件。当前仍是本地试跑安装体验候选，不是正式签名 `dmg/exe`。

## 当前可试跑

- macOS：通过 `.command` 和 `.app` 包装候选调用安全启动脚本。
- Windows：通过 PowerShell 或 `.bat` 启动候选调用安全启动流程。
- 启动前检查 Docker Desktop、端口占用、`deploy/customer.env`、真实外发关闭、日志目录和卸载说明。
- 不自动写入模型密钥、平台密钥、数据库密码或默认管理员密码。

## 正式安装包前必须补齐

- Apple Developer ID 或 Windows 代码签名证书。
- macOS `dmg` 或 Windows 安装器构建流水线。
- 安装、卸载、升级、失败回滚和健康检查的系统级测试。
- 升级前强制备份和更新后版本切换验证。
- 客户本地日志目录脱敏检查。
- 不打开真实外发、不启用后台外发 worker 的安装后门禁。

## 继续保持关闭

- `signed_dmg_exe_ready=false`
- `real_platform_send_ready=false`
- `silent_update_ready=false`
- `remote_control_ready=false`
