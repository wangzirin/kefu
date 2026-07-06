# P3-05S 知识审核发布与回归门禁第一片

日期：2026-07-01

## 工程控制卡

| 项目 | 结论 |
| --- | --- |
| 阶段定位 | 把“知识缺口 -> 文档草稿 -> 回归题”继续推进到“发布前门禁 -> 启用文档 -> 关闭缺口” |
| 当前完成 | 后端发布预检 API、发布 API、草稿检索评测、缺口页发布入口、回归测试和浏览器 QA |
| 不做事项 | 不做真实外发、不做平台渠道发送、不做完整知识版本回滚、不做多人审批流、不外呼模型 |
| 生产边界 | 仍是第一片门禁；正式商用还需要发布历史、审批人、版本 diff、回滚、批量发布和客户题库人工标注 |

## 为什么要做这一片

P3-05R 已经把质量页从普通指标改成错因诊断 BI，但如果诊断出“无知识、低置信、引用缺失”，系统必须能把错因修复成可发布知识。此前 P3-05O 已经能从缺口生成文档草稿、加入回归题库，但还缺少最关键的发布门禁。

本片补齐的链路是：

1. 缺口来源来自人工审核或评测失败。
2. 管理员生成知识文档草稿。
3. 管理员把该缺口加入回归题库。
4. 发布前运行回归门禁。
5. 门禁通过后才把草稿文档改为 active。
6. 同步把关联缺口标记为已解决。

## 后端新增能力

### 发布预检

接口：

`POST /api/knowledge-documents/{document_id}/publish-checks`

作用：

- 校验文档是否存在、是否属于当前租户。
- 校验文档是否已索引、是否有 chunk、是否有引用来源。
- 自动找到关联知识缺口和回归题。
- 运行知识评测，但只把知识质量问题作为发布阻断。
- 返回可发布、不可发布、阻断原因、提示原因和逐题结果。

### 发布执行

接口：

`POST /api/knowledge-documents/{document_id}/publication`

作用：

- 先执行同一套发布门禁。
- 门禁失败时不修改文档状态。
- 门禁通过后把文档和 chunk 改为 active。
- 如果文档来自知识缺口，则把缺口标记为 resolved。
- 写入审计事件 `knowledge_document.published`。

### 重要口径修正

原来的知识评测参数 `status` 同时承担了“题目状态”和“检索文档状态”，这会导致草稿发布前无法评测 draft 文档。本片新增 `search_status`：

| 字段 | 用途 |
| --- | --- |
| `status` | 选择 active/draft/archived 评测题 |
| `search_status` | 选择 active/draft/archived 知识文档进行检索 |

默认行为保持兼容：如果不传 `search_status`，仍沿用 `status`。

## 门禁规则

发布阻断项：

- 文档已归档。
- 文档未完成索引。
- 文档没有 chunk。
- 文档没有来源链接。
- 没有绑定回归题库。
- 没有绑定回归题。
- 目标回归题没有被评测。
- 检索无命中。
- 引用缺失。
- 期望词缺失。
- 期望来源或文档不匹配。
- 必须覆盖的证据没有召回。
- 禁用词命中。
- 置信度低于发布阈值。

只作为提示、不阻断知识发布：

- 高风险问题必须转人工。
- 该题不允许自动回复。

原因是：知识是否可以发布，和该问题是否允许自动回复不是同一件事。强合规题可以拥有正确知识，但仍然必须走人工确认。

## 前端新增能力

缺口页新增“发布知识”动作：

- 只有管理员或 owner 可用。
- 必须先有知识草稿。
- 必须先加入回归题。
- 已发布后显示发布状态，不重复发布。
- 发布成功后刷新知识文档、知识缺口和评测状态。

当前按钮放在“缺口闭环”页，而不是文档列表页。业务语义是修复某个错因后发布该知识，因此从缺口出发更清楚。

## 验证结果

后端：

```bash
/Users/ericlee/Desktop/肥肥lu/lite_a_customer_service/standard_ops/.venv/bin/pytest \
  backend/tests/test_knowledge_gaps_api.py \
  backend/tests/test_knowledge_evaluations_api.py \
  backend/tests/test_knowledge_documents_api.py -q
```

结果：

- 15 passed
- 仅有 FastAPI TestClient 的第三方弃用 warning

前端：

```bash
npm run build
```

结果：

- TypeScript 通过
- Vite build 通过

浏览器 QA：

- 地址：`http://127.0.0.1:5175/#gaps`
- 桌面端：P3-05S 可见，9 条缺口可见，9 个发布动作可见，无横向溢出，console error/warning 为 0
- 移动端：无横向溢出
- 截图：
  - `/Users/ericlee/Desktop/肥肥lu/lite_a_customer_service/standard_ops/output/p3_05s_knowledge_publish_gate/p3_05s_publish_gate_desktop.png`
  - `/Users/ericlee/Desktop/肥肥lu/lite_a_customer_service/standard_ops/output/p3_05s_knowledge_publish_gate/p3_05s_publish_gate_mobile.png`

## 仍未完成

- 知识文档版本 diff。
- 发布历史列表。
- 审核人、复核人、发布时间、回滚版本。
- 批量发布和批量回归。
- 前端展示门禁详情弹窗。
- 从质量 BI 一键跳转到对应缺口和发布记录。
- 真实客户 50-100 条题库的人工事实性标签。
- 生产级知识发布权限策略，例如业务 owner 与客服主管双人确认。

## 下一步建议

优先进入 P3-05T：知识发布记录、门禁详情和回滚第一片。

如果更看重生产稳定性，也可以切到 P3-06A：Redis/队列、生产并发、worker、死信、告警和限流。
