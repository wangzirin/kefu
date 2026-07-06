from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class TenantCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    slug: str = Field(min_length=1, max_length=80)
    plan: str = Field(default="standard_ops", max_length=40)


class TenantRead(BaseModel):
    id: int
    name: str
    slug: str
    plan: str
    status: str
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class UserCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: str = Field(min_length=3, max_length=180, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    password: str = Field(min_length=8, max_length=128)
    status: str = Field(default="active", max_length=32)


class UserStatusUpdate(BaseModel):
    status: str = Field(pattern="^(active|inactive)$")


class UserPasswordReset(BaseModel):
    new_password: str = Field(min_length=8, max_length=128)


class UserRead(BaseModel):
    id: int
    tenant_id: int
    name: str
    email: str
    status: str
    roles: List[str] = Field(default_factory=list)
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class RoleCreate(BaseModel):
    code: str = Field(min_length=1, max_length=60)
    name: str = Field(min_length=1, max_length=120)


class RoleRead(BaseModel):
    id: int
    tenant_id: int
    code: str
    name: str
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class UserRoleCreate(BaseModel):
    role_id: int


class UserRoleRead(BaseModel):
    id: int
    user_id: int
    role_id: int
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class TeamCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=1000)
    status: str = Field(default="active", max_length=32)


class TeamRead(BaseModel):
    id: int
    tenant_id: int
    name: str
    description: str
    status: str
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class TeamMemberCreate(BaseModel):
    user_id: int
    role_in_team: str = Field(default="agent", max_length=60)


class TeamMemberRead(BaseModel):
    id: int
    team_id: int
    user_id: int
    role_in_team: str
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class AuditEventRead(BaseModel):
    id: int
    tenant_id: int
    actor_id: Optional[int] = None
    action: str
    resource_type: str
    resource_id: str
    payload: str
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ChannelCreate(BaseModel):
    type: str = Field(min_length=1, max_length=40)
    name: str = Field(min_length=1, max_length=120)
    reply_mode: str = Field(default="assist", max_length=32)
    status: str = Field(default="planned", max_length=32)


class ChannelRead(BaseModel):
    id: int
    tenant_id: int
    type: str
    name: str
    reply_mode: str
    status: str
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ContactCreate(BaseModel):
    display_name: str = Field(min_length=1, max_length=120)
    phone: str = Field(default="", max_length=40)
    wechat: str = Field(default="", max_length=80)


class ContactRead(BaseModel):
    id: int
    tenant_id: int
    display_name: str
    phone: str
    wechat: str
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ConversationCreate(BaseModel):
    channel_id: int
    contact_id: int
    subject: str = Field(default="", max_length=180)
    status: str = Field(default="bot", max_length=32)
    priority: str = Field(default="normal", max_length=32)
    assigned_user_id: Optional[int] = None
    assigned_team_id: Optional[int] = None


class ConversationRead(BaseModel):
    id: int
    tenant_id: int
    channel_id: int
    contact_id: int
    assigned_user_id: Optional[int] = None
    assigned_team_id: Optional[int] = None
    status: str
    priority: str
    subject: str
    last_message_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class MessageCreate(BaseModel):
    direction: str = Field(pattern="^(inbound|outbound)$")
    sender_type: str = Field(min_length=1, max_length=32)
    content: str = Field(min_length=1)
    external_message_id: str = Field(default="", max_length=120)


class MessageRead(BaseModel):
    id: int
    conversation_id: int
    direction: str
    sender_type: str
    content: str
    external_message_id: str
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ConversationDetail(ConversationRead):
    messages: List[MessageRead] = []
