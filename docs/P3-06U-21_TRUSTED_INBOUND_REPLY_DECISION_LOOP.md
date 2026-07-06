# P3-06U-21 可信入站与回复决策闭环第一片

## 定位

本阶段把 P3-06U-20 的 `reply_decisions` 接入可信入站 worker，让一条已经通过官方 webhook 验签或自有入口签名的入站消息，不再直接进入旧的“模型草稿 + 人审”路径，而是先进入自动回复策略状态机。

本片只完成内部闭环：

- 可信入站消息进入 worker。
- worker 先创建 `reply_decision`。
- 按决策状态进入知识缺口、人审任务或 outbox 前置门禁。
- 全程保持 `external_write=false`。

它不打开真实外发，不调用真实模型，不代表微信、企微、抖音、淘宝、京东、拼多多已经自动回复成功。

## 新流程

```text
可信入站消息
  -> trusted_inbound_worker
  -> reply_decisions
  -> 状态分流
       auto_reply_ready       -> outbox_pre_gate，真实外发关闭
       manual_gate_required   -> human_review_task
       knowledge_gap          -> knowledge_gap
       blocked_by_policy      -> policy_gate，仅审计和复盘
```

## 状态分流

### auto_reply_ready

命中高置信业务对象问答卡时进入该状态。

当前处理：

- 创建 workflow run。
- workflow 的 `state_payload.outbox_pre_gate.eligible=true`。
- 记录 `external_write=false`。
- 不创建 `outbox_drafts`。
- 不创建 `outbox_delivery_jobs`。

原因：真实外发仍需要官方渠道授权、白名单、限流、幂等、回执和失败复盘全部验收。

### manual_gate_required

命中投诉、起诉、赔偿、法务等风险词，或对象问答卡置信度不足时进入该状态。

当前处理：

- 创建 workflow run。
- 创建 `human_review_task`。
- 人审证据里保留 `reply_decision_id`、置信度、对象问答卡来源和草稿。
- 坐席后续仍需人工批准，批准后才可能进入 outbox 草稿。

### knowledge_gap

没有命中业务对象，或命中对象但没有可信对象问答卡时进入该状态。

当前处理：

- 创建 workflow run。
- 创建或复用 `knowledge_gaps`，`source_type=reply_decision`。
- source ref 使用 `reply_decision:{id}`，保证幂等。
- evidence payload 保留消息、会话、渠道、业务对象、问答卡、命中词和决策详情。

### blocked_by_policy

命中私下转账、线下付款、绕过平台、刷单、虚假交易、保证收益等风险词时进入该状态。

当前处理：

- 创建 workflow run。
- workflow 进入 `policy_gate`。
- 不创建草稿、不进入 outbox、不进入真实发送。

## 本轮代码变化

- `backend/app/workers/trusted_inbound_orchestrator.py`
  - worker 改为先创建 `reply_decision`。
  - 新增 `auto_reply_ready`、`manual_gate_required`、`knowledge_gap`、`blocked_by_policy` 分流。
  - 新增 outbox 前置门禁，但不写出站草稿和发送任务。

- `backend/app/services/knowledge.py`
  - 新增 `create_knowledge_gap_from_reply_decision()`。
  - 支持由回复决策幂等生成知识缺口。

- `backend/app/schemas/inbound_worker.py`
  - worker item 追加 `reply_decision_id`、`knowledge_gap_id`、`outbox_draft_id`。

- `backend/app/schemas/knowledge.py` 与 `backend/app/api/knowledge.py`
  - 知识缺口来源允许 `reply_decision`。

- `backend/tests/test_trusted_inbound_worker_api.py`
  - 覆盖知识缺口同步、人审门禁、自动回复 outbox 前置门禁、租约、限流、失败重放。

## 验证重点

本片必须证明：

- 已验签的可信入站消息会产生 `reply_decision_id`。
- 未命中业务对象时，自动生成 `source_type=reply_decision` 的知识缺口。
- 命中风险词时，自动创建人审任务。
- 高置信对象问答卡只进入 outbox 前置门禁，不写 outbox 草稿。
- worker 租约、限流、失败重放仍然保留。

## 当前边界

- 没有真实平台外发。
- 没有真实模型调用。
- 没有自动创建 outbox draft。
- 没有 delivery job。
- 没有真实渠道回执 reconciliation。
- 没有把 RPA 研究能力写成正式渠道能力。

## 下一步

建议进入 P3-06U-22：

- 把工作台选中会话的最新 `reply_decision` 展示出来。
- 对 `knowledge_gap`、`manual_gate_required`、`auto_reply_ready` 给出更清楚的坐席动作提示。
- 为 `auto_reply_ready` 增加“外发关闭，所以停在预发送门禁”的可见状态。
- 继续保持真实外发关闭，除非后续有官方渠道、白名单和明确授权。
