#!/usr/bin/env python3
"""Local pgvector ANN index smoke.

This script creates disposable smoke tables in a PostgreSQL database, builds
HNSW and IVFFlat indexes, compares ANN top-k results with exact scan results,
prints timing/recall metrics, and drops every smoke table before exit.

It is intentionally not wired into the application query path.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import random
import time
from dataclasses import dataclass
from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine


DEFAULT_DATABASE_URL = "postgresql+psycopg://wanfa_ops:wanfa_ops_password@127.0.0.1:5432/wanfa_ops"


@dataclass(frozen=True)
class SmokeConfig:
    database_url: str
    rows: int
    dimensions: int
    top_k: int
    seed: int
    keep_tables: bool


def _pgvector_literal(vector: list[float]) -> str:
    return "[" + ",".join(f"{value:.8f}" for value in vector) + "]"


def _normalized(values: list[float]) -> list[float]:
    norm = math.sqrt(sum(value * value for value in values)) or 1.0
    return [round(value / norm, 8) for value in values]


def _sample_vectors(*, rows: int, dimensions: int, seed: int) -> list[list[float]]:
    rng = random.Random(seed)
    vectors: list[list[float]] = []
    for _ in range(rows):
        vectors.append(_normalized([rng.uniform(-1.0, 1.0) for _ in range(dimensions)]))
    return vectors


def _timed_execute(engine: Engine, statement: str, params: dict[str, Any] | None = None) -> float:
    started = time.perf_counter()
    with engine.begin() as connection:
        connection.execute(text(statement), params or {})
    return round((time.perf_counter() - started) * 1000, 3)


def _prepare_table(engine: Engine, *, table_name: str, dimensions: int, vectors: list[list[float]]) -> None:
    values = [
        {"source_id": f"chunk-{index}", "embedding": _pgvector_literal(vector)}
        for index, vector in enumerate(vectors)
    ]
    with engine.begin() as connection:
        connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        connection.execute(text(f"DROP TABLE IF EXISTS {table_name}"))
        connection.execute(
            text(
                f"""
                CREATE TABLE {table_name} (
                    id bigserial PRIMARY KEY,
                    tenant_id integer NOT NULL DEFAULT 1,
                    status text NOT NULL DEFAULT 'active',
                    source_id text NOT NULL,
                    embedding vector({dimensions}) NOT NULL
                )
                """
            )
        )
        connection.execute(
            text(
                f"""
                INSERT INTO {table_name} (source_id, embedding)
                VALUES (:source_id, CAST(:embedding AS vector))
                """
            ),
            values,
        )
        connection.execute(text(f"ANALYZE {table_name}"))


def _top_ids(
    engine: Engine,
    *,
    table_name: str,
    query_vector: list[float],
    top_k: int,
    force_index: bool,
    index_method: str,
) -> tuple[list[int], float, str]:
    options = []
    if force_index:
        options.append("SET LOCAL enable_seqscan = off")
        if index_method == "hnsw":
            options.append("SET LOCAL hnsw.ef_search = 100")
        elif index_method == "ivfflat":
            options.append("SET LOCAL ivfflat.probes = 10")
    query = (
        f"SELECT id FROM {table_name} "
        "WHERE tenant_id = 1 AND status = 'active' "
        "ORDER BY embedding <=> CAST(:query_vector AS vector) "
        "LIMIT :top_k"
    )
    explain = "EXPLAIN (FORMAT JSON) " + query
    started = time.perf_counter()
    with engine.begin() as connection:
        for option in options:
            connection.execute(text(option))
        rows = connection.execute(
            text(query),
            {"query_vector": _pgvector_literal(query_vector), "top_k": top_k},
        ).mappings()
        ids = [int(row["id"]) for row in rows]
        plan = connection.execute(
            text(explain),
            {"query_vector": _pgvector_literal(query_vector), "top_k": top_k},
        ).scalar_one()
    elapsed_ms = round((time.perf_counter() - started) * 1000, 3)
    plan_json = json.dumps(plan, ensure_ascii=False)
    return ids, elapsed_ms, plan_json


def _recall(expected: list[int], observed: list[int]) -> float:
    if not expected:
        return 0.0
    return round(len(set(expected).intersection(observed)) / len(expected), 4)


def _run_method(
    engine: Engine,
    *,
    table_name: str,
    method: str,
    config: SmokeConfig,
    vectors: list[list[float]],
    query_vector: list[float],
) -> dict[str, Any]:
    _prepare_table(engine, table_name=table_name, dimensions=config.dimensions, vectors=vectors)
    exact_ids, exact_ms, _ = _top_ids(
        engine,
        table_name=table_name,
        query_vector=query_vector,
        top_k=config.top_k,
        force_index=False,
        index_method="exact",
    )
    if method == "hnsw":
        index_sql = (
            f"CREATE INDEX {table_name}_hnsw_idx ON {table_name} "
            "USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64)"
        )
    else:
        lists = max(1, min(100, config.rows // 100))
        index_sql = (
            f"CREATE INDEX {table_name}_ivfflat_idx ON {table_name} "
            f"USING ivfflat (embedding vector_cosine_ops) WITH (lists = {lists})"
        )
    build_ms = _timed_execute(engine, index_sql)
    with engine.begin() as connection:
        connection.execute(text(f"ANALYZE {table_name}"))
    ann_ids, ann_ms, plan_json = _top_ids(
        engine,
        table_name=table_name,
        query_vector=query_vector,
        top_k=config.top_k,
        force_index=True,
        index_method=method,
    )
    return {
        "method": method,
        "table_name": table_name,
        "rows": config.rows,
        "dimensions": config.dimensions,
        "top_k": config.top_k,
        "index_build_ms": build_ms,
        "exact_query_ms": exact_ms,
        "ann_query_ms": ann_ms,
        "recall_at_k": _recall(exact_ids, ann_ids),
        "exact_ids": exact_ids,
        "ann_ids": ann_ids,
        "planner_mentions_index_method": method in plan_json.lower(),
    }


def run_smoke(config: SmokeConfig) -> dict[str, Any]:
    if config.rows < config.top_k:
        raise ValueError("rows must be greater than or equal to top_k")
    if config.dimensions < 8:
        raise ValueError("dimensions must be at least 8")
    if not config.database_url.startswith("postgresql"):
        raise ValueError("smoke requires a PostgreSQL DATABASE_URL; refusing non-PostgreSQL execution")

    engine = create_engine(config.database_url, pool_pre_ping=True)
    suffix = f"{int(time.time())}_{os.getpid()}"
    table_names = {
        "hnsw": f"tmp_pgvector_ann_hnsw_{suffix}",
        "ivfflat": f"tmp_pgvector_ann_ivfflat_{suffix}",
    }
    vectors = _sample_vectors(rows=config.rows, dimensions=config.dimensions, seed=config.seed)
    query_vector = vectors[min(42, config.rows - 1)]
    results: list[dict[str, Any]] = []
    try:
        with engine.begin() as connection:
            dialect = connection.execute(text("SELECT version()")).scalar_one()
            extension_version = connection.execute(
                text("SELECT extversion FROM pg_extension WHERE extname = 'vector'")
            ).scalar()
        for method, table_name in table_names.items():
            results.append(
                _run_method(
                    engine,
                    table_name=table_name,
                    method=method,
                    config=config,
                    vectors=vectors,
                    query_vector=query_vector,
                )
            )
        return {
            "status": "passed",
            "database": "postgresql",
            "postgres_version": dialect,
            "pgvector_version_before_smoke": extension_version,
            "external_model_call_performed": False,
            "application_query_path_changed": False,
            "results": results,
        }
    finally:
        if not config.keep_tables:
            with engine.begin() as connection:
                for table_name in table_names.values():
                    connection.execute(text(f"DROP TABLE IF EXISTS {table_name}"))


def parse_args() -> SmokeConfig:
    parser = argparse.ArgumentParser(description="Run a local pgvector HNSW/IVFFlat ANN smoke.")
    parser.add_argument(
        "--database-url",
        default=os.environ.get("ANN_SMOKE_DATABASE_URL")
        or os.environ.get("DATABASE_URL")
        or DEFAULT_DATABASE_URL,
        help="PostgreSQL SQLAlchemy URL. Defaults to local Docker compose database.",
    )
    parser.add_argument("--rows", type=int, default=2000)
    parser.add_argument("--dimensions", type=int, default=64)
    parser.add_argument("--top-k", type=int, default=10)
    parser.add_argument("--seed", type=int, default=20260626)
    parser.add_argument("--keep-tables", action="store_true", help="Keep smoke tables for manual inspection.")
    args = parser.parse_args()
    return SmokeConfig(
        database_url=args.database_url,
        rows=args.rows,
        dimensions=args.dimensions,
        top_k=args.top_k,
        seed=args.seed,
        keep_tables=args.keep_tables,
    )


def main() -> None:
    report = run_smoke(parse_args())
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
