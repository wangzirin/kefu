#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

from lib.h2w_pack8_common import (
    ROOT,
    base_result,
    display_path,
    read_json,
    scan_archive_candidates,
    write_csv,
    write_json,
    write_markdown_report,
    write_text,
)


PHASE = "H2W-DATA1"
SCHEMA_VERSION = "p3-06u-26h2w-data1.customer_material_intake.v1"
DEFAULT_OUTPUT_DIR = ROOT / "output/p3_06u_26h2w_data1_customer_material_intake"
DOC_PATH = ROOT / "docs/P3-06U-26H2W_DATA1_CUSTOMER_MATERIAL_INTAKE.md"
INTAKE_DIR = ROOT / "evals/p3_06u_26h2w_data1_customer_material_intake"
TRIAL_C0_SUMMARY = ROOT / "output/p3_06u_26h2w_trial_c0_co_creation_scope/summary.json"


FIELDNAMES = [
    "record_type",
    "item_id",
    "business_object",
    "title",
    "question",
    "standard_answer",
    "source_uri",
    "expected_behavior",
    "forbidden_terms",
    "handoff_condition",
]


def _sample_rows() -> list[dict[str, str]]:
    base_rows = [
        {
            "record_type": "business_object",
            "item_id": "OBJ-001",
            "business_object": "入门验证版客服系统",
            "title": "产品对象",
            "question": "你们最基础的客服系统适合谁？",
            "standard_answer": "适合需要先验证官网或私域客服的团队，重点是知识问答、留资和转人工边界。",
            "source_uri": "internal://pack8/sample/business-object",
            "expected_behavior": "引用产品对象后回答，不承诺真实平台已接通。",
            "forbidden_terms": "禁止承诺官方渠道已授权;禁止承诺平台外发已启用",
            "handoff_condition": "客户要求真实平台上线或合同承诺时转人工",
        },
        {
            "record_type": "process_policy",
            "item_id": "POL-001",
            "business_object": "本地试跑",
            "title": "本地部署流程",
            "question": "客户怎么启动本地试跑？",
            "standard_answer": "先准备客户环境文件，再运行本地启动脚本，系统会检查 Docker、端口、外发关闭和负责人账号。",
            "source_uri": "internal://pack8/sample/local-startup",
            "expected_behavior": "说明步骤和边界，不要求客户提供真实密钥。",
            "forbidden_terms": "默认密码;静默更新",
            "handoff_condition": "客户机器无法启动 Docker 时转人工",
        },
        {
            "record_type": "forbidden_commitment",
            "item_id": "FORBID-001",
            "business_object": "售前边界",
            "title": "禁用承诺",
            "question": "能不能保证准确率百分之百？",
            "standard_answer": "不能承诺百分之百准确率。试跑阶段会提供题库复测、质量报告和知识缺口修复建议。",
            "source_uri": "internal://pack8/sample/forbidden",
            "expected_behavior": "明确拒绝绝对化承诺。",
            "forbidden_terms": "百分之百准确;永不出错",
            "handoff_condition": "客户要求写入合同保证时转人工",
        },
        {
            "record_type": "handoff_rule",
            "item_id": "HANDOFF-001",
            "business_object": "人工接管",
            "title": "转人工规则",
            "question": "什么情况要转人工？",
            "standard_answer": "涉及价格合同、退款争议、投诉、平台真实接入、个人隐私或无法从知识库确认的问题，都应转人工。",
            "source_uri": "internal://pack8/sample/handoff",
            "expected_behavior": "把转人工视作安全处理，不算事实性失败。",
            "forbidden_terms": "自动处理所有问题",
            "handoff_condition": "命中争议、投诉、合同或隐私",
        },
    ]
    for index in range(1, 61):
        base_rows.append(
            {
                "record_type": "standard_qa",
                "item_id": f"QA-{index:03d}",
                "business_object": "共创试跑客服系统",
                "title": f"试跑问答 {index:03d}",
                "question": f"第 {index} 个客户常见问题应该如何处理？",
                "standard_answer": "先根据已发布知识资料回答；如果涉及未确认政策、价格承诺或真实平台上线，就提示需要人工确认。",
                "source_uri": f"internal://pack8/sample/qa/{index:03d}",
                "expected_behavior": "引用来源并保持受控试跑边界。",
                "forbidden_terms": "禁止承诺平台外发已启用;禁止承诺正式签收完成",
                "handoff_condition": "资料缺失或客户要求承诺",
            }
        )
    return base_rows


def run_h2w_data1_customer_material_intake(
    *,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    doc_path: Path = DOC_PATH,
    intake_dir: Path = INTAKE_DIR,
) -> dict:
    blockers: list[str] = []
    trial_c0 = read_json(TRIAL_C0_SUMMARY)
    if trial_c0.get("status") != "trial_scope_ready":
        blockers.append(f"TRIAL-C0 上游状态不满足：{trial_c0.get('status') or 'missing'}")

    intake_dir.mkdir(parents=True, exist_ok=True)
    materials_csv = intake_dir / "customer_materials_internal_sample.csv"
    questions_csv = intake_dir / "customer_trial_questions_internal_sample.csv"
    manifest_path = intake_dir / "manifest.json"
    rows = _sample_rows()
    write_csv(materials_csv, FIELDNAMES, rows)
    write_csv(questions_csv, ["question_id", "question", "expected_answer", "expected_action", "source_uri"], [
            {
                "question_id": row["item_id"],
                "question": row["question"],
                "expected_answer": row["standard_answer"],
                "expected_action": "answer_with_reference" if row["record_type"] != "handoff_rule" else "handoff",
                "source_uri": row["source_uri"],
            }
            for row in rows
            if row["record_type"] in {"standard_qa", "handoff_rule", "forbidden_commitment"}
        ])

    manifest = {
        "schema_version": SCHEMA_VERSION,
        "material_source": "internal_rehearsal_sample",
        "customer_data_used": False,
        "internal_sample_only": True,
        "files": {
            "materials_csv": display_path(materials_csv),
            "trial_questions_csv": display_path(questions_csv),
        },
        "record_count": len(rows),
        "question_count": 62,
        "desensitization_statement": "内部准真实样板，不含真实客户原文、手机号、邮箱、平台 payload 或密钥。",
    }
    write_json(manifest_path, manifest)
    blockers.extend(scan_archive_candidates([materials_csv, questions_csv, manifest_path]))

    status = "internal_sample_only_ready"
    result = base_result(SCHEMA_VERSION, PHASE, status, blockers)
    result.update(
        {
            "status": "blocked" if blockers else status,
            "manifest": manifest,
            "evidence_paths": [display_path(manifest_path), display_path(materials_csv), display_path(questions_csv)],
            "readiness": {
                "customer_materials_ready": False,
                "waiting_for_customer_materials": False,
                "internal_sample_only_ready": not blockers,
                "raw_customer_text_included": False,
                "secrets_included": False,
                "platform_payload_included": False,
            },
        }
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    write_json(output_dir / "summary.json", result)
    write_json(output_dir / "manifest_snapshot.json", manifest)
    write_markdown_report(
        doc_path,
        "H2W-DATA1 客户资料与问题接收门禁",
        result,
        [
            ("资料状态", ["当前使用内部准真实样板；未使用真实客户资料。", f"资料行数：{len(rows)}"]),
            ("证据文件", result["evidence_paths"]),
            ("安全声明", [manifest["desensitization_statement"]]),
        ],
    )
    return result


def main() -> int:
    result = run_h2w_data1_customer_material_intake()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] != "blocked" else 1


if __name__ == "__main__":
    raise SystemExit(main())
