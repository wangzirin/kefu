# H2W-11N/11O 复核与整体成熟度评估

更新时间：2026-07-05

## 本轮结论

本轮完成两项复核：

1. H2W-11N 客户确认结果导入实战：已按内部演练文件复跑通过。
2. H2W-11O 50-100 条脱敏题库导入实战：已按内部 100 题脱敏演练题库复跑通过。

这两项结果只能证明工程链路可以跑通，不能写成真实客户确认、真实客户题库、正式准确率签收或正式商用验收。

## 已执行命令

```bash
backend/.venv/bin/python scripts/generate_h2w11_internal_rehearsal_inputs.py
backend/.venv/bin/python -m py_compile scripts/generate_h2w11_internal_rehearsal_inputs.py scripts/check_p3_06u_26h2w11n_customer_confirmation_import.py scripts/check_p3_06u_26h2w11o_real_customer_eval_bank_import.py scripts/check_p3_06u_26h2w11p_final_answer_sampling.py
backend/.venv/bin/python scripts/check_p3_06u_26h2w11n_customer_confirmation_import.py
backend/.venv/bin/python scripts/check_p3_06u_26h2w11o_real_customer_eval_bank_import.py
backend/.venv/bin/python scripts/check_p3_06u_26h2w11p_final_answer_sampling.py
backend/.venv/bin/python -m pytest backend/tests/test_p3_06u_26h2w_next_stage_gates.py backend/tests/test_p3_06u_26h2w11m_customer_confirmation_import_gate.py backend/tests/test_p3_06u_26h2w11j_gap_final_answer_rehearsal.py -q
backend/.venv/bin/python -m pytest backend/tests/test_p3_06u_26h2w_sealed_pilot_package_gates.py -q
```

测试结果：

- H2W-11N/11O/11P 相关测试：`7 passed`。
- 封版包门禁回归测试：`22 passed`。
- 仅有既有 `StarletteDeprecationWarning`，不影响本轮结论。

## H2W-11N 复核结果

输出文件：

- `output/p3_06u_26h2w11n_customer_confirmation_import/summary.json`
- `output/p3_06u_26h2w11n_customer_confirmation_import/customer_revision_items.csv`
- `output/p3_06u_26h2w11n_customer_confirmation_import/customer_rejected_items.csv`

机器摘要：

| 指标 | 结果 |
|---|---:|
| 阶段状态 | `passed_internal_rehearsal` |
| 回传文件存在 | `true` |
| 内部演练确认 | `true` |
| 真实客户确认 | `false` |
| 确认条目 | `12` |
| 修订条目 | `0` |
| 拒绝条目 | `0` |
| 正式准确率签收 | `false` |

判断：

- 确认导入链路可用。
- 标准答案没有被直接篡改。
- 没有伪造客户签收。
- 当前确认来自内部演练文件，不是客户真实确认。

## H2W-11O 复核结果

输出文件：

- `output/p3_06u_26h2w11o_real_customer_eval_bank_import/summary.json`
- `output/p3_06u_26h2w11o_real_customer_eval_bank_import/real_customer_eval_bank_catalog_redacted.csv`

机器摘要：

| 指标 | 结果 |
|---|---:|
| 阶段状态 | `passed_internal_rehearsal` |
| 题目数量 | `100` |
| 数据来源 | `internal_synthetic_rehearsal` |
| 真实客户题库确认 | `false` |
| 脱敏扫描敏感行 | `0` |
| 期望答案覆盖 | `100/100` |
| 转人工标签覆盖 | `100/100` |
| 业务对象覆盖 | `100/100` |
| 引用来源覆盖 | `100/100` |
| 必含/禁用规则覆盖 | `100/100` |
| 可进入最终答案采样 | `true` |

判断：

- 100 题内部脱敏题库满足工程演练数量、字段完整性、脱敏和引用要求。
- 该题库不是客户真实题库，不能用于正式准确率销售承诺。
- 题库已能支撑后续最终答案采样、引用覆盖和转人工安全策略验证。

## H2W-11P 连带复核结果

输出文件：

- `output/p3_06u_26h2w11p_final_answer_sampling/summary.json`
- `output/p3_06u_26h2w11p_final_answer_sampling/final_answer_samples_redacted.csv`
- `output/p3_06u_26h2w11p_final_answer_sampling/final_answer_human_factuality_labels.csv`

机器摘要：

| 指标 | 结果 |
|---|---:|
| 阶段状态 | `passed` |
| 样本数 | `100` |
| 可事实性评价样本 | `40` |
| 最终答案事实性通过率 | `1.0` |
| 引用充分率 | `1.0` |
| 禁用承诺通过率 | `1.0` |
| 转人工正确率 | `1.0` |
| 客户质量报告候选 | `false` |
| 正式准确率签收 | `false` |

判断：

- 最终答案采样链路可用，并且没有把检索命中率冒充完整客服准确率。
- 由于输入题库是内部合成演练，报告只能作为内部质量候选，不能作为客户质量报告或签收件。

## 当前总体阶段判断

