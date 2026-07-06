# P3-06U-26H2W11 内部演练输入与应用层评估

## 结论

本轮已按内部工程需要生成两类输入：

- 内部业务模拟确认回传：`evals/p3_06u_26h2w11m_customer_confirmation_return_received.csv`
- 内部 100 条脱敏演练题库：`evals/p3_06u_26h2w11o_real_customer_eval_bank_received.csv`

这两份文件可以用于跑通工程链路，但不能写成真实客户确认、真实客户题库或正式客户准确率签收。系统已在门禁输出中标记：

- `internal_rehearsal_confirmation_used=true`
- `internal_synthetic_rehearsal_used=true`
- `real_customer_confirmation_performed=false`
- `ready_for_customer_quality_report_candidate=false`
- `ready_for_formal_accuracy_signoff=false`

跳开企业微信、企业渠道和真实外发之后，当前应用层不是“完全无事可做”。它已经适合继续做小微企业本地受控试点，但还没有达到“完整商用客服产品可封版”的程度。

## 本轮生成与验证

### 内部确认文件

- 生成脚本：`scripts/generate_h2w11_internal_rehearsal_inputs.py`
- 输出文件：`evals/p3_06u_26h2w11m_customer_confirmation_return_received.csv`
- 行数：12 条
- reviewer：内部演练系统
- reviewer role：内部业务模拟确认-非客户签收
- 结论：可用于工程 rehearsal，不可用于真实客户签收。

H2W-11N 结果：

- 状态：`passed_internal_rehearsal`
- 内部演练确认条目：12
- 真实客户确认条目：0
- 正式准确率签收：false

### 内部 100 条脱敏题库

- 生成脚本：`scripts/generate_h2w11_internal_rehearsal_inputs.py`
- 输出文件：`evals/p3_06u_26h2w11o_real_customer_eval_bank_received.csv`
- 行数：100 条
- 数据来源类型：`internal_synthetic_rehearsal`
- 覆盖场景：官网客服试点、知识维护、售后退换、价格套餐、发票合同、物流时效、隐私权限、知识缺口、投诉争议、模型成本。

H2W-11O 结果：

- 状态：`passed_internal_rehearsal`
- 样本数量：100
- 脱敏扫描：通过
- 期望答案覆盖：100/100
- 转人工标签覆盖：100/100
- 业务对象覆盖：100/100
- 引用来源覆盖：100/100

H2W-11P 结果：

- 状态：`passed`
- 数据来源类型：`internal_synthetic_rehearsal`
- 样本数：100
- 可评事实性样本：40
- 最终答案事实性通过率：1.0
- 引用充分率：1.0
- 禁用承诺通过率：1.0
- 转人工正确率：1.0
- 内部质量报告候选：true
- 客户质量报告候选：false
- 正式签收：false

## 应用层当前真实评分

| 维度 | 当前评分 | 说明 |
|---|---:|---|
| 本地受控试点可用度 | 80/100 | 登录、知识维护、质量报告、本地维护、内部题库 rehearsal 已可复现；适合内部演示和小范围共创试点。 |
| 应用层功能完整度 | 74/100 | 主要功能域已经存在，且多数有后端接口和落库证据；但生产检索运行环境、完整模型成本治理和持续质量回归还没封死。 |
| 前端产品化成熟度 | 72/100 | 桌面中台形态已成型，真实登录、知识维护和维护中心 smoke 通过；但 `App.tsx` 仍约 1.7 万行，复杂页拆分和逐按钮深审仍需继续。 |
| 后端事实链成熟度 | 76/100 | provenance、模型调用、引用快照、题库、质量报告、本地维护证据已较完整；但生产 pgvector runtime 和真实外部回执仍未完成。 |
| 完整商用客服成熟度 | 65/100 | 不考虑企业渠道后，产品仍缺生产检索环境、安装封版、长周期稳定性和真实客户持续运营证据。 |
| 全渠道自动回复成熟度 | 暂不评分 | 企业/平台真实接入本轮暂停，不纳入当前阶段判断。 |

## 已经比较扎实的部分

