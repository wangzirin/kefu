from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "docs" / "P3-06U-12_AI_RPA_REPLY_STRATEGY_INTEGRATION_PLAN.md"
RPA_DOC = ROOT / "docs" / "AI_RPA_CLOSED_LOOP_RESEARCH_TECHNICAL_SOLUTION.md"
IA_DOC = ROOT / "docs" / "P3-06U-11_INFORMATION_ARCHITECTURE_AND_WORKBENCH_RESCUE_PLAN.md"
OUTPUT = ROOT / "output" / "ai_rpa_closed_loop_research" / "latest_run.json"


def require_snippets(path: Path, snippets: list[str]) -> list[str]:
    text = path.read_text(encoding="utf-8")
    return [snippet for snippet in snippets if snippet not in text]


def main() -> int:
    required_files = [PLAN, RPA_DOC, IA_DOC]
    missing = [path for path in required_files if not path.exists()]
    if missing:
        print("Missing files:")
        for path in missing:
            print(f"- {path}")
        return 1

    missing_plan = require_snippets(
        PLAN,
        [
            "AI+RPA 研究线 = 非官方渠道场景下的坐席副驾驶",
            "P3-06U-12B",
            "delivery_mode",
            "human_takeover",
            "record_gap",
            "官方 API / Webhook 线：正式交付候选",
            "Playwright actionability",
            "Freshdesk workflows for AI agents",
        ],
    )
    if missing_plan:
        print(f"Plan missing snippets: {missing_plan}")
        return 1

    missing_rpa = require_snippets(
        RPA_DOC,
        [
            "reply_strategy",
            "delivery_mode=fill_draft_only",
            "delivery_mode=human_takeover",
            "delivery_mode=record_gap",
            "P3-06U-12_AI_RPA_REPLY_STRATEGY_INTEGRATION_PLAN.md",
            "不要一步跳到真实自动点击发送",
        ],
    )
    if missing_rpa:
        print(f"RPA doc missing snippets: {missing_rpa}")
        return 1

    missing_ia = require_snippets(
        IA_DOC,
        [
            "P3-06U-12：AI+RPA 回复策略与中台融合",
            "intent / answer_mode / delivery_mode / next_best_action",
            "暂时不做复杂账号角色拆分",
        ],
    )
    if missing_ia:
        print(f"IA doc missing snippets: {missing_ia}")
        return 1

    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "check_ai_rpa_closed_loop_research.py")],
        cwd=ROOT,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    payload = json.loads(OUTPUT.read_text(encoding="utf-8"))
    strategies = [result["reply_strategy"]["delivery_mode"] for result in payload["results"]]
    for required_mode in ["fill_draft_only", "human_takeover", "record_gap"]:
        if required_mode not in strategies:
            print(f"missing strategy mode in latest dry-run: {required_mode}")
            return 1

    print(
        json.dumps(
            {
                "status": "passed",
                "plan": str(PLAN),
                "messages_processed": payload["messages_processed"],
                "strategy_modes": sorted(set(strategies)),
                "external_write_performed": payload["external_write_performed"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
