#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from lib.h2w_pack8_common import (
    ROOT,
    base_result,
    boundary_blockers,
    display_path,
    read_json,
    sha256,
    summary_status,
    write_json,
    write_markdown_report,
)


PHASE = "H2W-DATA2R7"
SCHEMA_VERSION = "p3-06u-26h2w-data2r7.received_file_drop_gate.v1"
OUTPUT_DIR = ROOT / "output/p3_06u_26h2w_data2r7_received_file_drop_gate"
DOC_PATH = ROOT / "docs/P3-06U-26H2W_DATA2R7_RECEIVED_FILE_DROP_GATE.md"

INTAKE_DIR = ROOT / "evals/p3_06u_26h2w_data2_real_customer_material_readiness"
DATA2_SUMMARY = ROOT / "output/p3_06u_26h2w_data2_real_customer_material_readiness/summary.json"
DATA2R6_SUMMARY = ROOT / "output/p3_06u_26h2w_data2r6_material_handoff_bundle/summary.json"
PACK12_SUMMARY = ROOT / "output/p3_06u_26h2w_pack12_customer_data_rerun_orchestrator/summary.json"

REQUIRED_RECEIVED_FILENAMES = [
    "customer_materials_received.csv",
    "customer_trial_questions_received.csv",
    "customer_material_manifest_received.json",
]
REQUIRED_TEMPLATE_FILENAMES = [
    "customer_materials_real_template.csv",
    "customer_trial_questions_real_template.csv",
    "customer_material_manifest_template.json",
    "README.md",
]

READY_DATA2_STATUS = "customer_real_materials_ready"
INTERNAL_SAMPLE_DATA2_STATUS = "internal_sample_materials_ready_for_rehearsal"
WAITING_DATA2_STATUS = "waiting_for_real_customer_materials"
READY_HANDOFF_STATUS = "material_handoff_bundle_ready"
WAITING_PACK12_STATUS = "waiting_for_real_customer_materials_for_customer_data_rerun"
READY_PACK12_STATUS = "customer_data_rerun_orchestration_ready"
INTERNAL_SAMPLE_PACK12_STATUS = "internal_sample_data_rerun_orchestration_ready"


