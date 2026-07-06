# P2-27 still_missing 失败题短审查

日期：2026-06-27  
阶段：P2-27  
性质：短审查收口，不是新评测工程  
输入文件：`output/evals/p2_26_retrieval_quality_comparison/p2_26_failed_case_delta.csv`

## 0. Stage Card

| 检查项 | 本轮填写 |
| --- | --- |
| 当前阶段编号 | P2-27 |
| 上一阶段真实完成 | P2-26 完成 `top_k=5/8/10/12` 检索对比；默认推荐 `top_k=8`，`top_k=12` 仅作为召回池 |
| 上一阶段没有完成 | 真实客户 50-100 题、真实知识包、生成答案事实性评测、成熟坐席工作台、真实渠道闭环 |
| 本阶段客户可见价值 | 结束 P2 合成评测尾巴，给 P3 真实知识包和真实题库建设提供明确修订方向 |
| 本阶段是否只是评测 | 是，但只做失败题诊断，不新增跑分、报表、导出、历史列表或网格搜索 |
| 本阶段外部风险 | 无真实模型调用、无真实客户数据、无真实平台接入、无外部写入 |
| 验证方式 | 只读检查 P2-26 CSV/JSON 输出，生成本诊断文档，项目文档写回 |
| 写回位置 | Project_012 `执行记录.md`、`文件索引.md`、`复盘与采坑.md` |

## 1. 数据口径说明

路线计划草稿中写的是按 `delta_status=still_missing` 过滤；当前实际 CSV 没有 `delta_status` 字段，权威字段是 `outcome`。

实际字段：

```text
external_case_id, question_hash, source_channel, source_category,
question_type, risk_level, expected_source_uri, expected_chunk_ids_count,
outcome, baseline_top_k, baseline_failure_reason,
baseline_returned_chunk_ids_count, baseline_citation_precision,
first_recovered_top_k, first_recovered_failure_reason,
first_recovered_citation_precision, first_recovered_returned_chunk_ids_count,
final_top_k, final_failure_reason, final_citation_precision,
final_returned_chunk_ids_count
```

本轮按 `outcome=still_missing` 分析。

## 2. P2-26 失败题摘要

| 指标 | 数值 |
| --- | ---: |
| 基线完整证据未召回题 | 32 |
| 扩大 top-k 后 recovered | 14 |
| 到 `top_k=12` 仍 still_missing | 18 |
| regressed | 0 |
| 本轮是否调用外部模型 | 否 |
| 本轮是否写外部平台 | 否 |
| 本轮是否使用真实客户资料 | 否 |

18 道 still_missing 的来源分布：

| 维度 | 分布 |
| --- | --- |
| 来源文档 | `after-sales-v1` 7；`pricing-promotion-v1` 2；`account-privacy-v1` 2；`channel-rules-v1` 2；`logistics-v1` 2；`b2b-integration-v1` 2；`invoice-contract-v1` 1 |
| 业务分类 | 售后退换 7；价格优惠 2；账号隐私 2；渠道规则 2；发货物流 2；企业采购 2；发票合同 1 |
| 风险等级 | medium 8；high 5；low 4；critical 1 |
| final failure reason | `auto_reply_not_allowed` 14；空 2；`expected_source_missing` 1；`expected_terms_missing` 1 |

第一判断：这 18 道不是单一的“top-k 不够大”。`top_k=12` 已经扩大到召回池口径，仍未完整召回，主要问题转向文档结构、chunk 粒度、同源排序、风险题评分口径和少量标注复核。

## 3. Required Bucket Table

下表为非互斥分桶。同一道题可能同时属于多个桶，例如“同源排序不足 + 风险题评分口径耦合”。

