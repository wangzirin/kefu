#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import re
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

MATRIX_PATH = "docs/channel_autoreply_readiness_matrix.json"
DOC_PATH = "docs/P3-05C_OFFICIAL_CHANNEL_AUTOREPLY_READINESS.md"

REQUIRED_PROVIDERS = [
    "website",
    "wecom",
    "wechat_official_account",
    "douyin_open",
    "doudian_feige",
    "xiaohongshu",
    "taobao_tmall",
    "jd",
    "pinduoduo",
]

CURRENT_CODE_PROVIDERS = ["website", "wecom", "wechat_official_account"]

REQUIRED_DOC_PHRASES = [
    "P3-05C",
    "现在不能对外说",
    "平台可行不等于我们已实现",
    "企业微信客服",
    "微信公众号",
    "抖音开放平台",
    "小红书",
    "淘宝",
    "拼多多",
    "真实自动回复放行门槛",
    "OUTBOX_EXTERNAL_WRITE_ENABLED",
]

REQUIRED_SOURCE_HOSTS = [
    "developer.work.weixin.qq.com",
    "developers.weixin.qq.com",
    "developer.open-douyin.com",
    "op.jinritemai.com",
    "xiaohongshu.com",
    "open.taobao.com",
    "developer.alibaba.com",
    "jos.jd.com",
    "open.pinduoduo.com",
]


def _read(root: Path, relative_path: str) -> str:
    return (root / relative_path).read_text(encoding="utf-8")


def _load_matrix(root: Path) -> dict[str, Any]:
    return json.loads(_read(root, MATRIX_PATH))


def _channel_by_provider(matrix: dict[str, Any]) -> dict[str, dict[str, Any]]:
    channels = matrix.get("channels")
    if not isinstance(channels, list):
        return {}
    return {
        str(item.get("provider", "")): item
        for item in channels
        if isinstance(item, dict) and item.get("provider")
    }


def validate_matrix(matrix: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    channels = _channel_by_provider(matrix)

    missing = [provider for provider in REQUIRED_PROVIDERS if provider not in channels]
    if missing:
        errors.append("matrix missing providers: " + ", ".join(missing))

    summary = matrix.get("current_system_summary", {})
    if summary.get("production_autoreply_ready") is not False:
        errors.append("matrix summary must keep production_autoreply_ready=false")
    if summary.get("real_external_write_enabled") is not False:
        errors.append("matrix summary must keep real_external_write_enabled=false")

    code_ready = summary.get("current_code_ready_providers", [])
    if sorted(code_ready) != sorted(CURRENT_CODE_PROVIDERS):
        errors.append("matrix current_code_ready_providers must match current registry providers")

    for provider in REQUIRED_PROVIDERS:
        channel = channels.get(provider, {})
        for field in [
            "display_name",
            "official_autoreply_feasibility",
            "current_system_status",
            "production_autoreply_ready",
            "recommended_delivery_mode",
            "required_before_real_test",
            "official_sources",
            "commercial_conclusion",
        ]:
            if field not in channel:
                errors.append(f"{provider} missing field: {field}")
        if channel.get("production_autoreply_ready") is not False:
            errors.append(f"{provider} must not be marked production_autoreply_ready")
        if provider not in CURRENT_CODE_PROVIDERS and "No provider contract" not in str(channel.get("current_system_status", "")):
            errors.append(f"{provider} must state that no provider contract exists in current code")
        if not channel.get("official_sources"):
            errors.append(f"{provider} missing official_sources")

    pdd = channels.get("pinduoduo", {})
    if "not_publicly_verified" not in str(pdd.get("official_autoreply_feasibility", "")):
        errors.append("pinduoduo must remain not_publicly_verified until official API docs are obtained")

    return errors


def _extract_registry_provider_keys(registry_text: str) -> list[str]:
    match = re.search(r"_PROVIDER_CONTRACTS\s*=\s*\{(?P<body>.*?)\n\}", registry_text, flags=re.S)
    if not match:
        return []
    body = match.group("body")
    return sorted(set(re.findall(r'^\s+"([^"]+)":\s+ChannelProviderContract', body, flags=re.M)))


def validate_code_contracts(root: Path) -> list[str]:
    errors: list[str] = []
    registry_text = _read(root, "backend/app/services/channel_provider_registry.py")
    channel_connectors_text = _read(root, "backend/app/services/channel_connectors.py")
    outbox_worker_text = _read(root, "backend/app/workers/outbox_sender.py")
    env_text = _read(root, ".env.example")

    registry_providers = _extract_registry_provider_keys(registry_text)
    for provider in CURRENT_CODE_PROVIDERS:
        if provider not in registry_providers:
            errors.append(f"current provider missing from registry: {provider}")

    for unsupported_provider in ["douyin_open", "doudian_feige", "xiaohongshu", "taobao_tmall", "jd", "pinduoduo"]:
        if unsupported_provider in registry_providers:
            errors.append(f"unsupported provider unexpectedly present in registry: {unsupported_provider}")

    if "connector.external_write_enabled = False" not in channel_connectors_text:
        errors.append("channel connector configuration must force external_write_enabled=False")
    if "CONNECTOR_NOOP" not in channel_connectors_text or "official channel connector external write is disabled" not in channel_connectors_text:
        errors.append("channel connector send plan must remain connector_noop/blocked")
    if "external_write=False" not in outbox_worker_text and '"external_write": False' not in outbox_worker_text:
        errors.append("outbox worker must keep external_write false")
    if 'OUTBOX_EXTERNAL_WRITE_ENABLED=false' not in env_text:
        errors.append(".env.example must default OUTBOX_EXTERNAL_WRITE_ENABLED=false")

    return errors


def validate_doc(root: Path) -> list[str]:
    errors: list[str] = []
    doc_text = _read(root, DOC_PATH)
    missing_phrases = [phrase for phrase in REQUIRED_DOC_PHRASES if phrase not in doc_text]
    if missing_phrases:
        errors.append("doc missing phrases: " + ", ".join(missing_phrases))

    source_count = doc_text.count("https://")
    if source_count < 15:
        errors.append(f"doc must contain at least 15 source links, found {source_count}")

    missing_hosts = [host for host in REQUIRED_SOURCE_HOSTS if host not in doc_text]
    if missing_hosts:
        errors.append("doc missing source hosts: " + ", ".join(missing_hosts))

    if "个人号外挂" not in doc_text or "模拟点击" not in doc_text:
        errors.append("doc must explicitly exclude personal-account hooks and simulated clicks")

    return errors


def run_check(root: Path = ROOT) -> dict[str, Any]:
    matrix = _load_matrix(root)
    errors = []
    errors.extend(validate_matrix(matrix))
    errors.extend(validate_code_contracts(root))
    errors.extend(validate_doc(root))

    channels = _channel_by_provider(matrix)
    if errors:
        return {
            "status": "failed",
            "errors": errors,
            "production_autoreply_ready_count": sum(
                1 for channel in channels.values() if channel.get("production_autoreply_ready") is True
            ),
        }

    return {
        "status": "passed",
        "channel_count": len(channels),
        "current_code_ready_providers": matrix["current_system_summary"]["current_code_ready_providers"],
        "production_autoreply_ready_count": 0,
        "real_external_write_enabled": False,
        "external_platform_write_performed": False,
    }


def main() -> int:
    result = run_check()
    if result["status"] != "passed":
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1
    print("PASS p3-05c channel autoreply readiness")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
