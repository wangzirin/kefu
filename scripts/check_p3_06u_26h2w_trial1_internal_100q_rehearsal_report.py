#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PHASE = "H2W-TRIAL1"
DEFAULT_OUTPUT_DIR = ROOT / "output/p3_06u_26h2w_trial1_internal_100q_rehearsal_report"
DOC_PATH = ROOT / "docs/P3-06U-26H2W_TRIAL1_INTERNAL_100Q_REHEARSAL_REPORT.md"
H2W11O_SUMMARY = ROOT / "output/p3_06u_26h2w11o_real_customer_eval_bank_import/summary.json"
H2W11P_SUMMARY = ROOT / "output/p3_06u_26h2w11p_final_answer_sampling/summary.json"
FE3_SUMMARY = ROOT / "output/p3_06u_26h2w_fe3_frontend_browser_workflow_qa/summary.json"
PACK1_SUMMARY = ROOT / "output/p3_06u_26h2w_pack1_local_delivery_rehearsal/summary.json"
MODEL1_SUMMARY = ROOT / "output/p3_06u_26h2w_model1_bailian_cost_sample/summary.json"
H2W7D_RUNTIME = ROOT / "output/p3_06u_26h2w7d_runtime_pgvector_rehearsal/summary.json"


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


def _optional_status(path: Path) -> str:
    if not path.exists():
        return "missing"
    return str(_read_json(path).get("status", "unknown"))


