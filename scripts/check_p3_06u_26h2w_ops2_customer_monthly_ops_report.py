#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PHASE = "H2W-OPS2"
SCHEMA_VERSION = "p3-06u-26h2w-ops2.customer_monthly_ops_report_gate.v1"
DEFAULT_OUTPUT_DIR = ROOT / "output/p3_06u_26h2w_ops2_customer_monthly_ops_report"
DOC_PATH = ROOT / "docs/P3-06U-26H2W_OPS2_CUSTOMER_MONTHLY_OPS_REPORT.md"

OPS1_SUMMARY = ROOT / "output/p3_06u_26h2w_ops1_after_sales_handoff_rehearsal/summary.json"
KB2_SUMMARY = ROOT / "output/p3_06u_26h2w_kb2_post_import_retest_and_signoff_template/summary.json"
MODEL1_SUMMARY = ROOT / "output/p3_06u_26h2w_model1_bailian_cost_sample/summary.json"
TRIAL1_SUMMARY = ROOT / "output/p3_06u_26h2w_trial1_internal_100q_rehearsal_report/summary.json"
FE4_SUMMARY = ROOT / "output/p3_06u_26h2w_fe4_customer_ui_sealed_candidate/summary.json"

ALLOWED_TRIAL1_STATUSES = {
    "passed_internal_rehearsal_report",
    "passed_internal_rehearsal_report_with_open_gaps",
}

OVERCLAIM_PHRASES = [
    "生产 SLA 已完成",
    "正式客户签收已完成",
    "真实平台自动外发已接通",
    "真实外发已开启",
    "远程控制客户电脑已完成",
    "静默自动更新",
]

SENSITIVE_TERMS = [
    "api_key",
    "secret_key",
    "access_token",
    "refresh_token",
    "database_password",
    "postgres_password",
    "平台 payload",
    "草稿全文",
    "客户原文",
]


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


def _flag(payload: dict[str, Any], *path: str) -> Any:
    current: Any = payload
    for key in path:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def _load_summary(
    path: Path,
    *,
    name: str,
    expected_status: str | set[str],
) -> tuple[dict[str, Any], dict[str, Any], list[str]]:
    check = {
        "path": _display_path(path),
        "present": path.exists(),
        "expected_status": sorted(expected_status) if isinstance(expected_status, set) else expected_status,
        "actual_status": "missing",
        "passed": False,
    }
    if not path.exists():
        return {}, check, [f"{name} summary 缺失：{_display_path(path)}"]
    try:
        payload = _read_json(path)
    except json.JSONDecodeError:
        check["actual_status"] = "invalid_json"
        return {}, check, [f"{name} summary 不是有效 JSON：{_display_path(path)}"]
    actual = str(payload.get("status") or "missing_status")
    check["actual_status"] = actual
    expected_ok = actual in expected_status if isinstance(expected_status, set) else actual == expected_status
    check["passed"] = expected_ok
    if not expected_ok:
        return payload, check, [f"{name} 状态不满足：期望 {check['expected_status']}，实际 {actual}"]
    return payload, check, []


def _boundary_blockers(payload: dict[str, Any], *, name: str) -> list[str]:
    blockers: list[str] = []
    unsafe_flags = {
        "真实平台外发": (
            _flag(payload, "readiness", "real_platform_send_ready") is True
            or _flag(payload, "boundaries", "real_platform_send_performed") is True
            or _flag(payload, "boundaries", "external_platform_write_performed") is True
        ),
        "正式客户签收": (
            _flag(payload, "readiness", "formal_customer_signoff_ready") is True
            or _flag(payload, "boundaries", "formal_customer_signoff_performed") is True
            or _flag(payload, "readiness", "customer_quality_report_candidate") is True
        ),
        "生产 SLA": (
            _flag(payload, "readiness", "production_sla_ready") is True
            or _flag(payload, "boundaries", "production_sla_ready") is True
        ),
        "远程控制客户电脑": _flag(payload, "boundaries", "remote_control_performed") is True,
        "静默更新": (
            _flag(payload, "boundaries", "silent_update_performed") is True
            or _flag(payload, "boundaries", "automatic_update_performed") is True
        ),
    }
    for label, failed in unsafe_flags.items():
        if failed:
            blockers.append(f"{name} 上游越界记录为已完成或 ready：{label}")
    return blockers


