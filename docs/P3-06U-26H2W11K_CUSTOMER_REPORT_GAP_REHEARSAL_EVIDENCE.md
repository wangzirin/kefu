# H2W-11K 客户质量报告缺口演练证据汇入

## 结论

H2W-11K 已把 H2W-11J 的缺口样本本地演练结果汇入客户质量报告链路。质量报告现在可以结构化展示：

- 缺口样本本地演练共 7 条。
- 5 条自动回复样本为 `correct`。
- 2 条转人工样本为 `not_applicable`。
- 自动回复事实性、引用充分、禁用承诺通过、转人工正确性四项本地演练率均为 1.0。
- 演练结果可进入客户质量报告复核页。

这不是正式客户准确率签收，也不是线上平台外发验收。

## 已完成

1. 后端 `CustomerQualityReportRead` 新增 `gap_rehearsal_evidence`。
2. 后端质量报告生成逻辑读取 `output/p3_06u_26h2w11j_gap_final_answer_rehearsal/summary.json`。
3. 客户质量报告摘要、指标、复盘章节、签收前动作、签收检查项和数据边界都能带上缺口演练证据。
4. HTML、XLSX、DOCX 导出件同步带上缺口样本本地演练证据。
5. 前端质量复盘页的客户质量报告区新增“缺口样本本地演练证据”卡片。
6. 新增 H2W-11K 门禁脚本和 pytest，防止把本地演练误写成正式签收。

## 客户报告中的表达边界

客户质量报告可以展示本地演练结果，但必须同时展示以下边界：

- 不是正式客户准确率签收。
- 真实外发继续关闭。
- 不调用真实模型。
- 不连接真实平台。
- 不导出完整最终答案正文。
- 正式签收仍需客户确认标准答案、真实题库、线上回执、失败重试和审计闭环。

## 验收门禁

H2W-11K 通过必须满足：

- H2W-11J summary 为 `passed`。
- `ready_for_gap_quality_report_review=true`。
- `ready_for_formal_accuracy_signoff=false`。
- `provider_call_performed=false`。
- `real_platform_send_performed=false`。
- `external_platform_write_performed=false`。
- `final_answer_text_exported=false`。
- 前端存在 `data-h2w11k-gap-rehearsal-evidence`。
- 客户质量报告页面明确写出不是正式准确率签收。

## 停止门禁

出现任一情况必须停止推进：

- 把 H2W-11J 或 H2W-11K 写成正式客户准确率签收。
- 客户报告导出完整最终答案正文。
- UI 写成已真实外发、已接真实平台、已完成线上回执。
- H2W-11J 的缺口标签没有通过，或缺口标签含客户确认状态。
- 真实外发、真实 IM、正式电子签章或客户原始数据被误打开。

## 下一步

下一阶段继续保持两条线：

1. 质量线：补客户确认标准答案、真实题库、线上回执和正式报告签收。
2. 渠道线：企业微信、公众号、电商等真实接入只在官方授权、验签、解密、白名单和回执审计具备后另开专项。
