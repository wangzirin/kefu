#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


REQUIRED = {
    "scripts/smoke_bailian_chat_model.py": [
        "run_bailian_chat_smoke",
        "--allow-external-call",
        "blocked_external_call_not_allowed",
        "blocked_missing_api_key",
        "BAILIAN_API_KEY is not configured",
        "raw_text_logged",
        "provider_call_performed",
        "chat/completions",
    ],
    "backend/tests/test_bailian_chat_smoke_script.py": [
        "test_bailian_chat_smoke_blocks_external_call_without_explicit_allow",
        "test_bailian_chat_smoke_blocks_when_api_key_missing",
        "test_bailian_chat_smoke_calls_openai_compatible_provider_when_allowed",
        "test-key-not-real",
        "公开测试问题",
    ],
    "README.md": [
        "P2-20",
        "smoke_bailian_chat_model.py",
        "--allow-external-call",
        "blocked_missing_api_key",
    ],
    "docs/STAGE2_WORKFLOW_FOUNDATION.md": [
        "P2-20",
        "smoke_bailian_chat_model.py",
        "真实百炼聊天模型 smoke",
        "不会保存 API key",
    ],
}


def main() -> None:
    missing: list[str] = []
    for relative_path, fragments in REQUIRED.items():
        path = ROOT / relative_path
        if not path.exists():
            missing.append(f"{relative_path}: file missing")
            continue
        content = path.read_text(encoding="utf-8")
        for fragment in fragments:
            if fragment not in content:
                missing.append(f"{relative_path}: missing {fragment!r}")
    if missing:
        raise SystemExit("FAIL stage2 bailian chat smoke:\n" + "\n".join(missing))
    print("PASS stage2 bailian chat smoke")


if __name__ == "__main__":
    main()
