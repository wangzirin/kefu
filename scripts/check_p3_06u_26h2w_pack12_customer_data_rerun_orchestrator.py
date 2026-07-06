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
    boundary_blockers,
    display_path,
    scan_archive_candidates,
    summary_status,
    write_json,
    write_markdown_report,
)


PHASE = "H2W-PACK12"
SCHEMA_VERSION = "p3-06u-26h2w-pack12.customer_data_rerun_orchestrator.v1"
OUTPUT_DIR = ROOT / "output/p3_06u_26h2w_pack12_customer_data_rerun_orchestrator"
DOC_PATH = ROOT / "docs/P3-06U-26H2W_PACK12_CUSTOMER_DATA_RERUN_ORCHESTRATOR.md"


STAGES: dict[str, dict[str, Any]] = {
    "data2r": {
        "command": [sys.executable, "scripts/check_p3_06u_26h2w_data2r_real_customer_materials.py"],
        "summary": ROOT / "output/p3_06u_26h2w_data2r_real_customer_materials/summary.json",
        "ready": {"customer_real_materials_ready", "internal_sample_materials_ready_for_rehearsal"},
        "waiting": {"waiting_for_real_customer_materials"},
        "title": "真实客户资料接收门禁",
    },
    "kb6": {
        "command": [sys.executable, "scripts/check_p3_06u_26h2w_kb6_real_customer_knowledge_retest.py"],
        "summary": ROOT / "output/p3_06u_26h2w_kb6_real_customer_knowledge_retest/summary.json",
        "ready": {"customer_knowledge_retest_ready_with_customer_data", "customer_knowledge_retest_ready_with_internal_sample"},
        "waiting": {"waiting_for_real_customer_materials"},
        "title": "真实客户知识导入与复测",
    },
    "trial3": {
        "command": [sys.executable, "scripts/check_p3_06u_26h2w_trial3_real_customer_shadow_trial.py"],
        "summary": ROOT / "output/p3_06u_26h2w_trial3_real_customer_shadow_trial/summary.json",
        "ready": {"shadow_trial_ready_with_customer_data", "shadow_trial_ready_with_internal_sample"},
        "waiting": {"waiting_for_real_customer_materials"},
        "title": "真实客户影子试跑质量报告",
    },
    "fe9": {
        "command": ["node", "scripts/check_p3_06u_26h2w_fe9_customer_data_browser_qa.mjs"],
        "summary": ROOT / "output/p3_06u_26h2w_fe9_customer_data_browser_qa/summary.json",
        "ready": {"passed_customer_data_browser_qa", "passed_internal_sample_browser_qa"},
        "waiting": {"waiting_for_real_customer_materials"},
        "title": "客户资料状态前端复测",
    },
    "pack10": {
        "command": [sys.executable, "scripts/check_p3_06u_26h2w_pack10_customer_data_trial_package.py"],
        "summary": ROOT / "output/p3_06u_26h2w_pack10_customer_data_trial_package/summary.json",
        "ready": {"customer_data_local_trial_package_v2_candidate", "internal_sample_local_trial_package_v2_candidate"},
        "waiting": {"blocked_waiting_real_customer_materials"},
        "title": "五大缺口聚合封包",
    },
    "pack11": {
        "command": [sys.executable, "scripts/check_p3_06u_26h2w_pack11_local_trial_v3_candidate.py"],
        "summary": ROOT / "output/p3_06u_26h2w_pack11_local_trial_v3_candidate/summary.json",
        "ready": {"customer_data_local_trial_package_v3_candidate", "internal_sample_local_trial_package_v3_candidate"},
        "waiting": {"blocked_waiting_real_customer_materials"},
        "title": "本地试跑包 v3 候选聚合",
    },
}


REQUIRED_REAL_MATERIAL_FILES = [
    ROOT / "evals/p3_06u_26h2w_data2_real_customer_material_readiness/customer_materials_received.csv",
    ROOT / "evals/p3_06u_26h2w_data2_real_customer_material_readiness/customer_trial_questions_received.csv",
    ROOT / "evals/p3_06u_26h2w_data2_real_customer_material_readiness/customer_material_manifest_received.json",
]