### 已经真正做到的

1. 桌面客服中台主线已成型。
2. 账号、首任负责人、登录、本地工作区初始化等基础链路已具备。
3. 多渠道对话台已按客户可见工作台方向收束，不再把人工审核、待发送等旧流程作为主入口。
4. 知识运营已有客户资料模板、知识更新包、预检、导入、回归和复测模板链路。
5. 质量复盘已有最终答案采样、引用、禁用承诺、转人工正确性和内部 100 题质量报告链路。
6. PostgreSQL + pgvector runtime rehearsal 已通过，具备生产候选检索运行证据，但还没有切成真实客户生产检索上线。
7. 百炼/千问小样本成本验证已通过，已有 provider/model/token/latency 记录，但不是大规模模型质量验收。
8. 本地交付包、启动脚本、客户环境模板、诊断包、备份、恢复、签名更新包、售后交接 SOP 已形成候选闭环。
9. 客户启动说明、产品化总控、阶段文档和 Workspace 接力记录已经较完整。

### 仍没有做到的

1. 没有真实客户确认标准答案。
2. 没有真实客户 50-100 条脱敏题库。
3. 没有真实客户准确率签收。
4. 没有真实平台外发。
5. 没有真实 IM 闭环。
6. 没有企业微信、公众号、抖音、淘宝、京东、拼多多官方渠道上线。
7. 没有完整 macOS dmg / Windows exe 原生安装器。
8. 没有生产 SLA、持续监控值班和线上事故演练。
9. 没有客户侧长期使用后的命中率下降监测闭环。
10. 没有把内部合成题库替换成客户行业真实问题。

## 分维度评分

| 维度 | 分数 | 判断 |
|---|---:|---|
| 本地受控试点包 | 86/100 | 已可作为共创客户本地试点候选，仍需真实客户资料和安装器专项补强。 |
| 客户可见前端 | 82/100 | FE4 静态与浏览器点击 QA 通过，主流程已清爽很多；仍需真实客户使用后再看信息架构细节。 |
| 后端事实链 | 82/100 | provenance、模型成本、引用、质量、运维证据链已较完整；真实渠道回执和生产 SLA 未完成。 |
| 知识库维护 | 80/100 | 模板导入、预检、回归、复测、签收模板已具备；真实客户知识库与长期维护未验收。 |
| 质量与准确率证据 | 72/100 | 内部 100 题最终答案采样链路完整；缺真实客户题库、真实线上回执和正式签收。 |
| 模型路由与成本治理 | 75/100 | 小样本百炼/千问成本验证通过；大样本、持续预算和 provider 故障演练还不足。 |
| 本地交付与售后维护 | 80/100 | 启动脚本、诊断包、备份、恢复、更新包和 SOP 都有候选证据；完整原生安装器未做。 |
| 渠道/IM 商用闭环 | 35/100 | 当前主动暂停企业渠道，不可承诺微信、企微、电商平台真实自动回复上线。 |
| 安全与边界控制 | 84/100 | 真实外发、客户签收、provider 调用、RPA 正式交付等边界基本守住；仍需真实客户环境安全审计。 |
| 文档与接力 | 88/100 | 总控、阶段文档、索引、复盘较完整；后续要避免文档过多导致主线淹没。 |

## 综合评分

| 口径 | 当前评分 | 能不能对外 |
|---|---:|---|
| 小微企业本地受控试点候选 | 84/100 | 可以找第一批共创客户试用，但要明示试点边界。 |
| 共创客户本地交付候选 | 80/100 | 可以准备交付包和客户资料导入流程，仍需真实资料验收。 |
| 标准运营版成熟商用客服中台 | 70/100 | 还不能作为成熟商业成品大规模销售。 |
| 全渠道自动回复智能客服 | 40/100 | 不能对外承诺。渠道官方授权和真实外发未完成。 |
| 生产级长期运维产品 | 68/100 | 售后演练有了，但真实客户长期运行数据还没有。 |

## 是否需要子 agent 评判

本轮没有额外派发子 agent。

原因是本次核心问题不是观点分歧，而是事实状态复核：已有门禁脚本、机器摘要、pytest 和阶段文档足以判断两步是否完成。额外子 agent 如果不运行这些门禁，只会增加主观意见。

如果下一轮要做“正式商用发布前评审”，建议再派三类子 agent：

1. 产品体验审查：逐页看客户是否知道下一步怎么操作。
2. 后端事实链审查：核对每个 UI 状态是否有真实数据、审计和回滚证据。
3. 交付与风控审查：核对安装、备份、升级、渠道授权、真实外发和客户签收边界。

## 下一步建议

优先做两条线：

1. H2W-OPS2：客户侧月度运维报告，把诊断包、命中率、知识缺口、模型成本、异常回执、更新记录做成客户能看懂的周期报告。
2. H2W-INSTALL2：完整原生安装器专项，评估 macOS dmg、Windows exe、卸载、升级、日志、签名和回滚。

暂时不建议继续扩平台渠道，除非重新明确进入企业微信/微信客服官方沙箱专项。

