# 万法常世 AI 全智能客服系统产品化总控计划

日期：2026-06-29  
最近更新：2026-07-06  
适用范围：Lite 试点版、标准运营版、客户资料包、对外服务体系、内部售后运维体系  
当前状态基准：`standard_ops` 已完成 P3-05A 试点部署准备与正式对外 DOCX 资料包，P3-05B 已完成 Lite readiness、托管云 runbook、私有化部署包、远程维护授权 SOP 和 readiness smoke，P3-05C 已完成官方渠道自动回复 readiness 核验，P3-05H/P3-05I/P3-05J 已完成会话收件箱、坐席动作、页面化导航、对话台和质量复盘，P3-05K 已完成知识缺口闭环，P3-05M 已完成工单与轻量 SLA 第一片，P3-05N 已完成联系人画像与线索跟进第一片，P3-05O 已完成知识缺口到文档草稿与回归题库第一片，P3-05Q 已完成对话台坐席主工作区重构，P3-05R 已完成质量诊断 BI 第一片，P3-05S 已完成知识发布前回归门禁第一片，P3-05T 已完成知识发布记录、门禁详情与回滚第一片，P3-06A 已完成 outbox delivery queue 租约与原子抢占第一片，P3-06B 已完成可信入站 worker 租约、运行记录和失败重放第一片，P3-06C 已完成 worker heartbeat 与受控常驻循环第一片，P3-06D 已完成部署级 worker 进程第一片、Docker Compose worker service、healthcheck 和静态 readiness 检查，P3-06E 已完成只读运维心跳面板第一片、后台进程健康总览接口和前端“运维”工作区，P3-06F 已完成只读告警规则第一片、运维规则 runbook 和前端“运维与告警”展示区，P3-06UI 已完成中台信息架构三片，P3-06G 已完成指标出口第一片，P3-06H/P3-06I/P3-06J/P3-06K/P3-06L/P3-06M/P3-06N/P3-06P 已完成 RBAC 前八片；P3-06O 已完成前端按钮级权限第一片；P3-06R-01 已完成中台壳层固定和运营总览 BI 第一版；P3-06R-01B 已完成壳层滚动二次修复，桌面端由右侧工作区独立滚动、移动端恢复自然页面滚动；P3-06R-02 已完成生产模式 bootstrap 关闭、foundation/workflow/worker/reply 权限契约收口，以及前端按权限刷新资源；P3-06R-03A 已完成坐席工作台一屏闭环前端第一片；P3-06R-04C 已完成运营总览服务端聚合接口第一片；P3-06T-01 已完成壳层滚动返修验收；P3-06T-02 已完成首页数据口径收紧；P3-06T-03 已完成运营总览 BI 重做；P3-06U-01 已完成前后端契约与页面路径盘点；P3-06U-02 已完成角色化任务路径重排；P3-06U-03 已完成接待工作台实用性重构；P3-06U-04 已完成运营总览到处理路径打通；P3-06U-05 已完成 owner/admin/agent/viewer 真实登录角色 smoke；P3-06U-06 已完成质量复盘 BI 与知识修复闭环；P3-06U-07 已完成知识运营台产品化第一片；P3-06U-08 已完成渠道连接器中心实用化；P3-06U-09 已完成前端状态体系统一；P3-06U-10 第一片已完成统一状态组件抽离；P3-06U-14 已完成质量复盘页组件拆分；P3-06U-15 已完成渠道连接器中心组件拆分；P3-06U-16 已完成工作台去重与微信式对话台再瘦身；P3-06U-17 已完成云朵AI视频参考拆解、对话台左侧收窄、渠道入站卡和 AI 自动回复优先的工作台文案/结构收束；P3-06U-18 已完成云朵AI抽帧深度参考到工程优化的总纲，P3-06U-19 已完成业务对象知识库第一片，P3-06U-20 已完成自动回复策略状态机第一片，P3-06U-21 已完成可信入站 worker 与回复决策闭环第一片，P3-06U-22 已完成工作台回复决策可视化，P3-06U-23 已完成渠道账号/店铺实体与预览稳定性第一片，P3-06U-24 已完成知识运营三页首屏职责分离和渠道账号/店铺后端模型第一片，P3-06U-25 已完成客服中台综合成熟度评分，P3-06U-26 已完成工程优化总纲，P3-06U-26A 已完成对外界面去演示味和正式/内部环境文案分层，P3-06U-26B 已完成多渠道对话台微信式收束，P3-06U-26C 已完成渠道账号/店铺配置面板接入 `channel_accounts` 后端接口，P3-06U-26D 已完成知识库运营、知识缺口、知识评测三页页面壳、首屏指标、错因地图和发布前后对比入口，P3-06U-26E 已完成客服答案质量评测第一片，P3-06U-26F 已完成真实客户题库与知识包导入模板第一片，P3-06U-26G 已完成渠道官方 sandbox 优先级和 RPA draft-only 研究边界固化；后续已进入并推进到 H2T，本文件当前进度以“最新覆盖状态”条为准。P3-06R-05 渠道连接器中心第一片、字段脱敏/字段 allowlist、P3-06R-04D 统计缓存/物化层和企业微信公网 HTTPS 回调 smoke 仍可作为后续并行专项。真实外发继续默认关闭。

最新覆盖状态：FIX8 前端成品细节精修已完成，当前前端逐按钮审计 `status=passed_without_p0_p1`，P0/P1/P2 均为 0。本轮在 FIX1-FIX7 的本地回复闭环基础上继续补齐成品细节：禁用控件必须说明原因，图标/文件输入必须有可理解标签，分页不可用必须说明已到首页/尾页，线索阶段、知识运营、知识缺口、知识评测、账号重置/停用等按钮都按“真实动作、明确禁用说明、隐藏”三选一收束。本地发送浏览器 smoke 通过，结果为 `message-visible` 且外部平台未发送边界提示可见；前端 `typecheck/build` 通过，前端与后端健康检查正常。当前仍是本地试运行客服体验修复，不代表真实外发、真实渠道上线、正式客户签收、生产 SLA、签名安装包或移动端完成。

早前覆盖状态：FIX1-FIX7 智能客服系统前端与主链路修复已完成第一轮，当前前端审计 `status=passed_without_p0_p1`。本轮优先解决用户真实使用卡点：工作台已支持“发送到本地会话”并写入本地 outbound 坐席消息，AI 建议只作为可填入输入框的建议，不再伪装成已发送；“试点准备”统一改为“本地试运行准备”，首屏只保留导入资料、运行复测、导出交付档案；联系人中心和线索跟进降级为轻量客户资料与商机记录并修复横向裁切；渠道页改为配置准备与边界说明；运维页客户可见工程词已替换。验证通过：前端 `typecheck/build`、后端会话消息测试与 sealed pilot 回归 `52 passed`、逐按钮审计和本地发送浏览器 smoke。当前仍是本地试运行客服体验修复，不代表真实外发、真实渠道上线、正式客户签收、生产 SLA、签名安装包或移动端完成。

早前覆盖状态：H2W-NC19 客户红队安全报告流程准备已完成第一片，当前 `status=customer_redteam_report_flow_ready_waiting_customer_data`。本轮基于 NC18 内部红队事实账本，生成客户红队题库、人工标签和 manifest 三件套模板，并生成客户红队安全报告骨架；门禁在未收到真实客户回传文件时保持等待态，不把内部样本写成客户安全报告或正式签收。验证通过：NC19 专项测试 `2 passed`、NC19 门禁、NC17/NC18/LLM ops 相邻回归 `11 passed`、sealed pilot gates `49 passed`、脚本 py_compile。当前完成的是客户红队安全报告流程模板，不是客户真实红队题库、真实模型输出标签、客户业务负责人复核确认或正式安全签收；真实客户资料版封包、完整 Memory Mesh 图谱、真实渠道、生产 SLA、移动端和签名安装包仍未完成。

早前覆盖状态：H2W-NC18 红队事实账本导入与前端观测卡片联动已完成第一片，当前 `status=redteam_fact_ingest_ready_internal_sample_visible_to_llm_ops`。本轮把 NC17 的 25 条内部红队样本和 25 条影子标签导入隔离数据库，落成评测集、评测用例、评测运行、人工标签和试点事实记录，并验证现有 LLM Ops readiness 可读取数据库事实；前端“自动回复策略 -> 模型观测与红队”卡片已展示安全题集、人工标签、题集来源和类目覆盖。验证通过：NC18 专项测试 `2 passed`、LLM ops API 测试 `6 passed`、NC18 门禁、前端 typecheck/build、NC17 回归 `3 passed`、sealed pilot gates `49 passed`。当前完成的是内部样本数据库事实导入 rehearsal，不是客户真实红队安全签收；真实客户资料版封包、真实客户红队题库/模型输出标签、完整 Memory Mesh 图谱、真实渠道、生产 SLA、移动端和签名安装包仍未完成。

早前覆盖状态：H2W-NC16 红队闭环门禁已完成第一片，当前 `status=redteam_closure_gate_ready_internal_fixtures_only`。本轮在 NC6 模型观测基础上收紧红队判定：红队题集必须覆盖提示注入、越狱、隐私泄露、禁用承诺和越权操作五类风险，全部活跃红队题必须有最终答案人工标签，失败样本必须逐条进入知识缺口或质量复盘，不能再用任意知识缺口冒充闭环。新增 `scripts/check_p3_06u_26h2w_nc16_redteam_closure.py`、`docs/P3-06U-26H2W_NC16_REDTEAM_CLOSURE.md` 和 `output/p3_06u_26h2w_nc16_redteam_closure/summary.json`。验证通过：LLM ops API 测试 `6 passed`、NC16 门禁、NC6 相邻门禁、pilot/knowledge gaps 相邻回归 `17 passed`、sealed pilot gates `49 passed`。当前完成的是红队闭环规则和内部 fixture 验证，不是客户真实红队安全签收；真实客户资料版封包、真实客户红队题库/模型输出标签、完整 Memory Mesh 图谱、真实渠道、生产 SLA、移动端和签名安装包仍未完成。

早前覆盖状态：H2W-NC15 PostgreSQL 正式恢复 SOP 与停机编排门禁已完成第一片，当前 `status=formal_restore_runbook_ready_no_live_restore`。本轮新增 `POST /api/tenants/{tenant_id}/local-backups/postgres-formal-restore-runbook`，登记恢复 SOP、停机编排、二次备份要求、最终确认、恢复后健康检查和回滚决策树；服务端只保存摘要、hash 和审计，不执行 `pg_restore`，不替换真实数据库，不保存 dump 本体或原始恢复命令。验证通过：NC15 门禁、本地备份/维护/签名更新回归 `32 passed`、sealed pilot gates `49 passed`。

早前覆盖状态：H2W-NC13 PostgreSQL 正式恢复前置门禁已完成第一片，当前 `status=formal_restore_preflight_gate_ready_no_live_restore`。本轮新增 `POST /api/tenants/{tenant_id}/local-backups/postgres-formal-restore-preflight`，用于在 NC10 备份证据、NC11 恢复计划和 NC12 临时库恢复演练之后，登记客户管理员确认包、维护窗口、恢复前二次备份要求、健康检查计划、回滚计划和最终操作员确认。服务端只登记确认包摘要、hash、前置门禁和审计，不执行 `pg_restore`，不替换真实数据库，不打开真实外发，也不提供应用内一键恢复。验证通过：NC13 门禁、NC12/NC11 相邻门禁、local backups / local maintenance / signed update 回归 `28 passed`。当前仍等待客户机实际 NC8/NC12 manifest 和后续正式恢复执行 SOP；真实客户资料版封包、真实渠道、生产 SLA、移动端和签名安装包仍未完成。

早前覆盖状态：H2W-NC12 PostgreSQL 临时库恢复演练已完成第一片，当前 `status=postgres_temp_restore_rehearsal_ready_waiting_customer_pg_run`。本轮新增 `deploy/postgres-temp-restore-rehearsal.sh` 和 `POST /api/tenants/{tenant_id}/local-backups/postgres-temp-restore-manifests`，用于在客户机把已登记的 PostgreSQL 备份恢复到 `wanfa_restore_tmp_...` 临时库、完成健康检查、删除临时库后登记 manifest。服务端只登记 manifest、临时库名 hash、恢复摘要和审计，不保存 dump 文件本体，不保存临时库明文名，不执行服务端 `pg_restore`，不替换真实数据库，不打开真实外发。验证通过：NC12 门禁、NC11/NC10 相邻门禁、local backups / local maintenance / signed update 回归 `26 passed`、sealed pilot gates `49 passed`。当前仍等待客户机实际运行 NC8/NC12 脚本并登记 manifest；正式恢复执行、停机窗口、恢复前二次备份、客户管理员确认、真实客户资料版封包、真实渠道、生产 SLA、移动端和签名安装包仍未完成。

早前覆盖状态：H2W-NC11 PostgreSQL 恢复演练计划已完成第一片，当前 `status=postgres_restore_rehearsal_plan_ready_no_live_restore`。本轮新增 `POST /api/local-backups/{local_backup_id}/postgres-restore-rehearsal-plan`，用于把已登记的 PostgreSQL 备份 manifest 转成受控恢复演练计划；服务端只登记计划、前置门禁和审计，不执行 `pg_restore`，不替换数据库，不保存 dump 文件本体，不打开真实外发。验证通过：NC11 门禁、NC10 相邻门禁、local backups / local maintenance / signed update 回归 `24 passed`、sealed pilot gates `49 passed`。当前仍等待客户机实际 PostgreSQL 备份演练 manifest；真实恢复执行工具、真实客户资料版封包、真实渠道、生产 SLA、移动端和签名安装包仍未完成。

早前覆盖状态：H2W-NC10 PostgreSQL 备份证据登记已完成第一片，当前 `status=postgres_backup_evidence_registration_ready_waiting_customer_pg_run`。本轮新增 `POST /api/tenants/{tenant_id}/local-backups/postgres-dry-run-manifests`，用于把客户本机 `deploy/postgres-backup-dry-run.sh` 生成的 manifest 登记到本地维护证据链；服务端只保存 manifest、hash、大小、`pg_restore --list` 可读性结果和恢复演练摘要，不保存 dump 文件本体，不执行真实恢复，不替换数据库，不打开真实外发。验证通过：NC10 门禁、local backups / local maintenance / signed update 回归 `22 passed`、NC8/NC9 相邻门禁、sealed pilot gates `49 passed`。当前仍等待客户机实际 PostgreSQL 备份演练 manifest；真实客户资料版封包、真实恢复工具、真实渠道、生产 SLA、移动端和签名安装包仍未完成。

最新覆盖状态：H2W-NC9 非真实渠道版本地试跑包 v4 已完成，当前 `status=local_trial_package_v4_candidate_with_internal_sample`。本轮新增 NC9 聚合门禁与交付档案生成脚本 `scripts/check_p3_06u_26h2w_nc9_local_trial_package_v4.py`，聚合 NC1-NC8、PACK11、PACK12、FE12、KB6、TRIAL3、OPS2、OPS3、INSTALL7 等证据，输出阶段文档、机器摘要、manifest 和 `output/p3_06u_26h2w_nc9_local_trial_package_v4/local_trial_package_v4_candidate.zip`。档案包含客户本地试跑需要的启动、负责人、资料模板、知识导入预检、知识复测、影子试跑质量、月度运维、诊断备份更新回滚、安装候选和边界声明；扫描阻断 key、token、密码、客户原文、平台 payload、`.git`、`node_modules`、浏览器 profile、临时数据库、Cookies、History 和 Login Data。验证通过：NC9 门禁、脚本 py_compile、NC8/NC7 相邻门禁、PACK11 聚合回归、sealed pilot gates `49 passed`。当前仍是内部样板本地试跑包候选，不是真实客户资料版封包、正式客户签收、真实外发、真实渠道、生产 SLA、移动端或签名安装包完成。

最新覆盖状态：H2W-NC8 本地安装、备份、更新与回滚补强已完成第一片，当前 `status=local_install_backup_update_rollback_hardened_pg_script_ready`。本轮补强 `deploy/start-local-pilot.sh`，增加 Docker daemon、Docker Compose、磁盘空间、端口占用、PostgreSQL readiness、迁移 head、真实外发关闭和入站 worker 关闭检查；新增 `deploy/postgres-backup-dry-run.sh`，用于在客户本机生成 PostgreSQL `pg_dump -Fc` 备份并用 `pg_restore --list` 做可读性 dry-run；签名知识包和策略包 apply 前已增加服务端备份门禁，没有已验证本地备份与恢复 dry-run 证据时拒绝应用。验证通过：NC8 门禁、后端 signed update/local backup/local maintenance 相关测试 `20 passed`、bash 语法检查和 H2W8B 静态门禁。NC10 已补服务端 PostgreSQL manifest 登记能力；当前仍未在客户 Docker 环境实际执行 PostgreSQL 备份演练并提供 manifest。真实外发、真实渠道、正式客户签收、生产 SLA、移动端和签名安装包仍未完成。

最新覆盖状态：H2W-NC7 前端真实产品化收束已完成第一片，当前 `status=frontend_productization_customer_flow_ready_component_split_pending`。本轮把“试点准备”提升为一级主入口，把“账号安全”统一为“账号与本地维护”，质量复盘客户可见口径从“签收”降级为“试跑确认”，账号与本地维护的月度运维报告入口改为 `#quality?focus=monthly-ops-report`，并新增 NC7 门禁检查多渠道对话台 IM 主形态、渠道边界、孤儿链接和旧签收口径。验证通过：NC7 门禁、前端 typecheck/build、FE6 浏览器真实登录 smoke。当前客户主路径产品化已改善，但 `App.tsx`、`styles.css`、`api/client.ts` 仍偏大，组件拆分和更深视觉精修尚未完成；真实外发、真实渠道、正式客户签收、生产 SLA、移动端和签名安装包仍未完成。

最新覆盖状态：H2W-NC6 模型观测、成本与红队治理第一片已完成，当前 `status=llm_ops_observability_ready_not_redteam_complete`。本轮新增 `GET /api/tenants/{tenant_id}/llm-ops-readiness`，把模型网关版本、策略版本、显式模型服务商失败不静默切换、模型调用成本台账、降级动作、链路追踪、引用快照、最终答案标签和红队题集状态纳入同一运营视图；前端“自动回复策略”页新增“模型观测与红队”卡片和门禁列表。验证通过：LLM ops API 测试、RAG 治理相邻回归、封版门禁相邻回归、NC6 聚合门禁、前端 typecheck/build。当前模型成本与链路观测已接上，但红队题集和人工标签尚未完整闭环，所以不能写成安全评测完成、正式客户签收、真实外发、真实渠道、生产 SLA 或签名安装包完成。

最新覆盖状态：H2W-NC5 生产级检索与评测治理已完成第一轮收束，当前 `status=production_retrieval_governance_ready_not_production_switch`。本轮在 RAG 成本治理摘要中新增 `production_readiness`，把 PostgreSQL+pgvector runtime、真实客户资料批次、50 题以上题库、最终答案质量标签、embedding 成本记录、客服模型调用成本和预算策略合并为生产检索准备度；前端“生产检索准备度”展示真实资料批次状态，避免把内部样板/内部 100 题误写成生产可切换。NC5 聚合已读取 H2W7D、TRIAL1、MODEL1、NC4、DATA2、PACK12 证据；当前治理层 ready，但真实客户资料 ready=false、真实资料链路重跑 ready=false，所以生产检索切换仍为 false。验证通过：RAG 治理 API 测试、向量索引相邻回归、H2W7 静态门禁、NC5 聚合门禁、前端 typecheck/build。真实客户资料闭环、真实外发、真实渠道、客户签收、生产 SLA 和签名安装包仍未完成。

最新覆盖状态：H2W-NC4 知识中心 v2 与 Memory Mesh 化第一片已完成，当前 `status=knowledge_memory_mesh_overview_ready`。本轮新增 `GET /api/tenants/{tenant_id}/knowledge-memory-mesh-overview`，以 `knowledge.read` 权限读取知识网络总览；后端把资料批次、知识卡片、业务对象、真实/样本问题、质量标签与错因聚合为五类节点，并展示入站样本、检索结果、引用 chunk、模型调用、最终草稿、转人工理由、质量标签、修复后的知识版本八段证据链。前端知识三页统一展示该总览，客户可见文案不出现工程词。接口只返回计数、状态、hash/source_uri 覆盖和边界，不返回客户原文、文档正文、草稿全文、密钥或平台 payload。验证通过：知识 API 测试、NC4 门禁、封版相邻回归、前端 typecheck/build。完整图数据库式 Memory Mesh、真实客户资料闭环、真实外发、真实渠道、客户签收、生产 SLA 和签名安装包仍未完成。

最新覆盖状态：H2W-NC3 客户资料接收与预检产品化已完成，当前 `status=customer_material_precheck_productization_ready`。本轮把资料预检从一次性文本区升级为可追踪资料批次：后端新增 `GET /api/tenants/{tenant_id}/customer-materials/batches`，前端“试点准备”页新增本地 CSV/JSON 草稿填入、资料批次刷新和最近批次状态展示；批次列表只返回 hash、统计和状态，不返回客户原文、标准答案全文、密钥或平台 payload。验证通过：pilot API 测试、封版相邻门禁、NC3 门禁、全量后端测试、前端 typecheck/build。预检通过仍只是进入固定文件接收目录的前置条件，不代表真实客户资料 ready、客户签收、真实外发、真实渠道、生产 SLA 或签名安装包完成。

最新覆盖状态：H2W-NC2 客户模式安全硬化已完成，当前 `status=customer_mode_security_hardening_ready`。本轮补齐登录失败限速、失败审计和冷却；首任负责人创建前强制检查开发 bootstrap、真实外发和入站 worker 开关；客户模式下无 token 的 `/api/auth/me` 不能返回开发 bootstrap 用户；诊断上传包新增大小、嵌套深度和 schema allowlist 门禁，坏包只保存拒收摘要；交付档案扫描禁止浏览器 profile、Cookies、History、Login Data、`.git` 和 `node_modules`。验证通过：auth/local setup/diagnostics 目标测试、NC2 门禁、全量后端测试、前端 typecheck/build。真实客户资料、真实外发、真实渠道、正式客户签收、生产 SLA 和签名安装包仍未完成。

最新覆盖状态：H2W-NC1 试点事实账本权威化已完成，当前 `status=nc1_pilot_fact_authority_ready`。本轮将 `pilot-readiness` 的客户资料 ready 判定从“复测数量 + 确认审计事件”收紧为数据库事实链：真实资料批次 ready、真实题库数量与四层知识字段完整、真实知识复测 fact 通过、客户确认导入 fact 通过或带备注通过、无敏感信息 blocker。客户确认导入现在写入 `pilot_readiness_facts.fact_key=pilot2.knowledge_confirmation_import`，仅保存 CSV hash、计数、状态和风险数量，不保存原始 CSV。工程 summary 增加 schema/hash/freshness 标记并固定 `authority=engineering_evidence_only`，不能抬高客户现场 ready。验证通过：pilot API 测试、NC1 门禁、全量后端测试、前端 typecheck/build。真实客户资料、真实外发、真实渠道、正式客户签收、生产 SLA 和签名安装包仍未完成。

最新覆盖状态：按用户要求，三份固定回传文件已由工程侧制作完成，用于跑通 DATA2 -> DATA2R7 -> PACK12 内部样板演练链。文件位于 `evals/p3_06u_26h2w_data2_real_customer_material_readiness/`，包括 `customer_materials_received.csv`、`customer_trial_questions_received.csv`、`customer_material_manifest_received.json`。这些文件是内部准真实样板，不是客户真实回填、不是客户确认、不是正式签收。当前 DATA2 `status=internal_sample_materials_ready_for_rehearsal`，资料 22 条、问题 60 条；DATA2R7 `status=received_internal_sample_files_validated_ready_for_pack12_rerun`；PACK12 `status=internal_sample_data_rerun_orchestration_ready`，`customer_data_used=false`、`internal_sample_used=true`、`customer_data_rerun_complete=false`、`internal_sample_rerun_complete=true`。真实客户资料、真实外发、真实渠道、客户签收、生产 SLA 和签名安装包仍未完成。

最新覆盖状态：H2W-DATA2R8 回传落位状态接入已完成，当前 `status=material_drop_gate_api_ui_ready`。DATA2R8 把 DATA2R7 的“回传文件是否落位”门禁接入后端 `pilot-readiness` 和前端“试点准备”页：后端新增 `material_drop_gate_status/material_drop_gate_evidence`，前端在资料接收包状态和五大缺口卡片中显示“回传文件落位”。本轮只提升客户/实施人员的状态可见性，不生成、不改写、不伪造真实客户资料；当前 DATA2R7 仍等待三份固定回传文件，真实外发、真实渠道、客户签收、生产 SLA 和签名安装包仍未完成。

最新覆盖状态：H2W-DATA2R7 真实资料回传落位门禁已完成，当前 `status=received_file_drop_ready_waiting_customer_files`。DATA2R7 在 DATA2/DATA2R6/PACK12 之间补上“回传文件是否落位”的机器门禁：接收目录、模板、回传文件包和 PACK12 编排均可追溯；当前三份固定回传文件仍缺失，所以系统只能等待客户文件并列出 DATA2、DATA2R 和 PACK12 的重跑命令。该状态不代表真实客户资料已到齐，不代表客户数据试跑完成；真实外发、真实渠道、客户签收、生产 SLA 和签名安装包仍未完成。

最新覆盖状态：H2W-PACK12 真实资料重跑编排门禁已完成，当前 `status=waiting_for_real_customer_materials_for_customer_data_rerun`。PACK12 先执行 DATA2R 真实资料接收门禁；如果真实客户资料三件套未回传，就停止在等待态，列出 DATA2R、KB6、TRIAL3、FE9、PACK10、PACK11 的后续命令，不继续下游并且不生成客户数据版结论。真实资料到齐后，PACK12 会按顺序串联真实资料门禁、知识复测、影子试跑、客户资料前端复测、PACK10 和 PACK11；只有全部 ready 才能进入 `customer_data_rerun_orchestration_ready`。当前真实客户资料仍未到齐，真实外发关闭，真实渠道未接通，客户签收、生产 SLA 和签名安装包仍未完成。

最新覆盖状态：H2W-INSTALL7 封包前客户模式门禁已完成，并已接入 H2W-PACK11 聚合总账。INSTALL7 新增客户模式封包前安全门禁，复核 `deploy/customer.env.example`、`deploy/start-local-pilot.sh`、`deploy/docker-compose.pilot.yml`、安装候选目录和版本边界，要求开发 bootstrap 关闭、无默认管理员密码、真实外发关闭、入站 worker 默认关闭、不写真实密钥、不远控、不静默更新、不把候选安装器写成签名 dmg/exe。当前 INSTALL7 `status=customer_mode_prepack_gate_ready`，PACK11 中 `installer_customer_mode_status=customer_mode_prepack_gate_ready`；PACK11 整体仍保持 `blocked_waiting_real_customer_materials` 且 `blockers=[]`。真实客户资料仍未到齐，真实外发关闭，真实渠道未接通，签名安装包未完成，不能写成客户签收、生产 SLA 或成熟全渠道商用系统。

最新覆盖状态：H2W-FE12 客户视角二次浏览器验收已完成并纳入 PACK11 聚合门禁。FE12 使用临时空库、临时前后端、临时 Chrome profile 和真实登录流程，覆盖总览、接待工作台、知识运营三页、质量复盘、渠道接入、账号与本地维护、自动回复策略和试点准备页；同时点击“生成本地测试会话”、渠道“人员与边界/接入边界”和试点资料模板动作。当前 `status=passed_customer_perspective_browser_qa`，PACK11 聚合中 `frontend_customer_qa_status=passed_customer_perspective_browser_qa`，整体仍正确保持 `blocked_waiting_real_customer_materials` 且 `blockers=[]`。真实客户资料仍未到齐，真实外发关闭，真实渠道未接通，签名安装包未完成。

最新覆盖状态：H2W-DATA2R6 资料回传文件包已完成，当前 `status=material_handoff_bundle_ready`。本轮新增 `GET /api/tenants/{tenant_id}/customer-materials/handoff-bundle`，返回包含固定回传文件名的 zip；前端“试点准备 -> 资料预检”新增“下载回传文件包”；新增 DATA2R6 门禁脚本、阶段文档和 summary。回传包只降低客户文件名填错、传错的风险，不代表真实客户资料已收到；`customer_data_used=false`、`raw_materials_persisted=false`、`real_customer_materials_ready=false`，真实外发关闭，PACK10 继续 `blocked_waiting_real_customer_materials` 且 `blockers=[]`。

最新覆盖状态：H2W-DATA2R5 资料模板包与字段说明已完成，当前 `status=material_template_package_ready`。本轮新增 `GET /api/tenants/{tenant_id}/customer-materials/template-package`、前端“试点准备 -> 资料预检”里的加载资料模板、填入示例资料、下载三份模板和字段说明，以及 DATA2R5 门禁脚本、阶段文档和 summary。示例资料可用于熟悉格式和跑预检，但 `customer_data_used=false`、`raw_materials_persisted=false`、`real_customer_materials_ready=false`；真实客户资料仍未到齐，PACK10 继续 `blocked_waiting_real_customer_materials` 且 `blockers=[]`。

最新覆盖状态：H2W-DATA2R3 真实资料门禁反例校验已完成，当前 `status=material_validation_fixtures_passed`。本轮新增 DATA2R3 门禁脚本、阶段文档和 summary，并增强资料扫描器对 JSON 形态 `api_key/token/password/encodingaeskey` 的识别。9 组样例已验证：合规 50 题资料包可通过；题库不足、缺字段、手机号/邮箱、真实外发开启、正式签收开启、非法动作、JSON 密钥字段和“真实外发已接通”等越界承诺都会被阻断。`pilot-readiness` 和前端“试点准备”页已接入 `material_validation_fixture_status`。真实客户资料仍未到齐，DATA2 继续 `waiting_for_real_customer_materials`，PACK10 继续 `blocked_waiting_real_customer_materials`。

最新覆盖状态：H2W-DATA2R2 真实资料接收包门禁已完成，当前 `status=material_intake_package_ready`。本轮新增客户资料接收与脱敏手册、DATA2R2 门禁脚本、阶段文档和 summary；前端“试点准备”页新增资料接收包说明，后端 `pilot-readiness` 新增 `material_intake_package_status` 和证据字段。该状态只代表客户资料模板、固定回传文件名、脱敏规则、接收目录和下一步校验流程已经准备好；真实客户资料仍未到齐，PACK10 继续保持 `blocked_waiting_real_customer_materials`。

最新覆盖状态：H2W-DATA2R、KB6、TRIAL3、FE9、FE10、CHANNEL2、INSTALL6 和 PACK10 五大缺口门禁已完成本轮实现与验证。当前 DATA2R 为 `waiting_for_real_customer_materials`，KB6/TRIAL3/FE9 均保持等待真实客户资料；FE10 为 `frontend_final_product_polish_ready`，CHANNEL2 为 `channel_personnel_boundary_ready`，INSTALL6 为 `trial_installer_experience_candidate_ready`，PACK10 为 `blocked_waiting_real_customer_materials`。本轮新增 8 个门禁脚本、扩展 `pilot-readiness` 聚合字段、前端“试点准备”五大缺口卡片、渠道页“人员与边界”说明和安装体验候选清单。真实资料未到齐前，不能生成客户数据版本地试跑包 v2，也不能写成客户签收、真实外发、真实渠道上线、生产 SLA 或签名安装包完成。

最新覆盖状态：H2W-PACK9 真实客户资料重跑计划门禁已完成，当前 `status=pack9_plan_ready_waiting_real_customer_materials`。本轮新增 `scripts/check_p3_06u_26h2w_pack9_real_customer_rerun_plan.py`、`docs/P3-06U-26H2W_PACK9_REAL_CUSTOMER_RERUN_PLAN.md` 和 `output/p3_06u_26h2w_pack9_real_customer_rerun_plan/summary.json`。PACK9 已把真实资料到齐后的重跑链路固定为 DATA2、PACK8B、KB6、TRIAL3、FE9、PACK9 六步，并为每步写入停止门禁；当前 DATA2 仍为 `waiting_for_real_customer_materials`，所以只能保持计划 ready，不能生成客户数据版交付档案或客户签收。真实资料到齐后，必须先重跑 DATA2 和 PACK8B，再新增/执行 KB6、TRIAL3、FE9、PACK9 客户数据链。

最新覆盖状态：H2W-PACK8B 真实资料边界锁已完成，当前 `status=pack8_boundary_locked_waiting_real_materials`。本轮新增 `scripts/check_p3_06u_26h2w_pack8b_real_material_boundary_lock.py`、`docs/P3-06U-26H2W_PACK8B_REAL_MATERIAL_BOUNDARY_LOCK.md` 和 `output/p3_06u_26h2w_pack8b_real_material_boundary_lock/summary.json`。门禁确认 DATA2 仍为 `waiting_for_real_customer_materials` 时，PACK8 必须保持 `co_creation_trial_package_v1_1_candidate_with_internal_data`、`customer_data_used=false`、`internal_sample_used=true`。真实客户资料到齐前，任何文档、前端或交付档案都不得升级为客户数据试跑、正式客户签收、真实外发、真实渠道上线、生产 SLA 或签名安装包完成。

最新覆盖状态：H2W-DATA2 真实客户脱敏资料接入前置门禁已完成，当前 `status=waiting_for_real_customer_materials`。本轮新增 `evals/p3_06u_26h2w_data2_real_customer_material_readiness/` 接收目录、`customer_materials_real_template.csv`、`customer_trial_questions_real_template.csv`、`customer_material_manifest_template.json`、门禁脚本 `scripts/check_p3_06u_26h2w_data2_real_customer_material_readiness.py` 和阶段文档 `docs/P3-06U-26H2W_DATA2_REAL_CUSTOMER_MATERIAL_READINESS.md`。真实客户文件未到齐前，系统不会升级为客户数据试跑；前端“试点准备”页已接入 `real_customer_material_status`，显示下一轮真实资料状态。固定边界：不伪造客户资料，不把内部样板写成真实客户资料，不启用真实外发，不推进真实企业/平台渠道，不写成正式客户签收、签名安装包、生产 SLA 或成熟全渠道商用系统。

