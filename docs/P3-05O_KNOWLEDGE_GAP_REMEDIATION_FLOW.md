# P3-05O 知识缺口到文档草稿与回归题库闭环

日期：2026-06-30

## 阶段目标

把 P3-05K 已经沉淀出来的 `knowledge_gaps` 从“可分派待办”推进到“可补知识、可回归验证”的第一片闭环。

本阶段解决的问题：

- 知识缺口不再只停留在列表里。
- 管理员可以从缺口生成待审核知识文档草稿。
- 管理员可以把缺口加入固定回归题库。
- 缺口进入处理中状态，并记录草稿文档和回归题 ID。
- 前端中台可以直接看到某个缺口是否已生成草稿、是否已进入回归。

## 已完成能力

### 后端

- 新增 `POST /api/knowledge-gaps/{gap_id}/document-drafts`。
  - 输入：知识缺口 ID。
  - 输出：更新后的缺口、知识文档草稿、是否新建、草稿正文。
  - 行为：创建 `knowledge_documents` 草稿，`source_type=knowledge_gap_remediation`，`source_uri=knowledge-gap:{id}`。
  - 安全边界：文档状态为 `draft`，不会进入默认 active 检索，不会自动用于客户回复。
  - 幂等边界：缺口已关联文档时复用原文档，不重复创建。

- 新增 `POST /api/knowledge-gaps/{gap_id}/regression-cases`。
  - 输入：知识缺口 ID。
  - 输出：更新后的缺口、回归题库、回归题、是否新建。
  - 行为：创建或复用名为 `知识缺口回归题库` 的 active 评测集，并创建 `knowledge_gap_regression` 题目。
  - 数据来源：问题摘录、期望词、期望来源、来源渠道、来源分类来自缺口证据摘要。
  - 幂等边界：按 `knowledge-gap-{gap_id}` 复用已有题目，不重复创建。

- 缺口状态流：
  - 生成草稿或回归题后，缺口变为 `in_progress`。
  - 默认分派给当前操作人。
  - 不自动置为 `resolved`。
  - `evidence_payload.remediation` 写入草稿文档 ID、回归题库 ID、回归题 ID。

- 权限边界：
  - 只有 `owner/admin` 可以执行补知识闭环动作。
  - 坐席调用返回 403。
  - 跨租户调用返回 404。
  - 本阶段不执行真实外部平台写入。

### 前端

- `缺口` 工作区新增每条缺口的处理状态标签：
  - 草稿文档编号或“未生成草稿”。
  - 回归题编号或“未入回归”。

- 每条缺口新增操作：
  - `生成草稿` / `已有草稿`。
  - `加入回归` / `已入题库`。

- 操作成功后：
  - 刷新缺口列表。
  - 生成草稿后刷新知识文档列表。
  - 加入回归后刷新评测集列表。

- 演示模式仍只读，正式动作必须登录并携带 token。

## 已修改文件

后端：

- `backend/app/schemas/knowledge.py`
  - 新增 `KnowledgeGapDocumentDraftRead`。
  - 新增 `KnowledgeGapRegressionCaseRead`。

- `backend/app/services/knowledge.py`
  - 新增缺口草稿生成模板。
  - 新增草稿文档生成/复用逻辑。
  - 新增回归题库创建/复用逻辑。
  - 新增缺口 remediation 证据写回。
  - 新增审计事件。

- `backend/app/api/knowledge.py`
  - 新增 `document-drafts` 子资源接口。
  - 新增 `regression-cases` 子资源接口。

- `backend/tests/test_knowledge_gaps_api.py`
  - 新增 P3-05O 行为测试。
  - 覆盖草稿创建、草稿复用、回归题创建、回归题复用、坐席 403、跨租户 404。

前端：

- `frontend/src/api/client.ts`
  - 新增缺口草稿和回归题结果类型。
  - 新增 `createKnowledgeGapDocumentDraft`。
  - 新增 `createKnowledgeGapRegressionCase`。
  - 补齐 `KnowledgeEvaluationCase` 前端类型字段。

- `frontend/src/App.tsx`
  - 新增缺口草稿/回归动作处理。
  - 缺口卡片新增草稿和回归状态标签。
  - 缺口卡片新增“生成草稿”和“加入回归”按钮。
  - 补齐演示评测题字段。

- `frontend/src/data/navigation.ts`
  - 阶段标识更新到 `P3-05O`。

本机 QA 证据：

- `docs/p3_05o_gaps_preview.png`

## 验证记录

- 红灯测试：
  - `backend/.venv/bin/python -m pytest backend/tests/test_knowledge_gaps_api.py -q`
  - 初始失败点为 404，证明新接口此前不存在。

- 后端相关回归：
  - `backend/.venv/bin/python -m pytest backend/tests/test_knowledge_gaps_api.py backend/tests/test_knowledge_documents_api.py backend/tests/test_knowledge_evaluations_api.py -q`
  - 13 个测试通过。

- 前端构建：
  - `cd frontend && npm run build`
  - `tsc && vite build` 通过。

- 迁移头：
  - `cd backend && .venv/bin/alembic heads`
  - 返回 `0019_sales_leads (head)`。
  - 本轮未新增数据库迁移。

- 页面级检查：
  - headless Chrome 打开 `http://127.0.0.1:5175/#gaps`。
  - 点击开发演示入口。
  - 文本断言通过：
    - `知识缺口闭环`
    - `生成草稿` 或 `已有草稿`
    - `加入回归` 或 `已入题库`
    - `未生成草稿` 或 `草稿文档 #`
    - `未入回归` 或 `回归题 #`

## 当前不能承诺

- 不能说知识缺口已经自动解决。
- 不能说 AI 准确率已经提升。
- 不能说草稿文档已经发布到正式知识库。
- 不能说回归题通过。
- 不能说真实企业微信、公众号、抖音、小红书、淘宝、京东、拼多多已经自动回复上线。
- 不能说已经具备完整知识审核、版本回滚、多人审批和生产级质量运营。

## 下一步建议

优先级一：P3-05P 高级工单/SLA 第一片。

- 工单评论。
- 工单附件元数据。
- 单独重开动作。
- SLA 暂停、恢复、升级提示。

优先级二：知识审核发布流。

- 文档草稿详情。
- 草稿审核。
- 发布为 active。
- 发布前强制跑回归题。
- 发布后记录版本和回滚点。

优先级三：官方渠道公网 smoke。

- 公网 HTTPS 回调 URL。
- 企业微信 URL 验证。
- AES 解密。
- 入站消息入库。
- AI 草稿生成。
- 人审后白名单外发。

