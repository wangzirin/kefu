# P3-06U-26H2F 签名更新包暂存第一片

## Engineering Control Card

- Stage: P3-06U-26H2F
- 当前主线阶段: 本地应用售后更新链路第二片
- 上一阶段真正完成: H2E 签名更新包 dry-run 预检，覆盖签名、摘要、版本兼容、备份计划和健康检查计划
- 本片目标: 让预检通过的 `.wanfa-update` 更新包进入本地待处理暂存区，后续再由备份、健康检查和回滚流程继续处理
- 本片不做什么: 不执行更新、不创建真实备份、不迁移数据库、不替换程序文件、不重启服务、不调用模型、不写外部平台
- 产品口径: 这是更新包队列与审计的第一片，不是完整自动升级系统

## 为什么要把暂存单独拆出来

客户本地版的更新链路不能从“预检通过”直接跳到“立即应用”。中间必须有一个可审计的待处理状态：

1. 客户负责人或管理员拿到我方回传的签名更新包。
2. 本地系统先按 H2E 做签名、摘要和版本兼容预检。
3. 预检通过后，更新包被写入本地暂存表。
4. 暂存记录保留完整包体、预检结果、备份计划、健康检查计划和审计事件。
5. 后续 H2G / H2F-2 再进入真实备份、应用、健康检查和回滚。

这样做的意义是把“可信接收”和“危险执行”拆开，避免管理员误以为校验通过就已经可以覆盖本地数据或程序。

## 后端实现

新增数据表：

```text
signed_update_packages
```

唯一约束：

```text
tenant_id + package_id
```

核心字段：

| 字段 | 含义 |
| --- | --- |
| package_id | 更新包业务编号 |
| package_name | 更新包名称 |
| package_type | `knowledge` / `strategy` / `program` |
| package_version | 更新包版本 |
| current_app_version | 当前本地应用版本 |
| status | 当前为 `staged` |
| package_digest_sha256 | 完整更新包 canonical JSON 摘要 |
| package_payload | 完整更新包 JSON |
| preflight_result | H2E 预检结果 |
| backup_plan | 后续备份计划 |
| health_checks | 后续健康检查计划 |
| can_apply_now | 当前固定为 `false` |
| backup_required | 是否要求备份 |
| backup_created | 当前固定为 `false` |
| staged_by_id | 暂存操作人 |
| staged_at | 暂存时间 |
| applied_at | 当前为空 |
| error_message | 暂存失败或后续失败信息 |

新增迁移：

```text
backend/app/migrations/versions/0026_signed_update_packages.py
```

新增接口：

```text
POST /api/tenants/{tenant_id}/signed-update-package/staged
GET  /api/tenants/{tenant_id}/signed-update-package/staged
```

权限：

```text
updates.manage
```

当前只有负责人和管理员拥有 `updates.manage`。普通客服坐席不能预检、不能暂存、不能查看暂存更新包。

## 暂存规则

### 预检先行

暂存接口内部会先调用 H2E 预检逻辑。

只有满足以下条件才允许写入暂存表：

- manifest 签名有效。
- payload 摘要一致。
- 产品标识为 `wanfa-standard-ops`。
- 当前应用版本兼容。
- 预检结果 `can_stage=true`。

如果预检失败，接口返回 `400`，并把预检失败详情返回给前端。

### 幂等与冲突

同一个租户下：

- 同一个 `package_id` + 同一个完整包摘要：返回已有暂存记录，视为幂等。
- 同一个 `package_id` + 不同完整包摘要：返回 `409`，阻止覆盖。

这样可以避免客户重复点击导致重复记录，也能阻止同编号不同内容的更新包混入。

### 审计

暂存成功后写入审计事件：

```text
signed_update_package.staged
```

审计事件记录包编号、包类型、包版本和完整包摘要，不记录任何密码、token、API Key 或渠道密钥。

## 前端实现

入口仍在管理运维里的签名更新包区域。

新增能力：

- 在“校验更新包”旁增加“暂存更新包”按钮。
- 暂存前复用当前文本框里的 JSON 更新包。
- 暂存成功后刷新“已暂存更新包”列表。
- 列表展示包名、包类型、包版本、暂存时间和状态。
- 明确显示“未备份”和“执行关闭”。

前端要表达的口径：

- 暂存只是进入待处理队列。
- 当前没有创建备份。
- 当前不能执行更新。
- 程序文件、数据库迁移和真实平台外发都没有发生。

涉及文件：

- `frontend/src/api/client.ts`
- `frontend/src/App.tsx`
- `frontend/src/styles.css`