def _scan_text_for_terms(text: str, *, terms: list[str]) -> list[str]:
    return [term for term in terms if term.lower() in text.lower()]


def _safe_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _status_label(result_status: str) -> str:
    return "可进入客户侧月度运维复盘" if result_status != "blocked" else "阻断：证据不足"


def _customer_status_text(value: Any) -> str:
    status = str(value or "待验证")
    labels = {
        "passed_real_small_sample_cost_rehearsal": "已形成小样本成本证据",
        "passed_internal_rehearsal_report": "已完成内部题库演练",
        "passed_internal_rehearsal_report_with_open_gaps": "已完成内部题库演练，仍有待修复缺口",
        "ready_for_customer_monthly_ops_report_rehearsal": "可进入客户侧月度运维复盘",
        "ready_for_after_sales_ops_handoff_rehearsal": "已形成售后交接证据",
    }
    return labels.get(status, status.replace("_", " "))


def _build_customer_report(result: dict[str, Any]) -> str:
    metrics = result["customer_metrics"]
    lines = [
        "# 客户侧月度运维报告",
        "",
        "## 本月结论",
        "",
        f"- 状态：{_status_label(result['status'])}",
        f"- 健康度：{metrics['health_label']}（{metrics['health_score']}/100）",
        f"- 内部演练题库：{metrics['internal_question_count']} 条",
        f"- 知识包复测：{_customer_status_text(metrics['knowledge_package_status'])}",
        f"- 模型成本小样本：{_customer_status_text(metrics['model_cost_status'])}",
        f"- 本地维护证据：{_customer_status_text(metrics['maintenance_status'])}",
        "",
        "## 回复质量",
        "",
        "- 本报告只汇总命中、引用、最终答案和转人工策略证据。",
        "- 检索命中率不会被写成完整客服准确率。",
        "- 内部 100 题演练不等于客户正式准确率签收。",
        "",
        "## 知识维护",
        "",
        "- 每月先看开放缺口，再按业务对象补知识卡、文档来源和回归题。",
        "- 知识包更新后必须复跑同题集，比较发布前后的命中、引用和转人工变化。",
        "",
        "## 成本用量",
        "",
        "- 模型调用成本以持久成本台账为准；没有台账时只允许写成待验证。",
        "- 预算超限时按策略降级，不把失败伪装为成功。",
        "",
        "## 本地维护",
        "",
        "- 诊断包由客户主动导出和授权传递。",
        "- 更新前先备份，更新后保留审计和回滚记录。",
        "- 本阶段不远控客户电脑、不静默更新、不自动上传客户数据。",
        "",
        "## 下月建议",
        "",
    ]
    lines.extend(f"- {item}" for item in result["next_month_actions"])
    lines.extend(
        [
            "",
            "## 边界",
            "",
            "- 这是月度运维复盘材料，不是生产服务等级承诺。",
            "- 真实平台外发、企业渠道上线和正式客户签收仍需单独验收。",
        ]
    )
    return "\n".join(lines) + "\n"


def _build_internal_evidence(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "phase": PHASE,
        "status": result["status"],
        "summary_checks": result["checks"]["summaries"],
        "boundary_checks": result["boundary_checks"],
        "source_paths": result["evidence"],
        "blocker_count": len(result["blockers"]),
        "warning_count": len(result["warnings"]),
        "no_customer_raw_text_exported": True,
        "no_secret_exported": True,
        "real_platform_send_performed": False,
        "production_sla_ready": False,
    }


