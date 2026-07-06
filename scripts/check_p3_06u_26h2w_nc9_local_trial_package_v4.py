#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from lib.h2w_pack8_common import (
    ROOT,
    base_result,
    boundary_blockers,
    build_zip,
    display_path,
    load_expected_summary,
    scan_archive_candidates,
    sha256,
    write_json,
    write_markdown_report,
    write_text,
)


PHASE = "H2W-NC9"
SCHEMA_VERSION = "p3-06u-26h2w-nc9.local_trial_package_v4.v1"
DEFAULT_OUTPUT_DIR = ROOT / "output/p3_06u_26h2w_nc9_local_trial_package_v4"
DOC_PATH = ROOT / "docs/P3-06U-26H2W_NC9_LOCAL_TRIAL_PACKAGE_V4.md"
PACKAGE_README = DEFAULT_OUTPUT_DIR / "LOCAL_TRIAL_PACKAGE_V4_README.md"

UPSTREAMS: dict[str, tuple[Path, set[str]]] = {
    "nc1_fact_authority": (
        ROOT / "output/p3_06u_26h2w_nc1_pilot_fact_authority/summary.json",
        {"nc1_pilot_fact_authority_ready"},
    ),
    "nc2_customer_mode_security": (
        ROOT / "output/p3_06u_26h2w_nc2_customer_mode_hardening/summary.json",
        {"customer_mode_security_hardening_ready"},
    ),
    "nc3_material_precheck": (
        ROOT / "output/p3_06u_26h2w_nc3_customer_material_precheck_productization/summary.json",
        {"customer_material_precheck_productization_ready"},
    ),
    "nc4_knowledge_network": (
        ROOT / "output/p3_06u_26h2w_nc4_knowledge_memory_mesh_overview/summary.json",
        {"knowledge_memory_mesh_overview_ready"},
    ),
    "nc5_retrieval_governance": (
        ROOT / "output/p3_06u_26h2w_nc5_production_retrieval_governance/summary.json",
        {"production_retrieval_governance_ready_not_production_switch", "production_retrieval_governance_ready_for_switch"},
    ),
    "nc6_llm_ops": (
        ROOT / "output/p3_06u_26h2w_nc6_llm_ops_observability_redteam/summary.json",
        {"llm_ops_observability_ready_not_redteam_complete", "llm_ops_redteam_ready_for_controlled_pilot"},
    ),
    "nc7_frontend_productization": (
        ROOT / "output/p3_06u_26h2w_nc7_frontend_productization/summary.json",
        {"frontend_productization_customer_flow_ready_component_split_pending"},
    ),
    "nc8_install_backup_update": (
        ROOT / "output/p3_06u_26h2w_nc8_local_install_backup_update_rollback/summary.json",
        {"local_install_backup_update_rollback_hardened_pg_script_ready"},
    ),
    "pack11_trial_v3": (
        ROOT / "output/p3_06u_26h2w_pack11_local_trial_v3_candidate/summary.json",
        {"internal_sample_local_trial_package_v3_candidate", "customer_data_local_trial_package_v3_candidate"},
    ),
    "pack12_material_rerun": (
        ROOT / "output/p3_06u_26h2w_pack12_customer_data_rerun_orchestrator/summary.json",
        {"internal_sample_data_rerun_orchestration_ready", "customer_data_rerun_orchestration_ready"},
    ),
    "fe12_browser_qa": (
        ROOT / "output/p3_06u_26h2w_fe12_customer_perspective_browser_qa/summary.json",
        {"passed_customer_perspective_browser_qa"},
    ),
    "kb6_knowledge_retest": (
        ROOT / "output/p3_06u_26h2w_kb6_real_customer_knowledge_retest/summary.json",
        {"customer_knowledge_retest_ready_with_internal_sample", "customer_knowledge_retest_ready_with_customer_data"},
    ),
    "trial3_shadow_trial": (
        ROOT / "output/p3_06u_26h2w_trial3_real_customer_shadow_trial/summary.json",
        {"shadow_trial_ready_with_internal_sample", "shadow_trial_ready_with_customer_data"},
    ),
    "ops2_monthly_report": (
        ROOT / "output/p3_06u_26h2w_ops2_customer_monthly_ops_report/summary.json",
        {"ready_for_customer_monthly_ops_report_rehearsal"},
    ),
    "ops3_trial_ops_loop": (
        ROOT / "output/p3_06u_26h2w_ops3_customer_trial_ops_loop/summary.json",
        {"customer_trial_ops_loop_ready"},
    ),
    "install7_customer_mode": (
        ROOT / "output/p3_06u_26h2w_install7_customer_mode_prepack_gate/summary.json",
        {"customer_mode_prepack_gate_ready"},
    ),
}

