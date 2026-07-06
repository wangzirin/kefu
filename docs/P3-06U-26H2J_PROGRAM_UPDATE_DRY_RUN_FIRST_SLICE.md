# P3-06U-26H2J 程序更新演练计划第一片

## Engineering Control Card

- Stage: P3-06U-26H2J
- 当前主线阶段: 小微企业本地化交付后的诊断包、更新包、备份和售后运维闭环
- 上一阶段完成: H2I 已支持签名 `strategy` 更新包应用与回滚，并接入回复决策运行时
- 本阶段完成: 签名 `program` 更新包可以生成程序更新演练计划
- 本阶段没有完成: 程序文件替换、数据库迁移、服务重启、在线覆盖恢复、无人值守程序升级、客户授权上传、真实平台外发
- 安全边界: 不调用模型、不写外部平台、不保存密码/token/私钥/真实客户聊天原文；程序包仍不能真实应用

## 一句话结论

H2J 把“程序更新不能直接点一下就升级”落实为可见的本地演练能力：

```text
我方生成签名 program 更新包
-> 客户负责人/管理员本地预检
-> 暂存更新包
-> 生成程序更新演练计划
-> 查看目标版本、文件清单、迁移计划、维护窗口、回滚要求和阻断动作
-> 真实程序应用继续关闭
```

这一步的价值不是升级程序，而是让客户和我们在真正升级前确认“会检查什么、需要备份什么、哪些动作当前被禁止、为什么需要维护窗口”。

## 为什么需要程序更新演练

客户本地安装版后续一定会遇到程序升级问题，例如：

- 前端页面升级。
- 后端接口升级。
- 数据库结构新增字段。
- 更新中心自身能力升级。
- 本地诊断、备份、恢复工具升级。

但程序升级的风险高于知识包和策略包：

- 可能替换本地程序文件。
- 可能需要数据库迁移。
- 可能需要停止服务或重启服务。
- 可能导致客户本地工作台短暂不可用。
- 失败后需要上一版本程序包和数据库备份才能回滚。

因此 H2J 只开放演练计划，不开放真实程序应用。

## 后端新增能力

新增接口：

```text
POST /api/signed-update-packages/{signed_update_package_id}/program-dry-run
```

执行规则：

- 需要 `updates.manage` 权限。
- 更新包必须属于当前登录租户。
- 包必须已经暂存。
- `package_type` 必须是 `program`。
- 包状态必须保持 `staged`。
- 不创建真实备份。
- 不替换程序文件。
- 不执行数据库迁移。
- 不重启服务。
- 不调用模型。
- 不写外部平台。
- 写入 `signed_update_package.program_dry_run` 审计事件。

返回结果写入暂存包的 `preflight_result.program_dry_run_result`。

## 演练计划内容

演练结果包含：

- `dry_run_status=planned`
- 当前应用版本。
- 目标程序版本。
- 是否需要维护窗口。
- 程序包 payload 摘要。
- 文件数量和文件路径摘要。
- 迁移数量和迁移编号摘要。
- 需要影响的服务。
- 回滚要求。
- 计划步骤。
- 被阻断动作。
- 安全标志。

当前计划步骤：

| 步骤 | 状态 | 说明 |
| --- | --- | --- |
| 校验签名和摘要 | planned | 确认更新包可信且未被篡改 |
| 创建本地备份点 | required_before_apply | 程序更新前必须完成数据库物理备份和完整性校验 |
| 核对程序文件清单 | planned | 只读取文件路径、摘要和大小，不写入文件 |
| 迁移兼容性演练 | planned | 只生成迁移演练计划，不执行迁移 |
| 确认维护窗口 | required_before_apply | 客户管理员必须确认停机、重启和回滚窗口 |
| 生成更新后 smoke 清单 | planned | 列出登录、知识库、工作台和更新中心检查项 |
| 生成回滚方案 | planned | 确认上一版本程序包和更新前数据库备份 |

当前显式阻断动作：

- `replace_program_files`
- `execute_migrations`
- `restart_service`
- `external_write`
- `provider_call`
- `delete_existing_bundle`

## 前端变化

位置：

```text
管理运维 -> 账号与安全 -> 签名更新包预检
```

变化：

