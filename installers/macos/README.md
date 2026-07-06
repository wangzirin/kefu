# macOS 原生安装器候选结构

本目录是 H2W-INSTALL2 的候选包装层，不是已签名的正式 `.dmg`。

## 目标

- 为客户提供更接近原生应用的启动入口。
- 启动前检查 Docker Desktop、端口、`deploy/customer.env`、真实外发开关和首任负责人密码边界。
- 继续调用现有 `deploy/start-local-pilot.sh`，不改安全启动脚本核心逻辑。

## 当前文件

- `WanfaCustomerService.command`：macOS 双击启动候选。
- `preflight.sh`：启动前只读预检。
- `uninstall-notes.md`：客户手动清理说明。

## 固定边界

- 不自动创建 `deploy/customer.env`。
- 不写入数据库密码或模型凭据。
- 不开启真实外发。
- 不启用入站 worker。
- 不远控客户电脑。
- `signed_dmg_exe_ready=false`。
