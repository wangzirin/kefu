#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import re
import zipfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PHASE = "H2W-PACK7"
SCHEMA_VERSION = "p3-06u-26h2w-pack7.trial_handoff_archive_v2.v1"
DEFAULT_OUTPUT_DIR = ROOT / "output/p3_06u_26h2w_pack7_trial_handoff_archive_v2"
DOC_PATH = ROOT / "docs/P3-06U-26H2W_PACK7_TRIAL_HANDOFF_ARCHIVE_V2.md"

UPSTREAMS = {
    "pilot7": (
        ROOT / "output/p3_06u_26h2w_pilot7_co_creation_trial_readiness/summary.json",
        {"co_creation_trial_candidate_ready_with_internal_data", "co_creation_trial_candidate_ready_with_customer_data"},
    ),
    "fe7": (
        ROOT / "output/p3_06u_26h2w_fe7_customer_trial_browser_smoke/summary.json",
        {"passed_customer_trial_browser_smoke"},
    ),
    "kb4": (
        ROOT / "output/p3_06u_26h2w_kb4_customer_knowledge_trial_loop/summary.json",
        {"customer_knowledge_trial_loop_ready"},
    ),
    "install5": (
        ROOT / "output/p3_06u_26h2w_install5_local_startup_experience/summary.json",
        {"local_startup_experience_ready"},
    ),
    "ops3": (
        ROOT / "output/p3_06u_26h2w_ops3_customer_trial_ops_loop/summary.json",
        {"customer_trial_ops_loop_ready"},
    ),
    "pack5": (
        ROOT / "output/p3_06u_26h2w_pack5_customer_handoff_package/summary.json",
        {"ready_for_customer_local_pilot_handoff_candidate"},
    ),
}

INCLUDE_FILES = [
    ROOT / "docs/customer/万法常世AI智能客服系统_产品介绍.md",
    ROOT / "docs/customer/万法常世AI智能客服系统_客户使用手册.md",
    ROOT / "docs/customer/万法常世AI智能客服系统_服务体系介绍.md",
    ROOT / "docs/customer/万法常世AI客服本地试点启动说明.md",
    ROOT / "docs/customer/万法常世AI客服本地试跑启动体验说明.md",
    ROOT / "docs/customer/万法常世AI客服本地试跑运维说明.md",
    ROOT / "deploy/customer.env.example",
    ROOT / "deploy/start-local-pilot.sh",
    ROOT / "installers/INSTALL4_EXPERIENCE_CHECKLIST.md",
    ROOT / "installers/macos/README.md",
    ROOT / "installers/windows/README.md",
    ROOT / "evals/p3_06u_26h2w_kb3_customer_knowledge_center_template.csv",
    ROOT / "output/p3_06u_26h2w_kb4_customer_knowledge_trial_loop/wanfa_customer_knowledge_trial_template.xlsx",
    ROOT / "output/p3_06u_26h2w_ops2_customer_monthly_ops_report/customer_monthly_ops_report.md",
    ROOT / "output/p3_06u_26h2w_pilot7_co_creation_trial_readiness/summary.json",
    ROOT / "output/p3_06u_26h2w_fe7_customer_trial_browser_smoke/summary.json",
    ROOT / "output/p3_06u_26h2w_kb4_customer_knowledge_trial_loop/summary.json",
    ROOT / "output/p3_06u_26h2w_install5_local_startup_experience/summary.json",
    ROOT / "output/p3_06u_26h2w_ops3_customer_trial_ops_loop/summary.json",
]

FORBIDDEN_PATH_PARTS = {
    ".git",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    "chrome-profile",
    "browser-profile",
    "Cookies",
    "History",
    "Login Data",
}
SENSITIVE_KEY_RE = re.compile(r"(?i)(api[_-]?key|access[_-]?token|refresh[_-]?token|secret|password|encodingaeskey)")
PRIVATE_KEY_RE = re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")
ASSIGNMENT_LINE_RE = re.compile(r"^(?:export\s+)?(?P<key>[A-Za-z_][A-Za-z0-9_]*)\s*=\s*(?P<value>.*)$")
OVERCLAIMS = [
    "正式客户验收已完成",
    "真实外发已开启",
    "真实外发已接通",
    "全渠道已接通",
    "生产 SLA 已完成",
    "签名安装包已完成",
    "签名 dmg/exe 已完成",
]


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _content_findings(path: Path) -> list[str]:
    if path.suffix.lower() not in {".md", ".txt", ".csv", ".json", ".env", ".example", ".sh", ".ps1", ".bat", ".yml", ".yaml"}:
        return []
    text = path.read_text(encoding="utf-8", errors="ignore")
    findings: list[str] = []
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#") or "replace-with-local-random-password" in line:
            continue
        assignment = ASSIGNMENT_LINE_RE.match(line)
        if assignment:
            key = assignment.group("key")
            value = assignment.group("value").strip().strip("\"'`")
            if value.startswith("$") or "$(get_env_value" in value:
                continue
            if value and value.lower() not in {"false", "true", "none", "null"} and SENSITIVE_KEY_RE.search(key):
                findings.append(f"{_display_path(path)} 第 {line_number} 行包含疑似密钥、密码或 token 赋值")
                break
    if PRIVATE_KEY_RE.search(text):
        findings.append(f"{_display_path(path)} 包含私钥形态")
    if "/Users/ericlee/" in text:
        findings.append(f"{_display_path(path)} 包含本机绝对隐私路径")
    for phrase in OVERCLAIMS:
        if phrase in text:
            findings.append(f"{_display_path(path)} 包含越界承诺：{phrase}")
    return findings


