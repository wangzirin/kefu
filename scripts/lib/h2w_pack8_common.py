from __future__ import annotations

import csv
import hashlib
import json
import re
import zipfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]

NOT_READY_FOR = [
    "正式客户验收签收",
    "真实平台自动外发",
    "企业微信、公众号、抖音、淘宝、京东、拼多多等真实渠道接通",
    "生产 SLA 承诺",
    "已签名 dmg/exe 安装器",
    "RPA 或个人号外挂正式交付",
]

BOUNDARIES = {
    "formal_customer_signoff_ready": False,
    "real_platform_send_ready": False,
    "signed_dmg_exe_ready": False,
    "production_sla_ready": False,
    "rpa_formal_delivery_enabled": False,
}

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
JSON_SECRET_LINE_RE = re.compile(
    r"(?i)[\"']?(?P<key>api[_-]?key|access[_-]?token|refresh[_-]?token|secret|password|encodingaeskey)[\"']?\s*:\s*[\"'](?P<value>[^\"']{8,})[\"']"
)
PHONE_RE = re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)")
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
ABS_PRIVATE_PATH_RE = re.compile(r"/Users/ericlee/(?!Desktop/01_项目工作区/肥肥lu/lite_a_customer_service/standard_ops)")

OVERCLAIMS = [
    "正式客户验收已完成",
    "客户正式签收已完成",
    "正式准确率签收已完成",
    "真实外发已开启",
    "真实外发已接通",
    "全渠道已接通",
    "生产 SLA 已完成",
    "签名安装包已完成",
    "签名 dmg/exe 已完成",
]


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def summary_status(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"path": display_path(path), "present": False, "status": "missing", "blocker_count": 0}
    try:
        payload = read_json(path)
    except json.JSONDecodeError:
        return {"path": display_path(path), "present": True, "status": "invalid_json", "blocker_count": 1}
    blockers = payload.get("blockers")
    return {
        "path": display_path(path),
        "present": True,
        "status": str(payload.get("status") or "missing_status"),
        "blocker_count": len(blockers) if isinstance(blockers, list) else 0,
    }


def load_expected_summary(name: str, path: Path, expected_statuses: set[str]) -> tuple[dict[str, Any], dict[str, Any], list[str]]:
    status = summary_status(path)
    if not status["present"]:
        return {}, status, [f"{name} summary 缺失：{status['path']}"]
    if status["status"] == "invalid_json":
        return {}, status, [f"{name} summary 不是有效 JSON：{status['path']}"]
    payload = read_json(path)
    if status["status"] not in expected_statuses:
        return payload, status, [f"{name} 状态不满足：期望 {sorted(expected_statuses)}，实际 {status['status']}"]
    return payload, status, []


def flag(payload: dict[str, Any], *path: str) -> Any:
    current: Any = payload
    for key in path:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def boundary_blockers(name: str, payload: dict[str, Any]) -> list[str]:
    checks = {
        "真实外发已接通或已执行": (
            flag(payload, "readiness", "real_platform_send_ready") is True
            or flag(payload, "boundaries", "real_platform_send_performed") is True
            or flag(payload, "boundaries", "external_platform_write_performed") is True
        ),
        "客户正式签收已完成": (
            flag(payload, "readiness", "formal_customer_signoff_ready") is True
            or flag(payload, "readiness", "formal_accuracy_signoff") is True
            or flag(payload, "boundaries", "formal_customer_signoff_performed") is True
        ),
        "签名安装包已完成": (
            flag(payload, "readiness", "signed_dmg_exe_ready") is True
            or flag(payload, "readiness", "desktop_installer_ready") is True
            or flag(payload, "readiness", "native_installer_ready") is True
        ),
        "生产 SLA 已完成": (
            flag(payload, "readiness", "production_sla_ready") is True
            or flag(payload, "boundaries", "production_sla_ready") is True
        ),
        "RPA 正式交付已开启": (
            flag(payload, "readiness", "rpa_formal_delivery_ready") is True
            or flag(payload, "boundaries", "rpa_formal_delivery_enabled") is True
        ),
    }
    return [f"{name} 上游越界写成 ready 或已完成：{label}" for label, failed in checks.items() if failed]


def scan_text_file(path: Path, *, allow_internal_sample_contacts: bool = True) -> list[str]:
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
                findings.append(f"{display_path(path)} 第 {line_number} 行包含疑似密钥、密码或 token 赋值")
                break
        json_secret = JSON_SECRET_LINE_RE.search(line)
        if json_secret:
            value = json_secret.group("value").strip()
            if value.lower() not in {"false", "true", "none", "null", "replace-with-local-random-password"}:
                findings.append(f"{display_path(path)} 第 {line_number} 行包含疑似 JSON 密钥、密码或 token 字段")
                break
    if PRIVATE_KEY_RE.search(text):
        findings.append(f"{display_path(path)} 包含私钥形态")
    if ABS_PRIVATE_PATH_RE.search(text):
        findings.append(f"{display_path(path)} 包含本机绝对隐私路径")
    if not allow_internal_sample_contacts and (PHONE_RE.search(text) or EMAIL_RE.search(text)):
        findings.append(f"{display_path(path)} 包含疑似个人联系方式")
    for phrase in OVERCLAIMS:
        if phrase in text:
            findings.append(f"{display_path(path)} 包含越界承诺：{phrase}")
    return findings


def scan_archive_candidates(files: list[Path]) -> list[str]:
    findings: list[str] = []
    for file_path in files:
        if not file_path.exists():
            findings.append(f"候选文件缺失：{display_path(file_path)}")
            continue
        if set(file_path.parts) & FORBIDDEN_PATH_PARTS:
            findings.append(f"候选文件包含禁止路径：{display_path(file_path)}")
            continue
        findings.extend(scan_text_file(file_path))
    return findings


def write_markdown_report(path: Path, title: str, result: dict[str, Any], sections: list[tuple[str, list[str]]]) -> None:
    lines = [
        f"# {title}",
        "",
        "## 结论",
        "",
        f"- 阶段状态：`{result['status']}`",
        f"- 阻断项：`{len(result.get('blockers', []))}` 个",
        "",
    ]
    for heading, bullets in sections:
        lines.extend([f"## {heading}", ""])
        lines.extend([f"- {item}" for item in bullets] or ["- 无"])
        lines.append("")
    lines.extend(["## 不可承诺", ""])
    lines.extend([f"- {item}" for item in result.get("not_ready_for", NOT_READY_FOR)])
    lines.extend(["", "## 阻断项", ""])
    lines.extend([f"- {item}" for item in result.get("blockers", [])] or ["- 无"])
    write_text(path, "\n".join(lines) + "\n")


def build_zip(path: Path, files: list[Path], manifest: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
        for file_path in files:
            archive.write(file_path, arcname=display_path(file_path))


def base_result(schema_version: str, phase: str, status: str, blockers: list[str]) -> dict[str, Any]:
    return {
        "schema_version": schema_version,
        "phase": phase,
        "status": "blocked" if blockers else status,
        "blockers": sorted(set(blockers)),
        "boundaries": {**BOUNDARIES},
        "not_ready_for": [*NOT_READY_FOR],
        "customer_data_used": False,
        "internal_sample_used": True,
    }
