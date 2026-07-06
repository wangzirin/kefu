# H2W-PACK5 客户本地试点交付包

## 结论

- 阶段状态：`ready_for_customer_local_pilot_handoff_candidate`
- 可作为客户本地试点交付包候选：`true`
- PACK4 安全启动入口就绪：`true`
- FE4 客户可见界面就绪：`true`
- FE4 浏览器点击 QA 通过：`true`
- 客户资料文档齐备：`true`
- 部署文件齐备且安全：`true`

## 交付对象

本阶段面向小微企业本地受控试点。交付目标是让试点客户能在本机或局域网内启动客服中台、创建首任负责人、导入资料、查看会话与质量页面，并把诊断包、备份和更新流程纳入后续售后闭环。

## 交付包包含

- `deploy/start-local-pilot.sh`：已存在
- `deploy/customer.env.example`：已存在
- `deploy/docker-compose.yml`：已存在
- `deploy/docker-compose.pilot.yml`：已存在
- `docs/customer/万法常世AI智能客服系统_产品介绍.md`：已存在
- `docs/customer/万法常世AI智能客服系统_客户使用手册.md`：已存在
- `docs/customer/万法常世AI智能客服系统_服务体系介绍.md`：已存在
- `docs/customer/万法常世AI智能客服系统_正式部署后运营模式手册.md`：已存在
- `README.md`：已存在
- `docs/P3-06U-26H2W_PACK3_LOCAL_PILOT_CANDIDATE_READINESS.md`：已存在
- `docs/P3-06U-26H2W_PACK4_LOCAL_PILOT_DELIVERY_CHECKLIST.md`：已存在
- `docs/P3-06U-26H2W_FE4_CUSTOMER_UI_SEALED_CANDIDATE.md`：已存在
- `docs/PRODUCTIZATION_MASTER_PLAN_LITE_AND_STANDARD.md`：已存在

## 客户启动步骤

1. 安装并启动 Docker Desktop。
2. 复制 `deploy/customer.env.example` 为 `deploy/customer.env`。
3. 替换 `STANDARD_OPS_POSTGRES_PASSWORD` 和 `DATABASE_URL` 中的模板数据库密码。
4. 运行 `deploy/start-local-pilot.sh deploy/customer.env`。
5. 在本地登录页创建首任负责人账号；系统不预置默认管理员密码。
6. 进入账号与本地维护页，先做一次诊断包和备份演练，再进入知识导入和试点操作。

## 停止门禁

- 缺 PACK3、PACK4、FE4 或 FE4 浏览器点击证据时，不交付给客户试用。
- `deploy/customer.env` 不应进入交付仓库；客户只能从模板复制并在本地填写。
- 客户模板里出现真实模型 key、默认管理员密码、真实外发开启或入站 worker 开启时，立即阻断。
- 启动脚本没有数据库迁移、没有阻断模板密码、或默认启用 worker profile 时，立即阻断。
- 当前交付不包含真实平台自动外发、企业渠道真实上线、正式准确率签收或生产 SLA。

## 运维交接

- 客户本地问题优先通过诊断包、备份、更新包预检和审计记录排查。
- 命中率下降先走知识补充、标准答案修订、禁用承诺和转人工规则复测，不直接归因于模型失效。
- 程序更新必须先备份、预检、应用、健康检查，再保留回滚记录。

## 阻断项

- 无

## 警告

- 无

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
- `customer_specific_knowledge_ready=false`
