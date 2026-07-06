# P3-06U-26H2N 人工事实性标签入口第一片

日期：2026-07-03  
范围：标准运营版知识评测、月度质量复盘、人工答案质量标注  
状态：已完成第一片工程闭环

## 目标

H2M 已经把月度质量复盘做成只读服务端聚合，但其中“人工事实性标签”仍只是缺口指标。H2N 的目标是补上第一个可用入口：运营人员可以在知识评测结果里对单题最终答案质量做人工事实性标注，系统把标注结果回写到评测运行摘要和月度质量复盘里。

这一步不是完整客服准确率验收。它只解决“人工标注入口、服务端聚合、前端可操作、浏览器闭环证明”四件事。

## 已完成

- 后端新增 `PATCH /api/knowledge-evaluation-run-cases/{run_case_id}/factuality-label`。
- 后端新增 `label_knowledge_evaluation_run_case_factuality()`，允许具备知识管理权限的负责人/管理员标注单题结果。
- 标注状态支持：
  - `correct`：事实正确。
  - `partially_correct`：部分正确。
  - `incorrect`：事实有误。
  - `needs_human_review`：应转人工。
  - `not_applicable`：不适用，不纳入事实性得分。
- 服务端会重新计算评测运行摘要：
  - `final_answer_factuality_measured`
  - `final_answer_factuality_rate`
  - `final_answer_factuality_labeled_cases`
  - `citation_sufficiency_rate`
  - `forbidden_commitment_violation_rate`
  - `handoff_correctness`
  - `unsupported_answer_rate`
- 月度质量复盘接口会读取这些标注结果，让质量页不再只能展示“人工事实性标签缺口”。
- 前端知识评测详情里新增人工标注按钮：
  - 事实正确
  - 部分正确
  - 事实有误
  - 应转人工
- 前端标注后会刷新当前评测运行和本月质量复盘包。
- 新增浏览器 smoke：
  - `scripts/check_p3_06u_26h2n_factuality_label_ui.mjs`
  - 证据目录：`output/p3_06u_26h2n_factuality_label_ui/`

## 数据与审计边界

- 标注写入 `KnowledgeEvaluationRunCase.result_payload.answer_quality`，第一片不新增数据库迁移。
- 审计事件为 `knowledge_evaluation_run_case.factuality_labeled`。
- `reviewer_notes` 不保存明文，只记录 hash 与长度。
- 标注过程不调用模型。
- 标注过程不写外部平台。
- 标注过程不真实发送消息。
- 浏览器 smoke 使用临时 SQLite、临时后端、临时前端和临时 Chrome profile。

## 仍未完成

- 真实客户 50-100 条题库还没有作为客户项目级样本导入。
- 现有题库模板样例仍不能代表真实客户问题分布。
- 当前知识评测主体仍是检索和证据链评测，不是完整客服最终答案准确率。
- 系统还没有批量生成“最终客服答案”并把答案文本进入正式人工评审流。
- 还没有完整覆盖“事实正确、引用充分、禁用承诺、转人工正确性、客户投诉风险”的成套人工标注工作台。
- 还没有形成客户月度质量报告的正式签收口径。

## 验收口径

H2N 可以证明：

- 单题人工事实性标签可以在前端操作。
- 标签可以被后端权限、服务和审计接住。
- 标签可以回写评测运行摘要。
- 月度质量复盘可以读取标签后的事实性指标。
- 该链路不会调用模型、不会外发、不会泄露原始备注。

H2N 不能证明：

- 客服系统已经达到完整商用准确率。
- 所有真实客户问题已经覆盖。
- 多渠道自动回复已经上线。
- 知识库已经达到生产级 RAG 完整能力。
- 真实平台外发可以打开。

## 验证命令

```bash
cd /Users/ericlee/Desktop/01_项目工作区/肥肥lu/lite_a_customer_service/standard_ops/backend
./.venv/bin/python -m pytest tests/test_knowledge_evaluations_api.py -q
./.venv/bin/python -m py_compile app/services/knowledge.py app/api/knowledge.py app/schemas/knowledge.py

cd /Users/ericlee/Desktop/01_项目工作区/肥肥lu/lite_a_customer_service/standard_ops/frontend
npm run typecheck
npm run build

cd /Users/ericlee/Desktop/01_项目工作区/肥肥lu/lite_a_customer_service/standard_ops
node scripts/check_p3_06u_26h2n_factuality_label_ui.mjs
```

## 下一步

优先进入真实客户 50-100 题库的正式导入和标注流程：

- 设计客户可交付的题库 CSV/表格字段。
- 做导入前脱敏检查。
- 按业务对象、渠道、售前/售后、风险类型分布覆盖。
- 让系统生成或采集最终客服答案文本。
- 人工标注事实性、引用充分、禁用承诺、转人工是否正确。
- 把标注结果进入月度质量复盘和知识修复闭环。

如果继续恢复线，则做本机恢复工具第二片；但准确率验收主线应优先补真实题库和最终答案人工标注。
