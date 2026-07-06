# P3-06P RBAC 第八片：出站资源与失败复盘权限

日期：2026-07-01  
范围：outbox draft、dry-run send-attempt、outbox delivery job、delivery failure review  
状态：第八片完成

## Engineering Control Card

- Stage: P3-06P RBAC 第八片
- 当前主线阶段: 后端资源级 RBAC 收口
- 上一阶段真正完成: P3-06O 已让前端关键按钮读取 `user.permissions`
- 上一阶段明确没有完成: 出站草稿、试发记录、发送队列和失败复盘接口仍有“登录即可访问”的旧试点入口
- 本轮要交付的客户可见价值: 坐席能继续完成受控放行和试发；只读角色不能确认草稿、试发或处理失败；全局发送队列只允许 owner/admin 触发
- 本轮是否只是评测: 否
- 本轮不做什么: 不打开真实外发、不新增真实平台 sender、不改数据库结构、不做字段 allowlist、不新增人审独立权限
- 外部风险: 无真实外发；发送队列仍是 no-op/skeleton，`OUTBOX_EXTERNAL_WRITE_ENABLED` 默认关闭
- 需要用户授权的动作: 无
- 验证方式: P3-06P 后端测试、静态 readiness 检查、相关 outbox/渠道/失败复盘回归、前端 typecheck/build
- 写回文件: 产品化总控手册、Superpowers P3 计划、Workspace Project_012 记录
- 下一阶段: 字段脱敏与响应字段 allowlist，或按公网条件继续企业微信 HTTPS 回调 smoke

## 1. 权限矩阵

| 权限 | owner | admin | agent | viewer |
| --- | --- | --- | --- | --- |
| `outbox.draft.read` | 允许 | 允许 | 允许 | 禁止 |
| `outbox.draft.manage` | 允许 | 允许 | 允许 | 禁止 |
| `outbox.send_attempt.read` | 允许 | 允许 | 允许 | 禁止 |
| `outbox.send_attempt.manage` | 允许 | 允许 | 允许 | 禁止 |
| `outbox.send_plan.manage` | 允许 | 允许 | 允许 | 禁止 |
| `outbox.delivery_job.read` | 允许 | 允许 | 允许 | 禁止 |
| `outbox.delivery_job.manage` | 允许 | 允许 | 禁止 | 禁止 |
| `outbox.failure_review.read` | 允许 | 允许 | 允许 | 允许 |
| `outbox.failure_review.manage` | 允许 | 允许 | 允许 | 禁止 |

口径：

- `outbox.draft.manage` 控制从已审核回复生成草稿、确认草稿和取消草稿。agent 保留权限，因为这是坐席放行链路。
- `outbox.send_attempt.manage` 控制 dry-run 试发和 dry-run worker。它仍不触达外部平台，但会写入发送尝试和审计记录。
- `outbox.send_plan.manage` 继续控制官方渠道 no-op 发送计划。agent 可生成计划，但不能配置连接器密钥。
- `outbox.delivery_job.manage` 控制加入发送队列和手动运行发送队列。该入口未来可能连接真实 sender，因此第一片只给 owner/admin。
- `outbox.failure_review.read` 给 viewer 保留只读能力，保证渠道健康和质量复盘页可展示异常概况；viewer 不能标记处理。

## 2. 已迁移接口

