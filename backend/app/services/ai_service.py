from app.core.auth import CurrentPrincipal
from app.core.config import get_settings
from app.models.foundation import utc_now
from app.schemas.ai_service import AiServiceStatusRead


def get_ai_service_status(tenant_id: int, principal: CurrentPrincipal) -> AiServiceStatusRead:
    if tenant_id != principal.tenant.id:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="tenant not found")
    settings = get_settings()
    configured = bool(settings.bailian_api_key)
    status = "ready" if configured else "not_configured"
    label = "AI 服务正常" if configured else "AI 服务未配置"
    return AiServiceStatusRead(
        tenant_id=tenant_id,
        status=status,
        label=label,
        default_provider="bailian",
        default_model=settings.bailian_model,
        configured=configured,
        fallback_available=True,
        customer_visible_detail=label if configured else "AI 服务暂未配置，系统会转人工处理。",
        generated_at=utc_now(),
        secret_included=False,
    )

