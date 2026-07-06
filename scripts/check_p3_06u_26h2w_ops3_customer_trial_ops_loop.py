#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PHASE = "H2W-OPS3"
SCHEMA_VERSION = "p3-06u-26h2w-ops3.customer_trial_ops_loop.v1"
DEFAULT_OUTPUT_DIR = ROOT / "output/p3_06u_26h2w_ops3_customer_trial_ops_loop"
DOC_PATH = ROOT / "docs/P3-06U-26H2W_OPS3_CUSTOMER_TRIAL_OPS_LOOP.md"

OPS1_SUMMARY = ROOT / "output/p3_06u_26h2w_ops1_after_sales_handoff_rehearsal/summary.json"
OPS2_SUMMARY = ROOT / "output/p3_06u_26h2w_ops2_customer_monthly_ops_report/summary.json"
LOCAL_MAINTENANCE_SUMMARY = ROOT / "output/p3_06u_26h2w8b_local_maintenance_ui/summary.json"
CUSTOMER_DOC = ROOT / "docs/customer/万法常世AI客服本地试跑运维说明.md"
OPS2_CUSTOMER_REPORT = ROOT / "output/p3_06u_26h2w_ops2_customer_monthly_ops_report/customer_monthly_ops_report.md"
INTERNAL_EVIDENCE = ROOT / "output/p3_06u_26h2w_ops2_customer_monthly_ops_report/internal_evidence_summary.json"

REQUIRED_DOC_TERMS = [
    "月度运维报告",
    "质量复盘",
    "知识缺口",
    "诊断包",
    "售后接收台",
    "售后处理单",
    "签名更新包预检",
    "备份",
    "恢复演练",
    "审计记录",
    "不远控客户电脑",
    "不静默更新",
    "不自动上传客户数据",
]
SENSITIVE_TERMS = ["api_key=", "access_token=", "refresh_token=", "database_password=", "postgres_password="]
OVERCLAIMS = ["生产 SLA 已完成", "正式客户验收已完成", "真实外发已开启", "静默更新已开启", "远控客户电脑已完成"]


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _summary_status(path: Path) -> str:
    return str(_read_json(path).get("status") or "missing")


