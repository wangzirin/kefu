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
    write_json,
    write_markdown_report,
)


PHASE = "H2W-PACK9"
SCHEMA_VERSION = "p3-06u-26h2w-pack9.real_customer_rerun_plan.v1"
DEFAULT_OUTPUT_DIR = ROOT / "output/p3_06u_26h2w_pack9_real_customer_rerun_plan"
DOC_PATH = ROOT / "docs/P3-06U-26H2W_PACK9_REAL_CUSTOMER_RERUN_PLAN.md"

PACK8B_SUMMARY = ROOT / "output/p3_06u_26h2w_pack8b_real_material_boundary_lock/summary.json"
DATA2_SUMMARY = ROOT / "output/p3_06u_26h2w_data2_real_customer_material_readiness/summary.json"

WAITING_DATA2_STATUS = "waiting_for_real_customer_materials"
READY_DATA2_STATUSES = {"customer_real_materials_ready", "real_customer_materials_ready"}
PACK8B_WAITING_STATUS = "pack8_boundary_locked_waiting_real_materials"
PACK8B_REFRESH_STATUS = "pack8_boundary_ready_for_customer_data_refresh"

CURRENT_GATE_SCRIPTS = {
    "data2": ROOT / "scripts/check_p3_06u_26h2w_data2_real_customer_material_readiness.py",
    "pack8b": ROOT / "scripts/check_p3_06u_26h2w_pack8b_real_material_boundary_lock.py",
    "kb5_internal_line": ROOT / "scripts/check_p3_06u_26h2w_kb5_customer_knowledge_retest.py",
    "trial2_internal_line": ROOT / "scripts/check_p3_06u_26h2w_trial2_shadow_trial_report.py",
    "fe8": ROOT / "scripts/check_p3_06u_26h2w_fe8_trial_friction_frontend_qa.mjs",
    "pack8": ROOT / "scripts/check_p3_06u_26h2w_pack8_trial_package_v1_1.py",
}


def _read_status(path: Path) -> tuple[dict[str, Any], str]:
    if not path.exists():
        return {}, "missing"
    try:
        payload = read_json(path)
    except json.JSONDecodeError:
        return {}, "invalid_json"
    return payload, str(payload.get("status") or "missing_status")


def _script_matrix(scripts: dict[str, Path]) -> tuple[dict[str, dict[str, Any]], list[str]]:
    matrix: dict[str, dict[str, Any]] = {}
    missing: list[str] = []
    for name, path in scripts.items():
        exists = path.exists()
        matrix[name] = {"path": display_path(path), "exists": exists}
        if not exists:
            missing.append(f"{name} 门禁脚本缺失：{display_path(path)}")
    return matrix, missing


def _rerun_steps() -> list[dict[str, Any]]:
    return [
        {
            "step": "DATA2",
            "title": "真实客户脱敏资料门禁",
            "command": "python3 scripts/check_p3_06u_26h2w_data2_real_customer_material_readiness.py",
            "required_before_run": [
                "customer_materials_received.csv",
                "customer_trial_questions_received.csv",
                "customer_material_manifest_received.json",
            ],
            "stop_gate": "未满 50 条题库、存在 PII/secrets/platform payload、manifest 未声明脱敏，立即阻断。",
        },
        {
            "step": "PACK8B",
            "title": "解除内部样板锁前置检查",
            "command": "python3 scripts/check_p3_06u_26h2w_pack8b_real_material_boundary_lock.py",
            "required_before_run": ["DATA2 状态必须是 customer_real_materials_ready"],
            "stop_gate": "PACK8 仍写成内部样板候选时只能提示刷新，不允许写成客户数据包已完成。",
        },
        {
            "step": "KB6",
            "title": "真实客户知识导入与复测",
            "command": "待实现：DATA2 -> 客户知识复测，不能复用内部 DATA1 路径冒充客户数据。",
            "required_before_run": ["DATA2 真实资料 ready", "四层知识类型齐全", "来源引用齐全"],
            "stop_gate": "只测检索命中、不测最终客服答案，或系统替客户填写确认结果，立即阻断。",
        },
        {
            "step": "TRIAL3",
            "title": "真实客户资料影子试跑质量报告",
            "command": "待实现：DATA2/KB6 -> 最终答案、引用、转人工、安全边界、成本估算。",
            "required_before_run": ["KB6 复测通过", "真实外发仍关闭"],
            "stop_gate": "无引用高置信回答、禁用承诺复述、内部样板被写成客户签收，立即阻断。",
        },
        {
            "step": "FE9",
            "title": "客户数据状态前端复测",
            "command": "待实现：浏览器真实登录检查试点准备、知识中心、质量复盘和交付档案状态。",
            "required_before_run": ["TRIAL3 报告生成", "客户可见文案无工程词和越界完成态"],
            "stop_gate": "假按钮、假完成态、客户看不懂下一步，立即阻断。",
        },
        {
            "step": "PACK9",
            "title": "客户数据试跑交付档案候选",
            "command": "待实现：聚合 DATA2/KB6/TRIAL3/FE9 后生成非敏感档案。",
            "required_before_run": ["交付档案扫描通过", "不包含 secrets、客户原文、平台 payload、临时数据库"],
            "stop_gate": "写成正式客户验收、真实渠道已接通、签名安装包已完成，立即阻断。",
        },
    ]


