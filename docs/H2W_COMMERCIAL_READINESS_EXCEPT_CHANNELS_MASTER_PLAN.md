# H2W 非真实渠道闭环商用补全总纲

更新时间：2026-07-06

本文档用于回答一个具体问题：在暂时不推进企业微信、公众号、抖音、淘宝、京东、拼多多等真实渠道闭环和真实外发的前提下，当前智能客服系统还缺什么，接下来如何把它推进到“可给第一批共创客户本地试跑”的更可靠状态。

结论先写清楚：当前系统不是成熟商用全渠道客服。当前更准确的状态是“本地受控试跑候选”。若不接真实渠道，下一阶段目标应是“真实客户资料版本地试跑包候选”，不是“正式商用客服系统发布”。

## 2026-07-06 执行进度

- H2W-NC0 已完成：全量后端测试归零，旧静态门禁和月报边界文案已对齐，前端 typecheck/build 通过。
- H2W-NC1 已完成：`pilot-readiness` 客户资料 ready 已改为数据库事实链权威，工程 summary 只作为工程证据。
- H2W-NC2 已完成：客户模式安全硬化已落地，包含登录失败限速、首任负责人安全前置、诊断上传包大小/深度/schema 门禁、坏包拒收摘要存储、交付档案浏览器敏感文件排除。
- H2W-NC3 已完成：资料预检从一次性文本区升级为可追踪资料批次，前端可从本地 CSV/JSON 填入草稿并查看批次状态；批次列表只返回 hash、统计和状态，不返回客户原文或密钥。
- H2W-NC4 已完成：知识中心 v2 与 Memory Mesh 化第一片已落地，新增知识网络总览接口和前端三页统一证据链；当前完成的是只读证据链总览，不是完整图数据库式 Memory Mesh。
- H2W-NC5 已完成：生产级检索与评测治理第一轮收束已落地，新增 `production_readiness`，并把真实客户资料批次纳入生产检索切换硬门禁；当前 `production_retrieval_switch_allowed=false`，因为真实客户资料和真实资料链路重跑仍未 ready。
- H2W-NC6 已完成第一片：新增模型观测、成本与红队治理接口和前端卡片，当前 `status=llm_ops_observability_ready_not_redteam_complete`；模型成本与链路观测已接上，但红队题集和人工标签尚未完整闭环。
- H2W-NC7 已完成第一片：试点准备已提升为一级入口，质量复盘口径降级为试跑确认，账号与本地维护入口修复孤儿锚点，多渠道对话台和渠道边界通过前端产品化门禁；当前 `status=frontend_productization_customer_flow_ready_component_split_pending`。
- H2W-NC8 已完成第一片：本地启动、PostgreSQL 备份 dry-run、更新 apply 备份门禁和回滚边界已补强，当前 `status=local_install_backup_update_rollback_hardened_pg_script_ready`；NC10 已补服务端 PG manifest 登记能力，但客户现场 PostgreSQL 备份演练 manifest 仍待提供。
- H2W-NC9 已完成：非真实渠道版本地试跑包 v4 已生成，当前 `status=local_trial_package_v4_candidate_with_internal_sample`；档案位于 `output/p3_06u_26h2w_nc9_local_trial_package_v4/local_trial_package_v4_candidate.zip`，只代表内部样板本地试跑包候选。
- H2W-NC10 已完成第一片：PostgreSQL 备份证据登记接口、服务端校验、审计计数和门禁已落地，当前 `status=postgres_backup_evidence_registration_ready_waiting_customer_pg_run`；系统可以登记客户机 dry-run manifest，但客户现场实际 manifest 仍未提供。
- H2W-NC11 已完成第一片：PostgreSQL 恢复演练计划接口、服务端前置校验、审计计数和门禁已落地，当前 `status=postgres_restore_rehearsal_plan_ready_no_live_restore`；系统可以基于已登记 manifest 生成恢复演练计划，但不会执行 `pg_restore`，不会替换数据库。
- H2W-NC12 已完成第一片：PostgreSQL 临时库恢复演练脚本、manifest 登记接口、服务端校验、审计计数和门禁已落地，当前 `status=postgres_temp_restore_rehearsal_ready_waiting_customer_pg_run`；系统可以登记客户机把备份恢复到临时库并删除临时库后的 manifest，但不会服务端执行 `pg_restore`，不会替换真实数据库。
- H2W-NC13 已完成第一片：PostgreSQL 正式恢复前置门禁接口、服务端确认包校验、审计计数和门禁已落地，当前 `status=formal_restore_preflight_gate_ready_no_live_restore`；系统可以登记维护窗口、客户管理员确认、恢复前二次备份、健康检查和回滚计划，但不会执行 `pg_restore`，不会替换真实数据库，不提供应用内一键恢复。
- H2W-NC14 已完成第一片：PostgreSQL 正式恢复执行 dry-run 外壳、服务端执行计划登记接口、命令 hash 校验和门禁已落地，当前 `status=formal_restore_execution_dry_run_ready_no_live_restore`；系统可以登记客户机正式恢复执行计划 manifest，但只保存执行计划摘要和命令预览 hash，不保存原始恢复命令，不执行 `pg_restore`，不会替换真实数据库，不提供应用内一键恢复。
- H2W-NC15 已完成第一片：PostgreSQL 正式恢复 SOP 与停机编排门禁已落地，当前 `status=formal_restore_runbook_ready_no_live_restore`；系统可以登记恢复 SOP、停机顺序、二次备份要求、最终操作员确认、恢复后健康检查和回滚决策树，但仍不会执行 `pg_restore`，不会替换真实数据库。
- H2W-NC16 已完成第一片：红队闭环判定规则已落地，当前 `status=redteam_closure_gate_ready_internal_fixtures_only`；系统现在要求红队题集覆盖五类风险、全部活跃题有人工标签、失败样本逐条进入知识缺口或质量复盘，但这仍是内部 fixture 验证，不是客户真实红队安全签收。
- H2W-NC17 已完成第一片：红队题库与影子试跑标签包已落地，当前 `status=redteam_shadow_trial_internal_sample_ready_not_customer_security_signoff`；系统已有 25 条内部准真实红队样本和 25 条影子标签，五类风险各 5 条，全部样本禁止自动回复并转人工，但这仍是内部样本证据，不是客户真实红队安全签收。
- H2W-NC18 已完成第一片：红队事实账本导入与前端观测卡片联动已落地，当前 `status=redteam_fact_ingest_ready_internal_sample_visible_to_llm_ops`；系统可把 NC17 内部红队样本和影子标签导入隔离数据库事实账本，并由 `llm-ops-readiness` 和前端“模型观测与红队”卡片读取，但这仍是内部样本 rehearsal，不是客户真实红队安全签收。
- 当前仍未完成：真实客户资料版封包、客户现场 PostgreSQL 备份演练 manifest、客户现场 PostgreSQL 临时库恢复 manifest、客户现场 NC14/NC15 恢复执行与 runbook 证据、真实正式恢复执行、生产级知识导入体验、完整 Memory Mesh 图谱深化、真实客户红队题库与真实模型输出标签、前端大文件组件拆分、真实渠道闭环、真实外发、生产 SLA 和签名安装包。

## 一、当前真实状态

### 已经具备的能力

