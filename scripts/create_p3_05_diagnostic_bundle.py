#!/usr/bin/env python3
from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import json
import os
import re


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "output" / "diagnostics"

KEY_FILES = [
    "README.md",
    ".env.example",
    "deploy/docker-compose.yml",
    "backend/requirements.txt",
    "backend/alembic.ini",
    "backend/app/main.py",
    "backend/app/api/health.py",
    "backend/app/core/config.py",
    "docs/P3-05_PILOT_DEPLOYMENT_READINESS.md",
    "docs/customer/万法常世AI智能客服系统_产品介绍.md",
    "docs/customer/万法常世AI智能客服系统_服务体系介绍.md",
    "docs/customer/万法常世AI智能客服系统_客户使用手册.md",
    "docs/internal/万法常世AI智能客服系统_内部售后运营维护计划.md",
]

SECRET_HINTS = [
    re.compile(r"sk-[A-Za-z0-9_-]{12,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"(?i)bearer\\s+[A-Za-z0-9._-]{16,}"),
    re.compile(r"-----BEGIN PRIVATE KEY-----"),
]


def is_secret_like_env_key(key: str) -> bool:
    key_upper = key.upper()
    return (
        key_upper.endswith("API_KEY")
        or key_upper.endswith("_KEY")
        or "SECRET" in key_upper
        or key_upper.endswith("TOKEN")
        or key_upper.endswith("_TOKEN")
        or "PASSWORD" in key_upper
    )


def file_digest(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    return sha256(path.read_bytes()).hexdigest()


def safe_file_record(relative: str) -> dict:
    path = ROOT / relative
    exists = path.exists()
    stat = path.stat() if exists else None
    return {
        "path": relative,
        "exists": exists,
        "bytes": stat.st_size if stat else None,
        "sha256": file_digest(path),
    }


def parse_env_keys() -> dict:
    path = ROOT / ".env.example"
    keys = []
    external_write_default = None
    filled_secret_like_keys = []
    if not path.exists():
        return {
            "exists": False,
            "keys": [],
            "external_write_default": None,
            "filled_secret_like_keys": [],
        }

    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        value = value.strip()
        keys.append(key)
        if key == "OUTBOX_EXTERNAL_WRITE_ENABLED":
            external_write_default = value
        if is_secret_like_env_key(key):
            if value and "change-me" not in value and "password" not in value.lower():
                filled_secret_like_keys.append(key)

    return {
        "exists": True,
        "keys": keys,
        "external_write_default": external_write_default,
        "filled_secret_like_keys": filled_secret_like_keys,
    }


def migration_summary() -> dict:
    revisions = sorted(
        ROOT.glob("backend/app/migrations/versions/[0-9][0-9][0-9][0-9]_*.py")
    )
    return {
        "count": len(revisions),
        "first": revisions[0].name if revisions else None,
        "last": revisions[-1].name if revisions else None,
        "revisions": [item.name for item in revisions],
    }


def compose_summary() -> dict:
    path = ROOT / "deploy/docker-compose.yml"
    if not path.exists():
        return {"exists": False, "services": [], "ports": []}
    text = path.read_text(encoding="utf-8")
    services = [
        service
        for service in ["postgres", "redis", "backend", "frontend"]
        if f"  {service}:" in text or text.startswith(f"{service}:")
    ]
    ports = re.findall(r'"([0-9]+:[0-9]+)"', text)
    return {"exists": True, "services": services, "ports": ports}


def scan_key_files_for_secret_hints() -> list[dict]:
    findings = []
    for relative in KEY_FILES:
        path = ROOT / relative
        if not path.exists() or not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in SECRET_HINTS:
            if pattern.search(text):
                findings.append({"path": relative, "pattern": pattern.pattern})
    return findings


def build_bundle() -> dict:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    env = parse_env_keys()
    return {
        "generated_at_utc": now,
        "project_root": str(ROOT),
        "bundle_policy": {
            "reads_dot_env": False,
            "includes_api_keys": False,
            "includes_customer_message_text": False,
            "safe_for_remote_triage": True,
        },
        "files": [safe_file_record(path) for path in KEY_FILES],
        "env_example": env,
        "compose": compose_summary(),
        "migrations": migration_summary(),
        "safety": {
            "outbox_external_write_default": env.get("external_write_default"),
            "secret_hint_findings": scan_key_files_for_secret_hints(),
            "filled_secret_like_keys_in_env_example": env.get(
                "filled_secret_like_keys", []
            ),
        },
        "runtime_snapshot": {
            "cwd": os.getcwd(),
            "python": "bundled or project venv python expected",
            "docker_checked": False,
            "network_checked": False,
            "external_provider_checked": False,
        },
    }


def write_markdown(bundle: dict, markdown_path: Path) -> None:
    safety = bundle["safety"]
    lines = [
        "# P3-05A 诊断包摘要",
        "",
        f"生成时间：{bundle['generated_at_utc']}",
        "",
        "## 安全口径",
        "",
        "- 未读取 `.env` 明文。",
        "- 未包含 API key、平台 token 或客户聊天原文。",
        "- 未进行网络请求、Docker 操作或真实 provider 调用。",
        "",
        "## 关键状态",
        "",
        f"- 外发默认值：`{safety['outbox_external_write_default']}`",
        f"- Alembic 迁移数量：`{bundle['migrations']['count']}`",
        f"- Compose 服务：`{', '.join(bundle['compose']['services'])}`",
        f"- Compose 端口：`{', '.join(bundle['compose']['ports'])}`",
        f"- 密钥片段扫描命中：`{len(safety['secret_hint_findings'])}`",
        f"- `.env.example` 已填 secret-like 字段：`{len(safety['filled_secret_like_keys_in_env_example'])}`",
        "",
        "## 关键文件",
        "",
        "| 文件 | 存在 | 字节 | SHA256 |",
        "| --- | --- | ---: | --- |",
    ]
    for item in bundle["files"]:
        digest = item["sha256"][:12] if item["sha256"] else ""
        lines.append(
            f"| `{item['path']}` | {item['exists']} | {item['bytes'] or 0} | `{digest}` |"
        )
    lines.append("")
    lines.append("## 后续人工检查")
    lines.append("")
    lines.append("- 在客户试点环境中执行 PostgreSQL 空库迁移。")
    lines.append("- 在客户授权后配置真实模型 key 并做小样本 smoke。")
    lines.append("- 真实渠道接入前复核官方平台文档、回调域名、Token 和外发开关。")
    markdown_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    bundle = build_bundle()
    json_path = OUTPUT_DIR / f"p3_05_diagnostic_bundle_{stamp}.json"
    markdown_path = OUTPUT_DIR / f"p3_05_diagnostic_bundle_{stamp}.md"
    json_path.write_text(
        json.dumps(bundle, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    write_markdown(bundle, markdown_path)
    print(f"WROTE {json_path}")
    print(f"WROTE {markdown_path}")


if __name__ == "__main__":
    main()
