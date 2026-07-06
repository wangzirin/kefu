#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import re
import zipfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PHASE = "H2W-PILOT3"
SCHEMA_VERSION = "p3-06u-26h2w-pilot3.handoff_archive_gate.v1"
DEFAULT_OUTPUT_DIR = ROOT / "output/p3_06u_26h2w_pilot3_handoff_archive"
DOC_PATH = ROOT / "docs/P3-06U-26H2W_PILOT3_HANDOFF_ARCHIVE.md"

PILOT0_SUMMARY = ROOT / "output/p3_06u_26h2w_pilot0_readiness/summary.json"
PILOT2_SUMMARY = ROOT / "output/p3_06u_26h2w_pilot2_customer_confirmation_flow/summary.json"

DEFAULT_INCLUDE_FILES = [
    ROOT / "docs/customer/万法常世AI智能客服系统_产品介绍.md",
    ROOT / "docs/customer/万法常世AI智能客服系统_客户使用手册.md",
    ROOT / "docs/customer/万法常世AI智能客服系统_服务体系介绍.md",
    ROOT / "docs/customer/万法常世AI智能客服系统_正式部署后运营模式手册.md",
    ROOT / "docs/P3-06U-26H2W_PILOT0_READINESS_LEDGER.md",
    ROOT / "docs/P3-06U-26H2W_PILOT2_CUSTOMER_CONFIRMATION_FLOW.md",
    ROOT / "docs/P3-06U-26H2W_OPS2_CUSTOMER_MONTHLY_OPS_REPORT.md",
    ROOT / "docs/P3-06U-26H2W_INSTALL2_NATIVE_INSTALLER_READINESS.md",
    ROOT / "deploy/customer.env.example",
    ROOT / "deploy/start-local-pilot.sh",
    ROOT / "installers/macos/README.md",
    ROOT / "installers/windows/README.md",
    ROOT / "output/p3_06u_26h2w_ops2_customer_monthly_ops_report/customer_monthly_ops_report.md",
    ROOT / "output/p3_06u_26h2w_kb2_post_import_retest_and_signoff_template/customer_knowledge_retest_signoff_template.csv",
]

FORBIDDEN_PATH_PARTS = {
    ".git",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    "browser-profile",
    "chrome-profile",
    "Cookies",
    "History",
    "Login Data",
}
SENSITIVE_KEY_RE = re.compile(r"(?i)(api[_-]?key|access[_-]?token|refresh[_-]?token|secret|password|encodingaeskey)")
SECRET_ASSIGNMENT_RE = re.compile(
    r"(?i)(api[_-]?key|access[_-]?token|refresh[_-]?token|secret|password|encodingaeskey)[ \t]*[:=][ \t]*[\"']?[A-Za-z0-9_\-]{10,}"
)
PRIVATE_KEY_RE = re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")
ASSIGNMENT_LINE_RE = re.compile(r"^(?:export\s+)?(?P<key>[A-Za-z_][A-Za-z0-9_]*)\s*=\s*(?P<value>.*)$")


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _path_is_safe(path: Path) -> bool:
    parts = set(path.parts)
    return not (parts & FORBIDDEN_PATH_PARTS)


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
            normalized_value = assignment.group("value").strip().strip("\"'`")
            lower_value = normalized_value.lower()
            if not normalized_value or lower_value in {"false", "true", "none", "null"}:
                continue
            if "$" in normalized_value or normalized_value.startswith("("):
                continue
            if SENSITIVE_KEY_RE.search(key) and normalized_value:
                findings.append(f"{_display_path(path)} 第 {line_number} 行包含疑似密钥、密码或 token 赋值")
                break
    if PRIVATE_KEY_RE.search(text):
        findings.append(f"{_display_path(path)} 包含私钥形态")
    if "/Users/ericlee/" in text:
        findings.append(f"{_display_path(path)} 包含本机绝对隐私路径")
    overclaim_phrases = ["正式客户验收已完成", "真实外发已开启", "生产 SLA 已完成", "签名安装包已完成"]
    for phrase in overclaim_phrases:
        if phrase in text:
            findings.append(f"{_display_path(path)} 包含越界承诺：{phrase}")
    return findings


def _load_summary_status(path: Path, expected: set[str], name: str) -> tuple[dict[str, Any], list[str]]:
    if not path.exists():
        return {}, [f"{name} summary 缺失：{_display_path(path)}"]
    payload = _read_json(path)
    status = str(payload.get("status") or "")
    if status not in expected:
        return payload, [f"{name} 状态不满足：期望 {sorted(expected)}，实际 {status}"]
    return payload, []


