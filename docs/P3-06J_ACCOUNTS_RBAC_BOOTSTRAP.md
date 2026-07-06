# P3-06J RBAC 第三片：账号团队权限与 Bootstrap 保护

日期：2026-07-01  
范围：标准运营版客服中台账号、角色、团队接口权限边界  
状态：第三片完成

## Engineering Control Card

- Stage: P3-06J RBAC 第三片
- 当前主线阶段: 后端资源级 RBAC 收口
- 上一阶段真正完成: P3-06I 已让登录和 `/api/auth/me` 返回权限快照，并把审计查询迁到 `audit.events.read`
- 上一阶段明确没有完成: 账号/团队接口 `accounts.manage` 迁移、安全 bootstrap 门禁、按钮级权限、字段脱敏
- 本轮要交付的客户可见价值: 新客户空间仍能初始化首个管理员；初始化完成后，账号、角色、团队管理由 `accounts.manage` 权限控制
- 本轮是否只是评测: 否
- 本轮不做什么: 不新增数据库迁移、不引入一次性安装 token、不改前端页面、不改变真实外发开关
- 外部风险: 无外部平台动作，无真实外发
- 需要用户授权的动作: 无
- 验证方式: 账号/RBAC 后端测试、静态 readiness 检查、前端构建
- 下一阶段: RBAC 第四片，迁移会话、知识、工单、客户、线索等核心业务动作权限，或补前端按钮级权限

## 1. 本轮目标

账号体系不能只靠 `owner/admin` 角色硬判断。P3-06J 把账号、角色、团队接口迁到命名权限：

- `accounts.manage`

当前权限设计采用保守口径：

| 权限 | owner | admin | agent | viewer |
| --- | --- | --- | --- | --- |
| `accounts.manage` | 允许 | 禁止 | 禁止 | 禁止 |

这样做的原因是账号、角色、团队属于租户安全边界，不只是普通运营配置。后续如果需要让 admin 管理团队，可以单独拆 `teams.manage` 或 `accounts.read`，不要直接把所有账号管理权给 admin。

## 2. Bootstrap 保护

为了避免新租户无法创建首个管理员，本轮保留现有 bootstrap 特殊路径：

| 阶段 | 行为 |
| --- | --- |
| 租户还没有角色 | 允许无 token 创建第一个角色 |
| 租户还没有用户 | 允许无 token 创建第一个用户 |
| 租户还没有用户角色 | 允许无 token 完成首次角色分配 |
| 以上三步完成后 | 后续账号、角色、团队管理必须具备 `accounts.manage` |

当前 bootstrap 仍是工程受控试点口径，不是最终生产初始化方案。正式商用前还要补：

- 一次性安装 token。
- 初始化完成后关闭 bootstrap。
- 初始化动作审计和可追溯安装记录。
- 生产模式下禁止任意无 token bootstrap 的部署开关。

## 3. 已完成改动

- `backend/app/api/accounts.py` 引入 `principal_has_permission()`。
- 新增 `ACCOUNTS_MANAGE_PERMISSION = "accounts.manage"`。
- `_can_manage_tenant()` 从 `owner/admin` 角色判断改为 `accounts.manage` 权限判断，并保留同租户校验。
- `_require_manager()` 统一返回 `403 insufficient permission`。
- 首个角色、首个用户、首次角色分配的 bootstrap 条件保持不变。
- 新增测试覆盖 owner-only 权限矩阵、bootstrap 成功、无 token 后续管理失败、admin 后续管理失败、owner 团队成员管理成功。

## 4. 当前边界

| 未完成项 | 后续方向 |
| --- | --- |
| 一次性安装 token | 正式生产初始化前必须补 |
| `accounts.read` / `teams.manage` | 如果 admin 需要只读或团队管理，再拆更细权限 |
| 前端按钮级权限 | 根据 `user.permissions` 控制账号/团队入口和按钮 |
| 服务层统一权限 | 当前主要在 API 层，后续关键写动作还要向服务层收敛 |
| 审计 UI | 审计事件已有，但还没有正式账号安全审计页面 |

## 5. 验收结果

- `tests/test_p3_06j_accounts_rbac_bootstrap.py` 覆盖 P3-06J 新行为。
- `tests/test_accounts_api.py` 继续覆盖原账号、角色、团队主流程。
- `scripts/check_p3_06j_accounts_rbac_bootstrap.py` 用于静态确认权限迁移、测试和文档边界。

## 6. 后续建议

1. RBAC 第四片：会话动作、人工审核、outbox、工单、客户画像、线索动作迁到命名权限。
2. RBAC 第五片：前端按钮级权限统一读取 `user.permissions`，先从账号/团队、知识发布、工单动作开始。
3. RBAC 第六片：viewer/agent 字段脱敏和只读响应 allowlist。
4. 生产初始化专项：一次性安装 token、bootstrap 关闭、初始化审计和部署手册。