def run_h2w_pack9_real_customer_rerun_plan(
    *,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    doc_path: Path = DOC_PATH,
    pack8b_summary: Path = PACK8B_SUMMARY,
    data2_summary: Path = DATA2_SUMMARY,
    current_gate_scripts: dict[str, Path] | None = None,
) -> dict[str, Any]:
    blockers: list[str] = []
    warnings: list[str] = []
    scripts = current_gate_scripts or CURRENT_GATE_SCRIPTS

    pack8b_payload, pack8b_status = _read_status(pack8b_summary)
    data2_payload, data2_status = _read_status(data2_summary)

    if pack8b_status in {"missing", "invalid_json", "missing_status", "blocked"}:
        blockers.append(f"PACK8B summary 不可作为前置证据：{display_path(pack8b_summary)} ({pack8b_status})")
    if data2_status in {"missing", "invalid_json", "missing_status", "blocked"}:
        blockers.append(f"DATA2 summary 不可作为前置证据：{display_path(data2_summary)} ({data2_status})")

    if pack8b_payload:
        blockers.extend(boundary_blockers("pack8b", pack8b_payload))
    if data2_payload:
        blockers.extend(boundary_blockers("data2", data2_payload))

    script_matrix, script_blockers = _script_matrix(scripts)
    blockers.extend(script_blockers)

    data2_waiting = data2_status == WAITING_DATA2_STATUS
    data2_ready = data2_status in READY_DATA2_STATUSES
    data2_readiness_ready = data2_payload.get("readiness", {}).get("customer_real_materials_ready") is True
    data2_customer_data_used = data2_payload.get("customer_data_used") is True

    if data2_waiting:
        if pack8b_status != PACK8B_WAITING_STATUS:
            blockers.append(f"DATA2 等待真实资料时，PACK8B 必须保持锁定态；当前 PACK8B={pack8b_status}")
        if data2_customer_data_used or data2_readiness_ready:
            blockers.append("DATA2 等待状态不能同时标记 customer_data_used=true 或 customer_real_materials_ready=true")
    elif data2_ready:
        if not data2_readiness_ready or not data2_customer_data_used:
            blockers.append("DATA2 ready 状态必须同时标记 customer_real_materials_ready=true 与 customer_data_used=true")
        if pack8b_status not in {PACK8B_REFRESH_STATUS, PACK8B_WAITING_STATUS}:
            blockers.append(f"DATA2 ready 后 PACK8B 必须处于可刷新或锁定待重跑状态；当前 PACK8B={pack8b_status}")
        if pack8b_status == PACK8B_WAITING_STATUS:
            warnings.append("真实资料已 ready，但 PACK8B 仍是等待锁定态；需要先重跑 PACK8B，再进入 KB6/TRIAL3/PACK9。")
    elif data2_status not in {"missing", "invalid_json", "missing_status", "blocked"}:
        blockers.append(f"DATA2 状态不在 PACK9 可识别集合：{data2_status}")

    ready_for_pack9_planning = not blockers
    ready_to_run_customer_data_chain = ready_for_pack9_planning and data2_ready and pack8b_status == PACK8B_REFRESH_STATUS
    status = (
        "ready_to_run_customer_data_rerun_chain"
        if ready_to_run_customer_data_chain
        else "pack9_plan_ready_waiting_real_customer_materials"
        if ready_for_pack9_planning and data2_waiting
        else "pack9_plan_ready_real_materials_require_pack8b_refresh"
        if ready_for_pack9_planning and data2_ready
        else "blocked"
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    result = base_result(SCHEMA_VERSION, PHASE, status, blockers)
    result.update(
        {
            "warnings": warnings,
            "pack8b_status": pack8b_status,
            "data2_status": data2_status,
            "script_matrix": script_matrix,
            "rerun_steps": _rerun_steps(),
            "customer_data_used": data2_ready and data2_customer_data_used,
            "internal_sample_used": data2_waiting,
            "readiness": {
                "ready_for_pack9_planning": ready_for_pack9_planning,
                "waiting_for_real_customer_materials": data2_waiting,
                "ready_to_run_customer_data_chain": ready_to_run_customer_data_chain,
                "requires_pack8b_refresh": ready_for_pack9_planning and data2_ready and pack8b_status == PACK8B_WAITING_STATUS,
                "requires_kb6_trial3_fe9_pack9_implementation": True,
                "formal_customer_signoff_ready": False,
                "real_platform_send_ready": False,
                "signed_dmg_exe_ready": False,
                "production_sla_ready": False,
            },
            "evidence_paths": [
                display_path(pack8b_summary),
                display_path(data2_summary),
                display_path(doc_path),
                display_path(output_dir / "summary.json"),
            ],
        }
    )
    write_json(output_dir / "summary.json", result)
    write_markdown_report(
        doc_path,
        "H2W-PACK9 真实客户资料重跑计划门禁",
        result,
        [
            (
                "当前前置状态",
                [
                    f"PACK8B：`{pack8b_status}`",
                    f"DATA2：`{data2_status}`",
                    f"可执行计划：`{ready_for_pack9_planning}`",
                    f"可开跑客户数据链：`{ready_to_run_customer_data_chain}`",
                ],
            ),
            (
                "重跑步骤",
                [
                    f"{item['step']}：{item['title']}；停止门禁：{item['stop_gate']}"
                    for item in result["rerun_steps"]
                ],
            ),
            (
                "脚本现状",
                [f"{name}: `{info['exists']}` ({info['path']})" for name, info in script_matrix.items()],
            ),
            (
                "下一步",
                [
                    "真实客户资料未到齐前，只能保持 PACK9 计划 ready，不能生成客户数据版交付档案。",
                    "真实资料到齐后，先重跑 DATA2 和 PACK8B，再新增/执行 KB6、TRIAL3、FE9、PACK9 客户数据链。",
                ],
            ),
            ("警告", warnings),
        ],
    )
    return result


def main() -> int:
    result = run_h2w_pack9_real_customer_rerun_plan()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] != "blocked" else 1


if __name__ == "__main__":
    raise SystemExit(main())
