from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
RESEARCH_DIR = ROOT / "research" / "ai_rpa_closed_loop"
OUTPUT = ROOT / "output" / "ai_rpa_closed_loop_research" / "latest_run.json"


def main() -> int:
    required = [
        RESEARCH_DIR / "ai_rpa_closed_loop.py",
        RESEARCH_DIR / "run_research_loop.py",
        RESEARCH_DIR / "sample_inbound_messages.json",
        ROOT / "docs" / "AI_RPA_CLOSED_LOOP_RESEARCH_TECHNICAL_SOLUTION.md",
        ROOT / "backend" / "tests" / "test_ai_rpa_closed_loop_research.py",
    ]
    missing = [path for path in required if not path.exists()]
    if missing:
        print("Missing files:")
        for path in missing:
            print(f"- {path}")
        return 1

    subprocess.run(
        [
            sys.executable,
            str(RESEARCH_DIR / "run_research_loop.py"),
            "--output",
            str(OUTPUT),
        ],
        cwd=ROOT,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    payload = json.loads(OUTPUT.read_text(encoding="utf-8"))
    if payload["external_write_performed"]:
        print("external_write_performed must remain false")
        return 1
    if payload["messages_processed"] < 12:
        print("expected at least 12 synthetic messages")
        return 1

    all_actions = [
        action
        for result in payload["results"]
        for action in result["actions"]
    ]
    forbidden_action_kinds = {"click_send", "private_websocket_send", "cookie_replay"}
    seen_forbidden = [
        action["kind"] for action in all_actions if action["kind"] in forbidden_action_kinds
    ]
    if seen_forbidden:
        print(f"forbidden action kinds found: {seen_forbidden}")
        return 1

    results_by_id = {
        result["message"]["message_id"]: result for result in payload["results"]
    }
    required_ids = {
        "demo-001",
        "demo-002",
        "demo-004",
        "demo-006",
        "demo-007",
        "demo-010",
        "demo-012",
    }
    missing_ids = sorted(required_ids - set(results_by_id))
    if missing_ids:
        print(f"missing required strategy scenarios: {missing_ids}")
        return 1

    def strategy(message_id: str) -> dict[str, object]:
        return results_by_id[message_id]["reply_strategy"]

    if strategy("demo-001")["delivery_mode"] != "fill_draft_only":
        print("standard shipping question should remain fill_draft_only")
        return 1
    if strategy("demo-002")["delivery_mode"] != "human_takeover":
        print("refund complaint should route to human_takeover")
        return 1
    if strategy("demo-004")["delivery_mode"] != "record_gap":
        print("missing outdoor exposure knowledge should record_gap")
        return 1
    if strategy("demo-006")["delivery_mode"] != "human_takeover":
        print("lowest-price negotiation should route to human_takeover")
        return 1
    if strategy("demo-010")["delivery_mode"] != "human_takeover":
        print("attached after-sales damage case should route to human_takeover")
        return 1

    raw_text = json.dumps(payload, ensure_ascii=False)
    forbidden_snippets = [
        '"external_write": true',
        '"kind": "click_send"',
        '"kind": "private_websocket_send"',
        '"kind": "cookie_replay"',
        '"auto_send_enabled": true',
    ]
    leaked = [snippet for snippet in forbidden_snippets if snippet in raw_text]
    if leaked:
        print(f"forbidden snippets found in dry-run output: {leaked}")
        return 1

    print(
        json.dumps(
            {
                "status": "passed",
                "messages_processed": payload["messages_processed"],
                "external_write_performed": payload["external_write_performed"],
                "strategy_scenarios_checked": sorted(required_ids),
                "output": str(OUTPUT),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
