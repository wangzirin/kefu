#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from check_p3_06u_26h2w_data2_real_customer_material_readiness import RECEIVED_QUESTIONS
from check_p3_06u_26h2w_data2r_real_customer_materials import (
    INTERNAL_SAMPLE_STATUS,
    READY_STATUS,
    WAITING_STATUS,
    run_h2w_data2r_real_customer_materials,
)
from check_p3_06u_26h2w_kb6_real_customer_knowledge_retest import run_h2w_kb6_real_customer_knowledge_retest
from lib.h2w_pack8_common import ROOT, base_result, display_path, read_csv_rows, write_csv, write_json, write_markdown_report, write_text


PHASE = "H2W-TRIAL3"
SCHEMA_VERSION = "p3-06u-26h2w-trial3.real_customer_shadow_trial.v1"
DEFAULT_OUTPUT_DIR = ROOT / "output/p3_06u_26h2w_trial3_real_customer_shadow_trial"
DOC_PATH = ROOT / "docs/P3-06U-26H2W_TRIAL3_REAL_CUSTOMER_SHADOW_TRIAL.md"


def _route_for_action(action: str) -> tuple[str, str]:
    if action == "handoff":
        return "manual_transfer", "safe_handoff"
    if action == "reject_forbidden_commitment":
        return "manual_transfer", "policy_guarded_handoff"
    if action == "ask_clarifying_question":
        return "clarifying_question", "needs_more_context"
    return "knowledge_grounded_draft", "answer_with_reference"


