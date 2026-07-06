#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

from lib.h2w_pack8_common import ROOT, base_result, display_path, write_json, write_markdown_report


PHASE = "H2W-CROSS1"
SCHEMA_VERSION = "p3-06u-26h2w-cross1.full_stack_baseline.v1"
OUTPUT_DIR = ROOT / "output/p3_06u_26h2w_cross1_full_stack_baseline"
DOC_PATH = ROOT / "docs/P3-06U-26H2W_CROSS1_FULL_STACK_FACT_BASELINE.md"

REQUIRED_TEXT = [
    "72-76/100",
    "本地受控试跑",
    "真实客户资料试跑",
    "真实渠道闭环",
    "成熟商用全渠道客服",
    "不能用内部样板冒充客户资料",
    "真实外发关闭",
    "停止门禁",
]


def run_cross1() -> dict:
    blockers: list[str] = []
    text = DOC_PATH.read_text(encoding="utf-8") if DOC_PATH.exists() else ""
    if not DOC_PATH.exists():
        blockers.append(f"缺少 CROSS1 事实基线文档：{display_path(DOC_PATH)}")
    for marker in REQUIRED_TEXT:
        if marker not in text:
            blockers.append(f"CROSS1 文档缺少关键口径：{marker}")
    for phrase in ["真实外发已开启", "全渠道已接通", "客户正式签收已完成"]:
        if phrase in text:
            blockers.append(f"CROSS1 文档包含越界完成口径：{phrase}")

    status = "cross1_full_stack_baseline_ready" if not blockers else "blocked"
    result = base_result(SCHEMA_VERSION, PHASE, status, blockers)
    result.update(
        {
            "customer_data_used": False,
            "internal_sample_used": True,
            "readiness": {
                "local_controlled_trial": "candidate",
                "real_customer_material_trial": "waiting_for_real_customer_materials",
                "real_channel_loop": "not_connected",
                "mature_commercial_omnichannel": "not_ready",
            },
            "evidence_paths": [display_path(DOC_PATH), display_path(OUTPUT_DIR / "summary.json")],
        }
    )
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    write_json(OUTPUT_DIR / "summary.json", result)
    write_markdown_report(
        OUTPUT_DIR / "cross1_gate_report.md",
        "H2W-CROSS1 全维度事实基线门禁",
        result,
        [("证据", result["evidence_paths"])],
    )
    return result


def main() -> int:
    result = run_cross1()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if result["status"] == "blocked" else 0


if __name__ == "__main__":
    raise SystemExit(main())
