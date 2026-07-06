#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib.h2w_pack8_common import (
    ROOT,
    base_result,
    build_zip,
    boundary_blockers,
    display_path,
    load_expected_summary,
    scan_archive_candidates,
    write_json,
    write_markdown_report,
    write_text,
)


PHASE = "H2W-COMM1"
SCHEMA_VERSION = "p3-06u-26h2w-comm1.commercial-trial-launch-package.v1"
DEFAULT_OUTPUT_DIR = ROOT / "output/p3_06u_26h2w_comm1_commercial_trial_launch_package"
DOC_PATH = ROOT / "docs/P3-06U-26H2W_COMM1_COMMERCIAL_TRIAL_LAUNCH_PACKAGE.md"

UPSTREAMS = {
    "data2": (
        ROOT / "output/p3_06u_26h2w_data2_real_customer_material_readiness/summary.json",
        {"customer_real_materials_ready", "internal_sample_materials_ready_for_rehearsal"},
    ),
    "data2r7": (
        ROOT / "output/p3_06u_26h2w_data2r7_received_file_drop_gate/summary.json",
        {"received_customer_files_validated_ready_for_pack12_rerun", "received_internal_sample_files_validated_ready_for_pack12_rerun"},
    ),
    "pack12": (
        ROOT / "output/p3_06u_26h2w_pack12_customer_data_rerun_orchestrator/summary.json",
        {"customer_data_rerun_orchestration_ready", "internal_sample_data_rerun_orchestration_ready"},
    ),
    "kb3": (
        ROOT / "output/p3_06u_26h2w_kb3_customer_knowledge_center/summary.json",
        {"customer_knowledge_center_productized"},
    ),
    "kb6": (
        ROOT / "output/p3_06u_26h2w_kb6_real_customer_knowledge_retest/summary.json",
        {"customer_knowledge_retest_ready_with_customer_data", "customer_knowledge_retest_ready_with_internal_sample"},
    ),
    "fe10": (
        ROOT / "output/p3_06u_26h2w_fe10_final_product_polish_gate/summary.json",
        {"frontend_final_product_polish_ready"},
    ),
    "fe12": (
        ROOT / "output/p3_06u_26h2w_fe12_customer_perspective_browser_qa/summary.json",
        {"passed_customer_perspective_browser_qa"},
    ),
    "install6": (
        ROOT / "output/p3_06u_26h2w_install6_trial_installer_experience/summary.json",
        {"trial_installer_experience_candidate_ready"},
    ),
    "install7": (
        ROOT / "output/p3_06u_26h2w_install7_customer_mode_prepack_gate/summary.json",
        {"customer_mode_prepack_gate_ready"},
    ),
    "ops2": (
        ROOT / "output/p3_06u_26h2w_ops2_customer_monthly_ops_report/summary.json",
        {"ready_for_customer_monthly_ops_report_rehearsal"},
    ),
    "ops3": (
        ROOT / "output/p3_06u_26h2w_ops3_customer_trial_ops_loop/summary.json",
        {"customer_trial_ops_loop_ready"},
    ),
    "nc19": (
        ROOT / "output/p3_06u_26h2w_nc19_customer_redteam_report/summary.json",
        {"customer_redteam_report_flow_ready_waiting_customer_data", "customer_redteam_report_flow_ready_with_customer_data"},
    ),
    "pack11": (
        ROOT / "output/p3_06u_26h2w_pack11_local_trial_v3_candidate/summary.json",
        {"customer_data_local_trial_package_v3_candidate", "internal_sample_local_trial_package_v3_candidate", "blocked_waiting_real_customer_materials"},
    ),
    "nc9": (
        ROOT / "output/p3_06u_26h2w_nc9_local_trial_package_v4/summary.json",
        {"local_trial_package_v4_candidate_with_customer_data", "local_trial_package_v4_candidate_with_internal_sample"},
    ),
}


def _load_upstreams() -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]], list[str]]:
    payloads: dict[str, dict[str, Any]] = {}
    statuses: dict[str, dict[str, Any]] = {}
    blockers: list[str] = []
    for name, (path, expected_statuses) in UPSTREAMS.items():
        payload, status, stage_blockers = load_expected_summary(name, path, expected_statuses)
        payloads[name] = payload
        statuses[name] = status
        blockers.extend(stage_blockers)
        if payload:
            blockers.extend(boundary_blockers(name, payload))
    return payloads, statuses, blockers


def _upstream_status(statuses: dict[str, dict[str, Any]], key: str) -> str:
    return str(statuses.get(key, {}).get("status") or "missing")


