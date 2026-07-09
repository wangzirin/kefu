# H2W-MODEL1 百炼/千问真实小样本成本验证

## 结论

- 阶段状态：`guarded_external_call_not_allowed`
- 显式外部调用授权：`false`
- 真实 provider 调用：`false`
- 计划样本数：`5`
- 成功调用数：`0`
- 失败调用数：`0`
- tokens/字符量合计：`0`

## 停止门禁

- 默认不调用付费模型；必须显式传入 `--allow-external-call` 才能跑 5-10 条小样本。
- 显式 provider 失败不能静默 fallback，失败必须进入成本与质量证据。
- 没有持久成本记录、价格来源不可追溯、失败伪装成功时，不进入模型封版候选。
- 内部确定性回复不能计入真实模型成本。

## 阻断项

- 无

## 警告

- 内部 100 题证据未 ready；MODEL1 仍可只做 guarded planning

## 输出

- `C:\Users\123\AppData\Local\Temp\pytest-of-123\pytest-3\test_model1_defaults_to_no_ext0\model1\summary.json`

## 边界

- `provider_call_performed` 以 summary 为准
- `real_platform_send_performed=false`
- `formal_customer_signoff_performed=false`
