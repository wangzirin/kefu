#!/usr/bin/env python3
from __future__ import annotations

import importlib
import json
import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import Any

from lib.h2w_pack8_common import (
    ROOT,
    base_result,
    display_path,
    write_csv,
    write_json,
    write_markdown_report,
)


PHASE = "H2W-DATA2R3"
SCHEMA_VERSION = "p3-06u-26h2w-data2r3.material_validation_fixtures.v1"
OUTPUT_DIR = ROOT / "output/p3_06u_26h2w_data2r3_material_validation_fixtures"
DOC_PATH = ROOT / "docs/P3-06U-26H2W_DATA2R3_MATERIAL_VALIDATION_FIXTURES.md"

data2 = importlib.import_module("check_p3_06u_26h2w_data2_real_customer_material_readiness")


FixtureMutation = Callable[[list[dict[str, str]], list[dict[str, str]], dict[str, Any]], None]


def _base_material_rows() -> list[dict[str, str]]:
    records = [
        ("business_object", "OBJ-001", "标准套餐", "标准套餐说明", "客户问标准套餐包含什么？", "标准套餐包含基础接待、知识维护和月度复盘。", "customer-doc://fixture/product"),
        ("standard_qa", "QA-001", "标准套餐", "价格咨询", "标准套餐多少钱？", "以合同确认价格为准；系统只回答已发布资料中的价格口径。", "customer-doc://fixture/price"),
        ("process_policy", "POL-001", "售后流程", "售后政策", "售后怎么处理？", "先登记问题类型，再由售后负责人按政策处理。", "customer-doc://fixture/policy"),
        ("forbidden_commitment", "BAN-001", "服务边界", "禁用承诺", "能保证百分百解决吗？", "不能承诺绝对效果，遇到绝对化诉求必须转人工。", "customer-doc://fixture/forbidden"),
        ("handoff_rule", "HAND-001", "人工处理", "转人工规则", "我要投诉。", "投诉、退款争议、付款异常和资料不足时转人工。", "customer-doc://fixture/handoff"),
    ]
    rows: list[dict[str, str]] = []
    for record_type, item_id, business_object, title, question, answer, source_uri in records:
        rows.append(
            {
                "record_type": record_type,
                "item_id": item_id,
                "business_object": business_object,
                "title": title,
                "question": question,
                "standard_answer": answer,
                "source_uri": source_uri,
                "expected_behavior": "引用来源后回答；资料不足时转人工。",
                "forbidden_terms": "百分百保证；最低价；无条件补偿",
                "handoff_condition": "投诉、付款异常、退款争议、敏感信息或资料不足。",
                "desensitization_note": "测试样例已脱敏。",
            }
        )
    return rows


def _base_question_rows(count: int = 50) -> list[dict[str, str]]:
    actions = ["answer_with_reference", "handoff", "reject_forbidden_commitment", "ask_clarifying_question"]
    rows: list[dict[str, str]] = []
    for index in range(1, count + 1):
        action = actions[index % len(actions)]
        rows.append(
            {
                "question_id": f"Q-{index:03d}",
                "question": f"客户脱敏问题 {index:03d}：这个服务怎么安排？",
                "expected_answer": "按已发布知识资料回答；资料不足或触发边界时转人工。",
                "expected_action": action,
                "source_uri": "customer-doc://fixture/product",
                "business_object": "标准套餐",
                "desensitization_note": "测试样例已脱敏。",
            }
        )
    return rows


def _base_manifest() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "customer_alias": "资料校验样例客户",
        "provided_by_role": "业务负责人",
        "provided_at": "2026-07-05",
        "desensitization_owner_role": "运营负责人",
        "desensitization_statement": "已移除手机号、邮箱、订单号、平台 payload、密钥、token 和可识别个人信息。",
        "customer_data_used": True,
        "files": {
            "materials_csv": "customer_materials_received.csv",
            "trial_questions_csv": "customer_trial_questions_received.csv",
        },
        "expected_question_count": "50-100",
        "real_platform_send_enabled": False,
        "formal_customer_signoff_ready": False,
    }


def _write_fixture(
    fixture_dir: Path,
    materials: list[dict[str, str]],
    questions: list[dict[str, str]],
    manifest: dict[str, Any],
    *,
    material_fields: list[str] | None = None,
    question_fields: list[str] | None = None,
) -> None:
    write_csv(fixture_dir / "customer_materials_received.csv", material_fields or data2.MATERIAL_FIELDS, materials)
    write_csv(fixture_dir / "customer_trial_questions_received.csv", question_fields or data2.QUESTION_FIELDS, questions)
    write_json(fixture_dir / "customer_material_manifest_received.json", manifest)


