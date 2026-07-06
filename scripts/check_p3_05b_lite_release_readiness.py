#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import re
import sys
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]


REQUIRED_FILES = [
    "README.md",
    ".env.example",
    "deploy/docker-compose.yml",
    "deploy/docker-compose.pilot.yml",
    "backend/app/core/config.py",
    "backend/app/services/model_gateway.py",
    "docs/P3-05_PILOT_DEPLOYMENT_READINESS.md",
    "docs/P3-05B_LITE_PILOT_RELEASE_READINESS.md",
    "docs/P3-05B_HOSTED_CLOUD_RUNBOOK.md",
    "docs/P3-05B_PRIVATE_DEPLOYMENT_PACKAGE.md",
    "docs/P3-05B_HOSTED_CLOUD_PRIVATE_OPS_NEXT_PLAN.md",
    "docs/PRODUCTIZATION_MASTER_PLAN_LITE_AND_STANDARD.md",
    "docs/customer/万法常世AI智能客服系统_产品介绍.md",
    "docs/customer/万法常世AI智能客服系统_服务体系介绍.md",
    "docs/customer/万法常世AI智能客服系统_客户使用手册.md",
    "docs/internal/万法常世AI智能客服系统_内部售后运营维护计划.md",
    "docs/internal/REMOTE_MAINTENANCE_AUTHORIZATION_SOP.md",
    "scripts/check_p3_05_deployment_readiness.py",
    "scripts/create_p3_05_diagnostic_bundle.py",
]

REQUIRED_DOC_PHRASES = {
    "docs/P3-05B_LITE_PILOT_RELEASE_READINESS.md": [
        "Lite 试点版",
        "不能承诺",
        "真实外发",
        "封版验收门禁",
        "诊断包",
        "客户准备清单",
    ],
    "docs/P3-05B_HOSTED_CLOUD_RUNBOOK.md": [
        "C0 试点托管",
        "C1 正式托管",
        "HTTPS",
        "PostgreSQL",
        "Redis",
        "回滚",
    ],
    "docs/P3-05B_PRIVATE_DEPLOYMENT_PACKAGE.md": [
        "镜像",
        "env 模板",
        "迁移",
        "备份",
        "禁止项",
        "未授权真实外发",
    ],
    "docs/internal/REMOTE_MAINTENANCE_AUTHORIZATION_SOP.md": [
        "P0",
        "P1",
        "P2",
        "P3",
        "诊断包优先",
        "只读优先",
        "变更二次授权",
        "权限回收",
        "禁止命令",
        "故障复盘模板",
    ],
}

REQUIRED_ENV_KEYS = [
    "STANDARD_OPS_ENV",
    "DATABASE_URL",
    "REDIS_URL",
    "BAILIAN_API_KEY",
    "DEEPSEEK_API_KEY",
    "DEEPSEEK_FALLBACK_MODEL",
    "KNOWLEDGE_EMBEDDING_PROVIDER",
    "KNOWLEDGE_EMBEDDING_API_KEY",
    "KNOWLEDGE_VECTOR_STORE",
    "OUTBOX_WORKER_RATE_LIMIT_PER_MINUTE",
    "OUTBOX_EXTERNAL_WRITE_ENABLED",
    "WECOM_KF_SECRET",
    "WECOM_KF_CALLBACK_TOKEN",
    "WECOM_KF_ENCODING_AES_KEY",
]

BLANK_SECRET_KEYS = [
    "BAILIAN_API_KEY",
    "DEEPSEEK_API_KEY",
    "KNOWLEDGE_EMBEDDING_API_KEY",
    "WECOM_KF_SECRET",
    "WECOM_KF_CALLBACK_TOKEN",
    "WECOM_KF_ENCODING_AES_KEY",
]

FORBIDDEN_SECRET_FRAGMENTS = [
    "sk-",
    "Bearer ",
    "AKIA",
    "xoxb-",
    "-----BEGIN PRIVATE KEY-----",
]

CONFIG_REQUIRED_TOKENS = [
    "deepseek_fallback_model",
    "knowledge_embedding_provider",
    "knowledge_vector_store",
    "outbox_worker_rate_limit_per_minute",
    "outbox_worker_batch_size",
    "outbox_worker_max_attempts",
    "outbox_external_write_enabled",
]


def _read(root: Path, relative_path: str) -> str:
    return (root / relative_path).read_text(encoding="utf-8")


