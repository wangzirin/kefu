# P3-05M 工单与 SLA 第一片

## Engineering Control Card

| 项目 | 内容 |
| --- | --- |
| 阶段 | P3-05M 工单与 SLA 第一片 |
| 目标 | 在会话收件箱、坐席动作流和知识缺口闭环之后，新增独立工单资源，让商户能把需要跟进、升级、售后或长期处理的问题从会话中沉淀出来 |
| 产品边界 | 本阶段是标准运营版客服中台的工单骨架，不是完整 CRM、完整 ITSM、完整客户成功系统，也不是全渠道真实自动回复上线 |
| 安全边界 | 不打开真实外发；不写入真实平台密钥；演示模式下工单操作禁用；正式操作必须登录并通过租户和角色校验 |
| 当前状态 | 后端工单模型、迁移、API、权限、审计、轻量 SLA、前端工单工作区、测试和浏览器预览已完成；高级 SLA 策略、工单评论、附件、重开流程和主管质检仍未完成 |

## 为什么要做这一片

会话收件箱解决的是“消息来了谁处理”。工单解决的是“这件事要不要持续跟进、谁负责、多久内处理完、处理结果能不能追溯”。

没有工单时，客服系统容易变成一张消息列表：

- 客户售后问题处理到一半，换班后责任不清。
- 高优先级问题没有截止时间。
- 已解决、等客户、已关闭、已取消这些状态无法和会话状态区分。
- 客户投诉或复杂售后没有单独编号、责任人和处理说明。
- 管理员很难复盘为什么某个问题超时、谁处理过、最后怎么关闭。

P3-05M 的目的不是把所有工单能力一次做满，而是先把商用中台最小可信骨架搭起来。

## 本阶段完成内容

### 后端工单资源

新增 `SupportTicket` 模型和 `support_tickets` 表。

核心字段：

| 类别 | 字段 |
| --- | --- |
| 归属 | `tenant_id`、`conversation_id`、`channel_id`、`contact_id` |
| 内容 | `subject`、`description`、`source_type`、`source_ref` |
| 状态 | `status`、`priority` |
| 分派 | `assigned_user_id`、`assigned_team_id` |
| SLA | `sla_target_minutes`、`sla_due_at`、`sla_status` |
| 关闭 | `resolution_note`、`resolved_by_id`、`resolved_at` |
| 审计 | `created_by_id`、`updated_by_id`、`created_at`、`updated_at` |

幂等约束：

```text
tenant_id + source_type + source_ref
```

同一条会话重复生成工单，不会产生重复工单。接口会返回已有工单。

### API

新增接口：

```text
GET /api/tenants/{tenant_id}/support-tickets
POST /api/conversations/{conversation_id}/support-tickets
PATCH /api/support-tickets/{ticket_id}
```

列表支持：

- 状态筛选。
- 优先级筛选。
- 分派筛选：全部、我的、已分派、未分派。
- SLA 筛选：正常、临近、已超时、暂停、已完成。
- 关键词搜索。
- 服务端分页。

创建支持：

- 从会话生成工单。
- 自动带入会话所属渠道和联系人。
- 管理员可指定负责人或团队。
- 坐席创建时默认归属自己，不能替别人或团队分派。

更新支持：

- 修改主题、描述、状态、优先级、负责人、团队、SLA 目标、处理说明。
- 工单解决、关闭或取消时记录解决人和解决时间。
- 已完成工单不能通过普通更新直接重开；后续需要单独重开动作，避免关闭记录被随意改写。

### 权限边界

当前角色规则：

| 角色 | 能力 |
| --- | --- |
| owner/admin | 可查看、创建、分派、改派、更新租户内工单 |
| agent | 可查看租户内工单；可创建工单；可领取自己或未分派工单；不能分派给他人或团队 |
| 其他角色/未登录 | 无工单访问权 |

跨租户访问返回 404，不暴露其他租户资源存在性。

### 轻量 SLA

当前 SLA 是客服运营提示，不是完整合同级 SLA。

默认时限：

| 优先级 | 默认处理目标 |
| --- | --- |
| urgent | 30 分钟 |
| high | 60 分钟 |
| normal | 240 分钟 |
| low | 1440 分钟 |

SLA 状态：

| 状态 | 含义 |
| --- | --- |
| ok | 未临近截止 |
| warning | 15 分钟内将到期 |
| breached | 已超过截止时间 |
| paused | 等客户状态，暂时暂停运营提示 |
| completed | 已解决、已关闭或已取消 |

当前不包含：

- 工作日/节假日日历。
- 班次时间。
- 客户等级差异化 SLA。
- 多级升级通知。
- 赔付或合同承诺。
- 工单重开后重新计时。

这些进入后续高级 SLA 策略。

### 审计与事件

创建和更新工单时会双写：

- `ConversationEvent`：挂在原会话下，方便从会话追溯工单动作。
- `AuditEvent`：挂在租户审计流下，方便做合规、复盘和管理端查询。

事件 payload 记录：

- 动作名。
- 工单 ID。
- 动作前状态。
- 动作后状态。
- 本次修改字段。
- 操作人。

### 前端工单工作区

新增左侧导航：

```text
工单 -> #tickets
```

页面结构：

- 顶部 4 个工单指标。
- 状态、优先级、分派、SLA、搜索筛选。
- 工单列表，支持分页。
- 工单详情侧栏。
- 处理动作：开始处理、等客户、解决、关闭、取消。
- 可从候选会话生成工单。

