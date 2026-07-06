# P3-06U-26H2H 本地 SQLite 物理备份与恢复演练第一片

## Engineering Control Card

- Stage: P3-06U-26H2H
- 当前主线阶段: 小微企业本地化交付后的备份、更新和售后运维收束
- 上一阶段完成: H2G 已支持签名知识更新包的应用与按导入批次回滚
- 本阶段完成: 文件型 SQLite 本地库可以由负责人/管理员创建物理备份点，并在前端执行完整性校验
- 本阶段没有完成: 在线覆盖恢复、程序文件替换、数据库迁移、策略包应用、程序更新器、客户授权上传、定期上传、远程维护通道
- 安全边界: 不调用模型、不上传诊断包、不写外部平台、不执行程序包、不覆盖运行中的数据库、不保存密码/token/私钥/真实客户聊天原文

## 一句话结论

H2H 把本地交付里的“更新前必须备份”从文档要求推进为可操作能力。

当前更新链路已经可以做到：

```text
客户管理员登录本地工作台
-> 管理运维
-> 账号与安全
-> 本地备份点
-> 创建数据库物理备份
-> 校验 sha256 和 SQLite integrity_check
-> 后续再导入知识/策略/程序更新包
```

这一步不是为了让客户自己折腾数据库，而是让后续知识包、策略包和程序包应用前都有可审计的本地恢复依据。

## 后端新增能力

### 数据表

新增 `local_backup_records`：

- `backup_id`: 本地备份编号。
- `backup_type`: 当前为 `sqlite_database`。
- `status`: `created`、`verified` 或 `verification_failed`。
- `file_name`: 备份文件名。
- `file_path`: 后端内部保存的本机路径，不返回给前端。
- `file_size_bytes`: 文件大小。
- `sha256`: 备份文件摘要。
- `source_database_label`: 源数据库文件名。
- `source_database_hash`: 源数据库路径 hash，不暴露原始绝对路径。
- `restore_mode`: 当前固定为 `manual_rehearsal_only`。
- `manifest_payload`: 备份清单、恢复边界和最近校验结果。
- `created_by_id`、`created_at`、`verified_at`、`error_message`。

迁移文件：

```text
backend/app/migrations/versions/0027_local_backup_records.py
```

### 创建备份接口

```text
POST /api/tenants/{tenant_id}/local-backups
```

请求体：

```json
{
  "reason": "客户管理员手动创建本地数据库备份点。"
}
```

执行规则：

- 需要 `updates.manage` 权限。
- 只能操作当前登录账号所属租户。
- 只支持文件型 SQLite。
- 内存 SQLite 会返回 `409`，避免生成假备份。
- 非 SQLite 数据库当前返回不支持，后续 PostgreSQL 需要单独做 `pg_dump` 或快照方案。
- 备份采用 SQLite backup API，不直接粗暴复制正在运行的数据库文件。
- 生成 `.sqlite3` 备份文件和 `.manifest.json` 清单。
- 写入 `local_backup.created` 审计事件。
- API 返回不包含本机绝对 `file_path`。

### 列表接口

```text
GET /api/tenants/{tenant_id}/local-backups
```

执行规则：

- 需要 `updates.manage` 权限。
- 只返回当前租户的备份记录。
- 按创建时间倒序返回。
- 前端只展示最近备份点，避免把设置页做成复杂备份中心。

### 校验接口

```text
POST /api/local-backups/{local_backup_id}/verify
```

请求体：

```json
{
  "reason": "客户管理员执行本地备份完整性校验。"
}
```

校验内容：

- 备份文件是否存在。
- 当前文件 `sha256` 是否和记录一致。
- SQLite `PRAGMA integrity_check` 是否返回 `ok`。

校验成功后：

- `status=verified`
- 写入 `verified_at`
- 写入 `manifest_payload.last_verification`
- 写入 `local_backup.verified` 审计事件

校验失败后：

- `status=verification_failed`
- 写入 `error_message`
- 写入 `local_backup.verification_failed` 审计事件

## 前端新增能力

位置：

```text
管理运维 -> 账号与安全 -> 本地备份点
```

新增内容：

- “创建备份点”按钮。
- 最近备份点列表。
- 备份状态中文展示：
  - `created` -> 已创建
  - `verified` -> 已校验
  - `verification_failed` -> 校验失败
- 文件名、创建时间、文件大小、sha256 短码。
- “校验”按钮。
- 清晰提示当前只做“恢复演练”，不直接覆盖正在运行的本地库。

前端调用：

- `listLocalBackups()`
- `createLocalBackup()`
- `verifyLocalBackup()`

