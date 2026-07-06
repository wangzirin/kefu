#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def require_contains(path: str, needle: str) -> None:
    content = read(path)
    if needle not in content:
        raise AssertionError(f"{path} missing required marker: {needle}")


def require_absent(path: str, needles: list[str]) -> None:
    content = read(path)
    for needle in needles:
        if needle in content:
            raise AssertionError(f"{path} contains forbidden overclaim: {needle}")


def main() -> None:
    for path in [
        "backend/app/api/reply_strategies.py",
        "backend/app/services/reply_strategies.py",
        "backend/app/schemas/reply_strategies.py",
        "frontend/src/api/client.ts",
        "frontend/src/App.tsx",
        "frontend/src/styles.css",
    ]:
        if not (ROOT / path).exists():
            raise AssertionError(f"missing required file: {path}")

    for needle in [
        "app.include_router(reply_strategies.router)",
        "/tenants/{tenant_id}/reply-strategy",
        "TenantReplyStrategyUpdate",
        "tenant_reply_strategies",
        "customer_knowledge_center",
        "external_write_performed",
        "model_call_performed",
    ]:
        require_contains("backend/app/services/reply_strategies.py", needle) if needle == "customer_knowledge_center" else None
    require_contains("backend/app/main.py", "app.include_router(reply_strategies.router)")
    require_contains("backend/app/api/reply_strategies.py", "/tenants/{tenant_id}/reply-strategy")
    require_contains("backend/app/schemas/reply_strategies.py", "TenantReplyStrategyUpdate")
    require_contains("backend/app/services/reply_strategies.py", "tenant_reply_strategies")
    require_contains("backend/app/services/reply_strategies.py", "customer_knowledge_center")
    require_contains("backend/app/services/reply_strategies.py", "external_write_performed")
    require_contains("backend/app/services/reply_strategies.py", "model_call_performed")

    for needle in [
        "export async function getTenantReplyStrategy",
        "export async function updateTenantReplyStrategy",
        "export interface TenantReplyStrategy",
    ]:
        require_contains("frontend/src/api/client.ts", needle)

    for needle in [
        'data-h2w2-knowledge-center="true"',
        'data-h2w2-layer="business-object"',
        'data-h2w2-layer="standard-qa"',
        'data-h2w2-layer="process-policy"',
        'data-h2w2-layer="risk-rules"',
        'data-h2w2-reply-policy-editor="true"',
        'data-h2w2-action="save-reply-strategy"',
        "客户知识维护向导",
        "禁用承诺与转人工规则",
        "自动回复策略已保存",
    ]:
        require_contains("frontend/src/App.tsx", needle)

    for needle in [
        ".customer-knowledge-center",
        ".customer-knowledge-layer-grid",
        ".reply-policy-editor-card",
    ]:
        require_contains("frontend/src/styles.css", needle)

    require_absent(
        "frontend/src/App.tsx",
        ["已接通全平台", "已自动外发", "已完成正式准确率", "真实平台外发已开启"],
    )


if __name__ == "__main__":
    main()
