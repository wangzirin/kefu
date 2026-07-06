from __future__ import annotations

import argparse
import json
import sys
import time
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.auth import CurrentPrincipal
from app.core.config import get_settings
from app.db.session import get_session_factory
from app.models import Role, Tenant, User, UserRole, WorkerHeartbeat
from app.schemas.inbound_worker import TrustedInboundWorkerLoopRunCreate
from app.services.worker_heartbeats import worker_heartbeat_to_read
from app.workers.trusted_inbound_loop import run_trusted_inbound_worker_loop
from app.workers.trusted_inbound_orchestrator import WORKER_MODE


def resolve_worker_principal(
    db: Session,
    *,
    tenant_slug: str,
    user_email: str,
) -> CurrentPrincipal:
    if not tenant_slug:
        raise RuntimeError("TRUSTED_INBOUND_WORKER_TENANT_SLUG is required")
    if not user_email:
        raise RuntimeError("TRUSTED_INBOUND_WORKER_USER_EMAIL is required")
    tenant = db.scalar(select(Tenant).where(Tenant.slug == tenant_slug, Tenant.status == "active"))
    if tenant is None:
        raise RuntimeError(f"active tenant not found for slug: {tenant_slug}")
    user = db.scalar(
        select(User).where(
            User.tenant_id == tenant.id,
            User.email == user_email,
            User.status == "active",
        )
    )
    if user is None:
        raise RuntimeError(f"active worker user not found for tenant {tenant_slug}: {user_email}")
    role_query = (
        select(Role.code)
        .join(UserRole, UserRole.role_id == Role.id)
        .where(UserRole.user_id == user.id)
        .order_by(Role.code)
    )
    roles = list(db.scalars(role_query).all())
    if not {"owner", "admin"}.intersection(roles):
        raise RuntimeError("worker user must have owner or admin role")
    return CurrentPrincipal(user=user, tenant=tenant, roles=roles)


def _json_line(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True), flush=True)


def _build_loop_payload(args: argparse.Namespace) -> TrustedInboundWorkerLoopRunCreate:
    return TrustedInboundWorkerLoopRunCreate(
        iterations=1,
        sleep_seconds=0,
        batch_size=args.batch_size,
        rate_limit_per_minute=args.rate_limit_per_minute,
        worker_id=args.worker_id,
        lease_seconds=args.lease_seconds,
        stale_after_seconds=args.stale_after_seconds,
        mode=args.mode,
        risk_level=args.risk_level,
        intent=args.intent,
        knowledge_top_k=args.knowledge_top_k,
        model_provider=args.model_provider,
    )


def run_worker_service(db: Session, *, args: argparse.Namespace) -> int:
    principal = resolve_worker_principal(
        db,
        tenant_slug=args.tenant_slug,
        user_email=args.user_email,
    )
    completed_cycles = 0
    max_cycles = args.max_cycles
    _json_line(
        {
            "event": "trusted_inbound_worker_service_started",
            "tenant_id": principal.tenant.id,
            "tenant_slug": principal.tenant.slug,
            "worker_id": args.worker_id,
            "worker_type": WORKER_MODE,
            "max_cycles": max_cycles,
            "external_write": False,
        }
    )
    while max_cycles == 0 or completed_cycles < max_cycles:
        payload = _build_loop_payload(args)
        summary = run_trusted_inbound_worker_loop(
            db,
            tenant_id=principal.tenant.id,
            payload=payload,
            principal=principal,
        )
        completed_cycles += 1
        _json_line(
            {
                "event": "trusted_inbound_worker_service_cycle_completed",
                "tenant_id": principal.tenant.id,
                "worker_id": args.worker_id,
                "cycle": completed_cycles,
                "processed": summary.total_processed,
                "succeeded": summary.total_succeeded,
                "failed": summary.total_failed,
                "failed_iterations": summary.failed_iterations,
                "run_record_ids": summary.run_record_ids,
                "external_write": summary.external_write,
            }
        )
        if max_cycles != 0 and completed_cycles >= max_cycles:
            break
        time.sleep(args.sleep_seconds)
    _json_line(
        {
            "event": "trusted_inbound_worker_service_stopped",
            "tenant_id": principal.tenant.id,
            "worker_id": args.worker_id,
            "completed_cycles": completed_cycles,
            "external_write": False,
        }
    )
    return 0


def run_worker_healthcheck(db: Session, *, args: argparse.Namespace) -> int:
    principal = resolve_worker_principal(
        db,
        tenant_slug=args.tenant_slug,
        user_email=args.user_email,
    )
    heartbeat = db.scalar(
        select(WorkerHeartbeat).where(
            WorkerHeartbeat.tenant_id == principal.tenant.id,
            WorkerHeartbeat.worker_type == WORKER_MODE,
            WorkerHeartbeat.worker_id == args.worker_id,
        )
    )
    if heartbeat is None:
        _json_line(
            {
                "event": "trusted_inbound_worker_healthcheck",
                "worker_id": args.worker_id,
                "worker_type": WORKER_MODE,
                "health_status": "missing",
            }
        )
        return 1
    payload = worker_heartbeat_to_read(
        heartbeat,
        stale_after_seconds=args.stale_after_seconds,
    ).model_dump(mode="json")
    _json_line({"event": "trusted_inbound_worker_healthcheck", **payload})
    return 0 if payload["health_status"] == "healthy" else 1


def build_parser() -> argparse.ArgumentParser:
    settings = get_settings()
    parser = argparse.ArgumentParser(description="Run the trusted inbound worker as a deployment process.")
    parser.add_argument("--healthcheck", action="store_true", help="Check the current worker heartbeat and exit.")
    parser.add_argument("--tenant-slug", default=settings.trusted_inbound_worker_tenant_slug)
    parser.add_argument("--user-email", default=settings.trusted_inbound_worker_user_email)
    parser.add_argument("--worker-id", default=settings.trusted_inbound_worker_id)
    parser.add_argument("--max-cycles", type=int, default=0, help="0 means run until the process is stopped.")
    parser.add_argument("--sleep-seconds", type=float, default=settings.trusted_inbound_worker_sleep_seconds)
    parser.add_argument("--batch-size", type=int, default=settings.trusted_inbound_worker_batch_size)
    parser.add_argument(
        "--rate-limit-per-minute",
        type=int,
        default=settings.trusted_inbound_worker_rate_limit_per_minute,
    )
    parser.add_argument("--lease-seconds", type=int, default=settings.trusted_inbound_worker_lease_seconds)
    parser.add_argument(
        "--stale-after-seconds",
        type=int,
        default=settings.trusted_inbound_worker_heartbeat_stale_after_seconds,
    )
    parser.add_argument("--mode", default="model_assisted", choices=["knowledge_search", "model_assisted"])
    parser.add_argument("--risk-level", default="medium", choices=["low", "medium", "high", "critical"])
    parser.add_argument("--intent", default="general_inquiry")
    parser.add_argument("--knowledge-top-k", type=int, default=3)
    parser.add_argument("--model-provider", default="deterministic", choices=["deterministic", "auto", "bailian", "deepseek"])
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        session_factory = get_session_factory()
        with session_factory() as db:
            if args.healthcheck:
                return run_worker_healthcheck(db, args=args)
            return run_worker_service(db, args=args)
    except Exception as exc:
        _json_line(
            {
                "event": "trusted_inbound_worker_service_error",
                "error": str(exc),
                "external_write": False,
            }
        )
        return 2


if __name__ == "__main__":
    sys.exit(main())
