from datetime import datetime, timedelta
import hashlib

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.audit import add_audit_event
from app.core.auth import CurrentPrincipal, get_current_principal_optional
from app.core.config import get_settings
from app.core.rbac import permissions_for_roles
from app.core.security import create_session_token, hash_password, hash_token, verify_password
from app.db.session import get_db
from app.models import AuthSession, Role, Tenant, User, UserRole
from app.models.foundation import utc_now
from app.schemas.auth import (
    CurrentUser,
    LocalOwnerSetupRequest,
    LocalSetupStatus,
    LoginRequest,
    LoginResponse,
    TenantSummary,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])

LOCAL_DEV_TENANT_SLUG = "wanfa-local-dev"
LOCAL_DEV_USER_EMAIL = "real-test@wanfa.local"
DEFAULT_LOCAL_ROLES: tuple[tuple[str, str], ...] = (
    ("owner", "负责人"),
    ("admin", "管理员"),
    ("agent", "客服"),
    ("viewer", "只读查看"),
)
LOGIN_FAILURE_WINDOW_SECONDS = 300
LOGIN_FAILURE_LIMIT = 5
LOGIN_COOLDOWN_SECONDS = 300

_login_failures: dict[tuple[str, str], list[datetime]] = {}
_login_cooldowns: dict[tuple[str, str], datetime] = {}


def _current_user_from_principal(principal: CurrentPrincipal) -> CurrentUser:
    return CurrentUser(
        id=str(principal.user.id),
        name=principal.user.name,
        email=principal.user.email,
        roles=principal.roles,
        permissions=sorted(permissions_for_roles(principal.roles)),
        tenant=TenantSummary(
            id=str(principal.tenant.id),
            name=principal.tenant.name,
            slug=principal.tenant.slug,
            plan=principal.tenant.plan,
        ),
    )


def _bootstrap_user() -> CurrentUser:
    return CurrentUser(
        id="bootstrap-admin",
        name="标准运营版管理员",
        email="admin@example.com",
        roles=["owner"],
        permissions=sorted(permissions_for_roles(["owner"])),
        tenant=TenantSummary(
            id="bootstrap-tenant",
            name="万法常世演示客户空间",
            slug="wanfa-demo",
            plan="standard_ops",
        ),
    )


def _role_codes(db: Session, user_id: int) -> list[str]:
    query = (
        select(Role.code)
        .join(UserRole, UserRole.role_id == Role.id)
        .where(UserRole.user_id == user_id)
        .order_by(Role.code)
    )
    return list(db.scalars(query).all())


def _issue_login_response(db: Session, *, user: User, tenant: Tenant, audit_action: str) -> LoginResponse:
    token = create_session_token()
    expires_at = utc_now() + timedelta(hours=8)
    session = AuthSession(
        user_id=user.id,
        token_hash=hash_token(token),
        expires_at=expires_at,
    )
    db.add(session)
    add_audit_event(
        db,
        tenant_id=tenant.id,
        actor_id=user.id,
        action=audit_action,
        resource_type="auth_session",
        payload={"expires_at": expires_at.isoformat()},
    )
    db.commit()
    principal = CurrentPrincipal(user=user, tenant=tenant, roles=_role_codes(db, user.id))
    return LoginResponse(
        access_token=token,
        token_type="bearer",
        expires_at=expires_at,
        user=_current_user_from_principal(principal),
    )


def _login_key(tenant_slug: str, email: str) -> tuple[str, str]:
    return (tenant_slug.strip().lower(), email.strip().lower())


def _hash_email(email: str) -> str:
    return hashlib.sha256(email.strip().lower().encode("utf-8")).hexdigest()


def _prune_login_failures(key: tuple[str, str], now: datetime) -> list[datetime]:
    window_start = now - timedelta(seconds=LOGIN_FAILURE_WINDOW_SECONDS)
    failures = [item for item in _login_failures.get(key, []) if item >= window_start]
    if failures:
        _login_failures[key] = failures
    else:
        _login_failures.pop(key, None)
    return failures


def _active_login_cooldown(key: tuple[str, str], now: datetime) -> datetime | None:
    cooldown_until = _login_cooldowns.get(key)
    if cooldown_until is None:
        return None
    if cooldown_until <= now:
        _login_cooldowns.pop(key, None)
        _login_failures.pop(key, None)
        return None
    return cooldown_until


