# H2W-NC17 红队题库与影子试跑标签包

## 结论

- 阶段状态：`redteam_shadow_trial_internal_sample_ready_not_customer_security_signoff`
- 红队样本数：`25`
- 人工标签数：`25`
- 类目覆盖：`{'forbidden_commitment': 5, 'jailbreak': 5, 'over_permission': 5, 'privacy_leak': 5, 'prompt_injection': 5}`
- 转人工正确率：`1.0`
- 禁用承诺通过率：`1.0`
- 不安全复述数：`0`

## 当前阻断项

- 无

## 本阶段做了什么

- 建立 25 条内部准真实红队样本，覆盖提示注入、越狱、隐私泄露、禁用承诺和越权操作。
- 建立同样 25 条影子试跑人工标签，全部走安全拒绝或转人工路径。
- 校验样本与标签一一对应，不含真实客户原文、真实密钥或平台 payload。
- 校验该包只能作为内部演练证据，不能作为正式客户安全签收。

## 固定边界

- 本阶段不调用真实模型。
- 本阶段不打开真实外发。
- 本阶段不推进真实渠道接入。
- 本阶段不等于客户真实红队安全签收。

## 证据文件

- case_file: `evals/p3_06u_26h2w_nc17_redteam_shadow_trial/redteam_cases.csv`，存在：`true`
- label_file: `evals/p3_06u_26h2w_nc17_redteam_shadow_trial/redteam_labeled_shadow_results.csv`，存在：`true`
- nc16_summary: `output/p3_06u_26h2w_nc16_redteam_closure/summary.json`，存在：`true`
