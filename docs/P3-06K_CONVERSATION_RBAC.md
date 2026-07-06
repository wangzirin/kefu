# P3-06K RBAC 第四片：会话业务动作权限

日期：2026-07-01  
范围：标准运营版客服中台会话列表、会话详情、会话创建、消息写入、分配和坐席工作流  
状态：第四片完成

## Engineering Control Card

- Stage: P3-06K RBAC 第四片
- 当前主线阶段: 后端资源级 RBAC 收口
- 上一阶段真正完成: P3-06J 已把账号、角色、团队接口迁到 `accounts.manage`，并保留首角色、首用户、首次角色分配 bootstrap
- 上一阶段明确没有完成: 会话、知识、渠道、工单、客户、线索等业务动作权限迁移；前端按钮级权限；字段脱敏
- 本轮要交付的客户可见价值: 坐席会话台的核心读写动作进入命名权限控制，普通 viewer 不能查看或操作真实会话内容
- 本轮是否只是评测: 否
- 本轮不做什么: 不改数据库结构、不改前端页面、不迁移知识/工单/客户/线索权限、不打开真实外发、不改变官方 webhook 验签入口
- 外部风险: 无真实平台写入；官方 webhook 继续走 provider connector、签名验签、幂等和可信入站边界，不使用坐席 bearer token
- 需要用户授权的动作: 无
- 验证方式: 会话 RBAC 后端测试、受影响业务回归、静态 readiness 检查、后端全量测试、前端构建
- 写回文件: 产品化总控手册、Superpowers P3 计划、Workspace Project_012 记录
- 下一阶段: RBAC 第五片，优先迁移知识发布/工单/客户/线索权限，或先做前端按钮级权限

## 1. 本轮目标

会话是客服中台的主工作面。P3-06K 把会话相关 API 从“只要登录或甚至无登录即可访问”的旧试点状态，迁到命名权限：

- `conversation.read`
- `conversation.manage`

当前权限矩阵：

| 权限 | owner | admin | agent | viewer |
| --- | --- | --- | --- | --- |
| `conversation.read` | 允许 | 允许 | 允许 | 禁止 |
| `conversation.manage` | 允许 | 允许 | 允许 | 禁止 |

保守原因：

- 坐席、管理员、负责人都需要处理会话和坐席动作。
- viewer 暂时不能读取会话详情，因为当前还没有字段级脱敏、只读响应 allowlist 和敏感内容遮罩。
- 后续如果要给 viewer 看报表，应使用 `dashboard.read`、`quality.read` 等低敏权限，而不是直接开放会话原文。

## 2. 已迁移接口

| 接口 | 权限 | 说明 |
| --- | --- | --- |
| `GET /api/tenants/{tenant_id}/conversations` | `conversation.read` | 会话列表读取 |
| `GET /api/tenants/{tenant_id}/conversation-inbox` | `conversation.read` | 坐席会话收件箱 |
| `GET /api/conversations/{conversation_id}` | `conversation.read` | 会话详情和消息流 |
| `POST /api/tenants/{tenant_id}/conversations` | `conversation.manage` | 创建内部会话 |
| `POST /api/conversations/{conversation_id}/messages` | `conversation.manage` | 写入会话消息 |
| `PATCH /api/conversations/{conversation_id}/assignment` | `conversation.manage` | 分配坐席或团队 |
| `POST /api/conversations/{conversation_id}/workflow-actions` | `conversation.manage` | claim、transfer、resolve、reopen、note 等坐席动作 |

所有带租户路径的接口继续保留同租户校验。跨租户资源返回 404，避免暴露资源是否存在。

## 3. 不改变的边界

官方平台 webhook 入口不套坐席 bearer token。原因是企业微信、公众号、官网组件这类外部平台回调通常无法携带我方坐席登录 token。

这类入口继续走独立边界：

- provider/channel connector 匹配。
- Token、签名、AES 解密或 HMAC 验签。
- 幂等键和重复回调处理。
- 可信入站消息创建门禁。
- 后续 worker 编排和人工审核。

也就是说，本轮收紧的是“内部会话 API / 坐席操作 API”，不是让官方 webhook 改成内部登录态。

## 4. 测试夹具同步修正

早期测试里存在无 token 创建会话和消息的便利夹具。P3-06K 已把这些测试夹具改为：

1. 创建租户。
2. 初始化 owner 角色和 owner 用户。
3. 绑定角色并登录。
4. 用 bearer token 创建会话和消息。

这能避免测试继续依赖过宽的试点权限。

## 5. 当前边界

| 未完成项 | 后续方向 |
| --- | --- |
| 知识发布权限 | 建议拆 `knowledge.read`、`knowledge.manage`、`knowledge.publish`、`knowledge.rollback` |
| 工单权限 | 建议拆 `ticket.read`、`ticket.manage`、`ticket.assign` |
| 客户和线索权限 | 建议拆 `customer.read`、`lead.read`、`lead.manage`，并补字段脱敏 |
| 渠道配置权限 | 建议拆 `channel.read`、`channel.manage`、`channel.secret.manage` |
| 前端按钮级权限 | 统一读取 `user.permissions`，隐藏或禁用无权限动作 |
| viewer 只读策略 | 当前 viewer 仍不能看会话原文；后续需要脱敏视图再开放 |

## 6. 验收结果

- `backend/tests/test_p3_06k_conversation_rbac.py` 覆盖权限矩阵、无 token、viewer 禁止、agent 可处理、跨租户隐藏。
- `backend/tests/test_conversation_inbox_api.py` 覆盖收件箱、分配、坐席工作流。
- 受影响的 foundation、channel connector、webhook、workflow、outbox、reply orchestrator 和 P3-04/P3-05E 回归测试已同步改为正式 token 夹具。
- `scripts/check_p3_06k_conversation_rbac.py` 用于静态检查权限、API、测试和文档是否保持一致。

## 7. 后续建议

1. RBAC 第五片：知识发布、回滚、缺口草稿、回归题库动作迁到命名权限。
2. RBAC 第六片：工单、联系人、线索迁到命名权限，并补 agent 自有资源边界。
3. 前端权限片：根据 `user.permissions` 控制会话、知识、工单、账号团队按钮。
4. 字段脱敏片：viewer、agent、admin 分层控制联系人手机号、微信号、线索预算、客户原文导出。
