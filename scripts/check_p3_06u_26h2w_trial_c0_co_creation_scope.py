#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

from lib.h2w_pack8_common import ROOT, base_result, display_path, write_json, write_markdown_report, write_text


PHASE = "H2W-TRIAL-C0"
SCHEMA_VERSION = "p3-06u-26h2w-trial-c0.co_creation_scope.v1"
DEFAULT_OUTPUT_DIR = ROOT / "output/p3_06u_26h2w_trial_c0_co_creation_scope"
DOC_PATH = ROOT / "docs/P3-06U-26H2W_TRIAL_C0_CO_CREATION_SCOPE.md"


SCOPE = {
    "customer_type": "小微企业或中小型企业的首批共创试跑客户",
    "business_scenarios": ["售前咨询", "基础售后", "套餐/课程/服务说明", "预约/发货/开票流程", "高风险问题转人工"],
    "knowledge_material_types": ["业务对象", "标准问答", "流程政策", "禁用承诺", "转人工规则", "回归题库"],
    "trial_duration": "3-7 个工作日的本地受控试跑",
    "acceptance_roles": ["业务负责人", "客服负责人", "我方实施/售后负责人"],
    "deliverables": ["本地启动说明", "知识资料模板", "影子试跑质量报告", "月度运维报告", "诊断/备份/恢复说明", "交付档案 v1.1"],
    "out_of_scope": ["真实平台自动外发", "企业微信/抖音/淘宝等真实渠道接通", "生产 SLA", "签名 dmg/exe", "移动端", "RPA 正式交付"],
}


def run_h2w_trial_c0_co_creation_scope(
    *,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    doc_path: Path = DOC_PATH,
) -> dict:
    blockers: list[str] = []
    if not SCOPE["out_of_scope"]:
        blockers.append("缺少不可承诺边界")
    forbidden_goal_terms = {"真实平台自动外发", "生产 SLA", "签名 dmg/exe"}
    deliverable_text = " ".join(SCOPE["deliverables"])
    for term in forbidden_goal_terms:
        if term in deliverable_text:
            blockers.append(f"试跑交付物越界包含：{term}")

    result = base_result(SCHEMA_VERSION, PHASE, "trial_scope_ready", blockers)
    result.update(
        {
            "trial_scope": SCOPE,
            "evidence_paths": [display_path(output_dir / "scope.json"), display_path(doc_path)],
            "readiness": {
                "trial_scope_ready": not blockers,
                "real_platform_send_ready": False,
                "production_sla_ready": False,
                "signed_dmg_exe_ready": False,
            },
        }
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    write_json(output_dir / "scope.json", SCOPE)
    write_json(output_dir / "summary.json", result)
    write_markdown_report(
        doc_path,
        "H2W-TRIAL-C0 共创试跑范围冻结",
        result,
        [
            ("试跑对象", [SCOPE["customer_type"], f"试跑周期：{SCOPE['trial_duration']}"]),
            ("覆盖场景", SCOPE["business_scenarios"]),
            ("资料类型", SCOPE["knowledge_material_types"]),
            ("交付物", SCOPE["deliverables"]),
            ("本轮不做", SCOPE["out_of_scope"]),
        ],
    )
    write_text(
        output_dir / "scope_readme.md",
        "# 共创试跑范围\n\n本目录只保存 PACK8 试跑范围证据，不代表正式客户验收。\n",
    )
    return result


def main() -> int:
    result = run_h2w_trial_c0_co_creation_scope()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] != "blocked" else 1


if __name__ == "__main__":
    raise SystemExit(main())
