from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.tenants import require_tenant
from app.core.auth import CurrentPrincipal
from app.core.rbac import require_permission
from app.db.session import get_db
from app.models import DeliveryFailureReview
from app.schemas.delivery_failures import DeliveryFailureReviewRead, DeliveryFailureReviewUpdate
from app.services.delivery_failures import list_delivery_failure_reviews, update_delivery_failure_review

router = APIRouter(prefix="/api", tags=["delivery-failures"])

OUTBOX_FAILURE_REVIEW_READ_PERMISSION = "outbox.failure_review.read"
OUTBOX_FAILURE_REVIEW_MANAGE_PERMISSION = "outbox.failure_review.manage"


@router.get(
    "/tenants/{tenant_id}/delivery-failure-reviews",
    response_model=list[DeliveryFailureReviewRead],
)
def list_tenant_delivery_failure_reviews(
    tenant_id: int,
    status_filter: str | None = Query(default="open", alias="status"),
    principal: CurrentPrincipal = Depends(require_permission(OUTBOX_FAILURE_REVIEW_READ_PERMISSION)),
    db: Session = Depends(get_db),
) -> list[DeliveryFailureReview]:
    require_tenant(db, tenant_id)
    return list_delivery_failure_reviews(db, tenant_id=tenant_id, status_filter=status_filter, principal=principal)


@router.patch("/delivery-failure-reviews/{review_id}", response_model=DeliveryFailureReviewRead)
def update_tenant_delivery_failure_review(
    review_id: int,
    payload: DeliveryFailureReviewUpdate,
    principal: CurrentPrincipal = Depends(require_permission(OUTBOX_FAILURE_REVIEW_MANAGE_PERMISSION)),
    db: Session = Depends(get_db),
) -> DeliveryFailureReview:
    return update_delivery_failure_review(db, review_id=review_id, payload=payload, principal=principal)
