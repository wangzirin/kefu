#!/usr/bin/env python3
"""Static and local DB checks for P3-06U-11A."""

from __future__ import annotations

import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_text(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def table_count(db_path: Path, table: str, tenant_id: int | None = None) -> int:
    with sqlite3.connect(db_path) as conn:
        if tenant_id is None:
            row = conn.execute(f"select count(*) from {table}").fetchone()
        else:
            row = conn.execute(f"select count(*) from {table} where tenant_id = ?", (tenant_id,)).fetchone()
    return int(row[0])


def main() -> None:
    seed_script = read_text("scripts/seed_p3_06u_11_local_dev_workspace.py")
    app = read_text("frontend/src/App.tsx")
    conversation_panel = read_text("frontend/src/components/conversation/ConversationWorkbenchPanel.tsx")
    plan = read_text("docs/P3-06U-11_INFORMATION_ARCHITECTURE_AND_WORKBENCH_RESCUE_PLAN.md")

    for snippet in [
        "WANFA_LOCAL_DEV_PASSWORD",
        "password_source",
        '"password": "not_printed"',
        "generated_not_printed",
        "wanfa-local-dev",
        "real-test@wanfa.local",
        "DeliveryFailureReview",
        "KnowledgeGapItem",
    ]:
        require(snippet in seed_script, f"seed script missing required snippet: {snippet}")

    for forbidden in [
        'print(password',
        'print(token',
        'access_token',
        'wanfa_session_',
    ]:
        require(forbidden not in seed_script, f"seed script must not expose secrets via snippet: {forbidden}")

    for snippet in [
        "function refreshLiveWorkspaceResources()",
        '["live", "conversations", "reviews", "outbox"].includes(activeSection)',
        "onRefresh={refreshLiveWorkspaceResources}",
    ]:
        require(snippet in app, f"App missing live refresh snippet: {snippet}")

    for snippet in [
        "RefreshCw",
        "service-refresh-action",
        "刷新队列",
        "左侧选客户，右侧处理消息、AI 草稿和人工接管。",
    ]:
        require(snippet in conversation_panel, f"conversation panel missing refresh/simplification snippet: {snippet}")

    for phrase in [
        "P3-06U-11A",
        "真实本地开发库与登录稳定化",
        "多渠道对话台",
        "微信式",
    ]:
        require(phrase in plan, f"P3-06U-11 plan missing phrase: {phrase}")

    db_path = ROOT / "data" / "local_dev.sqlite"
    require(db_path.exists(), "local dev SQLite database must exist")
    with sqlite3.connect(db_path) as conn:
        row = conn.execute("select id from tenants where slug = ?", ("wanfa-local-dev",)).fetchone()
    require(row is not None, "wanfa-local-dev tenant must exist")
    tenant_id = int(row[0])

    minimums = {
        "users": 1,
        "roles": 4,
        "channels": 4,
        "contacts": 4,
        "conversations": 4,
        "human_review_tasks": 2,
        "outbox_drafts": 2,
        "knowledge_gaps": 2,
        "support_tickets": 1,
        "sales_leads": 1,
    }
    for table, minimum in minimums.items():
        count = table_count(db_path, table, tenant_id)
        require(count >= minimum, f"{table} expected >= {minimum}, got {count}")

    print("P3-06U-11A local dev workspace checks passed.")


if __name__ == "__main__":
    main()