def _is_customer_data_status(status: str) -> bool:
    return "customer" in status and "internal_sample" not in status and "waiting" not in status


def _docs(output_dir: Path) -> dict[str, str]:
    return {
        "COMMERCIAL_TRIAL_PACKAGE_README.md": f"""# 共创客户本地试跑包 v1 候选

这是一套面向第一批共创客户的本地受控试跑资料包。它适合用于售前演示、内部试跑、客户资料准备、知识中心演练、本地部署说明和试跑边界确认。

## 当前可对外表达

- 可以表达为：本地私有化智能客服试跑包、共创客户试跑版、知识库型客服中台候选。
- 可以承诺：本地启动、首任负责人创建、知识资料导入流程、质量复盘/月报、诊断包、备份恢复、更新预检、试跑交付档案。
- 必须说明：当前真实外发关闭，真实平台渠道未接通，正式签名安装包未完成，客户正式准确率签收需要真实资料和真实确认文件。

## 本包的五个核心产物

1. 真实客户样板资料包。
2. 客户知识中心最终流程。
3. 前端最终成品级 QA 证据。
4. 本地部署交付包 v1。
5. 对外试跑商业资料包。

## 使用顺序

先用样板资料演示完整流程，再接收真实客户资料，随后导入知识中心复测，最后输出试跑报告和交付档案。
""",
        "CUSTOMER_SAMPLE_MATERIALS_PACK.md": """# 真实客户样板资料包

## 用途

用于模拟第一家客户的资料接收、知识入库、问题复测和质量报告流程。当前样板是内部准真实资料，不代表真实客户签收结果。

## 资料清单

- 知识资料：产品、服务、价格、流程、政策、禁用承诺。
- 问题题库：50-100 条脱敏客户问题。
- 标准答案：每条问题对应可核验答案。
- 转人工规则：退款、投诉、法律、价格争议、身份信息等场景。
- 脱敏声明：不包含密钥、账号、平台原始载荷和未授权个人信息。

## 真实客户上线前必须补齐

客户需要回传真实脱敏资料、确认人、角色、确认时间和修订意见。没有真实回传文件时，只能作为内部演练。
""",
        "CUSTOMER_KNOWLEDGE_CENTER_FINAL_FLOW.md": """# 客户知识中心最终流程

## 六步流程

1. 导入资料：优先 CSV/XLSX，PDF/DOCX 作为来源资料。
2. 预检：检查字段、重复项、脱敏风险、禁用承诺和转人工规则。
3. 发布：生成可回滚的知识更新包。
4. 复测：对最终客服答案做质量候选评测。
5. 确认：等待客户回填确认文件，不由系统代签。
6. 质量报告：输出知识覆盖、引用覆盖、缺口和下一轮补充建议。

## 四层知识结构

- 业务对象：产品、服务、门店、课程、套餐。
- 标准问答：高频问题、标准答法、引用来源。
- 流程政策：售后、退款、发货、预约、开票。
- 禁用承诺与转人工规则：不能承诺什么，什么必须交给人工。
""",
        "FRONTEND_FINAL_QA_AND_PRODUCT_POLISH.md": """# 前端最终成品级 QA 与视觉收口

## 已纳入的验收口径

- 客户视角浏览器逐页点击。
- 总览、接待工作台、知识中心、质量复盘、渠道接入、账号与本地维护、试点准备、交付档案。
- 客户可见按钮必须是真实动作、明确禁用说明或隐藏。
- 多渠道对话台保持客服 IM 形态：左侧紧凑会话列表，右侧大面积消息流，转人工只作为会话状态。

## 仍保留的边界

前端可以用于本地试跑和客户演示，但真实渠道外发、正式平台回执和真实客户签收仍需要后续专项。
""",
        "LOCAL_DEPLOYMENT_HANDOFF_V1.md": """# 本地部署交付包 v1

## 客户本地启动流程

1. 检查 Docker Desktop。
2. 检查端口占用和客户环境文件。
3. 确认真实外发关闭。
4. 创建首任负责人账号。
5. 登录工作台。
6. 导入知识资料并运行复测。
7. 生成诊断包、备份和月度运维报告。

## 维护方式

- 客户本地生成诊断包。
- 售后接收诊断包后给出修复建议或更新包。
- 更新前必须备份。
- 更新后必须保留审计和回滚记录。

## 当前安装器状态

当前是启动候选和包装候选，不是已签名 dmg/exe。
""",
        "PRODUCT_INTRO_TRIAL_CUSTOMER.md": """# 产品介绍：万法常世智能客服中台

万法常世智能客服中台面向中小企业的私有化客服试跑场景，帮助企业把产品资料、服务流程、售后政策和高频问题整理为可复测、可追踪、可持续优化的知识库，并在本地环境中验证客服自动回复策略。

## 核心能力

- 知识资料导入与复测。
- 多渠道会话工作台原型。
- 自动回复策略与转人工边界。
- 质量复盘和月度运维报告。
- 诊断包、备份、恢复和更新预检。

## 适合场景

- 小微企业先用本地试跑验证知识库和客服流程。
- 客服资料还不标准，需要先梳理问答和流程。
- 希望先控制成本，不直接进入全渠道复杂接入。
""",
        "CUSTOMER_USER_MANUAL_TRIAL.md": """# 客户试跑使用手册

## 第一次使用

1. 启动本地工作台。
2. 创建首任负责人账号。
3. 登录后进入试点准备。
4. 按提示准备知识资料和问题题库。
5. 导入资料并查看预检结果。
6. 发布知识更新包并运行复测。
7. 查看质量报告和知识缺口。

## 日常维护

- 新产品、新价格、新政策先进入知识中心。
- 出现回答不准时，在质量复盘中查看原因。
- 补充资料后重新复测。
- 每月生成运维报告，检查质量、成本、知识缺口和维护建议。
""",
        "SERVICE_BOUNDARY_AND_TRIAL_AGREEMENT.md": """# 试跑服务边界说明

## 本轮包含

- 本地试跑部署指导。
- 样板资料演示。
- 客户资料导入模板。
- 知识复测和质量报告。
- 诊断包、备份、恢复、更新预检说明。

## 本轮不包含

- 真实平台自动外发。
- 企业微信、公众号、抖音、淘宝、京东、拼多多等真实渠道接通。
- 正式生产 SLA。
- 已签名 dmg/exe 安装包。
- RPA、个人号外挂或模拟点击作为正式交付能力。

## 客户确认

客户确认必须来自客户回填文件，包含确认人、角色、确认时间和修订意见。系统不会替客户预填确认结果。
""",
        "QUOTE_AND_SERVICE_SCOPE_TRIAL.md": """# 试跑报价与服务范围模板

## 建议报价结构

- 本地试跑部署服务费：覆盖启动、首任负责人、基础配置和试跑培训。
- 知识资料整理服务费：按资料复杂度、题库数量、业务对象数量和流程政策数量报价。
- 月度运维服务费：覆盖质量复盘、诊断包分析、知识缺口建议、更新预检和备份恢复指导。
- 正式渠道接入服务费：企业微信、公众号、电商平台等官方授权接入另行评估。

## 报价边界

本模板用于商务测算，不自动构成最终报价。正式报价需要根据客户资料量、坐席数量、渠道数量、模型调用成本和维护频次确认。
""",
        "SEVEN_CORE_BLOCKS_READINESS_MATRIX.md": """# 七大核心板块成熟度矩阵

| 核心板块 | 当前状态 | 可用于本地试跑 | 可用于正式生产 |
| --- | --- | --- | --- |
| 真实客户资料闭环 | 内部样板已跑通，等待真实客户资料 | 是 | 否 |
| 客户知识中心最终产品化 | 六步流程已形成 | 是 | 需真实客户确认 |
| 前端最终成品感 | 已完成客户视角 QA 与视觉收口证据 | 是 | 需真实客户试用反馈 |
| 真实渠道闭环 | 只保留官方授权路线，未接通真实外发 | 否 | 否 |
| 安装和交付体验 | 本地启动与安装候选体验已形成 | 是 | 需签名安装器专项 |
| 真实安全与红队报告 | 报告流程已准备，等待真实客户数据 | 部分 | 否 |
| 商用包装 | 试跑资料包已形成 | 是 | 需合同、报价和客户验收 |
""",
    }