## 安全边界

本片必须保持以下事实：

```text
不执行更新
backup_created=false
can_apply_now=false
program_execution_performed=false
database_migration_performed=false
external_write_performed=false
真实外发继续关闭
```

明确没有完成：

- 没有创建数据库快照。
- 没有复制知识库文件。
- 没有导入知识更新包。
- 没有应用策略更新包。
- 没有替换前端或后端程序文件。
- 没有执行 Alembic 迁移。
- 没有停止或重启服务。
- 没有执行健康检查。
- 没有回滚。
- 没有调用模型。
- 没有向微信、抖音、淘宝、京东、拼多多或其他平台发送消息。

## 已验证内容

### TDD 红灯

在实现暂存接口前新增三条 H2F 测试，运行：

```bash
cd backend && ./.venv/bin/python -m pytest tests/test_signed_update_packages_api.py -q
```

预期失败：

```text
3 failed with 404
```

说明接口尚未实现，测试先红。

### 后端针对性测试

实现后运行：

```bash
cd backend && ./.venv/bin/python -m pytest tests/test_signed_update_packages_api.py -q
```

结果：

```text
7 passed
```

覆盖：

- 负责人可暂存合法签名更新包。
- 篡改包不能暂存。
- 普通客服坐席不能暂存。
- 暂存记录保留包体、预检结果、备份计划和健康检查计划。
- 暂存不创建备份、不允许立即执行。

### 后端相关回归

运行：

```bash
cd backend && ./.venv/bin/python -m pytest tests/test_signed_update_packages_api.py tests/test_knowledge_update_packages_api.py tests/test_diagnostics_api.py tests/test_accounts_api.py -q
```

结果：

```text
19 passed
```

覆盖 H2B 账号治理、H2C 诊断包、H2D 知识更新包、H2E 签名预检和 H2F 暂存。

### 迁移编译

运行：

```bash
cd backend && ./.venv/bin/python -m py_compile app/migrations/versions/0026_signed_update_packages.py
```

结果通过。

注意：本机 shell 中直接运行 `python -m py_compile ...` 曾失败，原因是当前 shell 没有 `python` 命令；使用项目虚拟环境的 `./.venv/bin/python` 后通过。

### 前端验证

运行：

```bash
cd frontend && npm run typecheck
cd frontend && npm run build
```

结果通过。`npm run build` 仍有既有 Vite chunk 体积提醒，不是本片新增失败。

### 浏览器 smoke

使用独立临时后端端口、独立临时前端端口、临时 SQLite 数据库和临时 Chrome profile：

- 真实登录本地负责人账号。
- 打开系统设置。
- 确认“签名更新包预检”卡片存在。
- 确认“暂存更新包”按钮存在。
- 确认“已暂存更新包”列表存在。
- 确认空状态提示存在。
- 确认界面显示“执行关闭”。

CDP 文本检查结果：

```json
{
  "hash": "#settings",
  "hasPreflight": true,
  "hasStageButton": true,
  "hasStagedList": true,
  "hasEmpty": true,
  "hasExecutionClosed": true
}
```

截图证据：

```text
/Users/ericlee/Desktop/01_项目工作区/肥肥lu/lite_a_customer_service/standard_ops/output/p3_06u_26h2f_signed_update_stage_smoke.png
```

H2F smoke 使用的临时后端、临时前端、无头 Chrome 和临时 SQLite 数据库已经清理；正式本地预览服务不受影响。

## 对客户本地运维模型的意义

H2F 把“我们回传签名包”推进到了可审计的本地待处理状态：

1. 客户系统不再只会看包，还能保存可信更新包。
2. 更新包保存后有租户、操作人、时间和审计事件。
3. 同编号不同内容会被阻断。
4. 普通坐席无法触碰更新包入口。
5. 暂存记录为后续备份、应用、健康检查和回滚提供固定输入。

这解决的是“客户本地如何安全接收并排队处理更新包”。它还没有解决“如何真正应用更新包”。

## 下一步

建议进入 H2G / H2F-2，先做知识与策略更新的保守应用链：

1. 暂存更新包应用前创建真实本地备份快照。
2. 知识类 `.wanfa-update` 调用 H2D 知识更新包导入能力。
3. 导入后运行账户登录、知识检索、评测题和健康接口 smoke。
4. 失败时从备份快照回滚。
5. 所有应用、健康检查和回滚都写审计事件。

程序更新器继续后置。程序更新涉及停止进程、替换文件、数据库迁移、启动新进程、验证运行版本和端口切换，比知识包应用风险更高。
