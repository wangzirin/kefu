# 阶段 2：轻量 Workflow 与人工审核底座

日期：2026-06-25

最近更新：2026-06-27，P2-26 第一片已新增 `scripts/run_p2_26_retrieval_quality_comparison.py`，复用 P2-25 的动态 chunk 回填题库，对 `top_k=5/8/10/12` 做本地检索参数对比。当前结果为：top-k=5 时 `full_evidence_recall_at_k=57.9%`、`citation_precision=39.8%`；top-k=8 时 `full_evidence_recall_at_k=67.1%`、`citation_precision=32.2%`；top-k=10 时 `full_evidence_recall_at_k=72.4%`、`citation_precision=29.9%`；top-k=12 时 `full_evidence_recall_at_k=76.3%`、`citation_precision=27.8%`。基线完整证据未召回题 32 道，扩大 top-k 后救回 14 道，仍有 18 道到 top-k=12 都未完整召回。当前推荐生产默认先用 `top_k=8`，`top_k=12` 只作为召回池或重排实验候选；本轮不调用外部模型，不写外部平台，不使用真实客户资料，也不代表生成答案事实性、真实幻觉率或真实客户 50-100 题验收已经完成。

## 阶段定位

本阶段是标准运营版从“基础租户/账号/会话 API”走向“可运营客服中台”的第一片工程底座。

本阶段不引入完整 LangGraph runtime，不接真实渠道，不做授权网页采集，不向外部平台发送消息。当前目标是先让客服消息处理具备：

- 可创建流程实例。
- 可记录步骤尝试。
- 可保存检查点。
- 可把低置信/高风险/无知识命中的回复转为人工审核任务。
- 可从结构化知识卡片检索生成回复草稿。
- 可通过模型网关生成回复草稿，并记录 provider、model、prompt 摘要和用量估算。
- 可由坐席查看审核证据后批准、改写或拒绝。
- 可把已批准最终回复生成内部 outbox 草稿，并在发送前确认或取消。
- 可对 `ready_to_send` 草稿记录 dry-run 发送尝试，验证载荷和审计链，但不触达外部平台。
- 可在前端看到人工审核收件箱、待发送草稿、确认待发送和模拟发送结果。
- 可运行 outbox worker dry-run，批量扫描 `ready_to_send` 草稿，记录成功、失败、限流、回执占位和重试占位。
- 可为渠道配置官方连接器占位，生成内部发送计划，并记录未验签的回执占位。
- 可列出企业微信客服、微信公众号和官网客服组件的 provider 契约，并接收官方渠道 webhook 占位回调。
- 可使用开发 fixture 对企业微信、微信公众号和官网客服组件做服务端签名验证，并在消息内容、联系人身份和幂等键齐备时创建可信入站消息。
- 可对重复 provider event id 或 external message id 的回调做幂等拦截，避免重复写入客服消息。
- 可由受保护的入站 worker 扫描可信入站消息，调用 ReplyOrchestrator，生成 workflow run 和人工审核任务。
- 可把 ready outbox 草稿转换为发送队列 job，并由受保护队列 runner 记录锁、限流、重试、死信和 kill switch 阻断。
- 可把知识库问题沉淀为评测集，并在前端查看检索命中、引用覆盖、期望词覆盖和需复盘题目。
- 可留下审计事件。
- 可按租户隔离访问。

## 为什么先做这一层

后续 RAG 入库、模型路由、渠道回调、失败重试、人工接管、outbox 外发，都需要一个共同的流程记录层。否则即使能接页面采集或大模型，也无法稳定回答这些问题：

- 这条回复是从哪个入站消息触发的？
- 哪一步失败了？
- 为什么进入人工？
- 谁审核了？
- 审核前后的回复内容是什么？
- 是否可以重试且不重复写消息？

## 已新增数据表

| 表 | 作用 |
| --- | --- |
| `workflow_runs` | 一次客服处理流程，例如一条入站消息触发的回复流程 |
| `workflow_checkpoints` | 某一步的状态快照和输入/输出摘要 |
| `workflow_step_attempts` | 某一步的第几次尝试、成功/失败和错误信息 |
| `human_review_tasks` | 低置信、高风险或需人工确认的回复审核任务 |
| `knowledge_cards` | 结构化知识卡片，作为 RAG v1 前的可测试知识底座 |
| `outbox_drafts` | 已批准最终回复的内部待发送草稿 |
| `outbox_send_attempts` | outbox 草稿的发送尝试记录，当前只支持 dry-run |
| `channel_connectors` | 渠道官方连接器配置占位，当前强制外部写入关闭 |
| `channel_delivery_receipts` | 平台回执和 webhook 入口记录；未配置密钥时保持不可信，fixture 验签通过时可记录可信入站消息创建结果 |
| `delivery_failure_reviews` | 平台失败、限流、授权异常、未知状态等回执归一化后的复盘队列 |
| `outbox_delivery_jobs` | 发送队列 job；记录幂等键、锁、优先级、重试次数、外部写请求、最近尝试和死信原因 |

## 已新增 API

| 接口 | 作用 |
| --- | --- |
| `POST /api/conversations/{conversation_id}/workflow-runs` | 为会话创建工作流 |
| `GET /api/tenants/{tenant_id}/workflow-runs` | 按租户查看工作流 |
| `GET /api/workflow-runs/{workflow_run_id}` | 查看工作流详情、检查点、步骤尝试和审核任务 |
| `POST /api/workflow-runs/{workflow_run_id}/step-attempts` | 记录一步处理尝试 |
| `POST /api/workflow-runs/{workflow_run_id}/checkpoints` | 记录流程检查点 |
| `POST /api/workflow-runs/{workflow_run_id}/human-review-tasks` | 创建人工审核任务 |
| `GET /api/tenants/{tenant_id}/human-review-tasks` | 按租户查看人工审核任务 |
| `GET /api/tenants/{tenant_id}/human-review-inbox` | 坐席审核收件箱，返回任务、会话、原始消息、workflow 和证据包 |
| `PATCH /api/human-review-tasks/{task_id}` | 审核通过或拒绝任务 |
| `POST /api/human-review-tasks/{task_id}/outbox-drafts` | 从已批准人工审核创建待确认 outbox 草稿 |
| `GET /api/tenants/{tenant_id}/outbox-drafts` | 按租户查看 outbox 草稿 |
| `POST /api/outbox-drafts/{draft_id}/confirmation` | 确认草稿进入待发送状态 |
| `POST /api/outbox-drafts/{draft_id}/cancellation` | 取消待确认草稿 |
| `POST /api/outbox-drafts/{draft_id}/send-attempts` | 对 ready 草稿创建 dry-run 发送尝试 |
| `GET /api/outbox-drafts/{draft_id}/send-attempts` | 查看草稿发送尝试记录 |
| `POST /api/tenants/{tenant_id}/outbox-worker-runs` | 运行 outbox worker dry-run，批量处理 ready 草稿并记录发送检查结果 |
| `POST /api/tenants/{tenant_id}/trusted-inbound-worker-runs` | 运行可信入站编排 worker，把可信入站消息送入 ReplyOrchestrator 和人工审核收件箱 |
| `POST /api/channels/{channel_id}/connector-config` | 创建或更新渠道官方连接器占位配置 |
| `GET /api/channels/{channel_id}/connector-config` | 查看渠道官方连接器占位配置 |
| `POST /api/outbox-drafts/{draft_id}/connector-send-plans` | 为 ready 草稿生成官方渠道发送计划，当前只创建 blocked 记录 |
| `GET /api/channel-providers` | 查看官方渠道 provider registry，占位返回企业微信客服、微信公众号、官网客服组件 |
| `POST /api/webhooks/{provider}/channels/{channel_id}` | 接收官方平台 webhook 回调；当前支持 fixture 验签、可信入站消息创建和重复回调拦截 |
| `POST /api/channels/{channel_id}/delivery-receipts` | 记录平台回执占位，当前不声明已完成验签 |
| `GET /api/channels/{channel_id}/delivery-receipts` | 查看渠道回执占位记录 |
| `GET /api/tenants/{tenant_id}/delivery-failure-reviews` | 查看开放的失败复盘队列 |
| `PATCH /api/delivery-failure-reviews/{review_id}` | 将失败复盘项标记为已处理或忽略 |
| `POST /api/outbox-drafts/{draft_id}/delivery-jobs` | 为 ready 草稿创建发送队列 job，重复创建由幂等键挡住 |
| `GET /api/tenants/{tenant_id}/outbox-delivery-jobs` | 查看租户发送队列 job |
| `POST /api/tenants/{tenant_id}/outbox-delivery-queue-runs` | 运行发送队列骨架，记录锁、限流、重试、死信和 kill switch 结果 |
| `POST /api/tenants/{tenant_id}/knowledge-cards` | 创建结构化知识卡片 |
| `GET /api/tenants/{tenant_id}/knowledge-cards` | 按租户列出知识卡片 |
| `PATCH /api/knowledge-cards/{card_id}` | 更新知识卡片 |
| `POST /api/tenants/{tenant_id}/knowledge-searches` | 对 active 知识执行轻量检索 |

## P2-2 ReplyOrchestrator 最小骨架

已新增 `POST /api/messages/{message_id}/reply-orchestrations`。

这一接口把一条入站消息转为统一的回复处理流程：

```text
入站消息
  -> 创建 workflow run
  -> classify_intent
  -> retrieve_knowledge
  -> draft_reply
  -> risk_check
  -> 高置信低风险：completed / record_result
  -> 低置信、无知识命中、中高风险：human_review_tasks
```

当前输入中的 `intent`、`retrieved_knowledge_count`、`draft_reply`、`confidence`、`risk_level` 仍由调用方显式传入，用于验证编排链路。后续接真实系统时，应分别替换为：

| 当前占位字段 | 后续真实来源 |
| --- | --- |
| `intent` | 轻量分类器、规则分类或模型网关分类结果 |
| `retrieved_knowledge_count` | BM25/向量混合检索命中的知识片段数量 |
| `draft_reply` | RAG 生成、FAQ 模板或坐席辅助草稿 |
| `confidence` | 检索分数、重排分数、规则置信度和模型自评的综合分 |
| `risk_level` | 合规规则、敏感词、退款/承诺/医疗金融等风险分类 |

当前自动完成阈值为 `0.75`：

- `confidence >= 0.75`、`risk_level = low`、且知识命中数大于 0：流程完成，记录为可自动回复草稿。
- `confidence < 0.75`：进入人工审核，原因 `low_confidence`。
- 知识命中数为 0：进入人工审核，原因 `no_knowledge_hit`。
- `risk_level` 为 `medium/high/critical`：进入人工审核，原因 `risk_level_*`。

这个阶段仍不向任何外部平台发送消息，也不创建真实出站消息。它只完成“客服回复决策链路可被记录、复盘和接管”的后端骨架。

## P2-3 知识库检索接口 v1

已新增结构化知识卡片表 `knowledge_cards` 和轻量检索接口 `POST /api/tenants/{tenant_id}/knowledge-searches`。

当前知识卡片字段：

| 字段 | 作用 |
| --- | --- |
| `title` | 知识标题，用于检索加权 |
| `question` | 标准问题或适用场景 |
| `answer` | 标准答案或坐席参考答案 |
| `source_type` | 来源类型，例如 `manual`、`document`、`url` |
| `source_uri` | 来源位置，当前只做记录，不做自动采集 |
| `tags` | 主题标签 |
| `aliases` | 别名、同义词、常见问法 |
| `status` | `draft`、`active`、`archived` |

当前检索模式为 `lexical_bm25_v1`：

- 不新增外部依赖。
- 按租户读取 `active` 知识卡片。
- 对标题、问题、答案、标签、别名做中文 n-gram 与英文 token 化。
- 使用轻量 BM25 风格打分，并返回 `score`、`confidence` 和 `matched_terms`。
- 对多词查询要求至少命中两个有意义词，降低弱相关误召回。

当前权限边界：

- 创建和更新知识卡片需要 `owner` 或 `admin`。
- 检索和列表需要同租户有效 Bearer token。
- 跨租户访问返回 404。
- 知识创建和更新写入 `knowledge_card.created` / `knowledge_card.updated` 审计事件。

当前仍不是完整 RAG：

- P2-18 已补文档导入、文档分块和 chunk 级引用溯源。
- P2-18E 已把向量侧从 token signature stub 升级为 deterministic 本地 embedding + portable JSON vector，并预留 OpenAI-compatible embedding provider 边界。
- P2-18G 已增加 PostgreSQL/pgvector exact cosine 查询路径和向量索引重建入口；Docker Postgres 使用 `pgvector/pgvector:pg16`。
- P2-18F 已增加 embedding provider smoke API 和 provider 成本/延迟估算账本；外部 provider smoke 必须显式传 `allow_external_call=true`，且响应不回显 sample 原文。
- P2-18H 已增加 pgvector HNSW/IVFFlat dry-run 策略计划；当前只生成计划、DDL、rollback、query options 和安全检查，不执行真实 `CREATE INDEX`，也不把检索查询切换到 ANN。
- P2-18E 已有轻量 `lexical_overlap_reranker_v1`，但不是神经重排模型。
- 仍没有文档解析器、批量文件上传和评测集。
- ReplyOrchestrator 已经可以通过 `knowledge_search` 模式自动调用这个检索能力。

