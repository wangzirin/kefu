#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from lib.h2w_pack8_common import (
    ROOT,
    base_result,
    build_zip,
    display_path,
    read_json,
    scan_archive_candidates,
    write_json,
    write_markdown_report,
)


PHASE = "H2W-PACK10"
SCHEMA_VERSION = "p3-06u-26h2w-pack10.customer_data_trial_package.v1"
DEFAULT_OUTPUT_DIR = ROOT / "output/p3_06u_26h2w_pack10_customer_data_trial_package"
DOC_PATH = ROOT / "docs/P3-06U-26H2W_PACK10_CUSTOMER_DATA_TRIAL_PACKAGE.md"

STAGES = {
    "data2r": {
        "command": [sys.executable, "scripts/check_p3_06u_26h2w_data2r_real_customer_materials.py"],
        "summary": ROOT / "output/p3_06u_26h2w_data2r_real_customer_materials/summary.json",
        "ready": {"customer_real_materials_ready", "internal_sample_materials_ready_for_rehearsal"},
        "waiting": {"waiting_for_real_customer_materials"},
    },
    "kb6": {
        "command": [sys.executable, "scripts/check_p3_06u_26h2w_kb6_real_customer_knowledge_retest.py"],
        "summary": ROOT / "output/p3_06u_26h2w_kb6_real_customer_knowledge_retest/summary.json",
        "ready": {"customer_knowledge_retest_ready_with_customer_data", "customer_knowledge_retest_ready_with_internal_sample"},
        "waiting": {"waiting_for_real_customer_materials"},
    },
    "trial3": {
        "command": [sys.executable, "scripts/check_p3_06u_26h2w_trial3_real_customer_shadow_trial.py"],
        "summary": ROOT / "output/p3_06u_26h2w_trial3_real_customer_shadow_trial/summary.json",
        "ready": {"shadow_trial_ready_with_customer_data", "shadow_trial_ready_with_internal_sample"},
        "waiting": {"waiting_for_real_customer_materials"},
    },
    "fe9": {
        "command": ["node", "scripts/check_p3_06u_26h2w_fe9_customer_data_browser_qa.mjs"],
        "summary": ROOT / "output/p3_06u_26h2w_fe9_customer_data_browser_qa/summary.json",
        "ready": {"passed_customer_data_browser_qa", "passed_internal_sample_browser_qa"},
        "waiting": {"waiting_for_real_customer_materials"},
    },
    "fe10": {
        "command": ["node", "scripts/check_p3_06u_26h2w_fe10_final_product_polish_gate.mjs"],
        "summary": ROOT / "output/p3_06u_26h2w_fe10_final_product_polish_gate/summary.json",
        "ready": {"frontend_final_product_polish_ready"},
        "waiting": set(),
    },
    "channel2": {
        "command": [sys.executable, "scripts/check_p3_06u_26h2w_channel2_personnel_boundary.py"],
        "summary": ROOT / "output/p3_06u_26h2w_channel2_personnel_boundary/summary.json",
        "ready": {"channel_personnel_boundary_ready"},
        "waiting": set(),
    },
    "install6": {
        "command": [sys.executable, "scripts/check_p3_06u_26h2w_install6_trial_installer_experience.py"],
        "summary": ROOT / "output/p3_06u_26h2w_install6_trial_installer_experience/summary.json",
        "ready": {"trial_installer_experience_candidate_ready"},
        "waiting": set(),
    },
}


def _run_stage(code: str, spec: dict[str, Any]) -> dict[str, Any]:
    completed = subprocess.run(spec["command"], cwd=ROOT, text=True, capture_output=True, check=False)
    payload = read_json(spec["summary"])
    return {
        "code": code,
        "command": " ".join(spec["command"]),
        "returncode": completed.returncode,
        "status": payload.get("status", "missing"),
        "path": display_path(spec["summary"]),
        "stdout_tail": completed.stdout[-1200:],
        "stderr_tail": completed.stderr[-1200:],
    }


