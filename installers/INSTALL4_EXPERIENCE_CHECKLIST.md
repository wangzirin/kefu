# H2W-INSTALL4 本地安装候选体验清单

本清单用于共创客户本地试点包，不是正式签名安装器说明。

## 启动前

- 客户已安装并启动 Docker Desktop。
- 客户已从 `deploy/customer.env.example` 复制出 `deploy/customer.env`。
- 客户已把数据库密码替换为本地随机密码。
- `STANDARD_OPS_DEV_BOOTSTRAP_ENABLED=false`。
- `OUTBOX_EXTERNAL_WRITE_ENABLED=false`。
- `TRUSTED_INBOUND_WORKER_ENABLED=false`。
- `ADMIN_BOOTSTRAP_PASSWORD` 为空，首任负责人必须在本地界面创建。

## 运行中

- macOS 可使用 `.app` 包装候选或 `.command` 启动候选。
- Windows 可使用 PowerShell 启动候选或 `.bat` 双击入口。
- 健康检查只读取 Docker、端口、本地后端 `/health` 和安全开关。
- 日志目录只保存健康检查、版本号、端口和预检摘要，不保存客户原文、模型 key、平台 token 或数据库密码。

## 升级前

- 先在客服中台“账号与本地维护”生成备份。
- 再运行升级前备份预检脚本生成 manifest。
- 预检脚本不复制数据库、不读取密钥、不静默替换程序文件。
- 更新包必须走签名更新包预检、暂存、应用和回滚链路。

## 卸载与清理

- 当前没有写入系统安装目录，卸载以停止容器和手动清理项目目录为主。
- 清理前必须先导出备份、诊断包和客户需要保留的知识资料。
- 不远程控制客户电脑，不静默删除客户数据。

## 仍未完成

- `signed_dmg_exe_ready=false`
- `desktop_installer_ready=false`
- `native_installer_ready=false`
- Apple/Windows 代码签名未完成。
- 正式安装包兼容性 QA 未完成。
- 真实外发继续关闭。