## P2-4 ReplyOrchestrator 接入知识检索 v1

已在 `POST /api/messages/{message_id}/reply-orchestrations` 新增 `knowledge_search` 模式。

请求示例：

```json
{
  "mode": "knowledge_search",
  "intent": "after_sales_policy",
  "knowledge_top_k": 3
}
```

处理链路：

```text
入站消息
  -> 创建 workflow run
  -> classify_intent
  -> 调用结构化知识卡片检索
  -> 将 knowledge_matches 写入 workflow state
  -> 最高命中知识卡片 answer 作为 draft_reply
  -> risk_check
  -> 高置信低风险且有知识命中：completed
  -> 无知识命中、低置信、中高风险：human_review_tasks
```

新增响应字段：

| 字段 | 作用 |
| --- | --- |
| `knowledge_matches` | 本次检索命中的知识卡片摘要，包含 `card_id`、标题、分数、置信度、命中词和来源 |
| `draft_reply` | 命中知识卡片的标准答案；无命中时为人工确认提示 |

新增 workflow state 字段：

| 字段 | 作用 |
| --- | --- |
| `retrieval_mode` | 当前为 `manual` 或 `knowledge_search` |
| `retrieval_engine` | 当前为 `manual` 或 `lexical_bm25_v1` |
| `knowledge_matches` | 写入流程快照，便于后续复盘命中了哪些知识 |

当前判断规则：

- 有知识命中、综合置信度不低于 `0.75`、风险等级为 `low`：流程完成，记录为可自动回复草稿。
- 无知识命中：进入人工审核，原因 `no_knowledge_hit`。这个原因优先于低置信，方便运营侧补知识库。
- 低置信：进入人工审核，原因 `low_confidence`。
- 中高风险：进入人工审核，原因 `risk_level_*`。

P2-4 仍然只是“结构化知识卡片生成草稿”，不是完整智能客服：

- 没有默认调用真实大模型。
- 没有生成引用片段。
- 没有向量检索或重排。
- 没有自动发消息到外部平台。
- 没有把草稿写成出站消息。
- 没有坐席工作台前端处理这条人工审核任务。

## P2-5 模型网关草稿生成 v1

已在 `POST /api/messages/{message_id}/reply-orchestrations` 新增 `model_assisted` 模式。

请求示例：

```json
{
  "mode": "model_assisted",
  "intent": "after_sales_policy",
  "knowledge_top_k": 3,
  "model_provider": "deterministic"
}
```

处理链路：

```text
入站消息
  -> 创建 workflow run
  -> classify_intent
  -> 调用结构化知识卡片检索
  -> 将 knowledge_matches 写入 workflow state
  -> 调用模型网关生成 draft_reply
  -> 将 model_call 写入 workflow state
  -> risk_check
  -> 高置信低风险且模型可用：completed
  -> 无知识命中、模型不可用、低置信、中高风险：human_review_tasks
```

新增请求字段：

| 字段 | 作用 |
| --- | --- |
| `model_provider` | `deterministic`、`auto`、`bailian` 或 `deepseek` |
| `model_name` | 可选模型名；为空时使用 provider 默认模型 |
| `model_temperature` | 草稿生成温度，当前限制 `0-1` |

新增响应字段：

| 字段 | 作用 |
| --- | --- |
| `model_call` | 模型调用摘要，包含 provider、model、status、prompt 摘要、输入/输出用量估算、错误信息、route_name、complexity、target_model_tier、fallback_chain、human_review_required 和 route_reasons |

当前 provider 边界：

- `deterministic`：本地可重复草稿生成，用于测试、无 Key 演示和流程验证，不调用外部网络。
- `auto`：优先使用已配置 Key 的百炼，其次 DeepSeek；都没有 Key 时回到 deterministic。
- `bailian`：读取 `BAILIAN_API_BASE`、`BAILIAN_API_KEY`、`BAILIAN_MODEL`，走 OpenAI-compatible `chat/completions`。
- `deepseek`：读取 `DEEPSEEK_API_BASE`、`DEEPSEEK_API_KEY`、`DEEPSEEK_MODEL`，走 OpenAI-compatible `chat/completions`。
- 显式选择外部 provider 但未配置 Key 时，不会静默 fallback，而是进入人工审核，原因 `model_unavailable`。

P2-19 模型路由：

| 路由 | 适用 | 默认目标 |
| --- | --- | --- |
| `simple_fast` | 问候、导航、简单 FAQ | 百炼 `qwen3.6-flash` |
| `standard_support` | 普通售前、售后、政策解释 | 百炼 `qwen3.7-plus` |
| `premium_guarded` | 投诉、赔付、法律、合同、复杂政策 | 百炼 `qwen3.7-max`，并保留人工审核门 |
| `deterministic_safe_fallback` | 未配置外部模型 Key 或本地测试 | 本地 deterministic，不外呼、不消耗费用 |

路由输入包括 `intent`、`risk_level`、编排后的回复置信度、知识命中数和客户问题文本。P2-19 只解决“该走哪个模型档位、为什么、是否必须人审、fallback 链是什么”；不证明真实模型质量、回答准确率或幻觉率。

P2-20 真实百炼聊天模型 smoke：

```bash
python3 scripts/smoke_bailian_chat_model.py
python3 scripts/smoke_bailian_chat_model.py --allow-external-call
python3 scripts/smoke_bailian_chat_model.py --allow-external-call --require-success
```

- 默认不外呼，返回 `blocked_external_call_not_allowed`。
- 传 `--allow-external-call` 但没有 `BAILIAN_API_KEY` 时，返回 `blocked_missing_api_key`，不会调用 provider。
- 只有显式允许且配置了 `BAILIAN_API_KEY`，才调用百炼 `chat/completions`。
- smoke 只使用公开、非敏感样本文本；输出保留 input hash、字符数、估算 tokens、路由、人审门禁、latency 和 usage 摘要。
- smoke 结果不会保存 API key、不会把 sample 原文写入结果，也不会写入数据库。
- P2-20 只证明鉴权、网络、路由和 usage 摘要可观测；不证明真实客户题库回答质量、幻觉率、并发稳定性或最终成本。
- 2026-06-26 真实 smoke 已成功一次：`provider=bailian`、`model=qwen-plus`、`route_name=standard_support`、`status=succeeded`、`latency_ms≈1733`、usage 摘要 `prompt=182 / completion=42 / total=224`。本记录不包含 API key 或 sample 原文。

P2-21 真实百炼聊天模型质量评测入口：

```bash
python3 scripts/evaluate_bailian_chat_quality.py --limit 5
python3 scripts/evaluate_bailian_chat_quality.py --allow-external-call --limit 5
python3 scripts/evaluate_bailian_chat_quality.py --allow-external-call --limit 5 --require-success
```

- 默认不外呼，返回 `blocked_external_call_not_allowed`。
- 传 `--allow-external-call` 但没有 `BAILIAN_API_KEY` 时，返回 `blocked_missing_api_key`，不会调用 provider。
- 只有显式允许且配置了 `BAILIAN_API_KEY`，才按 `--limit` 调用百炼；默认最多跑 5 条，避免误批量消耗付费 API。
- 当前题集是 `built_in_public_synthetic_cases_v1` 脱敏合成题集，覆盖人工审核边界、发货退换货、价格承诺、渠道边界、订单状态、退款投诉、复杂集成、知识缺口、合同法务和隐私边界。
- 评测输出只记录 case id、分类、input hash、路由、usage、latency、期望词缺失数、禁用词命中数和人审门禁；不会把问题原文写入结果，不会保存 API key、知识原文或完整 provider 响应。
- 2026-06-26 真实小样本评测已成功一次：`attempted_calls=5`、`succeeded=5`、`average_latency_ms≈2596`、`total_tokens_or_chars=1037`、`human_review_required_cases=3`、`forbidden_term_hits=0`、`missing_expected_terms=3`。本记录不包含 API key、问题原文或完整 provider 响应。
- P2-21 只证明“模型质量评测入口、脱敏样本、安全外呼门禁和指标摘要”可运行；不证明真实模型质量验收、真实客户 50-100 题、人工标注、引用事实性、幻觉率、并发稳定性或最终成本已经完成。

P2-22 客服知识检索评测集升级：

- 新增 `customer_service_retrieval` 评测模式，保留原 `document_retrieval` 兼容路径。
- `knowledge_evaluation_cases` 新增 `question_type`、`expected_chunk_ids`、`must_have_all_evidence`、`expected_human_review`、`allow_auto_reply`、`forbidden_terms`、`risk_level`，用于把题库从“问题 + 期望词”升级为“客服商用验收题”。
- 运行评测时，期望词覆盖会基于 top-k 证据集合计算，避免多证据题只看 top1 造成误判。
- 运行报告新增 `full_evidence_recall_at_5`、`citation_precision`、`human_review_correctness`、`knowledge_gap_rate` 和 `forbidden_term_hits`，逐题 `result_payload` 记录返回 chunk、全证据是否召回、是否预测转人工、是否符合预期和禁用词命中。
- `allow_auto_reply=false` 或高风险且明确预期人审的题，会进入 `needs_review`；这类结果用于验证门禁正确性，不应简单理解成“模型失败”。
- P2-22 仍不生成自由文本答案，因此 `unsupported_answer_rate` 继续保持 `null`，后续必须在 `rag_model_assisted` 或端到端答案评测中再计算真实胡编率/幻觉率。

P2-22B 客服脱敏题库导入：

- `knowledge_evaluation_cases` 新增 `external_case_id`、`source_channel`、`source_category`、`annotation_notes`，用于保留脱敏题库的外部题号、来源渠道、业务分类和标注备注。
- 新增 `scripts/import_customer_service_eval_bank.py`，支持从 CSV 或 JSON 读取 50-100 条脱敏客户题，转换成 `customer_service_retrieval` API payload。
- 脚本默认 dry-run：只输出总数、风险等级分布、问题类型分布、渠道分布、需人审数、禁止自动回复数、case hash，不打印原始问题。
- 脚本默认拦截高置信隐私模式：手机号、邮箱和身份证号命中时返回 `blocked_sensitive_rows`，不生成 payload，不调用 API。
- 只有显式传 `--create --api-base --tenant-id --token` 时才会调用后端评测集创建 API；这属于内部 API 写入，不是外部平台发送，也不会调用模型 provider。
- 模板文件为 `evals/customer_service_eval_bank_template.csv`，真实客户题库导入前必须先完成脱敏、人工标注和来源确认。

P2-22C 客服评测运行报告导出：

- 新增 `scripts/export_customer_service_eval_report.py`，输入为知识评测运行 JSON，也就是 `POST /api/knowledge-evaluation-sets/{evaluation_set_id}/runs` 返回的结构。
- 默认输出两份文件：CSV 逐题表和 Markdown 复盘报告。CSV 便于筛选 `knowledge_gap`、`failure_reason`、`human_review_prediction_correct`、`citation_precision`；Markdown 便于给运营、知识库维护和项目管理复盘。
- 默认不导出原始问题，也不导出 `top_match.content_preview` 这类命中知识片段原文，只导出 `question_hash` 和可计算指标。需要内部人工复核原文时，必须显式传 `--include-raw-text`，且产物不应进入长期共享资料。
- 导出脚本只做本地文件读写，不调用模型、不调用平台、不创建评测集，也不触发任何外部写入；返回摘要中固定记录 `provider_call_performed=false` 和 `external_write_performed=false`。
- 这一步补的是“评测结果可被人审、可被知识运营消化”的闭环，不等于生成答案事实性评估、真实幻觉率评测或生产级质量认证已经完成。

P2-22D 客服评测运行读取 API：

- 新增 `GET /api/knowledge-evaluation-runs/{evaluation_run_id}`，复用 `KnowledgeEvaluationRunRead` 返回结构，包含汇总指标和逐题 `case_results`。
- 该接口只允许 owner/admin 使用；无 token 返回 401，普通坐席返回 403，其他租户 owner 读取返回 404。
- 设计用途是让已经落库的评测运行可以被重新取回，再交给 `scripts/export_customer_service_eval_report.py` 导出报告，不需要依赖一次性 POST 响应。
- 响应结构仍包含题目原文和 result payload，所以它不是普通坐席工作台接口，也不是客户对外自助下载接口。需要对外共享时，应先用 P2-22C 默认脱敏报告。

P2-22E 客服评测运行历史列表：