def _write_docs(output_dir: Path) -> list[Path]:
    generated: list[Path] = []
    for filename, body in _docs(output_dir).items():
        path = output_dir / filename
        write_text(path, body)
        generated.append(path)
    return generated


def _build_five_items(statuses: dict[str, dict[str, Any]], generated_docs: list[Path]) -> dict[str, dict[str, Any]]:
    doc_names = {path.name: display_path(path) for path in generated_docs}
    return {
        "真实客户样板资料包": {
            "ready": True,
            "status": "ready_with_internal_sample_waiting_customer_materials",
            "evidence": [
                _upstream_status(statuses, "data2"),
                _upstream_status(statuses, "data2r7"),
                doc_names["CUSTOMER_SAMPLE_MATERIALS_PACK.md"],
            ],
        },
        "客户知识中心最终流程": {
            "ready": True,
            "status": "knowledge_center_flow_ready",
            "evidence": [
                _upstream_status(statuses, "kb3"),
                _upstream_status(statuses, "kb6"),
                doc_names["CUSTOMER_KNOWLEDGE_CENTER_FINAL_FLOW.md"],
            ],
        },
        "前端最终成品级 QA": {
            "ready": True,
            "status": "frontend_customer_qa_and_polish_ready",
            "evidence": [
                _upstream_status(statuses, "fe10"),
                _upstream_status(statuses, "fe12"),
                doc_names["FRONTEND_FINAL_QA_AND_PRODUCT_POLISH.md"],
            ],
        },
        "本地部署交付包 v1": {
            "ready": True,
            "status": "local_deployment_handoff_v1_ready_as_candidate",
            "evidence": [
                _upstream_status(statuses, "install6"),
                _upstream_status(statuses, "install7"),
                _upstream_status(statuses, "ops2"),
                _upstream_status(statuses, "ops3"),
                doc_names["LOCAL_DEPLOYMENT_HANDOFF_V1.md"],
            ],
        },
        "对外试跑商业资料包": {
            "ready": True,
            "status": "commercial_trial_documents_ready",
            "evidence": [
                doc_names["PRODUCT_INTRO_TRIAL_CUSTOMER.md"],
                doc_names["CUSTOMER_USER_MANUAL_TRIAL.md"],
                doc_names["SERVICE_BOUNDARY_AND_TRIAL_AGREEMENT.md"],
                doc_names["QUOTE_AND_SERVICE_SCOPE_TRIAL.md"],
            ],
        },
    }


