from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.auth import CurrentPrincipal
from app.core.rbac import require_permission
from app.schemas.rpa_copilot import RpaCopilotDryRunRequest, RpaCopilotDryRunResponse
from app.services.rpa_copilot import run_rpa_copilot_strategy_dry_run


router = APIRouter(prefix="/api", tags=["rpa-copilot"])

CONVERSATION_READ_PERMISSION = "conversation.read"


@router.post(
    "/rpa-copilot/strategy-dry-run",
    response_model=RpaCopilotDryRunResponse,
)
def create_rpa_copilot_strategy_dry_run(
    payload: RpaCopilotDryRunRequest,
    principal: CurrentPrincipal = Depends(require_permission(CONVERSATION_READ_PERMISSION)),
) -> RpaCopilotDryRunResponse:
    return run_rpa_copilot_strategy_dry_run(payload, principal)