- 新增 `GET /api/knowledge-evaluation-sets/{evaluation_set_id}/runs`，返回 `KnowledgeEvaluationRunList`，按 `created_at desc, id desc` 展示最近运行，支持 `page` 和 `page_size`。
- 列表项使用 `KnowledgeEvaluationRunSummaryRead`，只包含运行级指标和 `summary_payload`，不包含逐题 `case_results`，也不返回问题原文。
- 该接口只允许 owner/admin 使用；无 token 返回 401，普通坐席返回 403，其他租户 owner 读取返回 404。
- 前端 `frontend/src/api/client.ts` 新增 `listKnowledgeEvaluationRuns` 和 `getKnowledgeEvaluationRun`；`frontend/src/App.tsx` 的“知识评测与质量”面板新增最近运行列表，点击历史运行后才调用详情接口。
- 这一步解决的是“刷新后还能找回历史评测运行”，不等于已经完成脱敏报告一键导出、真实客户 50-100 题验收、生成答案事实性评测或幻觉率统计。

P2-22F 客服评测脱敏报告 API 与前端下载入口：

- 新增 `GET /api/knowledge-evaluation-runs/{evaluation_run_id}/report?format=markdown|csv`，返回 `KnowledgeEvaluationRunReportRead`，包含 `filename`、`content_type`、`body`、`summary` 和安全边界标记。
- 该接口只允许 owner/admin 使用；无 token 返回 401，普通坐席返回 403，其他租户 owner 读取返回 404。
- API 只导出脱敏内容：Markdown 和 CSV 都只包含 `question_hash`、来源元数据、运行指标、失败原因、知识缺口和人审判断，不包含问题原文，不包含命中知识片段正文，也不支持 `include_raw_text` 参数。
- 返回固定记录 `raw_text_included=false`、`provider_call_performed=false`、`external_write_performed=false`，说明导出过程不调用模型 provider、不写外部平台。
- 前端 `frontend/src/api/client.ts` 新增 `exportKnowledgeEvaluationRunReport`；`frontend/src/App.tsx` 的当前运行头部新增“下载报告”和“CSV”按钮，浏览器本地用 Blob 下载返回正文。
- 这一步把“评测运行历史 -> 运行详情 -> 脱敏报告”连成运营可用闭环，但仍不是生成答案事实性评测，也没有真实客户 50-100 题验收。

P2-23 合成脱敏客服验收题库：

- 新增 `evals/customer_service_eval_bank_synthetic_80_2026-06-26.csv`，共 80 条题，字段沿用 P2-22B 导入模板。
- 题库覆盖 8 个渠道：`web_widget`、`wecom`、`official_account`、`douyin`、`xiaohongshu`、`taobao`、`jd`、`pdd`。
- 题库覆盖 10 类业务：产品咨询、价格优惠、下单支付、发货物流、售后退换、发票合同、账号隐私、渠道规则、企业采购、知识缺口。
- dry-run 校验结果：`total_cases=80`、`risk_level_counts low=23 medium=33 high=21 critical=3`、`human_review_expected_cases=57`、`auto_reply_blocked_cases=57`、`sensitive_row_count=0`。
- 新增 `docs/P2-23_SYNTHETIC_CUSTOMER_SERVICE_EVAL_BANK.md`，记录题库定位、覆盖范围、使用方式和边界。
- 新增测试覆盖该题库可被 `scripts/import_customer_service_eval_bank.py` dry-run 校验，且摘要和 case catalog 不包含问题原文、不触发 provider 或外部写入。
- 这份题库是安全压力测试和工程基线，不是自然流量分布；高风险、人审、知识缺口题被故意提高占比，用来验证系统不会对赔付、合同、隐私和平台规则问题贸然自动回复。

P2-24 合成题库知识检索闭环 smoke：

- 新增 `evals/p2_24_seed_knowledge_documents.json`，包含 9 份合成 seed 知识文档，标题和来源 URI 对齐 P2-23 题库中的产品套餐、渠道规则、价格优惠、下单支付、物流签收、售后退换、发票合同、账号隐私、企业采购与系统集成。
- 新增 `scripts/run_p2_24_synthetic_eval_smoke.py`，使用本地一次性 SQLite 和 FastAPI TestClient 创建临时租户，导入 seed 文档，复用 P2-23 80 题创建内部评测集，运行 `customer_service_retrieval`，再通过 P2-22F 报告 API 导出 Markdown/CSV。
- 新增 `backend/tests/test_p2_24_synthetic_eval_smoke_script.py`，验证 smoke 不调用外部模型、不写外部平台、不把原始问题写入结果摘要，并要求 `forbidden_term_hits=0`。
- 本地输出位于 `output/evals/p2_24_synthetic_eval_smoke/`，包含 summary JSON、脱敏 Markdown 复盘报告和脱敏 CSV 逐题表。
- 2026-06-26 smoke 指标：`seed_document_count=9`、`seed_chunk_count=36`、`total_cases=80`、`hit_rate=100.0%`、`citation_coverage=100.0%`、`expected_term_coverage=78.8%`、`average_confidence=0.6682`、`human_review_correctness=91.2%`、`forbidden_term_hits=0`、`unsupported_answer_rate=null`。
- 当前不足：`expected_term_coverage` 和 `citation_precision` 仍需优化，`full_evidence_recall_at_5=0.0%` 是因为 P2-23 题库尚未绑定导入后的动态 chunk id；知识缺口题当前通过 `allow_auto_reply=false` 进入人审，但还没有真正的知识缺口修复工作流。

P2-25 chunk id 回填评测对比：

- 新增 `scripts/run_p2_25_chunk_backfill_eval_comparison.py`，复用 P2-24 的本地 TestClient、安全环境、seed 文档导入和报告 API。
- 脚本先创建原始题库基线评测集，再读取 `/api/knowledge-documents/{document_id}/chunks` 返回的真实 chunk id，按 `expected_source_uri + expected_terms` 动态回填 `expected_chunk_ids`，再创建 chunk 回填版评测集。
- 新增 `backend/tests/test_p2_25_chunk_backfill_eval_comparison_script.py`，验证回填后 `full_evidence_cases` 变成可计算样本，并继续确认无外部模型调用、无外部平台写入、报告不含原始问题。
- 新增 `docs/P2-25_CHUNK_BACKFILL_EVAL_COMPARISON.md`，记录回填逻辑、输出目录、指标解释和下一步。
- 本地输出位于 `output/evals/p2_25_chunk_backfill_eval_comparison/`，包含 summary JSON、对比 Markdown、case binding CSV、回填版脱敏 Markdown 和回填版脱敏 CSV。
- 2026-06-27 对比指标：`bound_case_count=76/80`、`full_evidence_cases 0 -> 76`、`full_evidence_recall_at_5 0.0% -> 57.9%`、`citation_precision=39.8%`、`expected_term_coverage=78.8%`、`human_review_correctness=91.2%`。
- 当前判断：P2-25 让完整证据召回指标可解释，但 `57.9%` 说明 top-k 对具体 chunk 的完整覆盖仍不足。下一步应优先做 P2-26 检索/知识文档对比优化，而不是急着进入模型生成。

P2-26 检索 top-k 参数对比：

- 新增 `scripts/run_p2_26_retrieval_quality_comparison.py`，复用 P2-24 的本地 TestClient、安全环境、seed 文档导入和报告 API，并复用 P2-25 的动态 chunk id 回填逻辑。
- 脚本对同一个 chunk 回填版评测集运行 `top_k=5/8/10/12`，输出运行汇总、推荐 top-k、最高召回池 top-k、失败题 delta CSV 和推荐 top-k 对应的脱敏 Markdown/CSV 报告。
- 新增 `backend/tests/test_p2_26_retrieval_quality_comparison_script.py`，验证 top-k 对比不调用外部模型、不写外部平台、不输出原始问题，并生成失败题 delta。
- 新增 `docs/P2-26_RETRIEVAL_QUALITY_COMPARISON.md`，记录运行命令、输出目录、指标、默认推荐、召回池建议和下一步。
- 本地输出位于 `output/evals/p2_26_retrieval_quality_comparison/`，包含 summary JSON、对比 Markdown、失败题 delta CSV 和推荐 top-k=8 的脱敏评测报告。
- 2026-06-27 对比指标：`top_k=5/8/10/12` 的 `full_evidence_recall_at_k` 分别为 `57.9% / 67.1% / 72.4% / 76.3%`，`citation_precision` 分别为 `39.8% / 32.2% / 29.9% / 27.8%`，`forbidden_term_hits` 分别为 `0 / 2 / 3 / 3`。
- 当前判断：top-k 太小确实是完整证据召回不足原因之一，但直接扩大 top-k 会降低引用精度并引入安全噪音。生产默认先用 `top_k=8`；`top_k=12` 只作为召回池，必须配合二阶段重排、同源 boost、风险证据隔离和证据压缩。

P2-5 仍然不是完整智能客服：

- 没有向量检索、重排或引用片段级溯源。
- 没有模型路由成本统计表，只在 workflow state 中记录本次调用摘要。
- 已有 provider fallback 链路的决策记录，但还没有生产级限流、熔断、重试或队列。
- P2-5 当时没有出站消息、内部 outbox、平台官方回调和发送闭环；P2-7 已补内部 outbox 草稿，但仍没有真实发送闭环。
- 默认 deterministic 草稿只能证明编排链路，不代表真实模型回答质量。

## P2-6 坐席审核队列与草稿处理 API v1

已新增 `GET /api/tenants/{tenant_id}/human-review-inbox`，用于坐席工作台读取真正可处理的审核任务。

请求示例：

```text
GET /api/tenants/1/human-review-inbox?status=open
Authorization: Bearer <token>
```

返回结构按一条审核任务聚合以下信息：

| 字段 | 作用 |
| --- | --- |
| 任务字段 | `id`、`status`、`reason`、`risk_level`、`draft_reply`、`final_reply`、`assigned_user_id`、`reviewer_id` |
| `conversation` | 会话摘要，包含渠道、联系人、主题、优先级、分配坐席/团队 |
| `trigger_message` | 触发本次编排的入站消息原文、发送者类型和消息时间 |
| `workflow` | 对应 workflow run 的状态、当前步骤和创建/更新时间 |
| `evidence` | 编排证据包，包含意图、知识命中、模型调用、置信度、风险等级和草稿来源 |

`evidence` 当前重点字段：

| 字段 | 作用 |
| --- | --- |
| `retrieval_engine` | 当前通常为 `lexical_bm25_v1` |
| `knowledge_matches` | 本次命中的知识卡片摘要，供坐席判断依据是否够用 |
| `model_call` | 模型 provider、model、状态、错误信息和用量估算 |
| `confidence` | 编排器综合置信度 |
| `risk_level` | 当前风险等级 |
| `draft_source` | 草稿来源，例如 `knowledge_card`、`model_gateway`、`model_gateway_unavailable` |

已增强 `PATCH /api/human-review-tasks/{task_id}`：

- `decision=approved` 且传入 `final_reply`：记录坐席改写后的最终回复。
- `decision=approved` 且 `final_reply` 为空：默认使用原 `draft_reply` 作为最终回复。
- `decision=rejected`：关闭任务并保留拒绝原因。
- 审核完成后 workflow 进入 `completed / record_result`。
- workflow state 写入 `human_review`，包含 `task_id`、`decision`、`reviewer_id`、`final_reply`、`resolution_note` 和 `resolved_at`。
- 审核动作继续写入 `human_review.approved` 或 `human_review.rejected` 审计事件。

P2-6 仍然不是完整坐席工作台或发送闭环：

- 还没有前端审核队列页面。
- 审核通过不会自动创建出站消息。
- 审核通过不会发送到企业微信、官网客服、公众号或电商平台。
- P2-7 已补内部 outbox 草稿、幂等键和发送前确认；仍没有真实发送 attempts、发送重试、渠道回执和失败告警。
- 还没有坐席分配规则、队列 SLA、多人锁单或权限细分。

## P2-7 Outbox 草稿出站准备与发送前确认 v1

已新增 `outbox_drafts` 表和 outbox API。这个阶段的目标不是外发消息，而是把“已批准最终回复”放进一个可确认、可取消、可审计、防重复的内部待发送草稿队列。

新增接口：

| 接口 | 作用 |
| --- | --- |
| `POST /api/human-review-tasks/{task_id}/outbox-drafts` | 仅从 `approved` 人工审核任务创建 outbox 草稿 |
| `GET /api/tenants/{tenant_id}/outbox-drafts` | 按租户和可选 `status` 查看 outbox 草稿 |
| `POST /api/outbox-drafts/{draft_id}/confirmation` | 坐席确认草稿，状态从 `pending_confirmation` 进入 `ready_to_send` |
| `POST /api/outbox-drafts/{draft_id}/cancellation` | 坐席取消待确认草稿 |

当前状态机：

