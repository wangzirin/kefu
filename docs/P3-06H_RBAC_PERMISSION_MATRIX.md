# P3-06H RBAC 权限矩阵第一片

日期：2026-07-01  
范围：标准运营版客服中台后端权限边界  
状态：第一片完成

## Engineering Control Card

- Stage: P3-06H 第一片
- 当前主线阶段: 后端资源级 RBAC 收口
- 上一阶段真正完成: P3-06G 指标出口第一片，已新增只读 `/ops/metrics` 和前端指标出口面板
- 上一阶段明确没有完成: 全量 API 权限矩阵、按钮级权限、字段脱敏、viewer 后端只读策略
- 本轮要交付的客户可见价值: 管理运维类接口不再只靠散落角色判断，开始收口到命名权限
- 本轮是否只是评测: 否
- 本轮不做什么: 不一次性重写所有接口、不改变坐席工作台主链路、不新增数据库迁移、不改前端菜单
- 外部风险: 无外部动作
- 需要用户授权的动作: 无
- 验证方式: 后端 RBAC 测试、P3-06E/F/G 回归、静态 readiness 检查
- 下一阶段: RBAC 第二片，继续把会话、知识、渠道、工单、客户、账号等资源逐步迁到命名权限

## 1. 本轮目标

RBAC 第一片先建立后端命名权限底座，而不是继续把权限散落成 `require_any_role("owner", "admin")`。本轮只迁移管理运维三条接口，作为低风险样板：

- `ops.worker_health.read`
- `ops.alert_rules.read`
- `ops.metrics.read`

## 2. 新增后端权限模块

新增 `backend/app/core/rbac.py`：

| 函数 | 作用 |
| --- | --- |
| `ROLE_PERMISSIONS` | 定义 owner、admin、agent、viewer 的第一批权限集合 |
| `permissions_for_roles()` | 把一个用户的多个角色合并成权限集合 |
| `principal_has_permission()` | 判断当前 principal 是否具备某个权限 |
| `allowed_roles_for_permission()` | 反查某个权限当前由哪些角色持有 |
| `require_permission()` | FastAPI dependency，缺权限返回 403 |

## 3. 当前权限矩阵第一片

| 权限 | owner | admin | agent | viewer | 当前接入接口 |
| --- | --- | --- | --- | --- | --- |
| `ops.worker_health.read` | 允许 | 允许 | 禁止 | 禁止 | `GET /api/tenants/{tenant_id}/ops/worker-health` |
| `ops.alert_rules.read` | 允许 | 允许 | 禁止 | 禁止 | `GET /api/tenants/{tenant_id}/ops/alert-rules` |
| `ops.metrics.read` | 允许 | 允许 | 禁止 | 禁止 | `GET /api/tenants/{tenant_id}/ops/metrics` |

## 4. 已完成改动

- 新增中心化 RBAC 模块。
- 运维健康、告警规则、指标出口三条接口改用 `require_permission()`。
- 新增测试确认 owner/admin 拥有运维读权限，agent/viewer 不拥有。
- 新增接口测试确认 admin 可读 `ops/metrics`，agent 被 403 拦截，无 token 被 401 拦截。
- 保留同租户校验，跨租户仍返回 404。

## 5. 当前边界

| 未完成项 | 后续方向 |
| --- | --- |
| 全量 API 权限矩阵 | 第二片开始按资源迁移会话、知识、渠道、工单、客户、账号 |
| 按钮级权限 | 前端应从后端权限或 `/me` 权限快照决定动作可见性 |
| 字段脱敏 | viewer/agent 的敏感字段需要服务端 response allowlist |
| 审计权限 | 后续可把 `audit.events.read` 迁到 `require_permission()` |
| 初始化与账号管理 | 需要区分 bootstrap 阶段和正式生产账号管理阶段 |

## 6. 验收标准

- `app/core/rbac.py` 存在命名权限。
- 运维三条接口使用 `require_permission()`。
- agent 访问 `ops/metrics` 返回 403。
- 无 token 访问 `ops/metrics` 返回 401。
- P3-06E/F/G 相关测试仍通过。
- readiness 脚本通过。

## 7. 后续建议

1. RBAC 第二片：把 `audit.events.read`、账号管理、团队管理迁到命名权限。
2. RBAC 第三片：把会话动作、人工审核、outbox、工单、客户画像、线索动作迁到命名权限。
3. RBAC 第四片：补前端按钮级权限和 `/api/auth/me` 权限快照。
4. RBAC 第五片：补 viewer/agent 字段脱敏和只读响应 allowlist。
