#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PHASE = "H2W-FE3"
DEFAULT_OUTPUT_DIR = ROOT / "output/p3_06u_26h2w_fe3_frontend_browser_workflow_qa"
DOC_PATH = ROOT / "docs/P3-06U-26H2W_FE3_FRONTEND_BROWSER_WORKFLOW_QA.md"
FE2_SUMMARY = ROOT / "output/p3_06u_26h2w_fe2_frontend_workflow_qa/summary.json"
OWNER_LOGIN_SUMMARY = ROOT / "output/p3_06u_26h2w0_frontend_function_reality_owner_login/summary.json"
KNOWLEDGE_TRIAL_SUMMARY = ROOT / "output/p3_06u_26h2w11e_owner_customer_knowledge_trial/summary.json"
LOCAL_MAINTENANCE_SUMMARY = ROOT / "output/p3_06u_26h2w8b_local_maintenance_ui/summary.json"
WORKBENCH = ROOT / "frontend/src/components/conversation/ConversationWorkbenchPanel.tsx"
MATRIX = ROOT / "docs/FRONTEND_FUNCTION_REALITY_MATRIX.md"

WORKBENCH_FORBIDDEN_COPY = [
    "AI自主回复预备",
    "AI 自主回复预备",
    "待审核",
    "待发送",
    "批准入待发送",
    "发送图片",
    "添加附件",
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


def _summary_ok(path: Path, *, kind: str) -> tuple[bool, str]:
    if not path.exists():
        return False, f"缺少 {kind} 浏览器/门禁摘要：{_display_path(path)}"
    data = _read_json(path)
    if kind == "FE2":
        return data.get("status") == "passed", f"FE2 status={data.get('status')}"
    if kind == "owner-login":
        return bool(data.get("ok")) and bool(data.get("owner_login_performed_through_ui")), "owner login smoke ok"
    if kind == "knowledge-trial":
        return (
            bool(data.get("ok"))
            and bool(data.get("owner_login_performed_through_ui"))
            and bool(data.get("server_persistence_verified"))
            and bool(data.get("customer_publish_path_clicked_through_ui"))
        ), "knowledge trial smoke ok"
    if kind == "local-maintenance":
        return (
            data.get("api_readiness", {}).get("maturity_status") == "ready_for_rehearsal"
            and data.get("boundaries", {}).get("browser_logged_in_through_real_form") is True
            and data.get("boundaries", {}).get("real_platform_send_performed") is False
        ), "local maintenance smoke ok"
    return False, f"未知摘要类型：{kind}"


def _write_markdown(path: Path, result: dict[str, Any]) -> None:
    metrics = result["metrics"]
    lines = [
        "# H2W-FE3 前端浏览器真实工作流 QA",
        "",
        "## 结论",
        "",
        f"- 阶段状态：`{result['status']}`",
        f"- FE2 静态矩阵：`{str(metrics['fe2_static_passed']).lower()}`",
        f"- 负责人登录 smoke：`{str(metrics['owner_login_smoke_passed']).lower()}`",
        f"- 知识维护 smoke：`{str(metrics['knowledge_trial_smoke_passed']).lower()}`",
        f"- 本地维护 smoke：`{str(metrics['local_maintenance_smoke_passed']).lower()}`",
        f"- 对话台禁用文案命中：`{metrics['workbench_forbidden_copy_hits']}`",
        "",
        "## 停止门禁",
        "",
        "- 客户可见按钮必须是真实动作、明确禁用说明或隐藏。",
        "- 多渠道对话台只保留紧凑会话列表和大面积消息流；转人工只作为会话状态。",
        "- 负责人登录、知识维护和本地维护必须通过真实浏览器 smoke。",
        "- 本阶段不打开真实外发，不写客户签收。",
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
            "## 输出",
            "",
            f"- `{result['evidence']['summary_json']['path']}`",
            "",
            "## 边界",
            "",
            "- `real_platform_send_performed=false`",
            "- `formal_customer_signoff_performed=false`",
            "- `mobile_scope_included=false`",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_h2w_fe3_frontend_browser_workflow_qa(
    *,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = output_dir / "summary.json"
    blockers: list[str] = []
    warnings: list[str] = []

    checks = {
        "fe2_static_passed": _summary_ok(FE2_SUMMARY, kind="FE2"),
        "owner_login_smoke_passed": _summary_ok(OWNER_LOGIN_SUMMARY, kind="owner-login"),
        "knowledge_trial_smoke_passed": _summary_ok(KNOWLEDGE_TRIAL_SUMMARY, kind="knowledge-trial"),
        "local_maintenance_smoke_passed": _summary_ok(LOCAL_MAINTENANCE_SUMMARY, kind="local-maintenance"),
    }
    metrics: dict[str, Any] = {}
    for name, (ok, detail) in checks.items():
        metrics[name] = ok
        if not ok:
            blockers.append(detail)

    workbench_text = WORKBENCH.read_text(encoding="utf-8") if WORKBENCH.exists() else ""
    forbidden_hits = [text for text in WORKBENCH_FORBIDDEN_COPY if text in workbench_text]
    if forbidden_hits:
        blockers.append("多渠道对话台仍出现应收束文案：" + "、".join(forbidden_hits))
    metrics["workbench_forbidden_copy_hits"] = len(forbidden_hits)

    matrix_text = MATRIX.read_text(encoding="utf-8") if MATRIX.exists() else ""
    for required_page in ["运营总览", "多渠道对话台", "知识库运营", "知识缺口", "知识评测", "质量复盘", "渠道接入", "账号安全"]:
        if required_page not in matrix_text:
            blockers.append(f"功能真实性矩阵缺少页面：{required_page}")

    app_text = (ROOT / "frontend/src/App.tsx").read_text(encoding="utf-8")
    if "人工审核收件箱" in app_text or "待发送草稿" in app_text:
        warnings.append("系统仍保留人工审核/待发送独立功能页；本阶段仅要求多渠道对话台不暴露这些流程词")

    status = "passed" if not blockers else "blocked"
    result = {
        "phase": PHASE,
        "status": status,
        "metrics": metrics,
        "blockers": blockers,
        "warnings": warnings,
        "evidence": {
            "summary_json": {"path": _display_path(summary_path)},
            "fe2_summary": {"path": _display_path(FE2_SUMMARY), "present": FE2_SUMMARY.exists()},
            "owner_login_summary": {"path": _display_path(OWNER_LOGIN_SUMMARY), "present": OWNER_LOGIN_SUMMARY.exists()},
            "knowledge_trial_summary": {"path": _display_path(KNOWLEDGE_TRIAL_SUMMARY), "present": KNOWLEDGE_TRIAL_SUMMARY.exists()},
            "local_maintenance_summary": {"path": _display_path(LOCAL_MAINTENANCE_SUMMARY), "present": LOCAL_MAINTENANCE_SUMMARY.exists()},
        },
        "boundaries": {
            "real_platform_send_performed": False,
            "formal_customer_signoff_performed": False,
            "mobile_scope_included": False,
            "enterprise_channel_scope_included": False,
        },
    }
    _write_json(summary_path, result)
    _write_markdown(DOC_PATH, result)
    return result


def main() -> int:
    result = run_h2w_fe3_frontend_browser_workflow_qa()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if result["status"] == "blocked" else 0


if __name__ == "__main__":
    raise SystemExit(main())
