# P3-06I RBAC 第二片：权限快照与审计权限迁移

日期：2026-07-01  
范围：标准运营版客服中台认证响应、审计查询权限边界  
状态：第二片完成

## Engineering Control Card

- Stage: P3-06I RBAC 第二片
- 当前主线阶段: 后端资源级 RBAC 收口
- 上一阶段真正完成: P3-06H 已新增中心化命名权限，并把运维三条接口迁到 `ops.*.read`
- 上一阶段明确没有完成: `/api/auth/me` 权限快照、审计权限迁移、账号/团队初始化门禁、按钮级权限和字段脱敏
- 本轮要交付的客户可见价值: 管理员和前端可以从登录态直接知道当前账号具备哪些权限；审计查询不再依赖散落角色判断
- 本轮是否只是评测: 否
- 本轮不做什么: 不改账号初始化流程、不迁移所有账号/团队接口、不改数据库结构、不改变前端菜单
- 外部风险: 无外部平台动作，无真实外发
- 需要用户授权的动作: 无
- 验证方式: 后端权限测试、认证/审计回归、静态 readiness 检查、前端构建
- 下一阶段: RBAC 第三片，优先处理账号/团队正式管理权限与 bootstrap 边界，或进入会话/知识/工单动作权限迁移

## 1. 本轮目标

P3-06H 只有权限矩阵和运维接口样板，但前端和后续接口还不知道“当前用户实际有什么权限”。本轮先补最基础的权限快照：

- 登录响应 `LoginResponse.user.permissions` 返回当前账号权限集合。
- `GET /api/auth/me` 返回同一份权限集合。
- bootstrap 演示身份返回 owner 对应的权限集合，继续保持演示路径可用。
- 审计查询 `GET /api/tenants/{tenant_id}/audit-events` 改用 `require_permission("audit.events.read")`。

## 2. 当前新增权限快照

| 角色 | 当前返回的重点权限 |
| --- | --- |
| owner | `accounts.manage`、`audit.events.read`、`ops.metrics.read`、`knowledge.manage`、`conversation.manage` |
| admin | `audit.events.read`、`ops.metrics.read`、`knowledge.manage`、`conversation.manage` |
| agent | `conversation.manage`、`knowledge.read`、`customer.read` |
| viewer | `dashboard.read`、`quality.read`、`channel.read` |

这份快照不是最终按钮级权限系统，但它是后续前端把 `owner/admin` 硬判断替换成 `permissions.includes(...)` 的基础。

## 3. 已完成改动

- `CurrentUser` schema 新增 `permissions` 字段。
- 登录响应通过 `permissions_for_roles(principal.roles)` 计算权限集合。
- `/api/auth/me` 使用相同计算方式，避免登录响应和当前用户接口不一致。
- bootstrap 演示用户返回 owner 权限快照。
- 审计查询接口从 `require_any_role("owner", "admin")` 迁到 `require_permission("audit.events.read")`。
- 前端 `CurrentUser` 类型新增 `permissions` 字段，为后续按钮级权限做准备。

## 4. 为什么本轮不迁账号/团队接口

账号和团队接口当前包含启动期特殊逻辑：

| 接口域 | 当前特殊逻辑 | 本轮处理 |
| --- | --- | --- |
| 创建第一个角色 | 租户还没有角色时允许 bootstrap 创建 | 暂不修改 |
| 创建第一个用户 | 租户还没有用户时允许 bootstrap 创建 | 暂不修改 |
| 首次分配角色 | 租户还没有用户角色时允许 bootstrap 分配 | 暂不修改 |
| 后续账号/团队管理 | 已有 owner/admin 角色判断 | 下一片迁到 `accounts.manage` |

如果本轮直接把这些接口全部改成 `accounts.manage`，新租户初始化可能被锁死。下一片需要单独设计：

- 生产模式是否允许无 token bootstrap。
- bootstrap 是否必须通过一次性安装 token。
- 初始化完成后如何永久关闭 bootstrap。
- owner 是否独占 `accounts.manage`，admin 是否只读或可管理团队。

## 5. 当前边界

| 未完成项 | 后续方向 |
| --- | --- |
| 账号/团队正式管理权限 | 设计 `accounts.manage`、`accounts.read`、`teams.manage` 并保留安全初始化门禁 |
| 前端按钮级权限 | 用 `user.permissions` 替代散落的 `roles.includes(...)` |
| 会话/知识/工单/客户/线索权限 | 按资源域逐片迁移到命名权限 |
| viewer/agent 字段脱敏 | 服务端 response allowlist，不只靠前端隐藏 |
| 生产账号安全策略 | 密码策略、撤销、锁定、初始化令牌、审计 UI |

## 6. 验收结果

- `tests/test_p3_06i_rbac_permission_snapshot.py` 覆盖 owner 登录权限快照、`/auth/me` 权限快照、admin 审计可读、agent 审计 403。
- `tests/test_auth_rbac_audit.py` 继续覆盖登录、token hash、错误密码、无 token 401 和审计读取。
- `tests/test_p3_06h_rbac_permission_matrix.py` 继续覆盖 P3-06H 运维命名权限。
- `scripts/check_p3_06i_rbac_permission_snapshot.py` 用于静态确认权限快照、审计迁移、文档和测试存在。

## 7. 后续建议

1. RBAC 第三片：账号/团队权限迁移，但先补 bootstrap 一次性初始化策略，避免新客户空间无法创建首个管理员。
2. RBAC 第四片：会话动作、人工审核、outbox、工单、客户画像、线索动作迁到命名权限。
3. RBAC 第五片：前端按钮级权限统一读取 `user.permissions`。
4. RBAC 第六片：viewer/agent 字段脱敏和只读响应 allowlist。
