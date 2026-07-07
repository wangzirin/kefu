from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class ConversationInboxItemRead(BaseModel):
    id: int
    tenant_id: int
    channel_id: int
    channel_type: str
    channel_name: str
    contact_id: int
    contact_display_name: str
    assigned_user_id: Optional[int] = None
    assigned_team_id: Optional[int] = None
    status: str
    priority: str
    subject: str
    last_message_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    last_message_preview: str
    last_message_direction: Optional[str] = None
    last_customer_message_at: Optional[datetime] = None
    waiting_minutes: int
    sla_status: str
    sla_due_at: Optional[datetime] = None
    human_review_open_count: int
    outbox_pending_count: int
    delivery_failure_open_count: int
    next_action: str


class ConversationInboxList(BaseModel):
    items: list[ConversationInboxItemRead]
    page: int
    page_size: int
    total: int


class ConversationAssignmentUpdate(BaseModel):
    assigned_user_id: Optional[int] = None
    assigned_team_id: Optional[int] = None
    status: Optional[str] = Field(default=None, max_length=32)


ConversationWorkflowActionName = Literal[
    "claim",
    "release",
    "transfer",
    "close",
    "resolve",
    "follow_up",
    "wait_customer",
    "reopen",
    "note",
]


class ConversationWorkflowAction(BaseModel):
    action: ConversationWorkflowActionName
    target_user_id: Optional[int] = None
    target_team_id: Optional[int] = None
    note: str = Field(default="", max_length=1000)