PACKAGE_SECTIONS: dict[str, list[Path]] = {
    "启动说明": [
        ROOT / "docs/customer/万法常世AI客服本地试点启动说明.md",
        ROOT / "docs/customer/万法常世AI客服本地试跑启动体验说明.md",
        ROOT / "deploy/start-local-pilot.sh",
        ROOT / "deploy/start-local-pilot.command",
    ],
    "首任负责人说明": [
        ROOT / "docs/customer/万法常世AI客服本地试点启动说明.md",
        ROOT / "docs/P3-06U-26H2W_DEPLOY1_CLEAN_LOCAL_TRIAL.md",
        ROOT / "docs/P3-06U-26H2W_INSTALL7_CUSTOMER_MODE_PREPACK_GATE.md",
    ],
    "客户资料模板": [
        ROOT / "docs/customer/万法常世AI客服真实资料接收与脱敏手册.md",
        ROOT / "evals/p3_06u_26h2w_data2_real_customer_material_readiness/README.md",
        ROOT / "evals/p3_06u_26h2w_data2_real_customer_material_readiness/customer_materials_real_template.csv",
        ROOT / "evals/p3_06u_26h2w_data2_real_customer_material_readiness/customer_trial_questions_real_template.csv",
        ROOT / "evals/p3_06u_26h2w_data2_real_customer_material_readiness/customer_material_manifest_template.json",
    ],
    "知识导入和预检说明": [
        ROOT / "docs/P3-06U-26H2W_NC3_CUSTOMER_MATERIAL_PRECHECK_PRODUCTIZATION.md",
        ROOT / "docs/P3-06U-26H2W_KB3_CUSTOMER_KNOWLEDGE_CENTER.md",
        ROOT / "docs/P3-06U-26H2W_NC4_KNOWLEDGE_MEMORY_MESH_OVERVIEW.md",
        ROOT / "docs/P3-06U-26H2W_NC5_PRODUCTION_RETRIEVAL_GOVERNANCE.md",
    ],
    "知识复测报告": [
        ROOT / "output/p3_06u_26h2w_kb6_real_customer_knowledge_retest/real_customer_knowledge_retest_report.md",
        ROOT / "docs/P3-06U-26H2W_KB6_REAL_CUSTOMER_KNOWLEDGE_RETEST.md",
    ],
    "影子试跑质量报告": [
        ROOT / "output/p3_06u_26h2w_trial3_real_customer_shadow_trial/real_customer_shadow_trial_quality_report.md",
        ROOT / "docs/P3-06U-26H2W_TRIAL3_REAL_CUSTOMER_SHADOW_TRIAL.md",
    ],
    "月度运维报告": [
        ROOT / "output/p3_06u_26h2w_ops2_customer_monthly_ops_report/customer_monthly_ops_report.md",
        ROOT / "docs/P3-06U-26H2W_OPS2_CUSTOMER_MONTHLY_OPS_REPORT.md",
        ROOT / "docs/customer/万法常世AI客服本地试跑运维说明.md",
    ],
    "诊断备份更新回滚说明": [
        ROOT / "docs/customer/万法常世AI客服本地试跑运维说明.md",
        ROOT / "docs/P3-06U-26H2W_OPS3_CUSTOMER_TRIAL_OPS_LOOP.md",
        ROOT / "docs/P3-06U-26H2W_NC8_LOCAL_INSTALL_BACKUP_UPDATE_ROLLBACK.md",
        ROOT / "deploy/postgres-backup-dry-run.sh",
    ],
    "安装候选说明": [
        ROOT / "docs/P3-06U-26H2W_INSTALL6_TRIAL_INSTALLER_EXPERIENCE.md",
        ROOT / "docs/P3-06U-26H2W_INSTALL7_CUSTOMER_MODE_PREPACK_GATE.md",
        ROOT / "docs/customer/万法常世AI客服本地试跑启动体验说明.md",
        ROOT / "deploy/customer.env.example",
    ],
    "明确边界声明": [
        ROOT / "docs/H2W_COMMERCIAL_READINESS_EXCEPT_CHANNELS_MASTER_PLAN.md",
        PACKAGE_README,
    ],
}