1. 账号与本地初始化：真实登录、首任负责人、本地维护入口已经形成。
2. 知识维护：业务对象、标准问答、知识文档、资料包检查、导入、启用前复测和启用路径已可浏览器验证。
3. 质量闭环：题库、最终答案采样、人工事实性标签、质量报告、缺口证据和报告导出链路已基本成型。
4. 本地维护：诊断包、售后接收、签名更新计划、备份/恢复演练总账已有可见路径。
5. 前端真实性矩阵：63 行功能矩阵通过，客户可见工程词计数为 0。

## 仍必须继续做的非企业渠道事项

### 1. PostgreSQL + pgvector 运行环境

H2W-7D 当前状态：

- pgvector 代码 ready：true
- ANN 策略 ready：true
- 非 PostgreSQL fail-closed ready：true
- 内部 100 题 ready：true
- PostgreSQL runtime ready：false
- 生产检索切换 ready：false

这说明生产级检索不是代码空白，但还没有真正运行在 PostgreSQL + pgvector 上。下一步应补 Docker/PostgreSQL/pgvector 本地候选环境，并用 100 条题库跑召回、引用覆盖、延迟和成本。

### 2. 前端结构继续拆分

当前 `frontend/src/App.tsx` 约 16990 行，已经不是健康的长期维护状态。即使页面能跑，也会影响后续稳定迭代。

建议优先拆：

- 知识维护总流程和资料包导入逻辑。
- 运维与本地维护中心。
- 自动回复策略/模型路由页。
- 运营总览筛选和 BI 卡片。

### 3. 前端逐按钮深审继续保留

H2W-FE2 静态通过，但仍提示 `App.tsx` 内部变量包含 `dry-run/provider/outbox/sandbox/H2W` 等工程词。当前判断是客户可见页没有暴露，但后续每次新增页面都要继续跑浏览器深审。

### 4. 本地交付封版

当前能在开发环境跑通，不等于客户安装包封版。仍要补：

- 空库安装 rehearsal。
- 程序版本号和健康接口。
- 安装包或部署包启动脚本。
- 数据库迁移和旧库兼容。
- 备份、恢复、更新、回滚的封版文档和 smoke。

### 5. 模型真实调用和成本治理

本轮没有调用付费模型。当前能证明回复质量链路可跑，但不能证明真实 Qwen/百炼调用下的稳定成本、延迟和降级表现。后续可在受控限额下跑小样本真实模型 smoke。

## 当前是否“完全做好”

不是。

更准确的说法是：

> 这个系统已经从“原型展示”推进到“本地受控试点产品雏形”。它有真实登录、知识维护、质量复盘、本地维护和内部题库 rehearsal 证据；但离完整商用封版还差生产检索运行环境、前端结构瘦身、安装部署封版、真实模型成本验证和长期稳定性验证。

如果下一步不做企业/企微/电商平台真实接入，最合理的推进顺序是：

1. H2W-7D-runtime：补 PostgreSQL + pgvector 本地运行环境和检索评测。
2. H2W-FE3：前端深拆和逐按钮浏览器深审第二轮。
3. H2W-PACK1：本地安装/空库初始化/备份恢复/更新回滚封版 rehearsal。
4. H2W-MODEL1：百炼/千问真实小样本限额调用、成本台账和降级策略验收。
5. H2W-TRIAL1：用内部 100 题跑完整本地试点 rehearsal，并输出内部可读质量报告。

## 验证命令

```bash
backend/.venv/bin/python scripts/generate_h2w11_internal_rehearsal_inputs.py
backend/.venv/bin/python scripts/check_p3_06u_26h2w11n_customer_confirmation_import.py
backend/.venv/bin/python scripts/check_p3_06u_26h2w11o_real_customer_eval_bank_import.py
backend/.venv/bin/python scripts/check_p3_06u_26h2w11p_final_answer_sampling.py
backend/.venv/bin/python scripts/check_p3_06u_26h2w_fe2_frontend_workflow_qa.py
node scripts/check_p3_06u_26h2w0_frontend_function_reality_owner_login.mjs
node scripts/check_p3_06u_26h2w11e_owner_customer_knowledge_trial.mjs
node scripts/check_p3_06u_26h2w8b_local_maintenance_ui.mjs
backend/.venv/bin/python scripts/check_p3_06u_26h2w7d_production_retrieval_evidence.py
cd frontend && npm run typecheck
cd frontend && npm run build
```

本轮已运行上述核心命令。除 H2W-7D 因缺 PostgreSQL + pgvector runtime 保持阻断外，其余相关门禁通过。
