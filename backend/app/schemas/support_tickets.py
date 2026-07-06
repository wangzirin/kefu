from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field

SupportTicketStatus = Literal["open", "in_progress", "pending_customer", "resolved", "closed", "canceled"]
SupportTicketPriority = Literal["low", "normal", "high", "urgent"]


class SupportTicketCreate(BaseModel):
    subject: str = Field(default="", max_length=180)
    description: str = Field(default="", max_length=2000)
    priority: SupportTicketPriority | None = None
    assigned_user_id: Optional[int] = None
    assigned_team_id: Optional[int] = None
    sla_target_minutes: Optional[int] = Field(default=None, ge=5, le=10080)


class SupportTicketUpdate(BaseModel):
    subject: Optional[str] = Field(default=None, max_length=180)
    description: Optional[str] = Field(default=None, max_length=2000)
    status: Optional[SupportTicketStatus] = None
    priority: Optional[SupportTicketPriority] = None
    assigned_user_id: Optional[int] = None
    assigned_team_id: Optional[int] = None
    sla_target_minutes: Optional[int] = Field(default=None, ge=5, le=10080)
    resolution_note: Optional[str] = Field(default=None, max_length=2000)


class SupportTicketRead(BaseModel):
    id: int
    tenant_id: int
    conversation_id: int
    channel_id: int
    channel_name: str
    channel_type: str
    contact_id: int
    contact_display_name: str
    subject: str
    description: str
    status: str
    priority: str
    source_type: str
    source_ref: str
    assigned_user_id: Optional[int] = None
    assigned_team_id: Optional[int] = None
    sla_target_minutes: int
    sla_due_at: Optional[datetime] = None
    sla_status: str
    resolution_note: str
    created_by_id: Optional[int] = None
    updated_by_id: Optional[int] = None
    resolved_by_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None


class SupportTicketList(BaseModel):
    items: list[SupportTicketRead]
    page: int
    page_size: int
    total: int