## 为什么不直接做在线恢复

本片没有做“点击后直接覆盖当前数据库”，这是刻意边界。

原因：

1. 正在运行的后端服务可能占用 SQLite 文件。
2. 在线覆盖数据库容易破坏当前连接和事务。
3. 恢复动作应该先停服务、确认目标版本、校验备份、替换文件、重启服务、跑健康检查。
4. 真实客户环境需要二次确认，不能让一个网页按钮直接执行破坏性恢复。

所以当前 `restore_mode=manual_rehearsal_only`。下一片可以做“生成恢复计划”和“离线恢复工具 dry-run”，再进入真正的受控恢复。

## 与 H2G 的关系

H2G 的知识包应用已经有导入前计数快照和导入批次回滚，但那不是整库物理备份。

H2H 新增的是整库级恢复依据：

| 能力 | H2G | H2H |
| --- | --- | --- |
| 知识新增对象回滚 | 已完成 | 保留 |
| 导入批次 created ids | 已完成 | 保留 |
| SQLite 数据库物理备份 | 未完成 | 已完成第一片 |
| 备份 sha256 校验 | 未完成 | 已完成 |
| SQLite integrity_check | 未完成 | 已完成 |
| 在线恢复覆盖运行库 | 未完成 | 未做，继续阻断 |

## 安全边界

本片保持以下硬边界：

- `external_upload_performed=false`
- `external_platform_write_performed=false`
- `model_call_performed=false`
- `live_restore_performed=false`
- `database_file_path_exposed_to_frontend=false`
- 前端不展示本机数据库绝对路径。
- 文档和日志不保存 token、密码、私钥或真实客户聊天原文。
- 真实外发继续关闭。

## 验证结果

后端本地备份测试：

```bash
cd /Users/ericlee/Desktop/01_项目工作区/肥肥lu/lite_a_customer_service/standard_ops/backend
./.venv/bin/python -m pytest tests/test_local_backups_api.py -q
```

结果：

```text
3 passed
```

后端相关回归：

```bash
cd /Users/ericlee/Desktop/01_项目工作区/肥肥lu/lite_a_customer_service/standard_ops/backend
./.venv/bin/python -m pytest tests/test_local_backups_api.py tests/test_signed_update_packages_api.py tests/test_diagnostics_api.py tests/test_accounts_api.py -q
```

结果：

```text
22 passed
```

前端类型检查：

```bash
cd /Users/ericlee/Desktop/01_项目工作区/肥肥lu/lite_a_customer_service/standard_ops/frontend
npm run typecheck
```

结果：通过。

前端构建：

```bash
cd /Users/ericlee/Desktop/01_项目工作区/肥肥lu/lite_a_customer_service/standard_ops/frontend
npm run build
```

结果：通过；仍有既有 Vite chunk 体积提醒。

浏览器 smoke：

- 临时 SQLite。
- 临时后端 `8094`。
- 临时前端 `5194`。
- 临时 headless Chrome。
- 创建临时负责人账号。
- 打开 `#settings`。
- 看到“本地备份点”。
- 点击“创建备份点”。
- 点击“校验”。
- 页面出现“校验结果：已校验”。

截图和摘要：

```text
output/p3_06u_26h2h_local_backup_ui/screenshots/01_local_backup_card.png
output/p3_06u_26h2h_local_backup_ui/screenshots/02_backup_created.png
output/p3_06u_26h2h_local_backup_ui/screenshots/03_backup_verified.png
output/p3_06u_26h2h_local_backup_ui/summary.json
```

临时 SQLite 和备份库副本已清理，只保留截图与摘要。

## 当前还不能承诺

仍不能承诺：

- 程序包自动升级。
- 数据库迁移自动回滚。
- 在线一键恢复正在运行的 SQLite。
- PostgreSQL 物理备份。
- 客户授权自动上传诊断包。
- 定期上传质量摘要。
- 策略包应用。
- 真实外部平台自动发送。

## 下一步建议

继续 H2 主线时，建议按以下顺序推进：

1. `P3-06U-26H2I`：策略更新包应用第一片，只允许修改本地回复策略、转人工阈值和禁用承诺，必须支持预览差异和回滚。
2. `P3-06U-26H2J`：程序更新器 dry-run 第一片，只校验包、生成维护窗口计划、检查备份点，不替换程序文件。
3. `P3-06U-26H2K`：客户授权上传诊断包第一片，必须由客户手动确认，默认不开定期上传。
4. `P3-06U-26H2L`：本地恢复工具 dry-run，先生成停服务、替换、重启、健康检查步骤，不执行破坏性覆盖。
