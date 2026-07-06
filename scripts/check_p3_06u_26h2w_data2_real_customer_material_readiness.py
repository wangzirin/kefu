#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from lib.h2w_pack8_common import (
    ROOT,
    base_result,
    display_path,
    read_csv_rows,
    read_json,
    scan_text_file,
    write_csv,
    write_json,
    write_markdown_report,
    write_text,
)


PHASE = "H2W-DATA2"
SCHEMA_VERSION = "p3-06u-26h2w-data2.real_customer_material_readiness.v1"
DEFAULT_OUTPUT_DIR = ROOT / "output/p3_06u_26h2w_data2_real_customer_material_readiness"
DOC_PATH = ROOT / "docs/P3-06U-26H2W_DATA2_REAL_CUSTOMER_MATERIAL_READINESS.md"
INTAKE_DIR = ROOT / "evals/p3_06u_26h2w_data2_real_customer_material_readiness"
PACK8_SUMMARY = ROOT / "output/p3_06u_26h2w_pack8_trial_package_v1_1/summary.json"

MATERIALS_TEMPLATE = INTAKE_DIR / "customer_materials_real_template.csv"
QUESTIONS_TEMPLATE = INTAKE_DIR / "customer_trial_questions_real_template.csv"
MANIFEST_TEMPLATE = INTAKE_DIR / "customer_material_manifest_template.json"
README_PATH = INTAKE_DIR / "README.md"

RECEIVED_MATERIALS = INTAKE_DIR / "customer_materials_received.csv"
RECEIVED_QUESTIONS = INTAKE_DIR / "customer_trial_questions_received.csv"
RECEIVED_MANIFEST = INTAKE_DIR / "customer_material_manifest_received.json"

MATERIAL_FIELDS = [
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
    "desensitization_note",
]
QUESTION_FIELDS = [
    "question_id",
    "question",
    "expected_answer",
    "expected_action",
    "source_uri",
    "business_object",
    "desensitization_note",
]
REQUIRED_RECORD_TYPES = {
    "business_object",
    "standard_qa",
    "process_policy",
    "forbidden_commitment",
    "handoff_rule",
}
VALID_ACTIONS = {"answer_with_reference", "handoff", "reject_forbidden_commitment", "ask_clarifying_question"}
READY_STATUS = "customer_real_materials_ready"
INTERNAL_SAMPLE_STATUS = "internal_sample_materials_ready_for_rehearsal"


def _template_material_rows() -> list[dict[str, str]]:
    return [
        {
            "record_type": "business_object",
            "item_id": "OBJ-001",
            "business_object": "示例产品或服务名称",
            "title": "示例业务对象",
            "question": "客户会怎么问这个产品或服务？",
            "standard_answer": "请填写脱敏后的标准答法，不要填写真实联系人、手机号、订单号或平台消息原文。",
            "source_uri": "customer-doc://example/product-introduction",
            "expected_behavior": "引用来源后回答；资料不足时转人工。",
            "forbidden_terms": "请填写不能承诺的词或短语，用分号分隔。",
            "handoff_condition": "请填写需要转人工的情况。",
            "desensitization_note": "示例行，正式回传前请删除。",
        }
    ]


def _template_question_rows() -> list[dict[str, str]]:
    return [
        {
            "question_id": "Q-001",
            "question": "脱敏后的客户问题",
            "expected_answer": "业务负责人确认过的期望答案",
            "expected_action": "answer_with_reference",
            "source_uri": "customer-doc://example/product-introduction",
            "business_object": "示例产品或服务名称",
            "desensitization_note": "示例行，正式回传前请删除。",
        }
    ]


