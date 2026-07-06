# P3-06U-26H2W11 受控试点演练前置门禁第一片

## 定位

本片进入 H2W-11，但只做“受控试点 rehearsal 的前置门禁”，不冒充正式客户验收。

目标是把 50-100 题、客户知识包、质量报告、签收、本地维护闭环这些分散能力先放到一个可检查的入口里，判断系统是否具备进入端到端受控演练的最低条件。

## 本轮完成

- 新增 `scripts/check_p3_06u_26h2w11_rehearsal_preflight.py`。
- 读取 `evals/p3_01_realistic_customer_service_eval_bank_62_2026-06-27.csv`，使用既有题库导入解析器做脱敏题库校验。
- 读取 `evals/p3_06u_26f_real_customer_knowledge_package_template.json`，检查知识包文档、来源 URI 和隐私边界。
- 检查 H2W-11 需要复用的能力文件是否存在：
  - 题库导入 UI smoke。
  - 客户质量报告 UI smoke。
  - 客户报告签收 UI smoke。
  - 签收列表 UI smoke。
  - 本地维护 UI smoke。
  - 本地维护就绪度门禁。
  - 知识包导入 API 测试。
  - 质量报告导出脚本。
- 检查 H2W-8B 浏览器验收证据是否存在，并确认后端总账为 `ready_for_rehearsal`。
- 生成前置门禁摘要：`output/p3_06u_26h2w11_rehearsal_preflight/summary.json`。

## 当前前置门禁结果

- `status`: `ready_for_h2w11_preflight_rehearsal`
- `ready`: `true`
- 题库规模：62 题，满足 50-100 题 rehearsal 的最低区间。
- 敏感行：0。
- 知识包文档：7 份。
- 题库引用来源覆盖：7/7，无缺失来源 URI。
- H2W-8B 本地维护证据：已存在，`maturity_status=ready_for_rehearsal`，阻断项 0。
- 真实外发：未发生。
- 模型 provider 调用：未发生。
- 正式客户签收：未发生。

## 重要警告

当前 62 题是客户式脱敏样例，不是真实客户原始资料。

当前题库没有 `expected_answer` 字段。它可以进入受控演练前置门禁，但正式签收前仍需通过以下任一方式补齐答案口径：

- 采集系统最终客服答案样本，再做人工事实性、引用充分、禁用承诺和转人工正确性标注。
- 或由客户提供每类问题的期望回答/标准口径，再和系统最终答案做比对。

## 验收命令

```bash
python3 scripts/check_p3_06u_26h2w11_rehearsal_preflight.py
```

通过时必须看到：

- `status=ready_for_h2w11_preflight_rehearsal`
- `ready=true`
- `blockers=[]`
- `question_bank.total_cases` 在 50 到 100 之间。
- `question_bank.sensitive_row_count=0`
- `knowledge_package.missing_source_uris=[]`
- `h2w8b_summary.maturity_status=ready_for_rehearsal`
- `boundaries.external_platform_write_performed=false`
- `boundaries.provider_call_performed=false`

## 停止门禁

- 题库少于 50 题或超过 100 题，不进入 H2W-11 演练。
- 题库发现手机号、邮箱、身份证号等敏感行且未脱敏，不进入演练。
- 知识包无法覆盖题库 `expected_source_uri`，不进入演练。
- H2W-8B 本地维护证据缺失或未进入 `ready_for_rehearsal`，不进入演练。
- 质量报告、签收或本地维护脚本缺失，不进入演练。
- 任何真实外发、真实平台发送、真实模型批量调用、自动上传、远程控制或静默更新迹象，都停止演练。

## 仍未完成

- 尚未真正跑完整 H2W-11 负责人真实登录端到端 rehearsal。
- 尚未把知识包导入、题库导入、评测运行、最终答案采样、人工标签、质量报告、签收和本地维护证据串成同一条运行记录。
- 尚未使用客户真实脱敏资料。
- 尚未完成生产级 pgvector/rerank。
- 尚未接真实企业微信、公众号、抖音、淘宝、京东或拼多多外发。

## 下一步

进入 H2W-11A：负责人真实登录 rehearsal。

建议顺序：

1. 临时空库创建负责人。
2. 导入 7 份知识包文档。
3. 导入 62 题客户式题库。
4. 运行评测。
5. 抽样采集最终客服答案。
6. 批量写入人工事实性标签。
7. 导出客户质量报告。
8. 创建本地签收记录。
9. 读取 H2W-8B 本地维护总账作为运维证据。
10. 输出一个 rehearsal summary，不包含真实客户原文，不触发真实外发。
