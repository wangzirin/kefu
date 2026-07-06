# P3-06U-26H2I 签名策略更新包应用与回滚第一片

## Engineering Control Card

- Stage: P3-06U-26H2I
- 当前主线阶段: 小微企业本地化交付后的诊断包、更新包、备份和售后运维闭环
- 上一阶段完成: H2H 已支持本地 SQLite 物理备份点创建与 sha256 / integrity_check 校验
- 本阶段完成: 签名 `strategy` 更新包可以应用到本地回复策略，并支持回滚
- 本阶段没有完成: 程序更新器、程序文件替换、数据库迁移、服务重启、客户授权上传、离线恢复工具、真实平台外发
- 安全边界: 不调用模型、不上传诊断包、不写外部平台、不执行程序包、不保存密码/token/私钥/真实客户聊天原文

## 一句话结论

H2I 把“命中率下降不一定要升级程序”落实到可操作能力：

```text
诊断包暴露问题
-> 我方生成签名策略更新包
-> 客户负责人/管理员本地预检和暂存
-> 创建策略快照
-> 应用回复策略
-> 后续入站消息按新阈值、阻断词和转人工词决策
-> 如效果不对，回滚到上一份策略或关闭本次新增策略
```

策略包用于修复回复边界和路由规则，不用于新增知识内容，也不用于替换程序文件。

## 后端新增能力

### 数据表

新增 `tenant_reply_strategies`：

- `tenant_id`: 每个租户最多一份当前回复策略。
- `strategy_id`: 策略标识。
- `strategy_version`: 策略版本。
- `status`: `active` 或 `inactive`。
- `strategy_payload`: 当前策略内容。
- `previous_strategy_payload`: 应用前策略快照。
- `signed_update_package_id`: 来源签名更新包。
- `updated_by_id`、`created_at`、`updated_at`。

迁移文件：

```text
backend/app/migrations/versions/0028_tenant_reply_strategies.py
```

### 策略包格式

策略包 payload 使用：

```json
{
  "schema_version": "wanfa.reply_strategy_update.v1",
  "strategy_id": "local-support-risk-policy",
  "strategy_version": "2026.07.03.strategy.1",
  "reply_policy": {
    "auto_reply_threshold": 0.82,
    "manual_review_threshold": 0.5,
    "blocked_policy_terms": ["终身保证"],
    "manual_review_terms": ["退一赔三"],
    "force_draft_only": true
  },
  "model_routing": {
    "default_provider": "auto",
    "fast_model": "qwen3.6-flash",
    "standard_model": "qwen3.7-plus",
    "premium_model": "qwen3.7-max",
    "fallback_provider": "deepseek"
  }
}
```

第一片真正接入运行时的是：

- `auto_reply_threshold`
- `manual_review_threshold`
- `blocked_policy_terms`
- `manual_review_terms`
- `force_draft_only`

`model_routing` 当前先作为策略配置保存和展示证据，后续再接入模型网关运行时。这样可以避免一口气改动模型调用、成本和外部 provider。

### 应用策略包

沿用已有接口：

```text
POST /api/signed-update-packages/{signed_update_package_id}/apply
```

执行规则：

- 需要 `updates.manage` 权限。
- 包必须已通过签名预检并处于 `staged`。
- `package_type=strategy` 时走策略应用路径。
- 应用前保存现有策略快照。
- 写入或更新 `tenant_reply_strategies`。
- 更新签名包状态为 `applied`。
- 写入 `signed_update_package.strategy_applied` 审计事件。
- 安全标志保持：
  - `external_write_performed=false`
  - `provider_call_performed=false`
  - `program_execution_performed=false`
  - `database_migration_performed=false`

### 回滚策略包

沿用已有接口：

```text
POST /api/signed-update-packages/{signed_update_package_id}/rollback
```

执行规则：

- 需要 `updates.manage` 权限。
- 包必须处于 `applied`。
- 如果应用前存在旧策略，则恢复旧策略。
- 如果应用前没有旧策略，则把当前策略置为 `inactive`，后续回复决策回到默认策略。
- 更新签名包状态为 `rolled_back`。
- 写入 `signed_update_package.strategy_rolled_back` 审计事件。

## 回复决策运行时变化

`reply_decisions` 现在会读取当前租户的 active 策略：

- 默认阻断词仍保留。
- 策略包新增阻断词会与默认阻断词合并。
- 默认转人工词仍保留。
- 策略包新增转人工词会与默认转人工词合并。
- 策略包阈值会覆盖请求中的默认阈值。
- `force_draft_only=true` 会强制后续回复保持草稿模式，不允许进入外发许可状态。

这意味着策略包应用后，新的入站消息会受到策略影响；不是只在更新中心里显示一个“已应用”状态。

## 前端变化

