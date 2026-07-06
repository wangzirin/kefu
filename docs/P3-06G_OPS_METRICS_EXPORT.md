# P3-06G 指标出口第一片

日期：2026-07-01  
范围：标准运营版客服中台后端运维接口与前端管理运维页  
状态：第一片完成

## Engineering Control Card

- Stage: P3-06G 第一片
- 当前主线阶段: 管理运维可观测性收口
- 上一阶段真正完成: P3-06UI 管理运维内部二级 Tab，`#ops/#model/#settings` 已进入同一个管理运维工作区
- 上一阶段明确没有完成: 后端资源级 RBAC、真实通知通道、真实 Prometheus/Grafana 接入、真实云监控告警推送
- 本轮要交付的客户可见价值: 管理员可以在运维页看到 worker、告警、队列、失败复盘和外发边界的只读指标出口
- 本轮是否只是评测: 否
- 本轮不做什么: 不发送真实通知、不执行真实外发、不调用模型、不写平台、不新增数据库迁移
- 外部风险: 无真实外部动作；所有指标来自本地数据库和配置
- 需要用户授权的动作: 无
- 验证方式: 后端目标测试、前端构建、静态 readiness 检查
- 写回文件: 产品化总控计划、Superpowers P3 计划、Project_012 执行记录/关键决策/文件索引/复盘
- 下一阶段: RBAC 收口第一片

## 1. 本轮目标

P3-06F 已经让中台能看到告警规则的触发状态，但还没有一个面向运维系统的统一指标出口。P3-06G 第一片补齐这个缺口：把 worker 健康、告警规则、队列积压、死信任务、失败复盘和真实外发开关整理成稳定的只读指标。

这一片不是把系统接到真实 Prometheus、Grafana、阿里云云监控或告警群，而是先把可采集的数据口径做出来。

## 2. 新增接口

| 项目 | 内容 |
| --- | --- |
| 接口 | `GET /api/tenants/{tenant_id}/ops/metrics` |
| 权限 | 同租户，且当前仍沿用 `owner/admin` |
| 参数 | `stale_after_seconds`、`recent_run_limit` |
| 返回 | `summary`、`metrics`、`prometheus_text`、外部动作边界字段 |
| 外部动作 | `external_call_performed=false`、`external_platform_write_performed=false` |

## 3. 当前指标范围

| 指标 | 来源 | 作用 |
| --- | --- | --- |
| `wanfa_worker_total` | `worker_heartbeats` | 当前租户记录过心跳的 worker 总数 |
| `wanfa_worker_healthy` | `worker_heartbeats.health_status` | 心跳在阈值内的 worker 数 |
| `wanfa_worker_stale` | `worker_heartbeats.health_status` | 心跳超时的 worker 数 |
| `wanfa_worker_failed` | `worker_heartbeats.health_status` | 标记失败的 worker 数 |
| `wanfa_worker_loops_completed_total` | `worker_heartbeats.loops_completed` | worker 循环累计计数 |
| `wanfa_ops_alert_rules_firing` | `ops.alert_rules` | 当前触发的规则数 |
| `wanfa_ops_alert_rules_page` | `ops.alert_rules` | 需要立即处理的规则数 |
| `wanfa_ops_alert_rules_ticket` | `ops.alert_rules` | 需要跟进处理的规则数 |
| `wanfa_trusted_inbound_runs_failed_recent` | `trusted_inbound_worker_runs` | 最近窗口中失败的入站运行数 |
| `wanfa_trusted_inbound_runs_rate_limited_recent` | `trusted_inbound_worker_runs.rate_limited` | 最近窗口中被限流的任务数 |
| `wanfa_queue_backlog_total` | `outbox_delivery_jobs`、`trusted_inbound_message_jobs` | 出站和可信入站队列积压总数 |
| `wanfa_outbox_delivery_jobs` | `outbox_delivery_jobs.status` | 出站任务按状态聚合 |
| `wanfa_outbox_dead_letter_jobs` | `outbox_delivery_jobs.status` | 出站死信任务数 |
| `wanfa_delivery_failure_reviews` | `delivery_failure_reviews.status` | 失败复盘按状态聚合 |
| `wanfa_delivery_failure_reviews_open` | `delivery_failure_reviews.status` | 打开的失败复盘数 |
| `wanfa_external_write_enabled` | `OUTBOX_EXTERNAL_WRITE_ENABLED` | 真实外发总开关 |
| `wanfa_trusted_inbound_worker_enabled` | `TRUSTED_INBOUND_WORKER_ENABLED` | 可信入站 worker 配置开关 |

## 4. 前端变化

管理运维页新增“指标出口”板块：

- 上方显示立即处理规则、队列积压、死信任务、失败复盘四个关键数。
- 左侧显示优先级最高的重点指标，严重和关注项优先靠前。
- 右侧显示采集文本预览，便于后续对接 Prometheus 或云监控。
- 演示模式也提供结构一致的样例数据，方便本地预览。

## 5. 当前边界

| 不做项 | 原因 |
| --- | --- |
| 不暴露无鉴权 `/metrics` | 当前系统还没有完成后端资源级 RBAC 和部署网关鉴权策略 |
| 不接真实告警通知 | 需要先明确通知渠道、静默策略、值班和客户授权 |
| 不执行真实外发 | 指标出口只读，不应该改变队列或平台状态 |
| 不加入高基数标签 | 避免把用户、会话、消息、错误文本放入指标标签导致监控系统膨胀 |

## 6. 验收标准

- 后端接口返回 `summary`、`metrics`、`prometheus_text`。
- 指标覆盖 worker、告警、队列、失败复盘和外发边界。
- 响应明确 `external_call_performed=false`、`external_platform_write_performed=false`。
- 前端管理运维页出现“指标出口”和“采集文本预览”。
- 后端目标测试通过。
- 前端构建通过。
- 静态 readiness 脚本通过。

## 7. 后续建议

1. RBAC 收口第一片：把页面、按钮、API 和服务层权限矩阵统一，避免只靠前端隐藏菜单。
2. 指标出口第二片：按部署形态决定是否增加网关保护下的 Prometheus scrape endpoint。
3. 告警第二片：接入企业微信、飞书、邮件或短信前，先补静默、去重和 runbook 链接。
4. 生产部署片：把指标出口纳入托管云端版和私有化部署版的运维手册。
