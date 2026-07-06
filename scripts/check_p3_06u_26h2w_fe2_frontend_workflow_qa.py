#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PHASE = "H2W-FE2"
DEFAULT_OUTPUT_DIR = ROOT / "output/p3_06u_26h2w_fe2_frontend_workflow_qa"
DOC_PATH = ROOT / "docs/P3-06U-26H2W_FE2_FRONTEND_WORKFLOW_QA.md"
MATRIX = ROOT / "docs/FRONTEND_FUNCTION_REALITY_MATRIX.md"
WORKBENCH = ROOT / "frontend/src/components/conversation/ConversationWorkbenchPanel.tsx"
APP = ROOT / "frontend/src/App.tsx"
H2W0_STATIC = ROOT / "scripts/check_p3_06u_26h2w0_frontend_function_reality.py"
H2W0_BROWSER = ROOT / "scripts/check_p3_06u_26h2w0_frontend_function_reality_owner_login.mjs"
H2W3_DEEP_AUDIT = ROOT / "scripts/audit_p3_06u_26h2w3_frontend_clicks_and_ux.mjs"

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
    "账号安全",
}
ALLOWED_STATUSES = {"真实可用", "只读可用", "禁用合理", "应隐藏", "仅后端"}
CUSTOMER_BANNED_TERMS = ["dry-run", "provider", "outbox", "sandbox", "H2W", "P3-06"]
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


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


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
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        rows.append(cells)
    return rows


