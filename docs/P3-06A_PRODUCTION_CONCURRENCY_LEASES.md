# P3-06A 生产并发底座第一片：Outbox 队列租约与原子抢占

日期：2026-07-01

## 工程控制卡

| 项目 | 结论 |
| --- | --- |
| 阶段定位 | 把 outbox delivery queue 从单进程 skeleton 推进到具备最小生产并发保护的 DB 队列 |
| 当前完成 | job 租约 TTL、原子 claim、陈旧锁抢回、新鲜锁跳过、运行结果输出锁证据 |
| 不做事项 | 不接真实发送 API、不打开外部写入、不引入 Redis/Celery/BullMQ、不做多节点压测 |
| 生产边界 | 当前是 DB 队列并发安全第一片；真正高并发仍需要 Redis/消息队列、水平 worker、监控告警和压测 |

## 为什么先做这一片

标准运营版进入生产前，最危险的不是 UI 少一个按钮，而是多个 worker 同时跑时重复处理同一条待发送任务。当前系统已经有：

- `outbox_delivery_jobs`
- `locked_by`
- `locked_at`
- `attempts_count`
- `max_attempts`
- `retry_scheduled`
- `dead_letter`

但原先的候选查询只取 `queued` 和 `retry_scheduled`，处理时再把 job 改成 `locked`。这对单进程 dry-run 足够，对多 worker 不够稳。

P3-06A 第一片补的是队列并发的最小安全语义：

1. 新 worker 只能处理自己成功 claim 到的 job。
2. 新鲜锁不能被抢。
3. 陈旧锁可以被抢回。
4. 运行结果必须能解释哪些任务被跳过、哪些任务被抢回。

## 后端新增能力

### 请求参数

`OutboxDeliveryQueueRunCreate` 新增：

| 字段 | 默认 | 说明 |
| --- | --- | --- |
| `lease_seconds` | `60` | 判断 `locked` job 是否过期的租约秒数 |

### 原子 claim

新增 `_claim_delivery_job`：

- 使用带条件的 `UPDATE` 抢占任务。
- 条件包括：
  - job 属于当前租户；
  - job 是 `queued` 或 `retry_scheduled` 且已到 `next_run_at`；
  - 或 job 是 `locked`，但 `locked_at` 已早于租约过期 cutoff；
  - job id 必须匹配。
- 更新内容：
  - `status = locked`
  - `locked_by = worker_id`
  - `locked_at = now`
  - `updated_at = now`

实现细节：

- 使用 `execution_options(synchronize_session=False)`，避免 SQLite 测试环境中 Python 侧 datetime aware/naive 比较导致误判。
- 处理函数只处理已经 claim 成功的 job。

### 陈旧锁抢回

候选任务现在包含：

- 到期的 `queued`。
- 到期的 `retry_scheduled`。
- `locked` 但 `locked_at` 已超过 `lease_seconds` 的陈旧锁。

### 新鲜锁跳过

如果 job 是 `locked`，且 `locked_at` 仍在租约有效期内：

- 不处理。
- 不生成 attempt。
- 记录到 `skipped_job_ids`。

### 运行证据

`kill_switch` 中新增 `lease` 证据：

```json
{
  "worker_id": "frontend_delivery_queue_worker",
  "lease_seconds": 60,
  "stale_lock_cutoff": "...",
  "active_locked_skipped": 0,
  "atomic_claim": true
}
```

注意：字段暂放在 `kill_switch` 结构内，是为了不破坏现有前端和 API 响应结构。后续 P3-06B 可以把 worker run response 拆成更正式的 `runtime` 或 `concurrency` 字段。

## 当前验证

专项测试：

```bash
.venv/bin/pytest backend/tests/test_outbox_delivery_queue_api.py -q
```

结果：

- 5 个测试通过。
- 覆盖：
  - 重复运行不重复生成 attempt。
  - kill switch 阻断外部写入。
  - rate limit 保留未处理任务。
  - 新鲜 locked job 被跳过。
  - 陈旧 locked job 被抢回处理。
  - 失败重试后进入 dead letter。

## 仍未完成

- Redis / 专用消息队列。
- 多进程或多容器真实并发压测。
- worker 进程常驻运行器。
- 任务运行指标落表。
- worker heartbeat。
- dead letter 管理页面。
- outbox job 的批量重放。
- 可信入站 worker 的同等级租约化。
- 真实 sender provider 和回执 reconciliation。

## 下一步建议

继续 P3-06B：

1. 把可信入站 worker 也改成租约/claim 模式。
2. 增加 worker run 记录表，记录每次 worker 执行的扫描、处理、跳过、失败和耗时。
3. 前端 outbox 队列显示 lease、locked、dead letter 和重试原因。
4. 再决定是否引入 Redis 队列或 Postgres `FOR UPDATE SKIP LOCKED` 路径。
