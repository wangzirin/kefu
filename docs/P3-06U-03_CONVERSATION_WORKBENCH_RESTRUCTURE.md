# P3-06U-03 接待工作台实用性重构

日期：2026-07-01  
适用项目：万法常世 AI 全智能客服系统标准运营版  
工程目录：`/Users/ericlee/Desktop/肥肥lu/lite_a_customer_service/standard_ops`

## 1. 工程控制卡

| 项目 | 内容 |
| --- | --- |
| 阶段编号 | P3-06U-03 |
| 阶段名称 | 接待工作台实用性重构 |
| 上游阶段 | P3-06U-01 前后端契约矩阵、P3-06U-02 角色化任务路径 |
| 本阶段目标 | 把 `#live` 从普通会话详情页改成坐席可实际工作的三栏 IM 工作台 |
| 本阶段不做 | 不改变后端状态机；不打开真实外发；不伪装抖音、淘宝、京东、拼多多等未授权渠道已接通 |
| 验收方式 | 静态脚本、TypeScript typecheck、生产 build、浏览器三视口 smoke 和截图 |

## 2. 本轮改动

本轮将接待工作台从 `App.tsx` 拆到：

`frontend/src/components/conversation/ConversationWorkbenchPanel.tsx`

新的工作台按真实坐席任务拆成三栏：

| 区域 | 作用 |
| --- | --- |
| 会话队列 | 展示客户头像、渠道、等待时长、SLA、优先级、人工/AI 状态、待审和发送异常 |
| 消息处理区 | 展示客户问题、AI 草稿、人工审核、outbox、发送队列、失败复盘和系统门禁 |
| 右侧上下文 | 展示客户信息、AI 证据、知识引用、运营状态和只更新内部状态的处理动作 |

底部回复区明确拆分三件事：

- 修改 AI 草稿。
- 批准进入待发送。
- 确认待发送。

页面文案明确说明：**审核通过只生成内部待发送草稿；真实发送仍需官方渠道授权、白名单测试和外发开关。**

## 3. 前后端契约对齐

本阶段沿用已有后端契约，不新增伪能力。

| 前端动作 | 后端能力 | 权限 | 状态边界 |
| --- | --- | --- | --- |
| 领取 / 接手 / 重开会话 | `applyConversationWorkflowAction` | `conversation.manage` | 只改变内部会话状态 |
| 等客户 / 解决 | `applyConversationWorkflowAction` | `conversation.manage` | 只改变内部会话状态 |
| 只记内部备注 | `applyConversationWorkflowAction` 的 `note` | `conversation.manage` | 不触达外部平台 |
| 批准进入待发送 | `resolveHumanReviewTask` / 既有审核处理链 | `conversation.manage` + outbox 权限 | 从人审草稿进入 outbox |
| 确认待发送 | `confirmOutboxDraft` | outbox 管理权限 | 仅确认 outbox 草稿，不代表真实发送 |

## 4. 视觉和交互原则

接待工作台不是“功能展示页”，而是坐席工作桌面。

- 左栏优先解决“今天先处理谁”。
- 中栏优先解决“客户问了什么、AI 怎么答、证据够不够、我能不能放行”。
- 右栏优先解决“这个客户是谁、为什么有风险、需要补什么知识、后续去哪处理”。
- 所有真实外发相关能力都保持关闭态表达，不让客户误以为系统已经自动回复到外部平台。

## 5. 代码结构治理

`App.tsx` 已不再内联 `function ConversationWorkbenchPanel`。  
这一步为后续 P3-06U-04 到 P3-06U-09 留出结构空间：新增复杂页面应优先进入对应组件目录，不继续把主流程堆回 `App.tsx`。

## 6. 验证记录

已建立静态检查：

`scripts/check_p3_06u_03_conversation_workbench.py`

检查范围：

- 新组件存在。
- `App.tsx` 使用新组件并移除旧内联函数。
- 工作台包含会话列表、消息区、回复区、上下文区。
- 文案明确区分审核、待发送和真实外发关闭。
- 样式包含三栏布局和坐席工作台关键类。

浏览器 smoke 脚本：

`scripts/check_p3_06u_03_conversation_workbench.mjs`

检查范围：

- 桌面、窄屏、移动三视口能进入 `#live`。
- 工作台关键区域存在。
- 无页面级横向溢出。
- 截图保存到 `output/p3_06u_03_conversation_workbench/`。

## 7. 下一步

下一阶段进入：

**P3-06U-04 运营总览到处理路径打通。**

重点是让运营总览里的高风险会话、待发送草稿、知识缺口、渠道异常能直接进入对应工作区，并保留筛选上下文。不能让首页只停留在漂亮指标展示。
