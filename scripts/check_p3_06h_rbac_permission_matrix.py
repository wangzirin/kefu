#!/usr/bin/env python3
"""Static readiness checks for P3-06H RBAC permission matrix."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_text(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    rbac = read_text("backend/app/core/rbac.py")
    ops_api = read_text("backend/app/api/ops.py")
    test = read_text("backend/tests/test_p3_06h_rbac_permission_matrix.py")
    doc = read_text("docs/P3-06H_RBAC_PERMISSION_MATRIX.md")

    for snippet in [
        "ROLE_PERMISSIONS",
        "permissions_for_roles",
        "principal_has_permission",
        "allowed_roles_for_permission",
        "require_permission",
        '"ops.worker_health.read"',
        '"ops.alert_rules.read"',
        '"ops.metrics.read"',
    ]:
        require(snippet in rbac, f"rbac module missing snippet: {snippet}")

    for snippet in [
        'require_permission("ops.worker_health.read")',
        'require_permission("ops.alert_rules.read")',
        'require_permission("ops.metrics.read")',
        "_require_same_tenant",
    ]:
        require(snippet in ops_api, f"ops API missing permission snippet: {snippet}")

    require('require_any_role("owner", "admin")' not in ops_api, "ops API should use named permissions for P3-06H")

    for snippet in [
        "test_rbac_permission_matrix_maps_ops_permissions_to_owner_and_admin",
        "test_ops_metrics_permission_allows_admin_and_blocks_agent",
        "insufficient permission",
        "status_code == 401",
    ]:
        require(snippet in test, f"RBAC test missing snippet: {snippet}")

    for phrase in [
        "P3-06H RBAC 权限矩阵第一片",
        "命名权限",
        "owner",
        "admin",
        "agent",
        "viewer",
        "不一次性重写所有接口",
        "字段脱敏",
    ]:
        require(phrase in doc, f"RBAC documentation missing phrase: {phrase}")

    print("P3-06H RBAC permission matrix checks passed.")


if __name__ == "__main__":
    main()
