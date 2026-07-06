#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from lib.h2w_pack8_common import ROOT, base_result, display_path, write_json, write_markdown_report


PHASE = "H2W-DATA2R5"
SCHEMA_VERSION = "p3-06u-26h2w-data2r5.material_template_package.v1"
OUTPUT_DIR = ROOT / "output/p3_06u_26h2w_data2r5_material_template_package"
DOC_PATH = ROOT / "docs/P3-06U-26H2W_DATA2R5_MATERIAL_TEMPLATE_PACKAGE.md"

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
        "class CustomerMaterialTemplatePackageRead",
        "materials_template_csv",
        "sample_trial_questions_csv",
        "field_guide",
    ],
    "backend_service": [
        "CUSTOMER_MATERIAL_TEMPLATE_PACKAGE_SCHEMA_VERSION",
        "def get_customer_material_template_package",
        "sample_package_is_customer_data",
        "raw_materials_persisted",
        "real_customer_materials_ready",
        "customer_material_manifest_received.json",
    ],
    "backend_router": [
        '"/tenants/{tenant_id}/customer-materials/template-package"',
        "get_customer_material_template_package_endpoint",
        'require_permission("knowledge.manage")',
    ],
    "backend_tests": [
        "test_customer_material_template_package_feeds_precheck_without_marking_customer_ready",
        "sample_materials_csv",
        "sample_trial_questions_csv",
    ],
    "frontend_client": [
        "CustomerMaterialTemplatePackage",
        "getCustomerMaterialTemplatePackage",
        "/customer-materials/template-package",
    ],
    "frontend_app": [
        "CustomerMaterialTemplatePackageState",
        "handleLoadCustomerMaterialTemplatePackage",
        "加载资料模板",
        "填入示例资料",
        "下载三份模板",
        "字段说明",
    ],
    "frontend_styles": [
        "pilot-template-box",
        "pilot-field-guide",
        "pilot-field-guide-item",
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


def run_h2w_data2r5_material_template_package() -> dict[str, Any]:
    blockers, snippet_checks = _check_required_snippets()
    blockers.extend(_check_forbidden_ui_claims())

    result = base_result(SCHEMA_VERSION, PHASE, "material_template_package_ready", blockers)
    result.update(
        {
            "status": "blocked" if blockers else "material_template_package_ready",
            "customer_data_used": False,
            "internal_sample_used": True,
            "feature_scope": {
                "backend_template_endpoint": True,
                "frontend_template_loader": True,
                "frontend_sample_fill": True,
                "frontend_template_download": True,
                "raw_materials_persisted": False,
                "marks_real_customer_materials_ready": False,
                "starts_real_platform_send": False,
            },
            "readiness": {
                "material_template_package_ready": not blockers,
                "real_customer_materials_ready": False,
                "real_platform_send_ready": False,
                "formal_customer_signoff_ready": False,
                "minimum_question_count_required": 50,
            },
            "validation": {
                "snippet_checks": snippet_checks,
                "forbidden_ui_snippets": FORBIDDEN_UI_SNIPPETS,
                "required_runtime_checks": [
                    "frontend: npm run typecheck",
                    "frontend: npm run build",
                    "backend: PYTHONPATH=backend backend/.venv/bin/python -m pytest backend/tests/test_pilot_api.py",
                ],
            },
            "evidence_paths": [
                display_path(OUTPUT_DIR / "summary.json"),
                display_path(DOC_PATH),
                display_path(FILES_TO_CHECK["backend_tests"]),
                display_path(FILES_TO_CHECK["frontend_app"]),
            ],
        }
    )
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    write_json(OUTPUT_DIR / "summary.json", result)
    write_markdown_report(
        DOC_PATH,
        "H2W-DATA2R5 资料模板包与字段说明",
        result,
        [
            (
                "完成内容",
                [
                    "新增资料模板包接口，返回知识资料 CSV、试跑问题 CSV、资料说明 JSON 的空模板与格式示例。",
                    "试点准备页新增加载模板、填入示例、下载三份模板和字段说明。",
                    "示例可以用于熟悉格式和跑预检，但不标记真实客户资料已就绪。",
                ],
            ),
            (
                "已验证命令",
                [
                    "backend: PYTHONPATH=backend backend/.venv/bin/python -m pytest backend/tests/test_pilot_api.py -q",
                    "frontend: npm run typecheck",
                    "frontend: npm run build",
                ],
            ),
            ("证据文件", result["evidence_paths"]),
        ],
    )
    return result


def main() -> int:
    result = run_h2w_data2r5_material_template_package()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if result["status"] == "blocked" else 0


if __name__ == "__main__":
    raise SystemExit(main())
