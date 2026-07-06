#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = ROOT / "output/p3_06u_26h2w11e_owner_customer_knowledge_trial_static"
MJS_PATH = ROOT / "scripts/check_p3_06u_26h2w11e_owner_customer_knowledge_trial.mjs"
DOC_PATH = ROOT / "docs/P3-06U-26H2W11E_OWNER_CUSTOMER_KNOWLEDGE_TRIAL.md"
MASTER_PLAN_PATH = ROOT / "docs/P3-06U-26H2W_NETWORKED_ENGINEERING_MASTER_PLAN.md"
MATRIX_PATH = ROOT / "docs/FRONTEND_FUNCTION_REALITY_MATRIX.md"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _require_contains(name: str, content: str, needles: list[str]) -> list[str]:
    return [f"{name} missing {needle!r}" for needle in needles if needle not in content]


def run_h2w11e_owner_customer_knowledge_trial_static_gate(
    *,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
) -> dict[str, Any]:
    blockers: list[str] = []
    warnings: list[str] = []

    for path in [MJS_PATH, DOC_PATH, MASTER_PLAN_PATH, MATRIX_PATH]:
        if not path.exists():
            blockers.append(f"required file missing: {path.relative_to(ROOT)}")

    if blockers:
        result = {
            "phase": "H2W-11E",
            "status": "blocked",
            "blockers": blockers,
            "warnings": warnings,
            "boundaries": _boundaries(),
        }
        _write_summary(output_dir, result)
        return result

    mjs = _read(MJS_PATH)
    doc = _read(DOC_PATH)
    master_plan = _read(MASTER_PLAN_PATH)
    matrix = _read(MATRIX_PATH)

    blockers.extend(
        _require_contains(
            "scripts/check_p3_06u_26h2w11e_owner_customer_knowledge_trial.mjs",
            mjs,
            [
                "seedOwner",
                "loginThroughUi",
                "owner_login_performed_through_ui",
                "customer_publish_path_actions_checked",
                "customer_publish_path_clicked_through_ui",
                "server_persistence_verified",
                "verifyServerData",
                'data-h2w11d-customer-publish-path="true"',
                'data-h2w11d-action="convert-customer-intake"',
                'data-h2w11d-action="preview-update-package"',
                'data-h2w11d-action="import-update-package"',
                "#knowledge",
                "#evals",
                "#quality",
                "#gaps",
                "真实外发继续关闭",
                "客户确认记录不是正式验收",
                "external_platform_write_performed: false",
                "real_platform_send_performed: false",
                "model_call_performed: false",
                "formal_customer_signoff_performed: false",
                "real_customer_data_used: false",
            ],
        )
    )
    blockers.extend(
        _require_contains(
            "docs/P3-06U-26H2W11E_OWNER_CUSTOMER_KNOWLEDGE_TRIAL.md",
            doc,
            [
                "# H2W-11E 负责人真实登录逐页试用验收",
                "负责人真实登录",
                "生成资料包",
                "检查资料包",
                "导入知识库",
                "知识评测中心",
                "质量诊断",
                "知识缺口",
                "服务端落库",
                "真实外发继续关闭",
                "不是正式电子签章",
                "不是正式客户验收",
            ],
        )
    )
    blockers.extend(
        _require_contains(
            "docs/P3-06U-26H2W_NETWORKED_ENGINEERING_MASTER_PLAN.md",
            master_plan,
            [
                "H2W-11E",
                "负责人真实登录逐页试用验收",
                "空按钮",
                "重复入口",
                "客户术语",
                "知识三页边界",
            ],
        )
    )
    blockers.extend(
        _require_contains(
            "docs/FRONTEND_FUNCTION_REALITY_MATRIX.md",
            matrix,
            [
                "H2W-11E",
                "负责人真实登录逐页试用",
                "知识维护总流程",
            ],
        )
    )

    forbidden_runtime_shortcuts = [
        "localStorage.setItem('wanfa_standard_ops_access_token'",
        'localStorage.setItem("wanfa_standard_ops_access_token"',
        "demo_mode_used: true",
        "external_platform_write_performed: true",
        "real_platform_send_performed: true",
        "formal_customer_signoff_performed: true",
    ]
    found_shortcuts = [needle for needle in forbidden_runtime_shortcuts if needle in mjs]
    if found_shortcuts:
        blockers.append(f"H2W-11E browser gate contains forbidden shortcut or overclaim: {found_shortcuts}")

    if "emptyIconButtons" not in mjs:
        warnings.append("browser gate should keep checking visible empty icon-only buttons on linked pages")
    if "visibleOverclaims" not in mjs:
        warnings.append("browser gate should keep checking visible overclaim copy")

    result = {
        "phase": "H2W-11E",
        "status": "passed" if not blockers else "blocked",
        "blockers": blockers,
        "warnings": warnings,
        "checks": {
            "uses_real_login_form": "loginThroughUi" in mjs and "requestSubmit" in mjs,
            "checks_customer_publish_actions": mjs.count("data-h2w11d-action") >= 3,
            "checks_linked_pages": all(hash_value in mjs for hash_value in ["#evals", "#quality", "#gaps"]),
            "verifies_server_persistence": "verifyServerData" in mjs and "business_object_total" in mjs,
            "updates_reality_matrix": "H2W-11E" in matrix,
            "updates_master_plan": "H2W-11E" in master_plan,
        },
        "boundaries": _boundaries(),
    }
    _write_summary(output_dir, result)
    return result


def _boundaries() -> dict[str, bool]:
    return {
        "provider_call_performed": False,
        "external_platform_write_performed": False,
        "real_platform_send_performed": False,
        "formal_customer_signoff_performed": False,
        "electronic_signature_performed": False,
        "real_customer_data_used": False,
    }


def _write_summary(output_dir: Path, result: dict[str, Any]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "summary.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    result = run_h2w11e_owner_customer_knowledge_trial_static_gate()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result["blockers"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
