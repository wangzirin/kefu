from dataclasses import dataclass
import os

from app.core.config import Settings, get_settings
from app.services.channel_secret_store import (
    clear_local_connector_secrets,
    resolve_local_connector_secret_value,
    save_local_connector_secrets,
)


SILICONFLOW_PROVIDER = "siliconflow"
SILICONFLOW_BASE_URL = "https://api.siliconflow.cn/v1"
SILICONFLOW_EMBEDDING_MODEL = "BAAI/bge-large-zh-v1.5"
SILICONFLOW_RERANKER_MODEL = "BAAI/bge-reranker-v2-m3"
SILICONFLOW_LLM_MODEL = "Qwen/Qwen3.5-4B"
SILICONFLOW_CREDENTIAL_REF = "local:model_service:siliconflow"


@dataclass(frozen=True)
class SiliconFlowModelServiceConfig:
    provider: str
    base_url: str
    api_key: str
    api_key_source: str
    api_key_configured: bool
    api_key_masked: str
    embedding_model: str
    reranker_model: str
    llm_model: str


def mask_secret(value: str) -> str:
    clean = value.strip()
    if not clean:
        return ""
    if len(clean) <= 8:
        return "****"
    return f"{clean[:4]}****{clean[-4:]}"


def get_siliconflow_model_service_config(settings: Settings | None = None) -> SiliconFlowModelServiceConfig:
    settings = settings or get_settings()
    env_key = settings.siliconflow_api_key or os.getenv("SILICONFLOW_API_KEY", "").strip()
    local_key = ""
    if not env_key:
        local_key = resolve_local_connector_secret_value(
            credential_ref=SILICONFLOW_CREDENTIAL_REF,
            secret_key="api_key",
        )
    api_key = env_key or local_key
    source = "env" if env_key else ("local_encrypted" if local_key else "")
    return SiliconFlowModelServiceConfig(
        provider=SILICONFLOW_PROVIDER,
        base_url=settings.siliconflow_api_base or SILICONFLOW_BASE_URL,
        api_key=api_key,
        api_key_source=source,
        api_key_configured=bool(api_key),
        api_key_masked=mask_secret(api_key),
        embedding_model=settings.siliconflow_embedding_model or SILICONFLOW_EMBEDDING_MODEL,
        reranker_model=settings.siliconflow_reranker_model or SILICONFLOW_RERANKER_MODEL,
        llm_model=settings.siliconflow_llm_model or SILICONFLOW_LLM_MODEL,
    )


def save_siliconflow_api_key(api_key: str) -> None:
    save_local_connector_secrets(
        credential_ref=SILICONFLOW_CREDENTIAL_REF,
        secrets={"api_key": api_key.strip()},
    )


def clear_siliconflow_api_key() -> None:
    clear_local_connector_secrets(credential_ref=SILICONFLOW_CREDENTIAL_REF)
