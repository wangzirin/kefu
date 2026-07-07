from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.tenants import require_tenant
from app.core.audit import add_audit_event
from app.core.auth import CurrentPrincipal, get_current_principal_optional
from app.core.rbac import principal_has_permission
from app.core.security import hash_password
from app.db.session import get_db
from app.models import AuthSession, Role, Team, TeamMember, User, UserRole
from app.models.foundation import utc_now
from app.schemas.foundation import (
    RoleCreate,
    RoleRead,
    TeamCreate,
    TeamMemberCreate,
    TeamMemberRead,
    TeamRead,
    UserCreate,
    UserPasswordReset,
    UserRead,
    UserRoleCreate,
    UserRoleRead,
    UserStatusUpdate,
)

router = APIRouter(prefix="/api", tags=["accounts"])

ACCOUNTS_MANAGE_PERMISSION = "accounts.manage"


def _commit_or_conflict(db: Session, detail: str) -> None:
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail=detail) from exc


def _flush_or_conflict(db: Session, detail: str) -> None:
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail=detail) from exc


def _can_manage_tenant(principal: CurrentPrincipal | None, tenant_id: int) -> bool:
    return (
        principal is not None
        and principal.tenant.id == tenant_id
        and principal_has_permission(principal, ACCOUNTS_MANAGE_PERMISSION)
    )


def _require_manager(principal: CurrentPrincipal | None, tenant_id: int) -> None:
    if not _can_manage_tenant(principal, tenant_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="insufficient permission")


def _tenant_has_users(db: Session, tenant_id: int) -> bool:
    query = select(User.id).where(User.tenant_id == tenant_id).limit(1)
    return db.scalar(query) is not None


def _tenant_has_roles(db: Session, tenant_id: int) -> bool:
    query = select(Role.id).where(Role.tenant_id == tenant_id).limit(1)
    return db.scalar(query) is not None


def _tenant_has_user_roles(db: Session, tenant_id: int) -> bool:
    query = (
        select(UserRole.id)
        .join(User, User.id == UserRole.user_id)
        .where(User.tenant_id == tenant_id)
        .limit(1)
    )
    return db.scalar(query) is not None


def _user_role_codes(db: Session, user_id: int) -> list[str]:
    query = (
        select(Role.code)
        .join(UserRole, UserRole.role_id == Role.id)
        .where(UserRole.user_id == user_id)
        .order_by(Role.code)
    )
    return list(db.scalars(query).all())


def _user_payload(db: Session, user: User) -> dict:
    return {
        "id": user.id,
        "tenant_id": user.tenant_id,
        "name": user.name,
        "email": user.email,
        "status": user.status,
        "roles": _user_role_codes(db, user.id),
        "avatar_data_url": user.avatar_data_url,
        "public_profile": user.public_profile or {},
        "created_at": user.created_at,
    }


def _active_owner_count(db: Session, tenant_id: int) -> int:
    query = (
        select(func.count(User.id))
        .join(UserRole, UserRole.user_id == User.id)
        .join(Role, Role.id == UserRole.role_id)
        .where(User.tenant_id == tenant_id, User.status == "active", Role.code == "owner")
    )
    return int(db.scalar(query) or 0)


def _revoke_user_sessions(db: Session, user_id: int) -> int:
    sessions = list(
        db.scalars(
            select(AuthSession).where(AuthSession.user_id == user_id, AuthSession.revoked_at.is_(None))
        ).all()
    )
    for session in sessions:
        session.revoked_at = utc_now()
    return len(sessions)


@router.post(
    "/tenants/{tenant_id}/users",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
)
def create_user(
    tenant_id: int,
    payload: UserCreate,
    principal: CurrentPrincipal | None = Depends(get_current_principal_optional),
    db: Session = Depends(get_db),
) -> dict:
    require_tenant(db, tenant_id)
    if _tenant_has_users(db, tenant_id):
        _require_manager(principal, tenant_id)
    user = User(
        tenant_id=tenant_id,
        name=payload.name,
        email=payload.email.strip().lower(),
        password_hash=hash_password(payload.password),
        status=payload.status,
    )
    db.add(user)
    _flush_or_conflict(db, "user email already exists inside tenant")
    add_audit_event(
        db,
        tenant_id=tenant_id,
        action="user.created",
        resource_type="user",
        actor_id=principal.user.id if principal else None,
        resource_id=str(user.id),
        payload={"email": user.email, "status": user.status},
    )
    _commit_or_conflict(db, "user email already exists inside tenant")
    db.refresh(user)
    return _user_payload(db, user)


