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
    write_json,
    write_markdown_report,
    write_text,
)


PHASE = "H2W-DATA2R2"
SCHEMA_VERSION = "p3-06u-26h2w-data2r2.material_intake_package.v1"
DEFAULT_OUTPUT_DIR = ROOT / "output/p3_06u_26h2w_data2r2_material_intake_package"
DOC_PATH = ROOT / "docs/P3-06U-26H2W_DATA2R2_MATERIAL_INTAKE_PACKAGE.md"
CUSTOMER_GUIDE_PATH = ROOT / "docs/customer/万法常世AI客服真实资料接收与脱敏手册.md"
INTAKE_DIR = ROOT / "evals/p3_06u_26h2w_data2_real_customer_material_readiness"
MATERIALS_TEMPLATE = INTAKE_DIR / "customer_materials_real_template.csv"
QUESTIONS_TEMPLATE = INTAKE_DIR / "customer_trial_questions_real_template.csv"
MANIFEST_TEMPLATE = INTAKE_DIR / "customer_material_manifest_template.json"
INTAKE_README = INTAKE_DIR / "README.md"
DATA2R_SUMMARY = ROOT / "output/p3_06u_26h2w_data2r_real_customer_materials/summary.json"
PACK10_SUMMARY = ROOT / "output/p3_06u_26h2w_pack10_customer_data_trial_package/summary.json"
FRONTEND_APP = ROOT / "frontend/src/App.tsx"

MATERIAL_FIELDS = {
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
}
QUESTION_FIELDS = {
    "question_id",
    "question",
    "expected_answer",
    "expected_action",
    "source_uri",
    "business_object",
    "desensitization_note",
}
REQUIRED_GUIDE_PHRASES = [
    "知识资料",
    "试跑问题",
    "资料说明",
    "50 条",
    "脱敏",
    "禁用承诺",
    "转人工",
    "真实外发关闭",
]


def _ensure_customer_guide() -> None:
    lines = [
        "# 万法常世 AI 客服真实资料接收与脱敏手册",
        "",
        "## 这份资料包用来做什么",
        "",
        "这份资料包用于共创客户本地试跑前的知识库整理、客服答案复测和影子试跑。资料到齐后，系统会先做本地复测和质量报告，不会直接向微信、抖音、淘宝、京东、拼多多、小红书等平台发送消息。",
        "",
        "## 需要回传的三份文件",
        "",
        "| 文件 | 用途 | 固定文件名 |",
        "|---|---|---|",
        "| 知识资料 | 产品、服务、价格、流程政策、禁用承诺、转人工规则 | `customer_materials_received.csv` |",
        "| 试跑问题 | 50-100 条脱敏客户问题和期望答案 | `customer_trial_questions_received.csv` |",
        "| 资料说明 | 提供人角色、脱敏声明、文件说明 | `customer_material_manifest_received.json` |",
        "",
        "## 知识资料怎么填",
        "",
        "- 业务对象：产品、服务、套餐、门店、课程、项目等。",
        "- 标准问答：客户常问的问题、标准答法和可引用来源。",
        "- 流程政策：退款、售后、预约、发货、开票、服务边界。",
        "- 禁用承诺：不能承诺最低价、绝对效果、无条件退款、平台规则外补偿等。",
        "- 转人工规则：投诉、纠纷、敏感个人信息、付款异常、超出资料范围的问题。",
        "",
        "## 试跑问题怎么填",
        "",
        "- 至少 50 条，建议 50-100 条。",
        "- 每条问题必须有期望答案或期望动作。",
        "- 可以标注 `answer_with_reference`、`handoff`、`reject_forbidden_commitment`、`ask_clarifying_question`。",
        "- 正确转人工属于安全处理，不会被当作事实性失败。",
        "",
        "## 脱敏要求",
        "",
        "- 不放手机号、邮箱、身份证号、订单号、真实地址、付款信息、平台 payload、密钥、token、密码。",
        "- 不直接复制客户真实聊天原文；要改写成脱敏后的业务问题。",
        "- 资料来源可以写成 `customer-doc://售后政策` 这类内部来源，不写私密链接。",
        "",
        "## 试跑边界",
        "",
        "- 真实外发关闭。",
        "- 真实平台接入未开启。",
        "- 这不是正式客户验收签收。",
        "- 这不是生产 SLA。",
        "- 这不是签名安装包完成证明。",
        "",
        "## 资料到齐后的处理顺序",
        "",
        "1. 校验三份文件是否齐全。",
        "2. 扫描敏感信息和越界承诺。",
        "3. 导入知识资料并生成复测报告。",
        "4. 运行影子试跑，只生成草稿、建议和质量报告。",
        "5. 客户或业务负责人复核报告后，再决定下一轮修订。",
        "",
    ]
    write_text(CUSTOMER_GUIDE_PATH, "\n".join(lines))


def _csv_fields(path: Path) -> set[str]:
    rows = read_csv_rows(path)
    if not rows:
        return set()
    return set(rows[0].keys())


def _check_required_phrases(path: Path, phrases: list[str]) -> list[str]:
    text = path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""
    return [phrase for phrase in phrases if phrase not in text]


