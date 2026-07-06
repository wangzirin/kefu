from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from ai_rpa_closed_loop import build_default_engine, load_messages, result_to_dict


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the AI+RPA research closed loop in dry-run mode."
    )
    parser.add_argument(
        "--messages",
        type=Path,
        default=CURRENT_DIR / "sample_inbound_messages.json",
        help="Path to a JSON file containing synthetic inbound messages.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=CURRENT_DIR.parents[1]
        / "output"
        / "ai_rpa_closed_loop_research"
        / "latest_run.json",
        help="Where to write the dry-run audit result.",
    )
    args = parser.parse_args()

    engine = build_default_engine()
    messages = load_messages(args.messages)
    results = [result_to_dict(engine.handle(message)) for message in messages]

    payload = {
        "mode": "research_dry_run",
        "external_write_performed": any(
            action["external_write"]
            for result in results
            for action in result["actions"]
        ),
        "messages_processed": len(results),
        "results": results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
