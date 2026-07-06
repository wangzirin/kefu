# P3-06U-26H2G 签名知识更新包应用与回滚第一片

## Engineering Control Card

- Stage: P3-06U-26H2G
- 当前主线阶段: 小微企业本地化交付后的远程运维闭环
- 上一阶段完成: H2F 已支持 `.wanfa-update` 签名更新包预检通过后的本地暂存
- 本阶段完成: 暂存的签名知识更新包可以由负责人/管理员确认后备份并应用，也可以按导入批次回滚
- 本阶段没有完成: 策略包应用、程序更新器、数据库物理快照、程序文件替换、服务重启、数据库迁移、客户授权自动上传、真实外部平台写入
- 安全边界: 不调用模型、不写外部平台、不执行程序包、不迁移数据库、不保存密码/token/私钥/真实客户聊天原文

## 一句话结论

H2G 把签名更新链路从“可信包已暂存”推进到“知识包可受控应用和回滚”。

现在的客户本地更新链路是：

```text
我方制作知识更新包
-> 打包为签名 .wanfa-update
-> 客户本地预检签名/摘要/版本
-> 客户管理员暂存
-> 客户管理员确认备份并应用
-> 系统调用知识更新包导入
-> 记录导入批次和备份快照
-> 必要时按导入批次回滚
```

这解决的是命中率下降、知识过期、标准答案补充和回归题补充问题，不解决程序升级问题。

## 后端新增能力

### 应用接口

```text
POST /api/signed-update-packages/{signed_update_package_id}/apply
```

请求体：

```json
{
  "reason": "客户管理员确认应用本次签名知识更新包。"
}
```

执行规则：

- 需要 `updates.manage` 权限。
- 只能操作当前租户下的暂存包。
- 只允许 `package_type=knowledge`。
- `program` 和 `strategy` 在本片继续阻断。
- 只允许 `status=staged` 的包应用。
- 应用时解析签名包里的 `wanfa.knowledge_update_package.v1` payload。
- 复用 H2D 的 `import_knowledge_update_package()`，不另写一套知识导入逻辑。
- 应用成功后写入：
  - `status=applied`
  - `backup_created=true`
  - `applied_at`
  - `knowledge_import_batch_id`
  - `backup_plan.snapshot`
  - `apply_result`
  - `signed_update_package.applied` 审计事件

### 回滚接口

```text
POST /api/signed-update-packages/{signed_update_package_id}/rollback
```

请求体：

```json
{
  "reason": "客户管理员确认回滚本次签名知识更新包。"
}
```

执行规则：

- 需要 `updates.manage` 权限。
- 只能回滚 `status=applied` 的知识包。
- 必须存在 `knowledge_import_batch_id`。
- 复用 H2D 的 `rollback_knowledge_update_package_import()`。
- 回滚动作只归档本次导入创建的业务对象、对象问答卡、知识文档和评测集。
- 回滚成功后写入：
  - `status=rolled_back`
  - `rollback_result`
  - `backup_plan.rollback_status`
  - `signed_update_package.rolled_back` 审计事件

## 备份口径

本片的备份是真实的应用前恢复依据，但不是完整数据库物理备份。

当前备份由两部分组成：

1. 知识导入前计数快照  
   `backup_plan.snapshot.scope = pre_import_counts_only`

2. 导入批次 created ids  
   `knowledge_import_batch_id` 对应的 `KnowledgeImportBatch.result_payload.created`

因此当前可以可靠回滚“本次知识更新包创建的新对象”，包括：

- `knowledge_cards`
- `business_objects`
- `object_knowledge_cards`
- `knowledge_documents`
- `evaluation_sets`

当前不能承诺：

- 数据库整库物理恢复。
- 程序文件版本恢复。
- 配置文件恢复。
- 运行进程版本切换。
- 外部渠道状态恢复。

后续程序更新器和完整备份恢复演练必须单独做。

## 前端新增能力

位置：

```text
管理运维 -> 账号与安全 -> 签名更新包预检
```

新增交互：

- 已暂存更新包列表显示中文状态：
  - `staged` -> 待应用
  - `applied` -> 已应用
  - `rolled_back` -> 已回滚
- 知识包 `staged` 状态显示“备份并应用”按钮。
- 知识包 `applied` 状态显示“回滚”按钮。
- 程序包和策略包显示当前阶段不应用，不给假按钮。
- 列表展示：
  - 包名称
  - 包类型
  - 版本
  - 暂存时间
  - 知识导入批次
  - 备份状态
  - 外发状态

## 安全边界

本片仍保持以下硬边界：

- `external_write_performed=false`
- `program_execution_performed=false`
- `database_migration_performed=false`
- 不调用模型。
- 不调用真实渠道 API。
- 不替换本地程序文件。
- 不重启服务。
- 不自动上传诊断包。
- 不保存私钥、token、密码或客户聊天原文。

程序包当前会被明确阻断：

```text
program update is not supported in this slice; only signed knowledge packages can be applied
```

## 验证结果

后端签名更新包测试：

```bash
cd /Users/ericlee/Desktop/01_项目工作区/肥肥lu/lite_a_customer_service/standard_ops/backend
./.venv/bin/python -m pytest tests/test_signed_update_packages_api.py -q
```

结果：

```text
10 passed
```

后端相关回归：

```bash
cd /Users/ericlee/Desktop/01_项目工作区/肥肥lu/lite_a_customer_service/standard_ops/backend
./.venv/bin/python -m pytest tests/test_signed_update_packages_api.py tests/test_knowledge_update_packages_api.py tests/test_diagnostics_api.py tests/test_accounts_api.py -q
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

- 使用临时 SQLite、临时后端 `8092`、临时前端 `5192`。
- 创建临时负责人账号。
- 暂存一次性签名知识包。
- 打开设置页。
- 点击“备份并应用”。
- 确认页面进入“已应用”并出现“回滚”。
- 点击“回滚”。
- 确认页面进入“已回滚”。
- 临时 token、公钥、包文件和 SQLite 已清理。

证据目录：

```text
/Users/ericlee/Desktop/01_项目工作区/肥肥lu/lite_a_customer_service/standard_ops/output/p3_06u_26h2g_signed_update_apply_ui
```

截图：

- `01_staged.png`
- `02_applied.png`
- `03_rolled_back.png`
- `summary.json`

## 当前真实成熟度

相对 H2 本地运维模型，本片把“知识更新闭环”推进到可试点状态：

- 客户可以收到我方签名知识包。
- 客户本地可以校验、暂存、应用和回滚。
- 我方可以通过诊断包定位知识问题，再回传知识修复包。
- 客户管理员仍保留本地确认权。

但它仍不是完整自动升级系统：

- 没有客户授权自动上传诊断包。
- 没有我方云端补丁管理台。
- 没有策略包应用。
- 没有程序更新器。
- 没有数据库物理备份恢复演练。
- 没有安装包级升级和旧进程替换确认。

## 下一步建议

下一片建议做 H2H：

1. 策略更新包应用第一片  
   用于低置信阈值、转人工规则、禁用承诺词、模型路由策略的小范围更新。

2. 完整备份恢复演练第一片  
   至少支持 SQLite 本地库的更新前文件快照、恢复脚本和恢复后健康检查。

3. 程序更新器设计落地第一片  
   先做“版本包预检 + 旧进程检测 + 不执行替换”的 dry-run，不直接替换程序文件。

4. 客户授权上传第一片  
   仍默认手动下载诊断包；自动上传必须走客户明确授权、脱敏和审计。
