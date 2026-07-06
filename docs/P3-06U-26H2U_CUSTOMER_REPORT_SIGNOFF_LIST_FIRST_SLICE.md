# P3-06U-26H2U 客户签收记录列表第一片

## 定位

本片接在 H2T 客户签收记录之后，补上“负责人可以回看最近客户确认记录”的只读能力。它把 H2T 写入本地审计事件的签收记录，整理成质量复盘页可见的最近确认记录列表。

本片仍然不是电子签章，也不是正式合同签收。它只证明本地工作台已经能把“报告导出 -> 客户确认 -> 审计留档 -> 最近记录回看”这条轻量闭环跑通。

## 已完成

- 新增 `GET /api/tenants/{tenant_id}/customer-quality-report/signoffs`。
- 新增列表 schema `p3-06u-26h2u.customer_quality_report_signoff_list.v1`。
- 列表数据来源为 `customer_quality_report.signoff_recorded` 审计事件，不新增可变业务表。
- 支持 `page`、`page_size` 和 `period=YYYY-MM` 过滤。
- 列表项返回周期、报告状态、报告可信度、确认状态、确认方式、脱敏签收人、备注摘要状态、审计编号和记录时间。
- 签收人姓名仍只显示脱敏值。
- 备注仍只显示是否记录、hash 和长度，不返回备注原文。
- 前端质量复盘页客户质量报告区新增“最近确认记录”列表。
- 记录客户确认后，前端自动刷新最近确认记录。
- 新增浏览器 smoke `scripts/check_p3_06u_26h2u_customer_report_signoff_list_ui.mjs`。

## 权限

- 读取客户质量报告仍使用 `quality.read`。
- 记录客户确认结果使用 `accounts.manage`。
- 查看客户确认记录列表同样使用 `accounts.manage`。
- 当前负责人账号可查看和记录，普通管理员、坐席和只读账号不能查看客户确认记录列表。

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
- 不把本地签收记录列表包装成完整线上客服准确率。
- 真实外发、线上回执、失败重试、渠道审计、PDF/DOCX 和电子签章仍需后续单独验收。

## 验证

- `backend/.venv/bin/python -m py_compile backend/app/services/knowledge.py backend/app/api/knowledge.py backend/app/schemas/knowledge.py` -> 通过
- `cd backend && ./.venv/bin/python -m pytest tests/test_knowledge_evaluations_api.py::test_owner_can_capture_final_answer_samples_and_batch_label_factuality -q` -> 通过
- `cd backend && ./.venv/bin/python -m pytest tests/test_knowledge_evaluations_api.py tests/test_knowledge_gaps_api.py tests/test_reply_decisions_api.py tests/test_diagnostics_api.py -q` -> `24 passed`
- `cd frontend && npm run typecheck` -> 通过
- `cd frontend && npm run build` -> 通过，只有既有 Vite chunk 体积提醒
- `node --check scripts/check_p3_06u_26h2u_customer_report_signoff_list_ui.mjs` -> 通过
- `node scripts/check_p3_06u_26h2u_customer_report_signoff_list_ui.mjs` -> 通过

浏览器证据：

```text
output/p3_06u_26h2u_customer_report_signoff_list_ui/summary.json
output/p3_06u_26h2u_customer_report_signoff_list_ui/customer-report-signoff-list.png
```

关键证据：

- `schemaVersion=p3-06u-26h2u.customer_quality_report_signoff_list.v1`
- `total=1` 接口层列表记录可读
- `firstSignerDisplayName=李*`
- `hasNotesHash=true`
- `rawTextIncluded=false`
- `finalAnswerTextIncluded=false`
- `reviewerNotesIncluded=false`
- `signerNameRawIncluded=false`
- `externalPlatformWritePerformed=false`
- `rawSignerLeaked=false`
- `noteLeaked=false`
- 前端 `hasSignoffList=true`
- 前端 `hasSignoffListCount=true`
- 前端 `rawQuestionLeaked=false`
- 前端 `finalAnswerLeaked=false`

## 下一步

- H2V：线上回执汇总只读口径第一片，为未来真实线上准确率准备数据入口。
- 或 H2R2：XLSX 最终回复样本和人工标签导入导出。
- 或 H2W：客户质量报告 PDF/DOCX 导出第一片。

渠道官方接入验收仍不纳入本片，真实外发继续默认关闭。
