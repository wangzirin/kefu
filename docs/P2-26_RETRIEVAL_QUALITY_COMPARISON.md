# P2-26 检索质量参数对比

本文件记录 P2-26 的本地检索参数对比：在 P2-25 已经把 `expected_chunk_ids` 动态回填到 80 条合成脱敏客服题库后，继续使用同一批 seed 知识文档和同一批题，对 `top_k=5/8/10/12` 做可重复运行的质量对比。

## 为什么做

P2-25 让 `full_evidence_recall_at_5` 从不可解释的 0.0% 变成可审计的 57.9%，但它没有回答一个工程问题：完整证据召回低，是不是单纯因为 top-k 太小？

P2-26 的目标是先用本地实验量化这个问题：

- 扩大 top-k 是否能找回更多期望 chunk？
- 扩大 top-k 会不会明显拉低 citation precision？
- 扩大 top-k 是否会把风险词、无关证据或跨主题内容带进证据集合？
- 对当前系统来说，默认检索上下文应该设多少，召回池又应该设多少？

本轮仍然不进入模型生成答案，不评测自由文本事实性，也不把 `unsupported_answer_rate=null` 解读为幻觉率为 0。

## 新增文件

- `scripts/run_p2_26_retrieval_quality_comparison.py`
  - 复用 P2-24 的本地一次性 SQLite、FastAPI TestClient、seed 文档导入和脱敏报告 API。
  - 复用 P2-25 的 `expected_source_uri + expected_terms -> expected_chunk_ids` 动态回填逻辑。
  - 对同一个回填版评测集按多个 top-k 重复运行。
  - 输出每组 top-k 的完整证据召回、引用精度、期望词覆盖、人审判断和禁用词证据命中。
  - 输出基线失败题中哪些被扩大 top-k 救回，哪些到最大 top-k 仍失败。
- `backend/tests/test_p2_26_retrieval_quality_comparison_script.py`
  - 验证脚本不调用外部模型、不写外部平台、不把原始问题写进结果摘要。
  - 验证至少比较 5/8/10 三组 top-k，并输出失败题 delta。
- `output/evals/p2_26_retrieval_quality_comparison/`
  - 生成本地 summary JSON、Markdown 对比报告、失败题 delta CSV 和推荐 top-k 对应的脱敏报告。

## 运行命令

```bash
cd /Users/ericlee/Desktop/肥肥lu/lite_a_customer_service/standard_ops
.venv/bin/python scripts/run_p2_26_retrieval_quality_comparison.py \
  --output-dir output/evals/p2_26_retrieval_quality_comparison
```

可自定义 top-k：

```bash
.venv/bin/python scripts/run_p2_26_retrieval_quality_comparison.py \
  --top-ks 5,8,10,12 \
  --output-dir output/evals/p2_26_retrieval_quality_comparison
```

## 本次输出

2026-06-27 本地输出位于：

- `output/evals/p2_26_retrieval_quality_comparison/p2_26_retrieval_quality_comparison_summary.json`
- `output/evals/p2_26_retrieval_quality_comparison/p2_26_retrieval_quality_comparison.md`
- `output/evals/p2_26_retrieval_quality_comparison/p2_26_failed_case_delta.csv`
- `output/evals/p2_26_retrieval_quality_comparison/customer_service_eval_run_2_review.md`
- `output/evals/p2_26_retrieval_quality_comparison/customer_service_eval_run_2_cases.csv`

这些输出均为合成脱敏评测材料，不包含真实客户聊天、真实订单、真实平台私信或个人身份资料。

## 本次指标

| top_k | full_evidence_recall_at_k | full_evidence_covered_cases | citation_precision | expected_term_coverage | human_review_correctness | forbidden_term_hits |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 5 | 57.9% | 44/76 | 39.8% | 78.8% | 91.2% | 0 |
| 8 | 67.1% | 51/76 | 32.2% | 83.8% | 93.8% | 2 |
| 10 | 72.4% | 55/76 | 29.9% | 85.0% | 93.8% | 3 |
| 12 | 76.3% | 58/76 | 27.8% | 85.0% | 93.8% | 3 |

失败题变化：

- 基线 top-k：5。
- 基线完整证据未召回题数：32。
- 扩大 top-k 后转为完整召回题数：14。
- 到 top-k=12 仍未完整召回题数：18。
- 扩大 top-k 后回退题数：0。

## 如何解读

本轮结果证明：top-k 太小确实是当前完整证据召回不足的原因之一，但不是唯一原因。

扩大 top-k 的收益很明确：

- `top_k=5 -> 8`：完整证据召回从 57.9% 提升到 67.1%，救回 7 道完整证据题，期望词覆盖从 78.8% 到 83.8%。
- `top_k=8 -> 10`：召回继续提升到 72.4%，但引用精度继续下降。
- `top_k=10 -> 12`：召回提升到 76.3%，但期望词覆盖没有继续增长，citation precision 降到 27.8%。

扩大 top-k 的代价也很明确：

- citation precision 从 39.8% 降到 32.2%、29.9%、27.8%。
- 从 top-k=8 开始出现禁用词证据命中，说明更宽的召回集合会带来安全噪音。
- 直接把 10 或 12 条证据塞给模型生成，可能让模型看到更多跨主题或风险证据。

因此本轮不推荐简单把生产默认 top-k 拉到 12。

## 当前工程结论

当前推荐采用双层策略：

1. 生产默认检索上下文先用 `top_k=8`。
   - 相对 top-k=5，完整证据召回提升 9.2 个百分点。
   - 引用精度下降控制在 8 个百分点以内。
   - 禁用词证据命中控制在 2。
2. `top_k=12` 只作为召回池或后续重排实验候选。
   - 它有最高完整证据召回 76.3%。
   - 但 citation precision 只有 27.8%，不适合直接作为模型上下文。
3. 进入模型生成前，必须先补更强的二阶段筛选：
   - 同源证据 boost。
   - 风险词证据降权或隔离。
   - 多证据题的期望 source 覆盖检查。
   - 引用证据压缩，只把最相关的 3-5 个 chunk 交给模型。

## 仍未解决的问题

P2-26 仍有 18 道题到 top-k=12 都没有完整召回。这说明后续不能只调参数，还要继续拆解：

- seed 文档是否太薄，导致期望词分散或缺少明确段落。
- chunk 粒度是否不合理，标题 chunk 和正文 chunk 是否把证据拆散。
- lexical reranker 是否过粗，没有把同一来源的关键 chunk 排在一起。
- 风险、人审和售后题是否需要单独的政策型检索模板。
- 知识缺口题是否应进入单独的缺口修复流，而不是混在普通检索指标里。

## 下一步

建议 P2-27 继续做两件事：

1. 失败题分桶：按 `p2_26_failed_case_delta.csv` 把 18 道 still_missing case 分成“文档缺口、chunk 粒度、同源排序、风险词噪音、标注复核”几类。
2. 做知识文档和重排规则对比：
   - 先修订 seed 文档结构，增加更明确的章节和政策卡片。
   - 再增加同源 boost / 风险证据隔离的 reranker 实验。
   - 继续使用同一 80 题跑 before/after，对比 `full_evidence_recall_at_k`、`citation_precision`、`expected_term_coverage` 和 `forbidden_term_hits`。

只有检索证据稳定后，再进入 `rag_model_assisted` 生成答案事实性评测。

## 安全边界

- `provider_call_performed=false`
- `external_platform_write_performed=false`
- `raw_text_logged=false`
- `raw_text_included=false`
- 只写本地一次性内部测试数据库和本地输出目录。
- 不使用真实客户资料，不触达真实渠道，不消耗真实模型 API。
