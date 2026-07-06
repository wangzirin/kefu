# P3-06C Worker Heartbeat 与受控常驻循环第一片

## 结论

P3-06C 已完成第一片：系统现在具备可落库的 worker 心跳、健康状态计算、可信入站 worker 的受控循环运行入口，以及两个 worker 实例连续运行不重复处理同一条可信入站消息的 smoke 测试。

这一片不是完整生产监控系统。它还没有接入 Prometheus、告警短信、Kubernetes HPA、systemd 进程守护或真实多容器压测；它解决的是“后台 worker 运行态能不能被系统看见、被接口读取、被测试复现”的基础问题。

## 已完成

- 新增 `worker_heartbeats` 表，按 `tenant_id + worker_type + worker_id` 唯一记录 worker 实例状态。
- 新增 `WorkerHeartbeat` 模型和 `0022_worker_heartbeats` 迁移。
- 新增 `GET /api/tenants/{tenant_id}/worker-heartbeats`，支持 `stale_after_seconds`、`limit`、`offset`。
- 新增 `worker_heartbeats` 服务层，统一处理心跳 upsert、健康状态计算和只读输出。
- 新增 `POST /api/tenants/{tenant_id}/trusted-inbound-worker-loop-runs`，用于受控循环运行可信入站 worker。
- 循环运行期间会写入 `starting`、`running`、`idle` 或 `failed` 状态。
- 循环完成后会记录 `last_run_record_id`、`last_run_mode`、`loops_completed` 和上次运行摘要。
- 外部写入仍强制保持关闭，适合本地 smoke 和试点部署前的后台链路验证。
- 前端总览阶段标识更新为 `P3-06C`。

## 健康状态定义

| 字段 | 含义 |
| --- | --- |
| `status` | worker 自己上报的运行状态，例如 `starting`、`running`、`idle`、`failed`。 |
| `health_status` | 系统根据 `status` 和 `last_heartbeat_at` 计算出的健康状态。 |
| `healthy` | worker 最近有心跳，且 `status` 不是 `failed`。 |
| `stale` | worker 心跳超过 `stale_after_seconds`，说明可能卡住、进程退出或调度中断。 |
| `failed` | worker 主动记录了失败状态，需要人工排查最后错误和相关 run record。 |

默认 `stale_after_seconds=120`。接口可临时传入更短阈值做 smoke。

## 接口

### 查看 worker 心跳

```http
GET /api/tenants/{tenant_id}/worker-heartbeats?stale_after_seconds=120&limit=100&offset=0
Authorization: Bearer <token>
```

返回示例：

```json
[
  {
    "id": 1,
    "tenant_id": 1,
    "worker_type": "trusted_inbound_orchestrator",
    "worker_id": "trusted-loop-worker-1",
    "status": "idle",
    "health_status": "healthy",
    "last_run_record_id": 12,
    "last_run_mode": "trusted_inbound_orchestrator",
    "last_error": "",
    "loops_completed": 3,
    "metadata_payload": {}
  }
]
```

### 触发可信入站 worker 受控循环

```http
POST /api/tenants/{tenant_id}/trusted-inbound-worker-loop-runs
Authorization: Bearer <token>
Content-Type: application/json

{
  "iterations": 1,
  "sleep_seconds": 0,
  "batch_size": 5,
  "rate_limit_per_minute": 60,
  "worker_id": "trusted-loop-worker-1",
  "lease_seconds": 30,
  "mode": "model_assisted",
  "risk_level": "medium",
  "knowledge_top_k": 3,
  "model_provider": "deterministic"
}
```

返回会包含本次循环总计、每轮 run record id、最后一次 worker run 摘要和最新 heartbeat。

## 为什么这一片必要

P3-06A 和 P3-06B 已经把出站队列、可信入站 worker 的幂等和 lease 补起来了，但那仍然只是“接口触发一次”的能力。真实部署后，后台 worker 会长期运行；如果没有心跳和运行态记录，排障时只能看日志，很难回答：

- worker 进程是否还活着。
- 哪个 worker_id 最近处理过消息。
- 上一次成功或失败对应哪条 run record。
- 多个 worker 是否重复 claim 同一条消息。
- worker 是失败、卡住，还是只是暂时没有待处理任务。

P3-06C 先把这些信息落库并开放只读接口，后续才能接告警、部署守护和前端运维面板。

## 已验证

```bash
.venv/bin/python -m pytest tests/test_worker_heartbeats_api.py -q
.venv/bin/python -m pytest tests/test_trusted_inbound_worker_api.py tests/test_channel_webhooks_api.py tests/test_p3_05e_wecom_official_sandbox_connector.py -q
.venv/bin/python -m pytest tests/test_outbox_delivery_queue_api.py tests/test_outbox_api.py -q
.venv/bin/alembic heads
```

验证结果：

- `tests/test_worker_heartbeats_api.py`：3 个测试通过。
- 可信入站、企业微信 sandbox、渠道 webhook 相邻测试：20 个测试通过。
- outbox 相邻测试：13 个测试通过。
- Alembic head：`0022_worker_heartbeats`。

## 尚未完成

- 常驻 worker 的真实进程入口，例如 supervisor、systemd、Docker command、RQ worker 或 Kubernetes worker deployment。
- Prometheus 指标、告警规则和告警通知渠道。
- 多容器并发压测。
- 前端运维页展示 worker 心跳。
- 企业微信公网 HTTPS 回调真实 smoke。
- 真实外发白名单测试。

## 下一步建议

下一步优先进入 P3-06D：把当前受控循环核心接入正式部署形态。最低可行版本可以先做 Docker Compose worker service、命令行 runner、健康检查脚本和本地多实例 smoke；如果企业微信公网 URL、Token、EncodingAESKey 和可信 IP 条件已经齐备，可以并行做企业微信公网 HTTPS 回调 smoke。