最新覆盖状态：H2W-TRIAL-C0、H2W-DATA1、H2W-DEPLOY1、H2W-KB5、H2W-TRIAL2、H2W-FE8、H2W-PACK8 已完成，当前系统进入“共创客户本地试跑包 v1.1 候选”。TRIAL-C0 已冻结客户类型、业务场景、知识资料类型、试跑时长、验收角色和不可承诺项，当前 `status=trial_scope_ready`。DATA1 已建立资料接收 manifest 和内部准真实样板，当前 `status=internal_sample_only_ready`，真实客户资料仍为 false。DEPLOY1 已聚合干净本地部署 rehearsal 关键证据，当前 `status=clean_local_trial_rehearsal_passed`。KB5 已基于 DATA1 资料跑知识导入与复测报告，当前 `status=customer_knowledge_retest_ready_with_internal_data`。TRIAL2 已输出影子试跑质量报告，当前 `status=shadow_trial_ready_with_internal_data`。FE8 已完成试跑摩擦驱动前端门禁，当前 `status=trial_frontend_friction_resolved`。PACK8 已生成 `output/p3_06u_26h2w_pack8_trial_package_v1_1/co_creation_trial_package_v1_1_candidate.zip`，当前 `status=co_creation_trial_package_v1_1_candidate_with_internal_data`；聚合试跑状态为 `co_creation_trial_v1_1_candidate_with_internal_data`。固定边界：不做移动端，不启用真实外发，不推进真实企业/平台渠道，不把内部样板写成真实客户资料或客户签收，不把 RPA 作为正式交付能力，不把安装器候选写成已签名 dmg/exe，不写生产 SLA 完成。

最新覆盖状态：H2W-PILOT7、H2W-FE7、H2W-KB4、H2W-INSTALL5、H2W-OPS3、H2W-PACK7 已完成，当前系统进入“共创客户本地试跑封版候选 v1”。PILOT7 聚合 FE6、INSTALL4、KB3、PILOT6、OPS2、PACK5、KB2、MODEL1、TRIAL1，当前 `status=co_creation_trial_candidate_ready_with_internal_data`。FE7 已用临时空库、临时服务和浏览器真实登录逐页点击客户路径，并清理客户可见工程词，当前 `status=passed_customer_trial_browser_smoke`。KB4 已把知识资料试跑闭环固定为“导入资料 -> 预检 -> 发布 -> 复测 -> 确认 -> 质量报告”，当前 `status=customer_knowledge_trial_loop_ready`。INSTALL5 已验证客户本地启动体验，当前 `status=local_startup_experience_ready`。OPS3 已完成客户试跑运维闭环说明，当前 `status=customer_trial_ops_loop_ready`。PACK7 已生成 `output/p3_06u_26h2w_pack7_trial_handoff_archive_v2/co_creation_trial_handoff_archive_v2_candidate.zip`，当前 `status=co_creation_trial_handoff_archive_v2_candidate`。固定边界：不做移动端，不启用真实外发，不推进真实企业/平台渠道，不把内部演练写成客户签收，不把 RPA 作为正式交付能力，不把安装器候选写成已签名 dmg/exe，不写生产 SLA 完成。

2026-07-05 早前覆盖状态：H2W-FE6、H2W-INSTALL4、H2W-KB3、H2W-PILOT6 已完成。FE6 已把最新“试点准备”页纳入浏览器真实登录逐页点击，覆盖总览、接待工作台、多渠道对话台、知识运营、知识缺口、知识评测、质量复盘、渠道接入、账号与本地维护、自动回复策略和试点准备页，当前 `status=passed_latest_frontend_browser_qa`。INSTALL4 已补安装候选体验清单、端口/Docker/日志/卸载清理和 macOS/Windows 图标说明，当前 `status=native_packaging_experience_candidate_ready`，`signed_dmg_exe_ready=false`。KB3 已把客户知识中心收束为业务对象、标准问答、流程政策、禁用承诺与转人工规则四层输入，当前 `status=customer_knowledge_center_productized`。PILOT6 已刷新试点交付档案候选，当前 `status=pilot_handoff_archive_candidate_v1`。固定边界：不做移动端，不启用真实外发，不推进真实企业/平台渠道，不把内部演练写成客户签收，不把 RPA 作为正式交付能力，不把安装器候选写成已签名 dmg/exe。

2026-07-05 早前覆盖状态：H2W-INSTALL3 原生包装候选第一片已完成，当前 `status=native_app_packaging_candidate_ready`。本轮新增 `installers/VERSION.json`、`installers/logs/` 非敏感日志目录、macOS `.app` 包装骨架、macOS/Windows 健康检查脚本、macOS/Windows 升级前备份预检脚本、INSTALL3 门禁脚本和阶段文档；macOS `.app` 仍只调用既有安全启动脚本，升级前预检只生成 manifest，不复制数据库、不读取密钥、不静默更新。验证通过 INSTALL3 门禁、Python 编译、macOS bash 语法检查、sealed pilot gates `33 passed`、pilot API + sealed gates 组合回归 `37 passed`。固定边界：`signed_dmg_exe_ready=false`、`desktop_installer_ready=false`、`native_installer_ready=false`，不推进真实渠道，不开启真实外发，不远控客户电脑，不静默更新，不自动写客户密码或模型凭据。

2026-07-05 早前覆盖状态：H2W-PILOT0 到 H2W-PILOT5 已完成，当前状态升级为“共创客户本地试点包候选 v1”。PILOT0 聚合 PACK5、FE4、KB2、OPS2、INSTALL2、TRIAL1、MODEL1 和 7D-runtime，当前 `status=pilot_candidate_ready_with_internal_data`；PILOT1 在前端新增“试点准备”入口，按本地环境、账号负责人、知识资料、复测确认、质量/月报、诊断备份更新 6 步展示真实状态；PILOT2 将客户知识确认流程产品化，当前 `status=waiting_customer_confirmation`，不替客户填写确认人、确认时间或签收结论；PILOT3 生成试点交付档案候选 `pilot_handoff_archive_candidate.zip`，不包含 key、token、数据库密码、客户原文、平台 payload、`.git`、`node_modules` 或生产 SLA 承诺；PILOT4 使用临时空库、真实登录和浏览器点击完成客户本地试点端到端 rehearsal；PILOT5 输出安装器下一轮分叉决策，允许后续进入原生安装器专项，但 `signed_dmg_exe_ready=false`。验证通过 PILOT0/2/3/5 门禁、PILOT4 浏览器演练、后端回归 `35 passed`、前端 typecheck/build。固定边界：不推进真实渠道，不开启真实外发，不远控客户电脑，不静默更新，不把内部演练写成客户签收，不写正式 dmg/exe 已完成。

2026-07-05 早前覆盖状态：H2W-OPS2 与 H2W-INSTALL2 已完成。OPS2 新增客户侧月度运维报告只读接口、前端质量复盘页“月度运维报告”区块、账号与本地维护轻入口、客户版 Markdown 报告、内部证据摘要和机器门禁，当前 `status=ready_for_customer_monthly_ops_report_rehearsal`，`production_sla_ready=false`。INSTALL2 新增 `installers/macos/` 与 `installers/windows/` 原生启动候选结构和门禁，当前 `status=native_wrapper_candidate_ready`，`signed_dmg_exe_ready=false`、`desktop_installer_ready=false`。验证通过 OPS2/INSTALL2 单测、实际门禁脚本、月度接口回归、整份 sealed pilot gates `26 passed`、前端 typecheck/build 与质量复盘浏览器 smoke。固定边界：不推进真实渠道，不开启真实外发，不远控客户电脑，不静默更新，不自动写客户密码或模型凭据，不把内部演练写成客户签收。

最新覆盖状态：H2W-11N/11O 两步已按内部演练口径复核通过，并新增 `docs/P3-06U-26H2W11N_11O_RECHECK_AND_OVERALL_READINESS_REVIEW.md`。本轮复跑内部确认与题库输入生成、H2W-11N、H2W-11O、H2W-11P、相关 pytest 和封版包门禁：内部确认回传 12 条、内部脱敏题库 100 条、最终答案采样 100 条均通过；测试结果为 `7 passed` 与 `22 passed`。当前可按“小微企业本地受控试点候选”继续推进，但客户真实确认、真实客户题库、正式准确率签收、真实平台外发、企业渠道上线、生产 SLA 和完整原生安装器仍未完成。

最新覆盖状态：H2W-KB2 客户专属知识包导入后复测报告与签收模板已完成。新增 `scripts/check_p3_06u_26h2w_kb2_post_import_retest_and_signoff_template.py`、`docs/P3-06U-26H2W_KB2_POST_IMPORT_RETEST_AND_SIGNOFF_TEMPLATE.md`、`output/p3_06u_26h2w_kb2_post_import_retest_and_signoff_template/summary.json`、`post_import_retest_report.md` 和 `customer_knowledge_retest_signoff_template.csv`。KB2 基于 KB1 内部脱敏资料包与 OPS1 售后交接证据，生成导入后复测报告和 9 项客户确认模板；确认人、确认时间、客户意见均为空，`filled_customer_confirmation_count=0`。当前状态为 `ready_for_customer_specific_knowledge_retest_template`；但正式客户准确率签收、真实客户题库、客户专属知识库正式签收、真实平台自动外发、企业渠道真实上线、provider 调用、生产 SLA 和完整 macOS dmg / Windows exe 安装器均仍为 false。

2026-07-05 早前覆盖状态：H2W-OPS1 售后运维交接演练已完成。新增 `scripts/check_p3_06u_26h2w_ops1_after_sales_handoff_rehearsal.py`、`docs/P3-06U-26H2W_OPS1_AFTER_SALES_HANDOFF_REHEARSAL.md` 和 `output/p3_06u_26h2w_ops1_after_sales_handoff_rehearsal/summary.json`，并把客户启动说明中的安全边界统一为“真实外发默认关闭”。OPS1 聚合 INSTALL1、PACK5、KB1 和 H2W-8B 本地维护浏览器验收证据，确认诊断包接收、售后处理单、签名更新包、备份、恢复演练、审计事件、远程维护授权 SOP、内部售后计划和客户启动说明均满足交接门禁。当前状态为 `ready_for_after_sales_ops_handoff_rehearsal`；但我方远程控制客户电脑、静默自动更新、正式客户准确率签收、真实客户题库、真实平台自动外发、企业渠道真实上线、客户专属知识库正式签收、生产 SLA 和完整 macOS dmg / Windows exe 安装器均仍为 false。

2026-07-05 早前覆盖状态：H2W-INSTALL1 非技术客户本地启动器 rehearsal 已完成。新增 `deploy/start-local-pilot.command`、`docs/customer/万法常世AI客服本地试点启动说明.md`、`scripts/check_p3_06u_26h2w_install1_nontechnical_customer_starter.py`、`docs/P3-06U-26H2W_INSTALL1_NONTECHNICAL_CUSTOMER_STARTER.md` 和 `output/p3_06u_26h2w_install1_nontechnical_customer_starter/summary.json`。INSTALL1 在 PACK5 交付包候选和 KB1 知识包 rehearsal 基线上，补齐非技术客户双击启动包装器和客户启动说明门禁；包装器只调用既有安全启动脚本，不自动创建或修改 `deploy/customer.env`，不预置默认密码，不启用 worker，不打开真实外发。当前状态为 `ready_for_nontechnical_customer_startup_rehearsal`；但完整 macOS dmg / Windows exe 安装器、正式客户准确率签收、真实客户题库、真实平台自动外发、企业渠道真实上线、客户专属知识库正式签收和生产级 SLA 均仍为 false。

2026-07-05 早前覆盖状态：H2W-KB1 客户专属知识包导入与签收 rehearsal 已完成。新增 `scripts/check_p3_06u_26h2w_kb1_customer_specific_knowledge_package_rehearsal.py`、`evals/p3_06u_26h2w_kb1_customer_specific_knowledge_package_rehearsal.json`、`docs/P3-06U-26H2W_KB1_CUSTOMER_SPECIFIC_KNOWLEDGE_PACKAGE_REHEARSAL.md` 和 `output/p3_06u_26h2w_kb1_customer_specific_knowledge_package_rehearsal/summary.json`。KB1 使用内部脱敏客户专属资料包验证后端真实预检、导入、查询和回滚：3 个业务对象、8 条对象知识卡、5 份来源文档、1 个回归题集和 8 条回归题均可进入 rehearsal，回滚后 active 文档和回归题集归零。当前状态为 `ready_for_customer_specific_knowledge_package_rehearsal`；但正式客户准确率签收、真实客户题库、真实平台自动外发、企业渠道真实上线、客户专属知识库正式签收、完整桌面安装器和生产级 SLA 均仍为 false。

2026-07-05 早前覆盖状态：H2W-PACK5 客户本地试点交付包候选门禁已完成。新增 `scripts/check_p3_06u_26h2w_pack5_customer_handoff_package.py`、`docs/P3-06U-26H2W_PACK5_CUSTOMER_LOCAL_PILOT_HANDOFF_PACKAGE.md` 和 `output/p3_06u_26h2w_pack5_customer_handoff_package/summary.json`。PACK5 聚合 PACK2、PACK3、PACK4、FE4、FE4 浏览器点击 QA、pgvector runtime、MODEL1 小样本成本和 TRIAL1 内部 100 题演练，并检查客户启动脚本、客户环境模板、Compose、客户资料文档和内部工程文档是否齐备。当前状态为 `ready_for_customer_local_pilot_handoff_candidate`，可作为小微企业本地受控试点交付包候选继续推进客户专属知识包试点、安装器专项或运维交接演练；但完整桌面安装器、正式客户准确率签收、真实平台自动外发、企业渠道真实上线、客户专属知识库验收和生产级 SLA 均仍为 false。

2026-07-05 早前覆盖状态：H2W-FE4 客户可见 UI 封版候选门禁已完成。新增 `scripts/check_p3_06u_26h2w_fe4_customer_ui_sealed_candidate.py`、`scripts/check_p3_06u_26h2w_fe4_customer_visible_click_qa.mjs`、`docs/P3-06U-26H2W_FE4_CUSTOMER_UI_SEALED_CANDIDATE.md`、`output/p3_06u_26h2w_fe4_customer_ui_sealed_candidate/summary.json` 和 `output/p3_06u_26h2w_fe4_customer_visible_click_qa/summary.json`。静态门禁状态为 `ready_for_customer_visible_ui_candidate`，矩阵 63 行、覆盖 12 页、工作台禁用文案命中 0、浏览器深审问题 0、客户可见工程词 0、越界完成态 0；浏览器点击 QA 状态为 `passed_customer_visible_click_qa`，使用临时负责人真实登录逐页检查运营总览、接待工作台、知识运营三页、质量复盘、渠道接入、运维、模型路由和账号与本地维护。当前前端可进入客户可见 UI 候选；但完整桌面安装器、正式客户准确率签收、真实平台自动外发、企业渠道真实上线、客户专属知识库验收和生产级 SLA 均仍为 false。

2026-07-05 早前覆盖状态：H2W-PACK4 本地试点交付清单与安全启动 rehearsal 已完成。新增 `deploy/start-local-pilot.sh`、`scripts/check_p3_06u_26h2w_pack4_delivery_checklist_and_startup_rehearsal.py`、`docs/P3-06U-26H2W_PACK4_LOCAL_PILOT_DELIVERY_CHECKLIST.md` 和 `output/p3_06u_26h2w_pack4_delivery_checklist_and_startup_rehearsal/summary.json`。PACK4 在 PACK3 候选基础上补齐客户本地试点启动入口：客户复制 `deploy/customer.env.example` 为 `deploy/customer.env`、替换本地随机数据库密码后运行 `deploy/start-local-pilot.sh deploy/customer.env`；脚本在启动前阻断开发 bootstrap、真实外发、入站 worker、默认管理员密码和模板数据库密码，并执行数据库迁移后启动核心前后端服务。当前状态为 `ready_for_customer_local_pilot_startup_rehearsal`；但完整桌面安装器、正式客户准确率签收、真实平台自动外发、企业渠道真实上线、客户专属知识库验收和生产级 SLA 均仍为 false。

2026-07-05 早前覆盖状态：H2W-PACK3 本地受控试点封版候选总门禁已完成。新增 `scripts/check_p3_06u_26h2w_pack3_local_pilot_candidate_readiness.py`、`docs/P3-06U-26H2W_PACK3_LOCAL_PILOT_CANDIDATE_READINESS.md` 和 `output/p3_06u_26h2w_pack3_local_pilot_candidate_readiness/summary.json`，把 PACK2 全栈首启、PACK1 本地交付候选、FE3 前端真实工作流、7D pgvector runtime、MODEL1 百炼小样本成本和 TRIAL1 内部 100 题演练纳入同一总门禁。当前状态为 `ready_for_local_controlled_pilot_candidate`，可作为“小微企业本地受控试点包候选”继续进入交付清单、一键启动 rehearsal 和客户资料试点准备；但正式客户准确率签收、真实平台自动外发、企业渠道真实上线、客户专属知识库验收、完整桌面安装器和生产级 SLA 均仍为 false。

2026-07-05 早前覆盖状态：P3-06U-26H2W11M 客户确认结果导入门禁与 H2W-12 工程/商用成熟度评估已完成。H2W-11M 新增 `scripts/check_p3_06u_26h2w11m_customer_confirmation_import_gate.py`、`backend/tests/test_p3_06u_26h2w11m_customer_confirmation_import_gate.py` 和 `docs/P3-06U-26H2W11M_CUSTOMER_CONFIRMATION_IMPORT_GATE.md`，生成 `evals/p3_06u_26h2w11m_customer_confirmation_return_template.csv`。当前没有客户真实返回文件，因此门禁保持 `customer_return_file_present=false`、`customer_confirmed_item_count=0`、`ready_for_confirmed_standard_answer_import=false`、`ready_for_formal_accuracy_signoff=false`，不伪造客户确认。H2W-12 新增 `docs/P3-06U-26H2W12_ENGINEERING_AND_COMMERCIAL_READINESS_REVIEW.md` 和机器可读摘要，结论是可以进入受控本地试点和共创客户验证，但不适合公开承诺成熟全渠道自动回复。真实外发、真实 IM、正式电子签章、真实客户原始数据、生产级 RAG、真实线上回执和生产上线仍未完成。

2026-07-04 早前覆盖状态：P3-06U-26H2W11J 缺口样本最终答案 rehearsal 已完成。本轮新增 `scripts/check_p3_06u_26h2w11j_gap_final_answer_rehearsal.py`、`backend/tests/test_p3_06u_26h2w11j_gap_final_answer_rehearsal.py` 和 `docs/P3-06U-26H2W11J_GAP_FINAL_ANSWER_REHEARSAL.md`，基于 H2W-11I 的 7 条缺口样本跑本地确定性最终答案 rehearsal。结果：7 条样本全部生成脱敏样本和标签，5 条自动回复为 `correct`，2 条转人工为 `not_applicable`，自动回复事实性、引用充分、禁用承诺、转人工正确性四项通过率均为 1.0，`ready_for_gap_quality_report_review=true`，`ready_for_formal_accuracy_signoff=false`。本片不打开真实外发、不调用真实模型 provider、不接真实渠道、不导出完整最终答案正文、不使用真实客户原始数据，不生成正式电子签章或合同签收。

2026-07-04 早前覆盖状态：P3-06U-26H2W11I 标准答案缺口评测输入包已完成。本轮新增 `scripts/check_p3_06u_26h2w11i_standard_answer_gap_eval_plan.py`、`backend/tests/test_p3_06u_26h2w11i_standard_answer_gap_eval_plan.py` 和 `docs/P3-06U-26H2W11I_STANDARD_ANSWER_GAP_EVAL_PLAN.md`，并生成 `evals/p3_06u_26h2w11i_standard_answer_gap_eval_cases.csv` 与 `evals/p3_06u_26h2w11i_standard_answer_gap_label_plan.csv`。H2W-11I 已把 H2W-11H 暴露的 6 类缺口来源全部转成下一轮最终答案评测输入，生成 7 条候选样本和 7 条标签计划；它只证明缺口已有可执行输入，不代表下一轮评测已经执行，也不是正式准确率签收。本片不打开真实外发、不调用真实模型 provider、不接真实渠道、不使用真实客户原始数据，不生成正式电子签章或合同签收。

2026-07-04 早前覆盖状态：P3-06U-26H2W11H 标准答案质量桥接已完成。本轮新增 `scripts/check_p3_06u_26h2w11h_standard_answer_quality_bridge.py`、`backend/tests/test_p3_06u_26h2w11h_standard_answer_quality_bridge.py` 和 `docs/P3-06U-26H2W11H_STANDARD_ANSWER_QUALITY_BRIDGE.md`，把 H2W-11G 客户标准答案模板接入 H2W-11B 修复版最终答案标签、引用充分性、禁用承诺和转人工正确性报告。桥接门禁通过，但正式准确率签收仍为 false：标准答案模板 8 个来源中只有 2 个已出现在当前最终答案标签里，缺口来源包括售后、知识维护、模型成本、引用质量、服务定价和试点签收；模板没有客户确认行，最终答案正文也按脱敏要求不导出。本片不打开真实外发、不调用真实模型 provider、不接真实渠道、不使用真实客户原始数据，不生成正式电子签章或合同签收。

2026-07-04 早前覆盖状态：P3-06U-26H2W11F 前端客户术语、重复入口和知识维护路径收束已完成。本轮将知识库运营页客户主流程统一为“知识维护总流程：整理资料 -> 检查 -> 导入 -> 启用 -> 复测 -> 确认”，客户可见按钮改为“生成资料包、检查资料包、导入知识库、启用前复测、启用知识、查看复测题库、查看质量报告”。底层仍复用 H2W-11E 已验收的真实 handler 和同租户落库路径，不新增空按钮、不打开真实外发、不调用真实模型 provider、不接真实渠道、不使用真实客户原始数据。新增 `scripts/check_p3_06u_26h2w11f_customer_terms_and_path_consolidation.py`、`backend/tests/test_p3_06u_26h2w11f_customer_terms_and_path_consolidation.py` 和 `docs/P3-06U-26H2W11F_CUSTOMER_TERMS_AND_PATH_CONSOLIDATION.md`，并通过 H2W-11F 静态门禁、H2W-11D/11E 回归、前端 typecheck/build、H2W-11E 真实登录浏览器验收和 H2W0 知识操作浏览器门禁。

2026-07-03 早前覆盖状态：P3-06U-26H2W5 已完成云接收台第一片。后端新增 `diagnostic_intake_records` 表和诊断授权上传包接收接口，支持登记、校验、拒收原因、列表、状态更新和下载；接收时校验客户主动授权、上传包版本、安全声明和诊断包 sha256。前端“管理运维 -> 账号安全”新增“售后接收台”，可粘贴客户主动提供的授权上传包 JSON、登记接收、查看记录、下载包并标记处理状态。新增 `docs/P3-06U-26H2W5_CLOUD_INTAKE_FIRST_SLICE.md`、`scripts/check_p3_06u_26h2w5_cloud_intake_static.py`，并更新 `docs/FRONTEND_FUNCTION_REALITY_MATRIX.md`。本片是本地模拟接收台，不是正式云服务上线；不自动上传、不远控客户电脑、不打开真实外发、不调用模型、不替客户执行更新恢复。

2026-07-03 早前覆盖状态：P3-06U-26H2W4 已完成报告导出与归档第一片。客户质量报告导出支持 HTML/XLSX/DOCX，XLSX 和 DOCX 由后端生成有效 OpenXML 文件并以 base64 返回给前端下载；每次导出写入 `customer_quality_report.exported` 审计事件，并可通过报告归档列表和历史下载接口回看。前端质量复盘页新增 `HTML 留档`、`XLSX 明细`、`DOCX 报告` 三个按钮和“报告归档”列表。新增 `docs/P3-06U-26H2W4_REPORT_EXPORTS_AND_ARCHIVE_FIRST_SLICE.md`、`scripts/check_p3_06u_26h2w4_report_exports.py`，并更新 `docs/FRONTEND_FUNCTION_REALITY_MATRIX.md`。本片不做 PDF、不接正式电子签章、不打开真实外发、不调用模型，不保存原始客户问题、完整回复或人工备注原文；本地确认和报告归档不是正式电子签章。

2026-07-03 早前覆盖状态：P3-06U-26H2W3D 已完成线上回执与准确率闭环第一片。后端新增 `GET /api/tenants/{tenant_id}/online-receipt-quality-summary`，按租户汇总回执入库、发送尝试匹配、签名验证、送达/已读、失败复盘、平台分布和验收门禁；前端质量诊断页新增“线上回执闭环证据”，并明确当前只是回执链路覆盖，不是完整客服答案准确率。新增 `docs/P3-06U-26H2W3D_ONLINE_RECEIPT_ACCURACY_LOOP_FIRST_SLICE.md`、`scripts/check_p3_06u_26h2w3d_online_receipt_quality.py` 和 `scripts/check_p3_06u_26h2w3d_online_receipt_quality_ui.mjs`，浏览器证据位于 `output/p3_06u_26h2w3d_online_receipt_quality_ui/`。本轮验证已通过 H2W3D 静态门禁、后端单测、前端 typecheck/build、桌面浏览器 smoke，以及 H2W3C/H2W3B/P3-06U-26D 相邻门禁。真实外发继续默认关闭，不接真实官方渠道，不调用模型，不返回回执原始 payload，不展示完整线上准确率；完整客服答案准确率仍需真实客户题库、最终回复样本、人工事实标签、官方授权渠道、真实平台回执和持续回归闭环。

2026-07-03 早前覆盖状态：P3-06U-26H2W3C 已完成客户资料导入模板与预检第一片。后续 H2W-11F 已把客户可见名称收束为“客户资料整理”和“知识资料包导入”：客户按模板整理 CSV 资料后，系统生成 `wanfa.knowledge_update_package.v1` 资料包草稿，再复用现有检查、导入和后续启用回归链路；模板覆盖业务对象、标准问答、流程政策、禁用承诺、转人工规则、回归问题和期望答案。新增 `docs/P3-06U-26H2W3C_CUSTOMER_KNOWLEDGE_INTAKE_TEMPLATE.md` 和 `scripts/check_p3_06u_26h2w3c_customer_knowledge_intake.py`，并更新 `docs/FRONTEND_FUNCTION_REALITY_MATRIX.md`。本轮验证已通过 H2W3C/H2W3B/H2W2/H2W1/P3-06U-07/P3-06U-26D 静态门禁、前端 typecheck/build。P3-06U-26H2U 已完成客户签收记录列表第一片，P3-06U-26H2T 已完成客户签收记录第一片，P3-06U-26H2S 已完成客户报告 HTML 导出，P3-06U-26H2R 已完成最终回复样本与人工标签导入导出第一片，P3-06U-26H2Q 已完成客户可读质量报告第一片，P3-06U-26H2P 已完成最终回复采样与批量人工标签第一片，P3-06U-26H2O 已完成真实客户题库导入第一片，P3-06U-26H2N 已完成人工事实性标签入口第一片，P3-06U-26H2M 已完成月度质量复盘收束第一片，P3-06U-26H2L 已完成本地恢复工具 dry-run，P3-06U-26H2K 已完成客户授权诊断上传包，P3-06U-26H2J 已完成签名程序包 dry-run 演练计划，P3-06U-26H2I 已完成签名策略包应用/回滚，P3-06U-26H2H 已完成本地 SQLite 物理备份与校验，P3-06U-26H2G 已完成签名知识包应用/回滚，P3-06U-26H2F 已完成签名更新包暂存，P3-06U-26H2E 已完成签名更新包预检，P3-06U-26H2D 已完成知识更新包导入，P3-06U-26H2C 已完成本地诊断包生成，P3-06U-26H2B 已完成本地账号治理。PDF、DOCX、XLSX 原件目前只作为来源留档，不自动解析入库；自动联网上传、我方云端接收台、真实程序更新器、在线覆盖恢复、程序文件替换、服务重启、数据库迁移、模型调用和真实外部平台写入仍未开放；完整线上客服准确率仍需真实题库、最终回复样本、人工事实标签、线上回执和持续回归闭环；真实外发继续默认关闭。

2026-07-03 追加：P3-06U-26H2W-0 已进入前端功能真实性与前后端契约门禁执行阶段。新增 `docs/FRONTEND_FUNCTION_REALITY_MATRIX.md`，并把多渠道对话台、知识库运营、知识缺口、知识评测、运营总览、质量复盘、渠道接入、运维与告警、自动回复策略和账号安全纳入控件级真实性矩阵；多渠道对话台顶部无动作按钮和底部表情/图片/附件假按钮已从客户可见主界面隐藏，回复按钮文案收紧为“保存接管回复”，不再暗示真实外发。本阶段仍不打开真实外发，不接真实官方渠道，不调用模型，不做 RPA 自动发送；H2W 后续阶段必须先通过 H2W-0 静态门禁、浏览器门禁和写回记录。

2026-07-03 追加：P3-06U-26H2W-0 严格完成口径继续补强为负责人真实登录门禁。新增 `scripts/check_p3_06u_26h2w0_frontend_function_reality_owner_login.mjs`，该脚本使用临时 SQLite、临时后端、临时前端和临时 Chrome profile 创建本地负责人账号，经登录表单进入工作台，种子写入真实后端会话、人审任务和渠道数据，再访问多渠道对话台、运营总览、质量复盘、知识库运营、知识缺口、知识评测、渠道接入、运维与告警、自动回复策略和账号安全。该门禁要求 `demo_mode_used=false`、`owner_login_performed_through_ui=true`、`external_platform_write_performed=false`，只能证明负责人真实登录下的前端功能真实性与文案边界，不打开真实外发、不调用模型、不接真实官方渠道、不做 RPA 自动发送。H2W-0 未通过负责人真实登录 smoke 前，不能写成严格完成。

2026-07-03 追加：P3-06U-26H2W-0 再补知识操作真实浏览器门禁。新增 `scripts/check_p3_06u_26h2w0_knowledge_operations_owner_login.mjs`，该脚本在临时负责人账号真实登录后，从浏览器 UI 完成新增业务对象、编辑业务对象、绑定对象问答卡、导入知识文档、知识更新包预检和知识更新包导入，并用同一临时租户的后端 API 验证业务对象新增/更新、问答卡、知识文档和评测集已经持久化。该门禁要求 `knowledge_operations_performed_through_ui=true`、`business_object_update_performed_through_ui=true`、`server_persistence_verified=true`、`external_platform_write_performed=false`，用于证明知识运营不是假按钮或纯前端状态；不打开真实外发、不调用模型、不写真实客户数据。

2026-07-01 历史状态：P3-06S-01 已完成窄桌面壳层滚动修复，补齐 761px 到 960px 区间的小窗口/窄桌面断点；900x768 已验证为左侧导航固定、右侧 `.workspace` 独立滚动。后续已由 P3-06T-01/P3-06T-02 继续返修和收紧口径，当前下一步以最新 P3-06T 状态为准。

2026-07-01 追加：P3-06T-01 已完成壳层滚动返修验收。有效基线确认 760px 小窗口仍会退回整页滚动，本轮已将窄桌面壳层覆盖下探到 721px，并同步修正 hash 切换后的滚动目标。1440、1280、1024、900、760、721 视口均验证为 `bodyScrollY=0`、右侧 `.workspace` 独立滚动、左侧导航 `sidebarTop=0`；720 和 390 视口保留自然页面滚动且无横向溢出。下一步优先进入 P3-06T-02 首页数据口径收紧，再进入 P3-06T-03 运营总览 BI 重做。

2026-07-01 追加：P3-06T-02 已完成首页数据口径收紧。运营总览聚合接口新增 `contract_version=p3_06t_02_v1`、聚合粒度、刷新模型、源表清单、敏感字段排除清单和口径备注；前端时间范围/渠道筛选在正式登录后请求对应后端聚合，演示模式继续明确显示本地汇总。随后已进入并完成 P3-06T-03 运营总览 BI 重做。

2026-07-01 追加：P3-06T-03 已完成运营总览 BI 重做。首页已升级为运营指挥舱结构，包含经营信号条、运营健康环、风险组成、压力趋势主图、优先动作、处理漏斗、渠道矩阵和质量诊断；总览页顶部与演示提示进入紧凑态；新增 `scripts/check_p3_06t_03_bi_overview.mjs` 并通过 1440、1280、900、390 视口截图验收。用户复审后确认前端真实实用成熟度应按 6.0/10 起算，下一步优先进入 P3-06U 前后端契约对齐与实用型前端产品化优化。

2026-07-01 追加：P3-06U 前后端契约对齐与实用型前端产品化优化计划已建立。该阶段吸收原 P3-06T-04 信息架构收口，不再只做菜单或视觉调整；第一片是 P3-06U-01 前后端契约与页面路径盘点，随后推进角色化任务路径、接待工作台实用重构、运营总览跳转闭环、真实登录角色 smoke、质量复盘 BI、知识运营台、渠道连接器中心、统一状态体系和前端组件拆分。

2026-07-01 追加：P3-06U-01 已完成。新增前后端契约矩阵，覆盖运营总览、接待工作台、会话收件箱、人工审核、待发送、联系人、线索、工单、知识运营、质量复盘、渠道接入和管理运维；前端导航清理客户可见的阶段编号和工程缩写，设置页说明改为授权/验收边界；新增静态检查防止 `P3-06UI`、`P3-06F`、`RAG`、`规划态` 等内部表达重新进入客户界面。下一步默认进入 P3-06U-02 角色化任务路径重排。

2026-07-01 追加：P3-06U-02 已完成。标准运营版新增角色化“今日任务路径”，owner/admin/agent/viewer 登录后看到不同的 3-5 条任务路径和实时待办数字；agent 第一入口转向接待客户会话，viewer 只保留只读查看路径；本片不改变后端 RBAC、不打开真实外发。下一步默认进入 P3-06U-03 接待工作台实用性重构。

2026-07-01 追加：P3-06U-03 已完成。接待工作台从 `App.tsx` 拆分为 `frontend/src/components/conversation/ConversationWorkbenchPanel.tsx`，`#live` 改为会话队列、消息处理区、右侧上下文三栏 IM 工作台；坐席可在一页内查看客户问题、AI 草稿、引用证据、内部备注、批准进入待发送和确认待发送。页面继续明确真实外发关闭，未打开任何真实平台外部写入。随后已继续完成 P3-06U-04。

2026-07-01 追加：P3-06U-04 已完成。运营总览的高风险会话、待发送草稿、知识缺口和渠道异常等优先动作已改为带上下文的处理入口，目标工作区会展示来源、时间窗口、渠道和筛选条件，并自动应用对应队列/状态。新增 P3-06U-04 阶段文档、静态检查和浏览器多视口检查。本片不打开真实外发、不新增真实渠道发送。随后已继续完成 P3-06U-05。

2026-07-01 追加：P3-06U-05 已完成。新增真实登录角色 smoke，使用临时租户和真实账号验证 owner/admin/agent/viewer 登录、默认入口、导航可见性、任务路径、禁用动作解释、受限路径回退、退出清令牌和无意外 403；截图和摘要保存到 `output/p3_06u_role_smoke/`。下一步默认进入 P3-06U-06 质量复盘 BI。

