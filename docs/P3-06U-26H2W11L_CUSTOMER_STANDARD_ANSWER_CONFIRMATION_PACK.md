# H2W-11L 客户标准答案确认输入包

## 定位

H2W-11L 承接 H2W-11K 的客户质量报告缺口演练证据，生成一份可以交给客户或业务负责人逐项确认的标准答案输入包。

这一片解决的问题不是“正式准确率签收”，而是把后续正式签收之前必须确认的答案口径整理成可检查、可追溯、可填写的 CSV：

- 哪些问题允许自动回复。
- 哪些问题必须转人工。
- 标准答案是否符合业务事实。
- 必含词和禁用承诺是否准确。
- 引用来源是否能支撑对外回答。
- 本地缺口演练是否已有标签证据。

## 本轮完成

- 新增 `scripts/check_p3_06u_26h2w11l_customer_standard_answer_confirmation_pack.py`。
- 新增 `backend/tests/test_p3_06u_26h2w11l_customer_standard_answer_confirmation_pack.py`。
- 生成 `evals/p3_06u_26h2w11l_customer_standard_answer_confirmation_pack.csv`。
- 生成 `output/p3_06u_26h2w11l_customer_standard_answer_confirmation_pack/summary.json`。
- 生成 `output/p3_06u_26h2w11l_customer_standard_answer_confirmation_pack/customer_standard_answer_confirmation_pack_review.md`。

## 输入依据

- H2W-11G 标准答案模板：`evals/p3_06u_26h2w11g_customer_standard_answer_template.csv`。
- H2W-11J 缺口样本最终答案标签：`output/p3_06u_26h2w11j_gap_final_answer_rehearsal/gap_final_answer_labels.csv`。
- H2W-11K 客户质量报告缺口演练证据：`output/p3_06u_26h2w11k_customer_report_gap_rehearsal/summary.json`。

## 输出字段

确认输入包包含：

- `source_standard_case_id`：来源标准答案样本。
- `standard_answer_for_customer_review`：待客户确认的标准答案。
- `required_terms`：必须覆盖的关键口径。
- `forbidden_terms`：不能承诺或不能复述的高风险词。
- `allow_auto_reply`：是否可进入自动回复候选。
- `should_handoff`：是否应转人工。
- `local_rehearsal_status`：是否已有缺口本地演练证据。
- `final_answer_factuality_status`：本地演练标签状态。
- `needs_customer_confirmation=true`：仍需要客户确认。
- `customer_confirmed=false`：当前尚未确认。
- `not_formal_signoff=true`：当前不是正式签收。

## 真实边界

- H2W-11L 不是正式客户准确率签收。
- `customer_confirmed=false` 时，不能进入正式准确率签收。
- 真实外发继续关闭。
- 不调用真实模型 provider。
- 不连接真实微信、企微、抖音、淘宝、京东或拼多多外发。
- 不使用真实客户原始数据。
- 不生成正式电子签章、合同签收或完整线上准确率结论。

## 停止门禁

- 确认包没有覆盖所有标准答案样本时停止。
- 缺口演练证据少于 7 条时停止。
- 任意条目出现 `customer_confirmed=true` 时停止，除非后续另有真实客户确认专项。
- 任意条目把 `not_formal_signoff` 改为 `false` 时停止。
- 导出文件出现完整最终答案正文、真实客户原始问题、手机号、邮箱、身份证号时停止。
- H2W-11K 没有保持 `ready_for_formal_accuracy_signoff=false` 时停止。

## 验收命令

```bash
backend/.venv/bin/python scripts/check_p3_06u_26h2w11l_customer_standard_answer_confirmation_pack.py
backend/.venv/bin/pytest backend/tests/test_p3_06u_26h2w11l_customer_standard_answer_confirmation_pack.py -q
```

## 下一步

后续可以进入客户确认标准答案专项，或继续补真实题库、线上回执、正式报告签收和生产级检索证据。真实 IM 与官方渠道外发仍然另开授权专项。
