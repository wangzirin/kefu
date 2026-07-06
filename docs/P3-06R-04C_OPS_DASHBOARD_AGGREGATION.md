# P3-06R-04C 运营总览服务端聚合接口

日期：2026-07-01

## 目标

把运营总览从“前端按已加载样本临时拼装”推进到“后端只读聚合接口优先”，让首页具备更接近正式商用中台的指标来源。

本片只做读侧聚合，不触发模型调用，不触发真实渠道外发，不返回客户原文、AI 草稿正文或待发送正文。

## 已完成

- 新增后端接口：`GET /api/tenants/{tenant_id}/ops/dashboard`
- 新增 `dashboard.read` 权限：
  - owner、admin、viewer 可读。
  - agent 不可读经营总览。
- 新增后端聚合字段：
  - 入站会话数、入站消息数。
  - open 人审任务、高风险人审任务。
  - 待确认草稿、待发送草稿。
  - 失败复盘、死信/阻断发送任务。
  - 知识缺口、开放工单、开放线索。
  - 平均等待分钟、AI 草稿覆盖率、人工审核压力、异常压力、健康分。
  - 渠道矩阵、处理漏斗、趋势桶、最新知识评测质量信号、待处理事项。
- 新增前端 API 类型和调用：
  - `BusinessOpsDashboard`
  - `getBusinessOpsDashboard()`
- 前端首页接入：
  - 正式登录且具备 `dashboard.read` 时优先读取后端聚合接口。
  - 演示模式或接口不可用时回退到本地样本聚合。
  - 首页会标明当前使用“服务端聚合”或“本地样本”。

## 权限与安全边界

- 接口只返回聚合指标，不返回 message.content、draft.reply_text、human_review.draft_reply 等正文。
- 跨租户请求保持 404。
- 无 token 返回 401。
- agent 返回 403。
- viewer 可以读取脱敏经营指标，但不能读取会话、客户、工单、知识原文等明细。
- `external_call_performed=false`
- `external_platform_write_performed=false`

## 当前不是

- 不是完整历史数仓。
- 不是物化指标表。
- 不是 Prometheus/Grafana dashboard。
- 不是高并发实时流式 BI。
- 不是真实渠道外发能力。
- 不是字段级 allowlist/脱敏终局方案。

## 后续建议

1. P3-06R-03B：补真实登录端到端动作 smoke，验证坐席主路径在真实后端状态下可完成。
2. P3-06R-04D：把运营总览聚合从即时查询升级为可缓存/可物化的统计层。
3. P3-06R-05：渠道连接器中心第一片，把企微、公众号、电商平台入口状态做成正式配置台。
4. 字段脱敏与字段 allowlist：在真实客户试点前补齐，但不在当前片过度展开。

## 验证

- `.venv/bin/python -m pytest backend/tests/test_p3_06r_ops_dashboard_api.py -q`
- `.venv/bin/python -m pytest backend/tests/test_p3_06r_ops_dashboard_api.py backend/tests/test_p3_06h_rbac_permission_matrix.py backend/tests/test_p3_06i_rbac_permission_snapshot.py backend/tests/test_p3_06g_ops_metrics_api.py backend/tests/test_p3_06f_ops_alert_rules_api.py backend/tests/test_p3_06e_ops_worker_health_api.py -q`
- `cd frontend && npm run typecheck`
- `cd frontend && npm run build`
- Chrome 本地预览：`http://127.0.0.1:4174/#overview`
  - 首页可打开。
  - 运营图表可渲染。
  - 演示模式显示“本地样本”。
  - 左侧深色导航保持在左侧，未随键盘滚动漂移。