@router.get("/tenants/{tenant_id}/users", response_model=list[UserRead])
def list_users(
    tenant_id: int,
    principal: CurrentPrincipal | None = Depends(get_current_principal_optional),
    db: Session = Depends(get_db),
) -> list[dict]:
    require_tenant(db, tenant_id)
    _require_manager(principal, tenant_id)
    query = select(User).where(User.tenant_id == tenant_id).order_by(User.id)
    return [_user_payload(db, user) for user in db.scalars(query).all()]


@router.patch("/users/{user_id}/status", response_model=UserRead)
def update_user_status(
    user_id: int,
    payload: UserStatusUpdate,
    principal: CurrentPrincipal | None = Depends(get_current_principal_optional),
    db: Session = Depends(get_db),
) -> dict:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="user not found")
    _require_manager(principal, user.tenant_id)
    previous_status = user.status
    target_status = payload.status
    if previous_status == target_status:
        return _user_payload(db, user)
    if target_status != "active" and "owner" in _user_role_codes(db, user.id) and _active_owner_count(db, user.tenant_id) <= 1:
        raise HTTPException(status_code=409, detail="cannot disable the last active owner")

    user.status = target_status
    revoked_sessions = _revoke_user_sessions(db, user.id) if target_status != "active" else 0
    add_audit_event(
        db,
        tenant_id=user.tenant_id,
        action="user.status_changed",
        resource_type="user",
        actor_id=principal.user.id if principal else None,
        resource_id=str(user.id),
        payload={
            "email": user.email,
            "previous_status": previous_status,
            "status": target_status,
            "revoked_sessions": revoked_sessions,
        },
    )
    db.commit()
    db.refresh(user)
    return _user_payload(db, user)


@router.post("/users/{user_id}/password-reset", response_model=UserRead)
def reset_user_password(
    user_id: int,
    payload: UserPasswordReset,
    principal: CurrentPrincipal | None = Depends(get_current_principal_optional),
    db: Session = Depends(get_db),
) -> dict:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="user not found")
    _require_manager(principal, user.tenant_id)
    user.password_hash = hash_password(payload.new_password)
    revoked_sessions = _revoke_user_sessions(db, user.id)
    add_audit_event(
        db,
        tenant_id=user.tenant_id,
        action="user.password_reset",
        resource_type="user",
        actor_id=principal.user.id if principal else None,
        resource_id=str(user.id),
        payload={"email": user.email, "revoked_sessions": revoked_sessions},
    )
    db.commit()
    db.refresh(user)
    return _user_payload(db, user)


@router.post(
    "/tenants/{tenant_id}/roles",
    response_model=RoleRead,
    status_code=status.HTTP_201_CREATED,
)
def create_role(
    tenant_id: int,
    payload: RoleCreate,
    principal: CurrentPrincipal | None = Depends(get_current_principal_optional),
    db: Session = Depends(get_db),
) -> Role:
    require_tenant(db, tenant_id)
    if _tenant_has_roles(db, tenant_id):
        _require_manager(principal, tenant_id)
    role = Role(
        tenant_id=tenant_id,
        code=payload.code.strip().lower(),
        name=payload.name,
    )
    db.add(role)
    _flush_or_conflict(db, "role code already exists inside tenant")
    add_audit_event(
        db,
        tenant_id=tenant_id,
        action="role.created",
        resource_type="role",
        actor_id=principal.user.id if principal else None,
        resource_id=str(role.id),
        payload={"code": role.code},
    )
    _commit_or_conflict(db, "role code already exists inside tenant")
    db.refresh(role)
    return role


