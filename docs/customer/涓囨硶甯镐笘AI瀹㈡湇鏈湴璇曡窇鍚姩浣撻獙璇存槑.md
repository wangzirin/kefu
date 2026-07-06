# 万法常世 AI 客服本地试跑启动体验说明

本说明用于第一批共创客户本地试跑。当前交付目标是让客户能在本机或局域网内启动客服中台、创建首任负责人、导入知识资料、查看质量和运维证据；不是正式签名安装包，也不会向真实平台自动发送消息。

## 启动前准备

1. 安装并启动 Docker Desktop。
2. 从 `deploy/customer.env.example` 复制一份 `deploy/customer.env`。
3. 把 `STANDARD_OPS_POSTGRES_PASSWORD` 替换为客户本地随机数据库密码。
4. 同步替换 `DATABASE_URL` 里的数据库密码。
5. 保持 `OUTBOX_EXTERNAL_WRITE_ENABLED=false`。
6. 保持 `TRUSTED_INBOUND_WORKER_ENABLED=false`。
7. 保持 `ADMIN_BOOTSTRAP_PASSWORD` 为空。

## 启动方式

macOS 可以使用 `deploy/start-local-pilot.command` 或 `installers/macos/WanfaCustomerService.command`。Windows 可以使用 `installers/windows/start-wanfa-customer-service.bat` 或 PowerShell 启动候选。

启动脚本会检查 Docker Desktop、`customer.env`、数据库密码、外发开关和入站 worker 开关。检查失败时会停止，不会绕过安全开关继续启动。

## 首次进入

启动成功后，打开本地前端地址。第一次进入时创建首任负责人账号，系统不预置默认管理员密码。后续人员由负责人在“账号与本地维护”中新增、停用或重置密码。

## 常见阻断

- 未安装 Docker Desktop：先安装并启动 Docker Desktop。
- 没有 `customer.env`：从模板复制一份并填写。
- 仍使用模板数据库密码：替换为客户本地随机密码。
- 端口被占用：先确认是否已有客服中台在运行；不要自行删除数据库目录。
- 外发开关被打开：改回关闭状态后再启动。

## 日志和清理

本地日志只保存启动预检、版本、端口和安全开关状态，不保存客户原文、密钥、平台 token、数据库密码或浏览器资料。清理前先导出备份和诊断包；当前没有正式写入系统安装目录，卸载以停止容器和手动清理项目目录为主。

## 边界

- 真实外发关闭。
- 真实渠道未接通。
- 不远控客户电脑。
- 不静默更新。
- 签名 dmg/exe 未完成。
- 内部演练不是客户正式验收。
