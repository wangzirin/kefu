# P3-05K 知识缺口闭环

## Engineering Control Card

- Stage: P3-05K 知识缺口闭环。
- Goal: 把“无知识命中、低置信、人审积压、评测失败”从质量信号推进为可分派、可处理、可回归的运营待办。
- User concern: 不能一直做重复评测，也不能只在质量页说有知识缺口；系统必须能把缺口沉淀出来，进入知识库维护流程。
- Scope: 新增 `knowledge_gaps` 后端资源、同步接口、更新接口、前端独立缺口工作区和演示同形数据。
- Non-goal: 不做完整工单系统；不做客户真实 BI 仓库；不把缺口解决自动等同于回答准确；不打开任何真实外部发送。

## 本轮新增了什么

### 后端知识缺口资源

新增 `knowledge_gaps` 表和模型 `KnowledgeGapItem`。

字段覆盖：

- 来源：`source_type`、`source_ref`、`source_title`。
- 问题摘要：`question_excerpt`、`source_excerpt`。
- 缺口类型：`gap_type`、`expected_terms`、`evidence_payload`。
- 处理流：`status`、`severity`、`assigned_user_id`、`resolution_note`、`resolved_at`。
- 关联知识：`linked_knowledge_card_id`、`linked_knowledge_document_id`。
- 审计：`created_by_id`、`updated_by_id`、`resolved_by_id`、`created_at`、`updated_at`。

幂等约束：

```text
tenant_id + source_type + source_ref
```

同一个人审任务或同一个评测失败用例重复同步，不会生成重复缺口。

### 缺口同步来源

当前同步两类来源：

- 人审任务：低置信、无知识命中、知识缺失类 `HumanReviewTask`。
- 评测失败：`KnowledgeEvaluationRunCase` 中的 `no_hit`、`expected_terms_missing`、`expected_evidence_missing`、`citation_missing`、`low_confidence` 等缺口原因。

当前没有直接复制完整原始客户对话到缺口库，只保存摘录、来源 ID 和有限证据摘要。

### API

新增接口：

```text
GET /api/tenants/{tenant_id}/knowledge-gaps
POST /api/tenants/{tenant_id}/knowledge-gaps/sync
PATCH /api/knowledge-gaps/{gap_id}
```

权限边界：

- 列表、同步、更新当前均要求 `owner` 或 `admin`。
- 跨租户访问返回 404。
- 坐席角色暂不直接读完整缺口列表，后续可补脱敏坐席视图。

### 前端缺口工作区

新增左侧导航：

```text
缺口 -> #gaps
```

页面内容：

- 当前缺口总量。
- 待处理数量。
- 高严重度数量。
- 人审来源 / 评测来源构成。
- 最近同步摘要。
- 状态筛选、搜索、每页数量、分页。
- 每条缺口的来源、严重度、客户问题摘录、处理线索、证据摘要、期望词和负责人。
- 处理动作：标记处理中、标记已解决、不需补充、看来源。

演示模式下新增同形缺口数据，真实登录后请求后端 API。

## 本轮文件改动

- `backend/app/models/foundation.py`
  - 新增 `KnowledgeGapItem`。
- `backend/app/models/__init__.py`
  - 导出 `KnowledgeGapItem`。
- `backend/app/migrations/versions/0017_knowledge_gaps.py`
  - 新增 `knowledge_gaps` 迁移。
- `backend/app/schemas/knowledge.py`
  - 新增 `KnowledgeGapRead`、`KnowledgeGapList`、`KnowledgeGapSyncCreate`、`KnowledgeGapSyncRead`、`KnowledgeGapUpdate`。
- `backend/app/services/knowledge.py`
  - 新增缺口同步、列表、更新、严重度估算、来源去重和审计记录。
- `backend/app/api/knowledge.py`
  - 新增缺口列表、同步、更新 API。
- `backend/tests/test_knowledge_gaps_api.py`
  - 新增缺口闭环 API 测试。
- `frontend/src/api/client.ts`
  - 新增缺口类型和 `listKnowledgeGaps`、`syncKnowledgeGaps`、`updateKnowledgeGap`。
- `frontend/src/data/navigation.ts`
  - 新增 `缺口` 导航入口，阶段标识更新为 `P3-05K`。
- `frontend/src/App.tsx`
  - 新增 `KnowledgeGapState`、`KnowledgeGapPanel`、缺口刷新/同步/更新动作、演示缺口数据。
  - 总览和质量页的知识缺口口径优先读取真实缺口资源。
- `frontend/src/styles.css`
  - 新增缺口指标、同步摘要、缺口卡片、来源标签、证据条和移动端响应式样式。

## 验证结果

### 后端测试

已运行：

```bash
backend/.venv/bin/python -m pytest backend/tests/test_knowledge_gaps_api.py -q
```

结果：

- 2 个新增测试通过。
- 覆盖：同步人审来源、同步评测来源、重复同步去重、列表、状态更新、负责人分派、已解决状态、坐席 403、跨租户 404。

已运行：

```bash
backend/.venv/bin/python -m pytest backend/tests/test_knowledge_gaps_api.py backend/tests/test_knowledge_evaluations_api.py -q
```

结果：

- 8 个测试通过。
- 评测相关接口未被本轮改动破坏。

### 前端构建

已运行：

```bash
npm run build
```

结果：

- `tsc` 通过。
- `vite build` 通过。

### 浏览器验证

本地预览地址：

```text
http://127.0.0.1:5174/#gaps
```

验证口径：

- 桌面端能进入 `知识缺口闭环` 页面。
- 演示模式下能显示 9 条缺口。
- 最近同步摘要存在。
- 无横向溢出。
- 390px 移动端无横向溢出。
- 移动端操作区宽度不超过视口。

截图证据目录：

```text
/Users/ericlee/Desktop/肥肥lu/lite_a_customer_service/standard_ops/output/p3_05k_knowledge_gap_loop/
```

截图文件：

```text
knowledge-gaps-desktop.png
knowledge-gaps-mobile.png
```

## 当前仍然不能承诺

- 不能承诺完整工单/SLA 已完成。
- 不能承诺坐席 RBAC、主管质检、团队分派和权限矩阵已完成。
- 不能承诺知识缺口已自动生成新知识文档。
- 不能承诺缺口解决后回答准确率已经提升；必须再跑题库回归和人工事实性标注。
- 不能承诺企业微信、公众号、抖音、小红书、淘宝、京东、拼多多已经真实自动回复。
- 不能承诺真实外发已经打开。

## 下一步建议

优先继续三条线：

1. P3-05M：坐席权限、角色、工单/SLA 和主管视图。
2. P3-05N：联系人画像和线索跟进，把会话、客户身份、意向和转化闭起来。
3. 企业微信公网 smoke：若公网 HTTPS、可信 IP、企微后台权限和测试客服号具备，继续真实回调验证。

本轮结论：知识缺口已经从质量页里的“指标”升级为独立运营资源和工作区，可以支撑后续知识库维护、题库回归和客户月报口径；但它仍不是完整工单系统，也不代表真实全渠道自动回复上线。
