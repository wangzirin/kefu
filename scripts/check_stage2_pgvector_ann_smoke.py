#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


REQUIRED = {
    "scripts/smoke_pgvector_ann_indexes.py": [
        "CREATE EXTENSION IF NOT EXISTS vector",
        "USING hnsw",
        "USING ivfflat",
        "EXPLAIN (FORMAT JSON)",
        "recall_at_k",
        "DROP TABLE IF EXISTS",
        "external_model_call_performed",
        "application_query_path_changed",
        "refusing non-PostgreSQL execution",
    ],
    "README.md": [
        "P2-18H 第二片",
        "smoke_pgvector_ann_indexes.py",
        "真实建索引 smoke",
        "没有切换应用查询路径",
    ],
    "docs/STAGE2_WORKFLOW_FOUNDATION.md": [
        "P2-18H 第二片",
        "HNSW/IVFFlat 真实建索引 smoke",
        "没有切换应用查询路径",
        "external_model_call_performed=false",
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
        raise SystemExit("FAIL stage2 pgvector ann smoke:\n" + "\n".join(missing))
    print("PASS stage2 pgvector ann smoke")


if __name__ == "__main__":
    main()
