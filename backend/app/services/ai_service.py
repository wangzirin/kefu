import json
from time import perf_counter
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from fastapi import HTTPException, status

from app.core.auth import CurrentPrincipal
from app.core.config import get_settings
from app.models.foundation import utc_now
from app.schemas.ai_service import (
    AiServiceStatusRead,
    ModelServiceConfigRead,
    ModelServiceConfigUpdate,
    ModelServiceProbeRead,
    ModelServiceProbeResult,
    ModelServiceProviderRead,
)
from app.services.model_service_config import (
    SILICONFLOW_PROVIDER,
    clear_siliconflow_api_key,
    get_siliconflow_model_service_config,
    save_siliconflow_api_key,
)


def get_ai_service_status(tenant_id: int, principal: CurrentPrincipal) -> AiServiceStatusRead:
    if tenant_id != principal.tenant.id:
        raise HTTPException(status_code=404, detail="tenant not found")
    settings = get_settings()
    siliconflow = get_siliconflow_model_service_config(settings)
    configured = siliconflow.api_key_configured or bool(settings.bailian_api_key)
    status = "ready" if configured else "not_configured"
    label = "AI 服务正常" if configured else "AI 服务未配置"
    return AiServiceStatusRead(
        tenant_id=tenant_id,
        status=status,
        label=label,
        default_provider=SILICONFLOW_PROVIDER if siliconflow.api_key_configured else "bailian",
        default_model=siliconflow.llm_model if siliconflow.api_key_configured else settings.bailian_model,
        configured=configured,
        fallback_available=True,
        customer_visible_detail=label if configured else "AI 服务暂未配置，系统会转人工处理。",
        generated_at=utc_now(),
        secret_included=False,
    )


def _require_same_tenant(tenant_id: int, principal: CurrentPrincipal) -> None:
    if tenant_id != principal.tenant.id:
        raise HTTPException(status_code=404, detail="tenant not found")


def get_model_service_config(tenant_id: int, principal: CurrentPrincipal) -> ModelServiceConfigRead:
    _require_same_tenant(tenant_id, principal)
    siliconflow = get_siliconflow_model_service_config()
    return ModelServiceConfigRead(
        tenant_id=tenant_id,
        provider=ModelServiceProviderRead(
            key=SILICONFLOW_PROVIDER,
            label="硅基流动",
            base_url=siliconflow.base_url,
            api_key_configured=siliconflow.api_key_configured,
            api_key_masked=siliconflow.api_key_masked,
            api_key_source=siliconflow.api_key_source,
            embedding_model=siliconflow.embedding_model,
            reranker_model=siliconflow.reranker_model,
            llm_model=siliconflow.llm_model,
            secret_included=False,
        ),
        generated_at=utc_now(),
    )


def update_model_service_config(
    tenant_id: int,
    payload: ModelServiceConfigUpdate,
    principal: CurrentPrincipal,
) -> ModelServiceConfigRead:
    _require_same_tenant(tenant_id, principal)
    save_siliconflow_api_key(payload.api_key)
    return get_model_service_config(tenant_id, principal)


def clear_model_service_config(tenant_id: int, principal: CurrentPrincipal) -> ModelServiceConfigRead:
    _require_same_tenant(tenant_id, principal)
    clear_siliconflow_api_key()
    return get_model_service_config(tenant_id, principal)


def _post_probe(*, name: str, model: str, endpoint: str, api_key: str, payload: dict) -> ModelServiceProbeResult:
    started_at = perf_counter()
    request = Request(
        endpoint,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=get_settings().model_http_timeout_seconds) as response:
            response.read()
        return ModelServiceProbeResult(
            name=name,
            model=model,
            endpoint=endpoint,
            status="succeeded",
            latency_ms=max(0, int((perf_counter() - started_at) * 1000)),
        )
    except HTTPError as exc:
        error_message = f"HTTP {exc.code}"
    except (URLError, TimeoutError, ValueError, json.JSONDecodeError) as exc:
        error_message = str(exc)[:300]
    return ModelServiceProbeResult(
        name=name,
        model=model,
        endpoint=endpoint,
        status="failed",
        latency_ms=max(0, int((perf_counter() - started_at) * 1000)),
        error_message=error_message,
    )


def probe_model_service(tenant_id: int, principal: CurrentPrincipal) -> ModelServiceProbeRead:
    _require_same_tenant(tenant_id, principal)
    siliconflow = get_siliconflow_model_service_config()
    if not siliconflow.api_key_configured:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="SiliconFlow API key is not configured")
    base_url = siliconflow.base_url.rstrip("/")
    results = [
        _post_probe(
            name="embedding",
            model=siliconflow.embedding_model,
            endpoint=base_url + "/embeddings",
            api_key=siliconflow.api_key,
            payload={"model": siliconflow.embedding_model, "input": "你好"},
        ),
        _post_probe(
            name="reranker",
            model=siliconflow.reranker_model,
            endpoint=base_url + "/rerank",
            api_key=siliconflow.api_key,
            payload={"model": siliconflow.reranker_model, "query": "价格", "documents": ["价格请咨询客服", "售后规则"]},
        ),
        _post_probe(
            name="llm",
            model=siliconflow.llm_model,
            endpoint=base_url + "/chat/completions",
            api_key=siliconflow.api_key,
            payload={
                "model": siliconflow.llm_model,
                "messages": [{"role": "user", "content": "请回复：模型连通性测试"}],
                "temperature": 0.1,
                "enable_thinking": False,
                "max_tokens": 32,
            },
        ),
    ]
    overall = "succeeded" if all(item.status == "succeeded" for item in results) else "failed"
    return ModelServiceProbeRead(
        tenant_id=tenant_id,
        provider=SILICONFLOW_PROVIDER,
        status=overall,
        results=results,
        generated_at=utc_now(),
        secret_included=False,
    )
