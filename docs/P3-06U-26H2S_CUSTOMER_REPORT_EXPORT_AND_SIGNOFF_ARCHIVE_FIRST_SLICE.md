# P3-06U-26H2S 客户报告导出与签收留档第一片

## 定位

本片把 H2Q 的“客户可读质量报告”从页面展示推进到本地可交付留档：系统可以导出一份自包含 HTML 报告，并在本地审计表记录导出动作。

本片仍然不是完整客户正式签收。正式签收还需要客户确认、线上真实回执、失败重试、外发审计和持续回归。

## 已完成

- 新增 `GET /api/tenants/{tenant_id}/customer-quality-report/export?format=html`。
- 新增导出 schema `p3-06u-26h2s.customer_quality_report_export.v1`。
- 导出文件为本地自包含 HTML，文件名形如 `wanfa-customer-quality-report-{tenant_id}-{period}.html`。
- HTML 包含报告标题、周期、质量结论、关键指标、复盘章节、签收前动作、签收检查项、数据边界和签收确认区。
- 导出时写入审计事件 `customer_quality_report.exported`。
- 审计只记录 schema、文件名、body hash、字节数、报告状态、可信度和边界标记。
- 前端质量复盘页新增“导出报告”按钮，导出后显示已导出文件名和“待客户确认”状态。
- 新增浏览器 smoke `scripts/check_p3_06u_26h2s_customer_report_export_ui.mjs`。

## 明确边界

- 当前只支持 HTML，不支持 PDF、DOCX 或 XLSX。
- 不调用模型。
- 不写 outbox。
- 不打开真实外发。
- 不上传到我方云端。
- 不接官方渠道。
- 不保存客户签名图片或电子签章。
- 导出报告不包含原始客户问题、完整最终回复、人工备注明文、联系方式、密钥、token、cookie 或渠道 payload。
- 报告签收状态为 `pending_customer_confirmation`，表示“待客户确认”，不是“已签收”。

## 验证

- `backend`: `./.venv/bin/python -m py_compile app/services/knowledge.py app/api/knowledge.py app/schemas/knowledge.py` -> 通过
- `backend`: `./.venv/bin/python -m pytest tests/test_knowledge_evaluations_api.py::test_owner_can_capture_final_answer_samples_and_batch_label_factuality -q` -> 通过
- `backend`: `./.venv/bin/python -m pytest tests/test_knowledge_evaluations_api.py tests/test_knowledge_gaps_api.py tests/test_reply_decisions_api.py tests/test_diagnostics_api.py -q` -> `24 passed`
- `frontend`: `npm run typecheck` -> 通过
- `frontend`: `npm run build` -> 通过，只有既有 Vite chunk 体积提醒
- `node --check scripts/check_p3_06u_26h2s_customer_report_export_ui.mjs` -> 通过
- `node scripts/check_p3_06u_26h2s_customer_report_export_ui.mjs` -> 通过

浏览器证据：

```text
output/p3_06u_26h2s_customer_report_export_ui/summary.json
output/p3_06u_26h2s_customer_report_export_ui/customer-report-export.png
```

关键证据：

- `schemaVersion=p3-06u-26h2s.customer_quality_report_export.v1`
- `contentType=text/html; charset=utf-8`
- `hasSignoff=true`
- `hasBoundary=true`
- `rawQuestionLeaked=false`
- `finalAnswerLeaked=false`
- `rawTextIncluded=false`
- `finalAnswerTextIncluded=false`
- `reviewerNotesIncluded=false`
- `modelCallPerformed=false`
- `externalPlatformWritePerformed=false`

## 下一步

- H2T：客户签收记录第一片。建议新增“导入/记录客户签收结果”本地记录，不做复杂电子签章。
- 或 H2R2：XLSX 最终回复样本和人工标签导入导出。
- 或继续恢复线：本机恢复工具第二片。

渠道官方接入验收仍不纳入本片，真实外发继续默认关闭。
