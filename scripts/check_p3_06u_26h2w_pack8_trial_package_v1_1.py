#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

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
)


PHASE = "H2W-PACK8"
SCHEMA_VERSION = "p3-06u-26h2w-pack8.co_creation_trial_package_v1_1.v1"
DEFAULT_OUTPUT_DIR = ROOT / "output/p3_06u_26h2w_pack8_trial_package_v1_1"
DOC_PATH = ROOT / "docs/P3-06U-26H2W_PACK8_CO_CREATION_TRIAL_PACKAGE_V1_1.md"

UPSTREAMS = {
    "trial_c0": (ROOT / "output/p3_06u_26h2w_trial_c0_co_creation_scope/summary.json", {"trial_scope_ready"}),
    "data1": (
        ROOT / "output/p3_06u_26h2w_data1_customer_material_intake/summary.json",
        {"customer_materials_ready", "internal_sample_only_ready"},
    ),
    "deploy1": (
        ROOT / "output/p3_06u_26h2w_deploy1_clean_local_trial/summary.json",
        {"clean_local_trial_rehearsal_passed"},
    ),
    "kb5": (
        ROOT / "output/p3_06u_26h2w_kb5_customer_knowledge_retest/summary.json",
        {"customer_knowledge_retest_ready_with_customer_data", "customer_knowledge_retest_ready_with_internal_data"},
    ),
    "trial2": (
        ROOT / "output/p3_06u_26h2w_trial2_shadow_trial_report/summary.json",
        {"shadow_trial_ready_with_customer_data", "shadow_trial_ready_with_internal_data"},
    ),
    "fe8": (
        ROOT / "output/p3_06u_26h2w_fe8_trial_friction_frontend_qa/summary.json",
        {"trial_frontend_friction_resolved"},
    ),
    "ops3": (ROOT / "output/p3_06u_26h2w_ops3_customer_trial_ops_loop/summary.json", {"customer_trial_ops_loop_ready"}),
    "install5": (ROOT / "output/p3_06u_26h2w_install5_local_startup_experience/summary.json", {"local_startup_experience_ready"}),
    "pack7": (
        ROOT / "output/p3_06u_26h2w_pack7_trial_handoff_archive_v2/summary.json",
        {"co_creation_trial_handoff_archive_v2_candidate"},
    ),
}

INCLUDE_FILES = [
    ROOT / "docs/P3-06U-26H2W_TRIAL_C0_CO_CREATION_SCOPE.md",
    ROOT / "docs/P3-06U-26H2W_DATA1_CUSTOMER_MATERIAL_INTAKE.md",
    ROOT / "docs/P3-06U-26H2W_DEPLOY1_CLEAN_LOCAL_TRIAL.md",
    ROOT / "docs/P3-06U-26H2W_KB5_CUSTOMER_KNOWLEDGE_RETEST.md",
    ROOT / "docs/P3-06U-26H2W_TRIAL2_SHADOW_TRIAL_REPORT.md",
    ROOT / "docs/P3-06U-26H2W_PACK7_TRIAL_HANDOFF_ARCHIVE_V2.md",
    ROOT / "docs/customer/万法常世AI客服本地试跑启动体验说明.md",
    ROOT / "docs/customer/万法常世AI客服本地试跑运维说明.md",
    ROOT / "deploy/customer.env.example",
    ROOT / "deploy/start-local-pilot.sh",
    ROOT / "evals/p3_06u_26h2w_data1_customer_material_intake/manifest.json",
    ROOT / "evals/p3_06u_26h2w_data1_customer_material_intake/customer_materials_internal_sample.csv",
    ROOT / "evals/p3_06u_26h2w_data1_customer_material_intake/customer_trial_questions_internal_sample.csv",
    ROOT / "output/p3_06u_26h2w_kb5_customer_knowledge_retest/customer_knowledge_retest_report.md",
    ROOT / "output/p3_06u_26h2w_trial2_shadow_trial_report/shadow_trial_quality_report.md",
    ROOT / "output/p3_06u_26h2w_ops2_customer_monthly_ops_report/customer_monthly_ops_report.md",
]


def run_h2w_pack8_trial_package_v1_1(
    *,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    doc_path: Path = DOC_PATH,
) -> dict:
    blockers: list[str] = []
    upstreams: dict[str, dict] = {}
    payloads: dict[str, dict] = {}
    for name, (path, expected) in UPSTREAMS.items():
        payload, status, errors = load_expected_summary(name, path, expected)
        payloads[name] = payload
        upstreams[name] = status
        blockers.extend(errors)
        if payload:
            blockers.extend(boundary_blockers(name, payload))

    existing_files = [path for path in INCLUDE_FILES if path.exists()]
    blockers.extend(scan_archive_candidates(INCLUDE_FILES))
    customer_data_used = payloads.get("data1", {}).get("customer_data_used") is True
    archive_status = (
        "co_creation_trial_package_v1_1_candidate_with_customer_data"
        if customer_data_used
        else "co_creation_trial_package_v1_1_candidate_with_internal_data"
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    archive_path = output_dir / "co_creation_trial_package_v1_1_candidate.zip"
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "phase": PHASE,
        "status": archive_status,
        "customer_data_used": customer_data_used,
        "internal_sample_used": not customer_data_used,
        "upstreams": upstreams,
        "boundaries": {
            "formal_customer_signoff_ready": False,
            "real_platform_send_ready": False,
            "signed_dmg_exe_ready": False,
            "production_sla_ready": False,
            "rpa_formal_delivery_enabled": False,
        },
        "files": [{"path": display_path(path), "sha256": sha256(path)} for path in existing_files],
    }
    if not blockers:
        build_zip(archive_path, existing_files, manifest)

    result = base_result(SCHEMA_VERSION, PHASE, archive_status, blockers)
    result.update(
        {
            "upstreams": upstreams,
            "archive": {
                "path": display_path(archive_path),
                "exists": archive_path.exists(),
                "file_count": len(existing_files),
                "sha256": sha256(archive_path) if archive_path.exists() else None,
            },
            "manifest": manifest,
            "evidence_paths": [display_path(archive_path), display_path(output_dir / "manifest.json"), display_path(doc_path)],
            "customer_data_used": customer_data_used,
            "internal_sample_used": not customer_data_used,
            "readiness": {
                "co_creation_trial_package_v1_1_candidate": not blockers,
                "formal_customer_signoff_ready": False,
                "real_platform_send_ready": False,
                "signed_dmg_exe_ready": False,
                "production_sla_ready": False,
            },
        }
    )
    write_json(output_dir / "summary.json", result)
    write_json(output_dir / "manifest.json", manifest)
    write_markdown_report(
        doc_path,
        "H2W-PACK8 共创客户本地试跑包 v1.1 候选",
        result,
        [
            ("上游证据", [f"{name}: `{item['status']}` ({item['path']})" for name, item in upstreams.items()]),
            ("档案", [f"`{display_path(archive_path)}`", f"文件数：{len(existing_files)}"]),
            ("边界", ["这是 v1.1 候选包，不是正式客户验收。", "真实外发、真实渠道、签名安装器和生产 SLA 仍未完成。"]),
        ],
    )
    return result


def main() -> int:
    result = run_h2w_pack8_trial_package_v1_1()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] != "blocked" else 1


if __name__ == "__main__":
    raise SystemExit(main())