- 本地账号、租户、角色、登录和首任负责人创建链路已存在。
- 会话、消息、知识库、评测、质量复盘、试点准备、诊断包、备份/恢复演练、签名更新包、月度运维报告等模块已有后端和前端入口。
- 核心 API 与封包门禁验证通过：`pytest backend/tests/test_pilot_api.py backend/tests/test_p3_06u_26h2w_sealed_pilot_package_gates.py -q`，结果为 `58 passed`。
- 前端 `npm run typecheck` 与 `npm run build` 通过。
- FE12 客户视角浏览器 QA 已通过。
- FACT1/DATA3 已把一部分试点状态沉入数据库事实账本。
- KB6/TRIAL3 已能用内部样板资料跑知识复测和影子试跑。
- INSTALL7 已证明客户模式可以关闭开发 bootstrap、真实外发和 worker 默认开启。
- NC10 已具备 PostgreSQL backup dry-run manifest 的服务端登记能力，但只登记客户本机生成的 manifest，不上传 dump、不执行真实恢复。

### 不能宣称完成的能力

- 真实客户资料试跑未完成：现有状态仍是内部样板资料，`customer_data_used=false`。
- 正式客户签收未完成。
- 真实平台自动外发未开启。
- 真实渠道闭环本轮排除，不作为本计划目标。
- 生产 SLA 未完成。
- 正式签名安装包未完成。
- 高并发、真实 Postgres/pgvector 生产压力、真实多 worker 崩溃恢复未完成。
- 客户现场 PostgreSQL 备份演练 manifest 尚未提供，真实恢复工具和恢复窗口 SOP 尚未完成。
- 客户现场 PostgreSQL 临时库恢复演练 manifest 尚未提供，正式恢复执行 dry-run manifest 也尚未提供，正式恢复执行仍未开放。

### H2W-NC10：PostgreSQL 备份证据登记

目标：把 NC8 的客户本机 `pg_dump -Fc` 与 `pg_restore --list` 演练结果接入服务端本地维护证据链，让签名知识包/策略包更新前能读取“已验证备份 + 恢复可读性 dry-run”证据。

已完成：

- 新增 `POST /api/tenants/{tenant_id}/local-backups/postgres-dry-run-manifests`。
- 新增 manifest 校验：schema/status、`pg_dump_completed`、`pg_restore_list_completed`、sha256、文件大小、文件名安全、无敏感字段、无真实恢复、无数据库替换、无程序文件替换、真实外发关闭、入站 worker 关闭。
- 登记后写入 `LocalBackupRecord`，类型为 `postgres_pg_dump_custom`，`restore_mode=pg_restore_list_rehearsal_only`，并生成 `last_restore_dry_run`。
- 本地维护 readiness 已计入 `local_backup.postgres_dry_run_manifest_registered` 审计动作。
- 新增 NC10 门禁文档与 summary。

验收证据：

- `backend/.venv/bin/python -m pytest backend/tests/test_signed_update_packages_api.py backend/tests/test_local_backups_api.py backend/tests/test_local_maintenance_readiness_api.py -q`：`22 passed`。
- `python3 scripts/check_p3_06u_26h2w_nc10_postgres_backup_evidence_registration.py`：`status=postgres_backup_evidence_registration_ready_waiting_customer_pg_run`。
- `python3 scripts/check_p3_06u_26h2w_nc8_local_install_backup_update_rollback.py` 通过。
- `python3 scripts/check_p3_06u_26h2w_nc9_local_trial_package_v4.py` 通过。
- `backend/.venv/bin/python -m pytest backend/tests/test_p3_06u_26h2w_sealed_pilot_package_gates.py -q`：`49 passed`。

停止门禁：

- 没有客户机实际 manifest 时，不得写“客户现场 PostgreSQL 备份演练完成”。
- 没有真实恢复工具和停服窗口 SOP 时，不得写“恢复能力完成”。
- 任何接口上传或保存 dump 文件本体、执行真实恢复、替换数据库、打开真实外发，均阻断。

### H2W-NC11：PostgreSQL 恢复演练计划

目标：在 NC10 已登记 PostgreSQL 备份可读性 manifest 的基础上，生成客户可理解、售后可审计的恢复演练计划；本片只做计划，不做真实恢复。

已完成：

- 新增 `POST /api/local-backups/{local_backup_id}/postgres-restore-rehearsal-plan`。
- 新增 PostgreSQL 恢复演练计划 schema、服务层校验和审计动作 `local_backup.postgres_restore_rehearsal_plan_created`。
- 计划会写入 `LocalBackupRecord.manifest_payload.last_restore_rehearsal_plan` 和 `postgres_restore_rehearsal_plan`。
- 服务端要求备份记录必须是 `postgres_pg_dump_custom`、`verified`、`restore_mode=pg_restore_list_rehearsal_only`，且 manifest/safety 明确未真实恢复、未替换数据库、未保存 dump 本体、未打开真实外发。
- 本地维护 readiness 已能把 `last_restore_rehearsal_plan` 计入恢复演练证据。

验收证据：

- `backend/.venv/bin/python -m pytest backend/tests/test_local_backups_api.py -q`：`8 passed`。
- `backend/.venv/bin/python -m pytest backend/tests/test_local_maintenance_readiness_api.py -q`：`2 passed`。
- `backend/.venv/bin/python -m pytest backend/tests/test_signed_update_packages_api.py backend/tests/test_local_backups_api.py backend/tests/test_local_maintenance_readiness_api.py -q`：`24 passed`。
- `python3 scripts/check_p3_06u_26h2w_nc11_postgres_restore_rehearsal_plan.py`：`status=postgres_restore_rehearsal_plan_ready_no_live_restore`。
- `python3 scripts/check_p3_06u_26h2w_nc10_postgres_backup_evidence_registration.py`：仍为 `postgres_backup_evidence_registration_ready_waiting_customer_pg_run`。
- `backend/.venv/bin/python -m pytest backend/tests/test_p3_06u_26h2w_sealed_pilot_package_gates.py -q`：`49 passed`。

停止门禁：

- 没有客户机实际 manifest 时，不得写“客户现场 PostgreSQL 备份演练完成”。
- 没有真实恢复执行工具、临时库恢复、停机窗口、恢复前二次备份和恢复后健康检查时，不得写“恢复能力完成”。
- 本接口不得执行 `pg_restore`、不得替换数据库、不得保存 dump 文件本体、不得打开真实外发。

### H2W-NC12：PostgreSQL 临时库恢复演练

目标：在 NC10/NC11 之后，提供一个客户机本地临时库恢复演练脚本，并把演练 manifest 登记进本地维护证据链；本片只验证“备份能恢复到临时库并通过健康检查”，不做正式恢复。

已完成：

- 新增 `deploy/postgres-temp-restore-rehearsal.sh`。
- 脚本要求显式传入 NC8 备份演练目录，校验 `manifest.json` 与 `postgres.dump` sha256 一致。
- 脚本只允许使用 `wanfa_restore_tmp_...` 安全前缀临时库名，阻断正式库风险词。
- 脚本在客户本机 Docker Compose PostgreSQL 中执行 `createdb`、`pg_restore`、健康检查和 `dropdb`；输出 NC12 manifest。
- 新增 `POST /api/tenants/{tenant_id}/local-backups/postgres-temp-restore-manifests`。
- 服务端校验备份记录、sha256、临时库已创建、`pg_restore` 到临时库已完成、健康检查已完成、临时库已删除、真实恢复和真实外发全部为 false。
- 服务端只保存 manifest 摘要和临时库名 hash，不保存 dump 文件本体，不保存临时库明文名。
- 本地维护 readiness 已计入 `local_backup.postgres_temp_restore_manifest_registered` 审计动作。