| bucket | meaning | cases | fix direction | whether to fix before P3 |
| --- | --- | ---: | --- | --- |
| document_gap | seed 文档缺少足够明确、分章节、可被单题稳定命中的政策段落 | 18 | P3 建真实知识包，不再继续只修合成 seed；按售后、价格、隐私、渠道、物流、企业采购等业务主题重写为可引用政策卡片 | yes |
| chunk_granularity | 期望证据分散在多个 sibling chunk，召回到其中一部分但缺完整证据 | 10 | 调整 chunk 策略、标题继承、相邻 chunk 合并或 evidence compression，避免模型只看到半条政策 | maybe |
| source_ordering | 同源证据没有被排到前面，top source 被跨主题文档抢走 | 7 | 引入 source_uri boost、业务分类 filter、query intent -> source prior、同源证据聚合 | yes |
| risk_noise | 高风险/需人审题的 `auto_reply_not_allowed` 与完整证据召回失败混在一起，导致质量解读变脏 | 14 | 将“人审门禁正确”与“证据是否完整”拆分展示；高风险题不追求自动回复，只要求证据包足以辅助人工 | yes |
| label_issue | 期望 chunk 标注可能过宽、包含标题 chunk、或期望词本身只覆盖 2/3 | 4 | 人工复核 expected terms / expected chunk ids；真实题库阶段必须人工标注，不自动把所有命中词所在 chunk 都设为硬性全召回 | yes |

## 4. Primary Case Taxonomy

| case | category | risk | expected source | expected chunks | observed pattern | primary bucket | P3 action |
| --- | --- | --- | --- | ---: | --- | --- | --- |
| `cs-syn-042` | 售后退换 | critical | `after-sales-v1` | 2 | top source 正确但只召回部分售后证据；风险题正确进入人审 | chunk_granularity | 售后争议/赔付/误回复拆为独立高风险政策卡 |
| `cs-syn-036` | 售后退换 | high | `after-sales-v1` | 2 | top source 被下单支付抢走，售后证据靠后 | source_ordering | 售后意图优先绑定售后源，增加同源 boost |
| `cs-syn-038` | 售后退换 | high | `after-sales-v1` | 2 | top source 正确但缺一块售后证据 | chunk_granularity | 合并退换条件与平台售后流程证据 |
| `cs-syn-047` | 发票合同 | high | `invoice-contract-v1` | 3 | 命中发票合同部分证据，但缺完整三块 | chunk_granularity | 发票、合同、对公风险分别做可引用章节 |
| `cs-syn-010` | 价格优惠 | medium | `pricing-promotion-v1` | 3 | top source 正确但只召回一块价格证据，跨主题噪音较多 | document_gap | 价格、优惠、审批、合同价拆为独立政策卡 |
| `cs-syn-058` | 账号隐私 | high | `account-privacy-v1` | 3 | 隐私源命中但缺身份核验/权限回收完整证据 | chunk_granularity | 隐私/权限/删除请求做单独安全 SOP |
| `cs-syn-061` | 渠道规则 | high | `channel-rules-v1` | 3 | top source 被产品手册抢走，渠道边界证据严重靠后 | source_ordering | 按平台意图优先召回渠道规则文档 |
| `cs-syn-015` | 价格优惠 | medium | `pricing-promotion-v1` | 4 | 期望 4 个 chunk 过宽，top source 被下单支付抢走 | label_issue | 复核价格题 expected chunks，避免把整篇价格文档都当硬性证据 |
| `cs-syn-030` | 发货物流 | medium | `logistics-v1` | 2 | top source 被发票合同抢走，只召回一块物流证据 | source_ordering | 物流意图优先召回物流文档，隔离合同/财务噪音 |
| `cs-syn-034` | 售后退换 | medium | `after-sales-v1` | 2 | 售后源命中但缺另一块完整证据 | chunk_granularity | 售后条件与材料收集合并成客服可用证据包 |
| `cs-syn-041` | 售后退换 | medium | `after-sales-v1` | 3 | 命中售后源两块，但缺三块完整证据 | chunk_granularity | 复核三块硬性证据是否过严 |
| `cs-syn-043` | 售后退换 | medium | `after-sales-v1` | 2 | top source 被产品手册抢走，final precision 仍为 0 | source_ordering | 售后关键词和意图分类必须强约束来源 |
| `cs-syn-027` | 发货物流 | low | `logistics-v1` | 3 | top source 正确但期望三块，可能过宽 | label_issue | 复核低风险物流题是否需要三块证据才算完整 |
| `cs-syn-070` | 企业采购 | medium | `b2b-integration-v1` | 2 | B2B 源命中但缺一块集成/授权证据 | chunk_granularity | B2B 集成、授权、报表、频率限制拆为政策卡 |
| `cs-syn-073` | 企业采购 | medium | `b2b-integration-v1` | 2 | B2B 源命中一块，但同源另一块没上来 | chunk_granularity | 采购/数据授权/系统集成分章并加同源证据聚合 |
| `cs-syn-033` | 售后退换 | low | `after-sales-v1` | 2 | expected 可能包含标题或过短 chunk，实际业务证据命中一部分 | label_issue | 复核是否应把标题 chunk 计入 expected evidence |
| `cs-syn-060` | 账号隐私 | low | `account-privacy-v1` | 2 | top source 被售后抢走，final 为 expected source missing | source_ordering | 隐私/删除/权限类 query 强约束隐私源优先 |
| `cs-syn-064` | 渠道规则 | low | `channel-rules-v1` | 2 | expected terms 只覆盖 2/3，top source 被产品手册抢走 | label_issue | 复核期望词和渠道边界标注；真实题库人工修标 |