def _unique_existing_files(section_files: dict[str, list[Path]]) -> list[Path]:
    seen: set[Path] = set()
    files: list[Path] = []
    for paths in section_files.values():
        for path in paths:
            if path.exists() and path not in seen:
                files.append(path)
                seen.add(path)
    return files


def _write_package_readme(path: Path, *, status: str, customer_data_used: bool) -> None:
    source = "真实客户资料" if customer_data_used else "内部准真实样板"
    lines = [
        "# 万法常世 AI 客服本地试跑包 v4 候选说明",
        "",
        f"- 阶段状态：`{status}`",
        f"- 本次资料来源：{source}",
        "- 适用范围：小微企业共创客户的本地受控试跑。",
        "- 不适用范围：正式客户验收、真实平台自动外发、真实全渠道上线、生产 SLA、签名安装器。",
        "",
        "## 使用顺序",
        "",
        "1. 阅读启动说明，复制 `customer.env.example` 并在客户本机填写本地密码。",
        "2. 运行本地启动脚本，确认开发入口、真实外发和入站 worker 均为关闭。",
        "3. 第一次进入工作台时创建首任负责人账号。",
        "4. 按资料模板整理知识资料、标准问答、流程政策、禁用承诺和转人工规则。",
        "5. 先做资料预检，再导入知识，随后执行复测和影子试跑质量报告。",
        "6. 生成诊断包、备份证据、月度运维报告和更新预检记录。",
        "",
        "## 固定边界",
        "",
        "- 本包不包含真实 key、token、密码、私钥、客户原文或平台 payload。",
        "- 本包不包含 `.git`、`node_modules`、浏览器 profile、临时数据库、Cookies、History 或 Login Data。",
        "- 真实外发保持关闭，真实渠道未接通。",
        "- 程序更新仍是候选流程；签名 dmg/exe 安装器尚未完成。",
        "- 如果本次资料来源是内部样板，不能将报告写成真实客户签收或客户准确率验收。",
    ]
    write_text(path, "\n".join(lines) + "\n")


def _section_status() -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for name, paths in PACKAGE_SECTIONS.items():
        existing = [path for path in paths if path.exists()]
        result[name] = {
            "ready": bool(existing),
            "files": [display_path(path) for path in existing],
            "missing": [display_path(path) for path in paths if not path.exists()],
        }
    return result


def _archive_status(payloads: dict[str, dict[str, Any]]) -> tuple[str, bool]:
    pack11_customer = payloads.get("pack11_trial_v3", {}).get("customer_data_used") is True
    pack12_customer = payloads.get("pack12_material_rerun", {}).get("customer_data_used") is True
    customer_data_used = pack11_customer and pack12_customer
    if customer_data_used:
        return "local_trial_package_v4_candidate_with_real_customer_materials", True
    return "local_trial_package_v4_candidate_with_internal_sample", False


