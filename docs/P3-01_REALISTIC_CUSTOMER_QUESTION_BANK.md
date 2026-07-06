# P3-01 真实脱敏题库与真实知识包模板

日期：2026-06-27  
阶段：P3-01  
性质：真实试点材料准备，不是 P2 合成评测续作  

## Engineering Control Card

| 检查项 | 本轮填写 |
| --- | --- |
| Stage | P3-01 |
| 当前主线阶段 | 从 P2 检索评测收口转入 P3 真实试点材料闭环 |
| 上一阶段真正完成 | P2-27 已完成 18 道 `outcome=still_missing` 失败题短审查，P2 合成评测尾巴关闭 |
| 上一阶段明确没有完成 | 真实客户 50-100 题、真实知识包、生成答案事实性、坐席工作台产品化、真实渠道试点 |
| 本轮要交付的客户可见价值 | 形成客户可理解、可填写、可验收的题库模板和知识包模板，后续可直接进入试点资料收集 |
| 本轮是否只是评测 | 否。本轮只做材料模板、样例题库和 dry-run 校验 |
| 本轮不做什么 | 不导入真实客户资料、不调用模型、不连接平台、不新增 P2-28、不写外部系统 |
| 外部风险 | 无外部调用；主要风险是把样例题库误当真实客户验收，本文档明确禁止 |
| 需要用户授权的动作 | 真实客户数据导入、真实模型调用、真实平台账号接入、真实外发都需要另行授权 |
| 验证方式 | `import_customer_service_eval_bank.py` dry-run、pytest fixture 校验、冲突标记扫描 |
| 写回文件 | Project_012 执行记录、文件索引、复盘与采坑 |
| 下一阶段 | P3-02 生成答案事实性与引用评测 |

## 1. 本阶段产物

| 文件 | 作用 |
| --- | --- |
| `evals/p3_01_realistic_customer_service_eval_bank_62_2026-06-27.csv` | 62 条真实客户式试点题库样例，用于验证字段、分布、脱敏校验和知识包覆盖。它不是客户真实聊天记录。 |
| `evals/p3_01_realistic_knowledge_package_template.json` | 真实知识包模板，定义 P3 试点所需的 7 份核心知识文档、稳定 `source_uri`、标题、标签和原始文本结构。 |
| `evals/customer_service_eval_bank_template.csv` | 仍作为客户正式填写模板，字段与导入脚本保持兼容。 |
| `scripts/import_customer_service_eval_bank.py` | 题库导入与脱敏 dry-run 工具，默认不写库、不打印原始问题、不调用模型、不写外部平台。 |

## 2. 重要口径

P3-01 不再围绕 P2 的 80 条合成题刷指标。它的任务是建立真实试点资料的收集格式。

当前新增的 62 条题是“真实客户式样例题库”，用于：

- 验证字段是否完整。
- 验证分布是否接近真实试点。
- 验证脱敏 dry-run 能跑通。
- 验证知识包 source_uri 和业务主题是否覆盖核心客服场景。

它不能用于对外宣称：

- 已完成真实客户 50-100 题验收。
- 已证明真实准确率。
- 已证明真实幻觉率。
- 已完成客户真实知识库验收。

真正客户试点时，应复制模板并替换为客户提供或从客户历史问题中脱敏后的真实问题。

## 3. 题库字段

客户正式题库必须保留以下字段：

| 字段 | 必填 | 说明 |
| --- | --- | --- |
| `external_case_id` | 是 | 客户侧题号或内部题号，不放真实订单号、手机号或客户姓名 |
| `source_channel` | 是 | 入口，例如 `web_widget`、`wecom`、`official_account`、`douyin`、`xiaohongshu`、`taobao` |
| `source_category` | 是 | 业务分类，例如售前咨询、价格套餐优惠、交付部署周期、售后退款赔付 |
| `question` | 是 | 已脱敏问题，不含手机号、邮箱、身份证、真实订单号、地址、账号、平台昵称 |
| `question_type` | 是 | 可计算问题类型，例如 `pre_sales_consultation`、`pricing_package`、`risk_legal` |
| `expected_terms` | 是 | 期望证据中应出现的关键词，用分号分隔 |
| `expected_source_uri` | 知识缺口题可空 | 期望引用知识来源，必须和知识包 `source_uri` 对齐 |
| `expected_document_title` | 建议 | 期望文档标题，便于人工复核 |
| `expected_chunk_ids` | 可空 | 真实导入后再动态回填，不建议客户手填 |
| `must_have_all_evidence` | 是 | 是否必须召回全部期望 chunk |
| `expected_human_review` | 是 | 是否应该进入人工审核 |
| `allow_auto_reply` | 是 | 是否允许自动回复 |
| `forbidden_terms` | 建议 | 不允许模型或坐席草稿出现的危险承诺，用分号分隔 |
| `risk_level` | 是 | `low`、`medium`、`high`、`critical` |
| `required_citation` | 是 | 是否必须有引用 |
| `priority` | 是 | 复核优先级，数字越小越优先 |
| `status` | 是 | `active`、`draft` 或 `archived` |
| `annotation_notes` | 是 | 标注说明，不写真实隐私 |

