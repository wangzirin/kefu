# 标准运营版工程骨架

这是“万法常世 AI 全智能客服系统”的标准运营版工程目录，用于把当前 Lite 原型升级为可运营、可审计、可扩展的客服中台。

2026-07-06 最新状态以本条为准：FIX8 前端成品细节精修已完成，覆盖下面 FIX1-FIX7 的旧审计状态。逐按钮审计重新通过，当前 `status=passed_without_p0_p1`，P0/P1/P2 均为 0；本地发送浏览器 smoke 通过，结果为 `message-visible` 且“未发送到外部平台”边界提示可见。本轮补齐禁用控件原因、图标/文件输入标签、分页不可用说明、线索阶段按钮说明、知识运营/缺口/评测按钮说明、账号重置/停用边界说明，使客户可见按钮符合“真实动作、明确禁用说明、隐藏”三选一原则。验证通过：前端 `typecheck/build`、逐按钮审计和本地发送 smoke；后端健康检查正常。真实外发、真实渠道接通、正式客户签收、生产 SLA、签名安装包和移动端仍未完成。

2026-07-06 最新状态以本条为准：FIX1-FIX7 智能客服系统前端与主链路修复已完成第一轮，当前前端逐按钮审计 `status=passed_without_p0_p1`。本轮把接待工作台补成可用的本地回复闭环：坐席可在 `#live` 输入内容并点击“发送到本地会话”，后端写入 `direction=outbound`、`sender_type=agent`、`external_message_id=""` 的本地消息，消息流立即刷新，并明确展示“未发送到外部平台”；AI 建议改为“填入输入框”，不伪装成已发送。同步把“试点准备”收束为“本地试运行准备”，首屏突出导入资料、运行复测、导出交付档案；联系人和线索降级为轻量客户资料与商机记录，修复横向裁切；渠道页改为“配置准备与边界说明”，人工登记状态写成待官方验证；运维页客户可见 `outbox` 等工程词已替换为客户语言。验证通过：前端 `typecheck/build`、后端会话消息测试与 sealed pilot 回归 `52 passed`、逐按钮审计脚本和本地发送浏览器 smoke；当前 P0/P1 为 0，剩余 8 个 P2 均为禁用原因/图标标签细节。真实外发、真实渠道接通、正式客户签收、生产 SLA、签名安装包和移动端仍未完成。

2026-07-06 早前状态：H2W-COMM1 对外本地试跑商用包 v1 候选已完成，当前 `status=commercial_trial_launch_package_v1_candidate_with_internal_sample`。本轮把用户要求的五件事落成可验证产物：真实客户样板资料包、客户知识中心最终流程、前端最终成品级 QA、本地部署交付包 v1、对外试跑商业资料包；同时把七大核心板块写入机器可读矩阵：真实客户资料闭环、客户知识中心最终产品化、前端最终成品感、真实渠道闭环、安装和交付体验、真实安全与红队报告、商用包装。新增 COMM1 门禁脚本、专项测试、阶段文档、10 份试跑资料文档和 zip 档案；验证通过：COMM1 专项测试 `2 passed`、COMM1 门禁、COMM1/NC19/sealed pilot 回归 `53 passed`、脚本 py_compile、前端 typecheck/build。当前可以作为“共创客户本地受控试跑包”对外沟通，但仍不是成熟全渠道正式商用系统；真实客户资料、真实平台外发、真实渠道闭环、正式客户签收、生产 SLA、已签名 dmg/exe 安装包和移动端仍未完成。

2026-07-06 最新状态以本条为准：H2W-NC19 客户红队安全报告流程准备已完成第一片，当前 `status=customer_redteam_report_flow_ready_waiting_customer_data`。本轮基于 NC18 内部红队事实账本，生成客户红队题库、人工标签和 manifest 三件套模板，并生成客户红队安全报告骨架；门禁会在没有真实客户回传文件时保持“等待客户资料”，不会把内部样本写成客户安全报告或正式签收。验证通过：NC19 专项测试 `2 passed`、NC19 门禁、NC17/NC18/LLM ops 相邻回归 `11 passed`、sealed pilot gates `49 passed`、脚本 py_compile。当前完成的是客户红队安全报告流程模板和等待态，不是客户真实红队题库、真实模型输出标签、客户业务负责人复核确认或正式安全签收；真实客户资料版封包、完整 Memory Mesh 图谱、真实渠道、生产 SLA、签名安装包和移动端仍未完成。

2026-07-06 早前状态：H2W-NC18 红队事实账本导入与前端观测卡片联动已完成第一片，当前 `status=redteam_fact_ingest_ready_internal_sample_visible_to_llm_ops`。本轮把 NC17 的 25 条内部红队样本和 25 条影子标签导入隔离数据库，落成评测集、评测用例、评测运行、人工标签和试点事实记录，并验证现有 `GET /api/tenants/{tenant_id}/llm-ops-readiness` 能读取数据库事实；前端“自动回复策略 -> 模型观测与红队”卡片已展示安全题集、人工标签、题集来源和类目覆盖。验证通过：NC18 专项测试 `2 passed`、LLM ops API 测试 `6 passed`、NC18 门禁、前端 typecheck/build、NC17 回归 `3 passed`、sealed pilot gates `49 passed`。当前完成的是内部样本数据库事实导入 rehearsal，不是客户真实红队安全签收；真实客户资料版封包、真实客户红队题库/真实模型输出标签、完整 Memory Mesh 图谱、真实渠道、生产 SLA、签名安装包和移动端仍未完成。

2026-07-06 早前状态：H2W-NC17 红队题库与影子试跑标签包已完成第一片，当前 `status=redteam_shadow_trial_internal_sample_ready_not_customer_security_signoff`。本轮新增 25 条内部准真实红队样本和 25 条影子试跑人工标签，覆盖提示注入、越狱、隐私泄露、禁用承诺、越权操作五类风险；全部样本标记为不允许自动回复、需要人工复核，标签结果均走转人工安全路径，且不含真实客户原文、真实密钥或平台 payload。新增 NC17 门禁脚本、阶段文档和专门回归测试。验证通过：NC17 门禁、NC17 测试 `3 passed`、NC16 相邻门禁、LLM ops API 测试 `6 passed`、sealed pilot gates `49 passed`、脚本 py_compile。当前完成的是内部红队样本包和影子标签包，不是客户真实红队安全签收；真实客户资料版封包、真实客户红队题库/真实模型输出标签、完整 Memory Mesh 图谱、真实渠道、生产 SLA、签名安装包和移动端仍未完成。

2026-07-06 早前状态：H2W-NC16 红队闭环门禁已完成第一片，当前 `status=redteam_closure_gate_ready_internal_fixtures_only`。本轮收紧 `GET /api/tenants/{tenant_id}/llm-ops-readiness` 的红队判定：红队题集必须覆盖提示注入、越狱、隐私泄露、禁用承诺和越权操作五类风险，全部活跃红队题必须有最终答案人工标签，失败样本必须逐条进入知识缺口或质量复盘，不能再用任意知识缺口冒充闭环。新增 NC16 门禁脚本和阶段文档，验证通过：LLM ops API 测试 `6 passed`、NC16 门禁、NC6 相邻门禁、pilot/knowledge gaps 相邻回归 `17 passed`、sealed pilot gates `49 passed`。当前完成的是红队闭环规则和内部 fixture 验证，不是客户真实红队安全签收；真实客户资料版封包、真实客户红队题库/模型输出标签、完整 Memory Mesh 图谱、真实渠道、生产 SLA、签名安装包和移动端仍未完成。

2026-07-06 早前状态：H2W-NC15 PostgreSQL 正式恢复 SOP 与停机编排门禁已完成第一片，当前 `status=formal_restore_runbook_ready_no_live_restore`。本轮新增 `POST /api/tenants/{tenant_id}/local-backups/postgres-formal-restore-runbook`，用于在 NC14 正式恢复执行 dry-run 外壳之后登记恢复 SOP、停机编排、二次备份要求、最终确认、恢复后健康检查和回滚决策树。服务端只保存摘要、hash 和审计，不执行 `pg_restore`，不替换真实数据库，不保存 dump 本体或原始恢复命令。验证通过：NC15 门禁、本地备份/维护/签名更新回归 `32 passed`、sealed pilot gates `49 passed`。

2026-07-06 早前状态：H2W-NC13 PostgreSQL 正式恢复前置门禁已完成第一片，当前 `status=formal_restore_preflight_gate_ready_no_live_restore`。本轮新增 `POST /api/tenants/{tenant_id}/local-backups/postgres-formal-restore-preflight`，用于在 NC10 备份证据、NC11 恢复计划和 NC12 临时库恢复演练之后，登记客户管理员确认包、维护窗口、恢复前二次备份要求、健康检查计划、回滚计划和最终操作员确认。服务端只登记确认包摘要、hash、前置门禁和审计，不执行 `pg_restore`，不替换真实数据库，不打开真实外发，也不提供应用内一键恢复。验证通过：NC13 门禁、NC12/NC11 相邻门禁、local backups / local maintenance / signed update 回归 `28 passed`。当前仍等待客户机实际 NC8/NC12 manifest 和后续正式恢复执行 SOP；真实客户资料版封包、签名安装包、真实渠道、生产 SLA、移动端仍未完成。

2026-07-06 早前状态：H2W-NC12 PostgreSQL 临时库恢复演练已完成第一片，当前 `status=postgres_temp_restore_rehearsal_ready_waiting_customer_pg_run`。本轮新增 `deploy/postgres-temp-restore-rehearsal.sh` 和 `POST /api/tenants/{tenant_id}/local-backups/postgres-temp-restore-manifests`；客户机脚本会在明确传入 NC8 备份目录后，把 `postgres.dump` 恢复到安全前缀 `wanfa_restore_tmp_...` 的临时 PostgreSQL 数据库，跑健康检查，再删除临时库并输出 manifest。服务端只登记 manifest、hash、临时库恢复摘要和审计，不保存 dump 文件本体，不保存临时库明文名，不执行服务端 `pg_restore`，不替换真实数据库，不打开真实外发。验证通过：NC12 门禁、NC11/NC10 相邻门禁、local backups / local maintenance / signed update 回归 `26 passed`、sealed pilot gates `49 passed`。当前仍等待客户机实际运行 NC8/NC12 脚本并登记 manifest；正式恢复执行、停机窗口、恢复前二次备份、客户管理员确认、真实客户资料版封包、签名安装包、真实渠道、生产 SLA、移动端仍未完成。

2026-07-06 早前状态：H2W-NC11 PostgreSQL 恢复演练计划已完成第一片，当前 `status=postgres_restore_rehearsal_plan_ready_no_live_restore`。本轮新增 `POST /api/local-backups/{local_backup_id}/postgres-restore-rehearsal-plan`，用于基于 NC10 已登记的 PostgreSQL `pg_dump` / `pg_restore --list` manifest 生成受控恢复演练计划；服务端只做计划、校验和审计，写入 `last_restore_rehearsal_plan` / `postgres_restore_rehearsal_plan`，不执行 `pg_restore`，不替换数据库，不保存 dump 文件本体，不打开真实外发。验证通过：NC11 门禁、NC10 相邻门禁、local backups / local maintenance / signed update 回归 `24 passed`、sealed pilot gates `49 passed`。当前仍等待客户机实际 PostgreSQL 备份演练 manifest；真实恢复执行工具、真实客户资料版封包、签名安装包、真实渠道、生产 SLA、移动端仍未完成。

2026-07-06 早前状态：H2W-NC10 PostgreSQL 备份证据登记已完成第一片，当前 `status=postgres_backup_evidence_registration_ready_waiting_customer_pg_run`。本轮新增 `POST /api/tenants/{tenant_id}/local-backups/postgres-dry-run-manifests`，用于登记客户本机运行 `deploy/postgres-backup-dry-run.sh` 后生成的 manifest；服务端只保存 manifest、hash、大小、`pg_restore --list` 可读性结果和 `last_restore_dry_run` 摘要，不保存 dump 文件本体，不执行真实恢复，不替换数据库，不打开真实外发。验证通过：NC10 门禁、local backups / local maintenance / signed update 回归 `22 passed`、NC8/NC9 相邻门禁、sealed pilot gates `49 passed`。当前仍等待客户机实际 PostgreSQL 备份演练 manifest；真实客户资料版封包、真实恢复工具、签名安装包、真实渠道、生产 SLA、移动端仍未完成。

2026-07-06 最新状态以本条为准：H2W-NC9 非真实渠道版本地试跑包 v4 已完成，当前 `status=local_trial_package_v4_candidate_with_internal_sample`。本轮新增 `scripts/check_p3_06u_26h2w_nc9_local_trial_package_v4.py`，聚合 NC1-NC8、PACK11、PACK12、FE12、KB6、TRIAL3、OPS2、OPS3、INSTALL7 等证据，生成 `docs/P3-06U-26H2W_NC9_LOCAL_TRIAL_PACKAGE_V4.md`、`output/p3_06u_26h2w_nc9_local_trial_package_v4/summary.json`、`manifest.json` 和 `local_trial_package_v4_candidate.zip`。档案包含启动说明、首任负责人说明、资料模板、知识导入与预检、知识复测、影子试跑质量、月度运维、诊断备份更新回滚、安装候选和边界声明；扫描阻断 key、token、密码、客户原文、平台 payload、`.git`、`node_modules`、浏览器 profile、临时数据库、Cookies、History 和 Login Data。验证通过：NC9 门禁、脚本 py_compile、NC8/NC7 相邻门禁、PACK11 聚合回归、sealed pilot gates `49 passed`。当前仍是内部样板本地试跑包候选，不是真实客户资料版封包、正式客户签收、真实外发、真实渠道、生产 SLA、移动端或签名安装包完成。

2026-07-06 最新状态以本条为准：H2W-NC8 本地安装、备份、更新与回滚补强已完成第一片，当前 `status=local_install_backup_update_rollback_hardened_pg_script_ready`。本轮补强客户本地启动脚本，增加 Docker daemon、Docker Compose、磁盘空间、端口占用、PostgreSQL readiness、迁移 head、真实外发关闭和入站 worker 关闭检查；新增 `deploy/postgres-backup-dry-run.sh`，可在客户本机导出 PostgreSQL `pg_dump -Fc` 备份并用 `pg_restore --list` 校验可读性，且不执行真实恢复、不替换数据库；签名知识包和策略包 apply 前新增服务端门禁，必须存在已验证本地备份和恢复 dry-run 证据，否则拒绝应用。验证通过：NC8 门禁、后端 signed update/local backup/local maintenance 相关测试 `20 passed`、bash 语法检查、H2W8B 静态门禁。NC10 已补服务端 PostgreSQL manifest 登记能力；当前仍未在客户 Docker 环境实际执行 PostgreSQL 备份演练并提供 manifest。真实外发、真实渠道、正式客户签收、生产 SLA、移动端和签名安装包仍未完成。

2026-07-06 最新状态以本条为准：H2W-NC7 前端真实产品化收束已完成第一片，当前 `status=frontend_productization_customer_flow_ready_component_split_pending`。本轮把“试点准备”提升为一级主入口，把“账号安全”统一为“账号与本地维护”，质量复盘客户可见口径从“签收”降级为“试跑确认”，账号与本地维护的月度运维报告入口改为真实页面跳转，并用 NC7 门禁锁住多渠道对话台 IM 主形态、渠道页官方条件/未接通边界和孤儿链接问题。验证通过：NC7 门禁、前端 typecheck/build、FE6 浏览器真实登录 smoke。当前客户主路径产品化已改善，但 `App.tsx`、`styles.css`、`api/client.ts` 仍偏大，组件拆分和进一步视觉精修尚未完成；真实外发、真实渠道、正式客户签收、生产 SLA、移动端和签名安装包仍未完成。

2026-07-06 最新状态以本条为准：H2W-NC6 模型观测、成本与红队治理第一片已完成，当前 `status=llm_ops_observability_ready_not_redteam_complete`。本轮新增 `GET /api/tenants/{tenant_id}/llm-ops-readiness`，以 `ops.metrics.read` 权限读取模型网关版本、显式模型服务商失败不静默切换、模型调用成本台账、降级动作、链路追踪、引用快照、最终答案标签和红队题集状态；前端“自动回复策略”页新增“模型观测与红队”卡片和门禁列表。验证通过：LLM ops API 测试、RAG 治理相邻回归、封版门禁相邻回归、NC6 聚合门禁、前端 typecheck/build。当前模型成本与链路观测已接上，但红队题集和人工标签尚未完整闭环，所以不能写成安全评测完成、客户正式准确率签收、真实外发、真实渠道、生产 SLA 或签名安装包完成。

2026-07-06 最新状态以本条为准：H2W-NC5 生产级检索与评测治理已完成第一轮收束，当前 `status=production_retrieval_governance_ready_not_production_switch`。本轮新增 `production_readiness` 运行态总账，生产检索切换必须同时满足 PostgreSQL+pgvector runtime、真实客户资料批次、50 题以上题库、最终答案质量标签、embedding 成本记录、客服模型调用成本和预算策略；前端“生产检索准备度”已显示真实资料批次状态，避免把内部样板误写成生产可切换。验证通过：RAG 治理 API 测试、向量索引相邻回归、H2W7 静态门禁、NC5 聚合门禁、前端 typecheck/build。当前治理层 ready，但真实客户资料 ready=false、真实资料链路重跑 ready=false，所以不能切生产检索，不能写正式客户签收、真实外发、真实渠道、生产 SLA 或签名安装包完成。

2026-07-06 最新状态以本条为准：H2W-NC4 知识中心 v2 与 Memory Mesh 化第一片已完成，当前 `status=knowledge_memory_mesh_overview_ready`。本轮新增只读接口 `GET /api/tenants/{tenant_id}/knowledge-memory-mesh-overview`，把资料批次、知识卡片、业务对象、真实/样本问题、质量标签与错因纳入同一张知识网络总览；前端“知识库运营 / 知识缺口 / 知识评测”三页统一展示证据链，包括入站样本、检索结果、引用 chunk、模型调用、最终草稿、转人工理由、质量标签和修复后的知识版本。接口只返回计数、状态、hash/source_uri 覆盖和边界，不返回客户原文、文档正文或草稿全文。验证通过：知识 API 测试、NC4 门禁、封版相邻回归、前端 typecheck/build。当前仍不是完整图数据库式 Memory Mesh，不代表真实客户资料闭环、真实外发、真实渠道、正式客户签收、生产 SLA 或签名安装包完成。

2026-07-06 最新状态以本条为准：H2W-NC3 客户资料接收与预检产品化已完成，当前 `status=customer_material_precheck_productization_ready`。本轮新增资料预检批次只读接口 `GET /api/tenants/{tenant_id}/customer-materials/batches`，前端“试点准备”页支持从本地 CSV/JSON 填入资料草稿、刷新资料批次并展示最近批次状态；后端批次列表只返回 hash、统计和状态，不返回客户问题原文、标准答案全文、密钥或平台 payload。验证通过：`backend/tests/test_pilot_api.py`、封版相邻门禁、NC3 门禁、全量 `backend/tests`、前端 typecheck/build。预检批次通过只代表可以进入固定文件接收目录；真实客户资料闭环、真实外发、真实渠道、正式客户签收、生产 SLA 和签名安装包仍未完成。

2026-07-06 最新状态以本条为准：H2W-NC2 客户模式安全硬化已完成，当前 `status=customer_mode_security_hardening_ready`。本轮新增登录失败限速、失败审计和冷却；首任负责人创建会在开发 bootstrap、真实外发或入站 worker 误开启时阻断；客户模式下无 token 的 `/api/auth/me` 不能返回开发 bootstrap 用户；诊断上传包新增大小、嵌套深度和 schema allowlist 门禁，坏包只保存拒收摘要，不再原样长期保存；交付档案扫描禁止浏览器 profile、Cookies、History、Login Data、`.git` 和 `node_modules`。验证通过：auth/local setup/diagnostics 目标测试、NC2 门禁、全量 `backend/tests`、前端 typecheck/build。真实客户资料、真实外发、真实渠道、正式客户签收、生产 SLA 和签名安装包仍未完成。

2026-07-06 最新状态以本条为准：H2W-NC1 试点事实账本权威化已完成，当前 `status=nc1_pilot_fact_authority_ready`。`pilot-readiness` 新增 `customer_data_ready`、`customer_data_readiness_source`、`customer_data_ready_blockers`、`customer_data_ready_evidence` 和 `summary_evidence_authority`，客户资料 ready 只由数据库事实链决定；工程 `summary.json` 现在带 `schema_version`、`sha256`、`age_seconds`、`stale` 和 `authority=engineering_evidence_only`，只能作为工程证据。客户确认导入会落入 `pilot_readiness_facts` 的 `pilot2.knowledge_confirmation_import`，只保存 hash、计数、状态和风险数量，不保存原始 CSV。验证通过：`backend/tests/test_pilot_api.py`、NC1 门禁、全量 `backend/tests`、前端 typecheck/build。真实客户资料、真实外发、真实渠道、正式客户签收、生产 SLA 和签名安装包仍未完成。

2026-07-05 最新状态以本条为准：用户要求先由工程侧制作三份固定“客户回传”文件用于跑链路；本轮已在 `evals/p3_06u_26h2w_data2_real_customer_material_readiness/` 生成 `customer_materials_received.csv`、`customer_trial_questions_received.csv`、`customer_material_manifest_received.json`。这三份文件被明确标记为内部准真实样板，不是客户真实回填、不是客户确认、不是正式签收。DATA2 当前 `status=internal_sample_materials_ready_for_rehearsal`，包含 22 条知识资料、60 条试跑问题；DATA2R7 当前 `status=received_internal_sample_files_validated_ready_for_pack12_rerun`；PACK12 当前 `status=internal_sample_data_rerun_orchestration_ready`，`customer_data_used=false`、`internal_sample_used=true`、`customer_data_rerun_complete=false`、`internal_sample_rerun_complete=true`。本轮验证通过：DATA2、DATA2R7、DATA2R8、PACK12 门禁，封版门禁 `49 passed`，pilot API `9 passed`，前端 typecheck/build。真实客户资料、真实外发、真实渠道、正式客户签收、生产 SLA 和签名安装包仍未完成。

2026-07-05 最新状态以本条为准：H2W-DATA2R8 回传落位状态接入已完成，当前 `status=material_drop_gate_api_ui_ready`。`pilot-readiness` 已新增 `material_drop_gate_status` 和 `material_drop_gate_evidence`，前端“试点准备”页在资料接收包和五大缺口卡片中展示“回传文件落位”状态。新增 `scripts/check_p3_06u_26h2w_data2r8_material_drop_gate_api_ui.py`、`docs/P3-06U-26H2W_DATA2R8_MATERIAL_DROP_GATE_API_UI.md` 和 `output/p3_06u_26h2w_data2r8_material_drop_gate_api_ui/summary.json`。当前 DATA2R7 仍为 `received_file_drop_ready_waiting_customer_files`，三份固定客户回传文件尚未到齐；真实外发、真实渠道、客户签收、生产 SLA 和签名安装包仍未完成。

2026-07-05 最新状态以本条为准：H2W-DATA2R7 真实资料回传落位门禁已完成，当前 `status=received_file_drop_ready_waiting_customer_files`。新增 `scripts/check_p3_06u_26h2w_data2r7_received_file_drop_gate.py`、`docs/P3-06U-26H2W_DATA2R7_RECEIVED_FILE_DROP_GATE.md` 和 `output/p3_06u_26h2w_data2r7_received_file_drop_gate/summary.json`。DATA2R7 复核真实资料接收目录、四个模板/说明文件、DATA2、DATA2R6 回传文件包和 PACK12 重跑编排状态；当前三份固定回传文件 `customer_materials_received.csv`、`customer_trial_questions_received.csv`、`customer_material_manifest_received.json` 尚未回传，所以只输出等待客户文件和后续重跑命令，不升级为客户数据 ready。真实外发关闭，真实渠道未接通，客户签收、生产 SLA 和签名安装包仍未完成。

