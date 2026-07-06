# P3-06B 可信入站 Worker 租约与运行记录第一片

日期：2026-07-01

## 阶段定位

P3-06B 把可信入站 worker 从“手动触发后直接扫描可信 webhook 事件”推进到“每次运行可追溯、每条入站消息可租约化处理、异常后可重放”的生产化第一片。

本阶段仍然不接真实外发，不打开企业微信、公众号、电商平台的真实发送动作，也不引入 Redis/Celery/Kafka 或常驻 worker 进程。

## 已完成能力

### 1. Worker Run 运行记录

新增 `trusted_inbound_worker_runs` 表，记录每次 worker 调用：

- 租户、worker_id、运行模式
- batch_size、rate_limit_per_minute、lease_seconds
- scanned、processed、succeeded、failed、skipped、rate_limited
- request_payload、result_payload
- started_at、finished_at

同时新增只读接口：

```text
GET /api/tenants/{tenant_id}/trusted-inbound-worker-runs
```

用途是让后续运营和排障能看到最近的入站 worker 运行历史，而不是只能靠接口响应或日志回忆。

### 2. 入站消息处理租约

新增 `trusted_inbound_message_jobs` 表，以 `tenant_id + message_id` 和 `tenant_id + idempotency_key` 保证同一条可信入站消息只进入一个处理 job。

每条 job 记录：

- message_id、conversation_id、idempotency_key
- status：`queued`、`locked`、`succeeded`、`failed`
- attempts_count
- locked_by、locked_at
- last_run_record_id
- workflow_run_id、human_review_task_id
- last_error、completed_at

### 3. Fresh Lock 跳过

如果某条可信入站消息已经被另一个 worker 在 lease 期限内锁住，本轮 worker 会跳过它，并在响应里输出：

```json
{
  "lease": {
    "fresh_locked_skipped": 1
  }
}
```

这避免多个 worker 同时处理同一条入站消息。

### 4. Stale Lock 接管

如果某条消息处于 `locked`，但 `locked_at` 已超过 `lease_seconds`，新 worker 可以接管该 job。

响应会输出：

```json
{
  "lease": {
    "stale_locked_reclaimed": 1
  }
}
```

这解决 worker 异常退出后消息长期卡死的问题。

### 5. 失败后重放

如果编排过程中失败，job 会进入 `failed`，记录 `last_error`，不会创建 workflow run。

后续 worker 再次运行时，可以重新 claim 该 failed job，成功后把同一条消息推进到 workflow run 和人工审核任务。

## 接口变化

### POST 运行 worker

```text
POST /api/tenants/{tenant_id}/trusted-inbound-worker-runs
```

新增输入字段：

| 字段 | 默认 | 说明 |
| --- | --- | --- |
| `worker_id` | `manual_api_worker` | 标识本次运行者，用于锁和排障 |
| `lease_seconds` | `60` | locked job 超过该秒数后可被接管 |

新增响应字段：

| 字段 | 说明 |
| --- | --- |
| `run_record_id` | 本次运行记录 ID |
| `worker_id` | 本次 worker 标识 |
| `lease` | 租约证据，包括 claim、fresh skip、stale reclaim、failed replay |
| `items[].job_id` | 每条处理消息对应的入站 job ID |

### GET 查看运行记录

```text
GET /api/tenants/{tenant_id}/trusted-inbound-worker-runs?limit=20&offset=0
```

只读返回最近运行记录，不触发任何编排、外发或真实平台动作。

## 文件变更

| 文件 | 变更 |
| --- | --- |
| `backend/app/models/foundation.py` | 新增 `TrustedInboundWorkerRunRecord`、`TrustedInboundMessageJob` |
| `backend/app/models/__init__.py` | 导出新增模型和 `utc_now` |
| `backend/app/migrations/versions/0021_trusted_inbound_worker_leases.py` | 新增两张表和索引 |
| `backend/app/schemas/inbound_worker.py` | 新增 worker_id、lease_seconds、run_record 和 lease 响应 |
| `backend/app/api/inbound_worker.py` | 新增运行记录只读列表接口 |
| `backend/app/workers/trusted_inbound_orchestrator.py` | 新增运行记录、message job、租约 claim、stale 接管和 failed replay |
| `backend/tests/test_trusted_inbound_worker_api.py` | 新增 run record、fresh lock、stale reclaim、failed replay 测试 |

## 验证

已通过：

```bash
.venv/bin/pytest backend/tests/test_trusted_inbound_worker_api.py -q
```

结果：

```text
6 passed
```

## 当前边界

- 本阶段不代表真实企业微信、微信客服、公众号、抖音、小红书、淘宝、京东或拼多多已经真实接入。
- 本阶段不打开真实外发。
- 本阶段没有实现常驻 worker 进程。
- 本阶段没有实现 heartbeat、Prometheus 指标、告警和多容器压测。
- 本阶段仍是数据库租约第一片，不是 Redis/Celery/Kafka/云队列。

## 下一步

建议进入 P3-06C：

- 常驻 worker 启停方式
- heartbeat 字段或单独 heartbeat 表
- worker run 失败分级
- 入站 worker 监控指标
- 多实例 smoke 或小规模压测
- 企业微信公网 HTTPS 回调 smoke 的前置健康检查