```text
approved human_review_task
  -> outbox_draft.pending_confirmation / delivery_status=not_sent
  -> confirmation
  -> outbox_draft.ready_to_send / delivery_status=not_sent

approved human_review_task
  -> outbox_draft.pending_confirmation / delivery_status=not_sent
  -> cancellation
  -> outbox_draft.canceled / delivery_status=not_sent
```

当前 outbox 字段重点：

| 字段 | 作用 |
| --- | --- |
| `source_review_task_id` | 来源人工审核任务 |
| `source_workflow_run_id` | 来源 workflow run |
| `source_message_id` | 来源入站消息 |
| `conversation_id`、`channel_id`、`contact_id` | 未来渠道发送器所需的路由上下文 |
| `reply_text` | 坐席审核后的最终回复文本 |
| `idempotency_key` | 默认 `human_review_task:{id}:final_reply`，防止重复创建同一任务的待发送草稿 |
| `status` | 当前为 `pending_confirmation`、`ready_to_send` 或 `canceled` |
| `delivery_status` | 当前保持 `not_sent`，因为本阶段不做真实发送 |
| `confirmation_note`、`cancellation_reason` | 发送前确认或取消原因 |

当前安全与审计：

- 所有 outbox API 需要有效 Bearer token。
- 跨租户访问返回 404。
- 未批准的人工审核任务不能创建 outbox 草稿。
- 同一审核任务默认只能创建一个 outbox 草稿，重复创建返回 409。
- 已取消草稿不能再确认。
- 创建、确认和取消分别写入 `outbox_draft.created`、`outbox_draft.ready_to_send`、`outbox_draft.canceled` 审计事件。
- workflow state 会写入 `outbox_draft` 摘要，便于回看“这条回复后来进入了哪个待发送草稿”。

P2-7 仍然不是完整发送闭环：

- 还没有真实出站 `Message` 写入。
- 还没有渠道发送器。
- P2-8 已补发送尝试表和 dry-run 结果；仍没有真实重试、渠道回执、失败告警和平台消息 ID。
- 还没有前端 outbox 队列页面。
- 还没有企业微信、官网客服、公众号或电商平台的官方发送适配器。

## P2-8 Outbox dry-run 发送尝试记录 v1

已新增 `outbox_send_attempts` 表和 send attempt API。这个阶段的目标不是发送消息，而是把 `ready_to_send` 草稿进入真实渠道前的执行记录、幂等和审计链补上。

新增接口：

| 接口 | 作用 |
| --- | --- |
| `POST /api/outbox-drafts/{draft_id}/send-attempts` | 对 `ready_to_send` 草稿创建 dry-run 发送尝试 |
| `GET /api/outbox-drafts/{draft_id}/send-attempts` | 查看某个草稿的发送尝试记录 |

当前状态机：

```text
outbox_draft.ready_to_send / delivery_status=not_sent
  -> POST /send-attempts delivery_mode=dry_run
  -> outbox_send_attempt.succeeded / delivery_status=not_sent
  -> outbox_draft 仍保持 delivery_status=not_sent
```

当前 send attempt 字段重点：

| 字段 | 作用 |
| --- | --- |
| `outbox_draft_id` | 来源 outbox 草稿 |
| `attempt_number` | 同一草稿内的尝试序号 |
| `delivery_mode` | 当前只允许 `dry_run` |
| `provider` | 当前固定为 `dry_run` |
| `status` | dry-run 记录结果，当前成功为 `succeeded` |
| `delivery_status` | 当前保持 `not_sent`，因为没有真实外发 |
| `idempotency_key` | 默认 `outbox_draft:{id}:dry_run`，防止重复 dry-run 记录 |
| `request_payload` | dry-run 将要发送的路由上下文和回复预览 |
| `response_payload` | 明确 `external_write=false` 和 `would_send=true` |
| `external_message_id`、`sent_at` | 当前保持空，避免伪造真实平台回执 |

当前安全与审计：

- 所有 send attempt API 需要有效 Bearer token。
- 只能对同租户 outbox 草稿创建或查看发送尝试。
- 只有 `ready_to_send` 草稿可以创建 send attempt。
- 当前只支持 `delivery_mode=dry_run`，不支持真实发送。
- 重复 idempotency key 返回 409。
- dry-run 成功写入 `outbox_send_attempt.dry_run_succeeded` 审计事件。
- workflow state 会写入 `outbox_send_attempt` 摘要，便于回看“这条回复是否已经做过发送前 dry-run 检查”。

P2-8 仍然不是完整发送闭环：

- 没有调用企业微信、官网客服、公众号、抖音或电商平台 API。
- 没有真实出站 `Message` 写入。
- 没有真实平台 `external_message_id`。
- 没有失败重试、回执同步、限流、熔断和告警。
- P2-9 已补轻量前端队列入口，P2-10 已补 worker dry-run 发送检查；但仍不是完整坐席工作台，也不是官方渠道发送闭环。

## P2-9 坐席前端审核与待发送链路 v1

已把前端从静态队列推进到真实后端数据驱动的最小坐席闭环。这个阶段的目标不是做完整客服工作台，而是让坐席能在页面里完成一条受控链路：

```text
人工审核收件箱
  -> 查看会话、入站消息、证据包和回复草稿
  -> 批准入待发送，或拒绝该草稿
  -> 已批准任务生成待发送草稿
  -> 坐席确认待发送
  -> 触发模拟发送
  -> 页面显示模拟发送结果，仍保持 not_sent
```

前端新增能力：

| 能力 | 前端调用 |
| --- | --- |
| 读取人工审核收件箱 | `GET /api/tenants/{tenant_id}/human-review-inbox?status=open` |
| 批准或拒绝审核任务 | `PATCH /api/human-review-tasks/{task_id}` |
| 从已批准任务生成待发送草稿 | `POST /api/human-review-tasks/{task_id}/outbox-drafts` |
| 读取待确认和已确认草稿 | `GET /api/tenants/{tenant_id}/outbox-drafts` |
| 确认草稿进入待发送 | `POST /api/outbox-drafts/{draft_id}/confirmation` |
| 触发模拟发送 | `POST /api/outbox-drafts/{draft_id}/send-attempts` |
| 运行发送检查 | `POST /api/tenants/{tenant_id}/outbox-worker-runs` |
| 配置渠道连接器占位 | `POST /api/channels/{channel_id}/connector-config` |
| 生成官方渠道发送计划 | `POST /api/outbox-drafts/{draft_id}/connector-send-plans` |

当前页面边界：

- “人工审核收件箱”只处理 `open` 任务，显示原因、风险等级、入站消息、草稿和证据摘要。
- “批准入待发送”当前使用已有 `draft_reply` 作为最终回复；还没有富文本改写器、快捷话术和敏感词检查 UI。
- “待发送草稿”会显示 `pending_confirmation` 和 `ready_to_send` 草稿。
- `pending_confirmation` 只能确认待发送，不能模拟发送。
- `ready_to_send` 才能触发模拟发送。
- 单条模拟发送完成后按钮显示“已模拟”；worker 发送检查完成后按钮显示“已检查”。页面仍展示 `not_sent`，避免误读成真实平台发送。
- “生成渠道计划”会先写入官方连接器占位配置，再创建 `connector_noop` 发送计划；页面显示 `blocked`、`not_sent` 和“外部写入：否”。
- 页面文案已把可见的 `dry-run` 和 `outbox` 尽量改为中文；后端字段仍保留这些工程名，便于状态机和测试稳定。

P2-9 仍然不是完整坐席工作台：

- 没有会话详情抽屉、历史消息流和联系人画像。
- 没有坐席改写编辑器。
- 没有知识引用展开、模型调用详情展开和成本展示。
- 没有批量处理、分配、团队队列、SLA、工单或失败告警。
- 没有真实渠道外发、真实平台消息 ID、真实平台回执验签和真实重试。

## P2-10 Outbox worker dry-run 与回执/重试占位 v1

已新增 `POST /api/tenants/{tenant_id}/outbox-worker-runs`。这个阶段的目标不是接通平台外发，而是把“待发送草稿由 worker 扫描处理”的生产形态先做出来，并明确保留失败、限流、回执和重试字段。

请求示例：

```json
{
  "batch_size": 20,
  "rate_limit_per_minute": 60,
  "max_attempts": 3
}
```

当前 worker 行为：

- 只扫描同租户 `ready_to_send` 草稿。
- 按 `confirmed_at` 和 `id` 做稳定顺序处理。
- 默认每批最多 20 条，每分钟限流 60 条，最多尝试 3 次；可通过请求体或环境变量覆盖。
- 对已存在 `dry_run_worker + succeeded` 记录的草稿跳过，避免重复处理。
- 对已达到最大尝试次数的草稿跳过，后续应进入人工复盘或失败队列。
- 渠道状态为 `active` 时记录 `succeeded`；渠道不存在或非 active 时记录 `failed`。
- 当前所有 attempt 的 `delivery_status` 仍为 `not_sent`，`external_message_id` 为空，`sent_at` 为空。
- `request_payload` 和 `response_payload` 都明确写入 `external_write=false`，证明没有调用外部平台。

新增响应重点字段：

| 字段 | 作用 |
| --- | --- |
| `scanned` | 本次实际进入 worker 候选的 ready 草稿数量 |
| `processed` | 本次创建发送检查记录的草稿数量 |
| `succeeded` | worker dry-run 成功数量 |
| `failed` | worker dry-run 失败数量，例如渠道暂停 |
| `rate_limited` | 因本轮限流未处理的数量 |
| `rate_limited_draft_ids` | 被限流保留到后续批次的草稿 ID |
| `skipped_draft_ids` | 因已有成功记录或达到最大尝试次数而跳过的草稿 ID |
| `external_write` | 当前固定为 `false` |
| `rate_limit` | 本轮批大小、每分钟限流和最大尝试次数 |
| `attempts` | 本轮实际生成的 `outbox_send_attempts` |

attempt 的占位字段：

| 字段 | 当前含义 |
| --- | --- |
| `provider=dry_run_worker` | 说明该记录来自 worker，而不是坐席单条手动模拟 |
| `receipt_placeholder.status=not_available` | 当前没有真实平台回执 |
| `retry_placeholder.next_action=none` | 成功 dry-run，无需重试 |
| `retry_placeholder.next_action=retry_later` | 失败但仍有尝试次数，后续可接队列重试 |
| `retry_placeholder.next_action=manual_review` | 已无重试次数，后续应进人工复盘 |

前端同步：

- “待发送草稿”面板新增“运行发送检查”。
- 最近一次 worker 结果显示扫描、处理、成功、失败、限流和“外部写入：否”。
- worker 产生的记录显示为“发送检查 #N”，按钮显示“已检查”，避免和坐席单条“模拟发送”混淆。

P2-10 仍然不是完整发送闭环：

- 没有企业微信、公众号、抖音、小红书、淘宝、京东或拼多多的官方发送 adapter。
- 没有真实平台消息 ID。
- 没有真实回执 webhook。
- 没有队列系统、并发 worker、分布式锁、真实重试调度、熔断和告警。
- 当前限流只是单次 worker run 的容量控制，不是跨进程、跨实例的生产级限流。
- 当前失败状态只证明状态机和审计链能记录失败，不代表已经接入平台错误码。

## P2-11 官方渠道 connector 占位与真实回执前置设计

已新增 `channel_connectors`、`channel_delivery_receipts` 和 `POST /api/outbox-drafts/{draft_id}/connector-send-plans`。这一片不是接通企业微信、公众号或官网客服真实外发，而是先把未来官方渠道发送器需要的配置、验签、回执、失败码和队列边界落成可测试契约。

连接器配置请求示例：

```json
{
  "provider": "wecom",
  "mode": "noop",
  "status": "ready",
  "display_name": "企业微信客服官方接口占位",
  "capabilities": ["send_text", "delivery_receipt"],
  "public_config": {
    "official_authorization": "pending",
    "external_write": "disabled"
  },
  "webhook_path": "/api/webhooks/wecom/channels/1",
  "signature_mode": "wecom_token_aeskey"
}
```

当前强制边界：

- `external_write_enabled=false`，无论前端如何调用都不会真实外发。
- 默认 `secret_status=not_configured`，不会在响应体暴露密钥、令牌、回调密钥或 EncodingAESKey；P2-13 仅允许 `credential_ref` 指向开发 fixture 时显示 `fixture_configured`。
- `mode=noop` 只生成内部发送计划，`mode=official_api` 目前也不能打开外部写入。
- `connector-send-plans` 生成的 attempt 固定为 `delivery_mode=connector_noop`、`status=blocked`、`delivery_status=not_sent`。
- 发送计划 response payload 明确包含 `external_delivery_disabled`、`official_api_enabled=false`、回执契约、重试契约和 webhook 验签要求。
- 回执接口当前只记录占位事件，`verification_status=not_verified_placeholder`，不能对客户声称已完成官方平台验签。

