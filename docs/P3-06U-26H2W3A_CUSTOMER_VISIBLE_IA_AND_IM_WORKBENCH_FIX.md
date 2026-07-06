# P3-06U-26H2W3A 客户可见信息架构收口与对话台 IM 化修复

日期：2026-07-03

## 1. 本阶段目标

本阶段只处理客户可见前端与门禁口径，不开放真实外发，不接入新的官方渠道，不修改模型调用策略。

目标是把客服中台从“工程试验台味道”继续收束为小微企业可理解的本地客服产品：

- 总览页保持 BI 指挥舱，不再暴露待审、待发、工单后台池。
- 多渠道对话台继续向真实客服 IM 形态靠拢，左侧只保留会话列表，右侧只保留对话流和转人工接管输入区。
- 客户可见页面不再出现 API、sandbox、outbox、connector_noop、P3-06、H2W 等工程词。
- 总览、质量复盘、知识缺口不再跳转到隐藏后台页：`#reviews`、`#outbox`、`#conversations`、`#tickets`。
- 旧门禁脚本改为新的产品口径：检查三队列、消息流、外发边界、无旧审核/待发文案。

## 2. 子智能体交叉审查结论

本阶段派发 3 个只读审查子智能体：

| 子智能体 | 审查方向 | 关键结论 | 处理结果 |
|---|---|---|---|
| Dalton | 客户可见工程词、隐藏路由、假按钮 | 未发现 P0；发现渠道页旧沙盒面板、知识缺口跳 `#reviews`、客户页 `API` 和阶段编号残留 | 已移除旧沙盒面板，隐藏路由改到 `#live`，工程词改为客户语言 |
| Tesla | 知识运营真实性 | 业务对象、知识包、知识缺口、回归评测多数是真后端链路；“编辑知识草稿”命名和“完整准确率”口径需继续修 | 已写入矩阵和后续事项，后续把知识页继续压成四步维护流程 |
| Linnaeus | 多渠道对话台 UX | 双栏结构成立，但主屏仍像事件记录台；旧队列和 outbox/review 事件不应占据聊天主屏 | 已收束为三队列，主聊天区不再直接展示 outbox 状态和失败详情 |

## 3. 本次代码改动

### 3.1 多渠道对话台

改动文件：

- `frontend/src/components/conversation/ConversationWorkbenchPanel.tsx`
- `frontend/src/styles.css`
- `scripts/check_p3_06u_10b_conversation_workbench_simplification.mjs`
- `scripts/check_p3_06u_26h2v_console_ia_alignment.mjs`

已完成：

- 会话筛选收束为 `全部 / 我的 / 转人工`。
- 高风险、无知识、超时、失败、未分配等信号不再变成客户可见二级队列，统一归入转人工来源。
- 右侧主屏不再把 outbox 草稿、失败复盘、队列状态直接渲染成聊天气泡。
- “AI 建议/客户可见回复预案/待审/待发”进入门禁黑名单。
- 左侧列表从卡片化收窄为更接近 IM 会话列表，单项高度保持 82px，避免过瘦。
- 外发边界保留为“真实外发关闭”，不宣称平台已接通。

### 3.2 总览与质量页

改动文件：

- `frontend/src/App.tsx`
- `frontend/src/components/quality/QualityReviewPanel.tsx`

已完成：

- 总览页中的“待审核/待发送草稿/人工审核压力”改为“转人工/待处理回复/转人工压力”。
- 总览优先动作从“确认待发送草稿”改为“确认待处理回复”。
- 质量复盘的根因文案从“待发门禁”改为“回复闭环”。
- 质量复盘入口统一导向 `#live`、`#gaps`、`#evals`、`#channels` 等客户可见工作页。

### 3.3 渠道接入页

改动文件：

- `frontend/src/components/channels/ChannelConnectorCenterPanel.tsx`
- `frontend/src/App.tsx`

已完成：

