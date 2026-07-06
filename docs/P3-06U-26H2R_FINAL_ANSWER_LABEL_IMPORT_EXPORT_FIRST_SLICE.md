# P3-06U-26H2R 最终回复样本与人工标签导入导出第一片

日期：2026-07-03

## 定位

本片继续补齐“质量与准确率闭环”，不进入渠道正式接入，不打开真实外发。

H2P 已经能在知识评测详情里保存最终客服回复样本，并对已采样题做人工事实性标签。H2Q 已经能把题库规模、最终回复采样、人工事实性、引用覆盖和知识缺口整理成客户可读质量报告。H2R 解决的是下一层运营问题：把最终回复样本和人工标签导出给本地人工复核，再导回系统，方便多人协作、离线审阅和客户留档。

本片只做 CSV 第一片。暂不引入 XLSX 依赖，原因是当前项目没有稳定表格写入依赖，CSV 已可被 Excel、Numbers、WPS 打开；XLSX 可作为 H2R2 再做。

## 已完成能力

### 后端

- 新增 `GET /api/knowledge-evaluation-runs/{evaluation_run_id}/final-answer-labels/export`。
- 新增 `POST /api/knowledge-evaluation-runs/{evaluation_run_id}/final-answer-labels/imports`。
- 两个接口均要求 `knowledge.manage` 权限。
- 导出格式当前只支持 `csv`。
- 导出 schema 版本为 `p3-06u-26h2r.final_answer_label_io.v1`。
- 导出字段包括：
  - `evaluation_run_case_id`
  - `external_case_id`
  - `source_channel`
  - `source_category`
  - `question_hash`
  - `final_answer_text`
  - `final_answer_source`
  - `citation_uris`
  - `final_answer_factuality_status`
  - `citation_sufficient`
  - `forbidden_commitment_passed`
  - `handoff_correct`
  - `reviewer_notes`
- 导入支持 dry-run 预检。
- 导入优先按 `evaluation_run_case_id` 匹配本运行题目；如果题目来自另一轮运行，则回退按 `external_case_id` 匹配，便于跨运行复用标签。
- 导入会更新 `final_answer_sample` 和 `answer_quality`，并刷新评测运行摘要。
- 审计事件只记录导入导出计数、格式、匹配数、跳过数和 hash，不保存原始问题、最终回复正文或人工备注明文。

### 前端

- 知识评测详情新增“离线标注表”面板。
- 可一键导出 CSV，并把 CSV 内容放入本地文本区，便于检查和复制。
- 可粘贴 CSV 后先做预检。
- 预检通过后可导入标签。
- 导入成功后自动刷新当前运行、最近运行列表、月度质量复盘和客户质量报告。
- 面板明确说明：不会导出原始客户问题；CSV 包含最终回复样本，适合本地授权标注。

### 浏览器验收

新增浏览器 smoke：

```text
scripts/check_p3_06u_26h2r_final_answer_label_io_ui.mjs
```

验收覆盖：

- 临时后端、临时前端、临时 SQLite、临时 Chrome profile。
- 创建真实 owner 登录态。
- 创建知识文档、评测集、评测运行和最终回复样本。
- 批量标注样本。
- 打开知识评测页。
- 点击导出 CSV。
- 确认 CSV 包含 `question_hash`，不包含原始客户问题。
- 粘贴并预检 CSV。
- 导入 CSV。
- 确认导入成功提示和统计。
- 确认没有模型调用、没有外部平台写入、没有真实外发。

证据：

```text
output/p3_06u_26h2r_final_answer_label_io/summary.json
output/p3_06u_26h2r_final_answer_label_io/final-answer-label-io.png
```

## 数据与隐私边界

