# P3-06U-24 知识运营三页分离与渠道账号模型第一片

日期：2026-07-02

## 1. 本轮目标

本轮针对两个问题收口：

1. 知识运营下的“知识库运营、知识缺口、知识评测”看起来仍像同一个页面，用户无法快速判断三个入口各自承担什么工作。
2. 多渠道对话台已经能展示平台、账号、店铺和入口，但这些信息主要来自前端演示样本，还没有形成后端可读取的渠道账号/店铺身份模型。

本轮不做真实平台外发，不接入真实微信、抖音、淘宝、京东、拼多多账号，也不读取真实平台密钥。

## 2. 真实问题判断

### 2.1 知识三页的问题不是没有组件，而是首屏职责混淆

代码里原本已经有三条路由：

- `#knowledge`：知识文档、业务对象、对象问答卡、文档检索。
- `#gaps`：知识缺口、草稿生成、回归题、发布修复。
- `#evals`：评测集、评测运行、评测结果。

但三条路由都把同一个 `KnowledgeOperationsFlowPanel` 放在上方或过重位置，导致用户进入后先看到相似的知识流程总览。实际体验上会误判为“三个入口没有切开”。

本轮将三页重新按“首屏即主职责”的方式处理：

| 页面 | 当前首屏主职责 | 该页应该解决的问题 |
| --- | --- | --- |
| 知识库运营 | 业务对象、标准问答、文档草稿、引用来源和文档检索 | 客服回答到底从哪些可追溯知识里来 |
| 知识缺口 | 无知识命中、低置信、评测失败、人审失败的修复待办 | 哪些问题答不好，怎么补知识和加入回归 |
| 知识评测 | 固定题集、运行评测、命中率、引用覆盖、期望词覆盖 | 新知识发布前后质量是否变好或变差 |

### 2.2 三页现在的功能评价

知识库运营：已能承担“知识输入与检索”的工作。当前可维护业务对象、对象问答卡、文档、片段、发布记录和本地检索结果。仍然不是完整生产级 RAG，因为生产向量库、真实客户文档导入、重排质量和人工事实性标注还需要后续验收。

知识缺口：已能承担“错因进入修复队列”的工作。当前可以展示缺口来源、严重度、期望词、是否已生成草稿、是否加入回归、是否发布。仍需后续补真实客户问题来源、批量分派、责任人、修复时效和质量复盘深链。

知识评测：已能承担“固定题集回归”的工作。当前能创建评测集、运行评测、查看最近运行、命中率、引用覆盖和期望词覆盖。它已经切出独立页面，但仍需真实客户 50-100 题、人工事实性标签、生成答案评测和发布前后对比报告增强。

## 3. 本轮实现

### 3.1 前端信息架构

修改文件：

- `frontend/src/App.tsx`
- `frontend/src/api/client.ts`

关键调整：

- `#knowledge` 首屏直接渲染 `KnowledgeDocumentsPanel`，标题为“知识库运营”，增加 `data-knowledge-primary="library"`。
- `#gaps` 首屏直接渲染 `KnowledgeGapPanel`，标题为“知识缺口处理”，增加 `data-knowledge-primary="gaps"`。
- `#evals` 首屏直接渲染 `KnowledgeEvaluationPanel`，标题为“知识评测中心”，增加 `data-knowledge-primary="evals"`。
- 公共知识流转面板保留为辅助闭环信息，不再作为三个入口的首屏主内容。
- 多渠道对话台的渠道身份不再只依赖前端演示样本，新增读取后端 `channel_accounts` 的只读刷新链路。

### 3.2 后端渠道账号/店铺实体

修改文件：

- `backend/app/models/foundation.py`
- `backend/app/models/__init__.py`
- `backend/app/migrations/versions/0025_channel_accounts.py`
- `backend/app/schemas/channel_connectors.py`
- `backend/app/services/channel_connectors.py`
- `backend/app/api/channel_connectors.py`
- `backend/tests/test_channel_connectors_api.py`

新增能力：

