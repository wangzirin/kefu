#!/usr/bin/env python3
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]


REQUIRED_TEXT = {
    "frontend/src/api/client.ts": [
        "KnowledgeEvaluationSet",
        "KnowledgeEvaluationRun",
        "createKnowledgeEvaluationSet",
        "listKnowledgeEvaluationSets",
        "runKnowledgeEvaluationSet",
    ],
    "frontend/src/App.tsx": [
        "KnowledgeEvaluationPanel",
        "知识评测与质量",
        "创建评测集",
        "运行评测",
        "命中率",
        "引用覆盖",
        "期望词覆盖",
        "unsupported_answer_rate",
    ],
    "frontend/src/styles.css": [
        ".evaluation-panel",
        ".evaluation-layout",
        ".evaluation-form",
        ".quality-metric-grid",
        ".evaluation-case-row",
        ".evaluation-result-row",
    ],
    "frontend/src/data/navigation.ts": [
        'count: "评测"',
    ],
}


def fail(message: str) -> None:
    print(f"FAIL stage2 knowledge evaluation frontend: {message}")
    sys.exit(1)


def main() -> None:
    for path, snippets in REQUIRED_TEXT.items():
        full_path = ROOT / path
        if not full_path.exists():
            fail(f"missing file: {path}")
        content = full_path.read_text(encoding="utf-8")
        missing = [snippet for snippet in snippets if snippet not in content]
        if missing:
            fail(f"missing fragment in {path}: {', '.join(missing)}")
    print("PASS stage2 knowledge evaluation frontend")


if __name__ == "__main__":
    main()