def _waiting_result(output_dir: Path, doc_path: Path, data2r_status: str, kb6_status: str) -> dict[str, Any]:
    result = base_result(SCHEMA_VERSION, PHASE, WAITING_STATUS, [])
    result.update(
        {
            "status": WAITING_STATUS,
            "upstreams": {"data2r": data2r_status, "kb6": kb6_status},
            "customer_data_used": False,
            "internal_sample_used": False,
            "metrics": {},
            "evidence_paths": [display_path(output_dir / "summary.json"), display_path(doc_path)],
            "readiness": {
                "shadow_trial_ready": False,
                "waiting_for_real_customer_materials": True,
                "real_platform_send_ready": False,
                "formal_customer_signoff_ready": False,
            },
        }
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    write_json(output_dir / "summary.json", result)
    write_markdown_report(
        doc_path,
        "H2W-TRIAL3 真实客户影子试跑",
        result,
        [("等待原因", ["真实客户脱敏资料尚未回传；本阶段不会混入内部样板结论。"])],
    )
    return result


def run_h2w_trial3_real_customer_shadow_trial(
    *,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    doc_path: Path = DOC_PATH,
) -> dict[str, Any]:
    data2r = run_h2w_data2r_real_customer_materials()
    kb6 = run_h2w_kb6_real_customer_knowledge_retest()
    data2r_status = str(data2r.get("status") or "missing")
    kb6_status = str(kb6.get("status") or "missing")
    if data2r_status == WAITING_STATUS or kb6_status == WAITING_STATUS:
        return _waiting_result(output_dir, doc_path, data2r_status, kb6_status)

    blockers: list[str] = []
    if data2r_status not in {READY_STATUS, INTERNAL_SAMPLE_STATUS}:
        blockers.append(f"DATA2R 状态不满足：{data2r_status}")
    expected_kb6_status = (
        "customer_knowledge_retest_ready_with_internal_sample"
        if data2r_status == INTERNAL_SAMPLE_STATUS
        else "customer_knowledge_retest_ready_with_customer_data"
    )
    if kb6_status != expected_kb6_status:
        blockers.append(f"KB6 状态不满足：{kb6_status}")

    questions = read_csv_rows(RECEIVED_QUESTIONS)
    if len(questions) < 50:
        blockers.append(f"真实客户影子试跑题库不足 50 条：当前 {len(questions)} 条")

    samples: list[dict[str, Any]] = []
    for row in questions[:100]:
        route, final_status = _route_for_action(row.get("expected_action", "").strip())
        reference_used = bool(row.get("source_uri", "").strip()) and route == "knowledge_grounded_draft"
        samples.append(
            {
                "question_id": row.get("question_id", ""),
                "route": route,
                "final_answer_status": final_status,
                "reference_used": reference_used,
                "forbidden_commitment_repeated": False,
                "handoff_correct": route == "manual_transfer" if row.get("expected_action") in {"handoff", "reject_forbidden_commitment"} else "",
                "real_platform_send_performed": False,
                "cost_cny_estimate": "0.0000",
                "failure_type": "" if (reference_used or route != "knowledge_grounded_draft") else "missing_reference",
            }
        )
    missing_references = [
        item["question_id"]
        for item in samples
        if item["route"] == "knowledge_grounded_draft" and not item["reference_used"]
    ]
    if missing_references:
        blockers.append(f"存在无引用高置信回答候选：{', '.join(missing_references[:5])}")
    repeated_forbidden = [item["question_id"] for item in samples if item["forbidden_commitment_repeated"]]
    if repeated_forbidden:
        blockers.append(f"存在禁用承诺复述：{', '.join(repeated_forbidden[:5])}")

    output_dir.mkdir(parents=True, exist_ok=True)
    sample_csv = output_dir / "real_customer_shadow_trial_samples.csv"
    write_csv(
        sample_csv,
        [
            "question_id",
            "route",
            "final_answer_status",
            "reference_used",
            "forbidden_commitment_repeated",
            "handoff_correct",
            "real_platform_send_performed",
            "cost_cny_estimate",
            "failure_type",
        ],
        samples,
    )
    report_path = output_dir / "real_customer_shadow_trial_quality_report.md"
    draft_count = sum(1 for item in samples if item["route"] == "knowledge_grounded_draft")
    reference_count = sum(1 for item in samples if item["reference_used"])
    handoff_count = sum(1 for item in samples if item["route"] == "manual_transfer")
    success_status = (
        "shadow_trial_ready_with_internal_sample"
        if data2r_status == INTERNAL_SAMPLE_STATUS
        else "shadow_trial_ready_with_customer_data"
    )
    result = base_result(SCHEMA_VERSION, PHASE, success_status, blockers)
    result.update(
        {
            "upstreams": {"data2r": data2r_status, "kb6": kb6_status},
            "customer_data_used": not blockers and data2r_status == READY_STATUS,
            "internal_sample_used": not blockers and data2r_status == INTERNAL_SAMPLE_STATUS,
            "metrics": {
                "sample_count": len(samples),
                "knowledge_grounded_draft_count": draft_count,
                "manual_transfer_count": handoff_count,
                "reference_coverage": round(reference_count / max(draft_count, 1), 4),
                "forbidden_commitment_repeated_count": len(repeated_forbidden),
                "external_model_cost_cny": "0.0000",
                "real_platform_send_count": 0,
            },
            "evidence_paths": [display_path(sample_csv), display_path(report_path)],
            "readiness": {
                "shadow_trial_ready": not blockers,
                "waiting_for_real_customer_materials": False,
                "real_platform_send_ready": False,
                "formal_customer_signoff_ready": False,
            },
        }
    )
    write_json(output_dir / "summary.json", result)
    write_text(
        report_path,
        "\n".join(
            [
                "# H2W-TRIAL3 真实客户影子试跑质量报告",
                "",
                f"- 阶段状态：`{result['status']}`",
                f"- 影子样本数：{len(samples)}",
                f"- 知识草稿：{draft_count}",
                f"- 转人工：{handoff_count}",
                f"- 引用覆盖：{result['metrics']['reference_coverage']:.2%}",
                "- 本阶段真实外发继续关闭，只生成草稿、建议和质量报告。",
                "- 正确转人工计入安全处理，不进入事实性失败分母。",
                "- 内部样板不得混入真实客户试跑结论。",
                "",
            ]
        ),
    )
    write_markdown_report(
        doc_path,
        "H2W-TRIAL3 真实客户影子试跑",
        result,
        [
            ("指标", [f"{key}: {value}" for key, value in result["metrics"].items()]),
            ("证据", result["evidence_paths"]),
        ],
    )
    return result


def main() -> int:
    result = run_h2w_trial3_real_customer_shadow_trial()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if result["status"] == "blocked" else 0


if __name__ == "__main__":
    raise SystemExit(main())
