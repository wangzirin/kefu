from __future__ import annotations

import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
PROFILE_PATH = ROOT / "research/rpa_browser_reply_feasibility/profiles/douyin_web_dm.draft_only.locator_profile.json"
DOC_PATH = ROOT / "docs/P3-06U-12H_REAL_PAGE_LOCATOR_PROFILE_DRAFT.md"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def flatten_strings(value: object) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        out: list[str] = []
        for item in value:
            out.extend(flatten_strings(item))
        return out
    if isinstance(value, dict):
        out: list[str] = []
        for key, item in value.items():
            out.append(str(key))
            out.extend(flatten_strings(item))
        return out
    return []


def find_forbidden_keys(value: object, forbidden: set[str], path: str = "$") -> list[str]:
    findings: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            next_path = f"{path}.{key}"
            if key in forbidden:
                findings.append(next_path)
            findings.extend(find_forbidden_keys(item, forbidden, next_path))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            findings.extend(find_forbidden_keys(item, forbidden, f"{path}[{index}]"))
    return findings


def main() -> int:
    require(PROFILE_PATH.exists(), f"missing profile: {PROFILE_PATH}")
    require(DOC_PATH.exists(), f"missing doc: {DOC_PATH}")

    profile = read_json(PROFILE_PATH)
    doc_text = DOC_PATH.read_text(encoding="utf-8")
    profile_text = PROFILE_PATH.read_text(encoding="utf-8")

    require(profile.get("schema_version") == "rpa_locator_profile.v1", "profile schema_version mismatch")
    require(profile.get("profile_id") == "douyin_web_dm_draft_only_research_v1", "profile_id mismatch")
    require(profile.get("platform") == "douyin_web", "platform mismatch")
    require(profile.get("page_kind") == "personal_web_dm_popup", "page_kind must stay personal_web_dm_popup")
    require(profile.get("status") == "draft_profile_only", "profile status must stay draft_profile_only")

    not_equivalent_to = set(profile.get("not_equivalent_to", []))
    for required in [
        "douyin_shop_fengge",
        "douyin_enterprise_im",
        "douyin_open_platform_api",
        "official_customer_service_connector",
        "unattended_auto_reply",
    ]:
        require(required in not_equivalent_to, f"not_equivalent_to missing {required}")

    adapter_candidates = set(profile.get("adapter_candidates", []))
    require("accessibility_browser_adapter" in adapter_candidates, "real page profile must name accessibility boundary")
    require(
        profile.get("cdp_compatibility", {}).get("status") == "not_verified_for_current_logged_in_page",
        "CDP compatibility must remain unverified for current logged-in page",
    )

    delivery_policy = profile.get("delivery_policy", {})
    expected_false = [
        "send_allowed",
        "auto_send_allowed",
        "raw_private_data_persistence_allowed",
        "capture_screenshot_allowed",
        "store_cookie_token_localstorage_allowed",
    ]
    for key in expected_false:
        require(delivery_policy.get(key) is False, f"delivery_policy.{key} must be false")
    expected_true = [
        "must_not_click_send",
        "press_enter_blocked",
        "auto_clear_draft_required",
        "clear_draft_after_probe",
        "human_visible_operation_required",
        "operator_confirmation_required_before_any_real_page_probe",
    ]
    for key in expected_true:
        require(delivery_policy.get(key) is True, f"delivery_policy.{key} must be true")

    disallowed_use = set(profile.get("target_scope", {}).get("disallowed_use", []))
    for required in [
        "click_send",
        "press_enter_to_send",
        "scrape_private_messages",
        "persist_private_conversation",
        "read_cookie_token_or_localstorage",
    ]:
        require(required in disallowed_use, f"target_scope.disallowed_use missing {required}")

    forbidden_observations = set(profile.get("observation_contract", {}).get("forbidden_observations", []))
    for required in [
        "raw message text",
        "account ids",
        "cookies",
        "tokens",
        "localStorage",
        "sessionStorage",
        "screenshots of the private page",
        "raw accessibility tree dumps",
    ]:
        require(required in forbidden_observations, f"forbidden_observations missing {required}")

    all_strings = "\n".join(flatten_strings(profile))
    for required in ["draft_only", "must_not_click_send", "clear_draft_after_probe", "stop_without_action"]:
        require(required in all_strings, f"profile must contain safety marker {required}")

    forbidden_profile_keys = {
        "sample_private_message",
        "raw_message",
        "raw_messages",
        "conversation_samples",
        "conversation_names",
        "friend_names",
        "group_names",
        "avatar_url",
        "avatar_urls",
        "cookie",
        "cookies_value",
        "token",
        "local_storage",
        "raw_accessibility_tree",
        "screenshot_path",
    }
    forbidden_key_findings = find_forbidden_keys(profile, forbidden_profile_keys)
    require(not forbidden_key_findings, f"forbidden private-data keys found: {forbidden_key_findings}")

    long_digit_sequences = re.findall(r"(?<![A-Za-z0-9])\d{6,}(?![A-Za-z0-9])", profile_text)
    require(not long_digit_sequences, f"profile contains account-like long digit sequences: {long_digit_sequences}")

    for snippet in [
        "Engineering Control Card",
        "不是连接器",
        "不是抖店飞鸽",
        "Draft-Only",
        "不点击发送",
        "不保存私聊内容",
        "operator-mediated",
    ]:
        require(snippet in doc_text, f"doc missing required snippet: {snippet}")

    require("点击发送" in doc_text and "不点击发送" in doc_text, "doc must explicitly distinguish send boundary")
    require("capture_screenshot_allowed=false" in doc_text, "doc must state screenshot capture is disabled")
    require("raw_private_data_persistence_allowed=false" in doc_text, "doc must state raw private data is disabled")

    print(
        json.dumps(
            {
                "status": "passed",
                "profile_id": profile["profile_id"],
                "page_kind": profile["page_kind"],
                "delivery_mode": delivery_policy["delivery_mode"],
                "send_allowed": delivery_policy["send_allowed"],
                "auto_clear_draft_required": delivery_policy["auto_clear_draft_required"],
                "adapter_candidates": sorted(adapter_candidates),
                "privacy_persistence_allowed": delivery_policy["raw_private_data_persistence_allowed"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"FAIL: {exc}")
        raise SystemExit(1)
