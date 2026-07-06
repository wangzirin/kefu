from __future__ import annotations

import argparse
import getpass
import sys
from pathlib import Path

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker


ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
DEFAULT_DB = ROOT / "data" / "local_dev.sqlite"

if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.core.security import hash_password  # noqa: E402
from app.models import Role, Tenant, User, UserRole  # noqa: E402


DEFAULT_ROLES: tuple[tuple[str, str], ...] = (
    ("owner", "负责人"),
    ("admin", "管理员"),
    ("agent", "客服"),
    ("viewer", "只读查看"),
)


def sqlite_url(path: Path) -> str:
    return f"sqlite+pysqlite:///{path.expanduser().resolve()}"


def prompt_password() -> str:
    password = getpass.getpass("New admin password: ")
    confirm = getpass.getpass("Confirm password: ")
    if password != confirm:
        raise SystemExit("password confirmation does not match")
    return password


def main() -> None:
    parser = argparse.ArgumentParser(description="Create or reset a local admin account in the desktop SQLite database.")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB, help="SQLite database path.")
    parser.add_argument("--tenant-slug", required=True, help="Tenant slug used on the login page.")
    parser.add_argument("--tenant-name", default="本地客服工作台", help="Tenant name to create when missing.")
    parser.add_argument("--email", required=True, help="Admin email used on the login page.")
    parser.add_argument("--name", default="管理员", help="Admin display name.")
    parser.add_argument("--password", default="", help="New password. Omit to enter it interactively.")
    args = parser.parse_args()

    password = args.password or prompt_password()
    if len(password) < 8:
        raise SystemExit("password must be at least 8 characters")

    engine = create_engine(sqlite_url(args.db), connect_args={"check_same_thread": False})
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    tenant_slug = args.tenant_slug.strip().lower()
    email = args.email.strip().lower()

    with session_factory() as db:
        tenant = db.scalar(select(Tenant).where(Tenant.slug == tenant_slug))
        if tenant is None:
            tenant = Tenant(
                name=args.tenant_name.strip() or "本地客服工作台",
                slug=tenant_slug,
                plan="standard_ops",
                status="active",
            )
            db.add(tenant)
            db.flush()

        roles = {role.code: role for role in db.scalars(select(Role).where(Role.tenant_id == tenant.id)).all()}
        for code, name in DEFAULT_ROLES:
            if code not in roles:
                role = Role(tenant_id=tenant.id, code=code, name=name)
                db.add(role)
                db.flush()
                roles[code] = role

        user = db.scalar(select(User).where(User.tenant_id == tenant.id, User.email == email))
        if user is None:
            user = User(
                tenant_id=tenant.id,
                name=args.name.strip() or "管理员",
                email=email,
                password_hash=hash_password(password),
                status="active",
            )
            db.add(user)
            db.flush()
            action = "created"
        else:
            user.name = args.name.strip() or user.name
            user.password_hash = hash_password(password)
            user.status = "active"
            action = "reset"

        for code in ("owner", "admin"):
            role = roles[code]
            existing = db.scalar(select(UserRole).where(UserRole.user_id == user.id, UserRole.role_id == role.id))
            if existing is None:
                db.add(UserRole(user_id=user.id, role_id=role.id))

        db.commit()

    print(f"local admin {action}: tenant_slug={tenant_slug} email={email}")


if __name__ == "__main__":
    main()