def _build_seven_blocks(statuses: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {
        "真实客户资料闭环": {
            "status": "internal_sample_ready_waiting_real_customer_materials",
            "ready_for_controlled_trial": True,
            "ready_for_production": False,
            "evidence_status": [_upstream_status(statuses, "data2"), _upstream_status(statuses, "pack12")],
        },
        "客户知识中心最终产品化": {
            "status": "knowledge_center_productized_for_trial",
            "ready_for_controlled_trial": True,
            "ready_for_production": False,
            "evidence_status": [_upstream_status(statuses, "kb3"), _upstream_status(statuses, "kb6")],
        },
        "前端最终成品感": {
            "status": "frontend_polish_and_browser_qa_ready",
            "ready_for_controlled_trial": True,
            "ready_for_production": False,
            "evidence_status": [_upstream_status(statuses, "fe10"), _upstream_status(statuses, "fe12")],
        },
        "真实渠道闭环": {
            "status": "planned_official_authorization_required",
            "ready_for_controlled_trial": False,
            "ready_for_production": False,
            "evidence_status": ["real_platform_send_ready=false"],
        },
        "安装和交付体验": {
            "status": "local_start_and_installer_candidate_ready",
            "ready_for_controlled_trial": True,
            "ready_for_production": False,
            "evidence_status": [_upstream_status(statuses, "install6"), _upstream_status(statuses, "install7")],
        },
        "真实安全与红队报告": {
            "status": "redteam_report_flow_ready_waiting_customer_data",
            "ready_for_controlled_trial": True,
            "ready_for_production": False,
            "evidence_status": [_upstream_status(statuses, "nc19")],
        },
        "商用包装": {
            "status": "trial_commercial_pack_ready",
            "ready_for_controlled_trial": True,
            "ready_for_production": False,
            "evidence_status": ["COMM1 generated"],
        },
    }


def _business_score(seven_blocks: dict[str, dict[str, Any]]) -> dict[str, Any]:
    trial_ready = sum(1 for item in seven_blocks.values() if item["ready_for_controlled_trial"])
    production_ready = sum(1 for item in seven_blocks.values() if item["ready_for_production"])
    return {
        "controlled_local_trial_score": round(trial_ready / len(seven_blocks) * 100),
        "direct_production_commercial_score": round(production_ready / len(seven_blocks) * 100),
        "interpretation": "可作为共创客户本地受控试跑包推进；不能写成成熟全渠道正式商用系统。",
    }


def run_comm1_commercial_trial_launch_package(
    *,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    doc_path: Path = DOC_PATH,
) -> dict[str, Any]:
    payloads, statuses, blockers = _load_upstreams()
    customer_data_used = any(_is_customer_data_status(status["status"]) for name, status in statuses.items() if name in {"data2", "data2r7", "pack12", "kb6"})
    generated_docs = _write_docs(output_dir)
    five_items = _build_five_items(statuses, generated_docs)
    seven_blocks = _build_seven_blocks(statuses)

    evidence_files = [
        *generated_docs,
        ROOT / "docs/P3-06U-26H2W_PACK10_CUSTOMER_DATA_TRIAL_PACKAGE.md",
        ROOT / "docs/P3-06U-26H2W_PACK11_LOCAL_TRIAL_V3_CANDIDATE.md",
        ROOT / "docs/P3-06U-26H2W_NC19_CUSTOMER_REDTEAM_REPORT.md",
        ROOT / "installers/INSTALL6_SIGNING_READINESS_CHECKLIST.md",
        ROOT / "installers/macos/README.md",
        ROOT / "installers/windows/README.md",
        *(path for path, _ in UPSTREAMS.values()),
    ]
    evidence_files = [path for path in evidence_files if path.exists()]
    blockers.extend(scan_archive_candidates(evidence_files))

    status = (
        "blocked"
        if blockers
        else "commercial_trial_launch_package_v1_candidate_with_customer_data"
        if customer_data_used
        else "commercial_trial_launch_package_v1_candidate_with_internal_sample"
    )
    archive_path = output_dir / "commercial_trial_launch_package_v1_candidate.zip"
    if customer_data_used:
        archive_path = output_dir / "commercial_trial_launch_package_v1_candidate_with_customer_data.zip"

    result = base_result(SCHEMA_VERSION, PHASE, status, blockers)
    result.update(
        {
            "status": status,
            "customer_data_used": customer_data_used,
            "internal_sample_used": not customer_data_used,
            "upstream_statuses": {name: status_item for name, status_item in statuses.items()},
            "five_fast_items": five_items,
            "seven_core_blocks": seven_blocks,
            "business_score": _business_score(seven_blocks),
            "readiness": {
                "ready_for_external_pitch_as_controlled_trial": not blockers,
                "ready_for_paid_co_creation_local_trial": not blockers,
                "ready_for_direct_customer_production": False,
                "ready_for_mature_all_channel_commercial": False,
                "real_customer_data_ready": customer_data_used,
                "real_channel_closed_loop_ready": False,
                "signed_installer_ready": False,
                "formal_customer_signoff_ready": False,
                "production_sla_ready": False,
            },
            "boundaries": {
                **result["boundaries"],
                "customer_data_used": customer_data_used,
                "internal_sample_used": not customer_data_used,
                "real_channel_closed_loop_ready": False,
                "mature_all_channel_commercial_ready": False,
                "direct_customer_production_ready": False,
            },
            "generated_documents": [display_path(path) for path in generated_docs],
            "archive": {
                "path": display_path(archive_path),
                "created": status != "blocked",
                "secret_scan_findings": [],
            },
            "evidence_paths": [display_path(path) for path in evidence_files] + [display_path(output_dir / "summary.json"), display_path(doc_path)],
        }
    )

    if blockers:
        result["archive"]["created"] = False
        result["archive"]["secret_scan_findings"] = sorted(set(blockers))

    output_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "phase": PHASE,
        "status": result["status"],
        "five_fast_items": result["five_fast_items"],
        "seven_core_blocks": result["seven_core_blocks"],
        "business_score": result["business_score"],
        "boundaries": result["boundaries"],
        "not_ready_for": result["not_ready_for"],
        "generated_documents": result["generated_documents"],
    }
    write_json(output_dir / "manifest.json", manifest)
    write_json(output_dir / "summary.json", result)
    write_markdown_report(
        doc_path,
        "H2W-COMM1 对外本地试跑商用包 v1 候选",
        result,
        [
            ("五件事完成状态", [f"{name}: `{item['status']}`" for name, item in five_items.items()]),
            ("七大核心板块", [f"{name}: `{item['status']}`" for name, item in seven_blocks.items()]),
            ("可对外口径", ["可作为共创客户本地受控试跑包沟通", "不能作为成熟全渠道正式商用系统发布"]),
            ("档案", [f"路径：`{display_path(archive_path)}`", f"是否生成：`{result['archive']['created']}`"]),
        ],
    )
    if status != "blocked":
        build_zip(archive_path, evidence_files + [doc_path, output_dir / "manifest.json"], manifest)
    return result


def main() -> int:
    result = run_comm1_commercial_trial_launch_package()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if result["status"] == "blocked" else 0


if __name__ == "__main__":
    raise SystemExit(main())