验收证据：

- `bash -n deploy/postgres-temp-restore-rehearsal.sh`：通过。
- `python3 -m py_compile scripts/check_p3_06u_26h2w_nc12_postgres_temp_restore_rehearsal.py`：通过。
- `backend/.venv/bin/python -m pytest backend/tests/test_local_backups_api.py -q`：`10 passed`。
- `backend/.venv/bin/python -m pytest backend/tests/test_signed_update_packages_api.py backend/tests/test_local_backups_api.py backend/tests/test_local_maintenance_readiness_api.py -q`：`26 passed`。
- `python3 scripts/check_p3_06u_26h2w_nc12_postgres_temp_restore_rehearsal.py`：`status=postgres_temp_restore_rehearsal_ready_waiting_customer_pg_run`。
- `python3 scripts/check_p3_06u_26h2w_nc11_postgres_restore_rehearsal_plan.py`：仍为 `postgres_restore_rehearsal_plan_ready_no_live_restore`。
- `python3 scripts/check_p3_06u_26h2w_nc10_postgres_backup_evidence_registration.py`：仍为 `postgres_backup_evidence_registration_ready_waiting_customer_pg_run`。
- `backend/.venv/bin/python -m pytest backend/tests/test_p3_06u_26h2w_sealed_pilot_package_gates.py -q`：`49 passed`。

停止门禁：

- 没有客户机实际 NC8 备份 manifest 和 NC12 临时库恢复 manifest 时，不得写“客户现场 PostgreSQL 恢复演练完成”。
- NC12 manifest 只能证明临时库恢复和健康检查，不得写成正式恢复完成。
- 服务端不得执行 `pg_restore`、不得替换真实数据库、不得保存 dump 文件本体、不得打开真实外发。
- 正式恢复执行必须另有停机窗口、恢复前二次备份、客户管理员确认、恢复后健康检查和失败回滚路径。

### H2W-NC13：PostgreSQL 正式恢复前置门禁

目标：在 NC10 备份证据、NC11 恢复计划和 NC12 临时库恢复演练之后，补客户管理员确认、维护窗口、恢复前二次备份、健康检查和回滚计划的服务端门禁。本片只登记前置确认，不执行正式恢复。

已完成：

- 新增 `POST /api/tenants/{tenant_id}/local-backups/postgres-formal-restore-preflight`。
- 新增 PostgreSQL 正式恢复前置确认 schema、服务层校验和审计动作 `local_backup.postgres_formal_restore_preflight_registered`。
- 服务端要求同一备份记录已具备 NC10 `postgres_pg_dump_custom` 备份 manifest、NC11 `last_restore_rehearsal_plan` 和 NC12 `last_temp_restore_rehearsal`。
- 确认包必须明确维护窗口、停止服务窗口、恢复前二次备份、临时库验证、恢复后健康检查、回滚计划、客户管理员确认和最终操作员确认。
- 服务端只保存确认包摘要、hash、前置门禁和审计，不保存客户签名原文、不执行 `pg_restore`、不替换真实数据库、不打开真实外发。
- 本地维护 readiness 已计入 `local_backup.postgres_formal_restore_preflight_registered` 审计动作。

验收证据：

- `backend/.venv/bin/python -m pytest backend/tests/test_local_backups_api.py -q`：`12 passed`。
- `python3 -m py_compile scripts/check_p3_06u_26h2w_nc13_formal_restore_preflight.py`：通过。
- `python3 scripts/check_p3_06u_26h2w_nc13_formal_restore_preflight.py`：`status=formal_restore_preflight_gate_ready_no_live_restore`。
- `backend/.venv/bin/python -m pytest backend/tests/test_signed_update_packages_api.py backend/tests/test_local_backups_api.py backend/tests/test_local_maintenance_readiness_api.py -q`：`28 passed`。
- `python3 scripts/check_p3_06u_26h2w_nc12_postgres_temp_restore_rehearsal.py`：仍为 `postgres_temp_restore_rehearsal_ready_waiting_customer_pg_run`。
- `python3 scripts/check_p3_06u_26h2w_nc11_postgres_restore_rehearsal_plan.py`：仍为 `postgres_restore_rehearsal_plan_ready_no_live_restore`。

停止门禁：

- 没有 NC10 备份 manifest、NC11 恢复计划和 NC12 临时库恢复演练，不得登记正式恢复前置确认。
- NC13 通过也不得写成正式恢复执行完成；它只说明正式恢复前置条件已被工程化约束。
- 服务端不得执行 `pg_restore`、不得替换真实数据库、不得保存 dump 文件本体、不得打开真实外发、不得提供应用内一键恢复。
- 下一阶段若进入恢复执行，必须另有停机编排、恢复前二次备份生成、最终操作员确认、恢复后健康检查和失败回滚验证。

### H2W-NC14：PostgreSQL 正式恢复执行 dry-run 外壳

目标：在 NC13 正式恢复前置门禁之后，补一个客户机侧“正式恢复执行计划 dry-run”外壳和服务端登记接口。本片只证明正式恢复执行计划可以被结构化登记和审计，不执行真实恢复。

已完成：

- 新增 `deploy/postgres-formal-restore-dry-run.sh`。
- 新增 `POST /api/tenants/{tenant_id}/local-backups/postgres-formal-restore-execution-dry-run`。
- 新增 PostgreSQL 正式恢复执行 dry-run schema、服务层校验和审计动作 `local_backup.postgres_formal_restore_execution_dry_run_registered`。
- 客户机脚本要求显式传入 NC8 备份目录，校验 `manifest.json` 与 `postgres.dump` sha256 一致，检查客户环境中真实外发和入站 worker 均关闭，并输出 NC14 manifest。
- 客户机脚本只保存命令预览 hash，不保存原始恢复命令，不执行 `pg_restore`，不替换真实数据库，不打开真实外发。
- 服务端要求同一备份记录已具备 NC10 备份 manifest、NC11 恢复计划、NC12 临时库恢复演练和 NC13 正式恢复前置确认。
- 服务端只保存 manifest、执行计划摘要、命令 hash 和审计；不保存 dump 本体，不保存原始恢复命令，不提供应用内一键恢复。

验收证据：

- `backend/.venv/bin/python -m pytest backend/tests/test_local_backups_api.py -q`：`14 passed`。
- `bash -n deploy/postgres-formal-restore-dry-run.sh`：通过。
- `python3 -m py_compile scripts/check_p3_06u_26h2w_nc14_formal_restore_execution_dry_run.py`：通过。
- `python3 scripts/check_p3_06u_26h2w_nc14_formal_restore_execution_dry_run.py`：`status=formal_restore_execution_dry_run_ready_no_live_restore`。
- `backend/.venv/bin/python -m pytest backend/tests/test_signed_update_packages_api.py backend/tests/test_local_backups_api.py backend/tests/test_local_maintenance_readiness_api.py -q`：`30 passed`。
- `python3 scripts/check_p3_06u_26h2w_nc13_formal_restore_preflight.py`：仍为 `formal_restore_preflight_gate_ready_no_live_restore`。
- `backend/.venv/bin/python -m pytest backend/tests/test_p3_06u_26h2w_sealed_pilot_package_gates.py -q`：`49 passed`。

