from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field

LeadStage = Literal["new", "contacted", "proposal", "won", "invalid", "lost"]
LeadIntentLevel = Literal["cold", "warm", "hot"]


class SalesLeadCreate(BaseModel):
    title: str = Field(default="", max_length=180)
    summary: str = Field(default="", max_length=2000)
    stage: LeadStage = "new"
    intent_level: LeadIntentLevel = "warm"
    expected_budget: str = Field(default="", max_length=120)
    next_step: str = Field(default="", max_length=1000)
    owner_user_id: Optional[int] = None
    next_follow_up_at: Optional[datetime] = None


class SalesLeadUpdate(BaseModel):
    title: Optional[str] = Field(default=None, max_length=180)
    summary: Optional[str] = Field(default=None, max_length=2000)
    stage: Optional[LeadStage] = None
    intent_level: Optional[LeadIntentLevel] = None
    expected_budget: Optional[str] = Field(default=None, max_length=120)
    next_step: Optional[str] = Field(default=None, max_length=1000)
    owner_user_id: Optional[int] = None
    next_follow_up_at: Optional[datetime] = None


class SalesLeadRead(BaseModel):
    id: int
    tenant_id: int
    contact_id: int
    contact_display_name: str
    channel_id: int
    channel_name: str
    channel_type: str
    conversation_id: Optional[int] = None
    title: str
    summary: str
    stage: str
    intent_level: str
    expected_budget: str
    next_step: str
    owner_user_id: Optional[int] = None
    source_type: str
    source_ref: str
    latest_message_preview: str
    next_follow_up_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    created_by_id: Optional[int] = None
    updated_by_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class SalesLeadList(BaseModel):
    items: list[SalesLeadRead]
    page: int
    page_size: int
    total: int


class ContactConversationSummary(BaseModel):
    id: int
    channel_id: int
    channel_name: str
    channel_type: str
    status: str
    priority: str
    subject: str
    last_message_at: Optional[datetime] = None
    last_message_preview: str


class ContactTicketSummary(BaseModel):
    id: int
    subject: str
    status: str
    priority: str
    sla_status: str
    updated_at: Optional[datetime] = None


class ContactProfileRead(BaseModel):
    id: int
    tenant_id: int
    display_name: str
    phone: str
    wechat: str
    created_at: Optional[datetime] = None
    conversation_count: int
    open_conversation_count: int
    support_ticket_count: int
    open_support_ticket_count: int
    lead_count: int
    active_lead_count: int
    highest_intent_level: str
    latest_channel_id: Optional[int] = None
    latest_channel_name: str
    latest_channel_type: str
    last_message_at: Optional[datetime] = None
    last_message_preview: str
    next_action: str


class ContactProfileList(BaseModel):
    items: list[ContactProfileRead]
    page: int
    page_size: int
    total: int


class ContactProfileDetail(ContactProfileRead):
    recent_conversations: list[ContactConversationSummary]
    open_leads: list[SalesLeadRead]
    open_tickets: list[ContactTicketSummary]
