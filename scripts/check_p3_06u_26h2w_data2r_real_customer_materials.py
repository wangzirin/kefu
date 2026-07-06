#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from check_p3_06u_26h2w_data2_real_customer_material_readiness import (
    DEFAULT_OUTPUT_DIR as DATA2_OUTPUT_DIR,
    INTERNAL_SAMPLE_STATUS,
    READY_STATUS,
    run_h2w_data2_real_customer_material_readiness,
)
from lib.h2w_pack8_common import (
    ROOT,
    base_result,
    display_path,
    read_json,
    write_json,
    write_markdown_report,
)


PHASE = "H2W-DATA2R"
SCHEMA_VERSION = "p3-06u-26h2w-data2r.real_customer_materials.v1"
DEFAULT_OUTPUT_DIR = ROOT / "output/p3_06u_26h2w_data2r_real_customer_materials"
DOC_PATH = ROOT / "docs/P3-06U-26H2W_DATA2R_REAL_CUSTOMER_MATERIALS.md"
DATA2_SUMMARY = DATA2_OUTPUT_DIR / "summary.json"

WAITING_STATUS = "waiting_for_real_customer_materials"


def _data2_payload() -> dict[str, Any]:
    if not DATA2_SUMMARY.exists():
        run_h2w_data2_real_customer_material_readiness()
    return read_json(DATA2_SUMMARY)


def run_h2w_data2r_real_customer_materials(
    *,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    doc_path: Path = DOC_PATH,
) -> dict[str, Any]:
    data2 = _data2_payload()
    data2_status = str(data2.get("status") or "missing")
    blockers: list[str] = []

    if data2_status in {READY_STATUS, INTERNAL_SAMPLE_STATUS}:
        status = READY_STATUS
        if data2_status == INTERNAL_SAMPLE_STATUS:
            status = INTERNAL_SAMPLE_STATUS
    elif data2_status == WAITING_STATUS:
        status = WAITING_STATUS
    else:
        status = "blocked_real_customer_materials_invalid"
        blockers.append(f"DATA2 真实资料门禁状态不可用：{data2_status}")

    metrics = data2.get("metrics") if isinstance(data2.get("metrics"), dict) else {}
    missing_files = data2.get("missing_received_files") if isinstance(data2.get("missing_received_files"), list) else []
    result = base_result(SCHEMA_VERSION, PHASE, status, blockers)
    result.update(
        {
            "status": "blocked_real_customer_materials_invalid" if blockers else status,
            "upstreams": {
                "data2": {
                    "path": display_path(DATA2_SUMMARY),
                    "status": data2_status,
                    "blocker_count": len(data2.get("blockers", [])) if isinstance(data2.get("blockers"), list) else 0,
                }
            },
            "metrics": metrics,
            "missing_received_files": missing_files,
            "customer_data_used": status == READY_STATUS and not blockers,
            "internal_sample_used": status == INTERNAL_SAMPLE_STATUS and not blockers,
            "evidence_paths": [
                display_path(DATA2_SUMMARY),
                display_path(output_dir / "summary.json"),
                display_path(doc_path),
            ],
            "readiness": {
                "customer_real_materials_ready": status == READY_STATUS and not blockers,
                "internal_sample_materials_ready": status == INTERNAL_SAMPLE_STATUS and not blockers,
                "waiting_for_real_customer_materials": status == WAITING_STATUS and not blockers,
                "minimum_question_count_required": 50,
                "real_platform_send_ready": False,
                "formal_customer_signoff_ready": False,
            },
        }
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    write_json(output_dir / "summary.json", result)
    write_markdown_report(
        doc_path,
        "H2W-DATA2R 真实客户资料接收门禁",
        result,
        [
            (
                "资料状态",
                [
                    f"DATA2 状态：`{data2_status}`",
                    "真实客户资料未回传时只能停在等待态，不能使用内部样板冒充客户资料。",
                    "真实资料 ready 后，后续 KB6/TRIAL3/PACK10 才允许进入客户数据链。",
                ],
            ),
            ("缺失回传文件", [str(item) for item in missing_files]),
            ("指标", [f"{key}: {value}" for key, value in metrics.items()]),
        ],
    )
    return result


def main() -> int:
    result = run_h2w_data2r_real_customer_materials()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if result["status"] == "blocked_real_customer_materials_invalid" else 0


if __name__ == "__main__":
    raise SystemExit(main())
