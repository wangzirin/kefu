#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PHASE = "H2W-FE4"
DEFAULT_OUTPUT_DIR = ROOT / "output/p3_06u_26h2w_fe4_customer_ui_sealed_candidate"
DOC_PATH = ROOT / "docs/P3-06U-26H2W_FE4_CUSTOMER_UI_SEALED_CANDIDATE.md"

FE3_SUMMARY = ROOT / "output/p3_06u_26h2w_fe3_frontend_browser_workflow_qa/summary.json"
DEEP_AUDIT_SUMMARY = ROOT / "output/p3_06u_26h2w3_frontend_deep_audit/summary.json"
PACK4_SUMMARY = ROOT / "output/p3_06u_26h2w_pack4_delivery_checklist_and_startup_rehearsal/summary.json"
CLICK_QA_SUMMARY = ROOT / "output/p3_06u_26h2w_fe4_customer_visible_click_qa/summary.json"
MATRIX = ROOT / "docs/FRONTEND_FUNCTION_REALITY_MATRIX.md"
APP = ROOT / "frontend/src/App.tsx"
WORKBENCH = ROOT / "frontend/src/components/conversation/ConversationWorkbenchPanel.tsx"
NAVIGATION = ROOT / "frontend/src/data/navigation.ts"

REQUIRED_PAGES = {
    "运营总览",
    "多渠道对话台",
    "知识库运营",
    "知识缺口",
    "知识评测",
    "质量复盘",
    "渠道接入",
    "运维与告警",
    "自动回复策略",
    "模型路由",
    "账号安全",
}
ALLOWED_STATUSES = {"真实可用", "只读可用", "禁用合理", "应隐藏", "仅后端"}
HIDDEN_BACKEND_ROUTES = {
    "#conversations": "会话收件箱",
    "#reviews": "人工审核",
    "#outbox": "待发送草稿",
    "#tickets": "工单/SLA",
}
WORKBENCH_REQUIRED_MARKERS = [
    "service-thread-item",
    "service-message-stream",
    "转人工",
    "保存接管回复",
    'data-function-reality="no-fake-chat-actions"',
]
WORKBENCH_BANNED_COPY = [
    "AI自主回复预备",
    "AI 自主回复预备",
    "待审核",
    "待发送",
    "批准入待发送",
    "人工审核",
    "发送图片",
    "添加附件",
    "设为星标",
    "历史记录",
]
VISIBLE_ENGINEERING_SNIPPETS = [
    "Provider：",
    'aria-label="H2W7 门禁"',
    "预览工作区",
    "演示模式",
    "开发演示",
]
CUSTOMER_OVERCLAIMS = [
    "已接通全渠道",
    "全平台已接通",
    "真实外发已开启",
    "已发到微信",
    "已发到抖音",
    "已正式签收",
    "正式准确率签收完成",
    "线上准确率已完成",
]


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _parse_matrix_rows(matrix_text: str) -> list[list[str]]:
    start = matrix_text.find("## 2. 功能真实性明细")
    end = matrix_text.find("## 3.", start)
    if start < 0 or end < 0:
        return []
    rows: list[list[str]] = []
    for line in matrix_text[start:end].splitlines():
        stripped = line.strip()
        if not stripped.startswith("|") or stripped.startswith("|---") or "页面 | 区域" in stripped:
            continue
        rows.append([cell.strip() for cell in stripped.strip("|").split("|")])
    return rows


def _string_literal_for_object_property(text: str, property_name: str, value: str) -> bool:
    pattern = re.compile(rf"{re.escape(property_name)}\s*:\s*[\"']{re.escape(value)}[\"']")
    return bool(pattern.search(text))


def _summarize_deep_audit(data: dict[str, Any]) -> dict[str, Any]:
    results = data.get("results") or data.get("pages") or []
    preview_pages: list[str] = []
    pages_with_engineering_terms: list[str] = []
    if isinstance(results, list):
        for item in results:
            if not isinstance(item, dict):
                continue
            page = str(item.get("page") or item.get("hash") or item.get("name") or "unknown")
            if item.get("hasPreviewCopy") is True:
                preview_pages.append(page)
            if item.get("engineeringTermHits") or item.get("customerVisibleEngineeringTerms"):
                pages_with_engineering_terms.append(page)
    return {
        "issue_count": len(data.get("issues") or []),
        "runtime_error_count": len(data.get("runtimeErrors") or []),
        "preview_page_count": len(preview_pages),
        "preview_pages": preview_pages[:20],
        "pages_with_engineering_terms": pages_with_engineering_terms[:20],
    }


