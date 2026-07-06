#!/usr/bin/env python3
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]


REQUIRED_PATHS = [
    "backend/app/db/session.py",
    "backend/app/api/accounts.py",
    "backend/app/api/audit.py",
    "backend/app/api/tenants.py",
    "backend/app/api/conversations.py",
    "backend/app/schemas/foundation.py",
    "backend/tests/conftest.py",
    "backend/tests/test_accounts_api.py",
    "backend/tests/test_auth_rbac_audit.py",
    "backend/tests/test_foundation_api.py",
]

REQUIRED_TEXT = {
    "backend/app/main.py": [
        "app.include_router(accounts.router)",
        "app.include_router(audit.router)",
        "app.include_router(tenants.router)",
        "app.include_router(conversations.router)",
    ],
    "backend/app/models/foundation.py": [
        "class AuthSession",
        "class AuditEvent",
        "class Role",
        "class Team",
        "class ConversationEvent",
        "class Tag",
        "class ConversationTag",
    ],
    "backend/app/api/tenants.py": [
        "@router.post(\"\"",
        "@router.get(\"\"",
        "/{tenant_id}/channels",
        "/{tenant_id}/contacts",
    ],
    "backend/app/api/accounts.py": [
        "/tenants/{tenant_id}/users",
        "/tenants/{tenant_id}/roles",
        "/users/{user_id}/roles",
        "/tenants/{tenant_id}/teams",
        "/teams/{team_id}/members",
        "_require_manager",
        "_tenant_has_user_roles",
    ],
    "backend/app/api/auth.py": [
        "/login",
        "create_session_token",
        "hash_token",
        "verify_password",
    ],
    "backend/app/api/audit.py": [
        "/tenants/{tenant_id}/audit-events",
        "require_any_role(\"owner\", \"admin\")",
    ],
    "backend/app/api/conversations.py": [
        "/tenants/{tenant_id}/conversations",
        "/conversations/{conversation_id}/messages",
        "message.{payload.direction}",
    ],
    "backend/app/schemas/foundation.py": [
        "class UserCreate",
        "class RoleCreate",
        "class TeamCreate",
        "class TeamMemberCreate",
    ],
    "frontend/src/App.tsx": [
        "LoginScreen",
        "TOKEN_STORAGE_KEY",
        "开发演示进入",
        "logout",
    ],
    "frontend/src/api/client.ts": [
        "interface LoginRequest",
        "interface LoginResponse",
        "export async function login",
        "Authorization",
    ],
}


def fail(message: str) -> None:
    print(f"FAIL stage1 foundation: {message}")
    sys.exit(1)


def main() -> None:
    missing = [path for path in REQUIRED_PATHS if not (ROOT / path).exists()]
    if missing:
        fail("missing files: " + ", ".join(missing))

    for path, fragments in REQUIRED_TEXT.items():
        content = (ROOT / path).read_text(encoding="utf-8")
        for fragment in fragments:
            if fragment not in content:
                fail(f"missing fragment in {path}: {fragment}")

    print("PASS stage1 foundation")


if __name__ == "__main__":
    main()
