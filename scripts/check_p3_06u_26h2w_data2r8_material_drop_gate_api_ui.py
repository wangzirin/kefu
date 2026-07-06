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
    summary_status,
    write_json,
    write_markdown_report,
)


PHASE = "H2W-DATA2R8"
SCHEMA_VERSION = "p3-06u-26h2w-data2r8.material_drop_gate_api_ui.v1"
OUTPUT_DIR = ROOT / "output/p3_06u_26h2w_data2r8_material_drop_gate_api_ui"
DOC_PATH = ROOT / "docs/P3-06U-26H2W_DATA2R8_MATERIAL_DROP_GATE_API_UI.md"

BACKEND_SCHEMA = ROOT / "backend/app/schemas/pilot.py"
BACKEND_SERVICE = ROOT / "backend/app/services/pilot.py"
BACKEND_TESTS = ROOT / "backend/tests/test_pilot_api.py"
FRONTEND_CLIENT = ROOT / "frontend/src/api/client.ts"
FRONTEND_APP = ROOT / "frontend/src/App.tsx"
DATA2R7_SUMMARY = ROOT / "output/p3_06u_26h2w_data2r7_received_file_drop_gate/summary.json"

ACCEPTED_DATA2R7_STATUSES = {
    "received_file_drop_ready_waiting_customer_files",
    "received_files_present_pending_data2r_validation",
    "received_files_validated_ready_for_pack12_rerun",
    "received_internal_sample_files_validated_ready_for_pack12_rerun",
}

REQUIRED_SNIPPETS = {
    "backend_schema": [
        "material_drop_gate_status",
        "material_drop_gate_evidence",
    ],
    "backend_service": [
        "p3_06u_26h2w_data2r7_received_file_drop_gate/summary.json",
        '"material_drop_gate"',
        'material_drop_gate_status=five_gap_evidence["material_drop_gate"][0]',
        'material_drop_gate_evidence=five_gap_evidence["material_drop_gate"][1]',
    ],
    "backend_tests": [
        "material_drop_gate_status",
        "material_drop_gate_evidence",
    ],
    "frontend_client": [
        "material_drop_gate_status",
        "material_drop_gate_evidence",
    ],
    "frontend_app": [
        "回传文件落位",
        "received_file_drop_ready_waiting_customer_files",
        "received_files_present_pending_data2r_validation",
        "received_internal_sample_files_validated_ready_for_pack12_rerun",
        "文件已落位，待校验",
    ],
}


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _check_snippets(files: dict[str, Path]) -> tuple[list[str], list[dict[str, Any]]]:
    blockers: list[str] = []
    checks: list[dict[str, Any]] = []
    for key, snippets in REQUIRED_SNIPPETS.items():
        path = files[key]
        if not path.exists():
            blockers.append(f"{key} 文件缺失：{display_path(path)}")
            checks.append({"name": key, "path": display_path(path), "passed": False, "missing": snippets})
            continue
        text = _read(path)
        missing = [snippet for snippet in snippets if snippet not in text]
        if missing:
            blockers.append(f"{key} 缺少必要片段：{', '.join(missing)}")
        checks.append({"name": key, "path": display_path(path), "passed": not missing, "missing": missing})
    return blockers, checks


