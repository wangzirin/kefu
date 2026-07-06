# P3-06U-23 渠道账号/店铺实体与预览稳定性第一片

日期：2026-07-02

## 本轮目标

本轮先解决两个真实使用问题：

1. 本地预览不能稳定打开。之前服务端口正常，但手动打开容易停在登录入口或遇到前端空白页，影响继续评审。
2. 多渠道对话台只有“渠道标签”，还不能明确显示每条会话来自哪个平台账号、店铺或入口，不利于后续对接微信客服、抖音、淘宝、京东、拼多多等入口。

## 已完成

- 新增演示直达入口：`http://127.0.0.1:5182/?demo=1#live`。
- 当 URL 带 `?demo=1` 时，前端会清理本地 token，并自动进入开发演示态，不再要求先点“开发演示进入”。
- 多渠道对话台新增渠道来源条：平台、账号、店铺 / 入口、接入状态、回复模式。
- 会话列表新增来源账号与入口信息，保留后续从真实渠道回填数据的 UI 承载位。
- 演示数据补齐微信客服、抖音、淘宝、京东、拼多多、官网六类来源实体。
- 左侧会话列表从最大 236px 收窄到 224px，右侧聊天区在 1440px 视口保持主导。
- 固化浏览器验收脚本：`scripts/check_p3_06u_23_channel_identity_preview.mjs`。

## 重要修复

本轮排查到两个导致“预览打不开 / 空白页”的真实根因：

- `useMemo` 被放在登录页早退之后，进入演示态后 React hooks 数量变化，触发 `Rendered more hooks than during the previous render`。
- `ConversationWorkbenchPanel` 在会话数据加载瞬间 `selectedConversation=null`，但空状态 return 写得太晚，提前读取了 `selectedConversation.sla_status` 和 `selectedConversation.channel_name`。

修复后，空数据阶段会先进入“暂无会话”占位，不再崩溃。

## 当前边界

- 本片只完成前端与演示数据的“来源实体视图”。
- 还没有新增后端 `channel_accounts`、`store_accounts` 或 `channel_entrypoints` 表。
- 真实渠道仍未自动外发；微信客服、抖音、淘宝、京东、拼多多真实回复仍必须走官方 API、授权、回调、白名单和外发开关。
- RPA 仍只保留为内部研究与 draft-only 试验，不作为正式自动回复接入方式。

## 验证

已通过：

```bash
cd /Users/ericlee/Desktop/01_项目工作区/肥肥lu/lite_a_customer_service/standard_ops/frontend
npm run typecheck
npm run build

cd /Users/ericlee/Desktop/01_项目工作区/肥肥lu/lite_a_customer_service/standard_ops
CHROME_DEBUGGING_URL=http://127.0.0.1:9227 FRONTEND_URL='http://127.0.0.1:5182/?demo=1#live' node scripts/check_p3_06u_23_channel_identity_preview.mjs
```

浏览器证据：

- `output/p3_06u_23_channel_identity_preview/summary.json`
- `output/p3_06u_23_channel_identity_preview/desktop-1440.png`
- `output/p3_06u_23_channel_identity_preview/mobile-390.png`

验收结果：

- 桌面与手机视口均可自动进入演示。
- 不停留在登录页。
- 不出现空白页。
- 无运行时异常。
- 无横向溢出。
- 渠道来源条和回复决策条均可见。
- 1440px 视口左侧会话列表 224px，右侧聊天区 892px。

## 下一步建议

P3-06U-24 建议进入“渠道账号/店铺实体后端模型第一片”：

- 新增渠道账号表，保存平台、账号名称、店铺 / 入口、授权状态、回复模式、健康状态。
- 会话入站时把 `channel_id` 映射到具体账号 / 店铺实体。
- 前端从后端读取来源实体，不再只依赖演示数据。
- 渠道接入页与多渠道对话台共享同一份渠道账号状态。
- 继续保持真实外发关闭，先完成只读来源追踪和审计。
