# H2W-NC1 试点事实账本权威化

## 阶段状态

`H2W-NC1` 已把 `pilot-readiness` 的客户资料 ready 判定收束到数据库事实链。

当前结论：

- 工程 `summary.json` 继续作为历史证据、门禁证据和交付档案来源。
- 客户现场状态不再由旧 summary 或单条审计事件抬高。
- 真实客户资料 ready 必须同时满足资料批次、题库完整性、知识复测和客户确认导入四段数据库事实。
- 真实外发、真实渠道、正式客户签收、生产 SLA 和签名安装包仍未完成。

## 本轮改动

1. `pilot-readiness` 新增客户资料事实链字段：
   - `customer_data_ready`
   - `customer_data_readiness_source`
   - `customer_data_ready_blockers`
   - `customer_data_ready_evidence`
   - `summary_evidence_authority`

2. `customer_data_ready` 不再使用旧判定：

   ```text
   customer_confirmation_ready and retest_ready
   ```

   新判定必须同时满足：

   - `data3.customer_material_batch` 为真实资料 ready。
   - 题库不少于 50 条，四层知识类型齐全，动作类型合法。
   - 资料批次无 blocker、无脱敏或敏感信息风险。
   - `kb6/kb7` 真实客户知识复测 fact 通过。
   - `pilot2.knowledge_confirmation_import` 为通过或带备注通过。

3. 客户确认导入不再只写审计事件。

   现在会落入 `pilot_readiness_facts`：

   - `fact_key = pilot2.knowledge_confirmation_import`
   - 保存 CSV hash、行数、确认计数、修订计数、风险计数和状态。
   - 不保存原始 CSV，不保存客户意见全文。

4. summary 读取增加：

   - `schema_version`
   - `sha256`
   - `age_seconds`
   - `stale`
   - `authority = engineering_evidence_only`

## 验收命令

```bash
PYTHONPATH=backend backend/.venv/bin/python -m pytest backend/tests/test_pilot_api.py -q
backend/.venv/bin/python scripts/check_p3_06u_26h2w_nc1_pilot_fact_authority.py
```

## 停止门禁

- 任何客户可见 ready 状态来自旧 summary，而不是数据库事实链。
- 客户确认导入只写 audit event，不写结构化 fact。
- 内部样板、内部确认文件或工程 summary 被写成客户正式签收。
- 真实外发、真实渠道或签名安装包被误写为完成。
