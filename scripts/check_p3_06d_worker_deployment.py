#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = [
    ".env.example",
    "deploy/docker-compose.yml",
    "deploy/docker-compose.pilot.yml",
    "backend/app/workers/trusted_inbound_worker_service.py",
    "backend/app/workers/trusted_inbound_loop.py",
    "backend/app/services/worker_heartbeats.py",
    "backend/tests/test_p3_06d_worker_deployment.py",
    "docs/P3-06D_WORKER_PROCESS_DEPLOYMENT.md",
]

REQUIRED_ENV_KEYS = [
    "TRUSTED_INBOUND_WORKER_ENABLED",
    "TRUSTED_INBOUND_WORKER_TENANT_SLUG",
    "TRUSTED_INBOUND_WORKER_USER_EMAIL",
    "TRUSTED_INBOUND_WORKER_ID",
    "TRUSTED_INBOUND_WORKER_SLEEP_SECONDS",
    "TRUSTED_INBOUND_WORKER_BATCH_SIZE",
    "TRUSTED_INBOUND_WORKER_RATE_LIMIT_PER_MINUTE",
    "TRUSTED_INBOUND_WORKER_LEASE_SECONDS",
    "TRUSTED_INBOUND_WORKER_HEARTBEAT_STALE_AFTER_SECONDS",
]

REQUIRED_DOC_PHRASES = [
    "P3-06D",
    "Docker Compose worker service",
    "profiles",
    "healthcheck",
    "真实外发仍关闭",
    "告警",
    "不是完整高并发 SLA",
]


def _read(root: Path, relative_path: str) -> str:
    return (root / relative_path).read_text(encoding="utf-8")


def _parse_env_template(text: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def _extract_service_block(compose_text: str, service_name: str) -> str:
    pattern = re.compile(
        rf"^  {re.escape(service_name)}:\n(?P<body>(?:    .*\n|      .*\n|        .*\n|          .*\n|            .*\n|              .*\n)*)",
        flags=re.MULTILINE,
    )
    match = pattern.search(compose_text)
    if not match:
        return ""
    return match.group(0)


def _validate_env(env_text: str) -> list[str]:
    errors: list[str] = []
    values = _parse_env_template(env_text)
    missing = [key for key in REQUIRED_ENV_KEYS if key not in values]
    if missing:
        errors.append(".env.example missing worker keys: " + ", ".join(missing))
    if values.get("TRUSTED_INBOUND_WORKER_ENABLED", "").lower() != "false":
        errors.append("TRUSTED_INBOUND_WORKER_ENABLED must default to false")
    if values.get("TRUSTED_INBOUND_WORKER_TENANT_SLUG"):
        errors.append("TRUSTED_INBOUND_WORKER_TENANT_SLUG must be blank in .env.example")
    if values.get("TRUSTED_INBOUND_WORKER_USER_EMAIL"):
        errors.append("TRUSTED_INBOUND_WORKER_USER_EMAIL must be blank in .env.example")
    return errors


def _validate_compose(base_compose: str, pilot_compose: str) -> list[str]:
    errors: list[str] = []
    base_block = _extract_service_block(base_compose, "trusted-inbound-worker")
    pilot_block = _extract_service_block(pilot_compose, "trusted-inbound-worker")
    merged = base_block + "\n" + pilot_block
    if not base_block:
        errors.append("docker compose missing trusted-inbound-worker service")
        return errors
    if 'profiles: ["worker"]' not in merged and "profiles:\n      - worker" not in merged:
        errors.append("trusted-inbound-worker service must use worker profile")
    if "python" not in merged or "app.workers.trusted_inbound_worker_service" not in merged:
        errors.append("trusted-inbound-worker must run app.workers.trusted_inbound_worker_service")
    if "healthcheck:" not in merged or "--healthcheck" not in merged:
        errors.append("trusted-inbound-worker must define healthcheck using worker healthcheck mode")
    if "depends_on:" not in merged or "postgres:" not in merged or "redis:" not in merged:
        errors.append("trusted-inbound-worker must depend on postgres and redis")
    if 'OUTBOX_EXTERNAL_WRITE_ENABLED: "true"' in merged or "OUTBOX_EXTERNAL_WRITE_ENABLED: 'true'" in merged:
        errors.append("trusted-inbound-worker must force OUTBOX_EXTERNAL_WRITE_ENABLED false")
    if 'OUTBOX_EXTERNAL_WRITE_ENABLED: "false"' not in merged and "OUTBOX_EXTERNAL_WRITE_ENABLED: 'false'" not in merged:
        errors.append("trusted-inbound-worker must force OUTBOX_EXTERNAL_WRITE_ENABLED false")
    if "TRUSTED_INBOUND_WORKER_TENANT_SLUG" not in merged:
        errors.append("trusted-inbound-worker must expose TRUSTED_INBOUND_WORKER_TENANT_SLUG")
    if "TRUSTED_INBOUND_WORKER_USER_EMAIL" not in merged:
        errors.append("trusted-inbound-worker must expose TRUSTED_INBOUND_WORKER_USER_EMAIL")
    return errors


def _validate_worker_service(text: str) -> list[str]:
    required = [
        "resolve_worker_principal",
        "run_worker_service",
        "run_worker_healthcheck",
        "trusted_inbound_worker_service_started",
        "trusted_inbound_worker_service_cycle_completed",
        "external_write",
        "--healthcheck",
    ]
    missing = [token for token in required if token not in text]
    return ["worker service missing tokens: " + ", ".join(missing)] if missing else []


def run_p3_06d_worker_deployment_readiness(root: Path = ROOT) -> dict[str, object]:
    errors: list[str] = []
    missing_files = [path for path in REQUIRED_FILES if not (root / path).exists()]
    if missing_files:
        errors.append("missing required files: " + ", ".join(missing_files))

    if (root / ".env.example").exists():
        errors.extend(_validate_env(_read(root, ".env.example")))
    if (root / "deploy/docker-compose.yml").exists() and (root / "deploy/docker-compose.pilot.yml").exists():
        errors.extend(
            _validate_compose(
                _read(root, "deploy/docker-compose.yml"),
                _read(root, "deploy/docker-compose.pilot.yml"),
            )
        )
    if (root / "backend/app/workers/trusted_inbound_worker_service.py").exists():
        errors.extend(_validate_worker_service(_read(root, "backend/app/workers/trusted_inbound_worker_service.py")))
    if (root / "docs/P3-06D_WORKER_PROCESS_DEPLOYMENT.md").exists():
        doc_text = _read(root, "docs/P3-06D_WORKER_PROCESS_DEPLOYMENT.md")
        missing_doc_phrases = [phrase for phrase in REQUIRED_DOC_PHRASES if phrase not in doc_text]
        if missing_doc_phrases:
            errors.append("P3-06D doc missing phrases: " + ", ".join(missing_doc_phrases))

    return {
        "status": "passed" if not errors else "failed",
        "phase": "P3-06D",
        "check": "worker_process_deployment",
        "errors": errors,
        "external_call_performed": False,
        "external_platform_write_performed": False,
        "production_database_write_performed": False,
    }


def main() -> None:
    result = run_p3_06d_worker_deployment_readiness(ROOT)
    if result["status"] != "passed":
        print("FAIL p3-06d worker deployment: " + "; ".join(result["errors"]))
        sys.exit(1)
    print("PASS p3-06d worker deployment")


if __name__ == "__main__":
    main()
