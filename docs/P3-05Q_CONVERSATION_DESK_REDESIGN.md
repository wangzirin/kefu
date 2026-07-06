# P3-05Q 多渠道对话台主工作区重构

日期：2026-07-01  
阶段：P3-05Q  
范围：前端对话台主工作区第一片  
结论：对话台已经从“演示型三栏面板”升级为更接近真实坐席日常使用的工作台，但仍不代表真实全渠道外发已经接通。

## Engineering Control Card

- Goal: 让 `#live` 对话台成为客服坐席处理会话的主工作界面，而不是只展示模块的验收页。
- Customer-visible value: 坐席可以按队列进入会话，查看事件时间线、AI 草稿、知识引用、发送异常和客户上下文。
- Scope: 只改前端工作台呈现；复用现有会话、人审、outbox、失败复盘、发送队列和知识证据数据。
- Non-goal: 不新增真实平台外发；不接抖音、淘宝、京东、拼多多真实 API；不新增完整 message history 后端接口；不做 P3-05R 质量 BI。
- Stop condition: `#live` 有队列、有事件流、有右侧检查器、桌面和移动端不横向溢出，构建通过。

## 本轮改了什么

### 1. 队列分组

新增 8 个坐席队列入口：

| 队列 | 用途 |
|---|---|
| 全部 | 当前页会话池 |
| 我的 | 已分配给当前坐席 |
| 未分配 | 需要坐席领取 |
| 待审核 | AI 草稿需要人工核对 |
| 超时 | SLA 已超时 |
| 高风险 | 投诉、赔付、法务或高责任问题 |
| 无知识 | 无知识命中、低置信或需补 FAQ |
| 发送异常 | outbox 或渠道失败复盘 |

当前队列筛选是前端基于已加载会话、本页人审和失败复盘记录计算。生产大数据量下仍需要后端 server-side queue counts。

### 2. 会话事件时间线

原来对话区只有三条合成消息：客户入站、AI 草稿、系统门禁。现在改为从现有业务记录拼出事件流：

- 客户入站
- 进入人工审核
- AI 草稿生成
- 待发送草稿
- 发送队列任务
- 发送失败复盘
- 系统门禁

这不是完整历史聊天记录。完整聊天历史还需要后端提供 `conversation messages/events timeline` API。

### 3. 坐席动作集中

会话顶部新增建议动作和主操作：

- 领取 / 接手 / 重开
- 等客户
- 解决

草稿区动作集中为：

- 审核草稿
- 查看知识 / 补知识
- 建工单

这样坐席先看“建议动作”，再处理草稿或跳到相关模块。

### 4. 右侧上下文检查器

右侧从固定证据面板改成 4 个检查器标签：

| 标签 | 内容 |
|---|---|
| 客户 | 渠道、主题、等待时间、优先级、坐席分配 |
| AI | 模型路由、置信度、风险等级、草稿来源、人审门禁 |
| 知识 | 命中知识、片段预览、来源 URI |
| 运营 | 人审、待发送、队列任务、失败复盘、外部写入状态 |

这更接近成熟客服系统的右侧上下文面板。

### 5. 视觉与响应式

新增：

- 顶部坐席信号条。
- 队列 tab 卡。
- 真实工作台三列布局：队列、事件流、上下文检查器。
- 时间线事件卡片。
- 草稿编辑区。
- 右侧 segmented tabs。
- 1180px 以下单列降级，390px 移动端不横向溢出。

## 文件改动

- `frontend/src/App.tsx`
  - 重构 `ConversationWorkbenchPanel`。
  - 新增 `WorkbenchQueueKey`、`WorkbenchInspectorTab`、`WorkbenchQueueDefinition`、`ConversationTimelineEvent`。
  - 新增 `buildConversationTimeline`、`buildConversationNextBestAction`。
- `frontend/src/styles.css`
  - 新增对话台队列、坐席信号、三列工作区、事件时间线、草稿区和检查器样式。
  - 补充响应式规则。
- `frontend/src/data/navigation.ts`
  - 阶段标识从 `P3-05O` 更新为 `P3-05Q`。

## 验证结果

### 构建

已运行：

```bash
npm run build
```

结果：

- `tsc` 通过。
- `vite build` 通过。

### 浏览器检查

使用本机 Chrome DevTools 协议打开真实本地预览：

```text
http://127.0.0.1:5175/#live
```

先进入开发演示身份，再检查 `#live`。

桌面 1440x1000：

- `liveExists=true`
- `queueTabCount=8`
- `timelineCount=6`
- `inspectorTabs=客户 / AI / 知识 / 运营`
- `actionButtonCount=3`
- `overflowX=false`
- `consoleIssueCount=0`

移动端 390x1200：

- `liveExists=true`
- `queueTabCount=8`
- `timelineCount=6`
- `overflowX=false`
- `consoleIssueCount=0`

截图：

```text
/Users/ericlee/Desktop/肥肥lu/lite_a_customer_service/standard_ops/output/p3_05q_conversation_workbench/p3_05q_conversation_workbench_desktop.png
/Users/ericlee/Desktop/肥肥lu/lite_a_customer_service/standard_ops/output/p3_05q_conversation_workbench/p3_05q_conversation_workbench_mobile.png
```

## 当前仍不能承诺

- 不能承诺真实平台外发已经接通。
- 不能承诺抖音、淘宝、京东、拼多多、小红书或公众号已经能自动回复。
- 不能承诺对话台已经拥有完整历史消息 API。
- 不能承诺高并发已经解决。
- 不能承诺质量 BI 已经完成；P3-05R 才做错因 BI。

## 下一步

推荐进入 P3-05R：质量复盘升级为错因 BI。

P3-05R 应包含：

1. 错因 Pareto。
2. 质量漏斗。
3. 知识覆盖热力图。
4. 渠道失败堆叠图。
5. 人审结果矩阵。
6. 样本下钻到会话、人审、知识缺口、评测题。