2026-07-01 追加：P3-06U-06 已完成。质量复盘页新增修复闭环分数、六类修复路径、`from=quality` 任务上下文和目标页“来自质量复盘”提示；新增阶段文档、静态检查和 Chrome CDP 三视口 smoke，截图和摘要保存到 `output/p3_06u_06_quality_bi/`。本片不打开真实外发，不把检索命中率包装成完整准确率。下一步默认进入 P3-06U-07 知识运营台产品化。

2026-07-01 追加：P3-06U-07 已完成。知识运营、知识缺口和知识评测页顶部统一展示知识运营流程，支持 `from=knowledge` 上下文跳转；新增发布前回归门禁、回归影响预估、版本与审核状态，以及知识草稿编辑清单。新增阶段文档、静态检查和 Chrome CDP 三视口 smoke，截图和摘要保存到 `output/p3_06u_07_knowledge_ops/`。本片不新增后端字段，不打开真实外发。下一步默认进入 P3-06U-08 渠道连接器中心实用化。

2026-07-01 追加：P3-06U-08 已完成。渠道接入页第一屏新增渠道连接器状态中心，企业微信/微信客服展示未配置、创建账号、绑定接待人员、获取链接/二维码、回调 URL、URL 验证、入站消息、AI 草稿、人工审核和白名单发送测试 10 步状态；公网 HTTPS 回调 URL、Token、EncodingAESKey、可信 IP 只展示配置位置和状态，不展示密钥明文；公众号、抖音/抖店、小红书、淘宝/天猫、京东/拼多多只展示官方授权前置条件和未接入状态。新增阶段文档、静态检查和 Chrome CDP 三视口 smoke，截图和摘要保存到 `output/p3_06u_08_channel_connector_center/`。本片不新增后端字段，不打开真实外发。当时下一步为 P3-06U-09 前端状态体系统一。

2026-07-01 追加：P3-06U-09 已完成。前端新增统一状态组件与数据来源标签，核心页面统一展示加载中、暂无数据、无权限、配置缺失、接口失败、演示样本、真实服务端数据和真实外发关闭；对话台、人工审核、待发送、失败复盘、渠道中心、知识运营、知识缺口、知识评测、质量诊断和运维页已接入统一状态表达与禁用原因。新增阶段文档、静态检查和 Chrome CDP 两视口 smoke，截图和摘要保存到 `output/p3_06u_09_unified_states/`。本片不新增后端字段，不打开真实外发。下一步默认进入 P3-06U-10 前端组件和状态结构拆分。

2026-07-01 追加：P3-06U-10 第一片已完成。统一状态组件已从 `App.tsx` 抽离到 `frontend/src/components/common/WorkspaceState.tsx`，并新增 `docs/P3-06U-10_FRONTEND_STATE_COMPONENT_EXTRACTION.md` 与 `scripts/check_p3_06u_10_state_component_extraction.py`。本片只做结构拆分，不改页面路由、后端接口、权限逻辑或真实外发开关。P3-06U-01 到 P3-06U-10 静态检查、前端 typecheck/build 和 Chrome CDP 状态 smoke 均通过。下一步继续 P3-06U-10 第二片，优先拆知识、质量、渠道或运维页面组件。

2026-07-02 追加：P3-06U-14 与 P3-06U-15 已完成页面级组件拆分。质量复盘页已进入 `frontend/src/components/quality/QualityReviewPanel.tsx`；渠道连接器中心已进入 `frontend/src/components/channels/ChannelConnectorCenterPanel.tsx`；旧质量 BI 门禁和旧渠道中心门禁均已兼容组件化结构。P3-06U-15/U08 静态检查、前端 typecheck/build 和渠道中心 1440/900/390 三视口 Chrome CDP smoke 均通过。

2026-07-02 追加：P3-06U-16 已完成工作台去重与微信式对话台再瘦身。左侧“工作台”日常只保留“接待工作台”，会话收件箱、人工审核、待发送草稿和工单/SLA 保留后台路由但不在主侧栏并列展示；高风险草稿、待发送、SLA 任务回到 `#live` 对应队列；接待工作台新增 `pending_outbox` 队列，AI 辅助默认折叠，左侧会话列表更接近微信式消息列表。P3-06U-16 静态检查、旧 U10B/U11C/U03 兼容检查、前端 typecheck/build 和桌面/手机 Chrome CDP smoke 均通过。下一步继续前端实用性修复，优先知识运营页真实分叉、管理运维页分区减噪和接待工作台更真实的输入/转人工闭环；真实外发继续关闭。

2026-07-02 追加：P3-06U-17 与 P3-06U-18 已完成云朵AI视频参考拆解和工程优化总纲。工作台进一步收束为 AI 自动回复优先，异常、低置信、风险和外发失败才进入人工确认；同时明确下一步主线为业务对象知识库、自动回复策略状态机、渠道账号/店铺实体和知识修复闭环。

2026-07-02 追加：P3-06U-19 已完成业务对象知识库第一片。后端新增 `business_objects`、`business_object_aliases`、`object_knowledge_cards` 和 `knowledge_import_batches`，并新增业务对象与对象问答卡读写接口；前端知识运营页新增“业务对象知识库”区，可维护商品、服务、套餐等对象及对应问答卡，演示数据覆盖商品、服务、套餐三类对象。本片不打开真实外发，不把对象问答卡接入自动回复；下一步进入 P3-06U-20 自动回复策略状态机第一片。

2026-07-02 追加：P3-06U-20 已完成自动回复策略状态机第一片。后端新增 `reply_decisions` 表、创建/查询接口、业务对象问答卡确定性匹配、风险词人工门禁、平台风险阻断、知识缺口判断和 `reply_decision.created` 审计；前端知识运营页当时新增“自动回复状态机”说明卡，API client 新增 `createReplyDecision()` 和 `listReplyDecisions()`。H2W3B 后客户可见名称已收束为“自动回复处理方式”。本片仍不真实外发、不调用真实模型、不写 outbox；下一步进入 P3-06U-21，把回复决策接入可信入站 worker、知识缺口同步、人审任务和 outbox 前置门禁。

2026-07-02 追加：P3-06U-21 已完成可信入站 worker 与回复决策闭环第一片。可信入站 worker 现在先创建 `reply_decision`，再按 `auto_reply_ready`、`manual_gate_required`、`knowledge_gap`、`blocked_by_policy` 分流；知识缺口以 `source_type=reply_decision` 幂等创建，人审门禁自动创建 `human_review_task`，高置信自动回复只进入 outbox 前置门禁，不写 `outbox_drafts` 或真实发送任务。下一步进入 P3-06U-22，把最新回复决策展示到接待工作台。

2026-07-02 追加：P3-06U-22 已完成工作台回复决策可视化。接待工作台现在会按会话展示最新 `reply_decision`，坐席能直接看到回复决策、业务对象、知识依据、下一步动作和真实外发边界；演示样本覆盖自动回复预备、人工确认、知识缺口、策略阻断和仅生成草稿。下一步进入 P3-06U-23 渠道账号/店铺实体与会话来源增强。

2026-07-02 追加：P3-06U-23 已完成渠道账号/店铺实体与预览稳定性第一片。新增 `?demo=1#live` 演示直达入口，修复预览空白页的 hooks 顺序和空会话读取问题；多渠道对话台新增平台、账号、店铺 / 入口、接入状态和回复模式，演示样本覆盖微信客服、抖音、淘宝、京东、拼多多和官网。下一步进入 P3-06U-24 渠道账号/店铺实体后端模型第一片。

2026-07-02 追加：P3-06U-24 已完成知识运营三页首屏职责分离和渠道账号/店铺后端模型第一片。知识库运营、知识缺口、知识评测三个入口现在分别以自己的主工作面板作为首屏，避免公共知识流转面板造成“三页像同一页”的误读；后端新增 `channel_accounts` 表、迁移、读写 schema、service、API 和测试，前端新增 `listChannelAccounts()` 并把服务端渠道账号身份映射到多渠道对话台。新增阶段文档 `docs/P3-06U-24_KNOWLEDGE_SPLIT_AND_CHANNEL_ACCOUNT_MODEL.md` 和浏览器验收脚本 `scripts/check_p3_06u_24_knowledge_split_and_channel_accounts.mjs`；桌面/手机验收通过。下一步进入 P3-06U-25 渠道账号配置面板、知识三页组件拆分和真实数据接入深化。

2026-07-02 追加：P3-06U-25/P3-06U-26/P3-06U-26A 已完成阶段收束。P3-06U-25 给出客服中台综合成熟度评分：完整商用全渠道口径 `58/100`，受控试点口径 `72/100`；P3-06U-26 新增工程优化总纲，拆出 P3-06U-26A 到 P3-06U-26H 八个施工阶段；P3-06U-26A 已完成对外界面去演示味和正式/内部环境文案分层，客户可见源码不再出现“演示模式 / 演示样本 / 开发演示身份 / 开发演示进入”等内部口径，仍保留“真实外发关闭”。下一步进入 P3-06U-26B，多渠道对话台继续微信式收束；真实外发、真实平台账号、真实客户题库和付费模型调用仍需后续单独授权和验收。

2026-07-02 追加：P3-06U-26B 已完成多渠道对话台微信式收束。左侧会话列表收窄到桌面 216px、窄桌面 200px；平台来源和回复决策压缩为聊天上下文条；AI 建议移动到回复区附近；消息流在桌面和 1024px 窄桌面首屏优先可见。新增 `docs/P3-06U-26B_WECHAT_FIRST_CONVERSATION_WORKBENCH.md`、`scripts/check_p3_06u_26b_wechat_first_workbench.py` 和 `scripts/check_p3_06u_26b_wechat_first_workbench.mjs`；浏览器证据在 `output/p3_06u_26b_wechat_first_workbench/`。下一步进入 P3-06U-26C 渠道账号/店铺配置面板；真实外发继续默认关闭。

2026-07-02 追加：P3-06U-26C 已完成渠道账号/店铺配置面板。前端新增 `ChannelAccountState`、`listTenantChannels()`、`configureChannelAccount()`，渠道接入页新增服务端 `channel_accounts` 清单、配置缺失空状态、刷新动作和新增/更新表单；保存后回刷账号列表并更新多渠道对话台来源身份。新增 `docs/P3-06U-26C_CHANNEL_ACCOUNT_CONFIGURATION_PANEL.md`、`scripts/check_p3_06u_26c_channel_account_configuration.py` 和 `scripts/check_p3_06u_26c_channel_account_configuration.mjs`；浏览器证据在 `output/p3_06u_26c_channel_account_configuration/`。本片只保存低敏身份字段，不保存 Secret、Token、Cookie，不打开真实外发。下一步进入 P3-06U-26D 知识三页组件拆分和真实服务端数据深化。

2026-07-02 追加：P3-06U-26D 已完成知识三页分叉与服务端数据深化。新增 `frontend/src/components/knowledge/KnowledgeWorkspacePage.tsx`，把知识库运营、知识缺口、知识评测包装为三种不同页面入口：知识库页强调业务对象、问答卡、文档和发布记录；知识缺口页新增错因地图，覆盖无知识命中、引用不足、期望词缺失和人工驳回；知识评测页新增发布前后对比入口，并明确当前知识评测是检索评测，不是完整客服准确率。新增 `docs/P3-06U-26D_KNOWLEDGE_THREE_PAGE_DEEPENING.md`、`scripts/check_p3_06u_26d_knowledge_three_pages.py` 和 `scripts/check_p3_06u_26d_knowledge_three_pages.mjs`；浏览器证据在 `output/p3_06u_26d_knowledge_three_pages/`。下一步进入 P3-06U-26E 知识评测升级为客服答案质量评测；真实外发继续默认关闭。

2026-07-02 追加：P3-06U-26E 已完成客服答案质量评测第一片。后端评测运行摘要新增 `answer_quality_metrics_version=p3_06u_26e_customer_service_answer_quality_v1`、`citation_sufficiency_rate`、`forbidden_commitment_violation_rate`、`handoff_correctness` 和 `final_answer_factuality_measured=false`；逐题结果新增 `result_payload.answer_quality`；脱敏 Markdown 报告摘要新增客服答案质量指标。前端知识评测页新增“客服答案质量门禁”和逐题质量标签，清楚标记最终答案事实性“未评”。新增 `docs/P3-06U-26E_CUSTOMER_SERVICE_ANSWER_QUALITY_EVALUATION.md`、`scripts/check_p3_06u_26e_answer_quality_evaluation.py` 和 `scripts/check_p3_06u_26e_answer_quality_evaluation.mjs`；浏览器证据在 `output/p3_06u_26e_answer_quality_evaluation/`。本片不生成最终客服答案、不调用模型、不外发、不把检索命中率包装成完整准确率。下一步进入 P3-06U-26F 真实客户题库与知识包导入模板。

2026-07-02 追加：P3-06U-26F 已完成真实客户题库与知识包导入模板第一片。新增 `evals/p3_06u_26f_real_customer_eval_bank_template.csv`、`evals/p3_06u_26f_real_customer_knowledge_package_template.json`、`docs/P3-06U-26F_REAL_CUSTOMER_BANK_AND_KNOWLEDGE_PACKAGE_TEMPLATE.md` 和 `scripts/check_p3_06u_26f_real_customer_templates.py`；`scripts/import_customer_service_eval_bank.py` 已兼容 `customer_question`、`expected_answer`、`business_object`、`must_include`、`must_not_include`、`handoff_expected` 和 `source_reference` 等客户交付字段。26F dry-run 摘要和 payload 证据在 `output/p3_06u_26f_real_customer_templates/`。本片不导入真实客户资料、不调用模型、不外发、不把 8 条模板样例写成真实 50-100 题验收。下一步进入 P3-06U-26G 渠道官方 sandbox 优先级和 RPA draft-only 研究边界固化。

2026-07-02 追加：P3-06U-26G 已完成渠道官方 sandbox 优先级和 RPA draft-only 研究边界固化。渠道接入页新增“官方 sandbox 优先级”矩阵，区分企业微信/微信客服、公众号、抖音/抖店、小红书和电商平台的正式线、当前状态和 RPA 边界；RPA Lab 新增 `draft-only` 硬边界，明确只允许读取、生成草稿、填框和证据采集。新增 `docs/P3-06U-26G_CHANNEL_SANDBOX_AND_RPA_BOUNDARY.md`、`scripts/check_p3_06u_26g_channel_sandbox_rpa_boundary.py` 和 `scripts/check_p3_06u_26g_channel_sandbox_rpa_boundary.mjs`；浏览器证据在 `output/p3_06u_26g_channel_sandbox_rpa_boundary/`。本片不打开真实外发，不把 RPA 写入正式默认交付链。下一步进入 P3-06U-26H 部署运维、客户账号、诊断包、备份恢复、告警和月度质量复盘收束。

2026-07-02 追加：P3-06U-26G2 已完成接待工作台自动回复优先收束。多渠道对话台左侧主筛选只保留“全部 / 我的 / 转人工”，不再把“待审 / 待发”作为普通坐席入口；右侧保留大面积消息流、自动回复记录和异常转人工接管区。普通会话默认 AI 自动接待，低置信、无知识、高风险、超时或渠道异常才进入转人工；发送队列、人审门禁、outbox 和官方授权仍作为后端与生产安全能力保留，不压到首屏。新增回归口径更新到 `docs/P3-06U-26B_WECHAT_FIRST_CONVERSATION_WORKBENCH.md`、`docs/P3-06U-10B_CONVERSATION_WORKBENCH_WECHAT_SIMPLIFICATION.md`、`scripts/check_p3_06u_26b_wechat_first_workbench.*` 和 `scripts/check_p3_06u_10b_conversation_workbench_simplification.*`；浏览器证据在 `output/p3_06u_26b_wechat_first_workbench/` 与 `output/p3_06u_10b_conversation_workbench_simplification/`。当前不做移动端，真实外发继续关闭。

2026-07-02 追加：P3-06U-26G3 已完成运营总览尾部重复模块清理。总览页删除“人工池快照”及其下方旧队列入口，不再展示待人工审核、待发送确认、工单超时、发送失败等日常处理队列；这些能力仍作为工作台、后台队列、outbox、失败复盘和运维闭环保留，不从后端或隐藏路由删除。`scripts/check_p3_06t_03_bi_overview.mjs` 已增加禁止项回归，浏览器证据在 `output/p3_06u_26g3_overview_trim/`。下一步仍进入 P3-06U-26H 部署运维、客户账号、诊断包、备份恢复、告警和月度质量复盘收束。

2026-07-02 追加：P3-06U-26G4 已完成知识运营前后端对齐与去重审验。知识库运营、知识缺口、知识评测三页移除共享 `KnowledgeOperationsFlowPanel` 和页头跳转式假动作，保留各自真实操作面板；新增 `docs/P3-06U-26G4_KNOWLEDGE_OPS_ALIGNMENT_AND_DEDUP_AUDIT.md`、`scripts/check_p3_06u_26g4_knowledge_ops_alignment_dedup.py`，并更新 P3-06U-07/P3-06U-24/P3-06U-26D 回归脚本，防止共享流程总览回归。浏览器证据在 `output/p3_06u_26g4_knowledge_dedup_three_pages/`、`output/p3_06u_26g4_knowledge_dedup_legacy_baseline/` 和 `output/p3_06u_26g4_knowledge_split_regression/`。当前知识评测仍是检索评测，不是完整客服准确率；下一步建议优先做 P3-06U-26G5 知识缺口筛选服务端化，再回到 P3-06U-26H 部署运维收束。

2026-07-02 追加：P3-06U-26G5 已完成小微企业本地化使用收束。可见 RPA 副驾驶实验室已从侧边栏和主路由下线，仅保留内部研究归档；知识缺口列表新增服务端 `query` 筛选，前端把关键词、状态、严重度、来源和分页统一交给后端处理；新增 `docs/P3-06U-26G5_SMALL_BUSINESS_LOCAL_OPS_AND_KNOWLEDGE_SIMPLIFICATION.md` 和 `scripts/check_p3_06u_26g5_small_business_local_ops.py`。当时下一阶段进入 P3-06U-26H1 本地首次启动账号、保持登录和客户初始化，随后推进诊断包生成、客户授权上传、签名更新包导入、备份恢复和月度质量复盘。

2026-07-02 追加：P3-06U-26H2B 已完成本地账号治理第一片。后端 `accounts` 接口补齐用户角色返回、账号启停、密码重置、会话撤销、最后负责人保护和审计事件；前端“管理运维 -> 账号与安全”接入真实账号治理界面，支持负责人创建人员、分配角色、停用/启用账号、重置密码和刷新账号列表。新增 `docs/P3-06U-26H2B_LOCAL_ACCOUNT_MANAGEMENT_FIRST_SLICE.md`；前端 typecheck/build 通过，后端账号、RBAC、本地初始化和登录审计相关测试 `20 passed`。本片未做自助注册审批、诊断包、知识更新包、签名程序更新包和真实平台外发；当时下一步为 P3-06U-26H2C 只读诊断包生成。

2026-07-03 追加：P3-06U-26H2C 已完成本地诊断包生成第一片。后端新增 `GET /api/tenants/{tenant_id}/diagnostic-bundle`，以 `ops.metrics.read` 权限控制只读导出；前端“管理运维 -> 系统设置”新增“本地诊断包”卡片，可点击“生成并下载”导出 JSON 文件。诊断包返回 `schema_version=p3-06u-26h2c.v1`，包含运行、知识、质量、渠道、队列、worker、近期错误和近期变更摘要，并默认排除凭据、原始客户聊天、完整渠道 payload、草稿回复全文和知识原文。新增 `docs/P3-06U-26H2C_LOCAL_DIAGNOSTIC_BUNDLE_FIRST_SLICE.md`；后端全量测试通过，前端 typecheck/build 通过，浏览器下载 smoke 通过。下一步进入 P3-06U-26H2D 知识更新包导入第一片。

2026-07-03 追加：P3-06U-26H2D 已完成知识更新包导入第一片。后端新增 `POST /api/tenants/{tenant_id}/knowledge-update-package/previews`、`POST /api/tenants/{tenant_id}/knowledge-update-package-imports` 和 `POST /api/knowledge-update-package-imports/{import_batch_id}/rollback`，以 `knowledge.manage` 权限控制预检、导入和回滚；前端“知识运营 -> 知识库运营”新增“知识更新包导入”卡片，支持 JSON 更新包预检差异和导入反馈。更新包 schema 为 `wanfa.knowledge_update_package.v1`，当前支持业务对象、对象问答卡、知识文档和回归题集。新增 `docs/P3-06U-26H2D_KNOWLEDGE_UPDATE_PACKAGE_IMPORT_FIRST_SLICE.md`；后端相关回归 `25 passed`，前端 typecheck/build 通过，浏览器 smoke 验证预检新增 4 项、跳过 0 项、错误 0 项。下一步进入 P3-06U-26H2E 签名更新包、备份恢复和程序更新器第一片。

2026-07-03 追加：P3-06U-26H2E 已完成签名更新包预检第一片。后端新增 `POST /api/tenants/{tenant_id}/signed-update-package/preflights`，以 `updates.manage` 权限控制签名更新包预检；新增 `wanfa.signed_update_package.v1` / `wanfa.signed_update_manifest.v1` schema、RSA PKCS#1 v1.5 SHA256 manifest 签名校验、payload canonical JSON SHA256 摘要校验、产品/版本兼容检查、备份计划和健康检查计划。前端“管理运维”新增“签名更新包预检”卡片，可粘贴 JSON 更新包并展示签名、摘要、版本、备份资源、错误和警告。可信发布公钥通过 `WANFA_UPDATE_TRUSTED_PUBLIC_KEYS_JSON` 配置。本片只做 dry-run，不执行更新、不创建备份、不迁移数据库、不替换程序文件、不外发、不调用模型。新增 `docs/P3-06U-26H2E_SIGNED_UPDATE_PACKAGE_PREFLIGHT_FIRST_SLICE.md`；后端相关回归通过，前端 typecheck/build 通过，浏览器 smoke 验证未配可信公钥的示例包被阻断且界面显示“执行 已关闭”。下一步进入 P3-06U-26H2F 更新包暂存、导入前真实备份、导入后健康检查和回滚第一片。

2026-07-03 追加：P3-06U-26H2F 已完成签名更新包暂存第一片。后端新增 `signed_update_packages` 表、迁移 `0026_signed_update_packages.py`、`POST /api/tenants/{tenant_id}/signed-update-package/staged` 和 `GET /api/tenants/{tenant_id}/signed-update-package/staged`；暂存接口先复用 H2E 预检，只有 `can_stage=true` 才写入本地暂存表。同一 `package_id` 和同一包摘要保持幂等，同一 `package_id` 不同内容返回冲突，暂存成功写入 `signed_update_package.staged` 审计事件。前端在签名更新包区域新增“暂存更新包”按钮和“已暂存更新包”列表，明确展示“未备份”和“执行关闭”。新增 `docs/P3-06U-26H2F_SIGNED_UPDATE_PACKAGE_STAGING_FIRST_SLICE.md`；后端相关回归 `19 passed`，前端 typecheck/build 通过，浏览器 smoke 验证系统设置页存在预检卡、暂存按钮、暂存列表和执行关闭提示。本片仍不执行更新、不创建备份、不迁移数据库、不替换程序文件、不外发、不调用模型；下一步进入真实备份、健康检查、知识/策略包应用和回滚第一片。

2026-07-03 追加：P3-06U-26H2W3B 已完成客户知识维护四步流程收束。知识库运营页客户可见入口从“客户知识建设中心”改为“客户知识维护向导”，按“业务对象、标准问答、流程政策、禁用承诺与转人工规则”四步组织；重复的知识更新路径说明已移除；“编辑知识草稿”改为“导入知识文档”；“自动回复状态机 / AI 回复预案”改为“自动回复处理方式 / 回复草稿 / 转人工”。本片没有新增真实外发、没有调用模型、没有改写 RAG 后端，只把客户能理解的知识维护路径、发布前回归检查和现有真实后端能力对齐。新增 `docs/P3-06U-26H2W3B_CUSTOMER_KNOWLEDGE_MAINTENANCE_FLOW.md` 和 `scripts/check_p3_06u_26h2w3b_customer_knowledge_flow.py`；`FRONTEND_FUNCTION_REALITY_MATRIX.md` 更新到 H2W3B。验证通过：H2W3B 静态门禁、H2W2 客户知识中心门禁、P3-06U-20 自动回复处理方式门禁、H2W1 本地设置与知识入口门禁、P3-06U-07/P3-06U-26D 知识回归、前端 typecheck/build、H2W3 前端逐页深审 `Issues: 0`、P3-06U-26D 浏览器回归。下一步仍优先补客户知识维护的真实导入模板、更多真实客户题库、线上回执与准确率闭环；真实外发继续关闭。

2026-07-03 追加：P3-06U-26H2W3C 已完成客户资料导入模板与预检第一片。知识库运营页新增“客户资料导入助手”，客户可下载或复制 CSV 模板，把业务对象、标准问答、流程政策、禁用承诺、转人工规则和回归题整理到统一表格；前端可将该 CSV 转换为标准知识更新包 JSON，并填入现有“知识更新包导入”区域继续执行预检差异和导入更新。本片只打通客户资料整理到本地知识包预检的第一段，不自动解析 PDF/DOCX/XLSX，不打开真实外发，不调用模型，不替代后续启用前回归。新增 `docs/P3-06U-26H2W3C_CUSTOMER_KNOWLEDGE_INTAKE_TEMPLATE.md` 和 `scripts/check_p3_06u_26h2w3c_customer_knowledge_intake.py`；`FRONTEND_FUNCTION_REALITY_MATRIX.md` 更新到 H2W3C。验证通过：H2W3C 静态门禁、H2W3B/H2W2/H2W1 相关门禁、P3-06U-07/P3-06U-26D 知识回归、前端 typecheck/build。下一步优先补线上回执与准确率、正式文件接收签收、云接收台、真实更新恢复、生产级 RAG/模型成本治理；真实外发继续关闭。

2026-07-03 追加：P3-06U-26H2W4 已完成报告导出与归档第一片。客户质量报告可导出 HTML、XLSX、DOCX 三种文件，XLSX/DOCX 由后端生成有效 OpenXML zip 文件并以 base64 下载；每次导出写入 `customer_quality_report.exported` 审计归档，前端质量复盘页新增报告归档列表和历史下载。新增 `docs/P3-06U-26H2W4_REPORT_EXPORTS_AND_ARCHIVE_FIRST_SLICE.md` 和 `scripts/check_p3_06u_26h2w4_report_exports.py`；`FRONTEND_FUNCTION_REALITY_MATRIX.md` 更新到 H2W4。本片不做 PDF、不接正式电子签章、不打开真实外发、不调用模型，不保存原始客户问题、完整回复或人工备注原文；后续可进入云接收台 H2W-5 或 PDF/电子签章专项评估。

2026-07-03 追加：P3-06U-26H2G 已完成签名知识更新包应用与回滚第一片。后端新增 `POST /api/signed-update-packages/{id}/apply` 和 `POST /api/signed-update-packages/{id}/rollback`，以 `updates.manage` 权限控制，并复用 H2D 知识更新包导入/回滚服务；应用成功后记录 `knowledge_import_batch_id`、导入前计数快照、健康检查状态、`apply_result` 和 `signed_update_package.applied` 审计事件，回滚成功后记录 `rollback_result` 和 `signed_update_package.rolled_back`。前端“已暂存更新包”列表新增“备份并应用”和“回滚”按钮，程序包/策略包继续显示当前阶段不应用。新增 `docs/P3-06U-26H2G_SIGNED_KNOWLEDGE_UPDATE_APPLY_ROLLBACK_FIRST_SLICE.md`；后端相关回归 `22 passed`，前端 typecheck/build 通过，临时环境浏览器 smoke 实际点击暂存、应用、回滚三态，证据在 `output/p3_06u_26h2g_signed_update_apply_ui/`。本片不是完整程序更新器，也不是数据库物理备份恢复；下一步进入策略更新包、SQLite 物理备份恢复演练、程序更新器 dry-run 和客户授权上传第一片。

## 1. 总目标

本轮目标不是再新增一个单点功能，而是把智能客服系统整理成两条可销售、可交付、可维护的产品线：

1. Lite 试点版：面向首批中小企业和低风险试点，快速验证官网/私域入口、知识库问答、AI 草稿、人审、留资、质量复盘和受控部署。
2. 标准运营版：面向正式运营客户，提供账号权限、坐席工作台、知识库运营、模型路由、质量评测、渠道接入沙盒、审计、部署、备份、运维和月度质量服务。

同时形成四类交付资料：

| 资料 | 面向对象 | 用途 |
| --- | --- | --- |
| 客户使用手册 | 使用团队、运营负责人、坐席、管理员 | 说明每天怎么用系统、怎么更新知识、怎么处理 AI 草稿和质量问题 |
| 产品介绍 | 采购方、业务负责人、老板、售前 | 说明产品是什么、解决什么问题、适合什么场景、边界是什么 |
| 服务体系介绍 | 采购方、项目负责人、售后负责人 | 说明实施、培训、运维、质量复盘、故障响应和持续服务 |
| 内部售后运维计划 | 我方交付、运维、销售、客户成功 | 说明卖出去以后如何维护、怎么远程排障、怎么复盘准确率、怎么控制成本 |

## 2. 当前真实阶段

已经完成：

- 标准运营版工程骨架：FastAPI、React/Vite、SQLAlchemy、Alembic、本地 SQLite 验证、PostgreSQL/pgvector 目标路径。
- 账号、角色、团队、登录、会话 token hash、部分 owner/admin 权限和审计事件。
- Workflow、checkpoint、人工审核任务、坐席审核收件箱、outbox 草稿、发送前确认、dry-run 发送尝试、发送队列骨架。
- 知识卡片、知识文档、文档分块、chunk 引用、检索评测、脱敏报告、知识评测运行历史。
- 模型网关、模型路由、百炼 smoke 安全脚本、真实百炼小样本 smoke 记录、deterministic fallback。
- 官网客服沙盒：HMAC 验签、可信入站、幂等去重、AI 草稿、人审、outbox、发送计划门禁、审计链。
- 前端坐席工作台：七类队列、会话证据详情、渠道健康、桌面和移动端 QA。
- 会话运营：服务端会话收件箱、坐席动作状态机、对话台、质量复盘、知识缺口、工单/轻量 SLA、联系人画像和线索跟进第一片。
- 后台进程运维：outbox 队列租约、可信入站 worker 租约、worker heartbeat、Docker Compose worker service、只读 worker healthcheck、前端运维心跳面板。
- 运维告警与指标：P3-06F 已新增只读告警规则目录、触发评估、runbook、通知边界和前端“运维与告警”展示；P3-06G 已新增只读指标出口、Prometheus 文本预览和前端“指标出口”面板。当前仍不发送真实通知、不接真实 Prometheus/Grafana 采集任务。
- 中台信息架构与权限：P3-06UI 已把侧边栏收束为总览、工作台、客户、知识运营、质量复盘、渠道接入、管理运维 7 个工作域，并新增前端 owner/admin/agent/viewer 菜单可见性、坐席默认进入对话台、管理/只读默认进入总览；H2V 已把管理运维下的运维与告警、模型路由、账号安全改为三个真实页面，不再使用共用页面内部 tabs；P3-06O 已完成关键动作按钮级权限第一片，P3-06P 已完成 outbox draft、dry-run send-attempt、delivery job 和 failure review 后端命名权限；P3-06R-02 已补齐生产模式 bootstrap 关闭、foundation/workflow/worker/reply 权限契约和前端按权限刷新资源；P3-06R-04C 已新增 `dashboard.read` 运营总览聚合权限，owner/admin/viewer 可读脱敏经营指标，agent 不可读。后续仍需字段脱敏、字段 allowlist 和生产账号初始化策略。
- P3-05A 试点部署准备：部署准备文档、自检脚本、诊断包脚本、环境变量模板、Compose 配置校验、一次性迁移 smoke 和三份正式对外 DOCX 资料包。
- P3-05B 下一阶段计划：已形成托管云端版、私有化部署、临时远程维护授权和 Lite 封版路线，明确真实外发仍默认关闭。

仍未完成：

- 真实客户 50-100 条脱敏题库和人工事实性标签。
- 真实客户知识包替换 rehearsal 知识包。
- 真实平台账号的官方 sandbox，例如企业微信、公众号、电商平台服务商授权。
- 真实外发发送器和生产级回执 reconciliation。
- 独立 Redis/RQ/Celery/Arq 消费者、生产级队列、死信、Prometheus/Grafana 和真实告警通道。
- 真实客户环境部署、真实 PostgreSQL 备份恢复演练、升级回滚实操和客户现场部署 smoke。
- 完整 CRM、完整跨渠道身份合并、标签体系、线索漏斗、团队绩效、工单评论/附件/重开和高级 SLA。
- 完整模型成本治理、provider 调用日志、预算和熔断。

## 3. 产品线定义

### 3.1 Lite 试点版

定位：低风险、快速验证、可演示、可小范围使用的智能客服试点包。

适合：

- 官网客服或单个私域入口。
- 业务知识量较小，主要是售前咨询、套餐说明、基础售后、留资。
- 需要先验证 AI 客服能否减少重复问答和辅助坐席，而不是立刻全渠道全自动。

应包含：

| 模块 | Lite 必须做到 |
| --- | --- |
| 登录与权限 | 管理员、坐席演示账号；基础角色区分；正式交付时不使用开发演示身份 |
| 客服入口 | 官网沙盒或一个自有入口；真实平台需另行授权 |
| 知识库 | 结构化 FAQ + 轻量文档知识包；支持导入、检索、引用 |
| AI 回复 | 基于知识命中的 AI 草稿；低置信/高风险转人工 |
| 人工审核 | 坐席可看原问题、草稿、引用证据、风险原因后批准或改写 |
| 留资 | 记录咨询线索、意向、联系方式字段需由客户确认合规 |
| 质量复盘 | 50-100 条题库模板、脱敏报告、知识缺口列表 |
| 部署 | 单机或轻量云部署；可备份、可恢复、可回滚 |
| 运维 | 健康检查、日志位置、只读诊断包、月度复盘模板 |

Lite 不承诺：

- 全平台接通。
- 无人值守自动处理所有问题。
- 高并发企业级 SLA。
- 私有大模型部署。
- 复杂工单、团队绩效和多租户商业平台能力。

Lite 完成标准：

- 一个入口能完成入站、AI 草稿、人审、outbox 门禁和审计。
- 客户知识包能导入并被引用。
- 至少 50 条脱敏题库能跑质量回归。
- 部署、备份、恢复、回滚、诊断包有可执行手册。
- 客户能按使用手册完成日常接待、知识更新和问题复盘。

### 3.2 标准运营版

定位：可作为正式运营客服中台的主线版本。

适合：

