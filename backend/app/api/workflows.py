from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.tenants import require_tenant
from app.core.auth import CurrentPrincipal
from app.core.rbac import require_permission
from app.db.session import get_db
from app.models import HumanReviewTask, WorkflowRun
from app.schemas.workflows import (
    HumanReviewTaskCreate,
    HumanReviewInboxItemRead,
    HumanReviewTaskRead,
    HumanReviewTaskResolve,
    WorkflowCheckpointCreate,
    WorkflowCheckpointRead,
    WorkflowRunCreate,
    WorkflowRunDetail,
    WorkflowRunRead,
    WorkflowStepAttemptCreate,
    WorkflowStepAttemptRead,
)
from app.services.workflows import (
    add_checkpoint,
    add_step_attempt,
    create_human_review_task,
    create_workflow_run,
    list_human_review_inbox,
    require_workflow_run_for_principal,
    resolve_human_review_task,
)

router = APIRouter(prefix="/api", tags=["workflows"])

CONVERSATION_READ_PERMISSION = "conversation.read"
CONVERSATION_MANAGE_PERMISSION = "conversation.manage"


def _require_same_tenant(tenant_id: int, principal: CurrentPrincipal) -> None:
    if principal.tenant.id != tenant_id:
        # Keep cross-tenant resources indistinguishable from missing resources.
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="tenant not found")


@router.post(
    "/conversations/{conversation_id}/workflow-runs",
    response_model=WorkflowRunRead,
    status_code=status.HTTP_201_CREATED,
)
def create_conversation_workflow_run(
    conversation_id: int,
    payload: WorkflowRunCreate,
    principal: CurrentPrincipal = Depends(require_permission(CONVERSATION_MANAGE_PERMISSION)),
    db: Session = Depends(get_db),
) -> WorkflowRun:
    return create_workflow_run(db, conversation_id, payload, principal)


@router.get("/tenants/{tenant_id}/workflow-runs", response_model=list[WorkflowRunRead])
def list_tenant_workflow_runs(
    tenant_id: int,
    status_filter: str | None = Query(default=None, alias="status"),
    principal: CurrentPrincipal = Depends(require_permission(CONVERSATION_READ_PERMISSION)),
    db: Session = Depends(get_db),
) -> list[WorkflowRun]:
    require_tenant(db, tenant_id)
    _require_same_tenant(tenant_id, principal)
    query = select(WorkflowRun).where(WorkflowRun.tenant_id == tenant_id)
    if status_filter:
        query = query.where(WorkflowRun.status == status_filter)
    query = query.order_by(WorkflowRun.updated_at.desc(), WorkflowRun.id.desc())
    return list(db.scalars(query).all())


@router.get("/workflow-runs/{workflow_run_id}", response_model=WorkflowRunDetail)
def get_workflow_run(
    workflow_run_id: int,
    principal: CurrentPrincipal = Depends(require_permission(CONVERSATION_READ_PERMISSION)),
    db: Session = Depends(get_db),
) -> WorkflowRun:
    require_workflow_run_for_principal(db, workflow_run_id, principal)
    query = (
        select(WorkflowRun)
        .options(
            selectinload(WorkflowRun.checkpoints),
            selectinload(WorkflowRun.step_attempts),
            selectinload(WorkflowRun.human_review_tasks),
        )
        .where(WorkflowRun.id == workflow_run_id)
    )
    return db.scalar(query)


@router.post(
    "/workflow-runs/{workflow_run_id}/step-attempts",
    response_model=WorkflowStepAttemptRead,
    status_code=status.HTTP_201_CREATED,
)
def create_workflow_step_attempt(
    workflow_run_id: int,
    payload: WorkflowStepAttemptCreate,
    principal: CurrentPrincipal = Depends(require_permission(CONVERSATION_MANAGE_PERMISSION)),
    db: Session = Depends(get_db),
):
    return add_step_attempt(db, workflow_run_id, payload, principal)


@router.post(
    "/workflow-runs/{workflow_run_id}/checkpoints",
    response_model=WorkflowCheckpointRead,
    status_code=status.HTTP_201_CREATED,
)
def create_workflow_checkpoint(
    workflow_run_id: int,
    payload: WorkflowCheckpointCreate,
    principal: CurrentPrincipal = Depends(require_permission(CONVERSATION_MANAGE_PERMISSION)),
    db: Session = Depends(get_db),
):
    return add_checkpoint(db, workflow_run_id, payload, principal)


@router.post(
    "/workflow-runs/{workflow_run_id}/human-review-tasks",
    response_model=HumanReviewTaskRead,
    status_code=status.HTTP_201_CREATED,
)
def create_workflow_human_review_task(
    workflow_run_id: int,
    payload: HumanReviewTaskCreate,
    principal: CurrentPrincipal = Depends(require_permission(CONVERSATION_MANAGE_PERMISSION)),
    db: Session = Depends(get_db),
):
    return create_human_review_task(db, workflow_run_id, payload, principal)


@router.get("/tenants/{tenant_id}/human-review-tasks", response_model=list[HumanReviewTaskRead])
def list_tenant_human_review_tasks(
    tenant_id: int,
    status_filter: str | None = Query(default=None, alias="status"),
    principal: CurrentPrincipal = Depends(require_permission(CONVERSATION_READ_PERMISSION)),
    db: Session = Depends(get_db),
) -> list[HumanReviewTask]:
    require_tenant(db, tenant_id)
    _require_same_tenant(tenant_id, principal)
    query = select(HumanReviewTask).where(HumanReviewTask.tenant_id == tenant_id)
    if status_filter:
        query = query.where(HumanReviewTask.status == status_filter)
    query = query.order_by(HumanReviewTask.created_at.desc(), HumanReviewTask.id.desc())
    return list(db.scalars(query).all())


@router.get("/tenants/{tenant_id}/human-review-inbox", response_model=list[HumanReviewInboxItemRead])
def list_tenant_human_review_inbox(
    tenant_id: int,
    status_filter: str | None = Query(default="open", alias="status"),
    principal: CurrentPrincipal = Depends(require_permission(CONVERSATION_READ_PERMISSION)),
    db: Session = Depends(get_db),
) -> list[HumanReviewInboxItemRead]:
    require_tenant(db, tenant_id)
    _require_same_tenant(tenant_id, principal)
    return list_human_review_inbox(db, tenant_id, status_filter=status_filter, principal=principal)


@router.patch("/human-review-tasks/{task_id}", response_model=HumanReviewTaskRead)
def update_human_review_task(
    task_id: int,
    payload: HumanReviewTaskResolve,
    principal: CurrentPrincipal = Depends(require_permission(CONVERSATION_MANAGE_PERMISSION)),
    db: Session = Depends(get_db),
):
    return resolve_human_review_task(db, task_id, payload, principal)
