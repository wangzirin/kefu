# P3-06T-02 首页数据口径收紧

日期：2026-07-01

## Engineering Control Card

- Stage: P3-06T-02 首页数据口径收紧。
- 来源计划: `docs/P3-06T_NEXT_FOUR_ISSUES_ENGINEERING_PLAN.md` 的问题三。
- 本片客户可见价值: 首页指标不再只是“看起来像 BI”，而是明确显示数据来源、时间窗口、刷新方式、聚合粒度和敏感字段排除边界。
- 本片不是: 运营总览视觉大重做、历史数仓、物化统计表、Grafana 接入、真实外发、真实渠道联调。
- 外部动作: 无真实外发、无模型调用、无生产数据库动作。
- 本片停止条件: 后端响应可追溯；非法时间范围和未知渠道不能静默回退；前端正式登录筛选会请求服务端聚合；演示模式明确显示本地汇总。

## 本轮修复的问题

P3-06R-04C 已经有运营总览服务端聚合接口，P3-06T-01 已经修复首页壳层滚动。本轮继续处理首页数据可信度：

- 首页必须说明当前是服务端聚合、本地汇总还是演示样本。
- 时间范围和渠道筛选不能让客户误以为已经查询真实后台数据。
- 后端聚合必须明确排除客户原文、AI 草稿正文、出站草稿全文、联系方式、回执 raw payload 和连接器配置。
- 无效参数不能静默回退为默认视图。

## 后端改动

文件:

```text
backend/app/schemas/ops.py
backend/app/api/ops.py
backend/tests/test_p3_06r_ops_dashboard_api.py
```

新增数据契约字段:

| 字段 | 含义 |
| --- | --- |
| `data_source.contract_version` | 当前首页聚合契约版本，本轮为 `p3_06t_02_v1` |
| `data_source.aggregation_grain` | 聚合粒度，本轮为租户、时间范围、渠道维度 |
| `data_source.refresh_model` | 刷新方式，本轮为请求时即时读取 |
| `data_source.source_tables` | 聚合用到的内部业务表清单 |
| `data_source.excluded_fields` | 明确不进入首页响应的敏感字段清单 |
| `data_source.caveats` | 当前口径限制说明 |

继续保留并验收:

- `data_mode`
- `data_source`
- `source_window`
- `filters`
- `generated_at`
- `external_call_performed=false`
- `external_platform_write_performed=false`

新增/强化测试:

- owner/admin/viewer 可读，agent 禁止读取。
- 响应不包含客户原文、AI 草稿正文、出站草稿全文。
- `range=90d` 返回 422，不静默回退。
- 未知 `channel_id` 返回 404，不静默回退为全部渠道。
- 渠道筛选后返回明确的 `filters` 和契约版本。

## 前端改动

文件:

```text
frontend/src/api/client.ts
frontend/src/App.tsx
frontend/src/styles.css
```

改动:

- `BusinessOpsDashboardDataSource` 类型补齐契约字段。
- `refreshBusinessOpsDashboard()` 支持 `range` 和 `channel_id` 参数，不再固定请求 `today`。
- 运营总览时间范围和渠道筛选按钮在正式登录且具备 `dashboard.read` 权限时，会请求对应服务端聚合。
- 首页头部新增数据口径标签:
  - 时间窗口。
  - 刷新模型。
  - 源表数量。
  - 排除敏感字段数量。
- 演示模式仍显示本地汇总，但明确标注“本地汇总 / 时间范围 / 渠道”。

## 验证结果

后端:

```bash
cd backend
. .venv/bin/activate
pytest tests/test_p3_06r_ops_dashboard_api.py
```

结果: 4 passed，只有既有 `httpx` / Starlette deprecation warning。

前端:

```bash
cd frontend
npm run typecheck
npm run build
```

结果: 通过。Vite 仍提示 `OpsDashboardChart` chunk 大于 500kB，这是既有图表包体提示，不是本片错误。

浏览器 smoke:

```text
output/p3_06t_02_dashboard_contract_smoke/
```

结果:

- 首页可渲染。
- 数据口径标签可见。
- 点击“近 7 天”后按钮状态和口径标签更新。
- 无横向溢出。

## 剩余风险

- 本轮没有重做运营总览视觉和图表布局，P3-06T-03 仍需要做 BI 首页重做。
- 当前服务端聚合仍是即时读侧聚合，不是历史数仓、物化指标表或高并发 BI 缓存。
- 渠道筛选下知识缺口暂只在全部渠道视图统计；如果后续知识缺口要按渠道归因，需要补来源渠道字段。
- 当前前端正式登录后的服务端刷新需要真实 token 和权限；演示模式仍保持本地样本，不会请求真实接口。

## Stage Completion

- Stage: P3-06T-02 首页数据口径收紧。
- What changed: 后端 dashboard 响应补齐契约版本、聚合粒度、刷新模型、源表、敏感字段排除和口径备注；前端筛选按钮接入服务端聚合请求；首页新增数据口径标签。
- What was verified: 后端运营总览测试 4 个通过；前端 typecheck 通过；前端 build 通过；浏览器 smoke 通过。
- What remains not done: P3-06T-03 运营总览 BI 重做、P3-06T-04 信息架构收口、统计缓存/物化层、真实平台联调和真实外发。
- Whether this was customer-visible: 是，首页会直接展示更清楚的数据来源和口径。
- Whether this was only evaluation: 否，包含后端契约字段、前端刷新逻辑和页面口径展示。
- Next stage: P3-06T-03 运营总览 BI 重做。
