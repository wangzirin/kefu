#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    target = ROOT / path
    if not target.exists():
        raise AssertionError(f"missing required file: {path}")
    return target.read_text(encoding="utf-8")


def require(path: str, needles: list[str]) -> None:
    body = read(path)
    missing = [needle for needle in needles if needle not in body]
    if missing:
        raise AssertionError(f"{path} missing: {missing}")


def forbid(path: str, needles: list[str]) -> None:
    body = read(path)
    hits = [needle for needle in needles if needle in body]
    if hits:
        raise AssertionError(f"{path} contains forbidden phrases: {hits}")


def main() -> None:
    require(
        "backend/app/services/diagnostics.py",
        [
            "REMEDIATION_UPDATE_PLAN_SCHEMA_VERSION",
            "p3-06u-26h2w6b.signed_update_control_plan.v1",
            "create_diagnostic_remediation_update_plan",
            "diagnostic_remediation.signed_update_plan_created",
            "update_plan_prepared",
            "can_apply_from_plan_now",
            "plan_generated_only",
            "真实外发继续关闭",
            "program_package_apply_supported",
        ],
    )
    require(
        "backend/app/api/diagnostics.py",
        [
            "/signed-update-plan",
            "DiagnosticRemediationUpdatePlanCreate",
            "create_diagnostic_remediation_update_plan",
            "UPDATES_MANAGE_PERMISSION",
        ],
    )
    require(
        "backend/app/schemas/diagnostics.py",
        [
            "class DiagnosticRemediationUpdatePlanCreate",
            "signed_update_package_id",
            "operator_note",
        ],
    )
    require(
        "backend/tests/test_diagnostics_api.py",
        [
            "test_owner_can_link_remediation_to_signed_update_plan_and_refresh_status",
            "diagnostic_remediation.signed_update_plan_created",
            "signed_update_package.applied",
            "signed_update_package.rolled_back",
            "can_apply_from_plan_now",
            "plan_generated_only",
        ],
    )
    require(
        "frontend/src/api/client.ts",
        [
            "createDiagnosticRemediationUpdatePlan",
            "/signed-update-plan",
            "signed_update_package_id",
            "operator_note",
        ],
    )
    require(
        "frontend/src/App.tsx",
        [
            "handleCreateDiagnosticRemediationUpdatePlan",
            "createRemediationUpdatePlan",
            'data-h2w6b-remediation-plan="p3-06u-26h2w6b"',
            'data-h2w6b-remediation-action="create-plan"',
            "只生成计划",
            "update_plan_prepared",
        ],
    )
    require(
        "frontend/src/styles.css",
        [
            ".diagnostic-remediation-plan",
            ".diagnostic-remediation-plan-steps",
            ".diagnostic-remediation-package-select",
        ],
    )
    require(
        "docs/P3-06U-26H2W6B_SIGNED_UPDATE_CONTROL_PLAN.md",
        [
            "P3-06U-26H2W6B 受控更新计划",
            "不是完整自动更新器",
            "真实外发继续关闭",
            "不远程控制客户电脑",
            "不静默更新客户环境",
            "程序包继续只允许",
            "can_apply_from_plan_now",
            "停止门禁",
        ],
    )
    require(
        "docs/FRONTEND_FUNCTION_REALITY_MATRIX.md",
        [
            "P3-06U-26H2W6B",
            "生成受控更新计划",
            "刷新受控更新计划",
        ],
    )
    forbid(
        "docs/P3-06U-26H2W6B_SIGNED_UPDATE_CONTROL_PLAN.md",
        [
            "已完成自动更新器",
            "已远程更新客户环境",
            "静默更新完成",
            "远程修复完成",
            "真实外发已打开",
            "程序包可直接应用",
        ],
    )
    forbid(
        "frontend/src/App.tsx",
        [
            "静默更新完成",
            "远程修复完成",
            "真实外发已打开",
            "程序包可直接应用",
        ],
    )
    print("P3-06U-26H2W6B signed update control plan static check passed.")


if __name__ == "__main__":
    main()