- 从客户可见渠道页移除旧 `CopilotSandboxPanel`。
- “官方 sandbox 优先级”改为“官方测试接入优先级”。
- “RPA draft-only”改为“RPA 只做草稿”。
- “人工审核/待发送门禁/沙盒入站”改为“转人工/待确认回复/测试入站”。
- “API”改为“官方接口/服务端能力”。
- 渠道健康说明从“入站、出站”改为“入站、链路状态”。

### 3.4 全局状态条与导航

改动文件：

- `frontend/src/components/common/WorkspaceState.tsx`
- `frontend/src/data/navigation.ts`

已完成：

- “来自当前租户 API 与数据库”改为“来自当前租户服务与数据库”。
- “真实 API 未启用”改为“正式服务未启用”。
- 角色任务里的“查看自动回复”改为“抽查接待记录”。
- 任务描述从“AI 自动回复记录”改为“会话、知识命中和转人工状态”。

## 4. 验收证据

已运行：

```bash
cd /Users/ericlee/Desktop/01_项目工作区/肥肥lu/lite_a_customer_service/standard_ops/frontend
npm run typecheck
npm run build

cd /Users/ericlee/Desktop/01_项目工作区/肥肥lu/lite_a_customer_service/standard_ops
node scripts/check_p3_06u_26h2v_console_ia_alignment.mjs
node scripts/check_p3_06u_10b_conversation_workbench_simplification.mjs
node scripts/audit_p3_06u_26h2w3_frontend_clicks_and_ux.mjs
```

结果：

| 验收项 | 结果 | 证据目录 |
|---|---:|---|
| TypeScript 类型检查 | 通过 | 终端输出 |
| 前端生产构建 | 通过 | `frontend/dist/` |
| H2V 信息架构门禁 | 通过 | `output/p3_06u_26h2v_console_ia_alignment` |
| 10B 对话台 IM 化门禁 | 通过 | `output/p3_06u_10b_conversation_workbench_simplification` |
| H2W3 逐页点击深审 | 0 issues | `output/p3_06u_26h2w3_frontend_deep_audit` |

浏览器深审最终结果：`Issues: 0`。

## 5. 当前仍不能承诺

以下能力仍未进入正式完成态：

- 真实企业微信、公众号、抖音、小红书、淘宝、京东等官方通道全链路接入。
- 真实平台外发。
- 真实平台回执、失败重试、白名单发送闭环。
- 线上准确率下降自动诊断闭环。
- 客户自主上传 XLS/PDF/DOCX 后自动形成成熟知识库的完整签收流程。
- 完整客户侧版本更新、诊断包上传、远程补丁回传闭环。

## 6. 下一步建议

下一步不要再扩散页面功能，应继续做“六点剩余目标”里的可验证工程片：

1. 线上回执与准确率：先在本地模拟回执和失败原因，形成质量复盘输入。
2. XLS/PDF/DOCX 正式签收：实现客户资料上传、解析、预检、导入、回归题生成。
3. 云接收台：实现诊断包上传、版本包下载、更新记录。
4. 真实更新恢复：实现备份、恢复、版本升级回滚。
5. 生产级 RAG 与模型成本治理：把知识检索、模型调用、成本口径落到客户可理解的自动回复策略。
6. 客户知识发布流程：把业务对象、标准问答、流程政策、禁用承诺、转人工规则做成产品内引导。

## 7. 停止门禁

后续任何前端迭代如果出现以下情况，应停止继续加功能，先修真实性：

- 客户可见页出现 API、sandbox、outbox、connector_noop、P3-06、H2W 等工程词。
- 客户可见页直达 `#reviews`、`#outbox`、`#conversations`、`#tickets`。
- 多渠道对话台重新出现待审、待发、AI 建议、客户可见回复预案等旧主屏文案。
- 渠道接入页暗示已接通所有平台或可以自动真实外发。
- 知识评测被包装成完整线上客服准确率。
- 有按钮可点击但没有前端动作、后端接口、禁用理由或成功/失败反馈。