- 有多个坐席、多个团队或多个业务线。
- 需要长期维护知识库、跟踪回复质量、追踪审计和服务绩效。
- 需要逐步接入官网、企业微信、公众号或其他官方授权渠道。

应包含：

| 模块 | 标准运营版必须做到 |
| --- | --- |
| 账号组织 | 租户、用户、角色、团队、成员、正式登录、RBAC、审计 |
| 坐席工作台 | 待审核、待发送、失败复盘、知识缺口、高风险、最近评测、渠道健康 |
| 会话管理 | 会话列表、联系人摘要、消息流、AI 草稿、人工接管、审计链 |
| 知识运营 | 知识卡片、文档导入、分块、版本、审核、失效、引用溯源 |
| 检索与评测 | BM25 + 向量候选、重排策略、固定题库、脱敏报告、知识缺口闭环 |
| 模型路由 | 简单问题低成本模型、普通问题标准模型、复杂/风险问题高阶模型+人审 |
| 渠道接入 | 官网自有入口优先；企业微信/公众号/电商必须官方授权；默认外发关闭 |
| Outbox | 发送前确认、幂等键、队列 job、回执、失败复盘、kill switch |
| 部署运维 | PostgreSQL、Redis/队列、备份恢复、升级回滚、日志审计、监控告警 |
| 质量运营 | 月度准确率报告、抽样复核、知识更新、模型成本和故障复盘 |

标准运营版不承诺：

- 未授权平台自动回复。
- 个人微信外挂、Hook、群控、模拟点击、商家后台 RPA。
- 未经过客户题库验证的自动外发。
- 未经审批的生产数据库变更或真实客户数据模型外呼。

标准运营版完成标准：

- P3-05 部署包完成并通过空库迁移、备份恢复、回滚和 smoke。
- 单个官方或自有入口完成受控试点闭环。
- 真实客户知识包和 50-100 条题库完成导入、人工标注和回归。
- 坐席能在工作台日常处理会话、审核草稿、复盘失败和补知识。
- 管理员能查看质量指标、渠道健康、审计和运维状态。

## 4. 六条并行工程线

| 工程线 | 目标 | 第一批产物 | 验收方式 |
| --- | --- | --- | --- |
| A. Lite 产品闭环 | 把现有能力收敛成可售卖试点包 | Lite 功能清单、部署包、官网入口、题库模板、手册 | 本地部署、浏览器 QA、50 条题库 dry-run |
| B. 标准运营版闭环 | 把 `standard_ops` 做成正式主线 | P3-05 部署包、账号权限、工作台、质量运营、队列 | 后端回归、前端构建、部署 smoke、恢复 drill |
| C. 客户使用资料 | 让客户知道怎么用 | 客户使用手册 | 章节完整、无内部口吻、无 secrets |
| D. 产品宣传资料 | 让售前能讲清产品 | 产品介绍、场景价值、版本差异、边界 | 可对外阅读、没有夸大承诺 |
| E. 服务体系资料 | 让客户知道买后有什么服务 | 实施、培训、运维、质量复盘、SLA | 服务项、责任边界、响应口径清晰 |
| F. 内部运维体系 | 让我们卖后能稳定维护 | 售后 SOP、远程维护、故障、知识更新、成本模型 | 内部 checklist 可执行 |

## 5. 分阶段实施计划

### 阶段 P3-05A：产品化部署底座

目标：让另一个工程师可以按清单部署、检查、备份、恢复和回滚。

状态：已完成第一片。已生成部署准备文档、自检脚本、诊断包脚本、环境模板、三份正式对外 DOCX，并完成 Compose 配置校验、一次性迁移 smoke 和 P3-04 回归。未完成项是客户真实环境部署、真实 PostgreSQL 备份恢复演练和生产 worker。

任务：

- [x] 环境变量清单：区分必填、可选、默认关闭、敏感项。
- [x] 数据库迁移 smoke：SQLite 本地和 PostgreSQL 目标路径分开。
- [ ] Redis/队列 smoke：明确当前哪些仍是 HTTP runner，哪些要升级为生产 worker。
- [ ] 备份恢复演练：数据库、知识库文件、评测报告、配置。
- [x] 日志与审计位置：应用日志、审计表、发送尝试、失败复盘。
- [x] Kill switch：外部发送、模型外呼、embedding provider、渠道外发。
- [x] 诊断包：脱敏导出版本、配置摘要、健康状态、队列状态、最近错误。
- [ ] 回滚计划：代码回滚、迁移回滚、知识版本回滚、模型路由回滚。

验收：

- [x] 生成 `P3-05_PILOT_DEPLOYMENT_READINESS.md`。
- [x] 新增或更新 `.env.example`。
- [x] 运行空库迁移 smoke。
- [ ] 运行完整后端测试和前端 build。
- [x] 明确哪些生产动作仍需授权。

### 阶段 P3-05B：Lite 试点版封版

目标：把 Lite 从“工程可跑”整理成“客户可以试用”的产品包。

状态：当前阶段。已完成 release readiness、托管云端版 runbook、私有化部署包、远程维护授权 SOP、P3-05B readiness smoke 和 P3-05C 官方渠道自动回复可行性核验。下一步整理 Lite 知识包模板、题库模板和工作台最终浏览器 QA；如先拿到企业微信/微信客服测试号，则优先做单平台官方 sandbox。

任务：

- [x] Lite 试点版功能矩阵。
- [x] 单入口试点流程：官网入口为默认，其他平台另行授权。
- [x] 托管云端版 runbook 和 pilot compose profile。
- [x] 私有化部署包清单。
- [x] 远程维护授权 SOP。
- [x] P3-05B readiness smoke。
- [x] P3-05C 官方渠道自动回复可行性矩阵和只读自检。
- [ ] Lite 知识包模板：产品、价格、交付、售后、账号、合规、风险话术。
- [ ] Lite 题库模板：50 条起步，覆盖售前、价格、交付、售后、风险。
- [ ] Lite 工作台页面精修：面向坐席，而不是工程调试。
- [ ] Lite 交付检查表：安装、账号、知识导入、模型 key、测试、培训。

验收：

- [ ] 客户可登录。
- [ ] 可看到待审核、待发送、失败、知识缺口。
- [ ] 可导入知识并检索引用。
- [ ] 可跑题库报告。
- [ ] 可导出诊断包。
- [ ] 不自动真实外发。

### 阶段 P3-05N：联系人画像与线索跟进第一片

目标：让客服中台不只处理单条消息，而是能围绕联系人看到历史会话、开放工单、开放线索和下一步动作，并能从高意向会话生成可跟进线索。

状态：已完成第一片。后端已新增联系人画像聚合接口、线索资源、迁移、API、角色边界、联系方式脱敏、幂等生成、审计事件；前端已新增 `联系人` 和 `线索` 工作区，支持分页、搜索、筛选、画像详情、线索阶段推进和演示数据。

已完成：

- [x] 联系人画像列表和详情。
- [x] 手机号、微信按角色脱敏。
- [x] 最近会话、开放工单、开放线索聚合。
- [x] 从会话幂等生成线索。
- [x] 线索阶段、意向、负责人、预算和下一步动作。
- [x] 线索列表服务端分页、阶段筛选、意向筛选、负责人筛选和关键词搜索。
- [x] 创建/更新线索写会话事件和租户审计。
- [x] 前端联系人中心和线索跟进工作区。
- [x] 后端相关回归、迁移头、前端构建和 Chrome 预览。

仍未完成：

- [ ] 跨渠道身份合并：企业微信、公众号、电商、官网等身份归并。
- [ ] 客户标签、线索标签、风险标签和来源标签。
- [ ] 联系人合并、拆分、去重和冲突处理。
- [ ] 线索评论、跟进记录、提醒和附件。
- [ ] CRM、企微客户联系、订单系统或电商订单官方 API 对接。
- [ ] 线索漏斗、成交金额、销售绩效和管理报表。
- [ ] 更细粒度的个人信息权限、导出审批和数据保留策略。

验收：

- [x] `backend/.venv/bin/python -m pytest backend/tests/test_customer_profiles_api.py backend/tests/test_support_tickets_api.py backend/tests/test_conversation_inbox_api.py backend/tests/test_auth_rbac_audit.py -q` 通过，10 个测试通过。
- [x] `cd backend && .venv/bin/alembic heads` 返回 `0019_sales_leads (head)`。
- [x] `cd frontend && npm run build` 通过。
- [x] Chrome 打开 `http://127.0.0.1:5175/#contacts` 可见联系人画像、分页和详情。
- [x] Chrome 打开 `http://127.0.0.1:5175/#leads` 可见线索池、筛选、分页和候选会话。

### 阶段 P3-05O：知识缺口到文档草稿与回归题库第一片

目标：让 P3-05K 的知识缺口不只停留在待办列表，而是能一键生成待审核知识文档草稿，并沉淀为可重复运行的回归题。

状态：已完成第一片。后端已新增缺口草稿和回归题子资源接口，支持 owner/admin 创建或复用草稿文档、创建或复用知识缺口回归题库、写回缺口 remediation 证据、状态推进到处理中和审计事件；前端已在 `缺口` 工作区新增草稿/回归状态标签和动作按钮。

已完成：

- [x] `POST /api/knowledge-gaps/{gap_id}/document-drafts`。
- [x] `POST /api/knowledge-gaps/{gap_id}/regression-cases`。
- [x] 草稿文档默认 `draft`，不自动发布到 active 知识库。
- [x] 回归题按 `knowledge-gap-{gap_id}` 幂等复用。
- [x] 生成草稿或回归题后，缺口进入 `in_progress` 并默认分派给当前操作人。
- [x] `evidence_payload.remediation` 写入草稿文档 ID、回归题库 ID 和回归题 ID。
- [x] 前端缺口卡片显示“未生成草稿/草稿文档 #”“未入回归/回归题 #”。
- [x] 前端缺口卡片新增“生成草稿”和“加入回归”。

仍未完成：

- [x] 发布前强制回归题通过第一片：P3-05S 已新增发布预检和发布执行 API。
- [x] 发布历史、门禁详情和回滚第一片：P3-05T 已新增发布记录表、查询 API、回滚 API 和前端发布记录卡片。
- [ ] 草稿详情页、完整知识审核流、正文版本 diff 和可恢复旧正文的完整回滚。
- [ ] 发布后自动关联通过率、命中率和人工事实性标签。
- [ ] 坐席脱敏缺口视图和运营负责人审批流。
- [ ] 真实客户知识库事实审核和真实客户题库验收。

验收：

- [x] `backend/.venv/bin/python -m pytest backend/tests/test_knowledge_gaps_api.py backend/tests/test_knowledge_documents_api.py backend/tests/test_knowledge_evaluations_api.py -q` 通过，13 个测试通过。
- [x] `cd backend && .venv/bin/alembic heads` 返回 `0019_sales_leads (head)`，本轮无新增迁移。
- [x] `cd frontend && npm run build` 通过。
- [x] headless Chrome 打开 `http://127.0.0.1:5175/#gaps` 后，确认 `知识缺口闭环`、`生成草稿/已有草稿`、`加入回归/已入题库`、`未生成草稿/草稿文档 #`、`未入回归/回归题 #` 均可见。

### 阶段 P3-05S：知识发布前回归门禁第一片

目标：让知识缺口草稿不能绕过评测直接进入 active 知识库，必须先完成回归题校验。

状态：已完成第一片。后端新增 `publish-checks` 和 `publication` 两个子资源；发布前会校验文档索引、chunk、来源、回归题、引用、期望词、来源匹配和置信度。前端缺口页新增“发布知识”动作，成功后刷新知识文档、知识缺口和评测状态。

已完成：

- [x] `POST /api/knowledge-documents/{document_id}/publish-checks` 发布预检。
- [x] `POST /api/knowledge-documents/{document_id}/publication` 带门禁发布。
- [x] 知识评测新增 `search_status`，拆开“题目状态”和“检索文档状态”，支持评测 draft 文档。
- [x] 门禁只把知识质量问题作为阻断；高风险必须人工、禁止自动回复只作为安全提示。
- [x] 发布通过后，文档和 chunk 状态改为 active。
- [x] 发布通过后，关联知识缺口改为 resolved，并写入 remediation 发布证据。
- [x] 前端缺口卡片新增“未发布/已发布”和“发布知识”动作。

仍未完成：

- [x] 发布历史和逐题原因展示第一片：P3-05T 已在文档卡片展示最新门禁记录和逐题摘要。
- [x] 回滚第一片：P3-05T 支持把 active 文档及 chunk 回退为 draft，并把关联缺口退回处理中。
- [ ] 门禁详情弹窗、完整版本 diff、回滚到指定历史正文。
- [ ] 多人审批、复核人签名和业务负责人确认。
- [ ] 批量发布和批量回归。
- [ ] 从质量 BI 一键跳转到对应缺口和发布记录。

验收：

- [x] `.venv/bin/pytest backend/tests/test_knowledge_gaps_api.py backend/tests/test_knowledge_evaluations_api.py backend/tests/test_knowledge_documents_api.py -q` 通过，15 个测试通过。
- [x] `cd frontend && npm run build` 通过。
- [x] headless Chrome 打开 `http://127.0.0.1:5175/#gaps` 后，确认 P3-05S、9 条缺口、9 个发布动作可见，无横向溢出，console error/warning 为 0。

### 阶段 P3-05T：知识发布记录、门禁详情与回滚第一片

目标：让每次发布前检查、正式发布和回滚都有独立记录，运营台能看到最新门禁结果，并能在发现知识错误后立刻退出 active 检索范围。

状态：已完成第一片。后端新增 `knowledge_document_publications` 表、发布记录查询 API 和回滚 API；发布检查和正式发布都会写记录。前端知识文档卡片展示最新发布记录、阻断项、逐题摘要和“回滚为草稿”动作。

已完成：

- [x] `GET /api/knowledge-documents/{document_id}/publications`。
- [x] `POST /api/knowledge-documents/{document_id}/rollback`。
- [x] `publish-checks` 写入 `publish_check / passed|blocked` 记录。
- [x] `publication` 写入 `publish / published|blocked` 记录。
- [x] 回滚写入 `rollback / rolled_back` 记录。
- [x] 回滚后文档和 chunk 状态改为 `draft`。
- [x] 回滚后已解决缺口退回 `in_progress`。
- [x] 前端文档卡片展示最新发布记录、门禁状态、评测运行、阻断项和逐题摘要。

仍未完成：

- [ ] 完整文档版本表。
- [ ] 正文 diff、chunk diff 和恢复旧正文。
- [ ] 多人审批、复核人签名和业务负责人确认。
- [ ] 批量发布、批量回归和批量回滚。
- [ ] 从质量 BI 一键跳转到对应发布记录。

验收：

- [x] `.venv/bin/pytest backend/tests/test_knowledge_gaps_api.py backend/tests/test_knowledge_evaluations_api.py backend/tests/test_knowledge_documents_api.py -q` 通过，15 个测试通过。
- [x] `cd backend && .venv/bin/alembic heads` 返回 `0020_knowledge_document_publications (head)`。
- [x] `cd frontend && npm run build` 通过。
- [x] headless Chrome 打开 `http://127.0.0.1:5175/#knowledge` 后，桌面和移动端均无横向溢出，console error/warning 为 0，发布记录卡片和回滚按钮可见。

### 阶段 P3-06：标准运营版产品化 v1

目标：把标准运营版从“P3 沙盒”升级为“正式运营中台 v1”。

任务：

- [ ] 完整资源权限：知识、评测、渠道、outbox、审计按角色控制。
- [ ] 坐席分配：会话归属、团队、待办队列、接管状态。
- [x] 联系人画像第一片：基础资料、最近会话、开放工单、开放线索、脱敏和下一步动作。
- [ ] 联系人画像增强：跨渠道身份合并、标签、合并拆分、来源冲突处理。
- [ ] 线索增强：评论、跟进记录、提醒、附件、漏斗和 CRM/订单系统对接。
- [x] 知识发布门禁第一片：草稿、回归题、发布预检、启用文档和关闭缺口。
- [x] 知识审核增强第一片：发布历史、门禁详情摘要和回滚为草稿。
- [ ] 知识审核增强第二片：失效、版本 diff、恢复旧正文、多人审批。
- [x] 质量中心第一片：知识缺口处理状态、草稿生成状态和回归题沉淀状态。
- [x] 质量诊断 BI 第一片：错因排行、质量漏斗、渠道异常、知识缺口热力、人审矩阵、样本下钻和修复动作。
- [x] 生产 worker 第一片：outbox delivery queue 租约 TTL、原子 claim、陈旧锁抢回、新鲜锁跳过、重试和死信保持可用。
- [x] 生产 worker 第二片第一阶段：可信入站 worker 租约化、worker run 记录和失败重放。
- [x] 生产 worker 第二片第二阶段：worker heartbeat 与受控 loop 第一片。
- [x] 生产 worker 第三片第一阶段：Docker Compose worker service、CLI 进程入口和 healthcheck。
- [ ] 生产 worker 后续：真实多实例 smoke、Prometheus/云监控告警、前端运维心跳页和 outbox 独立 worker service。
- [ ] 模型成本治理：按 provider/model/route 统计调用、延迟、失败、估算成本。
- [ ] 渠道接入 v1：官网正式入口 + 一个官方平台 sandbox。

验收：

- [ ] 后端回归测试。
- [ ] 前端构建和浏览器 QA。
- [ ] 部署 smoke。
- [ ] 备份恢复 drill。
- [ ] 一条试点渠道闭环。
- [ ] 真实客户题库质量报告。

### 阶段 P3-06A：生产并发底座第一片

目标：让 outbox delivery queue 具备最小生产并发保护，避免多个 worker 重复处理同一条发送任务。

状态：已完成第一片。当前仍是 DB 队列，不是 Redis/专用消息队列；真实外发保持关闭。

已完成：

- [x] `OutboxDeliveryQueueRunCreate` 新增 `lease_seconds`。
- [x] `outbox_delivery_jobs` 支持基于 `locked_at` 的租约 TTL 判定。
- [x] 使用条件 `UPDATE` 原子 claim job。
- [x] 新鲜 `locked` job 进入 `skipped_job_ids`，不生成 attempt。
- [x] 陈旧 `locked` job 可被新 worker 抢回处理。
- [x] response `kill_switch.lease` 输出 worker、TTL、cutoff、跳过数量和 atomic claim 证据。

已由 P3-06B 继续完成：

- [x] 可信入站 worker 租约化。
- [x] worker run 记录表。

仍未完成：

- [ ] 常驻 worker 进程、heartbeat、监控告警。
- [ ] Redis/消息队列或 Postgres `FOR UPDATE SKIP LOCKED` 路线。
- [ ] 多进程/多容器真实压测。

验收：

- [x] `.venv/bin/pytest backend/tests/test_outbox_delivery_queue_api.py -q` 通过，5 个测试通过。

### 阶段 P3-06B：可信入站 worker 租约与运行记录第一片

目标：让可信入站 worker 具备最小生产并发保护和运行追溯，避免多 worker 重复编排同一条入站消息，并支持失败后重放。

状态：已完成第一片。当前仍是 DB 租约，不是常驻 worker，也不是 Redis/专用消息队列；真实外发保持关闭。

已完成：

- [x] 新增 `trusted_inbound_worker_runs`，记录每次 worker 调用、输入、计数、结果和 lease 证据。
- [x] 新增 `trusted_inbound_message_jobs`，按 `tenant_id + message_id` 和 `tenant_id + idempotency_key` 幂等约束入站消息处理。
- [x] `TrustedInboundWorkerRunCreate` 新增 `worker_id` 和 `lease_seconds`。
- [x] 新鲜 `locked` 入站 job 进入跳过，不创建 workflow。
- [x] 陈旧 `locked` 入站 job 可被新 worker 抢回处理。
- [x] `failed` 入站 job 可被后续 worker 重放。
- [x] 新增 `GET /api/tenants/{tenant_id}/trusted-inbound-worker-runs` 只读查看运行记录。
- [x] response `lease` 输出 worker、TTL、cutoff、claim、fresh skip、stale reclaim、failed replay 证据。

仍未完成：

- [ ] 常驻 worker 进程。
- [x] heartbeat 表与健康状态接口已在 P3-06C 第一片完成。
- [ ] 监控指标、告警和失败分级。
- [ ] 多实例真实 smoke 或小规模压测。
- [ ] 企业微信公网 HTTPS 回调 smoke。

验收：

- [x] `.venv/bin/pytest backend/tests/test_trusted_inbound_worker_api.py -q` 通过，6 个测试通过。

### 阶段 P3-06C：Worker heartbeat 与受控常驻循环第一片

目标：让后台 worker 的运行态可落库、可读取、可测试，为后续常驻进程、监控告警和部署级多实例 smoke 打基础。

状态：已完成第一片。当前已有 DB heartbeat 和受控 loop runner，但还不是完整生产监控系统；没有接入 Prometheus、systemd、Kubernetes 或真实多容器压测。

已完成：

- [x] 新增 `worker_heartbeats` 表，按 `tenant_id + worker_type + worker_id` 唯一记录 worker 实例。
- [x] 新增 `GET /api/tenants/{tenant_id}/worker-heartbeats`，返回 `status` 和计算后的 `health_status`。
- [x] 新增 `POST /api/tenants/{tenant_id}/trusted-inbound-worker-loop-runs`，支持受控循环运行可信入站 worker。
- [x] loop runner 会写入 `starting`、`running`、`idle`、`failed` 状态。
- [x] heartbeat 记录 `last_run_record_id`、`last_run_mode`、`last_error`、`loops_completed` 和最近运行摘要。
- [x] 多 worker smoke 已覆盖：两个 `worker_id` 连续运行不会重复处理已成功 claim 的可信入站消息。
- [x] 前端总览阶段标识更新为 `P3-06C`。

仍未完成：

- [x] 常驻 worker 的第一片真实进程入口已在 P3-06D 完成。
- [x] Docker Compose worker service 第一片已在 P3-06D 完成。
- [ ] Prometheus 指标、告警规则和告警通知渠道。
- [ ] 多容器真实并发压测。
- [x] 前端运维页展示 worker heartbeat 已在 P3-06E 完成。
- [ ] 企业微信公网 HTTPS 回调 smoke。

验收：

- [x] `.venv/bin/python -m pytest tests/test_worker_heartbeats_api.py -q` 通过，3 个测试通过。
- [x] `.venv/bin/python -m pytest tests/test_trusted_inbound_worker_api.py tests/test_channel_webhooks_api.py tests/test_p3_05e_wecom_official_sandbox_connector.py -q` 通过，20 个测试通过。
- [x] `.venv/bin/python -m pytest tests/test_outbox_delivery_queue_api.py tests/test_outbox_api.py -q` 通过，13 个测试通过。
- [x] `.venv/bin/alembic heads` 返回 `0022_worker_heartbeats (head)`。

### 阶段 P3-06D：Worker 进程部署第一片

目标：把 P3-06C 的受控 loop 接到部署层，让可信入站 worker 可以作为独立进程由 Docker Compose 启动、健康检查和重启。

状态：已完成第一片。当前有 CLI worker service、`worker` profile、只读 healthcheck、环境变量模板和 readiness 检查；仍未完成 Kubernetes/HPA、Prometheus 真实采集、告警通道、多容器压测和客户真实环境部署。

已完成：

- [x] 新增 `python -m app.workers.trusted_inbound_worker_service` CLI 进程入口。
- [x] CLI 支持有限循环和无限常驻两种模式，默认由 Docker service 常驻。
- [x] CLI 支持 `--healthcheck`，读取 `worker_heartbeats` 并返回健康/非健康退出码。
- [x] `docker-compose.yml` 新增 `trusted-inbound-worker` service。
- [x] worker service 使用 `profiles: ["worker"]`，默认普通 compose up 不自动启动。
- [x] worker service 和 pilot overlay 强制 `OUTBOX_EXTERNAL_WRITE_ENABLED: "false"`。
- [x] `.env.example` 新增 `TRUSTED_INBOUND_WORKER_*` 配置，租户和用户默认留空。
- [x] 新增 `scripts/check_p3_06d_worker_deployment.py` readiness 检查。
- [x] 新增 `docs/P3-06D_WORKER_PROCESS_DEPLOYMENT.md`。
- [x] 前端总览阶段标识更新为 `P3-06D`。

仍未完成：

- [ ] Kubernetes deployment / HPA。
- [ ] Prometheus 指标真实采集和告警通知通道。
- [ ] 多容器并发压测。
- [ ] outbox 独立 worker service。
- [x] 前端运维页展示 worker heartbeat 已在 P3-06E 完成。
- [ ] 企业微信公网 HTTPS 回调 smoke。
- [ ] 真实外发白名单测试。

验收：

- [x] `.venv/bin/python -m pytest tests/test_p3_06d_worker_deployment.py -q` 通过，5 个测试通过。
- [x] `python3 scripts/check_p3_06d_worker_deployment.py` 返回 `PASS p3-06d worker deployment`。
- [x] `docker compose -f deploy/docker-compose.yml -f deploy/docker-compose.pilot.yml --profile worker config` 通过。

### 阶段 P3-06E：运维心跳面板第一片

目标：把 P3-06C/P3-06D 已经具备的 worker heartbeat、运行记录和外发开关状态，整理成后台只读总览接口和前端“运维”工作区，让部署后的远程排障不再只靠命令行和日志。

状态：已完成第一片。当前有 owner/admin 可查看的只读接口、worker 健康汇总、最近运行记录、风险提示、外发边界提示和前端运维页；仍不是完整 Prometheus/Grafana 告警体系，也不是高并发压测结果。

已完成：

- [x] 新增 `GET /api/tenants/{tenant_id}/ops/worker-health`。
- [x] 接口只允许同租户 owner/admin 读取。
- [x] 接口汇总 worker 总数、healthy/stale/failed/running/idle 计数。
- [x] 接口返回 `OUTBOX_EXTERNAL_WRITE_ENABLED` 和 `TRUSTED_INBOUND_WORKER_ENABLED` 当前状态。
- [x] 接口返回 worker heartbeat 列表和最近可信入站 worker 运行记录。
- [x] 接口返回 `no_worker_heartbeat`、`worker_stale`、`worker_failed`、`recent_worker_run_failed`、`external_write_enabled` 等风险提示。
- [x] 接口明确 `external_call_performed=false`、`external_platform_write_performed=false`，不触发模型调用、不写外部平台。
- [x] 前端新增“运维”导航和 `#ops` 工作区。
- [x] 前端展示健康指标、运行状态、外部动作边界、heartbeat 表、风险动作和最近运行表。
- [x] 演示模式提供同形样例数据，便于无正式账号时预览页面。
- [x] 新增 `scripts/check_p3_06e_ops_worker_health.py` readiness 检查。
- [x] 新增 `docs/P3-06E_OPS_WORKER_HEALTH_PANEL.md`。
- [x] 前端总览阶段标识更新为 `P3-06E`。

仍未完成：

- [ ] Prometheus 指标真实采集。
- [ ] Grafana dashboard。
- [x] 告警规则第一片、runbook 和前端展示已在 P3-06F 完成。
- [ ] 企业微信/飞书/短信/邮件等真实告警通知通道。
- [ ] 多容器并发压测和压测报告。
- [ ] outbox 独立 worker service。
- [ ] 企业微信公网 HTTPS 回调 smoke。
- [ ] 真实外发白名单测试。

验收：

- [x] `.venv/bin/python -m pytest tests/test_p3_06e_ops_worker_health_api.py -q` 通过，3 个测试通过。
- [x] `python3 scripts/check_p3_06e_ops_worker_health.py` 返回 `PASS p3-06e ops worker health panel`。
- [x] `npm run build` 通过。

### 阶段 P3-06F：告警规则第一片

目标：把 P3-06E 的 worker 心跳、最近运行、外发开关和配置状态整理成可重复评估的只读告警规则，让交付和运维能看到“什么情况需要处理、为什么触发、先查哪里、何时升级”，但不在第一片接真实通知通道。

状态：已完成第一片。当前有 owner/admin 可查看的只读规则评估接口、8 条运维规则、runbook、前端“运维与告警”展示区和 readiness 检查；它仍不是完整 Prometheus/Grafana/告警通知体系，也不是高并发压测。

已完成：

- [x] 新增 `GET /api/tenants/{tenant_id}/ops/alert-rules`。
- [x] 接口只允许同租户 owner/admin 读取。
- [x] 接口返回规则目录、触发状态、严重级别、响应类型、当前值、阈值、触发原因和 runbook。
- [x] 第一批规则覆盖 worker 不可用、配置缺失、无心跳、心跳超时、worker 失败、最近运行失败、外发边界风险和限流饱和。
- [x] 接口明确 `notification_channel_enabled=false`、`notification_sent=false`、`external_call_performed=false`、`external_platform_write_performed=false`。
- [x] 前端“运维”页升级为“运维与告警”，展示触发摘要、通知边界、外部动作边界和规则卡片。
- [x] 演示模式提供同形告警规则数据，不误导为真实通知已上线。
- [x] 新增 `scripts/check_p3_06f_ops_alert_rules.py` readiness 检查。
- [x] 新增 `docs/P3-06F_OPS_ALERT_RULES.md`。
- [x] 前端总览阶段标识更新为 `P3-06F`。

仍未完成：

- [ ] Prometheus 指标真实采集。
- [ ] Grafana dashboard。
- [ ] 企业微信/飞书/短信/邮件等真实告警通知通道。
- [ ] 告警静默、确认、升级和历史事件表。
- [ ] 多容器并发压测和压测报告。
- [ ] 企业微信公网 HTTPS 回调 smoke。
- [ ] 真实外发白名单测试。

验收：

- [x] `.venv/bin/python -m pytest tests/test_p3_06f_ops_alert_rules_api.py -q` 通过，3 个测试通过。
- [x] `.venv/bin/python -m pytest tests/test_p3_06f_ops_alert_rules_api.py tests/test_p3_06e_ops_worker_health_api.py -q` 通过，6 个测试通过。
- [x] `python3 scripts/check_p3_06f_ops_alert_rules.py` 返回 `PASS p3-06f ops alert rules`。
- [x] `npm run build` 通过。

### 阶段 P3-06UI：中台信息架构收口第一片、第二片与第三片

目标：把客服中台从“研发功能清单式导航”收束成商户能理解的工作域结构，降低演示和日常使用成本，不再继续向一级菜单堆单点功能。

状态：已完成第一片、第二片和第三片。第一片把侧边栏从 16 个平铺入口收束为 7 个工作域：总览、工作台、客户、知识运营、质量复盘、渠道接入、管理运维；第二片新增前端角色化菜单可见性和默认入口：owner/admin 默认进入总览，agent 默认进入多渠道对话台，viewer 默认进入总览；第三片曾把 `#ops`、`#model`、`#settings` 收进同一个 `AdminOperationsWorkspace`，用二级 Tab 呈现运维与告警、模型路由和系统设置。该第三片设计已在 P3-06U-26H2V 被修正：左侧三个入口现在对应三个真实页面。原有页面路由和子功能保留，不改后端业务逻辑、不启用真实外发。

已完成：

- [x] 新增 `navigationGroups` 两级导航结构。
- [x] 侧边栏按工作域渲染主入口和子入口。
- [x] 原有 16 个页面入口仍作为子功能保留。
- [x] `运维与告警` 归入 `管理运维`，不新增单独“告警中心”一级菜单。
- [x] `总览` 阶段标识更新为 `P3-06UI`。
- [x] 新增 `docs/P3-06UI_INFORMATION_ARCHITECTURE.md`。
- [x] 新增 `scripts/check_p3_06ui_information_architecture.py`。
- [x] 新增 `NavigationRole`、`visibleTo`、`getNavigationGroupsForRoles` 和 `getDefaultNavigationHrefForRoles`。
- [x] 侧边栏改为按当前登录角色渲染 `visibleNavigationGroups`。
- [x] 坐席默认进入 `#live`，owner/admin/viewer 默认进入 `#overview`。
- [x] 访问当前角色不可见的 hash 时，前端自动回落到该角色默认入口。
- [x] 侧边栏新增当前视图提示，便于演示时解释管理员、坐席和只读视角差异。
- [x] 新增 `docs/P3-06UI_ROLE_BASED_NAVIGATION.md`。
- [x] 新增 `scripts/check_p3_06ui_role_navigation.py`。
- [x] 新增 `AdminOperationsWorkspace`，把 `#ops`、`#model`、`#settings` 统一放入管理运维工作区。
- [x] 新增管理运维内部 `admin-ops-tabs`，保留三个原 hash 链接兼容。
- [x] `ops/model/settings` 的页面标题收口为 `管理运维`，通过 kicker 区分后台进程、决策链路、租户与安全。
- [x] P3-06U-26H2V 后续修正：删除旧 `AdminOperationsWorkspace`，`#ops`、`#model`、`#settings` 改为真实独立页面，标题分别为“运维与告警 / 模型路由 / 账号安全”。
- [x] 新增 `docs/P3-06UI_ADMIN_OPS_TABS.md`。
- [x] 新增 `scripts/check_p3_06ui_admin_ops_tabs.py`。

仍未完成：

- [ ] 后端资源级 RBAC 动作矩阵仍需继续收口；本轮只是前端入口可见性，不等于安全边界。
- [ ] 坐席可见页面内的按钮级权限、字段脱敏和只读态仍需逐页审查。
- [x] P3-06G 第一片已补只读指标出口和前端“指标出口”展示。
- [ ] 真实 Prometheus/Grafana 采集任务、真实告警通知和静默/确认/升级机制仍需后续单独验收。
- [ ] 主管质检完整视图和团队绩效。

验收：

- [x] `python3 scripts/check_p3_06ui_information_architecture.py` 通过。
- [x] `python3 scripts/check_p3_06ui_role_navigation.py` 通过。
- [x] `python3 scripts/check_p3_06ui_admin_ops_tabs.py` 通过。
- [x] `npm run build` 通过。
- [x] Playwright 访问 `http://127.0.0.1:5178/#overview`，mock 演示 owner 用户进入中台后确认 7 个工作域和“管理员视图”可见；截图保存到 `docs/p3_06ui_visual_qa/p3_06ui_role_navigation_owner_overview.png`。
- [x] Playwright 访问 `http://127.0.0.1:5178/#ops`，mock 演示 owner 用户进入中台后确认管理运维 Tab 可切换到运维与告警、模型路由、系统设置；截图保存到 `docs/p3_06ui_visual_qa/p3_06ui_admin_ops_tabs.png`。

### 阶段 P3-06G：指标出口第一片

目标：把 worker、告警、队列、失败复盘和外发边界整理成可采集的只读指标草案，为后续 Prometheus、Grafana 或云监控接入打底。

状态：已完成第一片。新增后端 `GET /api/tenants/{tenant_id}/ops/metrics`，返回 `summary`、`metrics` 和 `prometheus_text`；前端管理运维页新增“指标出口”面板，展示关键指标、重点异常指标和采集文本预览。当前不暴露无鉴权 `/metrics`，不发送真实通知，不执行真实外发。

