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
    display_path,
    read_json,
    scan_archive_candidates,
    summary_status,
    write_json,
    write_markdown_report,
)


PHASE = "H2W-PACK11"
SCHEMA_VERSION = "p3-06u-26h2w-pack11.local_trial_v3_candidate.v1"
OUTPUT_DIR = ROOT / "output/p3_06u_26h2w_pack11_local_trial_v3_candidate"
DOC_PATH = ROOT / "docs/P3-06U-26H2W_PACK11_LOCAL_TRIAL_V3_CANDIDATE.md"
CROSS1_DOC = ROOT / "docs/P3-06U-26H2W_CROSS1_FULL_STACK_FACT_BASELINE.md"
FE12_DOC = ROOT / "docs/P3-06U-26H2W_FE12_CUSTOMER_PERSPECTIVE_BROWSER_QA.md"
INSTALL7_DOC = ROOT / "docs/P3-06U-26H2W_INSTALL7_CUSTOMER_MODE_PREPACK_GATE.md"

STAGES = {
    "cross1": {
        "command": [sys.executable, "scripts/check_p3_06u_26h2w_cross1_full_stack_baseline.py"],
        "summary": ROOT / "output/p3_06u_26h2w_cross1_full_stack_baseline/summary.json",
        "ready": {"cross1_full_stack_baseline_ready"},
        "waiting": set(),
    },
    "fact1_data3": {
        "command": [sys.executable, "scripts/check_p3_06u_26h2w_fact1_data3_runtime_facts.py"],
        "summary": ROOT / "output/p3_06u_26h2w_fact1_data3_runtime_facts/summary.json",
        "ready": {"fact1_data3_runtime_facts_ready"},
        "waiting": set(),
    },
    "fe11": {
        "command": ["node", "scripts/check_p3_06u_26h2w_fe11_safe_test_conversation_gate.mjs"],
        "summary": ROOT / "output/p3_06u_26h2w_fe11_safe_test_conversation_gate/summary.json",
        "ready": {"fe11_safe_test_conversation_ready"},
        "waiting": set(),
    },
    "fe12": {
        "command": ["node", "scripts/check_p3_06u_26h2w_fe12_customer_perspective_browser_qa.mjs"],
        "summary": ROOT / "output/p3_06u_26h2w_fe12_customer_perspective_browser_qa/summary.json",
        "ready": {"passed_customer_perspective_browser_qa"},
        "waiting": set(),
    },
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
    "fe10": {
        "command": ["node", "scripts/check_p3_06u_26h2w_fe10_final_product_polish_gate.mjs"],
        "summary": ROOT / "output/p3_06u_26h2w_fe10_final_product_polish_gate/summary.json",
        "ready": {"frontend_final_product_polish_ready"},
        "waiting": set(),
    },
    "install7": {
        "command": [sys.executable, "scripts/check_p3_06u_26h2w_install7_customer_mode_prepack_gate.py"],
        "summary": ROOT / "output/p3_06u_26h2w_install7_customer_mode_prepack_gate/summary.json",
        "ready": {"customer_mode_prepack_gate_ready"},
        "waiting": set(),
    },
    "pack10": {
        "command": [sys.executable, "scripts/check_p3_06u_26h2w_pack10_customer_data_trial_package.py"],
        "summary": ROOT / "output/p3_06u_26h2w_pack10_customer_data_trial_package/summary.json",
        "ready": {"customer_data_local_trial_package_v2_candidate", "internal_sample_local_trial_package_v2_candidate"},
        "waiting": {"blocked_waiting_real_customer_materials"},
    },
}


def _run_stage(code: str, spec: dict[str, Any]) -> dict[str, Any]:
    completed = subprocess.run(spec["command"], cwd=ROOT, text=True, capture_output=True, check=False)
    status = summary_status(spec["summary"])
    return {
        "code": code,
        "command": " ".join(spec["command"]),
        "returncode": completed.returncode,
        "status": status["status"],
        "path": display_path(spec["summary"]),
        "stdout_tail": completed.stdout[-800:],
        "stderr_tail": completed.stderr[-800:],
    }


def run_pack11() -> dict:
    blockers: list[str] = []
    stage_results = [_run_stage(code, spec) for code, spec in STAGES.items()]
    statuses = {item["code"]: str(item["status"]) for item in stage_results}
    waiting_for_real_materials = statuses.get("data2r") == "waiting_for_real_customer_materials"
    internal_sample_materials = statuses.get("data2r") == "internal_sample_materials_ready_for_rehearsal"

    for item in stage_results:
        spec = STAGES[item["code"]]
        actual = str(item["status"])
        if actual in spec["waiting"] and waiting_for_real_materials:
            continue
        if item["returncode"] != 0:
            blockers.append(f"{item['code']} 门禁命令失败：returncode={item['returncode']}")
        if actual not in spec["ready"]:
            blockers.append(f"{item['code']} 状态不满足：实际 {actual}，期望 {sorted(spec['ready'])}")

    archive_candidates = [
        CROSS1_DOC,
        FE12_DOC,
        INSTALL7_DOC,
        DOC_PATH,
        *(spec["summary"] for spec in STAGES.values()),
    ]
    blockers.extend(scan_archive_candidates([path for path in archive_candidates if path.exists()]))

    if waiting_for_real_materials:
        status = "blocked_waiting_real_customer_materials"
    elif blockers:
        status = "blocked"
    elif internal_sample_materials:
        status = "internal_sample_local_trial_package_v3_candidate"
    else:
        status = "customer_data_local_trial_package_v3_candidate"

    result = base_result(SCHEMA_VERSION, PHASE, status, [] if status == "blocked_waiting_real_customer_materials" else blockers)
    result.update(
        {
            "status": status,
            "blockers": sorted(set(blockers)),
            "customer_data_used": status == "customer_data_local_trial_package_v3_candidate",
            "internal_sample_used": waiting_for_real_materials or status == "internal_sample_local_trial_package_v3_candidate",
            "stage_results": stage_results,
            "readiness": {
                "pack11_status": status,
                "real_customer_material_status": statuses.get("data2r", "missing"),
                "knowledge_retest_status": statuses.get("kb6", "missing"),
                "shadow_trial_status": statuses.get("trial3", "missing"),
                "frontend_customer_qa_status": statuses.get("fe12", "missing"),
                "frontend_final_product_status": statuses.get("fe10", "missing"),
                "installer_customer_mode_status": statuses.get("install7", "missing"),
                "real_platform_send_ready": False,
                "formal_customer_signoff_ready": False,
                "signed_dmg_exe_ready": False,
            },
            "evidence_paths": [display_path(path) for path in archive_candidates if path.exists()]
            + [display_path(OUTPUT_DIR / "summary.json")],
        }
    )
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    write_json(OUTPUT_DIR / "summary.json", result)
    write_markdown_report(
        DOC_PATH,
        "H2W-PACK11 本地试跑包 v3 候选",
        result,
        [
            ("阶段状态", [f"{item['code']}: `{item['status']}`" for item in stage_results]),
            ("边界", ["真实外发关闭", "真实渠道未接通", "签名安装包未完成", "没有真实资料时保持等待态"]),
        ],
    )
    return result


def main() -> int:
    result = run_pack11()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if result["status"] == "blocked" else 0


if __name__ == "__main__":
    raise SystemExit(main())
