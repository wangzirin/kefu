from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Tenant(Base):
    __tablename__ = "tenants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    slug: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    plan: Mapped[str] = mapped_column(String(40), nullable=False, default="standard_ops")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    users: Mapped[list["User"]] = relationship(back_populates="tenant")


class User(Base):
    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("tenant_id", "email", name="uq_users_tenant_id_email"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    avatar_data_url: Mapped[str] = mapped_column(Text, nullable=False, default="")
    public_profile: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    personal_settings: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    tenant: Mapped[Tenant] = relationship(back_populates="users")


class Role(Base):
    __tablename__ = "roles"
    __table_args__ = (UniqueConstraint("tenant_id", "code", name="uq_roles_tenant_id_code"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    code: Mapped[str] = mapped_column(String(60), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class UserRole(Base):
    __tablename__ = "user_roles"
    __table_args__ = (UniqueConstraint("user_id", "role_id", name="uq_user_roles_user_id_role_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class AuthSession(Base):
    __tablename__ = "auth_sessions"
    __table_args__ = (UniqueConstraint("token_hash", name="uq_auth_sessions_token_hash"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class Team(Base):
    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class TeamMember(Base):
    __tablename__ = "team_members"
    __table_args__ = (UniqueConstraint("team_id", "user_id", name="uq_team_members_team_id_user_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    role_in_team: Mapped[str] = mapped_column(String(60), nullable=False, default="agent")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class Channel(Base):
    __tablename__ = "channels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    type: Mapped[str] = mapped_column(String(40), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    reply_mode: Mapped[str] = mapped_column(String(32), nullable=False, default="assist")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="planned")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class ChannelConnector(Base):
    __tablename__ = "channel_connectors"
    __table_args__ = (UniqueConstraint("tenant_id", "channel_id", name="uq_channel_connectors_tenant_id_channel_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    channel_id: Mapped[int] = mapped_column(ForeignKey("channels.id"), nullable=False)
    provider: Mapped[str] = mapped_column(String(80), nullable=False)
    mode: Mapped[str] = mapped_column(String(32), nullable=False, default="noop")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="draft")
    display_name: Mapped[str] = mapped_column(String(160), nullable=False, default="")
    capabilities: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    public_config: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    webhook_path: Mapped[str] = mapped_column(String(300), nullable=False, default="")
    signature_mode: Mapped[str] = mapped_column(String(80), nullable=False, default="not_configured")
    secret_status: Mapped[str] = mapped_column(String(40), nullable=False, default="not_configured")
    external_write_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    updated_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class ChannelAccount(Base):
    __tablename__ = "channel_accounts"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "channel_id",
            "account_name",
            "entrypoint_name",
            name="uq_channel_accounts_tenant_channel_account_entrypoint",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    channel_id: Mapped[int] = mapped_column(ForeignKey("channels.id"), nullable=False)
    connector_id: Mapped[int | None] = mapped_column(ForeignKey("channel_connectors.id"), nullable=True)
    provider: Mapped[str] = mapped_column(String(80), nullable=False, default="")
    platform: Mapped[str] = mapped_column(String(80), nullable=False, default="")
    account_name: Mapped[str] = mapped_column(String(160), nullable=False, default="")
    external_account_id: Mapped[str] = mapped_column(String(180), nullable=False, default="")
    store_name: Mapped[str] = mapped_column(String(160), nullable=False, default="")
    entrypoint_name: Mapped[str] = mapped_column(String(160), nullable=False, default="")
    authorization_status: Mapped[str] = mapped_column(String(40), nullable=False, default="not_configured")
    access_status: Mapped[str] = mapped_column(String(40), nullable=False, default="planned")
    reply_mode: Mapped[str] = mapped_column(String(40), nullable=False, default="draft_only")
    health_status: Mapped[str] = mapped_column(String(40), nullable=False, default="unknown")
    public_profile: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    updated_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class Contact(Base):
    __tablename__ = "contacts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    phone: Mapped[str] = mapped_column(String(40), nullable=False, default="")
    wechat: Mapped[str] = mapped_column(String(80), nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    channel_id: Mapped[int] = mapped_column(ForeignKey("channels.id"), nullable=False)
    contact_id: Mapped[int] = mapped_column(ForeignKey("contacts.id"), nullable=False)
    assigned_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    assigned_team_id: Mapped[int | None] = mapped_column(ForeignKey("teams.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="bot")
    priority: Mapped[str] = mapped_column(String(32), nullable=False, default="normal")
    subject: Mapped[str] = mapped_column(String(180), nullable=False, default="")
    last_message_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    messages: Mapped[list["Message"]] = relationship(back_populates="conversation")


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("conversations.id"), nullable=False)
    direction: Mapped[str] = mapped_column(String(16), nullable=False)
    sender_type: Mapped[str] = mapped_column(String(32), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    external_message_id: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    conversation: Mapped[Conversation] = relationship(back_populates="messages")


class ConversationEvent(Base):
    __tablename__ = "conversation_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("conversations.id"), nullable=False)
    event_type: Mapped[str] = mapped_column(String(80), nullable=False)
    actor_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    payload: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class PilotReadinessFact(Base):
    __tablename__ = "pilot_readiness_facts"
    __table_args__ = (
        UniqueConstraint("tenant_id", "fact_key", name="uq_pilot_readiness_facts_tenant_key"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    fact_key: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[str] = mapped_column(String(80), nullable=False)
    source: Mapped[str] = mapped_column(String(80), nullable=False, default="database")
    evidence_path: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    not_ready_for: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    created_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class CustomerMaterialBatch(Base):
    __tablename__ = "customer_material_batches"
    __table_args__ = (
        UniqueConstraint("tenant_id", "batch_code", name="uq_customer_material_batches_tenant_code"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    batch_code: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[str] = mapped_column(String(80), nullable=False)
    material_sha256: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    question_sha256: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    manifest_sha256: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    material_row_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    question_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    record_type_coverage: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    question_action_coverage: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    blocker_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    desensitization_risk_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    manifest_summary: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class TrustedInboundWorkerRunRecord(Base):
    __tablename__ = "trusted_inbound_worker_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    worker_id: Mapped[str] = mapped_column(String(120), nullable=False, default="manual_api_worker")
    mode: Mapped[str] = mapped_column(String(80), nullable=False, default="trusted_inbound_orchestrator")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="running")
    batch_size: Mapped[int] = mapped_column(Integer, nullable=False, default=20)
    rate_limit_per_minute: Mapped[int] = mapped_column(Integer, nullable=False, default=60)
    lease_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=60)
    scanned: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    processed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    succeeded: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    skipped: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    rate_limited: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    external_write: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    request_payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    result_payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    error_message: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class TrustedInboundMessageJob(Base):
    __tablename__ = "trusted_inbound_message_jobs"
    __table_args__ = (
        UniqueConstraint("tenant_id", "message_id", name="uq_trusted_inbound_message_jobs_tenant_message"),
        UniqueConstraint("tenant_id", "idempotency_key", name="uq_trusted_inbound_message_jobs_tenant_key"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("conversations.id"), nullable=False)
    message_id: Mapped[int] = mapped_column(ForeignKey("messages.id"), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(180), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="queued")
    attempts_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    locked_by: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    locked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_run_record_id: Mapped[int | None] = mapped_column(ForeignKey("trusted_inbound_worker_runs.id"), nullable=True)
    workflow_run_id: Mapped[int | None] = mapped_column(ForeignKey("workflow_runs.id"), nullable=True)
    human_review_task_id: Mapped[int | None] = mapped_column(ForeignKey("human_review_tasks.id"), nullable=True)
    last_error: Mapped[str] = mapped_column(Text, nullable=False, default="")
    next_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class WorkerHeartbeat(Base):
    __tablename__ = "worker_heartbeats"
    __table_args__ = (
        UniqueConstraint("tenant_id", "worker_type", "worker_id", name="uq_worker_heartbeats_tenant_worker"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    worker_type: Mapped[str] = mapped_column(String(80), nullable=False)
    worker_id: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="starting")
    last_heartbeat_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    last_run_record_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_run_mode: Mapped[str] = mapped_column(String(80), nullable=False, default="")
    last_error: Mapped[str] = mapped_column(Text, nullable=False, default="")
    loops_completed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    metadata_payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class SupportTicket(Base):
    __tablename__ = "support_tickets"
    __table_args__ = (
        UniqueConstraint("tenant_id", "source_type", "source_ref", name="uq_support_tickets_tenant_source"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("conversations.id"), nullable=False)
    channel_id: Mapped[int] = mapped_column(ForeignKey("channels.id"), nullable=False)
    contact_id: Mapped[int] = mapped_column(ForeignKey("contacts.id"), nullable=False)
    subject: Mapped[str] = mapped_column(String(180), nullable=False, default="")
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="open")
    priority: Mapped[str] = mapped_column(String(32), nullable=False, default="normal")
    source_type: Mapped[str] = mapped_column(String(60), nullable=False, default="conversation")
    source_ref: Mapped[str] = mapped_column(String(180), nullable=False)
    assigned_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    assigned_team_id: Mapped[int | None] = mapped_column(ForeignKey("teams.id"), nullable=True)
    sla_target_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=240)
    sla_due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sla_status: Mapped[str] = mapped_column(String(32), nullable=False, default="ok")
    resolution_note: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    updated_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    resolved_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class SalesLead(Base):
    __tablename__ = "sales_leads"
    __table_args__ = (
        UniqueConstraint("tenant_id", "source_type", "source_ref", name="uq_sales_leads_tenant_source"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    contact_id: Mapped[int] = mapped_column(ForeignKey("contacts.id"), nullable=False)
    channel_id: Mapped[int] = mapped_column(ForeignKey("channels.id"), nullable=False)
    conversation_id: Mapped[int | None] = mapped_column(ForeignKey("conversations.id"), nullable=True)
    title: Mapped[str] = mapped_column(String(180), nullable=False, default="")
    summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    stage: Mapped[str] = mapped_column(String(32), nullable=False, default="new")
    intent_level: Mapped[str] = mapped_column(String(32), nullable=False, default="warm")
    expected_budget: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    next_step: Mapped[str] = mapped_column(Text, nullable=False, default="")
    owner_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    source_type: Mapped[str] = mapped_column(String(60), nullable=False, default="conversation")
    source_ref: Mapped[str] = mapped_column(String(180), nullable=False)
    created_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    updated_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    next_follow_up_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    actor_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(120), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(80), nullable=False)
    resource_id: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    payload: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class Tag(Base):
    __tablename__ = "tags"
    __table_args__ = (UniqueConstraint("tenant_id", "name", name="uq_tags_tenant_id_name"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    color: Mapped[str] = mapped_column(String(32), nullable=False, default="#1d6fdb")
    kind: Mapped[str] = mapped_column(String(40), nullable=False, default="conversation")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class ConversationTag(Base):
    __tablename__ = "conversation_tags"
    __table_args__ = (
        UniqueConstraint("conversation_id", "tag_id", name="uq_conversation_tags_conversation_id_tag_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("conversations.id"), nullable=False)
    tag_id: Mapped[int] = mapped_column(ForeignKey("tags.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class KnowledgeCard(Base):
    __tablename__ = "knowledge_cards"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(180), nullable=False)
    question: Mapped[str] = mapped_column(Text, nullable=False, default="")
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    source_type: Mapped[str] = mapped_column(String(40), nullable=False, default="manual")
    source_uri: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    tags: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    aliases: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="draft")
    created_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    updated_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class BusinessObject(Base):
    __tablename__ = "business_objects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    type: Mapped[str] = mapped_column(String(40), nullable=False)
    title: Mapped[str] = mapped_column(String(180), nullable=False)
    external_id: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    attrs_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    created_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    updated_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class BusinessObjectAlias(Base):
    __tablename__ = "business_object_aliases"
    __table_args__ = (
        UniqueConstraint(
            "business_object_id",
            "alias",
            "channel_scope",
            name="uq_business_object_aliases_object_alias_scope",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    business_object_id: Mapped[int] = mapped_column(ForeignKey("business_objects.id"), nullable=False)
    alias: Mapped[str] = mapped_column(String(180), nullable=False)
    channel_scope: Mapped[str] = mapped_column(String(80), nullable=False, default="all")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class ObjectKnowledgeCard(Base):
    __tablename__ = "object_knowledge_cards"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    business_object_id: Mapped[int] = mapped_column(ForeignKey("business_objects.id"), nullable=False)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    trigger_keywords: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    media_refs: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    scope: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    source: Mapped[str] = mapped_column(String(120), nullable=False, default="manual")
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    created_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    updated_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class ReplyDecision(Base):
    __tablename__ = "reply_decisions"
    __table_args__ = (
        UniqueConstraint("tenant_id", "idempotency_key", name="uq_reply_decisions_tenant_idempotency_key"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("conversations.id"), nullable=False)
    message_id: Mapped[int] = mapped_column(ForeignKey("messages.id"), nullable=False)
    channel_id: Mapped[int] = mapped_column(ForeignKey("channels.id"), nullable=False)
    business_object_id: Mapped[int | None] = mapped_column(ForeignKey("business_objects.id"), nullable=True)
    object_knowledge_card_id: Mapped[int | None] = mapped_column(ForeignKey("object_knowledge_cards.id"), nullable=True)
    workflow_run_id: Mapped[int | None] = mapped_column(ForeignKey("workflow_runs.id"), nullable=True)
    provenance_id: Mapped[str] = mapped_column(String(180), nullable=False, default="")
    state: Mapped[str] = mapped_column(String(40), nullable=False, default="manual_gate_required")
    reason: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    delivery_mode: Mapped[str] = mapped_column(String(40), nullable=False, default="draft_only")
    draft_reply: Mapped[str] = mapped_column(Text, nullable=False, default="")
    matched_terms: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    decision_payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    external_write_allowed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    idempotency_key: Mapped[str] = mapped_column(String(180), nullable=False)
    created_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class ModelCallRecord(Base):
    __tablename__ = "model_call_records"
    __table_args__ = (
        UniqueConstraint("tenant_id", "idempotency_key", name="uq_model_call_records_tenant_idempotency_key"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    channel_id: Mapped[int | None] = mapped_column(ForeignKey("channels.id"), nullable=True)
    conversation_id: Mapped[int | None] = mapped_column(ForeignKey("conversations.id"), nullable=True)
    message_id: Mapped[int | None] = mapped_column(ForeignKey("messages.id"), nullable=True)
    workflow_run_id: Mapped[int | None] = mapped_column(ForeignKey("workflow_runs.id"), nullable=True)
    reply_decision_id: Mapped[int | None] = mapped_column(ForeignKey("reply_decisions.id"), nullable=True)
    outbox_draft_id: Mapped[int | None] = mapped_column(ForeignKey("outbox_drafts.id"), nullable=True)
    evaluation_run_case_id: Mapped[int | None] = mapped_column(ForeignKey("knowledge_evaluation_run_cases.id"), nullable=True)
    provenance_id: Mapped[str] = mapped_column(String(180), nullable=False, default="")
    request_id: Mapped[str] = mapped_column(String(180), nullable=False, default="")
    idempotency_key: Mapped[str] = mapped_column(String(180), nullable=False)
    provider: Mapped[str] = mapped_column(String(80), nullable=False)
    model: Mapped[str] = mapped_column(String(160), nullable=False)
    route_name: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    target_model_tier: Mapped[str] = mapped_column(String(40), nullable=False, default="")
    complexity: Mapped[str] = mapped_column(String(40), nullable=False, default="")
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="")
    error_code: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    input_units: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    output_units: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_units: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    unit_type: Mapped[str] = mapped_column(String(20), nullable=False, default="chars")
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    estimated_cost: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    currency: Mapped[str] = mapped_column(String(20), nullable=False, default="CNY")
    pricing_source: Mapped[str] = mapped_column(String(160), nullable=False, default="")
    pricing_version: Mapped[str] = mapped_column(String(80), nullable=False, default="")
    budget_policy_snapshot: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    degrade_action: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    raw_text_logged: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    metadata_payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class ReplyCitationSnapshot(Base):
    __tablename__ = "reply_citation_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    provenance_id: Mapped[str] = mapped_column(String(180), nullable=False, default="")
    reply_decision_id: Mapped[int | None] = mapped_column(ForeignKey("reply_decisions.id"), nullable=True)
    workflow_run_id: Mapped[int | None] = mapped_column(ForeignKey("workflow_runs.id"), nullable=True)
    outbox_draft_id: Mapped[int | None] = mapped_column(ForeignKey("outbox_drafts.id"), nullable=True)
    evaluation_run_case_id: Mapped[int | None] = mapped_column(ForeignKey("knowledge_evaluation_run_cases.id"), nullable=True)
    source_kind: Mapped[str] = mapped_column(String(60), nullable=False, default="")
    knowledge_card_id: Mapped[int | None] = mapped_column(ForeignKey("knowledge_cards.id"), nullable=True)
    object_knowledge_card_id: Mapped[int | None] = mapped_column(ForeignKey("object_knowledge_cards.id"), nullable=True)
    document_id: Mapped[int | None] = mapped_column(ForeignKey("knowledge_documents.id"), nullable=True)
    document_chunk_id: Mapped[int | None] = mapped_column(ForeignKey("knowledge_document_chunks.id"), nullable=True)
    chunk_index: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source_version: Mapped[str] = mapped_column(String(80), nullable=False, default="")
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    source_uri: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    char_start: Mapped[int | None] = mapped_column(Integer, nullable=True)
    char_end: Mapped[int | None] = mapped_column(Integer, nullable=True)
    score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    no_citation_reason: Mapped[str] = mapped_column(Text, nullable=False, default="")
    citation_payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class KnowledgeImportBatch(Base):
    __tablename__ = "knowledge_import_batches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    source_file_ref: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    object_type: Mapped[str] = mapped_column(String(40), nullable=False, default="")
    row_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    valid_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="draft")
    result_payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class SignedUpdatePackage(Base):
    __tablename__ = "signed_update_packages"
    __table_args__ = (
        UniqueConstraint("tenant_id", "package_id", name="uq_signed_update_packages_tenant_package"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    package_id: Mapped[str] = mapped_column(String(160), nullable=False)
    package_name: Mapped[str] = mapped_column(String(180), nullable=False)
    package_type: Mapped[str] = mapped_column(String(40), nullable=False)
    package_version: Mapped[str] = mapped_column(String(80), nullable=False)
    current_app_version: Mapped[str] = mapped_column(String(80), nullable=False, default="")
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="staged")
    package_digest_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    package_payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    preflight_result: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    backup_plan: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    health_checks: Mapped[list[dict]] = mapped_column(JSON, nullable=False, default=list)
    can_apply_now: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    backup_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    backup_created: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    staged_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    staged_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    applied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str] = mapped_column(Text, nullable=False, default="")


class LocalBackupRecord(Base):
    __tablename__ = "local_backup_records"
    __table_args__ = (
        UniqueConstraint("tenant_id", "backup_id", name="uq_local_backup_records_tenant_backup"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    backup_id: Mapped[str] = mapped_column(String(160), nullable=False)
    backup_type: Mapped[str] = mapped_column(String(60), nullable=False, default="sqlite_database")
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="created")
    file_name: Mapped[str] = mapped_column(String(260), nullable=False)
    file_path: Mapped[str] = mapped_column(String(800), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    source_database_label: Mapped[str] = mapped_column(String(260), nullable=False, default="")
    source_database_hash: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    restore_mode: Mapped[str] = mapped_column(String(80), nullable=False, default="manual_rehearsal_only")
    manifest_payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str] = mapped_column(Text, nullable=False, default="")


class DiagnosticIntakeRecord(Base):
    __tablename__ = "diagnostic_intake_records"
    __table_args__ = (
        UniqueConstraint("tenant_id", "intake_id", name="uq_diagnostic_intake_records_tenant_intake"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    intake_id: Mapped[str] = mapped_column(String(180), nullable=False)
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="received")
    validation_status: Mapped[str] = mapped_column(String(40), nullable=False, default="passed")
    package_filename: Mapped[str] = mapped_column(String(260), nullable=False, default="")
    diagnostic_bundle_filename: Mapped[str] = mapped_column(String(260), nullable=False, default="")
    package_sha256: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    diagnostic_bundle_sha256: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    package_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    source_channel: Mapped[str] = mapped_column(String(80), nullable=False, default="manual_transfer")
    rejection_reason: Mapped[str] = mapped_column(Text, nullable=False, default="")
    processing_note: Mapped[str] = mapped_column(Text, nullable=False, default="")
    authorization_summary: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    safety: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    package_payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    received_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    handled_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    handled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class DiagnosticRemediationRequest(Base):
    __tablename__ = "diagnostic_remediation_requests"
    __table_args__ = (
        UniqueConstraint("tenant_id", "request_id", name="uq_diagnostic_remediation_requests_tenant_request"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    intake_record_id: Mapped[int] = mapped_column(ForeignKey("diagnostic_intake_records.id"), nullable=False)
    request_id: Mapped[str] = mapped_column(String(180), nullable=False)
    request_type: Mapped[str] = mapped_column(String(60), nullable=False, default="knowledge_or_strategy_update")
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="draft")
    priority: Mapped[str] = mapped_column(String(30), nullable=False, default="normal")
    title: Mapped[str] = mapped_column(String(220), nullable=False, default="")
    summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    recommended_actions: Mapped[list[dict]] = mapped_column(JSON, nullable=False, default=list)
    update_request_manifest: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    safety: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    updated_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class TenantReplyStrategy(Base):
    __tablename__ = "tenant_reply_strategies"
    __table_args__ = (
        UniqueConstraint("tenant_id", name="uq_tenant_reply_strategies_tenant"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    strategy_id: Mapped[str] = mapped_column(String(160), nullable=False, default="")
    strategy_version: Mapped[str] = mapped_column(String(80), nullable=False, default="")
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="active")
    strategy_payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    previous_strategy_payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    signed_update_package_id: Mapped[int | None] = mapped_column(ForeignKey("signed_update_packages.id"), nullable=True)
    updated_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(180), nullable=False)
    source_type: Mapped[str] = mapped_column(String(40), nullable=False, default="manual_document")
    source_uri: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(80), nullable=False, default="")
    tags: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="draft")
    ingestion_status: Mapped[str] = mapped_column(String(40), nullable=False, default="indexed")
    chunk_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    updated_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class KnowledgeDocumentChunk(Base):
    __tablename__ = "knowledge_document_chunks"
    __table_args__ = (
        UniqueConstraint("document_id", "chunk_index", name="uq_knowledge_document_chunks_document_id_chunk_index"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    document_id: Mapped[int] = mapped_column(ForeignKey("knowledge_documents.id"), nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    section_title: Mapped[str] = mapped_column(String(180), nullable=False, default="")
    page_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(80), nullable=False, default="")
    source_uri: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    char_start: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    char_end: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    token_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    embedding_signature: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    embedding_vector: Mapped[list[float]] = mapped_column(JSON, nullable=False, default=list)
    embedding_provider: Mapped[str] = mapped_column(String(80), nullable=False, default="deterministic_local")
    embedding_model: Mapped[str] = mapped_column(String(120), nullable=False, default="deterministic-token-vector-v1")
    embedding_dimension: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    vector_store: Mapped[str] = mapped_column(String(80), nullable=False, default="sqlite_json_vector_store")
    vector_index_status: Mapped[str] = mapped_column(String(40), nullable=False, default="indexed")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class KnowledgeDocumentPublication(Base):
    __tablename__ = "knowledge_document_publications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    document_id: Mapped[int] = mapped_column(ForeignKey("knowledge_documents.id"), nullable=False)
    gap_id: Mapped[int | None] = mapped_column(ForeignKey("knowledge_gaps.id"), nullable=True)
    publication_type: Mapped[str] = mapped_column(String(40), nullable=False, default="publish_check")
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="passed")
    from_status: Mapped[str] = mapped_column(String(32), nullable=False, default="")
    to_status: Mapped[str] = mapped_column(String(32), nullable=False, default="")
    evaluation_set_id: Mapped[int | None] = mapped_column(ForeignKey("knowledge_evaluation_sets.id"), nullable=True)
    evaluation_run_id: Mapped[int | None] = mapped_column(ForeignKey("knowledge_evaluation_runs.id"), nullable=True)
    checked_case_ids: Mapped[list[int]] = mapped_column(JSON, nullable=False, default=list)
    case_results: Mapped[list[dict]] = mapped_column(JSON, nullable=False, default=list)
    blocking_reasons: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    advisory_reasons: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    checks: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    document_snapshot: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    previous_publication_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rollback_target_publication_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rollback_reason: Mapped[str] = mapped_column(Text, nullable=False, default="")
    external_write_performed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    model_call_performed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class KnowledgeEmbeddingProviderSmokeRun(Base):
    __tablename__ = "knowledge_embedding_provider_smoke_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    purpose: Mapped[str] = mapped_column(String(80), nullable=False, default="embedding_provider_smoke")
    privacy_level: Mapped[str] = mapped_column(String(80), nullable=False, default="business_internal_no_pii")
    embedding_provider: Mapped[str] = mapped_column(String(80), nullable=False)
    embedding_model: Mapped[str] = mapped_column(String(120), nullable=False)
    vector_engine: Mapped[str] = mapped_column(String(120), nullable=False)
    vector_store: Mapped[str] = mapped_column(String(80), nullable=False)
    embedding_dimension: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    output_dimension: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    input_text_hash: Mapped[str] = mapped_column(String(80), nullable=False, default="")
    input_character_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    estimated_input_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    pricing_input_per_1k_tokens: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    estimated_cost: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    cost_currency: Mapped[str] = mapped_column(String(16), nullable=False, default="CNY")
    provider_call_performed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    raw_text_logged: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    quality_checks: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    response_metadata: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    error_message: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class KnowledgeVectorIndexPlan(Base):
    __tablename__ = "knowledge_vector_index_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    document_id: Mapped[int | None] = mapped_column(ForeignKey("knowledge_documents.id"), nullable=True)
    status_filter: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    plan_status: Mapped[str] = mapped_column(String(32), nullable=False, default="planned")
    requested_strategy: Mapped[str] = mapped_column(String(40), nullable=False, default="auto")
    selected_strategy: Mapped[str] = mapped_column(String(80), nullable=False, default="")
    index_method: Mapped[str] = mapped_column(String(40), nullable=False, default="none")
    index_name: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    vector_store: Mapped[str] = mapped_column(String(80), nullable=False, default="")
    retrieval_backend: Mapped[str] = mapped_column(String(80), nullable=False, default="")
    embedding_provider: Mapped[str] = mapped_column(String(80), nullable=False, default="")
    embedding_model: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    embedding_dimension: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    target_chunk_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    estimated_build_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    estimated_memory_mb: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    maintenance_window: Mapped[str] = mapped_column(String(80), nullable=False, default="off_peak")
    maintenance_window_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    dry_run: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    execute_performed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    concurrent_build: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    ddl_statements: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    rollback_statements: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    safety_checks: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    recommendation_reasons: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    query_options: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class KnowledgeEvaluationSet(Base):
    __tablename__ = "knowledge_evaluation_sets"
    __table_args__ = (
        UniqueConstraint("tenant_id", "name", name="uq_knowledge_evaluation_sets_tenant_id_name"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(180), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="draft")
    evaluation_mode: Mapped[str] = mapped_column(String(60), nullable=False, default="document_retrieval")
    created_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    updated_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class KnowledgeEvaluationCase(Base):
    __tablename__ = "knowledge_evaluation_cases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    evaluation_set_id: Mapped[int] = mapped_column(ForeignKey("knowledge_evaluation_sets.id"), nullable=False)
    external_case_id: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    source_channel: Mapped[str] = mapped_column(String(80), nullable=False, default="")
    source_category: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    question: Mapped[str] = mapped_column(Text, nullable=False)
    question_type: Mapped[str] = mapped_column(String(80), nullable=False, default="standard_customer_question")
    expected_terms: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    expected_source_uri: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    expected_document_title: Mapped[str] = mapped_column(String(180), nullable=False, default="")
    expected_chunk_ids: Mapped[list[int]] = mapped_column(JSON, nullable=False, default=list)
    must_have_all_evidence: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    expected_human_review: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    allow_auto_reply: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    forbidden_terms: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    risk_level: Mapped[str] = mapped_column(String(32), nullable=False, default="low")
    annotation_notes: Mapped[str] = mapped_column(Text, nullable=False, default="")
    required_citation: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class KnowledgeEvaluationRun(Base):
    __tablename__ = "knowledge_evaluation_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    evaluation_set_id: Mapped[int] = mapped_column(ForeignKey("knowledge_evaluation_sets.id"), nullable=False)
    run_mode: Mapped[str] = mapped_column(String(60), nullable=False, default="document_retrieval")
    retrieval_mode: Mapped[str] = mapped_column(String(80), nullable=False, default="")
    vector_engine: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    total_cases: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    answered_cases: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    no_hit_cases: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    passed_cases: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failed_cases: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    needs_review_cases: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    citation_covered_cases: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    expected_term_covered_cases: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    hit_rate: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    citation_coverage: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    expected_term_coverage: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    average_confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    unsupported_answer_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    summary_payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class KnowledgeEvaluationRunCase(Base):
    __tablename__ = "knowledge_evaluation_run_cases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    evaluation_run_id: Mapped[int] = mapped_column(ForeignKey("knowledge_evaluation_runs.id"), nullable=False)
    evaluation_case_id: Mapped[int] = mapped_column(ForeignKey("knowledge_evaluation_cases.id"), nullable=False)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    top_score: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    top_confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    top_chunk_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    top_document_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    citation_present: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    expected_terms_found: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    matched_terms: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    failure_reason: Mapped[str] = mapped_column(Text, nullable=False, default="")
    result_payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class KnowledgeGapItem(Base):
    __tablename__ = "knowledge_gaps"
    __table_args__ = (
        UniqueConstraint("tenant_id", "source_type", "source_ref", name="uq_knowledge_gaps_tenant_source"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="open")
    severity: Mapped[str] = mapped_column(String(32), nullable=False, default="medium")
    source_type: Mapped[str] = mapped_column(String(60), nullable=False)
    source_ref: Mapped[str] = mapped_column(String(180), nullable=False)
    source_title: Mapped[str] = mapped_column(String(180), nullable=False, default="")
    source_excerpt: Mapped[str] = mapped_column(Text, nullable=False, default="")
    question_excerpt: Mapped[str] = mapped_column(Text, nullable=False, default="")
    gap_type: Mapped[str] = mapped_column(String(80), nullable=False, default="")
    expected_terms: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    evidence_payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    linked_knowledge_card_id: Mapped[int | None] = mapped_column(ForeignKey("knowledge_cards.id"), nullable=True)
    linked_knowledge_document_id: Mapped[int | None] = mapped_column(
        ForeignKey("knowledge_documents.id"),
        nullable=True,
    )
    assigned_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    updated_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    resolved_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    resolution_note: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class WorkflowRun(Base):
    __tablename__ = "workflow_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("conversations.id"), nullable=False)
    trigger_message_id: Mapped[int | None] = mapped_column(ForeignKey("messages.id"), nullable=True)
    workflow_type: Mapped[str] = mapped_column(String(80), nullable=False, default="customer_reply")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="running")
    current_step: Mapped[str] = mapped_column(String(80), nullable=False, default="classify_intent")
    idempotency_key: Mapped[str] = mapped_column(String(160), nullable=False, default="")
    state_payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    checkpoints: Mapped[list["WorkflowCheckpoint"]] = relationship(
        back_populates="workflow_run",
        order_by="WorkflowCheckpoint.id",
    )
    step_attempts: Mapped[list["WorkflowStepAttempt"]] = relationship(
        back_populates="workflow_run",
        order_by="WorkflowStepAttempt.id",
    )
    human_review_tasks: Mapped[list["HumanReviewTask"]] = relationship(
        back_populates="workflow_run",
        order_by="HumanReviewTask.id",
    )


class WorkflowCheckpoint(Base):
    __tablename__ = "workflow_checkpoints"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    workflow_run_id: Mapped[int] = mapped_column(ForeignKey("workflow_runs.id"), nullable=False)
    step_name: Mapped[str] = mapped_column(String(80), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    state_payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    input_summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    output_summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    error_message: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    workflow_run: Mapped[WorkflowRun] = relationship(back_populates="checkpoints")


class WorkflowStepAttempt(Base):
    __tablename__ = "workflow_step_attempts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    workflow_run_id: Mapped[int] = mapped_column(ForeignKey("workflow_runs.id"), nullable=False)
    step_name: Mapped[str] = mapped_column(String(80), nullable=False)
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    input_summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    output_summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    error_message: Mapped[str] = mapped_column(Text, nullable=False, default="")
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    workflow_run: Mapped[WorkflowRun] = relationship(back_populates="step_attempts")


class HumanReviewTask(Base):
    __tablename__ = "human_review_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    workflow_run_id: Mapped[int] = mapped_column(ForeignKey("workflow_runs.id"), nullable=False)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("conversations.id"), nullable=False)
    message_id: Mapped[int | None] = mapped_column(ForeignKey("messages.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="open")
    reason: Mapped[str] = mapped_column(String(120), nullable=False)
    risk_level: Mapped[str] = mapped_column(String(32), nullable=False, default="medium")
    draft_reply: Mapped[str] = mapped_column(Text, nullable=False, default="")
    final_reply: Mapped[str] = mapped_column(Text, nullable=False, default="")
    assigned_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    reviewer_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    resolution_note: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    workflow_run: Mapped[WorkflowRun] = relationship(back_populates="human_review_tasks")


class OutboxDraft(Base):
    __tablename__ = "outbox_drafts"
    __table_args__ = (UniqueConstraint("tenant_id", "idempotency_key", name="uq_outbox_drafts_tenant_id_idempotency_key"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("conversations.id"), nullable=False)
    channel_id: Mapped[int] = mapped_column(ForeignKey("channels.id"), nullable=False)
    contact_id: Mapped[int] = mapped_column(ForeignKey("contacts.id"), nullable=False)
    source_review_task_id: Mapped[int | None] = mapped_column(ForeignKey("human_review_tasks.id"), nullable=True)
    source_workflow_run_id: Mapped[int | None] = mapped_column(ForeignKey("workflow_runs.id"), nullable=True)
    source_message_id: Mapped[int | None] = mapped_column(ForeignKey("messages.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending_confirmation")
    delivery_status: Mapped[str] = mapped_column(String(32), nullable=False, default="not_sent")
    reply_text: Mapped[str] = mapped_column(Text, nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(180), nullable=False)
    confirmation_note: Mapped[str] = mapped_column(Text, nullable=False, default="")
    cancellation_reason: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    confirmed_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    canceled_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    canceled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class OutboxSendAttempt(Base):
    __tablename__ = "outbox_send_attempts"
    __table_args__ = (
        UniqueConstraint("tenant_id", "idempotency_key", name="uq_outbox_send_attempts_tenant_id_idempotency_key"),
        UniqueConstraint("outbox_draft_id", "attempt_number", name="uq_outbox_send_attempts_draft_attempt_number"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    outbox_draft_id: Mapped[int] = mapped_column(ForeignKey("outbox_drafts.id"), nullable=False)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("conversations.id"), nullable=False)
    channel_id: Mapped[int] = mapped_column(ForeignKey("channels.id"), nullable=False)
    contact_id: Mapped[int] = mapped_column(ForeignKey("contacts.id"), nullable=False)
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False)
    delivery_mode: Mapped[str] = mapped_column(String(32), nullable=False, default="dry_run")
    provider: Mapped[str] = mapped_column(String(80), nullable=False, default="dry_run")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="queued")
    delivery_status: Mapped[str] = mapped_column(String(32), nullable=False, default="not_sent")
    idempotency_key: Mapped[str] = mapped_column(String(180), nullable=False)
    external_message_id: Mapped[str] = mapped_column(String(180), nullable=False, default="")
    request_payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    response_payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    error_message: Mapped[str] = mapped_column(Text, nullable=False, default="")
    operator_note: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class OutboxDeliveryJob(Base):
    __tablename__ = "outbox_delivery_jobs"
    __table_args__ = (
        UniqueConstraint("tenant_id", "idempotency_key", name="uq_outbox_delivery_jobs_tenant_id_idempotency_key"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    outbox_draft_id: Mapped[int] = mapped_column(ForeignKey("outbox_drafts.id"), nullable=False)
    channel_id: Mapped[int] = mapped_column(ForeignKey("channels.id"), nullable=False)
    connector_id: Mapped[int | None] = mapped_column(ForeignKey("channel_connectors.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="queued")
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    attempts_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    locked_by: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    locked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    next_run_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    idempotency_key: Mapped[str] = mapped_column(String(180), nullable=False)
    external_write_requested: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    external_write_permitted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    last_attempt_id: Mapped[int | None] = mapped_column(ForeignKey("outbox_send_attempts.id"), nullable=True)
    last_error: Mapped[str] = mapped_column(Text, nullable=False, default="")
    dead_letter_reason: Mapped[str] = mapped_column(String(160), nullable=False, default="")
    created_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ChannelDeliveryReceipt(Base):
    __tablename__ = "channel_delivery_receipts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    channel_id: Mapped[int] = mapped_column(ForeignKey("channels.id"), nullable=False)
    connector_id: Mapped[int | None] = mapped_column(ForeignKey("channel_connectors.id"), nullable=True)
    matched_attempt_id: Mapped[int | None] = mapped_column(ForeignKey("outbox_send_attempts.id"), nullable=True)
    provider: Mapped[str] = mapped_column(String(80), nullable=False)
    external_message_id: Mapped[str] = mapped_column(String(180), nullable=False, default="")
    delivery_status: Mapped[str] = mapped_column(String(40), nullable=False, default="unknown")
    provider_status: Mapped[str] = mapped_column(String(80), nullable=False, default="")
    provider_error_code: Mapped[str] = mapped_column(String(80), nullable=False, default="")
    normalized_status: Mapped[str] = mapped_column(String(80), nullable=False, default="unknown")
    retryable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    needs_review: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    next_action: Mapped[str] = mapped_column(String(120), nullable=False, default="manual_review_provider_status")
    provider_event_id: Mapped[str] = mapped_column(String(180), nullable=False, default="")
    verification_status: Mapped[str] = mapped_column(String(60), nullable=False, default="not_verified_placeholder")
    signature_validated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    raw_payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class DeliveryFailureReview(Base):
    __tablename__ = "delivery_failure_reviews"
    __table_args__ = (UniqueConstraint("receipt_id", name="uq_delivery_failure_reviews_receipt_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    channel_id: Mapped[int] = mapped_column(ForeignKey("channels.id"), nullable=False)
    connector_id: Mapped[int | None] = mapped_column(ForeignKey("channel_connectors.id"), nullable=True)
    receipt_id: Mapped[int] = mapped_column(ForeignKey("channel_delivery_receipts.id"), nullable=False)
    matched_attempt_id: Mapped[int | None] = mapped_column(ForeignKey("outbox_send_attempts.id"), nullable=True)
    outbox_draft_id: Mapped[int | None] = mapped_column(ForeignKey("outbox_drafts.id"), nullable=True)
    provider: Mapped[str] = mapped_column(String(80), nullable=False)
    external_message_id: Mapped[str] = mapped_column(String(180), nullable=False, default="")
    provider_status: Mapped[str] = mapped_column(String(80), nullable=False, default="")
    provider_error_code: Mapped[str] = mapped_column(String(80), nullable=False, default="")
    normalized_status: Mapped[str] = mapped_column(String(80), nullable=False)
    severity: Mapped[str] = mapped_column(String(32), nullable=False, default="warning")
    retryable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    review_reason: Mapped[str] = mapped_column(String(120), nullable=False)
    next_action: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="open")
    resolution_note: Mapped[str] = mapped_column(Text, nullable=False, default="")
    resolved_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