2026-07-05 最新状态以本条为准：H2W-PACK12 真实资料重跑编排门禁已完成，当前 `status=waiting_for_real_customer_materials_for_customer_data_rerun`。新增 `scripts/check_p3_06u_26h2w_pack12_customer_data_rerun_orchestrator.py`、`docs/P3-06U-26H2W_PACK12_CUSTOMER_DATA_RERUN_ORCHESTRATOR.md` 和 `output/p3_06u_26h2w_pack12_customer_data_rerun_orchestrator/summary.json`。PACK12 先运行 DATA2R；当真实客户资料仍未回传时，停止在等待态并列出后续命令，不继续跑 KB6/TRIAL3/FE9/PACK10/PACK11，也不伪造客户数据链完成。真实资料到齐后，PACK12 会按 DATA2R -> KB6 -> TRIAL3 -> FE9 -> PACK10 -> PACK11 串联重跑，只有全部 ready 才会进入客户数据版重跑完成口径。当前真实资料仍未到齐，真实外发关闭，真实渠道未接通，客户签收、生产 SLA 和签名安装包仍未完成。

2026-07-05 最新状态以本条为准：H2W-INSTALL7 封包前客户模式门禁已完成，并已纳入 H2W-PACK11 聚合总账。新增 `scripts/check_p3_06u_26h2w_install7_customer_mode_prepack_gate.py`、`docs/P3-06U-26H2W_INSTALL7_CUSTOMER_MODE_PREPACK_GATE.md` 和 `output/p3_06u_26h2w_install7_customer_mode_prepack_gate/summary.json`。INSTALL7 复核客户模式启动前置条件：开发 bootstrap 关闭、无默认管理员密码、真实外发关闭、入站 worker 默认关闭、客户 env 不写入真实密钥、安装器/远控/静默更新均保持未完成边界；当前 `status=customer_mode_prepack_gate_ready`。PACK11 已改为读取 INSTALL7，当前 `installer_customer_mode_status=customer_mode_prepack_gate_ready`，整体仍保持 `blocked_waiting_real_customer_materials` 且 `blockers=[]`。真实客户资料仍未到齐，真实外发仍关闭，真实渠道未接通，正式签名安装包未完成，不能写成客户签收或成熟全渠道商用系统。

2026-07-05 最新状态以本条为准：H2W-CROSS1 到 H2W-PACK11 第一轮实现完成，并已补入 H2W-FE12 客户视角二次浏览器验收。新增数据库事实表 `pilot_readiness_facts` 和资料批次表 `customer_material_batches`，`pilot-readiness` 开始返回数据库事实和最新资料批次；资料预检只保存 hash、数量、覆盖类型和阻断数量，不保存客户原文。新增本地安全测试会话接口 `POST /api/tenants/{tenant_id}/pilot-safe-test-conversation`，前端多渠道对话台空态新增“生成本地测试会话”入口；该入口只写入本地数据库，不触发真实平台外发。新增 `docs/P3-06U-26H2W_CROSS1_FULL_STACK_FACT_BASELINE.md`、`docs/P3-06U-26H2W_FE12_CUSTOMER_PERSPECTIVE_BROWSER_QA.md`、`scripts/check_p3_06u_26h2w_cross1_full_stack_baseline.py`、`scripts/check_p3_06u_26h2w_fact1_data3_runtime_facts.py`、`scripts/check_p3_06u_26h2w_fe11_safe_test_conversation_gate.mjs`、`scripts/check_p3_06u_26h2w_fe12_customer_perspective_browser_qa.mjs`、`scripts/check_p3_06u_26h2w_pack11_local_trial_v3_candidate.py` 和 `output/p3_06u_26h2w_pack11_local_trial_v3_candidate/summary.json`。当前 CROSS1/FACT1/FE11/FE12 均通过，PACK11 正确保持 `blocked_waiting_real_customer_materials` 且 `blockers=[]`；真实客户资料仍未到齐，真实外发仍关闭，真实渠道未接通，签名安装包未完成。

2026-07-05 最新状态以本条为准：H2W-DATA2R6 资料回传文件包已完成，当前 `status=material_handoff_bundle_ready`。新增后端 `GET /api/tenants/{tenant_id}/customer-materials/handoff-bundle`，返回 base64 zip，包含固定回传文件 `customer_materials_received.csv`、`customer_trial_questions_received.csv`、`customer_material_manifest_received.json` 和 `README.md`；前端“试点准备 -> 资料预检”新增“下载回传文件包”按钮；新增门禁脚本 `scripts/check_p3_06u_26h2w_data2r6_material_handoff_bundle.py`、阶段文档 `docs/P3-06U-26H2W_DATA2R6_MATERIAL_HANDOFF_BUNDLE.md` 和输出 `output/p3_06u_26h2w_data2r6_material_handoff_bundle/summary.json`。该 zip 只用于降低客户回传文件名漂移风险，仍是示例和空模板，`customer_data_used=false`、`raw_materials_persisted=false`、`real_customer_materials_ready=false`；FE9 仍为 `waiting_for_real_customer_materials`，FE10 为 `frontend_final_product_polish_ready`，PACK10 仍为 `blocked_waiting_real_customer_materials` 且 `blockers=[]`。

2026-07-05 最新状态以本条为准：H2W-DATA2R5 资料模板包与字段说明已完成，当前 `status=material_template_package_ready`。新增后端 `GET /api/tenants/{tenant_id}/customer-materials/template-package`、前端“试点准备 -> 资料预检”里的加载资料模板、填入示例资料、下载三份模板和字段说明，新增门禁脚本 `scripts/check_p3_06u_26h2w_data2r5_material_template_package.py`、阶段文档 `docs/P3-06U-26H2W_DATA2R5_MATERIAL_TEMPLATE_PACKAGE.md` 和输出 `output/p3_06u_26h2w_data2r5_material_template_package/summary.json`。示例资料只用于熟悉格式和跑预检，`customer_data_used=false`、`raw_materials_persisted=false`、`real_customer_materials_ready=false`；PACK10 仍为 `blocked_waiting_real_customer_materials` 且 `blockers=[]`。

2026-07-05 最新状态以本条为准：H2W-DATA2R3 真实资料门禁反例校验已完成，当前 `status=material_validation_fixtures_passed`。新增门禁脚本 `scripts/check_p3_06u_26h2w_data2r3_material_validation_fixtures.py`、阶段文档 `docs/P3-06U-26H2W_DATA2R3_MATERIAL_VALIDATION_FIXTURES.md` 和输出 `output/p3_06u_26h2w_data2r3_material_validation_fixtures/summary.json`。本轮用 9 组样例验证 DATA2 真实资料校验器能放行合规 50 题资料包，并阻断题库不足、缺来源字段、个人联系方式、真实外发越界、正式签收越界、非法动作、JSON 密钥字段和越界承诺。`pilot-readiness` 已新增 `material_validation_fixture_status`，前端“试点准备”页会展示资料门禁校验状态。真实客户资料仍未到齐，DATA2 仍为 `waiting_for_real_customer_materials`，PACK10 仍为 `blocked_waiting_real_customer_materials`。

2026-07-05 最新状态以本条为准：H2W-DATA2R2 真实资料接收包门禁已完成，当前 `status=material_intake_package_ready`。新增客户资料接收与脱敏手册 `docs/customer/万法常世AI客服真实资料接收与脱敏手册.md`、门禁脚本 `scripts/check_p3_06u_26h2w_data2r2_material_intake_package.py`、阶段文档 `docs/P3-06U-26H2W_DATA2R2_MATERIAL_INTAKE_PACKAGE.md` 和输出 `output/p3_06u_26h2w_data2r2_material_intake_package/summary.json`。前端“试点准备”页新增资料接收包说明，后端 `pilot-readiness` 已新增 `material_intake_package_status`。本片只说明资料接收包、模板、脱敏手册和接收目录已准备好；真实客户资料仍未到齐，PACK10 仍为 `blocked_waiting_real_customer_materials`，不能生成客户数据版试跑包。

2026-07-05 最新状态以本条为准：H2W-DATA2R、KB6、TRIAL3、FE9、FE10、CHANNEL2、INSTALL6 和 PACK10 五大缺口门禁已完成本轮实现与验证。当前真实结果：DATA2R 为 `waiting_for_real_customer_materials`，KB6/TRIAL3/FE9 均因真实客户资料未到齐保持等待态；FE10 为 `frontend_final_product_polish_ready`，CHANNEL2 为 `channel_personnel_boundary_ready`，INSTALL6 为 `trial_installer_experience_candidate_ready`；PACK10 聚合状态为 `blocked_waiting_real_customer_materials`。本轮已扩展 `pilot-readiness` 聚合字段、前端“试点准备”五大缺口卡片、渠道页“人员与边界”说明和安装体验候选清单。边界不变：不伪造客户资料，不把内部样板写成客户试跑，不启用真实外发，不推进真实平台接入，不写成正式客户签收、生产 SLA 或签名安装包完成。

2026-07-05 最新状态以本条为准：H2W-PACK9 真实客户资料重跑计划门禁已完成。新增门禁脚本 `scripts/check_p3_06u_26h2w_pack9_real_customer_rerun_plan.py`、阶段文档 `docs/P3-06U-26H2W_PACK9_REAL_CUSTOMER_RERUN_PLAN.md` 和输出 `output/p3_06u_26h2w_pack9_real_customer_rerun_plan/summary.json`。当前 `status=pack9_plan_ready_waiting_real_customer_materials`：PACK9 已把真实资料到齐后的重跑链路固定为 DATA2 -> PACK8B -> KB6 -> TRIAL3 -> FE9 -> PACK9，但 DATA2 仍为 `waiting_for_real_customer_materials`，所以现在只能保持计划 ready，不能生成客户数据版交付档案。边界不变：不伪造客户资料，不把内部样板写成客户资料或客户签收，不启用真实外发，不推进真实渠道，不写生产 SLA 或签名安装包完成。

2026-07-05 最新状态以本条为准：H2W-PACK8B 真实资料边界锁已完成。新增门禁脚本 `scripts/check_p3_06u_26h2w_pack8b_real_material_boundary_lock.py`、阶段文档 `docs/P3-06U-26H2W_PACK8B_REAL_MATERIAL_BOUNDARY_LOCK.md` 和输出 `output/p3_06u_26h2w_pack8b_real_material_boundary_lock/summary.json`。当前 `status=pack8_boundary_locked_waiting_real_materials`：PACK8 仍为 `co_creation_trial_package_v1_1_candidate_with_internal_data`，DATA2 仍为 `waiting_for_real_customer_materials`，所以系统会继续把共创试跑包锁定为内部样板候选。真实客户资料未到齐前，不允许升级为客户数据包、正式客户签收、真实渠道上线、真实外发、生产 SLA 或签名安装包完成。

2026-07-05 最新状态以本条为准：H2W-DATA2 真实客户脱敏资料接入前置门禁已完成。新增 `evals/p3_06u_26h2w_data2_real_customer_material_readiness/` 接收目录、真实资料模板、真实题库模板、manifest 模板、门禁脚本 `scripts/check_p3_06u_26h2w_data2_real_customer_material_readiness.py` 和阶段文档 `docs/P3-06U-26H2W_DATA2_REAL_CUSTOMER_MATERIAL_READINESS.md`。当前 `status=waiting_for_real_customer_materials`，表示系统已准备好接收真实客户脱敏资料，但尚未收到固定文件 `customer_materials_received.csv`、`customer_trial_questions_received.csv`、`customer_material_manifest_received.json`。`pilot-readiness` 已新增真实资料状态字段，前端“试点准备”页会显示“下一轮真实资料：等待真实脱敏资料”。固定边界不变：不伪造客户资料，不把内部样板写成真实客户资料，不启用真实外发，不推进真实企业/平台渠道，不写成正式客户签收、签名安装包、生产 SLA 或成熟全渠道商用系统。

2026-07-05 最新状态以本条为准：H2W-TRIAL-C0、H2W-DATA1、H2W-DEPLOY1、H2W-KB5、H2W-TRIAL2、H2W-FE8 和 H2W-PACK8 已完成“共创客户本地试跑包 v1.1 候选”。TRIAL-C0 冻结共创试跑范围，当前 `status=trial_scope_ready`。DATA1 建立资料接收 manifest 和内部准真实样板，当前 `status=internal_sample_only_ready`，`customer_data_used=false`、`internal_sample_used=true`。DEPLOY1 复核干净本地试跑关键证据，当前 `status=clean_local_trial_rehearsal_passed`。KB5 基于 DATA1 内部样板输出知识导入与复测报告，当前 `status=customer_knowledge_retest_ready_with_internal_data`。TRIAL2 输出影子试跑质量报告，当前 `status=shadow_trial_ready_with_internal_data`。FE8 完成试跑摩擦门禁，当前 `status=trial_frontend_friction_resolved`。PACK8 已生成非敏感交付档案候选 `output/p3_06u_26h2w_pack8_trial_package_v1_1/co_creation_trial_package_v1_1_candidate.zip`，当前 `status=co_creation_trial_package_v1_1_candidate_with_internal_data`；聚合接口侧总状态为 `co_creation_trial_v1_1_candidate_with_internal_data`。固定边界不变：不做移动端，不启用真实外发，不推进真实企业/平台渠道，不把内部样板写成真实客户资料或客户签收，不把 RPA 作为正式交付能力，不写成正式签名 dmg/exe、生产 SLA 或成熟全渠道商用系统。

2026-07-05 最新状态以本条为准：H2W-PILOT7、H2W-FE7、H2W-KB4、H2W-INSTALL5、H2W-OPS3 和 H2W-PACK7 已完成“共创客户本地试跑封版 v1”候选。PILOT7 聚合 FE6、INSTALL4、KB3、PILOT6、OPS2、PACK5、KB2、MODEL1 和 TRIAL1，当前 `status=co_creation_trial_candidate_ready_with_internal_data`。FE7 使用临时空库、临时服务和浏览器真实登录，逐页点击试点准备、知识中心、质量复盘、账号与本地维护和交付档案入口，当前 `status=passed_customer_trial_browser_smoke`，并清理客户可见工程词。KB4 将知识中心试跑闭环固定为“导入资料 -> 预检 -> 发布 -> 复测 -> 确认 -> 质量报告”，当前 `status=customer_knowledge_trial_loop_ready`。INSTALL5 验证 Docker、端口、客户环境文件、外发关闭、日志和卸载/清理说明，当前 `status=local_startup_experience_ready`。OPS3 完成客户试跑运维闭环说明和诊断、月报、备份、恢复、更新预检、售后接收台证据聚合，当前 `status=customer_trial_ops_loop_ready`。PACK7 已生成非敏感交付档案候选 `output/p3_06u_26h2w_pack7_trial_handoff_archive_v2/co_creation_trial_handoff_archive_v2_candidate.zip`，当前 `status=co_creation_trial_handoff_archive_v2_candidate`。固定边界不变：不做移动端，不启用真实外发，不推进真实企业/平台渠道，不把内部演练写成客户签收，不把 RPA 作为正式交付能力，不写成正式签名 dmg/exe 或生产 SLA。

2026-07-05 最新状态以本条为准：H2W-FE6、H2W-INSTALL4、H2W-KB3 和 H2W-PILOT6 已完成本轮“共创客户本地试用包候选 v1”刷新。FE6 使用临时空库、临时前后端和浏览器真实登录逐页点击总览、接待工作台、多渠道对话台、知识运营三页、质量复盘、渠道接入、账号与本地维护、自动回复策略和试点准备页，状态为 `passed_latest_frontend_browser_qa`，截图证据在 `output/p3_06u_26h2w_fe6_latest_frontend_browser_qa/`。INSTALL4 补齐安装候选体验清单、macOS/Windows 图标说明、日志/端口/Docker/卸载清理检查，状态为 `native_packaging_experience_candidate_ready`，仍保持 `signed_dmg_exe_ready=false`。KB3 把客户知识中心收束为业务对象、标准问答、流程政策、禁用承诺与转人工规则四层输入，状态为 `customer_knowledge_center_productized`。PILOT6 已重新生成非敏感试点交付档案候选 `output/p3_06u_26h2w_pilot6_handoff_archive_refresh/pilot_handoff_archive_candidate_v1.zip`，状态为 `pilot_handoff_archive_candidate_v1`。固定边界不变：不做移动端，不启用真实外发，不推进真实企业/平台渠道，不把内部演练写成客户正式签收，不把 RPA 作为正式交付能力，不把安装器候选写成已签名 dmg/exe。

2026-07-05 最新状态以本条为准：H2W-INSTALL3 原生包装候选第一片已完成。新增 `installers/VERSION.json`、`installers/logs/` 非敏感日志目录、macOS `.app` 包装骨架 `installers/macos/WanfaCustomerService.app/`、macOS/Windows 健康检查脚本、macOS/Windows 升级前备份预检脚本，以及门禁脚本 `scripts/check_p3_06u_26h2w_install3_native_app_packaging_gate.py`。当前 INSTALL3 状态为 `native_app_packaging_candidate_ready`：macOS `.app` 包装候选、Windows 健康检查与升级预检候选、安装器版本文件和日志策略均通过门禁。固定边界不变：`signed_dmg_exe_ready=false`、`desktop_installer_ready=false`、`native_installer_ready=false`，不启用真实外发，不远控客户电脑，不静默更新，不自动填写客户密码或模型凭据。本轮验证通过：INSTALL3 门禁、Python 编译、macOS bash 语法检查、sealed pilot gates `33 passed`、pilot API + sealed gates 组合回归 `37 passed`。

2026-07-05 最新状态以本条为准：H2W-PILOT0 到 H2W-PILOT5 已完成“共创客户本地试点包候选 v1”封版前最后一轮。新增后端 `GET /api/tenants/{tenant_id}/pilot-readiness`、`POST /api/tenants/{tenant_id}/knowledge-confirmations/imports`，前端新增“试点准备”入口，按本地环境、账号负责人、知识资料、复测确认、质量/月报、诊断备份更新 6 步展示真实状态和阻断原因。新增门禁脚本 `scripts/check_p3_06u_26h2w_pilot0_readiness.py`、`scripts/check_p3_06u_26h2w_pilot2_customer_confirmation_flow.py`、`scripts/check_p3_06u_26h2w_pilot3_handoff_archive.py`、`scripts/check_p3_06u_26h2w_pilot4_customer_trial_rehearsal.mjs`、`scripts/check_p3_06u_26h2w_pilot5_installer_next_fork_decision.py`，并生成 `output/p3_06u_26h2w_pilot0_readiness/`、`pilot2_customer_confirmation_flow/`、`pilot3_handoff_archive/`、`pilot4_customer_trial_rehearsal/`、`pilot5_installer_next_fork_decision/`。当前 PILOT0 状态为 `pilot_candidate_ready_with_internal_data`，PILOT2 为 `waiting_customer_confirmation`，PILOT3 为 `pilot_handoff_archive_candidate`，PILOT4 为 `passed_customer_local_trial_rehearsal`，PILOT5 为 `installer_next_fork_decision_ready`。本轮验证通过：PILOT0/2/3/5 门禁、PILOT4 临时空库真实登录浏览器演练、后端回归 `35 passed`、前端 typecheck/build。固定边界不变：这不是客户正式签收，不是真实客户题库，不启用真实外发，不推进企业微信/抖音/淘宝/京东/拼多多真实接入，不远控客户电脑，不静默更新，`signed_dmg_exe_ready=false`。

2026-07-05 最新状态以本条为准：H2W-OPS2 客户侧月度运维报告 rehearsal 与 H2W-INSTALL2 原生安装器候选结构已完成。OPS2 新增只读接口 `GET /api/tenants/{tenant_id}/monthly-ops-report?year=&month=`、前端“质量复盘 -> 月度运维报告”区块、账号与本地维护轻入口、门禁脚本 `scripts/check_p3_06u_26h2w_ops2_customer_monthly_ops_report.py` 和输出 `output/p3_06u_26h2w_ops2_customer_monthly_ops_report/`；当前状态为 `ready_for_customer_monthly_ops_report_rehearsal`，但仍不是生产 SLA。INSTALL2 新增 `installers/macos/` 与 `installers/windows/` 候选包装目录、门禁脚本 `scripts/check_p3_06u_26h2w_install2_native_installer_readiness.py` 和输出 `output/p3_06u_26h2w_install2_native_installer_readiness/`；当前状态为 `native_wrapper_candidate_ready`，`signed_dmg_exe_ready=false`、`desktop_installer_ready=false`。本轮验证通过：OPS2/INSTALL2 单测、月度接口回归、整份 sealed pilot gates `26 passed`、前端 typecheck/build、质量复盘浏览器 smoke。固定边界不变：不推进真实渠道、不打开真实外发、不远控客户电脑、不静默更新、不自动写客户密码或模型凭据、不把内部演练写成客户签收。

2026-07-05 最新状态以本条为准：H2W-11N/11O 两步已按内部演练口径复核通过，并新增综合成熟度评估文档 `docs/P3-06U-26H2W11N_11O_RECHECK_AND_OVERALL_READINESS_REVIEW.md`。本轮复跑 `generate_h2w11_internal_rehearsal_inputs.py`、H2W-11N、H2W-11O 和 H2W-11P：内部确认回传 12 条、内部脱敏题库 100 条、最终答案采样 100 条均通过；相关测试 `7 passed`，封版包门禁回归 `22 passed`。当前小微企业本地受控试点候选约 `84/100`，共创客户本地交付候选约 `80/100`，标准运营版成熟商用约 `70/100`，全渠道自动回复约 `40/100`。边界不变：本轮不是客户真实确认、不是客户真实题库、不是正式准确率签收、不是真实平台外发、不是企业渠道上线，也不是完整 dmg/exe 原生安装器。

2026-07-05 最新状态以本条为准：H2W-KB2 客户专属知识包导入后复测报告与签收模板已通过。本轮新增 `scripts/check_p3_06u_26h2w_kb2_post_import_retest_and_signoff_template.py`、`docs/P3-06U-26H2W_KB2_POST_IMPORT_RETEST_AND_SIGNOFF_TEMPLATE.md` 和 `output/p3_06u_26h2w_kb2_post_import_retest_and_signoff_template/summary.json`，并生成 `post_import_retest_report.md` 与 `customer_knowledge_retest_signoff_template.csv`。KB2 聚合 KB1 的内部脱敏知识包导入、查询、回滚证据和 OPS1 售后交接证据，输出 9 项客户确认模板；模板中确认人、确认时间和客户意见均为空，`filled_customer_confirmation_count=0`。当前状态为 `ready_for_customer_specific_knowledge_retest_template`；但正式客户签收、客户专属知识库正式启用、真实客户数据、真实平台外发、企业渠道真实上线、provider 调用和生产 SLA 均仍为 false。

2026-07-05 早前状态：H2W-OPS1 售后运维交接演练已通过。本轮新增 `scripts/check_p3_06u_26h2w_ops1_after_sales_handoff_rehearsal.py`、`docs/P3-06U-26H2W_OPS1_AFTER_SALES_HANDOFF_REHEARSAL.md` 和 `output/p3_06u_26h2w_ops1_after_sales_handoff_rehearsal/summary.json`，并把客户启动说明中的安全边界统一为“真实外发默认关闭”。OPS1 聚合 INSTALL1、PACK5、KB1 和 H2W-8B 本地维护浏览器验收证据，确认诊断包接收、售后处理单、签名更新包、备份、恢复演练、审计事件、远程维护授权 SOP、内部售后计划和客户启动说明均满足交接门禁。当前状态为 `ready_for_after_sales_ops_handoff_rehearsal`；但我方远程控制客户电脑、静默自动更新、正式客户准确率签收、真实平台自动外发、企业渠道真实上线、生产 SLA 和完整 macOS dmg / Windows exe 安装器均仍为 false。

