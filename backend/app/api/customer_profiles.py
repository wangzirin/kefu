from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.api.tenants import require_tenant
from app.core.auth import CurrentPrincipal
from app.core.rbac import require_permission
from app.db.session import get_db
from app.schemas.customer_profiles import (
    ContactProfileDetail,
    ContactProfileList,
    SalesLeadCreate,
    SalesLeadList,
    SalesLeadRead,
    SalesLeadUpdate,
)
from app.services.customer_profiles import (
    create_lead_from_conversation,
    get_contact_profile,
    list_contact_profiles,
    list_sales_leads,
    update_sales_lead,
)

router = APIRouter(prefix="/api", tags=["customer-profiles"])

CUSTOMER_READ_PERMISSION = "customer.read"
LEAD_READ_PERMISSION = "lead.read"
LEAD_MANAGE_PERMISSION = "lead.manage"


@router.get("/tenants/{tenant_id}/contact-profiles", response_model=ContactProfileList)
def list_tenant_contact_profiles(
    tenant_id: int,
    query_text: str = Query(default="", alias="query", max_length=200),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    principal: CurrentPrincipal = Depends(require_permission(CUSTOMER_READ_PERMISSION)),
    db: Session = Depends(get_db),
) -> ContactProfileList:
    require_tenant(db, tenant_id)
    return list_contact_profiles(
        db,
        tenant_id,
        query_text=query_text,
        page=page,
        page_size=page_size,
        principal=principal,
    )


@router.get("/contact-profiles/{contact_id}", response_model=ContactProfileDetail)
def get_contact_profile_detail(
    contact_id: int,
    principal: CurrentPrincipal = Depends(require_permission(CUSTOMER_READ_PERMISSION)),
    db: Session = Depends(get_db),
) -> ContactProfileDetail:
    return get_contact_profile(db, contact_id, principal)


@router.get("/tenants/{tenant_id}/leads", response_model=SalesLeadList)
def list_tenant_sales_leads(
    tenant_id: int,
    stage: str = Query(default="all", max_length=32),
    intent: str = Query(default="all", max_length=32),
    owner: str = Query(default="all", pattern="^(all|mine|assigned|unassigned)$"),
    query_text: str = Query(default="", alias="query", max_length=200),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    principal: CurrentPrincipal = Depends(require_permission(LEAD_READ_PERMISSION)),
    db: Session = Depends(get_db),
) -> SalesLeadList:
    require_tenant(db, tenant_id)
    return list_sales_leads(
        db,
        tenant_id,
        stage=stage,
        intent=intent,
        owner=owner,
        query_text=query_text,
        page=page,
        page_size=page_size,
        principal=principal,
    )


@router.post("/conversations/{conversation_id}/leads", response_model=SalesLeadRead)
def post_lead_from_conversation(
    conversation_id: int,
    payload: SalesLeadCreate,
    response: Response,
    principal: CurrentPrincipal = Depends(require_permission(LEAD_MANAGE_PERMISSION)),
    db: Session = Depends(get_db),
) -> SalesLeadRead:
    lead, created = create_lead_from_conversation(db, conversation_id, payload, principal)
    response.status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
    return lead


@router.patch("/leads/{lead_id}", response_model=SalesLeadRead)
def patch_sales_lead(
    lead_id: int,
    payload: SalesLeadUpdate,
    principal: CurrentPrincipal = Depends(require_permission(LEAD_MANAGE_PERMISSION)),
    db: Session = Depends(get_db),
) -> SalesLeadRead:
    return update_sales_lead(db, lead_id, payload, principal)
