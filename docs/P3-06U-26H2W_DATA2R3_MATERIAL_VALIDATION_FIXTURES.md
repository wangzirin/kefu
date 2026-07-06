# H2W-DATA2R3 真实资料门禁反例校验

## 结论

- 阶段状态：`material_validation_fixtures_passed`
- 阻断项：`0` 个

## 校验目标

- 证明真实资料门禁能拦截少量题库、缺字段、敏感信息、密钥形态、真实外发和正式签收越界。

## 样例结果

- valid_minimum_50：通过预期；实际 通过；阻断 0 项
- too_few_questions：通过预期；实际 阻断；阻断 1 项
- missing_material_field：通过预期；实际 阻断；阻断 2 项
- contains_pii：通过预期；实际 阻断；阻断 1 项
- external_send_enabled：通过预期；实际 阻断；阻断 1 项
- formal_signoff_enabled：通过预期；实际 阻断；阻断 1 项
- invalid_action：通过预期；实际 阻断；阻断 1 项
- json_secret_field：通过预期；实际 阻断；阻断 1 项
- overclaim_phrase：通过预期；实际 阻断；阻断 1 项

## 证据文件

- output/p3_06u_26h2w_data2r3_material_validation_fixtures/summary.json
- docs/P3-06U-26H2W_DATA2R3_MATERIAL_VALIDATION_FIXTURES.md

## 不可承诺

- 正式客户验收签收
- 真实平台自动外发
- 企业微信、公众号、抖音、淘宝、京东、拼多多等真实渠道接通
- 生产 SLA 承诺
- 已签名 dmg/exe 安装器
- RPA 或个人号外挂正式交付

## 阻断项

- 无