def _parse_env_example(text: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def validate_env_template(env_text: str) -> list[str]:
    errors: list[str] = []
    env_values = _parse_env_example(env_text)

    missing_keys = [key for key in REQUIRED_ENV_KEYS if key not in env_values]
    if missing_keys:
        errors.append(".env.example missing keys: " + ", ".join(missing_keys))

    for fragment in FORBIDDEN_SECRET_FRAGMENTS:
        if fragment in env_text:
            errors.append(f"possible secret fragment in .env.example: {fragment}")

    if env_values.get("OUTBOX_EXTERNAL_WRITE_ENABLED", "").lower() != "false":
        errors.append("OUTBOX_EXTERNAL_WRITE_ENABLED must default to false")

    for key in BLANK_SECRET_KEYS:
        if env_values.get(key):
            errors.append(f"{key} must be empty in .env.example")

    for raw_line in env_text.splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key_upper = key.strip().upper()
        if not _is_sensitive_template_key(key_upper):
            continue
        if value.strip():
            errors.append(f"possible filled secret-like value in .env.example: {key.strip()}")

    return errors


def _is_sensitive_template_key(key_upper: str) -> bool:
    return (
        key_upper.endswith("API_KEY")
        or key_upper.endswith("_SECRET")
        or key_upper.endswith("SECRET")
        or key_upper.endswith("_TOKEN")
        or key_upper.endswith("TOKEN")
        or key_upper.endswith("ENCODING_AES_KEY")
        or key_upper.endswith("PRIVATE_KEY")
    )


def _extract_service_block(compose_text: str, service_name: str) -> str:
    pattern = re.compile(
        rf"^  {re.escape(service_name)}:\n(?P<body>(?:    .*\n|      .*\n|        .*\n|          .*\n|            .*\n|              .*\n)*)",
        flags=re.MULTILINE,
    )
    match = pattern.search(compose_text)
    if not match:
        return ""
    return match.group(0)


def validate_compose_contract(base_compose: str, pilot_compose: str) -> list[str]:
    errors: list[str] = []
    combined = base_compose + "\n" + pilot_compose

    for service_name in ["postgres", "redis", "backend", "frontend"]:
        base_block = _extract_service_block(base_compose, service_name)
        pilot_block = _extract_service_block(pilot_compose, service_name)
        if not base_block and not pilot_block:
            errors.append(f"docker compose service missing: {service_name}")
            continue

        merged_block = base_block + "\n" + pilot_block
        has_health_or_dependency = "healthcheck:" in merged_block or "depends_on:" in merged_block
        if not has_health_or_dependency:
            errors.append(f"docker compose service missing healthcheck or dependency: {service_name}")

    if "OUTBOX_EXTERNAL_WRITE_ENABLED: \"false\"" not in combined and "OUTBOX_EXTERNAL_WRITE_ENABLED: 'false'" not in combined:
        errors.append("pilot compose must force OUTBOX_EXTERNAL_WRITE_ENABLED to false")

    if "standard_ops_pilot_postgres" not in pilot_compose:
        errors.append("pilot compose missing dedicated postgres volume")
    if "standard_ops_pilot_redis" not in pilot_compose:
        errors.append("pilot compose missing dedicated redis volume")

    return errors


def validate_backend_config(config_text: str) -> list[str]:
    missing = [token for token in CONFIG_REQUIRED_TOKENS if token not in config_text]
    if not missing:
        return []
    return ["backend config missing tokens: " + ", ".join(missing)]


def _missing_phrases(text: str, phrases: Iterable[str]) -> list[str]:
    return [phrase for phrase in phrases if phrase not in text]


def run_p3_05b_lite_release_readiness(root: Path = ROOT) -> dict[str, object]:
    errors: list[str] = []

    missing_files = [path for path in REQUIRED_FILES if not (root / path).exists()]
    if missing_files:
        errors.append("missing required files: " + ", ".join(missing_files))

    for doc_path, phrases in REQUIRED_DOC_PHRASES.items():
        if not (root / doc_path).exists():
            continue
        text = _read(root, doc_path)
        missing = _missing_phrases(text, phrases)
        if missing:
            errors.append(f"{doc_path} missing phrases: " + ", ".join(missing))

    if (root / ".env.example").exists():
        errors.extend(validate_env_template(_read(root, ".env.example")))

    if (root / "deploy/docker-compose.yml").exists() and (root / "deploy/docker-compose.pilot.yml").exists():
        errors.extend(
            validate_compose_contract(
                _read(root, "deploy/docker-compose.yml"),
                _read(root, "deploy/docker-compose.pilot.yml"),
            )
        )

    if (root / "backend/app/core/config.py").exists():
        errors.extend(validate_backend_config(_read(root, "backend/app/core/config.py")))

    docx_dir = root / "output" / "documents"
    if docx_dir.exists():
        docx_files = list(docx_dir.glob("万法常世AI全智能客服系统_*_正式版.docx"))
        if len(docx_files) != 3:
            errors.append("expected 3 formal customer DOCX files when output/documents exists")

    return {
        "status": "passed" if not errors else "failed",
        "phase": "P3-05B",
        "check": "lite_release_readiness",
        "errors": errors,
        "checked_files": REQUIRED_FILES,
        "external_call_performed": False,
        "external_platform_write_performed": False,
        "production_database_write_performed": False,
    }


def fail(message: str) -> None:
    print(f"FAIL p3-05b lite release readiness: {message}")
    sys.exit(1)


def main() -> None:
    result = run_p3_05b_lite_release_readiness(ROOT)
    if result["status"] != "passed":
        fail("; ".join(result["errors"]))
    print("PASS p3-05b lite release readiness")


if __name__ == "__main__":
    main()
