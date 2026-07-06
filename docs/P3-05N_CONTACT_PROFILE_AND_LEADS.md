# P3-05N 联系人画像与线索跟进第一片

## Engineering Control Card

| 项目 | 内容 |
| --- | --- |
| 阶段 | P3-05N 联系人画像与线索跟进第一片 |
| 目标 | 在会话、工单和知识缺口之后，把客户关系从“单条会话”提升到“联系人画像 + 线索跟进”的最小运营闭环 |
| 产品边界 | 本阶段是客服中台的客户画像和销售线索骨架，不是完整 CRM，不替代客户已有销售系统，也不代表全渠道真实自动回复已上线 |
| 安全边界 | 不打开真实外发；演示模式禁用写入动作；正式操作必须登录并通过租户、角色、脱敏和审计校验 |
| 当前状态 | 后端联系人画像聚合、线索模型、迁移、API、权限、审计、前端联系人/线索工作区、分页筛选和浏览器预览已完成；标签体系、跨渠道身份合并、CRM 对接和完整销售漏斗仍未完成 |

## 为什么要做这一片

客服中台不能只看“消息列表”。一个客户可能先在官网问价格，又在企业微信问部署，再在电商平台问售后。坐席接待时需要知道这个人之前问过什么、是否有未处理工单、是否已经形成商机，以及下一步应该做什么。

P3-05N 先解决四个问题：

- 坐席打开联系人时能看到最近会话、开放工单和开放线索。
- 高意向咨询可以从会话沉淀成线索，而不是散落在聊天记录里。
- 管理员和坐席看到的敏感联系方式不同，避免过度暴露手机号和微信号。
- 线索推进必须有阶段、负责人、下一步动作和审计，不只是前端标签。

## 本阶段完成内容

### 后端联系人画像

新增联系人画像聚合接口，不新增重复联系人表，而是基于已有 `contacts`、`conversations`、`support_tickets` 和 `sales_leads` 聚合。

接口：

```text
GET /api/tenants/{tenant_id}/contact-profiles
GET /api/contact-profiles/{contact_id}
```

列表返回：

- 联系人基础信息。
- 手机号、微信号按角色脱敏。
- 最近渠道、最近消息和最近会话时间。
- 会话总数、开放会话数。
- 工单总数、开放工单数。
- 线索总数、活跃线索数。
- 最高意向等级。
- 系统建议下一步动作。

详情返回：

- 最近会话摘要。
- 开放线索。
- 开放工单。

### 后端线索资源

新增 `SalesLead` 模型和 `sales_leads` 表。

核心字段：

| 类别 | 字段 |
| --- | --- |
| 归属 | `tenant_id`、`contact_id`、`channel_id`、`conversation_id` |
| 内容 | `title`、`summary`、`expected_budget`、`next_step` |
| 阶段 | `stage`：new、contacted、proposal、won、invalid、lost |
| 意向 | `intent_level`：cold、warm、hot |
| 负责人 | `owner_user_id` |
| 来源 | `source_type`、`source_ref` |
| 关闭 | `closed_at` |
| 审计 | `created_by_id`、`updated_by_id`、`created_at`、`updated_at` |

幂等约束：

```text
tenant_id + source_type + source_ref
```

同一条会话重复生成线索，不会产生重复线索。

接口：

```text
GET /api/tenants/{tenant_id}/leads
POST /api/conversations/{conversation_id}/leads
PATCH /api/leads/{lead_id}
```

列表支持：

- 阶段筛选。
- 意向筛选。
- 负责人筛选：全部、我的、已分配、未分配。
- 关键词搜索。
- 服务端分页。

### 权限与脱敏

当前角色规则：

| 角色 | 联系人画像 | 联系方式 | 线索 |
| --- | --- | --- | --- |
| owner/admin | 可查看租户内画像和详情 | 原文显示 | 可创建、分配、更新 |
| agent | 可查看租户内画像和详情 | 手机号/微信脱敏 | 可创建；只能把线索归给自己或保持未分配 |
| 其他角色/未登录 | 无访问权 | 无 | 无 |

跨租户访问返回 404，不暴露资源存在性。

### 审计与事件

线索创建和更新会写入：

- `ConversationEvent`：挂在原会话下，便于从会话追溯线索动作。
- `AuditEvent`：挂在租户审计流下，便于管理端复盘。

记录内容包含：

