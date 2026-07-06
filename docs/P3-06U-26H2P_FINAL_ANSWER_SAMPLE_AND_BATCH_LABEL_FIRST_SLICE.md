# P3-06U-26H2P 最终回复采样与批量人工标签第一片

## Engineering Control Card

- Stage: P3-06U-26H2P
- 当前主线阶段: 七点计划中的第 7 点，客服准确率与质量闭环
- 上一阶段真正完成: H2O 真实客户 50-100 条脱敏题库可预检、可导入为客服质量评测集
- 上一阶段明确没有完成: 最终客服回复样本采集、批量人工事实性标签、客户可读质量报告签收
- 本文目标: 让评测运行里的每一道题可以挂载“最终客服回复样本”，并支持对已采样样本做批量人工事实性标签
- 本文不做什么: 不调用模型；不生成线上最终答案；不写 outbox；不外发微信、企微、抖音、淘宝、京东、拼多多或其他平台；不做渠道接入验收
- 当前产品口径: 本片证明“最终回复样本 -> 人工标签 -> 运行摘要 -> 月度质量复盘”闭环成立，不代表线上真实渠道已经自动回复

## 一句话结论

H2P 已经把知识评测从“只评检索和单条人工标签”推进到“可采样最终客服回复并批量标注”的第一片：后端新增最终回复样本接口和批量标签接口，前端知识评测页新增逐题样本输入和批量标注入口，月度质量复盘继续读取人工事实性指标。

## 本轮完成

### 后端

- 新增最终回复样本 schema：
  - `KnowledgeEvaluationRunCaseFinalAnswerSampleCreate`
  - `KnowledgeEvaluationRunCaseFinalAnswerSampleRead`
- 新增批量人工标签 schema：
  - `KnowledgeEvaluationRunCaseFactualityBatchLabelItem`
  - `KnowledgeEvaluationRunCaseFactualityBatchLabelCreate`
  - `KnowledgeEvaluationRunCaseFactualityBatchLabelRead`
- 新增最终回复样本接口：
  - `PATCH /api/knowledge-evaluation-run-cases/{run_case_id}/final-answer-sample`
- 新增批量标签接口：
  - `PATCH /api/knowledge-evaluation-runs/{evaluation_run_id}/factuality-labels/batch`
- 样本保存逻辑：
  - 将最终客服回复文本保存在本地评测用例 `result_payload.final_answer_sample`，用于授权用户后续人工查看和标注。
  - 审计事件只保存 hash、长度、来源、引用数量和备注 hash，不保存最终回复正文和备注明文。
  - 更新运行摘要里的 `final_answer_sampled_cases`、`final_answer_sample_coverage` 和 `final_answer_sample_note`。
- 批量标签逻辑：
  - 仅接受属于同一个评测运行的 case id。
  - 复用单条事实性标签口径，写入 `answer_quality.final_answer_factuality_status` 等字段。
  - 更新 `final_answer_factuality_rate`、`unsupported_answer_rate`、引用充分率、禁用承诺和转人工正确性。
  - 写入批量审计事件，不保存人工备注明文。

### 前端

- 知识评测页的“客服答案质量门禁”新增“最终回复样本”状态区。
- 逐题评测结果新增“最终客服回复样本”输入框：
  - 可粘贴或录入该题最终客服回复。
  - 保存后刷新当前运行详情。
  - 页面提示已采样题数和覆盖率。
- 新增批量标签按钮：
  - “批量标为事实正确”
  - “批量标为应转人工”
- 批量标签只处理已经采样的题，不会把未采样题误纳入最终答案准确率。

## 质量与安全边界

本片保留以下硬边界：

- 不调用任何大模型。
- 不自动生成客服回复。
- 不写外部平台。
- 不写 outbox。
- 不发送真实客户消息。
- 不保存渠道 token、cookie、密码、私钥或平台凭据。
- 审计事件不保存最终回复正文。
- 审计事件不保存人工备注明文。
- 批量标签只代表已采样、已标注题目，不代表所有线上会话准确率。

需要特别说明：最终回复样本文本会保存在本地评测用例里，因为人工标注需要看到答案正文。这里的“脱敏”边界是审计、报告摘要和 smoke summary 不回显原文；不是说授权评测页面完全不保存样本文本。

## 当前还没有完成

- 还没有自动从真实对话或 outbox 回执中采集最终回复。
- 还没有模型生成最终答案的离线评测链路。
- 还没有逐题多维打分表，例如事实性、语气、完整性、引用充分、风险承诺、是否应转人工分别打分。
- 还没有客户签收版质量报告。
- 还没有 CSV / XLSX 批量标签导入导出。
- 还没有把最终回复样本和知识缺口自动联动成知识修复任务。

## 验证结果

- `cd backend && ./.venv/bin/python -m pytest tests/test_knowledge_evaluations_api.py::test_owner_can_capture_final_answer_samples_and_batch_label_factuality -q`
  - 结果：通过
- `cd backend && ./.venv/bin/python -m pytest tests/test_knowledge_evaluations_api.py -q`
  - 结果：`10 passed`
- `cd backend && ./.venv/bin/python -m pytest tests/test_knowledge_evaluations_api.py tests/test_knowledge_gaps_api.py tests/test_reply_decisions_api.py tests/test_diagnostics_api.py -q`
  - 结果：`24 passed`
- `cd backend && ./.venv/bin/python -m py_compile app/services/knowledge.py app/api/knowledge.py app/schemas/knowledge.py`
  - 结果：通过
- `cd frontend && npm run typecheck`
  - 结果：通过
- `cd frontend && npm run build`
  - 结果：通过，仅有既有 Vite chunk 体积提醒
- `node scripts/check_p3_06u_26h2p_final_answer_sample_ui.mjs`
  - 结果：通过
  - 摘要：`output/p3_06u_26h2p_final_answer_sample_ui/summary.json`
  - 截图：`output/p3_06u_26h2p_final_answer_sample_ui/final-answer-sample-evals.png`

## 下一步

建议下一片继续留在七点计划第 7 点，推进“客户可读质量报告第一片”：

1. 从最新评测运行读取题库题数、样本覆盖率、人工事实性标签、需转人工样本、引用充分和禁用承诺结果。
2. 生成内部版质量报告 JSON / Markdown。
3. 区分三种口径：检索命中率、已采样最终回复事实性、完整线上准确率未验收。
4. 报告中明确写出“不调用模型、不外发、不包含真实平台消息”。
5. 后续再接 CSV / XLSX 批量标签导入和知识缺口联动。