def _write_report(path: Path, result: dict[str, Any]) -> None:
    metrics = result["metrics"]
    lines = [
        "# H2W-TRIAL1 内部 100 题完整试点演练报告",
        "",
        "> 本报告是内部演练，不是客户验收，不是正式准确率签收。",
        "",
        "## 总结",
        "",
        f"- 阶段状态：`{result['status']}`",
        f"- 题库来源：`{metrics['dataset_source_type']}`",
        f"- 题库数量：`{metrics['question_count']}`",
        f"- 最终答案事实正确率：`{metrics['final_answer_factuality_rate']}`",
        f"- 引用充分率：`{metrics['citation_sufficient_rate']}`",
        f"- 禁用承诺通过率：`{metrics['forbidden_commitment_pass_rate']}`",
        f"- 转人工正确率：`{metrics['handoff_correct_rate']}`",
        "",
        "## 本轮可用结论",
        "",
        "- 内部 100 题已经可以支撑受控试点前的工程演练。",
        "- 当前结论不能被包装为客户签收，也不能替代真实客户题库。",
        "- 前端、封版包、模型成本和 pgvector runtime 的状态必须继续随本报告同步展示。",
        "",
        "## 开放缺口",
        "",
    ]
    lines.extend([f"- {item}" for item in result["open_gaps"]] or ["- 无"])
    lines.extend(
        [
            "",
            "## 边界",
            "",
            "- `internal_quality_report_candidate=true`",
            "- `customer_quality_report_candidate=false`",
            "- `formal_accuracy_signoff=false`",
            "- `real_platform_send_performed=false`",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_markdown(path: Path, result: dict[str, Any]) -> None:
    lines = [
        "# H2W-TRIAL1 内部 100 题完整试点演练门禁",
        "",
        "## 结论",
        "",
        f"- 阶段状态：`{result['status']}`",
        f"- 内部质量报告候选：`{str(result['readiness']['internal_quality_report_candidate']).lower()}`",
        f"- 客户质量报告候选：`{str(result['readiness']['customer_quality_report_candidate']).lower()}`",
        f"- 正式准确率签收：`{str(result['readiness']['formal_accuracy_signoff']).lower()}`",
        "",
        "## 停止门禁",
        "",
        "- 只看检索命中、不评最终答案时，本阶段不通过。",
        "- 内部题库不能写成客户真实题库。",
        "- 真实外发、企业渠道、RPA 正式交付全部继续关闭。",
        "- summary 与报告标题必须写内部演练。",
        "",
        "## 阻断项",
        "",
    ]
    lines.extend([f"- {item}" for item in result["blockers"]] or ["- 无"])
    lines.extend(["", "## 开放缺口", ""])
    lines.extend([f"- {item}" for item in result["open_gaps"]] or ["- 无"])
    lines.extend(["", "## 输出", ""])
    lines.append(f"- `{result['evidence']['summary_json']['path']}`")
    lines.append(f"- `{result['evidence']['internal_report']['path']}`")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_h2w_trial1_internal_100q_rehearsal_report(
    *,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    h2w11o_summary: Path = H2W11O_SUMMARY,
    h2w11p_summary: Path = H2W11P_SUMMARY,
    fe3_summary: Path = FE3_SUMMARY,
    pack1_summary: Path = PACK1_SUMMARY,
    model1_summary: Path = MODEL1_SUMMARY,
    h2w7d_runtime_summary: Path = H2W7D_RUNTIME,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = output_dir / "summary.json"
    report_path = output_dir / "internal_trial_report.md"
    blockers: list[str] = []
    open_gaps: list[str] = []

    if not h2w11o_summary.exists():
        blockers.append("缺少 H2W-11O 内部 100 题导入证据")
        h2w11o = {}
    else:
        h2w11o = _read_json(h2w11o_summary)
    if not h2w11p_summary.exists():
        blockers.append("缺少 H2W-11P 最终答案采样证据")
        h2w11p = {}
    else:
        h2w11p = _read_json(h2w11p_summary)

    o_metrics = h2w11o.get("metrics", {})
    p_metrics = h2w11p.get("metrics", {})
    source_type = o_metrics.get("dataset_source_type", "")
    question_count = int(o_metrics.get("row_count") or 0)
    internal_bank_ready = (
        h2w11o.get("status") == "passed_internal_rehearsal"
        and question_count == 100
        and source_type == "internal_synthetic_rehearsal"
        and h2w11o.get("boundaries", {}).get("formal_accuracy_signoff_performed") is False
    )
    final_answer_ready = (
        h2w11p.get("status") == "passed"
        and h2w11p.get("readiness", {}).get("ready_for_internal_quality_report_candidate") is True
        and h2w11p.get("readiness", {}).get("ready_for_formal_accuracy_signoff") is False
        and h2w11p.get("boundaries", {}).get("retrieval_only_metric_used_as_accuracy") is False
    )
    if not internal_bank_ready:
        blockers.append("内部 100 题不是 ready 状态，或被错误标记成客户/正式签收")
    if not final_answer_ready:
        blockers.append("最终答案质量采样未 ready，或存在检索命中冒充准确率风险")

    fe3_status = _optional_status(fe3_summary)
    pack1_status = _optional_status(pack1_summary)
    model1_status = _optional_status(model1_summary)
    runtime_status = _optional_status(h2w7d_runtime_summary)
    if fe3_status != "passed":
        open_gaps.append(f"FE3 前端真实工作流状态为 {fe3_status}")
    if not pack1_status.startswith("passed"):
        open_gaps.append(f"PACK1 本地封版包状态为 {pack1_status}")
    if model1_status != "passed_real_small_sample_cost_rehearsal":
        open_gaps.append(f"MODEL1 真实小样本成本状态为 {model1_status}；默认不调用付费模型是预期边界")
    if runtime_status != "ready_for_runtime_rehearsal":
        open_gaps.append(f"7D-runtime pgvector 状态为 {runtime_status}")

    status = "blocked" if blockers else ("passed_internal_rehearsal_report_with_open_gaps" if open_gaps else "passed_internal_rehearsal_report")
    result = {
        "phase": PHASE,
        "status": status,
        "readiness": {
            "internal_100q_bank_ready": internal_bank_ready,
            "final_answer_sampling_ready": final_answer_ready,
            "internal_quality_report_candidate": not blockers,
            "customer_quality_report_candidate": False,
            "formal_accuracy_signoff": False,
        },
        "metrics": {
            "dataset_source_type": source_type,
            "question_count": question_count,
            "sample_count": int(p_metrics.get("sample_count") or 0),
            "final_answer_factuality_rate": p_metrics.get("final_answer_factuality_rate"),
            "citation_sufficient_rate": p_metrics.get("citation_sufficient_rate"),
            "forbidden_commitment_pass_rate": p_metrics.get("forbidden_commitment_pass_rate"),
            "handoff_correct_rate": p_metrics.get("handoff_correct_rate"),
        },
        "stage_statuses": {
            "fe3": fe3_status,
            "pack1": pack1_status,
            "model1": model1_status,
            "h2w7d_runtime": runtime_status,
        },
        "blockers": blockers,
        "open_gaps": open_gaps,
        "evidence": {
            "summary_json": {"path": _display_path(summary_path)},
            "internal_report": {"path": _display_path(report_path)},
            "h2w11o_summary": {"path": _display_path(h2w11o_summary), "present": h2w11o_summary.exists()},
            "h2w11p_summary": {"path": _display_path(h2w11p_summary), "present": h2w11p_summary.exists()},
        },
        "boundaries": {
            "internal_rehearsal_not_customer_signoff": True,
            "customer_quality_report_candidate": False,
            "formal_accuracy_signoff_performed": False,
            "real_platform_send_performed": False,
            "enterprise_channel_scope_included": False,
            "rpa_formal_delivery_included": False,
        },
    }
    _write_json(summary_path, result)
    _write_report(report_path, result)
    _write_markdown(DOC_PATH, result)
    return result


def main() -> int:
    result = run_h2w_trial1_internal_100q_rehearsal_report()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if result["status"] == "blocked" else 0


if __name__ == "__main__":
    raise SystemExit(main())
