# P3-06U-26F 真实客户题库与知识包导入模板

日期：2026-07-02  
性质：内部工程记录  
范围：真实客户题库模板、知识包模板、导入字段映射、脱敏校验边界

## 1. 目标

本阶段把 P3-06U-26E 的客服答案质量门禁继续往前推进一步：先把真实客户题库和知识包的输入格式固定下来。

P3-06U-26F 不代表已经拿到客户真实题库，也不代表最终答案事实性已经完成。它交付的是：

- 一个可给客户或内部运营填写的题库模板。
- 一个可承接业务对象、来源引用和发布审核的知识包模板。
- 导入脚本对新字段的兼容映射。
- 静态校验，证明模板不会默认调用模型、不会外发、不会把原始问题写进摘要。

## 2. 新增模板

| 文件 | 用途 |
| --- | --- |
| `evals/p3_06u_26f_real_customer_eval_bank_template.csv` | 真实客户题库填写模板样例，使用客户更容易理解的字段名。 |
| `evals/p3_06u_26f_real_customer_knowledge_package_template.json` | 真实知识包模板，包含版本、负责人、适用渠道、审核要求和 7 类核心知识文档。 |

题库正式导入建议保持 `50-100` 条。少于 50 条很难覆盖风险问题和知识缺口；多于 100 条会显著增加首轮人工标注成本。

当前 CSV 中 8 条只是模板样例，不是客户真实数据，也不是正式验收题库。

## 3. 题库字段

| 字段 | 说明 | 导入映射 |
| --- | --- | --- |
| `external_case_id` | 题号，不放真实订单号、手机号或客户姓名 | `external_case_id` |
| `source_channel` | 来源渠道，例如官网、企微、公众号、抖音、淘宝 | `source_channel` |
| `source_category` | 业务分类 | `source_category` |
| `customer_question` | 已脱敏客户问题 | `question` |
| `expected_answer` | 人工标准答案，用于后续事实性评测 | 当前只做 hash 和离线校验，不写入评测表 |
| `business_object` | 商品、服务、套餐、课程、项目或门店 | 当前只做 hash 和模板覆盖校验 |
| `must_include` | 答案必须包含的事实点 | `expected_terms` |
| `must_not_include` | 禁用承诺、禁用编造或危险话术 | `forbidden_terms` |
| `handoff_expected` | 是否应该转人工 | `expected_human_review` |
| `risk_tags` | 风险标签 | 用于推断 `risk_level` 和校验覆盖 |
| `source_reference` | 答案依据来源 | `expected_source_uri` |
| `expected_document_title` | 期望文档标题 | `expected_document_title` |
| `allow_auto_reply` | 是否允许自动回复 | `allow_auto_reply` |
| `required_citation` | 是否必须引用 | `required_citation` |

## 4. 知识包字段

知识包模板必须包含：

- `template_version`
- `intended_case_count_min=50`
- `intended_case_count_max=100`
- `privacy_boundary`
- `required_case_fields`
- `documents`

每个知识文档必须包含：

- `title`
- `source_uri`
- `owner`
- `version`
- `applies_to_channels`
- `review_required_before_publish`
- `tags`
- `raw_text`

`source_uri` 必须和题库里的 `source_reference` 对齐，否则评测只会得到“问题有标准答案，但没有可引用知识来源”的假阳性。

## 5. 导入脚本增强

`scripts/import_customer_service_eval_bank.py` 已兼容以下别名：

| 新模板字段 | 原评测字段 |
| --- | --- |
| `customer_question` | `question` |
| `must_include` | `expected_terms` |
| `source_reference` | `expected_source_uri` |
| `must_not_include` | `forbidden_terms` |
| `handoff_expected` | `expected_human_review` |

同时新增摘要字段：

- `p3_06u_26f_real_customer_template_supported`
- `business_object_cases`
- `expected_answer_rows`
- `source_reference_covered_cases`

`expected_answer` 和 `business_object` 当前不会直接写进评测表正文；导入器只在 `annotation_notes` 中写 hash，防止摘要或报告意外带出客户标准答案原文。

## 6. 验收命令

```bash
cd /Users/ericlee/Desktop/01_项目工作区/肥肥lu/lite_a_customer_service/standard_ops
.venv/bin/python scripts/check_p3_06u_26f_real_customer_templates.py
backend/.venv/bin/pytest backend/tests/test_customer_service_eval_bank_import_script.py -q
```

模板 dry-run 示例：

```bash
.venv/bin/python scripts/import_customer_service_eval_bank.py \
  evals/p3_06u_26f_real_customer_eval_bank_template.csv \
  --name "P3-06U-26F 真实客户题库模板样例" \
  --description "用于验证真实客户题库字段映射和脱敏边界；8 条只是模板样例。"
```

预期：

- `status=validated`
- `provider_call_performed=false`
- `external_write_performed=false`
- `raw_text_logged=false`
- `summary.expected_answer_rows=8`
- `summary.business_object_cases=8`
- `summary.source_reference_covered_cases=8`

## 7. 边界

- 不导入真实客户原始资料。
- 不调用模型。
- 不调用付费模型。
- 不打开真实外发。
- 不把 8 条模板样例写成真实 50-100 题验收。
- 不把 `expected_answer` 当前 hash 处理写成完整最终答案事实性评测。
- 真实客户题库导入前必须人工脱敏，发现手机号、邮箱、身份证等高置信隐私命中时必须先修正再导入。

## 8. 下一步

进入 P3-06U-26G：渠道官方 sandbox 优先级和 RPA draft-only 研究边界固化。等真实客户提供 50-100 条脱敏题和真实知识包后，再进入最终答案事实性评测和发布前后质量对比。
