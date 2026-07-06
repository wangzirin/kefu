# H2W-11M 客户标准答案确认结果导入门禁

日期：2026-07-04

## 定位

H2W-11M 接续 H2W-11L。H2W-11L 已生成“客户标准答案确认输入包”，但当前仍是 `customer_confirmed=false`。H2W-11M 不负责替客户确认答案，也不生成正式客户准确率签收；它只负责把“客户真实返回的确认表”变成可校验、可导入、可追溯的前置门禁。

本阶段的核心原则是：不伪造客户确认。

## 本轮完成

1. 新增客户确认结果导入门禁脚本：
   - `scripts/check_p3_06u_26h2w11m_customer_confirmation_import_gate.py`
2. 新增客户返回模板：
   - `evals/p3_06u_26h2w11m_customer_confirmation_return_template.csv`
3. 新增阶段输出：
   - `output/p3_06u_26h2w11m_customer_confirmation_import_gate/summary.json`
   - `output/p3_06u_26h2w11m_customer_confirmation_import_gate/customer_confirmation_import_gate_review.md`
4. 新增测试：
   - `backend/tests/test_p3_06u_26h2w11m_customer_confirmation_import_gate.py`

## 字段口径

客户返回模板要求客户或业务负责人只填写这些确认字段：

- `customer_decision`：`pending`、`approved`、`revise`、`reject`
- `customer_confirmed`：只有 `approved` 时才允许为 `true`
- `customer_reviewer`
- `customer_reviewer_role`
- `customer_confirmed_at`
- `customer_revision_request`

标准答案、必含词、禁用词、引用来源不能在返回表中直接改写。如果客户要求调整，必须写入 `customer_revision_request`，再由我们生成下一版标准答案包。

## 当前真实结果

当前没有客户真实返回文件，因此门禁输出应保持：

- `customer_return_file_present=false`
- `ready_for_customer_return_collection=true`
- `ready_for_confirmed_standard_answer_import=false`
- `ready_for_formal_accuracy_signoff=false`
- 真实外发继续关闭

这表示客户确认导入流程已经准备好，但客户还没有真实确认任何标准答案。

## 停止门禁

以下任一情况出现，必须停止进入正式准确率签收：

1. 没有客户返回文件，却写成客户已确认。
2. 返回文件条目数与 H2W-11L 确认包不一致。
3. `confirmation_item_id` 或 `source_standard_case_id` 被改写。
4. 标准答案、必含词、禁用词或引用来源被直接改写。
5. `approved` 条目没有确认人、角色和确认时间。
6. `revise` 或 `reject` 条目没有修改意见。
7. 返回文件出现手机号、邮箱、身份证号等疑似敏感信息。
8. 返回文件全部批准，也不能直接进入正式准确率签收；仍需真实题库、线上回执、正式报告签收和生产级检索证据。

## 验证命令

```bash
cd /Users/ericlee/Desktop/01_项目工作区/肥肥lu/lite_a_customer_service/standard_ops
backend/.venv/bin/python scripts/check_p3_06u_26h2w11m_customer_confirmation_import_gate.py
backend/.venv/bin/python -m py_compile scripts/check_p3_06u_26h2w11m_customer_confirmation_import_gate.py
backend/.venv/bin/pytest backend/tests/test_p3_06u_26h2w11m_customer_confirmation_import_gate.py -q
```

## 边界

- 不调用真实模型 provider。
- 不打开真实外发。
- 不连接真实微信、企微、抖音、淘宝、京东或拼多多。
- 不使用真实客户原始数据。
- 不生成正式电子签章、合同签收或正式客户准确率签收。
