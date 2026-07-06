#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "output/p3_06u_26h2w_nc7_frontend_productization"
SUMMARY_PATH = OUTPUT_DIR / "summary.json"
REPORT_PATH = OUTPUT_DIR / "frontend_productization_report.md"


def read_text(relative: str) -> str:
    path = ROOT / relative
    return path.read_text(encoding="utf-8") if path.exists() else ""


def line_count(relative: str) -> int:
    text = read_text(relative)
    return len(text.splitlines()) if text else 0


def has_navigation_group(source: str, label: str, href: str) -> bool:
    group_start = source.find(f'label: "{label}"')
    if group_start < 0:
        return False
    group_end = source.find("\n  {", group_start + 10)
    group_slice = source[group_start : group_end if group_end > group_start else len(source)]
    return f'href: "{href}"' in group_slice


def main() -> int:
    nav = read_text("frontend/src/data/navigation.ts")
    app = read_text("frontend/src/App.tsx")
    conversation = read_text("frontend/src/components/conversation/ConversationWorkbenchPanel.tsx")
    channels = read_text("frontend/src/components/channels/ChannelConnectorCenterPanel.tsx")
    quality = read_text("frontend/src/components/quality/QualityReviewPanel.tsx")

    blockers: list[str] = []
    warnings: list[str] = []

    if not has_navigation_group(nav, "试点准备", "#pilot"):
        blockers.append("试点准备没有成为一级主入口。")
    management_start = nav.find('label: "管理运维"')
    management_slice = nav[management_start:] if management_start >= 0 else ""
    if 'label: "试点准备"' in management_slice and 'label: "账号与本地维护"' in management_slice:
        blockers.append("试点准备仍埋在管理运维分组内。")
    if "账号安全" in nav or 'title: "账号安全"' in app:
        blockers.append("客户可见导航或页面标题仍使用旧称“账号安全”。")
    if 'href="#monthly-ops-report"' in app:
        blockers.append("账号与本地维护仍存在孤儿锚点 #monthly-ops-report。")
    if 'href="#quality?focus=monthly-ops-report"' not in app:
        blockers.append("账号与本地维护没有跳转到质量复盘里的月度运维报告。")

    old_signoff_terms = [
        "试点签收",
        "正式准确率签收",
        "签收前动作",
        "签收边界",
        "<span>签收人</span>",
        "签收人已脱敏",
    ]
    for term in old_signoff_terms:
        if term in quality:
            blockers.append(f"质量复盘仍残留偏正式签收口径：{term}")
    for term in ["试跑确认", "试跑确认前动作", "确认边界", "确认人"]:
        if term not in quality:
            blockers.append(f"质量复盘缺少试跑确认口径：{term}")

    conversation_markers = [
        "生成本地测试会话",
        "service-conversation-list",
        "service-message-stream",
        "转人工",
        "真实外发关闭",
        "保存接管回复",
    ]
    for marker in conversation_markers:
        if marker not in conversation:
            blockers.append(f"多渠道对话台缺少真实 IM 工作流标记：{marker}")
    for misleading in ["AI自主回复预备", "待审核", "待发送"]:
        if misleading in conversation:
            blockers.append(f"多渠道对话台仍出现干扰表达：{misleading}")

    channel_markers = ["官方接入条件", "未接通原因", "真实外发", "不使用 Cookie", "网页私信模拟发送"]
    for marker in channel_markers:
        if marker not in channels:
            blockers.append(f"渠道页缺少边界或未接通说明：{marker}")
    if "已接通" in channels and "未接通原因" not in channels:
        blockers.append("渠道页可能暗示已接通，但没有未接通原因兜底。")

    app_lines = line_count("frontend/src/App.tsx")
    styles_lines = line_count("frontend/src/styles.css")
    client_lines = line_count("frontend/src/api/client.ts")
    if app_lines > 12000:
        warnings.append(f"App.tsx 仍有 {app_lines} 行，页面组件拆分尚未完成。")
    if styles_lines > 9000:
        warnings.append(f"styles.css 仍有 {styles_lines} 行，样式拆分尚未完成。")
    if client_lines > 3500:
        warnings.append(f"api/client.ts 仍有 {client_lines} 行，API 模块拆分尚未完成。")

    status = (
        "frontend_productization_blocked"
        if blockers
        else "frontend_productization_customer_flow_ready_component_split_pending"
    )
    result = {
        "schema_version": "p3-06u-26h2w-nc7.frontend_productization.v1",
        "phase": "H2W-NC7",
        "status": status,
        "blockers": sorted(set(blockers)),
        "warnings": warnings,
        "boundaries": {
            "real_platform_send_ready": False,
            "real_channel_closed_loop_ready": False,
            "formal_customer_signoff_ready": False,
            "signed_dmg_exe_ready": False,
            "mobile_ready": False,
        },
        "not_ready_for": [
            "真实平台自动外发",
            "真实渠道闭环上线",
            "正式客户签收",
            "已签名安装包交付",
            "移动端使用",
            "大型组件拆分完成口径",
        ],
        "evidence_paths": [
            "frontend/src/data/navigation.ts",
            "frontend/src/App.tsx",
            "frontend/src/components/conversation/ConversationWorkbenchPanel.tsx",
            "frontend/src/components/channels/ChannelConnectorCenterPanel.tsx",
            "frontend/src/components/quality/QualityReviewPanel.tsx",
            "output/p3_06u_26h2w_nc7_frontend_productization/frontend_productization_report.md",
        ],
        "customer_data_used": False,
        "internal_sample_used": False,
        "checks": {
            "pilot_primary_entry": has_navigation_group(nav, "试点准备", "#pilot"),
            "monthly_ops_link": "#quality?focus=monthly-ops-report" in app,
            "conversation_markers": conversation_markers,
            "channel_boundary_markers": channel_markers,
            "app_lines": app_lines,
            "styles_lines": styles_lines,
            "client_lines": client_lines,
        },
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    SUMMARY_PATH.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    REPORT_PATH.write_text(
        "\n".join(
            [
                "# H2W-NC7 前端真实产品化收束",
                "",
                f"- 状态：`{status}`",
                f"- 阻断项：{len(result['blockers'])} 个",
                f"- 提醒项：{len(warnings)} 个",
                "",
                "## 已检查",
                "",
                "- 试点准备是否成为一级主入口。",
                "- 质量复盘是否降级为试跑确认口径。",
                "- 账号与本地维护是否避开孤儿锚点。",
                "- 多渠道对话台是否保持客服 IM 主形态。",
                "- 渠道页是否只表达官方条件、未接通原因和边界。",
                "",
                "## 阻断项",
                "",
                *(f"- {item}" for item in result["blockers"]),
                *(["- 无"] if not result["blockers"] else []),
                "",
                "## 提醒项",
                "",
                *(f"- {item}" for item in warnings),
                *(["- 无"] if not warnings else []),
                "",
                "## 边界",
                "",
                "- 本阶段不代表真实渠道已接通。",
                "- 本阶段不代表真实平台外发已开启。",
                "- 本阶段不代表正式客户签收或签名安装包完成。",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if blockers else 0


if __name__ == "__main__":
    raise SystemExit(main())