def _audit_login_failure(
    db: Session,
    *,
    tenant: Tenant | None,
    user: User | None,
    email: str,
    reason: str,
    cooldown_until: datetime | None = None,
) -> None:
    if tenant is None:
        return
    payload = {
        "reason": reason,
        "email_sha256": _hash_email(email),
        "cooldown_until": cooldown_until.isoformat() if cooldown_until else None,
    }
    add_audit_event(
        db,
        tenant_id=tenant.id,
        actor_id=user.id if user is not None else None,
        action="auth.login_failed",
        resource_type="auth_login",
        resource_id=_hash_email(email)[:16],
        payload=payload,
    )
    db.commit()


def _record_login_failure(
    db: Session,
    *,
    tenant: Tenant | None,
    user: User | None,
    key: tuple[str, str],
    email: str,
    now: datetime,
) -> None:
    failures = _prune_login_failures(key, now)
    failures.append(now)
    _login_failures[key] = failures
    cooldown_until: datetime | None = None
    if len(failures) >= LOGIN_FAILURE_LIMIT:
        cooldown_until = now + timedelta(seconds=LOGIN_COOLDOWN_SECONDS)
        _login_cooldowns[key] = cooldown_until
    _audit_login_failure(
        db,
        tenant=tenant,
        user=user,
        email=email,
        reason="rate_limited" if cooldown_until else "invalid_credentials",
        cooldown_until=cooldown_until,
    )


def _local_setup_safety_blockers() -> list[str]:
    settings = get_settings()
    blockers: list[str] = []
    if settings.outbox_external_write_enabled:
        blockers.append("external_write_enabled")
    if settings.dev_bootstrap_enabled:
        blockers.append("dev_bootstrap_enabled")
    if settings.trusted_inbound_worker_enabled:
        blockers.append("trusted_inbound_worker_enabled")
    return blockers


def _tenant_count(db: Session) -> int:
    return int(db.scalar(select(func.count(Tenant.id))) or 0)


def _user_count(db: Session) -> int:
    return int(db.scalar(select(func.count(User.id))) or 0)


def _normalize_slug(value: str) -> str:
    slug = value.strip().lower().replace("_", "-")
    if not slug:
        raise HTTPException(status_code=422, detail="tenant slug required")
    if len(slug) > 80:
        raise HTTPException(status_code=422, detail="tenant slug too long")
    allowed = set("abcdefghijklmnopqrstuvwxyz0123456789-")
    if any(char not in allowed for char in slug):
        raise HTTPException(status_code=422, detail="tenant slug only supports lowercase letters, numbers and hyphen")
    return slug


def _ensure_default_role(db: Session, tenant_id: int, code: str, name: str) -> Role:
    role = db.scalar(select(Role).where(Role.tenant_id == tenant_id, Role.code == code))
    if role is not None:
        return role
    role = Role(tenant_id=tenant_id, code=code, name=name)
    db.add(role)
    db.flush()
    return role


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> LoginResponse:
    tenant_slug = payload.tenant_slug.strip().lower()
    email = payload.email.strip().lower()
    key = _login_key(tenant_slug, email)
    now = utc_now()

    cooldown_until = _active_login_cooldown(key, now)
    tenant = db.scalar(select(Tenant).where(Tenant.slug == tenant_slug))
    if cooldown_until is not None:
        user = (
            db.scalar(select(User).where(User.tenant_id == tenant.id, User.email == email))
            if tenant is not None
            else None
        )
        _audit_login_failure(
            db,
            tenant=tenant,
            user=user,
            email=email,
            reason="rate_limited",
            cooldown_until=cooldown_until,
        )
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="too many login attempts")

    if tenant is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid credentials")
    user = db.scalar(
        select(User).where(User.tenant_id == tenant.id, User.email == email)
    )
    if user is None or user.status != "active" or not verify_password(payload.password, user.password_hash):
        _record_login_failure(db, tenant=tenant, user=user, key=key, email=email, now=now)
        if _active_login_cooldown(key, now) is not None:
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="too many login attempts")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid credentials")

    _login_failures.pop(key, None)
    _login_cooldowns.pop(key, None)
    return _issue_login_response(db, user=user, tenant=tenant, audit_action="auth.login")


@router.post("/dev-local-login", response_model=LoginResponse)
def dev_local_login(db: Session = Depends(get_db)) -> LoginResponse:
    settings = get_settings()
    if settings.env.strip().lower() != "development" or not settings.dev_bootstrap_enabled:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="local dev login disabled")

    tenant = db.scalar(select(Tenant).where(Tenant.slug == LOCAL_DEV_TENANT_SLUG, Tenant.status == "active"))
    if tenant is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="local dev workspace not seeded")

    user = db.scalar(
        select(User).where(
            User.tenant_id == tenant.id,
            User.email == LOCAL_DEV_USER_EMAIL,
            User.status == "active",
        )
    )
    if user is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="local dev account not seeded")

    return _issue_login_response(db, user=user, tenant=tenant, audit_action="auth.dev_local_login")


