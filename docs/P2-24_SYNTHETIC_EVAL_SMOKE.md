# P2-24 合成题库知识检索闭环 Smoke

本文件记录 P2-24 的本地闭环验证：用一组合成业务知识文档承接 P2-23 的 80 条合成脱敏客服验收题库，完成“导入知识文档 -> 导入评测题库 -> 运行检索评测 -> 导出脱敏报告”的最小闭环。

## 新增文件

- `evals/p2_24_seed_knowledge_documents.json`
  - 9 份合成 seed 知识文档。
  - 标题和来源 URI 对齐 P2-23 题库中的 `expected_document_title` 与 `expected_source_uri`。
  - 覆盖产品套餐、渠道规则、价格优惠、下单支付、物流签收、售后退换、发票合同、账号隐私、企业采购与集成。
- `scripts/run_p2_24_synthetic_eval_smoke.py`
  - 使用本地一次性 SQLite 和 FastAPI TestClient。
  - 创建临时租户和 owner。
  - 导入 seed 文档。
  - 使用 `scripts/import_customer_service_eval_bank.py` 校验 P2-23 80 题并创建内部评测集。
  - 运行 `customer_service_retrieval` 评测。
  - 通过报告 API 导出脱敏 Markdown 和 CSV。
- `backend/tests/test_p2_24_synthetic_eval_smoke_script.py`
  - 验证该 smoke 不调用外部模型、不写外部平台、不把原始问题写入结果摘要。

## 运行命令

该脚本依赖后端虚拟环境中的 FastAPI、SQLAlchemy 和 TestClient。请使用项目虚拟环境执行：

```bash
cd /Users/ericlee/Desktop/肥肥lu/lite_a_customer_service/standard_ops
.venv/bin/python scripts/run_p2_24_synthetic_eval_smoke.py \
  --output-dir output/evals/p2_24_synthetic_eval_smoke
```

## 本次结果

2026-06-26 本地 smoke 已生成：

- `output/evals/p2_24_synthetic_eval_smoke/p2_24_synthetic_eval_smoke_summary.json`
- `output/evals/p2_24_synthetic_eval_smoke/customer_service_eval_run_1_review.md`
- `output/evals/p2_24_synthetic_eval_smoke/customer_service_eval_run_1_cases.csv`

核心指标：

| 指标 | 结果 |
| --- | --- |
| seed_document_count | 9 |
| seed_chunk_count | 36 |
| total_cases | 80 |
| hit_rate | 100.0% |
| citation_coverage | 100.0% |
| expected_term_coverage | 78.8% |
| average_confidence | 0.6682 |
| human_review_correctness | 91.2% |
| forbidden_term_hits | 0 |
| unsupported_answer_rate | null |

## 当前判断

P2-24 证明了工程闭环已经可跑：知识文档可以被导入，80 条题库可以创建为内部评测集，检索评测可以落库，脱敏报告可以导出。

但这还不是正式质量验收：

- `expected_term_coverage=78.8%`，说明 seed 文档仍然偏薄，有些题的期望词没有被 top-k 证据完整覆盖。
- `citation_precision=39.8%`，说明 top-k 中有不少跨主题证据，当前 deterministic embedding + lexical reranker 仍比较粗。
- `full_evidence_recall_at_5=0.0%` 是因为 P2-23 题库没有绑定导入后的动态 chunk id；下一步如果要评多证据召回，需要先把运行时 chunk id 回填到评测题。
- `knowledge_gap_rate=0.0%` 只表示检索没有 no-hit；不表示知识缺口题已经被真正解决。知识缺口题当前通过 `allow_auto_reply=false` 进入人工审核，仍需要运营复核。
- 本轮不生成自由文本答案，所以 `unsupported_answer_rate` 仍为 `null`，不能解释为幻觉率为 0。

## 安全边界

- `provider_call_performed=false`
- `external_platform_write_performed=false`
- `raw_text_logged=false`
- 不使用真实客户聊天记录、真实订单、真实平台私信或真实个人身份资料。
- 脱敏报告不导出原始问题或命中知识片段原文。

## 下一步

1. 把 seed 文档从“覆盖术语”升级为更接近真实企业知识库的分章节文档。
2. 做 chunk id 回填版题库，让 `expected_chunk_ids` 真正参与多证据召回评测。
3. 增加运行对比报告：同一题库在知识修订前后比较 `expected_term_coverage`、`citation_precision`、`human_review_correctness`。
4. 在检索质量稳定后，再进入 `rag_model_assisted`：只允许模型基于检索证据生成带引用草稿，并做答案事实性复核。
