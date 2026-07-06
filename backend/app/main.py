from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import (
    accounts,
    audit,
    auth,
    channel_connectors,
    conversations,
    customer_profiles,
    delivery_failures,
    diagnostics,
    health,
    inbound_worker,
    knowledge,
    local_backups,
    ops,
    outbox,
    pilot,
    reply_decisions,
    reply_strategies,
    reply_orchestrator,
    rpa_copilot,
    signed_updates,
    support_tickets,
    tenants,
    workflows,
    worker_heartbeats,
)
from app.core.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        docs_url="/api/docs",
        openapi_url="/api/openapi.json",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.allowed_origins),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(accounts.router)
    app.include_router(audit.router)
    app.include_router(tenants.router)
    app.include_router(conversations.router)
    app.include_router(customer_profiles.router)
    app.include_router(workflows.router)
    app.include_router(worker_heartbeats.router)
    app.include_router(ops.router)
    app.include_router(outbox.router)
    app.include_router(pilot.router)
    app.include_router(reply_decisions.router)
    app.include_router(reply_strategies.router)
    app.include_router(channel_connectors.router)
    app.include_router(delivery_failures.router)
    app.include_router(diagnostics.router)
    app.include_router(inbound_worker.router)
    app.include_router(reply_orchestrator.router)
    app.include_router(rpa_copilot.router)
    app.include_router(knowledge.router)
    app.include_router(local_backups.router)
    app.include_router(signed_updates.router)
    app.include_router(support_tickets.router)
    return app


app = create_app()
