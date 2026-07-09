#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[1]


REQUIRED_FILES = [
    "README.md",
    ".env.example",
    "deploy/docker-compose.yml",
    "backend/alembic.ini",
    "backend/app/main.py",
    "backend/app/api/health.py",
    "backend/app/migrations/env.py",
    "docs/P3-05_PILOT_DEPLOYMENT_READINESS.md",
    "docs/PRODUCTIZATION_MASTER_PLAN_LITE_AND_STANDARD.md",
    "docs/customer/万法常世AI智能客服系统_产品介绍.md",
    "docs/customer/万法常世AI智能客服系统_服务体系介绍.md",
    "docs/customer/万法常世AI智能客服系统_客户使用手册.md",
    "docs/internal/万法常世AI智能客服系统_内部售后运营维护计划.md",
    "scripts/create_p3_05_diagnostic_bundle.py",
]

REQUIRED_ENV_KEYS = [
    "STANDARD_OPS_ENV",
    "STANDARD_OPS_APP_NAME",
    "STANDARD_OPS_ALLOWED_ORIGINS",
    "DATABASE_URL",
    "REDIS_URL",
    "ADMIN_BOOTSTRAP_EMAIL",
    "ADMIN_BOOTSTRAP_PASSWORD",
    "BAILIAN_API_BASE",
    "BAILIAN_API_KEY",
    "BAILIAN_MODEL",
    "DEEPSEEK_API_BASE",
    "DEEPSEEK_API_KEY",
    "KNOWLEDGE_EMBEDDING_PROVIDER",
    "KNOWLEDGE_VECTOR_STORE",
    "OUTBOX_EXTERNAL_WRITE_ENABLED",
    "WECOM_CORP_ID",
    "WECOM_KF_CALLBACK_TOKEN",
    "WECOM_KF_ENCODING_AES_KEY",
]

REQUIRED_DOC_PHRASES = [
    "Engineering Control Card",
    "环境变量清单",
    "备份与恢复",
    "诊断包",
    "远程维护方式",
    "准确率下降监控",
    "外发与渠道边界",
    "不能对外承诺",
]

FORBIDDEN_ENV_FRAGMENTS = [
    "sk-",
    "Bearer ",
    "AKIA",
    "xoxb-",
    "-----BEGIN PRIVATE KEY-----",
]


def fail(message: str) -> None:
    print(f"FAIL p3-05 readiness: {message}")
    sys.exit(1)


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _parse_env_example(text: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def main() -> None:
    missing = [item for item in REQUIRED_FILES if not (ROOT / item).exists()]
    if missing:
        fail("missing required files: " + ", ".join(missing))

    p3_doc = _read("docs/P3-05_PILOT_DEPLOYMENT_READINESS.md")
    missing_phrases = [phrase for phrase in REQUIRED_DOC_PHRASES if phrase not in p3_doc]
    if missing_phrases:
        fail("P3-05 document missing phrases: " + ", ".join(missing_phrases))

    env_text = _read(".env.example")
    env_values = _parse_env_example(env_text)
    missing_env = [key for key in REQUIRED_ENV_KEYS if key not in env_values]
    if missing_env:
        fail(".env.example missing keys: " + ", ".join(missing_env))

    for fragment in FORBIDDEN_ENV_FRAGMENTS:
        if fragment in env_text:
            fail(f"possible secret fragment in .env.example: {fragment}")

    if env_values.get("OUTBOX_EXTERNAL_WRITE_ENABLED", "").lower() != "false":
        fail("OUTBOX_EXTERNAL_WRITE_ENABLED must default to false")

    for key in ["BAILIAN_API_KEY", "DEEPSEEK_API_KEY", "KNOWLEDGE_EMBEDDING_API_KEY"]:
        if env_values.get(key):
            fail(f"{key} must be empty in .env.example")

    compose = _read("deploy/docker-compose.yml")
    for service in ["postgres:", "redis:", "backend:", "frontend:"]:
        if service not in compose:
            fail(f"docker compose service missing: {service.rstrip(':')}")
    for port in ['"5173:5173"', '"8000:8080"']:
        if port not in compose:
            fail(f"docker compose port mapping missing: {port}")

    revisions = sorted(
        ROOT.glob("backend/app/migrations/versions/[0-9][0-9][0-9][0-9]_*.py")
    )
    if len(revisions) < 16:
        fail(f"expected at least 16 Alembic revisions, found {len(revisions)}")

    customer_docs = [
        "docs/customer/万法常世AI智能客服系统_产品介绍.md",
        "docs/customer/万法常世AI智能客服系统_服务体系介绍.md",
        "docs/customer/万法常世AI智能客服系统_客户使用手册.md",
    ]
    for doc_path in customer_docs:
        text = _read(doc_path)
        if len(text.splitlines()) < 80:
            fail(f"customer doc looks too thin: {doc_path}")

    internal_doc = _read("docs/internal/万法常世AI智能客服系统_内部售后运营维护计划.md")
    for phrase in ["远程维护", "诊断包", "准确率下降", "故障", "运维成本"]:
        if phrase not in internal_doc:
            fail(f"internal support SOP missing phrase: {phrase}")

    docx_dir = ROOT / "output" / "documents"
    if docx_dir.exists():
        docx_files = list(docx_dir.glob("万法常世AI全智能客服系统_*_正式版.docx"))
        if docx_files and len(docx_files) < 3:
            fail("partial customer DOCX set exists; expected 3 formal DOCX files")

    for raw_line in env_text.splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key_upper = key.upper()
        is_secret_like = (
            key_upper.endswith("API_KEY")
            or key_upper.endswith("_KEY")
            or "SECRET" in key_upper
            or key_upper.endswith("TOKEN")
            or key_upper.endswith("_TOKEN")
        )
        if not is_secret_like:
            continue
        if value.strip():
            fail(f"possible filled secret-like value in .env.example: {key}")

    print("PASS p3-05 deployment readiness")


if __name__ == "__main__":
    main()
