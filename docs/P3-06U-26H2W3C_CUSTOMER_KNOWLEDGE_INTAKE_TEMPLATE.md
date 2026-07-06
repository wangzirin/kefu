# P3-06U-26H2W3C 客户资料导入模板与预检第一片

日期：2026-07-03

## 1. 阶段目标

本阶段只补“小微企业客户怎样把自己的资料交给系统维护知识库”的第一片。

目标不是做万能文件解析器，而是先把客户资料收敛成一个稳定、可预检、可追溯的导入格式：

- CSV/JSON 可以进入现有知识更新包预检。
- 预检通过后，继续走已有知识更新包导入接口。
- 导入后的文档仍需要发布前回归检查和确认发布版本。
- PDF/DOCX/XLSX 暂不自动解析，只作为来源留档或由人工整理成 CSV/JSON 后导入。

## 2. 本次完成

- 知识库运营页新增“客户资料导入助手”。
- 新增客户资料 CSV 模板，字段覆盖：
  - 资料类型
  - 对象类型
  - 对象名称
  - 别名
  - 客户问题
  - 标准答案
  - 流程标题
  - 流程正文
  - 禁用承诺词
  - 转人工词
  - 回归问题
  - 期望词
  - 禁止词
  - 来源
- 前端新增 CSV 转换器，把客户资料转换成 `wanfa.knowledge_update_package.v1`。
- 转换后写入既有“知识更新包 JSON”输入区，必须继续点击“预检差异”。
- CSV 模板可下载为本地文件。
- 页面明确写清：
  - PDF、DOCX、XLSX 原件先作为来源留档。
  - 当前不自动解析入库。
  - 导入不等于启用。
  - 完成预检、导入、回归题检查和确认发布后，才能进入客户签收记录。

## 3. 真实复用的能力

本片没有新造后端导入链路，而是复用已有真实接口：

| 步骤 | 真实能力 |
|---|---|
| CSV 转换 | 前端纯函数转换为 `wanfa.knowledge_update_package.v1` |
| 预检差异 | `POST /api/tenants/{tenant_id}/knowledge-update-package/previews` |
| 导入更新包 | `POST /api/tenants/{tenant_id}/knowledge-update-package-imports` |
| 文档启用 | `POST /api/knowledge-documents/{document_id}/publish-checks` 与 `publication` |
| 回归题 | 进入现有 knowledge evaluation set |

## 4. 当前边界

- 真实外发继续关闭。
- 不调用模型。
- 不接真实微信、抖音、淘宝、京东、拼多多等外部平台。
- PDF/DOCX/XLSX 暂不自动解析。
- 本片不做 OCR、不做大文件上传、不做病毒扫描、不做对象存储。
- 导入知识不等于启用知识。
- 发布前回归不等于完整线上客服准确率。

## 5. 验收门禁

新增静态门禁：

```bash
python3 scripts/check_p3_06u_26h2w3c_customer_knowledge_intake.py
```

必须满足：

- 前端存在 `data-h2w3c-customer-intake="true"`。
- 存在 CSV 模板、转换器和转换按钮。
- 页面文案明确 CSV/JSON 进入现有知识更新包预检。
- 页面文案明确 PDF/DOCX/XLSX 暂不自动解析。
- 功能真实性矩阵写入 H2W3C。

建议组合验证：

```bash
python3 scripts/check_p3_06u_26h2w3c_customer_knowledge_intake.py
python3 scripts/check_p3_06u_26h2w3b_customer_knowledge_flow.py
cd frontend && npm run typecheck
cd frontend && npm run build
```

## 6. 下一步

下一片建议做两条之一：

1. 浏览器真实点击 smoke：负责人登录后，点击“转换为更新包”，再点击“预检差异”，确认后端返回新增、跳过和错误计数。
2. 文件接收预检第一片：增加只读文件清单和 sha256 留档，但继续不自动解析 PDF/DOCX/XLSX。

