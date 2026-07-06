#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import replace
import hashlib
import json
import os
from pathlib import Path
import sys
from time import perf_counter


ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.core.config import Settings, get_settings  # noqa: E402
from app.services.model_gateway import (  # noqa: E402
    ModelDraftKnowledge,
    ModelDraftRequest,
    generate_reply_draft,
    select_model_route,
)


DEFAULT_SAMPLE_TEXT = "公开测试问题：标准客服系统如何处理低置信问题？"
DEFAULT_KNOWLEDGE = ModelDraftKnowledge(
    title="标准客服系统低置信处理边界",
    answer=(
        "低置信、高风险或缺少可引用知识的问题，应先生成内部草稿，进入人工审核，"
        "由坐席确认后再发送给客户。"
    ),
    source_uri="internal://p2-20-chat-smoke-public-sample",
    matched_terms=["低置信", "人工审核", "发送前确认"],
)


def _load_dotenv_file(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if not key or key in os.environ:
            continue
        os.environ[key] = value.strip().strip('"').strip("'")


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _estimate_tokens(text: str) -> int:
    return max(1, int(len(text) / 4) + 1)


def _planned_route(settings: Settings, sample_text: str):
    planning_settings = settings
    if not planning_settings.bailian_api_key:
        planning_settings = replace(planning_settings, bailian_api_key="__planning_only__")
    return select_model_route(
        user_message=sample_text,
        intent="customer_service_quality_smoke",
        risk_level="low",
        confidence=0.86,
        knowledge_count=1,
        requested_provider="auto",
        requested_model="",
        settings=planning_settings,
    )


def _base_result(
    *,
    status: str,
    settings: Settings,
    sample_text: str,
    allow_external_call: bool,
) -> dict:
    route = _planned_route(settings, sample_text)
    return {
        "status": status,
        "provider": "bailian",
        "model": route.model,
        "route_name": route.route_name,
        "complexity": route.complexity,
        "target_model_tier": route.target_model_tier,
        "fallback_chain": route.fallback_chain,
        "human_review_required": route.human_review_required,
        "route_reasons": route.reasons,
        "allow_external_call": allow_external_call,
        "provider_call_performed": False,
        "raw_text_logged": False,
        "input_text_hash": _hash_text(sample_text),
        "input_character_count": len(sample_text),
        "estimated_input_tokens": _estimate_tokens(sample_text),
        "latency_ms": 0,
        "usage_summary": {
            "prompt_tokens_or_chars": 0,
            "completion_tokens_or_chars": 0,
            "total_tokens_or_chars": 0,
        },
        "error_message": "",
    }


def run_bailian_chat_smoke(
    *,
    allow_external_call: bool,
    sample_text: str = DEFAULT_SAMPLE_TEXT,
    settings: Settings | None = None,
) -> dict:
    settings = settings or get_settings()
    sample_text = sample_text.strip() or DEFAULT_SAMPLE_TEXT
    if not allow_external_call:
        result = _base_result(
            status="blocked_external_call_not_allowed",
            settings=settings,
            sample_text=sample_text,
            allow_external_call=allow_external_call,
        )
        result["error_message"] = "pass --allow-external-call before running real Bailian chat smoke"
        return result
    if not settings.bailian_api_key:
        result = _base_result(
            status="blocked_missing_api_key",
            settings=settings,
            sample_text=sample_text,
            allow_external_call=allow_external_call,
        )
        result["error_message"] = "BAILIAN_API_KEY is not configured"
        return result

    request = ModelDraftRequest(
        user_message=sample_text,
        intent="customer_service_quality_smoke",
        knowledge=[DEFAULT_KNOWLEDGE],
        provider="auto",
        model="",
        temperature=0.2,
        confidence=0.86,
        risk_level="low",
    )
    started = perf_counter()
    draft = generate_reply_draft(request, settings=settings)
    latency_ms = round((perf_counter() - started) * 1000, 3)
    return {
        "status": draft.status,
        "provider": draft.provider,
        "model": draft.model,
        "route_name": draft.route_name,
        "complexity": draft.complexity,
        "target_model_tier": draft.target_model_tier,
        "fallback_chain": draft.fallback_chain or [],
        "human_review_required": draft.human_review_required,
        "route_reasons": draft.route_reasons or [],
        "allow_external_call": allow_external_call,
        "provider_call_performed": True,
        "raw_text_logged": False,
        "input_text_hash": _hash_text(sample_text),
        "input_character_count": len(sample_text),
        "estimated_input_tokens": _estimate_tokens(sample_text),
        "latency_ms": latency_ms,
        "usage_summary": {
            "prompt_tokens_or_chars": draft.prompt_chars,
            "completion_tokens_or_chars": draft.completion_chars,
            "total_tokens_or_chars": draft.total_chars,
        },
        "draft_preview": draft.draft_text[:220],
        "error_message": draft.error_message,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a guarded Bailian chat model smoke test.")
    parser.add_argument("--allow-external-call", action="store_true", help="Actually call Bailian chat/completions.")
    parser.add_argument("--require-success", action="store_true", help="Exit non-zero unless the smoke succeeds.")
    parser.add_argument("--sample-text", default=DEFAULT_SAMPLE_TEXT, help="Public, non-sensitive sample customer question.")
    args = parser.parse_args()

    _load_dotenv_file(ROOT / ".env")
    result = run_bailian_chat_smoke(
        allow_external_call=args.allow_external_call,
        sample_text=args.sample_text,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    if args.require_success and result["status"] != "succeeded":
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
