#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PHASE = "H2W-OPS1"
DEFAULT_OUTPUT_DIR = ROOT / "output/p3_06u_26h2w_ops1_after_sales_handoff_rehearsal"
DOC_PATH = ROOT / "docs/P3-06U-26H2W_OPS1_AFTER_SALES_HANDOFF_REHEARSAL.md"

INSTALL1_SUMMARY = ROOT / "output/p3_06u_26h2w_install1_nontechnical_customer_starter/summary.json"
PACK5_SUMMARY = ROOT / "output/p3_06u_26h2w_pack5_customer_handoff_package/summary.json"
KB1_SUMMARY = ROOT / "output/p3_06u_26h2w_kb1_customer_specific_knowledge_package_rehearsal/summary.json"
LOCAL_MAINTENANCE_SUMMARY = ROOT / "output/p3_06u_26h2w8b_local_maintenance_ui/summary.json"

REMOTE_MAINTENANCE_SOP = ROOT / "docs/internal/REMOTE_MAINTENANCE_AUTHORIZATION_SOP.md"
INTERNAL_OPS_PLAN = ROOT / "docs/internal/万法常世AI智能客服系统_内部售后运营维护计划.md"
CUSTOMER_QUICK_START_DOC = ROOT / "docs/customer/万法常世AI客服本地试点启动说明.md"


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _summary_status(path: Path, expected_status: str) -> tuple[bool, str, dict[str, Any]]:
    if not path.exists():
        return False, "missing", {}
    try:
        payload = _read_json(path)
    except json.JSONDecodeError:
        return False, "invalid_json", {}
    status = str(payload.get("status", "missing_status"))
    return status == expected_status, status, payload


def _flag(payload: dict[str, Any], *path: str) -> Any:
    current: Any = payload
    for key in path:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def _summary_boundary_checks(payload: dict[str, Any], *, name: str) -> list[str]:
    blockers: list[str] = []
    if _flag(payload, "boundaries", "real_platform_send_performed") is True:
        blockers.append(f"{name} 越界记录为已真实外发")
    if _flag(payload, "boundaries", "formal_customer_signoff_performed") is True:
        blockers.append(f"{name} 越界记录为已完成正式客户签收")
    if _flag(payload, "readiness", "formal_customer_signoff_ready") is True:
        blockers.append(f"{name} 越界记录为正式客户签收 ready")
    if _flag(payload, "readiness", "real_platform_send_ready") is True:
        blockers.append(f"{name} 越界记录为真实平台外发 ready")
    if _flag(payload, "readiness", "desktop_installer_ready") is True:
        blockers.append(f"{name} 越界记录为完整桌面安装器 ready")
    if name == "kb1" and _flag(payload, "readiness", "customer_specific_knowledge_ready") is True:
        blockers.append("KB1 越界记录为客户专属知识库正式 ready")
    return blockers


def _maintenance_summary_checks(payload: dict[str, Any]) -> tuple[bool, list[str], dict[str, bool], dict[str, int]]:
    api = payload.get("api_readiness", {}) if isinstance(payload.get("api_readiness"), dict) else {}
    safety = api.get("safety", {}) if isinstance(api.get("safety"), dict) else {}
    counts = api.get("counts", {}) if isinstance(api.get("counts"), dict) else {}
    boundaries = payload.get("boundaries", {}) if isinstance(payload.get("boundaries"), dict) else {}

    count_values = {
        "diagnostic_intake_accepted": int(counts.get("diagnostic_intake_accepted", 0) or 0),
        "remediation_request_total": int(counts.get("remediation_request_total", 0) or 0),
        "remediation_update_plan_prepared": int(counts.get("remediation_update_plan_prepared", 0) or 0),
        "signed_update_package_staged": int(counts.get("signed_update_package_staged", 0) or 0),
        "local_backup_verified": int(counts.get("local_backup_verified", 0) or 0),
        "restore_dry_run_total": int(counts.get("restore_dry_run_total", 0) or 0),
        "maintenance_audit_event_total": int(counts.get("maintenance_audit_event_total", 0) or 0),
    }
    checks = {
        "maturity_ready_for_rehearsal": api.get("maturity_status") == "ready_for_rehearsal",
        "customer_maintenance_rehearsal_ready": api.get("ready_for_customer_maintenance_rehearsal") is True,
        "no_api_blockers": int(api.get("blocker_count", 0) or 0) == 0,
        "diagnostic_upload_package_ready": count_values["diagnostic_intake_accepted"] >= 1,
        "remediation_request_ready": count_values["remediation_request_total"] >= 1,
        "signed_update_plan_ready": count_values["remediation_update_plan_prepared"] >= 1,
        "signed_update_package_ready": count_values["signed_update_package_staged"] >= 1,
        "backup_rehearsal_ready": count_values["local_backup_verified"] >= 1,
        "restore_dry_run_ready": count_values["restore_dry_run_total"] >= 1,
        "audit_evidence_ready": count_values["maintenance_audit_event_total"] >= 1,
        "external_write_not_performed": safety.get("external_write_performed") is False,
        "remote_control_not_performed": safety.get("remote_control_performed") is False
        and boundaries.get("remote_control_performed") is False,
        "silent_update_not_performed": safety.get("silent_update_performed") is False
        and boundaries.get("silent_update_performed") is False,
        "automatic_update_not_performed": safety.get("automatic_update_performed") is False,
        "automatic_upload_not_performed": safety.get("automatic_upload_performed") is False,
        "manual_transfer_required": safety.get("manual_transfer_required") is True,
        "customer_admin_confirmation_required": safety.get("customer_admin_confirmation_required") is True,
        "real_platform_send_not_performed": boundaries.get("real_platform_send_performed") is False,
    }
    blockers = [f"本地维护闭环证据不满足 OPS1 门禁：{name}" for name, passed in checks.items() if not passed]
    return not blockers, blockers, checks, count_values


