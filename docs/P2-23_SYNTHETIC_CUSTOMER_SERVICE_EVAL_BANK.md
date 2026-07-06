# P2-23 合成脱敏客户客服验收题库

最近更新：2026-06-26。

## 定位

本文件说明 `evals/customer_service_eval_bank_synthetic_80_2026-06-26.csv` 的设计口径。

这份题库是“真实业务语境的合成脱敏题库”，不是从真实客户聊天记录抽取，也不包含真实姓名、手机号、邮箱、订单号、地址、账号、token 或平台私信原文。它用于 P2-23 阶段验证客服知识检索、引用、知识缺口、转人工边界和后续脱敏报告链路。

## 覆盖范围

- 题量：80 条。
- 渠道：`web_widget`、`wecom`、`official_account`、`douyin`、`xiaohongshu`、`taobao`、`jd`、`pdd`。
- 业务分类：产品咨询、价格优惠、下单支付、发货物流、售后退换、发票合同、账号隐私、渠道规则、企业采购、知识缺口。
- 文档来源：使用 `internal://docs/...` 形式指向待建设的内部知识文档，包括产品与套餐、价格优惠、下单支付、发货物流、售后退换、发票合同、账号隐私、渠道规则和企业采购集成。
- 风险分布：`low=23`、`medium=33`、`high=21`、`critical=3`。
- 人审门禁：`expected_human_review=57`，`allow_auto_reply=false=57`。

## 设计原则

1. 题库不是自然流量抽样，而是验收题库。
   真实自然流量中普通问题占比会更高；本题库故意提高售后、赔付、合同、隐私、平台规则和知识缺口的占比，用来压测系统的安全边界。

2. 问题写得像客户会问的话，但不使用真实客户资料。
   例如会出现“超过七天退货”“合同主体变更”“平台客户昵称同步”等业务语境，但不会出现具体手机号、订单编号、姓名、地址或真实账号。

3. 默认先做 dry-run。
   `scripts/import_customer_service_eval_bank.py` 默认只校验和生成 payload，不写数据库、不调用模型、不写外部平台。

4. 本题库只证明检索和人审门禁可以被评测。
   它不证明模型生成答案无幻觉，不证明真实客户验收已完成，也不代表渠道已经真实接入。

## 使用方式

在 `standard_ops` 目录下执行：

```bash
python3 scripts/import_customer_service_eval_bank.py \
  evals/customer_service_eval_bank_synthetic_80_2026-06-26.csv \
  --name "P2-23 合成脱敏客户客服验收题库 80题" \
  --description "用于标准运营版 P2-23 的真实业务语境合成脱敏题库。不含真实客户身份或真实订单资料。"
```

预期 dry-run 结果：

- `status=validated`
- `total_cases=80`
- `sensitive_row_count=0`
- `raw_text_logged=false`
- `provider_call_performed=false`
- `external_write_performed=false`

如需写入本地测试环境，必须先有本地 owner/admin token，并显式传 `--create --api-base --tenant-id --token`。这一步仍然只是写入内部评测集 API，不会外呼模型或平台。

## 下一步接法

1. 导入本题库到本地临时租户。
2. 准备与 `internal://docs/...` 对应的 8-10 份知识文档。
3. 运行评测集，查看 `hit_rate`、`citation_precision`、`human_review_correctness` 和 `knowledge_gap_rate`。
4. 从前端“知识评测与质量”面板下载脱敏 Markdown/CSV 报告。
5. 人工复核失败题：区分知识缺口、文档没导入、检索没命中、应该转人工但未转、以及题目期望设计过严。

## 重要边界

- 不把这份题库称为真实客户数据。
- 不把 dry-run 称为真实客户验收。
- 不把检索评测通过称为生成答案无幻觉。
- 不把平台渠道字段称为平台已经真实接入。
- 后续导入真实客户题库时，仍要人工脱敏和人工抽查，不能只依赖脚本的手机号、邮箱、身份证号高置信拦截。
