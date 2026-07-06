#!/usr/bin/env python3
"""Seed a real local development workspace for P3-06U-11.

This script creates a deterministic local tenant, owner account, channels,
conversations, review tasks, outbox signals, knowledge gaps, a support ticket,
and a sales lead in the SQLite development database.

Credential policy:
- The script never prints a password or token.
- Set WANFA_LOCAL_DEV_PASSWORD to create or reset the local account password.
- If no password is provided and the account does not exist, a random password
  is generated only for hashing; rerun with WANFA_LOCAL_DEV_PASSWORD for manual
  browser login.
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import timedelta
import json
import os
from pathlib import Path
import secrets
import sys
from typing import Any

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session, sessionmaker


ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"
DEFAULT_DB_PATH = ROOT / "data" / "local_dev.sqlite"

sys.path.insert(0, str(BACKEND_DIR))

from app.core.security import hash_password  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.models import (  # noqa: E402
    Channel,
    ChannelDeliveryReceipt,
    Contact,
    Conversation,
    DeliveryFailureReview,
    HumanReviewTask,
    KnowledgeDocument,
    KnowledgeGapItem,
    Message,
    OutboxDeliveryJob,
    OutboxDraft,
    Role,
    SalesLead,
    SupportTicket,
    Team,
    TeamMember,
    Tenant,
    User,
    UserRole,
    WorkflowRun,
    utc_now,
)


def database_url() -> str:
    configured = os.getenv("DATABASE_URL", "").strip()
    if configured:
        return configured
    DEFAULT_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite+pysqlite:///{DEFAULT_DB_PATH}"


def scalar_count(db: Session, model: type[Any], tenant_id: int | None = None) -> int:
    query = select(func.count(model.id))
    if tenant_id is not None and hasattr(model, "tenant_id"):
        query = query.where(model.tenant_id == tenant_id)
    return int(db.scalar(query) or 0)


def get_or_create_role(db: Session, tenant_id: int, *, code: str, name: str) -> Role:
    role = db.scalar(select(Role).where(Role.tenant_id == tenant_id, Role.code == code))
    if role is None:
        role = Role(tenant_id=tenant_id, code=code, name=name)
        db.add(role)
        db.flush()
    else:
        role.name = name
    return role


def get_or_create_channel(db: Session, tenant_id: int, *, channel_type: str, name: str, status: str) -> Channel:
    channel = db.scalar(
        select(Channel).where(Channel.tenant_id == tenant_id, Channel.type == channel_type, Channel.name == name)
    )
    if channel is None:
        channel = Channel(
            tenant_id=tenant_id,
            type=channel_type,
            name=name,
            reply_mode="assist",
            status=status,
        )
        db.add(channel)
        db.flush()
    else:
        channel.reply_mode = "assist"
        channel.status = status
    return channel


def get_or_create_contact(db: Session, tenant_id: int, *, display_name: str, wechat: str = "") -> Contact:
    contact = db.scalar(select(Contact).where(Contact.tenant_id == tenant_id, Contact.display_name == display_name))
    if contact is None:
        contact = Contact(tenant_id=tenant_id, display_name=display_name, wechat=wechat)
        db.add(contact)
        db.flush()
    else:
        contact.wechat = wechat
    return contact


def get_or_create_team(db: Session, tenant_id: int) -> Team:
    team = db.scalar(select(Team).where(Team.tenant_id == tenant_id, Team.name == "试点接待组"))
    if team is None:
        team = Team(
            tenant_id=tenant_id,
            name="试点接待组",
            description="本地开发库用于验证多渠道对话台、人工审核和待发送门禁的测试坐席组。",
            status="active",
        )
        db.add(team)
        db.flush()
    return team


def ensure_team_member(db: Session, team: Team, user: User) -> None:
    member = db.scalar(select(TeamMember).where(TeamMember.team_id == team.id, TeamMember.user_id == user.id))
    if member is None:
        db.add(TeamMember(team_id=team.id, user_id=user.id, role_in_team="owner_agent"))


def ensure_owner_account(db: Session, tenant: Tenant) -> tuple[User, str]:
    email = os.getenv("WANFA_LOCAL_DEV_EMAIL", "real-test@wanfa.local").strip().lower()
    name = os.getenv("WANFA_LOCAL_DEV_USER_NAME", "本地真实测试负责人").strip() or "本地真实测试负责人"
    password = os.getenv("WANFA_LOCAL_DEV_PASSWORD", "")
    user = db.scalar(select(User).where(User.tenant_id == tenant.id, User.email == email))
    password_source = "preserved_existing_hash"
    if user is None:
        password_to_hash = password if password else secrets.token_urlsafe(24)
        password_source = "env_password_hash" if password else "generated_not_printed"
        user = User(
            tenant_id=tenant.id,
            name=name,
            email=email,
            password_hash=hash_password(password_to_hash),
            status="active",
        )
        db.add(user)
        db.flush()
    else:
        user.name = name
        user.status = "active"
        if password:
            user.password_hash = hash_password(password)
            password_source = "env_password_hash"
    owner_role = get_or_create_role(db, tenant.id, code="owner", name="空间负责人")
    for code, role_name in [
        ("admin", "运营管理员"),
        ("agent", "客服坐席"),
        ("viewer", "只读观察员"),
    ]:
        get_or_create_role(db, tenant.id, code=code, name=role_name)
    assignment = db.scalar(select(UserRole).where(UserRole.user_id == user.id, UserRole.role_id == owner_role.id))
    if assignment is None:
        db.add(UserRole(user_id=user.id, role_id=owner_role.id))
    return user, password_source


def ensure_message(
    db: Session,
    conversation: Conversation,
    *,
    direction: str,
    sender_type: str,
    content: str,
    minutes_ago: int,
) -> Message:
    message = db.scalar(select(Message).where(Message.conversation_id == conversation.id, Message.content == content))
    created_at = utc_now() - timedelta(minutes=minutes_ago)
    if message is None:
        message = Message(
            conversation_id=conversation.id,
            direction=direction,
            sender_type=sender_type,
            content=content,
            created_at=created_at,
        )
        db.add(message)
        db.flush()
    else:
        message.direction = direction
        message.sender_type = sender_type
        message.created_at = created_at
    if conversation.last_message_at is None or conversation.last_message_at < created_at:
        conversation.last_message_at = created_at
    return message


def ensure_conversation(
    db: Session,
    tenant_id: int,
    *,
    channel: Channel,
    contact: Contact,
    user: User,
    team: Team,
    subject: str,
    status: str,
    priority: str,
    assigned: bool,
    messages: Iterable[dict[str, Any]],
) -> tuple[Conversation, Message | None]:
    conversation = db.scalar(
        select(Conversation).where(
            Conversation.tenant_id == tenant_id,
            Conversation.channel_id == channel.id,
            Conversation.contact_id == contact.id,
            Conversation.subject == subject,
        )
    )
    if conversation is None:
        conversation = Conversation(
            tenant_id=tenant_id,
            channel_id=channel.id,
            contact_id=contact.id,
            assigned_user_id=user.id if assigned else None,
            assigned_team_id=team.id if assigned else None,
            status=status,
            priority=priority,
            subject=subject,
            last_message_at=utc_now(),
        )
        db.add(conversation)
        db.flush()
    else:
        conversation.assigned_user_id = user.id if assigned else None
        conversation.assigned_team_id = team.id if assigned else None
        conversation.status = status
        conversation.priority = priority
    last_inbound: Message | None = None
    for item in messages:
        msg = ensure_message(db, conversation, **item)
        if msg.direction == "inbound":
            last_inbound = msg
    return conversation, last_inbound


def ensure_review(
    db: Session,
    *,
    tenant_id: int,
    conversation: Conversation,
    trigger_message: Message | None,
    assigned_user_id: int | None,
    key: str,
    reason: str,
    risk_level: str,
    confidence: float,
    retrieved_knowledge_count: int,
    draft_reply: str,
    knowledge_matches: list[dict[str, Any]],
) -> HumanReviewTask:
    run = db.scalar(select(WorkflowRun).where(WorkflowRun.tenant_id == tenant_id, WorkflowRun.idempotency_key == key))
    state_payload = {
        "intent": conversation.subject,
        "retrieved_knowledge_count": retrieved_knowledge_count,
        "confidence": confidence,
        "risk_level": risk_level,
        "draft_source": "local_seed_ai_draft",
        "retrieval_mode": "hybrid_rag_expected",
        "retrieval_engine": "sqlite_dev_seed",
        "knowledge_matches": knowledge_matches,
        "model_call": {
            "provider": "bailian",
            "model": "qwen-plus",
            "external_call_performed": False,
            "reason": "local_dev_seed_only",
        },
        "auto_reply_threshold": 0.72,
    }
    if run is None:
        run = WorkflowRun(
            tenant_id=tenant_id,
            conversation_id=conversation.id,
            trigger_message_id=trigger_message.id if trigger_message else None,
            workflow_type="customer_reply",
            status="waiting_human",
            current_step="human_review",
            idempotency_key=key,
            state_payload=state_payload,
        )
        db.add(run)
        db.flush()
    else:
        run.conversation_id = conversation.id
        run.trigger_message_id = trigger_message.id if trigger_message else None
        run.status = "waiting_human"
        run.current_step = "human_review"
        run.state_payload = state_payload
        run.updated_at = utc_now()
    task = db.scalar(
        select(HumanReviewTask).where(
            HumanReviewTask.tenant_id == tenant_id,
            HumanReviewTask.workflow_run_id == run.id,
            HumanReviewTask.conversation_id == conversation.id,
        )
    )
    if task is None:
        task = HumanReviewTask(
            tenant_id=tenant_id,
            workflow_run_id=run.id,
            conversation_id=conversation.id,
            message_id=trigger_message.id if trigger_message else None,
            status="open",
            reason=reason,
            risk_level=risk_level,
            draft_reply=draft_reply,
            assigned_user_id=assigned_user_id,
        )
        db.add(task)
        db.flush()
    else:
        task.status = "open"
        task.reason = reason
        task.risk_level = risk_level
        task.draft_reply = draft_reply
        task.assigned_user_id = assigned_user_id
    return task


def ensure_outbox(
    db: Session,
    *,
    tenant_id: int,
    conversation: Conversation,
    channel: Channel,
    contact: Contact,
    user: User,
    source_review_task_id: int | None,
    source_workflow_run_id: int | None,
    source_message_id: int | None,
    key: str,
    reply_text: str,
    status: str = "pending_confirmation",
) -> OutboxDraft:
    draft = db.scalar(select(OutboxDraft).where(OutboxDraft.tenant_id == tenant_id, OutboxDraft.idempotency_key == key))
    if draft is None:
        draft = OutboxDraft(
            tenant_id=tenant_id,
            conversation_id=conversation.id,
            channel_id=channel.id,
            contact_id=contact.id,
            source_review_task_id=source_review_task_id,
            source_workflow_run_id=source_workflow_run_id,
            source_message_id=source_message_id,
            status=status,
            delivery_status="not_sent",
            reply_text=reply_text,
            idempotency_key=key,
            created_by_id=user.id,
        )
        db.add(draft)
        db.flush()
    else:
        draft.conversation_id = conversation.id
        draft.channel_id = channel.id
        draft.contact_id = contact.id
        draft.source_review_task_id = source_review_task_id
        draft.source_workflow_run_id = source_workflow_run_id
        draft.source_message_id = source_message_id
        draft.status = status
        draft.reply_text = reply_text
        draft.updated_at = utc_now()
    return draft


def ensure_delivery_failure(db: Session, *, tenant_id: int, channel: Channel, draft: OutboxDraft) -> None:
    receipt = db.scalar(
        select(ChannelDeliveryReceipt).where(
            ChannelDeliveryReceipt.tenant_id == tenant_id,
            ChannelDeliveryReceipt.provider_event_id == "local-dev-seed-taobao-delivery-blocked",
        )
    )
    if receipt is None:
        receipt = ChannelDeliveryReceipt(
            tenant_id=tenant_id,
            channel_id=channel.id,
            provider="taobao_open_platform",
            external_message_id="local-dev-message-001",
            delivery_status="failed",
            provider_status="blocked",
            provider_error_code="NO_OFFICIAL_SEND_AUTH",
            normalized_status="permission_blocked",
            retryable=False,
            needs_review=True,
            next_action="补齐官方授权和白名单测试后再放量",
            provider_event_id="local-dev-seed-taobao-delivery-blocked",
            verification_status="local_dev_seed",
            signature_validated=False,
            raw_payload={"seed": True, "external_write_performed": False},
        )
        db.add(receipt)
        db.flush()
    review = db.scalar(select(DeliveryFailureReview).where(DeliveryFailureReview.receipt_id == receipt.id))
    if review is None:
        db.add(
            DeliveryFailureReview(
                tenant_id=tenant_id,
                channel_id=channel.id,
                receipt_id=receipt.id,
                outbox_draft_id=draft.id,
                provider=receipt.provider,
                external_message_id=receipt.external_message_id,
                provider_status=receipt.provider_status,
                provider_error_code=receipt.provider_error_code,
                normalized_status=receipt.normalized_status,
                severity="warning",
                retryable=False,
                review_reason="本地种子数据：官方发送授权未完成，不能真实外发。",
                next_action="在渠道接入页完成官方授权、回调和白名单发送验收。",
                status="open",
            )
        )
    job = db.scalar(
        select(OutboxDeliveryJob).where(
            OutboxDeliveryJob.tenant_id == tenant_id,
            OutboxDeliveryJob.idempotency_key == "local-dev-seed-taobao-delivery-job",
        )
    )
    if job is None:
        db.add(
            OutboxDeliveryJob(
                tenant_id=tenant_id,
                outbox_draft_id=draft.id,
                channel_id=channel.id,
                status="blocked",
                priority=80,
                max_attempts=1,
                idempotency_key="local-dev-seed-taobao-delivery-job",
                external_write_requested=True,
                external_write_permitted=False,
                last_error="local dev seed: official connector not authorized",
                dead_letter_reason="official_authorization_missing",
                created_by_id=draft.created_by_id,
            )
        )


def ensure_knowledge_signals(db: Session, *, tenant_id: int, user: User, conversations: list[Conversation]) -> None:
    doc = db.scalar(select(KnowledgeDocument).where(KnowledgeDocument.tenant_id == tenant_id, KnowledgeDocument.title == "本地试点报价与部署说明"))
    if doc is None:
        doc = KnowledgeDocument(
            tenant_id=tenant_id,
            title="本地试点报价与部署说明",
            source_type="manual_document",
            source_uri="local://p3-06u-11/local-pilot-pricing",
            raw_text="入门验证版用于验证官网或单渠道客服、FAQ 命中、AI 草稿、人工审核和待发送门禁。真实外发需要官方渠道授权。",
            content_hash="local-p3-06u-11-pricing",
            tags=["入门验证版", "部署", "报价"],
            status="active",
            ingestion_status="indexed",
            chunk_count=1,
            created_by_id=user.id,
            updated_by_id=user.id,
        )
        db.add(doc)
        db.flush()
    for index, conversation in enumerate(conversations[:2], start=1):
        source_ref = f"conversation:{conversation.id}:local-dev-gap"
        gap = db.scalar(
            select(KnowledgeGapItem).where(KnowledgeGapItem.tenant_id == tenant_id, KnowledgeGapItem.source_ref == source_ref)
        )
        if gap is None:
            db.add(
                KnowledgeGapItem(
                    tenant_id=tenant_id,
                    status="open",
                    severity="high" if index == 1 else "medium",
                    source_type="conversation",
                    source_ref=source_ref,
                    source_title=conversation.subject,
                    source_excerpt="本地种子数据用于验证质量复盘和知识缺口能否进入修复闭环。",
                    question_excerpt=conversation.subject,
                    gap_type="missing_answer_detail",
                    expected_terms=["官方授权", "人工审核", "待发送门禁"],
                    evidence_payload={"seed": True, "conversation_id": conversation.id},
                    linked_knowledge_document_id=doc.id,
                    assigned_user_id=user.id,
                    created_by_id=user.id,
                    updated_by_id=user.id,
                )
            )


def ensure_customer_ops(db: Session, *, tenant_id: int, user: User, channel: Channel, contact: Contact, conversation: Conversation) -> None:
    ticket = db.scalar(
        select(SupportTicket).where(
            SupportTicket.tenant_id == tenant_id,
            SupportTicket.source_type == "conversation",
            SupportTicket.source_ref == f"local-dev-ticket:{conversation.id}",
        )
    )
    if ticket is None:
        db.add(
            SupportTicket(
                tenant_id=tenant_id,
                conversation_id=conversation.id,
                channel_id=channel.id,
                contact_id=contact.id,
                subject="确认试点部署范围和交付边界",
                description="本地种子工单：用于验证工单/SLA 在入门版是否需要降级为会话内跟进状态。",
                status="open",
                priority="medium",
                source_type="conversation",
                source_ref=f"local-dev-ticket:{conversation.id}",
                assigned_user_id=user.id,
                sla_target_minutes=240,
                sla_status="ok",
                created_by_id=user.id,
                updated_by_id=user.id,
            )
        )
    lead = db.scalar(
        select(SalesLead).where(
            SalesLead.tenant_id == tenant_id,
            SalesLead.source_type == "conversation",
            SalesLead.source_ref == f"local-dev-lead:{conversation.id}",
        )
    )
    if lead is None:
        db.add(
            SalesLead(
                tenant_id=tenant_id,
                contact_id=contact.id,
                channel_id=channel.id,
                conversation_id=conversation.id,
                title="标准运营版试点咨询",
                summary="客户关注单渠道试点、报价、人工审核和后续扩展到企微/电商平台的可行性。",
                stage="qualified",
                intent_level="hot",
                expected_budget="3-8 万试点预算",
                next_step="发送部署边界说明，确认是否进入企业微信官方接入联调。",
                owner_user_id=user.id,
                source_type="conversation",
                source_ref=f"local-dev-lead:{conversation.id}",
                created_by_id=user.id,
                updated_by_id=user.id,
                next_follow_up_at=utc_now() + timedelta(days=1),
            )
        )


def seed(db: Session) -> dict[str, Any]:
    tenant_slug = os.getenv("WANFA_LOCAL_DEV_TENANT_SLUG", "wanfa-local-dev").strip() or "wanfa-local-dev"
    tenant = db.scalar(select(Tenant).where(Tenant.slug == tenant_slug))
    if tenant is None:
        tenant = Tenant(name="万法常世本地真实测试空间", slug=tenant_slug, plan="standard_ops", status="active")
        db.add(tenant)
        db.flush()
    else:
        tenant.name = "万法常世本地真实测试空间"
        tenant.plan = "standard_ops"
        tenant.status = "active"

    user, password_source = ensure_owner_account(db, tenant)
    team = get_or_create_team(db, tenant.id)
    ensure_team_member(db, team, user)

    channels = {
        "wecom": get_or_create_channel(db, tenant.id, channel_type="wecom", name="企业微信客服", status="active"),
        "douyin": get_or_create_channel(db, tenant.id, channel_type="douyin", name="抖音小店私信", status="planned"),
        "taobao": get_or_create_channel(db, tenant.id, channel_type="taobao", name="淘宝店铺客服", status="planned"),
        "xiaohongshu": get_or_create_channel(db, tenant.id, channel_type="xiaohongshu", name="小红书私信", status="planned"),
    }
    contacts = {
        "li": get_or_create_contact(db, tenant.id, display_name="李女士", wechat="local-li"),
        "wang": get_or_create_contact(db, tenant.id, display_name="王先生", wechat="local-wang"),
        "chen": get_or_create_contact(db, tenant.id, display_name="陈经理", wechat="local-chen"),
        "zhao": get_or_create_contact(db, tenant.id, display_name="赵同学", wechat="local-zhao"),
    }

    c1, m1 = ensure_conversation(
        db,
        tenant.id,
        channel=channels["wecom"],
        contact=contacts["li"],
        user=user,
        team=team,
        subject="咨询入门验证版部署和报价",
        status="waiting_human",
        priority="high",
        assigned=True,
        messages=[
            {
                "direction": "inbound",
                "sender_type": "visitor",
                "content": "我们想先做一个入门验证版，能不能接企业微信客服？大概多久能上线？",
                "minutes_ago": 84,
            }
        ],
    )
    review1 = ensure_review(
        db,
        tenant_id=tenant.id,
        conversation=c1,
        trigger_message=m1,
        assigned_user_id=user.id,
        key="local-dev-review-wecom-lite",
        reason="报价和交付边界需要人工核对",
        risk_level="high",
        confidence=0.54,
        retrieved_knowledge_count=1,
        draft_reply="可以先从入门验证版开始，通常先完成知识库、AI 草稿、人工审核和企业微信客服官方回调验证。具体上线时间取决于贵司的企微认证、可信 IP、域名备案和测试白名单准备情况。",
        knowledge_matches=[
            {
                "title": "入门验证版交付边界",
                "source_uri": "local://p3-06u-11/local-pilot-pricing",
                "excerpt": "入门验证版验证官网或单渠道客服、FAQ 命中、AI 草稿、人工审核和待发送门禁。",
            }
        ],
    )

    c2, m2 = ensure_conversation(
        db,
        tenant.id,
        channel=channels["douyin"],
        contact=contacts["wang"],
        user=user,
        team=team,
        subject="追问抖音私信能否自动回复",
        status="bot",
        priority="normal",
        assigned=False,
        messages=[
            {
                "direction": "inbound",
                "sender_type": "visitor",
                "content": "如果粉丝在抖音私信问价格，系统可以马上自动回复吗？会不会违规？",
                "minutes_ago": 18,
            }
        ],
    )
    review2 = ensure_review(
        db,
        tenant_id=tenant.id,
        conversation=c2,
        trigger_message=m2,
        assigned_user_id=None,
        key="local-dev-review-douyin-auth",
        reason="涉及外部平台官方授权边界",
        risk_level="medium",
        confidence=0.42,
        retrieved_knowledge_count=0,
        draft_reply="抖音私信自动回复必须以官方开放能力或服务商授权为准。试点阶段可以先在中台生成 AI 草稿并由人工确认，不建议使用个人号外挂、模拟点击或非官方群控方式。",
        knowledge_matches=[],
    )

    c3, m3 = ensure_conversation(
        db,
        tenant.id,
        channel=channels["taobao"],
        contact=contacts["chen"],
        user=user,
        team=team,
        subject="淘宝售后物流和退款追问",
        status="handoff",
        priority="medium",
        assigned=True,
        messages=[
            {
                "direction": "inbound",
                "sender_type": "visitor",
                "content": "客户说物流一直没有更新，还问超过七天能不能退款，麻烦看一下怎么回复。",
                "minutes_ago": 47,
            },
            {
                "direction": "outbound",
                "sender_type": "agent",
                "content": "已收到，我们先核对订单状态，再给出退款和物流处理建议。",
                "minutes_ago": 42,
            },
        ],
    )
    draft = ensure_outbox(
        db,
        tenant_id=tenant.id,
        conversation=c3,
        channel=channels["taobao"],
        contact=contacts["chen"],
        user=user,
        source_review_task_id=None,
        source_workflow_run_id=None,
        source_message_id=m3.id if m3 else None,
        key="local-dev-taobao-pending-outbox",
        reply_text="建议先安抚客户并同步订单核查口径：我们正在为您核对物流节点，如确认物流异常，会按店铺售后规则协助处理退款或补发。",
        status="pending_confirmation",
    )
    ensure_delivery_failure(db, tenant_id=tenant.id, channel=channels["taobao"], draft=draft)

    c4, _ = ensure_conversation(
        db,
        tenant.id,
        channel=channels["xiaohongshu"],
        contact=contacts["zhao"],
        user=user,
        team=team,
        subject="小红书咨询能否预约演示",
        status="open",
        priority="normal",
        assigned=False,
        messages=[
            {
                "direction": "inbound",
                "sender_type": "visitor",
                "content": "看到你们说可以做 AI 客服中台，可以先看一个演示吗？",
                "minutes_ago": 6,
            }
        ],
    )

    ensure_outbox(
        db,
        tenant_id=tenant.id,
        conversation=c1,
        channel=channels["wecom"],
        contact=contacts["li"],
        user=user,
        source_review_task_id=review1.id,
        source_workflow_run_id=review1.workflow_run_id,
        source_message_id=m1.id if m1 else None,
        key="local-dev-wecom-lite-review-outbox",
        reply_text=review1.draft_reply,
        status="pending_confirmation",
    )

    ensure_knowledge_signals(db, tenant_id=tenant.id, user=user, conversations=[c1, c2])
    ensure_customer_ops(db, tenant_id=tenant.id, user=user, channel=channels["wecom"], contact=contacts["li"], conversation=c1)

    db.commit()
    return {
        "database_url": database_url().replace(str(Path.home()), "~"),
        "tenant": {"id": tenant.id, "slug": tenant.slug, "name": tenant.name},
        "user": {"id": user.id, "email": user.email, "name": user.name},
        "password": "not_printed",
        "password_source": password_source,
        "counts": {
            "tenants": scalar_count(db, Tenant),
            "users": scalar_count(db, User, tenant.id),
            "roles": scalar_count(db, Role, tenant.id),
            "channels": scalar_count(db, Channel, tenant.id),
            "contacts": scalar_count(db, Contact, tenant.id),
            "conversations": scalar_count(db, Conversation, tenant.id),
            "messages": int(
                db.scalar(
                    select(func.count(Message.id))
                    .join(Conversation, Conversation.id == Message.conversation_id)
                    .where(Conversation.tenant_id == tenant.id)
                )
                or 0
            ),
            "human_review_tasks": scalar_count(db, HumanReviewTask, tenant.id),
            "outbox_drafts": scalar_count(db, OutboxDraft, tenant.id),
            "delivery_failure_reviews": scalar_count(db, DeliveryFailureReview, tenant.id),
            "knowledge_gaps": scalar_count(db, KnowledgeGapItem, tenant.id),
            "support_tickets": scalar_count(db, SupportTicket, tenant.id),
            "sales_leads": scalar_count(db, SalesLead, tenant.id),
        },
    }


def main() -> None:
    url = database_url()
    engine = create_engine(url, connect_args={"check_same_thread": False} if url.startswith("sqlite") else {})
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    with session_factory() as db:
        result = seed(db)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