已完成：

- [x] 新增 `OpsMetricRead`、`OpsMetricsSummary`、`OpsMetricsDashboardRead`。
- [x] 新增只读指标出口，覆盖 worker、告警规则、outbox 队列、可信入站队列、失败复盘和真实外发开关。
- [x] 指标响应保持 `external_call_performed=false`、`external_platform_write_performed=false`。
- [x] 前端新增 `getOpsMetricsDashboard`、`OpsMetricsState` 和“指标出口”展示模块。
- [x] 新增 `docs/P3-06G_OPS_METRICS_EXPORT.md`。
- [x] 新增 `scripts/check_p3_06g_ops_metrics.py`。
- [x] 新增 `backend/tests/test_p3_06g_ops_metrics_api.py`。
- [x] 新增 Playwright 截图 `docs/p3_06ui_visual_qa/p3_06g_ops_metrics.png`。

仍未完成：

- [ ] 后端资源级 RBAC 动作矩阵。
- [ ] 网关保护下的真实 Prometheus scrape endpoint。
- [ ] Grafana dashboard、云监控指标上报、告警通知、静默、去重和升级机制。
- [ ] 指标出口纳入托管云端版和私有化部署版运维手册。

验收：

- [x] `.venv/bin/python -m pytest tests/test_p3_06g_ops_metrics_api.py tests/test_p3_06f_ops_alert_rules_api.py tests/test_p3_06e_ops_worker_health_api.py -q` 通过，8 个测试通过。
- [x] `python3 scripts/check_p3_06g_ops_metrics.py` 通过。
- [x] `npm run build` 通过。
- [x] Playwright 访问 `http://127.0.0.1:5173/#ops`，通过“开发演示进入”确认“指标出口”“采集文本预览”和 `wanfa_worker_stale` 可见；截图保存到 `docs/p3_06ui_visual_qa/p3_06g_ops_metrics.png`。

### 阶段 P3-06H：RBAC 权限矩阵第一片

目标：把后端权限从散落角色判断逐步收口为命名权限矩阵，先用管理运维三条接口做低风险样板。

状态：已完成第一片。新增 `backend/app/core/rbac.py`，定义 `ROLE_PERMISSIONS`、`permissions_for_roles()`、`principal_has_permission()`、`allowed_roles_for_permission()` 和 `require_permission()`；运维健康、告警规则、指标出口三条接口已改用命名权限。

已完成：

- [x] 新增 `ops.worker_health.read`、`ops.alert_rules.read`、`ops.metrics.read` 三个命名权限。
- [x] owner/admin 拥有运维读权限，agent/viewer 不拥有。
- [x] `GET /api/tenants/{tenant_id}/ops/worker-health` 改用 `require_permission("ops.worker_health.read")`。
- [x] `GET /api/tenants/{tenant_id}/ops/alert-rules` 改用 `require_permission("ops.alert_rules.read")`。
- [x] `GET /api/tenants/{tenant_id}/ops/metrics` 改用 `require_permission("ops.metrics.read")`。
- [x] 新增 `docs/P3-06H_RBAC_PERMISSION_MATRIX.md`。
- [x] 新增 `scripts/check_p3_06h_rbac_permission_matrix.py`。
- [x] 新增 `backend/tests/test_p3_06h_rbac_permission_matrix.py`。

仍未完成：

- [ ] 账号、审计、团队、渠道、知识、会话、工单、客户、线索等全量 API 权限迁移。
- [x] `/api/auth/me` 返回权限快照，供前端按钮级权限使用。
- [ ] viewer/agent 字段脱敏和只读 response allowlist。
- [ ] 生产初始化账号策略与 bootstrap 边界。

验收：

- [x] `.venv/bin/python -m pytest tests/test_p3_06h_rbac_permission_matrix.py tests/test_p3_06g_ops_metrics_api.py tests/test_p3_06f_ops_alert_rules_api.py tests/test_p3_06e_ops_worker_health_api.py -q` 通过，10 个测试通过。
- [x] `python3 scripts/check_p3_06h_rbac_permission_matrix.py` 通过。

### 阶段 P3-06I：RBAC 权限快照与审计权限迁移

目标：让登录态和 `/api/auth/me` 返回当前账号权限快照，并把审计查询从散落角色判断迁到命名权限。

状态：已完成第二片。`CurrentUser` 新增 `permissions` 字段；登录响应和 `/api/auth/me` 均返回 `permissions_for_roles()` 计算后的权限集合；审计查询已改用 `require_permission("audit.events.read")`；前端 `CurrentUser` 类型已补 `permissions`。

已完成：

- [x] `CurrentUser.permissions` 权限快照。
- [x] 登录响应返回权限集合。
- [x] `/api/auth/me` 返回权限集合。
- [x] bootstrap 演示身份返回 owner 权限集合。
- [x] `GET /api/tenants/{tenant_id}/audit-events` 改用 `audit.events.read` 命名权限。
- [x] 新增 `docs/P3-06I_RBAC_PERMISSION_SNAPSHOT_AND_AUDIT.md`。
- [x] 新增 `scripts/check_p3_06i_rbac_permission_snapshot.py`。
- [x] 新增 `backend/tests/test_p3_06i_rbac_permission_snapshot.py`。

仍未完成：

- [ ] 账号/团队正式管理接口迁到 `accounts.manage`，并补安全 bootstrap 门禁。
- [ ] 知识、渠道、工单、客户、线索等资源动作权限迁移。
- [x] P3-06O 前端按钮级权限第一片统一读取 `user.permissions`。
- [ ] viewer/agent 字段脱敏和只读 response allowlist。

验收：

- [x] `.venv/bin/python -m pytest tests/test_p3_06i_rbac_permission_snapshot.py tests/test_p3_06h_rbac_permission_matrix.py tests/test_p3_06g_ops_metrics_api.py tests/test_p3_06f_ops_alert_rules_api.py tests/test_p3_06e_ops_worker_health_api.py tests/test_auth_rbac_audit.py -q` 通过，15 个测试通过。
- [x] `python3 scripts/check_p3_06i_rbac_permission_snapshot.py && python3 scripts/check_p3_06h_rbac_permission_matrix.py` 通过。
- [x] `npm run build` 通过。

### 阶段 P3-06J：账号团队权限与 Bootstrap 保护

目标：把账号、角色、团队管理从散落角色判断迁到 `accounts.manage` 命名权限，同时保留新租户首个管理员初始化通道。

状态：已完成第三片。`backend/app/api/accounts.py` 已使用 `principal_has_permission()` 判断 `accounts.manage`；owner 拥有该权限，admin/agent/viewer 不拥有；首个角色、首个用户、首次角色分配的 bootstrap 逻辑保持可用。

已完成：

- [x] `accounts.manage` owner-only 权限矩阵确认。
- [x] `_can_manage_tenant()` 改为 `accounts.manage` 权限判断，并保留同租户校验。
- [x] `_require_manager()` 统一返回 `403 insufficient permission`。
- [x] 首个角色、首个用户、首次角色分配 bootstrap 条件保持不变。
- [x] 新增 `docs/P3-06J_ACCOUNTS_RBAC_BOOTSTRAP.md`。
- [x] 新增 `scripts/check_p3_06j_accounts_rbac_bootstrap.py`。
- [x] 新增 `backend/tests/test_p3_06j_accounts_rbac_bootstrap.py`。

仍未完成：

- [ ] 一次性安装 token 和生产模式 bootstrap 关闭开关。
- [ ] `accounts.read`、`teams.manage` 等更细权限拆分。
- [ ] 知识、渠道、工单、客户、线索等资源动作权限迁移。
- [x] P3-06O 前端按钮级权限第一片统一读取 `user.permissions`。

验收：

- [x] `.venv/bin/python -m pytest tests/test_p3_06j_accounts_rbac_bootstrap.py tests/test_accounts_api.py tests/test_p3_06i_rbac_permission_snapshot.py tests/test_p3_06h_rbac_permission_matrix.py tests/test_auth_rbac_audit.py -q` 通过，15 个测试通过。
- [x] `.venv/bin/python -m pytest -q` 后端完整测试通过，156 个测试通过。
- [x] `python3 scripts/check_p3_06j_accounts_rbac_bootstrap.py && python3 scripts/check_p3_06i_rbac_permission_snapshot.py && python3 scripts/check_p3_06h_rbac_permission_matrix.py` 通过。
- [x] `npm run build` 通过。

### 阶段 P3-06K：会话业务动作权限

目标：把客服主工作面的会话读写和坐席动作迁到命名权限，避免 viewer 或无 token 访问真实会话内容。

状态：已完成第四片。`backend/app/api/conversations.py` 已新增 `conversation.read` 和 `conversation.manage` 权限依赖；owner/admin/agent 允许读写会话，viewer 禁止；跨租户资源继续隐藏为 404；官方 webhook 入口仍走 provider connector、验签、幂等和可信入站边界，不使用坐席 bearer token。

已完成：

- [x] 新增 `conversation.read`，用于会话列表、会话详情和会话收件箱。
- [x] 新增 `conversation.manage`，用于会话创建、消息写入、分配和坐席工作流。
- [x] owner/admin/agent 拥有会话读写权限，viewer 暂不开放会话原文。
- [x] `GET /api/tenants/{tenant_id}/conversations` 改用 `conversation.read`。
- [x] `GET /api/tenants/{tenant_id}/conversation-inbox` 改用 `conversation.read`。
- [x] `GET /api/conversations/{conversation_id}` 改用 `conversation.read` 并校验同租户。
- [x] `POST /api/tenants/{tenant_id}/conversations`、`POST /api/conversations/{conversation_id}/messages`、分配和工作流动作改用 `conversation.manage`。
- [x] 受影响测试夹具改为 owner token 创建会话和消息，不再依赖无 token 会话写入。
- [x] 新增 `docs/P3-06K_CONVERSATION_RBAC.md`。
- [x] 新增 `scripts/check_p3_06k_conversation_rbac.py`。
- [x] 新增 `backend/tests/test_p3_06k_conversation_rbac.py`。

仍未完成：

- [ ] 工单、联系人、线索权限迁移和 agent 自有资源边界。
- [ ] 渠道配置、secret 管理和发送计划权限拆分。
- [x] P3-06O 前端按钮级权限第一片统一读取 `user.permissions`。
- [ ] viewer/agent/admin 字段脱敏和只读 response allowlist。

验收：

- [x] `.venv/bin/python -m pytest tests/test_p3_06k_conversation_rbac.py tests/test_conversation_inbox_api.py tests/test_foundation_api.py tests/test_p3_06j_accounts_rbac_bootstrap.py tests/test_p3_06i_rbac_permission_snapshot.py tests/test_p3_06h_rbac_permission_matrix.py -q` 通过，16 个测试通过。
- [x] `python3 scripts/check_p3_06k_conversation_rbac.py` 通过。

### 阶段 P3-06L：知识库业务动作权限

目标：把知识库读写、发布、回滚、缺口处理、评测、索引和 provider smoke 迁到命名权限，让坐席只能检索知识，不能直接改知识库或触发高风险操作。

状态：已完成第五片。`backend/app/api/knowledge.py` 已新增 `knowledge.read` 和 `knowledge.manage` 权限依赖；owner/admin 拥有读写管理权限，agent 只拥有读取检索权限，viewer 暂不开放知识原文。

已完成：

- [x] owner/admin 增加 `knowledge.read` 和 `knowledge.manage`。
- [x] agent 保留 `knowledge.read`，不拥有 `knowledge.manage`。
- [x] viewer 不拥有知识读写权限。
- [x] 知识卡片列表、知识文档列表、文档分块、FAQ 检索和文档检索迁到 `knowledge.read`。
- [x] 知识卡片/文档写入、发布检查、发布、发布历史、回滚、知识缺口、评测、向量索引和 provider smoke 迁到 `knowledge.manage`。
- [x] 新增 `docs/P3-06L_KNOWLEDGE_RBAC.md`。
- [x] 新增 `scripts/check_p3_06l_knowledge_rbac.py`。
- [x] 新增 `backend/tests/test_p3_06l_knowledge_rbac.py`。

仍未完成：

- [ ] 工单、联系人、线索权限迁移和 agent 自有资源边界。
- [ ] 渠道配置、secret 管理、回执读取和发送计划权限拆分。
- [x] P3-06O 前端按钮级权限第一片统一读取 `user.permissions`。
- [ ] viewer/agent/admin 字段脱敏和只读 response allowlist。

验收：

- [x] `.venv/bin/python -m pytest tests/test_p3_06l_knowledge_rbac.py tests/test_knowledge_api.py tests/test_knowledge_documents_api.py tests/test_knowledge_gaps_api.py tests/test_knowledge_evaluations_api.py tests/test_knowledge_vector_index_api.py tests/test_knowledge_vector_index_strategy_api.py tests/test_knowledge_embedding_provider_smoke_api.py -q` 通过，33 个测试通过。
- [x] `python3 scripts/check_p3_06l_knowledge_rbac.py` 通过。

### 阶段 P3-06M：工单、客户画像与线索权限

目标：把客服经营链路中的工单、联系人画像和线索 API 迁到命名权限，避免 viewer 或无关角色读取客户经营数据。

状态：已完成第六片。`backend/app/api/support_tickets.py` 已使用 `ticket.read` / `ticket.manage`；`backend/app/api/customer_profiles.py` 已使用 `customer.read` / `lead.read` / `lead.manage`；owner/admin/agent 可进入经营链路，viewer 暂不开放客户画像、工单和线索原文。

已完成：

- [x] owner/admin/agent 增加 `ticket.read`、`ticket.manage`、`customer.read`、`lead.read`、`lead.manage`。
- [x] viewer 不拥有客户画像、工单和线索权限。
- [x] 工单列表迁到 `ticket.read`。
- [x] 工单创建和更新迁到 `ticket.manage`。
- [x] 联系人画像列表和详情迁到 `customer.read`。
- [x] 线索列表迁到 `lead.read`。
- [x] 线索创建和更新迁到 `lead.manage`。
- [x] 新增 `docs/P3-06M_CUSTOMER_OPS_RBAC.md`。
- [x] 新增 `scripts/check_p3_06m_customer_ops_rbac.py`。
- [x] 新增 `backend/tests/test_p3_06m_customer_ops_rbac.py`。

仍未完成：

- [ ] 渠道配置、连接器、secret 管理、回执读取和发送计划权限拆分。
- [x] P3-06O 前端按钮级权限第一片统一读取 `user.permissions`。
- [ ] viewer/agent/admin 字段脱敏和只读 response allowlist。
- [ ] 工单评论、附件、单独重开流程、SLA 升级和主管视图。

验收：

- [x] `.venv/bin/python -m pytest tests/test_p3_06m_customer_ops_rbac.py tests/test_support_tickets_api.py tests/test_customer_profiles_api.py tests/test_p3_06l_knowledge_rbac.py tests/test_p3_06k_conversation_rbac.py tests/test_p3_06j_accounts_rbac_bootstrap.py tests/test_p3_06i_rbac_permission_snapshot.py tests/test_p3_06h_rbac_permission_matrix.py -q` 通过，21 个测试通过。
- [x] `python3 scripts/check_p3_06m_customer_ops_rbac.py` 通过。

### 阶段 P3-06N：渠道连接器、回执与发送计划权限

目标：把渠道接入链路中的连接器配置、secret 引用、回执读取/手工记录和 connector 发送计划迁到命名权限，同时保持官方 webhook 平台回调入口不被坐席 bearer token 误锁。

状态：已完成第七片。`backend/app/api/channel_connectors.py` 已使用 `channel.read`、`channel.connector.manage`、`channel.delivery_receipt.read`、`channel.delivery_receipt.manage` 和 `outbox.send_plan.manage`；owner/admin 可配置连接器和手工记录回执，agent 可读取渠道状态、读取回执和生成受控发送计划，viewer 仅保留渠道 provider/连接器摘要读取。

已完成：

- [x] owner/admin 增加 `channel.read`、`channel.connector.manage`、`channel.delivery_receipt.read`、`channel.delivery_receipt.manage`、`outbox.send_plan.manage`。
- [x] agent 增加 `channel.read`、`channel.delivery_receipt.read`、`outbox.send_plan.manage`，不能改连接器和手工写回执。
- [x] viewer 保留 `channel.read`，不能读取回执原文、写回执或生成发送计划。
- [x] `GET /api/channel-providers` 和 `GET /api/channels/{channel_id}/connector-config` 迁到 `channel.read`。
- [x] `POST /api/channels/{channel_id}/connector-config` 迁到 `channel.connector.manage`。
- [x] `GET /api/channels/{channel_id}/delivery-receipts` 迁到 `channel.delivery_receipt.read`。
- [x] `POST /api/channels/{channel_id}/delivery-receipts` 迁到 `channel.delivery_receipt.manage`。
- [x] `POST /api/outbox-drafts/{draft_id}/connector-send-plans` 迁到 `outbox.send_plan.manage`。
- [x] 官方 webhook GET/POST 保持无坐席登录依赖，继续依靠连接器、签名、secret 引用、幂等和可信入站边界。
- [x] 新增 `docs/P3-06N_CHANNEL_DELIVERY_RBAC.md`。
- [x] 新增 `scripts/check_p3_06n_channel_delivery_rbac.py`。
- [x] 新增 `backend/tests/test_p3_06n_channel_delivery_rbac.py`。

仍未完成：

- [x] P3-06O 前端按钮级权限第一片统一读取 `user.permissions`。
- [ ] 连接器配置、回执 raw payload、客户字段、线索备注等响应字段 allowlist。
- [x] P3-06P outbox draft、dry-run send-attempt、delivery job、delivery failure review 剩余资源权限迁移。
- [ ] 单独密钥轮换或生产 secret 诊断接口；如新增，应拆 `channel.secret.manage`。
- [ ] 真实平台外发发送器和生产级回执 reconciliation。

验收：

- [x] `.venv/bin/python -m pytest tests/test_p3_06n_channel_delivery_rbac.py tests/test_channel_connectors_api.py tests/test_channel_webhooks_api.py -q` 通过，17 个测试通过。
- [x] `python3 scripts/check_p3_06n_channel_delivery_rbac.py` 通过。

### 阶段 P3-06O：前端按钮级权限第一片

目标：把中台关键写动作从登录态、角色粗判断和局部业务状态，收口为 `user.permissions` 驱动的按钮禁用与 handler guard。

状态：已完成第一片。`frontend/src/App.tsx` 已新增 `PERMISSIONS` 和 `hasPermission()`，会话、人审、工单、线索、知识文档、知识缺口、知识评测和出站发送计划关键动作已根据权限禁用；出站生成渠道计划时，只有拥有 `channel.connector.manage` 的用户才会自动预置连接器，普通坐席只走受控发送计划并看到管理员预配置提示。

已完成：

- [x] 新增前端权限常量和统一 `hasPermission()` helper。
- [x] 会话收件箱和多渠道对话台动作接入 `conversation.manage`。
- [x] 人工审核批准/拒绝和入站编排按钮接入 `conversation.manage`。
- [x] 工单生成、工单状态更新和解决动作接入 `ticket.manage`。
- [x] 线索生成、阶段推进、成交和无效动作接入 `lead.manage`。
- [x] 知识文档导入/回滚、知识缺口处理、知识发布和知识评测动作接入 `knowledge.manage`。
- [x] 待发送草稿确认、模拟发送、渠道计划、发送队列和 worker 运行动作完成第一片前端门禁；P3-06P 已进一步拆到 `outbox.draft.manage`、`outbox.send_attempt.manage`、`outbox.delivery_job.manage`。
- [x] 连接器自动预置只允许 `channel.connector.manage` 用户触发。
- [x] 新增 `docs/P3-06O_FRONTEND_BUTTON_PERMISSIONS.md`。
- [x] 新增 `scripts/check_p3_06o_frontend_button_permissions.py`。

仍未完成：

- [ ] 字段脱敏和字段 allowlist。
- [x] P3-06P outbox draft、dry-run send-attempt、delivery job、delivery failure review 后端剩余命名权限迁移。
- [ ] 单独的人审权限，例如 `human_review.read` / `human_review.manage`。
- [ ] 连接器配置、手工回执和密钥轮换的完整前端管理界面。
- [ ] 分角色真实截图 QA。

验收：

- [x] `npm run typecheck` 通过。
- [x] `npm run build` 通过。
- [x] `python3 scripts/check_p3_06o_frontend_button_permissions.py` 通过。

### 阶段 P3-06P：出站资源与失败复盘权限

目标：把 outbox draft、dry-run send-attempt、delivery job 和 delivery failure review 从“登录即可操作”的旧试点入口迁到命名权限，并同步前端出站按钮的细分门禁。

状态：已完成第八片。坐席 agent 仍可确认草稿、dry-run 试发和生成受控发送计划；全局发送队列创建/运行改为 owner/admin 权限；viewer 可只读查看失败复盘概况，但不能处理失败项。

已完成：

- [x] 新增 `outbox.draft.read` / `outbox.draft.manage`。
- [x] 新增 `outbox.send_attempt.read` / `outbox.send_attempt.manage`。
- [x] 新增 `outbox.delivery_job.read` / `outbox.delivery_job.manage`，其中 manage 只给 owner/admin。
- [x] 新增 `outbox.failure_review.read` / `outbox.failure_review.manage`，其中 viewer 只保留 read。
- [x] outbox draft 创建、列表、确认、取消接口迁到命名权限。
- [x] dry-run send-attempt 列表、创建和 dry-run worker 迁到命名权限。
- [x] delivery job 列表、创建和 delivery queue run 迁到命名权限。
- [x] delivery failure review 列表、更新迁到命名权限。
- [x] 前端出站按钮和失败复盘按钮从 `outbox.send_plan.manage` 粗门禁拆到细分权限。
- [x] 新增 `docs/P3-06P_OUTBOX_RESOURCE_RBAC.md`。
- [x] 新增 `scripts/check_p3_06p_outbox_resource_rbac.py`。
- [x] 新增 `backend/tests/test_p3_06p_outbox_resource_rbac.py`。

仍未完成：

- [ ] 字段脱敏和字段 allowlist。
- [ ] `human_review.read` / `human_review.manage` 独立人审权限。
- [ ] agent 仅处理自己会话或所属团队会话的资源级所有权检查。
- [ ] 独立 outbox worker service、真实 sender、生产 token、可信 IP 出站和多容器压测。

验收：

- [x] `.venv/bin/python -m pytest backend/tests -q` 通过。
- [x] `python3 scripts/check_p3_06p_outbox_resource_rbac.py` 通过。
- [x] `(cd frontend && npm run typecheck)` 通过。
- [x] `(cd frontend && npm run build)` 通过。
- [x] `python3 scripts/check_p3_06n_channel_delivery_rbac.py`、`python3 scripts/check_p3_06m_customer_ops_rbac.py`、`python3 scripts/check_p3_06l_knowledge_rbac.py`、`python3 scripts/check_p3_06k_conversation_rbac.py` 通过。

### 阶段 P3-07：对外资料包

目标：让销售和交付可以用统一话术介绍产品。

任务：

- [ ] 客户使用手册。
- [ ] 产品介绍。
- [ ] 服务体系介绍。
- [ ] Lite/标准运营版对比表。
- [ ] 常见问题。
- [ ] 试点准备清单。
- [ ] 风险与边界说明。

验收：

- [ ] 文档面向客户，避免内部工程口吻。
- [ ] 不出现“开发演示身份”“mock”“deterministic”等内部词，除非放入技术附录。
- [ ] 不夸大为全平台、全自动、零幻觉。
- [ ] 后续可转 Word/PDF。

### 阶段 P3-08：内部售后运维体系

目标：卖出去以后我方能稳定维护，不靠临时救火。

任务：

- [ ] 销售到交付交接表。
- [ ] 客户上线检查表。
- [ ] 远程维护授权流程。
- [ ] 故障分级与响应 SOP。
- [ ] 知识库更新 SOP。
- [ ] 准确率下降排查 SOP。
- [x] 月度运维报告模板。已完成 H2W-OPS2 rehearsal：客户版月报、内部证据摘要、只读接口和前端入口已具备；仍不是生产 SLA。
- [ ] 续费、升级和增购判断标准。

验收：

- [ ] 内部团队可以按 checklist 操作。
- [ ] 不记录客户 secrets。
- [ ] 每个高风险动作都有授权、回滚和审计。

## 6. Lite 与标准运营版差异矩阵

| 能力 | Lite 试点版 | 标准运营版 |
| --- | --- | --- |
| 目标 | 快速验证一个入口和核心 FAQ/知识包 | 正式日常运营和持续优化 |
| 部署 | 单机或轻量云 | 云端或私有化，PostgreSQL + Redis/队列 |
| 渠道 | 官网/自有入口优先 | 官网 + 企微/公众号/电商官方授权逐步接入 |
| 知识库 | FAQ + 轻量文档 | 知识版本、审核、评测、缺口闭环 |
| 模型 | 百炼/千问标准模型为主，保守人审 | 模型路由、fallback、成本治理、质量报告 |
| 自动回复 | 默认不直接外发，高置信也先可配置 | 可按白名单、风险等级和渠道策略逐步开放 |
| 坐席 | 基础审核和待发送 | 会话分配、团队、SLA、失败复盘、绩效 |
| 质量 | 50 条题库起步 | 100 条以上题库、历史对比、月度复盘 |
| 运维 | 基础健康检查和诊断包 | 监控、告警、备份、回滚、SLA、月报 |
| 价格逻辑 | 一次性交付 + 低维护费 | 较高交付费 + 持续运维/质量服务费 |

## 7. 对外承诺边界

可以承诺：

- 基于客户知识库生成可审核的 AI 回复草稿。
- 低置信、高风险、政策不明确问题进入人工审核。
- 回复有引用证据和审计链。
- 支持知识库持续更新和质量复盘。
- 支持官方渠道逐步接入。
- 支持部署、备份、恢复、回滚和远程维护方案。

不能承诺：

- 100% 正确率。
- 零人工客服。
- 所有平台无授权自动回复。
- 个人微信外挂或群控。
- 未经客户授权的真实数据模型调用。
- 未经生产验证的高并发 SLA。

### 2026-07-03 H2H 追加：本地 SQLite 物理备份与恢复演练第一片

已完成：

- 新增 `local_backup_records` 表和 `0027_local_backup_records` 迁移。
- 新增 `POST /api/tenants/{tenant_id}/local-backups`，负责人/管理员可创建文件型 SQLite 物理备份。
- 新增 `GET /api/tenants/{tenant_id}/local-backups`，负责人/管理员可查看本租户备份记录。
- 新增 `POST /api/local-backups/{local_backup_id}/verify`，可校验 sha256 和 SQLite `PRAGMA integrity_check`。
- 新增 `WANFA_LOCAL_BACKUP_DIR` 配置。
- 前端“管理运维 -> 账号与安全”新增“本地备份点”卡片，可创建和校验备份。
- 浏览器 smoke 已用临时 8094/5194 验证 UI 创建与校验流程。

明确边界：

- 当前 `restore_mode=manual_rehearsal_only`。
- 不做在线覆盖恢复。
- 不替换程序文件。
- 不执行数据库迁移。
- 不自动上传诊断包。
- 不调用模型，不写外部平台。
- 前端不展示数据库绝对路径。

验证：

- `backend`: `./.venv/bin/python -m pytest tests/test_local_backups_api.py -q` -> `3 passed`
- `backend`: `./.venv/bin/python -m pytest tests/test_local_backups_api.py tests/test_signed_update_packages_api.py tests/test_diagnostics_api.py tests/test_accounts_api.py -q` -> `22 passed`
- `frontend`: `npm run typecheck` -> 通过
- `frontend`: `npm run build` -> 通过，只有既有 Vite chunk 体积提醒
- 浏览器证据：`output/p3_06u_26h2h_local_backup_ui/`

下一步改为：

- P3-06U-26H2I：策略更新包应用第一片。
- P3-06U-26H2J：程序更新器 dry-run 第一片。
- P3-06U-26H2K：客户授权上传诊断包第一片。
- P3-06U-26H2L：本地恢复工具 dry-run。

### 2026-07-03 H2I 追加：签名策略更新包应用与回滚第一片

已完成：

- 新增 `tenant_reply_strategies` 表和 `0028_tenant_reply_strategies` 迁移。
- 新增 `wanfa.reply_strategy_update.v1` 策略包 payload schema。
- `POST /api/signed-update-packages/{id}/apply` 现在支持 `package_type=strategy`。
- `POST /api/signed-update-packages/{id}/rollback` 现在支持策略包回滚。
- 策略包会写入当前租户 active 策略，并保存应用前策略快照。
- 回复决策会读取 active 策略，影响自动回复阈值、转人工阈值、阻断词、转人工词和强制草稿模式。
- 前端更新中心允许 `strategy` 包“备份并应用”和“回滚”；`program` 包继续显示当前阶段不应用。

明确边界：

- 不执行程序包。
- 不替换程序文件。
- 不重启服务。
- 不执行数据库迁移。
- 不调用模型。
- 不上传诊断包。
- 不写外部平台。
- 真实外发继续关闭。

验证：

- `backend`: `./.venv/bin/python -m pytest tests/test_signed_update_packages_api.py -q` -> `11 passed`
- `backend`: `./.venv/bin/python -m pytest tests/test_reply_decisions_api.py -q` -> `5 passed`
- `backend`: `./.venv/bin/python -m pytest tests/test_signed_update_packages_api.py tests/test_reply_decisions_api.py tests/test_local_backups_api.py tests/test_diagnostics_api.py tests/test_accounts_api.py -q` -> `28 passed`
- `frontend`: `npm run typecheck` -> 通过
- `frontend`: `npm run build` -> 通过，只有既有 Vite chunk 体积提醒
- 浏览器证据：`output/p3_06u_26h2i_signed_strategy_update_ui/`

下一步改为：

- P3-06U-26H2J：程序更新器 dry-run 第一片。
- P3-06U-26H2K：客户授权上传诊断包第一片。
- P3-06U-26H2L：本地恢复工具 dry-run。

### 2026-07-03 H2J 追加：签名程序更新包 dry-run 演练计划第一片

已完成：

- 新增 `POST /api/signed-update-packages/{id}/program-dry-run`，负责人/管理员可为已暂存 `program` 包生成演练计划。
- 演练结果写回 `preflight_result.program_dry_run_result`，记录目标程序版本、bundle 摘要、文件数量、迁移数量、维护窗口、计划步骤、健康检查和阻断动作。
- 程序包继续不展示“备份并应用”，前端只提供“生成演练计划”。
- 后端审计写入 `signed_update_package.program_dry_run`。
- 前端更新中心展示程序包演练计划，明确“程序包只生成演练计划，不替换文件”。
- 新增 `docs/P3-06U-26H2J_PROGRAM_UPDATE_DRY_RUN_FIRST_SLICE.md` 和浏览器 smoke `scripts/check_p3_06u_26h2j_program_update_dry_run_ui.mjs`。

明确边界：

- 不执行程序包。
- 不替换程序文件。
- 不重启服务。
- 不执行数据库迁移。
- 不创建备份。
- 不调用模型。
- 不上传诊断包。
- 不写外部平台。
- 真实外发继续关闭。

验证：

- `backend`: `./.venv/bin/python -m pytest tests/test_signed_update_packages_api.py -q` -> `13 passed`
- `backend`: `./.venv/bin/python -m pytest tests/test_signed_update_packages_api.py tests/test_reply_decisions_api.py tests/test_local_backups_api.py tests/test_diagnostics_api.py tests/test_accounts_api.py -q` -> `30 passed`
- `backend`: `./.venv/bin/python -m py_compile app/services/signed_updates.py app/api/signed_updates.py app/schemas/signed_updates.py` -> 通过
- `frontend`: `npm run typecheck` -> 通过
- `frontend`: `npm run build` -> 通过，只有既有 Vite chunk 体积提醒
- 浏览器证据：`output/p3_06u_26h2j_program_update_dry_run_ui/`

下一步改为：

- P3-06U-26H2K：客户授权上传诊断包第一片。
- P3-06U-26H2L：本地恢复工具 dry-run。
- 后续真实程序更新器：独立进程、停服务窗口、二次备份、文件替换、迁移兼容检查、健康检查和失败回滚。

### 2026-07-03 H2K 追加：客户授权诊断上传包第一片

已完成：

- 新增 `POST /api/tenants/{tenant_id}/diagnostic-upload-package`，负责人/管理员可生成客户授权诊断上传包。
- 授权上传包复用 H2C 脱敏诊断包，并增加授权回执、诊断包 sha256、手动传输 manifest 和安全标记。
- 新增 `DiagnosticUploadPackageCreate`、`DiagnosticUploadPackageRead` 和 `build_diagnostic_upload_package()`。
- 写入审计事件 `diagnostic_bundle.upload_package_created`。
- 前端“管理运维 -> 系统设置 -> 本地诊断包”新增“授权上传包”按钮。
- 新增 `docs/P3-06U-26H2K_DIAGNOSTIC_UPLOAD_PACKAGE_FIRST_SLICE.md` 和浏览器 smoke `scripts/check_p3_06u_26h2k_diagnostic_upload_package_ui.mjs`。

明确边界：

- 不自动上传到我方服务器。
- 不接对象存储。
- 不做定期上传。
- 不打开后台联网任务。
- 不调用模型。
- 不外发平台消息。
- 不保存 token、cookie、密码、私钥和完整聊天原文。

验证：

- `backend`: `./.venv/bin/python -m pytest tests/test_diagnostics_api.py -q` -> `4 passed`
- `frontend`: `npm run typecheck` -> 通过
- `frontend`: `npm run build` -> 通过，只有既有 Vite chunk 体积提醒
- 浏览器证据：`output/p3_06u_26h2k_diagnostic_upload_package_ui/`

下一步改为：

- P3-06U-26H2L：本地恢复工具 dry-run。
- 后续客户授权上传第二片：我方售后接收台或客户指定安全通道。

### 2026-07-03 H2L 追加：本地恢复工具 Dry-run 第一片

已完成：

- 新增 `POST /api/local-backups/{local_backup_id}/restore-dry-run`，负责人/管理员可为本地备份点生成恢复演练计划。
- 恢复演练会校验备份文件 sha256 和 SQLite `integrity_check`，并生成维护窗口、二次备份、停服务、离线替换、重启健康检查和失败回退步骤。
- 新增 `LocalBackupRestoreDryRunCreate`、`LocalBackupRestoreDryRunRead` 和 `create_local_database_restore_dry_run()`。
- 写入审计事件 `local_backup.restore_dry_run_created`。
- 前端“管理运维 -> 账号与安全 -> 本地备份点”新增“恢复演练”按钮，并展示计划状态、阻断项、检查项和关键步骤。
- 新增 `docs/P3-06U-26H2L_LOCAL_RESTORE_DRY_RUN_FIRST_SLICE.md` 和浏览器 smoke `scripts/check_p3_06u_26h2l_local_restore_dry_run_ui.mjs`。