def _load_upstreams() -> tuple[dict[str, Any], list[str]]:
    summaries: dict[str, Any] = {}
    blockers: list[str] = []
    for name, (path, expected) in UPSTREAMS.items():
        payload = _read_json(path)
        status = str(payload.get("status") or "missing")
        summaries[name] = {"path": _display_path(path), "status": status}
        if status not in expected:
            blockers.append(f"{name} 状态不满足：期望 {sorted(expected)}，实际 {status}")
        readiness = payload.get("readiness") if isinstance(payload.get("readiness"), dict) else {}
        boundaries = payload.get("boundaries") if isinstance(payload.get("boundaries"), dict) else {}
        if readiness.get("real_platform_send_ready") is True or boundaries.get("real_platform_send_performed") is True:
            blockers.append(f"{name} 越界声明真实外发 ready/performed")
        if readiness.get("signed_dmg_exe_ready") is True:
            blockers.append(f"{name} 越界声明 signed_dmg_exe_ready=true")
        if readiness.get("production_sla_ready") is True:
            blockers.append(f"{name} 越界声明 production_sla_ready=true")
    return summaries, blockers


def _write_archive(path: Path, files: list[Path], manifest: dict[str, Any]) -> None:
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
        for file_path in files:
            archive.write(file_path, arcname=_display_path(file_path))


def _write_markdown(path: Path, result: dict[str, Any]) -> None:
    lines = [
        "# H2W-PACK7 试跑交付档案 v2",
        "",
        "## 结论",
        "",
        f"- 阶段状态：`{result['status']}`",
        f"- 档案候选：`{result['archive']['path']}`",
        f"- 文件数：`{result['archive']['file_count']}`",
        "",
        "## 纳入证据",
        "",
    ]
    for name, item in result["upstreams"].items():
        lines.append(f"- {name}：`{item['status']}`，`{item['path']}`")
    lines.extend(["", "## 不包含内容", ""])
    lines.extend(
        [
            "- 真实 key、token、数据库密码和私钥。",
            "- 客户原文、草稿全文和平台 payload。",
            "- `.git`、`node_modules`、临时数据库和浏览器 profile。",
            "- 真实外发结果、生产 SLA、正式客户签收和已签名安装包承诺。",
        ]
    )
    lines.extend(["", "## 阻断项", ""])
    lines.extend([f"- {item}" for item in result["blockers"]] or ["- 无"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_h2w_pack7_trial_handoff_archive_v2(
    *,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    doc_path: Path = DOC_PATH,
) -> dict[str, Any]:
    upstreams, blockers = _load_upstreams()
    safe_files: list[Path] = []
    inventory: list[dict[str, Any]] = []
    for file_path in INCLUDE_FILES:
        item = {"path": _display_path(file_path), "present": file_path.exists(), "sha256": None}
        if not file_path.exists():
            blockers.append(f"交付档案文件缺失：{_display_path(file_path)}")
        elif set(file_path.parts) & FORBIDDEN_PATH_PARTS:
            blockers.append(f"交付档案包含禁止路径：{_display_path(file_path)}")
        else:
            blockers.extend(_content_findings(file_path))
            item["sha256"] = _sha256(file_path)
            safe_files.append(file_path)
        inventory.append(item)

    output_dir.mkdir(parents=True, exist_ok=True)
    archive_path = output_dir / "co_creation_trial_handoff_archive_v2_candidate.zip"
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "phase": PHASE,
        "archive_status": "co_creation_trial_handoff_archive_v2_candidate",
        "generated_from": upstreams,
        "boundaries": {
            "formal_customer_signoff_ready": False,
            "real_platform_send_ready": False,
            "signed_dmg_exe_ready": False,
            "production_sla_ready": False,
            "internal_rehearsal_not_customer_signoff": True,
        },
        "files": inventory,
    }
    if not blockers:
        _write_archive(archive_path, safe_files, manifest)

    result = {
        "schema_version": SCHEMA_VERSION,
        "phase": PHASE,
        "status": "blocked" if blockers else "co_creation_trial_handoff_archive_v2_candidate",
        "upstreams": upstreams,
        "archive": {"path": _display_path(archive_path), "exists": archive_path.exists(), "file_count": len(safe_files)},
        "manifest": manifest,
        "blockers": sorted(set(blockers)),
        "readiness": {
            "co_creation_trial_handoff_archive_v2_candidate": not blockers,
            "formal_customer_signoff_ready": False,
            "real_platform_send_ready": False,
            "signed_dmg_exe_ready": False,
            "production_sla_ready": False,
        },
        "boundaries": manifest["boundaries"],
    }
    _write_json(output_dir / "summary.json", result)
    _write_json(output_dir / "manifest.json", manifest)
    _write_markdown(doc_path, result)
    return result


def main() -> int:
    result = run_h2w_pack7_trial_handoff_archive_v2()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] != "blocked" else 1


if __name__ == "__main__":
    raise SystemExit(main())
