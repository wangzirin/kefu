#!/usr/bin/env python3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


REQUIRED = {
    "scripts/evaluate_bailian_chat_quality.py": [
        "run_bailian_chat_quality_evaluation",
        "QUALITY_EVAL_CASES",
        "--allow-external-call",
        "--limit",
        "blocked_external_call_not_allowed",
        "blocked_missing_api_key",
        "raw_text_logged",
        "provider_call_performed",
        "expected_terms_hit",
        "forbidden_terms_hit",
        "_score_forbidden_terms",
        "case_catalog",
        "built_in_public_synthetic_cases_v1",
    ],
    "backend/tests/test_bailian_chat_quality_eval_script.py": [
        "test_bailian_chat_quality_eval_blocks_without_explicit_allow",
        "test_bailian_chat_quality_eval_blocks_when_api_key_missing",
        "test_bailian_chat_quality_eval_calls_limited_fake_provider_and_scores_terms",
        "test_bailian_chat_quality_eval_ignores_forbidden_terms_in_safe_negation",
        "test-key-not-real",
        "客户说",
    ],
    "README.md": [
        "P2-21",
        "evaluate_bailian_chat_quality.py",
        "built_in_public_synthetic_cases_v1",
        "missing_expected_terms",
    ],
    "docs/STAGE2_WORKFLOW_FOUNDATION.md": [
        "P2-21",
        "evaluate_bailian_chat_quality.py",
        "脱敏合成题集",
        "不会把问题原文写入结果",
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
        raise SystemExit("FAIL stage2 bailian chat quality eval:\n" + "\n".join(missing))
    print("PASS stage2 bailian chat quality eval")


if __name__ == "__main__":
    main()
