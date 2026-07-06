from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.tenants import require_tenant
from app.core.auth import CurrentPrincipal
from app.core.rbac import require_permission
from app.db.session import get_db
from app.models import OutboxDraft
from app.schemas.outbox import (
    OutboxDeliveryJobCreate,
    OutboxDeliveryJobRead,
    OutboxDeliveryQueueRunCreate,
    OutboxDeliveryQueueRunRead,
    OutboxDraftCancel,
    OutboxDraftConfirm,
    OutboxDraftCreateFromReview,
    OutboxDraftRead,
    OutboxSendAttemptCreate,
    OutboxSendAttemptRead,
    OutboxWorkerRunCreate,
    OutboxWorkerRunRead,
)
from app.services.outbox import (
    cancel_outbox_draft,
    confirm_outbox_draft,
    create_outbox_draft_from_review_task,
    create_outbox_send_attempt,
    list_outbox_drafts,
    list_outbox_send_attempts,
)
from app.services.outbox_delivery_queue import (
    create_outbox_delivery_job,
    list_outbox_delivery_jobs,
    run_outbox_delivery_queue,
)
from app.workers.outbox_sender import run_outbox_worker_dry_run

router = APIRouter(prefix="/api", tags=["outbox"])

OUTBOX_DRAFT_READ_PERMISSION = "outbox.draft.read"
OUTBOX_DRAFT_MANAGE_PERMISSION = "outbox.draft.manage"
OUTBOX_SEND_ATTEMPT_READ_PERMISSION = "outbox.send_attempt.read"
OUTBOX_SEND_ATTEMPT_MANAGE_PERMISSION = "outbox.send_attempt.manage"
OUTBOX_DELIVERY_JOB_READ_PERMISSION = "outbox.delivery_job.read"
OUTBOX_DELIVERY_JOB_MANAGE_PERMISSION = "outbox.delivery_job.manage"


def _require_same_tenant(tenant_id: int, principal: CurrentPrincipal) -> None:
    if principal.tenant.id != tenant_id:
        raise HTTPException(status_code=404, detail="tenant not found")


@router.post(
    "/human-review-tasks/{task_id}/outbox-drafts",
    response_model=OutboxDraftRead,
    status_code=status.HTTP_201_CREATED,
)
def create_outbox_draft_from_human_review(
    task_id: int,
    payload: OutboxDraftCreateFromReview,
    principal: CurrentPrincipal = Depends(require_permission(OUTBOX_DRAFT_MANAGE_PERMISSION)),
    db: Session = Depends(get_db),
) -> OutboxDraft:
    return create_outbox_draft_from_review_task(db, task_id, payload, principal)


@router.get("/tenants/{tenant_id}/outbox-drafts", response_model=list[OutboxDraftRead])
def list_tenant_outbox_drafts(
    tenant_id: int,
    status_filter: str | None = Query(default=None, alias="status"),
    principal: CurrentPrincipal = Depends(require_permission(OUTBOX_DRAFT_READ_PERMISSION)),
    db: Session = Depends(get_db),
) -> list[OutboxDraft]:
    require_tenant(db, tenant_id)
    _require_same_tenant(tenant_id, principal)
    return list_outbox_drafts(db, tenant_id, status_filter=status_filter, principal=principal)


@router.post("/outbox-drafts/{draft_id}/confirmation", response_model=OutboxDraftRead)
def confirm_tenant_outbox_draft(
    draft_id: int,
    payload: OutboxDraftConfirm,
    principal: CurrentPrincipal = Depends(require_permission(OUTBOX_DRAFT_MANAGE_PERMISSION)),
    db: Session = Depends(get_db),
) -> OutboxDraft:
    return confirm_outbox_draft(db, draft_id, payload, principal)