2026-07-05 早前状态：H2W-INSTALL1 非技术客户本地启动器 rehearsal 已通过。本轮新增 `deploy/start-local-pilot.command`、`docs/customer/万法常世AI客服本地试点启动说明.md`、`scripts/check_p3_06u_26h2w_install1_nontechnical_customer_starter.py`、`docs/P3-06U-26H2W_INSTALL1_NONTECHNICAL_CUSTOMER_STARTER.md` 和 `output/p3_06u_26h2w_install1_nontechnical_customer_starter/summary.json`。INSTALL1 聚合 PACK5 与 KB1 证据，验证双击启动包装器、客户启动说明、安全启动脚本和客户环境模板均满足门禁：不自动创建客户 env、不预置默认密码、不启用 worker、不打开真实外发、不输出模型 key。当前状态为 `ready_for_nontechnical_customer_startup_rehearsal`；但完整 macOS dmg / Windows exe 安装器、正式客户准确率签收、真实平台自动外发、企业渠道真实上线、客户专属知识库正式验收和生产级 SLA 均仍为 false。

2026-07-05 早前状态：H2W-PACK5 客户本地试点交付包候选门禁已通过。本轮新增 `scripts/check_p3_06u_26h2w_pack5_customer_handoff_package.py`、`docs/P3-06U-26H2W_PACK5_CUSTOMER_LOCAL_PILOT_HANDOFF_PACKAGE.md` 和 `output/p3_06u_26h2w_pack5_customer_handoff_package/summary.json`。PACK5 只读聚合 PACK2 全栈首启、PACK3 本地受控试点候选、PACK4 安全启动入口、FE4 客户可见 UI、FE4 浏览器点击 QA、pgvector runtime、MODEL1 小样本成本和 TRIAL1 内部 100 题演练；同时检查 `deploy/start-local-pilot.sh`、`deploy/customer.env.example`、Docker Compose、客户资料文档和内部工程文档是否齐备。当前状态为 `ready_for_customer_local_pilot_handoff_candidate`，可作为小微企业本地受控试点交付包候选继续进入客户专属知识包试点或安装器专项；但正式客户准确率签收、真实平台自动外发、企业渠道真实上线、客户专属知识库验收、完整桌面安装器和生产级 SLA 均仍为 false。

2026-07-05 早前状态：H2W-FE4 客户可见 UI 封版候选门禁已通过。本轮新增 `scripts/check_p3_06u_26h2w_fe4_customer_ui_sealed_candidate.py`、`scripts/check_p3_06u_26h2w_fe4_customer_visible_click_qa.mjs`、`docs/P3-06U-26H2W_FE4_CUSTOMER_UI_SEALED_CANDIDATE.md`、`output/p3_06u_26h2w_fe4_customer_ui_sealed_candidate/summary.json` 和 `output/p3_06u_26h2w_fe4_customer_visible_click_qa/summary.json`。静态门禁结果为 `ready_for_customer_visible_ui_candidate`，浏览器点击 QA 结果为 `passed_customer_visible_click_qa`：脚本使用临时 SQLite、临时后端、临时前端和独立 Chrome profile，通过真实登录页创建负责人工作区，逐页检查运营总览、接待工作台、知识运营三页、质量复盘、渠道接入、运维、模型路由和账号与本地维护；多渠道对话台保持紧凑会话列表 + 大面积消息流，隐藏后台工作项不进入侧边栏，客户可见工程词、越界完成态和假外发均为 0。边界仍不变：这不是正式客户准确率签收、真实平台自动外发、企业渠道真实上线、客户专属知识库验收、完整桌面安装器或生产级 SLA。

2026-07-05 早前状态：H2W-PACK4 本地试点交付清单与安全启动 rehearsal 已通过。本轮新增 `deploy/start-local-pilot.sh`、`scripts/check_p3_06u_26h2w_pack4_delivery_checklist_and_startup_rehearsal.py`、`docs/P3-06U-26H2W_PACK4_LOCAL_PILOT_DELIVERY_CHECKLIST.md` 和 `output/p3_06u_26h2w_pack4_delivery_checklist_and_startup_rehearsal/summary.json`。当前状态为 `ready_for_customer_local_pilot_startup_rehearsal`，表示 PACK3 候选已具备客户本地试点启动入口和交付清单：客户需复制 `deploy/customer.env.example` 为 `deploy/customer.env`、替换本地随机数据库密码，再运行安全启动脚本；脚本会在启动前阻断开发 bootstrap、真实外发、入站 worker、默认管理员密码和模板数据库密码。边界仍不变：这不是完整桌面安装器、正式客户准确率签收、真实平台自动外发、企业渠道真实上线、客户专属知识库验收或生产级 SLA。

2026-07-05 早前状态：H2W-PACK3 本地受控试点封版候选总门禁已通过。本轮新增 `scripts/check_p3_06u_26h2w_pack3_local_pilot_candidate_readiness.py` 和阶段文档 `docs/P3-06U-26H2W_PACK3_LOCAL_PILOT_CANDIDATE_READINESS.md`，把 PACK2 全栈首启、PACK1 本地交付候选、FE3 前端真实工作流、7D pgvector runtime、MODEL1 百炼小样本成本和 TRIAL1 内部 100 题演练统一纳入机器可读总门禁。当前状态为 `ready_for_local_controlled_pilot_candidate`，代表可进入“小微企业本地受控试点包候选”的下一步打包和试用准备；边界仍不变：正式客户准确率签收、真实平台自动外发、企业渠道真实上线、客户专属知识库验收、完整桌面安装器和生产级 SLA 仍未完成。

2026-07-05 早前状态：H2W-PACK2 全栈首启封版 rehearsal 已通过。本轮新增 `scripts/check_p3_06u_26h2w_pack2_full_stack_startup_rehearsal.py`，使用 Docker PostgreSQL/pgvector 创建临时空库，跑完整 Alembic 迁移，启动真实 Uvicorn HTTP 服务，并通过 `/api/auth/local-setup/status`、`/api/auth/local-setup/owner`、`/api/auth/login`、`/api/auth/me` 验证首任负责人创建、创建后锁定、二次创建阻断和登录身份读取。`deploy/docker-compose.pilot.yml` 已显式关闭 `STANDARD_OPS_DEV_BOOTSTRAP_ENABLED`、`OUTBOX_EXTERNAL_WRITE_ENABLED` 和 backend 侧 `TRUSTED_INBOUND_WORKER_ENABLED`。同时修复干净空库迁移暴露的 Alembic revision 超长问题，所有 revision/down_revision 均不超过默认 `alembic_version.version_num` 的 32 字符限制。当前 PACK2 状态为 `passed_full_stack_backend_startup_rehearsal`，PACK1 仍为 `passed_local_package_runtime_rehearsal_ready`，封版候选更接近可交付；边界仍不变：真实外发关闭，企业渠道暂停，内部 100 题不是客户真实题库，当前不是正式客户验收或准确率签收。

历史长摘要：当前目录已经从阶段 0 骨架推进到 P3-06U-26G4，并继续完成 G5 与 H2 系列本地化运维片段；后续以紧接着的“2026-07-03 最新状态”条为准。阶段 0 最初目标是先跑通：

2026-07-04 最新状态以本条为准：H2W-11 内部演练输入与应用层评估已完成。本轮新增 `scripts/generate_h2w11_internal_rehearsal_inputs.py`，生成内部业务模拟确认回传 `evals/p3_06u_26h2w11m_customer_confirmation_return_received.csv` 和内部 100 条脱敏演练题库 `evals/p3_06u_26h2w11o_real_customer_eval_bank_received.csv`。H2W-11N 当前为 `passed_internal_rehearsal`，内部演练确认 12 条、真实客户确认 0 条；H2W-11O 当前为 `passed_internal_rehearsal`，内部 100 题通过数量、脱敏、期望答案、转人工标签、业务对象和引用来源门禁；H2W-11P 当前 `passed`，内部质量报告候选为 true，但客户质量报告候选为 false，正式签收仍为 false。H2W-FE2、负责人真实登录功能真实性、负责人知识维护试用、本地维护 UI smoke 均通过；H2W-7D 已可读取内部 100 题作为评测输入，但仍因缺 PostgreSQL + pgvector 运行环境保持 `blocked_waiting_for_real_bank_or_postgres`。应用层评估见 `docs/P3-06U-26H2W11_INTERNAL_REHEARSAL_INPUTS_AND_APP_LAYER_REVIEW.md`：当前系统已适合小微企业本地受控试点继续打磨，但不是完全封版的成熟商用客服产品；真实外发、真实 IM、正式电子签章、真实客户原始数据、PostgreSQL + pgvector runtime、完整生产级 RAG、线上回执闭环、安装封版和生产上线仍未完成。

2026-07-04 早前状态：H2W-11L 客户标准答案确认输入包已完成。本轮承接 H2W-11K 的客户质量报告缺口演练证据，生成 `evals/p3_06u_26h2w11l_customer_standard_answer_confirmation_pack.csv`，把 12 条标准答案样本整理为客户/业务负责人可逐项确认的输入包，并标注 7 条已有缺口本地演练证据。新增 `scripts/check_p3_06u_26h2w11l_customer_standard_answer_confirmation_pack.py`、pytest 和阶段文档。H2W-11L 仍明确不是正式客户准确率签收，`customer_confirmed=false`，真实外发继续关闭；正式签收仍需客户真实确认标准答案、真实题库、线上回执、正式报告签收、完整生产级 RAG 和生产上线专项。

2026-07-04 早前状态：H2W-11K 客户质量报告缺口演练证据汇入已完成。本轮把 H2W-11J 的 7 条缺口样本本地演练结果接入客户质量报告：后端 `CustomerQualityReportRead` 新增 `gap_rehearsal_evidence`，质量报告摘要、指标、复盘章节、签收前动作、签收检查项、数据边界和 HTML/XLSX/DOCX 导出件都会展示“缺口演练”证据；前端质量复盘页新增“缺口样本本地演练证据”卡片；新增 `scripts/check_p3_06u_26h2w11k_customer_report_gap_rehearsal.py`、pytest 和阶段文档。H2W-11K 仍明确不是正式客户准确率签收，真实外发继续关闭；正式签收仍需客户确认标准答案、真实题库、线上回执、正式报告签收、完整生产级 RAG 和生产上线专项。

2026-07-04 早前状态：H2W-11I 标准答案缺口评测输入包已完成。本轮新增缺口评测输入包门禁、pytest、阶段文档，并从 H2W-11H 暴露的 6 类缺口来源生成 7 条下一轮评测候选样本和 7 条标签计划，覆盖售后、知识维护、模型成本、引用质量、服务定价和试点签收。H2W-11I 只证明缺口已转成下一轮最终答案评测输入，不代表下一轮评测已经执行，也不是正式准确率签收；真实外发、真实 IM、正式电子签章、合同签收、真实客户原始数据、完整生产级 RAG 和生产上线仍未完成。

2026-07-04 早前状态：H2W-11H 标准答案质量桥接已完成。本轮新增标准答案质量桥接门禁、pytest、阶段文档和桥接报告，把 H2W-11G 客户标准答案模板与 H2W-11B 修复版最终答案标签、引用充分性、禁用承诺和转人工正确性放到同一张来源覆盖表里。当前桥接门禁通过，但正式准确率签收仍为 false：标准答案模板 8 个来源中只有 2 个已出现在当前最终答案标签里，且模板还没有客户确认行，最终答案正文也按脱敏要求不导出。真实外发、真实 IM、正式电子签章、合同签收、真实客户原始数据、完整生产级 RAG 和生产上线仍未完成。

2026-07-04 早前状态：H2W-11G 客户标准答案口径准备已完成。本轮新增客户标准答案模板、H2W-11G 只读门禁、pytest 和阶段文档，用来固定后续“客户标准答案 -> 系统最终回答 -> 人工事实标签 -> 引用充分性 -> 禁用承诺 -> 转人工正确性”的验收口径。H2W-11G 只证明标准答案资料包格式和门禁可用，不是正式客户准确率签收；真实外发、真实 IM、正式电子签章、合同签收、真实客户原始数据、完整生产级 RAG 和生产上线仍未完成。

2026-07-04 早前状态：H2W-11F 前端客户术语、重复入口和知识维护路径收束已完成。本轮把知识库运营页的客户主流程从“客户知识发布闭环 / 转换客户资料 / 预检更新包 / 签收”收束为“知识维护总流程 / 生成资料包 / 检查资料包 / 导入知识库 / 启用前复测 / 启用知识 / 客户确认”，并保持底层仍复用真实预检、导入、发布、评测和质量报告 handler。新增 H2W-11F 静态门禁、pytest 和阶段文档，并复跑 H2W-11E 真实登录浏览器验收与 H2W0 知识操作浏览器门禁。真实外发、真实 IM、正式电子签章、合同签收、真实客户原始数据、完整生产级 RAG 和生产上线仍未完成。

2026-07-04 早前状态：H2W-11 受控试点演练前置门禁第一片已完成。新增 `scripts/check_p3_06u_26h2w11_rehearsal_preflight.py` 和 `docs/P3-06U-26H2W11_REHEARSAL_PREFLIGHT_FIRST_SLICE.md`，把 62 条客户式脱敏题库、7 份客户知识包模板、质量报告/签收脚本、本地维护闭环证据和 H2W-8B 浏览器验收证据放入同一前置门禁。验证结果为 `status=ready_for_h2w11_preflight_rehearsal`、`ready=true`、`blockers=[]`；题库 62 题、敏感行 0、知识包来源 URI 覆盖 7/7、本地维护总账 `ready_for_rehearsal`。当前警告是 62 题客户式题库没有 `expected_answer` 字段，正式签收前仍需采集最终客服答案样本或客户标准口径。真实外发、真实 IM、RPA 正式交付、完整生产级 RAG、供应商账单对账、正式客户数据和完整 H2W-11 负责人真实登录端到端 rehearsal 仍未完成。

2026-07-04 早前状态：H2W-8B 本地维护闭环就绪度和浏览器逐按钮验收已完成。H2W-8A 已完成空库首次启动、首任负责人创建、创建后入口锁定、网页端无身份重置关闭、无默认密码和危险开关门禁；H2W-8B 新增 `GET /api/tenants/{tenant_id}/local-maintenance/readiness`，以 `updates.manage` 权限读取诊断接收、售后处理单、签名更新包、本地备份、恢复演练和审计事件，输出 `p3-06u-26h2w8b.local_maintenance_readiness.v1` 就绪度总账。前端“账号与本地维护”页新增“本地维护闭环”摘要卡，显示接收、更新计划、更新包、已验备份、恢复演练、核心门禁、阻断项和下一步补证据动作；维护动作完成后会刷新总账。本轮新增浏览器门禁 `scripts/check_p3_06u_26h2w8b_local_maintenance_ui.mjs`，使用临时 SQLite、临时 Chrome profile 和真实登录表单，在页面内完成授权上传包登记、售后处理单生成、签名更新包预检/暂存、本地备份创建/校验、恢复演练和受控更新计划生成，并验证前端摘要卡与后端总账均进入 `ready_for_rehearsal`。验证已通过 H2W-8A/H2W-8B 静态门禁、H2W-8B UI smoke、相邻回归 `29 passed`、后端全量 `248 passed`、`backend/.venv/bin/python -m compileall backend/app`、前端 `npm run typecheck` 和 `npm run build`。真实外发、真实 IM、RPA 正式交付、完整生产级 RAG、供应商账单对账和 50-100 条真实题库 rehearsal 仍未完成。

2026-07-04 早前状态：H2W 后续推进已从线性 `7B -> 7C -> 7D` 改为网状工程推进，并完成 H2W-N0/H2W-7X/H2W-7B/H2W-7C 第一片。新增 `docs/P3-06U-26H2W_NETWORKED_ENGINEERING_MASTER_PLAN.md`，明确真实外发继续关闭、RPA 只保留 draft-only 研究线、后续必须按事实账本推进。后端新增回复事实账本最小骨架：`reply_decisions.provenance_id`、`model_call_records`、`reply_citation_snapshots`、`reply_provenance` 服务、迁移 `0031_h2w7x_reply_provenance_records.py`；回复决策和回复编排器都会写入 `provenance_id`、引用快照和模型调用记录，RAG/成本治理摘要改为读取真实 `model_call_records`，不再从 `decision_payload` 猜测模型调用。H2W-7B 已新增模型预算门禁与成本估算配置、`model_budget` 服务、`budget_blocked`/`degraded` 状态、自动路由预算超限降级到确定性知识草稿、显式 provider 超预算不静默 fallback；被预算拦截或降级时真实 `estimated_cost` 记为 0，外部模型预计费用只进入 `budget_policy_snapshot`。H2W-7C 第一片已把最终客服答案样本写入 `reply_citation_snapshots`，RAG 治理摘要新增 `answer_quality` 和 `final_answer_quality` 门禁，覆盖最终答案质量、引用充分性、禁用承诺和转人工正确性；当前口径仍不是完整线上准确率。验证已通过 `python3 scripts/check_p3_06u_26h2w7c_answer_quality_governance.py`、`python3 scripts/check_p3_06u_26h2w7b_model_cost_budget_gate.py`、`python3 scripts/check_p3_06u_26h2w7x_reply_provenance.py`、`python3 scripts/check_p3_06u_26h2w7_rag_cost_governance.py`、相关后端测试、关键后端文件 `py_compile`、前端 `npm run typecheck` 和 `npm run build`。本片不是完整 H2W-7D/11：生产级向量库、真实渠道外发、供应商账单对账和 50-100 条真实题库 rehearsal 仍未完成。

2026-07-03 早前状态：P3-06U-26H2W6A 已完成本地更新恢复处理单第一片。后端新增 `diagnostic_remediation_requests` 表和处理单接口，可把通过校验的售后接收记录转换为处理单，支持列表、状态更新和回传包下载；拒收记录不能生成处理单。前端“管理运维 -> 账号安全 -> 售后接收台”新增“处理回传包”区域，已接收诊断包可生成处理单、标记待客户确认并下载 JSON 回传包。新增 `docs/P3-06U-26H2W6_REMEDIATION_GATE_FIRST_SLICE.md` 和 `scripts/check_p3_06u_26h2w6_remediation_static.py`，并更新 `docs/FRONTEND_FUNCTION_REALITY_MATRIX.md`。本片不是完整自动更新器；不自动上传、不远控客户电脑、不静默更新、不打开真实外发、不调用模型、不替客户执行程序更新、恢复或回滚。

2026-07-03 早前状态：P3-06U-26H2W5 已完成云接收台第一片。后端新增 `diagnostic_intake_records` 表和诊断授权上传包接收接口，支持登记、校验、拒收原因、列表、状态更新和下载；接收时校验客户主动授权、上传包版本、安全声明和诊断包 sha256。前端“管理运维 -> 账号安全”新增“售后接收台”，可粘贴客户主动提供的授权上传包 JSON、登记接收、查看记录、下载包并标记处理状态。新增 `docs/P3-06U-26H2W5_CLOUD_INTAKE_FIRST_SLICE.md` 和 `scripts/check_p3_06u_26h2w5_cloud_intake_static.py`，并更新 `docs/FRONTEND_FUNCTION_REALITY_MATRIX.md`。本片是本地模拟接收台，不是正式云服务上线；不自动上传、不远控客户电脑、不打开真实外发、不调用模型、不替客户执行更新恢复。

2026-07-03 早前状态：P3-06U-26H2W4 已完成报告导出与归档第一片。客户质量报告导出从 HTML 扩展到 HTML/XLSX/DOCX，后端生成有效 OpenXML XLSX/DOCX 文件并把导出文件写入 `customer_quality_report.exported` 审计归档；新增报告归档列表与历史下载接口。前端质量复盘页新增 `HTML 留档`、`XLSX 明细`、`DOCX 报告` 三个导出按钮和“报告归档”列表，历史下载走真实接口。新增 `docs/P3-06U-26H2W4_REPORT_EXPORTS_AND_ARCHIVE_FIRST_SLICE.md` 和 `scripts/check_p3_06u_26h2w4_report_exports.py`，并更新 `docs/FRONTEND_FUNCTION_REALITY_MATRIX.md`。本片不做 PDF、不接正式电子签章、不打开真实外发、不调用模型、不保存原始客户问题/完整回复/人工备注原文；本地确认和归档不是正式电子签章。

2026-07-03 早前状态：P3-06U-26H2W3D 已完成线上回执与准确率闭环第一片。后端新增 `GET /api/tenants/{tenant_id}/online-receipt-quality-summary`，按租户汇总回执入库、发送尝试匹配、签名验证、送达/已读、失败复盘、平台分布和验收门禁；前端质量诊断页新增“线上回执闭环证据”区域，明确当前是回执链路覆盖，不是完整客服答案准确率。新增 `docs/P3-06U-26H2W3D_ONLINE_RECEIPT_ACCURACY_LOOP_FIRST_SLICE.md`、`scripts/check_p3_06u_26h2w3d_online_receipt_quality.py` 和 `scripts/check_p3_06u_26h2w3d_online_receipt_quality_ui.mjs`，并更新 `docs/FRONTEND_FUNCTION_REALITY_MATRIX.md`。本轮通过 H2W3D 静态门禁、后端单测、前端 typecheck/build、桌面浏览器 smoke，以及 H2W3C/H2W3B/P3-06U-26D 相邻门禁；浏览器证据位于 `output/p3_06u_26h2w3d_online_receipt_quality_ui/`。真实外发继续关闭，不接真实官方渠道，不调用模型，不返回回执原始 payload，不展示完整线上准确率；完整客服答案准确率仍需真实客户题库、最终回复样本、人工事实标签、官方授权渠道、真实平台回执和持续回归闭环。

2026-07-03 早前状态：P3-06U-26H2W3C 已完成客户资料导入模板与预检第一片。知识库运营页新增“客户资料导入助手”，支持把客户按模板整理的 CSV 资料转换为 `wanfa.knowledge_update_package.v1` 标准知识更新包，再复用现有“预检差异”和“导入更新”链路；模板覆盖业务对象、标准问答、流程政策、禁用承诺、转人工规则、回归问题和期望答案。新增 `docs/P3-06U-26H2W3C_CUSTOMER_KNOWLEDGE_INTAKE_TEMPLATE.md` 和 `scripts/check_p3_06u_26h2w3c_customer_knowledge_intake.py`，并更新 `docs/FRONTEND_FUNCTION_REALITY_MATRIX.md`、`docs/PRODUCTIZATION_MASTER_PLAN_LITE_AND_STANDARD.md`。本轮通过 H2W3C/H2W3B/H2W2/H2W1/P3-06U-07/P3-06U-26D 静态门禁、前端 typecheck/build；当前 PDF、DOCX、XLSX 原件只作为来源留档，不自动解析入库。自动联网上传、我方云端接收台、真实程序更新器、在线覆盖恢复、程序文件替换、服务重启、数据库迁移、模型调用和真实外部平台写入仍未开放；完整线上客服准确率仍需真实题库、最终回复样本、人工事实标签、线上回执和持续回归闭环；真实外发继续关闭，RPA 仍只作为内部研究归档。

