#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from lib.h2w_pack8_common import (
    ROOT,
    base_result,
    display_path,
    read_json,
    scan_text_file,
    write_json,
    write_markdown_report,
)


PHASE = "H2W-PACK8B"
SCHEMA_VERSION = "p3-06u-26h2w-pack8b.real_material_boundary_lock.v1"
DEFAULT_OUTPUT_DIR = ROOT / "output/p3_06u_26h2w_pack8b_real_material_boundary_lock"
DOC_PATH = ROOT / "docs/P3-06U-26H2W_PACK8B_REAL_MATERIAL_BOUNDARY_LOCK.md"

PACK8_SUMMARY = ROOT / "output/p3_06u_26h2w_pack8_trial_package_v1_1/summary.json"
DATA2_SUMMARY = ROOT / "output/p3_06u_26h2w_data2_real_customer_material_readiness/summary.json"
FRONTEND_APP = ROOT / "frontend/src/App.tsx"
FRONTEND_CLIENT = ROOT / "frontend/src/api/client.ts"
PILOT_SERVICE = ROOT / "backend/app/services/pilot.py"
README_PATH = ROOT / "README.md"
MASTER_PLAN = ROOT / "docs/PRODUCTIZATION_MASTER_PLAN_LITE_AND_STANDARD.md"

WAITING_DATA2_STATUS = "waiting_for_real_customer_materials"
READY_DATA2_STATUSES = {"customer_real_materials_ready", "real_customer_materials_ready"}
INTERNAL_PACK8_STATUS = "co_creation_trial_package_v1_1_candidate_with_internal_data"
CUSTOMER_PACK8_STATUS = "co_creation_trial_package_v1_1_candidate_with_customer_data"


def _read_status(path: Path) -> tuple[dict[str, Any], str]:
    if not path.exists():
        return {}, "missing"
    try:
        payload = read_json(path)
    except json.JSONDecodeError:
        return {}, "invalid_json"
    return payload, str(payload.get("status") or "missing_status")


def _file_contains(path: Path, phrase: str) -> bool:
    if not path.exists():
        return False
    return phrase in path.read_text(encoding="utf-8", errors="ignore")


def _missing_phrases(path: Path, phrases: list[str]) -> list[str]:
    return [phrase for phrase in phrases if not _file_contains(path, phrase)]


def _boundary_scan_findings(path: Path, *, allow_absolute_project_paths: bool) -> list[str]:
    findings = scan_text_file(path)
    if allow_absolute_project_paths:
        findings = [item for item in findings if "包含本机绝对隐私路径" not in item]
    return findings


