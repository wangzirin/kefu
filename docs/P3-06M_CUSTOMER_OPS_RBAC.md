# P3-06M RBAC 第六片：工单、客户画像与线索权限

日期：2026-07-01  
范围：工单列表、工单创建/更新、联系人画像列表/详情、线索列表、线索创建/更新  
状态：第六片完成

## Engineering Control Card

- Stage: P3-06M RBAC 第六片
- 当前主线阶段: 后端资源级 RBAC 收口
- 上一阶段真正完成: P3-06L 已把知识库读写、发布、回滚、缺口、评测和索引迁到 `knowledge.read` / `knowledge.manage`
- 上一阶段明确没有完成: 工单、客户、线索、渠道配置权限迁移；前端按钮级权限；字段脱敏
- 本轮要交付的客户可见价值: 客服经营链路的核心数据不再只靠“登录即可进入”；坐席可处理自己的工单和线索，viewer 不能读取客户画像、工单和线索原文
- 本轮是否只是评测: 否
- 本轮不做什么: 不改数据库结构、不改前端页面、不改工单/SLA 业务规则、不迁移渠道配置/secret/webhook/send plan 权限、不打开真实外发
- 外部风险: 无真实外发；无模型调用；不读写第三方平台
- 需要用户授权的动作: 无
- 验证方式: P3-06M 后端测试、工单/客户/线索业务回归、前几片 RBAC 回归、静态 readiness 检查、后端全量测试、前端构建
- 写回文件: 产品化总控手册、Superpowers P3 计划、Workspace Project_012 记录
- 下一阶段: RBAC 第七片，优先迁移渠道配置、连接器、回执读取、发送计划和 secret 读取边界，或进入前端按钮级权限

## 1. 权限矩阵

| 权限 | owner | admin | agent | viewer |
| --- | --- | --- | --- | --- |
| `ticket.read` | 允许 | 允许 | 允许 | 禁止 |
| `ticket.manage` | 允许 | 允许 | 允许 | 禁止 |
| `customer.read` | 允许 | 允许 | 允许 | 禁止 |
| `lead.read` | 允许 | 允许 | 允许 | 禁止 |
| `lead.manage` | 允许 | 允许 | 允许 | 禁止 |

口径：

- `ticket.read` 控制工单列表和筛选。
- `ticket.manage` 控制由会话生成工单、更新工单状态、优先级、处理说明和分派字段。
- `customer.read` 控制联系人画像列表和联系人详情。
- `lead.read` 控制线索列表和筛选。
- `lead.manage` 控制由会话生成线索和推进线索阶段。
- viewer 暂不开放客户画像、工单或线索，因为客户资料、联系方式、对话摘要和经营状态仍属于敏感运营数据。

## 2. 已迁移接口

| 接口 | 权限 |
| --- | --- |
| `GET /api/tenants/{tenant_id}/support-tickets` | `ticket.read` |
| `POST /api/conversations/{conversation_id}/support-tickets` | `ticket.manage` |
| `PATCH /api/support-tickets/{ticket_id}` | `ticket.manage` |
| `GET /api/tenants/{tenant_id}/contact-profiles` | `customer.read` |
| `GET /api/contact-profiles/{contact_id}` | `customer.read` |
| `GET /api/tenants/{tenant_id}/leads` | `lead.read` |
| `POST /api/conversations/{conversation_id}/leads` | `lead.manage` |
| `PATCH /api/leads/{lead_id}` | `lead.manage` |

## 3. 保留的服务层规则

本轮只迁移 API 入口权限，不改变已有业务规则。

继续保留：

- 跨租户资源返回 404。
- 坐席可以处理工单和线索，但不能把自己的工单或线索随意分给别人。
- 工单仍保留 agent 自有分派限制、团队分派限制、完成态重开 409 和 SLA 计算。
- 联系人画像对坐席仍显示脱敏电话和微信号；owner/admin 可看完整字段。
- 线索仍保留 agent 只能认领或处理自己负责的线索。

## 4. 为什么渠道配置后置

渠道配置不是普通业务数据，里面包含官方连接器、回调、签名、secret 引用、发送计划和真实外发风险。

下一片应单独拆成：

1. `channel.read`：读取渠道状态和健康摘要。
2. `channel.manage`：修改渠道基础配置。
3. `channel.secret.manage`：绑定或轮换 secret 引用，不返回 secret 明文。
4. `channel.webhook.read`：读取 webhook 验证/回调状态。
5. `outbox.send_plan.manage`：创建或调整发送计划，但仍受外发开关和人工审核限制。

这样可以避免把密钥和真实平台动作混在工单/客户/线索这类经营数据权限里。

## 5. 验收结果

- `backend/tests/test_p3_06m_customer_ops_rbac.py` 覆盖权限矩阵、viewer 403、agent 自有工单/线索处理、客户画像脱敏和跨租户 404。
- 工单、联系人画像、线索原有业务回归通过。
- P3-06H 到 P3-06L 的 RBAC 回归通过。
- `scripts/check_p3_06m_customer_ops_rbac.py` 用于静态检查 RBAC、API、测试和文档是否保持一致。

## 6. 后续建议

1. RBAC 第七片：迁移渠道配置、连接器配置、secret 引用、回执读取和发送计划权限。
2. 前端按钮级权限：用 `user.permissions` 控制生成工单、更新工单、生成线索、推进线索、知识发布、回滚、评测运行等按钮。
3. 字段脱敏片：按 owner/admin/agent/viewer 分层处理电话、微信号、对话摘要、预算、线索备注、工单描述和导出字段。
4. 工单增强片：补工单评论、附件、重开流程、SLA 升级和主管视图。