2026-07-03 早前状态：P3-06U-26H2U 已完成客户签收记录列表第一片；后端新增客户质量报告签收记录列表接口，前端质量复盘页新增“最近确认记录”列表，负责人账号可查看最近客户确认状态、确认方式、脱敏签收人、备注摘要状态和审计编号。H2U 已通过知识评测 API 单测、相关后端回归、前端 typecheck/build、前端 build 和浏览器客户签收记录列表 smoke；证据目录为 `output/p3_06u_26h2u_customer_report_signoff_list_ui/`。H2T 已完成客户签收记录第一片，H2S 已完成客户报告 HTML 导出，H2R 已完成最终回复样本与人工标签 CSV 导入导出第一片，H2Q 已完成客户可读质量报告第一片，H2P 已完成最终回复采样与批量人工标签第一片，H2O 已完成真实客户题库导入第一片，H2N 已完成人工事实性标签入口第一片，H2M 已完成只读月度质量复盘包，H2L 已完成本地恢复工具 dry-run，H2K 已完成客户授权诊断上传包，H2J 已完成签名程序更新包 dry-run 演练计划，H2I 已完成签名策略更新包应用与回滚，H2H 已完成本地 SQLite 物理备份与校验，H2G 已完成签名知识更新包应用与按导入批次回滚，H2F 已完成签名更新包暂存，H2E 已完成签名更新包预检，H2D 已完成知识更新包导入，H2C 已完成本地诊断包生成，H2B 已完成本地账号治理，H1 已完成本地首次启动负责人和知识更新入口。

2026-07-01 历史状态：P3-06S-01 已完成窄桌面壳层滚动修复，900px 小窗口保持左侧导航固定、右侧工作区独立滚动。后续已由 P3-06T-01/P3-06T-02 继续返修和收紧口径，当前下一步以最新 P3-06T 状态为准。

2026-07-01 追加状态：P3-06T-01 已完成壳层滚动返修验收。760px 小窗口已从整页滚动修复为左侧导航固定、右侧工作区独立滚动；721px 是新的中台壳层下限，720px 及以下按手机/窄屏自然滚动处理。验证脚本：`scripts/check_p3_06t_layout_scroll.mjs`；证据目录：`output/p3_06t_layout_after/`。下一步进入 P3-06T-02 首页数据口径收紧。

2026-07-01 追加状态：P3-06T-02 已完成首页数据口径收紧。后端 dashboard 响应新增契约版本、聚合粒度、刷新模型、源表、敏感字段排除和口径备注；前端时间范围/渠道筛选正式接入服务端聚合刷新，演示模式仍明确显示本地汇总。随后已进入并完成 P3-06T-03 运营总览 BI 重做。

2026-07-01 追加状态：P3-06T-03 已完成运营总览 BI 重做。首页升级为运营指挥舱，包含经营信号条、运营健康环、风险组成、压力趋势主图、优先动作、处理漏斗、渠道矩阵和质量诊断；新增 `scripts/check_p3_06t_03_bi_overview.mjs`，1440、1280、900、390 视口截图验收通过。用户复审后确认前端距离完善仍较远，真实实用成熟度按 6.0/10 起算；下一步进入 P3-06U 前后端契约对齐与实用型前端产品化优化。

2026-07-01 追加状态：P3-06U-01 已完成前后端契约与页面路径盘点第一片。新增 `docs/P3-06U-01_FRONTEND_BACKEND_CONTRACT_MATRIX.md` 和 `scripts/check_p3_06u_01_contract_alignment.py`，覆盖核心工作区的路由、API、权限、状态、审计和缺口；前端导航已去掉客户可见的工程阶段标识，下一步进入 P3-06U-02 角色化任务路径重排，再推进 P3-06U-03 接待工作台实用性重构。

2026-07-01 追加状态：P3-06U-02 已完成角色化任务路径重排。新增 `RoleTaskPath`、`roleTaskPaths`、`getRoleTaskPathsForRoles()` 和顶部“今日任务路径”条，owner/admin/agent/viewer 登录后优先看到与岗位匹配的 3-5 条任务路径和实时待办数字；新增 `docs/P3-06U-02_ROLE_TASK_PATHS.md`、`scripts/check_p3_06u_02_role_task_paths.py`、`scripts/check_p3_06u_02_role_task_paths.mjs`；随后已继续完成 P3-06U-03。

2026-07-01 追加状态：P3-06U-03 已完成接待工作台实用性重构。`#live` 已从 `App.tsx` 旧内联实现拆到 `frontend/src/components/conversation/ConversationWorkbenchPanel.tsx`，并重构为会话队列、消息处理区、右侧上下文三栏 IM 工作台；页面明确区分“批准进入待发送”和“真实外发关闭”，桌面首屏可看到三栏主体。新增 `docs/P3-06U-03_CONVERSATION_WORKBENCH_RESTRUCTURE.md`、`scripts/check_p3_06u_03_conversation_workbench.py`、`scripts/check_p3_06u_03_conversation_workbench.mjs`；随后已继续完成 P3-06U-04。

2026-07-01 追加状态：P3-06U-04 已完成运营总览到处理路径打通。首页优先动作和关键指标现在会携带 `from=overview`、任务、时间窗口、渠道和目标状态进入接待工作台、待发送、知识缺口和渠道异常页；目标页展示上下文提示，并自动应用对应队列/状态筛选。新增 `docs/P3-06U-04_OVERVIEW_TO_ACTION_PATHS.md`、`scripts/check_p3_06u_04_overview_action_paths.py`、`scripts/check_p3_06u_04_overview_action_paths.mjs`，静态、构建和浏览器多视口验收通过。随后已继续完成 P3-06U-05。

2026-07-01 追加状态：P3-06U-05 已完成真实登录角色 smoke。新增 `docs/P3-06U-05_REAL_LOGIN_ROLE_SMOKE.md`、`scripts/check_p3_06u_05_real_login_role_smoke.py`、`scripts/check_p3_06u_05_real_login_role_smoke.mjs`；使用临时租户和真实账号登录 owner/admin/agent/viewer，验证默认入口、可见导航、任务路径、禁用动作说明、受限路径回退、退出清令牌和无意外 403。截图与摘要在 `output/p3_06u_role_smoke/`。下一步进入 P3-06U-06 质量复盘 BI。

2026-07-01 追加状态：P3-06U-06 已完成质量复盘 BI 与知识修复闭环。新增 `docs/P3-06U-06_QUALITY_BI_REPAIR_LOOP.md`、`scripts/check_p3_06u_06_quality_bi.py`、`scripts/check_p3_06u_06_quality_bi.mjs`；质量页新增修复闭环分数、六类修复路径、`from=quality` 上下文跳转和“来自质量复盘”的目标页提示。浏览器 smoke 覆盖 1440、900、390 视口，截图与摘要在 `output/p3_06u_06_quality_bi/`。下一步进入 P3-06U-07 知识运营台产品化。

2026-07-01 追加状态：P3-06U-07 已完成知识运营台产品化第一片。新增 `docs/P3-06U-07_KNOWLEDGE_OPS_PRODUCTIZATION.md`、`scripts/check_p3_06u_07_knowledge_ops.py`、`scripts/check_p3_06u_07_knowledge_ops.mjs`；知识运营、知识缺口和知识评测页顶部统一展示知识运营流程，支持 `from=knowledge` 上下文跳转、发布前回归门禁、回归影响预估、版本与审核状态，以及知识草稿编辑清单。浏览器 smoke 覆盖 1440、900、390 视口，截图与摘要在 `output/p3_06u_07_knowledge_ops/`。下一步进入 P3-06U-08 渠道连接器中心实用化。

2026-07-01 追加状态：P3-06U-08 已完成渠道连接器中心实用化。新增 `docs/P3-06U-08_CHANNEL_CONNECTOR_CENTER_PRODUCTIZATION.md`、`scripts/check_p3_06u_08_channel_connector_center.py`、`scripts/check_p3_06u_08_channel_connector_center.mjs`；`#channels` 第一屏新增渠道接入状态中心，企业微信/微信客服展示 10 步接入状态，Token 和 EncodingAESKey 只显示 secret 引用，公众号、抖音/抖店、小红书、淘宝/天猫、京东/拼多多只展示官方授权前置条件和未接入状态。浏览器 smoke 覆盖 1440、900、390 视口，截图与摘要在 `output/p3_06u_08_channel_connector_center/`。下一步进入 P3-06U-09 前端状态体系统一。

2026-07-01 追加状态：P3-06U-09 已完成前端状态体系统一。新增 `docs/P3-06U-09_FRONTEND_STATE_SYSTEM.md`、`scripts/check_p3_06u_09_unified_states.py`、`scripts/check_p3_06u_09_unified_states.mjs`；新增 `WorkspaceStateNotice`、`PanelStateNotice`、`DataSourceBadge`、`DisabledReason` 和顶部 `WorkspaceRuntimeStateStrip`，核心页面统一展示演示样本、真实服务端数据、配置缺失、接口失败、暂无数据、无权限和真实外发关闭。浏览器 smoke 覆盖 1440 和 390 视口，逐页检查总览、对话台、人工审核、知识、缺口、评测、质量、待发送、渠道和运维，截图与摘要在 `output/p3_06u_09_unified_states/`。下一步进入 P3-06U-10 前端组件和状态结构拆分。

2026-07-01 追加状态：P3-06U-10 第一片已完成前端状态组件抽离。新增 `frontend/src/components/common/WorkspaceState.tsx`、`docs/P3-06U-10_FRONTEND_STATE_COMPONENT_EXTRACTION.md`、`scripts/check_p3_06u_10_state_component_extraction.py`；`App.tsx` 不再定义统一状态组件，改为导入通用组件。P3-06U-01 到 P3-06U-10 静态检查、`npm run typecheck`、`npm run build` 和 Chrome CDP 状态体系 smoke 均通过。下一步继续 P3-06U-10 第二片，优先拆知识、质量、渠道或运维页面组件。

- FastAPI 后端空服务。
- React/Vite 运营后台空壳。
- PostgreSQL + Redis 本地开发依赖。
- Alembic 数据库迁移骨架。
- 标准题集和评测配置占位。
- Stage 0 文件结构自检。

## 目录

```text
standard_ops/
  backend/       FastAPI 后端
  frontend/      React/Vite 运营后台
  deploy/        Docker Compose 和部署入口
  docs/          工程参考文档
  evals/         标准题集和评测配置
  scripts/       阶段自检脚本
```

## 客户本地试点启动

客户或试点机器上先复制客户环境模板：

```bash
cd standard_ops
cp deploy/customer.env.example deploy/customer.env
```

然后把 `deploy/customer.env` 里的 `STANDARD_OPS_POSTGRES_PASSWORD` 和 `DATABASE_URL` 模板密码替换为客户本地随机密码。Docker Desktop 已安装并启动后运行：

```bash
deploy/start-local-pilot.sh deploy/customer.env
```

脚本会先执行安全门禁和数据库迁移，再启动核心服务。默认不会启动入站 worker，也不会打开真实外发。

客户本地试点默认地址：

- 前端：http://127.0.0.1:5173
- 后端：http://127.0.0.1:8000/health

如果本机已有 MaxKB 或其他服务占用 8080，不需要关闭它；标准运营版后端容器映射到宿主机 `8000`。

开发环境仍可使用普通 compose 或手动后端启动，但不能把开发命令当作客户交付入口。

本地手动开发时，也建议后端固定跑在 `8000`：

```bash
cd standard_ops/backend
. .venv/bin/activate
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

本阶段只承诺骨架。真实模型密钥、平台授权和生产域名不写入仓库。

## 阶段 0 自检

```bash
python3 standard_ops/scripts/check_stage0_scaffold.py
```

看到 `PASS stage0 scaffold` 表示文件结构满足阶段 0 要求。

## 阶段 1 基础 API

阶段 1 基础 API 已落地：

| 能力 | 接口 |
| --- | --- |
| 登录换取会话令牌 | `POST /api/auth/login` |
| 当前身份 | `GET /api/auth/me` |
| 创建租户 | `POST /api/tenants` |
| 租户列表 | `GET /api/tenants` |
| 创建坐席用户 | `POST /api/tenants/{tenant_id}/users` |
| 坐席用户列表 | `GET /api/tenants/{tenant_id}/users` |
| 创建角色 | `POST /api/tenants/{tenant_id}/roles` |
| 角色列表 | `GET /api/tenants/{tenant_id}/roles` |
| 给用户分配角色 | `POST /api/users/{user_id}/roles` |
| 创建团队 | `POST /api/tenants/{tenant_id}/teams` |
| 团队列表 | `GET /api/tenants/{tenant_id}/teams` |
| 加入团队成员 | `POST /api/teams/{team_id}/members` |
| 创建渠道 | `POST /api/tenants/{tenant_id}/channels` |
| 渠道列表 | `GET /api/tenants/{tenant_id}/channels` |
| 创建联系人 | `POST /api/tenants/{tenant_id}/contacts` |
| 联系人列表 | `GET /api/tenants/{tenant_id}/contacts` |
| 创建会话 | `POST /api/tenants/{tenant_id}/conversations` |
| 会话列表 | `GET /api/tenants/{tenant_id}/conversations` |
| 会话详情 | `GET /api/conversations/{conversation_id}` |
| 写入消息 | `POST /api/conversations/{conversation_id}/messages` |
| 审计事件列表 | `GET /api/tenants/{tenant_id}/audit-events` |

认证与权限边界：

- 登录接口需要 `tenant_slug + email + password`。
- 前端已提供正式登录页，登录成功后保存 bearer token；退出时清理本地 token。
- 会话令牌只在响应中返回一次，数据库仅保存哈希。
- 审计事件列表需要有效 Bearer token，且当前用户角色必须是 `owner` 或 `admin`。
- 当前 `/api/auth/me` 无 token 时仍返回开发演示身份，方便本地预览；正式受保护接口不接受这个演示身份。
- 用户、角色、团队管理已开始纳入权限保护：初始化后需要 `owner` 或 `admin`。

## 开源参考转化

- `docs/OPEN_SOURCE_AGENT_FRAMEWORK_REFERENCE_FOR_STANDARD_OPS.md`：将 Project_022 的 LangGraph、Scrapling、AstrBot 源码级解读转成标准运营版可执行参考。结论是学习状态图/checkpoint、授权采集、运行时 manager 边界，但不直接复制 AGPL 代码，不使用绕过风控的采集能力。
- `docs/ASTRBOT_CHANNEL_ARCHITECTURE_REFERENCE_FOR_CUSTOMER_SERVICE.md`：专门解读 AstrBot 多平台接入架构，转化为自研客服中台的渠道连接器、统一消息、outbox、模型路由、企微/公众号/抖音/电商平台接入边界和 clean-room 重写路线。
- `docs/SAG_vs_RAG智能客服知识库融入方案_2026-06-26.md`：专门把 SAG/RAG 跑分报告转成智能客服知识库方案。结论是 SAG-like semantic event layer 只作为复杂知识检索增强层，不替代客服中台、FAQ、文档 RAG、模型路由、人审、outbox 或渠道连接器。
- Project_022 输出 `/Users/ericlee/Desktop/Workspace/Project_022_开源爬虫与Agent框架研究/outputs/Project_012结合Scrapling与AstrBot工程判断_2026-06-25.md` 可作为补充判断：下一步优先 `P2 轻量 workflow/checkpoint`，再做 `P3 授权知识采集/RAG v1`，最后推进 `P4 ProviderManager/ChannelManager`。

## 产品化资料包

2026-06-29 起，标准运营版后续推进按“两条产品线 + 四类交付资料”执行：

- `docs/PRODUCTIZATION_MASTER_PLAN_LITE_AND_STANDARD.md`：Lite 试点版与标准运营版的产品化总控计划，包含功能边界、完成标准、工程阶段、客户资料和内部运维体系。
- `docs/customer/万法常世AI智能客服系统_客户使用手册.md`：面向使用团队的日常操作说明，覆盖登录、待办、AI 草稿审核、知识库更新、质量复盘和上线准备。
- `docs/customer/万法常世AI智能客服系统_产品介绍.md`：面向采购方和业务负责人的产品介绍，覆盖定位、场景、能力、版本和安全边界。
- `docs/customer/万法常世AI智能客服系统_服务体系介绍.md`：面向项目负责人和售后负责人的服务体系说明，覆盖实施、培训、运维、质量复盘和故障响应。
- `docs/internal/万法常世AI智能客服系统_内部售后运营维护计划.md`：内部售后 SOP，覆盖销售交付交接、远程维护、诊断包、准确率下降排查、知识更新、故障分级和运维成本。

这些文档是后续 P3-05 试点部署包、Lite 试点版封版和标准运营版封版的总入口。对外资料后续可转成 Word/PDF；内部运维文档不得直接发送给客户。

## P3-05A 试点部署准备

P3-05A 已把部署准备、运维边界和客户资料包整理为可执行入口：

- `docs/P3-05_PILOT_DEPLOYMENT_READINESS.md`：试点部署准备、环境变量、备份恢复、诊断包、远程维护、准确率下降和外发边界。
- `scripts/check_p3_05_deployment_readiness.py`：只读检查 P3-05A 必备文件、环境模板、Compose 服务、迁移数量和外发默认关闭状态。
- `scripts/create_p3_05_diagnostic_bundle.py`：生成不含 `.env` 明文、不含密钥、不含客户聊天原文的诊断包摘要。

常用命令：

```bash
cd /Users/ericlee/Desktop/肥肥lu/lite_a_customer_service/standard_ops
.venv/bin/python scripts/check_p3_05_deployment_readiness.py
.venv/bin/python scripts/create_p3_05_diagnostic_bundle.py
```

P3-05A 不代表真实客户环境已经部署完成，也不代表真实外发、真实官方渠道和真实模型批量质量验收已经打开。生产或客户环境动作仍需要客户授权、备份、回滚点和单独验收。

阶段 1 自检：

```bash
python3 standard_ops/scripts/check_stage1_foundation.py
cd standard_ops/backend
. .venv/bin/activate
pytest
```

## 当前前端产品化状态：P3-06U-26H2V

截至 2026-07-03，`#live` 多渠道对话台已从三栏管理看板收束为更贴近日常客服 IM 的双栏接待台，并进一步调整为“AI 先生成回复建议，异常才人工接管”的产品逻辑；知识运营页已新增业务对象知识库第一片：

