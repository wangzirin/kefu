# P3-06U-26H2W7B 模型调用成本台账与预算门禁第一片

阶段代号：H2W-7B

日期：2026-07-04

## 1. 定位

本片接续 H2W-7X 的回复事实账本，把客服回复中的模型调用从“可见缺口”推进为可落账、可预算拦截、可降级、可审计的第一版能力。

它不是完整 FinOps 系统，也不是供应商账单对账系统。当前价格来自本地运维配置，用于预算门禁和试点估算，不等于阿里云百炼、DeepSeek 或其他供应商最终账单。

## 2. 已完成

1. 新增模型预算配置。
   - `MODEL_BUDGET_GUARD_ENABLED`
   - `MODEL_BUDGET_DAILY_LIMIT_CNY`
   - `MODEL_BUDGET_MONTHLY_LIMIT_CNY`
   - `MODEL_BUDGET_SINGLE_CALL_LIMIT_CNY`
   - `MODEL_BUDGET_PRICING_SOURCE`
   - `MODEL_BUDGET_PRICE_TABLE_VERSION`
   - `MODEL_PRICE_BAILIAN_*_PER_1K_UNITS`
   - `MODEL_PRICE_DEEPSEEK_PER_1K_UNITS`

2. 新增成本估算与预算判断服务。
   - 文件：`backend/app/services/model_budget.py`
   - 能力：按 provider、model、route、复杂度、输入/输出单位估算费用。
   - 能力：按单次、每日、每月预算判断是否允许外部模型调用。
   - 能力：输出 `budget_policy_snapshot`，保存预算、已花费、预计调用成本和价格版本。

3. 回复编排器接入预算门禁。
   - 显式 provider 超预算时返回 `budget_blocked`，显式 provider 不静默 fallback。
   - 自动路由超预算时降级到确定性知识草稿，状态为 `degraded`。
   - 降级或拦截都会进入人工复核，原因统一为 `model_budget_limited`。

4. 成本台账写入 `model_call_records`。
   - 记录 provider、model、route、复杂度、状态、字符/单位、估算成本、价格来源、预算快照和降级动作。
   - 被预算拦截时，实际 `estimated_cost` 记为 `0`，外部模型预计费用只保存在 `budget_policy_snapshot.estimated_call_cost`。
   - 自动降级到确定性草稿时，实际 `estimated_cost` 记为 `0`，避免污染日/月预算累计。

5. RAG/成本治理摘要新增预算门禁可见性。
   - 新增 `model_budget_policy` 门禁。
   - `model_policy` 返回预算开关、单次/每日/每月限额、价格来源和价格版本。

## 3. 当前运行口径

| 场景 | 当前行为 | 是否外部模型调用 |
|---|---|---|
| 明确指定百炼且预算充足 | 按模型网关正常请求，结果写入成本台账 | 取决于 API key 和调用结果 |
| 明确指定百炼但单次预算超限 | 返回 `budget_blocked`，进入人工复核 | 否 |
| 自动路由选择百炼但预算超限 | 降级确定性知识草稿，返回 `degraded`，进入人工复核 | 否 |
| 确定性模型 | 成本为 `0`，价格来源为 `deterministic_no_external_cost` | 否 |
| 无 API key | 仍按 `unavailable` 处理，不伪装成功 | 否 |

## 4. 停止门禁

1. 没有持久成本台账，却展示“模型成本治理完成”，停止。
2. 显式 provider 被预算或调用失败拦截后静默 fallback，停止。
3. 预算不足仍返回自动完成或伪成功回答，停止。
4. 被预算拦截的外部模型预计费用写进真实累计成本，停止。
5. 没有价格来源和价格版本，却展示具体金额，停止。
6. 真实外发、真实渠道发送或 RPA 外挂能力被本片打开，停止。

## 5. 尚未完成

1. 供应商真实账单对账。
2. 按渠道、店铺、客户、租户的细颗粒预算。
3. 前端模型成本台账详情页。
4. 高并发下的限流、熔断、队列级预算抢占。
5. 50-100 条真实脱敏题库下的成本、延迟、质量综合 rehearsal。
6. 生产级 pgvector/rerank 与最终答案事实性评测，这些属于 H2W-7C/7D 后续阶段。

## 6. 验收命令

```bash
cd /Users/ericlee/Desktop/01_项目工作区/肥肥lu/lite_a_customer_service/standard_ops
backend/.venv/bin/python -m pytest backend/tests/test_reply_orchestrator_api.py backend/tests/test_rag_cost_governance_api.py backend/tests/test_model_routing_policy.py -q
backend/.venv/bin/python -m py_compile backend/app/services/model_budget.py backend/app/services/model_gateway.py backend/app/services/reply_orchestrator.py backend/app/services/reply_provenance.py backend/app/services/rag_governance.py backend/app/core/config.py backend/app/schemas/reply_orchestrator.py backend/app/schemas/rag_governance.py
python3 scripts/check_p3_06u_26h2w7b_model_cost_budget_gate.py
python3 scripts/check_p3_06u_26h2w7x_reply_provenance.py
python3 scripts/check_p3_06u_26h2w7_rag_cost_governance.py
cd frontend && npm run typecheck && npm run build
```

## 7. 真实边界

- 真实外发继续关闭。
- RPA 不进入正式默认交付链。
- 本片不保存原始完整客户聊天原文到成本台账。
- 本片不把本地配置价格写成供应商真实账单。
- 本片不代表全平台官方渠道已经接通。