@router.get("/tenants/{tenant_id}/roles", response_model=list[RoleRead])
def list_roles(
    tenant_id: int,
    principal: CurrentPrincipal | None = Depends(get_current_principal_optional),
    db: Session = Depends(get_db),
) -> list[Role]:
    require_tenant(db, tenant_id)
    _require_manager(principal, tenant_id)
    query = select(Role).where(Role.tenant_id == tenant_id).order_by(Role.id)
    return list(db.scalars(query).all())


@router.post(
    "/users/{user_id}/roles",
    response_model=UserRoleRead,
    status_code=status.HTTP_201_CREATED,
)
def assign_role(
    user_id: int,
    payload: UserRoleCreate,
    principal: CurrentPrincipal | None = Depends(get_current_principal_optional),
    db: Session = Depends(get_db),
) -> UserRole:
    user = db.get(User, user_id)
    role = db.get(Role, payload.role_id)
    if user is None or role is None or user.tenant_id != role.tenant_id:
        raise HTTPException(status_code=404, detail="user or role not found")
    if _tenant_has_user_roles(db, user.tenant_id):
        _require_manager(principal, user.tenant_id)
    user_role = UserRole(user_id=user_id, role_id=payload.role_id)
    db.add(user_role)
    _flush_or_conflict(db, "role already assigned to user")
    add_audit_event(
        db,
        tenant_id=user.tenant_id,
        action="user_role.assigned",
        resource_type="user_role",
        actor_id=principal.user.id if principal else None,
        resource_id=str(user_role.id),
        payload={"user_id": user_id, "role_id": payload.role_id},
    )
    _commit_or_conflict(db, "role already assigned to user")
    db.refresh(user_role)
    return user_role


@router.post(
    "/tenants/{tenant_id}/teams",
    response_model=TeamRead,
    status_code=status.HTTP_201_CREATED,
)
def create_team(
    tenant_id: int,
    payload: TeamCreate,
    principal: CurrentPrincipal | None = Depends(get_current_principal_optional),
    db: Session = Depends(get_db),
) -> Team:
    require_tenant(db, tenant_id)
    _require_manager(principal, tenant_id)
    team = Team(tenant_id=tenant_id, **payload.model_dump())
    db.add(team)
    db.flush()
    add_audit_event(
        db,
        tenant_id=tenant_id,
        action="team.created",
        resource_type="team",
        actor_id=principal.user.id,
        resource_id=str(team.id),
        payload={"name": team.name, "status": team.status},
    )
    db.commit()
    db.refresh(team)
    return team


@router.get("/tenants/{tenant_id}/teams", response_model=list[TeamRead])
def list_teams(
    tenant_id: int,
    principal: CurrentPrincipal | None = Depends(get_current_principal_optional),
    db: Session = Depends(get_db),
) -> list[Team]:
    require_tenant(db, tenant_id)
    _require_manager(principal, tenant_id)
    query = select(Team).where(Team.tenant_id == tenant_id).order_by(Team.id)
    return list(db.scalars(query).all())


@router.post(
    "/teams/{team_id}/members",
    response_model=TeamMemberRead,
    status_code=status.HTTP_201_CREATED,
)
def add_team_member(
    team_id: int,
    payload: TeamMemberCreate,
    principal: CurrentPrincipal | None = Depends(get_current_principal_optional),
    db: Session = Depends(get_db),
) -> TeamMember:
    team = db.get(Team, team_id)
    user = db.get(User, payload.user_id)
    if team is None or user is None or team.tenant_id != user.tenant_id:
        raise HTTPException(status_code=404, detail="team or user not found")
    _require_manager(principal, team.tenant_id)
    member = TeamMember(
        team_id=team_id,
        user_id=payload.user_id,
        role_in_team=payload.role_in_team,
    )
    db.add(member)
    _flush_or_conflict(db, "user already belongs to team")
    add_audit_event(
        db,
        tenant_id=team.tenant_id,
        action="team_member.added",
        resource_type="team_member",
        actor_id=principal.user.id,
        resource_id=str(member.id),
        payload={"team_id": team_id, "user_id": payload.user_id},
    )
    _commit_or_conflict(db, "user already belongs to team")
    db.refresh(member)
    return member
