# P2-25 chunk id 回填评测对比

本文件记录 P2-25 的本地评测增强：在 P2-24 已跑通“合成 seed 知识文档 -> 80 题合成脱敏题库 -> 检索评测 -> 脱敏报告”之后，进一步把题库中的 `expected_chunk_ids` 从空值变成运行时可解释的真实 chunk id。

## 为什么做

P2-24 的 `full_evidence_recall_at_5=0.0%` 不是检索系统已经失败，而是因为 P2-23 题库没有绑定导入后的动态 chunk id。

这会带来一个问题：我们只能知道“有没有命中来源文档、有没有 citation、期望词有没有覆盖”，但无法回答更关键的问题：

- top-k 里是否找到了应该找的具体证据块？
- 多证据问题是不是只找到了其中一部分？
- 后续修改知识文档后，完整证据召回有没有变好？
- 如果接模型生成，模型看到的证据是不是足够完整？

P2-25 的目标不是直接提高召回率，而是让完整证据召回指标变成可审计、可对比、可持续优化。

## 新增文件

- `scripts/run_p2_25_chunk_backfill_eval_comparison.py`
  - 使用本地一次性 SQLite 和 FastAPI TestClient。
  - 导入 P2-24 的 9 份合成 seed 知识文档。
  - 读取每份文档实际生成的 chunk id。
  - 创建原始题库基线评测集。
  - 按 `expected_source_uri + expected_terms` 动态回填 `expected_chunk_ids`。
  - 创建 chunk 回填版评测集。
  - 对比两次运行指标，并导出脱敏报告和回填绑定表。
- `backend/tests/test_p2_25_chunk_backfill_eval_comparison_script.py`
  - 验证 P2-25 能让 `full_evidence_cases` 从 0 变成可计算样本。
  - 验证无外部模型调用、无外部平台写入、摘要不包含原始问题。

## 运行命令

```bash
cd /Users/ericlee/Desktop/肥肥lu/lite_a_customer_service/standard_ops
.venv/bin/python scripts/run_p2_25_chunk_backfill_eval_comparison.py \
  --output-dir output/evals/p2_25_chunk_backfill_eval_comparison
```

## 本次输出

2026-06-27 本地输出位于：

- `output/evals/p2_25_chunk_backfill_eval_comparison/p2_25_chunk_backfill_eval_comparison_summary.json`
- `output/evals/p2_25_chunk_backfill_eval_comparison/p2_25_chunk_backfill_eval_comparison.md`
- `output/evals/p2_25_chunk_backfill_eval_comparison/p2_25_chunk_backfill_case_bindings.csv`
- `output/evals/p2_25_chunk_backfill_eval_comparison/customer_service_eval_run_2_review.md`
- `output/evals/p2_25_chunk_backfill_eval_comparison/customer_service_eval_run_2_cases.csv`

这些输出均为合成脱敏评测材料，不包含真实客户聊天、真实订单、真实平台私信或个人身份资料。

## 本次指标

| 指标 | 原始题库 | chunk 回填题库 | 变化 |
| --- | ---: | ---: | ---: |
| total_cases | 80 | 80 | 0 |
| bound_case_count | 0 | 76 | +76 |
| full_evidence_cases | 0 | 76 | +76 |
| full_evidence_recall_at_5 | 0.0% | 57.9% | +57.9% |
| hit_rate | 100.0% | 100.0% | 0 |
| citation_coverage | 100.0% | 100.0% | 0 |
| expected_term_coverage | 78.8% | 78.8% | 0 |
| citation_precision | 39.8% | 39.8% | 0 |
| human_review_correctness | 91.2% | 91.2% | 0 |
| forbidden_term_hits | 0 | 0 | 0 |

## 如何回填

回填逻辑不依赖检索结果本身，避免“用答案定义答案”。

当前规则：

1. 读取每个 case 的 `expected_source_uri`。
2. 在导入后的知识文档 chunk 中找到同一 `source_uri` 的 chunk。
3. 用 case 的 `expected_terms` 扫描对应 source 的 chunk content。
4. 命中期望词的 chunk id 写入 `expected_chunk_ids`。
5. 缺少 `expected_source_uri` 的知识缺口题不回填。

本次结果：

- 76 题成功绑定 chunk id。
- 4 题未绑定，原因是这些题本身是知识缺口题，没有 `expected_source_uri`。
- 本轮没有使用 source 首块兜底，76 题都是基于期望词命中绑定。
- 共生成 155 条 expected chunk 链接，单题最多绑定 4 个 chunk。

## 如何解读

P2-25 的结论比较克制：

- 好消息：`full_evidence_recall_at_5` 已经从不可解释指标变成可解释指标。
- 风险：回填后只有 `57.9%` 的完整证据召回，说明 top-k 对具体 chunk 的完整覆盖还不够。
- 不变：`expected_term_coverage`、`citation_precision` 和 `human_review_correctness` 没有因为回填自动提升，因为本次只是改变评测标注，不是改变检索算法或知识内容。
- 重要边界：本轮仍不生成自由文本答案，因此 `unsupported_answer_rate=null` 不能解释为幻觉率为 0。

## 下一步

1. 先看 `p2_25_chunk_backfill_case_bindings.csv` 和 `customer_service_eval_run_2_cases.csv`，找出 `full_evidence_recalled_at_5=false` 的题。
2. 分析失败原因是 seed 文档太薄、chunk 太碎、top-k 太小、词法召回噪音，还是 reranker 规则太粗。
3. 做 P2-26：评测运行对比和知识文档修订实验，先提高 `full_evidence_recall_at_5` 与 `citation_precision`。
4. 只有检索证据稳定后，再进入 `rag_model_assisted`，让模型基于检索证据生成带引用草稿，并加入人工事实性复核。

## 安全边界

- `provider_call_performed=false`
- `external_platform_write_performed=false`
- `raw_text_logged=false`
- `raw_text_included=false`
- 只写本地一次性内部测试数据库和本地输出目录。
- 不使用真实客户资料，不触达真实渠道，不消耗真实模型 API。