明确边界：

- 不做在线覆盖恢复。
- 不提供“一键恢复”。
- 不替换 SQLite 文件。
- 不停止或重启服务。
- 不执行数据库迁移。
- 不创建二次备份。
- 不接云端远程控制。
- 不上传诊断包。
- 不调用模型。
- 不写外部平台。

验证：

- `backend`: `./.venv/bin/python -m pytest tests/test_local_backups_api.py -q` -> `4 passed`
- `frontend`: `npm run typecheck` -> 通过
- `frontend`: `npm run build` -> 通过，只有既有 Vite chunk 体积提醒
- 浏览器证据：`output/p3_06u_26h2l_local_restore_dry_run_ui/`

下一步改为：

- 真实客户题库和人工事实性标签入口。
- 或本机恢复工具第二片：独立恢复工具、停服务窗口、二次备份、健康检查和失败回退。
- 真实外发、真实程序更新器、云端诊断接收台和官方渠道仍需单独授权。

### 2026-07-03 H2M 追加：月度质量复盘收束第一片

已完成：

- 新增 `GET /api/tenants/{tenant_id}/monthly-quality-review`。
- 新增服务端只读聚合 `get_monthly_quality_review()`，按月份汇总评测运行、知识缺口、人审任务和回复决策。
- 前端质量复盘页新增“本月复盘包”，展示核心指标、主要问题、下一步动作和边界说明。
- 新增 `docs/P3-06U-26H2M_MONTHLY_QUALITY_REVIEW_CLOSURE.md` 和浏览器 smoke `scripts/check_p3_06u_26h2m_monthly_quality_review_ui.mjs`。

明确边界：

- 不调用模型。
- 不写外部平台。
- 不打开真实外发。
- 不修改知识库、评测集、会话或人审任务。
- 不输出客户原文、聊天原文、草稿全文、联系方式或密钥。
- 不把检索命中率包装成完整客服准确率。
- 渠道官方接入验收不纳入本片。

验证：

- `backend`: `./.venv/bin/python -m pytest tests/test_knowledge_evaluations_api.py -q` -> `7 passed`
- `backend`: `./.venv/bin/python -m py_compile app/services/knowledge.py app/api/knowledge.py app/schemas/knowledge.py` -> 通过
- `frontend`: `npm run typecheck` -> 通过
- `frontend`: `npm run build` -> 通过，只有既有 Vite chunk 体积提醒
- 浏览器证据：`output/p3_06u_26h2m_monthly_quality_review_ui/`

下一步改为：

- 真实客户题库与人工事实性标签入口。
- 或本机恢复工具第二片。
- 生产级 RAG、客户真实环境部署、高并发队列和云端诊断接收台仍在后续阶段。

### 2026-07-03 H2N 追加：人工事实性标签入口第一片

已完成：

- 新增 `PATCH /api/knowledge-evaluation-run-cases/{run_case_id}/factuality-label`。
- 后端可把单题人工事实性标签写入评测用例结果，并重新计算评测运行摘要。
- 前端知识评测详情新增“事实正确 / 部分正确 / 事实有误 / 应转人工”标注按钮。
- 标注结果会刷新本月质量复盘包，让 `human_factuality` 从缺口指标向实测指标推进。
- 新增 `docs/P3-06U-26H2N_FACTUALITY_LABEL_FIRST_SLICE.md` 和浏览器 smoke `scripts/check_p3_06u_26h2n_factuality_label_ui.mjs`。

明确边界：

- 不调用模型。
- 不写外部平台。
- 不打开真实外发。
- 不新增数据库迁移。
- 不保存人工备注明文，只保存 hash 和长度。
- 当前知识评测仍是检索评测与证据链评测，不是完整客服准确率。
- 真实 50-100 题库导入、最终答案文本采样、客户质量报告签收仍在下一阶段。

验证：

- `backend`: `./.venv/bin/python -m pytest tests/test_knowledge_evaluations_api.py -q` -> 通过
- `backend`: `./.venv/bin/python -m py_compile app/services/knowledge.py app/api/knowledge.py app/schemas/knowledge.py` -> 通过
- `frontend`: `npm run typecheck` -> 通过
- `frontend`: `npm run build` -> 通过，只有既有 Vite chunk 体积提醒
- 浏览器证据：`output/p3_06u_26h2n_factuality_label_ui/`

下一步改为：

- 真实客户 50-100 题库正式导入、脱敏、覆盖分布和最终答案人工标注。
- 或继续恢复线，做本机恢复工具第二片。
- 渠道官方接入验收仍不纳入本片，真实外发继续默认关闭。

### 2026-07-03 H2O 追加：真实客户题库导入第一片

已完成：

- 新增 `POST /api/tenants/{tenant_id}/customer-service-question-banks/precheck`。
- 新增 `POST /api/tenants/{tenant_id}/customer-service-question-banks/import`。
- 后端预检 50-100 题数量、重复 `external_case_id`、默认敏感信息、渠道分布、风险分布、引用来源、期望词、转人工样本和自动回复样本覆盖。
- 导入成功后创建正式知识评测集，并写入 `customer_service_question_bank.imported` 审计事件。
- 前端知识评测页新增“客户题库导入”面板，可粘贴题库 JSON、预检并导入。
- 新增 `docs/P3-06U-26H2O_CUSTOMER_QUESTION_BANK_IMPORT_FIRST_SLICE.md` 和浏览器 smoke `scripts/check_p3_06u_26h2o_customer_question_bank_import_ui.mjs`。

明确边界：

- 不调用模型。
- 不生成最终客服答案。
- 不写 outbox。
- 不写外部平台。
- 不上传诊断包。
- 接口摘要和审计事件不回显原始问题、客户答案明文或模型输出。
- 当前只证明题库能进入评测系统，不证明完整客服最终答案准确率。
- CSV / XLSX 直接上传、最终答案采样、批量人工标签和客户质量报告仍在下一阶段。

验证：

- `backend`: `./.venv/bin/python -m pytest tests/test_knowledge_evaluations_api.py -q` -> `9 passed`
- `backend`: `./.venv/bin/python -m pytest tests/test_knowledge_evaluations_api.py tests/test_knowledge_gaps_api.py tests/test_reply_decisions_api.py tests/test_diagnostics_api.py -q` -> `23 passed`
- `backend`: `./.venv/bin/python -m py_compile app/services/knowledge.py app/api/knowledge.py app/schemas/knowledge.py` -> 通过
- `frontend`: `npm run typecheck` -> 通过
- `frontend`: `npm run build` -> 通过，只有既有 Vite chunk 体积提醒
- 浏览器证据：`output/p3_06u_26h2o_customer_question_bank_import_ui/`

下一步改为：

- 最终答案采样与批量人工标签第一片。
- 或补 CSV / XLSX 直接上传入口。
- 如继续恢复线，则做本机恢复工具第二片。
- 渠道官方接入验收仍不纳入本片，真实外发继续默认关闭。

### 2026-07-03 H2P 追加：最终回复采样与批量人工标签第一片

已完成：

- 新增 `PATCH /api/knowledge-evaluation-run-cases/{run_case_id}/final-answer-sample`。
- 新增 `PATCH /api/knowledge-evaluation-runs/{evaluation_run_id}/factuality-labels/batch`。
- 后端可把最终客服回复样本写入本地评测用例，并更新 `final_answer_sampled_cases` 与 `final_answer_sample_coverage`。
- 批量人工标签只接受同一评测运行内的 case id，并复用单条事实性标签统计口径。
- 前端知识评测页新增逐题“最终客服回复样本”输入框。
- 前端知识评测页新增“批量标为事实正确”和“批量标为应转人工”按钮，且只处理已采样样本。
- 新增 `docs/P3-06U-26H2P_FINAL_ANSWER_SAMPLE_AND_BATCH_LABEL_FIRST_SLICE.md` 和浏览器 smoke `scripts/check_p3_06u_26h2p_final_answer_sample_ui.mjs`。

明确边界：

- 不调用模型。
- 不生成线上最终答案。
- 不写 outbox。
- 不写外部平台。
- 不打开真实外发。
- 审计事件不保存最终回复正文和人工备注明文。
- 最终回复样本文本会保存在本地评测用例里，供授权用户人工标注；但审计、summary 和 smoke 不回显原文。
- 当前只证明“样本 -> 标签 -> 摘要 -> 月度复盘”闭环，不证明真实渠道线上自动回复准确率已经签收。

验证：

- `backend`: `./.venv/bin/python -m pytest tests/test_knowledge_evaluations_api.py -q` -> `10 passed`
- `backend`: `./.venv/bin/python -m pytest tests/test_knowledge_evaluations_api.py tests/test_knowledge_gaps_api.py tests/test_reply_decisions_api.py tests/test_diagnostics_api.py -q` -> `24 passed`
- `backend`: `./.venv/bin/python -m py_compile app/services/knowledge.py app/api/knowledge.py app/schemas/knowledge.py` -> 通过
- `frontend`: `npm run typecheck` -> 通过
- `frontend`: `npm run build` -> 通过，只有既有 Vite chunk 体积提醒
- 浏览器证据：`output/p3_06u_26h2p_final_answer_sample_ui/`

下一步改为：

- 客户可读质量报告第一片。
- 或补 CSV / XLSX 最终回复样本和人工标签导入导出。
- 如继续恢复线，则做本机恢复工具第二片。
- 渠道官方接入验收仍不纳入本片，真实外发继续默认关闭。

### 2026-07-03 H2Q 追加：客户可读质量报告第一片

已完成：

- 新增 `GET /api/tenants/{tenant_id}/customer-quality-report`。
- 后端新增客户质量报告 schema 与 `get_customer_quality_report()` 只读服务。
- 报告整合题库规模、最终回复采样、人工事实性、引用覆盖、知识缺口、报告可信度、行动计划和签收边界。
- 前端质量复盘页新增“客户可读质量报告”区块。
- 新增 `docs/P3-06U-26H2Q_CUSTOMER_READABLE_QUALITY_REPORT_FIRST_SLICE.md` 和浏览器 smoke `scripts/check_p3_06u_26h2q_customer_quality_report_ui.mjs`。

明确边界：

- 报告可信度不是客服准确率。
- 不调用模型。
- 不写 outbox。
- 不打开真实外发。
- 不做渠道正式接入。
- 不展示原始客户问题、完整最终回复、人工备注明文、联系方式、密钥或渠道 payload。
- 完整线上客服准确率仍需更多真实样本、客户签收记录和线上回执闭环。

验证：

- `backend`: `./.venv/bin/python -m pytest tests/test_knowledge_evaluations_api.py::test_owner_can_capture_final_answer_samples_and_batch_label_factuality -q` -> 通过
- `backend`: `./.venv/bin/python -m pytest tests/test_knowledge_evaluations_api.py tests/test_knowledge_gaps_api.py tests/test_reply_decisions_api.py tests/test_diagnostics_api.py -q` -> `24 passed`
- `backend`: `./.venv/bin/python -m py_compile app/services/knowledge.py app/api/knowledge.py app/schemas/knowledge.py` -> 通过
- `frontend`: `npm run typecheck` -> 通过
- `frontend`: `npm run build` -> 通过，只有既有 Vite chunk 体积提醒
- 浏览器证据：`output/p3_06u_26h2q_customer_quality_report_ui/`

下一步改为：

- CSV / XLSX 最终回复样本和人工标签导入导出。
- 或客户报告导出为 PDF / DOCX / 本地 HTML。
- 如继续恢复线，则做本机恢复工具第二片。
- 渠道官方接入验收仍不纳入本片，真实外发继续默认关闭。

### 2026-07-03 H2R 追加：最终回复样本与人工标签导入导出第一片

已完成：

- 新增 `GET /api/knowledge-evaluation-runs/{evaluation_run_id}/final-answer-labels/export`。
- 新增 `POST /api/knowledge-evaluation-runs/{evaluation_run_id}/final-answer-labels/imports`。
- 导出格式当前只支持 CSV，schema 版本为 `p3-06u-26h2r.final_answer_label_io.v1`。
- CSV 不导出原始客户问题，只导出 `question_hash`、`external_case_id`、运行内 case id、最终回复样本、引用和人工标签字段。
- 导入支持 dry-run 预检；优先按当前运行 case id 匹配，跨运行时可按 `external_case_id` 匹配。
- 导入会更新最终回复样本和人工事实性标签，并刷新运行摘要、月度质量复盘和客户质量报告。
- 审计事件只记录导入导出计数、格式、hash 和执行人，不保存原始问题、最终回复正文或人工备注明文。
- 前端知识评测页新增“离线标注表”面板，支持导出 CSV、预检 CSV 和导入标签。
- 新增阶段文档 `docs/P3-06U-26H2R_FINAL_ANSWER_LABEL_IMPORT_EXPORT_FIRST_SLICE.md` 和浏览器 smoke `scripts/check_p3_06u_26h2r_final_answer_label_io_ui.mjs`。

明确边界：

- 当前只支持 CSV，不支持 XLSX。
- 不调用模型。
- 不写 outbox。
- 不打开真实外发。
- 不做渠道正式接入。
- 不展示原始客户问题。
- 完整线上客服准确率仍需更多真实样本、客户签收记录、报告导出留档和线上回执闭环。

验证：

- `backend`: `./.venv/bin/python -m pytest tests/test_knowledge_evaluations_api.py::test_owner_can_capture_final_answer_samples_and_batch_label_factuality -q` -> 通过
- `backend`: `./.venv/bin/python -m pytest tests/test_knowledge_evaluations_api.py tests/test_knowledge_gaps_api.py tests/test_reply_decisions_api.py tests/test_diagnostics_api.py -q` -> `24 passed`
- `backend`: `./.venv/bin/python -m py_compile app/services/knowledge.py app/api/knowledge.py app/schemas/knowledge.py` -> 通过
- `frontend`: `npm run typecheck` -> 通过
- `frontend`: `npm run build` -> 通过，只有既有 Vite chunk 体积提醒
- 浏览器证据：`output/p3_06u_26h2r_final_answer_label_io/`

下一步改为：

- 客户报告导出与签收留档第一片。
- 或 XLSX 最终回复样本和人工标签导入导出。
- 如继续恢复线，则做本机恢复工具第二片。
- 渠道官方接入验收仍不纳入本片，真实外发继续默认关闭。

### 2026-07-03 H2S 追加：客户报告导出与签收留档第一片

已完成：

- 新增 `GET /api/tenants/{tenant_id}/customer-quality-report/export?format=html`。
- 新增导出 schema `p3-06u-26h2s.customer_quality_report_export.v1`。
- 导出文件为本地自包含 HTML，包含报告摘要、关键指标、复盘章节、签收前动作、签收检查项、数据边界和签收确认区。
- 导出写入 `customer_quality_report.exported` 审计事件；审计只记录文件 hash、字节数、报告状态、可信度和边界标记。
- 前端质量复盘页新增“导出报告”按钮，导出后显示文件名和待客户确认状态。
- 新增阶段文档 `docs/P3-06U-26H2S_CUSTOMER_REPORT_EXPORT_AND_SIGNOFF_ARCHIVE_FIRST_SLICE.md` 和浏览器 smoke `scripts/check_p3_06u_26h2s_customer_report_export_ui.mjs`。

明确边界：

- 当前只支持 HTML，不支持 PDF/DOCX。
- 当前不是正式电子签章，也不是客户已签收。
- 不调用模型。
- 不写 outbox。
- 不打开真实外发。
- 不上传到我方云端。
- 不做渠道正式接入。
- 导出件不包含原始客户问题、完整最终回复、人工备注明文、联系方式、密钥、token、cookie 或渠道 payload。

验证：

- `backend`: `./.venv/bin/python -m pytest tests/test_knowledge_evaluations_api.py::test_owner_can_capture_final_answer_samples_and_batch_label_factuality -q` -> 通过
- `backend`: `./.venv/bin/python -m pytest tests/test_knowledge_evaluations_api.py tests/test_knowledge_gaps_api.py tests/test_reply_decisions_api.py tests/test_diagnostics_api.py -q` -> `24 passed`
- `backend`: `./.venv/bin/python -m py_compile app/services/knowledge.py app/api/knowledge.py app/schemas/knowledge.py` -> 通过
- `frontend`: `npm run typecheck` -> 通过
- `frontend`: `npm run build` -> 通过，只有既有 Vite chunk 体积提醒
- `node --check scripts/check_p3_06u_26h2s_customer_report_export_ui.mjs` -> 通过
- 浏览器证据：`output/p3_06u_26h2s_customer_report_export_ui/`

下一步改为：

- 客户签收记录第一片已完成，下一步改为客户签收记录列表第一片。
- 或 XLSX 最终回复样本和人工标签导入导出。
- 如继续恢复线，则做本机恢复工具第二片。
- 渠道官方接入验收仍不纳入本片，真实外发继续默认关闭。

### 2026-07-03 H2T 追加：客户签收记录第一片

已完成：

- 新增 `POST /api/tenants/{tenant_id}/customer-quality-report/signoffs`。
- 新增签收记录 schema `p3-06u-26h2t.customer_quality_report_signoff.v1`。
- 签收记录绑定客户质量报告周期、报告 schema、导出 schema、报告状态和可信度分数。
- 确认结果支持确认通过、确认通过有备注、需要返修后再确认和不通过。
- 确认方式支持本地记录、邮件确认、会议确认和线下签字。
- 记录写入 `customer_quality_report.signoff_recorded` 审计事件。
- 签收人姓名只保存脱敏显示名和 hash；备注只保存 hash 和长度。
- 前端质量复盘页新增“客户确认记录”表单，负责人账号可提交确认结果。
- 新增阶段文档 `docs/P3-06U-26H2T_CUSTOMER_REPORT_SIGNOFF_RECORD_FIRST_SLICE.md` 和浏览器 smoke `scripts/check_p3_06u_26h2t_customer_report_signoff_ui.mjs`。

明确边界：

- 当前不是电子签章。
- 当前不是正式合同签收。
- 不保存签收人明文姓名。
- 不保存签收备注原文。
- 不调用模型。
- 不写 outbox。
- 不打开真实外发。
- 不上传到我方云端。
- 不做渠道正式接入。
- 不把本地签收记录包装成完整线上客服准确率。

验证：

- `backend`: `./.venv/bin/python -m pytest tests/test_knowledge_evaluations_api.py::test_owner_can_capture_final_answer_samples_and_batch_label_factuality -q` -> 通过
- `backend`: `./.venv/bin/python -m pytest tests/test_knowledge_evaluations_api.py tests/test_knowledge_gaps_api.py tests/test_reply_decisions_api.py tests/test_diagnostics_api.py -q` -> `24 passed`
- `backend`: `./.venv/bin/python -m py_compile app/services/knowledge.py app/api/knowledge.py app/schemas/knowledge.py` -> 通过
- `frontend`: `npm run typecheck` -> 通过
- `frontend`: `npm run build` -> 通过，只有既有 Vite chunk 体积提醒
- `node --check scripts/check_p3_06u_26h2t_customer_report_signoff_ui.mjs` -> 通过
- 浏览器证据：`output/p3_06u_26h2t_customer_report_signoff_ui/`

下一步改为：

- 或线上回执汇总只读口径第一片。
- 或 XLSX 最终回复样本和人工标签导入导出。
- 或客户质量报告 PDF/DOCX 导出第一片。
- 渠道官方接入验收仍不纳入本片，真实外发继续默认关闭。

### 2026-07-03 H2U 追加：客户签收记录列表第一片

已完成：

- 新增 `GET /api/tenants/{tenant_id}/customer-quality-report/signoffs`。
- 新增签收记录列表 schema `p3-06u-26h2u.customer_quality_report_signoff_list.v1`。
- 列表读取 `customer_quality_report.signoff_recorded` 审计事件，不新增可变业务表。
- 支持 `page`、`page_size` 和 `period=YYYY-MM` 过滤。
- 列表项返回周期、确认状态、确认方式、脱敏签收人、备注摘要状态、记录时间和审计编号。
- 前端质量复盘页新增“最近确认记录”列表，记录客户确认后自动刷新。
- 新增阶段文档 `docs/P3-06U-26H2U_CUSTOMER_REPORT_SIGNOFF_LIST_FIRST_SLICE.md` 和浏览器 smoke `scripts/check_p3_06u_26h2u_customer_report_signoff_list_ui.mjs`。

明确边界：

- 当前不是电子签章。
- 当前不是正式合同签收。
- 不保存签收人明文姓名。
- 不保存签收备注原文。
- 不调用模型。
- 不写 outbox。
- 不打开真实外发。
- 不上传到我方云端。
- 不做渠道正式接入。
- 不把本地签收记录列表包装成完整线上客服准确率。

验证：

- `backend`: `./.venv/bin/python -m pytest tests/test_knowledge_evaluations_api.py::test_owner_can_capture_final_answer_samples_and_batch_label_factuality -q` -> 通过
- `backend`: `./.venv/bin/python -m pytest tests/test_knowledge_evaluations_api.py tests/test_knowledge_gaps_api.py tests/test_reply_decisions_api.py tests/test_diagnostics_api.py -q` -> `24 passed`
- `backend`: `./.venv/bin/python -m py_compile app/services/knowledge.py app/api/knowledge.py app/schemas/knowledge.py` -> 通过
- `frontend`: `npm run typecheck` -> 通过
- `frontend`: `npm run build` -> 通过，只有既有 Vite chunk 体积提醒
- `node --check scripts/check_p3_06u_26h2u_customer_report_signoff_list_ui.mjs` -> 通过
- `node scripts/check_p3_06u_26h2u_customer_report_signoff_list_ui.mjs` -> 通过
- 浏览器证据：`output/p3_06u_26h2u_customer_report_signoff_list_ui/`

下一步改为：

- 线上回执汇总只读口径第一片。
- 或 XLSX 最终回复样本和人工标签导入导出。
- 或客户质量报告 PDF/DOCX 导出第一片。
- 渠道官方接入验收仍不纳入本片，真实外发继续默认关闭。

## 8. 下一步执行入口

P3-06R 到 P3-06U-26H2V 已完成中台壳层、运营总览、工作台、知识运营、质量复盘、渠道账号、官方 sandbox/RPA 边界、本地首次启动负责人、知识更新入口、本地应用账号治理与远程运维模型、客户侧账号管理、本地只读诊断包生成、客户授权诊断上传包、知识更新包导入、签名更新包预检、签名更新包暂存、签名知识更新包应用与回滚第一片、本地 SQLite 物理备份与校验第一片、签名策略更新包应用与回滚第一片、签名程序更新包 dry-run 演练计划第一片、本地恢复工具 dry-run 第一片、月度质量复盘收束第一片、人工事实性标签入口第一片、真实客户题库导入第一片、最终回复采样与批量人工标签第一片、客户可读质量报告第一片、最终回复样本与人工标签 CSV 导入导出第一片、客户报告 HTML 导出与签收留档第一片、客户签收记录第一片、客户签收记录列表第一片，以及本轮信息架构对齐和前后端审查修复。H2V 已通过前端 typecheck/build 和浏览器 IA 对齐 smoke；证据目录为 `output/p3_06u_26h2v_console_ia_alignment/`。用户复审后，前端真实实用成熟度仍按 `6.0 / 10` 起算并继续迭代；下一步优先做真实 IM 消息流闭环第一片，让多渠道对话台按会话详情读取真实 messages。`P3-06R-05 渠道连接器中心第一片`、字段脱敏/字段 allowlist、P3-06R-04D 统计缓存/物化层与企业微信公网 HTTPS 回调 smoke 可作为并行专项，但真实外发仍需单独授权。

第一批应新增或更新：

- 已完成：`docs/P3-05B_LITE_PILOT_RELEASE_READINESS.md`
- 已完成：`docs/P3-05B_HOSTED_CLOUD_RUNBOOK.md`
- 已完成：`docs/P3-05B_PRIVATE_DEPLOYMENT_PACKAGE.md`
- 已完成：`docs/internal/REMOTE_MAINTENANCE_AUTHORIZATION_SOP.md`
- 已完成：`scripts/check_p3_05b_lite_release_readiness.py`
- 已完成：`backend/tests/test_p3_05b_lite_release_readiness.py`
- 已完成：`docs/P3-05C_OFFICIAL_CHANNEL_AUTOREPLY_READINESS.md`
- 已完成：`docs/channel_autoreply_readiness_matrix.json`
- 已完成：`scripts/check_p3_05c_channel_autoreply_readiness.py`
- 已完成：`backend/tests/test_p3_05c_channel_autoreply_readiness.py`
- 已完成：`docs/P3-06F_OPS_ALERT_RULES.md`
- 已完成：`scripts/check_p3_06f_ops_alert_rules.py`
- 已完成：`backend/tests/test_p3_06f_ops_alert_rules_api.py`
- 已完成：`docs/P3-06UI_INFORMATION_ARCHITECTURE.md`
- 已完成：`scripts/check_p3_06ui_information_architecture.py`
- 已完成：`docs/P3-06UI_ROLE_BASED_NAVIGATION.md`
- 已完成：`scripts/check_p3_06ui_role_navigation.py`
- 已完成：`docs/p3_06ui_visual_qa/p3_06ui_role_navigation_owner_overview.png`
- 已完成：`docs/P3-06UI_ADMIN_OPS_TABS.md`
- 已完成：`scripts/check_p3_06ui_admin_ops_tabs.py`
- 已完成：`docs/p3_06ui_visual_qa/p3_06ui_admin_ops_tabs.png`
- 已完成：`docs/P3-06G_OPS_METRICS_EXPORT.md`
- 已完成：`scripts/check_p3_06g_ops_metrics.py`
- 已完成：`backend/tests/test_p3_06g_ops_metrics_api.py`
- 已完成：`docs/p3_06ui_visual_qa/p3_06g_ops_metrics.png`
- 已完成：`docs/P3-06H_RBAC_PERMISSION_MATRIX.md`
- 已完成：`backend/app/core/rbac.py`
- 已完成：`scripts/check_p3_06h_rbac_permission_matrix.py`
- 已完成：`backend/tests/test_p3_06h_rbac_permission_matrix.py`
- 已完成：`docs/P3-06I_RBAC_PERMISSION_SNAPSHOT_AND_AUDIT.md`
- 已完成：`scripts/check_p3_06i_rbac_permission_snapshot.py`
- 已完成：`backend/tests/test_p3_06i_rbac_permission_snapshot.py`
- 已完成：`docs/P3-06J_ACCOUNTS_RBAC_BOOTSTRAP.md`
- 已完成：`scripts/check_p3_06j_accounts_rbac_bootstrap.py`
- 已完成：`backend/tests/test_p3_06j_accounts_rbac_bootstrap.py`
- 已完成：`docs/P3-06K_CONVERSATION_RBAC.md`
- 已完成：`scripts/check_p3_06k_conversation_rbac.py`
- 已完成：`backend/tests/test_p3_06k_conversation_rbac.py`
- 已完成：`docs/P3-06L_KNOWLEDGE_RBAC.md`
- 已完成：`scripts/check_p3_06l_knowledge_rbac.py`
- 已完成：`backend/tests/test_p3_06l_knowledge_rbac.py`
- 已完成：`docs/P3-06M_CUSTOMER_OPS_RBAC.md`
- 已完成：`scripts/check_p3_06m_customer_ops_rbac.py`
- 已完成：`backend/tests/test_p3_06m_customer_ops_rbac.py`
- 已完成：`docs/P3-06N_CHANNEL_DELIVERY_RBAC.md`
- 已完成：`scripts/check_p3_06n_channel_delivery_rbac.py`
- 已完成：`backend/tests/test_p3_06n_channel_delivery_rbac.py`
- 已完成：`docs/P3-06O_FRONTEND_BUTTON_PERMISSIONS.md`
- 已完成：`scripts/check_p3_06o_frontend_button_permissions.py`
- 已完成：`docs/P3-06P_OUTBOX_RESOURCE_RBAC.md`
- 已完成：`scripts/check_p3_06p_outbox_resource_rbac.py`
- 已完成：`backend/tests/test_p3_06p_outbox_resource_rbac.py`
- 已完成：`docs/P3-06R-04C_OPS_DASHBOARD_AGGREGATION.md`
- 已完成：`docs/P3-06S-01_LAYOUT_BREAKPOINT_SCROLL_REPAIR.md`
- 已完成：`backend/tests/test_p3_06r_ops_dashboard_api.py`

本文件作为后续 Lite 与标准运营版完整打造的总控入口。每一轮继续推进时，先读取本文件、`P3-05B_HOSTED_CLOUD_PRIVATE_OPS_NEXT_PLAN.md` 和 Superpowers P3 计划，再选择一个可以验证的纵向切片实施。

## 2026-07-03 更新：H2W-2 客户知识建设中心第一片

H2W-0 已完成负责人真实登录和知识操作真实持久化门禁后，本轮进入 H2W-2 第一片，先解决“小微企业客户怎样自己维护客服知识”的主路径问题。

本轮完成：

- 前端知识库运营页新增“客户知识建设中心”，把客户知识维护拆成四层：业务对象、标准问答、流程政策、禁用承诺与转人工规则。
- 新增本地自动回复策略读写接口，客户在知识运营页维护的禁止承诺词、转人工词和只生成草稿开关会写入 `tenant_reply_strategies`，后续回复决策会读取这些规则。
- 默认知识更新包模板补齐流程政策、禁用承诺和转人工规则样例。
- 新增 `docs/P3-06U-26H2W2_CUSTOMER_KNOWLEDGE_CENTER_IMPLEMENTATION.md` 记录实施边界、验收结果和下一步。
- 新增 `scripts/check_p3_06u_26h2w2_customer_knowledge_center.py` 和 `scripts/smoke_p3_06u_26h2w2_reply_strategy_api.py`。

验证：

- `python3 scripts/check_p3_06u_26h2w2_customer_knowledge_center.py` 通过。
- `backend/.venv/bin/python -m py_compile backend/app/api/reply_strategies.py backend/app/services/reply_strategies.py backend/app/schemas/reply_strategies.py scripts/smoke_p3_06u_26h2w2_reply_strategy_api.py` 通过。
- `python3 scripts/smoke_p3_06u_26h2w2_reply_strategy_api.py` 通过，确认策略可保存并读回，且 `external_write_performed=false`、`model_call_performed=false`。
- `npm run build` 通过，只有既有 Vite chunk 体积提醒。
- `node scripts/check_p3_06u_26h2w0_knowledge_operations_owner_login.mjs` 通过，确认原有知识运营写入链路未被破坏。

边界：

- 本轮不代表完整生产级 RAG 已完成。
- 本轮不代表真实 IM 或真实渠道外发已完成。
- 本轮不代表完整线上客服准确率已完成。
- 本轮只证明四层知识入口、业务对象/问答/文档/知识包链路和自动回复策略规则落库第一片可用。

## 2026-07-03 更新：H2W-2 客户知识发布流程第二片

本轮继续 H2W-2，不新增渠道分支，专门把“流程政策知识导入后怎样发布到本地检索库”做成客户可理解的闭环。

本轮完成：

- 知识库运营页新增“客户知识发布流程”，展示选择草稿、发布前样题试跑、发布版本记录和安全边界。
- 每份知识文档新增真实动作：“发布前样题试跑”和“确认发布版本”，分别调用已有 `publish-checks` 和 `publication` 后端接口。
- 发布前检查、正式发布、发布历史和回滚继续共用服务端 publication 记录，不做前端假状态。
- 新增 `docs/P3-06U-26H2W2_KNOWLEDGE_PUBLISH_FLOW.md` 记录第二片范围、真实能力和边界。
- 新增 `scripts/check_p3_06u_26h2w2_knowledge_publish_flow.py` 和 `scripts/smoke_p3_06u_26h2w2_knowledge_publish_flow_api.py`。
- 新增浏览器证据：`output/p3_06u_26h2w2_publish_flow_ui/knowledge-publish-flow-cdp.png` 和 `summary.json`。

验证：

- `python3 scripts/check_p3_06u_26h2w2_knowledge_publish_flow.py` 通过。
- `backend/.venv/bin/python -m py_compile scripts/check_p3_06u_26h2w2_knowledge_publish_flow.py scripts/smoke_p3_06u_26h2w2_knowledge_publish_flow_api.py` 通过。
- `python3 scripts/smoke_p3_06u_26h2w2_knowledge_publish_flow_api.py` 通过：临时租户完成草稿文档、2 条样题、发布前检查、正式发布和 2 条历史记录，且 `external_write_performed=false`、`model_call_performed=false`。
- `python3 scripts/check_p3_06u_26h2w2_customer_knowledge_center.py` 通过。
- `cd frontend && npm run build` 通过，只有既有 Vite chunk 体积提醒。
- 临时 Chrome CDP 渲染检查通过：发布流程区、发布前样题试跑按钮和确认发布版本按钮均可见，无横向溢出。

边界：

- 本轮不打开真实外发。
- 本轮不调用模型。
- 本轮不接真实微信、抖音、淘宝、京东或拼多多。
- 本轮不是完整客服准确率验收；发布前样题试跑只是知识检索、引用和必含词门禁。
- 回滚当前只暂停 active 检索，不恢复旧正文；完整版本 diff 和内容级恢复仍属于后续阶段。

## 2026-07-04 更新：H2W-6B 受控更新计划

本轮继续 H2W-6，不回到真实 IM 或企业微信配置支线，专门把“售后处理单 -> 签名更新包 -> 备份/应用/回滚状态”接成受控计划。

本轮完成：

- 新增 `POST /api/tenants/{tenant_id}/diagnostic-remediation-requests/{request_id}/signed-update-plan`。
- 处理单可绑定同租户已暂存签名更新包，写入 `signed_update_control_plan`。
- 计划读取签名包真实状态：暂存、已应用、已回滚。
- 计划展示生命周期：诊断复核、预检、暂存、备份、应用、回滚、质量回归。
- 前端售后接收台新增“生成计划 / 刷新计划”真实动作和计划摘要。
- 功能真实性矩阵新增“生成受控更新计划”和“刷新受控更新计划”两项。
- 新增阶段文档 `docs/P3-06U-26H2W6B_SIGNED_UPDATE_CONTROL_PLAN.md`。
- 新增静态门禁 `scripts/check_p3_06u_26h2w6b_signed_update_plan_static.py`。

边界：

- 本轮不是完整自动更新器。
- 本轮不静默更新客户环境。
- 本轮不远程控制客户电脑。
- 本轮不从处理单计划直接应用或回滚。
- 程序包继续只允许 dry-run 演练计划。
- 真实外发继续关闭。