def _write_templates() -> None:
    INTAKE_DIR.mkdir(parents=True, exist_ok=True)
    write_csv(MATERIALS_TEMPLATE, MATERIAL_FIELDS, _template_material_rows())
    write_csv(QUESTIONS_TEMPLATE, QUESTION_FIELDS, _template_question_rows())
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "customer_alias": "请填写客户简称或项目代号，不写真实个人姓名",
        "provided_by_role": "业务负责人/运营负责人/售后负责人",
        "provided_at": "YYYY-MM-DD",
        "desensitization_owner_role": "负责脱敏的人或角色",
        "desensitization_statement": "已移除手机号、邮箱、身份证号、订单号、平台 payload、密钥、token、密码、真实聊天原文中的可识别个人信息。",
        "customer_data_used": True,
        "files": {
            "materials_csv": "customer_materials_received.csv",
            "trial_questions_csv": "customer_trial_questions_received.csv",
        },
        "expected_question_count": "50-100",
        "real_platform_send_enabled": False,
        "formal_customer_signoff_ready": False,
    }
    write_json(MANIFEST_TEMPLATE, manifest)
    write_text(
        README_PATH,
        "\n".join(
            [
                "# H2W-DATA2 真实客户脱敏资料接收目录",
                "",
                "把客户回传文件放在本目录，文件名必须固定为：",
                "",
                "- `customer_materials_received.csv`",
                "- `customer_trial_questions_received.csv`",
                "- `customer_material_manifest_received.json`",
                "",
                "模板文件：",
                "",
                "- `customer_materials_real_template.csv`",
                "- `customer_trial_questions_real_template.csv`",
                "- `customer_material_manifest_template.json`",
                "",
                "硬边界：",
                "",
                "- 不放手机号、邮箱、身份证号、订单号、平台 payload、密钥、token、密码。",
                "- 不放客户真实聊天原文；只放脱敏后的问题和业务负责人确认的期望答案。",
                "- 题库少于 50 条时只能进入资料准备中，不能写成真实客户试跑通过。",
                "- 真实外发继续关闭，本目录只用于本地影子试跑和知识复测。",
                "",
                "三份回传文件的用途：",
                "",
                "- 知识资料：产品、服务、价格、流程政策、禁用承诺、转人工规则和可引用来源。",
                "- 试跑问题：50-100 条脱敏客户问题、期望答案和期望动作。",
                "- 资料说明：提供人角色、脱敏声明、文件说明，以及真实外发关闭确认。",
                "",
                "填写要求：",
                "",
                "- 禁用承诺要明确写出不能自动承诺的内容，例如最低价、绝对效果、无条件退款、平台规则外补偿。",
                "- 转人工规则要明确写出需要人工处理的情况，例如投诉、付款异常、售后纠纷、敏感个人信息或资料不足。",
                "- 资料到齐后仍先做本地复测和影子试跑，不代表正式客户签收。",
                "",
            ]
        ),
    )


def _missing_received_files() -> list[str]:
    missing: list[str] = []
    for path in [RECEIVED_MATERIALS, RECEIVED_QUESTIONS, RECEIVED_MANIFEST]:
        if not path.exists():
            missing.append(display_path(path))
    return missing


def _row_has_required_values(row: dict[str, str], fields: list[str]) -> bool:
    return all(str(row.get(field, "")).strip() for field in fields)


def _validate_received_materials() -> tuple[list[str], dict[str, Any]]:
    blockers: list[str] = []
    metrics: dict[str, Any] = {}
    materials = read_csv_rows(RECEIVED_MATERIALS)
    questions = read_csv_rows(RECEIVED_QUESTIONS)
    manifest = read_json(RECEIVED_MANIFEST)

    material_field_names = set(materials[0].keys()) if materials else set()
    question_field_names = set(questions[0].keys()) if questions else set()
    missing_material_fields = [field for field in MATERIAL_FIELDS if field not in material_field_names]
    missing_question_fields = [field for field in QUESTION_FIELDS if field not in question_field_names]
    if missing_material_fields:
        blockers.append(f"客户知识资料缺少字段：{', '.join(missing_material_fields)}")
    if missing_question_fields:
        blockers.append(f"客户试跑题库缺少字段：{', '.join(missing_question_fields)}")

    if len(questions) < 50:
        blockers.append(f"真实客户脱敏题库不足 50 条：当前 {len(questions)} 条")
    if not materials:
        blockers.append("客户知识资料为空")

    record_types = {row.get("record_type", "").strip() for row in materials}
    missing_record_types = sorted(REQUIRED_RECORD_TYPES - record_types)
    if missing_record_types:
        blockers.append(f"客户知识资料缺少类型：{', '.join(missing_record_types)}")

    invalid_actions = sorted({row.get("expected_action", "").strip() for row in questions} - VALID_ACTIONS - {""})
    if invalid_actions:
        blockers.append(f"客户试跑题库存在无法识别的 expected_action：{', '.join(invalid_actions)}")

    for index, row in enumerate(materials, start=2):
        if not _row_has_required_values(row, ["record_type", "item_id", "business_object", "standard_answer", "source_uri"]):
            blockers.append(f"客户知识资料第 {index} 行缺少必填字段")
            break
    for index, row in enumerate(questions, start=2):
        if not _row_has_required_values(row, ["question_id", "question", "expected_answer", "expected_action", "source_uri"]):
            blockers.append(f"客户试跑题库第 {index} 行缺少必填字段")
            break

    for path in [RECEIVED_MATERIALS, RECEIVED_QUESTIONS, RECEIVED_MANIFEST]:
        blockers.extend(scan_text_file(path, allow_internal_sample_contacts=False))

    if manifest.get("customer_data_used") is not True:
        blockers.append("manifest 未明确 customer_data_used=true")
    for field in ["customer_alias", "provided_by_role", "provided_at", "desensitization_owner_role", "desensitization_statement"]:
        if not str(manifest.get(field, "")).strip():
            blockers.append(f"manifest 缺少字段：{field}")
    if manifest.get("real_platform_send_enabled") is True:
        blockers.append("manifest 越界：real_platform_send_enabled=true")
    if manifest.get("formal_customer_signoff_ready") is True:
        blockers.append("manifest 越界：formal_customer_signoff_ready=true")

    metrics.update(
        {
            "material_rows": len(materials),
            "trial_question_count": len(questions),
            "record_types": sorted(record_types),
            "question_action_types": sorted({row.get("expected_action", "").strip() for row in questions if row.get("expected_action")}),
            "manifest_customer_alias_present": bool(str(manifest.get("customer_alias", "")).strip()),
            "internal_sample_only": manifest.get("internal_sample_only") is True,
            "real_customer_confirmation_performed": manifest.get("real_customer_confirmation_performed") is True,
        }
    )
    return blockers, metrics


