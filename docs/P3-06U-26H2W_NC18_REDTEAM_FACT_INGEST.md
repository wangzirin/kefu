# H2W-NC18 红队事实账本导入门禁

## 结论

- 阶段状态：`redteam_fact_ingest_ready_internal_sample_visible_to_llm_ops`
- 导入红队样本：`25` 条
- 导入人工标签：`25` 条
- LLM Ops 红队 readiness：`ready_for_controlled_pilot`
- 红队来源：`database_evaluation_tables`
- 内部样本：`true`

## 阻断项

- 无

## 本阶段做了什么

- 将 NC17 内部红队样本包导入隔离数据库，落成评测集、评测用例、评测运行和人工标签。
- 调用现有 `llm-ops-readiness` 服务读取数据库事实，验证“模型观测与红队”卡片已有可消费字段。
- 样本问题以脱敏占位落库，红队攻击描述只保存 hash，不保存原文。
- 写入 `pilot_readiness_facts` 事实记录，作为后续试跑包证据来源之一。

## 固定边界

- 本阶段不调用真实模型。
- 本阶段不打开真实外发。
- 本阶段不推进真实渠道接入。
- 本阶段不等于客户真实红队安全签收。

## 证据文件

- case_file: `evals/p3_06u_26h2w_nc17_redteam_shadow_trial/redteam_cases.csv`，存在：`true`
- label_file: `evals/p3_06u_26h2w_nc17_redteam_shadow_trial/redteam_labeled_shadow_results.csv`，存在：`true`
- nc17_summary: `output/p3_06u_26h2w_nc17_redteam_shadow_trial/summary.json`，存在：`true`
- summary: `output/p3_06u_26h2w_nc18_redteam_fact_ingest/summary.json`，存在：`true`
- markdown: `docs/P3-06U-26H2W_NC18_REDTEAM_FACT_INGEST.md`，存在：`true`
