# P3-06U-26H2O 真实客户题库导入第一片

## Engineering Control Card

- Stage: P3-06U-26H2O
- 当前主线阶段: 小微企业本地化交付后的质量验收基础
- 上一阶段真正完成: H2N 人工事实性标签入口第一片，评测运行可写入人工事实性标签并进入月度质量复盘
- 上一阶段明确没有完成: 真实客户 50-100 题题库正式导入、最终客服答案采样、批量人工标注和客户质量报告签收
- 本文目标: 让客户脱敏题库包可以先预检、再正式导入为客服质量评测集，并给出渠道、风险、引用和转人工覆盖分布
- 本文不做什么: 不调用模型；不生成最终客服答案；不写外部平台；不保存导入摘要里的原始问题；不替代客户验收报告
- 当前产品口径: 本片证明“题库进入系统”链路成立，不证明完整客服最终答案准确率已经验收

## 一句话结论

H2O 已经把“真实客户 50-100 条脱敏题库”从模板阶段推进到可导入阶段：后端提供题库预检和导入接口，前端知识评测页提供题库 JSON 粘贴、预检和导入入口，系统会阻断题量不足、重复编号和默认敏感信息命中，并把合格题库创建为正式评测集。

## 本轮完成

### 后端

- 新增客户题库包 schema：
  - `CustomerServiceQuestionBankImportCreate`
  - `CustomerServiceQuestionBankPrecheckRead`
- 新增预检接口：
  - `POST /api/tenants/{tenant_id}/customer-service-question-banks/precheck`
- 新增导入接口：
  - `POST /api/tenants/{tenant_id}/customer-service-question-banks/import`
- 预检规则覆盖：
  - 题量必须在 `minimum_case_count` 到 `maximum_case_count` 之间，默认 50-100 题。
  - `external_case_id` 不允许重复。
  - 默认阻断手机号、邮箱、身份证号等敏感信息命中。
  - 输出渠道、问题类型、风险等级、引用来源、期望词、转人工样本和自动回复样本覆盖。
- 导入成功后：
  - 复用现有知识评测集创建服务。
  - 创建 `KnowledgeEvaluationSet` 和对应 `KnowledgeEvaluationCase`。
  - 写入 `customer_service_question_bank.imported` 审计事件。
  - 审计和响应摘要不包含原始问题、客户答案明文或模型输出。

### 前端

- 知识评测页新增“客户题库导入”面板。
- 支持粘贴由表格转换后的题库 JSON。
- 支持“预检题库”和“导入题库”两步动作。
- 预检结果展示：
  - 题量。
  - 事实点覆盖。
  - 引用来源覆盖。
  - 转人工样本比例。
  - 渠道分布。
  - 风险分布。
  - 敏感命中数量。
  - 是否关闭原文回显。
- 导入成功后刷新知识评测集列表。

### 验证脚本

- 新增浏览器烟测：
  - `scripts/check_p3_06u_26h2o_customer_question_bank_import_ui.mjs`
- 该脚本会启动临时后端、临时前端、临时 SQLite 和临时无头 Chrome。
- 烟测流程：
  1. 创建临时本地负责人账号。
  2. 进入知识评测页。
  3. 使用前端默认 50 题脱敏样例。
  4. 点击“预检题库”。
  5. 确认显示“预检通过：50 题”。
  6. 点击“导入题库”。
  7. 确认显示“已导入 50 题”。
  8. 后端检查导入评测集存在且 `case_count=50`。
  9. 确认结果区不回显原始问题。
  10. 确认没有模型调用和外部平台写入。

## 质量与安全边界

本片保留以下硬边界：

- 不调用任何大模型。
- 不产生最终客服回复。
- 不写 outbox。
- 不外发到微信、企微、抖音、淘宝、京东、拼多多或其他平台。
- 不上传诊断包。
- 不保存 token、cookie、密码、私钥或渠道凭据。
- 默认阻断敏感信息题目，除非后续客户本地明确开启并承担审查流程。
- 页面导入摘要不展示原始问题文本。

需要特别说明：题库导入以后，题目会作为评测用例保存在本地系统中，这是为了后续回归评测和人工事实性标签。当前“不回显原文”指接口摘要、审计事件和烟测 summary 不回显原始问题，不是说本地评测用例不保存题目。

## 当前还没有完成

- 还没有做 CSV / XLSX 文件直接上传入口。
- 还没有做最终客服答案文本采样。
- 还没有批量运行模型回复质量评测。
- 还没有批量人工事实性标签工作台。
- 还没有客户签收版质量报告。
- 还没有生产级向量库和混合检索改造。
- 还没有真实渠道入站消息导出的客户题库闭环。
- 还没有把客户真实业务对象和知识包与题库导入做一键关联。

## 验证结果

- `cd backend && ./.venv/bin/python -m pytest tests/test_knowledge_evaluations_api.py -q`
  - 结果：`9 passed`
- `cd backend && ./.venv/bin/python -m pytest tests/test_knowledge_evaluations_api.py tests/test_knowledge_gaps_api.py tests/test_reply_decisions_api.py tests/test_diagnostics_api.py -q`
  - 结果：`23 passed`
- `cd backend && ./.venv/bin/python -m py_compile app/services/knowledge.py app/api/knowledge.py app/schemas/knowledge.py`
  - 结果：通过
- `cd frontend && npm run typecheck`
  - 结果：通过
- `cd frontend && npm run build`
  - 结果：通过，仅有既有 Vite chunk 体积提醒
- `node scripts/check_p3_06u_26h2o_customer_question_bank_import_ui.mjs`
  - 结果：通过
  - 证据目录：`output/p3_06u_26h2o_customer_question_bank_import_ui/`
  - 摘要：`case_count=50`，`raw_result_text_included=false`，`model_call_performed=false`，`external_platform_write_performed=false`

## 下一步

建议下一片进入“最终答案采样与批量人工标签”：

1. 选择一个已导入的客户题库。
2. 对每题生成或采集系统最终客服答案。
3. 把最终答案、引用、转人工判断和禁用承诺检查放到同一张批量标注表。
4. 让人工标注事实正确、部分正确、事实错误、应转人工、引用不足和禁用承诺违规。
5. 把批量标签写回评测运行。
6. 生成客户可读质量报告。

也可以并行补一个轻量文件上传入口，让客户交付 CSV/XLSX 后无需手动使用脚本转换。
