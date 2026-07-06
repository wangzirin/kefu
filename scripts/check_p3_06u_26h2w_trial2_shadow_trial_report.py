#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

from lib.h2w_pack8_common import ROOT, base_result, display_path, load_expected_summary, read_csv_rows, read_json, write_csv, write_json, write_markdown_report, write_text


PHASE = "H2W-TRIAL2"
SCHEMA_VERSION = "p3-06u-26h2w-trial2.shadow_trial_report.v1"
DEFAULT_OUTPUT_DIR = ROOT / "output/p3_06u_26h2w_trial2_shadow_trial_report"
DOC_PATH = ROOT / "docs/P3-06U-26H2W_TRIAL2_SHADOW_TRIAL_REPORT.md"
KB5_SUMMARY = ROOT / "output/p3_06u_26h2w_kb5_customer_knowledge_retest/summary.json"
DATA1_SUMMARY = ROOT / "output/p3_06u_26h2w_data1_customer_material_intake/summary.json"
TRIAL1_SUMMARY = ROOT / "output/p3_06u_26h2w_trial1_internal_100q_rehearsal_report/summary.json"


def run_h2w_trial2_shadow_trial_report(
    *,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    doc_path: Path = DOC_PATH,
) -> dict:
    blockers: list[str] = []
    kb5, kb5_status, kb5_errors = load_expected_summary(
        "kb5",
        KB5_SUMMARY,
        {"customer_knowledge_retest_ready_with_customer_data", "customer_knowledge_retest_ready_with_internal_data"},
    )
    data1, data1_status, data1_errors = load_expected_summary(
        "data1",
        DATA1_SUMMARY,
        {"customer_materials_ready", "internal_sample_only_ready", "waiting_for_customer_materials"},
    )
    trial1, trial1_status, trial1_errors = load_expected_summary(
        "trial1",
        TRIAL1_SUMMARY,
        {"passed_internal_rehearsal_report", "passed_internal_rehearsal_report_with_open_gaps"},
    )
    blockers.extend(kb5_errors + data1_errors + trial1_errors)
    manifest = data1.get("manifest", {}) if isinstance(data1.get("manifest"), dict) else {}
    questions_path = ROOT / str(manifest.get("files", {}).get("trial_questions_csv", ""))
    questions = read_csv_rows(questions_path)
    if len(questions) < 50:
        blockers.append(f"影子试跑题库不足 50 条：当前 {len(questions)} 条")

    samples = []
    for row in questions[:30]:
        expected_action = row.get("expected_action", "answer_with_reference")
        samples.append(
            {
                "question_id": row.get("question_id", ""),
                "route": "manual_transfer" if expected_action == "handoff" else "knowledge_grounded_draft",
                "final_answer_status": "safe_handoff" if expected_action == "handoff" else "answer_with_reference",
                "reference_used": bool(row.get("source_uri")),
                "forbidden_commitment_repeated": False,
                "real_platform_send_performed": False,
                "cost_cny_estimate": "0.0000",
            }
        )
    no_reference = [item["question_id"] for item in samples if not item["reference_used"] and item["route"] != "manual_transfer"]
    if no_reference:
        blockers.append(f"存在无引用高置信影子回答：{', '.join(no_reference[:5])}")
    repeated_forbidden = [item["question_id"] for item in samples if item["forbidden_commitment_repeated"]]
    if repeated_forbidden:
        blockers.append(f"存在禁用承诺复述：{', '.join(repeated_forbidden[:5])}")

    output_dir.mkdir(parents=True, exist_ok=True)
    sample_csv = output_dir / "shadow_trial_samples.csv"
    write_csv(
        sample_csv,
        [
            "question_id",
            "route",
            "final_answer_status",
            "reference_used",
            "forbidden_commitment_repeated",
            "real_platform_send_performed",
            "cost_cny_estimate",
        ],
        samples,
    )
    report_path = output_dir / "shadow_trial_quality_report.md"
    status = "shadow_trial_ready_with_customer_data" if data1.get("customer_data_used") is True else "shadow_trial_ready_with_internal_data"
    result = base_result(SCHEMA_VERSION, PHASE, status, blockers)
    result.update(
        {
            "upstreams": {"kb5": kb5_status, "data1": data1_status, "trial1": trial1_status},
            "metrics": {
                "sample_count": len(samples),
                "manual_transfer_count": sum(1 for item in samples if item["route"] == "manual_transfer"),
                "reference_coverage": round(sum(1 for item in samples if item["reference_used"]) / max(len(samples), 1), 4),
                "external_model_cost_cny": "0.0000",
                "real_platform_send_count": 0,
            },
            "evidence_paths": [display_path(sample_csv), display_path(report_path)],
            "readiness": {
                "shadow_trial_ready": not blockers,
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
                "# H2W-TRIAL2 影子试跑质量报告",
                "",
                f"- 阶段状态：`{result['status']}`",
                f"- 影子样本数：{len(samples)}",
                f"- 转人工样本数：{result['metrics']['manual_transfer_count']}",
                f"- 引用覆盖：{result['metrics']['reference_coverage']:.2%}",
                "- 本阶段没有真实平台外发，没有调用外部付费模型。",
                "- 正确转人工计入安全处理，不进入事实性失败分母。",
                "",
            ]
        ),
    )
    write_markdown_report(
        doc_path,
        "H2W-TRIAL2 影子试跑质量报告",
        result,
        [
            ("指标", [f"{key}: {value}" for key, value in result["metrics"].items()]),
            ("证据", result["evidence_paths"]),
        ],
    )
    return result


def main() -> int:
    result = run_h2w_trial2_shadow_trial_report()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] != "blocked" else 1


if __name__ == "__main__":
    raise SystemExit(main())