def _write_markdown(path: Path, result: dict[str, Any]) -> None:
    metrics = result["metrics"]
    lines = [
        "# H2W-FE2 前端全量点击与真实工作流 QA",
        "",
        "## 结论",
        "",
        f"- 阶段状态：`{result['status']}`",
        f"- 功能矩阵行数：`{metrics['matrix_row_count']}`",
        f"- 已覆盖页面数：`{metrics['covered_page_count']}`",
        f"- 真实动作控件：`{metrics['real_action_count']}`",
        f"- 禁用合理控件：`{metrics['disabled_or_hidden_count']}`",
        f"- 客户可见工程词风险：`{metrics['customer_visible_engineering_term_count']}`",
        "",
        "## 停止门禁",
        "",
        "- 每个客户可见按钮必须是真实动作、明确禁用说明或隐藏。",
        "- 多渠道对话台必须保持客服 IM 形态：左侧紧凑会话列表，右侧大面积消息流。",
        "- 转人工只作为会话状态，不再把普通流程写成待审核或待发送。",
        "- 客户可见文案不使用 dry-run、provider、outbox、sandbox、H2W、P3 等工程词。",
        "- 页面不能出现假分页、假按钮、重复入口或超出后端真实能力的文案。",
        "",
        "## 阻断项",
        "",
    ]
    if result["blockers"]:
        lines.extend(f"- {item}" for item in result["blockers"])
    else:
        lines.append("- 无")
    lines.extend(
        [
            "",
            "## 警告",
            "",
        ]
    )
    if result["warnings"]:
        lines.extend(f"- {item}" for item in result["warnings"])
    else:
        lines.append("- 无")
    lines.extend(
        [
            "",
            "## 输出",
            "",
            f"- `{result['evidence']['summary_json']['path']}`",
            "",
            "## 边界",
            "",
            "- 本脚本是静态真实性门禁；浏览器逐页点击仍需要运行 H2W0/H2W3 的 mjs 脚本。",
            "- 本阶段不打开真实外发。",
            "- 本阶段不把演示数据当正式客户签收。",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_h2w_fe2_frontend_workflow_qa(*, output_dir: Path = DEFAULT_OUTPUT_DIR) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = output_dir / "summary.json"
    blockers: list[str] = []
    warnings: list[str] = []

    for path in [MATRIX, WORKBENCH, APP, H2W0_STATIC, H2W0_BROWSER, H2W3_DEEP_AUDIT]:
        if not path.exists():
            blockers.append(f"缺少前端 QA 依赖文件：{_display_path(path)}")

    matrix_text = MATRIX.read_text(encoding="utf-8") if MATRIX.exists() else ""
    workbench_text = WORKBENCH.read_text(encoding="utf-8") if WORKBENCH.exists() else ""
    app_text = APP.read_text(encoding="utf-8") if APP.exists() else ""
    rows = _parse_matrix_rows(matrix_text)
    if len(rows) < 40:
        blockers.append(f"功能真实性矩阵行数不足：{len(rows)}")

    covered_pages = {row[0] for row in rows if len(row) >= 16}
    missing_pages = sorted(REQUIRED_PAGES - covered_pages)
    if missing_pages:
        blockers.append(f"功能真实性矩阵缺少页面：{missing_pages}")

    invalid_rows: list[str] = []
    real_action_count = 0
    disabled_or_hidden_count = 0
    for row in rows:
        if len(row) != 16:
            invalid_rows.append("列数错误：" + " | ".join(row[:4]))
            continue
        status = row[13]
        evidence = row[15]
        if status not in ALLOWED_STATUSES:
            invalid_rows.append(f"状态非法：{row[0]} / {row[2]} / {status}")
        if status == "真实可用":
            real_action_count += 1
        if status in {"禁用合理", "应隐藏"}:
            disabled_or_hidden_count += 1
        if evidence in {"", "无", "不适用"}:
            invalid_rows.append(f"证据不足：{row[0]} / {row[2]}")
    if invalid_rows:
        blockers.extend(invalid_rows[:20])
        if len(invalid_rows) > 20:
            warnings.append(f"另有 {len(invalid_rows) - 20} 条矩阵问题未展开")

    for term in WORKBENCH_BANNED_COPY:
        if term in workbench_text:
            blockers.append(f"多渠道对话台仍出现应收束文案：{term}")
    for needle in [
        "service-thread-item",
        "service-message-stream",
        "转人工",
        "保存接管回复",
        'data-function-reality="no-fake-chat-actions"',
    ]:
        if needle not in workbench_text:
            blockers.append(f"多渠道对话台缺少关键 IM/真实性标记：{needle}")

    customer_visible_hits = []
    for row in rows:
        if len(row) != 16:
            continue
        customer_facing_text = " ".join([row[0], row[1], row[2], row[3], row[14]])
        for term in CUSTOMER_BANNED_TERMS:
            if term in customer_facing_text:
                customer_visible_hits.append(f"{row[0]} / {row[2]} / {term}")
    if customer_visible_hits:
        blockers.append(f"功能真实性矩阵客户可见说明仍含工程词：{customer_visible_hits}")

    # The app source may contain internal variable names such as outbox/provider. Treat those as warnings only.
    app_source_hits = [term for term in CUSTOMER_BANNED_TERMS if term in app_text]
    if app_source_hits:
        warnings.append(
            "App.tsx 仍含内部工程词变量或开发数据；需通过浏览器 QA 判断是否客户可见："
            + ", ".join(app_source_hits)
        )

    result = {
        "phase": PHASE,
        "status": "passed" if not blockers else "blocked",
        "metrics": {
            "matrix_row_count": len(rows),
            "covered_page_count": len(covered_pages),
            "real_action_count": real_action_count,
            "disabled_or_hidden_count": disabled_or_hidden_count,
            "customer_visible_engineering_term_count": len(customer_visible_hits),
        },
        "blockers": blockers,
        "warnings": warnings,
        "evidence": {
            "summary_json": {"path": _display_path(summary_path)},
            "function_reality_matrix": {"path": _display_path(MATRIX)},
            "workbench_component": {"path": _display_path(WORKBENCH)},
            "browser_owner_login_smoke": {"path": _display_path(H2W0_BROWSER)},
            "deep_click_audit": {"path": _display_path(H2W3_DEEP_AUDIT)},
        },
        "boundaries": {
            "real_platform_send_performed": False,
            "mobile_scope_included": False,
            "demo_data_used_as_signoff": False,
        },
    }
    _write_json(summary_path, result)
    _write_markdown(DOC_PATH, result)
    return result


def main() -> int:
    result = run_h2w_fe2_frontend_workflow_qa()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if result["status"] == "blocked" else 0


if __name__ == "__main__":
    raise SystemExit(main())