def _document_checks(path: Path, required_terms: dict[str, str], *, overclaim_phrases: list[str]) -> tuple[bool, list[str], dict[str, bool]]:
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    checks = {"document_exists": path.exists()}
    checks.update({name: term in text for name, term in required_terms.items()})
    checks["no_overclaim_phrases"] = not any(phrase in text for phrase in overclaim_phrases)
    blockers = [f"{_display_path(path)} 不满足 OPS1 文档门禁：{name}" for name, passed in checks.items() if not passed]
    return not blockers, blockers, checks


def _write_markdown(path: Path, result: dict[str, Any]) -> None:
    readiness = result["readiness"]
    lines = [
        "# H2W-OPS1 售后运维交接演练",
        "",
        "## 结论",
        "",
        f"- 阶段状态：`{result['status']}`",
        f"- 售后运维交接演练就绪：`{str(readiness['ready_for_after_sales_ops_handoff_rehearsal']).lower()}`",
        f"- 本地维护闭环演练就绪：`{str(readiness['local_maintenance_rehearsal_ready']).lower()}`",
        f"- 诊断包接收证据：`{str(readiness['diagnostic_upload_package_ready']).lower()}`",
        f"- 签名更新包证据：`{str(readiness['signed_update_package_ready']).lower()}`",
        f"- 备份与恢复演练证据：`{str(readiness['backup_rehearsal_ready'] and readiness['restore_dry_run_ready']).lower()}`",
        f"- 正式客户签收就绪：`{str(readiness['formal_customer_signoff_ready']).lower()}`",
        f"- 生产 SLA 就绪：`{str(readiness['production_sla_ready']).lower()}`",
        "",
        "## 本阶段实际完成",
        "",
        "- 聚合 INSTALL1、PACK5、KB1 和 H2W-8B 本地维护浏览器验收证据。",
        "- 把诊断包接收、售后处理单、签名更新包、备份、恢复演练和审计事件纳入同一张售后交接门禁。",
        "- 检查远程维护授权 SOP、内部售后运营计划和客户启动说明是否覆盖诊断优先、只读优先、二次授权、备份、回滚、权限回收和禁止命令。",
        "- 明确本阶段不远控客户电脑、不静默更新、不修改客户环境、不打开真实外发、不生成正式客户签收。",
        "",
        "## 售后交接链路",
        "",
        "1. 客户本地启动应用并创建首任负责人。",
        "2. 客户导入知识资料前先生成诊断包和备份点。",
        "3. 出现问题时，客户主动导出授权上传包；我方售后接收台登记并生成处理单。",
        "4. 我方准备签名更新包或修复计划，客户管理员确认后再应用。",
        "5. 应用前确认备份，应用后做恢复演练或回滚记录。",
        "6. 月度复盘时复查质量、知识缺口、成本、告警和维护审计。",
        "",
        "## 阻断项",
        "",
    ]
    lines.extend([f"- {item}" for item in result["blockers"]] or ["- 无"])
    lines.extend(["", "## 不可对外承诺", ""])
    lines.extend([f"- {item}" for item in result["not_ready_for"]])
    lines.extend(
        [
            "",
            "## 固定边界",
            "",
            "- `remote_control_performed=false`",
            "- `silent_update_performed=false`",
            "- `automatic_update_performed=false`",
            "- `customer_environment_modified=false`",
            "- `real_platform_send_performed=false`",
            "- `formal_customer_signoff_performed=false`",
            "- `production_sla_ready=false`",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_h2w_ops1_after_sales_handoff_rehearsal(
    *,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    doc_path: Path = DOC_PATH,
    install1_summary: Path = INSTALL1_SUMMARY,
    pack5_summary: Path = PACK5_SUMMARY,
    kb1_summary: Path = KB1_SUMMARY,
    local_maintenance_summary: Path = LOCAL_MAINTENANCE_SUMMARY,
    remote_maintenance_sop: Path = REMOTE_MAINTENANCE_SOP,
    internal_ops_plan: Path = INTERNAL_OPS_PLAN,
    customer_quick_start_doc: Path = CUSTOMER_QUICK_START_DOC,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = output_dir / "summary.json"
    blockers: list[str] = []
    warnings: list[str] = []

    summary_specs = {
        "install1": (install1_summary, "ready_for_nontechnical_customer_startup_rehearsal"),
        "pack5": (pack5_summary, "ready_for_customer_local_pilot_handoff_candidate"),
        "kb1": (kb1_summary, "ready_for_customer_specific_knowledge_package_rehearsal"),
    }
    summary_checks: dict[str, dict[str, Any]] = {}
    summary_payloads: dict[str, dict[str, Any]] = {}
    for name, (path, expected_status) in summary_specs.items():
        ok, actual_status, payload = _summary_status(path, expected_status)
        summary_checks[name] = {
            "path": _display_path(path),
            "expected_status": expected_status,
            "actual_status": actual_status,
            "passed": ok,
        }
        summary_payloads[name] = payload
        if not ok:
            blockers.append(f"{name} 上游证据未就绪：期望 {expected_status}，实际 {actual_status}")
        blockers.extend(_summary_boundary_checks(payload, name=name))

    if not local_maintenance_summary.exists():
        maintenance_ready = False
        maintenance_checks: dict[str, bool] = {"summary_exists": False}
        maintenance_counts: dict[str, int] = {}
        blockers.append("H2W-8B 本地维护闭环浏览器验收 summary 缺失")
    else:
        try:
            local_maintenance = _read_json(local_maintenance_summary)
        except json.JSONDecodeError:
            local_maintenance = {}
            blockers.append("H2W-8B 本地维护闭环 summary 不是有效 JSON")
        maintenance_ready, maintenance_blockers, maintenance_checks, maintenance_counts = _maintenance_summary_checks(
            local_maintenance
        )
        blockers.extend(maintenance_blockers)

    overclaim_phrases = [
        "已经完成远程控制客户电脑",
        "远程控制客户电脑已完成",
        "静默自动更新",
        "自动静默更新",
        "生产 SLA 已完成",
        "正式客户签收已完成",
        "真实平台自动外发已接通",
        "真实外发已开启",
    ]
    remote_ready, remote_blockers, remote_checks = _document_checks(
        remote_maintenance_sop,
        {
            "diagnostic_first": "诊断包优先",
            "readonly_first": "只读优先",
            "second_authorization": "变更二次授权",
            "customer_confirmation": "客户确认",
            "backup_required": "备份",
            "rollback_required": "回滚",
            "permission_revocation": "权限回收",
            "forbidden_commands": "禁止命令",
        },
        overclaim_phrases=overclaim_phrases,
    )
    internal_ready, internal_blockers, internal_checks = _document_checks(
        internal_ops_plan,
        {
            "diagnostic_package": "诊断包",
            "knowledge_update": "知识库更新",
            "rollback": "回滚",
            "backup": "备份",
            "p1": "P1",
            "p2": "P2",
            "monthly_review": "月度",
        },
        overclaim_phrases=overclaim_phrases,
    )
    quick_start_ready, quick_start_blockers, quick_start_checks = _document_checks(
        customer_quick_start_doc,
        {
            "docker_desktop": "Docker Desktop",
            "customer_env": "customer.env",
            "first_owner": "首任负责人",
            "diagnostic_package": "诊断包",
            "backup": "备份",
            "external_write_closed": "真实外发默认关闭",
        },
        overclaim_phrases=overclaim_phrases,
    )
    blockers.extend(remote_blockers)
    blockers.extend(internal_blockers)
    blockers.extend(quick_start_blockers)

    if remote_checks.get("no_overclaim_phrases") is False:
        blockers.append("远程维护 SOP 出现远程控制、静默更新、生产 SLA 或正式签收越界表述")
    if maintenance_checks.get("remote_control_not_performed") is False:
        blockers.append("本地维护证据出现远程控制已执行，OPS1 只能做授权流程和演练")
    if maintenance_checks.get("silent_update_not_performed") is False:
        blockers.append("本地维护证据出现静默更新已执行，OPS1 只允许客户确认后的受控更新")

    summaries_ready = all(item["passed"] for item in summary_checks.values())
    ready = (
        summaries_ready
        and maintenance_ready
        and remote_ready
        and internal_ready
        and quick_start_ready
        and not blockers
    )
    status = "ready_for_after_sales_ops_handoff_rehearsal" if ready else "blocked"
    result = {
        "phase": PHASE,
        "status": status,
        "readiness": {
            "ready_for_after_sales_ops_handoff_rehearsal": ready,
            "install1_startup_ready": summary_checks["install1"]["passed"],
            "pack5_handoff_ready": summary_checks["pack5"]["passed"],
            "kb1_package_rehearsal_ready": summary_checks["kb1"]["passed"],
            "local_maintenance_rehearsal_ready": maintenance_ready,
            "diagnostic_upload_package_ready": maintenance_checks.get("diagnostic_upload_package_ready", False),
            "remediation_request_ready": maintenance_checks.get("remediation_request_ready", False),
            "signed_update_plan_ready": maintenance_checks.get("signed_update_plan_ready", False),
            "signed_update_package_ready": maintenance_checks.get("signed_update_package_ready", False),
            "backup_rehearsal_ready": maintenance_checks.get("backup_rehearsal_ready", False),
            "restore_dry_run_ready": maintenance_checks.get("restore_dry_run_ready", False),
            "audit_evidence_ready": maintenance_checks.get("audit_evidence_ready", False),
            "remote_maintenance_sop_ready": remote_ready,
            "internal_ops_plan_ready": internal_ready,
            "customer_quick_start_ready": quick_start_ready,
            "remote_control_ready": False,
            "silent_auto_update_ready": False,
            "formal_customer_signoff_ready": False,
            "real_platform_send_ready": False,
            "enterprise_channel_ready": False,
            "production_sla_ready": False,
            "desktop_installer_ready": False,
        },
        "checks": {
            "summaries": summary_checks,
            "local_maintenance": maintenance_checks,
            "remote_maintenance_sop": remote_checks,
            "internal_ops_plan": internal_checks,
            "customer_quick_start": quick_start_checks,
        },
        "counts": {
            "local_maintenance": maintenance_counts,
        },
        "blockers": blockers,
        "warnings": warnings,
        "not_ready_for": [
            "我方远程控制客户电脑",
            "静默自动更新客户本地应用",
            "正式客户准确率签收",
            "真实平台自动外发",
            "企业微信/微信客服/抖音/淘宝/京东/拼多多真实渠道上线",
            "生产环境长期监控、告警和 SLA",
            "完整 macOS dmg / Windows exe 安装器",
        ],
        "evidence": {
            "summary_json": {"path": _display_path(summary_path)},
            "markdown": {"path": _display_path(doc_path)},
            "install1_summary": {"path": _display_path(install1_summary), "present": install1_summary.exists()},
            "pack5_summary": {"path": _display_path(pack5_summary), "present": pack5_summary.exists()},
            "kb1_summary": {"path": _display_path(kb1_summary), "present": kb1_summary.exists()},
            "local_maintenance_summary": {
                "path": _display_path(local_maintenance_summary),
                "present": local_maintenance_summary.exists(),
            },
            "remote_maintenance_sop": {
                "path": _display_path(remote_maintenance_sop),
                "present": remote_maintenance_sop.exists(),
            },
            "internal_ops_plan": {"path": _display_path(internal_ops_plan), "present": internal_ops_plan.exists()},
            "customer_quick_start_doc": {
                "path": _display_path(customer_quick_start_doc),
                "present": customer_quick_start_doc.exists(),
            },
        },
        "boundaries": {
            "internal_rehearsal_not_customer_signoff": True,
            "remote_control_performed": False,
            "silent_update_performed": False,
            "automatic_update_performed": False,
            "automatic_upload_performed": False,
            "customer_environment_modified": False,
            "real_platform_send_performed": False,
            "enterprise_channel_scope_included": False,
            "rpa_formal_delivery_included": False,
            "formal_customer_signoff_performed": False,
            "provider_call_performed": False,
            "production_sla_ready": False,
        },
        "next_recommended_steps": [
            "H2W-KB2：客户专属知识包导入后复测报告与签收模板，不伪造客户签收。",
            "H2W-OPS2：若需要，再补客户侧月度运维报告导出和客户确认单。",
            "H2W-INSTALL2：如确实需要，再评估 macOS dmg / Windows exe 原生安装器。",
        ],
    }
    _write_json(summary_path, result)
    _write_markdown(doc_path, result)
    return result


def main() -> int:
    result = run_h2w_ops1_after_sales_handoff_rehearsal()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if result["status"] == "blocked" else 0


if __name__ == "__main__":
    raise SystemExit(main())
