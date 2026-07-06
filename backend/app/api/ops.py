from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.tenants import require_tenant
from app.core.auth import CurrentPrincipal
from app.core.config import get_settings
from app.core.rbac import require_permission
from app.db.session import get_db
from app.models import (
    Channel,
    Conversation,
    DeliveryFailureReview,
    HumanReviewTask,
    KnowledgeEvaluationRun,
    KnowledgeGapItem,
    Message,
    OutboxDeliveryJob,
    OutboxDraft,
    SalesLead,
    SupportTicket,
    TrustedInboundMessageJob,
    TrustedInboundWorkerRunRecord,
    utc_now,
)
from app.schemas.ops import (
    OpsDashboardActionItemRead,
    OpsDashboardChannelRead,
    OpsDashboardDataSourceRead,
    OpsDashboardFilterRead,
    OpsDashboardFunnelStageRead,
    OpsDashboardQualityRead,
    OpsDashboardRead,
    OpsDashboardSourceWindowRead,
    OpsDashboardSummaryRead,
    OpsDashboardTrendBucketRead,
    OpsMetricRead,
    OpsMetricsDashboardRead,
    OpsMetricsSummary,
    OpsAlertRuleRead,
    OpsAlertRulesDashboardRead,
    OpsAlertRunbookRead,
    OpsRiskRead,
    WorkerHealthDashboardRead,
    WorkerHealthSummary,
)
from app.services.worker_heartbeats import list_worker_heartbeats

router = APIRouter(prefix="/api", tags=["ops"])


def _require_same_tenant(tenant_id: int, principal: CurrentPrincipal) -> None:
    if principal.tenant.id != tenant_id:
        raise HTTPException(status_code=404, detail="tenant not found")


def _as_aware_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _ops_dashboard_start(range_key: str, now: datetime) -> datetime:
    current = _as_aware_utc(now) or utc_now()
    if range_key == "today":
        return current.replace(hour=0, minute=0, second=0, microsecond=0)
    if range_key == "7d":
        return current - timedelta(days=7)
    return current - timedelta(days=30)


def _ops_dashboard_window_label(range_key: str) -> str:
    if range_key == "today":
        return "今日 00:00 至当前"
    if range_key == "7d":
        return "近 7 天滚动窗口"
    return "近 30 天滚动窗口"


def _in_interval(value: datetime | None, start: datetime, end: datetime) -> bool:
    current = _as_aware_utc(value)
    return bool(current and start <= current <= end)


def _bounded_ratio(numerator: int | float, denominator: int | float) -> float:
    if denominator <= 0:
        return 0.0
    return round(max(0.0, min(float(numerator) / float(denominator), 1.0)), 4)


def _is_open_status(status_value: str, *, closed_statuses: set[str] | None = None) -> bool:
    closed = closed_statuses or {"closed", "resolved", "done", "canceled", "cancelled", "archived"}
    return status_value not in closed


def _is_delivery_blocked(status_value: str) -> bool:
    return status_value in {"blocked", "dead_letter", "dead_lettered", "failed"}


