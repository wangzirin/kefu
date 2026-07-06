#!/usr/bin/env python3
"""Static readiness checks for P3-06UI admin ops tabs."""

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
    styles = read_text("frontend/src/styles.css")
    navigation = read_text("frontend/src/data/navigation.ts")
    doc = read_text("docs/P3-06UI_ADMIN_OPS_TABS.md")

    for snippet in [
        'type AdminOperationsTab = "ops" | "model" | "settings"',
        "function getAdminOperationsTab",
        "AdminOperationsWorkspace",
        "admin-ops-tabs",
        'case "model":',
        'case "ops":',
        'case "settings":',
        "管理运维",
        "运维与告警",
        "模型路由",
        "系统设置",
    ]:
        require(snippet in app, f"App missing admin ops snippet: {snippet}")

    require(
        app.index('case "model":') < app.index('case "ops":') < app.index('case "settings":'),
        "model/ops/settings cases should be grouped into the admin operations workspace",
    )
    require("getAdminOperationsTab(activeSection)" in app, "active admin tab should derive from current hash section")
    require("OpsWorkerHealthPanel" in app and "ModelRoutingPanel" in app, "admin workspace must preserve existing ops and model panels")
    require("PlanningWorkspacePanel" in app, "admin workspace must preserve settings planning panel")

    for snippet in [
        ".admin-ops-workspace",
        ".admin-ops-tabs",
        ".admin-ops-tab",
        ".admin-ops-tab.is-active",
    ]:
        require(snippet in styles, f"styles missing admin ops snippet: {snippet}")

    for snippet in [
        'href: "#ops"',
        'href: "#model"',
        'href: "#settings"',
        'visibleTo: ["owner", "admin"]',
    ]:
        require(snippet in navigation, f"navigation missing admin ops snippet: {snippet}")

    for phrase in [
        "管理运维内部二级 Tab",
        "不改后端接口",
        "不启用真实外发",
        "不触发真实模型调用",
        "不保存真实密钥",
        "后端资源级 RBAC",
    ]:
        require(phrase in doc, f"documentation missing phrase: {phrase}")

    print("P3-06UI admin ops tabs checks passed.")


if __name__ == "__main__":
    main()
