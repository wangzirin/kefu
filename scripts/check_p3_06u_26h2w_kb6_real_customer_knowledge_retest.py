#!/usr/bin/env python3
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from check_p3_06u_26h2w_data2_real_customer_material_readiness import RECEIVED_MATERIALS, RECEIVED_QUESTIONS
from check_p3_06u_26h2w_data2r_real_customer_materials import (
    INTERNAL_SAMPLE_STATUS,
    READY_STATUS,
    WAITING_STATUS,
    run_h2w_data2r_real_customer_materials,
)
from lib.h2w_pack8_common import (
    ROOT,
    base_result,
    display_path,
    read_csv_rows,
    write_json,
    write_markdown_report,
    write_text,
)


PHASE = "H2W-KB6"
SCHEMA_VERSION = "p3-06u-26h2w-kb6.real_customer_knowledge_retest.v1"
DEFAULT_OUTPUT_DIR = ROOT / "output/p3_06u_26h2w_kb6_real_customer_knowledge_retest"
DOC_PATH = ROOT / "docs/P3-06U-26H2W_KB6_REAL_CUSTOMER_KNOWLEDGE_RETEST.md"

REQUIRED_RECORD_TYPES = {
    "business_object": "业务对象",
    "standard_qa": "标准问答",
    "process_policy": "流程政策",
    "forbidden_commitment": "禁用承诺",
    "handoff_rule": "转人工规则",
}


def _waiting_result(output_dir: Path, doc_path: Path, data2r: dict[str, Any]) -> dict[str, Any]:
    result = base_result(SCHEMA_VERSION, PHASE, WAITING_STATUS, [])
    result.update(
        {
            "status": WAITING_STATUS,
            "upstreams": {"data2r": data2r.get("status", "missing")},
            "customer_data_used": False,
            "internal_sample_used": False,
            "metrics": {},
            "evidence_paths": [display_path(output_dir / "summary.json"), display_path(doc_path)],
            "readiness": {
                "customer_knowledge_retest_ready": False,
                "waiting_for_real_customer_materials": True,
                "final_answer_quality_candidate": False,
                "formal_online_accuracy_signoff_ready": False,
                "system_prefilled_customer_confirmation": False,
                "real_platform_send_ready": False,
            },
        }
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    write_json(output_dir / "summary.json", result)
    write_markdown_report(
        doc_path,
        "H2W-KB6 真实客户知识导入与复测",
        result,
        [("等待原因", ["真实客户脱敏资料尚未回传；本阶段不会使用内部样板冒充客户资料。"])],
    )
    return result


def run_h2w_kb6_real_customer_knowledge_retest(
    *,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    doc_path: Path = DOC_PATH,
) -> dict[str, Any]:
    data2r = run_h2w_data2r_real_customer_materials()
    data2r_status = str(data2r.get("status") or "missing")
    if data2r_status == WAITING_STATUS:
        return _waiting_result(output_dir, doc_path, data2r)

    blockers: list[str] = []
    if data2r_status not in {READY_STATUS, INTERNAL_SAMPLE_STATUS}:
        blockers.append(f"DATA2R 状态不满足：{data2r_status}")

    materials = read_csv_rows(RECEIVED_MATERIALS)
    questions = read_csv_rows(RECEIVED_QUESTIONS)
    type_counts = Counter(row.get("record_type", "").strip() for row in materials)
    question_actions = Counter(row.get("expected_action", "").strip() for row in questions)
    source_coverage = sum(1 for row in materials if row.get("source_uri", "").strip()) / max(len(materials), 1)
    question_source_coverage = sum(1 for row in questions if row.get("source_uri", "").strip()) / max(len(questions), 1)
    forbidden_rows = sum(1 for row in materials if row.get("record_type") == "forbidden_commitment")
    handoff_rows = sum(1 for row in materials if row.get("record_type") == "handoff_rule")
    no_source_answer_questions = [
        row.get("question_id", "")
        for row in questions
        if row.get("expected_action") == "answer_with_reference" and not row.get("source_uri", "").strip()
    ]

    if len(questions) < 50:
        blockers.append(f"真实客户题库不足 50 条：当前 {len(questions)} 条")
    for record_type, label in REQUIRED_RECORD_TYPES.items():
        if type_counts.get(record_type, 0) <= 0:
            blockers.append(f"真实客户知识资料缺少：{label}")
    if no_source_answer_questions:
        blockers.append(f"存在需要引用回答但缺少来源的问题：{', '.join(no_source_answer_questions[:5])}")
    if forbidden_rows <= 0:
        blockers.append("缺少禁用承诺资料行")
    if handoff_rows <= 0:
        blockers.append("缺少转人工规则资料行")

    report_path = output_dir / "real_customer_knowledge_retest_report.md"
    success_status = (
        "customer_knowledge_retest_ready_with_internal_sample"
        if data2r_status == INTERNAL_SAMPLE_STATUS
        else "customer_knowledge_retest_ready_with_customer_data"
    )
    result = base_result(SCHEMA_VERSION, PHASE, success_status, blockers)
    result.update(
        {
            "upstreams": {"data2r": data2r_status},
            "customer_data_used": not blockers and data2r_status == READY_STATUS,
            "internal_sample_used": not blockers and data2r_status == INTERNAL_SAMPLE_STATUS,
            "metrics": {
                "material_rows": len(materials),
                "trial_question_count": len(questions),
                "record_type_counts": dict(type_counts),
                "question_action_counts": dict(question_actions),
                "source_coverage": round(source_coverage, 4),
                "question_source_coverage": round(question_source_coverage, 4),
                "forbidden_commitment_rows": forbidden_rows,
                "handoff_rule_rows": handoff_rows,
                "unanswered_gap_candidates": len(no_source_answer_questions),
            },
            "evidence_paths": [display_path(report_path), display_path(RECEIVED_MATERIALS), display_path(RECEIVED_QUESTIONS)],
            "readiness": {
                "customer_knowledge_retest_ready": not blockers,
                "waiting_for_real_customer_materials": False,
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
                "# H2W-KB6 真实客户知识导入与复测报告",
                "",
                f"- 阶段状态：`{result['status']}`",
                f"- 真实客户资料行数：{len(materials)}",
                f"- 真实客户题库题数：{len(questions)}",
                f"- 知识来源覆盖：{source_coverage:.2%}",
                f"- 题库引用覆盖：{question_source_coverage:.2%}",
                "- 本报告检查最终客服答案质量所需的知识基础，不把检索命中率写成线上准确率签收。",
                "- 系统不会替客户填写确认人、确认时间或签收结果。",
                "",
            ]
        ),
    )
    write_markdown_report(
        doc_path,
        "H2W-KB6 真实客户知识导入与复测",
        result,
        [
            ("指标", [f"{key}: {value}" for key, value in result["metrics"].items()]),
            ("证据", result["evidence_paths"]),
        ],
    )
    return result


def main() -> int:
    result = run_h2w_kb6_real_customer_knowledge_retest()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if result["status"] == "blocked" else 0


if __name__ == "__main__":
    raise SystemExit(main())