def _run_existing_validator(fixture_dir: Path) -> tuple[list[str], dict[str, Any]]:
    original = (data2.RECEIVED_MATERIALS, data2.RECEIVED_QUESTIONS, data2.RECEIVED_MANIFEST)
    data2.RECEIVED_MATERIALS = fixture_dir / "customer_materials_received.csv"
    data2.RECEIVED_QUESTIONS = fixture_dir / "customer_trial_questions_received.csv"
    data2.RECEIVED_MANIFEST = fixture_dir / "customer_material_manifest_received.json"
    try:
        return data2._validate_received_materials()
    finally:
        data2.RECEIVED_MATERIALS, data2.RECEIVED_QUESTIONS, data2.RECEIVED_MANIFEST = original


def _expect_contains(blockers: list[str], expected_fragments: list[str]) -> list[str]:
    missing: list[str] = []
    joined = "\n".join(blockers)
    for fragment in expected_fragments:
        if fragment not in joined:
            missing.append(fragment)
    return missing


def _sanitize_blockers(blockers: list[str], temp_root: Path) -> list[str]:
    temp_prefix = str(temp_root)
    return [item.replace(temp_prefix, "<fixture-temp>") for item in blockers]


def _fixture_definitions() -> list[dict[str, Any]]:
    def too_few_questions(_materials: list[dict[str, str]], questions: list[dict[str, str]], _manifest: dict[str, Any]) -> None:
        del questions[10:]

    def missing_material_field(materials: list[dict[str, str]], _questions: list[dict[str, str]], _manifest: dict[str, Any]) -> None:
        for row in materials:
            row.pop("source_uri", None)

    def contains_pii(_materials: list[dict[str, str]], questions: list[dict[str, str]], _manifest: dict[str, Any]) -> None:
        questions[0]["question"] = "客户说手机号是 13812345678，能直接联系我吗？"

    def external_send_enabled(_materials: list[dict[str, str]], _questions: list[dict[str, str]], manifest: dict[str, Any]) -> None:
        manifest["real_platform_send_enabled"] = True

    def formal_signoff_enabled(_materials: list[dict[str, str]], _questions: list[dict[str, str]], manifest: dict[str, Any]) -> None:
        manifest["formal_customer_signoff_ready"] = True

    def invalid_action(_materials: list[dict[str, str]], questions: list[dict[str, str]], _manifest: dict[str, Any]) -> None:
        questions[0]["expected_action"] = "auto_send_real_platform"

    def json_secret_field(_materials: list[dict[str, str]], _questions: list[dict[str, str]], manifest: dict[str, Any]) -> None:
        manifest["api_key"] = "stripe_test_api_key_placeholder"

    def overclaim_phrase(_materials: list[dict[str, str]], _questions: list[dict[str, str]], manifest: dict[str, Any]) -> None:
        manifest["operator_note"] = "真实外发已接通"

    return [
        {
            "code": "valid_minimum_50",
            "description": "5 类知识资料 + 50 条脱敏问题 + 关闭真实外发，应通过。",
            "mutation": None,
            "expect_pass": True,
            "expected_fragments": [],
        },
        {
            "code": "too_few_questions",
            "description": "题库少于 50 条必须阻断。",
            "mutation": too_few_questions,
            "expect_pass": False,
            "expected_fragments": ["不足 50"],
        },
        {
            "code": "missing_material_field",
            "description": "知识资料缺少来源字段必须阻断。",
            "mutation": missing_material_field,
            "expect_pass": False,
            "expected_fragments": ["缺少字段：source_uri"],
            "material_fields": [field for field in data2.MATERIAL_FIELDS if field != "source_uri"],
        },
        {
            "code": "contains_pii",
            "description": "资料含手机号或邮箱必须阻断。",
            "mutation": contains_pii,
            "expect_pass": False,
            "expected_fragments": ["疑似个人联系方式"],
        },
        {
            "code": "external_send_enabled",
            "description": "manifest 写真实外发开启必须阻断。",
            "mutation": external_send_enabled,
            "expect_pass": False,
            "expected_fragments": ["real_platform_send_enabled=true"],
        },
        {
            "code": "formal_signoff_enabled",
            "description": "manifest 写客户正式签收完成必须阻断。",
            "mutation": formal_signoff_enabled,
            "expect_pass": False,
            "expected_fragments": ["formal_customer_signoff_ready=true"],
        },
        {
            "code": "invalid_action",
            "description": "题库动作写真实自动外发必须阻断。",
            "mutation": invalid_action,
            "expect_pass": False,
            "expected_fragments": ["expected_action"],
        },
        {
            "code": "json_secret_field",
            "description": "JSON manifest 里出现 api_key/token/password 形态必须阻断。",
            "mutation": json_secret_field,
            "expect_pass": False,
            "expected_fragments": ["JSON 密钥"],
        },
        {
            "code": "overclaim_phrase",
            "description": "资料包出现真实外发已接通等越界承诺必须阻断。",
            "mutation": overclaim_phrase,
            "expect_pass": False,
            "expected_fragments": ["真实外发已接通"],
        },
    ]


