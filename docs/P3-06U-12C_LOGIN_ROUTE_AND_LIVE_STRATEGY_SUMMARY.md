# P3-06U-12C 登录路径保留与对话台策略摘要

日期：2026-07-02

## 目标

解决两个真实使用问题：

1. 打开 `#rpa-lab` 时如果没有登录，会被登录页拦住；登录成功后原本会被强制带回 `#overview`。
2. RPA 副驾驶策略只停留在实验页，尚未进入坐席日常处理路径。

本阶段保持边界：

- 不接真实平台账号。
- 不读取平台后台。
- 不保存人工粘贴消息。
- 不创建 outbox 外发动作。
- 不触发真实发送。

## 本轮完成

### 1. 登录后保留目标页面

修改 `frontend/src/App.tsx`：

- 正式登录成功后，不再固定跳转 `#overview`。
- “开发演示进入”也不再固定跳转 `#overview`。
- 会优先保留当前 hash，例如 `#rpa-lab`、`#live`。
- 如果当前账号无权访问目标页面，才回到该角色默认入口。

这解决了“我打开 RPA Lab 还是登录页，登录后又找不到 Lab”的问题。

### 2. 本地测试进入

新增后端接口：

```text
POST /api/auth/dev-local-login
```

用途：

- 只在 `STANDARD_OPS_ENV=development` 且开发 bootstrap 开启时可用。
- 使用本地开发库固定租户 `wanfa-local-dev`。
- 使用本地开发库固定账号 `real-test@wanfa.local`。
- 返回正常 bearer token。
- 不打印、不记录明文密码。

前端登录页新增按钮：

```text
本地测试进入
```

当前本地研究阶段优先点这个按钮，不需要手动输入密码。正式账号仍可使用租户、邮箱、密码登录。

### 3. 对话台策略摘要

修改 `frontend/src/components/conversation/ConversationWorkbenchPanel.tsx`：

- 在多渠道对话台的当前会话区域新增“回复策略”摘要。
- 点击“试算当前会话”后，调用同一个 dry-run 策略服务。
- 使用当前会话的最近客户消息或人审触发消息作为输入。
- 展示：
  - 填入草稿 / 人工接管 / 补知识。
  - 意图。
  - 下一步。
  - 置信度。
  - 引用数量。

这一步不是把 RPA Lab 变成正式平台接入能力，而是把策略判断能力放入坐席工作流做验证。

## 当前使用方式

本地预览：

```text
http://127.0.0.1:5181/#rpa-lab
```

如果出现登录页：

1. 不需要手填密码。
2. 点击“本地测试进入”。
3. 页面会继续停留在 `#rpa-lab`。

进入多渠道对话台：

```text
http://127.0.0.1:5181/#live
```

选择一条会话后，点击“试算当前会话”，查看回复策略摘要。

## 验证

已通过：

```bash
backend/.venv/bin/pytest -q backend/tests/test_auth_rbac_audit.py backend/tests/test_p3_06u_12b_rpa_copilot_api.py
npm run typecheck
npm run build
CHROME_DEBUGGING_URL=http://127.0.0.1:9227 FRONTEND_URL=http://127.0.0.1:5181/ node scripts/check_p3_06u_12c_login_route_and_live_strategy.mjs
```

浏览器证据：

```text
output/p3_06u_12c_login_route_and_live_strategy/
```

包含：

- `rpa-lab-after-local-login.png`
- `live-workbench-strategy-summary.png`
- `summary.json`

## 下一步

P3-06U-12D 建议继续做：

- 把“策略摘要”与已有 AI 草稿、人审原因、知识引用合并成一个更清楚的坐席判断区。
- 避免策略摘要、知识无命中提示、建议动作三块互相重复。
- 继续保持 dry-run，不保存、不外发。