停止门禁：

- 没有 NC13 `last_formal_restore_preflight` 时，不得登记正式恢复执行 dry-run。
- NC14 通过也不得写成正式恢复执行完成；它只说明正式恢复执行计划已经能被结构化登记和审计。
- 服务端和客户机脚本不得执行真实 `pg_restore`、不得替换真实数据库、不得保存 dump 文件本体、不得保存原始恢复命令、不得打开真实外发、不得提供应用内一键恢复。
- 真正进入恢复执行前，仍需要停机编排、恢复前二次备份真实生成、最终操作员确认、恢复后健康检查真实执行、失败回滚验证和客户现场确认。

## 二、全量审验发现的硬问题

### 1. 全量后端测试已在 NC0 归零，但必须持续回归

原审验发现核心门禁通过但全量后端测试仍有 5 个失败：

- 月度运维报告边界文案断言仍期待旧字符串。
- H2W11D、H2W11F、H2W11K 静态门禁仍依赖旧文案或旧 token。
- reply orchestrator 在全套运行时出现模型路由顺序污染，期望 `qwen3.7-max`，实际出现 `qwen-max`。

这些问题已在 NC0 修复，并通过全量后端测试和前端构建复验。后续仍要把“全量测试绿”作为每轮封包前门禁，避免旧门禁、配置隔离和状态漂移回潮。

### 2. `pilot-readiness` 仍混合数据库事实、审计事件和 summary 文件

后端审查发现：

- readiness 仍读取大量 `output/*/summary.json`。
- 只看 `knowledge_confirmation.imported` 审计事件存在，就可能把客户确认链路抬高。
- `customer_data_ready = customer_confirmation_ready and retest_ready` 没有强制要求真实资料 fact 已通过。

这会导致客户现场重装、清空库、旧 summary 残留时，前端可能看到不准确的 ready 状态。

### 3. 前端已经可用，但还不是最终产品级

前端审查发现：

- `frontend/src/App.tsx` 约 18,060 行。
- `frontend/src/styles.css` 约 12,189 行。
- `frontend/src/api/client.ts` 约 4,389 行。
- codebase-memory 显示 `App` 复杂度很高：cyclomatic 78，cognitive 102。
- 接待工作台更像受控试聊台，不是完整客服 IM。
- 知识中心仍偏 CSV/JSON 文本区操作，小微企业客户容易卡住。
- 渠道页部分步骤会给人“已经完成”的错觉，虽然真实渠道闭环并未完成。
- “签收”“客户确认”等词仍接近正式验收，应降级为“试跑确认”。

### 4. 安全与交付边界已完成 NC2 第一轮硬化，仍需后续交付级增强

原安全审查发现：

- `.env.example` 默认开发模式和 `STANDARD_OPS_DEV_BOOTSTRAP_ENABLED=true` 容易被误用。
- dev bootstrap 相关接口在开发态可返回 bootstrap owner。
- 登录缺少限速、失败计数和锁定策略。
- 诊断包接收会保存上传 payload，且主要信任客户端 safety 声明。
- PII 扫描偏窄，目前不能覆盖姓名、地址、订单号、微信号、身份证、合同号等。
- `output/` 中存在浏览器 profile、Cookies、History、Login Data 等测试残留，不能进入客户包。
- 客户默认 PostgreSQL/pgvector 环境与当前 SQLite-only 备份服务不匹配。

NC2 已完成第一轮硬化：登录失败限速和审计已补，客户模式首任负责人创建会阻断危险开关，客户模式不再无 token 返回开发 bootstrap，诊断包已新增大小/深度/schema 门禁并改为拒收摘要存储，交付档案扫描已禁止浏览器敏感文件。仍未完成的是更宽的 PII 识别、保留期/自动清理、PostgreSQL/pgvector 备份恢复一致性和正式签名安装器。

### 5. 知识库有方向，但还不是成熟 Memory Mesh

当前知识体系已经有四层结构：

- 业务对象
- 标准问答
- 流程政策
- 禁用承诺与转人工规则

也已经吸收了一部分 Memory Mesh 思想：

- 资料批次 hash
- 事实账本
- 引用溯源
- 知识缺口
- 质量复测
- 禁用承诺与转人工门禁
- 影子试跑

但它还不是完整 Memory Mesh。缺口包括：

- 没有真正的事件级长期记忆层。
- 没有把会话事件、知识修复、质量标签、模型调用、引用快照统一成可查询的记忆网络。
- 没有客户业务对象之间的关系图谱。
- 没有“每次真实对话 -> 错因 -> 知识修复 -> 回归验证 -> 新版本发布”的强制闭环。
- 没有成熟的混合检索、重排、引用快照和 pgvector 生产运行门禁。

补充审查结论：知识库/Memory Mesh 吸收程度约 45/100。当前最强的是“知识治理闭环”，不是“生产级 Memory Mesh”。真实客户资料进入后，风险会集中在状态命名漂移、raw text 隐私、生产检索切换、引用精度下降和最终答案事实性不足。

## 三、外部成熟方案对标

本轮重新核验了开源和商业产品方向。重点结论如下：

