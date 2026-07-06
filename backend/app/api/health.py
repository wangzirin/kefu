from fastapi import APIRouter

from app.core.config import get_settings

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict:
    settings = get_settings()
    return {
        "status": "ok",
        "service": "standard_ops_backend",
        "environment": settings.env,
    }


@router.get("/api/health")
def api_health() -> dict:
    return health()
