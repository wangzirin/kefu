from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def require_snippets(path: str, snippets: list[str]) -> list[str]:
    text = read(path)
    return [snippet for snippet in snippets if snippet not in text]


def run_node_check(path: str) -> None:
    subprocess.run(["node", "--check", path], cwd=ROOT, check=True, text=True)


def main() -> int:
    required_paths = [
        "scripts/lib/rpa_browser_adapters.mjs",
        "scripts/run_p3_06u_12e_rpa_browser_reply_feasibility.mjs",
        "docs/P3-06U-12F_DOUYIN_WEB_DM_DRAFT_ONLY_PROBE.md",
        "docs/P3-06U-12G_RPA_BROWSER_ADAPTER_ABSTRACTION.md",
    ]
    missing = [path for path in required_paths if not (ROOT / path).exists()]
    if missing:
        print(f"Missing required files: {missing}")
        return 1

    checks = {
        "scripts/lib/rpa_browser_adapters.mjs": [
            "cdp_browser_adapter",
            "accessibility_browser_adapter",
            "contract_only_fail_closed",
            "sendAllowedByDefault: false",
            "persistsRawPrivateMessages: false",
            "RPA_ALLOW_SEND=1",
            "I_UNDERSTAND_THIS_CAN_SEND",
        ],
        "scripts/run_p3_06u_12e_rpa_browser_reply_feasibility.mjs": [
            "RPA_BROWSER_ADAPTER",
            "RPA_PRINT_ADAPTER_CAPABILITIES",
            "browser_adapter: adapterKind",
            "external-write action",
        ],
        "docs/P3-06U-12G_RPA_BROWSER_ADAPTER_ABSTRACTION.md": [
            "Engineering Control Card",
            "cdp_browser_adapter",
            "accessibility_browser_adapter",
            "Draft-Only",
            "默认不发送",
            "不保存原始私聊数据",
            "contract-only",
        ],
    }
    failures: dict[str, list[str]] = {}
    for path, snippets in checks.items():
        missing_snippets = require_snippets(path, snippets)
        if missing_snippets:
            failures[path] = missing_snippets
    if failures:
        for path, snippets in failures.items():
            print(f"{path} missing snippets: {snippets}")
        return 1

    run_node_check("scripts/lib/rpa_browser_adapters.mjs")
    run_node_check("scripts/run_p3_06u_12e_rpa_browser_reply_feasibility.mjs")

    env = os.environ.copy()
    env["RPA_PRINT_ADAPTER_CAPABILITIES"] = "1"
    env["P3_06U_12E_OUTPUT"] = "output/p3_06u_12g_rpa_adapter_abstraction/check_capabilities"
    completed = subprocess.run(
        ["node", "scripts/run_p3_06u_12e_rpa_browser_reply_feasibility.mjs"],
        cwd=ROOT,
        env=env,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    payload = json.loads(completed.stdout)
    adapters = {item["adapter"]: item for item in payload["capabilities"]}
    if adapters.get("cdp_browser_adapter", {}).get("status") != "implemented":
        print("cdp_browser_adapter must be implemented")
        return 1
    if adapters.get("accessibility_browser_adapter", {}).get("status") != "contract_only_fail_closed":
        print("accessibility_browser_adapter must remain fail-closed")
        return 1
    if any(item.get("sendAllowedByDefault") for item in adapters.values()):
        print("RPA adapters must not allow send by default")
        return 1
    if any(item.get("persistsRawPrivateMessages") for item in adapters.values()):
        print("RPA adapters must not persist raw private messages")
        return 1

    fail_closed = subprocess.run(
        [
            "node",
            "-e",
            (
                "import('./scripts/lib/rpa_browser_adapters.mjs').then(async (m) => {"
                "const a = m.createRpaBrowserAdapter('accessibility_browser_adapter', {});"
                "try { await a.open(); process.exit(1); } "
                "catch (err) { if (!String(err.message).includes('contract-only')) process.exit(1); }"
                "})"
            ),
        ],
        cwd=ROOT,
        text=True,
    )
    if fail_closed.returncode != 0:
        print("accessibility_browser_adapter did not fail closed")
        return 1

    print(
        json.dumps(
            {
                "status": "passed",
                "adapters": sorted(adapters),
                "accessibility_fail_closed": True,
                "send_allowed_by_default": False,
                "raw_private_message_persistence": False,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

