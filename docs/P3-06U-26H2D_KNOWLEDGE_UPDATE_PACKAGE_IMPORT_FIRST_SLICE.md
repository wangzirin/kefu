# P3-06U-26H2D 知识更新包导入第一片

## 1. 阶段定位

本片解决客户本地应用交付后的第二个核心运维问题：客户现场出现知识命中下降、标准答案过期、业务套餐变化或评测题失败时，我方可以根据客户主动提供的诊断包制作一份知识修复包，客户管理员在本地工作台先预检差异，再决定是否导入。

本片不是程序自动更新器，不是远程控制，不是自动上传，也不是真实平台外发。它只做“知识内容补丁”的第一片能力。

## 2. 已完成内容

### 后端

- 新增知识更新包结构 `wanfa.knowledge_update_package.v1`。
- 新增 `POST /api/tenants/{tenant_id}/knowledge-update-package/previews`。
- 新增 `POST /api/tenants/{tenant_id}/knowledge-update-package-imports`。
- 新增 `POST /api/knowledge-update-package-imports/{import_batch_id}/rollback`。
- 权限要求：当前用户必须属于同一租户，并具备 `knowledge.manage` 权限。
- 预检接口只分析差异，不写入数据库。
- 导入接口支持追加：
  - 通用知识卡片。
  - 业务对象。
  - 对象级标准问答。
  - 知识文档与本地分块。
  - 回归评测题集。
- 导入批次写入 `KnowledgeImportBatch`，保存新增对象、跳过项、错误项、备份快照和回滚状态。
- 回滚接口会把本批次新增的对象、问答、文档、分块、评测题集归档，不物理删除。
- 导入和回滚都写审计记录。

### 前端

- 在“知识运营 -> 知识库运营”加入“知识更新包导入”卡片。
- 默认提供一份示例 JSON，方便本地试点理解格式。
- 支持点击“预检差异”查看新增、跳过、错误和批次状态。
- 支持点击“导入更新包”把知识包写入本地知识库。
- 导入成功后会刷新知识文档和知识评测数据。
- 页面只展示差异摘要，不展示完整客户原始文本。

### 安全边界

本片默认遵守以下边界：

- 不自动上传客户数据。
- 不主动连接我方云端。
- 不触发真实渠道外发。
- 不触发外部平台消息发送。
- 不调用付费模型。
- 不把诊断包当成数据库备份。
- 不把知识更新包当成程序更新包。
- 当前文档导入只允许确定性本地 embedding 口径；如果环境配置成外部 embedding provider，接口会拒绝导入，避免试点阶段意外产生外部调用。

## 3. 知识更新包格式

最小格式：

```json
{
  "schema_version": "wanfa.knowledge_update_package.v1",
  "package_id": "pkg-local-knowledge-fix-001",
  "package_name": "本地知识修复包",
  "source_diagnostic_filename": "wanfa-diagnostic-local.json",
  "notes": "用于补充业务对象、标准问答、政策文档和回归题。",
  "business_objects": [],
  "object_knowledge_cards": [],
  "knowledge_documents": [],
  "evaluation_sets": []
}
```

推荐使用方式：

1. 客户在本地导出诊断包。
2. 客户把诊断包发给我方运维。
3. 我方根据知识缺口、失败题、低置信问题制作知识更新包。
4. 客户管理员在本地导入前先点“预检差异”。
5. 确认新增项、跳过项和错误项后再点“导入更新包”。
6. 导入后跑知识评测回归。
7. 如果出现明显问题，使用该批次的回滚能力归档新增内容。

## 4. 为什么这样设计

本地交付的最大矛盾是：客户希望数据在本地，我方又需要持续维护知识质量。直接远程进入客户电脑、直接拿客户数据库、直接自动改客户知识库，都不适合作为默认方案。

所以本片采用“诊断包 + 知识更新包”的低风险运维模型：

- 诊断包负责把问题变成可排查证据。
- 知识更新包负责把修复变成可预检、可导入、可回滚的本地变更。
- 程序更新包负责版本升级，后续单独设计。

这样客户始终保留本地控制权，我方也可以持续修复知识命中率下降、话术过期和评测失败问题。

## 5. 当前未完成项

- 未实现签名 `.wanfa-update` 文件。
- 未实现知识更新包上传到我方运维台。
- 未实现客户侧自动检查更新。
- 未实现程序版本更新器。
- 未实现导入前完整数据库快照恢复。
- 未实现导入后自动运行指定评测集。
- 未实现图形化批次回滚按钮。
- 未实现知识包来源证书、签名校验和篡改检测。

## 6. 验收记录

后端接口与权限测试：

```bash
cd backend
./.venv/bin/python -m pytest tests/test_knowledge_update_packages_api.py -q
```

结果：通过，`3 passed`。

后端相关回归测试：

```bash
cd backend
./.venv/bin/python -m pytest tests/test_knowledge_update_packages_api.py tests/test_knowledge_api.py tests/test_knowledge_gaps_api.py tests/test_diagnostics_api.py tests/test_accounts_api.py tests/test_local_setup_api.py -q
```

结果：通过，`25 passed`。存在既有 Starlette/httpx deprecation warning，不影响本片。

前端类型检查：

```bash
npm --prefix frontend run typecheck
```

结果：通过。

前端构建：

```bash
npm --prefix frontend run build
```

结果：通过。存在既有 Vite chunk 体积提醒，不影响本片。

浏览器验收：

- 本地预览地址：`http://127.0.0.1:5182/#knowledge`
- 登录后进入“知识运营 -> 知识库运营”。
- 可见“知识更新包导入”卡片。
- 点击“预检差异”后，页面显示：
  - 新增：4
  - 跳过：0
  - 错误：0
  - 导入批次：预检
- 截图证据：
  - `output/p3_06u_26h2d_knowledge_update_package/knowledge-update-package-preview.png`
- 验证摘要：
  - `output/p3_06u_26h2d_knowledge_update_package/summary.json`

## 7. 本片暴露出的真实问题

浏览器验收时发现前端已经更新，但本地 8081 端口仍运行旧后端进程，导致新接口返回 `404 Not Found`。

处理方式：

- 定位旧进程占用 `127.0.0.1:8081`。
- 重启本地后端到最新代码。
- 重新运行浏览器 smoke，验证通过。

这个问题需要写入后续产品化更新器：程序更新不能只替换文件，还必须检查本地后端进程是否已重启到新版本，并提供健康检查结果。

## 8. 下一片建议

下一步建议进入 P3-06U-26H2E：签名更新包与程序更新器设计第一片。

优先做五件事：

1. 定义知识包、策略包、程序包三类更新包边界。
2. 增加更新包签名和校验字段。
3. 增加导入前本地备份点。
4. 增加导入后健康检查和评测回归。
5. 设计客户侧“检查更新、导入更新、失败回滚”的正式界面。

签名和备份做完之前，知识更新包只适合内部试点和受控客户现场，不适合无人值守自动更新。