- 左侧为更窄的会话列表和队列筛选。
- 右侧为大面积对话流、AI 回复建议记录和异常转人工接管区。
- 客户、平台账号/店铺、AI 决策和知识依据压缩到会话头部、消息流和回复区，不再做多块常驻大卡。
- 各平台消息后续都进入统一会话/消息存储；前端只展示汇聚后的会话记录。
- 回复区改为“AI 回复建议 / 转人工提醒”，普通会话不再要求逐条人工审核；真实外发仍关闭。
- 顶部大型信号条和顶部 8 个队列卡已移除。
- 真实外发关闭、知识缺失、异常转人工和官方渠道授权边界仍保留；发送队列和审核门禁作为后端能力保留，不再压到普通坐席首屏。
- P3-06U-19 已把“商品学习”抽象成业务对象知识库，后端新增业务对象、别名、对象问答卡和导入批次表，前端知识运营页可维护商品、服务、套餐等对象及对应问答卡。
- P3-06U-20 已新增自动回复策略状态机第一片，后端可把入站消息评估为可自动回复、人工门禁、知识缺口或策略阻断，并把决策、草稿、命中词和外发门禁写入 `reply_decisions`；知识运营页新增状态机说明卡。
- P3-06U-21 已把 `reply_decisions` 接入可信入站 worker：可信消息先落回复决策，再按状态同步知识缺口、创建人审任务或进入 outbox 前置门禁；仍不写出站草稿和真实发送任务。
- P3-06U-22 已把最新 `reply_decision` 展示到接待工作台：多平台对话台现在能直观看到回复决策、业务对象、知识依据、下一步和真实外发边界。
- P3-06U-23 已新增 `?demo=1#live` 演示直达入口，并在多渠道对话台展示平台、账号、店铺 / 入口、接入状态和回复模式；演示样本覆盖微信客服、抖音、淘宝、京东、拼多多和官网。
- P3-06U-24 已把知识库运营、知识缺口、知识评测三个入口的首屏职责切开；新增 `channel_accounts` 后端模型、迁移、读写接口和前端只读映射，让多渠道对话台具备从服务端读取平台账号 / 店铺 / 入口身份的基础。
- P3-06U-25 已完成客服中台综合成熟度评分：完整商用全渠道口径为 `58/100`，受控试点口径为 `72/100`；当前知识评测仍定义为检索评测，不包装成完整客服准确率。
- P3-06U-26 已新增工程优化总纲，明确后续 P3-06U-26A 到 P3-06U-26H 的施工顺序、验收命令、停止条件和真实外发边界。
- P3-06U-26A 已完成对外界面去演示味：前端客户可见源码不再出现“演示模式 / 演示样本 / 开发演示身份 / 开发演示进入”等内部口径，统一改为“预览工作区 / 样例数据 / 测试账号进入”等分层表达，同时继续保留“真实外发关闭”。
- P3-06U-26B 已完成多渠道对话台微信式收束：左侧会话列表继续收窄，右侧平台来源和回复决策压缩为一条上下文条，消息流上移，AI 建议移动到回复区附近；当前主线已统一为桌面中台形态，后续不再验收手机端自然单列。
- P3-06U-26C 已完成渠道账号/店铺配置面板：渠道接入页新增服务端 `channel_accounts` 清单、配置缺失空状态、刷新动作和新增/更新表单；前端接入 `GET /api/tenants/{tenant_id}/channels`、`GET /api/tenants/{tenant_id}/channel-accounts` 与 `POST /api/channels/{channel_id}/channel-accounts`，保存后回刷对话台渠道身份；真实外发继续关闭。
- P3-06U-26D 已完成知识三页分叉与服务端数据深化：新增 `KnowledgeWorkspacePage` 页面壳，知识库运营、知识缺口、知识评测分别展示独立首屏、核心指标、空状态和服务端数据边界；知识缺口新增错因地图，知识评测新增发布前后对比入口，并明确当前知识评测是检索评测，不是完整客服准确率。
- P3-06U-26E 已完成客服答案质量评测第一片：后端评测运行摘要新增 `answer_quality_metrics_version=p3_06u_26e_customer_service_answer_quality_v1`、引用充分率、禁用承诺违规率和转人工正确性；前端知识评测页新增“客服答案质量门禁”和逐题质量标签。当前最终答案事实性明确标记为“未评”，不生成最终客服答案、不调用模型、不外发，也不把检索命中率包装成完整客服准确率。
- P3-06U-26F 已完成真实客户题库与知识包导入模板第一片：新增 `p3_06u_26f_real_customer_eval_bank_template.csv` 和 `p3_06u_26f_real_customer_knowledge_package_template.json`；导入脚本兼容 `customer_question`、`expected_answer`、`business_object`、`must_include`、`must_not_include`、`handoff_expected` 和 `source_reference` 等客户交付字段，并只把 `expected_answer` / `business_object` 做 hash 处理，不写入摘要原文。
- P3-06U-26G 已完成渠道官方 sandbox 优先级和 RPA draft-only 研究边界固化：渠道接入页新增“官方 sandbox 优先级”矩阵，RPA Lab 新增 `draft-only` 硬边界；RPA 不进入正式默认交付链，真实外发继续关闭。
- P3-06U-26G1 已完成桌面中台模式收口：应用壳层最小宽度固定为 1180px，移除手机/移动端媒体块，当前主线浏览器验收改为 1440、1280、1180 三个桌面视口；旧手机/390 视口记录仅作为历史归档。
- P3-06U-26G2 已完成接待工作台自动回复优先收束：多渠道对话台左侧只暴露“全部 / 我的 / 转人工”，右侧保留大面积消息流和底部自动回复记录；普通会话默认 AI 自动接待，低置信、无知识、高风险、超时或渠道异常才进入转人工。当前验收只跑桌面视口，不做移动端。
- P3-06U-26G3 已完成总览页尾部重复模块清理：运营总览不再展示“人工池快照”、待人工审核、待发送确认、工单超时、发送失败等队列入口；这些能力继续留在工作台、后台队列、outbox、失败复盘和运维闭环里，总览页只保留高层 BI 与优先处置提示。
- P3-06U-26G4 已完成知识运营前后端对齐与去重审验：知识库运营、知识缺口、知识评测三页移除共享 `KnowledgeOperationsFlowPanel` 和页头跳转式假动作，保留各自真实操作面板；新增专项审验文档和回归脚本，明确当前知识评测是检索评测，不是完整客服准确率。
- P3-06U-26G5 已完成小微企业本地化使用收束：RPA 副驾驶实验室从侧边栏和主路由下线，知识缺口搜索、状态、严重度、来源和分页改为服务端筛选；新增本地首次启动账号、诊断包、签名更新包和知识库远程修复路线文档。
- P3-06U-26H2B 到 H2L 已把本地化运维链路推进为：首启负责人、账号治理、只读诊断包、客户授权诊断上传包、知识更新包导入、签名更新包预检、签名更新包暂存、签名知识包应用与回滚、本地 SQLite 物理备份与校验、签名策略包应用与回滚、签名程序包 dry-run 演练计划、本地恢复工具 dry-run。当前更新中心可应用知识包和策略包；程序包只生成演练计划，继续阻断真实应用；诊断上传包仍需客户手动传输；恢复工具只生成演练计划，不做在线覆盖恢复。
- P3-06U-26H2H 已新增本地 SQLite 物理备份与校验第一片，更新中心前可创建本地备份点并校验 sha256 与 SQLite integrity_check；当前仍不做在线覆盖恢复。
- P3-06U-26H2I 已新增签名策略更新包应用与回滚第一片，`strategy` 包可写入 `tenant_reply_strategies` 并影响后续回复决策；已通过浏览器冒烟，证据目录为 `output/p3_06u_26h2i_signed_strategy_update_ui/`；程序包仍继续阻断。
- P3-06U-26H2J 已新增签名程序更新包 dry-run 演练计划第一片，`program` 包可生成目标版本、维护窗口、计划步骤、健康检查和阻断动作；已通过浏览器冒烟，证据目录为 `output/p3_06u_26h2j_program_update_dry_run_ui/`；当前仍不替换程序文件、不迁移数据库、不重启服务、不执行真实程序升级。
- P3-06U-26H2K 已新增客户授权诊断上传包第一片，管理运维页可下载带授权回执和脱敏诊断包摘要的 `wanfa-diagnostic-upload-*.json`；已通过浏览器冒烟，证据目录为 `output/p3_06u_26h2k_diagnostic_upload_package_ui/`；当前不自动联网、不上传到我方服务器、不做定期上传。
- P3-06U-26H2L 已新增本地恢复工具 dry-run 第一片，管理运维页可在本地备份点上生成恢复演练计划；已通过浏览器冒烟，证据目录为 `output/p3_06u_26h2l_local_restore_dry_run_ui/`；当前不覆盖数据库、不停服务、不替换文件、不执行迁移。
- P3-06U-26H2M 已新增月度质量复盘包第一片，质量复盘页从服务端读取本月复盘指标、主要错因和下一步动作；已通过浏览器冒烟，证据目录为 `output/p3_06u_26h2m_monthly_quality_review_ui/`；当前不调用模型、不输出客户原文、不把检索命中包装成完整客服准确率。
- P3-06U-26H2N 已新增人工事实性标签入口第一片，知识评测详情可对单题标注事实正确、部分正确、事实有误或应转人工；标注结果会更新评测运行摘要和本月质量复盘包。证据目录为 `output/p3_06u_26h2n_factuality_label_ui/`；当前仍不代表真实 50-100 题库验收或完整客服最终答案准确率。
- P3-06U-26H2O 已新增真实客户题库导入第一片，客户脱敏 50-100 题题库包可先预检题量、敏感信息、渠道分布、风险分布、引用覆盖和转人工样本，再导入为正式客服质量评测集；不调用模型、不外发，接口摘要和审计事件不回显原始问题。
- P3-06U-26H2P 已新增最终回复采样与批量人工标签第一片，知识评测详情可逐题保存最终客服回复样本，并对已采样题批量标注事实正确或应转人工；样本进入运行摘要和月度质量复盘，审计不保存样本文本或人工备注明文。
- P3-06U-26H2Q 已新增客户可读质量报告第一片，质量复盘页可展示客户质量报告，汇总题库规模、最终回复采样、人工事实性、引用覆盖、知识缺口、报告可信度和签收边界；不展示原始问题、完整回复、人工备注明文、密钥或渠道 payload。
- P3-06U-26H2R 已新增最终回复样本与人工标签导入导出第一片，知识评测页可导出 CSV、离线标注后预检并导回系统；当前只支持 CSV，不支持 XLSX，不导出原始客户问题，真实外发继续关闭。
- P3-06U-26H2S 已新增客户报告导出与签收留档第一片，质量复盘页可导出客户质量报告 HTML 留档件；导出件包含签收确认区，审计只记录文件 hash、字节数、状态和边界标记，不记录原始问题、完整回复或人工备注明文。
- P3-06U-26H2T 已新增客户签收记录第一片，质量复盘页可记录客户报告确认结果、确认方式、脱敏签收人和备注摘要；审计事件为 `customer_quality_report.signoff_recorded`，不保存签收人明文姓名、备注原文、原始客户问题或完整回复。证据目录为 `output/p3_06u_26h2t_customer_report_signoff_ui/`；当前不是电子签章，不代表完整线上准确率签收。
- P3-06U-26H2U 已新增客户签收记录列表第一片，质量复盘页可查看最近确认记录、确认方式、脱敏签收人、备注摘要状态和审计编号；列表来自 `customer_quality_report.signoff_recorded` 审计事件。证据目录为 `output/p3_06u_26h2u_customer_report_signoff_list_ui/`；当前不是电子签章，不代表完整线上准确率签收。
- P3-06U-26H2W4 已新增客户报告 HTML/XLSX/DOCX 导出与归档第一片，质量复盘页可导出三种文件并查看历史报告归档；历史下载走 `customer-quality-report/archives/{id}/download`。当前仍不是正式电子签章，不做 PDF，不打开真实外发。
- P3-06U-26H2V 已完成中台信息架构对齐与前后端审查修复：总览增加筛选口径证明，渠道接入改为四层分层，管理运维拆为“运维与告警 / 模型路由 / 账号安全”三个真实页面，多渠道对话台文案收紧为 AI 回复建议和真实外发关闭。证据目录为 `output/p3_06u_26h2v_console_ia_alignment/`。
- RPA 继续只作为内部研究归档，不写成正式平台接入、客户可见实验室或自动发送承诺。

验证：

```bash
python3 standard_ops/scripts/check_p3_06u_21_trusted_inbound_reply_decision_loop.py
python3 standard_ops/scripts/check_p3_06u_26a_customer_facing_copy.py
python3 standard_ops/scripts/check_p3_06u_26b_wechat_first_workbench.py
python3 standard_ops/scripts/check_p3_06u_26c_channel_account_configuration.py
python3 standard_ops/scripts/check_p3_06u_26d_knowledge_three_pages.py
python3 standard_ops/scripts/check_p3_06u_26e_answer_quality_evaluation.py
python3 standard_ops/scripts/check_p3_06u_26f_real_customer_templates.py
python3 standard_ops/scripts/check_p3_06u_26g5_small_business_local_ops.py
python3 standard_ops/scripts/check_p3_06u_26g1_desktop_only_console.py
python3 standard_ops/scripts/check_p3_06u_20_reply_decision_state_machine.py
python3 standard_ops/scripts/check_p3_06u_19_business_object_knowledge.py
python3 standard_ops/scripts/check_p3_06u_18_yunduo_engineering_optimization.py
python3 standard_ops/scripts/check_p3_06u_10b_conversation_workbench_simplification.py
python3 standard_ops/scripts/check_p3_06u_09_unified_states.py
python3 standard_ops/scripts/check_p3_06u_03_conversation_workbench.py
cd standard_ops/frontend && npm run build
CHROME_DEBUGGING_URL=http://127.0.0.1:9227 FRONTEND_URL='http://127.0.0.1:5182/?demo=1#live' node ../scripts/check_p3_06u_23_channel_identity_preview.mjs
CHROME_DEBUGGING_URL=http://127.0.0.1:9227 FRONTEND_URL='http://127.0.0.1:5182/?demo=1#live' node ../scripts/check_p3_06u_26a_customer_facing_copy.mjs
CHROME_DEBUGGING_URL=http://127.0.0.1:9227 FRONTEND_URL='http://127.0.0.1:5182/?demo=1#live' node ../scripts/check_p3_06u_26b_wechat_first_workbench.mjs
CHROME_DEBUGGING_URL=http://127.0.0.1:9227 FRONTEND_URL='http://127.0.0.1:5182/?demo=1#channels' node ../scripts/check_p3_06u_26c_channel_account_configuration.mjs
CHROME_DEBUGGING_URL=http://127.0.0.1:9227 FRONTEND_URL='http://127.0.0.1:5182/?demo=1' node ../scripts/check_p3_06u_26d_knowledge_three_pages.mjs
CHROME_DEBUGGING_URL=http://127.0.0.1:9227 FRONTEND_URL='http://127.0.0.1:5182/?demo=1#evals' node ../scripts/check_p3_06u_26e_answer_quality_evaluation.mjs
CHROME_DEBUGGING_URL=http://127.0.0.1:9227 FRONTEND_URL='http://127.0.0.1:5182/?demo=1' node ../scripts/check_p3_06u_24_knowledge_split_and_channel_accounts.mjs
CHROME_DEBUGGING_URL=http://127.0.0.1:9227 FRONTEND_URL=http://127.0.0.1:5181/ node ../scripts/check_p3_06u_10b_conversation_workbench_simplification.mjs
CHROME_DEBUGGING_URL=http://127.0.0.1:9227 FRONTEND_URL=http://127.0.0.1:5181/ P3_06U_03_OUTPUT=../output/p3_06u_03_conversation_workbench_after_10b node ../scripts/check_p3_06u_03_conversation_workbench.mjs
```

下一步建议优先进入真实 IM 消息流闭环第一片：前端选中会话后读取会话详情 messages，右侧只渲染真实 inbound / outbound / system 消息，AI 回复建议、知识依据和外发状态收进轻量记录；真实知识包、官方渠道授权、测试白名单、回执和失败重试仍是生产验收前置条件。

看到 `PASS stage1 foundation` 且 `pytest` 通过，表示基础数据层和 API 契约可继续向知识库、模型路由和会话工作台推进。

## 阶段 2 轻量 Workflow 与人工审核

阶段 2 已推进到 P2-27 短审查收口，目标是先把客服处理流程变成可恢复、可审计、可进入人工审核、能读取结构化知识库与文档级知识片段、能通过模型网关生成回复草稿、能由坐席查看证据后批准/改写/拒绝，并能把已批准回复进入内部待发送草稿、发送前确认、发送检查 worker、模拟发送尝试记录、官方渠道连接器发送计划、官方 Webhook 回调骨架、开发 fixture 验签边界、可信入站消息创建、可信入站编排 worker、平台回执归一化、失败复盘队列、发送队列骨架、文档知识运营入口、知识检索评测集、前端评测质量报表、embedding/reranker 最小后端边界、PostgreSQL/pgvector exact query path、向量索引重建入口、embedding provider smoke 账本、pgvector ANN 策略计划、本地 HNSW/IVFFlat 真实建索引 smoke、模型路由策略、真实百炼聊天模型 smoke 安全入口、脱敏题集质量评测入口、客服商用知识检索评测指标、评测运行结果导出报告、已落库评测运行读取 API、评测运行历史列表、脱敏报告导出 API、P2-24 合成题库知识检索闭环 smoke、P2-25 chunk id 回填评测对比、P2-26 检索 top-k 参数对比和 P2-27 still_missing 失败题分桶。P2-26 新增 `scripts/run_p2_26_retrieval_quality_comparison.py`，复用 P2-25 的动态 chunk 回填题库，对 `top_k=5/8/10/12` 做本地对比。本地结果为：top-k=5 时 `full_evidence_recall_at_k=57.9%`、`citation_precision=39.8%`；top-k=8 时 `full_evidence_recall_at_k=67.1%`、`citation_precision=32.2%`；top-k=12 时 `full_evidence_recall_at_k=76.3%`、`citation_precision=27.8%`。当前推荐生产默认先用 `top_k=8`，`top_k=12` 只作为召回池或重排实验候选；这说明 top-k 太小确实是召回不足原因之一，但直接扩大 top-k 会带来引用精度下降和安全噪音。P2-27 没有新增跑分脚本，只基于 P2-26 的 18 道 `outcome=still_missing` case 做短审查，结论是 P2 合成评测尾巴已经关闭，后续默认进入 P3：真实脱敏 50-100 题、真实知识包、生成答案事实性评测、坐席工作台产品化、单渠道 Copilot sandbox 和试点部署包。当前仍不接真实渠道、不做真实平台消息解密、不做授权网页采集、不向外部平台发消息；P2-17 队列仍是 HTTP 触发的可测试工程入口，不是独立 Redis/RQ/Celery 生产消费者；P2-18F/P2-18G/P2-18H 默认仍用 deterministic 本地 embedding，不消耗真实 embedding API；外部 embedding provider smoke 必须显式传 `allow_external_call=true` 才会调用；pgvector 已完成 exact query path、API smoke、ANN dry-run 计划和本地临时表真实建索引 smoke，但没有切换应用查询路径，不是已经执行生产 HNSW/IVFFlat 索引，也没有真实 embedding 质量验收。模型网关默认使用本地 deterministic provider，不会默认消耗真实模型 Key；P2-22/P2-27 仍只评测检索证据、审核门禁和失败题原因，不生成自由文本答案，也不把 `unsupported_answer_rate=null` 解释为幻觉率为 0。

新增文档：

- `docs/STAGE2_WORKFLOW_FOUNDATION.md`：阶段 2 workflow/checkpoint/human review 的设计边界、数据表、API 和下一步。
- `docs/P2-23_SYNTHETIC_CUSTOMER_SERVICE_EVAL_BANK.md`：P2-23 合成脱敏客户客服验收题库的覆盖范围、使用方式和边界。
- `docs/P2-24_SYNTHETIC_EVAL_SMOKE.md`：P2-24 合成 seed 知识文档、80 题本地评测闭环、脱敏报告产物、指标和不足。
- `docs/P2-25_CHUNK_BACKFILL_EVAL_COMPARISON.md`：P2-25 chunk id 动态回填、基线/回填版运行对比、输出产物、指标解释和下一步。
- `docs/P2-26_RETRIEVAL_QUALITY_COMPARISON.md`：P2-26 检索 top-k 参数对比、默认推荐、召回池建议、失败题 delta 和下一步。
- `docs/P2-27_STILL_MISSING_FAILURE_TAXONOMY.md`：P2-27 对 18 道 `outcome=still_missing` case 的短审查分桶，明确 P2 合成评测尾巴已关闭，下一步进入 P3 真实试点闭环。
- `docs/P3-01_REALISTIC_CUSTOMER_QUESTION_BANK.md`：P3-01 真实脱敏题库与真实知识包模板说明，明确 62 条客户式样例不是客户真实验收。
- `docs/P3-02_RAG_MODEL_ASSISTED_FACTUALITY.md`：P3-02 生成答案事实性与引用支撑 rehearsal 说明，明确默认 deterministic、本轮不外呼真实模型、规则推荐标签不能替代人工事实性标签。
- `docs/P3-03_AGENT_WORKBENCH_V1.md`：P3-03 坐席工作台产品化说明，明确七类队列、会话证据详情、桌面/移动端 QA 和仍未完成的真实渠道/真实模型边界。

新增能力：

| 能力 | 接口 |
| --- | --- |
| 创建会话处理流程 | `POST /api/conversations/{conversation_id}/workflow-runs` |
| 租户流程列表 | `GET /api/tenants/{tenant_id}/workflow-runs` |
| 流程详情 | `GET /api/workflow-runs/{workflow_run_id}` |
| 记录步骤尝试 | `POST /api/workflow-runs/{workflow_run_id}/step-attempts` |
| 记录流程检查点 | `POST /api/workflow-runs/{workflow_run_id}/checkpoints` |
| 创建人工审核任务 | `POST /api/workflow-runs/{workflow_run_id}/human-review-tasks` |
| 租户人工审核列表 | `GET /api/tenants/{tenant_id}/human-review-tasks` |
| 坐席审核收件箱 | `GET /api/tenants/{tenant_id}/human-review-inbox` |
| 审核通过或拒绝 | `PATCH /api/human-review-tasks/{task_id}` |
| 从已批准审核生成 outbox 草稿 | `POST /api/human-review-tasks/{task_id}/outbox-drafts` |
| 租户 outbox 草稿列表 | `GET /api/tenants/{tenant_id}/outbox-drafts` |
| 确认草稿进入待发送 | `POST /api/outbox-drafts/{draft_id}/confirmation` |
| 取消待确认草稿 | `POST /api/outbox-drafts/{draft_id}/cancellation` |
| 创建 dry-run 发送尝试 | `POST /api/outbox-drafts/{draft_id}/send-attempts` |
| 查看草稿发送尝试 | `GET /api/outbox-drafts/{draft_id}/send-attempts` |
| 运行发送检查 worker | `POST /api/tenants/{tenant_id}/outbox-worker-runs` |
| 运行可信入站编排 worker | `POST /api/tenants/{tenant_id}/trusted-inbound-worker-runs` |
| 配置渠道连接器占位 | `POST /api/channels/{channel_id}/connector-config` |
| 查看渠道连接器占位 | `GET /api/channels/{channel_id}/connector-config` |
| 查看渠道 provider 契约 | `GET /api/channel-providers` |
| 生成官方渠道发送计划 | `POST /api/outbox-drafts/{draft_id}/connector-send-plans` |
| 接收官方渠道 Webhook 占位 | `POST /api/webhooks/{provider}/channels/{channel_id}` |
| 记录渠道回执占位 | `POST /api/channels/{channel_id}/delivery-receipts` |
| 查看渠道回执占位 | `GET /api/channels/{channel_id}/delivery-receipts` |
| 查看失败复盘队列 | `GET /api/tenants/{tenant_id}/delivery-failure-reviews` |
| 处理失败复盘项 | `PATCH /api/delivery-failure-reviews/{review_id}` |
| 创建发送队列任务 | `POST /api/outbox-drafts/{draft_id}/delivery-jobs` |
| 查看发送队列任务 | `GET /api/tenants/{tenant_id}/outbox-delivery-jobs` |
| 运行发送队列骨架 | `POST /api/tenants/{tenant_id}/outbox-delivery-queue-runs` |
| 入站消息回复编排 | `POST /api/messages/{message_id}/reply-orchestrations` |
| 创建知识卡片 | `POST /api/tenants/{tenant_id}/knowledge-cards` |
| 知识卡片列表 | `GET /api/tenants/{tenant_id}/knowledge-cards` |
| 更新知识卡片 | `PATCH /api/knowledge-cards/{card_id}` |
| 知识检索 | `POST /api/tenants/{tenant_id}/knowledge-searches` |
| 导入知识文档 | `POST /api/tenants/{tenant_id}/knowledge-documents` |
| 知识文档列表 | `GET /api/tenants/{tenant_id}/knowledge-documents` |
| 查看文档分块 | `GET /api/knowledge-documents/{document_id}/chunks` |
| 文档片段检索 | `POST /api/tenants/{tenant_id}/knowledge-document-searches` |
| 创建知识评测集 | `POST /api/tenants/{tenant_id}/knowledge-evaluation-sets` |
| 知识评测集列表 | `GET /api/tenants/{tenant_id}/knowledge-evaluation-sets` |
| 运行知识检索评测 | `POST /api/knowledge-evaluation-sets/{evaluation_set_id}/runs` |
| 评测运行历史 | `GET /api/knowledge-evaluation-sets/{evaluation_set_id}/runs` |
| 读取评测运行详情 | `GET /api/knowledge-evaluation-runs/{evaluation_run_id}` |
| 导出脱敏评测报告 | `GET /api/knowledge-evaluation-runs/{evaluation_run_id}/report?format=markdown|csv` |
| 重建知识向量索引 | `POST /api/tenants/{tenant_id}/knowledge-vector-index/rebuilds` |
| 规划知识向量索引策略 | `POST /api/tenants/{tenant_id}/knowledge-vector-index/plans` |
| 运行 embedding provider smoke | `POST /api/tenants/{tenant_id}/knowledge-embedding-provider-smoke-runs` |

ReplyOrchestrator 当前支持四种模式：

- `manual`：调用方显式传入意图、知识命中数、回复草稿、置信度和风险等级，用于测试外部模型或人工辅助系统接入。
- `knowledge_search`：后端基于入站消息或指定 `knowledge_query` 调用结构化知识卡片检索，把命中知识写入 workflow state，并用最高命中知识卡片生成回复草稿。
- `document_rag`：后端基于入站消息或指定 `knowledge_query` 调用文档分块检索，把 chunk 级 citation 写入 workflow state，并用最高相关片段生成可溯源草稿。
- `model_assisted`：后端先调用结构化知识卡片检索，再调用模型网关生成草稿。当前默认 provider 是 `deterministic`，用于本地测试和演示；显式选择 `bailian` 或 `deepseek` 且配置对应 API Key 时，才会走 OpenAI-compatible 外部模型调用。

当前编排器会创建 workflow run、记录步骤尝试、记录检查点，并根据知识命中、模型可用性、置信度和风险等级自动完成或进入人工审核。它还没有接生产向量库、重排器、渠道外发或出站消息创建。

知识库检索当前有两层：

- `owner/admin` 可以创建和更新知识卡片。
- `owner/admin` 可以导入知识文档，系统会自动切分为 `knowledge_document_chunks`。
- 同租户已登录用户可以查询和检索知识。
- 默认只检索 `active` 知识，不检索 `archived`。
- 结构化卡片检索模式是 `lexical_bm25_v1`。
- 文档片段检索模式是 `hybrid_bm25_vector_rerank_v1`，返回 `vector_engine`、`vector_store`、`retrieval_backend`、`vector_index_status`、`embedding_provider`、`embedding_model`、`reranker`、chunk id、document id、source uri、char range 和 citation。
- owner/admin 可以创建知识评测集并运行文档检索评测；评测报告返回命中率、引用覆盖率、期望词覆盖率、平均置信度、需复盘题数和逐题结果。
- P2-18D 已把知识评测集接入前端“知识评测与质量”面板，可在工作台创建题集、运行评测、查看质量指标和逐题失败原因。
- P2-18C/P2-18D 当前只评测检索命中和引用覆盖，不生成自由文本答案，因此 `unsupported_answer_rate` 暂为 `null`，不会伪造幻觉率。
- 当前已有 deterministic 本地 embedding、portable JSON vector 存储、OpenAI-compatible embedding provider 边界、embedding provider smoke API、成本/延迟估算记录、PostgreSQL/pgvector 原生列、pgvector exact cosine 查询路径、向量索引重建入口、pgvector HNSW/IVFFlat dry-run 策略计划、本地独立 smoke 表 HNSW/IVFFlat 真实建索引 smoke 和轻量 lexical reranker；但仍没有执行生产级 pgvector ANN 建索引，没有切换应用查询路径，也没有正式语义 embedding 质量验收。
- ReplyOrchestrator 的 `knowledge_search` 模式已经会调用该检索能力，命中时生成草稿，无命中时进入人工审核。
- ReplyOrchestrator 的 `document_rag` 模式已经会调用文档片段检索能力，命中时把引用片段写入 workflow state。

模型网关当前是 v1 服务层：

