# P3-06U-26H2W7 生产级 RAG 与模型成本治理第一片

## 1. 定位

本片把“生产级 RAG 与模型成本治理”的第一层门禁落到真实后端和前端页面：系统可以读取当前知识库、分块索引、评测、Embedding provider smoke、自动回复策略和近期回复决策，生成一份只读治理摘要。

这不是完整生产级 RAG 完成态，也不是完整模型成本报表。它用于判断当前系统距离生产级检索、引用溯源、模型预算和降级策略还有哪些明确缺口。

## 2. 已完成

1. 新增后端只读接口：
   - `GET /api/tenants/{tenant_id}/rag-cost-governance-summary`
   - 权限：`ops.metrics.read`
   - 返回 schema：`p3-06u-26h2w7.rag_cost_governance_summary.v1`

2. 新增后端服务：
   - `backend/app/services/rag_governance.py`
   - 汇总知识卡、业务对象、对象问答、启用文档、已索引片段、评测集、启用评测题、回复决策。
   - 汇总当前 embedding provider、embedding model、vector store、reranker。
   - 读取最近一次知识评测运行。
   - 读取最近一次 embedding provider smoke。
   - 读取当前租户自动回复策略。
   - 检查近期回复决策中是否已有模型调用成本记录。

3. 新增后端 schema：
   - `backend/app/schemas/rag_governance.py`

4. 新增后端测试：
   - `backend/tests/test_rag_cost_governance_api.py`
   - 覆盖负责人可读、坐席不可读、外发未发生、模型未调用、成本记录缺口仍被标记。

5. 前端模型路由页接入治理摘要：
   - `frontend/src/App.tsx`
   - `frontend/src/api/client.ts`
   - `frontend/src/styles.css`
   - 模型路由页新增“检索与成本治理”区域、向量与评测摘要、H2W7 门禁列表、刷新按钮。

## 3. 当前门禁含义

| 门禁 | 判断方式 | 当前口径 |
|---|---|---|
| 知识库基础 | 是否有启用文档和已索引片段 | 缺一则阻断 |
| 真实题库规模 | 启用评测题是否达到 50 条 | 少于 50 条只能警告，不能代表商用准确率 |
| 检索评测 | 最近评测命中率和引用覆盖是否达到受控试点线 | 只代表检索评测，不代表完整客服答案准确率 |
| 生产级向量库 | 是否有 pgvector 片段或已执行生产索引计划 | SQLite/JSON 向量扫描只能算过渡方案 |
| Embedding 成本记录 | 是否有 provider smoke 的 token、耗时和费用估算 | 已有 smoke 才算通过 |
| 客服模型调用成本 | 是否已有按回复决策记录的模型调用成本 | 当前大多仍是缺口，不允许展示为完整成本治理 |

## 4. 停止门禁

1. 没有引用或无引用原因，却把回答标成高置信自动回复，停止。
2. 没有模型调用成本记录，却展示“模型成本已治理”，停止。
3. SQLite/JSON 向量扫描被写成生产级向量库完成，停止。
4. 评测题不足 50 条，却宣称完整商用准确率稳定，停止。
5. 当前治理摘要触发外部模型调用或真实平台外发，停止。
6. 坐席账号能看到成本治理和系统门禁，停止。

## 5. 尚未完成

1. 模型调用成本台账与单次/日/月预算门禁已由 H2W-7B 第一片部分完成，但仍不是完整供应商账单对账或完整 FinOps。
2. 渠道预算、店铺预算、客户预算、模型层级预算和高并发抢占策略仍未完成。
3. 生产级向量库验收：pgvector/专用向量库、索引执行、回滚、性能 smoke。
4. 重排器治理：当前只记录配置，不代表真实 cross-encoder 或商业 reranker 已接入。
5. 每次最终回答引用溯源：需要把回复决策、引用片段、最终回复、无引用原因和转人工原因完整绑定。
6. 高并发成本保护：限流、熔断、队列、预算不足自动转人工仍需后续阶段。

## 6. 验收命令

```bash
cd /Users/ericlee/Desktop/01_项目工作区/肥肥lu/lite_a_customer_service/standard_ops
backend/.venv/bin/python -m pytest backend/tests/test_rag_cost_governance_api.py -q
python3 scripts/check_p3_06u_26h2w7_rag_cost_governance.py
node scripts/check_p3_06u_26h2w7_rag_cost_governance_ui.mjs
cd frontend && npm run typecheck && npm run build
```

## 7. 真实边界

- 本片没有调用真实大模型。
- 本片没有真实平台外发。
- 本片没有接企业微信、抖音、淘宝、京东或拼多多。
- 本片没有把本地 SQLite/JSON 检索包装成生产级向量库。
- 本片只完成 H2W-7 的第一片治理可见性和门禁，不代表 H2W-7 全部完成。
