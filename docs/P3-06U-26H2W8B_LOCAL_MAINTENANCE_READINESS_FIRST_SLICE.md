# P3-06U-26H2W8B 本地维护闭环就绪度与浏览器验收

## 定位

H2W-8B 第一片把已经存在的本地维护能力收束成一条可验收的客户本地运维链路：

`诊断包 -> 授权上传包 -> 售后接收台 -> 售后处理单 -> 签名更新包 -> 本地备份 -> 恢复演练 -> 审计证据`

本片不新增真实外发，不接真实企业微信、公众号、抖音、淘宝、京东或拼多多，也不做远程控制、静默更新或自动上传。它的目标是让客户负责人和我们自己的售后人员能看清：哪些维护步骤已经有证据，哪些仍缺证据，哪些安全边界不能越过。

## 本轮完成

- 新增后端服务 `backend/app/services/local_maintenance.py`。
- 新增只读接口 `GET /api/tenants/{tenant_id}/local-maintenance/readiness`。
- 接口权限使用 `updates.manage`，普通坐席不能读取本地维护总账。
- 接口读取真实数据库证据：
  - `diagnostic_intake_records`
  - `diagnostic_remediation_requests`
  - `signed_update_packages`
  - `local_backup_records`
  - `audit_events`
- 新增响应 schema `p3-06u-26h2w8b.local_maintenance_readiness.v1`。
- 前端 `账号与本地维护` 页面新增“本地维护闭环”摘要卡。
- 摘要卡展示：
  - 售后接收数量
  - 已生成更新计划数量
  - 签名更新包数量
  - 已校验备份数量
  - 恢复演练数量
  - 核心门禁状态
  - 阻断项或下一步补证据动作
- 备份、恢复演练、暂存更新包、应用、回滚、生成受控更新计划后，会刷新本地维护闭环摘要。
- 第二片新增独立浏览器门禁 `scripts/check_p3_06u_26h2w8b_local_maintenance_ui.mjs`：
  - 使用临时 SQLite、临时 Chrome profile 和临时 RSA 公钥。
  - 通过真实登录表单进入 `账号与本地维护`。
  - 在页面内完成授权上传包登记、售后处理单生成、签名更新包预检、签名包暂存、本地备份创建、备份校验、恢复演练和受控更新计划生成。
  - 最后同时检查前端摘要卡和后端 `/local-maintenance/readiness` 总账是否进入 `ready_for_rehearsal`。

## 成熟度口径

接口返回三种状态：

- `ready_for_rehearsal`：诊断接收、处理单、更新计划、签名更新包、已验备份、恢复演练和审计事件都有证据，且没有安全阻断项。
- `missing_evidence`：没有发现安全阻断，但维护链路证据不完整。
- `blocked`：发现外部写入、远程控制、静默更新、自动上传、原始客户文本泄露、备份错误或恢复演练被错误标记为可直接恢复等阻断项。

当前系统不允许把 `missing_evidence` 写成“已完成维护闭环”。前端会显示“继续补证据”。

## 安全边界

本片固定返回并校验以下边界：

- `external_write_performed=false`
- `remote_control_performed=false`
- `silent_update_performed=false`
- `automatic_update_performed=false`
- `automatic_upload_performed=false`
- `manual_transfer_required=true`
- `customer_admin_confirmation_required=true`
- `can_restore_now=false`
- `真实外发继续关闭=true`

这些字段是本地交付和售后维护的停止门禁，不是说明文字。

## 停止门禁

出现以下任一情况，不能把 H2W-8B 视为完成：

- 前端显示维护闭环已完成，但后端没有接收记录、处理单、签名更新包、备份、恢复演练或审计证据。
- 普通坐席可以读取本地维护总账。
- 接口发现真实外发、远程控制、静默更新、自动上传或原始客户文本泄露。
- 恢复演练返回 `can_restore_now=true`。
- 本地维护摘要只读页面没有标记 `data-h2w8b-local-maintenance="p3-06u-26h2w8b"`。
- 静态门禁或目标测试失败。

## 验收命令

```bash
backend/.venv/bin/python -m compileall backend/app
backend/.venv/bin/pytest backend/tests/test_local_maintenance_readiness_api.py
python3 scripts/check_p3_06u_26h2w8b_local_maintenance_readiness.py
node --check scripts/check_p3_06u_26h2w8b_local_maintenance_ui.mjs
node scripts/check_p3_06u_26h2w8b_local_maintenance_ui.mjs
cd frontend && npm run typecheck
cd frontend && npm run build
```

扩大回归建议：

```bash
backend/.venv/bin/pytest \
  backend/tests/test_local_maintenance_readiness_api.py \
  backend/tests/test_diagnostics_api.py \
  backend/tests/test_local_backups_api.py \
  backend/tests/test_signed_update_packages_api.py
```

## 已验证

- `backend/.venv/bin/python -m compileall backend/app` 通过。
- `backend/.venv/bin/pytest backend/tests/test_local_maintenance_readiness_api.py` 通过，结果 `2 passed`。
- `python3 scripts/check_p3_06u_26h2w8b_local_maintenance_readiness.py` 通过。
- `backend/.venv/bin/pytest backend/tests/test_local_maintenance_readiness_api.py backend/tests/test_diagnostics_api.py backend/tests/test_local_backups_api.py backend/tests/test_signed_update_packages_api.py` 通过，结果 `29 passed`。
- `backend/.venv/bin/pytest backend/tests` 全量通过，结果 `248 passed`。
- `cd frontend && npm run typecheck` 通过。
- `cd frontend && npm run build` 通过，仍只有既有 Vite chunk size warning。
- `node --check scripts/check_p3_06u_26h2w8b_local_maintenance_ui.mjs` 通过。
- `node scripts/check_p3_06u_26h2w8b_local_maintenance_ui.mjs` 通过；浏览器证据写入 `output/p3_06u_26h2w8b_local_maintenance_ui/`。
- 浏览器证据目录只保留 `summary.json`、截图和运行日志；脚本结束会清理临时 Chrome profile、临时 SQLite 和临时备份目录，避免把一次性登录态或测试库留作长期资料。

## 仍未完成

- 还没有把 50-100 条真实脱敏题库、知识包发布、质量报告和维护闭环串成 rehearsal。
- 还没有正式云端售后接收服务；当前仍是本地接收台和手动传输。
- 程序更新仍只支持 dry-run 演练计划，不替换文件、不重启服务、不跑真实迁移。
- 真实平台外发、真实 IM、RPA 正式交付和完整生产级 RAG 仍关闭。

## 下一步

优先补两件事：

1. 进入 H2W-11 前置 rehearsal，把客户知识包、50-100 条真实题库、质量报告签收和本地维护闭环做一次完整演练。
2. 后续如继续本地交付线，再补正式更新包签收、维护窗口、服务重启健康检查和程序版本回滚工具；仍不得跳过备份、审计和客户管理员确认。
