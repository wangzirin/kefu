# P3-06D Worker 进程部署第一片

## 结论

P3-06D 已完成第一片：可信入站 worker 现在有可被 Docker Compose 启动的独立进程入口、Docker Compose worker service、`worker` profile、只读 healthcheck、环境变量模板和静态 readiness 检查。

这一步把 P3-06C 的受控 loop 核心接到了部署层，但仍不是完整高并发 SLA。它没有完成 Kubernetes/HPA、Prometheus 真实采集、短信/电话告警、多容器压测和真实客户生产部署。

真实外发仍关闭。worker 只把可信入站消息推进到 workflow / human review，不绕过 outbox、人审、官方 API、可信 IP、白名单和客户授权。

## 新增能力

| 能力 | 本阶段实现 |
| --- | --- |
| CLI worker service | `python -m app.workers.trusted_inbound_worker_service` |
| Compose service | `trusted-inbound-worker` |
| 启动 profile | `profiles: ["worker"]`，默认普通 compose up 不启动 |
| 心跳 healthcheck | `python -m app.workers.trusted_inbound_worker_service --healthcheck` |
| 外发安全 | Compose 和 pilot overlay 强制 `OUTBOX_EXTERNAL_WRITE_ENABLED: "false"` |
| 配置模板 | `.env.example` 新增 `TRUSTED_INBOUND_WORKER_*` |
| 静态验收 | `scripts/check_p3_06d_worker_deployment.py` |

## 启动方式

先确保已经完成：

1. 数据库迁移已经到 `0022_worker_heartbeats` 或更新版本。
2. 租户已经创建。
3. worker 使用的内部账号已经创建，并具备 `owner` 或 `admin` 角色。
4. 可信入站 webhook 已按官方 sandbox 方式验证，不使用个人号外挂、Hook、群控或模拟点击。

在客户环境的 `.env` 中配置：

```bash
TRUSTED_INBOUND_WORKER_TENANT_SLUG=customer-tenant-slug
TRUSTED_INBOUND_WORKER_USER_EMAIL=ops-worker@example.com
TRUSTED_INBOUND_WORKER_ID=trusted-inbound-worker-1
TRUSTED_INBOUND_WORKER_SLEEP_SECONDS=5
TRUSTED_INBOUND_WORKER_BATCH_SIZE=20
TRUSTED_INBOUND_WORKER_RATE_LIMIT_PER_MINUTE=60
TRUSTED_INBOUND_WORKER_LEASE_SECONDS=60
TRUSTED_INBOUND_WORKER_HEARTBEAT_STALE_AFTER_SECONDS=180
OUTBOX_EXTERNAL_WRITE_ENABLED=false
```

启动 worker profile：

```bash
docker compose \
  -f deploy/docker-compose.yml \
  -f deploy/docker-compose.pilot.yml \
  --profile worker \
  up -d trusted-inbound-worker
```

查看日志：

```bash
docker compose \
  -f deploy/docker-compose.yml \
  -f deploy/docker-compose.pilot.yml \
  logs -f trusted-inbound-worker
```

日志是 JSON 行，核心事件：

| event | 含义 |
| --- | --- |
| `trusted_inbound_worker_service_started` | worker 进程启动，已解析租户和 worker 用户 |
| `trusted_inbound_worker_service_cycle_completed` | 完成一个循环，包含 processed/succeeded/failed/run_record_ids |
| `trusted_inbound_worker_service_stopped` | 有限循环结束或进程退出 |
| `trusted_inbound_worker_service_error` | 配置、租户、用户、数据库或运行错误 |

## Healthcheck

Compose healthcheck 使用：

```bash
python -m app.workers.trusted_inbound_worker_service \
  --healthcheck \
  --worker-id "$TRUSTED_INBOUND_WORKER_ID" \
  --stale-after-seconds "$TRUSTED_INBOUND_WORKER_HEARTBEAT_STALE_AFTER_SECONDS"
```

返回 `0` 的条件：

- 租户存在且 active。
- worker 用户存在且 active。
- worker 用户有 `owner` 或 `admin` 角色。
- `worker_heartbeats` 中存在对应 `worker_type + worker_id`。
- `health_status == healthy`。

返回非 `0` 的常见原因：

- `.env` 未配置 `TRUSTED_INBOUND_WORKER_TENANT_SLUG` 或 `TRUSTED_INBOUND_WORKER_USER_EMAIL`。
- worker 用户不存在、停用或无 owner/admin 角色。
- worker 还没写入过 heartbeat。
- heartbeat 超过 `TRUSTED_INBOUND_WORKER_HEARTBEAT_STALE_AFTER_SECONDS`。
- worker 最近状态为 `failed`。

## 告警规则草案

本阶段只提供规则草案，不接入真实告警通道。正式告警可接入 Prometheus、云监控、Sentry、飞书/企业微信机器人或客户已有监控平台。

| 告警 | 触发条件 | 级别 | 处理方式 |
| --- | --- | --- | --- |
| Worker missing | `worker_heartbeats` 查不到指定 worker | ticket | 检查 profile 是否启动、租户/用户配置是否正确 |
| Worker stale | `health_status=stale` 持续 5 分钟 | page | 查看容器日志、数据库连接、最近 run record |
| Worker failed | `health_status=failed` 任意出现 | page | 查看 `last_error`、最近 run record 和相关 message job |
| Failed iteration spike | 10 分钟内 failed_iterations 增加 | ticket/page | 检查模型、知识库、数据库和消息格式 |
| Backlog growth | 可信入站 queued/failed job 持续增加 | page | 检查 worker 是否卡住、限流是否过低、下游是否失败 |

告警必须链接到本文件或客户环境 runbook，不能只发“worker unhealthy”。

## 验收

```bash
cd backend && .venv/bin/python -m pytest tests/test_p3_06d_worker_deployment.py -q
cd backend && .venv/bin/python -m pytest tests/test_worker_heartbeats_api.py tests/test_trusted_inbound_worker_api.py -q
cd backend && .venv/bin/python -m pytest -q
cd backend && .venv/bin/alembic heads
cd frontend && npm run build
python scripts/check_p3_06d_worker_deployment.py
```

## 仍未完成

- Kubernetes deployment / HPA。
- Prometheus 指标真实采集。
- 告警通知通道真实接入。
- 多容器并发压测。
- outbox 独立 worker service。
- 生产级死信队列和重放台。
- 企业微信公网 HTTPS 回调 smoke。
- 真实外发白名单测试。

## 下一步

下一步建议 P3-06E：把 worker heartbeat 展示到前端运维/设置页，并补一个只读“后台进程健康”面板；同时准备企业微信公网 HTTPS 回调 smoke 条件。若客户真实环境已经可用，再做部署级多实例 smoke 和告警通道接入。