@router.post("/outbox-drafts/{draft_id}/cancellation", response_model=OutboxDraftRead)
def cancel_tenant_outbox_draft(
    draft_id: int,
    payload: OutboxDraftCancel,
    principal: CurrentPrincipal = Depends(require_permission(OUTBOX_DRAFT_MANAGE_PERMISSION)),
    db: Session = Depends(get_db),
) -> OutboxDraft:
    return cancel_outbox_draft(db, draft_id, payload, principal)


@router.post(
    "/outbox-drafts/{draft_id}/send-attempts",
    response_model=OutboxSendAttemptRead,
    status_code=status.HTTP_201_CREATED,
)
def create_tenant_outbox_send_attempt(
    draft_id: int,
    payload: OutboxSendAttemptCreate,
    principal: CurrentPrincipal = Depends(require_permission(OUTBOX_SEND_ATTEMPT_MANAGE_PERMISSION)),
    db: Session = Depends(get_db),
):
    return create_outbox_send_attempt(db, draft_id, payload, principal)


@router.get("/outbox-drafts/{draft_id}/send-attempts", response_model=list[OutboxSendAttemptRead])
def list_tenant_outbox_send_attempts(
    draft_id: int,
    principal: CurrentPrincipal = Depends(require_permission(OUTBOX_SEND_ATTEMPT_READ_PERMISSION)),
    db: Session = Depends(get_db),
):
    return list_outbox_send_attempts(db, draft_id, principal)


@router.post(
    "/outbox-drafts/{draft_id}/delivery-jobs",
    response_model=OutboxDeliveryJobRead,
    status_code=status.HTTP_201_CREATED,
)
def create_tenant_outbox_delivery_job(
    draft_id: int,
    payload: OutboxDeliveryJobCreate,
    principal: CurrentPrincipal = Depends(require_permission(OUTBOX_DELIVERY_JOB_MANAGE_PERMISSION)),
    db: Session = Depends(get_db),
):
    return create_outbox_delivery_job(db, draft_id, payload, principal)


@router.get("/tenants/{tenant_id}/outbox-delivery-jobs", response_model=list[OutboxDeliveryJobRead])
def list_tenant_outbox_delivery_jobs(
    tenant_id: int,
    status_filter: str | None = Query(default=None, alias="status"),
    principal: CurrentPrincipal = Depends(require_permission(OUTBOX_DELIVERY_JOB_READ_PERMISSION)),
    db: Session = Depends(get_db),
):
    require_tenant(db, tenant_id)
    _require_same_tenant(tenant_id, principal)
    return list_outbox_delivery_jobs(db, tenant_id=tenant_id, status_filter=status_filter, principal=principal)


@router.post(
    "/tenants/{tenant_id}/outbox-delivery-queue-runs",
    response_model=OutboxDeliveryQueueRunRead,
    status_code=status.HTTP_201_CREATED,
)
def create_tenant_outbox_delivery_queue_run(
    tenant_id: int,
    payload: OutboxDeliveryQueueRunCreate,
    principal: CurrentPrincipal = Depends(require_permission(OUTBOX_DELIVERY_JOB_MANAGE_PERMISSION)),
    db: Session = Depends(get_db),
) -> OutboxDeliveryQueueRunRead:
    require_tenant(db, tenant_id)
    _require_same_tenant(tenant_id, principal)
    return run_outbox_delivery_queue(db, tenant_id=tenant_id, payload=payload, principal=principal)


@router.post(
    "/tenants/{tenant_id}/outbox-worker-runs",
    response_model=OutboxWorkerRunRead,
    status_code=status.HTTP_201_CREATED,
)
def create_tenant_outbox_worker_run(
    tenant_id: int,
    payload: OutboxWorkerRunCreate,
    principal: CurrentPrincipal = Depends(require_permission(OUTBOX_SEND_ATTEMPT_MANAGE_PERMISSION)),
    db: Session = Depends(get_db),
) -> OutboxWorkerRunRead:
    require_tenant(db, tenant_id)
    _require_same_tenant(tenant_id, principal)
    return run_outbox_worker_dry_run(db, tenant_id=tenant_id, payload=payload, principal=principal)
