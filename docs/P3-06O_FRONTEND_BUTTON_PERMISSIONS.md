# P3-06O 前端按钮级权限第一片

日期：2026-07-01  
范围：客服中台前端关键动作按钮、处理函数 guard、出站发送计划前端权限提示  
状态：第一片完成

## Engineering Control Card

- Stage: P3-06O 前端按钮级权限第一片
- 当前主线阶段: RBAC 前端闭环
- 上一阶段真正完成: P3-06N 已把渠道连接器、回执和发送计划后端入口迁到命名权限
- 上一阶段明确没有完成: 前端按钮仍主要依赖登录态、角色粗判断或局部业务状态，未统一读取 `user.permissions`
- 本轮要交付的客户可见价值: 不同角色进入同一中台时，关键动作按钮会按后端权限快照禁用；坐席不会看到自己必然无法完成的连接器管理动作，查看角色也不能在前端触发高风险写动作
- 本轮是否只是评测: 否
- 本轮不做什么: 不新增后端权限、不改数据库、不打开真实外发、不新增真实渠道发送器、不重排 UI、不做字段脱敏
- 外部风险: 无真实外发；所有渠道动作仍保持内部计划或队列状态
- 需要用户授权的动作: 无
- 验证方式: 前端 typecheck、前端构建、P3-06O 静态 readiness 检查
- 写回文件: 产品化总控手册、Superpowers P3 计划、Workspace Project_012 记录
- 下一阶段: 继续补 outbox draft、dry-run send-attempt、delivery failure review 后端命名权限，或进入字段脱敏/只读字段 allowlist

## 1. 权限来源

前端不再自行根据 `owner/admin` 推断关键动作权限。本轮在 `frontend/src/App.tsx` 增加统一权限常量：

| 前端常量 | 后端权限 |
| --- | --- |
| `conversationManage` | `conversation.manage` |
| `ticketManage` | `ticket.manage` |
| `leadManage` | `lead.manage` |
| `knowledgeRead` | `knowledge.read` |
| `knowledgeManage` | `knowledge.manage` |
| `channelConnectorManage` | `channel.connector.manage` |
| `outboxSendPlanManage` | `outbox.send_plan.manage` |

判断统一走 `hasPermission(user, permission)`，权限数据来自登录和 `/api/auth/me` 返回的 `CurrentUser.permissions`。

## 2. 已接入的前端动作

| 页面 | 动作 | 前端权限 |
| --- | --- | --- |
| 会话收件箱 | 领取、重开、等待客户、解决、释放 | `conversation.manage` |
| 多渠道对话台 | 领取、重开、等待客户、解决 | `conversation.manage` |
| 人工审核收件箱 | 批准入待发送、拒绝 | `conversation.manage` |
| 官网 Copilot 沙盒 | 运行入站编排 | `conversation.manage` |
| 工单/SLA | 从会话生成工单、更新工单状态、解决工单 | `ticket.manage` |
| 线索跟进 | 从会话生成线索、推进线索阶段、成交、无效 | `lead.manage` |
| 知识文档运营 | 导入文档、回滚文档 | `knowledge.manage` |
| 知识缺口闭环 | 同步缺口、生成草稿、加入回归、发布知识、更新状态 | `knowledge.manage` |
| 知识评测与质量 | 创建评测集、运行评测、查看运行详情、导出报告 | `knowledge.manage` |
| 待发送草稿 | 确认待发送、模拟发送、生成渠道计划、加入发送队列、运行发送检查、运行发送队列 | P3-06O 第一片临时统一使用 `outbox.send_plan.manage`；P3-06P 已拆为 `outbox.draft.manage`、`outbox.send_attempt.manage`、`outbox.delivery_job.manage` |

## 3. 连接器动作的特殊处理

P3-06N 后，`agent` 可以生成受控发送计划，但不能配置连接器。

因此前端在出站动作里做了拆分：

- 拥有 `outbox.send_plan.manage` 的用户可以点击生成渠道计划。
- 只有拥有 `channel.connector.manage` 的用户才会在生成计划前自动调用 `ensureNoopChannelConnector()` 预置连接器。
- 没有连接器管理权限但有发送计划权限时，页面会提示“需管理员预先配置连接器”。

这样可以避免坐席因为自动预置连接器而触发必然 403，同时保留“坐席可生成受控发送计划”的后端设计。

## 4. 双层防线

本轮不是只改按钮禁用状态。

同时完成两层处理：

- 视觉和交互层：按钮根据权限、登录态、加载态和业务状态禁用。
- 事件处理层：对应 handler 再次检查 `hasPermission()`，防止绕过 disabled 状态后主动发起接口调用。

这仍然不是安全边界的全部。真正的安全边界仍以后端 `require_permission()` 为准，前端只负责减少误导和误触。

## 5. 未完成边界

本轮只做第一片，以下内容没有完成：

- 字段脱敏和字段 allowlist。
- `outbox draft` 创建/确认、`dry-run send-attempt`、`delivery failure review` 的后端命名权限细分已在 P3-06P 完成。
- 单独的人审权限，例如未来可拆 `human_review.manage`。
- 连接器配置页、手工回执页和密钥轮换页的完整前端管理界面。
- 多租户客户级管理员、主管、质检等更细角色 UI。
- 生产级真实外发开关、真实平台 token、真实渠道 API smoke。

## 6. 验收结果

- `npm run typecheck` 通过。
- `npm run build` 通过。
- 新增 `scripts/check_p3_06o_frontend_button_permissions.py`，静态检查权限常量、helper、按钮 props、处理函数 guard、连接器拆分逻辑、旧角色粗判断清理和文档写回。

## 7. 下一步建议

1. 字段 allowlist：联系人、线索、回执 raw payload、连接器 public config、审计事件按角色收口。
2. 拆人审权限：如果后续存在质检、主管和坐席不同职责，单独新增 `human_review.read` / `human_review.manage`。
3. 做真实角色截图 QA：分别用 owner、admin、agent、viewer 登录截关键页面，确认按钮禁用、可见区域和导航一致。
4. 企微官方 smoke 条件具备后，继续公网 HTTPS URL 验证、Token/AESKey 回调和白名单入站测试；真实外发仍需单独授权。