## 4. 推荐分布

P3 第一个正式客户题库建议 50-100 条。少于 50 条很难覆盖高风险和知识缺口，多于 100 条会增加首轮人工标注成本。

| 类型 | 目标数量 |
| --- | ---: |
| 售前咨询 | 10-15 |
| 价格/套餐/优惠 | 8-12 |
| 交付/部署/周期 | 8-12 |
| 售后/退款/赔付 | 8-12 |
| 账号/权限/发票 | 5-8 |
| 渠道接入/平台规则 | 8-12 |
| 投诉/高风险/法务 | 5-10 |
| 知识缺口/不确定问题 | 5-10 |
| 闲聊/无关/恶意诱导 | 5-8 |

本阶段样例题库使用 62 条，覆盖以上所有类型。它是客户式 rehearsing bank，不是客户真实数据。

## 5. 知识包模板

P3 第一版真实知识包至少包含：

| source_uri | 文档标题 | 作用 |
| --- | --- | --- |
| `internal://docs/p3/product-scope-v1` | 产品与服务范围说明 | 回答系统能做什么、不能做什么、入门/标准/企业版边界 |
| `internal://docs/p3/pricing-package-v1` | 套餐价格与商务规则 | 回答报价、优惠、升级、模型调用费和商务审批 |
| `internal://docs/p3/delivery-deployment-v1` | 交付部署与试点流程 | 回答交付周期、资料准备、渠道准备、上线回滚 |
| `internal://docs/p3/support-refund-v1` | 售后退款与服务变更规则 | 回答退款、暂停、模型切换、争议处理 |
| `internal://docs/p3/account-invoice-security-v1` | 账号权限发票与数据安全规范 | 回答权限隔离、发票、数据导出、隐私请求 |
| `internal://docs/p3/channel-compliance-v1` | 官方渠道接入与平台边界 | 回答企微、公众号、官网、电商/内容平台接入边界 |
| `internal://docs/p3/risk-legal-v1` | 高风险投诉与法务审核规范 | 回答赔付、合同、投诉、法务和舆情问题的转人工边界 |

真实客户交付时，每份知识文档应增加：

- 版本号。
- 负责人。
- 适用客户和适用渠道。
- 生效时间和失效条件。
- 禁用话术。
- 需要人工审核的触发条件。
- 最近一次审核记录。

## 6. Dry-run 校验命令

实际脚本使用位置参数，不使用 `--file`。

```bash
cd /Users/ericlee/Desktop/肥肥lu/lite_a_customer_service/standard_ops
.venv/bin/python scripts/import_customer_service_eval_bank.py \
  evals/p3_01_realistic_customer_service_eval_bank_62_2026-06-27.csv \
  --name "P3-01 真实客户式试点题库样例 62题" \
  --description "用于验证 P3-01 真实脱敏题库字段、分布和脱敏 dry-run 的客户式样例，不含真实客户身份或真实订单资料。"
```

预期：

- `status=validated`
- `summary.total_cases=62`
- `summary.sensitive_row_count=0`
- `raw_text_logged=false`
- `provider_call_performed=false`
- `external_write_performed=false`

如果真实客户题库 dry-run 返回 `blocked_sensitive_rows`，必须人工脱敏后重跑，不能用 `--allow-sensitive-rows` 绕过正式流程。

## 7. P3-01 完成边界

本阶段完成后，可以说：

- 已有真实客户题库字段模板。
- 已有 62 条客户式样例题库用于内部 rehearsal。
- 已有真实知识包 JSON 模板。
- 已验证导入脚本 dry-run 可校验题库且不外呼、不外写、不记录原文摘要。

不能说：

- 已完成真实客户 50-100 题验收。
- 已完成生成答案事实性评测。
- 已完成真实模型质量验收。
- 已完成真实渠道接入。
- 已达到可商用 V1。

## 8. 下一步

P3-02 才进入生成答案事实性与引用评测。P3-02 的前置条件是：

1. 使用客户真实脱敏题库，或至少使用本 P3-01 样例题库进行一次 rehearsal。
2. 知识包 source_uri 与题库 expected_source_uri 对齐。
3. 人工标注人审边界、禁用话术和期望引用。
4. 明确是否允许真实模型调用；没有授权时只能使用 deterministic 或 mock provider。