当前前端同步：

- 待发送草稿新增“生成渠道计划”按钮。
- 若渠道没有连接器配置，前端直接调用幂等的占位配置接口，不再用 404 作为正常分支。
- 生成后页面显示“渠道计划 #N · blocked · not_sent”和“官方计划 #N · 外部写入：否”。
- 已生成计划后按钮置灰，避免重复点击产生幂等冲突。

P2-11 仍然不是完整渠道接入：

- 没有企业微信客服真实 access token 获取、消息发送 API、回调验签和消息解密。
- 没有微信公众号、官网客服、小红书、抖音、淘宝、京东、拼多多的官方授权流程。
- 没有真实平台消息 ID，因此无法匹配真实送达、失败、撤回或用户已读事件。
- 没有生产级队列、分布式限流、锁、指数退避、熔断和告警。
- 当前错误码映射仍是契约占位，不能代表任何平台官方错误码已经接入。

## P2-12 官方渠道 Webhook 骨架

P2-12 解决的是“官方平台如何主动把事件回调到我们自己的客服中台”这一层工程骨架。它不是企业微信、微信公众号或电商平台的真实可用接入。P2-13 已在此基础上补了开发 fixture 验签，P2-14 又补了验签通过后的可信入站消息创建和重复回调拦截，但仍没有真实消息解密、主动回复 API、平台 token 刷新、服务商授权流程或生产级队列。

新增 provider registry：

| Provider | 显示名 | 默认签名模式 | 当前状态 |
| --- | --- | --- | --- |
| `wecom` | 企业微信客服 | `wecom_token_aeskey` | `skeleton_only` |
| `wechat_official_account` | 微信公众号 | `wechat_token` | `skeleton_only` |
| `website` | 官网客服组件 | `website_hmac_sha256` | `skeleton_only` |

新增 webhook 入口：

```text
POST /api/webhooks/{provider}/channels/{channel_id}
```

当前行为：

- 不要求 Bearer token，因为真实开放平台回调不会携带内部坐席登录态。
- 先检查 provider 是否在 registry 中。
- 再检查渠道是否存在、是否已经配置同 provider 的 `channel_connector`。
- provider 不存在、渠道不存在或 provider 不匹配时返回 404，避免泄露跨租户信息。
- 回调 payload 只落成 `channel_delivery_receipts` 的未可信记录。
- 不保存 `msg_signature`、`signature` 等签名值本身，只保存 query key 和验证状态摘要。
- 密钥未配置时标记 `secret_not_configured`。
- 如果 `credential_ref` 指向 P2-13 开发 fixture，服务端会计算签名并得到 `signature_validated` 或 `signature_invalid`。
- `signature_validated` 永远由服务端计算，调用方不能通过请求体自行声明为真。
- P2-14 起，验签通过且 payload 中具备消息内容、联系人身份和幂等键时，可以创建可信入站消息；P2-15 起，可由受保护 worker 触发内部编排，但仍不在 webhook 请求内直接自动回复或外部写入。

## P2-13 官方签名 fixture 与 secret store 边界

P2-13 不是“接通真实平台”，而是先把可信入口的第一道门做成可测试代码：密钥不能放在 `public_config`，签名值不能落库，只有服务端按 provider 规则计算出的有效签名才能把回执标记为 `signature_validated=true`。

新增服务：

| 文件 | 作用 |
| --- | --- |
| `backend/app/services/channel_secret_store.py` | 建立 `credential_ref -> secret material` 边界；当前只有 P2-13 fixture，真实客户密钥后续必须接 secret store/KMS |
| `backend/app/services/channel_webhook_verifier.py` | 按 provider 计算签名并返回验证摘要，不保存签名原文 |

当前 fixture 覆盖：

| Provider | 验证方式 | 当前边界 |
| --- | --- | --- |
| `wecom` | `sha1(sort(token, timestamp, nonce, Encrypt))` | 只验签，不解密 `Encrypt`，不创建 `messages` |
| `wechat_official_account` | 明文模式 `sha1(sort(token, timestamp, nonce))`；安全模式保留 `Encrypt` 签名路径 | 只覆盖 fixture，安全模式解密后置 |
| `website` | `HMAC-SHA256(timestamp + nonce + canonical_payload)` | 自有官网组件签名方案，生产还缺 nonce 存储和重放保护 |

当前新增保护：

- `public_config` 只允许保存 `credential_ref`，不保存 token、EncodingAESKey、app_secret 或 signing secret。
- `secret_status` 默认仍是 `not_configured`；只有 fixture ref 能显示 `fixture_configured`。
- `msg_signature`、`signature` 等 query 参数值不落库，只保存 query key。
- raw payload 中如果出现 `signature`、`token`、`secret`、`authorization`、`cookie` 等敏感 key，会被写成 `[redacted]`。
- timestamp 超出短窗口会返回 `timestamp_expired`，为后续重放保护预留边界。
- P2-13 完成时，验签成功的 webhook 只标记为 `verified_receipt_only`，`trusted_message_creation=false`，不会触发自动回复；P2-14 已在内容、联系人和幂等键齐备时允许创建可信入站消息。

P2-13 完成时仍未解决的缺口：

- 没有真实企业微信/公众号客户密钥存储表或 KMS。
- 没有企业微信/微信公众号 AES 解密。
- 没有 provider event id 或 nonce 的生产级持久化去重；P2-14 只做了基于现有回执和消息记录的轻量幂等拦截。
- 没有把真实平台加密事件解析为可信入站消息；P2-14 只支持开发 fixture 或明文测试 payload 中已包含内容和联系人身份的场景。
- 没有入站消息 worker、ReplyOrchestrator 自动触发、平台错误码归一化或真实外发。

这一层后续要升级为真实官方渠道接入，至少还需要：

| 能力 | 工程要求 |
| --- | --- |
| 官方验签 | 按企业微信、微信公众号、抖音、小红书、淘宝等官方文档分别实现签名校验，并补充固定 fixture |
| 消息解密 | 对加密 payload 接入官方算法，且密钥来自 secret store，不写入 `public_config` |
| 幂等去重 | 按 provider event id、external message id、timestamp 等组合去重 |
| 入站消息创建 | 只有验签通过且解析成功后，才允许写入 `messages` 和触发 reply orchestration |
| 平台错误码 | 建立 provider error code 映射，供 outbox worker 判断是否可重试 |
| 真实发送器 | 在 `external_write_enabled`、授权状态、限流和人工策略全部满足后，才打开官方 API 外发 |

## P2-14 可信入站消息管道与幂等去重

P2-14 解决的是“官方回调已经通过服务端验签以后，能不能进入我们自己的客服消息流”这一层问题。它仍然不是完整真实平台接入，因为真实企业微信/微信公众号的加密消息解密、服务商授权、access token 刷新和主动回复 API 还没有打开。

新增服务：

| 文件 | 作用 |
| --- | --- |
| `backend/app/services/trusted_inbound_messages.py` | 把已验签 webhook 解析为内部可信入站消息，负责联系人/会话复用、消息写入、幂等拦截、会话事件和审计事件 |
| `backend/app/services/channel_connectors.py` | 在 webhook 入口验签通过后调用可信入站消息管道，并把创建结果写入 receipt `parsed_event` 和 `webhook_intake` 摘要 |

当前可创建可信入站消息的条件：

| 条件 | 要求 |
| --- | --- |
| 事件类型 | `event_type=message` |
| 验签状态 | `signature_validated=true`，必须由服务端 verifier 计算，不能由请求体自称 |
| 幂等键 | 优先使用 `provider_event_id`，缺失时使用 `external_message_id` |
| 消息内容 | payload 中需要有 `Content`、`content`、`Text`、`text`、`message_content` 或 `message_text` |
| 联系人身份 | payload 中需要有 `FromUserName`、`FromUserId`、`external_userid`、`openid`、`user_id`、`visitor_id` 或 `contact_external_id` |

当前写入结果：

- 新联系人写入 `contacts`，当前用 `provider:external_contact_id` 临时写入 `Contact.wechat` 作为轻量映射；后续真实多渠道要升级为独立 external identity 表。
- 如果同租户、同渠道、同联系人已有未关闭会话，则复用会话；否则创建 `Conversation.status=bot` 的新会话。
- 写入 `Message.direction=inbound`、`sender_type=visitor`、`external_message_id=平台消息 ID`。
- 写入 `ConversationEvent.event_type=message.inbound.trusted_webhook`。
- 写入 `AuditEvent.action=channel_webhook.trusted_inbound_message_created`。
- Webhook 响应和 receipt `parsed_event` 返回 `trusted_message_creation`、`trusted_message_id`、`contact_id`、`conversation_id`、`idempotency_status` 和 `idempotency_key`。

当前重复回调处理：

- 如果同 provider、同 channel、同 provider event id 已有验签 receipt，优先视为重复。
- 如果没有 provider event id，但同 channel 下已经存在相同 `external_message_id` 的消息，也视为重复。
- 重复回调不会再写 `messages`，会返回 `status=duplicate_ignored`，并记录 `channel_webhook.duplicate_ignored` 审计事件。
- 当前幂等还不是生产级唯一约束；后续应增加独立 idempotency 表或数据库唯一索引，避免并发竞态。

当前明确未完成：

- Webhook 请求内仍不会直接调用 ReplyOrchestrator；P2-15 已提供受保护的 HTTP worker 入口，但还不是 Redis/RQ/Celery 生产队列。
- 还没有真实企业微信/微信公众号 AES 解密，因此加密 payload 仍只能用于验签，不会自动解出正文。
- 还没有 provider-specific 消息类型映射，例如图片、视频、订单卡片、商品卡片、菜单事件、撤回事件。
- 还没有多渠道联系人身份表，`Contact.wechat` 只是本阶段的轻量临时映射。
- P2-16 已补平台回执失败复盘队列；入站 worker 自身异常当前仍先落审计事件和 run item 摘要，后续再并入生产级死信/复盘队列。

## P2-15 可信入站消息编排 worker

P2-15 解决的是“可信入站消息已经入库以后，如何进入客服处理链路”。它不把 webhook 请求变成长耗时 AI 编排，也不打开真实外发，而是提供一个受保护的 worker 运行入口，由内部坐席或后续调度器触发。

新增文件：

| 文件 | 作用 |
| --- | --- |
| `backend/app/workers/trusted_inbound_orchestrator.py` | 扫描 `message.inbound.trusted_webhook` 会话事件，识别未编排可信消息，调用 ReplyOrchestrator，并记录审计 |
| `backend/app/api/inbound_worker.py` | 提供 `POST /api/tenants/{tenant_id}/trusted-inbound-worker-runs` 受保护入口 |
| `backend/app/schemas/inbound_worker.py` | 定义入站 worker 运行请求、单条处理结果和汇总响应 |
| `backend/tests/test_trusted_inbound_worker_api.py` | 覆盖可信消息进入人审、重复运行跳过、限流和错签回执不触发 |
| `scripts/check_stage2_trusted_inbound_worker.py` | P2-15 文件与关键合同自检 |

当前 worker 行为：

- 只扫描已由 P2-14 写入的 `ConversationEvent.event_type=message.inbound.trusted_webhook`。
- 默认 `mode=model_assisted`、`model_provider=deterministic`、`risk_level=medium`，因此会跑知识检索、模型网关草稿，并保守进入人工审核收件箱。
- 使用 `trusted_inbound_message:{message_id}:reply_orchestration` 作为 workflow idempotency key。
- 如果已有同 message id 和同 idempotency key 的 workflow run，重复 worker 运行会跳过，不重复创建 workflow 或人审任务。
- `rate_limit_per_minute=0` 时不会创建 workflow，只返回 rate limited 结果。
- 错签、未验签、缺内容或缺联系人导致没有可信入站 message 的回调，不会被 worker 扫描。
- 成功后写入 `trusted_inbound_worker.orchestrated` 审计事件，并把 worker 摘要写入 workflow state。
- 失败时写入 `trusted_inbound_worker.failed` 审计事件，后续仍需要接入生产级死信/复盘队列。

当前仍不是生产级队列：

- 没有 Redis/RQ/Celery/Arq 等后台消费者。
- 入站消息仍没有独立 idempotency 表或分布式锁来抵御高并发竞态；P2-17 已先给发送队列 job 增加唯一幂等键和锁字段骨架。
- P2-16 已有平台回执失败复盘表，但入站 worker 异常还没有进入同一队列。
- P2-16 已有开发级平台状态/错误码归一化，但没有真实平台解密或真实外部写入。
- 前端只提供“运行入站编排”轻入口，不是完整渠道运维台。

## P2-16 平台回执归一化与失败复盘队列

P2-16 解决的是“平台回执来了以后，系统如何判断它意味着什么，以及哪些异常需要人处理”。它不打开真实外发，也不自动重发，只把不同 provider 的成功、失败、限流、授权异常、权限不足、内容拒绝、接收人不可达和未知状态纳入统一状态机。

