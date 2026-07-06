# P3-05T 知识发布记录、门禁详情与回滚第一片

日期：2026-07-01

## 工程控制卡

| 项目 | 结论 |
| --- | --- |
| 阶段定位 | 把 P3-05S 的发布门禁变成可追溯、可复盘、可撤回的知识运营链路 |
| 当前完成 | 发布检查记录、发布执行记录、门禁逐题详情、文档回滚为草稿、前端发布记录卡片 |
| 不做事项 | 不做真实外发、不恢复旧正文、不做完整版本 diff、不做多人审批、不做批量发布 |
| 生产边界 | 当前是发布审计与检索范围回滚第一片；完整商用知识 CMS 还需要版本表、审批流和差异对比 |

## 为什么要做这一片

P3-05S 已经能阻止草稿绕过回归题直接进入 active 知识库，但如果没有发布记录，运营负责人无法回答三个问题：

1. 这份知识是什么时候被检查、被发布或被回滚的。
2. 发布门禁当时跑了哪些题，哪些题阻断，哪些只是提示。
3. 如果发现知识错误，能不能立刻把它退出正式检索范围。

本片补齐的是知识运营的最小审计闭环。

## 后端新增能力

### 发布记录表

新增表：

`knowledge_document_publications`

记录三类动作：

| 动作 | `publication_type` | 典型状态 |
| --- | --- | --- |
| 发布前检查 | `publish_check` | `passed` / `blocked` |
| 正式发布 | `publish` | `published` / `blocked` |
| 回滚 | `rollback` | `rolled_back` |

记录内容：

- 租户、文档、关联知识缺口。
- 发布动作类型和状态流转。
- 评测集、评测运行、检查题目 ID。
- 逐题门禁结果、阻断项、提示项。
- 文档快照元数据：标题、来源、hash、标签、chunk 数、状态。
- 是否外部写入、是否模型调用。
- 回滚目标发布记录和回滚原因。

安全边界：

- 不存完整 `raw_text`。
- 只存 `raw_text_hash` 和字符数。
- 不触发真实外发。
- 不触发真实模型批量调用。

### 发布检查记录

接口：

`POST /api/knowledge-documents/{document_id}/publish-checks`

新增行为：

- 每次检查都会写入一条 `publish_check` 记录。
- 门禁通过记为 `passed`。
- 门禁阻断记为 `blocked`。
- 记录逐题状态、阻断项和检查指标。

### 正式发布记录

接口：

`POST /api/knowledge-documents/{document_id}/publication`

新增行为：

- 门禁通过并启用文档后，写入 `publish / published` 记录。
- 门禁失败时，写入 `publish / blocked` 记录。
- 记录发布前文档快照，方便后续追溯当时发布的是哪一份知识。

### 发布记录查询

接口：

`GET /api/knowledge-documents/{document_id}/publications`

作用：

- 按文档查看最近发布检查、正式发布和回滚记录。
- 当前支持分页。
- 前端默认只取最近 8 条，避免运营台一次性拉全量历史。

### 回滚为草稿

接口：

`POST /api/knowledge-documents/{document_id}/rollback`

当前第一片回滚能力：

- 找到指定发布记录，或默认找到最近一次 `published` 记录。
- 把文档状态改为 `draft`。
- 把该文档的所有 chunk 状态改为 `draft`。
- 如果关联知识缺口已经 resolved，则退回 `in_progress`。
- 写入 `rollback / rolled_back` 发布记录。
- 写入审计事件。

明确没有完成：

- 不恢复旧正文。
- 不比较两个版本的正文差异。
- 不恢复旧 chunk 切分结果。
- 不做双人审批或负责人签名。

原因：

当前系统还没有知识文档版本表。强行宣称“完整回滚”会不真实。现在实现的是最重要的安全动作：发现错误后立刻让该知识退出 active 检索范围。

## 前端新增能力

位置：

`知识库 -> 文档`

每个文档新增发布记录卡片：

- 最新发布动作。
- 发布状态。
- 状态流转。
- 关联评测运行。
- 阻断项摘要。
- 最近 3 条逐题门禁结果。
- 回滚为草稿按钮。

按钮禁用规则：

- 未登录不可点。
- 非知识管理员不可点。
- 页面加载中不可点。
- 没有成功发布记录不可点。
- 文档不是 active 不可点。

界面提示：

> 回滚只暂停 active 检索，不恢复旧正文；完整版本 diff 属于下一阶段。

## 验收结果

后端：

```bash
.venv/bin/pytest backend/tests/test_knowledge_gaps_api.py backend/tests/test_knowledge_evaluations_api.py backend/tests/test_knowledge_documents_api.py -q
```

结果：

- 15 个测试通过。
- 覆盖发布检查记录、正式发布记录、阻断记录、发布后回滚、文档状态回 draft、chunk 状态回 draft、缺口退回处理中。

迁移：

```bash
cd backend && .venv/bin/alembic heads
```

结果：

- `0020_knowledge_document_publications (head)`

前端：

```bash
cd frontend && npm run build
```

结果：

- TypeScript 和 Vite 构建通过。

浏览器 QA：

- URL：`http://127.0.0.1:5175/#knowledge`
- 桌面视口：1440 x 1050。
- 移动视口：390 x 1000。
- 发布记录卡片：6 张可见。
- 回滚按钮：6 个可见。
- 横向溢出：无。
- console error/warning：0。
- 截图：
  - `output/p3-05t-knowledge-publications-desktop.png`
  - `output/p3-05t-knowledge-publications-mobile.png`

## 仍未完成

- 完整文档版本表。
- 正文 diff 和 chunk diff。
- 回滚到指定历史正文。
- 知识审批流、复核人、业务负责人确认。
- 批量发布、批量回归、批量回滚。
- 从质量 BI 一键跳转到具体发布记录。
- 发布记录的主管筛选、导出和审计报表。

## 下一步建议

进入 P3-06A：生产并发底座第一片。

优先目标：

1. 让可信入站 worker 和 outbox worker 具备生产级并发控制。
2. 增加任务租约、抢占、重试、死信和幂等执行证据。
3. 为托管云和私有化部署补齐“多进程不会重复处理同一条消息”的底座。