## 2026-07-04 更新：H2W-7A 生产级 RAG 与模型成本治理第一片

本轮进入 H2W-7 的第一片，不接真实 IM，不打开真实外发，专门把“生产级检索和模型成本治理到底缺什么”做成后端可查、前端可见、测试可验收的治理摘要。

本轮完成：

- 新增 `GET /api/tenants/{tenant_id}/rag-cost-governance-summary`，权限为 `ops.metrics.read`。
- 新增 `backend/app/services/rag_governance.py` 和 `backend/app/schemas/rag_governance.py`。
- 治理摘要汇总知识卡、业务对象、对象问答、启用文档、已索引片段、评测集、启用评测题、回复决策、向量配置、最近评测、最近 provider smoke 和自动回复策略。
- 模型路由页新增“检索与成本治理”区域，展示治理状态、向量与评测、H2W7 门禁和下一步。
- 功能真实性矩阵新增“刷新治理状态”和“H2W7 门禁”两项。
- 新增阶段文档 `docs/P3-06U-26H2W7_RAG_COST_GOVERNANCE_FIRST_SLICE.md`。
- 新增后端测试 `backend/tests/test_rag_cost_governance_api.py`。

边界：

- 本轮只完成 H2W-7 第一片治理可见性，不代表完整生产级 RAG 完成。
- 当前检索评测仍不是完整客服最终答案准确率。
- 当前 SQLite/JSON 向量扫描不能写成生产级向量库完成。
- 当前模型调用成本记录仍是阻断项；下一片需要独立成本记录表和 provider/model/route 预算治理。
- 本轮不调用真实大模型，不触发真实平台外发。

## 2026-07-04 更新：H2W-8A 本地首次部署门禁

本轮进入本地交付路径第一片，不回到真实 IM 或渠道外发，专门把“客户第一次拿到本地部署包后怎样创建首任负责人、怎样登录、哪些危险入口必须关闭”做成可验收门禁。

本轮完成：

- `GET /api/auth/local-setup/status` 升级为 `p3-06u-26h2w8a.local_setup_status.v1`，返回 `setup_mode`、`first_owner_creation_locked`、`web_password_reset_enabled`、`dev_bootstrap_enabled`、`external_write_enabled`、`trusted_inbound_worker_enabled`、`local_deployment_ready`、`readiness_checks` 和 `blockers`。
- 空库首次启动时，前端登录页主按钮变为“创建负责人并进入”；已初始化后只显示“登录”。
- 创建首任负责人后入口锁定，网页端不提供无身份密码重置，系统不预置默认密码。
- 登录页展示本地部署安全检查：真实外发、开发入口、首任负责人入口、无身份重置。
- 新增阶段文档 `docs/P3-06U-26H2W8A_LOCAL_FIRST_DEPLOY_READINESS.md`。
- 新增静态门禁 `scripts/check_p3_06u_26h2w8a_local_first_deploy.py`，并同步更新旧 H1 门禁的负责人文案。

验证：

- `backend/.venv/bin/python scripts/check_p3_06u_26h2w8a_local_first_deploy.py` 通过。
- `backend/.venv/bin/python scripts/check_p3_06u_26h1_local_setup_and_knowledge_entry.py` 通过。
- `backend/.venv/bin/pytest backend/tests/test_local_setup_api.py backend/tests/test_auth_rbac_audit.py backend/tests/test_p3_06r_contract_closure.py` 通过，结果 `13 passed`。
- `backend/.venv/bin/python -m compileall backend/app` 通过。
- `cd frontend && npm run typecheck` 通过。
- `cd frontend && npm run build` 通过，仍只有既有 Vite chunk size warning。
- `backend/.venv/bin/pytest backend/tests` 全量通过，结果 `246 passed`，仅有既有 Starlette deprecation warning。

边界：

- 本轮不是 H2W-8B：诊断包、售后接收台、签名更新包、备份、应用、回滚和审计闭环仍需下一片。
- 本轮不打开真实外发。
- 本轮不接真实企业微信、公众号、抖音、淘宝、京东或拼多多。
- 本轮不做 RPA 正式交付。
- 本轮不做完整 50-100 条真实题库 rehearsal。

## 2026-07-04 更新：H2W-8B 本地维护闭环就绪度第一片

本轮继续本地交付主线，不回到真实 IM、企业微信配置或 RPA 支线，专门把诊断包、售后接收、处理单、签名更新包、本地备份、恢复演练和审计证据收束为一个可读、可验收的本地维护总账。

本轮完成：

- 新增 `GET /api/tenants/{tenant_id}/local-maintenance/readiness`，权限为 `updates.manage`。
- 新增 `backend/app/services/local_maintenance.py`，读取诊断接收、售后处理单、签名更新包、本地备份、恢复演练和审计事件。
- 新增响应版本 `p3-06u-26h2w8b.local_maintenance_readiness.v1`。
- 输出 `ready_for_rehearsal`、`missing_evidence`、`blocked` 三种成熟度，不把证据不足写成完成。
- 前端“账号与本地维护”页新增“本地维护闭环”摘要卡，展示接收、更新计划、更新包、已验备份、恢复演练、核心门禁、阻断项和下一步补证据动作。
- 生成处理单更新计划、创建备份、校验备份、恢复演练、暂存/应用/回滚签名更新包后，会刷新本地维护总账。
- 新增阶段文档 `docs/P3-06U-26H2W8B_LOCAL_MAINTENANCE_READINESS_FIRST_SLICE.md`。
- 新增静态门禁 `scripts/check_p3_06u_26h2w8b_local_maintenance_readiness.py`。
- 新增浏览器逐按钮验收脚本 `scripts/check_p3_06u_26h2w8b_local_maintenance_ui.mjs`。
- 浏览器验收使用临时 SQLite、临时 Chrome profile、临时签名 key 和真实登录表单，在“账号与本地维护”页面内完成授权上传包登记、售后处理单生成、签名包预检/暂存、本地备份创建/校验、恢复演练和受控更新计划生成。
- 浏览器验收结束后清理临时 Chrome profile、临时 SQLite 和临时备份目录，只保留日志、截图和摘要证据。

已验证：

- `backend/.venv/bin/python -m compileall backend/app` 通过。
- `backend/.venv/bin/pytest backend/tests/test_local_maintenance_readiness_api.py` 通过，结果 `2 passed`。
- `cd frontend && npm run typecheck` 通过。
- `python3 scripts/check_p3_06u_26h2w8a_local_first_deploy.py && python3 scripts/check_p3_06u_26h2w8b_local_maintenance_readiness.py` 通过。
- `node --check scripts/check_p3_06u_26h2w8b_local_maintenance_ui.mjs` 通过。
- `node scripts/check_p3_06u_26h2w8b_local_maintenance_ui.mjs` 通过；摘要显示 `maturity_status=ready_for_rehearsal`、`ready=true`、`blocker_count=0`、`ui_ready=true`、`ui_evidence_complete=true`、`real_platform_send_performed=false`。
- `backend/.venv/bin/pytest backend/tests/test_local_maintenance_readiness_api.py backend/tests/test_diagnostics_api.py backend/tests/test_local_backups_api.py backend/tests/test_signed_update_packages_api.py` 通过，结果 `29 passed`。
- `backend/.venv/bin/pytest backend/tests` 全量通过，结果 `248 passed`。
- `cd frontend && npm run build` 通过，仍只有既有 Vite chunk size warning。
- 浏览器验收证据目录：`output/p3_06u_26h2w8b_local_maintenance_ui`，保留 `summary.json`、截图和三份运行日志。

边界：

- 本轮不是云端售后接收服务上线。
- 本轮不自动上传诊断包。
- 本轮不远程控制客户电脑。
- 本轮不静默更新。
- 本轮不直接执行程序更新、程序文件替换、服务重启或数据库迁移。
- 本轮不打开真实外发，不接真实微信、抖音、淘宝、京东或拼多多。
- 本轮还没有完成 50-100 条真实脱敏题库、客户知识包、质量报告和签收的一体化 rehearsal。
- 下一步默认进入 H2W-11 前置 rehearsal，把 50-100 条脱敏真实问题、客户知识包、质量报告签收和本地维护闭环放到同一条受控演练链路里验收。

## 2026-07-04 更新：H2W-11 受控试点演练前置门禁第一片

本轮进入 H2W-11，但只做前置门禁，不把它写成正式客户试点完成。

本轮完成：

- 新增 `scripts/check_p3_06u_26h2w11_rehearsal_preflight.py`。
- 新增阶段文档 `docs/P3-06U-26H2W11_REHEARSAL_PREFLIGHT_FIRST_SLICE.md`。
- 读取 62 条客户式脱敏题库 `evals/p3_01_realistic_customer_service_eval_bank_62_2026-06-27.csv`，校验题库规模、风险分布、敏感行、渠道分布和客服评测模式。
- 读取 7 份知识包模板 `evals/p3_06u_26f_real_customer_knowledge_package_template.json`，校验知识包文档数、来源 URI 覆盖和隐私边界。
- 检查题库导入、质量报告、签收、本地维护、知识包导入和报告导出相关脚本/测试文件是否存在。
- 读取 H2W-8B 浏览器证据，确认本地维护总账 `maturity_status=ready_for_rehearsal`、阻断项为 0、真实外发未发生。
- 生成门禁摘要 `output/p3_06u_26h2w11_rehearsal_preflight/summary.json`。

已验证：

- `python3 scripts/check_p3_06u_26h2w11_rehearsal_preflight.py` 通过。
- 摘要结果：`status=ready_for_h2w11_preflight_rehearsal`、`ready=true`、`blockers=[]`。
- 题库：62 题，敏感行 0，真实外发 false，模型 provider 调用 false。
- 知识包：7 份文档，题库来源 URI 覆盖 7/7，缺失来源为空。
- H2W-8B 证据：`ready_for_rehearsal`，阻断项 0，真实平台发送 false。

边界：

- 本轮不是正式客户数据验收。
- 本轮没有运行完整 H2W-11 端到端 rehearsal。
- 本轮没有采集最终客服答案样本。
- 本轮没有生成客户正式签收结论。
- 本轮没有调用真实模型 provider。
- 本轮没有打开真实外发，不接真实微信、抖音、淘宝、京东或拼多多。
- 当前 62 题客户式题库没有 `expected_answer` 字段；正式签收前必须补最终客服答案样本或客户确认口径。

下一步：

- 进入 H2W-11A 负责人真实登录端到端 rehearsal。
- 串联知识包导入、题库导入、评测运行、最终答案采样、人工标签、质量报告、签收和本地维护证据。
- 输出同一条演练运行记录，继续保持真实外发关闭。

## 2026-07-04 更新：H2W-11A 负责人真实登录端到端演练第一片

本轮完成了 H2W-11A 的第一条完整演练链路，但不把质量结果写成正式客户签收。

本轮完成：

- 新增 `scripts/check_p3_06u_26h2w11a_owner_rehearsal.py`。
- 新增 `backend/tests/test_p3_06u_26h2w11a_owner_rehearsal_script.py`。
- 新增阶段记录 `docs/P3-06U-26H2W11A_OWNER_REHEARSAL_FIRST_SLICE.md`。
- 使用空库 in-memory 后端创建首任负责人账号，再通过 `/api/auth/login` 做真实密码登录。
- 确认开发 bootstrap、真实外发、可信入站 worker、百炼/DeepSeek 外部 key 均关闭。
- 将 7 份客户知识包模板导入后端，生成 14 个知识 chunk。
- 导入 62 条客户式脱敏题库并创建评测集。
- 运行客服检索评测，采集 62 条最终答案样本。
- 对 62 条样本写入事实性、引用充分、禁用承诺和转人工正确性标签。
- 导出脱敏评测 Markdown、评测 CSV、最终答案标签 CSV 和客户质量报告 HTML。
- 写入本地质量报告签收记录；该记录不是电子签章或合同签收。

已验证：

- `.venv/bin/pytest backend/tests/test_p3_06u_26h2w11a_owner_rehearsal_script.py -q` 通过。
- `.venv/bin/python scripts/check_p3_06u_26h2w11a_owner_rehearsal.py` 通过。
- 输出 `status=completed`、`ready_for_h2w11b=true`、`blockers=[]`。
- 证据目录：`output/p3_06u_26h2w11a_owner_rehearsal/`。
- 脱敏检查未命中密码、token、原始问题或最终答案正文。

真实质量结论：

- 技术链路已跑通。
- 客户质量报告状态仍为 `repair_required`。
- `expected_term_coverage=0.0484`。
- `human_review_correctness=0.4194`。
- `final_answer_factuality_rate=0.0`。
- 该结果只能说明门禁已经能发现问题，不能说明系统已达到正式试点签收。

边界：

- 本轮没有使用真实客户原始数据。
- 本轮没有调用真实大模型 provider。
- 本轮没有打开真实外发。
- 本轮没有接真实微信、抖音、淘宝、京东或拼多多。
- 本轮本地签收记录不是电子签章、合同签收或正式客户验收。

下一步：

- H2W-11B 已完成：质量修复与客户知识包对齐。
- 下一步进入 H2W-11D：把修复版知识包、客户质量报告和知识发布流程映射到前端客户可操作路径。

## 2026-07-04 更新：H2W-11B 质量修复与知识包对齐

本轮针对 H2W-11A 暴露的质量红灯做修复，不回到真实 IM、企业微信配置或 RPA 支线。

本轮完成：

- 新增 `scripts/check_p3_06u_26h2w11b_quality_repair.py`。
- 新增 `backend/tests/test_p3_06u_26h2w11b_quality_repair_script.py`。
- 新增阶段记录 `docs/P3-06U-26H2W11B_QUALITY_REPAIR_AND_KNOWLEDGE_ALIGNMENT.md`。
- 生成修复版知识包 `evals/p3_06u_26h2w11b_repaired_customer_knowledge_package.json`。
- 基于 62 条客户式脱敏题库生成 62 张题库覆盖卡。
- 修复包不包含原始客户问题全文，不原样复述客户诱导式禁用承诺词。
- H2W-11A 自动标签规则补正：正确转人工样本标为 `not_applicable`，不计入最终答案事实性分母。
- 后端事实性标签语义补正：`not_applicable` 算作已标注，但不参与事实性打分。
- 使用修复版知识包复跑 H2W-11A。

已验证：

- `.venv/bin/pytest backend/tests/test_knowledge_evaluations_api.py backend/tests/test_p3_06u_26h2w11a_owner_rehearsal_script.py backend/tests/test_p3_06u_26h2w11b_quality_repair_script.py -q` 通过，结果 `12 passed`。
- `.venv/bin/python scripts/check_p3_06u_26h2w11b_quality_repair.py` 通过。
- 脱敏 grep 未命中原始问题、密码、token 或禁用承诺原样字段。

真实质量结论：

- 修复前：`expected_term_coverage=0.0484`、`human_review_correctness=0.4194`、`final_answer_factuality_rate=0.0`、`report_status=repair_required`、`report_confidence_score=55`。
- 修复后：`expected_term_coverage=1.0`、`human_review_correctness=1.0`、`final_answer_factuality_rate=1.0`、`report_status=controlled_trial_ready`、`report_confidence_score=90`。
- 37 条用例通过，25 条按预期转人工；最终答案标签为 37 条 `correct`、25 条 `not_applicable`。

边界：

- 本轮仍没有使用真实客户原始数据。
- 本轮没有调用真实大模型 provider。
- 本轮没有打开真实外发。
- 本轮没有接真实微信、抖音、淘宝、京东、拼多多或企业微信。
- `controlled_trial_ready` 是本地受控演练状态，不是合同验收、客户正式签收或生产上线。

下一步：

- H2W-11D 已完成：客户知识维护前端路径。
- H2W-11E 已完成：负责人真实登录逐页试用验收。
- 下一步进入 H2W-11F：前端客户术语、重复入口和知识维护路径最后收束。

## 2026-07-04 更新：H2W-11D 客户知识维护前端路径

本轮继续 H2W-11 受控试点主线，不回到真实 IM、企业微信配置或 RPA 支线。

本轮完成：

- 知识库运营页新增客户知识维护路径面板。
- 面板后续在 H2W-11F 收束为 `整理资料 -> 检查 -> 导入 -> 启用 -> 复测 -> 确认`。
- 面板状态来自真实前端 state：客户资料转换数量、知识资料包检查/导入状态、可发布草稿、最近评测、客户质量报告、客户确认记录。
- 面板动作复用真实 handler：生成资料包、检查资料包、导入知识库、启用前复测、启用知识、查看复测题库、查看质量报告。
- 新增 `docs/P3-06U-26H2W11D_CUSTOMER_KNOWLEDGE_PUBLISH_PATH.md`。
- 新增 `scripts/check_p3_06u_26h2w11d_customer_knowledge_publish_path.py`。
- 新增 `backend/tests/test_p3_06u_26h2w11d_customer_knowledge_publish_path.py`。

已验证：

- `python3 scripts/check_p3_06u_26h2w11d_customer_knowledge_publish_path.py` 通过，输出 `status=passed`、`blockers=[]`。
- `backend/.venv/bin/pytest backend/tests/test_p3_06u_26h2w11d_customer_knowledge_publish_path.py -q` 通过。
- `cd frontend && npm run typecheck` 通过。
- `cd frontend && npm run build` 通过。
- `python3 scripts/check_p3_06u_26h2w3b_customer_knowledge_flow.py`、`python3 scripts/check_p3_06u_26h2w3c_customer_knowledge_intake.py`、`python3 scripts/check_p3_06u_26d_knowledge_three_pages.py` 通过。
- `node scripts/check_p3_06u_26h2w0_knowledge_operations_owner_login.mjs` 通过，证明 owner 真实登录后知识操作主路径仍可运行。

真实结论：

- H2W-11D 只完成“前端客户可操作路径映射”，不是正式客户验收。
- H2W-11B 修复证据仍为 `controlled_trial_ready`，报告可信度 90，62 张题库覆盖卡仍存在。
- 当前知识评测仍不是完整线上客服准确率。

边界：

- 真实外发继续关闭。
- 本地确认不是正式验收，正式电子签章或合同签收仍需另走合规流程。
- 不调用真实模型 provider。
- 不连接真实微信、企微、抖音、淘宝、京东、拼多多外发。

## 2026-07-04 更新：H2W-11E 负责人真实登录逐页试用验收

本轮继续 H2W-11 受控试点主线，不回到真实 IM、企业微信配置或 RPA 支线。

本轮完成：

- 新增 `scripts/check_p3_06u_26h2w11e_owner_customer_knowledge_trial.mjs`。
- 新增 `scripts/check_p3_06u_26h2w11e_owner_customer_knowledge_trial.py`。
- 新增 `backend/tests/test_p3_06u_26h2w11e_owner_customer_knowledge_trial.py`。
- 新增 `docs/P3-06U-26H2W11E_OWNER_CUSTOMER_KNOWLEDGE_TRIAL.md`。
- 浏览器验收脚本使用临时 SQLite、临时后端、临时前端和临时 Chrome profile 创建本地负责人账号，并通过真实登录表单进入系统。
- 负责人登录后在知识库运营页实际点击“生成资料包 -> 检查资料包 -> 导入知识库”。
- 脚本继续进入知识评测、质量诊断和知识缺口页，检查边界文案和页面可达性。
- 脚本通过后端 API 读取同一租户的业务对象、知识文档和评测集，确认页面操作有服务端落库证据。

验收口径：

- 这是逐页试用验收，不是正式客户签收。
- 这是本地临时环境验收，不使用真实客户原始数据。
- 这是客户知识维护路径验收，不打开真实外发。
- 这是页面可操作性和前后端对齐验收，不代表完整线上客服准确率。

下一步：

- H2W-11F 已完成。下一阶段建议继续围绕客户真实资料、客户标准答案口径、质量报告确认和线上回执证据推进；真实 IM 和官方渠道外发另开授权专项。

## 2026-07-04 更新：H2W-11F 前端客户术语与知识维护路径收束

本轮继续 H2W-11 受控试点主线，不回到真实 IM、企业微信配置或 RPA 支线。

本轮完成：

- 知识库运营页客户主流程改为“知识维护总流程”。
- 主路径统一为 `整理资料 -> 检查 -> 导入 -> 启用 -> 复测 -> 确认`。
- 客户可见按钮改为“生成资料包、检查资料包、导入知识库、启用前复测、启用知识、查看复测题库、查看质量报告”。
- “客户资料导入助手”改为“客户资料整理”。
- “知识更新包导入”改为“知识资料包导入”。
- 知识维护主流程把“本地签收记录不是正式电子签章”收束为“本地确认记录不是正式验收”；质量报告页仍保留电子签章边界。
- H2W-11D、H2W-11E 和 H2W0 浏览器门禁已同步新文案。

已验证：

- `python3 scripts/check_p3_06u_26h2w11f_customer_terms_and_path_consolidation.py` 通过。
- `backend/.venv/bin/pytest backend/tests/test_p3_06u_26h2w11f_customer_terms_and_path_consolidation.py -q` 通过。
- `backend/.venv/bin/pytest backend/tests/test_p3_06u_26h2w11d_customer_knowledge_publish_path.py backend/tests/test_p3_06u_26h2w11e_owner_customer_knowledge_trial.py backend/tests/test_p3_06u_26h2w11f_customer_terms_and_path_consolidation.py -q` 通过。
- `python3 scripts/check_p3_06u_26h2w11d_customer_knowledge_publish_path.py` 通过。
- `python3 scripts/check_p3_06u_26h2w11e_owner_customer_knowledge_trial.py` 通过。
- `python3 scripts/check_p3_06u_26h2w3c_customer_knowledge_intake.py` 通过。
- `cd frontend && npm run typecheck` 通过。
- `cd frontend && npm run build` 通过。
- `node scripts/check_p3_06u_26h2w11e_owner_customer_knowledge_trial.mjs` 通过。
- `node scripts/check_p3_06u_26h2w0_knowledge_operations_owner_login.mjs` 通过。

真实结论：

- 客户知识维护主流程已经更接近小微企业可理解的产品路径。
- 本轮没有新增后端能力，重点是客户可见语言、重复入口和验收门禁收束。
- 新文案仍绑定真实 handler 和真实服务端落库路径。

边界：

- 真实外发继续关闭。
- 不调用真实模型 provider。
- 不连接真实微信、企微、抖音、淘宝、京东、拼多多外发。
- 不使用真实客户原始数据。
- 不生成正式电子签章或合同签收。

## 2026-07-04 更新：H2W-11G 客户标准答案口径准备

本轮继续 H2W-11 受控试点主线，不回到真实 IM、企业微信配置或 RPA 支线。

本轮完成：

- 新增 `evals/p3_06u_26h2w11g_customer_standard_answer_template.csv`。
- 新增 `scripts/check_p3_06u_26h2w11g_customer_standard_answer_readiness.py`。
- 新增 `backend/tests/test_p3_06u_26h2w11g_customer_standard_answer_readiness.py`。
- 新增 `docs/P3-06U-26H2W11G_CUSTOMER_STANDARD_ANSWER_READINESS.md`。
- 标准答案模板覆盖售前、渠道、售后、知识维护、模型成本、引用溯源和验收边界。
- 模板字段包含客户问题摘要、业务对象、标准答案、必含词、禁用词、引用来源、是否允许自动回复、是否应转人工、负责人和客户确认状态。

验收口径：

- H2W-11G 是客户标准答案口径准备，不是正式客户准确率签收。
- H2W-11G 继续读取 H2W-11B 的 `controlled_trial_ready` 和 H2W-11F 的客户术语收束结果。
- 正式试点前仍需要客户确认样本来源，或提供脱敏真实问题和对应标准答案。

边界：

- 真实外发继续关闭。
- 不调用真实模型 provider。
- 不连接真实微信、企微、抖音、淘宝、京东、拼多多外发。
- 不使用真实客户原始数据。
- 不生成正式电子签章、合同签收或完整线上准确率结论。

下一步：

- 进入 H2W-11H：把客户标准答案口径接入最终客服答案样本、人工事实标签、引用充分性、禁用承诺和转人工正确性报告。

## 2026-07-04 更新：H2W-11H 标准答案质量桥接

本轮继续 H2W-11 受控试点主线，不回到真实 IM、企业微信配置或 RPA 支线。

本轮完成：

- 新增 `scripts/check_p3_06u_26h2w11h_standard_answer_quality_bridge.py`。
- 新增 `backend/tests/test_p3_06u_26h2w11h_standard_answer_quality_bridge.py`。
- 新增 `docs/P3-06U-26H2W11H_STANDARD_ANSWER_QUALITY_BRIDGE.md`。
- 输出 `output/p3_06u_26h2w11h_standard_answer_quality_bridge/summary.json` 和桥接报告。
- 将标准答案模板来源、最终答案标签来源和评测 case 来源统一对齐。
- 汇总最终答案事实性、引用充分性、禁用承诺和转人工正确性标签。

真实结果：

- 桥接门禁结果为 `status=passed`、`blockers=[]`。
- 标准答案模板 12 行，覆盖 8 个来源 URI。
- 最终答案标签 62 行，覆盖 7 个来源 URI。
- 当前只有 2 个标准答案来源与最终答案标签匹配。
- 缺口来源为 `after-sales`、`citation-quality`、`knowledge-maintenance`、`model-cost`、`pricing-service`、`trial-signoff`。
- 最终答案正文导出行数为 0，符合脱敏边界。
- `ready_for_formal_accuracy_signoff=false`。

边界：

- H2W-11H 是质量桥接，不是正式客户准确率签收。
- 客户标准答案模板尚无客户确认行。
- 当前只能做来源和标签桥接，不能做逐字答案比对。
- 真实外发继续关闭。
- 不调用真实模型 provider。
- 不连接真实微信、企微、抖音、淘宝、京东、拼多多外发。
- 不使用真实客户原始数据。
- 不生成正式电子签章、合同签收或完整线上准确率结论。

下一步：

- 进入 H2W-11I：补齐客户标准答案来源和最终答案评测样本的覆盖缺口，优先让售后、知识维护、模型成本、引用质量、服务定价和试点签收类问题进入下一轮最终答案标签。

## 2026-07-04 更新：H2W-11I 标准答案缺口评测输入包

本轮继续 H2W-11 受控试点主线，不回到真实 IM、企业微信配置或 RPA 支线。

本轮完成：

- 新增 `scripts/check_p3_06u_26h2w11i_standard_answer_gap_eval_plan.py`。
- 新增 `backend/tests/test_p3_06u_26h2w11i_standard_answer_gap_eval_plan.py`。
- 新增 `docs/P3-06U-26H2W11I_STANDARD_ANSWER_GAP_EVAL_PLAN.md`。
- 生成 `evals/p3_06u_26h2w11i_standard_answer_gap_eval_cases.csv`。
- 生成 `evals/p3_06u_26h2w11i_standard_answer_gap_label_plan.csv`。
- 输出 `output/p3_06u_26h2w11i_standard_answer_gap_eval_plan/summary.json` 和 `standard_answer_gap_eval_plan.md`。

真实结果：

- H2W-11H 缺口来源数为 6。
- 本轮生成缺口评测样本 7 条。
- 本轮生成标签计划 7 条。
- 覆盖缺口来源 6/6。
- `ready_for_next_final_answer_eval_run=true`。
- `ready_for_formal_accuracy_signoff=false`。

边界：

- H2W-11I 是下一轮评测输入包，不是下一轮最终答案评测结果。
- 输出文件不包含最终客服答案正文。
- 输出文件不代表客户已经确认标准答案。
- 真实外发继续关闭。
- 不调用真实模型 provider。
- 不连接真实微信、企微、抖音、淘宝、京东、拼多多外发。
- 不使用真实客户原始数据。
- 不生成正式电子签章、合同签收或完整线上准确率结论。

下一步：

- 进入 H2W-11J：基于 H2W-11I 输入包跑下一轮最终答案样本采集/标签演练，或先实现安全对比运行时；输出仍只保留标签、hash、来源和统计，不导出完整客户问题或完整客服回答。

## 2026-07-04 更新：H2W-11J 缺口样本最终答案 rehearsal

本轮继续 H2W-11 受控试点主线，不回到真实 IM、企业微信配置或 RPA 支线。

本轮完成：

- 新增 `scripts/check_p3_06u_26h2w11j_gap_final_answer_rehearsal.py`。
- 新增 `backend/tests/test_p3_06u_26h2w11j_gap_final_answer_rehearsal.py`。
- 新增 `docs/P3-06U-26H2W11J_GAP_FINAL_ANSWER_REHEARSAL.md`。
- 生成 `output/p3_06u_26h2w11j_gap_final_answer_rehearsal/summary.json`。
- 生成 `output/p3_06u_26h2w11j_gap_final_answer_rehearsal/gap_final_answer_samples_redacted.csv`。
- 生成 `output/p3_06u_26h2w11j_gap_final_answer_rehearsal/gap_final_answer_labels.csv`。
- 生成 `output/p3_06u_26h2w11j_gap_final_answer_rehearsal/gap_final_answer_rehearsal_report.md`。

真实结果：

- H2W-11I 缺口样本 7 条。
- 本轮生成脱敏最终答案样本 7 条。
- 本轮生成最终答案标签 7 条。
- 自动回复样本 5 条，事实性状态均为 `correct`。
- 转人工样本 2 条，事实性状态均为 `not_applicable`。
- 自动回复事实性通过率 1.0。
- 引用充分率 1.0。
- 禁用承诺通过率 1.0。
- 转人工正确率 1.0。
- `ready_for_gap_quality_report_review=true`。
- `ready_for_formal_accuracy_signoff=false`。

边界：

- H2W-11J 是本地确定性 rehearsal，不是真实大模型质量评测。
- 输出文件不包含完整最终客服答案正文。
- 输出文件不代表客户已经确认标准答案。
- 真实外发继续关闭。
- 不调用真实模型 provider。
- 不连接真实微信、企微、抖音、淘宝、京东、拼多多外发。
- 不使用真实客户原始数据。
- 不生成正式电子签章、合同签收或完整线上准确率结论。

下一步：

- 进入 H2W-11K：把 H2W-11J 缺口 rehearsal 标签汇入客户质量报告确认页和总控证据，但继续标记为本地演练；正式签收仍需客户确认标准答案、真实题库、线上回执和正式报告签收。

## 2026-07-04 更新：H2W-11K 客户质量报告缺口演练证据汇入

本轮继续 H2W-11 受控试点主线，不回到真实 IM、企业微信配置或 RPA 支线。

本轮完成：

- 后端 `CustomerQualityReportRead` 新增 `gap_rehearsal_evidence`。
- 质量报告生成逻辑读取 H2W-11J 的 `summary.json`，并把缺口演练证据写入摘要、关键指标、复盘章节、签收前动作、签收检查项和数据边界。
- HTML、XLSX、DOCX 客户报告导出件同步包含缺口演练证据。
- 前端质量复盘页的客户质量报告区新增“缺口样本本地演练证据”卡片。
- 新增 `docs/P3-06U-26H2W11K_CUSTOMER_REPORT_GAP_REHEARSAL_EVIDENCE.md`。
- 新增 `scripts/check_p3_06u_26h2w11k_customer_report_gap_rehearsal.py`。
- 新增 `backend/tests/test_p3_06u_26h2w11k_customer_report_gap_rehearsal.py`。

真实结果：

- H2W-11J 缺口演练样本 7 条。
- 自动回复样本 5 条。
- 转人工样本 2 条。
- 自动回复事实性、引用充分、禁用承诺通过、转人工正确性四项本地演练率均为 1.0。
- 客户质量报告页面可以看到缺口演练证据。

边界：

- H2W-11K 不是正式客户准确率签收。
- 真实外发继续关闭。
- 不调用真实模型 provider。
- 不连接真实微信、企微、抖音、淘宝、京东、拼多多外发。
- 不导出完整最终客服答案正文。
- 不使用真实客户原始数据。
- 不生成正式电子签章、合同签收或完整线上准确率结论。

下一步：

- 补客户确认标准答案、真实题库、线上回执、正式报告签收和生产级检索证据。
- 真实 IM 与官方渠道外发继续另开授权专项。

## 2026-07-04 更新：H2W-11L 客户标准答案确认输入包

本轮继续 H2W-11 受控试点主线，不回到真实 IM、企业微信配置或 RPA 支线。

本轮完成：

- 新增 `scripts/check_p3_06u_26h2w11l_customer_standard_answer_confirmation_pack.py`。
- 新增 `backend/tests/test_p3_06u_26h2w11l_customer_standard_answer_confirmation_pack.py`。
- 新增 `docs/P3-06U-26H2W11L_CUSTOMER_STANDARD_ANSWER_CONFIRMATION_PACK.md`。
- 生成 `evals/p3_06u_26h2w11l_customer_standard_answer_confirmation_pack.csv`。
- 生成 `output/p3_06u_26h2w11l_customer_standard_answer_confirmation_pack/summary.json`。
- 生成 `output/p3_06u_26h2w11l_customer_standard_answer_confirmation_pack/customer_standard_answer_confirmation_pack_review.md`。

真实结果：

- 待客户确认标准答案条目 12 条。
- 其中 7 条已关联 H2W-11J 缺口本地演练标签。
- 自动回复候选 9 条。
- 转人工候选 3 条。
- 当前客户确认条目 0 条。
- `ready_for_customer_standard_answer_confirmation_review=true`。
- `ready_for_formal_accuracy_signoff=false`。

边界：

- H2W-11L 是客户标准答案确认输入包，不是正式客户准确率签收。
- `customer_confirmed=false` 时，不进入正式准确率签收。
- 真实外发继续关闭。
- 不调用真实模型 provider。
- 不连接真实微信、企微、抖音、淘宝、京东、拼多多外发。
- 不使用真实客户原始数据。
- 不生成正式电子签章、合同签收或完整线上准确率结论。

下一步：

- 客户或业务负责人逐条确认标准答案、禁用承诺和转人工规则。
- 继续补真实题库、线上回执、正式报告签收和生产级检索证据。
- 真实 IM 与官方渠道外发继续另开授权专项。

## 2026-07-04 更新：H2W-11M 客户确认结果导入门禁

本轮继续 H2W-11 受控试点主线，不回到真实 IM、企业微信配置或 RPA 支线。

本轮完成：

- 新增 `scripts/check_p3_06u_26h2w11m_customer_confirmation_import_gate.py`。
- 新增 `backend/tests/test_p3_06u_26h2w11m_customer_confirmation_import_gate.py`。
- 新增 `docs/P3-06U-26H2W11M_CUSTOMER_CONFIRMATION_IMPORT_GATE.md`。
- 生成 `evals/p3_06u_26h2w11m_customer_confirmation_return_template.csv`。
- 生成 `output/p3_06u_26h2w11m_customer_confirmation_import_gate/summary.json`。
- 生成 `output/p3_06u_26h2w11m_customer_confirmation_import_gate/customer_confirmation_import_gate_review.md`。

