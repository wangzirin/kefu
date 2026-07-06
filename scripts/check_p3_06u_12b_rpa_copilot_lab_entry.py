from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def require_snippets(path: str, snippets: list[str]) -> list[str]:
    text = read(path)
    return [snippet for snippet in snippets if snippet not in text]


def main() -> int:
    required_paths = [
        "backend/app/schemas/rpa_copilot.py",
        "backend/app/services/rpa_copilot.py",
        "backend/app/api/rpa_copilot.py",
        "backend/tests/test_p3_06u_12b_rpa_copilot_api.py",
        "frontend/src/components/rpa/RpaCopilotLabPanel.tsx",
        "docs/P3-06U-12B_RPA_COPILOT_LAB_ENTRY.md",
    ]
    missing = [path for path in required_paths if not (ROOT / path).exists()]
    if missing:
        print(f"Missing required files: {missing}")
        return 1

    checks = {
        "backend/app/main.py": ["rpa_copilot", "app.include_router(rpa_copilot.router)"],
        "backend/app/api/rpa_copilot.py": [
            '"/rpa-copilot/strategy-dry-run"',
            'CONVERSATION_READ_PERMISSION = "conversation.read"',
            "run_rpa_copilot_strategy_dry_run",
        ],
        "backend/app/services/rpa_copilot.py": [
            '"manual_import_only": True',
            '"persisted_to_database": False',
            '"external_write_performed": False',
            '"auto_send_enabled": False',
        ],
        "frontend/src/data/navigation.ts": [
            'label: "实验室"',
            'href: "#rpa-lab"',
            'label: "RPA副驾驶试验"',
        ],
        "frontend/src/App.tsx": [
            '| "rpa-lab"',
            '"rpa-lab": "rpa-lab"',
            "<RpaCopilotLabPanel",
            "title: \"RPA 副驾驶试验\"",
            'activeSection !== "rpa-lab"',
        ],
        "frontend/src/components/rpa/RpaCopilotLabPanel.tsx": [
            "runRpaCopilotStrategyDryRun",
            "本页只做人工粘贴消息后的回复策略试算",
            "不读取平台账号、不保存客户消息、不点击发送",
            "delivery_mode",
            "record_gap",
            "human_takeover",
        ],
        "frontend/src/api/client.ts": [
            "RpaCopilotDryRunRequest",
            "RpaCopilotDryRunResponse",
            "runRpaCopilotStrategyDryRun",
            '"/api/rpa-copilot/strategy-dry-run"',
        ],
        "docs/P3-06U-12B_RPA_COPILOT_LAB_ENTRY.md": [
            "后端策略试算/决策服务",
            "RPA 副驾驶试验页",
            "不写数据库",
            "不读取平台账号",
            "不点击发送",
        ],
    }
    failures: dict[str, list[str]] = {}
    for path, snippets in checks.items():
        missing_snippets = require_snippets(path, snippets)
        if missing_snippets:
            failures[path] = missing_snippets
    if failures:
        for path, missing_snippets in failures.items():
            print(f"{path} missing snippets: {missing_snippets}")
        return 1

    service_text = read("backend/app/services/rpa_copilot.py")
    forbidden_service_snippets = [
        "db.add",
        "db.commit",
        "create_outbox",
        "click_send",
        "cookie_replay",
        "private_websocket_send",
    ]
    leaked = [snippet for snippet in forbidden_service_snippets if snippet in service_text]
    if leaked:
        print(f"forbidden service snippets found: {leaked}")
        return 1

    print("P3-06U-12B RPA copilot lab entry checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