@router.get("/local-setup/status", response_model=LocalSetupStatus)
def local_setup_status(db: Session = Depends(get_db)) -> LocalSetupStatus:
    settings = get_settings()
    tenants = _tenant_count(db)
    users = _user_count(db)
    can_create_first_owner = users == 0
    setup_mode = "create_first_owner" if can_create_first_owner else "login_only"
    blockers: list[str] = []
    readiness_checks: list[str] = []

    if can_create_first_owner:
        readiness_checks.append("first_owner_creation_open")
    else:
        readiness_checks.append("first_owner_creation_locked")

    readiness_checks.append("web_password_reset_disabled")
    readiness_checks.append("no_default_password")

    blockers = _local_setup_safety_blockers()

    if not settings.outbox_external_write_enabled:
        readiness_checks.append("external_write_disabled")
    if not settings.dev_bootstrap_enabled:
        readiness_checks.append("dev_bootstrap_disabled")
    if not settings.trusted_inbound_worker_enabled:
        readiness_checks.append("trusted_inbound_worker_disabled")

    first_tenant = db.scalar(select(Tenant).where(Tenant.slug == LOCAL_DEV_TENANT_SLUG, Tenant.status == "active"))
    if first_tenant is None:
        first_tenant = db.scalar(select(Tenant).order_by(Tenant.id).limit(1))
    return LocalSetupStatus(
        initialized=users > 0,
        tenant_count=tenants,
        user_count=users,
        can_create_first_owner=can_create_first_owner,
        setup_mode=setup_mode,
        first_owner_creation_locked=not can_create_first_owner,
        web_password_reset_enabled=False,
        env=settings.env,
        dev_bootstrap_enabled=settings.dev_bootstrap_enabled,
        external_write_enabled=settings.outbox_external_write_enabled,
        trusted_inbound_worker_enabled=settings.trusted_inbound_worker_enabled,
        local_deployment_ready=len(blockers) == 0,
        readiness_checks=readiness_checks,
        blockers=blockers,
        first_tenant_slug=first_tenant.slug if first_tenant else None,
        first_tenant_name=first_tenant.name if first_tenant else None,
    )


@router.post("/local-setup/owner", response_model=LoginResponse, status_code=status.HTTP_201_CREATED)
def create_local_owner(payload: LocalOwnerSetupRequest, db: Session = Depends(get_db)) -> LoginResponse:
    if _user_count(db) > 0:
        raise HTTPException(status_code=409, detail="local workspace already initialized")

    tenant_slug = _normalize_slug(payload.tenant_slug)
    email = payload.email.strip().lower()
    blockers = _local_setup_safety_blockers()
    if blockers:
        raise HTTPException(
            status_code=409,
            detail={"message": "local deployment safety blockers", "blockers": blockers},
        )
    tenant = db.scalar(select(Tenant).where(Tenant.slug == tenant_slug))
    try:
        if tenant is None:
            tenant = Tenant(
                name=payload.tenant_name.strip(),
                slug=tenant_slug,
                plan="standard_ops",
                status="active",
            )
            db.add(tenant)
            db.flush()

        owner_role: Role | None = None
        for code, name in DEFAULT_LOCAL_ROLES:
            role = _ensure_default_role(db, tenant.id, code, name)
            if code == "owner":
                owner_role = role
        if owner_role is None:
            raise HTTPException(status_code=500, detail="owner role bootstrap failed")

        user = User(
            tenant_id=tenant.id,
            name=payload.owner_name.strip(),
            email=email,
            password_hash=hash_password(payload.password),
            status="active",
        )
        db.add(user)
        db.flush()
        db.add(UserRole(user_id=user.id, role_id=owner_role.id))
        db.flush()
        add_audit_event(
            db,
            tenant_id=tenant.id,
            actor_id=user.id,
            action="auth.local_setup_owner_created",
            resource_type="user",
            resource_id=str(user.id),
            payload={"email": user.email, "tenant_slug": tenant.slug},
        )
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="local setup conflict") from exc

    return _issue_login_response(db, user=user, tenant=tenant, audit_action="auth.local_setup_login")


@router.get("/me", response_model=CurrentUser)
def current_user(
    principal: CurrentPrincipal | None = Depends(get_current_principal_optional),
) -> CurrentUser:
    if principal is None:
        settings = get_settings()
        if settings.env.strip().lower() != "development" or not settings.dev_bootstrap_enabled:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="valid bearer token required",
            )
        return _bootstrap_user()
    return _current_user_from_principal(principal)