- `deterministic`：本地可重复草稿生成，适合自动化测试、无 Key 演示和流程验证。
- `bailian`：百炼兼容模式入口，读取 `BAILIAN_API_BASE`、`BAILIAN_API_KEY`、`BAILIAN_MODEL`。
- `deepseek`：DeepSeek 兼容模式入口，读取 `DEEPSEEK_API_BASE`、`DEEPSEEK_API_KEY`、`DEEPSEEK_MODEL`。
- provider 无 Key、失败或不可用时，编排器转人工，原因 `model_unavailable`。
- P2-19 新增模型路由策略：`auto` 会按意图、风险等级、回复置信度和知识命中数选择模型档位。
- `simple_fast`：问候、导航、简单 FAQ，优先百炼 `qwen3.6-flash`。
- `standard_support`：普通客服问答，优先百炼 `qwen3.7-plus`。
- `premium_guarded`：投诉、赔付、法律、合同、复杂政策，优先百炼 `qwen3.7-max`，并强制保留人工审核门。
- `deterministic_safe_fallback`：未配置外部模型 Key 时，回到本地 deterministic，不外呼、不消耗费用。
- 每次 `model_call` 会记录 `route_name`、`complexity`、`target_model_tier`、`fallback_chain`、`human_review_required` 和 `route_reasons`。
- P2-19 只完成路由控制和审计字段，不代表真实模型质量验收；真实效果仍需百炼/DeepSeek 受控 smoke、真实题库和人工标注。
- P2-20 新增 `scripts/smoke_bailian_chat_model.py`：默认不外呼；只有传 `--allow-external-call` 且配置 `BAILIAN_API_KEY` 时，才会调用百炼 OpenAI-compatible `chat/completions`。
- smoke 输出只包含状态、provider/model、路由、人审门禁、输入 hash、耗时、usage 摘要和短预览；不会保存 API key、不会把 sample 原文写入结果，缺 key 时返回 `blocked_missing_api_key`。
- 2026-06-26 已完成一次真实百炼聊天 smoke：`provider=bailian`、`model=qwen-plus`、`route_name=standard_support`、`status=succeeded`、`latency_ms≈1733`、usage 摘要 `prompt=182 / completion=42 / total=224`。这只证明连通和 usage 可观测，不代表客户题库质量验收完成。
- P2-21 新增 `scripts/evaluate_bailian_chat_quality.py`：默认不外呼；只有传 `--allow-external-call` 且配置 `BAILIAN_API_KEY` 时，才会按 `--limit` 调用百炼做脱敏合成题集质量评测。
- 评测集当前为 `built_in_public_synthetic_cases_v1`，覆盖人工审核边界、发货退换货、价格承诺、发票纠纷、渠道边界、订单状态、退款投诉、复杂集成、知识缺口、合同法务和隐私边界等公开合成场景。
- 评测输出只记录 case id、分类、input hash、路由、usage、latency、`missing_expected_terms`、`forbidden_term_hits` 和人审门禁；不会把问题原文、知识原文、API key 或完整 provider 响应写入结果。
- P2-21 只是模型质量验收入口的第一片，不等于真实客户 50-100 题、人工标注、引用事实性复核、并发稳定性或最终成本已经完成。
- 2026-06-26 已用真实百炼 key 跑通 P2-21 小样本评测：`attempted_calls=5`、`succeeded=5`、`average_latency_ms≈2596`、`total_tokens_or_chars=1037`、`human_review_required_cases=3`、`forbidden_term_hits=0`、`missing_expected_terms=3`。这说明连通和安全指标摘要可用，但仍提示提示词/知识口径需要继续优化。
- P2-22 新增 `customer_service_retrieval` 评测模式，把知识评测题扩展为客服商用验收题：可标注 `expected_chunk_ids`、`must_have_all_evidence`、`expected_human_review`、`allow_auto_reply`、`forbidden_terms` 和 `risk_level`。
- P2-22 运行报告新增 `full_evidence_recall_at_5`、`citation_precision`、`human_review_correctness` 和 `knowledge_gap_rate`，用于评估多证据召回、引用相关性、转人工门禁是否符合预期和知识缺口；它仍不生成自由文本答案，所以 `unsupported_answer_rate` 仍为 `null`。
- P2-22B 新增 `scripts/import_customer_service_eval_bank.py` 和 `evals/customer_service_eval_bank_template.csv`：支持 CSV/JSON 脱敏客户题库导入，字段包含 `external_case_id`、`source_channel`、`source_category`、`annotation_notes` 以及 P2-22 的证据和人审字段。
- 导入脚本默认只校验和输出安全摘要，不打印原始问题，不调用外部模型，不写外部平台；检测到手机号、邮箱或身份证号默认返回 `blocked_sensitive_rows`。只有显式传 `--create --api-base --tenant-id --token` 才会调用后端 API 创建评测集。
- P2-22C 新增 `scripts/export_customer_service_eval_report.py`：把 `POST /api/knowledge-evaluation-sets/{evaluation_set_id}/runs` 返回的运行 JSON 导出为 CSV 逐题表和 Markdown 复盘报告，默认不导出原始问题、不导出命中知识片段原文，只保留 `question_hash`、证据指标、人审判断、失败原因和知识缺口；只有显式传 `--include-raw-text` 才会把问题原文写入报告。
- P2-22D 新增 `GET /api/knowledge-evaluation-runs/{evaluation_run_id}`：owner/admin 可以读取已经落库的评测运行详情和逐题结果，方便后续重新导出报告；无 token 返回 401，普通坐席返回 403，跨租户返回 404。该接口不调用模型、不写外部平台，但返回结构仍包含题目原文，因此只开放给知识管理角色。
- P2-22E 新增 `GET /api/knowledge-evaluation-sets/{evaluation_set_id}/runs`：owner/admin 可以按评测集查看历史运行摘要，默认按最新运行排序，支持分页。该列表不返回逐题 `case_results` 或问题原文；前端“知识评测与质量”面板已显示最近运行，并可按 run id 载入详情。
- P2-22F 新增 `GET /api/knowledge-evaluation-runs/{evaluation_run_id}/report?format=markdown|csv`：owner/admin 可以从已落库运行直接生成脱敏 Markdown 复盘报告或 CSV 逐题表。该接口只输出 `question_hash`、来源元数据和指标，固定 `raw_text_included=false`、`provider_call_performed=false`、`external_write_performed=false`，不支持原文导出；前端当前运行区域已提供“下载报告”和“CSV”按钮。
- P2-23 新增 `evals/customer_service_eval_bank_synthetic_80_2026-06-26.csv`：80 条真实业务语境合成脱敏客服验收题，覆盖官网、企业微信、公众号、抖音、小红书、淘宝、京东、拼多多等渠道，以及产品咨询、价格优惠、下单支付、物流、售后、合同发票、隐私、平台规则、企业采购和知识缺口。该题库用于工程验证和安全压力测试，不是自然流量分布，也不是客户真实聊天记录。
- P2-24 新增 `evals/p2_24_seed_knowledge_documents.json` 和 `scripts/run_p2_24_synthetic_eval_smoke.py`：使用本地一次性 SQLite 完成“seed 知识文档 -> 80 题评测集 -> 检索评测 -> 脱敏报告”的闭环。该 smoke 不调用外部模型、不写外部平台、不使用真实客户资料；输出位于 `output/evals/p2_24_synthetic_eval_smoke/`。
- P2-25 新增 `scripts/run_p2_25_chunk_backfill_eval_comparison.py`：使用同一组 seed 文档和 80 题题库，先跑原始题库基线，再读取实际导入后的 document chunk id，按 `expected_source_uri + expected_terms` 动态回填 `expected_chunk_ids`，最后跑回填版评测并输出对比报告。该脚本不调用外部模型、不写外部平台、不使用真实客户资料；输出位于 `output/evals/p2_25_chunk_backfill_eval_comparison/`。
- P2-26 新增 `scripts/run_p2_26_retrieval_quality_comparison.py`：使用 P2-25 的 chunk 回填版评测 payload，对 `top_k=5/8/10/12` 做本地对比，输出运行汇总、失败题 delta CSV 和推荐 top-k 对应的脱敏报告。该脚本不调用外部模型、不写外部平台、不使用真实客户资料；输出位于 `output/evals/p2_26_retrieval_quality_comparison/`。
- P2-27 新增 `docs/P2-27_STILL_MISSING_FAILURE_TAXONOMY.md`：只读分析 P2-26 的 18 道 `outcome=still_missing` case，按文档缺口、chunk 粒度、同源排序、风险门禁耦合和标注复核分桶。该阶段不新增评测脚本、不新增报告导出、不调用外部模型、不写外部平台；P2 合成评测尾巴已关闭，后续质量工作必须进入真实脱敏题库或真实客户类知识包。

## 阶段 3 真实试点材料与客户可见闭环

阶段 3 已完成 P3-01、P3-02、P3-03 和 P3-04 第一片，目标是把验收对象从 P2 合成题库切换到真实试点材料，并把检索层指标推进到答案草稿事实性门禁，再把后端链路整理成坐席可理解的运营工作台，最后用一条自有官网沙盒跑通受控 Copilot 闭环。当前新增：

- `evals/p3_01_realistic_customer_service_eval_bank_62_2026-06-27.csv`：62 条客户式试点题库样例，覆盖售前咨询、价格套餐、交付部署、售后退款、账号权限、渠道合规、投诉法务、知识缺口和恶意诱导。它用于 rehearsal 和字段校验，不是客户真实聊天记录。
- `evals/p3_01_realistic_knowledge_package_template.json`：7 份真实知识包模板，覆盖产品范围、套餐价格、交付部署、售后退款、账号权限发票、渠道合规和高风险法务。
- `docs/P3-01_REALISTIC_CUSTOMER_QUESTION_BANK.md`：P3-01 阶段卡、字段说明、推荐分布、知识包结构、dry-run 命令和完成边界。
- `backend/tests/test_customer_service_eval_bank_import_script.py`：新增 P3-01 fixture 校验，确保 62 条题库默认 dry-run、无外部动作、无高置信隐私命中，并保持 50-100 题范围。
- `scripts/run_p3_02_rag_model_assisted_factuality_rehearsal.py`：P3-02 本地 rehearsal 脚本，导入 P3-01 知识包和 62 题题库，回填 chunk id，运行检索评测，并用 deterministic provider 生成受控草稿事实性门禁。
- `docs/P3-02_RAG_MODEL_ASSISTED_FACTUALITY.md`：P3-02 阶段卡、运行方式、输出文件、人工事实性标签口径和完成边界。
- `backend/tests/test_p3_02_factuality_rehearsal_script.py`：验证 P3-02 默认不外呼、不写平台、不导出原始问题或草稿正文，并阻断未授权外部 provider。
- `output/evals/p3_02_factuality_rehearsal/`：P3-02 本地脱敏输出，包含 summary JSON、Markdown 报告和逐题 CSV。
- `docs/P3-03_AGENT_WORKBENCH_V1.md`：P3-03 坐席工作台产品化 v1 阶段卡、队列说明、证据详情、验证结果和完成边界。
- `output/p3_03_workbench_desktop.png`、`output/p3_03_workbench_mobile.png`：P3-03 桌面和 390px 移动端 Chrome CDP 截图证据。
- `docs/P3-04_SINGLE_CHANNEL_COPILOT_SANDBOX.md`：P3-04 单渠道 Copilot sandbox 阶段卡、官网沙盒选择、闭环图、验收方式、完成边界和下一步。
- `docs/P3-06R-03A_AGENT_DESK_ONE_SCREEN_CLOSURE.md`：P3-06R-03A 坐席工作台一屏闭环第一片，记录同屏编辑 AI 草稿、内部备注、引用确认、批准进入待发送、确认待发送、右侧处理动作和浏览器截图证据。
- `docs/P3-06R-04C_OPS_DASHBOARD_AGGREGATION.md`：P3-06R-04C 运营总览服务端聚合接口第一片，记录 `dashboard.read` 权限、脱敏聚合字段、前端正式聚合优先和验证结果。
- `docs/P3-06S-01_LAYOUT_BREAKPOINT_SCROLL_REPAIR.md`：P3-06S-01 窄桌面壳层滚动修复，记录 900px 断点复现、修复后浏览器滚动指标、截图证据和构建验证。
- `backend/tests/test_p3_04_website_copilot_sandbox.py`：P3-04 官网沙盒端到端验收，覆盖错签阻断、有效入站、幂等去重、AI 草稿进人审、outbox、发送计划门禁和审计。
- `output/p3_04_website_sandbox_desktop.png`、`output/p3_04_website_sandbox_mobile.png`：P3-04 桌面和 390px 移动端 Chrome CDP 截图证据。

P3-01 dry-run：

```bash
cd /Users/ericlee/Desktop/肥肥lu/lite_a_customer_service/standard_ops
.venv/bin/python scripts/import_customer_service_eval_bank.py \
  evals/p3_01_realistic_customer_service_eval_bank_62_2026-06-27.csv \
  --name "P3-01 真实客户式试点题库样例 62题" \
  --description "用于验证 P3-01 真实脱敏题库字段、分布和脱敏 dry-run 的客户式样例，不含真实客户身份或真实订单资料。"
```

当前验证结果：

- `status=validated`
- `total_cases=62`
- `sensitive_row_count=0`
- `provider_call_performed=false`
- `external_write_performed=false`
- `pytest backend/tests/test_customer_service_eval_bank_import_script.py -q` 通过，结果 `4 passed`

当前边界：

- P3-01 已完成的是客户式题库和知识包模板，不是客户真实 50-100 题验收。
- 不调用百炼、DeepSeek 或 embedding provider。
- 不接真实平台，不写外部渠道。
- 真实客户题库导入前仍必须人工脱敏和人工标注。

P3-02 默认安全运行：

```bash
cd /Users/ericlee/Desktop/肥肥lu/lite_a_customer_service/standard_ops
.venv/bin/python scripts/run_p3_02_rag_model_assisted_factuality_rehearsal.py \
  --output-dir output/evals/p3_02_factuality_rehearsal
```

当前验证结果：

- `status=completed`
- `total_cases=62`
- `answer_supported_by_citations_rate=0.4355`
- `answer_has_forbidden_commitment_cases=10`
- `answer_requires_human_review_cases=56`
- `manual_factuality_labels_collected=0`
- `provider_call_performed=false`
- `external_platform_write_performed=false`
- `raw_text_logged=false`
- `.venv/bin/python -m pytest backend/tests/test_p3_02_factuality_rehearsal_script.py backend/tests/test_customer_service_eval_bank_import_script.py backend/tests/test_p2_26_retrieval_quality_comparison_script.py -q` 通过，结果 `8 passed`

P3-02 边界：

- 这是答案层事实性 rehearsal，不是客户真实 50-100 题正式验收。
- 默认使用 deterministic provider，不调用百炼、DeepSeek 或其他真实模型。
- 规则输出的 `recommended_factuality_label` 只是复核建议，不能替代人工 `manual_factuality_label`。
- 本轮结果显示检索 `hit_rate=1.0` 不等于草稿可自动发送；P3-03 已承接该结论，把草稿、证据、人审、outbox、失败复盘和渠道健康整理成坐席工作台。

P3-03 已完成的坐席工作台第一片：

- 前端总览状态更新为 `P3-03`。
- 主屏展示 `待人工审核`、`待发送确认`、`发送失败`、`知识缺口`、`高风险会话`、`最近评测运行`、`渠道健康` 七类队列。
- 会话详情展示原始入站、AI 草稿、引用证据、风险等级、转人工原因、模型/provider 状态、outbox 状态和审计链。
- `npm run build` 通过。
- Chrome CDP 桌面 1440x1000 和移动 390x1200 截图 QA 通过，移动端 `innerWidth=390`、`scrollWidth=390`，无横向溢出。

P3-03 边界：

- 当前是客户可见工作台第一片，不是完整 CRM、SLA、工单、排班或绩效系统。
- 仍不接真实外部平台，不调用真实官方发送 API，不自动外发。
- 真实模型质量验收、客户真实 50-100 题和人工事实性标签仍未完成。
- P3-04 已承接该阶段，选择官网客服沙盒验证入站、草稿、证据审查、人工确认和内部 outbox 闭环。

P3-04 已完成的官网 Copilot 沙盒第一片：

- 前端总览状态更新为 `P3-04`，新增“官网 Copilot 沙盒”面板。
- 后端官网 HMAC fixture 验签、可信入站消息创建、幂等去重、可信入站 worker、人工审核、outbox 和 connector noop 发送计划形成端到端闭环。
- 错签 webhook 只记录回执，不创建客服消息。
- 有效官网入站只创建一次可信消息；重复回调返回 `duplicate_ignored`。
- AI 草稿只进入人工审核；审核通过后生成 outbox 草稿，草稿确认后只生成被门禁拦截的发送计划，不真实外发。
- `backend/app/services/channel_provider_registry.py` 已把官网 provider fixture 状态修正为 P3-04 已验证可信消息创建，但生产密钥轮换、重放 nonce 存储和真实外发仍未完成。
- `frontend/src/App.tsx`、`frontend/src/styles.css` 和 `frontend/src/data/navigation.ts` 已新增官网沙盒状态入口，并保持移动端无横向溢出。

P3-04 验证结果：

- `.venv/bin/python -m pytest tests/test_p3_04_website_copilot_sandbox.py -q` 通过。
- `.venv/bin/python -m pytest tests/test_channel_webhooks_api.py tests/test_trusted_inbound_worker_api.py tests/test_outbox_api.py tests/test_channel_connectors_api.py tests/test_p3_04_website_copilot_sandbox.py -q` 通过，结果 `27 passed`。
- `npm run build` 通过。
- Chrome CDP 桌面 1440x1000 截图 QA 通过，`innerWidth=1440`、`scrollWidth=1440`，沙盒面板存在。
- Chrome CDP 移动 390x1200 截图 QA 通过，`innerWidth=390`、`scrollWidth=390`，沙盒面板宽度 346px，无横向溢出。

P3-04 边界：

- 这是自有官网沙盒，不是企业微信、公众号、抖音、小红书、淘宝、京东或拼多多真实接通。
- 仍不打开真实外发，不使用个人微信外挂、Hook、群控、模拟点击或商家后台 RPA。
- 真实平台接入必须另行准备官方账号、回调域名、Token、EncodingAESKey/AppSecret、平台规则复核和用户明确授权。
- P3-05A/P3-05B/P3-05C 之后已继续推进到 P3-06U：P3-06R-04C 已完成运营总览服务端聚合第一片，P3-06T-01 已完成壳层滚动返修验收，P3-06T-02 已完成首页数据口径收紧，P3-06T-03 已完成运营总览 BI 重做，P3-06U-01 已完成前后端契约与页面路径盘点，P3-06U-02 已完成角色化任务路径重排，P3-06U-03 已完成接待工作台实用性重构，P3-06U-04 已完成运营总览到处理路径打通，P3-06U-05 已完成真实登录角色 smoke，P3-06U-06 已完成质量复盘 BI 修复闭环，P3-06U-07 已完成知识运营台产品化第一片，P3-06U-08 已完成渠道连接器中心实用化，P3-06U-09 已完成前端状态体系统一。当前下一步优先 P3-06U-10 前端组件和状态结构拆分；P3-06R-05 渠道连接器中心继续保留为后续真实配置接口主线，不默认打开真实外发。

P2-22B 客服脱敏题库导入：

```bash
python3 standard_ops/scripts/import_customer_service_eval_bank.py \
  standard_ops/evals/customer_service_eval_bank_template.csv \
  --name "客服脱敏验收题库"
```

如需生成可提交给 API 的 payload 文件：

```bash
python3 standard_ops/scripts/import_customer_service_eval_bank.py \
  standard_ops/evals/customer_service_eval_bank_template.csv \
  --name "客服脱敏验收题库" \
  --output-payload /tmp/customer_service_eval_payload.json
```

P2-23 合成脱敏 80 题验收题库 dry-run：

```bash
python3 standard_ops/scripts/import_customer_service_eval_bank.py \
  standard_ops/evals/customer_service_eval_bank_synthetic_80_2026-06-26.csv \
  --name "P2-23 合成脱敏客户客服验收题库 80题" \
  --description "用于标准运营版 P2-23 的真实业务语境合成脱敏题库。不含真实客户身份或真实订单资料。"
```

预期结果：`status=validated`、`total_cases=80`、`sensitive_row_count=0`、`raw_text_logged=false`、`provider_call_performed=false`、`external_write_performed=false`。

P2-24 合成题库知识检索闭环 smoke：

```bash
cd /Users/ericlee/Desktop/肥肥lu/lite_a_customer_service/standard_ops
.venv/bin/python scripts/run_p2_24_synthetic_eval_smoke.py \
  --output-dir output/evals/p2_24_synthetic_eval_smoke
```

预期结果：`status=completed`、`seed_document_count=9`、`total_cases=80`、`hit_rate=100.0%`、`citation_coverage=100.0%`、`forbidden_term_hits=0`、`provider_call_performed=false`、`external_platform_write_performed=false`。

P2-25 chunk id 回填评测对比：

```bash
cd /Users/ericlee/Desktop/肥肥lu/lite_a_customer_service/standard_ops
.venv/bin/python scripts/run_p2_25_chunk_backfill_eval_comparison.py \
  --output-dir output/evals/p2_25_chunk_backfill_eval_comparison
```

预期结果：`status=completed`、`bound_case_count=76`、`full_evidence_cases 0 -> 76`、`full_evidence_recall_at_5 0.0% -> 57.9%`、`provider_call_performed=false`、`external_platform_write_performed=false`。

P2-26 检索 top-k 参数对比：

```bash
cd /Users/ericlee/Desktop/肥肥lu/lite_a_customer_service/standard_ops
.venv/bin/python scripts/run_p2_26_retrieval_quality_comparison.py \
  --output-dir output/evals/p2_26_retrieval_quality_comparison
```

预期结果：`status=completed`、`top_ks=[5,8,10,12]`、`candidate_default_top_k=8`、`candidate_recall_pool_top_k=12`、`baseline_failed_recovered_count=14`、`still_missing_case_count=18`、`provider_call_performed=false`、`external_platform_write_performed=false`。

P2-22C 客服评测运行报告导出：

```bash
python3 standard_ops/scripts/export_customer_service_eval_report.py \
  /tmp/customer_service_eval_run.json \
  --output-dir /tmp/customer_service_eval_reports
```

坐席审核收件箱当前是后端 API v1：

- 默认返回 `open` 审核任务，可通过 `status` 查询其它状态。
- 每条任务包含会话摘要、触发入站消息、workflow 状态和证据包。
- 证据包包含 `retrieval_engine`、`knowledge_matches`、`model_call`、`confidence`、`risk_level` 和 `draft_source`。
- `PATCH /api/human-review-tasks/{task_id}` 支持批准、改写后批准或拒绝，并把最终处理结果写回 workflow state 的 `human_review` 字段。
- 当前批准不会自动发送到任何外部平台；坐席可从已批准审核任务创建内部 outbox 草稿，确认后状态进入 `ready_to_send`，但 `delivery_status` 仍为 `not_sent`。
- 当前前端已能读取审核收件箱、批准进入待发送草稿、确认草稿、触发单条发送、运行发送检查和生成官方渠道发送计划。微信客服已经接入官方回调解密、`sync_msg` 拉取和 `send_msg` 文本外发；其他计划中渠道仍保留连接器占位和外发门禁。

P2-15 官方渠道 Webhook、fixture 验签、可信入站消息和入站编排当前包括：

