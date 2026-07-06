# P3-06R-03A 坐席工作台一屏闭环第一片

日期：2026-07-01

## 工程总控卡

- 阶段归属：P3-06R 阶段 5，坐席工作台一屏闭环。
- 本片目标：把现有 `#live` 多渠道对话台从“会话预览页”推进为坐席可实际处理的主工作区第一片。
- 客户可见价值：坐席在同一屏看到会话队列、对话时间线、AI 草稿、知识引用、风险状态、内部备注和放行动作，不再必须在人工审核、会话收件箱、待发送之间来回跳。
- 是否只是评测：否。本片是产品工作台能力，不是新增离线评测。
- 外部动作边界：不打开真实外发，不创建真实发送计划，不运行发送队列，不触达企业微信、公众号、抖音、小红书、淘宝、京东或拼多多。
- 写回位置：本文件、`P3-06R_ENGINEERING_OPTIMIZATION_PLAN.md`、`PRODUCTIZATION_MASTER_PLAN_LITE_AND_STANDARD.md`、Superpowers P3 总计划、Project_012 记录文件。

## 本片完成内容

### 1. AI 草稿从只读预览改为坐席可编辑

文件：`frontend/src/App.tsx`

- `ConversationWorkbenchPanel` 新增本地 `editableDraft`。
- 选中会话、人审任务或 outbox 草稿变化时，自动同步当前草稿。
- 草稿区从 `readOnly` textarea 改为可编辑 textarea。
- 文案明确为“坐席确认后的回复内容”，避免误解为模型直接外发。

### 2. 内部备注 / 审核意见进入同一屏

文件：`frontend/src/App.tsx`

- 新增 `internalNote`。
- 坐席可以在同一屏记录修改原因、风险判断、需补知识点或转人工原因。
- `handleConversationWorkflowAction` 支持可选备注参数；旧调用保持兼容，未传备注时仍使用默认动作备注。
- 新增“只记内部备注”动作，走 `conversation.workflow-actions` 的 `note` 动作。

### 3. 知识引用确认变成放行门禁

文件：`frontend/src/App.tsx`

- 新增 `citationsConfirmed`。
- 如果有知识引用，必须先勾选“已核对知识引用和回复事实”，才能点击“批准进入待发送”。
- 如果没有知识引用，界面提示“无知识引用，需谨慎放行或补知识”，但不阻断人工判断。

### 4. 审核批准进入待发送使用真实参数

文件：`frontend/src/App.tsx`

- `handleReviewApprove` 支持传入编辑后的 `finalReply` 和 `resolutionNote`。
- `#live` 工作台上的“批准进入待发送”会调用：
  - `resolveHumanReviewTask(taskId, { decision: "approved", final_reply, resolution_note })`
  - `createOutboxDraftFromReview(taskId)`
- 这仍然只是内部审核和 outbox 草稿创建，不是外部平台发送。

### 5. 发送前确认入口放到同一屏

文件：`frontend/src/App.tsx`

- 新增 `canConfirmOutboxDraft` 和 `onConfirmOutboxDraft`。
- 对已有关联 outbox draft 且状态为 `pending_confirmation` 的会话，在同一屏提供“确认待发送”入口。
- 该动作调用既有 `confirmOutboxDraft`，只把草稿推进到待发送状态，不触达真实渠道。

### 6. 右侧栏补齐处理动作区

文件：`frontend/src/App.tsx`

- 右侧 inspector 新增“处理动作”区。
- 包含：
  - 跟进
  - 标记高风险
  - 标记知识缺口
  - 查看待发送
- 其中“跟进”和“标记高风险”走内部会话动作/备注；“知识缺口”和“待发送”为工作区跳转入口。

### 7. 修复移动端工作台宽度被三栏撑大的问题

文件：`frontend/src/styles.css`

- `.app-shell` 从 `280px 1fr` 改为 `280px minmax(0, 1fr)`。
- 移动端 `.app-shell` 从 `1fr` 改为 `minmax(0, 1fr)`。
- 给对话台壳层、三栏布局、草稿按钮区等关键节点补 `min-width: 0` / `max-width: 100%`。
- 移动端队列 tabs 改为两列，按钮区和右侧动作区改为单列。

## 当前一屏闭环程度

已完成：

- 左栏会话队列：渠道、等待时间、SLA、风险、待审、发送异常。
- 中栏对话线程：客户消息、AI 草稿、人审事件、outbox、发送队列、失败复盘时间线。
- 中栏坐席处理：编辑 AI 草稿、写内部备注、确认引用、批准进入待发送、确认待发送。
- 右栏上下文：客户、AI、知识、运营状态和处理动作。
- 外发边界：所有按钮仍只做内部状态，不做真实平台写入。

仍未完成：

- 未做真实 token 登录下的端到端点击 smoke。
- 未新增服务端组合详情接口；当前仍复用已加载的会话、人审、outbox、失败复盘和 delivery job 数据。
- 未做工单评论、附件、重开、主管分配、跨渠道身份合并。
- 未接真实平台出站发送。
- 未做真实客服坐席高并发排队压测。

## 验证结果

命令验证：

```bash
cd frontend && npm run typecheck
cd frontend && npm run build
```

结果：

- `npm run typecheck` 通过。
- `npm run build` 通过，产物：
  - `dist/assets/index-sXHryeHt.css`
  - `dist/assets/index-CKbrQj_h.js`

浏览器验证：

- 预览地址：`http://127.0.0.1:5175/#live`
- 桌面视口：1440 x 1000
  - `rootExists=true`
  - `composerExists=true`
  - `editTextareaExists=true`
  - `approveExists=true`
  - `sideActionsExists=true`
  - `scrollWidth=1440`
  - `innerWidth=1440`
  - `overflowX=false`
  - `consoleErrors=0`
- 移动视口：390 x 844
  - `rootExists=true`
  - `composerExists=true`
  - `layoutWidth=300`
  - `scrollWidth=390`
  - `innerWidth=390`
  - `bodyScrollY=900`
  - `overflowX=false`
  - `actionGridWidth=270`
  - `consoleErrors=0`

截图证据：

- `output/p3_06r_agent_desk_closure/p3_06r_agent_desk_desktop.png`
- `output/p3_06r_agent_desk_closure/p3_06r_agent_desk_mobile.png`

## 下一步建议

P3-06R-03B 应优先做真实登录下的端到端动作 smoke：

1. 用测试租户和 agent 账号登录。
2. 准备一个 open human review task。
3. 在 `#live` 编辑草稿并填写内部备注。
4. 点击“批准进入待发送”。
5. 断言人审任务变为 resolved/approved。
6. 断言生成 outbox draft，且状态仍是内部待确认或待发送。
7. 点击“确认待发送”。
8. 断言不发生任何外部平台写入。

如果先转入渠道建设，则进入 P3-06R-04 渠道连接器中心第一片。
