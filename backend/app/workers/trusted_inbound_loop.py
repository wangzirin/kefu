from __future__ import annotations

import time

from sqlalchemy.orm import Session

from app.core.auth import CurrentPrincipal
from app.schemas.inbound_worker import (
    TrustedInboundWorkerLoopRunCreate,
    TrustedInboundWorkerLoopRunRead,
    TrustedInboundWorkerRunCreate,
    TrustedInboundWorkerRunRead,
)
from app.services.worker_heartbeats import upsert_worker_heartbeat, worker_heartbeat_to_read
from app.workers.trusted_inbound_orchestrator import WORKER_MODE, run_trusted_inbound_worker


def _single_run_payload(payload: TrustedInboundWorkerLoopRunCreate) -> TrustedInboundWorkerRunCreate:
    raw = payload.model_dump(exclude={"iterations", "sleep_seconds", "stale_after_seconds"})
    return TrustedInboundWorkerRunCreate(**raw)


def run_trusted_inbound_worker_loop(
    db: Session,
    *,
    tenant_id: int,
    payload: TrustedInboundWorkerLoopRunCreate,
    principal: CurrentPrincipal,
) -> TrustedInboundWorkerLoopRunRead:
    iterations_completed = 0
    failed_iterations = 0
    total_scanned = 0
    total_processed = 0
    total_succeeded = 0
    total_failed = 0
    total_skipped = 0
    total_rate_limited = 0
    external_write = False
    run_record_ids: list[int] = []
    last_run: TrustedInboundWorkerRunRead | None = None
    heartbeat = upsert_worker_heartbeat(
        db,
        tenant_id=tenant_id,
        worker_type=WORKER_MODE,
        worker_id=payload.worker_id,
        status="starting",
        metadata_payload={
            "loop": {
                "iterations_requested": payload.iterations,
                "sleep_seconds": payload.sleep_seconds,
                "external_write": False,
            }
        },
    )
    single_payload = _single_run_payload(payload)

    for index in range(payload.iterations):
        upsert_worker_heartbeat(
            db,
            tenant_id=tenant_id,
            worker_type=WORKER_MODE,
            worker_id=payload.worker_id,
            status="running",
            metadata_payload={
                "loop": {
                    "iteration": index + 1,
                    "iterations_requested": payload.iterations,
                    "external_write": False,
                }
            },
        )
        try:
            summary = run_trusted_inbound_worker(
                db,
                tenant_id=tenant_id,
                payload=single_payload,
                principal=principal,
            )
        except Exception as exc:  # pragma: no cover - defensive boundary for real daemon use
            failed_iterations += 1
            heartbeat = upsert_worker_heartbeat(
                db,
                tenant_id=tenant_id,
                worker_type=WORKER_MODE,
                worker_id=payload.worker_id,
                status="failed",
                last_error=str(exc)[:1000],
                metadata_payload={
                    "loop": {
                        "iteration": index + 1,
                        "iterations_requested": payload.iterations,
                        "external_write": False,
                    }
                },
            )
            break

        last_run = summary
        iterations_completed += 1
        total_scanned += summary.scanned
        total_processed += summary.processed
        total_succeeded += summary.succeeded
        total_failed += summary.failed
        total_skipped += summary.skipped
        total_rate_limited += summary.rate_limited
        external_write = external_write or summary.external_write
        if summary.run_record_id is not None:
            run_record_ids.append(summary.run_record_id)
        heartbeat = upsert_worker_heartbeat(
            db,
            tenant_id=tenant_id,
            worker_type=WORKER_MODE,
            worker_id=payload.worker_id,
            status="idle",
            last_run_record_id=summary.run_record_id,
            last_run_mode=summary.mode,
            last_error="",
            metadata_payload={
                "loop": {
                    "iteration": index + 1,
                    "iterations_requested": payload.iterations,
                    "external_write": False,
                },
                "last_summary": summary.model_dump(mode="json"),
            },
            increment_loops=True,
        )
        if payload.sleep_seconds > 0 and index < payload.iterations - 1:
            time.sleep(payload.sleep_seconds)

    return TrustedInboundWorkerLoopRunRead(
        tenant_id=tenant_id,
        worker_type=WORKER_MODE,
        worker_id=payload.worker_id,
        iterations_requested=payload.iterations,
        iterations_completed=iterations_completed,
        failed_iterations=failed_iterations,
        total_scanned=total_scanned,
        total_processed=total_processed,
        total_succeeded=total_succeeded,
        total_failed=total_failed,
        total_skipped=total_skipped,
        total_rate_limited=total_rate_limited,
        external_write=external_write,
        run_record_ids=run_record_ids,
        last_run=last_run,
        heartbeat=worker_heartbeat_to_read(
            heartbeat,
            stale_after_seconds=payload.stale_after_seconds,
        ),
    )