| 能力 | 接口 |
| --- | --- |
| 查询租户渠道账号/店铺身份 | `GET /api/tenants/{tenant_id}/channel-accounts` |
| 配置某渠道下的账号/店铺身份 | `POST /api/channels/{channel_id}/channel-accounts` |

新增表：`channel_accounts`

核心字段：

- `tenant_id`
- `channel_id`
- `connector_id`
- `provider`
- `platform`
- `account_name`
- `external_account_id`
- `store_name`
- `entrypoint_name`
- `authorization_status`
- `access_status`
- `reply_mode`
- `health_status`
- `public_profile`
- `last_sync_at`

安全边界：

- `public_profile` 会做敏感字段脱敏。
- API 返回不包含 `external_write_enabled`。
- 审计事件会记录本次配置仍为 `external_write_enabled=false`。
- 该模型只用于中台识别“这条会话来自哪个平台账号/店铺/入口”，不代表真实平台已经授权，也不代表能真实发送消息。

## 4. 验收结果

### 4.1 后端接口测试

命令：

```bash
cd /Users/ericlee/Desktop/01_项目工作区/肥肥lu/lite_a_customer_service/standard_ops/backend
.venv/bin/pytest tests/test_channel_connectors_api.py -q
```

结果：

```text
5 passed
```

仅有既有 `StarletteDeprecationWarning`，不影响本轮功能。

### 4.2 前端类型与构建

命令：

```bash
cd /Users/ericlee/Desktop/01_项目工作区/肥肥lu/lite_a_customer_service/standard_ops/frontend
npm run typecheck
npm run build
```

结果：

```text
typecheck passed
build passed
```

构建仍有既有 Vite chunk 体积提醒，不影响本轮知识页和渠道账号功能。

### 4.3 浏览器验收

新增脚本：

```text
scripts/check_p3_06u_24_knowledge_split_and_channel_accounts.mjs
```

命令：

```bash
cd /Users/ericlee/Desktop/01_项目工作区/肥肥lu/lite_a_customer_service/standard_ops
node scripts/check_p3_06u_24_knowledge_split_and_channel_accounts.mjs
```

结果：

```text
P3-06U-24 knowledge split check passed.
```

验收覆盖：

- 1440 桌面视口和 390 手机视口。
- `#knowledge` 首个主面板为“知识库运营”。
- `#gaps` 首个主面板为“知识缺口处理”。
- `#evals` 首个主面板为“知识评测中心”。
- 三页均无横向溢出。
- 多渠道对话台仍能展示渠道账号身份和回复模式。

截图目录：

```text
output/p3_06u_24_knowledge_split/
```

## 5. 本轮边界

本轮已经完成：

- 知识运营三个入口的首屏职责分离。
- 三页的浏览器级回归检查。
- 渠道账号/店铺身份的后端表、schema、service、API 和测试。
- 前端从后端读取渠道账号身份并映射到对话台展示。

本轮没有完成：

- 真实企业微信、公众号、抖音、淘宝、京东、拼多多官方账号授权。
- 真实平台消息发送。
- 真实平台消息回执 reconciliation。
- 完整生产级向量库和重排质量验收。
- 真实客户知识包和 50-100 条人工事实性题库。
- 知识三页的最终视觉重做和组件拆分。

## 6. 下一步建议

建议进入 `P3-06U-25`：

1. 把知识三页继续从 `App.tsx` 拆成独立组件，避免后续继续堆在一个大文件里。
2. 渠道接入页新增“渠道账号/店铺管理”真实配置面板，调用本轮新增的后端接口。
3. 多渠道对话台会话列表继续接入真实 `channel_accounts`，把“平台账号/店铺/入口”从演示样本升级为服务端数据。
4. 知识缺口页继续增强错因定位：无命中、引用不足、期望词缺失、人工驳回、策略阻断分别给出不同修复动作。
5. 知识评测页继续增强发布前后对比和真实客户题库导入，不把当前检索命中率包装成完整客服准确率。