def run_h2w_data2r3_material_validation_fixtures() -> dict[str, Any]:
    fixture_results: list[dict[str, Any]] = []
    blockers: list[str] = []

    with tempfile.TemporaryDirectory(prefix="h2w-data2r3-") as temp_dir_name:
        temp_root = Path(temp_dir_name)
        for definition in _fixture_definitions():
            materials = _base_material_rows()
            questions = _base_question_rows()
            manifest = _base_manifest()
            mutation: FixtureMutation | None = definition.get("mutation")
            if mutation is not None:
                mutation(materials, questions, manifest)
            fixture_dir = temp_root / definition["code"]
            _write_fixture(
                fixture_dir,
                materials,
                questions,
                manifest,
                material_fields=definition.get("material_fields"),
                question_fields=definition.get("question_fields"),
            )
            fixture_blockers, metrics = _run_existing_validator(fixture_dir)
            expected_pass = bool(definition["expect_pass"])
            missing_fragments = _expect_contains(fixture_blockers, definition["expected_fragments"])
            passed_expectation = (
                (not fixture_blockers and expected_pass)
                or (bool(fixture_blockers) and not expected_pass and not missing_fragments)
            )
            if not passed_expectation:
                blockers.append(
                    f"{definition['code']} 校验结果不符合预期：blockers={len(fixture_blockers)} missing={missing_fragments}"
                )
            sanitized_blockers = _sanitize_blockers(fixture_blockers, temp_root)
            fixture_results.append(
                {
                    "code": definition["code"],
                    "description": definition["description"],
                    "expected_pass": expected_pass,
                    "actual_pass": not fixture_blockers,
                    "passed_expectation": passed_expectation,
                    "blockers": sanitized_blockers,
                    "missing_expected_fragments": missing_fragments,
                    "metrics": metrics,
                }
            )

    result = base_result(SCHEMA_VERSION, PHASE, "material_validation_fixtures_passed", blockers)
    result.update(
        {
            "status": "blocked" if blockers else "material_validation_fixtures_passed",
            "customer_data_used": False,
            "internal_sample_used": False,
            "fixture_count": len(fixture_results),
            "fixture_results": fixture_results,
            "evidence_paths": [
                display_path(OUTPUT_DIR / "summary.json"),
                display_path(DOC_PATH),
            ],
            "readiness": {
                "material_validation_fixtures_passed": not blockers,
                "real_customer_materials_ready": False,
                "real_platform_send_ready": False,
                "formal_customer_signoff_ready": False,
                "minimum_question_count_required": 50,
            },
        }
    )
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    write_json(OUTPUT_DIR / "summary.json", result)
    write_markdown_report(
        DOC_PATH,
        "H2W-DATA2R3 真实资料门禁反例校验",
        result,
        [
            ("校验目标", ["证明真实资料门禁能拦截少量题库、缺字段、敏感信息、密钥形态、真实外发和正式签收越界。"]),
            (
                "样例结果",
                [
                    f"{item['code']}：{'通过预期' if item['passed_expectation'] else '未达预期'}；实际 {'通过' if item['actual_pass'] else '阻断'}；阻断 {len(item['blockers'])} 项"
                    for item in fixture_results
                ],
            ),
            ("证据文件", result["evidence_paths"]),
        ],
    )
    return result


def main() -> int:
    result = run_h2w_data2r3_material_validation_fixtures()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if result["status"] == "blocked" else 0


if __name__ == "__main__":
    raise SystemExit(main())
