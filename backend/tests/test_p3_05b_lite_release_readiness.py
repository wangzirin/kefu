import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = ROOT / "scripts" / "check_p3_05b_lite_release_readiness.py"


def _load_script():
    spec = importlib.util.spec_from_file_location("check_p3_05b_lite_release_readiness", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_p3_05b_lite_release_readiness_passes_on_current_project() -> None:
    module = _load_script()

    result = module.run_p3_05b_lite_release_readiness(ROOT)

    assert result["status"] == "passed"
    assert result["phase"] == "P3-05B"
    assert result["check"] == "lite_release_readiness"
    assert result["external_call_performed"] is False
    assert result["external_platform_write_performed"] is False
    assert result["production_database_write_performed"] is False
    assert result["errors"] == []


def test_env_template_validation_is_line_based_and_blocks_real_keys() -> None:
    module = _load_script()

    safe_env = """
STANDARD_OPS_ENV=pilot
DATABASE_URL=postgresql+psycopg://wanfa_ops:wanfa_ops_password@postgres:5432/wanfa_ops
REDIS_URL=redis://redis:6379/0
BAILIAN_API_KEY=
DEEPSEEK_API_KEY=
DEEPSEEK_FALLBACK_MODEL=deepseek-v4-flash
KNOWLEDGE_EMBEDDING_PROVIDER=deterministic_local
KNOWLEDGE_EMBEDDING_API_KEY=
KNOWLEDGE_VECTOR_STORE=sqlite_json_vector_store
KNOWLEDGE_EMBEDDING_PRICE_PER_1K_TOKENS=0
OUTBOX_WORKER_RATE_LIMIT_PER_MINUTE=60
OUTBOX_EXTERNAL_WRITE_ENABLED=false
WECOM_KF_SECRET=
WECOM_KF_CALLBACK_TOKEN=
WECOM_KF_ENCODING_AES_KEY=
"""

    assert module.validate_env_template(safe_env) == []

    unsafe_env = safe_env.replace("BAILIAN_API_KEY=", "BAILIAN_API_KEY=sk-test-not-real")
    errors = module.validate_env_template(unsafe_env)

    assert any("BAILIAN_API_KEY must be empty" in error for error in errors)
    assert any("possible secret fragment" in error for error in errors)


def test_compose_contract_requires_health_or_dependency_for_each_service() -> None:
    module = _load_script()

    base_compose = """
services:
  postgres:
    image: pgvector/pgvector:pg16
    healthcheck:
      test: ["CMD-SHELL", "pg_isready"]
  redis:
    image: redis:7-alpine
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
  backend:
    build:
      context: ../backend
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
  frontend:
    build:
      context: ../frontend
"""
    pilot_compose = """
services:
  backend:
    environment:
      OUTBOX_EXTERNAL_WRITE_ENABLED: "false"
  frontend:
    healthcheck:
      test:
        - CMD-SHELL
        - node -e "process.exit(0)"
volumes:
  standard_ops_pilot_postgres:
  standard_ops_pilot_redis:
"""

    assert module.validate_compose_contract(base_compose, pilot_compose) == []

    broken_base = base_compose.replace("    healthcheck:\n      test: [\"CMD\", \"redis-cli\", \"ping\"]\n", "")
    errors = module.validate_compose_contract(broken_base, pilot_compose)

    assert "docker compose service missing healthcheck or dependency: redis" in errors