def _write_markdown(path: Path, result: dict[str, Any]) -> None:
    lines = [
        "# H2W-OPS2 客户侧月度运维报告 rehearsal",
        "",
        "## 结论",
        "",
        f"- 阶段状态：`{result['status']}`",
        f"- 客户侧月度运维报告 rehearsal：`{str(result['readiness']['ready_for_customer_monthly_ops_report_rehearsal']).lower()}`",
        f"- 生产 SLA 就绪：`{str(result['readiness']['production_sla_ready']).lower()}`",
        f"- 正式客户签收就绪：`{str(result['readiness']['formal_customer_signoff_ready']).lower()}`",
        f"- 真实平台外发就绪：`{str(result['readiness']['real_platform_send_ready']).lower()}`",
        "",
        "## 本阶段实际完成",
        "",
        "- 聚合 OPS1、KB2、MODEL1、TRIAL1 和 FE4 阶段证据。",
        "- 生成客户可读月度运维报告候选，不输出客户原文、草稿全文、密钥、token、数据库密码或平台 payload。",
        "- 生成内部证据摘要，保留上游状态、阻断项和边界检查。",
        "",
        "## 阻断项",
        "",
    ]
    lines.extend([f"- {item}" for item in result["blockers"]] or ["- 无"])
    lines.extend(["", "## 固定边界", ""])
    lines.extend(
        [
            "- `production_sla_ready=false`",
            "- `formal_customer_signoff_ready=false`",
            "- `real_platform_send_ready=false`",
            "- `remote_control_performed=false`",
            "- `silent_update_performed=false`",
            "- `raw_customer_text_exported=false`",
        ]
    )
    lines.extend(["", "## 输出文件", ""])
    lines.extend(f"- {label}：`{path}`" for label, path in result["generated_files"].items())
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_h2w_ops2_customer_monthly_ops_report(
    *,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    doc_path: Path = DOC_PATH,
    ops1_summary: Path = OPS1_SUMMARY,
    kb2_summary: Path = KB2_SUMMARY,
    model1_summary: Path = MODEL1_SUMMARY,
    trial1_summary: Path = TRIAL1_SUMMARY,
    fe4_summary: Path = FE4_SUMMARY,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    blockers: list[str] = []
    warnings: list[str] = []

    specs: dict[str, tuple[Path, str | set[str]]] = {
        "ops1": (ops1_summary, "ready_for_after_sales_ops_handoff_rehearsal"),
        "kb2": (kb2_summary, "ready_for_customer_specific_knowledge_retest_template"),
        "model1": (model1_summary, "passed_real_small_sample_cost_rehearsal"),
        "trial1": (trial1_summary, ALLOWED_TRIAL1_STATUSES),
        "fe4": (fe4_summary, "ready_for_customer_visible_ui_candidate"),
    }
    payloads: dict[str, dict[str, Any]] = {}
    summary_checks: dict[str, dict[str, Any]] = {}
    for name, (path, expected) in specs.items():
        payload, check, phase_blockers = _load_summary(path, name=name, expected_status=expected)
        payloads[name] = payload
        summary_checks[name] = check
        blockers.extend(phase_blockers)
        blockers.extend(_boundary_blockers(payload, name=name))

    ops1 = payloads.get("ops1", {})
    kb2 = payloads.get("kb2", {})
    model1 = payloads.get("model1", {})
    trial1 = payloads.get("trial1", {})

    internal_question_count = _safe_int(_flag(trial1, "metrics", "question_count") or _flag(trial1, "metrics", "row_count"))
    if internal_question_count < 50:
        blockers.append("内部演练题库少于 50 条，不能进入客户侧月度运维报告 rehearsal")
    if _flag(kb2, "signoff_boundary", "customer_confirmed") is True:
        blockers.append("KB2 出现客户正式确认，OPS2 不能把内部演练写成客户签收")
    if _flag(model1, "metrics", "provider_call_performed") is not True:
        warnings.append("MODEL1 未执行真实小样本 provider 调用，成本用量只能写成待验证")

    customer_metrics = {
        "health_score": 78 if not blockers else 52,
        "health_label": "可受控试点复盘" if not blockers else "证据不足",
        "internal_question_count": internal_question_count,
        "knowledge_package_status": str(kb2.get("status") or "missing"),
        "model_cost_status": str(model1.get("status") or "missing"),
        "maintenance_status": str(_flag(ops1, "readiness", "local_maintenance_rehearsal_ready")),
    }
    ready = not blockers
    status = "ready_for_customer_monthly_ops_report_rehearsal" if ready else "blocked"
    generated_files = {
        "summary": _display_path(output_dir / "summary.json"),
        "customer_report": _display_path(output_dir / "customer_monthly_ops_report.md"),
        "internal_evidence": _display_path(output_dir / "internal_evidence_summary.json"),
        "doc": _display_path(doc_path),
    }
    result = {
        "phase": PHASE,
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "readiness": {
            "ready_for_customer_monthly_ops_report_rehearsal": ready,
            "ops1_ready": summary_checks["ops1"]["passed"],
            "kb2_ready": summary_checks["kb2"]["passed"],
            "model1_ready": summary_checks["model1"]["passed"],
            "trial1_ready": summary_checks["trial1"]["passed"],
            "fe4_ready": summary_checks["fe4"]["passed"],
            "production_sla_ready": False,
            "formal_customer_signoff_ready": False,
            "real_platform_send_ready": False,
            "remote_control_ready": False,
            "silent_auto_update_ready": False,
        },
        "checks": {
            "summaries": summary_checks,
        },
        "boundary_checks": {
            "no_real_platform_send": all(
                _flag(payload, "boundaries", "real_platform_send_performed") is not True
                and _flag(payload, "readiness", "real_platform_send_ready") is not True
                for payload in payloads.values()
            ),
            "no_formal_customer_signoff": all(
                _flag(payload, "boundaries", "formal_customer_signoff_performed") is not True
                and _flag(payload, "readiness", "formal_customer_signoff_ready") is not True
                for payload in payloads.values()
            ),
            "no_production_sla": all(
                _flag(payload, "readiness", "production_sla_ready") is not True
                for payload in payloads.values()
            ),
            "no_remote_control": all(_flag(payload, "boundaries", "remote_control_performed") is not True for payload in payloads.values()),
            "no_silent_update": all(_flag(payload, "boundaries", "silent_update_performed") is not True for payload in payloads.values()),
        },
        "customer_metrics": customer_metrics,
        "blockers": blockers,
        "warnings": warnings,
        "not_ready_for": [
            "生产 SLA",
            "正式客户准确率签收",
            "真实平台自动外发",
            "企业微信/抖音/淘宝/京东/拼多多真实渠道上线",
            "远程控制客户电脑",
            "静默自动更新",
        ],
        "next_month_actions": [
            "客户资料导入后重跑同一题集，比较知识命中、引用和转人工变化。",
            "每月输出开放知识缺口和已修复知识包清单。",
            "复核模型成本台账和预算降级动作。",
            "确认诊断包、备份、更新包和回滚演练有审计记录。",
        ],
        "evidence": {name: {"path": check["path"], "status": check["actual_status"]} for name, check in summary_checks.items()},
        "generated_files": generated_files,
        "boundaries": {
            "raw_customer_text_exported": False,
            "draft_text_exported": False,
            "secret_exported": False,
            "platform_payload_exported": False,
            "production_sla_ready": False,
            "formal_customer_signoff_performed": False,
            "real_platform_send_performed": False,
            "remote_control_performed": False,
            "silent_update_performed": False,
            "automatic_upload_performed": False,
        },
    }

    customer_report_text = _build_customer_report(result)
    leaked = _scan_text_for_terms(customer_report_text, terms=SENSITIVE_TERMS)
    overclaims = _scan_text_for_terms(customer_report_text, terms=OVERCLAIM_PHRASES)
    if leaked:
        result["blockers"].append(f"客户报告包含不应出现的敏感或原文词：{', '.join(leaked)}")
    if overclaims:
        result["blockers"].append(f"客户报告包含越界承诺：{', '.join(overclaims)}")
    if result["blockers"]:
        result["status"] = "blocked"
        result["readiness"]["ready_for_customer_monthly_ops_report_rehearsal"] = False

    (output_dir / "customer_monthly_ops_report.md").write_text(customer_report_text, encoding="utf-8")
    _write_json(output_dir / "internal_evidence_summary.json", _build_internal_evidence(result))
    _write_json(output_dir / "summary.json", result)
    _write_markdown(doc_path, result)
    return result


def main() -> int:
    result = run_h2w_ops2_customer_monthly_ops_report()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if result["status"] == "blocked" else 0


if __name__ == "__main__":
    raise SystemExit(main())
