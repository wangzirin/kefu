# H2W-11I 标准答案缺口评测输入包

## 定位

H2W-11I 接在 H2W-11H 之后，只做一件事：把 H2W-11H 暴露出来的标准答案来源缺口，转成下一轮最终答案评测可以使用的输入包。

这一片不是正式客户准确率签收，也不是下一轮最终答案评测已经完成。它只是把缺口来源、标准答案模板行、期望标签和脱敏边界整理成可复用文件，避免后续继续凭感觉补样本。

## 本片完成项

1. 新增门禁脚本：
   - `scripts/check_p3_06u_26h2w11i_standard_answer_gap_eval_plan.py`

2. 新增评测输入文件：
   - `evals/p3_06u_26h2w11i_standard_answer_gap_eval_cases.csv`
   - `evals/p3_06u_26h2w11i_standard_answer_gap_label_plan.csv`

3. 新增输出证据：
   - `output/p3_06u_26h2w11i_standard_answer_gap_eval_plan/summary.json`
   - `output/p3_06u_26h2w11i_standard_answer_gap_eval_plan/standard_answer_gap_eval_plan.md`

4. 新增测试：
   - `backend/tests/test_p3_06u_26h2w11i_standard_answer_gap_eval_plan.py`

## 真实口径

本片可以证明：

- H2W-11H 暴露的缺口来源都能映射到标准答案模板行。
- 每个缺口来源至少有一条下一轮评测候选样本。
- 候选样本保留标准答案 hash、引用来源、必含词、禁用词、自动回复/转人工口径。
- 输出文件不导出最终客服答案正文。
- 输出文件不代表真实客户确认。

本片不能证明：

- 下一轮最终答案评测已经执行。
- 系统最终回答已经对齐客户标准答案。
- 客户已经确认标准答案。
- 正式线上准确率已经可签收。
- 真实平台外发、真实 IM、正式电子签章或生产上线已经完成。

## 验收命令

```bash
python3 scripts/check_p3_06u_26h2w11i_standard_answer_gap_eval_plan.py
backend/.venv/bin/pytest backend/tests/test_p3_06u_26h2w11i_standard_answer_gap_eval_plan.py -q
python3 scripts/check_p3_06u_26h2w11h_standard_answer_quality_bridge.py
```

## 停止门禁

出现任一情况，本片不能通过：

- H2W-11H 未通过。
- H2W-11H 没有暴露标准答案来源缺口。
- 任一缺口来源没有下一轮评测候选样本。
- 候选样本被写成客户已确认。
- 候选样本出现手机号、邮箱、身份证号等疑似隐私。
- 输出文件导出最终客服答案正文。
- 报告把本片写成正式客户准确率签收、真实外发、正式电子签章、合同签收、生产上线或真实客户数据使用。

## 下一步

H2W-11I 通过后，下一步可以进入 H2W-11J：基于本输入包跑一轮新的最终答案样本采集/标签演练，或先设计安全对比运行时。安全对比运行时可以在本地临时环境读取最终答案正文做比对，但输出报告仍只保留标签、hash、来源和统计，不外泄完整客户问题或完整客服回答。
