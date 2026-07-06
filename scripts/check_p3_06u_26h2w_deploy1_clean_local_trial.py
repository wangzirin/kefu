#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

from lib.h2w_pack8_common import ROOT, base_result, display_path, load_expected_summary, scan_archive_candidates, write_json, write_markdown_report


PHASE = "H2W-DEPLOY1"
SCHEMA_VERSION = "p3-06u-26h2w-deploy1.clean_local_trial.v1"
DEFAULT_OUTPUT_DIR = ROOT / "output/p3_06u_26h2w_deploy1_clean_local_trial"
DOC_PATH = ROOT / "docs/P3-06U-26H2W_DEPLOY1_CLEAN_LOCAL_TRIAL.md"

UPSTREAMS = {
    "pack2": (
        ROOT / "output/p3_06u_26h2w_pack2_full_stack_startup_rehearsal/summary.json",
        {"passed_full_stack_backend_startup_rehearsal"},
    ),
    "install5": (
        ROOT / "output/p3_06u_26h2w_install5_local_startup_experience/summary.json",
        {"local_startup_experience_ready"},
    ),
    "pack4": (
        ROOT / "output/p3_06u_26h2w_pack4_delivery_checklist_and_startup_rehearsal/summary.json",
        {"ready_for_customer_local_pilot_startup_rehearsal"},
    ),
}

SAFETY_FILES = [
    ROOT / "deploy/customer.env.example",
    ROOT / "deploy/start-local-pilot.sh",
    ROOT / "deploy/docker-compose.pilot.yml",
]


def run_h2w_deploy1_clean_local_trial(
    *,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    doc_path: Path = DOC_PATH,
) -> dict:
    blockers: list[str] = []
    evidence: dict[str, dict] = {}
    for name, (path, expected) in UPSTREAMS.items():
        payload, status, errors = load_expected_summary(name, path, expected)
        evidence[name] = status
        blockers.extend(errors)
        if payload.get("readiness", {}).get("real_platform_send_ready") is True:
            blockers.append(f"{name} 越界声明真实外发 ready")
    blockers.extend(scan_archive_candidates(SAFETY_FILES))

    text = "\n".join(path.read_text(encoding="utf-8", errors="ignore") for path in SAFETY_FILES if path.exists())
    required_safety_terms = [
        "OUTBOX_EXTERNAL_WRITE_ENABLED=false",
        "TRUSTED_INBOUND_WORKER_ENABLED=false",
        "STANDARD_OPS_DEV_BOOTSTRAP_ENABLED=false",
    ]
    for term in required_safety_terms:
        if term not in text:
            blockers.append(f"客户启动安全配置缺少：{term}")

    result = base_result(SCHEMA_VERSION, PHASE, "clean_local_trial_rehearsal_passed", blockers)
    result.update(
        {
            "upstreams": evidence,
            "evidence_paths": [status["path"] for status in evidence.values()] + [display_path(path) for path in SAFETY_FILES],
            "readiness": {
                "clean_local_trial_rehearsal_passed": not blockers,
                "temporary_empty_database_evidence": evidence["pack2"]["status"] == "passed_full_stack_backend_startup_rehearsal",
                "owner_creation_evidence": evidence["pack2"]["status"] == "passed_full_stack_backend_startup_rehearsal",
                "real_platform_send_ready": False,
                "default_password_created": False,
            },
        }
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    write_json(output_dir / "summary.json", result)
    write_markdown_report(
        doc_path,
        "H2W-DEPLOY1 干净环境本地部署演练",
        result,
        [
            ("上游证据", [f"{name}: `{item['status']}` ({item['path']})" for name, item in evidence.items()]),
            ("安全配置", required_safety_terms),
        ],
    )
    return result


def main() -> int:
    result = run_h2w_deploy1_clean_local_trial()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] != "blocked" else 1


if __name__ == "__main__":
    raise SystemExit(main())