def run_nc9(
    *,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    doc_path: Path = DOC_PATH,
) -> dict[str, Any]:
    blockers: list[str] = []
    upstreams: dict[str, dict[str, Any]] = {}
    payloads: dict[str, dict[str, Any]] = {}
    for name, (path, expected) in UPSTREAMS.items():
        payload, status, errors = load_expected_summary(name, path, expected)
        payloads[name] = payload
        upstreams[name] = status
        blockers.extend(errors)
        if payload:
            blockers.extend(boundary_blockers(name, payload))

    status, customer_data_used = _archive_status(payloads)
    output_dir.mkdir(parents=True, exist_ok=True)
    _write_package_readme(PACKAGE_README, status=status, customer_data_used=customer_data_used)

    sections = _section_status()
    for name, item in sections.items():
        if not item["ready"]:
            blockers.append(f"NC9 档案缺少必需板块：{name}")

    package_files = _unique_existing_files(PACKAGE_SECTIONS)
    blockers.extend(scan_archive_candidates(package_files))

    archive_path = output_dir / "local_trial_package_v4_candidate.zip"
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "phase": PHASE,
        "status": status,
        "customer_data_used": customer_data_used,
        "internal_sample_used": not customer_data_used,
        "upstreams": upstreams,
        "sections": sections,
        "boundaries": {
            "formal_customer_signoff_ready": False,
            "real_platform_send_ready": False,
            "real_channel_integrations_ready": False,
            "signed_dmg_exe_ready": False,
            "production_sla_ready": False,
            "rpa_formal_delivery_enabled": False,
        },
        "not_ready_for": [
            "正式客户验收签收",
            "真实平台自动外发",
            "真实渠道接通",
            "生产 SLA 承诺",
            "已签名 dmg/exe 安装器",
            "成熟全渠道商用客服发布",
        ],
        "files": [{"path": display_path(path), "sha256": sha256(path)} for path in package_files],
    }

    if blockers:
        archive_path.unlink(missing_ok=True)
    else:
        build_zip(archive_path, package_files, manifest)

    result = base_result(SCHEMA_VERSION, PHASE, status, blockers)
    result.update(
        {
            "customer_data_used": customer_data_used,
            "internal_sample_used": not customer_data_used,
            "upstreams": upstreams,
            "sections": sections,
            "archive": {
                "path": display_path(archive_path),
                "exists": archive_path.exists(),
                "file_count": len(package_files),
                "sha256": sha256(archive_path) if archive_path.exists() else None,
            },
            "readiness": {
                "local_trial_package_v4_candidate": not blockers,
                "local_trial_package_v4_candidate_with_internal_sample": not blockers and not customer_data_used,
                "local_trial_package_v4_candidate_with_real_customer_materials": not blockers and customer_data_used,
                "formal_customer_signoff_ready": False,
                "real_platform_send_ready": False,
                "real_channel_integrations_ready": False,
                "signed_dmg_exe_ready": False,
                "production_sla_ready": False,
            },
            "evidence_paths": [
                display_path(archive_path),
                display_path(output_dir / "manifest.json"),
                display_path(output_dir / "summary.json"),
                display_path(doc_path),
                display_path(PACKAGE_README),
            ],
            "manifest": manifest,
            "known_limits": [
                "当前真实渠道闭环不在 NC9 范围内。",
                "当前签名安装包仍未完成。",
                "若 customer_data_used=false，本包只能作为内部样板试跑候选，不能写成真实客户资料版封包。",
                "NC5 生产检索治理和 NC6 模型观测可作为证据，但红队完整闭环与生产检索切换仍未完成。",
            ],
        }
    )

    write_json(output_dir / "summary.json", result)
    write_json(output_dir / "manifest.json", manifest)
    write_markdown_report(
        doc_path,
        "H2W-NC9 非真实渠道版本地试跑包 v4",
        result,
        [
            ("上游状态", [f"{name}: `{item['status']}` ({item['path']})" for name, item in upstreams.items()]),
            ("档案板块", [f"{name}: `{str(item['ready']).lower()}`，文件 {len(item['files'])} 个" for name, item in sections.items()]),
            ("档案候选", [f"`{display_path(archive_path)}`", f"文件数：{len(package_files)}"]),
            ("固定边界", result["known_limits"]),
        ],
    )
    return result


def main() -> int:
    result = run_nc9()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] != "blocked" else 1


if __name__ == "__main__":
    raise SystemExit(main())