def run_h2w_data2_real_customer_material_readiness(
    *,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    doc_path: Path = DOC_PATH,
) -> dict[str, Any]:
    _write_templates()
    blockers: list[str] = []
    pack8 = read_json(PACK8_SUMMARY)
    if pack8.get("status") not in {
        "co_creation_trial_package_v1_1_candidate_with_internal_data",
        "co_creation_trial_package_v1_1_candidate_with_customer_data",
    }:
        blockers.append(f"PACK8 上游状态不满足：{pack8.get('status') or 'missing'}")

    missing = _missing_received_files()
    metrics: dict[str, Any] = {}
    if missing:
        status = "waiting_for_real_customer_materials"
    else:
        validation_blockers, metrics = _validate_received_materials()
        blockers.extend(validation_blockers)
        status = INTERNAL_SAMPLE_STATUS if metrics.get("internal_sample_only") else READY_STATUS
    material_ready = not missing and not blockers
    internal_sample_ready = material_ready and status == INTERNAL_SAMPLE_STATUS
    real_customer_ready = material_ready and status == READY_STATUS

    result = base_result(SCHEMA_VERSION, PHASE, status, blockers)
    result.update(
        {
            "status": "blocked" if blockers else status,
            "missing_received_files": missing,
            "metrics": metrics,
            "customer_data_used": real_customer_ready,
            "internal_sample_used": internal_sample_ready,
            "template_paths": [
                display_path(MATERIALS_TEMPLATE),
                display_path(QUESTIONS_TEMPLATE),
                display_path(MANIFEST_TEMPLATE),
                display_path(README_PATH),
            ],
            "received_paths": [
                display_path(RECEIVED_MATERIALS),
                display_path(RECEIVED_QUESTIONS),
                display_path(RECEIVED_MANIFEST),
            ],
            "readiness": {
                "waiting_for_real_customer_materials": bool(missing) and not blockers,
                "customer_real_materials_ready": real_customer_ready,
                "internal_sample_materials_ready": internal_sample_ready,
                "minimum_question_count_required": 50,
                "real_platform_send_ready": False,
                "formal_customer_signoff_ready": False,
            },
        }
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    write_json(output_dir / "summary.json", result)
    write_markdown_report(
        doc_path,
        "H2W-DATA2 真实客户脱敏资料接入前置门禁",
        result,
        [
            ("当前状态", [f"状态：`{result['status']}`", "没有真实回传文件时，系统只能等待客户资料，不能升级为客户数据试跑。"]),
            ("模板文件", result["template_paths"]),
            ("客户回传文件", result["received_paths"]),
            ("缺失文件", missing),
            ("指标", [f"{key}: {value}" for key, value in metrics.items()]),
        ],
    )
    return result


def main() -> int:
    result = run_h2w_data2_real_customer_material_readiness()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if result["status"] == "blocked" else 0


if __name__ == "__main__":
    raise SystemExit(main())