def _write_markdown(path: Path, result: dict[str, Any]) -> None:
    metrics = result["metrics"]
    lines = [
        "# H2W-FE4 客户可见 UI 封版候选门禁",
        "",
        "## 结论",
        "",
        f"- 阶段状态：`{result['status']}`",
        f"- 可进入客户可见 UI 候选：`{str(result['readiness']['ready_for_customer_visible_ui_candidate']).lower()}`",
        f"- 功能真实性矩阵行数：`{metrics['matrix_row_count']}`",
        f"- 覆盖页面数：`{metrics['covered_page_count']}`",
        f"- 工作台禁用文案命中：`{metrics['workbench_banned_copy_hit_count']}`",
        f"- 深审问题数：`{metrics['deep_audit_issue_count']}`",
        f"- 深审运行时错误数：`{metrics['deep_audit_runtime_error_count']}`",
        "",
        "## 本阶段检查什么",
        "",
        "- 客户可见按钮必须是真实动作、明确禁用说明或隐藏。",
        "- 多渠道对话台保持客服对话形态：左侧紧凑会话列表，右侧大面积消息流。",
        "- 转人工只作为会话状态，不在主流程暴露待审核、待发送、AI 预备等干扰表达。",
        "- 隐藏后台页可以保留，但必须从主侧边栏隐藏，不得伪装成客户主流程。",
        "- 前端文案不能超过后端真实能力：真实外发、全渠道接通、正式签收都不能被写成已完成。",
        "",
        "## 阻断项",
        "",
    ]
    lines.extend([f"- {item}" for item in result["blockers"]] or ["- 无"])
    lines.extend(["", "## 警告", ""])
    lines.extend([f"- {item}" for item in result["warnings"]] or ["- 无"])
    lines.extend(
        [
            "",
            "## 证据",
            "",
            f"- summary：`{result['evidence']['summary_json']['path']}`",
            f"- FE3：`{result['evidence']['fe3_summary']['path']}`",
            f"- 深审：`{result['evidence']['deep_audit_summary']['path']}`",
            f"- PACK4：`{result['evidence']['pack4_summary']['path']}`",
            f"- 真实浏览器点击 QA：`{result['evidence']['click_qa_summary']['path']}`",
            "",
            "## 边界",
            "",
            "- `real_platform_send_performed=false`",
            "- `formal_customer_signoff_performed=false`",
            "- `enterprise_channel_scope_included=false`",
            "- `mobile_scope_included=false`",
            "- 本阶段不替代真实客户题库、真实渠道沙箱或正式准确率签收。",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_h2w_fe4_customer_ui_sealed_candidate(
    *,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    doc_path: Path = DOC_PATH,
    fe3_summary: Path = FE3_SUMMARY,
    deep_audit_summary: Path = DEEP_AUDIT_SUMMARY,
    pack4_summary: Path = PACK4_SUMMARY,
    matrix_path: Path = MATRIX,
    app_path: Path = APP,
    workbench_path: Path = WORKBENCH,
    navigation_path: Path = NAVIGATION,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = output_dir / "summary.json"
    blockers: list[str] = []
    warnings: list[str] = []

    for path, label in [
        (fe3_summary, "FE3 摘要"),
        (deep_audit_summary, "浏览器深审摘要"),
        (pack4_summary, "PACK4 摘要"),
        (matrix_path, "功能真实性矩阵"),
        (app_path, "App.tsx"),
        (workbench_path, "多渠道对话台组件"),
        (navigation_path, "导航配置"),
    ]:
        if not path.exists():
            blockers.append(f"缺少 {label}：{_display_path(path)}")

    fe3 = _read_json(fe3_summary) if fe3_summary.exists() else {}
    if fe3.get("status") != "passed":
        blockers.append(f"FE3 未通过：status={fe3.get('status')}")
    if fe3.get("boundaries", {}).get("real_platform_send_performed") is not False:
        blockers.append("FE3 边界未确认真实外发关闭")

    pack4 = _read_json(pack4_summary) if pack4_summary.exists() else {}
    if pack4.get("status") != "ready_for_customer_local_pilot_startup_rehearsal":
        blockers.append(f"PACK4 不是本地试点启动就绪状态：status={pack4.get('status')}")
    if pack4.get("boundaries", {}).get("formal_customer_signoff_performed") is not False:
        blockers.append("PACK4 边界未确认不是正式客户签收")

    deep_audit = _read_json(deep_audit_summary) if deep_audit_summary.exists() else {}
    deep_metrics = _summarize_deep_audit(deep_audit)
    if deep_metrics["issue_count"]:
        blockers.append(f"浏览器深审仍有问题：{deep_metrics['issue_count']} 个")
    if deep_metrics["runtime_error_count"]:
        blockers.append(f"浏览器深审仍有运行时错误：{deep_metrics['runtime_error_count']} 个")
    if deep_metrics["preview_page_count"]:
        warnings.append(
            "浏览器深审仍观察到预览/样例类文案页面："
            + "、".join(deep_metrics["preview_pages"])
            + "；FE4 只阻断客户可见误导词，后续可继续做文案收束。"
        )
    if deep_metrics["pages_with_engineering_terms"]:
        blockers.append("浏览器深审发现客户可见工程词页面：" + "、".join(deep_metrics["pages_with_engineering_terms"]))

    matrix_text = _read_text(matrix_path)
    rows = _parse_matrix_rows(matrix_text)
    covered_pages = {row[0] for row in rows if len(row) >= 16}
    missing_pages = sorted(REQUIRED_PAGES - covered_pages)
    if len(rows) < 50:
        blockers.append(f"功能真实性矩阵行数不足：{len(rows)}")
    if missing_pages:
        blockers.append(f"功能真实性矩阵缺少页面：{missing_pages}")

    invalid_rows: list[str] = []
    visible_fake_rows: list[str] = []
    for row in rows:
        if len(row) != 16:
            invalid_rows.append("列数错误：" + " / ".join(row[:4]))
            continue
        status = row[13]
        if status not in ALLOWED_STATUSES:
            invalid_rows.append(f"状态非法：{row[0]} / {row[2]} / {status}")
        if status == "仅前端":
            visible_fake_rows.append(f"{row[0]} / {row[2]}")
        if row[15] in {"", "无"}:
            invalid_rows.append(f"证据不足：{row[0]} / {row[2]}")
    if invalid_rows:
        blockers.extend(invalid_rows[:20])
        if len(invalid_rows) > 20:
            warnings.append(f"另有 {len(invalid_rows) - 20} 条矩阵问题未展开")
    if visible_fake_rows:
        blockers.append("矩阵仍存在仅前端客户可见控件：" + "、".join(visible_fake_rows[:20]))

    workbench_text = _read_text(workbench_path)
    for marker in WORKBENCH_REQUIRED_MARKERS:
        if marker not in workbench_text:
            blockers.append(f"多渠道对话台缺少关键标记：{marker}")
    workbench_banned_hits = [term for term in WORKBENCH_BANNED_COPY if term in workbench_text]
    if workbench_banned_hits:
        blockers.append("多渠道对话台仍出现应隐藏/收束文案：" + "、".join(workbench_banned_hits))
    if "chat-head-action" in workbench_text or "composer-tool-button" in workbench_text:
        blockers.append("多渠道对话台仍存在历史顶部动作或底部工具假按钮 class")

    app_text = _read_text(app_path)
    visible_engineering_hits = [term for term in VISIBLE_ENGINEERING_SNIPPETS if term in app_text]
    if visible_engineering_hits:
        blockers.append("App 客户可见文案或 aria 仍含工程词：" + "、".join(visible_engineering_hits))
    overclaim_hits = [term for term in CUSTOMER_OVERCLAIMS if term in app_text]
    if overclaim_hits:
        blockers.append("App 仍含可能误导客户的完成态承诺：" + "、".join(overclaim_hits))
    if "真实外发关闭" not in app_text:
        blockers.append("App 缺少真实外发关闭边界文案")

    navigation_text = _read_text(navigation_path)
    for href, label in HIDDEN_BACKEND_ROUTES.items():
        if href not in navigation_text:
            blockers.append(f"导航配置缺少后台路由记录：{label} {href}")
        if label not in navigation_text:
            blockers.append(f"导航配置缺少后台路由标签：{label}")
        if not _string_literal_for_object_property(navigation_text, "hiddenFromSidebar", "true"):
            # Fallback below catches TypeScript boolean separately.
            if "hiddenFromSidebar: true" not in navigation_text:
                blockers.append("导航配置没有隐藏后台路由的 hiddenFromSidebar=true 标记")
                break
    for href in ["#live", "#overview", "#knowledge", "#quality", "#channels", "#settings"]:
        if href not in navigation_text:
            blockers.append(f"主导航缺少正式工作页：{href}")

    status = "ready_for_customer_visible_ui_candidate" if not blockers else "blocked"
    result = {
        "phase": PHASE,
        "status": status,
        "readiness": {
            "ready_for_customer_visible_ui_candidate": not blockers,
            "ready_for_customer_formal_signoff": False,
            "ready_for_real_platform_send": False,
        },
        "metrics": {
            "matrix_row_count": len(rows),
            "covered_page_count": len(covered_pages),
            "workbench_banned_copy_hit_count": len(workbench_banned_hits),
            "deep_audit_issue_count": deep_metrics["issue_count"],
            "deep_audit_runtime_error_count": deep_metrics["runtime_error_count"],
            "deep_audit_preview_page_count": deep_metrics["preview_page_count"],
            "visible_engineering_hit_count": len(visible_engineering_hits),
            "overclaim_hit_count": len(overclaim_hits),
        },
        "blockers": blockers,
        "warnings": warnings,
        "evidence": {
            "summary_json": {"path": _display_path(summary_path)},
            "fe3_summary": {"path": _display_path(fe3_summary), "present": fe3_summary.exists()},
            "deep_audit_summary": {"path": _display_path(deep_audit_summary), "present": deep_audit_summary.exists()},
            "pack4_summary": {"path": _display_path(pack4_summary), "present": pack4_summary.exists()},
            "click_qa_summary": {"path": _display_path(CLICK_QA_SUMMARY), "present": CLICK_QA_SUMMARY.exists()},
        },
        "boundaries": {
            "real_platform_send_performed": False,
            "formal_customer_signoff_performed": False,
            "enterprise_channel_scope_included": False,
            "mobile_scope_included": False,
        },
    }
    _write_json(summary_path, result)
    _write_markdown(doc_path, result)
    return result


def main() -> int:
    result = run_h2w_fe4_customer_ui_sealed_candidate()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if result["status"] == "blocked" else 0


if __name__ == "__main__":
    raise SystemExit(main())
