from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.auth import CurrentPrincipal, get_current_principal_optional
from app.core.config import get_settings
from app.core.rbac import principal_has_permission
from app.db.session import get_db
from app.models import Channel, Contact, Tenant
from app.schemas.foundation import (
    ChannelCreate,
    ChannelRead,
    ContactCreate,
    ContactRead,
    TenantCreate,
    TenantRead,
)

router = APIRouter(prefix="/api/tenants", tags=["tenants"])

TENANTS_MANAGE_PERMISSION = "accounts.manage"
CHANNEL_READ_PERMISSION = "channel.read"
CHANNEL_MANAGE_PERMISSION = "channel.manage"
CUSTOMER_READ_PERMISSION = "customer.read"
CUSTOMER_MANAGE_PERMISSION = "customer.manage"


def _require_foundation_permission(
    principal: CurrentPrincipal | None,
    permission: str,
    *,
    tenant_id: int | None = None,
) -> None:
    if principal is None:
        if get_settings().dev_bootstrap_enabled:
            return
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="valid bearer token required",
        )
    if tenant_id is not None and principal.tenant.id != tenant_id:
        raise HTTPException(status_code=404, detail="tenant not found")
    if not principal_has_permission(principal, permission):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="insufficient permission")


@router.post("", response_model=TenantRead, status_code=status.HTTP_201_CREATED)
def create_tenant(
    payload: TenantCreate,
    principal: CurrentPrincipal | None = Depends(get_current_principal_optional),
    db: Session = Depends(get_db),
) -> Tenant:
    _require_foundation_permission(principal, TENANTS_MANAGE_PERMISSION)
    tenant = Tenant(name=payload.name, slug=payload.slug, plan=payload.plan)
    db.add(tenant)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="tenant slug already exists") from exc
    db.refresh(tenant)
    return tenant


@router.get("", response_model=list[TenantRead])
def list_tenants(
    principal: CurrentPrincipal | None = Depends(get_current_principal_optional),
    db: Session = Depends(get_db),
) -> list[Tenant]:
    _require_foundation_permission(principal, TENANTS_MANAGE_PERMISSION)
    return list(db.scalars(select(Tenant).order_by(Tenant.id)).all())


def require_tenant(db: Session, tenant_id: int) -> Tenant:
    tenant = db.get(Tenant, tenant_id)
    if tenant is None:
        raise HTTPException(status_code=404, detail="tenant not found")
    return tenant


@router.post(
    "/{tenant_id}/channels",
    response_model=ChannelRead,
    status_code=status.HTTP_201_CREATED,
)
def create_channel(
    tenant_id: int,
    payload: ChannelCreate,
    principal: CurrentPrincipal | None = Depends(get_current_principal_optional),
    db: Session = Depends(get_db),
) -> Channel:
    require_tenant(db, tenant_id)
    _require_foundation_permission(principal, CHANNEL_MANAGE_PERMISSION, tenant_id=tenant_id)
    channel = Channel(tenant_id=tenant_id, **payload.model_dump())
    db.add(channel)
    db.commit()
    db.refresh(channel)
    return channel


@router.get("/{tenant_id}/channels", response_model=list[ChannelRead])
def list_channels(
    tenant_id: int,
    principal: CurrentPrincipal | None = Depends(get_current_principal_optional),
    db: Session = Depends(get_db),
) -> list[Channel]:
    require_tenant(db, tenant_id)
    _require_foundation_permission(principal, CHANNEL_READ_PERMISSION, tenant_id=tenant_id)
    query = select(Channel).where(Channel.tenant_id == tenant_id).order_by(Channel.id)
    return list(db.scalars(query).all())


@router.post(
    "/{tenant_id}/contacts",
    response_model=ContactRead,
    status_code=status.HTTP_201_CREATED,
)
def create_contact(
    tenant_id: int,
    payload: ContactCreate,
    principal: CurrentPrincipal | None = Depends(get_current_principal_optional),
    db: Session = Depends(get_db),
) -> Contact:
    require_tenant(db, tenant_id)
    _require_foundation_permission(principal, CUSTOMER_MANAGE_PERMISSION, tenant_id=tenant_id)
    contact = Contact(tenant_id=tenant_id, **payload.model_dump())
    db.add(contact)
    db.commit()
    db.refresh(contact)
    return contact


@router.get("/{tenant_id}/contacts", response_model=list[ContactRead])
def list_contacts(
    tenant_id: int,
    principal: CurrentPrincipal | None = Depends(get_current_principal_optional),
    db: Session = Depends(get_db),
) -> list[Contact]:
    require_tenant(db, tenant_id)
    _require_foundation_permission(principal, CUSTOMER_READ_PERMISSION, tenant_id=tenant_id)
    query = select(Contact).where(Contact.tenant_id == tenant_id).order_by(Contact.id)
    return list(db.scalars(query).all())