位置：

```text
管理运维 -> 账号与安全 -> 签名更新包预检
```

变化：

- `knowledge` 包继续可应用和回滚。
- `strategy` 包现在也可应用和回滚。
- `program` 包继续显示当前阶段不应用。
- 已应用策略包展示策略版本。
- 应用和回滚按钮文案从“签名知识更新包”改为“签名更新包”，避免误导。

## 与 H2G / H2H 的关系

| 能力 | H2G | H2H | H2I |
| --- | --- | --- | --- |
| 知识包应用 | 已完成 | 保留 | 保留 |
| 知识包回滚 | 已完成 | 保留 | 保留 |
| SQLite 物理备份 | 未完成 | 已完成第一片 | 保留 |
| 策略包预检/暂存 | 已完成 | 保留 | 保留 |
| 策略包应用 | 未完成 | 未完成 | 已完成第一片 |
| 策略包回滚 | 未完成 | 未完成 | 已完成第一片 |
| 程序包应用 | 阻断 | 阻断 | 继续阻断 |

## 安全边界

本片保持以下硬边界：

- 不执行程序包。
- 不替换程序文件。
- 不重启服务。
- 不执行数据库迁移。
- 不调用模型。
- 不上传诊断包。
- 不写外部平台。
- 真实外发继续关闭。
- 策略包只影响后续本地回复决策，不 retroactively 改写历史会话。

## 验证结果

后端签名更新包测试：

```bash
cd /Users/ericlee/Desktop/01_项目工作区/肥肥lu/lite_a_customer_service/standard_ops/backend
./.venv/bin/python -m pytest tests/test_signed_update_packages_api.py -q
```

结果：

```text
11 passed
```

回复决策回归：

```bash
cd /Users/ericlee/Desktop/01_项目工作区/肥肥lu/lite_a_customer_service/standard_ops/backend
./.venv/bin/python -m pytest tests/test_reply_decisions_api.py -q
```

结果：

```text
5 passed
```

综合相关回归：

```bash
cd /Users/ericlee/Desktop/01_项目工作区/肥肥lu/lite_a_customer_service/standard_ops/backend
./.venv/bin/python -m pytest tests/test_signed_update_packages_api.py tests/test_reply_decisions_api.py tests/test_local_backups_api.py tests/test_diagnostics_api.py tests/test_accounts_api.py -q
```

结果：

```text
28 passed
```

前端验证：

```bash
cd /Users/ericlee/Desktop/01_项目工作区/肥肥lu/lite_a_customer_service/standard_ops/frontend
npm run typecheck
npm run build
```

结果：

```text
typecheck passed
build passed
```

保留一个既有 Vite chunk 警告：`OpsDashboardChart` 和主 bundle 均大于 500 kB；这不是 H2I 新增阻断，后续可单独做前端拆包。

浏览器冒烟：

```bash
cd /Users/ericlee/Desktop/01_项目工作区/肥肥lu/lite_a_customer_service/standard_ops
node output/p3_06u_26h2i_signed_strategy_update_ui/run_smoke.mjs
```

验证结果：

```text
passed
```

浏览器冒烟覆盖：

- 临时 SQLite 本地库建表和 stamp。
- 临时后端 `/health` 通过。
- 临时前端 dev server 通过。
- UI 创建本地负责人账号。
- UI 粘贴签名 `strategy` 更新包并预检通过。
- UI 暂存策略包。
- UI 应用策略包，已应用卡片展示策略版本。
- UI 回滚策略包。
- 全程无真实外发、无模型调用、无程序执行、无数据库迁移。

证据文件：

```text
output/p3_06u_26h2i_signed_strategy_update_ui/summary.json
output/p3_06u_26h2i_signed_strategy_update_ui/screenshots/01_strategy_staged.png
output/p3_06u_26h2i_signed_strategy_update_ui/screenshots/02_strategy_applied.png
output/p3_06u_26h2i_signed_strategy_update_ui/screenshots/03_strategy_rolled_back.png
```

策略包专项测试覆盖：

- 签名策略包可以暂存。
- 负责人可以应用策略包。
- 应用后写入 `tenant_reply_strategies`。
- 新增阻断词会影响后续 `reply_decisions`。
- 回滚后策略置为 `inactive`。
- 回滚后同一问题不再被该新增阻断词阻断。
- 审计事件包含 `signed_update_package.strategy_applied` 和 `signed_update_package.strategy_rolled_back`。

## 下一步

- P3-06U-26H2J：程序更新器 dry-run 第一片。
- P3-06U-26H2K：客户授权上传诊断包第一片。
- P3-06U-26H2L：本地恢复工具 dry-run。
- 月度质量复盘：把诊断包、知识包、策略包、题库回归和客户反馈连成售后运营节奏。
