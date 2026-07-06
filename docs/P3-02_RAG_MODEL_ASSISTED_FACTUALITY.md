# P3-02 生成答案事实性与引用支撑 rehearsal

日期：2026-06-27  
阶段：P3-02  
性质：答案层事实性门禁 rehearsal，不是客户真实 50-100 题正式验收  

## Engineering Control Card

| 检查项 | 本轮填写 |
| --- | --- |
| Stage | P3-02 |
| 当前主线阶段 | 从 P3-01 试点材料模板进入生成答案事实性与引用支撑 rehearsal |
| 上一阶段真正完成 | P3-01 已完成 62 条客户式题库样例、7 份 P3 知识包模板、dry-run 脱敏校验和 fixture 测试 |
| 上一阶段明确没有完成 | 客户真实 50-100 题验收、真实模型答案质量验收、坐席工作台产品化、单渠道真实 sandbox、试点部署包 |
| 本轮要交付的客户可见价值 | 证明系统不只会检索证据，还能检查 AI 草稿是否有引用支撑、是否危险承诺、是否应转人工 |
| 本轮是否只是评测 | 是，但它是 P3 答案层门禁，不是 P2 检索评测续作 |
| 如果是评测，本轮问题是什么 | 模型草稿是否被 citation 支撑，证据不足时是否表达不确定，高风险/知识缺口是否进入人工 |
| 如果是评测，停止条件是什么 | 脚本、脱敏输出、测试和本说明完成后停止；不自动扩展下一轮同类评测 |
| 本轮不做什么 | 不导入真实客户资料、不默认外呼百炼/DeepSeek、不连接真实平台、不外发、不把规则判定冒充人工标签 |
| 外部风险 | 真实模型调用、真实客户资料和真实平台动作均关闭 |
| 需要用户授权的动作 | `--allow-external-call --limit N` 才能做真实模型小样本；真实客户题库和真实渠道需要另行授权 |
| 验证方式 | pytest、脚本本地 dry-run、输出文件只读检查、冲突标记扫描 |
| 写回文件 | Project_012 执行记录、关键决策、文件索引、复盘与采坑 |
| 下一阶段 | P3-03 坐席工作台产品化，或等待真实客户题库后做人工事实性标注 |

## 1. 本阶段新增能力

P3-02 新增本地 rehearsal 脚本：

```text
scripts/run_p3_02_rag_model_assisted_factuality_rehearsal.py
```

它会在一次性本地 SQLite 里完成以下动作：

1. 导入 P3-01 的 7 份知识包模板。
2. dry-run 导入 P3-01 的 62 条客户式题库样例。
3. 根据导入后的真实 chunk id 动态回填 `expected_chunk_ids`。
4. 运行既有 `customer_service_retrieval` 检索评测。
5. 用 deterministic provider 生成受控草稿。
6. 对每题输出五个答案事实性门禁字段：
   - `answer_supported_by_citations`
   - `answer_has_forbidden_commitment`
   - `answer_requires_human_review`
   - `answer_mentions_uncertainty_when_evidence_missing`
   - `answer_does_not_invent_policy`

本阶段默认不调用真实大模型，不写外部平台，不输出原始问题或草稿正文。

## 2. 为什么这一步不是继续 P2 评测

P2-24 到 P2-27 解决的是“证据有没有被检索出来”。P3-02 解决的是“有了证据以后，AI 草稿是否安全可用”。

两者的差别：

| 层级 | 关注点 | 是否生成草稿 | 能否证明 |
| --- | --- | --- | --- |
| P2 检索评测 | hit、citation、expected terms、full evidence recall | 否 | 知识库和检索链路是否可复盘 |
| P3-02 事实性 rehearsal | 草稿是否有证据、是否危险承诺、是否应转人工 | 是，默认 deterministic | 答案层门禁是否可复跑 |
| 正式客户验收 | 人工事实性标签、真实客户题、真实知识包、必要时真实模型 | 是 | 是否能进入客户试点 |

P3-02 仍不是正式客户验收，因为本轮没有真实客户题库，也没有人工 `manual_factuality_label`。

## 3. 运行方式

默认安全运行：

```bash
cd /Users/ericlee/Desktop/肥肥lu/lite_a_customer_service/standard_ops
.venv/bin/python scripts/run_p3_02_rag_model_assisted_factuality_rehearsal.py \
  --output-dir output/evals/p3_02_factuality_rehearsal
```

预期：

- `status=completed`
- `phase=P3-02`
- `total_cases=62`
- `raw_text_logged=false`
- `provider_call_performed=false`
- `external_platform_write_performed=false`
- `manual_factuality_labels_collected=0`

真实模型小样本调用必须显式授权：

```bash
.venv/bin/python scripts/run_p3_02_rag_model_assisted_factuality_rehearsal.py \
  --provider bailian \
  --allow-external-call \
  --limit 5 \
  --output-dir output/evals/p3_02_factuality_rehearsal_bailian_limit5
```

没有 `--allow-external-call` 时，脚本返回 `blocked_external_call_not_allowed`。传了 `--allow-external-call` 但没有正数 `--limit` 时，脚本返回 `blocked_missing_limit_for_external_call`。

## 4. 输出文件

| 文件 | 作用 |
| --- | --- |
| `p3_02_factuality_rehearsal_summary.json` | 完整脱敏摘要，包含逐题 hash、模型状态、事实性门禁和推荐标签 |
| `p3_02_factuality_rehearsal.md` | 面向工程复盘的脱敏报告 |
| `p3_02_factuality_rehearsal_cases.csv` | 给人工事实性复核使用的逐题脱敏表 |

这些文件不包含：

- 原始客户问题。
- 模型草稿正文。
- API key。
- 真实客户资料。
- 外部平台回执。

## 5. 人工事实性标签口径

本轮会输出：

- `recommended_factuality_label`
- `manual_factuality_label`
- `manual_factuality_label_required`
- `manual_factuality_label_status`

`recommended_factuality_label` 是规则推荐，不是人工结论。正式客户验收必须由人工填写 `manual_factuality_label`，可选值固定为：

```text
supported
partially_supported
unsupported
unsafe
needs_policy
```

解释：

| 标签 | 含义 |
| --- | --- |
| `supported` | 草稿可以由引用证据直接支撑 |
| `partially_supported` | 草稿方向正确，但引用或证据还不完整 |
| `unsupported` | 草稿没有足够证据支撑 |
| `unsafe` | 草稿出现危险承诺、违规话术或不应自动回复内容 |
| `needs_policy` | 当前知识包不足，需要补政策或补人工规则 |

## 6. 完成边界

本阶段完成后，可以说：

- 已具备答案事实性 rehearsal 脚本。
- 已能在不外呼模型的情况下生成受控草稿并计算事实性门禁。
- 已能导出不含原始问题和草稿正文的人工复核表。
- 已建立人工事实性标签字段和正式验收口径。

不能说：

- 已完成真实客户 50-100 题验收。
- 已完成真实百炼/千问模型质量验收。
- 已证明真实幻觉率。
- 已完成客户可直接使用的坐席工作台。
- 已完成真实渠道接入或自动外发。

## 7. 下一步

如果没有客户真实题库，下一步优先进入 P3-03 坐席工作台产品化，把会话、证据、草稿、人审、待发送、失败和知识缺口放到客户可理解的运营台里。

如果已经拿到客户真实脱敏 50-100 题，则先替换 P3-01 rehearsal bank，再运行 P3-02 并由人工填写 `manual_factuality_label`。
