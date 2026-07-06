# P3-06E 运维心跳面板第一片

## 阶段结论

P3-06E 已完成第一片：标准运营版新增只读后台进程健康总览接口和前端“运维”工作区，用于查看可信入站 worker 的 heartbeat、最近运行、stale/failed 风险和真实外发开关状态。

这一步服务的是客户部署后的远程排障和内部运维，不代表真实渠道外发已经打开，也不代表完整 Prometheus/Grafana/告警体系已经完成。

## 本轮完成

- 新增 `GET /api/tenants/{tenant_id}/ops/worker-health`。
- 接口只读，不运行 worker，不触发模型调用，不写外部平台。
- 接口返回：
  - worker 数量汇总。
  - healthy/stale/failed/running/idle 计数。
  - `OUTBOX_EXTERNAL_WRITE_ENABLED` 当前状态。
  - `TRUSTED_INBOUND_WORKER_ENABLED` 当前状态。
  - worker heartbeat 列表。
  - 最近可信入站 worker 运行记录。
  - 运维风险与下一步动作。
- 接口要求 bearer token，且只允许 owner/admin 查看。
- 前端新增左侧导航“运维”。
- 前端新增 `#ops` 工作区：
  - 顶部健康指标卡。
  - 运行正常/需要处理状态。
  - 外部动作边界卡。
  - worker heartbeat 表。
  - 风险与动作卡。
  - 最近入站运行表。
- 演示模式提供同形样例数据，并明确外部写入为否。
- 总览阶段标识更新为 `P3-06E`。

## 关键文件

- `backend/app/api/ops.py`
- `backend/app/schemas/ops.py`
- `backend/app/schemas/inbound_worker.py`
- `backend/app/main.py`
- `backend/tests/test_p3_06e_ops_worker_health_api.py`
- `frontend/src/api/client.ts`
- `frontend/src/App.tsx`
- `frontend/src/styles.css`
- `frontend/src/data/navigation.ts`
- `scripts/check_p3_06e_ops_worker_health.py`

## 真实边界

- 不新增数据库表。
- 不新增常驻进程。
- 不执行真实 worker run。
- 不调用百炼、DeepSeek 或其他模型。
- 不写企业微信、微信、公众号、抖音、小红书、淘宝、京东、拼多多等外部平台。
- 不代表 Kubernetes/HPA 已完成。
- 不代表 Prometheus/Grafana/真实告警渠道已完成。
- 不代表高并发压测已完成。

## 后续建议

下一步可以二选一：

1. 企业微信公网 HTTPS 回调 smoke：在公网 URL、企微后台 Token/AESKey、测试客服账号具备后，做真实 URL 验证和白名单入站测试。
2. P3-06F 告警规则第一片：输出 Prometheus 指标草案、告警规则、运维 runbook 和只读 smoke，不接真实通知通道前不宣称告警已上线。
