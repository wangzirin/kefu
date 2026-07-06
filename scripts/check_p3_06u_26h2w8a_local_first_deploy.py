from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


REQUIRED_MARKERS = {
    "backend/app/schemas/auth.py": [
        "p3-06u-26h2w8a.local_setup_status.v1",
        "setup_mode",
        "first_owner_creation_locked",
        "web_password_reset_enabled",
        "local_deployment_ready",
        "readiness_checks",
        "blockers",
    ],
    "backend/app/api/auth.py": [
        "first_owner_creation_open",
        "first_owner_creation_locked",
        "web_password_reset_disabled",
        "no_default_password",
        "external_write_disabled",
        "dev_bootstrap_disabled",
        "trusted_inbound_worker_disabled",
        "external_write_enabled",
        "dev_bootstrap_enabled",
    ],
    "backend/tests/test_local_setup_api.py": [
        "test_local_setup_status_starts_uninitialized",
        "test_create_local_owner_bootstraps_tenant_roles_user_and_session",
        "test_local_setup_status_reports_delivery_blockers",
        "STANDARD_OPS_DEV_BOOTSTRAP_ENABLED",
        "OUTBOX_EXTERNAL_WRITE_ENABLED",
        "TRUSTED_INBOUND_WORKER_ENABLED",
    ],
    "frontend/src/api/client.ts": [
        "local_deployment_ready",
        "first_owner_creation_locked",
        "web_password_reset_enabled",
        "blockers",
    ],
    "frontend/src/App.tsx": [
        'data-local-setup-status="p3-06u-26h2w8a"',
        "创建负责人并进入",
        "真实外发已关闭",
        "开发入口已关闭",
        "无身份重置已关闭",
        "系统不会预置默认密码",
        "local-owner-setup",
    ],
    "frontend/src/styles.css": [
        ".local-setup-checks",
        ".local-setup-chip",
        ".local-setup-status.is-blocked",
    ],
    "docs/P3-06U-26H2W8A_LOCAL_FIRST_DEPLOY_READINESS.md": [
        "H2W-8A",
        "首任负责人",
        "真实外发默认关闭",
        "开发入口关闭",
        "网页端不提供无身份重置",
        "停止门禁",
    ],
}


FORBIDDEN_MARKERS = {
    "frontend/src/App.tsx": [
        "第一次本地部署时，先创建第一个管理员账号",
        "创建管理员并进入",
        "初始化本地管理员失败",
    ],
}


def read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def main() -> None:
    failures: list[str] = []
    for relative_path, markers in REQUIRED_MARKERS.items():
        path = ROOT / relative_path
        if not path.exists():
            failures.append(f"missing file: {relative_path}")
            continue
        text = read(relative_path)
        for marker in markers:
            if marker not in text:
                failures.append(f"{relative_path}: missing marker {marker!r}")

    for relative_path, markers in FORBIDDEN_MARKERS.items():
        text = read(relative_path)
        for marker in markers:
            if marker in text:
                failures.append(f"{relative_path}: forbidden marker {marker!r}")

    if failures:
        raise SystemExit("\n".join(failures))
    print("P3-06U-26H2W8A local first deploy static gate passed.")


if __name__ == "__main__":
    main()
