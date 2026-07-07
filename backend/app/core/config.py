from dataclasses import dataclass
import os
from typing import Tuple


def _split_origins(value: str) -> Tuple[str, ...]:
    origins = [item.strip() for item in value.split(",") if item.strip()]
    return tuple(
        origins
        or [
            "http://127.0.0.1:5173",
            "http://localhost:5173",
            "http://127.0.0.1:5174",
            "http://localhost:5174",
            "http://127.0.0.1:5188",
            "http://localhost:5188",
            "null",
        ]
    )


@dataclass(frozen=True)
class Settings:
    app_name: str
    env: str
    database_url: str
    redis_url: str
    allowed_origins: Tuple[str, ...]
    bailian_api_base: str
    bailian_api_key: str
    bailian_model: str
    bailian_fast_model: str
    bailian_standard_model: str
    bailian_premium_model: str
    deepseek_api_base: str
    deepseek_api_key: str
    deepseek_model: str
    deepseek_fallback_model: str
    model_http_timeout_seconds: float
    model_budget_guard_enabled: bool
    model_budget_daily_limit_cny: float
    model_budget_monthly_limit_cny: float
    model_budget_single_call_limit_cny: float
    model_budget_cost_currency: str
    model_budget_pricing_source: str
    model_budget_price_table_version: str
    model_price_bailian_fast_per_1k_units: float
    model_price_bailian_standard_per_1k_units: float
    model_price_bailian_premium_per_1k_units: float
    model_price_deepseek_per_1k_units: float
    model_price_deterministic_per_1k_units: float
    knowledge_embedding_provider: str
    knowledge_embedding_api_base: str
    knowledge_embedding_api_key: str
    knowledge_embedding_model: str
    knowledge_embedding_dimensions: int
    knowledge_embedding_price_per_1k_tokens: float
    knowledge_embedding_cost_currency: str
    knowledge_vector_store: str
    knowledge_reranker: str
    outbox_worker_batch_size: int
    outbox_worker_rate_limit_per_minute: int
    outbox_worker_max_attempts: int
    outbox_external_write_enabled: bool
    trusted_inbound_worker_enabled: bool
    trusted_inbound_worker_tenant_slug: str
    trusted_inbound_worker_user_email: str
    trusted_inbound_worker_id: str
    trusted_inbound_worker_sleep_seconds: float
    trusted_inbound_worker_batch_size: int
    trusted_inbound_worker_rate_limit_per_minute: int
    trusted_inbound_worker_lease_seconds: int
    trusted_inbound_worker_heartbeat_stale_after_seconds: int
    dev_bootstrap_enabled: bool
    signed_update_trusted_public_keys_json: str
    local_backup_dir: str