def run_h2w_pack8b_real_material_boundary_lock(
    *,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    doc_path: Path = DOC_PATH,
    pack8_summary: Path = PACK8_SUMMARY,
    data2_summary: Path = DATA2_SUMMARY,
    frontend_app: Path = FRONTEND_APP,
    frontend_client: Path = FRONTEND_CLIENT,
    pilot_service: Path = PILOT_SERVICE,
    readme_path: Path = README_PATH,
    master_plan: Path = MASTER_PLAN,
) -> dict[str, Any]:
    blockers: list[str] = []
    warnings: list[str] = []

    pack8_payload, pack8_status = _read_status(pack8_summary)
    data2_payload, data2_status = _read_status(data2_summary)

    if pack8_status in {"missing", "invalid_json", "missing_status"}:
        blockers.append(f"PACK8 summary 不可用：{display_path(pack8_summary)} ({pack8_status})")
    if data2_status in {"missing", "invalid_json", "missing_status"}:
        blockers.append(f"DATA2 summary 不可用：{display_path(data2_summary)} ({data2_status})")

    pack8_customer_data_used = pack8_payload.get("customer_data_used") is True
    pack8_internal_sample_used = pack8_payload.get("internal_sample_used") is True
    data2_customer_data_used = data2_payload.get("customer_data_used") is True
    data2_real_ready = data2_payload.get("readiness", {}).get("customer_real_materials_ready") is True
    data2_waiting = data2_status == WAITING_DATA2_STATUS

    if data2_waiting:
        if pack8_status != INTERNAL_PACK8_STATUS:
            blockers.append(
                f"DATA2 仍等待真实资料时，PACK8 必须保持内部样板候选；当前 PACK8={pack8_status}"
            )
        if pack8_customer_data_used:
            blockers.append("DATA2 仍等待真实资料时，PACK8 不能标记 customer_data_used=true")
        if not pack8_internal_sample_used:
            blockers.append("DATA2 仍等待真实资料时，PACK8 必须标记 internal_sample_used=true")
        if data2_customer_data_used:
            blockers.append("DATA2 等待状态不应同时标记 customer_data_used=true")
        if data2_real_ready:
            blockers.append("DATA2 等待状态不应同时标记 customer_real_materials_ready=true")
    elif data2_status in READY_DATA2_STATUSES:
        if pack8_status != CUSTOMER_PACK8_STATUS:
            warnings.append("真实资料已 ready，但 PACK8 仍未刷新为客户数据候选包，需要重跑 KB/TRIAL/PACK8。")
    elif data2_status not in {"missing", "invalid_json", "missing_status"}:
        blockers.append(f"DATA2 状态不在可识别集合：{data2_status}")

    expected_phrases = {
        frontend_app: ["real_customer_material_status", "等待真实脱敏资料"],
        frontend_client: ["real_customer_material_status", "real_customer_material_evidence"],
        pilot_service: ["DATA2 接收目录", "real_customer_material_status"],
        readme_path: [WAITING_DATA2_STATUS, "不伪造客户资料"],
        master_plan: [WAITING_DATA2_STATUS, "不伪造客户资料"],
    }
    for path, phrases in expected_phrases.items():
        if not path.exists():
            blockers.append(f"边界文件缺失：{display_path(path)}")
            continue
        missing = _missing_phrases(path, phrases)
        if missing:
            blockers.append(f"{display_path(path)} 缺少 DATA2 边界文案或字段：{', '.join(missing)}")
        blockers.extend(
            _boundary_scan_findings(
                path,
                allow_absolute_project_paths=path in {readme_path, master_plan},
            )
        )

    status = (
        "pack8_boundary_locked_waiting_real_materials"
        if data2_waiting
        else "pack8_boundary_ready_for_customer_data_refresh"
        if data2_status in READY_DATA2_STATUSES
        else "blocked"
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    result = base_result(SCHEMA_VERSION, PHASE, status, blockers)
    result.update(
        {
            "warnings": warnings,
            "pack8_status": pack8_status,
            "data2_status": data2_status,
            "customer_data_used": pack8_customer_data_used,
            "internal_sample_used": pack8_internal_sample_used,
            "readiness": {
                "pack8_boundary_locked": not blockers,
                "waiting_real_customer_materials": data2_waiting,
                "pack8_customer_data_refresh_required": bool(warnings),
                "formal_customer_signoff_ready": False,
                "real_platform_send_ready": False,
                "signed_dmg_exe_ready": False,
                "production_sla_ready": False,
            },
            "evidence_paths": [
                display_path(pack8_summary),
                display_path(data2_summary),
                display_path(doc_path),
                display_path(output_dir / "summary.json"),
            ],
            "checked_files": [display_path(path) for path in expected_phrases],
        }
    )
    write_json(output_dir / "summary.json", result)
    write_markdown_report(
        doc_path,
        "H2W-PACK8B 真实资料边界锁",
        result,
        [
            (
                "状态核验",
                [
                    f"PACK8：`{pack8_status}`",
                    f"DATA2：`{data2_status}`",
                    f"PACK8 customer_data_used：`{pack8_customer_data_used}`",
                    f"PACK8 internal_sample_used：`{pack8_internal_sample_used}`",
                ],
            ),
            (
                "检查范围",
                [display_path(path) for path in expected_phrases],
            ),
            (
                "下一步",
                [
                    "真实客户资料未到齐前，PACK8 继续保持内部样板候选口径。",
                    "客户资料到齐后，先重跑 DATA2，再重跑知识复测、影子试跑和 PACK8/PACK9 档案。",
                ],
            ),
            ("警告", warnings),
        ],
    )
    return result


def main() -> int:
    result = run_h2w_pack8b_real_material_boundary_lock()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] != "blocked" else 1


if __name__ == "__main__":
    raise SystemExit(main())
