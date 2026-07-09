from datetime import datetime

from pydantic import BaseModel, Field


class AiServiceStatusRead(BaseModel):
    tenant_id: int
    status: str
    label: str
    default_provider: str
    default_model: str
    configured: bool
    fallback_available: bool
    customer_visible_detail: str
    generated_at: datetime
    secret_included: bool = False


class ModelServiceProviderRead(BaseModel):
    key: str
    label: str
    base_url: str
    api_key_configured: bool
    api_key_masked: str
    api_key_source: str
    embedding_model: str
    reranker_model: str
    llm_model: str
    secret_included: bool = False


class ModelServiceConfigRead(BaseModel):
    tenant_id: int
    provider: ModelServiceProviderRead
    generated_at: datetime


class ModelServiceConfigUpdate(BaseModel):
    api_key: str = Field(min_length=8, max_length=300)


class ModelServiceProbeResult(BaseModel):
    name: str
    model: str
    endpoint: str
    status: str
    latency_ms: int
    error_message: str = ""


class ModelServiceProbeRead(BaseModel):
    tenant_id: int
    provider: str
    status: str
    results: list[ModelServiceProbeResult]
    generated_at: datetime
    secret_included: bool = False
