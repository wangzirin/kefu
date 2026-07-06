# P3-06U-26H2W8A 本地首次部署门禁

本文档用于记录 H2W-8A 的真实工程边界。本阶段只处理本地首次部署、首任负责人创建、登录入口和交付安全门禁，不处理真实渠道外发、RPA、售后更新包和远程维护闭环。

## 目标

中小企业拿到本地部署包后，第一次启动系统时可以在浏览器中创建首任负责人账号。系统创建完成后，首任负责人入口立即锁定，后续用户只能用已有账号登录，不能通过网页端无身份重置密码。

本阶段同时要求登录页和状态接口明确暴露以下事实：

- 真实外发默认关闭。
- 开发入口关闭。
- 网页端不提供无身份重置。
- 系统不会预置默认密码。
- 首任负责人只能在空库第一次创建。

## 已完成改动

### 后端状态接口

`GET /api/auth/local-setup/status` 已升级为 H2W-8A 状态口径，返回：

| 字段 | 用途 |
| --- | --- |
| `setup_mode` | `create_first_owner` 或 `login_only`，决定前端是创建首任负责人还是普通登录。 |
| `first_owner_creation_locked` | 已初始化后必须为 `true`，防止重复创建首任负责人。 |
| `web_password_reset_enabled` | 当前固定为 `false`，表示网页端不提供无身份重置。 |
| `dev_bootstrap_enabled` | 开发免登录入口是否开启。交付验收必须为 `false`。 |
| `external_write_enabled` | 真实平台外发是否开启。H2W-8A 必须为 `false`。 |
| `trusted_inbound_worker_enabled` | 入站工作线程是否开启。H2W-8A 默认关闭。 |
| `local_deployment_ready` | 当危险门禁全部关闭时为 `true`。 |
| `readiness_checks` | 已通过的本地部署检查项。 |
| `blockers` | 仍未关闭的阻断项。 |

### 首任负责人创建

`POST /api/auth/local-setup/owner` 保持只允许空库创建第一个账号。创建后系统会自动写入默认角色、负责人用户、登录会话和审计事件。

创建成功后再次调用该接口必须返回 `409`，不能通过网页端重复初始化。

### 前端登录页

登录页改为两种清晰状态：

- 空库首次启动：主按钮为“创建负责人并进入”。
- 已初始化：主按钮为“登录”。

页面展示本地部署安全检查，不再让客户在“登录”和“创建账号”之间猜测。

## 停止门禁

出现以下任一情况，本阶段不能标记为完成：

- 空库启动时无法通过界面创建首任负责人。
- 已初始化后仍能通过网页端再次创建首任负责人。
- 登录页仍把首任账号称为“管理员账号”，导致责任口径不清。
- `dev_bootstrap_enabled=true` 时仍显示本地部署已就绪。
- `external_write_enabled=true` 时仍显示本地部署已就绪。
- 网页端出现无身份密码重置入口。
- 系统预置固定默认密码。
- UI 写成“已接通真实渠道”或“已自动外发”，但后端仍是 dry-run 或外发关闭。

## 验收命令

```bash
python scripts/check_p3_06u_26h2w8a_local_first_deploy.py
backend/.venv/bin/pytest backend/tests/test_local_setup_api.py backend/tests/test_auth_rbac_audit.py backend/tests/test_p3_06r_contract_closure.py
npm run typecheck
npm run build
```

## 下一阶段边界

H2W-8A 完成后，才进入 H2W-8B：诊断包、售后接收台、签名更新包、备份校验、回滚和审计闭环。

真实外发继续关闭。渠道官方授权、验签、回执、失败重试和审计闭环需要单独进入渠道专项。
