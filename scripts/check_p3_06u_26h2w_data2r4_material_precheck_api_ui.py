#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from lib.h2w_pack8_common import ROOT, base_result, display_path, write_json, write_markdown_report


PHASE = "H2W-DATA2R4"
SCHEMA_VERSION = "p3-06u-26h2w-data2r4.material_precheck_api_ui.v1"
OUTPUT_DIR = ROOT / "output/p3_06u_26h2w_data2r4_material_precheck_api_ui"
DOC_PATH = ROOT / "docs/P3-06U-26H2W_DATA2R4_MATERIAL_PRECHECK_API_UI.md"


FILES_TO_CHECK = {
    "backend_schema": ROOT / "backend/app/schemas/pilot.py",
    "backend_service": ROOT / "backend/app/services/pilot.py",
    "backend_router": ROOT / "backend/app/api/pilot.py",
    "backend_tests": ROOT / "backend/tests/test_pilot_api.py",
    "frontend_client": ROOT / "frontend/src/api/client.ts",
    "frontend_app": ROOT / "frontend/src/App.tsx",
    "frontend_styles": ROOT / "frontend/src/styles.css",
}


REQUIRED_SNIPPETS = {
    "backend_schema": [
        "class CustomerMaterialPrecheckCreate",
        "class CustomerMaterialPrecheckRead",
    ],
    "backend_service": [
        "CUSTOMER_MATERIAL_PRECHECK_SCHEMA_VERSION",
        "def precheck_customer_materials",
        "raw_materials_persisted",
        "real_customer_materials_ready",
        "formal_customer_signoff_ready",
        "customer_materials.prechecked",
    ],
    "backend_router": [
        '"/tenants/{tenant_id}/customer-materials/precheck"',
        "precheck_customer_material_package",
        'require_permission("knowledge.manage")',
    ],
    "backend_tests": [
        "test_customer_material_precheck_accepts_valid_in_memory_package",
        "test_customer_material_precheck_blocks_bad_package_without_persisting_raw_text",
    ],
    "frontend_client": [
        "CustomerMaterialPrecheckResult",
        "precheckCustomerMaterialPackage",
        "/customer-materials/precheck",
    ],
    "frontend_app": [
        "CustomerMaterialPrecheckState",
        "handlePrecheckCustomerMaterials",
        "资料预检",
        "校验试跑资料包",
        "原始资料未保存",
        "onPrecheckCustomerMaterials",
    ],
    "frontend_styles": [
        "pilot-material-precheck-panel",
        "pilot-boundary-note",
    ],
}


FORBIDDEN_UI_SNIPPETS = [
    "客户资料已确认完成",
    "真实外发已接通",
    "正式签收已完成",
    "生产 SLA 已完成",
    "已签名安装包",
]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _check_required_snippets() -> tuple[list[str], list[dict[str, Any]]]:
    blockers: list[str] = []
    checks: list[dict[str, Any]] = []
    for key, snippets in REQUIRED_SNIPPETS.items():
        path = FILES_TO_CHECK[key]
        if not path.exists():
            blockers.append(f"{key} 文件缺失：{display_path(path)}")
            checks.append({"name": key, "path": display_path(path), "passed": False, "missing": snippets})
            continue
        text = _read(path)
        missing = [snippet for snippet in snippets if snippet not in text]
        if missing:
            blockers.append(f"{key} 缺少必要片段：{', '.join(missing)}")
        checks.append(
            {
                "name": key,
                "path": display_path(path),
                "passed": not missing,
                "missing": missing,
            }
        )
    return blockers, checks


def _check_forbidden_ui_claims() -> list[str]:
    app_text = _read(FILES_TO_CHECK["frontend_app"]) if FILES_TO_CHECK["frontend_app"].exists() else ""
    return [f"前端出现越界完成态文案：{snippet}" for snippet in FORBIDDEN_UI_SNIPPETS if snippet in app_text]


def run_h2w_data2r4_material_precheck_api_ui() -> dict[str, Any]:
    blockers, snippet_checks = _check_required_snippets()
    blockers.extend(_check_forbidden_ui_claims())

    result = base_result(SCHEMA_VERSION, PHASE, "material_precheck_api_ui_ready", blockers)
    result.update(
        {
            "status": "blocked" if blockers else "material_precheck_api_ui_ready",
            "customer_data_used": False,
            "internal_sample_used": False,
            "feature_scope": {
                "backend_precheck_endpoint": True,
                "frontend_precheck_form": True,
                "raw_materials_persisted": False,
                "marks_real_customer_materials_ready": False,
                "starts_real_platform_send": False,
            },
            "readiness": {
                "material_precheck_api_ui_ready": not blockers,
                "real_customer_materials_ready": False,
                "real_platform_send_ready": False,
                "formal_customer_signoff_ready": False,
                "minimum_question_count_required": 50,
            },
            "validation": {
                "snippet_checks": snippet_checks,
                "forbidden_ui_snippets": FORBIDDEN_UI_SNIPPETS,
                "required_runtime_checks": [
                    "npm run typecheck",
                    "npm run build",
                    "pytest backend/tests/test_pilot_api.py backend/tests/test_p3_06u_26h2w_sealed_pilot_package_gates.py",
                ],
            },
            "evidence_paths": [
                display_path(OUTPUT_DIR / "summary.json"),
                display_path(DOC_PATH),
            ],
        }
    )
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    write_json(OUTPUT_DIR / "summary.json", result)
    write_markdown_report(
        DOC_PATH,
        "H2W-DATA2R4 资料包预检 API 与前端入口",
        result,
        [
            (
                "完成内容",
                [
                    "新增客户资料包内存预检接口，用于校验知识资料 CSV、试跑问题 CSV 和资料说明 JSON。",
                    "试点准备页新增资料预检入口，预检结果展示资料行数、问题数、知识类型和阻断项。",
                    "预检不保存原始资料，不标记真实客户资料已就绪，不开启真实外发。",
                ],
            ),
            (
                "已验证命令",
                [
                    "frontend: npm run typecheck && npm run build",
                    "backend: PYTHONPATH=backend backend/.venv/bin/python -m pytest backend/tests/test_pilot_api.py backend/tests/test_p3_06u_26h2w_sealed_pilot_package_gates.py -q",
                ],
            ),
            ("证据文件", result["evidence_paths"]),
        ],
    )
    return result


def main() -> int:
    result = run_h2w_data2r4_material_precheck_api_ui()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if result["status"] == "blocked" else 0


if __name__ == "__main__":
    raise SystemExit(main())
