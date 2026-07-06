from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.api.tenants import require_tenant
from app.core.auth import CurrentPrincipal
from app.core.rbac import require_permission
from app.db.session import get_db
from app.schemas.support_tickets import SupportTicketCreate, SupportTicketList, SupportTicketRead, SupportTicketUpdate
from app.services.support_tickets import create_support_ticket_from_conversation, list_support_tickets, update_support_ticket

router = APIRouter(prefix="/api", tags=["support-tickets"])

TICKET_READ_PERMISSION = "ticket.read"
TICKET_MANAGE_PERMISSION = "ticket.manage"


@router.get("/tenants/{tenant_id}/support-tickets", response_model=SupportTicketList)
def list_tenant_support_tickets(
    tenant_id: int,
    status_filter: str | None = Query(default="all", alias="status", max_length=32),
    priority: str | None = Query(default="all", max_length=32),
    assigned: str = Query(default="all", pattern="^(all|mine|assigned|unassigned)$"),
    sla: str = Query(default="all", pattern="^(all|ok|warning|breached|paused|completed)$"),
    query_text: str = Query(default="", alias="query", max_length=200),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    principal: CurrentPrincipal = Depends(require_permission(TICKET_READ_PERMISSION)),
    db: Session = Depends(get_db),
) -> SupportTicketList:
    require_tenant(db, tenant_id)
    return list_support_tickets(
        db,
        tenant_id,
        status_filter=status_filter,
        priority=priority,
        assigned=assigned,
        sla=sla,
        query_text=query_text,
        page=page,
        page_size=page_size,
        principal=principal,
    )


@router.post("/conversations/{conversation_id}/support-tickets", response_model=SupportTicketRead)
def post_support_ticket_from_conversation(
    conversation_id: int,
    payload: SupportTicketCreate,
    response: Response,
    principal: CurrentPrincipal = Depends(require_permission(TICKET_MANAGE_PERMISSION)),
    db: Session = Depends(get_db),
) -> SupportTicketRead:
    ticket, created = create_support_ticket_from_conversation(db, conversation_id, payload, principal)
    response.status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
    return ticket


@router.patch("/support-tickets/{ticket_id}", response_model=SupportTicketRead)
def patch_support_ticket(
    ticket_id: int,
    payload: SupportTicketUpdate,
    principal: CurrentPrincipal = Depends(require_permission(TICKET_MANAGE_PERMISSION)),
    db: Session = Depends(get_db),
) -> SupportTicketRead:
    return update_support_ticket(db, ticket_id, payload, principal)
