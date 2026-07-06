# P3-06U-26H2W6B 受控更新计划

日期：2026-07-04

## 定位

本片承接 `P3-06U-26H2W6 本地更新恢复处理单第一片`，把售后处理单和签名更新中心连接起来。

它解决的是：客户本地生成诊断包以后，我方基于处理单准备签名更新包，客户本地中台能够看到这份处理单对应哪一个更新包、更新包当前处于什么状态、下一步需要备份、应用、回滚还是质量回归。

它不是完整自动更新器，不远程控制客户电脑，不静默更新客户环境，不替客户自动点击应用，不打开真实平台外发。

真实外发继续关闭。企业微信、公众号、抖音、小红书、淘宝、京东、拼多多等真实消息发送仍需官方授权、测试白名单、回执、失败重试和审计闭环后单独验收。

## 本片完成内容

### 后端

- 新增处理单绑定签名更新包计划接口：
  - `POST /api/tenants/{tenant_id}/diagnostic-remediation-requests/{request_id}/signed-update-plan`
- 新增 schema：
  - `DiagnosticRemediationUpdatePlanCreate`
- 新增服务函数：
  - `create_diagnostic_remediation_update_plan`
- 新增计划 schema：
  - `p3-06u-26h2w6b.signed_update_control_plan.v1`
- 处理单状态新增：
  - `update_plan_prepared`
- 新增审计动作：
  - `diagnostic_remediation.signed_update_plan_created`
- 计划会读取签名更新包真实状态：
  - `staged`
  - `applied`
  - `rolled_back`
- 计划会读取本地备份摘要，但不暴露本机绝对路径。

### 前端

- “账号安全 -> 售后接收台 -> 处理回传包”新增受控更新计划入口。
- 处理单可以从已暂存签名更新包中选择一个包生成计划。
- 已有计划的处理单可以刷新计划。
- 处理单内展示：
  - 更新包名称
  - 更新包类型
  - 更新包状态
  - 生命周期步骤
  - “只生成计划”的边界
- 前端不会从处理单计划里提供“应用”或“回滚”执行按钮。
- 真正的应用、回滚仍留在签名更新中心，由客户管理员手动确认。

## 计划字段

`signed_update_control_plan` 写入 `diagnostic_remediation_requests.update_request_manifest`。

核心字段：

| 字段 | 含义 |
|---|---|
| `schema_version` | 固定为 `p3-06u-26h2w6b.signed_update_control_plan.v1` |
| `request_id` | 处理单编号 |
| `signed_update_package` | 被绑定的签名更新包摘要 |
| `preflight_summary` | 签名、摘要、版本兼容预检摘要 |
| `local_backup` | 最近本地备份点摘要 |
| `lifecycle_steps` | 诊断复核、预检、暂存、备份、应用、回滚、质量回归步骤 |
| `can_apply_from_plan_now` | 固定 `false` |
| `can_rollback_from_plan_now` | 固定 `false` |
| `plan_generated_only` | 固定 `true` |

## 生命周期状态

| 步骤 | 当前含义 |
|---|---|
| `review_diagnostic` | 处理单已经生成并可复核 |
| `preflight` | 签名、摘要和版本兼容检查 |
| `stage` | 更新包已经进入暂存区 |
| `local_backup` | 已有备份、可创建备份或存在阻断 |
| `apply` | 仅提示签名更新中心是否可以人工应用，不从计划执行 |
| `rollback` | 仅提示签名更新中心是否可以人工回滚，不从计划执行 |
| `quality_regression` | 更新后需要回归评测和质量复盘 |

## 安全边界

计划和处理单安全字段必须保持保守：

- `remote_control_performed=false`
- `customer_environment_write_performed=false`
- `automatic_update_performed=false`
- `silent_update_performed=false`
- `network_push_performed=false`
- `external_write_performed=false`
- `plan_generated_only=true`
- `can_apply_now=false`
- `can_apply_from_plan_now=false`
- `can_rollback_from_plan_now=false`

程序包继续只允许 `program-dry-run`，不允许直接替换程序文件，不执行数据库迁移，不重启服务。

## 验收门禁

本片完成必须满足：

1. 处理单可以绑定同租户的已暂存签名更新包。
2. 不同租户或不存在的更新包不能绑定。
3. 绑定后处理单状态变为 `update_plan_prepared`。
4. 计划里能看到更新包真实状态。
5. 更新包应用后刷新计划，`apply` 步骤变为 `passed`。
6. 更新包回滚后刷新计划，`rollback` 步骤变为 `passed`。
7. 计划接口不能执行应用或回滚。
8. 计划接口不能打开真实外发。
9. 前端有“生成计划/刷新计划”真实动作。
10. 前端不得把计划写成“已更新客户环境”。

## 停止门禁

出现以下任一情况必须停止：

1. 计划接口自动调用应用、回滚或程序更新。
2. 计划里 `can_apply_from_plan_now=true`。
3. 处理单绑定了其他租户的更新包。
4. 程序包被写成可直接应用。
5. 页面把静默更新、远程修复或真实外发写成已完成能力。
6. 没有审计事件却声称计划已生成。
7. 没有后端测试，只靠前端截图声称完成。

## 验证命令

```bash
cd /Users/ericlee/Desktop/01_项目工作区/肥肥lu/lite_a_customer_service/standard_ops
python3 scripts/check_p3_06u_26h2w6b_signed_update_plan_static.py
node --check scripts/check_p3_06u_26h2w6b_signed_update_plan_ui.mjs
node scripts/check_p3_06u_26h2w6b_signed_update_plan_ui.mjs
backend/.venv/bin/python -m pytest backend/tests/test_diagnostics_api.py::test_owner_can_link_remediation_to_signed_update_plan_and_refresh_status -q
backend/.venv/bin/python -m pytest backend/tests/test_diagnostics_api.py backend/tests/test_signed_update_packages_api.py backend/tests/test_local_backups_api.py -q
cd frontend && npm run typecheck && npm run build
```

浏览器证据：

- `/Users/ericlee/Desktop/01_项目工作区/肥肥lu/lite_a_customer_service/standard_ops/output/p3_06u_26h2w6b_signed_update_plan_ui/desktop-1440-signed-update-plan.png`
- `/Users/ericlee/Desktop/01_项目工作区/肥肥lu/lite_a_customer_service/standard_ops/output/p3_06u_26h2w6b_signed_update_plan_ui/summary.json`

## 下一步

继续 H2W-6C 时，建议补本地更新中心的“计划筛选和更新后质量回归入口”，但仍然保持：

- 不做静默更新。
- 不做远程控制。
- 不打开真实外发。
- 程序包继续只做 dry-run。
- 应用和回滚必须保留客户管理员手动确认。