新增文件：

| 文件 | 作用 |
| --- | --- |
| `backend/app/services/delivery_failures.py` | 统一归一化平台状态和错误码，必要时创建失败复盘项 |
| `backend/app/api/delivery_failures.py` | 提供失败复盘队列列表和处理接口 |
| `backend/app/schemas/delivery_failures.py` | 定义失败复盘项读取和更新合同 |
| `backend/app/migrations/versions/0007_delivery_failure_reviews.py` | 给回执增加归一化字段，并新增失败复盘队列表 |
| `backend/tests/test_delivery_failure_reviews_api.py` | 覆盖限流失败、成功回执不进队列、未知状态进入人工复盘 |
| `scripts/check_stage2_delivery_failures.py` | P2-16 文件与关键合同自检 |

当前归一化结果：

| 原始状态或错误 | 统一状态 | 是否可重试 | 下一步 |
| --- | --- | --- | --- |
| `delivered`、`send_success`、`ok` | `delivered` | 否 | `none` |
| `read` | `read` | 否 | `none` |
| `received`、`webhook_received` | `received` | 否 | `none` |
| `45009`、`rate_limited`、`system_busy` | `rate_limited` | 是 | `retry_later` |
| `40014`、`42001`、`invalid_access_token` | `auth_failed` | 否 | `refresh_authorization_or_reconfigure_secret` |
| `48002`、`permission_denied` | `permission_denied` | 否 | `check_provider_scope_or_service_market_permission` |
| `customer_not_found`、`not_followed` | `recipient_unreachable` | 否 | `manual_contact_check` |
| `content_violation`、`sensitive_word` | `content_rejected` | 否 | `manual_rewrite` |
| 未识别状态 | `unknown_provider_status` | 否 | `manual_review_provider_status` |

当前接口行为：

- `POST /api/channels/{channel_id}/delivery-receipts` 写入回执时会同步计算 `provider_status`、`provider_error_code`、`normalized_status`、`retryable`、`needs_review` 和 `next_action`。
- `POST /api/webhooks/{provider}/channels/{channel_id}` 写入 webhook 回执时也走同一套归一化逻辑。
- `needs_review=true` 时创建 `delivery_failure_reviews`，并写入 `delivery_failure_review.created` 审计事件。
- `GET /api/tenants/{tenant_id}/delivery-failure-reviews?status=open` 返回开放复盘项。
- `PATCH /api/delivery-failure-reviews/{review_id}` 可把复盘项标记为 `resolved` 或 `ignored`，只改变内部复盘状态，不触发自动重发。

当前仍不是生产级失败治理：

- 没有真实官方发送 API 的 external message id 回填链路。
- 没有真实 provider 全量错误码表，只覆盖 P2-16 开发 fixture 常见类目。
- 没有生产级 retry scheduler、dead letter queue、告警、SLA 和坐席分派。
- 没有把入站 worker 异常、模型调用失败、RAG 失败统一纳入同一个复盘中心。
- 前端只是最小“失败复盘队列”，不是完整客服运维/工单台。

## P2-17 发送队列、锁、重试与 Kill Switch 骨架

P2-17 解决的是“真实外发前，系统如何避免重复发送、如何限流、如何重试、如何进入死信和复盘、如何一键阻断外部写入”。它仍不调用任何官方发送 API，不向微信、公众号、官网客服或电商平台写消息。

新增文件：

| 文件 | 作用 |
| --- | --- |
| `backend/app/services/outbox_delivery_queue.py` | 发送队列服务层，创建 job、运行队列、写锁、限流、重试、死信、合成回执和失败复盘 |
| `backend/app/migrations/versions/0008_outbox_delivery_jobs.py` | 新增 `outbox_delivery_jobs` 队列表 |
| `backend/tests/test_outbox_delivery_queue_api.py` | 覆盖幂等、重复运行不重复尝试、kill switch、限流、重试到死信 |
| `scripts/check_stage2_outbox_delivery_queue.py` | P2-17 文件与关键合同自检 |
| `frontend/src/api/client.ts` | 新增发送队列 job 和队列运行 API client |
| `frontend/src/App.tsx` | 待发送面板新增“加入发送队列”和“运行发送队列” |

当前队列状态：

| 状态 | 含义 |
| --- | --- |
| `queued` | 已入队，等待 runner 处理 |
| `locked` | runner 正在处理，写入 `locked_by` 与 `locked_at` |
| `succeeded` | 队列骨架处理成功；仍未真实外发 |
| `blocked` | 被 kill switch、连接器外部写关闭或未实现真实 sender 阻断 |
| `retry_scheduled` | 失败但未达到最大尝试次数，等待下一轮 |
| `dead_letter` | 达到最大尝试次数或不可继续，进入死信并联动失败复盘 |

当前行为：

- `POST /api/outbox-drafts/{draft_id}/delivery-jobs` 只允许 `ready_to_send` 草稿创建 job，并要求渠道连接器已配置为 ready。
- job 使用 `tenant_id + idempotency_key` 唯一约束，重复创建返回 409。
- `POST /api/tenants/{tenant_id}/outbox-delivery-queue-runs` 按优先级和 `next_run_at` 扫描 due job，并按 `rate_limit_per_minute` 截断处理数量。
- runner 处理前写入 `locked_by` 和 `locked_at`，处理后清空锁字段并写入最终状态。
- 每次队列处理都会创建 `delivery_queue` 类型的 `outbox_send_attempt`，但 `external_write=false`、`sent_at=null`、`external_message_id=""`。
- `OUTBOX_EXTERNAL_WRITE_ENABLED=false` 是默认全局 kill switch；请求外部写时会被标记为 `external_write_kill_switch`，并创建 `permission_denied` 失败复盘项。
- 渠道 inactive 会先进入 `retry_scheduled`，达到最大尝试次数后进入 `dead_letter`，并创建合成回执和失败复盘项。
- 前端展示最近队列运行的处理数、成功、阻断、重试、死信和外部写状态。

当前仍不是完整生产发送系统：

- runner 仍是 HTTP 触发，不是独立 Redis/RQ/Celery/Arq 后台消费者。
- 当前锁是数据库字段骨架，不是 `SELECT FOR UPDATE SKIP LOCKED` 或 Redis 分布式锁。
- 没有真实官方 sender adapter，没有 access token、平台消息 ID 回填、平台回执验签闭环。
- 队列失败复盘已覆盖发送 job，但模型调用失败、RAG 失败和入站 worker 异常还没有统一进入同一复盘中心。
- kill switch 默认关闭外部写是硬边界；打开前必须完成真实平台授权、测试账号、回调域名、验签/解密、限流、告警和回滚方案。

## P2-18/P2-18B/P2-18C/P2-18D/P2-18E/P2-18F/P2-18G/P2-18H RAG v1 与文档级知识工程

P2-18 第一片解决的是“知识库不再只有结构化 FAQ 卡片，而是能导入一份文档、生成 chunk index、按 chunk 检索并把引用证据写入 workflow”。P2-18B 第一片把这条能力接入前端“知识文档运营”面板，让管理员能从工作台导入纯文本知识文档，坐席能查看已索引文档、预览 chunk、运行文档片段检索并检查引用来源。P2-18C 第一片补上知识评测集和检索质量统计，让运营侧可以重复跑一组问题，查看命中率、引用覆盖、期望词覆盖和需复盘题目。P2-18D 第一片把评测集创建、运行和报表接入前端运营台，形成“导入文档 -> 检索片段 -> 建题集 -> 跑质量报表 -> 复盘缺口”的闭环雏形。P2-18E 第一片把 chunk 的 embedding 从“签名占位”推进到可存储、可配置、可审计的后端边界：默认 deterministic 本地 embedding，portable JSON vector 存储，OpenAI-compatible embedding provider 显式配置时 fail-closed，PostgreSQL 下启用 pgvector extension 边界，并用轻量 lexical reranker 合并 BM25 与向量相似度。P2-18G 第一片把 pgvector 从“只启用扩展”推进到可运行 exact query path：PostgreSQL 下有原生 `vector` 列、scope index、向量索引重建 API、显式 pgvector 非 PostgreSQL fail-closed 和真实 PostgreSQL smoke。P2-18F 第一片补上 embedding provider smoke 和成本/延迟账本：owner/admin 可触发 deterministic 或显式允许的 OpenAI-compatible provider smoke，系统记录 provider、model、输入 hash、估算 tokens、耗时、估算成本、币种和 usage 摘要，不保存 sample 原文。P2-18H 第一片补上 pgvector ANN 策略计划：owner/admin 可生成 exact/HNSW/IVFFlat 选择、表达式部分索引 DDL、rollback、query options、预计构建窗口、内存估算和安全检查；默认 dry-run，不执行真实 `CREATE INDEX`。P2-18H 第二片补上 HNSW/IVFFlat 真实建索引 smoke：用本地 PostgreSQL/pgvector 创建独立临时 smoke 表，真实构建 ANN 索引，比较 exact scan 和 ANN top-k 的 `recall_at_k`、构建耗时、查询耗时和 planner 结果，然后默认清理表。它仍不等于完整 RAG，因为当前没有在生产知识表执行 HNSW/IVFFlat 建索引、没有把应用查询切到 ANN、没有神经重排器、文档解析器、批量文件上传、真实客户 50-100 题评测集和生成答案事实性评估。

新增文件与改动：

