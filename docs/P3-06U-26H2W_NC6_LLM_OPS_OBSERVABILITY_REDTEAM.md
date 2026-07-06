# H2W-NC6 模型观测、成本与红队治理

## 结论

- 阶段状态：`llm_ops_observability_ready_not_redteam_complete`
- 后端接口 ready：`true`
- 前端展示 ready：`true`
- 成本台账 ready：`true`
- 链路追踪 ready：`true`
- 红队闭环 ready：`false`

## 当前阻断项

- 红队题集和人工标签尚未形成完整闭环，不能写成安全评测完成。

## 已纳入的证据

- schema: `backend/app/schemas/llm_ops.py`，存在：`true`
- service: `backend/app/services/llm_ops.py`，存在：`true`
- api: `backend/app/api/knowledge.py`，存在：`true`
- backend_test: `backend/tests/test_llm_ops_readiness_api.py`，存在：`true`
- frontend_client: `frontend/src/api/client.ts`，存在：`true`
- frontend_app: `frontend/src/App.tsx`，存在：`true`
- nc5: `output/p3_06u_26h2w_nc5_production_retrieval_governance/summary.json`，存在：`true`
- model1: `output/p3_06u_26h2w_model1_bailian_cost_sample/summary.json`，存在：`true`
- trial1: `output/p3_06u_26h2w_trial1_internal_100q_rehearsal_report/summary.json`，存在：`true`

## 固定边界

- 本阶段新增的是模型运营可观测与红队治理入口，不代表真实平台自动回复已开启。
- 没有 5-10 条真实模型小样本、价格版本和延迟记录时，不能写客户侧真实模型成本报告。
- 没有提示注入、隐私泄露、禁用承诺和越权操作题集的人工标签时，不能写红队安全闭环完成。
- 显式指定模型服务商失败不得静默切换；只有自动路由允许按策略降级。
- 真实外发、真实渠道、客户签收、生产 SLA 和签名安装包仍未完成。