def _payload(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return read_json(path)
    except json.JSONDecodeError:
        return {}


def _file_state(path: Path) -> dict[str, Any]:
    state: dict[str, Any] = {
        "path": display_path(path),
        "present": path.exists(),
    }
    if path.exists() and path.is_file():
        state.update(
            {
                "size_bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
        )
    return state


def _states_for(directory: Path, filenames: list[str]) -> list[dict[str, Any]]:
    return [_file_state(directory / filename) for filename in filenames]


def _missing_files(states: list[dict[str, Any]]) -> list[str]:
    return [str(item["path"]) for item in states if not item["present"]]


def run_h2w_data2r7_received_file_drop_gate(
    *,
    output_dir: Path = OUTPUT_DIR,
    doc_path: Path = DOC_PATH,
    intake_dir: Path = INTAKE_DIR,
    data2_summary: Path = DATA2_SUMMARY,
    handoff_summary: Path = DATA2R6_SUMMARY,
    pack12_summary: Path = PACK12_SUMMARY,
) -> dict[str, Any]:
    blockers: list[str] = []
    warnings: list[str] = []

    data2 = summary_status(data2_summary)
    handoff = summary_status(handoff_summary)
    pack12 = summary_status(pack12_summary)
    data2_payload = _payload(data2_summary)
    handoff_payload = _payload(handoff_summary)
    pack12_payload = _payload(pack12_summary)

    if not intake_dir.exists():
        blockers.append(f"真实资料接收目录缺失：{display_path(intake_dir)}")

    template_states = _states_for(intake_dir, REQUIRED_TEMPLATE_FILENAMES)
    received_states = _states_for(intake_dir, REQUIRED_RECEIVED_FILENAMES)
    missing_templates = _missing_files(template_states)
    missing_received = _missing_files(received_states)
    received_files_present = not missing_received

    if missing_templates:
        blockers.append(f"真实资料模板或说明缺失：{', '.join(missing_templates)}")
    if handoff["status"] != READY_HANDOFF_STATUS:
        blockers.append(f"DATA2R6 回传文件包状态不满足：实际 {handoff['status']}，期望 {READY_HANDOFF_STATUS}")
    if data2["status"] not in {WAITING_DATA2_STATUS, READY_DATA2_STATUS, INTERNAL_SAMPLE_DATA2_STATUS}:
        blockers.append(f"DATA2 真实资料门禁状态不可用：实际 {data2['status']}")
    if pack12["status"] not in {WAITING_PACK12_STATUS, READY_PACK12_STATUS, INTERNAL_SAMPLE_PACK12_STATUS}:
        blockers.append(
            f"PACK12 重跑编排状态不可用：实际 {pack12['status']}，期望 {WAITING_PACK12_STATUS}、{READY_PACK12_STATUS} 或 {INTERNAL_SAMPLE_PACK12_STATUS}"
        )

    blockers.extend(boundary_blockers("data2", data2_payload))
    blockers.extend(boundary_blockers("data2r6", handoff_payload))
    blockers.extend(boundary_blockers("pack12", pack12_payload))

    if received_files_present and data2["status"] == WAITING_DATA2_STATUS:
        warnings.append("三份固定回传文件已经存在，但 DATA2 当前仍是等待态；请先重跑 DATA2/DATA2R，再重跑 PACK12。")
    if missing_received and data2["status"] == READY_DATA2_STATUS:
        warnings.append("DATA2 显示真实资料已就绪，但当前接收目录存在缺失文件；请复核文件是否被移动或删除。")

    if blockers:
        status = "blocked"
    elif data2["status"] == INTERNAL_SAMPLE_DATA2_STATUS and received_files_present:
        status = "received_internal_sample_files_validated_ready_for_pack12_rerun"
    elif data2["status"] == READY_DATA2_STATUS and received_files_present:
        status = "received_files_validated_ready_for_pack12_rerun"
    elif received_files_present:
        status = "received_files_present_pending_data2r_validation"
    else:
        status = "received_file_drop_ready_waiting_customer_files"

    next_commands = [
        "backend/.venv/bin/python scripts/check_p3_06u_26h2w_data2_real_customer_material_readiness.py",
        "backend/.venv/bin/python scripts/check_p3_06u_26h2w_data2r_real_customer_materials.py",
        "backend/.venv/bin/python scripts/check_p3_06u_26h2w_pack12_customer_data_rerun_orchestrator.py",
    ]
    if status == "received_file_drop_ready_waiting_customer_files":
        next_action = "等待客户按固定文件名回传三份脱敏资料。"
    elif status == "received_files_present_pending_data2r_validation":
        next_action = "重跑 DATA2/DATA2R 校验三份文件，然后再重跑 PACK12。"
    elif status == "received_internal_sample_files_validated_ready_for_pack12_rerun":
        next_action = "直接重跑 PACK12，进入 KB6/TRIAL3/FE9/PACK10/PACK11 内部样板演练链。"
    elif status == "received_files_validated_ready_for_pack12_rerun":
        next_action = "直接重跑 PACK12，进入 KB6/TRIAL3/FE9/PACK10/PACK11 客户数据链。"
    else:
        next_action = "先处理阻断项。"

    result = base_result(SCHEMA_VERSION, PHASE, status, blockers)
    result.update(
        {
            "status": status,
            "blockers": sorted(set(blockers)),
            "warnings": warnings,
            "customer_data_used": status == "received_files_validated_ready_for_pack12_rerun",
            "internal_sample_used": status in {
                "received_file_drop_ready_waiting_customer_files",
                "received_internal_sample_files_validated_ready_for_pack12_rerun",
            },
            "intake_directory": display_path(intake_dir),
            "required_received_filenames": REQUIRED_RECEIVED_FILENAMES,
            "template_file_states": template_states,
            "received_file_states": received_states,
            "missing_received_files": missing_received,
            "upstreams": {
                "data2": data2,
                "data2r6_handoff_bundle": handoff,
                "pack12_rerun_orchestrator": pack12,
            },
            "next_action": next_action,
            "next_commands": next_commands,
            "readiness": {
                "received_file_drop_gate_ready": status != "blocked",
                "waiting_for_customer_files": status == "received_file_drop_ready_waiting_customer_files",
                "received_files_present": received_files_present,
                "needs_data2_validation_rerun": status == "received_files_present_pending_data2r_validation",
                "ready_for_pack12_rerun": status in {
                    "received_files_validated_ready_for_pack12_rerun",
                    "received_internal_sample_files_validated_ready_for_pack12_rerun",
                },
                "customer_real_materials_ready": data2["status"] == READY_DATA2_STATUS and received_files_present and not blockers,
                "internal_sample_materials_ready": data2["status"] == INTERNAL_SAMPLE_DATA2_STATUS and received_files_present and not blockers,
                "real_platform_send_ready": False,
                "formal_customer_signoff_ready": False,
                "signed_dmg_exe_ready": False,
                "minimum_question_count_required": 50,
            },
            "evidence_paths": [
                display_path(data2_summary),
                display_path(handoff_summary),
                display_path(pack12_summary),
                display_path(output_dir / "summary.json"),
                display_path(doc_path),
            ],
        }
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    write_json(output_dir / "summary.json", result)
    write_markdown_report(
        doc_path,
        "H2W-DATA2R7 真实资料回传落位门禁",
        result,
        [
            (
                "当前判断",
                [
                    f"接收目录：`{result['intake_directory']}`",
                    f"DATA2 状态：`{data2['status']}`",
                    f"PACK12 状态：`{pack12['status']}`",
                    f"下一步动作：{next_action}",
                ],
            ),
            ("固定回传文件", REQUIRED_RECEIVED_FILENAMES),
            ("缺失回传文件", missing_received),
            ("重跑命令", next_commands),
            (
                "边界",
                [
                    "本门禁只检查接收目录、固定文件名、上游状态和下一步动作，不生成、不伪造、不改写真实客户资料。",
                    "真实资料到齐后仍需 DATA2/DATA2R 内容校验通过，PACK12 才会运行客户数据链。",
                    "真实外发继续关闭，不生成正式客户签收、生产 SLA 或签名安装包完成态。",
                ],
            ),
            ("警告", warnings),
        ],
    )
    return result


def main() -> int:
    result = run_h2w_data2r7_received_file_drop_gate()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if result["status"] == "blocked" else 0


if __name__ == "__main__":
    raise SystemExit(main())