| 文件 | 作用 |
| --- | --- |
| `backend/app/migrations/versions/0009_knowledge_documents.py` | 新增 `knowledge_documents` 与 `knowledge_document_chunks` |
| `backend/app/models/foundation.py` | 新增 `KnowledgeDocument` 与 `KnowledgeDocumentChunk` |
| `backend/app/services/knowledge.py` | 新增文档导入、自动分块、deterministic 本地 embedding、portable JSON vector、OpenAI-compatible embedding provider 边界、BM25+vector+reranker 文档片段检索 |
| `backend/app/api/knowledge.py` | 新增文档导入、文档列表、chunk 列表和文档片段检索 API |
| `backend/app/schemas/knowledge.py` | 新增文档、chunk、文档检索输入输出合同 |
| `backend/app/schemas/reply_orchestrator.py` | 新增 `document_rag` 模式与 chunk 级 citation 字段 |
| `backend/app/services/reply_orchestrator.py` | 新增 `document_rag` 编排路径 |
| `backend/tests/test_knowledge_documents_api.py` | 覆盖文档导入、分块、chunk 引用检索和坐席只读边界 |
| `scripts/check_stage2_knowledge_documents.py` | P2-18 文件与关键合同自检 |
| `frontend/src/api/client.ts` | P2-18B 新增知识文档列表、导入、chunk 列表和文档片段检索 API client；P2-18D 新增评测集列表、创建和运行 API client |
| `frontend/src/App.tsx` | P2-18B 新增“知识文档运营”面板；P2-18D 新增“知识评测与质量”面板 |
| `frontend/src/styles.css` | P2-18B 新增知识文档表单、文档列表、检索结果和引用展示样式；P2-18D 新增评测表单、指标卡和逐题结果样式 |
| `scripts/check_stage2_knowledge_document_frontend.py` | P2-18B 前端文件与关键文案自检 |
| `backend/app/migrations/versions/0010_knowledge_evaluations.py` | P2-18C 新增知识评测集、题目、运行记录和逐题结果表 |
| `backend/tests/test_knowledge_evaluations_api.py` | P2-18C 覆盖评测集创建、运行报告、无 token 和坐席权限边界 |
| `scripts/check_stage2_knowledge_evaluations.py` | P2-18C 知识评测集和检索质量统计关键合同自检 |
| `scripts/check_stage2_knowledge_evaluation_frontend.py` | P2-18D 前端评测运营台文件、API client、关键文案和样式自检 |
| `backend/app/migrations/versions/0011_knowledge_embedding_index.py` | P2-18E 新增 chunk embedding vector、provider、model、dimension、vector store 和 index status 元数据，并在 PostgreSQL 下启用 `vector` extension |
| `scripts/check_stage2_knowledge_embedding_index.py` | P2-18E embedding index、provider fail-closed、vector store 和 reranker 文件/关键合同自检 |
| `backend/app/migrations/versions/0012_knowledge_pgvector_query_path.py` | P2-18G PostgreSQL 下新增 `embedding_pgvector vector` 原生列和 pgvector scope index，SQLite 下 no-op |
| `backend/tests/test_knowledge_vector_index_api.py` | P2-18G 覆盖向量索引重建、坐席权限、显式 pgvector 非 PostgreSQL fail-closed 和 pgvector SQL 过滤合同 |
| `scripts/check_stage2_knowledge_pgvector.py` | P2-18G pgvector query path、rebuild API、迁移、测试和前端 client 合同自检 |
| `backend/app/migrations/versions/0013_knowledge_embedding_provider_smoke.py` | P2-18F 新增 `knowledge_embedding_provider_smoke_runs` 表，保存 provider smoke 的成本/延迟/质量检查摘要 |
| `backend/tests/test_knowledge_embedding_provider_smoke_api.py` | P2-18F 覆盖 deterministic smoke、坐席权限、外部 provider 显式允许门禁和 mock OpenAI-compatible 成本记录 |
| `scripts/check_stage2_knowledge_embedding_provider_smoke.py` | P2-18F embedding provider smoke、成本记录、API、迁移和测试合同自检 |
| `backend/app/migrations/versions/0014_knowledge_vector_index_plans.py` | P2-18H 新增 `knowledge_vector_index_plans`，保存 ANN 策略计划、DDL、rollback、query options、安全检查和 dry-run 边界 |
| `backend/tests/test_knowledge_vector_index_strategy_api.py` | P2-18H 覆盖策略计划 API、坐席权限、非 PostgreSQL blocked dry-run 和 HNSW/IVFFlat DDL 合同 |
| `scripts/check_stage2_knowledge_vector_index_strategy.py` | P2-18H 向量索引策略计划、迁移、API、service、测试和 dry-run 边界自检 |
| `scripts/smoke_pgvector_ann_indexes.py` | P2-18H 第二片本地 ANN smoke：独立表真实构建 HNSW/IVFFlat，记录 exact vs ANN recall、构建耗时、查询耗时和 planner 命中，默认清理临时表 |
| `scripts/check_stage2_pgvector_ann_smoke.py` | P2-18H 第二片脚本和文档边界自检，确认没有外部模型调用、没有切换应用查询路径 |
| `scripts/smoke_bailian_chat_model.py` | P2-20 第一片真实百炼聊天模型 smoke 安全入口；默认不外呼，需 `--allow-external-call` 且配置 `BAILIAN_API_KEY` |
| `backend/tests/test_bailian_chat_smoke_script.py` | P2-20 覆盖未显式允许不外呼、缺 key 不外呼、有 key 且允许才调用，并检查输出不包含 key 或 sample 原文 |
| `scripts/check_stage2_bailian_chat_smoke.py` | P2-20 smoke 脚本、测试、README 和本阶段文档合同自检 |
| `scripts/evaluate_bailian_chat_quality.py` | P2-21 真实百炼聊天模型脱敏合成题集质量评测入口；默认不外呼，需 `--allow-external-call` 且配置 `BAILIAN_API_KEY` |
| `backend/tests/test_bailian_chat_quality_eval_script.py` | P2-21 覆盖未显式允许不外呼、缺 key 不外呼、有 key 且允许才按 limit 调用，并检查输出不包含 key 或问题原文 |
| `scripts/check_stage2_bailian_chat_quality_eval.py` | P2-21 质量评测脚本、测试、README 和本阶段文档合同自检 |
| `backend/app/migrations/versions/0015_customer_service_evaluation_fields.py` | P2-22 新增客服商用验收题字段：问题类型、期望 chunk、多证据、人审预期、自动回复门禁、禁用词和风险等级 |
| `backend/tests/test_knowledge_evaluations_api.py` | P2-22 覆盖 `customer_service_retrieval`、多证据召回、人工审核门禁、禁用词和商用评测指标 |
| `scripts/check_stage2_customer_service_evaluation.py` | P2-22 客服知识检索评测字段、指标、迁移、测试和文档合同自检 |
| `backend/app/migrations/versions/0016_customer_service_evaluation_import_metadata.py` | P2-22B 新增客服题库导入元数据字段：外部题号、来源渠道、业务分类和标注备注 |
| `scripts/import_customer_service_eval_bank.py` | P2-22B 脱敏客户题库 CSV/JSON 导入脚本；默认 dry-run、隐私拦截、不打印原始问题，可显式调用后端 API 创建评测集 |
| `evals/customer_service_eval_bank_template.csv` | P2-22B 客服脱敏题库导入模板 |
| `evals/customer_service_eval_bank_synthetic_80_2026-06-26.csv` | P2-23 合成脱敏客户客服验收题库，80 条，覆盖 8 个渠道、10 类业务和高风险/人审/知识缺口边界 |
| `docs/P2-23_SYNTHETIC_CUSTOMER_SERVICE_EVAL_BANK.md` | P2-23 题库说明，记录定位、覆盖范围、dry-run 用法和不能冒充真实客户数据的边界 |
| `backend/tests/test_customer_service_eval_bank_import_script.py` | P2-23 覆盖 CSV dry-run payload 构建、原始问题不进摘要、高置信 PII 默认阻断，以及 80 条合成脱敏题库 fixture 校验 |
| `evals/p2_24_seed_knowledge_documents.json` | P2-24 合成 seed 知识文档，承接 P2-23 80 题中的 9 个主要来源 URI |
| `scripts/run_p2_24_synthetic_eval_smoke.py` | P2-24 本地闭环 smoke：导入 seed 文档、创建 80 题评测集、运行检索评测、导出脱敏报告 |
| `backend/tests/test_p2_24_synthetic_eval_smoke_script.py` | P2-24 smoke 测试，验证无外部模型调用、无外部平台写入、无原始问题摘要和禁用词命中为 0 |
| `docs/P2-24_SYNTHETIC_EVAL_SMOKE.md` | P2-24 smoke 说明，记录运行命令、输出路径、核心指标、当前不足和下一步 |
| `scripts/run_p2_25_chunk_backfill_eval_comparison.py` | P2-25 chunk id 回填评测对比脚本：先跑原始题库基线，再读取真实文档 chunk id 回填 expected_chunk_ids，并导出对比结果 |
| `backend/tests/test_p2_25_chunk_backfill_eval_comparison_script.py` | P2-25 测试，验证 full_evidence_cases 从 0 变为可计算样本，并确认无外部模型/平台动作、无原始问题摘要 |
| `docs/P2-25_CHUNK_BACKFILL_EVAL_COMPARISON.md` | P2-25 说明，记录回填逻辑、输出产物、指标解释和下一步 |
| `output/evals/p2_25_chunk_backfill_eval_comparison/` | P2-25 本地输出目录，包含 summary JSON、对比 Markdown、case binding CSV 和回填版脱敏评测报告 |
| `scripts/run_p2_26_retrieval_quality_comparison.py` | P2-26 检索 top-k 参数对比脚本：复用 P2-25 回填题库，比较 5/8/10/12 的召回、引用精度、安全噪音和失败题变化 |
| `backend/tests/test_p2_26_retrieval_quality_comparison_script.py` | P2-26 测试，验证 top-k 对比无外部模型/平台动作、无原始问题摘要，并生成失败题 delta |
| `docs/P2-26_RETRIEVAL_QUALITY_COMPARISON.md` | P2-26 说明，记录运行命令、指标、默认 top-k 推荐、召回池建议和下一步 |
| `output/evals/p2_26_retrieval_quality_comparison/` | P2-26 本地输出目录，包含 summary JSON、对比 Markdown、失败题 delta CSV 和推荐 top-k=8 的脱敏评测报告 |
| `scripts/export_customer_service_eval_report.py` | P2-22C 客服评测运行 CSV/Markdown 导出脚本；默认只导出 question hash 和指标，不导出原始问题 |
| `backend/tests/test_customer_service_eval_report_export_script.py` | P2-22C 覆盖默认脱敏导出、知识缺口/人审字段和显式原文导出开关 |
| `frontend/src/api/client.ts` | P2-22F 新增评测运行历史、运行详情和脱敏报告导出 API client |
| `frontend/src/App.tsx` | P2-22F 在“知识评测与质量”面板展示最近运行历史、载入运行详情，并支持下载脱敏 Markdown/CSV 报告 |
| `frontend/src/styles.css` | P2-22F 新增评测运行历史行、当前运行头部和报告下载动作样式 |

新增 API：

| 接口 | 作用 |
| --- | --- |
| `POST /api/tenants/{tenant_id}/knowledge-documents` | 导入纯文本知识文档，自动生成 chunk |
| `GET /api/tenants/{tenant_id}/knowledge-documents` | 查看租户文档列表 |
| `GET /api/knowledge-documents/{document_id}/chunks` | 查看文档 chunk 与 citation |
| `POST /api/tenants/{tenant_id}/knowledge-document-searches` | 执行文档片段检索，返回 chunk 级可溯源证据 |
| `POST /api/tenants/{tenant_id}/knowledge-evaluation-sets` | 创建知识检索评测集和题目 |
| `GET /api/tenants/{tenant_id}/knowledge-evaluation-sets` | 查看租户知识评测集 |
| `POST /api/knowledge-evaluation-sets/{evaluation_set_id}/runs` | 运行文档检索评测并返回质量统计 |
| `GET /api/knowledge-evaluation-sets/{evaluation_set_id}/runs` | 查看某个评测集的历史运行摘要，owner/admin 可用 |
| `GET /api/knowledge-evaluation-runs/{evaluation_run_id}` | 读取已落库评测运行详情，owner/admin 可用 |
| `GET /api/knowledge-evaluation-runs/{evaluation_run_id}/report` | 导出已落库运行的脱敏 Markdown 或 CSV 报告，owner/admin 可用 |
| `POST /api/tenants/{tenant_id}/knowledge-vector-index/rebuilds` | 重建租户或指定文档的 chunk embedding/vector index，owner/admin 可用 |
| `POST /api/tenants/{tenant_id}/knowledge-vector-index/plans` | 创建 exact/HNSW/IVFFlat 向量索引策略计划，默认 dry-run，不执行真实建索引 |
| `POST /api/tenants/{tenant_id}/knowledge-embedding-provider-smoke-runs` | 运行 embedding provider smoke，记录 hash、tokens、耗时、估算成本和质量检查，不回显原文 |

当前行为：

- `owner/admin` 可以导入文档；坐席可以检索但不能导入。
- `owner/admin` 可以创建和运行知识评测集；坐席不能直接创建或运行评测。
- 导入时保存文档 `content_hash`、`chunk_count`、`ingestion_status=indexed`，并写 `knowledge_document.imported` 审计事件。
- chunk 保存 `chunk_index`、`section_title`、`char_start`、`char_end`、`token_count`、`source_uri`、`embedding_signature`、`embedding_vector`、`embedding_provider`、`embedding_model`、`embedding_dimension`、`vector_store` 和 `vector_index_status`。
- 文档检索返回 `retrieval_mode=hybrid_bm25_vector_rerank_v1`、`vector_engine`、`vector_store`、`retrieval_backend`、`vector_index_status`、`embedding_provider`、`embedding_model`、`reranker`、BM25 分、向量分和 reranker 分。
- 默认检索后端是 `python_json_vector_scan`；显式 `KNOWLEDGE_VECTOR_STORE=postgres_pgvector_store_v1` 且数据库为 PostgreSQL 时，检索后端为 `postgres_pgvector_exact_cosine_v1`。
- 显式 pgvector 但数据库不是 PostgreSQL 时，导入、检索和重建索引会返回 503，不静默 fallback 到 JSON vector。
- 默认 `KNOWLEDGE_EMBEDDING_PROVIDER=deterministic_local`，不会调用真实外部 embedding API；显式配置 `openai_compatible` 且缺少 API key/base 时，导入和检索会返回 503，不会静默 fallback。
- provider smoke 由 `POST /api/tenants/{tenant_id}/knowledge-embedding-provider-smoke-runs` 触发；deterministic provider 不外呼，OpenAI-compatible provider 必须请求体显式传 `allow_external_call=true`，否则返回 409。
- `knowledge_embedding_provider_smoke_runs` 只保存 sample 的 hash、字符数、估算 tokens、耗时、估算成本、币种、provider usage 摘要和质量检查，不保存 sample 原文、不保存 API key。
- 向量索引策略计划由 `POST /api/tenants/{tenant_id}/knowledge-vector-index/plans` 触发；默认 `dry_run=true`，只保存策略选择、DDL、rollback、query options、安全检查和预计窗口，不执行真实建索引。
- 显式 `postgres_pgvector_store_v1` 但数据库不是 PostgreSQL 时，策略计划会记录 `blocked_non_postgresql`，不会静默执行或伪装成可用 ANN。
- P2-18H 第二片的 `scripts/smoke_pgvector_ann_indexes.py` 只用于本地 PostgreSQL/pgvector 能力验证：默认连接本地 Docker compose 数据库，创建独立 smoke 表，执行 HNSW/IVFFlat 真实建索引 smoke，输出 `external_model_call_performed=false`、`application_query_path_changed=false`、exact/ANN top-k、`recall_at_k`、构建耗时和查询耗时，最后默认清理表。
- 评测运行保存命中率、引用覆盖率、期望词覆盖率、平均置信度、需复盘题数和逐题结果。
- 评测运行历史列表只返回运行摘要，不返回逐题结果或问题原文；需要人工复盘时再读取详情或导出脱敏报告。
- 评测运行脱敏报告接口只输出 `question_hash`、来源元数据和指标，不支持原文导出；原文复核仍使用 P2-22C 脚本显式内部开关，不能作为普通前端能力。
- P2-18D 前端评测面板可创建评测集、运行评测、展示命中率、引用覆盖、期望词覆盖、需复盘题数、检索模式、向量引擎和逐题失败原因。
- P2-18C/P2-18D 只评测“检索是否命中正确文档片段”和“引用/期望词是否覆盖”，不生成自由文本答案；因此 `unsupported_answer_rate=null` 是明确边界，不代表已经完成幻觉率评估。
- ReplyOrchestrator 支持 `mode=document_rag`，会把 `source_kind=document_chunk`、`document_id`、`chunk_id`、`chunk_index` 和 citation 写入 workflow state。
- 前端知识文档运营面板会在正式 token 登录后读取 active 文档，owner/admin 可导入纯文本知识文档，所有已登录用户可运行文档片段检索并查看引用来源。
- 前端知识评测面板会在正式 token 登录后读取 active 评测集；owner/admin 可创建和运行评测、查看最近运行历史、载入详情并下载脱敏 Markdown/CSV 报告，演示身份无 token 时只预览面板。
- 开发演示身份无 token 时只用于页面预览，不会真正调用受保护的文档导入或检索接口。