| 接口 | 权限 |
| --- | --- |
| `POST /api/human-review-tasks/{task_id}/outbox-drafts` | `outbox.draft.manage` |
| `GET /api/tenants/{tenant_id}/outbox-drafts` | `outbox.draft.read` |
| `POST /api/outbox-drafts/{draft_id}/confirmation` | `outbox.draft.manage` |
| `POST /api/outbox-drafts/{draft_id}/cancellation` | `outbox.draft.manage` |
| `GET /api/outbox-drafts/{draft_id}/send-attempts` | `outbox.send_attempt.read` |
| `POST /api/outbox-drafts/{draft_id}/send-attempts` | `outbox.send_attempt.manage` |
| `POST /api/tenants/{tenant_id}/outbox-worker-runs` | `outbox.send_attempt.manage` |
| `GET /api/tenants/{tenant_id}/outbox-delivery-jobs` | `outbox.delivery_job.read` |
| `POST /api/outbox-drafts/{draft_id}/delivery-jobs` | `outbox.delivery_job.manage` |
| `POST /api/tenants/{tenant_id}/outbox-delivery-queue-runs` | `outbox.delivery_job.manage` |
| `GET /api/tenants/{tenant_id}/delivery-failure-reviews` | `outbox.failure_review.read` |
| `PATCH /api/delivery-failure-reviews/{review_id}` | `outbox.failure_review.manage` |

## 3. 前端同步

P3-06O 第一片曾临时把出站按钮集中挂到 `outbox.send_plan.manage`。P3-06P 已拆开：

- 批准入待发送：需要 `conversation.manage` 与 `outbox.draft.manage`。
- 确认待发送：需要 `outbox.draft.manage`。
- 模拟发送和发送检查：需要 `outbox.send_attempt.manage`。
- 生成渠道计划：需要 `outbox.send_plan.manage`。
- 加入发送队列和运行发送队列：需要 `outbox.delivery_job.manage`。
- 标记失败复盘已处理：需要 `outbox.failure_review.manage`。

这不是只改按钮。对应 handler 也会再次检查权限，真正安全边界仍以后端 `require_permission()` 为准。

## 4. 保留的服务层规则

本轮只迁移 API 入口权限，不改变业务状态机：

- 跨租户草稿、尝试、队列任务和失败复盘继续返回 404。
- outbox draft 仍必须来自已批准的人审任务。
- send attempt 仍只允许 `ready_to_send` 草稿。
- dry-run、connector no-op 和 delivery queue skeleton 仍不做真实外部发送。
- delivery queue 的 kill switch、租约、限流、死信和失败复盘逻辑保持不变。
- 官方平台 webhook 仍走连接器签名边界，不套坐席 bearer token。

## 5. 未完成边界

- 字段脱敏和字段 allowlist 仍未完成，尤其是回执、联系人、线索和审计字段。
- `human_review.read` / `human_review.manage` 仍未拆出。
- `outbox.delivery_job.manage` 当前是 owner/admin 粗粒度权限，后续如果要让坐席“只发送自己负责会话”，需要增加资源所有权检查。
- 真实外发 sender、生产 token、可信 IP 出站和平台白名单仍未接通。
- 高并发压测、独立 outbox worker service 和多容器部署压测仍未完成。

## 6. 验收结果

- 新增 `backend/tests/test_p3_06p_outbox_resource_rbac.py`，覆盖权限矩阵、viewer 禁止草稿/试发、agent 可草稿确认和 dry-run、agent 禁止运行发送队列、owner/admin 可管理发送队列、viewer 可读失败复盘但不可处理、agent 可处理失败复盘。
- 新增 `scripts/check_p3_06p_outbox_resource_rbac.py`，静态检查 RBAC、API、前端 guard、测试和文档一致。
- 相关回归覆盖 outbox、delivery queue、delivery failure review、channel connector 和前端构建。

## 7. 后续建议

1. 字段 allowlist：按 owner/admin/agent/viewer 收口联系人、线索、回执、连接器 config 和审计事件响应字段。
2. 资源级所有权：让 agent 只能处理自己团队或自己领取的会话草稿，而不是租户内所有草稿。
3. 独立 outbox worker service：把手动 queue run 迁到后台进程，前端只显示状态和重新入队动作。
4. 官方渠道 smoke：公网 HTTPS、Token、EncodingAESKey、可信 IP 和测试客服账号具备后，做企业微信入站回调和白名单出站前置验证。
5. 真实外发前安全门：真实 sender 必须另做生产开关、审批、白名单、审计、速率限制和回滚 SOP。
