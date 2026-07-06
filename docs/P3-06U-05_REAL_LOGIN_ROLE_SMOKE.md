# P3-06U-05 真实登录与角色端到端前端 Smoke

日期：2026-07-01

## Engineering Control Card

| 项目 | 内容 |
| --- | --- |
| 阶段编号 | P3-06U-05 |
| 阶段名称 | 真实登录与角色端到端前端 Smoke |
| 上游阶段 | P3-06U-01 契约矩阵、P3-06U-02 角色任务路径、P3-06U-03 接待工作台、P3-06U-04 首页到处理路径 |
| 本片客户可见价值 | 证明中台不是只在演示身份下成立；真实账号登录后，不同岗位看到的入口、默认页和任务路径符合权限设计 |
| 本片工程目标 | 用真实账号、真实令牌、真实前端页面跑通 owner/admin/agent/viewer 四类角色 |
| 本片不做 | 不使用开发演示进入；不触发真实平台外发；不连接真实客户数据；不改生产数据库 |
| 停止条件 | 四类角色均可登录、默认页正确、菜单权限正确、任务路径正确、受限路径不误进、退出后清空令牌 |
| 验证方式 | 静态检查、前端 typecheck/build、后端 RBAC 回归、Chrome CDP 真实登录截图 smoke |

## 本片解决的问题

前几片已经把前后端契约、角色路径、接待工作台和首页处理入口做出来。它们仍然有一个风险：如果只靠开发演示身份验证，无法证明真实租户账号、真实登录令牌和真实权限矩阵下也成立。

本片把验证方式改为真实登录链路：

1. 通过后端 API 创建临时租户。
2. 创建 `owner`、`admin`、`agent`、`viewer` 四个真实用户。
3. 通过 `/api/auth/login` 获取真实令牌。
4. 在前端登录页输入租户、邮箱和密码。
5. 进入工作台后调用 `/api/auth/me` 确认当前身份。
6. 检查角色可见菜单、默认页、任务路径、受限路径和退出清理。

## 角色验收矩阵

| 角色 | 默认入口 | 应看到的主工作区 | 不应看到的主工作区 | 任务路径 |
| --- | --- | --- | --- | --- |
| owner | 运营总览 | 总览、工作台、客户、知识运营、质量复盘、渠道接入、管理运维 | 无 | 判断今日风险、处理高风险草稿、确认待发送、修复知识缺口、检查渠道接入 |
| admin | 运营总览 | 总览、工作台、客户、知识运营、质量复盘、渠道接入、管理运维 | 无 | 判断今日风险、处理高风险草稿、确认待发送、复盘质量错因、修复知识缺口 |
| agent | 运营总览 | 总览、工作台、客户、知识运营 | 质量复盘、渠道接入、管理运维、知识缺口、知识评测 | 接待客户会话、处理高风险草稿、确认待发送、跟进客户线索、跟进工单时效 |
| viewer | 运营总览 | 总览、质量复盘、渠道接入 | 工作台、客户、知识运营、管理运维 | 判断今日风险、复盘质量错因、检查渠道接入 |

## 禁用动作和受限路径

本片不是只检查“能不能登录”。还检查两个容易被忽略的体验边界：

| 边界 | 验证方式 | 期望 |
| --- | --- | --- |
| 可看但不可操作 | `agent` 进入知识库运营页 | 相关管理动作显示清楚原因，例如“仅管理员可导入” |
| 不可见也不可进 | `viewer` 直接访问 `#live` | 自动回到 `#overview`，不出现无解释的空白页 |

如果前端误向后端请求低权限接口并收到 `403`，脚本会记录为失败。正常状态下，前端应先根据权限隐藏入口或禁用动作，避免让用户撞到后端权限错误。

## 新增工程资产

| 文件 | 作用 |
| --- | --- |
| `scripts/check_p3_06u_05_real_login_role_smoke.mjs` | Chrome CDP 真实登录角色 smoke，生成截图和 `summary.json` |
| `scripts/check_p3_06u_05_real_login_role_smoke.py` | 静态门禁，确认脚本、前端稳定选择器和文档存在 |
| `output/p3_06u_role_smoke/` | 浏览器截图与结构摘要输出目录 |

前端仅新增稳定测试选择器：

- 登录表单：`data-role-smoke="login-form"`
- 租户输入：`data-role-smoke="tenant-slug"`
- 邮箱输入：`data-role-smoke="email"`
- 密码输入：`data-role-smoke="password"`
- 登录按钮：`data-role-smoke="login-submit"`
- 退出按钮：`data-role-smoke="logout-button"`
- 导航入口：`data-workspace-nav`
- 任务路径：`data-role-task-id`

这些标识不改变客户看到的视觉、文案和权限逻辑。

## 运行方式

后端需要先以开发测试环境启动，并保证数据库已经建表。推荐使用临时 SQLite 数据库，不污染正式环境：

```bash
cd /Users/ericlee/Desktop/肥肥lu/lite_a_customer_service/standard_ops/backend
DATABASE_URL=sqlite+pysqlite:////tmp/wanfa_p3_06u_05_smoke.sqlite STANDARD_OPS_ALLOWED_ORIGINS=http://127.0.0.1:5178 python - <<'PY'
import app.models  # noqa: F401
from app.db.base import Base
from app.db.session import get_engine
Base.metadata.create_all(bind=get_engine())
PY
DATABASE_URL=sqlite+pysqlite:////tmp/wanfa_p3_06u_05_smoke.sqlite STANDARD_OPS_ALLOWED_ORIGINS=http://127.0.0.1:5178 uvicorn app.main:app --host 127.0.0.1 --port 8081
```

前端需要通过 Vite 代理到后端：

```bash
cd /Users/ericlee/Desktop/肥肥lu/lite_a_customer_service/standard_ops/frontend
VITE_API_PROXY_TARGET=http://127.0.0.1:8081 npm run dev -- --host 127.0.0.1 --port 5178 --strictPort
```

Chrome 需要开启调试端口：

```bash
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9224 --user-data-dir=/tmp/wanfa-chrome-p3-06u-05
```

运行 smoke：

```bash
cd /Users/ericlee/Desktop/肥肥lu/lite_a_customer_service/standard_ops
BACKEND_URL=http://127.0.0.1:8081 FRONTEND_URL=http://127.0.0.1:5178/#overview CHROME_DEBUGGING_URL=http://127.0.0.1:9224 node scripts/check_p3_06u_05_real_login_role_smoke.mjs
```

## 验收输出

成功后输出：

- `output/p3_06u_role_smoke/owner-default.png`
- `output/p3_06u_role_smoke/admin-default.png`
- `output/p3_06u_role_smoke/agent-default.png`
- `output/p3_06u_role_smoke/agent-permission-note.png`
- `output/p3_06u_role_smoke/viewer-default.png`
- `output/p3_06u_role_smoke/viewer-restricted-redirect.png`
- `output/p3_06u_role_smoke/summary.json`

`summary.json` 会记录每个角色的默认页、当前用户角色、可见导航、任务路径、受限路径结果、退出是否清空令牌和 `403` 数量。

## 下一步

完成 P3-06U-05 后，下一片应进入 `P3-06U-06 质量复盘 BI`。

原因很直接：真实角色路径成立以后，中台最需要补的是“为什么答错、哪里变差、该修哪条知识”。质量复盘不能只是列表，它要能把低置信、转人工、无知识命中、发送失败和评测失败汇总成可定位、可修复、可复测的运营看板。
