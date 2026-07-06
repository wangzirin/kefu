from datetime import datetime
from typing import List

from pydantic import BaseModel, Field


class TenantSummary(BaseModel):
    id: str
    name: str
    slug: str
    plan: str


class CurrentUser(BaseModel):
    id: str
    name: str
    email: str
    roles: List[str]
    permissions: List[str] = Field(default_factory=list)
    tenant: TenantSummary


class LoginRequest(BaseModel):
    tenant_slug: str = Field(min_length=1, max_length=80)
    email: str = Field(min_length=3, max_length=180)
    password: str = Field(min_length=1, max_length=128)


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    expires_at: datetime
    user: CurrentUser


class LocalSetupStatus(BaseModel):
    schema_version: str = "p3-06u-26h2w8a.local_setup_status.v1"
    initialized: bool
    tenant_count: int
    user_count: int
    can_create_first_owner: bool
    setup_mode: str
    first_owner_creation_locked: bool
    web_password_reset_enabled: bool = False
    env: str
    dev_bootstrap_enabled: bool
    external_write_enabled: bool
    trusted_inbound_worker_enabled: bool
    local_deployment_ready: bool
    readiness_checks: List[str] = Field(default_factory=list)
    blockers: List[str] = Field(default_factory=list)
    first_tenant_slug: str | None = None
    first_tenant_name: str | None = None


class LocalOwnerSetupRequest(BaseModel):
    tenant_name: str = Field(default="本地客服工作台", min_length=1, max_length=120)
    tenant_slug: str = Field(default="wanfa-local", min_length=1, max_length=80)
    owner_name: str = Field(default="管理员", min_length=1, max_length=120)
    email: str = Field(min_length=3, max_length=180)
    password: str = Field(min_length=8, max_length=128)
