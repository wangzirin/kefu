# Windows 继续开发与本地试运行说明

本包用于在 Windows 电脑上继续开发“万法常世 AI 全智能客服系统 standard_ops”。它是开发交接包和本地试运行包，不是已签名的正式 exe 安装器。

## 包内边界

- 包含源码、文档、脚本、Docker 配置、Windows PowerShell/BAT 启动候选和关键审计证据。
- 不包含真实 `.env`、API key、数据库密码、`.git`、虚拟环境、`node_modules`、本地数据库、浏览器 profile 和大体积历史输出。
- 真实外发默认关闭。
- 企业微信、抖音、淘宝、京东、拼多多等真实渠道未在本包中接通。
- Windows 启动脚本是候选包装，不是已签名 exe。

## 推荐方式：Docker 本地试运行

适合先把系统跑起来，再继续开发。

1. 安装 Docker Desktop，并确认 Docker Desktop 已启动。
2. 解压本包，进入 `wanfa-standard-ops` 目录。
3. 复制环境模板：

```powershell
Copy-Item deploy\customer.env.example deploy\customer.env
```

4. 打开 `deploy\customer.env`，至少替换两处数据库密码：

```text
STANDARD_OPS_POSTGRES_PASSWORD=replace-with-local-random-password
DATABASE_URL=postgresql+psycopg://wanfa_ops:replace-with-local-random-password@postgres:5432/wanfa_ops
```

保持以下安全开关：

```text
STANDARD_OPS_DEV_BOOTSTRAP_ENABLED=false
OUTBOX_EXTERNAL_WRITE_ENABLED=false
TRUSTED_INBOUND_WORKER_ENABLED=false
ADMIN_BOOTSTRAP_PASSWORD=
```

5. 双击或运行：

```powershell
installers\windows\start-wanfa-customer-service.bat
```

也可以直接运行：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File installers\windows\Start-WanfaCustomerService.ps1
```

6. 启动后访问：

```text
前端工作台：http://127.0.0.1:5173
后端健康检查：http://127.0.0.1:18080/health
```

首次进入页面后创建首任负责人账号；本包不会预置默认密码。

## 开发方式：本机安装依赖

适合继续写代码、跑测试、改前端。

建议版本：

- Python 3.12
- Node.js 20 或更高
- Docker Desktop
- PowerShell 7 可选，Windows PowerShell 也可运行当前脚本

安装前端依赖：

```powershell
npm --prefix frontend install
npm --prefix frontend run typecheck
npm --prefix frontend run build
```

安装后端依赖：

```powershell
py -3.12 -m venv backend\.venv
backend\.venv\Scripts\python -m pip install -U pip
backend\.venv\Scripts\pip install -r backend\requirements.txt
```

开发时建议仍用 Docker 提供 PostgreSQL、Redis 和 pgvector。若使用本机启动后端，请确保 `DATABASE_URL` 指向可用 PostgreSQL，并执行迁移：

```powershell
cd backend
.\.venv\Scripts\python -m alembic -c alembic.ini upgrade head
.\.venv\Scripts\python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8081
```

另开一个终端启动前端：

```powershell
npm --prefix frontend run dev
```

开发模式默认访问：

```text
前端：http://127.0.0.1:5173
后端：http://127.0.0.1:8081/health
```

## 当前推荐验证命令

```powershell
npm --prefix frontend run typecheck
npm --prefix frontend run build
backend\.venv\Scripts\python -m pytest backend\tests\test_foundation_api.py backend\tests\test_p3_06u_26h2w_sealed_pilot_package_gates.py -q
node scripts\audit_p3_06u_frontend_button_logic_layout.mjs
backend\.venv\Scripts\python scripts\check_p3_06u_26h2w_install2_native_installer_readiness.py
backend\.venv\Scripts\python scripts\check_p3_06u_26h2w_install3_native_app_packaging_gate.py
```

## 如果启动失败

- 先确认 Docker Desktop 已启动，而不是只安装了 Docker CLI。
- 确认 `deploy\customer.env` 存在。
- 确认数据库密码不再是 `replace-with-local-random-password`。
- 确认端口 `5173`、`18080`、`5432`、`6379` 没有被其他项目占用。
- 运行 `installers\windows\HealthCheck-WanfaCustomerService.ps1` 查看本地状态。