def run_h2w_pack10_customer_data_trial_package(
    *,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    doc_path: Path = DOC_PATH,
) -> dict[str, Any]:
    blockers: list[str] = []
    stage_results = [_run_stage(code, spec) for code, spec in STAGES.items()]
    statuses = {item["code"]: str(item["status"]) for item in stage_results}
    waiting_for_real_materials = statuses.get("data2r") == "waiting_for_real_customer_materials"
    internal_sample_materials = statuses.get("data2r") == "internal_sample_materials_ready_for_rehearsal"

    for item in stage_results:
        spec = STAGES[item["code"]]
        status = str(item["status"])
        if item["returncode"] != 0:
            blockers.append(f"{item['code']} 门禁命令失败：returncode={item['returncode']}")
        if status in spec["waiting"] and waiting_for_real_materials:
            continue
        if status not in spec["ready"]:
            blockers.append(f"{item['code']} 状态不满足：实际 {status}，期望 {sorted(spec['ready'])}")

    archive_path = output_dir / "customer_data_local_trial_package_v2_candidate.zip"
    archive_files = [
        doc_path,
        ROOT / "docs/P3-06U-26H2W_DATA2R_REAL_CUSTOMER_MATERIALS.md",
        ROOT / "docs/P3-06U-26H2W_KB6_REAL_CUSTOMER_KNOWLEDGE_RETEST.md",
        ROOT / "docs/P3-06U-26H2W_TRIAL3_REAL_CUSTOMER_SHADOW_TRIAL.md",
        ROOT / "docs/P3-06U-26H2W_CHANNEL2_PERSONNEL_BOUNDARY.md",
        ROOT / "docs/P3-06U-26H2W_INSTALL6_TRIAL_INSTALLER_EXPERIENCE.md",
        ROOT / "installers/INSTALL6_SIGNING_READINESS_CHECKLIST.md",
        *(spec["summary"] for spec in STAGES.values()),
    ]
    archive_findings = scan_archive_candidates([path for path in archive_files if path.exists()])
    blockers.extend(archive_findings)

    if waiting_for_real_materials:
        status = "blocked_waiting_real_customer_materials"
    elif blockers:
        status = "blocked"
    elif internal_sample_materials:
        status = "internal_sample_local_trial_package_v2_candidate"
    else:
        status = "customer_data_local_trial_package_v2_candidate"
    if status == "internal_sample_local_trial_package_v2_candidate":
        archive_path = output_dir / "internal_sample_local_trial_package_v2_candidate.zip"

    result = base_result(SCHEMA_VERSION, PHASE, status, blockers if status == "blocked" else [])
    result.update(
        {
            "status": status,
            "blockers": sorted(set(blockers)),
            "customer_data_used": status == "customer_data_local_trial_package_v2_candidate",
            "internal_sample_used": status == "internal_sample_local_trial_package_v2_candidate",
            "stage_results": stage_results,
            "readiness": {
                "pack10_status": status,
                "real_customer_material_status": statuses.get("data2r", "missing"),
                "customer_knowledge_retest_status": statuses.get("kb6", "missing"),
                "shadow_trial_status": statuses.get("trial3", "missing"),
                "frontend_customer_qa_status": statuses.get("fe9", "missing"),
                "frontend_product_polish_status": statuses.get("fe10", "missing"),
                "channel_boundary_status": statuses.get("channel2", "missing"),
                "installer_trial_status": statuses.get("install6", "missing"),
                "real_platform_send_ready": False,
                "formal_customer_signoff_ready": False,
                "signed_dmg_exe_ready": False,
            },
            "archive": {
                "path": display_path(archive_path),
                "created": status in {"customer_data_local_trial_package_v2_candidate", "internal_sample_local_trial_package_v2_candidate"},
                "blocked_by_waiting_real_materials": waiting_for_real_materials,
            },
            "evidence_paths": [display_path(path) for path in archive_files if path.exists()] + [display_path(output_dir / "summary.json")],
        }
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    write_json(output_dir / "summary.json", result)
    write_markdown_report(
        doc_path,
        "H2W-PACK10 五大缺口聚合封包",
        result,
        [
            ("阶段状态", [f"{item['code']}: `{item['status']}`" for item in stage_results]),
            ("档案", [f"路径：`{display_path(archive_path)}`", f"是否生成：`{result['archive']['created']}`"]),
        ],
    )
    if status in {"customer_data_local_trial_package_v2_candidate", "internal_sample_local_trial_package_v2_candidate"}:
        manifest = {
            "schema_version": SCHEMA_VERSION,
            "status": status,
            "stage_statuses": statuses,
            "boundaries": result["boundaries"],
            "not_ready_for": result["not_ready_for"],
        }
        build_zip(archive_path, [path for path in archive_files if path.exists()], manifest)
    return result


def main() -> int:
    result = run_h2w_pack10_customer_data_trial_package()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if result["status"] == "blocked" else 0


if __name__ == "__main__":
    raise SystemExit(main())
