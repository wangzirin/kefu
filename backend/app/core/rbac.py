from __future__ import annotations

from fastapi import Depends, HTTPException, status

from app.core.auth import CurrentPrincipal, require_current_principal


ROLE_PERMISSIONS: dict[str, set[str]] = {
    "owner": {
        "dashboard.read",
        "quality.read",
        "ops.worker_health.read",
        "ops.alert_rules.read",
        "ops.metrics.read",
        "updates.manage",
        "audit.events.read",
        "accounts.manage",
        "knowledge.read",
        "knowledge.manage",
        "conversation.read",
        "conversation.manage",
        "ticket.read",
        "ticket.manage",
        "customer.read",
        "customer.manage",
        "lead.read",
        "lead.manage",
        "channel.read",
        "channel.manage",
        "channel.connector.manage",
        "channel.delivery_receipt.read",
        "channel.delivery_receipt.manage",
        "outbox.draft.read",
        "outbox.draft.manage",
        "outbox.send_attempt.read",
        "outbox.send_attempt.manage",
        "outbox.send_plan.manage",
        "outbox.delivery_job.read",
        "outbox.delivery_job.manage",
        "outbox.failure_review.read",
        "outbox.failure_review.manage",
    },
    "admin": {
        "dashboard.read",
        "quality.read",
        "ops.worker_health.read",
        "ops.alert_rules.read",
        "ops.metrics.read",
        "updates.manage",
        "audit.events.read",
        "knowledge.read",
        "knowledge.manage",
        "conversation.read",
        "conversation.manage",
        "ticket.read",
        "ticket.manage",
        "customer.read",
        "customer.manage",
        "lead.read",
        "lead.manage",
        "channel.read",
        "channel.manage",
        "channel.connector.manage",
        "channel.delivery_receipt.read",
        "channel.delivery_receipt.manage",
        "outbox.draft.read",
        "outbox.draft.manage",
        "outbox.send_attempt.read",
        "outbox.send_attempt.manage",
        "outbox.send_plan.manage",
        "outbox.delivery_job.read",
        "outbox.delivery_job.manage",
        "outbox.failure_review.read",
        "outbox.failure_review.manage",
    },
    "agent": {
        "conversation.read",
        "conversation.manage",
        "knowledge.read",
        "ticket.read",
        "ticket.manage",
        "customer.read",
        "customer.manage",
        "lead.read",
        "lead.manage",
        "channel.read",
        "channel.delivery_receipt.read",
        "outbox.draft.read",
        "outbox.draft.manage",
        "outbox.send_attempt.read",
        "outbox.send_attempt.manage",
        "outbox.send_plan.manage",
        "outbox.delivery_job.read",
        "outbox.failure_review.read",
        "outbox.failure_review.manage",
    },
    "viewer": {
        "dashboard.read",
        "quality.read",
        "channel.read",
        "outbox.failure_review.read",
    },
}


def permissions_for_roles(roles: list[str]) -> set[str]:
    permissions: set[str] = set()
    for role in roles:
        permissions.update(ROLE_PERMISSIONS.get(role, set()))
    return permissions


def principal_has_permission(principal: CurrentPrincipal, permission: str) -> bool:
    return permission in permissions_for_roles(principal.roles)


def allowed_roles_for_permission(permission: str) -> tuple[str, ...]:
    return tuple(
        sorted(
            role
            for role, permissions in ROLE_PERMISSIONS.items()
            if permission in permissions
        )
    )


def require_permission(permission: str):
    def dependency(
        principal: CurrentPrincipal = Depends(require_current_principal),
    ) -> CurrentPrincipal:
        if not principal_has_permission(principal, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="insufficient permission",
            )
        return principal

    return dependency
