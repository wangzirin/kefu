# H2W-11O 真实 50-100 条脱敏题库导入

## 结论

- 阶段状态：`passed`
- 输入文件：`/private/var/folders/cv/nv4r5wsj1sl83z83j23cggb40000gn/T/pytest-of-ericlee/pytest-505/test_h2w11o_and_11p_accept_rea0/real_customer_bank.csv`
- 数据来源类型：`unspecified`
- 真实题库文件存在：`true`
- 真实客户题库已确认：`true`
- 题目数量：`50`
- 是否满足 50-100 条：`true`
- 脱敏扫描通过：`true`
- 可进入最终答案采样：`true`

## 停止门禁

- 少于 50 条时只能写成题库准备中，不能写成准确率验收。
- 不允许 demo 题库冒充真实题库。
- 内部合成演练题库必须标记为 `internal_synthetic_rehearsal`，只能用于工程 rehearsal。
- 原文必须脱敏，疑似手机号、邮箱、身份证会阻断。
- 每条必须有期望答案和转人工标签。
- 每条建议绑定业务对象、引用来源、必含词或禁用词。

## 阻断项

- 无

## 输出

- `/private/var/folders/cv/nv4r5wsj1sl83z83j23cggb40000gn/T/pytest-of-ericlee/pytest-505/test_h2w11o_and_11p_accept_rea0/h2w11o/summary.json`
- `/private/var/folders/cv/nv4r5wsj1sl83z83j23cggb40000gn/T/pytest-of-ericlee/pytest-505/test_h2w11o_and_11p_accept_rea0/h2w11o/real_customer_eval_bank_catalog_redacted.csv`

## 边界

- 本阶段不调用付费模型。
- 本阶段不打开真实外发。
- 本阶段不导出原始问题或完整期望答案。
- 本阶段题库通过后也仍不是正式客户签收。