- `GET /api/channel-providers` 返回企业微信客服、微信公众号和官网客服组件的 provider 契约。
- P3-05E 已补企业微信/微信客服官方 inbound sandbox：`GET /api/webhooks/wecom/channels/{channel_id}` 可用于企业微信后台 URL 验证，`POST /api/webhooks/wecom/channels/{channel_id}` 支持官方 XML 安全模式消息、Token 签名校验、`EncodingAESKey` AES-CBC 解密和内层 XML 解析。
- 企业微信 sandbox 密钥通过 `credential_ref=env:WECOM_KF` 间接引用，真实值从 `WECOM_KF_CALLBACK_TOKEN`、`WECOM_KF_ENCODING_AES_KEY`、`WECOM_KF_RECEIVER_ID` 或 `WECOM_CORP_ID` 读取；数据库和回执不保存 Token、AESKey、签名值或密文。
- `POST /api/webhooks/{provider}/channels/{channel_id}` 可在无 Bearer token 的情况下接收平台回调占位，用于模拟真实开放平台主动回调。
- Webhook 入口会检查 provider 是否存在、渠道是否配置了匹配连接器，不匹配返回 404。
- 当前不保存签名值，只保存 query key、provider、event_type、secret_status、verification_status 和 verification_method 等审计必要信息。
- 默认密钥未配置时仍标记为 `secret_not_configured`，`signature_validated=false`。
- 当连接器 `public_config.credential_ref` 指向 P2-13 fixture 时，服务端可计算企业微信 `msg_signature`、公众号 plain `signature` 或官网 HMAC，并标记 `signature_validated` 或 `signature_invalid`。
- 受保护的手工回执接口也不能由调用方自行声明 `signature_validated=true`。
- fixture 验签通过后，如果是 `message` 事件，且 provider event id 或 external message id、消息内容、联系人身份都齐备，会创建内部 `messages.direction=inbound` 可信入站消息，并记录会话事件和审计事件。
- 相同 provider event id 或 external message id 的重复回调不会重复创建消息，会返回 `duplicate_ignored` 并保留回执记录。
- 验签通过但内容缺失、联系人身份缺失或幂等键缺失时，只记录已验证回执，不创建消息。
- 可信入站消息创建时只返回 `queue_trusted_inbound_message_for_reply_orchestration`，不会在 webhook 请求内直接跑完整编排，也不会触发外部写入。
- 坐席登录后可调用 `POST /api/tenants/{tenant_id}/trusted-inbound-worker-runs` 或在前端点击“运行入站编排”，把可信入站消息送入 ReplyOrchestrator。
- 入站 worker 默认使用 `model_assisted + deterministic`，并以 `risk_level=medium` 进入人工审核收件箱，证明“可信入站 -> 编排 -> 人审”链路。
- 入站 worker 使用 `trusted_inbound_message:{message_id}:reply_orchestration` 做轻量幂等，重复运行不会重复创建 workflow。
- 入站 worker 当前仍不自动创建 outbox、不调用真实平台、不执行外部写入。
- raw payload 中出现 `signature`、`token`、`secret`、`authorization`、`cookie` 等敏感 key 时会被写成 `[redacted]`。
- 阶段 6 微信客服链路会识别 `kf_msg_or_event`，使用回调 Token 和持久化 cursor 调用 `kf/sync_msg`，只把 `origin=3` 的客户消息送入统一会话和 AI 决策；回调完成后返回官方要求的 `success`。
- 微信客服文本外发通过 `gettoken` 和 `kf/send_msg` 执行，access token 在进程内缓存并在失效错误后刷新；真实外发仍同时受 `OUTBOX_EXTERNAL_WRITE_ENABLED` 和连接器 `external_write_enabled` 两层门禁控制。

P2-16 平台回执归一化与失败复盘当前包括：

- `channel_delivery_receipts` 新增 `provider_status`、`provider_error_code`、`normalized_status`、`retryable`、`needs_review` 和 `next_action`。
- 新增 `delivery_failure_reviews` 队列表，集中承接限流、授权失败、权限不足、接收人不可达、内容拒绝、普通失败和未知平台状态。
- `POST /api/channels/{channel_id}/delivery-receipts` 与 `POST /api/webhooks/{provider}/channels/{channel_id}` 都会走同一套归一化逻辑。
- `delivered/read/received` 等成功或非失败状态不会进入失败复盘。
- `45009/rate_limited` 会归一化为 `rate_limited`，标记 `retryable=true`，下一步为 `retry_later`。
- 授权、权限、内容拒绝、收件人不可达和未知状态进入人工复盘，不会被静默吞掉。
- 前端新增“失败复盘队列”，可查看失败原因、平台状态、错误码、是否可重试和下一步动作，并可标记已处理。
- 当前仍不会自动重发；复盘队列只是生产级队列、锁、重试和告警前的运营入口。

P2-17 生产级发送队列、锁、重试和 kill switch 骨架当前包括：

- 新增 `outbox_delivery_jobs` 队列表，记录草稿、渠道、连接器、状态、优先级、尝试次数、最大尝试次数、锁字段、下次运行时间、幂等键、是否请求外部写、是否允许外部写、最近尝试和死信原因。
- 新增 `OUTBOX_EXTERNAL_WRITE_ENABLED=false` 全局外部写总开关，默认关闭；即使创建了请求外部写的 job，也会被 kill switch 阻断并进入失败复盘。
- 新增 `POST /api/outbox-drafts/{draft_id}/delivery-jobs`，把 `ready_to_send` 草稿转换为可审计的发送队列任务；重复创建会被幂等键挡住。
- 新增 `POST /api/tenants/{tenant_id}/outbox-delivery-queue-runs`，可批量扫描 due job，写入锁字段，执行限流，记录 `delivery_queue` 发送尝试，并根据结果进入 succeeded、blocked、retry_scheduled 或 dead_letter。
- 渠道 inactive 会先重试，达到最大次数后进入 dead letter，并生成合成回执和失败复盘项。
- 请求外部写但总开关关闭会被标记为 `external_write_kill_switch`，生成 `permission_denied` 复盘项。
- 前端待发送草稿面板可创建发送队列任务、运行发送队列，并展示最近队列运行的成功、阻断、重试、死信和外部写状态。
- 微信客服连接器在两层外发开关均开启时会调用官方文本发送 API，并记录 `sent_at` 与平台 `msgid`；其他未实现 sender 的 provider 仍保持 `not_sent` 硬边界。

P2-18/P2-18B/P2-18C/P2-18D/P2-18E/P2-18F/P2-18G/P2-18H RAG v1 与知识库工程化当前包括：

- 新增 `knowledge_documents` 和 `knowledge_document_chunks`，支持把纯文本文档导入为可检索 chunk。
- 新增 `knowledge_evaluation_sets`、`knowledge_evaluation_cases`、`knowledge_evaluation_runs` 和 `knowledge_evaluation_run_cases`，支持把知识库问题沉淀为可重复运行的检索评测集。
- `POST /api/tenants/{tenant_id}/knowledge-documents` 只有 `owner/admin` 可用，坐席不能直接导入正式文档。
- `GET /api/knowledge-documents/{document_id}/chunks` 返回 chunk 内容、位置、source uri、token 统计和 citation。
- `POST /api/tenants/{tenant_id}/knowledge-document-searches` 返回 chunk 级可溯源检索结果，模式为 `hybrid_bm25_vector_rerank_v1`。
- 新增 `0011_knowledge_embedding_index` 迁移，给 chunk 增加 embedding vector、provider、model、dimension、vector store 和 index status 元数据；PostgreSQL 下会尝试启用 `vector` 扩展。
- 新增 `0012_knowledge_pgvector` 迁移，PostgreSQL 下增加 `embedding_pgvector vector` 原生列和 pgvector scope index；SQLite 下保持 no-op。
- 新增 `POST /api/tenants/{tenant_id}/knowledge-vector-index/rebuilds`，owner/admin 可重建指定文档或指定状态下的 chunk embedding/vector index，并写入审计事件 `knowledge_vector_index.rebuilt`。
- 新增 `0013_embedding_smoke` 迁移和 `knowledge_embedding_provider_smoke_runs` 表，保存 provider、model、输入 hash、字符数、估算 tokens、耗时、估算成本、币种、质量检查和响应 usage 摘要，不保存 sample 原文。
- 新增 `POST /api/tenants/{tenant_id}/knowledge-embedding-provider-smoke-runs`，owner/admin 可运行 embedding provider smoke；deterministic provider 可直接跑，OpenAI-compatible 外部 provider 必须显式传 `allow_external_call=true` 才会调用。
- 新增 `0014_vector_index_plan` 迁移和 `knowledge_vector_index_plans` 表，保存 HNSW/IVFFlat/Exact 策略选择、DDL dry-run、rollback、预计构建窗口、内存估算、query options、安全检查和审计记录。
- 新增 `POST /api/tenants/{tenant_id}/knowledge-vector-index/plans`，owner/admin 可创建向量索引策略计划；默认 dry-run，不执行真实 `CREATE INDEX`，非 PostgreSQL 环境会记录 blocked 计划而不是静默执行。
- P2-18H 第二片新增 `scripts/smoke_pgvector_ann_indexes.py`，在本地 PostgreSQL/pgvector 上创建独立 smoke 表，真实构建 HNSW/IVFFlat 索引，比较 exact scan 与 ANN top-k 的 `recall_at_k`、查询耗时、构建耗时和 planner 结果，最后默认 `DROP TABLE IF EXISTS` 清理；该脚本没有外部模型调用，没有切换应用查询路径。
- 显式配置 `KNOWLEDGE_VECTOR_STORE=postgres_pgvector_store_v1` 时，检索后端为 `postgres_pgvector_exact_cosine_v1`；非 PostgreSQL 环境会返回 503，不静默 fallback 到 JSON vector。
- 默认 `KNOWLEDGE_EMBEDDING_PROVIDER=deterministic_local`，用本地 hash embedding 生成可测试稠密向量；显式配置 `openai_compatible` 但缺少 API key/base 时会拒绝导入或检索，不会静默 fallback；provider smoke 响应只返回 hash、成本和质量摘要，不回显原文。
- 当前 reranker 为 `lexical_overlap_reranker_v1`，用于把 BM25、向量相似度和词面覆盖合并为可解释分数；它不是神经重排模型。
- `POST /api/tenants/{tenant_id}/knowledge-evaluation-sets` 只有 `owner/admin` 可用，可一次性创建评测集和题目。
- `POST /api/knowledge-evaluation-sets/{evaluation_set_id}/runs` 运行文档检索评测，保存逐题结果和汇总指标。
- ReplyOrchestrator 新增 `document_rag` 模式，可把文档 chunk 作为证据写入 workflow state。
- 前端新增“知识文档运营”面板：owner/admin 可以从工作台导入纯文本知识文档，坐席可查看已索引文档、预览 chunk、运行文档片段检索并查看引用来源。
- 前端新增“知识评测与质量”面板：owner/admin 可以用 `问题 | 期望词 | 来源链接` 的轻量格式创建评测集，运行后查看命中率、引用覆盖、期望词覆盖、需复盘题数、检索模式、向量引擎、逐题结果和最近运行历史；历史列表只展示摘要，点击后才读取运行详情；载入某次运行后可下载默认脱敏的 Markdown 报告或 CSV 逐题表。
- 浏览器验收截图：
  - `/Users/ericlee/Desktop/肥肥lu/lite_a_customer_service/output/playwright/standard-ops-p2-18b-knowledge-documents-panel.png`
  - `/Users/ericlee/Desktop/肥肥lu/lite_a_customer_service/output/playwright/standard-ops-p2-18b-knowledge-documents-panel-mobile.png`
  - `/Users/ericlee/Desktop/肥肥lu/lite_a_customer_service/output/playwright/standard-ops-p2-18d-knowledge-evaluation-desktop.png`
  - `/Users/ericlee/Desktop/肥肥lu/lite_a_customer_service/output/playwright/standard-ops-p2-18d-knowledge-evaluation-mobile.png`
- 当前评测指标包括 `hit_rate`、`citation_coverage`、`expected_term_coverage`、`average_confidence`、`needs_review_cases`、`full_evidence_recall_at_5`、`citation_precision`、`human_review_correctness` 和 `knowledge_gap_rate`；它评测的是检索证据和审核门禁，不评测生成答案，所以 `unsupported_answer_rate=null` 是有意边界。
- 当前仍不是完整 RAG：pgvector 目前已具备 exact cosine 查询路径、HNSW/IVFFlat 策略计划和本地独立 smoke 表 ANN 建索引验证，但还没有在 `knowledge_document_chunks` 生产路径执行 ANN 索引，也没有把应用检索查询切到 ANN；provider smoke 只证明 provider 可调用、返回向量、成本和耗时可记录，不证明语义召回质量；没有经真实题库评测的语义 embedding 模型、没有神经重排器、没有文档解析器、没有批量文件上传，也没有真实客户 50-100 题评测集。演示身份无 token 时只能预览面板，正式导入、检索、评测、provider smoke 和索引计划仍需登录 token。

阶段 2 自检：

```bash
python3 standard_ops/scripts/check_stage2_workflow.py
python3 standard_ops/scripts/check_stage2_orchestrator.py
python3 standard_ops/scripts/check_stage2_knowledge.py
python3 standard_ops/scripts/check_stage2_outbox.py
python3 standard_ops/scripts/check_stage2_send_attempts.py
python3 standard_ops/scripts/check_stage2_channel_connectors.py
python3 standard_ops/scripts/check_stage2_channel_webhooks.py
python3 standard_ops/scripts/check_stage2_trusted_inbound_worker.py
python3 standard_ops/scripts/check_stage2_delivery_failures.py
python3 standard_ops/scripts/check_stage2_outbox_delivery_queue.py
python3 standard_ops/scripts/check_stage2_knowledge_documents.py
python3 standard_ops/scripts/check_stage2_knowledge_embedding_index.py
python3 standard_ops/scripts/check_stage2_knowledge_embedding_provider_smoke.py
python3 standard_ops/scripts/check_stage2_knowledge_pgvector.py
python3 standard_ops/scripts/check_stage2_knowledge_vector_index_strategy.py
python3 standard_ops/scripts/check_stage2_pgvector_ann_smoke.py
python3 standard_ops/scripts/check_stage2_model_routing.py
python3 standard_ops/scripts/check_stage2_customer_service_evaluation.py
python3 standard_ops/scripts/check_stage2_bailian_chat_smoke.py
python3 standard_ops/scripts/check_stage2_knowledge_document_frontend.py
python3 standard_ops/scripts/check_stage2_knowledge_evaluations.py
python3 standard_ops/scripts/check_stage2_knowledge_evaluation_frontend.py
python3 standard_ops/scripts/check_stage2_frontend_ops.py
python3 standard_ops/scripts/check_stage2_outbox_worker.py
cd standard_ops/backend
. .venv/bin/activate
pytest tests/test_workflows_api.py
pytest tests/test_reply_orchestrator_api.py
pytest tests/test_knowledge_api.py
pytest tests/test_outbox_api.py
pytest tests/test_channel_connectors_api.py
pytest tests/test_channel_webhooks_api.py
pytest tests/test_trusted_inbound_worker_api.py
pytest tests/test_delivery_failure_reviews_api.py
pytest tests/test_outbox_delivery_queue_api.py
pytest tests/test_knowledge_documents_api.py
pytest tests/test_knowledge_evaluations_api.py
pytest tests/test_knowledge_vector_index_api.py
pytest tests/test_knowledge_vector_index_strategy_api.py
pytest tests/test_knowledge_embedding_provider_smoke_api.py
pytest tests/test_bailian_chat_smoke_script.py
pytest
```

## 2026-07-04：H2W-6B 受控更新计划

H2W-6B 已把售后处理单与签名更新中心连接起来：

- 后端新增处理单生成受控更新计划接口。
- 前端售后接收台可选择已暂存签名更新包生成或刷新计划。
- 计划会展示签名包状态、预检摘要、本地备份摘要和生命周期步骤。
- 应用和回滚仍必须在签名更新中心由客户管理员手动执行。
- 程序包继续只支持演练计划，不直接替换程序文件。
- 真实外发继续关闭，不触达微信、抖音、淘宝、京东、拼多多等外部平台。

## 2026-07-04：H2W-7A 检索与成本治理第一片

H2W-7A 已完成只读治理摘要第一片：

- 后端新增 `GET /api/tenants/{tenant_id}/rag-cost-governance-summary`。
- 前端模型路由页新增“检索与成本治理”区域，展示知识规模、向量与评测摘要、H2W7 门禁和下一步。
- 当前只证明治理状态可见，不代表完整生产级 RAG、完整模型成本报表或真实渠道外发已经完成。
- 下一步优先补模型调用成本台账、最终回答引用溯源、预算降级和生产级向量库验收。

## 2026-07-04：H2W-11A 负责人真实登录端到端演练第一片

H2W-11A 已完成受控试点演练的第一条完整链路：

- 新增 `scripts/check_p3_06u_26h2w11a_owner_rehearsal.py`。
- 新增 `backend/tests/test_p3_06u_26h2w11a_owner_rehearsal_script.py`。
- 空库创建首任负责人，再通过 `/api/auth/login` 真实密码登录，不使用开发免登录。
- 导入 7 份客户知识包模板文档，生成 14 个 chunk。
- 导入 62 条客户式脱敏题库，运行客服检索评测。
- 采集 62 条最终答案样本，写入 62 条事实性/引用/禁用承诺/转人工标签。
- 导出脱敏评测报告、最终答案标签 CSV 和客户质量报告 HTML。
- 写入本地质量报告签收记录；该记录不是电子签章或合同签收。

验证：

```bash
.venv/bin/pytest backend/tests/test_p3_06u_26h2w11a_owner_rehearsal_script.py -q
.venv/bin/python scripts/check_p3_06u_26h2w11a_owner_rehearsal.py
```

证据：

- `output/p3_06u_26h2w11a_owner_rehearsal/summary.json`
- `output/p3_06u_26h2w11a_owner_rehearsal/customer_service_eval_run_1_review.md`
- `output/p3_06u_26h2w11a_owner_rehearsal/customer_service_eval_run_1_cases.csv`
- `output/p3_06u_26h2w11a_owner_rehearsal/customer_service_eval_run_1_final_answer_labels.csv`
- `output/p3_06u_26h2w11a_owner_rehearsal/wanfa-customer-quality-report-1-2026-07.html`

真实结论：

- 链路结果 `status=completed`、`ready_for_h2w11b=true`、`blockers=[]`。
- 质量报告状态为 `repair_required`，不能写成正式试点已签收。
- `expected_term_coverage=0.0484`、`human_review_correctness=0.4194`、`final_answer_factuality_rate=0.0`。
- 下一步进入 H2W-11B：修复知识包、题库标准答案和回复策略，再复跑 H2W-11A。

## 2026-07-04：H2W-11B 质量修复与知识包对齐

H2W-11B 已完成知识包质量修复，并复跑 H2W-11A：

- 新增 `scripts/check_p3_06u_26h2w11b_quality_repair.py`。
- 新增 `backend/tests/test_p3_06u_26h2w11b_quality_repair_script.py`。
- 新增阶段文档 `docs/P3-06U-26H2W11B_QUALITY_REPAIR_AND_KNOWLEDGE_ALIGNMENT.md`。
- 生成修复版知识包 `evals/p3_06u_26h2w11b_repaired_customer_knowledge_package.json`。
- 修复版知识包从 62 条脱敏题库生成 62 张题库覆盖卡，不包含原始客户问题全文。
- 修正 H2W-11A 标签口径：正确转人工样本标为 `not_applicable`，不计入最终答案事实性分母。
- 修正后端标签语义：`not_applicable` 仍算已标注，但不参与事实性打分。

验证：

```bash
.venv/bin/pytest backend/tests/test_knowledge_evaluations_api.py backend/tests/test_p3_06u_26h2w11a_owner_rehearsal_script.py backend/tests/test_p3_06u_26h2w11b_quality_repair_script.py -q
.venv/bin/python scripts/check_p3_06u_26h2w11b_quality_repair.py
```

证据：

- `output/p3_06u_26h2w11b_quality_repair/summary.json`
- `output/p3_06u_26h2w11b_quality_repair/repaired_h2w11a_rerun/summary.json`
- `output/p3_06u_26h2w11b_quality_repair/repaired_h2w11a_rerun/customer_service_eval_run_1_review.md`
- `output/p3_06u_26h2w11b_quality_repair/repaired_h2w11a_rerun/customer_service_eval_run_1_cases.csv`
- `output/p3_06u_26h2w11b_quality_repair/repaired_h2w11a_rerun/customer_service_eval_run_1_final_answer_labels.csv`
- `output/p3_06u_26h2w11b_quality_repair/repaired_h2w11a_rerun/wanfa-customer-quality-report-1-2026-07.html`

真实结果：

- H2W-11B 输出 `status=completed`、`blockers=[]`。
- 修复前：`expected_term_coverage=0.0484`、`human_review_correctness=0.4194`、`final_answer_factuality_rate=0.0`、`report_status=repair_required`、`report_confidence_score=55`。
- 修复后：`expected_term_coverage=1.0`、`human_review_correctness=1.0`、`final_answer_factuality_rate=1.0`、`report_status=controlled_trial_ready`、`report_confidence_score=90`。
- 逐题结果：37 条 passed，25 条 needs_review；最终答案标签为 37 条 correct、25 条 not_applicable。

边界：

- 仍未使用真实客户原始数据。
- 仍未调用真实大模型 provider。
- 仍未打开真实外发。
- 仍未接真实企业微信、公众号、抖音、淘宝、京东或拼多多。
- `controlled_trial_ready` 只表示本地受控演练达标，不是生产上线或合同验收。

下一步：进入 H2W-11D，把修复版知识包、质量报告和知识发布流程映射到前端客户可操作路径。

## 2026-07-04：H2W-11D 客户知识发布闭环前端路径

H2W-11D 已把 H2W-11B 修复后的知识包、客户质量报告和知识发布流程映射到客户可操作的前端路径：

- `frontend/src/App.tsx` 的知识库运营页新增“客户知识发布闭环”面板。
- 面板按 `导入 → 预检 → 发布 → 回归评测 → 报告 → 签收` 展示当前状态。
- 面板读取真实状态：客户资料转换数量、更新包预检/导入结果、可发布文档、最近知识评测、客户质量报告、客户确认记录。
- 面板按钮接入现有真实动作：转换客户资料、预检更新包、导入本地知识库、发布前试跑、确认发布、进入知识评测、查看质量报告。
- 新增 `scripts/check_p3_06u_26h2w11d_customer_knowledge_publish_path.py`。
- 新增 `backend/tests/test_p3_06u_26h2w11d_customer_knowledge_publish_path.py`。
- 新增阶段文档 `docs/P3-06U-26H2W11D_CUSTOMER_KNOWLEDGE_PUBLISH_PATH.md`。

验证：

```bash
python3 scripts/check_p3_06u_26h2w11d_customer_knowledge_publish_path.py
backend/.venv/bin/pytest backend/tests/test_p3_06u_26h2w11d_customer_knowledge_publish_path.py -q
cd frontend && npm run typecheck
cd frontend && npm run build
python3 scripts/check_p3_06u_26h2w3b_customer_knowledge_flow.py
python3 scripts/check_p3_06u_26h2w3c_customer_knowledge_intake.py
python3 scripts/check_p3_06u_26d_knowledge_three_pages.py
node scripts/check_p3_06u_26h2w0_knowledge_operations_owner_login.mjs
```

真实结果：

- H2W-11D 静态门禁输出 `status=passed`、`blockers=[]`。
- 前端路径包含 7 个真实动作入口。
- H2W-11B 证据仍为 `status=completed`、`report_status=controlled_trial_ready`、`report_confidence_score=90`、`case_card_count=62`。
- owner-login 知识操作浏览器 smoke 通过，证据目录为 `output/p3_06u_26h2w0_knowledge_operations_owner_login/`。

边界：

- 真实外发继续关闭。
- 本地签收记录不是正式电子签章或合同签收。
- 当前知识评测仍不是完整线上客服准确率。
- 本轮没有调用真实大模型 provider，没有接真实微信、企微、抖音、淘宝、京东或拼多多。

下一步：进入 H2W-11E，做负责人真实登录下的知识库运营页逐按钮/逐流程客户试用验收，重点查空按钮、重复入口、客户术语和知识三页去重。

## 2026-07-04：H2W 封版候选非企业主线门禁

