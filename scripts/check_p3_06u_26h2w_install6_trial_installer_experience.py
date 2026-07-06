#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from lib.h2w_pack8_common import ROOT, base_result, display_path, read_json, scan_text_file, write_json, write_markdown_report


PHASE = "H2W-INSTALL6"
SCHEMA_VERSION = "p3-06u-26h2w-install6.trial_installer_experience.v1"
DEFAULT_OUTPUT_DIR = ROOT / "output/p3_06u_26h2w_install6_trial_installer_experience"
DOC_PATH = ROOT / "docs/P3-06U-26H2W_INSTALL6_TRIAL_INSTALLER_EXPERIENCE.md"
INSTALL5_SUMMARY = ROOT / "output/p3_06u_26h2w_install5_local_startup_experience/summary.json"

REQUIRED_FILES = [
    ROOT / "deploy/start-local-pilot.sh",
    ROOT / "deploy/start-local-pilot.command",
    ROOT / "deploy/customer.env.example",
    ROOT / "installers/VERSION.json",
    ROOT / "installers/INSTALL6_SIGNING_READINESS_CHECKLIST.md",
    ROOT / "installers/macos/WanfaCustomerService.command",
    ROOT / "installers/macos/WanfaCustomerService.app/Contents/Info.plist",
    ROOT / "installers/macos/WanfaCustomerService.app/Contents/MacOS/WanfaCustomerService",
    ROOT / "installers/macos/preflight.sh",
    ROOT / "installers/macos/health-check.sh",
    ROOT / "installers/macos/uninstall-notes.md",
    ROOT / "installers/windows/Start-WanfaCustomerService.ps1",
    ROOT / "installers/windows/start-wanfa-customer-service.bat",
    ROOT / "installers/windows/HealthCheck-WanfaCustomerService.ps1",
    ROOT / "installers/windows/uninstall-notes.md",
    ROOT / "installers/logs/README.md",
]

REQUIRED_MARKERS = {
    "deploy/start-local-pilot.sh": ["Docker", "OUTBOX_EXTERNAL_WRITE_ENABLED", "TRUSTED_INBOUND_WORKER_ENABLED"],
    "deploy/customer.env.example": ["OUTBOX_EXTERNAL_WRITE_ENABLED=false", "TRUSTED_INBOUND_WORKER_ENABLED=false"],
    "installers/INSTALL6_SIGNING_READINESS_CHECKLIST.md": ["signed_dmg_exe_ready=false", "正式安装包前必须补齐"],
    "installers/macos/preflight.sh": ["Docker Desktop", "端口"],
    "installers/windows/Start-WanfaCustomerService.ps1": ["Docker Desktop", "customer.env"],
    "installers/logs/README.md": ["数据库密码", "平台 token", "客户原文"],
}


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def run_h2w_install6_trial_installer_experience(
    *,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    doc_path: Path = DOC_PATH,
) -> dict[str, Any]:
    blockers: list[str] = []
    install5 = read_json(INSTALL5_SUMMARY)
    if install5.get("status") != "local_startup_experience_ready":
        blockers.append(f"INSTALL5 上游状态不满足：{install5.get('status') or 'missing'}")

    inventory = [{"path": display_path(path), "present": path.exists()} for path in REQUIRED_FILES]
    blockers.extend([f"安装体验候选文件缺失：{item['path']}" for item in inventory if not item["present"]])

    for rel_path, markers in REQUIRED_MARKERS.items():
        path = ROOT / rel_path
        text = _text(path)
        for marker in markers:
            if marker not in text:
                blockers.append(f"{rel_path} 缺少启动体验门禁标记：{marker}")

    version = read_json(ROOT / "installers/VERSION.json")
    boundaries = version.get("boundaries") if isinstance(version.get("boundaries"), dict) else {}
    if boundaries.get("signed_dmg_exe_ready") is not False:
        blockers.append("installers/VERSION.json 未保持 signed_dmg_exe_ready=false")
    if boundaries.get("real_platform_send_ready") is not False:
        blockers.append("installers/VERSION.json 未保持 real_platform_send_ready=false")

    for path in REQUIRED_FILES:
        if path.exists():
            blockers.extend(scan_text_file(path))

    result = base_result(SCHEMA_VERSION, PHASE, "trial_installer_experience_candidate_ready", blockers)
    result.update(
        {
            "customer_data_used": False,
            "internal_sample_used": False,
            "inventory": inventory,
            "evidence_paths": [display_path(path) for path in REQUIRED_FILES if path.exists()] + [display_path(doc_path)],
            "readiness": {
                "installer_trial_status": "trial_installer_experience_candidate_ready" if not blockers else "blocked",
                "native_wrapper_candidate_ready": not blockers,
                "signed_dmg_exe_ready": False,
                "real_platform_send_ready": False,
                "silent_update_ready": False,
                "remote_control_ready": False,
            },
        }
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    write_json(output_dir / "summary.json", result)
    write_markdown_report(
        doc_path,
        "H2W-INSTALL6 安装体验试跑候选",
        result,
        [
            ("覆盖文件", [item["path"] for item in inventory]),
            ("下一阶段签名安装包清单", [display_path(ROOT / "installers/INSTALL6_SIGNING_READINESS_CHECKLIST.md")]),
        ],
    )
    return result


def main() -> int:
    result = run_h2w_install6_trial_installer_experience()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if result["status"] == "blocked" else 0


if __name__ == "__main__":
    raise SystemExit(main())