| 项目 | 当前口径 |
| --- | --- |
| 原始客户问题 | 不导出 |
| 问题追踪 | 只导出 `question_hash`、`external_case_id` 和运行内 case id |
| 最终回复样本 | 可导出，供授权人工标注 |
| 人工备注 | 可导入，但审计不保存明文 |
| 审计事件 | 只保存计数、格式、hash 和执行人 |
| 模型调用 | 未发生 |
| 外部平台写入 | 未发生 |
| 真实外发 | 继续关闭 |

这里要特别区分：最终回复样本是为了质量评审而保存的本地评测材料，不等于原始客户聊天记录，也不代表线上消息已经发出。

## 与完整准确率的关系

H2R 让人工标签可以离线流转，但它仍不等于完整线上客服准确率已经验收。

当前已经具备：

- 真实客户题库导入。
- 最终回复样本保存。
- 单题人工事实性标签。
- 批量人工标签。
- 客户可读质量报告。
- 最终回复样本和人工标签 CSV 导入导出。

仍然缺少：

- 更多真实客户样本。
- 客户正式签收记录。
- 报告导出留档。
- 线上真实渠道回执。
- 失败重试与回执 reconciliation。
- 客户现场持续回归。

所以本片只能说明“离线样本与标签管理闭环”完成第一片，不能写成“线上自动回复准确率已完成”。

## 验证结果

```bash
cd /Users/ericlee/Desktop/01_项目工作区/肥肥lu/lite_a_customer_service/standard_ops/backend
./.venv/bin/python -m py_compile app/services/knowledge.py app/api/knowledge.py app/schemas/knowledge.py
```

结果：通过。

```bash
cd /Users/ericlee/Desktop/01_项目工作区/肥肥lu/lite_a_customer_service/standard_ops/backend
./.venv/bin/python -m pytest tests/test_knowledge_evaluations_api.py::test_owner_can_capture_final_answer_samples_and_batch_label_factuality -q
```

结果：通过。

```bash
cd /Users/ericlee/Desktop/01_项目工作区/肥肥lu/lite_a_customer_service/standard_ops/backend
./.venv/bin/python -m pytest tests/test_knowledge_evaluations_api.py tests/test_knowledge_gaps_api.py tests/test_reply_decisions_api.py tests/test_diagnostics_api.py -q
```

结果：`24 passed`。

```bash
cd /Users/ericlee/Desktop/01_项目工作区/肥肥lu/lite_a_customer_service/standard_ops/frontend
npm run typecheck
npm run build
```

结果：通过；`npm run build` 仍只有既有 Vite chunk 体积提醒。

```bash
cd /Users/ericlee/Desktop/01_项目工作区/肥肥lu/lite_a_customer_service/standard_ops
node --check scripts/check_p3_06u_26h2r_final_answer_label_io_ui.mjs
node scripts/check_p3_06u_26h2r_final_answer_label_io_ui.mjs
```

结果：通过。summary 显示：

- `token_persisted=false`
- `model_call_performed=false`
- `external_platform_write_performed=false`
- `rawQuestionLeaked=false`
- `externalWriteEnabled=false`

## 不做事项

- 不做 XLSX 文件上传/下载。
- 不生成真实客服最终答案。
- 不调用百炼、DeepSeek 或其他模型。
- 不写 outbox。
- 不接官方渠道。
- 不做 RPA。
- 不真实外发。
- 不上传诊断包。
- 不保存原始客户问题到导出文件。
- 不把质量报告可信度写成完整客服准确率。

## 下一步建议

优先做 `P3-06U-26H2S 客户报告导出与签收留档第一片`：

- 把客户可读质量报告导出为本地 HTML 或 PDF/DOCX。
- 增加报告生成时间、题库版本、运行编号、签收检查项和客户确认状态。
- 保持不展示原始问题、不展示完整回复、不展示人工备注明文。

备选下一步：

- `P3-06U-26H2R2`：补 XLSX 导入导出。
- `P3-06U-26H2T`：补更多真实样本分布、抽样复核和回归批次对比。
- 恢复线：本机恢复工具第二片。

渠道官方接入验收继续排除在本片之后，除非单独授权。
