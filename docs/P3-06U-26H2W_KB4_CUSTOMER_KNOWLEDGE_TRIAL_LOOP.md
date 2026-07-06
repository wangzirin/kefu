# H2W-KB4 客户知识资料试跑闭环

## 结论

- 阶段状态：`customer_knowledge_trial_loop_ready`
- CSV 模板：`evals/p3_06u_26h2w_kb3_customer_knowledge_center_template.csv`
- XLSX 模板：`output/p3_06u_26h2w_kb4_customer_knowledge_trial_loop/wanfa_customer_knowledge_trial_template.xlsx`

## 固定 6 步

- 导入资料
- 预检
- 发布
- 复测
- 确认
- 质量报告

## 边界

- CSV 可直接导入，XLSX 是同列名填写模板；本地试跑 v1 先另存为 CSV 后导入。
- PDF/DOCX 只作为来源资料，不承诺全自动高质量入库。
- 知识评测是客服答案质量候选评测，不是正式线上准确率签收。
- 真实外发继续关闭。

## 阻断项

- 无