- RAGFlow 强调深度文档理解、可解释 chunk、引用溯源、多路召回和重排，并支持复杂数据源，说明成熟 RAG 不只是向量库，而是“文档解析 + 切分可视化 + 引用 + 多路检索 + 重排 + 集成 API”。参考：[RAGFlow GitHub](https://github.com/infiniflow/ragflow)。
- MaxKB 定位企业级智能体平台，集成 RAG pipeline、workflow、MCP 工具能力，技术栈明确使用 PostgreSQL + pgvector。参考：[MaxKB GitHub](https://github.com/1Panel-dev/MaxKB)。
- FastGPT 强调开箱即用的数据处理、RAG 检索和可视化工作流编排。参考：[FastGPT GitHub](https://github.com/labring/FastGPT)。
- LiteLLM 已把多模型统一接口、成本追踪、预算、fallback、负载均衡和日志作为模型网关核心能力。参考：[LiteLLM GitHub](https://github.com/BerriAI/litellm)。
- Langfuse 把 traces、evals、prompt management、metrics、datasets 和 observability 作为 LLM 工程平台核心。参考：[Langfuse GitHub](https://github.com/langfuse/langfuse)。
- Promptfoo 把 prompt、agent、RAG 的自动评测、红队、安全扫描和 CI/CD 集成作为工程标配。参考：[Promptfoo GitHub](https://github.com/promptfoo/promptfoo)。
- Intercom 强调 Knowledge Hub 作为客户和内部支持内容的单一事实源，并可控制 AI 使用哪些内容、追踪哪些内容表现最好。参考：[Intercom Knowledge Management](https://www.intercom.com/blog/guide-customer-service-knowledge-management-ai/)。
- Zendesk AI Agents 对外宣称自动化、质量评审、多语言和持续改进；无论数字是否用于我们定价，成熟产品方向都是“意图识别 + 知识 + 流程动作 + 质量反馈 + 人工接管”。参考：[Zendesk AI Agents](https://www.zendesk.com/service/ai/ai-agents/)。
- OpenAI customer service demo 说明智能客服参考架构通常不止一个聊天模型，而是后端 agent orchestration、guardrails、tools 和前端工作台组合。参考：[openai-cs-agents-demo](https://github.com/openai/openai-cs-agents-demo)。

对照这些方案，我们当前方向正确，但仍缺四个成熟系统标志：

- 真正客户资料驱动的知识生命周期。
- 线上级 LLM 可观测与评测闭环。
- 客户可独立使用的低摩擦前端流程。
- 安全、安装、备份、更新、诊断的强门禁。

## 四、下一阶段总目标

在排除真实渠道闭环的情况下，下一阶段目标是：

> 把系统从“内部样板本地受控试跑候选”推进到“真实客户资料版本地试跑包候选”。该候选包必须能证明：客户能创建负责人、导入资料、预检、发布知识、复测、查看质量报告、生成诊断/备份/更新证据，并且所有 ready 状态来自数据库事实账本，而不是旧 summary 残留。

## 五、阶段推进计划

### H2W-NC0：全量测试与旧门禁归零

目标：先让工程健康度归零，避免在不稳定地基上继续叠功能。

施工内容：

- 修复全量后端测试 5 个失败。
- 更新 H2W11D/H2W11F/H2W11K 静态门禁，匹配当前产品文案。
- 统一月度运维报告边界文案。
- 修复 reply orchestrator 全套运行时的模型路由配置污染。
- 将 FastAPI/TestClient deprecation warning 记录为后续升级项。

验收命令：

```bash
KNOWLEDGE_EMBEDDING_PROVIDER=deterministic_local \
KNOWLEDGE_EMBEDDING_MODEL=deterministic-token-vector-v1 \
PYTHONPATH=backend backend/.venv/bin/python -m pytest backend/tests -q

cd frontend && npm run typecheck && npm run build
```

停止门禁：

- 全量后端测试不绿，不进入客户资料链路。
- 静态门禁仍依赖旧文案，不进入封包。

### H2W-NC1：试点事实账本权威化

目标：让 `pilot-readiness` 以数据库事实为准，summary 只作为工程证据。

施工内容：

- 修正 `customer_data_ready` 判定，必须同时满足：
  - 真实资料批次 ready。
  - 真实题库数量与字段完整。
  - 真实知识复测通过。
  - 客户确认导入结果为通过或带备注通过。
  - 无敏感信息 blocker。
- 将客户确认导入结果落为结构化 fact，不再只看 audit event。
- 为 summary 增加 freshness/schema/hash 校验；过期 summary 只能作为历史证据，不能抬高现场 ready。
- 空库、重装、缺少 output 目录时，前端必须显示等待态，而不是候选完成态。

验收：

- 清空 output 目录后，`pilot-readiness` 不误报 ready。
- 清空数据库后，前端显示首任负责人和等待资料，而不是封包候选。
- 有真实 fact 才能显示客户资料链路 ready。

停止门禁：

- 任何客户可见 ready 状态来自旧 summary 而非 DB fact，阻断。

### H2W-NC2：安全客户模式硬化

目标：让本地试跑包不会因为开发配置、诊断包、输出残留而误伤客户。

施工内容：

- 客户模式彻底禁用 dev bootstrap。
- 客户入口只允许 `deploy/customer.env` 和 pilot compose，不允许客户误跑 `.env.example`。
- 登录增加限速、失败计数、冷却和审计。
- 首任负责人创建只保留 `/auth/local-setup/owner`，禁掉空租户首用户绕过管理权限。
- 诊断包增加 size/depth/schema allowlist，不能只信任 safety 声明。
- 诊断包保存前剥离敏感字段，增加保留期和清理机制。
- 交付包强制排除浏览器 profile、Cookies、History、Login Data、临时数据库、`.git`、`node_modules`。

验收：

- customer mode 下 `/api/auth/dev-local-login` 和 bootstrap user 都不可用。
- 恶意诊断包、超大包、深层嵌套包、带 token 包被拒绝。
- 打包扫描不能发现 Cookies、History、Login Data、token、password、private key。

停止门禁：

- 开发 bootstrap 能在客户模式访问，阻断。
- 诊断包可保存明显敏感信息，阻断。
- 交付档案包含浏览器 profile，阻断。

### H2W-NC3：真实客户资料接收与预检产品化

目标：客户不再靠复制 CSV/JSON 文本区完成知识导入，而是走清晰的资料上传/预检/修正流程。

施工内容：

- 新增客户资料上传向导：
  - 知识资料。
  - 50-100 条脱敏问题。
  - 标准答案。
  - 禁用承诺。
  - 转人工规则。
  - 资料来源说明。
  - 脱敏声明。
- 支持 CSV/XLSX 作为正式入口。
- PDF/DOCX 先作为来源资料，不伪装成自动高质量入库。
- 预检报告定位到行、列、字段、风险原因。
- 资料批次落库只保存 hash、统计、覆盖率、风险计数，不保存原始敏感文本。

验收：

- 少于 50 条问题时只能显示资料准备中。
- 未脱敏、缺字段、含 token、含平台 payload 均阻断。
- 内部样板不能冒充真实客户资料。
- 当前实现已通过 NC3 门禁：资料批次 API、前端本地 CSV/JSON 草稿填入、批次刷新、原文不回显和边界文案均可验。

停止门禁：

- 系统替客户预填确认人或确认时间，阻断。
- 内部样板通过真实客户资料门禁，阻断。

### H2W-NC4：知识中心 v2 与 Memory Mesh 化

目标：把现在的“四层知识库”升级成更有吸引力、可解释、可维护的客户知识中心。

当前实现：已完成第一片 `knowledge_memory_mesh_overview_ready`。后端新增只读知识网络总览接口，前端知识三页统一展示五类节点与八段证据链；响应不返回客户原文、文档正文或草稿全文。完整图数据库式 Memory Mesh、来源冲突检测、自动知识修复和真实客户资料闭环仍属于后续深化。

施工内容：

- 四层知识保持为客户可理解的入口：
  - 业务对象。
  - 标准问答。
  - 流程政策。
  - 禁用承诺与转人工规则。
- 增加 Memory Mesh 思想的五类节点：
  - 资料批次。
  - 知识卡片。
  - 业务对象。
  - 真实/样本问题。
  - 质量标签与错因。
- 每一次回答形成 provenance：
  - 入站样本。
  - 检索结果。
  - 引用 chunk。
  - 模型调用。
  - 最终草稿。
  - 转人工理由。
  - 质量标签。
  - 修复后的知识版本。
- 增加知识版本图：
  - 导入版本。
  - 发布版本。
  - 回滚版本。
  - 复测版本。
- 增加 source authority：
  - 来源等级。
  - 版本时效。
  - 旧政策替换。
  - 新旧冲突。
  - 适用范围。
  - 废弃策略。
- 增加 semantic event / entity shadow：
  - 客户问题事件。
  - 业务对象实体。
  - 别名和同义表达。
  - 检索 trace。
  - 质量标签。
  - 修复动作。
- 增加知识缺口到修复的闭环：
  - 错因归类。
  - 推荐补知识。
  - 发布前差异。
  - 发布后回归。

验收：

- 任意一条质量失败样本能追到资料批次、知识卡、引用、模型调用和修复建议。
- 无引用高置信回答必须被阻断或降级。
- 禁用承诺样本不得复述禁用承诺。

停止门禁：

- 只测检索命中率、不测最终答案质量，阻断。
- 引用无法追到 chunk/version/hash/source_uri，阻断。

### H2W-NC5：生产级检索与评测治理

当前状态：已完成第一轮，`status=production_retrieval_governance_ready_not_production_switch`。治理层已经能把 pgvector runtime、检索评测、最终答案质量、模型成本和知识证据链聚合到同一张 `production_readiness` 总账；同时已修正一个关键风险：内部样板题库和内部 100 题只能证明机制，不能解锁生产检索切换。

目标：与 RAGFlow/FastGPT/MaxKB 的成熟方向对齐，补齐真实 RAG 工程门槛。

施工内容：

- PostgreSQL + pgvector 真实运行门禁。
- exact scan、HNSW、IVFFlat 策略选择和回滚方案。
- BM25 + vector + reranker 的候选路径。
- 真实题库跑召回、引用覆盖、延迟、成本。
- 记录 embedding provider、model、version、价格、失败降级。
- PDF/DOCX 解析先不承诺自动高质量，需人工确认抽取结果。
- 增加文档解析流水线：
  - PDF/DOCX/表格/OCR/页码。
  - 标题层级。
  - 重复检测。
  - 导入错误报告。
- 建立真实资料隐私门禁：
  - PII 扫描。
  - 脱敏预览。
  - raw_text 保留策略。
  - 删除级联。
  - 外部 embedding 发送确认。

验收：

- SQLite/JSON 检索不能伪装成生产向量库。
- 无 Postgres/pgvector runtime 不得写生产级检索完成。
- 真实题库跑出召回、引用、延迟、成本报告。
- 当前已通过 NC5 聚合门禁、RAG 治理 API 测试、向量索引相邻回归、H2W7 静态门禁和前端 typecheck/build。

停止门禁：

- 没有真实题库就切生产检索，阻断。
- 没有真实客户资料批次和真实资料链路重跑，就算 pgvector、内部题库和模型成本证据 ready，也必须阻断生产检索切换。
- 外部 embedding 成本不可追溯，阻断。

### H2W-NC6：LLM 网关、成本、观测与红队

当前执行结果：NC6 已完成第一片，NC16 已补红队闭环门禁第一片，NC17 已补内部红队题库与影子试跑标签包。NC6 新增 `GET /api/tenants/{tenant_id}/llm-ops-readiness`、`backend/app/services/llm_ops.py`、`backend/app/schemas/llm_ops.py`、`backend/tests/test_llm_ops_readiness_api.py`、前端“模型观测与红队”卡片，以及 `scripts/check_p3_06u_26h2w_nc6_llm_ops_observability_redteam.py`。NC16 新增 `scripts/check_p3_06u_26h2w_nc16_redteam_closure.py` 和 `docs/P3-06U-26H2W_NC16_REDTEAM_CLOSURE.md`，并收紧红队 ready 规则：必须覆盖提示注入、越狱、隐私泄露、禁用承诺和越权操作五类风险，全部活跃红队题必须有最终答案人工标签，失败样本必须逐条进入知识缺口或质量复盘。NC17 新增 `evals/p3_06u_26h2w_nc17_redteam_shadow_trial/`、`scripts/check_p3_06u_26h2w_nc17_redteam_shadow_trial.py`、`backend/tests/test_p3_06u_26h2w_nc17_redteam_shadow_trial.py` 和 `docs/P3-06U-26H2W_NC17_REDTEAM_SHADOW_TRIAL.md`，形成 25 条内部准真实样本与 25 条影子标签，五类风险各 5 条。当前 NC17 状态为 `redteam_shadow_trial_internal_sample_ready_not_customer_security_signoff`，说明内部红队样本包和标签包 ready；但没有真实客户红队题库、真实模型输出和客户安全签收，仍不能写安全评测完成。

目标：补齐 LiteLLM、Langfuse、Promptfoo 这类成熟工程体系对应的能力。

施工内容：

- 模型调用统一走模型网关抽象。
- 记录 provider、model、route、tokens/字符量、latency、价格版本、预算策略。
- 增加预算硬门禁：
  - 高阶模型降级。
  - 标准模型降级。
  - 确定性知识草稿。
  - 转人工。
- 增加可观测 trace：
  - 一次回复的检索、引用、模型调用、草稿、质量标签。
- 增加 prompt/回复策略版本。
- 增加 promptfoo 风格离线评测：
  - 幻觉。
  - 禁用承诺。
  - 越权承诺。
  - 隐私泄漏。
  - prompt injection。
  - 越狱。

验收：

- 5-10 条小样本真实模型调用可记录成本和延迟。
- 显式 provider 失败不能静默 fallback。
- 红队样本失败必须进入质量复盘和知识修复。

停止门禁：

- 模型失败被伪装成功，阻断。
- 没有成本台账却展示模型成本，阻断。

### H2W-NC7：前端真实产品化收束

目标：让小微企业客户可以在陪跑较少的情况下理解怎么用。

执行状态：已完成第一片，`status=frontend_productization_customer_flow_ready_component_split_pending`。试点准备、质量复盘口径、账号与本地维护入口、多渠道对话台主形态和渠道边界已通过 NC7 门禁；`App.tsx/styles.css/client.ts` 拆分仍未完成，作为后续技术债继续推进。

施工内容：

- 试点准备改为一级主入口或总览首屏行动区。
- 渠道页本轮只保留边界，不显示误导性的已完成。
- 接待工作台补真实 IM 流：
  - 左侧紧凑会话列表。
  - 右侧完整消息历史。
  - 转人工状态。
  - 解决/归档。
  - 失败原因。
  - 测试会话入口。
- 知识中心改为上传向导。
- 质量复盘统一把“签收”降级为“试跑确认”，正式签收置灰。
- 账号与本地维护拆分：
  - 账号。
  - 诊断。
  - 备份。
  - 更新。
  - 回滚。
- 为备份/更新/回滚增加二次确认。
- 修复疑似孤儿链接，如 `#monthly-ops-report`。
- 拆分 `App.tsx/styles.css/client.ts`，形成页面组件、hooks、API 模块。

验收：

- 老板、客服、知识维护、售后四个角色各跑一遍浏览器路径。
- 每个客户可见按钮必须三选一：真实动作、明确禁用、隐藏。
- 客户可见界面不得出现 `H2W`、`P3`、`dry-run`、`provider`、`outbox`、`sandbox`、`rehearsal` 等工程词。

停止门禁：

- 假按钮、假分页、误导性 ready、工程词暴露，阻断。

### H2W-NC8：本地安装、备份、更新与回滚补强

执行状态：已完成第一片，`status=local_install_backup_update_rollback_hardened_pg_script_ready`。客户本地启动脚本已补 Docker daemon、Docker Compose、磁盘、端口、PostgreSQL readiness、迁移 head、真实外发关闭和入站 worker 关闭检查；新增 `deploy/postgres-backup-dry-run.sh`，用于在客户本机生成 PostgreSQL `pg_dump -Fc` 备份并用 `pg_restore --list` 做可读性 dry-run；签名知识包和策略包 apply 前已增加服务端备份门禁，无已验证备份与恢复 dry-run 证据时拒绝应用。当前仍未在客户现场 Docker 环境实际执行 PostgreSQL 备份演练，服务端 PostgreSQL 物理备份证据登记还未产品化，macOS/Windows 仍是启动候选体验，不是签名安装包。

目标：让客户本地试跑包具备可恢复、可诊断、可升级的基本可信度。

施工内容：

- PostgreSQL 环境备份/恢复 dry-run。
- 升级前强制备份。
- 更新包 apply 前服务端检查备份存在且可恢复。
- 回滚必须有审计事件。
- macOS/Windows 启动脚本继续保持候选，不写正式签名安装包。
- 增加 Docker daemon、compose、端口、磁盘、DB readiness、迁移 head、worker 关闭、真实外发关闭检查。

验收：

- 空库启动。
- 首任负责人创建。
- 重启后状态一致。
- 备份、恢复 dry-run、更新预检、回滚入口可用。

停止门禁：

- 默认客户 Postgres 环境无法备份恢复，阻断。
- 更新绕过备份，阻断。

### H2W-NC9：非真实渠道版本地试跑包 v4

目标：在不接真实渠道的前提下，生成可给共创客户试跑的候选档案。

执行状态：已完成内部样板候选，当前 `status=local_trial_package_v4_candidate_with_internal_sample`。NC9 聚合 NC1-NC8、PACK11、PACK12、FE12、KB6、TRIAL3、OPS2、OPS3、INSTALL7 等证据，生成 `docs/P3-06U-26H2W_NC9_LOCAL_TRIAL_PACKAGE_V4.md`、`output/p3_06u_26h2w_nc9_local_trial_package_v4/summary.json`、`manifest.json` 和 `local_trial_package_v4_candidate.zip`。该档案不包含原始回传文件、客户原文、平台 payload、浏览器 profile、`.git`、`node_modules` 或临时数据库；当前不是客户真实资料版封包。

档案必须包含：

- 启动说明。
- 首任负责人说明。
- 客户资料模板。
- 知识导入和预检说明。
- 知识复测报告。
- 影子试跑质量报告。
- 月度运维报告。
- 诊断、备份、更新、回滚说明。
- 安装候选说明。
- 明确边界声明。

档案不得包含：

- key、token、密码、私钥。
- 客户原文。
- 平台 payload。
- `.git`。
- `node_modules`。
- 浏览器 profile。
- 临时数据库。
- Cookies、History、Login Data。

状态只允许：

- `blocked`
- `local_trial_package_v4_candidate_with_internal_sample`
- `local_trial_package_v4_candidate_with_real_customer_materials`

停止门禁：

- 写成正式客户验收，阻断。
- 写成真实渠道已接通，阻断。
- 写成签名安装包完成，阻断。

## 六、推荐执行顺序

1. H2W-NC0：全量测试与旧门禁归零。
2. H2W-NC1：试点事实账本权威化。
3. H2W-NC2：安全客户模式硬化。
4. H2W-NC3：真实客户资料接收与预检产品化。
5. H2W-NC4：知识中心 v2 与 Memory Mesh 化。
6. H2W-NC5：生产级检索与评测治理。
7. H2W-NC6：LLM 网关、成本、观测与红队。
8. H2W-NC7：前端真实产品化收束。
9. H2W-NC8：本地安装、备份、更新与回滚补强。
10. H2W-NC9：非真实渠道版本地试跑包 v4。

实际执行建议：

- NC0、NC1、NC2 必须先做，属于地基。
- NC3、NC4、NC7 可以并行，但必须共享同一套资料/知识/确认状态契约。
- NC5、NC6 可以先以最小闭环接入，不要一次性追求完整平台。
- NC8、NC9 放最后，否则会把不稳定状态打进客户包。

## 七、阶段性评分目标

当前评分：

- 本地受控试跑候选：约 72-76/100。
- 可收费共创试点：约 68-72/100。
- 非真实渠道版商用试跑：约 60/100。
- 成熟全渠道商用客服：约 35-45/100，本计划不覆盖真实渠道闭环。

完成 NC0-NC9 后目标：

- 本地受控试跑候选：85/100 以上。
- 可收费共创试点：80/100 左右。
- 非真实渠道版商用试跑：75/100 左右。
- 成熟全渠道商用客服：仍不超过 55/100，因为真实渠道闭环仍未做。

## 八、不可越界承诺

即使本计划全部完成，也不能宣称：

- 全渠道真实自动回复已上线。
- 企业微信、公众号、抖音、淘宝、京东、拼多多已接通。
- 正式客户验收签收完成。
- 生产 SLA 完成。
- 正式签名 dmg/exe 安装器完成。
- RPA 或个人号外挂可以正式交付。

可以宣称：

- 可进行本地受控试跑。
- 可用真实客户资料进行知识导入、复测和影子试跑。
- 可生成质量报告、知识缺口、运维报告和诊断/备份/更新证据。
- 真实外发默认关闭。
- 渠道接入需要另开官方授权专项。

## 九、2026-07-06 执行补充：NC10-NC15 PostgreSQL 恢复证据链

本计划执行后，PostgreSQL 本地维护链路已补到 NC15，但仍必须按“证据链候选”理解，不能写成生产恢复完成。

已完成：

- NC10：PostgreSQL `pg_dump -Fc` 与 `pg_restore --list` 备份可读性 manifest 登记。
- NC11：PostgreSQL 恢复演练计划登记。
- NC12：客户机临时库恢复演练 manifest 登记。
- NC13：正式恢复前置确认门禁登记。
- NC14：正式恢复执行 dry-run 外壳，登记恢复执行计划和命令预览 hash。
- NC15：正式恢复 SOP 与停机编排门禁登记，登记维护窗口、人工确认、二次备份、健康检查和回滚路径。

当前最新状态：

- NC19：`customer_redteam_report_flow_ready_waiting_customer_data`。
- NC18：`redteam_fact_ingest_ready_internal_sample_visible_to_llm_ops`。
- NC17：`redteam_shadow_trial_internal_sample_ready_not_customer_security_signoff`。
- NC16：`redteam_closure_gate_ready_internal_fixtures_only`。
- NC15：`formal_restore_runbook_ready_no_live_restore`。
- 应用内 `can_execute_restore_now=false`。
- 应用内 `can_execute_restore_in_app=false`。
- `restore_execution_performed=false`。

不可越界：

- 不能宣称 PostgreSQL 真实恢复已完成。
- 不能宣称一键恢复可用。
- 不能宣称生产恢复能力完成。
- 不能宣称客户现场已经完成 NC8/NC12/NC14 manifest。
- 不能宣称客户真实红队安全签收完成。
- 不能宣称真实客户模型输出红队标签完成。
- 不能把 NC19 客户红队报告模板写成客户安全报告完成。
- 不能把 NC18 内部样本导入数据库写成客户安全报告完成。
- 不能宣称真实外发、真实渠道、生产 SLA、签名安装包或移动端已完成。

后续如果继续恢复专项，必须另起客户现场恢复执行计划，至少包含：

- 客户现场真实 NC8/NC12/NC14 manifest。
- 停机窗口和客户管理员最终确认。
- 恢复前二次备份真实生成。
- 线下人工执行 `pg_restore`。
- 恢复后健康检查。
- 失败回滚验证。
- 客户确认记录。

在这些条件齐备之前，本系统只能说具备“PostgreSQL 恢复证据登记和 SOP 门禁能力”，不能说具备“正式生产恢复工具”。

## 十、2026-07-06 执行补充：NC18 红队事实账本导入

NC18 已把 NC17 内部红队样本包从文件证据推进到隔离数据库事实账本 rehearsal，并证明现有 `llm-ops-readiness` 可以读取 `knowledge_evaluation_*` 表中的红队样本、人工标签和失败回流状态。

已完成：

- NC18：导入 25 条内部红队样本和 25 条影子标签。
- NC18：写入 `knowledge_evaluation_sets`、`knowledge_evaluation_cases`、`knowledge_evaluation_runs`、`knowledge_evaluation_run_cases` 和 `pilot_readiness_facts`。
- NC18：`llm_ops_redteam.readiness=ready_for_controlled_pilot`。
- NC18：`internal_sample_only=true`，`raw_attack_vector_persisted=false`。
- NC18：前端“自动回复策略 -> 模型观测与红队”卡片展示安全题集、人工标签、题集来源和类目覆盖。

新增证据：

- `scripts/check_p3_06u_26h2w_nc18_redteam_fact_ingest.py`
- `backend/tests/test_p3_06u_26h2w_nc18_redteam_fact_ingest.py`
- `docs/P3-06U-26H2W_NC18_REDTEAM_FACT_INGEST.md`
- `output/p3_06u_26h2w_nc18_redteam_fact_ingest/summary.json`

验证：

- NC18 专项测试：`2 passed`。
- LLM Ops API 回归：`6 passed`。
- NC18 门禁：`redteam_fact_ingest_ready_internal_sample_visible_to_llm_ops`。
- 前端 typecheck/build：通过。
- NC17 回归：`3 passed`。
- sealed pilot gates：`49 passed`。

不可越界：

- NC18 不是客户真实红队题库。
- NC18 不是真实模型输出安全报告。
- NC18 不是客户安全签收。
- NC18 不打开真实外发、不接真实渠道、不代表生产 SLA。

## 十一、2026-07-06 执行补充：NC19 客户红队安全报告流程准备

NC19 已在 NC18 内部红队事实账本之上，补齐客户红队安全报告的资料接收模板和等待态门禁。它的作用是让后续真实客户安全报告有固定输入格式和硬边界，不让内部样本、模板样例或未回传文件冒充客户安全签收。

已完成：

- NC19：生成客户红队题库模板、人工标签模板和 manifest 模板。
- NC19：生成客户红队安全报告模板，默认显示等待客户资料。
- NC19：校验 NC18 已 ready，但不把 NC18 内部样本写成客户安全报告。
- NC19：门禁在没有 `customer_redteam_cases_received.csv`、`customer_redteam_labeled_results_received.csv` 和 `customer_redteam_manifest_received.json` 时保持等待态。

新增证据：

- `scripts/check_p3_06u_26h2w_nc19_customer_redteam_report_flow.py`
- `backend/tests/test_p3_06u_26h2w_nc19_customer_redteam_report_flow.py`
- `docs/P3-06U-26H2W_NC19_CUSTOMER_REDTEAM_REPORT_FLOW.md`
- `evals/p3_06u_26h2w_nc19_customer_redteam_report/customer_redteam_cases_template.csv`
- `evals/p3_06u_26h2w_nc19_customer_redteam_report/customer_redteam_labeled_results_template.csv`
- `evals/p3_06u_26h2w_nc19_customer_redteam_report/customer_redteam_manifest_template.json`
- `output/p3_06u_26h2w_nc19_customer_redteam_report/customer_redteam_security_report_template.md`
- `output/p3_06u_26h2w_nc19_customer_redteam_report/summary.json`

验证：

- NC19 专项测试：`2 passed`。
- NC19 门禁：`customer_redteam_report_flow_ready_waiting_customer_data`。
- NC17/NC18/LLM ops 相邻回归：`11 passed`。
- sealed pilot gates：`49 passed`。
- NC19 脚本 py_compile：通过。

不可越界：

- NC19 不是客户真实红队题库。
- NC19 不是真实模型输出安全报告。
- NC19 不是客户业务负责人复核确认。
- NC19 不是正式客户红队安全签收。
- NC19 不打开真实外发、不接真实渠道、不代表生产 SLA。

## 十二、2026-07-06 执行补充：COMM1 对外本地试跑商用包 v1 候选

COMM1 已把“最快速度对外”的五件事和七大核心板块收束成同一个门禁包。该阶段的正确商业口径是“共创客户本地受控试跑包候选”，不是成熟全渠道正式商用系统。

已完成五件事：

- 真实客户样板资料包：`ready_with_internal_sample_waiting_customer_materials`。
- 客户知识中心最终流程：`knowledge_center_flow_ready`。
- 前端最终成品级 QA：`frontend_customer_qa_and_polish_ready`。
- 本地部署交付包 v1：`local_deployment_handoff_v1_ready_as_candidate`。
- 对外试跑商业资料包：`commercial_trial_documents_ready`。

七大核心板块纳入矩阵：

- 真实客户资料闭环：内部样板可跑，等待真实客户资料。
- 客户知识中心最终产品化：六步流程可用于试跑。
- 前端最终成品感：FE10/FE12 证据通过。
- 真实渠道闭环：仅保留官方授权路线，真实外发继续关闭。
- 安装和交付体验：本地启动与安装候选可用于试跑。
- 真实安全与红队报告：NC19 模板与等待态 ready，真实客户报告未完成。
- 商用包装：产品介绍、使用手册、服务边界、报价范围模板和交付档案已形成。

新增证据：

- `scripts/check_p3_06u_26h2w_comm1_commercial_trial_launch_package.py`
- `backend/tests/test_p3_06u_26h2w_comm1_commercial_trial_launch_package.py`
- `docs/P3-06U-26H2W_COMM1_COMMERCIAL_TRIAL_LAUNCH_PACKAGE.md`
- `output/p3_06u_26h2w_comm1_commercial_trial_launch_package/summary.json`
- `output/p3_06u_26h2w_comm1_commercial_trial_launch_package/commercial_trial_launch_package_v1_candidate.zip`

验证：

- COMM1 专项测试：`2 passed`。
- COMM1 / NC19 / sealed pilot 回归：`53 passed`。
- 前端 typecheck/build：通过，保留既有大 chunk warning。
- COMM1 门禁：`commercial_trial_launch_package_v1_candidate_with_internal_sample`。

不可越界：

- COMM1 不等于真实客户资料版封包。
- COMM1 不等于正式客户签收。
- COMM1 不打开真实外发。
- COMM1 不接通企业微信、公众号、抖音、淘宝、京东、拼多多等真实渠道。
- COMM1 不等于生产 SLA。
- COMM1 不等于已签名 dmg/exe 安装包。
- COMM1 不等于移动端完成。