- `knowledge` 包继续支持“备份并应用”和“回滚”。
- `strategy` 包继续支持“备份并应用”和“回滚”。
- `program` 包不显示“备份并应用”按钮。
- `program` 包在暂存后显示“生成演练计划”。
- 演练计划生成后展示：
  - 目标版本。
  - 是否需要维护窗口。
  - 前三项计划步骤。
  - 已阻断动作。
  - “程序包只生成演练计划，不替换文件”的安全提示。

## 与 H2G / H2H / H2I 的关系

| 能力 | H2G | H2H | H2I | H2J |
| --- | --- | --- | --- | --- |
| 知识包应用/回滚 | 已完成 | 保留 | 保留 | 保留 |
| SQLite 物理备份校验 | 未完成 | 已完成第一片 | 保留 | 保留 |
| 策略包应用/回滚 | 未完成 | 未完成 | 已完成第一片 | 保留 |
| 程序包预检/暂存 | 已完成 | 保留 | 保留 | 保留 |
| 程序更新演练计划 | 未完成 | 未完成 | 未完成 | 已完成第一片 |
| 程序包真实应用 | 阻断 | 阻断 | 阻断 | 继续阻断 |

## 安全边界

本片保持以下硬边界：

- 程序包仍不能真实应用。
- 不替换程序文件。
- 不执行数据库迁移。
- 不停止或重启服务。
- 不删除现有程序包。
- 不调用模型。
- 不上传诊断包。
- 不写外部平台。
- 真实外发继续关闭。
- 只生成演练计划，不改变客户业务数据。

## 验证结果

后端签名更新包测试：

```bash
cd /Users/ericlee/Desktop/01_项目工作区/肥肥lu/lite_a_customer_service/standard_ops/backend
./.venv/bin/python -m pytest tests/test_signed_update_packages_api.py -q
```

结果：

```text
13 passed
```

综合相关回归：

```bash
cd /Users/ericlee/Desktop/01_项目工作区/肥肥lu/lite_a_customer_service/standard_ops/backend
./.venv/bin/python -m pytest tests/test_signed_update_packages_api.py tests/test_reply_decisions_api.py tests/test_local_backups_api.py tests/test_diagnostics_api.py tests/test_accounts_api.py -q
```

结果：

```text
30 passed
```

后端编译检查：

```bash
cd /Users/ericlee/Desktop/01_项目工作区/肥肥lu/lite_a_customer_service/standard_ops/backend
./.venv/bin/python -m py_compile app/services/signed_updates.py app/api/signed_updates.py app/schemas/signed_updates.py
```

结果：

```text
passed
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

保留一个既有 Vite chunk 警告：部分 bundle 大于 500 kB；这不是 H2J 新增阻断。

浏览器冒烟：

```bash
cd /Users/ericlee/Desktop/01_项目工作区/肥肥lu/lite_a_customer_service/standard_ops
node scripts/check_p3_06u_26h2j_program_update_dry_run_ui.mjs
```

结果：

```text
PASS p3-06u-26h2j program update dry-run UI smoke
```

浏览器冒烟覆盖：

- 临时 SQLite 本地库建表和 stamp。
- 临时后端 `/health` 通过。
- 临时前端 dev server 通过。
- 临时 Chrome profile。
- UI 创建本地负责人账号。
- UI 粘贴签名 `program` 更新包并预检通过。
- UI 暂存程序包。
- UI 生成程序更新演练计划。
- UI 确认没有程序包应用按钮。
- UI 确认演练计划显示目标版本、维护窗口、已阻断动作。
- 全程无真实外发、无模型调用、无程序执行、无数据库迁移。

证据文件：

```text
output/p3_06u_26h2j_program_update_dry_run_ui/summary.json
output/p3_06u_26h2j_program_update_dry_run_ui/program-dry-run-update-center.png
```

## 下一步

- P3-06U-26H2K：客户授权上传诊断包第一片。
- P3-06U-26H2L：本地恢复工具 dry-run。
- 后续程序更新器正式应用片必须先补：
  - 程序包文件落盘沙箱。
  - 维护窗口确认。
  - 运行进程版本检查。
  - 数据库迁移 dry-run。
  - 停服务/重启服务策略。
  - 更新后健康检查。
  - 程序包回滚。
  - 客户授权和审计闭环。