def _payload(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _run_or_read_stage(code: str, spec: dict[str, Any], *, execute: bool) -> dict[str, Any]:
    completed: subprocess.CompletedProcess[str] | None = None
    if execute:
        completed = subprocess.run(spec["command"], cwd=ROOT, text=True, capture_output=True, check=False)
    status = summary_status(spec["summary"])
    payload = _payload(spec["summary"])
    return {
        "code": code,
        "title": spec["title"],
        "command": " ".join(spec["command"]),
        "executed": execute,
        "returncode": completed.returncode if completed is not None else None,
        "status": status["status"],
        "path": display_path(spec["summary"]),
        "stdout_tail": completed.stdout[-800:] if completed is not None else "",
        "stderr_tail": completed.stderr[-800:] if completed is not None else "",
        "customer_data_used": payload.get("customer_data_used"),
        "internal_sample_used": payload.get("internal_sample_used"),
        "real_platform_send_ready": payload.get("readiness", {}).get("real_platform_send_ready"),
        "formal_customer_signoff_ready": payload.get("readiness", {}).get("formal_customer_signoff_ready"),
    }


def _stage_ready(stage: dict[str, Any], spec: dict[str, Any]) -> bool:
    return str(stage["status"]) in spec["ready"]


def _stage_waiting(stage: dict[str, Any], spec: dict[str, Any]) -> bool:
    return str(stage["status"]) in spec["waiting"]


def _pending_commands() -> list[str]:
    return [" ".join(spec["command"]) for spec in STAGES.values()]


def run_h2w_pack12_customer_data_rerun_orchestrator(
    *,
    output_dir: Path = OUTPUT_DIR,
    doc_path: Path = DOC_PATH,
    stage_specs: dict[str, dict[str, Any]] | None = None,
    execute_commands: bool = True,
) -> dict[str, Any]:
    specs = stage_specs or STAGES
    blockers: list[str] = []
    warnings: list[str] = []
    stage_results: list[dict[str, Any]] = []

    data2r = _run_or_read_stage("data2r", specs["data2r"], execute=execute_commands)
    stage_results.append(data2r)
    data2r_status = str(data2r["status"])
    waiting_for_real_materials = _stage_waiting(data2r, specs["data2r"])
    data_materials_ready = _stage_ready(data2r, specs["data2r"])
    real_materials_ready = data2r_status == "customer_real_materials_ready"
    internal_sample_materials_ready = data2r_status == "internal_sample_materials_ready_for_rehearsal"

    if data2r.get("returncode") not in {None, 0}:
        blockers.append(f"data2r 门禁命令失败：returncode={data2r['returncode']}")

    data2r_payload = _payload(specs["data2r"]["summary"])
    blockers.extend(boundary_blockers("data2r", data2r_payload))

    if waiting_for_real_materials:
        for material_path in REQUIRED_REAL_MATERIAL_FILES:
            if material_path.exists():
                warnings.append(f"DATA2R 仍等待真实资料，但发现固定回传文件存在：{display_path(material_path)}；建议复核文件内容并重跑 DATA2R。")
    elif not data_materials_ready:
        blockers.append(f"data2r 状态不满足：实际 {data2r_status}，期望 {sorted(specs['data2r']['ready'])} 或等待态 {sorted(specs['data2r']['waiting'])}")

    if data_materials_ready:
        for code in ["kb6", "trial3", "fe9", "pack10", "pack11"]:
            stage = _run_or_read_stage(code, specs[code], execute=execute_commands)
            stage_results.append(stage)
            payload = _payload(specs[code]["summary"])
            blockers.extend(boundary_blockers(code, payload))
            if stage.get("returncode") not in {None, 0}:
                blockers.append(f"{code} 门禁命令失败：returncode={stage['returncode']}")
            if not _stage_ready(stage, specs[code]):
                blockers.append(f"{code} 状态不满足：实际 {stage['status']}，期望 {sorted(specs[code]['ready'])}")

    archive_candidates = [doc_path, *(spec["summary"] for spec in specs.values())]
    blockers.extend(scan_archive_candidates([path for path in archive_candidates if path.exists()]))

    if waiting_for_real_materials and not blockers:
        status = "waiting_for_real_customer_materials_for_customer_data_rerun"
    elif blockers:
        status = "blocked"
    elif internal_sample_materials_ready:
        status = "internal_sample_data_rerun_orchestration_ready"
    else:
        status = "customer_data_rerun_orchestration_ready"

    readiness = {
        "pack12_status": status,
        "real_customer_material_status": data2r_status,
        "ready_to_run_customer_data_chain": real_materials_ready and not blockers,
        "ready_to_run_internal_sample_chain": internal_sample_materials_ready and not blockers,
        "waiting_for_real_customer_materials": waiting_for_real_materials,
        "downstream_skipped_until_real_materials_ready": waiting_for_real_materials,
        "customer_data_rerun_complete": status == "customer_data_rerun_orchestration_ready",
        "internal_sample_rerun_complete": status == "internal_sample_data_rerun_orchestration_ready",
        "formal_customer_signoff_ready": False,
        "real_platform_send_ready": False,
        "signed_dmg_exe_ready": False,
        "production_sla_ready": False,
    }

    result = base_result(SCHEMA_VERSION, PHASE, status, [] if status.startswith("waiting_") else blockers)
    result.update(
        {
            "status": status,
            "blockers": sorted(set(blockers)),
            "warnings": warnings,
            "customer_data_used": status == "customer_data_rerun_orchestration_ready",
            "internal_sample_used": waiting_for_real_materials or status == "internal_sample_data_rerun_orchestration_ready",
            "required_real_material_files": [display_path(path) for path in REQUIRED_REAL_MATERIAL_FILES],
            "stage_results": stage_results,
            "pending_commands_after_materials_ready": _pending_commands(),
            "readiness": readiness,
            "evidence_paths": [display_path(path) for path in archive_candidates if path.exists()]
            + [display_path(output_dir / "summary.json")],
        }
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    write_json(output_dir / "summary.json", result)
    write_markdown_report(
        doc_path,
        "H2W-PACK12 真实资料重跑编排门禁",
        result,
        [
            (
                "当前判断",
                [
                    f"真实资料状态：`{data2r_status}`",
                    f"等待真实资料：`{waiting_for_real_materials}`",
                    f"客户数据链完成：`{readiness['customer_data_rerun_complete']}`",
                ],
            ),
            (
                "阶段执行",
                [f"{item['code']}：`{item['status']}`，执行：`{item['executed']}`" for item in stage_results],
            ),
            (
                "真实资料到齐后命令",
                result["pending_commands_after_materials_ready"],
            ),
            (
                "固定回传文件",
                result["required_real_material_files"],
            ),
            (
                "边界",
                [
                    "没有真实资料时只输出等待态，不跑下游客户数据结论。",
                    "真实外发继续关闭，不把草稿或影子试跑写成平台已发送。",
                    "不生成正式客户签收、生产 SLA 或签名安装包完成态。",
                ],
            ),
            ("警告", warnings),
        ],
    )
    return result


def main() -> int:
    result = run_h2w_pack12_customer_data_rerun_orchestrator()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if result["status"] == "blocked" else 0


if __name__ == "__main__":
    raise SystemExit(main())
