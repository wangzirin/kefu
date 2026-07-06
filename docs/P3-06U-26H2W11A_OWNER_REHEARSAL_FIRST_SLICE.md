# P3-06U-26H2W11A 负责人真实登录端到端演练第一片

## 定位

H2W-11A 用来验证“本地负责人账号登录后，是否可以把知识包、题库、检索评测、最终答案采样、事实性标签、客户质量报告和本地签收记录串成同一条受控演练链路”。

本阶段不是正式客户试点签收，也不是线上自动回复准确率证明。真实外发、真实平台回执、真实大模型调用和正式电子签章仍全部关闭。

## 本轮完成

- 新增 `scripts/check_p3_06u_26h2w11a_owner_rehearsal.py`。
- 新增 `backend/tests/test_p3_06u_26h2w11a_owner_rehearsal_script.py`。
- 使用空库 in-memory 后端创建首任负责人账号，再通过 `/api/auth/login` 做真实密码登录。
- 禁用开发 bootstrap、真实外发 worker、可信入站 worker、百炼/DeepSeek 外部 key。
- 将 `evals/p3_06u_26f_real_customer_knowledge_package_template.json` 转为知识更新包导入后端。
- 通过知识更新包接口导入 7 份知识文档，生成 14 个 chunk。
- 使用 `evals/p3_01_realistic_customer_service_eval_bank_62_2026-06-27.csv` 导入 62 条客户式脱敏题库。
- 运行客服检索评测，采集 62 条最终答案样本。
- 为 62 条样本写入事实性、引用充分、禁用承诺、转人工正确性标签。
- 导出默认脱敏的评测 Markdown、评测 CSV、最终答案标签 CSV 和客户质量报告 HTML。
- 写入本地客户质量报告签收记录；该签收是本地记录，不是电子签章或合同签收。

## 验证结果

```bash
/Users/ericlee/Desktop/01_项目工作区/肥肥lu/lite_a_customer_service/standard_ops/.venv/bin/pytest backend/tests/test_p3_06u_26h2w11a_owner_rehearsal_script.py -q
/Users/ericlee/Desktop/01_项目工作区/肥肥lu/lite_a_customer_service/standard_ops/.venv/bin/python scripts/check_p3_06u_26h2w11a_owner_rehearsal.py
```

结果：

- `status=completed`
- `ready_for_h2w11b=true`
- `blockers=[]`
- 负责人登录：真实密码登录，未使用开发免登录。
- 知识包：7 份文档，14 个 chunk。
- 题库：62 题，敏感行 0，来源通道 8 类。
- 评测：62 题全部运行，62 条最终答案样本，62 条事实性标签。
- 质量报告：已生成，状态为 `repair_required`。
- 签收记录：本地记录已写入，正式电子签章和合同签收均为 false。
- 安全边界：provider 调用 false，外部平台写入 false，真实客户数据 false。

证据目录：

```text
output/p3_06u_26h2w11a_owner_rehearsal/
```

关键文件：

- `summary.json`
- `customer_service_eval_run_1_review.md`
- `customer_service_eval_run_1_cases.csv`
- `customer_service_eval_run_1_final_answer_labels.csv`
- `wanfa-customer-quality-report-1-2026-07.html`

## 真实质量结论

本轮技术闭环已经跑通，但质量没有达到可签收状态：

- 客户质量报告状态为 `repair_required`。
- `expected_term_coverage=0.0484`，说明当前知识包与 62 题期望词覆盖明显不足。
- `human_review_correctness=0.4194`，转人工预测仍不稳定。
- `final_answer_factuality_rate=0.0`，本地确定性回复器生成的最终答案样本不能作为可交付准确率证明。

所以 H2W-11A 的结论是：端到端演练链路可用，质量门禁开始能发现真实问题；不是“试点已可签收”。

## 停止门禁

后续任何阶段出现以下情况，必须停下修复：

- 把 `repair_required` 质量报告写成已达标。
- 把客户式脱敏样例题库写成真实客户数据。
- 把本地签收记录写成电子签章、合同签收或正式客户验收。
- 把本地确定性回复器结果写成百炼/千问/DeepSeek 真实模型效果。
- 把 `provider_call_performed=false` 的结果写成真实模型调用。
- 把 `external_platform_write_performed=false` 的结果写成已对接微信、抖音、淘宝、京东或拼多多真实外发。
- 把检索评测命中率写成完整客服准确率。

## 下一步

进入 H2W-11B：质量修复与客户知识包对齐。

优先动作：

- 将 62 题与 7 份知识文档做逐类对照，补充缺失的标准答案、流程政策、禁用承诺和转人工规则。
- 重新生成或补充 `expected_answer` 字段，让最终答案事实性标签有客户可确认的标准口径。
- 改进本地确定性回复器/知识命中策略，不让所有低置信结果一律退回人工。
- 复跑 H2W-11A，直到质量报告不再是 `repair_required`，再进入前端逐页客户试用 rehearsal。