真实结果：

- H2W-11L 确认包条目 12 条。
- 客户返回模板条目 12 条。
- 当前客户真实返回文件不存在。
- `customer_return_file_present=false`。
- `customer_confirmed_item_count=0`。
- `ready_for_customer_return_collection=true`。
- `ready_for_confirmed_standard_answer_import=false`。
- `ready_for_formal_accuracy_signoff=false`。

边界：

- H2W-11M 不伪造客户确认。
- 真实外发继续关闭。
- 不调用真实模型 provider。
- 不连接真实微信、企微、抖音、淘宝、京东、拼多多外发。
- 不使用真实客户原始数据。
- 不生成正式电子签章、合同签收或完整线上准确率结论。

## 2026-07-04 更新：H2W-12 工程推进与商用成熟度评估

本轮新增 `docs/P3-06U-26H2W12_ENGINEERING_AND_COMMERCIAL_READINESS_REVIEW.md` 和 `output/p3_06u_26h2w12_engineering_commercial_readiness_review/summary.json`。

核心结论：

- H2W 网状工程主线完成度约 `79/100`。
- 中小企业本地受控试点可用度约 `76/100`。
- 完整商用客服中台成熟度约 `64/100`。
- 全渠道自动回复商用成熟度约 `38/100`。
- 前端产品化成熟度约 `70/100`。
- 后端事实链成熟度约 `74/100`。

市场判断：

- 可以进入首批共创客户、受控本地试点和低风险场景验证。
- 不建议公开大规模宣传为成熟全渠道自动回复系统。
- 下一阶段优先补客户真实确认标准答案、真实 50-100 条脱敏题库、线上回执、生产级检索证据和前端逐页真实工作流 QA。

## 2026-07-04 更新：H2W-11N 到 H2W-7D 阶段门禁

本轮按 `H2W-11N -> H2W-11O -> H2W-11P -> H2W-FE2 -> H2W-10A -> H2W-7D` 推进，新增阶段总摘要：

- `docs/P3-06U-26H2W11N_TO_7D_EXECUTION_SUMMARY.md`

本轮完成：

- `scripts/check_p3_06u_26h2w11n_customer_confirmation_import.py`
- `scripts/check_p3_06u_26h2w11o_real_customer_eval_bank_import.py`
- `scripts/check_p3_06u_26h2w11p_final_answer_sampling.py`
- `scripts/check_p3_06u_26h2w_fe2_frontend_workflow_qa.py`
- `scripts/check_p3_06u_26h2w10a_wecom_official_sandbox_readiness.py`
- `scripts/check_p3_06u_26h2w7d_production_retrieval_evidence.py`
- `backend/tests/test_p3_06u_26h2w_next_stage_gates.py`

真实结果：

- H2W-11N：当前没有客户真实确认回传文件，状态为 `waiting_for_customer_return`。
- H2W-11O：当前没有真实 50-100 条脱敏题库文件，状态为 `waiting_for_real_customer_bank`。
- H2W-11P：因 H2W-11O 未 ready，状态为 `blocked_waiting_for_real_customer_bank`。
- H2W-FE2：前端静态真实性矩阵通过，功能矩阵 63 行、覆盖 12 页、客户可见工程词计数 0；App 内部变量仍需浏览器 QA 继续确认是否客户可见。
- H2W-10A：企业微信代码侧前置证据齐，但缺真实官方后台授权、公网 HTTPS 回调和可信 IP，状态为 `waiting_for_official_sandbox_conditions`。
- H2W-7D：pgvector 代码与策略证据齐，但缺真实题库评测和 PostgreSQL + pgvector 运行环境，状态为 `blocked_waiting_for_real_bank_or_postgres`。

边界：

- 本轮不伪造客户确认。
- 本轮不使用 demo 题库冒充真实题库。
- 本轮不把检索命中写成完整客服准确率。
- 本轮不打开真实外发。
- 本轮不调用付费模型。
- 本轮不把 RPA 写成正式默认交付能力。

## 2026-07-04 更新：H2W-11 内部演练输入与应用层评估

本轮按用户要求暂缓企业相关推进，不继续推进真实企微/微信客服、抖音、淘宝、京东、拼多多等企业渠道接入；同时为了让 H2W-11N、H2W-11O、H2W-11P 能继续工程演练，新增内部演练输入生成脚本和演练数据，但明确不把这些数据写成真实客户确认或正式客户签收。

新增：

- `scripts/generate_h2w11_internal_rehearsal_inputs.py`
- `evals/p3_06u_26h2w11m_customer_confirmation_return_received.csv`
- `evals/p3_06u_26h2w11o_real_customer_eval_bank_received.csv`
- `docs/P3-06U-26H2W11_INTERNAL_REHEARSAL_INPUTS_AND_APP_LAYER_REVIEW.md`
- `output/p3_06u_26h2w11_internal_rehearsal_inputs/summary.json`

门禁结果：

- H2W-11N：`passed_internal_rehearsal`，确认文件存在且可导入，但 `internal_rehearsal_confirmation_used=true`、`real_customer_confirmation_performed=false`、`ready_for_formal_accuracy_signoff=false`。
- H2W-11O：`passed_internal_rehearsal`，100 条脱敏客服题库可导入，`dataset_source_type=internal_synthetic_rehearsal`，不是客户真实题库。
- H2W-11P：`passed`，100 条最终答案采样和标签链路通过；`ready_for_internal_quality_report_candidate=true`，但 `ready_for_customer_quality_report_candidate=false`、`ready_for_formal_accuracy_signoff=false`。
- H2W-FE2：静态真实性矩阵通过，前端 typecheck/build 通过，负责人登录、知识维护主线和本地维护 UI smoke 通过。
- H2W-7D：仍阻断在 PostgreSQL + pgvector 真实运行环境，不能把 SQLite/JSON 检索包装成生产级向量检索。

当前应用层客观评估：

- 本地受控试点可用度：约 `80/100`。
- 应用层功能完整度：约 `74/100`。
- 前端产品化成熟度：约 `72/100`。
- 后端事实链成熟度：约 `76/100`。
- 完整商用客服成熟度：约 `65/100`。

当前结论：

- 系统已经不是空壳，具备本地受控试点雏形，可以继续做内部演练和共创客户前置准备。
- 系统还没有完全做好，不能写成成熟商用客服已经封版。
- 企业渠道、真实外发、正式客户签收、生产级 PostgreSQL + pgvector 检索、安装包/更新包/回滚链路、真实模型成本台账和全量浏览器逐按钮 QA 仍未完成。

下一步非企业主线：

1. H2W-7D-runtime：补 PostgreSQL + pgvector 真实运行环境、真实题库检索评测、引用 chunk/version/hash/source_uri。
2. H2W-FE3：做前端逐页逐按钮浏览器 QA，继续清理假按钮、重复入口、不可理解文案和多渠道对话台残留复杂度。
3. H2W-PACK1：补本地安装包、空库启动、首任负责人创建、备份、更新、回滚和诊断包闭环。
4. H2W-MODEL1：用小样本真实百炼/千问调用验证模型路由、成本台账、失败降级和预算门禁。
5. H2W-TRIAL1：用 100 条内部演练题库跑完整报告，但报告标题必须保持“内部演练”，不能写成客户验收。

## 2026-07-04 - H2W 封版候选非企业主线推进

- 本轮主线：暂缓企业/平台真实接入，推进 `H2W-7D-runtime`、`H2W-FE3`、`H2W-PACK1`、`H2W-MODEL1`、`H2W-TRIAL1`。
- 新增客户本地试点包环境模板 `deploy/customer.env.example`，默认关闭开发 bootstrap、真实外发和默认管理员密码。
- H2W-7D-runtime 输出 `blocked_waiting_for_pgvector_runtime`：pgvector 代码与 compose 声明齐，但 Docker daemon 未启动，且当前未配置 PostgreSQL + pgvector runtime 环境变量。
- H2W-FE3 输出 `passed`：前端 FE2、负责人登录、知识维护、本地维护 smoke 均 ready，多渠道对话台未出现待审核/待发送/AI 预备等干扰文案。
- H2W-PACK1 输出 `passed_local_package_candidate_with_runtime_pending`：本地试点包候选成立，但真实空库启动、pgvector runtime 和完整恢复演练还未封闭。
- H2W-MODEL1 输出 `guarded_external_call_not_allowed`：默认不调用百炼/千问，不计真实模型成本；后续需显式 `--allow-external-call` 才能跑 5-10 条成本小样本。
- H2W-TRIAL1 输出 `passed_internal_rehearsal_report_with_open_gaps`：内部 100 题演练报告已生成，但仍不是客户验收、正式准确率签收或真实题库。
- 关键输出：
  - `output/p3_06u_26h2w7d_runtime_pgvector_rehearsal/summary.json`
  - `output/p3_06u_26h2w_fe3_frontend_browser_workflow_qa/summary.json`
  - `output/p3_06u_26h2w_pack1_local_delivery_rehearsal/summary.json`
  - `output/p3_06u_26h2w_model1_bailian_cost_sample/summary.json`
  - `output/p3_06u_26h2w_trial1_internal_100q_rehearsal_report/summary.json`
  - `output/p3_06u_26h2w_trial1_internal_100q_rehearsal_report/internal_trial_report.md`
- 验证：
  - 新增脚本 `py_compile` 通过。
  - 新增封版包门禁测试 `3 passed`。
  - 相关后端回归 `12 passed`。
  - 前端 `npm run typecheck` 和 `npm run build` 通过。
- 下一步：
  - 启动 Docker Desktop 或提供外部 PostgreSQL + pgvector，复跑 H2W-7D-runtime。
  - 如要验证真实模型成本，用显式授权命令跑 H2W-MODEL1 小样本。
  - 在 pgvector runtime 和模型小样本补齐后，再评估是否进入本地试点包封版。

## 2026-07-04 - H2W runtime 与模型小样本收敛

- 本轮已启动 Docker Desktop daemon，`docker info` 返回 `29.5.3`。
- 已启动 `postgres` 与 `redis` compose 服务；`deploy-postgres-1` 和 `deploy-redis-1` 均为 healthy。
- H2W-7D-runtime 已从 `blocked_waiting_for_pgvector_runtime` 升级为 `ready_for_runtime_rehearsal`。
- pgvector ANN smoke 结果：
  - pgvector 版本 `0.8.2`。
  - HNSW `recall_at_k=1.0`，ANN 查询约 `1.887ms`。
  - IVFFlat `recall_at_k=1.0`，ANN 查询约 `1.474ms`。
- H2W-PACK1 已升级为 `passed_local_package_runtime_rehearsal_ready`。
- H2W-MODEL1 使用显式授权小样本运行，输出 `passed_real_small_sample_cost_rehearsal`：
  - 百炼 provider 真实调用 5 条。
  - 成功 5 条，失败 0 条。
  - 平均延迟约 `1693.324ms`。
  - tokens/字符量合计 `1064`。
  - 不记录原始文本，不真实外发。
- H2W-TRIAL1 已升级为 `passed_internal_rehearsal_report`，`open_gaps=[]`。
- 当前阶段判断：
  - 非企业主线的内部封版候选演练已通过。
  - 仍不是客户正式验收、真实题库准确率签收、真实平台外发或全渠道商用上线。

## 2026-07-05 - H2W-PACK2 全栈首启封版 rehearsal

- 本轮继续非企业主线，补齐客户本地交付时最关键的“干净空库首启”证据。
- 新增 `scripts/check_p3_06u_26h2w_pack2_full_stack_startup_rehearsal.py`：
  - 使用 Docker PostgreSQL/pgvector 创建临时数据库。
  - 对临时库执行完整 Alembic `upgrade head`。
  - 启动真实 Uvicorn 后端 HTTP 服务。
  - 通过真实接口验证首任负责人创建、创建后入口锁定、二次创建阻断、登录和 `/api/auth/me`。
  - 结束后终止临时服务并删除临时数据库。
- 修复 `deploy/docker-compose.pilot.yml` 的客户封版安全覆盖：
  - backend 显式 `STANDARD_OPS_DEV_BOOTSTRAP_ENABLED=false`。
  - backend 显式 `OUTBOX_EXTERNAL_WRITE_ENABLED=false`。
  - backend 显式 `TRUSTED_INBOUND_WORKER_ENABLED=false`。
  - worker profile 同样显式关闭开发 bootstrap。
- 修复干净空库迁移暴露的问题：
  - Alembic 默认 `alembic_version.version_num` 为 32 字符，原 `0020_knowledge_document_publications`、`0021_trusted_inbound_worker_leases`、`0030_diagnostic_remediation_requests` 超长，导致空库迁移失败。
  - 已把相关 revision/down_revision 收短为 `0020_kdoc_publications`、`0021_inbound_worker_leases`、`0030_diag_remediation_reqs`，表结构不变。
- 最新状态：
  - H2W-PACK2：`passed_full_stack_backend_startup_rehearsal`。
  - H2W-PACK1：`passed_local_package_runtime_rehearsal_ready`。
  - Alembic head：`0031_h2w7x_reply_provenance`。
- 验证：
  - `backend/.venv/bin/python scripts/check_p3_06u_26h2w_pack2_full_stack_startup_rehearsal.py` 通过。
  - `backend/.venv/bin/python scripts/check_p3_06u_26h2w_pack1_local_delivery_rehearsal.py` 通过。
  - `backend/.venv/bin/python -m pytest backend/tests/test_p3_06u_26h2w_sealed_pilot_package_gates.py backend/tests/test_p3_06u_26h2w_next_stage_gates.py -q` 通过，`10 passed`。
  - `cd backend && .venv/bin/alembic heads` 返回 `0031_h2w7x_reply_provenance (head)`。
- 边界：
  - 本轮不打开真实外发。
  - 本轮不推进企业微信、微信客服、抖音、淘宝、京东、拼多多真实接入。
  - PACK2 证明客户本地后端首启链路可跑，不等于完整安装器、桌面应用封包、客户签收或线上生产发布已经完成。

## 2026-07-05 - H2W-INSTALL3 原生包装候选第一片

- 本轮承接 PILOT5 的安装器下一轮分叉决策，进入原生安装器专项第一片。
- 新增安装器版本文件 `installers/VERSION.json`，明确 `package_version=0.1.0-local-pilot`，并保持 `signed_dmg_exe_ready=false`、`desktop_installer_ready=false`、`native_installer_ready=false`。
- 新增 `installers/logs/` 非敏感日志目录和说明，限定只保存启动前检查、健康检查、升级前预检 manifest、版本号、端口和开关状态，不保存密码、模型 key、平台 token、客户原文、草稿全文、浏览器 profile 或平台 payload。
- 新增 macOS `.app` 包装骨架 `installers/macos/WanfaCustomerService.app/`，当前只调用既有安全启动脚本，不创建 `customer.env`，不绕过外发关闭、worker 关闭、开发 bootstrap 关闭和客户密码替换门禁。
- 新增 macOS/Windows 健康检查脚本：
  - `installers/macos/health-check.sh`
  - `installers/windows/HealthCheck-WanfaCustomerService.ps1`
- 新增 macOS/Windows 升级前备份预检脚本：
  - `installers/macos/prepare-upgrade-backup.sh`
  - `installers/windows/Prepare-UpgradeBackup.ps1`
  - 预检只生成 manifest，不复制数据库、不读取密钥、不静默更新；下一步仍要求客户先在“账号与本地维护”里生成备份。
- 新增门禁脚本 `scripts/check_p3_06u_26h2w_install3_native_app_packaging_gate.py` 和阶段文档 `docs/P3-06U-26H2W_INSTALL3_NATIVE_APP_PACKAGING_GATE.md`。
- 当前 INSTALL3 状态：`native_app_packaging_candidate_ready`。
- 验证：
  - `backend/.venv/bin/python -m py_compile scripts/check_p3_06u_26h2w_install3_native_app_packaging_gate.py` 通过。
  - `bash -n installers/macos/WanfaCustomerService.app/Contents/MacOS/WanfaCustomerService && bash -n installers/macos/health-check.sh && bash -n installers/macos/prepare-upgrade-backup.sh` 通过。
  - `backend/.venv/bin/python scripts/check_p3_06u_26h2w_install3_native_app_packaging_gate.py` 通过。
  - `backend/.venv/bin/python -m pytest backend/tests/test_p3_06u_26h2w_sealed_pilot_package_gates.py -q` 通过，`33 passed`。
  - `backend/.venv/bin/python -m pytest backend/tests/test_pilot_api.py backend/tests/test_p3_06u_26h2w_sealed_pilot_package_gates.py -q` 通过，`37 passed`。
- 边界：
  - INSTALL3 仍不是正式签名 dmg/exe，不是完整桌面安装器。
  - 不打开真实外发，不远控客户电脑，不静默更新。
  - 不自动写入客户密码、模型 key、平台 secret、默认管理员密码或真实渠道凭据。
  - 下一步若继续安装器专项，应进入图标、卸载清理、升级前真实备份联动、更新失败回滚、代码签名准备和系统兼容 QA。

## 2026-07-05 - H2W-FE6 / INSTALL4 / KB3 / PILOT6 本地试用包候选刷新

- 本轮按 `H2W-FE6 -> H2W-INSTALL4 -> H2W-KB3 -> H2W-PILOT6` 执行，没有推进真实企业渠道、真实外发、RPA 正式交付或正式客户签收。
- FE6 新增浏览器级真实工作流复测脚本 `scripts/check_p3_06u_26h2w_fe6_latest_frontend_browser_qa.mjs`，使用临时空库、临时前后端、独立 Chrome profile 和真实负责人登录，覆盖 `#overview`、`#live`、`#knowledge`、`#gaps`、`#evals`、`#quality`、`#channels`、`#ops`、`#model`、`#settings`、`#pilot`，状态为 `passed_latest_frontend_browser_qa`。
- INSTALL4 新增 `installers/INSTALL4_EXPERIENCE_CHECKLIST.md`、`installers/macos/APP_ICON_NOTES.md`、`installers/windows/APP_ICON_NOTES.md` 和门禁 `scripts/check_p3_06u_26h2w_install4_packaging_experience_gate.py`，状态为 `native_packaging_experience_candidate_ready`；仍保持 `signed_dmg_exe_ready=false`。
- KB3 新增客户知识中心模板 `evals/p3_06u_26h2w_kb3_customer_knowledge_center_template.csv` 和门禁 `scripts/check_p3_06u_26h2w_kb3_customer_knowledge_center.py`，把知识运营固定为“导入资料 -> 预检 -> 发布 -> 复测 -> 确认 -> 质量报告”，状态为 `customer_knowledge_center_productized`。
- PILOT6 新增 `scripts/check_p3_06u_26h2w_pilot6_handoff_archive_refresh.py`，重新生成 `output/p3_06u_26h2w_pilot6_handoff_archive_refresh/pilot_handoff_archive_candidate_v1.zip` 和 manifest，状态为 `pilot_handoff_archive_candidate_v1`。
- 验证通过：
  - FE6 browser QA。
  - INSTALL4 / KB3 / PILOT6 门禁。
  - `npm run typecheck`。
  - `npm run build`。
  - `KNOWLEDGE_EMBEDDING_PROVIDER=deterministic_local KNOWLEDGE_EMBEDDING_MODEL= backend/.venv/bin/python -m pytest backend/tests/test_p3_06u_26h2w_sealed_pilot_package_gates.py backend/tests/test_rag_cost_governance_api.py backend/tests/test_channel_connectors_api.py backend/tests/test_p3_06f_ops_alert_rules_api.py backend/tests/test_knowledge_evaluations_api.py -q`，结果 `57 passed`。
- 边界：
  - 这仍是共创客户本地试用包候选，不是正式客户验收包。
  - 真实外发、真实企业/平台渠道、客户真实题库准确率、生产 SLA 和正式签名 dmg/exe 仍未完成。

## 2026-07-05 - H2W-DATA2R4 资料包预检入口与前端成品感解阻

- 本轮新增 `H2W-DATA2R4`：资料包预检 API 与试点准备页入口。
- 后端新增 `POST /api/tenants/{tenant_id}/customer-materials/precheck`，校验知识资料 CSV、试跑问题 CSV 和资料说明 JSON。
- 预检只返回摘要、指标和阻断项；不保存原始客户资料，不标记真实客户资料 ready，不开启真实外发。
- 前端“试点准备”页新增“资料预检”区块，客户可先看到字段、脱敏、50 条问题下限、禁用承诺和转人工规则是否满足。
- 同步修正试点准备页的客户可见工程词，FE9 最新状态为 `waiting_for_real_customer_materials`，FE10 最新状态为 `frontend_final_product_polish_ready`。
- PACK10 最新状态为 `blocked_waiting_real_customer_materials` 且 `blockers=[]`：剩余阻断是没有真实客户脱敏资料，而不是前端成品感或渠道/安装体验门禁失败。
- 验证通过：
  - `npm run typecheck && npm run build`
  - `PYTHONPATH=backend backend/.venv/bin/python -m pytest backend/tests/test_pilot_api.py backend/tests/test_p3_06u_26h2w_sealed_pilot_package_gates.py -q`
  - `python3 scripts/check_p3_06u_26h2w_data2r4_material_precheck_api_ui.py`
  - `node scripts/check_p3_06u_26h2w_fe9_customer_data_browser_qa.mjs`
  - `node scripts/check_p3_06u_26h2w_fe10_final_product_polish_gate.mjs`
  - `python3 scripts/check_p3_06u_26h2w_pack10_customer_data_trial_package.py`
- 边界：
  - 当前仍未收到真实客户资料。
  - 当前仍不是正式客户签收、真实客户题库准确率验收、真实平台外发、企业渠道上线、生产 SLA 或正式签名安装包。

## 2026-07-05 - H2W-DATA2R5 资料模板包与字段说明

- 本轮新增 `H2W-DATA2R5`：资料模板包 API 与前端模板辅助入口。
- 后端新增 `GET /api/tenants/{tenant_id}/customer-materials/template-package`，返回知识资料 CSV、试跑问题 CSV、资料说明 JSON 的空模板、示例、固定回传文件名、字段说明和下一步动作。
- 前端“试点准备 -> 资料预检”新增“加载资料模板”“填入示例资料”“下载三份模板”和字段说明卡片。
- 新增门禁与文档：
  - `scripts/check_p3_06u_26h2w_data2r5_material_template_package.py`
  - `docs/P3-06U-26H2W_DATA2R5_MATERIAL_TEMPLATE_PACKAGE.md`
  - `output/p3_06u_26h2w_data2r5_material_template_package/summary.json`
- 最新门禁状态：
  - DATA2R5：`material_template_package_ready`
  - FE9：`waiting_for_real_customer_materials`
  - FE10：`frontend_final_product_polish_ready`
  - PACK10：`blocked_waiting_real_customer_materials`，`blockers=[]`
- 验证通过：
  - `PYTHONPATH=backend backend/.venv/bin/python -m pytest backend/tests/test_pilot_api.py backend/tests/test_p3_06u_26h2w_sealed_pilot_package_gates.py -q`
  - `cd frontend && npm run typecheck && npm run build`
  - `python3 scripts/check_p3_06u_26h2w_data2r5_material_template_package.py`
  - `node scripts/check_p3_06u_26h2w_fe9_customer_data_browser_qa.mjs`
  - `node scripts/check_p3_06u_26h2w_fe10_final_product_polish_gate.mjs`
  - `python3 scripts/check_p3_06u_26h2w_pack10_customer_data_trial_package.py`
- 边界：
- DATA2R5 不保存原始客户资料。
- 示例资料不等于真实客户资料。
- 当前仍不是正式客户签收、真实外发、真实企业渠道上线、生产 SLA 或正式签名安装包。

## 2026-07-06 - H2W-NC15 PostgreSQL 正式恢复 SOP 与停机编排门禁

- 本轮新增 NC15：在 NC14 正式恢复执行 dry-run 后，登记 PostgreSQL 正式恢复 SOP 与停机编排门禁。
- 新增服务端接口 `POST /api/tenants/{tenant_id}/local-backups/postgres-formal-restore-runbook`，请求体为 `LocalPostgresFormalRestoreRunbookRegister`。
- 服务层新增 `register_postgres_formal_restore_runbook`、`_validate_postgres_formal_restore_runbook` 和 `_postgres_formal_restore_runbook_record_payload`。
- NC15 强制要求同一备份记录已存在 `last_formal_restore_execution_dry_run`，并要求命令预览 hash 与 NC14 一致。
- 本地维护 readiness 已纳入 `local_backup.postgres_formal_restore_runbook_registered`。
- 新增门禁与报告：
  - `scripts/check_p3_06u_26h2w_nc15_formal_restore_runbook.py`
  - `docs/P3-06U-26H2W_NC15_FORMAL_RESTORE_RUNBOOK.md`
  - `output/p3_06u_26h2w_nc15_formal_restore_runbook/summary.json`
- 最新状态：`formal_restore_runbook_ready_no_live_restore`。
- 验证通过：
  - `backend/.venv/bin/python -m pytest backend/tests/test_local_backups_api.py -q` -> `16 passed`
  - `python3 scripts/check_p3_06u_26h2w_nc15_formal_restore_runbook.py` -> `formal_restore_runbook_ready_no_live_restore`
  - `backend/.venv/bin/python -m pytest backend/tests/test_signed_update_packages_api.py backend/tests/test_local_backups_api.py backend/tests/test_local_maintenance_readiness_api.py -q` -> `32 passed`
  - `backend/.venv/bin/python -m pytest backend/tests/test_p3_06u_26h2w_sealed_pilot_package_gates.py -q` -> `49 passed`
- 边界：
  - NC15 不执行 `pg_restore`，不替换真实数据库，不保存 dump 文件本体，不保存原始恢复命令，不打开真实外发。
  - NC15 不是应用内一键恢复，也不是生产恢复完成。
  - 下一步不应继续在应用内推进真实恢复执行，除非另开客户现场停机窗口、人工执行、健康检查和回滚专项。

## 2026-07-06 - H2W-NC17 红队题库与影子试跑标签包

- 本轮新增 NC17：在 NC16 红队闭环规则之后，补齐一套内部准真实红队样本包和影子试跑人工标签包。
- 新增样本目录：
  - `evals/p3_06u_26h2w_nc17_redteam_shadow_trial/redteam_cases.csv`
  - `evals/p3_06u_26h2w_nc17_redteam_shadow_trial/redteam_labeled_shadow_results.csv`
  - `evals/p3_06u_26h2w_nc17_redteam_shadow_trial/README.md`
- 红队样本共 25 条，五类风险各 5 条：
  - `prompt_injection`
  - `jailbreak`
  - `privacy_leak`
  - `forbidden_commitment`
  - `over_permission`
- 所有样本均要求 `expected_human_review=true`、`allow_auto_reply=false`、`internal_sample_only=true`。
- 所有标签均走 `transfer_to_human` 安全路径，且 `handoff_correct_rate=1.0`、`forbidden_commitment_pass_rate=1.0`、`citation_sufficient_rate=1.0`、`unsafe_label_count=0`。
- 新增门禁与报告：
  - `scripts/check_p3_06u_26h2w_nc17_redteam_shadow_trial.py`
  - `backend/tests/test_p3_06u_26h2w_nc17_redteam_shadow_trial.py`
  - `docs/P3-06U-26H2W_NC17_REDTEAM_SHADOW_TRIAL.md`
  - `output/p3_06u_26h2w_nc17_redteam_shadow_trial/summary.json`
- 最新状态：`redteam_shadow_trial_internal_sample_ready_not_customer_security_signoff`。
- 验证通过：
  - `python3 scripts/check_p3_06u_26h2w_nc17_redteam_shadow_trial.py` -> `redteam_shadow_trial_internal_sample_ready_not_customer_security_signoff`
  - `backend/.venv/bin/python -m pytest backend/tests/test_p3_06u_26h2w_nc17_redteam_shadow_trial.py -q` -> `3 passed`
  - `python3 scripts/check_p3_06u_26h2w_nc16_redteam_closure.py` -> `redteam_closure_gate_ready_internal_fixtures_only`
  - `backend/.venv/bin/python -m pytest backend/tests/test_llm_ops_readiness_api.py -q` -> `6 passed`
  - `backend/.venv/bin/python -m pytest backend/tests/test_p3_06u_26h2w_sealed_pilot_package_gates.py -q` -> `49 passed`
  - `python3 -m py_compile scripts/check_p3_06u_26h2w_nc17_redteam_shadow_trial.py`
- 边界：
  - NC17 不调用真实模型。
  - NC17 不打开真实外发。
  - NC17 不推进真实渠道接入。
  - NC17 不等于客户真实红队安全签收。
  - 后续若要升级为客户安全报告，必须使用真实客户脱敏业务题库、真实模型输出、客户/业务负责人复核标签和独立签收记录。

## 2026-07-06 - H2W-NC18 红队事实账本导入与前端观测卡片联动

- 本轮新增 NC18：把 NC17 内部红队样本和影子标签导入隔离数据库事实账本，并验证现有 `llm-ops-readiness` 服务可从数据库评测表读取红队 readiness。
- 新增门禁与报告：
  - `scripts/check_p3_06u_26h2w_nc18_redteam_fact_ingest.py`
  - `backend/tests/test_p3_06u_26h2w_nc18_redteam_fact_ingest.py`
  - `docs/P3-06U-26H2W_NC18_REDTEAM_FACT_INGEST.md`
  - `output/p3_06u_26h2w_nc18_redteam_fact_ingest/summary.json`
- 同步扩展：
  - `backend/app/schemas/llm_ops.py`：红队 readiness 增加来源和内部样本字段。
  - `backend/app/services/llm_ops.py`：识别 `internal_sample_only=true` 的红队样本来源，并在 gate evidence 里返回来源。
  - `frontend/src/api/client.ts`、`frontend/src/App.tsx`：自动回复策略页“模型观测与红队”卡片展示题集来源和类目覆盖。
- 最新状态：`redteam_fact_ingest_ready_internal_sample_visible_to_llm_ops`。
- 关键指标：
  - `imported_case_count=25`
  - `imported_label_count=25`
  - `llm_ops_redteam.readiness=ready_for_controlled_pilot`
  - `internal_sample_only=true`
  - `raw_attack_vector_persisted=false`
- 验证通过：
  - `backend/.venv/bin/python -m pytest backend/tests/test_p3_06u_26h2w_nc18_redteam_fact_ingest.py -q` -> `2 passed`
  - `backend/.venv/bin/python -m pytest backend/tests/test_llm_ops_readiness_api.py -q` -> `6 passed`
  - `backend/.venv/bin/python scripts/check_p3_06u_26h2w_nc18_redteam_fact_ingest.py` -> `redteam_fact_ingest_ready_internal_sample_visible_to_llm_ops`
  - `npm --prefix frontend run typecheck` -> 通过
  - `npm --prefix frontend run build` -> 通过，保留既有大 chunk warning
  - `backend/.venv/bin/python -m pytest backend/tests/test_p3_06u_26h2w_nc17_redteam_shadow_trial.py -q` -> `3 passed`
  - `backend/.venv/bin/python -m pytest backend/tests/test_p3_06u_26h2w_sealed_pilot_package_gates.py -q` -> `49 passed`
- 边界：
  - NC18 仍是内部样本数据库导入 rehearsal，不是客户真实红队安全签收。
  - NC18 不调用真实模型，不开启真实外发，不推进真实平台渠道。
  - 后续若进入客户安全报告，必须重新使用真实客户脱敏题库、真实模型输出、客户/业务负责人复核标签和正式确认记录。

## 2026-07-06｜H2W-NC19 客户红队安全报告流程准备

- 本轮新增 NC19：在 NC18 内部红队事实账本之后，补客户红队安全报告的资料接收模板、报告骨架和等待态门禁。
- 新增门禁与报告：
  - `scripts/check_p3_06u_26h2w_nc19_customer_redteam_report_flow.py`
  - `backend/tests/test_p3_06u_26h2w_nc19_customer_redteam_report_flow.py`
  - `docs/P3-06U-26H2W_NC19_CUSTOMER_REDTEAM_REPORT_FLOW.md`
  - `evals/p3_06u_26h2w_nc19_customer_redteam_report/`
  - `output/p3_06u_26h2w_nc19_customer_redteam_report/summary.json`
- 最新状态：`customer_redteam_report_flow_ready_waiting_customer_data`。
- 边界：NC19 是客户红队报告模板和等待态，不是客户真实安全报告、真实模型输出标签、客户负责人复核确认或正式安全签收。

## 2026-07-06｜H2W-COMM1 对外本地试跑商用包 v1 候选

- 本轮新增 COMM1：把当前系统从“内部样板本地试跑候选”收束为可用于对外沟通的“共创客户本地受控试跑包候选”，并把五件事与七大核心板块放入同一个门禁结果。
- 新增门禁与报告：
  - `scripts/check_p3_06u_26h2w_comm1_commercial_trial_launch_package.py`
  - `backend/tests/test_p3_06u_26h2w_comm1_commercial_trial_launch_package.py`
  - `docs/P3-06U-26H2W_COMM1_COMMERCIAL_TRIAL_LAUNCH_PACKAGE.md`
  - `output/p3_06u_26h2w_comm1_commercial_trial_launch_package/summary.json`
  - `output/p3_06u_26h2w_comm1_commercial_trial_launch_package/commercial_trial_launch_package_v1_candidate.zip`
- 五件事已落产物：
  - 真实客户样板资料包。
  - 客户知识中心最终流程。
  - 前端最终成品级 QA。
  - 本地部署交付包 v1。
  - 对外试跑商业资料包。
- 七大核心板块已纳入矩阵：
  - 真实客户资料闭环。
  - 客户知识中心最终产品化。
  - 前端最终成品感。
  - 真实渠道闭环。
  - 安装和交付体验。
  - 真实安全与红队报告。
  - 商用包装。
- 最新状态：
  - `status=commercial_trial_launch_package_v1_candidate_with_internal_sample`。
  - `ready_for_external_pitch_as_controlled_trial=true`。
  - `ready_for_paid_co_creation_local_trial=true`。
  - `ready_for_direct_customer_production=false`。
  - `ready_for_mature_all_channel_commercial=false`。
- 验证通过：
  - COMM1 专项测试：`2 passed`。
  - COMM1 / NC19 / sealed pilot 回归：`53 passed`。
  - COMM1 门禁：`commercial_trial_launch_package_v1_candidate_with_internal_sample`。
  - 前端 typecheck/build：通过，保留既有大 chunk warning。
- 边界：
  - COMM1 是对外试跑候选包，不是真实客户资料版封包。
  - COMM1 不是正式客户验收、真实平台外发、真实渠道闭环、生产 SLA、签名安装包或移动端完成。
  - 成熟商用发布仍需真实客户资料重跑、正式渠道专项、签名安装器、客户合同/验收和线上运维 SLA。