当前仍不是完整 RAG：

- pgvector 当前已具备 exact cosine 查询路径、HNSW/IVFFlat dry-run 策略计划和本地独立表 HNSW/IVFFlat 真实建索引 smoke；还没有在 `knowledge_document_chunks` 生产路径执行 ANN 建索引，也没有把应用查询切到 ANN；当前 pytest 和默认运行使用 portable JSON vector。
- 还没有通过真实题库评测的语义 embedding provider；OpenAI-compatible provider 现在已有 smoke 与成本/延迟账本，但这只证明 provider 可调用和可观测，不证明召回质量。
- 还没有神经重排器、引用答案生成器、文档解析器和文件上传。
- 没有真实客户 50-100 条标准评测集；当前只有评测集能力和自动化测试样例。
- 没有生成答案评测链路，尚不能计算真实胡编率/幻觉率。
- `document_rag` 目前使用最高分 chunk 直接生成可溯源草稿，未调用真实模型综合多片段。
- 前端当前没有文件上传、版本审核、批量导入、知识失效策略、真实客户题库导入或生成答案事实性评估。

## 安全边界

- 所有 workflow 和 human review API 当前都要求有效 Bearer token。
- 跨租户访问返回 404，不暴露资源是否存在。
- 审核通过或拒绝会写入审计事件。
- ReplyOrchestrator 只接受入站消息；出站消息再次触发编排会返回 409。
- 知识卡片写入需要 `owner/admin`，坐席仅能检索，不能直接改正式知识。
- 坐席审核收件箱只返回同租户任务，跨租户访问返回 404。
- 审核通过只是内部记录最终回复；outbox 确认只是进入 `ready_to_send`；dry-run send attempt 和 worker dry-run 都只是记录发送前检查，不代表已经完成外部发送。
- 官方渠道 webhook 入口不使用坐席 Bearer token，但必须匹配 provider 和已配置连接器；未验签 payload 只允许落成未可信收据。
- P2-15 fixture 验签通过也只说明“签名算法边界可用”；只有内容、联系人身份和幂等键都齐备时才会创建可信 `messages`。入站 worker 只触发内部编排和人工审核，不会自动外发。
- P2-16 失败复盘只记录内部运营判断，不会自动重发或打开外部写入。
- P2-17 发送队列只记录内部 job、锁、尝试、重试和死信；即使请求外部写，默认也会被 `OUTBOX_EXTERNAL_WRITE_ENABLED=false` 阻断。
- P2-18G/P2-18H 默认 deterministic 本地 embedding 和 JSON vector 只是可测试工程边界；显式 `postgres_pgvector_store_v1` 需要 PostgreSQL + pgvector，非 PostgreSQL 环境真实导入/检索/重建会 fail-closed，策略计划只允许记录 blocked dry-run；不得对外宣称已启用生产级 HNSW/IVFFlat ANN、Milvus/Qdrant 或真实语义 embedding 质量验收。
- P2-18E 显式外部 embedding provider 缺 key/base 必须 fail-closed，不能静默 fallback 到本地 provider 后再对外说“真实 embedding 已可用”。
- P2-18F 外部 embedding provider smoke 必须显式传 `allow_external_call=true`；响应和审计只记录 hash、usage、成本和质量摘要，不保存 sample 原文、API key 或完整 provider 响应正文。
- P2-18B 前端导入入口只允许正式 token 下调用后端接口；真正的写权限仍以后端 owner/admin 校验为准，不能用前端按钮禁用替代权限控制。
- P2-18C 评测集当前只统计检索质量，不生成模型答案；不得把 `unsupported_answer_rate=null` 解读成“幻觉率为 0”。
- P2-18D 前端评测报表只是后端检索评测的运营入口，不能替代人工标注题库、生成答案事实性评估或真实客户试运行数据。
- 本阶段不保存客户真实隐私数据；默认不调用真实外部模型，只有显式选择 provider 且配置 Key 时才会调用；不执行真实渠道外发。

## 当前验收命令

```bash
python3 standard_ops/scripts/check_stage2_workflow.py
python3 standard_ops/scripts/check_stage2_orchestrator.py
python3 standard_ops/scripts/check_stage2_knowledge.py
python3 standard_ops/scripts/check_stage2_outbox.py
python3 standard_ops/scripts/check_stage2_send_attempts.py
python3 standard_ops/scripts/check_stage2_channel_connectors.py
python3 standard_ops/scripts/check_stage2_channel_webhooks.py
python3 standard_ops/scripts/check_stage2_trusted_inbound_worker.py
python3 standard_ops/scripts/check_stage2_delivery_failures.py
python3 standard_ops/scripts/check_stage2_outbox_delivery_queue.py
python3 standard_ops/scripts/check_stage2_knowledge_documents.py
python3 standard_ops/scripts/check_stage2_knowledge_embedding_index.py
python3 standard_ops/scripts/check_stage2_knowledge_embedding_provider_smoke.py
python3 standard_ops/scripts/check_stage2_knowledge_pgvector.py
python3 standard_ops/scripts/check_stage2_knowledge_vector_index_strategy.py
python3 standard_ops/scripts/check_stage2_pgvector_ann_smoke.py
python3 standard_ops/scripts/check_stage2_model_routing.py
python3 standard_ops/scripts/check_stage2_customer_service_evaluation.py
python3 standard_ops/scripts/check_stage2_bailian_chat_smoke.py
python3 standard_ops/scripts/check_stage2_knowledge_document_frontend.py
python3 standard_ops/scripts/check_stage2_knowledge_evaluations.py
python3 standard_ops/scripts/check_stage2_knowledge_evaluation_frontend.py
python3 standard_ops/scripts/check_stage2_frontend_ops.py
python3 standard_ops/scripts/check_stage2_outbox_worker.py
cd standard_ops/backend
. .venv/bin/activate
pytest tests/test_workflows_api.py
pytest tests/test_reply_orchestrator_api.py
pytest tests/test_knowledge_api.py
pytest tests/test_outbox_api.py
pytest tests/test_channel_connectors_api.py
pytest tests/test_channel_webhooks_api.py
pytest tests/test_trusted_inbound_worker_api.py
pytest tests/test_delivery_failure_reviews_api.py
pytest tests/test_outbox_delivery_queue_api.py
pytest tests/test_knowledge_documents_api.py
pytest tests/test_knowledge_evaluations_api.py
pytest tests/test_knowledge_vector_index_api.py
pytest tests/test_knowledge_vector_index_strategy_api.py
pytest tests/test_knowledge_embedding_provider_smoke_api.py
pytest
```

## 下一步

下一片建议继续 P2-27：基于 `output/evals/p2_26_retrieval_quality_comparison/p2_26_failed_case_delta.csv` 的 18 道 still_missing case，区分 seed 文档太薄、chunk 粒度不合理、同源排序不足、词法召回噪音、风险证据干扰和标注需要复核；然后做“知识文档修订前后”和“reranker 规则前后”的运行对比。当前生产默认建议先用 `top_k=8`，`top_k=12` 只作为召回池实验，不直接塞进模型上下文。只有 `full_evidence_recall_at_k`、`citation_precision`、`expected_term_coverage` 和 `forbidden_term_hits` 达到更稳状态后，再进入 `rag_model_assisted` 的生成答案事实性复核。后续也可以在用户明确允许后，用真实百炼/千问或其他 OpenAI-compatible embedding Key 做一次受控 provider smoke，并把结果同回填版题库检索质量关联；或者把 P2-18H 从独立 smoke 表推进到 `knowledge_document_chunks` 受控 ANN 建索引执行、exact vs ANN 召回对比、query path 切换实验、神经 reranker、导入审核流或真实客户题库导入。若按真实试点需要进入 `P2-18A 企业微信/官网客服官方闭环前置`，仍不直接打开真实外发：

```text
入站消息
  -> 创建 workflow run
  -> classify_intent
  -> 调用 knowledge_search
  -> 调用 model_gateway
  -> risk_check
  -> 人工审核任务进入坐席队列
  -> 坐席批准/改写/拒绝草稿
  -> 记录最终回复结果
  -> 创建待发送 outbox 草稿
  -> 人工确认后再进入渠道发送器
  -> 记录 dry-run 发送尝试，仍不触发真实平台外发
  -> 前端待发送队列可见
  -> worker 批量处理 dry-run、失败状态、重试占位和回执占位
  -> 按渠道类型选择官方 connector，占位实现仍不外发
  -> 已建立 provider registry 和 webhook 占位入口
  -> 已建立 P2-13 官方签名 fixture 和密钥存储边界
  -> 已补 P2-14 可信入站消息创建和轻量幂等去重
  -> 已补 P2-15 可信入站 worker、ReplyOrchestrator 触发和人工审核入口
  -> 已补 P2-16 平台回执归一化和失败复盘队列
  -> 已补 P2-17 发送队列 job、锁字段、限流、重试、死信和 kill switch 骨架
  -> 已补 P2-18 第一片：文档导入、分块、chunk 引用溯源和 document_rag 编排模式
  -> 已补 P2-18B 第一片：前端知识文档运营、导入表单、文档片段检索和引用展示
  -> 已补 P2-18C 第一片：知识评测集、文档检索质量统计和逐题复盘结果
  -> 已补 P2-18D 第一片：前端知识评测与质量面板、题集创建、运行评测和逐题结果展示
  -> 已补 P2-18E 第一片：chunk embedding 元数据、portable JSON vector、OpenAI-compatible provider fail-closed、pgvector extension 迁移边界和 lexical reranker
  -> 已补 P2-18G 第一片：PostgreSQL/pgvector 原生列、exact cosine 查询路径、向量索引重建 API、显式 pgvector 非 PostgreSQL fail-closed 和真实 PostgreSQL smoke
  -> 已补 P2-18F 第一片：embedding provider smoke API、成本/延迟估算记录、外部 provider 显式允许门禁和不回显原文边界
  -> 已补 P2-18H 第一片：pgvector HNSW/IVFFlat dry-run 策略计划、DDL、rollback、query options、构建窗口估算和安全检查
  -> 已补 P2-18H 第二片：本地独立 smoke 表 HNSW/IVFFlat 真实建索引 smoke，external_model_call_performed=false，没有切换应用查询路径
  -> 已补 P2-19 第一片：模型路由策略，按意图/风险/置信度/知识命中选择 simple_fast、standard_support、premium_guarded 或 deterministic_safe_fallback
  -> 已补 P2-20 第一片：真实百炼聊天模型单问 smoke 安全入口，显式 allow 才外呼
  -> 已补 P2-21 第一片：真实百炼聊天模型脱敏合成题集质量评测入口，记录 usage、latency、期望词和禁用词指标
  -> 已补 P2-25 第一片：chunk id 动态回填评测对比，让 full_evidence_recall_at_5 从不可解释变成可审计指标
  -> 已补 P2-26 第一片：检索 top-k 参数对比，默认建议 top_k=8，top_k=12 只作为召回池或重排实验候选
  -> 下一步做 P2-27 still_missing 失败题分桶、seed 文档修订、reranker 规则实验、客户 50-100 题脱敏评测、受控真实 embedding provider smoke、生产知识表 ANN 建索引执行实验、query path 切换实验、神经 reranker、导入审核流或真实客户题库
```

如果优先做渠道闭环，则先做真实平台授权材料、测试账号、回调域名、企业微信/官网客服消息解密、access token 管理、发送 adapter dry-run contract 和回滚方案；真实外发必须等这些前置验收通过后，再单独打开受控试点开关。
