# H2W-INSTALL5 本地启动体验试跑

## 结论

- 阶段状态：`local_startup_experience_ready`
- 本地启动体验：`true`
- 签名 dmg/exe：`false`

## 覆盖范围

- Docker Desktop 检查。
- 端口占用提示。
- `customer.env` 和数据库密码检查。
- 外发关闭和入站 worker 关闭检查。
- 日志目录、卸载/清理说明。

## 阻断项

- 无

## 边界

- `signed_dmg_exe_ready=false`
- `real_platform_send_ready=false`
- `silent_update_ready=false`
- `remote_control_ready=false`
