# P3-06U-26H2W4 报告导出与归档第一片

日期：2026-07-03

## 1. 阶段目标

本阶段只完成客户质量报告的“可下载、可归档、可回看”第一片。

它解决的问题是：质量复盘已经能生成客户可读报告后，客户或我方交付团队需要把报告以正式文件形式留存，而不是只停留在网页预览或单次 HTML 下载。

本阶段支持三种导出：

- HTML 留档：便于快速打开和内部查看。
- XLSX 明细：便于查看指标、复盘章节、动作项和边界。
- DOCX 报告：便于客户阅读、归档和后续线下确认。

## 2. 本次完成

### 2.1 后端

客户质量报告导出接口扩展为：

```text
GET /api/tenants/{tenant_id}/customer-quality-report/export?format=html|xlsx|docx
```

新增导出归档接口：

```text
GET /api/tenants/{tenant_id}/customer-quality-report/archives
GET /api/tenants/{tenant_id}/customer-quality-report/archives/{archive_event_id}/download
```

实现要点：

- HTML 继续以 UTF-8 文本返回。
- XLSX / DOCX 采用标准 OpenXML zip 文件结构生成，并以 base64 返回给前端下载。
- 每次导出都会写入 `customer_quality_report.exported` 审计事件。
- 审计事件保存文件体、文件名、格式、content type、sha256、字节数、报告周期、报告状态和边界标记。
- 导出文件不包含原始客户问题、完整客服回复、人工备注原文、渠道密钥或 raw payload。
- 本地确认和归档明确不是正式电子签章。

### 2.2 前端

质量复盘页客户报告区新增：

- `HTML 留档` 按钮。
- `XLSX 明细` 按钮。
- `DOCX 报告` 按钮。
- `报告归档` 列表。
- 历史归档下载按钮。

页面标记：

```text
data-h2w4-report-export="p3-06u-26h2w4"
data-h2w4-report-archives="p3-06u-26h2w4"
```

归档列表展示：

- 导出格式。
- 文件名。
- 报告周期。
- 报告状态。
- 生成时间。
- 文件大小。
- SHA256 摘要前缀。
- 审计编号。

## 3. 明确边界

本片不做这些事：

- 不做 PDF 导出；H2W-4 允许先完成 PDF 或 DOCX，本片选择 DOCX。
- 不接正式电子签章服务。
- 不把本地确认记录写成法律意义的电子签章。
- 不打开真实外发。
- 真实外发继续关闭。
- 不接真实企微、公众号、抖音、淘宝、京东、拼多多等平台发送。
- 不调用大模型。
- 不把回执覆盖率、检索命中率或样本评测结果包装成完整客服答案准确率。
- 不保存原始客户问题、完整客服回复或人工备注原文。

当前仍需后续完成：

- 更多真实客户题库。
- 最终回复样本和人工事实性标签。
- 真实官方渠道回执。
- 客户正式签收流程。
- 如需法律效力，另接合规电子签章服务。

## 4. 验收门禁

### 4.1 必须通过

```bash
python3 scripts/check_p3_06u_26h2w4_report_exports.py
cd backend && .venv/bin/python -m pytest tests/test_knowledge_evaluations_api.py::test_owner_can_capture_final_answer_samples_and_batch_label_factuality -q
cd frontend && npm run typecheck
cd frontend && npm run build
```

前端改动还必须完成浏览器 smoke，至少验证：

- 质量复盘页存在 HTML、XLSX、DOCX 三个导出按钮。
- 页面存在报告归档列表。
- 页面出现“不是正式电子签章”边界。
- 桌面宽度无横向溢出。
- 没有运行时错误。

### 4.2 停止门禁

出现任意一项，本阶段不能宣称完成：

- XLSX 或 DOCX 下载后不是有效 zip/OpenXML 文件。
- 导出文件包含原始客户问题、完整回复、人工备注原文或渠道密钥。
- 页面把本地确认写成正式电子签章。
- 归档列表只有前端样子，没有后端接口。
- 历史下载按钮没有真实接口或失败反馈。
- 静态门禁、后端测试、前端 typecheck/build 任意一个失败。
- 文档或页面声称真实外发已开启。

## 5. 下一步建议

H2W-4 后续可以继续做两条线：

1. PDF 导出或电子签章服务评估：只有接入真实电子签服务后，才允许使用正式电子签章表述。
2. 云接收台 H2W-5：把诊断包、质量报告、知识更新结果上传到我方云端接收台，形成客户环境的远程运维证据链。