def _bucket_key(value: datetime | None, *, range_key: str, start: datetime, end: datetime) -> str:
    current = _as_aware_utc(value)
    if current is None:
        return ""
    if range_key == "today":
        offset_hours = max(0, int((current - start).total_seconds() // 3600))
        bucket_start = min(offset_hours // 4 * 4, 20)
        return f"{bucket_start:02d}:00"
    if range_key == "7d":
        return current.strftime("%m-%d")
    span_seconds = max(1.0, (end - start).total_seconds())
    bucket_index = min(int(((current - start).total_seconds() / span_seconds) * 6), 5)
    bucket_start = start + timedelta(seconds=span_seconds / 6 * bucket_index)
    return bucket_start.strftime("%m-%d")


def _trend_buckets(range_key: str, *, start: datetime, end: datetime) -> list[OpsDashboardTrendBucketRead]:
    if range_key == "today":
        return [
            OpsDashboardTrendBucketRead(
                key=f"{hour:02d}:00",
                label=f"{hour:02d}:00",
                inbound=0,
                reviews=0,
                drafts=0,
                exceptions=0,
            )
            for hour in range(0, 24, 4)
        ]
    if range_key == "7d":
        days = [
            start + timedelta(days=offset)
            for offset in range(7)
        ]
        return [
            OpsDashboardTrendBucketRead(
                key=day.strftime("%m-%d"),
                label=day.strftime("%m-%d"),
                inbound=0,
                reviews=0,
                drafts=0,
                exceptions=0,
            )
            for day in days
        ]
    span_seconds = max(1.0, (end - start).total_seconds())
    buckets: list[OpsDashboardTrendBucketRead] = []
    for index in range(6):
        bucket_start = start + timedelta(seconds=span_seconds / 6 * index)
        buckets.append(
            OpsDashboardTrendBucketRead(
                key=bucket_start.strftime("%m-%d"),
                label=bucket_start.strftime("%m-%d"),
                inbound=0,
                reviews=0,
                drafts=0,
                exceptions=0,
            )
        )
    return buckets


def _build_worker_risks(
    *,
    heartbeats: list,
    recent_runs: list[TrustedInboundWorkerRunRecord],
    external_write_enabled: bool,
) -> list[OpsRiskRead]:
    risks: list[OpsRiskRead] = []
    if not heartbeats:
        risks.append(
            OpsRiskRead(
                code="no_worker_heartbeat",
                severity="warning",
                title="没有后台进程心跳",
                detail="当前租户还没有任何 worker heartbeat，说明后台进程尚未运行，或还没有写入心跳。",
                next_action="先确认 Docker Compose worker profile 是否已启动，并检查 TRUSTED_INBOUND_WORKER_* 配置。",
            )
        )
    for item in heartbeats:
        if item.health_status == "failed":
            risks.append(
                OpsRiskRead(
                    code="worker_failed",
                    severity="critical",
                    title=f"{item.worker_id} 处于失败状态",
                    detail=item.last_error or "worker heartbeat 标记为 failed，但没有写入具体错误。",
                    next_action="查看 worker 容器日志、最近运行记录和失败任务，修复后重启 worker。",
                )
            )
        elif item.health_status == "stale":
            risks.append(
                OpsRiskRead(
                    code="worker_stale",
                    severity="warning",
                    title=f"{item.worker_id} 心跳超时",
                    detail="该 worker 的最近心跳已超过 stale 阈值，可能已经停止、卡住或网络不可达。",
                    next_action="检查 worker 进程是否仍在运行，必要时重启 worker 并观察新心跳。",
                )
            )
    failed_recent_runs = [run for run in recent_runs if run.status == "failed" or run.failed > 0]
    if failed_recent_runs:
        risks.append(
            OpsRiskRead(
                code="recent_worker_run_failed",
                severity="warning",
                title="最近 worker 运行出现失败",
                detail=f"最近 {len(failed_recent_runs)} 条运行记录包含失败项，需要复盘对应任务。",
                next_action="打开最近运行记录，按 run id 排查失败任务、错误信息和知识/模型/人审状态。",
            )
        )
    if external_write_enabled:
        risks.append(
            OpsRiskRead(
                code="external_write_enabled",
                severity="critical",
                title="真实外发开关已开启",
                detail="当前环境允许真实平台外发，试点或本地演示环境不应默认开启。",
                next_action="确认是否已获得正式授权；没有授权时立即关闭真实外发开关。",
            )
        )
    return risks


def _ops_alert_rule(
    *,
    code: str,
    name: str,
    category: str,
    severity: str,
    response_type: str,
    firing: bool,
    signal: str,
    condition: str,
    threshold: str,
    duration: str,
    current_value: str,
    ok_reason: str,
    firing_reason: str,
    runbook_summary: str,
    first_checks: list[str],
    escalation: str,
    suppress_when: str,
) -> OpsAlertRuleRead:
    return OpsAlertRuleRead(
        code=code,
        name=name,
        category=category,
        severity=severity,
        response_type=response_type,
        status="firing" if firing else "ok",
        signal=signal,
        condition=condition,
        threshold=threshold,
        duration=duration,
        current_value=current_value,
        reason=firing_reason if firing else ok_reason,
        runbook=OpsAlertRunbookRead(
            summary=runbook_summary,
            first_checks=first_checks,
            escalation=escalation,
            suppress_when=suppress_when,
        ),
    )


def _build_ops_alert_rules(
    *,
    heartbeats: list,
    recent_runs: list[TrustedInboundWorkerRunRecord],
    stale_after_seconds: int,
    trusted_inbound_worker_enabled: bool,
    trusted_inbound_worker_tenant_slug: str,
    trusted_inbound_worker_user_email: str,
    external_write_enabled: bool,
) -> list[OpsAlertRuleRead]:
    stale_worker_ids = [item.worker_id for item in heartbeats if item.health_status == "stale"]
    failed_worker_ids = [item.worker_id for item in heartbeats if item.health_status == "failed"]
    healthy_worker_ids = [item.worker_id for item in heartbeats if item.health_status == "healthy"]
    failed_recent_runs = [
        run
        for run in recent_runs
        if run.status == "failed" or run.failed > 0
    ]
    runs_with_external_write = [run for run in recent_runs if run.external_write]
    rate_limited_runs = [run for run in recent_runs[:5] if run.rate_limited > 0]
    saturated_runs = [
        run
        for run in recent_runs[:5]
        if run.rate_limited > 0 and run.rate_limited >= max(run.processed, 1)
    ]
    config_missing = trusted_inbound_worker_enabled and (
        not trusted_inbound_worker_tenant_slug or not trusted_inbound_worker_user_email
    )
    processing_unavailable = trusted_inbound_worker_enabled and (
        not heartbeats or not healthy_worker_ids
    )
    rules = [
        _ops_alert_rule(
            code="trusted_inbound_processing_unavailable",
            name="可信入站处理不可用",
            category="worker",
            severity="critical",
            response_type="page",
            firing=processing_unavailable,
            signal="worker_heartbeats.summary",
            condition="worker enabled AND healthy_workers == 0",
            threshold="0 healthy worker",
            duration="连续 2 个评估窗口",
            current_value=f"healthy={len(healthy_worker_ids)} total={len(heartbeats)}",
            ok_reason="可信入站 worker 未启用，或至少有一个 healthy worker。",
            firing_reason="可信入站 worker 已启用，但当前没有 healthy worker，入站持续处理不可用。",
            runbook_summary="先恢复至少一个 healthy worker，再扩大真实入站试点。",
            first_checks=[
                "查看 worker heartbeat 是否为空、stale 或 failed。",
                "检查 worker 配置、容器状态和最近运行记录。",
                "恢复后用测试租户发送一条可信入站消息，确认进入人审。"
            ],
            escalation="影响真实入站处理时立即升级给后端负责人和交付负责人。",
            suppress_when="本环境未启用可信入站 worker，或处于计划维护窗口。",
        ),
        _ops_alert_rule(
            code="worker_config_incomplete_when_enabled",
            name="worker 启用但配置不完整",
            category="configuration",
            severity="warning",
            response_type="ticket",
            firing=config_missing,
            signal="TRUSTED_INBOUND_WORKER_*",
            condition="enabled == true AND tenant/user empty",
            threshold="tenant slug and user email required",
            duration="部署检查时",
            current_value=(
                f"tenant={'set' if trusted_inbound_worker_tenant_slug else 'empty'} "
                f"user={'set' if trusted_inbound_worker_user_email else 'empty'}"
            ),
            ok_reason="worker 启用开关关闭，或租户和用户配置已填写。",
            firing_reason="可信入站 worker 已启用，但缺少租户标识或管理员用户邮箱。",
            runbook_summary="补齐 worker principal 配置，确保 worker 以明确租户和 owner/admin 身份运行。",
            first_checks=[
                "检查 TRUSTED_INBOUND_WORKER_TENANT_SLUG 是否为空。",
                "检查 TRUSTED_INBOUND_WORKER_USER_EMAIL 是否为空。",
                "确认该用户为 active 且具备 owner/admin 权限。"
            ],
            escalation="上线前仍缺配置时升级给实施负责人。",
            suppress_when="本地演示或客户明确不启用后台 worker。",
        ),
        _ops_alert_rule(
            code="worker_heartbeat_missing",
            name="后台进程无心跳",
            category="worker",
            severity="warning",
            response_type="ticket",
            firing=not heartbeats,
            signal="worker_heartbeats.count",
            condition="count == 0",
            threshold="0",
            duration="持续 2 分钟",
            current_value=str(len(heartbeats)),
            ok_reason="当前租户已有 worker heartbeat。",
            firing_reason="当前租户没有任何 worker heartbeat，后台进程可能尚未启动或未写入心跳。",
            runbook_summary="确认后台 worker 是否已经按部署文档启动，并能写入 heartbeat。",
            first_checks=[
                "检查 Docker Compose worker profile 是否已启动。",
                "检查 TRUSTED_INBOUND_WORKER_TENANT_SLUG 和 TRUSTED_INBOUND_WORKER_USER_EMAIL 是否配置。",
                "查看 worker 容器日志，确认没有启动失败或权限错误。",
            ],
            escalation="如果 10 分钟内仍无心跳，升级给实施/后端负责人排查部署配置。",
            suppress_when="客户尚未启用任何后台 worker，且上线清单明确标记为不启用 worker。",
        ),
        _ops_alert_rule(
            code="trusted_inbound_worker_stale",
            name="可信入站 worker 心跳超时",
            category="worker",
            severity="warning",
            response_type="ticket",
            firing=bool(stale_worker_ids),
            signal="worker_heartbeats.health_status",
            condition="health_status == stale",
            threshold=f">{stale_after_seconds}s",
            duration="连续 1 个采样窗口",
            current_value=", ".join(stale_worker_ids) if stale_worker_ids else "0",
            ok_reason="当前没有 stale worker。",
            firing_reason="至少一个可信入站 worker 心跳超过 stale 阈值。",
            runbook_summary="确认 worker 是否卡住、退出或网络不可达。",
            first_checks=[
                "查看对应 worker_id 的最后心跳时间和 last_error。",
                "检查容器状态、CPU/内存和最近日志。",
                "必要时重启 worker，并观察下一次 heartbeat 是否恢复。",
            ],
            escalation="如果重启后 5 分钟内仍 stale，升级给后端负责人排查租约或数据库连接。",
            suppress_when="仅在计划维护窗口内、且已经暂停入站处理时临时静默。",
        ),
        _ops_alert_rule(
            code="trusted_inbound_worker_failed",
            name="可信入站 worker 失败",
            category="worker",
            severity="critical",
            response_type="page",
            firing=bool(failed_worker_ids),
            signal="worker_heartbeats.status",
            condition="health_status == failed",
            threshold=">=1 worker",
            duration="立即",
            current_value=", ".join(failed_worker_ids) if failed_worker_ids else "0",
            ok_reason="当前没有 failed worker。",
            firing_reason="至少一个可信入站 worker 处于 failed 状态。",
            runbook_summary="先确认失败原因，再决定重启、回放或暂停入站处理。",
            first_checks=[
                "查看 failed worker 的 last_error 和最近 trusted_inbound_worker_runs。",
                "确认失败是否来自模型、知识库、人审创建、数据库连接或配置错误。",
                "修复后先做白名单/测试租户 smoke，再恢复正式处理。",
            ],
            escalation="影响真实入站处理时立即升级给后端负责人和项目交付负责人。",
            suppress_when="仅在测试环境手动注入失败夹具时静默。",
        ),
        _ops_alert_rule(
            code="trusted_inbound_recent_run_failed",
            name="最近入站处理运行失败",
            category="worker_run",
            severity="warning",
            response_type="ticket",
            firing=bool(failed_recent_runs),
            signal="trusted_inbound_worker_runs.failed",
            condition="status == failed OR failed > 0",
            threshold=">=1 recent run",
            duration="最近运行窗口",
            current_value=str(len(failed_recent_runs)),
            ok_reason="最近运行记录没有失败项。",
            firing_reason="最近可信入站 worker 运行记录包含失败，需要复盘对应 run。",
            runbook_summary="按 run id 查失败任务，确认是否需要重放、补知识或转人工处理。",
            first_checks=[
                "打开最近运行记录，找到 status=failed 或 failed>0 的 run。",
                "查看 error_message、request_payload 和 result_payload 的脱敏字段。",
                "确认失败消息是否已进入 failed job，可按受控 worker 入口重放。",
            ],
            escalation="同一原因连续 3 次失败时升级给后端负责人，暂停扩大试点范围。",
            suppress_when="已确认是测试夹具或人为中断，且没有影响正式客户消息。",
        ),
        _ops_alert_rule(
            code="external_write_boundary_breach",
            name="真实外发边界风险",
            category="safety",
            severity="critical",
            response_type="page",
            firing=external_write_enabled or bool(runs_with_external_write),
            signal="真实外发开关 / 最近入站运行外部写入记录",
            condition="真实外发开关已开启，或最近运行记录显示发生外部写入",
            threshold="获得正式授权前必须关闭",
            duration="立即",
            current_value=(
                f"config={'enabled' if external_write_enabled else 'disabled'} "
                f"runs_with_write={len(runs_with_external_write)}"
            ),
            ok_reason="真实外发开关关闭。",
            firing_reason="当前环境存在真实外发配置或最近运行记录显示外部写入，需要立即确认授权边界。",
            runbook_summary="先核对授权和白名单，再确认是否允许继续真实发送。",
            first_checks=[
                "确认客户书面授权、测试白名单和平台官方 API 条件。",
                "确认发送队列、人工门禁、回执匹配和失败复盘已开启。",
                "如果不是正式测试窗口，立即关闭真实外发开关。",
            ],
            escalation="未授权开启时立即升级给项目负责人并关闭外发开关。",
            suppress_when="正式白名单测试窗口内，并已有授权记录和回滚方案。",
        ),
        _ops_alert_rule(
            code="trusted_inbound_rate_limit_saturation",
            name="可信入站限流饱和",
            category="worker_run",
            severity="warning",
            response_type="ticket",
            firing=len(rate_limited_runs) >= 3 or bool(saturated_runs),
            signal="trusted_inbound_worker_runs.rate_limited",
            condition="3/5 recent runs rate_limited > 0 OR rate_limited >= processed",
            threshold=">=3 recent runs or single saturated run",
            duration="最近 5 次运行窗口",
            current_value=f"rate_limited_runs={len(rate_limited_runs)} saturated_runs={len(saturated_runs)}",
            ok_reason="最近运行没有明显限流饱和。",
            firing_reason="最近可信入站 worker 运行出现连续限流或单次限流量超过处理量。",
            runbook_summary="先确认限流是否来自模型、入站 worker 配置或渠道平台，再调整批量和限速。",
            first_checks=[
                "查看最近 5 次 run 的 rate_limited、processed 和 batch_size。",
                "确认 TRUSTED_INBOUND_WORKER_RATE_LIMIT_PER_MINUTE 是否过低。",
                "如果限流来自模型或平台，降低批大小并增加人工审核缓冲。"
            ],
            escalation="连续出现限流且影响客户响应时升级给运维和模型路由负责人。",
            suppress_when="压测或演示环境主动降低限流阈值时临时静默。",
        ),
        _ops_alert_rule(
            code="trusted_inbound_worker_disabled",
            name="可信入站 worker 未启用",
            category="worker",
            severity="warning",
            response_type="ticket",
            firing=not trusted_inbound_worker_enabled,
            signal="TRUSTED_INBOUND_WORKER_ENABLED",
            condition="enabled == false",
            threshold="false",
            duration="部署检查时",
            current_value="enabled" if trusted_inbound_worker_enabled else "disabled",
            ok_reason="可信入站 worker 启用开关已打开。",
            firing_reason="可信入站 worker 启用开关关闭，真实入站消息不会由后台 worker 持续处理。",
            runbook_summary="确认当前环境是否应该启用可信入站 worker。",
            first_checks=[
                "检查客户部署清单是否要求启动可信入站 worker。",
                "如需启用，配置 TRUSTED_INBOUND_WORKER_ENABLED=true 并启动 worker profile。",
                "启用后观察 heartbeat 和最近运行记录。",
            ],
            escalation="上线清单要求启用但配置仍关闭时，升级给实施负责人。",
            suppress_when="本地演示、离线验收或客户明确不启用后台 worker。",
        ),
    ]
    return rules


def _count_by_status(db: Session, *, model: type, tenant_id: int) -> dict[str, int]:
    rows = db.execute(
        select(model.status, func.count())
        .where(model.tenant_id == tenant_id)
        .group_by(model.status)
    ).all()
    return {str(status): int(count) for status, count in rows}


def _ops_metric(
    *,
    name: str,
    metric_type: str,
    value: float | int,
    unit: str,
    labels: dict[str, str],
    description: str,
    source: str,
    status: str = "ok",
) -> OpsMetricRead:
    return OpsMetricRead(
        name=name,
        metric_type=metric_type,
        value=float(value),
        unit=unit,
        labels=labels,
        description=description,
        source=source,
        status=status,
    )


def _prometheus_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace("\n", "\\n").replace('"', '\\"')


def _format_prometheus_value(value: float) -> str:
    if value.is_integer():
        return str(int(value))
    return f"{value:.6f}".rstrip("0").rstrip(".")


def _build_prometheus_text(metrics: list[OpsMetricRead]) -> str:
    emitted_headers: set[str] = set()
    lines: list[str] = []
    for metric in metrics:
        if metric.name not in emitted_headers:
            lines.append(f"# HELP {metric.name} {_prometheus_escape(metric.description)}")
            lines.append(f"# TYPE {metric.name} {metric.metric_type}")
            emitted_headers.add(metric.name)
        label_text = ",".join(
            f'{key}="{_prometheus_escape(value)}"'
            for key, value in sorted(metric.labels.items())
        )
        suffix = f"{{{label_text}}}" if label_text else ""
        lines.append(f"{metric.name}{suffix} {_format_prometheus_value(metric.value)}")
    return "\n".join(lines) + "\n"


def _build_ops_metrics(
    *,
    tenant_id: int,
    heartbeats: list,
    recent_runs: list[TrustedInboundWorkerRunRecord],
    rules: list[OpsAlertRuleRead],
    outbox_job_counts: dict[str, int],
    trusted_message_job_counts: dict[str, int],
    delivery_failure_review_counts: dict[str, int],
    external_write_enabled: bool,
    trusted_inbound_worker_enabled: bool,
) -> tuple[OpsMetricsSummary, list[OpsMetricRead]]:
    tenant_labels = {"tenant_id": str(tenant_id)}
    healthy_workers = sum(1 for item in heartbeats if item.health_status == "healthy")
    stale_workers = sum(1 for item in heartbeats if item.health_status == "stale")
    failed_workers = sum(1 for item in heartbeats if item.health_status == "failed")
    failed_recent_runs = [run for run in recent_runs if run.status == "failed" or run.failed > 0]
    rate_limited_recent_runs = sum(run.rate_limited for run in recent_runs)
    firing_rules = [rule for rule in rules if rule.status == "firing"]
    page_rules = [rule for rule in firing_rules if rule.response_type == "page"]
    ticket_rules = [rule for rule in firing_rules if rule.response_type == "ticket"]
    outbox_backlog = sum(outbox_job_counts.get(status, 0) for status in ("queued", "retry_scheduled", "locked"))
    trusted_inbound_backlog = sum(trusted_message_job_counts.get(status, 0) for status in ("queued", "locked"))
    queue_backlog = outbox_backlog + trusted_inbound_backlog
    dead_letter_jobs = outbox_job_counts.get("dead_letter", 0)
    open_failure_reviews = delivery_failure_review_counts.get("open", 0)

    metrics = [
        _ops_metric(
            name="wanfa_worker_total",
            metric_type="gauge",
            value=len(heartbeats),
            unit="workers",
            labels=tenant_labels,
            description="Total registered worker heartbeat rows for the tenant.",
            source="worker_heartbeats",
        ),
        _ops_metric(
            name="wanfa_worker_healthy",
            metric_type="gauge",
            value=healthy_workers,
            unit="workers",
            labels=tenant_labels,
            description="Workers whose heartbeat is inside the stale threshold.",
            source="worker_heartbeats.health_status",
        ),
        _ops_metric(
            name="wanfa_worker_stale",
            metric_type="gauge",
            value=stale_workers,
            unit="workers",
            labels=tenant_labels,
            description="Workers whose heartbeat exceeded the stale threshold.",
            source="worker_heartbeats.health_status",
            status="warning" if stale_workers else "ok",
        ),
        _ops_metric(
            name="wanfa_worker_failed",
            metric_type="gauge",
            value=failed_workers,
            unit="workers",
            labels=tenant_labels,
            description="Workers currently marked failed.",
            source="worker_heartbeats.health_status",
            status="critical" if failed_workers else "ok",
        ),
        _ops_metric(
            name="wanfa_worker_loops_completed_total",
            metric_type="counter",
            value=sum(item.loops_completed for item in heartbeats),
            unit="loops",
            labels=tenant_labels,
            description="Total worker loop counter reported by heartbeats.",
            source="worker_heartbeats.loops_completed",
        ),
        _ops_metric(
            name="wanfa_ops_alert_rules_firing",
            metric_type="gauge",
            value=len(firing_rules),
            unit="rules",
            labels=tenant_labels,
            description="Currently firing operations alert rules.",
            source="ops.alert_rules",
            status="warning" if firing_rules else "ok",
        ),
        _ops_metric(
            name="wanfa_ops_alert_rules_page",
            metric_type="gauge",
            value=len(page_rules),
            unit="rules",
            labels=tenant_labels,
            description="Currently firing page-level alert rules.",
            source="ops.alert_rules",
            status="critical" if page_rules else "ok",
        ),
        _ops_metric(
            name="wanfa_ops_alert_rules_ticket",
            metric_type="gauge",
            value=len(ticket_rules),
            unit="rules",
            labels=tenant_labels,
            description="Currently firing ticket-level alert rules.",
            source="ops.alert_rules",
            status="warning" if ticket_rules else "ok",
        ),
        _ops_metric(
            name="wanfa_trusted_inbound_runs_failed_recent",
            metric_type="gauge",
            value=len(failed_recent_runs),
            unit="runs",
            labels=tenant_labels,
            description="Recent trusted inbound worker runs with failed status or failed items.",
            source="trusted_inbound_worker_runs",
            status="warning" if failed_recent_runs else "ok",
        ),
        _ops_metric(
            name="wanfa_trusted_inbound_runs_rate_limited_recent",
            metric_type="gauge",
            value=rate_limited_recent_runs,
            unit="items",
            labels=tenant_labels,
            description="Rate-limited items in the recent trusted inbound worker run window.",
            source="trusted_inbound_worker_runs.rate_limited",
            status="warning" if rate_limited_recent_runs else "ok",
        ),
        _ops_metric(
            name="wanfa_queue_backlog_total",
            metric_type="gauge",
            value=queue_backlog,
            unit="jobs",
            labels=tenant_labels,
            description="Total queued, retry-scheduled, or locked jobs across outbound and trusted inbound queues.",
            source="outbox_delivery_jobs + trusted_inbound_message_jobs",
            status="warning" if queue_backlog else "ok",
        ),
        _ops_metric(
            name="wanfa_outbox_dead_letter_jobs",
            metric_type="gauge",
            value=dead_letter_jobs,
            unit="jobs",
            labels=tenant_labels,
            description="Outbound delivery jobs that reached dead-letter state.",
            source="outbox_delivery_jobs.status",
            status="critical" if dead_letter_jobs else "ok",
        ),
        _ops_metric(
            name="wanfa_delivery_failure_reviews_open",
            metric_type="gauge",
            value=open_failure_reviews,
            unit="reviews",
            labels=tenant_labels,
            description="Open delivery failure reviews requiring human action.",
            source="delivery_failure_reviews.status",
            status="warning" if open_failure_reviews else "ok",
        ),
        _ops_metric(
            name="wanfa_external_write_enabled",
            metric_type="gauge",
            value=1 if external_write_enabled else 0,
            unit="boolean",
            labels=tenant_labels,
            description="Whether the global external platform write switch is enabled.",
            source="OUTBOX_EXTERNAL_WRITE_ENABLED",
            status="critical" if external_write_enabled else "ok",
        ),
        _ops_metric(
            name="wanfa_trusted_inbound_worker_enabled",
            metric_type="gauge",
            value=1 if trusted_inbound_worker_enabled else 0,
            unit="boolean",
            labels=tenant_labels,
            description="Whether the trusted inbound worker is enabled in configuration.",
            source="TRUSTED_INBOUND_WORKER_ENABLED",
            status="ok" if trusted_inbound_worker_enabled else "warning",
        ),
    ]

    for status in sorted(set(outbox_job_counts) | {"queued", "retry_scheduled", "locked", "dead_letter", "blocked"}):
        value = outbox_job_counts.get(status, 0)
        metrics.append(
            _ops_metric(
                name="wanfa_outbox_delivery_jobs",
                metric_type="gauge",
                value=value,
                unit="jobs",
                labels={**tenant_labels, "status": status},
                description="Outbound delivery job count by bounded status label.",
                source="outbox_delivery_jobs.status",
                status="critical" if status == "dead_letter" and value else "warning" if status in {"queued", "retry_scheduled", "locked", "blocked"} and value else "ok",
            )
        )
    for status in sorted(set(trusted_message_job_counts) | {"queued", "locked", "failed", "succeeded"}):
        value = trusted_message_job_counts.get(status, 0)
        metrics.append(
            _ops_metric(
                name="wanfa_trusted_inbound_message_jobs",
                metric_type="gauge",
                value=value,
                unit="jobs",
                labels={**tenant_labels, "status": status},
                description="Trusted inbound message job count by bounded status label.",
                source="trusted_inbound_message_jobs.status",
                status="warning" if status in {"queued", "locked", "failed"} and value else "ok",
            )
        )
    for status in sorted(set(delivery_failure_review_counts) | {"open", "resolved"}):
        value = delivery_failure_review_counts.get(status, 0)
        metrics.append(
            _ops_metric(
                name="wanfa_delivery_failure_reviews",
                metric_type="gauge",
                value=value,
                unit="reviews",
                labels={**tenant_labels, "status": status},
                description="Delivery failure review count by bounded status label.",
                source="delivery_failure_reviews.status",
                status="warning" if status == "open" and value else "ok",
            )
        )

    summary = OpsMetricsSummary(
        total_metrics=len(metrics),
        firing_alerts=len(firing_rules),
        page_alerts=len(page_rules),
        queue_backlog=queue_backlog,
        dead_letter_jobs=dead_letter_jobs,
        failed_worker_runs=len(failed_recent_runs),
        open_failure_reviews=open_failure_reviews,
        external_write_enabled=external_write_enabled,
        ready_for_prometheus_scrape=True,
    )
    return summary, metrics


def _filter_by_channel(items: list, channel_id: int | None) -> list:
    if channel_id is None:
        return items
    return [item for item in items if getattr(item, "channel_id", None) == channel_id]


def _filter_reviews_by_channel(
    reviews: list[HumanReviewTask],
    *,
    conversation_by_id: dict[int, Conversation],
    channel_id: int | None,
) -> list[HumanReviewTask]:
    if channel_id is None:
        return reviews
    return [
        item
        for item in reviews
        if conversation_by_id.get(item.conversation_id)
        and conversation_by_id[item.conversation_id].channel_id == channel_id
    ]


def _channel_counts(
    channels: list[Channel],
    *,
    conversations: list[Conversation],
    reviews: list[HumanReviewTask],
    drafts: list[OutboxDraft],
    failure_reviews: list[DeliveryFailureReview],
    blocked_jobs: list[OutboxDeliveryJob],
    conversation_by_id: dict[int, Conversation],
) -> list[OpsDashboardChannelRead]:
    rows: list[OpsDashboardChannelRead] = []
    for channel in channels:
        channel_reviews = [
            item
            for item in reviews
            if conversation_by_id.get(item.conversation_id)
            and conversation_by_id[item.conversation_id].channel_id == channel.id
        ]
        channel_pending_drafts = [
            item
            for item in drafts
            if item.channel_id == channel.id and item.status == "pending_confirmation"
        ]
        channel_ready_drafts = [
            item
            for item in drafts
            if item.channel_id == channel.id and item.status == "ready_to_send"
        ]
        channel_failure_reviews = [
            item
            for item in failure_reviews
            if item.channel_id == channel.id and _is_open_status(item.status)
        ]
        channel_blocked_jobs = [
            item
            for item in blocked_jobs
            if item.channel_id == channel.id
        ]
        inbound_conversations = sum(1 for item in conversations if item.channel_id == channel.id)
        workload = len(channel_reviews) + len(channel_pending_drafts) + len(channel_ready_drafts)
        exception_count = len(channel_failure_reviews) + len(channel_blocked_jobs)
        if inbound_conversations == 0 and workload == 0 and exception_count == 0:
            continue
        rows.append(
            OpsDashboardChannelRead(
                channel_id=channel.id,
                channel_name=channel.name,
                channel_type=channel.type,
                inbound_conversations=inbound_conversations,
                open_reviews=len(channel_reviews),
                pending_outbox_drafts=len(channel_pending_drafts),
                ready_outbox_drafts=len(channel_ready_drafts),
                open_failure_reviews=len(channel_failure_reviews),
                blocked_delivery_jobs=len(channel_blocked_jobs),
                workload=workload,
                exception_count=exception_count,
            )
        )
    return sorted(rows, key=lambda item: (item.workload + item.exception_count, item.inbound_conversations), reverse=True)


@router.get(
    "/tenants/{tenant_id}/ops/dashboard",
    response_model=OpsDashboardRead,
)
def get_ops_dashboard(
    tenant_id: int,
    range_key: str = Query(default="today", alias="range", pattern="^(today|7d|30d)$"),
    channel_id: int | None = Query(default=None),
    principal: CurrentPrincipal = Depends(require_permission("dashboard.read")),
    db: Session = Depends(get_db),
) -> OpsDashboardRead:
    require_tenant(db, tenant_id)
    _require_same_tenant(tenant_id, principal)

    now = utc_now()
    interval_start = _ops_dashboard_start(range_key, now)
    interval_end = now
    channels = list(
        db.scalars(
            select(Channel)
            .where(Channel.tenant_id == tenant_id)
            .order_by(Channel.id.asc())
        ).all()
    )
    if channel_id is not None and all(channel.id != channel_id for channel in channels):
        raise HTTPException(status_code=404, detail="channel not found")
    visible_channels = [channel for channel in channels if channel_id is None or channel.id == channel_id]
    selected_channel = visible_channels[0] if channel_id is not None and visible_channels else None

    all_conversations = list(
        db.scalars(
            select(Conversation)
            .where(Conversation.tenant_id == tenant_id)
            .order_by(Conversation.created_at.desc(), Conversation.id.desc())
        ).all()
    )
    conversation_by_id = {item.id: item for item in all_conversations}
    scoped_conversations = [
        item
        for item in all_conversations
        if _in_interval(item.created_at, interval_start, interval_end)
        and (channel_id is None or item.channel_id == channel_id)
    ]
    conversation_ids = [item.id for item in all_conversations]
    if conversation_ids:
        all_messages = list(
            db.scalars(
                select(Message)
                .where(Message.conversation_id.in_(conversation_ids))
                .order_by(Message.created_at.desc(), Message.id.desc())
            ).all()
        )
    else:
        all_messages = []
    scoped_inbound_messages = [
        item
        for item in all_messages
        if item.direction == "inbound"
        and _in_interval(item.created_at, interval_start, interval_end)
        and conversation_by_id.get(item.conversation_id)
        and (channel_id is None or conversation_by_id[item.conversation_id].channel_id == channel_id)
    ]

    reviews_in_range = [
        item
        for item in db.scalars(
            select(HumanReviewTask)
            .where(HumanReviewTask.tenant_id == tenant_id)
            .order_by(HumanReviewTask.created_at.desc(), HumanReviewTask.id.desc())
        ).all()
        if _in_interval(item.created_at, interval_start, interval_end)
    ]
    open_reviews = _filter_reviews_by_channel(
        [item for item in reviews_in_range if _is_open_status(item.status)],
        conversation_by_id=conversation_by_id,
        channel_id=channel_id,
    )
    high_risk_reviews = [
        item
        for item in open_reviews
        if item.risk_level in {"high", "critical"}
    ]

    drafts_in_range = _filter_by_channel(
        [
            item
            for item in db.scalars(
                select(OutboxDraft)
                .where(OutboxDraft.tenant_id == tenant_id)
                .order_by(OutboxDraft.created_at.desc(), OutboxDraft.id.desc())
            ).all()
            if _in_interval(item.created_at, interval_start, interval_end)
        ],
        channel_id,
    )
    pending_drafts = [item for item in drafts_in_range if item.status == "pending_confirmation"]
    ready_drafts = [item for item in drafts_in_range if item.status == "ready_to_send"]

    failure_reviews_in_range = _filter_by_channel(
        [
            item
            for item in db.scalars(
                select(DeliveryFailureReview)
                .where(DeliveryFailureReview.tenant_id == tenant_id)
                .order_by(DeliveryFailureReview.created_at.desc(), DeliveryFailureReview.id.desc())
            ).all()
            if _in_interval(item.created_at, interval_start, interval_end)
        ],
        channel_id,
    )
    open_failure_reviews = [
        item
        for item in failure_reviews_in_range
        if _is_open_status(item.status)
    ]
    blocked_jobs = _filter_by_channel(
        [
            item
            for item in db.scalars(
                select(OutboxDeliveryJob)
                .where(OutboxDeliveryJob.tenant_id == tenant_id)
                .order_by(OutboxDeliveryJob.created_at.desc(), OutboxDeliveryJob.id.desc())
            ).all()
            if _in_interval(item.created_at, interval_start, interval_end)
            and _is_delivery_blocked(item.status)
        ],
        channel_id,
    )
    open_knowledge_gaps = [
        item
        for item in db.scalars(
            select(KnowledgeGapItem)
            .where(KnowledgeGapItem.tenant_id == tenant_id)
            .order_by(KnowledgeGapItem.created_at.desc(), KnowledgeGapItem.id.desc())
        ).all()
        if channel_id is None
        and _in_interval(item.created_at, interval_start, interval_end)
        and _is_open_status(item.status)
    ]
    open_tickets = _filter_by_channel(
        [
            item
            for item in db.scalars(
                select(SupportTicket)
                .where(SupportTicket.tenant_id == tenant_id)
                .order_by(SupportTicket.created_at.desc(), SupportTicket.id.desc())
            ).all()
            if _in_interval(item.created_at, interval_start, interval_end)
            and _is_open_status(item.status)
        ],
        channel_id,
    )
    open_leads = _filter_by_channel(
        [
            item
            for item in db.scalars(
                select(SalesLead)
                .where(SalesLead.tenant_id == tenant_id)
                .order_by(SalesLead.created_at.desc(), SalesLead.id.desc())
            ).all()
            if _in_interval(item.created_at, interval_start, interval_end)
            and _is_open_status(item.stage, closed_statuses={"closed", "won", "lost", "resolved", "archived"})
        ],
        channel_id,
    )
    latest_evaluation = db.scalars(
        select(KnowledgeEvaluationRun)
        .where(KnowledgeEvaluationRun.tenant_id == tenant_id)
        .order_by(KnowledgeEvaluationRun.created_at.desc(), KnowledgeEvaluationRun.id.desc())
    ).first()

    wait_minutes = [
        max(0, int((interval_end - (_as_aware_utc(conversation_by_id[item.conversation_id].last_message_at) or interval_end)).total_seconds() // 60))
        for item in open_reviews
        if conversation_by_id.get(item.conversation_id)
    ]
    average_wait_minutes = int(sum(wait_minutes) / len(wait_minutes)) if wait_minutes else 0
    review_and_draft_total = len(open_reviews) + len(pending_drafts) + len(ready_drafts)
    ai_draft_coverage = _bounded_ratio(len(pending_drafts) + len(ready_drafts), review_and_draft_total)
    manual_review_pressure = _bounded_ratio(len(open_reviews), review_and_draft_total)
    exception_pressure = _bounded_ratio(
        len(open_failure_reviews) + len(blocked_jobs),
        review_and_draft_total + len(open_failure_reviews) + len(blocked_jobs),
    )
    health_score = max(
        0,
        min(
            100,
            int(
                100
                - manual_review_pressure * 24
                - exception_pressure * 32
                - min(len(high_risk_reviews) * 8, 24)
                - min(len(open_knowledge_gaps) * 5, 15)
            ),
        ),
    )

    trend_by_key = {item.key: item for item in _trend_buckets(range_key, start=interval_start, end=interval_end)}
    for item in scoped_conversations:
        key = _bucket_key(item.created_at, range_key=range_key, start=interval_start, end=interval_end)
        if key in trend_by_key:
            trend_by_key[key].inbound += 1
    for item in open_reviews:
        key = _bucket_key(item.created_at, range_key=range_key, start=interval_start, end=interval_end)
        if key in trend_by_key:
            trend_by_key[key].reviews += 1
    for item in pending_drafts + ready_drafts:
        key = _bucket_key(item.created_at, range_key=range_key, start=interval_start, end=interval_end)
        if key in trend_by_key:
            trend_by_key[key].drafts += 1
    for item in open_failure_reviews + blocked_jobs:
        key = _bucket_key(item.created_at, range_key=range_key, start=interval_start, end=interval_end)
        if key in trend_by_key:
            trend_by_key[key].exceptions += 1

    action_items: list[OpsDashboardActionItemRead] = []
    if high_risk_reviews:
        action_items.append(
            OpsDashboardActionItemRead(
                code="high_risk_review",
                title="高风险回复需要优先复核",
                detail="存在高风险或关键业务场景的人审任务，建议先处理再扩大自动回复范围。",
                severity="critical",
                href="/reviews",
                count=len(high_risk_reviews),
            )
        )
    if pending_drafts:
        action_items.append(
            OpsDashboardActionItemRead(
                code="pending_outbox_draft",
                title="待确认草稿积压",
                detail="有 AI 草稿等待人工确认，持续积压会拉长客户等待时间。",
                severity="warning",
                href="/outbox",
                count=len(pending_drafts),
            )
        )
    if open_failure_reviews or blocked_jobs:
        action_items.append(
            OpsDashboardActionItemRead(
                code="delivery_exception",
                title="渠道发送异常需要复盘",
                detail="存在发送失败复盘或死信任务，需要确认渠道权限、回执和重试策略。",
                severity="critical",
                href="/outbox/failures",
                count=len(open_failure_reviews) + len(blocked_jobs),
            )
        )
    if open_knowledge_gaps:
        action_items.append(
            OpsDashboardActionItemRead(
                code="knowledge_gap",
                title="知识库缺口待补齐",
                detail="评测或低置信复盘发现知识缺口，建议补充知识卡片或更新文档。",
                severity="warning",
                href="/knowledge/gaps",
                count=len(open_knowledge_gaps),
            )
        )

    return OpsDashboardRead(
        tenant_id=tenant_id,
        generated_at=interval_end,
        range=range_key,
        interval_start=interval_start,
        interval_end=interval_end,
        channel_id=channel_id,
        data_mode="server_aggregation",
        data_source=OpsDashboardDataSourceRead(
            mode="server_aggregation",
            label="服务端聚合",
            source="standard_ops_operational_tables",
            contract_version="p3_06t_02_v1",
            aggregation_grain="tenant_range_channel_aggregate",
            refresh_model="request_time_read",
            freshness="request_time_read",
            completeness="complete",
            source_tables=[
                "conversations",
                "messages",
                "human_review_tasks",
                "outbox_drafts",
                "delivery_failure_reviews",
                "outbox_delivery_jobs",
                "knowledge_gap_items",
                "support_tickets",
                "sales_leads",
                "knowledge_evaluation_runs",
            ],
            excluded_fields=[
                "messages.content",
                "human_review_tasks.draft_reply",
                "outbox_drafts.reply_text",
                "contacts.phone",
                "contacts.email",
                "sales_leads.contact_value",
                "delivery_receipts.raw_payload",
                "channel_connectors.public_config",
            ],
            caveats=[
                "即时读侧聚合，不是历史数仓或物化统计表。",
                "仅返回计数、比例、时间窗口和动作摘要，不返回客户原文或出站草稿全文。",
                "channel_id 筛选只统计该渠道关联的会话、草稿、失败复盘、工单和线索；知识缺口只在全部渠道视图统计。",
            ],
            is_demo=False,
            uses_local_sample=False,
            fallback_reason=None,
        ),
        source_window=OpsDashboardSourceWindowRead(
            range=range_key,
            label=_ops_dashboard_window_label(range_key),
            start=interval_start,
            end=interval_end,
            generated_at=interval_end,
            timezone="UTC",
        ),
        filters=OpsDashboardFilterRead(
            range=range_key,
            channel_id=channel_id,
            channel_name=selected_channel.name if selected_channel else None,
            channel_type=selected_channel.type if selected_channel else None,
            is_channel_filtered=channel_id is not None,
        ),
        summary=OpsDashboardSummaryRead(
            inbound_conversations=len(scoped_conversations),
            inbound_messages=len(scoped_inbound_messages),
            open_reviews=len(open_reviews),
            high_risk_reviews=len(high_risk_reviews),
            pending_outbox_drafts=len(pending_drafts),
            ready_outbox_drafts=len(ready_drafts),
            open_failure_reviews=len(open_failure_reviews),
            blocked_delivery_jobs=len(blocked_jobs),
            open_knowledge_gaps=len(open_knowledge_gaps),
            open_tickets=len(open_tickets),
            open_leads=len(open_leads),
            average_wait_minutes=average_wait_minutes,
            ai_draft_coverage=ai_draft_coverage,
            manual_review_pressure=manual_review_pressure,
            exception_pressure=exception_pressure,
            health_score=health_score,
        ),
        channels=_channel_counts(
            visible_channels,
            conversations=scoped_conversations,
            reviews=open_reviews,
            drafts=pending_drafts + ready_drafts,
            failure_reviews=open_failure_reviews,
            blocked_jobs=blocked_jobs,
            conversation_by_id=conversation_by_id,
        ),
        funnel=[
            OpsDashboardFunnelStageRead(key="inbound", label="进入会话", count=len(scoped_conversations)),
            OpsDashboardFunnelStageRead(key="drafted", label="生成草稿", count=len(pending_drafts) + len(ready_drafts)),
            OpsDashboardFunnelStageRead(key="review", label="人工复核", count=len(open_reviews)),
            OpsDashboardFunnelStageRead(key="exception", label="异常复盘", count=len(open_failure_reviews) + len(blocked_jobs)),
        ],
        trend=list(trend_by_key.values()),
        quality=OpsDashboardQualityRead(
            latest_evaluation_run_id=latest_evaluation.id if latest_evaluation else None,
            total_cases=latest_evaluation.total_cases if latest_evaluation else 0,
            hit_rate=latest_evaluation.hit_rate if latest_evaluation else None,
            citation_coverage=latest_evaluation.citation_coverage if latest_evaluation else None,
            expected_term_coverage=latest_evaluation.expected_term_coverage if latest_evaluation else None,
            needs_review_rate=_bounded_ratio(latest_evaluation.needs_review_cases, latest_evaluation.total_cases)
            if latest_evaluation
            else None,
            average_confidence=latest_evaluation.average_confidence if latest_evaluation else None,
        ),
        action_items=action_items,
        external_call_performed=False,
        external_platform_write_performed=False,
    )


@router.get(
    "/tenants/{tenant_id}/ops/worker-health",
    response_model=WorkerHealthDashboardRead,
)
def get_worker_health_dashboard(
    tenant_id: int,
    stale_after_seconds: int = Query(default=120, ge=1, le=3600),
    recent_run_limit: int = Query(default=10, ge=1, le=50),
    principal: CurrentPrincipal = Depends(require_permission("ops.worker_health.read")),
    db: Session = Depends(get_db),
) -> WorkerHealthDashboardRead:
    require_tenant(db, tenant_id)
    _require_same_tenant(tenant_id, principal)
    settings = get_settings()
    heartbeats = list_worker_heartbeats(
        db,
        tenant_id=tenant_id,
        stale_after_seconds=stale_after_seconds,
        limit=100,
        offset=0,
    )
    recent_runs = list(
        db.scalars(
            select(TrustedInboundWorkerRunRecord)
            .where(TrustedInboundWorkerRunRecord.tenant_id == tenant_id)
            .order_by(TrustedInboundWorkerRunRecord.started_at.desc(), TrustedInboundWorkerRunRecord.id.desc())
            .limit(recent_run_limit)
        ).all()
    )
    healthy = sum(1 for item in heartbeats if item.health_status == "healthy")
    stale = sum(1 for item in heartbeats if item.health_status == "stale")
    failed = sum(1 for item in heartbeats if item.health_status == "failed")
    running = sum(1 for item in heartbeats if item.status == "running")
    idle = sum(1 for item in heartbeats if item.status == "idle")
    risks = _build_worker_risks(
        heartbeats=heartbeats,
        recent_runs=recent_runs,
        external_write_enabled=settings.outbox_external_write_enabled,
    )
    return WorkerHealthDashboardRead(
        tenant_id=tenant_id,
        generated_at=utc_now(),
        stale_after_seconds=stale_after_seconds,
        summary=WorkerHealthSummary(
            total_workers=len(heartbeats),
            healthy_workers=healthy,
            stale_workers=stale,
            failed_workers=failed,
            running_workers=running,
            idle_workers=idle,
            external_write_enabled=settings.outbox_external_write_enabled,
            trusted_inbound_worker_enabled=settings.trusted_inbound_worker_enabled,
            requires_attention=bool(risks),
        ),
        heartbeats=heartbeats,
        recent_trusted_inbound_runs=recent_runs,
        risks=risks,
        external_call_performed=False,
        external_platform_write_performed=False,
    )


@router.get(
    "/tenants/{tenant_id}/ops/alert-rules",
    response_model=OpsAlertRulesDashboardRead,
)
def get_alert_rules_dashboard(
    tenant_id: int,
    stale_after_seconds: int = Query(default=120, ge=1, le=3600),
    recent_run_limit: int = Query(default=10, ge=1, le=50),
    principal: CurrentPrincipal = Depends(require_permission("ops.alert_rules.read")),
    db: Session = Depends(get_db),
) -> OpsAlertRulesDashboardRead:
    require_tenant(db, tenant_id)
    _require_same_tenant(tenant_id, principal)
    settings = get_settings()
    heartbeats = list_worker_heartbeats(
        db,
        tenant_id=tenant_id,
        stale_after_seconds=stale_after_seconds,
        limit=100,
        offset=0,
    )
    recent_runs = list(
        db.scalars(
            select(TrustedInboundWorkerRunRecord)
            .where(TrustedInboundWorkerRunRecord.tenant_id == tenant_id)
            .order_by(TrustedInboundWorkerRunRecord.started_at.desc(), TrustedInboundWorkerRunRecord.id.desc())
            .limit(recent_run_limit)
        ).all()
    )
    rules = _build_ops_alert_rules(
        heartbeats=heartbeats,
        recent_runs=recent_runs,
        stale_after_seconds=stale_after_seconds,
        trusted_inbound_worker_enabled=settings.trusted_inbound_worker_enabled,
        trusted_inbound_worker_tenant_slug=settings.trusted_inbound_worker_tenant_slug,
        trusted_inbound_worker_user_email=settings.trusted_inbound_worker_user_email,
        external_write_enabled=settings.outbox_external_write_enabled,
    )
    firing_rules = [rule for rule in rules if rule.status == "firing"]
    return OpsAlertRulesDashboardRead(
        tenant_id=tenant_id,
        generated_at=utc_now(),
        stale_after_seconds=stale_after_seconds,
        recent_run_limit=recent_run_limit,
        notification_channel_enabled=False,
        notification_sent=False,
        firing_count=len(firing_rules),
        page_count=sum(1 for rule in firing_rules if rule.response_type == "page"),
        ticket_count=sum(1 for rule in firing_rules if rule.response_type == "ticket"),
        rules=rules,
        external_call_performed=False,
        external_platform_write_performed=False,
    )


@router.get(
    "/tenants/{tenant_id}/ops/metrics",
    response_model=OpsMetricsDashboardRead,
)
def get_ops_metrics_dashboard(
    tenant_id: int,
    stale_after_seconds: int = Query(default=120, ge=1, le=3600),
    recent_run_limit: int = Query(default=10, ge=1, le=50),
    principal: CurrentPrincipal = Depends(require_permission("ops.metrics.read")),
    db: Session = Depends(get_db),
) -> OpsMetricsDashboardRead:
    require_tenant(db, tenant_id)
    _require_same_tenant(tenant_id, principal)
    settings = get_settings()
    heartbeats = list_worker_heartbeats(
        db,
        tenant_id=tenant_id,
        stale_after_seconds=stale_after_seconds,
        limit=100,
        offset=0,
    )
    recent_runs = list(
        db.scalars(
            select(TrustedInboundWorkerRunRecord)
            .where(TrustedInboundWorkerRunRecord.tenant_id == tenant_id)
            .order_by(TrustedInboundWorkerRunRecord.started_at.desc(), TrustedInboundWorkerRunRecord.id.desc())
            .limit(recent_run_limit)
        ).all()
    )
    rules = _build_ops_alert_rules(
        heartbeats=heartbeats,
        recent_runs=recent_runs,
        stale_after_seconds=stale_after_seconds,
        trusted_inbound_worker_enabled=settings.trusted_inbound_worker_enabled,
        trusted_inbound_worker_tenant_slug=settings.trusted_inbound_worker_tenant_slug,
        trusted_inbound_worker_user_email=settings.trusted_inbound_worker_user_email,
        external_write_enabled=settings.outbox_external_write_enabled,
    )
    summary, metrics = _build_ops_metrics(
        tenant_id=tenant_id,
        heartbeats=heartbeats,
        recent_runs=recent_runs,
        rules=rules,
        outbox_job_counts=_count_by_status(db, model=OutboxDeliveryJob, tenant_id=tenant_id),
        trusted_message_job_counts=_count_by_status(db, model=TrustedInboundMessageJob, tenant_id=tenant_id),
        delivery_failure_review_counts=_count_by_status(db, model=DeliveryFailureReview, tenant_id=tenant_id),
        external_write_enabled=settings.outbox_external_write_enabled,
        trusted_inbound_worker_enabled=settings.trusted_inbound_worker_enabled,
    )
    return OpsMetricsDashboardRead(
        tenant_id=tenant_id,
        generated_at=utc_now(),
        stale_after_seconds=stale_after_seconds,
        recent_run_limit=recent_run_limit,
        collection_model="pull_json_or_prometheus_text_preview",
        scrape_path=f"/api/tenants/{tenant_id}/ops/metrics",
        summary=summary,
        metrics=metrics,
        prometheus_text=_build_prometheus_text(metrics),
        external_call_performed=False,
        external_platform_write_performed=False,
    )
