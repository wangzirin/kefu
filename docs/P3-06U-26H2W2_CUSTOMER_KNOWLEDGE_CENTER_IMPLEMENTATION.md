# P3-06U-26H2W-2 客户知识建设中心第一片

## 目标

把小微企业能理解、能自己维护的知识入口落到产品里，不再只依赖“编辑知识草稿”这一类工程化入口。

本片只做四层知识中心第一片：

- 业务对象：商品、服务、套餐、课程、项目、门店。
- 标准问答：绑定到具体业务对象的问题、答案、触发关键词。
- 流程政策：售后、发票、退款、质保、服务流程等文档或知识包。
- 禁用承诺与转人工规则：写入本地自动回复策略，回复决策运行时会读取。

## 已完成

- 新增后端自动回复策略接口：
  - `GET /api/tenants/{tenant_id}/reply-strategy`
  - `PATCH /api/tenants/{tenant_id}/reply-strategy`
- 新增后端文件：
  - `backend/app/api/reply_strategies.py`
  - `backend/app/services/reply_strategies.py`
  - `backend/app/schemas/reply_strategies.py`
- 前端新增：
  - 客户知识建设中心四层卡片。
  - 自动回复策略编辑卡。
  - 禁止承诺词、转人工词、只生成草稿开关。
  - 保存后写入 `tenant_reply_strategies`，不是只存在前端状态。
- 默认知识更新包模板补充：
  - 流程政策标签。
  - 禁用承诺与转人工规则文档。
- 新增门禁脚本：
  - `scripts/check_p3_06u_26h2w2_customer_knowledge_center.py`
  - `scripts/smoke_p3_06u_26h2w2_reply_strategy_api.py`

## 验收结果

- `python3 scripts/check_p3_06u_26h2w2_customer_knowledge_center.py` 通过。
- `backend/.venv/bin/python -m py_compile backend/app/api/reply_strategies.py backend/app/services/reply_strategies.py backend/app/schemas/reply_strategies.py scripts/smoke_p3_06u_26h2w2_reply_strategy_api.py` 通过。
- `python3 scripts/smoke_p3_06u_26h2w2_reply_strategy_api.py` 通过：
  - 临时 SQLite。
  - 临时负责人账号。
  - 读取默认空策略。
  - 保存禁止承诺词、转人工词和只生成草稿开关。
  - 再读取确认已持久化。
  - `external_write_performed=false`。
  - `model_call_performed=false`。
- `npm run build` 通过，仍只有既有 Vite chunk 体积提醒。
- `node scripts/check_p3_06u_26h2w0_knowledge_operations_owner_login.mjs` 通过，证明原有知识运营写入链路仍可用。

## 当前边界

- 本片没有打开真实外发。
- 本片没有接真实企业微信、公众号、抖音、淘宝、京东、拼多多。
- 本片没有调用模型。
- 本片没有完成生产级 RAG。
- 本片没有证明完整线上客服准确率。
- 本片证明的是：客户知识四层入口可见，核心写入路径可用，禁用承诺/转人工规则已经能进入本地自动回复策略。

## 下一步

- 继续 H2W-2：把流程政策发布前样题试跑和发布版本记录做成更清晰的客户流程。
- 或进入 H2W-3：线上回执与准确率第一片，但真实 IM 和真实外发仍暂缓。
- 或进入 H2W-7：生产级检索与成本治理第一片，明确 pgvector、混合检索、重排和模型成本口径。
