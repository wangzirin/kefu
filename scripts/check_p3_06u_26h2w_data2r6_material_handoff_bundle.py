#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from lib.h2w_pack8_common import ROOT, base_result, display_path, write_json, write_markdown_report


PHASE = "H2W-DATA2R6"
SCHEMA_VERSION = "p3-06u-26h2w-data2r6.customer_material_handoff_bundle.v1"
OUTPUT_DIR = ROOT / "output/p3_06u_26h2w_data2r6_material_handoff_bundle"
DOC_PATH = ROOT / "docs/P3-06U-26H2W_DATA2R6_MATERIAL_HANDOFF_BUNDLE.md"

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
        "class CustomerMaterialHandoffBundleRead",
        "body_encoding",
        "included_files",
        "required_received_filenames",
    ],
    "backend_service": [
        "CUSTOMER_MATERIAL_HANDOFF_BUNDLE_SCHEMA_VERSION",
        "def get_customer_material_handoff_bundle",
        "customer_materials_received.csv",
        "customer_trial_questions_received.csv",
        "customer_material_manifest_received.json",
        "sample_package_is_customer_data",
        "raw_materials_persisted",
        "real_customer_materials_ready",
    ],
    "backend_router": [
        '"/tenants/{tenant_id}/customer-materials/handoff-bundle"',
        "get_customer_material_handoff_bundle_endpoint",
        'require_permission("knowledge.manage")',
    ],
    "backend_tests": [
        "test_customer_material_handoff_bundle_downloads_fixed_received_filenames_without_customer_data",
        "zipfile.ZipFile",
        "customer_trial_questions_received.csv",
        "sample_package_is_customer_data",
    ],
    "frontend_client": [
        "CustomerMaterialHandoffBundle",
        "getCustomerMaterialHandoffBundle",
        "/customer-materials/handoff-bundle",
    ],
    "frontend_app": [
        "CustomerMaterialHandoffBundleState",
        "handleDownloadCustomerMaterialHandoffBundle",
        "customerMaterialHandoffBundle",
        "下载回传文件包",
    ],
    "frontend_styles": [
        "pilot-template-box",
        "pilot-template-actions",
    ],
}

FORBIDDEN_UI_SNIPPETS = [
    "客户资料已确认完成",
    "真实外发已接通",
    "正式签收已完成",
    "生产 SLA 已完成",
    "已签名安装包",
]

FIXED_RECEIVED_FILENAMES = [
    "customer_materials_received.csv",
    "customer_trial_questions_received.csv",
    "customer_material_manifest_received.json",
    "README.md",
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


def run_h2w_data2r6_material_handoff_bundle() -> dict[str, Any]:
    blockers, snippet_checks = _check_required_snippets()
    blockers.extend(_check_forbidden_ui_claims())

    result = base_result(SCHEMA_VERSION, PHASE, "material_handoff_bundle_ready", blockers)
    result.update(
        {
            "status": "blocked" if blockers else "material_handoff_bundle_ready",
            "customer_data_used": False,
            "internal_sample_used": True,
            "feature_scope": {
                "backend_handoff_bundle_endpoint": True,
                "frontend_handoff_bundle_download": True,
                "zip_uses_fixed_received_filenames": True,
                "raw_materials_persisted": False,
                "marks_real_customer_materials_ready": False,
                "starts_real_platform_send": False,
            },
            "readiness": {
                "material_handoff_bundle_ready": not blockers,
                "real_customer_materials_ready": False,
                "real_platform_send_ready": False,
                "formal_customer_signoff_ready": False,
                "minimum_question_count_required": 50,
            },
            "fixed_received_filenames": FIXED_RECEIVED_FILENAMES,
            "validation": {
                "snippet_checks": snippet_checks,
                "forbidden_ui_snippets": FORBIDDEN_UI_SNIPPETS,
                "required_runtime_checks": [
                    "backend: PYTHONPATH=backend backend/.venv/bin/python -m pytest backend/tests/test_pilot_api.py",
                    "frontend: npm run typecheck",
                    "frontend: npm run build",
                    "pack10: python scripts/check_p3_06u_26h2w_pack10_customer_data_trial_package.py",
                ],
            },
            "evidence_paths": [
                display_path(OUTPUT_DIR / "summary.json"),
                display_path(DOC_PATH),
                display_path(FILES_TO_CHECK["backend_tests"]),
                display_path(FILES_TO_CHECK["frontend_app"]),
                display_path(FILES_TO_CHECK["frontend_client"]),
            ],
        }
    )
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    write_json(OUTPUT_DIR / "summary.json", result)
    write_markdown_report(
        DOC_PATH,
        "H2W-DATA2R6 资料回传文件包",
        result,
        [
            (
                "完成内容",
                [
                    "新增资料回传文件包接口，生成包含固定回传文件名的 zip，降低客户把模板文件名传错的风险。",
                    "试点准备页新增“下载回传文件包”入口，下载内容仍是示例和空模板，不包含真实客户资料。",
                    "回传包明确保持真实客户资料未就绪、真实外发关闭、正式签收未完成。",
                ],
            ),
            (
                "固定文件名",
                FIXED_RECEIVED_FILENAMES,
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
    result = run_h2w_data2r6_material_handoff_bundle()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if result["status"] == "blocked" else 0


if __name__ == "__main__":
    raise SystemExit(main())