## 5. 关键发现

### 5.1 售后退换是 P3 知识包第一优先级

18 道 still_missing 里 7 道来自 `after-sales-v1`。售后题覆盖退换、维修、七天无理由、平台流程、争议、赔付、误回复等多个场景，但当前 seed 文档只有少量段落，chunk 之间没有明确“条件 -> 材料 -> 禁止承诺 -> 人审动作”的结构。

P3 真实知识包应先把售后文档拆成：

- 七天无理由退换条件。
- 超过七天的人工审核条件。
- 软件服务开通后的退款判断。
- 直播/平台订单售后流程。
- 效果预期、赔付、误回复争议的人审 SOP。
- 硬件保修和少配件补发流程。

### 5.2 `auto_reply_not_allowed` 不是坏结果，但会污染证据召回解读

14/18 的 final failure reason 是 `auto_reply_not_allowed`。这些题大多本来就应该进入人工审核，所以不能把它们解释为“客服失败”。正确口径是：

- 人审门禁正确：这是安全能力。
- 证据不完整：这是知识包和检索能力问题。

后续报表应把这两件事拆开。高风险题不应追求自动发送，而应追求“给人工坐席足够完整、低噪音、可引用的证据包”。

### 5.3 top-k 已经不再是主问题

P2-26 证明扩大到 `top_k=12` 仍有 18 道不完整。继续加大 top-k 会进一步降低 citation precision，并把跨主题证据带进上下文。P3 不应再做新的 top-k 网格，而应改：

- 真实知识文档结构。
- source prior / 同源 boost。
- risk evidence isolation。
- evidence compression。
- 人工标注复核。

### 5.4 低风险题也有真实检索问题

`cs-syn-027`、`cs-syn-033`、`cs-syn-060`、`cs-syn-064` 是 low 风险题，不能用“高风险转人工”解释掉。它们暴露的是：

- 期望证据标注可能过宽或包含标题 chunk。
- 同源证据没有稳定排在前面。
- 低风险题如果证据包不完整，后续自动回复仍不安全。

## 6. 本轮不做的事

- 不新增 P2-28。
- 不新增新的评测运行表、报告下载、历史列表或 top-k 网格。
- 不调用百炼、DeepSeek、embedding provider 或任何外部模型。
- 不接真实平台。
- 不写外部渠道。
- 不导入真实客户问题。
- 不修改检索算法。

本轮只完成 P2-27 失败题分桶和 P2 评测尾巴收口。

## 7. P3 进入条件与下一步

P2 synthetic evaluation tail is closed. Further quality work must use real desensitized customer questions or real customer-like knowledge packages.

下一步默认进入 P3-01：

1. 准备真实脱敏 50-100 题模板。
2. 准备真实知识包结构，不再只依赖 P2 合成 seed 文档。
3. 先人工标注期望证据、风险等级、人审边界和禁用话术。
4. 再进入 `rag_model_assisted` 答案事实性评测。

如果必须在 P3 前做一个小修订，只允许修订知识包结构或标注口径，并用一次 before/after 检查，不能扩展为新评测基础设施。
