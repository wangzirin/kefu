from dataclasses import dataclass
from datetime import datetime, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_token
from app.db.session import get_db
from app.models import AuthSession, Role, Tenant, User, UserRole

bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class CurrentPrincipal:
    user: User
    tenant: Tenant
    roles: list[str]


def _as_aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def get_current_principal_optional(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> CurrentPrincipal | None:
    if credentials is None:
        return None
    token_hash = hash_token(credentials.credentials)
    query = select(AuthSession).where(AuthSession.token_hash == token_hash)
    session = db.scalar(query)
    if session is None or session.revoked_at is not None:
        return None
    if _as_aware(session.expires_at) <= datetime.now(timezone.utc):
        return None
    user = db.get(User, session.user_id)
    if user is None or user.status != "active":
        return None
    tenant = db.get(Tenant, user.tenant_id)
    if tenant is None or tenant.status != "active":
        return None
    role_query = (
        select(Role.code)
        .join(UserRole, UserRole.role_id == Role.id)
        .where(UserRole.user_id == user.id)
        .order_by(Role.code)
    )
    roles = list(db.scalars(role_query).all())
    return CurrentPrincipal(user=user, tenant=tenant, roles=roles)


def require_current_principal(
    principal: CurrentPrincipal | None = Depends(get_current_principal_optional),
) -> CurrentPrincipal:
    if principal is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="valid bearer token required",
        )
    return principal


def require_any_role(*allowed_roles: str):
    allowed = set(allowed_roles)

    def dependency(
        principal: CurrentPrincipal = Depends(require_current_principal),
    ) -> CurrentPrincipal:
        if not allowed.intersection(principal.roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="insufficient role",
            )
        return principal

    return dependency
