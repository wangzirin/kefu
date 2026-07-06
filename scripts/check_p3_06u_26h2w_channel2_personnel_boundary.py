#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

from lib.h2w_pack8_common import ROOT, base_result, display_path, write_json, write_markdown_report


PHASE = "H2W-CHANNEL2"
SCHEMA_VERSION = "p3-06u-26h2w-channel2.personnel_boundary.v1"
DEFAULT_OUTPUT_DIR = ROOT / "output/p3_06u_26h2w_channel2_personnel_boundary"
DOC_PATH = ROOT / "docs/P3-06U-26H2W_CHANNEL2_PERSONNEL_BOUNDARY.md"
CHANNEL_COMPONENT = ROOT / "frontend/src/components/channels/ChannelConnectorCenterPanel.tsx"
STYLES = ROOT / "frontend/src/styles.css"

REQUIRED_TEXT = [
    "人员与边界",
    "接待人员",
    "负责人",
    "管理员",
    "知识维护人",
    "运维联系人",
    "官方接入条件",
    "未接通原因",
    "企业微信",
    "微信客服",
    "公众号",
    "抖音",
    "淘宝",
    "京东",
    "拼多多",
    "小红书",
]
FORBIDDEN_TEXT = ["已接通全渠道", "真实外发已开启", "真实渠道已接通", "个人号外挂正式交付"]
REQUIRED_STYLE_MARKERS = ["channel-personnel-boundary", "channel-role-grid", "channel-boundary-checklist"]


def run_h2w_channel2_personnel_boundary(
    *,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    doc_path: Path = DOC_PATH,
) -> dict:
    component = CHANNEL_COMPONENT.read_text(encoding="utf-8") if CHANNEL_COMPONENT.exists() else ""
    styles = STYLES.read_text(encoding="utf-8") if STYLES.exists() else ""
    blockers: list[str] = []
    for marker in REQUIRED_TEXT:
        if marker not in component:
            blockers.append(f"渠道人员边界页缺少文案或数据：{marker}")
    for marker in REQUIRED_STYLE_MARKERS:
        if marker not in component and marker not in styles:
            blockers.append(f"渠道人员边界页缺少结构或样式：{marker}")
    for phrase in FORBIDDEN_TEXT:
        if phrase in component:
            blockers.append(f"渠道页包含越界完成口径：{phrase}")

    result = base_result(SCHEMA_VERSION, PHASE, "channel_personnel_boundary_ready", blockers)
    result.update(
        {
            "customer_data_used": False,
            "internal_sample_used": False,
            "evidence_paths": [display_path(CHANNEL_COMPONENT), display_path(STYLES), display_path(doc_path)],
            "readiness": {
                "channel_boundary_status": "channel_personnel_boundary_ready" if not blockers else "blocked",
                "real_platform_send_ready": False,
                "official_channel_connected": False,
                "personnel_boundary_visible": not blockers,
            },
            "covered_channels": ["企业微信", "微信客服", "公众号", "抖音", "淘宝", "京东", "拼多多", "小红书"],
            "covered_roles": ["负责人", "接待人员", "管理员", "知识维护人", "运维联系人"],
        }
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    write_json(output_dir / "summary.json", result)
    write_markdown_report(
        doc_path,
        "H2W-CHANNEL2 渠道人员配置与边界页",
        result,
        [
            ("覆盖角色", result["covered_roles"]),
            ("覆盖渠道", result["covered_channels"]),
            ("证据", result["evidence_paths"]),
        ],
    )
    return result


def main() -> int:
    result = run_h2w_channel2_personnel_boundary()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if result["status"] == "blocked" else 0


if __name__ == "__main__":
    raise SystemExit(main())
