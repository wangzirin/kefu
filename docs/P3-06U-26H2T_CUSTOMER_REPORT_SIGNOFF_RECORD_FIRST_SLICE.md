# P3-06U-26H2T 客户签收记录第一片

## 定位

本片接在 H2S 客户质量报告导出之后，补上“客户确认结果本地留档”能力：负责人账号可以在质量复盘页记录某一期客户质量报告的确认结果，并把记录写入本地审计事件。

本片仍然不是正式电子签章，也不是线上客服准确率完整签收。它只证明本地工作台已经能把“报告导出 -> 客户确认 -> 审计留档”这条轻量闭环跑通。

## 已完成

- 新增 `POST /api/tenants/{tenant_id}/customer-quality-report/signoffs`。
- 新增签收记录 schema `p3-06u-26h2t.customer_quality_report_signoff.v1`。
- 签收记录绑定现有客户质量报告周期、报告 schema、导出 schema、报告状态和可信度分数。
- 确认结果支持四类：确认通过、确认通过有备注、需要返修后再确认、不通过。
- 确认方式支持四类：本地记录、邮件确认、会议确认、线下签字。
- 签收人姓名只返回和审计保存脱敏显示名与 hash，不保存明文姓名。
- 备注只保存 hash 和长度，不保存备注原文。
- 审计事件为 `customer_quality_report.signoff_recorded`。
- 前端质量复盘页客户质量报告区新增“客户确认记录”表单。
- 前端提交后显示本期报告确认状态和脱敏签收人。
- 新增浏览器 smoke `scripts/check_p3_06u_26h2t_customer_report_signoff_ui.mjs`。

## 权限

- 读取客户质量报告仍使用 `quality.read`。
- 导出客户质量报告仍使用 `quality.read`。
- 记录客户确认结果使用 `accounts.manage`。
- 当前 `accounts.manage` 只有负责人账号具备，普通管理员、坐席和只读账号不能记录客户确认结果。

## 明确边界

- 不调用模型。
- 不写 outbox。
- 不打开真实外发。
- 不上传到我方云端。
- 不接官方渠道。
- 不做电子签章。
- 不保存签名图片。
- 不保存签收人明文姓名。
- 不保存签收备注原文。
- 不把本地签收记录包装成完整线上客服准确率。
- 真实外发、线上回执、失败重试、渠道审计和持续回归仍需后续单独验收。

## 验证

- `backend/.venv/bin/python -m py_compile backend/app/services/knowledge.py backend/app/api/knowledge.py backend/app/schemas/knowledge.py` -> 通过
- `cd backend && ./.venv/bin/python -m pytest tests/test_knowledge_evaluations_api.py::test_owner_can_capture_final_answer_samples_and_batch_label_factuality -q` -> 通过
- `cd backend && ./.venv/bin/python -m pytest tests/test_knowledge_evaluations_api.py tests/test_knowledge_gaps_api.py tests/test_reply_decisions_api.py tests/test_diagnostics_api.py -q` -> `24 passed`
- `cd frontend && npm run typecheck` -> 通过
- `cd frontend && npm run build` -> 通过，只有既有 Vite chunk 体积提醒
- `node --check scripts/check_p3_06u_26h2t_customer_report_signoff_ui.mjs` -> 通过
- `node scripts/check_p3_06u_26h2t_customer_report_signoff_ui.mjs` -> 通过
- `lsof -nP -iTCP:8109 -sTCP:LISTEN || true` -> 无残留
- `lsof -nP -iTCP:5209 -sTCP:LISTEN || true` -> 无残留
- `lsof -nP -iTCP:9249 -sTCP:LISTEN || true` -> 无残留

浏览器证据：

```text
output/p3_06u_26h2t_customer_report_signoff_ui/summary.json
output/p3_06u_26h2t_customer_report_signoff_ui/customer-report-signoff.png
```

关键证据：

- `schemaVersion=p3-06u-26h2t.customer_quality_report_signoff.v1`
- `statusLabel=确认通过，有备注`
- `rawTextIncluded=false`
- `finalAnswerTextIncluded=false`
- `reviewerNotesIncluded=false`
- `signerNameRawIncluded=false`
- `electronicSignaturePerformed=false`
- `formalContractSignoffPerformed=false`
- `modelCallPerformed=false`
- `externalPlatformWritePerformed=false`
- `rawSignerLeaked=false`
- `noteLeaked=false`
- `hasSignoffForm=true`
- `hasSignoffStatus=true`
- `hasMaskedSigner=true`

## 下一步

- H2U：客户质量报告签收记录列表第一片，允许负责人查看最近签收记录、状态和审计编号。
- 或 H2R2：XLSX 最终回复样本和人工标签导入导出。
- 或 H2V：线上回执汇总只读口径第一片，为未来“真实线上准确率”准备数据入口。

渠道官方接入验收仍不纳入本片，真实外发继续默认关闭。
