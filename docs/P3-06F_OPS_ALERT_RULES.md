# P3-06F 告警规则第一片

## 阶段结论

P3-06F 已完成第一片：标准运营版新增只读告警规则评估接口和前端“运维与告警”展示区，用于把 P3-06E 的 worker 心跳、最近运行、外发开关和配置状态固化成可重复评估的规则与 runbook。

本阶段不是完整告警系统。它不会发送企业微信、飞书、短信、邮件或 PagerDuty 通知，不接 Prometheus/Grafana，不触发模型调用，也不写任何外部平台。

## 本轮完成

- 新增 `GET /api/tenants/{tenant_id}/ops/alert-rules`。
- 接口只读，不启动 worker，不重放任务，不触发模型调用，不写外部平台。
- 接口要求 bearer token，且只允许同租户 owner/admin 查看。
- 接口返回：
  - 告警规则目录。
  - 每条规则当前 `ok` / `firing` 状态。
  - `page` / `ticket` 响应类型。
  - 触发原因、当前值、阈值和持续窗口。
  - runbook 首查步骤、升级口径和静默条件。
  - `notification_channel_enabled=false`。
  - `notification_sent=false`。
  - `external_call_performed=false`。
  - `external_platform_write_performed=false`。
- 前端“运维”页更新为“运维与告警”。
- 前端新增告警规则区：
  - 触发规则摘要。
  - 通知通道边界。
  - 外部动作边界。
  - 规则卡片与首查步骤。
- 演示模式提供同形规则数据，并明确没有真实通知和外部写入。
- 总览阶段标识更新为 `P3-06F`。

## 第一批规则

| 规则代码 | 类型 | 触发口径 |
| --- | --- | --- |
| `trusted_inbound_processing_unavailable` | page / critical | worker 已启用，但没有 healthy worker |
| `worker_config_incomplete_when_enabled` | ticket / warning | worker 已启用，但租户或管理员用户配置缺失 |
| `worker_heartbeat_missing` | ticket / warning | 当前租户没有任何 worker heartbeat |
| `trusted_inbound_worker_stale` | ticket / warning | 任一 worker heartbeat 超过 stale 阈值 |
| `trusted_inbound_worker_failed` | page / critical | 任一 worker 处于 failed 健康状态 |
| `trusted_inbound_recent_run_failed` | ticket / warning | 最近运行记录出现 failed 或 failed 计数大于 0 |
| `external_write_boundary_breach` | page / critical | 外发开关开启，或最近运行记录出现 external write |
| `trusted_inbound_rate_limit_saturation` | ticket / warning | 最近运行窗口出现连续限流或单次限流饱和 |

## 关键文件

- `backend/app/api/ops.py`
- `backend/app/schemas/ops.py`
- `backend/tests/test_p3_06f_ops_alert_rules_api.py`
- `frontend/src/api/client.ts`
- `frontend/src/App.tsx`
- `frontend/src/styles.css`
- `frontend/src/data/navigation.ts`
- `scripts/check_p3_06f_ops_alert_rules.py`

## 真实边界

- 不新增数据库表。
- 不新增常驻进程。
- 不执行真实 worker run。
- 不调用百炼、DeepSeek 或其他模型。
- 不发送企业微信、飞书、短信、邮件或 PagerDuty 通知。
- 不写企业微信、微信、公众号、抖音、小红书、淘宝、京东、拼多多等外部平台。
- 不代表 Prometheus/Grafana 已完成。
- 不代表高并发压测已完成。
- 不代表真实渠道自动回复上线。

## 后续建议

下一步可以二选一：

1. 企业微信公网 HTTPS 回调 smoke：具备公网 URL、企微后台 Token/AESKey、测试客服账号后，做真实 URL 验证和白名单入站测试。
2. P3-06G 指标出口第一片：新增只读 `/metrics` 草案或内部指标快照接口，但仍不接真实通知通道前不宣称告警系统上线。
