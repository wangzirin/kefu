# P3-06U-26H2W7C 最终答案质量治理第一片

日期：2026-07-04

## 定位

H2W-7C 的目标不是新增一个新的知识评测系统，而是把现有“知识检索评测”继续往客服真实使用口径推进：最终客服答案必须能看到样本、人工事实性标签、引用充分性、禁用承诺检查、转人工判断和引用快照。本片不是完整线上准确率，只是把答案质量证据接入统一治理链路。

本片完成的是第一片治理闭环：让最终答案样本与 `reply_citation_snapshots` 绑定，并让 RAG 治理摘要输出 `answer_quality` 与 `final_answer_quality` 门禁。

## 已完成

- 最终答案采样时写入引用快照。
- 有引用 URI 时写 `final_answer_citation_uri` 快照。
- 无引用 URI 时写 `final_answer_no_citation` 快照，并记录 `final_answer_sample_without_citation`。
- 引用快照只保存 URI、hash、文档 ID、版本和审计元数据，不把原始客服答案明文写入快照。
- 同一评测用例重复采样时，会替换该用例已有的最终答案引用快照，避免重复堆积。
- RAG 治理摘要新增 `answer_quality`。
- RAG 门禁新增 `final_answer_quality`。
- 治理摘要明确区分“检索评测”和“最终客服答案质量”，避免把检索命中包装成完整线上准确率。

## 质量口径

`answer_quality` 当前读取最近一次评测运行的 `knowledge_evaluation_run_cases.result_payload` 和 `reply_citation_snapshots`：

- 最终答案采样覆盖率：是否采集了最终客服答案样本。
- 最终答案事实性：人工标注 `correct`、`partially_correct`、`incorrect`、`needs_human_review`。
- 引用充分性：人工标注引用是否足够支撑答案。
- 禁用承诺：检查是否出现不该承诺的赔付、疗效、法律、金融等内容。
- 转人工正确性：应转人工时是否正确转人工。
- 引用快照数量：最终答案样本是否落到了统一引用账本。

只有当全部评测用例都完成样本、事实性标签、引用充分性、禁用承诺和转人工标签时，`complete_accuracy_measured` 才会为 `true`。

## 仍未完成

- 还没有达到 50-100 条真实脱敏题库 rehearsal。
- 还没有把该质量摘要完整接入前端图表。
- 还没有做生产级向量库、rerank 和供应商账单对账。
- 真实外发继续关闭，真实渠道外发也继续关闭。
- 真实平台自动回复仍需官方授权、测试白名单、验签、回执、失败重试和审计闭环。

## 停止门禁

- 只测检索命中，不测最终答案，不允许写成“客服准确率已完成”。
- 高置信答案没有引用快照或无引用原因，不允许进入自动回复封版。
- 没有人工事实性标签，不允许输出完整线上准确率。
- 引用只有文件名，没有 URI、hash、版本或快照，不允许作为签收证据。
- RPA、模拟点击、Cookie、Hook 和个人号外挂不进入正式默认交付链。

## 验收命令

```bash
python3 scripts/check_p3_06u_26h2w7c_answer_quality_governance.py
python3 scripts/check_p3_06u_26h2w7b_model_cost_budget_gate.py
python3 scripts/check_p3_06u_26h2w7x_reply_provenance.py
python3 scripts/check_p3_06u_26h2w7_rag_cost_governance.py
pytest backend/tests/test_knowledge_evaluations_api.py backend/tests/test_rag_cost_governance_api.py
```

## 下一步

优先把 `answer_quality` 接入前端模型路由或质量复盘页，让客户能看到“当前只是检索评测，还是已经完成最终答案人工复核”。之后再推进 H2W-8A/8B 本地首次部署与维护闭环，最后用 50-100 条真实脱敏题库做 H2W-11 受控试点 rehearsal。