def run_h2w_data2r2_material_intake_package(
    *,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    doc_path: Path = DOC_PATH,
) -> dict[str, Any]:
    _ensure_customer_guide()
    blockers: list[str] = []

    required_files = [
        MATERIALS_TEMPLATE,
        QUESTIONS_TEMPLATE,
        MANIFEST_TEMPLATE,
        INTAKE_README,
        CUSTOMER_GUIDE_PATH,
        DATA2R_SUMMARY,
        PACK10_SUMMARY,
        FRONTEND_APP,
    ]
    for file_path in required_files:
        if not file_path.exists():
            blockers.append(f"缺少资料接收包文件：{display_path(file_path)}")

    material_fields = _csv_fields(MATERIALS_TEMPLATE)
    question_fields = _csv_fields(QUESTIONS_TEMPLATE)
    missing_material_fields = sorted(MATERIAL_FIELDS - material_fields)
    missing_question_fields = sorted(QUESTION_FIELDS - question_fields)
    if missing_material_fields:
        blockers.append(f"知识资料模板缺少字段：{', '.join(missing_material_fields)}")
    if missing_question_fields:
        blockers.append(f"试跑问题模板缺少字段：{', '.join(missing_question_fields)}")

    manifest = read_json(MANIFEST_TEMPLATE)
    if manifest.get("customer_data_used") is not True:
        blockers.append("资料说明模板未明确 customer_data_used=true")
    if manifest.get("real_platform_send_enabled") is not False:
        blockers.append("资料说明模板未保持 real_platform_send_enabled=false")
    if manifest.get("formal_customer_signoff_ready") is not False:
        blockers.append("资料说明模板未保持 formal_customer_signoff_ready=false")

    for name, path in {
        "接收目录说明": INTAKE_README,
        "客户资料接收手册": CUSTOMER_GUIDE_PATH,
    }.items():
        missing_phrases = _check_required_phrases(path, REQUIRED_GUIDE_PHRASES)
        if missing_phrases:
            blockers.append(f"{name} 缺少关键说明：{', '.join(missing_phrases)}")

    frontend_text = FRONTEND_APP.read_text(encoding="utf-8", errors="ignore") if FRONTEND_APP.exists() else ""
    for phrase in ["资料接收包", "知识资料 CSV", "试跑问题 CSV", "资料说明 JSON", "客户资料未回传前"]:
        if phrase not in frontend_text:
            blockers.append(f"试点准备页缺少资料接收提示：{phrase}")

    data2r = read_json(DATA2R_SUMMARY)
    pack10 = read_json(PACK10_SUMMARY)
    if data2r.get("status") not in {"waiting_for_real_customer_materials", "customer_real_materials_ready"}:
        blockers.append(f"DATA2R 状态不可用于资料接收包：{data2r.get('status') or 'missing'}")
    if pack10.get("status") not in {
        "blocked_waiting_real_customer_materials",
        "customer_data_local_trial_package_v2_candidate",
    }:
        blockers.append(f"PACK10 状态不可用于资料接收包：{pack10.get('status') or 'missing'}")

    scan_targets = [
        MATERIALS_TEMPLATE,
        QUESTIONS_TEMPLATE,
        MANIFEST_TEMPLATE,
        INTAKE_README,
        CUSTOMER_GUIDE_PATH,
    ]
    for path in scan_targets:
        if path.exists():
            blockers.extend(scan_text_file(path, allow_internal_sample_contacts=False))

    status = "material_intake_package_ready"
    result = base_result(SCHEMA_VERSION, PHASE, status, blockers)
    result.update(
        {
            "status": "blocked" if blockers else status,
            "customer_data_used": False,
            "internal_sample_used": False,
            "data2r_status": data2r.get("status") or "missing",
            "pack10_status": pack10.get("status") or "missing",
            "template_paths": [display_path(path) for path in [MATERIALS_TEMPLATE, QUESTIONS_TEMPLATE, MANIFEST_TEMPLATE]],
            "customer_guide_path": display_path(CUSTOMER_GUIDE_PATH),
            "intake_directory": display_path(INTAKE_DIR),
            "received_file_names": [
                "customer_materials_received.csv",
                "customer_trial_questions_received.csv",
                "customer_material_manifest_received.json",
            ],
            "readiness": {
                "material_intake_package_ready": not blockers,
                "customer_real_materials_ready": data2r.get("status") == "customer_real_materials_ready",
                "waiting_for_real_customer_materials": data2r.get("status") == "waiting_for_real_customer_materials",
                "minimum_question_count_required": 50,
                "real_platform_send_ready": False,
                "formal_customer_signoff_ready": False,
            },
            "evidence_paths": [
                display_path(output_dir / "summary.json"),
                display_path(doc_path),
                display_path(CUSTOMER_GUIDE_PATH),
                display_path(INTAKE_README),
            ],
        }
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    write_json(output_dir / "summary.json", result)
    write_markdown_report(
        doc_path,
        "H2W-DATA2R2 真实资料接收包门禁",
        result,
        [
            (
                "资料接收包",
                [
                    f"接收目录：`{display_path(INTAKE_DIR)}`",
                    f"客户手册：`{display_path(CUSTOMER_GUIDE_PATH)}`",
                    "三份固定回传文件：`customer_materials_received.csv`、`customer_trial_questions_received.csv`、`customer_material_manifest_received.json`。",
                ],
            ),
            (
                "当前状态",
                [
                    f"DATA2R：`{result['data2r_status']}`",
                    f"PACK10：`{result['pack10_status']}`",
                    "真实客户资料未回传前，资料包只能处于准备就绪，不能生成客户数据版试跑包。",
                ],
            ),
            (
                "模板文件",
                [display_path(path) for path in [MATERIALS_TEMPLATE, QUESTIONS_TEMPLATE, MANIFEST_TEMPLATE, INTAKE_README]],
            ),
        ],
    )
    return result


def main() -> int:
    result = run_h2w_data2r2_material_intake_package()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if result["status"] == "blocked" else 0


if __name__ == "__main__":
    raise SystemExit(main())