def _flag(payload: dict[str, Any], *path: str) -> Any:
    current: Any = payload
    for key in path:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def _write_markdown(path: Path, result: dict[str, Any]) -> None:
    lines = [
        "# H2W-OPS3 客户试跑运维闭环",
        "",
        "## 结论",
        "",
        f"- 阶段状态：`{result['status']}`",
        f"- 运维闭环：`{str(result['readiness']['customer_trial_ops_loop_ready']).lower()}`",
        "",
        "## 覆盖能力",
        "",
        "- 诊断包。",
        "- 月度运维报告。",
        "- 备份与恢复演练。",
        "- 签名更新包预检。",
        "- 售后接收台与处理单。",
        "- 审计记录。",
        "",
        "## 阻断项",
        "",
    ]
    lines.extend([f"- {item}" for item in result["blockers"]] or ["- 无"])
    lines.extend(["", "## 边界", ""])
    lines.extend(
        [
            "- 不远控客户电脑。",
            "- 不静默更新。",
            "- 不自动上传诊断包。",
            "- 不输出密钥、客户原文、草稿全文或平台 payload。",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_h2w_ops3_customer_trial_ops_loop(
    *,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    doc_path: Path = DOC_PATH,
) -> dict[str, Any]:
    blockers: list[str] = []
    status_checks = {
        "ops1": _summary_status(OPS1_SUMMARY),
        "ops2": _summary_status(OPS2_SUMMARY),
        "local_maintenance_ui": _summary_status(LOCAL_MAINTENANCE_SUMMARY),
    }
    if status_checks["ops1"] != "ready_for_after_sales_ops_handoff_rehearsal":
        blockers.append(f"OPS1 上游状态不满足：{status_checks['ops1']}")
    if status_checks["ops2"] != "ready_for_customer_monthly_ops_report_rehearsal":
        blockers.append(f"OPS2 上游状态不满足：{status_checks['ops2']}")

    maintenance = _read_json(LOCAL_MAINTENANCE_SUMMARY)
    api_readiness = maintenance.get("api_readiness") if isinstance(maintenance.get("api_readiness"), dict) else {}
    counts = api_readiness.get("counts") if isinstance(api_readiness.get("counts"), dict) else {}
    required_counts = {
        "diagnostic_intake_accepted": counts.get("diagnostic_intake_accepted", 0),
        "remediation_update_plan_prepared": counts.get("remediation_update_plan_prepared", 0),
        "signed_update_package_total": counts.get("signed_update_package_total", 0),
        "local_backup_verified": counts.get("local_backup_verified", 0),
        "restore_dry_run_total": counts.get("restore_dry_run_total", 0),
        "maintenance_audit_event_total": counts.get("maintenance_audit_event_total", 0),
    }
    blockers.extend([f"本地维护试跑证据不足：{name}" for name, value in required_counts.items() if int(value or 0) <= 0])

    doc_text = _read_text(CUSTOMER_DOC)
    blockers.extend([f"客户运维说明缺少：{term}" for term in REQUIRED_DOC_TERMS if term not in doc_text])
    if not OPS2_CUSTOMER_REPORT.exists():
        blockers.append(f"缺少客户月度运维报告候选：{_display_path(OPS2_CUSTOMER_REPORT)}")
    if not INTERNAL_EVIDENCE.exists():
        blockers.append(f"缺少内部证据摘要：{_display_path(INTERNAL_EVIDENCE)}")

    scan_text = "\n".join([doc_text, _read_text(OPS2_CUSTOMER_REPORT), _read_text(INTERNAL_EVIDENCE)])
    blockers.extend([f"运维输出包含敏感词：{term}" for term in SENSITIVE_TERMS if term.lower() in scan_text.lower()])
    blockers.extend([f"运维输出包含越界承诺：{term}" for term in OVERCLAIMS if term in scan_text])

    ops2 = _read_json(OPS2_SUMMARY)
    if _flag(ops2, "readiness", "real_platform_send_ready") is True:
        blockers.append("OPS2 越界声明真实外发 ready")
    if _flag(ops2, "readiness", "production_sla_ready") is True:
        blockers.append("OPS2 越界声明生产 SLA ready")

    result = {
        "schema_version": SCHEMA_VERSION,
        "phase": PHASE,
        "status": "blocked" if blockers else "customer_trial_ops_loop_ready",
        "status_checks": status_checks,
        "maintenance_counts": required_counts,
        "blockers": sorted(set(blockers)),
        "evidence_paths": [
            _display_path(CUSTOMER_DOC),
            _display_path(OPS2_CUSTOMER_REPORT),
            _display_path(INTERNAL_EVIDENCE),
            _display_path(LOCAL_MAINTENANCE_SUMMARY),
        ],
        "readiness": {
            "customer_trial_ops_loop_ready": not blockers,
            "monthly_ops_report_ready": OPS2_CUSTOMER_REPORT.exists(),
            "diagnostic_backup_update_audit_ready": not any(int(value or 0) <= 0 for value in required_counts.values()),
            "production_sla_ready": False,
            "real_platform_send_ready": False,
            "remote_control_ready": False,
            "silent_update_ready": False,
        },
        "boundaries": {
            "raw_customer_text_exported": False,
            "secret_exported": False,
            "automatic_upload_performed": False,
            "remote_control_performed": False,
            "silent_update_performed": False,
            "real_platform_send_performed": False,
        },
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    _write_json(output_dir / "summary.json", result)
    _write_markdown(doc_path, result)
    return result


def main() -> int:
    result = run_h2w_ops3_customer_trial_ops_loop()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] != "blocked" else 1


if __name__ == "__main__":
    raise SystemExit(main())
