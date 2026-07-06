# P3-06U-26H2W11J 缺口样本最终答案 rehearsal

## 定位

H2W-11J 接在 H2W-11I 之后，只处理 H2W-11I 生成的 7 条缺口样本。

本轮目标是验证这些缺口样本已经能进入最终答案质量标签口径：事实性、引用充分性、禁用承诺和转人工正确性。

## 本轮做什么

- 读取 `evals/p3_06u_26h2w11i_standard_answer_gap_eval_cases.csv`。
- 读取 `evals/p3_06u_26h2w11i_standard_answer_gap_label_plan.csv`。
- 使用本地确定性 rehearsal 生成回复摘要。
- 导出脱敏样本文件和标签文件。
- 检查自动回复样本是否覆盖必含词。
- 检查转人工样本是否正确进入转人工口径。
- 检查引用来源、禁用承诺和客户确认边界。

## 本轮不做什么

- 不调用真实大模型。
- 不打开真实外发。
- 不连接微信、企微、抖音、淘宝、京东、拼多多等真实平台。
- 不导出完整最终答案正文。
- 不使用真实客户原始数据。
- 不生成正式电子签章、合同签收或正式客户准确率签收。

## 输出

- `output/p3_06u_26h2w11j_gap_final_answer_rehearsal/summary.json`
- `output/p3_06u_26h2w11j_gap_final_answer_rehearsal/gap_final_answer_samples_redacted.csv`
- `output/p3_06u_26h2w11j_gap_final_answer_rehearsal/gap_final_answer_labels.csv`
- `output/p3_06u_26h2w11j_gap_final_answer_rehearsal/gap_final_answer_rehearsal_report.md`

## 验收命令

```bash
python3 scripts/check_p3_06u_26h2w11j_gap_final_answer_rehearsal.py
backend/.venv/bin/pytest backend/tests/test_p3_06u_26h2w11j_gap_final_answer_rehearsal.py -q
```

## 停止门禁

- 如果导出文件包含完整最终答案正文，停止。
- 如果 H2W-11I 不是 `passed`，停止。
- 如果 H2W-11I 未标记 `ready_for_next_final_answer_eval_run=true`，停止。
- 如果任何样本出现禁用承诺词，停止。
- 如果任何样本误写客户已确认，停止。
- 如果任何真实外发、真实平台发送或真实模型调用被打开，停止。

## 通过口径

- `status=passed`。
- 7 条缺口样本全部生成脱敏样本和标签。
- 自动回复样本事实性通过率为 1.0。
- 引用充分率为 1.0。
- 禁用承诺通过率为 1.0。
- 转人工正确率为 1.0。
- `ready_for_gap_quality_report_review=true`。
- `ready_for_formal_accuracy_signoff=false`。

## 下一步

H2W-11K 应把 H2W-11J 的缺口 rehearsal 标签接入客户质量报告确认页和项目总控记录，但仍保持本地演练口径。
