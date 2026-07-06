#!/usr/bin/env python3
"""Static checks for P3-06U-05 real login role smoke."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_text(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    app = read_text("frontend/src/App.tsx")
    script = read_text("scripts/check_p3_06u_05_real_login_role_smoke.mjs")
    doc = read_text("docs/P3-06U-05_REAL_LOGIN_ROLE_SMOKE.md")

    for snippet in [
        'data-role-smoke="login-form"',
        'name="tenant_slug"',
        'data-role-smoke="tenant-slug"',
        'data-role-smoke="email"',
        'data-role-smoke="password"',
        'data-role-smoke="login-submit"',
        'data-role-smoke="logout-button"',
        "data-role-task-id",
        "data-workspace-nav",
    ]:
        require(snippet in app, f"App missing stable smoke selector: {snippet}")

    for snippet in [
        "seedTenantAndUsers",
        "loginThroughForm",
        "owner",
        "admin",
        "agent",
        "viewer",
        "window.localStorage.getItem",
        "/api/auth/login",
        "/api/auth/me",
        "unexpected403",
        "仅管理员可导入",
        "restrictedCheck",
        "output/p3_06u_role_smoke",
        "summary.json",
    ]:
        require(snippet in script, f"real login smoke script missing snippet: {snippet}")

    for phrase in [
        "# P3-06U-05 真实登录与角色端到端前端 Smoke",
        "真实账号",
        "真实令牌",
        "owner",
        "admin",
        "agent",
        "viewer",
        "不使用开发演示进入",
        "不触发真实平台外发",
        "P3-06U-06 质量复盘 BI",
    ]:
        require(phrase in doc, f"documentation missing phrase: {phrase}")

    print("P3-06U-05 real login role smoke static checks passed.")


if __name__ == "__main__":
    main()
