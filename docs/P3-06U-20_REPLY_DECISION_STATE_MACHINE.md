# P3-06U-20 自动回复策略状态机第一片

## 定位

本阶段把“客户消息能不能由 AI 自主回复”从前端演示和旧编排器里拆出来，形成一条可审计、可查询、可复盘的后端决策链。

它不是外发器，也不是替代 `reply_orchestrator`。当前只做四件事：

- 读取一条可信入站消息。
- 命中业务对象和对象问答卡。
- 根据置信度、风险词和渠道外发门禁生成回复决策。
- 写入 `reply_decisions`，保留草稿、原因、命中项和审计事件。

## 新增后端能力

新增数据表：

- `reply_decisions`

核心字段：

- `state`：`auto_reply_ready`、`manual_gate_required`、`knowledge_gap`、`blocked_by_policy`、`draft_only`
- `reason`：决策原因，例如 `object_card_high_confidence`、`no_business_object_match`
- `confidence`：对象问答卡综合置信度
- `delivery_mode`：`draft_only`、`human_review`、`external_write_allowed`、`blocked`
- `business_object_id`
- `object_knowledge_card_id`
- `draft_reply`
- `matched_terms`
- `decision_payload`
- `external_write_allowed`
- `idempotency_key`

新增接口：

- `POST /api/messages/{message_id}/reply-decisions`
- `GET /api/tenants/{tenant_id}/reply-decisions`

权限：

- 创建决策需要 `conversation.manage`
- 查询决策需要 `conversation.read`

审计：

- 每次新增决策都会写入 `reply_decision.created`

## 状态机规则

### 可自动回复

状态：`auto_reply_ready`

触发条件：

- 消息是入站消息。
- 命中 active 业务对象。
- 命中 active 对象问答卡。
- 综合置信度达到 `auto_reply_threshold`，默认 `0.72`。
- 未命中人工门禁词和阻断词。

当前交付边界：

- 即使达到自动回复条件，默认 `delivery_mode=draft_only`。
- 不调用真实模型。
- 不发送到微信、企微、抖音、淘宝、京东或拼多多。
- 真实外发必须等渠道 connector、白名单、回执、限流和 outbox 全链路验收。

### 人工门禁

状态：`manual_gate_required`

触发条件：

- 命中业务对象和对象问答卡，但置信度不足。
- 命中投诉、起诉、律师、赔偿、举报、监管、工商、差评、封号、违约、法务等风险词。

结果：

- 保留问答卡答案作为草稿。
- 不允许真实外发。
- 后续应进入坐席复核或质量复盘。

### 知识缺口

状态：`knowledge_gap`

触发条件：

- 没有命中业务对象。
- 命中业务对象，但没有可信对象问答卡。

结果：

- 不生成客户可见回复。
- 后续应回到知识运营补对象、别名、触发关键词或标准问答。

### 策略阻断

状态：`blocked_by_policy`

触发条件：

- 命中私下转账、线下付款、绕过平台、刷单、虚假交易、保证收益、百分百保证等平台或合规风险词。

结果：

- 不生成草稿。
- 不进入外发队列。
- 只保留阻断原因和命中词。

## 与现有模块关系

### 与业务对象知识库

P3-06U-19 新增的 `business_objects`、`business_object_aliases`、`object_knowledge_cards` 是本阶段的主要输入。

推荐知识维护顺序：

1. 先创建商品、服务、套餐、门店或项目对象。
2. 为对象补别名和平台常见叫法。
3. 为对象挂标准问答卡。
4. 问答卡写清触发关键词、标准答案、禁止承诺和适用范围。
5. 用回复决策接口验证命中结果。

### 与旧回复编排器

`reply_orchestrator` 仍然保留，适合继续做：

- 旧 workflow run。
- 人审 task。
- 知识卡或文档 RAG 草稿生成。
- 模型辅助草稿。

`reply_decisions` 更靠前，适合做：

- 是否能自动答。
- 为什么不能自动答。
- 是否知识缺口。
- 是否有合规阻断。
- 是否允许进入外发前置队列。

后续可把二者连接起来：

- `auto_reply_ready`：进入 outbox 或自动回复队列。
- `manual_gate_required`：创建 workflow run 和 human review task。
- `knowledge_gap`：同步到 knowledge gap。
- `blocked_by_policy`：只进入审计和质检复盘。

### 与 outbox

当前不写 `outbox_drafts`，也不创建 `outbox_delivery_jobs`。

原因：

- 现在仍处于自动回复策略验证阶段。
- 真实外发需要渠道 connector、官方授权、限流、幂等、失败回执和客户白名单。
- 不能因为命中知识卡就直接写入待发送队列。

## 前端变化

知识运营页新增“自动回复状态机”卡片：

- 展示业务对象 → 对象问答卡 → 风险门禁 → 草稿优先。
- 展示四类结果：可自动回复、人工门禁、知识缺口、策略阻断。
- 目的是让知识维护人员理解：不是补一条 FAQ 就能自动外发，而是必须通过对象、问答卡、置信度和风险门禁。

前端 API client 新增：

- `createReplyDecision()`
- `listReplyDecisions()`
- `ReplyDecision`
- `ReplyDecisionList`

当前没有把创建按钮塞进工作台，避免再次把多渠道对话台做复杂。后续应在工作台选中真实入站消息后，展示最新决策或提供“重新评估”按钮。

## 验证

新增后端测试：

- `backend/tests/test_reply_decisions_api.py`

覆盖：

- 高置信对象问答卡命中后进入 `auto_reply_ready` 和 `draft_only`。
- 幂等重复调用返回同一条决策。
- 查询列表可按 state 筛选。
- 未命中业务对象进入 `knowledge_gap`。
- 平台风险词进入 `blocked_by_policy`。
- 法务/赔付类风险词进入 `manual_gate_required`。
- 跨租户消息返回 404。
- 出站消息返回 409。

新增静态检查：

- `scripts/check_p3_06u_20_reply_decision_state_machine.py`

## 当前边界

- 没有真实模型调用。
- 没有真实平台外发。
- 没有自动创建 human review task。
- 没有自动创建 knowledge gap。
- 没有写 outbox。
- 没有接入渠道 connector 的真实发送限流。

## 下一步

建议进入 P3-06U-21：

- 把 `reply_decisions` 接到可信入站 worker。
- `knowledge_gap` 自动同步知识缺口。
- `manual_gate_required` 自动创建人审任务。
- `auto_reply_ready` 在外发关闭时生成可审查草稿，在外发开启且白名单通过后再进入 outbox。