演示模式下：

- 展示同形样例数据，便于客户理解产品形态。
- 所有真实写入动作禁用，避免误导为已连接真实业务。

正式登录后：

- 工单列表走后端分页接口。
- 创建和更新工单走正式 API。
- 操作完成后刷新当前页。

## 本轮文件改动

- `backend/app/models/foundation.py`
  - 新增 `SupportTicket`。
- `backend/app/models/__init__.py`
  - 导出 `SupportTicket`。
- `backend/app/migrations/versions/0018_support_tickets.py`
  - 新增 `support_tickets` 表迁移。
- `backend/app/schemas/support_tickets.py`
  - 新增工单创建、更新、读取和列表 schema。
- `backend/app/services/support_tickets.py`
  - 新增工单创建、列表、更新、权限校验、SLA 计算、事件和审计逻辑。
- `backend/app/api/support_tickets.py`
  - 新增工单 API 路由。
- `backend/app/main.py`
  - 注册工单 API。
- `backend/tests/test_support_tickets_api.py`
  - 新增工单 API 测试。
- `frontend/src/api/client.ts`
  - 新增工单类型和 API 客户端。
- `frontend/src/data/navigation.ts`
  - 新增 `工单` 工作区，阶段标识更新为 `P3-05M`。
- `frontend/src/App.tsx`
  - 新增工单状态、刷新、筛选、分页、创建、更新动作和 `SupportTicketPanel`。
- `frontend/src/styles.css`
  - 新增工单指标、列表、筛选、详情、候选会话和响应式样式。

## 已验证内容

### 后端新增测试

```bash
backend/.venv/bin/python -m pytest backend/tests/test_support_tickets_api.py -q
```

结果：

```text
2 passed
```

覆盖：

- 未登录访问返回 401。
- 从会话生成工单。
- 重复生成工单幂等返回已有工单。
- 工单列表分页和筛选。
- SLA 已超时筛选。
- 工单解决。
- 已完成工单普通重开返回 409。
- 坐席只能领取自己工单，不能替他人分派。
- 跨租户列表和更新返回 404。
- `ConversationEvent` 和 `AuditEvent` 均写入。

### 后端相关回归

```bash
backend/.venv/bin/python -m pytest backend/tests/test_support_tickets_api.py backend/tests/test_conversation_inbox_api.py -q
```

结果：

```text
5 passed
```

```bash
backend/.venv/bin/python -m pytest backend/tests/test_support_tickets_api.py backend/tests/test_conversation_inbox_api.py backend/tests/test_auth_rbac_audit.py -q
```

结果：

```text
8 passed
```

### 数据库迁移检查

```bash
cd backend
.venv/bin/alembic heads
```

结果：

```text
0018_support_tickets (head)
```

### 前端构建

```bash
cd frontend
npm run build
```

结果：

```text
tsc && vite build
build succeeded
```

### 浏览器验证

本地预览地址：

```text
http://127.0.0.1:5175/#tickets
```

已验证：

- 可进入登录页。
- 点击“开发演示进入”后可进入工单工作区。
- 左侧导航包含 `工单`。
- 工单页包含指标、筛选、分页列表、详情侧栏和候选会话。
- 分页可切换到第 2 页。
- 修复后第 2 页的 `SLA` 徽标没有左侧裁切。

浏览器限制：

- 本轮本地环境没有可用的前端 Playwright 依赖。
- Chrome 窗口自动缩放脚本未成功执行，因此移动端只做 CSS 响应式约束和构建校验，没有完成真实移动截图复核。

## 当前仍然不能承诺

- 不能承诺完整 CRM 已完成。
- 不能承诺完整工单平台已完成。
- 不能承诺合同级 SLA 已完成。
- 不能承诺工单评论、附件、内部协作、主管质检、服务升级通知已完成。
- 不能承诺普通坐席的全部细粒度权限矩阵已完成。
- 不能承诺企业微信、公众号、抖音、小红书、淘宝、京东或拼多多已经真实自动回复。
- 不能承诺真实外发已经打开。

## 对产品成熟度的真实评价

P3-05M 完成后，标准运营版中台从“会话处理系统”进一步推进为“会话 + 工单”的客服运营骨架。

现在已经能覆盖：

```text
客户消息进入会话池
-> 坐席领取/处理会话
-> 复杂问题生成工单
-> 工单分派负责人
-> 按优先级给出处理时限
-> 处理状态和结果留痕
-> 管理员通过列表筛选超时和待处理事项
```

这已经比纯 FAQ、纯聊天窗口或纯前端演示更接近可商用客服中台。但它仍是第一片工单能力，不能替代成熟工单系统、客户成功系统或售后工单平台。

## 下一步建议

优先继续三条线：

1. P3-05N：联系人画像与线索跟进，把客户身份、历史会话、标签、意向和跟进状态连起来。
2. P3-05O：知识缺口到知识文档和题库回归建议流，把缺口闭环真正接回知识库更新。
3. 企业微信公网 smoke：若公网 HTTPS、可信 IP、企微后台权限、Token 和 EncodingAESKey 都具备，继续真实回调验证。

本轮结论：工单与 SLA 第一片已经完成，可以作为标准运营版中台的商用骨架继续扩展；但对客户只能表述为“工单和 SLA 运营提示已具备第一版”，不能表述为“完整工单系统/合同 SLA 已完成”。