def get_settings() -> Settings:
    return Settings(
        app_name=os.getenv(
            "STANDARD_OPS_APP_NAME", "Wanfa Customer Service Standard Ops"
        ),
        env=os.getenv("STANDARD_OPS_ENV", "development"),
        database_url=os.getenv(
            "DATABASE_URL",
            "postgresql+psycopg://wanfa_ops:wanfa_ops_password@localhost:5432/wanfa_ops",
        ),
        redis_url=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
        allowed_origins=_split_origins(
            os.getenv(
                "STANDARD_OPS_ALLOWED_ORIGINS",
                "http://127.0.0.1:5173,http://localhost:5173,"
                "http://127.0.0.1:5174,http://localhost:5174,"
                "http://127.0.0.1:5188,http://localhost:5188,null",
            )
        ),
        bailian_api_base=os.getenv("BAILIAN_API_BASE", "https://dashscope.aliyuncs.com/compatible-mode/v1"),
        bailian_api_key=os.getenv("BAILIAN_API_KEY", ""),
        bailian_model=os.getenv("BAILIAN_MODEL", "qwen-plus"),
        bailian_fast_model=os.getenv("BAILIAN_FAST_MODEL", "qwen3.6-flash"),
        bailian_standard_model=os.getenv("BAILIAN_STANDARD_MODEL", "qwen3.7-plus"),
        bailian_premium_model=os.getenv("BAILIAN_PREMIUM_MODEL", "qwen3.7-max"),
        deepseek_api_base=os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com"),
        deepseek_api_key=os.getenv("DEEPSEEK_API_KEY", ""),
        deepseek_model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
        deepseek_fallback_model=os.getenv("DEEPSEEK_FALLBACK_MODEL", "deepseek-v4-flash"),
        model_http_timeout_seconds=float(os.getenv("MODEL_HTTP_TIMEOUT_SECONDS", "20")),
        model_budget_guard_enabled=os.getenv("MODEL_BUDGET_GUARD_ENABLED", "true").strip().lower()
        in {"1", "true", "yes", "on"},
        model_budget_daily_limit_cny=float(os.getenv("MODEL_BUDGET_DAILY_LIMIT_CNY", "0")),
        model_budget_monthly_limit_cny=float(os.getenv("MODEL_BUDGET_MONTHLY_LIMIT_CNY", "0")),
        model_budget_single_call_limit_cny=float(os.getenv("MODEL_BUDGET_SINGLE_CALL_LIMIT_CNY", "0")),
        model_budget_cost_currency=os.getenv("MODEL_BUDGET_COST_CURRENCY", "CNY").strip() or "CNY",
        model_budget_pricing_source=os.getenv(
            "MODEL_BUDGET_PRICING_SOURCE",
            "operator_config_default_estimate_not_provider_bill",
        ).strip()
        or "operator_config_default_estimate_not_provider_bill",
        model_budget_price_table_version=os.getenv("MODEL_BUDGET_PRICE_TABLE_VERSION", "local-estimate-2026-07").strip()
        or "local-estimate-2026-07",
        model_price_bailian_fast_per_1k_units=float(os.getenv("MODEL_PRICE_BAILIAN_FAST_PER_1K_UNITS", "0.001")),
        model_price_bailian_standard_per_1k_units=float(os.getenv("MODEL_PRICE_BAILIAN_STANDARD_PER_1K_UNITS", "0.004")),
        model_price_bailian_premium_per_1k_units=float(os.getenv("MODEL_PRICE_BAILIAN_PREMIUM_PER_1K_UNITS", "0.02")),
        model_price_deepseek_per_1k_units=float(os.getenv("MODEL_PRICE_DEEPSEEK_PER_1K_UNITS", "0.004")),
        model_price_deterministic_per_1k_units=float(os.getenv("MODEL_PRICE_DETERMINISTIC_PER_1K_UNITS", "0")),
        knowledge_embedding_provider=os.getenv("KNOWLEDGE_EMBEDDING_PROVIDER", "deterministic_local").strip(),
        knowledge_embedding_api_base=os.getenv("KNOWLEDGE_EMBEDDING_API_BASE", "").strip(),
        knowledge_embedding_api_key=os.getenv("KNOWLEDGE_EMBEDDING_API_KEY", "").strip(),
        knowledge_embedding_model=os.getenv("KNOWLEDGE_EMBEDDING_MODEL", "deterministic-token-vector-v1").strip(),
        knowledge_embedding_dimensions=int(os.getenv("KNOWLEDGE_EMBEDDING_DIMENSIONS", "64")),
        knowledge_embedding_price_per_1k_tokens=float(os.getenv("KNOWLEDGE_EMBEDDING_PRICE_PER_1K_TOKENS", "0")),
        knowledge_embedding_cost_currency=os.getenv("KNOWLEDGE_EMBEDDING_COST_CURRENCY", "CNY").strip() or "CNY",
        knowledge_vector_store=os.getenv("KNOWLEDGE_VECTOR_STORE", "sqlite_json_vector_store").strip(),
        knowledge_reranker=os.getenv("KNOWLEDGE_RERANKER", "lexical_overlap_reranker_v1").strip(),
        outbox_worker_batch_size=int(os.getenv("OUTBOX_WORKER_BATCH_SIZE", "20")),
        outbox_worker_rate_limit_per_minute=int(os.getenv("OUTBOX_WORKER_RATE_LIMIT_PER_MINUTE", "60")),
        outbox_worker_max_attempts=int(os.getenv("OUTBOX_WORKER_MAX_ATTEMPTS", "3")),
        outbox_external_write_enabled=os.getenv("OUTBOX_EXTERNAL_WRITE_ENABLED", "false").strip().lower()
        in {"1", "true", "yes", "on"},
        trusted_inbound_worker_enabled=os.getenv("TRUSTED_INBOUND_WORKER_ENABLED", "false").strip().lower()
        in {"1", "true", "yes", "on"},
        trusted_inbound_worker_tenant_slug=os.getenv("TRUSTED_INBOUND_WORKER_TENANT_SLUG", "").strip(),
        trusted_inbound_worker_user_email=os.getenv("TRUSTED_INBOUND_WORKER_USER_EMAIL", "").strip(),
        trusted_inbound_worker_id=os.getenv("TRUSTED_INBOUND_WORKER_ID", "trusted-inbound-worker-1").strip()
        or "trusted-inbound-worker-1",
        trusted_inbound_worker_sleep_seconds=float(os.getenv("TRUSTED_INBOUND_WORKER_SLEEP_SECONDS", "5")),
        trusted_inbound_worker_batch_size=int(os.getenv("TRUSTED_INBOUND_WORKER_BATCH_SIZE", "20")),
        trusted_inbound_worker_rate_limit_per_minute=int(
            os.getenv("TRUSTED_INBOUND_WORKER_RATE_LIMIT_PER_MINUTE", "60")
        ),
        trusted_inbound_worker_lease_seconds=int(os.getenv("TRUSTED_INBOUND_WORKER_LEASE_SECONDS", "60")),
        trusted_inbound_worker_heartbeat_stale_after_seconds=int(
            os.getenv("TRUSTED_INBOUND_WORKER_HEARTBEAT_STALE_AFTER_SECONDS", "180")
        ),
        dev_bootstrap_enabled=os.getenv(
            "STANDARD_OPS_DEV_BOOTSTRAP_ENABLED",
            "true" if os.getenv("STANDARD_OPS_ENV", "development").strip().lower() == "development" else "false",
        ).strip().lower()
        in {"1", "true", "yes", "on"},
        signed_update_trusted_public_keys_json=os.getenv("WANFA_UPDATE_TRUSTED_PUBLIC_KEYS_JSON", "").strip(),
        local_backup_dir=os.getenv("WANFA_LOCAL_BACKUP_DIR", "data/local_backups").strip() or "data/local_backups",
    )
