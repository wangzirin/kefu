#!/usr/bin/env python3
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from lib.h2w_pack8_common import ROOT, base_result, display_path, load_expected_summary, read_csv_rows, read_json, write_json, write_markdown_report, write_text


PHASE = "H2W-KB5"
SCHEMA_VERSION = "p3-06u-26h2w-kb5.customer_knowledge_retest.v1"
DEFAULT_OUTPUT_DIR = ROOT / "output/p3_06u_26h2w_kb5_customer_knowledge_retest"
DOC_PATH = ROOT / "docs/P3-06U-26H2W_KB5_CUSTOMER_KNOWLEDGE_RETEST.md"
DATA1_SUMMARY = ROOT / "output/p3_06u_26h2w_data1_customer_material_intake/summary.json"
KB4_SUMMARY = ROOT / "output/p3_06u_26h2w_kb4_customer_knowledge_trial_loop/summary.json"


def run_h2w_kb5_customer_knowledge_retest(
    *,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    doc_path: Path = DOC_PATH,
) -> dict:
    blockers: list[str] = []
    data1, data1_status, data1_errors = load_expected_summary(
        "data1",
        DATA1_SUMMARY,
        {"customer_materials_ready", "waiting_for_customer_materials", "internal_sample_only_ready"},
    )
    kb4, kb4_status, kb4_errors = load_expected_summary("kb4", KB4_SUMMARY, {"customer_knowledge_trial_loop_ready"})
    blockers.extend(data1_errors)
    blockers.extend(kb4_errors)
    manifest = data1.get("manifest", {}) if isinstance(data1.get("manifest"), dict) else {}
    materials_path = ROOT / str(manifest.get("files", {}).get("materials_csv", ""))
    questions_path = ROOT / str(manifest.get("files", {}).get("trial_questions_csv", ""))
    materials = read_csv_rows(materials_path)
    questions = read_csv_rows(questions_path)
    type_counts = Counter(row.get("record_type", "") for row in materials)
    source_coverage = sum(1 for row in materials if row.get("source_uri")) / max(len(materials), 1)
    forbidden_checks = sum(1 for row in materials if row.get("forbidden_terms"))
    handoff_checks = sum(1 for row in materials if row.get("handoff_condition"))

    if len(questions) < 50:
        blockers.append(f"试跑题库不足 50 条：当前 {len(questions)} 条")
    for record_type in ["business_object", "standard_qa", "process_policy", "forbidden_commitment", "handoff_rule"]:
        if type_counts.get(record_type, 0) <= 0:
            blockers.append(f"资料缺少四层知识类型：{record_type}")

    report_path = output_dir / "customer_knowledge_retest_report.md"
    status = (
        "customer_knowledge_retest_ready_with_customer_data"
        if data1.get("customer_data_used") is True
        else "customer_knowledge_retest_ready_with_internal_data"
    )
    result = base_result(SCHEMA_VERSION, PHASE, status, blockers)
    result.update(
        {
            "upstreams": {"data1": data1_status, "kb4": kb4_status},
            "metrics": {
                "material_rows": len(materials),
                "trial_question_count": len(questions),
                "record_type_counts": dict(type_counts),
                "source_coverage": round(source_coverage, 4),
                "forbidden_commitment_rows": forbidden_checks,
                "handoff_rule_rows": handoff_checks,
            },
            "evidence_paths": [display_path(report_path), display_path(materials_path), display_path(questions_path)],
            "readiness": {
                "customer_knowledge_retest_ready": not blockers,
                "final_answer_quality_candidate": not blockers,
                "formal_online_accuracy_signoff_ready": False,
                "system_prefilled_customer_confirmation": False,
                "real_platform_send_ready": False,
            },
        }
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    write_json(output_dir / "summary.json", result)
    write_text(
        report_path,
        "\n".join(
            [
                "# H2W-KB5 客户知识导入与复测报告",
                "",
                f"- 阶段状态：`{result['status']}`",
                f"- 资料行数：{len(materials)}",
                f"- 试跑题数：{len(questions)}",
                f"- 来源覆盖：{source_coverage:.2%}",
                "- 本报告是客服答案质量候选复测，不是正式线上准确率签收。",
                "- 系统不会替客户填写确认人、确认时间或签收结果。",
                "",
            ]
        ),
    )
    write_markdown_report(
        doc_path,
        "H2W-KB5 客户知识导入与复测",
        result,
        [
            ("指标", [f"{key}: {value}" for key, value in result["metrics"].items()]),
            ("证据", result["evidence_paths"]),
        ],
    )
    return result


def main() -> int:
    result = run_h2w_kb5_customer_knowledge_retest()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] != "blocked" else 1


if __name__ == "__main__":
    raise SystemExit(main())