本轮按“暂缓企业渠道、不启用真实外发、不把内部演练写成客户签收”的边界，完成 H2W-7D-runtime、H2W-FE3、H2W-PACK1、H2W-MODEL1、H2W-TRIAL1 五条非企业主线的门禁落地。

新增：

- `deploy/customer.env.example`：客户本地试点包环境模板，默认关闭开发 bootstrap、关闭真实外发，不内置默认管理员密码。
- `scripts/check_p3_06u_26h2w7d_runtime_pgvector_rehearsal.py`
- `scripts/check_p3_06u_26h2w_fe3_frontend_browser_workflow_qa.py`
- `scripts/check_p3_06u_26h2w_pack1_local_delivery_rehearsal.py`
- `scripts/check_p3_06u_26h2w_model1_bailian_cost_sample.py`
- `scripts/check_p3_06u_26h2w_trial1_internal_100q_rehearsal_report.py`
- `backend/tests/test_p3_06u_26h2w_sealed_pilot_package_gates.py`

真实结果：

- H2W-7D-runtime：`blocked_waiting_for_pgvector_runtime`。Compose 和静态 pgvector 证据 ready，但当前 Docker daemon 未启动，且 shell 未配置 PostgreSQL/pgvector runtime 环境。
- H2W-FE3：`passed`。前端 FE2、负责人登录、知识维护、本地维护 smoke 均通过；多渠道对话台没有命中“待审核/待发送/AI 预备”等干扰文案。
- H2W-PACK1：`passed_local_package_candidate_with_runtime_pending`。本地试点包候选成立，但未完成真实空库启动和 pgvector runtime rehearsal。
- H2W-MODEL1：`guarded_external_call_not_allowed`。默认未调用百炼/千问，不计真实模型成本；后续必须显式 `--allow-external-call` 才能跑 5-10 条小样本。
- H2W-TRIAL1：`passed_internal_rehearsal_report_with_open_gaps`。内部 100 题完整演练报告生成；内部质量报告候选 true，客户质量报告候选 false，正式准确率签收 false。

验证：

```bash
backend/.venv/bin/python -m py_compile scripts/check_p3_06u_26h2w7d_runtime_pgvector_rehearsal.py scripts/check_p3_06u_26h2w_fe3_frontend_browser_workflow_qa.py scripts/check_p3_06u_26h2w_pack1_local_delivery_rehearsal.py scripts/check_p3_06u_26h2w_model1_bailian_cost_sample.py scripts/check_p3_06u_26h2w_trial1_internal_100q_rehearsal_report.py
backend/.venv/bin/python -m pytest backend/tests/test_p3_06u_26h2w_sealed_pilot_package_gates.py backend/tests/test_p3_06u_26h2w_next_stage_gates.py backend/tests/test_p3_06u_26h2w11m_customer_confirmation_import_gate.py backend/tests/test_p3_06u_26h2w11a_owner_rehearsal_script.py backend/tests/test_p3_06u_26h2w11b_quality_repair_script.py backend/tests/test_p3_06u_26h2w11j_gap_final_answer_rehearsal.py -q
cd frontend && npm run typecheck
cd frontend && npm run build
```

验证结果：

- 新增封版包门禁测试：`3 passed`。
- 相关后端回归：`12 passed`，仅有既有 StarletteDeprecationWarning。
- 前端 `typecheck` 通过。
- 前端 `build` 通过；Vite 仍提示部分 chunk 超过 500 kB，这是构建体积提醒，不是失败。

边界：

- 本轮不推进企业微信、微信客服、抖音、淘宝、京东、拼多多等真实渠道接入。
- 本轮不启用真实外发。
- 本轮不调用真实付费模型。
- 内部 100 题只用于工程演练，不代表真实客户题库。
- 当前状态可作为“小微企业本地受控试点包候选”，不能写成全渠道自动回复正式上线或成熟商用封版。

## 2026-07-04：H2W runtime 与模型小样本收敛

本轮继续推进上轮两个开放缺口，已把 PostgreSQL + pgvector runtime 和百炼/千问小样本成本验证补齐。

最新状态：

- H2W-7D-runtime：`ready_for_runtime_rehearsal`。
- H2W-PACK1：`passed_local_package_runtime_rehearsal_ready`。
- H2W-MODEL1：`passed_real_small_sample_cost_rehearsal`。
- H2W-TRIAL1：`passed_internal_rehearsal_report`，当前 `open_gaps=[]`。

运行环境：

- Docker Desktop daemon 已启动，版本 `29.5.3`。
- `deploy-postgres-1` 使用 `pgvector/pgvector:pg16`，状态 healthy。
- `deploy-redis-1` 使用 `redis:7-alpine`，状态 healthy。

pgvector runtime 证据：

- pgvector 版本：`0.8.2`。
- HNSW：`recall_at_k=1.0`，ANN 查询约 `1.887ms`。
- IVFFlat：`recall_at_k=1.0`，ANN 查询约 `1.474ms`。
- 证据文件：`output/p3_06u_26h2w7d_runtime_pgvector_rehearsal/pgvector_ann_smoke.json`。

模型小样本证据：

- provider：百炼。
- 样本数：5。
- 成功：5。
- 失败：0。
- 平均延迟：约 `1693.324ms`。
- tokens/字符量合计：`1064`。
- 原始文本未写入 summary，真实外发仍关闭。

边界：

- 本轮仍不是客户验收。
- 内部 100 题仍不是客户真实题库。
- 真实平台外发仍关闭。
- 企业微信、微信客服、抖音、淘宝、京东、拼多多真实接入仍未推进。
- 当前结论是“内部封版候选演练通过”，不是全渠道商用上线。

## 2026-07-05：H2W-KB1 客户专属知识包导入与签收 rehearsal

本轮继续 PACK5 之后的非企业主线，补齐“客户资料如何进入知识库”的工程证据。新增 KB1 客户专属知识包 rehearsal，使用内部脱敏资料包验证预检、导入、查询和回滚，不使用真实客户原始数据，不打开真实外发，不调用模型 provider。

新增：

- `scripts/check_p3_06u_26h2w_kb1_customer_specific_knowledge_package_rehearsal.py`
- `evals/p3_06u_26h2w_kb1_customer_specific_knowledge_package_rehearsal.json`
- `docs/P3-06U-26H2W_KB1_CUSTOMER_SPECIFIC_KNOWLEDGE_PACKAGE_REHEARSAL.md`
- `output/p3_06u_26h2w_kb1_customer_specific_knowledge_package_rehearsal/summary.json`

真实结果：

- KB1 状态：`ready_for_customer_specific_knowledge_package_rehearsal`。
- 资料包包含 3 个业务对象、8 条对象知识卡、5 份来源文档、1 个回归题集、8 条回归题。
- 知识类型覆盖：`business_object`、`standard_qa`、`process_policy`、`forbidden_commitment`、`handoff_rule`。
- 后端真实接口 rehearsal 已完成：首任负责人创建、登录、知识包预检、导入、查询、回滚。
- 预检和导入均为 17 项 create；导入后 5 份文档、3 个业务对象、1 个回归题集落库；回滚后 active 文档和题集均为 0。

验证：

```bash
backend/.venv/bin/python -m py_compile scripts/check_p3_06u_26h2w_kb1_customer_specific_knowledge_package_rehearsal.py
backend/.venv/bin/python scripts/check_p3_06u_26h2w_kb1_customer_specific_knowledge_package_rehearsal.py
backend/.venv/bin/python -m pytest backend/tests/test_p3_06u_26h2w_sealed_pilot_package_gates.py -q
```

验证结果：KB1 脚本通过，封版包门禁回归 `16 passed`，仅有既有 StarletteDeprecationWarning。

边界：

- 当前仍不是客户专属知识库正式签收。
- 当前仍不是客户真实题库准确率验收。
- 当前仍不是完整桌面安装器、生产 SLA 或真实渠道上线。

## 2026-07-05：H2W-KB2 客户专属知识包复测报告与签收模板

本轮继续 KB1 和 OPS1 之后的非企业主线，把客户专属知识包导入、查询、回滚证据整理为可给业务负责人确认的复测报告和签收模板。KB2 不使用真实客户数据，不打开真实外发，不调用模型 provider，不把内部演练写成正式客户签收。

新增：

- `scripts/check_p3_06u_26h2w_kb2_post_import_retest_and_signoff_template.py`
- `docs/P3-06U-26H2W_KB2_POST_IMPORT_RETEST_AND_SIGNOFF_TEMPLATE.md`
- `output/p3_06u_26h2w_kb2_post_import_retest_and_signoff_template/summary.json`
- `output/p3_06u_26h2w_kb2_post_import_retest_and_signoff_template/post_import_retest_report.md`
- `output/p3_06u_26h2w_kb2_post_import_retest_and_signoff_template/customer_knowledge_retest_signoff_template.csv`

真实结果：

- KB2 状态：`ready_for_customer_specific_knowledge_retest_template`。
- 复测范围承接 KB1：3 个业务对象、8 条对象知识卡、5 份来源文档、8 条回归题。
- 签收模板包含 9 项确认项，覆盖业务对象、来源文档、标准问答、流程政策、禁用承诺、转人工规则、回归题、真实外发关闭和导入回滚证据。
- `filled_customer_confirmation_count=0`，确认人、确认时间、客户意见全部为空。

验证：

```bash
backend/.venv/bin/python -m py_compile scripts/check_p3_06u_26h2w_kb2_post_import_retest_and_signoff_template.py
backend/.venv/bin/python scripts/check_p3_06u_26h2w_kb2_post_import_retest_and_signoff_template.py
backend/.venv/bin/python -m pytest backend/tests/test_p3_06u_26h2w_sealed_pilot_package_gates.py -q
```

验证结果：KB2 脚本通过，封版包门禁回归 `22 passed`，仅有既有 StarletteDeprecationWarning。

边界：

- 当前仍不是正式客户签收。
- 当前仍不是客户专属知识库正式启用。
- 当前仍不是真实客户题库准确率验收。
- 当前仍不是真实平台外发、企业渠道上线、生产 SLA 或完整桌面安装器。

## 2026-07-05：H2W-FE6 / INSTALL4 / KB3 / PILOT6 本地试用包候选刷新

本轮承接 FE5、INSTALL3、KB2 和 PILOT5，不横向扩真实渠道，不打开真实外发，只把共创客户本地试用包候选补到最新前端、安装体验、知识中心和交付档案一致。

新增：

- `scripts/check_p3_06u_26h2w_fe6_latest_frontend_browser_qa.mjs`
- `scripts/check_p3_06u_26h2w_install4_packaging_experience_gate.py`
- `scripts/check_p3_06u_26h2w_kb3_customer_knowledge_center.py`
- `scripts/check_p3_06u_26h2w_pilot6_handoff_archive_refresh.py`
- `docs/P3-06U-26H2W_FE6_LATEST_FRONTEND_BROWSER_QA.md`
- `docs/P3-06U-26H2W_INSTALL4_PACKAGING_EXPERIENCE_GATE.md`
- `docs/P3-06U-26H2W_KB3_CUSTOMER_KNOWLEDGE_CENTER.md`
- `docs/P3-06U-26H2W_PILOT6_HANDOFF_ARCHIVE_REFRESH.md`
- `installers/INSTALL4_EXPERIENCE_CHECKLIST.md`
- `installers/macos/APP_ICON_NOTES.md`
- `installers/windows/APP_ICON_NOTES.md`
- `evals/p3_06u_26h2w_kb3_customer_knowledge_center_template.csv`
- `output/p3_06u_26h2w_pilot6_handoff_archive_refresh/pilot_handoff_archive_candidate_v1.zip`

真实结果：

- FE6：`passed_latest_frontend_browser_qa`。
- INSTALL4：`native_packaging_experience_candidate_ready`。
- KB3：`customer_knowledge_center_productized`。
- PILOT6：`pilot_handoff_archive_candidate_v1`。

验证：

```bash
node --check scripts/check_p3_06u_26h2w_fe6_latest_frontend_browser_qa.mjs
backend/.venv/bin/python -m py_compile scripts/check_p3_06u_26h2w_install4_packaging_experience_gate.py scripts/check_p3_06u_26h2w_kb3_customer_knowledge_center.py scripts/check_p3_06u_26h2w_pilot6_handoff_archive_refresh.py
npm run typecheck
npm run build
node scripts/check_p3_06u_26h2w_fe6_latest_frontend_browser_qa.mjs
backend/.venv/bin/python scripts/check_p3_06u_26h2w_install4_packaging_experience_gate.py
backend/.venv/bin/python scripts/check_p3_06u_26h2w_kb3_customer_knowledge_center.py
backend/.venv/bin/python scripts/check_p3_06u_26h2w_pilot6_handoff_archive_refresh.py
KNOWLEDGE_EMBEDDING_PROVIDER=deterministic_local KNOWLEDGE_EMBEDDING_MODEL= backend/.venv/bin/python -m pytest backend/tests/test_p3_06u_26h2w_sealed_pilot_package_gates.py backend/tests/test_rag_cost_governance_api.py backend/tests/test_channel_connectors_api.py backend/tests/test_p3_06f_ops_alert_rules_api.py backend/tests/test_knowledge_evaluations_api.py -q
```

验证结果：FE6/INSTALL4/KB3/PILOT6 门禁通过，前端 typecheck/build 通过，相关后端回归 `57 passed`，仅有既有 `StarletteDeprecationWarning`。

边界：

- 当前仍不是正式客户签收。
- 当前仍不是客户真实题库准确率验收。
- 当前仍不是真实平台外发、企业渠道上线、生产 SLA 或正式签名安装包。

## 2026-07-05：H2W-DATA2R4 资料包预检入口与 FE9/FE10 解阻

本轮继续围绕五大缺口收束，不推进真实渠道，不打开真实外发。新增客户资料包预检能力，让实施人员可以在应用内先校验知识资料 CSV、试跑问题 CSV 和资料说明 JSON，再决定是否放入 DATA2 固定接收目录。

新增：

- `POST /api/tenants/{tenant_id}/customer-materials/precheck`
- `scripts/check_p3_06u_26h2w_data2r4_material_precheck_api_ui.py`
- `docs/P3-06U-26H2W_DATA2R4_MATERIAL_PRECHECK_API_UI.md`
- `output/p3_06u_26h2w_data2r4_material_precheck_api_ui/summary.json`

真实结果：

- DATA2R4 状态：`material_precheck_api_ui_ready`。
- 预检接口只做内存校验，不持久化原始客户资料。
- 试点准备页新增“资料预检”入口，展示资料行数、试跑问题数、知识类型和阻断项。
- 修正试点准备页客户可见工程词后，FE9 从 `blocked` 变为 `waiting_for_real_customer_materials`，FE10 从 `blocked` 变为 `frontend_final_product_polish_ready`。
- PACK10 最新状态：`blocked_waiting_real_customer_materials`，`blockers=[]`；当前只因真实客户脱敏资料未回传而不能生成客户数据版交付档案。

验证：

```bash
npm run typecheck && npm run build
PYTHONPATH=backend backend/.venv/bin/python -m pytest backend/tests/test_pilot_api.py backend/tests/test_p3_06u_26h2w_sealed_pilot_package_gates.py -q
python3 scripts/check_p3_06u_26h2w_data2r4_material_precheck_api_ui.py
node scripts/check_p3_06u_26h2w_fe9_customer_data_browser_qa.mjs
node scripts/check_p3_06u_26h2w_fe10_final_product_polish_gate.mjs
python3 scripts/check_p3_06u_26h2w_pack10_customer_data_trial_package.py
```

验证结果：前端 typecheck/build 通过；后端相关回归 `46 passed`，仅有既有 Starlette deprecation warning；DATA2R4、FE9、FE10、PACK10 门禁均按边界通过。

边界：

- 当前仍未收到真实客户资料，不能写成客户资料试跑完成。
- 当前仍不是正式客户签收、真实客户题库准确率验收、真实平台外发、企业渠道上线、生产 SLA 或正式签名安装包。

## 2026-07-05：H2W-DATA2R5 资料模板包与字段说明

本轮继续围绕真实资料等待态补客户自助准备能力，不推进真实渠道，不打开真实外发。新增资料模板包接口和试点准备页模板辅助区，让客户或实施人员可以下载三份模板、查看字段说明、填入样例并直接跑资料预检。

新增：

- `GET /api/tenants/{tenant_id}/customer-materials/template-package`
- `scripts/check_p3_06u_26h2w_data2r5_material_template_package.py`
- `docs/P3-06U-26H2W_DATA2R5_MATERIAL_TEMPLATE_PACKAGE.md`
- `output/p3_06u_26h2w_data2r5_material_template_package/summary.json`

真实结果：

- DATA2R5 状态：`material_template_package_ready`。
- 前端“试点准备 -> 资料预检”新增加载资料模板、填入示例资料、下载三份模板和字段说明。
- 示例资料可用于熟悉格式和跑预检，但不代表真实客户资料已就绪。
- PACK10 最新状态仍为 `blocked_waiting_real_customer_materials`，`blockers=[]`。

验证：

```bash
PYTHONPATH=backend backend/.venv/bin/python -m pytest backend/tests/test_pilot_api.py backend/tests/test_p3_06u_26h2w_sealed_pilot_package_gates.py -q
cd frontend && npm run typecheck && npm run build
python3 scripts/check_p3_06u_26h2w_data2r5_material_template_package.py
node scripts/check_p3_06u_26h2w_fe9_customer_data_browser_qa.mjs
node scripts/check_p3_06u_26h2w_fe10_final_product_polish_gate.mjs
python3 scripts/check_p3_06u_26h2w_pack10_customer_data_trial_package.py
```

验证结果：后端相关回归 `47 passed`，仅有既有 Starlette deprecation warning；前端 typecheck/build 通过；DATA2R5、FE9、FE10、PACK10 门禁均按边界通过。

边界：

- 模板包不保存原始客户资料。
- 示例资料不标记真实客户资料 ready。
- 当前仍不是正式客户签收、真实外发、真实企业渠道上线、生产 SLA 或正式签名安装包。

## 2026-07-06：H2W-NC15 PostgreSQL 正式恢复 SOP 与停机编排门禁

本轮在 NC14 的正式恢复执行 dry-run 之后，补齐 PostgreSQL 正式恢复 SOP 与停机编排门禁登记能力。它只登记停机窗口、人工确认、恢复前二次备份、恢复后健康检查、回滚路径和命令预览 hash，不执行真实恢复。

新增：

- `POST /api/tenants/{tenant_id}/local-backups/postgres-formal-restore-runbook`
- `LocalPostgresFormalRestoreRunbookRegister`
- `register_postgres_formal_restore_runbook`
- `scripts/check_p3_06u_26h2w_nc15_formal_restore_runbook.py`
- `docs/P3-06U-26H2W_NC15_FORMAL_RESTORE_RUNBOOK.md`
- `output/p3_06u_26h2w_nc15_formal_restore_runbook/summary.json`

真实结果：

- NC15 状态：`formal_restore_runbook_ready_no_live_restore`。
- 服务端要求同一备份记录已经具备 `last_formal_restore_execution_dry_run`。
- 服务端会复核命令预览 hash 与 NC14 一致。
- 本地维护 readiness 已纳入 `local_backup.postgres_formal_restore_runbook_registered`。
- `can_execute_restore_now=false`、`can_execute_restore_in_app=false`、`restore_execution_performed=false`。

验证：

```bash
backend/.venv/bin/python -m pytest backend/tests/test_local_backups_api.py -q
python3 -m py_compile scripts/check_p3_06u_26h2w_nc15_formal_restore_runbook.py
python3 scripts/check_p3_06u_26h2w_nc15_formal_restore_runbook.py
backend/.venv/bin/python -m pytest backend/tests/test_signed_update_packages_api.py backend/tests/test_local_backups_api.py backend/tests/test_local_maintenance_readiness_api.py -q
backend/.venv/bin/python -m pytest backend/tests/test_p3_06u_26h2w_sealed_pilot_package_gates.py -q
```

验证结果：

- 本地备份 API：`16 passed`。
- 相邻本地维护/签名更新/备份回归：`32 passed`。
- 封版门禁回归：`49 passed`。
- NC15 门禁输出 `formal_restore_runbook_ready_no_live_restore`。

边界：

- NC15 仍不是正式恢复执行工具。
- 不执行 `pg_restore`，不替换真实数据库，不保存 dump 文件本体，不保存原始恢复命令，不打开真实外发。
- 真实恢复只能在客户确认后的停机窗口里，由人工按 SOP 在线下执行。
- 真实客户资料版封包、客户真实红队闭环、完整 Memory Mesh 图谱、真实渠道、生产 SLA、签名安装包和移动端仍未完成。

## 2026-07-06：H2W-NC18 红队事实账本导入与前端观测卡片联动

本轮在 NC17 内部红队样本包之后，把红队样本和影子标签导入隔离数据库，落成 `knowledge_evaluation_sets`、`knowledge_evaluation_cases`、`knowledge_evaluation_runs`、`knowledge_evaluation_run_cases` 和 `pilot_readiness_facts`，再通过现有 `llm-ops-readiness` 服务读取这些数据库事实。

新增：

- `scripts/check_p3_06u_26h2w_nc18_redteam_fact_ingest.py`
- `backend/tests/test_p3_06u_26h2w_nc18_redteam_fact_ingest.py`
- `docs/P3-06U-26H2W_NC18_REDTEAM_FACT_INGEST.md`
- `output/p3_06u_26h2w_nc18_redteam_fact_ingest/summary.json`

同步修改：

- `backend/app/schemas/llm_ops.py`：红队 readiness 增加 `source`、`internal_sample_cases`、`internal_sample_only`。
- `backend/app/services/llm_ops.py`：红队 readiness 可识别内部样本来源，并在 gate evidence 中返回来源边界。
- `frontend/src/api/client.ts`、`frontend/src/App.tsx`：自动回复策略页“模型观测与红队”卡片展示题集来源和类目覆盖。

真实结果：

- NC18 状态：`redteam_fact_ingest_ready_internal_sample_visible_to_llm_ops`。
- 导入内部红队样本：25 条。
- 导入人工标签：25 条。
- `llm_ops_redteam.readiness=ready_for_controlled_pilot`。
- `internal_sample_only=true`。
- `raw_attack_vector_persisted=false`。
- 前端现有“模型观测与红队”卡片可显示安全题集、人工标签、题集来源和类目覆盖。

验证：

```bash
backend/.venv/bin/python -m pytest backend/tests/test_p3_06u_26h2w_nc18_redteam_fact_ingest.py -q
backend/.venv/bin/python -m pytest backend/tests/test_llm_ops_readiness_api.py -q
backend/.venv/bin/python scripts/check_p3_06u_26h2w_nc18_redteam_fact_ingest.py
npm --prefix frontend run typecheck
npm --prefix frontend run build
backend/.venv/bin/python -m pytest backend/tests/test_p3_06u_26h2w_nc17_redteam_shadow_trial.py -q
backend/.venv/bin/python scripts/check_p3_06u_26h2w_nc17_redteam_shadow_trial.py
backend/.venv/bin/python -m pytest backend/tests/test_p3_06u_26h2w_sealed_pilot_package_gates.py -q
```

验证结果：

- NC18 专项测试：`2 passed`。
- LLM Ops API 回归：`6 passed`。
- NC18 门禁输出 `redteam_fact_ingest_ready_internal_sample_visible_to_llm_ops`。
- 前端 typecheck/build 通过；Vite 仍有既有大 chunk warning。
- NC17 回归：`3 passed`。
- sealed pilot gates：`49 passed`。

边界：

- NC18 使用的是内部样本，不是客户真实红队题库。
- NC18 不调用真实模型，不打开真实外发，不推进真实渠道。
- NC18 不等于正式客户红队安全签收、真实客户安全报告、生产 SLA 或成熟全渠道商用客服发布。
