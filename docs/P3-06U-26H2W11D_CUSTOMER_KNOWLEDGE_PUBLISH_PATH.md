# H2W-11D 客户知识发布闭环前端路径

## 定位

H2W-11D 把 H2W-11B 的修复版知识包、客户质量报告和知识发布流程映射到前端客户可操作路径。

本阶段不是正式客户签收完成，也不是全渠道自动回复上线。它只证明：本地负责人进入知识库运营页后，可以按一条清楚的路径理解和执行“导入 -> 预检 -> 发布 -> 回归评测 -> 报告 -> 签收”。

## 本轮完成

- 在知识库运营页新增 `客户知识发布闭环` 面板。
- 面板使用真实前端状态，而不是固定演示文案：
  - 客户资料模板转换数量。
  - 知识更新包预检 / 导入状态。
  - 可发布草稿和已启用文档数量。
  - 最近一次知识评测命中率、引用覆盖和需复核题数。
  - 客户质量报告状态和可信度。
  - 客户确认记录状态。
- 面板按钮接入现有真实 handler：
  - 转换客户资料。
  - 预检更新包。
  - 导入本地知识库。
  - 发布前试跑首个可发布文档。
  - 确认发布首个可发布文档。
  - 进入知识评测页。
  - 查看质量报告页。
- 新增静态门禁脚本：
  - `scripts/check_p3_06u_26h2w11d_customer_knowledge_publish_path.py`
- 新增后端测试：
  - `backend/tests/test_p3_06u_26h2w11d_customer_knowledge_publish_path.py`

## 与 H2W-11B 的关系

H2W-11B 已完成质量修复与知识包对齐：

- 修复版知识包路径：
  - `evals/p3_06u_26h2w11b_repaired_customer_knowledge_package.json`
- 修复汇总路径：
  - `output/p3_06u_26h2w11b_quality_repair/summary.json`
- 修复后结论：
  - `status=completed`
  - `blockers=[]`
  - `report_status=controlled_trial_ready`
  - `report_confidence_score=90`
  - `case_card_count=62`
  - `expected_term_document_coverage_after=1.0`

H2W-11D 不重新生成修复知识包，而是把这条修复后的能力映射到客户能操作、能理解、能继续验收的前端路径。

## 当前边界

- 真实外发继续关闭。
- 不调用真实外部模型。
- 不连接微信、企微、抖音、淘宝、京东、拼多多等真实平台外发。
- 不使用 RPA、Cookie、Hook、个人号外挂作为正式交付路径。
- 客户签收仍是本地留档记录，不是正式电子签章，也不是合同签署。
- 当前知识评测仍不是完整线上客服准确率；它主要覆盖检索命中、引用覆盖、期望词覆盖和部分最终答案样本。

## 验收门禁

H2W-11D 必须同时满足：

- 前端存在 `data-h2w11d-customer-publish-path="true"`。
- 前端展示完整路径：`导入 -> 预检 -> 发布 -> 回归评测 -> 报告 -> 签收`。
- 前端状态接入 `knowledgeEvaluation`、`customerQualityReport`、`customerQualityReportSignoffs`。
- 面板按钮不得只是图标，必须连接到现有 handler 或真实页面入口。
- H2W-11B 修复汇总必须仍为 `completed` 且无 blocker。
- H2W-11B 修复报告必须仍为 `controlled_trial_ready`，可信度为 `90`。
- 文案不得写成真实外发已完成、全平台已接通、正式电子签章已完成或合同签收已完成。

## 验收命令

```bash
python3 scripts/check_p3_06u_26h2w11d_customer_knowledge_publish_path.py
backend/.venv/bin/pytest backend/tests/test_p3_06u_26h2w11d_customer_knowledge_publish_path.py -q
cd frontend && npm run typecheck
cd frontend && npm run build
```

## 下一步

进入 H2W-11E：

- 用真实负责人账号逐页走一次知识库运营页。
- 验证客户资料转换、更新包预检、导入、发布前试跑、确认发布、评测、质量报告和本地签收的前端体验。
- 检查是否还有只展示图标但没有真实动作的按钮。
- 检查知识库运营、知识缺口、知识评测三页是否仍有重复入口或客户看不懂的术语。
