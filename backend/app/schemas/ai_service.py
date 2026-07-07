from datetime import datetime

from pydantic import BaseModel


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