def _write_archive(
    archive_path: Path,
    include_files: list[Path],
    manifest: dict[str, Any],
) -> None:
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
        for file_path in include_files:
            archive.write(file_path, arcname=_display_path(file_path))


def _write_markdown(path: Path, result: dict[str, Any]) -> None:
    lines = [
        "# H2W-PILOT3 试点交付档案",
        "",
        "## 结论",
        "",
        f"- 阶段状态：`{result['status']}`",
        f"- 档案候选：`{result['archive']['path']}`",
        f"- 文件数：{result['archive']['file_count']}",
        "",
        "## 不包含内容",
        "",
    ]
    lines.extend(f"- {item}" for item in result["not_included"])
    if result["blockers"]:
        lines.extend(["", "## 阻断项", ""])
        lines.extend(f"- {item}" for item in result["blockers"])
    lines.extend(
        [
            "",
            "## 边界",
            "",
            "- 当前档案是试点交付候选，不是正式客户验收包。",
            "- 真实外发、签名安装器和生产 SLA 仍保持关闭或未完成。",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_h2w_pilot3_handoff_archive(
    *,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    doc_path: Path = DOC_PATH,
    pilot0_summary: Path = PILOT0_SUMMARY,
    pilot2_summary: Path = PILOT2_SUMMARY,
    include_files: list[Path] = DEFAULT_INCLUDE_FILES,
) -> dict[str, Any]:
    blockers: list[str] = []
    pilot0, errors = _load_summary_status(
        pilot0_summary,
        {"pilot_candidate_ready_with_internal_data", "pilot_candidate_ready_with_customer_data"},
        "PILOT0",
    )
    blockers.extend(errors)
    pilot2, errors = _load_summary_status(
        pilot2_summary,
        {"waiting_customer_confirmation", "ready_for_customer_confirmation_import_rehearsal"},
        "PILOT2",
    )
    blockers.extend(errors)

    safe_files: list[Path] = []
    inventory: list[dict[str, Any]] = []
    for file_path in include_files:
        exists = file_path.exists()
        item = {"path": _display_path(file_path), "present": exists, "sha256": None}
        if not exists:
            blockers.append(f"交付档案文件缺失：{_display_path(file_path)}")
        elif not _path_is_safe(file_path):
            blockers.append(f"交付档案包含禁止路径：{_display_path(file_path)}")
        else:
            findings = _content_findings(file_path)
            blockers.extend(findings)
            item["sha256"] = _sha256(file_path)
            safe_files.append(file_path)
        inventory.append(item)

    output_dir.mkdir(parents=True, exist_ok=True)
    archive_path = output_dir / "pilot_handoff_archive_candidate.zip"
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "phase": PHASE,
        "archive_status": "pilot_handoff_archive_candidate",
        "generated_from": {
            "pilot0_status": pilot0.get("status"),
            "pilot2_status": pilot2.get("status"),
        },
        "boundaries": {
            "formal_customer_signoff_ready": False,
            "real_platform_send_ready": False,
            "signed_dmg_exe_ready": False,
            "production_sla_ready": False,
        },
        "files": inventory,
    }
    if not blockers:
        _write_archive(archive_path, safe_files, manifest)

    result = {
        "schema_version": SCHEMA_VERSION,
        "phase": PHASE,
        "status": "blocked" if blockers else "pilot_handoff_archive_candidate",
        "archive": {
            "path": _display_path(archive_path),
            "exists": archive_path.exists(),
            "file_count": len(safe_files),
        },
        "manifest": manifest,
        "blockers": sorted(set(blockers)),
        "not_included": [
            "真实 key、token、数据库密码和私钥",
            "客户原文、草稿全文和平台 payload",
            ".git、node_modules、临时数据库和浏览器 profile",
            "真实外发结果、生产 SLA 和正式客户验收承诺",
        ],
        "readiness": {
            "pilot_handoff_archive_candidate": not blockers,
            "formal_customer_signoff_ready": False,
            "real_platform_send_ready": False,
            "signed_dmg_exe_ready": False,
        },
    }
    _write_json(output_dir / "summary.json", result)
    _write_json(output_dir / "manifest.json", manifest)
    _write_markdown(doc_path, result)
    return result


def main() -> int:
    result = run_h2w_pilot3_handoff_archive()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] != "blocked" else 1


if __name__ == "__main__":
    raise SystemExit(main())