- 线索 ID。
- 来源会话 ID。
- 联系人 ID。
- 修改前状态。
- 修改后状态。
- 本次修改字段。
- 操作人。

### 前端联系人中心

新增导航：

```text
联系人 -> #contacts
```

页面结构：

- 顶部联系人指标。
- 搜索和分页。
- 左侧联系人列表。
- 右侧联系人画像。
- 最近会话。
- 开放线索。
- 开放工单。

演示模式下展示同形样例数据，动作禁用，不读取真实客户消息。

正式登录后：

- 列表和详情走后端接口。
- 管理员看原始联系方式。
- 坐席看脱敏联系方式。

### 前端线索跟进

新增导航：

```text
线索 -> #leads
```

页面结构：

- 顶部线索指标。
- 阶段、意向、负责人、关键词筛选。
- 线索分页列表。
- 线索阶段推进动作。
- 右侧可转线索的会话候选。

正式登录后：

- 可从会话生成线索。
- 可推进为已联系、待报价、已成交、无效。
- 更新后刷新线索池、联系人画像和会话收件箱。

## 本轮文件改动

- `backend/app/models/foundation.py`
  - 新增 `SalesLead`。
- `backend/app/models/__init__.py`
  - 导出 `SalesLead`。
- `backend/app/migrations/versions/0019_sales_leads.py`
  - 新增 `sales_leads` 表迁移。
- `backend/app/schemas/customer_profiles.py`
  - 新增联系人画像、联系人详情、线索创建、线索更新和线索列表 schema。
- `backend/app/services/customer_profiles.py`
  - 新增联系人画像聚合、联系方式脱敏、线索创建、线索列表、线索更新、角色校验、幂等去重和审计逻辑。
- `backend/app/api/customer_profiles.py`
  - 新增联系人画像和线索 API。
- `backend/app/main.py`
  - 注册联系人画像和线索 API。
- `backend/tests/test_customer_profiles_api.py`
  - 新增联系人画像和线索 API 测试。
- `frontend/src/api/client.ts`
  - 新增联系人画像、联系人详情、线索类型和 API 客户端。
- `frontend/src/data/navigation.ts`
  - 阶段标识更新为 `P3-05N`，联系人从规划变为画像，线索从规划变为跟进。
- `frontend/src/App.tsx`
  - 新增联系人画像状态、线索状态、刷新、筛选、选择、生成线索、推进线索和演示数据。
- `frontend/src/styles.css`
  - 新增联系人画像、线索池、意向标签、阶段标签、分页列表和响应式样式。

## 已验证内容

后端新增与相关回归：

```bash
backend/.venv/bin/python -m pytest \
  backend/tests/test_customer_profiles_api.py \
  backend/tests/test_support_tickets_api.py \
  backend/tests/test_conversation_inbox_api.py \
  backend/tests/test_auth_rbac_audit.py -q
```

结果：

```text
10 passed
```

迁移头：

```bash
cd backend && .venv/bin/alembic heads
```

结果：

```text
0019_sales_leads (head)
```

前端构建：

```bash
cd frontend && npm run build
```

结果：

```text
tsc && vite build 成功
```

浏览器预览：

- `http://127.0.0.1:5175/#contacts`
  - 开发演示进入后可见联系人指标、分页列表、画像详情、最近会话、开放线索和开放工单。
- `http://127.0.0.1:5175/#leads`
  - 开发演示进入后可见线索指标、阶段筛选、意向筛选、负责人筛选、分页列表和可转线索会话。

## 尚未完成

- 跨渠道身份合并规则：同一客户在企业微信、公众号、电商、官网等渠道的身份归并。
- 标签体系：客户标签、线索标签、风险标签、来源标签。
- 联系人合并与拆分。
- 线索评论、跟进记录、提醒和附件。
- CRM、企微客户联系、订单系统或电商订单的官方 API 对接。
- 线索漏斗看板、成交金额统计和销售绩效报表。
- 客户个人信息的细粒度字段权限、导出审批和数据保留策略。
- 真实官方渠道 smoke 和真实外发。

## 下一步

优先顺序：

1. P3-05O：把知识缺口推进到知识文档补充和题库回归建议，避免缺口只停留在列表状态。
2. P3-05P：工单评论、附件、重开流程和高级 SLA 第一片。
3. P3-06：标准运营版产品化 v1，把账号权限、部署、运维、质量报告和客户试点流程继续收敛。
4. 公网和企业微信条件具备时，并行做官方 HTTPS 回调 smoke。