def _payload(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return read_json(path)
    except json.JSONDecodeError:
        return {}


def run_h2w_data2r8_material_drop_gate_api_ui(
    *,
    output_dir: Path = OUTPUT_DIR,
    doc_path: Path = DOC_PATH,
    backend_schema: Path = BACKEND_SCHEMA,
    backend_service: Path = BACKEND_SERVICE,
    backend_tests: Path = BACKEND_TESTS,
    frontend_client: Path = FRONTEND_CLIENT,
    frontend_app: Path = FRONTEND_APP,
    data2r7_summary: Path = DATA2R7_SUMMARY,
) -> dict[str, Any]:
    files = {
        "backend_schema": backend_schema,
        "backend_service": backend_service,
        "backend_tests": backend_tests,
        "frontend_client": frontend_client,
        "frontend_app": frontend_app,
    }
    blockers, snippet_checks = _check_snippets(files)

    data2r7_status = summary_status(data2r7_summary)
    data2r7_payload = _payload(data2r7_summary)
    if not data2r7_status["present"]:
        blockers.append(f"DATA2R7 summary 缺失：{data2r7_status['path']}")
    elif data2r7_status["status"] == "invalid_json":
        blockers.append(f"DATA2R7 summary 不是有效 JSON：{data2r7_status['path']}")
    elif data2r7_status["status"] not in ACCEPTED_DATA2R7_STATUSES:
        blockers.append(
            f"DATA2R7 状态不可用于前端展示：实际 {data2r7_status['status']}，期望 {sorted(ACCEPTED_DATA2R7_STATUSES)}"
        )
    blockers.extend(boundary_blockers("data2r7", data2r7_payload))

    status = "material_drop_gate_api_ui_ready"
    result = base_result(SCHEMA_VERSION, PHASE, status, blockers)
    result.update(
        {
            "status": "blocked" if blockers else status,
            "customer_data_used": bool(data2r7_payload.get("customer_data_used") is True),
            "internal_sample_used": bool(data2r7_payload.get("internal_sample_used") is True),
            "snippet_checks": snippet_checks,
            "upstreams": {"data2r7": data2r7_status},
            "readiness": {
                "pilot_readiness_exposes_material_drop_gate": not any(
                    item["name"] in {"backend_schema", "backend_service", "frontend_client"} and not item["passed"]
                    for item in snippet_checks
                ),
                "frontend_displays_material_drop_gate": not any(
                    item["name"] == "frontend_app" and not item["passed"] for item in snippet_checks
                ),
                "received_file_drop_gate_ready": data2r7_status["status"] in ACCEPTED_DATA2R7_STATUSES,
                "real_customer_materials_ready": bool(
                    data2r7_status["status"] == "received_files_validated_ready_for_pack12_rerun"
                    and data2r7_payload.get("readiness", {}).get("customer_real_materials_ready") is True
                ),
                "internal_sample_materials_ready": bool(
                    data2r7_status["status"] == "received_internal_sample_files_validated_ready_for_pack12_rerun"
                    and data2r7_payload.get("readiness", {}).get("internal_sample_materials_ready") is True
                ),
                "real_platform_send_ready": False,
                "formal_customer_signoff_ready": False,
                "signed_dmg_exe_ready": False,
            },
            "evidence_paths": [
                display_path(backend_schema),
                display_path(backend_service),
                display_path(frontend_client),
                display_path(frontend_app),
                display_path(data2r7_summary),
                display_path(output_dir / "summary.json"),
                display_path(doc_path),
            ],
        }
    )
    write_json(output_dir / "summary.json", result)
    write_markdown_report(
        doc_path,
        "H2W-DATA2R8 回传落位状态接入",
        result,
        [
            (
                "接入范围",
                [
                    "后端 pilot-readiness 新增回传文件落位状态和证据字段。",
                    "前端试点准备页展示资料包、资料门禁和回传文件落位三段状态。",
                    "五大缺口卡片新增回传落位卡片，避免客户资料等待态被隐藏。",
                ],
            ),
            ("DATA2R7 上游", [f"状态：`{data2r7_status['status']}`", f"路径：`{data2r7_status['path']}`"]),
            (
                "边界",
                [
                    "本阶段只展示 DATA2R7 的机器门禁，不生成、不改写、不伪造真实客户资料。",
                    "真实资料仍需客户按固定文件名回传并通过 DATA2/DATA2R 内容校验。",
                    "真实外发、真实渠道、正式签收、生产 SLA 和签名安装包继续关闭或未完成。",
                ],
            ),
        ],
    )
    return result


def main() -> int:
    result = run_h2w_data2r8_material_drop_gate_api_ui()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if result["status"] == "blocked" else 0


if __name__ == "__main__":
    raise SystemExit(main())
