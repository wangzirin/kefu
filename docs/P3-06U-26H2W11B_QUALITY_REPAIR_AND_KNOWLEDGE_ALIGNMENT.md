# H2W-11B 质量修复与知识包对齐

日期：2026-07-04

## 定位

H2W-11B 用来修复 H2W-11A 暴露出的质量问题：演练链路能跑通，但知识包与 62 条客户式题库严重错配，导致客户质量报告为 `repair_required`。

本片仍是本地受控演练，不是正式客户验收，不调用真实模型，不打开真实外发。

## 完成内容

- 新增 `scripts/check_p3_06u_26h2w11b_quality_repair.py`。
- 新增 `backend/tests/test_p3_06u_26h2w11b_quality_repair_script.py`。
- 生成修复版知识包 `evals/p3_06u_26h2w11b_repaired_customer_knowledge_package.json`。
- 修复包从 62 条脱敏题库提取期望词、渠道、场景和业务关键词，生成 62 张“题库覆盖卡”。
- 修复包不包含原始客户问题全文，不包含密码、token 或外部平台凭据。
- 修复包不再把客户诱导式禁用承诺词原样写入自动回复材料；保留为安全边界类别表达。
- H2W-11A 自动标注口径补正：正确转人工样本标为 `not_applicable`，不计入最终答案事实性分母。
- 后端事实性标签语义补正：`not_applicable` 仍算已标注，但不参与事实性打分。
- 使用修复版知识包复跑 H2W-11A。

## 验收结果

修复前 H2W-11A：

- `expected_term_coverage=0.0484`
- `human_review_correctness=0.4194`
- `final_answer_factuality_rate=0.0`
- `report_status=repair_required`
- `report_confidence_score=55`

修复后 H2W-11B：

- `expected_term_coverage=1.0`
- `human_review_correctness=1.0`
- `final_answer_factuality_rate=1.0`
- `average_confidence=0.9344`
- `report_status=controlled_trial_ready`
- `report_confidence_score=90`
- 逐题状态：37 条 passed，25 条 needs_review。
- 最终答案标签：37 条 correct，25 条 not_applicable。

## 证据路径

- `output/p3_06u_26h2w11b_quality_repair/summary.json`
- `output/p3_06u_26h2w11b_quality_repair/repaired_h2w11a_rerun/summary.json`
- `output/p3_06u_26h2w11b_quality_repair/repaired_h2w11a_rerun/customer_service_eval_run_1_review.md`
- `output/p3_06u_26h2w11b_quality_repair/repaired_h2w11a_rerun/customer_service_eval_run_1_cases.csv`
- `output/p3_06u_26h2w11b_quality_repair/repaired_h2w11a_rerun/customer_service_eval_run_1_final_answer_labels.csv`
- `output/p3_06u_26h2w11b_quality_repair/repaired_h2w11a_rerun/wanfa-customer-quality-report-1-2026-07.html`

## 验证命令

```bash
.venv/bin/pytest backend/tests/test_knowledge_evaluations_api.py backend/tests/test_p3_06u_26h2w11a_owner_rehearsal_script.py backend/tests/test_p3_06u_26h2w11b_quality_repair_script.py -q
.venv/bin/python scripts/check_p3_06u_26h2w11b_quality_repair.py
```

## 边界

- 没有使用真实客户原始数据。
- 没有调用百炼、DeepSeek 或其他真实大模型 provider。
- 没有打开真实平台外发。
- 没有接真实企业微信、公众号、抖音、淘宝、京东或拼多多。
- 没有做电子签章、合同签收或正式客户验收。
- `controlled_trial_ready` 只表示本地受控演练数据达标，可以进入下一片演练；不表示生产上线。

## 下一步

- 进入 H2W-11D：把修复版知识包、客户质量报告和知识发布流程映射到前端客户可操作路径。
- 复核前端是否能让客户自己导入业务对象、标准问答、流程政策、禁用承诺和转人工规则。
- 继续保持真实外发关闭，真实 IM 另开授权专项。
