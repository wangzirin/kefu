from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
import sys

from app.core.auth import CurrentPrincipal
from app.schemas.rpa_copilot import RpaCopilotDryRunRequest, RpaCopilotDryRunResponse


RESEARCH_DIR = Path(__file__).resolve().parents[3] / "research" / "ai_rpa_closed_loop"
if str(RESEARCH_DIR) not in sys.path:
    sys.path.insert(0, str(RESEARCH_DIR))

from ai_rpa_closed_loop import ChannelMessage, build_default_engine, result_to_dict  # noqa: E402


def run_rpa_copilot_strategy_dry_run(
    payload: RpaCopilotDryRunRequest,
    principal: CurrentPrincipal,
) -> RpaCopilotDryRunResponse:
    message = ChannelMessage(
        message_id=f"manual-{principal.tenant.id}-{principal.user.id}",
        channel=payload.channel,
        customer_name=payload.customer_name,
        text=payload.text,
        received_at=datetime.now(timezone.utc).isoformat(),
        attachments=list(payload.attachments),
        metadata={
            **payload.metadata,
            "tenant_id": str(principal.tenant.id),
            "operator_user_id": str(principal.user.id),
            "import_mode": "manual_paste",
        },
    )
    result = build_default_engine().handle(message)
    result_payload = result_to_dict(result)
    result_payload["audit"] = {
        **result_payload["audit"],
        "tenant_id": principal.tenant.id,
        "operator_user_id": principal.user.id,
        "entrypoint": "rpa_copilot_lab",
        "manual_import_only": True,
        "persisted_to_database": False,
        "external_write_performed": False,
        "auto_send_enabled": False,
    }
    for action in result.actions:
        if action.external_write:
            raise RuntimeError(f"RPA copilot dry-run produced external write action: {asdict(action)}")
    return RpaCopilotDryRunResponse(
        tenant_id=principal.tenant.id,
        operator_user_id=principal.user.id,
        mode="research_dry_run",
        **result_payload,
    )
