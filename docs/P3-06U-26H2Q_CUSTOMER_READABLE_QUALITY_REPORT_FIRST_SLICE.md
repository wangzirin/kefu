# P3-06U-26H2Q 客户可读质量报告第一片

日期：2026-07-03

## 定位

本片继续留在七点计划中的“质量与准确率闭环”，不进入第 3 点渠道正式接入验收。

H2Q 的目标是把 H2M 月度质量复盘、H2N 人工事实性标签、H2O 真实客户题库导入和 H2P 最终回复采样/批量标签，收束成客户能读懂的质量报告第一片。它用于客户月度复盘、试点沟通和签收前判断，但不把当前结果包装成完整线上客服准确率。

## 已完成

- 后端新增客户质量报告 schema：
  - `CustomerQualityReportRead`
  - `CustomerQualityReportMetricRead`
  - `CustomerQualityReportSectionRead`
  - `CustomerQualityReportActionRead`
- 后端新增只读服务 `get_customer_quality_report()`：
  - 复用现有月度质量复盘聚合。
  - 增加报告状态、报告可信度分数、客户可读结论、摘要、指标、章节、行动计划和签收检查项。
  - 明确报告可信度不是客服准确率。
- 后端新增接口：
  - `GET /api/tenants/{tenant_id}/customer-quality-report`
  - 权限沿用 `quality.read`。
- 前端 API client 新增 `getCustomerQualityReport()` 和对应类型。
- 前端质量复盘页新增“客户可读质量报告”区块：
  - 展示报告状态、报告可信度、质量结论、摘要、关键指标、分章节说明、签收前动作和签收边界。
  - 不展示原始客户问题、完整回复、渠道 payload、token、密钥或密码。

## 报告口径

报告状态当前分为：

- `sample_insufficient`：题库少于 50 条，只能方向性复盘。
- `sample_capture_required`：题库够，但最终回复样本不足。
- `human_label_required`：已有样本，但缺人工事实性标签。
- `controlled_trial_ready`：样本、最终回复和人工标签形成初步闭环，可进入受控试点质量签收。
- `repair_required`：已有复盘依据，但仍需补知识、复核转人工或跑同题集回归。

报告可信度由以下因素合成：

- 真实题库规模。
- 最终回复采样覆盖率。
- 人工事实性标签结果。
- 引用覆盖。
- 知识缺口闭环。
- 是否仍存在关键阻断问题。

它不是线上客服准确率，也不是平台真实外发验收。

## 验证

- `cd backend && ./.venv/bin/python -m pytest tests/test_knowledge_evaluations_api.py::test_owner_can_capture_final_answer_samples_and_batch_label_factuality -q`
  - 通过。
- `cd backend && ./.venv/bin/python -m pytest tests/test_knowledge_evaluations_api.py tests/test_knowledge_gaps_api.py tests/test_reply_decisions_api.py tests/test_diagnostics_api.py -q`
  - `24 passed`。
- `cd backend && ./.venv/bin/python -m py_compile app/services/knowledge.py app/api/knowledge.py app/schemas/knowledge.py`
  - 通过。
- `cd frontend && npm run typecheck`
  - 通过。
- `cd frontend && npm run build`
  - 通过，仍只有既有 Vite chunk 体积提醒。
- `node scripts/check_p3_06u_26h2q_customer_quality_report_ui.mjs`
  - 通过。
  - 证据目录：`output/p3_06u_26h2q_customer_quality_report_ui/`

## 边界

- 本轮不接官方渠道。
- 本轮不做 RPA。
- 本轮不调用模型。
- 本轮不写 outbox。
- 本轮不真实外发。
- 本轮不上传诊断包。
- 本轮不把检索命中率或报告可信度写成完整客服准确率。
- 客户报告不包含原始客户问题、完整最终回复、人工备注明文、联系方式、token、密钥或渠道 payload。

## 下一步

建议继续留在质量闭环，优先补：

1. CSV / XLSX 最终回复样本和人工标签导入导出。
2. 客户报告导出为 PDF / DOCX 或本地 HTML。
3. 更多真实样本的分层统计和签收记录。

第 3 点渠道正式官方接入验收仍然后置，除非单独授权。
