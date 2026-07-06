# H2W-INSTALL7 封包前客户模式门禁

## 结论

- 阶段状态：`customer_mode_prepack_gate_ready`
- 阻断项：`0` 个

## 客户模式硬边界

- 开发登录入口关闭：`STANDARD_OPS_DEV_BOOTSTRAP_ENABLED=false`
- 真实外发关闭：`OUTBOX_EXTERNAL_WRITE_ENABLED=false`
- 入站 worker 默认关闭：`TRUSTED_INBOUND_WORKER_ENABLED=false`
- 首任负责人必须在本地界面创建，模板不预置管理员密码
- 安装器仍为候选结构，签名 dmg/exe、静默更新和远控均保持 false

## 覆盖文件

- deploy/start-local-pilot.sh
- deploy/start-local-pilot.command
- deploy/customer.env.example
- deploy/docker-compose.pilot.yml
- installers/VERSION.json
- installers/macos/preflight.sh
- installers/macos/health-check.sh
- installers/macos/uninstall-notes.md
- installers/windows/Start-WanfaCustomerService.ps1
- installers/windows/HealthCheck-WanfaCustomerService.ps1
- installers/windows/uninstall-notes.md
- installers/logs/README.md
- docs/customer/万法常世AI客服本地试跑启动体验说明.md

## 不可承诺

- 正式客户验收签收
- 真实平台自动外发
- 企业微信、公众号、抖音、淘宝、京东、拼多多等真实渠道接通
- 生产 SLA 承诺
- 已签名 dmg/exe 安装器
- RPA 或个人号外挂正式交付

## 阻断项

- 无
