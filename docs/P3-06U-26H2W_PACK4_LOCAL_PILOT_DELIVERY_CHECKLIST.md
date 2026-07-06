# H2W-PACK4 本地试点交付清单与安全启动 rehearsal

## 结论

- 阶段状态：`ready_for_customer_local_pilot_startup_rehearsal`
- PACK3 上游候选已就绪：`true`
- 客户安全启动脚本已就绪：`true`
- 客户环境模板已就绪：`true`
- Compose 静态解析已通过：`true`
- worker 默认不启动：`true`
- 可进入客户本地试点启动 rehearsal：`true`

## 客户本地交付步骤

1. 安装并启动 Docker Desktop。
2. 复制 `deploy/customer.env.example` 为 `deploy/customer.env`。
3. 把 `STANDARD_OPS_POSTGRES_PASSWORD` 和 `DATABASE_URL` 里的模板密码替换为本地随机密码。
4. 运行 `deploy/start-local-pilot.sh deploy/customer.env`。
5. 打开前端工作台，在登录页创建首任负责人；系统不预置默认管理员密码。

## 停止门禁

- 客户环境里开发 bootstrap、真实外发或入站 worker 任一开启，禁止启动。
- 未替换模板数据库密码，禁止启动；只有内部 rehearsal 可显式设置 `WANFA_ALLOW_TEMPLATE_PASSWORD_FOR_REHEARSAL=true`。
- 启动命令不得默认启用 `worker` profile。
- 没有 PACK3 上游候选证据，不进入客户本地试点启动 rehearsal。
- 本阶段不代表完整桌面安装器、正式客户签收、真实渠道上线或生产 SLA。

## 阻断项

- 无

## 警告

- 无

## 验收证据

- summary_json: `output/p3_06u_26h2w_pack4_delivery_checklist_and_startup_rehearsal/summary.json`
- markdown: `docs/P3-06U-26H2W_PACK4_LOCAL_PILOT_DELIVERY_CHECKLIST.md`
- start_script: `deploy/start-local-pilot.sh`
- customer_env_template: `deploy/customer.env.example`
- pack3_summary: `output/p3_06u_26h2w_pack3_local_pilot_candidate_readiness/summary.json`

## 不可对外承诺

- 完整桌面安装器或双击安装包
- 正式客户准确率签收
- 真实平台自动外发
- 企业微信/微信客服/抖音/淘宝/京东/拼多多真实渠道上线
- 客户专属知识库验收
- 生产环境长期监控、告警和 SLA

## 固定边界

- `real_platform_send_performed=false`
- `enterprise_channel_scope_included=false`
- `formal_customer_signoff_performed=false`
- `desktop_installer_ready=false`
- `rpa_formal_delivery_included=false`
